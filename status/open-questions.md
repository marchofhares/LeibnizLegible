# Open questions — Leibniz Legible

_The whole "Open questions" section of STATUS.md, moved verbatim by ARCH2 on 2026-11-19, the numbers intact. This file stays live: numbers are permanent; a new question takes the next free number, gets its full text at the top of the list here and one line in the index in `STATUS.md`; an answer or a restatement is written into the question's own text here, and its index line follows._

## Open questions

36. **R1: two things Part B decides before it measures (2026-11-17).** (a)
    **PHILIUMM's dataset has no test split** (`train_clean`, `train_noisy`,
    `val`; LT1's finding of 28 October). R1's prompt tunes the LM weight
    and the beam "on PHILIUMM's validation split only" and reports "on
    PHILIUMM's test split"; tuning and reporting on the same 1,878 lines
    would flatter the decoder by whatever the tuning fits. Proposed: split
    `val`'s 27 pages once, by page and by seed, into a tuning half and a
    reporting half, report the greedy number of the whole split beside
    both, and say so in `reports/decoding/r1-decoding.md`; the same split
    then serves the temperature fit of Task 4. The alternative, tuning on
    a slice of `train_clean`, is worse: the model was trained on those
    lines and its posteriors there are sharper than on unseen pages. (b)
    **Which text the language model should see.** The C3 amendment of 16
    September (PROMPTS.md, point 4) says to train the model "on diplomatic
    GT, never on edition text, or it will push toward expansions"; R1's
    prompt names the edition's reading text and the aligned lines, which
    are edition text too. `lm-build` follows R1's prompt and can build the
    two variants that answer the worry — `--fold align` (case, accents,
    u/v, i/j and punctuation out of the model, so that it weighs letters
    and not conventions; its known weakness: punctuation is the unknown
    token) and `--sources gt` (the minted lines alone, which at least are
    lines) — and `--extra` takes diplomatic text of the operator's choice
    (PHILIUMM's `train_clean` text is CC BY 4.0 and diplomatic, but its
    pages are among the held-out pages whose aligned lines Task 3 reports
    on, so it cannot serve that set). The validation half decides; the
    prompt's own rule covers the case that none of them earns a quarter
    of a point. Also for Part B: whether the readers' codecs are NFC or
    NFD (`bench lm-tokens` says), and that K3's stored TrOCR figure is the
    mean probability of the generated tokens, not a sequence score.
35. **What the first releases publish beyond the lines (2026-11-18, REL1
    Part A; the operator's before Part B's step 9).** (a) *The catalogue
    records.* D1 rides inside the transcriptions record, and its
    `katalog_records` table is the store's catalogue records as they are:
    the 24,916 read from the catalogue's website, or, once A3b's import is
    written, the Arbeitsstelle's whole export of 70,405. The licence is
    settled (CC BY 4.0 in writing, 2026-10-12) and the card carries the
    registry's credit; republishing the whole catalogue as a table in a
    Zenodo record is still a larger step than showing it on the site, and
    SPECS §7.7 says to ask where a partner might wince: a line to the
    Arbeitsstelle before publishing is the operator's call, as is leaving
    the table out of this version (the crosswalk alone names the record
    ids). (b) *The creators.* The four report records name one person with
    an ORCID; the datasets' deposit files default to the project's name and
    take `--creator` at Part B. (c) *The Hugging Face namespace*, proposed
    `leibniz-legible`; the organisation is the operator's to create. (d)
    *The resource type "Model"* is set in the browser: the deposit API takes
    no such upload type.
34. **"No NC input" and the training lines in the NC-derived deposit
    (2026-11-18, REL1 Part A; to be read before the model is published).**
    The registry's `model-k3-trocr` row says the model has no NC input and
    is CC BY 4.0 (the owner, 2026-10-21): the Bern model is MIT and K2's
    lines are open-bucket edition text. The same row lists `edition-potsdam`
    and `edition-gwlb` among its inputs, and the lines read through those
    channels are released in `leibniz-gt-nc` under CC BY-NC 4.0. Both are
    the owner's scheme (§70-free reading text is open whatever copy it was
    read from; the NC terms sit on the files), and a reader who holds the
    model card beside the NC deposit's card will see the two side by side.
    The model card therefore says it in plain words and names the
    lawyer-memo question (checklist §6, "NC terms on a PDF and reading text
    free of § 70"), taking no position; how many training lines came
    through each channel is not in a committed report (`k3-trainset.json`
    counts by reader, hand and stratum, not by channel). The operator's to
    decide before publishing: release as the registry says with that
    sentence; or CC BY-NC 4.0 for this version until the memo answers; or a
    retrain on the `ia` lines alone (K3b). The readings on the site carry
    the same question in a weaker form (machine output of the model).
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
    **Restated 2026-11-17 (K3b-prep): the tools are built; the numbers are
    K3b's Task 0.** (a) Answered by `leibniz align audit-convert` and
    `audit-score --corrections`: the strict reading and the precision under
    the fold, by stratum and by hand, with Wilson intervals; what stays open
    is the figure itself and whether the factory's threshold is the right line
    between "right under the fold" and not (a corrected line at or above it is
    as close to the minted text as the factory asks of a reading). (b)
    Answered by the registry entry `edition-k2-audit` and `leibniz align
    audit-apply`; open: the credit wording, and with it the credit line on the
    dataset card and `gt-open`'s inputs (REL1). (c) Answered by `leibniz align
    audit-sheet-k2`: `--context N` for the next sheet, `--refs` for a page of
    the two lines that asked for a larger excerpt and the French line of
    record 59196; per-line language stays Open question 31's. (d) New: a
    re-mint replaces a record's rows, verified ones included, so `kurrent-mint
    --write` over a record with verified lines would drop them; `audit-apply`
    run again restores the corrected lines and leaves a confirmed line whose
    text changed. Whether the factory gets a guard for verified rows, or K3b
    simply never re-mints those records, is K3b's to decide.
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
    fair copy). **2026-11-17, G1b** (the G1b entry in the Phase log; the
    commands under Next): **(g) answered** as the plan page's G1 row says —
    the gold is drawn first, among all the eligible lines, up to the caps,
    spread over the strata, and the strata are filled around it;
    `--bad-gold-share` defaults to 0.5, so that an always-Bern strategy
    shows (e). Whether the supply reaches 500 is the rebuild's "Gold supply"
    line. **(h) answered**: `--min-ratio` 0.5 skips a pair whose shorter
    reading is under half the longer (`lopsided`); the rebuild prints how
    many. **(i) stays the operator's**, served by `--strata` (weights by
    stratum, e.g. `fair_copy=0.35,light_revision=0.35,heavy_revision=0.2,
    scrap=0.1`; a stratum left out gives no row); without it the allocation
    is equal, as in the first pack. **(j) New, the operator's to answer
    before the rebuild — whose reading is the first candidate?** The pack
    pairs "the reading the store shows" with the Bern reading. On 21 October
    that was v1's on every German page; since K4's run 617 it is k3-trocr's
    on the pages that run read. Three ways: *(1) today's store, the default*
    — k3-trocr against Bern where K4 read the page, v1 against Bern
    elsewhere: the pair that concerns what the site shows, and the one an
    imported judgment can honestly replace; k3-trocr reads German better
    than v1 (28.6 % against 46.6 % CER on the letter pool), so more pairs
    should hold a right reading. But the gold comes from K2's mint and K3
    trained k3-trocr on K2's mint: on gold rows the stored reading is a
    reader on its own training lines, so it will be right there more often
    than on the other rows, pairs where both readings are right fall out
    (the same text, or "both" under the fold), and a player's score on gold
    will overstate their score on the rest. *(2) `--as-of-run 616`* — the
    store as it stood before K4's reading (616 is K4's `page_lang` run,
    which wrote no line): v1 against Bern, the first pack's pairing, its
    gold untouched by either reader's training; but the judged pair is then
    not the text the site shows on those pages, and importing its winner
    would lay a `corrected` row over k3-trocr's reading on the strength of
    a comparison k3-trocr was not in — a pack for calibrating the game, not
    for import. *(3) not built* — today's store with gold only from lines
    K3 kept out of training (its validation split, the audit lines), which
    needs K3's manifest as an input: a small session if (1)'s gold proves
    too easy. This session's recommendation: build (1) and (2), six and a
    half minutes each, read the two supply lines side by side, and send (1)
    to the game with the caveat on its gold unless its supply is thin; the
    choice is the operator's and the game session's (CAL1). **2026-11-18:
    way 3 is built, as the operator asked it** — `--only-records
    reports/kurrent/k3-val-pieces.csv` draws the whole pack, rows and gold,
    from K3's 98 validation records, which the reader was not trained on
    (K3 held them out for validation), so on today's store neither the gold
    nor the other rows are the reader's training lines. What it costs is
    the pool (98 records; fair copy on 2 and scrap on 3 of them), so the
    pack may be small and its gold under the cap: the rebuild prints both.
    The three rebuild lines stand side by side under Next.

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
