"""``leibniz legal`` — the legal registries on the terminal (Phase L1).

``licences`` prints the third-party licence registry, ``outputs`` the table of
this project's own outputs with the licence each carries and why, ``volumes``
the §70/§71 expiry registry. The data lives in :mod:`leibniz.legal`; this
module only renders it (``--format tsv`` and ``json`` for machines).
"""

from __future__ import annotations

import json
from datetime import date

import typer
from rich.console import Console
from rich.table import Table

from leibniz import legal

app = typer.Typer(
    help="The legal registries: third-party licences, this project's outputs, the §70 volumes.",
    no_args_is_help=True,
)
console = Console()

_TABLE_COLUMNS = (
    "key",
    "kind",
    "licence as obtained",
    "obtained",
    "licence now",
    "seen",
    "bucket",
    "deposit",
    "used",
)


def _emit(rows: list[dict[str, str]], columns: tuple[str, ...], fmt: str, title: str) -> None:
    if fmt == "json":
        typer.echo(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if fmt == "tsv":
        typer.echo("\t".join(columns))
        for r in rows:
            typer.echo("\t".join(str(r.get(c, "")).replace("\t", " ") for c in columns))
        return
    if fmt != "table":
        raise typer.BadParameter("--format must be table, tsv or json")
    table = Table(title=title)
    for c in columns:
        table.add_column(c, overflow="fold")
    for r in rows:
        table.add_row(*(str(r.get(c, "")) for c in columns))
    console.print(table)


@app.command()
def licences(
    fmt: str = typer.Option("table", "--format", help="table | tsv | json"),
    key: list[str] = typer.Option([], "--key", help="Only these entries (repeatable)."),
    full: bool = typer.Option(
        False, "--full", help="Every column in the table, not the short set."
    ),
) -> None:
    """Print the licence registry: every third-party artifact and its licence state."""
    rows = legal.licence_rows()
    if key:
        unknown = sorted(set(key) - set(legal.ARTIFACTS))
        if unknown:
            raise typer.BadParameter(f"unknown key(s) {unknown}")
        rows = [r for r in rows if r["key"] in key]
    columns = legal.LICENCE_COLUMNS if (full or fmt != "table") else _TABLE_COLUMNS
    _emit(rows, columns, fmt, f"Third-party artifacts ({legal.REGISTRY_DATE.isoformat()})")
    if fmt == "table":
        console.print(
            "[dim]bucket: open — derived data may enter the CC BY outputs; nc — the nc partition "
            "(SPECS §7.3); none — nothing derived. deposit: where lines minted through the channel "
            "go (D3). --full for sources, versions and what was built; --format tsv|json.[/dim]"
        )


@app.command()
def outputs(fmt: str = typer.Option("table", "--format", help="table | tsv | json")) -> None:
    """Print this project's outputs with the licence each carries and why."""
    _emit(
        legal.output_rows(),
        ("key", "output", "licence", "why", "inputs", "decided"),
        fmt,
        "This project's outputs",
    )


@app.command()
def volumes(
    today: str = typer.Option(
        "", "--today", help="ISO date to evaluate expiry at (default: today)."
    ),
    fmt: str = typer.Option("table", "--format", help="table | tsv | json"),
) -> None:
    """Print the §70/§71 expiry registry of the Akademie-Ausgabe volumes."""
    when = date.fromisoformat(today) if today else date.today()
    rows = [
        {
            "volume": v.label,
            "published": str(v.first_publication_year),
            "free from": v.free_from.isoformat(),
            "free today": "yes" if v.is_expired(when) else "no",
            "note": v.note or "",
        }
        for v in sorted(legal.REGISTRY, key=lambda v: (v.series, str(v.volume), v.edition or ""))
    ]
    _emit(
        rows,
        ("volume", "published", "free from", "free today", "note"),
        fmt,
        f"AA reading text, §70/§71 expiry as of {when.isoformat()}",
    )


__all__ = ["app"]
