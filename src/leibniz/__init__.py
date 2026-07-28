"""Leibniz Legible — an open access layer for the digitized Leibniz Nachlass.

This package is the whole project: a batch pipeline plus a thin serving layer,
exposed as one CLI (`leibniz`) with a subcommand per stage. The canonical
working store is a single SQLite file (``data/inventory.sqlite``); dataset
releases are Parquet.

The output is machine transcription with honest labels — Vorausedition-grade,
explicitly subordinate to the Akademie-Ausgabe. It is never "an edition".

See ``SPECS.md`` for the law, ``PROMPTS.md`` for the build plan, and
``STATUS.md`` for current state.
"""

# Single source of truth for the version. ``pyproject.toml`` reads it from here
# (``[tool.hatch.version]``), and the CLI ``--version`` flag reports it.
__version__ = "0.1.0"

__all__ = ["__version__"]
