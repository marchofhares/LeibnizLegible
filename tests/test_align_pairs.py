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
