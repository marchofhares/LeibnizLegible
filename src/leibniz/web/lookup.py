"""Go to what a scholar cites (2026-10): a shelfmark and its folio, an
Akademie-Ausgabe number, a work or page id.

Search finds words; a citation names a place. ``LH IV, 6, 18 Bl. 1r`` is a
folio of a convolute, ``A VI, 4 N. 109`` a piece of the edition, and a reader
who types either wants that page, not a list of pages that mention it. This
module reads a query as a citation where it can be one and says where it
points:

* **Shelfmark**, with or without ``Bl.``: the works whose shelfmark has the
  same key (:func:`leibniz.catalog.shelfmarks.signature_key` — Roman or Arabic,
  any punctuation), then, given a folio, the pages that carry it by the folio
  rule the catalogue pieces use (:mod:`leibniz.align.resolve`). A shelfmark
  that is only the beginning of others (``LH 35, 3``) lists those; a bare
  section (``LH 35``) points at its place in the browse index.
* **Akademie-Ausgabe**: ``A``/``AA``, series (Roman or Arabic), volume, and
  ``N.``/``Nr.`` piece — the catalogue records that carry that reference, each
  placed on its scan (:mod:`leibniz.web.pieces`) or, where it cannot be, its
  work with the reason.
* **Ids**: a work id or a page id the store knows.

Anything else is not a citation (``kind`` is ``None``) and search alone
answers it. Pure functions over prepared indexes; the API builds them once per
process.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field

from leibniz import db
from leibniz.align.resolve import folio_span_from_signature, index_pages, select_span
from leibniz.catalog.shelfmarks import normalize_signature, roman_to_int, signature_key
from leibniz.web import pieces

MAX_TARGETS = 20
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}

# "A VI, 4 N. 109", "AA VI,4 N.109", "A 6 4 Nr 109", "AA II, 1, N. 130a"
_AA = re.compile(
    r"^\s*A{1,2}\.?\s+(?P<series>[IVX]+|[1-8])\s*[,.]?\s*(?P<volume>\d+)\s*[A-D]?\s*"
    r"(?:,?\s*(?:N|Nr|No)\.?\s*(?P<piece>\d+\s*[a-z]?))?\s*\.?\s*$",
    re.IGNORECASE,
)
_WORK_ID = re.compile(r"^(?:\d{8}|DE-611-HS-\d+|\d{8,10}X?)$")
# A family label typed in lower case ("lh 4, 6, 18"): the shelfmark parser reads
# "LH" case-sensitively, as the signature it is in a catalogue, not a word.
_FAMILY_CASE = re.compile(r"^(lh|lbr|lk)(?=[\s.,f\d]|$)", re.IGNORECASE)
_FAMILY_SPELLING = {"lh": "LH", "lbr": "LBr", "lk": "LK"}
_PAGE_ID = re.compile(r"^(?P<work>[A-Za-z0-9-]+):(?P<seq>\d{4})$")


@dataclass(slots=True)
class Target:
    """One place a citation points at: a page, a work, or a section of the index."""

    kind: str  # "page" | "work" | "section"
    url: str  # a path on this site
    label: str  # what the citation names there, as a reader reads it
    work_id: str | None = None
    page_id: str | None = None
    detail: str | None = None  # e.g. the work's title, or why a piece is not on its folio
    text_url: str | None = None  # a catalogue piece's text across its folios


@dataclass(slots=True)
class Lookup:
    query: str
    kind: str | None  # "shelfmark" | "aa" | "id" | None (not a citation)
    targets: list[Target] = field(default_factory=list)
    reason: str | None = None  # a citation that leads nowhere says why
    more: int = 0  # targets beyond MAX_TARGETS

    def to_dict(self) -> dict:
        out = asdict(self)
        out["targets"] = [
            {k: v for k, v in asdict(t).items() if v is not None} for t in self.targets
        ]
        return out


# ---- reading a query ------------------------------------------------------------ #


@dataclass(frozen=True, slots=True)
class AaRef:
    series: int
    volume: str
    piece: str | None

    @property
    def label(self) -> str:
        out = f"AA {ROMAN.get(self.series, self.series)},{self.volume}"
        return f"{out} N. {self.piece}" if self.piece else out


def parse_aa(query: str) -> AaRef | None:
    """An Akademie-Ausgabe reference, or ``None``."""
    m = _AA.match(query or "")
    if m is None:
        return None
    raw = m.group("series")
    series = int(raw) if raw.isdigit() else roman_to_int(raw.upper())
    if series is None or not 1 <= series <= 8:
        return None
    piece = re.sub(r"\s+", "", m.group("piece") or "").lower() or None
    return AaRef(series, str(int(m.group("volume"))), piece)


def aa_key(series: object, volume: object, piece: object) -> tuple[int, str, str] | None:
    """The key a catalogue AA reference is filed under (strings and numbers alike)."""
    try:
        s = int(str(series))
    except (TypeError, ValueError):
        return None
    vol = str(volume).strip()
    num = str(piece or "").strip().lower()
    if not vol or not num:
        return None
    return s, vol.lstrip("0") or "0", num


def build_aa_index(conn: sqlite3.Connection) -> dict[tuple[int, str, str], list[str]]:
    """``(series, volume, piece)`` → the ids of the catalogue records citing it."""
    out: dict[tuple[int, str, str], list[str]] = {}
    for rec in db.iter_katalog_records(conn):
        for ref in rec.aa_refs or []:
            key = aa_key(ref.get("series"), ref.get("volume"), ref.get("piece"))
            if key is not None and rec.record_id not in out.get(key, []):
                out.setdefault(key, []).append(rec.record_id)
    return out


def build_shelfmark_index(works: Iterable[db.Work]) -> dict[str, list[str]]:
    """Shelfmark key → the ids of the works that carry it."""
    out: dict[str, list[str]] = {}
    for work in works:
        for mark in work.shelfmarks or []:
            key = signature_key(str(mark))
            if key is not None and work.gwlb_object_id not in out.get(key, []):
                out.setdefault(key, []).append(work.gwlb_object_id)
    return out


# ---- resolving ------------------------------------------------------------------- #


def _folio_text(label: str | None, seq: int) -> str:
    return f"fol. {label}" if label else f"canvas {seq}"


def _work_target(work: db.Work | None, work_id: str, detail: str | None = None) -> Target:
    title = (work.title if work else None) or work_id
    marks = ", ".join(work.shelfmarks or []) if work else ""
    return Target(
        kind="work",
        url=f"/work/{work_id}",
        label=marks or title,
        work_id=work_id,
        detail=detail or (title if marks and title != marks else None),
    )


def _by_shelfmark(
    conn: sqlite3.Connection,
    query: str,
    shelfmarks: Mapping[str, Sequence[str]],
    titles: Mapping[str, str],
) -> Lookup | None:
    sig = normalize_signature(query)
    key = sig.key
    if key is None:
        return None
    out = Lookup(query, "shelfmark")
    works = list(shelfmarks.get(key, ()))
    span = folio_span_from_signature(query) if sig.blatt else None
    if not works:
        # the beginning of other shelfmarks: "LH 35, 3" → its convolutes
        prefix = f"{key},"
        works = sorted(w for k, ids in shelfmarks.items() if k.startswith(prefix) for w in ids)
        if not works:
            out.reason = f"no digitized work has the shelfmark {query.strip()!r}"
            return out
        if sig.family == "LH" and len(sig.parts) == 1 and sig.parts[0].isdigit():
            out.targets.append(
                Target("section", f"/browse#lh-{sig.parts[0]}", f"LH {sig.parts[0]}")
            )
            out.more = len(works)
            return out
    for work_id in works:
        work = db.get_work(conn, work_id)
        if work is None:
            continue
        if span is None:
            out.targets.append(_work_target(work, work_id, titles.get(work_id)))
            continue
        found = select_span(index_pages(db.get_pages(conn, work_id)), work_id, span)
        if not found.resolved:
            out.targets.append(
                _work_target(
                    work,
                    work_id,
                    f"no page of this work carries a folio label in {span.label} "
                    f"({found.labelled_pages} of its pages carry folio labels)",
                )
            )
            continue
        first, last = found.pages[0], found.pages[-1]
        where = _folio_text(first.label, first.seq)
        if last.id != first.id:
            where += f" to {_folio_text(last.label, last.seq)} ({len(found.pages)} pages)"
        out.targets.append(
            Target(
                kind="page",
                url=f"/page/{first.id}",
                label=f"{', '.join(work.shelfmarks or [work_id])}, {where}",
                work_id=work_id,
                page_id=first.id,
                detail=titles.get(work_id) or work.title,
            )
        )
    return out


def _by_aa(
    conn: sqlite3.Connection,
    ref: AaRef,
    query: str,
    aa_index: Mapping[tuple[int, str, str], Sequence[str]],
) -> Lookup:
    out = Lookup(query, "aa")
    if ref.piece is None:
        out.reason = f"{ref.label} names a volume: add the piece (N. …) to go to it"
        return out
    key = aa_key(ref.series, ref.volume, ref.piece)
    records = list(aa_index.get(key, ())) if key else []
    if not records:
        out.reason = f"no catalogue record linked to a digitized work cites {ref.label}"
        return out
    for record_id in records:
        record = db.get_katalog_record(conn, record_id)
        if record is None:
            continue
        title = record.metadata.get("titel") or record.metadata.get("title") or record_id
        placed = pieces.place_record(conn, record)
        if isinstance(placed, pieces.Placement):
            first = placed.pages[0]
            work = db.get_work(conn, placed.work_id)
            marks = ", ".join(work.shelfmarks or []) if work else placed.work_id
            out.targets.append(
                Target(
                    kind="page",
                    url=f"/page/{first.id}",
                    label=f"{ref.label}: {marks}, {placed.folio_label}",
                    work_id=placed.work_id,
                    page_id=first.id,
                    detail=str(title),
                    text_url=f"/api/records/{record_id}/text?work={placed.work_id}",
                )
            )
            continue
        links = db.crosswalk_for_record(conn, record_id)
        if links:
            work = db.get_work(conn, links[0].work_id)
            target = _work_target(work, links[0].work_id, placed.reason)
            target.label = f"{ref.label}: {target.label}"
            out.targets.append(target)
    if not out.targets:
        out.reason = f"the records citing {ref.label} are not linked to a digitized work"
    return out


def _by_id(conn: sqlite3.Connection, query: str) -> Lookup | None:
    text = query.strip()
    m = _PAGE_ID.match(text)
    if m is not None:
        page = db.get_page(conn, text)
        if page is None:
            return None
        return Lookup(
            query,
            "id",
            [
                Target(
                    "page",
                    f"/page/{page.id}",
                    _folio_text(page.label, page.seq),
                    page.work_id,
                    page.id,
                )
            ],
        )
    if _WORK_ID.match(text):
        work = db.get_work(conn, text)
        if work is None:
            return None
        return Lookup(query, "id", [_work_target(work, text)])
    return None


def lookup(
    conn: sqlite3.Connection,
    query: str,
    *,
    shelfmarks: Mapping[str, Sequence[str]],
    aa_index: Mapping[tuple[int, str, str], Sequence[str]],
    titles: Mapping[str, str] | None = None,
) -> Lookup:
    """Read ``query`` as a citation and say where it points (:class:`Lookup`)."""
    text = " ".join((query or "").split())
    titles = titles or {}
    found: Lookup | None = None
    if text:
        ref = parse_aa(text)
        if ref is not None:
            found = _by_aa(conn, ref, text, aa_index)
        else:
            mark = _FAMILY_CASE.sub(lambda m: _FAMILY_SPELLING[m.group(1).lower()], text)
            found = _by_id(conn, text) or _by_shelfmark(conn, mark, shelfmarks, titles)
    if found is None:
        return Lookup(text, None)
    if len(found.targets) > MAX_TARGETS:
        found.more += len(found.targets) - MAX_TARGETS
        found.targets = found.targets[:MAX_TARGETS]
    return found


__all__ = [
    "MAX_TARGETS",
    "AaRef",
    "Lookup",
    "Target",
    "aa_key",
    "build_aa_index",
    "build_shelfmark_index",
    "lookup",
    "parse_aa",
]
