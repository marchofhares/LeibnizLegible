"""Tests for engine adapters (offline; no kraken, injected HTTP for anthropic)."""

from __future__ import annotations

import copy

import pytest

from leibniz.htr import engines
from leibniz.htr.engines import (
    GEMINI_URL,
    OPENAI_URL,
    AnthropicEngine,
    GeminiEngine,
    KrakenEngine,
    MissingKeyError,
    OpenAIEngine,
    estimate_gemini_cost,
    estimate_openai_cost,
)

# -- Kraken (heavy deps absent in the test env) ----------------------------- #


def test_kraken_engine_constructs_without_kraken() -> None:
    # Construction is cheap and lazy — no import of kraken/torch yet.
    eng = KrakenEngine("data/models/foo/model.safetensors")
    assert eng.name == "kraken"
    assert eng.version == "model"  # basename stem


def test_kraken_engine_transcribe_errors_without_stack() -> None:
    # This checks the graceful-degradation path when the optional kraken/torch
    # stack is absent — so it only applies when the stack is NOT installed. With
    # the `bench` extra present (e.g. a live-run env) there is no import error to
    # test, so skip rather than assert an env the run has deliberately changed.
    try:
        import kraken  # noqa: F401
        import torch  # noqa: F401
    except ModuleNotFoundError:
        eng = KrakenEngine("nonexistent.safetensors")
        with pytest.raises(ModuleNotFoundError):
            eng.transcribe([b"\xff\xd8\xff"])
    else:
        pytest.skip("kraken stack installed (bench extra); absent-stack path not exercisable")


# -- Anthropic (graceful skip + injected transport) ------------------------- #


def test_anthropic_missing_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingKeyError):
        AnthropicEngine()


class _FakeResp:
    def __init__(self, text: str, status: int = 200) -> None:
        self.status_code = status
        self._text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return {"content": [{"type": "text", "text": self._text}]}


class _FakeClient:
    """Records posts and returns a scripted transcription per call."""

    def __init__(self, replies: list[str]) -> None:
        self.replies = replies
        self.posts: list[dict] = []

    def post(self, url, headers=None, json=None):  # noqa: A002 - mirror httpx
        self.posts.append({"url": url, "headers": headers, "json": json})
        return _FakeResp(self.replies[len(self.posts) - 1])

    def close(self) -> None:
        pass


def test_anthropic_transcribe_with_injected_client() -> None:
    client = _FakeClient(["prima", "secunda"])
    eng = AnthropicEngine(api_key="sk-test", client=client, min_interval=0, sleep=lambda _s: None)
    out = eng.transcribe([b"\xff\xd8\xffimg1", b"\x89PNG\r\n\x1a\nimg2"])
    assert out == ["prima", "secunda"]
    # Media types sniffed from magic bytes into the request payload.
    src0 = client.posts[0]["json"]["messages"][0]["content"][0]["source"]
    src1 = client.posts[1]["json"]["messages"][0]["content"][0]["source"]
    assert src0["media_type"] == "image/jpeg"
    assert src1["media_type"] == "image/png"
    # Auth + version headers present.
    assert client.posts[0]["headers"]["x-api-key"] == "sk-test"
    assert client.posts[0]["headers"]["anthropic-version"] == engines.ANTHROPIC_VERSION


def test_anthropic_retries_then_succeeds() -> None:
    class Flaky:
        def __init__(self):
            self.n = 0

        def post(self, url, headers=None, json=None):  # noqa: A002
            self.n += 1
            return _FakeResp("ok", status=200 if self.n > 2 else 529)

        def close(self):
            pass

    eng = AnthropicEngine(api_key="k", client=Flaky(), max_retries=4, sleep=lambda _s: None)
    assert eng.transcribe([b"x"]) == ["ok"]


def test_sniff_media_type() -> None:
    assert engines._sniff_media_type(b"\xff\xd8\xff\xe0") == "image/jpeg"
    assert engines._sniff_media_type(b"\x89PNG\r\n\x1a\n") == "image/png"
    assert engines._sniff_media_type(b"RIFF????WEBP") == "image/webp"
    assert engines._sniff_media_type(b"unknown") == "image/jpeg"  # default


def test_extract_text_concatenates_blocks() -> None:
    payload = {
        "content": [{"type": "text", "text": "a"}, {"type": "other"}, {"type": "text", "text": "b"}]
    }
    assert engines._extract_text(payload) == "ab"


# -- OpenAI (graceful skip + injected transport + usage/cost) --------------- #


def test_openai_missing_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(MissingKeyError):
        OpenAIEngine()


class _OAResp:
    def __init__(self, text: str, ptok: int, ctok: int, status: int = 200) -> None:
        self.status_code = status
        self._t, self._p, self._c = text, ptok, ctok

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return {
            "choices": [{"message": {"content": self._t}}],
            "usage": {"prompt_tokens": self._p, "completion_tokens": self._c},
        }


class _OAClient:
    def __init__(self, replies) -> None:
        self.replies = replies
        self.posts: list[dict] = []

    def post(self, url, headers=None, json=None):  # noqa: A002
        self.posts.append({"url": url, "headers": headers, "json": json})
        t, p, c = self.replies[len(self.posts) - 1]
        return _OAResp(t, p, c)

    def close(self) -> None:
        pass


def test_openai_transcribe_accumulates_usage_and_cost() -> None:
    client = _OAClient([("prima", 600, 20), ("secunda", 550, 25)])
    eng = OpenAIEngine(
        api_key="sk-test", model="gpt-4o", client=client, min_interval=0, sleep=lambda _s: None
    )
    out = eng.transcribe([b"\xff\xd8\xffimg1", b"\x89PNG\r\n\x1a\nimg2"])
    assert out == ["prima", "secunda"]
    assert eng.usage_input == 1150
    assert eng.usage_output == 45
    # Data-URL image blocks + auth header shape.
    content = client.posts[0]["json"]["messages"][0]["content"]
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert content[1]["image_url"]["detail"] == "high"
    assert client.posts[0]["headers"]["Authorization"] == "Bearer sk-test"
    assert client.posts[0]["json"]["model"] == "gpt-4o"
    # Cost = 1150 in @ $2.50/1M + 45 out @ $10/1M.
    assert eng.cost == pytest.approx(1150 * 2.5 / 1e6 + 45 * 10 / 1e6)


def test_openai_omits_temperature_when_none() -> None:
    client = _OAClient([("x", 1, 1)])
    eng = OpenAIEngine(api_key="k", client=client, temperature=None, min_interval=0)
    eng.transcribe([b"x"])
    assert "temperature" not in client.posts[0]["json"]
    assert "max_completion_tokens" in client.posts[0]["json"]


def test_estimate_openai_cost_prefix_match() -> None:
    # Dated snapshot id prices as its base family.
    exact = estimate_openai_cost("gpt-4o", 1_000_000, 0)
    dated = estimate_openai_cost("gpt-4o-2024-08-06", 1_000_000, 0)
    assert exact == dated == pytest.approx(2.50)
    assert estimate_openai_cost("some-unknown-model", 1000, 1000) is None
    # Longest prefix wins: a gpt-5.6 tier prices as itself, not as bare gpt-5.
    assert estimate_openai_cost("gpt-5.6-luna", 1_000_000, 0) == pytest.approx(0.20)
    assert estimate_openai_cost("gpt-5.6-sol-2026-01-01", 1_000_000, 0) == pytest.approx(4.00)


def test_openai_url_is_overridable() -> None:
    client = _OAClient([("x", 1, 1)])
    eng = OpenAIEngine(api_key="k", url="https://example.test/v1/cc", client=client, min_interval=0)
    eng.transcribe([b"x"])
    assert client.posts[0]["url"] == "https://example.test/v1/cc"
    # And the default stays the OpenAI endpoint.
    client2 = _OAClient([("x", 1, 1)])
    OpenAIEngine(api_key="k", client=client2, min_interval=0).transcribe([b"x"])
    assert client2.posts[0]["url"] == OPENAI_URL


class _TempPinned400:
    """First call: the gpt-5.x 'temperature is pinned' 400; then normal replies."""

    def __init__(self, replies) -> None:
        self.replies = replies
        self.posts: list[dict] = []

    def post(self, url, headers=None, json=None):  # noqa: A002
        # Snapshot the body: the engine mutates it in place on the retry.
        self.posts.append({"url": url, "headers": headers, "json": copy.deepcopy(json)})
        if len(self.posts) == 1:

            class _Err:
                status_code = 400

                @staticmethod
                def json() -> dict:
                    return {"error": {"param": "temperature", "code": "unsupported_value"}}

                @staticmethod
                def raise_for_status() -> None:
                    raise RuntimeError("HTTP 400")

            return _Err()
        t, p, c = self.replies[len(self.posts) - 2]
        return _OAResp(t, p, c)

    def close(self) -> None:
        pass


def test_openai_drops_temperature_on_pinned_temperature_400() -> None:
    client = _TempPinned400([("prima", 10, 2), ("secunda", 10, 2)])
    eng = OpenAIEngine(api_key="k", client=client, min_interval=0, sleep=lambda _s: None)
    out = eng.transcribe([b"img1", b"img2"])
    assert out == ["prima", "secunda"]
    # Retry of the first image drops temperature; later images never send it.
    assert "temperature" in client.posts[0]["json"]
    assert "temperature" not in client.posts[1]["json"]
    assert "temperature" not in client.posts[2]["json"]
    assert eng.temperature is None


# -- Gemini (OpenAI-compatible endpoint; injected HTTP) ---------------------- #


def test_gemini_missing_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(MissingKeyError):
        GeminiEngine()


def test_gemini_posts_google_endpoint_with_env_key(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gm-test")
    client = _OAClient([("linea", 1000, 40)])
    eng = GeminiEngine(client=client, min_interval=0)
    assert eng.transcribe([b"\xff\xd8\xffimg"]) == ["linea"]
    assert eng.name == "gemini"
    assert eng.version == "gemini-3.8-flash"
    assert client.posts[0]["url"] == GEMINI_URL
    assert client.posts[0]["headers"]["Authorization"] == "Bearer gm-test"
    # Cost from the Gemini table: 1000 in @ $0.75/1M + 40 out @ $3.75/1M.
    assert eng.cost == pytest.approx(1000 * 0.75 / 1e6 + 40 * 3.75 / 1e6)


def test_estimate_gemini_cost_prefix_and_unknown() -> None:
    exact = estimate_gemini_cost("gemini-3.8-flash", 1_000_000, 0)
    dated = estimate_gemini_cost("gemini-3.8-flash-001", 1_000_000, 0)
    assert exact == dated == pytest.approx(0.75)
    assert estimate_gemini_cost("gemini-unknown", 1000, 1000) is None


def test_should_flush_before_bounds_padded_batch_area() -> None:
    # Normal lines: a full batch of 16 × 2k px stays under the 64k budget.
    assert not engines._should_flush_before(15, 2000, 2000)
    # A wide line shrinks the batch: at 9k px wide, the 8th line would push the
    # padded area over budget (8 × 9000 = 72k) — flush first.
    assert engines._should_flush_before(7, 9000, 2000)
    assert engines._should_flush_before(7, 2000, 9000)  # incoming line is the wide one
    # An empty buffer never flushes (the single line still gets transcribed).
    assert not engines._should_flush_before(0, 0, 9000)


class _FlakyTransport:
    """First post raises a transport error (dead proxied socket); then replies."""

    def __init__(self, replies) -> None:
        self.replies = replies
        self.posts = 0

    def post(self, url, headers=None, json=None):  # noqa: A002
        self.posts += 1
        if self.posts == 1:
            import httpx

            raise httpx.ReadTimeout("simulated dead tunneled connection")
        t, p, c = self.replies[self.posts - 2]
        return _OAResp(t, p, c)

    def close(self) -> None:
        pass


def test_openai_retries_transport_error_then_succeeds() -> None:
    client = _FlakyTransport([("prima", 5, 2)])
    eng = OpenAIEngine(api_key="k", client=client, min_interval=0, sleep=lambda _s: None)
    assert eng.transcribe([b"img"]) == ["prima"]
    assert client.posts == 2


def test_openai_transport_error_exhausts_retries() -> None:
    class _AlwaysDead:
        posts = 0

        def post(self, url, headers=None, json=None):  # noqa: A002
            self.posts += 1
            import httpx

            raise httpx.ConnectError("proxy down")

        def close(self) -> None:
            pass

    client = _AlwaysDead()
    eng = OpenAIEngine(
        api_key="k", client=client, min_interval=0, max_retries=2, sleep=lambda _s: None
    )
    import httpx

    with pytest.raises(httpx.ConnectError):
        eng.transcribe([b"img"])
    assert client.posts == 3  # initial + 2 retries
