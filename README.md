# Leibniz Legible

**Live at https://leibnizlegible.com (since 2026-09-21).**

An open **access layer** for the digitized Leibniz Nachlass — every one of the
236,795 page records held by the Gottfried Wilhelm Leibniz Bibliothek (GWLB),
Hannover, machine-transcribed with per-line confidence and provenance,
typo-tolerantly searchable, and browsable in an open IIIF viewer cross-linked to
the scholarly catalogue.

This is **machine output with honest labels** — Vorausedition-grade, explicitly
subordinate to the Akademie-Ausgabe. It is never "an edition". The edition is
about half way through the volumes it plans (68 by 2023, completion expected
around 2055), and one of its editors estimates that three quarters of Leibniz's
papers have never been published anywhere (Kliege-Biller, Münster, 2023);
making all of it *legible and findable* is the point.

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
uv run leibniz images duplicates     # sheet-sides registered under two folio labels → reports/duplicates.md
```

**Sheet-sides are registered twice.** In the GWLB's static-JPEG delivery a scan
is one side of an unfolded sheet — two folio pages side by side — and the METS
lists that one image under both folio labels (outer side `1r` + `2v`, inner side
`1v` + `2r`). The corpus run read every such image twice, so the page and line
totals below count those repeats and search returns them as twin hits.
`leibniz images duplicates` hashes the thumbnails and lists the pairs; folding
them in the index and publishing a distinct-scan count is the next data fix.

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

### Search, viewer, IIIF (Phases D1/D2)

The viewer shell is stamped per route (title, description, canonical URL, share
metadata) and, for `/work/{id}` and `/page/{id}`, carries a server-rendered
summary — the catalogue entries and page list, or the machine text — so search
engines, answer engines and readers without JavaScript see the content; the app
replaces it on boot. `/sitemap.xml` lists every work, `/llms.txt` describes the
API for agents, `/robots.txt` opens the JSON routes and keeps blind crawlers off
the IIIF manifests.

```bash
uv sync --extra web                        # fastapi + uvicorn
uv run leibniz index build                 # page index → data/search.sqlite (SQLite FTS5)
uv run leibniz index query "calculemus"    # try it from the shell
uv run leibniz serve                       # http://127.0.0.1:8000 — search, /work/…, /page/…, /about
# production: typo-tolerant Meilisearch
docker compose up -d meilisearch
uv run leibniz index build --backend meili --meili-key "$MEILI_MASTER_KEY"
uv run leibniz serve --backend meili --host 0.0.0.0 --base-url https://your.host
```

The index folds text and query onto the aligner's early-modern comparison
alphabet (u≡v, i≡j, ſ→s, diacritics, ligatures), so *ut* finds *vt*. The API
(`/api/search`, `/api/works/{id}`, `/api/pages/{id}`, `/api/stats`) serves
every line with its geometry, text, confidence, status and provenance; each
work is also a IIIF Presentation 3 manifest (`/manifests/{id}`) whose canvases
reference W3C annotation pages (`/annotations/{page_id}`) carrying the
transcription — the interop deliverable D7. The viewer under
`src/leibniz/web/static/` is plain ES modules (no build step): OpenSeadragon on
the GWLB's own Image API (static JPEG where no service exists) or on the
project's image mirror when `LEIBNIZ_IMAGE_BASE_URL` is set, a line-polygon
overlay, status badges, confidence bands, provenance per line, EN/DE.

### Releases (Phase D3)

```bash
uv sync --extra release                    # pyarrow
uv run leibniz release export              # data/release/leibniz-{inventory,transcriptions,gt}/
uv run leibniz release checklist           # the upload runbook (reports/release-checklist.md)
```

Each export ships Parquet (or `--format jsonl`), a `MANIFEST.json` with row
counts and SHA-256s, and a dataset card with provenance, licence, attribution,
error rates and the anti-contamination note. `reports/tier1-final.md` states
the project against SPECS §3, criterion by criterion.

### Deploying (a public host)

```bash
deploy/prepare-store.sh                                # desktop: compact, verified serving copy of the store
curl -fsSL https://raw.githubusercontent.com/marchofhares/leibnizlegible/main/deploy/install.sh | bash  # server: users, venv, Meilisearch, Caddy, units
leibniz index build --backend meili                    # server: one pass over the store, an hour or two
leibniz index bench --url https://your.host            # search p95 against SPECS §3.3 (500 ms)
```

```bash
uv run leibniz images thumbs                              # desktop: thumbnails for the mirror (Pillow, all cores)
rclone sync data/images r2:leibniz-images && rclone sync data/thumbs r2:leibniz-images/thumbs
uv run leibniz images check-mirror --base-url https://images.leibnizlegible.com  # HEADs a sample
```

`deploy/README.md` is the runbook: sizing, the store copy, `install.sh`, the
search-only Meilisearch key, the index build, verification, measurement, the
hardening that is on by default (per-client rate limit, security headers,
CORS for IIIF consumers, read-only store, seven-day logs, `robots.txt`) and
day-two operations. `Dockerfile` + `deploy/docker-compose.prod.yml` are the
all-container alternative. `leibniz serve` takes every option from the
environment too (`deploy/env.example`), runs `--workers N`, and answers
`/healthz` for the process manager. Nothing on the server is precious: the
store is a copy, the index a rebuild, and the images stay at the GWLB.

## Where things live

| Path | What |
| --- | --- |
| `src/leibniz/` | the package: one CLI (`leibniz`), one subpackage per pipeline stage |
| `src/leibniz/db.py` | canonical SQLite schema (SPECS §4.3) + typed helpers |
| `src/leibniz/legal.py` | §70/§71 copyright-expiry registry for AA reading text |
| `src/leibniz/net.py` | polite HTTP client — UA, ≤1 req/s per host, backoff (SPECS §7.4) |
| `src/leibniz/harvest/` | OAI-PMH + IIIF harvest → `works`/`pages`, and the corpus census |
| `src/leibniz/images/` | local delivery-derivative image cache (fetch/verify/stats), thumbnails + mirror check |
| `src/leibniz/catalog/` | Ritter-Katalog scraper + works crosswalk (shelfmark normaliser) |
| `src/leibniz/htr/` | benchmark harness (D5) + engine adapters (Kraken / VLM) — B1 |
| `src/leibniz/layout/` | Kraken baseline segmentation of a page into line images |
| `src/leibniz/align/` | retro-alignment engine + the C2 GT factory (resolver, anchor-guided banded DP, strata, volume sources, reading-text extractor, ingestion) |
| `src/leibniz/pipeline/` | corpus segment/recognize batch pipeline + per-page seg-stats — C1 |
| `src/leibniz/search/` | page index: folding, snippets, SQLite FTS5 + Meilisearch backends — D1 |
| `src/leibniz/web/` | FastAPI JSON API, IIIF v3 manifests + annotations, the static viewer — D1/D2 |
| `src/leibniz/release/` | Parquet/JSONL dataset exports + cards — D3 |
| `tests/` | offline tests mirroring the package |
| `data/` | working store — **git-ignored, never committed** (see `data/README.md`) |
| `reports/` | committed reports (census, benchmarks, alignment yield) |
| `deploy/` | the deployment kit: runbook, `install.sh`, systemd units, Caddyfile, env files, production compose |
| `.github/` | the issue form the viewer's "Report an error" link opens |

## Status

**The v1 corpus run is complete (2026-09-11): 236,210 of 236,795 page records —
99.75% of the digitized Nachlass — are machine-recognised, 13.5M line records
with per-line confidence and provenance (sheet-sides registered twice included;
see the duplicates note above).** The remainder is enumerated (569 skips
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
deferred to the C3 ablation). **Phase D is built on v1 (2026-09-16): the search index, the JSON API, IIIF
Presentation 3 manifests with W3C annotations, the viewer, and the dataset
exports with cards** — the v1 public beta; the operator runs `leibniz index
build` + `leibniz serve` on the corpus store. **The deployment kit landed the
same day** (`deploy/`: runbook, systemd + Caddy, container stack; the app
hardened for public traffic — rate limit, security headers, CORS, read-only
store, `/healthz`, `leibniz index bench`); the site went live on
2026-09-21 (`deploy/README.md` is the runbook). Next is **C3** (fine-tune v2, a
gate; see the amended prompt), then C4 re-reads the corpus and swaps v2 in under
a new run. Reports are on Zenodo: project statement
[10.5281/zenodo.22782813](https://doi.org/10.5281/zenodo.22782813), census
[10.5281/zenodo.22782815](https://doi.org/10.5281/zenodo.22782815), PHILIUMM
reproduction [10.5281/zenodo.22782817](https://doi.org/10.5281/zenodo.22782817),
retro-aligned GT [10.5281/zenodo.22782819](https://doi.org/10.5281/zenodo.22782819).
See `STATUS.md`; `NOTES.md` holds the 2026-09-16 strategy review.

## Licensing (summary — see SPECS §7)

Code is Apache-2.0. GWLB scans are Public Domain Mark 1.0. By default the app
loads them from the GWLB's own endpoints (SPECS §3.4); the public site serves
its own mirror of the GWLB's delivery scans instead (`LEIBNIZ_IMAGE_BASE_URL`;
an operator decision recorded in `STATUS.md`, Divergences), with every page
linking to its original at the GWLB. Only §70/§71-expired AA *reading text* is
ever redistributed; NC-licensed sources stay in a quarantined bucket excluded
from public releases and the UI. Provenance is mandatory on every stored and
exported line.
