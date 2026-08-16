"""``leibniz pipeline`` — the corpus segmentation + recognition CLI (Phase C1).

Subcommands:

* ``leibniz pipeline segment``   — segment cached pages (pending → segmented),
  storing line geometry + per-page segmentation stats.
* ``leibniz pipeline recognize`` — recognise segmented pages (segmented →
  recognized), filling line text + confidence.
* ``leibniz pipeline status``    — print the corpus status histogram + per-set.
* ``leibniz pipeline report``    — (re)write ``reports/htr-v1-sample.md`` from the
  store.

``segment``/``recognize`` need the kraken+torch stack (the optional ``bench``
extra) and a local image cache; they preflight-check for kraken and exit with a
clear install hint if it is absent. ``status``/``report`` are pure DB reads and
run without the heavy stack.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Table

from leibniz import db
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT
from leibniz.pipeline import geometry
from leibniz.pipeline import report as report_mod
from leibniz.pipeline.recognize import audit_page, recognize_pages
from leibniz.pipeline.segment import segment_pages

app = typer.Typer(
    help="Corpus batch pipeline (C1): segment → recognize, resumable & idempotent.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

DEFAULT_HTR = "data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors"
DEFAULT_SEG = "data/models/philiumm-seg/blla_ft_leibniz_v1_0.4750.safetensors"
DEFAULT_REPORT = Path("reports/htr-v1-sample.md")


def _require_kraken() -> None:
    """Exit cleanly if the kraken stack (optional ``bench`` extra) is absent."""
    try:
        import kraken  # noqa: F401
    except ModuleNotFoundError:
        console.print(
            "[red]The segmentation/recognition stages need the kraken+torch stack "
            "(the optional [cyan]bench[/cyan] extra).[/red]\n"
            "Install it in the run env: [cyan]uv pip install kraken[/cyan] "
            "(and fetch the models with [cyan]leibniz bench fetch[/cyan]).\n"
            "The rest of the pipeline (status, report) runs without it."
        )
        raise typer.Exit(code=1) from None


def _parse_shard(spec: str | None) -> tuple[int, int] | None:
    """Parse ``--shard i/N`` (1-based, e.g. ``2/4``) into a 0-based ``(index, count)``.

    N parallel operators each pass a distinct ``i/N``; the work-id hash makes
    the shards disjoint and complete, so their union is exactly one full pass.
    """
    if not spec:
        return None
    try:
        i_s, n_s = spec.split("/", 1)
        i, n = int(i_s), int(n_s)
    except ValueError:
        raise typer.BadParameter(f"--shard wants 'i/N' (e.g. 2/4), got {spec!r}") from None
    if n < 1 or not (1 <= i <= n):
        raise typer.BadParameter(f"--shard index must be between 1 and N, got {spec!r}")
    return (i - 1, n)


def _set_mem_limit(gb: float) -> None:
    """Cap the process address space (POSIX ``RLIMIT_AS``).

    Under Linux overcommit a runaway allocation "succeeds" and then OOM-kills
    the machine when touched — no in-process handler ever fires (the live
    corpus run died this way). With a cap, the same allocation raises a normal
    error inside one page, which the pipeline's fault tolerance turns into a
    skip; the run itself survives.
    """
    try:
        import resource
    except ImportError:  # pragma: no cover - non-POSIX platform
        console.print("[yellow]--mem-limit-gb is unsupported on this platform; ignored.[/yellow]")
        return
    limit = int(gb * 1024**3)
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    console.print(f"[dim]address-space cap: {gb:g} GB[/dim]")


@app.command()
def segment(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    images_root: Path = typer.Option(
        DEFAULT_IMAGES_ROOT, "--images", help="Local image cache root."
    ),
    seg_model: str = typer.Option(DEFAULT_SEG, "--seg-model", help="PHILIUMM segmentation model."),
    set_: str | None = typer.Option(None, "--set", "-s", help="Only works in this primary set."),
    work: list[str] | None = typer.Option(None, "--work", "-w", help="Only these object id(s)."),
    sample: int | None = typer.Option(None, "--sample", help="Cap pages processed this run."),
    redo: bool = typer.Option(False, "--redo", help="Re-segment pages already done."),
    device: str = typer.Option("cpu", "--device", help="cpu | cuda | auto (GPU-aware)."),
    shard: str | None = typer.Option(
        None, "--shard", help="Process shard i/N of the works (e.g. 2/4) — parallel workers."
    ),
    min_lines: int = typer.Option(1, "--min-lines", help="Below this, a page is 'blank'/skipped."),
    mem_limit_gb: float | None = typer.Option(
        None,
        "--mem-limit-gb",
        help="Cap address space (GB): runaway allocs fail a page, not the box.",
    ),
) -> None:
    """Segment cached pages into line geometry + per-page segmentation stats."""
    _require_kraken()
    if mem_limit_gb:
        _set_mem_limit(mem_limit_gb)
    from leibniz.layout.segment import PageSegmenter

    conn = db.init_db(db_path)
    pending = db.count_pages_by_status(conn, "pending", set_name=set_)
    console.print(
        f"[bold]pipeline segment[/bold] — {pending:,} pending pages (set={set_ or 'all'})"
    )
    segmenter = PageSegmenter(seg_model, device=device)
    total = sample or pending
    try:
        with Progress(
            TextColumn("[cyan]segmenting"), BarColumn(), MofNCompleteColumn(), console=console
        ) as progress:
            task = progress.add_task("seg", total=total or None)
            result = segment_pages(
                conn,
                segmenter,
                model_version=Path(seg_model).stem,
                images_root=images_root,
                set_name=set_,
                work_ids=work or None,
                redo=redo,
                sample=sample,
                shard=_parse_shard(shard),
                min_lines=min_lines,
                progress=lambda _pid, _o: progress.advance(task),
            )
    except FileNotFoundError as exc:  # images-root preflight: abort, mark nothing
        console.print(f"[red]{exc}[/red]")
        conn.close()
        raise typer.Exit(code=2) from None
    console.print(
        f"\n[bold green]segmented {result.segmented:,}[/bold green] pages "
        f"({result.n_lines:,} lines, {result.mean_lines:.1f}/pg) · "
        f"skipped {result.skipped:,} · {result.seconds:.0f}s"
    )
    if result.failures:
        console.print(f"[yellow]{len(result.failures)} skips[/yellow]: {result.failures[:3]}")
    conn.close()


@app.command()
def recognize(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    images_root: Path = typer.Option(
        DEFAULT_IMAGES_ROOT, "--images", help="Local image cache root."
    ),
    htr_model: str = typer.Option(DEFAULT_HTR, "--htr-model", help="PHILIUMM HTR model."),
    seg_model: str = typer.Option(DEFAULT_SEG, "--seg-model", help="Segmentation model (cropper)."),
    set_: str | None = typer.Option(None, "--set", "-s", help="Only works in this primary set."),
    work: list[str] | None = typer.Option(None, "--work", "-w", help="Only these object id(s)."),
    sample: int | None = typer.Option(None, "--sample", help="Cap pages processed this run."),
    redo: bool = typer.Option(False, "--redo", help="Re-recognise pages already done."),
    device: str = typer.Option("cpu", "--device", help="cpu | cuda | auto (GPU-aware)."),
    shard: str | None = typer.Option(
        None, "--shard", help="Process shard i/N of the works (e.g. 2/4) — parallel workers."
    ),
    batch_size: int = typer.Option(16, "--batch-size", help="HTR batch size."),
    mem_limit_gb: float | None = typer.Option(
        None,
        "--mem-limit-gb",
        help="Cap address space (GB): runaway allocs fail a page, not the box.",
    ),
) -> None:
    """Recognise segmented pages: crop each stored line, HTR, store text + conf."""
    _require_kraken()
    if mem_limit_gb:
        _set_mem_limit(mem_limit_gb)
    from leibniz.htr.engines import KrakenEngine
    from leibniz.layout.segment import PageSegmenter

    conn = db.init_db(db_path)
    segmented = db.count_pages_by_status(conn, "segmented", set_name=set_)
    console.print(
        f"[bold]pipeline recognize[/bold] — {segmented:,} segmented pages (set={set_ or 'all'})"
    )
    cropper = PageSegmenter(seg_model, device=device)
    recognizer = KrakenEngine(htr_model, device=device, batch_size=batch_size)
    total = sample or segmented
    try:
        with Progress(
            TextColumn("[cyan]recognising"), BarColumn(), MofNCompleteColumn(), console=console
        ) as progress:
            task = progress.add_task("rec", total=total or None)
            result = recognize_pages(
                conn,
                cropper,
                recognizer,
                model_version=recognizer.version,
                images_root=images_root,
                set_name=set_,
                work_ids=work or None,
                redo=redo,
                sample=sample,
                shard=_parse_shard(shard),
                progress=lambda _pid, _o: progress.advance(task),
            )
    except FileNotFoundError as exc:  # images-root preflight: abort, mark nothing
        console.print(f"[red]{exc}[/red]")
        conn.close()
        raise typer.Exit(code=2) from None
    console.print(
        f"\n[bold green]recognised {result.recognized:,}[/bold green] pages "
        f"({result.n_lines:,} lines) · skipped {result.skipped:,} · {result.seconds:.0f}s"
    )
    if result.failures:
        console.print(f"[yellow]{len(result.failures)} issues[/yellow]: {result.failures[:3]}")
    console.print("Run [cyan]leibniz pipeline report[/cyan] to update reports/htr-v1-sample.md.")
    conn.close()


@app.command()
def status(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
) -> None:
    """Print the corpus pipeline status histogram."""
    conn = db.init_db(db_path)
    hist = db.status_histogram(conn)
    total = sum(hist.values())
    console.print(f"[bold]pipeline status[/bold] — {total:,} pages")
    for st in ("pending", "segmented", "recognized", "skipped"):
        n = hist.get(st, 0)
        pct = (100.0 * n / total) if total else 0.0
        console.print(f"  {st:<11} {n:>10,}  ({pct:.1f}%)")
    console.print(
        f"  lines: {db.count_lines(conn):,} ({db.count_lines(conn, recognized=True):,} recognised)"
    )
    conn.close()


@app.command()
def audit(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    page: str | None = typer.Option(
        None, "--page", help="Page id (default: the next page recognize would attempt)."
    ),
) -> None:
    """Audit a page's stored line geometry against the crop guards (no kraken needed)."""
    conn = db.init_db(db_path)
    if page is None:
        target = next(
            iter(db.iter_pages_by_status(conn, "segmented", require_cached=True, limit=1)), None
        )
        if target is None:
            console.print("[yellow]No segmented+cached pages to audit.[/yellow]")
            conn.close()
            raise typer.Exit(code=0)
    else:
        target = db.get_page(conn, page)
        if target is None:
            console.print(f"[red]Unknown page id {page!r}.[/red]")
            conn.close()
            raise typer.Exit(code=1)
    rows = audit_page(conn, target)
    conn.close()
    cap = geometry.max_crop_area(target.width, target.height) / 1e6
    console.print(
        f"[bold]pipeline audit[/bold] — {target.id} "
        f"({target.width or '?'}×{target.height or '?'} px, {len(rows)} lines, "
        f"crop cap {cap:.0f} MPx)"
    )
    table = Table("line", "bl pts", "bl px", "poly pts", "est crop", "MPx", "verdict")
    for r in rows:
        bad = r["verdict"] != "ok"
        table.add_row(
            str(r["line_seq"]),
            str(r["n_baseline_pts"]),
            str(r["baseline_px"]),
            str(r["n_boundary_pts"]),
            r["est_crop"] or "—",
            str(r["est_mpx"]) if r["est_mpx"] is not None else "—",
            r["verdict"],
            style="red" if bad else None,
        )
    console.print(table)
    n_bad = sum(1 for r in rows if r["verdict"] != "ok")
    colour = "red" if n_bad else "green"
    console.print(f"{len(rows) - n_bad} croppable · [{colour}]{n_bad} guarded[/{colour}]")


@app.command()
def report(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store path."),
    out: Path = typer.Option(DEFAULT_REPORT, "--out", help="Report markdown path."),
) -> None:
    """(Re)write reports/htr-v1-sample.md from the current store."""
    conn = db.init_db(db_path)
    rep = report_mod.gather_report(conn, generated_at=db.utcnow_iso())
    conn.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_mod.render_report(rep), encoding="utf-8")
    console.print(
        f"[bold]pipeline report[/bold] → {out}  "
        f"({rep.status_counts.get('recognized', 0):,} recognised pages)"
    )


__all__ = ["app"]
