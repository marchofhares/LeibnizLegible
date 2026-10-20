# The letter-pool test set: placement and draw (K2b Task 2)

695 German letters of the pool name a first witness in the GWLB's Leibniz collections with a `Bl.` range (the mixed-language letters with such a witness, 23, are counted apart and not used). Each was placed the way the GT factory localizes a piece: the work through the crosswalk's signature keys, the pages through the C2 resolver's folio labels; the store was opened read-only. A letter is dropped under the first reason that applies: no work in the store for its shelfmark, no folio-labelled canvas in its range, no recognised line on its pages, or a second text on its leaves named by the *Überlieferung* block. The draw (seed 20261019) takes every letter in Leibniz's hand (L) or his scribe's (l) and a sample of the correspondents' letters (K, k) of the same size, allocated over siglum and year in proportion to the pool, and splits the set once, stratified by siglum and year, into a selection half (K3 and K4 may choose a reader on it) and a test half (reported only). The set is frozen in `letterpool-testset.csv` (no text) and the texts under `data/kurrent/letterpool/` (CC BY-NC 4.0, nc bucket).

## Placement by reason

| reason | L | l | K | k | other | all |
|---|---:|---:|---:|---:|---:|---:|
| placed | 67 | 0 | 482 | 13 | 3 | **565** |
| no_work | 14 | 0 | 57 | 1 | 0 | **72** |
| no_canvas | 0 | 0 | 9 | 1 | 0 | **10** |
| no_lines | 0 | 0 | 0 | 0 | 0 | **0** |
| shared | 30 | 1 | 12 | 2 | 3 | **48** |

Placed: **565 letters on 1,782 pages with 76,230 recognised lines** (1,319,833 reference characters).

| year | placed letters | pages | lines |
|---|---:|---:|---:|
| 1708 | 10 | 44 | 1,843 |
| 1709 | 34 | 104 | 4,635 |
| 1710 | 17 | 44 | 1,613 |
| 1711 | 42 | 122 | 4,599 |
| 1712 | 31 | 76 | 2,372 |
| 1713 | 170 | 516 | 21,763 |
| 1714 | 76 | 232 | 9,004 |
| 1715 | 65 | 242 | 12,312 |
| 1716 | 120 | 402 | 18,089 |

## Disjointness

Pages shared with K2's German pieces (`data/kurrent/german_pieces.jsonl`): **0** on 0 letters. Pages shared with the PHILIUMM held-out pages (`reports/philiumm/heldout_pages.csv`): **0** on 0 letters.

## The draw

**134 letters, 386 pages, 18,815 recognised lines, 325,624 reference characters.**

380 distinct pages; 2 groups of drawn letters share pages (short pieces on one leaf: 1713-166, 1713-167 on 2; 1713-168, 1713-171, 1713-172 on 2). The metric's free prefix and suffix leave a neighbour's text uncharged.

| siglum | letters | pages | lines | selection half | test half |
|---|---:|---:|---:|---:|---:|
| K | 65 | 202 | 7,807 | 33 | 32 |
| L | 67 | 176 | 10,756 | 33 | 34 |
| k | 2 | 8 | 252 | 1 | 1 |

| year | letters | pages | lines | selection half | test half |
|---|---:|---:|---:|---:|---:|
| 1708 | 2 | 6 | 271 | 1 | 1 |
| 1709 | 10 | 26 | 998 | 5 | 5 |
| 1710 | 3 | 8 | 319 | 2 | 1 |
| 1711 | 6 | 14 | 404 | 3 | 3 |
| 1712 | 5 | 10 | 170 | 2 | 3 |
| 1713 | 48 | 132 | 5,943 | 24 | 24 |
| 1714 | 15 | 48 | 2,208 | 8 | 7 |
| 1715 | 19 | 64 | 4,102 | 10 | 9 |
| 1716 | 26 | 78 | 4,400 | 12 | 14 |

| half | letters | pages | lines | chars |
|---|---:|---:|---:|---:|
| selection | 67 | 186 | 7,696 | 138,942 |
| test | 67 | 200 | 11,119 | 186,682 |

*lines* are the recognised lines of the C1 run on the letters' pages, every one (nothing filtered); the metric of Task 3 aligns each letter's reference text to their concatenation. *pages* count canvases; a leaf is two.
