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

## 1. Export

```bash
uv sync --extra release                    # pyarrow
leibniz index build                        # refreshes the corpus statistics too
leibniz release export --out data/release  # inventory + transcriptions + gt + gt-nc (Parquet)
leibniz release export --format jsonl      # JSONL.gz mirror, if wanted
leibniz legal licences                     # the registry every card's licence line comes from
```

Each dataset directory holds `MANIFEST.json` (files, row counts, SHA-256, git
SHA, generator) and `README.md` (the dataset card). Check:

- [ ] `MANIFEST.json` row counts match `leibniz pipeline status` / `align gt-report`.
- [ ] `leibniz-transcriptions`: no row has `source.license_bucket == "nc"` (the
      exporter drops them; spot-check with a quick query on the Parquet).
- [ ] `leibniz-gt` (the open deposit, CC BY 4.0): every row `license_bucket ==
      "open"` and every row's `source` names `channel ia` or no channel; the
      card's "Licence" section lists the channels and their line counts, and
      says how many lines went to the other deposit and how many to neither.
- [ ] `leibniz-gt-nc` (the NC-derived deposit, CC BY-NC 4.0, since 2026-10): every
      row's `source` names `channel potsdam`, `channel gwlb` or a joined channel
      containing one of them; the card names the Potsdam channel's licence as
      stated in writing (2026-10-12) and the GWLB repository's; **the two deposits
      are disjoint** (`gt_id` sets do not overlap) and together with the
      "released in neither" count add up to the store's `gt_lines`.
- [ ] Both ground-truth cards' audit note states the current audit state honestly
      (preliminary until Q #18 closes).
- [ ] The README of every dataset carries the attribution lines (the NC deposit
      also the edition-text line naming the Leibniz-Edition Potsdam and the GWLB
      Leibniz-Archiv), the "Licence" section quoting the registry, and the
      anti-contamination note ("machine output — do not ingest as verified text").

## 2. Zenodo (datasets)

One record per dataset, resource type **Dataset**, licence per the card
(`leibniz-inventory` CC0 1.0 with the katalog records CC BY 4.0;
`leibniz-transcriptions` and `leibniz-gt` CC BY 4.0; `leibniz-gt-nc` CC BY-NC
4.0, with the attribution to the Leibniz-Edition Potsdam (BBAW) and the GWLB
Leibniz-Archiv the card carries). Community:
`https://zenodo.org/communities/leibniz/`. Metadata to fill:

- [ ] Title as the card's title; version = the export's `generated_at` date.
- [ ] Description = the card's summary + attribution + the anti-contamination note.
- [ ] `related_identifiers`: `isSupplementTo` the code repository;
      `isDerivedFrom` doi:10.5281/zenodo.21457538 (PHILIUMM HTR model) and
      doi:10.5281/zenodo.21537859 (segmentation model) for the transcriptions;
      `isDerivedFrom` the PHILIUMM dataset (doi:10.5281/zenodo.21622297) and
      `isDocumentedBy` the retro-alignment report (doi:10.5281/zenodo.22782819)
      for both GT deposits; `isDocumentedBy` the project statement
      (doi:10.5281/zenodo.22782813) for all four. The transcriptions' and the
      GT deposits' descriptions say that the model was obtained under CC BY 4.0
      and is published by its makers under CC BY-NC 4.0 since 2026-10-15 (the
      registry's wording, `leibniz legal licences --key philiumm-htr-model`).
- [ ] Keywords: leibniz, nachlass, handwritten text recognition, htr, iiif,
      digital humanities, ground truth, machine transcription.
- [ ] Reserve the DOI first, write it into the card's "DOI" line, re-export, upload.
- [ ] Hugging Face mirror (D2 + D3 only): same card as the dataset README,
      `license: cc-by-4.0` for `leibniz-transcriptions` and `leibniz-gt`,
      `license: cc-by-nc-4.0` for `leibniz-gt-nc`, the Parquet files as-is.

## 3. Model (after Phase C3)

- [ ] `leibniz-htr-v2` weights + the finalized model card (`reports/htr-v2-eval.md`
      + data statement + per-stratum/per-language error rates + intended use +
      the "machine output, not an edition" framing). Resource type **Model**,
      `isDerivedFrom` the PHILIUMM checkpoint, `isDocumentedBy` the project
      statement. **Licence per the registry** (`leibniz legal outputs`): a model
      fine-tuned from the PHILIUMM checkpoint (v2, K3's kraken candidate) is
      **CC BY-NC 4.0** — PHILIUMM publishes its models under CC BY-NC 4.0 since
      2026-10-15 and the owner honours the change for models built from theirs
      (2026-10-13); K3's candidates with no NC input (the TrOCR model from the
      Bern model, MIT; one from kraken's PP-OCRv6, Apache-2.0; both on K2's open
      edition lines) are **CC BY 4.0** if released (the owner, 2026-10-21). The
      model card names every training input with its registry key. Until then
      the corpus is read by PHILIUMM's model, which is theirs to release (and
      is: obtained under CC BY 4.0, CC BY-NC 4.0 since 2026-10-15).

## 4. Reports (D8)

Published 2026-09-16 on Zenodo, mirrored on evanatlas.com/research:

- project statement — doi:10.5281/zenodo.22782813
- corpus census (A1) — doi:10.5281/zenodo.22782815
- PHILIUMM reproduction + VLM benchmark (B1) — doi:10.5281/zenodo.22782817
- retro-aligned ground truth (B2–C2) — doi:10.5281/zenodo.22782819

New versions of a report are new Zenodo versions of the same concept record
(never a new record); update the mirrored manifest's DOI on the website.

## 5. After upload

- [ ] Write the DOIs into `README.md` (Status section) and `STATUS.md`.
- [ ] Add the dataset DOIs to the About page (`src/leibniz/web/static/`).
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
