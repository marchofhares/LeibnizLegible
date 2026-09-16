"""``leibniz release`` — package the datasets for deposit (Phase D3)."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from leibniz import db
from leibniz.release.export import DATASETS, DEFAULT_CHUNK_ROWS, DEFAULT_OUT, export_all
from leibniz.search.documents import corpus_stats

app = typer.Typer(
    help="Releases (D3): export datasets + cards; print the checklist.", no_args_is_help=True
)
console = Console()

CHECKLIST = Path("reports/release-checklist.md")


@app.command()
def export(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="Canonical SQLite store."),
    out: Path = typer.Option(DEFAULT_OUT, "--out", help="Output root (one dir per dataset)."),
    fmt: str = typer.Option("parquet", "--format", help="parquet (needs pyarrow) or jsonl."),
    dataset: list[str] = typer.Option(
        [], "--dataset", help="Which datasets (inventory, transcriptions, gt); default all."
    ),
    chunk_rows: int = typer.Option(DEFAULT_CHUNK_ROWS, "--chunk-rows", help="Rows per file."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Skip the corpus statistics scan."),
) -> None:
    """Write the dataset exports (files + MANIFEST.json + README card)."""
    chosen = tuple(dataset) if dataset else DATASETS
    unknown = [d for d in chosen if d not in DATASETS]
    if unknown:
        raise typer.BadParameter(f"unknown dataset(s) {unknown}; expected {DATASETS}")
    conn = db.init_db(db_path)
    try:
        stats = None if no_stats else corpus_stats(conn)
        exports = export_all(
            conn, out, datasets=chosen, fmt=fmt, chunk_rows=chunk_rows, stats=stats
        )
    finally:
        conn.close()
    table = Table(title="Exports")
    for col in ("dataset", "table", "rows", "files", "bytes"):
        table.add_column(col, justify="right" if col in ("rows", "files", "bytes") else "left")
    for exp in exports:
        for name, n in exp.row_counts.items():
            files = [f for f in exp.files if f.path.startswith(name + "-")]
            table.add_row(
                exp.dataset, name, f"{n:,}", str(len(files)), f"{sum(f.bytes for f in files):,}"
            )
    console.print(table)
    console.print(f"Written under [cyan]{out}[/cyan]. Next: [cyan]{CHECKLIST}[/cyan].")


@app.command()
def checklist() -> None:
    """Print the release checklist (the operator's upload runbook)."""
    if CHECKLIST.exists():
        console.print(CHECKLIST.read_text(encoding="utf-8"))
    else:
        console.print(f"[yellow]{CHECKLIST} not found[/yellow]")


__all__ = ["app"]
