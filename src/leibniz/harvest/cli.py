"""``leibniz harvest`` — the OAI/IIIF harvest CLI (Phase A1).

Three subcommands:

* ``leibniz harvest oai`` — ListRecords over the Leibniz sets → ``works``.
* ``leibniz harvest manifests`` — IIIF manifests → ``pages`` (slice-able).
* ``leibniz harvest census`` — recompute ``reports/census.md`` from the store.

All network access goes through the polite client (SPECS §7.4); every run is
recorded in ``runs`` with the git SHA that produced it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from leibniz import db
from leibniz.harvest import census as census_mod
from leibniz.harvest import manifests as manifests_mod
from leibniz.harvest import oai as oai_mod
from leibniz.net import PoliteClient

app = typer.Typer(
    help="Harvest OAI-PMH + IIIF into the inventory and compute the census (A1).",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

DEFAULT_CENSUS_PATH = Path("reports/census.md")


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


@app.command()
def oai(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    cache_dir: Path = typer.Option(
        oai_mod.DEFAULT_CACHE_DIR, "--cache", help="Raw OAI XML cache dir."
    ),
    sets: list[str] | None = typer.Option(
        None, "--set", "-s", help="OAI set(s) to harvest; default all five Leibniz sets."
    ),
    force: bool = typer.Option(False, "--force", help="Re-fetch even cached pages."),
    limit_pages: int | None = typer.Option(
        None, "--limit-pages", help="Cap pages per set (dev slice)."
    ),
    min_interval: float = typer.Option(
        1.0, "--min-interval", help="Min seconds between requests/host."
    ),
) -> None:
    """Harvest OAI-PMH ListRecords into ``works`` (cache-first, resumable)."""
    target_sets = tuple(sets) if sets else oai_mod.LEIBNIZ_SETS
    conn = db.init_db(db_path)
    run_id = db.start_run(
        conn,
        "harvest_oai",
        params={"sets": list(target_sets), "force": force, "limit_pages": limit_pages},
        git_sha=_git_sha(),
    )
    console.print(f"[bold]harvest oai[/bold] → sets: {', '.join(target_sets)}")
    try:
        with (
            PoliteClient(min_interval=min_interval) as client,
            Progress(
                TextColumn("[cyan]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console,
            ) as progress,
        ):
            tasks: dict[str, int] = {}

            def cb(set_name: str, done: int, total: int | None) -> None:
                if set_name not in tasks:
                    tasks[set_name] = progress.add_task(set_name, total=total)
                progress.update(tasks[set_name], completed=done, total=total)

            stats = oai_mod.harvest_oai(
                conn,
                client=client,
                sets=target_sets,
                cache_dir=cache_dir,
                force=force,
                limit_pages=limit_pages,
                progress=cb,
            )
    except Exception:
        db.finish_run(conn, run_id, n_ok=db.count_works(conn))
        conn.close()
        raise

    n_works = db.count_works(conn)
    total_pages = census_mod.compute_census(conn, generated_at="").n_pages
    db.finish_run(conn, run_id, n_input=None, n_ok=n_works)

    console.print()
    for s in stats:
        console.print(
            f"  {s.set_name}: {s.records} records "
            f"(fetched {s.pages_fetched}, cached {s.pages_read} pages)"
        )
    console.print(
        f"\n[bold green]works: {n_works:,}[/bold green] · "
        f"[bold green]page images: {total_pages:,}[/bold green]"
    )
    console.print("Run [cyan]leibniz harvest census[/cyan] to (re)write reports/census.md.")
    conn.close()


@app.command()
def manifests(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    cache_dir: Path = typer.Option(
        manifests_mod.DEFAULT_CACHE_DIR, "--cache", help="Raw manifest cache dir."
    ),
    set_: str | None = typer.Option(None, "--set", "-s", help="Only works in this primary set."),
    work: list[str] | None = typer.Option(None, "--work", "-w", help="Only these object id(s)."),
    limit: int | None = typer.Option(None, "--limit", help="Cap number of works (dev slice)."),
    force: bool = typer.Option(False, "--force", help="Re-fetch even cached manifests."),
    min_interval: float = typer.Option(
        1.0, "--min-interval", help="Min seconds between requests/host."
    ),
) -> None:
    """Harvest IIIF manifests into ``pages`` (cache-first). Slice with filters."""
    conn = db.init_db(db_path)
    if work:
        works = [w for oid in work if (w := db.get_work(conn, oid)) is not None]
    else:
        works = list(db.iter_works(conn, set_name=set_))
    if limit is not None:
        works = works[:limit]
    if not works:
        console.print(
            "[yellow]No matching works — run harvest oai first, or widen filters.[/yellow]"
        )
        conn.close()
        raise typer.Exit(code=0)

    run_id = db.start_run(
        conn,
        "harvest_manifests",
        params={"set": set_, "n_works": len(works), "force": force},
        git_sha=_git_sha(),
    )
    console.print(f"[bold]harvest manifests[/bold] → {len(works):,} works")
    with (
        PoliteClient(min_interval=min_interval) as client,
        Progress(
            TextColumn("manifests"), BarColumn(), MofNCompleteColumn(), console=console
        ) as progress,
    ):
        task = progress.add_task("manifests", total=len(works))
        stats = manifests_mod.harvest_manifests(
            conn,
            client=client,
            works=works,
            cache_dir=cache_dir,
            force=force,
            progress=lambda _oid, _n: progress.advance(task),
        )
    db.finish_run(
        conn,
        run_id,
        n_input=stats.works,
        n_ok=stats.works - len(stats.failures),
        n_failed=len(stats.failures),
    )
    console.print(
        f"\n[bold green]pages: {stats.pages:,}[/bold green] from {stats.works:,} works "
        f"(fetched {stats.fetched}, cached {stats.cached})"
    )
    if stats.count_mismatches:
        console.print(
            f"[yellow]{len(stats.count_mismatches)} works: manifest canvas count "
            "≠ METS n_canvases (see runs log).[/yellow]"
        )
    if stats.failures:
        console.print(f"[red]{len(stats.failures)} failures:[/red] {stats.failures[:5]}")
    conn.close()


@app.command()
def census(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    out: Path = typer.Option(DEFAULT_CENSUS_PATH, "--out", help="Census markdown output path."),
) -> None:
    """Recompute ``reports/census.md`` from the current store."""
    conn = db.init_db(db_path)
    data = census_mod.compute_census(conn, generated_at=db.utcnow_iso())
    conn.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(census_mod.render_census(data), encoding="utf-8")
    band = "within" if data.in_gate_band else "OUTSIDE"
    console.print(
        f"[bold]census[/bold] → {out}\n"
        f"  works: {data.n_works:,} · page images: {data.n_pages:,} "
        f"([{'green' if data.in_gate_band else 'red'}]{band} the ~150–250k band[/])"
    )


__all__ = ["app"]
