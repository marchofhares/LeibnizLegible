"""ASGI middleware for the public deployment (Phase D hardening).

Two small, dependency-free pieces the reverse proxy could also do but that the
app should not rely on it for:

* :class:`RateLimitMiddleware` — a per-client token bucket over the API, the
  IIIF manifests and the annotation pages (the routes that cost a store or a
  Meilisearch query). Static files and the viewer shell are never limited.
  A client over the limit gets ``429`` with ``Retry-After``. The bucket state
  is per process: with ``leibniz serve --workers N`` each worker limits on its
  own, so the effective allowance is N× the configured rate (SPECS asks for no
  analytics, so there is deliberately no shared store of client addresses).
* :class:`SecurityHeadersMiddleware` — the response headers a public site
  should carry: a Content Security Policy that keeps scripts to our own origin
  while letting images and IIIF ``info.json`` come from the GWLB (or any
  https host, since the store decides where a work's images live),
  ``nosniff``, a referrer policy consistent with the viewer's ``<meta>``,
  and a permissions policy that turns off sensors the viewer never uses.
  HSTS is left to the TLS terminator, which is the only party that knows the
  connection is TLS.

Both are pure ASGI (no ``BaseHTTPMiddleware``), so streaming and the event
loop are untouched.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

RATE_LIMITED_PREFIXES: tuple[str, ...] = ("/api/", "/manifests/", "/annotations/")

# The viewer's own scripts and styles only; images and XHR (OpenSeadragon's
# ``info.json``) from any https origin because page images are the GWLB's and
# the store, not the code, says which host serves them. ``data:`` images cover
# the empty favicon. Framing is allowed on purpose: the viewer is read-only,
# has no sessions, and embedding it is a feature, not a risk.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https:; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer-when-downgrade",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
}


class RateLimitMiddleware:
    """Token bucket per client address: ``rate`` requests/second, ``burst`` at once.

    ``clock`` is injectable for tests. Buckets are kept in a bounded dict:
    once more than ``max_clients`` are tracked, idle buckets (refilled to the
    brim) are swept, at most once per second, and the oldest go if that is
    not enough — so a flood of addresses cannot grow memory without bound.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        rate: float,
        burst: int,
        prefixes: Iterable[str] = RATE_LIMITED_PREFIXES,
        clock: Callable[[], float] = time.monotonic,
        max_clients: int = 10_000,
    ) -> None:
        self.app = app
        self.rate = max(0.0, float(rate))
        self.burst = max(1, int(burst))
        self.prefixes = tuple(prefixes)
        self.clock = clock
        self.max_clients = max(1, int(max_clients))
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, updated_at)
        self._last_sweep = 0.0

    @property
    def enabled(self) -> bool:
        return self.rate > 0

    @staticmethod
    def client_key(scope: Scope) -> str:
        """The peer address (uvicorn substitutes ``X-Forwarded-For`` for trusted proxies)."""
        client = scope.get("client")
        return str(client[0]) if client else "unknown"

    def take(self, key: str) -> float:
        """Take one token for ``key``: ``0.0`` if allowed, else seconds until one is due."""
        now = self.clock()
        tokens, at = self._buckets.get(key, (float(self.burst), now))
        tokens = min(float(self.burst), tokens + max(0.0, now - at) * self.rate)
        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            self._maybe_sweep(now)
            return 0.0
        self._buckets[key] = (tokens, now)
        return (1.0 - tokens) / self.rate

    def _maybe_sweep(self, now: float) -> None:
        if len(self._buckets) <= self.max_clients or now - self._last_sweep < 1.0:
            return
        self._last_sweep = now
        idle_after = self.burst / self.rate
        for key in [k for k, (_, at) in self._buckets.items() if now - at >= idle_after]:
            del self._buckets[key]
        excess = len(self._buckets) - self.max_clients
        if excess > 0:
            oldest = sorted(self._buckets, key=lambda k: self._buckets[k][1])[:excess]
            for key in oldest:
                del self._buckets[key]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or not self.enabled
            or not str(scope.get("path", "")).startswith(self.prefixes)
        ):
            await self.app(scope, receive, send)
            return
        wait = self.take(self.client_key(scope))
        if wait > 0:
            response = JSONResponse(
                {"detail": "rate limit exceeded; slow down"},
                status_code=429,
                headers={"Retry-After": str(max(1, math.ceil(wait))), "Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    """Add :data:`SECURITY_HEADERS` to every HTTP response (existing headers win)."""

    def __init__(self, app: ASGIApp, *, headers: dict[str, str] | None = None) -> None:
        self.app = app
        self.headers = dict(SECURITY_HEADERS if headers is None else headers)
        self._encoded = [
            (k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in self.headers.items()
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw = list(message.get("headers") or [])
                present = {k.lower() for k, _ in raw}
                raw.extend((k, v) for k, v in self._encoded if k not in present)
                message = {**message, "headers": raw}
            await send(message)

        await self.app(scope, receive, send_with_headers)


__all__ = [
    "CONTENT_SECURITY_POLICY",
    "RATE_LIMITED_PREFIXES",
    "SECURITY_HEADERS",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]
