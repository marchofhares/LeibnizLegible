"""Tests for the polite HTTP client — offline via ``httpx.MockTransport``.

No real socket is opened and no real time passes: a fake clock records the
throttle/backoff sleeps so the politeness guarantees are asserted deterministically.
"""

from __future__ import annotations

import httpx
import pytest

from leibniz import net


class FakeClock:
    """Deterministic monotonic clock; ``sleep`` advances it and logs the wait."""

    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds


def _client(handler, clock: FakeClock, **kw) -> net.PoliteClient:
    transport = httpx.MockTransport(handler)
    return net.PoliteClient(
        client=httpx.Client(transport=transport),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
        **kw,
    )


# -- User-Agent ------------------------------------------------------------- #


def test_user_agent_prefers_explicit() -> None:
    assert net.default_user_agent({"LEIBNIZ_USER_AGENT": "custom/1.0"}) == "custom/1.0"


def test_user_agent_embeds_contact_email() -> None:
    ua = net.default_user_agent({"LEIBNIZ_CONTACT_EMAIL": "me@example.org"})
    assert "mailto:me@example.org" in ua
    assert net.PROJECT_URL in ua


def test_user_agent_fallback_is_contactless() -> None:
    ua = net.default_user_agent({})
    assert "leibniz-legible" in ua and "mailto:" not in ua


# -- Throttle --------------------------------------------------------------- #


def test_throttle_enforces_min_interval_per_host() -> None:
    clock = FakeClock()

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok")

    pc = _client(handler, clock, min_interval=1.0)
    pc.get_text("https://host.example/a")
    pc.get_text("https://host.example/b")  # same host → must wait ~1s
    assert clock.sleeps == [pytest.approx(1.0)]


def test_throttle_is_per_host() -> None:
    clock = FakeClock()

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok")

    pc = _client(handler, clock, min_interval=1.0)
    pc.get_text("https://host-a.example/x")
    pc.get_text("https://host-b.example/y")  # different host → no wait
    assert clock.sleeps == []


def test_user_agent_header_is_sent() -> None:
    clock = FakeClock()
    seen: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req.headers.get("user-agent", ""))
        return httpx.Response(200, text="ok")

    pc = _client(handler, clock, min_interval=0, user_agent="leibniz-test/9")
    pc.get_text("https://host.example/a")
    assert seen == ["leibniz-test/9"]


# -- Retry / backoff -------------------------------------------------------- #


def test_retries_transient_then_succeeds() -> None:
    clock = FakeClock()
    calls = {"n": 0}

    def handler(_req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200 if calls["n"] >= 3 else 503, text="x")

    pc = _client(handler, clock, min_interval=0)
    resp = pc.get("https://host.example/a")
    assert resp.status_code == 200
    assert calls["n"] == 3
    assert clock.sleeps == [pytest.approx(2.0), pytest.approx(4.0)]  # 2**1, 2**2


def test_retry_gives_up_and_raises() -> None:
    clock = FakeClock()

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    pc = _client(handler, clock, min_interval=0, max_retries=2)
    with pytest.raises(net.RetryError):
        pc.get("https://host.example/a")
    assert clock.sleeps == [pytest.approx(2.0), pytest.approx(4.0)]


def test_non_retryable_404_propagates() -> None:
    clock = FakeClock()

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="nope")

    pc = _client(handler, clock, min_interval=0)
    with pytest.raises(httpx.HTTPStatusError):
        pc.get("https://host.example/missing")


def test_transport_error_is_retried_then_raises() -> None:
    clock = FakeClock()

    def handler(_req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    pc = _client(handler, clock, min_interval=0, max_retries=1)
    with pytest.raises(net.RetryError):
        pc.get("https://host.example/a")
    assert clock.sleeps == [pytest.approx(2.0)]
