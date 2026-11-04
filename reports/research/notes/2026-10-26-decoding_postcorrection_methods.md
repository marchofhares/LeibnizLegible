# Non-data levers for lowering CER of kraken 7.0.3 / TrOCR HTR on historical Latin/French and German Kurrent manuscripts: decoding with LMs, system combination, post-correction, segmentation, noisy-GT training, normalisation, writer adaptation (literature 2022–2026, status October 2026)

Scope note for the report writer: these notes cover levers other than adding more ground truth. Project baseline: kraken 7.0.3 (CTC line recogniser) at about 8 % CER on Latin/French (a scholar's cursive, fine-tuned model), and 30–50 % CER on a draft-writer's German Kurrent; TrOCR-style models are also in use; about 300,000 aligned lines and the full Academy edition text are available. All figures carry their source, test set and baseline. "Estimate" or "inference" marks my own reasoning. Absolute CER changes are in percentage points (pp).

## Method by method: what each lever is, its measured gain, cost, open code, and fit with kraken/eScriptorium

### Takeaway
The best-documented and lowest-risk lever is CTC beam-search decoding with a character n-gram LM. On medieval Latin/French and 19th-century French handwriting at 8–10 % CER it gives −0.5 to −1.0 pp CER, but kraken 7.0.3 itself now ships only a greedy decoder, so the LM decoding has to be bolted on. Three other levers can give larger gains but need more care: post-correctors trained on in-domain data, fixing line extraction, and adapting to the target writer. Zero-shot, text-only LLM correction is unreliable outside English and gets worse as CER rises.

### Cited Findings

**1. CTC decoding with n-gram language models**
- PyLaia (Teklia, ICDAR 2024) adds n-gram LM decoding at character, subword or word level (SRILM or KenLM LMs). It decodes by beam search through torchaudio's `ctc_decoder`, "taking into account lexicon constraints". The LMs are "completely auto-tuned … without requiring any additional data". Across 12 datasets the average gain is −12 % relative CER and −13 % relative WER — [Tarride et al. 2024, arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- Setup in that paper: a 6-gram character LM with modified Kneser-Ney smoothing, built on each dataset's *training transcriptions only*. The LM weight was fixed at 1.5, the optimum found on NorHand v3 — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- Measured test-set CER, without LM → with LM (Table 4). Training-set sizes are from Table 1:
  - Himanis (medieval Latin and French; 18,504 training lines): 9.87 → 8.87 (−1.00 pp, −10.1 % rel.). WER 29.25 → 24.37.
  - HOME-Alcar (12th–14th c. Latin cartularies; 59,969 training lines): 8.35 → 7.85 (−0.50 pp, −6.0 %). WER 26.15 → 23.20.
  - Belfort (19th c. French; 25,800 training lines): 10.54 → 9.52 (−1.02 pp, −9.7 %). WER 28.12 → 23.73.
  - POPP (19th c. French, harder): 16.49 → 16.09 (−0.40 pp, −5.7 %).
  - NorHand v1/v2/v3 (19th c. Norwegian): 7.94 → 6.55, 9.72 → 8.23, 7.52 → 6.36 (−15 to −18 % rel.).
  - NewsEye (printed Fraktur, validation set): 1.82 → 1.77.
  - Esposalles (single writer): 0.76 → **1.04, i.e. worse**.
  
  Source: [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- The authors state that for datasets with CER below 2 % "the language model tends to create more errors than it can correct". On the other datasets the LM gave −0.9 pp CER on average (−12.2 % rel.) and −4.0 pp WER (−17.9 % rel.). The LM improved 11 of the 12 datasets — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- The Belfort model card on Hugging Face repeats the result: 10.54 % CER without LM, 9.52 % with the 6-gram character LM — [Teklia/pylaia-belfort](https://huggingface.co/Teklia/pylaia-belfort)
- A second Teklia study tested PyLaia and DAN on IAM, RIMES and NorHand v2 and reports that character or subword n-gram models improved all three (abstract-level information only) — [arXiv 2404.19317](https://arxiv.org/abs/2404.19317)
- Cost: the LM decoder runs only on CPU. Measured on an RTX 3080 Ti: 0.01 s/image on GPU without LM, 0.03 s on CPU without LM, 0.12 s on CPU with LM. The authors recommend LMs for batch processing — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- How PyLaia builds an LM, from its documentation:
  - A `tokens.txt` file starts with `<ctc>` and includes `<space>`.
  - Each level has its own lexicon file (`lexicon_characters.txt`, `lexicon_subwords.txt`, `lexicon_words.txt`). At character level each character maps to itself and word gaps are written as `<space>`.
  - KenLM build command: `bin/lmplz --order 6 --text corpus_characters.txt --arpa model_characters.arpa --discount_fallback`. The docs recommend order 6 for characters and subwords and order 3 for words; `--discount_fallback` can be dropped for large corpora.
  
  Source: [PyLaia docs, language models](https://doc.teklia.com/pylaia/usage/language_models/)
- Licences:
  - PyLaia 1.1.2 (last upload October 2024): MIT — [PyPI pylaia](https://pypi.org/project/pylaia/)
  - pyctcdecode 0.5.0 (last upload 20 January 2023): Apache-2.0. It is described as a CTC beam search decoder with KenLM n-gram support, hotword boosting and BPE vocabularies — [PyPI pyctcdecode](https://pypi.org/project/pyctcdecode/); [GitHub pyctcdecode](https://github.com/kensho-technologies/pyctcdecode)
  - flashlight-text 0.0.7 (December 2024): the GitHub LICENSE file says MIT, but the PyPI metadata says "BSD licensed". The two sources conflict — [GitHub flashlight/text](https://github.com/flashlight/text); [PyPI flashlight-text](https://pypi.org/project/flashlight-text/)
  - KenLM: "Most of the code here is licensed under the LGPL", with listed exceptions — [GitHub kpu/kenlm](https://github.com/kpu/kenlm)
  - CTCWordBeamSearch: MIT — [GitHub CTCWordBeamSearch](https://github.com/githubharald/CTCWordBeamSearch)
- Lexicon-constrained vs lexicon-free decoding:
  - torchaudio's `ctc_decoder` takes a lexicon file, a tokens file and an optional LM, with tunable beam size and LM weight. Passing `lexicon=None` gives lexicon-free decoding — [torchaudio decoder docs](https://pytorch.org/audio/0.12.0/models.decoder.html)
  - Word Beam Search restricts output to dictionary words but has a free mode for numbers and punctuation, and offers word-level LM scoring modes — [CTCWordBeamSearch](https://github.com/elavin11/ctcwordbeamsearch); [ICFHR 2018 poster](https://iapr.org/archives/icfhr2018/SlidesPosters/Poster-55.pdf)
- kraken 7.0.3 has no LM decoding and no beam search. In the 7.0.3 tag, `kraken/lib/ctc_decoder.py` declares `__all__ = ['greedy_decoder']`, although its module docstring still mentions a thresholding decoder and "a more complex beam search decoder". The 5.3.0, 6.0.0 and 6.0.3 tags still define `beam_decoder`, `greedy_decoder` and `blank_threshold_decoder` — [kraken 7.0.3 ctc_decoder.py](https://github.com/mittagessen/kraken/blob/7.0.3/kraken/lib/ctc_decoder.py); [kraken 6.0.3 ctc_decoder.py](https://github.com/mittagessen/kraken/blob/6.0.3/kraken/lib/ctc_decoder.py)
- A shallow clone of the kraken main branch (October 2026) has no references to KenLM, pyctcdecode, lexicons or torchaudio — [kraken repository](https://github.com/mittagessen/kraken)
- For comparison on NorHand v1: kraken trained by experts scored 12.2 % CER (as reported by Maarand et al.), PyLaia by experts 8.9 %, HTR+ 8.3 %, and PyLaia with LM 6.6 %. These come from different training runs and are not an LM-only comparison — [arXiv 2404.18722, Table 5](https://arxiv.org/abs/2404.18722)

**2. Ensembling and system combination**
- TrOCR on 16th-century Latin letters by Rudolf Gwalther: 142 pages, 4,037 lines, split 3,603 train / 433 validation.
  - TrOCR-base baseline: 1.93 % CER. Best single augmented model (rotation or elastic augmentation): 1.86 %.
  - Voting over all 11 models: 1.66 %. Voting over the top 5: 1.60 %.
  - Method: each model contributes its top-5 beam hypotheses and the most-voted full sentence wins. Character-level voting was dropped because it sometimes produced mixed-script output.
  - Earlier results on this material: HTR+ 2.74 %, and TrOCR-base by Ströbel et al. 3.18 %.
  - Cost: about 1 h per model on an A100 40 GB. Code is at github.com/erez-meoded/TrOCR-HTR; no licence is stated.
  
  Source: [arXiv 2508.11499 (2025)](https://arxiv.org/abs/2508.11499)
- Older OCR evidence (2018, printed early modern books, not handwriting): cross-fold training plus confidence voting cut errors by "up to 50 % and more" — [Reul et al., arXiv 1711.09670](https://ar5iv.labs.arxiv.org/html/1711.09670)
- I found no 2022–2026 paper that measures ROVER or confusion-network combination of two different HTR engines (for example a CTC model with an encoder–decoder model) on historical handwriting. A search returned only the 2025 TrOCR study and pre-2022 OCR work — [search result set incl. arXiv 2508.11499](https://arxiv.org/abs/2508.11499)

**3. Post-correction with seq2seq models and LLMs** (full detail under the LLM key question below)
- mT5-small (~300M parameters) as a post-processor in HAND, on READ 2016 (historical German handwriting):
  - Line level: CER 2.71 → 1.65, WER 10.98 → 4.95. Paragraph level: CER 3.18 → 2.13. Single page: 3.41 → 2.36.
  - The corrector was trained with augmentation designed from the recogniser's own error analysis, using NFKC normalisation.
  - Caveat: the paper's Table III reports a differently defined "error rate" that does not match these values.
  
  Source: [HAND, arXiv 2412.18981](https://arxiv.org/abs/2412.18981)
- ByT5-small post-correction on a 14th-century Medieval Greek manuscript (KONVENS 2026), trained on synthetic noisy→clean pairs generated from validation error profiles:
  - With *automatically detected* line polygons: WER 36.82 → 30.87 (−16.2 % mean relative), and for HTR trained from scratch WER 44.79 → 36.50 with CER 12.54 → 11.55.
  - With manually corrected polygons, effects were "smaller and less consistent, … including CER degradation in some settings".
  - The authors conclude that post-correction "does not replace accurate TLD or HTR".
  
  Source: [Andersen, Pizzone, Yousef, KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf)
- Byzantine Greek (EMNLP Findings 2023): running a classifier to filter erroneous HTR lines *before* a neural post-corrector significantly reduced the corrector's own mistakes, because correctors introduce new errors — [Pavlopoulos et al. 2023](https://eprints.cs.univie.ac.at/8012)
- A Stuttgart master's thesis (2023; not peer-reviewed) combines a CLIP image encoder with ByT5 for multimodal post-correction of German texts from 1783–1903. It reports beating a text-only state-of-the-art model — [Wu 2023, Univ. Stuttgart](https://elib.uni-stuttgart.de/handle/11682/14250)

**4. Segmentation and line-extraction quality**
- Boillet, Kermorvant and Paquet (IJDAR 2022) measured line-level HTR CER on manually annotated lines versus lines from three detectors (manual / Doc-UFCN / dhSegment / ARU-Net):
  - HOME (medieval charters): 12.0 / 36.1 / 23.3 / 80.1
  - Alcar: 12.5 / 22.9 / 27.6 / 30.0
  - Balsac: 4.3 / 7.2 / 8.2 / 29.7
  - Bozen: 5.8 / 8.8 / 10.0 / 86.5
  - Horae: 10.6 / 15.2 / 12.0 / 30.3
  - ARU-Net fails mainly through merged lines.
  - Unifying the polygon labels cut Bozen CER from 27.3 to 8.8 and ScribbleLens from 14.3 to 9.8.
  
  Source: [arXiv 2203.12346](https://ar5iv.labs.arxiv.org/html/2203.12346)
- The same paper notes that pixel-level and IoU metrics miss wrong line splits and merges. The authors therefore evaluate line detection by its effect on HTR output — [arXiv 2203.12346](https://arxiv.org/abs/2203.12346)
- KONVENS 2026 (Transkribus pipeline): switching from manually corrected to automatic line polygons raised test CER from 2.69 % to 8.90 % (WER 14.36 → 36.82) for HTR initialised from a pretrained model. For HTR trained from scratch, CER rose from 3.01 % to 12.54 % — [KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf)
- YALTAi (JDMDH 2023) uses YOLOv5 object detection for regions inside kraken 4.1. It "clearly" beats kraken's segmentation on small training sets (up to about 1,110 samples). These are region metrics, with no CER reported — [Clérice, JDMDH 9806](https://jdmdh.episciences.org/9806)
- kraken 7.0 adds plug-ins ("external implementations of layout analysis, text recognition, and reading order") through Python entry points, with a D-FINE layout plug-in as the example. It also adds baseline-detection metrics modelled on the Transkribus evaluation scheme — [kraken releases](https://github.com/mittagessen/kraken/releases)
- The plug-in is `dfine_kraken` (Apache-2.0), installed with `pip install dfine_kraken`. It adapts ArgoHA's D-FINE implementation and its models are not compatible with pre-7 kraken — [dfine_kraken](https://github.com/mittagessen/dfine_kraken); [kraken API docs source](https://github.com/mittagessen/kraken/blob/main/docs/user_guide/api.rst)
- A 2025 KBLab practitioner comparison of Transkribus, kraken and TrOCR on medieval Latin found that region detection strongly limits recognition quality (blog; search snippet only) — [KBLab 2025](https://kb-labb.github.io/posts/2025-06-11-from-parchment-to-pixel/)
- The READ project report (2017) lists touching or overlapping lines, intra-line skew and above-line additions as key failure sources. It states that poor segmentation seriously degrades HTR, and that baseline representations can give results comparable to polygons — [READ D6.11](https://readcoop.eu/wp-content/uploads/2017/12/READ_D6.11_Line_and_Word_Segmentation_Tools_P2.pdf)

**5. Training on noisy or aligner-produced ground truth (confidence filtering, self-training)**
- PyLaia line confidence:
  - The mean softmax after CTC decoding correlates with line recognition rate (rank 0.60, linear 0.62 on NorHand v1). Monte Carlo dropout degraded recognition.
  - Temperature scaling raises the linear correlation, for example Esposalles 0.23 → 0.71, NewsEye 0.45 → 0.74, Belfort 0.58 → 0.78. T = 2.0 is a robust default.
  
  Source: [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- kraken 7.0.3's `TorchSeqRecognizer.forward` already applies a temperature: `probs = (logits / self.temperature).softmax(1)` — [kraken 7.0.3 models.py](https://github.com/mittagessen/kraken/blob/7.0.3/kraken/lib/models.py)
- Self-training with confidence-based pseudo-label selection (Wolf & Fink, ICPR 2022; synthetic-to-real adaptation of word recognisers):
  - GW: CER 25.41 (initial) → 16.65 (all pseudo-labels) → 12.37 (threshold) → 12.28 (confidence schedule). Random selection gave 16.75.
  - IAM: 21.78 → 16.19 → 9.96 with thresholding.
  - Caveat: the search tool reported that the table extraction was partly garbled, so these numbers need checking against the PDF.
  
  Source: [arXiv 2206.03149](https://arxiv.org/abs/2206.03149)
- The IJDAR 2024 extension of that work combines several confidence measures to remove wrong pseudo-labels. It claims to beat other adaptation strategies when no manual labels exist (abstract only) — [Wolf & Fink 2024, IJDAR](https://link.springer.com/10.1007/s10032-024-00484-9)
- A 2026 study of label-error detection in Arabic-script HTR datasets notes that the topic "has received comparatively little attention in HTR". It argues that the CTC training signal mixes alignment uncertainty with label correctness, so classification-oriented noise methods do not transfer directly (search snippet) — [arXiv 2601.16713](https://arxiv.org/abs/2601.16713)
- One HTR-plus-LLM Latin workflow runs two LLM calls per chunk and flags a line as "unclear" when the two runs differ by more than about 5 % CER or diverge strongly from the HTR. Flagged lines are excluded from the training data — [arXiv 2507.04132](https://arxiv.org/abs/2507.04132)

**6. Normalisation, abbreviations and codec**
- Camps, Vidal-Gorène and Vernet (ICDAR 2021) studied a heavily abbreviated medieval Latin manuscript, with about 47 % of words containing at least one abbreviation:
  - Character-based HTR: 10.59 / 9.69 % CER on expanded transcriptions (D-exp1/D-exp2) against 4.89 / 4.55 % on abbreviated (graphemic) transcriptions (D-abb1/D-abb2).
  - Word-based HTR: 3.76 / 2.96 on expanded and 5.57 / 4.83 on abbreviated.
  - The two kinds of score are measured against different reference strings and are not strictly comparable.
  - The paper also tested a modular route: HTR, then word segmentation (Boudams), then expansion (Pie).
  - It cites earlier work in which deletions, including letters that expansion should have added, made up more than half of HTR errors.
  
  Source: [arXiv 2107.03450](https://arxiv.org/abs/2107.03450)
- kraken `ketos` exposes `-u/--normalization` with NFD, NFKD, NFC or NFKC for ground-truth normalisation — [kraken ketos/recognition.py](https://github.com/mittagessen/kraken/blob/main/kraken/ketos/recognition.py)
- In 7.0.3, `ketos test` applies Unicode normalisation to both prediction and ground truth; before, only the ground truth was normalised. CER figures from 7.0.3 and earlier versions may therefore differ — [kraken releases](https://github.com/mittagessen/kraken/releases)
- Evaluation normalisation can reverse conclusions. In LLM OCR correction, GPT-4o's relative CER gain was 58.1 % on English with long-s→s and w→v normalisation but 34.9 % without it. On Finnish it was +11.9 % with normalisation and −10.1 % without — [Kanerva et al. 2025, arXiv 2502.01205](https://arxiv.org/html/2502.01205v1)
- CATMuS-Medieval defines shared transcription guidelines and models for Latin scripts of the 8th–16th centuries (DH2024). I did not retrieve a graphemic-versus-normalised CER ablation from it — [CATMuS DH2024](https://halshs.archives-ouvertes.fr/hal-04346939v1/file/DH2024___CATMuS-5.pdf)
- PyLaia's authors report degraded CTC performance on private datasets "featuring blank areas and abbreviations" — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)

**7. Writer-specific adaptation**
- Kohút and Hradiš (2023): fine-tuning with data augmentation "remained resistant to overfitting even on very small target datasets". On a large real-world dataset it improved error rates by about 25 % relative with 16 lines from a new writer and about 50 % with 256 lines — [arXiv 2302.06308](https://arxiv.org/abs/2302.06308)
- The Bullinger dataset (ICDAR 2023) is built for writer adaptation: 16th-century Latin and Early New High German letters, 3,622 annotated letters by 306 writers. It covers supervised adaptation for frequent writers and self-supervised adaptation for writers with few letters. I could not retrieve its CER tables (PDF returned 403) — [Bullinger dataset, Univ. Bern](https://boris.unibe.ch/185720/); [TC11 BullingerDB](https://tc11.cvc.uab.es/datasets/BullingerDB_1)
- An unreviewed Research Square preprint reports a meta-learning writer-adaptive method reaching CER 0.3492 on Bullinger. Not verified — [Research Square rs-10697326](https://www.researchsquare.com/article/rs-10697326/latest)

**8. Other levers found**
- kraken 7.1 (5 August; the releases page does not show the year) adds a new recognition architecture based on PP-OCRv6 with "pretrained multilingual base models" in tiny, small and medium sizes. No CER figures were found. The project's 7.0.3 install predates it — [kraken releases](https://github.com/mittagessen/kraken/releases)
- Multimodal LLMs used directly as recognisers:
  - On 17th-century German handwriting, zero-shot Gemini scored 74 % CER against 9.2–10.1 % for fine-tuned CNN and TrOCR models (search snippet) — [arXiv 2410.24034](https://arxiv.org/abs/2410.24034)
  - On 18th–19th c. English, LLM direct transcription reached 5.7–7 % CER — [Humphries et al., arXiv 2411.03340](https://arxiv.org/abs/2411.03340)
  - On READ2016 (German), Transkribus "The Text Titan" scored 40.63 % CER and beat the LLMs tested; on ICDAR2017 it scored 14.40 % — [Crosilla et al. 2025, arXiv 2503.15195](https://arxiv.org/abs/2503.15195)

### Inferences
- Summary matrix. All gain figures are estimates extrapolated from the cited studies, not measured on this project.
  - **Character n-gram LM beam search on kraken outputs**
    - Gain at ~8 % Latin/French: −0.5 to −1.0 pp measured on comparable data; perhaps up to −1.5 pp with a far larger in-domain LM (estimate).
    - Gain at 30–50 % Kurrent: small in relative terms (estimate; −2.4 % rel. measured at 16.5 % CER on POPP).
    - Cost: CPU only; hours of integration code.
    - Fit: runs beside kraken via a custom decoder, or inside `rpred` as a decoder callable.
  - **TrOCR n-best voting ensemble**
    - Gain: about −14 % rel. vs best single model, measured at about 1.9 % CER.
    - Cost: N× training (about 1 A100-hour per model for 3.6k lines).
    - Fit: runs beside kraken.
  - **kraken + TrOCR system combination**
    - Gain: unmeasured in the 2022–2026 literature.
    - Cost: alignment and voting code.
    - Fit: runs beside kraken.
  - **ByT5/mT5 post-corrector trained on in-domain HTR→GT pairs**
    - Gain: −8 % to −39 % rel. measured in other settings. Largest where errors come from segmentation; can hurt on clean lines.
    - Cost: GPU fine-tuning.
    - Fit: runs beside kraken and eScriptorium.
  - **Zero-shot text-only LLM correction**
    - Gain: often negative outside English.
    - Fit: runs beside kraken and eScriptorium.
  - **Multimodal LLM correction (image + HTR text) with disagreement flagging**
    - Gain: promising in Latin case studies (final WER 2–7 %), but no controlled CER ablation exists.
    - Cost: API cost, plus hallucination audit.
    - Fit: runs beside kraken and eScriptorium.
  - **Better line extraction** (D-FINE/YOLO plug-ins, polygon fixes, label unification)
    - Gain: potentially the largest on revised drafts; measured CER multipliers of about 1.1–4.2× between automatic and correct lines, depending on detector and material.
    - Fit: inside kraken 7 via plug-ins; eScriptorium support unverified.
  - **Writer fine-tuning** with 16–256 corrected lines: −25 to −50 % rel. measured on a modern real-world dataset.
  - **Confidence filtering of aligner-produced GT**: plausible but unmeasured for HTR alignment noise.
- For kraken + eScriptorium, the least disruptive path is to keep kraken for segmentation and optical modelling, run the LM decoding, post-correction and combination as a batch step outside, and re-import the results as PAGE/ALTO. This is inference; I did not verify which kraken version current eScriptorium releases bundle.

### Gaps
- No 2022–2026 measurements were found for checkpoint averaging, model soups or test-time augmentation in HTR, nor for ROVER-style combination of a CTC engine with an encoder–decoder engine on historical handwriting.
- Calamari's and Loghi's decoding options, and any Transkribus or Loghi technical report quantifying LM decoding, were not found or verified. Licences: Calamari is GPL-3.0 ([PyPI calamari-ocr](https://pypi.org/project/calamari-ocr/), [GitHub](https://github.com/Calamari-OCR/calamari)); Loghi is MIT ([GitHub knaw-huc/loghi](https://github.com/knaw-huc/loghi)).
- I could not confirm whether torchaudio's `ctc_decoder` is still shipped in torchaudio 2.9–2.11 (2.11.0 was released March 2026, per [PyPI](https://pypi.org/project/torchaudio/)). flashlight-text can be used directly instead.
- No measured NFD-vs-NFC, u/v, long-s or mixed-language-training CER ablations for HTR were found for 2022–2026.
- No LM-fusion results for TrOCR on historical handwriting were found.

## Which single method gives the largest reliable gain on a model already at about 8 % CER on a scholar's Latin/French cursive, and what is the realistic range?

### Takeaway
The most *reliable* single lever is beam-search decoding of the kraken CTC outputs with a character n-gram LM. On medieval Latin/French and 19th-century French handwriting at 8–10 % CER it gives a measured −0.5 to −1.0 pp CER, using LMs built only from training transcriptions. An LM built from the much larger, in-domain Academy edition plausibly reaches −0.7 to −1.5 pp (estimate). Two levers have higher ceilings but are less reliable: a post-corrector trained on in-domain data and multimodal LLM correction. Text-only zero-shot LLM correction is not reliable for Latin or French.

### Cited Findings
- Character 6-gram LM decoding, measured on comparable material: Himanis (medieval Latin/French) 9.87 → 8.87 % CER, HOME-Alcar (medieval Latin) 8.35 → 7.85 %, Belfort (19th c. French) 10.54 → 9.52 %. WER fell more, by 3–5 pp — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- The LM helped 11 of 12 datasets and hurt only where CER was already below 2 % (Esposalles 0.76 → 1.04) — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- Those LMs used only each dataset's training text: 18,504 lines for Himanis and 59,969 for HOME-Alcar — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- TrOCR ensemble voting on 16th-century Latin (Gwalther) improved validation CER from 1.86 % (best single model) to 1.60 %, about −14 % relative. The top-5 models appear to have been chosen on the same validation set — [arXiv 2508.11499](https://arxiv.org/abs/2508.11499)
- In-domain trained post-correctors reached large relative gains in other settings: mT5-small on READ 2016 German, 2.71 → 1.65 % line CER — [arXiv 2412.18981](https://arxiv.org/abs/2412.18981)
- In the ICDAR 2026 HIPE-OCRepair competition (printed text, en/fr/de), the best system, a Mistral Small 3 24B with continued pre-training plus LoRA fine-tuning, reduced micro character Match Error Rate from 0.0226 to 0.0050. French went from 0.0176 to 0.0042 — [arXiv 2607.08143](https://arxiv.org/abs/2607.08143)
- Text-only LLM correction outside English often hurts:
  - In Kanerva et al., all open models increased CER on Finnish (+19 % to +77 % relative); only GPT-4o improved it (−11.9 %) — [arXiv 2502.01205](https://arxiv.org/html/2502.01205v1)
  - In Boros et al., 14 LLMs "mostly degrade the input text, occasionally leave it unchanged, and rarely improve it" — [Boros et al., LaTeCH-CLfL 2024](https://aclanthology.org/2024.latechclfl-1.14/)
- A Latin court-hand workflow fed both the page image and the HTR text (Transkribus PyLaia model, 5.25 % validation CER) to an LLM, then expanded abbreviations. Final WER was about 2.0–6.3 % across four cases. There is no stage-by-stage CER ablation — [arXiv 2507.04132](https://arxiv.org/abs/2507.04132)
- Writer fine-tuning gives −25 % relative with 16 lines and −50 % with 256 lines for a *new* writer — [arXiv 2302.06308](https://arxiv.org/abs/2302.06308)

### Inferences
- Realistic expectation for the 8 % Latin/French kraken model (estimate):
  - Character 6-gram LM decoding: −0.5 to −1.0 pp, i.e. 8.0 → about 7.0–7.5 %.
  - With an edition-scale LM correctly normalised to the ground-truth conventions: perhaps −1.5 pp.
  - Most of the gain will show in WER and word-level readability.
- The writer adaptation gain probably does not carry over here. The kraken model is already fine-tuned on this scholar's hand from a large aligned corpus, so the 25–50 % "new writer" figure does not apply; residual gains from more writer adaptation are likely small (inference).
- **Leakage warning.** If the LM is trained on the full Academy edition, it contains the text of any test document that has been edited. That would inflate measured gains. Hold out the edition text of every evaluation document from the LM corpus.
- For documents already in the edition, aligning the edition text to the image beats recognition. The LM matters for unedited material (inference).
- The edition's conventions (expanded abbreviations, normalised u/v, i/j and long s, editorial punctuation, apparatus) must be mapped to the transcription conventions and Unicode normalisation of the ground truth and the kraken codec. Otherwise the LM pushes the output toward edition spelling, and CER against diplomatic ground truth can rise (inference, supported by the normalisation effects in [arXiv 2502.01205](https://arxiv.org/html/2502.01205v1)).
- Before investing elsewhere, run a cheap diagnostic: recognise a validation set on corrected lines and on automatic lines (the Boillet method). This measures how much of the 8 % comes from segmentation. Published gaps between correct and automatic lines range from about 1.1× to 4.2× CER ([arXiv 2203.12346](https://ar5iv.labs.arxiv.org/html/2203.12346); [KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf)).

### Gaps
- No published LM-decoding result for a kraken model was found, nor one for an LM built from a large external edition corpus instead of the training transcriptions.
- No measurement of LM gains specifically on a single scholar's Latin/French cursive.
- No controlled CER ablation of multimodal LLM correction for Latin or French at about 8 % CER.

## Which methods are known to help the hard case (a draft-writer's German Kurrent with abbreviations and revisions at 30–50 % CER)?

### Takeaway
At 30–50 % CER the evidence favours fixing the input and the optical model rather than decoding or correction tricks. The best-supported levers are:
- **Line extraction for revised drafts.** Automatic versus correct lines can triple CER.
- **Writer-specific fine-tuning on a few hundred corrected lines.** −25 to −50 % relative.
- **Graphemic transcription of abbreviations** instead of expansion, with expansion done in a later stage.
- **Confidence-filtered self-training** on the writer's unlabelled pages.

LM decoding and LLM post-correction give small or negative gains at this error level.

### Cited Findings
- Line extraction: on HOME medieval charters, line-level CER was 12.0 % with manual lines against 36.1 % with Doc-UFCN lines and 23.3 % with dhSegment lines. Merged lines drove ARU-Net to 80.1 % — [arXiv 2203.12346](https://ar5iv.labs.arxiv.org/html/2203.12346)
- Automatic polygons multiplied CER by 3.3–4.2× on a Medieval Greek scholarly hand (2.69 → 8.90 %; 3.01 → 12.54 %) — [KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf)
- The READ project lists touching or overlapping lines and above-line additions among the main failure sources — [READ D6.11](https://readcoop.eu/wp-content/uploads/2017/12/READ_D6.11_Line_and_Word_Segmentation_Tools_P2.pdf)
- Few-line writer fine-tuning: about −25 % relative with 16 lines and −50 % with 256 lines from a new writer — [arXiv 2302.06308](https://arxiv.org/abs/2302.06308)
- Abbreviations: on a heavily abbreviated Latin manuscript, the character-based HTR scored 4.55–4.89 % CER on graphemic (abbreviated) transcriptions and 9.69–10.59 % when trained and evaluated on expanded text — [arXiv 2107.03450](https://arxiv.org/abs/2107.03450)
- PyLaia's authors observed CTC degradation on material "featuring blank areas and abbreviations" — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- LM decoding at higher CER: on POPP (16.49 % CER) the gain was only −0.40 pp (−5.7 % rel.), much less than on the 8–10 % datasets — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- LLM correction at high CER:
  - When gains occurred, they were "insufficient to shift the output from 'unusable' (CER over 10 %) to 'good'". The best case was GPT-4o on ICDAR2017 with an 8 % CER decrease. "All the open-source models failed to show improvement and rather increased the error rates" — [Crosilla et al. 2025](https://arxiv.org/abs/2503.15195)
  - On German READ2016 even Transkribus' best general model scored 40.63 % CER — [Crosilla et al. 2025](https://arxiv.org/abs/2503.15195)
- Zero-shot multimodal LLM recognition of 17th-century German handwriting: about 74 % CER (Gemini), against 9.2–10.1 % for fine-tuned models (snippet) — [arXiv 2410.24034](https://arxiv.org/abs/2410.24034)
- A secondary summary of a June 2025 Transkribus benchmark reports 10.8 % CER for Text Titan I-ter against 35.0 % for Gemini 2.5 Flash on historical handwriting. Not verified against the original — [LlamaIndex summary](https://www.llamaindex.ai/insights/best-ai-for-handwriting-recognition)
- A blog claims Gemini 3 "solves handwriting recognition", without a controlled Kurrent CER. Anecdotal — [Generative History](https://generativehistory.substack.com/p/gemini-3-solves-handwriting-recognition/comments)
- Post-correction recovers part of segmentation-induced error: ByT5 cut WER 44.79 → 36.50 and CER 12.54 → 11.55 on automatic polygons, with smaller or negative effects on clean polygons — [KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf)
- Confidence-filtered self-training on unlabelled target data: GW word recognition CER 25.41 → 12.28 with a confidence schedule, against 16.65 using all pseudo-labels (extraction partly garbled; verify) — [arXiv 2206.03149](https://arxiv.org/abs/2206.03149)
- Existing Kurrent starting points:
  - TrOCR model for 16th–18th c. Kurrent: test CER 0.05416 — [dh-unibe/trocr-kurrent-XVI-XVII](https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII)
  - Transkribus Kurrent/Sütterlin 17th–20th c. model: validation CER 5.40 % — [Transkribus model page](https://www.transkribus.org/models/german-kurrent-and-sutterlin-17th-20th-century)
  - A 19th-century Kurrent line dataset of 9,317 lines (Zenodo, October 2025) — [Zenodo 17252677](https://zenodo.org/records/17252677)
  - Background on general Kurrent models: [Hodel et al., JOHD 2021](https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.46)

### Inferences
- Suggested order for the Kurrent drafts (inference):
  1. Audit segmentation on revised pages: interlinear insertions, strike-throughs and marginal additions. Use the recognition-on-GT-lines-vs-automatic-lines diagnostic. Try the kraken 7 D-FINE plug-in or a YOLO line or region model where blla merges lines.
  2. Adopt graphemic abbreviation transcription in the Kurrent ground truth and codec, and expand afterwards with a separate seq2seq step or a lexicon.
  3. Fine-tune on 100–300 hand-corrected lines of this writer, starting from a Kurrent base model.
  4. Self-train on the writer's unlabelled pages, keeping only lines with high temperature-calibrated confidence.
  5. Only then add LM decoding and, later, a trained post-corrector.
- At 30–50 % CER, n-gram LM decoding is likely worth only a few percent relative (estimate). Text-only LLM correction is likely to produce plausible but wrong German ("hallucinated plausibility") and should not be applied unsupervised.
- Strike-throughs and revisions may need a transcription policy decision (for example, transcribe deleted text with a marker, or skip it). Inconsistent policy shows up as label noise. I found no source quantifying this.

### Gaps
- No 2022–2026 paper reports CER before and after LM decoding, post-correction or writer adaptation specifically for German Kurrent drafts with heavy revisions.
- The Bullinger writer-adaptation CER tables (Latin and Early New High German) could not be retrieved.
- No measured effect of strike-through or insertion handling on CER was found.

## What open code exists for CTC + LM decoding that works with kraken's models, or how would one get kraken's outputs into pyctcdecode or a custom beam search?

### Takeaway
kraken 7.0.3 has no LM or beam-search decoding; only `greedy_decoder` remains, and the beam and threshold decoders of 5.x–6.0.x are gone. There is a clean hook, though:
- `TorchSeqRecognizer.forward()` returns per-line softmax matrices of shape (N, W, C).
- Label 0 of kraken's codec is the CTC blank.
- `TorchSeqRecognizer` accepts a custom `decoder` function.

So kraken outputs can be fed to flashlight-text or torchaudio's `ctc_decoder` (the approach PyLaia uses, with lexicon-free character LMs), to pyctcdecode (word-level KenLM), or to Word Beam Search. All of these are open source, under MIT, Apache-2.0 or LGPL.

### Cited Findings
- kraken 7.0.3 `ctc_decoder.py` exports only `greedy_decoder`. The 6.0.3 tag defines `beam_decoder`, `greedy_decoder` and `blank_threshold_decoder` — [7.0.3 source](https://github.com/mittagessen/kraken/blob/7.0.3/kraken/lib/ctc_decoder.py); [6.0.3 source](https://github.com/mittagessen/kraken/blob/6.0.3/kraken/lib/ctc_decoder.py)
- `TorchSeqRecognizer.forward(line, lens)` "performs a forward pass on a torch tensor of one or more lines with shape (N, C, H, W) and returns a numpy array (N, W, C)" plus output sequence lengths. It computes `probs = (logits / self.temperature).softmax(1)` — [kraken 7.0.3 models.py](https://github.com/mittagessen/kraken/blob/7.0.3/kraken/lib/models.py)
- The constructor takes a "decoder: Decoder function used for mapping softmax activations to …" argument — [kraken 7.0.3 models.py](https://github.com/mittagessen/kraken/blob/7.0.3/kraken/lib/models.py)
- The kraken codec states: "As 0 is the blank label in a CTC output layer, output labels and input …" — [kraken codec.py (main)](https://github.com/mittagessen/kraken/blob/main/kraken/lib/codec.py)
- kraken is Apache-2.0 — [kraken LICENSE](https://github.com/mittagessen/kraken/blob/main/LICENSE)
- kraken 7.0 adds a batched API with parallel line extraction and processing, and plug-in entry points for external recognition implementations — [kraken releases](https://github.com/mittagessen/kraken/releases)
- PyLaia uses torchaudio's `ctc_decoder` (flashlight) with KenLM ARPA models at character, subword or word level — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- PyLaia's file conventions and KenLM commands are documented: `tokens.txt` with `<ctc>` and `<space>`, per-level lexicons, `lmplz --order 6` for characters — [PyLaia docs](https://doc.teklia.com/pylaia/usage/language_models/)
- torchaudio's `ctc_decoder`: lexicon file or `None` for lexicon-free decoding, a tokens file, an optional LM, plus beam size and LM weight — [torchaudio docs](https://pytorch.org/audio/0.12.0/models.decoder.html)
- pyctcdecode: CTC beam search with KenLM n-gram support (Apache-2.0, last release 0.5.0 in January 2023) — [PyPI](https://pypi.org/project/pyctcdecode/); [GitHub](https://github.com/kensho-technologies/pyctcdecode)
- pyctcdecode requires logits of shape (time, vocabulary) whose width equals the label list exactly. A size mismatch raises an error, as in a NeMo user report — [NeMo issue 5738](https://github.com/NVIDIA/NeMo/issues/5738)
- Word Beam Search (MIT): dictionary-constrained CTC decoding with optional word LM and a free mode for non-words, aimed at HTR — [CTCWordBeamSearch](https://github.com/githubharald/CTCWordBeamSearch)
- githubharald's CTCDecoder offers a character-level LM inside beam search and a lexicon search over a BK-tree. Licence not checked — [CTCDecoder](https://github.com/githubharald/CTCDecoder)
- A shallow clone of kraken main shows no LM integration (no KenLM, pyctcdecode or torchaudio references) — [kraken repository](https://github.com/mittagessen/kraken)

### Inferences
- Integration recipe (inference; to be tested):
  1. Load the model and build lines with kraken's own line extractor, so that polygons and dewarping match training.
  2. Call `TorchSeqRecognizer.forward()` to get (N, W, C) probabilities. Take `log` and trim each row to its output length.
  3. Build the token list from the codec, with index 0 as blank and index i as the character(s) mapped to label i. Check that the codec maps labels to characters one to one; multi-label or merged codecs need a custom mapping.
  4. Decode:
     - (a) With flashlight-text or torchaudio `ctc_decoder` and a character 6-gram KenLM (lexicon-free, PyLaia style; space as a token).
     - (b) With pyctcdecode and a word 3-gram KenLM plus unigram list. pyctcdecode is word-oriented and its last release dates from 2023.
     - (c) With Word Beam Search in free mode for an edition-derived lexicon.
  5. Tune LM weight and word bonus on a held-out validation set.
- To keep eScriptorium-compatible character positions and confidences, implement the beam search as a `decoder` callable that returns label/start/end/confidence tuples like `greedy_decoder`, and pass it to `TorchSeqRecognizer` (inference from the constructor signature). Otherwise run decoding outside and re-import only the text.
- Building the LM from the project's data (inference):
  1. Concatenate the 300k aligned lines and the edition text, after excluding evaluation documents.
  2. Normalise to the codec (same Unicode form as `ketos -u`, same abbreviation, u/v and long-s policy). Drop characters not in the codec.
  3. Write characters space-separated with `<space>` between words.
  4. Run `lmplz --order 6` (modified Kneser-Ney). Optionally build `build_binary` for speed.
  5. Also build a word 3-gram for comparison.
  6. Prefer lexicon-free character LMs for abbreviated, variably spelled text. Lexicon constraints risk forcing out names, abbreviations and non-standard spellings.
- Building an n-gram LM from a corpus of this size takes minutes on a CPU (estimate). Decoding throughput in the PyLaia measurement was about 4× slower than greedy on CPU, roughly 0.12 s per line image ([arXiv 2404.18722](https://arxiv.org/abs/2404.18722)). 300k lines would take about 10 CPU-hours single-threaded, and the job parallelises easily (estimate).

### Gaps
- No public project was found that already wires kraken models to pyctcdecode, flashlight or KenLM. No kraken GitHub issue on LM decoding could be retrieved, because GitHub API search was blocked in this session.
- I did not verify whether torchaudio 2.9–2.11 still includes `ctc_decoder` (flashlight-text is the fallback).
- Calamari's decoder options were not verified (Calamari is GPL-3.0).

## What do 2024–2026 papers on LLM post-correction of historical HTR/OCR output report (gains, failure modes, languages)?

### Takeaway
Results split cleanly by setup:
- **Large gains:** fine-tuned or continued-pre-trained LLMs on printed OCR (up to about −78 % relative in HIPE-OCRepair 2026), and frontier models on English text.
- **Promising but unablated:** multimodal correction (image plus HTR text) in Latin and English case studies.
- **Little gain or harm:** zero-shot open models on non-English historical text, and any correction when HTR CER exceeds about 10 %.

Documented failure modes include over-correction of clean lines, plausible but wrong names and words, invented grammatical text on damaged lines, overgeneration and omissions, and normalising text into another language. Latin and German handwriting evidence is thin.

### Cited Findings
- **Boros et al. 2024 (LaTeCH-CLfL)**
  - 14 foundation LLMs (GPT-2 to GPT-4, BLOOM/BLOOMZ, OPT, LLaMA/LLaMA-2) tested on benchmarks in en, de, fr and grc. These included HTR of Byzantine Greek (htrec), classical commentaries mixing German, English, Latin and Greek (ajmc), and German Fraktur newspapers.
  - LLMs "mostly degrade the input text, occasionally leave it unchanged, and rarely improve it".
  - Few-shot prompting did not help. The htrec and ajmc data saw the most severe degradation.
  
  Source: [ACL Anthology 2024.latechclfl-1.14](https://aclanthology.org/2024.latechclfl-1.14/)
- **Kanerva et al. 2025** (18th c. English ECCO at OCR CER 0.07; Finnish Fraktur newspapers at CER 0.09), relative CER change on English / Finnish:
  - GPT-4o: −58.1 % / −11.9 %
  - Llama-3.1-70B: −38.7 % / +47.0 %
  - Gemma-2-27B: −35.6 % / +19.1 %
  - Llama-3-8B: −7.3 % / +68.8 %
  - Mixtral-8x7B: +14.9 % / +76.5 %
  
  Source: [arXiv 2502.01205](https://arxiv.org/html/2502.01205v1)
- Kanerva et al., failure modes: overgeneration ("Here is the corrected text:"); without overgeneration removal, Llama English CER became worse (−74.1 % improvement, i.e. a large increase). Smaller models sometimes omitted text. Very short segments of 50–100 words were notably worse; gains levelled off at 200–300 words. Code: github.com/TurkuNLP/ocr-postcorrection-lm, licence not stated — [arXiv 2502.01205](https://arxiv.org/html/2502.01205v1)
- **HIPE-OCRepair, ICDAR 2026** (printed only; English, French, German; 17th–20th c.; no Latin, no handwriting):
  - Baseline cMER 0.0226 → 0.0050 for BnF-Mistral, a Mistral Small 3 24B with about 80B tokens of continued pre-training, LoRA fine-tuning on about 10k pairs plus synthetic pairs, and a judge-and-retry loop.
  - German 0.0286 → 0.0061; French 0.0176 → 0.0042.
  - "All teams used decoder-only large language models ranging from 8B to 24B parameters."
  - "Overcorrection on low-noise inputs emerges as a recurring challenge". A zero-shot Qwen3-8B run was worse than no correction on French (0.0185 vs 0.0176).
  - The retry loop reduced the share of flagged outputs from 42 % to 6 %.
  
  Source: [arXiv 2607.08143](https://arxiv.org/abs/2607.08143)
- **Crosilla, Klic & Colavizza 2025** (Journal of Documentation): MLLMs "do not possess a significant capability for self-correction". Post-correction gains were inconsistent across datasets, and open-source models increased error rates. The best case, GPT-4o on ICDAR2017 (German/French/Italian 19th c.), lowered CER by 8 %, but output stayed "unusable". Transkribus models beat LLMs on German and multilingual sets — [arXiv 2503.15195](https://arxiv.org/abs/2503.15195); [Emerald JD 81(7)](https://www.emerald.com/jd/article/81/7/334/1275080/Benchmarking-large-language-models-for-handwritten)
- **Humphries et al. 2024** (18th–19th c. English handwriting): LLM correction of Transkribus or conventional HTR output reached CER as low as 1.8 % and WER 3.5 %. Direct LLM transcription scored 5.7–7 % CER. The tool, Transcription Pearl, is described as open source, but no licence was found — [arXiv 2411.03340](https://arxiv.org/abs/2411.03340)
- **Latin court hand, 2025** (15th c. English plea rolls):
  - Pipeline: multimodal LLM correction (deskewed image chunks of about 10 lines with numbered baselines, plus HTR text), then a separate LLM abbreviation expansion, then named-entity correction. Final WER was about 2–6.3 %.
  - Failure modes: semantic substitutions ("boviculi" read as "bonorum"); grammatical invented text on corrupted lines ("idemque Willelmus ex post"); plausible wrong names ("Barthelmum Barlawe" for "Ewanum Barlawe"); wrong dates and places.
  - Safeguards: dual-run disagreement flagging and expert review.
  - No code licence is stated.
  
  Source: [arXiv 2507.04132](https://arxiv.org/abs/2507.04132)
- **Greif et al. 2025** (printed German city directories, 1754–1870): multimodal post-correction (image plus OCR text) "consistently produces highly accurate transcriptions (<1 % CER)" without fine-tuning — [arXiv 2504.00414](https://arxiv.org/abs/2504.00414)
- **2026 preprint on digitisation pipelines**: lists hallucinated corrections, run-to-run non-determinism, and "normalizing" Latin terms into another language (a Latin word changed to Spanish) (snippet) — [arXiv 2608.24976](https://arxiv.org/abs/2608.24976)
- **Medieval Latin OCR-to-translation pipelines, 2026**: adding LLM correction gave no statistically reliable gain (snippet) — [arXiv 2607.03836](https://arxiv.org/abs/2607.03836)
- **MDPI Information, 2026**: a cross-pathway study of handwritten historical documents reports that "Pathway B" (apparently the LLM-assisted correction route) brought mean CER to 4.74 % and WER to 8.47 % relative to the OCR baseline, but its conclusions favour direct multimodal transcription, which had the lowest errors. Snippet only; the full text returned 403 — [MDPI Information 17(8):722](https://www.mdpi.com/2078-2489/17/8/722)
- **Trained small correctors**: mT5-small on READ 2016 German, line CER 2.71 → 1.65 — [arXiv 2412.18981](https://arxiv.org/abs/2412.18981). ByT5-small on Medieval Greek, CER 12.54 → 11.55 on automatic polygons, sometimes worse on clean lines — [KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf). Filtering lines before correction reduces introduced errors — [Pavlopoulos et al. 2023](https://eprints.cs.univie.ac.at/8012)

### Inferences
- For this project (inference):
  - Do not run zero-shot, text-only LLM correction over whole outputs.
  - If LLMs are used, give the model the line image (multimodal), restrict it to edits, and route only low-confidence lines to it.
  - Run it twice and flag disagreements, as in arXiv 2507.04132.
  - Reject outputs whose length ratio or edit distance is out of range (the HIPE team's 0.35×–2.8× guard).
  - Abstain on high-confidence lines, given that over-correction of low-noise inputs is documented.
- A ByT5 corrector trained on the project's own (kraken output → ground truth) pairs is the open, reproducible variant. Generate the pairs by running cross-validated kraken models over the 300k aligned lines. The expected gain is 10–40 % relative at about 8 % CER (estimate, from HAND and KONVENS). The gain shrinks where lines are already clean.
- "Hallucinated plausibility" shows up in names, dates, rare Latin words and damaged lines. Track entity-level accuracy separately from CER, because CER under-weights these errors (inference).

### Gaps
- No 2024–2026 study with controlled CER before and after LLM correction of *handwritten* German Kurrent or Latin/French scholarly cursive was found.
- HIPE-OCRepair covers only printed text and excludes Latin.
- Boros et al.'s per-dataset numbers (figures only) were not extracted.

## Costs on a 6 GB GPU and on a rented 24 GB card

### Takeaway
The cheapest levers need no GPU at all: n-gram LM decoding, segmentation audits, and confidence filtering. They fit any machine. ByT5-small or mT5-small correctors and kraken fine-tuning fit a 6 GB card (estimate). TrOCR ensembles and ByT5-base are more practical on 24 GB. Local LLM correction needs at least 24 GB for 8B models in fp16, and around 44 GB for 70B models even at 4-bit.

### Cited Findings
- PyLaia LM decoding is CPU-bound: 0.12 s/image with LM on CPU against 0.03 s without LM on CPU and 0.01 s on GPU (RTX 3080 Ti) — [arXiv 2404.18722](https://arxiv.org/abs/2404.18722)
- LLM memory as measured by Kanerva et al.:
  - Llama-3-8B: 6.3 GB at 4-bit, 16.1 GB at fp16.
  - Llama-3.1-70B: 43.6 GB at 4-bit, 132.1 GB at fp16; at 4-bit it "would need 2 GPUs at 32 GB each".
  - fp16 improved CER gains by 2.5–4.7 points for most models compared with 4-bit.
  
  Source: [arXiv 2502.01205](https://arxiv.org/html/2502.01205v1)
- TrOCR-base training on 3,603 lines took about 1 h per model on an A100 40 GB; the 11-model ensemble therefore took about 11 GPU-hours — [arXiv 2508.11499](https://arxiv.org/abs/2508.11499)
- The HIPE-OCRepair winner used about 80B tokens of continued pre-training of a 24B model, far beyond a single rented card. Other teams used Qwen3-14B instruction tuning, or zero-shot Qwen3-8B via Ollama — [arXiv 2607.08143](https://arxiv.org/abs/2607.08143)
- HAND's corrector is mT5-small with about 300M parameters — [arXiv 2412.18981](https://arxiv.org/abs/2412.18981). KONVENS 2026 used google/byt5-small — [KONVENS 2026](https://www.korpuslab.uni-hamburg.de/en/konvens2026/121.pdf)
- API route: LLM transcription and correction is described as about 50× faster and about 1/50th the cost of proprietary HTR — [arXiv 2411.03340](https://arxiv.org/abs/2411.03340). A blog anecdote puts 100 pages at about $100 in Transkribus against about $1 with Gemini — [Generative History](https://generativehistory.substack.com/p/gemini-3-solves-handwriting-recognition/comments)

### Inferences
- **6 GB GPU** (estimates):
  - kraken training and inference: fine.
  - n-gram LM decoding: CPU.
  - ByT5-small or mT5-small fine-tuning (about 300M parameters): feasible with small batches, fp16/bf16 and gradient checkpointing.
  - TrOCR-base fine-tuning: possible but slow (batch 1–4).
  - Local LLMs: 8B at 4-bit (6.3 GB measured) does not fit with headroom, so use 3–4B models or CPU offload.
- **24 GB rented card** (estimates):
  - TrOCR ensembles and ByT5-base correctors: comfortable.
  - 8B LLM in fp16 or 14B at 4-bit: fits for inference.
  - QLoRA fine-tuning of 7–14B correctors: feasible.
  - 24B at 4-bit: borderline for inference, and roughly 13–15 GB of weights.
  - 70B: not feasible (needs about 44 GB at 4-bit).
- Order of cost-effectiveness (inference): n-gram LM decoding and the segmentation diagnostic (CPU, days of engineering) < confidence filtering and self-training (GPU-hours) < ByT5 corrector (tens of GPU-hours on 24 GB, including cross-validated pair generation) < TrOCR ensemble (N × training) < LLM pipelines (API costs plus audit effort).

### Gaps
- I found no published GPU-memory or throughput figures for kraken 7 training, ByT5-small HTR correctors, or TrOCR fine-tuning on 6 GB cards. Those figures above are estimates.
- No per-page API cost study for multimodal LLM correction of historical handwriting was found beyond the cited claims.
