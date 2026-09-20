"""``leibniz images`` — the local image-cache CLI (Phase A2).

Four subcommands:

* ``leibniz images pages`` — derive ``pages`` rows (delivery URLs) from the
  cached OAI METS, offline (the deferred A1 page population).
* ``leibniz images fetch`` — download delivery derivatives (resumable, polite).
* ``leibniz images verify`` — re-check the cache and report gaps.
* ``leibniz images stats`` — roll up counts/bytes/dimensions into census.md.
* ``leibniz images thumbs`` — derive thumbnails for the image mirror.
* ``leibniz images check-mirror`` — sample the mirror after an upload.

Every mutating run on the store is recorded in ``runs`` with the git SHA
(provenance, §4.5); thumbnails are derived files outside the store.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from leibniz import db
from leibniz.harvest.oai import DEFAULT_CACHE_DIR as OAI_CACHE_DIR
from leibniz.images import fetch as fetch_mod
from leibniz.images import pages as pages_mod
from leibniz.images import thumbs as thumbs_mod
from leibniz.net import PoliteClient

app = typer.Typer(
    help="Cache page-image delivery derivatives locally (A2): derive, fetch, verify, stats.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

DEFAULT_CENSUS_PATH = Path("reports/census.md")


def _object_ids_for(conn, set_name: str | None, works: list[str] | None) -> set[str] | None:
    """Resolve a ``--set``/``--work`` selection to a set of object ids (or None=all)."""
    if works:
        return set(works)
    if set_name:
        return {w.gwlb_object_id for w in db.iter_works(conn, set_name=set_name)}
    return None


@app.command()
def pages(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    oai_cache: Path = typer.Option(OAI_CACHE_DIR, "--oai-cache", help="Cached OAI XML dir."),
    set_: str | None = typer.Option(None, "--set", "-s", help="Only works in this primary set."),
    work: list[str] | None = typer.Option(None, "--work", "-w", help="Only these object id(s)."),
) -> None:
    """Populate ``pages`` (delivery URLs) from the cached METS ``fileSec`` — offline."""
    conn = db.init_db(db_path)
    if not any(Path(oai_cache).glob("*/page_*.xml")):
        console.print(
            f"[red]No cached OAI XML under {oai_cache} — run "
            "[cyan]leibniz harvest oai[/cyan] first.[/red]"
        )
        conn.close()
        raise typer.Exit(code=1)
    include = _object_ids_for(conn, set_, work)
    run_id = db.start_run(
        conn, "images_pages", params={"set": set_, "work": work}, git_sha=db.git_sha()
    )
    with Progress(
        TextColumn("[cyan]deriving pages"), BarColumn(), MofNCompleteColumn(), console=console
    ) as progress:
        task = progress.add_task("pages", total=len(include) if include is not None else None)
        stats = pages_mod.populate_pages_from_cache(
            conn,
            cache_dir=oai_cache,
            include=include,
            progress=lambda _oid, _n: progress.advance(task),
        )
    db.finish_run(conn, run_id, n_input=stats.works, n_ok=stats.pages)
    console.print(
        f"\n[bold green]pages: {stats.pages:,}[/bold green] from {stats.works:,} works "
        f"(static {stats.static_pages:,} · iiif {stats.iiif_pages:,}; "
        f"{stats.zero_page_works:,} zero-page works)"
    )
    conn.close()


@app.command()
def fetch(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    images_root: Path = typer.Option(
        fetch_mod.DEFAULT_IMAGES_ROOT, "--images", help="Local image cache root."
    ),
    set_: str | None = typer.Option(None, "--set", "-s", help="Only works in this primary set."),
    work: list[str] | None = typer.Option(None, "--work", "-w", help="Only these object id(s)."),
    limit: int | None = typer.Option(None, "--limit", help="Cap pages downloaded this run."),
    redo: bool = typer.Option(False, "--redo", help="Re-download pages already cached."),
    min_interval: float = typer.Option(
        1.0, "--min-interval", help="Min seconds between requests/host (SPECS §7.4)."
    ),
) -> None:
    """Download delivery derivatives into the local cache (resumable, polite)."""
    conn = db.init_db(db_path)
    target = db.count_fetch_targets(conn, set_name=set_)
    if target == 0:
        console.print(
            "[yellow]No fetch targets — run [cyan]leibniz images pages[/cyan] first "
            "(or widen --set/--work).[/yellow]"
        )
        conn.close()
        raise typer.Exit(code=0)
    run_id = db.start_run(
        conn,
        "images_fetch",
        params={
            "set": set_,
            "work": work,
            "limit": limit,
            "redo": redo,
            "images_root": str(images_root),  # the store's only record of where the cache is
        },
        git_sha=db.git_sha(),
    )
    console.print(f"[bold]images fetch[/bold] → up to {target:,} target pages")
    stats = fetch_mod.FetchStats()
    try:
        with (
            PoliteClient(min_interval=min_interval) as client,
            Progress(
                TextColumn("[cyan]fetching"), BarColumn(), MofNCompleteColumn(), console=console
            ) as progress,
        ):
            task = progress.add_task("fetch", total=limit or target)
            stats = fetch_mod.fetch_images(
                conn,
                client=client,
                images_root=images_root,
                set_name=set_,
                work_ids=work or None,
                redo=redo,
                limit=limit,
                progress=lambda _pid, _ok: progress.advance(task),
            )
    finally:
        db.finish_run(
            conn,
            run_id,
            n_input=stats.considered,
            n_ok=stats.fetched,
            n_failed=len(stats.failures),
        )
    console.print(
        f"\n[bold green]fetched: {stats.fetched:,}[/bold green] "
        f"({fetch_mod.human_bytes(stats.bytes)}) · skipped {stats.skipped:,} already cached"
    )
    if stats.failures:
        console.print(f"[red]{len(stats.failures)} failures:[/red] {stats.failures[:5]}")
    console.print("Run [cyan]leibniz images stats[/cyan] to update reports/census.md.")
    conn.close()


@app.command()
def verify(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    images_root: Path = typer.Option(
        fetch_mod.DEFAULT_IMAGES_ROOT, "--images", help="Local image cache root."
    ),
    set_: str | None = typer.Option(None, "--set", "-s", help="Only works in this primary set."),
    work: list[str] | None = typer.Option(None, "--work", "-w", help="Only these object id(s)."),
    deep: bool = typer.Option(False, "--deep", help="Re-hash file bytes (slower, thorough)."),
) -> None:
    """Re-check the cache against the manifest and report gaps."""
    conn = db.init_db(db_path)
    stats = fetch_mod.verify_images(
        conn,
        images_root=images_root,
        set_name=set_,
        work_ids=work or None,
        deep=deep,
    )
    conn.close()
    console.print(
        f"[bold]verify[/bold] → {stats.ok:,}/{stats.recorded:,} OK · "
        f"{stats.unfetched:,} still uncached"
    )
    for label, ids in (
        ("missing file", stats.missing_file),
        ("size mismatch", stats.size_mismatch),
        ("checksum mismatch", stats.checksum_mismatch),
    ):
        if ids:
            console.print(f"[red]{len(ids)} {label}:[/red] {ids[:5]}")
    if not (stats.missing_file or stats.size_mismatch or stats.checksum_mismatch):
        console.print("[green]No corruption detected.[/green]")


@app.command()
def stats(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    out: Path = typer.Option(DEFAULT_CENSUS_PATH, "--out", help="Census markdown to append to."),
) -> None:
    """Roll up cache counts/bytes/dimensions and append them to reports/census.md."""
    conn = db.init_db(db_path)
    data = fetch_mod.image_stats(conn)
    conn.close()
    section = fetch_mod.render_stats_section(data, generated_at=db.utcnow_iso())
    fetch_mod.append_stats_to_census(out, section)
    console.print(
        f"[bold]images stats[/bold] → {out}\n"
        f"  cached {data.fetched:,}/{data.fetch_targets:,} pages · "
        f"{fetch_mod.human_bytes(data.total_bytes)}"
    )


__all__ = ["app"]


@app.command()
def thumbs(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    images_root: Path = typer.Option(
        fetch_mod.DEFAULT_IMAGES_ROOT, "--images", help="Image cache root."
    ),
    out: Path = typer.Option(
        thumbs_mod.DEFAULT_THUMBS_ROOT, "--out", help="Where the thumbnails go."
    ),
    width: int = typer.Option(thumbs_mod.DEFAULT_WIDTH, "--width", help="Thumbnail width (px)."),
    workers: int = typer.Option(
        os.cpu_count() or 1, "--workers", help="Parallel processes (default: the cores)."
    ),
    redo: bool = typer.Option(False, "--redo", help="Rebuild thumbnails that already exist."),
) -> None:
    """Derive one thumbnail per cached page, in the cache's layout (for the mirror)."""
    conn = db.init_db(db_path)
    try:
        try:
            thumbs_mod.preflight_images_root(conn, images_root)
        except FileNotFoundError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(2) from exc
        n = len(thumbs_mod.cached_pages(conn))
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as bar:
            task = bar.add_task("thumbnails", total=n)
            stats = thumbs_mod.build_thumbnails(
                conn,
                images_root,
                out,
                width=width,
                workers=workers,
                redo=redo,
                progress=lambda _pid, _outcome: bar.advance(task),
            )
    finally:
        conn.close()
    console.print(
        f"[green]{stats.made:,} made[/green], {stats.skipped:,} already there, "
        f"{stats.missing:,} source files missing, {stats.failed:,} failed → {out}"
    )
    if stats.failures:
        console.print("failed (first 50): " + ", ".join(stats.failures))
    if stats.missing:
        console.print(
            f"[yellow]{stats.missing:,} pages the store records as cached have no file "
            f"under {images_root}[/yellow] — run `leibniz images verify` to see what the "
            "cache is missing."
        )
    raise typer.Exit(1 if (stats.failed or stats.missing) else 0)


@app.command("check-mirror")
def check_mirror(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    base_url: str = typer.Option(
        ..., "--base-url", envvar="LEIBNIZ_IMAGE_BASE_URL", help="The mirror's origin."
    ),
    sample: int = typer.Option(500, "--sample", help="Pages to check (0 = every cached page)."),
    no_thumbs: bool = typer.Option(False, "--no-thumbs", help="Skip the thumbnails."),
    as_json: bool = typer.Option(False, "--json", help="Print the report as JSON."),
) -> None:
    """HEAD a sample of cached pages on the mirror; compare sizes with the cache manifest."""
    conn = db.init_db(db_path)
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            report = thumbs_mod.check_mirror(
                conn, base_url, client=client, sample=sample, thumbs=not no_thumbs
            )
    finally:
        conn.close()
    if as_json:
        console.print_json(json.dumps(report.to_dict()))
    else:
        console.print(
            f"{report.ok:,}/{report.checked:,} images ok · {len(report.missing):,} missing · "
            f"{len(report.size_mismatch):,} size mismatches · {len(report.errors):,} errors"
        )
        if not no_thumbs:
            console.print(
                f"{report.thumbs_checked - len(report.thumbs_missing):,}/{report.thumbs_checked:,} "
                f"thumbnails ok · {len(report.thumbs_missing):,} missing"
            )
        for label, ids in (
            ("missing", report.missing),
            ("size mismatch", report.size_mismatch),
            ("errors", report.errors),
            ("thumbnails missing", report.thumbs_missing),
        ):
            if ids:
                console.print(
                    f"  {label}: " + ", ".join(ids[:20]) + (" …" if len(ids) > 20 else "")
                )
        console.print(
            "[green]mirror complete[/green]" if report.complete else "[red]mirror incomplete[/red]"
        )
    raise typer.Exit(0 if report.complete else 1)
