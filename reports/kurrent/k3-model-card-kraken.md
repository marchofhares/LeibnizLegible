# Model card (draft): k3-kraken

A Leibniz Kurrent reader for the German stratum of the Nachlass: the PHILIUMM project's kraken recognition model for Leibniz's Latin and French (FoNDUE-GD v2 fine-tuned; self-reported CER 8.33 %), fine-tuned on K2's German ground truth. **Machine output, not an edition**: the model's text is Vorausedition-grade machine transcription with per-line confidence and provenance, subordinate to the Akademie-Ausgabe; it is never a reading of record.

## Data statement

- **Base model:** FoNDUE-GD_v2_ft_Leibniz.safetensors (PHILIUMM) (CC BY 4.0; Zenodo 10.5281/zenodo.21457538).
- **Training lines:** 55,585 minted lines of the German pieces of the §70-expired Akademie-Ausgabe volumes, placed on the GWLB's scans by the factory (60,163 rows selected, 1,434 excluded: audit 215, bracket 1,154, math 32, noise 33); the text is the edition's reading text (CC BY 4.0 in this project's release as K2's lines are open-bucket), the images the GWLB's (Public Domain Mark 1.0). By reader: trocr-kurrent-xvi-xvii 50,720, v1 9,443.
- **Validation lines:** 3,133, whole pieces held out, page-disjoint, stratified by stratum and hand; checkpoints were chosen on them alone.
- **Never trained on:** the GWLB letter pool (CC BY-NC 4.0; evaluation only), the Dresdner Hofdiarium lines of the Kurrent Trace package (nc; evaluation only), PHILIUMM's held-out pages, K2's audit sheet lines.
- **Precision of the training lines: unmeasured.** K2's 200-line audit sheet (half in Leibniz's own hand) awaits its judge at the Leibniz-Edition; no verdict existed when this model was trained. The screen before training (the length ratio of the minted text to the reading and the alignment confidence against the band the Latin and French mint occupies) put leibniz 7.4 % of 1,949 lines, other 6.9 % of 47,647 lines outside the band.
- **Licence of this model:** open.

## Training

- Settings: `FoNDUE-GD_v2_ft_Leibniz-b2-lr0.0001-union-x8`; epochs 37, the best at epoch 36 (validation CER 15.56 %).
- Hardware: one GTX 1660 Ti (6 GB) under WSL2; 44.5 h of training.

## Error rates

| set | CER | 95 % interval | note |
|---|---:|---|---|
| letter pool, all 134 letters | 30.63 % | 26.54 %–34.50 % | unfiltered, philiumm policy |
| letter pool, test half | 33.60 % | 27.01 %–38.86 % | unfiltered, philiumm policy |
| letter pool, Leibniz's own hand (L) | 39.66 % | 34.73 %–43.88 % | unfiltered, philiumm policy |
| letter pool, the correspondents' hands (K/k) | 20.32 % | 16.84 %–24.58 % | unfiltered, philiumm policy |
| validation set | 15.56 % | — | the edition's text as reference; substitutions 43.42 %, insertions 10.72 %, deletions 45.86 % of the edits |
| Dresden (sanity) | 13.20 % | — | a 1673 chancery hand; a ranking, not a benchmark |

## Intended use

Reading the German pages of the digitised Leibniz Nachlass line by line for search and browsing (K4), with every line labelled machine output and its confidence shown; not a substitute for the Akademie-Ausgabe, not for other hands or centuries without measurement.

## Speed

52 ms a line on the GTX 1660 Ti as K1 measured it; reading every German page at K2's all-in throughput: 4.6 h.
