# K3: the evaluation, and the choice for K4

Two Leibniz Kurrent models fine-tuned on K2's German mint (55,596 training lines; 3,133 validation lines, page-disjoint, for the checkpoints), measured where nothing was tuned: the GWLB letter pool (K2b's frozen set, its metric and code: the letter's reference against every recognised line on its pages, nothing filtered; CC BY-NC 4.0, numbers only), Dresden as a sanity check, the validation set for the composition of the errors. CER under the `philiumm` policy with 95 % bootstrap intervals over letters. Generated 2026-10-26.

## The letter pool

| reader | all 134 letters | selection half | test half | Leibniz's hand (L) | the correspondents' (K/k) |
|---|---:|---:|---:|---:|---:|
| v1 (K2b) | 46.6 % (43.3 %–49.5 %) | 44.5 % (41.4 %–47.6 %) | 48.2 % (43.1 %–52.4 %) | 53.7 % (49.9 %–56.9 %) | 38.5 % (35.9 %–41.9 %) |
| philiumm (K2b) | 52.9 % (49.8 %–55.6 %) | 50.5 % (47.5 %–53.5 %) | 54.6 % (50.0 %–58.6 %) | 59.3 % (55.8 %–62.3 %) | 45.5 % (43.0 %–48.6 %) |
| trocr-kurrent-xvi-xvii (K2b) | 37.0 % (32.5 %–41.0 %) | 34.1 % (29.5 %–38.6 %) | 39.2 % (32.2 %–44.8 %) | 49.2 % (44.8 %–52.9 %) | 23.2 % (19.6 %–27.3 %) |
| trocr-hanse-xvi (K2b) | 35.6 % (31.2 %–39.6 %) | 32.3 % (27.8 %–36.7 %) | 38.0 % (31.1 %–43.7 %) | 46.7 % (42.1 %–50.7 %) | 22.8 % (19.3 %–27.1 %) |
| trocr-hanse-xvii (K2b) | 38.9 % (34.6 %–42.8 %) | 35.8 % (31.3 %–40.1 %) | 41.2 % (34.6 %–46.6 %) | 49.8 % (45.3 %–53.5 %) | 26.4 % (22.7 %–30.8 %) |
| **k3-trocr** | **28.6 % (24.6 %–32.5 %)** | **24.7 % (21.0 %–28.3 %)** | **31.6 % (25.3 %–36.8 %)** | 36.7 % (31.9 %–41.0 %) | 19.4 % (15.7 %–23.8 %) |
| **k3-kraken** | **30.6 % (26.5 %–34.5 %)** | **26.6 % (23.0 %–30.4 %)** | **33.6 % (27.0 %–38.9 %)** | 39.7 % (34.7 %–43.9 %) | 20.3 % (16.8 %–24.6 %) |

Lines read, counted per letter (an empty reading counts as deleted): k3-trocr 18,814 lines with a reading of 18,815 (105 ms a line in the read); k3-kraken 14,874 lines with a reading of 18,815 (11 ms a line in the read).

By year (the K3 models; letters per year as K2b drew them):

| year | k3-trocr | k3-kraken |
|---|---:|---:|
| 1708 | 19.5 % (7.9 %–24.9 %) | 22.5 % (9.2 %–28.7 %) |
| 1709 | 27.4 % (16.8 %–40.4 %) | 31.2 % (20.3 %–44.5 %) |
| 1710 | 21.2 % (19.8 %–25.3 %) | 22.2 % (20.2 %–28.3 %) |
| 1711 | 32.1 % (8.1 %–47.9 %) | 33.2 % (9.9 %–48.7 %) |
| 1712 | 11.3 % (8.0 %–14.8 %) | 15.5 % (11.0 %–20.3 %) |
| 1713 | 25.1 % (19.2 %–31.9 %) | 26.6 % (20.6 %–33.5 %) |
| 1714 | 29.5 % (20.3 %–37.9 %) | 30.8 % (22.1 %–38.8 %) |
| 1715 | 35.4 % (23.3 %–43.0 %) | 38.1 % (25.6 %–45.9 %) |
| 1716 | 28.3 % (23.5 %–33.3 %) | 30.3 % (24.8 %–35.7 %) |

## The validation set (the mint's own text as reference)

| model | CER (95 %) | Leibniz's hand | other hands | heavy | light | scrap | reader rows | v1 rows | sub / ins / del | tax |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| k3-trocr | 11.84 % (11.31 %–12.33 %) | 19.7 % | 11.4 % | 13.3 % | 8.3 % | 6.7 % | 10.9 % | 16.9 % | 42 % / 21 % / 37 % | 1.7 pts |
| k3-kraken | 15.56 % (15.05 %–16.09 %) | 23.8 % | 15.1 % | 17.8 % | 10.2 % | 5.0 % | 15.0 % | 18.9 % | 43 % / 11 % / 46 % | 1.8 pts |

Where the two models disagree on a validation line (2,935 of 3,133), one of them is exactly right on 13.5 % (k3-trocr 325, k3-kraken 70) — the number the C3 amendment asks for.

## Dresden (a chancery hand, a sanity check; nc, numbers only)

| reader | CER (95 %) | ms a line |
|---|---:|---:|
| k3-trocr | 11.9 % (10.7 %–13.1 %) | 181 |
| k3-kraken | 13.2 % (12.1 %–14.3 %) | 52 |

## Speed, and the time to read every German page

| model | ms a line (model, Dresden, as K1 measured) | all-in ms a line (K2's overhead added) | K2's 310,831 lines |
|---|---:|---:|---:|
| k3-trocr, the decoder's cache on (K2's setting) | 152 | 155 | 13.3 h |
| k3-trocr | 181 | 183 | 15.8 h |
| k3-kraken | 52 | 54 | 4.6 h |

## The choice for K4

the better letter-pool CER on the selection half, unless the faster model's selection-half CER lies within the better model's 95 % bootstrap interval there, in which case speed decides (every re-read of the German pages pays the speed difference).

- Best selection-half CER: **k3-trocr** at 24.7 % (21.0 %–28.3 %); the runner-up k3-kraken at 26.6 %.
- The faster model: **k3-kraken** (52 ms a line); within the margin (3.6 %): **yes**.
- **The rule's answer: k3-kraken.** The choice is the operator's; recorded in STATUS.md.

## The ablation

Planned, triggered by the screen (3,451 reader lines outside the band, the manifest's screen field; train-trocr --drop-screen / train-kraken --drop-screen), not run: the GPU time of the phase went to the two trainings. Pending for K3b with the audit verdicts.

## What this is not

- The precision of the training lines is unmeasured (K2's audit sheet awaits its judge); the screen's figures are in `k3-trainset.md`.
- The validation set is the mint's own text, so its numbers carry the mint's conventions; the letter pool is the honest German error rate.
