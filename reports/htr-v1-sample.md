# HTR v1 — corpus segmentation + recognition pipeline (Phase C1)

_Leibniz Legible, Phase C1. Generated 2026-07-30T14:58:37Z. Deliverable of PROMPTS C1 (SPECS §3, §4.5, §6, §9). Numeric sections are queried from the store by `leibniz pipeline report`; prose is templated._

## What the pipeline does

Two idempotent, resumable stages advance every page through a status machine on the `pages` table: `pending → segmented → recognized`, with genuine failures diverted to `skipped` **with a reason** (SPECS §3).

- **`segment`** runs the PHILIUMM baseline segmenter over each cached page, writes every line's **geometry** (baseline + polygon) to `lines` with `status='machine'` and no text yet, and computes a per-page **segmentation-statistics** row in `page_stats`.
- **`recognize`** crops each stored line from its geometry — without re-running the neural segmenter — runs the PHILIUMM HTR model (the B1-reproduced 7.95 % CER model), and fills each line's **text** + per-line **confidence**, repointing the line's run/model at the recognition run (the text's provenance, SPECS §4.5).

Both stages are status-driven & resumable (commit per page), idempotent (`--redo` re-processes; re-segmentation clears old lines), fault-tolerant (a bad page is skipped-with-reason and logged, never fatal), provenance-complete (one `runs` row per batch: model@version, params, git SHA, counts, wall time), engine-agnostic (segmenter/recogniser injected, so kraken stays optional), and GPU-aware (`--device`, `--batch-size`; CPU fallback). `--sample N` caps a run for the dev slice.

## Pipeline coverage

- **Pages in scope:** 236,795
- **pending:** 236,297 (99.8%)
- **segmented:** 0 (0.0%)
- **recognized:** 498 (0.2%)
- **skipped:** 0 (0.0%)
- **Lines:** 26,902 segmented · 26,504 recognised (text + confidence).

## Throughput

| Run | Stage | Model | Input | OK | Failed |
| ---: | --- | --- | ---: | ---: | ---: |
| 4 | segment | blla_ft_leibniz_v1_0.4750 | 500 | 498 | 2 |
| 5 | recognize | FoNDUE-GD_v2_ft_Leibniz | 498 | 0 | 498 |
| 6 | recognize | FoNDUE-GD_v2_ft_Leibniz | 498 | 413 | 85 |
| 7 | recognize | FoNDUE-GD_v2_ft_Leibniz | 498 | 0 | 498 |
| 8 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 9 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 10 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 11 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 12 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 13 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 14 | recognize | FoNDUE-GD_v2_ft_Leibniz | 431 | 55 | 376 |
| 15 | recognize | FoNDUE-GD_v2_ft_Leibniz | 374 | 374 | 0 |

## Per-line confidence

Mean 0.771 · median 0.805 over recognised lines.

| Confidence | Lines |
| --- | ---: |
| < 0.50 | 2,479 |
| 0.50–0.70 | 3,996 |
| 0.70–0.80 | 4,771 |
| 0.80–0.90 | 4,094 |
| ≥ 0.90 | 7,831 |

## Per set

| Set | Pages | Segmented | Recognized | Skipped | Mean lines/pg |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leibnitiana | 1,768 | 0 | 0 | 0 | 0.0 |
| LeibnizBriefwechsel | 72,284 | 0 | 0 | 0 | 0.0 |
| LeibnizHandschriften | 58,828 | 0 | 498 | 0 | 53.8 |
| LeibnizMarginalien | 103,887 | 0 | 0 | 0 | 0.0 |
| leibniz-rekonstruktionen | 28 | 0 | 0 | 0 | 0.0 |

## Segmentation quality — measured, because it is the known risk

Segmentation is the unsolved half of the corpus (SPECS §9: layered revisions, marginalia, snippets). C1 measures it per page rather than fixing it blindly: `page_stats` records `n_lines`/`n_regions`, `region_coverage`, line-height mean/median/CV (irregular spacing = revised-draft signature), `n_overlaps` (boxes overlapping ≥30 % — layered revisions / marginalia), and `n_short_lines` (< 40 % of median width — interlinear insertions / snippets). These are the raw signal the stratum heuristic reads in C2 (per piece) and C4 (per page).

Over 500 segmented pages: mean **53.8 lines/page**, mean region coverage **32.7%**, mean line-height CV **0.28**. **81.2%** of pages have overlapping line boxes; **92.4%** have short lines.

Worst-overlap pages (segmentation-risk candidates for inspection):

| Page | Lines | Overlaps |
| --- | ---: | ---: |
| `00051016:0021` | 141 | 305 |
| `00051016:0024` | 141 | 305 |
| `00051016:0022` | 156 | 278 |
| `00051016:0023` | 156 | 278 |
| `00051016:0008` | 169 | 233 |
| `00051016:0005` | 168 | 233 |
| `00051016:0006` | 140 | 220 |
| `00051016:0007` | 140 | 220 |
| `00051012:0161` | 144 | 193 |
| `00051012:0164` | 143 | 193 |


## Skip / failure taxonomy

_No skips recorded._

Anticipated per-set difficulty (quantified once the run completes): **Marginalien** (44 % of pages) is the hard case — annotated printed books whose HTR target is the marginal hand, not the printed body (needs zone separation, STATUS Open Q #5); **Handschriften** carries the layered-revision drafts (high line-height CV / overlaps / short lines); **Briefwechsel** fair copies are the clean stratum; German/Kurrent (~15 % of the corpus) is transcribed but at far higher CER (Latin+French model) — a C4 per-language honesty item, not a skip.

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
