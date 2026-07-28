# Leibniz Legible

An open **access layer** for the digitized Leibniz Nachlass — every page of the
~200,000 page images held by the Gottfried Wilhelm Leibniz Bibliothek (GWLB),
Hannover, machine-transcribed with per-line confidence and provenance,
typo-tolerantly searchable, and browsable in an open IIIF viewer cross-linked to
the scholarly catalogue.

This is **machine output with honest labels** — Vorausedition-grade, explicitly
subordinate to the Akademie-Ausgabe. It is never "an edition". Roughly 75% of the
Nachlass has never been printed; making it *legible and findable* is the point.

- **`SPECS.md`** — the project's law (mission, deliverables, architecture, legal rails).
- **`PROMPTS.md`** — the phase-by-phase build plan.
- **`STATUS.md`** — living state; read it first.

## Quickstart

Requires [`uv`](https://docs.astral.sh/uv/). Python 3.12 is provisioned by `uv`
(the system interpreter is not used).

```bash
uv sync --python 3.12      # create the venv (CPython 3.12) and install everything
uv run leibniz --version   # -> leibniz 0.1.0
uv run leibniz info

uv run ruff check .        # lint
uv run ruff format --check . # style
uv run pytest              # tests (all offline)
```

## Where things live

| Path | What |
| --- | --- |
| `src/leibniz/` | the package: one CLI (`leibniz`), one subpackage per pipeline stage |
| `src/leibniz/db.py` | canonical SQLite schema (SPECS §4.3) + typed helpers |
| `src/leibniz/legal.py` | §70/§71 copyright-expiry registry for AA reading text |
| `tests/` | offline tests mirroring the package |
| `data/` | working store — **git-ignored, never committed** (see `data/README.md`) |
| `reports/` | committed reports (census, benchmarks, alignment yield) |

## Status

Phase **A0 (repo scaffold)** is complete: installable package, runnable CLI, the
database schema, and the legal registry, all with green lint + tests. Next up is
**A1** (OAI/IIIF harvest → the first real corpus page count). See `STATUS.md`.

## Licensing (summary — see SPECS §7)

Code is Apache-2.0. GWLB scans are Public Domain Mark 1.0 and are always loaded
from GWLB's own IIIF endpoints — **never rehosted**. Only §70/§71-expired AA
*reading text* is ever redistributed; NC-licensed sources stay in a quarantined
bucket excluded from public releases and the UI. Provenance is mandatory on every
stored and exported line.
