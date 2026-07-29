"""Build the katalog ↔ works crosswalk (Phase A3).

Two match methods, in confidence order (SPECS §4.3 stores both method + conf):

1. **``gwlb_link`` (conf 1.0)** — the katalog record links out to the GWLB scan
   as ``…/resolve?id={object_id}``; that id *is* our ``works`` primary key, so
   the join is explicit and authoritative. This is the primary method.
2. **``shelfmark`` (conf 0.7)** — no link, but the record's signature normalises
   (:mod:`leibniz.catalog.shelfmarks`) to the same key as a work's
   ``shelfLocator``. Secondary, and never overrides a link for the same pair.

A GWLB link that points at an object we didn't harvest (out-of-scope holding, or
a non-Leibniz set) is counted as *unresolved* rather than dropped — it's a signal
about corpus boundaries, reported honestly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from leibniz import db
from leibniz.catalog.shelfmarks import signature_keys

CONF_GWLB_LINK = 1.0
CONF_SHELFMARK = 0.7

ProgressFn = Callable[[str], None]


@dataclass(slots=True)
class CrosswalkStats:
    """Bookkeeping returned by :func:`build_crosswalk`."""

    records: int = 0
    records_matched: int = 0
    records_unmatched_with_shelfmark: int = 0
    records_foreign: int = 0  # unmatched and no recognisable Leibniz signature
    gwlb_link_matches: int = 0
    gwlb_link_unresolved: int = 0  # links to an object not in our works table
    shelfmark_matches: int = 0
    works_matched: set[str] = field(default_factory=set)


def build_work_key_index(conn) -> dict[str, list[str]]:
    """Map each normalized shelfmark key → the work ids that carry it.

    Built once per crosswalk run so the shelfmark method is a dict lookup, not a
    scan per record. One key can map to several works (shared base signatures —
    the multi-volume Marginalien, STATUS Open Q #4).
    """
    index: dict[str, list[str]] = {}
    for work in db.iter_works(conn):
        for key in signature_keys(work.shelfmarks):
            index.setdefault(key, []).append(work.gwlb_object_id)
    return index


def build_crosswalk(conn, *, progress: ProgressFn | None = None) -> CrosswalkStats:
    """Populate ``crosswalk`` from ``katalog_records`` × ``works``.

    Idempotent: :func:`db.upsert_crosswalk` keeps the higher-confidence method on
    a repeated pair, so re-running never degrades a link match to a shelfmark one.
    """
    work_index = build_work_key_index(conn)
    known_work_ids = {w.gwlb_object_id for w in db.iter_works(conn)}
    stats = CrosswalkStats()

    for rec in db.iter_katalog_records(conn):
        stats.records += 1
        matched_here: set[str] = set()

        for oid in rec.gwlb_ids:
            if oid in known_work_ids:
                db.upsert_crosswalk(
                    conn,
                    db.CrosswalkMatch(rec.record_id, oid, "gwlb_link", CONF_GWLB_LINK),
                )
                matched_here.add(oid)
                stats.gwlb_link_matches += 1
            else:
                stats.gwlb_link_unresolved += 1

        for key in signature_keys(rec.shelfmark_refs):
            for oid in work_index.get(key, []):
                if oid not in matched_here:
                    db.upsert_crosswalk(
                        conn,
                        db.CrosswalkMatch(rec.record_id, oid, "shelfmark", CONF_SHELFMARK),
                    )
                    matched_here.add(oid)
                    stats.shelfmark_matches += 1

        if matched_here:
            stats.records_matched += 1
            stats.works_matched.update(matched_here)
        elif signature_keys(rec.shelfmark_refs):
            stats.records_unmatched_with_shelfmark += 1
        else:
            stats.records_foreign += 1
        if progress is not None:
            progress(rec.record_id)

    conn.commit()
    return stats


__all__ = [
    "CONF_GWLB_LINK",
    "CONF_SHELFMARK",
    "CrosswalkStats",
    "build_crosswalk",
    "build_work_key_index",
]
