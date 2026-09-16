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

## Second witness: the machine reading

For every judged line the folded similarity between the minted text and the HTR reading of the same strip was computed. 6 of the 8 non-*correct* verdicts sit on lines where the two agree at ≥ 0.8, i.e. the machine read the same words the edition gives; **6 verdicts are listed for re-checking.** The machine reading is not ground truth, but it is an independent reader of the strip, and a *wrong* it contradicts this strongly is more often a misjudged verdict than a misaligned line.

| # | ref | stratum | verdict | agreement | minted text | HTR reading | why re-check |
|---|---|---|---|---:|---|---|---|
| 1 | `DE-611-HS-862260:0064:004` | fair_copy | wrong | 0.89 | a fait deux personnes, page 513 en 1053) | a fait deuae versonnes, age 513. en 1053.) | machine reading agrees at 0.89: likely the same line |
| 2 | `00068377:0548:015` | fair_copy | wrong | 0.86 | veüe, à droitfe] ny à gauche, mais avec toutte | verie, adroit ny a gaucme, mais avec toutte | machine reading agrees at 0.86: likely the same line |
| 3 | `DE-611-HS-860628:0257:012` | fair_copy | wrong | 0.82 | donnée au Rd Pere Verjus qui | dovnće au a. Pere Verjus quis | machine reading agrees at 0.82: likely the same line |
| 4 | `DE-611-HS-974894:0243:031` | fair_copy | wrong | 0.98 | but, qu’il seroit trop long de rapporter icy. | but, qu’il seroit trop long de rapporter ici. | machine reading agrees at 0.98: likely the same line |
| 5 | `00068377:1270:027` | fair_copy | wrong | 0.93 | la difficulté demeure toujours à multiplier cette presence | la diffienete demeuve toujours à multiplier cette presence | machine reading agrees at 0.93: likely the same line |
| 6 | `00068377:0963:001` | fair_copy | unreadable | 0.88 | laquelle je suis | eaquelle ce suis | machine reading agrees at 0.88: likely the same line |
