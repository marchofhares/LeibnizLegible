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
| `tests/` | offline tests mirroring the package |
| `data/` | working store — **git-ignored, never committed** (see `data/README.md`) |
| `reports/` | committed reports (census, benchmarks, alignment yield) |

## Status

Phases **A0–A3** are complete (`STATUS.md` has the detail). A1's census found
**2,225 works / 236,795 page images**; A2 populated the full `pages` table
offline and now caches JPEG delivery derivatives (dev slice pulled, full pull
~365 GB left as an operator command); A3's katalog crosswalk already links
**1,094 / 2,225 works (49.2%)** from a 6-query sample, with 99.96% GWLB-link
resolution (`reports/crosswalk.md`). A notable finding: only ~⅓ of pages are
IIIF-served, but the METS `fileSec` yields a uniform static-JPEG delivery URL for
all of them. Next up is **B1** (benchmark harness + PHILIUMM reproduction, a
gate), then **B2** (retro-alignment). See `STATUS.md`.

## Licensing (summary — see SPECS §7)

Code is Apache-2.0. GWLB scans are Public Domain Mark 1.0 and are always loaded
from GWLB's own IIIF endpoints — **never rehosted**. Only §70/§71-expired AA
*reading text* is ever redistributed; NC-licensed sources stay in a quarantined
bucket excluded from public releases and the UI. Provenance is mandatory on every
stored and exported line.
