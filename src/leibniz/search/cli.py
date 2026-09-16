"""``leibniz index`` — build and query the search index (Phase D1).

Subcommands:

* ``leibniz index build``  — (re)build the page index from the store
  (``--backend fts5`` writes ``data/search.sqlite``; ``--backend meili`` loads a
  Meilisearch instance). Records corpus statistics for ``/api/stats``.
* ``leibniz index status`` — build metadata + document count.
* ``leibniz index query``  — run a query from the shell (a debugging aid).
"""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from leibniz import db
from leibniz.search import open_backend
from leibniz.search.backend import SearchQuery
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import DEFAULT_INDEX_PATH
from leibniz.search.meili import DEFAULT_MEILI_URL

app = typer.Typer(help="Search index (D1): SQLite FTS5 or Meilisearch.", no_args_is_help=True)
console = Console()

DB_OPT = typer.Option(db.DEFAULT_DB_PATH, "--db", help="Path to the canonical SQLite store.")
BACKEND_OPT = typer.Option("fts5", "--backend", help="fts5 (single file) or meili (server).")
INDEX_OPT = typer.Option(DEFAULT_INDEX_PATH, "--index", help="FTS5 index file (fts5 backend).")
MEILI_URL_OPT = typer.Option(None, "--meili-url", help="Meilisearch URL (env MEILI_URL).")
MEILI_KEY_OPT = typer.Option(
    None, "--meili-key", help="Meilisearch API key (env MEILI_MASTER_KEY)."
)


def _backend(backend: str, index: Path, meili_url: str | None, meili_key: str | None):
    return open_backend(
        backend,
        path=str(index),
        meili_url=meili_url or os.environ.get("MEILI_URL") or DEFAULT_MEILI_URL,
        meili_key=meili_key or os.environ.get("MEILI_MASTER_KEY"),
    )


@app.command()
def build(
    db_path: Path = DB_OPT,
    backend: str = BACKEND_OPT,
    index: Path = INDEX_OPT,
    meili_url: str | None = MEILI_URL_OPT,
    meili_key: str | None = MEILI_KEY_OPT,
    set_name: str | None = typer.Option(None, "--set", help="Index one OAI set only."),
    work: str | None = typer.Option(None, "--work", help="Index one work only."),
    limit: int | None = typer.Option(None, "--limit", help="Cap the number of pages (dev)."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Skip the corpus statistics scan."),
) -> None:
    """(Re)build the search index from the store."""
    be = _backend(backend, index, meili_url, meili_key)
    conn = db.init_db(db_path)
    try:
        meta = {"db": str(db_path), "git_sha": db.git_sha()}
        if not no_stats:
            console.print("Computing corpus statistics …")
            meta["stats"] = corpus_stats(conn)
        console.print(f"Indexing pages into [cyan]{be.name}[/cyan] …")
        n = be.rebuild(
            iter_page_docs(conn, set_name=set_name, work_id=work, limit=limit), meta=meta
        )
    finally:
        conn.close()
    console.print(f"[green]Indexed {n:,} pages[/green] ({be.name}).")


@app.command()
def status(
    backend: str = BACKEND_OPT,
    index: Path = INDEX_OPT,
    meili_url: str | None = MEILI_URL_OPT,
    meili_key: str | None = MEILI_KEY_OPT,
) -> None:
    """Print the index's build metadata and document count."""
    be = _backend(backend, index, meili_url, meili_key)
    meta = be.meta()
    console.print(f"backend: {be.name}   documents: {be.count():,}")
    for k in ("built_at", "n_docs", "git_sha", "db"):
        if k in meta:
            console.print(f"{k}: {meta[k]}")
    stats = meta.get("stats") or {}
    if stats:
        console.print(
            f"corpus: {stats.get('works', 0):,} works · {stats.get('pages', 0):,} pages · "
            f"{stats.get('pages_recognized', 0):,} recognised · {stats.get('lines', 0):,} lines"
        )


@app.command()
def query(
    q: str = typer.Argument(..., help="Query text."),
    backend: str = BACKEND_OPT,
    index: Path = INDEX_OPT,
    meili_url: str | None = MEILI_URL_OPT,
    meili_key: str | None = MEILI_KEY_OPT,
    set_name: str | None = typer.Option(None, "--set"),
    lang: str | None = typer.Option(None, "--lang"),
    stratum: str | None = typer.Option(None, "--stratum"),
    min_conf: float | None = typer.Option(None, "--min-conf"),
    limit: int = typer.Option(10, "--limit"),
) -> None:
    """Run a query and print the hits."""
    be = _backend(backend, index, meili_url, meili_key)
    res = be.search(
        SearchQuery(
            q=q, set_name=set_name, lang=lang, stratum=stratum, min_conf=min_conf, limit=limit
        )
    )
    console.print(f"{res.total:,} hits ({res.backend}, {res.took_ms} ms)")
    table = Table(show_lines=False)
    for col in ("page", "work / folio", "conf", "snippet"):
        table.add_column(col)
    for h in res.hits:
        table.add_row(
            h.page_id,
            f"{h.title or h.work_id} · {h.label or h.seq}",
            f"{h.mean_conf:.2f}" if h.mean_conf is not None else "—",
            h.snippet.replace("<mark>", "[bold]").replace("</mark>", "[/bold]"),
        )
    console.print(table)


__all__ = ["app"]
