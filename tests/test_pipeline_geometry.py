"""Tests for the pure-geometry crop guards (C1 corpus-run robustness).

``estimate_crop_size`` replicates kraken 7.0.3's rectified ``output_shape``
computation, so these tests pin the guard to concrete geometries: sane lines
must pass untouched, and the live OOM-kill class — boundary points that rectify
far from the baseline — must be flagged before PIL would allocate the crop.
"""

from __future__ import annotations

from leibniz.pipeline import geometry


def test_straight_two_point_line_is_bounded() -> None:
    # kraken's 2-point fast path only rotates: bounded by the source bbox diagonal.
    est = geometry.estimate_crop_size(
        [(0, 0), (1000, 0)], [(0, -30), (1000, -30), (1000, 30), (0, 30)]
    )
    assert est is not None
    assert est[0] < 1200 and est[1] < 1200


def test_gently_curved_line_estimates_at_line_scale() -> None:
    bl = [(100, 200), (1000, 210), (1900, 200)]
    poly = [(100, 150), (1900, 150), (1900, 260), (100, 260)]
    est = geometry.estimate_crop_size(bl, poly)
    assert est is not None
    w, h = est
    assert 1500 < w < 2200  # ~ the baseline's cumulative length
    assert 50 < h < 300  # ~ the envelope height
    assert geometry.drop_reason(bl, poly, page_width=2000, page_height=2500) is None


def test_zero_length_segment_is_unprojectable() -> None:
    # kraken normalises per-segment directions: 0/0 → NaN → unpredictable.
    est = geometry.estimate_crop_size([(0, 0), (0, 0), (10, 0)], [(0, -5), (10, -5), (10, 5)])
    assert est is None


def test_far_flung_boundary_flags_oversize() -> None:
    # Boundary points axially deep inside a segment but far perpendicular: the
    # rectified extents explode — the class that OOM-killed the live run.
    bl = [(0.0, 0.0), (50_000.0, 0.0), (50_000.0, 1.0)]
    poly = [(10.0, -8000.0), (25_000.0, 8000.0), (30.0, 10.0)]
    est = geometry.estimate_crop_size(bl, poly)
    assert est is not None
    assert est[0] * est[1] > 100_000_000  # hundreds of megapixels
    reason = geometry.drop_reason(bl, poly, page_width=2000, page_height=2500)
    assert reason is not None and reason.startswith("oversize_crop")


def test_short_baseline_dropped_and_boundaryless_passes() -> None:
    assert geometry.drop_reason([(0, 0), (3, 0)], []) == "short_baseline"
    # No boundary: kraken fails these fast itself; fakes don't need one.
    assert geometry.drop_reason([(0, 0), (500, 0)], None) is None


def test_max_crop_area_floor_and_factor() -> None:
    assert geometry.max_crop_area(None, None) == geometry.MAX_CROP_AREA_FLOOR
    assert geometry.max_crop_area(4000, 4000) == geometry.PAGE_AREA_FACTOR * 16_000_000


def _png(w: int, h: int) -> bytes:
    """A minimal PNG header (IHDR only) — enough for the byte-peeking parser."""
    return (
        b"\x89PNG\r\n\x1a\n"
        + (13).to_bytes(4, "big")
        + b"IHDR"
        + w.to_bytes(4, "big")
        + h.to_bytes(4, "big")
        + b"\x00" * 5
    )


def test_png_dimensions_parses_header_only() -> None:
    assert geometry.png_dimensions(_png(900, 1)) == (900, 1)
    assert geometry.png_dimensions(_png(11, 11)) == (11, 11)
    assert geometry.png_dimensions(b"crop0") is None
    assert geometry.png_dimensions(b"") is None


def test_sliver_crops_are_refused_real_thin_lines_kept() -> None:
    # The live killer: a ~900×1 mask stripe that the recogniser's
    # aspect-preserving resize would blow up to >100k px wide (5.3 GB conv2d).
    assert geometry.crop_drop_reason(_png(900, 1)) == "sliver_crop:900x1"
    assert geometry.crop_drop_reason(_png(2, 500)) == "sliver_crop:2x500"
    # Real content stays: specks, and genuinely thin low-res lines (~90:1).
    assert geometry.crop_drop_reason(_png(11, 11)) is None
    assert geometry.crop_drop_reason(_png(898, 10)) is None
    # Non-PNG bytes are not judged here (engine's transformed-width cap covers).
    assert geometry.crop_drop_reason(b"not-a-png") is None
