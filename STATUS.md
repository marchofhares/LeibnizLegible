# STATUS — Leibniz Legible

_The project's shared memory, as an index: where the project stands, one row per phase, the key numbers, the open questions by number, what is next. Every session reads it in full, then the phase files under `status/` that its prompt names._
_It has a budget, at most 600 lines and 80,000 bytes (`tests/test_status_budget.py`): a session writes its record in its own file under `status/` and only its own lines here. The rule is in `status/README.md`._

_Last updated:_

- 2026-11-19: ARCH2 — STATUS.md and PROMPTS.md are indexes with a budget; each phase's record is a file under `status/`, each prompt as run a file under `prompts/` → `status/README.md`
- 2026-11-18: DQ1 — the desktop queue: the backup chore, P1 Task 3 (the zone census), M1's print trial (decision (a) for roman print, the Fraktur half pending) → `status/2026-11-17-dq1.md`
- 2026-11-18: G1b follow-up — main merged; `leibniz pack fragments --only-records CSV` (Open question 30 j, way 3) → `status/2026-11-17-g1b.md`
- 2026-11-18: REL1 Part A — the first releases, built in a cloud session on fixtures; Part B is the operator's desktop → `status/2026-11-17-rel1.md`
- 2026-11-17: R1 Part A — decoding with a language model, the code; Part B is the desktop's → `status/2026-11-17-r1.md`

_The one line that stood here to 2026-11-18, with every item back to July → `status/last-updated-to-2026-11-18.md`._

---

## Current state

### Where the project stands (2026-11-19)

**Live.** The site shows 12,947,584 lines (`/api/stats`, the index built 2026-10-31): 11,407,896 of the PHILIUMM kraken
model `FoNDUE-GD_v2_ft_Leibniz` (v1; 7.95 % CER on PHILIUMM's validation lines, a Latin and French number) and 1,539,688
of the German reader `k3-trocr@runs-615-epoch-5` on 24,078 German pages, live since the operator's switch of 30 and 31
October (K4; 28.6 % CER on the letter pool against v1's 46.6 %). A German page the language pass missed keeps v1's text.

**The store.** The last write to the master store that the entries record is K4's of 2026-10-30 (run 616, the `page_lang`
table; run 617, the German reader's readings; 19,354,243,072 bytes after). `gt_lines` holds 333,680 rows since K2's
write (run 609). DQ1's backup chore of 17 November made the dated copy `inventory-2026-11-17.sqlite`, uploaded and checked.

**The last batch (17–18 November)**, six sessions, all merged (#63 to #68; no pull request is open): ARCH1, the archive;
K3b-prep, the verdict tools for the sheet the Edition judged (`audit-convert`, `audit-score --corrections`, `audit-apply`,
`audit-sheet-k2`); REL1 Part A, the first releases prepared on fixtures (the cards true to the store, the model package
`leibniz-kurrent-trocr`, the Zenodo and Hugging Face scripts, `release check`); R1 Part A, decoding with a language
model (three decoders behind one interface, `bench lm-build`); G1b, the gold-first draw for the fragment pack; and DQ1
on the desktop: the backup chore, P1 Task 3 (the zone census: 1.6 % of the 44,104 v1 lines inside a figure or formula
zone) and M1's print trial (on the operator's 24 roman lines Gallicorpora+ reads at 3.56 % CER against v1's 14.94 %:
decision (a) for roman print, the Fraktur half pending). None of it wrote the store; nothing of it is deployed.

**Next on the desktop: K3b.** Its Task 0 converts and scores the Edition's verdicts on K2's audit sheet (returned on
6 November: 76 lines confirmed, 118 corrected) and then makes the one write, `leibniz align audit-apply --write`, after
a backup and the operator's go; the commands are in `status/2026-11-17-k3b-prep.md`. **For the operator: REL1 Part B**,
the ten steps of its runbook (the exports from the master store, the DOI reservations, the uploads, the drafts published
in the browser), after Open questions 34 and 35 and after K3b's write if the verified lines are to be in the first
version (`status/2026-11-17-rel1.md`).

### The phases, newest first

| Phase | Dates | State | In one line | Entry |
| --- | --- | --- | --- | --- |
| DQ1 (P1 Task 3, M1's print trial) | 2026-11-17/18 | merged (#68) · ⏳ the Fraktur half of the sheet | the desktop read-only queue: the backup chore, P1 Task 3 (the zone census on PHILIUMM's v2 segmentation model over 621 pages), M1's print trial (decision (a) for roman print) | `status/2026-11-17-dq1.md` |
| REL1 | 2026-11-17/18 | Part A merged (#65) · ⏳ Part B (the operator's desktop) · ⏳ Part C | the first releases, Part A: four records prepared, the cards true to the store, the Zenodo and Hugging Face scripts up to the draft, `release check` | `status/2026-11-17-rel1.md` |
| R1 | 2026-11-17 | Part A merged (#66) · ⏳ Part B on the desktop (Tasks 3 and 4, the Finish) | decoding with a language model and one confidence per line, the code | `status/2026-11-17-r1.md` |
| K3b-prep | 2026-11-17 | merged (#64) · the store steps are K3b's Task 0 | the verdict tools: `audit-convert`, `audit-score --corrections`, `audit-apply`, `audit-sheet-k2`, three registry entries | `status/2026-11-17-k3b-prep.md` |
| G1b | 2026-11-17/18 | merged (#67) · ⏳ the operator's answer to Open question 30 (j), the rebuild on the desktop, the copy to the box | the gold-first draw for the fragment pack; `--only-records` added on 2026-11-18 | `status/2026-11-17-g1b.md` |
| ARCH1 | 2026-11-17 | merged (#63) | the archive: the finished phases moved out of STATUS.md and PROMPTS.md, verbatim | `status/2026-11-17-arch1.md` |
| Arrivals | 2026-11-16 | recorded (no code, no data) | two arrivals: the K2 audit sheet is judged (the Edition's Arbeitsstelle, 6 November); PHILIUMM's v2 segmentation model is published (3 November) | `status/2026-11-16-arrivals.md` |
| K4 | 2026-10-26/30 | ✅ live (the operator's switch, 2026-10-31; #58 merged) · next round: a second language pass | German on the site: k3-trocr over the German pages, the store written once (runs 616 and 617), the language filter | `status/2026-10-26-k4.md` |
| LT1 | 2026-10-28 | ✅ Part A (merged as #56) · ✅ Part B (the operator's run, 2026-10-29/30) · LT1b when wanted | the page-level test of frontier vision models against the project's readers | `status/2026-10-28-lt1.md` |
| K3 | 2026-10-21/24 | ✅ done · ✅ the operator's choice (2026-10-26: TrOCR) · merged (#55) · what is pending is K3b's | a Leibniz Kurrent model: k3-trocr 28.6 % CER and k3-kraken 30.6 % on the letter pool | `status/2026-10-21-k3.md` |
| A3b | 2026-10-21/22 | built, merged (#53, the reports #54) · the heading's ⏳ (the dry run again, the write, the serving copy) to be closed: see Next | the Arbeitskatalog import (the Arbeitsstelle's export, 70,405 records), the holdings page | `status/2026-10-21-a3b.md` |
| G1 | 2026-10-21 | ✅ merged (#51) · ✅ the real pack, built and checked · the pack is rebuilt (G1b) before any copy to the box · the judgments import is P8's | the Calculemus seam: `leibniz pack fragments`, `pack check`, `pack judgments` | `status/2026-10-21-g1.md` |
| L1 | 2026-10-21 | built, merged (#50) · the operator's lines and the owner's open decision stand | the licence registry; the ground truth as two deposits by channel | `status/2026-10-21-l1.md` |
| W6 | 2026-10-21 | built, merged (#49) | two reader's items from the Leibniz-Edition: the catalogue's search by shelfmark on every work page, a scope paragraph on About | `status/2026-10-21-w6.md` |
| K2 | 2026-10-20/21 | ✅ done, merged (#48) | German ground truth: the Bern reader over the German pieces, then the factory; `gt_lines` 315,797 → 333,680 rows | `status/2026-10-20-k2.md` |
| C2c | 2026-10-20 | ✅ done, merged (#47) | the re-mint: 315,797 open-bucket lines | `status/2026-10-20-c2c.md` |
| K2b | 2026-10-19/20 | ✅ done, merged (#46) | the letter-pool test set: 134 letters, the first measured German error rates | `status/2026-10-19-k2b.md` |
| A0 to W5 | 2026-07-28 to 2026-10-10 | done (the list below) | every phase before 2026-10-19 | `STATUS-archive.md` |

_State: the ✅ and ⏳ marks of each entry's heading, brought up to the merges on main. #63 to #68 were verified on GitHub on 2026-11-19 (no pull request is open); #51, #55, #56 and #58 are as the entries record them; #46 to #50, #53 and #54 are read from the merge commits on main, where a heading written before its merge still says "⏳ the operator's pull request". "The K3 entry" in a prompt means the file in that row._

### Before 2026-10-19: in STATUS-archive.md

_Entries before 2026-10-19 (the entry of 2026-10-14 back to July, and the retained subsections from "Prior gate (retained)" to "A3 in numbers") → STATUS-archive.md, "Current state (archived)"._

- W5 — the review's fixes and six reader features (2026-10-10) → STATUS-archive.md
- K1 — Kurrent track (2026-10-09) → STATUS-archive.md
- W4 — text access (2026-10-08) → STATUS-archive.md
- S1 — a staging site on the VPS (2026-10-08) → STATUS-archive.md
- P1 — PHILIUMM cross-checks (2026-10-08) → STATUS-archive.md
- C2b — the audit closed and read (2026-10-07) → STATUS-archive.md
- W3 fix — the viewer's modules as one versioned set (2026-10-06) → STATUS-archive.md
- W3 — the browse index: shelfmark family → section → convolute (2026-10-06) → STATUS-archive.md
- W2 — "quoted phrases" and -exclusions in search (2026-10-02) → STATUS-archive.md
- W1 — the overlay toggle, plain-text export, deploys visible at once (2026-10-02) → STATUS-archive.md
- D — a sibling app on the host: Calculemus, flagged off (2026-09-27) → STATUS-archive.md
- D — the image mirror (2026-09-16, operator decision; see Divergences) → STATUS-archive.md
- D — deployment kit, public-traffic hardening, public-repo prep (2026-09-16, later session) → STATUS-archive.md
- D1–D3 — search, viewer, IIIF, releases, built on v1 (2026-09-16) → STATUS-archive.md
- C1 — corpus-run robustness, from the first live runs (2026-07-29/30) → STATUS-archive.md
- C2 — close-out: the hand audit is preliminary; gate deferred to C3 (2026-09-16) → STATUS-archive.md
- C2 — the mint ran; hand-audit tooling (2026-09-15/16) → STATUS-archive.md
- C2 — the mint's first live runs: workers OOM-killed → aligner rebuilt (2026-09-15) → STATUS-archive.md
- C2 — GT factory at scale, the inputs built and run (2026-09-11) → STATUS-archive.md
- C2 — GT factory at scale (2026-07-29) → STATUS-archive.md
- C1 — Corpus segmentation + HTR v1 (2026-07-29) → STATUS-archive.md
- B2 — Retro-alignment prototype (2026-07-29) → STATUS-archive.md
- B1 — Benchmark harness + PHILIUMM reproduction (2026-07-29) → STATUS-archive.md
- A3 — Katalog crosswalk (2026-07-29) → STATUS-archive.md
- A2 — Image cache (2026-07-29) → STATUS-archive.md
- A1 — OAI/IIIF harvest → inventory + corpus census (2026-07-29) → STATUS-archive.md
- A0 — Repo scaffold (2026-07-28) → STATUS-archive.md

---

## Key numbers

| Metric | Value |
| --- | --- |
| Tests passing | **1,228** with 10 skipped (2026-11-18, G1b merged with main at #66, in the slim environment: `.venv-cloud`, Python 3.13.18, the `web` + `gt` + `release` extras; main's 1,193 there and G1b's 35; G1b alone on 17 November 1,103 with 3 skipped, 1,071 at its pre-flight); 1,225 (2026-11-18, R1 Part A merged with main at #65, in `.venv-cloud` on CPython 3.12.13 with the `web` + `gt` + `release` + `bench` + `decode` extras and KenLM's programs on `KENLM_BIN`; 1 skipped; **1,193** with 10 skipped in the slim environment, Python 3.13.18 with `web` + `gt` + `release`, where REL1 counted 1,160 and 3); 1,136 (2026-11-17, R1 Part A, in `.venv-cloud` on CPython 3.12.13 with the `web` + `gt` + `release` + `bench` + `decode` extras and KenLM's programs on `KENLM_BIN`; 1 skipped; 1,095 at its pre-flight; 1,104 with 10 skipped in the slim environment, Python 3.13.18 with `web` + `gt` + `release`, where ARCH1 counted 1,071 and 3); **1,160** (2026-11-18, REL1 Part A merged with main at #64, a cloud checkout with the `web` + `gt` + `release` extras; 3 skipped for want of numpy; 1,120 on the branch before that merge; 1,071 on main at ARCH1's merge); 1096 (2026-10-30, main with K4 merged, checked in a cloud checkout with the `web` + `gt` + `release` extras before the pull request); 1,052 (2026-10-30, K4, in `.venv-w3` with the `web` + `gt` + `release` extras; 1 skipped, `test_align_letterpool_eval.py`'s eleven for want of numpy there); 1026 (2026-10-26, main with K3 merged, checked in a cloud checkout with the `web` + `gt` + `release` extras before the pull request); 904 (2026-10-26, K3, in `.venv-k1` with the `bench` + `gt` + `kurrent` extras); 980 (2026-10-22, A3b follow-up 2, in `.venv-cloud` with the `web` + `gt` + `release` extras; 979 after the first follow-up, 976 after A3b on 2026-10-21, 948 at its pre-flight); 948 (2026-10-21, G1, in `.venv-cloud` with the `web` + `gt` + `release` extras; 880 at its pre-flight); 880 (2026-10-21, L1, in `.venv-cloud` with the `web` + `gt` + `release` extras; 859 at its pre-flight on main the same day); 866 (2026-10-21, K2, in `.venv-k1`; 859 at W6 the same day in `.venv-cloud` with the `web` + `gt` + `release` extras, 856 at its pre-flight; 841 at K2b, in `.venv-k1` with the `bench` + `gt` + `kurrent` extras: 807 at the pre-flight, +18 parser, +5 set, +11 metric; 808 after W5, with the `web` + `gt` + `release` extras; 704 after K1, in `.venv-k1`; 644 after W4, 634 after S1, 621 after P1 Task 2, 606 after C2b, those with the `gt` + `web` + `release` extras) |
| **REL1 Part A (2026-11-18)** | no master figure: a cloud session. **The scored audit as restored to `reports/gt-audit/audit-summary.json`: 200 lines, 199 judged, 185 scored, corpus-weighted precision 72.3 %, 92.2 % usable, FAIL at 95 %** (by stratum, scored and precision: fair_copy 50, 84.0 % · light_revision 45, 86.7 % · heavy_revision 48, 64.6 % · scrap 42, 57.1 %; the committed file had read 8 lines, 95.0 %, PASS, a test's output, since 2026-10-10) · the export on a synthetic store (8,000 pages, 528,000 line rows, 404 MB): 480,000 lines written as Parquet in **27.3 s at a peak of 289 MiB** in the cloud container · the dry run on K4's fixture store: 4 folders, 4 deposit files, 21 dry-run `PUT`s to Zenodo, 22 files to the Hub, the NC deposit refused · read through the public APIs on 2026-11-17: the PHILIUMM models CC BY-NC 4.0, their dataset CC BY 4.0, the Bern model MIT, all as the registry has them |
| **R1 Part A (2026-11-17): decoding, the code** | no CER and no threshold yet: the CER pairs (greedy against beam-lm on PHILIUMM's split, the judged lines, the held-out pages, k3-kraken on the letter pool) and the calibrated thresholds are Part B's, on the desktop. Produced here: flashlight's score is the best path's natural-log probability plus the weight times KenLM's log10 probability (measured on a toy model); one synthetic line of 472 frames by 150 labels decodes on the cloud container's CPU in **0.44 s** with flashlight at beam 50 and every label a frame, 0.13 s at 20 labels a frame, 0.07 s at 10; the prefix beam in 0.30 s at beam 50, 0.10 s at 20; the toy models from the fixture store 12 lines / 457 characters (Latin and French) and 13 / 476 (German), fixture sentences that say nothing about the Nachlass |
| **K4 live (2026-10-31)** | the live index rebuilt beside the old one 12:36–17:35 (**4 h 59 m**; 5 h 33 m on 10 October); `/api/stats` after the swap: lines shown **12,947,584** (FoNDUE-GD_v2_ft_Leibniz 11,407,896 · k3-trocr@runs-615-epoch-5 1,539,688), pages by language de 30,797 · fr 62,330 · la 110,167 · mixed 13,801 · unknown 19,115, built 2026-10-31T17:34:46Z; search `Herr` lang=de **9,933** pages; the transfer 1 h 49 m at 2.65 MB/s; the box's root disk 42 GB of 75 used after the switch (the staging build had left 679 MB free: stopped and dropped) |
| **K4 German pages and READER's run (2026-10-30)** | `page_lang` 236,210 rows under run 616 (la 110,167 · fr 62,330 · de 30,797 · unknown 19,115 · mixed 13,801); run 617 (stage recognize, model `k3-trocr@runs-615-epoch-5`, scope `de`): **1,539,688 rows on 24,078 German pages** (the 6,719 German Marginalien pages left out; 33 empty readings without a row; 252,278 rows on crops under 80 px); the lines shown under the rule 12,947,584, of them READER's 1,539,688 and v1's 11,407,896; the master store 19,354,243,072 bytes after (+2,210,672,640) |
| **K4 reading job (2026-10-28/30)** | 1,539,721 lines in 39 h over two launches (one guard kill), 90.8 ms a line, 39,666 lines an hour, host peak 2,769,976 KB, card peak 5,922 MiB, GPU 88.2 % mean |
| **K4 serving copy (2026-10-30)** | `inventory-serving-2026-10-30.sqlite` on D: **18,314,969,088 bytes** (4,471,428 pages; the master's 4,725,157), `VACUUM INTO` 08:57–09:38 over the share at 4–7 MiB/s; its integrity check over the share stopped after 79 min at under a megabyte a second and moved to the box; SHA-256 `3ff238b22a89e8dde77d7f965b47045785b0d37740bf25eae0f2c1496da8f782` (58 min 32 s over the share) |
| **K4 browser checks (2026-10-30)** | **92 of 92** on a fixture store (Playwright 1.64.1, Chromium build 1243, EN and DE, 1,280 and 390 px, axe-core 0 violations) |
| **LT1 letter pool, page models (2026-10-30)** | 34 letters, 98 pages (L 48, K/k 50), K2b's metric, failed pages charged / left out (30 letters): **Gemini 4 Argon 24.2 % (17.3–31.5) / 19.5 %** · **Gemini 3.1 Pro 25.8 % / 21.7 %** · **Claude Fable 5.1 26.4 % / 24.4 %** · k3-trocr 26.9 % (21.9–31.9) / 25.7 % · k3-kraken 29.5 % / 27.8 % · trocr-kurrent-xvi-xvii 35.0 % · v1 43.9 %; Leibniz's hand (L) Argon 33.3 %, Claude 33.9 %, Gemini 3.1 Pro 35.8 %, k3-trocr 33.4 %; the correspondents' (K/k) Argon 13.2 %, Gemini 3.1 Pro 13.8 %, Claude 17.4 %, k3-trocr 19.0 %; the diff on 1,664 aligner-accepted lines: exactly right k3-trocr 363, Claude 272, Gemini 3.1 Pro 210, Argon 190, both wrong 1,126–1,183 |
| **LT1 PHILIUMM held-out pages, page models (2026-10-30)** | 27 pages, 34 calls, 1,878 reference lines, page CER against the dataset's PAGE XML, failed pages charged / left out: **Claude Fable 5.1 22.5 % (18.0–27.5)** · Gemini 3.1 Pro 27.2 % / 24.5 % · Gemini 4 Argon 33.6 % / 30.7 % (per-page median 17.0 %, max 229 %); the PHILIUMM kraken model **7.95 %** on the same 1,878 lines as the dataset cut them (B1), 26.29 % (25.13–27.48) on `page-lines`' audit-style crops (LT1b); failures after one retry: Claude 0, Gemini 3.1 Pro 1 (+ 4 on the pool), Argon 1 (+ 1); cost logged for 132 pages each: Argon 1.06 USD, Gemini 3.1 Pro 1.43, Claude 11.43 |
| **K3 training (2026-10-22/25)** | **kraken** (runs row 614): ketos from the PHILIUMM checkpoint, the codec 178 → 203 code points, batch 2 × 8, four loader workers, **37 epochs in 44.5 h** (71 min an epoch, 13 lines/s all-in, the card at 2.2 GB), stopped after checkpoint 36 at kraken's accuracy 0.8659; **TrOCR** (runs row 615): the whole Bern model, Adafactor with gradient checkpointing at batch 8, **six epochs in 27.0 h** (4.5 h an epoch, 3.45 lines/s, the process at 3.5 GB), the best at epoch 5 |
| **K3 validation CER (3,133 held-out mint lines)** | **k3-trocr 11.84 %** (Leibniz's hand 19.7 %, other hands 11.4 %; heavy 13.3 % · light 8.3 %) · **k3-kraken 15.56 %** (23.8 % / 15.1 %; 17.8 % · 10.2 %); the pilots' single epochs 13.67 / 24.74 %; the two disagree on 2,935 lines, one exactly right on 13.5 % |
| **K3 letter-pool CER, unfiltered (2026-10-26)** | K2b's set, philiumm policy, 95 % bootstrap over letters: **k3-trocr 28.6 % (24.6–32.5)** · selection 24.7 % (21.0–28.3) · test 31.6 % (25.3–36.8) · Leibniz's hand (L) 36.7 % (31.9–41.0) · the correspondents' (K/k) 19.4 % (15.7–23.8); **k3-kraken 30.6 % (26.5–34.5)** · selection 26.6 % (23.0–30.4) · test 33.6 % (27.0–38.9) · L 39.7 % (34.7–43.9) · K/k 20.3 % (16.8–24.6); against the Bern base 37.0 %, v1 46.6 %, philiumm 52.9 % (K2b); the kraken model reads nothing on 3,905 of the 18,445 lines (2,517 narrower than 80 px) |
| **K3 Dresden and speed (2026-10-26)** | Dresden (383 lines, philiumm policy): k3-trocr 11.9 % (10.7–13.1), k3-kraken 13.2 % (12.1–14.3) (the Bern base 7.4 %, PHILIUMM 29.5 % in K1); ms a line on the GTX 1660 Ti as K1 measured: k3-trocr 181, with the decoder's cache 152, k3-kraken 52; K2's 310,831 lines at K2's overhead: 13.3 h / 4.6 h |
| **A3b Arbeitskatalog export (2026-10-21)** | `ritter.csv` **70,405 records**, 45 columns · `URL_Ms` on 49,341 (GWLB 39,673: 39,257 by id, 416 by PPN; Arcinsys 4,189) · holdings 215: **Hannover NLB 48,167 (68.4 %)** · no shelfmark 7,509 · Hannover NLA 4,218 · printed witness 1,700 · `pdf_url` 18,995 rows, 25,012 of the 35,133 records with a piece number matched · Ordnungsvermerk on 3,051 records (259 names) · the mapping on the fixture: textart, signatur, titel, datum, aa **100 %** over 21 website records, the names 46/46 cells through the persons table, hand rule 21/21 · the operator's dry runs on the store (2026-10-22): first datum 98.4 % before the second-date fix, nine renumbered ids, 16 hand changes of 24,907; second signatur 99.6 %, titel 99.9 %, textart 100 %, aa 100 %, datum 98.6 % before the short-date rule (346 "other"), 48726 → 69490, eight unmatched, every ground-truth id present · browser checks 84 + 32 |
| **G1 fragment pack (2026-10-21, the operator's run)** | the 2,148 German records on 4,734 pages: **305,602 lines** (the latest run of each) → another registration's (W5's twins) **112,513 (36.8 %)** · no v1 text 21,419 · empty reading 49 · the same text 1,441 · under 10 characters 50,176 · over 50 40,551 · refused under §70 0 → **79,453 eligible** (fair 55 · light 18,904 · heavy 59,345 · scrap 1,149; Leibniz's own hand 5,188, 6.5 %) → **2,000 rows** (fair 55 · light 649 · heavy 648 · scrap 648; his hand 131, 6.5 %; de 1,939 · mixed 61; the longer reading 10–19 380 · 20–29 330 · 30–39 497 · 40–50 793) · **gold 56 (2.8 %): truth 42 (the Bern reading every time, v1 never) · both-wrong 14**; of the 2,000, 553 lines with a reader-minted row: 282 withheld (NC deposit), 271 open — **one reading equal to the minted text under the fold on 43 (15.9 %)**, neither on 228 (84.1 %); `pack check` OK; 390 s, the store read-only |
| **K2 German ground truth (2026-10-21)** | the Bern reader `trocr-kurrent-xvi-xvii` over **310,831 lines** on 4,807 pages of the 2,148 German records (7 h 26 min, 87 ms a line, fp32 + kv cache, batch 16; every Dresden reading as the checkpoint's defaults'); at the factory's gate **v1 10.8 % → Bern 16.9 %** of the lines (Leibniz's own hand 9.5 → 12.5 %); the rule: 1,178 pieces to the reader, 402 kept by v1, 568 none; the write (run 609): **`gt_lines` 315,797 → 333,680** (50,720 reader rows) · **German records 42,278 → 60,163** · Leibniz's own hand 1,888 → 2,612; the 200-line sheet half his hand, half the others, judged by the Leibniz-Edition's Arbeitsstelle and returned 2026-11-06 (76 correct · 21 boundary · 98 corrected without a verdict · 1 wrong · 3 unreadable · 1 blank; 118 corrected transcriptions, median 43 characters; scored by hand group, strict and under the fold, in K3b's Task 0) |
| **C2c re-mint (2026-10-20), beside the C2 mint** | **315,797 open-bucket lines** (was 297,424; +6.2 %) · fair 10,234 (9,913) · light 100,085 (96,175) · heavy 203,749 (190,162) · scrap 1,729 (1,174) · 6,130 records (5,526) on 17,669 pages (16,843) · by channel ia 213,520 · gwlb 52,057 · potsdam 50,220 · 7,308 of 16,807 pieces minted, 337,432 pairs, every skip structural (0 locked; C2: 746) · **hyphen flag 848 (0.3 %; was 7,822, 2.6 %)**, 8,523 minted lines end in a hyphen mark (271) · bracket 4,811 (1.5 %) · math 255 (0.1 %) · **Leibniz's own hand 14.9 %** under the strict rule (25.7 % under the loose rule on the old mint; the strict rule there 15.1 %) · A VI,4: 62,164 paired, agree 9,506 · disagree 774 · **1,472 held-out pages** |
| **K2b letter-pool test set (2026-10-19)** | the GWLB pool, nine checked volumes (1708–1716, version 1 each): **2,533 letters** parsed (835 German, 1,179 French, 489 Latin) · **695 German and placeable** (L 111, l 1, K 560, k 17) · **565 placed** on the store (no work 72 · no canvas 10 · no lines 0 · shared leaves 48) · disjoint from K2's German pieces' pages (0 of 1,782) and the PHILIUMM held-out pages (0) · **the set: 134 letters (67 L, 65 K, 2 k) · 386 pages · 18,815 recognised lines · 325,624 reference characters**; selection half 67 letters, 7,696 lines · test half 67, 11,119 lines; CC BY-NC 4.0, nc bucket, the texts gitignored |
| **K2b German CER, unfiltered (2026-10-20)** | `philiumm` policy, pooled, 95 % bootstrap over letters: v1 **46.6 %** (43.3–49.5 %) · philiumm **52.9 %** (49.8–55.6 %) · trocr-kurrent-xvi-xvii **37.0 %** (32.5–41.0 %) · trocr-hanse-xvi **35.6 %** (31.2–39.6 %) (evaluate only) · trocr-hanse-xvii **38.9 %** (34.6–42.8 %) (evaluate only); test half 48.2 / 54.6 / 39.2 / 38.0 / 41.2 %; the correspondents' hands (K/k) 38.5 / 45.5 / 23.2 / 22.8 / 26.4 %, Leibniz's own (L) 53.7 / 59.3 / 49.2 / 46.7 / 49.8 %; per-letter medians 42.9 / 49.4 / 31.5 / 28.3 / 32.8 %; **selected** (the aligner's accepted lines only): yield 21.6 / 15.0 / 26.5 / 28.7 / 26.6 %, CER 28.7 / 31.9 / 15.6 / 15.5 / 18.0 % |
| **W5 live (2026-10-11, `/api/stats`)** | 236,795 page records · **196,439 distinct scans** · 40,297 scans registered under more than one label: 39,442 spreads split, 855 folded, 519 candidates left · lines 13,508,625 · **9,846,450 lines once each** · 15,425 letters (Bodemann, from correspSearch) · 991 / 1,060 letter convolutes named (680 before) |
| **K1 pilot on Leibniz's German (2026-10-09)** | 20 German pieces + 5 controls, 2,639 lines, GPU; German yield at the factory's gate: philiumm **12.5 %** · trocr-kurrent-xvi-xvii **20.2 %** · trocr-hanse-xvii **20.6 %** · trocr-hanse-xvi **22.5 %** · v1 **16.4 %**; control yield: philiumm 41.6 % · trocr-kurrent-xvi-xvii 23.6 % · trocr-hanse-xvii 18.2 % · trocr-hanse-xvi 30.5 % · v1 40.5 %; gate **GO** |
| **K1 Dresden ranking (2026-10-09)** | 383 Kurrent Trace lines, GPU; CER under the `philiumm` policy: trocr-kurrent-xvi-xvii **7.4 %** · trocr-hanse-xvi **8.9 %** · trocr-hanse-xvii **10.9 %** · philiumm **29.5 %** · mccatmus **51.7 %**; the baseline `philiumm` at 29.5 % is not noise |
| **K1 aligner noise tolerance (2026-10-09)** | 1,878 lines, 76 pieces; base CER 7.95 %; yield at 30 % CER 97.0 % / 94.0 % / 79.8 % / 46.0 % (fair / light / heavy / scrap); **break-even yield < 50 % at ≈ 55 / 48 / 38 / 29 % CER**, precision < 95 % at ≈ 51 / 48 / 42 / 39 % |
| **K1 German census (2026-10-09)** | cache 10,029 records: de 2,036 · la 3,631 · fr 3,999 · mixed 331 · unknown 32; **2,173 German pieces** of 10,121 with a text, 5,874 pages, **401,394 lines, 40,915 minted (10.2 %)** vs Latin + French 1,328,532 lines, 252,762 minted (19.0 %); minted text with German stopwords 27,643 (67.6 %) at mean confidence 0.839; Leibniz's hand 82 pieces, 18,056 lines |
| **W4 text access (2026-10-08)** | the live page view before: a drag in the line list selected 0 characters, select-all copied 11,828 with the chrome; after, on the fixture store: **39/39** browser checks, axe-core 0 violations ×5, 390 px without horizontal scroll; on staging (operator, the same evening): record 41800 answers **84 lines on 2 pages, mean confidence 0.96** |
| **W3 browse index (2026-10-06)** | 2,225 works under 36 section anchors: LH 750 in 30 sections · LBr 1,060 · Marg 370 · Other 45 in 4 sets |
| **W3 letter convolutes with a correspondent** | **680 / 1,060 (64.2 %)**; with catalogue records 744 (70.2 %); most frequent name kept 634 + 25 (F series) · a lesser name that fits the shelf order 21 · withheld 60 · records naming nobody 4 |
| W3 `/api/works` on the corpus store | 0.64 s first call, 2 ms after; 781 KB, 84 KB gzipped · `/browse` HTML 187 KB, 43 KB gzipped |
| **Phase D (2026-09-16)** | search index (FTS5/Meili) · API · IIIF v3 + annotations · viewer (EN/DE, axe-clean) · Parquet exports + cards |
| Reports on Zenodo | statement 22782813 · census 22782815 · PHILIUMM repro 22782817 · retro-aligned GT 22782819 |
| **C1 corpus run (2026-09-11)** | **COMPLETE: 236,210/236,795 pages recognised (99.75%) · 13,508,625 lines** |
| C1 corpus remainder | 569 skips (enumerated reasons) · 16 permanently unfetchable (GWLB redirect loops) |
| C1 corpus cache | 236,779 pages · **395.6 GB** (drive-D image store) |
| C1 final architecture | 4 sharded CPU seg workers (~515 pg/h) ∥ 1 GPU recogniser (~940 pg/h), WAL + keyset batches |
| **C1 pipeline** | `pending→segmented→recognized` state machine, resumable/idempotent; +27 tests |
| C1 segmentation stats | per-page line count / coverage / height-CV / overlaps / short-lines → `page_stats` |
| **C2 GT factory** | enumerate §70 pieces → resolve canvases → anchored align → stratum-threshold → mint; +33 tests |
| C2 folio resolver (Open Q #10) | katalog `Bl.` range × IIIF folio labels → exact canvases (**solved**) |
| C2 banded aligner | O(len·band) NW + traceback; **0 mismatches vs full DP** (exactness-tested) |
| **C2 anchored aligner (2026-09-15)** | k-gram chain → chunked band; crash shape **44 MB / 1.9 s** (was ~6 GB, OOM-killed); 300k-char treatise 112 MB / 46 s |
| **C2 mint (2026-09-16)** | **297,424 open-bucket GT lines** (fair 9,913 · light 96,175 · heavy 190,162 · scrap 1,174) from 6,383 pieces; 5.9× target; ~2 h on 6 workers |
| **C2 hand audit (PHILIUMM, 2026-10-07)** | 199/200 judged: 136 correct · 33 boundary · 16 wrong · 14 unreadable → **weighted precision 72.3 % (FAIL at 95 %)**, usable **92.2 %**; per stratum 84.0 / 86.7 / 64.6 / 57.1 %; **1 misaligned line in 185 scored**; patterns: boundary-letter 35 · normalization 16 · hyphen 13 · bracket 7 · math 5 · reading 4 · addition 2 |
| C2 normalization tax, first sample | 46 corrections, 45 placed: 9.4 % as written / 7.9 % folded; on the accent-and-comma lines **3.1 % / 0.0 %** |
| C2 audit agreement | the operator's 20 (2026-09-16) vs PHILIUMM: 11/20 |
| **C2 reach census (2026-10-08)** | 297,424 lines · hyphen **7,822 (2.6 %)** · bracket 4,338 (1.5 %) · math 249 (0.1 %, a floor) · addition proxy 82.7 % (useless) · Marginalien 0 · LH 35 9,145 |
| **P1 Task 2: A VI,4 under two aligners (2026-10-08)** | 62,114 paired lines on 735 pages: agree 9,307 · near 2,886 · disagree 771 · ours only 5,145 · theirs only 21,949 (7,838 on 161 pages with no mint at all) · neither 22,056; HTR witness on disagreements 383 / 381; **1,149 held-out pages** |
| **P1 Task 1: their aligner's example (2026-10-08)** | theirs 230/257 (89.5 %, no gate; 212 at ≥ 0.7) · this project per region **194/257 (75.5 %)**, 179 at raw ≥ 0.7 · both same 170 · theirs only 40 (the interleaved marginalia) |
| **C2 hand census (2026-10-08)** | of 296,587 lines with a Textart: author's own hand **40.1 %**, **Leibniz's own hand 25.7 %** (fair 1.7 · light 8.3 · heavy 35.8 · scrap 18.2 %) |
| C2 edition texts | 10,029 records: median 2.5k chars · p90 15k · **186 over 100k** (VI,6 N. 2 = 754k) |
| C2 stratum thresholds | fair_copy 0.55 · light 0.62 · heavy 0.72 · scrap 0.80 (drafts held higher) |
| **C2 extraction QA (live, real Leibniz print)** | `gpt-4o` reading-text extract, head/page-no dropped; 2-model QA flagged **1/2**, agreement **0.67** |
| C2 target | ≥50k new open-bucket lines (vs PHILIUMM ~63k) — awaits corpus HTR + keyed extraction |
| **B2 aligner yield · precision (favorable, real HTR)** | **98.8% · 97.5%** → **GO** |
| B2 yield · precision by condition | div3% 98.5/96.7 · div6% 98.2/97.2 · omit15% 94.2/95.5 · div3%+omit15% 84.2/92.0 |
| **B2 false-mints of edition-omitted lines** | **0** (every omission condition) |
| B2 live pipeline | GWLB IIIF → seg **44 lines** → HTR → GPT-4o §70 extract (all run) |
| B2 verified §70 ↔ scan pair | `00068642` c0 = AA VI,4 N.109 (katalog) |
| **HTR CER (B1): measured vs claimed** | **7.95%** (CI 7.49–8.46) vs 8.33% → **GO** |
| HTR WER (B1) | 27.04% (CI 25.95–28.19) vs claimed 28.56% |
| Val lines · char-perfect | 1,878 · 464 (24.7%) |
| CER by policy (philiumm/lenient/strict) | 7.95% / 7.61% / 7.95% |
| **VLM vs HTR (150-line subsample) CER** | Kraken 8.19% · gpt-4o 45.87% · gpt-4.1 38.62% · gpt-4.1-mini 34.79% |
| VLM comparison API cost | **$0.49** (450 calls, usage-metered) |
| Unique works · page images | 2,225 · **236,795** |
| **`pages` rows populated** | **236,795** (static 159,162 · iiif 77,633) |
| Images cached (dev slice) | 80 · 126.3 MB · verify 80/80 OK |
| Mean page size · full-pull estimate | ~1.6 MB · **≈ 365 GB** |
| Katalog records scraped (sample) | 15,382 (12,384 GWLB-linked) |
| **Crosswalk: works matched** | **1,094 / 2,225 (49.2%)** from 6 queries |
| Crosswalk link→work resolution | 99.96% (5 unresolved of 12,389) |
| Katalog result cap (per query) | 5,000 rows (no pagination) |

Per-set crosswalk coverage (sample): Handschriften 401/756 (53.0%) ·
Briefwechsel 545/1,059 (51.5%) · Marginalien 146/396 (36.9%).

Legal registry (A0, unchanged): 42 entries; 32 free today. Licence registry
(L1, 2026-10-21): 31 third-party artifacts, 9 outputs; `leibniz legal licences`.

---

## Open questions

The full text of every question is in `status/open-questions.md`; numbers are permanent, and a new question takes the next free number, with its full text there and one line here.

| No. | Question | State |
| --- | --- | --- |
| 36 | R1: two things Part B decides before it measures (2026-11-17) | open |
| 35 | What the first releases publish beyond the lines (2026-11-18, REL1 Part A; the operator's before Part B's step 9) | open |
| 34 | "No NC input" and the training lines in the NC-derived deposit (2026-11-18, REL1 Part A; before the model is published) | open |
| 33 | The Edition's verdict convention and the licence of its corrected lines (2026-11-16) | restated 2026-11-17; (b) the licence settled 2026-11-16 |
| 32 | The narrow crops among the German lines (2026-10-28, K4; for K3b's segmentation measurement) | open |
| 31 | German pages that mix scripts, and print (2026-10-26, K4) | open |
| 30 | The Calculemus seam's open points (2026-10-21, G1) | open: (g) and (h) answered 2026-11-17, (i) and (j) the operator's |
| 29 | Licence asks open after L1 (2026-10-21) | open |
| 28 | Leibniz holdings outside the GWLB (2026-10-14, after a reader's request) | open: decisions (b) and (c) stand |
| 27 | The catalogue in the store is part of the Arbeitskatalog (2026-10-10, W5's staging look) | "closed on the code side" 2026-10-21 (A3b) |
| 26 | The twin rule's corpus-wide error is unmeasured (2026-10-10, W5) | open |
| 25 | Kalliope's terms (2026-10-10, W5) | open |
| 24 | The PHILIUMM model does not read Kurrent as noise (2026-10-09, K1) | "answered by Tasks 3 and 4" (K1) |
| 23 | The factory's Textart rule never fired (2026-10-09, K1) | open |
| 22 | The browse index wants two authorities (2026-10-06, W3) | open |
| 21 | Fold the metadata fields in the Meilisearch index (2026-10-02) | resolved |
| 20 | Multi-word queries on Meilisearch are not AND (2026-10-02) | resolved |
| 19 | Sheet-sides registered twice (2026-09-23) | resolved |
| 18 | (C2) Precision of the minted GT | restated 2026-10-07 (audited); added to 2026-10-20 (C2c) |
| 17 | (C2) Edge-of-passage scatter under unit costs | open |
| 16 | (C2) Ten §70 volumes have no free digital copy | open |
| 15 | (C1) Line-confidence source | resolved |
| 14 | (C1) Segmentation on Marginalien / drafts is unmeasured on real images | resolved |
| 13 | (C2) Real GT minting awaits three operator inputs | resolved |
| 12 | (B2) Edition-text extraction QA at scale | resolved |
| 11 | (B2) Draft strata need a higher threshold | resolved |
| 10 | (B2) Piece→canvas localization | resolved |
| 9 | LLM-on-Leibniz numbers pending a key | resolved |
| 8 | No per-line language labels in the PHILIUMM GT | open |
| 7 | B1 residual gap (0.38 pt) | open |
| 6 | (A0) §71 editio-princeps assumption; re-edition term restarts | open (for the lawyer memo) |
| 5 | Marginalien scope (from A1) | open |
| 4 | Shelfmark-secondary limits (A3) | open |
| 3 | Katalog full scrape — the §70 volumes are done; the rest is an operator job | open |
| 2 | `pages` population is partial | resolved |
| 1 | IIIF vs static delivery (A2) | resolved |
| 0 | Strategy review 2026-09-16 → `NOTES.md` | open (a standing pointer) |

---

## Divergences

The divergences recorded to 2026-11-18 are in `status/divergences-to-2026-11-18.md`, verbatim and frozen. From 2026-11-19 a session records its divergences in its own phase file under `status/`, in a "Divergences" section.

---

## Next

_Open items only, in order; each ends with the file whose "Hand-over" section carries the commands. The paragraphs of the old "Next" are in those files, verbatim._

1. **K3b, the next desktop session** (branch `k3b-own-hand`, as ARCH2's brief names it). Task 0: convert, score, the dry run, then the one write after a backup and the
   operator's go; then Tasks 1 and 2 → `status/2026-11-17-k3b-prep.md`. The order of its tasks → `status/2026-11-16-arrivals.md`; what K3 left it → `status/2026-10-21-k3.md`.
2. **REL1 Part B, the operator's desktop** (ten steps): Open questions 34 and 35 first, and after K3b's write if the verified lines are to be in the first version; then
   **Part C**, a cloud session once the DOIs exist → `status/2026-11-17-rel1.md`.
3. **R1 Part B** on the desktop, when no other torch process runs; Open question 36 first → `status/2026-11-17-r1.md` (the hand-over is in its Phase log).
4. **The Fraktur half of the print sheet** (the operator's 25 lines), then `leibniz layout print-trial cer` and `report`; M1 Tasks 1 to 4 are a later session
   → `status/2026-11-17-dq1.md`.
5. **G1b**: the operator's answer to Open question 30 (j), the rebuild, the check and the choice of pack, the copy to the box, then the game's own runbook
   → `status/2026-11-17-g1b.md`; the judgments import (P8) when the game's judgment pack comes back → `status/2026-10-21-g1.md`.
6. **The box's disk**: a volume before C4's index rebuild and before the next staging index → `status/2026-10-26-k4.md`.
7. **A3b**: the entry still marks the dry run again, the write and the serving copy ⏳, while commit `7cf8dc8` of 2026-10-22 carries the reports of "the import run of
   22 October": confirm with step 6's checks and close the entry; later the persons and places tables, the refresh with the next export → `status/2026-10-21-a3b.md`.
8. **Desktop chores**: C: at 25 GB free (`wsl --shutdown`, `Optimize-VHD`) and the `credential.helper` path in `~/.gitconfig` → `status/2026-11-17-dq1.md`;
   `leibniz align gt-report` when the store is next read → `status/2026-11-17-rel1.md`.
9. **K4's second language pass**, the next round → `status/2026-10-26-k4.md`. **LT1b** when wanted, and the rerun cadence → `status/2026-10-28-lt1.md`.
10. **C3 as amended** (`PROMPTS.md`), on the re-minted lines: its inputs and the files kept until it has read them → `status/2026-10-20-c2c.md`, `status/2026-10-20-k2.md`;
    every ablation with and without R1's decoder → `status/2026-11-17-r1.md`; then **C4**. The gate and the order of the C phases → `status/next-earlier.md`.
11. **After P1 Task 3**, for later sessions: the census again with each later PHILIUMM model, a flag in the viewer for the v1 lines inside figure or formula zones,
    a zones table with M1 Tasks 2–3 → `status/2026-11-17-dq1.md`.
12. **L1's lines for the operator**: the Nantes HMER code's address and licence, the Göttingen series' terms when their directors answer, PHILIUMM's code licence;
    and the owner's open decision on an NC channel for the later Reihe IV volumes and Reihe VIII → `status/2026-10-21-l1.md`.
13. **Letters without a recorded answer** (the operator's): to the research directors in Hanover and Münster, and the ask for the Edition's Transkribus pages
    → `status/2026-10-21-l1.md` (the note of 2026-10-14).
14. **To the Edition's Arbeitsstelle** (the operator's): the reply to the editor, three sentences → `status/2026-10-21-w6.md`; the credit wording (Open question 33 b)
    → `status/2026-11-17-rel1.md`; the Faszikel grouping (Open question 22 a) → `status/next-earlier.md`.
15. **To the PHILIUMM team** (the operator's): the three sentences on the census → `status/2026-11-17-dq1.md`; the second judging round (Open question 18)
    → `status/2026-10-20-c2c.md`; the sheet of 300 disagreements → `status/next-earlier.md`.
16. **Other mail** (the operator's): the report's tables to the colleague → `status/2026-10-28-lt1.md`; the three sentences to the print tools' author
    → `status/2026-11-17-dq1.md`; the 16 redirect-loop delivery URLs to the GWLB → `status/next-earlier.md`.
17. **Housekeeping**: the W5 prompt was never saved, it is in neither `PROMPTS.md` nor `PROMPTS-archive.md` → `status/2026-10-21-w6.md`.
18. **2027-01-01**: AA I,17 and IV,4 become free of §70 (`src/leibniz/legal.py`).

_Standing: the letter-pool set is reported on and never tuned on, and its text stays under `data/` → `status/2026-10-19-k2b.md`._
