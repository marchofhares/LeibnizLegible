"""Tests for §70 volume ingestion / piece enumeration (offline)."""

from __future__ import annotations

from datetime import date

from leibniz import db
from leibniz.align.volumes import (
    assess_extraction,
    enumerate_pieces,
    expired_volume_index,
    volume_source,
)

TODAY = date(2026, 7, 29)


def test_expired_volume_index_uses_free_edition() -> None:
    idx = expired_volume_index(TODAY)
    assert (6, "4") in idx  # VI,4 (1999) free since 2025
    assert (1, "1") in idx
    # II,1 present via the 1926 edition (2006 Neubearbeitung is protected)
    assert idx[(2, "1")].first_publication_year == 1926
    # a protected volume is absent (VII,8 free only in 2050)
    assert (7, "8") not in idx


def test_volume_source_registry() -> None:
    src = volume_source(6, 4)
    assert src is not None and src.series == 6
    assert volume_source(99, 1) is None


def _seed(conn) -> None:
    db.upsert_work(conn, db.Work("W", "LeibnizHandschriften"))
    for i, lab in enumerate(["164r", "164v", "165r", "165v"], start=1):
        db.upsert_page(conn, db.Page(work_id="W", seq=i, label=lab))
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="REC1",
            metadata={"textart": "Reinschrift"},
            shelfmark_refs=["LH 4, 6, 18 Bl. 164-165"],
            aa_refs=[{"series": 6, "volume": 4, "piece": "109"}],
        ),
    )
    # a record citing a PROTECTED volume (VII,8) — must not become a piece
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="REC2",
            shelfmark_refs=["LH 35, 1, 1 Bl. 1-2"],
            aa_refs=[{"series": 7, "volume": 8, "piece": "5"}],
        ),
    )
    db.upsert_crosswalk(conn, db.CrosswalkMatch("REC1", "W", "gwlb_link", 1.0))
    conn.commit()


def test_enumerate_pieces_join() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    pieces, stats = enumerate_pieces(conn, today=TODAY)
    assert stats.pieces == 1  # only the expired-volume citation
    p = pieces[0]
    assert p.aa_label == "AA VI,4 N.109"
    assert p.work_id == "W"
    assert p.folio_range == (164, 165)
    assert p.textart == "Reinschrift"
    assert p.localizable
    assert stats.by_volume == {"VI,4": 1}


def test_enumerate_pieces_volume_filter() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    pieces, _ = enumerate_pieces(conn, today=TODAY, series=1)
    assert pieces == []  # no series-I pieces in the fixture


def test_enumerate_unlinked_piece_not_localizable() -> None:
    conn = db.init_db(":memory:")
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="R",
            shelfmark_refs=["LBr. 999 Bl. 1-2"],
            aa_refs=[{"series": 1, "volume": 1, "piece": "1"}],
        ),
    )
    conn.commit()
    pieces, stats = enumerate_pieces(conn, today=TODAY)
    assert len(pieces) == 1
    assert pieces[0].work_id is None and not pieces[0].localizable
    assert stats.with_work == 0 and stats.with_folio_range == 1


def test_assess_extraction() -> None:
    qa = assess_extraction(
        [
            ("same reading text here", "same reading text here"),  # agree
            ("", ""),  # both no-reading-text: agreement
            ("apparatus bled in lots extra words", "clean reading text"),  # diverge → flag
            ("found text", ""),  # empty disagreement → flag
        ]
    )
    assert qa.n_sampled == 4
    assert qa.n_flagged == 2
    assert qa.n_empty_disagreements == 1
    assert 0.0 < qa.error_rate < 1.0


def test_assess_extraction_empty() -> None:
    qa = assess_extraction([])
    assert qa.n_sampled == 0 and qa.error_rate == 0.0
