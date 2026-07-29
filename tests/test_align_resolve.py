"""Tests for the piece→canvas resolver (offline)."""

from __future__ import annotations

from leibniz import db
from leibniz.align.resolve import (
    parse_bl_range,
    parse_folio_label,
    resolve_canvases,
    resolve_piece,
)


def test_parse_folio_label() -> None:
    assert parse_folio_label("164r").num == 164
    assert parse_folio_label("164r").side == "r"
    assert parse_folio_label("164v").side == "v"
    assert parse_folio_label("12").side == ""
    assert parse_folio_label("[7]").num == 7
    assert parse_folio_label("cover") is None
    assert parse_folio_label(None) is None
    assert parse_folio_label("") is None


def test_parse_bl_range() -> None:
    assert parse_bl_range("164-169") == (164, 169)
    assert parse_bl_range("164r-169v") == (164, 169)
    assert parse_bl_range("12") == (12, 12)
    assert parse_bl_range("12r") == (12, 12)
    assert parse_bl_range("169-164") == (164, 169)  # normalised
    assert parse_bl_range("no folio here") is None
    assert parse_bl_range(None) is None


def _work_with_folios(labels: list[str]):
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("W", "LeibnizHandschriften"))
    for i, lab in enumerate(labels, start=1):
        db.upsert_page(conn, db.Page(work_id="W", seq=i, label=lab))
    conn.commit()
    return conn


def test_resolve_canvases_recto_verso() -> None:
    conn = _work_with_folios(["163r", "163v", "164r", "164v", "165r", "165v"])
    res = resolve_canvases(conn, "W", 164, 165)
    assert res.canvas_seqs == [3, 4, 5, 6]
    assert res.canvas_indices == [2, 3, 4, 5]  # 0-based for the IIIF fetcher
    assert res.resolved
    assert res.labelled_pages == 6


def test_resolve_single_folio() -> None:
    conn = _work_with_folios(["1r", "1v", "2r", "2v"])
    res = resolve_canvases(conn, "W", 2, 2)
    assert res.canvas_seqs == [3, 4]


def test_resolve_piece_from_signature() -> None:
    conn = _work_with_folios(["163r", "164r", "164v", "165r"])
    res = resolve_piece(conn, "W", "LH 4, 6, 18 Bl. 164-165")
    assert res is not None and res.canvas_seqs == [2, 3, 4]


def test_resolve_piece_no_folio_range() -> None:
    conn = _work_with_folios(["1r", "1v"])
    assert resolve_piece(conn, "W", "LH 4, 6, 18") is None  # no Bl. component


def test_unlabelled_pages_ignored() -> None:
    conn = _work_with_folios(["cover", "164r", "spine", "165r"])
    res = resolve_canvases(conn, "W", 164, 165)
    assert res.canvas_seqs == [2, 4]
    assert res.labelled_pages == 2  # only the two real folios counted
