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
