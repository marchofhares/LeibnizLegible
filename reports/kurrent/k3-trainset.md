# K3: the training set

The minted lines selected for the fine-tune, tagged, screened and split; crops under `data/train/k3/`, every row in its `manifest.jsonl`. Generated 2026-10-21.

## Selection

**60,163 open-bucket rows** on 1,447 records and 3,854 pages.

| reader | lines | records | characters |
|---|---:|---:|---:|
| trocr-kurrent-xvi-xvii | 50,720 | 1,046 | 2,283,061 |
| v1 | 9,443 | 401 | 392,855 |

| hand group | lines | records | characters |
|---|---:|---:|---:|
| leibniz | 2,612 | 51 | 99,383 |
| other | 57,551 | 1,396 | 2,576,533 |

## Exclusions

1,434 rows excluded, the first reason that applies in the order held-out page, letter-pool page, Marginalien, math, bracket, noise, audit, then the crop's failure.

| reason | rows |
|---|---:|
| audit | 215 |
| bracket | 1,154 |
| math | 32 |
| noise | 33 |

By reason and reader: audit/trocr-kurrent-xvi-xvii 205, audit/v1 10, bracket/trocr-kurrent-xvi-xvii 889, bracket/v1 265, math/trocr-kurrent-xvi-xvii 4, math/v1 28, noise/trocr-kurrent-xvi-xvii 26, noise/v1 7.

## The screen

The band the v1-minted Latin and French lines occupy (273,517 rows): the ratio of the minted text's length to the v1 reading's between **0.80 and 1.44** (median 1.00), the alignment confidence at or above **0.733** (median 0.950). A reader line is outside the band when its ratio against the reader's own reading, or its confidence, falls outside.

| group | lines | ratio p2.5 / median / p97.5 | conf p2.5 / median | outside | share | by |
|---|---:|---|---|---:|---:|---|
| leibniz | 1,949 | 0.83 / 1.00 / 1.53 | 0.731 / 0.906 | 145 | 7.4 % | conf_low 52, ratio_high 66, ratio_low 35 |
| other | 47,647 | 0.83 / 1.00 / 1.41 | 0.727 / 0.918 | 3,306 | 6.9 % | conf_low 1,556, ratio_high 1,116, ratio_low 988 |

The v1-minted rows of the same records, for comparison: 1,583 of 9,133 outside (17.3 %).

**Stop rule:** more than 10 % of the Leibniz-hand lines outside stops the phase at Checkpoint A — **not triggered**.

The twenty worst reader lines (farthest outside the ratio band, then the lowest confidence):

| ref | group | record | stratum | ratio | conf | why | minted / reading chars |
|---|---|---|---|---:|---:|---|---:|
| `DE-611-HS-970451:0002:056` | other | 58770 | heavy_revision | 21.000 | 1.000 | ratio_high | 21 / 1 |
| `DE-611-HS-867509:0122:009` | other | 44102 | heavy_revision | 15.000 | 1.000 | ratio_high | 15 / 1 |
| `00068422:0004:032` | other | 56509 | heavy_revision | 14.000 | 1.000 | ratio_high | 14 / 1 |
| `00068430:0029:036` | other | 58297 | heavy_revision | 14.000 | 1.000 | ratio_high | 14 / 1 |
| `DE-611-HS-856291:0012:037` | other | 72 | heavy_revision | 14.000 | 1.000 | ratio_high | 14 / 1 |
| `DE-611-HS-960158:0136:031` | other | 43717 | heavy_revision | 13.000 | 1.000 | ratio_high | 13 / 1 |
| `00068593:0053:000` | other | 58810 | light_revision | 13.000 | 1.000 | ratio_high | 13 / 1 |
| `DE-611-HS-971300:0068:026` | other | 17368 | heavy_revision | 11.000 | 1.000 | ratio_high | 11 / 1 |
| `DE-611-HS-974056:0019:013` | other | 3779 | light_revision | 11.000 | 1.000 | ratio_high | 11 / 1 |
| `DE-611-HS-959461:0081:045` | other | 42703 | light_revision | 11.000 | 1.000 | ratio_high | 11 / 1 |
| `00068541:0005:151` | other | 44026 | heavy_revision | 11.000 | 1.000 | ratio_high | 11 / 1 |
| `DE-611-HS-867509:0122:006` | other | 44102 | heavy_revision | 11.000 | 1.000 | ratio_high | 11 / 1 |
| `DE-611-HS-959461:0084:027` | other | 42703 | light_revision | 10.000 | 1.000 | ratio_high | 10 / 1 |
| `00068782:0137:111` | other | 59738 | heavy_revision | 9.000 | 1.000 | ratio_high | 9 / 1 |
| `DE-611-HS-862243:0001:012` | other | 9606 | light_revision | 9.000 | 1.000 | ratio_high | 9 / 1 |
| `DE-611-HS-959461:0098:021` | other | 27161 | light_revision | 8.000 | 1.000 | ratio_high | 8 / 1 |
| `DE-611-HS-867509:0161:034` | other | 28714 | heavy_revision | 8.000 | 1.000 | ratio_high | 8 / 1 |
| `00068823:0107:098` | other | 43519 | heavy_revision | 8.000 | 1.000 | ratio_high | 8 / 1 |
| `DE-611-HS-867509:0120:008` | other | 44102 | heavy_revision | 8.000 | 1.000 | ratio_high | 8 / 1 |
| `00068430:0024:100` | other | 57247 | heavy_revision | 8.000 | 1.000 | ratio_high | 8 / 1 |

## The split

Kept: **58,729 lines** on 1,446 records, 3,850 pages, 1,321 units (records joined over shared pages), 2,601,780 characters. The validation pieces were read from the frozen file `reports/kurrent/k3-val-pieces.csv`.
 Pages on both sides: **0**.

| split | lines | records | pages | units | characters |
|---|---:|---:|---:|---:|---:|
| train | 55,596 | 1,348 | 3,634 | 1,229 | 2,454,505 |
| val | 3,133 | 98 | 216 | 92 | 147,275 |

By stratum and hand group (train / val lines, the validation share):

| cell | train | val | val share |
|---|---:|---:|---:|
| fair_copy/other | 27 | 7 | 20.6 % |
| heavy_revision/leibniz | 2,242 | 164 | 6.8 % |
| heavy_revision/other | 35,331 | 1,953 | 5.2 % |
| light_revision/leibniz | 44 | 0 | 0.0 % |
| light_revision/other | 17,650 | 949 | 5.1 % |
| scrap/other | 302 | 60 | 16.6 % |

By reader (train / val):

| reader | train | val |
|---|---:|---:|
| trocr-kurrent-xvi-xvii | 46,921 | 2,675 |
| v1 | 8,675 | 458 |

## Disk, from the sample

1,000 of 1,000 sampled lines cut: 0.16 GB, **157.7 KB a line**; projected for 58,729 kept lines: **9.48 GB**.

## The crops

3,850 pages cut; by status: ok 58,729; 9.42 GB on disk (the PNGs; the sidecars beside them).

## What this is, and is not

- The text is the edition's reading text as the factory minted it (NFC; the scribe's line-end mark kept as `¬` since C2b): abbreviations expanded, u/v and i/j as the edition prints them. A model trained on it learns the edition's conventions, not a diplomatic transcription (the C3 prompt's normalization tax).
- The precision of the reader-placed lines is unmeasured: K2's audit sheet awaits its judge. The screen above is a length-and-confidence check, not a reading.
- The validation set chooses checkpoints; it is drawn from the same mint, so it shares the mint's biases. The honest German error rate is the letter pool's (K2b), never trained on.
