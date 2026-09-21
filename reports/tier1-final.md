# Tier 1 — status against the success criteria (v1 public beta, 2026-09-16)

_The criterion-by-criterion summary SPECS §3 asks for, stated plainly. "Tier 1
is done when…" — it is not done; this is where it stands with the v1 model. The
file is rewritten as phases land (C3/C4 will change rows 1–2)._

| # | Criterion (SPECS §3) | State | Evidence |
| --- | --- | --- | --- |
| 1 | ≥95 % of enumerable Hannover pages segmented and transcribed **with the v2 model**; remainder enumerated with reasons | **Partly.** 99.75 % of pages transcribed with the **v1** (PHILIUMM) model — 236,210 of 236,795; 569 skips with reasons, 16 unfetchable. v2 (C3) not yet trained. | `reports/htr-v1-sample.md`, `STATUS.md` |
| 2 | CER ≤ 7 % on the Latin/French validation set; German and math strata measured and reported separately | **Not met.** v1 measures 7.95 % (95 % CI 7.49–8.46), WER 27.0 %, on 1,878 la/fr lines. German/Kurrent and mathematical strata are transcribed but unmeasured (no GT). | `reports/philiumm-repro.md` |
| 3 | Typo-tolerant full-text search over all machine transcriptions, grouped by piece with page hits, p95 < 500 ms, deep links into the viewer | **Met (measured live 2026-09-21).** On the public deployment, `leibniz index bench` over 200 queries through HTTPS: wall-clock **p50 108 ms, p95 210 ms, max 368 ms**; Meilisearch itself p50 8 ms, p95 60 ms. Typo tolerance confirmed against the index (`calculemuz` → *Calculemus*), as is the orthography fold (`calculemvs` → *Calculemus*). 235,723 pages indexed. The one shortfall is unchanged: piece-level grouping is by work + katalog AA references, not yet by piece page-range. Meilisearch (typo tolerance) or SQLite FTS5 (prefix + orthography folding); results per page with work grouping in the viewer; deep links `/page/{page_id}`. Piece-level grouping is by work + katalog AA references, not yet by piece page-range. | `src/leibniz/search/`, `leibniz index build` |
| 4 | Viewer: any page reachable by shelfmark, katalog record, or search hit; GWLB IIIF loaded directly, no rehosting; every line shows status + confidence on demand | **Built (D2); the "no rehosting" clause is diverged from by operator decision** (STATUS.md, Divergences): the public site serves its own mirror of the GWLB delivery scans, PDM 1.0, with every page linking to its original; the direct-from-GWLB mode remains the code's default. OpenSeadragon, line overlay, status badges, confidence bands, provenance per line, EN/DE. Shelfmark/AA/katalog searches resolve through the index. | `src/leibniz/web/`, `web/images.py` |
| 5 | Provenance: zero unlabeled text anywhere — every published line traceable to image URI, model+version, run date, status | **Met** in the store, the API, the annotations and the exports; enforced by the schema (§4.5). | `db.py`, `web/api.py`, `web/iiif.py`, `release/export.py` |
| 6 | D1–D5 released with DOIs and model cards; D8 census + benchmark reports published | **Partly.** D8: census, benchmark and retro-alignment reports + the project statement published on Zenodo (DOIs in `reports/release-checklist.md`). D1–D3 exports are built and carded (`leibniz release export`), uploads pending; D4 (model) waits for C3; D5 (harness) is in the repo (Apache-2.0), no DOI yet. | `reports/release-checklist.md` |

## What "v1 public beta" means

The corpus is legible and findable with the v1 model. The serving layer, the
provenance regime and the release tooling are complete for that model; the
model itself is one point short of the gate and is the next phase (C3) — a
re-run (C4) swaps v2 in under a new `run_id` with no change to the viewer or the
API, which always show the latest run per line and keep the older rows.

## Remaining work, in order

1. **C3 — fine-tune v2** on PHILIUMM GT + the minted C2 GT, with the four
   changes recorded in `PROMPTS.md` (vision re-extraction of the edition text;
   staged training with the hand-corrected lines last; confidence filtering of
   minted lines; character n-gram LM decoding), a page-disjoint diplomatic
   held-out set, and the ablation that doubles as the C2 precision test.
2. **C4 — corpus re-run + enrichment** (language id, stratum heuristic on
   every page); regenerate `reports/corpus-v2.md`.
3. **Operator: deployment done (2026-09-21).** leibnizlegible.com serves the
   v1 corpus from a 2 vCPU / 4 GB VPS behind Caddy, with Meilisearch and the
   criterion-3 numbers above. Outstanding: the image mirror upload (in
   progress; images load from the GWLB until it completes), the courtesy note
   to the GWLB, and the D1–D3 dataset uploads per the checklist.
