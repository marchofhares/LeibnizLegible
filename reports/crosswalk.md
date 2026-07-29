# Katalog crosswalk — Ritter-Katalog ↔ GWLB works (Phase A3)

_Leibniz Legible, Phase A3. Generated 2026-07-29T01:37:49Z. Joins the BBAW Arbeitskatalog der Leibniz-Edition (Ritter-Katalog) to our harvested works so every scan links to its scholarly record and (where catalogued) its AA volume/piece._

> Data from the Arbeitskatalog der Leibniz-Edition (Ritter-Katalog), Berlin-Brandenburgische Akademie der Wissenschaften (TELOTA), https://leibniz-katalog.bbaw.de/ — licensed CC BY 4.0.

## What this measures

The katalog has **no public API** and caps every query at 5,000 rows, so a full enumeration of its >70,200 records is an operator-scale job (see *Operator command*). This run scraped a **bounded sample** and matched it against all 2,225 harvested works, by two methods:

- **`gwlb_link` (conf 1.0)** — the record's *Signatur* cell links to the scan as `…/resolve?id={object_id}`; that id is our works key. Authoritative.
- **`shelfmark` (conf 0.7)** — no link, but the record's signature normalises to the same key as a work's shelfmark (Roman/Arabic, spacing, and leaf-suffix tolerant).

Sample queries this run: `reihe=1&bd=1`, `reihe=1&bd=2`, `reihe=2&bd=1`, `reihe=3&bd=1`, `sign_ol=LH 35`, `sign_ol=Leibn. Marg. 1`.

## Headline

- **Katalog records scraped:** 15,382
- **Records matched to a work:** 12,535 (81.5% of scraped)
- **Crosswalk links written:** 12,582
- **Distinct works matched:** 1,094 / 2,225 (**49.2%** of the corpus)
- **Links by method:** gwlb_link: 12,384, shelfmark: 198
- **GWLB links to non-harvested objects:** 5 (out-of-scope holdings or non-Leibniz sets — expected, not an error).

> The ≥80%-of-works target is a **full-scrape** goal. This sample covers 49.2% of works; the per-set table shows where the sampled queries landed. Record→work resolution via GWLB links is the quality signal to read here, not absolute corpus coverage.

## Work coverage by set

| Primary set | Works | Matched | % matched |
| --- | ---: | ---: | ---: |
| Leibnitiana | 12 | 2 | 16.7% |
| LeibnizBriefwechsel | 1,059 | 545 | 51.5% |
| LeibnizHandschriften | 756 | 401 | 53.0% |
| LeibnizMarginalien | 396 | 146 | 36.9% |
| leibniz-rekonstruktionen | 2 | 0 | 0.0% |
| **All** | **2,225** | **1,094** | **49.2%** |

## Unmatched records (samples, with reasons)

Two reasons a scraped record has no work: it belongs to a **non-Hannover holding** (British Library, Cambridge, Paris — out of Tier-1 scope), or it carries a **Leibniz signature we didn't match** (a work outside the sample, or a normaliser gap — the latter is the actionable bucket).

**Foreign / out-of-scope holdings:**

- `10005` — (no signature)
- `10040` — Oxford Bodl. Smith Mss. 46 S. 479-480
- `10053` — Hannover NLA Dep. 84 A 180 Bl. 139-140 (vgl.34497) (Wasserschaden 1946)
- `10054` — Hannover NLA Dep. 84 A 180 Bl. 158-159
- `10055` — Kortholt, Epistolae 4 S. 253-254
- `10072` — Ann Arbor Univ. of Michigan Library Dept. of Rare Books and Special Coll.
- `10097` — (no signature)
- `10098` — (no signature)

**Leibniz signature, unmatched (work not in sample, or a normaliser gap):**

- `11512` — Hannover NLB Leibn. Marg. 10, 1, S. 154-166 → key `Marg 10,1`
- `11970` — Hannover NLB Bibliotheksakten A2 Bl. 261-262 (jetzt LK-MOW Ammon10 Bl. B 261-262) → key `LK mow,ammon10,bl,b,261-262`
- `12433` — Hannover NLB Leibn. Marg. 10, 1, S. 167-169 → key `Marg 10,1`
- `13619` — Hannover NLB Leibn. Marg. 10, 1, S. 172-178 (L' Handexpl. d. Erstdr. mit eigh. Notaten, Marginalien & Unterstreichgn) → key `Marg 10,1`
- `1469` — Hannover NLB Leibn. Marg. 199, S. 1 (Bl. 1r° ; Titelblatt), S. 2 (Bl. 1v° ), S. 4 (Bl. 2v° ), Bl. 17v° –19r°, Bl. 20r° , Bl. 51r° → key `Marg 199`
- `1526` — Hannover NLB Leibn. Marg. 16, Stück 2 → key `Marg 16,stück,2`
- `1563` — Hannover NLB Leibn. Marg. 16, Stück 1 → key `Marg 16,stück,1`
- `15736` — Hannover NLB Bibliotheksakten A5a Bl. 122 (jetzt LK-MOW Ernst August10 Bl. D122) → key `LK mow,ernst,august10,bl,d122`

## Operator command (full scrape)

The full crosswalk needs every katalog record. Because of the 5000-row cap, enumerate in sub-cap slices and let the scraper flag any that still cap out (then narrow those):

```
# Correspondence: one slice per AA volume (Reihe × Band)
leibniz catalog scrape --reihe 1 --bd 1   # … sweep all volumes
# Manuscripts / Marginalia: by signature prefix, deepened on a cap warning
leibniz catalog scrape --sign 'LH 1'  --sign 'LH 2'  # …
leibniz catalog crosswalk && leibniz catalog report
```

Estimate: ~70k records over sub-cap queries at ≤1 req/s ≈ a few hours of polite crawling; a TELOTA data dump (SPECS §8) would replace it outright.

## Method & caveats

- **Source:** live scrape of `leibniz-katalog.bbaw.de` (server-rendered; raw HTML cached under `data/katalog/`). No API; 5000-row result cap; no pagination.
- **Join key:** the GWLB `resolve?id=` link is exact; the shelfmark method is a normalised-string fallback and can mis-group shared base signatures (the multi-volume Marginalien; STATUS Open Q #4).
- **Honesty:** absolute work-coverage here is bounded by the sample, not by the crosswalk's accuracy. Re-run after the full scrape for the real number.
