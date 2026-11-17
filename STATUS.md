# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-11-17 (**ARCH1 — the archive: the Current state and Phase log entries dated before 2026-10-19 and the finished paragraphs of Next moved verbatim to `STATUS-archive.md`, the prompts already run to `PROMPTS-archive.md`; at the move STATUS.md 8,113 → 5,390 lines and PROMPTS.md 3,907 → 143; docs only, nothing deployed; the pull request and the merge the operator's, before any other session branches**); 2026-11-16, later (**the Edition's corrected lines may be released under CC BY 4.0, Open question 33 (b): the verified set goes to the open deposit with the Edition's credit; the sessions from here are laid out on the operator's plan page**); earlier the same day (**two arrivals recorded, no code, no data: the Leibniz-Edition's Arbeitsstelle returned K2's 200-line audit sheet on 6 November with every line judged and the correct text written out for 118 lines, to be converted and scored in K3b's Task 0; PHILIUMM published the v2 of its segmentation model on 3 November, CC BY-NC 4.0, and no better HTR model, so P1 Task 3 can run**; 2026-10-31: **K4 live — German on the site: the operator's switch of 30 and 31 October, the live index rebuilt in 4 h 59 m; 1,539,688 lines of k3-trocr on 24,078 pages shown, the language filter open**; 2026-10-30: **K4 — German on the site, built on the desktop on `k4-german-site`: the operator's choice of reader recorded verbatim ("I agree to go with TrOCR."; READER `k3-trocr`); the reading job 39 h over two launches; after the operator's go of the 30th the master store written once — the `page_lang` table, 236,210 rows under run 616, and READER's readings as one scoped run, 1,539,688 rows on 24,078 German pages under run 617 — and verified read-only; 92 browser checks on a fixture store; the serving copy on D: (18,314,969,088 bytes); the box commands, the checks with their expected answers and the live switch in order handed to the operator; nothing deployed, the branch pushed, not merged**; earlier the same day, **LT1 Part B — the page-level test run on the desktop: on the GWLB letters Gemini 4 Argon 24.2 %, Gemini 3.1 Pro 25.8 %, Claude Fable 5.1 26.4 %, k3-trocr 26.9 %, inside each other's intervals; on PHILIUMM's held-out pages the best page model 22.5 % against the kraken model's 7.95 %; 13.92 USD of API calls; the numbers in `reports/htr/page-llm.md`**; 2026-10-28: **LT1 — the page-level test of frontier vision models against the project's readers, Part A built in a cloud session on `claude/kind-tesla-xhk9ac`: `bench page-read` (whole pages, one a call, one prompt, temperature 0, reasoning at the floor, the cost logged and capped, resumable), `page-score` (PHILIUMM's 27 held-out pages by page CER with the kraken model beside, the letter pool through a page reader kind of K2b's metric, the line diff), `page-report`; the two page lists committed (34 calls on PHILIUMM, 100 pool pages of 34 letters); the model ids and settings pinned (gemini-3.1-pro-preview and gemini-4-argon at thinking_level low, claude-fable-5-1 at effort low — thinking cannot be off); the dry run's estimate under 15 USD a model; 1060 tests; Part B the operator's desktop**; 2026-10-26: **K3 — a Leibniz Kurrent model, done on the desktop on `k3-kurrent-model`: two models trained on K2's German mint and measured on the letter pool — k3-trocr 28.6 % CER, k3-kraken 30.6 %, against 37.0 % for the Bern model as it came; the choice for K4 open until the operator answers**; 2026-10-22: **A3b follow-up 2, after the operator's second dry run (settled on signatur 99.6 %, titel 99.9 %, textart and aa 100 %; datum 98.6 % with 346 "other", half the website's short second dates `(123)` for the export's `(00-01-23)`, now read as agreement in a column of their own, the stored value the export's; 48726 carried as 69490, the other eight unmatched, every ground-truth id in the export); 980 tests**; earlier the same day, **A3b follow-up, after the operator's dry run on the master store (datum 98.4 %, a STOP on nine renumbered ids, 16 hand changes): the second date's zero parts dropped as the website does, text the website's parser lost as HTML tags counted as agreement, a store id the export no longer carries mapped by Kat.-Nr. and shelfmark and the STOP kept for ground-truth references only, the names rendered through the persons table with their GND and KorrespDB ids (46 of 46 cells on the live records), the holdings page reworked — 'Where Leibniz's papers are held', a one-sentence intro, the works heading naming the store's state, the digitised copies hidden before the import, a line on Browse, one source line from the registry (export of 19 October 2026); 979 tests, 84 + 32 browser checks; on `claude/adoring-volta-eogav8`, the dry run again the operator's**; 2026-10-21: **A3b — the Arbeitskatalog import, built in a cloud session on fixtures cut from the Arbeitsstelle's export of 21 October: one `ritter.csv` row → the record the website parser produced, the column-to-key mapping read off 23 records fetched live from the catalogue and proved on the committed fixture (the five judged keys at 100 %, the hand rule unchanged), the whole catalogue into the store by `leibniz catalog import-access --write` after a dry run that prints the agreement table and stops if the ground truth or the crosswalk references a record the export lacks; the holding institution from the shelfmark (215 holdings over the 70,405 records, the GWLB's own collections 68.4 %), `reports/holdings.md`, `/holdings` and `/api/holdings`, the catalogue's links to digitised copies elsewhere and the edition's PDF per piece on the work page, the Ordnungsvermerk in the Faszikel index, 'the whole Arbeitskatalog, refreshed <date>' wording; 976 tests, 57 browser checks; on `claude/adoring-volta-eogav8`, the store steps the operator's**; earlier the same day, **G1 — the Calculemus seam, built in a cloud session on the fixture store: `leibniz pack fragments` (German A/B pairs, the stored v1 text against K2's Bern reading, gold from K2's reader-minted rows in the open deposit, a line refused unless its volume is §70-free), `leibniz pack check` (the contract of Calculemus SPECS §6.6 as two JSON schemas), `leibniz pack judgments` (the game's converged judgments as new 'corrected' lines, a dry run unless `--write`; the both-rejected lines as the Scriptorium queue); 948 tests; merged as #51; the real pack built and checked on the desktop the same day: 2,000 rows from 79,453 eligible lines, gold 56 (2.8 %; the cap allows 500: on the 271 selected lines with an open reader-minted row, one reading equals the minted text on 43, and it is never the v1 text) — the owner chooses before the copy to the box**; earlier the same day, **L1 — the licence registry, built in a cloud session: one entry per third-party artifact with its licence as obtained and as published (the PHILIUMM models CC BY-NC 4.0 on Zenodo since 2026-10-15, the dataset CC BY 4.0, the Potsdam channel and the Arbeitskatalog as stated in writing on 2026-10-12, the records re-read 2026-10-21), the outputs table (the owner's scheme of 13 October), `leibniz legal licences`; the ground truth exports as two deposits by channel (CC BY 4.0 / CC BY-NC 4.0); About, llms.txt, the cards and the attribution line read their licence lines from the registry; SPECS §2 and §7 amended; the lawyer-memo list in the release checklist; 880 tests; on `claude/relaxed-dijkstra-uus9rz`, the pull request the operator's**; earlier the same day, **W6 — two reader's items from the Leibniz-Edition (13 October), built in a cloud session on the fixture store: a search link into the Leibniz-Katalog by shelfmark on every work page, whether or not the store holds the work's records (the catalogue's spelling checked live: Arabic numerals, `LBr` without the library's period, `Leibn. Marg.`; 2,184 of the 2,225 works get a link), and the scope sentence, EN and DE, on About, in llms.txt and the README; 859 tests; on `claude/busy-dirac-n30a43`, the pull request the operator's**; 2026-10-20: **C2c — the re-mint under W5's rules, done on the desktop: 297,424 minted lines deleted and 315,797 minted in their place (+6.2 %; 710 `LBrF` records now localizable, neighbours on a shared folio no longer erased, nothing filed under a volume without text); the hyphen flag 7,822 → 848, 8,523 lines keep the scribe's mark; Leibniz's own hand 14.9 % under the strict rule (25.7 % under the loose one, the difference the rule's); 1,472 held-out pages; the second judging sheet drawn; on `c2c-remint`, the pull request the operator's**; earlier the same day, **K2b — the letter-pool test set, done on the desktop: 134 letters of the GWLB pool frozen as the honest German test set (67 in Leibniz's hand, 67 of the correspondents'; 18,815 lines), nothing filtered; the first German error rates — v1 46.6 % CER, philiumm 52.9 %, trocr-kurrent-xvi-xvii 37.0 %, trocr-hanse-xvi 35.6 %, trocr-hanse-xvii 38.9 %; the correspondents' hands 23–46 %, Leibniz's own 47–59 %; on `k2b-letterpool`, the pull request the operator's**; 2026-10-14: **the Edition's replies of 12 and 13 October recorded, no code: the Potsdam series' texts CC BY-NC 4.0 in writing, an Arbeitskatalog export offered, reader feedback on catalogue links and scope, the holdings outside the GWLB surveyed — Open questions 27 and 28, the L1 note under Next**; 2026-10-11: **W5 live: merged as #42 and deployed on 2026-10-10, the index rebuilt and the letters fetched overnight — 196,439 distinct scans among 236,795 page records, 9,846,450 lines once each, 40,297 scans registered under more than one label (39,442 spreads split, 855 folded), 15,425 letters**; 2026-10-10: **W5 — the review's fixes and six features readers ask for, in code on `claude/amazing-mayer-y6i9g0`: the GT factory fixed before the re-mint (record-owned lines, folio sides, one volume per piece, the en dash, "LBrF", one hand rule, the audit's own numbers); the site's search (every word by default, exactness first, folded metadata, no empty pages past 10,000), safe 404s, the right folios for "Text of this piece", source links that open, per-page GWLB links, named letter convolutes, IIIF fixes; scans registered twice folded and spreads split at the fold; citable lines; citation lookup; letters by correspondent, date and place; a Faszikel index of the catalogue's pieces; links out**; 2026-10-09: **K1 — the Kurrent track, done on the desktop: the aligner's noise tolerance measured (yield holds to ≈ 55 / 48 / 38 / 29 % CER by stratum), the German census run on the store (2,173 German pieces, 401,394 recognised lines, minted at 10.2 % against 19.0 % on Latin and French), the bootstrap readers ranked on Dresden (trocr-kurrent-xvi-xvii 7.4 %, trocr-hanse-xvi 8.9 %, trocr-hanse-xvii 10.9 %, philiumm 29.5 %, mccatmus 51.7 % CER), the pilot on Leibniz's German run (German yield at the gate philiumm 12.5 %, trocr-kurrent-xvi-xvii 20.2 %, trocr-hanse-xvii 20.6 %, trocr-hanse-xvi 22.5 %, v1 16.4 %); gate for K2: GO with trocr-kurrent-xvi-xvii**; 2026-10-08: **S1, the staging site: built, installed and verified the same day; `https://staging.leibnizlegible.com` runs the branch behind a password against the live store and index**; earlier the same day, **C2b, the census run on the store: a quarter of the minted ground truth is in Leibniz's own hand, 7,822 lines lose their hyphen to the mint, the addition proxy marks 83 % of lines and is useless; 2026-10-07, C2b: the PHILIUMM team's 200-line audit scored and read** — corpus-weighted precision 72.3 % as written, 92.2 % with boundary slips counted usable, one misaligned line in 185 scored; the patterns behind the verdicts named and measured, the dropped line-end hyphen fixed in the aligner, the reach census built for the operator's run, the C3 prompt amended; 2026-10-06, later the same day, a fault found live after W3's deploy and its fix: the viewer's ES modules are served as one versioned set, so a deploy can no longer pair a new `app.js` with cached old modules; W3: a browse page — the Nachlass by shelfmark family, section and convolute at `/browse`, `GET /api/works`, a breadcrumb from every work page back to its section; 2026-10-02 — W2: search reads "quoted phrases" and -exclusions, and the hint under the box says so and what exact matching misses; earlier the same day, W1: the line-overlay toggle fixed, plain-text export per folio and per work, content-hashed viewer assets; earlier: 2026-09-27 — room for Calculemus on the host, flagged off; 2026-09-23 — discoverability, About page, duplicate sheet-sides; 2026-09-16 — **Phase D built on v1 — search index, API, IIIF v3 + annotations, viewer, release exports; reports + project statement published on Zenodo; strategy review recorded in `NOTES.md` and the C3 prompt amended. C2 stands as closed on the mint with the precision gate deferred to C3. Later the same day: the deployment kit (`deploy/`), public-traffic hardening of the app, `LICENSE` + issue form for the repository going public.**)._

---

## Current state

**2026-11-17: ARCH1 — the archive: the finished phases moved out of STATUS.md
and PROMPTS.md, verbatim; a cloud session, alone, on the branch it was given,
`claude/blissful-mccarthy-ktud6m`, from main at `f2ce06c` (#62); docs only: no
code, no data, nothing deployed; the pull request and the merge are the
operator's, before any other session branches.** `STATUS-archive.md` now holds
the Current state entries dated before 2026-10-19 (the entry of 2026-10-14
back to July, with the retained subsections from "Prior gate (retained)" to
"A3 in numbers"), the 27 Phase log entries from W5 (2026-10-10) back to A0
(2026-07-28), and the twelve paragraphs of Next whose every item is done or
superseded; `PROMPTS-archive.md` holds the original prompts of A0 to C2 and D1
to D3 and the sixteen follow-up prompts from W3 to K4. STATUS.md keeps one
pointer line in Current state, one per moved Phase log entry and one in Next;
Key numbers, Open questions and Divergences are whole, and every entry of
2026-10-19 or later stays where it was. PROMPTS.md keeps "How to use this
file" (two sentences on the archive files added), COMMON CONTEXT, C3 with its
two amendments, C4, E1 and the "Follow-up phases (2026-10)" heading with a
table of the sixteen archived run prompts; new prompts are appended below the
table, this one the first. **The counts (`wc -l`, before and after the move):
STATUS.md 8,113 → 5,390 lines (612,651 → 424,587 bytes) with 2,771 in
STATUS-archive.md; PROMPTS.md 3,907 → 143 lines (260,339 → 13,577 bytes) with
3,807 in PROMPTS-archive.md.** The proof, by a script of the session's (not
committed) that reads the old files from `origin/main` and the four files as
committed: every old line is in the working file or in its archive (none
missing), the content lines stand in their old order in both files and none
stands twice; **STATUS.md's 8,113 old lines = 5,361 kept + 2,752 archived**,
with 29 new lines in STATUS.md (the pointer lines) and 19 in the archive (the
title, the two-line head, three section headings, rules and blank lines);
**PROMPTS.md's 3,907 = 119 kept + 3,788 archived**, with 24 new lines in
PROMPTS.md (the two sentences, two pointer lines, the table's 18 lines, the
two lines around it, one blank line) and 19 in the archive. No test or module
reads either file (no line in `tests` names them; the 25 lines in `src` are
docstrings, comments and message strings). ruff clean and **1,071 passed, 3
skipped** before and after (the three need numpy, which the three extras do
not bring). With this entry, the Phase log entry, the Divergences entry and
the line in Next, STATUS.md stands at 5,594 lines, and PROMPTS.md with this
prompt appended at 333. In Next stay every paragraph of 2026-10-19 or later
and four older blocks with an open item each (the L1 note of 14 October, P1,
W3, the A0–C2 block). The ARCH1 entry in the Phase log has the detail.

**2026-11-16: two arrivals, recorded (no code, no data).** (a) **The K2 audit
sheet is judged.** The Leibniz-Edition's Arbeitsstelle (Potsdam) returned the
200 lines of `data/kurrent/k2-audit.html` on 6 November as a Numbers table with
the sheet's four columns and one of its own, "transcription (complete and
correct)". Its convention differs from the sheet's: "correct" only where the
minted text was completely right; where anything was wrong, no verdict and the
correct text of the whole line in the extra column; "boundary" for a slip at an
edge; "note" for comments only. Counted from the file: 76 correct, 21 boundary
(20 with a transcription), 98 with a transcription and no verdict, 1 wrong (its
note: the crop and the text do not match), 3 unreadable (two ask for a larger
excerpt), 1 blank; 118 corrected transcriptions, 9 to 74 characters, median 43;
one note says a line of AA IV,1 N.008 (record 59196, German by the census at
0.97) is French. Read strictly, 76 of the 196 judged lines are right as written
(39 %; 49 % with boundary), under a stricter standard than the PHILIUMM audit's,
so the figure is not comparable with C2b's 72.3 % until the C2b pattern code has
measured the folded distance between the minted text and the Edition's text,
which K3b's Task 0 does after converting the table to the C2 CSV shape (a
transcription without a verdict counts as "wrong"; the transcriptions go to a
corrections file). The verdicts and the transcriptions stay under
`data/kurrent/` (the Edition's own text; its credit and licence asked on 16 November; the licence settled the same evening, CC BY 4.0 for the open deposit, Open question 33 b); the 76 confirmed and 118 corrected lines are K3b's first verified
lines, half in Leibniz's own hand by the sheet's design. (b) **PHILIUMM's v2
segmentation model is published** (3 November; the HTR engineer's mail of the
same day): `DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2`,
RF-DETR-Seg Nano on 1,060 pages (1,002 train, 40 validation, 18 test), training
resolution 1,272 px (v1: 720), eight SegmOnto classes (MainZone, MarginTextZone,
NumberingZone, DigitizationArtefactZone, GraphicZone-figure, MathsRegion-complex,
-inline, -strikethrough), validation segm mAP 0.47 (MainZone 0.91,
MarginTextZone 0.62, the formula classes 0.08–0.19), two checkpoints, a
threshold of 0.4 recommended, `cc-by-nc-4.0` on the card, read 16 November; its
dataset `DenisaBumba/layout-leibniz-dataset-v2` public under CC BY 4.0 since 12
November (392 unique pages: 334 train, 40 validation, 18 test, the 1,060
counting augmented copies; PAGE XML and the originals, most named by shelfmark
and folio), so the training pages can be listed and the annotations are open;
her further attempts produced no better HTR model, so C3 starts from the CC BY
base as amended. P1 Task 3 can run, its census sample drawn outside her
training pages and the held-out pages.
The notes for both sessions are on the operator's plan page (K3b, P1 Task 3);
this entry is the record. Open question 33 carries the two open points.

**2026-10-31: K4 live — German on the site; the operator's switch of 30
and 31 October, the box commands of the K4 entry run in order with one
change of route.** The serving copy reached the box in 1 h 49 m
(18,314,969,088 bytes, the digest matching, integrity ok, the five row
counts the master's), staging ran the branch on it and the first round of
checks answered as expected. The staging index build then filled the root
disk (679 MB free of 75 GB: two store copies and one index leave no room for
a second index) and was stopped and dropped; the route became the switch
first: #58 merged, the code updated on the box, the staging copy renamed
over the live file with the app stopped for seconds (31 GB free after), the
live index rebuilt beside the old one 12:36–17:35 (4 h 59 m) and swapped in,
the app restarted, staging back on main at `35cec06`. The live checks:
About names k3-trocr with the stamps model CC BY 4.0, base MIT, readings CC
BY 4.0; llms.txt three mentions, 28.6 %, no fixture string; `/api/stats`
readers de `k3-trocr@runs-615-epoch-5`, **lines shown 12,947,584
(FoNDUE-GD_v2_ft_Leibniz 11,407,896 · k3-trocr@runs-615-epoch-5
1,539,688)**, pages by language de 30,797 · fr 62,330 · la 110,167 · mixed
13,801 · unknown 19,115, the index built 2026-10-31T17:34:46Z; the page
`DE-611-HS-971383:0035` under run 617 with 203 READER lines; the search
`Herr` with the German filter **9,933 pages, all de**. A Hetzner volume for
the box goes before C4's rebuild (Next). The K4 entry in the Phase log has
the switch's detail.

**2026-10-30: K4 — German on the site; the branch `k4-german-site` from
main at #55; Tasks 0–4 done; the reading job finished 2026-10-30 00:49
(k3-trocr over 1,539,721 lines on 24,078 German pages, under the 6 GB
scope with the guard; two launches, one guard kill at 19:09 on the 28th,
the card 22 MiB over the 5,900 line, no leak; 91 ms a line, 39 h in all; 0
skipped, 33 empty); the dated backup copy of the store on D: verified
(01:26, the same SHA-256 on both sides); after the operator's go of the
30th the master store written once, 08:40–08:51: the `page_lang` table
(236,210 rows under run 616, stage enrich) and READER's readings as one
scoped run (1,539,688 rows on 24,078 pages under run 617, stage recognize,
model `k3-trocr@runs-615-epoch-5`, scope `de`), the store 19,354,243,072
bytes after (+2,210,672,640), WAL empty, verified read-only; Checkpoint D;
the browser checks on the fixture store 92 of 92 (Checkpoint E; one
phone-width fault of About's found and fixed on the way); Task 6: the
serving copy on D: (18,314,969,088 bytes; the `VACUUM INTO` 08:57–09:38 at
the share's 4–7 MiB/s, its integrity check over the share stopped after
79 minutes at under a megabyte a second and moved to the box, its SHA-256
`3ff238b22a89…` in 58 min 32 s),
the box commands, the curl checks with their expected answers and the live
switch in order in the K4 entry; the branch pushed, the compare URL
printed; nothing deployed, nothing merged.** The operator's
choice of reader, verbatim: **"I agree to go with TrOCR."** READER is
`k3-trocr` (`data/models/k3/trocr/best`, read with `--kv-cache`; on the
letter pool 28.6 % CER against v1's 46.6 %, in Leibniz's own hand 36.7 %
against 53.7 %, so Task 4's gate is met on K3's numbers); its readings carry
CC BY 4.0 like v1's (the registry's `model-k3-trocr`: the Bern base MIT,
K2's lines open-bucket). Prerequisites verified: K3 merged (main at
`c0b1a45`, #55; `k3-trocr` and `k3-kraken` in the CANDIDATES table; the
checkpoint on D: behind the `data/models/k3` symlink, `model.safetensors`
1,335,747,032 bytes with its `generation_config.json`;
`reports/kurrent/k3-eval.md`; runs rows 614 and 615 in the store); K2b's
test set present (`reports/kurrent/letterpool-testset.csv`,
`data/kurrent/letterpool/testset.jsonl`, `letterpool-eval.md`). Baseline:
ruff clean in both environments; pytest **1,026 passed, 1 skipped** in
`.venv-k1` (44.2 s) and **1,016 passed, 1 skipped** in `.venv-w3` (41.3 s;
the letter-pool metric's tests need numpy, which that environment lacks).
The desktop: GTX 1660 Ti, 1,188 MiB of 6,144 MiB held by Xwayland; RAM
9,943 MiB with 9,050 available, swap 8,192 MiB; **C: 33 GB free** (the
budget for every write under `/`), D: 368 GB free; the store
17,143,570,432 bytes, WAL empty. The plan, what was found before the go and
the open points are in the K4 entry of the Phase log.

**2026-10-30: LT1 Part B — the page-level test run on the operator's
desktop; the numbers in `reports/htr/page-llm.md` (with `.json` and
`page-llm.scores.json`), committed on `lt1-results` and carried with this
entry to the operator's pull request; 13.92 USD of API calls; no store
write, nothing deployed.** Three frontier models read whole pages — Gemini 4
Argon, Gemini 3.1 Pro, Claude Fable 5.1; one prompt, temperature 0 where the
API takes it, reasoning at the floor the API allows (none has an off), a
long side of 2,000 px — on two sets. **The GWLB letter pool, 34 letters and
98 pages, K2b's metric, failed pages charged:** Argon 24.2 % (17.3–31.5),
Gemini 3.1 Pro 25.8 %, Claude 26.4 %, k3-trocr 26.9 % (21.9–31.9), k3-kraken
29.5 %, the Bern model as it came 35.0 %, v1 43.9 %; on the 30 letters every
page model read in full, Argon 19.5 %, Gemini 3.1 Pro 21.7 %, Claude 24.4 %,
k3-trocr 25.7 %; by hand, the correspondents' Argon 13.2 % and Gemini 13.8 %
against k3-trocr's 19.0 %, Leibniz's own 33.3 to 35.8 % against 33.4 %:
parity on his hand, the page models ahead on the cleaner hands. **PHILIUMM's
27 held-out pages (34 calls), Latin and French, page CER against the
dataset's PAGE XML:** Claude 22.5 % (18.0–27.5), Gemini 3.1 Pro 27.2 %
(24.5 % with its one failed page left out), Argon 33.6 % (30.7 %; per-page
median 17.0 %, max 229 %: runaways); the PHILIUMM kraken model reads the same
1,878 lines at **7.95 %** on the dataset's own crops (B1), about three times
better than the best page model. That kraken row is quoted from B1, not
measured on this harness: `bench page-lines` cuts with the audit's padded
polygon mask, and the model, trained on kraken's baseline extraction, read
those crops at 26.29 % (25.13–27.48) — a measure of how much a dedicated
model depends on the line extraction it was trained with, and LT1b's first
item (Next). **The diff on the pool's 1,664 aligner-accepted lines:**
k3-trocr exactly right on 363 (22 %), the page models on 190 to 272; both
wrong on 1,126 to 1,183; the page models' line counts 2.1 to 2.3 times the
reference's because they read every line on the page while the reference
holds the accepted ones, so their "invented" column is not hallucination.
**Failures, after one retry each:** Claude none; Gemini 3.1 Pro one runaway
on PHILIUMM's pages and four pool pages empty or runaway; Argon one empty
page in each set. **Cost, logged:** Argon 1.06 USD for 132 pages (0.8 cents
a page: about 190 USD for the 24,078 German pages, about 1,900 for the
corpus), Gemini 3.1 Pro 1.43, Claude 11.43. **The reading:** parity on
Leibniz's German correspondence, a three-to-one loss on Latin and French, and
in both cases the frontier models' errors differ from the fine-tuned models'
— the second-reader case, not the replacement case; the operator's decision
of 29 October stands: the project's own readers, with the page models as
second readers where the diff earns it. The run also tripped one defect:
`page-score` reads every JSONL in the readings folder as page readings and
failed on the kraken line dump the runbook had put there (`--models` named
the three models as the workaround; LT1b fixes it). The LT1 entry in the
Phase log has the detail.

**2026-10-28: LT1 — the page-level test of frontier vision models against
the project's readers, Part A built in a cloud session on fixtures; the branch
`claude/kind-tesla-xhk9ac`, the pull request the operator's; Part B (the API
runs, the scoring, the report's numbers) the operator's desktop, the runbook
under Next; no API call was made here, no store write, nothing deployed.** A
colleague holds that the current frontier models read whole pages far better
than the project's readers; B1's only LLM numbers used line crops. The fair
protocol is now code: `leibniz bench page-read` sends whole pages, one page a
call (a half at a time where the list names a column), one prompt for every
model (Humphries' recipe: every line in reading order, one output line per
manuscript line, character by character, nothing else), temperature 0 where
the API takes it, reasoning off or at the floor the API allows, `max_tokens`
4,000, the image downscaled to a long side of 2,000 px, every call's usage and
estimated cost logged, a refusal, an empty answer or a runaway recorded and
retried once, the run resumable by page and stopped at a cost cap. The
engines (`htr/engines.py`) now return a structured reply (text, stop reason,
usage): Claude gets `output_config.effort` (thinking is always on and cannot be
disabled on the Claude 5 models; *low* is the floor), no `temperature` (the
current models reject it) and a usage/pricing table of its own; Gemini gets
`thinking_level` (3.x Pro and 4 Argon take low | medium | high and have no
off) and the rows `gemini-3.1-pro-preview` (2.00 / 12.00 USD per 1M) and
`gemini-4-argon` (2.00 / 10.00 through 2026-11-30); OpenAI gets
`reasoning_effort` with a step-down chain (none → minimal → low) on a 400. The
scoring (`htr/pagescore.py`): PHILIUMM's held-out pages with the dataset's own
PAGE XML as the page reference (its lines in document order — the parquet
carries text and image only, so the page is rebuilt from the XML the Hub
publishes beside each scan), page CER pooled over pages with a bootstrap,
failed pages charged as 100 % and left out, the kraken model's page CER from
its line readings of the same lines (`bench page-lines` cuts them for `bench
run`); the letter pool through a reader kind *page* for `letterpool_eval`
(`PageReadings`: the page text attached to the page, `machine_text`
concatenates the pages in order, the infix metric, pooling and aggregation
unchanged), both ways for failed pages, beside v1, the Bern model and the K3
models on the same letters; the colleague's line diff (both readers' lines
aligned to the same reference lines: exactly one right, both wrong, invented,
dropped, the length ratio). `bench page-report` renders
`reports/htr/page-llm.md` + `.json` with the protocol, the settings per model,
the sets, the tables, the cost, the refusals both ways, the diff and the two
caveats (small sets; the pool's references are checked letter transcriptions,
not a random sample of the German pages). The two page lists are committed:
`reports/htr/page-list-philiumm.csv` — the whole `val` split, **27 pages as 34
calls** (7 openings read as left and right; 16 calls on pages the store also
holds), not the 50 the prompt names: the held-out split has 27 pages, and the
dataset has no `test` split (`val` is it) — and `page-list-pool.csv`, **100
pool pages of 34 letters drawn seeded (20261028), whole letters at a time: 50
pages in Leibniz's hand, 50 in the correspondents', 19 and 15 letters, 18 of
the selection half and 16 of the test half**. The dry run's estimates for the
134 calls a model, at the pricing tables and an assumed 1,500 output tokens a
page (thinking included) with image sizes assumed (1,333 × 2,000 px, none on
disk here): claude-fable-5-1 **14.80 USD**, gemini-3.1-pro-preview **2.85 USD**,
gemini-4-argon **2.45 USD** (gpt-5.5, if wanted, 2.21 USD) — under the 20 USD
cap a model the prompt sets; the real run records the APIs' own usage. Tests
1016 → **1060**, ruff clean; the LT1 entry in the Phase log has the detail
and the pre-flight's facts; Part B's runbook is under Next.

**2026-10-21/26: K3 — a Leibniz Kurrent model, done on the desktop; the
branch `k3-kurrent-model`, the pull request the operator's; nothing
deployed; the choice for K4 open until the operator answers.** Two models
fine-tuned on K2's German mint (55,596 training lines, 3,133 page-disjoint
validation lines frozen before any training, every line tagged by hand and
reader, the screen for misplaced lines not triggered) and measured where
nothing was tuned: **on the GWLB letter pool (K2b's frozen set, nothing
filtered) k3-trocr reads at 28.6 % CER (24.6–32.5) and k3-kraken at 30.6 %
(26.5–34.5), against 37.0 % for the Bern model as it came and 46.6 % for
the stored v1 text; Leibniz's own hand 36.7 % and 39.7 % (49.2 % before),
the correspondents' 19.4 % and 20.3 %**; on the validation set 11.84 % and
15.56 %; on Dresden 11.9 % and 13.2 %; 152 and 52 ms a line on this card.
The trainings: kraken 37 epochs in 44.5 h (stopped on the operator's
approval), TrOCR six epochs in 27 h — after a crash, two stops and three
guard kills along the way, every one the session's own doing (two jobs at
once on the 9.9 GB host) and each recorded under Divergences; the artefacts
live on D: behind the `data/models/k3` symlink. The rule the report proposes
answers **kraken** (within the margin on the selection half, ten times
faster); the operator decides. PP-OCRv6, the ablation and a rental are
K3b's. The K3 entry in the Phase log has the detail; `reports/kurrent/k3-eval.md`
the numbers.

**2026-10-22, later: A3b follow-up 2, after the operator's second dry run;
the dry run is to run once more; nothing written to the store, nothing
deployed.** The second run on the master store settled signatur (99.6 %),
titel (99.9 %), textart and aa (100 %); datum read 98.6 % with 346 "other"
rows of two kinds — genuine corrections in the master (16706 and 16707:
store `1698`, export `1700-01-14 (00-01-04)`), which stay "other", and the
website's copy printing a short second date as a bare number with its
leading zeros gone (17346: store `1700-02-02 (123)`, export `1700-02-02
(00-01-23)`). The second kind is now a rule of the comparison only
(`website_short_second_date`): the website's `(123)` agrees with the export's
`(00-01-23)` when the digits match after the dashes and leading zeros are
removed, counted in a column of its own, "Website short date", among the
agreeing classes; the stored value stays the export's. The rest of the run
read right: 48726 carried as 69490 by Kat.-Nr. and shelfmark, the other
eight ids without a match (their crosswalk links dropped by the rebuild),
every ground-truth id in the export, the write free to proceed once the
third dry run says settled. Tests 979 → **980**, ruff clean.

**2026-10-22: A3b follow-up, built in the same cloud session on the same
branch after the operator's dry run on the master store; the dry run is to
run again; nothing written to the store, nothing deployed.** The operator's
run of `import-access --dry-run` on the 24,916 records found `datum` at
98.4 % (397 "other" rows where the website shortens the second date:
`1693-06-29 (93-06)` against the export's `(93-06-00)`), a STOP on nine
record ids the export no longer carries (1738, 48726, 58654, 62088, 69210,
69212, 69213, 69214, 69215 — all still on the public website; 48726 is
Kat.-Nr. 18752 there, which the export carries as record 69490: the Access
master renumbers or merges a few records between TELOTA's half-yearly
imports), values the website's parser had lost as HTML tags (`<Trig>onometria`,
`<bey dem> Bergambt`, `<prs. …>` in a Textart, the format code before a bare
`°`), and the hand rule changing on 16 of 24,907 records (five lose
"Leibniz's own hand"). The rules now: the second date drops its `-00` parts
as the first date does (192 rows of the export carry such a `JJMMTT`;
genuine edits such as `1698` against `1700-01-14 (00-01-04)` stay "other");
a store value equal to the export's with every `<…>` segment removed, or a
bare `°` where the export names the format code, counts as agreement in a
column of its own, "Website lost markup", the export's value kept and the
report saying how many rows it restores per key; a store id the export lacks
is mapped to the export's record with the same Kat.-Nr. and shelfmark (else
the same Kat.-Nr. where unique, else the row whose `Identisch_mit` or
`mergenr` names it — `mergenr` is an internal number that never equals an
id in this export), compared under that id and listed with its new id in the
report, the crosswalk rebuilt under the new id; the STOP stays only for an
id `gt_lines` references, a crosswalk-only reference is reported as remapped
or dropped; the hand rule's changes are listed in full and no longer block
the write (the export's fuller Textart decides; K3's training set was built
on the old Textart — the sixteen, with before and after, are in the
operator's `reports/import-access-dryrun.md`, which this session cannot see:
the operator pastes them into the A3b entry). The names: joined through
`pers_norm.csv` (`korr` → `gnd`, `idhannover`) the export reproduces the
website's cells, link markers and all, on **46 of 46 cells of the 23 live
records**, so the record carries the website's form and, as new keys,
`absender_gnd`, `absender_korrespdb`, `adressat_gnd`, `adressat_korrespdb`;
over the whole export 94.3 % of the name occurrences have a persons-table
row (the rest show bare, as on the website). The holdings page: "Where
Leibniz's papers are held" (DE "Wo Leibniz' Papiere aufbewahrt werden")
everywhere, a one-sentence intro, the "How this was read" section replaced
by one footnote line under the table, the digitised-copies block hidden
while the store carries no import run, the works heading naming the store's
state ("before the catalogue import" / "the whole Arbeitskatalog, refreshed
<date>"), one line at the top of Browse (EN, DE, and in the server-rendered
index), and the credit in one place — a source line from
`legal.arbeitskatalog_credit()` ("Source: Arbeitskatalog der Leibniz-Edition,
Leibniz-Edition Potsdam I (BBAW), CC BY 4.0, export of 19 October 2026",
both linked) on the holdings page and above the work page's records, the
old attribution line gone; About's catalogue block, `llms.txt` and the
README say the records come from the Arbeitsstelle's export, not the
website. The export's date is 19 October (provided on the 21st): the
registry's `ARBEITSKATALOG_EXPORT_DATE`, the fixtures and the hand-over say
so, and the operator's dry run takes `--export-date 2026-10-19`. Tests 976 →
**979**, ruff clean; the browser checks on the fixture store: **84 of 84**
after the import (EN, DE, 390 px; axe-core 0 violations) and **32 of 32**
before it (the partial wording, the works heading, no digitised-copies
block). The follow-up's detail is the first block of the A3b entry in the
Phase log; the dry run's command and the staging checks are under Next.

**2026-10-21: A3b — the Arbeitskatalog import, built in a cloud session on
fixtures cut from the Arbeitsstelle's export; the branch
`claude/adoring-volta-eogav8`, the pull request the operator's; the store
steps handed over under Next; nothing written to the store, nothing
deployed.** The Leibniz-Edition Potsdam's Access database, exported with
mdbtools as CSV (`arbeitskatalog-csv.zip`, 19 tables; `ritter.csv` **70,405
records** in 45 columns as the csv module reads it), maps row by row to the
record the website parser produced (`catalog/arbeitskatalog.py`), so every
reader of `katalog_records` keeps working unchanged. Which Access column
feeds which key was read off the website, not guessed: 23 records fetched
live from the catalogue's extended search on 2026-10-21 (24 polite GETs at
1.5 s with the project's User-Agent; one record newer than the website's
copy answered nothing) and parsed with the website parser gave the rules —
`Kat.-Nr.` = `KA KAT_NR/Zusatz`; `Datum` from `JJJJMMTT` with a `00` month or
day dropped and the other calendar's `JJMMTT` in parentheses; `Akademie
Ausgabe` = `REIHE | bd.nnn / UNr Aufl. …` with the piece zero-filled to three
digits (so the stored `aa_refs` keep their `044`), the series alone where
the cell names no piece; `Format und Umfang` from `FORMAT` (2 Folio … 24
Vigesimoquart) and `UMFANG` rounded to two decimals; `Signatur` = `SIGN` with
its spaces folded; `Textart` = `UEBERLFG`; the names bare (the website
appends its link texts, which every reader strips); the Wortlaut with its
markup removed. On the committed fixture (the 21 of those records that are
also in the 30-row cut) the five judged keys agree on **100 %**: textart,
signatur and titel 21 of 21 exact, datum 19 exact and 2 where the website
prints nothing, aa 20 exact and 1 where the website's copy names the series
alone; incipit, katnr, sigle, ort and wortlaut 21 of 21; **the hand rule gives
the same answer on 21 of 21**; what differs is explained — the website's `°`
for a 32° format, three printings the two copies edited apart, the PPN link
the website parser had no rule for. New keys: `holding` (a token table over
the shelfmark's prefix, `catalog/holdings.py`: **215 holdings** over the
export, the GWLB's own collections **48,167 records, 68.4 %**, no shelfmark
7,509, the Landesarchiv Hannover 4,218, a printed witness only 1,700),
`url_ms`, `ordnungsvermerk` with its normalised name and the OV tables'
title, `ordnungsnummer`, `identisch_mit`, `last_change`, `aa_pdf` (the
edition's PDF per piece from `pdf_url`: 25,012 of the 35,133 rows with a
piece number), the GWLB link by PPN as well as by id (416 + 39,257).
`leibniz catalog import-access --csv-dir … --export-date … [--write]` (a dry
run by default): the agreement table over every record the store holds, the
check that every record id `gt_lines` and the crosswalk reference exists in
the export (it stops and prints the ids otherwise), and with `--write` the
replacement of `katalog_records` by record id, the crosswalk rebuilt from
scratch (gwlb_link first, shelfmark second) and the report of records per
work, works without a record and the records whose `URL_Ms` points outside
the GWLB; idempotent; a run in `runs` carries the export's date. `leibniz
catalog holdings` renders `reports/holdings.md` (committed from the export:
records by holding, digitised copies by domain — **49,341 records link one,
39,673 to the GWLB, 4,189 to the Landesarchiv's Arcinsys** — the works
section follows the operator's import). On the site: `/holdings` (EN, DE)
and `GET /api/holdings` from the same data, linked from About's scope
paragraph; the work page and the record API carry `url_ms` where it points
outside the GWLB and `aa_pdf` where the channel is open (the registry: the
GWLB repository and the Potsdam Arbeitsstellen, CC BY-NC 4.0; the Münster
files sit behind a permission page, no link), and the Ordnungsvermerk, which
the Faszikel index (`/api/contents`) searches and shows; "part of the
Arbeitskatalog" becomes "the whole Arbeitskatalog, refreshed <date>" on
About, the browse page and the work page as soon as the store carries an
import run (`katalog` in `/api/stats`), and in `llms.txt` and the README
now. **Open question 27 closed** on the code side, its Monadologie numbers
corrected: 39739, 39743 and 39744 are the pieces' Kat.-Nr., the records are
55406, 55407 and 54786 (LH 4, 1, 1a Bl. 1-6, LH 4, 1, 1b Bl. 1-10 and Bl.
1/1-16/1); Open question 28's survey superseded by the export's table. Tests
948 → **976**, ruff clean; **57 browser checks** on the fixture store (EN, DE,
390 px; axe-core 0 violations in nine states; no console errors). **Not done
here:** the dry run and the write on the master store (the operator's, under
Next, in order), `reports/crosswalk.md` (needs the store), the persons and
places tables (recorded in the Phase log, left for a later step). The A3b
entry in the Phase log has the detail.

**2026-10-21: G1 — the Calculemus seam, built in a cloud session on the
fixture store and merged as #51; the real pack built and checked on the
desktop the same day; nothing deployed, nothing yet copied to the box.**
Calculemus played on a synthetic pack because this seam was never built
(NOTES.md B); it now exists in `src/leibniz/pack/`. (a) `leibniz pack
fragments` reads the store read-only, K2's readings and K1's German pieces
and writes a fragment pack under `packs/` (gitignored): one row per line of
the German pieces whose stored v1 text (the row `latest_lines` shows) and
Bern reading are non-empty and differ after whitespace normalisation, the
longer 10–50 characters, on a page the image mirror serves, each line once
where the library registered a scan twice (W5's twin rule); the two
candidates (`htr_best`, `model_alt`, each with its confidence) in an order
drawn per line under the seed; the box the audit's crop (`line_geometry`,
`crop_box`, 12 px); stratum, hand and language the piece's; equal numbers
per stratum, Leibniz's own hand (the strict rule) at least at its share of
the eligible lines; `license_bucket` 'open' on every row, and a line whose
piece's volume is not §70-free on `--today` refused. Gold: a selected line
with a row K2's reader minted in the open deposit (`legal.deposit_for`:
never the Potsdam or GWLB-repository channel) — the candidate equal to the
minted text under the aligner's fold is the truth, neither equal makes the
row both-wrong, both equal makes it no gold; at most `--gold-rate` 0.25 of
the rows, at most `--bad-gold-share` 0.25 of the gold both-wrong. (b)
`leibniz pack check` validates a pack against the contract — Calculemus
SPECS §6.6 mirrored as `src/leibniz/pack/fragment_pack.schema.json` and
`judgment_pack.schema.json`, enforced by a validator of the module's own (no
new dependency) — and the rules a schema cannot say (one of truth and
both-wrong on a gold row, two distinct candidates, canonical line ids, each
line once). (c) `leibniz pack judgments --in FILE [--write]` imports the
game's converged judgments as new `corrected` lines under one `crowd` run
(`crowd_ab_v1@<the game's sha>`, the posterior as confidence, the judgment
row verbatim as `source`), never updating or deleting a machine row,
idempotent on the line and `decided_at`; the both-rejected lines go to
`reports/scriptorium-queue.md`, a section per judgment pack. SPECS §11
records the seam. Tests 880 → 948, ruff clean. **The real pack** (the
operator's run, 16:15 EDT, 390 s, the store read-only; `pack check` OK): the
2,148 German records' 4,734 pages carry 305,602 lines, **112,513 of them
(36.8 %) another registration's** (W5's twins), 90,727 outside 10–50
characters, none refused under §70 — **79,453 eligible, 2,000 selected**
(fair copy 55, all there are; light 649, heavy 648, scrap 648; Leibniz's own
hand 131, 6.5 %, its share of the pool). **Gold 56 (2.8 %; the cap allows
500): truth 42, both-wrong 14** — the supply is the limit. Of the 2,000, 553
lines have a row K2's reader minted: 282 in the NC deposit (withheld) and 271
in the open, and on those 271 one reading equals the minted text under the
fold on **43 (15.9 %): the Bern reading on 42, the v1 text on none**, both on
1; neither on 228 (84.1 %). v1 is never the truth because K2 aligned the
edition on the Bern reading and v1 reads German at 46.6 % CER (K2b), so every
truth-gold row is a line the Bern model reads exactly. That 15.9 % is a
first, biased indication of the number NOTES B asks for before an A/B design
(it wants about 70 % on heavy revision): the owner's choices before the copy
to the box are Open question 30 (g)–(i). The judgments import is P8's. The
G1 entry in the Phase log has the detail.

**2026-10-21: L1 — the licence registry, built in a cloud session on the
branch it was given, `claude/relaxed-dijkstra-uus9rz`; the pull request the
operator's; nothing deployed.** `src/leibniz/legal.py` carries, beside the
§70 volume registry, one entry per third-party artifact (31): name, source,
version, the licence as obtained with its date, the licence as currently
published where it changed with the date seen, the bucket consequence
(SPECS §7.3), what this project built from it, and for the edition's
channels the D3 deposit their lines go to; and the table of this project's
own outputs (9) with the licence each carries and why. The public records
were re-read on 2026-10-21: the PHILIUMM HTR and segmentation models read
**CC BY-NC 4.0 on Zenodo since 2026-10-15** (obtained under CC BY 4.0 on
2026-07-29), the PHILIUMM dataset CC BY 4.0 unchanged, the Bern TrOCR
models MIT, the two fgho models still without a licence, the Dresden 1673
record CC BY 4.0 in its field (the package's README CC BY-NC-SA 4.0: the
conflict stands) with two sibling Dresden records (the 1673 TEI, the 1665
diary; CC BY 4.0, not used), HME-Leibniz CC BY-NC 4.0, Gallicorpora+'s
record CC BY 4.0. The decisions recorded (Task 0, verbatim in the L1
entry): PHILIUMM's models CC BY-NC 4.0 from 15 October, their dataset CC
BY 4.0, their code's licence asked; the owner's scheme — code Apache-2.0,
the transcriptions and the open ground truth CC BY 4.0, the NC-derived
ground truth a second deposit under CC BY-NC 4.0, models fine-tuned from
PHILIUMM's checkpoint CC BY-NC 4.0, K3's candidates without NC input CC BY
4.0; the Potsdam head's statement of 12 October (Series IV, V and VIII
under CC BY-NC 4.0; the Arbeitskatalog CC BY 4.0; the Göttingen series
asked). **The ground truth now exports as two deposits by channel**:
`leibniz-gt` (CC BY 4.0: `channel ia` and rows without a channel) and
`leibniz-gt-nc` (CC BY-NC 4.0: the Potsdam Reihe IV PDFs and the GWLB
repository's PDFs; a joined channel counts as the more restricted one; the
letter pool in neither); each card has a Licence section quoting the
registry and counting its lines by channel. About (EN, DE) gains Ground
truth, Models and Letters under Licensing, and its Transcriptions paragraph,
`llms.txt`, the attribution line of the API and the manifests say the
transcriptions are machine output of a model obtained under CC BY 4.0;
`leibniz legal licences | outputs | volumes` print the tables. SPECS §2 (D3
two deposits, D4 CC BY-NC 4.0) and §7 (the dated amendment) say the same;
`reports/release-checklist.md` §6 is the lawyer-memo list (irrevocability
for copies already obtained, model output under a weights licence,
ShareAlike, NC terms on a PDF and §70-free text — if not, the NC deposit
opens up —, the Potsdam lines, §71, GPL/AGPL tools beside Apache-2.0 code).
Tests 859 → 880, ruff clean. **Not done here:** staging (the hand-over under
Next); the GitHub-hosted licences the prompt asked to read (dfine_kraken)
and the Nantes code's address, which this session could not reach (its
GitHub access is scoped to this repository: an operator line under Next);
the recorded-not-decided question of an NC channel now (Next). The L1 entry
in the Phase log has the detail.

**2026-10-21: W6 — two reader's items from the Leibniz-Edition (13 October),
built in a cloud session on the fixture store; the branch
`claude/busy-dirac-n30a43`, the pull request the operator's; nothing
deployed.** (a) Every work page links the Leibniz-Katalog's own search by the
work's shelfmark (`sign_ol=`, a substring match on the catalogue's Signatur),
whether or not the store holds the work's records: `1665058609` (Leibn. Marg.
196) has none and now links
https://leibniz-katalog.bbaw.de/de/extended-search?sign_ol=Leibn.+Marg.+196,
which answers its one record. The catalogue's spelling was checked live, one
search per family and a few more to settle its forms: Arabic numerals
throughout (`LH 4, 6, 18` answers the two records on the work's folios),
**`LBr` without the period the library writes (`LBr 464` answers eleven
records; `LBr. 464` and the prompt's `LBr. 164` none)**, `Leibn. Marg.`, the
F series run together (`LBrF 1`), `, Stück 1` and `175:1` as the library has
them; `links.katalog_spelling` turns the library's `LH IV, 6, 18` /
`LBr. 464` / `ZEN Leibn. Marg. 40` into the catalogue's. `/api/works/{id}`
gains `katalog_search_urls` (one entry per distinct shelfmark, stored order:
`shelfmark`, `query`, `url`) and an OpenAPI summary; the server-rendered page
carries the link after "IIIF manifest" and, where no record is held, a
"Catalogue records" heading with one sentence (the site holds part of the
Arbeitskatalog so far; search it for the shelfmark); the viewer lists it
after the manifests and in the catalogue section, which says the same
instead of the bare "none", EN and DE. Over the live works list of
2026-10-21, **2,184 of the 2,225 works get a link** (24 carry no shelfmark,
17 only a foreign one: `Ms`, `Nm-A`, `P-A` …). (b) A scope paragraph on About
after "What this is", EN and DE, without numbers — the site covers the scans
the GWLB has published of its Leibniz collections, not all of Leibniz's
papers; much is not yet digitised at the GWLB and elsewhere, other
institutions hold manuscripts, the Niedersächsisches Landesarchiv Hannover
among them; the Arbeitskatalog records them all and the site holds part of
its records so far — and the same in one line under "Scope" in `llms.txt`
and the README. Tests 856 → 859, ruff clean; 51 browser checks in headless
Chromium on the fixture store (EN, DE, 390 px, axe-core 0 violations in nine
states, no console errors). **The records themselves and the holdings page
wait for the Arbeitskatalog export** (Open question 27). The W6 entry in the
Phase log has the detail; Next has the staging checks and the three
sentences for the editor.

**2026-10-20/21: K2 — German ground truth, done on the desktop; the
branch `k2-german-gt`, the pull request the operator's; nothing deployed.** The Bern Kurrent reader
(`trocr-kurrent-xvi-xvii`, K1's gate) over every recognised line of the
census's German pieces, then the factory over those readings, as the plan
page's K2 prompt (with its amendment of 10 October) and the preamble of 19
October say. Task 0 done (the pre-flight; the go came after it); Task 1 in
progress (the code built and tested; the sweep and the Dresden check done:
fp32 with the decoder's cache on at batch 16 reads every Dresden line as
the checkpoint's defaults do at a third of the time; **the reading job ran
from 19:36 EDT to 03:07 the next morning** (7 h 26 min after a restart on an
engine fix at 19:40): 310,831 lines read, none skipped; Checkpoint A). Task
2 done (the dry run, 1 h 05 min: **the Bern reading lifts the German yield at
the same gate from 10.8 % to 16.9 %, Leibniz's own hand 9.5 → 12.5 %; the
rule gives 1,178 pieces to it and leaves 402; the German records' mint
42,278 → 68,769 lines expected**; Checkpoint B). Task 3 done (the backup
copy of 20 October verified byte-identical past the header; the go; the
write in 7.8 s, run 609: **`gt_lines` 315,797 → 333,680 rows, 50,720 of them
the reader's; the German records 42,278 → 60,163 lines, Leibniz's own hand
1,888 → 2,612** — the dry run's expectation counted lines two pieces share
twice, the store keeps each once; gt-report and audit-reach count the reader
rows as decided, 50,720 and none skipped; Checkpoint C). Finish done: the
200-line audit sheet half from Leibniz's own hand, half from the others;
`k2-write.md`; 866 tests. **K3 starts after the sheet is judged, or after the
operator decides to go without.** The K2 entry in the Phase log has the
detail.

**2026-10-20: C2c — the re-mint, done on the desktop; the branch
`c2c-remint` waits for the operator's pull request, nothing deployed.** The
one re-mint of the ground truth under W5's rules, before C3 and before K2
writes, as the plan page's C2c prompt and the preamble of 19 October say.
The store was written in two steps only, each after a backup and the
operator's go: `gt-reset` (the ownership column filled, then **297,424
minted lines deleted**, none kept) and the six shards, which minted
**315,797 open-bucket lines** (fair 10,234 · light 100,085 · heavy 203,749
· scrap 1,729) from 6,130 catalogue records on 17,669 pages in 66–71
minutes, every skip structural (no `database is locked`, so no `--resume`).
The edition cache was rebuilt first: the same 10,029 texts, byte for byte,
now with the printed piece each came from, which moved 20 records to the
volume their text came from and leaves nothing filed under II,1, I,2, I,4
or I,5. The +18,373 lines are accounted for: 9,965 come from 710 `LBrF`
records the old shelfmark parser could not place, 10,260 lie on pages the
old code placed too (neighbours on a shared folio no longer erase each
other's lines; a record aligns under its own volume), 634 on newly placed
pages; 2,486 old lines are gone, 1,758 of them from pages the folio-side
fix no longer gives their record. **The hyphen flag fell from 7,822 (2.6 %)
to 848 (0.3 %)**, and 8,523 minted lines now end in the scribe's mark;
brackets 4,811 and math 255 move with the count. **Leibniz's own hand
under W5's strict rule: 14.9 %** of the lines with a Textart (the loose
rule said 25.7 %; the strict rule gives 15.1 % on the old mint too, so the
fall is the rule's). The A VI,4 cross-check: 62,164 paired lines, agree
9,506, disagree 774, and **1,472 held-out pages** as before. The second
judging sheet for the PHILIUMM team is drawn (`--seed 1`, 200 lines,
`reports/gt-audit/round2/`). Store backup before the re-mint on D:, 30.7
minutes. The C2c entry in the Phase log has the detail.

**2026-10-20: K2b — the letter-pool test set, done on the desktop (Checkpoint
C); the branch `k2b-letterpool` waits for the operator's pull request, nothing
deployed.** The honest German test set from the GWLB's checked transcriptions
of the correspondence of 1708–1716 (CC BY-NC 4.0, nc bucket: internal
evaluation only — the texts stay under `data/`, the reports carry numbers and
letter numbers), placed on the store's pages through the C2 resolver, frozen,
and measured, as the plan page's K2b prompt and the preamble of 19 October
say. The nine checked volumes (version 1 each) parse into **2,533 letters**
(835 German), **695 of them German and placeable**; **565 placed** on the
store (72 no work, 10 no canvas, 48 shared leaves), no page among K2's German
pieces or the PHILIUMM held-out pages; the set drawn seeded and stratified by
siglum and year: **134 letters — all 67 in Leibniz's hand that placed and 67
of the correspondents' — on 386 pages with 18,815 recognised lines and 325,624
reference characters, split once into a selection half and a test half of 67
letters each** (`reports/kurrent/letterpool-testset.csv`). The metric is the
letter's reference against every recognised line on its pages, an infix
alignment, nothing filtered. **The first measured German error rates (CER,
`philiumm` policy, 95 % bootstrap over letters): the stored v1 text 46.6 %
(43.3–49.5 %), philiumm 52.9 %, trocr-kurrent-xvi-xvii 37.0 % (32.5–41.0 %),
trocr-hanse-xvi 35.6 % (31.2–39.6 %) (evaluate only), trocr-hanse-xvii 38.9 %
(evaluate only); on the test half 48.2 / 54.6 / 39.2 / 38.0 / 41.2 %; the
correspondents' hands 38.5 / 45.5 / 23.2 / 22.8 / 26.4 %, Leibniz's own 53.7 /
59.3 / 49.2 / 46.7 / 49.8 %. The lines the factory's aligner would accept
(15–29 % of them) read at 15–32 %, 18 to 21 points under the unfiltered
rates** (`reports/kurrent/letterpool-eval.md`). K1's gate holds:
trocr-kurrent-xvi-xvii (MIT) is K2's reader; K3 reports its rate on this set
and never tunes on it. The GPU read 18,445 distinct lines four times in 4 h 31
min; the store was opened read-only; ruff clean, 841 tests. The K2b entry in
the Phase log has the detail.

_Entries before 2026-10-19 (the entry of 2026-10-14 back to July, and the retained subsections from "Prior gate (retained)" to "A3 in numbers") → STATUS-archive.md, "Current state (archived)"._

---

## Phase log

### REL1 — the first releases (2026-11-17) ✅ Task 0 · ✅ Task 1 (Checkpoint A) · ⏳ Task 2 · ⏳ Task 3 · ⏳ Task 4 · ⏳ Part B (the operator's desktop) · ⏳ Part C

- **Setting and pre-flight (Task 0; recorded, no go waited for).** Part A, a
  cloud session on the branch it was given, `claude/clever-gates-56b0a4`, from
  main at `9ae24de` (#63, ARCH1 merged: the archive files are in force);
  `git fetch origin main && git merge origin/main` already up to date; no
  store in the checkout (`data/README.md` only), so everything here runs on
  fixtures; `.venv-cloud` made with the web, gt and release extras
  (`UV_PROJECT_ENVIRONMENT=.venv-cloud uv sync --extra web --extra gt --extra
  release`; Python 3.13); no token of any kind. Baseline: ruff clean,
  **1,071 passed, 3 skipped** (`python -m pytest`; the three need numpy).
  The fixture store of the pre-flight is K4's (`tools/browser-checks/k4-seed.py`:
  the test fixtures with the German rows and one scoped k3-trocr run);
  `leibniz release export --format parquet` and `--format jsonl` wrote the
  four datasets (works 4, pages 8, crosswalk 1, katalog_records 1; lines 19;
  gt 7; gt-nc 1) and `leibniz release checklist` printed the checklist.
  **Confirmed:** (a) `iter_transcriptions` applies K4's precedence — the
  fixture page `00069377:0001` exports the scoped row on the line the scoped
  run wrote (`model` `k3-trocr@runs-615-epoch-5`, `run_id` 8) and the first
  model's rows on its other four lines; the column is `run_id` (with
  `run_at`), not `run` as the prompt writes it; (b) the ground truth splits
  by channel as L1 decided (open: `ia` and rows without a channel; nc:
  `potsdam`, `gwlb`, joined channels; the letter pool in neither); (c) the
  inventory tables are `works`, `pages`, `crosswalk`, `katalog_records`, the
  last the store's catalogue records as they are — on the fixture one
  website-shaped record; on the master, by STATUS.md, 24,916 records read
  from the catalogue's website unless A3b's write has run since (its entry
  still reads ⏳), and then 70,405 from the Arbeitsstelle's export; the card
  asks the store which (`catalog_refreshed`) and words the credit
  accordingly. **Found, and not foreseen by the prompt:** (1) *the committed
  audit summary was a test's.* `tests/test_align_audit.py` ran `align
  audit-score` without `--summary`, so every test run wrote an 8-line
  stand-in audit over `reports/gt-audit/audit-summary.json`; the file was
  first committed in that state (2026-10-10, `b725def`) and has read "8
  rows, 95.0 %, passes the gate" on main since. Both ground-truth cards
  quote that file, so an export from main said "Hand audit of 8 of 8 sampled
  lines … precision 95.0 % as written, which passes the 95 % gate", and the
  committed `reports/gt-factory.md` (the operator's run of 21 October) says
  the same with "Audited 2" and 50 to 100 % per stratum. (2) *The export
  opened the master with `db.init_db`*: a writing connection that runs the
  schema DDL and the migrations; Part B's rule is a read-only store. (3)
  *The export held a million line rows in memory per file* (`_chunks` built
  each chunk as a list) and sorted the whole `lines` table (`ORDER BY
  page_id, line_seq, rank` with no index on the pair): gigabytes of Python
  objects and of temporary file on a 9.9 GB host. (4) *The cards said
  nothing true about the German reader's licence, the language pass or the
  inventory*, and stated one model in the attribution line. The three
  answers of the operator's note of 16 November: the model's public name
  **`leibniz-kurrent-trocr`**; D1 inside the transcriptions record **yes**;
  the Hugging Face namespace was left as `[NAMESPACE]`, so proposed:
  **`leibniz-legible`** (`https://huggingface.co/leibniz-legible` answered
  404 on 2026-11-17: no public profile of that name; the operator creates the
  organisation or names another). The plan as carried out is the tasks below.
- **Task 1, the cards true to the store — CHECKPOINT A.** *The audit
  summary restored and fenced:* `leibniz align audit-score
  reports/gt-audit/gt-audit-verdicts-philiumm.csv` with the C2 mint's stratum
  counts as weights (9,913 · 96,175 · 190,162 · 1,174, Key numbers) wrote the
  real summary back — **200 lines, 199 judged, 185 scored, corpus-weighted
  precision 72.3 %, 92.2 % with boundary slips usable, FAIL at 95 %** — and
  its stratum table is the committed `reports/gt-audit.md`'s line for line;
  the four test invocations now pass `--summary` into the test's own folder,
  and a test pins the committed summary to the audit; the two wrong passages
  of `reports/gt-factory.md` (the Audited and Est. precision columns, the
  sentence under them) were re-rendered by the report's own code from the
  restored summary (50 · 45 · 48 · 42 scored; 84.0 · 86.7 · 64.6 · 57.1 %)
  and nothing else in that file touched; the operator's next `align
  gt-report` on the store regenerates the whole. *The export*
  (`release/export.py`): the store opened read-only by the CLI
  (`audit_reach.open_readonly`; a missing store is an error, never created);
  the lines read page by page along `ix_lines_page` (`CROSS JOIN` pins the
  order, a test reads the query plan: no temporary B-tree) with the current
  row of each line chosen in Python under the same rank `(precedence, run
  id)`; chunks streamed to the writers, never held; a re-export clears an
  older run's extra chunk files. `MANIFEST.json` (version 2) now carries
  everything a card states as a number: `counts` (the lines by model, by
  run, by language, by status, by collection, the pages with lines — tallied
  as the rows are written; a deposit's lines by channel, stratum and reader,
  and the verified ones), `corpus` (works, pages by status, pages by
  language from `page_lang`, the reading runs with their scope, the
  catalogue records and the export they were refreshed from, `gt_lines`),
  `audit` (the scored summary) and `deposit_census`. **D2 with D1 inside
  it:** the `transcriptions` folder holds `lines-NNNN` and the four
  inventory tables under one manifest and one card; `inventory` stays
  exportable on its own (the repository's copy; not a record). *The cards*
  (`release/cards.py`, `release/measured.py`, `release/state.py`): every
  card opens with the Hugging Face front matter (license, language la/fr/de,
  pretty_name, size_categories from the main table's rows, task_categories
  image-to-text, tags, one config per table) above the Markdown that is the
  Zenodo README; a table of what the record holds with each table's own
  licence line (lines CC BY 4.0; works, pages, crosswalk CC0 1.0; the
  catalogue records CC BY 4.0 with `arbeitskatalog_credit` where the store
  holds the export, and "the records read from the catalogue's website, a
  part of the catalogue" where it does not). The transcriptions card names
  both models per line (`model`, `run_id`, `run_at`; the lines of each model
  and of each scoped run, from the manifest), the German reader with its
  three stamps from `legal.site_readers()` (model CC BY 4.0, base MIT,
  readings CC BY 4.0), the rule a page read twice follows, the language pass
  with its threshold, precision and recall (about three quarters of the
  German pages by the census's measure; a missed page keeps the first
  model's text), the Marginalien left to the first model, K3's numbers with
  what each was measured on and LT1's table beside them. Both ground-truth
  cards have an Audit section: the first audit's sentence from the summary,
  with its judge (the PHILIUMM team, 2026-10-07), the mint it was measured
  on and the plain statement that the re-mint in the deposit has not been
  judged again; K2's sheet with its judge (the Leibniz-Edition's
  Arbeitsstelle, Potsdam, returned 2026-11-06), its stricter convention and
  the counts of the entry of 2026-11-16 (76 · 21 · 98 · 1 · 3 · 1; 118
  corrected), the precision "scored in K3b" until
  `reports/kurrent/k2-audit.md` is committed and by pointing at that report
  after; the verified subset counted from the export (rows whose `source`
  carries `verified leibniz-edition`, of them the corrected ones in `channel
  edition-k2-audit`) and credited from the registry's entry once main has
  it, and until the store holds such rows the open card says the subset
  follows in the next version. Main does not carry K3b-prep's code or the
  registry entry yet; nothing here depends on the order of the merges. The
  anti-contamination note stands in every card and every Zenodo description,
  with a second sentence for a reader that is a training pipeline. **A
  card's numbers have three sources and no fourth:** the registry
  (licences), the manifest (counts), a committed report (measured figures:
  `k3-eval.json`, `page-llm.json`, `k4-reading.json`, read at render time; a
  missing report is named and nothing quoted; B1's 7.95 % stays a constant
  pinned to `reports/philiumm-repro.md` by a test). *The DOI mechanism:*
  `RELEASE.json` at the release root holds the reserved DOIs, the Hub
  namespace and the creators; `leibniz release cards --out ROOT [--doi
  record=DOI …] [--hf-namespace NS] [--creator "Family, Given|ORCID"]`
  re-renders every card and deposit file from the manifests alone, each card
  with its own DOI and its siblings'. Tests 1,071 → **1,090** at this
  checkpoint, ruff clean.

### ARCH1 — the archive (2026-11-17) ✅ Task 0 · ✅ Task 1 · ✅ Task 2 · ✅ Task 3 · ⏳ the operator's pull request and merge

- **Setting and pre-flight (Task 0).** A cloud session, alone, on the branch
  it was given, `claude/blissful-mccarthy-ktud6m`, from main at `f2ce06c`
  (#62); `git fetch origin main && git merge origin/main` already up to date;
  no `data/inventory.sqlite`, so a cloud checkout. `.venv-cloud` made with `uv
  sync --extra web --extra gt --extra release` (uv 0.11.32; Python 3.13.18,
  uv's default here). Baseline: `ruff check` clean, `ruff format --check` 296
  files already formatted, **1,071 passed, 3 skipped**
  (`test_align_letterpool_eval`, `test_htr_pagereport` and
  `test_htr_pagescore` need numpy, which these extras do not bring). The files
  as found (`wc -l`, `wc -c`): STATUS.md 8,113 lines, 612,651 bytes;
  PROMPTS.md 3,907 lines, 260,339 bytes. Read first, as the prompt says:
  PROMPTS.md's "How to use this file" and COMMON CONTEXT, STATUS.md's headings
  and the first lines of its Current state entries, then the kept Current
  state entries and the whole of Next, which the judgement on Next needs. The
  pre-flight recorded, the session proceeded (the preamble's item 6 and the
  cloud batch note of 17 November).
- **Task 1 — STATUS-archive.md (commit `df97d6e`).** By the old file's line
  numbers: *Current state*, lines 603–1,248 moved (the entry of 2026-10-14
  back to the undated entries of July, and the eight headings of retained
  subsections: "Prior gate (retained)" twice, "Phase B1 in numbers", "What was
  built (B1)", "Delivery-model correction", "What was built (A2 + A3)", "A2 in
  numbers", "A3 in numbers"), one pointer line in their place; the entries
  from 2026-11-16 back to K2b's of 2026-10-20 stay. *Phase log*, lines
  4,382–6,285 moved (27 entries, W5 of 2026-10-10 back to A0 of 2026-07-28), a
  pointer line for each with its heading's title and date; K4 back to K2b
  stay. *Next*, lines 7,843–7,993, 8,019–8,050 and 8,072–8,089 moved, one
  pointer line at the first emptied place. Key numbers, Open questions and
  Divergences untouched. The cut was made by a script that asserts the text at
  every boundary and that every moved dated entry is before 2026-10-19 and
  every kept one is not.
- **The judgement on Next, paragraph by paragraph.** Every paragraph dated
  2026-10-19 or later stays, as the entries of those days do: the kept entries
  and the open prompts say "under Next" of them (LT1's Part B runbook of 28
  October has been run and stays for that reason and for LT1b's reruns). Of
  the sixteen older blocks, **twelve moved**: W5 of 10 October (its own
  heading says steps 1 to 6 are done); K1 of 9 October (merged as #41; K2,
  which it feeds, is done); the Kurrent path proposed on 9 October and the
  operator's choice of the letter-pool route the same day (K2, K2b, K3 and K4
  have all run; the audit by a reader of Kurrent it leaves open came back on 6
  November); the final merge of 8 October (#40, live); W4's staging look (its
  steps ticked, merged and live); S1 (installed and verified; its standing
  staging line is superseded by the final-merge paragraph and by every later
  staging line, and the rule never to send a staging link stands in
  `deploy/README.md` §14); C2b of 7 October (items 1 to 3 ticked; item 4, the
  second judging round, restated in C2c's paragraph of 20 October, which
  stays); the W3 fix (merged as #39, live, every later staging check reads its
  `/static/m/` addresses); W2 and W1 (live, checked 6 October); Phase D
  deployable of 16 September (live since 21 September with the search
  criterion measured; its release-export item is carried by C2c's paragraph
  and by REL1). **Four stay, each with an open item:** the L1 note of 14
  October (the letters to the research directors in Hanover and Münster and
  the ask for the Edition's Transkribus pages have no recorded answer, and
  L1's paragraph of 21 October points to it); P1 of 8 October (the sheet of
  300 disagreements to offer the PHILIUMM team has no recorded outcome; its
  Task 3 is carried by the paragraph of 16 November); W3 of 6 October (the
  question to the Edition about the grouping is Open question 22 (a)); the
  A0–C2 block at the end with its closing line (C3 has not run; the report of
  the 16 redirect-loop URLs to the GWLB has no recorded outcome).
- **Task 2 — PROMPTS-archive.md (commit `8dcdfa2`).** By the old file's line
  numbers: lines 60–169 (the prompts of A0, A1, A2, A3, B1, B2, C1, C2),
  212–241 (D1, D2, D3) and 256–3,907 (the sixteen follow-up prompts: W3, C2b,
  P1, S1, W4, K1, K2b, C2c, K2, W6, L1, G1, A3b, K3, LT1, K4) moved under two
  section headings, "Original phase prompts (archived)" and "Follow-up phases
  (2026-10) (archived)". PROMPTS.md keeps "How to use this file" with one new
  paragraph of two sentences (where the run prompts and the old entries are
  and that a prompt naming one means the archived text; that nothing is
  appended to the archive files), COMMON CONTEXT, a pointer line where A0 to
  C2 stood, C3 with the amendments of 16 September and 7 October, C4, a
  pointer line where D1 to D3 stood, E1, and the "Follow-up phases (2026-10)"
  heading with its sentence, the table (phase, date run, the heading in the
  archive; the dates are the headings' own) and the line "New prompts are
  appended below this line, verbatim, as before." P1's prompt is archived with
  the others though its Task 3 is still to run; the plan page carries that
  session's note.
- **Task 3 — the proof.** A script of the session's (not committed) reads the
  old files from `origin/main` and the four files as they stand, knowing
  nothing of the cut. (A) As a multiset of lines, every old line is in the
  working file or in its archive: 0 missing in STATUS, 0 in PROMPTS; no old
  line other than a blank line or a `---` rule stands more often than before.
  (B) On the content lines (every line but a blank line and a rule) the old
  file is exactly an interleaving of the two new files with their added lines
  left out, so nothing is reordered, dropped or copied: STATUS 7,871 content
  lines = 5,249 kept + 2,622 archived; PROMPTS 3,525 = 79 + 3,446. (C) Over
  all lines, kept being the most old lines that still stand in the working
  file in their old order (difflib's matching blocks, equal to an exact
  longest-common-subsequence count): **STATUS.md 8,113 = 5,361 kept + 2,752
  archived; STATUS.md 5,390 = 5,361 + 29 new; STATUS-archive.md 2,771 =
  2,752 + 19 new. PROMPTS.md 3,907 = 119 kept + 3,788 archived; PROMPTS.md
  143 = 119 + 24 new; PROMPTS-archive.md 3,807 = 3,788 + 19 new.** The new lines,
  printed in full by the script: in STATUS 29 pointer lines, the archive's
  title, two head lines and three section headings, 3 rules and 10 blank
  lines; in PROMPTS 2 pointer lines, 18 table lines, the archive's title, two
  head lines and two section headings, the paragraph of two sentences, the two
  lines around the table, 3 rules and 12 blank lines. Blank lines and rules
  are interchangeable in this count: one blank line of Next stands in the
  archive between two moved runs rather than after the third, and the cut's
  own ranges move 3,792 lines of PROMPTS.md where the proof counts 3,788, four
  blank lines and rules being counted as kept where one still stands in the
  old place. `wc -l` after the move: 5,390 STATUS.md, 2,771 STATUS-archive.md,
  143 PROMPTS.md, 3,807 PROMPTS-archive.md. The script ran again on the files
  with this entry and the prompt in them; the hand-over has its counts.
- **No reader of either file in the code.** `grep -rn 'STATUS.md\|PROMPTS.md'
  tests src`: no line in `tests`; 25 lines in `src`, each a docstring, a
  comment or a message string, none opening the file. One of them now names a
  section that has moved: `src/leibniz/web/static/README.md` line 155 says
  "see STATUS.md, "Delivery-model correction"", which is in STATUS-archive.md
  under "Current state (archived)"; left as it is (this phase changes no file
  under `src`), the preamble's clause 8 covers it. The other files that name
  the two (README.md, SPECS.md, NOTES.md, `deploy/README.md`, the reports, the
  issue template) name the file as a whole or a section that stays
  (Divergences, Open questions, the C3 amendment). ruff clean, **1,071 passed,
  3 skipped** after the move as before it.
- **Found on the way, not changed.** (a) In this environment `uv run --no-sync
  pytest` stops at collection on `tests/test_enrich_pagelang.py` and
  `tests/test_pipeline_import_readings.py` (`from tests.conftest import …`
  with no `tests/__init__.py`: the repository root is not on the path); `uv
  run --no-sync python -m pytest` collects and passes them, and is how the
  counts above were made. A one-line `pythonpath = ["."]` under
  `[tool.pytest.ini_options]` would settle it; a code session's. (b) The "Last
  updated" line at the head of STATUS.md was 12,634 bytes before this session
  and grows with every one; the prompt names no place for it, so it was
  extended as every session extends it. On the operator's word a later session
  can move all but its last few items to the archive. (c) W6's housekeeping
  note still holds: the W5 prompt was never appended to PROMPTS.md, so it is
  in neither prompts file.
- **Hand-over.** Three commits on `claude/blissful-mccarthy-ktud6m`: the
  STATUS move, the PROMPTS move, this record with the prompt. Compare:
  https://github.com/marchofhares/LeibnizLegible/compare/main...claude/blissful-mccarthy-ktud6m?expand=1
  — the operator opens and merges the pull request, and no other session
  branches before that (both files are the ones every session appends to).
  From the merge on the preamble's clause 8 holds. Nothing under `data/`,
  nothing deployed, no file under `src`, `tests`, `deploy` or `reports`
  changed.

### K4 — German on the site (2026-10-26/30) ✅ Task 0 · ✅ Task 1 (Checkpoint A) · ✅ Task 2 (Checkpoint B) · ✅ Task 3 pilot (Checkpoint C) · ✅ the operator's go (2026-10-28) · ✅ the reading job (2026-10-28 09:50 – 2026-10-30 00:49, two launches) · ✅ Task 4 (Checkpoint D: the store written 2026-10-30 08:40–08:51) · ✅ Task 5 (Checkpoint E: 92 browser checks) · ✅ Task 6 (the serving copy on D:; the box commands, the checks and the live switch handed to the operator) · ✅ live (the operator's switch, 2026-10-31)

- **The live switch (2026-10-30/31, the operator's).** The transfer 1 h 49 m
  at 2.65 MB/s over the share; on the box the digest
  `3ff238b22a89e8dde77d7f965b47045785b0d37740bf25eae0f2c1496da8f782`,
  integrity ok, journal mode delete, works 2,225 · pages 236,795 · lines
  15,061,271 · gt_lines 333,680 · runs 617; staging on `k4-german-site` at
  `f166628`; round one: every expected answer (the `models` key is absent
  from the old index's stats rather than the old single-model row the
  runbook expected). The staging index build (`staging.sh --index`, 15 GB
  free at the start, the live index 15 GB) ran the disk to 679 MB free and
  was stopped (`systemctl stop leibniz-index-staging`) and dropped
  (`--drop-index`); the route: #58 merged, the §9 update (main d3391c2 →
  35cec06), the live app stopped, the staging copy renamed over the live
  file, the stale -wal/-shm removed, the app started, staging.env back on
  the live path, 31 GB free; the live rebuild as a transient unit
  `leibniz-index` 12:36–17:35 (4 h 59 m; 55 min CPU), the old index gone
  with the swap (42 GB used after); `systemctl restart leibniz-legible`,
  `staging.sh --main`, `--status`; the checks against the live site in
  Current state. Lesson, recorded under Next: the 75 GB disk cannot hold two
  store copies and two indexes; a volume before C4.

- **The operator's choice of reader (26 October), verbatim:** "I agree to go
  with TrOCR." So READER is `k3-trocr` (`data/models/k3/trocr/best`, the
  epoch-5 weights of runs row 615, version string
  `k3-trocr@runs-615-epoch-5`), read with `--kv-cache` as K2 read; its
  readings carry CC BY 4.0 like v1's (`legal.py`, `model-k3-trocr`: the Bern
  base MIT, K2's lines open-bucket edition text), so nothing on About, in
  `llms.txt`, the attribution line, the D2 export or the fragment packs
  changes its terms; Task 5 adds the readings to the outputs table and lets
  About read the sentence from the registry. The K3 "Next" line and the K3
  entry's choice bullet now carry the answer.
- **The operator's go (26 October), verbatim:** "go. The store histogram
  finishes or is stopped before Task 3's pilot starts: one process of yours
  on the machine during a GPU job." (The histogram: a read-only side look
  at the store's `lines` table started in Task 0.)
- **Setting (Task 0).** The operator's desktop, the WSL checkout
  `/home/evana/LeibnizLegible`, a Claude Code session; main at `c0b1a45`
  (#55, K3 merged) and `origin/main` the same; `k4-german-site` created with
  `git checkout -B k4-german-site origin/main`, the name the operator gave.
  The tree clean apart from the operator's own untracked files (`logs/`,
  `*.log`, `resume-run.sh`, `.python-version`, the two gt-audit HTML sheets),
  left alone. GPU: GTX 1660 Ti, driver 610.57.01, 1,188 MiB of 6,144 MiB
  held by Xwayland, nothing else on it. Disk: `/` 1007 G with 885 G free
  (the growing file on C:), **C: 476 G with 33 G free — the budget for every
  write under `/`**, `/mnt/d` 932 G with 368 G free; RAM 9,943 MiB (9,050
  available), swap 8,192 MiB; user systemd running (`systemd-run` present).
  `.venv-k1`: Python 3.12.13, torch 2.12.0+cu130 with CUDA available,
  transformers 5.12.1; `.venv-w3`: Python 3.12.13, no torch. Baseline:
  `ruff check` clean and 225 files formatted in both; pytest **1,026 passed,
  1 skipped** in 44.2 s (`.venv-k1`; the skip is the absent-stack path) and
  **1,016 passed, 1 skipped** in 41.3 s (`.venv-w3`; the skip is the
  letter-pool metric's module, which needs numpy). The store
  `data/inventory.sqlite`: 17,143,570,432 bytes, modified 2026-10-25 13:23,
  WAL empty, journal mode `wal`, page size 4,096 over 4,185,442 pages, no
  freelist; opened `mode=ro` only; the last runs row 615 (K3's TrOCR
  training).
- **Prerequisites, each verified (Task 0).** K3 merged: `htr/kurrent.py`
  carries `k3-trocr` and `k3-kraken` in CANDIDATES (off by default);
  `data/models/k3/trocr/best/` on D: behind the symlink holds
  `model.safetensors` (1,335,747,032 bytes), `config.json`,
  `generation_config.json`, the processor and tokenizer files and
  `val-hyps.json`; `reports/kurrent/k3-eval.md` and the two model cards are
  on main; runs rows 614 (kraken) and 615 (TrOCR) are in the store. The
  operator's choice of reader: above. K2b's test set:
  `reports/kurrent/letterpool-testset.csv` (134 letters),
  `data/kurrent/letterpool/testset.jsonl`, `reports/kurrent/letterpool-eval.md`
  with v1's rows (46.6 % overall, 53.7 % in Leibniz's own hand, 38.5 % the
  correspondents'). K2's readings (`data/kurrent/k2-readings/
  trocr-kurrent-xvi-xvii.jsonl`, 310,831 lines) are the Bern model's, not
  READER's, so nothing is reused. Page images under `/mnt/d/leibniz-images`.
- **Found while reading, before the go (Task 0).** (1) `kurrent-read` plans
  its pages from the census's pieces file (`--german`) and the factory's
  placement, and has no page-list option; Task 3 adds `--pages <file>` (one
  page id a line, Task 1's German pages) and leaves the K2 path as it is.
  (2) `read_pages` is one process — the page image decoded in the main
  process, the crops cut in memory, no loader workers — so the memory rule's
  "four loader workers at most" is met with none; the host memory is the
  pilot's to measure. (3) `set_line_recognition` updates rows in place, as
  the prompt says; Task 4 writes the new run's rows with `insert_line` under
  the run's id, the v1 row's geometry copied, and never touches v1's rows.
  (4) The index's `lang` field is the majority of `lines.lang` today
  (`_majority_lang` in `search/documents.py`); Task 2 lets a `page_lang` row
  override it. (5) C: has 33 GB free: the serving copy of Task 6 (`VACUUM
  INTO`, about the store's size) is written to `/mnt/d/`, not under the
  checkout, and the write of Task 4 states its expected size against C:
  from Task 1's line count before the go. (6) The backup copy goes beside the
  operator's chore's copies under `/mnt/d/leibniz-backups/`, dated, with its
  SHA-256 in a file beside it.
- **Task 1, which pages are German — CHECKPOINT A** (`leibniz enrich
  page-lang`, the new `enrich` group; `enrich/pagelang.py`, `enrich/cli.py`,
  +8 tests; `reports/kurrent/page-lang.md` + `.json` + `page-lang-works.csv`;
  `data/kurrent/page-lang.jsonl` and `german-pages.txt`, gitignored; the log
  `logs/k4-page-lang.log`). Every recognised page's current machine text
  (the newest run per line, text columns only) classified with K1's
  stopword identifier, unchanged: **236,210 pages, 12,825,054 lines with
  text, in 3 min 13 s at 486 MB** (the store read-only). The verdicts: la
  110,326, fr 62,463, **de 22,501**, mixed 19,992, unknown 20,928. *The
  measure:* the census's pieces placed by the factory's resolver today —
  the German pieces (German, or mixed with German leading) 1,688 pieces on
  **4,648 distinct pages** (the positives; the census's 5,874 summed its
  pieces' pages), the Latin and French pieces 5,486 on **16,616 pages** (the
  negatives), 97 pages both claim and 468 of the other pieces set aside;
  21,232 labelled pages measured. The identifier's own verdict (`lang ==
  "de"`: two German hits, a share of 0.65, eight tokens) reads **95.6 %
  precision, 53.0 % recall**. A page counts as German at a threshold on the
  leading language, its hit count, its share of all hits and the tokens; the
  grid (hits 2–20, share 0.3–0.95, tokens 8–40) is in the report, and
  precision barely moves across it (95.2–97 %) while recall falls from 74 %
  to 39 %: the false calls are a floor set by the labels (a German piece's
  Latin page, a Latin piece's German page), not by the rule. **The threshold,
  chosen for a precision of 95 %: German leads the stopword hits with at
  least two of them on a page of eight or more tokens (`hits≥2 score≥0.3
  tokens≥8`): precision 95.2 %, recall 74.5 % — 3,626 labelled pages called
  German, 173 of them Latin or French pieces' pages, 1,180 German pieces'
  pages missed.** The missed pages are what a Latin-trained model makes of
  Kurrent: their machine text reads `mixed` (682) or `unknown` (396), the
  German share of their hits a median 0.18 — v1 writes Latin and French
  words where it cannot read. The confusion matrix (the piece's language
  against the verdict) is in the report: of the pages of Latin pieces
  7,706, 19 read `de`; of French pieces' 8,814, 95; of German pieces' 4,438,
  2,405 read `de`, 1,228 `mixed`, 581 `unknown`. *The German pages:* the
  threshold's pages joined with the census's German pages (the edition's
  text is the better evidence; each page's evidence recorded — machine,
  edition, both): **30,797 pages, 1,708,517 lines** — by the machine text
  alone 26,164, by the edition alone 1,180, by both 3,453; by collection
  LeibnizBriefwechsel 14,455 pages (699,198 lines; 20.0 % of its pages),
  LeibnizHandschriften 9,604 (716,924; 16.4 %), **LeibnizMarginalien 6,719
  (291,329; 6.5 %) — printed books**, Leibnitiana 18, leibniz-rekonstruktionen
  1; 934 convolutes carry a German page (the forty with the most in the
  report, all in the CSV: LBr. F 20 892 pages, Leibn. Marg. 104 Stück 1 833,
  LBr. 411 798, LBr. 501 604, LH 23, 2, 21 590 …). `langid` itself is
  unchanged (K1's tests stand); the identifier's `mixed` and `unknown` on
  v1's reading of Kurrent is the finding, and the threshold's "German
  leads" is the adjustment, made outside the module. `--reuse` re-renders a
  threshold or the report from the same pass (20 s); `--list-exclude-set`
  keeps a collection out of the reading job's page list without touching
  the verdicts. **Two questions for the operator at this checkpoint:** (1)
  the Marginalien are print — the reader is a handwriting model, v1 reads
  the print well enough to find its German, and no ground truth exists for
  either on print — so the session proposes to leave the collection's 6,719
  pages out of the reading job's list (`--list-exclude-set
  LeibnizMarginalien`: 24,078 pages, 1,417,188 lines remain) and to record a
  print reader as an open point; (2) whether 95.2 % precision (a floor) is
  good enough to open the search page's language filter (Task 5).
- **Task 2, which reading wins — CHECKPOINT B** (`db.py`: `runs.scope`,
  `run_precedence`, `run_rank_cte`, `current_predicate`, `current_lines`,
  `count_current_lines`, the `page_lang` table and its helpers;
  `search/documents.py`, `release/export.py`, `pack/judgments.py` on the
  rule; `enrich/pagelang.py` `write_table` and `--write`;
  `align/letterpool_mixed.py` and `leibniz align letterpool-mixed`;
  +12 tests in `tests/test_current_rule.py`, +5 elsewhere; no store write).
  *The rule, once, in the store layer:* a line row's rank is **(the run's
  precedence, the run id)** — precedence 2 for a corrections run (stage
  `crowd`, G1's judgments), 1 for a run scoped to a language (`runs.scope`,
  an additive column; K4's Kurrent run declares `de`), 0 for an unscoped run
  (v1, C4's v2); the highest rank is current, so a scoped run beats every
  unscoped run on the lines it wrote whatever their age, a line it did not
  write (an empty reading writes no row) shows the newest unscoped row, and
  a corrected line outlives both. Read from the runs row, never from JSON:
  in Python `db.current_lines` (what `latest_lines` now returns, its name
  kept for its callers — the page view, the citations, the exports, the
  twins, the fragment pack, the index documents); in SQL a CTE over `runs`
  (`run_rank_cte`) joined on `run_id` and a `NOT EXISTS` probe
  (`current_predicate`) comparing the row values, used by
  `line_summaries_by_page` (the work and manifest endpoints), the D2 export
  (`iter_transcriptions`: ordered by rank, the last row wins), the stats
  (`corpus_stats`: the lines the store shows, their confidence histogram and
  the models by line count, through `count_current_lines` — one full scan
  plus one probe per row) and the judgments importer's `machine_row`. On a
  store from before K4 opened read-only (the website's and the exports'
  connections never migrate) the CTE has no `scope` column to read and every
  run counts as unscoped, which is what such a store holds; the `page_lang`
  readers answer empty there. *Timed on a synthetic 3,500-page work* (57
  lines a page, 199,500 lines; a scoped run on every tenth page with every
  fifth line left unwritten, a newer unscoped run on another tenth; 235,550
  rows; best of five): **the run-id-only probe of 2026-09 154 ms, the ranked
  probe 227 ms, the per-page Python loop 1,683 ms** (the probe keeps the
  covering unique index for the rival rows and settles their rank with one
  primary-key lookup in `runs`; the loop decodes every row's geometry);
  `count_current_lines` over the 235,550 rows 216 ms; the probe and the
  loop agree on every page. *The page language for the index:* a
  `page_lang` table (page_id, lang, score, n_tokens, evidence, run_id),
  written by `leibniz enrich page-lang --write` under a run of stage
  `enrich` (model `langid@<threshold>`; an upsert per page, so a second
  write replaces the rows under a new run — tested), read by
  `search/documents.py` for each document's `lang` (the work's rows in one
  query; a page without a row keeps the lines' majority, `unknown` today)
  and by `/api/stats` as `pages_by_lang`; a page is `de` where the German
  flag says so, else the identifier's verdict. *The stats' line count*
  changes meaning: the current rows with text (12,825,054 on this store
  under v1 alone) instead of every row whose text is not null (the old
  count took empty readings in) — the About page reads the figure from the
  index build, so it changes at the rebuild. *What reading a mixed page
  whole costs,* measured on the letter pool (`reports/kurrent/k4-mixed-letters.md`
  + `.json`): a letter is *mixed* when the identifier calls its reference
  text mixed or Latin and French hold a quarter of its stopword hits — **2
  of the 134 letters** (217 lines, 4,711 reference characters; the Latin
  and French share of the hits over the letters: quartiles 0.00 / 0.00 /
  0.01 — the pool is German correspondence by construction); on them v1
  39.1 % and k3-trocr 40.6 % CER, on the 132 German letters 46.8 % and 28.4
  %, so the reader's gain is 18.3 points on the German letters and −1.6 on
  the mixed ones, a difference of 19.9 points on two letters — a sign, not
  a measure; the per-line choice is Open question 31. Tests **1,036 passed,
  1 skipped** in `.venv-w3`, ruff clean.
- **Task 3, the reading — the pilot, CHECKPOINT C** (`leibniz align
  kurrent-read --pages <list> [--narrow-px N]`: a plan over any page list,
  the crops narrower than N px counted first; `kurrent_pilot.page_lines`
  now takes the current *unscoped* row of each line, so a resumed or
  repeated job after Task 4 reads the v1 geometry and never the Kurrent
  run's own rows; `count_lines_on` counts a line once however many rows it
  has; +2 tests. `pipeline/import_readings.py` and `leibniz pipeline
  import-readings` (Task 4's writer: one scoped run beside v1, the v1 row's
  geometry copied, an empty reading writes no row, a dry run by default,
  idempotent, resumable by page; +4 tests) are built and tested on
  fixtures; nothing written. The readings live on D: behind
  `data/kurrent/k4-readings` → `/mnt/d/leibniz-train/k4/readings/`, the logs
  under `/mnt/d/leibniz-train/k4/logs/` (`logs/k4-read.log` a symlink).
  Tests **1,042 passed, 1 skipped** in `.venv-w3`, **1,052 passed, 1
  skipped** in `.venv-k1`, ruff clean.) *The list:* the German pages
  without the Marginalien (the proposal of Checkpoint A, the operator's
  answer pending): **24,078 pages, 1,539,721 lines** the job reads (every v1
  row with a text, the 122,533 read as empty included — a Kurrent reader may
  read what v1 could not; 1,417,188 carry text), every page's image in the
  cache; the full list with the Marginalien 30,797 pages, 1,846,897 lines.
  *The crops under 80 px* (the amendment): **252,286 of the 1,539,721 lines
  (16.4 %)**, the polygon's box measured before padding — on the letter pool
  the same measure gives 3,172 of 18,445 (K3 counted 2,517 on the padded
  crop). *What READER does on them:* on the pool's 3,172 narrow crops
  k3-trocr returned a reading on 3,171 (one empty), a single character on
  2,422 (`e` 741, `n` 234, `d` 190, `h` 175 …), two on 576; v1 on the same
  crops: empty 1,284, one character 1,325, two 423, three or more 140; the
  two agree on 275. In the pilot's sample (below) 224 of the 2,000 lines are
  narrow: READER read all of them, 175 as one character; v1 85 empty, 92 one
  character. On the wide crops READER read every line (v1 left 19 empty) at
  36.2 characters a line against v1's 36.8. **The pilot** (the amendment's
  2,000 lines: `--sweep --sweep-batches 16 --sweep-kv on`, a sample of 28
  pages spread over the list, under `systemd-run --user --scope -p
  MemoryMax=6G`, `/usr/bin/time -v` and the guard; the log
  `k4-pilot.log`, the guard's record `k4-pilot-guard.csv`): **2,000 lines in
  250.5 s — 7.98 lines/s, 125.3 ms a line all-in** (243.6 s in the engine;
  the pace rose from 350 ms a line over the first three pages, the model's
  load and warm-up, to 125 over the whole; K3 measured 152 ms on the pool's
  crops); **host memory 2,291,072 KB at peak (2.19 GB) under the 6 GB
  scope**, the host never under 7,493 MiB available; the card: torch's
  reserved peak 4,564 MiB, nvidia-smi's 5,697 MiB with Xwayland's 1,041 —
  203 MiB under the guard's 5,900 limit, so the job runs with
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` against fragmentation
  and, if the guard ends it, resumes by page; GPU utilisation a mean 4 %
  (the decoder's cache makes each step a small kernel; the card is
  latency-bound, not full); wall 7 min 38 s with the narrow-crop count
  (about three minutes) and the load. The guard's first pattern
  (`kurrent-read --pages`) matched nothing because `--db` precedes `--pages`
  on the command line; it was restarted two minutes in as
  `[k]urrent-read --db`, which the job uses. The sweep's 2,000 readings sit
  in `readings/sweep/` and do not count towards the job. **The figure for
  the go: at the pilot's 125.3 ms a line the 1,539,721 lines take 53.6 h —
  two days and six hours; with the Marginalien (1,846,897 lines) 64.3 h,
  two days and sixteen hours.** Disk: the readings about 174 bytes a line
  (the sweep's file), 268 MB on D: for the job; the logs on D:; nothing on
  C: (30 GB free, down from 33 at Task 0). The launch script
  `/mnt/d/leibniz-train/k4/logs/run-read.sh`: the job under the scope with
  `--log-every 600`, the guard at 5,900 MiB on the card and a host floor of
  2,500 MiB sampling every 5 s, one torch process, nothing else of the
  session's beside it. **Asked of the operator at this checkpoint:** the
  go for the job (about 54 hours; or 64 with the Marginalien), and for
  Task 4 whether READER's one-character readings on the 252,286 crops under
  80 px go into the store (the amendment writes every non-empty reading;
  the session would rather write no row for a crop under 80 px, so those
  lines keep v1's row — a rule the importer can apply, recorded with its
  count).
- **The operator's decisions (28 October), verbatim.** Before them, the
  operator's own note: "The apartment lost power for a second today and the
  PC restarted; nothing of yours was running, the pilot had finished and you
  were waiting for me since Monday. Before resuming I added
  autoMemoryReclaim=gradual under [experimental] in .wslconfig and ran wsl
  --shutdown, because Windows hung at the lock screen yesterday with the VM
  holding memory. A read-only quick_check of the store is running
  (~/quickcheck.log); launch nothing before it prints ok. Your background
  histogram task died with the session; do not restart it." (The histogram
  was a read-only probe of row lengths; its figures are not needed again.
  `.wslconfig` now: `memory=10GB`, `swap=8GB`, `autoMemoryReclaim=gradual`.)
  Then: "1. Go for the reading job without the Marginalien (M1's domain), at
  the pilot's settings. Before launching, give run-read.sh a retry loop: if
  the job ends with a non-zero exit, relaunch it from the readings file
  after 60 seconds, up to five times, logging each relaunch, so a guard kill
  does not wait for a human. Then launch under the memory scope with the
  guard and report the first progress line and the expected finish time.
  2. Task 4 writes every non-empty reading, crops under 80 px included, as
  the amendment says: the letter-pool number was measured on all crops, and
  one run per page keeps K3b's later replacement simple. Count the narrow
  crops in the K4 report and record them as an open question for K3b's
  segmentation measurement. 3. The language filter: decide at Task 5. Print
  checkpoint A's table again then (pages by language, precision, recall,
  the threshold), since I did not see it on Monday. 4. pytest beside the
  job: yes, in .venv-w3 or with CUDA_VISIBLE_DEVICES set to empty, with -p
  no:cacheprovider, under a gigabyte, never two at once, never anything
  that touches the GPU." So: the page list stays the 24,078 pages without
  the Marginalien; `run-read.sh` (on D:, the first version kept as
  `run-read.sh.v1`) now loops: the job under the scope with the guard
  beside it, `READ-EXIT <code> launch <n>` logged at each end, and after a
  non-zero exit `# relaunch <n> of 5 in 60 s` then the same command (the
  job reads what its JSONL does not hold, one page lost at most), at most
  five relaunches, then `READ-DONE`. Task 4's importer writes every
  non-empty reading as built; the narrow-crop count (252,286 of the job's
  lines under 80 px) goes into the K4 report and Open question 32 for K3b.
- **The job launched (28 October).** The operator's read-only
  `PRAGMA quick_check` printed `ok` after 894 s; nothing else ran. 09:50:13
  `setsid nohup bash /mnt/d/leibniz-train/k4/logs/run-read.sh` from a
  plain shell (the harness's own background tasks die with a session, as
  the histogram did): launch 1 under `systemd-run --user --scope -p
  MemoryMax=6G` (unit `run-p1387-i1672.scope`), `/usr/bin/time -v`, the
  guard beside it at 5,900 MiB on the card and a 2,500 MiB host floor,
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, batch 16, the
  decoder's cache, `--log-every 600`. The engine was up by 09:51; **the
  first progress line, 10:00:35: 5,771 of 1,539,721 lines done, 34,327
  lines/h, 105 ms a line, ETA 44 h 41 m, pages 107 of 24,078** — faster
  than the pilot's 125 ms (the pilot's figure carried the load and the
  narrow-crop count; GPU utilisation now a mean 80 % over the guard's first
  130 samples against the pilot's 4 %). **Expected finish: about 2026-10-30
  07:00 at the job's own pace, 15:30 at the pilot's.** Memory at the first
  line: the python process 1,859,336 KB resident, the host never under 7,555
  MiB available, the card's peak 5,734 MiB (166 MiB under the guard; the
  pilot's 5,697). Readings in `data/kurrent/k4-readings/k3-trocr.jsonl`
  (945 KB after eight minutes), the stats beside them. Beside the job this
  session runs ruff and one pytest at a time (`python -m pytest -p
  no:cacheprovider`, `CUDA_VISIBLE_DEVICES=` empty; the five touched test
  files took 157 MB and 5 s) and writes Task 4's and Task 5's code; the
  browser checks of Task 5 (headless Chromium) wait for the job's end
  rather than share the card. Built while the job runs: the importer counts
  the crops under 80 px per collection as it goes (`narrow_lines`,
  `narrow_rows`; no second pass over the geometry), `leibniz pipeline
  k4-report` (`pipeline/k4_report.py`) writes `reports/kurrent/k4-reading.md`
  and `.json` from the job's stats file, its log (launches, relaunches,
  exits, `/usr/bin/time`'s peak RSS per launch), the guard's CSV and the
  import's summary JSON, numbers only, no store read.
- **The first guard kill and the relaunch (2026-10-28, 19:09–19:34).** The
  guard killed launch 1 at 19:09:56 with the card at 5,922 MiB, 22 over the
  5,900 line, after 363,739 lines and 4,932 pages at a steady 91 ms a line
  (launch 1 ran 9 h 20 m; exit 143). No leak: over the guard's 6,619 samples
  the hourly means from 10:00 on sat between 5,623 and 5,769 MiB, 160
  samples went over 5,800, and the kill was one of those spikes (5,622 →
  5,889 → 5,922 MiB across ten seconds); the host never under 6,879 MiB
  available. The retry loop relaunched at 19:11:06 (relaunch 1 of 5, launch
  2) from the readings file: 366,804 lines taken as done, the job resumed
  after the 4,932 done pages. The resume costs time the pace line hides:
  the pace clock starts before the loop that skips the done pages, and a
  skipped page still costs one `page_lines` query on the store, so the
  4,932 skips took about five minutes at 15 % GPU utilisation and launch
  2's first progress line (19:24:20, 1,519 lines this run) showed 400 ms a
  line, its second (19:34:21, 374,895 lines done, 8,091 this run, pages
  5,049) 149 ms; the interval between the two, 6,572 lines in 601 s, is 91
  ms a line, launch 1's pace. The skip cost grows with progress, about a
  minute per thousand done pages at each relaunch. **Expected finish on the
  interval pace: about 2026-10-30 01:00 without further kills; each further
  kill costs the 60 s wait, the model load, the skip phase and the page in
  progress.** The card after the relaunch: 5,575 MiB, 87–88 °C, the
  driver's software thermal slowdown active, SM clock 1,575–1,665 MHz of
  2,100, 93 W of 120; the guard logs no temperature, so whether launch 1
  ran throttled the same way is unknown. The guard's limit is the
  operator's to raise; the K4 report's launches table carries the kill.
- **The job's end (2026-10-30 00:49:38): READ-DONE, exit 0, two launches.**
  Launch 2 ran 29 h 38 m 24 s (`/usr/bin/time -v`, peak RSS 2,769,976 KB)
  and read 1,172,917 lines at 90.8 ms a line, 39,666 lines an hour, 28.6 of
  its 29.6 hours in the engine; launch 1 had read 366,804 in 9 h 20 m. In
  all **1,539,721 of 1,539,721 lines on 24,078 pages, 0 skipped, 33 read as
  empty** (no row for those at Task 4), 38 h 59 m from the first launch to
  READ-DONE; the readings file `k3-trocr.jsonl` 273,008,360 bytes,
  1,539,721 rows, every line id once. The guard over both launches: 27,574
  samples, the card's peak 5,922 MiB (the kill), GPU utilisation a mean
  88.2 %, the host never under 6,727 MiB available, one kill. Both
  launches' pace held at 91 ms a line, the pilot's 125 ms never seen in the
  job. The dated backup copy of the master store to
  `/mnt/d/leibniz-backups/inventory-2026-10-30.sqlite` (the sqlite3 backup
  API from a read-only connection, 4,096 pages a step, the SHA-256 written
  beside it) started 00:55:55 under a 2 GB scope; D: had 347 GB free, C: 51
  GB. **Stopped at 01:02 and replaced by a plain copy:** the backup API's
  per-step commits over the drive share ran at 3.4 MB a second (262,144 of
  4,185,442 pages in 311 s, an 83-minute job against a measured 54 MB a
  second for a direct write to D: and 561 MB a second reading the store),
  and the store has had no write since 2026-10-25 and no write-ahead
  content to fold in (`journal_mode` wal, the `-wal` file empty), so a copy
  of the file is the same database. `cp` took 1,055 s (01:02:50–01:20:25),
  the digests of both sides 374 s more: **`inventory-2026-10-30.sqlite`,
  17,143,570,432 bytes, SHA-256
  `2cde43729fc9c177b32e469ec3b55a18e89347c39d6222fa44a90fa5cea0a58f` on the
  source and on the copy, the digest beside the copy in `.sha256`
  (`sha256sum -c` form).** D: 331 GB free after it. The write waits for the
  operator's go.
- **The importer's dry run (2026-10-30 01:27–01:30, the store read-only).**
  `leibniz pipeline import-readings` over the job's file without `--write`,
  under a 4 GB scope: 3 min 34 s, 489,604 KB peak RSS. **It would write
  1,539,688 rows on 24,078 pages** under one run (model
  `k3-trocr@runs-615-epoch-5`, scope `de`): 1,539,721 lines on the pages,
  33 read as empty (no row), 0 lines without a reading, 0 orphan readings,
  0 pages done before. Crops under 80 px: 252,286 lines, 252,278 of them
  with a row (8 of the 33 empties are narrow). By collection: Handschriften
  9,604 pages, 757,241 lines, 757,227 rows, 87,619 narrow; Briefwechsel
  14,455 pages, 780,959 lines, 780,940 rows, 164,360 narrow; Leibnitiana 18
  pages, 1,481 lines, 1,481 rows, 279 narrow; Rekonstruktionen 1 page, 40
  lines, 40 rows, 28 narrow. Store before the write 17,143,570,432 bytes,
  WAL 0 bytes. The go request printed for the operator with these numbers,
  the gate and the commands.
- **Task 4's writes (2026-10-30 08:40–08:51) — CHECKPOINT D.** The
  operator's go (30 October), verbatim: "Go 1 and Go 2, in that order. After
  the two writes, print the German pages and lines under the new run, the
  run row (stage, model, scope), the store's size and the time -v peak; then
  the K4 report and the import summary, and checkpoint D. The off-site
  upload of the backup is mine and runs beside you from D:. Nothing else
  touches the store until you say the writes are done." Pre-flight: no
  process of the session's running, the store 17,143,570,432 bytes with an
  empty WAL, C: 51 GB free, the write's five inputs at their recorded
  SHA-256. Each write from a detached shell under
  `systemd-run --user --scope -p MemoryMax=4G` with `/usr/bin/time -v`,
  nothing else of the session's beside it; the launchers and logs under
  `/mnt/d/leibniz-train/k4/logs/` (`run-write-1.sh`, `write-1.log`,
  `run-write-2.sh`, `write-2.log`, `after-write.log`). **Write 1**
  (08:40:46–08:41:10; 23.5 s, 570,072 KB peak): `leibniz enrich page-lang
  --db data/inventory.sqlite --reuse --write --list-exclude-set
  LeibnizMarginalien --today 2026-10-26` read Task 1's 236,210 rows back,
  measured the threshold on the census labels again (hits≥2 score≥0.3
  tokens≥8: precision 95.2 %, recall 74.5 % on 21,232 labelled pages, 173
  Latin or French pages called German) and wrote **236,210 `page_lang` rows
  under run 616** (stage `enrich`, model `langid@hits≥2 score≥0.3
  tokens≥8`, no scope): de 30,797, la 110,167, fr 62,330, unknown 19,115,
  mixed 13,801. The page list (24,078 pages) and `page-lang.jsonl` came out
  byte-identical to Task 1's (SHA-256 compared before and after); the two
  reports changed only in their "generated" date. The store 17,163,821,056
  bytes after (+20,250,624), the WAL checkpointed and removed on close.
  **Write 2** (08:41:59–08:51:07; 9 min 7 s, 517,996 KB peak, 32 % of a
  CPU): `leibniz pipeline import-readings --db data/inventory.sqlite
  --readings data/kurrent/k4-readings/k3-trocr.jsonl --pages
  data/kurrent/german-pages.txt --model k3-trocr@runs-615-epoch-5 --reader
  k3-trocr --scope de --write --summary reports/kurrent/k4-import.json
  --note …` wrote **1,539,688 rows on 24,078 pages under run 617** (stage
  `recognize`, model `k3-trocr@runs-615-epoch-5`, scope `de`; n_input
  1,539,721, n_ok 1,539,688, n_failed 0; git `afb756f`; the note and the
  import's counts in the run's params): 33 empty readings without a row, 0
  lines without a reading, 0 orphan readings, 0 pages done before; crops
  under 80 px 252,286 lines, 252,278 of them with a row. By collection:
  Briefwechsel 14,455 pages, 780,940 rows; Handschriften 9,604, 757,227;
  Leibnitiana 18, 1,481; Rekonstruktionen 1, 40 — the dry run's numbers
  exactly. **Verified read-only afterwards** (`after-write.log`, 9 s): every
  row of run 617 status `machine`, lang `de`, model
  `k3-trocr@runs-615-epoch-5`, none without text, geometry or confidence;
  run 617 the only run with a scope; 30,797 German pages in `page_lang`,
  24,078 of them with rows under run 617, the other 6,719 the Marginalien
  pages the job left out, no page under the run unmarked. **The store
  after: 19,354,243,072 bytes** (4,725,157 pages of 4,096, freelist 0;
  +2,210,672,640 over the backup's 17,143,570,432), WAL 0 bytes, journal
  mode `wal`; C: 48 GB free. The K4 report built from the job's stats, log
  and guard CSV and the import summary (`leibniz pipeline k4-report …
  --store-before 17143570432 --today 2026-10-30` → `reports/kurrent/
  k4-reading.md` and `.json`; `reports/kurrent/k4-import.json`): the job's
  table (90.8 ms a line, 39,666 lines an hour in the last launch; peak host
  RSS 2,769,976 KB on the launch that ended on its own; card peak 5,922
  MiB; GPU utilisation 88.2 % mean; host MemAvailable minimum 6,727 MiB),
  the coverage sentence, the write's table and the collection table. The
  operator's off-site upload of the backup (rclone from D:) ran beside the
  writes, theirs. Nothing deployed; the serving copy is Task 6's.
- **Task 5's browser checks (2026-10-30 09:05–09:20) — CHECKPOINT E.** As
  W4 ran them: Playwright from npm on the Windows side of the box
  (`playwright@1.64.1` with `playwright-core`, `axe-core@4.14.0`, 3
  packages, 22 MB, in `%LOCALAPPDATA%\Temp\pw-k4`), Windows Node
  v24.14.0, the preinstalled Chromium build `chromium-1243` under
  `ms-playwright` (Playwright 1.64.1 expects build 1248, so the checks get
  the executable's path as an argument), against `leibniz serve --backend
  none --rate-limit 0` in WSL on a fixture store (the test fixtures'
  `seed_store` + `seed_german`, one scoped `k3-trocr@runs-615-epoch-5` run
  with one re-read line on `00069377:0001`, `page_lang` rows). The install
  was the operator's at the keyboard: the session's permission classifier
  refused the npm command, and a first form of the line through `cmd.exe`
  failed on the Windows side before writing anything ("The system cannot
  find the path specified."); the Node install's bash shim with
  `WSLENV=PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` carried the variable to the
  Windows process and installed in 3 s, no browser downloaded. The scripts
  are committed for the re-run after the deploy: `tools/browser-checks/k4-seed.py`
  and `tools/browser-checks/k4-checks.mjs` (the GWLB stubbed with a one-pixel
  JPEG and a level-0 `info.json`; axe-core served from the app's origin
  through a route, the CSP being `script-src 'self'`). **What is checked, in
  EN and DE at 1,280 and 390 px:** About (the models row, pages by language
  with German, READER named from the `data-reader-de` stamp, the base's MIT
  from the stamps, no placeholder left), the search form (the language
  filter visible, its six values `'' la fr de mixed unknown`, the label
  "Language (detected)" / "Sprache (erkannt)", the hint naming 95 % and 75 %
  and being the field's `aria-describedby`, the writing-stage filter
  hidden), the German page (`k3-trocr@runs-615-epoch-5` on its line, v1 on
  the others, the provenance row labelled "Model" / "Modell"), no console or
  page errors, no horizontal scroll, axe-core 0 violations on every view;
  12 screenshots. **First run 86 of 92:** (1) the page view threw on the
  stub's `info.json` ("Nothing in the info.json to construct image pyramids
  from", then "Invalid array length"): a level-0 service without `sizes` or
  `tiles` gives OpenSeadragon nothing, the stub's fault, fixed in the stub;
  (2) **About scrolled sideways at 390 px, 411 px wide, in both languages —
  not K4's rows: the "Report a problem" link, whose text is the full issues
  URL, 380 px of unbreakable text, on main before K4.** Fixed in
  `style.css` (`.about a { overflow-wrap: anywhere; }`, one rule). **Second
  run 92 of 92, 0 failed.** The German page at 390 px looked at: line 1 as
  READER's reading, the citation and the text block naming both models with
  their runs, the warning box's Kurrent rate. ruff clean; pytest **1,062
  passed, 1 skipped** (55.3 s, 809,716 KB under the 1 GB scope beside the
  serving copy, no GPU).
- **Task 6, the serving copy and the box (2026-10-30, from 08:56).** The copy:
  `deploy/prepare-store.sh data/inventory.sqlite
  /mnt/d/leibniz-serving/inventory-serving-2026-10-30.sqlite` from 08:56:53
  under a 4 GB scope (`run-serving-copy.sh` under
  `/mnt/d/leibniz-train/k4/logs/`; the output on D: by the disk rule, C: 48 GB
  free; `UV_NO_SYNC=1`, no GPU; the older `inventory-serving.sqlite` of 22
  October left beside it). The `VACUUM INTO` finished at 09:38 — about 41
  minutes, the share's write pace 4–7 MiB/s, against the README's ten minutes
  for a copy on the VHD — at **18,314,969,088 bytes**: 4,471,428 pages of
  4,096 against the master's 4,725,157, so 253,729 pages (1,039,273,984 bytes)
  freed by the vacuum; `journal_mode delete`, freelist 0, read from the copy's
  header. The script's `integrity_check` then ran over the share, a b-tree
  walk in 4 KiB random reads at under a megabyte a second (0.7 MiB/s in a 20 s
  sample at 10:55; about 31 GB read in 79 minutes against an 18.3 GB file, the
  2 MB page cache turning over), with no end to estimate: stopped at 10:57:23
  (SIGTERM to the python child; the script's wall 2:00:30, peak 27,740 KB,
  exit 143). The copy was complete and closed at 09:38 and is untouched by the
  stop. The integrity check moves to the box, where the file lies on local
  disk (the command below, with the row counts it must print); the script's
  last step, the SHA-256, re-run on its own from 10:57:45 (`run-sha256.sh`, a
  512 MB scope), read sequentially at 1.6–2.0 MiB/s while the operator's
  `rclone check` of the backups folder read the five backup copies at once
  over the same share (from 10:31), and faster once that ended: **58 min 32 s**
  in all (10:57:45–11:56:18, 5.0 MiB/s over the whole file, peak 7,552 KB);
  the digest **`3ff238b22a89e8dde77d7f965b47045785b0d37740bf25eae0f2c1496da8f782`**,
  in `inventory-serving-2026-10-30.sqlite.sha256` beside the copy, in
  `sha256sum -c` form. The lesson for the README: `prepare-store.sh` is built for a
  copy on the VHD; over the drive share the vacuum takes four times the budget
  and the integrity check cannot be run at all, so on this desktop the check
  belongs on the box.

  **The numbers for the checks, read from the master** (`k4-stats.py`,
  read-only under a 1 GB scope, 11:02:06–11:11:24, `corpus_stats` 538 s, peak
  39,692 KB): the lines shown under the rule **12,947,584**, by model
  `FoNDUE-GD_v2_ft_Leibniz` 11,407,896 and `k3-trocr@runs-615-epoch-5`
  1,539,688 (run 617's rows, every one of them current); pages by language la
  110,167 · fr 62,330 · de 30,797 · unknown 19,115 · mixed 13,801; works
  2,225, pages 236,795 (recognized 236,210, skipped 569); the confidence
  histogram under 0.5 907,117 · 0.5–0.7 998,464 · 0.7–0.8 897,761 · 0.8–0.9
  2,344,657 · 0.9 and above 7,799,585. The tables' row counts, which the copy
  must repeat on the box: works 2,225 · pages 236,795 · lines 15,061,271 ·
  gt_lines 333,680 · runs 617. The page for the checks,
  `DE-611-HS-971383:0035` (Briefwechsel, folio 18r, a portrait scan of 2,447 ×
  4,018, so no spread for the twins rule to halve): 203 lines, all 203 current
  ones READER's (run 348's 203 v1 rows beneath), `page_lang` de at 0.5405 on
  351 tokens, evidence both, run 616. One thing the master's numbers caught:
  the store's v1 rows carry the model string `FoNDUE-GD_v2_ft_Leibniz`; the
  fixture's `…@v1` is the tests' own, and llms.txt had the fixture's string
  for the real site — corrected on this branch (the fixture-based checks
  script keeps it, as it should).

  **The box, in order.** The target, the user name and the password are on the
  operator's plan page; `HOST` and `USER` stand for them below. The transfer
  reads D: over the share, so it waits for the rclone check to end or shares
  its pace; the README's budget is an hour and a half.

  ```bash
  # the desktop: the transfer to a second path on the box (deploy/README.md §14)
  rsync -avP /mnt/d/leibniz-serving/inventory-serving-2026-10-30.sqlite root@HOST:/var/lib/leibniz-legible/inventory-staging.sqlite

  # the box: the digest (the one this entry prints), the owner, then the integrity
  # check and the row counts the share could not give — read-only, local disk
  ssh root@HOST
  sha256sum /var/lib/leibniz-legible/inventory-staging.sqlite
  chown leibniz:leibniz /var/lib/leibniz-legible/inventory-staging.sqlite
  python3 -c "import sqlite3; c = sqlite3.connect('file:/var/lib/leibniz-legible/inventory-staging.sqlite?mode=ro', uri=True); print('integrity:', c.execute('PRAGMA integrity_check').fetchone()[0]); print('journal mode:', c.execute('PRAGMA journal_mode').fetchone()[0]); [print(t, c.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0]) for t in ('works', 'pages', 'lines', 'gt_lines', 'runs')]"
  #   integrity: ok · journal mode: delete · works 2225 · pages 236795 · lines 15061271 · gt_lines 333680 · runs 617
  #   (the desktop's read-only quick_check of the 17 GB master took 894 s on its VHD on the 28th; budget that order)

  # the box: staging on the copy and on the branch (the branch is on origin)
  sed -i 's#^LEIBNIZ_DB_PATH=.*#LEIBNIZ_DB_PATH=/var/lib/leibniz-legible/inventory-staging.sqlite#' /etc/leibniz-legible/staging.env
  grep '^LEIBNIZ_DB_PATH=' /etc/leibniz-legible/staging.env
  /opt/leibniz-legible/deploy/staging.sh k4-german-site      # restarts the unit, waits for /healthz, prints the address
  ```

  **The checks, round one** — the new store under the old index: pages,
  About's reader sentences and `/api/stats`' readers come from the store and
  the registry at once; search, the models row and the pages-by-language row
  wait for the index build. Each line's expected answer follows it.

  ```bash
  S=https://staging.leibnizlegible.com
  curl -su USER $S/healthz                                                     # {"status":"ok",…}
  curl -su USER $S/about | grep -o 'data-reader-de="k3-trocr"' | wc -l         # 1
  curl -su USER $S/about | grep -o 'data-licence-de-[a-z]*="[^"]*"'
  #   data-licence-de-model="CC BY 4.0"  data-licence-de-base="MIT"  data-licence-de-readings="CC BY 4.0"
  curl -su USER $S/static/i18n.js | grep -c "'search.lang':\|'search.lang.help':\|'about.numbers.langs':\|'about.numbers.models':\|'lang.de.text':"
  #   10 (five keys, each in EN and DE)
  curl -su USER $S/llms.txt | grep -c k3-trocr                                 # 3
  curl -su USER $S/llms.txt | grep -c '28.6%'                                  # 1
  curl -su USER $S/llms.txt | grep -c 'three quarters'                         # 1
  curl -su USER $S/llms.txt | grep -c 'FoNDUE-GD_v2_ft_Leibniz@v1'             # 0
  curl -su USER $S/api/stats | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s["readers"]["de"]); print(s["models"]); print(s.get("pages_by_lang"))'
  #   {'reader': 'k3-trocr', 'version': 'k3-trocr@runs-615-epoch-5', 'model': "K3's TrOCR model, …", 'model_licence': 'CC BY 4.0',
  #    'base': 'dh-unibe/trocr-kurrent-XVI-XVII (the Bern Kurrent TrOCR model)', 'base_licence': 'MIT', 'readings_licence': 'CC BY 4.0', 'output': 'readings-de'}
  #   then, until the build: the old index's models (FoNDUE-GD_v2_ft_Leibniz alone) and None
  curl -su USER $S/api/pages/DE-611-HS-971383:0035 | python3 -c 'import json,sys,collections; p=json.load(sys.stdin); print(p["label"], p["run"]["run_id"], p["run"]["stage"], p["run"]["model"]); print(collections.Counter(l["model"] for l in p["lines"]))'
  #   18r 617 recognize k3-trocr@runs-615-epoch-5
  #   Counter({'k3-trocr@runs-615-epoch-5': 203})
  curl -su USER "$S/api/search?q=Herr&lang=de" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["total"], {h["lang"] for h in r["hits"]})'
  #   until the build: 0 set() — the old index filed every page under the lines' own lang, unknown until C4
  ```

  In the browser, with the password: `$S/page/DE-611-HS-971383:0035` — every
  line's provenance row names `k3-trocr@runs-615-epoch-5`, the citation is
  pinned to run 617; `$S/about` — the licence paragraph with the stamps filled
  in (below); `$S/search` — the "Language (detected)" filter, five values
  under "Any language", the hint beneath it, the writing-stage filter hidden.
  Then the index:

  ```bash
  /opt/leibniz-legible/deploy/staging.sh --index     # prints df -h /var/lib/meilisearch, asks "Build it? [y/N]"; staging down for the build; 5 h 33 m last time
  journalctl -fu leibniz-index-staging               # Ctrl-C leaves the build running; the script starts the unit again when it ends
  ```

  **The checks, round two**, after the build (the staging unit is started
  again by the script):

  ```bash
  curl -su USER $S/api/stats | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s["lines"], s["models"]); print(s["pages_by_lang"]); print(s["index_built_at"])'
  #   12947584 {'FoNDUE-GD_v2_ft_Leibniz': 11407896, 'k3-trocr@runs-615-epoch-5': 1539688}
  #   {'de': 30797, 'fr': 62330, 'la': 110167, 'mixed': 13801, 'unknown': 19115}
  #   the build's own time
  curl -su USER "$S/api/search?q=Herr&lang=de" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["total"], {h["lang"] for h in r["hits"]})'
  #   a count above 0, and {'de'}
  ```

  And About in the browser: the row "Recognition models (lines shown)" with
  both models and their counts, the row "Pages by language" with the five
  values.

  **What the site now says.** About, EN: "The German pages are read by this
  project's own Kurrent model (k3-trocr), fine-tuned from the Bern Kurrent
  model (MIT) on open edition text with no non-commercial input, so the model
  is CC BY 4.0 and its readings are CC BY 4.0." (the stamps `readerDe`,
  `deBase`, `deModel`, `deReadings` filled from the registry at each serve);
  DE: "Die deutschen Seiten liest das projekteigene Kurrent-Modell (k3-trocr),
  feinabgestimmt aus dem Berner Kurrent-Modell (MIT) …". About's models
  paragraph: "The re-read covers the German pages a language pass over the
  machine text found — about three quarters of the German pages by the
  census's measure, found with 95% precision — the printed Marginalien
  excepted; the rest keep the older model's text, so a German page may still
  show the first model's reading." About's numbers, once the index is built:
  "Recognition models (lines shown)" FoNDUE-GD_v2_ft_Leibniz 11,407,896 ·
  k3-trocr@runs-615-epoch-5 1,539,688; "Pages by language" la 110,167 · fr
  62,330 · de 30,797 · unknown 19,115 · mixed 13,801. The search form:
  "Language (detected)" / "Sprache (erkannt)", five values, the hint "The
  labels come from a language pass over the machine text; German is detected
  with 95 % precision and about 75 % recall." A German page: each line's
  provenance row "Model: k3-trocr@runs-615-epoch-5", the citation pinned to
  run 617. llms.txt: the second model named with its 28.6% against 46.6%, the
  three-quarters coverage, the model string per line in the API, the licence
  line "CC BY 4.0, its readings CC BY 4.0".

  **The operator's live switch, in order, after the merge.** One departure
  from the prompt's order: the index build must run K4's code (the
  pages-by-language count, the scoped-run rule in the documents), so the §9
  update of the live checkout comes before the rebuild; K4's code reads a
  store without the `page_lang` table (`has_table` guards), so the code may go
  live before the store. The staging copy is the serving copy, so the live
  file is replaced by one rename and no second transfer; the staging unit is
  stopped first, as the rebuild wants it anyway (§14, Memory).

  ```bash
  # 1. the code (README §9, Update the app)
  sudo -u leibniz -H git -C /opt/leibniz-legible pull --ff-only
  sudo -u leibniz -H env UV_CACHE_DIR=/opt/leibniz-legible/.uv/cache UV_PYTHON_INSTALL_DIR=/opt/leibniz-legible/.uv/python uv sync --project /opt/leibniz-legible --frozen --no-dev --extra web
  systemctl restart leibniz-legible && curl -s http://127.0.0.1:8000/healthz    # {"status":"ok",…}
  # 2. the live serving copy replaced (one rename; requests in flight keep the old file until they close it)
  systemctl stop leibniz-legible-staging
  mv -f /var/lib/leibniz-legible/inventory-staging.sqlite /var/lib/leibniz-legible/inventory.sqlite
  sha256sum /var/lib/leibniz-legible/inventory.sqlite                           # the digest above
  sed -i 's#^LEIBNIZ_DB_PATH=.*#LEIBNIZ_DB_PATH=/var/lib/leibniz-legible/inventory.sqlite#' /etc/leibniz-legible/staging.env
  # 3. the staging index dropped first (its disk), then the live index rebuilt beside the live one (§5; 5 h 33 m last time)
  /opt/leibniz-legible/deploy/staging.sh --drop-index
  du -sh /var/lib/meilisearch && df -h /var/lib/meilisearch
  systemd-run --unit=leibniz-index --uid=leibniz --gid=leibniz -p WorkingDirectory=/opt/leibniz-legible --setenv=LEIBNIZ_DB_PATH=/var/lib/leibniz-legible/inventory.sqlite --setenv=MEILI_MASTER_KEY="$(sed -n 's/^MEILI_MASTER_KEY=//p' /etc/meilisearch/env)" /opt/leibniz-legible/.venv/bin/leibniz index build --backend meili
  journalctl -fu leibniz-index
  # 4. after the swap: the app restarted so /api/stats reads the new build (§9, A new corpus run); staging back on main
  systemctl restart leibniz-legible
  /opt/leibniz-legible/deploy/staging.sh --main
  /opt/leibniz-legible/deploy/staging.sh --status
  # 5. the checks: both rounds above against https://leibnizlegible.com, without -u, the same answers
  ```

  Then the operator's STATUS line for the switch (the build's time, the live
  `/api/stats` figures) — the numbers are theirs to produce. ruff clean;
  pytest in `.venv-w3` **1,052 passed, 1 skipped** (40.0 s, 219,356 KB under
  the 1 GB scope; the skip is `test_align_letterpool_eval.py`, its eleven
  tests wanting numpy, which that environment lacks: 1,052 + 11 is Checkpoint
  E's 1,062 passed and 1 skipped). Nothing deployed; the branch pushed, not
  merged; the compare URL printed.
- **The operator's decision on the language filter (28 October),
  verbatim:** "The language filter: open it, with the five values and the
  label "language (detected)"; the help text says the labels come from a
  language pass over the machine text, German detected with 95 % precision
  and about 75 % recall. About's sentence and the K4 report say the re-read
  covers the German pages the language pass found, about three quarters of
  them by the census's measure, and that the rest keep the older text;
  record the threshold and a second pass as the next round's item in Next.
  Build Task 5's second part now, the browser checks after the job as you
  planned." Done in the second part of Task 5: the search form's language
  field is shown (`index.html`; the writing-stage field stays hidden), its
  label `Language (detected)` / `Sprache (erkannt)`, a hint under it
  (`search.lang.help`, EN and DE); About's "How wrong is it?" paragraph and
  the K4 report's coverage line say what the re-read covers and that the
  rest keeps the older text; `llms.txt` says the same for the `lang`
  parameter; the Next item is at the head of "Next".
- **Plan, as printed for the go.** *Task 1:* `leibniz enrich page-lang`
  (a new `enrich` group, `enrich/cli.py`, `enrich/pagelang.py`): every
  recognised page's text under the current rule classified with
  `langid.classify`, into `data/kurrent/page-lang.jsonl` (page_id, lang,
  score, n_tokens, plus the hits); the measure against the census's pieces —
  the German pieces' pages as positives, the Latin and French pieces' pages
  as negatives (`reports/kurrent/german_pieces_index.csv` and the census's
  summary; pages shared by both groups set aside and counted) — precision
  and recall for German along the score and token thresholds, the threshold
  set for precision; `langid` adjusted for noisy machine text only if the
  numbers call for it and only with K1's tests unchanged; German pages and
  lines by collection and convolute in `reports/kurrent/page-lang.md`.
  One read-only pass over the store (the text of 13.5 M lines). Checkpoint
  A. *Task 2:* an additive `runs.scope` column (`_migrate`), set by the
  writer of Task 4 to `de`; one precedence, `run_rank`, in `db.py` — a
  scoped run's row beats an unscoped run's row on the same (page_id,
  line_seq), among runs of the same kind the higher run id wins — used by
  `latest_lines`, `line_summaries_by_page` (the `NOT EXISTS` probe reads the
  rank through a join on `runs`, no JSON), the index documents, the API, the
  exports and the stats; the per-line fallback of the amendment follows (a
  line the scoped run did not write shows the newest unscoped row); a
  `page_lang` table (page_id, lang, score, n_tokens, run_id) read by
  `search/documents.py` for the index's `lang`; the cost of reading mixed
  pages whole measured on the letter pool's mixed letters; tests on fixtures
  for every reader; the probe timed on the synthetic work as its docstring
  did. Checkpoint B. *Task 3:* `/mnt/d/leibniz-train/k4/` behind
  `data/kurrent/k4-readings`; the crops under 80 px counted among the
  German lines; a 2,000-line pilot with `k3-trocr --kv-cache` at batch 16
  under `/usr/bin/time -v` for the host memory and the pace, the figure in
  days from Task 1's count; then, after the go, the whole job under
  `systemd-run --user --scope -p MemoryMax=6G` and nohup with a log on D:,
  the guard watching the card, nothing else of the session's beside it.
  Checkpoint C. *Task 4:* the gate (met on K3's numbers); the backup copy to
  D: with its SHA-256; the go; `leibniz enrich page-lang --write` (the table,
  a runs row of stage `enrich`) and `leibniz pipeline import-readings` (one
  runs row of stage `recognize`, model `k3-trocr@runs-615-epoch-5`, scope
  `de`; one row per non-empty reading with the v1 row's geometry, status
  `machine`, lang `de`; idempotent, resumable by page); the counts and the
  store's size after. Checkpoint D. *Task 5:* About (EN, DE) and `llms.txt`
  name READER and the letter-pool number and what it was measured on; the
  outputs table; the provenance line checked; the language filter opened if
  the operator says so on Task 1's numbers; tests and the browser checks.
  Checkpoint E. *Task 6:* the serving copy to D:, the box commands and the
  `curl -su USER …` checks for the operator, the entry completed, the push
  and the compare URL. Expected days: Task 1 and Task 2 within the day; the
  reading's days come from the pilot and Task 1's count (K3 measured 152 ms a
  line for READER with the cache on this card, 13.3 h for K2's 310,831
  lines; the German pages beyond the census's 5,874 are not yet counted).

### LT1 — the page-level LLM test (2026-10-28) ✅ Task 0 · ✅ Task 1 (Checkpoint A) · ✅ Task 2 (Checkpoint B) · ✅ Task 3 (the report's code, the runbook, the hand-over) · ✅ Part B (the operator's run, 2026-10-29/30)
- **Part B, the operator's run (2026-10-29/30).** After #56 the second
  checkout on main with numpy added; `page-fetch` 54 files; the three dry runs
  (134 calls a model, every image size known: 2.81, 2.41 and 14.98 USD
  estimated at 1,500 output tokens a page) and the three reads in one detached
  loop under a 20 USD cap a model: Claude 132 read and 2 resumed, every page
  ok; the logged usage 1.43, 1.06 and 11.43 USD (output tokens 552 to 975 a
  page, thinking included). The pool scoring first (the store free of
  writes), then, after K4's writes, `page-lines` (1,878 lines from the val
  XML) and the kraken run on them: **26.29 % (25.13–27.48)** against B1's
  7.95 % on the same lines as the dataset cut them — the audit crop, a padded
  polygon mask, is not the extraction the model was trained on, so the kraken
  row of the PHILIUMM table is quoted from B1 and the measured gap is LT1b's
  first item. `page-score --set philiumm` without the dump, the models named
  (the scorer had read the dump as readings and failed on `page_id`); the
  report rendered; `reports/htr/` committed on `lt1-results` and carried to
  the operator's pull request with this entry. The numbers are in Current
  state and Key numbers; the report's two caveats stand (27 and 98 pages; the
  pool's references are checked letters, not a random sample).

- **Setting.** A cloud session on the branch it was given,
  `claude/kind-tesla-xhk9ac`, from main at `c0b1a45` (#55 merged; `git merge
  origin/main` already up to date). No `data/inventory.sqlite`, so fixtures
  throughout; `.venv-cloud` made with the web, gt and release extras (pyarrow
  comes with release) and **numpy added** (`VIRTUAL_ENV=.venv-cloud uv pip
  install numpy`): the pool metric's infix alignment is a numpy row and its
  tests skip without it. Baseline before any change: `ruff check` clean,
  `ruff format --check` 266 files formatted, **pytest 1016 passed, 1 skipped**
  (the numpy skip) in 47 s. No API key in the session; every API path is tested
  against scripted replies and recorded fixtures. Network used, politely: the
  Hub's dataset info and file tree (three GETs), one val page's JPEG and XML
  from the Hub (two GETs, 2,323,554 and 55,089 bytes), two pages from the
  public mirror (two GETs), one Hub listing GET by `page-list` (cached under
  `data/philiumm/hf-files.json`), and the documentation pages of the three
  APIs; nothing sent to any API.
- **Task 0, the facts.** (a) *The PHILIUMM parquet*: the dataset's features are
  `text` (string) and `image` (Image) and nothing else — no page, no line
  order — over the splits `train_clean` 18,254, `train_noisy` 43,372, `val`
  1,878 rows; so a page reference cannot be rebuilt from the parquet. The Hub
  repository carries the pages themselves: `val/` holds **54 files, 27 JPEG +
  PAGE XML pairs** (eScriptorium exports, `TextRegion` with SegmOnto types,
  `TextLine` with `Coords`, `Baseline` and `Unicode`); `LH_1_2_1_0004r.xml`
  names its image 2,482 × 4,214 px and carries 104 lines with text in a main
  zone and margin zones. The page reference is therefore the val XML's lines in
  document order (`align/pagexml.py`, the P1 reader), the empty ones dropped.
  (b) *The mapping*: `reports/philiumm/heldout_pages.csv` has 1,475 rows
  (1,155 noisy, 290 clean, 30 val); the 30 val rows come from 23 files — 16
  files map to one store page each, 7 are openings (`LH_35_1_27_0009v-0008r`)
  mapped to two store pages; 4 val files are not in it (2 eScriptorium-id
  names the P1 matcher could not parse, 2 without a page). Real images exist
  for every val page without the store: the Hub's own `val/*.jpg`, and they
  are the GWLB's derivatives — the Hub's `LH_1_2_1_0004r.jpg` and the mirror's
  `00068282/0007.jpg` (its store page) are both 2,482 × 4,214 px. So the
  PHILIUMM set is the whole val split, 27 pages, their image from the Hub
  (`page-fetch`; on the desktop too), the openings read as a left and a right
  half (one column at a time, as the protocol says; the XML's lines split by
  their x-centre against the page's midline). Nothing is left out for want of
  a mapping; the prompt's 50 is not reachable from the held-out split. (c)
  *The pool set*: 134 letters (67 L, 65 K, 2 k), 67 selection / 67 test; 386
  page slots, 380 distinct pages (six pages carry two letters), 35 works;
  18,815 recognised lines, 325,624 reference characters; 2.88 pages a letter
  on average, 8 at most; `letterpool_eval.machine_text` attaches readings by
  line id to the store's lines in reading order and joins the texts by
  spaces — the page kind attaches by page id instead (below). (d) *The APIs*
  (their documentation read 2026-10-28): Gemini has no bare `gemini-3.1-pro`
  — the id is **`gemini-3.1-pro-preview`**, `thinking_level` low | medium |
  high, default high, no off; **`gemini-4-argon` exists** (the models page
  lists it as stable), thinking_level low | medium | high, no off; on the
  OpenAI-compatible endpoint the level travels in `extra_body.google.
  thinking_config` and cannot be combined with `reasoning_effort`; temperature
  is accepted there (B1 sent 0.0 live). Claude: **`claude-fable-5-1`**;
  thinking is always on and `{type: "disabled"}` returns a 400, so "without a
  thinking block" is not available — `output_config.effort` *low* is the
  floor; `temperature` is rejected by the current models; images are 28 × 28
  px patches, the Claude 4.7+ tier fitting the image into a 2,576 px long
  edge and 4,784 visual tokens (a 1,178 × 2,000 page: 3,096 tokens);
  `stop_reason` names `refusal` and `max_tokens`. OpenAI: `reasoning_effort`
  values are model-dependent (`none`, `minimal`, `low`, …; gpt-5.5 takes
  `none`, GPT-6 Astra does not), so the engine steps down a chain on a 400.
  (e) *Pricing rows added*: `ANTHROPIC_PRICES` (claude-fable-5-1 10.00 /
  50.00; opus-5-5 4.00 / 20.00; sonnet-5-5 2.00 / 10.00; haiku-5-5 0.10 /
  0.50 — the first Anthropic cost accounting in the harness),
  `gemini-3.1-pro-preview` 2.00 / 12.00 (prompts of at most 200k tokens),
  `gemini-4-argon` 2.00 / 10.00 (through 2026-11-30; 4.00 / 20.00 from
  2026-12-01: a run after that date re-derives the cost from the logged
  usage). The plan and its cost are in Current state; the preamble's item 6
  applies (a cloud session records the pre-flight and proceeds).
- **Task 1, the page reader (`htr/pageread.py`, `htr/engines.py`).** The page
  list CSV: `page_id, set, source, column, letter_id, hand, half, work_id,
  seq, ref` (source `store` → the image cache's layout `{work}/{seq:04d}.jpg`
  under `--images` or the public mirror; `hf:val/<file>.jpg` → the Hub;
  column `whole | left | right`). `prepare_image` crops the half, downscales
  so the long side is at most 2,000 px (never up), re-encodes JPEG q92: the
  mirror's 2,482 × 4,214 page became 1,178 × 2,000 px, 790,097 bytes; the
  wide `DE-611-HS-859659:0001` (4,896 × 4,179) 2,000 × 1,707 px, 1,034,421
  bytes. `ImageStore`: a local root first, then the cache, then one polite
  fetch kept under `--cache`. `read_pages`: one call a row, the reply
  classified `ok | refused | runaway | empty` (`error` for an API error, a
  4xx not retried), the failed statuses retried once, the JSONL row carrying
  page, set, column, letter, hand, half, engine, model, the settings (prompt
  SHA-256, max_tokens, temperature, the reasoning setting, the long side),
  the image sizes sent, the text and its lines, the status and the first
  attempt's, the stop reason, the usage (input, output, reasoning), the cost,
  the milliseconds; resumable, `--redo failed | all`; the cost cap stops the
  run before the next call. `plan_read` (the dry run) counts the calls and
  estimates the input tokens by each API's documented image rule on the real
  size where the image is on disk (else 1,333 × 2,000 assumed) plus an output
  assumption the operator states. The engines: `ApiReply` and `classify_stop`
  shared; `AnthropicEngine.reply` with `effort`, no temperature, usage and
  `cost`; `OpenAIEngine.reply` with `reasoning_effort` and the chain,
  `finish_reason`, `completion_tokens_details.reasoning_tokens`;
  `GeminiEngine` with `thinking_level`; the three image-token rules
  (`anthropic_image_tokens`, `gemini_image_tokens`, `openai_image_tokens`).
  `build_engine` sets the page protocol per engine; `echo` is the offline
  stub. Checkpoint A: 10 engine tests and 16 reader tests, all offline.
- **Task 2, the scoring (`htr/pagescore.py`, `align/letterpool_eval.py`).**
  (a) `philiumm_refs` reads `<stem>.xml` per list row (a column's lines by
  x-centre); `score_page` normalises both sides under the four policies
  (`philiumm` the headline) and takes the edit distance of the page's lines
  joined by spaces (a numpy row for long strings, checked against the
  harness's DP); `pooled_pages` with the B1 bootstrap over pages, `charge` and
  `omit` for the failed pages; `aggregate_pages` per model and policy. The
  kraken model: `cut_page_lines` cuts every val line with text through the
  audit's crop machinery (polygon masked, no downscaling) into Kraken's image +
  `.gt.txt` pairs named `<stem>__<index>`, `bench run DIR --engine kraken
  --out DUMP` reads them, `kraken_page_texts` joins the dump back into pages
  (B1's dump cannot stand in: its ids are parquet rows and name no page). (b)
  `PageReadings` in `letterpool_eval`: `machine_text(lines, readings,
  page_ids=…)` concatenates the pages' lines in order for the page kind (a page
  read empty is one empty line, so it still counts), `score_set` and
  `selected_scores` pass the letter's page ids, `reader_info` counts a page
  reader's lines and reports no per-line pace; `pool_page_readings` builds one
  from a readings file (`page:<model>`), `score_pool` scores the drawn letters
  under v1, the line readers on disk (k3-trocr, k3-kraken, the Bern model) and
  the page models with `build_result`'s pieces, then the same letters without
  those any page model failed on (the paired "left out" view). (c) The diff:
  `align_lines` (Needleman–Wunsch over lines, a pair costs 1 − similarity, a
  gap 0.35, so two lines under 30 % similar are not paired), `diff_lines`
  counts both right, only a / only b right, both wrong, near (≤ 10 % CER),
  invented, dropped, the length ratios; on PHILIUMM against the kraken dump's
  lines, on the pool against k3-trocr with the factory's aligner cutting the
  letter's text into k3-trocr's accepted lines as the reference lines (the
  declined lines counted). Checkpoint B: 11 scoring tests, the pool one on the
  fixture store with a page reader that fails one page.
- **Task 3, the report and the commands.** `htr/pagereport.py` renders
  `reports/htr/page-llm.md` + `.json` from `page-llm.scores.json` (numbers
  only; the committed K2b/K3 whole-set rows read from their JSON and shown
  beside the subset rows; B1's line-crop table for scale). The commands:
  `bench page-list` (the two lists), `page-fetch` (the Hub's val pages, one a
  second), `page-read`, `page-lines`, `page-score --set philiumm | pool`
  (`--split test` is read as `val` and recorded), `page-report`. Tests: 1016 →
  **1060** passed (the numpy skip now runs), ruff clean, 272 files formatted.
- **Not done here (Part B, the operator's).** The API reads, the kraken line
  run, the two scorings and the report's numbers: the runbook under Next.
  `reports/htr/page-llm.md` does not exist until `page-report` runs on the
  desktop; no number of the test exists yet.

### K3 — a Leibniz Kurrent model (2026-10-21/24) ✅ Task 0 · ✅ Task 1 (Checkpoint A) · ✅ Task 2 (Checkpoint B) · ✅ Task 3 (Checkpoint C: kraken and TrOCR) · ✅ Task 4 (Checkpoint D) · ✅ the operator's choice (2026-10-26: TrOCR)

- **The operator's decision on the prerequisite (21 October), verbatim:**
  "The prerequisite "K2's audit sheet judged": the operator decides to go
  without, conditionally. The sheet (data/kurrent/k2-audit.html, 200 lines,
  half in Leibniz's own hand) is being sent to a judge at the Leibniz-Edition;
  no verdict exists yet." Its consequences, from the same note: (a) every
  training line tagged in the manifest by hand (Leibniz's own under W5's
  strict rule, against the rest) and by reader (K2's reader rows against the
  v1-minted rows); (b) a cheap screen for misplaced lines before any
  training — per K2 line the alignment confidence and the ratio of the
  minted text's length to the Bern reading's length, by hand group against
  the band the v1-minted Latin and French lines occupy; the share outside the
  band per group and the twenty worst line ids into this entry; more than
  about one Leibniz-hand line in ten outside the band stops the phase at
  Checkpoint A; (c) one more ablation for the stronger candidate, the same
  training without a flagged class, run only if a verdict arrives or the
  screen flags a class, else recorded as planned; (d) the model cards state
  that the precision of the German training lines is unmeasured, the audit
  pending, with the screen's figures beside the statement.
- **Setting (Task 0).** The operator's desktop, the WSL checkout
  `/home/evana/LeibnizLegible`, a Claude Code session; main at `af8a1b9`
  (#48, K2 merged) and `origin/main` the same; `k3-kurrent-model` created
  with `git checkout -B k3-kurrent-model origin/main`, the name the
  operator gave. The tree clean apart from the operator's own untracked
  files (`logs/`, `*.log`, `resume-run.sh`, `.python-version`, the two
  gt-audit HTML sheets), left alone. GPU: GTX 1660 Ti, driver 610.57.01,
  1,142 MiB of 6,144 MiB held by Xwayland, nothing else on it. Disk: `/`
  1007 G with 895 G free, `/mnt/d` 932 G with 412 G free; RAM 9 GiB, 16
  cores. `.venv-k1`: Python 3.12, torch 2.12.0+cu130 with CUDA available,
  transformers 5.12.1, kraken 7.0.3, lightning 2.6.1, safetensors 0.7.0,
  pyarrow 25.0.0, no accelerate. Baseline in `.venv-k1`: `ruff check`
  clean, `ruff format --check` 231 files formatted, **pytest 866 passed, 1
  skipped** in 38.5 s. The backup chore of the store may be running in
  another window (the operator's note); it holds no lock.
- **Prerequisites, each verified (Task 0).** K2 merged: `gt_lines` holds
  **50,720 rows whose source names `reader trocr-kurrent-xvi-xvii`**
  (333,680 rows in all, the store 17,094,205,440 bytes, modified 2026-10-21
  07:36, WAL empty, opened `mode=ro`), `reports/kurrent/k2-mint.md`
  present, run 609 the last runs row. K2b merged:
  `reports/kurrent/letterpool-testset.csv` (134 letters), the texts under
  `data/kurrent/letterpool/` (`testset.jsonl`), the metric in
  `align/letterpool_eval.py` with its checksum check. The audit sheet: the
  operator's decision above. C3 has not landed (no `train-set` tool in the
  code), so Task 1 builds `leibniz htr train-set` under the `bench` group
  for both.
- **The training rows, counted read-only (Task 0).** On the 2,148 German
  records: **60,163 rows on 1,447 records, 3,854 pages** — 50,720 the
  reader's, 9,443 from the v1 text; by hand under the strict rule
  **Leibniz's own 2,612** (2,093 reader, 519 v1, on 51 records), the
  author's own hand but not Leibniz 1,973 (61 records), partial 15,746
  (422), other 39,832 (913); by stratum heavy_revision 40,641 ·
  light_revision 19,057 · scrap 406 · fair_copy 59; 44.5 characters a line
  on average (median 46). **None of the 3,854 pages is among the 1,472
  held-out pages of `reports/philiumm/heldout_pages.csv` or the 380 pages
  of the letter pool's set.** The works are 158 Briefwechsel and 95
  Handschriften convolutes: no Marginalien. The C2b exclusions that apply:
  `math` 32 rows (4 reader, 28 v1) and `bracket` 1,149 rows (883 reader,
  266 v1), the v1 rows from `data/gt/flags.jsonl`, the reader rows from the
  same patterns run over their text (`audit_patterns.is_math_dense`,
  `has_bracket`). The 200 lines of K2's audit sheet are all among these
  rows, as are 20 of the 199 PHILIUMM-judged lines (German pieces minted
  from the v1 text): both sets stay out of training and of checkpoint
  selection, tagged `audit`, so the judges' verdicts remain a sanity set.
  The text is NFC (60,160 of 60,163 rows); 813 rows end in `¬`, the
  scribe's line-end mark the aligner keeps since C2b; a few dozen carry
  symbols the OCR layer leaked (`©`, `™`, `■`, `•`, `®`), to be excluded
  and counted. The PHILIUMM codec (178 code points, NFD: combining marks,
  no precomposed letters) lacks, in NFD, 32 of the training text's 131
  distinct characters — none of them a letter but `¬`, the em dash, `*`,
  the apostrophe and typographic quotes, `æ`/`Æ`/`œ`; the umlauts decompose
  onto `u`/`a`/`o` + U+0308, which it has; `ß` it has; the edition text has
  no long s (0 of 60,163 rows) — so the codec grows by `--resize union`.
  The Bern checkpoint (`dh-unibe/trocr-kurrent-XVI-XVII`, snapshot
  `a6bb6086`): a ViT encoder at 384 px (768 hidden, 12 layers) and a
  12-layer decoder (d_model 1,024, vocab 50,265, untied head), 333.9 M
  parameters, 1.3 GB in fp32 as K2 loaded it; its readings are NFC (49,912
  of the first 50,001).
- **Task 1, the training set (Checkpoint A;** `htr/trainset.py`, `leibniz
  bench train-set`, +9 tests; `reports/kurrent/k3-trainset.md` + `.json`, the
  frozen validation pieces `k3-val-pieces.csv`; the crops and `manifest.jsonl`
  under `data/train/k3/`, gitignored**).** One tool for K3 and C3 under the
  `bench` group (C3 has not landed its own): the open-bucket rows of the
  records given (K3: the census's German pieces), each tagged with its record,
  volume, stratum, hand (`catalog/hands.py`: own / partial / other, and the
  strict rule's *Leibniz's own* against the rest), the reader whose text it
  was aligned on (`reader_from_source`: K2's reader rows against the v1-minted
  rows), its alignment confidence, the text it was aligned on and the screen's
  figures, then the exclusions, the screen, the split, the crops. *The
  selection:* **60,163 rows on 1,447 records and 3,854 pages** —
  trocr-kurrent-xvi-xvii 50,720, v1 9,443 by reader; Leibniz's own hand 2,612
  lines on 51 records, the rest 57,551. *Exclusions*, the first reason that
  applies (held-out page, letter-pool page, Marginalien, math, bracket, noise,
  audit): **1,434 rows** — audit 215, bracket 1,154, math 32, noise 33 (by
  reader: audit/trocr-kurrent-xvi-xvii 205, audit/v1 10,
  bracket/trocr-kurrent-xvi-xvii 889, bracket/v1 265,
  math/trocr-kurrent-xvi-xvii 4, math/v1 28, noise/trocr-kurrent-xvi-xvii 26,
  noise/v1 7); the `bracket` flag now also fires on the edition's angle
  brackets, `noise` on symbols the OCR layer leaked (`©`, `®`, `™`, `■`, `□`,
  `•`), `audit` keeps K2's 200 sheet lines and the 20 PHILIUMM-judged lines on
  German pieces out of training and of checkpoint selection (a sanity set once
  judged). No row sits on a held-out page, a pool page or a Marginalien work.
- **The screen (Task 1, the operator's note (b)).** The band the **273,517
  v1-minted Latin and French rows** occupy: the ratio of the minted text's
  length to the v1 reading's (whitespace collapsed) between **0.80 and 1.44**
  (the central 95 %; median 1.00), the alignment confidence at or above
  **0.733** (median 0.950). The reader's lines that no flag excluded, by hand
  group, against it — **Leibniz's own hand: 1,949 lines, 145 outside (7.4 %:
  conf_low 52, ratio_high 66, ratio_low 35); the other hands: 47,647 lines,
  3,306 outside (6.9 %: conf_low 1,556, ratio_high 1,116, ratio_low 988)**;
  ratio quantiles p2.5 / median / p97.5 0.83 / 1.00 / 1.53 for his hand, 0.83
  / 1.00 / 1.41 for the rest. For comparison the v1-minted rows of the same
  German records: 1,583 of 9,133 outside (17.3 %). **The stop rule (10 % of
  the Leibniz-hand lines) is not triggered.** The twenty worst reader lines,
  every one a minted slice of 8 to 21 characters on a reading of a single
  character at confidence 1.000 (the aligner's matched fraction is over the
  reading's characters, so a one-letter reading that matches scores 1.0 and
  places an edition slice on no evidence; all twenty are in other hands):
  `DE-611-HS-970451:0002:056` (other, heavy_revision, ratio 21.0, conf 1.000,
  21 / 1 chars); `DE-611-HS-867509:0122:009` (other, heavy_revision, ratio
  15.0, conf 1.000, 15 / 1 chars); `00068422:0004:032` (other, heavy_revision,
  ratio 14.0, conf 1.000, 14 / 1 chars); `00068430:0029:036` (other,
  heavy_revision, ratio 14.0, conf 1.000, 14 / 1 chars);
  `DE-611-HS-856291:0012:037` (other, heavy_revision, ratio 14.0, conf 1.000,
  14 / 1 chars); `DE-611-HS-960158:0136:031` (other, heavy_revision, ratio
  13.0, conf 1.000, 13 / 1 chars); `00068593:0053:000` (other, light_revision,
  ratio 13.0, conf 1.000, 13 / 1 chars); `DE-611-HS-971300:0068:026` (other,
  heavy_revision, ratio 11.0, conf 1.000, 11 / 1 chars);
  `DE-611-HS-974056:0019:013` (other, light_revision, ratio 11.0, conf 1.000,
  11 / 1 chars); `DE-611-HS-959461:0081:045` (other, light_revision, ratio
  11.0, conf 1.000, 11 / 1 chars); `00068541:0005:151` (other, heavy_revision,
  ratio 11.0, conf 1.000, 11 / 1 chars); `DE-611-HS-867509:0122:006` (other,
  heavy_revision, ratio 11.0, conf 1.000, 11 / 1 chars);
  `DE-611-HS-959461:0084:027` (other, light_revision, ratio 10.0, conf 1.000,
  10 / 1 chars); `00068782:0137:111` (other, heavy_revision, ratio 9.0, conf
  1.000, 9 / 1 chars); `DE-611-HS-862243:0001:012` (other, light_revision,
  ratio 9.0, conf 1.000, 9 / 1 chars); `DE-611-HS-959461:0098:021` (other,
  light_revision, ratio 8.0, conf 1.000, 8 / 1 chars);
  `DE-611-HS-867509:0161:034` (other, heavy_revision, ratio 8.0, conf 1.000, 8
  / 1 chars); `00068823:0107:098` (other, heavy_revision, ratio 8.0, conf
  1.000, 8 / 1 chars); `DE-611-HS-867509:0120:008` (other, heavy_revision,
  ratio 8.0, conf 1.000, 8 / 1 chars); `00068430:0024:100` (other,
  heavy_revision, ratio 8.0, conf 1.000, 8 / 1 chars). The manifest carries
  each line's verdict (`screen`: `ratio_low`, `ratio_high`, `conf_low`,
  `no_reading`), so **the ablation of note (c) is triggered by the screen** —
  the class is "outside the band", 3,451 reader lines (`train-trocr
  --drop-screen`, `train-kraken --drop-screen`) — and runs for the stronger
  candidate in Task 3 if the timing allows.
- **The split (Task 1).** Kept: **58,729 lines** on 1,446 records, 3,850
  pages, 1,321 units (records joined over the pages they share, union-find, so
  no page is on both sides), 2,601,780 characters. The validation set drawn
  before any crop was cut, seed 20261021, 5 % of the lines per (stratum, hand
  group) cell, whole units: **train 55,596 lines on 3,634 pages, val 3,133
  lines on 216 pages (98 records, 92 units); pages on both sides 0**; by
  reader train / val: trocr-kurrent-xvi-xvii 46,921 / 2,675, v1 8,675 / 458;
  by cell train / val: fair_copy/other 27 / 7, heavy_revision/leibniz 2,242 /
  164, heavy_revision/other 35,331 / 1,953, light_revision/leibniz 44 / 0 (one
  unit: it stays in training), light_revision/other 17,650 / 949, scrap/other
  302 / 60. The pieces are frozen in `reports/kurrent/k3-val-pieces.csv` and
  reused by every later run (`--redraw` is the only way past it).
- **The crops (Task 1).** The disk from a seeded 1,000-line sample first:
  1,000 of 1,000 cut, **157.7 KB a line**, 9.48 GB projected. Then every kept
  line through the pilot's crop (`audit.crop_image`: the polygon masked, 12 px
  of context, no downscaling) into `data/train/k3/<split>/<page>/<seq>.png`
  with the minted text (NFC, as stored) in `<seq>.gt.txt`, eight worker
  processes, the page image decoded once: **3,850 pages, ok 58,729; 9.42 GB of
  PNGs**; `train.txt` and `val.txt` list the crops for ketos, `manifest.jsonl`
  every row with its tags and its split. **Checkpoint A.**
- **Task 2 (b), the kraken pilot** (`leibniz bench train-kraken --pilot
  --start`, `--account`; `data/models/k3/kraken-pilot/` on D: with
  `account.json`, the best weights and their validation hypotheses; the log
  `logs/k3-kraken-pilot.log`, the guard's record `k3-kraken-pilot-guard.csv`).
  `ketos train` (kraken 7.0.3, `.venv-k1`) from the PHILIUMM checkpoint with
  `--resize union` (the codec grew from 178 to 198 code points, the twenty
  added all symbols: `¬`, the em dash, the apostrophe and typographic quotes,
  `æ`, `ı`, `£`, `$`, `%`, `*`, `{}`, `\\`, `º`, a combining macron and
  cedilla — the umlauts decompose in NFD onto marks it had), `-u NFD
  --normalize-whitespace`, batch 4 with 4-step gradient accumulation, learning
  rate 1e-4 (AdamW, cosine), two loader workers, one fixed epoch over a seeded
  **20,000 lines** of the training list, under
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Two earlier attempts
  failed on memory: at batch 16 the card reached 4.8 GB and the run died at
  its first steps with `CUDA error: unknown error`; at batch 8 (and again at
  batch 4 without expandable segments) the reserved memory climbed past 5.4 GB
  over half an hour — the caching allocator fragmenting on the lines' variable
  widths — and the machine, or the guard, stopped it (the batch-8 run was the
  one running when the machine crashed; the batch-4 run was killed by the
  guard at 5,411 MiB after 4,014 batches, 16,056 lines, in 34 min). With
  expandable segments the same batch-4 run peaked at **2,776 MiB** and
  finished: **47.9 min for the epoch, validation and conversion (6.95 lines/s
  all-in; GPU utilisation 16 % on average — the run is bound by the loader,
  not the card)**; kraken's own validation accuracy 0.7676; the best weights
  scored by the project's engine on the **3,133 validation lines: CER 24.74
  %** (philiumm policy; WER 65.2 %; 49 lines exact; 46.0 lines/s at inference,
  batch 16). By hand group 32.1 % on Leibniz's own (164 lines) and 24.3 % on
  the other hands; by stratum heavy_revision 27.6 %, light_revision 18.0 %,
  scrap 9.5 % (60 lines), fair_copy 44.8 % (7); on the reader's rows 24.6 %,
  the v1 rows 25.7 %; deletions 39 % of its edits, substitutions 53 %,
  insertions 8 %; the normalization tax on this set 2.1 points (24.74 %
  against 22.68 % under the aligner's fold). Extrapolated: **one epoch over
  the 55,596 training lines ≈ 2.2 h; thirty epochs ≈ 2.8 days** (early
  stopping will take fewer). Disk: 66 MB on D: (one lightning checkpoint, the
  weights), the logs on C:.
- **Task 2 (a), the TrOCR memory probe** (`leibniz bench train-trocr --pilot
  --pilot-lines 2000 --no-pilot-val --max-mib 4000`;
  `data/models/k3/trocr-probe/pilot.json`; the loop's log
  `logs/k3-trocr-probe-loop.log`). Each setting of `PILOT_SETTINGS` on the
  same 2,000 training lines under a hard allocator cap of 4,000 MiB for the
  process (`torch.cuda.set_per_process_memory_fraction`; with Xwayland's 1.2
  GB and the CUDA context the card then holds about 5.6 GB at most, under its
  6,144 MiB, so an allocation past the cap raises an out-of-memory error in
  the process instead of spilling into host memory as WSL2 otherwise does —
  the first attempt without the cap reached 5.7 GB in one burst at the first
  AdamW step and the guard killed the whole probe). The rows: adamw-b8 out of
  memory at the cap; adafactor-b8 out of memory at the cap;
  adamw-frozen-encoder-b8 out of memory at the cap;
  adafactor-frozen-encoder-b8 8.19 lines/s at a peak of 3,988 MiB (11.3 h for
  six epochs); adafactor-grad-ckpt-b8 3.55 lines/s at a peak of 3,436 MiB
  (26.1 h for six epochs); adafactor-fp16-b8 out of memory at the cap;
  adafactor-grad-ckpt-fp16-b8 0.97 lines/s at a peak of 4,000 MiB (95.1 h for
  six epochs). So on this card the Bern model fine-tunes only with Adafactor,
  and either the encoder frozen (the fastest, 8.2 lines/s, the decoder's 248 M
  parameters trained) or gradient checkpointing (the whole model, at less than
  half the pace); half precision is slower by a factor of eight on the GTX
  1660 Ti (no tensor cores; K2 saw the same at inference) and out of the
  question. Two more settings were added for the 20,000-line epochs —
  Adafactor on everything at batch 4 with 2-step accumulation, and the frozen
  encoder at batch 16 — and the 20,000-line epochs with the validation CER run
  for the frozen encoder, the batch-4 whole model and the checkpointed whole
  model (in progress; Checkpoint B follows).
- **Task 2 (a), the TrOCR epochs** (`leibniz bench train-trocr --pilot
  --pilot-lines 20000 --pilot-save --max-mib 4000`;
  `data/models/k3/trocr/pilot.json`, the weights under
  `data/models/k3/trocr/<setting>/` on D:; `logs/k3-trocr-pilot-loop.log`).
  Two more probe settings first: Adafactor on the whole model at batch 4 with
  2-step accumulation — out of memory at the cap (3,930 MiB), so the whole
  model trains on this card only with gradient checkpointing — and the frozen
  encoder at batch 16: 10.23 lines/s at 3,956 MiB. Then the two feasible
  settings for one pass over 20,000 training lines each, the validation set
  (3,133 lines) scored after, the pilot's weights kept (the first run of these
  epochs lost its validation to an out-of-memory error: generating at batch 16
  with the per-step scores kept, beside the training state — fixed, see
  Divergences). **The frozen encoder (Adafactor, batch 8): 20,000 lines in
  40.5 min (8.24 lines/s), peak 3,488 MiB, validation CER 18.78 % (267 lines
  exact; 8.6 lines/s at inference). The whole model with gradient
  checkpointing (Adafactor, batch 8): 20,000 lines in 93.9 min (3.55 lines/s),
  peak 3,496 MiB, validation CER 13.67 % (397 exact).** The base model as it
  came read this validation set at about 30 % in the smoke run; after 20,000
  lines the frozen-encoder fine-tune is at 18.8 % and the whole-model one at
  13.7 % — five points for 2.3 times the time. Extrapolated to six epochs over
  the 55,596 training lines with a validation pass each: **frozen encoder 11.9
  h, whole model 26.7 h**; neither near the week the prompt holds the plan to.
- **Against the week, and renting (Task 2).** The plan on this GPU: the
  whole-model TrOCR fine-tune 1.1 days for six epochs (the frozen encoder
  0.5), the kraken fine-tune 2.8 days for thirty epochs at the pilot's
  loader-bound pace (early stopping will take fewer; more loader workers may
  halve it), the two sequential on one card: about four days, under the week.
  The operator's rule for a rented 24 GB card is a saving of more than two
  days; what a rental would save is not a number this session produced
  (nothing ran on such a card), and the arithmetic with its assumptions is in
  `tools/k3-rented-gpu.md` with the prices found on 21 October: the saving is
  of the order of two days, mostly on the kraken side where the pace is the
  loader's, not the card's, so the honest statement is that a rental buys the
  whole model under AdamW at a real batch size — a training this card cannot
  run at all — more than it buys days. The decision is the operator's (asked
  at Checkpoint B); nothing was rented.
- **The operator's decisions at Checkpoint B (2026-10-22), verbatim:** "go for
  the runs rows. Stay on this GPU; keep tools/k3-rented-gpu.md for a second
  round after the first results and the audit verdicts, where a 24 GB card
  would train the whole model under AdamW and the ablation together. TrOCR:
  the whole model with gradient checkpointing, six epochs, early stopping on
  the validation set. Kraken first as planned; since the GPU sits at 16 % and
  the loader sets the pace, start its first epoch with eight loader workers
  and keep them if the pace rises and memory stays under the guard, else fall
  back to four. Checkpoints on D: as agreed; state each job's expected disk
  use before it starts; report at checkpoint C after each training." So: no
  rental in this round; Task 3 trains kraken first (early stopping, eight
  loader workers to begin with) and then the whole TrOCR model with gradient
  checkpointing, six epochs with early stopping on the validation set; one
  runs row per training; the PP-OCRv6 pilot's outcome decides whether a third
  training follows.
- **The stop of 22 October (Task 3).** The kraken training was launched at
  07:36:46 with eight loader workers (runs row 610); WSL stopped entirely at
  about 07:4x (a Windows update had installed itself; the updater is off now,
  the operator says) and the session ended with it. The launch's log was empty
  and its guard had ended after one sample at 07:36:48: the guard's pattern
  carried a trailing space (`k3/kraken `) that never matches ketos' command
  line (`k3/kraken/checkpoints`), so it saw no process and quit, and ketos
  writes its log block-buffered, so an empty log minutes in is what a live
  process looks like until the machine goes down. Whether ketos died at once
  or with the machine cannot be told from the disk; the exact command line ran
  for ninety seconds in the foreground afterwards without an error. Fixed: a
  started ketos runs with `PYTHONUNBUFFERED=1` (the log shows progress as it
  happens) and the guard's pattern is `[k]etos.*k3/kraken/`; runs row 610
  closed with zero counts (nothing was trained under it); the training
  relaunched with **four loader workers**, as the operator asked ("I would
  rather be slow than crash again"), under a new runs row.
- **The second stop of 22 October, and the launch that holds (Task 3).** The
  relaunch of 07:57 (four workers, runs row 611) went down with WSL at about
  07:59: the guard's record shows the host's available memory falling from
  8,585 MiB at 07:57:57 to 78 MiB at 07:58:51, its last sample, with no swap
  on the 9.9 GB VM — because the session had started, beside the training's
  start-up, the PP-OCRv6 pilot's accounting on the CPU (a second torch process
  over 3,133 crops on all cores), the same pairing as at the 07:36 launch; a
  distro shutdown with a termination signal to every process is how WSL2 ends
  a distro whose memory is gone. The operator asked, verbatim: "WSL stopped
  again at about <time>, during your relaunch; every process got a termination
  signal first, so a distro shutdown, not a crash. Two questions before
  anything runs: (1) did you run any wsl.exe, shutdown, pkill or kill command
  in this session, and what exactly was running at the moment it stopped? (2)
  how much system memory does the full kraken training need: does ketos
  preload all 55,596 crops into RAM (the pilot's 20,000 fit; the VM has 9.9
  GB), and if so, which option keeps them on disk? Answer both and wait; do
  not relaunch anything until I say go." The answers (no wsl.exe, no shutdown;
  the two `pkill` pairs on the hung PP-OCRv6 pilot at 07:35, the first of
  which matched the session's own shell; the guards' own `pkill` on their
  pattern, which never fired on a kraken run; and the memory record above;
  ketos' path-format dataset, `GroundTruthDataset`, keeps per line only the
  image's path, box and encoded text and opens the PNG from disk on every
  access, so nothing is preloaded and the full set costs the RAM the pilot did
  — the main process and about half a gigabyte per loader worker) are in the
  session's reply of 22 October. The operator's decision, verbatim: "Your
  account is accepted and so is your proposal: kraken alone with four workers,
  nothing else of yours on the machine while it trains, the PP-OCRv6
  accounting after the training ends, the guard's host floor at 2,500 MiB, and
  ketos under systemd-run with MemoryMax=7G if systemd is enabled. WSL now has
  8 GB of swap. One ordering change: do not relaunch yet. I am running a
  catalogue import that writes the store and then makes a serving copy, about
  an hour; I will write "go kraken" when it is done. Until then do nothing on
  the machine." Done at "go kraken" (12:27): runs row 611 closed with zero
  counts (nothing trained under it; the operator's catalogue import had taken
  row 612 meanwhile); **the training launched at 12:28 as runs row 613, alone,
  four loader workers, batch 4 with 4-step accumulation, early stopping
  (`--lag 5`), expandable segments, ketos inside `systemd-run --user --scope
  -p MemoryMax=7G` (`tools/ketos-memcapped.sh`, so the kernel's OOM killer
  takes ketos before the VM), the guard at 5,700 MiB on the card and a host
  floor of 2,500 MiB, the log unbuffered; WSL has 8 GB of swap since the
  morning.** Nothing else of the session's runs while it trains; the PP-OCRv6
  pilot's accounting waits for its end.
- **The guard's kill of 13:07, and the launch that holds (Task 3).** The
  training of 12:28 (runs row 613) ran 37 minutes at a steady 2,401–2,564 MiB
  on the card, GPU utilisation 20–40 %, **3.90 batches of 4 a second — 15.6
  lines/s, 2.2 times the pilot's pace: the four loader workers pay** — 7,478
  of 13,899 batches into its first epoch (29,912 lines seen); then one sample
  read 5,763 MiB and the guard ended it at 13:07:40 (the host never under 6.8
  GB available; the abort checkpoint kept, no epoch checkpoint). One batch
  with an outlier line, not growth: the training list's widest crops reach
  4,214 px at the model's 120 px height (the 99th percentile is 1,954). Row
  613 closed with the 29,912 lines seen and nothing produced. **Relaunched
  fresh from the base at 13:11 as runs row 614**: the kraken list capped at
  2,560 px of width at height 120 (`data/models/k3/kraken/train-capped.txt`:
  55,585 of the 55,596 training lines, the 11 dropped listed beside it; the
  validation set's widest is 2,270 and stays whole), batch 2 with 8-step
  accumulation (the same effective batch of 16, half the worst-case footprint,
  little cost while the loader sets the pace), four workers, the scope, the
  guard and everything else as at 12:28 (`train-kraken --train-list`, new).
  Also found: a watcher whose command line names ketos and the checkpoints
  directory is itself a match for the guard's pattern and dies with the job;
  the watchers no longer say the word.
- **Task 3 (b), the kraken training — CHECKPOINT C** (`leibniz bench
  train-kraken --start` with `--train-list
  data/models/k3/kraken/train-capped.txt`, batch 2 × 8-step accumulation, four
  loader workers, early stopping with `--lag 5`, under
  `tools/ketos-memcapped.sh` and the guard; runs row 614;
  `data/models/k3/kraken/` on D: with `best.safetensors`,
  `best-val-hyps.json`, `val-breakdown.json`, `account.json`, the ten best
  lightning checkpoints and the abort checkpoint; the log
  `logs/k3-kraken.log`, the guard's record `k3-kraken-guard.csv`). Launched
  2026-10-22 13:11, stopped 2026-10-24 09:37 after checkpoint 36: **37 epochs
  in 44.5 h, 72 min an epoch over the 55,585 capped lines with the validation
  pass (about 13 lines/s all-in; the card at a steady 1.8–2.2 GB, utilisation
  27 %, the host never under 5.5 GB available, swap under 1.5 GB, no guard
  trip)**. Kraken's own validation accuracy by epoch: 0.7961, 0.8133, 0.8256,
  0.8316, 0.8356, 0.8392, 0.8408, 0.8417, 0.8426, 0.8431, 0.8431, 0.8432,
  0.8437, 0.8449, 0.8457, 0.8473, 0.8497, 0.8516, 0.8534, 0.8550, 0.8578,
  0.8581, 0.8601, 0.8612, 0.8624, 0.8633, 0.8642, 0.8641, 0.8644, 0.8644,
  0.8644, 0.8646, 0.8645, 0.8648, 0.8650, 0.8653, **0.8659** — gains of a few
  ten-thousandths an epoch from epoch 26 on, which reset early stopping (its
  minimum delta is zero) every time; the session recommended stopping after
  the next checkpoint and the operator answered, verbatim, "your
  recommendation is approved" (2026-10-24 morning); ketos was sent a
  termination signal after checkpoint 36 landed and `ketos convert` turned
  that checkpoint into `best_0.8659.safetensors`. The codec grew from 178 to
  203 code points (`--resize union`; the added ones all symbols and the
  edition's angle brackets). **Scored by the project's engine on the 3,133
  validation lines: CER 15.56 % (95 % bootstrap 15.05 %–16.09 %; WER 45.8 %;
  181 lines exact), against 24.74 % after the pilot's single epoch and 52.9 %
  for the PHILIUMM base on the letter pool (K2b)**; by hand group Leibniz's
  own 23.8 % (164 lines), the other hands 15.1 %; by stratum heavy_revision
  17.8 %, light_revision 10.2 %, scrap 5.0 % (60 lines), fair_copy 32.2 % (7
  lines); on the reader's rows 15.0 %, the v1 rows 18.9 %; the errors 43 %
  substitutions, 11 % insertions, 46 % deletions; the normalization tax on
  this set 1.83 points (15.56 % against 13.73 % under the aligner's fold).
  Inference 35.2 lines/s at batch 16 on this card. Runs row 614 finished with
  the 55,585 training lines. Disk: 0.6 GB on D:. The letter-pool and Dresden
  numbers come in Task 4.
- **Task 3 (a), the TrOCR training — CHECKPOINT C** (`leibniz bench
  train-trocr --settings adafactor-grad-ckpt-b8 --epochs 6 --patience 3
  --max-mib 4000`, the whole Bern model with gradient checkpointing, Adafactor
  at batch 8, learning rate 5e-5 with a linear warm-up and decay to a tenth
  over the 41,700 steps, the per-epoch validation generating at batch 8
  without scores; runs row 615; `data/models/k3/trocr/` on D: with `best/`
  (the epoch-5 weights, 1.3 GB, loadable as a reader), `last/`, `state.json`,
  `best/val-hyps.json`, `val-breakdown.json`; the loop's log
  `logs/k3-trocr-loop.log`, the guard's record `k3-trocr-guard.csv`). Launched
  2026-10-24 09:42, finished 2026-10-25 13:23: **six epochs in 27.6 h, 4.5 h
  an epoch over the 55,596 training lines at 3.42–3.47 lines/s plus a
  6.5-minute validation pass; the process at a steady 3.5 GB of the card (the
  guard's limit raised to 5,900 MiB on the way, the desktop's Xwayland having
  grown to 1.4 GB), GPU utilisation 82 %, the host never under 6.3 GB
  available, swap under 1 GB, no guard trip.** Validation CER by epoch 14.47,
  13.14, 13.35, 12.34, 11.99, 11.84 % — epoch 2 the one step back (the
  learning rate still near its peak), then the anneal; **the best at epoch 5:
  11.84 % (95 % bootstrap 11.31 %–12.33 %; 436 lines exact)**, against 13.67 %
  after the pilot's 20,000 lines and about 30 % for the base as it came; by
  hand group Leibniz's own 19.7 % (164 lines), the other hands 11.4 %; by
  stratum heavy_revision 13.3 %, light_revision 8.3 %, scrap 6.7 % (60 lines),
  fair_copy 23.0 % (7); on the reader's rows 10.9 %, the v1 rows 16.9 %; the
  errors 42 % substitutions, 21 % insertions, 37 % deletions (kraken's were 43
  / 11 / 46: the TrOCR model inserts where kraken drops); the tax on this set
  1.72 points. **Against the kraken model on the same 3,133 lines: 11.84 % to
  15.56 %; the two disagree on 2,935 lines, and on 395 of those (13.5 %) one
  of them is exactly right (TrOCR 325, kraken 70) — the number the C3
  amendment asks for.** Disk: 2.7 GB on D:. The letter-pool, Dresden and speed
  numbers come in Task 4.
- **The stop of 26 October, and PP-OCRv6 set aside (Task 4).** With the
  letter-pool evaluation of the two K3 models done (08:03), the session ran
  the PP-OCRv6 pilot's accounting: its GPU scoring failed in the kraken 7.1
  side environment for the second time (`CUDA driver error: device not ready`
  at the first convolution; the environment's torch wheel does not run on this
  card though it loads), and the fallback scoring on the CPU grew until the
  kernel's OOM killer took it at 08:30:45 — the journal of that boot: `Out of
  memory: Killed process 11584 (leibniz) total-vm:22885020kB,
  anon-rss:9371424kB` — and the distro shut down at 08:32:25, the session with
  it. Dresden had not run. The operator's decision, verbatim: "drop the
  PP-OCRv6 accounting from this phase altogether: its side environment has a
  CUDA fault and its CPU scoring is the heaviest thing left; record it as
  pending for K3b." So: the PP-OCRv6 pilot's weights
  (`data/models/k3/ppocr-pilot/checkpoints/best_0.8295.safetensors`, kraken's
  accuracy 0.8295 after one epoch over 20,000 lines in 107.6 min at batch 1 ×
  16, peak 3,009 MiB) stay on D: unscored by the project's metric; the
  account, the side environment's CUDA fault and a full PP-OCRv6 training are
  K3b's. Task 4 finishes with Dresden and the speeds for the two K3 models
  only, one job at a time.
- **Task 4, the evaluation — CHECKPOINT D** (`leibniz align letterpool-eval
  --read --readers k3-trocr,k3-kraken --reports-dir
  reports/kurrent/k3-letterpool` — K2b's metric and code, the frozen set
  verified against its checksums, nothing filtered; `leibniz bench
  kurrent-smoke --candidates k3-trocr,k3-kraken` into
  `reports/kurrent/k3-dresden/` as K1 measured and `k3-dresden-kv/` with the
  decoder's cache; `leibniz bench k3-report eval` →
  `reports/kurrent/k3-eval.md` + `.json` and the two model cards
  `k3-model-card-trocr.md`, `k3-model-card-kraken.md`; the readings under
  `data/kurrent/letterpool-readings/` and `data/kurrent/smoke-k3*/`,
  gitignored, nc). **The letter pool (134 letters, 18,815 lines, 325,624
  reference characters; CER under the philiumm policy, 95 % bootstrap over
  letters): k3-trocr 28.6 % (24.6–32.5 %), selection half 24.7 % (21.0–28.3
  %), test half 31.6 % (25.3–36.8 %), Leibniz's own hand (L) 36.7 % (31.9–41.0
  %), the correspondents' (K/k) 19.4 % (15.7–23.8 %); k3-kraken 30.6 %
  (26.5–34.5 %), selection 26.6 % (23.0–30.4 %), test 33.6 % (27.0–38.9 %), L
  39.7 % (34.7–43.9 %), K/k 20.3 % (16.8–24.6 %)** — against K2b's rows on the
  same set: v1 46.6 %, philiumm 52.9 %, the Bern model as it came 37.0 %
  (selection 34.1, test 39.2; L 49.2, K/k 23.2), trocr-hanse-xvi 35.6 %
  (evaluate only). By year k3-trocr: 1708 19.5, 1709 27.4, 1710 21.2, 1711
  32.1, 1712 11.3, 1713 25.1, 1714 29.5, 1715 35.4, 1716 28.3; k3-kraken: 1708
  22.5, 1709 31.2, 1710 22.2, 1711 33.2, 1712 15.5, 1713 26.6, 1714 30.8, 1715
  38.1, 1716 30.3. Lines read (counted per letter; an empty reading counts as
  deleted): k3-trocr 18,814, k3-kraken 14,874 — the kraken model returns
  nothing on 3,905 of the 18,445 distinct lines (the PHILIUMM base on 957),
  2,517 of them crops narrower than 80 px, a letter or two where the TrOCR
  model reads 'h', 'e', '2', 'H.'; the mint holds few such lines. The
  aligner-selected rates (labelled flattered): k3-trocr 6,295 lines accepted
  at 10.3 %, k3-kraken 5,738 at 14.6 %.
- **The validation set, Dresden and speed (Task 4).** Validation (the mint's
  own text; 3,133 lines): k3-trocr 11.84 %, k3-kraken 15.56 % (the Checkpoint
  C bullets have the breakdowns, the compositions and the tax); where the two
  disagree (2,935 lines) one is exactly right on 13.5 % (TrOCR 325, kraken
  70). Dresden (383 Kurrent Trace lines, a 1673 chancery hand, nc, numbers
  only; a sanity check, not a ranking): k3-trocr 11.9 % (10.7–13.1 %),
  k3-kraken 13.2 % (12.1–14.3 %) — against the Bern base's 7.4 % and
  PHILIUMM's 29.5 % in K1: the TrOCR fine-tune gave up some of the chancery
  hand, the kraken fine-tune learned it. **Speed on this card as K1 measured
  (fp32, no cache, batch 8, the PNG path): k3-trocr 181 ms a line, k3-kraken
  52 ms; with the decoder's cache at batch 16 (K2's setting) k3-trocr 152 ms;
  reading K2's 310,831 lines at K2's measured overhead of 2.1 ms a line:
  k3-trocr 13.3 h with the cache (15.8 h without), k3-kraken 4.6 h.**
  PP-OCRv6: set aside (the bullet above); the ablation of note (c), triggered
  by the screen (3,451 lines outside the band), planned, not run — the phase's
  GPU time went to the two trainings.
- **The choice for K4 (Task 4).** The rule as the report proposes it: the
  better letter-pool CER on the selection half, unless the faster model's
  selection-half CER lies within the better model's 95 % bootstrap interval
  there, in which case speed decides (every re-read of the German pages pays
  the speed difference). The better selection-half CER is **k3-trocr** at 24.7
  % (21.0 %–28.3 %), the runner-up k3-kraken at 26.6 %; the faster model is
  **k3-kraken** (52 ms a line against 181), within the margin (3.6 %): yes;
  **the rule's answer: k3-kraken**. Put to the operator in two sentences. **The operator's
  answer (2026-10-26), verbatim: "I agree to go with TrOCR."** — READER for
  K4 is `k3-trocr`; the K4 entry carries it.
- **Plan, as printed for the go.** *Task 1:* `leibniz htr train-set` (a
  new `htr/trainset.py`): the rows above through the pilot's crop (the
  polygon masked, the audit's padding, no downscale) into
  `data/train/k3/<split>/<page>/<seq>.png` + `.gt.txt` with a
  `manifest.jsonl` (line id, record, volume, stratum, hand group, reader,
  alignment confidence, the screen's figures, split and the reason for an
  exclusion); the disk from a 1,000-line sample first; the validation set
  drawn before any crop is cut, seeded, as whole pieces joined over shared
  pages (so page-disjoint), stratified by stratum and hand group, about 5 %
  of the lines, its piece list committed as `reports/kurrent/k3-val-pieces.csv`;
  the screen of (b) with its band from the v1-minted Latin and French
  rows; `reports/kurrent/k3-trainset.md` + `.json`. Checkpoint A, or a
  stop if the screen says so. *Task 2:* two timing pilots on 20,000
  training lines, one epoch each — (a) a plain PyTorch loop over the Bern
  checkpoint (`leibniz htr train-trocr`), first the memory of AdamW on
  every parameter, then Adafactor, a frozen encoder, gradient checkpointing
  and fp16 autocast, each with its seconds, peak VRAM and lines per second,
  the feasible ones carried to the end of the epoch and scored on the
  validation set; (b) `ketos train` from the PHILIUMM checkpoint with the
  codec grown (`--resize union`), timed the same way; the PP-OCRv6 base of
  the amendment needs kraken 7.1 in a separate environment — a load test
  there first, after a go for the install. Then the extrapolation to the
  full plan against a week, and `tools/k3-rented-gpu.md` if a 24 GB card
  saves more than two days. Checkpoint B. *Task 3:* both candidates under
  nohup with a log under `logs/` and a runs row each (a go before the
  first), checkpoints chosen on the validation set only, artefacts under
  `data/models/k3/<candidate>/`; the ablation of (c) planned. Checkpoint C
  after each. *Task 4:* the letter pool through `letterpool-eval` with the
  new models as CANDIDATES entries (the choice on the selection half,
  reported on the test half), the validation set by stratum and hand with
  the error composition, Dresden as a sanity check, the speed as K1
  measured it and the projection from K2's throughput;
  `reports/kurrent/k3-eval.md` + `.json`, a model card draft per model; the
  choice put to the operator in two sentences. Checkpoint D. Expected
  days: the pilots produce them; the only measured rates so far are
  inference rates — 87 ms a line for the Bern reader on this card (K2) and
  34 ms for the PHILIUMM model on Dresden (K1). Nothing to download before
  the pilots; the kraken 7.1 environment and any rental need a go.

### A3b — the Arbeitskatalog import (2026-10-21/22) ✅ Task 0 · ✅ Task 1 · ✅ Task 2 · ✅ Task 3 · ✅ Task 4 · ✅ the operator's first dry run read, the follow-up built · ⏳ the operator's dry run again, write, serving copy and pull request

- **Follow-up of 2026-10-22, after the operator's dry run on the master
  store (its figures the operator's: `datum` 98.4 % with 397 "other" rows,
  the nine ids, 16 hand changes of 24,907, the angle-bracket cases).**
  (1) `date_cell`: the second date's `00` month or day dropped as the first
  date's (`(93-06-00)` → `(93-06)`, `(99-00-00)` → `(99)`); the export
  carries 192 such values (176 a `00` day, 16 both) — if `datum` stays under
  99 % on the next dry run, the remaining "other" examples are the short
  `JJMMTT` values (596 rows of three to five digits, zero-filled here) and
  are to be sent back. (2) `classify`: a new class `markup` — the store's
  value equals the export's with every `<…>` segment removed
  (`website_lost_markup`; for `umfang` also a bare `°` where the export
  names the code) — counted as agreement, shown in its own column, and
  summed under the table ("The export restores text the website's parser
  lost as markup on titel N, …"). (3) `remap_missing` and the report: a
  store id the export lacks → the export's record with the same Kat.-Nr. and
  shelfmark, else the same Kat.-Nr. where unique, else the row whose
  `Identisch_mit` or `mergenr` names it (checked over the export: `mergenr`
  is an internal number on 893 rows, never an id; `Identisch_mit` names none
  of the nine); the record is compared under its new id and listed in the
  report with Kat.-Nr., shelfmark and the rule that matched; the write
  records the mapping in the run's params and the rebuilt crosswalk links
  the export's record under its own id; the CLI stops only for an id
  `gt_lines.record_id` references (printed with its proposed new id) and
  prints a line per crosswalk-only reference (remapped or dropped by the
  rebuild). (4) `names_as_website`: the export's `|`-separated names
  through `pers_norm.csv` (`korr` → `gnd`, `idhannover`), each name with
  `(KorrespDB)` and `(GND)` as the website writes them, run together as the
  website's cell reads; on the 23 live records 46 of 46 cells reproduced
  (0 mismatches), so the record carries the website's form (the dry run
  reads "exact" instead of "markers only") and the identifiers as
  `absender_gnd`, `absender_korrespdb`, `adressat_gnd`, `adressat_korrespdb`;
  without the persons table the bare strings stay. Over the export: 2,856
  distinct names, 984 cells with several; 94.3 % of the name occurrences
  have a persons row (unmatched: `?` 1,605, `(Monatl.Ausz.)`, `(Acta
  Eruditorum)`, names the table lacks). `pers_norm.csv` joins the fixture (7
  rows). (5) `Comparison.settled` no longer counts hand changes; the report
  lists every change with before and after ("listed, not blocking"); the
  sixteen are in the operator's `reports/import-access-dryrun.md` and are
  to be pasted here; K3's training set was built on the old Textart (the
  export's fuller `UEBERLFG`, with the `<…>` parts the website lost,
  decides from the write on). (6) The holdings page (`views/holdings.js`,
  i18n EN and DE): the phrase "Where Leibniz's papers are held" / "Wo
  Leibniz' Papiere aufbewahrt werden" in the title, the heading, the About
  sentence, `llms.txt`, the README and `reports/holdings.md`; the intro one
  sentence; the method section gone, its rules one footnote under the table
  (`holdings.footnote`, with the record count); the digitised-copies block
  rendered only with a refresh date; the works heading with the store's
  state (`holdings.works.state.before` / `.whole`); Browse's top line
  (`browse.holdings`, `browse.holdings.link`; the server-rendered index
  too); the credit from `legal.arbeitskatalog_credit()` (the entry's
  licence, `ARBEITSKATALOG_EXPORT_DATE` 2026-10-19, the catalogue's and the
  Arbeitsstelle's URLs; `credit` in `/api/holdings`, `katalog_credit` in
  `/api/works/{id}`) rendered by `common.sourceLine` on the holdings page
  and above the work page's records, the date in the reader's language, the
  old `work.katalog.attr` line removed, the server-rendered work page
  carrying the same line; About's catalogue block, `llms.txt` and the
  README say the records come from the Arbeitsstelle's export, not the
  website; `/holdings` in the sitemap. (7) Tests 976 → **979** (+3:
  markup, names, remap; the others extended), ruff clean; browser checks:
  **84 of 84** on the fixture store with the fixture export imported (EN,
  DE, 390 px: the heading and title, the one-sentence intro, the footnote,
  no method section, the works heading with the date, the digitised copies
  shown, the source line with its two links, the work page's source line and
  links out, the partial/whole sentences, Browse's line, About's sentence;
  axe-core 0 violations in nine states) and **32 of 32** on the fixture
  store before the import (the works heading "before the catalogue
  import", no digitised-copies block, the partial wording on the work page
  and About). Screenshots in the session's scratchpad.
- **Follow-up 2 of 2026-10-22, after the operator's second dry run (its
  figures the operator's: signatur 99.6 %, titel 99.9 %, textart 100 %, aa
  100 %, datum 98.6 % with 346 "other"; 48726 → 69490, eight ids unmatched,
  every ground-truth id present).** The 346 are two kinds: the master's
  corrections (16706, 16707: `1698` → `1700-01-14 (00-01-04)`), which stay
  "other", and the website's short second dates (17346: `(123)` for the
  export's `(00-01-23)`). `classify` gains `shortdate`
  (`website_short_second_date`: the export's second date with its dashes
  gone and its leading zeros dropped equals the website's), a column of its
  own in the table and an agreeing class; the record keeps the export's
  value. The rule is the date key's only. Tests 979 → **980**.
- **Setting and pre-flight (Task 0).** A cloud session on the branch it was
  given, `claude/adoring-volta-eogav8`, under the session preamble of 19
  October as updated on 21 October (printed with the prompt in `PROMPTS.md`);
  main at `cc02a74` (#52, G1's record merged); `git status --porcelain`
  clean; `git fetch origin main && git merge origin/main` already up to date.
  No store: the fixture store of `tests/conftest.py` and fixtures cut from
  the export. `.venv-cloud` made with `uv sync --extra web --extra gt --extra
  release --python 3.12`. Baseline: `ruff check` clean, `ruff format --check`
  241 files already formatted, **948 passed, 1 skipped** (numpy). The zip
  unpacked under `data/external/arbeitskatalog/csv/` (gitignored; the zip
  carries a `csv/` directory, flattened). **The row counts as the csv module
  reads them** (`field_size_limit` raised; multi-line fields quoted):
  `ritter.csv` **70,405** rows, **45** columns (the prompt's inspection said
  46); `pdf_url.csv` 18,995; `OV_mit_Infos.csv` 198; `OV_mit_Inhalt.csv`
  207; `Faszikel_Ms_mit_Infos.csv` 368; `Drucke.csv` **835** (the prompt said
  917: its multi-line notes fold into fewer rows); `Handschriften.csv` 124;
  `HAB.csv` 141; `Orte.csv` 451; `Orte_Hannover.csv` 367; `pers_norm.csv`
  1,569; `personen_xlsx.csv` 1,014; `Jahre.csv` 67; `Ordnr.csv` 173;
  `RegNr.csv` 206; `Tabelle1.csv` 92; `export.csv` 321; `Bogen.csv` 4;
  `Wasserzeichen.csv` 5. The pre-flight recorded, the session proceeded (the
  preamble's item 6).
- **The export, as read (Task 0/1).** `ID` 1 to 71,573, all digits, distinct.
  `URL_Ms` on 49,341 rows: `digitale-sammlungen.gwlb.de` 39,673 (39,257
  `resolve?id=`, 416 `resolve?PPN=` — the Marginalien, whose work ids are
  PPNs), `www.arcinsys.niedersachsen.de` 4,189, `resolver.sub.uni-goettingen.de`
  509, `kalliope-verbund.info` 422, `staatsbibliothek-berlin.de` 398,
  `digital.slub-dresden.de` 375, `www.archiv-bbaw.findbuch.net` 372,
  `www.digitale-sammlungen.de` 358, `opac.tib.eu` 318, `dx.doi.org` 269,
  `polona.pl` 247, `gallica.bnf.fr` 205, `soeg.kb.dk` 200 … (the table in
  `reports/holdings.md`). `JJJJMMTT` eight digits on 63,670 rows (10,841 with
  month and day `00`, 9,714 with the day `00`), empty on 6,731, four digits
  on 3, nine on 1; `JJMMTT` (the other calendar) on 13,490. `SIGN` folded
  differs from `SIGN_oL` on 920 rows; `SIGN_oL` is empty where `SIGN` is not
  on 339, both empty on 7,509. `wortlaut` on 5,348 rows (4,391 with markup).
  `Ordnungsvermerk_normiert` on 3,051 rows, 259 distinct (2,855 on `Ms`
  shelfmarks, 179 on LH, 14 on LBr); 132 of the 259 are in `OV_mit_Infos`,
  135 in `OV_mit_Inhalt`, whose `Thema` is filled for 16 of its 189 names.
  `Identisch_mit` on 5,441 rows, 2,595 of them the record itself.
  `Letzte_Aenderg` on 32,564 rows, the latest date in them 2026-08-25.
  `REIHE` empty on 23,682 rows; 35,133 rows carry a piece number, 25,012 of
  them with a row in `pdf_url` (hosts: `www.gwlb.de` 10,609,
  `leibniz-potsdam.bbaw.de` 6,038, `www.uni-muenster.de` 1,840,
  `leibniz-berlin.bbaw.de` 353, `leibnizp2.bbaw.de` 155). 39 records with a
  GWLB-collection shelfmark link a copy elsewhere (Kalliope, for LBr 98).
  **The Monadologie:** records **55406** (Kat.-Nr. 39739, `LH 4, 1, 1a Bl.
  1-6`), **55407** (39743, `LH 4, 1, 1b Bl. 1-10`) and **54786** (39744, `LH
  4, 1, 1b Bl. 1/1-16/1`), all `[La Monadologie]`, dated 17140900, assigned
  to Reihe VI; the ids 39739, 39743 and 39744 that Open question 27 quoted
  are other pieces (`LH 37, 5`, `LH 4, 7B, 3`, `LH 1, 11`). The two records
  on `LH 4, 6, 18` are 41800 (Kat.-Nr. 53823) and 59095 (81115); Leibn. Marg.
  196 is record 1585 (70248), linked by PPN 1665058609.
- **What the website renders (Task 1; 24 polite GETs on 2026-10-21, one per
  1.5 s, `id=` and `katnr=` on the extended search, parsed with
  `scrape.parse_result_table`; the pages kept in the session's scratchpad,
  the 23 parsed records committed as
  `tests/fixtures/arbeitskatalog/site_records_live.json`).** Record 71572,
  newer than the website's copy, answered nothing. The rules, as the module
  docstring states them: `Kat.-Nr.` = `KA KAT_NR/Zusatz` (`Cc2 1505/C`, `K
  22257`); `Signatur` = `SIGN` (the cell carries the double spaces the
  parser folds); `Datum` = `YYYY`, `YYYY-MM` or `YYYY-MM-DD` with a `00`
  month or day dropped (`16930006` → `1693`), nine digits verbatim, four
  digits nothing (the module keeps the year), `JJMMTT` as `(99-11-28)`;
  `Akademie Ausgabe` = `8 | 3.044`, `2 | 1.130 / a Teildr. Aufl. 2 (1988)`,
  `1 | 17.155 / Beil.zu N.154 (tlw.)`, `5 | 1250.007`, and the series alone
  (`4`, `6`) where `nr` is empty — `parse_aa_refs` reads that cell and
  `BEZUG` as it read the website's; `Sigle` = `TZ`; `Absendeort` = `ORT`;
  `Textart` = `UEBERLFG`; `Format und Umfang` = Folio/Quart/Oktav/Duodez/
  Sedez/Vigesimoquart for `FORMAT` 2/4/8/12/16/24 (a bare `°` for 32; the
  module writes `32°`), `UMFANG` `6.1999998` → `6.2 Seiten/Spalten`, `1` →
  `1 Seite/Spalte`, `0` → nothing; `Drucke`, `Bemerkungen`, `Bezüge` the
  columns with line breaks folded; the names bare in the export, `Leibniz
  (GND)` / `Oldenburg (KorrespDB) (GND)` on the website; the Wortlaut with
  `&xs+NNNNN&x{` anchors removed, apparatus notes (`<app2a>…</app2a>`)
  dropped with their content, other tags stripped, `_` a space, `^<` `^>`
  kept as angle brackets. The website shows no date for 64358 and the series
  alone for 22579 where the export has `16990000` and `5 | 1163.010`; the
  printings of 24633, 28335 and 46308 read differently in the two copies.
- **The module (Task 1).** `catalog/arbeitskatalog.py`: `read_export`
  (every table, counts), `record_from_row` (the website parser's keys —
  `katnr`, `signatur`, `titel`, `incipit`, `datum`, `aa`, `sigle`,
  `absender`, `adressat`, `ort`, `textart`, `umfang`, `drucke`,
  `bemerkungen`, `bezuege`, `gwlb_ids` — and `holding`, `url_ms`,
  `ordnungsvermerk`, `ordnungsvermerk_norm`, `ordnungsvermerk_title`,
  `_komplex`, `_epoche`, `ordnungsnummer`, `identisch_mit` (another record
  only), `last_change`, `aa_pdf`; `shelfmark_refs`, `aa_refs`, the
  Wortlaut as `transcription_snippet`), `compare_records` (per key: exact,
  whitespace-only, the website's link texts only, export adds, export
  lacks, other; up to three examples per class; the share over the records
  where the website had a value; the hand rule before and after;
  `settled` = the five keys ≥ 99 % and no hand change), `missing_references`
  (`gt_lines.record_id` where the column exists, `crosswalk`),
  `write_import` (upsert every row, clear the crosswalk, delete what the
  export no longer has, rebuild, the run), `render_*`.
  `catalog/holdings.py`: `holding_of` (the token table: 90 place names and three written in two tokens, the
  institution abbreviations and words, the connectors; `Hannover NLB` for
  the bare families and the library's own prefix; a printed witness, a
  private collection, an unstated whereabouts, no shelfmark as four
  labels), the report data and its Markdown. Tests:
  `tests/test_catalog_arbeitskatalog.py` (the cells, the fixture row by row,
  the Monadologie, **the proof against the website's own rendering**, the
  classes, the store: stop, write, idempotence, the CLI),
  `tests/test_catalog_holdings.py`, `tests/test_web_holdings.py`.
- **The fixture (Task 1).** `tests/fixtures/arbeitskatalog/`: `ritter.csv`
  30 rows (the three records of the July scrape's sample, the Monadologie,
  LH 4, 6, 18, Marg. 196, a double date, a series-only cell, printed
  witnesses, a Landesarchiv link, excerpts with Wortlaut and
  Ordnungsvermerk, holdings in London, Oxford, Göttingen, Paris, Kopenhagen),
  `pdf_url.csv` 21, `OV_mit_Infos.csv` 8, `OV_mit_Inhalt.csv` 7,
  `Faszikel_Ms_mit_Infos.csv` 8, `site_records_live.json` 23, a README with
  the attribution. Over the 21 records in both: **textart, signatur, titel
  100 %** (21 exact), **datum 100 %** (19 exact, 2 export adds), **aa 100 %**
  (20 exact, 1 export adds), incipit, katnr, sigle, ort, wortlaut 21 exact,
  absender and adressat exact or link-texts-only, umfang 20 exact and 1
  other (`°`), drucke 18 exact and 3 other, gwlb_ids 20 exact and 1 export
  adds (the PPN); hand rule 21 of 21; `Mapping: **settled**`.
- **The import (Task 2).** `leibniz catalog import-access --db … --csv-dir …
  --export-date YYYY-MM-DD [--write] [--force] [--report FILE]`: reads the
  export, maps it, prints the agreement table (and writes it to `--report`),
  checks the referenced ids and stops with them printed (exit 1) if any is
  missing, and without `--write` ends there. With `--write` it refuses an
  unsettled mapping unless `--force`, then upserts every row, clears the
  crosswalk, deletes the store's records the export no longer carries,
  rebuilds the crosswalk (`crosswalk.build_crosswalk`: gwlb_link 1.0,
  shelfmark 0.7) and prints: records written and deleted; links, records
  matched, by method; works with and without a record, the records-per-work
  bands (1, 2–5, 6–20, 21–100, 101–500, over 500) and the most on one
  work; `URL_Ms` outside the GWLB by domain and the records linking nothing.
  The run is `catalog_import_access` in `runs` with `export_date`,
  `csv_dir`, `records`, `deleted` in its params; the site reads the date
  from it. On the fixture store (two works, the fixture export): 30
  written, k-109 deleted, the two records of LH 4, 6, 18 linked by their
  GWLB links; on a store seeded with the 23 website records and three
  works: 30 written, 2 deleted (the website records not in the cut), 4
  links (two by id, one by PPN, one by id), idempotent. The piece-text
  route places 41800 on `LH 4, 6, 18 Bl. 1` as before (`pieces.place`
  unchanged); the Faszikel index finds `praefatio` as before.
- **The surfaces (Task 3).** (1) `leibniz catalog holdings [--db …|--csv-dir
  … --export-date …] --out reports/holdings.md`; the committed report is
  from the export (the works section says it waits for the store);
  `GET /api/holdings` and `/holdings` (`views/holdings.js`; EN and DE; the
  four labels for records naming no institution translated; a store under
  1,000 records shows every row, a larger one sums holdings under 20
  records as *other*; the tables scroll inside their box at 390 px); About's
  scope paragraph gains "Where Leibniz's papers lie, institution by
  institution, as the catalogue records them: the holdings page". (2)
  `_record_dict` gains `url_ms` and `url_ms_domain` (only outside the GWLB:
  a GWLB link is the work itself), `aa_pdf` (`links.edition_pdf_link`: url,
  printed page, `AA I,17`, where, terms from the registry, channel —
  `links.PDF_HOSTS`: the GWLB repository (`gwlb`), the Potsdam Arbeitsstellen
  (`potsdam`, `viii`), all CC BY-NC 4.0; Münster (`muenster`) not linked),
  `ordnungsvermerk` (name, the slip's wording, title, Komplex, epoch,
  number), `holding`; the viewer's record card lists "Digitised copy at
  {host}" and "In the Akademie-Ausgabe: {volume}, p. {page} (PDF, {where},
  {terms})" among the links out (`rel="noopener"`), the server-rendered work
  page and the piece-text header the same. (3) `/api/contents` matches the
  Ordnungsvermerk's name and title, carries it per match (the browse page
  shows "Ordnungsvermerk {name} ({title})"), and answers `katalog`
  {`records`, `refreshed`}, as `/api/stats` and `/api/works/{id}`
  (`katalog_coverage`) do; with a refresh date the browse status line, the
  work page's no-record sentence (viewer and server-rendered) and About's
  scope paragraph say "the whole Arbeitskatalog, refreshed {date}" (EN, DE),
  without one the W6 wording stands; `llms.txt` and the README say the whole
  catalogue as exported on 2026-10-21 (70,405 records) and name `/holdings`.
  (4) **Persons and places, recorded, not used:** `pers_norm.csv` (1,569
  rows: `korr` the catalogue's short name, `pers_name` with dates, `gnd`,
  `idhannover` — the Leibniz-Connection id the website's "(KorrespDB)" link
  carries —, `reihe`, `bd_nr`), `personen_xlsx.csv` (1,014: `pers_name`,
  `gndText`, `GND`, birth and death dates), `Orte.csv` (451: `ort`, a
  GeoNames id, its link), `Orte_Hannover.csv` (367: the Hanover place
  authority with GeoNames ids and 18 columns); a later step can turn the
  names on the work page into GND links and the places into GeoNames; the
  letters page keeps Bodemann's catalogue.
- **Verified (Task 4).** `ruff check` and `ruff format --check` clean; **976
  passed, 1 skipped** (+28: 16 arbeitskatalog, 7 holdings, 5 web). `leibniz
  serve --backend none --port 8765` on the fixture store with the fixture
  export imported and one record of LH 4, 6, 18 carrying a Gallica copy, a
  GWLB-repository PDF and an Ordnungsvermerk; Playwright 1.64.1 from npm in
  the scratchpad driving the preinstalled Chromium (build 1194) by
  `executablePath`, the GWLB's thumbnails answered with a stub JPEG and a
  level-0 `info.json`, axe-core 4.14.0 served from the app's own origin
  through a route: **57 checks, all passed** — `/holdings` in EN, DE and at
  390 px (heading, title, the intro with the API's count and the date, the
  first row `Hannover NLB`, the works sentence, the translated label),
  `/work/00068642` (the copy link with `rel="noopener"`, the PDF link with
  volume, page and terms, the Ordnungsvermerk row, no Münster link, the two
  export records), `/work/DE-611-HS-854976` (the whole-catalogue sentence),
  `/about` (the scope paragraph with the date, the holdings link), `/browse`
  (a filter matching nothing: the whole-catalogue status line); no
  horizontal scroll at 390 px; no console, page or request errors;
  **axe-core 0 violations in all nine states**. Screenshots in the session's
  scratchpad. The server stopped.
- **Not done here.** The master store was not opened (none in the cloud): the
  dry run, the backup, the write, the serving copy and the index rebuild are
  the operator's (Next). `reports/crosswalk.md` was not re-rendered (it reads
  the store). The persons and places tables are recorded only. Firefox and
  Safari were not run. Nothing in Key numbers was measured anew except the
  test count and the export's own figures.
- **Noticed.** The prompt's inspection counted 46 columns and 917 `Drucke`
  rows; the csv module reads 45 and 835 (the quoted multi-line fields). The
  catalogue website's Signatur cell shows `SIGN`, with the double spaces,
  not the normalised `SIGN_oL` its `sign_ol` search matches. The export is
  newer than the website's copy (its `Letzte_Aenderg` runs to 2026-08-25;
  record 71572 is not on the website), so some "other" differences in the
  real dry run will be edits, not mapping faults: read the examples.

### G1 — the Calculemus seam (2026-10-21) ✅ Task 0 · ✅ Task 1 · ✅ Task 2 · ✅ Task 3 · ✅ merged (#51) · ✅ the real pack, built and checked (the operator's run) · ⏳ the owner's choices and the copy to the box

- **Setting and pre-flight (Task 0).** A cloud session on the branch it was
  given, `claude/keen-keller-rvxmzf`, under the session preamble of 19
  October as updated on 21 October (printed with the prompt in
  `PROMPTS.md`); main at `bbc80a6` (#50, L1 merged); `git status
  --porcelain` clean; `git fetch origin main && git merge origin/main`
  already up to date, and again before this record (main had not moved). No
  `data/inventory.sqlite`: the fixture store of `tests/conftest.py`;
  `.venv-cloud` made with `uv sync --extra web --extra gt --extra release`
  (Python 3.13.16). Baseline: `ruff check` clean, `ruff format --check` 233
  files already formatted, **pytest 880 passed, 1 skipped**
  (`test_align_letterpool_eval` needs numpy). The fixture store read: its
  `lines` carry `lang` 'la' and 'fr' (one NULL), none 'de'; its three
  `gt_lines` rows name no channel, no reader and no `record_id` (two open
  `AA VI,4 N.109`, one nc `transkriptionspool`); no page has a `local_path`;
  and no readings file exists — Task 1 builds both fixtures. The preamble
  names a K3 entry to read: main has none (K3 runs on the desktop, on its
  own branch). The pre-flight recorded, the session proceeded (the prompt's
  Task 0; the preamble's item 6).
- **The fragment pack (Task 1; `src/leibniz/pack/fragments.py`, `leibniz
  pack fragments`).** Pure functions over rows and one read-only gathering
  pass (`audit_reach.open_readonly`: `mode=ro`, `query_only`).
  *The inputs:* K1's `german_pieces.jsonl` (the census's
  `asdict(PieceCensus)` rows; a record cited more than once is merged, its
  pages united and its volumes kept; the hand under the strict rule,
  `catalog/hands.is_leibniz_hand(hand, absender)`; the volume from `series`
  and `volume_label`); K2's readings (`line_id, text, conf, model, device,
  ms`); the reader-minted rows, `gt_lines` whose source names `reader
  trocr-kurrent-xvi-xvii` (`pairs.reader_from_source`), each with its
  deposit from the registry (`legal.deposit_for` over
  `pairs.channels_from_source`) and the AA label its source opens with.
  *The rules, in this order* — a line is counted under the first it fails,
  so the §70 count is of lines that would otherwise have been rows:
  `no_image` (the page has no `local_path`: the mirror lacks it),
  `no_page_size`, `twin_elsewhere` (another registration of the same scan
  carries the line: W5's twin rule, `images/twins.resolve_work` once per
  work and `own_lines(for_index=True)`, so that a spread's half is a row on
  its own page and a fold's text on its primary, each physical line once, as
  the index and the exports count it), `already_corrected` (the row
  `latest_lines` shows is not machine text: a crowd row), `no_v1_text`, `no_reading`, `empty_reading`,
  `same_text` (after whitespace normalisation), `too_short` / `too_long`
  (the longer reading against `--min-chars` 10 / `--max-chars` 50),
  `not_german` (the piece's language neither `de` nor `mixed`),
  `no_provenance` (the v1 row lacks its confidence, model or run date),
  `no_geometry`, `no_shelfmark` (neither the work nor the piece names one),
  `not_70_expired` (refused: the piece's volume is not §70-free on
  `--today`; a record cited in several volumes needs every one free). A
  page two pieces share goes, line by line, to the piece the line's
  reader-minted row names, else to the lower record id.
  *A row:* `fragment_id` (`llf-` + 16 hex of the line and its two readings)
  and `cand_id`s (`c-` + 12 hex of the line, source and text), opaque and
  stable for the same readings; `image` — `delivery` 'static',
  `page_image_url` the mirror's from `local_path` (`web/images.py`:
  `https://images.leibnizlegible.com/<work>/<seq>.jpg`), `bbox` the audit's
  crop in page pixels (`audit.line_geometry` and `audit.crop_box`: 12 px of
  context, the band about the baseline where a line has no polygon, clamped
  to the page), `canvas_id` the page's GWLB canvas or, for a page without
  one (the static works, whose pages come from the METS), the site's own
  manifest canvas (`https://leibnizlegible.com/manifests/<work>/canvas/<seq>`),
  `folio_label` the page's label or else its canvas position (as the
  manifests do); `candidates` — the v1 text (`htr_best`, `prior_conf` its
  conf) and the Bern reading (`model_alt`, its conf), whitespace-normalised,
  their order drawn per line under the seed, independent of the other lines;
  `stratum` and `lang` (`de` | `mixed`) the piece's; `machine_conf` the v1
  conf; `n_chars` the longer candidate's length; `demand_weight` 1;
  `license_bucket` 'open'; `provenance` — `image_uri` the GWLB's delivery
  JPEG (`ImageSource.source_url`), `model` the v1 row's model and beside it
  `model_alt` the reading's (`dh-unibe/trocr-kurrent-XVI-XVII`), `run_at`
  the v1 run's (finished, else started), `status` 'machine' ('aligned' on
  gold rows), `shelfmark` the work's first (else the piece's signature),
  `katalog_record_id` the reader row's record or the piece's, `aa_ref` the
  reader row's AA label (open deposit only); `attribution` — the registry's
  `gwlb-images` entry with the GWLB's name, the transcriptions' attribution
  line (`web/attribution.TRANSCRIPTIONS`), the registry's
  `trocr-kurrent-xvi-xvii` entry (MIT), and the project's own line (the pack
  CC BY 4.0, from `legal.output("transcriptions")`). *The header:* `kind`,
  `schema_version` 1, `pack_id` (`ll-fragments-<today>-s<seed>-<10 hex of
  the rows>`), `built_at`, `source {repo, git_sha, run_ids}` — the v1 rows'
  recognition runs and, where a row draws on a reader-minted row, the
  reader's `gt_factory` runs (K2: 609). The file is written whole or not at
  all (`.part`, then a rename).
  *Selection:* `audit.allocate` over the strata (equal numbers per stratum,
  a short stratum's remainder going to the others, as the audit sheets
  draw), then Leibniz's own hand: its natural share is its share of the
  eligible lines, the target the ceiling of that share of the selection;
  each stratum first takes its own share of his lines, then one more at a
  time where most of his lines are left, until the target is met. Drawn
  under `--seed`; the rows in line order.
  *Gold:* among the selected lines, those whose reader-minted row is in the
  open deposit. `fold_verdict` (the aligner's fold,
  `align/normalize.normalize`) gives `v1` or `alt` (that candidate folds to
  the minted text: its `truth_cand_id`), `both_wrong` (neither does),
  `ambiguous` (both do, as `Vnd daß` / `und daß`: no gold, the fold cannot
  tell them apart) or `unfoldable`. `gold_counts` takes the most gold rows
  the supply allows with at most `--gold-rate` of the rows gold and at most
  `--bad-gold-share` of the gold both-wrong, the both-wrong share as near
  its cap as the truths allow, drawn under the seed apart from the
  selection. A gold row is `{is_gold, truth_cand_id | both_wrong: true,
  source 'aa_aligned', align_conf}`. A line whose reader-minted row the
  registry puts in the NC deposit (the Potsdam Reihe IV PDFs, the GWLB
  repository's) is counted as withheld and lends its row neither gold nor
  its AA label. The cap on both-wrong matters twice over: the minted text
  is the edition's normalised reading, so an expansion the fold does not
  forgive reads as both-wrong; and the precision of the reader rows (K2's
  audit sheet, by hand) is not yet judged.
  *What the command prints:* the pieces, pages and lines; the skips by rule;
  the eligible lines; the selection by stratum and by hand, pool against
  pack; the languages; each candidate's lengths (min, median, mean, max)
  and the longer one's in 10-character bins; the order; the gold — the cap,
  the truths (v1 / Bern), the both-wrong, the verdicts on the selected lines
  with a reader row, the withheld; the runs; the pack id.
- **The check (Task 1; `src/leibniz/pack/check.py`, `leibniz pack check FILE
  [--judgments]`).** The two schemas mirror the contract key for key
  (`additionalProperties: false` throughout: an unknown key is drift), with
  the one addition the prompt names, `provenance.model_alt`. The validator
  enforces `type`, `properties`, `required`, `additionalProperties`,
  `enum`, `const`, `minimum`, `maximum`, `minLength`, `minItems`,
  `maxItems`, `items` and local `$ref`s, and refuses a schema that names
  any other keyword; JSON `true` is not `1`, and `NaN` / `Infinity` are
  refused. After the schema, per row: two candidates with distinct ids and
  texts, `license_bucket` 'open', a gold row with exactly one of
  `truth_cand_id` and `both_wrong: true` and its truth among the
  candidates, a non-gold row with neither, a static image with its URL,
  `n_chars` the longer candidate's length, a canonical line id whose page
  and work are the row's; across rows, each fragment and each line once;
  the header first and once. On any error: exit 1, the errors by line (the
  first 50 printed).
- **The fixtures (Task 1).** `conftest.seed_german` adds German rows to the
  fixture store, through a fixture of its own (`german_store_path`) so that
  the 880 tests before G1 see the store they were written against: a
  Handschriften work `00069377` (piece `k-4101`, AA IV,3, a draft in
  Leibniz's own hand, heavy revision; two cached pages and one not) and a
  static letter `DE-611-HS-870001` (piece `k-4402`, AA IV,4 — §70-free from
  2027-01-01 —, a correspondent's letter, `mixed`, light revision, no GWLB
  canvas); twelve lines with `lang` 'de' (one re-read by a later run, one
  baseline-only, one at the page's edge); six `gt_lines` rows — five the
  reader minted (a truth on each reading, a both-wrong, one both readings
  fold to, one in the Potsdam channel) and one minted from the v1 text.
  `tests/fixtures/pack/`: `german_pieces.jsonl` (the two pieces in the
  census's row format), `trocr-kurrent-xvi-xvii.jsonl` (ten readings, among
  them an empty one, one that differs in spaces only, one too short, one too
  long), `judgments.jsonl` (a judgment pack: three converged, one of them on
  a line the store lacks, and one both-rejected).
- **The import (Task 2; `src/leibniz/pack/judgments.py`, `leibniz pack
  judgments --in FILE [--write] [--fragments PACK] [--queue PATH]`).** The
  judgment pack is checked whole first; a pack that fails is refused and
  nothing is read from it. A dry run opens the store read-only and writes
  nothing to it; `--write` opens it for writing and inserts, in one
  transaction, one `runs` row (stage `crowd`, model
  `crowd_ab_v1@<header.game.git_sha>`, params: the judgment pack, the file,
  the fragment pack, the row count; `git_sha` this repository's) and one
  `lines` row per converged judgment — `status` 'corrected', `text` the
  winning text, `conf` the posterior, `model` the run's, `baseline`,
  `polygon` and `lang` copied from the line's latest machine row, `source`
  the judgment row as read, byte for byte. Plain inserts: no row is updated
  or deleted, and the new run keeps the crowd's row beside the machine rows
  under `UNIQUE(page_id, line_seq, run_id)`. Skipped and counted: a line
  with no machine row; a decision the store already holds (the line and
  `decided_at`, read from the crowd rows' sources — the import is
  idempotent, and with nothing new it opens no run); an earlier decision or
  a duplicate for one line within the pack; and, given `--fragments`, a line
  not in the fragment pack, a winning `cand_id` not among its candidates, a
  winning text not the candidate's word for word. The both-rejected rows
  render into `reports/scriptorium-queue.md` (`--queue`), in a dry run too
  (a report, not the store): a section per judgment pack between markers —
  the line, its page (linked, with the work's shelfmark and the folio), the
  two readings with their sources (from the fragment pack; without it, the
  store's v1 reading only), the posterior, the date; reading a pack again
  replaces its section, another pack adds its own; no contributor is named
  in it. SPECS §11 gains a dated amendment naming the commands and where the
  contract lives; NOTES B says the seam exists. No queue file is committed:
  none has been rendered from a real judgment pack.
- **Verified (Task 3).** `ruff check` clean, `ruff format --check` 241 files
  already formatted, **948 passed, 1 skipped** (+68): 31 in
  `tests/test_pack_fragments.py` (the inputs, the box, the fold, the caps,
  the gold on the fixture, the NC exclusion, the v1-minted row, the skips,
  the row's fields, `latest_lines`'s row, the §70 refusal both ways and the
  builder's raise, a scan registered twice, a crowd row taking its line
  out, the order,
  reproducibility, the selection's strata and hand share, the command end
  to end with the store's bytes unchanged); 26 in
  `tests/test_pack_check.py` (the schemas, the validator, a good pack, a
  doctored 'nc' row, nineteen other violations, `NaN` and blank lines,
  judgment packs); 11 in `tests/test_pack_judgments.py` (the dry run, the
  write beside unchanged machine rows, idempotence, a new decision,
  duplicates in a pack, the winners against the fragment pack, a refused
  pack, the queue's sections, the SPECS record). On a scratch copy of the
  German fixture store the commands ran in turn: `pack fragments` (5 rows),
  `pack check` (OK), `pack judgments` dry run (2 to import, 1 queued, 1
  without a machine row), `--write` (a run, 2 rows), `--write` again (0 to
  import, `already_imported` 2, no run). **No number from the corpus**: this
  session had no store.
- **The real pack (the operator's run on the desktop, 2026-10-21, after #51
  was merged at 16:05 EDT).** `uv run --no-sync leibniz pack fragments
  --readings data/kurrent/k2-readings/trocr-kurrent-xvi-xvii.jsonl --pieces
  data/kurrent/german_pieces.jsonl --limit 2000 --seed 20261022 --out
  /mnt/d/leibniz-packs/fragments-2026-10-22.jsonl` in `.venv-w3`: the pack
  under `/mnt/d/leibniz-packs/` rather than `packs/` (the operator's choice),
  and `--today` left to its default, so the §70 check and the pack id carry
  the run's day, 2026-10-21, while the file name says 22 (no volume changes
  its status between the two). Built 20:15:58Z in **390.0 s**, the store
  read-only; pack `ll-fragments-2026-10-21-s20261022-e86be52b1c`; 77 runs in
  its header (the v1 rows' 76 recognition runs, and 609, K2's mint). What it
  printed, and what follows from it:
  *Pieces and lines:* 2,148 records on 4,734 pages, all in the store, none
  without a cached image; 305,602 lines on them (the latest run of each);
  310,831 readings in the file.
  *Skipped, under the first rule each line failed:* `twin_elsewhere`
  **112,513** (36.8 % of the lines; corpus-wide, W5's index keeps 9,846,450
  of 13,508,625, so 27.1 % are second registrations: the German pages,
  letters among them, carry more spreads than the average); `no_v1_text`
  21,419; `empty_reading` 49; `same_text` 1,441; `too_short` 50,176 and
  `too_long` 40,551 (together 53.3 % of the 170,180 lines that reached the
  length rule); `not_70_expired` 0; every other rule 0 (no line lacked a
  reading, its provenance, geometry or a shelfmark, and none was a crowd
  row).
  *Eligible:* **79,453** (26.0 % of the lines): fair copy 55 (0.1 %), light
  revision 18,904 (23.8 %), heavy revision 59,345 (74.7 %), scrap 1,149
  (1.4 %); Leibniz's own hand 5,188 (6.5 %).
  *Selected:* **2,000** — fair copy 55 (2.8 %), light 649 (32.5 %), heavy
  648 (32.4 %), scrap 648 (32.4 %): the equal allocation took every
  fair-copy line and shared its remainder among the others; Leibniz's own
  hand 131 (6.5 %, the ceiling of his share of the pool), other hands
  1,869; de 1,939, mixed 61.
  *Lengths* (characters, whitespace normalised): v1 min 1 · median 34 ·
  mean 31.9 · max 50; Bern min 1 · median 33 · mean 31.2 · max 50; the
  longer of the two 10–19 380 · 20–29 330 · 30–39 497 · 40–50 793. The
  window bounds the longer reading only, as the prompt set it, so the
  shorter can be a single character.
  *Order:* v1 first in 1,007 rows, the Bern reading first in 993.
  *Gold:* **56 of 2,000 (2.8 %; the cap 0.25 × 2,000 = 500): truth 42 (v1
  0, Bern 42), both-wrong 14** (25 % of the gold: at its cap). Of the
  2,000, 553 lines (27.6 %) have a row K2's reader minted: **282 withheld**
  (the NC deposit: the Potsdam Reihe IV PDFs or the GWLB repository's;
  51.0 % of those lines) and **271 open**; on the 271, the fold makes one
  candidate equal to the minted text on 42 (15.5 %) — always the Bern
  reading —, both on 1, neither on 228 (84.1 %), unfoldable 0. The truths
  bound the gold: with 42 of them, 14 both-wrong rows fit under the 25 %
  cap, 56 in all.
  *The check:* `uv run --no-sync leibniz pack check
  /mnt/d/leibniz-packs/fragments-2026-10-22.jsonl` → "OK — fragment pack,
  schema_version 1", "rows 2,000; gold 56 (truth 42, both wrong 14);
  license_bucket 'open' on every row", "lang: de 1,939 · mixed 61",
  "stratum: fair_copy 55 · heavy_revision 648 · light_revision 649 · scrap
  648", "first candidate: htr_best 1,007 · model_alt 993".
  *What the numbers say.* (1) Every count adds up: the skips and the
  eligible lines to the 305,602 lines; the strata, the length bins, the
  languages and the orders each to 2,000; his hand to the ceiling of 6.5 %
  of 2,000. (2) The gold supply, not the cap, sets the gold, and two things
  shrink it: half the reader rows on the selected lines came through an NC
  channel, and the open half rarely holds an exact reading. (3) The truth
  is never v1, by construction: K2 aligned the edition text on the Bern
  reading, so the minted span follows that reading's line, and v1 reads
  German at 46.6 % CER (K2b); the calibration set is "lines the Bern model
  reads exactly", likely the easier lines. (4) On the 271 selected lines
  with an open reader row, either reading equals the edition's text under
  the fold on 43 (15.9 %): the first number of the kind NOTES B asks for
  before an A/B design ("the fraction of disagreements where either reading
  is exactly right"; it wants about 70 % on heavy revision) — biased upward,
  since these are lines the aligner accepted on the Bern reading, and
  downward, since the fold does not forgive the edition's expansions of
  abbreviations and the aligner's boundary slips count as "neither"; and
  the reader rows' precision by hand is not yet judged (K2's sheet). Read
  with those caveats, it says that most German A/B fragments will end
  both-rejected, in the Scriptorium queue. (5) The equal allocation gives
  scrap a third of the pack (1.4 % of the pool) and heavy revision a third
  (74.7 %); NOTES B would aim A/B at fair copy and light revision. The
  choices are the owner's, before the copy to the box: Open question 30
  (g)–(i).
- **Noticed, for P8 and the game** (Open question 30). What the site shows
  of a line is its latest run, so an imported judgment is what the viewer,
  the index and the exports show next — until a later machine run (C4)
  re-reads the page and shows above it. The judgment row in `source`
  carries the players' `display_name`s, and the page API and the IIIF
  annotations print `source`. `provenance.model_alt` is an addition to the
  frozen contract.

### L1 — licence registry (2026-10-21) ✅ Task 0 · ✅ Task 1 · ✅ Task 2 · ⏳ the operator's pull request and staging look

- **Setting and pre-flight (Task 0).** A cloud session on the branch it was
  given, `claude/relaxed-dijkstra-uus9rz`, from main at `aafcb05` (#49, W6
  merged); `git status --porcelain` clean; `git merge origin/main` already up
  to date. The session was handed the older preamble (8 and 14 October, the
  one naming `claude/dazzling-hopper-uxji2x` as the plan's one branch); the
  preamble of 19 October in `PROMPTS.md` says that branch is merged (#45) and
  closed and that a cloud session works on the branch it was given, and the
  repo wins (Divergences). No store: the fixture store of `tests/conftest.py`;
  `.venv-cloud` made with `uv sync --extra web --extra gt --extra release`
  (Python 3.13.16). Baseline on a clean worktree of main: `ruff check` clean,
  `ruff format --check` 231 files already formatted, **859 passed, 1 skipped**
  (`test_align_letterpool_eval` needs numpy). The operator's answers to Task
  0 came with the prompt as the note of 21 October; a cloud session does not
  wait (the preamble's item 6). Recorded verbatim, roles for names:
  - *(1) PHILIUMM's decision.* "The operator asked on 13 October: 'Can I
    confirm from our call and my previous email that you do want a CC BY NC
    for your current and future models, but as for data/code/transcriptions I
    produce, the more permissive (CC BY, Apache-2.0) terms are acceptable?'
    The project lead answered on 15 October: 'I confirm that this is what we
    intend to do in terms of CC BY.' The HTR engineer wrote the same day: 'I
    updated the license for the models only to "Creative Commons Attribution
    Non Commercial 4.0 International" (CC BY-NC 4.0).' So: their models CC
    BY-NC 4.0 from 15 October; their dataset unchanged, CC BY 4.0; their
    GitLab code's licence not stated, asked on 13 October; this project's
    outputs may stay CC BY and Apache-2.0 with their agreement."
  - *(2) The owner's scheme, as on the plan page.* "Code Apache-2.0; the
    transcriptions (the site, dataset D2, the IIIF annotations) and the open
    ground truth CC BY 4.0; the NC-derived ground truth a second deposit under
    CC BY-NC 4.0; a model fine-tuned from PHILIUMM's checkpoint (v2, and K3's
    kraken candidate) CC BY-NC 4.0. New since the prompt was written: K3
    (running now) also trains a TrOCR candidate from the Bern model (MIT) on
    K2's lines, which are open-bucket edition text, and may train one from
    kraken's PP-OCRv6 model (Apache-2.0); neither has an NC input, and the
    owner chooses CC BY 4.0 for those two if released. The GWLB letter pool
    (CC BY-NC 4.0) is used for evaluation only (K2b) and taints no model."
  - *(3)* "The apparatus-reinsertion script has not been received; its
    licence is unknown; the ask stands."
  - *(4) The Potsdam head's statement of 12 October, verbatim with roles:*
    "you are free to use them [the electronic texts of the edition, the PDFs
    of the volumes] under the CC BY-NC 4.0 licence (in particular, the 'NC'
    restriction is part of the agreement between De Gruyter and the BBAW).
    However, I can only speak for Series IV, V, and VIII, for which the
    [BBAW] is responsible. The licensing policy for the Series for which the
    Akademie der Wissenschaften zu Göttingen is responsible may be different"
    (Series I, III and VII: the research director in Hanover; II and VI: in
    Münster; the operator is writing to both). "Regarding the Arbeitskatalog
    you can use the data under the CC BY 4.0 licence."
  - *(5) Registry entries added by K1, K2b and K2 since the prompt:* the GWLB
    letter pool (CC BY-NC 4.0, version 1 of each year 1708–1716, evaluation
    only; `reports/kurrent/letterpool-sources.json`); the Bern TrOCR model
    dh-unibe/trocr-kurrent-XVI-XVII (MIT); the two fgho Hanse models (no
    licence stated, evaluated only); kraken's PP-OCRv6 (Apache-2.0, a K3
    candidate base).
  - *(6)* "Nothing merges or deploys here. If About or llms.txt change, print
    the staging line and the checks for the operator, as W6 did."
- **What the public records say (2026-10-21, 13:36 UTC; seventeen polite
  GETs of the Zenodo and Hugging Face APIs with the project's User-Agent, one
  per 1.5 s; nothing on GitHub, which this session may not read outside this
  repository).** Zenodo 21457538 (the HTR model): `cc-by-nc-4.0`, the record
  updated 2026-10-15T07:46Z, files unchanged (`FoNDUE-GD_v2_ft_Leibniz.safetensors`
  and its configs); 21537859 (the segmentation model): `cc-by-nc-4.0`,
  updated 2026-10-15T07:47Z; 21622297 (the dataset's Zenodo twin, published
  2026-07-27): `cc-by-4.0`, updated 2026-09-10; the Hub dataset
  `DenisaBumba/htr_leibniz_dataset_v1`: `cc-by-4.0`, revision `b53f531c`
  (the one P1 read); 14399779 (FoNDUE-GD v2): `cc-by-4.0`; 13788177
  (McCATMuS): `cc-by-4.0`; 15303243 (Dresden 1673, Mscr.Dresd.K.117):
  `cc-by-4.0` in the field — the package's README applies CC BY-NC-SA 4.0,
  the conflict stands — and its related identifiers name two sibling sets,
  15295553 (the TEI of the 1673 diary, `cc-by-4.0`) and 14356190 (the 1665
  diary, Mscr.Dresd.K.80, `cc-by-4.0`): the prompt's "three Dresden sets";
  18804566 (HME-Leibniz): `cc-by-nc-4.0`; 7410360 (Gallicorpora+): the
  record says `cc-by-4.0` (the prompt had the repository as CC0-1.0, which
  stays unread here); `dh-unibe/trocr-kurrent-XVI-XVII` and
  `dh-unibe/trocr-kurrent`: `mit`; `fgho/trocr-hanseXVII-kurrent` and
  `fgho/trocr-hanseXVI-kurrent`: no licence in the card or the tags.
- **The registry (Task 1; `src/leibniz/legal.py`, 31 entries, 9 outputs;
  +13 tests in `tests/test_legal_licences.py`).** `Artifact(key, name, kind,
  source, version, obtained: Terms, current: Terms | None, bucket, built,
  notes, channel, deposit, used, asked)`; `Terms(licence, seen, where,
  since)`. The entries: the PHILIUMM HTR model, segmentation model, dataset
  and alignment code (the script not received), FoNDUE-GD, McCATMuS, the two
  dh-unibe models, the two fgho models, PP-OCRv6, the three Dresden sets,
  Bullinger, the letter pool, the GWLB images, the Arbeitskatalog (CC BY 4.0
  in writing 2026-10-12), Bodemann via correspSearch, Kalliope (no licence
  stated; not used), the edition's channels — `ia` (public-domain scans,
  deposit open), `gwlb` (CC BY-NC 4.0 as published; the Göttingen series
  asked; deposit nc), `potsdam` (no terms on 2026-09-11; the NC notice seen
  2026-10-10; CC BY-NC 4.0 in writing 2026-10-12; deposit nc), `muenster`
  (written permission; not fetched), the Reihe VIII TEI (CC BY-NC 4.0 in
  writing for Series VIII; not used) — HME-Leibniz, and the tools run
  beside the repository: Gallicorpora+, YALTAi (GPL-3.0, archived 2026-04),
  dfine_kraken (its licence to be read: an operator line under Next),
  ultralytics YOLO (AGPL-3.0), the Nantes HMER code (no LICENSE file; its
  address is not in the repo). The channel entries carry the C2c re-mint's
  lines by channel from Key numbers (ia 213,520 · gwlb 52,057 · potsdam
  50,220; K2's 50,720 reader rows are not counted by channel in any
  committed report). `OUTPUTS`: code Apache-2.0; inventory CC0 1.0 with the
  records CC BY 4.0; the transcriptions CC BY 4.0 ("machine output of a model
  obtained under CC BY 4.0 …"); `gt-open` CC BY 4.0; `gt-nc` CC BY-NC 4.0;
  `model-v2` (v2 and K3's kraken candidate) CC BY-NC 4.0; `model-k3-trocr`
  and `model-k3-ppocr` CC BY 4.0 if released; the reports CC BY 4.0.
  `deposit_for(channels, bucket)`: a channel the registry does not release
  (the letter pool, Münster) or does not know → no deposit; one NC channel
  among several → nc; otherwise open for the open bucket; a row with no
  channel recorded goes by its bucket (the factory's legal gate), an
  nc-bucket row without a channel is not released.
  `pairs.channels_from_source` reads `channel ia`, `channel ia+gwlb` from the
  factory's source string. `leibniz legal licences` (table; `--full`,
  `--format tsv|json`, `--key`), `legal outputs`, `legal volumes --today`
  (`src/leibniz/legal_cli.py`). Tests: every entry has a licence string and a
  date no later than the registry's; the relicensing is a dated change; the
  nc rule of `align/pairs.py` agrees (its buckets are the registry's open
  and nc, the factory's default open bucket is what the registry says for
  every §70-free channel, the letter pool is nc and released in neither
  deposit, every channel `volumes_sources` can write is known); the deposit
  rule on ten source strings; the CLI; the checklist and SPECS carry what
  the registry says.
- **The surfaces (Task 2).** *SPECS:* §2 D3 "CC BY 4.0 (open deposit); the
  NC-derived subset released separately under CC BY-NC 4.0 as
  `leibniz-gt-nc`", D4 "CC BY-NC 4.0 for a model fine-tuned from the PHILIUMM
  checkpoint; CC BY 4.0 for a candidate with no NC input"; §7.2 names the
  registry, §7.3 the separate deposit, §7.5 the memo list's home; the
  amendment paragraph of 2026-10-21 after §7.7 records (a) PHILIUMM's
  decision, (b) the owner's scheme, (c) the edition's channels, (d) D3 as
  two deposits, (e) the NC-channel question recorded, not decided. *The
  exports* (`release/export.py`): `DATASETS` = inventory, transcriptions,
  gt, gt-nc; `iter_gt` / `iter_gt_nc` select by `gt_deposit(source,
  bucket)`; `gt_deposit_census` counts every `gt_lines` row by deposit and
  channel label; the fixture store's two rows (no channel) stay in the open
  deposit. *The cards* (`release/cards.py`): every licence line from
  `legal.OUTPUTS` (`CARD_META[..]["output"]`), a "## Licence" section with
  the registry's reason and, for the two ground-truth cards, "Channels in
  this deposit … lines: `ia` n · …", "Left to the other deposit … released
  in neither … of … rows"; the NC card's attribution names the
  Leibniz-Edition Potsdam (CC BY-NC 4.0 as stated in writing on 2026-10-12)
  and the GWLB Leibniz-Archiv; the citation line carries the bare licence.
  *The attribution line* (`web/attribution.py`, on `/api/works/{id}`,
  `/api/pages/{id}`, the manifests and the cards): "… obtained under CC BY
  4.0; published by its makers under CC BY-NC 4.0 since 2026-10-15 …
  CC BY 4.0." — the dates from the registry. *About* (`i18n.js`, EN and DE;
  `views/about.js`): the Transcriptions paragraph now opens "Leibniz Legible,
  CC BY 4.0. Machine output of a model obtained under CC BY 4.0: the PHILIUMM
  HTR model (doi:10.5281/zenodo.21457538), which its makers have published
  under CC BY-NC 4.0 since 15 October 2026, agreeing that these
  transcriptions stay CC BY 4.0."; new blocks **Ground truth** (two deposits
  by channel; the open one CC BY 4.0 on §70-free reading text from
  public-domain scans and line images under the Public Domain Mark; the
  second CC BY-NC 4.0 from the Potsdam Reihe IV files, released in writing on
  12 October 2026, and the GWLB repository's PDFs; each card says which
  channels it holds; the site shows the machine transcription only),
  **Models** (the PHILIUMM model obtained under CC BY 4.0, CC BY-NC 4.0
  since 15 October 2026; a model fine-tuned from it CC BY-NC 4.0; one
  without NC input, from the Bern model (MIT) on open edition text, CC BY
  4.0; fixed at release from the registry) and **Letters** (Bodemann via
  correspSearch, CC BY 4.0), between Transcriptions and Code. *`llms.txt`*:
  the same three lines under Licences and the registry's command. *The
  README's* licensing summary follows. *The checklist*
  (`reports/release-checklist.md`): the four exports and their checks (the
  deposits disjoint and adding up), the NC deposit's Zenodo record and Hub
  licence, the model's licence per the registry, and **§6, the lawyer-memo
  list**: SPECS §7.5's five, then irrevocability for copies already
  obtained, model output under a weights licence, ShareAlike (Bullinger,
  from K1; the Dresden text), NC terms on a PDF and §70-free text (if not,
  the NC deposit opens up), redistribution of lines derived from the Potsdam
  PDFs, §71, GPL/AGPL tools beside an Apache-2.0 codebase, the Göttingen
  series, Kalliope. A test ties the About strings in both languages,
  `llms.txt` and the attribution line to the registry
  (`tests/test_web_api.py`); the export tests cover the two deposits and the
  cards' counts.
- **Verified.** `ruff check` and `ruff format --check` clean; **880 passed,
  1 skipped** (+13 registry, +2 export, +1 About, +5 the deposit rule's
  parameters). `node --check` on `i18n.js` and `about.js`. Nothing was run
  against a browser (the About blocks are strings in the tables the W6
  session's browser checks exercised; the staging look is the operator's).
- **Not done here.** The store was not opened (none in the cloud); staging
  is the operator's (Next); GitHub-hosted licences were not read (dfine_kraken;
  the Gallicorpora+ and YALTAi repositories; the Nantes code), since this
  session's GitHub access is scoped to this repository: entries say so, and
  the operator's line is under Next; the Göttingen series' answers and the
  apparatus script are open asks, dated in the registry.
- **Noticed.** `htr/artifacts.py` and `htr/kurrent.py` still carry
  `LICENSE = "CC BY 4.0"` for the PHILIUMM model: that is the licence as
  obtained, which the registry records as such; the report they render
  (`reports/philiumm-repro.md`, B1) is a dated record and was not rewritten.
  `reports/kurrent/bootstrap-candidates.md`'s licences table says CC BY 4.0
  for `philiumm` as of 2026-10-09, which was true then. The W5 prompt is
  still missing from `PROMPTS.md` (W6's housekeeping note).

### W6 — two reader's items from the Leibniz-Edition (2026-10-21) ✅ Task 0 · ✅ Task 1 · ✅ Task 2 · ✅ Task 3 · ⏳ the operator's pull request and staging look

- **Setting and pre-flight (Task 0).** A cloud session on the branch it was
  given, `claude/busy-dirac-n30a43`, from main at `af8a1b9` (#48, K2 merged);
  `git status --porcelain` clean; `git fetch origin main && git merge
  origin/main` already up to date. No store: the fixture store of
  `tests/conftest.py`. `.venv-cloud` made with `uv sync --extra web --extra gt
  --extra release` (uv 0.11.32; Python 3.13.16, uv's default here). Baseline:
  `ruff check` clean, `ruff format --check` 231 files already formatted,
  **856 passed, 1 skipped** (`test_align_letterpool_eval` needs numpy, which
  these extras do not bring). `node` v22.22.0; Chromium build 1194
  preinstalled under `/opt/pw-browsers/`. The live API
  `https://leibnizlegible.com/api/works/1665058609`: set
  `LeibnizMarginalien`, shelfmarks `["Leibn. Marg. 196"]`, 566 canvases,
  **`katalog` empty**, browse family `Marg`; the two fixture works read live
  beside it: `00068642` (shelfmarks `["LH 4, 6, 18"]`, two records whose
  shelfmarks are `LH 4, 6, 18 Bl. 1` and `Bl. 2`) and `DE-611-HS-854976`
  (`["LBr. 464"]`, no record). The pre-flight recorded, the session proceeded
  (the preamble's item 6).
- **What the catalogue answered (Task 1, 2026-10-21; eight polite GETs, one
  per 1.5 s, with the project's User-Agent `leibniz-legible/0.1`).** The
  extended search takes `sign_ol` and runs `select where (Signatur contains
  "…")`, as its result page prints; the Signatur column's own tooltip says
  "Römische Zahlen werden als arabische wiedergegeben".
  - `…/de/extended-search?sign_ol=Leibn.+Marg.+196` → **1 Ergebnis**: id
    1585, Kat.-Nr. 70248, Signatur `Hannover NLB Leibn. Marg. 196`, "[Marg.
    in: Dal Pozzo, Maraviglie heroiche del sesso donnesco …, 1678]" — the
    record the editor's own link found and the store does not hold.
  - `…?sign_ol=LH+4%2C+6%2C+18` → **2 Ergebnisse**: `LH 4, 6, 18 Bl. 1`,
    `LH 4, 6, 18 Bl. 2` — the two records the store holds for `00068642`.
  - `…?sign_ol=LBr.+464` → **0**; `…?sign_ol=LBr+464` → **11 Ergebnisse**,
    `LBr 464 Bl. 1` … `LBr 464 Bl. 19-20`; `…?sign_ol=LBr.+164` (the prompt's
    example) → **0**. The catalogue writes the correspondence **without the
    library's period**.
  - `…?sign_ol=LBrF+1` → **600 Ergebnisse** (`LBrF 1 Bl. 3`, `LBrF 12 Bl.
    107`, …: the substring takes LBrF 1, 10–19 and 100–199 with it, the price
    of the catalogue's own match, which the editor's link pays too): the F
    series runs together, as W5 found in the records.
  - `…?sign_ol=Leibn.+Marg.+135` → **4**: `Hannover NLB Leibn. Marg. 135,
    Stück 1` to `Stück 4`; `…?sign_ol=Leibn.+Marg.+175` → **6 Ergebnisse**
    under five Signaturen, `Hannover NLB Leibn. Marg. 175:1, Stück 1`, `175:1,
    Stück 2`, `175:2, Stück 1` to `3`: the Stück and the colon forms are the
    library's too, so they stay in the search.
- **The spelling rule (`web/links.py`: `katalog_spelling`,
  `katalog_search_url`; in the module docstring beside the `id` note).**
  `split_family` names the family; the label takes the catalogue's form
  (`LH`, `LBr`, `Leibn. Marg.`, `LK`/`LK-MOW`); a comma group that is one
  Roman numeral becomes Arabic (`LH IV, 6, 18` → `LH 4, 6, 18`, `LH XXXV, I,
  17` → `LH 35, 1, 17`; `7 C` is a sub-part and stays); the groups are joined
  with `, `; a leaf reference (`Bl.`), a parenthesis, a page (`S.`) and what
  follows them are dropped, since the search is for the work; the library's
  `ZEN` shelf prefix falls away with the label; `LBr. F 1` → `LBrF 1`; the
  library's `Lh 35, 4, 14` and `LH35, 7, 3` are read as `LH`. A foreign
  signature (`Ms XXIII, 23a`, `Nm-A 605`) gives `None` and no link. Over
  `/api/works` as read on 2026-10-21: **2,184 of the 2,225 works get at least
  one link** (LH 750, LBr 1,059, Marg 370, and 5 whose `LH` shelfmark has
  Roman sub-groups and browses as "Other"); 24 works carry no shelfmark and
  17 only foreign ones; 205 carry more than one link (several shelfmarks);
  1,225 shelfmark strings are respelled for the search, nearly all by
  dropping `ZEN `, the rest Roman → Arabic, `Lh`/`LH35` → `LH`, comma
  spacing. Tests for each family, the respellings and strings of no family
  (`tests/test_web_links.py`).
- **The surfaces (Task 1).** `GET /api/works/{work_id}`: `katalog_search_urls`,
  one entry per distinct shelfmark in stored order — `shelfmark` as the
  library writes it, `query` as the catalogue spells it, `url` — empty when
  the work has none; two spellings of one shelfmark give one entry; the route
  gains an OpenAPI summary and description. The server-rendered work page
  (`_ssr_work`): ` · Search the Leibniz-Katalog for <shelfmark>` after "IIIF
  manifest" in the first paragraph and, where no record is held, the heading
  "Catalogue records (Arbeitskatalog der Leibniz-Edition, CC BY 4.0)" over
  one sentence, "No catalogue record is linked to this work yet, and this
  site holds part of the Arbeitskatalog so far; search it for LBr. 464."
  with the shelfmark linked (no link where the work has no shelfmark). The
  viewer (`views/work.js`): the link(s) after "IIIF manifest with our
  transcriptions" in the header's link list, and in the catalogue section,
  which says the browse page's sentence instead of the bare
  `work.katalog.none` (removed) — EN "No catalogue record is linked to this
  work yet. This site holds part of the Arbeitskatalog so far, not yet every
  record.", DE "Diesem Werk ist bisher kein Katalogisat zugeordnet. Diese
  Seite führt bisher einen Teil des Arbeitskatalogs, noch nicht jeden
  Eintrag." — then the link(s); `work.katalog.search` EN "Search the
  Leibniz-Katalog for {shelfmark}", DE "Im Leibniz-Katalog nach {shelfmark}
  suchen"; `rel="noopener"` and the `linklist` styling of the other links
  out. The link text shows the shelfmark as the library writes it (what the
  page shows); the address carries the catalogue's spelling.
- **The scope sentence (Task 2).** `about.what.scope`, after `about.what.p1`
  in both tables and rendered between p1 and p2: EN "The site covers the
  scans the GWLB has published of its Leibniz collections. That is not all
  of Leibniz's papers: much is not yet digitised, at the GWLB and elsewhere,
  and other institutions hold manuscripts of his, the Niedersächsisches
  Landesarchiv Hannover among them. The Arbeitskatalog der Leibniz-Edition
  records them all, wherever they lie; this site holds part of its records
  so far, and every work here links to the catalogue's own search by
  shelfmark." and its German. No numbers (Open question 28's survey is not
  quoted). The same in one line under `## Scope` in `static/llms.txt` and as
  a **Scope.** paragraph where the README describes the site. A test that
  the EN and DE tables carry the same keys, each once (none existed;
  `tests/test_web_api.py`).
- **Verified (Task 3).** `ruff check` and `ruff format --check` clean; **859
  passed, 1 skipped** (+1 links, +2 api). `leibniz serve --backend none
  --port 8765` on a seeded fixture store; Playwright 1.64.1 from npm in the
  scratchpad driving the preinstalled Chromium by `executablePath`, the
  GWLB's thumbnails answered with a stub JPEG and a level-0 `info.json`,
  axe-core 4.14.0 served from the app's own origin through a route because
  the CSP is `script-src 'self'`: **51 checks, all passed** — `00068642` in
  EN, DE and at 390 px (the header link after the manifests, its text, its
  `href` and `rel="noopener"`, the catalogue section still listing its
  records); `DE-611-HS-854976`, which has no record, in EN, DE and at 390 px
  (the sentence and the same link in the section); `/about` in EN, DE and at
  390 px (the scope paragraph second under "What this is"); no horizontal
  scroll at 390 px; no console, page or failed-request errors; **axe-core 0
  violations in all nine states**. Screenshots in the session's scratchpad.
  The server stopped.
- **Not done here.** The master store was not opened (none in the cloud);
  staging is the operator's (the hand-over under Next); Firefox and Safari
  were not run. Nothing in Key numbers was measured anew except the test
  count.
- **Noticed.** `PROMPTS.md` has no "Phase W5" section: the W5 prompt was
  never appended (W4 and K1 are; the W5 entry in this file stands).
  Housekeeping for a later session.

### K2 — German ground truth (2026-10-20/21) ✅ Task 0 · ✅ Task 1 (Checkpoint A) · ✅ Task 2 (Checkpoint B) · ✅ Task 3 (Checkpoint C) · ✅ Finish · ⏳ the operator's pull request

- **Setting (Task 0).** The operator's desktop, the WSL checkout
  `/home/evana/LeibnizLegible`, a Claude Code session; main at `436f682`
  (#47, C2c merged) and `origin/main` the same; `k2-german-gt` created with
  `git checkout -B k2-german-gt origin/main`, the name the operator gave in
  chat. The tree clean apart from the operator's own untracked files
  (`logs/`, `*.log`, `resume-run.sh`, `.python-version`, the two gt-audit
  HTML sheets), left alone. GPU: GTX 1660 Ti, driver 610.57.01, 1,450 MiB of
  6,144 MiB held by Xwayland, nothing else on it. Disk: `/` 1007 G with 895 G
  free, `/mnt/d` 932 G with 433 G free; RAM 9.7 GiB, 16 cores. `.venv-k1`:
  Python 3.12.13, torch 2.12.0+cu130 with CUDA available, transformers
  5.12.1. **The operator's backup chore was running** (since 17:35, the
  backup API from a `mode=ro` connection into
  `/mnt/d/leibniz-backups/inventory-2026-10-20.sqlite`); it reads the store
  only, and nothing has written to the store since the C2c mint at 15:00.
  Baseline in `.venv-k1`: `ruff check` clean, `ruff format --check` 224 files
  formatted, **pytest 841 passed, 1 skipped** in 37.4 s.
- **The store, read-only (Task 0).** `data/inventory.sqlite` 17,085,796,352
  bytes, modified 2026-10-20 15:00, WAL empty. `gt_lines` **315,797** rows,
  every row owned by a record (`record_id` on all), **0 rows naming a
  reader** — K2 has not run; **42,278 rows on the German records**, which is
  Task 2's "before" (the amendment: the re-mint ran first; the prompt's
  40,915 is K1's count on the C2 mint).
- **The K1 inputs (Task 0).** `data/kurrent/german_pieces.jsonl`: 2,173 rows
  (2,148 distinct records; the census lists a record once per citation),
  1,665 with recognised lines, 47 of them in Leibniz's own hand under the
  census's rule; the census summed 401,394 lines over pieces, which share
  pages — distinct pages 4,734. C2c's edition-cache bullet read: no German
  record lost or changed its text. Under today's factory (W5's folio sides,
  the rebuilt cache) the same records resolve to 4,745 pages: 1,699
  localizable (1,694 in the census), the page set the same for 1,901
  records, narrower for 217, wider for 25, otherwise different for 5; 25
  records are minted under another volume today (the volume their text came
  from). **The union is 4,807 pages with 310,831 distinct recognised lines**;
  all 4,807 page images are in `/mnt/d/leibniz-images`. The reading job
  covers the union, so the mint of Task 3 finds a reading on every line the
  factory places. The weights load: four lines of AA I,7 N.044 (katalog
  10186, `Konz.; eigh.`) read on `cuda:0` in 27.2 s including the load;
  333.9 M parameters, 1.3 GB in fp32 (allocated 1,292 MiB).
- **Plan, as printed for the go.** Task 1: `leibniz align kurrent-read`
  beside the pilot — crops cut in memory (no PNG round trip), one decode per
  page, a resumable JSONL in the pilot's row format, skips counted by reason,
  a progress line every few minutes; the profile of one batch, the sweep on
  2,000 lines at batch 8/16/32, the fp16 check on Dresden into a cache dir of
  its own (accepted within 0.2 CER points of K1's 7.4 %); the reading job
  under nohup after a go on the measured ETA (310,831 lines: 30.5 h at the
  pilot's 353 ms, 8.6 h at 100 ms, 4.3 h at 50 ms). Task 2: the dry run per
  piece, the stored mint by `record_id`, the rule, the reports, the
  side-by-side page. Task 3: the consumers decided and tested, the guard both
  ways, the source string with the reader before `katalog`; the backup check
  (the operator's copy of today, verified by size and SHA-256, proposed in
  place of a second 30-minute copy) and the go; the write; `gt-report`.
  Finish: the audit sheet in German beside English, STATUS, PROMPTS, push.
  Nothing to download or install. The operator said "go".
- **Task 1, the code** (`align/kurrent_read.py`, `leibniz align kurrent-read`;
  `htr/trocr.py`; +8 tests on a stub reader, +2 on the engine's stub;
  commit `27b7f9d`, which also carries the Task 2 and Task 3 code and its
  tests, built while the measurements ran). The pages: the census's
  `page_ids` united with the factory's resolver for the same records
  (`plan_pages`; the plan written beside the readings as `plan.json`). The
  reading: page by page, the image decoded once, each line cut in memory with
  the pilot's crop (`audit.crop_image`, the polygon masked, no downscale),
  the page's lines ordered by width so a batch's generation steps go to lines
  of like length, batches handed to the engine as images
  (`TrOCREngine.transcribe_images`: no PNG encoding and decoding), the page's
  rows appended at once (an interrupted run loses one page at most), lines
  without geometry or outside the image and pages without a cached image
  skipped and counted by reason (`<reader>.skipped.jsonl` beside the
  readings), the stats (`<reader>.stats.json`: lines total, done, read this
  run, skipped by reason, lines/h, ms/line, ETA, the engine's settings)
  rewritten and a progress line logged every 180 s. The engine gained
  `dtype="float16"` (the model in half precision), `use_cache=True` (the
  decoder's key/value cache: the Kurrent checkpoints' generation config
  switches it off, so every step re-reads the whole prefix) and per-stage
  timings; both knobs are off by default, so the readers measured in K1 and
  K2b behave as they did, and `kurrent-smoke` takes them as `--dtype` and
  `--kv-cache` for the Dresden check. `--profile` times one batch the pilot's
  way and K2's; `--sweep` reads the same sample of lines with each setting
  into scratch files and records lines/s and the GPU's peak memory;
  `--report` renders `reports/kurrent/k2-read.md` from the files.
- **The profile (Task 1).** One batch of 8 lines after a warm-up, ms per line,
  the pilot's path against K2's: page decode 15.2 (one page decoded for eight
  lines; on a full page it is a fraction of that), crop 1.6, PNG encode 11.4 →
  —, PNG decode 1.3 → —, processor 8.0 → 7.7, transfer 0.4, **generation
  250.2 → 254.6**, postprocess 0.5; **289 → 280 ms a line in all**. So the
  amendment's premise — that the model's compute is a small part of the 353
  ms — does not hold on this card: generation is nine tenths of the time, and
  the image side (which the in-memory path removes) a tenth. The reason is in
  the checkpoint's generation config: `use_cache: false`, so each of the up
  to 160 decoding steps re-encodes the whole prefix. The sweep measures the
  cache switched on and half precision, each checked on Dresden before use.
- **The sweep and the Dresden check (Task 1;** `reports/kurrent/k2-read.md`,
  `k2-read.json`; the per-setting readings under
  `data/kurrent/k2-readings/sweep/`, the Dresden runs under
  `data/kurrent/smoke-k2-{fp32,fp32kv,fp16kv}/`**).** The same 2,000 lines,
  a sample spread over the job's pages, read with nine settings; wall time
  with decoding and cutting; the GPU's peak reserved memory for the process.
  The checkpoint's defaults (fp32, no cache): batch 8 **313.9 ms** a line
  (2,418 MiB), batch 16 321.2 (3,968), batch 32 339.2 (6,412) — a larger
  batch buys nothing without the cache, since the longest line's steps are
  re-encoded for the whole batch. **The cache on, fp32: batch 8 108.2 ms
  (2,796 MiB), batch 16 93.7 (4,018), batch 32 82.2 (6,348).** Half
  precision with the cache is slower on this card (363.1 / 303.4 / 270.1 ms;
  the GTX 1660 Ti has no tensor cores). The readings agree: against the
  defaults at batch 8, the cache changes **0 of 2,000** readings at batch 8
  and 1 at batch 16 and 32 — a change of batch size alone changes 1 in 2,000
  without the cache too; fp16 changes 39 of 2,000 (2 %). **Dresden** (383
  Kurrent Trace lines, `philiumm` policy): the defaults re-read today 7.4 %
  CER (6.7–8.2), lenient 5.2 %, strict 7.5 %, 343 ms a line — K1's numbers;
  **fp32 with the cache 7.4 % (6.7–8.2), lenient 5.2 %, strict 7.5 %, 111 ms
  a line, all 383 readings identical to the defaults'**; fp16 with the cache
  7.4 %, lenient 5.3 %, 378 of 383 identical, 328 ms a line. **The setting:
  `b16-float32-kv`** — fp32, the decoder's cache on, batch 16, 10.67 lines/s,
  the fastest that fits in 6 GB (batch 32 reserved 6,348 MiB, past the
  card's 6,144 MiB: under WSL2 the allocation spills into shared system
  memory instead of failing, which is why it ran at all). **ETA for the
  310,831 lines: about 8 h 05 min**; with Xwayland's 1,450 MiB the card holds
  about 5.5 GB at the peak. Half precision is not taken (slower here, and it
  changes readings). The reading job needs the operator's go (a job over an
  hour); the command, which also resumes an interrupted run from its JSONL:
  `cd /home/evana/LeibnizLegible && export UV_PROJECT_ENVIRONMENT=.venv-k1 &&
  nohup uv run leibniz align kurrent-read --batch-size 16 --dtype float32
  --kv-cache > logs/k2-read.log 2>&1 &` — progress every 180 s in the log and
  in `data/kurrent/k2-readings/trocr-kurrent-xvi-xvii.stats.json`; the
  report afterwards with `leibniz align kurrent-read --report --chosen
  b16-float32-kv` and the three `--dresden label=path` of the runs above.
- **The reading job (Task 1; Checkpoint A).** The operator said "go"; the
  job started at 19:36 EDT under nohup with the command above, readings to
  `data/kurrent/k2-readings/trocr-kurrent-xvi-xvii.jsonl`, the log
  `logs/k2-read.log` (the operator's directory, untracked). Its first 25
  pages ran at **79 ms a line (45,351 lines/h, ETA 6 h 48 m)**, faster than
  the sweep's sample. Found in the first minutes: transformers logged a
  warning on every batch ("Both `max_new_tokens` (=160) and
  `max_length`(=128) seem to have been set"), two lines per batch, some
  19,000 batches to come — the checkpoint's generation config carries
  `max_length: 128` and the engine bounds each call with `max_new_tokens`,
  which takes precedence. Fixed in `htr/trocr.py`
  (`_drop_checkpoint_max_length`: the loaded model's `max_length` cleared,
  the generated length unchanged; +1 test), checked on CPU on a Dresden line
  (`dresden1673-0001_00000007-tr_1_tl_13`: the same text as the GPU run's,
  no warning). The job was stopped after 3,316 lines (its log kept as
  `logs/k2-read-first-start.log`) and **restarted at 19:40 EDT on the
  fixed code**, resuming from the JSONL (the stats say so: `lines_before`).
  To resume after any interruption, run the same command again; to follow,
  `grep -v '^\[transformers\]' logs/k2-read.log | tail` or the stats file.
- **The job finished (Task 1 ✅;** `reports/kurrent/k2-read.md` re-rendered
  with its figures**).** 2026-10-21 03:07 EDT: **310,831 of 310,831 lines
  read, 0 skipped**, 4,807 of 4,807 pages; the resumed run 307,515 lines in
  **7 h 26 min** wall (7 h 15 min in the engine), **41,367 lines/h, 87 ms a
  line**; the GPU idle afterwards. The readings
  (`data/kurrent/k2-readings/trocr-kurrent-xvi-xvii.jsonl`, 310,831 rows,
  every line id once; a summary beside it in `readings-summary.json`): 110
  empty readings (0.04 %); confidence (mean token probability) mean 0.755,
  median 0.815, deciles 0.43 / 0.97; 27.4 characters a line on average
  (median 27, longest 238; 4 readings of 150 characters or more, the
  160-token cap never the binding one).
- **The dry run (Task 2; Checkpoint B;** `reports/kurrent/k2-mint.md`,
  `k2-mint.json`, `k2-mint-by-volume.csv`, `k2-mint-pieces.csv`; the
  per-piece decisions `data/kurrent/k2-decisions.jsonl`, the reader's pairs
  `data/kurrent/k2-pairs.jsonl` (66,084 rows, 1,532 records), the operator's
  page `data/kurrent/k2-side-by-side.html` (40 lines, seed 20261020), all
  three gitignored**).** `leibniz align kurrent-mint` over the complete
  readings, the store read-only, 2026-10-21 03:13–04:18 EDT: **1 h 05 min**
  (3,903 s, 441 MB peak). *That is over the preamble's hour without a go:*
  a scratch dry run on the first 5,246 readings had taken 19 min and the
  session took that as the estimate; with every line read, every piece's
  alignment was real work. Nothing was written. The pieces: 2,148 German
  records, **1,668 aligned** (skipped as the census knew: 449 not
  localizable, 29 without canvases, 2 without recognised lines), 390,548
  lines on their pages (shared pages counted per piece), 390,417 of them
  with a reading (100.0 %). **Yield at the factory's gate, the same lines,
  the same thresholds: v1 10.8 % (42,278 lines, mean matched fraction
  0.839) → Bern 16.9 % (66,084 lines, 0.897)**; by stratum fair_copy 40.4 →
  50.9 %, light_revision 19.5 → 26.7 %, heavy_revision 8.7 → 14.5 %, scrap
  4.2 → 7.3 %; by hand own 8.1 → 14.5 %, partial 10.4 → 18.0 %, other 11.4 →
  16.8 %, **Leibniz's hand 9.5 → 12.5 %**; German 11.0 → 17.0 %, mixed with
  German leading 7.8 → 16.0 %; every volume up except VI,4 (22.3 → 19.6 %,
  12 pieces). **The rule's verdict: 1,178 pieces to the Bern reading, 402
  keep the v1 mint (77 of them ties), 568 mint nothing under either** (88
  aligned pieces where neither clears the gate, 480 skipped). **The German
  records' mint: 42,278 → 68,769 lines (+62.7 %)** — 58,991 on the Bern
  reading on the pieces it won, replacing 32,500 v1 rows there, 9,778 v1
  rows staying on the pieces it did not win; Leibniz's own hand 1,888 →
  2,714 lines on 54 pieces (2,187 of them on the Bern reading). The whole
  store: 315,797 rows → **342,288 expected** (before the factory's ownership
  rule, which can move a few lines between records at the write).
- **The backup check (for Task 3).** The operator's copy
  `/mnt/d/leibniz-backups/inventory-2026-10-20.sqlite`, 17,085,796,352
  bytes, written 2026-10-20 18:03 by the backup API from a `mode=ro`
  connection — the store's size to the byte (the store last written 15:00,
  WAL empty since). The whole-file hashes differ — store
  `32411cbaf80a8d2c928607ca470fac2b80005ae687b1c579da8e2f168fbaab4c`, copy
  `13aa65ff0626d756c75d9d4257c1009959398900479bd25cca8618badde8e0ce` — and
  `cmp -l` on the first 100 bytes names why: the backup API rewrites the
  header's change counter (offset 24), its "version-valid-for" copy (92),
  the schema cookie (40; it sets the destination's old value plus one) and
  the writing library's version (96; 3.46.1 in the copy, 3.53.1 in the
  store). **Past the 100-byte header the two files are byte-identical**
  (`cmp -i 100`, exit 0, no differing byte; 1 min 32 s to hash the store on
  `/`, 3 min 59 s the copy on `/mnt/d`). The copy is a faithful backup by
  content; the Task 3 write waits for the operator's go.
- **The write (Task 3; Checkpoint C;** `logs/k2-mint-write.log`,
  `data/kurrent/k2-readings/write-stats.json`; the account in
  `reports/kurrent/k2-write.md` and `k2-write.json`**).** The operator said
  "go" (with two additions for after the write, below). `leibniz align
  kurrent-mint --write` replayed the saved dry run, 2026-10-21 07:36 EDT,
  **7.8 s** wall: every record's stored mint re-read and found as the dry run
  saw it; **runs row 609** (`gt_factory`, model
  `retro-aligner+trocr-kurrent-xvi-xvii`, 1,178 pieces in, 1,178 written, 0
  failed, code `92828ac`); **rows removed 32,497, written 50,723**; the
  factory's ownership rule: 343 lines won from another record's row, 8,268
  pairs lost to one. **`gt_lines` 315,797 → 333,680 rows** (+17,883, +5.7 %),
  against the dry run's 342,288 expected — the 8,608 the account explains:
  the dry run's 58,991 pairs on the won pieces name **51,435 distinct lines**
  (6,344 lines were claimed by two or more Bern-won pieces sharing a page,
  7,556 claims beyond the first — the dry run counted each piece's pairs,
  the store keeps one row per line); of the distinct lines, **50,720 are
  the reader's rows now**, **715 stayed with a v1 row of another record**
  (714 of them German pieces the rule left to v1, 1 of another language)
  whose alignment confidence was higher or tied (mean margin +0.060; 123
  ties, where the lower record id keeps the line), 0 have no row; the 3
  rows written and gone again were won by a later piece's higher
  confidence. Every line is in `gt_lines` once (333,680 distinct
  references). **Rows on the 2,148 German records 42,278 → 60,163 (+42.3 %;
  the dry run's 68,769 counted shared lines twice)**: reader 50,720, v1
  9,443; by stratum fair_copy 59, light_revision 19,057, heavy_revision
  40,641, scrap 406; reader rows fair 58 · light 16,260 · heavy 34,149 ·
  scrap 253, all `open`. **Leibniz's own hand: 1,888 → 2,612 rows** on the
  records `catalog/hands.py` gives him (81 records, 54 of them with lines
  at the gate), 2,093 of them the reader's. Reader rows outside the won
  pieces 0; v1 rows left on them 0.
- **The consumers after the write (Task 3).** `leibniz align gt-report`
  (17 s): **333,680 open-bucket lines**, a table "aligned on a reader's
  text" — `trocr-kurrent-xvi-xvii` **50,720**, the v1 text 282,960 — the
  reader rows counted in every table of `reports/gt-factory.md`.
  `leibniz align audit-reach` (25 s, the operator's addition: confirm it
  treats K2's rows as the Task 3 decision says and skips none as
  non-canonical): **`n_reader_rows` 50,720, left out of every flag count
  as decided** (the hyphen flag compares the minted text with the store's
  v1 HTR text, which is not the text those rows were aligned on);
  **`n_skipped` 0** — no row's reference fails the canonical
  `{page_id}:{line_seq:03d}` form. The reach census therefore covers the
  282,960 v1 rows on 14,834 pages from 5,167 records (was 315,797 / 17,669
  / 6,130 before K2 replaced 1,178 German pieces' rows); its flags moved
  with them — hyphen 848 → 736 (0.26 %), math 255 → 254, addition 262,243 →
  234,896 (83.0 %), eigh 57,559 → 55,309 (18.3 → 19.7 %), Leibniz's hand
  (strict) 46,893 → 45,524 (14.9 → 16.2 %), bracket 4,811 → 4,170, lh35
  9,162 → 9,124; `data/gt/flags.jsonl` rewritten (gitignored). The
  pre-K2 flags file for C3 is the one C2c wrote; C3 should re-run
  `audit-reach` or read this one. `gt-reset` keeps reader rows (tested),
  the v1 factory skips a reader-minted record (tested), the release export
  carries the reader in the source string (tested).
- **The audit sheet (Finish; the operator's addition: stratified by hand).**
  `leibniz align kurrent-mint --audit` (46 s) → `data/kurrent/k2-audit.html`
  (69.6 MB, every crop inlined) and `k2-audit-lines.csv`, gitignored, bilingual
  (German beside English; the verdict values stay the C2 CSV's). **200 of the
  reader's rows, seed 20261020: 100 from the 2,093 in Leibniz's own hand
  (98 heavy_revision, 2 light_revision — all that pool has of them), 100
  from the 48,627 in other hands (25 per stratum: fair_copy, light_revision,
  heavy_revision, scrap)**, each half drawn equal per stratum under the
  seed, the two mixed under the seed again. The sheet does not say which
  half a line is from (a `data-group` attribute carries it, invisibly; the
  help text says the sheet is half and half); the lines CSV's new `group`
  column (`leibniz_hand` / `other_hands`) does — **to score by hand, join
  the judge's verdict CSV with `k2-audit-lines.csv` on `ref`** (the scorer
  `leibniz align audit-score` does it when the lines CSV carries a group:
  a table by group beside the one by stratum). Why by hand: K2b put this reader near 49 % CER on
  Leibniz's own letters, close to the aligner's break-even on drafts (K1:
  ≈ 48 % CER on heavy revision), so misplaced lines would hide there; a
  precision figure for his hand on its own is what K3 needs before it
  weights those lines. Every one of the 200 lines has its crop.
- **What K3 needs (the hand-over).** The German training rows are the
  60,163 on the German records — the 50,720 reader rows
  (`gt_lines.source LIKE '%; reader trocr-kurrent-xvi-xvii;%'`, or
  `record_id` in `data/kurrent/k2-decisions.jsonl` with `winner = bern`)
  and the 9,443 v1 rows on the 402 pieces the rule left (`winner =
  stored`); hold out the 1,472 pages of `reports/philiumm/heldout_pages.csv`
  and the 134 letters of K2b's pool; the 2,612 lines in Leibniz's own hand
  carry the audit's verdict once judged. **K3 starts after the sheet is
  judged, or after the operator decides to go without**; the precision
  figures by hand come from the join above. The readings
  (`data/kurrent/k2-readings/`, 310,831 rows) are the reader's text on
  every German line, usable as a weak teacher; the backup copy
  `/mnt/d/leibniz-backups/inventory-2026-10-20.sqlite` is the store before
  K2's write — keep it, and `data/kurrent/`, until K3 is merged. The store
  changed, so the backup chore runs again with today's date.
- **Code of the finish.** `audit.sample_lines` takes `record_ids` /
  `exclude_records`; `AuditLine.group` and the lines CSV's `group` column
  (every sheet, empty where unused); `kurrent_mint.build_audit_sheet` draws
  by hand and returns the counts by group; `account_write` /
  `render_write_report` / `write_write_report` and `kurrent-mint --account`
  (read-only) wrote `k2-write.md`; the write saves its counters beside the
  readings. Ruff clean; **pytest 866 passed, 1 skipped**. Branch
  `k2-german-gt`, pushed; compare
  https://github.com/marchofhares/leibnizlegible/compare/main...k2-german-gt?expand=1
  — the operator opens and merges the pull request. Nothing deployed,
  nothing sent; the website serves its own copy of the store.
- **The operator's decision on the audit sheet (2026-10-21, with the K3
  go), verbatim:** "The prerequisite "K2's audit sheet judged": the operator
  decides to go without, conditionally. The sheet (data/kurrent/k2-audit.html,
  200 lines, half in Leibniz's own hand) is being sent to a judge at the
  Leibniz-Edition; no verdict exists yet." K3 starts on it; the K3 entry
  records the conditions. When the verdict comes, score it with
  `leibniz align audit-score` (the lines CSV carries the `group` column)
  and put the figures by hand into this entry.

### C2c — the re-mint (2026-10-20) ✅ Task 0 · ✅ Task 1 · ✅ Task 2 (Checkpoint: the mint) · ✅ Task 3 · ⏳ the operator's pull request

- **Setting (Task 0).** The operator's desktop, the WSL checkout
  `/home/evana/LeibnizLegible`; main at `e2e29de` (#46, K2b) and
  `origin/main` the same; `c2c-remint` created with `git checkout -B
  c2c-remint origin/main`. The tree is clean apart from the operator's own
  untracked files (`logs/`, `*.log`, `resume-run.sh`, `.python-version`,
  `reports/gt-audit/gt-audit.html`), left alone. `pgrep -af leibniz`: no
  process. Disk: `/mnt/d` 932 G with 452 G free, `/` 1007 G with 896 G
  free; RAM 9.7 GiB, 16 cores. Baseline in `.venv-w3`: ruff clean, 224
  files formatted, **pytest 831 passed, 1 skipped** (the letter-pool test
  needs numpy, which the w3 environment lacks) in 31.8 s.
- **The store before (read-only, `mode=ro` + `query_only`).**
  `data/inventory.sqlite` 17,061,699,584 bytes, last written 2026-09-15
  20:16 (the C2 mint), WAL empty. `gt_lines` **297,424** rows, all `open`
  (fair_copy 9,913 · light_revision 96,175 · heavy_revision 190,162 · scrap
  1,174); the store predates W5, so `gt_lines` has no `record_id` column:
  every row's source names its catalogue record (`AA I,8 N.094 (§70-expired
  AA reading text; katalog 10000)`), so **297,424 owned by 5,526 records, 0
  not owned**, which is what `gt-reset` will report; **0 rows whose source
  names a reader** — K2 has not run. The schema the current code would
  create differs from the store's in that one column only (checked against
  a fresh `init_db` in the scratchpad), so `open_db`, which the
  edition-cache, report, sheet and vi4 commands use, has nothing to migrate
  here until `gt-reset` adds the column.
- **The inputs.** `data/gt/edition_cache.jsonl`: 10,029 records, written
  2026-09-15 13:12, keys `record_id` and `text` only — the format before W5
  (no pieces per record, so the factory would warn and mint a record citing
  two volumes under its first citation; Task 1 rebuilds it). 28 extracted
  volume texts under `data/editions/text/`. `data/philiumm/noisy/` holds
  735 PAGE files beside `hf-files.json` (P1's fetch): match and compare
  re-run without a download. The last backup is
  `/mnt/d/leibniz-backups/inventory-2026-10-19.sqlite` (17,061,699,584
  bytes). The image cache `/mnt/d/leibniz-images` is mounted.
- **The headline numbers as they stand.** `reports/gt-factory.md`: 297,424
  open-bucket lines (generated 2026-09-15). `reports/gt-audit/reach.md`:
  297,424 lines on 16,843 pages from 5,526 records; hyphen 7,822 (2.6 %),
  math 249 (0.1 %), bracket 4,338 (1.5 %), own hand 118,928 (40.1 %),
  Leibniz's hand 76,147 (25.7 %). `reports/philiumm/heldout_pages.csv`:
  1,475 rows, 1,472 distinct pages; the cross-check 62,114 paired lines on
  732 matched noisy files.
- **Found in pre-flight.** `leibniz align gt-reset` without `--yes` writes
  before it asks: it brings `gt_lines` up to ownership under the write lock
  (adds `record_id`, two indexes, fills 297,424 owners from their sources)
  and commits, and only then asks; answering no leaves that change in the
  store. The plan therefore asks for the first go before that first
  invocation, after the backup.
- **Task 1 — the backup.** After the operator's go: SQLite's backup API
  from a `mode=ro` connection (`python3 -c`, `pages=262144` a step) into
  `/mnt/d/leibniz-backups/inventory-2026-10-20-pre-remint.sqlite`:
  **17,061,699,584 bytes, the store's size, in 1,839 s (30.7 min)**, about
  9 MB/s onto the Windows drive; it opens and holds the 297,424 rows
  (`logs/c2c-backup.log`).
- **Task 1 — the edition cache.** The old cache kept as
  `data/gt/edition_cache.pre-c2c.jsonl`; `leibniz align edition-cache` (2 s;
  `logs/c2c-edition-cache.log`): **10,029 records with reading text before
  and after** (108,580,517 characters; 931 records cite an ingested volume
  without a text found), by volume I,3 661 · I,6 583 · I,7 607 · I,8 540 ·
  I,9 677 · I,10 645 · I,11 747 · I,12 662 · I,14 670 · I,15 782 · I,16 676
  · III,1 356 · III,3 563 · III,4 423 · IV,1 153 · IV,2 154 · IV,3 263 ·
  VI,1 40 · VI,3 228 · VI,4 566 · VI,6 33, the same as the volumes the old
  records cite. **No record gained or lost a text and no text changed (all
  10,029 byte-identical)**; what changed is that every record now carries
  its refs — one printed piece each (none joins two), by channel ia 7,232 ·
  gwlb 2,228 · potsdam 569. Against the C2 mint: of the 5,526 records it
  filed (each under one volume label), **5,506 are minted under the same
  volume now and 20 under another** — the volume their text came from: II,1
  → I,3 7, II,1 → III,3 4, I,5 → I,6 2, I,3 → III,3 2, and one each I,5 →
  III,4, I,2 → IV,3, III,3 → III,4, III,3 → I,3, I,4 → III,4 (lines that
  were filed under II,1, I,2, I,4 and I,5, volumes with no text, are
  gone). The store's modification time did not move (`open_db` found
  nothing to migrate; the empty WAL was checkpointed away on close).
  (`logs/c2c-cache-diff.log`.) **For K2's Task 0:** the K1 census and
  `data/kurrent/german_pieces.jsonl` (2,173 pieces, 2,148 records, 1,676 of
  them on localizable pieces) were built on the old cache; none of those
  records lost or changed its text, so K2's input stands as built; the only
  difference K2 sees is that a record's mint volume now follows its refs.
- **Task 2 — gt-reset, asked (go A).** `leibniz align gt-reset`, answered
  no (3 s; `logs/c2c-gt-reset-ask.log`): "297,424 minted lines owned by
  catalogue records (297,424 owners filled in from their source just now);
  0 other lines are kept." Checked read-only after: `gt_lines` now carries
  `record_id` on all 297,424 rows (5,526 distinct) and the indexes
  `ix_gt_record`, `ix_gt_ref` beside `ix_gt_bucket`; the store file
  17,081,397,248 bytes (+19.7 MB, the column and the two indexes). Nothing
  deleted.
- **Task 2 — gt-reset (go B).** `leibniz align gt-reset --yes` (1.4 s;
  `logs/c2c-gt-reset.log`): "deleted 297,424 lines (open 297,424)"; 0 kept;
  `gt_lines` holds 0 rows after.
- **Task 2 — the six shards (go C).** Launched 13:47 EDT, `.venv-w3`, each
  `nohup uv run leibniz align factory data/gt/edition_cache.jsonl --shard
  i/6` into `logs/c2c-shard-<i>.log`, no `--resume`. 16,807 pieces (one per
  record now; C2 enumerated 17,162 citations), 2,801–2,802 a shard; about
  33 pieces a minute a shard in the first twenty minutes, 58 in the next
  twenty; 2.0–2.1 GiB of RAM in use throughout. All six ended between 14:55
  and 15:00 (66–71 min). **Every skip is structural: no `error:` skip, no
  `database is locked`, so no `--resume` pass.** Per shard, minted lines
  from pieces: 59,225 from 1,240 · 50,191 from 1,285 · 55,294 from 1,207 ·
  58,003 from 1,180 · 56,725 from 1,199 · 57,994 from 1,197 — **337,432
  pairs from 7,308 pieces**; skips: not localizable 4,714 · no edition
  text 4,632 · no canvases 141 · no HTR lines 12 (7,308 + 9,499 = 16,807).
  (C2's pass 1: 317,365 pairs from 6,383 pieces; 5,567 · 4,314 · 141 · 11
  · 746 locked.) **The store after (read-only): `gt_lines` 315,797 rows,
  all `open`, every row owned (6,130 records), each line once; fair_copy
  10,234 · light_revision 100,085 · heavy_revision 203,749 · scrap 1,729;
  0 rows naming a reader.** The pairs exceed the rows because a line two
  records mint is kept once, for the higher alignment confidence. Sources
  now name the channel (`AA I,10 N.367 (§70-expired AA reading text;
  channel ia; katalog 10034)`). **CHECKPOINT: the mint is complete.**
  (The session's own watcher for the shards' end matched its own command
  line in `pgrep` and never fired; the logs were read when the operator
  asked, at 16:57.)
- **Task 3 — the reports (read-only).** `gt-report` (18 s) →
  `reports/gt-factory.md`: 315,797 open-bucket lines, 632 % of the 50k
  target; with a folio range 12,367 (11,617 before), localizable 12,345
  (71.9 %; 11,595, 67.6 % before). `audit-reach` (28 s) → `reach.md`,
  `reach-summary.json`, `data/gt/flags.jsonl` (the old flags kept as
  `flags.pre-c2c.jsonl`): 315,797 lines on 17,669 pages from 6,130 records
  (6,115 with a Textart). `philiumm-vi4 match` (8 min 50 s) and `compare`
  (2 min) → `reports/philiumm/`. `audit-sheet --seed 1 --images
  /mnt/d/leibniz-images --out reports/gt-audit/round2` (45 s): 200 lines,
  50 a stratum, 200 with image strips; `gt-audit.html` is 55.7 MB. The
  first round's `reports/gt-audit/gt-audit-lines.csv` is untouched.
- **Before → after, by stratum.** fair_copy 9,913 → 10,234 (+321) ·
  light_revision 96,175 → 100,085 (+3,910) · heavy_revision 190,162 →
  203,749 (+13,587) · scrap 1,174 → 1,729 (+555); **all 297,424 → 315,797
  (+18,373, +6.2 %)**; records 5,526 → 6,130; pages 16,843 → 17,669. Mean
  alignment confidence unchanged by stratum (fair 0.932, light 0.902, heavy
  0.919; scrap 0.925 → 0.938). **By channel** (the old rows' channel read
  from their record's refs, the texts being byte-identical): ia 202,448 →
  213,520 · gwlb 45,584 → 52,057 · potsdam 49,392 → 50,220. **By volume**:
  every volume with text gains (I,3 +3,749, I,6 +2,398, I,7 +1,842, I,14
  +1,759, the rest +4 to +1,205); the four without text lose everything
  they held: II,1 600, I,5 103, I,2 15, I,4 9 (727 lines).
- **Why the mint grew, line by line** (the old mint read from the backup;
  the placement of every record recomputed read-only under the code before
  W5, `9c96c7f`, in a scratch worktree, and under today's). 294,938 of the
  297,424 old lines are minted again (99.2 %); 2,486 are not; 20,859 are
  new; 38,023 of the lines minted both times now belong to another record
  (the C2 mint kept the last shard's writer, the factory now the higher
  confidence). Of the **20,859 new lines**: 9,965 come from the **710
  records localizable now and not before — all 710 `LBrF` shelfmarks**
  (W5: "`LBrF 20` parses as LBr F 20"; the before/after placement found no
  other new kind); 634 from pages newly placed for records localizable
  before (folio sides); **10,260 on pages the old code placed too** —
  the lines a neighbour's re-mint erased on a shared folio in C2
  (`delete_gt_for_refs` cleared every line of a piece's pages; C2 stored
  297,424 rows of 341,045 logged pairs, now 315,797 of 337,432) and lines
  a record now aligns under the volume its text came from; the two are not
  separated here. Of the **2,486 lines not minted again**: 1,758 lie on
  pages the record is no longer placed on (924 records' page sets narrowed
  by the folio-side fix, 18 widened), 728 on pages still placed (alignment
  or ownership). The skips moved accordingly: not localizable 5,567 → 4,714
  (citations then, records now); no edition text 4,314 → 4,632 — the
  factory asks for a place before a text, and 471 of the 710 newly
  localizable `LBrF` records have no text, so they moved from the first
  skip to the second; no canvases 141 → 141; no HTR lines 11 → 12; locked
  746 → 0.
- **The hyphen.** Flag (HTR line ends in a mark, minted text in a letter):
  **7,822 (2.6 %) → 848 (0.3 %)**; fair_copy 7.7 → 0.3 %, light 4.0 → 0.3
  %, heavy 1.7 → 0.2 %, scrap 2.0 → 0.3 %. **Minted lines that end in a
  hyphen mark: 271 → 8,523** (`-` 7,523, `–` 973, `=` 27). Of the 848
  left, 540 are the last minted line before an unminted one (the next line
  fell below the threshold or lies outside the piece, so the projection
  has no word to carry on; a sample of 12 shows the dash at the passage's
  edge, and at a word boundary in the edition: `plu-` → `plu`, `Argu-` →
  `Argu`), the rest a cut the projection placed at a word boundary, which
  the fix leaves dropped by design. The lines whose HTR read no mark (8 of
  the audit's 14) are invisible to this flag, as C2b said; the re-mint
  cannot invent a mark there.
- **Bracket and math.** Bracket 4,338 (1.5 %) → 4,811 (1.5 %); math 249
  (0.1 %) → 255 (0.1 %); both move with the line count. LH 35 9,145 →
  9,162; Marginalien 0 → 0; the addition proxy 82.7 → 83.0 %.
- **Leibniz's own hand.** Under W5's strict rule (`catalog/hands.py`: an
  `eigh.` on an address, a correction or a postscript is *partial*; a
  namesake is not Leibniz): **own hand 57,559 (18.3 %), Leibniz's hand
  46,893 (14.9 %)** of the 313,917 lines with a Textart; by stratum
  Leibniz's hand fair 0.4 · light 1.9 · heavy 22.2 · scrap 11.7 %. The
  loose rule said 40.1 / 25.7 % on the old mint. **The fall is the rule,
  not the mint**: the strict rule on the old mint gives 18.3 / 15.1 %, the
  loose rule on the new mint 40.0 / 25.4 %. What the strict rule removes
  is 64,604 old lines (68,114 new) whose `eigh.` qualifies a part only —
  in IV,1 all of it (34.9 % → 0.0 %: `Konz. mit zahlr. eigh. Korr. &
  Erg.`, scribes' copies with his corrections), in I,10 and I,12 nearly
  all (31.8 → 1.7 %, 50.1 → 1.4 % own hand) — and 571 lines whose sender
  is a namesake. VI,4 barely moves (64.7 → 60.6 %), IV,2 98.0 → 84.4 %.
- **The A VI,4 cross-check.** Noisy files matched 732 → **735**, lines
  paired 62,114 → **62,164** (their lines 93,021 → 93,410): the three LH 4,
  5, 10 files that share a key were already paired in P1 and are counted
  as matched now (P1's own fix `47721b9`, after its last committed run),
  not a mint effect. Buckets: agree 9,307 → **9,506** (15.3 %) · near
  2,886 → 2,924 · disagree 771 → **774** (1.2 %) · ours only 5,145 →
  5,234 · theirs only 21,949 → 21,730 · neither 22,056 → 21,996; on the
  minted heavy-revision lines agree 51.4 → 51.6 %, disagree 4.2 → 4.2 %.
  The HTR witness on the disagreements: ours 384, theirs 383, tie 7.
  Files with no minted line 161 of 731 → 159 of 734 (7,333 of their
  lines). **Held-out pages: 1,472**, as before (1,475 rows; the report's
  prose said 1,149 before W5's count fix).

### K2b — the letter-pool test set (2026-10-19/20) ✅ Task 0 · ✅ Task 1 (Checkpoint A) · ✅ Task 2 (Checkpoint B) · ✅ Task 3 (Checkpoint C: five readers measured) · ⏳ the operator's pull request

- **Setting.** The operator's desktop: the WSL checkout
  `/home/evana/LeibnizLegible`, driven from a Claude Code session opened on the
  `\wsl.localhost` path (the Windows side shows the `.sh` files and a CSV as
  modified — the mode-bit artefact; inside WSL the tree is clean, and the
  untracked `logs/`, `*.log`, `resume-run.sh`, `.python-version` and
  `reports/gt-audit/gt-audit.html` are the operator's own, left alone).
  `git pull --ff-only` on main: already up to date at `82e2091` (#45);
  `k2b-letterpool` created with `git checkout -B k2b-letterpool origin/main`,
  the branch the preamble of 19 October names. Disk: `/` 1007 G with 898 G
  free, `/mnt/d` 932 G with 452 G free. GPU: GTX 1660 Ti, driver 610.57.01,
  1,232 MiB of 6,144 MiB held by the desktop (Xwayland), nothing else on it.
  `.venv-k1` from K1: Python 3.12.13, torch 2.12.0+cu130 with CUDA 13.0
  available, transformers 5.12.1, pdfplumber 0.11.10, pypdfium2 5.13.0, numpy
  2.4.6, Pillow 12.3.0, kraken 7.0.3; uv 0.12.0; no `edlib` and no `pypdf`
  (nothing will be installed: the infix alignment is a numpy DP). Baseline in
  `.venv-k1`: `ruff check` clean, `ruff format --check` 215 files formatted,
  **pytest 807 passed, 1 skipped in 33.8 s**. The store
  `data/inventory.sqlite` is 17,061,699,584 bytes (as K1 found it) and is
  opened read-only throughout; `/mnt/d/leibniz-images` is mounted;
  `data/kurrent/german_pieces.jsonl` has 2,173 rows (the K2 input, the
  disjointness check's German side); `reports/philiumm/heldout_pages.csv` is
  present; `data/models/hf/` holds the three TrOCR checkpoints K1 cached. The
  nine repository pages for the checked years 1708–1716 answered 200 and each
  links `LAA-Transkriptionen<year>-v1.pdf` (the 1714 page: Version 1 of 3
  November 2020, 2.97 MB, "Lizenz: CC BY-NC 4.0", a Zitierhinweis and a
  BibLaTeX entry). The go came after this pre-flight; nothing was fetched
  before it.
- **Plan, as printed for the go.** *Task 1* (no go needed; about 27 MB over
  nine requests at one a second): `tools/fetch-letterpool.sh` and `leibniz
  align letterpool-fetch` into `data/external/letterpool/` with
  `reports/kurrent/letterpool-sources.json` (version, date, SHA-256, URL — no
  text); `align/letterpool.py` on pdfplumber's characters (body size kept;
  line numbers, running heads, Überlieferung block and footnotes dropped;
  NFC; editorial brackets as the C2b flags describe them), the first witness's
  siglum, kind, shelfmark and leaves through `normalize_signature`, the
  language through `enrich.langid.classify`; tests on a synthetic PDF built in
  the test; the per-year report; ten letters checked against the PDF by eye.
  Checkpoint A. *Task 2* (store read-only, minutes): the work through the
  crosswalk's signature keys, the pages through the C2 resolver; drops counted
  by reason (no work, no folio-labelled canvas in range, no recognised lines,
  shared leaves); disjointness against `german_pieces.jsonl`'s pages and
  `heldout_pages.csv`; the draw seeded and stratified by siglum and year
  (every L and l letter, a K and k sample of about the same size), split
  once into a selection half and a test half per the amendment of 10 October;
  `reports/kurrent/letterpool-testset.csv` (no text) and the texts under
  `data/kurrent/letterpool/`. Checkpoint B. *Task 3*: the metric — the
  letter's reference against the concatenation of every recognised line on
  its pages in reading order, an infix (semi-global) alignment with the
  machine text's prefix and suffix free, as a vectorised numpy DP checked
  against the full DP on fixtures; CER pooled and per letter with a bootstrap
  over letters, under the B1 harness's three policies and the Kurrent
  package's reading policy, per siglum, year and half; a selected line-level
  CER beside it; `v1` from the store (no GPU, minutes); then, **after a go**,
  `philiumm`, `trocr-kurrent-xvi-xvii`, `trocr-hanse-xvi` and
  `trocr-hanse-xvii` through the pilot's crop machinery into
  `data/kurrent/letterpool-readings/<reader>.jsonl`, resumable, under nohup
  with a log under `logs/` (K1's rates of 334 / 209 / 337 / 34 ms a line put
  it at hours once the line count is known); `letterpool-eval.md` and
  `.json`, numbers only. Checkpoint C. Then STATUS.md, PROMPTS.md, ruff and
  pytest, push, the compare URL; no merge, nothing deployed.
- **Task 1, the pool fetched and parsed** (`align/letterpool.py`, `leibniz
  align letterpool-fetch` and `letterpool-parse`, +18 tests on a synthetic
  two-page PDF built in the test; `reports/kurrent/letterpool-sources.json`,
  `letterpool-parse.md` + `.json`; the PDFs under `data/external/letterpool/`,
  the page cache and the letters under `data/kurrent/letterpool/`). *The
  fetch:* each year's repository page names its newest PDF; all nine checked
  years are at version 1 (1708–1712, 1715 and 1716 of 28 October 2020, 1713
  and 1714 of 3 November 2020), 25,422,200 bytes and 3,579 pages in all, each
  recorded with its SHA-256, URL, page count and the citation the page gives
  (the Zitierhinweis names the volume's compiler and editor, as attribution
  asks; licence CC BY-NC 4.0, bucket nc). *The parser:* pdfplumber's
  characters per line with size, font and token edges; the volume's layout
  learned once (body 12.0 pt, small type under 11.2 pt, the text block
  49.0–508.1 pt, pitch 16.7 pt); per page the running head (the top 9 %)
  dropped and its `N.` cross-checked, the margin line numbers (every fifth
  typeset line, outside the block, on the side EDMAC alternates) stripped by
  position, the notes at the foot dropped (small type, or a short body-type
  run opening with a line-number key under a gap), a heading recognised by
  its shape (number, full stop, capitals — the small-caps running head comes
  out of the text layer in lowercase, the headings in capitals), the dateline
  and any subtitle ("Beilage zu N.5") held until the *Überlieferung* line
  arrives, the block parsed for its first witness (siglum, kind, the
  shelfmark up to its leaves through `normalize_signature`, the
  correspondent's parenthesis removed first because the A3 normaliser cuts at
  one), a second text on the leaves noted ("Auf Bl.4vo L von N.69"), the
  text's lines joined with the print's hyphenation undone
  (`edition.join_lines`), the editorial brackets resolved as the C2b flags
  describe them (a supplied letter or mark attached to a word keeps its
  content, 5,009 of them; a bracketed insertion standing alone — an identified
  name, a reference, a supplied word — goes, 3,085; an angle-bracket remark of
  the editor goes, 437; nested groups innermost first), a letter printed in
  several drafts (⟨L1⟩ … ⟨L2⟩; 25 letters) kept to its first witness's draft,
  and the language by the K1 identifier. Three traps of the text layer: an
  umlaut is a base vowel followed by a spacing diaeresis (U+00A8; 3,101 of
  them, most the Ü of *Überlieferung*), which NFC never composes, so it is
  composed first; the maths font's angle brackets come as CIDs; the other
  CIDs (integral signs, a Greek font) are dropped. *Results:* **2,533
  letters** on 3,579 pages — 835 German, 1,179 French, 489 Latin, 27 mixed, 3
  unknown; by first witness L 812, l 26, K 1,553, k 91, other 51 (copies,
  prints, none named); **2,090 placeable** (LBr, LH or LK with a `Bl.` range;
  6 LK-MOW witnesses carry letter-prefixed folios and are not); **695 German
  and placeable: L 111, l 1, K 560, k 17** (and 6 copies, siglum A); 353
  letters name a second text on their leaves. The source's own numbering has
  three faults, recorded as anomalies and kept as printed: 1709 prints "52."
  for the letter after 40 and again for the fifty-second (ids `1709-52` and
  `1709-52-2`), 1713 prints 473 twice and no 472, 1715 prints "290." for the
  letter after 239 and again later; eleven running heads in 1716 and one each
  in 1713 and 1714 name another letter than the page carries. *The spot
  check:* ten letters drawn seeded (three German K, two German L, one German
  k, one with shared leaves, one enclosure with a subtitle, one French, one
  Latin) and read line by line against the page dump — heading, dateline,
  witness and the text's start and end right on all ten, after two faults the
  check itself found and the parser now handles: a letter printed in four
  drafts had all four concatenated (now the first witness's draft alone,
  recorded in `segment`), and a body-type footnote wrapping onto a second
  line escaped the note splitter (now taken as a run). A correspondent's own
  numbering written on the leaf ("N.44.") stays in the text, since it is on
  the page. ruff clean, 825 tests. **Checkpoint A: the letters parse
  reliably.**
- **Task 2, the letters placed and the set frozen** (`align/letterpool_set.py`,
  `leibniz align letterpool-set`, +5 tests on a seeded fixture store;
  `reports/kurrent/letterpool-testset.csv` (the frozen set, no text),
  `letterpool-placement.csv` (every German letter's placement and reason),
  `letterpool-set.md` + `.json`; the reference texts in
  `data/kurrent/letterpool/testset.jsonl`, gitignored, nc bucket). The store
  read-only (`open_readonly`); 2.9 s. *Placement* as the factory and the web
  layer place a piece: the first witness's key through the crosswalk's
  signature index (`build_work_key_index`; where a key names several works the
  first whose folio labels cover the leaves wins), the leaves through the C2
  resolver (`select_span`, the sides kept), the recognised lines counted per
  page (`lines.text` not null), a drop under the first reason that applies.
  Of the **695 German letters with a placeable witness** (23 mixed-language
  ones counted apart): **placed 565** (L 67, K 482, k 13, A 3), **no work 72**
  (LBr 827 — 21 of them, Schöttel's letters — is not among the store's works;
  the LK-MOW convolutes are not either, the store holds no LK key at all; two
  `LH XLI` witnesses name no section), **no canvas 10**, **no lines 0**,
  **shared leaves 48** (L 30, l 1, K 12, k 2, A 3: the block names a second
  text on the leaves, "Auf Bl.4vo L von N.69"). The placed letters sit on
  1,782 pages with 76,230 recognised lines (1,319,833 reference characters);
  by year 1713 is the largest (170 letters). *Disjointness:* no page of a
  placed letter is among K2's German pieces' pages
  (`data/kurrent/german_pieces.jsonl`, 0 of 1,782) or the PHILIUMM held-out
  pages (`reports/philiumm/heldout_pages.csv`, 0) — as expected from the
  years, now checked page by page. *The draw* (seed 20261019): every placed
  letter in Leibniz's hand — **67 L** (no l letter placed: the one l witness
  shares its leaves) — and **67 correspondents' letters** (65 K, 2 k)
  allocated over the (siglum, year) cells in proportion to the pool by
  largest remainder and drawn seeded within each cell; the set split once,
  seeded, within each (siglum, year) cell, into the **selection half (67)**
  and the **test half (67)**, per the amendment of 10 October. **134 letters,
  386 pages, 18,815 recognised lines, 325,624 reference characters** —
  selection 186 pages, 7,696 lines, 138,942 characters; test 200 pages, 11,119
  lines, 186,682 characters; letters from 2 (1708) to 48 (1713) a year; lines
  per letter 46 / 102 / 187 at the quartiles, 1,088 at most, up to 8 pages.
  Two groups of drawn letters share pages (short pieces on one leaf: 1713-166
  and 167 on two pages; 1713-168, 171 and 172 on two pages), 380 distinct pages
  in all; the metric's free prefix and suffix leave a neighbour's text
  uncharged. The CSV carries letter, year, number, half, siglum, kind,
  shelfmark, leaves, work, page ids, pages, lines, characters and the SHA-256
  of the reference text; the texts file carries the text with the same
  checksum, so a later session can verify the set it measures is the frozen
  one. 830 tests, ruff clean. **Checkpoint B: the set is frozen.**
- **Task 3 (i), the metric built and v1 measured**
  (`align/letterpool_eval.py`, `leibniz align letterpool-eval` with `--read`
  for the GPU step, +11 tests in all; `reports/kurrent/letterpool-eval.md`, `.json`
  and `letterpool-eval-letters.csv`, one row per letter, reader and policy,
  numbers only). *The metric, letter by letter, nothing filtered:* the
  reference text against the concatenation, in reading order, of every
  recognised line on the letter's pages, aligned so that machine text before
  and after the letter is free and everything inside the span counts — the
  infix (semi-global, edlib's HW) alignment as a vectorised numpy dynamic
  programme, one row per reference character (the diagonal and vertical
  moves element-wise, the horizontal move as a cumulative minimum), checked
  against the full table on 300 random pairs; the span's end is the last
  minimum of the final row, its start the reverse problem pinned at that end.
  No new dependency. CER = edits ÷ reference characters, pooled, with the B1
  harness's bootstrap over the letters as atoms (1,000 resamples, seed 12345),
  and as a per-letter distribution; four policies — the harness's `philiumm`
  (NFD, whitespace collapsed; case and diacritics kept: the headline),
  `lenient`, `strict` (NFC; the lines are joined by single spaces on both
  sides) and the Kurrent Trace package's `reading` (NFC, long s folded, as K1
  scored Dresden); per hand (L; K/k), year and half. Beside it, labelled
  *selected*, the line-level CER over the lines `align_piece` accepts at the
  factory's unknown-stratum threshold 0.65 (the minted slice against the
  reader's line). The frozen set is verified against its checksums before
  anything is scored; a changed text refuses. **`v1`, the stored text of the
  C1 run — the German error rate of what the website shows today — on the
  134 letters (18,815 lines, 17,399 of them, counted per letter, with a non-empty stored
  reading; 17,032 distinct lines): CER 46.6 % (95 % interval 43.3–49.5 %) under `philiumm`, 45.2 %
  lenient, 46.8 % strict, 46.8 % reading; selection half 44.5 % (41.4–47.6
  %), test half 48.2 % (43.1–52.4 %); by hand, the correspondents' letters
  (K/k, 67 letters, 8,059 lines) 38.5 % (35.9–41.9 %) and Leibniz's own (L,
  67 letters, 10,756 lines) 53.7 % (49.9–56.9 %); per letter the median is
  42.9 % (quartiles 34.7 % and 57.9 %, from 20.8 % to 73.6 %); on average
  68.2 % of a letter's machine text lies inside the aligned span. The
  selected number says what the selection hides: the aligner accepts 4,056
  of the 18,815 lines (21.6 %) and on those v1 reads at 28.7 % — eighteen
  points under the unfiltered rate.** Scoring one reader under four policies
  took 7 minutes.
- **Task 3 (ii), the four readers read on the GPU** (the go given on
  2026-10-19; `leibniz align letterpool-eval --read --crop-cache
  data/kurrent/letterpool-crops` under nohup, `logs/k2b-read-2.log`; the
  readings in `data/kurrent/letterpool-readings/<reader>.jsonl`, one JSON line
  per page line with the reader's text and timing, gitignored). `philiumm`,
  `trocr-kurrent-xvi-xvii` and, evaluate-only, `trocr-hanse-xvi` and
  `trocr-hanse-xvii` read the set's lines afresh through the pilot's crop
  machinery (the v1 geometry, the polygon masked, no downscaling, batches of 8
  on the GTX 1660 Ti): 18,445 distinct lines, since the set's 18,815 count a
  page two letters share once per letter. The first launch (20:34, New York
  time) was stopped at 20:39 with 4,218 philiumm readings: at 64 ms of wall
  time a line against 15 ms in the model, the loop was spending most of its
  time on the page images read from D: and the polygon cuts, which every
  reader would repeat; a crop cache was added to the pilot's reader
  (`crop_all(cache_dir=…)`: a PNG per line under
  `data/kurrent/letterpool-crops/`, cut once and read by the next reader; 1.9
  GB, re-creatable) and the job relaunched at 20:40 with the 4,218 readings
  kept. philiumm was done at 20:56, trocr-kurrent-xvi-xvii at 22:44,
  trocr-hanse-xvi at 23:22, trocr-hanse-xvii at 01:11 — 4 h 31 min of reading,
  no line skipped, 3.3 GB of GPU memory in use when checked; model time per
  line as the readers measured it 15 / 340 / 124 / 352 ms. The job scored the
  set at its end (01:42) with the module as imported at launch; the set was
  re-scored at 09:23 on 20 October with the readers' lines-read count changed
  to count per letter — the same numbers, that column apart — and that run's
  reports are the committed ones. Nothing was written to the store. (The host
  stopped the session's background watcher for memory during the run and it
  was not restarted, as instructed; the operator prompted the session once the
  job had ended.)
- **Task 3 (iii), the numbers — Checkpoint C**
  (`reports/kurrent/letterpool-eval.md`, `.json` and
  `letterpool-eval-letters.csv`: 2,680 rows, one per letter, reader and
  policy, counts and rates with letter numbers only; the pool cited volume by
  volume with its version). Five readers on the 134 letters, nothing filtered;
  CER under the `philiumm` policy, pooled over characters, with the 95 %
  bootstrap interval over letters: **v1 46.6 % (43.3–49.5 %), philiumm 52.9 %
  (49.8–55.6 %), trocr-kurrent-xvi-xvii 37.0 % (32.5–41.0 %), trocr-hanse-xvi
  35.6 % (31.2–39.6 %), trocr-hanse-xvii 38.9 % (34.6–42.8 %)**; the other
  policies move each reader by under two points (lenient 45.2 / 51.6 / 35.8 /
  34.4 / 37.6; strict 46.8 / 53.0 / 37.1 / 35.7 / 38.9; reading 46.8 / 53.0 /
  37.0 / 35.7 / 38.9 %). *The halves:* selection 44.5 / 50.5 / 34.1 / 32.3 /
  35.8 %, test 48.2 / 54.6 / 39.2 / 38.0 / 41.2 % — the test half is the
  harder one for every reader, by 3.8 to 5.7 points. *By hand:* the
  correspondents' letters (K/k, 67 letters, 8,059 lines) v1 38.5 % (35.9–41.9
  %), philiumm 45.5 % (43.0–48.6 %), trocr-kurrent-xvi-xvii 23.2 % (19.6–27.3
  %), trocr-hanse-xvi 22.8 % (19.3–27.1 %), trocr-hanse-xvii 26.4 % (22.7–30.8
  %); Leibniz's own hand (L, 67 letters, 10,756 lines) 53.7 % (49.9–56.9 %),
  59.3 % (55.8–62.3 %), 49.2 % (44.8–52.9 %), 46.7 % (42.1–50.7 %), 49.8 %
  (45.3–53.5 %). *By year:* 1712 (5 letters) is the easiest for every reader
  (30.5 / 40.6 / 13.8 / 13.8 / 17.0 %) and 1715 (19) the hardest (52.6 / 58.6
  / 45.3 / 43.8 / 47.0 %); 1713, the largest year (48), reads at 44.7 / 50.7 /
  34.6 / 33.2 / 36.4 %. *Per letter:* the medians 42.9 / 49.4 / 31.5 / 28.3 /
  32.8 %, the quartiles 34.7–57.9 % for v1 and 17.0–47.9 % for
  trocr-hanse-xvi; the best letter of any reader at 7.5 % (trocr-hanse-xvi),
  the worst at 73.6 % (v1); 68 % of a letter's machine text lies inside the
  aligned span, the same for every reader. *Selected* — the lines
  `align_piece` accepts at 0.65, the factory's gate: v1 4,056 lines (21.6 %)
  at 28.7 %, philiumm 2,821 (15.0 %) at 31.9 %, trocr-kurrent-xvi-xvii 4,993
  (26.5 %) at 15.6 %, trocr-hanse-xvi 5,408 (28.7 %) at 15.5 %,
  trocr-hanse-xvii 5,006 (26.6 %) at 18.0 % — 18 to 21 points under the
  unfiltered rates, which is the size of the flattery an aligner-filtered
  evaluation carries. *What it says:* the three TrOCR readers read the
  correspondents' hands at 23–26 % against v1's 38.5 % and Leibniz's own at
  47–50 % against 53.7 %; their intervals overlap pairwise, trocr-hanse-xvi
  1.5 points under trocr-kurrent-xvi-xvii; philiumm, the kraken baseline K1
  would fine-tune from, is the worst reader on every cut. K1's gate holds:
  trocr-kurrent-xvi-xvii (MIT) is the reader for K2, the two Hanse models
  stating no licence and evaluated only. The lines read per reader, of the
  18,815: v1 17,399 (a stored reading that is not empty), philiumm 17,848,
  trocr-kurrent-xvi-xvii 18,807, the two Hanse readers 18,815; an empty
  reading counts as deleted. The frozen set's checksums were verified before
  scoring. **Checkpoint C: the German error rates are measured, on a set no
  reader chose.**
- **Licence handling, and what is where.** The pool is CC BY-NC 4.0 (nc
  bucket, SPECS §1.4 and §7.3): its text serves internal evaluation only.
  Committed, numbers and identifiers only:
  `reports/kurrent/letterpool-sources.json` (each volume's version, date,
  SHA-256, URL and Zitierhinweis), `letterpool-parse.md` + `.json` (counts),
  `letterpool-placement.csv` and `letterpool-testset.csv` (letter numbers,
  shelfmarks, page ids, counts and the texts' checksums), `letterpool-set.md`
  + `.json`, `letterpool-eval.md` + `.json` and `letterpool-eval-letters.csv`.
  Never committed, under the gitignored `data/`: the nine PDFs
  (`data/external/letterpool/`, 25 MB), the page cache, the letters and the
  frozen set's texts (`data/kurrent/letterpool/`, 33 MB), the readers' output
  (`data/kurrent/letterpool-readings/`, 13 MB — the project's machine text of
  the store's pages, kept beside the set it was read for) and the crop cache
  (`data/kurrent/letterpool-crops/`, 1.9 GB, rebuilt by the next `--read`). No
  reader was chosen or tuned on the set; nothing reached the website, a
  release or training; the store was opened read-only throughout. The README
  gained a Kurrent-track section with the commands. ruff clean; **841 tests**
  (807 at the pre-flight, +18 parser, +5 set, +11 metric; 1 skipped as
  before). The branch `k2b-letterpool` carries five commits and this
  close-out; the pull request and the merge are the operator's.

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
| Tests passing | **1096** (2026-10-30, main with K4 merged, checked in a cloud checkout with the `web` + `gt` + `release` extras before the pull request); 1,052 (2026-10-30, K4, in `.venv-w3` with the `web` + `gt` + `release` extras; 1 skipped, `test_align_letterpool_eval.py`'s eleven for want of numpy there); 1026 (2026-10-26, main with K3 merged, checked in a cloud checkout with the `web` + `gt` + `release` extras before the pull request); 904 (2026-10-26, K3, in `.venv-k1` with the `bench` + `gt` + `kurrent` extras); 980 (2026-10-22, A3b follow-up 2, in `.venv-cloud` with the `web` + `gt` + `release` extras; 979 after the first follow-up, 976 after A3b on 2026-10-21, 948 at its pre-flight); 948 (2026-10-21, G1, in `.venv-cloud` with the `web` + `gt` + `release` extras; 880 at its pre-flight); 880 (2026-10-21, L1, in `.venv-cloud` with the `web` + `gt` + `release` extras; 859 at its pre-flight on main the same day); 866 (2026-10-21, K2, in `.venv-k1`; 859 at W6 the same day in `.venv-cloud` with the `web` + `gt` + `release` extras, 856 at its pre-flight; 841 at K2b, in `.venv-k1` with the `bench` + `gt` + `kurrent` extras: 807 at the pre-flight, +18 parser, +5 set, +11 metric; 808 after W5, with the `web` + `gt` + `release` extras; 704 after K1, in `.venv-k1`; 644 after W4, 634 after S1, 621 after P1 Task 2, 606 after C2b, those with the `gt` + `web` + `release` extras) |
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

33. **The Edition's verdict convention and the licence of its corrected lines
    (2026-11-16).** K2's audit sheet came back with a fifth column of
    corrected transcriptions and no "wrong" verdicts (the Current state entry
    of 2026-11-16). (a) The scorer reads the C2 shape, so a converter maps
    "transcription, no verdict" to wrong and keeps the transcriptions as
    corrections; the honest precision is the one under the aligner's fold,
    measured by the C2b pattern code over the corrections, not the strict
    39 %. (b) The 118 corrected lines are the Arbeitsstelle's own text.
    **Settled 2026-11-16, after the question of the same day: the corrected
    lines may go into the open ground-truth release under CC BY 4.0** (the
    operator's record of the Edition's answer); the credit wording is still
    to be confirmed (until then: the Leibniz-Edition's Arbeitsstelle,
    Potsdam, with the date 2026-11-06). So the verified set, the 76 confirmed
    and the 118 corrected lines, goes to the open deposit with that credit:
    a registry entry `edition-k2-audit` (text, CC BY 4.0, channel
    `edition-k2-audit`, deposit open) and an `audit-apply` command that
    writes the verified lines into `gt_lines` are the K3b-prep cloud
    session's; the write itself is K3b's Task 0, after a backup and a go;
    the corrections file may be committed under `reports/kurrent/` (while
    the licence was open it was to stay under `data/`). (c) Two lines were unjudgeable without context
    and one is a French line in a German piece: the next sheet renders the
    neighbouring lines, and per-line language on mixed pieces stays Open
    question 31's.
32. **The narrow crops among the German lines (2026-10-28, K4; for K3b's
    segmentation measurement).** Of the 1,539,721 lines the K4 reading job
    reads, 252,286 (16.4 %) are crops under 80 px wide, segmentation
    fragments either way: on the letter pool's 3,172 such crops READER
    returned a single character on 2,422 (v1: 1,284 empty, 1,325 one
    character). The operator's decision of 28 October: Task 4 writes every
    non-empty reading, these included, because the letter-pool number was
    measured on all crops and one run per page keeps K3b's replacement
    simple. Open for K3b: whether its segmentation measurement counts these
    fragments as segmentation errors (merged or split lines) and whether a
    re-segmentation removes them; the count by collection is in the K4
    report (`reports/kurrent/k4-reading.md`, Task 4).
31. **German pages that mix scripts, and print (2026-10-26, K4).** (a) K4
    reads every German page whole with the Kurrent reader, the Latin and
    French passages on it included; on the letter pool's two mixed letters
    the reader gains nothing over v1 where it gains 18 points on the German
    ones (`reports/kurrent/k4-mixed-letters.md`; two letters, a sign only).
    A per-line choice between the Kurrent reading and the unscoped one —
    by the line's own language, which the identifier cannot tell on a
    seven-word line, or by the readers' confidences, which are not
    comparable across models — needs per-line German ground truth on mixed
    pages, which the pool does not give. Until then a mixed page shows the
    Kurrent run's row wherever it wrote one. (b) The Marginalien are
    printed books: v1 reads their print well enough for the identifier to
    find 6,719 German pages, the Kurrent reader is a handwriting model, and
    no ground truth exists for either on print. The session proposed to
    leave the collection out of the reading job (the operator's answer is
    in the K4 entry); a print reader (Fraktur) is a step of its own.
30. **The Calculemus seam's open points (2026-10-21, G1).** None blocks the
    first pack. (a) `provenance.model_alt` (the Bern reader's model beside
    the v1 row's) is an addition to the contract of Calculemus SPECS §6.6,
    named in the G1 prompt; the game's importer must accept or ignore it —
    if it rejects unknown keys, either the game's SPECS gains the key or the
    pack drops it (a line in `fragments.build_row`, a line in the schema).
    (b) A page the GWLB serves without a IIIF canvas (the static works)
    names the site's own manifest canvas as its `canvas_id`. (c) What the
    site shows of a line is its latest run (`latest_lines`): an imported
    judgment shows until a later machine run (C4) re-reads the page and
    shows above it; C4's current-run decision (SPECS §4.3 left it open)
    should say whether a `corrected` row outranks a later machine row. (d)
    The judgment row stored verbatim carries the players' `display_name`s
    into `lines.source`, which the page API and the IIIF annotations print
    once the serving copy holds the rows: P8 confirms the game's consent
    covers it, or the import strips the names (the prompt asks for the row
    verbatim). (e) Gold rests on K2's reader rows, whose precision by hand
    the K2 audit sheet will give; a both-wrong verdict can also be an
    edition expansion the fold does not forgive, hence its cap. (f) The
    demand weight is 1 on every row until search logs or the Reference Desk
    give better (NOTES.md B). **2026-10-21, the first real pack** (the
    operator's run; the G1 entry in the Phase log), three choices for the
    owner before the copy to the box: (g) *The gold is 56 rows, 2.8 % of the
    pack:* the cap allows 500, the supply gives 42 truths, all of them the
    Bern reading, and so 14 both-wrong rows. Whether 56 rows calibrate the
    players is the game's question. If they do not, the change is a
    gold-first draw: the gold-eligible lines among all the eligible drawn
    first, up to the caps, then the strata filled — the prompt's "gold among
    the selected lines" would become "among the eligible lines"; the truth
    gold would stay lines the Bern model reads exactly, mostly heavy
    revision. Code, tests and a rebuild of six and a half minutes. (h) *The
    shorter reading can be one character:* the 10–50 window bounds the longer
    reading only, as the prompt set it, so a pair where one reader failed
    asks nothing; a floor on the shorter reading, or on the ratio of the two
    lengths, would drop such pairs. The pack file alone says how many there
    are (the line under Next). (i) *The aim:* the equal allocation gives
    scrap and heavy revision a third of the pack each (1.4 % and 74.7 % of
    the pool), and either reading equals the edition's text on 15.9 % of the
    selected lines with an open reader row — far under the 70 % NOTES B asks
    on heavy revision before an A/B design, so most German fragments will end
    both-rejected. Ship this pack as a trial, whose both-rejected rate per
    stratum is the measurement the game can make, or aim the next pack
    (NOTES B: fair copy and light revision; German has 55 eligible lines of
    fair copy).

29. **Licence asks open after L1 (2026-10-21).** The registry
    (`src/leibniz/legal.py`, `leibniz legal licences`) records them with
    dates; none is this project's to decide. (a) The Göttingen series: the
    licensing of Reihe I, III, VII (Hanover) and II, VI (Münster) may differ
    from Potsdam's; the GWLB repository's Reihe I PDFs stay CC BY-NC 4.0 as
    published and their lines in the NC deposit until an answer comes (the
    operator's letters, October 2026). (b) PHILIUMM's GitLab code states no
    licence (asked 2026-10-13); the apparatus-reinsertion script has not been
    received. (c) `mittagessen/dfine_kraken`'s licence file is unread (the
    cloud session's GitHub access is scoped to this repository); the Nantes
    HMER code's address is not in the repo; both are tools run beside the
    repository, nothing imported. (d) The Kurrent Trace package's licence
    conflict (Zenodo field CC BY 4.0, README CC BY-NC-SA 4.0) is the author's
    to resolve; nc bucket until then. (e) The lawyer-memo questions in
    `reports/release-checklist.md` §6, first among them whether NC terms on
    a PDF reach reading text free of §70 — if not, the NC deposit opens up.
    (f) At every release, re-read the records (`leibniz legal licences`
    lists the sources) and move the "seen" dates; the registry's compile
    date is `legal.REGISTRY_DATE`.
28. **Leibniz holdings outside the GWLB (2026-10-14, after a reader's
    request).** The site covers the GWLB's digitised Nachlass (the
    library's three Leibniz collections, as the census found them); an
    editor at the Leibniz-Edition asked that the site say so and consider
    other institutions' scans, the Niedersächsisches Landesarchiv Hannover
    first, since most of that material is unpublished and some is not in
    the Arbeitskatalog. A one-off survey on 2026-10-14, by hand (substring
    queries on the Leibniz-Katalog's Signatur field, `sign_ol=`; records,
    not pages; the search caps at 5,000 rows, so the bare LH and LBr
    families read only "more than 5,000" each; link counts are links, not
    records): "Hannover NLB" 1,059 (Marg. 483; Bibliotheksakten and LK-MOW
    277, which no GWLB digital collection holds; Ms 6); "Hannover NLA"
    4,162 records pointing at 165 distinct Arcinsys units, of which 4 in a
    sample of 24 offer scans (the Landesarchiv's own viewer, static
    derivatives, no IIIF or METS seen; its usage notes put metadata under
    CC0 and digitised items under the Public Domain Mark, and ask written
    consent before an institutional republication); Berlin 1,327 (links to
    SBB shelfmark pages and the BBAW archive's finding aid, no digital
    objects); Göttingen 680 (143 PURLs resolving to the GDZ); Paris 546
    (146 Gallica arks; BnF, NuBIS and Académie des sciences finding aids);
    Gotha 460 (105 into the ThULB digital library); Kopenhagen 443 (200
    Royal Library catalogue permalinks); Wolfenbüttel 431 (129 NLA
    Wolfenbüttel Arcinsys, 38 HAB diglib); London 408 (22 Royal Society
    items); Halle 308, Wien 168, Oxford 67, Dresden 66, Cambridge 58, Rom
    34, München 18, Petersburg 16, Florenz 2, with no or few digital links.
    So the Arbeitskatalog is the list of the diaspora as the Edition knows
    it, and it links roughly 450 records to digitised copies in
    IIIF-capable libraries (Göttingen, Gallica, Gotha, the HAB, the Royal
    Society) plus the Landesarchiv's digitised units. The exact table comes
    from the export (Open question 27): an institution parser over the
    Signatur string and a count of digital-copy links by domain, rendered
    as `reports/holdings.md`; the survey above is superseded by it and is
    not to be quoted on the site. Decisions, none taken: (a) an About
    sentence on scope now, in the short web session Open question 27 names
    (it needs no numbers), and a holdings page from the report, with the
    import; (b) an ingestion phase for the IIIF-served institutions, each a
    source field through the store, a set in browse, an attribution line, a
    rights check (Gallica's terms restrict commercial reuse) and a
    licence-registry entry; (c) the Landesarchiv as its own track, gated on
    a contact, its written consent and a fetch route. (b) and (c) come
    after L1, the re-mint, C3 and the Kurrent steps. **2026-10-21 (W6):**
    (a)'s sentence is on About, EN and DE, in `llms.txt` and the README,
    without numbers; the holdings page waits for the export and the import.
    **2026-10-21 (A3b): the survey above is superseded** by the export's
    own table, `reports/holdings.md` (rendered by `leibniz catalog holdings`;
    on the site `/holdings`): of the **70,405 records, 48,167 (68.4 %)** name
    the GWLB's collections (`Hannover NLB`: LH, LBr, LBrF, LK, Ms, Marg.),
    7,509 carry no shelfmark, **4,218 the Niedersächsisches Landesarchiv
    Hannover** (`Hannover NLA`), 1,700 a printed witness only; then Kassel
    ULB 826, Göttingen StUB 656, Berlin BBAW 622, Berlin SB 542, Gotha FB
    460, Basel UB 440, Kopenhagen KB 439, Paris BN 301, Halle ULB 297,
    Wolfenbüttel HAB 273, Warszawa BN 248, Leiden UB 219, London BL 200,
    London RS 188, Freiberg Bergakademie 178 … (215 holdings); 95 in private
    hands, 72 with no whereabouts stated. **49,341 records link a digitised
    copy**: 39,673 the GWLB (this site's works), 4,189 the Landesarchiv's
    Arcinsys, 509 Göttingen's resolver, 422 Kalliope, 398 the SBB, 375 the
    SLUB, 372 the BBAW archive's finding aid, 358 the MDZ, 318 the TIB, 269
    DOIs, 247 Polona, 205 Gallica, 200 the Royal Library Copenhagen, 112
    Kiel, 108 the HAB … (records, not pages; whether a link opens images, a
    finding aid or a catalogue record is not checked). Decisions (b) and (c)
    stand as written; the figures to size them by are now the table's.
    **2026-10-22 (A3b follow-up):** the page is "Where Leibniz's papers are
    held" (`/holdings`), with one source line from the registry, the
    digitised copies shown only once the store carries the import, and a
    line at the top of Browse pointing to it; the export's date is 19
    October 2026 (provided on the 21st).
27. **The catalogue in the store is part of the Arbeitskatalog (2026-10-10,
    W5's staging look).** The store holds the records of the §70 volumes'
    sweep (C2) and the July sample (A3): 24,916 records, 1,197 of 2,225 works
    with any. `Monadologie` in the browse filter found nothing on staging:
    the Leibniz-Katalog has the piece on LH 4, 1, 1a Bl. 1–6 and LH 4, 1, 1b
    (records 39739, 39743, 39744), and the store has no record for either
    convolute. The Faszikel index, the title search and the convolute names
    from the catalogue reach as far as the records do; the browse page now
    says so when nothing matches. The remedy is the full scrape
    (`reports/crosswalk.md`, "Operator command": signature-prefix slices,
    a few hours at the polite rate, then `leibniz catalog crosswalk`) and a
    new serving copy, or a TELOTA export.
    **2026-10-14:** a one-time export of the Arbeitskatalog has been offered
    by the Potsdam Arbeitsstelle (an up-to-date Access export directly, or
    XML through TELOTA at its half-year import); the scrape is on hold until
    the export arrives or is refused. The import step, when it lands, one
    session: parse the file (mdbtools or a Python Access reader); assert
    that its record identifier is the one the website uses in its addresses
    before any row is replaced (`gt_lines.record_id` and the piece-text
    links depend on it; if the identifiers differ, map them and stop if the
    mapping is not one-to-one); keep the catalogue's links to digitised
    copies; rebuild `katalog_records` and run `leibniz catalog crosswalk`;
    render `reports/crosswalk.md` and a new `reports/holdings.md` (records
    by holding institution, digital-copy links by domain) from the data; a
    new serving copy and restart; the search index carries catalogue
    titles, so a rebuild follows, best bundled with the next one M1 or K4
    needs. Refresh on the catalogue's half-year cycle, and say on About when
    it was last refreshed. Two web items need no export and go first, in a
    short web session of their own: a link from every work page to the
    catalogue's search by shelfmark (`sign_ol=` on the extended search, the
    form the reader's own link used), whether or not the store holds the
    work's records (`1665058609`, Leibn. Marg. 196, has none), and an About
    sentence on scope, EN and DE (Open question 28). The holdings page waits
    for the import, because its numbers come from `reports/holdings.md`.
    **2026-10-21 (W6):** the two web items are built on
    `claude/busy-dirac-n30a43`: the search by shelfmark on every work page
    (the catalogue's spelling checked live — `LBr` without a period, Arabic
    numerals) and the About sentence; the import step and the holdings page
    still wait for the export.
    **2026-10-21 (A3b): closed on the code side.** The export arrived the same
    day (the Access database, as CSV; 70,405 records); the import is built
    and proved on fixtures (`leibniz catalog import-access`: the mapping read
    off the website, the agreement table, the referenced-id check, the
    write, the crosswalk) and waits for the operator's dry run, backup and
    `--write` on the master store, then the serving copy and the index
    rebuild bundled with K4's (Next). **The numbers above are corrected:**
    39739, 39743 and 39744 are the Monadologie pieces' Kat.-Nr., not record
    ids — those records are 55406, 55407 and 54786 (`LH 4, 1, 1a Bl. 1-6`,
    `LH 4, 1, 1b Bl. 1-10`, `LH 4, 1, 1b Bl. 1/1-16/1`), found by shelfmark;
    the record ids 39739, 39743 and 39744 are other pieces. The website's
    identifier is the export's `ID`, one-to-one (23 records checked live, the
    ids of `gt_lines` and the crosswalk asserted before any write). The
    refresh is the catalogue's half-year cycle: a new export, the same
    command; About, the browse page, the work page and `/api/stats` show the
    export's date.
    **2026-10-22 (A3b follow-up): record ids are stable except for merges,
    and the website lags the master.** The operator's dry run found nine
    store ids the export no longer carries (1738, 48726, 58654, 62088,
    69210, 69212–69215), all still on the public website; 48726 is Kat.-Nr.
    18752 there and record 69490 in the export: the Access master renumbers
    or merges a few records between TELOTA's half-yearly imports, so the
    website's copy is older than the export (its `Letzte_Aenderg` runs to
    2026-08-25; record 71572 is on the website not at all). The import maps
    such an id to the export's record with the same Kat.-Nr. and shelfmark
    (else the Kat.-Nr. alone where unique, else `Identisch_mit` or
    `mergenr`), lists the mapping in the report and rebuilds the crosswalk
    under the new id; only an id the ground truth references stops it. A
    link to a record by id (`/api/records/{id}/text`, the catalogue's own
    `id=` search) can therefore go stale at a merge; the Kat.-Nr. is the
    steadier handle.
26. **The twin rule's corpus-wide error is unmeasured (2026-10-10, W5).** The
    thresholds come from 27 works (25 groups checked byte for byte). The line
    check guards against folding two different pages that happen to share a
    size, but a pair whose pages carry no lines is never confirmed (left
    unfolded), and a spread photographed rotated by 180° (not seen) would
    swap its halves. After the rebuild (2026-10-11), `twins` in `/api/stats`
    reads 40,297 groups (39,442 spreads, 855 folds, 519 unconfirmed); the
    operator spot-checked six decisions, five spreads in LBr and LH and one
    fold: all correct (no Marginalien pair came up in that sample). A wider
    sample per family would measure the error; until then the About page
    states the counts as the rule makes them.
25. **Kalliope's terms (2026-10-10, W5).** Kalliope has a record per LBr
    convolute (its ids are our work ids) with correspondents and places by
    GND and, for 387 convolutes, the letters by folio ("Darin: Blatt 1: Brief
    von …"). Its site states no licence; its participation contract grants
    publication of the metadata under CC BY-SA, and the GWLB's digitisation
    policy puts its own metadata under CC0. Ask before harvesting; the
    letters come from correspSearch (CC BY 4.0) meanwhile. **2026-10-21
    (L1):** the licence registry carries the entry (`kalliope`: no licence
    stated, seen 2026-10-10, not used).
24. **The PHILIUMM model does not read Kurrent as noise (2026-10-09, K1).**
    The C2 factory minted 40,915 lines on the 2,173 German pieces (10.2 % of
    their 401,394 recognised lines, half the Latin and French rate); 27,643
    of them carry German stopwords in the minted text, at a mean confidence
    of 0.839 on machine text of 41.0 folded characters a line — chance
    alignment gives ≈ 0.50 at 60 % CER
    (`reports/kurrent/align-tolerance.md`). Either the model's multilingual
    FoNDUE-GD base reads Kurrent in part, or the accepted lines are the
    legible minority (dates, names, Latin-script words inside German lines).
    The K1 pilot (Task 4) measures the baseline's German yield and shows the
    operator the crops; if the lines are right, a slice of the German ground
    truth is already minted and the baseline is a candidate reader for K2 in
    its own right. *Answered by Tasks 3 and 4:* on the Dresden chancery hand
    the model reads at 29.5 % CER (the Bern TrOCR model 7.4 %); on the
    pilot's German lines it mints 12.5 % at the factory's gate, the stored
    v1 text 16.4 %, the Bern model 20.2 % — a reader, the weaker one, and on
    Leibniz's own hand the weakest (8.1 % against 25.4 %).
23. **The factory's Textart rule never fired (2026-10-09, K1).**
    `stratum_from_textart` matches full words (`reinschrift`, `abfertigung`,
    `konzept`, `abschrift`, `auszug`); the catalogue writes abbreviations
    (`Abf.`, `Konz.`, `Abschr.`, `Ausz.`, `Reinschr.`). A document class was
    recognised on 129 of the 10,121 pieces with a text, so the C2 mint's
    stratum — and its threshold — came from the layout statistics alone.
    Teaching the rule the abbreviations is a one-line change that moves a
    share of the minted lines between strata; the thresholds were set
    against the layout stratum, so it belongs with C4's calibration, not in
    a re-mint on its own.
22. **The browse index wants two authorities (2026-10-06, W3).** (a) *LH section names* are cut from the GWLB's titles: LH 11 reads "Allgemeinen Geschichte" (the title's dative), LH 9 "Archälogie" and LH 15 "Würtemberg" (the library's spellings), LH 37 and LH 42 have no name (their titles name sub-groups), and the twelve sections without a digitized unit are absent. A reviewed table of the 42 section names would settle all four; the question to the Leibniz-Edition is whether the grouping matches how the Arbeitsstellen think of the Faszikel. (b) *Correspondents*: 380 of the 1,060 letter convolutes are unnamed (316 without linked records, 4 whose records name nobody, 60 whose names do not fit the order of the LBr numbers). A full Arbeitskatalog export completes them with no code change. The order check cannot see a wrong name that happens to fit alphabetically, and the F series has no order to check against; a reader who knows the convolutes should look over the named ones once (`/api/works?family=LBr`).
21. ~~**Fold the metadata fields in the Meilisearch index (2026-10-02).**~~
    **Resolved in code (W5); live with the next index rebuild** (`meta_folded`;
    `leibniz index settings` refuses an index built without it). Original note: Titles, shelfmarks, AA references and folio labels are indexed as written, so a quoted reference finds nothing (W2), and even unquoted a Roman numeral with V or J never meets its folded form: *VI* is sent as *ui* and no typo is allowed under four letters. Measured on 1.53.2: `VI` does not find a page whose only VI is in `AA VI,4 N. 109`, and `AA VI,4 N. 109` finds it only through the bare *aa*, below an unrelated page whose text has *aa*. FTS5 folds those columns. Index folded copies at the next rebuild (C4) — a rebuild drops and refills the index, so not in a routine deploy.
20. ~~**Multi-word queries on Meilisearch are not AND (2026-10-02).**~~
    **Resolved in code (W5):** `matchingStrategy: "all"` by default, `match=any`
    on request (a box under the search field). Original note: `meili.py` sends no `matchingStrategy`, so Meilisearch's default `last` drops words from the end of the query when results run short and typo-matches the first word left: live, `deus mundus` reports 97,633 hits (at result 8,900, 98 of 100 hold neither word — French *des*) and `mundus deus` 3,775, where FTS5 requires every word. `matchingStrategy: "all"` would make the backends agree and the counts honest, at the cost of pages where a word was misread past typo tolerance — a product decision, open. Quoted phrases and exclusions hold under either strategy.
19. ~~**Sheet-sides registered twice (2026-09-23).**~~ **Resolved in code (W5,
    2026-10-10); live with the next index rebuild.** `images/twins.py`: found
    from the store, confirmed by line geometry, spreads split, the rest folded;
    the About page states the distinct-scan count the build writes.
    Original note: Static-JPEG works list one scan of an unfolded sheet under two folio labels; the corpus run read each twice. Run `leibniz images duplicates` over the thumbnails, publish the distinct-scan count, fold twins in the index build, and restate `pages`/`lines` on the About page.

0. **Strategy review 2026-09-16 → `NOTES.md`** (accuracy levers incl. the review-queue design and the LLM-as-detector pilot; the Calculemus rescope and the missing `leibniz pack` seam; the four Academy seams; loose ends). The C3 changes live in the amended C3 prompt.
1. ~~IIIF vs static delivery (A2).~~ **Resolved for A2:** cache the uniform METS
   `DEFAULT` JPEG for every page. **D2 still** must degrade to a plain image where
   no IIIF Image API exists (only the ~33% IIIF works get deep-zoom).
2. ~~`pages` population is partial.~~ **Resolved:** all 236,795 pages derived
   offline from the METS `fileSec` via `images pages`.
3. **Katalog full scrape — the §70 volumes are done; the rest is an operator
   job.** `catalog scrape --expired-volumes` sweeps every expired volume in ~10
   min (substring `bd` matching + year deepening, see the C2 log). The remaining
   ~45k non-§70 records still need signature-prefix slices (or the `id_hannover`
   enumeration) for A3's ≥80 % work coverage; a TELOTA dump would moot it.
4. **Shelfmark-secondary limits (A3).** The normaliser matches LH/LBr cleanly, but
   some Marginalien records carry page/prose signatures (`Leibn. Marg. 10, 1, S.
   154-166`; relocated `(jetzt LK-MOW …)` notes) that don't match a work key —
   because the *work's* shelfmark form differs (`ZEN Leibn. Marg. N` vs the
   record's part/page form) or the work isn't in the sample. Impact is small
   (shelfmark is 198 of 12,582 links); the GWLB link carries the crosswalk. Ties
   into the multi-volume Marginalien part-suffix issue below.
5. **Marginalien scope** (from A1). 396 annotated printed books, 103,887 pages
   (44% of pages). HTR target is the *marginal annotations*, not the printed body —
   a C1/C4 segmentation/stratum concern, flagged early.
6. _(A0)_ §71 editio-princeps assumption; re-edition term restarts — for the
   lawyer memo (SPECS §7.5).
7. **B1 residual gap (0.38 pt).** Our 7.95% is *below* the 8.33% claim but ~0.5 pt
   above what a matched ketos-test might report; ruled out normalization as the
   cause (sensitivity <0.4 pt). Likely subset composition / their exact eval
   harness. Immaterial to the gate; note it if we ever re-run their `ketos test`.
8. **No per-line language labels in the PHILIUMM GT** (features are `text`+`image`
   only). The 7.95% is a Latin+French number by construction; a real per-language
   split waits for the C4 language-ID pass. German/Kurrent remains unmeasured here.
9. ~~**LLM-on-Leibniz numbers pending a key.**~~ **Done** — a supplied OpenAI key
   ran the 3-model VLM panel (gpt-4o/4.1/4.1-mini): 35–46% CER, 4–6× the fine-tuned
   model. The `anthropic` adapter is equally ready for a Claude comparison. Finding
   worth following up: the *smallest* VLM scored best — the larger models modernise
   archaic spelling more (a prompt-engineering lever, not pursued in Tier 1).
10. ~~**(B2) Piece→canvas localization.**~~ **Resolved (C2):** `align/resolve.py`
    turns a katalog `Bl.` range into exact canvases via the IIIF folio labels C1
    now stores on `pages.label`. Offline-tested; the single biggest C2 gap, closed.
11. ~~**(B2) Draft strata need a higher threshold.**~~ **Addressed (C2):**
    `align/stratum.py` + `factory.STRATUM_THRESHOLDS` set the mint threshold per
    piece (fair 0.55 → heavy 0.72) from the C1 seg-stats + katalog `textart`. C4
    calibrates the thresholds against the GT audit.
12. ~~**(B2) Edition-text extraction QA at scale.**~~ **Addressed (C2), measured
    at scale (2026-09-11):** `volumes.assess_extraction` runs for free between the
    two independent OCR layers of the same volume (IA Tesseract vs GWLB ABBYY):
    5 volumes, mean agreement 81.6%, 54/200
    pieces flagged. The live vision QA (gpt-4o, 1/2 flagged, 0.67) stands as the
    two-model variant. Residual OCR error in the labels is the known cost of the
    free path; the priced vision upgrade is in `reports/gt-factory.md`.
13. ~~**(C2) Real GT minting awaits three operator inputs.**~~ **Resolved
    (2026-09-16):** the §70 katalog sweep + crosswalk ran here, the page
    anchors come from the print itself (every AA page's running head names
    the pieces starting on it, so `align/edition.py` derives piece → page
    ranges from the volume's own text layer — no TELOTA dump needed), and the
    mint ran on the operator's store: 297,424 lines (C2 log). What remains
    for the gate is precision, i.e. the hand audit (Q #18).
16. **(C2) Ten §70 volumes have no free digital copy** (I,1, I,2, I,4, I,5,
    I,13, II,1 (1926), III,2, VI,2, VII,1, VII,2 — 6,082 of the
    17,162 piece citations). HathiTrust holds the ≤1928 prints as
    US-public-domain (US-IP viewing), the Göttingen repository (bot-challenged
    here) and a TELOTA/Leibniz-Archiv ask cover the rest; Münster's II/VI,4
    Internetausgaben need written permission. Also for the lawyer memo: the GWLB
    repositorium PDFs are a **CC BY-NC channel** for §70-free text — the
    registry prefers the unencumbered archive.org scans and flags GWLB-only
    volumes (I,3, I,14, I,15).
14. ~~**(C1) Segmentation on Marginalien / drafts is unmeasured on real images.**~~
    **Measured (2026-09-11):** the corpus run put a `page_stats` row on every
    segmented page — line counts, region coverage, height-CV, overlap and
    short-line anomalies across all sets and strata (`reports/htr-v1-sample.md`
    carries the distributions). The observed failure modes (speck lines on scrap
    pages, sliver crops, ~120 MP foldouts) are guarded and enumerated rather
    than fatal; threshold re-tuning against these real distributions is now a
    C4 calibration task with data in hand.
15. ~~**(C1) Line-confidence source.**~~ **Resolved (2026-09-11):** real CTC
    posteriors populate at corpus scale — 13.5M recognised lines carry
    confidences (mean ≈0.77 on the validation slice; `conf > 1` count is 0
    corpus-wide after the `140d58d`/token-layout fixes). They are ready to gate
    search and the UI.

18. **(C2) Precision of the minted GT — audited 2026-10-07, restated.** The
    PHILIUMM team judged 199 of the 200 lines: **weighted precision 72.3 %
    as written, FAIL at 95 % in every stratum; 92.2 % with boundary slips
    counted usable** (`reports/gt-audit.md`, C2b log). Read by pattern, the
    gate as written measures three different things at once. (a) *Does the
    mint pick the right line?* Yes: one misaligned line in 185 scored. (b)
    *Does the slice start and end where the line does?* Not always: 35 lines
    are a letter or a short word off at an end (18 %, worst in scraps and
    heavy revision), and 13 lost the scribe's line-end hyphen (fixed in the
    aligner; the re-mint before C3 applies it). (c) *Is the edition's text
    the page's text?* No, by design: accents, capitals and commas the
    edition regularises (16 lines), disputed readings (4), editorial brackets
    leaked from the apparatus (7), formulae (5) and inline additions (2) are
    the reading text being a reading text. The levers, in order: the
    re-mint with hyphens kept; the C3 exclusions (math, Marginalien, bracket
    lines — Amendment 2); Denisa's apparatus-reinsertion script for the
    additions (Standing items); and for the boundary slips Q #17's edge
    scatter plus a one-letter cut at line ends that is as much the segmenter's
    crop as the aligner's. What stays open: a second judging round on a fresh
    200 after the re-mint (the sheet and the CSV shape are theirs to reuse),
    and C3's ablation as the empirical test. The threshold levers
    (`STRATUM_THRESHOLDS`) would not have helped: the failing lines are
    well-aligned.
    **2026-10-20, after the re-mint (C2c):** the first lever is pulled. Of
    the 315,797 re-minted lines, 848 (0.3 %) still end in a letter where
    the HTR read a line-end mark (7,822, 2.6 %, before), 540 of them the
    last minted line before an unminted one, and 8,523 lines now end in
    the scribe's mark; the lines where the HTR read no mark remain, and only
    a reader or C3 sees them. Editorial brackets 4,811 (1.5 %) and math
    lines 255 (0.1 %, a floor) are flagged in `data/gt/flags.jsonl` for
    C3's exclusions. **The second judging round is now possible**: a fresh
    200 of the re-minted lines, drawn with `--seed 1`, 50 a stratum, in the
    first round's CSV shape (`reports/gt-audit/round2/gt-audit.html` and
    `gt-audit-lines.csv`), to offer the PHILIUMM team; its score against
    the first round's would measure what the re-mint changed for a reader.
17. **(C2) Edge-of-passage scatter under unit costs.** With the HTR ends not
    free (the piece's lines must all be consumed) and the edition ends free,
    the DP is indifferent between matching the passage's last few characters
    in place and scattering them as chance single-character matches over
    uncovered manuscript further down (a tie; the leading side is even a local
    win for the scatter). The band now caps it at ≤ `band` (256) characters
    per end; the full DP scattered without bound. Effect: the last line(s)
    before a stretch of uncovered manuscript can be minted missing their
    final characters. Measure on the hand-audit sheet; candidate fixes are a
    tie-break that prefers deletions past the last anchor, or freeing the HTR
    ends *inside* the anchored band (no longer degenerate there).

---

## Divergences (recorded per the COMMON-CONTEXT rule)

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

## Next

**ARCH1 (2026-11-17): the archive is built on `claude/blissful-mccarthy-ktud6m` (compare: https://github.com/marchofhares/LeibnizLegible/compare/main...claude/blissful-mccarthy-ktud6m?expand=1); the operator opens and merges the pull request before any other session branches, since STATUS.md and PROMPTS.md are the files every session appends to; from the merge on the preamble's clause 8 holds — the entries before 2026-10-19 are in `STATUS-archive.md`, the prompts already run in `PROMPTS-archive.md`, nothing is appended to either, and a prompt that names an archived entry means the archived text.**

**K3b and P1 Task 3 can start (2026-11-16).** The inputs both waited for are
in: the Edition's verdicts on K2's sheet (6 November; converted and scored in
K3b's Task 0 by hand group, strict and under the fold; the 76 confirmed and
118 corrected lines seed the verified set) and PHILIUMM's v2 segmentation
model (3 November; P1 Task 3 runs on it, the sample drawn outside her training
pages, listed from her public dataset, and the held-out pages). The GPU has been idle since
30 October. Order on the desktop: K3b Tasks 0 to 2, stopping at checkpoint B
while the hand work is made; P1 Task 3 and M1's print trial in that gap; R1
Part B after its Part A; K3b Tasks 3 to 5 when the verified set is in. In the
cloud first: the archive of the old phases, alone and merged before anything
else branches; then a small K3b-prep session (the verdict converter, the
corrections column through the pattern code, context lines on the audit
sheet, the registry entries `philiumm-seg-v2` and `edition-k2-audit`); then
REL1 Part A, G1b, R1 Part A. The notes for the sessions are on the operator's
plan page, with the order of 2026-11-16: the archive alone and merged first;
P1 Task 3 on the desktop beside K3b-prep in the cloud; then K3b Tasks 0 to 2
with REL1 Part A beside it; M1's print trial in K3b's gap; REL1 Parts B and
C; R1; G1b and the game session. The Edition's table is on the desktop as
`data/kurrent/k2-audit-verdicts-edition.csv` (ref, stratum, verdict,
transcription, note) with a stopgap C2-shaped `k2-audit-verdicts.csv` made
outside the repo the same day, which K3b-prep's converter regenerates; the
corrected lines' licence is settled (Open question 33 b), so the verified
set goes to the open deposit.

**The box's disk (2026-10-31): a Hetzner volume before C4's index rebuild.** The root disk is 75 GB; the live store copy (16 GB → 18 GB now), a staging copy during a switch, Meilisearch with one index (15 GB) and a second index during any rebuild beside a live one do not fit together, and the staging build of 31 October filled it. A 100 GB volume (a few euros a month, attached without a reboot: format, mount, fstab) for `/var/lib/meilisearch` or `/var/lib/leibniz-legible`, the service stopped for the minutes of the copy; a desktop chore with the box commands from deploy/README.md, before C4's rebuild and before the next staging index. The plan page's standing item has it.

**K4 (2026-10-28): the next round's item — a second language pass.** K4
read the German pages the language pass found at the threshold hits≥2
score≥0.3 tokens≥8 (`leibniz enrich page-lang`; on the census's pieces
precision 95.2 %, recall 74.5 %, so about three quarters of the German pages
by that measure: 30,797 pages called German, 24,078 of them in the job, the
Marginalien left out); a German page the pass missed keeps v1's text and
shows as such. Next round: a second pass with a stronger signal — the
identifier over READER's own text on the pages the first pass left
`unknown` or `mixed` with German second, the census's German pieces'
neighbouring pages, or a lower threshold measured again on the census —
then the reading job over the newly found pages only (resumable; a second
scoped run beside the first, the precedence rule showing the newest), the
page_lang table updated under its own runs row, and the index rebuilt. C4
keeps its run unscoped and leaves German pages alone.

**LT1 (2026-10-30): Part B done on the desktop; the numbers are in
`reports/htr/page-llm.md`, committed on `lt1-results` and carried to the
operator's pull request from `claude/gracious-thompson-pp1ror` with this
entry; nothing deployed; the operator sends the report's tables to the
colleague with the report's caveats.** LT1b, a small cloud session when
wanted: (a) the kraken row measured on this harness — the 27 pages read
through kraken's own XML line extraction (the path the dataset's crops came
from) instead of `page-lines`' audit crop, so the dedicated model's page CER
stands beside the page models' on the same scans, and the 26.29 % against
7.95 % gap is explained in the report; (b) `page-score` skips a JSONL
without `page_id` instead of failing, and the runbook keeps line dumps out of
the readings folder; (c) Gemini Carbon, when the models list serves it, as
one more read with a price row; (d) the page models' reading order against
the segmenter's on the 100 pool pages, from the readings already on disk.
The rerun cadence (the plan page's standing item): each new model served,
after each of K3b, R1 and C3, and before any public claim about the readers.

**LT1 (2026-10-28): Part A built in a cloud session; the branch
`claude/kind-tesla-xhk9ac` carries it (compare:
https://github.com/marchofhares/LeibnizLegible/compare/main...claude/kind-tesla-xhk9ac?expand=1);
merged as #56; nothing deployed. Part B, done 2026-10-30 (the block above
has the numbers), was the operator's, from the second checkout beside K4's reading job: the reads
are API traffic on the CPU (no torch process, no GPU); the one kraken step
waits until K4's job has ended.** The keys as environment variables
(`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`; `OPENAI_API_KEY` only if gpt-5.5 is
wanted), never in the repo; the master store read-only; the pool's texts
never leave the machine (only page images go out, the GWLB's public-domain
scans). In order, each with its expected cost (the dry run's estimates from
this session, at the pricing tables with 1,500 output tokens a page assumed
and the image sizes assumed; the real run logs the APIs' own usage) and time:
   1. **The checkout and the environment.** Before the merge
      `git -C ~/LeibnizLegible-g1 fetch origin claude/kind-tesla-xhk9ac && git -C ~/LeibnizLegible-g1 checkout --detach origin/claude/kind-tesla-xhk9ac`,
      after it `… fetch origin main && … checkout --detach origin/main`; then
      `cd ~/LeibnizLegible-g1 && export UV_PROJECT_ENVIRONMENT=.venv-g1 && uv sync --extra web --extra gt --extra release`
      and, if `uv run --no-sync python -c 'import numpy'` fails,
      `VIRTUAL_ENV=.venv-g1 uv pip install numpy` (the pool metric needs it;
      one package). Seconds to a minute.
   2. **The val pages from the Hub** (CC BY 4.0; one request a second):
      `uv run --no-sync leibniz bench page-fetch --val-pages /home/evana/LeibnizLegible/data/gt/philiumm-val-pages`
      → `page-fetch 54 files fetched now, 54 present in …` (27 JPEG + 27 XML;
      the one page fetched here was 2.3 MB, so the lot is of the order of
      tens of megabytes; about a minute of requests). Free.
   3. **The dry runs** (no call; the plan with the real image sizes, the pool's
      from `/mnt/d/leibniz-images`): for each of
      `--engine gemini --model gemini-3.1-pro-preview`,
      `--engine gemini --model gemini-4-argon`,
      `--engine anthropic --model claude-fable-5-1`:
      `uv run --no-sync leibniz bench page-read --pages reports/htr/page-list-philiumm.csv --pages reports/htr/page-list-pool.csv <engine and model> --images /mnt/d/leibniz-images --val-pages /home/evana/LeibnizLegible/data/gt/philiumm-val-pages --out /home/evana/LeibnizLegible/data/bench/page-llm --max-cost 20 --dry-run`
      → `134 calls to make … pages {'philiumm': 34, 'pool': 100} … estimate:
      <input tokens> (image sizes known for 134 of 134) + 201,000 output
      tokens assumed … → <USD>; cap 20.00 USD`. This session's figures with
      the sizes assumed: gemini-3.1-pro-preview 2.85 USD, gemini-4-argon 2.45
      USD, claude-fable-5-1 14.80 USD (gpt-5.5 2.21 USD if run). Then the go.
   4. **The reads**, the same three commands without `--dry-run` (the cap of
      20 USD a model stays; a run that stops at the cap or on an error is
      resumed by running the command again; `--redo failed` reads the failed
      pages once more). Expected per command: a line per page
      `<model>: <page> [<column>] ok · N lines · <in>+<out> tokens · <USD> ·
      <s> s`, then `done: 134 read, 0 skipped, statuses {…}, <USD> USD → …`.
      Time: unmeasured until the first pages print their seconds; bounded by
      the 300 s deadline a call (`--timeout`), the polite half-second between
      calls, and one retry per failed page. Cost: the estimates above, the
      real figure in the log. The readings land in
      `/home/evana/LeibnizLegible/data/bench/page-llm/<model>.jsonl` and the
      images sent under `…/page-llm/images/` (gitignored; keep them: they are
      the record of what each model saw).
   5. **The kraken model on the same lines** — after K4's reading job has
      ended (one torch process on the machine), from the main checkout in
      `.venv-k1` (kraken 7.0.3; CPU is enough — B1 read the 1,878 val lines
      in about 160 s on CPU):
      `cd ~/LeibnizLegible && UV_PROJECT_ENVIRONMENT=.venv-k1 uv run --no-sync leibniz bench page-lines --val-pages data/gt/philiumm-val-pages --out data/bench/page-llm/val-lines`
      → `page-lines <n> lines written to …` (the val XML's lines with text and
      geometry; the parquet's val split has 1,878 rows), then
      `UV_PROJECT_ENVIRONMENT=.venv-k1 uv run --no-sync leibniz bench run data/bench/page-llm/val-lines --engine kraken --out data/bench/page-llm/kraken-val-lines.jsonl`
      → `kraken@FoNDUE-GD_v2_ft_Leibniz on <n> lines [philiumm]: CER …`
      (B1's model, the default path; the number should sit near B1's 7.95 %
      if the cut matches the dataset's own crops, and the report quotes what
      it is). Minutes. (The main checkout must carry the branch or the
      merged main for `page-lines` to exist: `git pull --ff-only` after the
      merge, or run from the second checkout with `UV_PROJECT_ENVIRONMENT`
      pointing at the main checkout's `.venv-k1` and `PYTHONPATH=src`.)
   6. **The scoring** (the store read-only; the pool's texts verified against
      the frozen checksums first):
      `uv run --no-sync leibniz bench page-score --set philiumm --pages reports/htr/page-list-philiumm.csv --readings /home/evana/LeibnizLegible/data/bench/page-llm --val-pages /home/evana/LeibnizLegible/data/gt/philiumm-val-pages --kraken-lines /home/evana/LeibnizLegible/data/bench/page-llm/kraken-val-lines.jsonl --scores reports/htr/page-llm.scores.json`
      → a line per reader `<model>: page CER … with <k> failed pages charged;
      … with them left out; 34 pages` and the kraken row; then
      `uv run --no-sync leibniz bench page-score --set pool --pages reports/htr/page-list-pool.csv --readings /home/evana/LeibnizLegible/data/bench/page-llm --db /home/evana/LeibnizLegible/data/inventory.sqlite --testset reports/kurrent/letterpool-testset.csv --texts /home/evana/LeibnizLegible/data/kurrent/letterpool/testset.jsonl --pool-readings /home/evana/LeibnizLegible/data/kurrent/letterpool-readings --scores reports/htr/page-llm.scores.json`
      → `34 letters, 100 pages (L 50, K/k 50)`, a line per reader (`v1`,
      `k3-trocr`, `k3-kraken`, `trocr-kurrent-xvi-xvii` where their readings
      are on disk, `page:<model>` for each model) with CER and interval, the
      failed pages and the letters with every page read. Seconds to minutes;
      free.
   7. **The report**: `uv run --no-sync leibniz bench page-report` →
      `reports/htr/page-llm.md` and `.json`. Read it; then from the main
      checkout commit `reports/htr/` (the lists, the score file, the report —
      numbers only; nothing under `data/`), write the headline numbers into
      the LT1 entry and Current state, push, and print the compare URL. The
      report's numbers go to the colleague as they are, with the two caveats
      (the sets are small; the pool's references are checked letter
      transcriptions of 1708–1716, not a random sample of the German pages).

**A3b (2026-10-21, the follow-up 2026-10-22): built in a cloud session on
fixtures cut from the export; the branch `claude/adoring-volta-eogav8`
carries it (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...claude/adoring-volta-eogav8?expand=1);
the operator opens and merges the pull request; nothing written to the
store, nothing deployed.** The operator's first dry run (2026-10-22) is read
and answered (the Current state entry of that day): the dry run runs again
on the branch before the merge, from the second checkout at the branch's
head, or after the merge from main. The export sits on the desktop at
`data/external/arbeitskatalog/csv/` (gitignored; the zip's `csv/` folder
flattened so `ritter.csv` lies directly under it). In order:
   1. **The dry run again, from the second checkout** (the store opened as
      every catalog command opens it; no table written): before the merge
      `git -C ~/LeibnizLegible-g1 fetch origin claude/adoring-volta-eogav8 && git -C ~/LeibnizLegible-g1 checkout --detach origin/claude/adoring-volta-eogav8`,
      after it
      `git -C ~/LeibnizLegible-g1 fetch origin main && git -C ~/LeibnizLegible-g1 checkout --detach origin/main`,
      then `cd ~/LeibnizLegible-g1 && export UV_PROJECT_ENVIRONMENT=.venv-g1 && uv sync --extra web --extra gt --extra release`,
      then `uv run --no-sync leibniz catalog import-access --db /home/evana/LeibnizLegible/data/inventory.sqlite --csv-dir /home/evana/LeibnizLegible/data/external/arbeitskatalog/csv --export-date 2026-10-19 --dry-run --report /home/evana/LeibnizLegible/reports/import-access-dryrun.md`
      (`--export-date` is required; the export is of 19 October). Expected,
      in this order: `catalog import-access ← …: ritter.csv 70,405,
      pdf_url.csv 18,995, pers_norm.csv 1,569, …`; `70,405 rows mapped to
      records`; `Records in the store: 24,916 · compared with the export:
      <n> (of them 9 under another id) · in the store but not in the export:
      <m> · in the export only (new): <k>`; the agreement table — the five ✱
      rows (textart, signatur, titel, datum, aa) should each read ≥ 99.0 %
      (the second run read signatur 99.6 %, titel 99.9 %, textart and aa
      100 %), `datum` now with its 397 second-date rows under `Exact` and
      the website's short second dates (`(123)` for `(00-01-23)`) under
      `Website short date`, the master's corrections (16706, 16707) under
      `Other`, the angle-bracket rows under `Website lost markup`, the names
      under `Exact` rather than `Markers only`; `The export restores text the
      website's parser lost as markup on titel …, incipit …, textart …,
      umfang … records.`; `Records in the store whose id the export no
      longer carries: 9 …` with a line per id (`48726 (Kat.-Nr. 18752, LBr
      543 Bl. 3): → 69490 by Kat.-Nr. and shelfmark`, and the others' new
      ids or `no match in the export`); `The hand rule (catalog/hands.py)
      gives the same answer before and after on 24,891 of 24,907 records
      (the export's fuller Textart decides; listed, not blocking):` and the
      sixteen with before and after — paste them into the A3b entry; a
      `crosswalk: record <id> is carried by the export as <new id>; its
      links are rebuilt under that id` line per remapped id (or `… not in
      the export; its links are dropped by the rebuild`); `every record id
      the ground truth references exists in the export` (a red `STOP:` line
      with ids instead ends the run with exit 1: paste the ids into the pull
      request and stop); `Mapping: **settled**` (or `NOT settled`: then the
      examples say why — for `datum`, the remaining "other" examples are to
      be sent back — and `--force` is the operator's call, not this
      session's); `Dry run: nothing written.` About a minute. The table is in
      `reports/import-access-dryrun.md`: commit it with the reports below,
      and paste the five ✱ rows and the sixteen hand changes into the A3b
      entry.
   2. **The backup chore** with today's date (the store is about to change),
      then the go.
   3. **The write**: the same command with `--write` in place of `--dry-run`
      (`--force` only after a NOT-settled table has been read). Expected:
      `Run <id>: 70,405 records written, <m> deleted …`; `Crosswalk rebuilt:
      <links> links · records matched <r>/70,405 · by method gwlb_link <g>
      (+<u> to objects not in the store) · shelfmark <s>` (A3's sample
      resolved 12,384 of 12,389 link matches; the 39,257 id and 416 PPN links
      should resolve as well, the unresolved ones being GWLB objects outside
      the five sets); `Works: <with> of 2,225 carry a record, <without> none.
      Records per work (works in each band): 1: …, 2–5: …, 6–20: …, 21–100:
      …, 101–500: …, over 500: …; the most on one work: …`; `URL_Ms outside
      the GWLB: <n> records (<k> link nothing); by domain:
      www.arcinsys.niedersachsen.de …`. A few minutes. Then
      `uv run --no-sync leibniz catalog holdings --db /home/evana/LeibnizLegible/data/inventory.sqlite --out /home/evana/LeibnizLegible/reports/holdings.md`
      (the works section now filled: `<with> of 2,225 works carry at least
      one record`) and
      `uv run --no-sync leibniz catalog report --db /home/evana/LeibnizLegible/data/inventory.sqlite --out /home/evana/LeibnizLegible/reports/crosswalk.md`;
      commit the three reports from the main checkout (the second one is
      detached) and write the write's figures into the A3b entry.
   4. **The serving copy and the restart** (deploy/README.md §2, §9):
      `deploy/prepare-store.sh data/inventory.sqlite inventory-serving.sqlite`,
      the rsync, the restart of both units; the index rebuild (§5; the
      catalogue's titles and the pieces on each page are indexed, so the
      search and the page documents follow the new records only after it)
      bundled with K4's, with the staging unit stopped as on 2026-10-11.
   5. **Staging before the merge** (the branch on the live store, which still
      holds the website's 24,916 records: the wording is the partial one):
      `ssh <target> sudo /opt/leibniz-legible/deploy/staging.sh claude/adoring-volta-eogav8`
      (the target and the user name on the plan page), then over HTTP, the
      expected answer after the arrow:
      - `curl -su USER https://staging.leibnizlegible.com/api/stats | python3 -c 'import sys, json; print(json.load(sys.stdin)["katalog"])'` → `{'records': 24916, 'refreshed': None}`;
      - `curl -su USER https://staging.leibnizlegible.com/api/holdings | python3 -c 'import sys, json; d = json.load(sys.stdin); print(d["records"], d["refreshed"], d["works"], d["works_with_records"], d["by_holding"][0]["holding"], d["credit"]["text"])'` → `24916 None 2225 1197 Hannover NLB Source: Arbeitskatalog der Leibniz-Edition, Leibniz-Edition Potsdam I (BBAW), CC BY 4.0, export of 19 October 2026` (the holdings read from the website records' shelfmarks);
      - `curl -su USER https://staging.leibnizlegible.com/holdings | grep -o "Where Leibniz&#x27;s papers are held" | wc -l` → `3` (the title, og:title and twitter:title), and `| grep -c "papers lie"` → `0`;
      - `curl -su USER https://staging.leibnizlegible.com/work/00068642 | grep -c 'export of 19 October 2026</p>'` → `1` (the source line above the records), and `curl -su USER https://staging.leibnizlegible.com/browse | grep -c 'Looking for something that is not here?'` → `1`;
      - `curl -su USER https://staging.leibnizlegible.com/work/DE-611-HS-854976 | grep -c 'holds part of the Arbeitskatalog so far'` → `1` (the W6 wording, until the import);
      - `B=$(curl -su USER https://staging.leibnizlegible.com/about | grep -o '/static/m/[0-9a-f]*/' | head -1); curl -su USER "https://staging.leibnizlegible.com${B}i18n.js" | grep -c "'about.what.scope.whole':"` → `2`, the same file `| grep -c "'holdings.heading':"` → `2`, `| grep -c "aufbewahrt werden"` → `3` (the heading, the About sentence, the Browse line), `| grep -c "papers lie"` → `0`;
      - `curl -su USER https://staging.leibnizlegible.com/llms.txt | grep -c '/api/holdings'` → `2`, and `| grep -c "not from the catalogue's website"` → `1`;
      - `curl -su USER https://staging.leibnizlegible.com/robots.txt | grep -c '^Allow\|^Disallow'` → `10` (A3b touches no robots rule).
      In the browser, with the password: `/holdings` (EN and DE: the
      one-sentence intro, the table with its footnote, no digitised-copies
      block, the works heading "before the catalogue import", the source
      line with its two links), `/browse` (the line at the top), `/about`
      (the second paragraph of "What this is" and the holdings link after
      it; the catalogue block under Licensing says the records come from the
      export, EN and DE), `/work/00068642` (the source line above its two
      records). Then merge and the §9 update.
   6. **After the write and the new serving copy** (the live site, or staging
      against it): `… /api/stats … ["katalog"]` → `{'records': 70405,
      'refreshed': '2026-10-19'}`; `curl -s https://leibnizlegible.com/api/works/1665058609 | python3 -c 'import sys, json; k = json.load(sys.stdin)["katalog"]; print(len(k), k[0]["record_id"], k[0]["match_method"], k[0]["title"][:40])'` → `1 1585 gwlb_link [Marg. in: Dal Pozzo, Maraviglie heroiche` (Marg. 196, by its PPN link); `curl -s 'https://leibnizlegible.com/api/contents?q=monadologie' | python3 -c 'import sys, json; d = json.load(sys.stdin); print(d["total"], [m["where"] for w in d["works"] for m in w["matches"]])'` → `1` or more, the matches on `LH 4, 1, 1a Bl. 1-6`, `LH 4, 1, 1b Bl. 1-10`, `LH 4, 1, 1b Bl. 1/1-16/1`; a work page with an outside link: `curl -s 'https://leibnizlegible.com/api/lookup?q=LBr.%2098'` names the work of LBr 98, whose `/api/works/<id>` records carry `url_ms` `http://kalliope-verbund.info/DE-611-HS-959406` and whose `/work/<id>` page reads `Digitised copy at kalliope-verbund.info`; `/api/holdings` → `records` 70405, `by_holding[0]` `Hannover NLB` 48167, `works` 2225 and `works_with_records` as the write reported. In the browser: `/about` EN and DE (the scope paragraph now ends "refreshed 2026-10-19 from the Arbeitsstelle's export"), `/holdings` EN and DE (the whole table, the digitised copies, the works heading "the whole Arbeitskatalog, refreshed 2026-10-19"), `/browse` with `Monadologie` in the filter (the convolutes LH 4, 1, 1a and 1b listed under "In the catalogue's pieces"); `/api/works/<the work of LBr 543>` carries record 69490 where the website had 48726.
   **Later, not now:** the persons and places tables (GND links on the work
   page, GeoNames for the places); the refresh with the next export (the same
   command with its date). No email is drafted here: the Arbeitsstelle's
   export is acknowledged by the operator.

**G1 (2026-10-21): merged as #51; the real pack built and checked on the
desktop the same day** (`/mnt/d/leibniz-packs/fragments-2026-10-22.jsonl`,
pack `ll-fragments-2026-10-21-s20261022-e86be52b1c`: 2,000 rows, gold 56;
the G1 entry in the Phase log). **Before the copy to the box, the owner's
choice** (Open question 30 (g)–(i)): ship this pack as the trial it is, or
have a cloud session add a gold-first draw (and, if the count below is
large, a floor on the shorter reading) and rebuild — six and a half minutes
on the desktop. The count, from the pack file alone (no store):
   - `python3 -c 'import json,sys; rows=[json.loads(l) for l in open(sys.argv[1], encoding="utf-8")][1:]; short=[r for r in rows if 2*min(len(c["text"]) for c in r["candidates"]) < r["n_chars"]]; print(len(short), "of", len(rows), "rows: the shorter reading under half the longer;", sum(r["gold"]["is_gold"] for r in short), "of them gold")' /mnt/d/leibniz-packs/fragments-2026-10-22.jsonl` → "N of 2000 rows: the shorter reading under half the longer; G of them gold".
   **The copy to the box**, once chosen: `scp
   /mnt/d/leibniz-packs/fragments-2026-10-22.jsonl root@<target>:/root/`
   (the target on the plan page); the import into the game is the game's
   runbook. **The judgments import is P8's**: when the game's judgment pack
   comes back, `uv run --no-sync leibniz pack judgments --in
   <judgments.jsonl> --fragments
   /mnt/d/leibniz-packs/fragments-2026-10-22.jsonl` (a dry run: the plan,
   and the Scriptorium queue rendered) and, after a backup of the store and
   the operator's go, the same with `--write`; keep the pack file until then
   (the winners are checked against it). This record is on
   `claude/keen-keller-rvxmzf`, restarted from main after the merge
   (compare:
   https://github.com/marchofhares/leibnizlegible/compare/main...claude/keen-keller-rvxmzf?expand=1);
   the operator opens and merges its pull request.

**L1 (2026-10-21): built in a cloud session; the branch
`claude/relaxed-dijkstra-uus9rz` carries it (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...claude/relaxed-dijkstra-uus9rz?expand=1);
the operator opens and merges the pull request; nothing deployed.** About
and `llms.txt` changed, so the staging look before the merge: `ssh <target>
sudo /opt/leibniz-legible/deploy/staging.sh claude/relaxed-dijkstra-uus9rz`
(the target and the user name on the plan page; paste the output back), then
over HTTP, each line asking for the password once, the expected answer after
the arrow:
   - `B=$(curl -su USER https://staging.leibnizlegible.com/about | grep -o '/static/m/[0-9a-f]*/' | head -1); curl -su USER "https://staging.leibnizlegible.com${B}i18n.js" | grep -c "'about.license.models.p':"` → `2` (EN and DE); the same file `| grep -c "'about.license.gt.p':"` → `2`, `| grep -c "'about.license.letters.p':"` → `2`, `| grep -c 'CC BY-NC 4.0'` → `6` (three paragraphs in each language);
   - `curl -su USER https://staging.leibnizlegible.com/llms.txt | grep -c 'CC BY-NC 4.0'` → `3`, and `| grep -c 'obtained under CC BY 4.0'` → `2`;
   - `curl -su USER https://staging.leibnizlegible.com/api/works/00068642 | grep -c 'obtained under CC BY 4.0; published by its makers under CC BY-NC 4.0 since 2026-10-15'` → `1` (the attribution line the API and the manifests carry);
   - `curl -su USER https://staging.leibnizlegible.com/robots.txt | grep -c '^Allow\|^Disallow'` → `10`, and `diff <(curl -su USER https://staging.leibnizlegible.com/robots.txt) <(curl -s https://leibnizlegible.com/robots.txt)` → nothing, or the `Sitemap:` line alone (L1 touches no robots rule).
   In the browser, with the password: `/about`, EN and DE, under "Licensing
   and attribution" seven blocks in this order — Page images, Catalogue data,
   Transcriptions (opening "Machine output of a model obtained under CC BY
   4.0"), Ground truth, Models, Letters, Code. Then merge and the §9 update;
   no index rebuild is needed (nothing in the index changed). **Operator
   lines after the merge, none urgent:** (a) read the licence file of
   `mittagessen/dfine_kraken` and the Nantes HMER repository's address and
   licence, and write them into the two entries (`dfine-kraken`,
   `nantes-hmer` in `src/leibniz/legal.py`); (b) when the research directors
   in Hanover and Münster answer, write their terms into `edition-gwlb` and
   `edition-muenster` (and the D3 deposit of the `gwlb` channel, if it
   changes); (c) PHILIUMM's code licence and the apparatus script, when they
   come (`philiumm-code`); (d) at every release, `leibniz legal licences
   --format tsv` is the list of records to re-read, and the cards and About
   follow the registry. **The owner's open decision, recorded in L1, not
   acted on:** the later Reihe IV volumes (IV,4 onwards, inside their
   25-year term) and Reihe VIII could feed the factory as an NC channel now
   instead of on §70 expiry, under the Potsdam statement of 12 October
   (Series IV, V and VIII under CC BY-NC 4.0); Reihe IV is the German series,
   so this is Kurrent ground truth for K2 and K3, whose models are CC BY-NC
   4.0 in any case. The costs: those volumes' catalogue records (the
   Arbeitskatalog export, Open question 27), a SPECS §7 amendment, registry
   entries (`viii` exists with `deposit="nc"`; a Reihe IV NC channel would be
   a new key), the edition cache rebuilt from those PDFs, and a bigger
   re-mint under the K2 factory guard. The L1 note of 2026-10-14 below has
   the first version.

**W6 (2026-10-21): built in a cloud session on the fixture store; the branch
`claude/busy-dirac-n30a43` carries it (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...claude/busy-dirac-n30a43?expand=1);
the operator opens and merges the pull request; nothing deployed.** Before
the merge, the staging look: `ssh <target> sudo
/opt/leibniz-legible/deploy/staging.sh claude/busy-dirac-n30a43` (the target
and the user name on the plan page), then over HTTP, each line asking for the
password once, the expected answer after the arrow:
   - `curl -su USER https://staging.leibnizlegible.com/api/works/1665058609 | python3 -c 'import sys, json; print(json.load(sys.stdin)["katalog_search_urls"])'` → `[{'shelfmark': 'Leibn. Marg. 196', 'query': 'Leibn. Marg. 196', 'url': 'https://leibniz-katalog.bbaw.de/de/extended-search?sign_ol=Leibn.+Marg.+196'}]`;
   - `curl -su USER https://staging.leibnizlegible.com/work/1665058609 | grep -o 'sign_ol=[^"]*' | sort | uniq -c` → `2 sign_ol=Leibn.+Marg.+196` (the header's link and the sentence's), and `… | grep -c 'this site holds part of the Arbeitskatalog so far; search it for'` → `1`;
   - `curl -su USER https://staging.leibnizlegible.com/work/00068642 | grep -o 'Search the Leibniz-Katalog for [^<]*'` → `Search the Leibniz-Katalog for LH 4, 6, 18` (the live store's spelling), its two records still listed under the heading;
   - `B=$(curl -su USER https://staging.leibnizlegible.com/about | grep -o '/static/m/[0-9a-f]*/' | head -1); curl -su USER "https://staging.leibnizlegible.com${B}i18n.js" | grep -c "'about.what.scope':"` → `2`, and the same file `| grep -c 'Landesarchiv Hannover'` → `2` (EN and DE);
   - `curl -su USER https://staging.leibnizlegible.com/robots.txt | grep -c '^Allow\|^Disallow'` → `10`, and `diff <(curl -su USER https://staging.leibnizlegible.com/robots.txt) <(curl -s https://leibnizlegible.com/robots.txt)` → nothing, or the `Sitemap:` line alone if staging names its own host (W6 touches no robots rule; the live file's md5 on 2026-10-21 is `b8e54f8c99497e55d3800ca9e49a5280`).
   In the browser, with the password: `/work/1665058609` (the link in the
   header and under "Catalogue records", EN and DE), `/work/00068642` (the
   link and the records), `/about` (the second paragraph of "What this is").
   Then merge and the §9 update; no index rebuild is needed (nothing in the
   index changed). **The reply to the editor** (three sentences; the operator
   sends): (1) every work page now links the Leibniz-Katalog's own search by
   the work's shelfmark, whether or not the site yet holds the work's records
   — for Leibn. Marg. 196 that is
   https://leibniz-katalog.bbaw.de/de/extended-search?sign_ol=Leibn.+Marg.+196;
   (2) the About page now says, in English and German, that the site covers
   the scans the GWLB has published of its Leibniz collections and not all of
   Leibniz's papers, since much is not yet digitised at the GWLB and elsewhere
   and other institutions hold manuscripts, the Niedersächsisches Landesarchiv
   Hannover among them, all of them recorded in the Arbeitskatalog; (3) the
   records themselves, Marg. 196's included, follow once the Arbeitskatalog
   export the Arbeitsstelle offered arrives and is imported, and until then
   the site holds the part of the catalogue it has and says so on every work
   page without records. **The holdings page and the records wait for the
   export** (Open question 27). Housekeeping: the W5 prompt is missing from
   `PROMPTS.md`.

**K3 (2026-10-26): a Leibniz Kurrent model — two models trained and measured on the desktop; the branch `k3-kurrent-model` carries the code, the reports and the docs (compare: https://github.com/marchofhares/LeibnizLegible/compare/main...k3-kurrent-model?expand=1); the operator opens and merges the pull request; nothing deployed.** Read first: `reports/kurrent/k3-eval.md` (the letter pool, the validation set, Dresden, the speeds, the choice rule and its answer), then the two model cards `k3-model-card-trocr.md` and `k3-model-card-kraken.md`, `k3-pilots.md` and `k3-trainset.md`. **Keep `data/models/k3/` (a symlink to `/mnt/d/leibniz-train/k3/`: the two models, their validation hypotheses and accounts, the PP-OCRv6 pilot's weights) and `data/train/k3/` (the crops, the manifest, the split lists).** The models as readers: the CANDIDATES keys `k3-trocr` (`data/models/k3/trocr/best`, a Hub-style checkpoint directory the TrOCR engine loads by path; its `generation_config.json` carries `use_cache: true`; MIT base, the fine-tune open) and `k3-kraken` (`data/models/k3/kraken/best.safetensors`, kraken 7.0.3; CC BY 4.0 base, the fine-tune open), both off by default; version strings `k3-trocr@runs-615-epoch-5` and `k3-kraken@runs-614-checkpoint-36`. **The choice for K4 is the operator's, on the numbers (`k3-eval.md`): the rule's answer is k3-kraken — k3-trocr has the better selection-half CER (24.7 %), k3-kraken is the faster (52 ms a line) and lies within the margin (3.6 %).** **The operator's answer (2026-10-26), verbatim: "I agree to go with TrOCR."** READER for K4 is `k3-trocr` (`data/models/k3/trocr/best`), read with `--kv-cache`; K4 runs on `k4-german-site`. Pending for K3b: the PP-OCRv6 pilot's accounting (its side environment's CUDA fault; its weights on D:) and a full PP-OCRv6 training, the ablation without the screened lines (planned, not run), a 24 GB rental for the whole model under AdamW (`tools/k3-rented-gpu.md`), and K2's audit verdicts, in since 2026-11-06 (the manifest's tags let a class of lines go without recutting).

**K2 (2026-10-21): German ground truth, done on the desktop; the branch
`k2-german-gt` carries the code, the reports and the docs (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...k2-german-gt?expand=1);
the operator opens and merges the pull request; nothing deployed** (the
website serves its own copy of the store). Read first:
`reports/kurrent/k2-mint.md` (the yields, the rule's verdicts, what it
measures and what it does not), then `k2-write.md` (what the store holds
now and where the dry run's expectation went) and `k2-read.md` (the
reading job and the setting). The master store changed today (`gt_lines`:
32,497 rows deleted, 50,723 written under run 609), so the backup chore
runs again with today's date; the copy from before the write is
`/mnt/d/leibniz-backups/inventory-2026-10-20.sqlite` — keep it, and
`data/kurrent/` (the readings, the decisions, the pairs, the sheets),
until K3 is merged. **The audit sheet `data/kurrent/k2-audit.html` is the
operator's to hand to a judge** (half the lines in Leibniz's own hand,
half in other hands, mixed, the sheet silent on which; the verdict CSV
joins `k2-audit-lines.csv` on `ref` for the figure by hand, which
`leibniz align audit-score` reports as a table by group). **K3 starts after the sheet is judged,
or after the operator decides to go without** — on the 60,163 lines of the
German records (50,720 the reader's), the held-out pages and K2b's 134
letters excluded, with the precision by hand as the weight on Leibniz's
own lines. C3 reads `data/gt/flags.jsonl` as `audit-reach` wrote it today
(the reader rows left out, 282,960 v1 rows flagged).

**C2c (2026-10-20): the re-mint, done on the desktop; the branch
`c2c-remint` carries the reports and docs (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...c2c-remint?expand=1);
the operator opens and merges the pull request; nothing deployed** (the
website serves its own copy of the store and no row of `gt_lines`). The
master store changed today (`gt_lines`: 297,424 rows deleted and 315,797
minted; the `record_id` column and two indexes added), so the backup
chore's three lines run again with the date of the run, and the upload;
the backup from before the re-mint is
`/mnt/d/leibniz-backups/inventory-2026-10-20-pre-remint.sqlite`. Keep
`data/gt/edition_cache.pre-c2c.jsonl` and `data/gt/flags.pre-c2c.jsonl`
until C3 has read the new files. From here: **W5's step (5) is done.**
**C3 may start** on the re-minted lines under Amendment 2 — hyphens kept
(done); the `math` and Marginalien lines excluded and the `bracket` lines
cleaned or dropped, from `data/gt/flags.jsonl`; the 1,472 pages of
`reports/philiumm/heldout_pages.csv` held out; strata by hand with
`catalog/hands.py` (its strict rule: Leibniz's own hand 14.9 % of the lines
with a Textart); the first round's judged lines as a sanity set — 196 of
its 200 lines are minted again, 195 with the same text apart from a kept
end mark, so C3 checks each line's presence. **K2 writes after this
merge**: its Task 0 reads the C2c entry's edition-cache bullet (its input
`german_pieces.jsonl` stands as built), and it mints only with the K2
prompt's factory guard, because a full re-mint replaces every row a record
owns. **The D3 ground-truth release** takes its inputs from the store as it
now stands — 315,797 open-bucket lines whose sources name channel and
record — with `reports/gt-factory.md` and `reports/gt-audit/audit-summary.json`
for the card. The second judging round (Open question 18) is the
operator's to offer: `reports/gt-audit/round2/gt-audit.html`.

**K2b (2026-10-20): done on the desktop; the branch `k2b-letterpool` carries
it (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...k2b-letterpool?expand=1);
the operator opens and merges the pull request; nothing deployed** (K2b
changes nothing the website runs). Read first:
`reports/kurrent/letterpool-eval.md` (the readers' numbers, the metric, what
it measures and what it does not), then `letterpool-set.md` (the placement,
the drops, the draw) and `letterpool-parse.md`. Keep
`data/external/letterpool/` (the nine PDFs), `data/kurrent/letterpool/` (the
parsed letters and the frozen set's texts) and
`data/kurrent/letterpool-readings/` (the four readers' readings) — all
gitignored, nc bucket; `data/kurrent/letterpool-crops/` (1.9 GB) is a cache
the next `--read` rebuilds. Standing rules for the set: **K3 reports its
German error rate on this set — the test half's number beside the whole — and
never tunes on it**; a reader may be chosen on the selection half;
`letterpool-eval` verifies the set's checksums before any scoring and a
changed text refuses; the pool's text is never on the website, in a release,
in a committed file or in training (SPECS §1.4 and §7.3), and every report
carries numbers and letter numbers only. The page-disjointness check used the
K1 census's German pieces (K2's input); repeat it against K2's minted pages
once K2 has run (`leibniz align letterpool-set` prints it). The About page may
cite v1's German number (46.6 % CER on 134 letters of 1708–1716, nothing
filtered) in a later web step; until then it keeps calling German unmeasured.
For K2 the gate holds: trocr-kurrent-xvi-xvii (MIT), 37.0 % on the whole set
and 23.2 % on the correspondents' hands; the K3 target is Leibniz's own hand,
which every reader reads at 46.7 % or worse.

**L1 (2026-10-14): inputs from the Edition, in writing, for Task 0.** On
2026-10-12 the head of the Potsdam Arbeitsstellen (Reihen IV, V and VIII)
wrote that the edition's electronic texts of those series (the PDFs of the
volumes) may be used under CC BY-NC 4.0, the NC term being part of the
BBAW's agreement with De Gruyter; that the Arbeitskatalog data may be used
under CC BY 4.0; and that the series the Akademie der Wissenschaften zu
Göttingen is responsible for may differ (I, III, VII: the research director
in Hanover; II, VI: in Münster), to be asked separately; the operator is
writing to both. Consequences for L1: the Potsdam channel's licence is now
a CC licence, which permits sharing derived material under non-commercial
terms with attribution, so the lines minted from the Reihe IV PDFs join the
NC deposit (the plan's "Potsdam lines only once its Arbeitsstelle has said
yes" is met by this statement; the operator's reply of 14 October states
the intended use, a separate CC BY-NC 4.0 deposit with attribution to the
Leibniz-Edition and the BBAW and NC models, and invites correction); the
registry entry for the GWLB repository's PDFs stays CC BY-NC 4.0; the memo
question whether NC terms on a PDF reach reading text free of §70 stays,
restated as "if not, the NC deposit opens up"; the Göttingen series stay
"as obtained" with a dated "asked" note until their directors answer. A
decision for the owner, to record in L1 and not act on there: the later
Reihe IV volumes (IV,4 onwards, still inside their 25-year term) and Reihe
VIII (its TEI, SPECS §7.3) could feed the factory as an NC channel now
instead of on §70 expiry; Reihe IV is the German series, so this is Kurrent
ground truth for K2 and K3, whose models are CC BY-NC in any case. It needs
the catalogue records of those volumes, which were never scraped (Open
question 27: the export), a SPECS §7 amendment, registry entries, the
edition cache rebuilt from those PDFs and a bigger re-mint; the operator's
reply put it to the Arbeitsstelle conditionally. The Arbeitsstelle would
also welcome a first step towards a Kurrent model for Leibniz: the operator
has asked for a colleague who reads Leibniz's German to judge K2's audit
sheet of 200 lines, and for any German pages with corrected transcriptions
in the Edition's Transkribus material (an NC channel if granted). If the
judge comes from the Edition, K2's sheet gets German labels beside the
English ones; names of individuals stay out of this file and of PROMPTS.md.

_Paragraphs before 2026-10-19 whose every item is done or superseded (W5 of 2026-10-10; K1, the Kurrent path and the letter-pool choice of 2026-10-09; the final merge, W4 and S1 of 2026-10-08; C2b of 2026-10-07; the W3 fix of 2026-10-06; W2 and W1 of 2026-10-02; Phase D deployable of 2026-09-16) → STATUS-archive.md, "Next (archived)"; the three older paragraphs below (P1, W3, the A0–C2 block) stay, each with an open item._

**P1 (2026-10-08): Task 2 ran on the store** (`9c85f0a`); a later `compare`
rerun adds the coverage section to the report (optional, minutes). Task 3
waits for the new RF-DETR model. Merge order unchanged: after the PHILIUMM
team has seen the numbers. The four runs, for the record:

1. `uv run leibniz align philiumm-vi4 fetch` — the Hub listing and the 735
   noisy PAGE files into `data/philiumm/noisy/` at one request a second
   (about fifteen minutes; resumable: run it again if it stops).
2. `uv run leibniz align philiumm-vi4 match` — read-only on the store;
   prints files matched per split, pairs at IoU 0.3/0.5/0.7 and the layouts
   chosen; writes `reports/philiumm/heldout_pages.csv` and
   `vi4-match-summary.json`. Look at the unresolved list: a shelfmark
   spelling the matcher does not try is a one-line fix here.
3. `uv run leibniz align philiumm-vi4 compare` — writes
   `reports/philiumm/vi4-crosscheck.md`, `vi4-summary.json` and
   `vi4-disagreements-sample.csv`; the full CSVs stay under `data/philiumm/`.
4. `uv run leibniz align philiumm-vi4 sheet --images /mnt/d/leibniz-images`
   — `data/philiumm/philiumm-disagreements.html`, 300 lines with both
   texts, verdicts downloadable in the C2 CSV shape: the second sheet to
   offer the PHILIUMM team.
Then `git add reports/philiumm && git commit && git push`, and paste the
console summaries here. Task 3 waits for the new RF-DETR model. Merge order
unchanged: after the PHILIUMM team has seen the numbers.

**W3 (2026-10-06), operator:** ✅ merged (#38) and live the same day; the
checks below passed. The steps were: merge `web-browse-index`, then the §9 update on
the VPS (`deploy/README.md`) — code only: no index rebuild, no Meilisearch
restart, no new dependency. Then, over HTTP: `/browse` answers 200 and its
HTML holds the family headings, `id="lh-35"` and `/work/` links; `/api/works`
answers 200 JSON with `groups`; `/robots.txt` has the line `Allow:
/api/works`; `/sitemap.xml` lists `/browse`; `/llms.txt` mentions `/browse`;
and the three W1/W2 checks still pass (a page's `/text` starts with `# `, the
search page says "for an exact phrase", `style.css` hides the overlay by
`visibility`). In a private window: the nav link, EN and DE, the filter, the
order toggle of the letters, `/browse#lh-35`, a work page's breadcrumb.
(Returning readers were expected to see the old modules for up to an hour;
they saw a broken mix instead — the W3 fix.) Still open: the reply
to the reader at the Leibniz-Edition: the index is there; does the grouping
match how the Arbeitsstellen think of the Faszikel (Open questions #22); and
the two standing asks — a TELOTA contact for an Arbeitskatalog export, which
would name the remaining letter convolutes, and CC BY or written permission
for the Reihe VIII reading text (both answered 2026-10-12: an export is
offered, the text is CC BY-NC 4.0; the L1 note at the top of Next). Next
phase: K1, from a fresh session on the merged main.

**A0–A3 + B1–B2 + C1 (machinery *and* corpus run) + C2 (machinery *and* mint) all green; C2's precision gate is deferred to C3's ablation (audit preliminary).**
Per SPECS §5 sequencing, C is sequential: **C2 minting, then C3**, then C4 and
the D phases.

- **C2 — closed on the mint; the precision gate rides with C3.** 297,424
  lines minted; the hand audit is preliminary (20/200, Q #18) and stays
  open in `reports/gt-audit/` for a reader of the hands. The C3 ablation
  (PHILIUMM GT alone vs + C2 GT) is the empirical test of the minted GT; if
  it shows no gain, come back to Q #18 / Q #17 and the per-stratum
  thresholds before spending on labels. Optional clean-label upgrade:
  vision re-extraction of the minted pieces' pages (priced in the report;
  low three figures at most).
- **Phase C3 — Fine-tune v2 + per-stratum eval (gate).** Train `leibniz-htr-v2`
  from the PHILIUMM checkpoint on PHILIUMM GT + the C2 open-bucket GT
  (+ ablations). Hold out a page-disjoint test set stratified by stratum +
  language; evaluate with the B1 harness. Gate: **CER ≤7% on la/fr**.
- **Operator (SPECS §8), now higher-value than ever:** a **TELOTA katalog
  dump** would complete the scrape *and* supply the §70 anchors in one move —
  and with the corpus read, emailing PHILIUMM (Rabouin/Bumba) the B1/B2/C1
  results carries real weight: their models just machine-read the entire
  Nachlass. Report the 16 redirect-loop delivery URLs to GWLB while at it.

No code or data blockers for C2 minting; the only dependency is the corpus store's location.
