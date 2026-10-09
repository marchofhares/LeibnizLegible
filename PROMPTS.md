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
>
> **Amendment 2 (2026-10-07, from the audit — see STATUS.md "C2b").** The PHILIUMM team judged the 200-line sheet (199 verdicts); the patterns behind the non-*correct* verdicts and their reach across the mint are in `reports/gt-audit.md` and `reports/gt-audit/reach.md`. Six consequences for C3:
> 1. **Train on the re-minted lines with hyphens kept** (`align_piece(keep_hyphen=True)`, the default since C2b): the missing line-end hyphen was the most frequent fault of the minted text. The re-mint runs once, before C3, with every C2b flag in place (the factory is idempotent; about two hours on six shards).
> 2. **Exclude lines flagged `math`** (`data/gt/flags.jsonl` from `leibniz align audit-reach`) **and lines from Marginalien works**: formula lines are wrong in the mint and in the HTR alike, and the Marginalien body is print, not Leibniz.
> 3. **Exclude PHILIUMM's 1,010 pages from the held-out set** (`reports/philiumm/heldout_pages.csv`, once P1 has produced it): the model this project runs trained on them.
> 4. **Stratify the held-out set by stratum, language and hand** (`eigh.` in the record's Textart, the `eigh` flag of the reach census).
> 5. **Keep the 199 PHILIUMM-judged lines and their corrections out of training** (`reports/gt-audit/gt-audit-verdicts-philiumm.csv`, `…-corrections.csv`) and use them as a sanity set: a model that gets them wrong where the auditors read them is not better.
> 6. **Report CER by hand** as well as by stratum and language.

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

---

## Follow-up phases (2026-10)

_Phases outside the A0–E1 build order, each run from one prompt in one session. The prompts are appended verbatim, as they were given, except that a correspondent's name is withheld (square brackets mark the place); `STATUS.md` records what each session found and where it departed from its prompt._

### Phase W3 — A browse page (run 2026-10-06)

~~~~text
Phase W3 — A browse page: the Nachlass by shelfmark family, section and convolute.
One local session on the operator's Windows desktop: pre-flight, build, hand-over,
deploy, verify.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md. If this prompt conflicts with the repo, the repo + STATUS.md
win; record the divergence in STATUS.md. This phase is W3: STATUS.md already holds
W1 (overlay toggle, text export) and W2 (quoted phrases and exclusions in search),
both of 2026-10-02. Do not reuse either label.

## Where you run, and the rules that follow from it
You run in Claude Code on the operator's Windows desktop, started from PowerShell,
inside the repository checkout. Your shell tool may be PowerShell or Git Bash:
check which (`$PSVersionTable` works only in PowerShell; `echo $0` only in bash)
and write commands for the shell you actually have. In Windows PowerShell 5.1
`&&` does not chain commands (use `;` or separate calls), environment variables
are set with `$env:NAME = "value"`, and there are no heredocs: write any script
to a file under scratchpad/ (gitignored) and run it from there.
This machine holds the project's data. data/inventory.sqlite is the MASTER store
(13.5M v1 lines, 297k gt_lines, the product of two months of compute) and
data/images is the 396 GB page cache. Rules:
- Open the store read-only only: through `uv run leibniz …` commands (they open
  mode=ro) or through Python's sqlite3 with a `file:…?mode=ro` URI. Never run a
  write, a VACUUM, or a move against it. Never delete anything under data/.
- Ask the operator, before running anything: (a) is this checkout the one the
  C1/C2 runs used, and did those runs happen inside WSL2 (STATUS says the box is
  a 16-core WSL2 machine with a GTX 1660 Ti); (b) the path of data/inventory.sqlite
  as seen from this shell. Wait for the answers.
- Keep the existing Python environment intact. If `.venv` exists and holds
  `bin/python` but no `Scripts\python.exe`, it is the Linux environment the
  pipeline runs in; do not let Windows uv touch it. Before any `uv` command set
  `$env:UV_PROJECT_ENVIRONMENT = ".venv-win"` (bash: `export
  UV_PROJECT_ENVIRONMENT=.venv-win`) and add the line `.venv-win/` to .gitignore
  (commit it with the rest; note it in STATUS). If `uv --version` fails, ask the
  operator before installing anything (`winget install astral-sh.uv`).
- Line endings: the repo has no .gitattributes. Check `git config --get
  core.autocrlf`. Write new text files with LF endings; before each commit read
  `git diff --stat` and treat a file where every line changed as a line-ending
  accident: revert it and redo the edit.
- The operator merges. You push the branch and hand over; you never merge and
  never close the PR. You may create the PR with `gh` only on the operator's yes.
- The VPS: you run nothing there without the operator's explicit yes in chat for
  the exact command shown, and nothing other than the §9 "Update the app" block
  from deploy/README.md.
- Email: you draft; the operator sends.

## Task 0 — Pre-flight (report, then wait for a go)
1. `git status --porcelain` must be empty and `git rev-parse --abbrev-ref HEAD`
   should be main; otherwise stop and ask. `git fetch origin` and `git pull
   --ff-only origin main`. Confirm `git remote -v` points at
   github.com/marchofhares/leibnizlegible and that `git config user.name` and
   `user.email` are set.
2. Environment: `uv --version`; `node --version` (needed only for the Playwright
   check in Task 3; if absent, ask the operator whether to install it with
   `winget install OpenJS.NodeJS.LTS` or to do the browser check by hand);
   `gh --version` and `gh auth status` (optional, for creating the PR); `ssh -V`
   (for the deploy in Task 5).
3. Baseline on this machine, with UV_PROJECT_ENVIRONMENT set as above: `uv sync
   --extra web --extra gt --extra release`, `uv run ruff check .`, `uv run ruff
   format --check .`, `uv run pytest -q`. Record the counts. Failures that are
   Windows-only (file locking on temp SQLite files, path separators, a missing
   SQLite FTS5 module) are pre-existing and not yours: list them in STATUS.md
   under "Suite on Windows" and, if WSL is available, run the suite there too
   (`wsl -e bash -lc "cd <path> && uv run pytest -q"`) for the clean bill. Never
   change unrelated tests or code to make them pass on Windows.
4. Live-site state. STATUS.md's "Next" still lists the §9 deploy of W1 and W2 as
   an operator step; find out whether it ran:
   - GET https://leibnizlegible.com/api/pages/00068221:0043/text → 200 and a body
     starting with "# " (W1 text export);
   - GET https://leibnizlegible.com/search → the HTML contains the phrase
     "for an exact phrase" (the W2 hint);
   - GET https://leibnizlegible.com/static/style.css → contains
     ".line-overlay.is-hidden" followed by "visibility: hidden" (the W1 overlay fix).
   Use Invoke-WebRequest -UseBasicParsing or curl. Record pass/fail for each; a
   failure means the VPS is behind main, which the deploy in Task 5 fixes (it
   pulls main), so re-check all three after that deploy.
5. Print a short plan and wait for the operator's "go".

## Context
Leibniz Legible (https://leibnizlegible.com) is live. The web layer is
src/leibniz/web/: api.py (FastAPI, create_app; JSON API; the viewer shell served
for INDEX_ROUTES, each with a server-rendered fallback for crawlers via
_stamp_shell and the _ssr_* helpers; _sitemap_xml lists one URL per work;
DAY_CACHE is the one-day Cache-Control header), static/ (app.js router with
parseRoute and the VIEWS map for /, /search, /about, /work/{id}, /page/{id};
views in static/views/; EN and DE strings in static/i18n.js; helpers in
static/dom.js including setLabel and folioLabel; index.html with the site nav
linking Search and About; robots.txt and llms.txt). Store access is in
src/leibniz/db.py: Work(gwlb_object_id, set_name, title, shelfmarks, metadata,
manifest_url, n_canvases), iter_works(conn, set_name=None), get_pages.
_katalog_for_work(conn, work_id) in api.py returns the catalogue records linked
to a work; its `correspondent` field is the record's `absender` only, which is
why the browse index reads the raw record metadata instead (LBr rule below).
Shelfmark parsing lives in src/leibniz/catalog/shelfmarks.py:
normalize_signature(raw) → Signature(family in {"LH","LBr","Marg","LK"} or
None, parts: tuple of normalised tokens, lower-cased, Roman numerals converted
to Arabic, e.g. "LH XXXV, 3 A 8" → ('35','3','a','8'), blatt). Tests:
tests/test_web_*.py with the fixture store `store_path` from tests/conftest.py
and the `_client` helper in tests/test_web_api.py. The app starts with
`uv run leibniz serve` (a top-level command; `--backend none` runs it without a
search index; the default store path is data/inventory.sqlite, opened read-only;
single-worker mode is plain uvicorn and works on Windows). Everything runs
offline. Branch `web-browse-index`, created from the updated main.

The site has search, work pages and page views, but no way to browse. A reader
from the Leibniz-Edition ([name and role withheld]) asked
for "an index of the individual shelfmark groups", so that one can "start from
the group name ('Faszikel') and identify the relevant shelfmark and folios". The
work pages already list folios with thumbnails; the missing levels are above them.

## The data, as it actually is (2,225 works)
You have the live store, so export the metadata the grouping needs as committed
fixtures, read-only. Write scratchpad/export_live_fixtures.py with this content
and run it from the repo root with `uv run python scratchpad/export_live_fixtures.py`
(adjust the path to the store if the operator gave another):

    import json, sqlite3
    from pathlib import Path
    conn = sqlite3.connect("file:data/inventory.sqlite?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    out = Path("tests/fixtures")
    def dump(name, sql):
        rows = [dict(r) for r in conn.execute(sql)]
        body = "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n"
        (out / name).write_text(body, encoding="utf-8", newline="\n")
        print(f"{name}: {len(rows)} rows")
    dump("works_live.json",
         "SELECT gwlb_object_id, set_name, title, shelfmarks, n_canvases "
         "FROM works ORDER BY gwlb_object_id")
    dump("lbr_correspondents_live.json", """
         SELECT c.work_id,
                json_extract(k.metadata,'$.absender') AS absender,
                json_extract(k.metadata,'$.adressat') AS adressat,
                COUNT(*) AS n_records,
                MIN(json_extract(k.metadata,'$.titel')) AS titel
           FROM crosswalk c
           JOIN katalog_records k ON k.record_id = c.katalog_record_id
           JOIN works w ON w.gwlb_object_id = c.work_id
          WHERE w.set_name = 'LeibnizBriefwechsel'
          GROUP BY c.work_id, json_extract(k.metadata,'$.absender'),
                   json_extract(k.metadata,'$.adressat')
          ORDER BY c.work_id, n_records DESC""")
    dump("crosswalk_works_live.json",
         "SELECT DISTINCT work_id FROM crosswalk ORDER BY work_id")

Expect 2,225 works rows, a few thousand LBr rows, and about 1,300 crosswalked
work ids; the three files together are well under a megabyte of CC0 and CC BY
metadata and are committed with this phase. The works file carries
`shelfmarks` as a JSON-encoded array inside a string. Inspect the real rows
before writing the rules, and report in STATUS.md any shape the rules below do
not cover. What the census and these files show:
- LeibnizHandschriften, 756 works: titles carry the section name and shelfmark,
  e.g. "Leibniz-Handschriften zur Mathematik LH 35, 3 A 8", "Leibniz-Handschriften
  zur Theologie LH 1, 19", "Leibniz-Handschriften zu Braunschweig-Lüneburg LH 23,
  2, 21". The section is the first shelfmark part (LH 1 … LH 42, the Ritter
  scheme); its name is the "zur/zu/zum …" phrase in the title.
- LeibnizBriefwechsel, 1,059 works: titles are the generic "Nachlass Gottfried
  Wilhelm Leibniz"; the shelfmark is "LBr. 228" or "LBr. F 20". The harvest keeps
  no names from MODS, so the correspondent is only available from the linked
  catalogue records: their metadata carries `absender` and `adressat` as separate
  fields, each like "Oldenburg (KorrespDB) (GND)" or "Leibniz (GND)", and a
  `titel` like "Leibniz an Heinrich Oldenburg". Roughly half of all works have
  records today, so there must be a graceful fallback.
- LeibnizMarginalien, 396 works: titles are the long titles of the annotated
  printed books; shelfmarks like "Leibn. Marg. 64:1" or "Leibn. Marg. 230, Stück 1".
- leibniz-rekonstruktionen (2) and Leibnitiana (12): small, list them as their
  own groups.

## Task 1 — Grouping logic (pure, tested)
Add src/leibniz/web/browse.py with pure functions that take Work rows, a map
work_id → correspondent rows (absender, adressat, n_records, titel), and the set
of work ids with records, and return a tree family → section → entries. Rules:
- LH: section = first part as an integer; section label = the majority "zur/zu/
  zum X" phrase among that section's titles, fallback "LH <n>". Entries sorted by
  natural order of the remaining parts (numeric before alphabetic, 2 before 10).
- LBr: one section, entries labelled by correspondent: pool the work's absender
  and adressat values, drop Leibniz himself (any value whose name part is
  "Leibniz"), strip parenthesised source tags like "(KorrespDB)" and "(GND)",
  normalise "Surname,Initials" to "Surname, Initials", and take the most
  frequent remaining name weighted by n_records; fallback to the titel pattern
  "X an Leibniz" / "Leibniz an X"; final fallback the bare shelfmark. Offer both
  orders in the data: alphabetical by label and by LBr number (lettered numbers
  such as "F 20" sort after the plain numbers, by letter then number).
- Marg: one section, sorted by Marg number, title truncated to about 120
  characters at a word boundary with the full title in a title attribute.
- Everything else (LK, foreign, unparsable, the two small sets): an "Other"
  section per set, sorted by shelfmark string.
Each entry: work_id, shelfmark(s), label, title, n_canvases, and whether the work
has catalogue records. Tests on synthetic Work rows covering every rule above,
including Roman-numeral shelfmarks, a work whose only correspondent row is
Leibniz himself, and missing records; plus one test over the three live
fixtures asserting the headline shape: every work lands in exactly one entry,
the LH sections present, and the share of LBr works that received a
correspondent label (print that share; it goes in STATUS.md).

## Task 2 — API
GET /api/works (no id): the full list, compact rows (work_id, set, title,
shelfmarks, family, section, section_label, label, n_canvases, has_katalog),
plus a `groups` tree from Task 1, under DAY_CACHE. Compute once per process on
first use and hold in memory (the works table changes only on a corpus run; the
app restarts then; several worker processes each holding a copy is fine); build
the correspondent labels with one grouped SQL query over the crosswalk and
katalog_records tables (json_extract on metadata for absender, adressat and
titel; the same query as the export above) rather than one query per work.
Optional `?set=` and `?family=` filters. Make sure the existing
/api/works/{work_id} and /api/works/{work_id}/text routes are not shadowed. Add
`Allow: /api/works` (no trailing slash) to static/robots.txt: the current rule
allows only `/api/works/`, and `Disallow: /api/` would catch the bare path. Tests
on the fixture store: shape, grouping of the fixture's LH and LBr works, filters,
cache header, robots.

## Task 3 — The browse page, verified against the real store
- Route /browse: add to INDEX_ROUTES with a server-rendered fallback
  (_ssr_browse) that lists every family and section with links to the work
  pages, so crawlers and readers without JavaScript get the whole index; add
  /browse to the sitemap and a line to static/llms.txt.
- Client: static/views/browse.js registered in app.js (parseRoute and the VIEWS
  map); a nav link "Browse" (DE: "Signaturen") in index.html via data-i18n, and a
  link from the search view's empty state. Layout: family tabs or headed
  sections (Handschriften, Briefwechsel, Marginalien, Other), collapsible
  sections using details/summary with counts (works, pages), a client-side
  filter box that narrows by shelfmark, label or title as you type, and an
  LBr sort toggle (by name / by number). Each entry links to /work/{id}; every
  section has a stable anchor (e.g. #lh-35) so work pages can link back: add a
  breadcrumb on the work page "Browse › LH 35 · Mathematik" pointing at the
  anchor. All strings EN and DE; section labels are the archive's own German
  phrases and stay as data in both languages. Keyboard reachable, visible focus,
  no horizontal scroll at phone width, honest about machine text where the
  existing views are.
- Tests: the INDEX_ROUTES test covers /browse; SSR contains a link to each
  fixture work; sitemap includes /browse; robots allows /api/works.
- Verification against the real store. Start the app in the background on the
  master store, read-only, on a spare port: `uv run leibniz serve --backend none
  --port 8765` (search answers 503 by design; works, pages and /browse work).
  First over HTTP: /browse returns the server-rendered index with every family
  and a link per work; /api/works returns the rows and the groups tree in well
  under a second after the first call; /robots.txt, /sitemap.xml and /llms.txt
  carry the new lines. Then in a browser. If Node is present: Playwright from
  npm in scratchpad/pw (`npm init -y`, `npm install playwright axe-core`, `npx
  playwright install chromium`, about 150 MB; plain `chromium.launch()`, no proxy
  settings here), load http://127.0.0.1:8765/browse and check: the tree renders,
  the filter narrows, the LBr toggle reorders, an entry link resolves to its
  work page, a work page's breadcrumb lands on its section anchor, EN and DE, no
  console errors, axe-core zero violations; phone width too (390 px, no
  horizontal scroll). Screenshots under scratchpad/, never in the repo. If Node
  is absent and the operator declined to install it, print that URL and the
  same checklist for the operator to run in their own browser, and wait for
  their report. Stop the server when done.

## Task 4 — Record, commit, push, hand over
ruff + pytest clean (with the Windows caveat from Task 0 recorded). STATUS.md: a
"W3" entry (Current state, Phase log, Key numbers, Next) with what was built,
the grouping rules, the measured LBr label share, the known limits
(correspondent labels exist only where catalogue records are linked, about half
the works today; a full Arbeitskatalog export from TELOTA would complete them,
and the labels then fill in by re-running the catalogue crosswalk on the
desktop and copying the store, with no code change), the three live fixtures,
the Windows notes (.venv-win, suite results), and the follow-ups you see; under
Next, the operator's §9 deploy and the live checks of Task 5. Append this prompt
verbatim to PROMPTS.md under a heading "Follow-up phases (2026-10)" (create it
if absent). Commit in sensible pieces with descriptive messages (fixtures and
.gitignore; browse.py and tests; API; viewer; docs), then `git push -u origin
web-browse-index`. Then hand over: print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...web-browse-index?expand=1
(or, if gh is authenticated and the operator says yes, create the PR with
`gh pr create --base main --head web-browse-index` and a short title and body),
tell the operator what to read in the diff (the STATUS.md entry, the LBr share,
any shapes the rules could not place), and ask them to say "merged" when the
PR is merged. Wait. Do not touch the branch or main in the meantime.

## Task 5 — Deploy, only after "merged", only with a yes
Ask the operator for the SSH target (for example root@leibnizlegible.com) and
whether to run the deploy from this session. Show the exact command first and
run it only on an explicit yes. It is the §9 "Update the app" block from
deploy/README.md and nothing else; the remote shell is bash, so `&&` is right
inside the quoted string even from PowerShell; if the login user is not root,
prefix systemctl with sudo:

    ssh <target> "sudo -u leibniz -H git -C /opt/leibniz-legible pull --ff-only && sudo -u leibniz -H env UV_CACHE_DIR=/opt/leibniz-legible/.uv/cache UV_PYTHON_INSTALL_DIR=/opt/leibniz-legible/.uv/python uv sync --project /opt/leibniz-legible --frozen --no-dev --extra web && systemctl restart leibniz-legible && sleep 2 && curl -s http://127.0.0.1:8000/healthz"

Code only: no index rebuild, no Meilisearch restart, no new dependency. If the
operator prefers to run it themselves, print the block and wait for their
output. Then verify live, over HTTP from here: /browse is 200 and its
server-rendered body holds the family headings, a section anchor and a /work/
link; /api/works is 200 JSON with `groups`; /robots.txt has the exact line
`Allow: /api/works`; /sitemap.xml lists /browse; /llms.txt mentions /browse;
and the three W1/W2 checks from Task 0 all pass now. Tell the operator to open
https://leibnizlegible.com/browse in a private window and look at the nav link,
EN and DE, the filter, the LBr toggle, one LH anchor and a work page's
breadcrumb; returning readers may see the old ES modules for up to an hour
(Caddy's cache on /static/). If anything fails live, say exactly what, propose
the fix as a new branch, and do not patch anything on the server.

## Task 6 — Draft the message to [the reader] (the operator sends it)
Write a short reply in English to his mail of 2 October, as a draft in
scratchpad/[reader]-reply.md and in chat: the index is live at
https://leibnizlegible.com/browse, grouped by LH section with the Ritter names,
LBr by correspondent where the Arbeitskatalog links exist, Marginalien by
number; the transcription export and the overlay fix are live as well (if the
Task 5 checks confirm it); ask whether the grouping matches how the
Arbeitsstellen think of the Faszikel; and repeat, briefly, the two asks from
the operator's 2 October mail: the TELOTA contact for an Arbeitskatalog export
(which would complete the correspondent labels for the other half of the
works), and CC BY or written permission for the Reihe VIII reading text. No
numbers in the draft that the session did not measure. Do not send anything.

## Finish
A closing summary in chat: what is merged and live, the LBr label share, the
pre-existing Windows test failures if any, what [the reader]'s reply would unlock, and
that the next phase is K1 from a fresh session on the merged main.
~~~~


### Phase C2b — Close the C2 audit and learn from it (run 2026-10-07)

~~~~text
Phase C2b — Close the C2 audit and learn from it: score the PHILIUMM verdicts,
name the failure patterns, measure their reach across the mint, build the cheap
fix. One local session on the operator's desktop (WSL2 Ubuntu).

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md, in particular the C2 close-out of 2026-09-16 and Open
question #18. If this prompt conflicts with the repo, the repo + STATUS.md win;
record the divergence in STATUS.md. Write the "C2b — audit close-out" entry in
STATUS.md after every task; if one exists, continue from its first unfinished
task on the existing branch.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible. data/inventory.sqlite is the MASTER store (16 GB:
13.5M v1 lines, 297k gt_lines): open it read-only only (`uv run leibniz …`
commands open it mode=ro; your own Python uses a `file:…?mode=ro` URI); never
write, VACUUM or move it. The page-image cache is /mnt/d/leibniz-images.
`.venv` is the pipeline environment (never run `uv sync` against it); use the
side environment `.venv-w3` (export UV_PROJECT_ENVIRONMENT=.venv-w3 for every
`uv` command; its extras are web, gt and release). This phase writes nothing to
the store: the fix it builds is applied by a re-mint scheduled before C3, not
here. Every result lives in reports/ as small committed files rendered by code
from data; never write a number you did not produce. The operator merges, after
the PHILIUMM team has seen the scored result (the repo is public). You push the
branch and hand over. Branch: `c2-audit-closeout`, created from main.

## Task 0 — Pre-flight (report, then wait for a go)
`git status --porcelain` shows nothing but the operator's own untracked files
(logs, *.log, resume-run.sh, .python-version, reports/gt-audit/gt-audit.html
and the like; leave them alone); HEAD is main; `git pull --ff-only origin
main`. Confirm reports/gt-audit/gt-audit-verdicts-philiumm.csv exists with the
columns ref, stratum, verdict, note and about 200 rows; if not, ask for its
path. Baseline: `uv run ruff check .`, `uv run ruff format --check .`,
`uv run pytest -q`; record the counts. Print a short plan and wait for "go".

## What arrived
On 2026-10-07 Denisa-Florina Bumba and David Rabouin (PHILIUMM) returned the
200-line audit sheet (reports/gt-audit/gt-audit.html, built 2026-09-16 by
`leibniz align audit-sheet --seed 0`, equal numbers per stratum; its lines are
in reports/gt-audit/gt-audit-lines.csv with gt_text and htr_text per ref) with
199 of 200 lines judged. Their summary, in substance: they sometimes corrected
the transcription in the note but still marked "correct" when the alignment
was right and the issues minor; one line they could not decipher; very often
the end-of-line hyphen is missing on words cut at the line end while the word
slice itself is right; "boundary" was used for small boundary issues, a letter
missing at the start or one added at the end; sections with mathematical
expressions are generally wrong, as in their own HTR; additions appear inline
because the edition renders the final state, although visually they do not
belong to the line; overall the alignments are very good. The operator's own
preliminary 20-line pass (12 correct, 5 wrong, 3 unreadable, fair copies only)
is reports/gt-audit/gt-audit-verdicts.csv with reports/gt-audit.md; its
second-witness check found all five "wrong" verdicts contradicted by the
machine reading.

## Task 1 — Score
`uv run leibniz align audit-score reports/gt-audit/gt-audit-verdicts-philiumm.csv`
regenerates reports/gt-audit.md: precision per stratum with Wilson intervals,
the corpus-weighted figure against the 95 % gate, the second-witness list.
Read it. Also compute agreement between the operator's 20 verdicts and theirs
on the same refs and put it in the report. Record the verdict, PASS or FAIL,
per stratum and weighted, and what "usable" (boundary included) gives. Commit.

## Task 2 — Name the patterns
Add src/leibniz/align/audit_patterns.py (pure, tested on synthetic rows): for
each judged row, from verdict, note, gt_text, htr_text, the folded similarity
and the HTR line's last character, assign one pattern:
- hyphen: the HTR line ends in one of the aligner's hyphen characters
  (align.py _HYPHENS) and the minted text ends in a letter;
- boundary-letter: verdict boundary, or a one-character difference at either
  end between the minted text and a correction given in the note;
- math: digits, operators, Greek or bracket density above a cut you state, or
  the note says so;
- addition: the note says so, or the minted text exceeds the HTR reading in
  folded length by more than the aligner's insertion floor;
- unreadable; correct; other.
Notes are free text in English or French: match conservatively and keep a
committed override CSV (ref, pattern, why) for rows the rules cannot decide;
print those rows and ask the operator to settle them in chat. Where a note
carries a corrected transcription, store (ref, minted text, correction) in
reports/gt-audit/gt-audit-philiumm-corrections.csv and compute the folded
similarity between minted and corrected text: the first measured sample of the
normalization tax on real lines. Extend reports/gt-audit.md with a pattern
table per stratum and the corrections table (render through audit.py's
report code, prose templated). Commit.

## Task 3 — Reach across the mint (read-only)
`leibniz align audit-reach`, over all open-bucket gt_lines joined to the v1
lines (line_image_ref is the canonical "{page_id}:{line_seq:03d}"; take the
recognised row as audit.line_geometry does):
- hyphen: minted lines whose HTR text ends in a hyphen character while the
  minted text ends in a letter; count and share per stratum and per volume;
- math: the Task 2 density score per minted line, plus the piece's volume
  (Reihe III and the mathematical LH 35 pieces); counts above the cut;
- additions: minted lines on pages whose page_stats overlap or short-line
  fractions exceed the heavy-revision cuts in align/stratum.py (a proxy; say so);
- hand: per minted line, whether the piece's catalogue textart carries "eigh."
  (Leibniz's own hand; gt_lines.source names the record id, katalog_records
  holds textart); shares per stratum and per volume;
- Marginalien: minted lines whose work is in the Marginalien set (expected
  near zero; measure).
Writes reports/gt-audit/reach.md and reach-summary.json; per-line flags to
data/gt/flags.jsonl (ref, flags) for C3, with a committed count table. Run it
here (minutes). Commit.

## Task 4 — The cheap fix, built and tested, not applied
In src/leibniz/align/align.py add keep_hyphen (default True for new mints):
when dehyphenation joined a word across a line break, the earlier line's
minted slice ends with the very hyphen character the HTR line showed ("=" stays
"="), and the next line's slice starts with the rest of the word as now.
AlignedLine records that it happened. Tests; the B2 evaluate harness gives the
same numbers with the option off. Do not re-mint: the re-mint runs once, before
C3, with every C2b flag in place (STATUS.md's Next records it with the runbook
line: the factory is idempotent, about two hours on six shards). Commit.

## Task 5 — Amend C3
In PROMPTS.md, under the C3 prompt's 2026-09-16 amendment, add "Amendment 2
(2026-10, from the audit)": train on re-minted lines with hyphens kept; exclude
lines flagged math and lines from Marginalien works; exclude PHILIUMM's 1,010
pages from the held-out set (reports/philiumm/heldout_pages.csv once P1 has
produced it); stratify the held-out set by stratum, language and hand (eigh.);
keep the 199 PHILIUMM-judged lines and their corrections out of training and
use them as a sanity set; report CER by hand. Commit.

## Finish and hand-over
STATUS.md: the C2 gate verdict with its numbers; Open question #18 closed or
restated; the patterns and their reach; the hand census; under Next, the
re-mint before C3. Append this prompt verbatim to PROMPTS.md under "Follow-up
phases (2026-10)". ruff + pytest clean. `git push -u origin c2-audit-closeout`,
print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...c2-audit-closeout?expand=1
and a five-line summary of the verdict for the operator to send to the PHILIUMM
team. Do not merge.
~~~~


### Phase P1 — PHILIUMM cross-checks (Tasks 1 and 2 built 2026-10-08; Task 3 waits for the layout model)

~~~~text
Phase P1 — PHILIUMM cross-checks: their aligner sample, the A VI,4 cross-comparison,
and a layout-zone census. One local session on the operator's desktop (WSL2
Ubuntu), with the data, the store and the GPU at hand.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md. If this prompt conflicts with the repo, the repo + STATUS.md
win; record the divergence in STATUS.md. Write the "P1 — PHILIUMM cross-checks"
entry in STATUS.md after every task. If STATUS.md already carries a P1 entry,
continue from its first unfinished task; if that entry says the branch was
merged, create `philiumm-layout-census` from main and continue there.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible, the one the C1 corpus run, the C2 mint and W3 used.
Facts, to verify in Task 0 rather than assume:
- data/inventory.sqlite is the MASTER store (16 GB: 13.5M v1 lines, 297k
  gt_lines). Open it read-only only: `uv run leibniz …` commands open it
  mode=ro; your own Python uses a `file:…?mode=ro` URI. Never write to it, never
  VACUUM or move it, never delete anything under data/. This phase writes
  nothing to the store.
- The page-image cache is /mnt/d/leibniz-images (the D: drive); the runbooks
  pass it as `--images /mnt/d/leibniz-images`, and pages.local_path is relative
  to that root (see align/audit.py attach_images).
- `.venv` is the pipeline environment (kraken, torch with CUDA): never run
  `uv sync` against it and never install into it. Use the side environment W3
  made, `.venv-w3` (web, gt and release extras; gt brings Pillow for crops):
  export UV_PROJECT_ENVIRONMENT=.venv-w3 in your shell for every `uv` command.
  This phase adds no Python dependency to the project; PHILIUMM's pipeline gets
  its own environment under data/philiumm/ (Task 3).
- The GPU is a GTX 1660 Ti (6 GB) reachable from WSL2. Task 3 may use it;
  nothing else here needs it.
- Long jobs run under nohup with a log under logs/ (gitignored); poll the log,
  print its tail when done. Ask the operator for a go before: cloning and
  installing their pipeline, running it, a download over 1 GB, a job expected
  to run over an hour, and installing any software (apt, npm).
- Every result lives in reports/philiumm/ and reports/layout/ as small
  committed files (Markdown, JSON, CSV of at most a few thousand rows),
  rendered by code from data, prose templated. Bulky artefacts (downloads,
  crops, HTML sheets, models, full CSVs) go under data/ (gitignored) and are
  described, not committed. Never write a number you did not produce.
- The operator merges, and only after the numbers have been shared with the
  PHILIUMM team: the repo is public, so a merge is a publication. You push the
  branch and hand over; you never merge. Nothing is deployed. Branch:
  `philiumm-crosschecks`, created from main.
- Their two GitLab repositories have no licence file, and on 2026-10-06 they
  said they are considering CC BY-NC for their dataset and models as well. Read
  their code, run their pipeline locally under data/, copy nothing from either
  repository into this one, and record the commit SHAs you used.

## Task 0 — Pre-flight (report, then wait for a go)
1. `git status --porcelain` shows nothing but the operator's own untracked
   files (logs, *.log, resume-run.sh, .python-version, reports/gt-audit/
   gt-audit.html and the like; leave them alone). `git rev-parse --abbrev-ref
   HEAD` is main; `git pull --ff-only origin main`; confirm the remote.
2. `df -h data /mnt/d`; `uv --version`; `git lfs version` (Task 3 needs it;
   if missing, ask before `sudo apt-get install -y git-lfs`); `nvidia-smi`.
3. Baseline in .venv-w3: `uv run ruff check .`, `uv run ruff format --check .`,
   `uv run pytest -q`. Record the counts.
4. Ask the operator two things and wait: whether PHILIUMM's new RF-DETR model
   has been published (the gate before Task 3), and whether Task 3 should run
   on the current bundled model regardless, for the 13 October call.
5. Print a short plan with the steps you expect, their durations and what
   needs a go, and wait for the operator's "go".

## Background (all you need)
The ERC PHILIUMM project (David Rabouin, Denisa-Florina Bumba; Laboratoire SPHERE,
Université Paris Cité – CNRS) built the Leibniz HTR model this project runs
(FoNDUE-GD_v2_ft_Leibniz, Zenodo 10.5281/zenodo.21457538, CC BY 4.0 as obtained)
and the baseline segmentation model of the v1 corpus run (Zenodo
10.5281/zenodo.21537859, CC BY 4.0). In an email exchange from 2026-09-28 they
offered to collaborate; Denisa pointed to three things (below); she and David
then judged the 200-line ground-truth audit sheet and returned it on
2026-10-07 (scored in a separate session, not here); and a call is set for
2026-10-13. The owner brings three cross-checks of their three things to that
call. On 2026-10-07 David also noted that their model was not trained on
printed material (the Marginalien), on hands other than Leibniz's, or on
Kurrent; Task 3's sample takes the first of these into account.
1. Their alignment code (PASSIM `seriatim --linewise` + a filter + a sliding-window
   second pass):
   https://gitlab.com/eman8/scripts/htr-ocr/alignement-verite-de-terrain-et-transcriptions
   (branch main; raw files at .../-/raw/main/<path>). Worked example in the repo:
   GT/LH_1_3_4_0001-0002_1.txt (edition reading text for LH I 3,4 Bl. 1–2, from
   A VI,4); HTR/LH_1_3_4_0002r-0001v.xml and HTR/LH_1_3_4_0002v-0001r.xml (PAGE XML
   with HTR lines; each image is an opening with two folios); htr_replaced_gt/ (the
   same files with aligned GT written into each line's <Unicode>, blank where
   nothing aligned); alignment_report.csv with columns
   filename,nb_htr_lines,nb_gt_aligned,pct_gt_aligned,nb_low_conf,pct_low_conf,
   nb_ratio_too_low,pct_ratio_too_low,nb_ratio_too_high,pct_ratio_too_high,
   nb_no_alignment,pct_no_alignment,nb_window_passages,nb_fallback_lines.
   Their totals on the sample, read from that committed CSV: 257 HTR lines, 230
   aligned (89.5 %). Settings: the README's defaults are conf_threshold 0.0,
   min_token_ratio 0.4, max_token_ratio 2.5 and min_sim 0.5, and its usage
   example runs --conf_threshold 0.7; the dataset card states the noisy split was
   filtered at Levenshtein ≥ 0.7. Treat 0.7 as the comparable per-line threshold
   and say where each number comes from; do not state any other setting without
   a source. Record the commit SHA you fetched.
2. Their dataset, Hugging Face DenisaBumba/htr_leibniz_dataset_v1 (CC BY 4.0 as
   obtained; the former name DenisaB/… redirects to it; Zenodo twin
   10.5281/zenodo.21622297, whose data.zip is 4.2 GB, do not fetch it).
   train/noisy/ = 735 PAGE XML + JPG pages whose lines carry edition text aligned
   from A VI,4 by the code above (blank <Unicode> where unaligned; 43,372 aligned
   lines); train/clean/ = 248 hand-corrected pages; val/ = 27 pages (used by this
   project's B1 reproduction). The Hub lists 1,966 files under train/ and 54
   under val/, consistent with those counts. Names are shelfmark + folio:
   LH_1_12_2_0124r.xml = LH I 12, 2 Bl. 124r; LH_1_20_0063r-0062v.xml = an
   opening showing 63r and 62v. List files via
   https://huggingface.co/api/datasets/DenisaBumba/htr_leibniz_dataset_v1 (the
   siblings array); fetch with
   https://huggingface.co/datasets/DenisaBumba/htr_leibniz_dataset_v1/resolve/main/<path>.
   Only XML files are needed. Update HF_DATASET in src/leibniz/htr/artifacts.py
   and its attribution line to the new name. The model this project runs trained
   on the noisy and clean pages, so those 1,010 pages must be excluded from any
   future evaluation set (Phase C3).
3. Their layout pipeline:
   https://gitlab.com/eman8/scripts/htr-ocr/scripts-pour-le-pretraitement-des-corpus-pour-escriptorium
   (branch main; models in Git LFS: `git lfs install`, clone, `git lfs pull`).
   The README gives two installation paths; the Linux one is a single Python 3.12
   environment (supervision requires 3.12) with `pip install -r requirements.txt`
   (rfdetr, supervision, kraken 7), marked "should work, not tested"; a uv venv
   is an acceptable substitute for their conda command. Run:
   `python main_pipeline.py --input <images> --output <results> --config
   config_local.json` (no API key; the local config names their last best model
   and a detection confidence of 0.4). Steps: RF-DETR zone prediction (MainZone,
   MarginTextZone, DigitizationArtefactZone, GraphicZone-figure, NumberingZone;
   formula classes GraphicZone-formula{,-inline,-strikethrough,-complex} masked if
   emitted), COCO → PAGE XML regions (03_regions_xml), masks over figure and
   formula zones, binarisation, masked image, Kraken baselines inside text zones
   (06_baselines_and_htr), merge, polygon simplification, overlap fixes, line
   splitting; final PAGE XML in 10_fixed_lines. Bundles
   models/segmentation/baselines/best_0.4750.safetensors, apparently the same
   checkpoint as this project's v1 segmenter (blla_ft_leibniz_v1_0.4750): verify
   by checksum, and if so the only difference from v1 lines is masking plus
   region merge. Denisa expects to publish a new RF-DETR model, fine-tuned on
   corrected formula polygons and compared with D-FINE, by mid to late October
   2026; Task 3 is gated on it unless the operator said otherwise in Task 0.

## Task 1 — This project's aligner on their sample (needs no local data)
- Add src/leibniz/align/pagexml.py: PAGE XML TextLines in reading order (region
  order, then line order) with id, Coords polygon, Baseline, and <Unicode> text
  (may be empty). Offline test on a trimmed fixture.
- Fetch the sample files (cache-first, polite UA) into data/philiumm/sample/.
- Run align_piece (src/leibniz/align/align.py; inputs HtrLine(ref, text)) with the
  full GT text against each HTR file separately with free_edition_ends=True,
  mirroring their per-file run; also try the two page concatenation orders and
  report the best. Use the default threshold and also a threshold you argue is
  comparable to their 0.7 rule.
- Produce their CSV columns from this project's result (nb_gt_aligned = minted,
  nb_no_alignment = declined, filter columns N/A) and a line-by-line comparison
  against their htr_replaced_gt output with this project's normalizer
  (src/leibniz/align/normalize.py) and folded similarity (src/leibniz/align/dp.py,
  as audit.py uses it): both aligned and same text (≥ 0.9), both aligned but
  different, this project only, theirs only, neither. Print the differing pairs.
- CLI `leibniz align philiumm-sample`; report reports/philiumm/alignment-sample.md.
  Commit. CHECKPOINT A: update the STATUS.md entry and commit.

## Task 2 — Cross-compare A VI,4 (run here)
Build, with offline tests on fixtures, one CLI with subcommands, then run them
in order on the store:
- `leibniz align philiumm-vi4 fetch`: the 735 train/noisy XML files into
  data/philiumm/noisy/, cache-first, resumable, at most one request per second
  (about fifteen minutes).
- `leibniz align philiumm-vi4 match`: file name → shelfmark + folio(s); works via
  works.shelfmarks and src/leibniz/catalog/shelfmarks.py (Roman numerals likely;
  write the parser to inspect real shelfmark strings and report unparsed names);
  canvases via pages.label with src/leibniz/align/resolve.py; openings may map to
  one canvas or two, handle both, report ambiguities. Lines by geometry: scale
  their Coords from imageWidth/imageHeight to pages.width/height, greedy
  one-to-one by polygon IoU (report threshold and sensitivity). The lines table
  may hold several runs per page: use the run that produced the recognised text.
  gt_lines.line_image_ref carries the canonical line id "{page_id}:{line_seq:03d}"
  for factory-minted rows (align/pairs.py; audit.split_ref parses it); the test
  store's seeded gt_lines rows use an older "#xywh" form, so assert the real
  form on the store before relying on it.
- `leibniz align philiumm-vi4 compare`: their aligned text vs gt_lines.text for the
  matched line, lines.text as third witness; normalizer + folded similarity;
  buckets agree (≥ 0.9), near (0.7–0.9), disagree (< 0.7), this project only,
  theirs only, neither; per stratum and per page. State what agreement does not
  prove (two aligners fed the same edition text can share a mistake).
  Writes: reports/philiumm/vi4-crosscheck.md; reports/philiumm/vi4-summary.json;
  reports/philiumm/heldout_pages.csv (this project's page_ids for all 1,010 of
  their pages, for C3); reports/philiumm/vi4-disagreements-sample.csv (at most
  500 rows); full disagreement and double-witnessed CSVs under data/philiumm/.
- `leibniz align philiumm-vi4 sheet`: a second audit sheet of disagreements,
  data/philiumm/philiumm-disagreements.html, through the crop machinery in
  src/leibniz/align/audit.py. That machinery must accept an explicit list of
  line refs; if K1 has already landed that refactor on main, reuse it, else do
  it here without changing the existing sheet's behaviour or tests. The sheet
  downloads verdicts in the same CSV shape as the C2 sheet (ref, stratum,
  verdict, note), so the PHILIUMM team could judge it the way they judged the
  first. Never touch reports/gt-audit/gt-audit-lines.csv or
  gt-audit-verdicts*.csv.
Every subcommand ends with a compact printed summary. Run fetch, match, compare
and sheet here (crops from /mnt/d/leibniz-images), read the results, commit
reports/philiumm. CHECKPOINT B: update the STATUS.md entry and commit.
GATE for Task 3: per the operator's Task 0 answers. If the new model is out, or
the operator asked for the census on the current model, continue. Otherwise
state in STATUS.md that Task 3 waits for the model, commit, and go to the
hand-over; a later session resumes at Task 3 with this prompt.

## Task 3 — Layout-zone census (run here, with a go)
Build, with fixtures:
- `leibniz layout sample --n 400 --seed 0`: equal numbers per stratum
  (page_stats.stratum_heuristic; fall back to set/work if NULL, which it is
  under C1) plus 100 pages from LH 35 (find via works.shelfmarks) and 100 pages
  from the Marginalien set as a separate block (printed body with marginal
  notes, the case David raised), reproducible; symlink or copy cached JPEGs
  from /mnt/d/leibniz-images into data/philiumm/layout-sample/images/ named by
  page_id; write the sample list to reports/layout/sample.csv.
- tools/philiumm-layout-env.sh: creates a separate Python 3.12 environment under
  data/philiumm/rfdetr-env/ (uv venv or python -m venv), clones their pipeline
  with LFS into data/philiumm/rfdetr-pipeline/ (record the commit SHA and the
  checksums of the model files), installs requirements, and prints a diagnosis
  on failure. tools/philiumm-layout-run.sh: runs main_pipeline.py on the sample
  with config_local.json under nohup, logging to logs/. Never modify their
  repo; keep any local patch as a .patch file under data/philiumm/.
- src/leibniz/layout/zones.py (pure, tested): parse 03_regions_xml zones by class
  with polygons and 10_fixed_lines lines; geometry via
  src/leibniz/pipeline/geometry.py or plain Python, no new heavy dependency.
- `leibniz layout zone-census`: per page and per stratum, the LH 35 and the
  Marginalien blocks separate: zones per class; share of pages with any figure,
  formula, margin zone; v1 lines whose polygon lies mostly inside a figure or
  formula zone, count and share; on the Marginalien block, v1 lines inside
  MainZone (the printed body) vs MarginTextZone (the notes); v1 line count vs
  their final line count; matched-line comparison by IoU. Writes
  reports/layout/zone-census.md, reports/layout/zone-census-summary.json,
  reports/layout/zone-census-per-page.csv (the sample is small enough to commit).
Ask for a go, run the environment script, the sample, the pipeline (hours, GPU
optional) and the census here; if the environment cannot be made to work on
this machine, say so in STATUS.md and stop the task honestly. Commit
reports/layout. CHECKPOINT C: update the STATUS.md entry and commit.

## Finish and hand-over
Complete STATUS.md's "P1 — PHILIUMM cross-checks" entry: what was built, key
numbers, what is unmeasured and why, open questions (opening vs folio canvas
mapping; class coverage of the bundled checkpoint; flagging v1 lines inside
non-text zones in the viewer now; a v2 zones table with SegmOnto type, polygon
and a LaTeX field; the printed-body share of Marginalien lines), next steps
(rerun Task 3 with each later PHILIUMM model; use heldout_pages.csv in C3;
the licence change PHILIUMM is considering, with the fact that this project's
copies were obtained under CC BY 4.0, for the lawyer memo). Append this prompt
verbatim to PROMPTS.md under "Follow-up phases (2026-10)". ruff + pytest clean,
all tests offline. Commit in sensible pieces and `git push -u origin
philiumm-crosschecks`. Then hand over: print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...philiumm-crosschecks?expand=1,
a plain-language summary of the cross-checks for the operator to bring to the
call (what agrees, what differs, what it does not prove), and the reminder
that the PR is merged only after the PHILIUMM team has seen the numbers. Do
not merge.
~~~~


### Phase S1 — A staging site on the VPS (built 2026-10-08; the install is the operator's)

_Run in a cloud session under the 8 October plan's session preamble: one branch
(`claude/dazzling-hopper-uxji2x`, not `deploy-staging`), no merge, no §9
production update, the kit installed on the box from a clone of the branch and
`staging.sh` run from that clone or from the staging checkout. The preamble's
text is below the prompt, once; the departures are in `STATUS.md`, Divergences._

~~~~text
Phase S1 — A staging site on the VPS: see a branch on the real server, behind a
password, before anyone else does. One local session on the operator's desktop
(WSL2 Ubuntu) for the code and the runbook; the installation on the box over
SSH, each step shown and run only on the operator's yes.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md, STATUS.md, and deploy/README.md in full (§1, §3 to §5, §8, §9 and §13
above all), deploy/Caddyfile, deploy/leibniz-legible.service, deploy/env.example
and deploy/install.sh. If this prompt conflicts with the repo, the repo +
STATUS.md win; record the divergence in STATUS.md. Write the "S1 — staging site"
entry in STATUS.md at the end.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible. Nothing here touches data/ or the master store; use
`.venv-w3` (export UV_PROJECT_ENVIRONMENT=.venv-w3). The operator merges; you
push and hand over. The VPS: nothing runs there without the operator's explicit
yes for the exact command shown, and every command you run there is one of this
phase's own scripts, the §9 block, or a one-line read-only check. Never edit a
file on the box by hand: a fix goes into the kit, on a branch. Branch:
`deploy-staging`, created from main.

## What exists on the box (from the runbook; verify the few facts Task 0 names)
A 2 vCPU / 4 GB Hetzner VPS. The app: system user `leibniz`, checkout
/opt/leibniz-legible with its own .venv made by uv with
UV_CACHE_DIR=/opt/leibniz-legible/.uv/cache and
UV_PYTHON_INSTALL_DIR=/opt/leibniz-legible/.uv/python; unit
leibniz-legible.service (hardened sandbox; WorkingDirectory the checkout;
EnvironmentFile /etc/leibniz-legible/env; ExecStart .venv/bin/leibniz serve;
ReadWritePaths /var/lib/leibniz-legible), listening on 127.0.0.1:8000 with two
workers. The serving store /var/lib/leibniz-legible/inventory.sqlite is a
rollback-journal copy the app opens read-only. Meilisearch on 127.0.0.1:7700,
master key in /etc/meilisearch/env (root:meilisearch, 0640), a restricted
search key in the app's env (deploy/meili-search-key.sh made it; read that
script to learn which indexes the key is scoped to). The index uid is
leibniz_pages with leibniz_pages_meta beside it (search/meili.py
DEFAULT_INDEX_UID; MeiliBackend takes index_uid, but nothing sets it from the
environment yet). Caddy: /etc/caddy/Caddyfile from deploy/Caddyfile with
LEIBNIZ_DOMAIN from /etc/leibniz-legible/caddy.env, and
`import /etc/caddy/conf.d/*.caddy` at its end, present on the live box since
Calculemus (§13 item 2 says how it was added by hand); each sibling block names
its domain literally, never as a {$VAR} fallback. DNS is on Cloudflare; a host
Caddy must get a certificate for is DNS-only (grey cloud) before its block goes
live (§1, §13). Calculemus runs on 127.0.0.1:3000 under its own user. Memory
is the constraint (§13 item 4): Meilisearch relies on the page cache for its
p95.

## Task 0 — Pre-flight (report, then wait for a go)
Clean tree on main (the operator's own untracked files aside); `git pull
--ff-only origin main`; baseline ruff + pytest. Ask the operator and wait: the
SSH target; whether the DNS record `staging` (A, and AAAA if the box has IPv6)
is in place as DNS-only; the user name they want for the password prompt (the
password itself is typed on the box, never in chat). Then, with a yes, one
read-only check on the box:
    ssh <target> 'free -m; df -h /var/lib/leibniz-legible /var/lib/meilisearch /opt; systemctl is-active leibniz-legible meilisearch caddy; caddy version; tail -2 /etc/caddy/Caddyfile; ls /etc/caddy/conf.d'
Record memory and disk, the Caddy version (the directive is basic_auth from
Caddy 2.8, basicauth before) and that the import line is there. Print a plan
and wait for "go".

## Task 1 — One small code change: the index name from the environment
web/settings.py: LEIBNIZ_MEILI_INDEX (default leibniz_pages) passed to
MeiliBackend as index_uid; `leibniz serve --meili-index`; `leibniz index
build|status|query --meili-index` likewise; deploy/env.example documents it.
Tests in tests/test_web_settings.py and the search CLI tests. Nothing changes
for production: the default is the current name.

## Task 2 — The staging kit (deploy/, documented in a new runbook §14)
- deploy/leibniz-legible-staging.service: the production unit with
  WorkingDirectory=/opt/leibniz-legible-staging,
  EnvironmentFile=/etc/leibniz-legible/staging.env,
  ExecStart=/opt/leibniz-legible-staging/.venv/bin/leibniz serve, the same
  sandbox lines, the same ReadWritePaths.
- deploy/staging.env.example: the production env with LEIBNIZ_PORT=8001,
  LEIBNIZ_WORKERS=1, LEIBNIZ_BASE_URL=https://staging.leibnizlegible.com, the
  same LEIBNIZ_DB_PATH (both processes open the copy read-only), the same
  MEILI_URL and search key, LEIBNIZ_MEILI_INDEX=leibniz_pages (production's
  index, read only) with a comment on when to point it at a staging index,
  LEIBNIZ_RATE_LIMIT=0 (one reader behind a password), the same image base URL.
- deploy/staging.caddy.example: a site block for staging.leibnizlegible.com,
  named literally: basic_auth (or basicauth, per Task 0) with one user and a
  bcrypt hash placeholder; encode zstd gzip; the production headers plus
  X-Robots-Tag "noindex, nofollow"; reverse_proxy 127.0.0.1:8001; its own JSON
  access log under /var/log/caddy with roll_keep_for 168h. Installed as
  /etc/caddy/conf.d/staging.caddy. Basic auth already turns every crawler away
  with 401; the header is belt and braces.
- deploy/staging-install.sh, run once as root on the box: creates
  /opt/leibniz-legible-staging as a clone of the public repository owned by
  leibniz (https, no credentials); `uv sync --frozen --no-dev --extra web` into
  its own .venv with the shared cache and interpreter directories; installs the
  unit; installs staging.env from the example if absent, else leaves it;
  asks for the password on the terminal and writes the Caddy block with the
  hash from `caddy hash-password` (the plaintext never leaves the terminal);
  `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, then
  `systemctl reload caddy` (reload, never restart; the apex stays up; a failed
  validate changes nothing); `systemctl enable --now leibniz-legible-staging`;
  `curl -s http://127.0.0.1:8001/healthz`. Idempotent: a re-run updates in
  place and keeps the existing password unless asked.
- deploy/staging.sh <branch>, as root, any time: as leibniz,
  `git -C /opt/leibniz-legible-staging fetch origin && git checkout -B
  staging origin/<branch>`; uv sync as above; restart the staging unit;
  healthz; print https://staging.leibnizlegible.com. Options: `--main` puts
  staging back on main; `--index` builds a staging Meilisearch index named
  leibniz_pages_staging with the master key from /etc/meilisearch/env and
  points staging.env at it, for a branch that changes what the index holds
  (M1): an hour or more, double the index's disk, and the staging unit
  stopped meanwhile; the script says so and asks before building. If the
  search key is scoped to named indexes, the script widens it or makes a
  second one with the master key; read deploy/meili-search-key.sh first.
- deploy/README.md §14 "Staging site": what it is for; the one-time setup
  (the DNS record, staging-install.sh); daily use (push a branch,
  staging.sh <branch>, look, merge, §9, staging.sh --main); what is shared
  (the store copy, Meilisearch, the uv caches) and what is not (the base URL
  embedded in staging's manifests, which are never to be shared); the data
  caveat (a branch that needs a new serving copy, as M1 does, needs that copy
  uploaded to a second path and LEIBNIZ_DB_PATH in staging.env pointed at it:
  §2 and a 15 GB transfer); memory (one worker, about 150 MB RSS; stop the
  staging unit during an index build); the password (one user; change it by
  re-running the install script); teardown (disable the unit, remove the block,
  reload Caddy, remove the checkout).
Tests: a test reads the staging unit, env and Caddy examples beside their
production counterparts and asserts the intended differences and nothing else;
shell scripts pass `bash -n`, and shellcheck if it is installed.

## Task 3 — Record, push, hand over
STATUS.md "S1 — staging site" entry; append this prompt verbatim to PROMPTS.md
under "Follow-up phases (2026-10)". ruff + pytest. `git push -u origin
deploy-staging`; print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...deploy-staging?expand=1;
wait for "merged".

## Task 4 — Install on the box, each step with a yes
1. The production §9 update (the exact command as in W4; code only), so the
   box holds the kit and the settings change; healthz on 8000.
2. The install: `ssh -t <target> sudo /opt/leibniz-legible/deploy/staging-install.sh`,
   run by the operator in their own terminal because of the password prompt
   (print the line for them), or by you with `ssh -t` if they prefer to type
   the password into your terminal. Then your checks, read-only:
   `systemctl is-active leibniz-legible-staging`; healthz on 8001;
   `curl -sI https://staging.leibnizlegible.com/` answers 401 without
   credentials; the operator confirms the page opens with the password in
   their browser.
3. A first use: `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh main`;
   then /browse on staging matches production, and `/api/stats` on both report
   the same build.
If anything fails, say exactly what, fix it in the kit on a new branch, and
never patch anything on the box by hand.
~~~~

The session preamble of the 8 October plan, pasted before this prompt (and
before every later one of that plan):

~~~~text
SESSION PREAMBLE — read together with the phase prompt that follows; where
they differ, this preamble wins.

1. One branch. All work in this plan lives on the branch
   `claude/dazzling-hopper-uxji2x`, with one open pull request against main.
   Do not create the branch the prompt names. Start with
   `git fetch origin claude/dazzling-hopper-uxji2x && git checkout claude/dazzling-hopper-uxji2x && git pull`,
   commit there, `git push -u origin claude/dazzling-hopper-uxji2x`. The operator gives you
   permission to push to that branch. If this is a cloud session with a
   designated branch of its own, say so once, ask the operator to confirm,
   then proceed on `claude/dazzling-hopper-uxji2x`.

2. No merge, no production deploy, nothing sent. Replace every "wait for
   merged", "§9 update", "verify live" and "deploy" step of the prompt with:
   push the branch; print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh claude/dazzling-hopper-uxji2x`
   (once the staging kit of step S1 exists on the box); run the live checks
   against https://staging.leibnizlegible.com with the operator's password,
   or against a local server on a spare port. The live site changes only at
   the operator's final merge. Emails: you draft, the operator sends.

3. Shared memory. Read STATUS.md first: "Current state", the entries "C2b"
   and "P1", "Open questions" 18 and "Next". Prepend your phase entry to the
   Phase log and Current state as the prompt says, and append the prompt to
   PROMPTS.md under "Follow-up phases (2026-10)". Record in "Divergences"
   where you departed from the prompt, this preamble included.

4. Where you run. If this checkout has no data/inventory.sqlite (a cloud
   session), build and test on fixtures and hand every store, GPU and VPS
   step to the operator as exact commands with the expected output, as the
   C2b and P1 sessions did; the operator pastes the console back. If it has
   the store (the WSL desktop), run them yourself under the prompt's rules:
   the store read-only, a go before long jobs, downloads over a gigabyte and
   any install. The side environment is .venv-w3 on the desktop; in the cloud
   make your own (.venv-cloud, with the web, gt and release extras).

5. Numbers. Never write a number you did not produce. The committed reports
   (reports/gt-audit.md, reports/gt-audit/reach.md, reports/philiumm/*.md)
   carry the ones produced so far.
~~~~


### Phase W4 — Text access (run 2026-10-08)

_Run in a cloud session under the 8 October plan's session preamble, in its
evening revision (below the prompt): one branch (`claude/dazzling-hopper-uxji2x`,
not `web-text-access`), no wait for "merged", Task 5 replaced by the staging
site; the browser checks ran against the fixture store, the staging checks are
handed to the operator. The departures are in `STATUS.md`, Divergences._

~~~~text
Phase W4 — Text access: a copyable text panel on the page view, the text of a
catalogue piece across its folios, and downloads where readers look. One local
session on the operator's desktop (WSL2 Ubuntu); pre-flight, build, verify on
the real store, hand over, deploy, verify live.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md. If this prompt conflicts with the repo, the repo + STATUS.md
win; record the divergence in STATUS.md. This phase is W4: W1 (overlay toggle,
text export), W2 (search operators) and W3 (the browse index, then the
versioned-modules fix) exist in STATUS.md. Do not reuse their labels.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible. data/inventory.sqlite is the MASTER store (16 GB):
open it read-only only (`uv run leibniz …` opens it mode=ro); never write,
VACUUM or move it; never delete anything under data/. `.venv` is the pipeline
environment (never run `uv sync` against it); use `.venv-w3` (export
UV_PROJECT_ENVIRONMENT=.venv-w3 for every `uv` command). Long-running checks
run against a local server on a spare port. The operator merges; you push and
hand over; you never merge. The VPS: nothing runs there without the operator's
explicit yes for the exact command shown, and nothing but the §9 "Update the
app" block from deploy/README.md. Email: you draft; the operator sends.
Branch: `web-text-access`, created from main.

## Task 0 — Pre-flight (report, then wait for a go)
1. `git status --porcelain` shows nothing but the operator's own untracked
   files; HEAD is main; `git pull --ff-only origin main`; confirm the remote.
2. `node --version` (Playwright; if absent, the browser checks are the
   operator's, by the checklist you print). Baseline: `uv run ruff check .`,
   `uv run ruff format --check .`, `uv run pytest -q`; record the counts.
3. Look at the live page before changing anything: in headless Chromium (or
   by asking the operator to try in their browser) open
   https://leibnizlegible.com/page/00068221:0043, select text in the line panel
   and read the selection; read static/style.css for user-select rules and
   views/page.js for click handlers that cancel selection. Record what a reader
   can and cannot select today.
4. Print a short plan and wait for "go".

## Context
David Rabouin (PHILIUMM, 2026-10-07): "I think it would be very useful for your
reader to have access to a text version of the all page in which an expression
occurs. As it stands, one cannot copy the transcription and one can imagine
that a student or a colleague would like to quote the whole passage in which
an expression occurs." W1 (2026-10-02) added GET /api/pages/{id}/text and
/api/works/{id}/text, plain text with a `# ` provenance header (and ?format=tsv),
linked as "Download text" on the page and work views. A whole passage, however,
is a catalogue piece (a letter, a draft) that spans folios, and nothing serves
that; and a reader who wants to quote selects text on the page rather than
downloading a file.
The web layer is src/leibniz/web/: api.py (create_app; _page_text and
_work_text render the plain-text format; _ssr_page carries the machine text for
crawlers; _katalog_for_work returns a work's catalogue records with sender,
addressee, date, aa_labels and shelfmarks), static/views/page.js and work.js,
static/i18n.js (EN and DE), static/api.js. Since W3's fix the shell loads the
viewer's modules from /static/m/<build>/, hashed as a set, so a changed module
reaches returning readers at once; nothing to do for that. The piece→canvas
resolver is src/leibniz/align/resolve.py: resolve_piece(conn, work_id,
signature) places a catalogue record's shelfmark with a Bl. range onto canvases
(pages.label holds folio labels); C2 localized 11,595 pieces with it. The
fixture store (tests/conftest.py) has record k-109 on work 00068642 with
shelfmark "LH IV, 6, 18 Bl. 1-2", which resolves to two of its three pages.

## Task 1 — The text panel on the page view
Under the line panel (or as a tab beside it), a "Text" section showing the
page's recognised lines as one block of selectable text in reading order, one
line per line, with a Copy button (navigator.clipboard.writeText inside the
click handler; on rejection select the block and say so) and the existing
per-page download beside it, named plainly ("Download this page as text" /
"Diese Seite als Text herunterladen"). Status and confidence stay with the
line panel; the block carries one line of provenance above it (model, run date,
the wording rule from attribution.py). If Task 0 found that selection in the
line panel is blocked, unblock it as well. EN and DE; keyboard reachable; the
server-rendered page keeps carrying the text for crawlers.

## Task 2 — The text of a catalogue piece
GET /api/records/{record_id}/text: for a catalogue record linked to a work
whose shelfmark the resolver can place, the lines of those canvases in order,
in the W1 plain-text format with a header naming the record (title, date,
sender and addressee, AA reference where known), the work, the folio range and
the canvases; ?format=tsv as for W1; 404 for an unknown record; for a record
that cannot be placed, a 404 whose detail says so (document it in the OpenAPI
summary). On the work page, every catalogue record that can be placed gets a
link "Text of this piece (Bl. 1–2)" / "Text dieses Stücks (Bl. 1–2)"; the API's
records carry `text_url` only where it resolves. robots.txt: Allow
/api/records/. llms.txt and the README document it. Tests on the fixture store:
k-109 resolves and streams two pages; a record without a folio range answers
404 with the reason; TSV; robots.

## Task 3 — Downloads where readers look
On the page view and the work view, the download links move from the link list
into the text panel's toolbar (the work view keeps "Download the text of this
work"). The About page's section on the text says that text is available per
page, per work and per catalogue piece.

## Task 4 — Verify against the real store, record, hand over
Tests; ruff. `uv run leibniz serve --backend none --port 8765` on the master
store (read-only; search answers 503 by design). Over HTTP: a page with text;
a record text for a work with placed records (find one through /api/works);
a record that cannot be placed; TSV; robots; llms. In a browser (Playwright
from npm in scratchpad/pw if Node is present, plain chromium.launch(); else
the operator by your checklist at http://127.0.0.1:8765): select and copy on
the panel, the piece link from a work page, EN and DE, phone width (390 px,
no horizontal scroll), no console errors, axe-core zero violations. Stop the
server. STATUS.md: a "W4" entry (Current state, Phase log, Key numbers, Next)
including what Task 0 found about selection. Append this prompt verbatim to
PROMPTS.md under "Follow-up phases (2026-10)". Commit in sensible pieces,
`git push -u origin web-text-access`, print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...web-text-access?expand=1,
and ask the operator to say "merged". Wait.

## Task 5 — Deploy, only after "merged", only with a yes
Ask for the SSH target and whether to run the deploy from this session. Show
the exact command first and run it only on an explicit yes; it is the §9 block
and nothing else (the remote shell is bash; if the login user is not root,
prefix systemctl with sudo):

    ssh <target> "sudo -u leibniz -H git -C /opt/leibniz-legible pull --ff-only && sudo -u leibniz -H env UV_CACHE_DIR=/opt/leibniz-legible/.uv/cache UV_PYTHON_INSTALL_DIR=/opt/leibniz-legible/.uv/python uv sync --project /opt/leibniz-legible --frozen --no-dev --extra web && systemctl restart leibniz-legible && sleep 2 && curl -s http://127.0.0.1:8000/healthz"

Code only: no index rebuild, no Meilisearch restart. Then verify live over
HTTP: a page view's server-rendered text, a record text URL, robots.txt with
the new Allow line, llms.txt. Ask the operator to open a page view in the
browser they used before the deploy, without a hard reload, and confirm the
panel and the Copy button work (the versioned-modules fix is what makes this
safe; say so if anything looks stale). If anything fails live, say exactly
what, propose the fix as a new branch, and do not patch anything on the
server.

## Task 6 — Three sentences for the operator's reply to David
In scratchpad/david-text-access.md and in chat: the page text panel with Copy,
the text of a catalogue piece across its folios from the work page, and that
per-page and per-work downloads have existed since 2 October. No numbers you
did not measure. Do not send anything.
~~~~

The session preamble of the 8 October plan, in the revision given to this
session (the S1 entry above carries the earlier wording):

~~~~text
SESSION PREAMBLE — read together with the phase prompt that follows; where
they differ, this preamble wins.

1. One branch. All work in this plan lives on the branch
   `claude/dazzling-hopper-uxji2x`, with one open pull request against main.
   Do not create the branch the prompt names. Start with
   `git fetch origin claude/dazzling-hopper-uxji2x && git checkout claude/dazzling-hopper-uxji2x && git pull`,
   commit there, `git push -u origin claude/dazzling-hopper-uxji2x`. The operator gives you
   permission to push to that branch. If this is a cloud session with a
   designated branch of its own, say so once, ask the operator to confirm,
   then proceed on `claude/dazzling-hopper-uxji2x`.

2. No merge, no production deploy, nothing sent. Replace every "wait for
   merged", "§9 update", "verify live" and "deploy" step of the prompt with:
   push the branch; print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible-staging/deploy/staging.sh claude/dazzling-hopper-uxji2x`
   (the staging site of step S1 exists; until the final merge the script
   runs from the staging checkout, afterwards from
   /opt/leibniz-legible/deploy/staging.sh). The operator runs that line and
   pastes the output. Then the checks against
   https://staging.leibnizlegible.com: without credentials it answers 401 to
   everything, which is the one check you can run yourself; the rest you
   hand the operator as `curl -su USER …` lines to run and paste back. The
   password never reaches you; the SSH target and the user name are on the
   operator's plan page, not in the repo, so never write them into STATUS.md
   or PROMPTS.md. Checks that need no box can run against a local server on
   a spare port. The live site changes only at the operator's final merge.
   Emails: you draft, the operator sends.

3. Shared memory. Read STATUS.md first: "Current state", the entries "S1",
   "C2b" and "P1", "Open questions" 18 and "Next". Prepend your phase entry to the
   Phase log and Current state as the prompt says, and append the prompt to
   PROMPTS.md under "Follow-up phases (2026-10)". Record in "Divergences"
   where you departed from the prompt, this preamble included.

4. Where you run. If this checkout has no data/inventory.sqlite (a cloud
   session), build and test on fixtures and hand every store, GPU and VPS
   step to the operator as exact commands with the expected output, as the
   C2b and P1 sessions did; the operator pastes the console back. If it has
   the store (the WSL desktop), run them yourself under the prompt's rules:
   the store read-only, a go before long jobs, downloads over a gigabyte and
   any install. The side environment is .venv-w3 on the desktop; in the cloud
   make your own (.venv-cloud, with the web, gt and release extras).

5. Numbers. Never write a number you did not produce. The committed reports
   (reports/gt-audit.md, reports/gt-audit/reach.md, reports/philiumm/*.md)
   carry the ones produced so far.
~~~~

### Phase K1 — Kurrent track (run 2026-10-09)

_Run on the operator's desktop — the WSL checkout, driven from a Claude Code
session that opened in the stale Windows clone — under the 8 October plan's
session preamble in the revision given to this session (below the prompt): one
branch (`claude/dazzling-hopper-uxji2x`, not `kurrent-k1`), nothing deployed,
the operator's "go" waited for after Task 0 as the prompt says. The departures
are in `STATUS.md`, Divergences._

~~~~text
Phase K1 — Kurrent track: German census, aligner noise tolerance, bootstrap readers.
One local session on the operator's desktop (WSL2 Ubuntu), with the data, the
store and the GPU at hand.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md. If this prompt conflicts with the repo, the repo + STATUS.md
win; record the divergence in STATUS.md. Write the "K1 — Kurrent track" entry in
STATUS.md after every task, not only at the end, so a fresh session can take
over at any checkpoint. If STATUS.md already carries a K1 entry, continue from
its first unfinished task on the existing branch.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible, the one the C1 corpus run, the C2 mint and W3 used.
Facts, to verify in Task 0 rather than assume:
- data/inventory.sqlite is the MASTER store (16 GB: 13.5M v1 lines, 297k
  gt_lines). Open it read-only only: `uv run leibniz …` commands open it
  mode=ro; your own Python uses a `file:…?mode=ro` URI. Never write to it, never
  VACUUM or move it, never delete anything under data/.
- The page-image cache is /mnt/d/leibniz-images (the D: drive); the runbooks
  pass it as `--images /mnt/d/leibniz-images`, and pages.local_path is relative
  to that root (see align/audit.py attach_images).
- data/gt/edition_cache.jsonl is the C2 edition cache (10,029 records).
- `.venv` is the pipeline environment (kraken, torch with CUDA): never run
  `uv sync` against it and never install into it. `.venv-w3` is the side
  environment W3 made (web, gt, release extras). This phase gets its own:
  after Task 1 adds the `kurrent` extra, create it with
  `UV_PROJECT_ENVIRONMENT=.venv-k1 uv sync --extra bench --extra gt --extra kurrent`
  and run everything in this phase with `UV_PROJECT_ENVIRONMENT=.venv-k1`
  exported in your shell. Check that .gitignore already ignores side
  environments (W3 added a rule); if `.venv-k1/` would show in `git status`,
  add it to the same rule.
- The GPU is a GTX 1660 Ti (6 GB) reachable from WSL2 (the C1 recogniser ran on
  it). Verify in the new environment with
  `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"`
  before any GPU step; if it prints False, say so and run on CPU with --sample.
- Long jobs run under nohup with a log under logs/ (gitignored), and you poll
  the log rather than block; print the tail when done. Ask the operator for a
  go before: a download over 1 GB, a job expected to run over an hour,
  installing any software (apt, winget, npm), and launching Plan B's training.
- Every result lives in reports/kurrent/ as small committed files (Markdown,
  JSON, CSV of at most a few thousand rows), rendered by code from data, prose
  templated. Bulky artefacts (model weights, datasets, crops, HTML pages, full
  CSVs, the pilot readings) go under data/ (gitignored) and are described, not
  committed. Never write a number you did not produce.
- This phase writes nothing to the store: not to gt_lines, not to lines, not
  to runs. Every reading a candidate model produces lives in JSON under
  data/kurrent/. The reason: the recognise stage (pipeline/recognize.py →
  db.set_line_recognition) UPDATES each line's existing row in place, and every
  reader of the store (the viewer, the index, the text and release exports, the
  audit crops) takes the highest run id per line as the current text; a second
  reader's rows would overwrite or shadow the v1 reading. Versioned line rows
  are a C4 decision (STATUS.md, Divergences), not this phase's.
- New Python dependencies (transformers for TrOCR) go in a new optional extra
  `kurrent` under [project.optional-dependencies] in pyproject.toml, next to the
  existing `bench` extra (which already carries kraken and therefore torch).
  Lock with `uv lock`; pin transformers to a release whose torch requirement the
  already-locked torch satisfies, and never bump torch. Imports stay lazy so
  the tests run without the extra.
- The operator merges. You push the branch and hand over; you never merge.
  Nothing is deployed in this phase. Branch: `kurrent-k1`, created from main.

## Task 0 — Pre-flight (report, then wait for a go)
1. `git status --porcelain` shows nothing but the operator's own untracked
   files (logs, *.log, resume-run.sh, .python-version, reports/gt-audit/
   gt-audit.html and the like; leave them alone). `git rev-parse --abbrev-ref
   HEAD` is main; `git pull --ff-only origin main`; confirm the remote.
2. `nvidia-smi` (driver, VRAM, nothing else running on the GPU); `df -h data
   /mnt/d`; `uv --version`; whether data/external/kurrent-trace/Kurrent-Trace-v0.1/
   exists with data/published_gt.jsonl, images/lines/dresden1673/ and labels/
   dresden1673/ (if not, ask the operator for the zip path or Drive id and run
   tools/fetch-kurrent-trace.sh; it verifies the checksum and runs the
   package's validator).
3. Baseline in .venv-w3 for now: `uv run ruff check .`, `uv run ruff format
   --check .`, `uv run pytest -q`. Record the counts.
4. Print a short plan with the steps you expect, their durations and what
   needs a go, and wait for the operator's "go".

## Background (all you need)
About 15 % of the Nachlass is German, written in Kurrent. The HTR model this
project runs (PHILIUMM's FoNDUE-GD_v2_ft_Leibniz) knows Latin and French and
reads Kurrent as noise. No Leibniz German ground truth exists anywhere; PHILIUMM
confirmed by email (David Rabouin, 2026-09-29) that they have none and that their
project barely touched the German correspondence, and on 2026-10-07 he added
that their model "was not trained for Kurrentschrift either and we might expect
very bad result on this corpus". Vision language models are assumed out (SPECS
§1.6 records 70–80 % CER zero-shot on Kurrent); Task 3 may measure that on
Dresden if an API key is set in the operator's environment.
The route is the project's own retro-alignment factory. Reihe I of the Academy
edition is the general correspondence, a large share German, and its §70-expired
volumes are in the edition cache where a free copy exists (I,3, I,6 to I,12 and
I,14 to I,16; I,1, I,2, I,4, I,5 and I,13 have none). The C2 factory minted
158,570 open-bucket lines from the Reihe I volumes (the sum of the Reihe I rows
in reports/gt-factory.md), all aligned against the Latin and French model's
machine text, so the hypothesis is that German lines were declined, not minted,
and the German ground truth is still unmade in pieces the factory has already
localized. What unlocks it is a bootstrap reader that reads Kurrent at all. This
phase measures and prepares; it runs no corpus job. Phase K2 will run the
factory on German pieces with the reader this phase selects; K3 will fine-tune
on what K2 mints.
Candidate readers already exist (all verified reachable on 2026-10-05); test
them before training anything:
- dh-unibe/trocr-kurrent-XVI-XVII (Hugging Face): TrOCR line model, MIT licence,
  German Kurrent 16th–18th century, model.safetensors 1.34 GB; the model card
  reports test CER 5.4 % on held-out lines of the same hands, Swiss-biased data,
  and states that it reads one line image per call. Fine-tuned from
  dh-unibe/trocr-kurrent (19th century, MIT), which may be run for reference.
- fgho/trocr-hanseXVII-kurrent and fgho/trocr-hanseXVI-kurrent: TrOCR, fine-tuned
  from the Bern model on 17th and 16th century north German administrative
  records. No licence stated on the Hub: evaluate only, never build on them
  unless a licence appears; say so in the report.
- McCATMuS (Zenodo 10.5281/zenodo.13788177): Kraken model, CC BY 4.0, 22 datasets,
  mostly French with some German, 16th–21st century. It ships as
  McCATMuS_nfd_nofix_V1.mlmodel (CoreML, 16 MB), not a safetensors container.
  KrakenEngine (src/leibniz/htr/engines.py) loads through
  kraken.models.loaders.load_models, adopted in B1 for the safetensors model; if
  that refuses the CoreML file, add the legacy path (kraken's load_any) behind
  the same engine class. Do a one-line load check before any long run.
- PHILIUMM's own model as the baseline, expected to fail on Kurrent. Its
  weights are already under data/models/ from B1 (check; else `uv run leibniz
  bench fetch`).
TrOCR models read ONE LINE IMAGE per call; this project stores line geometry for
every page, so crops come from the store through the crop machinery in
src/leibniz/align/audit.py (line_geometry, crop_box, crop_line).
Kurrent smoke-test data (a chancery hand, not Leibniz's, but the closest period in
public): Stefan Beckert's Dresdner Hofdiarium ground truth, Zenodo
10.5281/zenodo.15303243 (1673, Mscr.Dresd.K.117: a JPG and a per-leaf ALTO XML
per page), 10.5281/zenodo.15303398 (1653–56, K.113: the same layout plus a METS
file), 10.5281/zenodo.14356190 (1665, K.80: one zip). Zenodo's licence field says
CC BY 4.0 on all three; the 1673 README says CC BY-NC-SA 4.0; until the author
resolves that, the Dresden text is nc bucket: internal evaluation only. The
Kurrent Trace package (fetched by tools/fetch-kurrent-trace.sh) holds 383
pixel-exact line crops under images/lines/dresden1673/*.png, labels under
labels/dresden1673/*.gt.txt (crops and labels in separate trees, so the
image-plus-sidecar loader in htr/data.py will not pair them), the records in
data/published_gt.jsonl (read this file), and a scripts/ directory whose
validator the fetch script runs; check what scorer it ships before relying on
one. Use the package if present, else cut crops from the Zenodo ALTO polygons.
Plan B training data, only if no candidate reader is usable: the Bullinger HTR
dataset (github.com/pstroe/bullinger-htr, Git LFS, about an hour to clone,
165,673 line PNG + TXT pairs, folders `de` and `la` split by langid, 16th century,
CC BY-SA 4.0; note the ShareAlike question for a released model in the lawyer-memo
list) plus the Dresden sets.
Everything fetched from outside lives under data/. Record every source's licence.

## Task 1 — Aligner noise tolerance (needs no data; do this first)
The B2 harness (src/leibniz/align/evaluate.py) measures the aligner on the
PHILIUMM validation split with real HTR text and can perturb the edition side
(build_reference's char_perturb). reports/philiumm-repro.lines.jsonl holds ref
and hyp for all 1,878 lines, in val order, at about 8 % CER; the strings are
normalised under the philiumm policy (NFD, whitespace collapsed), which is fine
for this purpose. Build pieces of 25 consecutive lines from that file in file
order (GoldLine.image may be empty bytes) and pass the hyp dict in place of
run_htr_cached, so no model and no images are needed. Add an HTR-side
corruption option: substitutions, insertions and deletions applied to the
machine text to reach target CERs of 10, 20, 30, 40, 50 and 60 % against the
ref, fixed seed, a realistic confusion set rather than uniform random letters
(say what you chose: visually similar letter pairs, a dropped or doubled minim,
a merged or split word space); report the achieved CER per level. Measure yield
and precision per level at the factory's standard thresholds per stratum
(STRATUM_THRESHOLDS in src/leibniz/align/factory.py). Report the break-even: the
CER where yield drops below 50 % and where precision drops below 95 %. Write
reports/kurrent/align-tolerance.md and align-tolerance.json. Tests on fixtures.
Add the `kurrent` extra and lock it now; create .venv-k1 and switch to it; run
the suite there. Commit.

## Task 2 — German census of the edition pieces
- src/leibniz/enrich/langid.py: pure, tested stopword classifier returning
  la | fr | de | mixed | unknown with a score; handles 17th-century spellings
  (vnd, vndt, daß, seyn, sey, alß, wan, umb, auff) and returns unknown below a
  length you justify. No model, no network. The enrich package is C4's; this is
  its first module, built for clean edition text, and C4 may replace it for
  noisy HTR lines; say so in the docstring.
- `leibniz align kurrent-census`: classify every edition-cache record; join to
  pieces (src/leibniz/align/volumes.py: enumerate_pieces / PieceRef with
  record_id, work_id, signature, folio_range, textart), canvases
  (src/leibniz/align/resolve.py), v1 lines (the recognised run) and minted lines
  (gt_lines.source contains "katalog {record_id}", see align/factory.py). The
  stratum per piece comes from align/stratum.py's classify_piece over the pages'
  page_stats plus textart, exactly as the factory computes it;
  page_stats.stratum_heuristic is NULL under C1, so do not read that column.
  Also record per piece whether the catalogue's textart marks Leibniz's own
  hand (`eigh.`), since the Kurrent question is also a question of whose hand.
  Per volume and overall: pieces by language; localized pages and v1 lines on
  German pieces; minted lines and yield on German vs Latin and French pieces
  (the hypothesis test); language by Textart and by hand. Writes
  reports/kurrent/census.md, census-summary.json, census-by-volume.csv; the full
  piece list data/kurrent/german_pieces.jsonl (record_id, work_id, page_ids,
  n_lines, stratum, hand, language score) for K2, plus a committed
  reports/kurrent/german_pieces_index.csv without page lists.
Test on fixtures, then run it here (minutes, no GPU), read the results, commit
the reports. CHECKPOINT A: write the STATUS.md entry so far and commit. The
operator may stop here and resume later.

## Task 3 — Bootstrap readers, smoke test on Dresden
- A TrOCR reader class (in src/leibniz/htr/engines.py or a sibling module)
  implementing BOTH protocols: the bench harness's Engine
  (src/leibniz/htr/bench.py: transcribe over line image bytes → text) and the
  pipeline's Recognizer (src/leibniz/pipeline/recognize.py: transcribe_conf →
  text and confidence or None; version from the model id). KrakenEngine
  implements both; copy that shape. It lives behind the `kurrent` extra with an
  offline test using a stub model. Load the Kraken candidate through
  KrakenEngine (CoreML path, see Background). Model weights download to
  data/models/hf/ on first use, cache-first.
- `leibniz bench kurrent-smoke` (the HTR harness's CLI is registered as `bench`
  in src/leibniz/cli.py; do not add an `htr` group): build the Dresden test set
  (the package if present, read from data/published_gt.jsonl; else Zenodo ALTO
  → crops), run every candidate plus the PHILIUMM baseline, score with the B1
  harness under all three normalization policies, since Dresden conventions
  differ (u/v as written, long s distinguished); if the package ships a scorer,
  report its strict and reading scores too; record wall time per line and
  device. If OPENAI_API_KEY or ANTHROPIC_API_KEY is set in the environment, add
  one zero-shot vision row on a seeded 150-line subsample through the existing
  OpenAIEngine or AnthropicEngine (cents; only images are sent, never the nc
  text), skipping gracefully without a key. Writes
  reports/kurrent/bootstrap-candidates.md and .json. The report must say this is
  a ranking, not a benchmark: public data may sit in a candidate's training set.
Test on a stub, then ask for a go for the downloads (about 1.3 GB per TrOCR
model), start with the McCATMuS load check, run the smoke test here (CPU is
fine for 383 lines; use the GPU if available), read the results, commit the
reports. CHECKPOINT B: update the STATUS.md entry and commit.

## Task 4 — Pilot on Leibniz's own German, without ground truth
- The crop machinery in src/leibniz/align/audit.py must accept an explicit list
  of line refs ("{page_id}:{line_seq:03d}") and return crops. If P1 has already
  landed that refactor on main, reuse it; if not, do it here without changing
  the existing sheet's behaviour or tests.
- `leibniz align kurrent-pilot`: from data/kurrent/german_pieces.jsonl pick 20
  German pieces across volumes, strata and hands with resolved canvases, plus 5
  Latin or French control pieces; cap pages, with --sample for slow devices.
  For each candidate that scored reasonably in Task 3 (define the cut in the
  report; well below the PHILIUMM baseline's Dresden CER is the obvious one),
  plus the PHILIUMM baseline, read those pages' lines from the stored v1
  geometry (crops from /mnt/d/leibniz-images through the crop machinery) and
  write the readings to data/kurrent/pilot-readings/<reader>.jsonl, one row
  per line (line_id, text, conf, model, device, ms), resumable. Nothing goes
  into the store; the pipeline's recognise stage is not used. Then run the
  factory's alignment per piece per reader as a DRY RUN, building the HtrLine
  lists from those JSONL files: yield and mean confidence at the standard
  per-stratum thresholds, nothing written to gt_lines. The aligner's confidence
  is a similarity to the edition text, so German yield is a ground-truth-free
  measure of how well each reader reads Leibniz's German. The control pieces
  must show the opposite ordering, PHILIUMM winning; if not, the method is
  broken and the report says so.
- Also render data/kurrent/pilot-side-by-side.html: 30 German line crops with
  every reader's text, for the operator to eyeball; ask the operator to say
  whether any reader produces German words, and record the answer verbatim.
- Writes reports/kurrent/pilot.md, pilot-yield.csv, pilot-summary.json with the
  verdict: which reader K2 should use and the expected German yield.
Test on fixtures, ask for a go (GPU strongly preferred; hours on CPU with
--sample), run it under nohup with a log, read the results and the operator's
verdict, commit. CHECKPOINT C: update the STATUS.md entry and commit.

## Task 5 — Plan B, only if no reader clears the Task 1 break-even in Task 4
Build fetch and conversion commands for Bullinger (folder de plus a la sample)
and the three Dresden sets into Kraken training format under data/external/,
record licences, write a ketos fine-tuning config from the PHILIUMM checkpoint
with the codec resized to admit ß, umlauts and long s, and a runbook. Fetch and
convert only with a go; training is launched only if the GPU is available and
the operator confirms, as a background job with a log. Skip this task entirely
if Task 4 found a usable reader.

## Finish and hand-over
Complete STATUS.md's "K1 — Kurrent track" entry: what was built, key numbers
(German pieces, pages and lines; German vs Latin-French minted yield; break-even
CER; Dresden CER per candidate; pilot yield per reader), licences recorded, open
questions, and a gate verdict for K2: GO with a named reader and expected yield,
or NO-GO with the reason. Append this prompt verbatim to PROMPTS.md under
"Follow-up phases (2026-10)". ruff + pytest clean in .venv-k1, all tests
offline. Commit in sensible pieces and `git push -u origin kurrent-k1`. Then
hand over: print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...kurrent-k1?expand=1,
tell the operator what to read in the diff (the gate verdict, the census
numbers, the licences table), remind them that data/kurrent/ holds K2's input
and the pilot evidence and must be kept, and that nothing is deployed. Do not
merge.
~~~~

The session preamble of the 8 October plan, in the revision given to this
session (against the W4 entry's wording it names "W4" among the entries to
read and adds point 6, the go):

~~~~text
SESSION PREAMBLE — read together with the phase prompt that follows; where
they differ, this preamble wins.

1. One branch. All work in this plan lives on the branch
   `claude/dazzling-hopper-uxji2x`, with one open pull request against main.
   Do not create the branch the prompt names. Start with
   `git fetch origin claude/dazzling-hopper-uxji2x && git checkout claude/dazzling-hopper-uxji2x && git pull`,
   commit there, `git push -u origin claude/dazzling-hopper-uxji2x`. The operator gives you
   permission to push to that branch. If this is a cloud session with a
   designated branch of its own, say so once, ask the operator to confirm,
   then proceed on `claude/dazzling-hopper-uxji2x`.

2. No merge, no production deploy, nothing sent. Replace every "wait for
   merged", "§9 update", "verify live" and "deploy" step of the prompt with:
   push the branch; print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible-staging/deploy/staging.sh claude/dazzling-hopper-uxji2x`
   (the staging site of step S1 exists; until the final merge the script
   runs from the staging checkout, afterwards from
   /opt/leibniz-legible/deploy/staging.sh). The operator runs that line and
   pastes the output. Then the checks against
   https://staging.leibnizlegible.com: without credentials it answers 401 to
   everything, which is the one check you can run yourself; the rest you
   hand the operator as `curl -su USER …` lines to run and paste back. The
   password never reaches you; the SSH target and the user name are on the
   operator's plan page, not in the repo, so never write them into STATUS.md
   or PROMPTS.md. Checks that need no box can run against a local server on
   a spare port. The live site changes only at the operator's final merge.
   Emails: you draft, the operator sends.

3. Shared memory. Read STATUS.md first: "Current state", the entries "W4",
   "S1", "C2b" and "P1", "Open questions" 18 and "Next". Prepend your phase entry to the
   Phase log and Current state as the prompt says, and append the prompt to
   PROMPTS.md under "Follow-up phases (2026-10)". Record in "Divergences"
   where you departed from the prompt, this preamble included.

4. Where you run. If this checkout has no data/inventory.sqlite (a cloud
   session), build and test on fixtures and hand every store, GPU and VPS
   step to the operator as exact commands with the expected output, as the
   C2b and P1 sessions did; the operator pastes the console back. If it has
   the store (the WSL desktop), run them yourself under the prompt's rules:
   the store read-only, a go before long jobs, downloads over a gigabyte and
   any install. The side environment is .venv-w3 on the desktop; in the cloud
   make your own (.venv-cloud, with the web, gt and release extras).

5. Numbers. Never write a number you did not produce. The committed reports
   (reports/gt-audit.md, reports/gt-audit/reach.md, reports/philiumm/*.md)
   carry the ones produced so far.

6. A go. Where the prompt says to print a plan and wait for "go", a cloud
   session that was started with the whole step as its task does not wait
   (nobody answers mid-task): it records the pre-flight in STATUS.md,
   proceeds, and notes the departure under Divergences. The operator's yes
   is still needed for anything on the box or the store, which a cloud
   session hands over anyway. A desktop session waits as the prompt says.
~~~~
