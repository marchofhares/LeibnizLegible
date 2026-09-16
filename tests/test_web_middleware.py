"""Rate limiting and security headers — the pure-ASGI middleware over a tiny app."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from leibniz.web.middleware import (
    CONTENT_SECURITY_POLICY,
    SECURITY_HEADERS,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


class Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def _app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/x")
    def x() -> dict:
        return {"ok": True}

    @app.get("/static/y")
    def y() -> dict:
        return {"ok": True}

    return app


def test_burst_then_429_then_refill() -> None:
    clock = Clock()
    app = _app()
    app.add_middleware(RateLimitMiddleware, rate=2.0, burst=3, clock=clock)
    c = TestClient(app)
    assert [c.get("/api/x").status_code for _ in range(4)] == [200, 200, 200, 429]
    r = c.get("/api/x")
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "1" and r.headers["Cache-Control"] == "no-store"
    assert r.json()["detail"].startswith("rate limit")
    # never limited: the viewer shell and static files
    assert c.get("/static/y").status_code == 200
    # half a second at 2/s refills exactly one token
    clock.t += 0.5
    assert c.get("/api/x").status_code == 200
    assert c.get("/api/x").status_code == 429


def test_buckets_are_per_client() -> None:
    m = RateLimitMiddleware(_app(), rate=1.0, burst=1, clock=Clock())
    assert m.take("10.0.0.1") == 0.0
    assert m.take("10.0.0.2") == 0.0
    assert m.take("10.0.0.1") == 1.0  # a full second until the next token
    assert m.client_key({"client": ("203.0.113.9", 4321)}) == "203.0.113.9"
    assert m.client_key({"client": None}) == "unknown"


def test_zero_rate_disables() -> None:
    app = _app()
    app.add_middleware(RateLimitMiddleware, rate=0, burst=1)
    c = TestClient(app)
    assert all(c.get("/api/x").status_code == 200 for _ in range(50))


def test_bounded_memory_sweeps_idle_and_oldest() -> None:
    clock = Clock()
    m = RateLimitMiddleware(_app(), rate=1.0, burst=2, clock=clock, max_clients=3)
    for key in ("a", "b", "c", "d"):
        m.take(key)
    # four clients, cap three, none idle → the oldest bucket goes
    assert len(m._buckets) == 3 and "a" not in m._buckets
    clock.t += 10  # everyone idle (refilled) — one new client sweeps them all
    m.take("e")
    assert set(m._buckets) == {"e"}


def test_security_headers_on_every_response() -> None:
    app = _app()
    app.add_middleware(SecurityHeadersMiddleware)
    c = TestClient(app)
    r = c.get("/api/x")
    for name, value in SECURITY_HEADERS.items():
        assert r.headers[name] == value
    assert r.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert "script-src 'self'" in CONTENT_SECURITY_POLICY
    assert "frame-ancestors" not in CONTENT_SECURITY_POLICY  # embedding is allowed on purpose
    assert c.get("/nope").status_code == 404
    assert c.get("/nope").headers["X-Content-Type-Options"] == "nosniff"


def test_app_set_header_wins() -> None:
    app = FastAPI()

    @app.get("/z")
    def z() -> JSONResponse:
        return JSONResponse({}, headers={"X-Content-Type-Options": "custom"})

    app.add_middleware(SecurityHeadersMiddleware)
    r = TestClient(app).get("/z")
    assert r.headers["X-Content-Type-Options"] == "custom"
    assert r.headers["Referrer-Policy"] == SECURITY_HEADERS["Referrer-Policy"]
