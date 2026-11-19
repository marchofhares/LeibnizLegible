# Divergences recorded to 2026-11-18 — Leibniz Legible

_The whole "Divergences" section of STATUS.md, moved verbatim by ARCH2 on 2026-11-19. Frozen: nothing is appended here. From 2026-11-19 a session records its divergences in its own phase file under `status/` (`status/README.md`)._

## Divergences (recorded per the COMMON-CONTEXT rule)

- **2026-11-17 — DQ1 (P1 Task 3 and M1 Task 1b), departures from the prompts,
  the notes and the preamble.** (1) *`python -m pytest`, not bare `pytest`*,
  for the baselines and the Finish: two test files import `tests.conftest`,
  which the bare command cannot find (ARCH1's Divergence 9). (2) *Her
  `requirements.txt` not installed as pinned*: rfdetr 1.8.0 needs supervision
  ≥ 0.29 (0.31.7 installed, her pin 0.28.0), and kraken 7.0.3 stands in for
  7.0.2 because 7.0.2 pins torch ≤ 2.10 and the torch this card is proven on
  is 2.12.0; everything else as she pins it. (3) *No `git lfs pull`*: only the
  `.pth` files are LFS, the two v2 checkpoints came from the Hub with the same
  sizes and digests as the clone's pointers, the v1 checkpoints were not
  fetched and the one-page v1 smoke test the note permits was not run. (4)
  *The pipeline read copies downscaled to 2,000 px on the long side, not the
  cached scans*: rfdetr 1.8.0 upsamples the masks of all 300 queries to the
  input size before thresholding and a 10–20 megapixel scan spills the 6 GB
  card into host memory (the guard killed the first pilot, the second crawled
  at 18 minutes a page); the census scales her zones and lines back to the
  scan's pixels, per page, and records the factor. (5) *Her step 6 was run as
  one kraken process per batch of 25 pages, in `16-mixed`, with a CPU pass*
  for pages wider than twice their height and for any page the card refused
  — the same command, flags, model and text direction as her
  `segment_page`, the model loaded once instead of once a page; her default on
  CUDA is `bf16-mixed`, which this Turing card lacks; her repository is
  untouched (the driver `tools/philiumm_layout_stages.py` calls her step
  functions, each stage its own interpreter, the operator's change 4). (6)
  *The driver wraps rfdetr's `predict` to empty the CUDA cache after each
  page* and the run sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`:
  a wrapper around a library call, nothing of hers changed. (7) *The model
  files sit in a runtime root on the VHD* (`data/philiumm/rfdetr-runtime/`,
  the working directory her relative model path resolves in) instead of in
  the clone on D:, because reads from D: over the share crawled beside the
  backup chore's reads; *the results are on the VHD too* (about 2 GB at
  2,000 px, not the multi-gigabyte outputs the D: rule is for), the scans
  symlinked as the operator's change 2 says and the 2,000 px copies written
  on the VHD (503 MiB), C: standing above 25 GB throughout. (8) *The images
  are named `<work>_<seq>.jpg`*, not by page id: a colon is illegal on the
  Windows file systems D: is one of, and the pipeline names its outputs by
  the stem. (9) *The strata*: `page_stats.stratum_heuristic` is NULL on every
  page, so the fallback is the OAI set — Briefwechsel and Handschriften, 200
  each, one page a work; the Leibnitiana (12 works, 1,768 pages) and the
  reconstruction set (28 pages) are not strata, and LH 35 works leave the
  Handschriften stratum for their own block. (10) *The `rclone check` of the
  backup chore is restricted to the day's two files*: a hash check of the
  whole folder reads 105 GB over the drive share. (11) *The registry gained
  the print trial's tools here* — dfine_kraken (Apache-2.0, read on GitHub),
  the LADaS D-FINE large model (Apache-2.0) and Gallicorpora+ marked as run —
  as the M1 note asks, while the two PHILIUMM v2 entries stay with the
  K3b-prep session as the DQ1 note says; `REGISTRY_DATE` moved to
  2026-11-17 so the new readings pass the registry's date check. (12) *The
  print trial's 50 lines are v1 lines inside LADaS print zones with at least
  15 characters of v1 text*, 25 from German-print pages and 25 from the
  others, one line a page a round: a rule of this session's, so a crop is a
  line of print and not a fragment. (13) *The two STATUS entries carry the
  DQ1 note's names* ("P1 — Task 3, the zone census", "M1 — the print trial
  (Task 1b)"), not the P1 prompt's "P1 — PHILIUMM cross-checks", whose entry
  is archived. (14) *Four pages have zones but no pipeline lines*: the four
  pages wider than twice their height went to the CPU pass, which was stopped
  by hand after 46 s so the kraken stage stayed inside the six-hour limit (a
  single wide strip had run over 11 minutes on the CPU in the pilot without
  finishing); the census counts them as pages without final lines. (15)
  *The kraken stage ran in `32-true`, not her CUDA default `bf16-mixed`*:
  the card has no bf16, `16-mixed` saved no memory and ran CPU-bound in the
  polygonizer at two minutes a page with a topology warning on most lines, so
  the stage was stopped after seven pages and resumed in fp32 with those
  seven kept.

- **2026-11-18 — REL1 Part A, departures from the prompt, the operator's
  note of 16 November and the preamble.** (1) *No go waited for* after Task
  0 (the cloud batch note of 17 November, the preamble's clause 6); the
  three questions were answered by the note, the namespace by a proposal.
  (2) *Work the prompt did not name, done because the cards could not be
  true without it*: the committed audit summary restored and the tests that
  overwrote it fenced; `reports/gt-factory.md`'s two audit passages
  re-rendered from it; the export opened read-only, read along the page
  index and streamed. (3) *`run_id`, not `run`*: the transcriptions' column
  is `run_id` (with `run_at`), and the card names it so. (4) *The cards'
  figures are read from the committed reports at render time*
  (`release/measured.py`), not typed into the cards, and the counts come
  from the manifest; "the counts in every card come from the export's
  MANIFEST" is kept by moving the audit summary, the deposit census and
  the store's summary into the manifest. (5) *`leibniz release cards`, not
  `export --cards-only --doi`*: a command of its own that needs no store;
  `export`, `cards` and `model` all take `--doi`, `--hf-namespace` and
  `--creator`. (6) *The scripts are thin entry points*; their logic is in
  `src/leibniz/release/zenodo.py` and `hub.py`, where it is tested. (7)
  *The Zenodo script has two steps*, `reserve` and `upload`, since the DOI
  must be in the card before the files go up; the prompt describes one
  pass. (8) *"Tests against a recorded response"*: one fixture is a
  recording (Zenodo's 403 without a token); the success responses follow
  the API documentation's field lists, since no token exists in a cloud
  session; Part B's step 2 is the live check. (9) *The model record's
  upload type is `other`*: the deposit API has no "model"; the browser step
  sets it. Its related identifiers are this session's choice in the
  checklist's pattern (the code, the Bern model's address, the project
  statement); the checklist's §3 named the PHILIUMM checkpoint, which this
  model does not derive from. (10) *The checklist said the mirror takes D2
  and D3*; the prompt says the open deposit only, and the upload script
  refuses the NC deposit; the checklist's line is amended. (11) *One command
  the prompt did not ask for*: `leibniz release check`, so the checklist's
  §1 checks against `/api/stats` are a command's PASS and FAIL lines. (12)
  *`huggingface_hub` added to the `release` extra* (already locked through
  transformers): a dependency change, made because hand-rolling the Hub's
  large-file protocol would be the larger risk. (13) *The LICENSE file
  names the Creative Commons licence and its address* and does not
  reproduce the legal code, which this session would have had to type; the
  base model's MIT notice is reproduced in full, as fetched. (14) *Numbers
  not produced here are quoted from where they stand*: K2's audit counts
  from the entry of 2026-11-16 (as the note allows), the store's expected
  counts in the runbook from the K4 entries; the only figures this session
  measured are the test counts, the restored audit summary and the
  synthetic store's 27.3 s and 289 MiB. (15) *The session ran past midnight
  UTC*: the records were read and the 403 recorded on 2026-11-17, the
  entry is dated 2026-11-18. (16) *The registry is untouched*: "(if
  released)" on `model-k3-trocr` and the "seen" dates are Part C's, on the
  day of the release. (17) *The merge of 2026-11-18* (main at #64): both
  sides' entries kept in STATUS.md and PROMPTS.md, REL1's above K3b-prep's,
  which in PROMPTS.md puts the later prompt above the earlier one against
  the file's own oldest-first order; and the operator's note's "credits
  them from the registry" is met by the wording the registry's note
  prescribes and the entry's licence, not by the entry's name.

- **2026-11-17 — R1 Part A, departures from the prompt, the preamble of 19
  October (as updated) and the batch note of 17 November.** (1) *No go
  waited for* at Task 0 or at the checkpoints (the preamble's item 6, the
  batch note). (2) *`.venv-cloud` on CPython 3.12.13 with the web, gt,
  release, bench and decode extras*, not uv's default 3.13 and not "bench +
  gt" alone: flashlight-text has no wheel for 3.13, the project's Python is
  3.12, and the web and release extras keep the whole suite running; the
  slim 3.13 environment of the other cloud sessions was run once beside it.
  (3) *The matrix is `(N, C, W)`*, labels by frames, in kraken 7.0.3, not
  `(N, W, C)` as the prompt and kraken's docstring say; the decoders take
  kraken's layout. (4) *The engine's confidence is the mean per-character
  posterior*, each character's the highest of its run, not "the mean
  per-step probability"; and TrOCR's stored figure is the mean probability
  of its generated tokens, not "the decoder's sequence score"
  (`htr/trocr.py`). (5) *flashlight-text directly, no torchaudio*:
  torchaudio is not in the lock at all; 2.11.1 still ships `ctc_decoder`,
  a wrapper around the same package. (6) *The language model's text is
  normalised to the reader's conventions, not through the aligner's fold*:
  the fold drops case, accents and punctuation, which a diplomatic reader
  writes and a model built on folded text could not score; the fold is the
  option `--fold align`, with the decoder mapping each label through it.
  (7) *The edition's running text is cut into lines of at most 48
  characters* (`--wrap`; 0 turns it off): "one line a sentence" on
  paragraphs would teach the model a paragraph's beginning and end, a
  capital and a full stop, where a manuscript line begins and ends anywhere.
  (8) *A record of the edition cache needs a named piece and channel*: a
  cache line without `refs` is left out and counted, stricter than
  `legal.deposit_for`, which lets a channel-less minted row go by its
  bucket; and the §70 test is applied to both sources on the day of the
  build, so the fixture's row of a 2027 volume stays out. (9) *The PHILIUMM
  "test split's pages" are the `val` rows of
  `reports/philiumm/heldout_pages.csv`*: the dataset has no test split
  (Open question 36 a). (10) *Additions the prompt did not name*:
  `--decoder prefix-beam` on the command line beside the two it names,
  `--beam-tokens`, `bench lm-tokens`, `KrakenEngine.temperature`,
  `transcribe_scored` and `posteriors`, `--extra`, `--sources`, `--fold`,
  `--form`, `--tokens`, pyctcdecode recorded in the registry as not used,
  and a date for the latest entry, `legal.REGISTRY_UPDATED` after the merge
  of 18 November (the registry's compilation date of 21
  October stays, since the other records were not re-read). (11) *The toy
  report is not committed*: `reports/decoding/` is written by Part B from
  the store; fixture counts under that name would read as the Nachlass's.
  (12) *`lmplz` and `build_binary` were built in the cloud container* from
  the kenlm source distribution (Boost's headers from apt) to prove the
  path; nothing of it is in the repository. (13) *Finish items done here*
  although the Finish is the whole phase's: the registry entries, the
  SPECS §4.5 amendment as far as Part A can state it, the prompt in
  PROMPTS.md; Key numbers' CER pairs and thresholds and the amendment's
  figures wait for Part B. (14) *The second `git merge origin/main`* before
  the final push found main where it was at the start. (15) *Merged with
  main at #65 on 18 November, at the operator's word* (K3b-prep, #64, and
  REL1 Part A, #65, had landed): conflicts in STATUS.md, PROMPTS.md,
  `legal.py`, its test and `uv.lock`. Both sides' entries are kept, the
  newer above (REL1 of 18 November, then this one, then K3b-prep); in
  PROMPTS.md this prompt stands last, after the two already on main; **this
  entry's Open question 34 is now 36** (REL1 had taken 34 and 35) and every
  reference of this session's to it is changed; the registry keeps main's
  `REGISTRY_UPDATED` and the three decoding tools join its test's list of
  entries added since; the lock keeps both sides' lines and `uv lock` leaves
  it as merged. After the merge: ruff clean, 318 files formatted, 1,225
  passed and 1 skipped (1,193 and 10 in the slim environment).
- **2026-11-17 — K3b-prep, departures from the prompt and the preamble of 19
  October (updated 21 October and 16 November).** (1) *No go waited for*: a
  cloud session started with the whole step records the pre-flight and
  proceeds (the preamble's clause 6, the cloud batch note). (2) *Two items
  outside the prompt*, at the operator's word during the session: bare
  `pytest` collects every test file; the viewer README's pointer to the
  archived "Delivery-model correction". (3) *The STATUS entry was written
  once, at the finish*, not after every task; the code was committed and
  pushed task by task. (4) *Task 5 before Tasks 1 to 3, and those three in one
  commit*: `audit-apply` checks its channel against the registry, and the
  three share one module. (5) *`audit-score --corrections` refuses to run on
  the defaults*: `--out`, `--summary` and `--overrides` must be named, where
  the prompt only says the K2 sheet is scored with them named. (6) *A fourth
  precision column*, under the fold with the boundary lines counted, beside
  the three the prompt names. (7) *The patterns of a re-written line come from
  the word-level difference to the judge's line*, where the prompt asks only
  that the correction come from the file: without it every converted row would
  have been *other*; the rules were written with none of the Edition's text to
  try them on. (8) *`--weights-reader` and `--title` on `audit-score`*, and
  the store opened read-only for the weights: K2's sheet was drawn from one
  reader's rows, so the whole mint's stratum shares are the wrong weights for
  it. (9) *`k3b-verified.csv` says `corrected`* for a line the judge re-wrote
  without a verdict, where the converted verdict CSV says *wrong*. (10)
  *`audit-apply` leaves and lists* a confirmed line whose stored text is no
  longer the sheet's, a line with no row and a line with more than one; it
  does not touch `license_bucket`. (11) *`db.record_run`*, a new helper, so
  that the run row and the rows land in one transaction (`start_run` and
  `finish_run` each commit). (12) *The sheet has a field for the corrected
  line and a five-column download*, where the prompt asks for the help text's
  sentence only; the context strips are greyscale JPEGs, not PNGs, for the
  sheet's size. (13) *`REGISTRY_UPDATED` added* instead of moving
  `REGISTRY_DATE`, which says when the older records were re-read; the outputs
  table was left alone. (14) *Numbers not produced here*: the registry entry's
  "200 rows, 118 with a corrected transcription" and the counts the synthetic
  200-row test is shaped on are the operator's, from the entry of 2026-11-16.
  (15) *The branch check made the clone shallow for a moment* (every remote
  tip fetched at depth 1 to read its `legal.py`); it was unshallowed from main
  before the next commit and nothing pushed was affected.
- **2026-11-17 — G1b, departures from the prompt and the preamble of 19
  October (updated 21 October and 16 November).** (1) *No go waited for*: a
  cloud session started with the whole step records the pre-flight and
  proceeds (the preamble's item 6, the cloud batch note of 17 November). (2)
  *"The row order … shuffled under the seed as before"*: G1's rows stood in
  line order (the G1 entry: "the rows in line order"); the rows are now
  shuffled under the seed, as the prompt asks, which is new, not as before.
  (3) *"The pack never reveals which rows are gold (check.py's rule)"*:
  `check.py` has no such rule and the contract's row carries `gold.is_gold`;
  what the pack can keep to is that nothing else tells a gold row from
  another (no key, no place in the file), which is tested; `check.py` and
  the schemas are unchanged. (4) *The gold is spread over the strata*, not
  drawn plainly among all candidates: each stratum gives truths and
  both-wrong rows by the allocation the rows use, a short stratum's share
  going to the others, so the cap is still reached whenever the supply
  allows; a plain draw would have put the gold where the pool is (heavy
  revision). (5) *The floor is `--min-ratio`*, the second of the prompt's
  two; `--min-chars` still bounds the longer reading only. (6) *A stratum
  the weights leave out gives no row and no gold*; the weights are relative
  and need not sum to 1. (7) *`--as-of-run`, which the prompt does not ask
  for*: since K4 the stored reading on the German pages is k3-trocr's, so
  "the first pack's readings and pieces" no longer gives the first pack's
  pairing; the option pins the first candidate to an earlier store, the
  default is unchanged, and the question is Open question 30 (j). The
  printout says "the stored reading" where it said "v1". (8)
  *`GoldPlan.verdicts` and `.withheld` are over the eligible lines*, not the
  selection, since the gold is chosen there; the printout gives both. (9)
  *Three commits*: the draw, `--as-of-run`, the record (the batch note:
  commit and push after every task). (10) *`python -m pytest`*, as ARCH1
  found (two test files import `tests.conftest`). (11) *The rebuild's
  commands under Next come in two forms*, today's store and `--as-of-run
  616`, because of (7); their expected output is given as the lines to read
  and the sums that must hold, without figures, except where the first
  pack's own counts must come back (the preamble's item 5). **Follow-up of
  2026-11-18** (the operator's word in the session, not a prompt of its own;
  nothing appended to PROMPTS.md for it): (12) *the merge orders the entries
  by when they were recorded*, not by side: REL1, R1, K3b-prep, G1b, ARCH1,
  as the two merges before it on main did; (13) *PROMPTS.md keeps main's
  order of its three prompts* (REL1, K3b-prep, R1) and sets G1b's before
  them, after ARCH1's, the order of appending; (14) *G1b's "merged as #63"
  on ARCH1's line in Next gave way to main's wording*; (15) *`--only-records`
  filters by the line's piece, not by the page*: on a page two pieces share,
  a line of a piece not listed is skipped (`other_record`) rather than given
  to the listed one; (16) *a list none of whose records is a piece is
  refused* rather than written as an empty pack; (17) *the tests figure is
  the slim environment's* (web, gt, release), where ten tests skip for want
  of numpy, torch, kraken, KenLM or flashlight; main's 1,225 is R1's fuller
  environment.
- **2026-11-17 — ARCH1, departures from the prompt and the preamble of 19
  October (updated 21 October and 16 November).** (1) *No go waited for*: a
  cloud session started with the whole step records the pre-flight and
  proceeds (the preamble's item 6, the cloud batch note of 17 November). (2)
  *Eight retained subsections, not seven*: the prompt's list names seven and
  "Prior gate (retained)" stands twice; all eight headings moved. (3) *Next's
  pointer line names what moved*, not "entries before 2026-10-19": twelve of
  the sixteen blocks older than 19 October moved, four stay with an open item
  each (the L1 note of 14 October, P1, W3, the A0–C2 block), and nothing dated
  2026-10-19 or later moved, LT1's Part B runbook included though it has been
  run (the kept entries point to it under Next); the pointer stands at the
  first emptied place. (4) *Two pointer lines in PROMPTS.md* where the
  original prompts stood, which the prompt does not ask for and the preamble's
  clause 8 does; the table lists the sixteen follow-up prompts only. (5) *P1's
  prompt is archived though its Task 3 has not run*: the prompt says every
  prompt under the heading. (6) *One old line is not verbatim in either file*:
  STATUS.md's "Last updated" line, extended at its head as every session
  extends it, its old text whole behind the new item. (7) *The proof counts
  blank lines and `---` rules as interchangeable*; on the content lines it is
  exact, order included. (8) *Three commits, not two*: the two moves as the
  prompt says, then this record and the prompt (the batch note: commit and
  push after every task). (9) *`python -m pytest`, not bare `pytest`*: two
  test files import `tests.conftest`, which the bare command cannot find in
  this environment (the ARCH1 entry, "Found on the way"). (10) *Nothing else
  touched*: the README's file list and the one line under `src` that names an
  archived section were left as they are (docs of this phase are the four
  files).
- **2026-10-28 — LT1, departures from the prompt and the preamble of 19
  October (updated 21 October).** (1) *No go waited for*: a cloud session
  started with the whole step records the pre-flight and proceeds (the
  preamble's item 6); every API, store and GPU step is handed over. (2) *The
  page reference comes from the dataset's PAGE XML, not the parquet*: the
  parquet has text and image only; the Hub's `val/` carries the pages (JPEG +
  XML). (3) *`--split test` means `val`*: the dataset has no test split; its
  held-out split is `val`, the one B1 scored. (4) *27 PHILIUMM pages, not
  50*: the held-out split has 27; the list carries them all (34 calls). (5)
  *PHILIUMM's images come from the Hub*, not the desktop cache or the mirror:
  the same GWLB derivatives (checked on one page: identical dimensions), and
  the XML's coordinates belong to them; 16 of the 27 are also store pages,
  recorded in the list. (6) *Openings are read as two halves* (left, right),
  the XML lines split at the midline — the protocol's "one column at a time";
  `page-list --no-split-openings` reads them whole. (7) *Claude cannot run
  without a thinking block*: thinking is always on on the Claude 5 models and
  `disabled` is a 400; effort *low* is sent and recorded; `temperature` is not
  sent (rejected). (8) *The Gemini id is `gemini-3.1-pro-preview`* (no bare
  `gemini-3.1-pro`); `gemini-4-argon` exists and is in the plan as a third
  model. (9) *numpy installed into `.venv-cloud`*, which the preamble's extras
  list lacks: the pool metric needs it (one package, no `uv sync`). (10) *The
  pool draw is by whole letters*: 100 pages = 34 letters, since the metric
  charges a letter for every line on its pages. (11) *The kraken model's page
  CER is a re-run on the val lines cut from the Hub's images*, not B1's dump
  (its ids name no page); the cut is `bench page-lines`. (12) *Three helper
  commands beyond the prompt's three*: `page-list`, `page-fetch`,
  `page-lines`. (13) *The pool diff's reference lines are the aligner's
  slices of the letter text onto k3-trocr's lines*: the pool has no
  line-segmented reference; the report says so. (14) *The report is code
  only*: no `reports/htr/page-llm.md` is committed, since no number exists
  yet. (15) *A first `ANTHROPIC_PRICES` table*: the Anthropic engine had no
  cost accounting before.

- **2026-10-26 — K4, departures from the prompt (Tasks 1 and 2).** (1) *A
  third precedence class.* The prompt's rule is scoped over unscoped, then
  the newest; the store already holds, since G1, a corrections run (stage
  `crowd`) whose rows must outlive every machine reading, and under the
  prompt's rule alone a crowd run written after K4 would lose to the
  Kurrent run on German pages. So the rule ranks a corrections run above a
  scoped run, read from the runs row like the scope. (2) *The threshold's
  sweep starts at two hits*, the identifier's own floor (one stopword
  decided a language on long pages in a first sweep, at 94.8 % precision);
  the chosen threshold keeps the identifier's floor and loosens its share.
  (3) *The German page set joins the census's pages* with the threshold's:
  the edition's text is the better evidence for the 1,180 pages v1 garbles
  past recognition, and each page's evidence is recorded; the prompt's
  "classified with langid" alone would have left them to v1. (4) *The stats'
  line count* is the current rows with text, not every row whose text is
  not null (the old count took 683,571 empty readings in); the index and
  the exports already left them out. (5) *The Marginalien* — the session
  proposed to leave the collection's German pages out of the reading job
  (Open question 31 (b)); the operator decides at Checkpoint A.
- **2026-10-22 — A3b follow-up, departures from the follow-up's text.** (1)
  *The sixteen hand changes are not listed here*: they are in the operator's
  dry-run report, which this session cannot see; the report now prints every
  change with before and after, and the operator pastes them into the A3b
  entry. (2) *The names carry the website's link markers* (the follow-up's
  test, ≥ 99 % on the compared records, was met on the 23 live records: 46 of
  46 cells); the GND ids are kept as asked and the KorrespDB ids beside
  them, since the website links both. (3) *`mergenr` never matches*: it is
  an internal number on 893 rows of the export, never a record id; the rule
  is implemented and will not fire on this export. (4) *The export's date is
  2026-10-19 throughout* (the registry, the fixtures, the tests, the
  hand-over's `--export-date`); the A3b entry of 2026-10-21 says "export of
  21 October" where it means the day the file was provided. (5) *The
  digitised-copies block is hidden by the viewer* when `refreshed` is null;
  the API still returns the figures. (6) *The before-import browser pass*
  skips the label check (that store has no printed witness) and the
  390 px state (the same layout as after). (7) *The short `JJMMTT` values*
  (three to five digits, 596 rows) are zero-filled to six and rendered by
  the same rule; the website's rendering of them was not seen.
- **2026-10-21 — A3b, departures from the prompt and from the preamble of
  19 October (updated 21 October).** (1) *No go waited for*: Task 0 says
  "record it, then proceed", and the session did (the preamble's item 6);
  the store is the operator's (Next). (2) *24 live GETs to the catalogue*:
  the prompt builds on fixtures, but "which Access column feeds which key
  is not to be guessed" and the store's records were out of reach, so 23
  records were fetched from the catalogue's extended search with the
  project's polite client (one per 1.5 s) and parsed with the website
  parser; the parsed records are the committed fixture, no page is. (3)
  *`--export-date` is required* on `import-access` (the prompt's command
  lacks it): the date reaches the site, so it is never implied. (4) *The dry
  run opens the store as every catalog command does* (`db.init_db`; no
  table written without `--write`). (5) *More keys than the prompt names*:
  `aa` (the rendered cell; the website parser parsed it and stored only
  `aa_refs`), `bemerkungen` and `bezuege` (parsed by the website parser,
  never stored), `aa_pdf`, `ordnungsvermerk_title`, `_komplex`, `_epoche`,
  and a reference without a volume in `aa_refs` where the cell names the
  series alone (what the API's `aa_planned`, built in W5, was waiting for);
  the comparison judges `aa` on the references with a volume. (6) *Two
  renderings differ from the website on purpose*: `32°` where the website
  prints a bare `°`, and a four-digit `JJJJMMTT` kept as the year where the
  website prints nothing (3 records). (7) *The agreement share leaves
  "export adds" out of its denominator*: a value the website never had
  proves nothing about the mapping; "export lacks" and "other" count
  against. (8) *The GWLB link by PPN* (416 rows) is taken as a work id
  beside `resolve?id=` (the prompt names `GWLB_RESOLVE_RE` only): the
  Marginalien's ids are PPNs, as Marg. 196 showed. (9) *`reports/holdings.md`
  is rendered from the export*, not the store (none in the cloud); its works
  section says so and the operator re-renders after the import. (10) *The
  Ordnungsvermerk level* is a field on each record, searched and shown by
  the Faszikel index, not a regrouping of the index. (11) *`reports/crosswalk.md`
  not re-rendered* (it reads the store). (12) *The K3 entry* the preamble
  names does not exist on main (K3 runs on the desktop, on its own branch).
  (13) *The holdings page's threshold*: holdings under 20 records are summed
  as "other" on a store of the whole catalogue; a store under 1,000 records
  (the fixture, a staging copy) shows every row. (14) *`identisch_mit`* is
  stored only where it names another record (2,595 rows name the record
  itself).
- **2026-10-21 — G1, departures from the prompt and from the preamble of
  19 October (updated 21 October).** (1) *No go waited for*: Task 0 says
  "record it, then proceed", and the session did (the preamble's item 6);
  the store, the box and the real pack are the operator's (Next). (2) *The
  K3 entry* the preamble names does not exist on main (K3 runs on the
  desktop, on its own branch); nothing of K3 was read. (3) *The fixture
  store's German rows* are an extension (`conftest.seed_german`, applied by
  a fixture of its own, `german_store_path`) rather than rows in
  `seed_store` itself, so that the 880 tests before G1 see the store they
  were written against. (4) *`provenance.model_alt`*: the prompt names the
  Bern reader "beside" the v1 row's model "as model_alt"; it is a key of
  `provenance`, the candidates keep the contract's four keys, and the schema
  allows it — an addition to the frozen contract (Open question 30). (5)
  *`canvas_id` and `folio_label`* are required by the contract and empty on
  some pages: a page without a GWLB canvas (the static works) names the
  site's own manifest canvas, a page without a label its canvas position.
  (6) *More rules than the prompt names*, each counted and printed:
  `no_page_size`, `already_corrected`, `not_german`, `no_provenance`,
  `no_geometry`, `no_shelfmark`; and a gold verdict the prompt does not
  name — both candidates fold to the minted text — which makes the row no
  gold. A record the census cites in several volumes is refused unless
  every one is §70-free. (7) *"Stratified by stratum"* is read as the audit
  sheets' equal allocation (`audit.allocate`), not a proportional draw; the
  printout sets the pool's shares beside the pack's. (8) *The shelfmark*
  falls back to the piece's signature where the work has none. (9) *`pack
  check` has its own validator*, not the `jsonschema` package, which no
  extra of `.venv-w3` installs and `uv run --no-sync` would not add. (10)
  *`pack judgments`* takes two options beyond `--in` and `--write`:
  `--fragments` (the fragment pack the judgments answer: the queue's second
  reading, and each winner checked against the line's candidates) and
  `--queue`; it refuses a judgment pack that does not check, renders the
  queue in a dry run too, and opens no run when nothing is new; the checker
  requires canonical line ids, which the import splits into page and line.
  (11) *An imported line's `conf` is the game's posterior* (the contract
  gives a crowd decision no other confidence). (12) *The environment*:
  `.venv-cloud` resolved to Python 3.13.16, as L1's. (13) *Scans registered
  twice* (W5's twins), which the prompt does not name, give each line one
  row, as the index and the exports count it: read for the preamble's W5
  entry, so that a physical line, and its gold, cannot enter the pack under
  two page ids.

- **2026-10-21 — L1, departures from the prompt and from the preamble it
  came with.** (1) *The branch.* The session was handed the older session
  preamble (8 and 14 October), which puts all work on
  `claude/dazzling-hopper-uxji2x`; the preamble of 19 October recorded in
  `PROMPTS.md` says that branch is merged (#45) and closed and that a cloud
  session works on the branch it was given at start. The repo wins: the work
  is on `claude/relaxed-dijkstra-uus9rz`, from main at `aafcb05`, and the
  staging line names `/opt/leibniz-legible/deploy/staging.sh` (the live
  checkout carries the kit since W4), not the staging checkout's. (2) *No
  go waited for*, and Task 0's "ask the operator, and wait" answered by the
  operator's note of 21 October, recorded verbatim (the preamble's item 6
  for a cloud session). (3) *The prompt's run rules* (the WSL checkout,
  `.venv-w3`, the branch `licence-registry`, "wait for merged", the §9
  deploy and the live check of /about) replaced by the cloud rules: a fresh
  `.venv-cloud`, the fixture store, the staging line and `curl` checks under
  Next. (4) *The registry's home.* The registry is in `src/leibniz/legal.py`
  as the prompt says; the `leibniz legal` commands live in a sibling module,
  `src/leibniz/legal_cli.py`, so that the registry module (imported by
  `volumes_sources`, `attribution`, the cards) does not import typer and
  rich. (5) *Live reads.* The Zenodo and Hugging Face records were re-read
  (seventeen GETs, one per 1.5 s) so that the "as currently published"
  column carries today's date and the record's own field rather than
  hearsay; the prompt's Gallicorpora+ note ("repository CC0-1.0; the licence
  on the record to be confirmed") is confirmed as CC BY 4.0 on the record,
  the repository itself unread. GitHub-hosted repositories (dfine_kraken,
  whose licence the prompt says to read; YALTAi; the Nantes code) were not
  read, because this session's GitHub access is scoped to this repository;
  the entries say so and the operator's line is under Next. (6) *The three
  Dresden sets.* The repo's tooling holds one Dresden set (the Kurrent Trace
  package, from Zenodo 15303243); that record's related identifiers name two
  siblings (15295553, 14356190), which were read and entered as not used, so
  that "the three Dresden sets" are three entries with their field licences.
  (7) *Rows without a channel.* The prompt's deposit rule is by channel;
  rows minted before the factory wrote the channel into `source` (none in
  the master store since C2c; the fixture store's two) have none, and the
  export puts an open-bucket row without a channel into the open deposit by
  its bucket, the factory's legal gate, and says how many such rows a
  deposit holds (`(not recorded)`), rather than dropping them silently.
  (8) *The letter pool* has a channel key (`letterpool`) and `deposit=None`
  in the registry so that a row of it can never reach a deposit, although
  no such row exists: K2b's standing rule ("never in a release") is kept
  over the amendment's "NC-derived ground truth released as a second
  deposit", which the entry notes as "training allowed by its licence for
  an NC model, after K2b's split — recorded, not done". (9) *The README*
  is amended though the prompt does not name it, because its licensing
  summary said NC sources are "excluded from public releases", which the
  second deposit makes false. (10) *The pairs rule.* The prompt's test
  "the nc rule in align/pairs.py agrees with the registry for the sources
  it names" names two sources (§70 text, the Transkriptionspool); the test
  also checks every channel `volumes_sources` can write against the
  registry, since the channels are what the deposits turn on. (11) *The
  environment.* `.venv-cloud` resolved to Python 3.13.16; 859 → 880 tests
  there, the letter-pool evaluation skipped for want of numpy, as before.

- **2026-10-21 — K3, departures from the prompt and the preamble.** (1) *The
  machine crashed during Task 2.* At about 09:27 EDT, with the kraken timing
  pilot running at batch 8 (its second attempt; the first, at batch 16, had
  died at the first steps with `CUDA error: unknown error` once the card's
  memory reached 4.8 GB) and the kraken 7.1 side environment installing,
  every process on the WSL machine failed with bus errors; the operator's
  diagnosis is that Ubuntu's virtual disk on the host's C: drive could not
  grow (C: had about 40 GB free afterwards). The card had reached 5.9 GB of
  its 6,144 MiB in the pilot's last minute (K2 saw the same spill into shared
  host memory under WSL2). After the restart: the store passed
  `PRAGMA quick_check` (the operator); the training set on disk was verified
  against its manifest (58,729 crops, none missing, none zero-length, every
  PNG trailer and sidecar intact, 9.42 GB) and kept where it is; the uv cache
  held 34 wheels damaged by the crash (invalid `WHEEL` metadata), cleaned one
  by one with `uv cache clean` until the side environment installed; the
  branch was merged with `origin/main` (W6, #49), STATUS.md keeping both
  sides' entries with K3 above W6 (the phase in progress), as the preamble's
  rule 7 says. (2) *Model artefacts live on D:.* By the operator's
  instruction, every checkpoint and optimizer state goes under
  `/mnt/d/leibniz-train/k3/`; `data/models/k3` is a symlink to it, so the
  paths the prompt and the reports name still hold; `df -h /mnt/c` is the
  budget for every write to `/` from here on, and each training job states
  its expected disk use against it before it starts. (3) *Guards.* Every
  training job runs under `tools/gpu-guard.sh`, which samples the card every
  two seconds and kills the job before its memory passes 5,300 MiB; the
  TrOCR loop fails itself when its reserved memory passes `--max-mib` (4,500
  by default); the kraken pilot runs at batch 4 with 4-step gradient
  accumulation instead of batch 16. (4) *The kraken 7.1 side environment*
  (`.venv-k3-ppocr`: kraken 7.1.1, torch 2.12.0 pinned to the cached wheel,
  the project installed editable without dependencies) is the amendment's
  "separate environment" for PP-OCRv6; `.venv-k1` stays at kraken 7.0.3 as
  the prompt says.
  (5) *The TrOCR pilot epochs ran twice.* The first pass over 20,000 lines
  per setting (16:20–18:43) lost its validation: the loop generated at batch
  16 with the per-step scores kept (half a gigabyte for the confidence no
  validation needs) beside the training state, and ran out of memory under
  the cap; the pilot had saved no weights, so the epochs were run again
  (18:47–21:15) with the validation generating at batch 8 without scores
  after the optimizer and the gradients are dropped, and each pilot's weights
  kept on D:. The timings of both passes agree (8.35 / 8.24 and 3.53 / 3.55
  lines/s); the first pass's rows are in `data/models/k3/trocr/pilot-noval.json`.
  (6) *The PP-OCRv6 pilot at batch 4 was killed by the guard* at its first
  steps (5,835 MiB on the card) and rerun at batch 1 with 16-step
  accumulation.
  (7) *Two jobs at once, three times.* The host ran out of memory at the 07:36
  and 07:58 launches of 22 October (the PP-OCRv6 pilot's CPU scoring started
  beside the kraken training's start-up; the machine went down both times),
  and on 25 October at 15:54 the guard killed the letter-pool read of the K3
  models at its host floor (available memory 6,981 → 1,778 MiB in eight
  seconds) because the same CPU scoring ran beside it; the session itself then
  ended while waiting. Every one of these was the session's own pairing of a
  GPU job with a second torch process on the 9.9 GB host. The rule from here,
  the operator's: one job at a time, the GPU idle before each, nothing else of
  the session's on the machine while a job runs, the disk use stated against
  C: before any job that writes.

- **2026-10-21 — W6, departures from the prompt and from the preamble of
  19 October.** (1) *The LBr spelling.* The prompt's context said the
  catalogue writes the correspondence with a period (`LBr. 164`); live,
  `LBr. 164` and `LBr. 464` answer nothing and `LBr 464` eleven records, so
  the rule, the docstring and the tests say `LBr` without the period. (2)
  *Eight live searches, not three.* One per family as the prompt asked
  (Marg. 196, LH 4, 6, 18, LBr. 464 → 0 and then LBr 464) and four more to
  settle the forms the rule depends on (`LBr. 164`, `LBrF 1`, `Leibn. Marg.
  135`, `Leibn. Marg. 175`); one request per 1.5 s with the project's
  User-Agent, all recorded in the W6 entry. (3) *A third key.* Each
  `katalog_search_urls` entry carries `query`, the catalogue's spelling,
  beside `shelfmark` and `url`, so an API reader sees what is searched when
  the library's spelling differs. (4) *`work.katalog.none` removed*, as
  "replaces" said; a work with neither records nor a shelfmark shows the
  sentence alone, on the server-rendered page and in the viewer. (5) *The
  prompt verbatim.* The phase prompt is appended to PROMPTS.md in full; the
  preamble of 19 October, word for word the one printed under K2b (checked
  with `diff`), is referenced there, as K2 did. (6) *No go waited for*, per
  the preamble's item 6 for a cloud session; nothing touched the box or the
  store. (7) *The environment.* `.venv-cloud` resolved to Python 3.13.16
  (uv's default in this container); 856 → 859 tests there, the letter-pool
  evaluation skipped for want of numpy, as in `.venv-w3`. (8) *The browser.*
  Playwright 1.64.1 drove the preinstalled Chromium
  (`/opt/pw-browsers/chromium`) against a local server, so the proxy's CA
  was not needed; the GWLB's thumbnails were stubbed as W4 did.

- **2026-10-20 — C2c, departures from the prompt and from the preamble of
  19 October.** (1) *Three goes for the writes, not two.* `leibniz align
  gt-reset` without `--yes` fills the ownership column under the write lock
  and commits before it asks, so answering no leaves the column, two
  indexes and 297,424 owners in the store; found in pre-flight, the
  operator gave a go for that invocation (after the backup), another for
  `--yes`, a third for the shards. (2) *"Read-only" through a read-write
  connection.* `edition-cache`, `gt-report`, `audit-sheet` and
  `philiumm-vi4 match`/`compare` open the store with `open_db`, which
  connects read-write and runs the schema's `IF NOT EXISTS` DDL and the
  `pages` migration; a comparison against a fresh schema found nothing to
  add except `gt_lines.record_id` (which `gt-reset` adds), and the store's
  modification time did not move across `edition-cache`. The census, the
  counts and the before/after analysis used `mode=ro` + `query_only`. (3)
  *The second sheet's HTML is not committed.* `reports/gt-audit/round2/`
  commits `gt-audit-lines.csv`; `gt-audit.html` (55.7 MB of embedded image
  strips cut from the GWLB's scans) stays on the desktop like the first
  round's, which was never committed. (4) *The analysis went past the
  reports.* To explain the mint's growth, the old mint was read from the
  backup and every record's placement recomputed under the code before W5
  (`9c96c7f`, a scratch worktree, removed after) and today's, read-only;
  scripts and outputs stayed in the session's scratchpad. (5) *The shards'
  end was read late.* The session's watcher for the six processes matched
  its own command line in `pgrep` and never fired; the shards ended by
  15:00 EDT and their logs were read at 16:57 when the operator asked. No
  effect on the data. (6) *The old cache and flags kept.*
  `data/gt/edition_cache.pre-c2c.jsonl` (the prompt's) and
  `data/gt/flags.pre-c2c.jsonl` (not asked; the before side of the
  census), both under `data/`, uncommitted. (7) *Tests.* The baseline and
  the final run are in `.venv-w3` (831 passed, 1 skipped: the letter-pool
  test needs numpy, which the w3 extras do not bring); Key numbers keeps
  K2b's 841 from `.venv-k1`. No code changed.

- **2026-10-19/20 — K2b, departures from the prompt and from the preamble of
  19 October.** (1) *No `tools/fetch-letterpool.sh`.* The prompt offered a
  script or a `leibniz align letterpool-fetch` command; the command alone was
  built, since it records the registry as it fetches. (2) *No edlib.* The
  infix alignment is a vectorised numpy dynamic programme, which the prompt
  allowed ("or a banded DP"); nothing was installed. (3) *"K2's German
  pieces".* K2 has not run, so the page-disjointness check used the K1
  census's `data/kurrent/german_pieces.jsonl`, the pieces K2 will mint from;
  the check is to be repeated against K2's minted pages when they exist. (4)
  *The citation names people.* The pool's Zitierhinweis names the volume's
  compiler and editor; it is carried as given in `letterpool-sources.json` and
  `letterpool-eval.md`, as attribution under CC BY-NC asks, while STATUS.md
  and PROMPTS.md say "the volume's compiler and editor". (5) *The reading job
  was stopped and relaunched once.* Five minutes into the first launch
  (philiumm, 4,218 lines) the loop was spending most of its wall time on the
  page images and the polygon cuts, repeated for every reader (64 ms a line
  against 15 in the model); a crop cache was added to the pilot's reader as a
  backwards-compatible option, and the job relaunched resumably with the 4,218
  readings kept. (6) *The scoring ran twice.* The reading job scores at its
  end and did so with the module as imported at launch, before the readers'
  table's lines-read count was changed to count per letter; the set was
  re-scored from the same readings the next morning (the same numbers, that
  column apart), and that run's reports are committed. (7) *The spot check.*
  The ten letters were checked against the PDF's text layer dumped line by
  line with positions and sizes (what the parser reads), not against the
  rendered page.
- **2026-10-09 — K1, departures from the prompt and from the plan's
  preamble.** (1) *Where it ran.* The Claude Code session opened in
  `C:\Users\evana\LeibnizLegible`, a Windows clone from July (a 96 MB store,
  an old branch, an uncommitted operator edit to `reports/census.md`, all
  left alone); every command ran in the WSL checkout
  `/home/evana/LeibnizLegible` through `wsl.exe`, where the store, the
  environments, the image cache and the GPU are. (2) *Branch.*
  `claude/dazzling-hopper-uxji2x` per the preamble, not `kurrent-k1`; the
  hand-over's compare URL names it. (3) *`.venv`.* The prompt calls it the
  pipeline environment with kraken and torch; it holds neither
  (site-packages of 2026-09-20). Nothing in K1 uses it; `.venv-k1` carries
  the stack. (4) *Textart.* The stratum is computed "exactly as the factory
  computes it", abbreviations unmatched and all; the finding is recorded
  (Open questions #23), not fixed. (5) *The German list.*
  `german_pieces.jsonl` holds the `de` pieces and the `mixed` ones with
  German leading (113 of 2,173); the `language` field tells them apart, and
  K2 may filter. (6) *The harness.* `evaluate.LineEval` gained `burst` and
  `summarize` a `factory_gate` option, off by default; the B2 report's
  numbers are unchanged. (7) *Two checks the prompt did not ask for.* The
  census reads the minted text's language and the machine text's length
  behind every minted line, because the hypothesis test came out half-way
  (German minted at half the rate, not near zero) and the question "what did
  the factory mint on German pieces?" needed an answer without ground truth.
  (8) *The tolerance model's op mix* is substitution-heavier than the
  recorded errors, on purpose and said so: the harder case for the gate. (9) *The gos.* The operator's "go" came on the pre-flight
  plan, which named the Task 3 downloads (which models, 4 GB) and the Task 4
  run with their sizes as the points needing one; they were not asked for a
  second time. (10) *TrOCR output* is tidied of the space the models set
  before punctuation; the raw convention is the labels', not a misreading,
  and the report says so. (11) `audit.crop_line` gained keyword options
  (`pad`, `max_width`, `mask_polygon`); its defaults and the sheet are
  unchanged. (12) *The pilot's size.* Pages capped at 2 per piece (the
  prompt says "cap pages"), pieces with fewer than 20 recognised lines left
  out, batch 16; the first launch decoded the page image once per line and
  was stopped and resumed after the fix (the readings are resumable, nothing
  was lost). (13) *The gate rule* was fixed before the numbers: GO when the
  controls order correctly and the best reader beats the baseline's German
  yield; whether it reaches half the baseline's control yield is said beside
  it.

- **2026-10-08 — W4, departures from the prompt and from the plan's
  preamble.** (1) *Where it ran.* A cloud session with no store: Task 0's
  look at the live page ran here (headless Chromium through the proxy), the
  browser checks of Task 4 ran against the fixture store, and the real-store
  and staging checks are handed over (Next); the operator asked for the step
  to be completed in one session, so Task 0's "wait for go" was not waited
  for and its findings are recorded instead. (2) *Branch.*
  `claude/dazzling-hopper-uxji2x`, the plan's one branch, not
  `web-text-access`; no "merged"; Task 5 replaced by `staging.sh` and the
  checks against staging, as the plan's amendment says. (3) *The line list.*
  Beyond unblocking the selection, page.js answers a `copy` whose selection
  lies in the list with the lines' selected text alone: Chromium left a
  blank line where the badges were, and `Selection.toString()` still
  reported them. (4) The header's link list gained "Text of this page", an
  anchor to the block, in place of the download it lost; the prompt names
  neither. (5) A record is placed from the *first of its shelfmarks that
  carries a folio range* (the factory reads the first shelfmark only) and
  from its best crosswalk link, then the next link where the best cannot
  place it. (6) The piece's download is named
  `leibniz-legible_record-<id>.txt`, so a record id can never be read as a
  work id. (7) The record header carries `attr.KATALOG` beside the project's
  own licence line, since catalogue data travels in the file. (8) The
  fixture's k-109 resolves to three pages, not the prompt's "two of three":
  `Bl. 1-2` includes folio 2's recto, the skipped third page; the tests
  state it. (9) The string `page.download` is gone; `page.text.download`
  names the moved link. (10) `resolve.py` gained `index_pages` and
  `select_folios`, and `db.py` `crosswalk_for_record`, beyond the prompt's
  list of files.

- **2026-10-08 — S1, departures from the prompt and from the plan's
  preamble.** (1) *Where it ran.* A cloud session with no SSH: Task 0's
  look at the box and Task 4's install are handed over as commands (Next),
  as the C2b and P1 sessions did with the store. (2) *Branch.*
  `claude/dazzling-hopper-uxji2x`, the plan's one branch, not
  `deploy-staging` and not the session's own designated branch; no wait for
  "merged"; no §9 production update: the kit is installed from a clone of
  the branch, as the plan's amendment says. (3) The install folds Task 4's
  step 3 in: `staging-install.sh --branch BRANCH` ends by running
  `staging.sh BRANCH`. (4) `staging.sh` has `--status` and `--drop-index`
  beyond the prompt's `--main` and `--index`. (5) The user name is asked
  for on the terminal when `--user` is not given (the prompt had the
  session ask the operator; nobody could answer here). (6) The staging
  index is `leibniz_pages_staging` and the key's scope is checked, not
  widened: `meili-search-key.sh` already scopes the key to
  `leibniz_pages*`. (7) `staging.env` is installed from the example with
  the live env's store path, key, image origin and proxy address copied in,
  since the example cannot carry the key. (8) The password stays although
  the operator said an unlisted host would do (the S1 log says why). (9)
  `--index` and §14 cite §5's measured 5 h 33 m for the live build; no new
  figure was produced.

- **2026-10-07 — C2b, departures from the prompt.** (1) *Where it ran.* The
  prompt assumed the WSL2 checkout with the master store and `.venv-w3`;
  this session ran in a cloud container on a fresh clone with no store, in
  a side environment `.venv-cloud` (`gt` + `web` + `release` extras). So
  the stratum weights for `audit-score` came from the committed C2 mint
  counts (`--weights`, named in the report), and Task 3's reach census was
  built and tested on a seeded store only. The operator then ran both on
  the master store on 2026-10-08: the score reproduced 72.3 % and the
  census numbers are in the C2b log. (2) *Branch.* `claude/dazzling-hopper-uxji2x`,
  the session's designated branch, not `c2-audit-closeout`. (3) *Pattern
  names.* `bracket`, `normalization` and `reading` were added to the
  prompt's list (see the C2b log for why). (4) *Precedence.* A *boundary*
  verdict names its line before the hyphen signal; the prompt had the
  hyphen rule first. (5) *The override file* was written by this session
  from the notes (three lines), not settled by the operator in chat; the
  `why` column says so and the operator may change it and re-run. (6)
  *Second witness.* Strips under four folded characters are no longer
  listed for re-checking (a rule change to the 2026-09-16 tooling). (7)
  `audit-score` without `--weights` now refuses a missing store instead of
  creating an empty one (the old behaviour would have scored with equal
  weights, silently).

- **2026-10-06 — W3, departures from the prompt.** (1) *Where it ran.* The
  prompt assumed a Windows checkout (Windows uv, `.venv-win`, the suite's
  Windows failures listed). This checkout is the WSL2 tree the corpus runs
  used, opened from Windows as `\\wsl.localhost\Ubuntu\…`, so git, uv, pytest
  and the app ran inside WSL through `wsl.exe`: Windows git reports this
  tree's shell scripts as modified (mode bits) and has `autocrlf=true`, and
  SQLite across the 9P share is not something to try on the master store.
  The side environment is `.venv-w3`, and `.gitignore` has `.venv-*/` rather
  than `.venv-win/`. The suite was not run on Windows. Playwright ran from
  Windows Node in the session's temp folder (not `scratchpad/pw`) against the
  WSL server over localhost; its screenshots stayed there. (2) *The letters'
  names are checked against the order of their numbers*, beyond the prompt's
  "most frequent name" (Phase log W3): fewer names, none knowingly wrong.
  (3) *The correspondents query* has one predicate more than the prompt's
  export (`OR w.shelfmarks LIKE '%LBr%'`), for the LBr convolute filed in the
  manuscripts' set; the fixture was exported with the module's own query.
  (4) *The family follows the shelfmark, not the set*, except for the two
  small sets. (5) `catalog/shelfmarks.py` gained `split_family()` — the label
  search of `normalize_signature`, extracted so the tail can be read as
  written; keys and matching are unchanged. (6) In `/api/works` the `groups`
  tree lists work ids and the rows carry the rest, so each title travels
  once. (7) The prompt calls the LH sections "the Ritter scheme"; this
  repository's own texts give the LH and LBr shelfmarks to Bodemann's
  catalogues (1889/1895). The page names neither and says the section names
  are cut from the library's titles. (8) The EN/DE buttons' spoken names
  changed (an axe finding older than this phase, on every view).
- **2026-10-02 — W1 text export, two departures from the prompt.** (1) The
  download name is `leibniz-legible_<id>.txt` with the page id's colon as `_`
  (`leibniz-legible_00068221_0043.txt`): Windows refuses `:` in a file name;
  browsers would rewrite it anyway, curl and other clients would not. The id
  itself, colon included, is in the file's header. (2) The work export names
  the source image and the model/run/date per page, under each `## Folio`
  heading, rather than in the work's header: every page has its own image,
  and the corpus run's batches give neighbouring pages different run ids. The
  TSV variant is served as `text/tab-separated-values`, the plain variant as
  `text/plain`.
- **2026-09-30 — `tools/` introduced for operator-run helper scripts.** Not in
  the SPECS §4 package layout; it holds shell scripts the operator runs on the
  desktop that holds `data/`, never pipeline code. First entry:
  `tools/fetch-kurrent-trace.sh`, which downloads (or takes a local copy of),
  checksum-verifies, unpacks and validates the "Kurrent Trace v0.1" package —
  383 Dresdner Hofdiarium 1673 line crops with transcriptions (Beckert, Zenodo
  15303243) plus 180 unlabelled machine segments from LH 35, 3 A 8, Bl. 22r–v —
  into `data/external/kurrent-trace/` (gitignored). It is the Kurrent smoke-test
  set for the planned Kurrent track (K1). Its Dresden text carries a licence
  conflict (Zenodo field CC BY 4.0, README CC BY-NC-SA 4.0): nc bucket, internal
  evaluation only, never exported or committed, until the author resolves it.
- **2026-09-27 — a sibling application shares the host.** Calculemus, the
  game built on this corpus, runs on the same VPS under its own user, unit
  and Caddy site block (`deploy/README.md` §13). No link to it renders on
  leibnizlegible.com unless `LEIBNIZ_CALCULEMUS_URL` is set; default off.
- **2026-09-16 — page images served from the project's own mirror, not from
  the GWLB (operator decision).** SPECS §3.4 and §7.1 say the viewer loads
  images from the GWLB's IIIF endpoints and that nothing is rehosted. The
  public site (leibnizlegible.com) instead serves the A2 image cache — the
  GWLB's own delivery derivatives, Public Domain Mark 1.0, no related rights
  under §68 UrhG — from `images.leibnizlegible.com` (Cloudflare R2), plus
  thumbnails derived from them. Reasons, in the operator's words: uptime,
  control, engineering (the line polygons were computed on exactly these
  files, so the overlay sits on the pixels the HTR read), and the framing
  that a free open-access resource competes with no Leibniz project and
  serves the same goals every Leibniz scholar has. What does not change:
  every page links to its original at the GWLB; the page API, the
  annotations and the dataset exports keep naming the GWLB URI as the
  source image (§4.5 provenance); the attribution names the GWLB and the
  Public Domain Mark on every view; the GWLB is told before launch. The
  code keeps the direct-from-GWLB mode as its default —
  `LEIBNIZ_IMAGE_BASE_URL` unset — so the divergence is a configuration,
  not a fork (`web/images.py`). **Live since 2026-09-23**, after a 40-hour
  upload at a measured 2.8 MB/s; the site ran on the GWLB's endpoints in the
  meantime, which is why the switch cost no downtime.

- **Viewer without a bundler (D2):** SPECS §4.2 says "vanilla TS/Vite"; the
  viewer ships as plain ES modules + CSS with no build step (types via JSDoc,
  OpenSeadragon vendored), so the repo's CI stays Python-only and `leibniz
  serve` needs no Node toolchain. Same stack otherwise (OpenSeadragon on GWLB
  IIIF, FastAPI serving it).
- **D1 built before C4 (D):** SPECS §5 sequences D1 after C4; nothing in the
  index or viewer depends on v2 — lines are versioned per `run_id` and the
  API/index always show the latest run per line — so D shipped on v1 and C4
  swaps v2 in with a re-index. `lang`/`stratum` filters exist and read
  `unknown` until C4 fills them.
- **Releases not gated on the §7.5 memo / §8 letters (operator decision,
  2026-09-16):** recorded in `reports/release-checklist.md` §0.
- **Schema extension (C1):** added a `page_stats` table (per-page segmentation
  metrics) and a `pages.label` column (folio label) beyond the SPECS §4.3 canonical
  list. `page_stats` is queried by the C2/C4 stratum heuristic; `pages.label` is the
  key for the C2 piece→canvas resolver. Both are additive and migration-safe
  (`SCHEMA_SQL` `CREATE TABLE IF NOT EXISTS` + additive `ALTER TABLE` in `_migrate`).
- **`lines` provenance (C1):** the two-stage pipeline writes geometry with the
  *segmentation* run id, then recognition repoints `run_id`/`model` at the
  *recognition* run (the text's provenance, SPECS §4.5); the segmentation run is
  retained in `page_stats.run_id` and `lines.source`. The C4 append-per-run /
  version-rows decision (db.py docstring) is still deferred.
- **C1/C2 live runs deferred to an operator env.** This build environment has no
  kraken/torch stack, no GPU, and no image cache (bulk `data/` is gitignored and
  ephemeral), so the corpus segment/recognize was **not** run here. The 2026-09-11
  session *did* run the C2 data inputs here at full scale (OAI harvest, §70
  katalog sweep, crosswalk, volume ingestion + extraction) — all reproducible
  with the CLI, cache-first; only the mint needs the operator's corpus store.
- **Optional dependency `gt` (C2):** `pdfplumber` for PDF text layers
  (`uv sync --extra gt`); imported lazily, tests run without it.
- **`data/editions/` (C2):** raw §70 volume text layers + extracted piece JSON;
  gitignored like the rest of `data/`.
