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

from leibniz import db
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT
from leibniz.pipeline import report as report_mod
from leibniz.pipeline.recognize import recognize_pages
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
    min_lines: int = typer.Option(1, "--min-lines", help="Below this, a page is 'blank'/skipped."),
) -> None:
    """Segment cached pages into line geometry + per-page segmentation stats."""
    _require_kraken()
    from leibniz.layout.segment import PageSegmenter

    conn = db.init_db(db_path)
    pending = db.count_pages_by_status(conn, "pending", set_name=set_)
    console.print(
        f"[bold]pipeline segment[/bold] — {pending:,} pending pages (set={set_ or 'all'})"
    )
    segmenter = PageSegmenter(seg_model, device=device)
    total = sample or pending
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
            min_lines=min_lines,
            progress=lambda _pid, _o: progress.advance(task),
        )
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
    batch_size: int = typer.Option(16, "--batch-size", help="HTR batch size."),
) -> None:
    """Recognise segmented pages: crop each stored line, HTR, store text + conf."""
    _require_kraken()
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
            progress=lambda _pid, _o: progress.advance(task),
        )
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
