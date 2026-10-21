# K2: the German pieces minted from the Bern Kurrent reading

The factory's alignment over the readings of `trocr-kurrent-xvi-xvii` for every German piece of the census (`data/kurrent/german_pieces.jsonl`), at the per-stratum thresholds (fair_copy 0.55, light_revision 0.62, heavy_revision 0.72, scrap 0.80, unknown 0.65) with the aligner's defaults (hyphens kept), the edition text from the cache — as a dry run, nothing written — beside what `gt_lines` holds for each piece's record today (the C2c re-mint from the stored v1 text, read by `record_id`). **The rule:** one reader per piece: the reader's mint replaces the stored one where it mints more lines at the same per-stratum gate; elsewhere the stored mint stays (a tie keeps it); a piece whose rows name this reader is re-minted by it. What the factory mints is the edition's text in either case; the reader only decides where a line is placed. Generated 2026-10-21.

## Lines read and skipped

The reading job's pages: 4,807 (the census's 4,734 and the factory's 4,745 placement, united), 310,831 recognised lines once each.
Read: **310,831** of 310,831; skipped 0; left unread 0. Model `dh-unibe/trocr-kurrent-XVI-XVII` on `cuda`, settings {"model": "dh-unibe/trocr-kurrent-XVI-XVII", "batch_size": 16, "dtype": "float32", "use_cache": true, "max_new_tokens": 160, "clean_up_spaces": true}; the last run 41,367 lines/h.
On the pieces: 2,148 records, 1,668 aligned (skipped: no_canvases 29, no_htr_lines 2, not_localizable 449); 390,548 lines on their pages (a page two pieces share counts for each), 390,417 of them with a reading by the reader (100.0 %).

## Yield at the factory's gate

*v1*: the rows `gt_lines` holds for the record today (the C2c re-mint from the stored text); *Bern*: the dry run over the reader's text; *conf*: the aligner's mean matched fraction over the minted lines; *won*: pieces the rule gives to each; *after K2*: the piece's lines once the rule is applied.

| group | pieces | lines | read | v1 minted | v1 yield | v1 conf | Bern minted | **Bern yield** | Bern conf | won: Bern | won: v1 | after K2 | yield after |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **all German records** (the skipped ones with 0 lines) | 2,148 | 390,548 | 390,417 | 42,278 | 10.8 % | 0.839 | 66,084 | **16.9 %** | 0.897 | 1,178 | 402 | 68,769 | 17.6 % |
| fair_copy | 4 | 114 | 114 | 46 | 40.4 % | 0.723 | 58 | **50.9 %** | 0.888 | 3 | 1 | 59 | 51.8 % |
| light_revision | 511 | 79,439 | 79,400 | 15,466 | 19.5 % | 0.832 | 21,195 | **26.7 %** | 0.917 | 390 | 108 | 21,516 | 27.1 % |
| heavy_revision | 1,122 | 305,405 | 305,313 | 26,532 | 8.7 % | 0.842 | 44,421 | **14.5 %** | 0.887 | 774 | 279 | 46,714 | 15.3 % |
| scrap | 31 | 5,590 | 5,590 | 234 | 4.2 % | 0.909 | 410 | **7.3 %** | 0.900 | 11 | 14 | 480 | 8.6 % |

### By hand

*own*: the piece is in its author's own hand (the catalogue's *eigh.* on the piece, `catalog/hands.py`); *partial*: an address, a correction or a postscript only; *other*: a scribe's; *Leibniz's hand*: *own* with no sender or Leibniz as sender.

| group | pieces | lines | read | v1 minted | v1 yield | v1 conf | Bern minted | **Bern yield** | Bern conf | won: Bern | won: v1 | after K2 | yield after |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| own | 137 | 36,565 | 36,562 | 2,967 | 8.1 % | 0.839 | 5,284 | **14.5 %** | 0.881 | 90 | 39 | 5,530 | 15.1 % |
| partial | 467 | 100,692 | 100,651 | 10,447 | 10.4 % | 0.831 | 18,138 | **18.0 %** | 0.890 | 365 | 95 | 18,562 | 18.4 % |
| other | 1,064 | 253,291 | 253,204 | 28,864 | 11.4 % | 0.842 | 42,662 | **16.8 %** | 0.902 | 723 | 268 | 44,677 | 17.6 % |
| **Leibniz's hand** | 54 | 19,896 | 19,896 | 1,888 | 9.5 % | 0.834 | 2,490 | **12.5 %** | 0.890 | 32 | 21 | 2,714 | 13.6 % |

### By language

| group | pieces | lines | read | v1 minted | v1 yield | v1 conf | Bern minted | **Bern yield** | Bern conf | won: Bern | won: v1 | after K2 | yield after |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| German | 1,574 | 365,322 | 365,192 | 40,301 | 11.0 % | 0.836 | 62,059 | **17.0 %** | 0.897 | 1,132 | 361 | 64,374 | 17.6 % |
| mixed, German leading | 94 | 25,226 | 25,225 | 1,977 | 7.8 % | 0.900 | 4,025 | **16.0 %** | 0.902 | 46 | 41 | 4,395 | 17.4 % |

### By volume

`k2-mint-by-volume.csv` has the same rows.

| group | pieces | lines | read | v1 minted | v1 yield | v1 conf | Bern minted | **Bern yield** | Bern conf | won: Bern | won: v1 | after K2 | yield after |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| I,3 | 33 | 5,620 | 5,620 | 26 | 0.5 % | 0.899 | 30 | **0.5 %** | 0.865 | 11 | 11 | 41 | 0.7 % |
| I,6 | 87 | 16,345 | 16,338 | 1,709 | 10.5 % | 0.817 | 2,758 | **16.9 %** | 0.898 | 68 | 18 | 2,867 | 17.5 % |
| I,7 | 75 | 15,308 | 15,300 | 1,718 | 11.2 % | 0.838 | 2,154 | **14.1 %** | 0.893 | 53 | 21 | 2,229 | 14.6 % |
| I,8 | 59 | 11,584 | 11,581 | 906 | 7.8 % | 0.832 | 1,324 | **11.4 %** | 0.878 | 39 | 14 | 1,382 | 11.9 % |
| I,9 | 102 | 18,015 | 18,003 | 1,649 | 9.2 % | 0.838 | 2,681 | **14.9 %** | 0.897 | 82 | 18 | 2,765 | 15.3 % |
| I,10 | 101 | 17,444 | 17,438 | 1,591 | 9.1 % | 0.823 | 2,637 | **15.1 %** | 0.889 | 77 | 22 | 2,749 | 15.8 % |
| I,11 | 127 | 20,559 | 20,544 | 1,914 | 9.3 % | 0.833 | 2,973 | **14.5 %** | 0.897 | 87 | 38 | 3,145 | 15.3 % |
| I,12 | 103 | 15,165 | 15,160 | 1,443 | 9.5 % | 0.821 | 2,460 | **16.2 %** | 0.905 | 79 | 19 | 2,510 | 16.6 % |
| I,14 | 60 | 7,840 | 7,828 | 1,048 | 13.4 % | 0.821 | 1,924 | **24.5 %** | 0.902 | 51 | 9 | 1,968 | 25.1 % |
| I,15 | 109 | 16,271 | 16,260 | 2,209 | 13.6 % | 0.818 | 3,499 | **21.5 %** | 0.894 | 86 | 22 | 3,701 | 22.7 % |
| I,16 | 84 | 12,814 | 12,801 | 1,825 | 14.2 % | 0.818 | 2,983 | **23.3 %** | 0.918 | 72 | 12 | 3,031 | 23.7 % |
| III,1 | 10 | 1,422 | 1,421 | 135 | 9.5 % | 0.854 | 297 | **20.9 %** | 0.817 | 5 | 3 | 305 | 21.4 % |
| III,3 | 305 | 72,844 | 72,828 | 4,167 | 5.7 % | 0.846 | 8,710 | **12.0 %** | 0.876 | 193 | 82 | 9,153 | 12.6 % |
| III,4 | 206 | 47,263 | 47,252 | 4,621 | 9.8 % | 0.844 | 6,947 | **14.7 %** | 0.890 | 131 | 61 | 7,641 | 16.2 % |
| IV,1 | 26 | 29,003 | 29,003 | 6,180 | 21.3 % | 0.866 | 8,573 | **29.6 %** | 0.914 | 24 | 2 | 8,587 | 29.6 % |
| IV,2 | 9 | 5,864 | 5,864 | 766 | 13.1 % | 0.813 | 1,738 | **29.6 %** | 0.921 | 8 | 1 | 1,761 | 30.0 % |
| IV,3 | 131 | 58,961 | 58,950 | 8,749 | 14.8 % | 0.832 | 10,900 | **18.5 %** | 0.897 | 90 | 34 | 11,157 | 18.9 % |
| VI,3 | 29 | 15,386 | 15,386 | 989 | 6.4 % | 0.915 | 2,940 | **19.1 %** | 0.913 | 19 | 6 | 3,030 | 19.7 % |
| VI,4 | 12 | 2,840 | 2,840 | 633 | 22.3 % | 0.809 | 556 | **19.6 %** | 0.877 | 3 | 9 | 747 | 26.3 % |

## The pieces won by each reader

Of 2,148 German records, the rule gives **1,178** to the Bern reading, **402** keep the v1 mint, and 568 mint nothing under either (no lines at the gate, or no piece to align).

## The mint after K2, against before

Lines minted on the German records: **42,278 → 68,769** (58,991 aligned on the Bern reading on the pieces it won, replacing 32,500 v1 rows there; 9,778 v1 rows stay on the pieces it did not win). The whole store: 315,797 rows before, **342,288 expected** after the write — before the factory's ownership rule speaks (a line two records mint goes to the higher alignment confidence, so the written count can differ by a few; Task 3 reports the difference).

## The training set this leaves for K3

After the write, the German pieces carry 68,769 minted lines: 58,991 whose source names `reader trocr-kurrent-xvi-xvii` (select them by `gt_lines.source LIKE '%; reader trocr-kurrent-xvi-xvii;%'`, or by `record_id` from `data/kurrent/k2-decisions.jsonl`, `winner = bern`) and 9,778 from the v1 text on the pieces the rule left as they were (`winner = stored`). By stratum and by hand, the *after K2* column above; Leibniz's own hand: 2,714 lines on 54 pieces (2,187 of them on the Bern reading).

## What this measures, and what it does not

- Yield is minted lines over all recognised lines on the piece's pages; the pages carry other hands and other texts, and the edition omits or reorders what the page holds, so no reader reaches 100 %. The *v1* and *Bern* columns are measured on the same lines; the ordering is the measurement.
- The stored mint's lines were counted by `record_id` (the factory's ownership rule already applied: a line two records mint belongs to one); the dry run's pairs are the piece's own, before that rule. The expected store count is therefore an expectation.
- A high alignment confidence says the reader's text matches the edition's letters on that line; it does not say the slice landed on the right line, and TrOCR errs fluently. The side-by-side page (`data/kurrent/k2-side-by-side.html`) and the audit sheet (`data/kurrent/k2-audit.html`) are for that.
