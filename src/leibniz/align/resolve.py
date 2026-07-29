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
# A Blatt range: ``164-169`` / ``164r-169v`` / ``12`` (single folio).
_BL_RANGE_RE = re.compile(
    r"(\d+)\s*[rv]?\s*(?:[-–]\s*(\d+)\s*[rv]?)?",
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


def parse_bl_range(text: str | None) -> tuple[int, int] | None:
    """Extract a numeric folio range from a ``Bl.`` string.

    ``"164-169"`` → ``(164, 169)``; ``"12r"`` → ``(12, 12)``; ``"12"`` →
    ``(12, 12)``. Returns ``None`` if no leading folio number is present.
    """
    if not text:
        return None
    m = _BL_RANGE_RE.search(text)
    if m is None:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    return (lo, hi) if lo <= hi else (hi, lo)


def folio_range_from_signature(signature: str | None) -> tuple[int, int] | None:
    """Pull the folio range from a full shelfmark via the A3 normaliser.

    ``"LH 4, 6, 18 Bl. 164-169"`` → ``(164, 169)``. Uses
    :func:`leibniz.catalog.shelfmarks.normalize_signature`, which already isolates
    the ``Bl.`` component, so this stays consistent with the crosswalk's parsing.
    """
    if not signature:
        return None
    sig = normalize_signature(signature)
    return parse_bl_range(sig.blatt)


def build_folio_index(conn, work_id: str) -> dict[int, list[db.Page]]:
    """Map ``folio number -> pages`` for a work, using ``pages.label``.

    A folio usually has two pages (recto + verso). Pages whose label is not a
    folio number are omitted (they can never satisfy a folio range). Each folio's
    pages are ordered recto-before-verso then by canvas sequence.
    """
    index: dict[int, list[db.Page]] = {}
    for page in db.get_pages(conn, work_id):
        ref = parse_folio_label(page.label)
        if ref is None:
            continue
        index.setdefault(ref.num, []).append(page)
    for pages in index.values():
        pages.sort(key=lambda p: (_side_rank(p.label), p.seq))
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


def resolve_canvases(conn, work_id: str, folio_lo: int, folio_hi: int) -> ResolveResult:
    """Select a work's pages whose folio number falls in ``[folio_lo, folio_hi]``.

    The core of the piece→canvas resolver: given the folio range a katalog piece
    occupies, return the concrete pages (recto + verso of each folio), in reading
    order, ready for :mod:`leibniz.align.prototype` to fetch and segment.
    """
    index = build_folio_index(conn, work_id)
    labelled = sum(len(v) for v in index.values())
    pages: list[db.Page] = []
    for folio in range(folio_lo, folio_hi + 1):
        pages.extend(index.get(folio, []))
    pages.sort(key=lambda p: p.seq)
    return ResolveResult(
        work_id=work_id,
        folio_lo=folio_lo,
        folio_hi=folio_hi,
        pages=pages,
        labelled_pages=labelled,
    )


def resolve_piece(conn, work_id: str, signature: str | None) -> ResolveResult | None:
    """Resolve a piece's canvases from its shelfmark's ``Bl.`` range.

    Convenience wrapper: parse the folio range out of the signature and select the
    work's matching pages. Returns ``None`` when the signature carries no folio
    range (the piece must then be localized another way — e.g. a whole small work,
    or a TELOTA page anchor).
    """
    rng = folio_range_from_signature(signature)
    if rng is None:
        return None
    return resolve_canvases(conn, work_id, rng[0], rng[1])


__all__ = [
    "FolioRef",
    "ResolveResult",
    "build_folio_index",
    "folio_range_from_signature",
    "parse_bl_range",
    "parse_folio_label",
    "resolve_canvases",
    "resolve_piece",
]
