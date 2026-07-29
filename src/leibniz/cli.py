"""The ``leibniz`` command-line interface.

One CLI, one subcommand group per pipeline stage (SPECS §4.2). At scaffold time
only ``--version`` and a couple of introspection helpers are wired up; each
later phase attaches its own Typer sub-app here (``harvest``, ``images``,
``bench``, ``pipeline``, ``index``, ``serve``, ``release`` …).
"""

from __future__ import annotations

import typer
from rich.console import Console

from leibniz import __version__
from leibniz.harvest.cli import app as harvest_app

app = typer.Typer(
    name="leibniz",
    help="Leibniz Legible — machine transcription, search, and IIIF browsing "
    "for the digitized Leibniz Nachlass.",
    no_args_is_help=True,
    add_completion=False,
)

# Stage sub-apps attach here, one per pipeline stage (SPECS §4.2).
app.add_typer(harvest_app, name="harvest")

_console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"leibniz {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Leibniz Legible command-line interface."""


@app.command()
def info() -> None:
    """Print a short description of the project and where to look next."""
    _console.print(f"[bold]Leibniz Legible[/bold] v{__version__}")
    _console.print(
        "Access layer for the digitized Leibniz Nachlass — machine transcription "
        "with per-line confidence and provenance, typo-tolerant search, IIIF viewer."
    )
    _console.print("Read [cyan]SPECS.md[/cyan] (law), [cyan]STATUS.md[/cyan] (state).")


if __name__ == "__main__":  # pragma: no cover
    app()
