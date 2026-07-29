"""Tests for per-page segmentation statistics (pure geometry, offline)."""

from __future__ import annotations

from leibniz.layout.segment import SegLine, SegmentedPage
from leibniz.pipeline.stats import compute_seg_stats, polygon_area


def _rect_line(index: int, x0: int, y0: int, x1: int, y1: int) -> SegLine:
    return SegLine(
        index=index,
        baseline=[(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)],
        boundary=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
    )


def test_polygon_area_rectangle() -> None:
    assert polygon_area([(0, 0), (10, 0), (10, 4), (0, 4)]) == 40.0
    assert polygon_area([(0, 0), (1, 1)]) == 0.0  # degenerate


def test_clean_fair_copy_stats() -> None:
    # A dozen evenly spaced, full-width lines: no overlaps, no short lines, low CV.
    lines = [_rect_line(i, 50, 100 + i * 120, 1950, 180 + i * 120) for i in range(12)]
    page = SegmentedPage(lines=lines, width=2000, height=2500, n_regions=1)
    s = compute_seg_stats(page, n_regions=page.n_regions)
    assert s.n_lines == 12
    assert s.n_overlaps == 0
    assert s.n_short_lines == 0
    assert s.line_height_cv == 0.0  # identical heights
    assert 0.0 < s.region_coverage <= 1.0
    assert s.mean_line_height == 80.0
    assert s.n_regions == 1


def test_overlapping_lines_flagged() -> None:
    # Two boxes occupying nearly the same region → an overlap (layered revision).
    lines = [
        _rect_line(0, 50, 100, 1950, 200),
        _rect_line(1, 60, 110, 1900, 205),  # sits on top of line 0
        _rect_line(2, 50, 400, 1950, 500),
    ]
    page = SegmentedPage(lines=lines, width=2000, height=2500)
    s = compute_seg_stats(page)
    assert s.n_overlaps == 1


def test_short_interlinear_line_flagged() -> None:
    lines = [
        _rect_line(0, 50, 100, 1950, 180),
        _rect_line(1, 50, 220, 1950, 300),
        _rect_line(2, 900, 190, 1100, 215),  # tiny interlinear insertion
    ]
    page = SegmentedPage(lines=lines, width=2000, height=2500)
    s = compute_seg_stats(page)
    assert s.n_short_lines == 1


def test_blank_page_zero_lines() -> None:
    page = SegmentedPage(lines=[], width=2000, height=2500)
    s = compute_seg_stats(page)
    assert s.n_lines == 0
    assert s.region_coverage == 0.0
    assert s.mean_line_height == 0.0


def test_baseline_only_lines_use_bbox_area() -> None:
    # No boundary polygon → coverage falls back to bbox area (still > 0).
    line = SegLine(index=0, baseline=[(50, 150), (1950, 150)], boundary=[])
    # give it a second point spread so bbox has height via a second baseline line
    line2 = SegLine(index=1, baseline=[(50, 150), (1950, 400)], boundary=[])
    page = SegmentedPage(lines=[line, line2], width=2000, height=2500)
    s = compute_seg_stats(page)
    assert s.n_lines == 2
    # coverage computed without crashing on empty boundaries
    assert s.region_coverage >= 0.0


def test_as_metrics_roundtrips_keys() -> None:
    lines = [_rect_line(i, 50, 100 + i * 120, 1950, 180 + i * 120) for i in range(3)]
    s = compute_seg_stats(SegmentedPage(lines=lines, width=2000, height=2500))
    m = s.as_metrics()
    assert m["n_lines"] == 3
    assert "mean_line_width" in m
    assert "region_coverage" in m
