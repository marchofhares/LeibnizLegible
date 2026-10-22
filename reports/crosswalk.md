# Katalog crosswalk — Ritter-Katalog ↔ GWLB works (Phase A3)

_Leibniz Legible, Phase A3. Generated 2026-10-22T16:22:46Z. Joins the BBAW Arbeitskatalog der Leibniz-Edition (Ritter-Katalog) to our harvested works so every scan links to its scholarly record and (where catalogued) its AA volume/piece._

> Data from the Arbeitskatalog der Leibniz-Edition (Ritter-Katalog), Berlin-Brandenburgische Akademie der Wissenschaften (TELOTA), https://leibniz-katalog.bbaw.de/ — licensed CC BY 4.0.

## What this measures

The katalog has **no public API** and caps every query at 5,000 rows, so a full enumeration of its >70,200 records is an operator-scale job (see *Operator command*). This run scraped a **bounded sample** and matched it against all 2,225 harvested works, by two methods:

- **`gwlb_link` (conf 1.0)** — the record's *Signatur* cell links to the scan as `…/resolve?id={object_id}`; that id is our works key. Authoritative.
- **`shelfmark` (conf 0.7)** — no link, but the record's signature normalises to the same key as a work's shelfmark (Roman/Arabic, spacing, and leaf-suffix tolerant).

## Headline

- **Katalog records scraped:** 70,405
- **Records matched to a work:** 39,588 (56.2% of scraped)
- **Crosswalk links written:** 39,784
- **Distinct works matched:** 2,183 / 2,225 (**98.1%** of the corpus)
- **Links by method:** gwlb_link: 39,575, shelfmark: 209
- **GWLB links to non-harvested objects:** 98 (out-of-scope holdings or non-Leibniz sets — expected, not an error).

> The ≥80%-of-works target is a **full-scrape** goal. This sample covers 98.1% of works; the per-set table shows where the sampled queries landed. Record→work resolution via GWLB links is the quality signal to read here, not absolute corpus coverage.

## Work coverage by set

| Primary set | Works | Matched | % matched |
| --- | ---: | ---: | ---: |
| Leibnitiana | 12 | 7 | 58.3% |
| LeibnizBriefwechsel | 1,059 | 1,059 | 100.0% |
| LeibnizHandschriften | 756 | 749 | 99.1% |
| LeibnizMarginalien | 396 | 368 | 92.9% |
| leibniz-rekonstruktionen | 2 | 0 | 0.0% |
| **All** | **2,225** | **2,183** | **98.1%** |

## Unmatched records (samples, with reasons)

Two reasons a scraped record has no work: it belongs to a **non-Hannover holding** (British Library, Cambridge, Paris — out of Tier-1 scope), or it carries a **Leibniz signature we didn't match** (a work outside the sample, or a normaliser gap — the latter is the actionable bucket).

**Foreign / out-of-scope holdings:**

- `10005` — (no signature)
- `10007` — Gotha FB B 199 Bl. 476
- `10008` — (no signature)
- `10009` — (no signature)
- `10010` — Ms 23, 817 [b] Bl. 73-74
- `10011` — (no signature)
- `10014` — Dresden HStA 10024 Geheimer Rat (Geheimes Archiv), Nr. Loc. 08062/02 Bl. 11r°-20r°
- `10015` — Hannover NLA Cal.Br. 11, 1116 Bl. 279-282

**Leibniz signature, unmatched (work not in sample, or a normaliser gap):**

- `10195` — LH 12, 5, 1 Bl. 5 (Kriegsverlust) → key `LH 12,5,1`
- `10196` — LH 12, 5, 1 Bl. 5 (Kriegsverlust) → key `LH 12,5,1`
- `10394` — LH 1, 6, 3b Bl. 3-4 → key `LH 1,6,3b`
- `11970` — Hannover NLB Bibliotheksakten A2 Bl. 261-262 (jetzt LK-MOW Ammon10 Bl. B 261-262) → key `LK mow,ammon10,bl,b,261-262`
- `1469` — Hannover NLB Leibn. Marg. 199, S. 1 (Bl. 1r° ; Titelblatt), S. 2 (Bl. 1v° ), S. 4 (Bl. 2v° ), Bl. 17v° –19r°, Bl. 20r° , Bl. 51r° → key `Marg 199`
- `1509` — Hannover NLB Leibn. Marg. 200 → key `Marg 200`
- `1564` — Hannover NLB Leibn. Marg. 214 → key `Marg 214`
- `1569` — Hannover NLB Leibn. Marg. 209 → key `Marg 209`

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
