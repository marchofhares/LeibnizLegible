"""Stratum heuristic — fair copy vs draft (Phase C2; STATUS Open Q #11).

Strata are first-class in this project (SPECS §6): every metric reports per
stratum, because an aggregate CER hides the failure mode that matters (a draft's
layered revisions). C2 needs a stratum label at *mint time* — B2 showed drafts
must clear a higher alignment threshold than fair copies — and C4 will calibrate
it corpus-wide. This module is the "start heuristic" the prompt asks for:
combine the **segmentation statistics** C1 stored (``page_stats``) with the
**katalog text type** (``Reinschrift`` / ``Konzept`` / …) into one of the SPECS
§4.3 strata.

The two signals are complementary: the katalog type is a human judgement of the
*document class* (a fair copy vs a draft) but is often absent; the segmentation
stats are always available and measure the *layout consequence* of revision
(irregular line heights, overlapping boxes from interlinear insertions, short
snippet lines). Where both are present and agree, confidence is high; where they
disagree, the layout evidence is trusted for the mint threshold but the
disagreement is recorded.

The field this feeds is named ``stratum_heuristic`` on purpose (SPECS §6:
"honesty in naming") — it is a layout+type heuristic, not a diplomatic judgement.
Pure and offline.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from leibniz.db import PageStats

# Segmentation-stat thresholds (fractions are per line). Tuned to the C1 stats
# definitions; deliberately conservative so a clean copy is not misread as a draft.
SCRAP_MAX_LINES = 3  # a handful of lines → a scrap/note, not a piece stratum
FAIR_MAX_CV = 0.28  # line-height coefficient of variation
FAIR_MAX_OVERLAP_FRAC = 0.05  # overlapping-box pairs ÷ lines
FAIR_MAX_SHORT_FRAC = 0.15  # short (interlinear) lines ÷ lines
HEAVY_MIN_CV = 0.45
HEAVY_MIN_OVERLAP_FRAC = 0.20
HEAVY_MIN_SHORT_FRAC = 0.35

# Katalog ``textart`` keywords → the document-class stratum they imply. Matched
# as case-insensitive substrings; the AA/katalog vocabulary is German.
_TEXTART_STRATUM: tuple[tuple[tuple[str, ...], str], ...] = (
    (("reinschrift", "abfertigung", "ausfertigung"), "fair_copy"),
    (("abschrift", "kopie"), "fair_copy"),  # a clean copy by another hand
    (("konzept", "entwurf"), "heavy_revision"),  # author's working draft
    (("auszug", "exzerpt", "notiz", "aufzeichnung", "fragment"), "scrap"),
)


def stratum_from_textart(textart: str | None) -> str | None:
    """Map a katalog ``textart`` to a stratum, or ``None`` if not recognised."""
    t = (textart or "").lower()
    if not t:
        return None
    for keys, stratum in _TEXTART_STRATUM:
        if any(k in t for k in keys):
            return stratum
    return None


def classify_page(ps: PageStats) -> str:
    """Classify one page's stratum from its segmentation statistics.

    Returns ``unknown`` for a page with no lines (blank/cover — not a stratum),
    ``scrap`` for a few-line note, else ``fair_copy`` / ``light_revision`` /
    ``heavy_revision`` from the line-height regularity, overlap, and short-line
    signals (each a documented signature of interlinear revision).
    """
    n = ps.n_lines
    if n <= 0:
        return "unknown"
    if n <= SCRAP_MAX_LINES:
        return "scrap"
    overlap_frac = (ps.n_overlaps or 0) / n
    short_frac = (ps.n_short_lines or 0) / n
    cv = ps.line_height_cv or 0.0

    heavy_signals = (
        int(cv >= HEAVY_MIN_CV)
        + int(overlap_frac >= HEAVY_MIN_OVERLAP_FRAC)
        + int(short_frac >= HEAVY_MIN_SHORT_FRAC)
    )
    if heavy_signals >= 2 or overlap_frac >= 0.5:
        return "heavy_revision"
    if (
        cv <= FAIR_MAX_CV
        and overlap_frac <= FAIR_MAX_OVERLAP_FRAC
        and short_frac <= FAIR_MAX_SHORT_FRAC
    ):
        return "fair_copy"
    return "light_revision"


_SEVERITY = {"fair_copy": 0, "light_revision": 1, "heavy_revision": 2}


@dataclass(slots=True)
class StratumResult:
    """A piece's heuristic stratum with the evidence that produced it."""

    stratum: str
    confidence: float
    seg_stratum: str | None
    katalog_stratum: str | None
    n_pages: int
    n_lines: int

    @property
    def agree(self) -> bool:
        return (
            self.seg_stratum is not None
            and self.katalog_stratum is not None
            and self.seg_stratum == self.katalog_stratum
        )


def _aggregate(pages: Sequence[PageStats]) -> PageStats | None:
    """Pool several pages' stats into one line-weighted synthetic page."""
    real = [p for p in pages if p.n_lines > 0]
    if not real:
        return None
    total_lines = sum(p.n_lines for p in real)
    overlaps = sum(p.n_overlaps or 0 for p in real)
    short = sum(p.n_short_lines or 0 for p in real)
    # line-weighted mean CV across pages
    cv = sum((p.line_height_cv or 0.0) * p.n_lines for p in real) / total_lines
    return PageStats(
        page_id="<aggregate>",
        n_lines=total_lines,
        line_height_cv=cv,
        n_overlaps=overlaps,
        n_short_lines=short,
    )


def classify_piece(pages: Sequence[PageStats], *, textart: str | None = None) -> StratumResult:
    """Classify a piece's stratum from its pages' seg-stats + the katalog type.

    Combines the two signals: the segmentation stats (always available) give the
    layout stratum; the katalog ``textart`` (often absent) gives the document
    class. When both are present the label leans on the katalog class but is
    pulled toward the layout evidence on strong disagreement (a "Reinschrift"
    whose layout screams heavy revision is recorded as ``light_revision``, not a
    clean fair copy). Confidence rises when the two agree.
    """
    agg = _aggregate(pages)
    seg = classify_page(agg) if agg is not None else None
    kat = stratum_from_textart(textart)
    n_pages = len(pages)
    n_lines = agg.n_lines if agg is not None else 0

    if seg is None and kat is None:
        return StratumResult("unknown", 0.0, seg, kat, n_pages, n_lines)
    if seg is None:
        return StratumResult(kat, 0.5, seg, kat, n_pages, n_lines)
    if kat is None:
        return StratumResult(seg, 0.6, seg, kat, n_pages, n_lines)

    # Both present. 'scrap' from either wins (it is a size judgement).
    if "scrap" in (seg, kat):
        return StratumResult("scrap", 0.7 if seg == kat else 0.5, seg, kat, n_pages, n_lines)
    if seg == kat:
        return StratumResult(seg, 0.9, seg, kat, n_pages, n_lines)
    # Disagreement among fair/light/heavy: take the more severe of the two, but
    # only one step toward it (don't call a katalog fair copy 'heavy' outright).
    hi = max(_SEVERITY.get(seg, 1), _SEVERITY.get(kat, 1))
    lo = min(_SEVERITY.get(seg, 1), _SEVERITY.get(kat, 1))
    blended = ["fair_copy", "light_revision", "heavy_revision"][min(hi, lo + 1)]
    return StratumResult(blended, 0.5, seg, kat, n_pages, n_lines)


__all__ = [
    "StratumResult",
    "classify_page",
    "classify_piece",
    "stratum_from_textart",
]
