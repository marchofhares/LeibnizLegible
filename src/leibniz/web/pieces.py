"""Where a catalogue piece sits on its scan (W4, text access).

The Arbeitskatalog describes *pieces* — a letter, a draft, a treatise — while
the GWLB scans *convolutes*, works of 16 to 414 canvases, and the crosswalk
links a record to the whole work. A record's shelfmark carries a ``Bl.``
(folio) range, and the C2 resolver (:mod:`leibniz.align.resolve`) turns that
range into the work's canvases by their folio labels. This module applies the
same rule for the web layer — the one the GT factory used to localize 11,595
pieces (``align/volumes.py``: the record's shelfmark, its best crosswalk link)
— and says for every record either which pages carry it or why it cannot be
placed, so that ``/api/records/{id}/text`` can serve a piece across its folios
and the work page can offer the link only where it resolves.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from leibniz import db
from leibniz.align.resolve import folio_range_from_signature, index_pages, select_folios


def folio_label(lo: int, hi: int) -> str:
    """``Bl. 1–2``, or ``Bl. 12`` for a single folio, as a catalogue reads."""
    return f"Bl. {lo}" if lo == hi else f"Bl. {lo}–{hi}"


@dataclass(frozen=True, slots=True)
class Placement:
    """A record placed on a work's pages: the folio range, the shelfmark that
    carried it, and the pages in canvas order."""

    record_id: str
    work_id: str
    signature: str
    folio_lo: int
    folio_hi: int
    pages: list[db.Page]

    @property
    def folio_label(self) -> str:
        return folio_label(self.folio_lo, self.folio_hi)

    @property
    def page_ids(self) -> list[str]:
        return [p.id for p in self.pages]


@dataclass(frozen=True, slots=True)
class Unplaced:
    """A record that cannot be placed, and the reason, in words a 404 can carry."""

    record_id: str
    reason: str


def _folio_range(record: db.KatalogRecord) -> tuple[str, tuple[int, int]] | None:
    """The first of the record's shelfmarks that names a ``Bl.`` range, with it."""
    for signature in record.shelfmark_refs:
        rng = folio_range_from_signature(signature)
        if rng is not None:
            return signature, rng
    return None


def place(
    record: db.KatalogRecord, work_id: str | None, index: dict[int, list[db.Page]]
) -> Placement | Unplaced:
    """Place one record on one work, given the work's folio index
    (:func:`leibniz.align.resolve.index_pages`, built once per work)."""
    rid = record.record_id
    if work_id is None:
        return Unplaced(rid, f"record {rid} is not linked to a digitized work")
    found = _folio_range(record)
    if found is None:
        marks = "; ".join(m for m in record.shelfmark_refs if m)
        what = (
            f"its shelfmark {marks!r} names"
            if marks
            else "it carries no shelfmark, so nothing names"
        )
        return Unplaced(
            rid, f"record {rid} cannot be placed on the scan: {what} no folio (Bl.) range"
        )
    signature, (lo, hi) = found
    res = select_folios(index, work_id, lo, hi)
    if not res.resolved:
        return Unplaced(
            rid,
            f"record {rid} cannot be placed on the scan: {signature!r} names folios "
            f"{folio_label(lo, hi)}, but no page of work {work_id} carries a folio label in "
            f"that range ({res.labelled_pages} of its pages carry folio labels)",
        )
    return Placement(rid, work_id, signature, lo, hi, res.pages)


def place_all(
    work_id: str, pages: list[db.Page], records: list[db.KatalogRecord]
) -> dict[str, Placement | Unplaced]:
    """Every record of a work against one folio index, by record id."""
    index = index_pages(pages)
    return {rec.record_id: place(rec, work_id, index) for rec in records}


def place_record(conn: sqlite3.Connection, record: db.KatalogRecord) -> Placement | Unplaced:
    """Place a record on the work its best crosswalk link names (the factory's
    rule); where it links several works, the first that places it wins."""
    links = db.crosswalk_for_record(conn, record.record_id)
    if not links:
        return place(record, None, {})
    last: Placement | Unplaced | None = None
    for link in links:
        last = place(record, link.work_id, index_pages(db.get_pages(conn, link.work_id)))
        if isinstance(last, Placement):
            return last
    assert last is not None
    return last


__all__ = ["Placement", "Unplaced", "folio_label", "place", "place_all", "place_record"]
