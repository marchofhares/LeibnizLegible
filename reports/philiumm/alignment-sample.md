# PHILIUMM's worked example under this project's aligner

Their repository `eman8/scripts/htr-ocr/alignement-verite-de-terrain-et-transcriptions` at commit `9d2ee4e500e0`: the edition reading text (9,415 characters), the HTR lines of `LH_1_3_4_0002r-0001v.xml` (142 lines), `LH_1_3_4_0002v-0001r.xml` (115 lines), and their aligned output.

**Their run, from the committed `alignment_report.csv`:** 257 HTR lines, 230 replaced by edition text (89.5 %), 26 without a match, 0 blanked by the confidence gate, 1 + 0 by the word-ratio gates; 206 Passim passages, 27 fallback lines. Settings, from their README: defaults `--conf_threshold 0.0` (no per-line gate, which the zero in `nb_low_conf` confirms), `--min_token_ratio 0.4`, `--max_token_ratio 2.5`, `--min_sim 0.5`; the usage example runs `--conf_threshold 0.7`, and the dataset card states the noisy split was filtered at Levenshtein ≥ 0.7. Their per-line score is `1 − Levenshtein ÷ max(len)` on the raw text between the HTR line and the best window of whole edition words (`src/filter_passim_results.py`). Their output carries that score on every aligned line: 212 of the 230 scored lines reach 0.7 and 230 reach 0.5 — the rows to set against the *raw ≥ 0.7* and *raw ≥ 0.5* columns below.

**This project's aligner:** the whole edition text projected onto the lines by global alignment of the folded strings (`align_piece`, `free_edition_ends=True`), a line minted when ≥ 0.60 of its folded characters are matched (`align_conf`); the minted text is a character slice of the edition. *raw ≥ 0.7* applies their formula and the dataset card's cut to the HTR line and its minted slice; *raw ≥ 0.5* their `--min_sim`. A minted line with a hyphen kept carries one character the edition lacks.

## Yield under four ways of feeding the example

| configuration | lines | minted | yield | minted, raw ≥ 0.7 | minted, raw ≥ 0.5 |
|---|---:|---:|---:|---:|---:|
| file:LH_1_3_4_0002r-0001v.xml | 142 | 121 | 85.2 % | 112 (78.9 %) | 119 (83.8 %) |
| file:LH_1_3_4_0002v-0001r.xml | 115 | 51 | 44.3 % | 47 (40.9 %) | 50 (43.5 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | 257 | 108 | 42.0 % | 98 (38.1 %) | 106 (41.2 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | 257 | 173 | 67.3 % | 158 (61.5 %) | 169 (65.8 %) |
| regions | 257 | 194 | 75.5 % | 179 (69.6 %) | 192 (74.7 %) |

*per file*: one piece per PAGE file, as their run takes a file. Each image is one side of a bifolium: `0002r-0001v` shows folios 1v and 2r, adjacent in the text; `0002v-0001r` shows 2v and 1r, the end and the start of the passage, which one monotone alignment cannot both place. *concat*: both files as one piece, in either order. *regions*: each `TextRegion` (a main zone, a margin) as its own piece against the whole text — the unit at which the text is contiguous, and the one the comparison below uses for its best case.

## In their CSV's columns

**file:LH_1_3_4_0002r-0001v.xml**

| filename | nb_htr_lines | nb_gt_aligned | pct_gt_aligned | nb_no_alignment | pct_no_alignment |
|---|---:|---:|---:|---:|---:|
| LH_1_3_4_0002r-0001v.xml | 142 | 121 | 85.2 | 21 | 14.8 |
| TOTAL | 142 | 121 | 85.2 | 21 | 14.8 |

**file:LH_1_3_4_0002v-0001r.xml**

| filename | nb_htr_lines | nb_gt_aligned | pct_gt_aligned | nb_no_alignment | pct_no_alignment |
|---|---:|---:|---:|---:|---:|
| LH_1_3_4_0002v-0001r.xml | 115 | 51 | 44.3 | 64 | 55.7 |
| TOTAL | 115 | 51 | 44.3 | 64 | 55.7 |

**concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml**

| filename | nb_htr_lines | nb_gt_aligned | pct_gt_aligned | nb_no_alignment | pct_no_alignment |
|---|---:|---:|---:|---:|---:|
| LH_1_3_4_0002r-0001v.xml | 142 | 106 | 74.6 | 36 | 25.4 |
| LH_1_3_4_0002v-0001r.xml | 115 | 2 | 1.7 | 113 | 98.3 |
| TOTAL | 257 | 108 | 42.0 | 149 | 58.0 |

**concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml**

| filename | nb_htr_lines | nb_gt_aligned | pct_gt_aligned | nb_no_alignment | pct_no_alignment |
|---|---:|---:|---:|---:|---:|
| LH_1_3_4_0002r-0001v.xml | 142 | 121 | 85.2 | 21 | 14.8 |
| LH_1_3_4_0002v-0001r.xml | 115 | 52 | 45.2 | 63 | 54.8 |
| TOTAL | 257 | 173 | 67.3 | 84 | 32.7 |

**regions**

| filename | nb_htr_lines | nb_gt_aligned | pct_gt_aligned | nb_no_alignment | pct_no_alignment |
|---|---:|---:|---:|---:|---:|
| LH_1_3_4_0002r-0001v.xml | 142 | 122 | 85.9 | 20 | 14.1 |
| LH_1_3_4_0002v-0001r.xml | 115 | 72 | 62.6 | 43 | 37.4 |
| TOTAL | 257 | 194 | 75.5 | 63 | 24.5 |

The confidence and word-ratio columns of their report have no counterpart here (n/a).

## Line by line against their output

For every HTR line: *both same* — both aligned it and the texts agree at folded similarity ≥ 0.9; *both different* — both aligned it, the texts differ; *ours only*; *theirs only*; *neither*.

| configuration | file | lines | both same | both different | ours only | theirs only | neither |
|---|---|---:|---:|---:|---:|---:|---:|
| file:LH_1_3_4_0002r-0001v.xml | LH_1_3_4_0002r-0001v.xml | 142 | 111 (78.2 %) | 9 (6.3 %) | 1 (0.7 %) | 12 (8.5 %) | 9 (6.3 %) |
| file:LH_1_3_4_0002r-0001v.xml | **all** | 142 | 111 (78.2 %) | 9 (6.3 %) | 1 (0.7 %) | 12 (8.5 %) | 9 (6.3 %) |
| file:LH_1_3_4_0002v-0001r.xml | LH_1_3_4_0002v-0001r.xml | 115 | 39 (33.9 %) | 11 (9.6 %) | 1 (0.9 %) | 48 (41.7 %) | 16 (13.9 %) |
| file:LH_1_3_4_0002v-0001r.xml | **all** | 115 | 39 (33.9 %) | 11 (9.6 %) | 1 (0.9 %) | 48 (41.7 %) | 16 (13.9 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | LH_1_3_4_0002r-0001v.xml | 142 | 97 (68.3 %) | 7 (4.9 %) | 2 (1.4 %) | 28 (19.7 %) | 8 (5.6 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | LH_1_3_4_0002v-0001r.xml | 115 | 0 (0.0 %) | 0 (0.0 %) | 2 (1.7 %) | 98 (85.2 %) | 15 (13.0 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | **all** | 257 | 97 (37.7 %) | 7 (2.7 %) | 4 (1.6 %) | 126 (49.0 %) | 23 (8.9 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | LH_1_3_4_0002r-0001v.xml | 142 | 111 (78.2 %) | 9 (6.3 %) | 1 (0.7 %) | 12 (8.5 %) | 9 (6.3 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | LH_1_3_4_0002v-0001r.xml | 115 | 38 (33.0 %) | 12 (10.4 %) | 2 (1.7 %) | 48 (41.7 %) | 15 (13.0 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | **all** | 257 | 149 (58.0 %) | 21 (8.2 %) | 3 (1.2 %) | 60 (23.3 %) | 24 (9.3 %) |
| regions | LH_1_3_4_0002r-0001v.xml | 142 | 112 (78.9 %) | 8 (5.6 %) | 2 (1.4 %) | 12 (8.5 %) | 8 (5.6 %) |
| regions | LH_1_3_4_0002v-0001r.xml | 115 | 58 (50.4 %) | 12 (10.4 %) | 2 (1.7 %) | 28 (24.3 %) | 15 (13.0 %) |
| regions | **all** | 257 | 170 (66.1 %) | 20 (7.8 %) | 4 (1.6 %) | 40 (15.6 %) | 23 (8.9 %) |

By zone type (SegmOnto, from the regions' `custom` attribute), all files:

| configuration | zone | lines | both same | both different | ours only | theirs only | neither |
|---|---|---:|---:|---:|---:|---:|---:|
| file:LH_1_3_4_0002r-0001v.xml | DigitizationArtefactZone | 3 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 3 (100.0 %) |
| file:LH_1_3_4_0002r-0001v.xml | MainZone | 116 | 97 (83.6 %) | 7 (6.0 %) | 1 (0.9 %) | 8 (6.9 %) | 3 (2.6 %) |
| file:LH_1_3_4_0002r-0001v.xml | MarginTextZone | 21 | 14 (66.7 %) | 2 (9.5 %) | 0 (0.0 %) | 4 (19.0 %) | 1 (4.8 %) |
| file:LH_1_3_4_0002r-0001v.xml | NumberingZone | 2 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 2 (100.0 %) |
| file:LH_1_3_4_0002v-0001r.xml | DigitizationArtefactZone | 3 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 3 (100.0 %) |
| file:LH_1_3_4_0002v-0001r.xml | MainZone | 68 | 32 (47.1 %) | 9 (13.2 %) | 0 (0.0 %) | 20 (29.4 %) | 7 (10.3 %) |
| file:LH_1_3_4_0002v-0001r.xml | MarginTextZone | 43 | 7 (16.3 %) | 2 (4.7 %) | 0 (0.0 %) | 28 (65.1 %) | 6 (14.0 %) |
| file:LH_1_3_4_0002v-0001r.xml | NumberingZone | 1 | 0 (0.0 %) | 0 (0.0 %) | 1 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | DigitizationArtefactZone | 6 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 6 (100.0 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | MainZone | 184 | 97 (52.7 %) | 7 (3.8 %) | 1 (0.5 %) | 69 (37.5 %) | 10 (5.4 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | MarginTextZone | 64 | 0 (0.0 %) | 0 (0.0 %) | 2 (3.1 %) | 57 (89.1 %) | 5 (7.8 %) |
| concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml | NumberingZone | 3 | 0 (0.0 %) | 0 (0.0 %) | 1 (33.3 %) | 0 (0.0 %) | 2 (66.7 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | DigitizationArtefactZone | 6 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 6 (100.0 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | MainZone | 184 | 129 (70.1 %) | 16 (8.7 %) | 1 (0.5 %) | 28 (15.2 %) | 10 (5.4 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | MarginTextZone | 64 | 20 (31.2 %) | 5 (7.8 %) | 1 (1.6 %) | 32 (50.0 %) | 6 (9.4 %) |
| concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml | NumberingZone | 3 | 0 (0.0 %) | 0 (0.0 %) | 1 (33.3 %) | 0 (0.0 %) | 2 (66.7 %) |
| regions | DigitizationArtefactZone | 6 | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 6 (100.0 %) |
| regions | MainZone | 184 | 131 (71.2 %) | 15 (8.2 %) | 2 (1.1 %) | 27 (14.7 %) | 9 (4.9 %) |
| regions | MarginTextZone | 64 | 39 (60.9 %) | 5 (7.8 %) | 0 (0.0 %) | 13 (20.3 %) | 7 (10.9 %) |
| regions | NumberingZone | 3 | 0 (0.0 %) | 0 (0.0 %) | 2 (66.7 %) | 0 (0.0 %) | 1 (33.3 %) |

Agreement is not correctness: two aligners fed the same edition text can share a mistake, and a line both decline (the library stamp, a page number, a line the edition omits) is not thereby wrong. What the comparison shows is where the two methods make different calls, which is where a human look pays. One witness is on the sheet, though: on a line both aligned differently, the HTR reading of the strip is closer to one of the two texts. *file:LH_1_3_4_0002r-0001v.xml*: closer to this project's slice on 4, to their window on 5, equally close on 0 of 9; *file:LH_1_3_4_0002v-0001r.xml*: closer to this project's slice on 3, to their window on 8, equally close on 0 of 11; *concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml*: closer to this project's slice on 4, to their window on 3, equally close on 0 of 7; *concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml*: closer to this project's slice on 7, to their window on 14, equally close on 0 of 21; *regions*: closer to this project's slice on 9, to their window on 11, equally close on 0 of 20. A slice that runs on past the window where the HTR reads more words is the usual case.

### Where they differ — file:LH_1_3_4_0002r-0001v.xml

22 lines; the first 22 below, all in `data/philiumm/sample/comparison.csv`.

| file | # | zone | bucket | HTR line | this project | theirs | their score | HTR↔ours | HTR↔theirs |
|---|---:|---|---|---|---|---|---:|---:|---:|
| LH_1_3_4_0002r-0001v | 11 | MainZone | both_different | Brentius  in protgomenisq petium | Brentius in prolegomenis contra Petrum | Brentius in prolegomenis contra | 0.69 | 0.74 | 0.71 |
| LH_1_3_4_0002r-0001v | 21 | MainZone | theirs_only | haberi traditione Ecelesiae, prorsus quemadmodum | — | haberi traditione Ecclesiae, d | 0.60 | — | 0.60 |
| LH_1_3_4_0002r-0001v | 55 | MainZone | theirs_only | et pro octavo | — | et pro octavo | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 56 | MainZone | theirs_only |  a, suisto praerepla | — | a Christo praecepta, | 0.65 | — | 0.74 |
| LH_1_3_4_0002r-0001v | 67 | MainZone | both_different | sed divinitatis personas. diit christus | sed divinitatis personas. Et cum dicitur Christus | sed divinitatis personas. Et cum | 0.77 | 0.79 | 0.76 |
| LH_1_3_4_0002r-0001v | 68 | MainZone | both_different | est DEus versus est etristus est persona dulrimentis | est Deus, sensus est Christus est persona divinitatis. | est Deus, sensus est Christus est persona d | 0.69 | 0.81 | 0.73 |
| LH_1_3_4_0002r-0001v | 78 | MainZone | ours_only | ali quod necesse est esse inter Percipiens perceptiam | aliquod est inter personam percipientem et perceptam, qua | — | — | 0.48 | — |
| LH_1_3_4_0002r-0001v | 79 | MainZone | theirs_only | et perceptionem et perceptum. quae tamen | — | percipientem et perceptam, quae tamen | 0.78 | — | 0.79 |
| LH_1_3_4_0002r-0001v | 80 | MainZone | theirs_only | unum sunt peci personam percistientem | — | est inter personam percipientem | 0.68 | — | 0.68 |
| LH_1_3_4_0002r-0001v | 81 | MainZone | theirs_only | et perceptam, quae tamen  unum | — | et perceptam, quae tamen unum | 0.97 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 82 | MainZone | theirs_only | individuum sunt. | — | individuum sunt. | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 84 | MainZone | both_different | et  ircamatione, longe aptior | et unitate incarnatione, longe tutior aptior | incarnatione, longe tutior | 0.69 | 0.58 | 0.70 |
| LH_1_3_4_0002r-0001v | 107 | MainZone | both_different | Et cultum  magis e humanitatem hiiste | et cultum unio magis in humanitate Christi humanitatem | et cultum unio magis in humanitate | 0.59 | 0.59 | 0.58 |
| LH_1_3_4_0002r-0001v | 108 | MainZone | theirs_only | quam divinitatem Christi inmc haber | — | quam divinitatem Christi in animo habere | 0.85 | — | 0.85 |
| LH_1_3_4_0002r-0001v | 111 | MainZone | both_different | malo redeantur amimosque ad  | malo medeantur, animosque ad Deum | malo medeantur, animosque ad | 0.89 | 0.78 | 0.93 |
| LH_1_3_4_0002r-0001v | 118 | MainZone | both_different | apud Catholices. | apud Catholicos. Q | apud Catholicos. | 0.94 | 0.82 | 0.93 |
| LH_1_3_4_0002r-0001v | 119 | MarginTextZone | theirs_only | verbum seu id quod intelligifut, est | — | Verbum seu id quod intelligitur, est | 0.92 | — | 0.94 |
| LH_1_3_4_0002r-0001v | 120 | MarginTextZone | theirs_only | imago patris, quia pater vertum percipitus | — | imago patris, quia pater verbum percipiens | 0.93 | — | 0.93 |
| LH_1_3_4_0002r-0001v | 121 | MarginTextZone | theirs_only | in ipsum percipit quod ipse est, nempe | — | id ipsum percipit quod ipse est, nempe | 0.97 | — | 0.97 |
| LH_1_3_4_0002r-0001v | 122 | MarginTextZone | both_different | Montem illam quae se intelligit. Percrptio | arnationem creatas communicatas esse Christo humanitati Percept… | Mentem illam quae se intelligit. Sententi | 0.83 | 0.40 | 0.83 |
| LH_1_3_4_0002r-0001v | 132 | MarginTextZone | both_different | reale abstractum preter  perceptio | reale abstractum praeter cogita perceptionem (c) | reale abstractum praeter cogita | 0.71 | 0.72 | 0.73 |
| LH_1_3_4_0002r-0001v | 139 | MarginTextZone | theirs_only | quantum seiam | — | quantum sciam | 0.92 | — | 0.92 |

### Where they differ — file:LH_1_3_4_0002v-0001r.xml

60 lines; the first 60 below, all in `data/philiumm/sample/comparison.csv`.

| file | # | zone | bucket | HTR line | this project | theirs | their score | HTR↔ours | HTR↔theirs |
|---|---:|---|---|---|---|---|---:|---:|---:|
| LH_1_3_4_0002v-0001r | 2 | MainZone | theirs_only |  sutius est statuere in scriptua sacra | — | Tutius est statuere in scriptura sacra | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 3 | MainZone | theirs_only | nihil contineri nisi verbum Dei, nec autores librorum | — | nihil contineri nisi verbum Dei, nec autores librorum | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 4 | MainZone | theirs_only | etiam in his quae ad salutem nnon pertinent, qualia | — | etiam in his quae ad salutem non pertinent, qualia | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 5 | MainZone | theirs_only | sunt philosophica, chromologica, Geographica, | — | sunt philosophica, chronologica, Geographica, | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 6 | MainZone | theirs_only | Salsum dixisse. Errores autim si qui sunt libra | — | falsum dixisse. Errores autem si qui sunt, libra | 0.94 | — | 0.96 |
| LH_1_3_4_0002v-0001r | 7 | MainZone | theirs_only | riorum, culpa irrepsisde, aut a verbis male | — | riorum culpa irrepsisse, aut a verbis male | 0.95 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 8 | MainZone | theirs_only | intellectis nasci | — | intellectis nasci | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 9 | MainZone | theirs_only | In libis inditt Tobiae;, a equi | — | In libris Judith, Tobiae, | 0.58 | — | 0.66 |
| LH_1_3_4_0002v-0001r | 18 | MainZone | both_different | tamen communior sententia veteris | tamen communis communior sententia veteris | communis communior sententia veteris | 0.83 | 0.79 | 0.83 |
| LH_1_3_4_0002v-0001r | 28 | MainZone | both_different | eos esse viptos ad fidei dogmata confirmanda | eos esse aptos ad fidei dogmata confirmanda. Cum vero | eos esse aptos ad fidei dogmata confirmanda. | 0.93 | 0.79 | 0.95 |
| LH_1_3_4_0002v-0001r | 30 | MainZone | both_different | sit quod ex horum fibrorum indigeat, videtar | sit, quod horum librorum indigeat, videt | sit, quod horum librorum indigeat, | 0.70 | 0.86 | 0.72 |
| LH_1_3_4_0002v-0001r | 31 | MainZone | theirs_only | cum vero | — | Cum vero | 0.88 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 44 | MainZone | both_different | cum libri Mosis et prophetarum sint liter | Cum libri Mosis et prophetarum sint | Cum libri Mosis et prophetarum sint lingua | 0.88 | 0.85 | 0.90 |
| LH_1_3_4_0002v-0001r | 45 | MainZone | both_different | lingua Hebraica para scripti, nec ut (exept | lingua Hebraica pura scripti, nec (excepto Dani | Hebraica pura scripti, nec (excepto | 0.70 | 0.76 | 0.68 |
| LH_1_3_4_0002v-0001r | 46 | MainZone | both_different | et alianca ad misur habeant credi | ele) chaldaica admista habeant, credi | chaldaica admista habeant, credi | 0.73 | 0.74 | 0.76 |
| LH_1_3_4_0002v-0001r | 52 | MainZone | both_different | exilicationem ejus | explicationem ejus versio | explicationem ejus | 0.94 | 0.68 | 0.94 |
| LH_1_3_4_0002v-0001r | 53 | MainZone | both_different | nc g0 interpretum | ne 70 interpretum | 70 interpretum | 0.76 | 0.88 | 0.76 |
| LH_1_3_4_0002v-0001r | 54 | MainZone | both_different | juvari dubium nullum est. | juvari dubium nullum | juvari dubium nullum est. | 1.00 | 0.83 | 1.00 |
| LH_1_3_4_0002v-0001r | 55 | MainZone | theirs_only | Esse adhuc quaedam quae in Cilgata | — | Esse adhuc quaedam quae in Vulgata | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 56 | MainZone | theirs_only | eu thanticum enim est cui tulo fidi posse publice statusum est | — | Authenticum enim est cui tuto fidi posse publice statutum est, | 0.90 | — | 0.92 |
| LH_1_3_4_0002v-0001r | 57 | MainZone | theirs_only | fortasse corcigi possint, non negant atesle qui | — | fortasse corrigi possint, non negant, catholici, | 0.79 | — | 0.83 |
| LH_1_3_4_0002v-0001r | 58 | MainZone | theirs_only | eam autpenticam | — | eam authenticam | 0.93 | — | 0.93 |
| LH_1_3_4_0002v-0001r | 59 | MainZone | theirs_only | dutumnatum eregri legentibus possit | — | periculum creari legentibus possit. | 0.69 | — | 0.71 |
| LH_1_3_4_0002v-0001r | 60 | MainZone | theirs_only | ntorqersionibus vutuaubus  hoc tantam statuta | — | De versionibus vulgaribus hoc t a n t u m statutum | 0.64 | — | 0.66 |
| LH_1_3_4_0002v-0001r | 61 | MainZone | theirs_only | Erolesa tegantur. Neque enim negari potest aliquando pert | — | Ecclesia legantur. Neque enim negari potest aliquando | 0.84 | — | 0.84 |
| LH_1_3_4_0002v-0001r | 62 | MainZone | theirs_only | es at nea promisne concedantur  | — | est ut non promiscue concedantur | 0.81 | — | 0.81 |
| LH_1_3_4_0002v-0001r | 63 | MainZone | theirs_only | fulherus prae(. in asalinos. slio | — | Lutherus praef. in psalmos. Scio | 0.76 | — | 0.77 |
| LH_1_3_4_0002v-0001r | 64 | MainZone | theirs_only | Hempndentisseinae lementatis eum qui | — | impudentissimae temeritatis eum qui | 0.78 | — | 0.78 |
| LH_1_3_4_0002v-0001r | 65 | MainZone | theirs_only | e e arotiteri aliquen seripturo liom | — | audeat profiteri aliquem scripturae librum | 0.67 | — | 0.67 |
| LH_1_3_4_0002v-0001r | 71 | MarginTextZone | theirs_only | Quotias cunque mihi animo propono | — | Quotiescunque mihi animo propono | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 72 | MarginTextZone | theirs_only | qualia dogmata essem ipse propositurus | — | qualia dogmata essem ipse propositurus | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 73 | MarginTextZone | theirs_only | si mihi e summa esset potestas | — | si mihi summa esset concessa | 0.77 | — | 0.77 |
| LH_1_3_4_0002v-0001r | 74 | MarginTextZone | theirs_only | statuendi oncta, rebus omibus expensu | — | statuendi, rebus omnibus expens | 0.78 | — | 0.78 |
| LH_1_3_4_0002v-0001r | 75 | MarginTextZone | theirs_only | e_ inclino  in dogmata Ecclesiae | — | is inclino ut nega in dogmata Ecclesiae | 0.77 | — | 0.74 |
| LH_1_3_4_0002v-0001r | 76 | MarginTextZone | theirs_only | Romanae conservanda,  | — | Romanae conservanda, | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 77 | MarginTextZone | theirs_only | etsic malta passim in ea tolem | — | etsi multa passim in ea toler | 0.90 | — | 0.90 |
| LH_1_3_4_0002v-0001r | 78 | MarginTextZone | theirs_only | corrigere tantum praxes quasdam | — | corrigerem tantum praxes quasdam | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 79 | MarginTextZone | theirs_only | a viris pris ac prudentibus apd | — | a viris piis ac prudentibus apud | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 80 | MarginTextZone | theirs_only | ipses ejus partis dudum improbatas | — | ipsos ejus partis dudum improbatas, | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 81 | MarginTextZone | both_different | quae adhuc in Eeclesia tomana | ubi in Ecclesia Romana | quae adhuc in Ecclesia Romana | 0.93 | 0.62 | 0.93 |
| LH_1_3_4_0002v-0001r | 83 | MarginTextZone | theirs_only | vitio temporumque passim toterantur | — | vitio temporum passim tolerantur. | 0.86 | — | 0.89 |
| LH_1_3_4_0002v-0001r | 84 | MarginTextZone | theirs_only | Si natus essem in Eeclesia | — | Si natus essem in Ecclesia | 0.96 | — | 0.96 |
| LH_1_3_4_0002v-0001r | 85 | MarginTextZone | theirs_only | Nomana profecto ab ea non recederem | — | Romana profecto ab ea non recederem, | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 86 | MarginTextZone | theirs_only | etsi omnia credersm, quae nunc | — | etsi omnia crederem, quae nunc | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 87 | MarginTextZone | theirs_only | credo | — | credo | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 90 | MarginTextZone | theirs_only | Pontificis antormtas quae multos | — | Pontificis autoritas quae multos | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 91 | MarginTextZone | theirs_only | maxime me certe omnium minita | — | maxime, me certe omnium minime | 0.90 | — | 0.93 |
| LH_1_3_4_0002v-0001r | 92 | MarginTextZone | theirs_only | deterret credo enim recto ejus | — | um est. enim recto ejus | 0.60 | — | 0.60 |
| LH_1_3_4_0002v-0001r | 93 | MarginTextZone | theirs_only | su nihil utilius ecclesiae posse | — | usu nihil utilius Ecclesiae posse | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 94 | MarginTextZone | theirs_only | Rebus omnibus expensis mihi vali | — | Rebus omnibus expensis mihi valde | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 95 | MarginTextZone | theirs_only | credibile videtur edituram aliquado | — | credibile videtur redituram aliquando | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 96 | MarginTextZone | theirs_only | Unionem Calesiarum in occidente | — | Unionem Ecclesiarum in occidente, | 0.88 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 97 | MarginTextZone | theirs_only | praesertum ubi in Eclesia Romana | — | praesertim ubi in Ecclesia Romana | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 98 | MarginTextZone | theirs_only | roformabuntur non fidei dogmata | — | reformabuntur non fidei dogmata | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 99 | MarginTextZone | theirs_only | Sed praxes quaedam male recepto | — | sed praxes quaedam male receptae | 0.91 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 100 | MarginTextZone | theirs_only | nec ub calesia ipsa approbatae | — | nec ab Ecclesia ipsa approbat | 0.83 | — | 0.83 |
| LH_1_3_4_0002v-0001r | 101 | NumberingZone | ours_only | u | unde peri | — | — | 0.11 | — |
| LH_1_3_4_0002v-0001r | 102 | MarginTextZone | theirs_only | clari legentibus possiu | — | creari legentibus possit. | 0.84 | — | 0.88 |
| LH_1_3_4_0002v-0001r | 103 | MarginTextZone | theirs_only | nullum inesse mendum unde pericu | — | nullum inesse mendum unde pericul | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 111 | MarginTextZone | both_different | debet saltem ae Biccu e | debet saltem – Bibliam ei ejus fieri. | debet saltem – Bi | 0.70 | 0.56 | 0.65 |

### Where they differ — concat:LH_1_3_4_0002r-0001v.xml + LH_1_3_4_0002v-0001r.xml

137 lines; the first 60 below, all in `data/philiumm/sample/comparison.csv`.

| file | # | zone | bucket | HTR line | this project | theirs | their score | HTR↔ours | HTR↔theirs |
|---|---:|---|---|---|---|---|---:|---:|---:|
| LH_1_3_4_0002r-0001v | 11 | MainZone | both_different | Brentius  in protgomenisq petium | Brentius in prolegomenis contra Petrum | Brentius in prolegomenis contra | 0.69 | 0.74 | 0.71 |
| LH_1_3_4_0002r-0001v | 21 | MainZone | theirs_only | haberi traditione Ecelesiae, prorsus quemadmodum | — | haberi traditione Ecclesiae, d | 0.60 | — | 0.60 |
| LH_1_3_4_0002r-0001v | 55 | MainZone | theirs_only | et pro octavo | — | et pro octavo | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 56 | MainZone | theirs_only |  a, suisto praerepla | — | a Christo praecepta, | 0.65 | — | 0.74 |
| LH_1_3_4_0002r-0001v | 67 | MainZone | both_different | sed divinitatis personas. diit christus | sed divinitatis personas. Et cum dicitur Christus | sed divinitatis personas. Et cum | 0.77 | 0.79 | 0.76 |
| LH_1_3_4_0002r-0001v | 68 | MainZone | both_different | est DEus versus est etristus est persona dulrimentis | est Deus, sensus est Christus est persona divinitatis. | est Deus, sensus est Christus est persona d | 0.69 | 0.81 | 0.73 |
| LH_1_3_4_0002r-0001v | 78 | MainZone | ours_only | ali quod necesse est esse inter Percipiens perceptiam | aliquod est inter personam percipientem et perceptam, qua | — | — | 0.48 | — |
| LH_1_3_4_0002r-0001v | 79 | MainZone | theirs_only | et perceptionem et perceptum. quae tamen | — | percipientem et perceptam, quae tamen | 0.78 | — | 0.79 |
| LH_1_3_4_0002r-0001v | 80 | MainZone | theirs_only | unum sunt peci personam percistientem | — | est inter personam percipientem | 0.68 | — | 0.68 |
| LH_1_3_4_0002r-0001v | 81 | MainZone | theirs_only | et perceptam, quae tamen  unum | — | et perceptam, quae tamen unum | 0.97 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 82 | MainZone | theirs_only | individuum sunt. | — | individuum sunt. | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 84 | MainZone | both_different | et  ircamatione, longe aptior | et unitate incarnatione, longe tutior aptior | incarnatione, longe tutior | 0.69 | 0.58 | 0.70 |
| LH_1_3_4_0002r-0001v | 107 | MainZone | both_different | Et cultum  magis e humanitatem hiiste | et cultum unio magis in humanitate Christi humanitatem | et cultum unio magis in humanitate | 0.59 | 0.59 | 0.58 |
| LH_1_3_4_0002r-0001v | 108 | MainZone | theirs_only | quam divinitatem Christi inmc haber | — | quam divinitatem Christi in animo habere | 0.85 | — | 0.85 |
| LH_1_3_4_0002r-0001v | 111 | MainZone | both_different | malo redeantur amimosque ad  | malo medeantur, animosque ad Deum | malo medeantur, animosque ad | 0.89 | 0.78 | 0.93 |
| LH_1_3_4_0002r-0001v | 118 | MainZone | both_different | apud Catholices. | apud Catholicos. Q | apud Catholicos. | 0.94 | 0.82 | 0.93 |
| LH_1_3_4_0002r-0001v | 119 | MarginTextZone | theirs_only | verbum seu id quod intelligifut, est | — | Verbum seu id quod intelligitur, est | 0.92 | — | 0.94 |
| LH_1_3_4_0002r-0001v | 120 | MarginTextZone | theirs_only | imago patris, quia pater vertum percipitus | — | imago patris, quia pater verbum percipiens | 0.93 | — | 0.93 |
| LH_1_3_4_0002r-0001v | 121 | MarginTextZone | theirs_only | in ipsum percipit quod ipse est, nempe | — | id ipsum percipit quod ipse est, nempe | 0.97 | — | 0.97 |
| LH_1_3_4_0002r-0001v | 122 | MarginTextZone | theirs_only | Montem illam quae se intelligit. Percrptio | — | Mentem illam quae se intelligit. Sententi | 0.83 | — | 0.83 |
| LH_1_3_4_0002r-0001v | 123 | MarginTextZone | theirs_only | ipsa est seu Amor est spiritus sanctus; diam | — | ipsa seu Amor est Spiritus Sanctus; Deum | 0.80 | — | 0.86 |
| LH_1_3_4_0002r-0001v | 124 | MarginTextZone | theirs_only | enim percipere se ipsum, idem est quod | — | enim percipere se ipsum, idem est quod | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 125 | MarginTextZone | theirs_only | se amare. Procedit autem a patre siliam | — | se amare. Procedit autem a Patre filio | 0.90 | — | 0.92 |
| LH_1_3_4_0002r-0001v | 126 | MarginTextZone | theirs_only | quia Amaeus et Amas etamatum amore | — | quia Amans et amatum amore | 0.74 | — | 0.74 |
| LH_1_3_4_0002r-0001v | 127 | MarginTextZone | theirs_only | non tempore quidem, rei tamen natara | — | non tempore quidem, rei tamen natura | 0.97 | — | 0.97 |
| LH_1_3_4_0002r-0001v | 128 | MarginTextZone | theirs_only | priora sunt. | — | priora sunt. | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 129 | MarginTextZone | theirs_only | Sciendum est autem | — | Sciendum est autem | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 130 | MarginTextZone | ours_only | et | est Sp | — | — | 0.33 | — |
| LH_1_3_4_0002r-0001v | 131 | MarginTextZone | theirs_only | in tota natura nullum,me nosse Ens | — | in tota natura nullum me nosse Ens | 0.97 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 132 | MarginTextZone | theirs_only | reale abstractum preter  perceptio | — | reale abstractum praeter cogita | 0.71 | — | 0.73 |
| LH_1_3_4_0002r-0001v | 133 | MarginTextZone | theirs_only | cogitratio percepsionem Nam | — | cogitatio (d) perceptionem. Nam | 0.77 | — | 0.86 |
| LH_1_3_4_0002r-0001v | 134 | MarginTextZone | theirs_only | modum esse modae n tantum alibi. | — | motum esse modum tantum alibi | 0.81 | — | 0.84 |
| LH_1_3_4_0002r-0001v | 135 | MarginTextZone | theirs_only | ostensum est | — | ostensum est. | 0.92 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 136 | MarginTextZone | theirs_only | Vim antu in corporibus | — | Vim autem in corporibus | 0.87 | — | 0.87 |
| LH_1_3_4_0002r-0001v | 137 | MarginTextZone | theirs_only | Graeci admittunt pietum | — | Graeci admittunt Spiritum | 0.88 | — | 0.88 |
| LH_1_3_4_0002r-0001v | 138 | MarginTextZone | theirs_only | procederi a patre. per silimus | — | procedere a patre per filiu | 0.83 | — | 0.86 |
| LH_1_3_4_0002r-0001v | 139 | MarginTextZone | theirs_only | quantum seiam | — | quantum sciam | 0.92 | — | 0.92 |
| LH_1_3_4_0002v-0001r | 2 | MainZone | theirs_only |  sutius est statuere in scriptua sacra | — | Tutius est statuere in scriptura sacra | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 3 | MainZone | theirs_only | nihil contineri nisi verbum Dei, nec autores librorum | — | nihil contineri nisi verbum Dei, nec autores librorum | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 4 | MainZone | theirs_only | etiam in his quae ad salutem nnon pertinent, qualia | — | etiam in his quae ad salutem non pertinent, qualia | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 5 | MainZone | theirs_only | sunt philosophica, chromologica, Geographica, | — | sunt philosophica, chronologica, Geographica, | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 6 | MainZone | theirs_only | Salsum dixisse. Errores autim si qui sunt libra | — | falsum dixisse. Errores autem si qui sunt, libra | 0.94 | — | 0.96 |
| LH_1_3_4_0002v-0001r | 7 | MainZone | theirs_only | riorum, culpa irrepsisde, aut a verbis male | — | riorum culpa irrepsisse, aut a verbis male | 0.95 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 8 | MainZone | theirs_only | intellectis nasci | — | intellectis nasci | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 9 | MainZone | theirs_only | In libis inditt Tobiae;, a equi | — | In libris Judith, Tobiae, | 0.58 | — | 0.66 |
| LH_1_3_4_0002v-0001r | 10 | MainZone | theirs_only | sapientiae, Maccabaeorum, nihil continetur | — | Sapientiae, Maccabaeorum, nihil continetur | 0.98 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 11 | MainZone | theirs_only | quod prohibeat eos intlanonicos censeri | — | quod prohibeat eos inter Canonicos censeri | 0.90 | — | 0.90 |
| LH_1_3_4_0002v-0001r | 12 | MainZone | theirs_only | ssi Licet autem fatendum sit sHicronusmum | — | . Licet autem fatendum sit Hieronymum | 0.83 | — | 0.80 |
| LH_1_3_4_0002v-0001r | 14 | MainZone | theirs_only | illam Canonicis debitam autoritatem non | — | illam Canonicis debitam autoritatem non | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 15 | MainZone | theirs_only | tribuisse, major tamen rcclesiae pars | — | tribuisse, major tamen Ecclesiae pars | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 16 | MainZone | theirs_only | pro camonicis eos invaluit tamen sententia | — | pro Canonicis eos invaluit tamen sententia | 0.95 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 17 | MainZone | theirs_only | in Eeclesia ut pro fanonicis haberentur | — | in Ecclesia ut pro Canonicis haberentur | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 18 | MainZone | theirs_only | tamen communior sententia veteris | — | communis communior sententia veteris | 0.83 | — | 0.83 |
| LH_1_3_4_0002v-0001r | 19 | MainZone | theirs_only | Ecclesia videtur fuisse in contrarium, et | — | Ecclesia[e] videtur fuisse in contrarium, et | 0.93 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 20 | MainZone | theirs_only | proinde Ecclesia catholica traditionis constia | — | proinde Ecclesia Catholica traditionis conscia | 0.96 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 21 | MainZone | theirs_only | potuit statuere ut pro canonicis haberentur | — | potuit statuere ut pro Canonicis haberentur. | 0.95 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 22 | MainZone | theirs_only | certe nullae afferri possunt contra hos libros | — | Certe nullae afferri possunt contra hos libros | 0.98 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 23 | MainZone | theirs_only | satis graves dubitandi rationes qu et plerique | — | satis graves dubitandi rationes et pleraeque | 0.89 | — | 0.89 |
| LH_1_3_4_0002v-0001r | 24 | MainZone | theirs_only | quae afferuatur, in libros quosdam ab omnibus | — | quae afferuntur, in libros quosdam ab omnibus | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 25 | MainZone | theirs_only | Receptos possunt torqueri | — | receptos possunt torqueri. | 0.92 | — | 1.00 |

### Where they differ — concat:LH_1_3_4_0002v-0001r.xml + LH_1_3_4_0002r-0001v.xml

84 lines; the first 60 below, all in `data/philiumm/sample/comparison.csv`.

| file | # | zone | bucket | HTR line | this project | theirs | their score | HTR↔ours | HTR↔theirs |
|---|---:|---|---|---|---|---|---:|---:|---:|
| LH_1_3_4_0002v-0001r | 2 | MainZone | theirs_only |  sutius est statuere in scriptua sacra | — | Tutius est statuere in scriptura sacra | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 3 | MainZone | theirs_only | nihil contineri nisi verbum Dei, nec autores librorum | — | nihil contineri nisi verbum Dei, nec autores librorum | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 4 | MainZone | theirs_only | etiam in his quae ad salutem nnon pertinent, qualia | — | etiam in his quae ad salutem non pertinent, qualia | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 5 | MainZone | theirs_only | sunt philosophica, chromologica, Geographica, | — | sunt philosophica, chronologica, Geographica, | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 6 | MainZone | theirs_only | Salsum dixisse. Errores autim si qui sunt libra | — | falsum dixisse. Errores autem si qui sunt, libra | 0.94 | — | 0.96 |
| LH_1_3_4_0002v-0001r | 7 | MainZone | theirs_only | riorum, culpa irrepsisde, aut a verbis male | — | riorum culpa irrepsisse, aut a verbis male | 0.95 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 8 | MainZone | theirs_only | intellectis nasci | — | intellectis nasci | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 9 | MainZone | theirs_only | In libis inditt Tobiae;, a equi | — | In libris Judith, Tobiae, | 0.58 | — | 0.66 |
| LH_1_3_4_0002v-0001r | 18 | MainZone | both_different | tamen communior sententia veteris | tamen communis communior sententia veteris | communis communior sententia veteris | 0.83 | 0.79 | 0.83 |
| LH_1_3_4_0002v-0001r | 28 | MainZone | both_different | eos esse viptos ad fidei dogmata confirmanda | eos esse aptos ad fidei dogmata confirmanda. Cum vero | eos esse aptos ad fidei dogmata confirmanda. | 0.93 | 0.79 | 0.95 |
| LH_1_3_4_0002v-0001r | 30 | MainZone | both_different | sit quod ex horum fibrorum indigeat, videtar | sit, quod horum librorum indigeat, videt | sit, quod horum librorum indigeat, | 0.70 | 0.86 | 0.72 |
| LH_1_3_4_0002v-0001r | 31 | MainZone | theirs_only | cum vero | — | Cum vero | 0.88 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 44 | MainZone | both_different | cum libri Mosis et prophetarum sint liter | Cum libri Mosis et prophetarum sint | Cum libri Mosis et prophetarum sint lingua | 0.88 | 0.85 | 0.90 |
| LH_1_3_4_0002v-0001r | 45 | MainZone | both_different | lingua Hebraica para scripti, nec ut (exept | lingua Hebraica pura scripti, nec (excepto Dani | Hebraica pura scripti, nec (excepto | 0.70 | 0.76 | 0.68 |
| LH_1_3_4_0002v-0001r | 46 | MainZone | both_different | et alianca ad misur habeant credi | ele) chaldaica admista habeant, credi | chaldaica admista habeant, credi | 0.73 | 0.74 | 0.76 |
| LH_1_3_4_0002v-0001r | 52 | MainZone | both_different | exilicationem ejus | explicationem ejus versio | explicationem ejus | 0.94 | 0.68 | 0.94 |
| LH_1_3_4_0002v-0001r | 53 | MainZone | both_different | nc g0 interpretum | ne 70 interpretum | 70 interpretum | 0.76 | 0.88 | 0.76 |
| LH_1_3_4_0002v-0001r | 54 | MainZone | both_different | juvari dubium nullum est. | juvari dubium nullum | juvari dubium nullum est. | 1.00 | 0.83 | 1.00 |
| LH_1_3_4_0002v-0001r | 55 | MainZone | theirs_only | Esse adhuc quaedam quae in Cilgata | — | Esse adhuc quaedam quae in Vulgata | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 56 | MainZone | theirs_only | eu thanticum enim est cui tulo fidi posse publice statusum est | — | Authenticum enim est cui tuto fidi posse publice statutum est, | 0.90 | — | 0.92 |
| LH_1_3_4_0002v-0001r | 57 | MainZone | theirs_only | fortasse corcigi possint, non negant atesle qui | — | fortasse corrigi possint, non negant, catholici, | 0.79 | — | 0.83 |
| LH_1_3_4_0002v-0001r | 58 | MainZone | theirs_only | eam autpenticam | — | eam authenticam | 0.93 | — | 0.93 |
| LH_1_3_4_0002v-0001r | 59 | MainZone | theirs_only | dutumnatum eregri legentibus possit | — | periculum creari legentibus possit. | 0.69 | — | 0.71 |
| LH_1_3_4_0002v-0001r | 60 | MainZone | theirs_only | ntorqersionibus vutuaubus  hoc tantam statuta | — | De versionibus vulgaribus hoc t a n t u m statutum | 0.64 | — | 0.66 |
| LH_1_3_4_0002v-0001r | 61 | MainZone | theirs_only | Erolesa tegantur. Neque enim negari potest aliquando pert | — | Ecclesia legantur. Neque enim negari potest aliquando | 0.84 | — | 0.84 |
| LH_1_3_4_0002v-0001r | 62 | MainZone | theirs_only | es at nea promisne concedantur  | — | est ut non promiscue concedantur | 0.81 | — | 0.81 |
| LH_1_3_4_0002v-0001r | 63 | MainZone | theirs_only | fulherus prae(. in asalinos. slio | — | Lutherus praef. in psalmos. Scio | 0.76 | — | 0.77 |
| LH_1_3_4_0002v-0001r | 64 | MainZone | theirs_only | Hempndentisseinae lementatis eum qui | — | impudentissimae temeritatis eum qui | 0.78 | — | 0.78 |
| LH_1_3_4_0002v-0001r | 65 | MainZone | theirs_only | e e arotiteri aliquen seripturo liom | — | audeat profiteri aliquem scripturae librum | 0.67 | — | 0.67 |
| LH_1_3_4_0002v-0001r | 71 | MarginTextZone | theirs_only | Quotias cunque mihi animo propono | — | Quotiescunque mihi animo propono | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 72 | MarginTextZone | theirs_only | qualia dogmata essem ipse propositurus | — | qualia dogmata essem ipse propositurus | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 73 | MarginTextZone | theirs_only | si mihi e summa esset potestas | — | si mihi summa esset concessa | 0.77 | — | 0.77 |
| LH_1_3_4_0002v-0001r | 74 | MarginTextZone | theirs_only | statuendi oncta, rebus omibus expensu | — | statuendi, rebus omnibus expens | 0.78 | — | 0.78 |
| LH_1_3_4_0002v-0001r | 75 | MarginTextZone | theirs_only | e_ inclino  in dogmata Ecclesiae | — | is inclino ut nega in dogmata Ecclesiae | 0.77 | — | 0.74 |
| LH_1_3_4_0002v-0001r | 76 | MarginTextZone | theirs_only | Romanae conservanda,  | — | Romanae conservanda, | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 77 | MarginTextZone | theirs_only | etsic malta passim in ea tolem | — | etsi multa passim in ea toler | 0.90 | — | 0.90 |
| LH_1_3_4_0002v-0001r | 78 | MarginTextZone | theirs_only | corrigere tantum praxes quasdam | — | corrigerem tantum praxes quasdam | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 79 | MarginTextZone | theirs_only | a viris pris ac prudentibus apd | — | a viris piis ac prudentibus apud | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 80 | MarginTextZone | theirs_only | ipses ejus partis dudum improbatas | — | ipsos ejus partis dudum improbatas, | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 81 | MarginTextZone | both_different | quae adhuc in Eeclesia tomana | ubi in Ecclesia Romana | quae adhuc in Ecclesia Romana | 0.93 | 0.62 | 0.93 |
| LH_1_3_4_0002v-0001r | 83 | MarginTextZone | theirs_only | vitio temporumque passim toterantur | — | vitio temporum passim tolerantur. | 0.86 | — | 0.89 |
| LH_1_3_4_0002v-0001r | 84 | MarginTextZone | theirs_only | Si natus essem in Eeclesia | — | Si natus essem in Ecclesia | 0.96 | — | 0.96 |
| LH_1_3_4_0002v-0001r | 85 | MarginTextZone | theirs_only | Nomana profecto ab ea non recederem | — | Romana profecto ab ea non recederem, | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 86 | MarginTextZone | theirs_only | etsi omnia credersm, quae nunc | — | etsi omnia crederem, quae nunc | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 87 | MarginTextZone | theirs_only | credo | — | credo | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 90 | MarginTextZone | theirs_only | Pontificis antormtas quae multos | — | Pontificis autoritas quae multos | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 91 | MarginTextZone | theirs_only | maxime me certe omnium minita | — | maxime, me certe omnium minime | 0.90 | — | 0.93 |
| LH_1_3_4_0002v-0001r | 92 | MarginTextZone | theirs_only | deterret credo enim recto ejus | — | um est. enim recto ejus | 0.60 | — | 0.60 |
| LH_1_3_4_0002v-0001r | 93 | MarginTextZone | theirs_only | su nihil utilius ecclesiae posse | — | usu nihil utilius Ecclesiae posse | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 94 | MarginTextZone | theirs_only | Rebus omnibus expensis mihi vali | — | Rebus omnibus expensis mihi valde | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 95 | MarginTextZone | theirs_only | credibile videtur edituram aliquado | — | credibile videtur redituram aliquando | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 96 | MarginTextZone | theirs_only | Unionem Calesiarum in occidente | — | Unionem Ecclesiarum in occidente, | 0.88 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 97 | MarginTextZone | theirs_only | praesertum ubi in Eclesia Romana | — | praesertim ubi in Ecclesia Romana | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 98 | MarginTextZone | theirs_only | roformabuntur non fidei dogmata | — | reformabuntur non fidei dogmata | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 99 | MarginTextZone | theirs_only | Sed praxes quaedam male recepto | — | sed praxes quaedam male receptae | 0.91 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 100 | MarginTextZone | theirs_only | nec ub calesia ipsa approbatae | — | nec ab Ecclesia ipsa approbat | 0.83 | — | 0.83 |
| LH_1_3_4_0002v-0001r | 101 | NumberingZone | ours_only | u | unde peri | — | — | 0.11 | — |
| LH_1_3_4_0002v-0001r | 102 | MarginTextZone | theirs_only | clari legentibus possiu | — | creari legentibus possit. | 0.84 | — | 0.88 |
| LH_1_3_4_0002v-0001r | 103 | MarginTextZone | theirs_only | nullum inesse mendum unde pericu | — | nullum inesse mendum unde pericul | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 111 | MarginTextZone | both_different | debet saltem ae Biccu e | debet saltem – Bibliam ei ejus fieri. | debet saltem – Bi | 0.70 | 0.56 | 0.65 |

### Where they differ — regions

64 lines; the first 60 below, all in `data/philiumm/sample/comparison.csv`.

| file | # | zone | bucket | HTR line | this project | theirs | their score | HTR↔ours | HTR↔theirs |
|---|---:|---|---|---|---|---|---:|---:|---:|
| LH_1_3_4_0002r-0001v | 11 | MainZone | both_different | Brentius  in protgomenisq petium | Brentius in prolegomenis contra Petrum | Brentius in prolegomenis contra | 0.69 | 0.74 | 0.71 |
| LH_1_3_4_0002r-0001v | 21 | MainZone | theirs_only | haberi traditione Ecelesiae, prorsus quemadmodum | — | haberi traditione Ecclesiae, d | 0.60 | — | 0.60 |
| LH_1_3_4_0002r-0001v | 55 | MainZone | theirs_only | et pro octavo | — | et pro octavo | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 56 | MainZone | theirs_only |  a, suisto praerepla | — | a Christo praecepta, | 0.65 | — | 0.74 |
| LH_1_3_4_0002r-0001v | 63 | MainZone | both_different | de DEUM unum numero esse pro | em. Deum, unum numero esse pro | . Deum, unum numero esse pro | 0.79 | 0.93 | 0.89 |
| LH_1_3_4_0002r-0001v | 67 | MainZone | both_different | sed divinitatis personas. diit christus | sed divinitatis personas. Et cum dicitur Christus | sed divinitatis personas. Et cum | 0.77 | 0.79 | 0.76 |
| LH_1_3_4_0002r-0001v | 68 | MainZone | both_different | est DEus versus est etristus est persona dulrimentis | est Deus, sensus est Christus est persona divinitatis. | est Deus, sensus est Christus est persona d | 0.69 | 0.81 | 0.73 |
| LH_1_3_4_0002r-0001v | 78 | MainZone | ours_only | ali quod necesse est esse inter Percipiens perceptiam | aliquod est inter personam percipientem et perceptam, qua | — | — | 0.48 | — |
| LH_1_3_4_0002r-0001v | 79 | MainZone | theirs_only | et perceptionem et perceptum. quae tamen | — | percipientem et perceptam, quae tamen | 0.78 | — | 0.79 |
| LH_1_3_4_0002r-0001v | 80 | MainZone | theirs_only | unum sunt peci personam percistientem | — | est inter personam percipientem | 0.68 | — | 0.68 |
| LH_1_3_4_0002r-0001v | 81 | MainZone | theirs_only | et perceptam, quae tamen  unum | — | et perceptam, quae tamen unum | 0.97 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 82 | MainZone | theirs_only | individuum sunt. | — | individuum sunt. | 1.00 | — | 1.00 |
| LH_1_3_4_0002r-0001v | 84 | MainZone | both_different | et  ircamatione, longe aptior | et unitate incarnatione, longe tutior aptior | incarnatione, longe tutior | 0.69 | 0.58 | 0.70 |
| LH_1_3_4_0002r-0001v | 107 | MainZone | both_different | Et cultum  magis e humanitatem hiiste | et cultum unio magis in humanitate Christi humanitatem | et cultum unio magis in humanitate | 0.59 | 0.59 | 0.58 |
| LH_1_3_4_0002r-0001v | 108 | MainZone | theirs_only | quam divinitatem Christi inmc haber | — | quam divinitatem Christi in animo habere | 0.85 | — | 0.85 |
| LH_1_3_4_0002r-0001v | 111 | MainZone | both_different | malo redeantur amimosque ad  | malo medeantur, animosque ad Deum | malo medeantur, animosque ad | 0.89 | 0.78 | 0.93 |
| LH_1_3_4_0002r-0001v | 119 | MarginTextZone | theirs_only | verbum seu id quod intelligifut, est | — | Verbum seu id quod intelligitur, est | 0.92 | — | 0.94 |
| LH_1_3_4_0002r-0001v | 120 | MarginTextZone | theirs_only | imago patris, quia pater vertum percipitus | — | imago patris, quia pater verbum percipiens | 0.93 | — | 0.93 |
| LH_1_3_4_0002r-0001v | 121 | MarginTextZone | theirs_only | in ipsum percipit quod ipse est, nempe | — | id ipsum percipit quod ipse est, nempe | 0.97 | — | 0.97 |
| LH_1_3_4_0002r-0001v | 122 | MarginTextZone | theirs_only | Montem illam quae se intelligit. Percrptio | — | Mentem illam quae se intelligit. Sententi | 0.83 | — | 0.83 |
| LH_1_3_4_0002r-0001v | 132 | MarginTextZone | both_different | reale abstractum preter  perceptio | reale abstractum praeter cogita perceptionem (c) | reale abstractum praeter cogita | 0.71 | 0.72 | 0.73 |
| LH_1_3_4_0002r-0001v | 141 | NumberingZone | ours_only | z | Z | — | — | 1.00 | — |
| LH_1_3_4_0002v-0001r | 2 | MainZone | theirs_only |  sutius est statuere in scriptua sacra | — | Tutius est statuere in scriptura sacra | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 3 | MainZone | theirs_only | nihil contineri nisi verbum Dei, nec autores librorum | — | nihil contineri nisi verbum Dei, nec autores librorum | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 4 | MainZone | theirs_only | etiam in his quae ad salutem nnon pertinent, qualia | — | etiam in his quae ad salutem non pertinent, qualia | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 5 | MainZone | theirs_only | sunt philosophica, chromologica, Geographica, | — | sunt philosophica, chronologica, Geographica, | 0.98 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 6 | MainZone | theirs_only | Salsum dixisse. Errores autim si qui sunt libra | — | falsum dixisse. Errores autem si qui sunt, libra | 0.94 | — | 0.96 |
| LH_1_3_4_0002v-0001r | 7 | MainZone | theirs_only | riorum, culpa irrepsisde, aut a verbis male | — | riorum culpa irrepsisse, aut a verbis male | 0.95 | — | 0.98 |
| LH_1_3_4_0002v-0001r | 8 | MainZone | theirs_only | intellectis nasci | — | intellectis nasci | 1.00 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 18 | MainZone | both_different | tamen communior sententia veteris | tamen communis communior sententia veteris | communis communior sententia veteris | 0.83 | 0.79 | 0.83 |
| LH_1_3_4_0002v-0001r | 28 | MainZone | both_different | eos esse viptos ad fidei dogmata confirmanda | eos esse aptos ad fidei dogmata confirmanda. Cum vero | eos esse aptos ad fidei dogmata confirmanda. | 0.93 | 0.79 | 0.95 |
| LH_1_3_4_0002v-0001r | 30 | MainZone | both_different | sit quod ex horum fibrorum indigeat, videtar | sit, quod horum librorum indigeat, videt | sit, quod horum librorum indigeat, | 0.70 | 0.86 | 0.72 |
| LH_1_3_4_0002v-0001r | 31 | MainZone | theirs_only | cum vero | — | Cum vero | 0.88 | — | 1.00 |
| LH_1_3_4_0002v-0001r | 44 | MainZone | both_different | cum libri Mosis et prophetarum sint liter | Cum libri Mosis et prophetarum sint | Cum libri Mosis et prophetarum sint lingua | 0.88 | 0.85 | 0.90 |
| LH_1_3_4_0002v-0001r | 45 | MainZone | both_different | lingua Hebraica para scripti, nec ut (exept | lingua Hebraica pura scripti, nec (excepto Dani | Hebraica pura scripti, nec (excepto | 0.70 | 0.76 | 0.68 |
| LH_1_3_4_0002v-0001r | 46 | MainZone | both_different | et alianca ad misur habeant credi | ele) chaldaica admista habeant, credi | chaldaica admista habeant, credi | 0.73 | 0.74 | 0.76 |
| LH_1_3_4_0002v-0001r | 52 | MainZone | both_different | exilicationem ejus | explicationem ejus versio | explicationem ejus | 0.94 | 0.68 | 0.94 |
| LH_1_3_4_0002v-0001r | 53 | MainZone | both_different | nc g0 interpretum | ne 70 interpretum | 70 interpretum | 0.76 | 0.88 | 0.76 |
| LH_1_3_4_0002v-0001r | 55 | MainZone | theirs_only | Esse adhuc quaedam quae in Cilgata | — | Esse adhuc quaedam quae in Vulgata | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 56 | MainZone | theirs_only | eu thanticum enim est cui tulo fidi posse publice statusum est | — | Authenticum enim est cui tuto fidi posse publice statutum est, | 0.90 | — | 0.92 |
| LH_1_3_4_0002v-0001r | 57 | MainZone | theirs_only | fortasse corcigi possint, non negant atesle qui | — | fortasse corrigi possint, non negant, catholici, | 0.79 | — | 0.83 |
| LH_1_3_4_0002v-0001r | 58 | MainZone | theirs_only | eam autpenticam | — | eam authenticam | 0.93 | — | 0.93 |
| LH_1_3_4_0002v-0001r | 59 | MainZone | theirs_only | dutumnatum eregri legentibus possit | — | periculum creari legentibus possit. | 0.69 | — | 0.71 |
| LH_1_3_4_0002v-0001r | 60 | MainZone | theirs_only | ntorqersionibus vutuaubus  hoc tantam statuta | — | De versionibus vulgaribus hoc t a n t u m statutum | 0.64 | — | 0.66 |
| LH_1_3_4_0002v-0001r | 61 | MainZone | theirs_only | Erolesa tegantur. Neque enim negari potest aliquando pert | — | Ecclesia legantur. Neque enim negari potest aliquando | 0.84 | — | 0.84 |
| LH_1_3_4_0002v-0001r | 62 | MainZone | theirs_only | es at nea promisne concedantur  | — | est ut non promiscue concedantur | 0.81 | — | 0.81 |
| LH_1_3_4_0002v-0001r | 63 | MainZone | theirs_only | fulherus prae(. in asalinos. slio | — | Lutherus praef. in psalmos. Scio | 0.76 | — | 0.77 |
| LH_1_3_4_0002v-0001r | 64 | MainZone | theirs_only | Hempndentisseinae lementatis eum qui | — | impudentissimae temeritatis eum qui | 0.78 | — | 0.78 |
| LH_1_3_4_0002v-0001r | 65 | MainZone | theirs_only | e e arotiteri aliquen seripturo liom | — | audeat profiteri aliquem scripturae librum | 0.67 | — | 0.67 |
| LH_1_3_4_0002v-0001r | 67 | MainZone | ours_only | i | i | — | — | 1.00 | — |
| LH_1_3_4_0002v-0001r | 73 | MarginTextZone | both_different | si mihi e summa esset potestas | si mihi summa esset concessa potestas | si mihi summa esset concessa | 0.77 | 0.70 | 0.77 |
| LH_1_3_4_0002v-0001r | 76 | MarginTextZone | both_different | Romanae conservanda,  | Romanae conservanda, nec in ea | Romanae conservanda, | 1.00 | 0.66 | 1.00 |
| LH_1_3_4_0002v-0001r | 92 | MarginTextZone | both_different | deterret credo enim recto ejus | deterret, credo In libris | um est. enim recto ejus | 0.60 | 0.63 | 0.60 |
| LH_1_3_4_0002v-0001r | 93 | MarginTextZone | theirs_only | su nihil utilius ecclesiae posse | — | usu nihil utilius Ecclesiae posse | 0.94 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 94 | MarginTextZone | theirs_only | Rebus omnibus expensis mihi vali | — | Rebus omnibus expensis mihi valde | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 95 | MarginTextZone | theirs_only | credibile videtur edituram aliquado | — | credibile videtur redituram aliquando | 0.95 | — | 0.95 |
| LH_1_3_4_0002v-0001r | 96 | MarginTextZone | theirs_only | Unionem Calesiarum in occidente | — | Unionem Ecclesiarum in occidente, | 0.88 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 97 | MarginTextZone | theirs_only | praesertum ubi in Eclesia Romana | — | praesertim ubi in Ecclesia Romana | 0.94 | — | 0.94 |
| LH_1_3_4_0002v-0001r | 98 | MarginTextZone | theirs_only | roformabuntur non fidei dogmata | — | reformabuntur non fidei dogmata | 0.97 | — | 0.97 |
| LH_1_3_4_0002v-0001r | 99 | MarginTextZone | theirs_only | Sed praxes quaedam male recepto | — | sed praxes quaedam male receptae | 0.91 | — | 0.94 |
