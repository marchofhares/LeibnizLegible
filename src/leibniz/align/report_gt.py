"""Render the GT-factory report (``reports/gt-factory.md``; Phase C2 deliverable).

Pulls the minted ``gt_lines`` aggregates from the store (counts by volume /
series / stratum / license bucket), the §70 piece enumeration (how much of the
expired corpus is localizable), and compares the open-bucket yield to PHILIUMM's
63k baseline and the ≥50k target. Like the C1 report, the numbers are queried so
an operator run fills them in; a *Status of the live run* note explains the zero
state until the factory has run against real corpus HTR + extracted edition text.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from leibniz.align.ingest import DEFAULT_EDITIONS_DIR, cross_source_qa, text_path, volume_label
from leibniz.align.volumes import enumerate_pieces
from leibniz.align.volumes_sources import CHANNEL_TERMS, readable_sources, sources_for
from leibniz.legal import expired_volumes

# PHILIUMM GT baseline (SPECS §1.3): ~63k lines; the C2 target is ≥50k NEW open lines.
PHILIUMM_BASELINE = 63_000
TARGET_OPEN_LINES = 50_000

_SOURCE_VOLUME_RE = re.compile(r"AA\s+([IVX]+),(\S+?)\s+N")


@dataclass(slots=True)
class GtReport:
    """Structured GT-factory summary."""

    generated_at: str
    n_gt_total: int
    n_open: int
    n_nc: int
    by_stratum: dict[str, int]
    by_volume: dict[str, int]
    by_series: dict[str, int]
    enum_pieces: int
    enum_localizable: int
    enum_with_work: int
    enum_with_folio: int
    enum_by_volume: dict[str, int]
    audit: dict[str, tuple[int, float]] = field(default_factory=dict)  # stratum → (n, precision)
    extraction: list[VolumeExtraction] = field(default_factory=list)
    cache_records: int = 0  # katalog records with reading text in the edition cache
    cache_by_volume: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class VolumeExtraction:
    """What the text-layer extraction produced for one §70 volume."""

    volume: str
    kind: str  # ia | gwlb | potsdam | muenster | none
    terms: str
    n_pages: int = 0
    n_reading_pages: int = 0
    n_pieces: int = 0
    n_chars: int = 0
    n_anomalies: int = 0
    katalog_pieces: int = 0  # katalog records citing the volume (from the enumeration)
    qa_agreement: float | None = None  # cross-source agreement, if two sources exist
    qa_flagged: int | None = None
    qa_sampled: int | None = None
    note: str = ""


def _volume_of(source: str) -> str | None:
    m = _SOURCE_VOLUME_RE.search(source or "")
    return f"{m.group(1)},{m.group(2)}" if m else None


def gather_gt(
    conn,
    *,
    today: date,
    audit: dict[str, tuple[int, float]] | None = None,
    editions_dir: Path = DEFAULT_EDITIONS_DIR,
    edition_cache: Path | None = None,
) -> GtReport:
    """Query minted ``gt_lines`` + piece enumeration into a :class:`GtReport`."""
    n_open = conn.execute("SELECT COUNT(*) FROM gt_lines WHERE license_bucket = 'open'").fetchone()[
        0
    ]
    n_nc = conn.execute("SELECT COUNT(*) FROM gt_lines WHERE license_bucket = 'nc'").fetchone()[0]

    by_stratum: dict[str, int] = {}
    for row in conn.execute(
        "SELECT stratum, COUNT(*) FROM gt_lines WHERE license_bucket = 'open' GROUP BY stratum"
    ):
        by_stratum[row[0] or "unknown"] = row[1]

    by_volume: dict[str, int] = {}
    by_series: dict[str, int] = {}
    for row in conn.execute(
        "SELECT source, COUNT(*) FROM gt_lines WHERE license_bucket = 'open' GROUP BY source"
    ):
        vol = _volume_of(row[0])
        if vol:
            by_volume[vol] = by_volume.get(vol, 0) + row[1]
            series = vol.split(",")[0]
            by_series[series] = by_series.get(series, 0) + row[1]

    try:
        _pieces, enum = enumerate_pieces(conn, today=today)
    except Exception:  # pragma: no cover - defensive; katalog absent
        enum = None

    extraction = gather_extraction(today, enum.by_volume if enum else {}, editions_dir)
    cache_records, cache_by_volume = _edition_cache_stats(edition_cache)

    return GtReport(
        generated_at=today.isoformat() if isinstance(today, date) else str(today),
        n_gt_total=n_open + n_nc,
        n_open=n_open,
        n_nc=n_nc,
        by_stratum=by_stratum,
        by_volume=by_volume,
        by_series=by_series,
        enum_pieces=enum.pieces if enum else 0,
        enum_localizable=enum.localizable if enum else 0,
        enum_with_work=enum.with_work if enum else 0,
        enum_with_folio=enum.with_folio_range if enum else 0,
        enum_by_volume=dict(enum.by_volume) if enum else {},
        audit=audit or {},
        extraction=extraction,
        cache_records=cache_records,
        cache_by_volume=cache_by_volume,
    )


def _load_extracted(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def gather_extraction(
    today: date, katalog_by_volume: dict[str, int], editions_dir: Path = DEFAULT_EDITIONS_DIR
) -> list[VolumeExtraction]:
    """One row per §70 volume: its source channel and what the extraction yielded.

    Reads the per-source JSON written by ``leibniz align ingest``; a volume with
    two ingested sources (an IA scan and the GWLB PDF) also gets the
    cross-source agreement from :func:`~leibniz.align.ingest.cross_source_qa`.
    """
    rows: list[VolumeExtraction] = []
    seen: set[tuple[int, int]] = set()
    for v in expired_volumes(today):
        if not isinstance(v.volume, int) or (v.series, v.volume) in seen:
            continue
        seen.add((v.series, v.volume))
        label = volume_label(v.series, v.volume)
        katalog_n = katalog_by_volume.get(label, 0)
        readable = readable_sources(v.series, v.volume)
        if not readable:
            entries = sources_for(v.series, v.volume)
            kind = entries[0].kind if entries else "none"
            note = "; ".join(e.note for e in entries if e.note)
            rows.append(
                VolumeExtraction(
                    label, kind, CHANNEL_TERMS.get(kind, ""), katalog_pieces=katalog_n, note=note
                )
            )
            continue
        extracted = [(src, _load_extracted(text_path(src, editions_dir))) for src in readable]
        primary = next(((src, d) for src, d in extracted if d is not None), None)
        if primary is None:
            src = readable[0]
            rows.append(
                VolumeExtraction(
                    label, src.kind, src.terms, katalog_pieces=katalog_n, note="not ingested yet"
                )
            )
            continue
        src, d = primary
        # multi-part volumes (VI,4 A/C/…): merge the parts' pieces
        pieces: dict[str, str] = {}
        n_pages = n_reading = n_anom = 0
        for s2, d2 in extracted:
            if d2 is None or s2.kind != src.kind:
                continue
            for k, pv in d2["pieces"].items():
                pieces.setdefault(k, pv["text"])
            n_pages += d2["n_pages"]
            n_reading += d2["n_reading_pages"]
            n_anom += len(d2["anomalies"])
        row = VolumeExtraction(
            label,
            src.kind,
            src.terms,
            n_pages=n_pages,
            n_reading_pages=n_reading,
            n_pieces=len(pieces),
            n_chars=sum(len(t) for t in pieces.values()),
            n_anomalies=n_anom,
            katalog_pieces=katalog_n,
        )
        other = next((d2 for s2, d2 in extracted if d2 is not None and s2.kind != src.kind), None)
        if other is not None:
            qa, _only = cross_source_qa(
                pieces, {k: pv["text"] for k, pv in other["pieces"].items()}
            )
            row.qa_agreement = qa.mean_agreement
            row.qa_flagged = qa.n_flagged
            row.qa_sampled = qa.n_sampled
        rows.append(row)
    return rows


def _edition_cache_stats(path: Path | None) -> tuple[int, dict[str, int]]:
    if path is None or not path.exists():
        return 0, {}
    cache = json.loads(path.read_text(encoding="utf-8"))
    return len(cache), {}


def render_gt(rep: GtReport) -> str:
    """Render the ``reports/gt-factory.md`` deliverable."""
    started = rep.n_open > 0
    lines: list[str] = []
    A = lines.append
    A("# GT factory — retro-aligned ground truth at scale (Phase C2)")
    A("")
    A(
        f"_Leibniz Legible, Phase C2. Generated {rep.generated_at}. Deliverable of "
        "PROMPTS C2 (SPECS §1.4, §6, §7). Counts are queried from the store by "
        "`leibniz align gt-report`; prose is templated._"
    )
    A("")
    _render_method(A)
    _render_sources(A, rep)
    _render_extraction_validation(A)
    _render_enumeration(A, rep)
    _render_yield(A, rep)
    _render_strata(A, rep)
    if not started:
        _render_deferred(A, rep)
    _render_cost(A, rep)
    _render_runbook(A)
    return "\n".join(lines)


def _render_sources(A, rep: GtReport) -> None:
    A("## §70 volumes: sources and extracted reading text")
    A("")
    if not rep.extraction:
        A("_No volume sources registered._")
        A("")
        return
    A(
        "Each §70-expired volume's reading text is read from a **free digital copy of "
        "the print** (`align/volumes_sources.py`, verified 2026-09-11): a public-domain "
        "library scan on the Internet Archive with its OCR layer (preferred — an "
        "unencumbered channel), the Leibniz-Archiv's own PDF in the GWLB repositorium "
        "(CC BY-NC channel; the reading text itself is §70-free, but the channel is a "
        "partner's, so it is used only where no scan exists and flagged for the lawyer "
        "memo), or the Potsdam Arbeitsstelle's born-digital text PDFs. The extractor "
        "(`align/edition.py`) reads the page layout — running head, body type vs. the "
        "smaller apparatus type (learned per volume), piece headings, margin line "
        "numbers, the editorial dateline/*Überlieferung* block — and emits one reading "
        "text per printed piece with its page anchors; apparatus, commentary, "
        "introductions and indices never enter it (SPECS §7.2)."
    )
    A("")
    A(
        "| Volume | Source | Pages read | Pieces extracted | Katalog pieces | Reading text | "
        "Anomalies | Cross-source agreement |"
    )
    A("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    tot_pieces = tot_chars = tot_kat = 0
    n_readable = 0
    for row in rep.extraction:
        if row.kind == "none" or row.note == "not ingested yet":
            src = "—" if row.kind == "none" else row.kind
            A(f"| {row.volume} | {src} | — | — | {row.katalog_pieces:,} | _{row.note}_ | — | — |")
            continue
        n_readable += 1
        tot_pieces += row.n_pieces
        tot_chars += row.n_chars
        tot_kat += row.katalog_pieces
        qa = (
            f"{row.qa_agreement:.1%} ({row.qa_flagged}/{row.qa_sampled} flagged)"
            if row.qa_agreement is not None
            else "—"
        )
        A(
            f"| {row.volume} | {row.kind} | {row.n_reading_pages:,}/{row.n_pages:,} | "
            f"{row.n_pieces:,} | {row.katalog_pieces:,} | {row.n_chars / 1000:,.0f}k chars | "
            f"{row.n_anomalies} | {qa} |"
        )
    n_none = sum(1 for r in rep.extraction if r.kind == "none")
    A("")
    A(
        f"**{n_readable} of {len(rep.extraction)} §70 volumes have a readable free digital "
        f"copy** → **{tot_pieces:,} printed pieces / {tot_chars / 1e6:.2f}M characters of "
        f"reading text extracted**; {n_none} volumes have no free digital copy at all "
        "(1923–1927 prints are US-public-domain on HathiTrust; a TELOTA/Göttingen ask "
        "covers the rest — operator). Terms per channel: "
        + "; ".join(f"**{k}** — {v}" for k, v in CHANNEL_TERMS.items() if k != "none")
        + "."
    )
    A("")
    if rep.cache_records:
        A(
            f"**Edition cache:** {rep.cache_records:,} katalog records (manuscript witnesses "
            "citing an ingested volume) carry their piece's reading text in "
            "`data/gt/edition_cache.json` — the factory's input."
        )
        A("")


def _render_cost(A, rep: GtReport) -> None:
    A("## What the extraction costs — and the optional vision upgrade")
    A("")
    readable = [r for r in rep.extraction if r.kind != "none" and r.n_pages]
    pages = sum(r.n_reading_pages for r in readable)
    ocr_pages = sum(r.n_reading_pages for r in readable if r.kind in ("ia", "gwlb"))
    A(
        f"The text-layer path above costs **nothing but crawl time** (~1 GB of hOCR/PDF, "
        f"polite ≤1 req/s). Its labels carry the OCR layer's residual error (Tesseract on "
        f"the IA scans, ABBYY on the GWLB PDFs, none on the born-digital Potsdam volumes); "
        f"the cross-source agreement column measures it where two layers exist. A cleaner "
        f"label comes from a **vision-LLM pass over the {ocr_pages:,} OCR'd reading-text "
        f"pages** (of {pages:,} reading pages total), the B2 extractor (`align/pdftext.py`, "
        "validated live on Leibniz print) — priced from the measured ~2,000 tokens/page "
        "(≈1,500 in / ≈500 out at the observed page sizes):"
    )
    A("")
    A("| Model | $/M in · out | Per page | All OCR'd pages | Batch API (−50 %) |")
    A("| --- | --- | ---: | ---: | ---: |")
    for name, cin, cout in (
        ("Claude Sonnet 5", 2.0, 10.0),
        ("Claude Opus 5", 5.0, 25.0),
        ("gpt-4o-class (B1/B2 adapter)", 2.5, 10.0),
    ):
        per = (1500 * cin + 500 * cout) / 1e6
        A(
            f"| {name} | ${cin:.2f} · ${cout:.2f} | ${per:.4f} | ${per * ocr_pages:,.0f} | "
            f"${per * ocr_pages / 2:,.0f} |"
        )
    A("")
    A(
        "So the whole-corpus vision pass is a **two-figure to low-three-figure dollar item** "
        "(SPECS §10 budgets $500–3,000 for all LLM passes), and it need not run on every "
        "page: mint from the free OCR text first, then re-extract only the pieces that "
        "actually minted lines (a fraction of the pages) and re-mint — the factory is "
        "idempotent. A two-model QA sample (`assess_extraction`, ~200 pages × 2 models) "
        "adds a few dollars. No GPU is involved in C2; alignment is CPU work."
    )
    A("")


def _render_extraction_validation(A) -> None:
    A("## Extraction path — validated live on real Leibniz print")
    A("")
    A(
        "The one factory step that cannot be unit-tested offline — vision-LLM extraction "
        "of the reading text with the apparatus excluded (step 3), and the "
        "`assess_extraction` QA over it (Open Q #12) — was **run live this session** on real "
        "Leibniz edition print (Gerhardt, *Die philosophischen Schriften* Bd. II, 1875, "
        "public domain — archive.org `diephilosophisc02gerhgoog`; the Leibniz↔Arnauld "
        "correspondence). A public-domain edition stands in for the §70 AA print purely to "
        "exercise the extraction machinery; the production open bucket is §70 AA text only."
    )
    A("")
    A(
        "- **Reading text, apparatus excluded:** on a clean Latin page (leaf 110) `gpt-4o` "
        "transcribed the constituted text faithfully and **correctly dropped** the running "
        "head (*Leibniz an Antoine Arnauld*), the page number (81), and the signature mark — "
        "the reading-text/paratext separation SPECS §7.2 demands."
    )
    A(
        "- **QA caught a real divergence:** a two-model spot-check (`gpt-4o` vs the weaker "
        "`gpt-4o-mini` as control) over 2 pages measured **mean agreement 0.67**, flagging "
        "**1 / 2** pages — precisely the code-switched Latin/German page (leaf 90) where the "
        "control model dropped ~60 % of the text (883 vs 2,349 chars). That is exactly the "
        "unstable-extraction signal `assess_extraction` exists to surface for a per-volume "
        "error estimate. Evidence: `reports/gt-factory-extraction-qa.json`."
    )
    A(
        "- **Takeaway for scale:** use the stronger model for production extraction and the "
        "cross-model (or manual) agreement as the QA gate; code-switched and heavy-apparatus "
        "pages are where extraction error concentrates, so the per-volume error estimate must "
        "be stratified, not a single number."
    )
    A("")


def _render_method(A) -> None:
    A("## The factory")
    A("")
    A(
        "Scales the B2 retro-aligner (98.8 % yield / 97.5 % precision on favourable "
        "material under real HTR) across every §70-expired AA volume. Each piece is "
        "localized and minted by one chain:"
    )
    A("")
    A(
        "1. **Enumerate pieces** — a §70-expired volume's pieces *are* the katalog "
        "records whose AA reference cites it (`legal.py` × `katalog_records.aa_refs`)."
    )
    A(
        "2. **Localize the scan** — the A3 crosswalk gives each piece's GWLB work; the "
        "folio resolver (Open Q #10: canvas labels are folio numbers) maps the katalog "
        "`Bl.` range to the exact canvases."
    )
    A(
        "3. **Reading text** — extracted from the expired volume's print, apparatus "
        "excluded (B2's `pdftext`, SPECS §7.2), with a spot-check extraction-error "
        "estimate (`assess_extraction`)."
    )
    A(
        "4. **Align & mint** — the B2 aligner (banded for long multi-page pieces) projects "
        "the reading text onto the C1 HTR lines; the **stratum sets the mint threshold** "
        "(fair copies 0.55 … heavy revision 0.72 — drafts held to a higher bar), and "
        "below-threshold lines are discarded (SPECS §6)."
    )
    A(
        "5. **License gate** — §70 reading text → `license_bucket='open'`; any "
        "Transkriptionspool-derived pairs → `'nc'`, never in a CC BY export (SPECS §7.3), "
        "enforced at mint time by `GtPair`."
    )
    A("")


def _render_enumeration(A, rep: GtReport) -> None:
    A("## Piece enumeration (localizable §70 corpus)")
    A("")
    if rep.enum_pieces:
        loc_pct = 100.0 * rep.enum_localizable / rep.enum_pieces
        A(f"- **§70 pieces cited in the katalog:** {rep.enum_pieces:,}")
        A(
            f"- **With a crosswalked work:** {rep.enum_with_work:,} · "
            f"**with a folio range:** {rep.enum_with_folio:,}"
        )
        A(
            f"- **Localizable (work + folio range → canvases):** {rep.enum_localizable:,} "
            f"({loc_pct:.1f}%)"
        )
        if rep.enum_by_volume:
            A("")
            A("| Volume | §70 pieces |")
            A("| --- | ---: |")
            for vol, n in sorted(rep.enum_by_volume.items()):
                A(f"| {vol} | {n:,} |")
    else:
        A(
            "_No §70 pieces enumerated yet — needs the katalog scraped (A3 full run) so "
            "`aa_refs` and the crosswalk are populated._"
        )
    A("")


def _render_yield(A, rep: GtReport) -> None:
    A("## Minted ground truth")
    A("")
    A(f"- **Open-bucket aligned lines (CC BY):** {rep.n_open:,}")
    A(f"- **NC-bucket lines (internal only, never exported):** {rep.n_nc:,}")
    pct_target = 100.0 * rep.n_open / TARGET_OPEN_LINES if TARGET_OPEN_LINES else 0.0
    A(
        f"- **vs the ≥{TARGET_OPEN_LINES // 1000}k target:** {pct_target:.0f}% "
        f"· **vs PHILIUMM's ~{PHILIUMM_BASELINE // 1000}k baseline:** "
        f"{(100.0 * rep.n_open / PHILIUMM_BASELINE):.0f}%"
    )
    A("")
    if rep.by_volume:
        A("| Volume | Open lines |")
        A("| --- | ---: |")
        for vol, n in sorted(rep.by_volume.items()):
            A(f"| {vol} | {n:,} |")
        A("")


def _render_strata(A, rep: GtReport) -> None:
    A("## By stratum")
    A("")
    if rep.by_stratum:
        A("| Stratum | Open lines | Audited | Est. precision |")
        A("| --- | ---: | ---: | ---: |")
        for stratum in ("fair_copy", "light_revision", "heavy_revision", "scrap", "unknown"):
            n = rep.by_stratum.get(stratum, 0)
            if n == 0:
                continue
            aud = rep.audit.get(stratum)
            aud_n = f"{aud[0]:,}" if aud else "—"
            aud_p = f"{aud[1]:.1%}" if aud else "_pending hand-audit_"
            A(f"| {stratum} | {n:,} | {aud_n} | {aud_p} |")
        A("")
        A(
            "Estimated precision comes from a hand-audit of ~200 lines stratified by "
            "stratum (the operator step below); until then the B2 measurement stands as "
            "the expectation — **97.5 % on fair copies**, degrading on drafts exactly as "
            "the omission conditions predicted, which is why drafts carry a higher mint "
            "threshold."
        )
    else:
        A("_No minted lines yet._")
    A("")


def _render_deferred(A, rep: GtReport) -> None:
    A("## Status of the live run")
    A("")
    A(
        "Of the factory's three inputs, **two are now in hand and one is on the operator's "
        f"machine.** (1) The katalog is scraped for every §70 volume ({rep.enum_pieces:,} "
        f"piece citations, {rep.enum_localizable:,} localizable to exact canvases through "
        "the crosswalk + folio resolver — `leibniz catalog scrape --expired-volumes`, "
        "~8 minutes of polite crawling, re-runnable anywhere). (2) The §70 reading text is "
        "extracted per piece from the volumes' free digital copies (table above; "
        "`leibniz align ingest`), joined to the katalog into the edition cache. (3) The C1 "
        "corpus HTR lines — 13.5M recognised lines — live in the operator's "
        "`data/inventory.sqlite`; this build environment has none, so `gt_lines` is still "
        "empty here. Minting is therefore one operator command away: run the three "
        "commands of the runbook below on the machine that holds the corpus store, then "
        "`leibniz align gt-report` fills the yield tables. The B2 prototype already proved "
        "the chain on one real piece (AA VI,4 N.109): GWLB IIIF → segment → HTR → §70 "
        "extraction → align."
    )
    A("")


def _render_runbook(A) -> None:
    A("## Operator runbook")
    A("")
    A("```bash")
    A("# On the machine holding the C1 corpus store (data/inventory.sqlite):")
    A("leibniz catalog scrape --expired-volumes  # every §70 volume's katalog records (~8 min)")
    A("leibniz catalog crosswalk                 # records → works")
    A("leibniz align pieces                      # enumerate §70 localizable pieces")
    A("leibniz align ingest                      # fetch + extract each volume's reading text")
    A("leibniz align edition-cache               # join to the katalog → the edition cache")
    A("leibniz align factory data/gt/edition_cache.json   # mint gt_lines (open bucket)")
    A("leibniz align gt-report                   # writes reports/gt-factory.md with the yield")
    A("# Optional clean-label upgrade (needs a key): vision-extract the minted pieces' pages")
    A("#   with `leibniz align extract`, rebuild the cache, re-run the factory (idempotent).")
    A("```")
    A("")
    A(
        "Discard-below-threshold is automatic (the aligner mints only ≥-threshold lines, "
        "the threshold set per stratum). Re-running is idempotent (gt_lines for a piece's "
        "line refs are replaced). NC-derived pairs are quarantined to `license_bucket='nc'` "
        "and excluded from every CC BY export."
    )
    A("")


__all__ = [
    "PHILIUMM_BASELINE",
    "TARGET_OPEN_LINES",
    "GtReport",
    "VolumeExtraction",
    "gather_extraction",
    "gather_gt",
    "render_gt",
]
