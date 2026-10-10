"""Where a catalogue piece sits on its scan (W4): the C2 resolver's rule,
applied record by record for the web layer, with the reason where it fails."""

from __future__ import annotations

from leibniz import db
from leibniz.align.resolve import index_pages
from leibniz.web import pieces

W1 = "00068642"  # three pages labelled 1r, 1v, 2r
W2 = "DE-611-HS-854976"  # one page, no folio label


def _record(rid: str, marks: list[str]) -> db.KatalogRecord:
    return db.KatalogRecord(record_id=rid, metadata={"titel": rid}, shelfmark_refs=marks)


def test_folio_label() -> None:
    assert pieces.folio_label(1, 2) == "Bl. 1–2"
    assert pieces.folio_label(12, 12) == "Bl. 12"


def test_the_fixture_record_is_placed_on_two_of_three_pages(store_path) -> None:
    conn = db.connect(store_path)
    rec = db.get_katalog_record(conn, "k-109")
    placed = pieces.place(rec, W1, index_pages(db.get_pages(conn, W1)))
    conn.close()
    assert isinstance(placed, pieces.Placement)
    # 1r, 1v and 2r: folio 2's recto lies inside Bl. 1-2 (skipped, but the piece's)
    assert placed.page_ids == [f"{W1}:0001", f"{W1}:0002", f"{W1}:0003"]
    assert (placed.folio_lo, placed.folio_hi, placed.folio_label) == (1, 2, "Bl. 1–2")
    assert placed.signature == "LH IV, 6, 18 Bl. 1-2" and placed.work_id == W1


def test_unplaced_records_say_why(store_path) -> None:
    conn = db.connect(store_path)
    index = index_pages(db.get_pages(conn, W1))
    conn.close()
    unlinked = pieces.place(_record("k-a", ["LH IV, 6, 18 Bl. 1"]), None, index)
    assert isinstance(unlinked, pieces.Unplaced)
    assert unlinked.reason == "record k-a is not linked to a digitized work"
    no_range = pieces.place(_record("k-b", ["LH IV, 6, 18"]), W1, index)
    assert isinstance(no_range, pieces.Unplaced)
    assert "its shelfmark 'LH IV, 6, 18' names no folio (Bl.) range" in no_range.reason
    no_mark = pieces.place(_record("k-c", []), W1, index)
    assert isinstance(no_mark, pieces.Unplaced) and "carries no shelfmark" in no_mark.reason
    far = pieces.place(_record("k-d", ["LH IV, 6, 18 Bl. 9"]), W1, index)
    assert isinstance(far, pieces.Unplaced)
    assert "'LH IV, 6, 18 Bl. 9' names folios Bl. 9" in far.reason
    assert f"no page of work {W1} carries a folio label in that range" in far.reason
    assert "(3 of its pages carry folio labels)" in far.reason
    # the first shelfmark with a range places the record (the factory reads the first only)
    second = pieces.place(_record("k-e", ["LH IV, 6, 18", "LH IV, 6, 18 Bl. 2"]), W1, index)
    assert isinstance(second, pieces.Placement)
    assert second.page_ids == [f"{W1}:0003"] and second.folio_label == "Bl. 2"
    assert second.signature == "LH IV, 6, 18 Bl. 2"


def test_place_all_uses_one_index_per_work(store_path) -> None:
    conn = db.connect(store_path)
    pages = db.get_pages(conn, W1)
    rec = db.get_katalog_record(conn, "k-109")
    conn.close()
    out = pieces.place_all(W1, pages, [rec, _record("k-b", ["LH IV, 6, 18"])])
    assert set(out) == {"k-109", "k-b"}
    assert isinstance(out["k-109"], pieces.Placement) and isinstance(out["k-b"], pieces.Unplaced)


def test_place_record_follows_the_best_link_then_the_next(store_path) -> None:
    conn = db.connect(store_path)
    assert isinstance(
        pieces.place_record(conn, db.get_katalog_record(conn, "k-109")), pieces.Placement
    )
    # linked to two works: the best link (W2, a gwlb_link at 1.0) has no folio
    # labels, so the shelfmark link to W1 places it
    two = _record("k-two", ["LH IV, 6, 18 Bl. 1"])
    db.upsert_katalog_record(conn, two)
    db.upsert_crosswalk(conn, db.CrosswalkMatch("k-two", W2, "gwlb_link", 1.0))
    db.upsert_crosswalk(conn, db.CrosswalkMatch("k-two", W1, "shelfmark", 0.7))
    # linked to nothing
    loose = _record("k-loose", ["LH IV, 6, 18 Bl. 1"])
    db.upsert_katalog_record(conn, loose)
    conn.commit()
    assert [m.work_id for m in db.crosswalk_for_record(conn, "k-two")] == [W2, W1]
    placed = pieces.place_record(conn, two)
    assert isinstance(placed, pieces.Placement) and placed.work_id == W1
    assert placed.page_ids == [f"{W1}:0001", f"{W1}:0002"]  # Bl. 1: 1r and 1v
    unplaced = pieces.place_record(conn, loose)
    assert isinstance(unplaced, pieces.Unplaced) and "not linked" in unplaced.reason
    # where no link places it, the last reason is the one reported
    only_w2 = _record("k-w2", ["LH IV, 6, 18 Bl. 1"])
    db.upsert_katalog_record(conn, only_w2)
    db.upsert_crosswalk(conn, db.CrosswalkMatch("k-w2", W2, "gwlb_link", 1.0))
    conn.commit()
    res = pieces.place_record(conn, only_w2)
    assert isinstance(res, pieces.Unplaced) and f"no page of work {W2}" in res.reason
    conn.close()


def test_place_record_on_the_work_the_page_offered_it_from() -> None:
    # A record linked to two works that both carry its folios: the work page
    # of the second work offers "Text of this piece", and the download must
    # serve that work's folios, not the best link's (2026-10).
    conn = db.init_db(":memory:")
    for wid in ("WA", "WB"):
        db.upsert_work(conn, db.Work(wid, "LeibnizHandschriften"))
        for seq, label in enumerate(("1r", "1v"), start=1):
            db.upsert_page(conn, db.Page(work_id=wid, seq=seq, label=label))
    rec = db.KatalogRecord(record_id="R", shelfmark_refs=["LH 1 Bl. 1"])
    db.upsert_katalog_record(conn, rec)
    db.upsert_crosswalk(conn, db.CrosswalkMatch("R", "WA", "gwlb_link", 1.0))
    db.upsert_crosswalk(conn, db.CrosswalkMatch("R", "WB", "shelfmark", 0.7))
    best = pieces.place_record(conn, rec)
    assert isinstance(best, pieces.Placement) and best.work_id == "WA"
    on_b = pieces.place_record(conn, rec, "WB")
    assert isinstance(on_b, pieces.Placement) and on_b.page_ids == ["WB:0001", "WB:0002"]
    stray = pieces.place_record(conn, rec, "WC")
    assert isinstance(stray, pieces.Unplaced) and "not linked to work WC" in stray.reason


def test_placement_keeps_the_sides() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("W", "LeibnizBriefwechsel"))
    for seq, label in enumerate(("108r", "108v", "109r"), start=1):
        db.upsert_page(conn, db.Page(work_id="W", seq=seq, label=label))
    rec = db.KatalogRecord(record_id="R", shelfmark_refs=["LBr 1 Bl. 108v°"])
    placed = pieces.place(rec, "W", pieces.index_pages(db.get_pages(conn, "W")))
    assert isinstance(placed, pieces.Placement)
    assert placed.page_ids == ["W:0002"] and placed.folio_label == "Bl. 108v"
