"""``leibniz catalog`` — the Ritter-Katalog crosswalk CLI (Phase A3).

Three subcommands:

* ``leibniz catalog scrape`` — fetch/parse katalog queries → ``katalog_records``.
* ``leibniz catalog crosswalk`` — match records to works → ``crosswalk``.
* ``leibniz catalog report`` — write ``reports/crosswalk.md``.

Every mutating run is recorded in ``runs`` with the git SHA (provenance, §4.5).
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from leibniz import db
from leibniz.catalog import crosswalk as crosswalk_mod
from leibniz.catalog import report as report_mod
from leibniz.catalog import scrape as scrape_mod
from leibniz.net import PoliteClient

app = typer.Typer(
    help="Join the BBAW Ritter-Katalog to our works (A3): scrape, crosswalk, report.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

DEFAULT_REPORT_PATH = Path("reports/crosswalk.md")


@app.command()
def scrape(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    cache_dir: Path = typer.Option(
        scrape_mod.DEFAULT_CACHE_DIR, "--cache", help="Raw katalog HTML cache dir."
    ),
    sample: bool = typer.Option(
        False, "--sample", help="Use the built-in cross-set sample query set."
    ),
    sign: list[str] | None = typer.Option(
        None, "--sign", help="Signature-prefix query (repeatable), e.g. 'LH 35'."
    ),
    reihe: str | None = typer.Option(None, "--reihe", help="AA series filter (with --bd)."),
    bd: str | None = typer.Option(None, "--bd", help="AA volume filter (with --reihe)."),
    q: str | None = typer.Option(None, "--q", help="Free-text global-search query."),
    volume: list[str] | None = typer.Option(
        None,
        "--volume",
        help="One AA volume's records as 'SERIES,VOLUME' (repeatable, e.g. 1,6); "
        "a capped slice is re-run by year automatically.",
    ),
    expired_volumes: bool = typer.Option(
        False,
        "--expired-volumes",
        help="Every §70-expired volume (legal.py, as of --today) — the C2 sweep.",
    ),
    today: str | None = typer.Option(None, "--today", help="ISO date for §70 expiry."),
    force: bool = typer.Option(False, "--force", help="Re-fetch even cached queries."),
    min_interval: float = typer.Option(
        1.5, "--min-interval", help="Min seconds between requests/host (SPECS §7.4)."
    ),
) -> None:
    """Scrape katalog search results into ``katalog_records`` (cache-first)."""
    queries: list[dict[str, str]] = []
    if sample:
        queries += scrape_mod.default_sample_queries()
    queries += [{"sign_ol": s} for s in (sign or [])]
    if reihe and bd:
        queries.append({"reihe": reihe, "bd": bd})
    elif reihe:
        queries.append({"reihe": reihe})
    if q:
        queries.append({"q": q})
    volumes = _volume_targets(volume, expired_volumes, today)
    if not queries and not volumes:
        console.print(
            "[yellow]Nothing to scrape — pass [cyan]--sample[/cyan], a query "
            "([cyan]--sign[/cyan] / [cyan]--reihe --bd[/cyan] / [cyan]--q[/cyan]), "
            "[cyan]--volume S,V[/cyan] or [cyan]--expired-volumes[/cyan].[/yellow]"
        )
        raise typer.Exit(code=1)

    conn = db.init_db(db_path)
    run_id = db.start_run(
        conn,
        "catalog_scrape",
        params={"queries": queries, "volumes": [f"{s},{v}" for s, v in volumes]},
        git_sha=db.git_sha(),
    )
    console.print(
        f"[bold]catalog scrape[/bold] → {len(queries)} queries, {len(volumes)} volume slices"
    )
    with (
        PoliteClient(min_interval=min_interval) as client,
        Progress(
            TextColumn("[cyan]scraping"), BarColumn(), MofNCompleteColumn(), console=console
        ) as progress,
    ):
        task = progress.add_task("scrape", total=len(queries) + len(volumes))
        stats = scrape_mod.scrape(
            conn,
            client=client,
            queries=queries,
            cache_dir=cache_dir,
            force=force,
            progress=lambda _slug, _n: progress.advance(task),
        )
        for series, vol in volumes:
            vstats = scrape_mod.scrape_volume(
                conn, client=client, series=series, volume=vol, cache_dir=cache_dir, force=force
            )
            progress.advance(task)
            console.print(
                f"  {_roman(series)},{vol}: {vstats.volume_records:,} records cite it"
                f"{' (deepened by year)' if vstats.deepened else ''}"
                f"{' ⚠ capped' if vstats.capped_queries else ''}"
            )
            stats.queries += vstats.queries
            stats.fetched += vstats.fetched
            stats.cached += vstats.cached
            stats.records += vstats.records
            stats.with_gwlb_link += vstats.with_gwlb_link
            stats.capped_queries += vstats.capped_queries
            stats.failures += vstats.failures
    db.finish_run(
        conn, run_id, n_input=stats.queries, n_ok=stats.records, n_failed=len(stats.failures)
    )
    console.print(
        f"\n[bold green]records: {stats.records:,}[/bold green] "
        f"({stats.with_gwlb_link:,} with a GWLB link) from {stats.queries} queries "
        f"(fetched {stats.fetched}, cached {stats.cached})"
    )
    if stats.capped_queries:
        console.print(
            f"[red]⚠ {len(stats.capped_queries)} queries hit the "
            f"{scrape_mod.RESULT_CAP:,}-row cap (narrow them):[/red] {stats.capped_queries}"
        )
    if stats.failures:
        console.print(f"[red]{len(stats.failures)} failures:[/red] {stats.failures[:5]}")
    console.print("Next: [cyan]leibniz catalog crosswalk[/cyan] then [cyan]... report[/cyan].")
    conn.close()


@app.command()
def crosswalk(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
) -> None:
    """Build the ``crosswalk`` from ``katalog_records`` × ``works``."""
    conn = db.init_db(db_path)
    n_records = db.count_katalog_records(conn)
    if n_records == 0:
        console.print(
            "[yellow]No katalog records — run [cyan]catalog scrape[/cyan] first.[/yellow]"
        )
        conn.close()
        raise typer.Exit(code=0)
    run_id = db.start_run(conn, "catalog_crosswalk", git_sha=db.git_sha())
    with Progress(
        TextColumn("[cyan]matching"), BarColumn(), MofNCompleteColumn(), console=console
    ) as progress:
        task = progress.add_task("crosswalk", total=n_records)
        stats = crosswalk_mod.build_crosswalk(conn, progress=lambda _rid: progress.advance(task))
    db.finish_run(conn, run_id, n_input=stats.records, n_ok=stats.records_matched)
    console.print(
        f"\n[bold green]links: {db.count_crosswalk(conn):,}[/bold green] · "
        f"records matched {stats.records_matched:,}/{stats.records:,} · "
        f"works matched {len(stats.works_matched):,}"
    )
    console.print(
        f"  by method — gwlb_link {stats.gwlb_link_matches:,} "
        f"(+{stats.gwlb_link_unresolved:,} unresolved) · shelfmark {stats.shelfmark_matches:,}"
    )
    conn.close()


def _roman(series: int) -> str:
    return {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}.get(
        series, str(series)
    )


def _volume_targets(
    volume: list[str] | None, expired_volumes: bool, today: str | None
) -> list[tuple[int, int]]:
    """Resolve ``--volume S,V`` / ``--expired-volumes`` into (series, volume) pairs."""
    targets: list[tuple[int, int]] = []
    for spec in volume or []:
        try:
            s_, v_ = (int(x) for x in spec.split(","))
        except ValueError as exc:
            raise typer.BadParameter(f"--volume expects 'SERIES,VOLUME', got {spec!r}") from exc
        targets.append((s_, v_))
    if expired_volumes:
        from datetime import date

        from leibniz.legal import expired_volumes as _expired

        t = date.fromisoformat(today) if today else date.today()
        for vol in _expired(t):
            if isinstance(vol.volume, int) and (vol.series, vol.volume) not in targets:
                targets.append((vol.series, vol.volume))
    return targets


def _latest_scrape_queries(conn) -> list[dict]:
    row = conn.execute(
        "SELECT params FROM runs WHERE stage='catalog_scrape' AND params IS NOT NULL "
        "ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return []
    try:
        return json.loads(row[0]).get("queries", [])
    except (json.JSONDecodeError, AttributeError):
        return []


@app.command()
def report(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    out: Path = typer.Option(DEFAULT_REPORT_PATH, "--out", help="Crosswalk markdown output."),
) -> None:
    """Write ``reports/crosswalk.md`` from the current store."""
    conn = db.init_db(db_path)
    data = report_mod.compute_crosswalk_report(
        conn, generated_at=db.utcnow_iso(), sample_queries=_latest_scrape_queries(conn)
    )
    conn.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_mod.render_crosswalk_report(data), encoding="utf-8")
    console.print(
        f"[bold]catalog report[/bold] → {out}\n"
        f"  works matched: {data.works_matched:,}/{data.n_works:,} "
        f"({data.works_pct:.1f}%) · records {data.records_matched:,}/{data.n_records:,}"
    )


__all__ = ["app"]
