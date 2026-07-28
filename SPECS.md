# Leibniz Legible — Project Specification

_Working title `leibniz-legible`; rename at will. v0.1, 2026-07-28._
_Destined for its own repository. This document is the project's law; `PROMPTS.md` is its build plan; `STATUS.md` (created in Phase 0) is its living state._

**Mission.** Every page of the digitized Leibniz Nachlass — ~50,000 pieces on ~100,000 sheets (~200,000 page images) held by the Gottfried Wilhelm Leibniz Bibliothek (GWLB), Hannover — machine-transcribed with per-line confidence and provenance, full-text searchable with typo tolerance, and browsable in an open IIIF viewer cross-linked to the scholarly catalogue. Shipped as open datasets, open model weights, a public benchmark, and one modest web application. Target: **usable public release by late 2027**.

**Posture.** This is an _access layer_: Vorausedition-grade, explicitly subordinate to the Akademie-Ausgabe (AA). It is machine output with honest labels, never "an edition." Roughly 75% of the Nachlass has never been printed in any form; making it _legible and findable_ is the deliverable. The register toward the institutions (GWLB, the four Arbeitsstellen, BBAW / Akademie der Wissenschaften zu Göttingen) is supplier and admirer, never competitor. When in doubt, the project under-claims.

---

## 1. Ground truth about the ground truth

Everything below was verified against primary sources in July 2026. Re-verify anything load-bearing before relying on it (things drift; LeibnizCentral, for instance, is already dead).

### 1.1 Images: done, open, machine-accessible

- The entire Hannover Nachlass was digitized 2016–2019 and is online at **https://digitale-sammlungen.gwlb.de/** (Kitodo.Presentation).
- **OAI-PMH endpoint** (verified live): `https://digitale-sammlungen.gwlb.de/oai2/` — METS/MODS. Relevant sets and record counts (records are works/convolutes, not pages): `LeibnizHandschriften` (756), `LeibnizBriefwechsel` (1,060 — matches Bodemann's 1,063 LBr correspondent numbers, i.e. essentially complete), `LeibnizMarginalien` (396), `Leibnitiana` (1,823), `leibniz-rekonstruktionen` (fragment-reconstruction results).
- **IIIF**: Presentation API 2.0 manifests at `https://digitale-sammlungen.gwlb.de/content/{8-digit-id}/manifest.json`; images via IIIF Image API 2 level1 from pyramid TIFFs (`…/iiif/{id}/ptif/…`). Sample canvas ≈ 2008×2561 px for a quarto — ~300 dpi class. Adequate for line HTR; marginal for tiny interlinear insertions.
- **Rights**: manuscript scans **Public Domain Mark 1.0**; metadata **CC0 1.0** (GWLB Open-Digitisation-Policy, 2019). §68 UrhG (+ BGH _Bibelreproduktion_) means no related rights subsist in the scans. **Higher-resolution master TIFFs are free for scientific projects on request**: digitalisierung@gwlb.de.
- Not covered: non-Hannover holdings (Landesarchiv Hannover, Wolfenbüttel, Gotha, Berlin, Paris, Warsaw, London, Basel, Florence — a few percent of the corpus) and the consortium-held transmitted-light fragment scans (MusterFabrik/Fraunhofer). Both are out of scope for Tier 1.

### 1.2 Catalogue: the join table exists

- **Ritter-Katalog / Arbeitskatalog der Leibniz-Edition**: https://leibniz-katalog.bbaw.de/ — **>70,200 records**, the metadata spine of the whole field. Covers nearly all known writings and letters; filters for date, correspondent, shelfmark (LH/LBr signature), AA volume/piece number, other prints; links out to GWLB scans; includes rough transcriptions of >5,000 short notes. **License CC BY 4.0** (covers database rights). **No public API** — scrape politely or request a dump from TELOTA (BBAW's DH department, which runs it).
- Auxiliary: Leibniz-Connection (persons/correspondence DB, https://leibniz-connection.adw-goe.de/); Bodemann's catalogues (1889 LBr / 1895 LH) define the shelfmark system.

### 1.3 HTR: a foundation shipped in July 2026 (build on it, verify it first)

All from the ERC project **PHILIUMM** (Paris, PI David Rabouin; grant ended 2026 — the team is a partnership opportunity):

- **HTR model for Leibniz's hand**: Zenodo DOI `10.5281/zenodo.21457538`, CC BY 4.0, Kraken/eScriptorium stack (FoNDUE-GD base), **self-reported CER 8.33%** (WER 28.56%) on a Leibniz validation set, vs 15.04% base. Latin + French only.
- **Ground truth**: HuggingFace `DenisaB/htr_leibniz_dataset_v1`, CC BY 4.0, ~63k lines (train_clean 18,254 / train_noisy 43,372 / val 1,878), image+text pairs. (A Zenodo twin DOI 404'd at research time.)
- **Segmentation**: Kraken baseline-segmentation model, Zenodo `10.5281/zenodo.21537859` (274 pp, 20,217 baselines, SegmOnto zones), CC BY 4.0; plus HF `DenisaB/rfdetr-segmentation-leibniz-dataset` (COCO instance segmentation: text/graphic/formula zones).
- **Math expressions**: HME-Leibniz, Zenodo `10.5281/zenodo.18804566` — 4,571 cropped expressions with LaTeX. **CC BY-NC** — NC-quarantined (see §7).
- Caveats: these artifacts were days old at research time and unreplicated; CER is line-level on pre-segmented lines. **Phase B1 reproduces the numbers before anything is built on them.**

### 1.4 Text for retro-alignment: legally free and substantial

- ~50 AA volumes are free PDFs via https://www.leibnizedition.de/ and the Göttingen repository (rep.adw-goe.de, "Leibniz-Edition Digital"); Vorauseditionen exist for III,10; IV,11; VI,5; plus Reihe-I transcriptions 1708–1716.
- **§70 UrhG gives scientific editions a 25-year term** (calendar-year end). Volumes whose edited reading text is free of §70 and §71 today (published ≤2000): **Reihe I,1–16 + Harz supplement; II,1 (1926 text); III,1–4; IV,1–3; VI,1–4 + VI,6; VII,1–2** — ~34 volumes/parts, ~25–30k printed pages. New expiries every Jan 1 (2027: I,17 + IV,4; 2029: III,5 + VII,3; …).
- **Hard rule**: use only the constituted _reading text_ of expired volumes. Editor introductions, apparatus, commentary, and indices are ordinary §2 works (70 years p.m.a.) — never extract, never redistribute.
- **NC-licensed text** (usable for internal alignment/eval under §44b/§60d TDM; never redistributed in CC BY releases): GWLB Transkriptionspool (~4,000 letter transcriptions 1708–1716, per-year PDFs, CC BY-NC 4.0); Repositorium volume PDFs (CC BY-NC); Reihe VIII TEI (github.com/telota/LeibnizVIII-LaTeX_TEI, CC BY-NC).
- 19th-century editions (Gerhardt, Klopp, Dutens, Couturat, Grua, Foucher de Careil) are long public-domain and on archive.org/Google Books — bonus alignment fodder; Münster maintains concordances to AA shelfmarks.

### 1.5 External ground-truth pools (for the German/Kurrent gap and general robustness)

- **Bullinger HTR GT**: 165,673 aligned lines, ~80% Latin, 16th c. (github.com/pstroe/bullinger-htr) — the proof that alignment-minted GT works at scale (their fine-tune hit CER ~7%).
- **CATMuS** (Medieval + Modern), **HTR-United** registry (German Kurrent sets), **TRIDIS**. Pool per license terms; document provenance per line.
- Published lesson (Bullinger): multilingual training data beats monolingual on mixed Latin/German corpora.

### 1.6 What does not exist (opportunities, and honesty obligations)

- No Leibniz **German/Kurrent** GT anywhere; frontier LLMs are catastrophic on Kurrent (70–80% CER zero-shot). ~15% of the corpus is German. Report this stratum separately and honestly.
- No published **normalization-aware aligner** for edition text → diplomatic lines (closest: Transkribus Text-Image Matching; CTC forced alignment, arXiv 2508.07904; eScriptorium+Passim pipeline).
- No published **LLM benchmark on 17th-c. Latin/French secretary hands** — our benchmark harness fills it.
- No public scribe-hand census, no public watermark data (internal to Münster/Potsdam). Out of scope for Tier 1.
- GWLB's own HTR pilot targets production **October 2027** (library digitization workflow, not an edition workflow). Coordinate, don't collide: see §8.

---

## 2. Deliverables

| ID  | Deliverable                                                                                                                          | License                                | Home                 |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------- | -------------------- |
| D1  | `leibniz-inventory` — canonical page-level inventory: work ↔ shelfmark ↔ IIIF manifest ↔ canvas ↔ image URL ↔ katalog record crosswalk | CC0                                    | Zenodo + repo        |
| D2  | `leibniz-transcriptions` — full-corpus machine transcription, per-line records with confidence + provenance                            | CC BY 4.0                              | Zenodo + HF          |
| D3  | `leibniz-gt` — retro-aligned ground truth (line image + text), stratified, with per-line alignment confidence                          | CC BY 4.0 (NC-derived subset excluded) | Zenodo + HF          |
| D4  | `leibniz-htr-v2` — fine-tuned Kraken model(s) + model card with per-stratum/per-language error rates                                   | CC BY 4.0                              | Zenodo + HF          |
| D5  | `leibniz-htr-bench` — reproducible evaluation harness incl. frontier-VLM comparison                                                    | Apache-2.0                             | repo                 |
| D6  | Web app — typo-tolerant search + IIIF viewer with line overlays, confidence display, status badges, katalog/AA links                   | Apache-2.0 (code)                      | public URL           |
| D7  | IIIF Presentation 3 manifests wrapping GWLB images + W3C annotation pages carrying transcriptions                                      | CC BY 4.0                              | served by D6         |
| D8  | Reports: corpus census (first real page count), CER benchmark paper draft, alignment-yield report by stratum                           | CC BY 4.0                              | repo `/reports`      |

## 3. Success criteria (Tier 1 is done when…)

1. ≥95% (target 100%) of enumerable Hannover Leibniz pages are segmented and transcribed with the v2 model; the remainder is enumerated with reasons (blank, cover, image defect).
2. **CER ≤7% on the Latin/French validation set**; German and math strata measured and reported separately, whatever the numbers are. Per-stratum honesty is a success criterion, not a caveat.
3. Search: typo-tolerant full-text over all machine transcriptions, results grouped by piece with page hits, p95 < 500 ms, deep links into the viewer.
4. Viewer: any page reachable by shelfmark, katalog record, or search hit; images loaded from GWLB IIIF directly (**no rehosting of images**); every line shows status (`machine` / `aligned` / `corrected` / `verified`) and confidence on demand.
5. Provenance: **zero unlabeled text anywhere** — every published line traceable to (source image URI, model+version, run date, status). This is the anti-contamination guarantee.
6. D1–D5 released with DOIs and model cards; D8 census + benchmark reports published.

## 4. Architecture

### 4.1 Shape

Batch pipeline + thin serving layer. One Python package, one CLI, one SQLite database as the canonical working store, Parquet exports as the release format, a small API + static frontend for serving.

```
harvest (OAI+IIIF) ──▶ inventory.sqlite ──▶ image cache (local, gitignored)
                                 │
katalog crosswalk ───────────────┤
                                 ▼
                    segment (Kraken, PHILIUMM seg model)
                                 ▼
                    recognize (Kraken, PHILIUMM → v2) ──▶ lines (text, conf)
                                 ▼                              ▲
                    enrich (lang-id, stratum heuristic)         │ fine-tune loop
                                 ▼                              │
                    index (Meilisearch) + IIIF v3/annotations   │
                                 ▼                              │
                    web app (FastAPI + OpenSeadragon)           │
                                                                │
GT factory: AA PDFs → reading-text extraction → piece↔scan match
            → forced alignment → leibniz-gt ────────────────────┘
```

### 4.2 Stack (chosen for one developer + LLM coding; deviate only with a note in STATUS.md)

- **Python 3.12**, `uv` for env/deps, `ruff` + `pytest`, `typer` CLI exposed as `leibniz`.
- **Kraken (v7+)** for segmentation/recognition/fine-tuning (PHILIUMM models are Kraken-stack). No Transkribus dependency (cost + lock-in); note Text-Image Matching exists there as a fallback comparison.
- **SQLite** (single file, `data/inventory.sqlite`) as canonical store; **Parquet** exports for datasets; no server DB.
- **Meilisearch** (docker) for search — typo tolerance out of the box; SQLite FTS5 as the dev fallback.
- **FastAPI** serving JSON + static frontend; **OpenSeadragon** against GWLB's IIIF Image API; vanilla TS/Vite frontend (no framework unless it earns its keep).
- **Anthropic Batch API** for bounded LLM passes (AA reading-text extraction QA, optional correction passes). LLM output is never stored without `status='corrected'` + model version.
- GPU: rented per-run (Kraken fine-tune + corpus inference ≈ 150–300 GPU-hours total).

### 4.3 Data model (canonical tables)

- `works` — gwlb_object_id (PK), set, shelfmark(s), title, mets/mods metadata (JSON), manifest_url, n_canvases.
- `pages` — work_id, seq, canvas_id, image_service_url, width, height, status (pending/segmented/recognized/skipped+reason).
- `lines` — page_id, line_seq, baseline/polygon (JSON), `text`, `conf` (0–1), `model` (name@version), `run_id`, `status` ENUM(`machine`,`aligned`,`corrected`,`verified`), `lang` (la/fr/de/mixed/unknown), source fields for non-machine statuses.
- `katalog_records` — record_id, katalog metadata (JSON), shelfmark refs, AA volume/piece refs, transcription snippet if any.
- `crosswalk` — katalog_record_id ↔ work_id (+ page range where derivable), match_method, match_conf.
- `gt_lines` — line image ref, text, source (AA volume/page | transkriptionspool | manual), stratum ENUM(`fair_copy`,`light_revision`,`heavy_revision`,`scrap`,`unknown`), align_conf, license_bucket ENUM(`open`,`nc`).
- `runs` — pipeline run bookkeeping: stage, model, params, started/finished, counts, git SHA.

### 4.4 ID scheme

Canonical page ID: `{gwlb_object_id}:{canvas_seq}` (e.g. `00068642:0007`). Canonical line ID: page ID + `:{line_seq}`. Shelfmark strings (e.g. `LH XXXV, 3, 5 Bl. 12`) are attributes, not keys — they are not unique or stable enough.

### 4.5 Provenance schema (the non-negotiable)

Every line record that leaves the pipeline carries: canonical image URI (GWLB), region coords, `model@version`, run timestamp, confidence, status, and — for `corrected`/`verified` — who/what corrected it. Dataset exports embed this per row. The web app renders status; the datasets ship it; nothing is published stripped of it.

## 5. Phases

Build order, mapped 1:1 to `PROMPTS.md`. Letters group phases; gates are go/no-go decision points.

| Phase | Name                                        | Depends on | Gate                                                       |
| ----- | ------------------------------------------- | ---------- | ---------------------------------------------------------- |
| A0    | Repo scaffold + STATUS.md                   | —          |                                                            |
| A1    | OAI/IIIF harvest → inventory + corpus census | A0         | **First real page count** published in `/reports`          |
| A2    | Image cache (resumable, polite)             | A1         |                                                            |
| A3    | Katalog crosswalk                           | A1         |                                                            |
| B1    | Benchmark harness + PHILIUMM reproduction   | A0         | **CER ≈ 8.3% reproduced?** If not, stop and reassess       |
| B2    | Retro-alignment prototype (~10 pages)       | A2, B1     | **Alignment yield acceptable on fair copies?**             |
| C1    | Corpus segmentation + HTR v1 (batch, resumable) | A2, B1  |                                                            |
| C2    | GT factory at scale (expired AA volumes)    | B2, A3     |                                                            |
| C3    | Fine-tune v2 + per-stratum eval             | C2         | **CER ≤7% la/fr?** Ship best model regardless, report honestly |
| C4    | Corpus re-run v2 + enrichment (lang-id, strata) | C1, C3 |                                                            |
| D1    | Search index + API                          | C4         |                                                            |
| D2    | Viewer web app + IIIF v3/annotations        | D1         |                                                            |
| D3    | Dataset/model releases + reports            | C4, D2     |                                                            |
| E1    | (Stretch) line-correction micro-UI          | D2         |                                                            |

Rough calendar at focused solo pace: A phases ≈ 1 month; B ≈ 1 month; C ≈ 3–5 months (GPU + alignment engineering dominate); D ≈ 2–3 months. Slack to late 2027 is deliberate.

## 6. Quality strategy

- **Strata are first-class.** Pages get a heuristic stratum label (fair copy / light revision / heavy revision / scrap) from layout statistics + katalog type; all metrics report per stratum. Aggregate numbers hide the failure mode that matters.
- **The benchmark is a deliverable.** `leibniz-htr-bench` evaluates any engine (Kraken models, frontier VLMs via API) against a held-out set with a frozen protocol. First published numbers for LLMs on 17th-c. secretary hands.
- **LLM correction is opt-in and labeled.** A correction pass may run on high-value subsets (e.g. Reihe V scraps); output is `status='corrected'`, never overwrites `machine` rows, and hallucination risk is mitigated by image-grounded prompting + disagreement flags (HTR vs LLM divergence > threshold ⇒ flag, don't auto-accept).
- **Alignment confidence gates GT.** Below-threshold aligned lines are discarded, not shipped. The alignment-yield-by-stratum report (D8) states plainly where retro-alignment fails.

## 7. Legal & etiquette rails

1. Images PDM 1.0; metadata CC0; katalog CC BY (attribute BBAW/TELOTA). Scans carry no related rights (§68 UrhG; BGH _Bibelreproduktion_).
2. §70-expired reading text only (list in §1.4; auto-grows each Jan 1). **Never** editor introductions/apparatus/commentary. Track expiry dates in code (`legal.py`), not in heads.
3. **NC quarantine**: Transkriptionspool, Repositorium PDFs, Reihe VIII TEI, HME-Leibniz are CC BY-NC. Usable internally (TDM: §44b/§60d UrhG) for alignment and evaluation; derived text goes in a `license_bucket='nc'` partition **excluded from all CC BY releases**. The public web app does not display NC-derived text.
4. **Politeness**: before any bulk pull, record `robots.txt` + any machine-readable TDM reservation in `/reports/crawl-posture.md`. Custom User-Agent with contact email. Default ≤1 req/s per host, exponential backoff, resume tokens. Cache everything; never re-crawl what's cached.
5. **Lawyer memo before first public dataset release** (checklist: §68 scan status, §70/§71 volume math, De Gruyter contract question, NC-on-monetized-surfaces question, database rights). Budget €2–5k.
6. Watch: BGH revision in Kneschke v. LAION (TDM ground rules) — pending as of mid-2026.
7. **Relationship > rights.** Where the law permits but a partner would wince, ask first. The GWLB's goodwill (master TIFFs, pilot cooperation) is worth more than any position we could litigate.

## 8. Operator actions (human, non-code — run in parallel with A/B phases)

- Email **GWLB** (digitalisierung@gwlb.de, cc Leibniz-Archiv): introduce the project as an open access layer; ask about master-TIFF terms, the 2026–27 HTR pilot's scope, and cooperation. Before C1 goes corpus-wide.
- Email **PHILIUMM** (Rabouin/Bumba): report the reproduction result (B1), note the 404 GT DOI, propose continuation/partnership. Their ERC ended 2026.
- Email **TELOTA/BBAW**: request a Ritter-Katalog dump (CC BY makes this easy to grant); scraping is the fallback, not the opener.
- Soft-contact **Michael Kempe** (Leibniz-Archiv) and the **Leibniz-Gesellschaft** with the subordinate-Vorausedition framing before anything is public.
- **Emergent Ventures** application (fast, proven channel for this profile); draft the Arcadia / VolkswagenStiftung angle for Tier 2/3 later.
- German IP lawyer memo (§7.5).

## 9. Risks

| Risk                                                                       | Mitigation                                                                                                    |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| PHILIUMM numbers don't reproduce                                            | Gate B1 before building on them; fall back to training from scratch on their GT + external pools              |
| Page-level chaos (layers, marginalia, snippets) breaks segmentation         | This is the real unsolved half; measure segmentation quality per stratum in B1/C1; RF-DETR zones as backup    |
| Retro-alignment yield collapses on revised drafts                           | Expected (30–50%); gate B2 on fair copies first; ship the honest yield report as a research contribution      |
| German Kurrent stratum stays bad                                            | Pool external Kurrent GT; report separately; flag in UI; it's ~15% of the corpus, not a Tier 1 blocker        |
| Hallucination contamination via LLM passes                                  | Provenance schema (§4.5); corrected ≠ machine; disagreement flags; never publish unlabeled text               |
| Institutional friction (perceived claim-jumping)                            | §8 contacts before public launch; Vorausedition framing; never the word "edition" for our output              |
| GWLB blocks/limits crawling                                                 | Politeness rails; the OAI/IIIF endpoints exist to be harvested; escalate to a conversation, not a workaround  |
| Solo bandwidth / burnout                                                    | Phases are independently shippable; A1's census and B1's benchmark are standalone publishable artifacts       |
| Duplication with GWLB's Oct-2027 pilot                                      | §8 email; if they ship first, our GT/bench/search/viewer remain complementary                                 |

## 10. Budget (cash, excluding the developer's time)

- Storage: 300–500 GB derivatives + workspace → local disk + one backup ≈ $0–300.
- GPU: fine-tunes + 2 corpus inference passes ≈ 150–300 GPU-hours ≈ **$300–1,000** rented.
- LLM passes: reading-text extraction QA + bounded correction subsets via Batch API ≈ **$500–3,000** depending on scope.
- Serving: small VPS + Meilisearch + domain ≈ **$20–50/month**.
- Legal memo: **€2–5k**.
- Total to public MVP: **≈ $5–10k**; comfortably inside an Emergent Ventures grant.

## 11. Out of scope (Tier 2+; resist the creep)

Aligned edition-text display in the viewer beyond GT needs; probabilistic dating model; scribe-hand classification; fragment-reassembly benchmark; watermark work; translation layer; human verification at scale (Tier 3); any Academy-of-Games integration (four thin seams documented separately — later); non-Hannover holdings; TEI critical markup. Each is a fine follow-on; none blocks "legible and searchable."
