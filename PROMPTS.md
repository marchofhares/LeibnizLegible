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

### Phase G1b — the gold-first draw (run 2026-11-17)

_Run in a cloud session on the branch it was given
(`claude/eloquent-cannon-d2xv4r`), under the session preamble of 19 October
as updated on 21 October and 16 November, given with the prompt and printed
first below; the cloud batch note of 17 November, given after the prompt, is
printed last. No go was waited for (the preamble's item 6 and the note); the
departures, and one finding the prompt did not foresee (whose reading the
pack's first candidate is since K4: Open question 30 j), are in `STATUS.md`._

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

Phase G1b — the gold-first draw for the fragment pack. One cloud session on
the branch it was given; the fixture store; no GPU, no deploy. About two
hours. The operator rebuilds the pack on the desktop afterwards.

FIRST: read PROMPTS.md (COMMON CONTEXT), STATUS.md (the G1 entry; Open
question 30, items g to i; "Next"), src/leibniz/pack/fragments.py (the
draw, choose_gold, gold_counts; DEFAULT_GOLD_RATE 0.25,
DEFAULT_BAD_GOLD_SHARE 0.25, DEFAULT_MIN_CHARS 10, DEFAULT_MAX_CHARS 50),
src/leibniz/pack/check.py and src/leibniz/pack/cli.py. If this prompt
conflicts with the repo, the repo + STATUS.md win; record the divergence.
Write the "G1b — the gold-first draw" entry in STATUS.md.

## Why
The first real pack (2026-10-22: 2,000 rows, 56 gold, 2.8 %) found its gold
after the random draw, so the cap of 25 % was out of reach: 42 truths and 14
both-wrong rows in the whole selection. Open question 30 (g) and (h) are
answered as the plan page's G1 row says: draw the gold-eligible lines first,
among all eligible lines, up to the caps, then fill the strata; put a floor
under the shorter reading so that a pair where one reader failed asks
nothing. Item (i), the allocation across strata, stays the operator's: build
the option, keep the equal allocation as the default, and let the rebuild
command choose.

## Task 1 — The draw (code and tests)
In fragments.py: (a) gold first: among every eligible line, the truth-gold
candidates (either reading equal to the edition text under the fold) and
the both-wrong candidates are drawn first, seeded, up to gold_rate × limit
with at most bad_share of the gold both-wrong, then the strata are filled to
the limit with the rest; the row order in the pack is shuffled under the
seed as before and the pack never reveals which rows are gold (check.py's
rule). (b) `--bad-gold-share` default raised to 0.5, so an always-Bern
strategy is measurable (Open question 30 e and g). (c) The floor:
`--min-chars` applies to the shorter reading as well as the longer, or a new
`--min-ratio` (default 0.5) drops pairs whose shorter reading is under half
the longer; say which you chose and why in the docstring and the STATUS
entry. (d) `--strata` with weights ("fair_copy=0.35,light_revision=0.35,
heavy_revision=0.2,scrap=0.1" as the example), the equal allocation the
default; a stratum short of lines gives its surplus to the others as the
equal allocation does today. Tests on synthetic eligible sets: the cap is
reached when the supply allows; the both-wrong share; the floor; the
weights; the seed's reproducibility; `pack check` on the result.

## Task 2 — Record, push, hand over
STATUS.md: the entry; Open question 30 (g) and (h) answered, (i) left to the
operator with the option that serves it; "Next": the rebuild line for the
desktop (the two commands with absolute paths, the first pack's readings and
pieces, a new seed and date, the store read-only), the copy to the box and
the game session (CAL1) after it. Append this prompt verbatim to PROMPTS.md
under "Follow-up phases (2026-10)". ruff + pytest clean. Push, print the
compare URL. Do not merge.

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

### Phase DQ1 — the desktop read-only queue: the backup chore, P1 Task 3 (the zone census) and M1's print trial (run 2026-11-17)

_Run on the operator's desktop on `desktop-queue-1`, under the session
preamble of 19 October as updated on 21 October and 16 November (printed
first), the operator's note of 17 November for the queue (which wins over the
notes below), the P1 prompt with its operator's note of 16 November, and the
M1 prompt with its amendment of 13 October and its operator's note of 16
November; everything was given together and is printed below verbatim. The
go of 17 November and its four changes are recorded in `STATUS.md` (the P1 entry)._

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

OPERATOR'S NOTE, 17 November 2026: the desktop read-only queue, DQ1. Read it
with the preamble above and the two prompts and two notes that follow it;
where they differ, this note wins, over the branch names in both notes too.

What this session is. One desktop session that runs, in this order: (0) the
backup chore, if a copy is due; (1) P1 Task 3, the zone census with
PHILIUMM's v2 segmentation model, under the P1 prompt and its operator's
note of 16 November; (2) M1's print trial, Task 1b alone, under the M1
prompt, its amendment of 13 October and its operator's note of 16 November.
The store is read-only throughout: nothing here writes to
data/inventory.sqlite; if a step would, stop and say so. Nothing is
deployed, sent or merged.

Branch: desktop-queue-1, created from main as the preamble says, one branch
for the whole queue (not philiumm-layout-census, not marginalia-print-trial).
Two STATUS.md entries, "P1 — Task 3, the zone census" and "M1 — the print
trial (Task 1b)", each kept current after every task so that a fresh session
can take over with `claude --continue`; both prompts, both notes and this
note appended to PROMPTS.md once, under "Follow-up phases (2026-10)".

One go. Task 0 is one combined pre-flight: the clean tree and the branch;
nvidia-smi (nothing on the GPU); df -h /mnt/c /mnt/d; the baselines in
.venv-w3 and .venv-k1; whether git lfs is installed; whether the backup is
due (the newest copy under /mnt/d/leibniz-backups/ and in r2backup against
30 October, K4's write); the plan with durations. Report it and wait for one
"go". After it, proceed without asking for: the installs the two prompts
name, each into its own environment under data/ (never .venv, never the
project's dependencies): her pipeline's Python 3.12 environment, git lfs
through apt if missing, the dfine_kraken or YALTAi environment under
data/print/; downloads up to 5 GB in all (the LFS models, the v2
checkpoints, the page images); jobs up to six hours each, under nohup with a
log under logs/, polled. Stop and ask for: anything over those limits;
anything that would write to the store; a rental; an apt package other than
git-lfs; anything the prompts did not foresee. Claude Code's own permission
prompts are the operator's to answer as they come.

0. The backup chore, only if due: the four lines of the chore (a read-only
   SQLite backup to /mnt/d/leibniz-backups/inventory-YYYY-MM-DD.sqlite,
   rclone copy to r2backup:leibniz-backups, rclone check --one-way) with
   today's date, under nohup with a log, the copy first; it reads only and
   runs beside everything below; report its `rclone check` line when it
   ends. If a copy is current, say so and skip.
1. P1 Task 3 as its note says, through checkpoint C and its Finish, with two
   changes: commit and push after every task (not only at the end), and
   leave the two registry entries (philiumm-seg-v2, philiumm-layout-dataset-v2)
   to the K3b-prep cloud session running today; name them in the STATUS
   entry instead. The three sentences for the model's author go into the
   STATUS entry and the final summary.
2. M1's print trial as its note says, with two changes: render the sheet of
   50 printed lines early, as soon as the print zones are known, print its
   path and continue with everything that needs no transcription (zones per
   class, the print-body share, the IoU of the v1 lines with the print
   zones, the Fraktur share, the tools' licences into the registry); when
   the operator pastes "done", compute the CER and finish the report; if no
   "done" has come when everything else is done, write the report with the
   CER marked pending and the exact command that computes it, and finish.
3. Finish: ruff + pytest; both STATUS entries complete (what ran, the
   numbers, what is pending); "Next" updated (K3b is the next desktop
   session; its Task 0 reads the K3b-prep tools); push desktop-queue-1;
   print the compare URL and a ten-line summary. Do not merge.

Memory and disk, the rule of 26 October for every job: its expected host
memory from a pilot measured with /usr/bin/time -v, under 6 GB, run under
systemd-run --scope -p MemoryMax=6G, one torch process at a time, four
loader workers at most, nothing else of yours beside it. Her pipeline's
clone, its environment, the models and the 600 images go under
/mnt/d/leibniz-layout/ (symlinked from data/philiumm/ as K3 did for its
models) unless df -h /mnt/c shows more than 25 GB free; the print trial's
environment the same under /mnt/d/leibniz-print/; state the expected disk
before each write. If the machine or the session dies, the operator resumes
with `claude --continue`; read STATUS.md's two entries and the logs first and
continue from the last completed task.

Phase P1 — PHILIUMM cross-checks: their aligner sample, the A VI,4 cross-comparison,
and a layout-zone census. One local session on the operator's desktop (WSL2
Ubuntu), with the data, the store and the GPU at hand.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md. If this prompt conflicts with the repo, the repo + STATUS.md
win; record the divergence in STATUS.md. Write the "P1 — PHILIUMM cross-checks"
entry in STATUS.md after every task. If STATUS.md already carries a P1 entry,
continue from its first unfinished task; if that entry says the branch was
merged, create `philiumm-layout-census` from main and continue there.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible, the one the C1 corpus run, the C2 mint and W3 used.
Facts, to verify in Task 0 rather than assume:
- data/inventory.sqlite is the MASTER store (16 GB: 13.5M v1 lines, 297k
  gt_lines). Open it read-only only: `uv run leibniz …` commands open it
  mode=ro; your own Python uses a `file:…?mode=ro` URI. Never write to it, never
  VACUUM or move it, never delete anything under data/. This phase writes
  nothing to the store.
- The page-image cache is /mnt/d/leibniz-images (the D: drive); the runbooks
  pass it as `--images /mnt/d/leibniz-images`, and pages.local_path is relative
  to that root (see align/audit.py attach_images).
- `.venv` is the pipeline environment (kraken, torch with CUDA): never run
  `uv sync` against it and never install into it. Use the side environment W3
  made, `.venv-w3` (web, gt and release extras; gt brings Pillow for crops):
  export UV_PROJECT_ENVIRONMENT=.venv-w3 in your shell for every `uv` command.
  This phase adds no Python dependency to the project; PHILIUMM's pipeline gets
  its own environment under data/philiumm/ (Task 3).
- The GPU is a GTX 1660 Ti (6 GB) reachable from WSL2. Task 3 may use it;
  nothing else here needs it.
- Long jobs run under nohup with a log under logs/ (gitignored); poll the log,
  print its tail when done. Ask the operator for a go before: cloning and
  installing their pipeline, running it, a download over 1 GB, a job expected
  to run over an hour, and installing any software (apt, npm).
- Every result lives in reports/philiumm/ and reports/layout/ as small
  committed files (Markdown, JSON, CSV of at most a few thousand rows),
  rendered by code from data, prose templated. Bulky artefacts (downloads,
  crops, HTML sheets, models, full CSVs) go under data/ (gitignored) and are
  described, not committed. Never write a number you did not produce.
- The operator merges, and only after the numbers have been shared with the
  PHILIUMM team: the repo is public, so a merge is a publication. You push the
  branch and hand over; you never merge. Nothing is deployed. Branch:
  `philiumm-crosschecks`, created from main.
- Their two GitLab repositories have no licence file, and on 2026-10-06 they
  said they are considering CC BY-NC for their dataset and models as well. Read
  their code, run their pipeline locally under data/, copy nothing from either
  repository into this one, and record the commit SHAs you used.

## Task 0 — Pre-flight (report, then wait for a go)
1. `git status --porcelain` shows nothing but the operator's own untracked
   files (logs, *.log, resume-run.sh, .python-version, reports/gt-audit/
   gt-audit.html and the like; leave them alone). `git rev-parse --abbrev-ref
   HEAD` is main; `git pull --ff-only origin main`; confirm the remote.
2. `df -h data /mnt/d`; `uv --version`; `git lfs version` (Task 3 needs it;
   if missing, ask before `sudo apt-get install -y git-lfs`); `nvidia-smi`.
3. Baseline in .venv-w3: `uv run ruff check .`, `uv run ruff format --check .`,
   `uv run pytest -q`. Record the counts.
4. Ask the operator two things and wait: whether PHILIUMM's new RF-DETR model
   has been published (the gate before Task 3), and whether Task 3 should run
   on the current bundled model regardless, for the 13 October call.
5. Print a short plan with the steps you expect, their durations and what
   needs a go, and wait for the operator's "go".

## Background (all you need)
The ERC PHILIUMM project (David Rabouin, Denisa-Florina Bumba; Laboratoire SPHERE,
Université Paris Cité – CNRS) built the Leibniz HTR model this project runs
(FoNDUE-GD_v2_ft_Leibniz, Zenodo 10.5281/zenodo.21457538, CC BY 4.0 as obtained)
and the baseline segmentation model of the v1 corpus run (Zenodo
10.5281/zenodo.21537859, CC BY 4.0). In an email exchange from 2026-09-28 they
offered to collaborate; Denisa pointed to three things (below); she and David
then judged the 200-line ground-truth audit sheet and returned it on
2026-10-07 (scored in a separate session, not here); and a call is set for
2026-10-13. The owner brings three cross-checks of their three things to that
call. On 2026-10-07 David also noted that their model was not trained on
printed material (the Marginalien), on hands other than Leibniz's, or on
Kurrent; Task 3's sample takes the first of these into account.
1. Their alignment code (PASSIM `seriatim --linewise` + a filter + a sliding-window
   second pass):
   https://gitlab.com/eman8/scripts/htr-ocr/alignement-verite-de-terrain-et-transcriptions
   (branch main; raw files at .../-/raw/main/<path>). Worked example in the repo:
   GT/LH_1_3_4_0001-0002_1.txt (edition reading text for LH I 3,4 Bl. 1–2, from
   A VI,4); HTR/LH_1_3_4_0002r-0001v.xml and HTR/LH_1_3_4_0002v-0001r.xml (PAGE XML
   with HTR lines; each image is an opening with two folios); htr_replaced_gt/ (the
   same files with aligned GT written into each line's <Unicode>, blank where
   nothing aligned); alignment_report.csv with columns
   filename,nb_htr_lines,nb_gt_aligned,pct_gt_aligned,nb_low_conf,pct_low_conf,
   nb_ratio_too_low,pct_ratio_too_low,nb_ratio_too_high,pct_ratio_too_high,
   nb_no_alignment,pct_no_alignment,nb_window_passages,nb_fallback_lines.
   Their totals on the sample, read from that committed CSV: 257 HTR lines, 230
   aligned (89.5 %). Settings: the README's defaults are conf_threshold 0.0,
   min_token_ratio 0.4, max_token_ratio 2.5 and min_sim 0.5, and its usage
   example runs --conf_threshold 0.7; the dataset card states the noisy split was
   filtered at Levenshtein ≥ 0.7. Treat 0.7 as the comparable per-line threshold
   and say where each number comes from; do not state any other setting without
   a source. Record the commit SHA you fetched.
2. Their dataset, Hugging Face DenisaBumba/htr_leibniz_dataset_v1 (CC BY 4.0 as
   obtained; the former name DenisaB/… redirects to it; Zenodo twin
   10.5281/zenodo.21622297, whose data.zip is 4.2 GB, do not fetch it).
   train/noisy/ = 735 PAGE XML + JPG pages whose lines carry edition text aligned
   from A VI,4 by the code above (blank <Unicode> where unaligned; 43,372 aligned
   lines); train/clean/ = 248 hand-corrected pages; val/ = 27 pages (used by this
   project's B1 reproduction). The Hub lists 1,966 files under train/ and 54
   under val/, consistent with those counts. Names are shelfmark + folio:
   LH_1_12_2_0124r.xml = LH I 12, 2 Bl. 124r; LH_1_20_0063r-0062v.xml = an
   opening showing 63r and 62v. List files via
   https://huggingface.co/api/datasets/DenisaBumba/htr_leibniz_dataset_v1 (the
   siblings array); fetch with
   https://huggingface.co/datasets/DenisaBumba/htr_leibniz_dataset_v1/resolve/main/<path>.
   Only XML files are needed. Update HF_DATASET in src/leibniz/htr/artifacts.py
   and its attribution line to the new name. The model this project runs trained
   on the noisy and clean pages, so those 1,010 pages must be excluded from any
   future evaluation set (Phase C3).
3. Their layout pipeline:
   https://gitlab.com/eman8/scripts/htr-ocr/scripts-pour-le-pretraitement-des-corpus-pour-escriptorium
   (branch main; models in Git LFS: `git lfs install`, clone, `git lfs pull`).
   The README gives two installation paths; the Linux one is a single Python 3.12
   environment (supervision requires 3.12) with `pip install -r requirements.txt`
   (rfdetr, supervision, kraken 7), marked "should work, not tested"; a uv venv
   is an acceptable substitute for their conda command. Run:
   `python main_pipeline.py --input <images> --output <results> --config
   config_local.json` (no API key; the local config names their last best model
   and a detection confidence of 0.4). Steps: RF-DETR zone prediction (MainZone,
   MarginTextZone, DigitizationArtefactZone, GraphicZone-figure, NumberingZone;
   formula classes GraphicZone-formula{,-inline,-strikethrough,-complex} masked if
   emitted), COCO → PAGE XML regions (03_regions_xml), masks over figure and
   formula zones, binarisation, masked image, Kraken baselines inside text zones
   (06_baselines_and_htr), merge, polygon simplification, overlap fixes, line
   splitting; final PAGE XML in 10_fixed_lines. Bundles
   models/segmentation/baselines/best_0.4750.safetensors, apparently the same
   checkpoint as this project's v1 segmenter (blla_ft_leibniz_v1_0.4750): verify
   by checksum, and if so the only difference from v1 lines is masking plus
   region merge. Denisa expects to publish a new RF-DETR model, fine-tuned on
   corrected formula polygons and compared with D-FINE, by mid to late October
   2026; Task 3 is gated on it unless the operator said otherwise in Task 0.

## Task 1 — This project's aligner on their sample (needs no local data)
- Add src/leibniz/align/pagexml.py: PAGE XML TextLines in reading order (region
  order, then line order) with id, Coords polygon, Baseline, and <Unicode> text
  (may be empty). Offline test on a trimmed fixture.
- Fetch the sample files (cache-first, polite UA) into data/philiumm/sample/.
- Run align_piece (src/leibniz/align/align.py; inputs HtrLine(ref, text)) with the
  full GT text against each HTR file separately with free_edition_ends=True,
  mirroring their per-file run; also try the two page concatenation orders and
  report the best. Use the default threshold and also a threshold you argue is
  comparable to their 0.7 rule.
- Produce their CSV columns from this project's result (nb_gt_aligned = minted,
  nb_no_alignment = declined, filter columns N/A) and a line-by-line comparison
  against their htr_replaced_gt output with this project's normalizer
  (src/leibniz/align/normalize.py) and folded similarity (src/leibniz/align/dp.py,
  as audit.py uses it): both aligned and same text (≥ 0.9), both aligned but
  different, this project only, theirs only, neither. Print the differing pairs.
- CLI `leibniz align philiumm-sample`; report reports/philiumm/alignment-sample.md.
  Commit. CHECKPOINT A: update the STATUS.md entry and commit.

## Task 2 — Cross-compare A VI,4 (run here)
Build, with offline tests on fixtures, one CLI with subcommands, then run them
in order on the store:
- `leibniz align philiumm-vi4 fetch`: the 735 train/noisy XML files into
  data/philiumm/noisy/, cache-first, resumable, at most one request per second
  (about fifteen minutes).
- `leibniz align philiumm-vi4 match`: file name → shelfmark + folio(s); works via
  works.shelfmarks and src/leibniz/catalog/shelfmarks.py (Roman numerals likely;
  write the parser to inspect real shelfmark strings and report unparsed names);
  canvases via pages.label with src/leibniz/align/resolve.py; openings may map to
  one canvas or two, handle both, report ambiguities. Lines by geometry: scale
  their Coords from imageWidth/imageHeight to pages.width/height, greedy
  one-to-one by polygon IoU (report threshold and sensitivity). The lines table
  may hold several runs per page: use the run that produced the recognised text.
  gt_lines.line_image_ref carries the canonical line id "{page_id}:{line_seq:03d}"
  for factory-minted rows (align/pairs.py; audit.split_ref parses it); the test
  store's seeded gt_lines rows use an older "#xywh" form, so assert the real
  form on the store before relying on it.
- `leibniz align philiumm-vi4 compare`: their aligned text vs gt_lines.text for the
  matched line, lines.text as third witness; normalizer + folded similarity;
  buckets agree (≥ 0.9), near (0.7–0.9), disagree (< 0.7), this project only,
  theirs only, neither; per stratum and per page. State what agreement does not
  prove (two aligners fed the same edition text can share a mistake).
  Writes: reports/philiumm/vi4-crosscheck.md; reports/philiumm/vi4-summary.json;
  reports/philiumm/heldout_pages.csv (this project's page_ids for all 1,010 of
  their pages, for C3); reports/philiumm/vi4-disagreements-sample.csv (at most
  500 rows); full disagreement and double-witnessed CSVs under data/philiumm/.
- `leibniz align philiumm-vi4 sheet`: a second audit sheet of disagreements,
  data/philiumm/philiumm-disagreements.html, through the crop machinery in
  src/leibniz/align/audit.py. That machinery must accept an explicit list of
  line refs; if K1 has already landed that refactor on main, reuse it, else do
  it here without changing the existing sheet's behaviour or tests. The sheet
  downloads verdicts in the same CSV shape as the C2 sheet (ref, stratum,
  verdict, note), so the PHILIUMM team could judge it the way they judged the
  first. Never touch reports/gt-audit/gt-audit-lines.csv or
  gt-audit-verdicts*.csv.
Every subcommand ends with a compact printed summary. Run fetch, match, compare
and sheet here (crops from /mnt/d/leibniz-images), read the results, commit
reports/philiumm. CHECKPOINT B: update the STATUS.md entry and commit.
GATE for Task 3: per the operator's Task 0 answers. If the new model is out, or
the operator asked for the census on the current model, continue. Otherwise
state in STATUS.md that Task 3 waits for the model, commit, and go to the
hand-over; a later session resumes at Task 3 with this prompt.

## Task 3 — Layout-zone census (run here, with a go)
Build, with fixtures:
- `leibniz layout sample --n 400 --seed 0`: equal numbers per stratum
  (page_stats.stratum_heuristic; fall back to set/work if NULL, which it is
  under C1) plus 100 pages from LH 35 (find via works.shelfmarks) and 100 pages
  from the Marginalien set as a separate block (printed body with marginal
  notes, the case David raised), reproducible; symlink or copy cached JPEGs
  from /mnt/d/leibniz-images into data/philiumm/layout-sample/images/ named by
  page_id; write the sample list to reports/layout/sample.csv.
- tools/philiumm-layout-env.sh: creates a separate Python 3.12 environment under
  data/philiumm/rfdetr-env/ (uv venv or python -m venv), clones their pipeline
  with LFS into data/philiumm/rfdetr-pipeline/ (record the commit SHA and the
  checksums of the model files), installs requirements, and prints a diagnosis
  on failure. tools/philiumm-layout-run.sh: runs main_pipeline.py on the sample
  with config_local.json under nohup, logging to logs/. Never modify their
  repo; keep any local patch as a .patch file under data/philiumm/.
- src/leibniz/layout/zones.py (pure, tested): parse 03_regions_xml zones by class
  with polygons and 10_fixed_lines lines; geometry via
  src/leibniz/pipeline/geometry.py or plain Python, no new heavy dependency.
- `leibniz layout zone-census`: per page and per stratum, the LH 35 and the
  Marginalien blocks separate: zones per class; share of pages with any figure,
  formula, margin zone; v1 lines whose polygon lies mostly inside a figure or
  formula zone, count and share; on the Marginalien block, v1 lines inside
  MainZone (the printed body) vs MarginTextZone (the notes); v1 line count vs
  their final line count; matched-line comparison by IoU. Writes
  reports/layout/zone-census.md, reports/layout/zone-census-summary.json,
  reports/layout/zone-census-per-page.csv (the sample is small enough to commit).
Ask for a go, run the environment script, the sample, the pipeline (hours, GPU
optional) and the census here; if the environment cannot be made to work on
this machine, say so in STATUS.md and stop the task honestly. Commit
reports/layout. CHECKPOINT C: update the STATUS.md entry and commit.

## Finish and hand-over
Complete STATUS.md's "P1 — PHILIUMM cross-checks" entry: what was built, key
numbers, what is unmeasured and why, open questions (opening vs folio canvas
mapping; class coverage of the bundled checkpoint; flagging v1 lines inside
non-text zones in the viewer now; a v2 zones table with SegmOnto type, polygon
and a LaTeX field; the printed-body share of Marginalien lines), next steps
(rerun Task 3 with each later PHILIUMM model; use heldout_pages.csv in C3;
the licence change PHILIUMM is considering, with the fact that this project's
copies were obtained under CC BY 4.0, for the lawyer memo). Append this prompt
verbatim to PROMPTS.md under "Follow-up phases (2026-10)". ruff + pytest clean,
all tests offline. Commit in sensible pieces and `git push -u origin
philiumm-crosschecks`. Then hand over: print the compare URL
https://github.com/marchofhares/leibnizlegible/compare/main...philiumm-crosschecks?expand=1,
a plain-language summary of the cross-checks for the operator to bring to the
call (what agrees, what differs, what it does not prove), and the reminder
that the PR is merged only after the PHILIUMM team has seen the numbers. Do
not merge.

OPERATOR'S NOTE, 16 November 2026, for P1 Task 3 (where it differs from the P1
prompt and the preamble, this note wins):
- Tasks 1 and 2 are done and merged (STATUS.md, the P1 entry); only Task 3
  runs here. Branch: philiumm-layout-census, created from main as the
  preamble says. Task 0's two questions are answered: PHILIUMM's new model is
  published, and Task 3 runs on it.
- The model is DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2
  on Hugging Face (RF-DETR-Seg Nano; checkpoint_best_ema_v2.pth and
  checkpoint_best_regular_v2.pth; training resolution 1,272 px; eight
  SegmOnto classes: MainZone, MarginTextZone, NumberingZone,
  DigitizationArtefactZone, GraphicZone-figure, MathsRegion-complex,
  MathsRegion-inline, MathsRegion-strikethrough; the author recommends a
  detection threshold of 0.4; licence CC BY-NC 4.0 on the card, its outputs
  this project's own under the agreement of 15 October). Download both
  checkpoints under data/philiumm/models/ (cache-first; record the SHA-256
  of each and the card's revision), point her pipeline's config at the EMA
  checkpoint, and record which checkpoint and threshold ran in the report.
  Her pipeline bundles a v1 checkpoint: do not run the census on it except
  as a one-page smoke test. The class names in the P1 prompt are v1's: parse
  whatever the v2 model emits and report the classes it used.
- The sample: first list the author's training pages from her dataset,
  DenisaBumba/layout-leibniz-dataset-v2 (public, CC BY 4.0; the originals
  under original/train and original/valid, 334 and 40 pages, most named by
  shelfmark and folio as the HTR dataset's files are, some by eScriptorium
  page id, which image matching against the cache resolves; write the list
  to reports/layout/philiumm-layout-pages.csv as Task 2 did for the HTR
  dataset), then draw the 600 pages outside that list and outside
  reports/philiumm/heldout_pages.csv; her 18 test pages may enter the
  sample as a named block, since they are her own held-out set; include
  DE-611-HS-971383:0035 (a page with two writing directions) as a named
  extra, and, if STATUS.md carries a K3b entry with its 24 segmentation
  pages, those 24 as a second named block, so the hand-corrected lines K3b
  collects serve this census too.
- Memory and disk, the rules of 26 October (the preamble): the expected host
  memory of the pipeline from a 20-page pilot measured with /usr/bin/time -v,
  under 6 GB, run under systemd-run --scope -p MemoryMax=6G; one torch
  process at a time; the clone, the models and the 600 images stated against
  df -h /mnt/c before they are written, or under /mnt/d/ if C: is short.
- Add registry entries philiumm-seg-v2 (the model, CC BY-NC 4.0) and
  philiumm-layout-dataset-v2 (the dataset, CC BY 4.0) to src/leibniz/legal.py
  beside the v1 entries (source, version, licence as published with the
  date seen, the bucket, what this project built from it: the zone census),
  with a test as the other entries have.
- Nothing is deployed; nothing is written to the store. Push the branch,
  print the compare URL, and end with three sentences for the operator's
  mail to the model's author: the sample, the checkpoint and threshold, the
  headline of the census. Do not send anything.

Phase M1 — Marginalien triage: separate the printed body of the annotated
books from Leibniz's notes, count both, and say so in search, the viewer, the
exports and the counts. One local session on the operator's desktop (WSL2
Ubuntu), possibly stopped and resumed at its checkpoints; the GPU if zones are
needed for every page; a deploy with an index rebuild at the end.

FIRST: read PROMPTS.md (its COMMON CONTEXT block applies to this session in full),
SPECS.md and STATUS.md (Open question #5, the W3 and P1 entries, and
reports/layout/zone-census.md from P1 Task 3). If this prompt conflicts with
the repo, the repo + STATUS.md win; record the divergence in STATUS.md. Write
the "M1 — Marginalien triage" entry in STATUS.md after every task; resume from
it if present.

## Where you run, and the rules that follow from it
You run in Claude Code in bash under WSL2 Ubuntu, in the checkout at
/home/evana/LeibnizLegible. data/inventory.sqlite is the MASTER store (16 GB).
This phase writes to it, in Tasks 2 and 3 only, through project code with a
runs row, idempotent and resumable, and only after a dated backup copy: before
the first write, `deploy/prepare-store.sh`-style `VACUUM INTO` to
/mnt/d/leibniz-inventory-backup-<date>.sqlite with its SHA-256 (about ten
minutes), and the operator's explicit go. Everything else opens the store
read-only. The page-image cache is /mnt/d/leibniz-images. `.venv` is the
pipeline environment (never run `uv sync` against it); use `.venv-w3`
(export UV_PROJECT_ENVIRONMENT=.venv-w3); PHILIUMM's layout pipeline lives in
its own environment under data/philiumm/ from P1 Task 3 (tools/
philiumm-layout-env.sh, tools/philiumm-layout-run.sh), copies nothing into the
repo, and runs only with a go. Long jobs under nohup with logs under logs/;
ask for a go before any job over an hour. Results in reports/marginalia/ as
small committed files rendered by code from data; never write a number you did
not produce. The operator merges; you push and hand over. The deploy at the end
needs a new serving copy, an index rebuild and a restart: each step shown, run
only on a yes. Branch: `marginalia-triage`, created from main.

## Task 0 — Pre-flight (report, then wait for a go)
Clean tree on main (the operator's own untracked files aside); `git pull
--ff-only origin main`; `df -h data /mnt/d` (the backup copy needs 20 GB on
D:); `nvidia-smi`; baseline ruff + pytest counts; confirm reports/layout/
zone-census-per-page.csv exists with a Marginalien block (P1 Task 3); if it
does not, stop and say so. Print a plan and wait for "go".

## Background
The census (reports/census.md) counts 396 annotated printed books, 103,887
pages, 44 % of all page images; W3 lists 370 of them by Marginalien number.
The v1 run read every line of their printed bodies with a model trained on
Leibniz's hand. David Rabouin (PHILIUMM, 2026-10-07): the model "was not
trained to transcribe printed material and it will introduce noise if you plan
future training. Moreover, these texts are not from Leibniz (only the
manuscript notes in the books are)". Search under "All collections" returns
printed-book text as if it were Nachlass text; the About page's counts include
it; STATUS Open question #5 flagged the scope in July. P1 Task 3 ran PHILIUMM's
layout pipeline on 100 Marginalien pages and reports how v1 lines fall into
MainZone (the printed body) and MarginTextZone (the notes). What nobody has
published: how many lines of Leibniz's own notes the 396 books hold.

## Task 1 — The cheapest classifier that separates print from notes (read-only)
Per Marginalien work: pages, v1 lines, mean confidence, page_stats (line-height
CV, overlaps, short lines). On the P1 sample, with its zone labels as truth,
fit and compare three ways of calling a v1 line printed body: geometry (a line
within the page's main text block, found from the lines' own x-extents and
regular heights, vs outside it), the v1 confidence distribution, and the zone
model itself. Report precision and recall for "note" per method, and choose:
the geometric rule if it reaches 90 % precision on notes, else the zone model
for every page (Task 2). Writes reports/marginalia/census.md (first part) and
reports/marginalia/classifier.json. Commit. CHECKPOINT A.

## Task 2 — Zones for every Marginalien page (only if Task 1 chose the model)
Measure the pipeline's rate on 200 pages first and print the ETA for 103,887
(resumable, under nohup, outputs under data/layout/); ask for a go. Then
`leibniz layout zones-import`: the per-page zones into a new additive table
page_zones(page_id, zone_class, polygon, source, run_id) with a runs row,
idempotent, after the backup copy and the go. Commit the schema change with
its migration and tests. CHECKPOINT B.

## Task 3 — The flag
`leibniz layout mark-printed`: per Marginalien page and line, printed = inside
a printed-body zone (or by the geometric rule where Task 1 chose it), written
per page into page_stats.metrics (JSON, additive) and per line into a new
additive table line_flags(line_id, flag, source, run_id); one pass, a runs
row, idempotent, resumable; after the backup copy and a go if Task 2 did not
already take one. Counts into reports/marginalia/census.md: lines of notes vs
lines of print per work, and the headline numbers for the corpus. Commit.
CHECKPOINT C.

## Task 4 — Search, viewer, exports, counts, docs
- search/documents.py marks printed lines; the index build leaves printed-body
  text out of the default document text and keeps it in a separate field, so a
  search can include it (`?printed=1` on /api/search; a checkbox "Include the
  printed text of annotated books" / DE equivalent on the search form); snippets
  never come from printed lines unless asked; a hit on a Marginalien page says
  "notes in a printed book".
- The page view badges printed lines and lists the notes first in the line
  panel; the work page says "annotated printed book: N pages, M lines of notes";
  /api/pages carries `printed` per line.
- /api/stats and the About page restate the corpus counts with print separated;
  llms.txt says what the Marginalien are and how the flag works.
- release/export.py carries `printed` per line and the dataset card says so;
  C3's exclusion reads line_flags (document it in the C3 amendment).
Tests throughout; the fixture store gains a Marginalien work with a printed
page. Verify on the master store: `uv run leibniz index build` into a scratch
FTS5 file under data/ (not the serving index), `uv run leibniz serve --port
8765` on it, HTTP and browser checks (search with and without the box, a
Marginalien page view, the work page, About, EN and DE, axe 0). Commit.
CHECKPOINT D.

## Finish and hand-over
STATUS.md entry: the headline numbers, the classifier chosen and its
precision, what changed where; Open question #5 closed; the backup copy's path
and hash. Append this prompt to PROMPTS.md under "Follow-up phases
(2026-10)". ruff + pytest. `git push -u origin marginalia-triage`; the compare
URL; wait for "merged". Then the deploy, each step shown and run only on a
yes: a new serving copy (deploy/README.md §2, from the store with the new
tables), its transfer, the index rebuild on the box (§5, hours; the app keeps
serving the old index until the build swaps it in), the §9 code update and
restart; then verify live (a search with and without the printed text, a
Marginalien page, /api/stats, About) and in the operator's browser without a
hard reload.

## Amendment of 2026-10-13 (Denisa's follow-up email; where it differs from the tasks above, it wins)
PHILIUMM recommends, for the printed text, the Gallicorpora+ kraken model
(https://github.com/Gallicorpora/Segmentation-and-HTR-Models, release 1.0.0,
Gallicorpora+_best.mlmodel; repository CC0-1.0; DOI 10.5281/zenodo.7410360;
French print of the 16th to 19th century) and, for the print layout, the
YALTAi pipeline (SegmOnto zones, ALTO output). YALTAi is archived (2026-04,
GPL-3.0) and its README points to the kraken D-FINE plugin
(https://github.com/mittagessen/dfine_kraken) and kraken 7. Her command, for
the record: `yaltai kraken --device cpu -I "images/*.jpg" --alto --suffix
".xml" segment --yolo tests/nano-yolo-ladas.pt ocr -m
Gallicorpora+_best.mlmodel`; the YOLO file named there is the fixture in
YALTAi's own tests/ folder, not a published model.
- Task 0 is relaxed: reports/layout/zone-census-per-page.csv may be absent
  (their v2 segmentation model is published since 4 November). Then run Task 1b first
  and use its print zones as the printed-body truth for Task 1; the notes
  count stays provisional until P1 Task 3 has run, and the report says so.
- Task 1b — The print trial (new; read-only on the store; can run before
  anything else in this phase, as its own session if the operator says so).
  100 Marginalien pages: the P1 block if it exists, else 100 pages drawn by
  seed across the 396 works, the Fraktur-set books included on purpose. In a
  separate environment under data/print/ (never .venv, never the repo's
  dependencies), with a go: the dfine_kraken plugin on kraken 7 for zones;
  if it will not install or has no usable model, YALTAi in its own venv on
  the device the operator names (`--device cuda:0` on the 1660 Ti), its
  GPL/AGPL noted; then kraken with Gallicorpora+ on the printed-body lines.
  Save PAGE XML (or convert the ALTO) under data/print/, nothing into the
  store. Report: zones per class per page; the printed-body share; the
  model's CER on 50 printed lines the operator transcribes in a sheet the
  session renders (ten minutes of print), roman and Fraktur type separately;
  the overlap (IoU) of the v1 lines with the print zones. Decision, written
  into reports/marginalia/print-trial.md: (a) the printed text is read with
  a print model and shown as such; (b) print is flagged only and never read;
  (c) a Latin or Fraktur print model is needed first. Everything run goes to
  L1's registry (name, version, licence, how it ran).
- Task 2 may run the trial's zone model for the printed body where their v2
  model is not yet available; the notes come from their model when it lands.
- Task 4 under decision (a): the printed-body text is a run of its own
  (model Gallicorpora+, its licence per L1), shown as "print, read by an OCR
  model" and still out of the default search; the handwriting model's
  readings of printed lines are superseded, not deleted.
- The count of Leibniz's own notes (Task 3's headline) is the number for
  David; the trial's print numbers are for Denisa, with thanks.

OPERATOR'S NOTE, 16 November 2026, for M1's print trial (where it differs from
the M1 prompt, its amendment and the preamble, this note wins):
- Only Task 1b runs in this session, as the amendment of 13 October defines
  it: the print trial on 100 Marginalien pages, the store read-only, nothing
  written, no deploy; Tasks 1 to 4 and the Finish are a later session.
  Branch: marginalia-print-trial, from main. Task 0 is only the clean tree,
  the baseline, nvidia-smi and df -h /mnt/c /mnt/d; the zone-census file
  may be absent.
- The 100 pages: P1 Task 3's Marginalien block if reports/layout/ carries
  it on main (then the pipeline's zones for those pages are the first
  comparison), else 100 pages drawn by seed across the 396 works, the
  Fraktur books in on purpose; write the list to
  reports/marginalia/print-trial-pages.csv.
- The tools: dfine_kraken on kraken 7 in its own environment under
  data/print/ (a go for the install); YALTAi in its own venv only as the
  fallback, its GPL and the AGPL underneath noted; Gallicorpora+ on the
  printed-body lines. Every tool run goes to legal.py's registry with its
  licence. Memory, the rule of 26 October: the expected host memory from a
  pilot measured with /usr/bin/time -v, under 6 GB, systemd-run --scope -p
  MemoryMax=6G, one torch process.
- The sheet of 50 printed lines for the operator to transcribe (roman and
  Fraktur apart): render it under data/print/, print its path, stop, and
  resume when the operator pastes "done".
- Finish: reports/marginalia/print-trial.md with the decision (a), (b) or
  (c) and the numbers; the STATUS entry; the M1 prompt and this note to
  PROMPTS.md; push; the compare URL; three sentences for the operator's
  mail to the tools' author (what ran, the print-body share, the CER on
  print). Do not merge.
~~~~
