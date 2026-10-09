# The Kurrent pilot: candidate readers on Leibniz's own German

20 German pieces from the census (`data/kurrent/german_pieces.jsonl`), spread over 13 volumes, the strata and the hands, 2 of them in Leibniz's own hand; 5 Latin or French control pieces. Pages capped at 2 per piece. Readers: `philiumm`, `trocr-kurrent-xvi-xvii`, `trocr-hanse-xvii`, `trocr-hanse-xvi`, `v1`; `v1` is the stored machine text of the corpus run (the factory's own reader), the others read the same lines afresh from the page images (the v1 geometry, the polygon masked). Each reader's text is aligned to the piece's edition text as a dry run at the factory's per-stratum threshold; **yield** is the share of lines that clear the factory's gate, **confidence** the aligner's matched fraction. Nothing was written to the store.

## Yield at the factory's gate

| reader | German lines | aligned | **German yield** | mean conf | control lines | aligned | control yield | mean conf | ms/line | device |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| trocr-hanse-xvi | 2,288 | 515 | **22.5 %** | 0.335 | 351 | 107 | 30.5 % | 0.406 | 164 | cuda |
| trocr-hanse-xvii | 2,288 | 471 | **20.6 %** | 0.326 | 351 | 64 | 18.2 % | 0.339 | 356 | cuda |
| trocr-kurrent-xvi-xvii | 2,288 | 463 | **20.2 %** | 0.323 | 351 | 83 | 23.6 % | 0.358 | 353 | cuda |
| v1 | 2,288 | 375 | **16.4 %** | 0.308 | 351 | 142 | 40.5 % | 0.445 | — | store |
| philiumm | 2,288 | 285 | **12.5 %** | 0.296 | 351 | 146 | 41.6 % | 0.447 | 17 | cuda |

## The control check

The control pieces are won by `philiumm`: the Latin-trained baseline (philiumm) wins the control pieces as it must.

## German yield by stratum and by hand

| reader | fair_copy | heavy_revision | light_revision | scrap |
|---|---:|---:|---:|---:|
| philiumm | 27.8 % (54) | 8.0 % (1,119) | 35.9 % (460) | 2.4 % (655) |
| trocr-kurrent-xvi-xvii | 38.9 % (54) | 17.6 % (1,119) | 42.6 % (460) | 7.5 % (655) |
| trocr-hanse-xvii | 37.0 % (54) | 18.0 % (1,119) | 43.5 % (460) | 7.6 % (655) |
| trocr-hanse-xvi | 40.7 % (54) | 19.1 % (1,119) | 44.8 % (460) | 11.1 % (655) |
| v1 | 33.3 % (54) | 13.1 % (1,119) | 38.7 % (460) | 4.9 % (655) |

| reader | other | own | partial |
|---|---:|---:|---:|
| philiumm | 14.3 % (1,095) | 8.1 % (688) | 14.3 % (505) |
| trocr-kurrent-xvi-xvii | 13.5 % (1,095) | 25.4 % (688) | 27.7 % (505) |
| trocr-hanse-xvii | 15.1 % (1,095) | 24.4 % (688) | 27.3 % (505) |
| trocr-hanse-xvi | 14.8 % (1,095) | 27.3 % (688) | 32.7 % (505) |
| v1 | 13.9 % (1,095) | 17.6 % (688) | 20.2 % (505) |

## The pieces

| role | record | AA | volume | stratum | hand | pages read / total | lines | philiumm | trocr-kurrent-xvi-xvii | trocr-hanse-xvii | trocr-hanse-xvi | v1 |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| german | 42213 | AA I,3 N.454 | I,3 | heavy_revision | own | 2 / 2 | 73 | 8.2 % | 0.0 % | 0.0 % | 2.7 % | 1.4 % |
| german | 29507 | AA I,3 N.496 | I,3 | light_revision | own | 2 / 2 | 76 | 0.0 % | 0.0 % | 1.3 % | 0.0 % | 0.0 % |
| german | 14964 | AA I,10 N.169 | I,10 | heavy_revision | other | 2 / 6 | 396 | 7.8 % | 2.8 % | 7.1 % | 3.3 % | 4.8 % |
| german | 58675 | AA VI,3 N.089 | VI,3 | light_revision | other | 2 / 2 | 140 | 54.3 % | 52.1 % | 54.3 % | 54.3 % | 55.7 % |
| german | 58771 | AA IV,1 N.029 | IV,1 | heavy_revision | partial | 2 / 2 | 80 | 17.5 % | 36.2 % | 36.2 % | 37.5 % | 20.0 % |
| german | 3220 | AA I,6 N.123 | I,6 | light_revision | partial | 2 / 2 | 33 | 3.0 % | 6.1 % | 6.1 % | 9.1 % | 3.0 % |
| german | 42202 | AA III,3 N.393 | III,3 | scrap | other | 2 / 2 | 26 | 7.7 % | 7.7 % | 7.7 % | 19.2 % | 3.8 % |
| german | 33409 | AA III,4 N.077 | III,4 | scrap | partial | 2 / 4 | 95 | 3.2 % | 10.5 % | 15.8 % | 12.6 % | 2.1 % |
| german | 21453 | AA I,15 N.307 | I,15 | fair_copy | other | 2 / 2 | 28 | 50.0 % | 75.0 % | 71.4 % | 75.0 % | 60.7 % |
| german | 9429 | AA I,7 N.045 | I,7 | heavy_revision | own (L) | 2 / 4 | 306 | 3.3 % | 18.6 % | 17.0 % | 18.0 % | 13.1 % |
| german | 35140 | AA III,1 N.014 | III,1 | light_revision | own | 2 / 2 | 49 | 46.9 % | 40.8 % | 40.8 % | 49.0 % | 49.0 % |
| german | 16897 | AA I,15 N.074 | I,15 | heavy_revision | other | 2 / 2 | 79 | 29.1 % | 38.0 % | 36.7 % | 44.3 % | 34.2 % |
| german | 10047 | AA I,10 N.337 | I,10 | light_revision | other | 2 / 2 | 31 | 32.3 % | 35.5 % | 32.3 % | 35.5 % | 29.0 % |
| german | 13864 | AA I,12 N.019 | I,12 | heavy_revision | partial | 2 / 2 | 74 | 2.7 % | 16.2 % | 14.9 % | 18.9 % | 8.1 % |
| german | 57924 | AA IV,2 N.011 | IV,2 | light_revision | partial | 2 / 8 | 58 | 70.7 % | 86.2 % | 82.8 % | 86.2 % | 82.8 % |
| german | 55765 | AA IV,3 N.084 | IV,3 | scrap | other | 2 / 2 | 369 | 0.0 % | 0.0 % | 0.0 % | 0.0 % | 0.0 % |
| german | 59196 | AA IV,1 N.008 | IV,1 | scrap | partial | 2 / 4 | 165 | 6.7 % | 22.4 % | 20.0 % | 33.9 % | 17.6 % |
| german | 11660 | AA I,12 N.067 | I,12 | fair_copy | other | 2 / 2 | 26 | 3.8 % | 0.0 % | 0.0 % | 3.8 % | 3.8 % |
| german | 30178 | AA IV,3 N.038 | IV,3 | heavy_revision | own (L) | 2 / 4 | 111 | 2.7 % | 52.3 % | 46.8 % | 58.6 % | 34.2 % |
| german | 43865 | AA III,3 N.315 | III,3 | light_revision | own | 2 / 4 | 73 | 19.2 % | 54.8 % | 58.9 % | 57.5 % | 24.7 % |
| control | 5391 | AA I,6 N.358 | I,6 | heavy_revision | la | 2 / 4 | 115 | 66.1 % | 38.3 % | 25.2 % | 47.8 % | 67.0 % |
| control | 20352 | AA I,14 N.239 | I,14 | heavy_revision | fr | 2 / 2 | 70 | 50.0 % | 12.9 % | 14.3 % | 25.7 % | 50.0 % |
| control | 19262 | AA I,14 N.178 | I,14 | light_revision | la | 2 / 2 | 21 | 42.9 % | 42.9 % | 28.6 % | 47.6 % | 42.9 % |
| control | 5886 | AA I,6 N.208 | I,6 | light_revision | fr | 2 / 4 | 55 | 43.6 % | 34.5 % | 34.5 % | 40.0 % | 32.7 % |
| control | 57598 | AA VI,3 N.082 | VI,3 | heavy_revision | la | 2 / 2 | 90 | 2.2 % | 2.2 % | 0.0 % | 2.2 % | 3.3 % |

## The operator's look

`data/kurrent/pilot-side-by-side.html` shows thirty German line crops with every reader's text. Asked whether any reader produces German words, the operator said: *(not yet recorded)*

## Verdict for K2

The reader K2 should use is **`trocr-kurrent-xvi-xvii`** at **20.2 %** of the German pieces' lines at the factory's gate (the `philiumm` baseline: 12.5 %). `trocr-hanse-xvi` has the highest German yield (22.5%) but states no licence (none stated): evaluated, not built on; `trocr-kurrent-xvi-xvii` (MIT) is the reader K2 may use. The control pieces order as they must, so the German ordering can be trusted as far as a ground-truth-free measure goes.

## What this measures, and what it does not

- Yield is minted lines over all lines of the piece's pages; a piece's pages may carry other hands and other texts, and the edition text may omit or reorder what the page holds (C2b, P1), so no reader reaches 100 % and the absolute numbers are the factory's, not the readers'. The ordering between readers on the same lines is the measurement.
- A high confidence says the machine text matches the edition's letters; it does not say the slice landed on the right line. The C2b audit found one misaligned line in 185 with the baseline; a reader with far noisier text could do worse at the boundaries, which the tolerance study (Task 1) bounds.
- The crops are bounding boxes with the polygon masked, not kraken's dewarped extraction; `v1` was read the corpus run's way, the others this way, so `philiumm` against `v1` is the price of the crop.
