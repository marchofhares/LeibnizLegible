# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-07-29 (end of Phase B2)._

---

## Current state

**Phase B2 (retro-alignment prototype) — complete. Gate: ✅ GO — green-light C2.**
The retro-alignment engine (`src/leibniz/align/`, the C2/C3 GT-factory core) is
built and measured. On the one ground truth we have — the PHILIUMM val split
(real Leibniz line images + gold text) under **real HTR** — the aligner mints
**98.8% of lines at 97.5% precision** (diplomatic; 98%+/97% across divergence
conditions), clearing the ≥60% yield / ≥95% precision gate with wide margin. The
decisive precision result: across every *omission* condition the aligner minted
**zero** edition-omitted lines (`false_pos = 0`) — confidence withholds exactly
the lines with no edition counterpart, so a real edition dropping material costs
*yield, not polluted GT*. The whole pipeline was run **live on real data**: GWLB
IIIF → segment (PHILIUMM seg model, 44 lines on a real page) → HTR (readable
Latin) → §70-expired edition-text extraction (GPT-4o on real AA VI,4 print,
apparatus-separated) → align. **Verdict: build the C2 factory.** Full deliverable:
`reports/alignment-prototype.md`.

Key sub-findings (feed C2): (1) the biggest scaling obstacle is **localizing a
piece's canvases inside GWLB convolutes** (16–414 canvases; katalog links the
convolute, §70-volume OCR is too garbled to text-search) — but GWLB IIIF canvas
labels **are folio numbers** (`164r`…), so the katalog's `Bl.` range maps to exact
canvases (this is the resolver C2 must wire in); (2) **drafts** (heavy revision)
align worse than fair copies exactly as the omission conditions predict — hold
them to a higher threshold; (3) the normalizer folds orthographic
edition/diplomatic divergence away, so u/v, i/j, long-s, ligatures and struck-out
runs cost the alignment nothing.

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
| Tests passing | **274** (+1 skipped) |
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

1. ~~IIIF vs static delivery (A2).~~ **Resolved for A2:** cache the uniform METS
   `DEFAULT` JPEG for every page. **D2 still** must degrade to a plain image where
   no IIIF Image API exists (only the ~33% IIIF works get deep-zoom).
2. ~~`pages` population is partial.~~ **Resolved:** all 236,795 pages derived
   offline from the METS `fileSec` via `images pages`.
3. **Katalog full scrape is an operator job.** The 5000-row cap means enumeration
   must partition into sub-cap slices (by AA volume / signature prefix, deepened
   on a cap warning). The `id_hannover` field could enumerate the *digitized*
   subset directly — worth trying at scale. A TELOTA dump (SPECS §8) would moot it.
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
10. **(B2) Piece→canvas localization is C2's first build.** The aligner works; the
    integration gap is finding *which canvases* transcribe an edition piece. GWLB
    scans are convolutes (16–414 canvases), the katalog links the convolute (with a
    `Bl.` folio range), and older §70-volume OCR is too garbled to text-search. The
    solve is demonstrated: **IIIF canvas labels are folio numbers** (`164r`…), so
    `Bl.` range → canvas indices directly. C2 wires this + a folio-range parser.
11. **(B2) Draft strata need a higher threshold.** Fair copies clear the gate; drafts
    (heavy revision — edition drops deletions, resolves corrections, inlines marginal
    insertions) lose yield exactly as the omission conditions predict. The C4 stratum
    heuristic should set the mint threshold per piece (precision held, yield traded).
12. **(B2) Edition-text extraction QA at scale.** GPT-4o reads clean §70 *print*
    reliably (apparatus excluded), but C2 needs a per-page reading-text/apparatus
    error estimate (spot-check sample) and should prefer volumes with a real text
    layer where they exist. No API key ⇒ this step skips gracefully.

---

## Next

**A0–A3 + B1 + B2 all green.** Per SPECS §5 sequencing (C sequential; D after C4).
B2's GO unblocks C2; C1 was already unblocked by A2 + B1.

- **Phase C1 — Corpus segmentation + HTR v1 (batch).** Independent of B2. Needs the
  full image pull (operator command, ~365 GB) + the reproduced model. Reuse
  `layout/segment.py` (built in B2, kraken-5→7 shim) and `htr/engines.KrakenEngine`;
  record per-page segmentation stats for the C4 stratum heuristic. B1 harness = the
  eval backbone.
- **Phase C2 — GT factory at scale.** Now green-lit. Scale `src/leibniz/align/`
  across the §70-expired volumes (`legal.py` → 32 free). **Build first:** the
  piece→canvas resolver (IIIF folio labels + katalog `Bl.` ranges — Open Q #10),
  volume reading-text extraction with QA (#12), and stratum-aware thresholds (#11).
  Emit `gt_lines` (`license_bucket='open'`; Transkriptionspool → `nc`). Target ≥50k
  new open-bucket lines; the aligner is ready (98.8%/97.5% on favorable material).
- **Operator (SPECS §8):** email PHILIUMM (Rabouin/Bumba) the B1 reproduction +
  the B2 result (their seg + HTR models drive a working alignment pipeline). Request
  a TELOTA katalog dump — it would give piece↔scan page anchors and moot most of the
  C2 localization build.

No blockers for C1 or C2.
