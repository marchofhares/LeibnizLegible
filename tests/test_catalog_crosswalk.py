"""Tests for the katalog ↔ works crosswalk (both match methods, honestly counted)."""

from __future__ import annotations

from leibniz import db
from leibniz.catalog import crosswalk as X


def _seed(conn) -> None:
    # Works.
    db.upsert_work(conn, db.Work("00068199", "LeibnizHandschriften", shelfmarks=["LH 35, 13, 2c"]))
    db.upsert_work(conn, db.Work("DE-611-HS-1", "LeibnizBriefwechsel", shelfmarks=["LBr. 57, 1"]))
    db.upsert_work(conn, db.Work("00099", "LeibnizHandschriften", shelfmarks=["LH 40, 1"]))
    # Records.
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            "342", metadata={"gwlb_ids": ["00068199"]}, shelfmark_refs=["LH 35, 13, 2c Bl. 64"]
        ),
    )  # gwlb link → 00068199
    db.upsert_katalog_record(
        conn, db.KatalogRecord("500", shelfmark_refs=["LBr 57,1"])
    )  # shelfmark → DE-611-HS-1
    db.upsert_katalog_record(
        conn, db.KatalogRecord("33", shelfmark_refs=["London BL Add.Mss. 4294"])
    )  # foreign
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord("999", metadata={"gwlb_ids": ["NONEXIST-9"]}, shelfmark_refs=["LH 99, 9"]),
    )  # unresolved link + unmatched Leibniz signature


def test_crosswalk_methods_and_counts() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    stats = X.build_crosswalk(conn)

    assert stats.gwlb_link_matches == 1
    assert stats.shelfmark_matches == 1
    assert stats.gwlb_link_unresolved == 1
    assert stats.records_matched == 2
    assert stats.records_foreign == 1
    assert stats.records_unmatched_with_shelfmark == 1
    assert stats.works_matched == {"00068199", "DE-611-HS-1"}
    conn.close()


def test_crosswalk_link_uses_gwlb_method_over_shelfmark() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    X.build_crosswalk(conn)
    # Record 342 matches 00068199 by BOTH link and shelfmark; the link (conf 1.0) wins.
    row = conn.execute(
        "SELECT match_method, match_conf FROM crosswalk "
        "WHERE katalog_record_id='342' AND work_id='00068199'"
    ).fetchone()
    assert row["match_method"] == "gwlb_link"
    assert row["match_conf"] == 1.0
    conn.close()


def test_shelfmark_match_normalises_spelling() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    X.build_crosswalk(conn)
    # 'LBr 57,1' (record) ↔ 'LBr. 57, 1' (work) normalise to the same key.
    row = conn.execute(
        "SELECT match_method FROM crosswalk WHERE katalog_record_id='500'"
    ).fetchone()
    assert row["match_method"] == "shelfmark"
    conn.close()


def test_crosswalk_is_idempotent() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    X.build_crosswalk(conn)
    n1 = db.count_crosswalk(conn)
    X.build_crosswalk(conn)
    assert db.count_crosswalk(conn) == n1
    conn.close()


def test_upsert_crosswalk_keeps_higher_confidence() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("W", "LeibnizHandschriften"))
    db.upsert_katalog_record(conn, db.KatalogRecord("R"))
    # shelfmark first, then the authoritative link → method upgrades to gwlb_link.
    db.upsert_crosswalk(conn, db.CrosswalkMatch("R", "W", "shelfmark", 0.7))
    db.upsert_crosswalk(conn, db.CrosswalkMatch("R", "W", "gwlb_link", 1.0))
    row = conn.execute("SELECT match_method, match_conf FROM crosswalk").fetchone()
    assert row["match_method"] == "gwlb_link" and row["match_conf"] == 1.0
    # A subsequent lower-confidence write must NOT downgrade it.
    db.upsert_crosswalk(conn, db.CrosswalkMatch("R", "W", "shelfmark", 0.7))
    row = conn.execute("SELECT match_method FROM crosswalk").fetchone()
    assert row["match_method"] == "gwlb_link"
    conn.close()


def test_build_work_key_index_groups_variants() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("A", "LeibnizHandschriften", shelfmarks=["LH XXXV, 3, 5"]))
    db.upsert_work(conn, db.Work("B", "LeibnizHandschriften", shelfmarks=["LH 35, 3, 5"]))
    index = X.build_work_key_index(conn)
    # Both works normalise to the same key → both reachable under it.
    assert set(index["LH 35,3,5"]) == {"A", "B"}
    conn.close()
