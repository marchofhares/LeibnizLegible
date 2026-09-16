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
- The public web app (D2) rehosts no images and carries only machine text plus
  §70-expired reading text; it is the lighter surface and ships first (v1).

## 1. Export

```bash
uv sync --extra release                    # pyarrow
leibniz index build                        # refreshes the corpus statistics too
leibniz release export --out data/release  # inventory + transcriptions + gt (Parquet)
leibniz release export --format jsonl      # JSONL.gz mirror, if wanted
```

Each dataset directory holds `MANIFEST.json` (files, row counts, SHA-256, git
SHA, generator) and `README.md` (the dataset card). Check:

- [ ] `MANIFEST.json` row counts match `leibniz pipeline status` / `align gt-report`.
- [ ] `leibniz-transcriptions`: no row has `source.license_bucket == "nc"` (the
      exporter drops them; spot-check with a quick query on the Parquet).
- [ ] `leibniz-gt`: every row `license_bucket == "open"`; the card's audit note
      states the current audit state honestly (preliminary until Q #18 closes).
- [ ] The README of every dataset carries all three attribution lines and the
      anti-contamination note ("machine output — do not ingest as verified text").

## 2. Zenodo (datasets)

One record per dataset, resource type **Dataset**, licence per the card
(`leibniz-inventory` CC0 1.0 with the katalog records CC BY 4.0;
`leibniz-transcriptions` and `leibniz-gt` CC BY 4.0). Community:
`https://zenodo.org/communities/leibniz/`. Metadata to fill:

- [ ] Title as the card's title; version = the export's `generated_at` date.
- [ ] Description = the card's summary + attribution + the anti-contamination note.
- [ ] `related_identifiers`: `isSupplementTo` the code repository;
      `isDerivedFrom` doi:10.5281/zenodo.21457538 (PHILIUMM HTR model) and
      doi:10.5281/zenodo.21537859 (segmentation model) for the transcriptions;
      `isDerivedFrom` the PHILIUMM dataset (doi:10.5281/zenodo.21622297) and
      `isDocumentedBy` the retro-alignment report (doi:10.5281/zenodo.22782819)
      for the GT; `isDocumentedBy` the project statement
      (doi:10.5281/zenodo.22782813) for all three.
- [ ] Keywords: leibniz, nachlass, handwritten text recognition, htr, iiif,
      digital humanities, ground truth, machine transcription.
- [ ] Reserve the DOI first, write it into the card's "DOI" line, re-export, upload.
- [ ] Hugging Face mirror (D2 + D3 only): same card as the dataset README,
      `license: cc-by-4.0`, the Parquet files as-is.

## 3. Model (after Phase C3)

- [ ] `leibniz-htr-v2` weights + the finalized model card (`reports/htr-v2-eval.md`
      + data statement + per-stratum/per-language error rates + intended use +
      the "machine output, not an edition" framing). Resource type **Model**,
      CC BY 4.0, `isDerivedFrom` the PHILIUMM checkpoint, `isDocumentedBy` the
      project statement. Until then the corpus is read by PHILIUMM's model,
      which is theirs to release (and is, CC BY 4.0).

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
