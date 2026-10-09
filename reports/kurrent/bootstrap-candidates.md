# Bootstrap readers for Kurrent: a ranking on Dresden

383 lines on 20 pages of the Dresdner Hofdiarium 1673 (Mscr.Dresd.K.117, Stefan Beckert's ground truth as the Kurrent Trace v0.1 package cuts it), read once by every candidate and scored by the B1 harness under its three normalisation policies — `philiumm` (NFD, whitespace collapsed; case and diacritics kept), `lenient` (case and diacritics folded), `strict` (NFC, whitespace as written) — with a 95 % bootstrap interval, and by the package's two scores (strict NFC; a reading policy that folds the long s to s and collapses whitespace), reimplemented on the same edit distance and, where the package's own script ran, confirmed by it. Device `cuda` (CUDA available); wall time per line includes image decoding and, for the first lines, model warm-up.

**A ranking, not a benchmark.** The Dresden lines are public and may sit in a candidate's training set; the hand is a chancery's of the 1670s, not Leibniz's or his correspondents'; and the text is nc-bucket material (the package applies CC BY-NC-SA 4.0 where Zenodo says CC BY 4.0), so this report carries numbers only — the readings and the references stay under `data/kurrent/smoke/`. The number that decides K2 is the pilot's yield on Leibniz's own German pages (Task 4).

## Character error rate by policy

| candidate | CER philiumm (95 % CI) | CER lenient | CER strict | WER philiumm | package strict NFC | package reading | exact lines | empty outputs | mean conf | ms/line | device |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| trocr-kurrent-xvi-xvii | 7.4 % (6.7 %–8.2 %) | 5.2 % | 7.5 % | 36.2 % | 7.6 % | 5.9 % | 120 | 0 | 0.963 | 334 | cuda:0 |
| trocr-hanse-xvi | 8.9 % (8.2 %–9.6 %) | 6.7 % | 9.0 % | 40.2 % | 9.1 % | 7.3 % | 88 | 0 | 0.927 | 209 | cuda:0 |
| trocr-hanse-xvii | 10.9 % (10.0 %–11.6 %) | 8.5 % | 10.9 % | 45.8 % | 11.1 % | 9.3 % | 55 | 0 | 0.941 | 337 | cuda:0 |
| philiumm | 29.5 % (28.2 %–30.9 %) | 26.3 % | 29.5 % | 79.2 % | 29.6 % | 28.1 % | 15 | 0 | 0.810 | 34 | cuda |
| mccatmus | 51.7 % (50.2 %–53.2 %) | 49.5 % | 51.7 % | 100.8 % | 51.8 % | 51.0 % | 6 | 0 | 0.807 | 19 | cuda |

No vision row: neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` was set when the smoke test ran.

The package's own `scripts/evaluate.py` ran on the same readings; its strict and reading CER agree with the columns above to the printed precision for: `philiumm`, `mccatmus`, `trocr-kurrent-xvi-xvii`, `trocr-hanse-xvii`, `trocr-hanse-xvi`.

## Licences and provenance

| candidate | kind | source | licence | note |
|---|---|---|---|---|
| philiumm | kraken | Zenodo 10.5281/zenodo.21457538 | CC BY 4.0 | the project's baseline: FoNDUE-GD_v2 fine-tuned on Leibniz's Latin and French |
| mccatmus | kraken | Zenodo 10.5281/zenodo.13788177 | CC BY 4.0 | McCATMuS v1: 22 datasets, mostly French, some German; 16th–21st c.; CoreML |
| trocr-kurrent-xvi-xvii | trocr | https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII | MIT | German Kurrent of the 16th–18th c., Swiss-biased; the card reports test CER 5.4 % |
| trocr-hanse-xvii | trocr | https://huggingface.co/fgho/trocr-hanseXVII-kurrent | none stated | 17th-c. north German administrative records; from the Bern model; evaluate only |
| trocr-hanse-xvi | trocr | https://huggingface.co/fgho/trocr-hanseXVI-kurrent | none stated | 16th-c. north German administrative records; from the Bern model; evaluate only |

The two `fgho` models state no licence on the Hub: they are evaluated here and nothing is built on them unless a licence appears. The Dresden text: see above. The crops' images carry the source's Public Domain Mark 1.0.

## Reading the table

- The `philiumm` policy is the project's headline (the B1 reproduction's); `strict` is the honest upper bound; `lenient` says how much is case and accents. The Dresden conventions keep u/v as written and distinguish the long s, so the package's reading policy (long s folded) is the kindest to a reader trained on modern s.
- Exact lines are under the package's reading policy. Empty outputs are lines a reader returned blank; they count as full deletions in every score.
- Mean confidence is each reader's own: kraken's mean character posterior, TrOCR's mean token probability. They are not on one scale across readers.
