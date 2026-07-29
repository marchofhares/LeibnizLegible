"""Tests for census computation + rendering, against a seeded in-memory store."""

from __future__ import annotations

from leibniz import db
from leibniz.harvest import census


def _work(conn, oid, primary, sets, pages, shelfmarks, has_iiif=False) -> None:
    db.upsert_work(
        conn,
        db.Work(
            gwlb_object_id=oid,
            set_name=primary,
            shelfmarks=shelfmarks,
            metadata={"leibniz_sets": sets, "has_iiif_manifest": has_iiif},
            n_canvases=pages,
        ),
    )


def _seed(conn) -> None:
    _work(conn, "A", "LeibnizHandschriften", ["LeibnizHandschriften", "Leibnitiana"], 100, ["LH 1"])
    _work(conn, "B", "LeibnizBriefwechsel", ["LeibnizBriefwechsel", "Leibnitiana"], 50, ["LBr. 2"])
    _work(
        conn,
        "C",
        "LeibnizMarginalien",
        ["LeibnizMarginalien"],
        200,
        ["Leibn. Marg. 3", "ZEN Leibn. Marg. 3"],
    )
    _work(conn, "D", "leibniz-rekonstruktionen", ["leibniz-rekonstruktionen", "Leibnitiana"], 0, [])
    _work(conn, "E", "Leibnitiana", ["Leibnitiana"], 10, ["Ms junk"])
    _work(conn, "F", "LeibnizHandschriften", ["LeibnizHandschriften"], 5, ["LH 1"])  # dup shelfmark


def test_totals_and_dedup() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    d = census.compute_census(conn, generated_at="2026-07-29T00:00:00Z")
    assert d.n_works == 6
    assert d.n_pages == 365  # 100+50+200+0+10+5
    assert d.multi_set_works == 3  # A, B, D belong to >1 set
    conn.close()


def test_primary_vs_membership_views() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    d = census.compute_census(conn, generated_at="x")
    by = {s.set_name: s for s in d.set_stats}
    # Primary (disjoint) view sums to the unique total.
    assert sum(s.primary_works for s in d.set_stats) == 6
    assert by["LeibnizHandschriften"].primary_works == 2
    assert by["LeibnizHandschriften"].primary_pages == 105
    assert by["Leibnitiana"].primary_works == 1  # only E is primary-Leibnitiana
    # Membership (overlapping) view counts a work in every set it belongs to.
    assert by["Leibnitiana"].membership_works == 4  # A, B, D, E
    conn.close()


def test_anomalies() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    d = census.compute_census(conn, generated_at="x")
    assert [r.object_id for r in d.zero_canvas] == ["D"]
    assert d.no_shelfmark == 1  # D
    # "LH 1" appears on both A and F.
    dup = dict(d.duplicate_shelfmarks)
    assert set(dup["LH 1"]) == {"A", "F"}
    conn.close()


def test_shelfmark_coverage() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    d = census.compute_census(conn, generated_at="x")
    cov = d.coverage_overall
    assert cov["LH"] == 2 and cov["LBr"] == 1 and cov["Marg"] == 1
    assert cov["other"] == 1 and cov["none"] == 1 and cov["LK"] == 0
    conn.close()


def test_image_delivery_split() -> None:
    conn = db.init_db(":memory:")
    _work(conn, "I", "LeibnizHandschriften", ["LeibnizHandschriften"], 40, ["LH 1"], has_iiif=True)
    _work(conn, "S", "LeibnizBriefwechsel", ["LeibnizBriefwechsel"], 60, ["LBr. 1"], has_iiif=False)
    d = census.compute_census(conn, generated_at="x")
    assert d.iiif_works == 1 and d.iiif_pages == 40
    by = {s.set_name: s for s in d.set_stats}
    assert by["LeibnizHandschriften"].iiif_works == 1
    assert by["LeibnizBriefwechsel"].iiif_works == 0
    md = census.render_census(d)
    assert "## Image delivery" in md
    conn.close()


def test_gate_band_boundaries() -> None:
    for pages, expected in [(149_999, False), (150_000, True), (250_000, True), (250_001, False)]:
        conn = db.init_db(":memory:")
        _work(conn, "X", "LeibnizHandschriften", ["LeibnizHandschriften"], pages, ["LH 1"])
        d = census.compute_census(conn, generated_at="x")
        assert d.in_gate_band is expected
        conn.close()


def test_render_contains_key_sections() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    d = census.compute_census(conn, generated_at="2026-07-29T00:00:00Z")
    md = census.render_census(d)
    conn.close()
    assert "# Corpus census" in md
    assert "Unique works" in md and "Unique page images" in md
    assert "365" in md  # the page total
    assert "## Works and pages per set" in md
    assert "## Shelfmark coverage" in md
    assert "## Anomalies" in md
    # 365 is well below the band → the report must say so plainly.
    assert "outside" in md.lower()
