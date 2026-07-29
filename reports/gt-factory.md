# GT factory — retro-aligned ground truth at scale (Phase C2)

_Leibniz Legible, Phase C2. Generated 2026-07-29. Deliverable of PROMPTS C2 (SPECS §1.4, §6, §7). Counts are queried from the store by `leibniz align gt-report`; prose is templated._

## The factory

Scales the B2 retro-aligner (98.8 % yield / 97.5 % precision on favourable material under real HTR) across every §70-expired AA volume. Each piece is localized and minted by one chain:

1. **Enumerate pieces** — a §70-expired volume's pieces *are* the katalog records whose AA reference cites it (`legal.py` × `katalog_records.aa_refs`).
2. **Localize the scan** — the A3 crosswalk gives each piece's GWLB work; the folio resolver (Open Q #10: canvas labels are folio numbers) maps the katalog `Bl.` range to the exact canvases.
3. **Reading text** — extracted from the expired volume's print, apparatus excluded (B2's `pdftext`, SPECS §7.2), with a spot-check extraction-error estimate (`assess_extraction`).
4. **Align & mint** — the B2 aligner (banded for long multi-page pieces) projects the reading text onto the C1 HTR lines; the **stratum sets the mint threshold** (fair copies 0.55 … heavy revision 0.72 — drafts held to a higher bar), and below-threshold lines are discarded (SPECS §6).
5. **License gate** — §70 reading text → `license_bucket='open'`; any Transkriptionspool-derived pairs → `'nc'`, never in a CC BY export (SPECS §7.3), enforced at mint time by `GtPair`.

## Extraction path — validated live on real Leibniz print

The one factory step that cannot be unit-tested offline — vision-LLM extraction of the reading text with the apparatus excluded (step 3), and the `assess_extraction` QA over it (Open Q #12) — was **run live this session** on real Leibniz edition print (Gerhardt, *Die philosophischen Schriften* Bd. II, 1875, public domain — archive.org `diephilosophisc02gerhgoog`; the Leibniz↔Arnauld correspondence). A public-domain edition stands in for the §70 AA print purely to exercise the extraction machinery; the production open bucket is §70 AA text only.

- **Reading text, apparatus excluded:** on a clean Latin page (leaf 110) `gpt-4o` transcribed the constituted text faithfully and **correctly dropped** the running head (*Leibniz an Antoine Arnauld*), the page number (81), and the signature mark — the reading-text/paratext separation SPECS §7.2 demands.
- **QA caught a real divergence:** a two-model spot-check (`gpt-4o` vs the weaker `gpt-4o-mini` as control) over 2 pages measured **mean agreement 0.67**, flagging **1 / 2** pages — precisely the code-switched Latin/German page (leaf 90) where the control model dropped ~60 % of the text (883 vs 2,349 chars). That is exactly the unstable-extraction signal `assess_extraction` exists to surface for a per-volume error estimate. Evidence: `reports/gt-factory-extraction-qa.json`.
- **Takeaway for scale:** use the stronger model for production extraction and the cross-model (or manual) agreement as the QA gate; code-switched and heavy-apparatus pages are where extraction error concentrates, so the per-volume error estimate must be stratified, not a single number.

## Piece enumeration (localizable §70 corpus)

_No §70 pieces enumerated yet — needs the katalog scraped (A3 full run) so `aa_refs` and the crosswalk are populated._

## Minted ground truth

- **Open-bucket aligned lines (CC BY):** 0
- **NC-bucket lines (internal only, never exported):** 0
- **vs the ≥50k target:** 0% · **vs PHILIUMM's ~63k baseline:** 0%

## By stratum

_No minted lines yet._

## Status of the live run

The factory is **built and offline-tested end-to-end** (piece enumeration, folio→canvas resolution, HTR gathering, banded alignment, stratum thresholding, license-gated minting, idempotent re-mint). Minting real ground truth additionally needs three inputs absent from this build environment: **(1)** the C1 corpus HTR lines (the pipeline is built but the segment/recognize passes need the kraken stack + full image pull — see `htr-v1-sample.md`); **(2)** the full katalog scrape so `aa_refs` + the crosswalk cover the §70 volumes (A3 documented the operator run); **(3)** the extracted §70 reading text per piece (a vision pass with an API key + the volume page-anchors). With those, `leibniz align factory` mints `gt_lines` and `leibniz align gt-report` fills every number above. The B2 prototype already proved the chain on one real piece (AA VI,4 N.109): GWLB IIIF → segment → HTR → GPT-4o §70 extraction → align.

## Operator runbook

```bash
# Prereqs: A3 full katalog scrape + C1 corpus recognition complete.
leibniz align pieces                      # enumerate §70 localizable pieces
#  extract each piece's §70 reading text (vision, apparatus excluded) into a
#  {record_id: text} JSON cache — needs OPENAI_API_KEY + volume page-anchors:
leibniz align extract <ia_id> <leaves> --out piece.txt   # per piece (B2 path)
leibniz align factory --edition-cache data/gt/edition_cache.json
leibniz align gt-report                   # writes reports/gt-factory.md
```

Discard-below-threshold is automatic (the aligner mints only ≥-threshold lines, the threshold set per stratum). Re-running is idempotent (gt_lines for a piece's line refs are replaced). NC-derived pairs are quarantined to `license_bucket='nc'` and excluded from every CC BY export.
