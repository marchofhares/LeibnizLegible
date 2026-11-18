# Release checklist — datasets, model, reports (Phase D3)

_The operator's upload runbook. `leibniz release export` stages everything under
`data/release/`; this file says what to check before each upload and where it
goes. Regenerate the exports after every corpus run (new `run_id`) — the cards
and `MANIFEST.json` carry the counts and checksums of that run._

## 0. Decision record

- **2026-09-16 (operator):** releases are **not** gated on the §8 correspondence
  (GWLB, PHILIUMM, TELOTA) or the §7.5 lawyer memo. Both remain recommended and
  are tracked in `STATUS.md`; neither blocks an upload. Recorded here so the
  divergence from SPECS §7.5 is explicit, not silent.
- The public web app (D2) serves its own mirror of the GWLB delivery scans (every page links to its original) and carries only machine text plus
  §70-expired reading text; it is the lighter surface and ships first (v1).

- **2026-11-16 (operator, REL1):** the first releases are four Zenodo records in
  the `leibniz` community — `leibniz-transcriptions` with the inventory (D1)
  inside it, `leibniz-gt`, `leibniz-gt-nc`, and the German reader under the public
  name **`leibniz-kurrent-trocr`** — with a Hugging Face mirror of the first two
  open ones and the model. The namespace of the mirror was left open; REL1 Part A
  proposes `leibniz-legible` (no public profile of that name on 2026-11-17).

## 1. Export

```bash
uv sync --extra release                    # pyarrow, huggingface_hub
leibniz release export --db <store> --out <root>   # inventory + transcriptions + gt + gt-nc (Parquet)
leibniz release export --format jsonl      # JSONL.gz mirror, if wanted
leibniz release check --out <root> --stats stats.json   # the checks below, PASS or FAIL
leibniz legal licences                     # the registry every card's licence line comes from
```

_Since REL1 (2026-11): the export opens the store read-only and streams the lines
(a Parquet batch in memory, no sort of the table); the transcriptions folder
carries the four inventory tables beside the lines (D2 with D1 inside it: one
record), `leibniz-inventory` staying exportable on its own as the repository's
copy; `MANIFEST.json` carries every count a card quotes; `RELEASE.json` at the
root holds the reserved DOIs, the Hugging Face namespace and the creators, and
`leibniz release cards --out <root>` re-renders every card and deposit file from
the manifests, without the store. `<root>` is a dated folder
(`/mnt/d/leibniz-release/YYYY-MM-DD`)._

Each dataset directory holds `MANIFEST.json` (files, row counts, SHA-256, git
SHA, generator, the counts) and `README.md` (the dataset card, with the Hugging
Face front matter above it). `leibniz release check` runs these and prints one
line each; `stats.json` is the site's `/api/stats` saved to a file:

- [ ] `MANIFEST.json` row counts match `leibniz pipeline status` / `align gt-report`;
      the lines and the lines by model match `/api/stats` (`lines`, `models`).
- [ ] `leibniz-transcriptions`: no row has `source.license_bucket == "nc"` (the
      exporter drops them); every line carries `model`, `run_id` and `status`.
- [ ] `leibniz-gt` (the open deposit, CC BY 4.0): every row `license_bucket ==
      "open"` and every row's `source` names `channel ia`, `channel
      edition-k2-audit` (the Edition's corrected lines, once in the store) or no
      channel; the card's "Licence" section lists the channels and their line
      counts, and says how many lines went to the other deposit and how many to
      neither.
- [ ] `leibniz-gt-nc` (the NC-derived deposit, CC BY-NC 4.0, since 2026-10): every
      row's `source` names `channel potsdam`, `channel gwlb` or a joined channel
      containing one of them; the card names the Potsdam channel's licence as
      stated in writing (2026-10-12) and the GWLB repository's; **the two deposits
      are disjoint** (`gt_id` sets do not overlap) and together with the
      "released in neither" count add up to the store's `gt_lines`.
- [ ] Both ground-truth cards' Audit section states the audit as it stands: the
      first audit's precision (C2b: 199 of 200 judged, 72.3 % as written, 92.2 %
      usable) with its judge and the mint it was measured on; K2's sheet with its
      judge and its counts, its precision only by pointing at
      `reports/kurrent/k2-audit.md` once K3b has committed it; the verified lines
      counted from the export, or "follows in the next version". **Read the
      sentence**: it must not say "8 of 8 sampled lines" (until 2026-11 the test
      suite overwrote `reports/gt-audit/audit-summary.json`; the check command
      fails a card that does).
- [ ] The README of every dataset carries the attribution lines (the NC deposit
      also the edition-text line naming the Leibniz-Edition Potsdam and the GWLB
      Leibniz-Archiv), the "Licence" section quoting the registry, and the
      anti-contamination note ("machine output — do not ingest as verified text").
- [ ] The transcriptions card names both models per line (`model`, `run_id`) with
      the export's own counts, the German reader's three licences from the
      registry, K3's and LT1's numbers with what they were measured on, the
      language pass and its coverage, the Marginalien left to the first model, and
      the catalogue records' credit as the store's state warrants (the registry's
      line with the export's date where the Arbeitsstelle's export is in the store;
      "the records read from the catalogue's website" where it is not).

## 2. Zenodo (datasets)

One record per dataset, resource type **Dataset**, licence per the card
(`leibniz-transcriptions` CC BY 4.0, carrying the inventory tables under their
own lines: the project's tables CC0 1.0, the katalog records CC BY 4.0;
`leibniz-gt` CC BY 4.0; `leibniz-gt-nc` CC BY-NC 4.0, with the attribution to the
Leibniz-Edition Potsdam (BBAW) and the GWLB Leibniz-Archiv the card carries).
Community: `https://zenodo.org/communities/leibniz/`. The metadata is written by
the export into `<root>/leibniz-<dataset>.zenodo.json` and sent by
`tools/release/zenodo_deposit.py`; check it on the draft:

- [ ] Title as the card's title; version = the export's `generated_at` date.
- [ ] Description = the card's summary + attribution + the anti-contamination note.
- [ ] `related_identifiers`: `isSupplementTo` the code repository;
      `isDerivedFrom` doi:10.5281/zenodo.21457538 (PHILIUMM HTR model) and
      doi:10.5281/zenodo.21537859 (segmentation model) for the transcriptions;
      `isDerivedFrom` the PHILIUMM dataset (doi:10.5281/zenodo.21622297) and
      `isDocumentedBy` the retro-alignment report (doi:10.5281/zenodo.22782819)
      for both GT deposits; `isDocumentedBy` the project statement
      (doi:10.5281/zenodo.22782813) for all. The transcriptions' and the
      GT deposits' descriptions say that the model was obtained under CC BY 4.0
      and is published by its makers under CC BY-NC 4.0 since 2026-10-15 (the
      registry's wording, `leibniz legal licences --key philiumm-htr-model`).
- [ ] Keywords: leibniz, nachlass, handwritten text recognition, htr, iiif,
      digital humanities, ground truth, machine transcription.
- [ ] Creators: as on the project's four reports (one person with an ORCID):
      `leibniz release cards --out <root> --creator "Family, Given|ORCID"`; the
      default is the project's name.
- [ ] Reserve the DOI first (`zenodo_deposit.py reserve --root <root> --record
      <record>` writes it into `RELEASE.json`), re-render the cards (`leibniz
      release cards --out <root>`: each card carries its DOI and its siblings'),
      then upload (`zenodo_deposit.py upload …`: resumable, size and MD5 checked;
      it stops at the draft). **Publishing is the operator's click, after reading
      the draft**; the token needs `deposit:write` only.
- [ ] Hugging Face mirror (D2 with D1, D3's **open** deposit, the model; **not**
      `leibniz-gt-nc`, which is on Zenodo only — the upload script refuses it):
      `tools/release/hf_upload.py --root <root> --record <record> --namespace
      <ns>`; the same card as the README, `license: cc-by-4.0`, the Parquet files
      as they are; the repository is created private and made public by the
      operator when the DOIs are on the site.

## 3. Model

- [ ] **`leibniz-kurrent-trocr`** (REL1, 2026-11): K3's TrOCR model, READER of the
      German pages (`k3-trocr@runs-615-epoch-5`). `leibniz release model --weights
      <checkpoint> --out <root>` packages the inference files with README (K3's
      card brought to the finish), LICENSE (CC BY 4.0 per the registry's
      `model-k3-trocr`; the base model's MIT notice in full), `MANIFEST.json` and
      a zip. Zenodo: `isSupplementTo` the code repository, `isDerivedFrom` the
      Bern model (https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII),
      `isDocumentedBy` the project statement; the deposit API has no "model"
      upload type, so the draft is created as **Other** and the operator sets
      **Model** in the browser before publishing. Read on the card, before
      publishing, the sentence on what "no NC input" means (STATUS.md, Open
      question 34).
- [ ] `leibniz-htr-v2` weights + the finalized model card (`reports/htr-v2-eval.md`
      + data statement + per-stratum/per-language error rates + intended use +
      the "machine output, not an edition" framing), after Phase C3. Resource type
      **Model**, `isDerivedFrom` the PHILIUMM checkpoint, `isDocumentedBy` the
      project statement. **Licence per the registry** (`leibniz legal outputs`): a
      model fine-tuned from the PHILIUMM checkpoint (v2, K3's kraken candidate) is
      **CC BY-NC 4.0** — PHILIUMM publishes its models under CC BY-NC 4.0 since
      2026-10-15 and the owner honours the change for models built from theirs
      (2026-10-13); K3's candidates with no NC input (the TrOCR model from the
      Bern model, MIT; one from kraken's PP-OCRv6, Apache-2.0; both on K2's open
      edition lines) are **CC BY 4.0** if released (the owner, 2026-10-21). The
      model card names every training input with its registry key. Until then
      the Latin and French pages are read by PHILIUMM's model, which is theirs to
      release (and is: obtained under CC BY 4.0, CC BY-NC 4.0 since 2026-10-15).

## 4. Reports (D8)

Published 2026-09-16 on Zenodo, mirrored on evanatlas.com/research:

- project statement — doi:10.5281/zenodo.22782813
- corpus census (A1) — doi:10.5281/zenodo.22782815
- PHILIUMM reproduction + VLM benchmark (B1) — doi:10.5281/zenodo.22782817
- retro-aligned ground truth (B2–C2) — doi:10.5281/zenodo.22782819

New versions of a report are new Zenodo versions of the same concept record
(never a new record); update the mirrored manifest's DOI on the website.

## 5. After upload

- [ ] Write the DOIs into `README.md` (Status section) and `STATUS.md`: REL1's
      Part C, from the line `RELEASE.json` gives (one constant per record in
      `src/leibniz/web/attribution.py`).
- [ ] Add the dataset DOIs to the About page (`src/leibniz/web/static/`) and
      `llms.txt`; drop "(if released)" from the registry's `model-k3-trocr` row.
- [ ] Make the Hugging Face repositories public once the DOIs are on the site.
- [ ] Re-read the third-party records on the day (STATUS.md, Open question 29 f)
      and move the registry's "seen" dates.
- [ ] Announce to the §8 contacts (GWLB, PHILIUMM, TELOTA, Leibniz-Archiv).

## 6. Lawyer memo (SPECS §7.5): the questions

The memo is recommended before the first public dataset release and does not
gate an upload (§0). This is the list of questions as it stands; the project
records them and does not answer them (SPECS §7.7: relationship > rights).
Added 2026-10-21 (L1) unless dated otherwise.

- [ ] (SPECS §7.5) The §68 UrhG status of the scans (no related rights; BGH
      _Bibelreproduktion_).
- [ ] (SPECS §7.5) The §70/§71 volume math in `src/leibniz/legal.py`: the
      calendar-year rule, re-editions that restart the clock (II,1 2006), the
      editio-princeps assumption (STATUS.md Open question 6).
- [ ] (SPECS §7.5) The De Gruyter contract question: the edition's publisher
      and the NC term the BBAW's agreement carries (the head of the
      Leibniz-Edition Potsdam, 2026-10-12).
- [ ] (SPECS §7.5) NC-licensed material on monetised or advertising-bearing
      surfaces; database rights in the catalogue and in this project's tables.
- [ ] **Irrevocability for copies already obtained.** This project obtained the
      PHILIUMM HTR and segmentation models under CC BY 4.0 on 2026-07-29; their
      makers publish them under CC BY-NC 4.0 since 2026-10-15. CC BY 4.0 states
      its grant as irrevocable (§2(a)(1)) and a relicensing applies to copies
      obtained after it — does the copy held, and what was built from it before
      and after that date, stay under the terms it was obtained under? The
      owner has chosen to honour the change for models fine-tuned from theirs
      regardless (SPECS §7.7); the question matters for the record.
- [ ] **The status of model output under a weights licence.** Whether machine
      transcriptions produced by a model carry any licence condition of the
      model's weights (CC BY or CC BY-NC) at all; the transcriptions are released
      CC BY 4.0 with PHILIUMM's agreement either way.
- [ ] **ShareAlike reach (from K1, 2026-10-09).** Whether training on CC BY-SA
      4.0 ground truth (the Bullinger HTR data, not used so far) would make a
      model or its output ShareAlike; the same for a CC BY-NC-SA reading of the
      Dresden 1673 text (nc bucket, evaluation only).
- [ ] **NC terms on a PDF and reading text free of § 70.** The Potsdam
      Arbeitsstelle's Reihe IV PDFs (CC BY-NC 4.0 in writing, 2026-10-12) and the
      GWLB repository's volume PDFs (CC BY-NC 4.0) carry the constituted reading
      text of volumes whose §70 term has run out. Do the channel's NC terms reach
      that text, or only the file, its layout and the protected parts of the
      book? **If not, the NC-derived deposit (`leibniz-gt-nc`) opens up** and
      joins the open one; until then the lines are released under CC BY-NC 4.0.
      Alternatively those volumes can be re-sourced from other scans (IV,1 has
      one on archive.org).
- [ ] **Redistribution of lines derived from the Potsdam PDFs.** The
      Arbeitsstelle's statement of 2026-10-12 licenses the electronic texts of
      Series IV, V and VIII under CC BY-NC 4.0; the page notice seen 2026-10-10
      ("ausschließlich für nichtkommerzielle Zwecke") is not a CC licence and
      says nothing about derived data. Does the CC BY-NC grant cover the line
      pairs minted from the files (text projected onto manuscript line images),
      and what attribution does it ask for? The operator's reply of 2026-10-14
      stated the intended use and invited correction.
- [ ] **§ 71 UrhG (the first-publication right, 25 years).** Whether it reaches
      the machine text of pieces first published in recent AA volumes — the
      corpus transcription reads manuscripts whose text the edition published
      first, some within the last 25 years.
- [ ] **Data produced by GPL and AGPL tools beside an Apache-2.0 codebase.**
      YALTAi (GPL-3.0), ultralytics YOLO (AGPL-3.0) and, if its licence says so,
      dfine_kraken may be run beside the repository, never imported; what their
      licences say about the data they produce (segmentations, layouts) and
      about a service that runs them.
- [ ] **The Göttingen series (asked, October 2026).** The licensing of the
      series the Akademie der Wissenschaften zu Göttingen is responsible for (I,
      III, VII: the research director in Hanover; II, VI: in Münster) may differ
      from Potsdam's; the GWLB repository's Reihe I PDFs stay CC BY-NC 4.0 as
      published until an answer comes.
- [ ] **Kalliope (STATUS.md Open question 25).** A record per LBr convolute, no
      licence stated on the site; the participation contract grants CC BY-SA for
      the metadata. Not used; ask before harvesting.
