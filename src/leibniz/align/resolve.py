"""Piece → canvas resolution (Phase C2's first build; STATUS Open Q #10).

The GT factory can only align an edition piece to the *manuscript lines that
transcribe it* — but a GWLB scan is a **convolute** of 16–414 canvases, and the
katalog links the whole convolute (a work id), not the piece's pages. B2's
localization finding is the key that unlocks this at scale:

    GWLB IIIF canvas labels **are folio numbers** (``164r``, ``164v``, …),
    and the katalog gives each piece a ``Bl.`` (Blatt / folio) range,
    so ``Bl. 164–169`` maps to exactly the canvases labelled 164r…169v.

C1 already stored those labels on every page (``pages.label``, from the METS
``ORDERLABEL`` / IIIF canvas label). This module turns a katalog piece's folio
range into the concrete pages (and 0-based IIIF canvas indices) that carry it:

* :func:`parse_folio_label` — ``"164r"`` → folio 164, side ``r``;
* :func:`parse_bl_range` / :func:`folio_range_from_signature` — pull the folio
  range out of a ``Bl.`` string or a full shelfmark (reusing the A3 normaliser);
* :func:`build_folio_index` / :func:`resolve_canvases` — map a work's pages by
  folio and select those inside a range, in reading order.

Pure and offline: everything reads the ``pages`` rows already in the store.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from leibniz import db
from leibniz.catalog.shelfmarks import normalize_signature

# A folio label: an optional bracket, digits, an optional recto/verso side, an
# optional sub-letter (``12a``). GWLB uses ``164r``/``164v``; some works label
# plain ``1``/``2`` (no side) or ``[1]``.
_FOLIO_RE = re.compile(r"^\[?(\d+)\s*([rv])?\s*([a-z])?\]?$", re.IGNORECASE)
# A Blatt range: ``164-169`` / ``164r-169v`` / ``12`` (single folio) / ``108v°``.
# The sides are captured: a piece on ``Bl. 5v`` is the verso only, and
# ``12v–13r`` is two pages, not all four of folios 12 and 13.
_BL_RANGE_RE = re.compile(
    r"(\d+)\s*([rv])?\s*°?\s*(?:[-–]\s*(\d+)\s*([rv])?\s*°?)?",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FolioRef:
    """A parsed folio label: number, optional side (``r``/``v``), sub-letter."""

    num: int
    side: str = ""
    sub: str = ""

    @property
    def sort_key(self) -> tuple[int, int, str]:
        # recto before verso; a page with no side sorts first within its folio.
        return (self.num, {"": 0, "r": 1, "v": 2}.get(self.side, 3), self.sub)


def parse_folio_label(label: str | None) -> FolioRef | None:
    """Parse a page folio label (``"164r"``) into a :class:`FolioRef`, or ``None``.

    Returns ``None`` for labels that are not folio numbers (cover, empty, ``"—"``),
    so callers can distinguish "no folio here" from a real folio.
    """
    if not label:
        return None
    m = _FOLIO_RE.match(label.strip())
    if m is None:
        return None
    return FolioRef(num=int(m.group(1)), side=(m.group(2) or "").lower(), sub=(m.group(3) or ""))


@dataclass(frozen=True, slots=True)
class FolioSpan:
    """A ``Bl.`` range with its sides: ``12v–13r`` is ``FolioSpan(12, 13, "v", "r")``.

    An empty side means the whole folio (``Bl. 12`` is both 12r and 12v); a side
    on the first folio says where the piece begins, one on the last folio where
    it ends.
    """

    lo: int
    hi: int
    side_lo: str = ""
    side_hi: str = ""

    @property
    def range(self) -> tuple[int, int]:
        return (self.lo, self.hi)

    @property
    def label(self) -> str:
        """``Bl. 12v–13r`` / ``Bl. 12`` / ``Bl. 1–2``, as a catalogue reads."""
        a = f"{self.lo}{self.side_lo}"
        b = f"{self.hi}{self.side_hi}"
        return f"Bl. {a}" if a == b else f"Bl. {a}–{b}"

    def includes(self, ref: FolioRef) -> bool:
        """Whether a page's folio label falls inside the span (a page whose label
        has no side is inside whenever its folio number is)."""
        if not self.lo <= ref.num <= self.hi:
            return False
        if ref.num == self.lo and self.side_lo == "v" and ref.side == "r":
            return False
        return not (ref.num == self.hi and self.side_hi == "r" and ref.side == "v")


def parse_bl_span(text: str | None) -> FolioSpan | None:
    """Extract a folio span, sides included, from a ``Bl.`` string.

    ``"164-169"`` → ``164–169``; ``"12v-13r"`` → ``12v–13r``; ``"108v°"`` →
    ``108v``; ``"12"`` → folio 12, both sides. ``None`` if no folio number.
    A reversed range is put in order (with its sides).
    """
    if not text:
        return None
    m = _BL_RANGE_RE.search(text)
    if m is None:
        return None
    lo, side_lo = int(m.group(1)), (m.group(2) or "").lower()
    if m.group(3):
        hi, side_hi = int(m.group(3)), (m.group(4) or "").lower()
    else:
        hi, side_hi = lo, side_lo
    if (hi, _SIDE_ORDER.get(side_hi, 0)) < (lo, _SIDE_ORDER.get(side_lo, 0)):
        lo, hi, side_lo, side_hi = hi, lo, side_hi, side_lo
    return FolioSpan(lo, hi, side_lo, side_hi)


_SIDE_ORDER = {"": 0, "r": 1, "v": 2}


def parse_bl_range(text: str | None) -> tuple[int, int] | None:
    """Extract a numeric folio range from a ``Bl.`` string (sides dropped).

    ``"164-169"`` → ``(164, 169)``; ``"12r"`` → ``(12, 12)``; ``"12"`` →
    ``(12, 12)``. Returns ``None`` if no leading folio number is present.
    :func:`parse_bl_span` keeps the sides.
    """
    span = parse_bl_span(text)
    return span.range if span is not None else None


def folio_span_from_signature(signature: str | None) -> FolioSpan | None:
    """Pull the folio span from a full shelfmark via the A3 normaliser.

    ``"LH 4, 6, 18 Bl. 164v-169r"`` → ``164v–169r``. Uses
    :func:`leibniz.catalog.shelfmarks.normalize_signature`, which already isolates
    the ``Bl.`` component, so this stays consistent with the crosswalk's parsing.
    """
    if not signature:
        return None
    return parse_bl_span(normalize_signature(signature).blatt)


def folio_range_from_signature(signature: str | None) -> tuple[int, int] | None:
    """:func:`folio_span_from_signature` without the sides: ``(164, 169)``."""
    span = folio_span_from_signature(signature)
    return span.range if span is not None else None


def build_folio_index(conn, work_id: str) -> dict[int, list[db.Page]]:
    """Map ``folio number -> pages`` for a work, using ``pages.label``.

    A folio usually has two pages (recto + verso). Pages whose label is not a
    folio number are omitted (they can never satisfy a folio range). Each folio's
    pages are ordered recto-before-verso then by canvas sequence.
    """
    return index_pages(db.get_pages(conn, work_id))


def index_pages(pages: list[db.Page]) -> dict[int, list[db.Page]]:
    """:func:`build_folio_index` over pages already read (the web layer places
    every catalogue record of a work against one index built once)."""
    index: dict[int, list[db.Page]] = {}
    for page in pages:
        ref = parse_folio_label(page.label)
        if ref is None:
            continue
        index.setdefault(ref.num, []).append(page)
    for group in index.values():
        group.sort(key=lambda p: (_side_rank(p.label), p.seq))
    return index


def _side_rank(label: str | None) -> int:
    ref = parse_folio_label(label)
    return {"": 0, "r": 1, "v": 2}.get(ref.side, 3) if ref else 4


@dataclass(slots=True)
class ResolveResult:
    """The outcome of resolving a folio range to a work's canvases."""

    work_id: str
    folio_lo: int
    folio_hi: int
    pages: list[db.Page]
    labelled_pages: int  # how many of the work's pages carry a folio label at all
    side_lo: str = ""  # "v": the range starts on the verso of folio_lo
    side_hi: str = ""  # "r": the range ends on the recto of folio_hi

    @property
    def canvas_seqs(self) -> list[int]:
        """1-based canvas sequences (``pages.seq``), reading order."""
        return [p.seq for p in self.pages]

    @property
    def canvas_indices(self) -> list[int]:
        """0-based IIIF canvas indices (``seq - 1``) for the prototype fetcher."""
        return [p.seq - 1 for p in self.pages]

    @property
    def resolved(self) -> bool:
        return bool(self.pages)


def resolve_canvases(
    conn,
    work_id: str,
    folio_lo: int,
    folio_hi: int,
    *,
    side_lo: str = "",
    side_hi: str = "",
) -> ResolveResult:
    """Select a work's pages whose folio falls in ``[folio_lo, folio_hi]``.

    The core of the piece→canvas resolver: given the folio range a katalog piece
    occupies, return the concrete pages, in reading order. ``side_lo="v"`` leaves
    out the recto of the first folio and ``side_hi="r"`` the verso of the last
    (``Bl. 12v–13r``); with no sides both sides of every folio are taken.
    """
    return select_folios(
        build_folio_index(conn, work_id),
        work_id,
        folio_lo,
        folio_hi,
        side_lo=side_lo,
        side_hi=side_hi,
    )


def select_folios(
    index: dict[int, list[db.Page]],
    work_id: str,
    folio_lo: int,
    folio_hi: int,
    *,
    side_lo: str = "",
    side_hi: str = "",
) -> ResolveResult:
    """:func:`resolve_canvases` over a folio index already built
    (:func:`build_folio_index` / :func:`index_pages`): the pages inside the
    span from ``folio_lo`` (on side ``side_lo``) to ``folio_hi`` (on side
    ``side_hi``), in canvas order.

    Before 2026-10 the sides were dropped, so a piece on ``Bl. 5v`` also took
    5r, and two pieces sharing a folio shared both its pages; the GT factory
    then minted each against the other's lines.
    """
    span = FolioSpan(folio_lo, folio_hi, side_lo, side_hi)
    labelled = sum(len(v) for v in index.values())
    pages: list[db.Page] = []
    for folio in range(folio_lo, folio_hi + 1):
        for page in index.get(folio, []):
            ref = parse_folio_label(page.label)
            if ref is None or span.includes(ref):
                pages.append(page)
    pages.sort(key=lambda p: p.seq)
    return ResolveResult(
        work_id=work_id,
        folio_lo=folio_lo,
        folio_hi=folio_hi,
        pages=pages,
        labelled_pages=labelled,
        side_lo=side_lo,
        side_hi=side_hi,
    )


def select_span(index: dict[int, list[db.Page]], work_id: str, span: FolioSpan) -> ResolveResult:
    """:func:`select_folios` for a :class:`FolioSpan`."""
    return select_folios(
        index, work_id, span.lo, span.hi, side_lo=span.side_lo, side_hi=span.side_hi
    )


def resolve_piece(conn, work_id: str, signature: str | None) -> ResolveResult | None:
    """Resolve a piece's canvases from its shelfmark's ``Bl.`` range.

    Convenience wrapper: parse the folio span out of the signature and select the
    work's matching pages. Returns ``None`` when the signature carries no folio
    range (the piece must then be localized another way — e.g. a whole small work,
    or a TELOTA page anchor).
    """
    span = folio_span_from_signature(signature)
    if span is None:
        return None
    return select_span(build_folio_index(conn, work_id), work_id, span)


__all__ = [
    "FolioRef",
    "FolioSpan",
    "ResolveResult",
    "build_folio_index",
    "folio_range_from_signature",
    "folio_span_from_signature",
    "index_pages",
    "parse_bl_range",
    "parse_bl_span",
    "parse_folio_label",
    "resolve_canvases",
    "resolve_piece",
    "select_folios",
    "select_span",
]
