# HTR v1 — corpus segmentation + recognition pipeline (Phase C1)

_Leibniz Legible, Phase C1. Generated 2026-07-29T00:00:00Z. Deliverable of PROMPTS C1 (SPECS §3, §4.5, §6, §9). Numeric sections are queried from the store by `leibniz pipeline report`; prose is templated._

## What the pipeline does

Two idempotent, resumable stages advance every page through a status machine on the `pages` table: `pending → segmented → recognized`, with genuine failures diverted to `skipped` **with a reason** (SPECS §3).

- **`segment`** runs the PHILIUMM baseline segmenter over each cached page, writes every line's **geometry** (baseline + polygon) to `lines` with `status='machine'` and no text yet, and computes a per-page **segmentation-statistics** row in `page_stats`.
- **`recognize`** crops each stored line from its geometry — without re-running the neural segmenter — runs the PHILIUMM HTR model (the B1-reproduced 7.95 % CER model), and fills each line's **text** + per-line **confidence**, repointing the line's run/model at the recognition run (the text's provenance, SPECS §4.5).

Both stages are status-driven & resumable (commit per page), idempotent (`--redo` re-processes; re-segmentation clears old lines), fault-tolerant (a bad page is skipped-with-reason and logged, never fatal), provenance-complete (one `runs` row per batch: model@version, params, git SHA, counts, wall time), engine-agnostic (segmenter/recogniser injected, so kraken stays optional), and GPU-aware (`--device`, `--batch-size`; CPU fallback). `--sample N` caps a run for the dev slice.

## Pipeline coverage

- **Pages in scope:** 0
- **pending:** 0 (0.0%)
- **segmented:** 0 (0.0%)
- **recognized:** 0 (0.0%)
- **skipped:** 0 (0.0%)
- **Lines:** 0 segmented · 0 recognised (text + confidence).

## Per-line confidence

_No recognised lines with confidence yet (run `leibniz pipeline recognize`)._

## Per set

_No pages processed yet._

## Segmentation quality — measured, because it is the known risk

Segmentation is the unsolved half of the corpus (SPECS §9: layered revisions, marginalia, snippets). C1 measures it per page rather than fixing it blindly: `page_stats` records `n_lines`/`n_regions`, `region_coverage`, line-height mean/median/CV (irregular spacing = revised-draft signature), `n_overlaps` (boxes overlapping ≥30 % — layered revisions / marginalia), and `n_short_lines` (< 40 % of median width — interlinear insertions / snippets). These are the raw signal the stratum heuristic reads in C2 (per piece) and C4 (per page).

_No segmentation stats yet (run `leibniz pipeline segment`)._

## Skip / failure taxonomy

_No skips recorded._

Anticipated per-set difficulty (quantified once the run completes): **Marginalien** (44 % of pages) is the hard case — annotated printed books whose HTR target is the marginal hand, not the printed body (needs zone separation, STATUS Open Q #5); **Handschriften** carries the layered-revision drafts (high line-height CV / overlaps / short lines); **Briefwechsel** fair copies are the clean stratum; German/Kurrent (~15 % of the corpus) is transcribed but at far higher CER (Latin+French model) — a C4 per-language honesty item, not a skip.

## Status of the live run

The numeric sections above read zero because the segment/recognize stages need the optional kraken+torch stack (a multi-GB install plus the PHILIUMM model files) **and** the local image cache (the A2 full pull is ~365 GB and, like all `data/`, is gitignored, so it does not travel between sessions); no GPU is attached in this build environment. Rather than fabricate throughput and confidence numbers, the pipeline was **built and fully offline-tested** here, and the sample + corpus runs are the operator commands below — `leibniz pipeline report` refreshes every number the moment they run.

**Machinery verification (this session).** The complete state machine was exercised end-to-end against fake segmenter/recogniser objects and synthetic page images: `pending → segmented → recognized` with geometry + text + confidence + provenance stored, per-page segmentation stats computed, blank pages skipped with a reason, a raising segmenter isolated to its page, crop/line-count drift handled as a logged partial, `--redo` without duplicating lines, `--sample`/`--set` scoping, and `runs` bookkeeping — plus unit tests of the segmentation-stats geometry on hand-built fair-copy / overlapping / interlinear / blank pages. All pipeline tests pass; the kraken-absent CLI guard exits cleanly with an install hint.

## Operator runbook

```bash
# 1. Install the heavy stack and fetch the PHILIUMM models (CC BY 4.0).
uv pip install kraken pyarrow            # the `bench` extra
leibniz bench fetch                      # HTR model + val split

# 2. Pull a ~500-page dev slice spanning all sets (if not already cached).
leibniz images fetch --set LeibnizHandschriften --limit 150
leibniz images fetch --set LeibnizBriefwechsel  --limit 150
leibniz images fetch --set LeibnizMarginalien   --limit 150
leibniz images fetch --set Leibnitiana          --limit 50

# 3. Run the pipeline on the sample (GPU if available).
leibniz pipeline segment   --sample 500 --device cuda
leibniz pipeline recognize --sample 500 --device cuda --batch-size 32
leibniz pipeline status
leibniz pipeline report                  # refreshes this file

# 4. Full corpus (documented; resumable — checkpoint across invocations):
leibniz pipeline segment   --device cuda
leibniz pipeline recognize --device cuda --batch-size 32
leibniz pipeline report
```

### GPU-hour and cost estimate (full corpus, one pass)

Preliminary, to be calibrated by the sample run's measured pages/hour (recorded in `runs` wall-time): ~3–6 s/page combined (segment + recognize) on a modern GPU → 236,795 pages ≈ **~260 GPU-hours** per pass (range ~120–330 by GPU class / page size / line density) ≈ **$65–330** at $0.5–1.5/GPU-hour. C1 (v1) and C4 (v2) are two passes; SPECS §4.2 budgets 150–300 GPU-hours total. CPU-only is fine for the sample, impractical for the corpus.

### Reproduce / regenerate

```
leibniz pipeline segment [--set S] [--work ID] [--sample N] [--redo] [--device D]
leibniz pipeline recognize [--sample N] [--redo] [--device D] [--batch-size B]
leibniz pipeline status
leibniz pipeline report --out reports/htr-v1-sample.md
```

Models: segmentation `blla_ft_leibniz_v1` (doi:10.5281/zenodo.21537859) + HTR `FoNDUE-GD_v2_ft_Leibniz` (doi:10.5281/zenodo.21457538), both PHILIUMM, CC BY 4.0.
