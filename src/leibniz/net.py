"""Polite HTTP client — the crawling-etiquette rails, as code (SPECS §7.4).

Every outbound request the project makes to GWLB or BBAW goes through
:class:`PoliteClient`, which guarantees, in one place:

* an **identifying User-Agent** carrying the project URL and a contact email
  (from the environment; see ``.env.example``),
* **≤ 1 request/second per host** (tracked per host, so two hosts don't
  serialise against each other),
* **exponential backoff** (2s, 4s, 8s, 16s) on ``429``/``5xx``/transport errors,
* a small, typed surface (``get_text``/``get_bytes``/``get_json``).

Cache-first behaviour (never re-fetch what's on disk) lives in the callers
(``harvest.oai``, ``harvest.manifests``) because *what* counts as the cache key
differs per stage; this class only makes the network access itself polite.

The client is fully injectable for offline tests: pass an ``httpx.Client`` built
on a ``MockTransport`` plus ``min_interval=0`` and no real socket is opened and
no real time passes.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

PROJECT_URL = "https://github.com/marchofhares/leibnizlegible"
_FALLBACK_UA = f"leibniz-legible/0.1 (+{PROJECT_URL})"

# HTTP statuses worth retrying: rate-limit + transient server errors.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


def default_user_agent(env: Mapping[str, str] | None = None) -> str:
    """Build the crawler User-Agent, preferring explicit env configuration.

    Order: ``LEIBNIZ_USER_AGENT`` verbatim if set; else a string embedding
    ``LEIBNIZ_CONTACT_EMAIL`` if that is set; else a contactless fallback (only
    for tests / dry runs — real crawls should set a contact per SPECS §7.4).
    """
    env = os.environ if env is None else env
    ua = env.get("LEIBNIZ_USER_AGENT")
    if ua:
        return ua
    email = env.get("LEIBNIZ_CONTACT_EMAIL")
    if email:
        return f"leibniz-legible/0.1 (+{PROJECT_URL}; mailto:{email})"
    return _FALLBACK_UA


class RetryError(RuntimeError):
    """Raised when a request still fails after exhausting all retries."""


class PoliteClient:
    """A rate-limited, retrying, self-identifying HTTP GET client.

    Not thread-safe; the pipeline crawls one host at a time from one thread.
    Use as a context manager so an internally-created ``httpx.Client`` is
    closed. An injected ``client`` is left open (the caller owns it).
    """

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        min_interval: float = 1.0,
        max_retries: int = 4,
        backoff_base: float = 2.0,
        timeout: float = 60.0,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.user_agent = user_agent or default_user_agent()
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep
        self._monotonic = monotonic
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent},
        )
        # host -> monotonic timestamp of the last request to that host.
        self._last_by_host: dict[str, float] = {}

    # -- lifecycle ---------------------------------------------------------- #

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> PoliteClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- politeness --------------------------------------------------------- #

    def _throttle(self, host: str) -> None:
        """Sleep so consecutive requests to ``host`` are ≥ ``min_interval`` apart."""
        if self.min_interval <= 0:
            return
        last = self._last_by_host.get(host)
        if last is not None:
            wait = self.min_interval - (self._monotonic() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_by_host[host] = self._monotonic()

    # -- core --------------------------------------------------------------- #

    def get(self, url: str, params: Mapping[str, Any] | None = None) -> httpx.Response:
        """GET ``url`` politely, retrying transient failures with backoff.

        Raises :class:`RetryError` if every attempt fails, or
        ``httpx.HTTPStatusError`` for a non-retryable ``4xx`` (e.g. a genuine
        ``404``) that the caller should see.
        """
        host = httpx.URL(url).host
        headers = {"User-Agent": self.user_agent}
        attempt = 0
        while True:
            self._throttle(host)
            try:
                resp = self._client.get(url, params=params, headers=headers)
            except httpx.TransportError as exc:
                if attempt >= self.max_retries:
                    raise RetryError(f"transport error for {url}: {exc}") from exc
                attempt += 1
                self._sleep(self.backoff_base**attempt)
                continue

            if resp.status_code in RETRY_STATUSES:
                if attempt >= self.max_retries:
                    raise RetryError(f"{resp.status_code} for {url} after {attempt} retries")
                attempt += 1
                self._sleep(self.backoff_base**attempt)
                continue

            resp.raise_for_status()
            return resp

    def get_text(self, url: str, params: Mapping[str, Any] | None = None) -> str:
        return self.get(url, params).text

    def get_bytes(self, url: str, params: Mapping[str, Any] | None = None) -> bytes:
        return self.get(url, params).content

    def get_json(self, url: str, params: Mapping[str, Any] | None = None) -> Any:
        return self.get(url, params).json()


__all__ = [
    "PROJECT_URL",
    "RETRY_STATUSES",
    "PoliteClient",
    "RetryError",
    "default_user_agent",
]
