# The print trial: a print layout model and a print OCR model on 100 Marginalien pages

M1 Task 1b, run 2026-11-18 on the desktop, the store read-only. The pages are the Marginalien block of the zone census sample (100 pages of 89 annotated printed books, drawn one page a book, 30 of them German print by the K4 language pass, the Fraktur question). Zones: kraken 7.1.1 with the D-FINE large region model trained on LADaS (37 SegmOnto classes, Apache-2.0; `ladas_l.safetensors`, MD5 `06aa34eacb02`), device cuda:0, on the census's 2,000 px copies, the coordinates scaled back to the scan. The printed-body lines are the store's v1 lines that lie mostly (half their pixels or more) inside a print zone; the OCR model is Gallicorpora+ (kraken, French print of the 16th to 19th century, release 1.0.0, CC0 repository) run through a PAGE XML of those lines on the full-resolution scan.

## Decision

**(a) the printed body is read with a print model and shown as such: roman 3.6% → (a) on the sheet. The fraktur half of the sheet is not transcribed yet, so this holds for the type scored; the other type's decision follows its transcription.**

## Zones per class

| class | group | zones | pages with it |
|---|---|---:|---:|
| MainZone-Entry | print | 195 | 11 (11.0 %) |
| MainZone-P | print | 129 | 44 (44.0 %) |
| RunningTitleZone | print | 93 | 63 (63.0 %) |
| MainZone-Continued | print | 70 | 55 (55.0 %) |
| MarginTextZone-Notes | print | 67 | 34 (34.0 %) |
| NumberingZone | print | 43 | 42 (42.0 %) |
| QuireMarksZone | print | 35 | 28 (28.0 %) |
| MainZone-Sp | print | 34 | 14 (14.0 %) |
| MainZone-Head | print | 27 | 19 (19.0 %) |
| MainZone-Signature | print | 27 | 13 (13.0 %) |
| StampZone-Sticker | other | 21 | 12 (12.0 %) |
| AdvertisementZone | print | 13 | 1 (1.0 %) |
| DropCapitalZone | print | 13 | 13 (13.0 %) |
| DigitizationArtefactZone | other | 12 | 12 (12.0 %) |
| GraphicZone | print | 12 | 9 (9.0 %) |
| MusicZone | print | 12 | 12 (12.0 %) |
| TitlePageZone | print | 12 | 9 (9.0 %) |
| MainZone-Lg | print | 8 | 6 (6.0 %) |
| MainZone-Maths | print | 8 | 5 (5.0 %) |
| StampZone | other | 8 | 8 (8.0 %) |
| GraphicZone-Decoration | print | 5 | 5 (5.0 %) |
| MarginTextZone-ManuscriptAddendum | manuscript | 5 | 4 (4.0 %) |
| MainZone-Other | print | 4 | 3 (3.0 %) |
| GraphicZone-Part | print | 1 | 1 (1.0 %) |
| MainZone-Date | print | 1 | 1 (1.0 %) |
| MainZone-ListItem | print | 1 | 1 (1.0 %) |

Pages with zones: 100 of 100. Pages with a `MarginTextZone-ManuscriptAddendum` zone, the class for a handwritten addition in a printed margin: 4 (4.0 %). Mean page area under print zones 34.7 %, under manuscript zones 0.0 %.

## The printed-body share

| type | pages | v1 lines | in print zones | in manuscript zones | other zones | outside | IoU of the print lines with the print zones (mean · median) |
|---|---:|---:|---:|---:|---:|---:|---|
| fraktur | 30 | 1,790 | 1,013 (56.6 %) | 1 (0.1 %) | 45 | 731 | 0.68 · 0.84 |
| roman | 70 | 3,791 | 2,450 (64.6 %) | 1 (0.0 %) | 13 | 1,327 | 0.74 · 0.82 |
| **all** | 100 | 5,581 | 3,463 (62.1 %) | 2 (0.0 %) | 58 | 2,058 | 0.72 · 0.83 |

### Against PHILIUMM's v2 zones on the same pages

PHILIUMM's model (trained on manuscripts) calls `MainZone` where LADaS calls the printed body and `MarginTextZone` where LADaS calls a manuscript addendum. On the 5,581 v1 lines of the pages both models saw: print by PHILIUMM 64.2 %, by LADaS 62.1 %; the same call on 3,968 lines (71.1 %); the IoU of the two models' print areas 0.80 (mean over pages).

| LADaS \\ PHILIUMM | lines |
|---|---:|
| print \\ print | 2,892 |
| outside \\ outside | 1,075 |
| outside \\ print | 647 |
| print \\ outside | 338 |
| outside \\ manuscript | 275 |
| print \\ other | 194 |
| outside \\ other | 61 |
| other \\ print | 42 |
| print \\ manuscript | 39 |
| other \\ outside | 16 |
| manuscript \\ manuscript | 1 |
| manuscript \\ outside | 1 |

## The Fraktur share

Over the Marginalien in the store (103,626 pages with a language verdict), the K4 pass calls 6,719 pages German (6.5 %): German print in these books is Fraktur as a rule, Latin and French print roman, so that share is the corpus's Fraktur share as far as a page's language says its type. The sample holds 30 German pages on purpose.

## The CER on 50 printed lines

| model | lines scored | CER (all) | roman | Fraktur |
|---|---:|---:|---:|---:|
| Gallicorpora+ (print) | 24 | 3.6 % | 3.6 % (24 lines) | pending |
| v1, the handwriting model | 24 | 14.9 % | 14.9 % (24 lines) | pending |

Normalisation: NFD · collapse-ws · strip; then abbreviation marks (macron, tilde, overline) dropped; ¬ and ⸗ read as -; ’ as '. The operator's transcriptions (data/print/transcriptions/print-sheet-transcriptions-2026-11-18.csv) are the reference; 24 of the 50 lines carry one. Without the fold the CER is 4.3 % for Gallicorpora+ and 15.2 % for v1.

## What this does and does not show

- The LADaS model was trained on French print of the 17th century to the present; its per-class scores on its own test set are low for several classes (the README beside the model). A zone here is its guess.
- The printed-body share is a share of v1 lines, which the handwriting segmenter drew; a printed line it split or merged counts as the segmenter left it.
- Fifty lines decide the CER within a few points at best; the roman and Fraktur halves are 25 lines each.
- Nothing was written to the store; the tools' licences are in the registry (`leibniz legal licences`).

Files: `print-trial-summary.json`, `print-trial-per-page.csv`, `print-trial-pages.csv`; the per-line calls under `data/print/print-trial-lines.csv`.
