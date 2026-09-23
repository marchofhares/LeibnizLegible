# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-09-23 (discoverability, About page, duplicate sheet-sides; earlier: 2026-09-16 — **Phase D built on v1 — search index, API, IIIF v3 + annotations, viewer, release exports; reports + project statement published on Zenodo; strategy review recorded in `NOTES.md` and the C3 prompt amended. C2 stands as closed on the mint with the precision gate deferred to C3. Later the same day: the deployment kit (`deploy/`), public-traffic hardening of the app, `LICENSE` + issue form for the repository going public.**)._

---

## Current state

**2026-09-23 (later): discoverability, About page, and a data caveat.** The
viewer shell now carries a favicon set, a web manifest, share metadata
(OpenGraph/Twitter with a 1200×630 card), a canonical URL and JSON-LD; the
server stamps title, description and canonical per route and renders a summary
for `/work/{id}` (catalogue entries, page list) and `/page/{id}` (the machine
text) in place of `<!--ll:ssr-->`, so crawlers, answer engines and no-JS
readers see content, and unknown ids are real 404s. New root files:
`/sitemap.xml` (every work), `/llms.txt` (the API and the wording rule for
agents), `/favicon.ico`; `robots.txt` opens the JSON API and keeps blind
crawlers off the IIIF routes; `/docs` and `/redoc` are off (the CSP blocked
their CDN assets), `/openapi.json` stays. The About page names the maintainer,
credits the GWLB, the Arbeitskatalog, PHILIUMM/FoNDUE/Kraken and the
precedents, describes the Akademie-Ausgabe with its own figures (68 volumes by
2023, about half of ~130, completion ~2055; Kliege-Biller 2023 for "three
quarters never published" — the source the "three quarters" sentence lacked),
adds a timeline, a citation line and the four report DOIs. The two unpopulated
search filters (language, writing stage) are hidden until C4. Work pages show
the katalog's other printings (`drucke`) and series-only AA assignments
(`aa_planned`). **Data caveat found today:** in the static-JPEG delivery a
scan is one side of an unfolded sheet registered under both folio labels
(outer `1r`+`2v`, inner `1v`+`2r`); sampled works show every sheet-side read
twice, so `pages`/`lines` totals include repeats and search returns twin hits.
`leibniz images duplicates` (new) hashes the thumbnails and lists the pairs;
folding them in the index and publishing a distinct-scan count is the next
data fix (Open Q #19). 524 tests, ruff clean.


**🚀 Phase D built on the v1 transcription (2026-09-16): the corpus is
searchable and browsable — the v1 public beta.** `leibniz index build` folds
every recognised page onto the aligner's early-modern comparison alphabet and
indexes it in SQLite FTS5 (single file) or Meilisearch (typo tolerance);
`leibniz serve` runs a FastAPI JSON API (`/api/search`, `/api/works/{id}`,
`/api/pages/{id}`, `/api/stats`), IIIF Presentation 3 manifests with W3C
annotation pages carrying every line's text + provenance (deliverable D7), and
the viewer: OpenSeadragon 5.0.1 on the GWLB's own Image API (static JPEG where
no service exists), a line-polygon overlay, status badges, five confidence
bands, a provenance disclosure per line, EN/DE, WCAG-clean (axe 0 violations
on every view). `leibniz release export` writes the three datasets as Parquet
(or JSONL) with `MANIFEST.json` checksums and dataset cards carrying
provenance, licence, attribution, error rates and the anti-contamination note.
`reports/release-checklist.md` is the upload runbook; `reports/tier1-final.md`
states the project against SPECS §3 criterion by criterion. **518 tests**, ruff
clean. The operator step: `leibniz index build && leibniz serve` on the corpus
store (the index build scans 13.5M lines once; the FTS5 file will be a few GB),
then measure search p95.

**🌐 LIVE (2026-09-21): https://leibnizlegible.com.** The v1 corpus is public
and searchable. A 2 vCPU / 4 GB Hetzner VPS in Falkenstein runs `leibniz
serve` behind Caddy (automatic TLS) with Meilisearch; the 15 GB serving store
and the 235,723-page index live on the box; **page images come from the
project's own mirror** (2026-09-23): all 236,779 delivery derivatives
(395.6 GiB) plus their derived thumbnails (6.0 GiB) on Cloudflare R2 behind
`images.leibnizlegible.com`, verified with `leibniz images check-mirror`
(500-page sample: every image and thumbnail present, no size mismatches)
before the switch. The GWLB's servers now carry none of the viewer's traffic,
and every page still links to its original there. **SPECS §3.3's search criterion
is met and measured:** 200 queries over HTTPS gave wall-clock p50 108 ms,
**p95 210 ms**, max 368 ms against the 500 ms bar (Meilisearch itself p50
8 ms, p95 60 ms). Typo tolerance and the early-modern fold both confirmed
live. What the deployment cost in wall clock, for the next operator: the
serving copy 10 min, its transfer 1 h 36 m at a measured 2.8 MB/s, the index
build **5 h 33 m** (disk-bound; only 32 min of CPU). `reports/tier1-final.md`
row 3 is updated from "to be measured" to met.

**Deployable (2026-09-16, later session).** The deployment kit is in `deploy/`
(runbook, `install.sh`, systemd units, Caddyfile, container stack) and the app
is hardened for public traffic (per-client rate limit, CSP + security headers,
CORS for IIIF consumers, gzip, read-only store connections, `/healthz`,
`robots.txt`, `leibniz index bench` for the p95 criterion). Going live is the
operator's runbook (`deploy/README.md`): a small VPS, the serving copy of the
store, the Meilisearch build, the DNS records, the image mirror on Cloudflare
R2 (an operator decision that diverges from SPECS §3.4's "never rehosted" —
recorded under Divergences; the code's default stays direct-from-GWLB) — and
the note to the GWLB before launch. `LICENSE` (Apache-2.0) and the issue form
the viewer's "Report an error" link opens are in place for the repository
going public. **518 tests**, ruff clean.

**Published (2026-09-16), CC BY 4.0, Zenodo community `leibniz`:** the project
statement (doi:10.5281/zenodo.22782813), the corpus census
(doi:10.5281/zenodo.22782815), the PHILIUMM reproduction + VLM benchmark
(doi:10.5281/zenodo.22782817), and the retro-aligned ground-truth reports
(doi:10.5281/zenodo.22782819); mirrored at evanatlas.com/research.

**Strategy review (2026-09-16) — recorded, not built:** `NOTES.md` (accuracy
levers, the Calculemus rescope, the four Academy seams, loose ends) and the
**C3 amendment in `PROMPTS.md`** (expect ~1 CER point from v2; vision
re-extraction, staged training, confidence filtering, n-gram LM decoding).
SPECS §1.5's Bullinger claim corrected (their models are 9.1–9.2% CER; 6.5% is
their GT's own error rate).

**🏁 C1 corpus run COMPLETE (2026-09-11): the full Nachlass is machine-read.**
**236,210 of 236,795 pages recognised (99.75%)** — **13,508,625 lines** with
text, per-line confidence and full provenance in the store. The remainder is
enumerated, not lost: 569 pages skipped with recorded reasons (blanks, specks,
oversize foldouts, degenerate geometry) and **16 pages permanently unfetchable**
(GWLB delivery URLs in a redirect loop — works `00068368`/`00068744` a.o.; worth
reporting upstream). Image cache: 236,779 pages / **395.6 GB**.
`reports/htr-v1-sample.md` and `reports/census.md` are regenerated from the
store with the real numbers. The run took ~6 weeks wall clock on one 16-core
GTX-1660-Ti desktop (WSL2), the last week in the final architecture: **4
sharded CPU segmentation workers + 1 concurrent GPU recogniser** (~515 and ~940
pages/hour respectively), all stages resumable and re-runnable via one operator
script. Every robustness fix that made this survivable is logged in the Phase
log below. **C2 GT minting is now unblocked on the HTR side** — its remaining
inputs are the katalog full scrape (Open Q #3) and the §70 page anchors (Open
Q #13).

**C2 — GT factory at scale: the two data inputs that blocked minting are now
built and run at full scale (2026-09-11, this session).** (1) **Katalog:** every
§70-expired volume's records are scraped (`leibniz catalog scrape
--expired-volumes`: 31 volume slices, sub-cap by construction — the site
matches `bd` as a *substring*, so colliding volume numbers are deepened by
year; **24,916 records, 17,646 crosswalk links, 1,197
works**), yielding **17,162 §70 piece citations, 11,595
localizable to exact canvases** (crosswalk + folio resolver, 68 %).
(2) **Reading text:** the §70 volumes' free digital copies were located and
verified (archive.org public-domain scans with hOCR, the GWLB repositorium
PDFs, Potsdam's born-digital PDFs — **21 of 31 volumes readable**),
and a layout-aware extractor (`align/edition.py`) read **6,188
printed pieces / 26.2M characters of reading text** with page
anchors (Open Q #13's "page anchors" solved by the print's own running heads
and headings), joined to the katalog into the edition cache
(**10,029 manuscript witnesses with their piece's text**).
Cross-source agreement between two independent OCR layers of the same volume
(IA Tesseract vs GWLB ABBYY, 5 volumes) is the free extraction-QA
estimate: **81.6% mean agreement**. (3) The C1 HTR lines live on
the operator's machine, so `gt_lines` is still empty *here*: minting is one
runbook away (`reports/gt-factory.md`). The whole C pipeline is wired: pages
flow `pending → segmented → recognized` (C1), and §70-expired edition text is
retro-aligned onto those recognized lines to mint `gt_lines` (C2).

**Phase C1 — corpus segmentation + HTR v1 batch pipeline.** Built `leibniz
pipeline segment` / `recognize`: a status-driven, resumable, idempotent state
machine over `pages`, storing per-line geometry + text + confidence with
`status='machine'` and one `runs` row per batch (model@version, params, git SHA,
counts, wall time). Per-page failures are isolated and enumerated with a reason
(blank → `no_lines`, missing image, segmenter error). **Segmentation quality is
measured, not assumed:** every page gets a `page_stats` row (line count, region
coverage, line-height CV, overlap + short-line anomalies) — the signal the C2/C4
stratum heuristic reads. Engine-agnostic (kraken segmenter/recogniser injected;
fakes in tests), GPU-aware (`--device`), `--redo`/`--sample`. The live 500-page
run needs the kraken stack + image pull (absent here); the pipeline is built and
offline-tested (+27 tests) with the operator runbook + GPU/cost estimates in
`reports/htr-v1-sample.md` (regenerated by `leibniz pipeline report`).

**Phase C2 — GT factory at scale. ✅ The B2→C2 localization bet holds.** Built
`leibniz align factory`: for each §70-expired volume it enumerates the pieces
(katalog `aa_refs` × `legal.py`), localizes each scan (A3 crosswalk → work; **the
folio resolver** turns the katalog `Bl.` range into exact canvases via the IIIF
folio labels C1 stored — Open Q #10 **solved**), gathers the piece's C1 HTR lines,
aligns the §70 reading text onto them (**anchor-guided banded aligner** for
long multi-page pieces and for edition texts far longer than the piece —
B2's blocking gap, now built and exact-vs-full-DP tested), sets the mint
threshold **per stratum** (fair copies 0.55 … heavy revision 0.72 — Open Q #11),
and mints `gt_lines` with provenance + the license gate (§70 → `open`;
Transkriptionspool → `nc`, never in a CC BY export). Below-threshold lines are
discarded; re-minting is idempotent. **Live-validated (this session, OpenAI key
supplied):** the vision reading-text extraction + `assess_extraction` QA (Open Q
#12) run on real Leibniz edition print (Gerhardt II, 1875, PD) — `gpt-4o`
faithfully transcribed the reading text and **dropped the running head / page
number / signature**, and the two-model QA flagged **1/2** pages (mean agreement
0.67), catching exactly the code-switched page where the control model dropped
~60% of the text. Full deliverable `reports/gt-factory.md`
(+ `reports/gt-factory-extraction-qa.json`); regenerated by `leibniz align
gt-report`. Machinery offline-tested (+33 tests). **The mint has run
(2026-09-15/16, operator's store, six shard workers, ~2 h + a cleanup pass):
297,424 open-bucket lines** — fair_copy 9,913 · light_revision 96,175 ·
heavy_revision 190,162 · scrap 1,174 — from 6,383 minted piece citations,
**5.9× the ≥50k target**, after two live failures the run itself surfaced and
that are fixed (the aligner OOM on volume-length edition texts; WAL lock
collisions between workers). What the factory cannot measure is *precision*:
the C2 gate is the 200-line hand audit, now tooled (`leibniz align
audit-sheet` → an HTML sheet of line strips with verdict buttons;
`audit-score` → per-stratum precision with Wilson intervals and the
corpus-weighted figure against the 95 % gate).

### Prior gate (retained): Phase B2 (retro-alignment prototype) — ✅ GO.
The aligner (`src/leibniz/align/`) mints **98.8% of lines at 97.5% precision** on
the PHILIUMM val split under real HTR (diplomatic; 98%+/97% across divergence
conditions), with **zero** edition-omitted false mints — confidence withholds
lines with no edition counterpart, so a dropped passage costs *yield, not polluted
GT*. C2 is built directly on this engine. Full deliverable:
`reports/alignment-prototype.md`.

### Prior gate (retained): Phase B1 (benchmark harness + PHILIUMM reproduction) — ✅ GO.
The engine-agnostic HTR evaluation harness (deliverable **D5**) is built and, run
against the PHILIUMM model on its own 1,878-line val split, **reproduces the
claimed CER**: measured **7.95%** (95% CI 7.49–8.46) vs the self-reported
**8.33%** — Δ **−0.38**, inside the ±1-point gate. It lands *exactly* on the
model's own `metadata.json` figure (accuracy 0.9205 → 7.95% char error). WER
27.04% vs claimed 28.56%. **Verdict: build on the PHILIUMM model** (unblocks the
C phases; B2 too). Full deliverable: `reports/philiumm-repro.md`.

Earlier this cycle: **Phases A2 (image cache) and A3 (katalog crosswalk)** —
complete. Both depend only on A1 (done). A0→A1→A2→A3 are all green.

### Phase B1 in numbers (this session)

- **CER 7.95%** (95% CI 7.49–8.46), **WER 27.04%** on 1,878 val lines, `philiumm`
  policy (NFD + whitespace-collapse — the model's own training normalization).
- **464 / 1,878 (24.7%) lines character-perfect**; macro-CER 9.16% (the short
  marginal-fragment lines carry the tail, which is why the headline is micro-averaged).
- **Normalization sensitivity:** philiumm 7.95% · lenient 7.61% · strict 7.95% —
  normalization moves the number <0.4 pt, so it is **not** the source of any gap.
- **Frontier-VLM comparison (RAN, OpenAI key supplied):** on a seeded 150-line
  subsample, zero-shot vision LLMs are **4–6× worse** than the fine-tuned HTR
  model (Kraken 8.19% on the same lines): **gpt-4o 45.87%**, **gpt-4.1 38.62%**,
  **gpt-4.1-mini 34.79%** CER. Counterintuitively the *smallest* model won among
  the three — the flagships more often "modernize"/normalise the archaic spelling.
  Total API cost **$0.49** (450 calls; usage captured from each response). First
  published LLM-on-Leibniz numbers.
- **Throughput:** ~1,878 lines in ~160 s on CPU (batch 8), no GPU.

### What was built (B1) — deliverable D5

```
src/leibniz/htr/
  metrics.py    CER/WER, edit distance, the named NormPolicy (frozen recipe),
                micro/macro aggregation, bootstrap CIs (deterministic, seeded)
  bench.py      LinePair input · Engine protocol · transcribe_pairs +
                score_hypotheses + evaluate · EvalResult · per-line JSONL dumps ·
                the frozen protocol `b1-2026-07` · EchoEngine (tests)
  engines.py    KrakenEngine (safetensors via kraken.models.loaders.load_models;
                pre-extracted-line inference, valid_norm=False) + AnthropicEngine
                + OpenAIEngine (Claude/GPT vision over httpx; skip without a key;
                capture token usage + $ cost)
  data.py       loaders: HF parquet val split · image+.gt.txt dir · seeded subsample
  artifacts.py  cache-first streaming fetch of the Zenodo model + HF val split
  report.py     render reports/philiumm-repro.md + gate verdict + VLM-panel table
  cli.py        leibniz bench {fetch, protocol, run, repro}  (+ --reuse-hyps,
                --with-llm --llm-engine {anthropic,openai} --llm-model … [panel])
reports/philiumm-repro.md          B1 deliverable (measured vs claimed, honest)
reports/philiumm-repro.lines.jsonl per-line error-analysis dump (1,878 rows)
pyproject.toml   optional `bench` extra (kraken, pyarrow) — lazily imported
```

The heavy stack (kraken, torch, pyarrow) is an **optional** extra, imported
lazily: the harness, its metrics, and all its tests run without it. Artifacts are
CC BY 4.0, cached under `data/models/`, `data/gt/` (gitignored).

- **A2** gives us a resumable, checksummed local image cache and — as a bonus —
  the **full `pages` table** (236,795 rows), derived **offline** from the METS
  we already cached. A live dev slice of **80 images** was pulled and verified.
- **A3** joins the BBAW Ritter-Katalog to our works. A 6-query live sample
  already crosswalks **1,094 / 2,225 works (49.2%)** with **99.96% GWLB-link
  resolution**; the full scrape (an operator job) is documented.

Everything is green and offline-testable:

- `uv run ruff check .` / `ruff format --check .` — clean (72 files).
- `uv run pytest` — **236 passed, 1 skipped** (was 171; +65 for the HTR harness).
  The one skip is the parquet-loader test, which needs the optional `pyarrow`.

Bulk artifacts (the SQLite store, `data/images/`, `data/katalog/`, `data/oai/`,
and now `data/models/`, `data/gt/`, `data/bench/`) are gitignored. Committed
deliverables: `reports/census.md`, `reports/crosswalk.md`, and **new**
`reports/philiumm-repro.md` (+ its per-line `.lines.jsonl` error dump).

### ⚙️ Delivery-model correction (revises the A2 prompt; see Divergences)

The A2 prompt assumed the IIIF Image API for every page. Per the A1 "Major
drift", only ~1/3 of works are IIIF-served. **Resolution:** the GWLB METS
`fileSec` — already inside the cached OAI ListRecords XML — carries an
authoritative `DEFAULT` JPEG URL (`…/content/{id}/jpgs/default/{seq:08d}.jpg`)
for **every** page, IIIF and static alike. A2 caches that uniform derivative
across all 236,795 pages; the IIIF Image API service URL is still stored per
page (`pages.image_service_url`) for D2 deep-zoom, but is not the cache source.
This makes A2 uniform, offline-derivable, and free of URL guessing.

### What was built (A2 + A3)

```
src/leibniz/images/            IMAGE CACHE (A2)
  pages.py     derive pages (delivery URLs) from cached METS fileSec — offline
  jpeg.py      dependency-free JPEG dimension + truncation reader (SOF/EOI walk)
  fetch.py     fetch (resumable, integrity-retry) / verify / stats(+census)
  cli.py       leibniz images {pages,fetch,verify,stats}
src/leibniz/catalog/           KATALOG CROSSWALK (A3)
  shelfmarks.py  robust LH/LBr/Marg/LK normaliser (Roman↔Arabic, Bl./S., Stück)
  scrape.py      23-column result-table parser + polite enumeration (5000-cap aware)
  crosswalk.py   gwlb_link (1.0) primary + shelfmark (0.7) secondary matcher
  report.py      reports/crosswalk.md
  cli.py         leibniz catalog {scrape,crosswalk,report}
  __init__.py    KATALOG_ATTRIBUTION (CC BY 4.0)
src/leibniz/db.py              + pages image-cache columns & migration; katalog_records
                               + crosswalk typed helpers; git_sha()
reports/crosswalk.md           A3 deliverable (match-rate by set/method, honest)
reports/census.md              + "Image cache (Phase A2)" section
tests/                         +80 tests; fixtures/{images/thumb_sample.jpg,
                               mets/listrecords_filesec.xml, katalog/results_sample.html}
```

### A2 in numbers

- **`pages` fully populated: 236,795 rows** (static 159,162 · iiif 77,633; 27
  zero-page works) — matches the A1 census exactly. Derived offline in ~34 s from
  `data/oai/`; **resolves Open Q #2.**
- **Dev slice pulled live:** `00067974` (LH 35, 1, 13 — IIIF, 40 pp) +
  `DE-611-HS-854976` (LBr. 464 — static, 40 pp) = **80 images, 126.3 MB**;
  `images verify --deep` → 80/80 OK, 0 corruption.
- **Mean page ≈ 1.6 MB → projected full pull ≈ 365 GB** (within SPECS' 200–400 GB).
  Measured dimensions 1098×1793 … 4921×4394 px.
- Fetch is **sequential**: with one GWLB host at ≤1 req/s (SPECS §7.4), per-host
  concurrency is a no-op, so throughput is set by `--min-interval`, not threads.

### A3 in numbers (live 6-query sample)

- **16,177 records scraped → 15,382 distinct**; **12,582 crosswalk links**.
- **Records matched: 12,535 / 15,382 (81.5%).**
- **Works matched: 1,094 / 2,225 = 49.2%** — from *six* queries.
- By method: **gwlb_link 12,384 (+5 unresolved) · shelfmark 198.** Link→work
  resolution = **99.96%** (the join is essentially exact).
- **3 of 6 queries hit the 5000-row cap** (Reihe I,1 / I,2 / `sign_ol=LH 35`) —
  flagged, not silently truncated. Full ≥80% coverage needs the full scrape.

---

## Phase log

### D — the image mirror (2026-09-16, operator decision; see Divergences) ✅

The public site serves its own copy of the GWLB delivery scans. Built as a
switch, default off:

- **`web/images.py`** — `ImageSource`: with `LEIBNIZ_IMAGE_BASE_URL` set,
  every cached page's display URLs become `{base}/{work_id}/{seq:04d}.jpg`
  and `{base}/thumbs/…` (the cache's own layout, `images/fetch.cache_relpath`,
  so the bucket is the cache directory uploaded as it is), delivered as a
  static image (no IIIF service); pages never cached keep their GWLB URLs.
  The page API adds `image_origin` and `source_image_url` (the GWLB URI,
  always); search hits get mirror thumbnails; the manifests paint the mirror
  copy and record the GWLB source per canvas; annotations keep `leibniz:imageUri`
  on the GWLB; `attribution()` has a mirror wording for the web surfaces while
  the dataset cards keep the original line. `/api/stats` reports
  `images.origin`, and the server stamps `<html data-image-origin>` into the
  shell (read once, ETag + 304) so the viewer's footer, page attribution and
  About texts switch without another request (EN + DE strings added).
- **`leibniz images thumbs`** (`images/thumbs.py`) — one thumbnail per cached
  page, 320 px wide, Pillow decoding at reduced scale from the JPEG DCT, all
  cores, resumable; **`leibniz images check-mirror`** HEADs a sample of the
  mirror and compares sizes with the cache manifest (`rclone check` is the
  full check). Runbook §12 covers the R2 bucket, the custom domain, rclone.
- Caddyfile: `www.` → bare domain; env examples name the mirror.

### D — deployment kit, public-traffic hardening, public-repo prep (2026-09-16, later session) ✅

The serving layer was finished but nothing existed to put it on a host. Built,
offline-tested and documented so that going live is an operator runbook
(`deploy/README.md`), not another coding session:

- **`deploy/`**: `install.sh` (idempotent Debian/Ubuntu bootstrap: users,
  directories, uv + venv as the service user, the Meilisearch binary with a
  generated master key, Caddy from its apt repository, the units),
  `leibniz-legible.service` + `meilisearch.service` (hardened sandboxes, the
  app bound to localhost), `Caddyfile` (auto-TLS, zstd/gzip, HSTS, a JSON
  access log kept seven days, an optional edge rate-limit block),
  `env.example` / `meilisearch.env.example` / `caddy.env.example`,
  `prepare-store.sh` (desktop: WAL checkpoint → `VACUUM INTO` → integrity
  check → SHA-256; a compact rollback-journal copy the read-only app opens
  without sidecars), `meili-search-key.sh` (a search/stats-only key, so the
  master key never reaches the serving process), and
  `docker-compose.prod.yml` + a root `Dockerfile` (uv multi-stage, non-root,
  healthcheck on `/healthz`) as the all-container alternative. The compose
  file validates (`docker compose config`, required variables enforced); the
  image build itself is unverified here — no Docker daemon in this
  environment.
- **`leibniz serve`** takes every option from the environment
  (`web/settings.py`: `LEIBNIZ_DB_PATH`, `LEIBNIZ_SEARCH_BACKEND`,
  `LEIBNIZ_BASE_URL`, `LEIBNIZ_WORKERS`, `MEILI_API_KEY` …), runs
  `--workers N` through an ASGI factory (`web/asgi.py`), and `LEIBNIZ_DB_PATH`
  is now honoured by every command (`.env.example` documented it; nothing
  read it).
- **Hardening in the app** (`web/middleware.py`, so every way of running it
  is covered): a per-client token-bucket rate limit on `/api`, `/manifests`,
  `/annotations` (default 10/s, burst 40, `429` + `Retry-After`, bounded
  memory), security headers with a CSP (`script-src 'self'`; the viewer's one
  inline script moved to `static/boot.js`), CORS `*` on the JSON routes so
  Mirador elsewhere can load the manifests (D7 needed it and lacked it),
  gzip (a 3,500-page manifest: 2.5 MB → 62 KB), `no-cache` on the viewer
  shell, `/robots.txt` closing the machine endpoints to crawlers (one walking
  the manifests would pull every GWLB image), every store connection
  `mode=ro` + `query_only`, Meilisearch outages answered with `503`
  (`/api/stats` and `/healthz` degrade instead of raising), and
  `GET /healthz` for the process manager and an uptime monitor.
- **The giants** (works of 1,000–3,500 pages): the work and manifest
  endpoints run one query per work (`line_summaries_by_page`, a `NOT EXISTS`
  probe on the lines' covering unique index) instead of one per page.
  Measured on a synthetic 3,500-page × 60-line work with a partial re-run:
  180 ms against 228 ms for the per-page loop, the fastest of five plans
  tried (`GROUP BY` and window forms were slower). So the loop was never the
  problem the previous session guessed (SQLite answers a page-keyed query in
  ~60 µs); the gain is ~20 % and the real cost was payload size, now gzipped
  (`/api/works` for that giant: 238 ms end to end, 485 KB → 30 KB).
- **`leibniz index bench`** (`search/bench.py`): p50/p95/max over HTTP for
  a built-in list of fifty Nachlass queries (with misspellings for the typo
  tolerance) or a file of real ones, `--concurrency`, exit 1 when p95 misses
  SPECS §3.3's 500 ms — the measurement step of the runbook.
- **Public-repo prep**: `LICENSE` (Apache-2.0 verbatim; declared in
  `pyproject`/README, absent until now),
  `.github/ISSUE_TEMPLATE/transcription-error.yml` (an issue form; the
  viewer's "Report an error" link now opens it with the page id and URL
  prefilled), Issues confirmed enabled on the repository.
- **Verified**: 504 tests (+29), ruff clean; every viewer route driven under
  Playwright/Chromium against the real app with the CSP and the rate limit
  on (EN/DE, search, work, page with OpenSeadragon on a same-origin image,
  about, a 404): zero CSP violations, zero console errors; the limiter trips
  at the configured burst.
- **Follow-up, same day — the kit against a real Meilisearch (v1.53.2 binary,
  the version now pinned in `install.sh` and both compose files).** Two
  things the fakes had hidden: (1) on current Meilisearch, deleting an index
  that does not exist is a task that *fails* with `index_not_found` (a 404
  was the pre-1.0 behaviour the fake copied), so the very first
  `leibniz index build --backend meili` on a fresh server aborted — the
  backend now ignores exactly that failure, and the fake fails like the
  server; (2) Meilisearch creates `dumps/` in its working directory at
  startup, which under the unit's `ProtectSystem=strict` is a
  permission-denied crash — reproduced as an unprivileged user with a
  read-only cwd, fixed with `WorkingDirectory=/var/lib/meilisearch` and
  explicit `MEILI_DB_PATH`/`MEILI_DUMP_DIR`/`MEILI_SNAPSHOT_DIR`. Also:
  `install.sh` runs git and uv as the service user (git refuses to act as
  root on another user's checkout, which would have broken every re-run),
  restarts Caddy only once a real domain is configured, and installs the
  pinned Meilisearch release only when absent (an upgrade must be
  deliberate: a newer binary refuses an older index); `leibniz index
  status/query` accept `MEILI_API_KEY`. Then the full path end to end with
  the real server: search-only key created and confined (document writes
  and key listing 403), index built on a fresh server, `leibniz serve
  --workers 2` healthy, the misspelt `calculemvs` finds *Calculemus*,
  `/api/stats` served from the build metadata through the search key,
  `leibniz index bench` 60/60, and with Meilisearch stopped: search 503,
  pages 200, `/healthz` degraded. That bench also exposed a 40 ms stall on
  every kept-alive request after the first when `--workers` > 1 (wall p95
  52 ms against a 1 ms backend): uvicorn's own shared listening socket is
  created with ``proto=0`` and asyncio sets ``TCP_NODELAY`` on accepted
  connections only when the socket says IPPROTO_TCP, so Nagle's algorithm
  met the peer's delayed ACK. `leibniz serve` now binds its own
  IPPROTO_TCP socket for the multiprocess supervisor — 44 ms → 1–3 ms per
  request, bench p95 3 ms with two workers. And the bench itself now paces
  its launches (8/s, under the app's 10/s limit) and reports `429`s apart,
  so on the production configuration it measures the server rather than
  its own rate limiting.

### D1–D3 — search, viewer, IIIF, releases, built on v1 (2026-09-16) ✅

Built the whole serving layer against the v1 store, offline-tested end to end
(seeded store → index → API → viewer screenshot under Playwright):

- **D1 search** (`src/leibniz/search/`): `documents.py` (one doc per recognised
  page: latest run per line, majority language, `page_stats.stratum_heuristic`,
  katalog records rendered as `AA I,3 N. 12` labels), `normalize.py` (the
  aligner's fold minus struck-text elision, shared by index and query),
  `snippet.py` (hits marked in the *original* text via the folded→original
  offset map; the only HTML the API emits), `fts5.py` (contentless FTS5 over
  the folded text + title/shelfmark/AA columns weighted ×3 in bm25; prefix
  matching from 3 chars; filters as column predicates), `meili.py` (plain httpx;
  drop → create → settings → batched documents, each awaited on the task queue;
  doc ids with `:` → `_`), `cli.py` (`leibniz index build|status|query`). The
  build records corpus statistics (counts + confidence histogram) in the index
  for `/api/stats`.
- **D2 API + viewer** (`src/leibniz/web/`): `api.py` (`create_app`; per-request
  store connections; latest-run line selection; bbox from polygon; prev/next;
  404s as `{"detail"}`; 503 when no index), `iiif.py` (Presentation 3 manifest
  per work wrapping GWLB image services; annotation page per page with
  `supplementing` TextualBody annotations targeting `#xywh`, provenance under
  the `leibniz:` JSON-LD namespace), `attribution.py` (one source for the
  three attribution lines), `geometry.py`, `cli.py` (`leibniz serve`,
  `--check` lists routes). The viewer (`static/`, 15 files + vendored
  OpenSeadragon 5.0.1, 624 KB) is plain ES modules served by the app at `/`,
  `/search`, `/work/{id}`, `/page/{id}`, `/about`; 177 i18n keys EN + DE;
  no-JS search form; dark mode; phone width; zero axe violations.
- **D3 releases** (`src/leibniz/release/`): `export.py` (row generators for
  inventory / transcriptions / gt; latest run per line; NC rows excluded;
  chunked Parquet via pyarrow or gzip JSONL; `MANIFEST.json` with SHA-256s),
  `cards.py` (the dataset cards), `cli.py` (`leibniz release export|checklist`);
  `reports/release-checklist.md`, `reports/tier1-final.md`.
- `docker-compose.yml` (Meilisearch), `.env.example` (`MEILI_*`), `pyproject`
  extras `web` + `release` (fastapi/uvicorn in the dev group so tests run).
- Tests **+47** (475 total): folding/snippets, documents, FTS5, Meilisearch
  against a fake server, IIIF builders, the API over `TestClient`, exports
  (JSONL always, Parquet when pyarrow is present), CLIs.

### C1 — corpus-run robustness, from the first live runs (2026-07-29/30)

The operator's first real 500-page runs (GPU + WSL/CPU) surfaced four defects the
offline fakes could not; all are fixed with offline regression tests:

1. **Confidence was a pixel cut position** (`_tok_conf` now picks the [0,1]
   posterior field, else `None`) — Open Q #15's exact worry.
2. **`--device cuda` crashed both stages** (kraken wants `(accelerator, device
   count)`, not a device string) and **segmentation ignored its device**.
3. **A sub-5px baseline sank its whole page** (17 % of the sample); such lines
   are now filtered up front and just left untranscribed.
4. **A "poison page" killed recognition entirely, four runs in a row** — the
   process died (`Terminated`, no traceback) at the same page each time, once
   with PIL `1.0 / w` divide-by-zero warnings, once silently. Reading kraken
   7.0.3's `extract_polygons`: it rectifies each line's boundary into
   along-baseline × perpendicular coordinates and sizes the output crop from
   their **raw, unclamped extents** — degenerate stored geometry (zero-length
   segments → NaN mesh quads; far-flung rectified points → an OOM-scale
   allocation the OS kills mid-way). Five layers now prevent the whole class:
   (a) same-pixel consecutive points are collapsed before cropping;
   (b) `pipeline/geometry.py` **replicates kraken's `output_shape` arithmetic**
   (pure Python, offline-tested) and drops any line whose implied crop exceeds
   `max(4× page area, 24 MPx)` — the OOM class caught *before* allocation;
   (c) PIL-attributed `RuntimeWarning`s are escalated to errors inside
   `crop_lines` (a NaN'd transform never yields a usable crop);
   (d) a failed page-crop falls back to per-line cropping, so a poison line
   costs *the line*, not the page; and (e) a SIGALRM **crop deadline**
   (120 s/page, 30 s/line) converts any residual in-process stall into the
   normal skip path. `leibniz pipeline audit [--page ID]` prints any page's
   per-line geometry verdicts from the store alone (no kraken) — the operator's
   first tool when a page skips or dies.

**Root cause, finally caught live** (rlimit'd probe on the operator box, page
`00051012:0070` — a small scrap page segmented into 21 speck "lines"): the
killer was never the crop — it was **recognition**. One line's dewarped crop is
a ~900×1 px empty mask sliver; `ImageInputTransforms` resizes crops to model
input height *preserving aspect ratio*, so the sliver becomes >100k px wide,
the whole batch pads to it, and a single `F.conv2d` allocates **5.3 GB**
(`DefaultCPUAllocator` enforce-fail under the probe's rlimit; under normal
Linux overcommit it "succeeds" and the OS kills the machine — invisible to
every in-process handler, which is why layers a–e couldn't catch it). Fixes:
the pipeline now judges the **actual crop raster** before recognition (PNG
header peek, no imaging dep: `min side < 4 px` or `aspect > 100:1` →
`sliver_crop:{w}x{h}`, line dropped); `KrakenEngine` refuses transformed lines
wider than 10k px (`("", None)` placeholder — backstop for any caller); and
`pipeline segment/recognize --mem-limit-gb N` caps the process address space so
any residual runaway allocation fails one page instead of the box.

**Operator validation (2026-07-30): the crash class is closed.** A full 431-page
CPU pass completed with zero crashes; the poison page recognised with its sliver
enumerated (`sliver_crop:900x5`), and the original gate finally reports
**`conf > 1` count = 0** (Open Q #15's field shape confirmed live at scale).
Two calibrations from that run: an address-space cap must clear torch's
*virtual* arena — 6 GB starved it after ~55 pages (alloc-fail skips); use
**`--mem-limit-gb 12`+** (virtual ≠ resident). And a batch padded to its widest
line multiplied conv memory (a 722 MB single alloc) — `KrakenEngine` now flushes
on a padded-area budget (`n × widest ≤ 64k` width-units), bounding peak memory
on CPU and GPU alike.

**Concurrency root cause found and fixed (2026-08-27).** The first genuinely
concurrent run (shard workers + recogniser) died with `database is locked`
despite WAL + a 30 s busy timeout: each stage walked its work list with one
**long-lived read cursor on the same connection it writes with**, pinning a WAL
snapshot; the first write after any *other* worker commits then fails with an
un-retryable snapshot-upgrade BUSY (the timeout cannot help). Single-writer
runs never trip it — true concurrency always will. Both stages now page their
work lists in small **closed keyset batches** (`WORK_CHUNK`,
`iter_pages_by_status(after=…)`): no open cursor survives into a write, and the
keyset advances over raw batches so sparse shards terminate. Along the way an
orphaned Aug-19 worker (never killed by an incomplete cleanup) was found to
have quietly segmented 46,857 pages over 8.3 days before exiting — enumerated
in `runs`, and the reason corpus progress outpaced the single-worker estimate.

**Corpus throughput, measured (2026-08-16): segmentation is CPU-bound at
~140 pages/hour** — 47,448 pages (20%) segmented in ~12 days; `nvidia-smi`
shows the GPU loaded but ~idle (9%), because kraken's per-page cost is
dominated by single-threaded CPU vectorization, not the neural pass. On the
operator's 16-core box that left 15 cores idle and implied 56 more days.
Answer: **sharded parallel workers.** `segment`/`recognize` now take
`--shard i/N` (stable crc32 over `work_id`; shards are disjoint, complete, and
keep a work's folios together), and `db.connect` enables WAL + a 30 s busy
timeout so N per-page-committing processes coexist safely. The operator
runbook runs 1 CUDA + 3 CPU segment workers (~3–4×, ≈2–2.5 weeks for the
remainder); recognition stays a single GPU worker (~3.5 s/page measured).

**Corpus-run incident (2026-08-02): a stale command block without `--images`
mass-skipped the corpus in the DB.** The full ~395 GB pull had completed
(236,779/236,795 verified, 16 redirect-loop failures) with the cache moved to a
second drive; a re-run of an older snippet then pointed segment/recognize at
the default (deleted) root and marked ~236k cached pages `image_missing` in one
pass. No data was harmed — images, manifest (sha256/local_path), geometry, and
recognitions all intact — and statuses were restored from the manifest
(`skip_reason='image_missing' AND sha256 IS NOT NULL` → back to
segmented/pending). Two guards now prevent recurrence: a **preflight** on both
stages aborts (marking nothing) when ≥5 sampled cached pages all lack files
under the given root ("wrong --images root?"), and segment skips **oversize
images** (> 80 MPx; ~120 MPx foldouts observed) with a reason instead of
risking an OOM — the suspected killer of the first corpus segment attempt,
which died ~1,550 pages in.

**CUDA smoke (100 fresh pages): segmentation ran (7,496 lines, 75/pg —
Marginalien-dense), recognition failed 100/100** with `Input type
(torch.FloatTensor) and weight type (torch.cuda.FloatTensor)`: kraken's
`_rec_predict` never moves inputs — after `prepare_for_inference` puts the net
on the accelerator, the caller owns the transfer. `KrakenEngine` now records
the net's parameter device at load and moves each batch onto it (`lens` stays
on CPU for sequence packing). Same smoke exposed the kraken-7 token layout
`(grapheme, start, end, conf)`: front-to-back `[0,1]`-scanning misread
`start == 0` (every line's first token) as confidence 0.0 — `_tok_conf` now
scans from the end, where the posterior always lives. **Open calibration:**
GPU segmentation measured 18.8 s/page on the dense dev slice — verify GPU
engagement (`nvidia-smi` during a run) and re-estimate the corpus segment pass
on mixed sets; the ≈260 GPU-h estimate assumed 3–6 s/page combined.

(1–3 landed as `140d58d`; 4 across this entry's commits.) Live evidence: real
posteriors ≈0.6–0.9 populate at scale (CPU: 498/500 pages, 23k lines, mean
conf 0.771, `conf>1` = 0 — the C1 validation gate is **passed**). Remaining
operator gate: the CUDA recognition re-run, then the corpus pass.

### C2 — close-out: the hand audit is preliminary; gate deferred to C3 (2026-09-16)

The operator judged **20 of the 200** sheet lines and stopped, saying so
plainly: not confident in the verdicts, wants them treated as preliminary
and open to review. Recorded as such; C2 is closed on the mint, not on the
gate.

- **What the 20 say:** all in `fair_copy` (the sheet lists strata in
  order): 12 correct · 0 boundary · 5 wrong · 3 unreadable → 70.6 %
  precision on 17 scored, Wilson 47–87 % — a FAIL as written
  (`reports/gt-audit.md`, committed from the operator's machine with the
  two CSVs).
- **What the second witness says:** `audit-score` now cross-checks every
  verdict against the folded similarity between the minted text and the HTR
  reading of the *same strip* (the crops are in the page's own pixel space —
  the C1 segmenter never resizes). **All five "wrong" lines agree with the
  machine reading at 0.82–0.98** (e.g. minted "but, qu'il seroit trop long
  de rapporter icy." vs HTR "… rapporter ici."; "la difficulté demeure
  toujours à multiplier cette presence" vs "la diffienete demeuve toujours
  …"): the machine read the words the edition gives, on that strip. Read as
  misjudged verdicts — the auditor's own reading of themselves — the fair-copy
  sample is 17/17. The three "unreadable" are two short lines and an Italian
  one. None of this is a pass: 17 lines, one stratum, one non-specialist.
- **Tooling:** `audit-score --lines` (default: the sheet's own CSV) writes a
  "Second witness" section listing verdicts to re-check (a *wrong* or
  *unreadable* at ≥ 0.8 agreement, a *correct* below 0.5) with both texts
  side by side; +1 test.
- **Decision:** proceed to C3 with the gate **deferred**, on two grounds.
  (1) The audit gives no evidence of a precision problem, only of an
  unfinished audit. (2) C3's design already contains the decisive test: the
  ablation *PHILIUMM GT alone* vs *+ C2 GT* on the page-disjoint held-out set
  measures what the minted lines are worth without anyone reading a hand.
  A GT that is 30 % misaligned would show up there as no gain or a loss. The
  hand audit stays open (Q #18) for whoever can read the hands; the sheet
  and the flagged list are in the repo.

### C2 — the mint ran; hand-audit tooling (2026-09-15/16) ✅ mint · ⏳ audit

The operator's runbook run, with the fixes below merged in between:

- **Pass 1** (six `--shard i/6` workers, no `--resume`, ~1 GB RAM total,
  ~2 h): **317,365 pairs from 6,383 pieces** at 30–45 pieces/min/shard.
  Skips: 5,567 not localizable · 4,314 no edition text (the ten volumes
  without a free copy, Open Q #16) · 141 no canvases · 11 no HTR lines ·
  **746 `error:OperationalError: database is locked`** — the C1 WAL
  stale-snapshot failure on the per-piece commit (4.3 % of pieces; each one
  skipped, the shard alive thanks to the per-piece guard).
- **Cleanup pass** (`--resume`, after `factory.write_pairs` moved to
  `BEGIN IMMEDIATE` + retries): re-minted the 746, +23,680 pairs on the five
  shards with a summary; three shards then crashed on the *run bookkeeping*
  stamp — the last deferred write left — after all their pieces; fixed by
  routing every factory write through `with_write_lock`.
- **Store:** `gt_lines` = **297,424** rows, all `open` (§70 sources only):
  fair_copy 9,913 · light_revision 96,175 · heavy_revision 190,162 · scrap
  1,174. Lower than the log totals (341k pairs) because citations overlap —
  a re-minted piece replaces the rows of shared line refs; the store counts
  distinct lines. **5.9× the ≥50k target**; `reports/gt-factory.md`
  regenerated and committed from the operator's machine.
- Read of the strata: two thirds of the minted lines sit in
  `heavy_revision`, the stratum held to the 0.72 threshold — the Nachlass
  is mostly drafts, and the heuristic (Open Q #11) calls most pages so;
  C4 recalibrates it against the audit.
- **Hand-audit tooling** (`align/audit.py`, CLI `audit-sheet` /
  `audit-score`, +9 tests): draws equal numbers per stratum (a
  proportional draw would give fair copies a handful), cuts each line's
  strip from the cached page by its C1 polygon, writes one self-contained
  HTML sheet (strip · minted text · HTR text · correct / boundary / wrong /
  unreadable, saved in the browser, downloaded as CSV); the scorer reports
  precision per stratum with Wilson 95 % intervals, the *usable* rate
  (boundary-off lines included) and the corpus-weighted precision against
  `GATE_PRECISION` (95 %) as `reports/gt-audit.md`. **The audit itself is
  the operator's next step** (the strips need the image cache on drive D).

### C2 — the mint's first live runs: workers OOM-killed → aligner rebuilt (2026-09-15)

The operator launched the mint on the WSL box (16 cores, an 11 GB VM) with 12,
then 8, then 6 shard workers on the JSONL cache; every attempt took the VM
down. `dmesg` finally named it: **one worker at 5.7 GB RSS**, not the sum of
many. Root cause, confirmed in the code and reproduced here:

- **`dp.align_banded` widened its band to the whole length difference**
  (`half = max(band, |n−m| + 8)`), so a piece whose edition text is far longer
  than its HTR spine got the *full matrix back*, at 5 bytes a cell. That shape
  is the norm, not an edge case: **186 of the 10,029 cached records carry
  >100k characters** (VI,6 N. 2, the Nouveaux Essais, is 753,788 characters
  and is cited by 6 records; one 497,888-character piece by 63) — a 100-line
  spine against one of those was ~15 GB.
- **Fix — `align/anchored.py`**: localize first, align second. Shared 8-grams
  of the folded texts (index the shorter side, scan the longer) → longest
  monotone chain (patience LIS, isolated outliers dropped) → a fixed-width
  band about the piecewise-linear path through the anchors → the DP in
  ~8k-row **chunks cut at matched runs** (each chunk a few MB, whatever the
  piece length). `dp.align_in_band` is the new core: per-row column windows,
  two rolling distance rows, a one-byte move table, per-side/per-end free
  gaps, and a hard `max_cells` guard; `align_banded` is reimplemented on it and
  now *refuses* a runaway band instead of allocating it. Pieces that share
  nothing with their text fall back to the null alignment (nothing minted)
  rather than a worker death.
- **Measured (synthetic, this box):** the crash shape (10k spine vs 120k
  text) — **44 MB peak, 1.9 s** (was ~6 GB and killed); a 300k-character
  treatise vs its 330k text — 112 MB, 46 s; real cache text (3k spine inside
  the 753k Nouveaux Essais) — **yield 0.98, 3.6 s**; exact vs the full DP on
  near-parallel pairs, chunk joins included.
- **Two GT-quality guards the same failure exposed** (`align.py`): the free
  edition overhang (insertions before the first / after the last HTR hit) no
  longer lands in the first/last line's slice — with a parent record's text
  served for a sub-piece it was the whole overhang; and a line is refused when
  the alignment inserts more edition characters into it than
  `max(12, its own length)` (an apparatus block or an omitted passage glued to
  a well-matched line — the matched fraction cannot see it). `AlignedLine`
  gained `n_inserted`.
- **Factory:** one bad piece can no longer end a shard — `run_factory` catches
  per-piece exceptions, rolls back, and records `skipped:error:<Type>`.
- **Live, two hours into the fixed run (six shards, ~1 GB used, ~2,000
  pieces and ~30k lines per shard):** three shards logged a piece
  `failed: OperationalError: database is locked` — the C1 WAL
  snapshot-upgrade failure again, now on the mint's per-piece commit: a
  deferred write that waits for another worker's commit fails at once with a
  stale snapshot (the busy timeout never runs). `factory.write_pairs` now
  takes the write lock first (`BEGIN IMMEDIATE`, one transaction per piece)
  and retries a lock collision with jittered backoff; the affected pieces
  are re-minted by a `--resume` pass (they carry no `gt_lines`).
- Tests **+13** (417 total: anchoring, localization both ways, chunk joins,
  the memory bound, the guards, projection); ruff clean. Also recorded: with
  unit costs and non-free HTR ends, the last ≤ `band` characters of a passage
  can scatter as chance matches over uncovered manuscript (Open Q #17).

### C2 — GT factory at scale, the inputs built and run (2026-09-11) ✅

The 07-29 build (below) mints nothing without three inputs; this session
built and ran two of them at full scale, so the factory now waits only for the
store that holds the C1 HTR lines.

- **Katalog sweep of every §70 volume** (`catalog/scrape.py` `scrape_volume`,
  CLI `--volume S,V` / `--expired-volumes`). Measured live: the katalog matches
  `reihe`/`bd` as **substrings** (`bd=1` returns volumes 10–19 too; the form's
  `*_exact` flags are ignored), and a bare-year `datum_bis` is exclusive — so a
  capped volume slice is re-run by year (`datum_ab=Y&datum_bis=Y1231`) and
  filtered client-side by the parsed AA column. 31 slices, 173 + 144 queries,
  ~10 min at ≤1 req/s: **24,916 records (17,562 with a GWLB
  link) → 17,646 crosswalk links, 1,197 works** (crosswalk works
  matched 1,197/2,225; the §70 volumes' records only — the full 70k scrape
  remains an A3 operator job). `parse_aa_refs` now keeps the katalog's
  *Unternummer*: `/ tlw.` (a partial witness) → `partial: true`, a page/line
  locus → `note`; only a single letter is a sub-piece.
- **Piece enumeration at scale:** **17,162 §70 piece citations · with
  work 12,385 · with folio range 11,617 · localizable
  11,595 (67.6 %)** — the folio resolver (Open Q #10)
  holds on real data across all 31 volumes (`leibniz align pieces`).
- **Volume sources** (`align/volumes_sources.py`, verified 2026-09-11):
  archive.org holds Trent University's scans of ~30 AA volumes (no access
  restriction, Tesseract hOCR + leaf images), the GWLB repositorium serves
  I,3/9/11–27, III,5–9, VII,3–8 (ABBYY text layer, **CC BY-NC channel**),
  Potsdam serves IV,1–10 born-digital, Münster's Internetausgaben (II, VI,4)
  require written permission (operator ask; never auto-fetched). **21
  of 31 expired volumes are readable**; 10 have no free digital copy (I,1, I,2,
  I,4, I,5, I,13, II,1 (1926), III,2, VI,2, VII,1, VII,2 — HathiTrust holds the
  1923–27 prints as US-PD; TELOTA/Göttingen ask for the rest). Preference:
  IA (unencumbered) > GWLB (flag for the lawyer memo) > Münster (ask).
- **Reading-text extractor** (`align/edition.py`, +11 tests): one
  layout model over hOCR and PDF text layers (`pdfplumber`, optional `gt`
  extra). Per volume it learns the body/apparatus type sizes (Tesseract 41/33
  px, ABBYY 10/9.5 pt, Potsdam 10.5/9 pt) and the paragraph indent; per page it
  peels the running head (which lists the pieces *starting* on the page — the
  anchor), cuts the apparatus block at the bottom, drops margin line numbers
  (also when OCR glues them to a line), detects piece headings (`13. GOTTFRIED
  CHRISTIAN OTTO AN LEIBNIZ`, OCR'd `i.`, ABBYY's small-caps-as-lowercase),
  skips the dateline/*Überlieferung* block until the body margin, and carries
  the current piece across pages; a garbled head never re-synchronises the
  piece, an unplaceable boundary drops the page's tail instead of
  misattributing it (precision over recall). Validated on three source types:
  I,6 hOCR 352/362 pieces, IV,1 Potsdam 52/52, I,11 GWLB 501/521; a leak
  heuristic flags 0.1 % of extracted lines.
- **Ingestion + edition cache** (`align/ingest.py`, CLI `leibniz align ingest` /
  `edition-cache`): cache-first fetch → extract → per-volume JSON with piece
  texts + page anchors; the cache join maps every katalog record citing an
  ingested piece to its text (sub-piece → parent fallback). **Run here:**
  6,188 pieces / 26.16M chars over 21
  volumes; **10,029 records carry reading text.** Cross-source
  QA on the 5 volumes with two independent OCR layers: mean
  agreement 81.6% (54 of 200 pieces
  flagged >10 % CER).
- **Report** (`reports/gt-factory.md`, regenerated): sources/terms table per
  volume, extraction + QA numbers, the priced vision upgrade (Sonnet 5 / Opus 5
  / gpt-4o-class per page and for all OCR'd pages, Batch −50 %), the operator
  runbook. Tests **+16** (401 total); ruff clean.

### C2 — GT factory at scale (2026-07-29) ✅

Built the C2 GT factory on top of the B2 aligner (`src/leibniz/align/*` extended).

- **The join** (`volumes.py`): a §70-expired volume's pieces *are* the katalog
  records citing it — `enumerate_pieces` walks `katalog_records.aa_refs` ×
  `legal.expired_volumes` × the A3 crosswalk, emitting a `PieceRef` per citation
  with the work id (best crosswalk link), folio range, and katalog text type.
- **Piece→canvas resolver** (`resolve.py`, Open Q #10 **solved**): the folio-range
  parser + `pages.label` (folio labels C1 now stores) turn a katalog `Bl.` range
  into exact canvases (`Bl. 164–165` → the recto/verso canvases). Pure/offline.
- **Banded aligner** (`dp.align_banded` + `align._align_spine`): O(len·band)
  Needleman–Wunsch with traceback for long multi-page pieces past the 30M-cell
  guard (B2's blocking gap). Tested **exact vs the full DP** (0 mismatches, wide
  band; exact at band 32 on 8%-noise near-parallel pairs) and length-difference-safe.
- **Stratum heuristic** (`stratum.py`, Open Q #11): fair_copy vs draft from the C1
  segmentation stats + katalog `textart` (Reinschrift/Konzept…); sets the mint
  threshold per piece (drafts held higher — precision over yield).
- **Factory** (`factory.py`): resolve → gather C1 HTR lines → align (banded) →
  stratum-threshold → mint `gt_lines` with provenance + license gate (§70 `open`;
  Transkriptionspool `nc`). Below-threshold discarded; idempotent re-mint; one
  `runs` row per batch. Edition text is **injected** (`edition_text_for`), so the
  whole orchestration is offline-testable; the production provider wires `pdftext`.
- **Extraction QA** (`volumes.assess_extraction`, Open Q #12): a two-pass /
  two-model agreement estimate flagging unstable extractions for a per-volume
  error rate. **Validated live** on real Leibniz print (Gerhardt II, 1875, PD,
  archive.org): `gpt-4o` extracted the reading text and dropped the running head /
  page number / signature; two-model QA flagged 1/2 pages (mean agreement 0.67) —
  the code-switched page where `gpt-4o-mini` dropped ~60% of the text. Evidence:
  `reports/gt-factory-extraction-qa.json`.
- CLI: `leibniz align {pieces, factory, gt-report}`. Deliverable
  `reports/gt-factory.md` (piece enumeration, yield vs the 63k/≥50k targets, by
  stratum, the live extraction validation, operator runbook). Tests **+33**; ruff
  clean; offline (kraken/keys not needed — the aligner + factory run without them).

### C1 — Corpus segmentation + HTR v1 (2026-07-29) ✅

Built the corpus batch pipeline `src/leibniz/pipeline/*` + extended the store.

- **State machine**: `pending → segmented → recognized` over `pages`, resumable
  (commit per page), idempotent (`--redo` clears + re-segments), `--sample`/`--set`
  scoping, per-page fault tolerance (skipped + reason, never fatal), one `runs`
  row per batch (model@version, params, git SHA, counts, wall time).
- **segment** (`segment.py`): PHILIUMM baseline segmenter → line geometry into
  `lines` (`status='machine'`, text empty) + a `page_stats` row.
- **recognize** (`recognize.py`): crops each stored line from geometry (no
  re-segmentation — `PageSegmenter.crop_lines`), PHILIUMM HTR → text + per-line
  confidence, repointing run/model at the recognition run (SPECS §4.5).
- **Segmentation stats** (`stats.py`): pure-geometry per-page metrics (line count,
  region coverage, line-height CV, overlap + short-line anomalies) — the layout
  signal the C2/C4 stratum heuristic reads. Fully offline-tested.
- **Store**: new `page_stats` table + `pages.label` (folio label, for the C2
  resolver) + `Line`/`PageStats` + status/line/stats helpers (`db.py`).
  `KrakenEngine.transcribe_conf` and `PageSegmenter.crop_lines` added.
- CLI: `leibniz pipeline {segment, recognize, status, report}` (status/report run
  without kraken; segment/recognize preflight-check the stack). The live 500-page
  run needs the kraken stack + image pull (absent here); built + offline-tested
  (+27 tests), operator runbook + GPU/cost estimates in `reports/htr-v1-sample.md`.

### B2 — Retro-alignment prototype (2026-07-29) ✅ Gate: GO — green-light C2

Built the retro-alignment engine (`src/leibniz/align/*` + `src/leibniz/layout/segment.py`)
and measured it end-to-end. **Aligner yield 98.8% at 97.5% precision on favorable
material under real HTR; false-mints 0 under omission ⇒ build the C2 GT factory.**

- **The engine** (`src/leibniz/align/`, pure + offline-tested):
  - `normalize.py` — the lossy *alignment* comparison alphabet (casefold, u≡v,
    i≡j, long-s, ligatures, a small Latin-brevigraph list, struck `xx` elision,
    punctuation) **with a folded→original offset map** so the minted GT is a slice
    of the *original* edition (accents/capitals intact), not the folded form.
  - `dp.py` — Needleman–Wunsch with full traceback + semi-global (free-end) option
    (the path `metrics.edit_distance` doesn't give). Documents the both-free
    degeneracy the aligner avoids.
  - `align.py` — the **boundary-projection** retro-aligner: HTR spine ↔ edition
    text → per-line projected slice + confidence; hyphenation-rejoin across line
    breaks; free edition overhang.
  - `evaluate.py` — the quantitative harness (real HTR on the val split; exact
    per-line grading; divergence + omission conditions; threshold sweep).
  - `pairs.py` — mint `gt_lines` with provenance + the **license-bucket gate**
    (`open` only for §70; `nc` never in CC BY) enforced at write time.
  - `pdftext.py` — §70 reading-text extraction (GPT-4o vision on scanned print,
    apparatus excluded per §7.2; text-layer fallback; skips without a key).
  - `prototype.py` — GWLB IIIF → segment → HTR → align orchestration (no rehosting).
  - `cli.py`, `report.py` — `leibniz align {eval,extract,run,report}`; the report.
  - `layout/segment.py` — PHILIUMM baseline segmentation (kraken-5→7 metadata shim).
- **Quantitative gate (real HTR on the PHILIUMM val split, `data/bench/` cached):**
  diplomatic 98.8%/97.5% (yield/precision) · divergence 3% 98.5%/96.7% · divergence
  6% 98.2%/97.2% · omits-15% 94.2%/95.5% · divergence 3%+omits-15% 84.2%/92.0%.
  **`false_pos = 0` in every condition** — the confidence signal never mints an
  edition-omitted line, so precision loss is lost yield, not polluted GT.
- **Live pipeline, run on real data this session:** GWLB IIIF `/full/full/0/default.jpg`
  (2008×2561 quarto) → PHILIUMM seg (**44 lines** on `00068642` c0, LH 4,6,18) → HTR
  (readable Latin) → GPT-4o extracts clean §70 AA VI,4 reading text (apparatus
  excluded). Katalog-verified pair: `00068642` c0 = **AA VI,4 N.109**.
- **Localization finding (for C2):** GWLB IIIF canvas labels *are* folio numbers
  (`164r`…), so the katalog `Bl.` range → exact canvases (Bl.164–169 → 322–333).
  This is the piece→canvas resolver C2 needs; the §70-volume OCR is too garbled to
  text-search, and scans are convolutes of 16–414 canvases.
- Tests **+43** (→ **274 passing**, 1 skipped); ruff clean. Kraken/torch/pyarrow
  used live but remain the optional `bench` extra (the align engine + its tests
  run without them; the 1 skip is the absent-stack path, now unexercisable).
  Deliverable `reports/alignment-prototype.md` (+ `alignment-eval.json`).

### B1 — Benchmark harness + PHILIUMM reproduction (2026-07-29) ✅ Gate: GO

Built `src/leibniz/htr/*` (deliverable D5) and reproduced the PHILIUMM CER on the
model's own val split. **Measured CER 7.95% (95% CI 7.49–8.46) vs claimed 8.33%,
Δ −0.38 → reproduced; build on the model.**

- **Artifacts (CC BY 4.0), fetched + documented:** HTR model (Zenodo
  `10.5281/zenodo.21457538`, `FoNDUE-GD_v2_ft_Leibniz.safetensors`, 16 MB, 178
  graphemes), val GT (HF `DenisaB/htr_leibniz_dataset_v1` val split, 1,878
  pre-extracted line/text pairs, 303 MB parquet), segmentation model DOI
  `21537859` (recorded; not needed to score pre-segmented lines).
- **Harness:** engine-agnostic; `Engine` protocol + `KrakenEngine` (local),
  `AnthropicEngine` and `OpenAIEngine` (Claude/GPT vision, skip without a key).
  CER/WER via unicode-aware Levenshtein under a **named, published normalization
  policy** (`philiumm` mirrors the model's training NFD + whitespace-collapse),
  micro-averaged, with seeded **bootstrap CIs**; per-line JSONL dumps; a **frozen
  protocol** `b1-2026-07`.
- **Frontier-VLM comparison (ran with a supplied OpenAI key):** 3-model panel on a
  seeded 150-line subsample — gpt-4o 45.87% / gpt-4.1 38.62% / gpt-4.1-mini 34.79%
  CER, all 4–6× the fine-tuned model's 8.19% on the same lines; total cost $0.49,
  token usage captured per response. The `--llm-model` flag is repeatable for a
  panel; each VLM row carries its input/output tokens + estimated $ in the report.
- **Key technical finding (a divergence worth remembering):** the model is a
  kraken-5-era **safetensors** container. kraken 7.0.3's `load_any` /
  `TorchVGSLModel.load_model` only parse CoreML and **fail** on it — load it via
  `kraken.models.loaders.load_models(..., tasks=['recognition'])`. And the val
  images are **already polygon-extracted, dewarped lines**, so inference must run
  the recognition net *directly* with `ImageInputTransforms(valid_norm=False)`
  (the baseline-model path); the box/`valid_norm=True` path mis-preprocesses and
  yields ~50% CER garbage. Both are documented in `engines.py` and the report.
- **Normalization matters, but not here:** philiumm 7.95% · lenient (fold
  case+diacritics) 7.61% · strict 7.95% — <0.4 pt spread, so the small gap to
  8.33% is *not* a normalization artifact (it is subset composition / their exact
  ketos-test harness; immaterial to the gate).
- **`--reuse-hyps`** re-scores/re-renders the report from a cached raw-hypothesis
  dump in ~6 s (no inference), so wording can iterate without a GPU/CPU pass.
- Tests: **+58** (229 total; 1 skipped = parquet needs `pyarrow`). ruff clean.
  Kraken/torch/pyarrow are an **optional `bench` extra**, imported lazily — the
  harness and its whole test suite run without them.
- Deliverable `reports/philiumm-repro.md` (measured vs claimed, discrepancy,
  sensitivity, error analysis, protocol, gate) + `reports/philiumm-repro.lines.jsonl`.

### A3 — Katalog crosswalk (2026-07-29) ✅

Built `src/leibniz/catalog/*` and ran a live sample against `leibniz-katalog.bbaw.de`.

- **Site structure (inspected live, documented in `scrape.py`):** server-rendered
  Laravel app, **no API**; GET `/de/global-search?q=…` and `/de/extended-search?…`
  (fields incl. `sign_ol`, `reihe`/`bd`/`nr` = AA series/vol/piece,
  `absender_oder_adressat`, `datum_ab/bis`, and **`id_hannover`**); results are one
  23-column HTML `<table>`; the **Signatur** cell links the scan as
  `…/resolve?id={object_id}` = our works PK. **5000-row result cap**, no pagination.
- **Normaliser** (`shelfmarks.py`): canonicalises LH/LBr/Marg/LK signatures —
  Roman↔Arabic (`LH XXXV,3,5` ≡ `LH 35,3,5`), spacing/punctuation, `Bl.` leaf
  capture, `S.` (Seite) + parenthetical drop, `Stück` kept (a distinct work).
  Tested against messy real strings.
- **Crosswalk**: GWLB link primary (conf 1.0), normalized-shelfmark secondary
  (0.7); method + conf per link; higher-confidence-wins upsert.
- **Deliverable** `reports/crosswalk.md`: coverage by set/method, unmatched
  samples with reasons, operator command for the full scrape. CC BY attribution
  recorded in `catalog.KATALOG_ATTRIBUTION`.
- Raw HTML cached under `data/katalog/` (gitignored). ruff clean; catalog tests green.

### A2 — Image cache (2026-07-29) ✅

Built `src/leibniz/images/*` + extended the `pages` schema/manifest.

- **Schema**: added `image_url,thumb_url,delivery,local_path,n_bytes,sha256,`
  `fetched_at` to `pages` with an idempotent `ALTER TABLE` migration (A1-era DBs
  upgrade in place, no data loss). `upsert_page` preserves the download manifest
  + status on re-derivation (COALESCE).
- **`images pages`**: parses the METS `fileSec`+physical structMap from the OAI
  cache → per-page `DEFAULT` JPEG URL + thumb + delivery mode, offline. Populated
  all 236,795 pages.
- **`images fetch`**: downloads to `data/images/{oid}/{seq:04d}.jpg`, records
  size/sha256/dims (dims read off the JPEG via a dependency-free SOF walk),
  cache-first resume, JPEG-EOI integrity retry, `--set`/`--work`/`--limit`/`--redo`.
- **`images verify`** (existence/size/`--deep` re-hash, gap count) + **`images
  stats`** (counts/bytes/MP-histogram → appended to `census.md`, idempotently).
- Ran the dev slice + `images stats`. Full corpus pull left as an operator command.

### A1 — OAI/IIIF harvest → inventory + corpus census (2026-07-29) ✅ Gate: GO

Built `src/leibniz/net.py` + `src/leibniz/harvest/*` and ran the harvest live.
2,225 works · 236,795 page images (within the 150–250k gate band). No §44b TDM
reservation. `reports/census.md` published. (Full detail retained in git history.)

### A0 — Repo scaffold (2026-07-28) ✅

Scaffold, `legal.py` (§70/§71 registry), `db.py` (7 tables). 27 tests green.

---

## Key numbers

| Metric | Value |
| --- | --- |
| Tests passing | **475** |
| **Phase D (2026-09-16)** | search index (FTS5/Meili) · API · IIIF v3 + annotations · viewer (EN/DE, axe-clean) · Parquet exports + cards |
| Reports on Zenodo | statement 22782813 · census 22782815 · PHILIUMM repro 22782817 · retro-aligned GT 22782819 |
| **C1 corpus run (2026-09-11)** | **COMPLETE: 236,210/236,795 pages recognised (99.75%) · 13,508,625 lines** |
| C1 corpus remainder | 569 skips (enumerated reasons) · 16 permanently unfetchable (GWLB redirect loops) |
| C1 corpus cache | 236,779 pages · **395.6 GB** (drive-D image store) |
| C1 final architecture | 4 sharded CPU seg workers (~515 pg/h) ∥ 1 GPU recogniser (~940 pg/h), WAL + keyset batches |
| **C1 pipeline** | `pending→segmented→recognized` state machine, resumable/idempotent; +27 tests |
| C1 segmentation stats | per-page line count / coverage / height-CV / overlaps / short-lines → `page_stats` |
| **C2 GT factory** | enumerate §70 pieces → resolve canvases → anchored align → stratum-threshold → mint; +33 tests |
| C2 folio resolver (Open Q #10) | katalog `Bl.` range × IIIF folio labels → exact canvases (**solved**) |
| C2 banded aligner | O(len·band) NW + traceback; **0 mismatches vs full DP** (exactness-tested) |
| **C2 anchored aligner (2026-09-15)** | k-gram chain → chunked band; crash shape **44 MB / 1.9 s** (was ~6 GB, OOM-killed); 300k-char treatise 112 MB / 46 s |
| **C2 mint (2026-09-16)** | **297,424 open-bucket GT lines** (fair 9,913 · light 96,175 · heavy 190,162 · scrap 1,174) from 6,383 pieces; 5.9× target; ~2 h on 6 workers |
| C2 hand audit | **preliminary**: 20/200 judged (fair copies only) — 12 correct · 5 wrong · 3 unreadable; all 5 "wrong" agree with the HTR reading at 0.82–0.98 (likely misjudged); gate **deferred** to C3's ablation |
| C2 edition texts | 10,029 records: median 2.5k chars · p90 15k · **186 over 100k** (VI,6 N. 2 = 754k) |
| C2 stratum thresholds | fair_copy 0.55 · light 0.62 · heavy 0.72 · scrap 0.80 (drafts held higher) |
| **C2 extraction QA (live, real Leibniz print)** | `gpt-4o` reading-text extract, head/page-no dropped; 2-model QA flagged **1/2**, agreement **0.67** |
| C2 target | ≥50k new open-bucket lines (vs PHILIUMM ~63k) — awaits corpus HTR + keyed extraction |
| **B2 aligner yield · precision (favorable, real HTR)** | **98.8% · 97.5%** → **GO** |
| B2 yield · precision by condition | div3% 98.5/96.7 · div6% 98.2/97.2 · omit15% 94.2/95.5 · div3%+omit15% 84.2/92.0 |
| **B2 false-mints of edition-omitted lines** | **0** (every omission condition) |
| B2 live pipeline | GWLB IIIF → seg **44 lines** → HTR → GPT-4o §70 extract (all run) |
| B2 verified §70 ↔ scan pair | `00068642` c0 = AA VI,4 N.109 (katalog) |
| **HTR CER (B1): measured vs claimed** | **7.95%** (CI 7.49–8.46) vs 8.33% → **GO** |
| HTR WER (B1) | 27.04% (CI 25.95–28.19) vs claimed 28.56% |
| Val lines · char-perfect | 1,878 · 464 (24.7%) |
| CER by policy (philiumm/lenient/strict) | 7.95% / 7.61% / 7.95% |
| **VLM vs HTR (150-line subsample) CER** | Kraken 8.19% · gpt-4o 45.87% · gpt-4.1 38.62% · gpt-4.1-mini 34.79% |
| VLM comparison API cost | **$0.49** (450 calls, usage-metered) |
| Unique works · page images | 2,225 · **236,795** |
| **`pages` rows populated** | **236,795** (static 159,162 · iiif 77,633) |
| Images cached (dev slice) | 80 · 126.3 MB · verify 80/80 OK |
| Mean page size · full-pull estimate | ~1.6 MB · **≈ 365 GB** |
| Katalog records scraped (sample) | 15,382 (12,384 GWLB-linked) |
| **Crosswalk: works matched** | **1,094 / 2,225 (49.2%)** from 6 queries |
| Crosswalk link→work resolution | 99.96% (5 unresolved of 12,389) |
| Katalog result cap (per query) | 5,000 rows (no pagination) |

Per-set crosswalk coverage (sample): Handschriften 401/756 (53.0%) ·
Briefwechsel 545/1,059 (51.5%) · Marginalien 146/396 (36.9%).

Legal registry (A0, unchanged): 42 entries; 32 free today.

---

## Open questions

19. **Sheet-sides registered twice (2026-09-23).** Static-JPEG works list one scan of an unfolded sheet under two folio labels; the corpus run read each twice. Run `leibniz images duplicates` over the thumbnails, publish the distinct-scan count, fold twins in the index build, and restate `pages`/`lines` on the About page.

0. **Strategy review 2026-09-16 → `NOTES.md`** (accuracy levers incl. the review-queue design and the LLM-as-detector pilot; the Calculemus rescope and the missing `leibniz pack` seam; the four Academy seams; loose ends). The C3 changes live in the amended C3 prompt.
1. ~~IIIF vs static delivery (A2).~~ **Resolved for A2:** cache the uniform METS
   `DEFAULT` JPEG for every page. **D2 still** must degrade to a plain image where
   no IIIF Image API exists (only the ~33% IIIF works get deep-zoom).
2. ~~`pages` population is partial.~~ **Resolved:** all 236,795 pages derived
   offline from the METS `fileSec` via `images pages`.
3. **Katalog full scrape — the §70 volumes are done; the rest is an operator
   job.** `catalog scrape --expired-volumes` sweeps every expired volume in ~10
   min (substring `bd` matching + year deepening, see the C2 log). The remaining
   ~45k non-§70 records still need signature-prefix slices (or the `id_hannover`
   enumeration) for A3's ≥80 % work coverage; a TELOTA dump would moot it.
4. **Shelfmark-secondary limits (A3).** The normaliser matches LH/LBr cleanly, but
   some Marginalien records carry page/prose signatures (`Leibn. Marg. 10, 1, S.
   154-166`; relocated `(jetzt LK-MOW …)` notes) that don't match a work key —
   because the *work's* shelfmark form differs (`ZEN Leibn. Marg. N` vs the
   record's part/page form) or the work isn't in the sample. Impact is small
   (shelfmark is 198 of 12,582 links); the GWLB link carries the crosswalk. Ties
   into the multi-volume Marginalien part-suffix issue below.
5. **Marginalien scope** (from A1). 396 annotated printed books, 103,887 pages
   (44% of pages). HTR target is the *marginal annotations*, not the printed body —
   a C1/C4 segmentation/stratum concern, flagged early.
6. _(A0)_ §71 editio-princeps assumption; re-edition term restarts — for the
   lawyer memo (SPECS §7.5).
7. **B1 residual gap (0.38 pt).** Our 7.95% is *below* the 8.33% claim but ~0.5 pt
   above what a matched ketos-test might report; ruled out normalization as the
   cause (sensitivity <0.4 pt). Likely subset composition / their exact eval
   harness. Immaterial to the gate; note it if we ever re-run their `ketos test`.
8. **No per-line language labels in the PHILIUMM GT** (features are `text`+`image`
   only). The 7.95% is a Latin+French number by construction; a real per-language
   split waits for the C4 language-ID pass. German/Kurrent remains unmeasured here.
9. ~~**LLM-on-Leibniz numbers pending a key.**~~ **Done** — a supplied OpenAI key
   ran the 3-model VLM panel (gpt-4o/4.1/4.1-mini): 35–46% CER, 4–6× the fine-tuned
   model. The `anthropic` adapter is equally ready for a Claude comparison. Finding
   worth following up: the *smallest* VLM scored best — the larger models modernise
   archaic spelling more (a prompt-engineering lever, not pursued in Tier 1).
10. ~~**(B2) Piece→canvas localization.**~~ **Resolved (C2):** `align/resolve.py`
    turns a katalog `Bl.` range into exact canvases via the IIIF folio labels C1
    now stores on `pages.label`. Offline-tested; the single biggest C2 gap, closed.
11. ~~**(B2) Draft strata need a higher threshold.**~~ **Addressed (C2):**
    `align/stratum.py` + `factory.STRATUM_THRESHOLDS` set the mint threshold per
    piece (fair 0.55 → heavy 0.72) from the C1 seg-stats + katalog `textart`. C4
    calibrates the thresholds against the GT audit.
12. ~~**(B2) Edition-text extraction QA at scale.**~~ **Addressed (C2), measured
    at scale (2026-09-11):** `volumes.assess_extraction` runs for free between the
    two independent OCR layers of the same volume (IA Tesseract vs GWLB ABBYY):
    5 volumes, mean agreement 81.6%, 54/200
    pieces flagged. The live vision QA (gpt-4o, 1/2 flagged, 0.67) stands as the
    two-model variant. Residual OCR error in the labels is the known cost of the
    free path; the priced vision upgrade is in `reports/gt-factory.md`.
13. ~~**(C2) Real GT minting awaits three operator inputs.**~~ **Resolved
    (2026-09-16):** the §70 katalog sweep + crosswalk ran here, the page
    anchors come from the print itself (every AA page's running head names
    the pieces starting on it, so `align/edition.py` derives piece → page
    ranges from the volume's own text layer — no TELOTA dump needed), and the
    mint ran on the operator's store: 297,424 lines (C2 log). What remains
    for the gate is precision, i.e. the hand audit (Q #18).
16. **(C2) Ten §70 volumes have no free digital copy** (I,1, I,2, I,4, I,5,
    I,13, II,1 (1926), III,2, VI,2, VII,1, VII,2 — 6,082 of the
    17,162 piece citations). HathiTrust holds the ≤1928 prints as
    US-public-domain (US-IP viewing), the Göttingen repository (bot-challenged
    here) and a TELOTA/Leibniz-Archiv ask cover the rest; Münster's II/VI,4
    Internetausgaben need written permission. Also for the lawyer memo: the GWLB
    repositorium PDFs are a **CC BY-NC channel** for §70-free text — the
    registry prefers the unencumbered archive.org scans and flags GWLB-only
    volumes (I,3, I,14, I,15).
14. ~~**(C1) Segmentation on Marginalien / drafts is unmeasured on real images.**~~
    **Measured (2026-09-11):** the corpus run put a `page_stats` row on every
    segmented page — line counts, region coverage, height-CV, overlap and
    short-line anomalies across all sets and strata (`reports/htr-v1-sample.md`
    carries the distributions). The observed failure modes (speck lines on scrap
    pages, sliver crops, ~120 MP foldouts) are guarded and enumerated rather
    than fatal; threshold re-tuning against these real distributions is now a
    C4 calibration task with data in hand.
15. ~~**(C1) Line-confidence source.**~~ **Resolved (2026-09-11):** real CTC
    posteriors populate at corpus scale — 13.5M recognised lines carry
    confidences (mean ≈0.77 on the validation slice; `conf > 1` count is 0
    corpus-wide after the `140d58d`/token-layout fixes). They are ready to gate
    search and the UI.

18. **(C2) Precision of the minted GT: audit preliminary, gate deferred.**
    Yield is 5.9× target, but B2's 97.5 % precision was measured on
    favourable material against PHILIUMM's diplomatic GT; the corpus mint has
    no reference. The operator judged 20/200 (fair copies): 12 correct, 5
    wrong, 3 unreadable — and all five "wrong" sit on lines whose HTR reading
    agrees with the minted text at 0.82–0.98, i.e. likely misjudged (C2
    close-out log). Open until someone who reads the hands finishes the sheet
    (`reports/gt-audit/`), or C3's ablation (PHILIUMM GT alone vs + C2 GT on
    the held-out set) settles the question empirically — the latter is now
    the plan. If a stratum then fails, the levers are its threshold
    (`STRATUM_THRESHOLDS`), the burst/overhang guards, and Q #17.
17. **(C2) Edge-of-passage scatter under unit costs.** With the HTR ends not
    free (the piece's lines must all be consumed) and the edition ends free,
    the DP is indifferent between matching the passage's last few characters
    in place and scattering them as chance single-character matches over
    uncovered manuscript further down (a tie; the leading side is even a local
    win for the scatter). The band now caps it at ≤ `band` (256) characters
    per end; the full DP scattered without bound. Effect: the last line(s)
    before a stretch of uncovered manuscript can be minted missing their
    final characters. Measure on the hand-audit sheet; candidate fixes are a
    tie-break that prefers deletions past the last anchor, or freeing the HTR
    ends *inside* the anchored band (no longer degenerate there).

---

## Divergences (recorded per the COMMON-CONTEXT rule)

- **2026-09-16 — page images served from the project's own mirror, not from
  the GWLB (operator decision).** SPECS §3.4 and §7.1 say the viewer loads
  images from the GWLB's IIIF endpoints and that nothing is rehosted. The
  public site (leibnizlegible.com) instead serves the A2 image cache — the
  GWLB's own delivery derivatives, Public Domain Mark 1.0, no related rights
  under §68 UrhG — from `images.leibnizlegible.com` (Cloudflare R2), plus
  thumbnails derived from them. Reasons, in the operator's words: uptime,
  control, engineering (the line polygons were computed on exactly these
  files, so the overlay sits on the pixels the HTR read), and the framing
  that a free open-access resource competes with no Leibniz project and
  serves the same goals every Leibniz scholar has. What does not change:
  every page links to its original at the GWLB; the page API, the
  annotations and the dataset exports keep naming the GWLB URI as the
  source image (§4.5 provenance); the attribution names the GWLB and the
  Public Domain Mark on every view; the GWLB is told before launch. The
  code keeps the direct-from-GWLB mode as its default —
  `LEIBNIZ_IMAGE_BASE_URL` unset — so the divergence is a configuration,
  not a fork (`web/images.py`). **Live since 2026-09-23**, after a 40-hour
  upload at a measured 2.8 MB/s; the site ran on the GWLB's endpoints in the
  meantime, which is why the switch cost no downtime.

- **Viewer without a bundler (D2):** SPECS §4.2 says "vanilla TS/Vite"; the
  viewer ships as plain ES modules + CSS with no build step (types via JSDoc,
  OpenSeadragon vendored), so the repo's CI stays Python-only and `leibniz
  serve` needs no Node toolchain. Same stack otherwise (OpenSeadragon on GWLB
  IIIF, FastAPI serving it).
- **D1 built before C4 (D):** SPECS §5 sequences D1 after C4; nothing in the
  index or viewer depends on v2 — lines are versioned per `run_id` and the
  API/index always show the latest run per line — so D shipped on v1 and C4
  swaps v2 in with a re-index. `lang`/`stratum` filters exist and read
  `unknown` until C4 fills them.
- **Releases not gated on the §7.5 memo / §8 letters (operator decision,
  2026-09-16):** recorded in `reports/release-checklist.md` §0.
- **Schema extension (C1):** added a `page_stats` table (per-page segmentation
  metrics) and a `pages.label` column (folio label) beyond the SPECS §4.3 canonical
  list. `page_stats` is queried by the C2/C4 stratum heuristic; `pages.label` is the
  key for the C2 piece→canvas resolver. Both are additive and migration-safe
  (`SCHEMA_SQL` `CREATE TABLE IF NOT EXISTS` + additive `ALTER TABLE` in `_migrate`).
- **`lines` provenance (C1):** the two-stage pipeline writes geometry with the
  *segmentation* run id, then recognition repoints `run_id`/`model` at the
  *recognition* run (the text's provenance, SPECS §4.5); the segmentation run is
  retained in `page_stats.run_id` and `lines.source`. The C4 append-per-run /
  version-rows decision (db.py docstring) is still deferred.
- **C1/C2 live runs deferred to an operator env.** This build environment has no
  kraken/torch stack, no GPU, and no image cache (bulk `data/` is gitignored and
  ephemeral), so the corpus segment/recognize was **not** run here. The 2026-09-11
  session *did* run the C2 data inputs here at full scale (OAI harvest, §70
  katalog sweep, crosswalk, volume ingestion + extraction) — all reproducible
  with the CLI, cache-first; only the mint needs the operator's corpus store.
- **Optional dependency `gt` (C2):** `pdfplumber` for PDF text layers
  (`uv sync --extra gt`); imported lazily, tests run without it.
- **`data/editions/` (C2):** raw §70 volume text layers + extracted piece JSON;
  gitignored like the rest of `data/`.

## Next

**Phase D is built on v1 and deployable (2026-09-16); the operator runs the
runbook.** `deploy/README.md`: `deploy/prepare-store.sh` on the desktop,
`install.sh` on a small VPS, `leibniz index build --backend meili` (one pass,
an hour or two), `leibniz index bench` against the 500 ms p95 criterion, the
courtesy note to the GWLB before launch, then `leibniz release export` + the
checklist for the dataset uploads.

**A0–A3 + B1–B2 + C1 (machinery *and* corpus run) + C2 (machinery *and* mint) all green; C2's precision gate is deferred to C3's ablation (audit preliminary).**
Per SPECS §5 sequencing, C is sequential: **C2 minting, then C3**, then C4 and
the D phases.

- **C2 — closed on the mint; the precision gate rides with C3.** 297,424
  lines minted; the hand audit is preliminary (20/200, Q #18) and stays
  open in `reports/gt-audit/` for a reader of the hands. The C3 ablation
  (PHILIUMM GT alone vs + C2 GT) is the empirical test of the minted GT; if
  it shows no gain, come back to Q #18 / Q #17 and the per-stratum
  thresholds before spending on labels. Optional clean-label upgrade:
  vision re-extraction of the minted pieces' pages (priced in the report;
  low three figures at most).
- **Phase C3 — Fine-tune v2 + per-stratum eval (gate).** Train `leibniz-htr-v2`
  from the PHILIUMM checkpoint on PHILIUMM GT + the C2 open-bucket GT
  (+ ablations). Hold out a page-disjoint test set stratified by stratum +
  language; evaluate with the B1 harness. Gate: **CER ≤7% on la/fr**.
- **Operator (SPECS §8), now higher-value than ever:** a **TELOTA katalog
  dump** would complete the scrape *and* supply the §70 anchors in one move —
  and with the corpus read, emailing PHILIUMM (Rabouin/Bumba) the B1/B2/C1
  results carries real weight: their models just machine-read the entire
  Nachlass. Report the 16 redirect-loop delivery URLs to GWLB while at it.

No code or data blockers for C2 minting; the only dependency is the corpus store's location.
