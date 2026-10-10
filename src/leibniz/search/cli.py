"""``leibniz index`` — build and query the search index (Phase D1).

Subcommands:

* ``leibniz index build``  — (re)build the page index from the store
  (``--backend fts5`` writes ``data/search.sqlite``; ``--backend meili`` loads a
  Meilisearch instance). Records corpus statistics for ``/api/stats``.
* ``leibniz index status`` — build metadata + document count.
* ``leibniz index query``  — run a query from the shell (a debugging aid).
* ``leibniz index bench``  — search latency (p50/p95) against a running
  ``leibniz serve``, judged against SPECS §3.3's p95 < 500 ms.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

from leibniz import db
from leibniz.images import twins as twins_mod
from leibniz.search import open_backend
from leibniz.search.backend import SearchQuery
from leibniz.search.bench import DEFAULT_QUERIES, DEFAULT_RATE, bench_search
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import DEFAULT_INDEX_PATH
from leibniz.search.meili import DEFAULT_INDEX_UID, DEFAULT_MEILI_URL

app = typer.Typer(help="Search index (D1): SQLite FTS5 or Meilisearch.", no_args_is_help=True)
console = Console()

DB_OPT = typer.Option(db.DEFAULT_DB_PATH, "--db", help="Path to the canonical SQLite store.")
BACKEND_OPT = typer.Option("fts5", "--backend", help="fts5 (single file) or meili (server).")
INDEX_OPT = typer.Option(DEFAULT_INDEX_PATH, "--index", help="FTS5 index file (fts5 backend).")
MEILI_URL_OPT = typer.Option(None, "--meili-url", help="Meilisearch URL (env MEILI_URL).")
MEILI_KEY_OPT = typer.Option(
    None, "--meili-key", help="Meilisearch API key (env MEILI_MASTER_KEY, else MEILI_API_KEY)."
)
MEILI_INDEX_OPT = typer.Option(
    None,
    "--meili-index",
    help=f"Meilisearch index uid (env LEIBNIZ_MEILI_INDEX; default {DEFAULT_INDEX_UID}).",
)


def _backend(
    backend: str,
    index: Path,
    meili_url: str | None,
    meili_key: str | None,
    meili_index: str | None = None,
):
    return open_backend(
        backend,
        path=str(index),
        meili_url=meili_url or os.environ.get("MEILI_URL") or DEFAULT_MEILI_URL,
        meili_key=meili_key
        or os.environ.get("MEILI_MASTER_KEY")
        or os.environ.get("MEILI_API_KEY"),
        meili_index=meili_index or os.environ.get("LEIBNIZ_MEILI_INDEX") or DEFAULT_INDEX_UID,
    )


@app.command()
def build(
    db_path: Path = DB_OPT,
    backend: str = BACKEND_OPT,
    index: Path = INDEX_OPT,
    meili_url: str | None = MEILI_URL_OPT,
    meili_key: str | None = MEILI_KEY_OPT,
    meili_index: str | None = MEILI_INDEX_OPT,
    set_name: str | None = typer.Option(None, "--set", help="Index one OAI set only."),
    work: str | None = typer.Option(None, "--work", help="Index one work only."),
    limit: int | None = typer.Option(None, "--limit", help="Cap the number of pages (dev)."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Skip the corpus statistics scan."),
    twins_path: Path | None = typer.Option(
        None,
        "--twins",
        help="Where to write the scans registered twice (env LEIBNIZ_TWINS_PATH; default "
        "beside the index, see `leibniz images twins`). Written by a full build only.",
    ),
) -> None:
    """(Re)build the search index from the store.

    Scans the library registered under two folio labels are indexed once — a
    spread as its two halves, any other twin on one page — and the groups are
    written beside the index for the web application (`--twins`)."""
    be = _backend(backend, index, meili_url, meili_key, meili_index)
    uid = meili_index or os.environ.get("LEIBNIZ_MEILI_INDEX") or DEFAULT_INDEX_UID
    target = twins_path or twins_mod.twins_path_for(backend, index, db_path, uid)
    full = set_name is None and work is None and limit is None
    groups: list[twins_mod.TwinGroup] = []
    twin_stats = twins_mod.TwinStats()
    indexed = {"pages": 0, "lines": 0}
    conn = db.init_db(db_path)
    try:
        meta: dict = {"db": str(db_path), "git_sha": db.git_sha()}
        if not no_stats:
            console.print("Computing corpus statistics …")
            meta["stats"] = corpus_stats(conn)

        def docs():
            for doc in iter_page_docs(
                conn,
                set_name=set_name,
                work_id=work,
                limit=limit,
                twins_out=groups,
                twin_stats=twin_stats,
            ):
                indexed["pages"] += 1
                indexed["lines"] += doc.n_lines
                yield doc

        def final_meta() -> dict:
            # what only the documents can tell: the lines each scan carries once
            if "stats" in meta and full:
                meta["stats"].update(
                    twins_mod.dedup_stats(meta["stats"], twin_stats, indexed["lines"])
                )
            return meta

        console.print(f"Indexing pages into [cyan]{be.name}[/cyan] …")
        n = be.rebuild(docs(), meta=final_meta)
    finally:
        conn.close()
    console.print(f"[green]Indexed {n:,} pages[/green] ({be.name}).")
    found = twin_stats.to_dict()
    console.print(
        f"Scans registered more than once: {found['groups']:,} confirmed "
        f"({found['spreads']:,} spreads, {found['folds']:,} folded), "
        f"{found['unconfirmed']:,} candidates left as they are."
    )
    if full:
        built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        written = twins_mod.TwinIndex(groups, found, built).write(target)
        console.print(f"Twins written to {written} — restart the web application to use them.")
    else:
        console.print("[yellow]A partial build: the twins file is left as it was.[/yellow]")


@app.command()
def settings(
    meili_url: str | None = MEILI_URL_OPT,
    meili_key: str | None = MEILI_KEY_OPT,
    meili_index: str | None = MEILI_INDEX_OPT,
) -> None:
    """Apply the code's Meilisearch settings (ranking, typo rules) to the live index
    without rebuilding it. A change of document fields still needs `index build`."""
    from leibniz.search.meili import SETTINGS

    be = _backend("meili", Path(DEFAULT_INDEX_PATH), meili_url, meili_key, meili_index)
    task = be.push_settings()
    console.print(
        f"[green]settings applied[/green] to {be.index_uid} (task {task.get('uid')}, "
        f"{task.get('status')}): ranking {SETTINGS['rankingRules']}"
    )


@app.command()
def status(
    backend: str = BACKEND_OPT,
    index: Path = INDEX_OPT,
    meili_url: str | None = MEILI_URL_OPT,
    meili_key: str | None = MEILI_KEY_OPT,
    meili_index: str | None = MEILI_INDEX_OPT,
) -> None:
    """Print the index's build metadata and document count."""
    be = _backend(backend, index, meili_url, meili_key, meili_index)
    meta = be.meta()
    where = f" ({be.index_uid})" if hasattr(be, "index_uid") else ""
    console.print(f"backend: {be.name}{where}   documents: {be.count():,}")
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
    meili_index: str | None = MEILI_INDEX_OPT,
    set_name: str | None = typer.Option(None, "--set"),
    lang: str | None = typer.Option(None, "--lang"),
    stratum: str | None = typer.Option(None, "--stratum"),
    min_conf: float | None = typer.Option(None, "--min-conf"),
    limit: int = typer.Option(10, "--limit"),
) -> None:
    """Run a query and print the hits."""
    be = _backend(backend, index, meili_url, meili_key, meili_index)
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


@app.command()
def bench(
    url: str = typer.Option(
        "http://127.0.0.1:8000", "--url", help="Base URL of a running `leibniz serve`."
    ),
    n: int = typer.Option(200, "--n", help="Number of searches to run."),
    concurrency: int = typer.Option(1, "--concurrency", help="Parallel clients."),
    rate: float = typer.Option(
        DEFAULT_RATE,
        "--rate",
        help="Launches per second (0 = unpaced); the default stays under the app's own limit.",
    ),
    queries: Path | None = typer.Option(
        None, "--queries", help="File with one query per line (default: a built-in list)."
    ),
    limit: int = typer.Option(20, "--limit", help="Hits per search (the viewer asks for 20)."),
    as_json: bool = typer.Option(False, "--json", help="Print the result as JSON."),
) -> None:
    """Measure search latency over HTTP; exit 1 if p95 misses SPECS §3.3 (500 ms)."""
    qs: tuple[str, ...] = DEFAULT_QUERIES
    if queries is not None:
        qs = tuple(queries.read_text(encoding="utf-8").splitlines())
    with httpx.Client(base_url=url, timeout=30.0) as client:
        res = bench_search(client, qs, n=n, limit=limit, concurrency=concurrency, rate=rate)
    if as_json:
        console.print_json(json.dumps(res))
    else:
        w, b = res["wall_ms"], res["backend_ms"]
        console.print(
            f"{res['ok']}/{res['n']} searches ok, {res['errors']} errors, "
            f"{res['rate_limited']} rate-limited (429), concurrency {res['concurrency']}, "
            f"{res['rate']:g}/s pacing, {res['queries']} distinct queries"
        )
        console.print(
            f"wall clock  p50 {w['p50']:.0f} ms · p95 {w['p95']:.0f} ms · max {w['max']:.0f} ms"
        )
        console.print(
            f"backend     p50 {b['p50']:.0f} ms · p95 {b['p95']:.0f} ms · max {b['max']:.0f} ms"
        )
        verdict = "[green]PASS[/green]" if res["pass"] else "[red]FAIL[/red]"
        console.print(f"criterion   p95 < {res['criterion_p95_ms']} ms → {verdict}")
    raise typer.Exit(0 if res["pass"] else 1)


__all__ = ["app"]
