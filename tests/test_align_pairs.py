"""Tests for minting gt_lines from an alignment (offline)."""

from __future__ import annotations

import pytest

from leibniz.align.align import AlignedLine, AlignmentResult
from leibniz.align.pairs import GtPair, count_open_bucket, insert_gt_pairs, result_to_pairs
from leibniz.db import init_db


def _result(*lines: AlignedLine) -> AlignmentResult:
    return AlignmentResult(
        lines=list(lines),
        threshold=0.6,
        norm_name="align-default",
        global_distance=0,
        edition_chars=100,
    )


def _line(ref: str, ed: str, conf: float, aligned: bool) -> AlignedLine:
    return AlignedLine(
        ref=ref,
        htr_text="htr " + ref,
        edition_text=ed,
        align_conf=conf,
        n_htr_chars=len(ed),
        n_matched=int(len(ed) * conf),
        aligned=aligned,
    )


def test_only_aligned_lines_minted() -> None:
    res = _result(
        _line("a", "prima linea", 0.9, True),
        _line("b", "", 0.1, False),
        _line("c", "tertia linea", 0.8, True),
    )
    pairs = result_to_pairs(res, source="AA VI,4 N.109", stratum="fair_copy")
    assert [p.line_image_ref for p in pairs] == ["a", "c"]
    assert all(p.license_bucket == "open" for p in pairs)


def test_license_and_stratum_validation() -> None:
    with pytest.raises(ValueError, match="license_bucket"):
        GtPair("r", "t", "s", "fair_copy", 0.9, "bogus")
    with pytest.raises(ValueError, match="stratum"):
        GtPair("r", "t", "s", "bogus", 0.9, "open")


def test_nc_bucket_kept_separate() -> None:
    res = _result(_line("a", "text", 0.9, True))
    pairs = result_to_pairs(res, source="Transkriptionspool", license_bucket="nc")
    assert count_open_bucket(pairs) == 0
    assert pairs[0].license_bucket == "nc"


def test_insert_into_gt_lines() -> None:
    res = _result(_line("a", "prima", 0.9, True), _line("b", "secunda", 0.85, True))
    pairs = result_to_pairs(res, source="AA VI,4 N.109", stratum="light_revision")
    conn = init_db(":memory:")
    n = insert_gt_pairs(conn, pairs)
    conn.commit()
    assert n == 2
    rows = conn.execute(
        "SELECT text, source, stratum, license_bucket FROM gt_lines ORDER BY id"
    ).fetchall()
    assert rows[0]["text"] == "prima"
    assert rows[0]["license_bucket"] == "open"
    assert rows[1]["stratum"] == "light_revision"
    conn.close()


def test_minted_text_is_one_line() -> None:
    # A manuscript line spanning two print lines: the slice carried the print's
    # newline (65 of the 200 audited lines did before 2026-10).
    res = _result(_line("P:0001:000", " J'ay fait\ncorriger  à la plume ", 0.9, True))
    (pair,) = result_to_pairs(res, source="s", record_id="R1")
    assert pair.text == "J'ay fait corriger à la plume"
    assert pair.record_id == "R1"
    raw = result_to_pairs(res, source="s", strip=False)
    assert "\n" in raw[0].text


def test_reader_rows_are_told_apart_and_kept_by_the_reset() -> None:
    from leibniz import db
    from leibniz.align.pairs import (
        count_reader_rows,
        delete_minted,
        ensure_gt_ownership,
        has_reader_rows,
        insert_gt_pairs,
        reader_from_source,
        record_readers,
    )

    v1 = "AA I,3 N.1 (§70-expired AA reading text; channel ia; katalog r1)"
    k2 = (
        "AA I,3 N.2 (§70-expired AA reading text; channel ia; "
        "reader trocr-kurrent-xvi-xvii; katalog r2)"
    )
    assert reader_from_source(v1) is None
    assert reader_from_source(k2) == "trocr-kurrent-xvi-xvii"
    assert reader_from_source(None) is None and reader_from_source("transkriptionspool") is None
    conn = db.init_db(":memory:")
    ensure_gt_ownership(conn)
    insert_gt_pairs(
        conn,
        [
            GtPair("P:0001:000", "eins", v1, "fair_copy", 0.9, "open", "r1"),
            GtPair("P:0001:001", "zwei", k2, "fair_copy", 0.9, "open", "r2"),
            GtPair("P:0001:002", "drei", k2, "fair_copy", 0.9, "open", "r2"),
            GtPair("P:0001:003", "nc", "transkriptionspool", "fair_copy", 0.9, "nc"),
        ],
    )
    assert has_reader_rows(conn, "r2") and not has_reader_rows(conn, "r1")
    assert record_readers(conn, "r2") == {"trocr-kurrent-xvi-xvii"}
    assert record_readers(conn, "r1") == {None} and record_readers(conn, "r9") == set()
    assert count_reader_rows(conn) == {"trocr-kurrent-xvi-xvii": 2}
    removed = delete_minted(conn)
    assert removed == {"open": 1}
    left = [r[0] for r in conn.execute("SELECT text FROM gt_lines ORDER BY id")]
    assert left == ["zwei", "drei", "nc"]  # the reader's rows and the unowned row stay
