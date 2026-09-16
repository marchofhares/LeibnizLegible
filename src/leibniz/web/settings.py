"""Serve-time configuration — the one place the CLI, the ASGI factory and the
deployment files agree on.

Every setting has an environment variable, because a systemd unit or a
container image configures the process through its environment, and because
uvicorn's worker processes (``leibniz serve --workers N``) must rebuild the
application from scratch: the CLI exports its options with :meth:`to_env` and
:mod:`leibniz.web.asgi` reads them back with :meth:`from_env`.

| Variable                  | Setting        | Default                       |
| ------------------------- | -------------- | ----------------------------- |
| ``LEIBNIZ_DB_PATH``       | ``db_path``    | ``data/inventory.sqlite``     |
| ``LEIBNIZ_SEARCH_BACKEND``| ``backend``    | ``fts5`` (``meili``, ``none``)|
| ``LEIBNIZ_INDEX_PATH``    | ``index_path`` | ``data/search.sqlite``        |
| ``MEILI_URL``             | ``meili_url``  | ``http://127.0.0.1:7700``     |
| ``MEILI_API_KEY``         | ``meili_key``  | (``MEILI_MASTER_KEY`` fallback)|
| ``LEIBNIZ_HOST``          | ``host``       | ``127.0.0.1``                 |
| ``LEIBNIZ_PORT``          | ``port``       | ``8000``                      |
| ``LEIBNIZ_BASE_URL``      | ``base_url``   | from the request              |
| ``LEIBNIZ_WORKERS``       | ``workers``    | ``1``                         |
| ``LEIBNIZ_RATE_LIMIT``    | ``rate_limit`` | ``10`` requests/s per client  |
| ``LEIBNIZ_RATE_BURST``    | ``rate_burst`` | ``40``                        |
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from leibniz import db
from leibniz.search import open_backend
from leibniz.search.backend import SearchBackend
from leibniz.search.fts5 import DEFAULT_INDEX_PATH
from leibniz.search.meili import DEFAULT_MEILI_URL

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI

BACKENDS = ("fts5", "meili", "none")
DEFAULT_RATE_LIMIT = 10.0  # requests per second, per client address
DEFAULT_RATE_BURST = 40

ENV: dict[str, str] = {
    "db_path": "LEIBNIZ_DB_PATH",
    "backend": "LEIBNIZ_SEARCH_BACKEND",
    "index_path": "LEIBNIZ_INDEX_PATH",
    "meili_url": "MEILI_URL",
    "meili_key": "MEILI_API_KEY",
    "host": "LEIBNIZ_HOST",
    "port": "LEIBNIZ_PORT",
    "base_url": "LEIBNIZ_BASE_URL",
    "workers": "LEIBNIZ_WORKERS",
    "rate_limit": "LEIBNIZ_RATE_LIMIT",
    "rate_burst": "LEIBNIZ_RATE_BURST",
}
MEILI_KEY_FALLBACK = "MEILI_MASTER_KEY"  # the dev name; production uses a search-only key


@dataclass(slots=True)
class ServeSettings:
    """Everything ``leibniz serve`` needs to build and bind the application."""

    db_path: Path = db.DEFAULT_DB_PATH
    backend: str = "fts5"
    index_path: Path = Path(DEFAULT_INDEX_PATH)
    meili_url: str = DEFAULT_MEILI_URL
    meili_key: str | None = None
    host: str = "127.0.0.1"
    port: int = 8000
    base_url: str | None = None
    workers: int = 1
    rate_limit: float = DEFAULT_RATE_LIMIT
    rate_burst: int = DEFAULT_RATE_BURST

    def __post_init__(self) -> None:
        self.backend = (self.backend or "fts5").lower()
        if self.backend not in BACKENDS:
            raise ValueError(
                f"unknown search backend {self.backend!r} (expected one of {BACKENDS})"
            )
        self.db_path = Path(self.db_path)
        self.index_path = Path(self.index_path)
        self.workers = max(1, int(self.workers))
        self.rate_limit = max(0.0, float(self.rate_limit))
        self.rate_burst = max(1, int(self.rate_burst))
        self.base_url = (self.base_url or "").strip().rstrip("/") or None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ServeSettings:
        """Build from the environment (unset or empty variables keep the default)."""
        e = os.environ if env is None else env

        def get(key: str, default: object) -> object:
            value = e.get(ENV[key])
            return default if value is None or value == "" else value

        return cls(
            db_path=Path(str(get("db_path", db.DEFAULT_DB_PATH))),
            backend=str(get("backend", "fts5")),
            index_path=Path(str(get("index_path", DEFAULT_INDEX_PATH))),
            meili_url=str(get("meili_url", DEFAULT_MEILI_URL)),
            meili_key=e.get(ENV["meili_key"]) or e.get(MEILI_KEY_FALLBACK) or None,
            host=str(get("host", "127.0.0.1")),
            port=int(str(get("port", 8000))),
            base_url=e.get(ENV["base_url"]) or None,
            workers=int(str(get("workers", 1))),
            rate_limit=float(str(get("rate_limit", DEFAULT_RATE_LIMIT))),
            rate_burst=int(str(get("rate_burst", DEFAULT_RATE_BURST))),
        )

    def to_env(self) -> dict[str, str]:
        """The settings as environment variables — how worker processes receive them."""
        out = {
            ENV["db_path"]: str(self.db_path),
            ENV["backend"]: self.backend,
            ENV["index_path"]: str(self.index_path),
            ENV["meili_url"]: self.meili_url,
            ENV["host"]: self.host,
            ENV["port"]: str(self.port),
            ENV["workers"]: str(self.workers),
            ENV["rate_limit"]: str(self.rate_limit),
            ENV["rate_burst"]: str(self.rate_burst),
        }
        if self.meili_key:
            out[ENV["meili_key"]] = self.meili_key
        if self.base_url:
            out[ENV["base_url"]] = self.base_url
        return out

    def open_search(self) -> SearchBackend | None:
        if self.backend == "none":
            return None
        return open_backend(
            self.backend,
            path=str(self.index_path),
            meili_url=self.meili_url,
            meili_key=self.meili_key,
        )

    def build_app(self) -> FastAPI:
        from leibniz.web.api import create_app

        return create_app(
            self.db_path,
            search=self.open_search(),
            base_url=self.base_url,
            rate_limit=self.rate_limit,
            rate_burst=self.rate_burst,
        )


__all__ = [
    "BACKENDS",
    "DEFAULT_RATE_BURST",
    "DEFAULT_RATE_LIMIT",
    "ENV",
    "MEILI_KEY_FALLBACK",
    "ServeSettings",
]
