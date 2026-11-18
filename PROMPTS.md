# Leibniz Legible — Build Prompts

_Companion to `SPECS.md`. v0.1, 2026-07-28._

## How to use this file

Each phase below is a **standalone prompt for a fresh Claude coding session**. The sessions share no memory; the repository is the memory. The protocol:

1. Start a fresh session in the repo. Paste the **COMMON CONTEXT** block, then the one phase prompt you're running.
2. The session must begin by reading `SPECS.md` and `STATUS.md`, and end by updating `STATUS.md` and committing. If reality in the repo contradicts a prompt (files missing, schema drifted), trust the repo + `STATUS.md`, note the divergence in `STATUS.md`, and adapt.
3. Run one phase per session. Phases marked as **gates** end with a go/no-go recommendation written into `STATUS.md` — read it before launching the next phase.
4. Dependencies are listed per phase; A1→A2→A3 and B1→B2 can interleave, C phases are sequential, D phases follow C4.

The prompts that have been run are in `PROMPTS-archive.md`, moved there verbatim (ARCH1, 2026-11-17), and the `STATUS.md` entries dated before 2026-10-19 are in `STATUS-archive.md`; a prompt that names an archived prompt or entry means the archived text. Nothing is appended to the two archive files: a new prompt goes under "Follow-up phases (2026-10)" below and a new entry into `STATUS.md`, as before.

---

## COMMON CONTEXT (paste at the top of every session)

```
You are building "Leibniz Legible": every page of the digitized Leibniz Nachlass
(~200,000 page images at the Gottfried Wilhelm Leibniz Bibliothek, Hannover)
machine-transcribed with per-line confidence and provenance, typo-tolerantly
searchable, and browsable in an open IIIF viewer linked to the scholarly
catalogue. Access layer, not an edition: output is Vorausedition-grade machine
text with honest labels, subordinate to the Akademie-Ausgabe.

FIRST: read SPECS.md (the law) and STATUS.md (current state) in full. If this
prompt conflicts with the repo, the repo + STATUS.md win; record the divergence.

Conventions (from SPECS §4, enforce throughout):
- Python 3.12, `uv` for env/deps, `ruff` lint, `pytest` tests, `typer` CLI
  exposed as `leibniz` (one CLI, subcommands per stage).
- Package layout: src/leibniz/{harvest,catalog,layout,htr,align,enrich,search,
  release,legal,web}/ ; tests in tests/ mirroring; generated reports in
  reports/ (committed); bulk data under data/ (gitignored).
- Canonical store: SQLite at data/inventory.sqlite via a thin typed layer
  (sqlite3 or sqlite-utils; no ORM). Schema per SPECS §4.3. Release exports
  are Parquet.
- IDs: page = "{gwlb_object_id}:{canvas_seq:04d}", line = page + ":{line_seq:03d}".
- Provenance is non-negotiable (SPECS §4.5): every stored line carries model,
  version, run_id, confidence, status ∈ {machine, aligned, corrected, verified}.
  Never store or export text without these fields.
- License buckets (SPECS §7): 'open' vs 'nc'. NC-derived text never enters
  CC BY exports or the public UI. Only §70-expired AA reading text (list in
  src/leibniz/legal.py, from SPECS §1.4) may be redistributed; never editor
  introductions/apparatus/commentary.
- Crawling etiquette: custom User-Agent with contact email, ≤1 req/s per host,
  exponential backoff, resumable, cache-first (never re-fetch cached items).
- Secrets via .env (ANTHROPIC_API_KEY optional); never committed. Everything
  must run without the key (LLM steps skip gracefully).
- Keep functions small and typed; every non-trivial module gets tests that run
  offline (fixtures under tests/fixtures/, no network in tests).

FINISH by: running ruff + pytest clean; updating STATUS.md (what changed, key
numbers, open questions, recommended next phase / gate verdict); committing
with a descriptive message.
```

---

_The prompts of Phases A0, A1, A2, A3, B1, B2, C1 and C2, which have run → `PROMPTS-archive.md`, "Original phase prompts (archived)"._

---

## Phase C3 — Fine-tune v2 + per-stratum eval **(gate)**

_Depends on: C2._

> Train `leibniz-htr-v2`. Training set: PHILIUMM GT (CC BY) + C2 open-bucket GT (+ NC-bucket as train-only if it measurably helps — document; NC data may train a CC BY-released model per the TDM analysis in SPECS §7, but note the question in the model card for the lawyer memo). Consider pooling external multilingual GT (Bullinger 165k lines ~80% Latin — github.com/pstroe/bullinger-htr; German Kurrent sets from HTR-United/CATMuS for the de stratum) — the Bullinger lesson says multilingual pooling helps; ablate if time allows.
>
> Use Kraken's training (ketos) fine-tuning from the PHILIUMM checkpoint; hold out a test set that is (a) disjoint from all training GT at the *page* level, (b) stratified by stratum and language. Evaluate with the B1 harness: overall + per-stratum + per-language CER/WER, compared against PHILIUMM baseline on the identical set.
>
> Deliverables: model artifact + `reports/htr-v2-eval.md` + a model card draft (data statement incl. licenses, metrics per stratum/language, intended use, the "machine output, not an edition" framing).
>
> **Gate**: CER ≤7% on la/fr ⇒ target met. Either way, ship the best model and record honest numbers; if v2 beats v1 nowhere, investigate before C4 re-runs the corpus.

> **Amendment (2026-09-16, strategy review — read before running C3).** The published analogue runs against the optimistic case: Bullinger went from ~110k to ~377k alignment-minted lines and CER did not move (9.13% → 9.1–9.2%), because the label floor, not model capacity, binds — their refined GT itself measures 6.5% CER. Our minted labels are Akademie-Ausgabe *reading text* (abbreviations silently expanded, u/v and i/j normalized, struck passages omitted) scored against a *diplomatic* validation set, so every expansion is a systematic insertion error that does not average out with scale; and the mint keeps only lines v1 already read at ≥0.55–0.80 folded similarity, so the GT is biased toward what v1 already gets right. Expect about one point (7.95% → ~7%), not two or three. Four changes that move the odds, all cheap:
> 1. **Re-extract the minted pieces' pages with a vision model before training** (`leibniz align extract`; priced in `reports/gt-factory.md` at two to low three figures). Removes OCR-layer noise (Tesseract/ABBYY, 81.6% cross-source agreement) and editorial brackets (`droit[e]` leaked into a minted line). Does not remove normalization.
> 2. **Stage the training**: minted (aligned) lines first, PHILIUMM's hand-corrected lines *last* and upweighted (their own stage1_noisy / stage2_clean configs already have this shape). Select checkpoints on a diplomatic set that is page-disjoint from training; verify the val files are disjoint from `train_clean`'s files (val was drawn from the clean subset). The NC-licensed Transkriptionspool is usable as an evaluation-only second set under the TDM rules (§7.3) — different source, different conventions, never redistributed.
> 3. **Filter minted lines by v1 CTC confidence as well as alignment similarity** (Peer et al. 2025's γ-filter; optimum 30–60%), and **report error composition**: deletions/insertions clustered at abbreviation sites are the normalization tax, and one CER number hides it. Ablate: PHILIUMM GT alone · + minted · + minted filtered · + minted re-extracted.
> 4. **Add character n-gram language-model decoding** (Tarride et al. 2024: −12% relative CER across 12 datasets in PyLaia). Kraken does not ship one as far as verified; implement over the CTC logits (torchaudio `ctc_decoder` + KenLM). Train the LM on *diplomatic* GT, never on edition text, or it will push toward expansions. Report with and without.
>
> Two honesty notes for the model card: (a) the ablation is a weaker test of GT precision than STATUS assumed — a flat result is consistent with Bullinger even at good precision, so the hand audit (Q #18) still matters; (b) the PHILIUMM transcription conventions are on an access-controlled wiki, so any published claim of "diplomatic" fidelity must state what was verified. Also measure, once v2 exists, the number nobody has: on the val split, the fraction of v1/v2 *disagreements* where either reading is exactly right, per stratum — it decides whether Calculemus's A/B mechanic has the truth in the pair.
>
> **Amendment 2 (2026-10-07, from the audit — see STATUS.md "C2b").** The PHILIUMM team judged the 200-line sheet (199 verdicts); the patterns behind the non-*correct* verdicts and their reach across the mint are in `reports/gt-audit.md` and `reports/gt-audit/reach.md`. Six consequences for C3:
> 1. **Train on the re-minted lines with hyphens kept** (`align_piece(keep_hyphen=True)`, the default since C2b): the missing line-end hyphen was the most frequent fault of the minted text. The re-mint runs once, before C3, with every C2b flag in place (the factory is idempotent; about two hours on six shards).
> 2. **Exclude lines flagged `math`** (`data/gt/flags.jsonl` from `leibniz align audit-reach`) **and lines from Marginalien works**: formula lines are wrong in the mint and in the HTR alike, and the Marginalien body is print, not Leibniz.
> 3. **Exclude PHILIUMM's 1,010 pages from the held-out set** (`reports/philiumm/heldout_pages.csv`, once P1 has produced it): the model this project runs trained on them.
> 4. **Stratify the held-out set by stratum, language and hand** (`eigh.` in the record's Textart, the `eigh` flag of the reach census).
> 5. **Keep the 199 PHILIUMM-judged lines and their corrections out of training** (`reports/gt-audit/gt-audit-verdicts-philiumm.csv`, `…-corrections.csv`) and use them as a sanity set: a model that gets them wrong where the auditors read them is not better.
> 6. **Report CER by hand** as well as by stratum and language.

---

## Phase C4 — Corpus re-run v2 + enrichment

_Depends on: C1, C3._

> Re-run recognition corpus-wide with v2 (same pipeline, new run_id; keep v1 rows — lines table is append-per-run with a current-run pointer, or version rows; pick and document). Add the enrichment stage `leibniz pipeline enrich`: per-line language ID (a fast classifier — lingua/fasttext class — with a `mixed` label for code-switched lines; Latin/French/German are the classes that matter) and per-page stratum labels (heuristic from segmentation stats + katalog type + GT-audit calibration; label the field `stratum_heuristic` — honesty in naming).
>
> Deliverable: `reports/corpus-v2.md` — coverage (% pages recognized, skip reasons), confidence and language distributions corpus-wide, stratum distribution. This report contains numbers nobody has ever computed (e.g. the actual machine-estimated language split of the Nachlass vs the folklore 40/30/15) — write it accordingly.

---

_The prompts of Phases D1, D2 and D3, which have run → `PROMPTS-archive.md`, "Original phase prompts (archived)"._

---

## Phase E1 (stretch) — Correction micro-UI

_Depends on: D2._

> Smallest useful human-in-the-loop: on the page view, an "improve this line" affordance → auth via a simple invite-token allowlist (no accounts system) → submitted corrections stored as new line versions with `status='corrected'`, corrector identity, and timestamp; original machine rows immutable; a `/corrections` review queue where the operator promotes to `status='verified'`. Export corrections as a supplementary GT dataset. Rate-limited, spam-safe, and entirely optional to the Tier 1 definition of done — do not let this phase grow into a platform.

---

## Follow-up phases (2026-10)

_Phases outside the A0–E1 build order, each run from one prompt in one session. The prompts are appended verbatim, as they were given, except that a correspondent's name is withheld (square brackets mark the place); `STATUS.md` records what each session found and where it departed from its prompt._

The prompts run so far are in `PROMPTS-archive.md` under "Follow-up phases (2026-10) (archived)", each verbatim under its heading:

| Phase | Date run | Its heading in the archive |
| --- | --- | --- |
| W3 | 2026-10-06 | `### Phase W3 — A browse page (run 2026-10-06)` |
| C2b | 2026-10-07 | `### Phase C2b — Close the C2 audit and learn from it (run 2026-10-07)` |
| P1 | 2026-10-08 (Tasks 1 and 2 built; Task 3 waits for the layout model) | `### Phase P1 — PHILIUMM cross-checks (Tasks 1 and 2 built 2026-10-08; Task 3 waits for the layout model)` |
| S1 | 2026-10-08 (built; the install is the operator's) | `### Phase S1 — A staging site on the VPS (built 2026-10-08; the install is the operator's)` |
| W4 | 2026-10-08 | `### Phase W4 — Text access (run 2026-10-08)` |
| K1 | 2026-10-09 | `### Phase K1 — Kurrent track (run 2026-10-09)` |
| K2b | 2026-10-19 | `### Phase K2b — the letter-pool test set (run 2026-10-19)` |
| C2c | 2026-10-20 | `### Phase C2c — the re-mint (run 2026-10-20)` |
| K2 | 2026-10-20 | `### Phase K2 — German ground truth (run 2026-10-20)` |
| W6 | 2026-10-21 | `### Phase W6 — two reader's items from the Leibniz-Edition (run 2026-10-21)` |
| L1 | 2026-10-21 | `### Phase L1 — the licence registry (run 2026-10-21)` |
| G1 | 2026-10-21 | `### Phase G1 — the Calculemus seam (run 2026-10-21)` |
| A3b | 2026-10-21 | `### Phase A3b — the Arbeitskatalog import (run 2026-10-21)` |
| K3 | 2026-10-21 | `### Phase K3 — a Leibniz Kurrent model (run 2026-10-21)` |
| LT1 | 2026-10-28 | `### Phase LT1 — the page-level LLM test (run 2026-10-28)` |
| K4 | 2026-10-26 | `### Phase K4 — German on the site (run 2026-10-26)` |

New prompts are appended below this line, verbatim, as before.

### Phase ARCH1 — the archive (run 2026-11-17)

_Run in a cloud session, alone, on the branch it was given
(`claude/blissful-mccarthy-ktud6m`), under the session preamble of 19 October
as updated on 21 October and 16 November, given with the prompt and printed
first below; the cloud batch note of 17 November, given after the prompt, is
printed last. No go was waited for (the preamble's item 6 and the note); the
departures are in `STATUS.md`, Divergences._

~~~~text
SESSION PREAMBLE, 19 October 2026, as given to K2b, C2c, K2, W6 and K3;
updated 21 October in three places: the branch names in clause 1, the entry
list in clause 3, the disk line in clause 4; and 16 November in one, clause 8,
the archive files. Read it with the phase prompt that
follows; where they differ, this preamble wins. It replaces the preamble on the
plan page of 8 and 14 October.

1. One branch per step, from main. The branch claude/dazzling-hopper-uxji2x of
   the older preamble is merged (pull request #45) and closed: do not use it.
   A desktop session creates the branch the operator names in chat (K2b was
   k2b-letterpool, C2c c2c-remint, K2 k2-german-gt, K3 k3-kurrent-model) with
   `git fetch origin main && git checkout -B <branch> origin/main`.
   A cloud session works on the branch it was given at start and creates no
   other; it begins with `git fetch origin main && git merge origin/main`.
   Commit there; `git push -u origin <branch>`; end by printing the compare URL
   against main. The operator opens and merges the pull request.

2. No merge, no production deploy, nothing sent. Where a prompt says "wait for
   merged", "§9 update", "verify live" or "deploy": push the branch instead
   and, if the website changed, print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh <branch>` and the
   checks as `curl -su USER …` lines with their expected answers. The target,
   the user name and the password are on the operator's plan page, never in
   the repo, STATUS.md or PROMPTS.md. The live site changes only at the
   operator's merge and the operator's §9 update. Emails: you draft, the
   operator sends.

3. Shared memory. Read STATUS.md first: "Current state" (the entries of 21, 20,
   14, 11 and 10 October), the K3, L1, W6, K2, C2c, K2b, W5 and K1 entries,
   Open questions 27 to 29, "Next". Prepend your entry to Current state and the
   Phase log as the prompt says; append the prompt verbatim to PROMPTS.md under
   "Follow-up phases (2026-10)"; record departures from the prompt, this
   preamble included, under "Divergences". Names of individuals stay out of
   STATUS.md and PROMPTS.md: write the role and the date.

4. Where you run. A checkout without data/inventory.sqlite is a cloud session:
   build and test on fixtures; hand every store, GPU and box step to the
   operator as exact commands with the expected output; make your own
   environment, .venv-cloud, with the web, gt and release extras. A checkout
   with the store is the operator's WSL desktop: run those steps yourself under
   the prompt's rules: the store read-only unless the prompt says otherwise, a
   "go" before any job over an hour, any download over a gigabyte and any
   install. The side environments are .venv-w3 (web, gt, release) and .venv-k1
   (bench, gt, kurrent; every GPU step); never run `uv sync` against .venv.
   Disk: Ubuntu's filesystem is a growing file on the host's C: drive, so the
   budget for any large write is `df -h /mnt/c`, never `df /`; model
   checkpoints and anything over a few gigabytes go under /mnt/d/.

5. Numbers. Never write a number you did not produce. The committed reports
   carry the ones produced so far.

6. A go. A desktop session waits wherever the prompt says to wait; the operator
   is at the keyboard. A cloud session started with the whole step as its task
   records the pre-flight and proceeds, noting the departure under Divergences;
   the operator's yes is still needed for anything on the box or the store,
   which a cloud session hands over anyway.

7. Two sessions may be in flight on different branches, one desktop, one cloud.
   If `git merge origin/main` meets a conflict in STATUS.md or PROMPTS.md, keep
   both sides' entries, the newer above, and say so.

8. The archive (16 November). Once ARCH1 is merged, STATUS-archive.md holds
   the Current state and Phase log entries dated before 19 October and
   PROMPTS-archive.md every prompt already run; STATUS.md and PROMPTS.md
   keep one pointer line in each emptied place. A prompt that names an
   archived entry means the archived text: open the archive file for it.
   Append nothing to the archive files; new entries and prompts go to
   STATUS.md and PROMPTS.md as before. Until ARCH1 is merged the files are
   as they were and this clause is void.

Phase ARCH1 — archive the finished phases out of STATUS.md and PROMPTS.md, so
that every later session reads a fraction of the text. One cloud session,
alone: no other session in flight on either side until this is merged,
because the two files it rewrites are the ones every session appends to.
Docs only: no code, no data, no deploy. About an hour.

FIRST: read PROMPTS.md's "How to use this file" and COMMON CONTEXT, and
STATUS.md's section headings (`grep -n '^## \|^### ' STATUS.md`), the first
lines of its Current state entries (`grep -n '^\*\*2026-' STATUS.md`) and the
top of "Next". If this prompt conflicts with the repo, the repo + STATUS.md
win; record the divergence. Write the "ARCH1 — the archive" entry in
STATUS.md at the end.

## Where you run, and the rules that follow from it
A cloud checkout without the store; .venv-cloud (web, gt, release extras) for
ruff and pytest only. The branch this session was given; `git fetch origin
main && git merge origin/main` first. No file under data/, no deploy. Every
line moved is moved verbatim: the archive files are the record, STATUS.md
and PROMPTS.md the working memory. Never write a number you did not produce:
the line counts you report are `wc -l` on the files before and after.

## What the files are, on 16 November
STATUS.md (about 8,100 lines, 611 KB): "Current state" (dated entries,
newest first, from 2026-11-16 back to July, followed by seven retained
subsections headed "Prior gate (retained)" (two), "Phase B1 in numbers",
"What was built (B1)", "Delivery-model correction", "What was built (A2 +
A3)", "A2 in numbers", "A3 in numbers"); "Phase log" (one ### entry per
phase, newest first, from K4 of 2026-10-26 back to A0 of 2026-07-28); "Key
numbers"; "Open questions" (numbered, live); "Divergences" (numbered,
live); "Next" (dated paragraphs, newest first). PROMPTS.md (about 3,900
lines, 260 KB): "How to use this file"; "COMMON CONTEXT (paste at the top of
every session)"; the original phase prompts A0 to E1; "Follow-up phases
(2026-10)" with every prompt as run since W3 appended verbatim (W3, C2b, P1,
S1, W4, K1, K2b, C2c, K2, W6, L1, G1, A3b, K3, LT1, K4). Sessions read
STATUS.md in full and PROMPTS.md's COMMON CONTEXT; the run prompts are a
record nobody rereads, and the operator's plan page carries each with a
Copy button.

## Task 1 — STATUS-archive.md
Create STATUS-archive.md with a two-line head (what it is; that nothing is
appended here) and these sections, each entry moved verbatim with its
heading, in the order it had:
- "Current state (archived)": the Current state entries dated before
  2026-10-19 (the entry of 2026-10-14 back to July) and the seven retained
  subsections.
- "Phase log (archived)": the Phase log entries dated before 2026-10-19 (W5
  of 2026-10-10 back to A0 of 2026-07-28).
- "Next (archived)": the paragraphs of "Next" whose every item is done or
  superseded by a later paragraph, judged from their own wording and the
  Current state; a paragraph with one open item stays, and when in doubt it
  stays.
Leave in STATUS.md, in each emptied place, one pointer line per moved Phase
log entry (its heading text and date, "→ STATUS-archive.md") and one line
each for Current state and Next ("entries before 2026-10-19 →
STATUS-archive.md"). Key numbers, Open questions and Divergences stay whole:
they are numbered or quoted elsewhere. The entries of 2026-10-19 and later
(K2b, C2c, K2, W6, L1, G1, A3b, K3, LT1, K4 and November's) stay, because
the open prompts name them.

## Task 2 — PROMPTS-archive.md
Create PROMPTS-archive.md with the same kind of head and move verbatim: the
original prompts of the phases that have run (A0, A1, A2, A3, B1, B2, C1,
C2, D1, D2, D3) and every prompt under "Follow-up phases (2026-10)". Keep in
PROMPTS.md: "How to use this file", COMMON CONTEXT, the prompts of C3 (with
its amendments, which C3 still needs), C4 and E1, and the "Follow-up phases
(2026-10)" heading followed by a table of the archived run prompts (phase,
date run, its heading in the archive) and one line saying that new prompts
are appended below it as before. Amend "How to use this file" with two
sentences on the archive files.

## Task 3 — Prove nothing was lost
A script in the session (not committed) reads the four files and shows that
every line of the old STATUS.md is in the new STATUS.md or in
STATUS-archive.md, and the same for PROMPTS.md, with only the pointer lines,
the archive heads and the table new; print the counts (old lines, kept,
archived, new) and `wc -l` of the four files. Check that no test or module
reads either file (`grep -rn 'STATUS.md\|PROMPTS.md' tests src` names only
docstrings and messages). ruff + pytest.

## Finish
STATUS.md: the "ARCH1 — the archive" entry at the top of Current state and
in the Phase log with the counts, and one line in Next; append this prompt
verbatim to PROMPTS.md under "Follow-up phases (2026-10)", the first prompt
below the table. Commit in two pieces (the STATUS move, the PROMPTS move),
push, print the compare URL. Do not merge.

CLOUD BATCH, 17 November 2026. Read this with the preamble and the prompt
above; where they differ, this note wins. Complete this step: record Task 0
and proceed without a go; where the prompt says to wait, proceed and note the
departure under Divergences. The operator answers nothing mid-task, so decide
the small things yourself and record them; stop only for something the prompt
did not foresee, and then write the question into the STATUS entry and push.
Other sessions run today on their own branches (K3b-prep, REL1 Part A, R1
Part A, G1b in the cloud; desktop-queue-1 on the desktop), so `git fetch
origin main && git merge origin/main` at the start and again before the final
push; on a conflict in STATUS.md or PROMPTS.md keep both sides' entries, the
newer above, and say so. Commit and push after every task. End with the
compare URL and a ten-line summary. Do not merge.
If this is ARCH1: it runs alone; the operator starts nothing else until it
is merged, so there is no parallel session to merge from.
If this is R1: Part A only here; Part B is a desktop session later, as the
prompt says; end at checkpoint B with the hand-over for Part B.
If this is REL1 Part A: the operator's note of 16 November follows this one
with Task 0's three answers; a bracket left unfilled means "propose and
proceed".
If this is CAL1 on the Calculemus repository: the Leibniz Legible preamble
does not apply; the prompt carries the game's conventions; no other session
runs on that repository today.
~~~~

### Phase REL1 — the first releases (Part A run 2026-11-17/18)

_Part A run in a cloud session on the branch it was given
(`claude/clever-gates-56b0a4`), under the session preamble of 19 October as
updated on 21 October and 16 November, given with the prompt and printed first
below; the operator's note of 16 November and the cloud batch note of 17
November, given after the prompt, are printed last, in the order they were
given. No go was waited for (the preamble's item 6 and the batch note); the
note's three brackets came as printed, the third unfilled. Part B is the
operator's desktop and Part C a later cloud session; the departures are in
`STATUS.md`, Divergences._

~~~~text
SESSION PREAMBLE, 19 October 2026, as given to K2b, C2c, K2, W6 and K3;
updated 21 October in three places: the branch names in clause 1, the entry
list in clause 3, the disk line in clause 4; and 16 November in one, clause 8,
the archive files. Read it with the phase prompt that
follows; where they differ, this preamble wins. It replaces the preamble on the
plan page of 8 and 14 October.

1. One branch per step, from main. The branch claude/dazzling-hopper-uxji2x of
   the older preamble is merged (pull request #45) and closed: do not use it.
   A desktop session creates the branch the operator names in chat (K2b was
   k2b-letterpool, C2c c2c-remint, K2 k2-german-gt, K3 k3-kurrent-model) with
   `git fetch origin main && git checkout -B <branch> origin/main`.
   A cloud session works on the branch it was given at start and creates no
   other; it begins with `git fetch origin main && git merge origin/main`.
   Commit there; `git push -u origin <branch>`; end by printing the compare URL
   against main. The operator opens and merges the pull request.

2. No merge, no production deploy, nothing sent. Where a prompt says "wait for
   merged", "§9 update", "verify live" or "deploy": push the branch instead
   and, if the website changed, print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh <branch>` and the
   checks as `curl -su USER …` lines with their expected answers. The target,
   the user name and the password are on the operator's plan page, never in
   the repo, STATUS.md or PROMPTS.md. The live site changes only at the
   operator's merge and the operator's §9 update. Emails: you draft, the
   operator sends.

3. Shared memory. Read STATUS.md first: "Current state" (the entries of 21, 20,
   14, 11 and 10 October), the K3, L1, W6, K2, C2c, K2b, W5 and K1 entries,
   Open questions 27 to 29, "Next". Prepend your entry to Current state and the
   Phase log as the prompt says; append the prompt verbatim to PROMPTS.md under
   "Follow-up phases (2026-10)"; record departures from the prompt, this
   preamble included, under "Divergences". Names of individuals stay out of
   STATUS.md and PROMPTS.md: write the role and the date.

4. Where you run. A checkout without data/inventory.sqlite is a cloud session:
   build and test on fixtures; hand every store, GPU and box step to the
   operator as exact commands with the expected output; make your own
   environment, .venv-cloud, with the web, gt and release extras. A checkout
   with the store is the operator's WSL desktop: run those steps yourself under
   the prompt's rules: the store read-only unless the prompt says otherwise, a
   "go" before any job over an hour, any download over a gigabyte and any
   install. The side environments are .venv-w3 (web, gt, release) and .venv-k1
   (bench, gt, kurrent; every GPU step); never run `uv sync` against .venv.
   Disk: Ubuntu's filesystem is a growing file on the host's C: drive, so the
   budget for any large write is `df -h /mnt/c`, never `df /`; model
   checkpoints and anything over a few gigabytes go under /mnt/d/.

5. Numbers. Never write a number you did not produce. The committed reports
   carry the ones produced so far.

6. A go. A desktop session waits wherever the prompt says to wait; the operator
   is at the keyboard. A cloud session started with the whole step as its task
   records the pre-flight and proceeds, noting the departure under Divergences;
   the operator's yes is still needed for anything on the box or the store,
   which a cloud session hands over anyway.

7. Two sessions may be in flight on different branches, one desktop, one cloud.
   If `git merge origin/main` meets a conflict in STATUS.md or PROMPTS.md, keep
   both sides' entries, the newer above, and say so.

8. The archive (16 November). Once ARCH1 is merged, STATUS-archive.md holds
   the Current state and Phase log entries dated before 19 October and
   PROMPTS-archive.md every prompt already run; STATUS.md and PROMPTS.md
   keep one pointer line in each emptied place. A prompt that names an
   archived entry means the archived text: open the archive file for it.
   Append nothing to the archive files; new entries and prompts go to
   STATUS.md and PROMPTS.md as before. Until ARCH1 is merged the files are
   as they were and this clause is void.

Phase REL1 — the first releases: the transcriptions with the inventory
inside them (D2 with D1), the ground truth in two deposits (D3), the German
reader (D4). Three parts. Part A in a cloud session on the branch it was
given: the cards, the metadata, the model package, the deposit scripts, a
dry run on the fixture store. Part B on the operator's desktop: the exports
from the master store, the DOI reservations, the uploads. Part C a short
cloud session on the same branch: the DOIs into the registry, the README,
STATUS and About, pushed for the operator's merge and §9 update. No store
write; nothing deployed by the session.

FIRST: read PROMPTS.md (COMMON CONTEXT), SPECS.md (§2 the deliverables
table, §7 licences), STATUS.md (the L1, K3, K4 and LT1 entries; "Next"),
reports/release-checklist.md in full (§0 to §6: it is the specification of
this phase), src/leibniz/release/ (export.py, cards.py, cli.py),
src/leibniz/legal.py (the registry: licences, outputs, deposit_for,
arbeitskatalog_credit), src/leibniz/web/attribution.py (the DOIs the site
already cites), reports/kurrent/k3-model-card-trocr.md and
reports/htr/page-llm.md (the LT1 numbers). If this prompt conflicts with the
repo, the repo + STATUS.md win; record the divergence. Write the "REL1 — the
first releases" entry in STATUS.md after every task; if one exists, continue
from its first unfinished task.

## Where you run, and the rules that follow from it
Part A: the cloud checkout, .venv-cloud with the web + gt + release extras
(pyarrow comes with release), the fixture store; no token of any kind. Part
B: /home/evana/LeibnizLegible-g1 on main with .venv-g1
(UV_PROJECT_ENVIRONMENT=.venv-g1), the master store read-only
(/home/evana/LeibnizLegible/data/inventory.sqlite), the exports to
/mnt/d/leibniz-release/, the tokens ZENODO_TOKEN and HF_TOKEN as environment
variables the operator sets in the window; every job states its expected
host memory and stays under 6 GB, one process at a time. Nothing non-
commercial leaves the machine except in the NC deposit under its own
licence; the letter pool's texts never (they are evaluation only). Never
write a number you did not produce; the counts in every card come from the
export's MANIFEST.

## Background
The store carries two recognition runs per the K4 rule: the PHILIUMM model
(FoNDUE-GD_v2_ft_Leibniz) on every page and k3-trocr@runs-615-epoch-5 as a
scoped run on 24,078 German pages; the lines shown are 12,947,584
(11,407,896 + 1,539,688). The ground truth is 333,680 aligned lines in two
deposits by channel (legal.deposit_for). The registry (L1) decides every
licence line; the K3 card and the LT1 report carry the German reader's
numbers: 28.6 % CER on the letter pool (36.7 % in Leibniz's own hand), 11.84
% on the validation set, parity with the frontier page models on the
letters. Zenodo already holds four reports of this project (the checklist
names their DOIs); the datasets go into the leibniz community, one record
each, DOI reserved before the card is final. Hugging Face mirrors D2, D3's
open deposit and the model.

## Part A, cloud

### Task 0 — Pre-flight (report, then wait for a go)
A clean tree on the branch; ruff + pytest baseline; `leibniz release export
--format parquet` and `--format jsonl` on the fixture store into a temp dir,
and `leibniz release checklist`; read what the cards say today. Confirm or
report: that iter_transcriptions applies K4's precedence rule (a fixture
page with a scoped run exports the scoped row, with model and run per
line); that the gt deposits split by channel as L1 decided; what the
inventory tables hold now (the Arbeitskatalog records with their credit).
Three questions for the operator: the model's public name (proposal
leibniz-kurrent-trocr), D1 inside the transcriptions record (yes unless
they say otherwise), the Hugging Face namespace. Print the plan; wait for
"go".

### Task 1 — The cards, true to the store (code and tests)
The transcriptions card names both models per line (`model`, `run`), the
German reader with its licence stamps from the registry (model, base,
readings), the K3 and LT1 numbers with what they were measured on, the
language pass and its coverage (about three quarters of the German pages by
the census's measure; the rest the first model's text), the Marginalien
excepted; the inventory tables inside the same record with their own
licence lines (CC0 for the project's tables, CC BY 4.0 with the
arbeitskatalog_credit line for the catalogue records). Both ground-truth
cards state the audit honestly as the checklist §1 asks (the precision
measured in C2b, the K2 sheet with its judge). Every card gets the Hugging
Face front matter (license, language, size_categories, task_categories, the
pretty name) above the Markdown, so one file is the Zenodo description's
source and the HF README. The anti-contamination note of the checklist in
each description. Tests on the fixture export. CHECKPOINT A.

### Task 2 — The model package (code and tests)
`leibniz release model --weights DIR --card FILE --name NAME --out DIR`:
copies the TrOCR checkpoint's files (config, generation config, weights,
processor and tokenizer files) into a release folder with a README (the K3
card brought to the finish: the LT1 table beside the K3 numbers, the K4 run
it reads on the site, the licence as the registry decides, the usage with
transformers and the decoder's cache, the statement that the training
lines' precision is unmeasured until the audit), a LICENSE file, a
MANIFEST.json with sizes and SHA-256, and a zip for Zenodo. Tested on a
tiny stand-in directory.

### Task 3 — Zenodo and Hugging Face, scripted (code and tests)
`tools/release/zenodo_deposit.py`: from a record's folder and its metadata
JSON (title, description from the card, creators, licence, version = the
export's date, keywords and related_identifiers exactly as the checklist §2
lists them per record, the community), create a draft deposition, reserve
its DOI and print it, upload the files with a resumable loop and a size
check, and stop: the operator publishes in the browser after reading the
draft. `tools/release/hf_upload.py`: the folder to a dataset or model repo
under the namespace, README first, Parquet as is, private until the
operator flips it. Both read their token from the environment only, never
from a file; both have a --dry-run that prints the request without
sending; tests against a recorded response, no network in pytest.

### Task 4 — The runbook and the hand-over
In the STATUS entry under Next, Part B in order, each command with its
expected time and answer: the export of all four datasets from the master
(`leibniz release export --db … --out /mnt/d/leibniz-release/YYYY-MM-DD
--format parquet`, the MANIFEST checks of the checklist §1 against
`/api/stats`' live figures), the model package from
/home/evana/LeibnizLegible/data/models/k3/trocr/best, the DOI reservation
per record (the script's first step), the cards re-rendered with the DOIs
(`leibniz release export --cards-only --doi …` or the mechanism you build),
the uploads, the browser steps on Zenodo and Hugging Face, and the line
that tells Part C the DOIs. Append this prompt verbatim to PROMPTS.md under
"Follow-up phases (2026-10)". ruff + pytest clean. Push, print the compare
URL. Do not merge.

## Part B — the operator's desktop
The runbook, in order. The exports read the store for about an hour; the
uploads are gigabytes. The operator publishes each Zenodo record after
reading its draft, and sets the Hugging Face repos public when the DOIs
are on the site.

## Part C — cloud, after the operator pastes the DOIs
The DOIs into the registry (attribution.py: one constant per record, read by
About's Licensing section, llms.txt and the README's Status section), the
About rows that cite them (EN and DE), STATUS.md's Current state and Key
numbers, the checklist's §5 ticked; tests; push, compare URL; the §9 update
the operator's. Then the announcement to the §8 contacts is the operator's
mail, with the links.

OPERATOR'S NOTE, 16 November 2026, for REL1 Part A (where it differs from the
REL1 prompt and the preamble, this note wins):
- Task 0's three answers, so you need not stop: the model's public name is
  [leibniz-kurrent-trocr]; D1 rides inside the transcriptions record [yes];
  the Hugging Face namespace is [NAMESPACE]. (The operator fills the three
  brackets before pasting; a bracket left as it is means "propose and
  proceed".)
- The open ground-truth deposit gains a verified subset: the lines of K2's
  audit sheet confirmed or corrected by the Leibniz-Edition's Arbeitsstelle
  (returned 2026-11-06; CC BY 4.0, settled 2026-11-16; the credit wording to
  confirm, until then "the Leibniz-Edition's Arbeitsstelle, Potsdam"). They
  reach the store through K3b-prep's audit-apply (source "; verified
  leibniz-edition 2026-11-06"; channel edition-k2-audit for the corrected
  lines, so legal.deposit_for sends them to the open deposit). If main
  carries that code and legal.py's edition-k2-audit entry, the open card
  counts the verified lines from the export's MANIFEST and credits them from
  the registry; if not, the card says the subset follows in the next
  version. Both ground-truth cards state the K2 audit: 200 lines judged by
  the Edition, the counts as STATUS.md's entry of 2026-11-16 gives them, the
  precision figures only if reports/kurrent/k2-audit.md is on main (K3b's
  Task 0), else "scored in K3b".
- The transcriptions card's German paragraph: k3-trocr, 28.6 % CER on the
  letter pool, 36.7 % in Leibniz's own hand, 11.84 % on the validation set,
  the LT1 table beside it; the language pass's coverage as the K4 entry
  states it (about three quarters of the German pages by the census's
  measure).
- Nothing is sent or published by the session: the deposit scripts stop at
  the draft and the reserved DOI; Part B is the operator's, from the second
  checkout.

CLOUD BATCH, 17 November 2026. Read this with the preamble and the prompt
above; where they differ, this note wins. Complete this step: record Task 0
and proceed without a go; where the prompt says to wait, proceed and note the
departure under Divergences. The operator answers nothing mid-task, so decide
the small things yourself and record them; stop only for something the prompt
did not foresee, and then write the question into the STATUS entry and push.
Other sessions run today on their own branches (K3b-prep, REL1 Part A, R1
Part A, G1b in the cloud; desktop-queue-1 on the desktop), so `git fetch
origin main && git merge origin/main` at the start and again before the final
push; on a conflict in STATUS.md or PROMPTS.md keep both sides' entries, the
newer above, and say so. Commit and push after every task. End with the
compare URL and a ten-line summary. Do not merge.
If this is ARCH1: it runs alone; the operator starts nothing else until it
is merged, so there is no parallel session to merge from.
If this is R1: Part A only here; Part B is a desktop session later, as the
prompt says; end at checkpoint B with the hand-over for Part B.
If this is REL1 Part A: the operator's note of 16 November follows this one
with Task 0's three answers; a bracket left unfilled means "propose and
proceed".
If this is CAL1 on the Calculemus repository: the Leibniz Legible preamble
does not apply; the prompt carries the game's conventions; no other session
runs on that repository today.
~~~~

### Phase K3b-prep — the verdict tools (run 2026-11-17)

_Run in a cloud session on the branch it was given
(`claude/confident-brown-2xwlqs`), beside the desktop, under the session preamble of 19 October
as updated on 21 October and 16 November, given with the prompt and printed
first below; the cloud batch note of 17 November, given after the prompt, is
printed after it, and the operator's message sent while the session ran is
printed last. No go was waited for (the preamble's clause 6 and the note);
the departures are in `STATUS.md`, Divergences._

~~~~text
SESSION PREAMBLE, 19 October 2026, as given to K2b, C2c, K2, W6 and K3;
updated 21 October in three places: the branch names in clause 1, the entry
list in clause 3, the disk line in clause 4; and 16 November in one, clause 8,
the archive files. Read it with the phase prompt that
follows; where they differ, this preamble wins. It replaces the preamble on the
plan page of 8 and 14 October.

1. One branch per step, from main. The branch claude/dazzling-hopper-uxji2x of
   the older preamble is merged (pull request #45) and closed: do not use it.
   A desktop session creates the branch the operator names in chat (K2b was
   k2b-letterpool, C2c c2c-remint, K2 k2-german-gt, K3 k3-kurrent-model) with
   `git fetch origin main && git checkout -B <branch> origin/main`.
   A cloud session works on the branch it was given at start and creates no
   other; it begins with `git fetch origin main && git merge origin/main`.
   Commit there; `git push -u origin <branch>`; end by printing the compare URL
   against main. The operator opens and merges the pull request.

2. No merge, no production deploy, nothing sent. Where a prompt says "wait for
   merged", "§9 update", "verify live" or "deploy": push the branch instead
   and, if the website changed, print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh <branch>` and the
   checks as `curl -su USER …` lines with their expected answers. The target,
   the user name and the password are on the operator's plan page, never in
   the repo, STATUS.md or PROMPTS.md. The live site changes only at the
   operator's merge and the operator's §9 update. Emails: you draft, the
   operator sends.

3. Shared memory. Read STATUS.md first: "Current state" (the entries of 21, 20,
   14, 11 and 10 October), the K3, L1, W6, K2, C2c, K2b, W5 and K1 entries,
   Open questions 27 to 29, "Next". Prepend your entry to Current state and the
   Phase log as the prompt says; append the prompt verbatim to PROMPTS.md under
   "Follow-up phases (2026-10)"; record departures from the prompt, this
   preamble included, under "Divergences". Names of individuals stay out of
   STATUS.md and PROMPTS.md: write the role and the date.

4. Where you run. A checkout without data/inventory.sqlite is a cloud session:
   build and test on fixtures; hand every store, GPU and box step to the
   operator as exact commands with the expected output; make your own
   environment, .venv-cloud, with the web, gt and release extras. A checkout
   with the store is the operator's WSL desktop: run those steps yourself under
   the prompt's rules: the store read-only unless the prompt says otherwise, a
   "go" before any job over an hour, any download over a gigabyte and any
   install. The side environments are .venv-w3 (web, gt, release) and .venv-k1
   (bench, gt, kurrent; every GPU step); never run `uv sync` against .venv.
   Disk: Ubuntu's filesystem is a growing file on the host's C: drive, so the
   budget for any large write is `df -h /mnt/c`, never `df /`; model
   checkpoints and anything over a few gigabytes go under /mnt/d/.

5. Numbers. Never write a number you did not produce. The committed reports
   carry the ones produced so far.

6. A go. A desktop session waits wherever the prompt says to wait; the operator
   is at the keyboard. A cloud session started with the whole step as its task
   records the pre-flight and proceeds, noting the departure under Divergences;
   the operator's yes is still needed for anything on the box or the store,
   which a cloud session hands over anyway.

7. Two sessions may be in flight on different branches, one desktop, one cloud.
   If `git merge origin/main` meets a conflict in STATUS.md or PROMPTS.md, keep
   both sides' entries, the newer above, and say so.

8. The archive (16 November). Once ARCH1 is merged, STATUS-archive.md holds
   the Current state and Phase log entries dated before 19 October and
   PROMPTS-archive.md every prompt already run; STATUS.md and PROMPTS.md
   keep one pointer line in each emptied place. A prompt that names an
   archived entry means the archived text: open the archive file for it.
   Append nothing to the archive files; new entries and prompts go to
   STATUS.md and PROMPTS.md as before. Until ARCH1 is merged the files are
   as they were and this clause is void.

Phase K3b-prep — the tools K3b's desktop session runs: the Edition's verdicts
converted and scored under the fold, the verified lines written into the
store (a dry run here, the write on the desktop), the audit sheet with a
hand filter and context lines, three registry entries. One cloud session on
the branch it was given, beside the desktop; fixtures only; no store, no
GPU, no deploy. Two to three hours.

FIRST: read PROMPTS.md (COMMON CONTEXT), STATUS.md ("Current state": the
entries of 2026-11-16; Open question 33; the K2 entry's audit-sheet
paragraph; "Next"), src/leibniz/align/audit.py (read_verdicts,
score_verdicts, score_by_group, write_sheet, crop_box, crop_line),
src/leibniz/align/audit_patterns.py (classify_rows, Correction,
corrections_table, write_corrections_csv), src/leibniz/align/kurrent_mint.py
(build_audit_sheet, AUDIT_GROUPS), src/leibniz/align/pairs.py (the source
string: READER_MARK, _RECORD_RE, _CHANNEL_RE, channels_from_source,
insert_gt_pairs), src/leibniz/release/export.py (iter_gt, iter_gt_nc,
gt_deposit), src/leibniz/legal.py (Artifact, Terms, deposit_for, the
edition-potsdam entry as the model of a channel entry) and, in
src/leibniz/align/cli.py, audit-score and the k2 command's --audit path. If
this prompt conflicts with the repo, the repo + STATUS.md win; record the
divergence. Write the "K3b-prep — the verdict tools" entry in STATUS.md
after every task.

## What arrived, and what was settled
The Leibniz-Edition's Arbeitsstelle judged K2's 200-line sheet
(data/kurrent/k2-audit.html; its lines CSV data/kurrent/k2-audit-lines.csv,
columns ref, stratum, align_conf, folio, gt_text, htr_text, image, group,
where group is leibniz_hand or other_hands) and returned it on 2026-11-06 as
a table with the sheet's columns and one of its own. The operator exported
it to data/kurrent/k2-audit-verdicts-edition.csv with the header
`ref,stratum,verdict,transcription,note` (200 rows). Their convention:
"correct" only where the minted text is completely right; where anything
was wrong, no verdict and the correct text of the whole line in
`transcription`; "boundary" for a slip at an edge (20 of the 21 with a
transcription too); "wrong" once (crop and text do not match); "unreadable"
three times; one row blank; "note" holds comments only. Counts: 76 correct,
21 boundary, 98 transcription without a verdict, 1 wrong, 3 unreadable, 1
blank; 118 transcriptions in all. Settled on 2026-11-16 (STATUS.md, Open
question 33 b): the corrected lines may go into the open ground-truth
release under CC BY 4.0; the credit wording is to be confirmed (until then
"the Leibniz-Edition's Arbeitsstelle, Potsdam", with the date 2026-11-06).
You have none of their text: every test runs on a synthetic set of the same
shape. Names of individuals stay out of the repo.

## Task 1 — `leibniz align audit-convert` (code and tests)
`audit-convert IN.csv --lines LINES.csv --out OUT.csv --corrections CORR.csv`:
IN has the Edition's shape; OUT the C2 shape `ref, stratum, verdict, note`
that read_verdicts and score_verdicts take: a verdict given stays; a row
with a transcription and no verdict becomes "wrong", its note kept and a
fixed phrase appended ("converted: a transcription without a verdict counts
as wrong; the Edition's text is in the corrections file"); a row with
neither stays unjudged. CORR has `ref, stratum, group, gt_text,
transcription, folded_similarity, note` for every row with a transcription,
gt_text from LINES by ref, the folded similarity by the aligner's fold
(align/dp.py as audit.py uses it). Print the tally by class and by group.
Tests on synthetic rows covering the convention's four cases.

## Task 2 — Precision under the fold, by group (audit-score)
`audit-score` gains `--corrections CORR.csv`: when given, the pattern code
takes each row's correction from the file instead of parsing the note (a
Correction built from the column; classify_rows accepts a mapping ref →
corrected text), and the report gains a section "Under the fold": per
stratum and per group, judged lines; correct as written; boundary;
corrected with a folded similarity at or above the factory's acceptance
threshold for the row's stratum (STRATUM_THRESHOLDS in align/factory.py),
which count as right under the fold; corrected below it; wrong; unreadable;
and three precisions with Wilson intervals: strict, usable (boundary
counted) and under the fold. The summary JSON carries the three figures per
group. The defaults of audit-score point at the C2 audit (reports/gt-audit.md,
reports/gt-audit/audit-summary.json, the overrides beside the verdicts): the
K2 sheet is scored with explicit --out, --summary and --overrides under
reports/kurrent/, and a test shows the C2 files untouched by such a run.
Tests on synthetic rows.

## Task 3 — `leibniz align audit-apply`: the verified lines into the store (code, tests, dry run)
`audit-apply --verdicts OUT.csv --lines LINES.csv --corrections CORR.csv
[--write]`, a dry run by default. For every judged line of the sheet whose
verdict is correct, boundary or a correction, a verified row: the correct
lines keep their text; the corrected lines get the Edition's text; the
source string gains, before "katalog", "; verified leibniz-edition
2026-11-06" and, for a corrected line, "; channel edition-k2-audit" in place
of the channel it had (the Edition's transcription is their text under CC
BY 4.0, so the open deposit takes it whatever copy the minted text came
through; a confirmed line keeps its channel and its deposit), keeping
READER_MARK and `katalog <id>` last so every existing parser still reads
the row; a boundary line counts as verified only where a transcription was
given, with that text. The dry run prints what would change (rows by class;
text replacements; channel changes; the deposit each row would go to by
legal.deposit_for) and writes reports/kurrent/k3b-verified.csv (ref, group,
stratum, verdict, text, verified_by, licence: the minted text where
unchanged, the Edition's where corrected). With --write: one transaction
through project code with a runs row (stage gt_audit, model
"leibniz-edition-k2-audit"), idempotent (a second run changes nothing and
says so), gt-report's counts unchanged afterwards. Tests on the fixture
store with synthetic rows: the dry run, the write, idempotence, and that
export.iter_gt puts a corrected row in the open deposit and a confirmed
Potsdam-channel row in the NC deposit as before. The desktop runs the write
in K3b's Task 0 after a backup and the operator's go.

## Task 4 — `leibniz align audit-sheet-k2`: a hand filter and context lines
A command of its own that wraps build_audit_sheet (the k2 command's --audit
path and its tests stay as they are), taking the readings as that path takes
them, plus: --n and --seed; --hand own|other|both (default both as today;
own draws every line from the records in Leibniz's own hand under the strict
rule); --exclude-refs CSV... (a lines CSV: none of its refs again);
--exclude-records CSV (reports/kurrent/k3-val-pieces.csv, column record_id);
--exclude-pages CSV... (reports/kurrent/letterpool-testset.csv, column
page_ids; reports/philiumm/heldout_pages.csv, column page_id); --context N
(N lines above and below the sampled line on the same page, by line_seq,
rendered as greyed strips with the same CROP_PAD; the verdict applies to the
middle line and the help text says so); --out DIR and --name NAME so a
second sheet never overwrites k2-audit.html; --refs CSV (an explicit list of
refs, for the three-line page of the two unreadable lines and the French
line, record 59196, with context). The help text, bilingual as today, says a
corrected transcription is welcome in the note or, as the Edition did, as
the whole line's text in a column of its own. Tests on the fixture store.

## Task 5 — The registry
Three entries in src/leibniz/legal.py, with tests as the others have:
edition-k2-audit (kind text; the Arbeitsstelle's verdicts and corrected
transcriptions of K2's sheet, returned 2026-11-06; obtained Terms "CC BY
4.0", seen 2026-11-16, "the Edition's answer, recorded by the operator;
STATUS.md Open question 33"; bucket open; channel edition-k2-audit; deposit
open; built: the verified lines of K3b and the audit figures on the K3
cards; notes: the credit wording to confirm); philiumm-seg-v2 (model,
DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2, CC BY-NC
4.0 as published on the card, its outputs unrestricted by the agreement of
2026-10-15; built: P1 Task 3's census) and philiumm-layout-dataset-v2
(dataset, DenisaBumba/layout-leibniz-dataset-v2, CC BY 4.0, public since
2026-11-12, 392 unique pages; built: the census sample drawn outside its
pages), unless P1 Task 3's branch has added the last two first (check main
and the open branches; if so, leave them). `leibniz legal licences` prints
them.

## Finish
STATUS.md: the entry; Open question 33 restated (a and b answered by the
tools, c by Task 4's page); "Next": K3b's Task 0 runs audit-convert,
audit-score with the corrections, audit-apply (the dry run, then --write
after the backup and a go), and its Task 2 draws the sheet with
audit-sheet-k2 --hand own --n 300 --context 1 and the three exclusions.
Append this prompt verbatim to PROMPTS.md under "Follow-up phases
(2026-10)". ruff + pytest clean. Push, print the compare URL. Do not merge.

CLOUD BATCH, 17 November 2026. Read this with the preamble and the prompt
above; where they differ, this note wins. Complete this step: record Task 0
and proceed without a go; where the prompt says to wait, proceed and note the
departure under Divergences. The operator answers nothing mid-task, so decide
the small things yourself and record them; stop only for something the prompt
did not foresee, and then write the question into the STATUS entry and push.
Other sessions run today on their own branches (K3b-prep, REL1 Part A, R1
Part A, G1b in the cloud; desktop-queue-1 on the desktop), so `git fetch
origin main && git merge origin/main` at the start and again before the final
push; on a conflict in STATUS.md or PROMPTS.md keep both sides' entries, the
newer above, and say so. Commit and push after every task. End with the
compare URL and a ten-line summary. Do not merge.
If this is ARCH1: it runs alone; the operator starts nothing else until it
is merged, so there is no parallel session to merge from.
If this is R1: Part A only here; Part B is a desktop session later, as the
prompt says; end at checkpoint B with the hand-over for Part B.
If this is REL1 Part A: the operator's note of 16 November follows this one
with Task 0's three answers; a bracket left unfilled means "propose and
proceed".
If this is CAL1 on the Calculemus repository: the Leibniz Legible preamble
does not apply; the prompt carries the game's conventions; no other session
runs on that repository today.
~~~~

_The operator's message during the session, verbatim:_

~~~~text
Also, found by ARCH1: make bare `pytest` collect the K4 test files it skips on the tests.conftest import (`python -m pytest` runs them); point src/leibniz/web/static/README.md line 155 at the archived "Delivery-model correction" in STATUS-archive.md. The W5 prompt is in neither prompts file because W5 had none; leave that.
~~~~

### Phase R1 — decoding and confidence (Part A run 2026-11-17; Part B is the desktop's)

_Part A run in a cloud session on the branch it was given
(`claude/modest-cori-wds26r`), under the session preamble of 19 October as
updated on 21 October and 16 November, given with the prompt and printed
first below; the cloud batch note of 17 November, given after the prompt, is
printed last. No go was waited for (the preamble's item 6 and the note); the
departures are in `STATUS.md`, Divergences. Part B (Tasks 3 and 4, the
Finish) runs from the same prompt on the operator's desktop._

~~~~text
SESSION PREAMBLE, 19 October 2026, as given to K2b, C2c, K2, W6 and K3;
updated 21 October in three places: the branch names in clause 1, the entry
list in clause 3, the disk line in clause 4; and 16 November in one, clause 8,
the archive files. Read it with the phase prompt that
follows; where they differ, this preamble wins. It replaces the preamble on the
plan page of 8 and 14 October.

1. One branch per step, from main. The branch claude/dazzling-hopper-uxji2x of
   the older preamble is merged (pull request #45) and closed: do not use it.
   A desktop session creates the branch the operator names in chat (K2b was
   k2b-letterpool, C2c c2c-remint, K2 k2-german-gt, K3 k3-kurrent-model) with
   `git fetch origin main && git checkout -B <branch> origin/main`.
   A cloud session works on the branch it was given at start and creates no
   other; it begins with `git fetch origin main && git merge origin/main`.
   Commit there; `git push -u origin <branch>`; end by printing the compare URL
   against main. The operator opens and merges the pull request.

2. No merge, no production deploy, nothing sent. Where a prompt says "wait for
   merged", "§9 update", "verify live" or "deploy": push the branch instead
   and, if the website changed, print for the operator the staging line
   `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh <branch>` and the
   checks as `curl -su USER …` lines with their expected answers. The target,
   the user name and the password are on the operator's plan page, never in
   the repo, STATUS.md or PROMPTS.md. The live site changes only at the
   operator's merge and the operator's §9 update. Emails: you draft, the
   operator sends.

3. Shared memory. Read STATUS.md first: "Current state" (the entries of 21, 20,
   14, 11 and 10 October), the K3, L1, W6, K2, C2c, K2b, W5 and K1 entries,
   Open questions 27 to 29, "Next". Prepend your entry to Current state and the
   Phase log as the prompt says; append the prompt verbatim to PROMPTS.md under
   "Follow-up phases (2026-10)"; record departures from the prompt, this
   preamble included, under "Divergences". Names of individuals stay out of
   STATUS.md and PROMPTS.md: write the role and the date.

4. Where you run. A checkout without data/inventory.sqlite is a cloud session:
   build and test on fixtures; hand every store, GPU and box step to the
   operator as exact commands with the expected output; make your own
   environment, .venv-cloud, with the web, gt and release extras. A checkout
   with the store is the operator's WSL desktop: run those steps yourself under
   the prompt's rules: the store read-only unless the prompt says otherwise, a
   "go" before any job over an hour, any download over a gigabyte and any
   install. The side environments are .venv-w3 (web, gt, release) and .venv-k1
   (bench, gt, kurrent; every GPU step); never run `uv sync` against .venv.
   Disk: Ubuntu's filesystem is a growing file on the host's C: drive, so the
   budget for any large write is `df -h /mnt/c`, never `df /`; model
   checkpoints and anything over a few gigabytes go under /mnt/d/.

5. Numbers. Never write a number you did not produce. The committed reports
   carry the ones produced so far.

6. A go. A desktop session waits wherever the prompt says to wait; the operator
   is at the keyboard. A cloud session started with the whole step as its task
   records the pre-flight and proceeds, noting the departure under Divergences;
   the operator's yes is still needed for anything on the box or the store,
   which a cloud session hands over anyway.

7. Two sessions may be in flight on different branches, one desktop, one cloud.
   If `git merge origin/main` meets a conflict in STATUS.md or PROMPTS.md, keep
   both sides' entries, the newer above, and say so.

8. The archive (16 November). Once ARCH1 is merged, STATUS-archive.md holds
   the Current state and Phase log entries dated before 19 October and
   PROMPTS-archive.md every prompt already run; STATUS.md and PROMPTS.md
   keep one pointer line in each emptied place. A prompt that names an
   archived entry means the archived text: open the archive file for it.
   Append nothing to the archive files; new entries and prompts go to
   STATUS.md and PROMPTS.md as before. Until ARCH1 is merged the files are
   as they were and this clause is void.

Phase R1 — decoding with a language model, and one calibrated confidence per
line. Two parts: Part A in a cloud session on its own branch (the code, the
tests, a toy model from the fixture store); Part B on the operator's desktop
(the real language model from the edition text, the measurement, the
calibration), on the same branch, when no other torch process runs. No store
write; no deploy: C4 carries the decoder into the pipeline, K4's readings
get the calibration as a mapping recorded beside their run.

FIRST: read PROMPTS.md (COMMON CONTEXT), SPECS.md (§4.5 confidence, §7),
STATUS.md (the B1, K1, K3 and K4 entries; "Next"), reports/kurrent/k3-eval.md
and reports/htr/* from B1 (the harness's measured CER on PHILIUMM's split). If
this prompt conflicts with the repo, the repo + STATUS.md win; record the
divergence. Write the "R1 — decoding and confidence" entry in STATUS.md after
every task; if one exists, continue from its first unfinished task.

## Where you run, and the rules that follow from it
Part A: the cloud checkout, .venv-cloud with the bench + gt extras, the
fixture store; nothing of the desktop's. Part B: /home/evana/LeibnizLegible,
.venv-k1, the master store read-only, the PHILIUMM dataset and model under
data/ as K1 left them; one torch process on the machine at a time, so Part B
waits for K4's reading job; every job states its expected host memory first
(under 6 GB; `systemd-run --scope -p MemoryMax=6G` in the preamble's form);
long jobs under nohup with logs. Never write a number you did not produce.
Licences: flashlight-text (MIT on GitHub, "BSD" on PyPI: record both),
KenLM (LGPL: a tool and a linked library, never copied into the code; a line
in legal.py's registry), pyctcdecode (Apache-2.0, last release 2023, not the
first choice). The language model is built from text the project may use
(the edition's reading text of the open channels and the aligned lines);
the letter pool and Dresden are evaluation only and never enter it.

## Background
kraken 7.0.3 decodes greedily and nothing else: the beam and threshold
decoders of 6.x are gone and main has no language-model code. The hook is
clean: TorchSeqRecognizer.forward returns each line's softmax matrix (N, W,
C) after `logits / temperature`, label 0 is the CTC blank, and the recogniser
takes a custom decoder callable. KrakenEngine (src/leibniz/htr/engines.py)
calls `_rec_predict` and returns the greedy text with the mean per-step
probability as the line's confidence (SPECS §4.5); TrOCREngine (htr/trocr.py)
returns the decoder's sequence score. On comparable material at 8 to 10 % CER
a character 6-gram model built from training text alone took half a point to
a point off (Himanis 9.87 → 8.87, HOME-Alcar 8.35 → 7.85, Belfort 10.54 →
9.52; PyLaia, ICDAR 2024; lexicon-free, LM weight 1.5, about 0.12 s a line on
the CPU against 0.03 greedy); temperature scaling (T about 2) raised the
correlation between a line's confidence and its error from 0.2–0.6 to
0.7–0.8 on three datasets. The project's Latin and French reader is
PHILIUMM's kraken model today and C3's rebuild tomorrow; the German reader is
k3-trocr (K4). The gates that will use the score: the Scriptorium queue, the
vision-language second reader on flagged lines, the game's choice of lines,
pseudo-labels for self-training, C3's and C4's reports.

## Part A, cloud

### Task 0 — Pre-flight (report, then wait for a go)
A clean tree on the branch; ruff + pytest baseline; `pip index versions` for
flashlight-text, kenlm and pyctcdecode under the project's Python; whether
torchaudio in the lock still ships ctc_decoder (2.9 to 2.11 may not; use
flashlight-text directly if not). Print the plan; wait for "go".

### Task 1 — The decoder behind one interface (code and tests)
`src/leibniz/htr/decoding.py`: `Decoder` with `greedy` (today's behaviour,
bit for bit), `beam_lm` (flashlight-text's lexicon-free decoder with a KenLM
character model: beam size, LM weight and the blank/space handling as
PyLaia's recipe; tokens file written from kraken's codec with label 0 the
blank and the space a token), and `prefix_beam` (a pure-Python CTC prefix
beam search of the project's own with the same n-gram interface, for the
tests and as a fallback without the extras). Every decoder returns (text,
score, per-character scores) so the confidence of Task 3 is one function
over them. KrakenEngine takes `decoder=` and passes it to the recogniser;
`leibniz bench run` and `align letterpool-eval` take `--decoder greedy|beam-lm
--lm PATH --lm-weight W --beam N`. Tests on synthetic softmax matrices: the
greedy path unchanged; beam without LM equals greedy where the posterior is
peaked; a hand-made 3-gram pulls a near-tie to the modelled spelling; the
codec round trip. New dependencies as an optional extra `decode`; the
fallback path imports nothing new. CHECKPOINT A.

### Task 2 — The language model from the project's text (code; a toy model)
`leibniz bench lm-build --order 6 --out PATH`: the training text from
data/gt/edition_cache.jsonl (the open channels only, legal.deposit_for) and
gt_lines of the open bucket, normalised to the codec's conventions (the
aligner's fold, NFC, the hyphen rule of C2c, one line a sentence), with every
document of the evaluation sets held out by piece id (the PHILIUMM test
split's pages, the held-out pages of reports/philiumm/heldout_pages.csv,
K3's validation pieces, the letter pool's pages, Dresden); KenLM's lmplz with
modified Kneser-Ney and the ARPA kept beside a binary; the counts (lines,
characters, the held-out pieces) in reports/decoding/lm-build.md. On the
fixture store the toy model proves the path. A Latin-and-French model and a
German model as two files; say which text each saw. CHECKPOINT B: push,
print the compare URL, hand over Part B.

## Part B, desktop (after K4's reading job; the GPU idle, one torch process)

### Task 3 — The measurement
The real models from Task 2 (minutes on the CPU). Then CER greedy against
beam-lm, the LM weight and beam tuned on PHILIUMM's validation split only and
reported on: PHILIUMM's test split (B1's harness, their model, the honest
Latin-and-French number), the 20 PHILIUMM-judged lines, the held-out pages'
aligned lines (fair and light strata), and the German model's effect on
k3-kraken over the letter pool's selection half (reported on the test half)
— the German case is the lower bound, since at 30 % CER the model has less
to pull on. The cost in seconds a line on this CPU. If the Latin-and-French
gain is under a quarter of a point on the test split, say so and keep the
decoder off by default. reports/decoding/r1-decoding.md + .json.

### Task 4 — One confidence per line, calibrated
For both engines (kraken greedy and beam, TrOCR's sequence score) fit
temperature scaling on a validation set (PHILIUMM's split for the Latin and
French reader; K3's 3,133 validation lines for k3-trocr, whose hypotheses
and scores K3 kept under data/models/k3/trocr/best/) and report on the test
sets: the correlation of the score with the line's CER, the reliability by
decile, the share of lines under a threshold that are in fact right. Give the
thresholds the gates need, each with its measured precision: "exactly right
with 90 % precision", "worth a human's look", "send to the second reader".
Record the mapping as a JSON the store can carry per run (runs.params), so
K4's run gets its mapping without a re-read and C4's run gets its own.
CHECKPOINT C.

## Finish
STATUS.md: the R1 entry, "Key numbers" (the CER pairs, the thresholds),
"Next" (C3 scores every ablation with and without the decoder; C4 runs with it
if Task 3 earned it; the gates read the thresholds); legal.py: flashlight-text
and KenLM as tools with their licences; SPECS §4.5 amended with the
calibration; the prompt verbatim in PROMPTS.md under "Follow-up phases
(2026-10)". ruff + pytest clean. Push, print the compare URL. Do not merge.

CLOUD BATCH, 17 November 2026. Read this with the preamble and the prompt
above; where they differ, this note wins. Complete this step: record Task 0
and proceed without a go; where the prompt says to wait, proceed and note the
departure under Divergences. The operator answers nothing mid-task, so decide
the small things yourself and record them; stop only for something the prompt
did not foresee, and then write the question into the STATUS entry and push.
Other sessions run today on their own branches (K3b-prep, REL1 Part A, R1
Part A, G1b in the cloud; desktop-queue-1 on the desktop), so `git fetch
origin main && git merge origin/main` at the start and again before the final
push; on a conflict in STATUS.md or PROMPTS.md keep both sides' entries, the
newer above, and say so. Commit and push after every task. End with the
compare URL and a ten-line summary. Do not merge.
If this is ARCH1: it runs alone; the operator starts nothing else until it
is merged, so there is no parallel session to merge from.
If this is R1: Part A only here; Part B is a desktop session later, as the
prompt says; end at checkpoint B with the hand-over for Part B.
If this is REL1 Part A: the operator's note of 16 November follows this one
with Task 0's three answers; a bracket left unfilled means "propose and
proceed".
If this is CAL1 on the Calculemus repository: the Leibniz Legible preamble
does not apply; the prompt carries the game's conventions; no other session
runs on that repository today.
~~~~
