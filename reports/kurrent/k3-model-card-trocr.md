# Model card (draft): k3-trocr

A Leibniz Kurrent reader for the German stratum of the Nachlass: a TrOCR vision-encoder–decoder fine-tuned on German Kurrent of the 16th–18th centuries (Bern; the card reports test CER 5.4 %), fine-tuned on K2's German ground truth. **Machine output, not an edition**: the model's text is Vorausedition-grade machine transcription with per-line confidence and provenance, subordinate to the Akademie-Ausgabe; it is never a reading of record.

## Data statement

- **Base model:** dh-unibe/trocr-kurrent-XVI-XVII (MIT; https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII).
- **Training lines:** 55,596 minted lines of the German pieces of the §70-expired Akademie-Ausgabe volumes, placed on the GWLB's scans by the factory (60,163 rows selected, 1,434 excluded: audit 215, bracket 1,154, math 32, noise 33); the text is the edition's reading text (CC BY 4.0 in this project's release as K2's lines are open-bucket), the images the GWLB's (Public Domain Mark 1.0). By reader: trocr-kurrent-xvi-xvii 50,720, v1 9,443.
- **Validation lines:** 3,133, whole pieces held out, page-disjoint, stratified by stratum and hand; checkpoints were chosen on them alone.
- **Never trained on:** the GWLB letter pool (CC BY-NC 4.0; evaluation only), the Dresdner Hofdiarium lines of the Kurrent Trace package (nc; evaluation only), PHILIUMM's held-out pages, K2's audit sheet lines.
- **Precision of the training lines: unmeasured.** K2's 200-line audit sheet (half in Leibniz's own hand) awaits its judge at the Leibniz-Edition; no verdict existed when this model was trained. The screen before training (the length ratio of the minted text to the reading and the alignment confidence against the band the Latin and French mint occupies) put leibniz 7.4 % of 1,949 lines, other 6.9 % of 47,647 lines outside the band.
- **Licence of this model:** open.

## Training

- Settings: `adafactor-grad-ckpt-b8`; epochs 6, the best at epoch 5 (validation CER 11.84 %).
- Hardware: one GTX 1660 Ti (6 GB) under WSL2; 27.6 h of training.

## Error rates

| set | CER | 95 % interval | note |
|---|---:|---|---|
| letter pool, all 134 letters | 28.61 % | 24.61 %–32.55 % | unfiltered, philiumm policy |
| letter pool, test half | 31.55 % | 25.29 %–36.76 % | unfiltered, philiumm policy |
| letter pool, Leibniz's own hand (L) | 36.68 % | 31.89 %–41.01 % | unfiltered, philiumm policy |
| letter pool, the correspondents' hands (K/k) | 19.40 % | 15.69 %–23.83 % | unfiltered, philiumm policy |
| validation set | 11.84 % | — | the edition's text as reference; substitutions 41.96 %, insertions 21.12 %, deletions 36.92 % of the edits |
| Dresden (sanity) | 11.93 % | — | a 1673 chancery hand; a ranking, not a benchmark |

## Intended use

Reading the German pages of the digitised Leibniz Nachlass line by line for search and browsing (K4), with every line labelled machine output and its confidence shown; not a substitute for the Akademie-Ausgabe, not for other hands or centuries without measurement.

## Speed

181 ms a line on the GTX 1660 Ti as K1 measured it; reading every German page at K2's all-in throughput: 15.8 h.
