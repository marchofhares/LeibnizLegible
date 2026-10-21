# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-10-21 (**L1 — the licence registry, built in a cloud session: one entry per third-party artifact with its licence as obtained and as published (the PHILIUMM models CC BY-NC 4.0 on Zenodo since 2026-10-15, the dataset CC BY 4.0, the Potsdam channel and the Arbeitskatalog as stated in writing on 2026-10-12, the records re-read 2026-10-21), the outputs table (the owner's scheme of 13 October), `leibniz legal licences`; the ground truth exports as two deposits by channel (CC BY 4.0 / CC BY-NC 4.0); About, llms.txt, the cards and the attribution line read their licence lines from the registry; SPECS §2 and §7 amended; the lawyer-memo list in the release checklist; 880 tests; on `claude/relaxed-dijkstra-uus9rz`, the pull request the operator's**; earlier the same day, **W6 — two reader's items from the Leibniz-Edition (13 October), built in a cloud session on the fixture store: a search link into the Leibniz-Katalog by shelfmark on every work page, whether or not the store holds the work's records (the catalogue's spelling checked live: Arabic numerals, `LBr` without the library's period, `Leibn. Marg.`; 2,184 of the 2,225 works get a link), and the scope sentence, EN and DE, on About, in llms.txt and the README; 859 tests; on `claude/busy-dirac-n30a43`, the pull request the operator's**; 2026-10-20: **C2c — the re-mint under W5's rules, done on the desktop: 297,424 minted lines deleted and 315,797 minted in their place (+6.2 %; 710 `LBrF` records now localizable, neighbours on a shared folio no longer erased, nothing filed under a volume without text); the hyphen flag 7,822 → 848, 8,523 lines keep the scribe's mark; Leibniz's own hand 14.9 % under the strict rule (25.7 % under the loose one, the difference the rule's); 1,472 held-out pages; the second judging sheet drawn; on `c2c-remint`, the pull request the operator's**; earlier the same day, **K2b — the letter-pool test set, done on the desktop: 134 letters of the GWLB pool frozen as the honest German test set (67 in Leibniz's hand, 67 of the correspondents'; 18,815 lines), nothing filtered; the first German error rates — v1 46.6 % CER, philiumm 52.9 %, trocr-kurrent-xvi-xvii 37.0 %, trocr-hanse-xvi 35.6 %, trocr-hanse-xvii 38.9 %; the correspondents' hands 23–46 %, Leibniz's own 47–59 %; on `k2b-letterpool`, the pull request the operator's**; 2026-10-14: **the Edition's replies of 12 and 13 October recorded, no code: the Potsdam series' texts CC BY-NC 4.0 in writing, an Arbeitskatalog export offered, reader feedback on catalogue links and scope, the holdings outside the GWLB surveyed — Open questions 27 and 28, the L1 note under Next**; 2026-10-11: **W5 live: merged as #42 and deployed on 2026-10-10, the index rebuilt and the letters fetched overnight — 196,439 distinct scans among 236,795 page records, 9,846,450 lines once each, 40,297 scans registered under more than one label (39,442 spreads split, 855 folded), 15,425 letters**; 2026-10-10: **W5 — the review's fixes and six features readers ask for, in code on `claude/amazing-mayer-y6i9g0`: the GT factory fixed before the re-mint (record-owned lines, folio sides, one volume per piece, the en dash, "LBrF", one hand rule, the audit's own numbers); the site's search (every word by default, exactness first, folded metadata, no empty pages past 10,000), safe 404s, the right folios for "Text of this piece", source links that open, per-page GWLB links, named letter convolutes, IIIF fixes; scans registered twice folded and spreads split at the fold; citable lines; citation lookup; letters by correspondent, date and place; a Faszikel index of the catalogue's pieces; links out**; 2026-10-09: **K1 — the Kurrent track, done on the desktop: the aligner's noise tolerance measured (yield holds to ≈ 55 / 48 / 38 / 29 % CER by stratum), the German census run on the store (2,173 German pieces, 401,394 recognised lines, minted at 10.2 % against 19.0 % on Latin and French), the bootstrap readers ranked on Dresden (trocr-kurrent-xvi-xvii 7.4 %, trocr-hanse-xvi 8.9 %, trocr-hanse-xvii 10.9 %, philiumm 29.5 %, mccatmus 51.7 % CER), the pilot on Leibniz's German run (German yield at the gate philiumm 12.5 %, trocr-kurrent-xvi-xvii 20.2 %, trocr-hanse-xvii 20.6 %, trocr-hanse-xvi 22.5 %, v1 16.4 %); gate for K2: GO with trocr-kurrent-xvi-xvii**; 2026-10-08: **S1, the staging site: built, installed and verified the same day; `https://staging.leibnizlegible.com` runs the branch behind a password against the live store and index**; earlier the same day, **C2b, the census run on the store: a quarter of the minted ground truth is in Leibniz's own hand, 7,822 lines lose their hyphen to the mint, the addition proxy marks 83 % of lines and is useless; 2026-10-07, C2b: the PHILIUMM team's 200-line audit scored and read** — corpus-weighted precision 72.3 % as written, 92.2 % with boundary slips counted usable, one misaligned line in 185 scored; the patterns behind the verdicts named and measured, the dropped line-end hyphen fixed in the aligner, the reach census built for the operator's run, the C3 prompt amended; 2026-10-06, later the same day, a fault found live after W3's deploy and its fix: the viewer's ES modules are served as one versioned set, so a deploy can no longer pair a new `app.js` with cached old modules; W3: a browse page — the Nachlass by shelfmark family, section and convolute at `/browse`, `GET /api/works`, a breadcrumb from every work page back to its section; 2026-10-02 — W2: search reads "quoted phrases" and -exclusions, and the hint under the box says so and what exact matching misses; earlier the same day, W1: the line-overlay toggle fixed, plain-text export per folio and per work, content-hashed viewer assets; earlier: 2026-09-27 — room for Calculemus on the host, flagged off; 2026-09-23 — discoverability, About page, duplicate sheet-sides; 2026-09-16 — **Phase D built on v1 — search index, API, IIIF v3 + annotations, viewer, release exports; reports + project statement published on Zenodo; strategy review recorded in `NOTES.md` and the C3 prompt amended. C2 stands as closed on the mint with the precision gate deferred to C3. Later the same day: the deployment kit (`deploy/`), public-traffic hardening of the app, `LICENSE` + issue form for the repository going public.**)._

---

## Current state

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

**2026-10-14: the Edition's replies, recorded (no code, no data).** Two
emails from the Leibniz-Edition Potsdam, both answered by the operator on
14 October (roles, not names, by the operator's rule). (a) 12 October, from
the head of the Potsdam Arbeitsstellen (Reihen IV, V and VIII): the
edition's electronic texts of those series (the PDFs of the volumes) may be
used under CC BY-NC 4.0, the NC term being part of the BBAW's agreement
with De Gruyter; the Arbeitskatalog data under CC BY 4.0; a one-time
export of the Arbeitskatalog is offered (an up-to-date Access export
directly, or XML through TELOTA, whose eXist database is fed twice a year
and feeds the website); the series the Göttingen academy is responsible
for may differ (I, III, VII: the research director in Hanover; II, VI: in
Münster) and are to be asked separately; the Arbeitsstelle would welcome a
first step towards a Kurrent model for Leibniz. (b) 13 October, from an
editor there: a Marginalien work (`1665058609`, Leibn. Marg. 196) is not
linked to its catalogue search (verified: the store holds no record for
that work, Open question 27); records should link to the catalogue (they
do since W5, `23359e0`; the catalogue's ID is stable while title, incipit
and date change on its half-year cycle); the site should say that the
GWLB's scans cover only part of Leibniz's writings; and other
institutions' scans, the Niedersächsisches Landesarchiv Hannover first,
could be included, since most of that material is unpublished and some is
not in the catalogue. Where it lands: Open question 27 (the export
replaces the scrape; the import step and two web items), Open question 28
(other holdings, new, with a first survey), the L1 note at the top of
Next (the licence inputs, the NC-channel decision, the Kurrent asks).

**2026-10-11: W5 live.** Merged as #42 (merge commit `aac0fc9`) after the
operator's staging look on 2026-10-10 — twelve HTTP checks against the live
store and index answered as designed, and the browser look was good except
that `Monadologie` found nothing in the browse filter (the store's catalogue
is part of the Arbeitskatalog: Open questions #27; `25961a1` makes the page
say so) — and deployed the same evening (the §9 update; it carried K1's code
along). Overnight the index was rebuilt with the staging unit stopped
(runbook §14), into a second index swapped in at the end, so search stayed
up; the letters were fetched beside it; one restart of both units. Live
since 2026-10-11 (`/api/stats`): **196,439 distinct scans** among 236,795
page records — 40,297 scans registered under more than one folio label,
39,442 of them spreads split at the fold and 855 folded onto one page, 519
candidates left as they were — and **9,846,450 lines once each** against
13,508,625; **15,425 letters** on `/letters`, and 991 of the 1,060 letter
convolutes named (680 before). The operator spot-checked six decisions (five
spreads in LBr and LH, one fold): all correct. Still to come: the re-mint
before C3 (Next).

**2026-10-10: W5 — the review's fixes and six reader features, in code.** A
review of the whole project — code, reports, the live site — found faults in
the GT factory that the one re-mint before C3 would have inherited, and
faults on the live site. Both are fixed on `claude/amazing-mayer-y6i9g0`,
with the six features readers are most likely to ask for: duplicate scans
folded and spreads split, citable lines, lookup of what scholars cite,
letters by correspondent, date and place, a Faszikel index of the
catalogue's pieces, and links out. Tests 705 → 808, ruff clean, the new views
checked in a headless browser on the fixture store. **Not deployed or
re-run by the session** (live since that evening: above): the factory fixes
take effect with the re-mint (a full run, without `--resume`), the search
fixes and the twin folding with the next index rebuild, the letters with
`leibniz catalog letters`. The numbers the new code produces on the corpus
(distinct scans, lines once each, spreads, letters filed) did not exist
yet; the index build writes them to `/api/stats` and the twins file. The
W5 entry in the Phase log has the detail and Next the operator's order.

**2026-10-09: K1 — the Kurrent track, done; gate for K2: GO with
`trocr-kurrent-xvi-xvii`.** The German question measured before any reader
is chosen, on the desktop, the store read-only. (a) *How much HTR noise the
aligner survives* (`leibniz align kurrent-tolerance`,
`reports/kurrent/align-tolerance.md`): the B2 harness over the recorded B1
machine text (1,878 validation lines in 76 pieces of 25, base CER 7.95 %),
the HTR side corrupted by a confusion model of a cursive hand (look-alike
letters, dropped and doubled minims, merged minims, merged and split word
spaces) to 10–60 % CER against the gold, yield and precision read at the
factory's thresholds with the factory's gate. Precision stays at or above
95.7 % up to 40 % CER in fair copy, light and heavy revision; yield at 30 %
CER is 97.0 % / 94.0 % / 79.8 % / 46.0 % (fair copy / light / heavy /
scrap). Break-even by linear interpolation between the levels: **yield falls
under 50 % at ≈ 55 / 48 / 38 / 29 % CER** (fair copy at threshold 0.55 /
light 0.62 / heavy 0.72 / scrap 0.80), **precision under 95 % at ≈ 51 / 48 /
42 / 39 %**. A reader at 30 % CER on Kurrent feeds the factory; one at 50 %
does not, on drafts. (b) *The German census* (`leibniz align
kurrent-census`, `reports/kurrent/census.md`, `enrich/langid.py` — the
`enrich` package's first module, a stopword identifier): of the 10,029
edition-cache records, 2,036 are German, 3,631 Latin, 3,999 French, 331
mixed, 32 unknown. Of the 17,162 §70 pieces, 10,121 have a text; **2,173 are
German** (German, or mixed with German leading), 1,694 localizable, 1,665
with recognised lines on **5,874 pages, 401,394 lines**; the factory minted
**40,915** lines on them (**yield 10.2 %**) against 252,762 on 1,328,532
lines of the Latin and French pieces (19.0 %) — about half the rate, stratum
for stratum (heavy revision 8.0 % vs 17.1 %, light 19.3 % vs 23.0 %), **not
the near-zero the hypothesis expected**. Of the German-piece mint, 27,643
lines (67.6 %) carry German stopwords in their minted text, at a mean
confidence of 0.839 (Latin and French pieces 0.927) on machine text of 41.0
folded characters a line (Latin and French 46.2): the PHILIUMM model is not
reading Kurrent as noise — chance alignment gives ≈ 0.50 at 60 % CER in the
tolerance study. Whether those lines are right is the pilot's question (Task
4). German pieces in Leibniz's own hand: 82 (18,056 lines).
`data/kurrent/german_pieces.jsonl` is K2's input. One rule found hollow on
the way: the factory's Textart rule recognised a document class on 129 of
the 10,121 pieces — the catalogue abbreviates (`Abf.`, `Konz.`) — so the C2
stratum came from the layout alone (Open questions #23). (c) *The readers on
Dresden* (`leibniz bench kurrent-smoke`,
`reports/kurrent/bootstrap-candidates.md`): on the 383 Kurrent Trace lines,
CER under the project's `philiumm` policy — `trocr-kurrent-xvi-xvii` **7.4
%**; `trocr-hanse-xvi` **8.9 %**; `trocr-hanse-xvii` **10.9 %**; `philiumm`
**29.5 %**; `mccatmus` **51.7 %**. The PHILIUMM baseline at 29.5 % is not
noise on Kurrent; the Bern TrOCR model at 7.4 % is the reader to beat. A
ranking, not a benchmark (public lines, nc text). (d) *The pilot* (`leibniz
align kurrent-pilot`, `reports/kurrent/pilot.md`): 20 German pieces and 5
controls, 2,639 lines read afresh by every reader, the factory's alignment
as a dry run. German yield at the gate: `philiumm` **12.5 %**,
`trocr-kurrent-xvi-xvii` **20.2 %**, `trocr-hanse-xvii` **20.6 %**,
`trocr-hanse-xvi` **22.5 %**, `v1` **16.4 %**; on the controls `philiumm`
41.6 %, `trocr-kurrent-xvi-xvii` 23.6 %, `trocr-hanse-xvii` 18.2 %,
`trocr-hanse-xvi` 30.5 %, `v1` 40.5 %. **GO for K2 with
`trocr-kurrent-xvi-xvii` (MIT)**: German yield 20.2 % at the factory's gate
on the pilot's lines against 12.5 % for the `philiumm` baseline read the
same way and 16.4 % for the stored v1 text — 1.23× the factory's own German
mint on the same lines, 1.6× the baseline's; the controls order as they must
(`philiumm` wins them). `trocr-hanse-xvi` reads 22.5 % but states no licence
on the Hub: evaluated, not built on. It stays under half the baseline's
yield on the Latin and French controls (41.6 %): German pieces will mint,
but thinner than Latin and French ones do with the model made for them. 704
tests, ruff clean, in `.venv-k1`. The branch is pushed; nothing is deployed.

**2026-10-08 (evening): W4 — text access: a copyable text block on every
page view, the text of a catalogue piece across its folios, the downloads
where readers look.** David Rabouin's first point of 7 October: "as it
stands, one cannot copy the transcription", and a reader wants the text of
the whole page or passage. Measured first on the live page view (headless
Chromium, `/page/00068221:0043`, 108 lines): each line's text sits inside the
`<button>` that selects the line, so a drag across lines selects nothing, a
drag within a line selects nothing and counts as a click (the image zooms
to the line), a double-click selects nothing; select-all then copy does
work and takes the whole page with it, 11,828 characters of chrome, badges
and provenance summaries around the lines. Now, under the line list, a
**Text** block holds the page's recognised lines as one piece of selectable
text in reading order, one line per line, with **Copy the text** (the
clipboard API from inside the click; where the browser refuses, the block
is selected and a status line says to press Ctrl+C), the per-page download
beside it as "Download this page as text", and one line of provenance
above the block (the model and run date behind the lines, the wording
rule); the header's link list points at the block ("Text of this page")
instead of carrying the download. The line list is unblocked as well: its
text is `user-select: text`, the badges, the number and the hidden labels
`none`, a click does nothing while a selection stands in the list, and a
`copy` whose selection lies in the list hands the clipboard the selected
parts of the lines, one per line, and nothing else (Chromium alone copied
the two lines with a blank line between them). **`GET
/api/records/{record_id}/text`**: the text of a catalogue piece — a letter,
a draft — across the folios its shelfmark's `Bl.` range names, placed by the
C2 resolver the way the factory localized its pieces (`web/pieces.py`: the
record's shelfmark with a range, its best crosswalk link), in the work
export's layout under a header naming the record (title, incipit, date,
sender and addressee, AA reference, the katalog URL), the work, the folio
range, the canvases and the catalogue's licence; `?format=tsv`; 404 for an
unknown record and, with the reason in `detail`, for a record not linked to
a work, without a folio range, or whose folios no page label carries. The
work API's `katalog` entries carry `text_url`, `folio_label`, `folio_range`
and `n_pages` only where a record is placed; the work page shows "Text of
this piece (Bl. 1–2)" under each such record, server-rendered too;
`robots.txt` allows `/api/records/`; `llms.txt` and the README document it;
the About page's transcriptions paragraph says text comes per page, per
work and per piece. EN and DE throughout. **644 tests** (634 → 644), ruff
clean; against the app on the fixture store in headless Chromium, **39
checks** pass (selection and copy on the block and in the line list, the
piece's download from the work page, EN and DE, 390 px without horizontal
scroll, no console errors, axe-core 0 violations on the page and work views
in both languages and at phone width). On staging the same evening, the
operator's six HTTP checks answered as designed, the first run of the piece
text on the real store (record 41800: 84 lines on its 2 pages, mean
confidence 0.96), and their look in the browser was good. **Merged into
main with the rest of the branch the same evening** (pull request #40,
merge commit `62711b3`, 2026-10-09 UTC) **and live since the same evening:**
the §9 update on the box (no new dependency, `/healthz` ok), the seven
checks against `https://leibnizlegible.com` as on staging, and staging back
on main at `62711b3`.

**2026-10-08: S1 — the staging kit is on the branch; the install on the box
is the operator's.** A second copy of the site at
`https://staging.leibnizlegible.com`, behind HTTP basic auth, running any
pushed branch against the live serving store and the live search index, so
that every later web change (W4, L1, later M1) is looked at on the real
server before it is merged. Built in a cloud session, so nothing ran on the
box: `deploy/leibniz-legible-staging.service`, `staging.env.example`,
`staging.caddy.example`, `staging-install.sh` (root, once, idempotent; the
password typed on the box and hashed by `caddy hash-password`; the site
block validated over the whole Caddy configuration before a `reload`, never
a restart) and `staging.sh` (`BRANCH`, `--main`, `--status`, `--index`,
`--drop-index`), with runbook §14 and a test that holds each file to its
production counterpart. One code change: the Meilisearch index name comes
from the environment (`LEIBNIZ_MEILI_INDEX`; `leibniz serve --meili-index`;
`leibniz index build|status|query --meili-index`; the default is the live
name, so production is unchanged), which is what lets a staging index be
built beside the live one. 634 tests, ruff clean. **Installed on the box
the same day and verified by the operator:** the first run stopped at the
Caddy reload over a log file that `caddy validate` had created as root (the
S1 log has it; the fixed kit's re-run went through); then the page opens
with the password, `/browse` matches the live site, `/api/stats` reports
the same figures from the same index, and every authenticated response
carries HSTS and `X-Robots-Tag: noindex, nofollow` without a `Server`
header. From here on, every web change on the branch is one `staging.sh`
line and a look before anything is merged.

**2026-10-07: C2b — the audit closed and read.** On 7 October Denisa-Florina
Bumba and David Rabouin (PHILIUMM) returned the 200-line hand-audit sheet
with 199 verdicts and 86 notes. Scored (`reports/gt-audit.md`): **corpus-
weighted precision 72.3 %** against the 95 % gate — **FAIL as written**, in
every stratum (fair copies 84.0 %, light revision 86.7 %, heavy revision
64.6 %, scraps 57.1 %); counting boundary-off lines as usable, **92.2 %**.
Read line by line, the failure is not the one the gate was written for.
One pattern per judged line, from the verdict, the note, the minted text
and the HTR reading (`align/audit_patterns.py`): of the 16 *wrong*
verdicts, **one is a wrong line** (a fragment of *vérité* on a strip that
reads *serviteur*); the other fifteen are the right line with the
edition's text differing from the page — five formula lines, three
accents or commas the edition regularises, three disputed readings
(*Casal* for *Casai*), two editorial brackets leaked from the apparatus
(`droit[e]`, `[l'j`), two interlinear additions rendered inline. The 33
*boundary* verdicts are a letter or a short word off at an end, as the
auditors said. On 14 of the *correct* lines the note names a missing
line-end hyphen: the word was split by the scribe, the mint rejoined it
and cut it bare. That one is fixed: `align_piece(keep_hyphen=True)`, now
the default, puts the scribe's own mark back on the earlier line (an `=`
stays an `=`); it reaches the 6 lines whose HTR read the mark, not the 8
where the HTR dropped it too. The notes' 46 corrections, placed in the
minted text, give the first sample of the normalization tax on real
lines: 3.1 % character distance as written on the accent-and-comma
lines, 0.0 % under the aligner's fold — the fold hides exactly what a
diplomatic scorer charges. A read-only census (`leibniz align
audit-reach`, run by the operator on the store on 2026-10-08,
`reports/gt-audit/reach.md`) measures every pattern across the 297,424
minted lines: **7,822 (2.6 %) lose their hyphen to the mint** (7.7 % of
fair copies), what the re-mint changes; 4,338 (1.5 %) carry an editorial
bracket; the density cut flags 249 formula lines (0.1 %), two thirds of
them in Reihe III, a floor; the addition proxy marks 82.7 % of lines and
99.3 % of heavy revision, i.e. it restates the stratum and is no use as a
filter; no minted line is from a Marginalien work. **The hand census: of
the 296,587 lines whose record has a Textart, 40.1 % are in their
author's own hand and 25.7 % in Leibniz's** — 1.7 % of fair copies (the
secretaries' Abfertigungen), 8.3 % of light revision, 35.8 % of heavy
revision (his drafts), 18.2 % of scraps; the rest of the own-hand share
is correspondents' hands on letters he received. The C3 prompt carries
Amendment 2: train on the re-minted lines with hyphens
kept, exclude formula and Marginalien lines, hold out PHILIUMM's pages,
stratify by hand, keep the 199 judged lines as a sanity set. The
operator's own 20 verdicts of 16 September agree with PHILIUMM's on 11:
four lines the operator called wrong they call correct, as the second
witness had predicted. 606 tests, ruff clean. Branch
`claude/dazzling-hopper-uxji2x` (see Divergences); merge after the
PHILIUMM team has seen the scored report.

**2026-10-06 (later): W3 fix — a deploy no longer mixes new and old viewer
modules.** Minutes after W3 went live the operator opened `/browse` and saw
"nav.browse" in the nav, "browse.heading" in the tab title, and "Something
went wrong: api.works is not a function". Cause: the proxy lets browsers keep
`/static/*` for an hour and the shell named only `app.js` by content hash, so
a returning reader ran the new `app.js` and `views/browse.js` against the
`i18n.js` and `api.js` cached before the deploy. A hard reload cleared it and
every such browser heals within the hour, but any deploy that changes what
one module asks of another would do it again (W1 had recorded the imported
modules as "not versioned" and expected a lag, not a broken page). The shell
now loads the modules from `/static/m/<build>/`, where `<build>` hashes every
module; their relative imports resolve under the same prefix, so a browser
gets one consistent set. Reproduced before the fix and healed after it in one
browser behind a proxy that caches as Caddy does (8 checks); every view and
the 60 browse checks hold on the corpus store. On the same branch, a second
report from the operator's look round: each catalogue record on a work page
ended "Link: gwlb_link, confidence 1.00" — the crosswalk's method name shown
as if it were a label. It now reads "The catalogue record itself links to
this scan · confidence 1.00" (or "Linked by matching shelfmarks · confidence
0.70"), in both languages. Beside it, the row "Correspondent" had held the
record's sender with the catalogue's link text ("Correspondent: Leibniz
(GND)" on every letter he wrote); records now show *Sender* and *Addressee*
as the catalogue names them, and the API carries both. 573 tests, ruff
clean. Live after the operator's §9 update of `web-versioned-modules`.

**2026-10-06: W3 — a browse page: the Nachlass by shelfmark family, section
and convolute.** The same reader at the Leibniz-Edition asked for "an index of
the individual shelfmark groups", to "start from the group name ('Faszikel')
and identify the relevant shelfmark and folios". The site had search, work
pages and page views and nothing above them. `/browse` now lists all 2,225
works: the manuscripts in the 30 LH sections that have digitized units
(*LH 1 · Theologie* … *LH 35 · Mathematik* … *LH 42*), the 1,060 letter
convolutes by correspondent or by number, the 370 annotated books by number,
and 45 works outside the three series by collection. A filter narrows by
shelfmark, name or title as you type; every section has an anchor
(`/browse#lh-35`) and every work page a breadcrumb back to it; the whole index
is server-rendered for crawlers and readers without JavaScript; `GET
/api/works` serves it as data; EN and DE. **A correspondent is named on 680 of
the 1,060 letter convolutes (64.2 %)**, while 744 (70.2 %) have catalogue
records at all. The gap is deliberate: the linked records are not the whole
convolute, and the name found most often in them is in some sixty cases
somebody else's (LBr. 57, Johann Bernoulli's, would have read "Mencke, O.").
The LBr numbers run alphabetically by correspondent, so a name is shown only
where it fits that order — a missing name is honest, a wrong one is not.
569 tests, ruff clean; verified against the corpus store on the desktop (over
HTTP, then 60 checks in Chromium, axe 0 violations). **Live since 2026-10-06:**
merged as #38, the §9 update run the same evening, eight HTTP checks and the
same 60 browser checks passed against the live site, whose `/api/works` gives
the numbers above. The §9 updates of W1 and W2 were found live that day,
before this phase began (all three checks passed).

**2026-10-02 (later): W2 — search reads "quotes" and -minus.** The query
used to be folded before either backend saw it, and folding turns every
quotation mark and minus sign into a space: on the live site `"deus mundus"`
and `deus -mundus` returned exactly what `deus mundus` did (97,633 hits each),
`AND`/`OR` were searched as the words *and*/*or*, and on FTS5 `deus -mundus`
found precisely the pages with *mundus*. Nothing in the history, the docs, the
issues or the PRs decided against operators; the aligner's fold simply ate
them. Now `"…"` (also „…“, “…”, «…») matches the folded words exactly and in
order and `-word` / `-"…"` leaves out the pages that contain them, in both
backends, while a query without either reads exactly as before. The hint under
the search box says how, and that exact matching misses words the machine
misread; the no-results hint suggests dropping the quotes. On Meilisearch a
quoted shelfmark or AA reference finds nothing yet (Open questions #21).
545 tests, ruff clean. Live after the operator's §9 update — no index rebuild
(Phase log W2 has the checks).

**2026-10-02: W1 — two reports from a reader at the Leibniz-Edition.** "Show
line overlay does not seem to work": it did not. OpenSeadragon writes an
inline `display: block` on the overlay element at every redraw, an inline
style beats a class rule, so `.line-overlay.is-hidden { display: none }` never
won — the button flipped `aria-pressed` and the class while the polygons stayed
on screen. Fixed (hide by `visibility`, hidden polygons take no clicks, the
label says what pressing does, the choice is remembered per browser) and
verified in Chromium on the live page before and the fixed viewer after. "An
option to export the transcription of each folio": `GET /api/pages/{id}/text`
and `GET /api/works/{id}/text` (plain text, `?format=tsv`, a `# ` provenance
header; a work streamed page by page under `## Folio …` lines), linked from
the page and work views and their server-rendered fallbacks. And the shell
now names `style.css`, `boot.js`, `app.js` by content hash, so a deploy
reaches returning readers at once. 536 tests, ruff clean. Live after the
operator's §9 update (Phase log W1 has the checks).

**2026-09-23 (later): discoverability, About page, and a data caveat.** The
viewer shell now carries a favicon set, a web manifest, share metadata
(OpenGraph/Twitter with a 1200×630 card), a canonical URL and JSON-LD; the
server stamps title, description and canonical per route and renders a summary
for `/work/{id}` (catalogue entries, page list) and `/page/{id}` (the machine
text) in place of `<!--ll:ssr-->`, so crawlers, answer engines and no-JS
readers see content, and unknown ids are real 404s. New root files:
`/sitemap.xml` (every work), `/llms.txt` (the API and the wording rule for
agents), `/favicon.ico`; `robots.txt` opens the JSON API and keeps blind
crawlers off the IIIF routes; `/docs` and `/redoc` are off (the CSP blocked
their CDN assets), `/openapi.json` stays. The About page names the maintainer,
credits the GWLB, the Arbeitskatalog, PHILIUMM/FoNDUE/Kraken and the
precedents, describes the Akademie-Ausgabe with its own figures (68 volumes by
2023, about half of ~130, completion ~2055; Kliege-Biller 2023 for "three
quarters never published" — the source the "three quarters" sentence lacked),
adds a timeline, a citation line and the four report DOIs. The two unpopulated
search filters (language, writing stage) are hidden until C4. Work pages show
the katalog's other printings (`drucke`) and series-only AA assignments
(`aa_planned`). **Data caveat found today:** in the static-JPEG delivery a
scan is one side of an unfolded sheet registered under both folio labels
(outer `1r`+`2v`, inner `1v`+`2r`); sampled works show every sheet-side read
twice, so `pages`/`lines` totals include repeats and search returns twin hits.
`leibniz images duplicates` (new) hashes the thumbnails and lists the pairs;
folding them in the index and publishing a distinct-scan count is the next
data fix (Open Q #19). 524 tests, ruff clean.


**🚀 Phase D built on the v1 transcription (2026-09-16): the corpus is
searchable and browsable — the v1 public beta.** `leibniz index build` folds
every recognised page onto the aligner's early-modern comparison alphabet and
indexes it in SQLite FTS5 (single file) or Meilisearch (typo tolerance);
`leibniz serve` runs a FastAPI JSON API (`/api/search`, `/api/works/{id}`,
`/api/pages/{id}`, `/api/stats`), IIIF Presentation 3 manifests with W3C
annotation pages carrying every line's text + provenance (deliverable D7), and
the viewer: OpenSeadragon 5.0.1 on the GWLB's own Image API (static JPEG where
no service exists), a line-polygon overlay, status badges, five confidence
bands, a provenance disclosure per line, EN/DE, WCAG-clean (axe 0 violations
on every view). `leibniz release export` writes the three datasets as Parquet
(or JSONL) with `MANIFEST.json` checksums and dataset cards carrying
provenance, licence, attribution, error rates and the anti-contamination note.
`reports/release-checklist.md` is the upload runbook; `reports/tier1-final.md`
states the project against SPECS §3 criterion by criterion. **518 tests**, ruff
clean. The operator step: `leibniz index build && leibniz serve` on the corpus
store (the index build scans 13.5M lines once; the FTS5 file will be a few GB),
then measure search p95.

**🌐 LIVE (2026-09-21): https://leibnizlegible.com.** The v1 corpus is public
and searchable. A 2 vCPU / 4 GB Hetzner VPS in Falkenstein runs `leibniz
serve` behind Caddy (automatic TLS) with Meilisearch; the 15 GB serving store
and the 235,723-page index live on the box; **page images come from the
project's own mirror** (2026-09-23): all 236,779 delivery derivatives
(395.6 GiB) plus their derived thumbnails (6.0 GiB) on Cloudflare R2 behind
`images.leibnizlegible.com`, verified with `leibniz images check-mirror`
(500-page sample: every image and thumbnail present, no size mismatches)
before the switch. The GWLB's servers now carry none of the viewer's traffic,
and every page still links to its original there. **SPECS §3.3's search criterion
is met and measured:** 200 queries over HTTPS gave wall-clock p50 108 ms,
**p95 210 ms**, max 368 ms against the 500 ms bar (Meilisearch itself p50
8 ms, p95 60 ms). Typo tolerance and the early-modern fold both confirmed
live. What the deployment cost in wall clock, for the next operator: the
serving copy 10 min, its transfer 1 h 36 m at a measured 2.8 MB/s, the index
build **5 h 33 m** (disk-bound; only 32 min of CPU). `reports/tier1-final.md`
row 3 is updated from "to be measured" to met.

**Deployable (2026-09-16, later session).** The deployment kit is in `deploy/`
(runbook, `install.sh`, systemd units, Caddyfile, container stack) and the app
is hardened for public traffic (per-client rate limit, CSP + security headers,
CORS for IIIF consumers, gzip, read-only store connections, `/healthz`,
`robots.txt`, `leibniz index bench` for the p95 criterion). Going live is the
operator's runbook (`deploy/README.md`): a small VPS, the serving copy of the
store, the Meilisearch build, the DNS records, the image mirror on Cloudflare
R2 (an operator decision that diverges from SPECS §3.4's "never rehosted" —
recorded under Divergences; the code's default stays direct-from-GWLB) — and
the note to the GWLB before launch. `LICENSE` (Apache-2.0) and the issue form
the viewer's "Report an error" link opens are in place for the repository
going public. **518 tests**, ruff clean.

**Published (2026-09-16), CC BY 4.0, Zenodo community `leibniz`:** the project
statement (doi:10.5281/zenodo.22782813), the corpus census
(doi:10.5281/zenodo.22782815), the PHILIUMM reproduction + VLM benchmark
(doi:10.5281/zenodo.22782817), and the retro-aligned ground-truth reports
(doi:10.5281/zenodo.22782819); mirrored at evanatlas.com/research.

**Strategy review (2026-09-16) — recorded, not built:** `NOTES.md` (accuracy
levers, the Calculemus rescope, the four Academy seams, loose ends) and the
**C3 amendment in `PROMPTS.md`** (expect ~1 CER point from v2; vision
re-extraction, staged training, confidence filtering, n-gram LM decoding).
SPECS §1.5's Bullinger claim corrected (their models are 9.1–9.2% CER; 6.5% is
their GT's own error rate).

**🏁 C1 corpus run COMPLETE (2026-09-11): the full Nachlass is machine-read.**
**236,210 of 236,795 pages recognised (99.75%)** — **13,508,625 lines** with
text, per-line confidence and full provenance in the store. The remainder is
enumerated, not lost: 569 pages skipped with recorded reasons (blanks, specks,
oversize foldouts, degenerate geometry) and **16 pages permanently unfetchable**
(GWLB delivery URLs in a redirect loop — works `00068368`/`00068744` a.o.; worth
reporting upstream). Image cache: 236,779 pages / **395.6 GB**.
`reports/htr-v1-sample.md` and `reports/census.md` are regenerated from the
store with the real numbers. The run took ~6 weeks wall clock on one 16-core
GTX-1660-Ti desktop (WSL2), the last week in the final architecture: **4
sharded CPU segmentation workers + 1 concurrent GPU recogniser** (~515 and ~940
pages/hour respectively), all stages resumable and re-runnable via one operator
script. Every robustness fix that made this survivable is logged in the Phase
log below. **C2 GT minting is now unblocked on the HTR side** — its remaining
inputs are the katalog full scrape (Open Q #3) and the §70 page anchors (Open
Q #13).

**C2 — GT factory at scale: the two data inputs that blocked minting are now
built and run at full scale (2026-09-11, this session).** (1) **Katalog:** every
§70-expired volume's records are scraped (`leibniz catalog scrape
--expired-volumes`: 31 volume slices, sub-cap by construction — the site
matches `bd` as a *substring*, so colliding volume numbers are deepened by
year; **24,916 records, 17,646 crosswalk links, 1,197
works**), yielding **17,162 §70 piece citations, 11,595
localizable to exact canvases** (crosswalk + folio resolver, 68 %).
(2) **Reading text:** the §70 volumes' free digital copies were located and
verified (archive.org public-domain scans with hOCR, the GWLB repositorium
PDFs, Potsdam's born-digital PDFs — **21 of 31 volumes readable**),
and a layout-aware extractor (`align/edition.py`) read **6,188
printed pieces / 26.2M characters of reading text** with page
anchors (Open Q #13's "page anchors" solved by the print's own running heads
and headings), joined to the katalog into the edition cache
(**10,029 manuscript witnesses with their piece's text**).
Cross-source agreement between two independent OCR layers of the same volume
(IA Tesseract vs GWLB ABBYY, 5 volumes) is the free extraction-QA
estimate: **81.6% mean agreement**. (3) The C1 HTR lines live on
the operator's machine, so `gt_lines` is still empty *here*: minting is one
runbook away (`reports/gt-factory.md`). The whole C pipeline is wired: pages
flow `pending → segmented → recognized` (C1), and §70-expired edition text is
retro-aligned onto those recognized lines to mint `gt_lines` (C2).

**Phase C1 — corpus segmentation + HTR v1 batch pipeline.** Built `leibniz
pipeline segment` / `recognize`: a status-driven, resumable, idempotent state
machine over `pages`, storing per-line geometry + text + confidence with
`status='machine'` and one `runs` row per batch (model@version, params, git SHA,
counts, wall time). Per-page failures are isolated and enumerated with a reason
(blank → `no_lines`, missing image, segmenter error). **Segmentation quality is
measured, not assumed:** every page gets a `page_stats` row (line count, region
coverage, line-height CV, overlap + short-line anomalies) — the signal the C2/C4
stratum heuristic reads. Engine-agnostic (kraken segmenter/recogniser injected;
fakes in tests), GPU-aware (`--device`), `--redo`/`--sample`. The live 500-page
run needs the kraken stack + image pull (absent here); the pipeline is built and
offline-tested (+27 tests) with the operator runbook + GPU/cost estimates in
`reports/htr-v1-sample.md` (regenerated by `leibniz pipeline report`).

**Phase C2 — GT factory at scale. ✅ The B2→C2 localization bet holds.** Built
`leibniz align factory`: for each §70-expired volume it enumerates the pieces
(katalog `aa_refs` × `legal.py`), localizes each scan (A3 crosswalk → work; **the
folio resolver** turns the katalog `Bl.` range into exact canvases via the IIIF
folio labels C1 stored — Open Q #10 **solved**), gathers the piece's C1 HTR lines,
aligns the §70 reading text onto them (**anchor-guided banded aligner** for
long multi-page pieces and for edition texts far longer than the piece —
B2's blocking gap, now built and exact-vs-full-DP tested), sets the mint
threshold **per stratum** (fair copies 0.55 … heavy revision 0.72 — Open Q #11),
and mints `gt_lines` with provenance + the license gate (§70 → `open`;
Transkriptionspool → `nc`, never in a CC BY export). Below-threshold lines are
discarded; re-minting is idempotent. **Live-validated (this session, OpenAI key
supplied):** the vision reading-text extraction + `assess_extraction` QA (Open Q
#12) run on real Leibniz edition print (Gerhardt II, 1875, PD) — `gpt-4o`
faithfully transcribed the reading text and **dropped the running head / page
number / signature**, and the two-model QA flagged **1/2** pages (mean agreement
0.67), catching exactly the code-switched page where the control model dropped
~60% of the text. Full deliverable `reports/gt-factory.md`
(+ `reports/gt-factory-extraction-qa.json`); regenerated by `leibniz align
gt-report`. Machinery offline-tested (+33 tests). **The mint has run
(2026-09-15/16, operator's store, six shard workers, ~2 h + a cleanup pass):
297,424 open-bucket lines** — fair_copy 9,913 · light_revision 96,175 ·
heavy_revision 190,162 · scrap 1,174 — from 6,383 minted piece citations,
**5.9× the ≥50k target**, after two live failures the run itself surfaced and
that are fixed (the aligner OOM on volume-length edition texts; WAL lock
collisions between workers). What the factory cannot measure is *precision*:
the C2 gate is the 200-line hand audit, now tooled (`leibniz align
audit-sheet` → an HTML sheet of line strips with verdict buttons;
`audit-score` → per-stratum precision with Wilson intervals and the
corpus-weighted figure against the 95 % gate).

### Prior gate (retained): Phase B2 (retro-alignment prototype) — ✅ GO.
The aligner (`src/leibniz/align/`) mints **98.8% of lines at 97.5% precision** on
the PHILIUMM val split under real HTR (diplomatic; 98%+/97% across divergence
conditions), with **zero** edition-omitted false mints — confidence withholds
lines with no edition counterpart, so a dropped passage costs *yield, not polluted
GT*. C2 is built directly on this engine. Full deliverable:
`reports/alignment-prototype.md`.

### Prior gate (retained): Phase B1 (benchmark harness + PHILIUMM reproduction) — ✅ GO.
The engine-agnostic HTR evaluation harness (deliverable **D5**) is built and, run
against the PHILIUMM model on its own 1,878-line val split, **reproduces the
claimed CER**: measured **7.95%** (95% CI 7.49–8.46) vs the self-reported
**8.33%** — Δ **−0.38**, inside the ±1-point gate. It lands *exactly* on the
model's own `metadata.json` figure (accuracy 0.9205 → 7.95% char error). WER
27.04% vs claimed 28.56%. **Verdict: build on the PHILIUMM model** (unblocks the
C phases; B2 too). Full deliverable: `reports/philiumm-repro.md`.

Earlier this cycle: **Phases A2 (image cache) and A3 (katalog crosswalk)** —
complete. Both depend only on A1 (done). A0→A1→A2→A3 are all green.

### Phase B1 in numbers (this session)

- **CER 7.95%** (95% CI 7.49–8.46), **WER 27.04%** on 1,878 val lines, `philiumm`
  policy (NFD + whitespace-collapse — the model's own training normalization).
- **464 / 1,878 (24.7%) lines character-perfect**; macro-CER 9.16% (the short
  marginal-fragment lines carry the tail, which is why the headline is micro-averaged).
- **Normalization sensitivity:** philiumm 7.95% · lenient 7.61% · strict 7.95% —
  normalization moves the number <0.4 pt, so it is **not** the source of any gap.
- **Frontier-VLM comparison (RAN, OpenAI key supplied):** on a seeded 150-line
  subsample, zero-shot vision LLMs are **4–6× worse** than the fine-tuned HTR
  model (Kraken 8.19% on the same lines): **gpt-4o 45.87%**, **gpt-4.1 38.62%**,
  **gpt-4.1-mini 34.79%** CER. Counterintuitively the *smallest* model won among
  the three — the flagships more often "modernize"/normalise the archaic spelling.
  Total API cost **$0.49** (450 calls; usage captured from each response). First
  published LLM-on-Leibniz numbers.
- **Throughput:** ~1,878 lines in ~160 s on CPU (batch 8), no GPU.

### What was built (B1) — deliverable D5

```
src/leibniz/htr/
  metrics.py    CER/WER, edit distance, the named NormPolicy (frozen recipe),
                micro/macro aggregation, bootstrap CIs (deterministic, seeded)
  bench.py      LinePair input · Engine protocol · transcribe_pairs +
                score_hypotheses + evaluate · EvalResult · per-line JSONL dumps ·
                the frozen protocol `b1-2026-07` · EchoEngine (tests)
  engines.py    KrakenEngine (safetensors via kraken.models.loaders.load_models;
                pre-extracted-line inference, valid_norm=False) + AnthropicEngine
                + OpenAIEngine (Claude/GPT vision over httpx; skip without a key;
                capture token usage + $ cost)
  data.py       loaders: HF parquet val split · image+.gt.txt dir · seeded subsample
  artifacts.py  cache-first streaming fetch of the Zenodo model + HF val split
  report.py     render reports/philiumm-repro.md + gate verdict + VLM-panel table
  cli.py        leibniz bench {fetch, protocol, run, repro}  (+ --reuse-hyps,
                --with-llm --llm-engine {anthropic,openai} --llm-model … [panel])
reports/philiumm-repro.md          B1 deliverable (measured vs claimed, honest)
reports/philiumm-repro.lines.jsonl per-line error-analysis dump (1,878 rows)
pyproject.toml   optional `bench` extra (kraken, pyarrow) — lazily imported
```

The heavy stack (kraken, torch, pyarrow) is an **optional** extra, imported
lazily: the harness, its metrics, and all its tests run without it. Artifacts are
CC BY 4.0, cached under `data/models/`, `data/gt/` (gitignored).

- **A2** gives us a resumable, checksummed local image cache and — as a bonus —
  the **full `pages` table** (236,795 rows), derived **offline** from the METS
  we already cached. A live dev slice of **80 images** was pulled and verified.
- **A3** joins the BBAW Ritter-Katalog to our works. A 6-query live sample
  already crosswalks **1,094 / 2,225 works (49.2%)** with **99.96% GWLB-link
  resolution**; the full scrape (an operator job) is documented.

Everything is green and offline-testable:

- `uv run ruff check .` / `ruff format --check .` — clean (72 files).
- `uv run pytest` — **236 passed, 1 skipped** (was 171; +65 for the HTR harness).
  The one skip is the parquet-loader test, which needs the optional `pyarrow`.

Bulk artifacts (the SQLite store, `data/images/`, `data/katalog/`, `data/oai/`,
and now `data/models/`, `data/gt/`, `data/bench/`) are gitignored. Committed
deliverables: `reports/census.md`, `reports/crosswalk.md`, and **new**
`reports/philiumm-repro.md` (+ its per-line `.lines.jsonl` error dump).

### ⚙️ Delivery-model correction (revises the A2 prompt; see Divergences)

The A2 prompt assumed the IIIF Image API for every page. Per the A1 "Major
drift", only ~1/3 of works are IIIF-served. **Resolution:** the GWLB METS
`fileSec` — already inside the cached OAI ListRecords XML — carries an
authoritative `DEFAULT` JPEG URL (`…/content/{id}/jpgs/default/{seq:08d}.jpg`)
for **every** page, IIIF and static alike. A2 caches that uniform derivative
across all 236,795 pages; the IIIF Image API service URL is still stored per
page (`pages.image_service_url`) for D2 deep-zoom, but is not the cache source.
This makes A2 uniform, offline-derivable, and free of URL guessing.

### What was built (A2 + A3)

```
src/leibniz/images/            IMAGE CACHE (A2)
  pages.py     derive pages (delivery URLs) from cached METS fileSec — offline
  jpeg.py      dependency-free JPEG dimension + truncation reader (SOF/EOI walk)
  fetch.py     fetch (resumable, integrity-retry) / verify / stats(+census)
  cli.py       leibniz images {pages,fetch,verify,stats}
src/leibniz/catalog/           KATALOG CROSSWALK (A3)
  shelfmarks.py  robust LH/LBr/Marg/LK normaliser (Roman↔Arabic, Bl./S., Stück)
  scrape.py      23-column result-table parser + polite enumeration (5000-cap aware)
  crosswalk.py   gwlb_link (1.0) primary + shelfmark (0.7) secondary matcher
  report.py      reports/crosswalk.md
  cli.py         leibniz catalog {scrape,crosswalk,report}
  __init__.py    KATALOG_ATTRIBUTION (CC BY 4.0)
src/leibniz/db.py              + pages image-cache columns & migration; katalog_records
                               + crosswalk typed helpers; git_sha()
reports/crosswalk.md           A3 deliverable (match-rate by set/method, honest)
reports/census.md              + "Image cache (Phase A2)" section
tests/                         +80 tests; fixtures/{images/thumb_sample.jpg,
                               mets/listrecords_filesec.xml, katalog/results_sample.html}
```

### A2 in numbers

- **`pages` fully populated: 236,795 rows** (static 159,162 · iiif 77,633; 27
  zero-page works) — matches the A1 census exactly. Derived offline in ~34 s from
  `data/oai/`; **resolves Open Q #2.**
- **Dev slice pulled live:** `00067974` (LH 35, 1, 13 — IIIF, 40 pp) +
  `DE-611-HS-854976` (LBr. 464 — static, 40 pp) = **80 images, 126.3 MB**;
  `images verify --deep` → 80/80 OK, 0 corruption.
- **Mean page ≈ 1.6 MB → projected full pull ≈ 365 GB** (within SPECS' 200–400 GB).
  Measured dimensions 1098×1793 … 4921×4394 px.
- Fetch is **sequential**: with one GWLB host at ≤1 req/s (SPECS §7.4), per-host
  concurrency is a no-op, so throughput is set by `--min-interval`, not threads.

### A3 in numbers (live 6-query sample)

- **16,177 records scraped → 15,382 distinct**; **12,582 crosswalk links**.
- **Records matched: 12,535 / 15,382 (81.5%).**
- **Works matched: 1,094 / 2,225 = 49.2%** — from *six* queries.
- By method: **gwlb_link 12,384 (+5 unresolved) · shelfmark 198.** Link→work
  resolution = **99.96%** (the join is essentially exact).
- **3 of 6 queries hit the 5000-row cap** (Reihe I,1 / I,2 / `sign_ol=LH 35`) —
  flagged, not silently truncated. Full ≥80% coverage needs the full scrape.

---

## Phase log

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

### W5 — the review's fixes and six reader features (2026-10-10) ✅ code · ✅ deploy · ✅ index rebuild · ✅ letters · ⏳ re-mint

- **Setting.** A cloud session on a fresh clone of main at `9c96c7f` (after
  #41); the fixture store only — no store, server or live index. Live
  checks were polite GETs: the GWLB (an IIIF `info.json`, the resolver's
  page link, the repository's volume pages), correspSearch (sample pages),
  the Leibniz-Katalog's extended search. Baseline 705 tests; 808 at the end,
  ruff clean.
- **GT factory, before the re-mint** (`b725def`). Minted rows belong to their
  catalogue record (`gt_lines.record_id`, its index and the backfill from
  `source` added by the factory under its write lock, never on a read
  path): re-minting a record replaces its rows only, so two pieces sharing a
  folio no longer erase each other's lines, `--resume` skips a record by its
  own rows, and a line two records mint goes to the higher alignment
  confidence (ties: the lower record id) whatever the shard order. `Bl.`
  ranges keep their sides (`resolve.FolioSpan`: `Bl. 5v` is the verso), in
  the factory, the web placement and the K1 census and pilot. One piece per
  record: the edition cache records which printed pieces and which free copy
  a record's text came from, and the factory mints it once under that
  volume — no line is filed under a volume without text; each row's source
  names its channel. The en dash and the double oblique hyphen are line-end
  hyphens; minted text is one line. `LBrF 20` parses as LBr F 20. One hand
  rule for both censuses (`catalog/hands.py`). The scored audit writes
  `reports/gt-audit/audit-summary.json`, which the GT card and `gt-report`
  quote instead of the preliminary 97.5 %. The vi4 summary counts every
  held-out page in the CSV. K1's pilot report re-rendered from its own 2-page
  run (the committed one mixed a 3-page selection over 2-page readings).
- **The site's faults** (`ed4d63e`). Search: every word must match by
  default (`match=any` the broader net; Meilisearch's default dropped words);
  exactness ranks before proximity (`monas` before *Monasteris*); titles,
  shelfmarks, AA references and folio labels indexed folded like the query
  (`meta_folded`, so `AA VI,4 N. 109` finds its pages); paging stops at the
  10,000 reachable hits with `reachable` in the answer; control characters,
  malformed filters and the index's refusals are a 400/422, not a 500 or a
  false 503. A 404 page escapes the path in its canonical and og:url tags.
  "Text of this piece" downloads the folios of the work it was offered on.
  The source image links to the delivery JPEG the machine read (the IIIF
  base URI answers 400), the IIIF service beside it. Every page links to
  its own page in the GWLB viewer (`resolve?id=…&page=<seq>`, checked).
  Letter convolutes are named by shelfmark and correspondent instead of
  "Nachlass Gottfried Wilhelm Leibniz". IIIF: the extension context before
  the Presentation context, Image API 2 services with `@id`/`@type` and a
  profile URI, no null sizes, no manifest for a work without pages. IPv6
  clients are rate-limited by their /64.
- **Scans registered twice** (`d02140d`; Open questions #19). A probe of 27
  works found the rule (`images/twins.py`): same image size, file sizes
  within max(1 KB, 0.1 %), a recto and a verso; confirmed only when the
  lines lie in the same places (IoU ≥ 0.8 for half of them). It happens in
  the IIIF works too. A spread (one recto and one verso, landscape) is split
  at the fold, verso left; triples, upright images and spreads with many
  lines across the fold are folded onto one page. The index build applies it
  as it reads the lines and writes the groups beside the index for the web
  app; `leibniz images twins` writes the same file alone. Its figures reach
  `/api/stats` as `scans` (each scan once), `lines_once` and `twins`;
  `images` there has said where the images are served from since the
  mirror, and the first draft's count under that key never reached the
  About page (caught before the merge, tested through the API now).
- **Citable lines** (`7cf6c06`). Lines numbered from 1; `/page/<id>#L<n>`;
  a Cite box with model, run and a permalink pinned to the run;
  `?run=N` reads a page as run N left it, so a citation keeps its text
  after C4.
- **Lookup** (`1c0a9e4`). `/api/lookup` and the search page: a shelfmark with
  or without its folio, an AA piece number, a work or page id → the place.
  A "Search this work" box on every work page.
- **Letters; the Faszikel index** (`5ae21e3`). `leibniz catalog letters`:
  Bodemann's 1889 catalogue (the LBr numbering) letter by letter from
  correspSearch (BBAW, CC BY 4.0) → `letters.json` beside the store;
  `/letters`, `/api/letters`, the letters on each convolute's page, years
  and places in the browse index, and names for the convolutes the
  catalogue records leave unnamed (the alphabetical check still applies).
  A reader asked for a Faszikel index: a work's catalogue records now come in
  folio order, `/api/contents` and the browse filter find the convolute that
  holds a piece by its title, and the index gives each page the titles and
  AA references of the pieces on its folios — for the catalogue records the
  store holds (Open questions #27: not, for one, the Monadologie's).
- **Links out** (`23359e0`). Each catalogue record links its record in the
  Leibniz-Katalog (its extended search, id and catalogue number), its first
  folio at the GWLB, the volume of each AA reference where it can be read
  (the repository's own page for I,3/9/11/12/14–27, III,5–9, VII,3–8, each
  checked — the repository shows its index for any other address), and for
  a letter of 1708–1716 not yet edited the Leibniz-Archiv's transcriptions
  of that year. The catalogue's attribution names its editor, the
  Arbeitsstelle Potsdam I.
- **Not decided here.** Kalliope holds per-convolute records for every LBr
  work (its ids are the work ids) with GND places and folio notes, but
  states no licence on its site; not used (Open questions #25).
- **The staging look and the deploy (2026-10-10/11; the operator ran every
  command on the box, this session read the outputs and checked the live
  site over HTTP).** Staging ran the branch at `8d532da`, then `25961a1`.
  Twelve HTTP checks against the live store and index answered as designed:
  the shelfmark and AA lookups (`LH IV, 6, 18 Bl. 1r` and `A VI, 4 N. 109` →
  `00068642:0001`); the piece texts pinned to their work; the Katalog links
  with their catalogue numbers; the record and page links to the GWLB; the
  source image a JPEG; the permalink pinned to run 74; two words 63 hits with
  `match=all` against 376 with `match=any`, the old behaviour; page 600
  clamped to 500 of 10,000 reachable; a malformed `set` refused with 422
  (FastAPI's check of the parameter's shape; the plan page had said 400);
  `/api/letters` 503 before the letters existed. The browser look was good
  except `Monadologie` in the browse filter, which found nothing: the store
  has no catalogue record for LH 4, 1, 1a or 1b (Open questions #27). Two
  fixes on the way, both on staging before the merge: `8d532da` (the build
  wrote its distinct-scan count under `images`, the key `/api/stats` already
  used for the image origin, so the About tile could never show; now
  `scans`, tested through the API) and `25961a1` (the browse page's status
  line says what the catalogue found, and that the site holds part of it).
  Merged as #42 (`aac0fc9`); the §9 update, which carried K1's code along
  (it changes nothing the site runs); `staging.sh --main`. The index rebuild
  under §5 with the staging unit stopped (§14): the live index 17 GB with
  33 GB free before; the second generation swapped in at about 02:59 UTC on
  2026-10-11, after about five and a half hours (49.5 minutes of CPU), and
  the old one deleted (34 GB free after). `leibniz catalog letters` ran
  beside it as a transient unit of its own, about half an hour. One restart
  of both units after both.
- **Live figures (`/api/stats`, read 2026-10-11).** works 2,225 · pages
  236,795 · **scans 196,439** · lines 13,508,625 · **lines_once 9,846,450**
  · twins: candidates 40,816, groups 40,297 (spreads 39,442, folds 855),
  unconfirmed 519, registrations 80,653, second registrations 40,356 · index
  built 2026-10-11T02:59:06Z. `/api/letters`: 15,425 letters (correspSearch
  listed 15,439 on 2026-10-10). `/api/works`: 991 of the 1,060 LBr
  convolutes named (680 before), 1,043 with the years of their letters.
  Search: `monas` puts *monas* itself first (before: *Monasteriax*);
  `characteristica universalis` 85 pages, the two copies of one text that
  headed the list on 2026-10-10 (`DE-611-HS-855676:0004` and `:0005`) now
  the left and right halves of a split spread; `AA VI,4 N. 109` 88 pages (the
  review counted 123,980). The operator's spot-check of six decisions (five
  spreads in LBr and LH, one fold): all correct.

### K1 — Kurrent track (2026-10-09) ✅ Tasks 0–4 · gate for K2: **GO** with `trocr-kurrent-xvi-xvii` · ✅ the operator's verdict · ✅ merged (#41)

- **Setting.** The operator's desktop: the WSL checkout
  `/home/evana/LeibnizLegible` (the Claude Code session opened in the stale
  Windows clone and drove WSL through `wsl.exe`; Divergences), on the plan's
  one branch after a fast-forward to `014b3a1`; the store read-only
  (17,061,699,584 bytes); the Kurrent Trace package present and complete
  (383 crops, 383 labels, 383 records, a validator and a scorer that reports
  strict NFC and a reading policy — NFC, long s to s, whitespace collapsed —
  as micro-averaged CER and WER). `.venv-k1` from `uv sync --extra bench
  --extra gt --extra kurrent`, built from the uv cache in seconds: torch
  2.12.0+cu130 sees the GTX 1660 Ti (CUDA 13.0). Baseline in `.venv-w3`:
  ruff clean, 644 tests. Task 0 also found `.venv` — the prompt's "pipeline
  environment" — without torch or kraken (its site-packages last changed
  2026-09-20); nothing in K1 depends on it. No API key in the environment,
  so Task 3's vision row will be skipped unless one is exported. The go came
  after the pre-flight.
- **Task 1, the aligner's noise tolerance** (`align/tolerance.py`, `leibniz
  align kurrent-tolerance`, +15 tests; `reports/kurrent/align-tolerance.md`
  + `.json`). The B2 harness over the recorded B1 machine text
  (`reports/philiumm-repro.lines.jsonl`, 1,878 lines in validation order, 76
  pieces of 25, the gold joined as the edition text), no model and no image.
  The HTR side is corrupted at a per-character rate: a fired letter is
  replaced by a look-alike from a table for a cursive hand (the minims u n m
  i r, the round letters a o e c, the long-s family s f l t, b h k, g q p y,
  capitals, digits; multi-character targets for split minims), or dropped,
  doubled, merged with its neighbour (*in*, *ni*, *rn*, *nn* → *m* and the
  like) or split off by a word space; a fired space is a merged word space.
  The rate is calibrated per level by bisection (three uniforms per
  position, so a higher rate fires a superset); the achieved CER is measured
  with the B1 scorer's edit distance, the folded CER (after the aligner's
  normalisation) beside it. Levels hit 10.0 %, 20.0 %, 30.0 %, 40.0 %, 50.0
  %, 60.0 %. Yield and precision at the five stratum thresholds with the
  factory's gate — the harness's `LineEval` gained `burst` and `summarize` a
  `factory_gate` option, off by default, so the B2 numbers are what they
  were. Results: precision ≥ 95.7 % through 40 % CER in fair copy, light and
  heavy revision; yield at 30 % CER 97.0 % / 94.0 % / 79.8 % / 46.0 %;
  break-even yield < 50 % at ≈ 55 / 48 / 38 / 29 % CER and precision < 95 %
  at ≈ 51 / 48 / 42 / 39 % (fair / light / heavy / scrap). The recorded
  machine text's own errors are 39.4 % substitutions, 39.7 % deletions and
  20.9 % insertions; the model is heavier on substitutions, and a dropped
  character costs the confidence nothing where a substituted one counts
  against it, so the break-even is on the conservative side. Uniform
  corruption is the smooth middle: real errors cluster. The `kurrent` extra:
  transformers 5.12.1 (5.13 and later need safetensors ≥ 0.8; kraken 7.0.3
  pins < 0.8), tokenizers 0.22.2, huggingface-hub 1.16.1, hf-xet 1.7.0;
  torch unchanged. Commit `5eb5d55`.
- **Task 2, the German census** (`enrich/langid.py`,
  `align/kurrent_census.py`, `leibniz align kurrent-census`, +28 tests;
  `reports/kurrent/census.md`, `census-summary.json`,
  `census-by-volume.csv`, `german_pieces_index.csv`;
  `data/kurrent/german_pieces.jsonl` for K2; 22 s on the store, read-only).
  *The identifier:* three disjoint stopword lists with the 17th-century
  spellings (*vnd*, *vndt*, *daß*, *seyn*, *sey*, *alß*, *wan*, *umb*,
  *auff*), the French elision clitics counted as French, the words two
  languages share (*et*, *est*, *de*, *in*, *si*, *non*, *qui*, *des*,
  *die*, *nos*, *vos*) in no list; under 8 tokens or under 2 hits → unknown
  (stopwords are about one token in three, so eight tokens give two or three
  hits, and two is the least that keeps a loanword or a Latin date from
  deciding); dominance ≥ 0.65 names the language, a runner-up at ≥ 0.25
  makes it mixed. The pieces classified `de` have dominance quartiles 0.94 /
  0.98 / 1.00. *The join:* `enumerate_pieces` → one folio index per work →
  the C2 resolver's pages → recognised lines (`lines.text` not null, as the
  factory gathers them) → minted lines by the factory's `source` string →
  the stratum by `classify_piece` over the pages' `page_stats` plus Textart.
  *The hand:* `eigh.` on the piece itself (`Abf., eigh.`, `Konz.; eigh.`) is
  *own*; on an address, a correction or a postscript only (`Abf.; eigh.
  Aufschr.`) is *partial*; Leibniz's hand is *own* with no sender or Leibniz
  as sender (the C2b rule). *Results:* cache 2,036 de · 3,631 la · 3,999 fr
  · 331 mixed · 32 unknown; 10,121 pieces with a text (7,041 without — the
  volumes with no free copy); German 2,173 pieces (113 of them mixed with
  German leading), 1,694 localizable, 5,874 pages, 401,394 lines, 40,915
  minted (10.2 %); Latin and French 7,694 pieces, 1,328,532 lines, 252,762
  minted (19.0 %). By volume: the Reihe I volumes with a text run from 61 to
  171 German pieces (9–22 %); III,3 373 of 567 and III,4 278 of 424 are
  German (the Harz mining correspondence), IV,3 140 of 263; VI,4 14 of 566.
  German pieces by stratum: heavy revision 1,124 pieces at 8.0 % yield,
  light 507 at 19.3 %, fair copy 4, scrap 31. By hand: own 183, partial 542,
  other 1,430; **Leibniz's own hand 82 pieces, 18,056 lines.** *The mint
  check* (two ground-truth-free readings of the 40,915 lines the factory
  minted on German pieces): 27,643 (67.6 %) carry German stopwords and no
  Latin or French ones in the minted text, 3,178 (7.8 %) the reverse
  (addresses, titles, quotations in Latin script), 7,628 neither; mean
  confidence 0.839 against 0.927 on Latin and French pieces, on machine text
  of 41.0 folded characters a line against 46.2. So the hypothesis — German
  declined, not minted — holds only by half: the German yield is half the
  Latin and French one, but what was minted is German text aligned at a
  confidence chance cannot give. Either the PHILIUMM model reads Kurrent far
  better than its makers expect (its FoNDUE-GD base is multilingual), or the
  lines it accepted are the legible minority; the pilot (Task 4) measures
  the baseline's yield on German pieces directly and the operator's look at
  the side-by-side will say whether the words are German. *A finding on the
  way:* `stratum_from_textart` matches full words the catalogue never writes
  — it recognised a class on 129 of 10,121 pieces — so the C2 mint's
  stratum, and with it the threshold, came from the layout statistics alone
  (Open questions #23; recorded, not fixed).
- **Task 3, the bootstrap readers on Dresden** (`htr/trocr.py`,
  `htr/kurrent.py`, `leibniz bench kurrent-smoke`, +12 tests;
  `reports/kurrent/bootstrap-candidates.md` + `.json`; raw readings under
  `data/kurrent/smoke/`). `TrOCREngine` wraps a Hub TrOCR checkpoint behind
  both reader protocols (`transcribe`, `transcribe_conf` with the mean token
  probability as confidence), weights to `data/models/hf/` (inference files
  only, never the optimizer states); the Kurrent fine-tunes set a space
  before every punctuation mark, a Transkribus label convention, and the
  engine closes it (`tidy`), said in the report. McCATMuS (16 MB, Zenodo)
  loads through kraken's own `load_models` — the CoreML loader is an entry
  point, so `KrakenEngine` needed no legacy path. The Dresden set is the
  Kurrent Trace package's 383 lines on 20 pages, read once per candidate on
  the GPU and scored under the B1 harness's three policies and the package's
  two (strict NFC; reading: long s folded, whitespace collapsed), the
  package's own `scripts/evaluate.py` run on the same readings as a check
  and agreeing on every row. **Ranking (CER, `philiumm` policy):**
  `trocr-kurrent-xvi-xvii` 7.4 % (6.7 %–8.2 %; lenient 5.2 %, package
  reading 5.9 %; 334 ms/line); `trocr-hanse-xvi` 8.9 % (8.2 %–9.6 %; lenient
  6.7 %, package reading 7.3 %; 209 ms/line); `trocr-hanse-xvii` 10.9 %
  (10.0 %–11.6 %; lenient 8.5 %, package reading 9.3 %; 337 ms/line);
  `philiumm` 29.5 % (28.2 %–30.9 %; lenient 26.3 %, package reading 28.1 %;
  34 ms/line); `mccatmus` 51.7 % (50.2 %–53.2 %; lenient 49.5 %, package
  reading 51.0 %; 19 ms/line). No vision row (no API key in the
  environment). The report says what it is: a ranking, not a benchmark — the
  Dresden lines are public and may sit in a training set, and the text is
  nc-bucket, so the report carries numbers only. Two readings for K2: the
  baseline reads a chancery Kurrent at 29.5 %, far from noise (Open
  questions #24 again), and the Bern TrOCR model reads it at 7.4 %.
  Qualifying for the pilot (at or under two thirds of the baseline's CER,
  the cut named in advance): `trocr-kurrent-xvi-xvii`, `trocr-hanse-xvi`,
  `trocr-hanse-xvii`.
- **Task 4, the pilot on Leibniz's own German** (`align/kurrent_pilot.py`,
  `leibniz align kurrent-pilot`, +5 tests; `reports/kurrent/pilot.md`,
  `pilot-yield.csv`, `pilot-summary.json`; readings in
  `data/kurrent/pilot-readings/`, the page in
  `data/kurrent/pilot-side-by-side.html`). 20 German pieces drawn from the
  census over 13 volumes, the strata (fair_copy 2, heavy_revision 7,
  light_revision 7, scrap 4) and the hands (other 8, own 6, partial 6; 2 in
  Leibniz's own hand), plus 5 Latin or French controls (la, fr, la, fr, la);
  pages capped at 2 per piece, 50 pages, 2,639 lines. Readers: `philiumm`,
  `trocr-kurrent-xvi-xvii`, `trocr-hanse-xvii`, `trocr-hanse-xvi`, `v1`
  (`v1` is the stored machine text; the others read the same lines afresh
  from the page images through the audit module's crop machinery, the
  polygon masked, no downscale, each page decoded once). Every reading went
  to JSONL under `data/kurrent/`, resumable, nothing to the store. Then the
  factory's alignment per piece per reader as a dry run at the per-stratum
  thresholds. **Yield at the gate:** `philiumm` German 12.5 % (conf 0.296),
  controls 41.6 % (conf 0.447); `trocr-kurrent-xvi-xvii` German 20.2 % (conf
  0.323), controls 23.6 % (conf 0.358); `trocr-hanse-xvii` German 20.6 %
  (conf 0.326), controls 18.2 % (conf 0.339); `trocr-hanse-xvi` German 22.5
  % (conf 0.335), controls 30.5 % (conf 0.406); `v1` German 16.4 % (conf
  0.308), controls 40.5 % (conf 0.445). By stratum for
  `trocr-kurrent-xvi-xvii`: fair_copy 38.9 % (54 lines); heavy_revision 17.6
  % (1,119 lines); light_revision 42.6 % (460 lines); scrap 7.5 % (655
  lines); by hand: other 13.5 % (1,095 lines); own 25.4 % (688 lines);
  partial 27.7 % (505 lines). The controls: the Latin-trained baseline
  (philiumm) wins the control pieces as it must. The operator's look at the
  thirty crops of `data/kurrent/pilot-side-by-side.html` is still to be
  recorded: `uv run --no-sync leibniz align kurrent-pilot --no-read
  --operator-verdict "…"` re-renders the reports from the readings on disk
  with the answer verbatim. **Gate:** **GO for K2 with
  `trocr-kurrent-xvi-xvii` (MIT)**: German yield 20.2 % at the factory's
  gate on the pilot's lines against 12.5 % for the `philiumm` baseline read
  the same way and 16.4 % for the stored v1 text — 1.23× the factory's own
  German mint on the same lines, 1.6× the baseline's; the controls order as
  they must (`philiumm` wins them). `trocr-hanse-xvi` reads 22.5 % but
  states no licence on the Hub: evaluated, not built on. It stays under half
  the baseline's yield on the Latin and French controls (41.6 %): German
  pieces will mint, but thinner than Latin and French ones do with the model
  made for them. On Dresden the same reader read at 7.4 % CER, under the
  Task 1 break-even for every stratum (yield falls under 50 % at ≈ 38 % CER
  on heavy revision, the German pieces' main stratum), so the yield the
  pilot measures is the pages' and the edition's, not the reader's noise.
  Task 5 (Plan B) is skipped: a usable reader exists.
- **Numbers to carry.** Break-even CER (yield < 50 %) ≈ 55 / 48 / 38 / 29 %
  and (precision < 95 %) ≈ 51 / 48 / 42 / 39 % by stratum; German pieces
  2,173, pages 5,874, lines 401,394; minted yield German 10.2 % vs Latin and
  French 19.0 %; Leibniz's hand 82 pieces; Dresden CER (`philiumm` policy)
  trocr-kurrent-xvi-xvii 7.4 %, trocr-hanse-xvi 8.9 %, trocr-hanse-xvii 10.9
  %, philiumm 29.5 %, mccatmus 51.7 %; pilot German yield philiumm 12.5 %,
  trocr-kurrent-xvi-xvii 20.2 %, trocr-hanse-xvii 20.6 %, trocr-hanse-xvi
  22.5 %, v1 16.4 %; control yield philiumm 41.6 %, trocr-kurrent-xvi-xvii
  23.6 %, trocr-hanse-xvii 18.2 %, trocr-hanse-xvi 30.5 %, v1 40.5 %.
- **Licences recorded so far.** Kurrent Trace v0.1 (data/external): the
  Dresden transcript under CC BY-NC-SA 4.0 by the package (Zenodo's field
  says CC BY 4.0; the conflict is unresolved; nc bucket, internal evaluation
  only), images Public Domain Mark 1.0, the package's own code CC0.
  Candidate readers, from the Hub and Zenodo on 2026-10-09:
  dh-unibe/trocr-kurrent-XVI-XVII and dh-unibe/trocr-kurrent MIT;
  fgho/trocr-hanseXVII-kurrent and fgho/trocr-hanseXVI-kurrent no licence
  stated (evaluate only); McCATMuS CC BY 4.0; Bullinger HTR (GitHub)
  CC-BY-SA-4.0. transformers (Apache-2.0) is the new dependency.
- **Next.** K2: run the factory on the German pieces of
  `data/kurrent/german_pieces.jsonl` with `trocr-kurrent-xvi-xvii` as the
  reader (its readings to JSONL first, then the alignment; the factory's
  recognise stage must not write a second reader's rows into `lines`, so K2
  needs the versioned-rows decision or a side table), expecting a German
  yield near 20.2 % of the pieces' lines at the factory's thresholds; K3
  fine-tunes on what K2 mints. The operator's look at the side-by-side page
  goes into the report when it comes. Nothing is deployed; the branch is
  pushed.

### W4 — text access (2026-10-08) ✅ built and checked on the fixture store · ✅ on staging, the HTTP checks pasted and the browser look good · ✅ merged (#40) · ✅ live

- **Setting.** A cloud session, no store, on the plan's one branch under the
  preamble's evening revision (see Divergences): the code and the tests
  here, the browser checks against the app on the fixture store, the look
  at the live page through the container's proxy (the W1 Playwright recipe:
  `executablePath` the preinstalled Chromium, `proxy` from `HTTPS_PROXY`,
  the egress CA pinned by SPKI), the staging checks handed over.
- **Task 0, what a reader could select today** (the live page view
  `/page/00068221:0043`, 108 lines, headless Chromium, 2026-10-08). The
  line's text is inside the `<button class="line__btn">` that selects the
  line (`user-select` `auto` on both): a drag across three lines left the
  selection collapsed; a drag within one line selected nothing and counted
  as a click (the line highlighted, the image zoomed to it); a double-click
  on a word selected nothing; a plain click highlighted its line, as
  designed. Select-all then copy did reach the clipboard: 11,752 characters
  selected, 11,828 copied, starting "Skip to main content / Leibniz Legible
  / Machine transcription of the Leibniz Nachlass / Search / Browse / About
  / EN / DE …", every badge ("machine. HTR output, unreviewed."), every
  confidence chip and every "Provenance" summary between the lines. With
  `user-select: text` injected on the button and the text, a drag across
  lines selected, and took the badges and the hidden "Line 2" labels with
  it; a drag within a line still counted as a click. No `user-select` rule
  existed in `style.css`; no handler cancelled a selection, the button did.
  Baseline 634 tests, ruff and format clean.
- **Task 1, the text block** (`views/page.js`, `style.css`, `i18n.js`). The
  right column is now `.page-side`: the line list, then `<section
  id="page-text">` with a heading "Text", a help line, a toolbar (`<button
  id="copy-text">` "Copy the text", the download as a button-styled link
  "Download this page as text", a `role="status"` live region), one line of
  provenance — "Machine transcription: {model}, run of {date}; … Quote it
  as “the machine reads it as …”, never as “Leibniz wrote”." with one entry
  per recognition run behind the lines, newest first, from the lines'
  `model`, `run_id` and `run_at` — and a `<pre class="page-text__block">`
  with the lines' texts joined by newlines (a line break inside a text
  becomes a space, as the export writes it; `white-space: pre-wrap`, so a
  long line wraps on screen and copies as one line). Copy calls
  `navigator.clipboard.writeText` inside the click handler (the user's
  gesture is current there) and reports "Copied: N lines."; on rejection,
  or without the API, it selects the block and says "The browser did not
  allow the clipboard. The text is selected: press Ctrl+C (⌘C on a Mac) to
  copy it." A page without text has no block. The header's link list no
  longer carries "Download text"; it carries "Text of this page", an
  in-page anchor to the block that the router leaves to the browser. **The
  line list unblocked:** `.line__text { user-select: text }`, the number,
  the badges, the button's hidden label and the provenance summary `none`;
  `onListClick` returns while a non-collapsed selection stands inside the
  list (a drag within a line, the second click of a double-click), so
  taking text never zooms the image; and a `copy` event whose selection
  lies inside the list is answered by page.js with the selected part of
  each line's text, one per line (Chromium honours `user-select: none` in
  the copy but leaves a blank line in the chrome's place and reports the
  chrome in `Selection.toString()`; other browsers draw the line elsewhere;
  the handler makes the result the same everywhere). The help line says
  how. Keyboard: Copy is a button, the download a link, the jump an anchor;
  Tab, Enter.
- **Task 2, the text of a catalogue piece.** `web/pieces.py` places a
  record the way `align/volumes.py` enumerated the factory's pieces: the
  first of its shelfmarks that carries a `Bl.` range
  (`resolve.folio_range_from_signature`), the work its best crosswalk link
  names (`db.crosswalk_for_record`, by confidence, `gwlb_link` before a
  shelfmark guess), the range selected over the work's folio labels
  (`resolve.index_pages` + `resolve.select_folios`, split out of
  `resolve_canvases` so one index serves every record of a work; the
  factory's path is unchanged). `Placement` carries the pages, the range,
  the shelfmark; `Unplaced` carries the reason in words: "record X is not
  linked to a digitized work", "… its shelfmark 'LH IV, 6, 18' names no
  folio (Bl.) range", "… carries no shelfmark", "… 'LH IV, 6, 18 Bl. 9'
  names folios Bl. 9, but no page of work W carries a folio label in that
  range (3 of its pages carry folio labels)". Where a record links several
  works, the best link is tried first and the next where it cannot place
  it. `GET /api/records/{record_id}/text` (summary "The text of a catalogue
  piece across its folios"; `RECORD_RESPONSES` documents the 404 cases):
  the `# ` header — the project line, `Piece:` (the route's own URL; a
  piece has no page of its own), `Catalogue record: id — title`, incipit,
  date, sender and addressee where the record is a letter, the AA reference
  or "assigned, not yet published", other printings, the katalog URL,
  `Work:`, the title row, `Folios: Bl. 1–2 (from the shelfmark …): n pages,
  canvases a–b, page ids … to …`, the GWLB original, the line count over
  the placed pages, `attr.KATALOG` (catalogue data travels in the file),
  honesty, licence, wording rule, the work layout line — then the pages in
  canvas order through `_page_chunks`, the generator `_work_text` now
  shares (one connection per stream, as W1 built it). Download name
  `leibniz-legible_record-<id>.txt`. `_katalog_for_work` builds one folio
  index per work (from the pages the caller already read) and adds
  `text_url`, `folio_label`, `folio_range`, `n_pages` to the placed
  records; `_ssr_work` renders the same link; `views/work.js` shows "Text
  of this piece ({range})" / "Text dieses Stücks ({range})" under the
  record. `robots.txt`: `Allow: /api/records/` before `Disallow: /api/`;
  `llms.txt` and the README describe the route and `text_url`.
- **Task 3.** The page view's download lives in the block's toolbar; the
  work view keeps "Download the text of this work". The About page's
  transcriptions paragraph (EN and DE) says the text can be taken away per
  page, per work and per catalogue piece, each file with its provenance.
- **Task 4, verified.** Tests +10 (644): `select_folios` against
  `resolve_canvases` over one index; the placements and every reason; the
  record export's header order and body (the fixture's k-109, `Bl. 1-2`,
  places on **three** pages — 1r, 1v and 2r, the last skipped and reported
  as the one-line note — not the "two of three" the prompt expected), the
  TSV rows, the 404s and their wording, the OpenAPI entry, robots, llms,
  the server-rendered link only where a record is placed, and the viewer's
  strings in both languages with `page.download` gone. Then `leibniz serve
  --backend none` on the fixture store and 39 Playwright checks in headless
  Chromium (the GWLB image requests answered with a stub JPEG and a level-0
  `info.json`; axe-core served from the app's own origin because the CSP
  is `script-src 'self'`): the block's text equals the page's lines; a drag
  over it selects; Copy fills the clipboard and the status line, by mouse
  and by Enter; the jump link; in the line list a drag across two lines
  selects without a click, Ctrl+C copies exactly "line\nline", a partial
  selection copies the selected parts, a drag within a line never zooms, a
  plain click still chooses the line, a double-click selects a word; the
  work page's piece link downloads `leibniz-legible_record-k-109.txt` with
  its three folios; a skipped page has no block; About in EN and DE; the
  whole block and the piece link in DE; the clipboard refused and absent;
  390 px without horizontal scroll on page, work and About; no console or
  page errors; axe-core 0 violations on the page view (EN, DE, 390 px) and
  the work view (EN, DE). Screenshots in the session's scratchpad.
- **Not measured here.** Firefox and Safari were not run (only Chromium is
  installed): the line list's selection rests on `user-select: text`
  inside a `<button>`, which the CSS UI spec allows and both browsers
  support, and the copy handler is plain DOM; the operator's look on staging
  in their own browser is the test. The master store was not opened; the
  staging checks under Next are the real-data run.
- **On staging, verified by the operator the same evening.** `staging.sh`
  put the branch on staging and the six HTTP checks came back as designed:
  the server-rendered page view still carries its text; `GET
  /api/records/41800/text` answers the header as built — the record's
  title, incipit, date (1682), AA VI,4 N. 109, its other printing, the work,
  `Folios: Bl. 1 (from the shelfmark LH 4, 6, 18 Bl. 1): 2 pages, canvases
  1–2`, the catalogue's licence line — then two `## Folio` blocks, and
  **84 recognised lines on its 2 pages, mean confidence 0.96**, the first
  run of the piece text on the real store; the work's records carry
  `text_url` for 41800 and 59095 and no other; an unknown record answers
  404; `robots.txt` allows `/api/records/`. The look in the browser followed
  the same evening: good, the operator said. W4 is closed on this branch.
- **Merged and live, 2026-10-09 UTC (the evening of 8 October in New
  York).** Pull request #40 merged as `62711b3`; the desktop's main
  fast-forwarded to it; the runbook's §9 block ran on the box as one `ssh`
  line (24 packages checked, nothing new, restart, `/healthz` ok with
  search ok); the seven checks against `https://leibnizlegible.com`
  answered as on staging (the server-rendered page, record 41800's header
  with `Work: https://leibnizlegible.com/work/00068642` and its 84 lines at
  0.96, two `## Folio` blocks, `text_url` for 41800 and 59095, 404 for an
  unknown record, `Allow: /api/records/`, llms.txt); `staging.sh --main`
  put staging back on main at `62711b3`. The scored audit and the
  cross-check reports are public with the merge; the PHILIUMM team had the
  report first.
- **Next.** K1 on the desktop (it continues on the branch and goes into a
  new pull request); L1 after the call of 13 October; the three sentences
  for David went in the email of 8 October.

### S1 — a staging site on the VPS (2026-10-08) ✅ kit · ✅ installed and verified

- **Setting.** A cloud session, no SSH and no store, on the plan's one branch
  (the preamble; see Divergences). Task 0's look at the box (memory, disk,
  the Caddy version, the `import` line) could not run here; the scripts
  check the two facts they depend on themselves: the Caddy version decides
  `basic_auth` against `basicauth` (renamed in 2.8), and a Caddyfile without
  the §13 import line stops the install before it changes anything. The
  rest is handed over as commands under Next. **The operator's look at the
  box, pasted back the same day:** 3,814 MB of RAM with 3,118 MB available
  and 3,223 MB in the page cache, 618 MB of the 4 GB swap in use; one 75 GB
  disk with 33 GB free; the app, Meilisearch and Caddy active; Caddy
  v2.11.4, so the directive is `basic_auth`; the import line in place with
  `calculemus.caddy` beside it. Nothing in it changes the kit.
- **Task 1, the index name from the environment.** `LEIBNIZ_MEILI_INDEX`
  (default `leibniz_pages`) in `web/settings.py` (`ServeSettings.meili_index`,
  through `to_env`/`from_env` so worker processes get it), `leibniz serve
  --meili-index`, `leibniz index build|status|query --meili-index` (the
  option, else the variable, else the default; `index status` prints the
  uid), `open_backend(meili_index=)` into `MeiliBackend(index_uid=)`, which
  already existed; `deploy/env.example` and the compose file carry the
  variable. Nothing changes for production.
- **Task 2, the kit** (`deploy/`, runbook §14). The unit is the production
  unit with its own checkout `/opt/leibniz-legible-staging`,
  `EnvironmentFile=/etc/leibniz-legible/staging.env` and venv, the same
  sandbox and `ReadWritePaths`. The env is `env.example` with
  `LEIBNIZ_PORT=8001`, `LEIBNIZ_WORKERS=1`,
  `LEIBNIZ_BASE_URL=https://staging.leibnizlegible.com`,
  `LEIBNIZ_RATE_LIMIT=0`. The site block is the production block plus
  `basic_auth` (one user, a bcrypt hash) and `X-Robots-Tag "noindex,
  nofollow"`, the domain named literally, its own JSON log kept 168 h.
  `staging-install.sh` (root, once, idempotent): the preconditions first,
  then the checkout and venv as `leibniz` with the live checkout's uv
  caches; the unit; `staging.env` from the example with the live env's
  store path, search key, image origin and proxy address copied in (an
  existing file is left alone); the site block rendered from the example
  with the hash from `caddy hash-password` (the password read on the
  terminal and piped, never on a command line); `caddy validate` over the
  whole configuration, then `systemctl reload caddy` (a failed validate
  puts the previous block back and reloads nothing); `systemctl enable`;
  then `staging.sh BRANCH`. A re-run keeps the password unless
  `--password`; `--user` renames. `staging.sh BRANCH` (root, any time):
  fetch, `checkout -B staging origin/BRANCH`, `uv sync --frozen`, restart,
  `/healthz`, the address; `--main`; `--status`; `--index` builds
  `leibniz_pages_staging` as a transient systemd unit with the master key
  after saying what it costs and asking, the staging unit stopped meanwhile
  and the serving key's scope checked first (`meili-search-key.sh` scopes
  it to `leibniz_pages*`, which covers the name); `--drop-index`. Both
  scripts `bash -n` and shellcheck clean.
- **Tests.** +12 (634): the settings and both CLIs take the index name (a
  fake Meilisearch records that a build touches only the named index and
  its `_meta`); `tests/test_deploy_staging.py` holds the unit to four
  changed lines, the env to four changed values, the Caddy block to the
  production directives plus its two additions, and the scripts to `bash
  -n` (shellcheck where installed) and to the same domain, port, paths and
  index names as the examples.
- **The first run on the box (2026-10-08, 13:16 UTC) stopped at the Caddy
  reload:** `open /var/log/caddy/leibniz-legible-staging.log: permission
  denied`. The directory was Caddy's own (`drwxr-xr-x caddy caddy`); the
  file was not: `caddy validate`, run as root a moment earlier, provisions
  the log writers and had created the missing log as `root:root 0600`, and
  the reload, as the caddy user, could not open it. The live site stayed up
  (a refused reload keeps the running configuration), and everything before
  that step was in place: the checkout, the unit file, `staging.env`, the
  site block with the hash (the password typed once, kept by the re-run).
  Fix in the kit: the installer creates the log file and gives it to the
  caddy user before validate runs, and owns the directory for that user as
  `install.sh` does (`mkdir -p`, not `install -d`, which resets an existing
  directory's mode). **The re-run at 13:25 UTC went through:** validate,
  reload, the unit, the venv (24 packages, the system CPython 3.12.3 as on
  the live checkout), `/healthz` ok with search ok, staging on `2f7a362`;
  the certificate was not yet issued at the script's last check. Minutes
  later, from the cloud session: `https://staging.leibnizlegible.com/`
  answers `401` over a valid certificate with `WWW-Authenticate: Basic
  realm="restricted"`, the live site `200`. One detail for the record: the
  401 itself carries `Server: Caddy` and neither the HSTS nor the
  `X-Robots-Tag` header, because Caddy writes its own error responses
  outside the `header` directive's wrapper; every response that passes the
  password goes through the proxy and carries them, as the live site's
  `200` and its app-served `404` show (HSTS present, no `Server`). A 401 is
  not indexable content, so nothing is lost. The piped `caddy
  hash-password` worked (the hash is in the block, the password survived
  the re-run); `systemd-run --remain-after-exit` with `--setenv` and the
  read of the key's scope (`GET /keys/{key}`) are still untested.
- **Open.** The operator wrote that an unlisted host would do without a
  password. The kit keeps basic auth: the certificate Caddy obtains puts
  the host name in the public certificate-transparency logs the moment the
  site exists, so "not findable" is not available, and the password is what
  keeps the site private. Dropping it is a small change if wanted.
- **Verified by the operator, 2026-10-08.** The page opens in the browser
  with the password; `/browse` matches the live site; an authenticated
  `GET /` answers `200` with HSTS and `X-Robots-Tag: noindex, nofollow` and
  no `Server` header; `/api/stats` is identical on both sites (2,225 works,
  236,795 pages, 13,508,625 lines, the same confidence histogram), as it
  must be, both reading the same index.
- **Next.** W4, text access, on this branch, verified on staging with
  `staging.sh claude/dazzling-hopper-uxji2x` before anything is merged.

### P1 — PHILIUMM cross-checks (2026-10-08) ✅ Task 1 · ✅ Task 2 run on the store · ⏸ Task 3 (waits for the layout model)

- **Setting.** Run in the cloud session on the C2b branch (no store needed for
  Task 1). Their alignment repository was read at commit `9d2ee4e500e0`
  (main, "Delete temporary files", 2026-09-21): no licence file; nothing copied,
  the worked example fetched cache-first by raw URL into `data/philiumm/sample/`
  (`align/philiumm/fetch.py`, the commit pinned in a `COMMIT` marker). Task 0's
  two questions: the new RF-DETR model is not out (Denisa expects it mid-to-late
  October), and Task 3 waits for it.
- **What was built.** `align/pagexml.py` (PAGE XML lines in document order, with
  zone type, geometry, text and their per-line attributes; tested on a fixture);
  `align/philiumm/sample.py` + `leibniz align philiumm-sample` (fetch, align
  under four configurations, their CSV columns, the line-by-line comparison,
  the HTR-witness tally, `reports/philiumm/alignment-sample.md` + `.json`,
  the full pairs in `data/philiumm/sample/comparison.csv`); +10 tests (616).
- **Their run** (`alignment_report.csv`): 257 HTR lines, 230 replaced
  (89.5 %), 26 without a match; no per-line gate
  (`--conf_threshold 0.0`, `nb_low_conf` = 0), `--min_sim 0.5`; their score is
  `1 − Levenshtein ÷ max(len)` on raw text between the HTR line and the best
  window of whole edition words. Their output carries it per line:
  212 of 230 aligned lines reach 0.7, 230 reach 0.5.
- **This project's aligner on the same files** (`align_piece`, free edition
  ends, threshold 0.60; *raw ≥ 0.7* = their formula and the dataset card's cut
  on the HTR line vs the minted slice):
  per file 121/142 (85.2 %) and 51/115 (44.3 %) —
  each image is a bifolium side, and `0002v-0001r` holds 2v and 1r, the end
  and the start of the passage, which one monotone alignment cannot both
  place; both files as one piece 108/257 and 173/257 by order;
  **per region (each zone its own piece) 194/257 (75.5 %), 179 at
  raw ≥ 0.7 (69.6 %)** against their 230 (89.5 %) with no gate and
  212 at ≥ 0.7.
- **Line by line, per region vs theirs:** both same 170 (66.1 %),
  both different 20, this project only 4, theirs only 40, neither 23.
  By zone: MainZone 131/184 same, 27 theirs only; MarginTextZone
  39/64 same, 13 theirs only; the 6 library-stamp lines and the page
  numbers are *neither* on both sides. On the 20 lines both aligned
  differently, the HTR reading of the strip is closer to this project's slice
  on 9 and to their window on 11: the usual shape is a slice running on past
  a window where the HTR reads more words (`Brentius in prolegomenis contra
  Petrum` vs `… contra`), or a window reaching into the next line.
- **Why the 40 *theirs only* lines (22 of them with their score ≥ 0.9).** The
  edition text interleaves the marginal notes at their textual position
  (`Am Rande:` blocks of several hundred characters) and passages the page
  puts elsewhere, so a main zone's monotone alignment meets long edition-only
  insertions: the exact DP prefers to mis-match the lines that follow (file
  B's main zone, lines 2–8 `Tutius est statuere…` and 55–65, placed on the
  margin text at confidence 0.2–0.4), or the insertions land on a line and
  sink it (file A, lines 79–82) or trip the burst guard (line 108, 63 inserted
  characters). Forcing the anchor-guided path for every size gives 191, the
  same block lost. Their Passim windows are order-free and immune. **This is
  the same mechanism C2b saw in the mint** (additions rendered inline, the
  edition's order against the page's), now measured on their example: a
  monotone aligner needs the marginalia separated from the main text before
  alignment (Denisa's apparatus-reinsertion script, or the edition's own
  markup), or an order-free fallback for the lines it declines.
- **What it does not prove.** Agreement is not correctness: both aligners read
  the same edition text and can share a mistake; a line both decline is not
  thereby wrong; the HTR witness is a noisy reader. The example is one
  heavily revised draft (LH I 3,4, a Konzept with marginalia); Task 2 measures
  the same question on 735 pages.
- **Task 2, built and tested, not yet run** (`align/philiumm/vi4.py`, `leibniz
  align philiumm-vi4 fetch | match | compare | sheet`; +5 tests, 621). The
  Hub lists 1,010 PAGE files (735 noisy, 248 clean, 27 val; revision
  `b53f531c…`, licence `cc-by-4.0` as listed): 999 names read as shelfmark +
  folio (`LH_1_12_2_0124r`), 483 of them openings, 8 are eScriptorium ids
  with no shelfmark, 3 lack a side letter. *match* finds the work by the
  shelfmark's signature keys (the store spells `LH 1, 3, 7 A` and `LH 1, 3,
  7a`; both tried, letter parts joined or split), the page by the C2
  resolver's folio index, and pairs lines by bounding-box IoU ≥ 0.5 (0.3 and
  0.7 reported), greedy and one to one; an opening is laid out as two canvases
  side by side in whichever order pairs more area, or as one scan when both
  labels point at the same file; `reports/philiumm/heldout_pages.csv` gets
  every resolved page of every split for C3. *compare* buckets each paired
  line (agree ≥ 0.9, near 0.7–0.9, disagree, ours only, theirs only, neither)
  per stratum, zone and file, with the HTR witness on the disagreements;
  *sheet* writes `data/philiumm/philiumm-disagreements.html` through the C2
  crop machinery, which now takes explicit refs and shows PHILIUMM's text
  under the minted one (`audit.lines_for_refs`, `write_sheet`; the sampled
  sheet unchanged). The dataset constant and the site's attribution follow
  the Hub's rename to `DenisaBumba/…`. Expect, from Task 1: disagreements
  concentrated on pages with margin zones; `no_layout` where their image
  is not the GWLB derivative at a uniform scale — the report counts both.
- **Task 2, run on the store (2026-10-08, `reports/philiumm/vi4-crosscheck.md`,
  `vi4-summary.json`, `vi4-match-summary.json`, `heldout_pages.csv`).** Of the
  1,010 files, 735 noisy matched with lines paired and
  233 clean + 23 val resolved to pages; 19 did not: 8 eScriptorium
  ids with no shelfmark in the name, and 11 folios of LH 35, 1, 1 whose work
  (`00067960`) carries no folio label on any of its 54 pages — the same class
  the C2 resolver cannot localize. **1,149 distinct pages are held out for C3.**
  On the matched noisy files 93,021 of their lines met 62,114 of this project's
  at bounding-box IoU ≥ 0.5 (68,351 at 0.3, 54,492 at 0.7); 419 openings
  were the sheet scan the store registers under both folio labels, paired
  against the registration that carries the minted lines.
- **The paired lines, judged** (62,114): agree 9,307 (15.0 %) · near 2,886 ·
  disagree 771 · this project only 5,145 · theirs only 21,949 ·
  neither 22,056. This project minted text on 18,109 of the paired lines
  (29.2 %), theirs on 34,913 (56.2 %); where both have text
  (12,964), they agree at ≥ 0.9 on 71.8 % and differ at < 0.7 on 5.9 %.
  Every minted pair is heavy revision bar 112: these are drafts, held to the 0.72
  threshold, against a run with no per-line gate. On the 771 *disagree* lines the
  HTR reading is closer to this project's text on 383 and to theirs on 381
  (near: 1159 / 1682): a coin toss, as two sound aligners on one edition should
  give; the sample shows mostly line-start and line-end slips of a word (their
  whole-word window against this project's slice), the audit's boundary pattern.
- **Where the gap is.** 161 of the 731 judged files carry no minted line at all;
  their text covers 7,838 paired lines there — coverage (pieces the factory did
  not localize, had no edition text for, or declined whole), not alignment.
  On the 570 files with some mint: theirs only 14,111 against this project
  only 5,145. By zone: main zones, this project 17,513 lines with text to
  their 29,957; **margin zones 596 to 4,954** — the marginalia the monotone
  aligner cannot place (Task 1's finding, at scale). What agreement does not
  prove: both read the same edition; a shared reading is the edition's, not
  the page's. The sheet (`data/philiumm/philiumm-disagreements.html`, 300
  lines, both texts, verdicts in the C2 CSV shape) is the second thing to
  offer the PHILIUMM team.

### C2b — the audit closed and read (2026-10-07) ✅ score · ✅ patterns · ✅ hyphen fix · ⏳ reach census (operator's run)

- **What arrived.** `reports/gt-audit/gt-audit-verdicts-philiumm.csv`: the
  sheet of 2026-09-16 (`audit-sheet --seed 0`, 50 lines per stratum) judged
  by the PHILIUMM team — 136 correct · 33 boundary · 16 wrong · 14
  unreadable · 1 blank ("we cannot decipher"); 86 notes in English, with
  corrections in quotes. Their own summary, in substance: they marked
  *correct* when the alignment was right and the issues minor; the
  line-end hyphen is very often missing on words cut at the line end;
  *boundary* was used for a letter missing at the start or added at the
  end; sections with mathematical expressions are generally wrong, as in
  their own HTR; additions appear inline because the edition renders the
  final state; overall the alignments are very good.
- **Score** (`audit-score`, `reports/gt-audit.md`). Precision = correct ÷
  (correct + boundary + wrong): fair_copy 42/50 = 84.0 % (Wilson 71–92),
  light_revision 39/45 = 86.7 % (74–94), heavy_revision 31/48 = 64.6 %
  (50–77), scrap 24/42 = 57.1 % (42–71); pooled 136/185 = 73.5 %;
  **corpus-weighted 72.3 %, FAIL at ≥ 95 %**, every stratum below the gate.
  *Usable* (boundary included): 88.0 / 97.8 / 89.6 / 90.5 %, **weighted
  92.2 %**. Weights are the C2 mint's stratum counts (9,913 · 96,175 ·
  190,162 · 1,174), passed on the command line because this session had no
  store; the report names the source. The second witness now skips strips
  under four folded characters (the 14 unreadables are mostly one letter)
  and lists 9 verdicts, all *wrong* lines whose HTR reading agrees with the
  minted text at 0.82–0.98: the right line, read differently.
- **Agreement with the operator's preliminary pass** (20 lines, fair copies):
  11/20. PHILIUMM calls *correct* four lines the operator called *wrong*
  (all four were on the 2026-09-16 re-check list) and three the operator
  could not read; they call *wrong* two the operator passed (*Casal* /
  *Casai*; a capital and an accent).
- **Patterns** (`align/audit_patterns.py`, rules and precedence in its
  docstring and in the report; per-line CSV
  `gt-audit-verdicts-philiumm-patterns.csv`; 3 lines settled by hand in
  `gt-audit-pattern-overrides.csv`). Over the 199 judged lines: correct
  102 · boundary-letter 35 · normalization 16 · unreadable 14 · hyphen 13 ·
  bracket 7 · math 5 · reading 4 · addition 2 · other 1. By verdict: the 16
  *wrong* are math 5, reading 3, normalization 3, addition 2, bracket 2,
  **other 1 — the one misaligned line** (`DE-611-HS-959288:0086:029`,
  minted *érité*, strip *serviteur*). The 136 *correct* carry 13 hyphen, 13
  normalization, 4 boundary-letter, 3 bracket, 1 reading notes: the
  auditors' "corrected in the comment but assigned correct". The prompt
  named seven patterns; *bracket*, *normalization* and *reading* were
  added because without them fifteen of the sixteen *wrong* verdicts
  would read *other*, and none of those fifteen is a wrong line.
- **Hyphens.** 14 lines carry the signal; 6 have an HTR line ending in a
  hyphen mark (what the fix restores), 8 a note saying the hyphen is on the
  page while the HTR read none. The mint's stored text is stripped, so the
  census can see only the first kind; the second is a C3 question (the
  re-mint cannot invent a mark the HTR did not read).
- **Corrections** (`gt-audit-verdicts-philiumm-corrections.csv`): 46 notes
  spell out an edit, 45 placed in the minted text. Mean character distance
  minted → corrected, as written / under the aligner's fold: all 9.4 / 7.9 %;
  boundary-letter 8.6 / 7.9 %; **normalization 3.1 / 0.0 %**; reading
  3.3 / 3.4 %; bracket 8.0 / 6.3 %; the addition 32.1 / 32.7 %. Word-level
  corrections, so floors.
- **The fix** (`align/align.py`): `keep_hyphen=True` by default; the
  earlier line's slice ends with the HTR line's own mark when the cut falls
  inside a word; `AlignedLine.kept_hyphen` records it; a dash the
  projection leaves at a word boundary stays dropped. Off, the slices are
  byte-identical to the C2 mint's (tested). The B2 harness takes the knob
  through `EvalConfig` and gives the same numbers either way: its grade
  folds punctuation away. **Not applied to the store**: the re-mint runs
  once, before C3 (Next).
- **Reach census** (`align/audit_reach.py`, `leibniz align audit-reach`):
  per open-bucket minted line — hyphen (HTR mark + minted letter), math
  (the audit's density cut, which misses inline algebra in prose: `ia yy x
  2ax —` is 4 %), addition (a proxy: the page's overlap or short-line
  fraction at the heavy-revision cut), eigh. (the record's Textart),
  Marginalien (the work's set), bracket, LH 35. Writes
  `reports/gt-audit/reach.md`, `reach-summary.json` and
  `data/gt/flags.jsonl` for C3; opens the store `mode=ro` + `query_only`.
  Built and tested on a seeded store in the cloud session; run by the
  operator on the master store on 2026-10-08 (minutes; the local
  `audit-score` against the store reproduced 72.3 %).
- **Reach, measured (2026-10-08, `reports/gt-audit/reach.md`).** 297,424
  open-bucket lines on 16,843 pages from 5,526 records (5,513 with a
  Textart; 0 rows skipped). *Hyphen* 7,822 (2.6 %): fair_copy 7.7 % ·
  light 4.0 % · heavy 1.7 % · scrap 2.0 %; by volume up to 6.5 % (IV,1)
  and 7.3 % (VI,1); the sheet's mechanical rate was 6/199 = 3 %, so the
  mint-wide figure is as expected and is the exact set the re-mint
  changes. *Bracket* 4,338 (1.5 %; IV,3 4.3 %, VI,3 2.4 %): C3 should
  drop or clean them (the flag is in `flags.jsonl`). *Math* 249 (0.1 %):
  III,1 72 (1.3 %) · III,3 55 · III,4 39 — two thirds in Reihe III, as a
  precise-but-blind cut should; the sheet's rate from the notes was 2.5 %,
  so the flag is a floor and the layout-zone census (P1 Task 3) is the
  instrument. *Addition* 246,003 (82.7 %; heavy 99.3 %, light 58.2 %,
  fair 2.0 %): the page-layout proxy restates the stratum heuristic and
  must not be used as a filter — the audit found inline additions on 1 %
  of lines; the honest route is Denisa's apparatus-reinsertion script.
  *Marginalien* 0, *LH 35* 9,145 (3.1 %; III,1 57 %).
- **The hand census (2026-10-08).** Of the 296,587 minted lines whose
  record has a Textart, **118,928 (40.1 %) are in their author's own hand
  (`eigh.`) and 76,147 (25.7 %) in Leibniz's** (own hand, and the record
  names no sender or Leibniz as sender). By stratum, Leibniz's hand:
  fair_copy 1.7 % · light_revision 8.3 % · heavy_revision 35.8 % · scrap
  18.2 %. By volume: IV,2 98 %, VI,4 65 %, VI,6 55 %, III,1 46 %, I,7
  36 %, IV,1 35 %, I,3 29 %, I,12 28 %; IV,3 6 %, VI,3 10 %, III,3 4 %.
  The gap between the two figures is the correspondents' own hands on
  letters he received, largest in Reihe I (I,3: 82 % own hand, 29 %
  Leibniz's). For the call: three quarters of this ground truth is hands
  other than Leibniz's — David's point that their model saw only his.
- **Tooling:** `audit-score --weights/--weights-source` (no store needed;
  refuses to create an empty store when `--db` is missing), `--compare`
  (+ `--compare-labels`), `--patterns/--no-patterns`, `--overrides`,
  `--patterns-out`, `--corrections-out`; `audit-reach`. +33 tests (606).
- **C3 amendment 2** in PROMPTS.md (six points); the C2b prompt appended
  under "Follow-up phases (2026-10)".

### W3 fix — the viewer's modules as one versioned set (2026-10-06) ✅

- **The fault, live.** W3 was deployed and passed its checks. Minutes later
  the operator opened `/browse` in the browser they had used all day: the nav
  read "Search | nav.browse | About", the tab "browse.heading — Leibniz
  Legible", the page "Something went wrong: api.works is not a function". A
  hard reload cleared it.
- **Cause.** `deploy/Caddyfile` sends `Cache-Control: public, max-age=3600`
  on `/static/*`. The shell (`no-cache`) named `app.js?v=<hash>`, so the new
  `app.js` was fetched at once, and with it `views/browse.js`, which no
  browser had yet. But `app.js` imports `./i18n.js`, `./dom.js`, `../api.js`
  by plain address, and those came from the cache of an hour or less before:
  an `i18n.js` without the `nav.browse` and `browse.*` strings (so `t()` gave
  the keys back) and an `api.js` without `works()`. The live server itself
  sent the right files throughout.
- **Why the checks missed it.** Every browser check, the 60 on the desktop
  and the 60 on the live site, began with an empty profile, and a fresh
  browser has no old module to pair with the new `app.js`. W1 had recorded
  the imported modules as "not versioned" and expected a lag of up to an
  hour; the hand-over repeated that. The truth was a mix of new and old code.
- **The fix** (`web/api.py`). The modules are versioned as a set, not one by
  one: `_modules_build` hashes every `.js` file outside `vendor/` (names and
  contents, 12 hex digits), the shell loads `/static/m/<build>/app.js`, and
  because every import in the viewer is relative, `./i18n.js` and
  `../api.js` resolve under the same prefix. The app mounts the static
  directory a second time at `/static/m/{build}`, before `/static`; any build
  answers with the current files (a shell from just before a restart still
  gets one consistent set), and the plain addresses still answer (a tab
  opened before a deploy). `style.css` and `boot.js` keep their `?v=`. No
  JavaScript changed.
- **Reproduced, then healed.** A proxy that adds the Caddyfile's header to
  `/static/*` (Playwright's own request routing switches the browser cache
  off, so it cannot stand in for one), the app restarted behind it from one
  tree after another, and one browser context across them. Main before W3
  (`30d0849`) → W3 as deployed (`8d54354`): the operator's three symptoms,
  word for word. The same browser → the fix: healthy, every module from one
  build path. → the fix with only `i18n.js` changed, `app.js` untouched: the
  new label at once, under a new build path. A reader away during W3 (before
  W3 → the fix): healthy. Control: a fresh browser on W3 is healthy.
- **Verified.** 570 tests (+1; 571 with the link wording below), ruff clean: the shell names one module build
  on every route; every module is served under it and imports only by
  relative path (the invariant the prefix rests on); the build moves when an
  imported module changes — the fault's shape — and stays put for the
  stylesheet or a vendored script. On the corpus store every view (search,
  browse, about, work, a page with its 84 lines, not found) loads its ten
  modules from one build path, the language carries from view to view (one
  `i18n.js`, not two copies), and the 60 browse checks pass unchanged.
- **For every later deploy.** Check as a returning reader too: open the site,
  deploy, reload in the same browser without a hard reload.
- **Also on this branch: a record's link, in words.** The operator, looking
  round the new index, opened LH 40 (`/work/00068539`): each of its 19
  catalogue records ended "Link: gwlb_link, confidence 1.00", which read
  like an unfilled placeholder. It was the crosswalk's `match_method` put
  into the sentence as it is stored (so since Phase D, `ede16e1`; not new
  with W3). The store holds two methods,
  `gwlb_link` (17,557 links, the catalogue record's own link to the scan)
  and `shelfmark` (89, matched by normalised shelfmark). `views/work.js` now
  words each (`work.katalog.match.<method>`, EN and DE: "The catalogue
  record itself links to this scan · confidence 1.00", "Linked by matching
  shelfmarks · confidence 0.70"; "by hand" is ready for a manual link), and
  a method without words still shows by name rather than vanish. The API
  keeps `match_method` as it is. A test ties the words to the methods
  `catalog/crosswalk.py` writes (571 tests); checked in Chromium on LH 40,
  on a work linked both ways (`00068032`), in German, and with a made-up
  method. **Not changed, seen beside it:** a skipped page shows its reason
  as stored ("skipped (no_lines)" on the work page, "Reason: no_lines" on
  the page view); wording those wants the list of reasons from the store.
- **Also on this branch: sender and addressee instead of "Correspondent".**
  The same section had one row, "Correspondent", holding the record's
  `absender` as scraped, link text included — so every letter *from*
  Leibniz read "Correspondent: Leibniz (GND)" (since Phase D as well). Over
  the 17,646 linked records the cells are regular: 29,672 single names, 220
  cells naming two people run together ("Bossuet (KorrespDB) (GND)Pirot
  (KorrespDB) (GND)"), 133 lone "?", a few "Leibniz (GND)?" and "Ilgen ?",
  two ending "u.a."; 2,618 records name nobody. `browse.names_as_written`
  reads a cell for showing rather than counting: link texts gone, people
  apart, `Surname,Initials` spaced, and the catalogue's doubt kept ("Leibniz
  ?", "?", "u.a."). `/api/works/{id}` records now carry `sender` and
  `addressee` (lists) beside `correspondent`, which now means what it says —
  the people beside Leibniz ("Hansen" on a letter either way, "Brosseau;
  Cordemann" on a third-party letter, `null` where nobody is named) — and
  the work page shows two rows, *Sender* / *Addressee* (DE *Absender* /
  *Adressat*, the catalogue's own column names), only where the record
  names someone. Checked in Chromium on LH 40 (8 of 19 records name people:
  "Leibniz" → "Danckelmann, E.", the two electors, Strattmann), on LBr. 501
  (197 records; "Crafft, J.D.; Leibniz" from one cell) and on LBr. F 20 (14
  letters from "?" to the landgrave, 4 from "?" to "?"), in German, axe 0
  violations; 573 tests. `llms.txt` names the two fields.
- **Docs.** `deploy/README.md` §9, README, and the comment in
  `deploy/Caddyfile` (the live Caddyfile is edited by hand and keeps its old
  comment; nothing needs doing on the box).

### W3 — the browse index: shelfmark family → section → convolute (2026-10-06) ✅

From the same reader at the Leibniz-Edition as W1: an index of the shelfmark
groups, to get from a group's name to the shelfmark and its folios. The work
pages already list the folios; the levels above them were missing.

- **What is there.** `/browse` (nav: *Browse* / *Signaturen*): four headed
  families, each section a `<details>` with its counts — *Handschriften (LH)*
  750 works in 30 sections, *Briefwechsel (LBr)* 1,060, *Marginalien* 370,
  *Other* 45 in four sets (Leibnitiana 12, the reconstructions 2, and the 5
  manuscript-set and 26 Marginalien-set works without a usable shelfmark).
  A filter box narrows by shelfmark, name or title as you type (accent-blind;
  a query starts at a word, and ends at one once a separator is typed: `LH 3,`
  is section 3, `LH 3` still finds LH 35); the letters switch between name and
  number order; every entry links `/work/{id}` and shows its page count and a
  **K** where catalogue records are linked. Sections carry stable anchors
  (`#lh-35`, `#lbr`, `#marg`, `#other-leibnitiana`); a work page opens with
  "Browse › LH 35 · Mathematik" pointing at its anchor, and the index opens
  and focuses the section a `#fragment` names. The search view's start and
  no-result states link to the index. EN and DE; the family and section
  names are the archive's own German words in both.
- **Server side.** `_ssr_browse` renders the whole index into the shell (every
  family and section, a link per work, `<details>` so it works without
  JavaScript), stamped once per process; `/browse` is in `INDEX_ROUTES`, the
  sitemap and `llms.txt`; the work page's server-rendered summary carries the
  same breadcrumb. `GET /api/works` (no id): `works`, a compact row per work
  (`work_id`, `set`, `title`, `shelfmark`, `shelfmarks`, `family`, `section`,
  `section_label`, `label`, `n_canvases`, `has_katalog`), and `groups`, the
  tree (family → section with `anchor`, `title`, counts and the work ids of
  its `entries` in order; the letters also `by_number`), under `DAY_CACHE`,
  built on first use and held for the life of the process, with `?set=` and
  `?family=`. `/api/works/{id}` gained `browse` (the work's section).
  `robots.txt` gained `Allow: /api/works`: the old rule covered only
  `/api/works/`, and `Disallow: /api/` caught the bare path.
- **The grouping rules** (`web/browse.py`: pure functions over the `works`
  rows, one grouped query of sender/addressee pairs per letter convolute —
  `CORRESPONDENTS_SQL` — and the ids of the works with records; about 50 ms
  for the corpus).
  - *Family* is that of the first shelfmark with a recognised label, whatever
    the OAI set; the two small sets are never spread over the series; they,
    and every work without a usable LH/LBr/Marg shelfmark, go to *Other*, one
    section per set, by shelfmark string.
  - *LH*: the section is the first part as a number (Roman numerals read).
    Its label is the phrase the library's titles give it ("Leibniz-Handschriften
    zur *Mathematik* LH 35, …"; "zur/zu/zum" dropped, the catalogue's slips
    tolerated) where more than half of the section's titles agree, else
    `LH <n>`; an entry whose own phrase differs carries it. In 28 sections
    the titles name one phrase and no other; LH 37 and LH 42 get none (their
    titles name sub-groups: "LH 37, 1 · Akustik", "LH 42, 4, 1 ·
    Aufzeichnungen zur Rechenmaschine").
  - *LBr*: one section. Per convolute the names beside Leibniz in the linked
    records' sender and addressee cells are counted per record (source tags
    `(KorrespDB)`, `(GND)` stripped, cells naming several people split,
    `Surname,Initials` spaced, doubt marks dropped, a bare surname counted
    with its one fuller form), else the *X* of a record titled "X an Leibniz"
    / "Leibniz an X", else nothing. Then the order check below decides which
    name, if any, is shown; without one the label is the bare shelfmark.
    Two orders: by name (accent-blind; the unnamed last, by number, under a
    line that says so) and by number (the F series after the plain numbers).
  - *Marg*: one section by number; the title cut at a word near 120
    characters, the whole title in the `title` attribute.
  - *Order* is natural (2 before 10, numbers before letters) and read from
    the shelfmark as written.
- **Why the letters are checked against their numbers.** The store holds the
  catalogue records of the §70 volumes only, so a convolute's linked records
  are often a handful of third-party letters, and "the most frequent name"
  is then wrong with full confidence: LBr. 57 (Johann Bernoulli) → "Mencke,
  O.", LBr. 16 (Arnauld) → the landgrave who forwarded his letters, LBr. 389
  (Helmont) → "Motzfeld" on twenty records. The LBr numbers run
  alphabetically by correspondent (Bodemann, 1889; the labels themselves show
  it: 2 Abercromby … 1028 Zunner), so `names_in_order` keeps the longest run
  of names that stays alphabetical down the numbers (a weighted longest
  non-decreasing chain; more records, then the earlier mention, break ties).
  A name may be filed under any word of it (Ursinus v.Bär under B,
  DesVignoles under V, "gen. Schütz" under Sch), with J read as I as the
  numbering interfiles them, and an umlaut as its vowel or spelled out. A
  convolute's lesser name wins where its most frequent one is out of place;
  a most frequent name outside the run is still shown when ten or more
  records carry it and its initial fits between its neighbours' (C and K as
  one) — the catalogue spells some names otherwise than the shelf does.
  **Measured on the corpus:** of the 1,025 numbered convolutes 713 have name
  candidates; 634 keep their most frequent name (two of them by that last
  rule: Chuno, LBr. 185, and Crafft, LBr. 501), 21 take a lesser name that
  fits (Addison, Arnauld, Berckelmann, Bernoulli, Drevet, Helmont, Kraus,
  Mocenigo, Schott, Spinoza …), 58 stay unnamed. The F series (princes, by
  house and first name) has no single order: it keeps its most frequent name,
  and a name that would label two F convolutes stays with the one that has
  more records (25 of 35 named, 2 withheld). In all **680 of 1,060 (64.2 %)**
  carry a name; 744 (70.2 %) have records; 4 have records that name nobody.
  What the check cannot see: a wrong name that happens to fit alphabetically.
- **Shapes in the live rows that the prompt's rules did not cover.**
  (1) `LBr. 726` is filed in the manuscripts' set: placed with the letters,
  and the correspondents query takes `OR w.shelfmarks LIKE '%LBr%'` so it
  gets its name (Philipp, Chr.). (2) `L Br. 827`, the label spelled apart,
  parses to no family: repaired in `browse.py` only, placed with the letters.
  (3) The normaliser reads a lone C, D, I, L, M, V or X as a Roman numeral,
  right for `LH XXXV, I, 17` and wrong for the part letters of `LH 1, 3, 7 C`
  (it would sort I, L, C, D, M before A): order comes from the shelfmark as
  written, and a letter is a numeral only where the section itself is
  written in Roman. (4) 35 manuscripts carry a second shelfmark, a variant
  or a slip of the first (`LH 1, 3, 7 A` / `LH 1, 3, 7a`, `Lh 35, 4, 14`,
  `LH35, 7, 3`, `LHH 41, 7c`); the first one places them.
  (5) Sender and addressee cells run several people together without a
  separator ("Brand,H. (KorrespDB) (GND)Leibniz (GND)"), carry qualifiers in
  parentheses that belong to the name ("Leopold I. (Kaiser)"), `?` for an
  unknown, or are empty. (6) The one live candidate for the
  title fallback is "Leibniz an -- (?)"; a name without a letter is refused,
  so the fallback names no convolute today. (7) Five Leibnitiana works carry
  LH shelfmarks (`LH XLII,5`, `LH XXXV, I, 17, Bl. 1 - 17`): they stay in
  their own group as asked, and the filter finds them by shelfmark. (8) Five
  works of the manuscripts' set have no LH shelfmark (four "Handschriftenbestand
  Ms", `Ms IV, 471 : A-F` …, one without any), and 26 of the Marginalien set
  have none or a foreign one (22 of them with no page images): *Other*.
  (9) Section labels are verbatim: LH 11 reads "Allgemeinen Geschichte" (the
  dative of "zur Allgemeinen Geschichte"), LH 9 "Archälogie" and LH 15
  "Würtemberg" (the library's spellings). (10) 27 works have no page images
  and are listed with "0 pages".
- **The three live fixtures** (`tests/fixtures/works_live.json`,
  `lbr_correspondents_live.json`, `crosswalk_works_live.json`; 2,225, 2,244
  and 1,197 rows, 0.9 MB of CC0 and CC BY metadata), exported read-only
  (`mode=ro`) from the corpus store on 2026-10-06: the works table
  (`gwlb_object_id, set_name, title, shelfmarks, n_canvases`, by id),
  `browse.CORRESPONDENTS_SQL`, and `SELECT DISTINCT work_id FROM crosswalk`,
  one JSON object per line. `tests/test_web_browse.py` runs the tree over
  them (every work in exactly one entry, the sections, the family counts, the
  share, eleven convolutes by name) beside synthetic tests of every rule.
- **Verified.** 569 tests (+24), ruff clean. Against the corpus store,
  opened read-only by `leibniz serve --backend none --port 8765` (the store's
  size and date unchanged afterwards): `/api/works` 0.64 s on the first call
  and 2 ms after it, 781 KB (84 KB gzipped), 2,225 rows, every work once in
  the tree; `/browse` 187 KB of HTML (43 KB gzipped) with 2,225 distinct
  `/work/` links under 36 anchors; robots, sitemap (2,229 URLs) and llms.txt
  carry the new lines; search answers 503 by design. Then 60 checks in
  Chromium (Playwright): the tree, the filter (shelfmark, name, title,
  accents, the word boundary, no match, clearing), both orders of the letters
  and the note between named and unnamed, keyboard reach and a visible focus
  ring, an entry to its work page, the breadcrumb back to its opened and
  focused section (in-app and on a full load), EN and DE with the open
  sections kept across the switch, the search view's link, 390 px without
  horizontal scroll (sections open, filtering, the work page), the index
  with JavaScript off, no console errors and no failed request; axe-core 0
  violations in seven states. The first axe run found one violation that
  predates this phase, on every view: the EN/DE buttons' spoken names
  ("English") did not contain their visible labels — now "EN: English",
  "DE: German" (WCAG 2.5.3).
- **Where it ran** (see Divergences). Inside WSL2, on the checkout the corpus
  runs used, from a session started in Windows; a separate environment
  `.venv-w3` (`UV_PROJECT_ENVIRONMENT`, `UV_FROZEN`) so the pipeline's `.venv`
  was never synced; `.gitignore` has `.venv-*/`. **Suite on Windows:** not
  run — nothing here executes on the Windows side but the browser; the
  suite's clean bill is the WSL one above. Opening the WAL-mode store
  read-only leaves an empty `inventory.sqlite-wal` and a 32 KB `-shm` beside
  it (as `leibniz serve` always has); they are not a write to the store.
- **Known limits.** A correspondent's name exists only where catalogue
  records are linked and agree with the shelf order: 380 convolutes are
  unnamed (316 without records, 4 whose records name nobody, 60 withheld). A
  full Arbeitskatalog export from TELOTA would complete them, and the labels
  then fill in by re-running the catalogue crosswalk on the desktop and
  copying the store, with no code change. Names are the catalogue's short
  forms ("Bernoulli, Joh."). The twelve LH sections without a digitized unit
  (14, 16–18, 22, 26, 28–33) do not appear. `/api/works` may be cached for a
  day. (The hour for which browsers kept the imported ES modules turned out
  to be a fault, not a limit: see the W3 fix above.)
- **Follow-ups seen.** A reviewed table of the 42 LH section names (Open
  questions #22); full names for the correspondents (the records' titles
  have them: "Leibniz an Heinrich Oldenburg"); the same breadcrumb on the
  page view; cross-listing the Leibnitiana pieces that carry LH shelfmarks;
  `L Br.` and the lone-letter Roman reading in `catalog/shelfmarks.py` itself
  (left alone here: it is the crosswalk's key).

### W2 — "quoted phrases" and -exclusions in search (2026-10-02) ✅

- **Why they did nothing.** `search/normalize.py` folded the whole query with
  the aligner's recipe (punctuation → space) before either backend saw it, so
  quotation marks and minus signs vanished and `AND`/`OR` became words. Live
  (Meilisearch): `deus` 10,450 hits, `deus mundus` 97,633, and `"deus mundus"`,
  `deus -mundus`, `deus AND mundus` 97,633 as well (the top hits of the last
  marked English *and*). On FTS5, `deus -mundus` returned exactly the pages
  with *mundus* and `deus OR mundus` only pages that also hold the word *or*.
  No decision against operators anywhere: the search layer was written once in
  Phase D (`ede16e1`) and touched since only by deploy fixes, `matchingStrategy`
  never appears, the UI said "a word or a phrase" from day one, and `llms.txt`
  (2026-09-23) described the behaviour. `NOTES.md` A.5 ("exact-match search
  degrades from ~5% … WER predicts search behaviour (ours 27%)") is why the
  operators are opt-in and the hint warns.
- **The parser** (`normalize.parse_query` → `ParsedQuery(words, phrases,
  excluded)`) reads the raw query before folding. A quotation mark (`"` „ “ ” ‟
  « », not single quotes: ’ is the French apostrophe) opens a phrase and the
  next closes it; an unclosed one runs to the end. A `-` excludes only where it
  starts a word or a phrase, so *Braunschweig-Lüneburg* and a free-standing
  dash read as before (`-Braunschweig-Lüneburg` excludes that run). Each word
  and phrase is folded on its own (*„Vt sit“* is the phrase *ut sit*),
  de-duplicated, 12 clauses as before with exclusions and phrases first. A
  query with neither operator parses to the old `query_terms` exactly
  (asserted against the old reader over the bench's fifty queries and 2,000
  random ones). Exclusions alone search nothing.
- **FTS5** (`match_query`): phrases as FTS5 phrases (exact, no prefix), the
  words as before, then `(…) NOT ("a" OR "b c")`. Every token is still quoted,
  so typed text never reaches FTS5 as syntax (a 3,000-query hostile fuzz is in
  the suite; FTS5's `NOT` is binary, hence no exclusion-only MATCH).
- **Meilisearch** (`meili_query`): its native `"…"` and `-` (≥ 1.8; pinned
  1.53.2), sent as exclusions, phrases, then the words exactly as before. The
  order is load-bearing, measured on the real binary: Meilisearch reads only
  the first ten terms (a phrase or an exclusion is one; an exclusion after the
  tenth word was silently ignored) and matches the last word as a prefix
  (`calcul -mundus` found nothing, `-mundus calcul` found *calculemus*).
  Phrases stay mandatory under the default `matchingStrategy: last` and
  exclusions always apply; quoted and excluded words are exact, no typos and no
  prefix (`"deus mundos"` finds nothing against *deus mundus*; `-deus` keeps
  pages with *des*).
- **Snippets** mark a phrase as one run in the original text (`<mark>Calculemus,
  inquit</mark>`), a quoted word only exactly, an excluded word never.
- **Copy**: `search.hint` EN/DE and the static `index.html` (the operators, and
  that exact matching misses misread words); `search.empty.hint` adds "or no
  quotes" / "oder ohne Anführungszeichen"; `llms.txt`, the `q` description in
  `/openapi.json`, README.
- **Verified**: 545 tests (+9), ruff clean. Against the real Meilisearch 1.53.2
  through `MeiliBackend`, on a synthetic 80-page early-modern corpus (u/v, ſ,
  capitals, punctuation, line breaks): 360 phrase and phrase+exclusion queries
  return the same pages as FTS5 and as the folded text (0 mismatches); 120
  word+exclusion checks remove exactly the pages holding the excluded word, in
  both backends; a phrase across a line break is found by both; 3,000 hostile
  queries, 0 errors. Server-side p95 on a 30,000-document Zipf index: one word
  11 ms, a phrase of two common words 5 ms, word −common word 6 ms, phrase −word
  + two words 21 ms. The app served over the seeded store with each backend and
  driven in headless Chromium (typed queries, the language switch): phrases,
  „German quotes“, word order, `-word`, `-"phrase"`, `-de` alone (no hits, no
  error), both hints in EN and DE; no console errors but the sandbox's blocked
  GWLB thumbnails.
- **Known gap, Meilisearch only** (Open questions #21): the live index keeps
  titles, shelfmarks, AA references and folio labels as written — only the page
  text is folded — and there a comma or full stop breaks a phrase and *V*/*J*
  do not fold, so a quoted `"LH XXXV, 3, 5"` or `"AA VI,4 N. 109"` finds
  nothing where FTS5, which folds those columns, finds the work. The
  no-results hint says to drop the quotes.

### W1 — the overlay toggle, plain-text export, deploys visible at once (2026-10-02) ✅

From a reader's report (Leibniz-Edition): the overlay button did nothing, and
could each folio's transcription be exported?

- **The toggle, root cause.** `views/page.js` attaches the line SVG with
  `viewer.addOverlay`; OpenSeadragon 5.0.1's `Overlay.drawHTML` sets
  `element.style.display = "block"` on every redraw, and that inline style
  beat `.line-overlay.is-hidden { display: none }`. Reproduced on the live
  site (`/page/00068221:0043`, headless Chromium): after a click
  `aria-pressed="false"` and the class were set, computed `display` stayed
  `block`, the polygon's `getBoundingClientRect()` stayed 16×9 px. A second
  trap the trial of `visibility: hidden` alone exposed: the polygons carry
  `pointer-events: all`, which ignores visibility, so an invisible line still
  took the click (`elementFromPoint` at its centre returned the polygon).
- **The fix.** `style.css` hides with `visibility: hidden` and sets the hidden
  polygons' `pointer-events: none` (page.js also drops a gesture that starts
  on a hidden overlay); a line chosen in the panel still zooms the image and
  keeps its polygon's highlight for when the overlay returns. The label says
  what pressing does — "Hide line overlay" / "Show line overlay", DE
  "Zeilenraster ausblenden" / "einblenden" (`page.overlay.hide|show`; the old
  `page.overlay.toggle` key is gone) — and `aria-pressed` keeps the state, as
  asked. (The ARIA practices prefer a toggle whose label never changes; if a
  screen-reader user finds "Hide line overlay, pressed" confusing, drop
  `aria-pressed` and let the label carry the state.) The choice is remembered
  per browser in `localStorage['leibniz-legible.overlay']` (`shown`/`hidden`,
  absent = shown), every access in try/catch; with storage blocked it lasts
  for the tab.
- **Plain-text export.** `GET /api/pages/{page_id}/text` and `GET
  /api/works/{work_id}/text`, `text/plain; charset=utf-8` (`?format=tsv`:
  `text/tab-separated-values`, columns `line_id, line_seq, conf, status,
  text` under a header row), `Content-Disposition: attachment;
  filename="leibniz-legible_<id>.txt"` (the page id's colon as `_`, see
  Divergences), `CACHE_HEADERS`, 404 like the JSON routes, in the OpenAPI
  schema with summaries. Header lines start with `# `: project and URL, the
  page or work URL, title and shelfmark(s), folio and page id, the GWLB
  original, the source image URI, model · run · run date per recognition run
  behind the lines (a page partly re-read by a later run lists both, with
  line counts), line count and mean confidence, `attr.HONESTY`,
  `attr.TEXT_LICENCE`, `attr.WORDING_RULE`, and a line saying how the body is
  laid out. Then a blank line and the lines `latest_lines` gives, with text,
  exactly as `/api/pages` shows them (one helper, `_with_text`, now serves
  both; a line break inside a text becomes a space so one output line stays
  one line). The work export is a `StreamingResponse` over a generator: the
  header from the one `line_summaries_by_page` query, then per page in canvas
  order `## Folio <label> — <page_id>` (`## Canvas <n>` where no label is
  recorded), its source image and model as `# ` lines, its lines; a page
  without text is a one-line note (`# No recognised text on this page
  (skipped: no_lines).`). The generator opens its own read-only connection
  (`_open(..., any_thread=True)`: Starlette steps a sync body iterator on
  whatever worker thread is free) and closes it at the end or when the client
  goes away. Nested under `/api/pages/` and `/api/works/`, so `robots.txt`
  already admits them and the JSON routes are not shadowed (the `str`
  convertor never matches a slash). Links: "Download text" / "Text
  herunterladen" in the page header's link list, "Download the text of this
  work" / "Text dieses Werks herunterladen" in the work view's links (both
  only when there is text; `api.pageTextUrl` / `api.workTextUrl`), and the
  same links in `_ssr_page` / `_ssr_work`. Documented in `llms.txt` (machine
  access) and the README.
- **Deploys visible at once.** `create_app` rewrites the shell's
  `/static/style.css`, `/static/boot.js` and `/static/app.js` references to
  `?v=<first 12 hex of the file's SHA-256>`, computed once at startup (a
  restart picks up new files). **Not versioned: the ES modules `app.js`
  imports** (`views/*.js`, `i18n.js`, `api.js`, `dom.js`) — Caddy lets
  browsers cache `/static/*` for an hour, so a change to those can still lag
  up to an hour for a returning reader. For this deploy that means the CSS
  half of the overlay fix lands at once (the old page.js toggles the class,
  so hiding works) while the new labels and download links can take the
  hour. Doing better would mean the server stamping an import map, or
  versioned import specifiers — not done.
- **Runbook fix.** `deploy/README.md` §9's by-hand update ran
  `git -C /opt/leibniz-legible pull` as root, which git refuses in the
  leibniz-owned checkout ("dubious ownership" — the reason `install.sh` runs
  git and uv as the service user); it now does the same as `install.sh`.
- **Verified.** Tests +11 (536 with the `gt` and `release` extras; without
  `gt` the six Pillow tests error on import, as before this change), ruff
  clean. Headless Chromium against the live site (the bug reproduced; the new
  rule injected with `addStyleTag`: polygons `visibility: hidden` after a
  click and the hit test falls through to the canvas, `visible` again after
  the second), then 26 checks of the new viewer against the app on the
  fixture store (labels EN/DE, `aria-pressed`, the stored choice across
  in-app navigation and reload and with storage blocked, no selection through
  a hidden line, panel selection while hidden, both downloads and their file
  names, no link on a skipped page, versioned asset URLs, no console errors,
  no CSP violations) and axe-core: 0 violations (page with the overlay shown
  and hidden, EN and DE; work view).
- **Playwright recipe** (re-run after deploying). In a scratch directory:
  `npm init -y && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install playwright`.
  On the operator's machine `npx playwright install chromium` and plain
  `chromium.launch()`; in a Claude Code cloud container launch
  `executablePath: '/opt/pw-browsers/chromium'`, `proxy: { server:
  process.env.HTTPS_PROXY }`, and — not `ignoreHTTPSErrors` — pin the egress
  proxy's CA: `awk '/BEGIN CERTIFICATE/{n++} n{print > sprintf("c%03d.pem",
  n)}' /root/.ccr/ca-bundle.crt; for f in c*.pem; do openssl x509 -in $f
  -pubkey -noout | openssl pkey -pubin -outform der | openssl dgst -sha256
  -binary | base64; done | paste -sd,` → `args:
  ['--ignore-certificate-errors-spki-list=<that list>']`. Then: open
  `https://leibnizlegible.com/page/00068221:0043`, wait for
  `.line-overlay__poly`, click `#overlay-toggle`, read the polygon's computed
  `visibility` and the button's text. Today: `visible | Show line overlay`
  (the bug); after the deploy: `hidden | Show line overlay`, and a second
  click gives `visible | Hide line overlay`.

### D — a sibling app on the host: Calculemus, flagged off (2026-09-27) ✅

The game Calculemus! (its own repository and kit) moves onto the same VPS
under `calculemus.leibnizlegible.com`. Changed here: `deploy/Caddyfile`
imports `/etc/caddy/conf.d/*.caddy` (sibling apps keep their own site blocks
there; `install.sh` creates the directory; the live box needs the one-line
edit by hand, since the installer copies the Caddyfile only once), runbook
§13 (DNS, the edit, memory on the 4 GB box, backups — `/var/lib/calculemus`
is the first non-rebuildable data on the host), and the
`LEIBNIZ_CALCULEMUS_URL` switch (`web/settings.py`, stamped into the shell as
`<html data-calculemus-url>` like the image origin; the About page renders
its link only then). Default off: nothing about the game in the served HTML
until the operator sets it. Tests +2 (525), ruff clean.

### D — the image mirror (2026-09-16, operator decision; see Divergences) ✅

The public site serves its own copy of the GWLB delivery scans. Built as a
switch, default off:

- **`web/images.py`** — `ImageSource`: with `LEIBNIZ_IMAGE_BASE_URL` set,
  every cached page's display URLs become `{base}/{work_id}/{seq:04d}.jpg`
  and `{base}/thumbs/…` (the cache's own layout, `images/fetch.cache_relpath`,
  so the bucket is the cache directory uploaded as it is), delivered as a
  static image (no IIIF service); pages never cached keep their GWLB URLs.
  The page API adds `image_origin` and `source_image_url` (the GWLB URI,
  always); search hits get mirror thumbnails; the manifests paint the mirror
  copy and record the GWLB source per canvas; annotations keep `leibniz:imageUri`
  on the GWLB; `attribution()` has a mirror wording for the web surfaces while
  the dataset cards keep the original line. `/api/stats` reports
  `images.origin`, and the server stamps `<html data-image-origin>` into the
  shell (read once, ETag + 304) so the viewer's footer, page attribution and
  About texts switch without another request (EN + DE strings added).
- **`leibniz images thumbs`** (`images/thumbs.py`) — one thumbnail per cached
  page, 320 px wide, Pillow decoding at reduced scale from the JPEG DCT, all
  cores, resumable; **`leibniz images check-mirror`** HEADs a sample of the
  mirror and compares sizes with the cache manifest (`rclone check` is the
  full check). Runbook §12 covers the R2 bucket, the custom domain, rclone.
- Caddyfile: `www.` → bare domain; env examples name the mirror.

### D — deployment kit, public-traffic hardening, public-repo prep (2026-09-16, later session) ✅

The serving layer was finished but nothing existed to put it on a host. Built,
offline-tested and documented so that going live is an operator runbook
(`deploy/README.md`), not another coding session:

- **`deploy/`**: `install.sh` (idempotent Debian/Ubuntu bootstrap: users,
  directories, uv + venv as the service user, the Meilisearch binary with a
  generated master key, Caddy from its apt repository, the units),
  `leibniz-legible.service` + `meilisearch.service` (hardened sandboxes, the
  app bound to localhost), `Caddyfile` (auto-TLS, zstd/gzip, HSTS, a JSON
  access log kept seven days, an optional edge rate-limit block),
  `env.example` / `meilisearch.env.example` / `caddy.env.example`,
  `prepare-store.sh` (desktop: WAL checkpoint → `VACUUM INTO` → integrity
  check → SHA-256; a compact rollback-journal copy the read-only app opens
  without sidecars), `meili-search-key.sh` (a search/stats-only key, so the
  master key never reaches the serving process), and
  `docker-compose.prod.yml` + a root `Dockerfile` (uv multi-stage, non-root,
  healthcheck on `/healthz`) as the all-container alternative. The compose
  file validates (`docker compose config`, required variables enforced); the
  image build itself is unverified here — no Docker daemon in this
  environment.
- **`leibniz serve`** takes every option from the environment
  (`web/settings.py`: `LEIBNIZ_DB_PATH`, `LEIBNIZ_SEARCH_BACKEND`,
  `LEIBNIZ_BASE_URL`, `LEIBNIZ_WORKERS`, `MEILI_API_KEY` …), runs
  `--workers N` through an ASGI factory (`web/asgi.py`), and `LEIBNIZ_DB_PATH`
  is now honoured by every command (`.env.example` documented it; nothing
  read it).
- **Hardening in the app** (`web/middleware.py`, so every way of running it
  is covered): a per-client token-bucket rate limit on `/api`, `/manifests`,
  `/annotations` (default 10/s, burst 40, `429` + `Retry-After`, bounded
  memory), security headers with a CSP (`script-src 'self'`; the viewer's one
  inline script moved to `static/boot.js`), CORS `*` on the JSON routes so
  Mirador elsewhere can load the manifests (D7 needed it and lacked it),
  gzip (a 3,500-page manifest: 2.5 MB → 62 KB), `no-cache` on the viewer
  shell, `/robots.txt` closing the machine endpoints to crawlers (one walking
  the manifests would pull every GWLB image), every store connection
  `mode=ro` + `query_only`, Meilisearch outages answered with `503`
  (`/api/stats` and `/healthz` degrade instead of raising), and
  `GET /healthz` for the process manager and an uptime monitor.
- **The giants** (works of 1,000–3,500 pages): the work and manifest
  endpoints run one query per work (`line_summaries_by_page`, a `NOT EXISTS`
  probe on the lines' covering unique index) instead of one per page.
  Measured on a synthetic 3,500-page × 60-line work with a partial re-run:
  180 ms against 228 ms for the per-page loop, the fastest of five plans
  tried (`GROUP BY` and window forms were slower). So the loop was never the
  problem the previous session guessed (SQLite answers a page-keyed query in
  ~60 µs); the gain is ~20 % and the real cost was payload size, now gzipped
  (`/api/works` for that giant: 238 ms end to end, 485 KB → 30 KB).
- **`leibniz index bench`** (`search/bench.py`): p50/p95/max over HTTP for
  a built-in list of fifty Nachlass queries (with misspellings for the typo
  tolerance) or a file of real ones, `--concurrency`, exit 1 when p95 misses
  SPECS §3.3's 500 ms — the measurement step of the runbook.
- **Public-repo prep**: `LICENSE` (Apache-2.0 verbatim; declared in
  `pyproject`/README, absent until now),
  `.github/ISSUE_TEMPLATE/transcription-error.yml` (an issue form; the
  viewer's "Report an error" link now opens it with the page id and URL
  prefilled), Issues confirmed enabled on the repository.
- **Verified**: 504 tests (+29), ruff clean; every viewer route driven under
  Playwright/Chromium against the real app with the CSP and the rate limit
  on (EN/DE, search, work, page with OpenSeadragon on a same-origin image,
  about, a 404): zero CSP violations, zero console errors; the limiter trips
  at the configured burst.
- **Follow-up, same day — the kit against a real Meilisearch (v1.53.2 binary,
  the version now pinned in `install.sh` and both compose files).** Two
  things the fakes had hidden: (1) on current Meilisearch, deleting an index
  that does not exist is a task that *fails* with `index_not_found` (a 404
  was the pre-1.0 behaviour the fake copied), so the very first
  `leibniz index build --backend meili` on a fresh server aborted — the
  backend now ignores exactly that failure, and the fake fails like the
  server; (2) Meilisearch creates `dumps/` in its working directory at
  startup, which under the unit's `ProtectSystem=strict` is a
  permission-denied crash — reproduced as an unprivileged user with a
  read-only cwd, fixed with `WorkingDirectory=/var/lib/meilisearch` and
  explicit `MEILI_DB_PATH`/`MEILI_DUMP_DIR`/`MEILI_SNAPSHOT_DIR`. Also:
  `install.sh` runs git and uv as the service user (git refuses to act as
  root on another user's checkout, which would have broken every re-run),
  restarts Caddy only once a real domain is configured, and installs the
  pinned Meilisearch release only when absent (an upgrade must be
  deliberate: a newer binary refuses an older index); `leibniz index
  status/query` accept `MEILI_API_KEY`. Then the full path end to end with
  the real server: search-only key created and confined (document writes
  and key listing 403), index built on a fresh server, `leibniz serve
  --workers 2` healthy, the misspelt `calculemvs` finds *Calculemus*,
  `/api/stats` served from the build metadata through the search key,
  `leibniz index bench` 60/60, and with Meilisearch stopped: search 503,
  pages 200, `/healthz` degraded. That bench also exposed a 40 ms stall on
  every kept-alive request after the first when `--workers` > 1 (wall p95
  52 ms against a 1 ms backend): uvicorn's own shared listening socket is
  created with ``proto=0`` and asyncio sets ``TCP_NODELAY`` on accepted
  connections only when the socket says IPPROTO_TCP, so Nagle's algorithm
  met the peer's delayed ACK. `leibniz serve` now binds its own
  IPPROTO_TCP socket for the multiprocess supervisor — 44 ms → 1–3 ms per
  request, bench p95 3 ms with two workers. And the bench itself now paces
  its launches (8/s, under the app's 10/s limit) and reports `429`s apart,
  so on the production configuration it measures the server rather than
  its own rate limiting.

### D1–D3 — search, viewer, IIIF, releases, built on v1 (2026-09-16) ✅

Built the whole serving layer against the v1 store, offline-tested end to end
(seeded store → index → API → viewer screenshot under Playwright):

- **D1 search** (`src/leibniz/search/`): `documents.py` (one doc per recognised
  page: latest run per line, majority language, `page_stats.stratum_heuristic`,
  katalog records rendered as `AA I,3 N. 12` labels), `normalize.py` (the
  aligner's fold minus struck-text elision, shared by index and query),
  `snippet.py` (hits marked in the *original* text via the folded→original
  offset map; the only HTML the API emits), `fts5.py` (contentless FTS5 over
  the folded text + title/shelfmark/AA columns weighted ×3 in bm25; prefix
  matching from 3 chars; filters as column predicates), `meili.py` (plain httpx;
  drop → create → settings → batched documents, each awaited on the task queue;
  doc ids with `:` → `_`), `cli.py` (`leibniz index build|status|query`). The
  build records corpus statistics (counts + confidence histogram) in the index
  for `/api/stats`.
- **D2 API + viewer** (`src/leibniz/web/`): `api.py` (`create_app`; per-request
  store connections; latest-run line selection; bbox from polygon; prev/next;
  404s as `{"detail"}`; 503 when no index), `iiif.py` (Presentation 3 manifest
  per work wrapping GWLB image services; annotation page per page with
  `supplementing` TextualBody annotations targeting `#xywh`, provenance under
  the `leibniz:` JSON-LD namespace), `attribution.py` (one source for the
  three attribution lines), `geometry.py`, `cli.py` (`leibniz serve`,
  `--check` lists routes). The viewer (`static/`, 15 files + vendored
  OpenSeadragon 5.0.1, 624 KB) is plain ES modules served by the app at `/`,
  `/search`, `/work/{id}`, `/page/{id}`, `/about`; 177 i18n keys EN + DE;
  no-JS search form; dark mode; phone width; zero axe violations.
- **D3 releases** (`src/leibniz/release/`): `export.py` (row generators for
  inventory / transcriptions / gt; latest run per line; NC rows excluded;
  chunked Parquet via pyarrow or gzip JSONL; `MANIFEST.json` with SHA-256s),
  `cards.py` (the dataset cards), `cli.py` (`leibniz release export|checklist`);
  `reports/release-checklist.md`, `reports/tier1-final.md`.
- `docker-compose.yml` (Meilisearch), `.env.example` (`MEILI_*`), `pyproject`
  extras `web` + `release` (fastapi/uvicorn in the dev group so tests run).
- Tests **+47** (475 total): folding/snippets, documents, FTS5, Meilisearch
  against a fake server, IIIF builders, the API over `TestClient`, exports
  (JSONL always, Parquet when pyarrow is present), CLIs.

### C1 — corpus-run robustness, from the first live runs (2026-07-29/30)

The operator's first real 500-page runs (GPU + WSL/CPU) surfaced four defects the
offline fakes could not; all are fixed with offline regression tests:

1. **Confidence was a pixel cut position** (`_tok_conf` now picks the [0,1]
   posterior field, else `None`) — Open Q #15's exact worry.
2. **`--device cuda` crashed both stages** (kraken wants `(accelerator, device
   count)`, not a device string) and **segmentation ignored its device**.
3. **A sub-5px baseline sank its whole page** (17 % of the sample); such lines
   are now filtered up front and just left untranscribed.
4. **A "poison page" killed recognition entirely, four runs in a row** — the
   process died (`Terminated`, no traceback) at the same page each time, once
   with PIL `1.0 / w` divide-by-zero warnings, once silently. Reading kraken
   7.0.3's `extract_polygons`: it rectifies each line's boundary into
   along-baseline × perpendicular coordinates and sizes the output crop from
   their **raw, unclamped extents** — degenerate stored geometry (zero-length
   segments → NaN mesh quads; far-flung rectified points → an OOM-scale
   allocation the OS kills mid-way). Five layers now prevent the whole class:
   (a) same-pixel consecutive points are collapsed before cropping;
   (b) `pipeline/geometry.py` **replicates kraken's `output_shape` arithmetic**
   (pure Python, offline-tested) and drops any line whose implied crop exceeds
   `max(4× page area, 24 MPx)` — the OOM class caught *before* allocation;
   (c) PIL-attributed `RuntimeWarning`s are escalated to errors inside
   `crop_lines` (a NaN'd transform never yields a usable crop);
   (d) a failed page-crop falls back to per-line cropping, so a poison line
   costs *the line*, not the page; and (e) a SIGALRM **crop deadline**
   (120 s/page, 30 s/line) converts any residual in-process stall into the
   normal skip path. `leibniz pipeline audit [--page ID]` prints any page's
   per-line geometry verdicts from the store alone (no kraken) — the operator's
   first tool when a page skips or dies.

**Root cause, finally caught live** (rlimit'd probe on the operator box, page
`00051012:0070` — a small scrap page segmented into 21 speck "lines"): the
killer was never the crop — it was **recognition**. One line's dewarped crop is
a ~900×1 px empty mask sliver; `ImageInputTransforms` resizes crops to model
input height *preserving aspect ratio*, so the sliver becomes >100k px wide,
the whole batch pads to it, and a single `F.conv2d` allocates **5.3 GB**
(`DefaultCPUAllocator` enforce-fail under the probe's rlimit; under normal
Linux overcommit it "succeeds" and the OS kills the machine — invisible to
every in-process handler, which is why layers a–e couldn't catch it). Fixes:
the pipeline now judges the **actual crop raster** before recognition (PNG
header peek, no imaging dep: `min side < 4 px` or `aspect > 100:1` →
`sliver_crop:{w}x{h}`, line dropped); `KrakenEngine` refuses transformed lines
wider than 10k px (`("", None)` placeholder — backstop for any caller); and
`pipeline segment/recognize --mem-limit-gb N` caps the process address space so
any residual runaway allocation fails one page instead of the box.

**Operator validation (2026-07-30): the crash class is closed.** A full 431-page
CPU pass completed with zero crashes; the poison page recognised with its sliver
enumerated (`sliver_crop:900x5`), and the original gate finally reports
**`conf > 1` count = 0** (Open Q #15's field shape confirmed live at scale).
Two calibrations from that run: an address-space cap must clear torch's
*virtual* arena — 6 GB starved it after ~55 pages (alloc-fail skips); use
**`--mem-limit-gb 12`+** (virtual ≠ resident). And a batch padded to its widest
line multiplied conv memory (a 722 MB single alloc) — `KrakenEngine` now flushes
on a padded-area budget (`n × widest ≤ 64k` width-units), bounding peak memory
on CPU and GPU alike.

**Concurrency root cause found and fixed (2026-08-27).** The first genuinely
concurrent run (shard workers + recogniser) died with `database is locked`
despite WAL + a 30 s busy timeout: each stage walked its work list with one
**long-lived read cursor on the same connection it writes with**, pinning a WAL
snapshot; the first write after any *other* worker commits then fails with an
un-retryable snapshot-upgrade BUSY (the timeout cannot help). Single-writer
runs never trip it — true concurrency always will. Both stages now page their
work lists in small **closed keyset batches** (`WORK_CHUNK`,
`iter_pages_by_status(after=…)`): no open cursor survives into a write, and the
keyset advances over raw batches so sparse shards terminate. Along the way an
orphaned Aug-19 worker (never killed by an incomplete cleanup) was found to
have quietly segmented 46,857 pages over 8.3 days before exiting — enumerated
in `runs`, and the reason corpus progress outpaced the single-worker estimate.

**Corpus throughput, measured (2026-08-16): segmentation is CPU-bound at
~140 pages/hour** — 47,448 pages (20%) segmented in ~12 days; `nvidia-smi`
shows the GPU loaded but ~idle (9%), because kraken's per-page cost is
dominated by single-threaded CPU vectorization, not the neural pass. On the
operator's 16-core box that left 15 cores idle and implied 56 more days.
Answer: **sharded parallel workers.** `segment`/`recognize` now take
`--shard i/N` (stable crc32 over `work_id`; shards are disjoint, complete, and
keep a work's folios together), and `db.connect` enables WAL + a 30 s busy
timeout so N per-page-committing processes coexist safely. The operator
runbook runs 1 CUDA + 3 CPU segment workers (~3–4×, ≈2–2.5 weeks for the
remainder); recognition stays a single GPU worker (~3.5 s/page measured).

**Corpus-run incident (2026-08-02): a stale command block without `--images`
mass-skipped the corpus in the DB.** The full ~395 GB pull had completed
(236,779/236,795 verified, 16 redirect-loop failures) with the cache moved to a
second drive; a re-run of an older snippet then pointed segment/recognize at
the default (deleted) root and marked ~236k cached pages `image_missing` in one
pass. No data was harmed — images, manifest (sha256/local_path), geometry, and
recognitions all intact — and statuses were restored from the manifest
(`skip_reason='image_missing' AND sha256 IS NOT NULL` → back to
segmented/pending). Two guards now prevent recurrence: a **preflight** on both
stages aborts (marking nothing) when ≥5 sampled cached pages all lack files
under the given root ("wrong --images root?"), and segment skips **oversize
images** (> 80 MPx; ~120 MPx foldouts observed) with a reason instead of
risking an OOM — the suspected killer of the first corpus segment attempt,
which died ~1,550 pages in.

**CUDA smoke (100 fresh pages): segmentation ran (7,496 lines, 75/pg —
Marginalien-dense), recognition failed 100/100** with `Input type
(torch.FloatTensor) and weight type (torch.cuda.FloatTensor)`: kraken's
`_rec_predict` never moves inputs — after `prepare_for_inference` puts the net
on the accelerator, the caller owns the transfer. `KrakenEngine` now records
the net's parameter device at load and moves each batch onto it (`lens` stays
on CPU for sequence packing). Same smoke exposed the kraken-7 token layout
`(grapheme, start, end, conf)`: front-to-back `[0,1]`-scanning misread
`start == 0` (every line's first token) as confidence 0.0 — `_tok_conf` now
scans from the end, where the posterior always lives. **Open calibration:**
GPU segmentation measured 18.8 s/page on the dense dev slice — verify GPU
engagement (`nvidia-smi` during a run) and re-estimate the corpus segment pass
on mixed sets; the ≈260 GPU-h estimate assumed 3–6 s/page combined.

(1–3 landed as `140d58d`; 4 across this entry's commits.) Live evidence: real
posteriors ≈0.6–0.9 populate at scale (CPU: 498/500 pages, 23k lines, mean
conf 0.771, `conf>1` = 0 — the C1 validation gate is **passed**). Remaining
operator gate: the CUDA recognition re-run, then the corpus pass.

### C2 — close-out: the hand audit is preliminary; gate deferred to C3 (2026-09-16)

The operator judged **20 of the 200** sheet lines and stopped, saying so
plainly: not confident in the verdicts, wants them treated as preliminary
and open to review. Recorded as such; C2 is closed on the mint, not on the
gate.

- **What the 20 say:** all in `fair_copy` (the sheet lists strata in
  order): 12 correct · 0 boundary · 5 wrong · 3 unreadable → 70.6 %
  precision on 17 scored, Wilson 47–87 % — a FAIL as written
  (`reports/gt-audit.md`, committed from the operator's machine with the
  two CSVs).
- **What the second witness says:** `audit-score` now cross-checks every
  verdict against the folded similarity between the minted text and the HTR
  reading of the *same strip* (the crops are in the page's own pixel space —
  the C1 segmenter never resizes). **All five "wrong" lines agree with the
  machine reading at 0.82–0.98** (e.g. minted "but, qu'il seroit trop long
  de rapporter icy." vs HTR "… rapporter ici."; "la difficulté demeure
  toujours à multiplier cette presence" vs "la diffienete demeuve toujours
  …"): the machine read the words the edition gives, on that strip. Read as
  misjudged verdicts — the auditor's own reading of themselves — the fair-copy
  sample is 17/17. The three "unreadable" are two short lines and an Italian
  one. None of this is a pass: 17 lines, one stratum, one non-specialist.
- **Tooling:** `audit-score --lines` (default: the sheet's own CSV) writes a
  "Second witness" section listing verdicts to re-check (a *wrong* or
  *unreadable* at ≥ 0.8 agreement, a *correct* below 0.5) with both texts
  side by side; +1 test.
- **Decision:** proceed to C3 with the gate **deferred**, on two grounds.
  (1) The audit gives no evidence of a precision problem, only of an
  unfinished audit. (2) C3's design already contains the decisive test: the
  ablation *PHILIUMM GT alone* vs *+ C2 GT* on the page-disjoint held-out set
  measures what the minted lines are worth without anyone reading a hand.
  A GT that is 30 % misaligned would show up there as no gain or a loss. The
  hand audit stays open (Q #18) for whoever can read the hands; the sheet
  and the flagged list are in the repo.

### C2 — the mint ran; hand-audit tooling (2026-09-15/16) ✅ mint · ⏳ audit

The operator's runbook run, with the fixes below merged in between:

- **Pass 1** (six `--shard i/6` workers, no `--resume`, ~1 GB RAM total,
  ~2 h): **317,365 pairs from 6,383 pieces** at 30–45 pieces/min/shard.
  Skips: 5,567 not localizable · 4,314 no edition text (the ten volumes
  without a free copy, Open Q #16) · 141 no canvases · 11 no HTR lines ·
  **746 `error:OperationalError: database is locked`** — the C1 WAL
  stale-snapshot failure on the per-piece commit (4.3 % of pieces; each one
  skipped, the shard alive thanks to the per-piece guard).
- **Cleanup pass** (`--resume`, after `factory.write_pairs` moved to
  `BEGIN IMMEDIATE` + retries): re-minted the 746, +23,680 pairs on the five
  shards with a summary; three shards then crashed on the *run bookkeeping*
  stamp — the last deferred write left — after all their pieces; fixed by
  routing every factory write through `with_write_lock`.
- **Store:** `gt_lines` = **297,424** rows, all `open` (§70 sources only):
  fair_copy 9,913 · light_revision 96,175 · heavy_revision 190,162 · scrap
  1,174. Lower than the log totals (341k pairs) because citations overlap —
  a re-minted piece replaces the rows of shared line refs; the store counts
  distinct lines. **5.9× the ≥50k target**; `reports/gt-factory.md`
  regenerated and committed from the operator's machine.
- Read of the strata: two thirds of the minted lines sit in
  `heavy_revision`, the stratum held to the 0.72 threshold — the Nachlass
  is mostly drafts, and the heuristic (Open Q #11) calls most pages so;
  C4 recalibrates it against the audit.
- **Hand-audit tooling** (`align/audit.py`, CLI `audit-sheet` /
  `audit-score`, +9 tests): draws equal numbers per stratum (a
  proportional draw would give fair copies a handful), cuts each line's
  strip from the cached page by its C1 polygon, writes one self-contained
  HTML sheet (strip · minted text · HTR text · correct / boundary / wrong /
  unreadable, saved in the browser, downloaded as CSV); the scorer reports
  precision per stratum with Wilson 95 % intervals, the *usable* rate
  (boundary-off lines included) and the corpus-weighted precision against
  `GATE_PRECISION` (95 %) as `reports/gt-audit.md`. **The audit itself is
  the operator's next step** (the strips need the image cache on drive D).

### C2 — the mint's first live runs: workers OOM-killed → aligner rebuilt (2026-09-15)

The operator launched the mint on the WSL box (16 cores, an 11 GB VM) with 12,
then 8, then 6 shard workers on the JSONL cache; every attempt took the VM
down. `dmesg` finally named it: **one worker at 5.7 GB RSS**, not the sum of
many. Root cause, confirmed in the code and reproduced here:

- **`dp.align_banded` widened its band to the whole length difference**
  (`half = max(band, |n−m| + 8)`), so a piece whose edition text is far longer
  than its HTR spine got the *full matrix back*, at 5 bytes a cell. That shape
  is the norm, not an edge case: **186 of the 10,029 cached records carry
  >100k characters** (VI,6 N. 2, the Nouveaux Essais, is 753,788 characters
  and is cited by 6 records; one 497,888-character piece by 63) — a 100-line
  spine against one of those was ~15 GB.
- **Fix — `align/anchored.py`**: localize first, align second. Shared 8-grams
  of the folded texts (index the shorter side, scan the longer) → longest
  monotone chain (patience LIS, isolated outliers dropped) → a fixed-width
  band about the piecewise-linear path through the anchors → the DP in
  ~8k-row **chunks cut at matched runs** (each chunk a few MB, whatever the
  piece length). `dp.align_in_band` is the new core: per-row column windows,
  two rolling distance rows, a one-byte move table, per-side/per-end free
  gaps, and a hard `max_cells` guard; `align_banded` is reimplemented on it and
  now *refuses* a runaway band instead of allocating it. Pieces that share
  nothing with their text fall back to the null alignment (nothing minted)
  rather than a worker death.
- **Measured (synthetic, this box):** the crash shape (10k spine vs 120k
  text) — **44 MB peak, 1.9 s** (was ~6 GB and killed); a 300k-character
  treatise vs its 330k text — 112 MB, 46 s; real cache text (3k spine inside
  the 753k Nouveaux Essais) — **yield 0.98, 3.6 s**; exact vs the full DP on
  near-parallel pairs, chunk joins included.
- **Two GT-quality guards the same failure exposed** (`align.py`): the free
  edition overhang (insertions before the first / after the last HTR hit) no
  longer lands in the first/last line's slice — with a parent record's text
  served for a sub-piece it was the whole overhang; and a line is refused when
  the alignment inserts more edition characters into it than
  `max(12, its own length)` (an apparatus block or an omitted passage glued to
  a well-matched line — the matched fraction cannot see it). `AlignedLine`
  gained `n_inserted`.
- **Factory:** one bad piece can no longer end a shard — `run_factory` catches
  per-piece exceptions, rolls back, and records `skipped:error:<Type>`.
- **Live, two hours into the fixed run (six shards, ~1 GB used, ~2,000
  pieces and ~30k lines per shard):** three shards logged a piece
  `failed: OperationalError: database is locked` — the C1 WAL
  snapshot-upgrade failure again, now on the mint's per-piece commit: a
  deferred write that waits for another worker's commit fails at once with a
  stale snapshot (the busy timeout never runs). `factory.write_pairs` now
  takes the write lock first (`BEGIN IMMEDIATE`, one transaction per piece)
  and retries a lock collision with jittered backoff; the affected pieces
  are re-minted by a `--resume` pass (they carry no `gt_lines`).
- Tests **+13** (417 total: anchoring, localization both ways, chunk joins,
  the memory bound, the guards, projection); ruff clean. Also recorded: with
  unit costs and non-free HTR ends, the last ≤ `band` characters of a passage
  can scatter as chance matches over uncovered manuscript (Open Q #17).

### C2 — GT factory at scale, the inputs built and run (2026-09-11) ✅

The 07-29 build (below) mints nothing without three inputs; this session
built and ran two of them at full scale, so the factory now waits only for the
store that holds the C1 HTR lines.

- **Katalog sweep of every §70 volume** (`catalog/scrape.py` `scrape_volume`,
  CLI `--volume S,V` / `--expired-volumes`). Measured live: the katalog matches
  `reihe`/`bd` as **substrings** (`bd=1` returns volumes 10–19 too; the form's
  `*_exact` flags are ignored), and a bare-year `datum_bis` is exclusive — so a
  capped volume slice is re-run by year (`datum_ab=Y&datum_bis=Y1231`) and
  filtered client-side by the parsed AA column. 31 slices, 173 + 144 queries,
  ~10 min at ≤1 req/s: **24,916 records (17,562 with a GWLB
  link) → 17,646 crosswalk links, 1,197 works** (crosswalk works
  matched 1,197/2,225; the §70 volumes' records only — the full 70k scrape
  remains an A3 operator job). `parse_aa_refs` now keeps the katalog's
  *Unternummer*: `/ tlw.` (a partial witness) → `partial: true`, a page/line
  locus → `note`; only a single letter is a sub-piece.
- **Piece enumeration at scale:** **17,162 §70 piece citations · with
  work 12,385 · with folio range 11,617 · localizable
  11,595 (67.6 %)** — the folio resolver (Open Q #10)
  holds on real data across all 31 volumes (`leibniz align pieces`).
- **Volume sources** (`align/volumes_sources.py`, verified 2026-09-11):
  archive.org holds Trent University's scans of ~30 AA volumes (no access
  restriction, Tesseract hOCR + leaf images), the GWLB repositorium serves
  I,3/9/11–27, III,5–9, VII,3–8 (ABBYY text layer, **CC BY-NC channel**),
  Potsdam serves IV,1–10 born-digital, Münster's Internetausgaben (II, VI,4)
  require written permission (operator ask; never auto-fetched). **21
  of 31 expired volumes are readable**; 10 have no free digital copy (I,1, I,2,
  I,4, I,5, I,13, II,1 (1926), III,2, VI,2, VII,1, VII,2 — HathiTrust holds the
  1923–27 prints as US-PD; TELOTA/Göttingen ask for the rest). Preference:
  IA (unencumbered) > GWLB (flag for the lawyer memo) > Münster (ask).
- **Reading-text extractor** (`align/edition.py`, +11 tests): one
  layout model over hOCR and PDF text layers (`pdfplumber`, optional `gt`
  extra). Per volume it learns the body/apparatus type sizes (Tesseract 41/33
  px, ABBYY 10/9.5 pt, Potsdam 10.5/9 pt) and the paragraph indent; per page it
  peels the running head (which lists the pieces *starting* on the page — the
  anchor), cuts the apparatus block at the bottom, drops margin line numbers
  (also when OCR glues them to a line), detects piece headings (`13. GOTTFRIED
  CHRISTIAN OTTO AN LEIBNIZ`, OCR'd `i.`, ABBYY's small-caps-as-lowercase),
  skips the dateline/*Überlieferung* block until the body margin, and carries
  the current piece across pages; a garbled head never re-synchronises the
  piece, an unplaceable boundary drops the page's tail instead of
  misattributing it (precision over recall). Validated on three source types:
  I,6 hOCR 352/362 pieces, IV,1 Potsdam 52/52, I,11 GWLB 501/521; a leak
  heuristic flags 0.1 % of extracted lines.
- **Ingestion + edition cache** (`align/ingest.py`, CLI `leibniz align ingest` /
  `edition-cache`): cache-first fetch → extract → per-volume JSON with piece
  texts + page anchors; the cache join maps every katalog record citing an
  ingested piece to its text (sub-piece → parent fallback). **Run here:**
  6,188 pieces / 26.16M chars over 21
  volumes; **10,029 records carry reading text.** Cross-source
  QA on the 5 volumes with two independent OCR layers: mean
  agreement 81.6% (54 of 200 pieces
  flagged >10 % CER).
- **Report** (`reports/gt-factory.md`, regenerated): sources/terms table per
  volume, extraction + QA numbers, the priced vision upgrade (Sonnet 5 / Opus 5
  / gpt-4o-class per page and for all OCR'd pages, Batch −50 %), the operator
  runbook. Tests **+16** (401 total); ruff clean.

### C2 — GT factory at scale (2026-07-29) ✅

Built the C2 GT factory on top of the B2 aligner (`src/leibniz/align/*` extended).

- **The join** (`volumes.py`): a §70-expired volume's pieces *are* the katalog
  records citing it — `enumerate_pieces` walks `katalog_records.aa_refs` ×
  `legal.expired_volumes` × the A3 crosswalk, emitting a `PieceRef` per citation
  with the work id (best crosswalk link), folio range, and katalog text type.
- **Piece→canvas resolver** (`resolve.py`, Open Q #10 **solved**): the folio-range
  parser + `pages.label` (folio labels C1 now stores) turn a katalog `Bl.` range
  into exact canvases (`Bl. 164–165` → the recto/verso canvases). Pure/offline.
- **Banded aligner** (`dp.align_banded` + `align._align_spine`): O(len·band)
  Needleman–Wunsch with traceback for long multi-page pieces past the 30M-cell
  guard (B2's blocking gap). Tested **exact vs the full DP** (0 mismatches, wide
  band; exact at band 32 on 8%-noise near-parallel pairs) and length-difference-safe.
- **Stratum heuristic** (`stratum.py`, Open Q #11): fair_copy vs draft from the C1
  segmentation stats + katalog `textart` (Reinschrift/Konzept…); sets the mint
  threshold per piece (drafts held higher — precision over yield).
- **Factory** (`factory.py`): resolve → gather C1 HTR lines → align (banded) →
  stratum-threshold → mint `gt_lines` with provenance + license gate (§70 `open`;
  Transkriptionspool `nc`). Below-threshold discarded; idempotent re-mint; one
  `runs` row per batch. Edition text is **injected** (`edition_text_for`), so the
  whole orchestration is offline-testable; the production provider wires `pdftext`.
- **Extraction QA** (`volumes.assess_extraction`, Open Q #12): a two-pass /
  two-model agreement estimate flagging unstable extractions for a per-volume
  error rate. **Validated live** on real Leibniz print (Gerhardt II, 1875, PD,
  archive.org): `gpt-4o` extracted the reading text and dropped the running head /
  page number / signature; two-model QA flagged 1/2 pages (mean agreement 0.67) —
  the code-switched page where `gpt-4o-mini` dropped ~60% of the text. Evidence:
  `reports/gt-factory-extraction-qa.json`.
- CLI: `leibniz align {pieces, factory, gt-report}`. Deliverable
  `reports/gt-factory.md` (piece enumeration, yield vs the 63k/≥50k targets, by
  stratum, the live extraction validation, operator runbook). Tests **+33**; ruff
  clean; offline (kraken/keys not needed — the aligner + factory run without them).

### C1 — Corpus segmentation + HTR v1 (2026-07-29) ✅

Built the corpus batch pipeline `src/leibniz/pipeline/*` + extended the store.

- **State machine**: `pending → segmented → recognized` over `pages`, resumable
  (commit per page), idempotent (`--redo` clears + re-segments), `--sample`/`--set`
  scoping, per-page fault tolerance (skipped + reason, never fatal), one `runs`
  row per batch (model@version, params, git SHA, counts, wall time).
- **segment** (`segment.py`): PHILIUMM baseline segmenter → line geometry into
  `lines` (`status='machine'`, text empty) + a `page_stats` row.
- **recognize** (`recognize.py`): crops each stored line from geometry (no
  re-segmentation — `PageSegmenter.crop_lines`), PHILIUMM HTR → text + per-line
  confidence, repointing run/model at the recognition run (SPECS §4.5).
- **Segmentation stats** (`stats.py`): pure-geometry per-page metrics (line count,
  region coverage, line-height CV, overlap + short-line anomalies) — the layout
  signal the C2/C4 stratum heuristic reads. Fully offline-tested.
- **Store**: new `page_stats` table + `pages.label` (folio label, for the C2
  resolver) + `Line`/`PageStats` + status/line/stats helpers (`db.py`).
  `KrakenEngine.transcribe_conf` and `PageSegmenter.crop_lines` added.
- CLI: `leibniz pipeline {segment, recognize, status, report}` (status/report run
  without kraken; segment/recognize preflight-check the stack). The live 500-page
  run needs the kraken stack + image pull (absent here); built + offline-tested
  (+27 tests), operator runbook + GPU/cost estimates in `reports/htr-v1-sample.md`.

### B2 — Retro-alignment prototype (2026-07-29) ✅ Gate: GO — green-light C2

Built the retro-alignment engine (`src/leibniz/align/*` + `src/leibniz/layout/segment.py`)
and measured it end-to-end. **Aligner yield 98.8% at 97.5% precision on favorable
material under real HTR; false-mints 0 under omission ⇒ build the C2 GT factory.**

- **The engine** (`src/leibniz/align/`, pure + offline-tested):
  - `normalize.py` — the lossy *alignment* comparison alphabet (casefold, u≡v,
    i≡j, long-s, ligatures, a small Latin-brevigraph list, struck `xx` elision,
    punctuation) **with a folded→original offset map** so the minted GT is a slice
    of the *original* edition (accents/capitals intact), not the folded form.
  - `dp.py` — Needleman–Wunsch with full traceback + semi-global (free-end) option
    (the path `metrics.edit_distance` doesn't give). Documents the both-free
    degeneracy the aligner avoids.
  - `align.py` — the **boundary-projection** retro-aligner: HTR spine ↔ edition
    text → per-line projected slice + confidence; hyphenation-rejoin across line
    breaks; free edition overhang.
  - `evaluate.py` — the quantitative harness (real HTR on the val split; exact
    per-line grading; divergence + omission conditions; threshold sweep).
  - `pairs.py` — mint `gt_lines` with provenance + the **license-bucket gate**
    (`open` only for §70; `nc` never in CC BY) enforced at write time.
  - `pdftext.py` — §70 reading-text extraction (GPT-4o vision on scanned print,
    apparatus excluded per §7.2; text-layer fallback; skips without a key).
  - `prototype.py` — GWLB IIIF → segment → HTR → align orchestration (no rehosting).
  - `cli.py`, `report.py` — `leibniz align {eval,extract,run,report}`; the report.
  - `layout/segment.py` — PHILIUMM baseline segmentation (kraken-5→7 metadata shim).
- **Quantitative gate (real HTR on the PHILIUMM val split, `data/bench/` cached):**
  diplomatic 98.8%/97.5% (yield/precision) · divergence 3% 98.5%/96.7% · divergence
  6% 98.2%/97.2% · omits-15% 94.2%/95.5% · divergence 3%+omits-15% 84.2%/92.0%.
  **`false_pos = 0` in every condition** — the confidence signal never mints an
  edition-omitted line, so precision loss is lost yield, not polluted GT.
- **Live pipeline, run on real data this session:** GWLB IIIF `/full/full/0/default.jpg`
  (2008×2561 quarto) → PHILIUMM seg (**44 lines** on `00068642` c0, LH 4,6,18) → HTR
  (readable Latin) → GPT-4o extracts clean §70 AA VI,4 reading text (apparatus
  excluded). Katalog-verified pair: `00068642` c0 = **AA VI,4 N.109**.
- **Localization finding (for C2):** GWLB IIIF canvas labels *are* folio numbers
  (`164r`…), so the katalog `Bl.` range → exact canvases (Bl.164–169 → 322–333).
  This is the piece→canvas resolver C2 needs; the §70-volume OCR is too garbled to
  text-search, and scans are convolutes of 16–414 canvases.
- Tests **+43** (→ **274 passing**, 1 skipped); ruff clean. Kraken/torch/pyarrow
  used live but remain the optional `bench` extra (the align engine + its tests
  run without them; the 1 skip is the absent-stack path, now unexercisable).
  Deliverable `reports/alignment-prototype.md` (+ `alignment-eval.json`).

### B1 — Benchmark harness + PHILIUMM reproduction (2026-07-29) ✅ Gate: GO

Built `src/leibniz/htr/*` (deliverable D5) and reproduced the PHILIUMM CER on the
model's own val split. **Measured CER 7.95% (95% CI 7.49–8.46) vs claimed 8.33%,
Δ −0.38 → reproduced; build on the model.**

- **Artifacts (CC BY 4.0), fetched + documented:** HTR model (Zenodo
  `10.5281/zenodo.21457538`, `FoNDUE-GD_v2_ft_Leibniz.safetensors`, 16 MB, 178
  graphemes), val GT (HF `DenisaB/htr_leibniz_dataset_v1` val split, 1,878
  pre-extracted line/text pairs, 303 MB parquet), segmentation model DOI
  `21537859` (recorded; not needed to score pre-segmented lines).
- **Harness:** engine-agnostic; `Engine` protocol + `KrakenEngine` (local),
  `AnthropicEngine` and `OpenAIEngine` (Claude/GPT vision, skip without a key).
  CER/WER via unicode-aware Levenshtein under a **named, published normalization
  policy** (`philiumm` mirrors the model's training NFD + whitespace-collapse),
  micro-averaged, with seeded **bootstrap CIs**; per-line JSONL dumps; a **frozen
  protocol** `b1-2026-07`.
- **Frontier-VLM comparison (ran with a supplied OpenAI key):** 3-model panel on a
  seeded 150-line subsample — gpt-4o 45.87% / gpt-4.1 38.62% / gpt-4.1-mini 34.79%
  CER, all 4–6× the fine-tuned model's 8.19% on the same lines; total cost $0.49,
  token usage captured per response. The `--llm-model` flag is repeatable for a
  panel; each VLM row carries its input/output tokens + estimated $ in the report.
- **Key technical finding (a divergence worth remembering):** the model is a
  kraken-5-era **safetensors** container. kraken 7.0.3's `load_any` /
  `TorchVGSLModel.load_model` only parse CoreML and **fail** on it — load it via
  `kraken.models.loaders.load_models(..., tasks=['recognition'])`. And the val
  images are **already polygon-extracted, dewarped lines**, so inference must run
  the recognition net *directly* with `ImageInputTransforms(valid_norm=False)`
  (the baseline-model path); the box/`valid_norm=True` path mis-preprocesses and
  yields ~50% CER garbage. Both are documented in `engines.py` and the report.
- **Normalization matters, but not here:** philiumm 7.95% · lenient (fold
  case+diacritics) 7.61% · strict 7.95% — <0.4 pt spread, so the small gap to
  8.33% is *not* a normalization artifact (it is subset composition / their exact
  ketos-test harness; immaterial to the gate).
- **`--reuse-hyps`** re-scores/re-renders the report from a cached raw-hypothesis
  dump in ~6 s (no inference), so wording can iterate without a GPU/CPU pass.
- Tests: **+58** (229 total; 1 skipped = parquet needs `pyarrow`). ruff clean.
  Kraken/torch/pyarrow are an **optional `bench` extra**, imported lazily — the
  harness and its whole test suite run without them.
- Deliverable `reports/philiumm-repro.md` (measured vs claimed, discrepancy,
  sensitivity, error analysis, protocol, gate) + `reports/philiumm-repro.lines.jsonl`.

### A3 — Katalog crosswalk (2026-07-29) ✅

Built `src/leibniz/catalog/*` and ran a live sample against `leibniz-katalog.bbaw.de`.

- **Site structure (inspected live, documented in `scrape.py`):** server-rendered
  Laravel app, **no API**; GET `/de/global-search?q=…` and `/de/extended-search?…`
  (fields incl. `sign_ol`, `reihe`/`bd`/`nr` = AA series/vol/piece,
  `absender_oder_adressat`, `datum_ab/bis`, and **`id_hannover`**); results are one
  23-column HTML `<table>`; the **Signatur** cell links the scan as
  `…/resolve?id={object_id}` = our works PK. **5000-row result cap**, no pagination.
- **Normaliser** (`shelfmarks.py`): canonicalises LH/LBr/Marg/LK signatures —
  Roman↔Arabic (`LH XXXV,3,5` ≡ `LH 35,3,5`), spacing/punctuation, `Bl.` leaf
  capture, `S.` (Seite) + parenthetical drop, `Stück` kept (a distinct work).
  Tested against messy real strings.
- **Crosswalk**: GWLB link primary (conf 1.0), normalized-shelfmark secondary
  (0.7); method + conf per link; higher-confidence-wins upsert.
- **Deliverable** `reports/crosswalk.md`: coverage by set/method, unmatched
  samples with reasons, operator command for the full scrape. CC BY attribution
  recorded in `catalog.KATALOG_ATTRIBUTION`.
- Raw HTML cached under `data/katalog/` (gitignored). ruff clean; catalog tests green.

### A2 — Image cache (2026-07-29) ✅

Built `src/leibniz/images/*` + extended the `pages` schema/manifest.

- **Schema**: added `image_url,thumb_url,delivery,local_path,n_bytes,sha256,`
  `fetched_at` to `pages` with an idempotent `ALTER TABLE` migration (A1-era DBs
  upgrade in place, no data loss). `upsert_page` preserves the download manifest
  + status on re-derivation (COALESCE).
- **`images pages`**: parses the METS `fileSec`+physical structMap from the OAI
  cache → per-page `DEFAULT` JPEG URL + thumb + delivery mode, offline. Populated
  all 236,795 pages.
- **`images fetch`**: downloads to `data/images/{oid}/{seq:04d}.jpg`, records
  size/sha256/dims (dims read off the JPEG via a dependency-free SOF walk),
  cache-first resume, JPEG-EOI integrity retry, `--set`/`--work`/`--limit`/`--redo`.
- **`images verify`** (existence/size/`--deep` re-hash, gap count) + **`images
  stats`** (counts/bytes/MP-histogram → appended to `census.md`, idempotently).
- Ran the dev slice + `images stats`. Full corpus pull left as an operator command.

### A1 — OAI/IIIF harvest → inventory + corpus census (2026-07-29) ✅ Gate: GO

Built `src/leibniz/net.py` + `src/leibniz/harvest/*` and ran the harvest live.
2,225 works · 236,795 page images (within the 150–250k gate band). No §44b TDM
reservation. `reports/census.md` published. (Full detail retained in git history.)

### A0 — Repo scaffold (2026-07-28) ✅

Scaffold, `legal.py` (§70/§71 registry), `db.py` (7 tables). 27 tests green.

---

## Key numbers

| Metric | Value |
| --- | --- |
| Tests passing | **880** (2026-10-21, L1, in `.venv-cloud` with the `web` + `gt` + `release` extras; 859 at its pre-flight on main the same day); 866 (2026-10-21, K2, in `.venv-k1`; 859 at W6 the same day in `.venv-cloud` with the `web` + `gt` + `release` extras, 856 at its pre-flight; 841 at K2b, in `.venv-k1` with the `bench` + `gt` + `kurrent` extras: 807 at the pre-flight, +18 parser, +5 set, +11 metric; 808 after W5, with the `web` + `gt` + `release` extras; 704 after K1, in `.venv-k1`; 644 after W4, 634 after S1, 621 after P1 Task 2, 606 after C2b, those with the `gt` + `web` + `release` extras) |
| **K2 German ground truth (2026-10-21)** | the Bern reader `trocr-kurrent-xvi-xvii` over **310,831 lines** on 4,807 pages of the 2,148 German records (7 h 26 min, 87 ms a line, fp32 + kv cache, batch 16; every Dresden reading as the checkpoint's defaults'); at the factory's gate **v1 10.8 % → Bern 16.9 %** of the lines (Leibniz's own hand 9.5 → 12.5 %); the rule: 1,178 pieces to the reader, 402 kept by v1, 568 none; the write (run 609): **`gt_lines` 315,797 → 333,680** (50,720 reader rows) · **German records 42,278 → 60,163** · Leibniz's own hand 1,888 → 2,612; the 200-line sheet half his hand, half the others, awaiting a judge |
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

**W5 (2026-10-10): ✅ live — merged as #42 and deployed on 2026-10-10, the
index rebuilt and the letters fetched overnight (the W5 entry has the record).
Steps (1) to (6) below are done; (5), the re-mint, on 2026-10-20 (C2c, on
`c2c-remint`).** The operator's order, as it was: (1) Open a pull request from the branch and read it; put it on
staging (`staging.sh claude/amazing-mayer-y6i9g0`) and look: a search for
two words, `LH IV, 6, 18 Bl. 1r` in the search box, a page's Cite box and
`#L3`, `/letters` (empty until step 4), a work page's record links. (2) Merge;
the §9 update on the box. (3) Rebuild the index on the server (`leibniz index
build --backend meili`, an evening): it writes `meta_folded`, folds the
twins and writes `<store dir>/leibniz_pages.twins.json`; restart the app.
`leibniz index settings` alone is not enough (it refuses an index without
`meta_folded`). Staging's own index, if rebuilt, writes its own twins file.
(4) `leibniz catalog letters --db /var/lib/leibniz-legible/inventory.sqlite`
on the server as the service user (about 1,550 requests at one a second;
resumable) writes `letters.json` beside the store; restart. (5) On the
desktop, before C3: `leibniz align edition-cache` again (it now records the
pieces per record); back the store up; `leibniz align gt-reset` (deletes the
lines the factory minted, keeps imported ground truth — a re-mint alone would
leave the old lines of records the new rules no longer mint); the six shards
without `--resume`; then `audit-reach`, `gt-report`, and `philiumm-vi4`
match/compare; read the counts before quoting any. (6) Read `/api/stats` (`scans`, `lines_once`, `twins`) and
spot-check twins (Open questions #26) before the About page's figures are
quoted anywhere.

**K1 (2026-10-09): done on the desktop; gate for K2: GO with
`trocr-kurrent-xvi-xvii`.** The branch `claude/dazzling-hopper-uxji2x`
carries it (compare:
https://github.com/marchofhares/leibnizlegible/compare/main...claude/dazzling-hopper-uxji2x?expand=1);
**merged into main on 2026-10-09 (pull request #41, merge commit
`9c96c7f`)**, nothing deployed: K1 changes nothing the website runs (checked
from a cloud session: the web extra resolves to the same packages and `leibniz
serve` starts without the `kurrent` extra). Read first: the gate verdict and the Task 4 bullet in
the K1 entry, `reports/kurrent/census.md` (the German pieces and the mint
check), `reports/kurrent/bootstrap-candidates.md` (the Dresden ranking and
the licences table), `reports/kurrent/pilot.md`. Keep `data/kurrent/`:
`german_pieces.jsonl` is K2's input, `pilot-readings/` and
`pilot-side-by-side.html` are the pilot's evidence, `smoke/` the Dresden
readings. The operator's look at the side-by-side page is recorded verbatim
in `reports/kurrent/pilot.md` (commit `d75cb5a`): "Yes, Partly."

**The Kurrent path after K1, as proposed to the operator (2026-10-09; not
yet scheduled).** (1) *K2, German ground truth:* read the German pieces'
lines (`data/kurrent/german_pieces.jsonl`) with `trocr-kurrent-xvi-xvii`
into JSONL beside the store, as the pilot did, and mint from those readings
into `gt_lines` with a source string naming the reader. `lines` is not
touched, so K2 needs no versioned-rows decision. (2) *K3, a Leibniz Kurrent
model:* fine-tune on K2's German lines and evaluate on page-disjoint
held-out German lines; compare a TrOCR fine-tune from the Bern model with a
kraken fine-tune from the PHILIUMM checkpoint with a German codec (ß,
umlauts, long s), by accuracy and by speed (the pilot timed
`trocr-kurrent-xvi-xvii` at 353 ms a line against 17 for `philiumm`). An
honest German CER needs a hand audit of minted German lines by a reader of
Kurrent (PHILIUMM has none), or the GWLB Transkriptionspool as an
internal-only test set (nc bucket, SPECS §1.4 and §7.3). (3) *German on the
site:* `lines` is unique on `(page_id, line_seq, run_id)` and every reader
of the store (viewer, index, exports: `latest_lines`) shows the newest run,
so a second reader's text can be added as a new run without touching v1.
Two decisions first: which pages are German beyond the edition pieces (a
language pass over the v1 text, checked against the census's German
pieces), and which reading wins per line once C4 adds a newer Latin and
French run, since the newest-run rule would cover a German line's Kurrent
reading with v2's. Then a new serving copy and an index rebuild, as for M1;
the search fold already maps ß to ss and drops umlauts. The About page and
llms.txt keep calling German unmeasured until K3 measures it.

**The operator's choice (2026-10-09): the letter-pool route for the honest
German test set**, not a hand audit: the GWLB's checked transcriptions of the
correspondence of 1708–1716 (for example "Transkriptionen des
Leibniz-Briefwechsels 1714 für die Leibniz-Akademie-Ausgabe (überprüft)", one
PDF a year on the Leibniz-Archiv's repository pages at gwlb.de; CC BY-NC 4.0,
so nc bucket, internal evaluation only, SPECS §1.4 and §7.3). An audit by a
reader of Kurrent stays possible later, as a check on the ground truth itself.
The path is now four steps with prompts on the operator's plan page: **K2**
(German ground truth on the edition pieces), **K2b** (the letter-pool test
set; independent of K2), **K3** (training both candidates; the reader for K4
is the operator's choice on K3's numbers) and **K4** (German on the site: the
language pass, a precedence rule so that a German page's Kurrent run outlives
C4's newer unscoped run, the re-read, a new serving copy and index). Found
while writing them (a cloud session, nothing run on the store): (a) every pool
letter's "Überlieferung" block names its witness's siglum (L Leibniz's own
hand, l his scribe, K the correspondent's own hand, k the correspondent's
scribe) and its shelfmark with leaves ("LBr. 164 Bl. 31–32"), so the C2
resolver can place it; it also notes a second text on the same leaves ("Auf
Bl. 4 vo L von N. 69"); the PDFs' text layer decomposes umlauts, so NFC first.
(b) A reader tag in the factory's source string must stand before "katalog":
`audit_reach.parse_source` reads the record id up to ")" or a space, so
"katalog 41800; reader …" parses as "41800;" (checked). (c) The re-mint before
C3 runs the factory without `--resume`, and `write_pairs` replaces every row
of a piece's line refs, so a K2 mint in `gt_lines` needs a guard in the
factory or the re-mint undoes it; the K2 prompt adds one. (d) GPU time,
estimated: re-reading every German page (about 15 % of the 236,795 pages)
takes a Kraken-speed model one to two days rather than under one: the model
reads a line in 17 ms, but the C1 recogniser kept about 940 pages an hour with
the images read from D:. The Bern reader takes more than a week.

**The final merge: ✅ merged and live** (pull request #40, merge commit
`62711b3`, the evening of 8 October in New York, 2026-10-09 UTC), after the
scored audit had gone to the PHILIUMM team and the staging look was done.
Done the same evening, in order: main fast-forwarded on the desktop; the
§9 update on the box (code only, `/healthz` ok); the seven checks against
the live site, as on staging; `/opt/leibniz-legible/deploy/staging.sh
--main`, staging on main at `62711b3`. The live site now carries C2b, P1
(Tasks 1 and 2), S1 and W4. From here: K1 on the desktop, continuing on
`claude/dazzling-hopper-uxji2x` and into a new pull request; every later
web step goes to staging with `/opt/leibniz-legible/deploy/staging.sh
BRANCH` (the live checkout carries the kit now) and back with `--main`.

**W4 (2026-10-08), operator — the staging look, in WSL, before anything
merges.** The SSH target and the staging user name are on the plan page,
not here.

1. ✅ Done 2026-10-08, evening. Put the branch on staging:
   `ssh <target> sudo /opt/leibniz-legible-staging/deploy/staging.sh claude/dazzling-hopper-uxji2x`
   (it fetches, syncs the venv, restarts the staging unit, prints `/healthz`
   and the address; paste the output back).
2. ✅ Done the same evening, every answer as expected (record 41800: 84
   recognised lines on its 2 pages, mean confidence 0.96). Over HTTP, each
   line asks for the password once; the expected answer is after the arrow:
   - `curl -su USER https://staging.leibnizlegible.com/page/00068221:0043 | grep -c 'The machine reads it as'` → `1` (the server-rendered text is still there);
   - `curl -su USER https://staging.leibnizlegible.com/api/records/41800/text | head -16` → a `# ` header beginning `# Leibniz Legible`, with `# Catalogue record: 41800 — [Praefatio operis ad instaurationem scientiarum]`, `# Akademie-Ausgabe: AA VI,4 N. 109`, `# Work: https://staging.leibnizlegible.com/work/00068642`, `# Folios: Bl. 1 (from the shelfmark LH 4, 6, 18 Bl. 1): 2 pages, canvases 1–2, …` (the live work's records, read from the live API on 2026-10-08: 41800 is on Bl. 1, 59095 "De cognitione" on Bl. 2);
   - `curl -su USER https://staging.leibnizlegible.com/api/records/41800/text | grep -c '^## Folio'` → `2`;
   - `curl -su USER 'https://staging.leibnizlegible.com/api/records/41800/text?format=tsv' | sed -n '/^line_id/p'` → the TSV column row;
   - `curl -su USER https://staging.leibnizlegible.com/api/works/00068642 | grep -o '"text_url": *"[^"]*"'` → two `text_url` values, `/api/records/41800/text` and `/api/records/59095/text`;
   - `curl -su USER -o /dev/null -w '%{http_code}\n' https://staging.leibnizlegible.com/api/records/nope/text` → `404`;
   - `curl -su USER https://staging.leibnizlegible.com/robots.txt | grep records` → `Allow: /api/records/`;
   - `curl -su USER https://staging.leibnizlegible.com/llms.txt | grep -c '/api/records/{record_id}/text'` → `1`.
3. ✅ Done the same evening, the browser look good. In the browser, with the password: `/page/00068221:0043` — the Text block
   under the line list, Copy (then paste somewhere: 108 lines, nothing
   else), "Download this page as text", "Text of this page" in the header;
   drag across two lines of the line list and copy: the two lines alone;
   `/work/00068642` — "Text of this piece (Bl. 1)" under the Praefatio
   record and "(Bl. 2)" under De cognitione, each a download; DE; `/about`,
   the transcriptions paragraph. Phone width if a phone is at hand.
4. Anything wrong: say so in a session; it fixes it on the branch and the
   `staging.sh` line runs again. Nothing merges here; the final merge is
   the plan's own step, after the emails and this look.
5. The three sentences for David are in the hand-over (and in the session's
   `scratchpad/david-text-access.md`); say "on a preview" or nothing about
   where.

**S1 (2026-10-08): ✅ staging installed and verified** (the S1 log has the
run, the first failure and the fix). Standing, for every web step from now
on: push the branch, then
`ssh <target> sudo /opt/leibniz-legible-staging/deploy/staging.sh claude/dazzling-hopper-uxji2x`
(after the final merge, `/opt/leibniz-legible/deploy/staging.sh`), look at
`https://staging.leibnizlegible.com` with the password, and only then merge;
`staging.sh --main` after the merge. A new password:
`/opt/leibniz-legible-staging/deploy/staging-install.sh --password`. The
kit clone `/opt/leibniz-legible-kit` is no longer needed (`rm -rf`). Never
send a staging link to anyone. Next step of the plan: W4, text access, on
this branch.

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

**C2b (2026-10-07), operator — in this order:**

1. ✅ Done 2026-10-08: the score against the store reproduced 72.3 %; the
   reach census ran (minutes) and its reports are committed (`bd01eef`).
2. ✅ Done 2026-10-08, evening: the scored report (`reports/gt-audit.md`)
   went to Denisa and David with the reply to their notes of 7 October.
   They have seen the score first, so the merge is no longer held by it.
3. ✅ Done 2026-10-20 (C2c; the C2c entry has the numbers). **Before C3, once:** the re-mint with hyphens kept. The factory is
   idempotent and the aligner's default is now `keep_hyphen=True`, so it is
   the C2 runbook line **without `--resume`** (resume skips every piece
   already minted): six shards of
   `uv run leibniz align factory data/gt/edition_cache.jsonl --shard $i/6`
   under nohup, about two hours; then `leibniz align gt-report` and
   `leibniz align audit-reach` again (the hyphen share should drop to the
   lines whose HTR read no mark). Do it after P1 has produced
   `reports/philiumm/heldout_pages.csv`, so one re-mint carries every C2b
   flag.
4. Offer PHILIUMM a second judging round on a fresh 200 of the re-minted
   lines (`audit-sheet --seed 1`), same CSV shape. The sheet exists since
   2026-10-20: `reports/gt-audit/round2/gt-audit.html` (on the desktop; not
   committed, like the first round's), the operator's to offer.

**W3 fix (2026-10-06), operator:** merge `web-versioned-modules`, then the §9
update on the VPS — code only. Then, over HTTP: the shell of any page names
`/static/m/<12 hex digits>/app.js` and no `"/static/app.js`; that address and
`/static/m/<the same>/i18n.js` answer 200; `/browse` and `/api/works` answer
as before. In the browser you used earlier that day, with no hard reload:
`/browse` works and the nav reads "Browse", and on `/work/00068539` the first
catalogue record reads "Sender: Leibniz", "Addressee: Danckelmann, E." (no
"(GND)" anywhere) and ends "The catalogue record itself links to this scan ·
confidence 1.00".

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

**W2 (2026-10-02), operator:** ✅ live (checked 2026-10-06). After merging, the §9 update on the VPS — code
only: no index rebuild, no Meilisearch restart, no new dependency. Then on
the box: `deus` and `deus mundus` report what they did (10,450 and 97,633),
`"deus mundus"` far fewer, `deus -mundus` fewer than `deus`. Readers may see
the old hint for up to an hour (the imported modules keep plain URLs).

**W1 (2026-10-02), operator:** ✅ live (checked 2026-10-06). After merging `web-overlay-text-export`, the
§9 update on the VPS (`deploy/README.md`), then the checks in the W1 log:
both text endpoints answer `200` with a `# ` header, and the overlay
one-liner prints `hidden | Show line overlay`. Optionally tell the reader at
the Leibniz-Edition that both reports are answered.

**Phase D is built on v1 and deployable (2026-09-16); the operator runs the
runbook.** `deploy/README.md`: `deploy/prepare-store.sh` on the desktop,
`install.sh` on a small VPS, `leibniz index build --backend meili` (one pass,
an hour or two), `leibniz index bench` against the 500 ms p95 criterion, the
courtesy note to the GWLB before launch, then `leibniz release export` + the
checklist for the dataset uploads.

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
