# COMMON CONTEXT as pasted to 2026-11-18, and two sentences of PROMPTS.md

_Kept verbatim by ARCH2 on 2026-11-19, which amended these places of `PROMPTS.md` for the files under `status/` and `prompts/`: the sentence of "How to use this file" on where a new prompt and a new entry go, the COMMON CONTEXT block as every session up to DQ1 was given it, and the line under which the run prompts were appended. A record: do not paste this block; the current one is in `PROMPTS.md`._

## From "How to use this file", as it stood

The prompts that have been run are in `PROMPTS-archive.md`, moved there verbatim (ARCH1, 2026-11-17), and the `STATUS.md` entries dated before 2026-10-19 are in `STATUS-archive.md`; a prompt that names an archived prompt or entry means the archived text. Nothing is appended to the two archive files: a new prompt goes under "Follow-up phases (2026-10)" below and a new entry into `STATUS.md`, as before.

## COMMON CONTEXT, as it stood

```
You are building "Leibniz Legible": every page of the digitized Leibniz Nachlass
(~200,000 page images at the Gottfried Wilhelm Leibniz Bibliothek, Hannover)
machine-transcribed with per-line confidence and provenance, typo-tolerantly
searchable, and browsable in an open IIIF viewer linked to the scholarly
catalogue. Access layer, not an edition: output is Vorausedition-grade machine
text with honest labels, subordinate to the Akademie-Ausgabe.

FIRST: read SPECS.md (the law) and STATUS.md (current state) in full. If this
prompt conflicts with the repo, the repo + STATUS.md win; record the divergence.

Conventions (from SPECS §4, enforce throughout):
- Python 3.12, `uv` for env/deps, `ruff` lint, `pytest` tests, `typer` CLI
  exposed as `leibniz` (one CLI, subcommands per stage).
- Package layout: src/leibniz/{harvest,catalog,layout,htr,align,enrich,search,
  release,legal,web}/ ; tests in tests/ mirroring; generated reports in
  reports/ (committed); bulk data under data/ (gitignored).
- Canonical store: SQLite at data/inventory.sqlite via a thin typed layer
  (sqlite3 or sqlite-utils; no ORM). Schema per SPECS §4.3. Release exports
  are Parquet.
- IDs: page = "{gwlb_object_id}:{canvas_seq:04d}", line = page + ":{line_seq:03d}".
- Provenance is non-negotiable (SPECS §4.5): every stored line carries model,
  version, run_id, confidence, status ∈ {machine, aligned, corrected, verified}.
  Never store or export text without these fields.
- License buckets (SPECS §7): 'open' vs 'nc'. NC-derived text never enters
  CC BY exports or the public UI. Only §70-expired AA reading text (list in
  src/leibniz/legal.py, from SPECS §1.4) may be redistributed; never editor
  introductions/apparatus/commentary.
- Crawling etiquette: custom User-Agent with contact email, ≤1 req/s per host,
  exponential backoff, resumable, cache-first (never re-fetch cached items).
- Secrets via .env (ANTHROPIC_API_KEY optional); never committed. Everything
  must run without the key (LLM steps skip gracefully).
- Keep functions small and typed; every non-trivial module gets tests that run
  offline (fixtures under tests/fixtures/, no network in tests).

FINISH by: running ruff + pytest clean; updating STATUS.md (what changed, key
numbers, open questions, recommended next phase / gate verdict); committing
with a descriptive message.
```

## Below the table of "Follow-up phases (2026-10)", as it stood

New prompts are appended below this line, verbatim, as before.
