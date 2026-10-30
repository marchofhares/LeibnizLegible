# K4 — the German pages read by READER, and written beside v1

Generated 2026-10-30. The page-language pass and its measure (pages by language, the threshold, precision and recall) are in `reports/kurrent/page-lang.md`; the cost of reading mixed pages whole is in `reports/kurrent/k4-mixed-letters.md`.

## The reading job

| | |
|---|---:|
| reader · model | k3-trocr · data/models/k3/trocr/best |
| device · batch · cache | cuda · 16 · True |
| pages | 24,078 of 24,078 |
| lines on them | 1,539,721 |
| lines read (this file) | 1,539,721 |
| of which in the last launch | 1,172,917 |
| skipped | 0 (none) |
| pace (last launch) | 90.8 ms a line · 39,666 lines/h |
| wall (last launch) | 29.6 h (in the engine 28.6 h) |
| started · updated · finished | 2026-10-28T23:14:11+00:00 · 2026-10-30T04:48:22+00:00 · True |

**What the re-read covers.** The job's pages are the German pages the language pass over the machine text found (`leibniz enrich page-lang`, threshold hits≥2 score≥0.3 tokens≥8; on the census's pieces precision 95.2 %, recall 74.5 %, so about three quarters of the German pages by that measure; 30,797 pages called German of 236,210, the printed Marginalien left out of the job). A German page the pass missed keeps v1's text (the operator, 28 October); a second pass is the next round's item (STATUS.md, Next).

### Launches, memory, the guard

| | |
|---|---:|
| launches · relaunches | 2 · 1 |
| relaunched after exits | 143 |
| exits (code, launch) | 143@1, 0@2 |
| peak host RSS (`/usr/bin/time -v`, launches that ended on their own) | 2,769,976 KB |
| wall per launch that ended on its own | 29:38:24 |
| guard samples · starts | 27,574 · 2 |
| card peak (nvidia-smi, Xwayland included) | 5,922 MiB |
| GPU utilisation, mean | 88.2 % |
| host MemAvailable, minimum | 6,727 MiB |
| guard kills | 1 |

First progress line: `10:00:35 k3-trocr: 5,771/1,539,721 lines done (5,771 this run, 0 skipped) · 34,327 lines/h · 105 ms/line · ETA 44h 41m · pages 107/24,078`

Last progress line: `finished: k3-trocr: 1,539,721/1,539,721 lines done (1,172,917 this run, 0 skipped) · 39,666 lines/h · 91 ms/line · ETA 0s · pages 24,078/24,078`

## The write (Task 4)

| | |
|---|---:|
| run | 617 (stage recognize, model k3-trocr@runs-615-epoch-5, scope de) |
| pages in the list | 24,078 (without readings 0) |
| lines considered | 1,539,721 |
| rows written | 1,539,688 on 24,078 pages |
| empty readings (no row) | 33 |
| lines without a reading | 0 |
| orphan readings | 0 |
| crops under 80 px | 252,286 lines, 252,278 of them with a row |
| under the run after | 24,078 pages, 1,539,688 rows |
| store after | 19,354,243,072 bytes (+2,210,672,640 bytes), WAL 0 |

| collection | pages | lines | rows | crops under 80 px |
|---|---:|---:|---:|---:|
| Leibnitiana | 18 | 1,481 | 1,481 | 279 |
| LeibnizBriefwechsel | 14,455 | 780,959 | 780,940 | 164,360 |
| LeibnizHandschriften | 9,604 | 757,241 | 757,227 | 87,619 |
| leibniz-rekonstruktionen | 1 | 40 | 40 | 28 |

Every non-empty reading got a row, the narrow crops included (the operator's decision of 28 October): the letter-pool number was measured on all crops, and one run per page keeps K3b's replacement simple. The narrow crops are segmentation fragments either way — READER returns a single character on most of them — and their count is Open question 32 for K3b's segmentation measurement (STATUS.md).
