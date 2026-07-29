# STATUS — Leibniz Legible

_Living state of the project. Every session reads this before starting and
updates it before committing. The repo is the memory; this file is its index._

_Last updated: 2026-07-29 (end of Phase A1)._

---

## Current state

**Phase A1 (OAI/IIIF harvest → inventory + corpus census) — complete. Gate: GO.**

The harvest stage is built, tested, and run live against the GWLB. The project's
first genuinely new artifact — the real page count of the digitized Leibniz
Nachlass — exists in `reports/census.md`:

- **2,225 unique works · 236,795 page images** — **within** the SPECS §1
  expected band (150–250k), close to the folkloric "~200,000" estimate. The
  gate stop-condition is **not** triggered; **A2 is green-lit.**
- All endpoint facts in SPECS §1 verified live (OAI set counts match exactly).
- **No machine-readable §44b TDM reservation** on either host
  (`reports/crawl-posture.md`) — harvest proceeds under the SPECS §7.4 rails.

Everything is green and offline-testable:

- `uv run ruff check .` / `ruff format --check .` — clean.
- `uv run pytest` — **91 passed** (was 27; +64 for harvest/net/census).

The A1 gate deliverable is the census; the `pages` table is populated for the
IIIF-served works touched by the manifest validation slice, with the full pull
left as a documented operator action (see Phase log). Nothing bulk beyond the
OAI XML cache (`data/oai/`, ~200 MB, gitignored) was fetched.

### What was built (A1)

```
src/leibniz/net.py           polite HTTP client (UA+contact, ≤1 req/s/host, backoff,
                             follow_redirects toggle) — the SPECS §7.4 rails as code
src/leibniz/harvest/
  oai.py                     OAI-PMH ListRecords → works; defensive METS/MODS parse;
                             cache-first, resumable (resumptionToken + expiry restart)
  manifests.py               IIIF manifests → pages; cache-first; categorises
                             no_manifest (static-JPEG-only works) vs failures
  shelfmarks.py              coarse LH/LBr/Marg/LK family classifier (census coverage)
  census.py                  compute + render reports/census.md
  cli.py                     leibniz harvest {oai,manifests,census}
src/leibniz/db.py            + runs bookkeeping (start_run/finish_run, utcnow_iso)
reports/crawl-posture.md     robots/TDM baseline for GWLB + BBAW hosts
reports/census.md            THE first real page count (publishable artifact)
tests/                       test_{net,harvest_oai,harvest_manifests,shelfmarks,
                             census,harvest_cli,runs}.py + fixtures/{oai,manifests}
```

### Decisions & divergences (repo wins; recorded per protocol)

- **Object id is not always the 8-digit id SPECS §4.4 assumes.** Handschriften /
  Leibnitiana use `00068642`-style ids; Briefwechsel + Rekonstruktionen use
  Kalliope `DE-611-HS-…`; Marginalien use VD17 numeric ids (`733605036`,
  `1016728174`). The `{id}:{seq:04d}` page-id scheme still holds (string id). We
  store the OAI `<identifier>` verbatim — it is exactly what the content URLs use.
- **Manifest URL is constructed** (`…/content/{id}/manifest.json`) when the METS
  lacks a `mods:identifier[@type='iiif']` (the common case). See the IIIF drift
  below for the crucial consequence.
- **Set overlap is massive** (81.4% of works are in ≥2 Leibniz sets; nearly all
  are also in `Leibnitiana`). A work's *primary* set is assigned deterministically
  by priority (Handschriften → Briefwechsel → Marginalien → Rekonstruktionen →
  Leibnitiana) from its own `setSpec` list, and the census dedups by object id.
  The naive sum of set sizes (4,037) is ~1.8× the real 2,225 objects.
- **Page count from the OAI METS alone.** The physical-structMap `page`-division
  count equals the IIIF canvas count (checked 00068642: 4 == 4), so the gate
  number needs no image/manifest fetch. `harvest manifests` cross-checks per-work.
- **ruff:** added `flake8-bugbear.extend-immutable-calls` for `typer.Option`/
  `typer.Argument` (idiomatic Typer defaults, not B008 violations).
- **Repo-local `scratchpad/` gitignored** (session temp; the canonical scratchpad
  is outside the repo).

### ⚠️ Major drift: IIIF vs. static-JPEG delivery (revises SPECS §1.1)

SPECS §1.1 assumed IIIF Image API tiles from pyramid TIFFs for the *whole*
Nachlass. Reality, measured this phase:

- **~812 works / 77,633 pages (33%) are IIIF-served** (manifest + `iiif/{id}/ptif/…`
  Image API). Almost all of Handschriften.
- **~1,413 works / 159,162 pages (67%) are static-JPEG-only** — no manifest
  (`…/manifest.json` 302-redirects to a viewer page), no Image API
  (`iiif/{id}/ptif/…/info.json` → 404); images exist only at
  `…/content/{id}/jpgs/{default,thumbs}/{seq:08d}.jpg`. **All** of Briefwechsel
  and **most** of Marginalien.

Signal: presence of `mods:identifier[@type='iiif']` in the METS (stored as
`works.metadata.has_iiif_manifest`). Spot-checked (~9 works) and close but
**imperfect** — one unflagged object (`DE-611-HS-4277399`) also served a
manifest — so 812 is a **lower bound** on IIIF coverage; A2 must establish
per-work delivery definitively. **Consequences for later phases:**

- **A2** cannot use the IIIF Image API for the majority of pages; it must fall
  back to the static JPEG derivative (`…/content/{id}/jpgs/default/…`, confirmed
  200) and its prompt ("delivery via the IIIF Image API") needs this caveat.
- **D2**'s OpenSeadragon deep-zoom only works for IIIF pages; static-JPEG pages
  degrade to plain-image display.

---

## Phase log

### A1 — OAI/IIIF harvest → inventory + corpus census (2026-07-29) ✅ Gate: GO

Built `src/leibniz/net.py` + `src/leibniz/harvest/*` and ran the harvest live.

- **Crawl posture** (`reports/crawl-posture.md`): probed `robots.txt`, headers,
  and every §44b TDM mechanism (`/.well-known/tdmrep.json`, `TDM-Reservation`/
  `X-Robots-Tag` headers, `tdm-reservation` meta) on both `digitale-sammlungen.gwlb.de`
  and `leibniz-katalog.bbaw.de`. **No reservation exists**; neither host serves a
  `robots.txt` with rules (GWLB 302s into the TYPO3 app; BBAW 404s). Verdict: proceed.
- **`harvest oai`**: paged `ListRecords` (`metadataPrefix=mets`, 5 records/page)
  over all five sets, ~810 requests at ≤1 req/s (~14 min), raw XML cached under
  `data/oai/`. Parsed METS/MODS → 2,225 works. Cache-first re-runs re-parse offline.
- **`harvest manifests`**: validated on a 13-work stratified slice — 3 IIIF works
  → 302 pages populated; 6 correctly categorised `no_manifest`; fail-fast via
  `follow_redirects=False`. The full manifest pull (and full `pages` population,
  incl. the static-JPEG path) is left as an operator action for A2's slice.
- **`reports/census.md`**: the first real page count, written as a publishable
  artifact (per-set, overlap cross-check, IIIF/static split, pages-per-work
  distribution, shelfmark coverage 98.2%, anomalies).
- Tooling: ruff clean, **91** pytest green, all offline (fixtures trimmed from real
  GWLB responses).

### A0 — Repo scaffold (2026-07-28) ✅

Scaffold per PROMPTS.md A0: `pyproject.toml` + `leibniz` entry point; the
`src/leibniz/` skeleton; `tests/`; `.gitignore`, `.env.example`, `data/`.
`legal.py` (§70/§71 expiry registry, years verified against leibnizedition.de)
and `db.py` (seven SPECS §4.3 tables, idempotent `init_db`, typed works/pages
helpers). 27 tests green.

---

## Key numbers

| Metric | Value |
| --- | --- |
| Tests passing | 91 (offline) |
| **Unique works** | **2,225** |
| **Unique page images** | **236,795** — within the 150–250k gate band ✅ |
| OAI records (with overlap) | 4,037; 1,811 works (81.4%) in ≥2 Leibniz sets |
| IIIF-served | 812 works / 77,633 pages (33%) |
| Static-JPEG-only | 1,413 works / 159,162 pages (67%) |
| Pages/work | mean 106.4 · median 26 · max 3,572 (`DE-611-HS-3618673`, LBr. F 20) |
| Shelfmark coverage (parseable LH/LBr/Marg) | 98.2% |
| Anomalies | 27 zero-canvas · 24 no-shelfmark · 56 shared-shelfmark strings |

**Page images per primary set** (disjoint; sums to the unique total):

| Set | Works | Pages |
| --- | ---: | ---: |
| LeibnizMarginalien | 396 | 103,887 |
| LeibnizBriefwechsel | 1,059 | 72,284 |
| LeibnizHandschriften | 756 | 58,828 |
| Leibnitiana (residual) | 12 | 1,768 |
| leibniz-rekonstruktionen | 2 | 28 |

(Marginalien lead in *pages* because they are annotated **printed books**, not
autograph manuscripts — high page counts, but Leibniz's marginalia are the point.)

Legal registry (from A0, unchanged): 42 entries; 32 free today; upcoming
expiries I,17 · IV,4 (2027), III,5 · VII,3 (2029), … VII,8 (2050).

---

## Open questions

1. **IIIF vs static-JPEG delivery (A2/D2 design).** ~67% of pages are static-JPEG
   only. A2 must fetch those from `…/content/{id}/jpgs/…` (not the Image API) and
   populate their `pages` rows (dimensions unavailable without downloading; the
   METS has none). The `has_iiif_manifest` flag is a *lower bound* — verify
   per-work in A2 (at least one unflagged object had a manifest).
2. **`pages` population is partial.** Only the IIIF works in the A1 validation
   slice have `pages` rows. Full population (IIIF via manifests, static via
   METS structMap / static-JPEG enumeration) folds into A2, where image delivery
   is handled anyway. Decide there whether to derive static-work pages from the
   cached METS `fileSec`/`structMap` (offline, already have it) or on download.
3. **Marginalien scope.** 396 annotated printed books, 103,887 pages (44% of the
   corpus by pages). In scope per SPECS (LeibnizMarginalien set), but the HTR
   target is Leibniz's *marginal annotations*, not the printed body text — a
   segmentation/stratum concern for C1/C4, flagged early.
4. **Shared-shelfmark strings (56).** Mostly multi-volume printed Marginalien
   where each part is a separate work under one `Leibn. Marg. N` base signature
   (e.g. `ZEN Leibn. Marg. 41` → 29 works). Legitimate, but the A3 shelfmark
   normaliser + crosswalk must handle part suffixes (`:1`, `, Stück 1`).
5. **`leibnizcentral.de` dead links in METS.** DVLINKS `dv:reference` points to
   the defunct LeibnizCentral (SPECS §1 already notes it dead) — harmless, ignored.
6. _(A0, still open)_ §71 editio-princeps assumption; re-edition term restarts
   (II,1 2006, Reihe VI 1990 reprints) — for the lawyer memo (SPECS §7.5).

---

## Next

**Recommended: Phase A2 — Image cache**, now green-lit by the A1 gate. But read
Open question #1 first: A2's prompt assumes the IIIF Image API for every page;
**that holds for only ~1/3 of pages**. A2 must add a static-JPEG delivery path
(`…/content/{id}/jpgs/default/{seq:08d}.jpg`) and can derive per-page rows from
the already-cached METS. Keep the full pull as an operator command (~200–400 GB).

**Also ready:**
- **A3 (katalog crosswalk)** — depends on A1 (done). The 98.2% shelfmark coverage
  and the parsed LH/LBr/Marg signatures are a strong basis; note the multi-volume
  part-suffix issue (Open question #4).
- **B1 (benchmark harness + PHILIUMM reproduction)** — independent of A1–A3
  (depends only on A0); a good parallel track.

Sequencing per SPECS §5: A1→A2→A3 and B1→B2 can interleave; C sequential; D
follows C4.
