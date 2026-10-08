# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-10-08 (**S1, the staging site: the kit is on the branch and tested; the install on the box is the operator's**; earlier the same day, **C2b, the census run on the store: a quarter of the minted ground truth is in Leibniz's own hand, 7,822 lines lose their hyphen to the mint, the addition proxy marks 83 % of lines and is useless; 2026-10-07, C2b: the PHILIUMM team's 200-line audit scored and read** — corpus-weighted precision 72.3 % as written, 92.2 % with boundary slips counted usable, one misaligned line in 185 scored; the patterns behind the verdicts named and measured, the dropped line-end hyphen fixed in the aligner, the reach census built for the operator's run, the C3 prompt amended; 2026-10-06, later the same day, a fault found live after W3's deploy and its fix: the viewer's ES modules are served as one versioned set, so a deploy can no longer pair a new `app.js` with cached old modules; W3: a browse page — the Nachlass by shelfmark family, section and convolute at `/browse`, `GET /api/works`, a breadcrumb from every work page back to its section; 2026-10-02 — W2: search reads "quoted phrases" and -exclusions, and the hint under the box says so and what exact matching misses; earlier the same day, W1: the line-overlay toggle fixed, plain-text export per folio and per work, content-hashed viewer assets; earlier: 2026-09-27 — room for Calculemus on the host, flagged off; 2026-09-23 — discoverability, About page, duplicate sheet-sides; 2026-09-16 — **Phase D built on v1 — search index, API, IIIF v3 + annotations, viewer, release exports; reports + project statement published on Zenodo; strategy review recorded in `NOTES.md` and the C3 prompt amended. C2 stands as closed on the mint with the precision gate deferred to C3. Later the same day: the deployment kit (`deploy/`), public-traffic hardening of the app, `LICENSE` + issue form for the repository going public.**)._

---

## Current state

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
built beside the live one. 634 tests, ruff clean. The operator's commands
are under Next; the first run on the box is the kit's first real test.

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

### S1 — a staging site on the VPS (2026-10-08) ✅ kit built and tested · ⏳ the install (operator)

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
- **Next.** The install (Next); then W4, verified on staging.

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
| Tests passing | **621** (2026-10-08, P1 Task 2; 616 after Task 1, 606 after C2b; with the `gt` + `web` + `release` extras) |
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

Legal registry (A0, unchanged): 42 entries; 32 free today.

---

## Open questions

22. **The browse index wants two authorities (2026-10-06, W3).** (a) *LH section names* are cut from the GWLB's titles: LH 11 reads "Allgemeinen Geschichte" (the title's dative), LH 9 "Archälogie" and LH 15 "Würtemberg" (the library's spellings), LH 37 and LH 42 have no name (their titles name sub-groups), and the twelve sections without a digitized unit are absent. A reviewed table of the 42 section names would settle all four; the question to the Leibniz-Edition is whether the grouping matches how the Arbeitsstellen think of the Faszikel. (b) *Correspondents*: 380 of the 1,060 letter convolutes are unnamed (316 without linked records, 4 whose records name nobody, 60 whose names do not fit the order of the LBr numbers). A full Arbeitskatalog export completes them with no code change. The order check cannot see a wrong name that happens to fit alphabetically, and the F series has no order to check against; a reader who knows the convolutes should look over the named ones once (`/api/works?family=LBr`).
21. **Fold the metadata fields in the Meilisearch index (2026-10-02).** Titles, shelfmarks, AA references and folio labels are indexed as written, so a quoted reference finds nothing (W2), and even unquoted a Roman numeral with V or J never meets its folded form: *VI* is sent as *ui* and no typo is allowed under four letters. Measured on 1.53.2: `VI` does not find a page whose only VI is in `AA VI,4 N. 109`, and `AA VI,4 N. 109` finds it only through the bare *aa*, below an unrelated page whose text has *aa*. FTS5 folds those columns. Index folded copies at the next rebuild (C4) — a rebuild drops and refills the index, so not in a routine deploy.
20. **Multi-word queries on Meilisearch are not AND (2026-10-02).** `meili.py` sends no `matchingStrategy`, so Meilisearch's default `last` drops words from the end of the query when results run short and typo-matches the first word left: live, `deus mundus` reports 97,633 hits (at result 8,900, 98 of 100 hold neither word — French *des*) and `mundus deus` 3,775, where FTS5 requires every word. `matchingStrategy: "all"` would make the backends agree and the counts honest, at the cost of pages where a word was misread past typo tolerance — a product decision, open. Quoted phrases and exclusions hold under either strategy.
19. **Sheet-sides registered twice (2026-09-23).** Static-JPEG works list one scan of an unfolded sheet under two folio labels; the corpus run read each twice. Run `leibniz images duplicates` over the thumbnails, publish the distinct-scan count, fold twins in the index build, and restate `pages`/`lines` on the About page.

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

**S1 (2026-10-08), operator — the install, in this order:**

1. ✅ Done 2026-10-08 (the figures are in the S1 log). The read-only look at
   the box, for the record:
   `ssh <target> 'free -m; df -h /var/lib/leibniz-legible /var/lib/meilisearch /opt; systemctl is-active leibniz-legible meilisearch caddy; caddy version; tail -2 /etc/caddy/Caddyfile; ls /etc/caddy/conf.d'`
2. DNS: ✅ the `staging` A record exists, DNS only; an AAAA record too if the
   box has IPv6.
3. ✅ Installed 2026-10-08 (user `evanatlas`): the first run stopped at the
   Caddy reload (the S1 log says why), the re-run with the fixed kit went
   through. The re-run line, which keeps the password:
   `ssh -t root@49.13.13.213 'sudo git -C /opt/leibniz-legible-kit pull --ff-only && sudo /opt/leibniz-legible-kit/deploy/staging-install.sh --user evanatlas --branch claude/dazzling-hopper-uxji2x'`
   The first run's line, for the record, with NAME the user name:
   `ssh -t <target> 'sudo git clone --branch claude/dazzling-hopper-uxji2x --depth 1 https://github.com/marchofhares/LeibnizLegible /opt/leibniz-legible-kit && sudo /opt/leibniz-legible-kit/deploy/staging-install.sh --user NAME --branch claude/dazzling-hopper-uxji2x'`
   Expected, in order: no precondition message; `cloned … (claude/dazzling-hopper-uxji2x)`;
   `wrote /etc/leibniz-legible/staging.env …` with seven lines under it;
   `== caddy: … (basic_auth, user NAME)` then Caddy's `Valid configuration`;
   `== staging ← claude/dazzling-hopper-uxji2x`, uv's sync lines,
   `{"status":"ok","version":"0.1.0","store":true,"search":{"backend":"meili","ok":true}}`,
   `staging runs claude/dazzling-hopper-uxji2x at <sha> — <subject>`;
   `https://staging.leibnizlegible.com/ answers 401 without credentials`.
   If the certificate is not there yet the last line says so and
   `journalctl -u caddy -n 20` shows it being obtained.
4. ✅ from the cloud session, 2026-10-08: `401` over a valid certificate
   without credentials, the live site `200`. Still the operator's: the
   on-box line `ssh <target> 'systemctl is-active leibniz-legible-staging; curl -s http://127.0.0.1:8001/healthz; echo; curl -sI https://staging.leibnizlegible.com/ | head -1'`
   → `active`, the healthz line above, `HTTP/2 401`. In the browser, with
   the password: `/browse` on staging matches production, and
   `curl -s https://leibnizlegible.com/api/stats` and
   `curl -su NAME https://staging.leibnizlegible.com/api/stats` report the
   same figures (the same index).
5. From now on every web step ends with
   `ssh <target> sudo /opt/leibniz-legible-staging/deploy/staging.sh <branch>`
   (after the final merge, `/opt/leibniz-legible/deploy/staging.sh`), and
   `--main` after the merge. `rm -rf /opt/leibniz-legible-kit` once the
   install is done; the staging checkout carries the kit.
   If anything fails, paste the output into a session: the fix goes into the
   kit on the branch and the install is re-run (it is idempotent).

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
2. Send Denisa and David the five-line summary (the session's hand-over)
   with `reports/gt-audit.md` attached; then merge. They judged the lines;
   they see the score first.
3. **Before C3, once:** the re-mint with hyphens kept. The factory is
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
   lines (`audit-sheet --seed 1`), same CSV shape.

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
for the Reihe VIII reading text. Next phase: K1, from a fresh session on the
merged main.

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
