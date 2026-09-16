"""``leibniz serve`` — run the JSON API + viewer (Phases D1/D2)."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console

from leibniz import db
from leibniz.search import open_backend
from leibniz.search.fts5 import DEFAULT_INDEX_PATH
from leibniz.search.meili import DEFAULT_MEILI_URL

console = Console()


def serve(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="Canonical SQLite store."),
    backend: str = typer.Option("fts5", "--backend", help="Search backend: fts5 | meili | none."),
    index: Path = typer.Option(DEFAULT_INDEX_PATH, "--index", help="FTS5 index file."),
    meili_url: str | None = typer.Option(None, "--meili-url", help="Meilisearch URL."),
    meili_key: str | None = typer.Option(None, "--meili-key", help="Meilisearch API key."),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    base_url: str | None = typer.Option(
        None, "--base-url", help="Public base URL for IIIF ids (default: from the request)."
    ),
    check: bool = typer.Option(
        False, "--check", help="Build the app and list routes; do not serve."
    ),
) -> None:
    """Serve the API, the IIIF manifests/annotations and the viewer."""
    from leibniz.web.api import create_app

    search = None
    if backend != "none":
        search = open_backend(
            backend,
            path=str(index),
            meili_url=meili_url or os.environ.get("MEILI_URL") or DEFAULT_MEILI_URL,
            meili_key=meili_key or os.environ.get("MEILI_MASTER_KEY"),
        )
    app = create_app(db_path, search=search, base_url=base_url)
    if check:
        for route in app.routes:
            path = getattr(route, "path", None)
            if path:
                console.print(path)
        return
    import uvicorn

    console.print(f"Serving Leibniz Legible on http://{host}:{port}  (store {db_path}, {backend})")
    uvicorn.run(app, host=host, port=port, log_level="info")


__all__ = ["serve"]
