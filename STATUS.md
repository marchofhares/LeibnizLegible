# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-07-28 (end of Phase A0)._

---

## Current state

**Phase A0 (Repo scaffold) — complete.** The project is a working, installable
Python 3.12 package with a runnable CLI, the canonical SQLite schema, and the
legal expiry registry — the two pieces of "law as code" that later phases lean
on. Everything is offline and green:

- `uv run leibniz --version` → `leibniz 0.1.0`; `python -m leibniz` works too.
- `uv run ruff check .` and `uv run ruff format --check .` — clean.
- `uv run pytest` — **27 passed** (CLI smoke, DB helpers, legal registry incl.
  the required boundary cases).

No harvesting, no images, no models yet — those are A1+. The `data/` tree is
created and git-ignored; nothing bulk has been fetched.

### Layout as built

```
pyproject.toml          uv-managed, py3.12, entry point `leibniz`; deps typer/httpx/lxml/rich
src/leibniz/
  __init__.py           __version__ (single source of truth)
  cli.py                Typer app; --version + `info`; sub-apps attach here per phase
  __main__.py           `python -m leibniz`
  db.py                 SQLite schema (7 tables) + typed works/pages helpers
  legal.py              §70/§71 AA-volume expiry registry + expired_volumes()
  harvest/ catalog/ layout/ htr/ align/ enrich/ search/ release/ web/
                        empty-but-importable subpackages, each docstring'd with its
                        future responsibility (A1–D3)
tests/                  test_cli.py, test_db.py, test_legal.py, fixtures/
data/                   .gitkeep + README (never committed; see the README)
reports/                (empty; A1 writes the first census here)
```

### Decisions & divergences from the prompt (repo wins; recorded per protocol)

- **`legal.py` and `db.py` are modules, not subpackages.** The COMMON CONTEXT
  lists `legal` among the `{...}/` subpackages, but the A0 prompt says "Create
  `src/leibniz/legal.py`" / `db.py`. Followed the specific instruction: both are
  single files. The other nine names are subpackages (later phases add files
  inside them, e.g. `htr/bench.py`, `web/api.py`).
- **`ruff format` adopted alongside `ruff lint`.** COMMON CONTEXT names only
  "ruff lint", but the repo now also passes `ruff format --check` so style is
  mechanical, not a matter of taste.
- **Python 3.12 via `uv`.** The container's system Python is 3.11; `uv`
  provisioned CPython 3.12.11 and the package pins `requires-python = ">=3.12"`.
  `uv.lock` is committed for reproducibility.
- **`lines` table is append-per-run.** Surrogate integer PK + non-unique
  canonical `line_id`, with `UNIQUE(page_id, line_seq, run_id)`. The
  current-run-pointer vs. version-rows choice (SPECS/C4) is deliberately left
  open; A0 only lays the table down.
- **Legal registry uses real, cross-checked first-publication years** (see Key
  numbers) rather than SPECS-derived approximations. A consistency test asserts
  the registry reproduces the exact "free today" set in SPECS §1.4.

---

## Phase log

### A0 — Repo scaffold (2026-07-28) ✅

Built the scaffold per PROMPTS.md A0: `pyproject.toml` + `leibniz` entry point;
the `src/leibniz/` skeleton; `tests/` with a CLI smoke test; `.gitignore`,
`.env.example`, `data/` with README + `.gitkeep`.

`legal.py`: encoded the §70/§71 expiry registry as structured `Volume` data with
`first_publication_year`, computed `free_from = date(pub_year + 26, 1, 1)` (25-yr
term under the §69 calendar-year rule), and `expired_volumes(today)`. First-pub
years were **verified against the edition's own site (leibnizedition.de)** and
cross-checked against gwlb.de / rep.adw-goe.de / De Gruyter. All five build-prompt
anchors confirmed (I,17=2001, IV,4=2001, III,5=2003, VII,3=2003, VII,8=2024).
Modeled II,1's dual edition (1926 free / 2006 *Neubearbeitung* protected to 2032).

`db.py`: DDL for all seven SPECS §4.3 tables (enums as `CHECK` constraints, JSON
as TEXT, FKs on), idempotent `init_db()`, and typed `Work`/`Page` dataclasses
with upsert/get/iter helpers. The ID scheme (`{object}:{seq:04d}` /
`…:{line_seq:03d}`) is implemented and tested.

Tooling verified: ruff (lint + format) clean, 27 pytest tests green, all offline.

---

## Key numbers

| Metric | Value |
| --- | --- |
| Tests passing | 27 (offline) |
| DB tables | 7 — works, pages, lines, katalog_records, crosswalk, gt_lines, runs |
| Legal registry entries | 42 |
| AA reading text **free today** (2026-07-28) | **32 entries** (SPECS §1.4 says "~34 volumes/parts" — reconciles: VI,4 alone is 4 physical parts A–D) |
| Still protected | 10 |

**Upcoming §70/§71 expiries** (matches SPECS §1.4's "2027 / 2029" claims, extended):

| 1 Jan | Volumes entering the public domain |
| --- | --- |
| 2027 | I,17 · IV,4 |
| 2029 | III,5 · VII,3 |
| 2032 | II,1 (2006 *Neubearbeitung*) |
| 2034 | VII,4 · VII,5 |
| 2038 | VII,6 |
| 2045 | VII,7 |
| 2050 | VII,8 |

(No AA page images have been counted yet — the **first real page count** is A1's
gate deliverable, `reports/census.md`. Expected band ~150–250k page images.)

---

## Open questions

1. **§71 editio-princeps assumption.** The registry uses one `free_from` date
   per volume, treating §70 (scientific edition) and §71 (first publication of a
   previously unpublished work) as expiring together — true when both run from
   the same first-publication event. Confirm in the lawyer memo (SPECS §7.5) that
   no piece carries a §71 clock starting later than its volume's.
2. **Re-editions & reprints.** II,1's 2006 *Neubearbeitung* is modeled as a
   fresh 25-yr term (→2032); Reihe VI's 1990 *durchgesehene Nachdrucke* (VI,1/2/6)
   are assumed **not** to restart the term. Both assumptions want a lawyer's nod
   before any extraction from those volumes.
3. **Registry coverage is intentionally partial.** It lists volumes with a
   confirmed year through the 2050 horizon in the series we care about (I–IV, VI,
   VII); it is *not* the full ~60-volume AA. Extend as later volumes' years are
   verified. VI,3's year is 1980 vs 1981 across sources (legally immaterial).
4. **Python version.** Container default is 3.11; we rely on `uv` to supply 3.12.
   Any CI must `uv sync --python 3.12`, not the system interpreter.
5. **Endpoint facts unverified.** OAI set counts, IIIF URL shapes, and rights
   statements in SPECS §1 are quoted from July-2026 research and are **not**
   re-checked in A0. A1 must verify them live and record drift here.

---

## Next

**Recommended: Phase A1 — OAI/IIIF harvest → inventory + corpus census (gate).**
It produces the project's first genuinely new artifact — the real page count —
and unblocks A2 (images) and A3 (crosswalk).

- **A1** depends only on A0 (ready now). Gate: total page count in the ~150–250k
  band, published in `reports/census.md`.
- **B1** (benchmark harness + PHILIUMM reproduction) is independent of A1–A3 and
  can interleave / run in parallel — it also depends only on A0. Good candidate
  for a second track.

Sequencing per SPECS §5: A1→A2→A3 and B1→B2 can interleave; C is sequential; D
follows C4.
