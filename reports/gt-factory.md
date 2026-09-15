# GT factory — retro-aligned ground truth at scale (Phase C2)

_Leibniz Legible, Phase C2. Generated 2026-09-11. Deliverable of PROMPTS C2 (SPECS §1.4, §6, §7). Counts are queried from the store by `leibniz align gt-report`; prose is templated._

## The factory

Scales the B2 retro-aligner (98.8 % yield / 97.5 % precision on favourable material under real HTR) across every §70-expired AA volume. Each piece is localized and minted by one chain:

1. **Enumerate pieces** — a §70-expired volume's pieces *are* the katalog records whose AA reference cites it (`legal.py` × `katalog_records.aa_refs`).
2. **Localize the scan** — the A3 crosswalk gives each piece's GWLB work; the folio resolver (Open Q #10: canvas labels are folio numbers) maps the katalog `Bl.` range to the exact canvases.
3. **Reading text** — extracted from the expired volume's print, apparatus excluded (B2's `pdftext`, SPECS §7.2), with a spot-check extraction-error estimate (`assess_extraction`).
4. **Align & mint** — the B2 aligner (banded for long multi-page pieces) projects the reading text onto the C1 HTR lines; the **stratum sets the mint threshold** (fair copies 0.55 … heavy revision 0.72 — drafts held to a higher bar), and below-threshold lines are discarded (SPECS §6).
5. **License gate** — §70 reading text → `license_bucket='open'`; any Transkriptionspool-derived pairs → `'nc'`, never in a CC BY export (SPECS §7.3), enforced at mint time by `GtPair`.

## §70 volumes: sources and extracted reading text

Each §70-expired volume's reading text is read from a **free digital copy of the print** (`align/volumes_sources.py`, verified 2026-09-11): a public-domain library scan on the Internet Archive with its OCR layer (preferred — an unencumbered channel), the Leibniz-Archiv's own PDF in the GWLB repositorium (CC BY-NC channel; the reading text itself is §70-free, but the channel is a partner's, so it is used only where no scan exists and flagged for the lawyer memo), or the Potsdam Arbeitsstelle's born-digital text PDFs. The extractor (`align/edition.py`) reads the page layout — running head, body type vs. the smaller apparatus type (learned per volume), piece headings, margin line numbers, the editorial dateline/*Überlieferung* block — and emits one reading text per printed piece with its page anchors; apparatus, commentary, introductions and indices never enter it (SPECS §7.2).

| Volume | Source | Pages read | Pieces extracted | Katalog pieces | Reading text | Anomalies | Cross-source agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| I,1 | — | — | — | 710 | _1923; HathiTrust (US-PD) / TELOTA ask_ | — | — |
| I,2 | — | — | — | 843 | _1927; HathiTrust (US-PD) / TELOTA ask_ | — | — |
| I,3 | gwlb | 492/711 | 420 | 924 | 931k chars | 18 | — |
| I,4 | — | — | — | 1,396 | _1950; no free digital copy found_ | — | — |
| I,5 | — | — | — | 680 | _1954; no free digital copy found_ | — | — |
| I,6 | ia | 593/758 | 352 | 612 | 1,132k chars | 48 | — |
| I,7 | ia | 659/842 | 350 | 671 | 1,188k chars | 70 | — |
| I,8 | ia | 570/772 | 354 | 586 | 1,080k chars | 51 | — |
| I,9 | ia | 647/904 | 428 | 716 | 1,071k chars | 60 | 84.1% (12/40 flagged) |
| I,10 | ia | 636/894 | 437 | 712 | 1,068k chars | 63 | — |
| I,11 | ia | 706/974 | 475 | 762 | 1,136k chars | 63 | 89.2% (9/40 flagged) |
| I,12 | ia | 694/954 | 446 | 679 | 1,101k chars | 61 | 74.4% (6/40 flagged) |
| I,13 | — | — | — | 615 | _1987; not online at GWLB, not on IA_ | — | — |
| I,14 | gwlb | 865/1,081 | 490 | 688 | 1,428k chars | 58 | — |
| I,15 | gwlb | 848/1,033 | 550 | 784 | 1,370k chars | 1 | — |
| I,16 | ia | 741/954 | 451 | 679 | 1,185k chars | 47 | 88.3% (8/40 flagged) |
| II,1 | — | — | — | 698 | _1926 print; HathiTrust (US-PD) / TELOTA ask_ | — | — |
| III,1 | ia | 655/956 | 81 | 411 | 777k chars | 13 | — |
| III,2 | — | — | — | 598 | _1987; no free digital copy found_ | — | — |
| III,3 | ia | 785/966 | 353 | 734 | 1,131k chars | 67 | — |
| III,4 | ia | 661/826 | 281 | 453 | 1,016k chars | 42 | — |
| IV,1 | potsdam | 583/793 | 51 | 154 | 1,437k chars | 3 | 71.9% (19/40 flagged) |
| IV,2 | potsdam | 575/692 | 28 | 161 | 1,133k chars | 0 | — |
| IV,3 | potsdam | 888/999 | 141 | 266 | 1,679k chars | 5 | — |
| VI,1 | ia | 484/616 | 26 | 41 | 1,084k chars | 106 | — |
| VI,2 | — | — | — | 92 | _1966; no free digital copy found_ | — | — |
| VI,3 | ia | 628/794 | 90 | 234 | 1,207k chars | 69 | — |
| VI,4 | ia | 1,918/2,642 | 377 | 777 | 3,111k chars | 51 | — |
| VI,6 | ia | 375/652 | 7 | 36 | 896k chars | 28 | — |
| VII,1 | — | — | — | 303 | _1990; not online at GWLB, not on IA_ | — | — |
| VII,2 | — | — | — | 147 | _1996; not online at GWLB, not on IA_ | — | — |

**21 of 31 §70 volumes have a readable free digital copy** → **6,188 printed pieces / 26.16M characters of reading text extracted**; 10 volumes have no free digital copy at all (1923–1927 prints are US-public-domain on HathiTrust; a TELOTA/Göttingen ask covers the rest — operator). Terms per channel: **ia** — public-domain scan, no access restriction; **gwlb** — CC BY-NC 4.0 channel (text §70-free; flag for the lawyer memo); **potsdam** — no terms stated (edition's own site); **muenster** — written permission required (operator ask; not auto-fetched).

**Edition cache:** 10,029 katalog records (manuscript witnesses citing an ingested volume) carry their piece's reading text in `data/gt/edition_cache.json` — the factory's input.

## Extraction path — validated live on real Leibniz print

The one factory step that cannot be unit-tested offline — vision-LLM extraction of the reading text with the apparatus excluded (step 3), and the `assess_extraction` QA over it (Open Q #12) — was **run live this session** on real Leibniz edition print (Gerhardt, *Die philosophischen Schriften* Bd. II, 1875, public domain — archive.org `diephilosophisc02gerhgoog`; the Leibniz↔Arnauld correspondence). A public-domain edition stands in for the §70 AA print purely to exercise the extraction machinery; the production open bucket is §70 AA text only.

- **Reading text, apparatus excluded:** on a clean Latin page (leaf 110) `gpt-4o` transcribed the constituted text faithfully and **correctly dropped** the running head (*Leibniz an Antoine Arnauld*), the page number (81), and the signature mark — the reading-text/paratext separation SPECS §7.2 demands.
- **QA caught a real divergence:** a two-model spot-check (`gpt-4o` vs the weaker `gpt-4o-mini` as control) over 2 pages measured **mean agreement 0.67**, flagging **1 / 2** pages — precisely the code-switched Latin/German page (leaf 90) where the control model dropped ~60 % of the text (883 vs 2,349 chars). That is exactly the unstable-extraction signal `assess_extraction` exists to surface for a per-volume error estimate. Evidence: `reports/gt-factory-extraction-qa.json`.
- **Takeaway for scale:** use the stronger model for production extraction and the cross-model (or manual) agreement as the QA gate; code-switched and heavy-apparatus pages are where extraction error concentrates, so the per-volume error estimate must be stratified, not a single number.

## Piece enumeration (localizable §70 corpus)

- **§70 pieces cited in the katalog:** 17,162
- **With a crosswalked work:** 12,385 · **with a folio range:** 11,617
- **Localizable (work + folio range → canvases):** 11,595 (67.6%)

| Volume | §70 pieces |
| --- | ---: |
| I,1 | 710 |
| I,10 | 712 |
| I,11 | 762 |
| I,12 | 679 |
| I,13 | 615 |
| I,14 | 688 |
| I,15 | 784 |
| I,16 | 679 |
| I,2 | 843 |
| I,3 | 924 |
| I,4 | 1,396 |
| I,5 | 680 |
| I,6 | 612 |
| I,7 | 671 |
| I,8 | 586 |
| I,9 | 716 |
| II,1 | 698 |
| III,1 | 411 |
| III,2 | 598 |
| III,3 | 734 |
| III,4 | 453 |
| IV,1 | 154 |
| IV,2 | 161 |
| IV,3 | 266 |
| VI,1 | 41 |
| VI,2 | 92 |
| VI,3 | 234 |
| VI,4 | 777 |
| VI,6 | 36 |
| VII,1 | 303 |
| VII,2 | 147 |

## Minted ground truth

- **Open-bucket aligned lines (CC BY):** 0
- **NC-bucket lines (internal only, never exported):** 0
- **vs the ≥50k target:** 0% · **vs PHILIUMM's ~63k baseline:** 0%

## By stratum

_No minted lines yet._

## Status of the live run

Of the factory's three inputs, **two are now in hand and one is on the operator's machine.** (1) The katalog is scraped for every §70 volume (17,162 piece citations, 11,595 localizable to exact canvases through the crosswalk + folio resolver — `leibniz catalog scrape --expired-volumes`, ~8 minutes of polite crawling, re-runnable anywhere). (2) The §70 reading text is extracted per piece from the volumes' free digital copies (table above; `leibniz align ingest`), joined to the katalog into the edition cache. (3) The C1 corpus HTR lines — 13.5M recognised lines — live in the operator's `data/inventory.sqlite`; this build environment has none, so `gt_lines` is still empty here. Minting is therefore one operator command away: run the three commands of the runbook below on the machine that holds the corpus store, then `leibniz align gt-report` fills the yield tables. The B2 prototype already proved the chain on one real piece (AA VI,4 N.109): GWLB IIIF → segment → HTR → §70 extraction → align.

## What the extraction costs — and the optional vision upgrade

The text-layer path above costs **nothing but crawl time** (~1 GB of hOCR/PDF, polite ≤1 req/s). Its labels carry the OCR layer's residual error (Tesseract on the IA scans, ABBYY on the GWLB PDFs, none on the born-digital Potsdam volumes); the cross-source agreement column measures it where two layers exist. A cleaner label comes from a **vision-LLM pass over the 12,957 OCR'd reading-text pages** (of 15,003 reading pages total), the B2 extractor (`align/pdftext.py`, validated live on Leibniz print) — priced from the measured ~2,000 tokens/page (≈1,500 in / ≈500 out at the observed page sizes):

| Model | $/M in · out | Per page | All OCR'd pages | Batch API (−50 %) |
| --- | --- | ---: | ---: | ---: |
| Claude Sonnet 5 | $2.00 · $10.00 | $0.0080 | $104 | $52 |
| Claude Opus 5 | $5.00 · $25.00 | $0.0200 | $259 | $130 |
| gpt-4o-class (B1/B2 adapter) | $2.50 · $10.00 | $0.0088 | $113 | $57 |

So the whole-corpus vision pass is a **two-figure to low-three-figure dollar item** (SPECS §10 budgets $500–3,000 for all LLM passes), and it need not run on every page: mint from the free OCR text first, then re-extract only the pieces that actually minted lines (a fraction of the pages) and re-mint — the factory is idempotent. A two-model QA sample (`assess_extraction`, ~200 pages × 2 models) adds a few dollars. No GPU is involved in C2; alignment is CPU work.

## Operator runbook

```bash
# On the machine holding the C1 corpus store (data/inventory.sqlite):
leibniz catalog scrape --expired-volumes  # every §70 volume's katalog records (~8 min)
leibniz catalog crosswalk                 # records → works
leibniz align pieces                      # enumerate §70 localizable pieces
leibniz align ingest                      # fetch + extract each volume's reading text
leibniz align edition-cache               # join to the katalog → the edition cache
mkdir -p logs && for i in $(seq 1 8); do    # mint gt_lines: 8 parallel shards,
  nohup uv run leibniz align factory data/gt/edition_cache.json \
    --shard $i/8 --resume > logs/factory-$i.log 2>&1 &   # resumable, ~2–3 h on 16 cores
  sleep 5   # stagger the starts (each worker parses the cache once, ~0.5 GB peak)
done; tail -n 1 logs/factory-*.log     # progress: one line per 25 pieces per shard
leibniz align gt-report                   # writes reports/gt-factory.md with the yield
# Optional clean-label upgrade (needs a key): vision-extract the minted pieces' pages
#   with `leibniz align extract`, rebuild the cache, re-run the factory (idempotent).
```

Discard-below-threshold is automatic (the aligner mints only ≥-threshold lines, the threshold set per stratum). Re-running is idempotent (gt_lines for a piece's line refs are replaced), `--resume` skips pieces already minted, and `--shard i/N` splits the piece list disjointly across N workers (the aligner costs ~3–10 s per piece, so ~11,600 pieces are a ~20 h single-core job and a ~2 h twelve-shard one). NC-derived pairs are quarantined to `license_bucket='nc'` and excluded from every CC BY export.
