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

### Harvest (Phase A1)

```bash
# Set a contact for the polite crawler (SPECS §7.4); copy .env.example → .env.
export LEIBNIZ_CONTACT_EMAIL="you@example.org"

uv run leibniz harvest oai            # OAI-PMH → works (all 5 Leibniz sets; ~15 min, ≤1 req/s)
uv run leibniz harvest census         # write reports/census.md (the first real page count)
uv run leibniz harvest manifests --set leibniz-rekonstruktionen  # IIIF manifests → pages (a slice)
```

Both harvest commands are **cache-first and resumable** (raw XML/JSON under
`data/oai/`, `data/manifests/`); re-running re-parses from cache without
re-fetching. See `reports/crawl-posture.md` for the crawl-etiquette baseline.

### Image cache (Phase A2)

```bash
uv run leibniz images pages          # derive all pages' delivery URLs from cached METS (offline)
uv run leibniz images fetch --work 00067974 --work DE-611-HS-854976  # pull a dev slice
uv run leibniz images verify --deep  # re-checksum the cache, report gaps
uv run leibniz images stats          # counts/bytes/dimensions → reports/census.md
```

Caches one JPEG delivery derivative per page under `data/images/` — resumable,
checksummed, integrity-retried. The full-corpus pull (~365 GB) is an operator
command; a `--set`/`--work`/`--limit` slice pulls a dev corpus. Images are
**never rehosted** — this is an internal working store for the HTR pipeline.

### Katalog crosswalk (Phase A3)

```bash
uv run leibniz catalog scrape --sample   # scrape a cross-set sample of Ritter-Katalog records
uv run leibniz catalog crosswalk         # match records → works (GWLB link + shelfmark)
uv run leibniz catalog report            # write reports/crosswalk.md
```

Joins the BBAW Ritter-Katalog (CC BY 4.0) to our works so every scan links to its
scholarly record. No public API; the site caps results at 5000 rows, so the full
scrape partitions into sub-cap slices (an operator job).

### GT factory (Phase C2)

```bash
uv sync --extra gt                              # + pdfplumber (PDF text layers)
uv run leibniz catalog scrape --expired-volumes # every §70-expired volume's katalog records (~8 min)
uv run leibniz catalog crosswalk                # records → works
uv run leibniz align pieces                     # enumerate the §70 pieces localizable to canvases
uv run leibniz align ingest                     # fetch + extract each volume's reading text (cache-first)
uv run leibniz align edition-cache              # join to the katalog → data/gt/edition_cache.jsonl
uv run leibniz align factory data/gt/edition_cache.jsonl --shard 1/6 --resume  # ×6 workers (needs the C1 HTR lines)
uv run leibniz align gt-report                  # writes reports/gt-factory.md
uv run leibniz align audit-sheet --images /path/to/image-cache   # 200 line strips → reports/gt-audit/gt-audit.html
uv run leibniz align audit-score reports/gt-audit/gt-audit-verdicts.csv  # precision per stratum → reports/gt-audit.md
```

The reading text of each §70-expired Akademie-Ausgabe volume is read from a
free digital copy of the print (archive.org scans with their OCR layer, the
GWLB repositorium PDFs, Potsdam's born-digital PDFs — `align/volumes_sources.py`
records the channel and its terms per volume) by a layout-aware extractor
(`align/edition.py`: running head, body vs. apparatus type, piece headings,
margin numbers) — apparatus, commentary and introductions never enter it
(SPECS §7.2). Minting itself runs where the C1 corpus store lives.

## Where things live

| Path | What |
| --- | --- |
| `src/leibniz/` | the package: one CLI (`leibniz`), one subpackage per pipeline stage |
| `src/leibniz/db.py` | canonical SQLite schema (SPECS §4.3) + typed helpers |
| `src/leibniz/legal.py` | §70/§71 copyright-expiry registry for AA reading text |
| `src/leibniz/net.py` | polite HTTP client — UA, ≤1 req/s per host, backoff (SPECS §7.4) |
| `src/leibniz/harvest/` | OAI-PMH + IIIF harvest → `works`/`pages`, and the corpus census |
| `src/leibniz/images/` | local delivery-derivative image cache (fetch/verify/stats) |
| `src/leibniz/catalog/` | Ritter-Katalog scraper + works crosswalk (shelfmark normaliser) |
| `src/leibniz/htr/` | benchmark harness (D5) + engine adapters (Kraken / VLM) — B1 |
| `src/leibniz/layout/` | Kraken baseline segmentation of a page into line images |
| `src/leibniz/align/` | retro-alignment engine + the C2 GT factory (resolver, anchor-guided banded DP, strata, volume sources, reading-text extractor, ingestion) |
| `src/leibniz/pipeline/` | corpus segment/recognize batch pipeline + per-page seg-stats — C1 |
| `tests/` | offline tests mirroring the package |
| `data/` | working store — **git-ignored, never committed** (see `data/README.md`) |
| `reports/` | committed reports (census, benchmarks, alignment yield) |

## Status

**The v1 corpus run is complete (2026-09-11): 236,210 of 236,795 pages —
99.75% of the digitized Nachlass — are machine-recognised, 13.5M lines with
per-line confidence and provenance.** The remainder is enumerated (569 skips
with reasons; 16 pages behind broken GWLB redirects). Phases **A0–A3, B1–B2,
C1** are complete (`STATUS.md` has the detail). A1's census found **2,225 works
/ 236,795 page images**; A2/A3 built the image cache (395.6 GB) and katalog
crosswalk. **B1** reproduced the PHILIUMM HTR CER (**7.95 %** vs claimed
8.33 %) and **B2** green-lit the retro-aligner (**98.8 % yield / 97.5 %
precision** on favourable material). **C1** built — and has now run at corpus
scale — the resumable segment/recognize pipeline (`leibniz pipeline`, sharded
parallel workers + concurrent GPU recognition); **C2** built the GT factory
(`leibniz align factory`) and has now run its inputs at full scale: the §70
katalog sweep (17,162 piece citations, 11,595 localizable)
and the reading-text extraction of 21 of 31 expired volumes from
their free digital copies (6,188 pieces, 26.2M
characters, 10,029 witnesses with text). **The mint has run (2026-09-16):
297,424 open-bucket ground-truth lines**, 5.9× the 50k target, in about two
hours on six workers. Its precision is only preliminarily audited (20 of
200 sheet lines, `leibniz align audit-sheet` / `audit-score`; the gate is
deferred to the C3 ablation). Next is **C3** (fine-tune v2, a gate). See
`STATUS.md`.

## Licensing (summary — see SPECS §7)

Code is Apache-2.0. GWLB scans are Public Domain Mark 1.0 and are always loaded
from GWLB's own IIIF endpoints — **never rehosted**. Only §70/§71-expired AA
*reading text* is ever redistributed; NC-licensed sources stay in a quarantined
bucket excluded from public releases and the UI. Provenance is mandatory on every
stored and exported line.
