"""``leibniz serve`` — run the JSON API + viewer (Phases D1/D2).

Every option can also come from the environment (``deploy/env.example`` lists
the variables), which is how the systemd unit and the container configure it.
"""

from __future__ import annotations

import inspect
import os
import socket
from pathlib import Path

import typer
from rich.console import Console

from leibniz import db
from leibniz.search.fts5 import DEFAULT_INDEX_PATH
from leibniz.search.meili import DEFAULT_MEILI_URL
from leibniz.web.settings import (
    DEFAULT_RATE_BURST,
    DEFAULT_RATE_LIMIT,
    ENV,
    MEILI_KEY_FALLBACK,
    ServeSettings,
)

console = Console()


def listening_socket(host: str, port: int) -> socket.socket:
    """A bound, inheritable listening socket for the multi-worker path, created
    with ``proto=IPPROTO_TCP`` on purpose.

    uvicorn's own ``Config.bind_socket`` leaves ``proto`` at 0, and asyncio
    enables ``TCP_NODELAY`` on accepted connections only when the listening
    socket says IPPROTO_TCP. With ``--workers`` > 1 every response after the
    first on a kept-alive connection (which is how Caddy talks to us) waited
    ~40 ms for the peer's delayed ACK — Nagle's algorithm. Measured: 44 ms →
    1 ms per request. Single-worker mode is unaffected because there uvicorn
    lets asyncio create the socket itself.
    """
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.set_inheritable(True)
    return sock


def serve(
    db_path: Path = typer.Option(
        db.DEFAULT_DB_PATH,
        "--db",
        envvar=ENV["db_path"],
        help="Canonical SQLite store (opened read-only).",
    ),
    backend: str = typer.Option(
        "fts5", "--backend", envvar=ENV["backend"], help="Search backend: fts5 | meili | none."
    ),
    index: Path = typer.Option(
        DEFAULT_INDEX_PATH, "--index", envvar=ENV["index_path"], help="FTS5 index file."
    ),
    meili_url: str = typer.Option(
        DEFAULT_MEILI_URL, "--meili-url", envvar=ENV["meili_url"], help="Meilisearch URL."
    ),
    meili_key: str | None = typer.Option(
        None,
        "--meili-key",
        envvar=[ENV["meili_key"], MEILI_KEY_FALLBACK],
        help="Meilisearch API key (a search-only key in production).",
    ),
    host: str = typer.Option("127.0.0.1", "--host", envvar=ENV["host"]),
    port: int = typer.Option(8000, "--port", envvar=ENV["port"]),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        envvar=ENV["base_url"],
        help="Public base URL embedded in IIIF ids (default: from the request).",
    ),
    workers: int = typer.Option(
        1, "--workers", envvar=ENV["workers"], help="uvicorn worker processes."
    ),
    rate_limit: float = typer.Option(
        DEFAULT_RATE_LIMIT,
        "--rate-limit",
        envvar=ENV["rate_limit"],
        help="Per-client requests/second on the API, manifests and annotations (0 = off).",
    ),
    rate_burst: int = typer.Option(
        DEFAULT_RATE_BURST, "--rate-burst", envvar=ENV["rate_burst"], help="Per-client burst."
    ),
    image_base_url: str | None = typer.Option(
        None,
        "--image-base-url",
        envvar=ENV["image_base_url"],
        help="Serve page images from this mirror of the image cache (unset: from the GWLB).",
    ),
    forwarded_allow_ips: str | None = typer.Option(
        None,
        "--forwarded-allow-ips",
        envvar="FORWARDED_ALLOW_IPS",
        help="Proxies whose X-Forwarded-* headers to trust (uvicorn; default 127.0.0.1).",
    ),
    check: bool = typer.Option(
        False, "--check", help="Build the app and list routes; do not serve."
    ),
) -> None:
    """Serve the API, the IIIF manifests/annotations and the viewer."""
    try:
        settings = ServeSettings(
            db_path=db_path,
            backend=backend,
            index_path=index,
            meili_url=meili_url,
            meili_key=meili_key,
            host=host,
            port=port,
            base_url=base_url,
            workers=workers,
            rate_limit=rate_limit,
            rate_burst=rate_burst,
            image_base_url=image_base_url,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if settings.base_url_is_placeholder:
        console.print(
            f"[yellow]warning:[/yellow] LEIBNIZ_BASE_URL is still a placeholder "
            f"({settings.base_url}). It is embedded in every IIIF manifest and "
            "annotation id, which are meant to be permanent — set it to the real "
            "public origin before anyone fetches a manifest."
        )
    if check:
        app = settings.build_app()
        for route in app.routes:
            path = getattr(route, "path", None)
            if path:
                console.print(path)
        return
    import uvicorn

    limit = f"{settings.rate_limit:g}/s" if settings.rate_limit else "off"
    images = settings.image_base_url or "the GWLB"
    console.print(
        f"Serving Leibniz Legible on http://{settings.host}:{settings.port}  "
        f"(store {settings.db_path}, {settings.backend}, {settings.workers} worker(s), "
        f"rate limit {limit}, images from {images})"
    )
    options = {
        "host": settings.host,
        "port": settings.port,
        "proxy_headers": True,
        "forwarded_allow_ips": forwarded_allow_ips,
        "log_level": "info",
    }
    if settings.workers > 1:
        # Worker processes rebuild the app from the environment (leibniz.web.asgi).
        # The socket is ours (see listening_socket) rather than uvicorn.run()'s.
        from uvicorn.supervisors import Multiprocess

        os.environ.update(settings.to_env())
        config = uvicorn.Config(
            "leibniz.web.asgi:app", factory=True, workers=settings.workers, **options
        )
        sockets = [listening_socket(settings.host, settings.port)]
        if "target" in inspect.signature(Multiprocess.__init__).parameters:  # uvicorn < 0.31
            Multiprocess(config, target=uvicorn.Server(config).run, sockets=sockets).run()
        else:
            Multiprocess(config, sockets=sockets).run()
    else:
        uvicorn.run(settings.build_app(), **options)


__all__ = ["serve"]
