"""Tests for engine adapters (offline; no kraken, injected HTTP for anthropic)."""

from __future__ import annotations

import pytest

from leibniz.htr import engines
from leibniz.htr.engines import AnthropicEngine, KrakenEngine, MissingKeyError

# -- Kraken (heavy deps absent in the test env) ----------------------------- #


def test_kraken_engine_constructs_without_kraken() -> None:
    # Construction is cheap and lazy — no import of kraken/torch yet.
    eng = KrakenEngine("data/models/foo/model.safetensors")
    assert eng.name == "kraken"
    assert eng.version == "model"  # basename stem


def test_kraken_engine_transcribe_errors_without_stack() -> None:
    eng = KrakenEngine("nonexistent.safetensors")
    # The project test env has no kraken/torch: a clear ModuleNotFoundError.
    with pytest.raises(ModuleNotFoundError):
        eng.transcribe([b"\xff\xd8\xff"])


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
