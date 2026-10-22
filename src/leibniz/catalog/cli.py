"""``leibniz catalog`` — the Ritter-Katalog crosswalk CLI (Phase A3).

Three subcommands:

* ``leibniz catalog scrape`` — fetch/parse katalog queries → ``katalog_records``.
* ``leibniz catalog crosswalk`` — match records to works → ``crosswalk``.
* ``leibniz catalog report`` — write ``reports/crosswalk.md``.
* ``leibniz catalog letters`` — Bodemann's letters from correspSearch (CC BY 4.0)
  → the letters file the web application reads (who, when, where per letter).
* ``leibniz catalog import-access`` — the whole Arbeitskatalog from the
  Arbeitsstelle's Access export (A3b): a dry run compares every record the
  store holds with the export, key by key; ``--write`` replaces
  ``katalog_records`` and rebuilds the crosswalk.
* ``leibniz catalog holdings`` — ``reports/holdings.md``: records by holding
  institution, digitised copies by domain, the GWLB works with and without
  records.

Every mutating run is recorded in ``runs`` with the git SHA (provenance, §4.5).
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from leibniz import db
from leibniz.catalog import arbeitskatalog as access_mod
from leibniz.catalog import crosswalk as crosswalk_mod
from leibniz.catalog import holdings as holdings_mod
from leibniz.catalog import letters as letters_mod
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
DEFAULT_HOLDINGS_PATH = Path("reports/holdings.md")
DEFAULT_CSV_DIR = Path("data/external/arbeitskatalog/csv")


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


@app.command()
def letters(
    db_path: Path = typer.Option(
        db.DEFAULT_DB_PATH, "--db", help="The store the web application serves (for --out)."
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="The letters file (env LEIBNIZ_LETTERS_PATH; default letters.json beside the store).",
    ),
    cache_dir: Path = typer.Option(
        Path("data/cache/correspsearch"),
        "--cache",
        help="Where the API pages are kept; a run resumes from them.",
    ),
    min_interval: float = typer.Option(1.0, "--min-interval", help="Seconds between requests."),
) -> None:
    """Fetch Bodemann's catalogue of the letters (1889) from correspSearch, letter by
    letter, and write the file behind the site's letters: who wrote to whom, when and
    from where, filed by LBr convolute. CC BY 4.0 (correspSearch, BBAW; data: Portal
    Der deutsche Brief im 18. Jahrhundert). About 1,550 requests at one a second."""
    target = out or letters_mod.letters_path_for(db_path)
    with (
        PoliteClient(min_interval=min_interval) as client,
        Progress(
            TextColumn("[cyan]correspSearch"), BarColumn(), MofNCompleteColumn(), console=console
        ) as progress,
    ):
        task = progress.add_task("pages", total=None)

        def advance(n: int, total: int) -> None:
            progress.update(task, completed=n, total=total)

        found = letters_mod.harvest(client.get_bytes, cache_dir, progress=advance)
    index = letters_mod.LettersIndex(found, letters_mod.built_now())
    index.write(target)
    placed = sum(1 for ltr in found if ltr.convolute)
    console.print(
        f"{len(found):,} letters ({placed:,} filed under a convolute, "
        f"{len(index.convolutes):,} convolutes) → {target}. Restart the web application "
        "to show them."
    )


@app.command("import-access")
def import_access(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    csv_dir: Path = typer.Option(
        DEFAULT_CSV_DIR,
        "--csv-dir",
        help="The export's CSV files (ritter.csv and the side tables).",
    ),
    export_date: str = typer.Option(
        ...,
        "--export-date",
        help="The date of the Access export (ISO), recorded with the run and shown on the "
        "site as the catalogue's refresh date.",
    ),
    write: bool = typer.Option(
        False,
        "--write/--dry-run",
        help="Replace katalog_records by the export and rebuild the crosswalk. Default: the "
        "dry run, which compares and writes nothing.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Write although the mapping is not settled on this store's records (the "
        "operator's call, after reading the table).",
    ),
    report: Path | None = typer.Option(
        None, "--report", help="Also write the agreement table (Markdown) to this file."
    ),
) -> None:
    """Import the whole Arbeitskatalog from the Arbeitsstelle's Access export (A3b).

    The dry run (the default) maps every row of ritter.csv to a record, compares each
    record the store already holds with the export's row of the same id, key by key,
    and prints the agreement table; it also checks that every record the ground truth
    and the crosswalk reference exists in the export. With --write, after the operator's
    backup and go, it replaces katalog_records by record_id (every row of the export;
    idempotent), rebuilds the crosswalk (gwlb_link first, shelfmark second) and reports
    records per work, works without a record, and the records whose URL_Ms points
    outside the GWLB.
    """
    try:
        export = access_mod.read_export(csv_dir)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(
        f"[bold]catalog import-access[/bold] ← {csv_dir}: "
        + ", ".join(f"{name} {n:,}" for name, n in export.counts.items())
    )
    records = access_mod.records_from_export(export)
    by_id = {r.record_id: r for r in records}
    console.print(f"  {len(records):,} rows mapped to records")

    conn = db.init_db(db_path)
    try:
        comparison = access_mod.compare_records(db.iter_katalog_records(conn), by_id, export.ritter)
        table = access_mod.render_comparison(comparison)
        console.print(table, markup=False, highlight=False)
        if report is not None:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(table + "\n", encoding="utf-8")
            console.print(f"  agreement table → {report}")
        missing = access_mod.missing_references(conn, set(by_id))
        target = {r.old_id: r.new_id for r in comparison.remapped}
        for rid in missing.get("crosswalk", []):
            # the rebuild links the export's record under its new id, or drops the link
            where = target.get(rid)
            console.print(
                f"  crosswalk: record {rid} is "
                + (
                    f"carried by the export as {where}; its links are rebuilt under that id"
                    if where
                    else "not in the export; its links are dropped by the rebuild"
                )
            )
        if missing.get("gt_lines"):
            ids = missing["gt_lines"]
            shown = ", ".join(
                f"{rid} (→ {target[rid]})" if target.get(rid) else rid for rid in ids[:50]
            ) + (" …" if len(ids) > 50 else "")
            console.print(
                f"[red]STOP: {len(ids):,} record id(s) the ground truth (gt_lines.record_id) "
                f"references are not in the export:[/red] {shown}"
            )
            console.print("[red]Nothing written.[/red]")
            raise typer.Exit(code=1)
        console.print("  every record id the ground truth references exists in the export")
        if not write:
            console.print(
                "[yellow]Dry run: nothing written.[/yellow] After the backup and the operator's "
                "go: the same command with [cyan]--write[/cyan]."
            )
            return
        if not comparison.settled and not force:
            console.print(
                "[red]The mapping is not settled on this store's records (the table above); "
                "nothing written. Pass --force to write anyway.[/red]"
            )
            raise typer.Exit(code=1)
        with Progress(
            TextColumn("[cyan]crosswalk"), BarColumn(), MofNCompleteColumn(), console=console
        ) as progress:
            task = progress.add_task("crosswalk", total=len(records))
            stats = access_mod.write_import(
                conn,
                records,
                export_date=export_date,
                csv_dir=csv_dir,
                git_sha=db.git_sha(),
                progress=lambda _rid: progress.advance(task),
                remapped=comparison.remapped,
            )
        console.print(access_mod.render_import_stats(stats), markup=False, highlight=False)
        console.print(
            "Next: [cyan]leibniz catalog holdings --db …[/cyan] and "
            "[cyan]leibniz catalog report --db …[/cyan]; then the serving copy and the index "
            "rebuild (the catalogue's titles are indexed)."
        )
    finally:
        conn.close()


@app.command()
def holdings(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    csv_dir: Path | None = typer.Option(
        None,
        "--csv-dir",
        help="Render from the export alone (no store): the records' side only; the works "
        "section waits for the import.",
    ),
    export_date: str | None = typer.Option(
        None, "--export-date", help="With --csv-dir: the export's date, for the report's header."
    ),
    out: Path = typer.Option(DEFAULT_HOLDINGS_PATH, "--out", help="Holdings markdown output."),
) -> None:
    """Write ``reports/holdings.md``: the Arbeitskatalog's records by holding institution,
    the digitised copies by the domain of their link, and the GWLB works with and without
    catalogue records."""
    generated_at = db.utcnow_iso()
    if csv_dir is not None:
        export = access_mod.read_export(csv_dir)
        records = access_mod.records_from_export(export)
        when = f" of {export_date}" if export_date else ""
        data = holdings_mod.holdings_from_records(
            records, generated_at=generated_at, source=f"the Arbeitskatalog export{when}"
        )
    else:
        conn = db.init_db(db_path)
        try:
            data = holdings_mod.holdings_from_store(conn, generated_at=generated_at)
        finally:
            conn.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(holdings_mod.render_holdings_md(data), encoding="utf-8")
    console.print(
        f"[bold]catalog holdings[/bold] → {out}\n"
        f"  {data.records:,} records · {len(data.by_holding):,} holdings · "
        f"{data.with_url:,} with a digitised copy · works "
        + (
            f"{data.works_with_records:,}/{data.works:,} with records"
            if data.works is not None
            else "(not from the export alone)"
        )
    )
