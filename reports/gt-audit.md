# GT hand audit — C2 precision gate

Verdicts from `gt-audit-verdicts.csv` (200 sheet lines); stratum weights from `data/inventory.sqlite`.

**200 lines on the sheet · 20 judged · 180 left blank · 3 unreadable.**

**Corpus-weighted precision: 70.6 %** (strata weighted by their share of minted lines) — gate ≥ 95 %: **FAIL**.

| stratum | judged | correct | boundary | wrong | precision | 95 % CI | usable | weight |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| fair_copy | 17 | 12 | 0 | 5 | 70.6 % | 47–87 % | 70.6 % | 3.3 % |
| light_revision | 0 | 0 | 0 | 0 | — | — | — | 32.3 % |
| heavy_revision | 0 | 0 | 0 | 0 | — | — | — | 63.9 % |
| scrap | 0 | 0 | 0 | 0 | — | — | — | 0.4 % |
| **pooled (unweighted)** | 17 | 12 | 0 | 5 | 70.6 % | 47–87 % | 70.6 % | |

*precision* = correct ÷ (correct + boundary + wrong); *usable* also counts boundary-off lines (the right line, a word or more off at an end). Intervals are Wilson 95 %. Equal numbers were drawn per stratum, so the pooled row over-represents the rare strata; the weighted figure is the one to read.
