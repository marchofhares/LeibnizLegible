"""Tests for engine adapters (offline; no kraken, injected HTTP for anthropic)."""

from __future__ import annotations

import pytest

from leibniz.htr import engines
from leibniz.htr.engines import (
    AnthropicEngine,
    KrakenEngine,
    MissingKeyError,
    OpenAIEngine,
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
