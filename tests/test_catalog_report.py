"""Tests for the crosswalk report computation + rendering."""

from __future__ import annotations

from leibniz import db
from leibniz.catalog import crosswalk as X
from leibniz.catalog import report as R


def _seed_and_build(conn) -> None:
    db.upsert_work(conn, db.Work("00068199", "LeibnizHandschriften", shelfmarks=["LH 35, 13, 2c"]))
    db.upsert_work(conn, db.Work("DE-611-HS-1", "LeibnizBriefwechsel", shelfmarks=["LBr. 57, 1"]))
    db.upsert_work(conn, db.Work("00099", "LeibnizHandschriften", shelfmarks=["LH 40, 1"]))
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            "342", metadata={"gwlb_ids": ["00068199"]}, shelfmark_refs=["LH 35, 13, 2c"]
        ),
    )
    db.upsert_katalog_record(conn, db.KatalogRecord("500", shelfmark_refs=["LBr 57,1"]))
    db.upsert_katalog_record(conn, db.KatalogRecord("33", shelfmark_refs=["London BL 4294"]))
    X.build_crosswalk(conn)


def test_compute_report_numbers() -> None:
    conn = db.init_db(":memory:")
    _seed_and_build(conn)
    rep = R.compute_crosswalk_report(conn, generated_at="2026-07-29T00:00:00Z")
    assert rep.n_records == 3
    assert rep.records_matched == 2
    assert rep.n_works == 3
    assert rep.works_matched == 2
    assert rep.method_counts.get("gwlb_link") == 1
    assert rep.method_counts.get("shelfmark") == 1
    # 66.7% of 3 works matched.
    assert 66.0 < rep.works_pct < 67.0
    conn.close()


def test_report_coverage_by_set() -> None:
    conn = db.init_db(":memory:")
    _seed_and_build(conn)
    rep = R.compute_crosswalk_report(conn, generated_at="x")
    cov = {c.set_name: c for c in rep.coverage_by_set}
    assert cov["LeibnizHandschriften"].works == 2
    assert cov["LeibnizHandschriften"].matched == 1  # only 00068199
    assert cov["LeibnizBriefwechsel"].matched == 1
    conn.close()


def test_report_lists_foreign_unmatched() -> None:
    conn = db.init_db(":memory:")
    _seed_and_build(conn)
    rep = R.compute_crosswalk_report(conn, generated_at="x")
    foreign_ids = {rid for rid, _ in rep.unmatched_foreign}
    assert "33" in foreign_ids  # London BL record has no Leibniz signature key
    conn.close()


def test_render_report_markdown() -> None:
    conn = db.init_db(":memory:")
    _seed_and_build(conn)
    rep = R.compute_crosswalk_report(
        conn, generated_at="2026-07-29T00:00:00Z", sample_queries=[{"q": "Newton"}]
    )
    md = R.render_crosswalk_report(rep)
    assert "# Katalog crosswalk" in md
    assert "CC BY 4.0" in md  # attribution present
    assert "Work coverage by set" in md
    assert "Operator command" in md
    conn.close()
