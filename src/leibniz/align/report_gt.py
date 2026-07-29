"""Render the GT-factory report (``reports/gt-factory.md``; Phase C2 deliverable).

Pulls the minted ``gt_lines`` aggregates from the store (counts by volume /
series / stratum / license bucket), the §70 piece enumeration (how much of the
expired corpus is localizable), and compares the open-bucket yield to PHILIUMM's
63k baseline and the ≥50k target. Like the C1 report, the numbers are queried so
an operator run fills them in; a *Status of the live run* note explains the zero
state until the factory has run against real corpus HTR + extracted edition text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from leibniz.align.volumes import enumerate_pieces

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


def _volume_of(source: str) -> str | None:
    m = _SOURCE_VOLUME_RE.search(source or "")
    return f"{m.group(1)},{m.group(2)}" if m else None


def gather_gt(conn, *, today: date, audit: dict[str, tuple[int, float]] | None = None) -> GtReport:
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
    )


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
    _render_extraction_validation(A)
    _render_enumeration(A, rep)
    _render_yield(A, rep)
    _render_strata(A, rep)
    if not started:
        _render_deferred(A)
    _render_runbook(A)
    return "\n".join(lines)


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


def _render_deferred(A) -> None:
    A("## Status of the live run")
    A("")
    A(
        "The factory is **built and offline-tested end-to-end** (piece enumeration, "
        "folio→canvas resolution, HTR gathering, banded alignment, stratum thresholding, "
        "license-gated minting, idempotent re-mint). Minting real ground truth additionally "
        "needs three inputs absent from this build environment: **(1)** the C1 corpus HTR "
        "lines (the pipeline is built but the segment/recognize passes need the kraken stack "
        "+ full image pull — see `htr-v1-sample.md`); **(2)** the full katalog scrape so "
        "`aa_refs` + the crosswalk cover the §70 volumes (A3 documented the operator run); "
        "**(3)** the extracted §70 reading text per piece (a vision pass with an API key + "
        "the volume page-anchors). With those, `leibniz align factory` mints `gt_lines` and "
        "`leibniz align gt-report` fills every number above. The B2 prototype already proved "
        "the chain on one real piece (AA VI,4 N.109): GWLB IIIF → segment → HTR → GPT-4o §70 "
        "extraction → align."
    )
    A("")


def _render_runbook(A) -> None:
    A("## Operator runbook")
    A("")
    A("```bash")
    A("# Prereqs: A3 full katalog scrape + C1 corpus recognition complete.")
    A("leibniz align pieces                      # enumerate §70 localizable pieces")
    A("#  extract each piece's §70 reading text (vision, apparatus excluded) into a")
    A("#  {record_id: text} JSON cache — needs OPENAI_API_KEY + volume page-anchors:")
    A("leibniz align extract <ia_id> <leaves> --out piece.txt   # per piece (B2 path)")
    A("leibniz align factory --edition-cache data/gt/edition_cache.json")
    A("leibniz align gt-report                   # writes reports/gt-factory.md")
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
    "gather_gt",
    "render_gt",
]
