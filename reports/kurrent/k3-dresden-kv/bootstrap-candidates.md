# Bootstrap readers for Kurrent: a ranking on Dresden

383 lines on 20 pages of the Dresdner Hofdiarium 1673 (Mscr.Dresd.K.117, Stefan Beckert's ground truth as the Kurrent Trace v0.1 package cuts it), read once by every candidate and scored by the B1 harness under its three normalisation policies — `philiumm` (NFD, whitespace collapsed; case and diacritics kept), `lenient` (case and diacritics folded), `strict` (NFC, whitespace as written) — with a 95 % bootstrap interval, and by the package's two scores (strict NFC; a reading policy that folds the long s to s and collapses whitespace), reimplemented on the same edit distance and, where the package's own script ran, confirmed by it. Device `cuda` (CUDA available); wall time per line includes image decoding and, for the first lines, model warm-up.

**A ranking, not a benchmark.** The Dresden lines are public and may sit in a candidate's training set; the hand is a chancery's of the 1670s, not Leibniz's or his correspondents'; and the text is nc-bucket material (the package applies CC BY-NC-SA 4.0 where Zenodo says CC BY 4.0), so this report carries numbers only — the readings and the references stay under `data/kurrent/smoke/`. The number that decides K2 is the pilot's yield on Leibniz's own German pages (Task 4).

## Character error rate by policy

| candidate | CER philiumm (95 % CI) | CER lenient | CER strict | WER philiumm | package strict NFC | package reading | exact lines | empty outputs | mean conf | ms/line | device |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| k3-trocr | 11.9 % (10.7 %–13.1 %) | 9.2 % | 12.0 % | 46.7 % | 12.1 % | 10.4 % | 51 | 0 | 0.908 | 152 | cuda:0 |
| k3-kraken | 13.2 % (12.1 %–14.3 %) | 10.4 % | 13.2 % | 55.3 % | 13.3 % | 11.6 % | 27 | 1 | 0.906 | 76 | cuda |

No vision row: neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` was set when the smoke test ran.

The package's own `scripts/evaluate.py` ran on the same readings; its strict and reading CER agree with the columns above to the printed precision for: `k3-trocr`, `k3-kraken`.

## Licences and provenance

| candidate | kind | source | licence | note |
|---|---|---|---|---|
| k3-trocr | trocr | K3: dh-unibe/trocr-kurrent-XVI-XVII fine-tuned on K2's German mint (runs row 615) | MIT (the base) · the fine-tune open | the whole model, Adafactor with gradient checkpointing, six epochs, the best on the frozen validation set |
| k3-kraken | kraken | K3: FoNDUE-GD_v2_ft_Leibniz fine-tuned on K2's German mint, the codec grown (runs row 614) | CC BY 4.0 (the base) · the fine-tune open | ketos from the PHILIUMM checkpoint, 37 epochs, stopped after checkpoint 36 |

The two `fgho` models state no licence on the Hub: they are evaluated here and nothing is built on them unless a licence appears. The Dresden text: see above. The crops' images carry the source's Public Domain Mark 1.0.

## Reading the table

- The `philiumm` policy is the project's headline (the B1 reproduction's); `strict` is the honest upper bound; `lenient` says how much is case and accents. The Dresden conventions keep u/v as written and distinguish the long s, so the package's reading policy (long s folded) is the kindest to a reader trained on modern s.
- Exact lines are under the package's reading policy. Empty outputs are lines a reader returned blank; they count as full deletions in every score.
- Mean confidence is each reader's own: kraken's mean character posterior, TrOCR's mean token probability. They are not on one scale across readers.
