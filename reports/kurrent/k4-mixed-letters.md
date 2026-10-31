# What reading a mixed page whole costs: the letter pool's mixed letters

K4 reads every German page whole with the Kurrent reader, Latin and French passages included. On the letter pool (134 letters, `philiumm` policy, the per-letter scores of `reports/kurrent/k3-letterpool/letterpool-eval-letters.csv`) a letter is *mixed* when the identifier says mixed, or Latin and French hold ≥ 0.25 of the stopword hits of its reference text: **2 mixed letters, 132 German ones**. The Latin-and-French share of the hits over the letters: quartiles 0.00 / 0.00 / 0.01.

| group | reader | letters | lines | reference chars | CER (pooled) | median letter CER |
|---|---|---:|---:|---:|---:|---:|
| mixed | v1 | 2 | 217 | 4,711 | 39.1 % | 42.0 % |
| mixed | k3-trocr | 2 | 217 | 4,711 | 40.6 % | 38.5 % |
| german | v1 | 132 | 18,598 | 323,605 | 46.8 % | 42.9 % |
| german | k3-trocr | 132 | 18,598 | 323,605 | 28.4 % | 20.6 % |

**The gain of k3-trocr over v1** (pooled CER, points): on the German letters 18.3 %, on the mixed letters -1.6 %; the cost of reading the mixed letters whole is the difference, **19.9 %** of CER. A letter-level measure: the pool has no per-line reference text, so what a per-line choice between the two readings would recover is an open question (STATUS.md).
