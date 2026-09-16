# NOTES — strategy review of 2026-09-16 (follow-up work, not yet done)

_Repo notes from the review that shipped Phase D on v1. Nothing here is built;
each section says what would be built, why, and what it depends on. `STATUS.md`
links here from its Open questions. Numbers cite `reports/` unless stated._

## A. Accuracy levers, in the order they pay

1. **v2 fine-tune (C3)** — expect about one CER point on the PHILIUMM
   validation set (7.95% → ~7%), not more, for the reasons and with the four
   changes recorded in the C3 amendment in `PROMPTS.md`. The corpus-wide gain
   (correspondents' hands, drafts) is likely larger and invisible to that set —
   hold out a corpus-representative, page-disjoint slice of the minted GT and
   report both.
2. **Character n-gram LM decoding** — ~−12% relative CER in PyLaia (Tarride et
   al. 2024); not in Kraken; implementable over the CTC logits (torchaudio
   `ctc_decoder` + KenLM). Train the LM on diplomatic GT only.
3. **Targeted review beats volume.** On the val split, correcting the worst 10%
   of lines by CER leaves 5.3%; the worst 20% leaves 3.6%; the worst 30%, 2.4%
   (computed from `reports/philiumm-repro.lines.jsonl`). The lever is a
   *calibrated flag*, not a corpus-wide pass. Candidate flags, cheapest first:
   - per-line CTC confidence, already stored (calibrate it: measure CER by
     confidence band on the val split with `transcribe_conf`; temperature-scale
     if needed — PyLaia reports ~0.7–0.8 correlation with line accuracy after
     calibration);
   - v1 vs v2 disagreement, free after C4;
   - two independent vision-model readings disagreeing (Isom 2025's recipe:
     flag, never rewrite, when two runs differ by >5% CER);
   - a text-only LLM plausibility flag — weakest; the literature (Boros et al.
     2024; Kanerva et al. 2025) shows text-only post-correction is net-harmful
     on near-correct historical text and rewards normalization the metric forgives.
   **Pilot:** score each flag's precision/recall at catching lines with CER >10%
   on the 1,878 val lines. A day with the existing harness.
4. **Image-grounded LLM correction as a second, labelled layer** — Humphries et
   al. 2024: strict CER 10% → 4% with a *different* model than the recognizer
   (no self-correction ability); but most of the remaining "gain" is
   punctuation, capitals and spelling modernization. For the diplomatic layer
   that is corruption; for a reading/search layer it is the goal. Ship as
   `status='corrected'` rows with `source={"method": "vlm-grounded", …}`, never
   overwriting `machine`; run first on the ~14% of lines below 0.7 confidence
   (low four figures via the Batch API); never corpus-wide without a grant.
5. **When is CER "good enough"** (for the About page and the paper): reading
   <5% very good, 5–10% good, >10% poor (Muehlberger et al. 2019); exact-match
   search degrades from ~5%, keyword spotting works to ~30%, WER predicts
   search behaviour (ours 27%); NLP wants word accuracy >90%, floor 80% (van
   Strien et al. 2020); RAG/QA: French "high noise" ≥5.6% CER (MultiOCR-QA
   2025; OHRBench 2025) — 7% is not RAG-comfortable, so RAG must run on the
   corrected layer and cite line ids + images.

## B. Calculemus — rescope, not abandon

- **Slot:** alignment trains the model everywhere; Calculemus adjudicates
  specific lines into `corrected` (never `verified`, never training data by its
  own SPECS). Throughput from its simulator: ~39 encounters per converged line
  at 8–10 s → ~10 lines per player-hour; the corpus would need >1M player-hours.
  Its structural advantage: alignment reaches only the ~2% of lines with a
  printed edition; on the other 98% a human is the only source of truth.
- **The real gate is candidate generation, and it sits here.** `lines` stores
  one hypothesis per line per run; no n-best. Cheapest candidates: v1 vs v2
  disagreement after C4; then an image-grounded VLM reading as a second
  heterogeneous reader; deterministic confusion variants last (they only
  confirm what v1 already got right). **Measure the unmeasured number first:**
  fraction of v1/v2 disagreements on the val split where either reading is
  exactly right, per stratum. Below ~70% on heavy revision, aim A/B at fair
  copies/light revision and at GT audit; the rest needs free transcription.
- **The LL seam** (Calculemus SPECS Appendix A): `leibniz pack fragments`
  (fragment-pack JSONL from `lines` + `pages` + crosswalk + gold rows from
  open-bucket `gt_lines`, `license_bucket='open'` enforced) and `leibniz pack
  judgments` (import `converged` rows as `status='corrected'` with the judgment
  row verbatim in `source`; `both_rejected` → a Scriptorium queue report).
  Neither exists. Demand weights should come from search logs and Reference
  Desk misses once D1 is live.
- **Cheapest scientifically valuable deployment:** finish the stalled 200-line
  GT audit with a gold-heavy, scholar-mode-only pack (minted text vs HTR
  reading over the strip). Caveat for players: edition text is normalized
  (expanded abbreviations), so "matches the image" must be explained, or the
  fold applied to both candidates.
- **Scriptorium** (free transcription for `both_rejected` and the unprinted
  98%) = LL's E1 micro-UI. Neither repo has it.
- Calculemus's docs carry no throughput model or audience estimate; one page of
  arithmetic belongs before its P5 art phase.

## C. The four thin seams to The Academy of Games (SPECS §11 promised them)

Greenfield on the Academy side: its Magister has one hard-wired retrieval tool
over a hashed bag-of-words index with no ANN index; ingesting 13.5M lines there
is not viable (uuid `refId`, per-item LLM cataloguing, no third-kind visibility
branch). All four seams consume *this* project's D1/D2 surfaces:

1. **Magister search tool** — a `search_nachlass` tool backed by a thin remote
   adapter over `/api/search` + `/api/pages/{id}` (degrades to nothing when the
   URL env var is unset), a new ADR, and citations carried in the Magister's
   structured envelope because its post-filter strips URLs from prose; the
   chat renders no citation block today, so that UI is the largest piece.
   Wording rule: "the machine reads it as …", never "Leibniz wrote".
2. **Reference Desk source** — the same adapter through `reference.ask`, which
   already renders a "Sources cited" block; the natural home for a
   status/confidence badge.
3. **Theatrum exhibit** — once D2 is deployed, a link-only exhibit pointing at
   the viewer (link-rot watched by its `theatrum_health` job).
4. **Library materials** — a handful of `materials` rows for the four Zenodo
   records and, later, the dataset/model DOIs, so the Magister can *name* the
   project before any search seam exists.

## D. Loose ends found in the review

- Academy `docs/decisions/0003-library-embeddings.md` says `vector(256)`; the
  code and migration 0016 use 1024. Two ADRs share the number 0018. (Not fixed:
  Academy updates were out of scope this session.)
- PHILIUMM's transcription conventions live on an access-controlled wiki; the
  HF dataset card does not state diplomatic vs normalized handling of
  abbreviations. Any published "diplomatic fidelity" claim must say what was
  verified.
- SPECS §1.5 credited Bullinger with a ~7% CER model — corrected 2026-09-16
  (published model numbers 9.1–9.2%; 6.5% is their GT's own error rate).
- The `val` split was drawn from PHILIUMM's clean subset; verify page-level
  disjointness from `train_clean` before C3 checkpoint selection.
- 16 GWLB delivery URLs loop (works `00068368`/`00068744` a.o.) — report upstream.
