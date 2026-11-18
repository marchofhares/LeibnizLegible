# Layout-zone census: PHILIUMM's v2 segmentation model over a sample of the Nachlass

PHILIUMM's RF-DETR-Seg model `DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2` (checkpoint `checkpoint_best_ema_v2.pth`, SHA-256 `ba76c8e59288…`, card revision `4a5c7d93e8a6`, licence CC BY-NC 4.0 (the card, read 2026-11-16)), run through her own pipeline (GitLab commit `3f1c7853883d`) at resolution 1272 px and detection threshold 0.4, over 621 pages of this project's store (reports/layout/sample.csv), on 2026-11-18. The kraken baselines inside her zones are the pipeline's bundled model, byte-identical to this project's v1 segmenter. The v1 lines are the store's current lines, in the scan's pixels; the pipeline's zones and lines are scaled back from the image size it worked on (the table below says where that size was the scan's).

## The sample

| block | pages | with detections | with final lines | pipeline image at scan size |
|---|---:|---:|---:|---:|
| Briefwechsel (correspondence) | 200 | 200 | 200 | 7 of 200 |
| Handschriften (LH, without LH 35) | 200 | 200 | 199 | 8 of 200 |
| LH 35 (mathematics) | 100 | 100 | 98 | 5 of 100 |
| Marginalien (annotated printed books) | 100 | 100 | 99 | 1 of 100 |
| PHILIUMM's test pages | 20 | 20 | 20 | 0 of 20 |
| named extra | 1 | 1 | 1 | 0 of 1 |
| **all** | 621 | 621 | 617 | 21 of 621 |

## Zones per class

Zones per page (mean), and the share of pages with at least one zone of the class. The classes are the ones the model emitted.

| block | DigitizationArtefactZone | GraphicZone-figure | MainZone | MarginTextZone | MathsRegion-complex | MathsRegion-inline | NumberingZone |
|---|---:|---:|---:|---:|---:|---:|---:|
| Briefwechsel (correspondence) | 1.00 · 100.0 % | 0.23 · 16.0 % | 1.50 · 93.5 % | 1.21 · 53.5 % | 0.06 · 2.0 % | 0.08 · 4.5 % | 1.08 · 79.0 % |
| Handschriften (LH, without LH 35) | 1.00 · 100.0 % | 0.13 · 8.0 % | 1.44 · 88.5 % | 1.59 · 48.5 % | 0.03 · 1.5 % | 0.10 · 4.0 % | 1.06 · 77.0 % |
| LH 35 (mathematics) | 1.00 · 100.0 % | 1.38 · 46.0 % | 1.44 · 87.0 % | 2.77 · 62.0 % | 1.12 · 18.0 % | 6.05 · 55.0 % | 0.75 · 65.0 % |
| Marginalien (annotated printed books) | 1.01 · 100.0 % | 0.39 · 14.0 % | 0.89 · 80.0 % | 0.47 · 24.0 % | 0.77 · 22.0 % | 1.39 · 37.0 % | 0.18 · 18.0 % |
| PHILIUMM's test pages | 1.00 · 100.0 % | 1.80 · 60.0 % | 1.80 · 100.0 % | 3.50 · 85.0 % | 0.15 · 5.0 % | 4.65 · 40.0 % | 1.15 · 85.0 % |
| named extra | 1.00 · 100.0 % | – | 1.00 · 100.0 % | 2.00 · 100.0 % | – | – | 1.00 · 100.0 % |
| **all** | 1.00 · 100.0 % | 0.46 · 19.3 % | 1.38 · 88.9 % | 1.54 · 49.6 % | 0.34 · 7.7 % | 1.40 · 18.8 % | 0.88 · 66.5 % |

Mean detection confidence per class, over all pages: DigitizationArtefactZone 0.97, GraphicZone-figure 0.74, MainZone 0.94, MarginTextZone 0.73, MathsRegion-complex 0.49, MathsRegion-inline 0.52, NumberingZone 0.77.

## Pages with a figure, a formula, a margin zone

| block | any figure zone | any formula zone | any margin zone | any main zone | page area under main · margin · figure · formula |
|---|---:|---:|---:|---:|---|
| Briefwechsel (correspondence) | 16.0 % (32) | 5.0 % (10) | 53.5 % (107) | 93.5 % (187) | 43.3 % · 2.4 % · 0.3 % · 0.2 % |
| Handschriften (LH, without LH 35) | 8.0 % (16) | 4.5 % (9) | 48.5 % (97) | 88.5 % (177) | 44.4 % · 2.2 % · 0.1 % · 0.2 % |
| LH 35 (mathematics) | 46.0 % (46) | 56.0 % (56) | 62.0 % (62) | 87.0 % (87) | 47.5 % · 3.2 % · 1.4 % · 3.5 % |
| Marginalien (annotated printed books) | 14.0 % (14) | 40.0 % (40) | 24.0 % (24) | 80.0 % (80) | 30.4 % · 1.1 % · 0.7 % · 2.1 % |
| PHILIUMM's test pages | 60.0 % (12) | 40.0 % (8) | 85.0 % (17) | 100.0 % (20) | 51.1 % · 4.5 % · 1.2 % · 1.1 % |
| named extra | 0.0 % (0) | 0.0 % (0) | 100.0 % (1) | 100.0 % (1) | 75.5 % · 3.6 % · 0.0 % · 0.0 % |
| **all** | 19.3 % (120) | 19.8 % (123) | 49.6 % (308) | 88.9 % (552) | 42.5 % · 2.3 % · 0.5 % · 1.1 % |

## Where the v1 lines fall

A v1 line is counted in the zone group that holds at least 50 % of its pixels (the largest such group); `outside` is a line no group holds to that share — outside every zone, or split between zones.

| block | v1 lines | main | margin | numbering | figure | formula | artefact | outside | **in figure or formula** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Briefwechsel (correspondence) | 9,089 | 8,225 (90.5 %) | 543 (6.0 %) | 37 (0.4 %) | 25 (0.3 %) | 24 (0.3 %) | 71 (0.8 %) | 164 (1.8 %) | **49 (0.5 %)** |
| Handschriften (LH, without LH 35) | 15,922 | 13,626 (85.6 %) | 1,826 (11.5 %) | 10 (0.1 %) | 4 (0.0 %) | 17 (0.1 %) | 100 (0.6 %) | 339 (2.1 %) | **21 (0.1 %)** |
| LH 35 (mathematics) | 10,629 | 8,643 (81.3 %) | 1,058 (10.0 %) | 3 (0.0 %) | 54 (0.5 %) | 366 (3.4 %) | 28 (0.3 %) | 477 (4.5 %) | **420 (4.0 %)** |
| Marginalien (annotated printed books) | 5,581 | 3,588 (64.3 %) | 327 (5.9 %) | 3 (0.1 %) | 112 (2.0 %) | 71 (1.3 %) | 50 (0.9 %) | 1,430 (25.6 %) | **183 (3.3 %)** |
| PHILIUMM's test pages | 2,680 | 2,199 (82.0 %) | 415 (15.5 %) | 0 (0.0 %) | 2 (0.1 %) | 12 (0.4 %) | 0 (0.0 %) | 52 (1.9 %) | **14 (0.5 %)** |
| named extra | 203 | 191 (94.1 %) | 7 (3.5 %) | 1 (0.5 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 4 (2.0 %) | **0 (0.0 %)** |
| **all** | 44,104 | 36,472 (82.7 %) | 4,176 (9.5 %) | 54 (0.1 %) | 197 (0.4 %) | 490 (1.1 %) | 249 (0.6 %) | 2,466 (5.6 %) | **687 (1.6 %)** |

### The Marginalien: printed body against notes

On the annotated printed books, `MainZone` is the printed body and `MarginTextZone` the handwritten notes (the model was trained on manuscripts, not on print: the count is what it emits there). By the language the K4 pass gave the page's v1 text (`de` is German print, the Fraktur question):

| language | pages | v1 lines | in main (print body) | in margin (notes) | elsewhere | their final lines | in main · in margin |
|---|---:|---:|---:|---:|---:|---:|---|
| de | 30 | 1,790 | 1,175 (65.6 %) | 95 (5.3 %) | 520 | 1,247 | 1,146 · 98 |
| fr | 15 | 939 | 414 (44.1 %) | 51 (5.4 %) | 474 | 394 | 356 · 38 |
| la | 45 | 2,289 | 1,677 (73.3 %) | 181 (7.9 %) | 431 | 1,893 | 1,846 · 42 |
| mixed | 5 | 505 | 290 (57.4 %) | 0 (0.0 %) | 215 | 287 | 286 · 0 |
| unknown | 5 | 58 | 32 (55.2 %) | 0 (0.0 %) | 26 | 22 | 22 · 0 |
| **all** | 100 | 5,581 | 3,588 (64.3 %) | 327 (5.9 %) | 1,666 | 3,843 | 3,656 · 178 |

## v1 lines against the pipeline's final lines

The pipeline's final lines (`10_fixed_lines`) are the same kraken model's baselines run on the binarised scan with figure, formula and artefact zones erased, merged into the zones, clipped to their region and split where they crossed two. Matched: greedy one-to-one pairs by polygon IoU.

| block | v1 lines | their lines | theirs ÷ v1 | median per page | matched at IoU ≥ 0.5 | of v1 | of theirs | at ≥ 0.3 | at ≥ 0.7 | mean IoU of pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Briefwechsel (correspondence) | 9,089 | 11,412 | 1.26 | 1.17 | 5,607 | 61.7 % | 49.1 % | 6,420 | 4,588 | 0.75 |
| Handschriften (LH, without LH 35) | 15,922 | 16,318 | 1.02 | 1.01 | 12,616 | 79.2 % | 77.3 % | 13,535 | 10,976 | 0.79 |
| LH 35 (mathematics) | 10,629 | 9,497 | 0.89 | 0.97 | 6,421 | 60.4 % | 67.6 % | 7,262 | 5,270 | 0.76 |
| Marginalien (annotated printed books) | 5,581 | 3,843 | 0.69 | 0.97 | 2,372 | 42.5 % | 61.7 % | 2,711 | 1,942 | 0.78 |
| PHILIUMM's test pages | 2,680 | 2,668 | 1.00 | 1.00 | 1,997 | 74.5 % | 74.9 % | 2,206 | 1,679 | 0.78 |
| named extra | 203 | 137 | 0.67 | 0.67 | 62 | 30.5 % | 45.3 % | 99 | 32 | 0.71 |
| **all** | 44,104 | 43,875 | 0.99 | 1.01 | 29,075 | 65.9 % | 66.3 % | 32,233 | 24,487 | 0.77 |

Their final lines by region type, over all pages: main 39,106, margin 4,669, numbering 46, figure 33, formula 21.

## What this does and does not show

- The zones are a model's output, not a judgement: the card gives validation AP 0.91 for MainZone, 0.62 for MarginTextZone, 0.55 for GraphicZone-figure and 0.08–0.19 for the three formula classes, so a formula count here is a lower bound of unknown tightness and a margin count carries that class's error.
- A v1 line inside a figure or formula zone is a line the HTR read where there is no running text; the share is the part of the v1 text that a zone-aware pipeline would not have read.
- Their line count against v1's compares two runs of one baseline model: the difference is the masking, the merge into zones, the clipping and the splitting, not a second segmenter.
- The sample is drawn by work, not by page: a page from a long convolute weighs as much as a page from a short one.
- Nothing here was measured against hand-drawn zones; the 18 test pages are her held-out set, judged by her, not here.

Files: `zone-census-summary.json` (every number above), `zone-census-per-page.csv` (one row a page), `sample.csv` (the sample), `philiumm-layout-pages.csv` (her training pages, kept out).
