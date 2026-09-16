# Leibniz Legible — Build Prompts

_Companion to `SPECS.md`. v0.1, 2026-07-28._

## How to use this file

Each phase below is a **standalone prompt for a fresh Claude coding session**. The sessions share no memory; the repository is the memory. The protocol:

1. Start a fresh session in the repo. Paste the **COMMON CONTEXT** block, then the one phase prompt you're running.
2. The session must begin by reading `SPECS.md` and `STATUS.md`, and end by updating `STATUS.md` and committing. If reality in the repo contradicts a prompt (files missing, schema drifted), trust the repo + `STATUS.md`, note the divergence in `STATUS.md`, and adapt.
3. Run one phase per session. Phases marked as **gates** end with a go/no-go recommendation written into `STATUS.md` — read it before launching the next phase.
4. Dependencies are listed per phase; A1→A2→A3 and B1→B2 can interleave, C phases are sequential, D phases follow C4.

---

## COMMON CONTEXT (paste at the top of every session)

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

---

## Phase A0 — Repo scaffold

_Depends on: nothing (empty repo containing SPECS.md + PROMPTS.md)._

> Scaffold the project. Create: `pyproject.toml` (uv-managed, Python 3.12; deps: typer, httpx, lxml, rich; dev: ruff, pytest) with the `leibniz` CLI entry point; the `src/leibniz/` package skeleton per COMMON CONTEXT with empty-but-importable modules; `tests/` with one smoke test that the CLI runs (`leibniz --version`); `.gitignore` (data/, .env, caches); `.env.example`; `data/` with a `.gitkeep` and README explaining it's never committed.
>
> Create `src/leibniz/legal.py`: the §70/§71-expired volume registry from SPECS §1.4 as structured data — each AA volume with series, volume number, first-publication year, and a `free_from` year computed as publication_year + 26 (calendar-year rule); a function `expired_volumes(today)` returning what's usable; unit tests including the boundary cases (I,17 free from 2027-01-01; VII,8 not until 2050).
>
> Create `src/leibniz/db.py`: SQLite schema DDL for the tables in SPECS §4.3 (works, pages, lines, katalog_records, crosswalk, gt_lines, runs), idempotent `init_db()`, and typed insert/query helpers for works and pages. Tests against a temp DB.
>
> Create `STATUS.md` with sections: Current state / Phase log / Key numbers / Open questions / Next. Fill in A0's entry.

---

## Phase A1 — Harvest: OAI + IIIF → inventory + corpus census **(gate)**

_Depends on: A0._

> Build the harvest stage. Endpoint facts (verify live before coding against them; record any drift in STATUS.md): OAI-PMH at `https://digitale-sammlungen.gwlb.de/oai2/` serving METS/MODS; sets `LeibnizHandschriften` (~756 records), `LeibnizBriefwechsel` (~1,060), `LeibnizMarginalien` (~396), `Leibnitiana` (~1,823), `leibniz-rekonstruktionen`. IIIF Presentation 2.0 manifests at `https://digitale-sammlungen.gwlb.de/content/{id}/manifest.json` (sample known-good id: 00068642); canvases carry an IIIF Image API 2 service.
>
> First, record the crawl posture: fetch and commit `robots.txt` and response headers for both hosts into `reports/crawl-posture.md`; check for any machine-readable TDM reservation (§44b UrhG) and say plainly whether one exists. If one exists, stop and flag in STATUS.md.
>
> Then implement `leibniz harvest oai` (ListRecords with resumptionToken paging, per-set, raw XML cached under data/oai/, parsed into `works`: object id, set, title, shelfmark(s) from MODS, manifest URL) and `leibniz harvest manifests` (fetch+cache each work's manifest, populate `pages` with canvas seq/id/image-service URL/dimensions). Both resumable and cache-first; polite per COMMON CONTEXT. Parse defensively — Kitodo METS/MODS has quirks; keep raw XML so parsing can be re-run offline. Tests use fixture XML/manifests, no network.
>
> Deliverable beyond code: **`reports/census.md` — the first real page count.** Works and pages per set; distribution of pages-per-work; shelfmark coverage (how many works have parseable LH/LBr signatures); anomalies (zero-canvas works, duplicate signatures). This census number ("how many page images actually exist") does not exist publicly anywhere — write the report as a publishable artifact.
>
> **Gate**: STATUS.md states the total page count and whether it's in the expected ~150–250k band. Wildly off ⇒ investigate before A2.

---

## Phase A2 — Image cache

_Depends on: A1._

> Implement `leibniz images fetch`: download the delivery derivative for every page via the IIIF Image API (`{service}/full/full/0/default.jpg`) into `data/images/{object_id}/{canvas_seq}.jpg`, with: resumability (skip existing, verify by size/checksum), a manifest of downloaded files with checksums in SQLite (extend `pages`), politeness (COMMON CONTEXT; make concurrency configurable but default conservative), integrity retry for truncated images, and a `--set`/`--work` filter so small slices can be pulled for development. Add `leibniz images verify` (re-checksum, report gaps) and `leibniz images stats` (count, bytes, dimensions histogram → append to reports/census.md).
>
> Do NOT start a full-corpus pull in this session. Pull one small set slice (e.g. one Handschriften work + one Briefwechsel work, ~50–200 images) as the dev corpus, record it in STATUS.md, and leave the full pull as a documented operator command with a time/disk estimate (expect ~200–400 GB total).

---

## Phase A3 — Katalog crosswalk

_Depends on: A1._

> Goal: join the BBAW Ritter-Katalog (https://leibniz-katalog.bbaw.de/, >70,200 records, CC BY 4.0, no public API) to our works/pages, so every scan links to its scholarly record and (where catalogued) its AA volume/piece.
>
> Check STATUS.md first: if a TELOTA data dump has arrived (operator action, SPECS §8), ingest that. Otherwise build a polite scraper: enumerate records via the site's search/browse (server-rendered app — inspect its URL structure first and document it in the module docstring), cache raw HTML under data/katalog/, parse into `katalog_records` (record id, shelfmark refs, dating, incipit, correspondent, AA volume/piece refs, links to GWLB scans if present, transcription snippet if present). Attribution: CC BY — record the required attribution string in the module and in future exports.
>
> Then build the crosswalk: match records to `works` primarily via the katalog's own outbound GWLB links, secondarily via normalized shelfmark strings (write a robust LH/LBr signature normalizer — formats vary: "LH XXXV, 3, 5", "LBr. 57,1", "LK-MOW …"; test it against messy real examples from fixtures). Store method + confidence per match.
>
> Deliverable: `reports/crosswalk.md` — match-rate by set and method, unmatched samples with reasons. Target ≥80% of works matched; report honestly whatever results.

---

## Phase B1 — Benchmark harness + PHILIUMM reproduction **(gate)**

_Depends on: A0 (independent of A1–A3)._

> Build `src/leibniz/htr/bench.py` + `leibniz bench` — an engine-agnostic evaluation harness — and use it to reproduce PHILIUMM's numbers before we build anything on them.
>
> Artifacts (all CC BY; cache under data/models/ and data/gt/): HTR model Zenodo DOI 10.5281/zenodo.21457538 (Kraken-stack, self-reported CER 8.33%); GT dataset HuggingFace `DenisaB/htr_leibniz_dataset_v1` (~63k lines; splits train_clean/train_noisy/val); segmentation model Zenodo 10.5281/zenodo.21537859. Download, inspect formats, and document exactly what they contain in reports/philiumm-repro.md (the val split is ~1,878 lines).
>
> Harness requirements: input = (line image, reference text) pairs; engines are pluggable adapters — implement `kraken` (local inference) and `anthropic` (Claude vision via API, zero-shot line transcription; skip gracefully without a key); metrics = CER/WER (character-level edit distance, unicode-normalized; document the normalization policy — it changes results) with bootstrap confidence intervals; per-line output dumps for error analysis. Frozen protocol documented so numbers are comparable across runs.
>
> Run: PHILIUMM model on the PHILIUMM val split. Optionally (if key present): Claude on a 100–200 line random subsample for the first published LLM-on-Leibniz numbers.
>
> Deliverable: `reports/philiumm-repro.md` — measured CER vs the claimed 8.33%, discrepancy analysis, per-language breakdown if labels allow, LLM comparison if run.
>
> **Gate**: STATUS.md verdict — "reproduced within ~1 CER point: build on it" or "not reproduced: reassess (retrain from their GT before proceeding to C phases)."

---

## Phase B2 — Retro-alignment prototype **(gate)**

_Depends on: A2 (dev image slice), B1 (working model)._

> The core bet of the GT strategy: edition reading text from §70-expired AA volumes can be aligned to manuscript line images to mint training data (the Bullinger project minted 165k lines this way). Prototype it on ~10 pages before scaling.
>
> Pick a favorable target: one §70-expired Reihe I volume (check `legal.py`; the PDFs are free via leibnizedition.de / rep.adw-goe.de) and one letter whose scan is in the dev slice with a confident crosswalk match (fair-copy correspondence = the easy stratum; that's intentional for the go/no-go).
>
> Steps: (1) extract the reading text for that piece from the volume PDF — older volumes are scanned print, so this may need OCR or vision-LLM extraction; keep reading text rigorously separated from apparatus/footnotes (smaller type, stair-step layout) and NEVER extract introductions/commentary (SPECS §7.2); (2) segment the manuscript pages (PHILIUMM segmentation model); (3) run HTR (PHILIUMM model) to get machine text per line; (4) align edition text to lines via character-level alignment of machine text ↔ edition text (Needleman-Wunsch or CTC-style DP; normalize both sides: lowercase, strip diacritics, expand a small rule list of common Latin abbreviations; tolerate hyphenation across lines); (5) emit aligned (line image, edition text) pairs with per-line alignment scores; (6) hand-inspect every pair and record precision.
>
> Deliverable: `reports/alignment-prototype.md` — per-line yield (% of lines aligned above threshold), inspected precision, failure taxonomy (normalization gaps, layout, apparatus bleed-through), and honest notes on what scaling needs.
>
> **Gate**: STATUS.md verdict. Yield ≥60% at ≥95% precision on this favorable material ⇒ green-light C2. Below ⇒ iterate here or descope C2 to Transkriptionspool-style diplomatic sources (NC bucket, training-only).

---

## Phase C1 — Corpus segmentation + HTR v1

_Depends on: A2, B1 (and the full image pull having been run by the operator)._

> Build the corpus-scale batch pipeline: `leibniz pipeline segment` and `leibniz pipeline recognize`. Requirements: processes pages by status (pending → segmented → recognized), resumable and idempotent (re-running skips done work; a `--redo` flag re-processes), records every batch in `runs` (model@version, params, git SHA, counts, wall time), stores line polygons/baselines + text + per-line confidence with `status='machine'`, tolerates and logs per-page failures without dying, GPU-aware batching with a CPU fallback, and a `--sample N` mode.
>
> Segmentation quality is the known risk (layered revisions, marginalia, snippets): compute per-page segmentation stats (line count, region coverage, overlap anomalies) and store them — they feed the stratum heuristic in C4.
>
> In this session: run the full pipeline on a ~500-page sample spanning all sets, inspect, fix the worst failure modes, write `reports/htr-v1-sample.md` (throughput, confidence distributions, qualitative failures per set). Leave the corpus run as a documented operator command with GPU-hour and cost estimates.

---

## Phase C2 — GT factory at scale

_Depends on: B2 green, A3._

> Scale the B2 prototype across all §70-expired volumes (`legal.py` list; ~34 volumes ≈ 25–30k printed pages). Components: (1) volume ingestion — download/cache expired-volume PDFs, extract reading text per piece with page anchors, using the B2 extraction approach hardened with spot-check QA (sample pages verified via vision-LLM or manual; track an extraction-error estimate); (2) piece↔scan resolution via the A3 crosswalk (AA volume/piece refs in katalog records); (3) the B2 aligner, hardened: hyphenation, multi-page pieces, marginal insertions, pieces spanning scan boundaries; (4) emission into `gt_lines` with stratum labels (start heuristic: correspondence fair copies vs drafts via segmentation stats + katalog type), alignment confidence, and `license_bucket='open'`; Transkriptionspool-derived pairs (if used) go to `license_bucket='nc'`.
>
> Discard below-threshold alignments — a smaller clean corpus beats a larger polluted one.
>
> Deliverable: `reports/gt-factory.md` — aligned-line counts by volume/series/stratum, estimated precision by stratum (sample-audit ~200 lines stratified by hand), comparison to PHILIUMM's 63k baseline. Target: ≥50k new open-bucket aligned lines; report honestly whatever results.

---

## Phase C3 — Fine-tune v2 + per-stratum eval **(gate)**

_Depends on: C2._

> Train `leibniz-htr-v2`. Training set: PHILIUMM GT (CC BY) + C2 open-bucket GT (+ NC-bucket as train-only if it measurably helps — document; NC data may train a CC BY-released model per the TDM analysis in SPECS §7, but note the question in the model card for the lawyer memo). Consider pooling external multilingual GT (Bullinger 165k lines ~80% Latin — github.com/pstroe/bullinger-htr; German Kurrent sets from HTR-United/CATMuS for the de stratum) — the Bullinger lesson says multilingual pooling helps; ablate if time allows.
>
> Use Kraken's training (ketos) fine-tuning from the PHILIUMM checkpoint; hold out a test set that is (a) disjoint from all training GT at the *page* level, (b) stratified by stratum and language. Evaluate with the B1 harness: overall + per-stratum + per-language CER/WER, compared against PHILIUMM baseline on the identical set.
>
> Deliverables: model artifact + `reports/htr-v2-eval.md` + a model card draft (data statement incl. licenses, metrics per stratum/language, intended use, the "machine output, not an edition" framing).
>
> **Gate**: CER ≤7% on la/fr ⇒ target met. Either way, ship the best model and record honest numbers; if v2 beats v1 nowhere, investigate before C4 re-runs the corpus.

> **Amendment (2026-09-16, strategy review — read before running C3).** The published analogue runs against the optimistic case: Bullinger went from ~110k to ~377k alignment-minted lines and CER did not move (9.13% → 9.1–9.2%), because the label floor, not model capacity, binds — their refined GT itself measures 6.5% CER. Our minted labels are Akademie-Ausgabe *reading text* (abbreviations silently expanded, u/v and i/j normalized, struck passages omitted) scored against a *diplomatic* validation set, so every expansion is a systematic insertion error that does not average out with scale; and the mint keeps only lines v1 already read at ≥0.55–0.80 folded similarity, so the GT is biased toward what v1 already gets right. Expect about one point (7.95% → ~7%), not two or three. Four changes that move the odds, all cheap:
> 1. **Re-extract the minted pieces' pages with a vision model before training** (`leibniz align extract`; priced in `reports/gt-factory.md` at two to low three figures). Removes OCR-layer noise (Tesseract/ABBYY, 81.6% cross-source agreement) and editorial brackets (`droit[e]` leaked into a minted line). Does not remove normalization.
> 2. **Stage the training**: minted (aligned) lines first, PHILIUMM's hand-corrected lines *last* and upweighted (their own stage1_noisy / stage2_clean configs already have this shape). Select checkpoints on a diplomatic set that is page-disjoint from training; verify the val files are disjoint from `train_clean`'s files (val was drawn from the clean subset). The NC-licensed Transkriptionspool is usable as an evaluation-only second set under the TDM rules (§7.3) — different source, different conventions, never redistributed.
> 3. **Filter minted lines by v1 CTC confidence as well as alignment similarity** (Peer et al. 2025's γ-filter; optimum 30–60%), and **report error composition**: deletions/insertions clustered at abbreviation sites are the normalization tax, and one CER number hides it. Ablate: PHILIUMM GT alone · + minted · + minted filtered · + minted re-extracted.
> 4. **Add character n-gram language-model decoding** (Tarride et al. 2024: −12% relative CER across 12 datasets in PyLaia). Kraken does not ship one as far as verified; implement over the CTC logits (torchaudio `ctc_decoder` + KenLM). Train the LM on *diplomatic* GT, never on edition text, or it will push toward expansions. Report with and without.
>
> Two honesty notes for the model card: (a) the ablation is a weaker test of GT precision than STATUS assumed — a flat result is consistent with Bullinger even at good precision, so the hand audit (Q #18) still matters; (b) the PHILIUMM transcription conventions are on an access-controlled wiki, so any published claim of "diplomatic" fidelity must state what was verified. Also measure, once v2 exists, the number nobody has: on the val split, the fraction of v1/v2 *disagreements* where either reading is exactly right, per stratum — it decides whether Calculemus's A/B mechanic has the truth in the pair.

---

## Phase C4 — Corpus re-run v2 + enrichment

_Depends on: C1, C3._

> Re-run recognition corpus-wide with v2 (same pipeline, new run_id; keep v1 rows — lines table is append-per-run with a current-run pointer, or version rows; pick and document). Add the enrichment stage `leibniz pipeline enrich`: per-line language ID (a fast classifier — lingua/fasttext class — with a `mixed` label for code-switched lines; Latin/French/German are the classes that matter) and per-page stratum labels (heuristic from segmentation stats + katalog type + GT-audit calibration; label the field `stratum_heuristic` — honesty in naming).
>
> Deliverable: `reports/corpus-v2.md` — coverage (% pages recognized, skip reasons), confidence and language distributions corpus-wide, stratum distribution. This report contains numbers nobody has ever computed (e.g. the actual machine-estimated language split of the Nachlass vs the folklore 40/30/15) — write it accordingly.

---

## Phase D1 — Search index + API

_Depends on: C4._

> Stand up search: Meilisearch via docker-compose (dev fallback: SQLite FTS5 behind the same interface). Index documents = one per page (concatenated line text, object/canvas ids, shelfmark, katalog refs, language mix, stratum, mean confidence) plus a piece-level rollup where the crosswalk allows. Typo tolerance on (that's the point — CER-noisy text needs fuzzy match); synonyms file for common early-modern spelling variants (u/v, i/j, ſ/s) if Meilisearch's normalization doesn't already cover them — test and document.
>
> Build the FastAPI service (`src/leibniz/web/api.py`): `/search` (query → page hits with highlighted snippets, filters: set, language, date range via katalog, stratum, min confidence), `/works/{id}`, `/pages/{id}` (lines with coords, text, confidence, status, provenance), `/manifests/{id}` (stub for D2). `leibniz index build` + `leibniz serve`. Tests against a small fixture index.

---

## Phase D2 — Viewer web app + IIIF v3/annotations

_Depends on: D1._

> Build the public frontend (vanilla TS + Vite, served by the FastAPI app): (1) search page — query box, filters, results grouped by piece/work with snippets; (2) page view — OpenSeadragon loading tiles **directly from GWLB's IIIF Image API** (we never rehost or proxy images), line-polygon overlay toggle, per-line text panel with status badge and confidence shading, click-line-to-highlight both ways; (3) work view — canvas strip, shelfmark, katalog record link (with CC BY attribution to BBAW/TELOTA), AA volume/piece link where known, PDM/source attribution to GWLB on every page; (4) an honest "About" page: what this is (machine transcription, Vorausedition-grade, subordinate to the Akademie-Ausgabe), what the error rates are per stratum (from C3/C4 reports), how to report errors.
>
> Also implement `/manifests/{id}`: IIIF Presentation 3 manifests wrapping GWLB image services with W3C annotation pages carrying our per-line transcriptions (motivation `supplementing`, provenance fields in each annotation) — the interop deliverable D7, so Mirador/other IIIF apps can consume our layer.
>
> Accessibility matters (alt text, keyboard nav, contrast). No analytics beyond server logs. German + English UI strings (simple i18n dict, no framework).

---

## Phase D3 — Releases + reports

_Depends on: C4, D2._

> Package and release: (1) `leibniz release export` → Parquet exports per SPECS §2: D1 inventory (CC0), D2 transcriptions (CC BY, provenance columns mandatory, NC bucket excluded), D3 gt (CC BY, open bucket only, stratum + align_conf columns), with dataset cards (README per dataset: schema, provenance, license, attribution strings for GWLB/BBAW, known error rates, the anti-contamination note "machine output — do not ingest as verified text"); (2) model release bundle for v2 (weights + finalized model card); (3) a release checklist doc that BLOCKS on the lawyer memo (SPECS §7.5) — generate everything, stage it, and mark the upload steps as operator actions gated on legal sign-off; (4) `reports/tier1-final.md` — the summary against SPECS §3 success criteria, stated plainly, criterion by criterion.
>
> Do not upload to Zenodo/HF in this session; produce the artifacts and the exact upload runbook (metadata, DOI reservation steps, license fields).

---

## Phase E1 (stretch) — Correction micro-UI

_Depends on: D2._

> Smallest useful human-in-the-loop: on the page view, an "improve this line" affordance → auth via a simple invite-token allowlist (no accounts system) → submitted corrections stored as new line versions with `status='corrected'`, corrector identity, and timestamp; original machine rows immutable; a `/corrections` review queue where the operator promotes to `status='verified'`. Export corrections as a supplementary GT dataset. Rate-limited, spam-safe, and entirely optional to the Tier 1 definition of done — do not let this phase grow into a platform.
