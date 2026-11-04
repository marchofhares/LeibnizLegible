# Open-weight HTR models, engines and 2024–2026 evidence for reading 17th/18th-century German Kurrent (status: October 2026)

*What the project already has (not re-researched, used here only for comparison): a kraken fine-tune of PHILIUMM's FoNDUE-GD on Leibniz Latin/French (7.95 % CER on its validation split); dh-unibe/trocr-kurrent-XVI-XVII at 37 % CER (honest 1708–1716 test set) and 49 % (Leibniz's own hand), now fine-tuned on ~55k aligned German lines (11.8 % CER, aligner-placed validation); the fgho Hanse TrOCR models; kraken PP-OCRv6; McCATMuS. Hardware: kraken 7.0.3, a GTX 1660 Ti (6 GB), and a 24 GB card rentable for days. In this file, "Estimate:" marks my own reasoning. Everything else comes from the cited source.*

## Q1. Which open-weight models exist for Kurrent or German historical handwriting (plus usable comparable-script bases), with licences and reported CERs?

### Takeaway
Few open-weight models target 17th/18th-century Kurrent, and the project already holds the strongest line-level one (dh-unibe XVI-XVII). Three base models are new since mid-2026 and worth testing:
- **kraken "Llama party"** (Apache-2.0): a page-wise, multilingual model that runs inside kraken 7.
- **LightOnOCR-3-1B-Historic-German-Handwriting** (CC BY-SA 4.0): a page-level VLM, mostly trained on 19th-century hands. It records deletions and insertions with inline marks.
- **UB Mannheim's kraken `german_handwriting`** (CC BY-SA 4.0): a kraken German-handwriting base whose training data includes 17th-century material.

The Nordic multi-century TrOCR models are Apache-2.0 bases for related Gothic cursive hands. All the reported CERs are in-domain. Out-of-domain numbers for the same models are many times worse.

### Cited Findings
**Kurrent- and German-specific models on Hugging Face**
- **dh-unibe/trocr-kurrent.**
  - Licence and base: MIT; base microsoft/trocr-base-handwritten.
  - Scope: "19th century German".
  - Data: 292,997 training, 7,513 eval and 15,817 test lines. Sources include the Zurich State Archives Regierungsratsprotokolle, Humboldt lecture notes (BBAW), the Eugen Huber diary, Semper material and the 19th-century Greifswald Konzilsprotokolle.
  - Results: eval CER 2.83 %, test CER 2.66 %.
  - Caveats: "has not been extensively tested". It accepts line images only, so pages must be segmented first (DH Bern segments with kraken).
  - [HF](https://huggingface.co/dh-unibe/trocr-kurrent)
- **dh-unibe/trocr-kurrent-XVI-XVII.**
  - Licence and base: MIT; base dh-unibe/trocr-kurrent.
  - Data: 16th–18th century, ~1,579,200 words, biased toward Swiss archives (StAZH Stillstandsprotokolle and Ratsmanuale, Königsfelden, Einsiedeln, Greifswald).
  - Results: eval CER 5.67 % and test CER 5.42 %, "evaluated against the same hands" on an automatic split.
  - A parallel public Transkribus PyLaia model, "German Kurrent 16th–18th", exists.
  - [HF](https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII)
- **The same XVI-XVII model out of domain:** 43.5 % CER on 164 test lines of a 1505 Hanserezess (Lübeck), evaluated 2026-06-06. [HF dataset](https://huggingface.co/datasets/jwidmer/kurrent-hanse-xvi-test-lines-with-evaluation)
- **fgho/trocr-hanseXVII-kurrent** (no licence in the card).
  - Base: fine-tuned from dh-unibe XVI-XVII.
  - Data: 17th-century north-German administrative records (Städtetage minutes, Lübeck Seegerichtsakten, Ratsprotokolle).
  - Results: best eval CER 0.40 %, test CER 3.82 %.
  - [HF](https://huggingface.co/fgho/trocr-hanseXVII-kurrent)
- **b-straub/LightOnOCR-3-1B-Historic-German-Handwriting.**
  - Licences: weights CC BY-SA 4.0 (ShareAlike because one training source is BY-SA). The base, LightOnOCR-3-1B, is Apache-2.0. The repository scripts are MIT.
  - What it does: whole-page recognition with no segmentation step, written line by line in reading order. Struck text is marked ⟦…⟧, insertions ⟨…⟩, underlines 〔…〕, super- and subscripts ⌈…⌉ / ⌊…⌋, and illegible spots ▨.
  - Training: vision encoder and projector only (409.6M of 1,005.6M parameters; the language model is frozen). 21,038 pages, 17.7M characters, from the 1790s to the mid-20th century, mostly 1820–1880.
    - 62.5 % of pages are Alfred Escher letters, covering 700+ writers.
    - French is about 8 % of pages, Latin under 1 %.
  - Results on 610 held-out pages: CER 4.74 %, order-tolerant CER 3.85 %, 91.5 % of words exact, 2 runaway pages. The stock LightOnOCR-3-1B scores 45.0 % CER.
  - Per source: Escher 3.01 %, StAZH minutes 0.90 %, DTA lecture notes 1.21 %, Basel land register 8.20 %, Nägeli letters 13.2 %, Humboldt manuscripts 28.4 % (21 % without its one runaway).
  - Compute: trained on 1× RTX PRO 6000 Blackwell, peak 88.6 GB, about 11 GPU-hours. In a few-shot test, 28 pages of an unseen hard corpus and 60 steps (~1 h) halved CER from 44 % to 25 %.
  - Inference:
    - vLLM on an RTX A4000: 7.0 s per page.
    - GGUF pair: 639 MB q8 text model plus 829 MB bf16 vision projector. The vision encoder must run in bf16, because in f16 it overflows and outputs only "!!!!".
    - The browser app needs about 1.8 GB of GPU memory.
  - [HF](https://huggingface.co/b-straub/LightOnOCR-3-1B-Historic-German-Handwriting); scripts at [GitHub (MIT)](https://github.com/b-straub/historic-htr-ocr)
- **slawa188/trocr-kurrent-galicia-lora** (MIT). A LoRA adapter (r=8) on dh-unibe/trocr-kurrent, trained on 57 lines from one Galician family archive (1840–1944). On 35 held-out lines, soft CER fell from 42.6 % to 37.8 %, an 11 % relative reduction. Trained on an Apple M4 with 24 GB. [HF](https://huggingface.co/slawa188/trocr-kurrent-galicia-lora)
- **Mir0da/HTR-VT-german.** No licence and no data or evaluation information. Described as the "German-model" of a HAW Hamburg bachelor thesis. [HF](https://huggingface.co/Mir0da/HTR-VT-german)

**Kurrent and German kraken models on Zenodo** (each is a ~16 MB CoreML `.mlmodel`)
- **Weil, "HTR model for German manuscripts trained from several datasets"** (`german_handwriting.mlmodel`).
  - Licence: CC BY-SA 4.0 (2023). Base: the print model `digitue_best`.
  - Ground truth: Tübingen Konsilien 1659–1665, Greifswald Konzilsprotokolle, READ Bozen (ICFHR 2016) and StABS Ratsbücher/Urfehdenbuch. Later rounds added the ubtue ground truth and the StAZH RRB Kurrent XIX set.
  - The wiki logs a `ketos pretrain` run on the large dataset.
  - No CER is stated on the record.
  - [Zenodo](https://doi.org/10.5281/zenodo.7933463); [UB Mannheim wiki](https://github.com/UB-Mannheim/kraken/wiki/Training-German-Handwriting)
- **Alze, "HTR model for German manuscripts in Kurrent writing"** v1.3.0 (CC BY 4.0, 2026-08-01). Fine-tuned from Weil's model on only 12 pages of one travel diary by Louise Le Beau. No CER. The record lists clusters of letters the model confuses, such as a/e/c/n/r/u/m/i, p/g/z, f/ſ/h and k/t. [Zenodo](https://doi.org/10.5281/zenodo.21747522)
- **Kuhn, "Fanny loves Wilhelm"** (CC BY 4.0, 2026). A single-hand fine-tune of Weil's model, made in eScriptorium, for Fanny Mendelssohn Hensel's letters. Reported only as "significantly better results on test-pages than the base model". [Zenodo](https://doi.org/10.5281/zenodo.18207676)
- **Baránek, "Bohemian provenance 19th century"** (CC BY 4.0, 2024). 62,000 lines, mostly German-language Jewish registers. No CER on the record. [Zenodo](https://doi.org/10.5281/zenodo.11673242)
- **Baden State Library, "Joseph von Laßberg"** (CC BY 4.0, 2024). Trained on 246 images of Laßberg's autographs. [Zenodo](https://doi.org/10.5281/zenodo.14534740)
- **"Regg.F.III-damaged"** (CC BY 4.0, 2026-10-12). Water-damaged 15th-century Early New High German, using TRIDIS v2 as base. CER 2.3 %. [Zenodo](https://doi.org/10.5281/zenodo.23313428)
- **FoNDUE-GD v2.1** (CC BY 4.0, 2026-07-24; the project's base). Its training table includes:
  - German: StAZH 19th century (94,201 lines), Swiss Federal Council, Meyer von Schauensee 18th century (9,303 lines), Basler Urfehdebuch 16th century, and 16th/17th-century "Crimes et châtiments".
  - Dutch: IJSBERG (259,517 lines) and REPUBLIC.
  - Latin: PHILIUMM (13,049 lines).
  - [Zenodo](https://doi.org/10.5281/zenodo.21536798)
- **Licence flag:** the Zenodo record of PHILIUMM's Leibniz fine-tune lists **CC BY-NC 4.0** ([Zenodo](https://doi.org/10.5281/zenodo.21457538)). The project's own B1 report says the PHILIUMM model was "released CC BY 4.0" ([Zenodo](https://doi.org/10.5281/zenodo.22782817)).

**Multilingual base models that cover German**
- **kraken "Llama party" base.**
  - Licence and location: Apache-2.0; Zenodo DOI 10.5281/zenodo.20642057 (2026-06-11), mirrored on HF as small-models-for-glam/kraken-party-base.
  - Architecture: a Swin-base encoder (ImageNet-22k initialisation) and a ~40M-parameter Llama decoder with byte-level tokenisation, pretrained on the historical subset of Common Corpus. The model is prompted with line positions, either boxes or baseline curves, so it works with both kinds of segmentation.
  - Held-out test CER by language: German 9.10 %, Latin 7.47 %, French 7.49 %, Swedish 6.10 %, German shorthand 4.22 %; micro-average 10.16 %.
  - German training sets include FONDUE-DE-MSS-16/18/19/20, the Dresdner Hofdiarium, Bullinger Gwalther ground truth, the Nuremberg letterbooks, the HTR Winter School 2025 Early Modern German set, mkn-kurrent-gt and Gantner's Kurrent lines, plus printed material.
  - Caveats: "intended to be fine-tuned", and abbreviations are inconsistent across sources.
  - Trained on 5× A40 in BF16 (batch 16, gradient accumulation 16). Requires kraken ≥7.0 plus the `party` package from GitHub.
  - [HF mirror](https://huggingface.co/small-models-for-glam/kraken-party-base); [Zenodo](https://doi.org/10.5281/zenodo.20642057)
- **party README.**
  - Language tokens can steer the output language per line.
  - Fine-tuning: `party compile` (its datasets are not compatible with kraken's), then `party train --load-from-repo …` with `--prompt-mode curves|boxes`. `--freeze-encoder` "substantially" reduces training memory.
  - Inference runs through `kraken … ocr -m model.safetensors`. The base model download is 518.4 MB, and quantisation is not supported.
  - An older base model with language tokens is at 10.5281/zenodo.14616980.
  - [README](https://github.com/mittagessen/party); [Apache-2.0 LICENSE](https://github.com/mittagessen/party/blob/main/LICENSE)
- **kraken 7.1 PP-OCRv6 base models** (Apache-2.0, 2026-08-05; tiny / small / medium; the project already has this family):
  - German test (3,007 lines): CER 4.61 / 2.51 / 1.62 %.
  - Latin (5,748 lines): 14.03 / 9.12 / 6.45 %.
  - French: 14.02 / 10.01 / 7.56 %.
  - Training included synthetic data generated with pangoline. The models require kraken ≥7.1.0.
  - [kraken changelog](https://kraken.re/main/changelog.html); [HF mirror](https://huggingface.co/small-models-for-glam/kraken-ppocrv6-medium)
- **TRIDIS v2** (MIT).
  - Architecture: TrOCR-large with a historical RoBERTa decoder.
  - Data: 11th–16th-century documentary manuscripts (245k lines; the corpora include Königsfelden), plus 400k GAN-synthetic lines used in pretraining.
  - Results: about 5–10 % CER on three external unseen sets; claimed WER about 30 % lower than CRNN+CTC on the same data.
  - A kraken (CRNN) version is on Zenodo under MIT.
  - [HF](https://huggingface.co/magistermilitum/tridis_v2_HTR_historical_manuscripts); [Zenodo](https://doi.org/10.5281/zenodo.13862096)

**Comparable-script bases: Swedish and Finnish multi-century models**
- **Riksarkivet/trocr-base-handwritten-hist-swe-2, "Swedish Lion Libre".**
  - Licence and data: Apache-2.0; Swedish running-text handwriting, 1600–1900.
  - In-domain CER: as low as 0.75 %.
  - Out-of-domain archives: 2.50 % (1792) to 21.79 % (1654). Examples: 1690 6.11 %, 1716 6.50 %, 1723 11.40 %, 1679 14.22 %.
  - The card suggests fine-tuning on "20-50 letters".
  - [HF](https://huggingface.co/Riksarkivet/trocr-base-handwritten-hist-swe-2)
- **Kansallisarkisto/multicentury-htr-model.**
  - Licence and architecture: Apache-2.0; TrOCR-large; input 192×1024.
  - Data: more than 913k handwritten and typewritten lines, 16th–20th century, Finnish and Swedish.
  - Results: test CER 2.8 % on ~111,800 rows. The small variant scores 4.08 %.
  - [HF](https://huggingface.co/Kansallisarkisto/multicentury-htr-model); [HF small](https://huggingface.co/Kansallisarkisto/multicentury-htr-model-small)
- **Kansallisarkisto/multicentury-ppocrv6-medium** (Apache-2.0). Trained on 1,445,496 lines on 128 LUMI devices. In-domain HTR CER 6.12 %, against 54.55 % for stock PP-OCRv6. [HF](https://huggingface.co/Kansallisarkisto/multicentury-ppocrv6-medium)

**Not open, or nothing found**
- **Transkribus "supermodels" such as The Text Titan I** are TrOCR-based (TrHTR), available only through a paid subscription, and not meant for fine-tuning ([Crosilla et al.](https://arxiv.org/abs/2503.15195)). For Titan, "users cannot fine-tune it" ([Romein et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12202554/)).
- **Teklia PyLaia models:** the only German one, `pylaia-newseye-austrian` (MIT), is trained on 19th-century Austrian newspapers (print); validation CER 1.82 %. [HF](https://huggingface.co/Teklia/pylaia-newseye-austrian)
- **Loghi:** its suggested generic model targets 17th–18th-century Dutch handwriting. [README](https://github.com/knaw-huc/loghi)
- **PERO-OCR:** handwriting and Fraktur models are available on request from the authors, or through its web service and API. [README](https://github.com/DCGM/pero-ocr)

### Inferences
Each item below gets an estimated gain for this project and a hardware fit. All of it is estimation.

- **dh-unibe/trocr-kurrent (19th century).** Estimate: little gain. It is the parent of the model already fine-tuned, and its data is 150 years too late.
  - The in-domain versus out-of-domain gap explains why the project's 37 % sits so far above the card's 5.42 %. The same XVI-XVII model scored 43.5 % out of domain on the 1505 Hanserezess lines (jwidmer).
- **Kraken "Llama party" base.** Estimate: the most promising new base to run inside kraken.
  - Why: it is multilingual with per-line language tokens, which suits Leibniz's mixed Latin/French/German pages. It uses whole-page context, and its training includes 16th–18th-century German manuscripts (FONDUE-DE-MSS-16/18, Hofdiarium, Nuremberg letterbooks, Early Modern German).
  - Its 9.10 % German CER is a mixed manuscript-and-print figure, so it does not predict Leibniz performance.
  - Estimated outcome after fine-tuning on the project's PageXML: from parity to perhaps 10–30 % relative CER reduction against the current per-language models. Uncertainty is high.
  - Hardware: fine-tuning needs the rented 24 GB card. On 6 GB it might work only with `--freeze-encoder` and tiny batches.
  - The GTX 1660 Ti (Turing) has no bf16, so it would need fp32 or fp16. This is from my background knowledge, not verified here.
- **LightOnOCR-3-1B-Historic-German-Handwriting.** Estimate: zero-shot on 1690–1716 hands will probably be poor, perhaps 25–50 % CER, since even Humboldt's 1799 hand is at 28 %. As a base for fine-tuning, though, it is the only open model found that natively transcribes deletions and insertions on whole pages.
  - It also skips segmentation errors, which matters for Leibniz's heavily revised drafts.
  - The documented few-shot result (44 → 25 % with 28 pages) suggests large gains are possible. That requires page-level diplomatic ground truth (with revision marks and page reading order), which aligned line text may not provide.
  - Hardware: training is very heavy (88.6 GB peak at batch 8×4 with 6,144-token sequences). On 24 GB it needs batch 1, gradient checkpointing and possibly LoRA. Feasible but unverified.
  - Inference via GGUF should fit in 6 GB, but the bf16-only vision encoder is a risk on Turing (assumption).
  - Licence: ShareAlike (CC BY-SA 4.0) applies to derivatives.
- **Weil's `german_handwriting` kraken model** and its Kurrent derivatives. Estimate: a sensible kraken German base, an alternative to FoNDUE-GD for German lines, that fine-tunes easily on 6 GB.
  - Expect it to be a useful second opinion or ensemble member inside eScriptorium. It is unlikely to beat the 55k-line TrOCR fine-tune on its own.
- **Riksarkivet and Kansallisarkisto TrOCR models.** Swedish 17th–18th-century hands are German-style Gothic cursive (my background knowledge, not verified here).
  - Estimate: 0–10 % at best against continuing from the already-adapted dh-unibe model, because the decoder's language and charset don't match.
  - The TrOCR-large multicentury model would also need the 24 GB card.
- **TRIDIS, Regg.F.III and the Bohemian/Laßberg/Fanny models.** Estimate: wrong period or narrow single-collection scope, so negligible direct gain.

### Gaps
- No open model reports CER on 1680–1716 German letters, and none on Leibniz's hand. All candidates need the project's honest test set.
- No CER is published for Weil's `german_handwriting` (its `metadata.json` may hold training accuracy; not read).
- Not reviewed here:
  - fhswf/TrOCR_german_handwritten: AFL-3.0 per hub metadata, probably modern handwriting.
  - Riksarkivet's SATRN and Donut models.
  - HTRMoPo, kraken's model repository: htrmopo.org was blocked by the session proxy, so models listed only there may be missing.
- The licence of Loghi's generic model weights is not stated in its README.

## Q2. What do 2024–2026 benchmarks say about the best architecture for small historical datasets and for multilingual pages? Which open engines exist, under which licences?

### Takeaway
At line level on historical material, compact CTC recognisers still match or beat much larger transformer and VLM recognisers once both are fine-tuned:
- PyLaia (4.8M parameters) ties TrOCR-base (334M) on Bullinger.
- Fine-tuned PP-OCRv6 beats a fine-tuned Qwen3.5-9B line recognizer on medieval Latin.

Broad multilingual pretraining is what most improves generalisation. Zero-shot VLMs remain far behind on German historical hands. The best proprietary model (Gemini 3 Pro) still has 28.5 % CER on handwritten pages in a 2026 benchmark, and late-2024 VLMs scored 71–80 % on READ2016. Page-level VLMs pay off only when fine-tuned on the target material.

### Cited Findings
- **BullingerDB** (Peer, Scius-Bertrand, Scheurer, Fischer; arXiv May 2026).
  - Data: 20,898 pages and 499,222 lines by 796 writers; about 80 % Latin, the rest mostly Early New High German with code-switching.
  - Total test CER: HTRFlor (0.8M parameters) 19.2 %, PyLaia (4.8M) 9.2 %, Retsinas et al. (7.4M) 9.8 %, TrOCR-base (334M) 9.1 %.
  - Writers not seen in training are harder for every model (TrOCR 9.6 % vs 8.2 % on frequent writers). "PyLaia attains similar CERs despite being considerably smaller."
  - The dataset is on Zenodo (record 19728926); no licence is stated on the page.
  - [arXiv](https://arxiv.org/abs/2605.30235)
- **Kiessling, "A Free Lunch? Adapting PP-OCRv6 for Historical Text Recognition"** (arXiv, Sept 2026).
  - General models were pretrained on about 6.2M real lines in 37 languages plus about 1M synthetic lines.
  - Held-out macro CER: kraken CRNN 12.41 % vs PP-OCRv6 medium 7.15 %. Micro CER: 10.84 % vs 7.03 %.
  - After fine-tuning on CATMuS, PP-OCRv6 medium beats Medusa, a Qwen3.5-9B line recognizer: Latin 8.70 vs 13.07 %, French 3.36 vs 3.74 %, Spanish 7.99 vs 11.19 %.
  - The medium model is about 45× faster than Medusa. Training ran on A40s.
  - "VLMs often struggle with historical hands and diplomatic transcription norms."
  - [arXiv](https://arxiv.org/abs/2609.20064)
- **METATR v1.0** (TEKLIA; arXiv 2026), covering 29 languages.
  - Handwritten-document CER: Gemini 3 Pro 28.5 %, Claude Opus 4.5 31.2 %, Azure Layout 49.1 %, Qwen3-VL-8B 54.9 %, Churro-3B 58.1 %, GPT-5.1 59.5 %, PeroOCR 73.9 %, olmOCR-2 95.3 %, LightOnOCR-2-1B 255.7 %.
  - Conclusions: proprietary models are "the upper limit", open VLMs show higher variance, and traditional OCR "struggle[s] with multilingual and historical pages".
  - [arXiv](https://arxiv.org/abs/2605.26712)
- **Crosilla, Klic, Colavizza** (2025; zero-shot, page level, model versions of late 2024).
  - READ2016 (German, 15th–19th century, 50 pages): Text Titan I 40.63 %, Claude 3.5 Sonnet 71.17 %, GPT-4o 80.20 %, Qwen2-VL-7B 76.37 %.
  - ICDAR2017 (19th century, German/French/Italian): Titan 14.40 %, Claude 41.19 %.
  - LLM post-correction did not reliably help.
  - [arXiv](https://arxiv.org/abs/2503.15195)
- **Goethe- und Schiller-Archiv** (DHd 2026). Prior studies find multimodal LLMs inferior to Transkribus, especially on German Kurrent. MLLMs alone are "insufficient", but merging MLLM and HTR outputs may beat conventional HTR. [Zenodo](https://doi.org/10.5281/zenodo.19004817)
- **The project's own B1 report:** zero-shot frontier VLMs scored 36.6–78.7 % CER on PHILIUMM Leibniz validation lines (Latin/French), against 7.95 % for the fine-tuned kraken model. [Zenodo](https://doi.org/10.5281/zenodo.22782817)
- **Romein, Rabus, Leifert, Ströbel** (Int. J. Digital Humanities 2025).
  - On Republic (Dutch 1576–1795, 42,359 lines): HTR+ 1.78 %, PyLaia 3.89 %, IDA 3.54 % (3.05 % with a language model), fine-tuned TrOCR 3.97 %, Titan 3.61 %.
  - On German shorthand: IDA 9.53 %, fine-tuned TrOCR 9.70 %, PyLaia 11.90 %.
  - The authors say LSTM/CTC trains on comparatively small data while transformers appear to need large sets, though they did not test this directly.
  - Fine-tuning TrOCR took about 10 h on a V100 for ~40k lines.
  - [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12202554/)
- **HTR-VT** (Pattern Recognition 2025): line-level CER on READ2016 (Early Modern German, 8,349 training lines).
  - HTR-VT 3.9 % (53.5M parameters); DAN 4.1 %; VAN 4.1 %; FCN 4.6 %; plain ViT 8.5 %.
  - Code is Apache-2.0, trains on one RTX 4090 (24 GB), and checkpoints are on Google Drive.
  - [arXiv](https://arxiv.org/abs/2409.08573); [GitHub](https://github.com/YutingLi0606/HTR-VT)
- **HTR-ConvText** (arXiv 2512.05021).
  - CER: READ2016 3.6 %, IAM 4.0 %, LAM 2.7 %; about 65.9M parameters; CTC decoding at inference.
  - Licence conflict: the HF card says Apache-2.0 but the GitHub LICENSE is GPL-3.0.
  - [HF](https://huggingface.co/DAIR-Group/HTR-ConvText); [GitHub LICENSE](https://github.com/DAIR-Group/HTR-ConvText/blob/main/LICENSE)
- **CHURRO-3B** (a Qwen2.5-VL-3B fine-tune).
  - Data: 99,491 pages from 155 corpora in 46 language clusters.
  - Results: normalised Levenshtein similarity of 70.1 % on handwritten and 82.3 % on printed pages, beating Gemini 2.5 Pro.
  - Licence: "qwen-research" (non-commercial).
  - [arXiv](https://arxiv.org/abs/2509.19768); [HF](https://huggingface.co/stanford-oval/churro-3B)
- **A Qwen3-VL-8B fine-tune on CATMuS medieval:** CER 37.78 % to 19.97 % on 100 test lines. No licence stated. [HF](https://huggingface.co/small-models-for-glam/Qwen3-VL-8B-catmus)
- **TrOCR with domain-specific augmentation** on 16th-century Latin (the Gwalther dataset): CER 1.86 % for a single model and 1.60 % for a 5-model voting ensemble. [arXiv](https://arxiv.org/abs/2508.11499)
- **Open engines and their licences:**
  - kraken 7.1.1: Apache-2.0 ([PyPI](https://pypi.org/project/kraken/)).
  - party: Apache-2.0 ([GitHub](https://github.com/mittagessen/party)).
  - PyLaia 1.1.2: MIT ([PyPI](https://pypi.org/project/pylaia/)).
  - Loghi / loghi-htr: MIT ([GitHub](https://github.com/knaw-huc/loghi)).
  - PERO-OCR 0.7.0: BSD-3-Clause ([PyPI](https://pypi.org/project/pero-ocr/)).
  - DAN: CeCILL-C ([GitHub](https://github.com/FactoDeepLearning/DAN)).
  - Calamari 2.3.1: GPL-3.0 ([PyPI](https://pypi.org/project/calamari-ocr/)).
  - HTRflow 0.2.6: EUPL-1.2 ([PyPI](https://pypi.org/project/htrflow/)).
  - Donut: MIT ([GitHub](https://github.com/clovaai/donut)).
  - DTrOCR: only an unofficial MIT re-implementation was found ([GitHub](https://github.com/arvindrajan92/DTrOCR)).
  - PaddleOCR 3.7.0: Apache-2.0 ([PyPI](https://pypi.org/project/paddleocr/)).
  - LightOnOCR-3 0.8B / 1B / 4B: Apache-2.0 ([HF](https://huggingface.co/lightonai/LightOnOCR-3-1B)).

### Inferences
- **Small data, line level.** Estimate: stay with fine-tuned line recognisers (TrOCR, kraken CRNN or PP-OCRv6, PyLaia) as the main engine. Gains will come mostly from:
  - better base models: broad multilingual pretraining like party or PP-OCRv6;
  - augmentation and ensembling;
  - writer adaptation.

  Switching architecture alone is unlikely to help much. On Bullinger, a 70× larger TrOCR equals PyLaia, and on READ2016 the CTC variants (HTR-VT, HTR-ConvText, DAN, VAN) lie within 0.5 CER points of each other.
- **Multilingual pages.** Estimate: models with explicit multilingual pretraining and language conditioning are the best-supported option. Party has per-line language tokens; PP-OCRv6 general models showed 12.4 → 7.2 % macro CER over the kraken CRNN.
- **HTR-VT and HTR-ConvText trained from scratch** on the 55k lines with a 24 GB rental: estimate 0–15 % relative gain over the current fine-tuned TrOCR, uncertain. These are research code bases with no kraken integration, and HTR-ConvText's licence is ambiguous.
- **VLMs.** Estimate: zero-shot VLMs are not a viable main recogniser for Leibniz's Kurrent. That follows from METATR's 28.5 % best handwritten CER, the 71–80 % READ2016 results from 2024 and the project's own 36.6–78.7 % on Leibniz lines. Their realistic use is a second opinion or merger (as in the GSA workflow), or fine-tuned page-level models (LightOnOCR historic).
  - CHURRO's non-commercial licence may conflict with an open-source project's licensing.

### Gaps
- The full 2023 Bullinger writer-adaptation numbers were not retrievable (the paper PDF returned 403).
- No 2024–2026 head-to-head of party, TrOCR and PP-OCRv6 on Early Modern German Kurrent letters was found.
- METATR's per-dataset table could not be mapped reliably to model columns from the PDF text, so per-model READ-2016 CERs are not reported here.
- DAN and PyLaia from TEKLIA's GitLab could not be checked: bot protection blocked access.

## Q3. Does self-supervised or synthetic-data pretraining give measurable gains, and at what compute?

### Takeaway
Self-supervised pretraining on unlabeled target-domain lines helps a lot when only 100–1,000 lines are labelled. At about 10k labelled lines the gain is gone, and transfer from a related labelled model beats it throughout. Synthetic handwriting pretraining is on average worse than pretraining on real data unless the synthetic lines closely resemble the target hand.

At the project's scale (55k aligned lines plus strong Kurrent bases), neither lever is likely to move CER much. The exception is writer-specific cases with very few labelled lines.

### Cited Findings
- **Kišš & Hradiš** (ICDAR 2024), pretraining on 1,141,566 unlabeled Bentham lines. Test CER with 100 / 1k / 10k labelled lines:

  | Starting point | 100 lines | 1k lines | 10k lines |
  |---|---|---|---|
  | From scratch | 23.36 % | 8.33 % | 2.75 % |
  | Feature-quantisation SSL | 10.09 % | 4.80 % | 2.91 % |
  | VICReg SSL | 19.58 % | 8.35 % | 3.60 % |
  | Transfer from a related labelled model | 5.87 % | 3.81 % | 2.27 % |

  Their conclusion: SSL "struggles to outperform transfer learning from closely related domains". The code (DCGM/pero-pretraining) is BSD-2-Clause. [arXiv](https://arxiv.org/abs/2405.00420); [GitHub](https://github.com/DCGM/pero-pretraining)
- **kraken keeps `ketos pretrain`** (self-supervised recognition pretraining) in 7.0, which now writes checkpoints. [kraken changelog](https://kraken.re/main/changelog.html). UB Mannheim ran `ketos pretrain` for its German handwriting model but published no figures on the gain. [Wiki](https://github.com/UB-Mannheim/kraken/wiki/Training-German-Handwriting)
- **Pippi, Cascianelli, Kermorvant, Cucchiara** (ICDAR 2023).
  - Pretraining on synthetic lines from a styled handwriting generator was on average worse than on real datasets.
    - Washington, 6 fine-tuning lines: IAM-pretrained 18.8 % vs synthetic 54.9 % (31.3 % with width adjustment and varied styles).
    - Saint Gall, 5 lines: Rodrigo-pretrained 14.4 % vs synthetic 18.8 %.
  - Training from scratch on fewer than 230 lines did not converge.
  - Both visual appearance and language similarity matter. ICFHR16 (German) was the most distant pretraining source for the Italian, English and Latin targets.
  - [arXiv](https://arxiv.org/abs/2305.02593)
- **TRIDIS v2** used 400k GAN-generated lines in pretraining, with no ablation reported. [HF](https://huggingface.co/magistermilitum/tridis_v2_HTR_historical_manuscripts)
- **kraken 7.1's PP-OCRv6 bases** include synthetic data rendered with pangoline, about 1M of roughly 7.2M training lines. [Changelog](https://kraken.re/main/changelog.html); [arXiv](https://arxiv.org/abs/2609.20064). Pangoline (Apache-2.0) renders text to PDF with parallel ALTO files. [GitHub](https://github.com/mittagessen/pangoline)
- **Jha, "Danish HTR Synthetic Lines (18th-century style)"** (CC BY 4.0, 2026). 160,000 line images in period hands, Kurrent and copperplate. Recommended alongside real data. No HTR gains reported. [Zenodo](https://doi.org/10.5281/zenodo.22093255)

### Inferences
- **SSL on the project's millions of unlabeled line crops.** Estimate: under 5 % relative CER change for the general German model, which already has 55k lines and a Kurrent-pretrained base. In Kišš & Hradiš, SSL gave no gain at 10k labelled lines, and transfer from a related labelled model won.
  - Compute (estimate): days on the 24 GB card for millions of lines.
  - It might help a writer-specific model only if verified Leibniz own-hand lines number in the tens to hundreds and no closely related labelled base exists, which is not the case here.
- **Rendered Kurrent-font synthetic lines.** Estimate: little or no gain in overall CER, given Pippi's findings and Kurrent fonts' distance from real 1700 hands. Possibly useful for rare signs or abbreviations underrepresented in real data. Cheap to try with pangoline on 6 GB.
- **Using the unlabeled data instead for pseudo-labelling and self-training** is untested in the sources reviewed here. Estimate: probably more promising than SSL for this project.

### Gaps
- No study reports SSL or synthetic pretraining gains specifically for German Kurrent.
- Mitra et al. (WACV 2026, word-level, modern) and the April 2026 synthetic-to-real HTR paper (arXiv 2604.09713) were not reviewed.

## Q4. Are there approaches with reported results for one writer's hand with heavy revisions (writer adaptation, few-shot adaptation, style tokens)?

### Takeaway
Plain fine-tuning of a strong general model on a few dozen to a few hundred lines of the target writer, with augmentation, is the best-documented lever. It gives about 25 % relative CER reduction with 16 lines and about 50 % with 256 lines on new writers, and up to 82 % for distinct but source-like scripts such as Kurrent. Writer-style embeddings (AdaIN) gain less and do not generalise to unseen writers.

For heavy revisions, the only open model found that explicitly transcribes deletions and insertions is the page-level LightOnOCR historic-German fine-tune.

### Cited Findings
- **Kohút & Hradiš** (ICDAR 2023), fine-tuning a CTC CNN-LSTM on new writers with augmentation.
  - Average relative CER improvement: 25 % with 16 lines, 50 % with 256 lines.
  - The largest reductions, up to 82 %, came for "distinct yet to some extent source-like" scripts "such as Kurrent". Gothic averaged up to 60 %.
  - For easy, source-like hands: at most 10 %, and overfitting worsened CER by up to 15 % with few lines.
  - Augmentation consistently helped. The method is used in the PERO OCR web application.
  - [arXiv](https://arxiv.org/abs/2302.06308)
- **Kohút, Hradiš, Kišš** (ICDAR 2023), Writer Style Block (AdaIN on learned writer embeddings).
  - Writer-dependent best case: a 9.22 % relative CER reduction.
  - For new writers it did worse than the baseline when picking an existing embedding. It is "not suitable for writer-independent use", and simple fine-tuning was better at similar cost.
  - [arXiv](https://arxiv.org/abs/2302.06318)
- **Pippi et al.** (ICDAR 2023), single-writer fine-tuning with 5–15 lines.
  - Leopardi, 15 lines: best 12.7 % (LAM-pretrained), worst 38.7 % (German ICFHR16-pretrained).
  - Washington, 6 lines: best 18.8 % (IAM-pretrained).
  - Choosing the pretraining source matters most at 1–3 % of the data.
  - [arXiv](https://arxiv.org/abs/2305.02593)
- **Kiessling 2026**, manuscript-specific few-shot adaptation (20–240 lines, 300 steps).
  - The kraken CRNN improved with just 20 lines on all four manuscripts.
  - PP-OCRv6 needed 40–80 lines, but its absolute CER was lower.
  - [arXiv](https://arxiv.org/abs/2609.20064)
- **LightOnOCR historic German.**
  - Few-shot: 28 pages and 60 steps took CER from 44 % to 25 %.
  - Marks are less reliable than text: 324 of 92,796 validation words had a missing or wrong mark.
  - Page reading order is kept: insertions written away from their anchor come out as separate blocks. Whole struck passages are written as plain text without ⟦⟧.
  - [HF](https://huggingface.co/b-straub/LightOnOCR-3-1B-Historic-German-Handwriting)
- **Smaller single-collection results.**
  - A 57-line LoRA on TrOCR-Kurrent: 42.6 % to 37.8 % soft CER ([HF](https://huggingface.co/slawa188/trocr-kurrent-galicia-lora)).
  - A single-hand kraken fine-tune (Fanny Hensel): "significantly better" than its base, with no figures ([Zenodo](https://doi.org/10.5281/zenodo.18207676)).
- **The Bullinger writer-adaptation benchmark** (Scius-Bertrand et al., ICDAR 2023) covers 3,622 letters by 306 writers, with baselines before and after supervised and self-supervised adaptation. Figures not retrieved. [BORIS record](https://boris.unibe.ch/185720/)

### Inferences
- **Leibniz's own hand (49 % CER baseline).** Estimate: a dedicated writer-adaptation step is the best-supported lever. Take the project's best general model and fine-tune it on verified own-hand lines with augmentation.
  - Starting from the general fine-tune's own-hand error, expect roughly 20–40 % further relative reduction with about 100–300 verified lines. That is extrapolated from Kohút & Hradiš (Kurrent-like scripts benefit most).
  - Fits 6 GB for kraken/PP-OCRv6. TrOCR-base fits with LoRA or small batches.
  - It needs a writer-disjoint, honest test split: same-page evaluation inflates gains (Kiessling's few-shot sets are same-page).
- **Revisions (strikeouts, interlinear insertions).** Estimate: line recognisers will keep failing where the segmentation or line ground truth does not represent revisions.
  - A page-level model trained with revision marks (LightOnOCR historic as base) is the only open route found. Expect high payoff on draft pages but large ground-truth-conversion effort.
  - Style tokens or writer embeddings: not recommended, given the WSB results.

### Gaps
- No published writer-adaptation results on 17th/18th-century German autographs, nor on correction-heavy drafts.
- No open model reports accuracy on revision marks except LightOnOCR historic's mark-error count.

## Q5. Which of these could run inside kraken/eScriptorium, or beside them in the project's pipeline?

### Takeaway
Inside kraken:
- Party runs today on kraken ≥7.0 as a plugin-style recogniser fed by existing segmentation.
- kraken's PP-OCRv6 models need kraken ≥7.1.0, so the project's 7.0.3 must be upgraded.
- Weil's and the other Zenodo kraken models load directly.

eScriptorium's development branch already pins kraken 7.1. TrOCR-family models, LightOnOCR, CHURRO and HTR-VT run beside kraken: segment with kraken, recognise elsewhere, and write the text back to PageXML/ALTO.

### Cited Findings
- **kraken 7.0** (2026-04-07):
  - adds a plugin system (Python entry points) for external segmentation, recognition and reading-order models, used via `--model`;
  - adds batched GPU recognition;
  - produces checkpoints converted to safetensors;
  - separates `--load` (start a new fine-tuning run from weights) from `--resume`.

  kraken 7.0.3 added DDP for `ketos train`. Recognition models now pull lines from XML in the data type they were trained on (boxes or baselines). [kraken changelog](https://kraken.re/main/changelog.html)
- **kraken 7.1** (2026-08-05) adds the PP-OCRv6 architecture and its base models. [Changelog](https://kraken.re/main/changelog.html). The model cards state `kraken_version>=7.1.0`. [HF](https://huggingface.co/small-models-for-glam/kraken-ppocrv6-medium). The latest PyPI release is 7.1.1. [PyPI](https://pypi.org/project/kraken/)
- **Party** recognises only: it needs segmented PageXML or ALTO, runs through the `kraken … ocr` CLI, and its card states kraken ≥7.0. [README](https://github.com/mittagessen/party); [HF](https://huggingface.co/small-models-for-glam/kraken-party-base)
- **eScriptorium's develop branch** pins `kraken~=7.1.0` and the plugin `dfine-kraken~=0.4.3`. [requirements.txt](https://gitlab.com/scripta/escriptorium/-/raw/develop/app/requirements.txt)
- **TrOCR Kurrent models read line crops.** The DH Bern serving stack segments with kraken first. [HF](https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII). HTRflow (EUPL-1.2) chains segmentation and TrOCR models from YAML pipelines. [HF](https://huggingface.co/Riksarkivet/trocr-base-handwritten-hist-swe-2)
- **LightOnOCR historic German** runs under Transformers, vLLM or llama.cpp, or in the browser. It outputs page text with marks; `convert_output.py` converts that to TEI P5 or HTML. [HF](https://huggingface.co/b-straub/LightOnOCR-3-1B-Historic-German-Handwriting)

### Inferences
- **Practical integration order.** Estimate:
  1. Upgrade to kraken 7.1.x to match eScriptorium's develop pin, so the PP-OCRv6 bases can run.
  2. Pilot party with existing segmentation on a held-out set.
  3. Keep TrOCR (and possibly LightOnOCR) as side engines writing back into PageXML.
- **Whether eScriptorium's UI can train or run party models** was not verified. Plan on CLI-side party fine-tuning and inference, then import into eScriptorium.
- **Hardware summary.** Estimate:
  - kraken CRNN and PP-OCRv6: train on 6 GB.
  - Party, TrOCR-large, HTR-VT and LightOnOCR fine-tuning: need the rented 24 GB card. LightOnOCR also needs heavy memory-saving measures.
  - Inference for all except CHURRO and other 3B+ VLMs should fit 6 GB (CHURRO needs quantisation).
  - The 1660 Ti lacks bf16, which matters for party's recommended bf16 and LightOnOCR's bf16 vision encoder. This is background knowledge, unverified here.

### Gaps
- Whether eScriptorium exposes party or PP-OCRv6 training in its UI is unknown.
- No data was found on party fine-tuning memory use at given batch sizes or image sizes.
