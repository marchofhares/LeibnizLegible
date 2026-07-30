"""Pure-geometry guards for the recognition crop (C1 corpus-run robustness).

kraken's ``extract_polygons`` (7.0.3, fast path) rectifies each line's bounding
polygon into "along-baseline × perpendicular" coordinates and hands PIL an
output image sized from the **raw, unclamped min/max extents** of those
rectified points. Its closest-segment assignment measures only *axial*
overshoot, and rectified x grows with the baseline's **cumulative** length — so
a garbage baseline (a scribbling, doubling-back polyline; a real segmenter
artifact observed on the first live corpus run) implies a crop of hundreds of
megapixels. PIL then allocates it: the process is OOM-killed mid-allocation
with no Python traceback (the operator saw bare ``Terminated``), which would
stall a weeks-long run at the same page forever.

This module replicates kraken's arithmetic cheaply and dependency-free (no
numpy, no kraken) so the pipeline can refuse such lines *before* PIL allocates
anything: :func:`estimate_crop_size` mirrors the ``pol_dst_pts`` →
``output_shape`` computation, and :func:`max_crop_area` sets the acceptance
cap. Fully offline-testable.
"""

from __future__ import annotations

from collections.abc import Sequence

Point = tuple[float, float]

# Minimum baseline length (px) kraken's polygon extractor accepts; shorter lines
# raise and are skipped rather than allowed to fail the whole page.
MIN_BASELINE_PX = 5.0

# A rectified crop may legitimately exceed the page a little (dewarping a long
# curved line stretches it); it may never dwarf the page. The floor keeps the
# cap meaningful when page dimensions are unrecorded (census: delivery
# derivatives observed up to ~12 MP).
PAGE_AREA_FACTOR = 4.0
MAX_CROP_AREA_FLOOR = 24_000_000  # px²


def dedupe_points(pts: object) -> list[Point]:
    """Drop consecutive points that collapse onto the same integer pixel.

    kraken normalises per-segment direction vectors (``diff / norm``) and slices
    its dewarping mesh per baseline segment: a zero-length segment is a 0/0 →
    NaN, and a (sub-)pixel one a zero-width mesh quad (PIL ``1.0 / w``
    divide-by-zero). The polyline *length* check can't see either — a
    zero-length segment adds nothing to the total — so collapse the points
    themselves; at raster resolution this is loss-free.
    """
    out: list[Point] = []
    for p in pts or []:  # type: ignore[union-attr]
        q = (float(p[0]), float(p[1]))
        if not out or (int(out[-1][0]), int(out[-1][1])) != (int(q[0]), int(q[1])):
            out.append(q)
    return out


def polyline_length(pts: Sequence[Point]) -> float:
    """Total polyline length (0.0 if absent or a single point)."""
    if not pts or len(pts) < 2:
        return 0.0
    total = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:], strict=False):
        total += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return total


def estimate_crop_size(
    baseline: Sequence[Point], boundary: Sequence[Point]
) -> tuple[int, int] | None:
    """Predict kraken's rectified ``output_shape`` for one line: ``(width, height)``.

    Mirrors ``extract_polygons``'s fast path (kraken 7.0.3): each boundary point
    is assigned the baseline segment with the smallest *axial overshoot*
    ``max(-x, x - |seg|)``, its rectified x is the cumulative baseline length at
    that segment plus the axial coordinate, its rectified y the signed
    perpendicular distance; the output image spans the raw min/max of those.
    Returns ``None`` when the geometry cannot be projected at all (fewer than
    two distinct baseline points, a zero-length segment, no boundary) — cases
    kraken itself raises on.
    """
    bl = [(float(p[0]), float(p[1])) for p in (baseline or [])]
    poly = [(float(p[0]), float(p[1])) for p in (boundary or [])]
    if len(bl) < 2 or not poly:
        return None

    norms: list[float] = []
    normed: list[Point] = []
    for (x0, y0), (x1, y1) in zip(bl, bl[1:], strict=False):
        n = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if n == 0.0:
            return None  # kraken: 0/0 → NaN coordinates → unpredictable
        norms.append(n)
        normed.append(((x1 - x0) / n, (y1 - y0) / n))
    cum = [0.0]
    for n in norms:
        cum.append(cum[-1] + n)

    if len(bl) == 2:
        # kraken's straight-line path only rotates the polygon's bbox — the
        # output is bounded by the source bbox diagonal, never pathological.
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        d = int(((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2) ** 0.5) + 2
        return d, d

    if len(poly) > 200:
        # kraken approximates >50-point polygons (tol 2 px) before projecting;
        # a stride subsample (last point kept) is enough to detect extent
        # blowups while keeping this guard O(200 × segments) per line.
        step = len(poly) // 200 + 1
        poly = poly[::step] + [poly[-1]]

    dst_x: list[float] = []
    dst_y: list[float] = []
    for px, py in poly:
        best_k = 0
        best_over: float | None = None
        best_x = 0.0
        for k, ((bx, by), (ux, uy)) in enumerate(zip(bl[:-1], normed, strict=True)):
            x_loc = (px - bx) * ux + (py - by) * uy
            over = max(-x_loc, x_loc - norms[k])
            if best_over is None or over < best_over:
                best_k, best_over, best_x = k, over, x_loc
        bx, by = bl[best_k]
        ux, uy = normed[best_k]
        dst_x.append(cum[best_k] + best_x)
        dst_y.append(ux * (py - by) - uy * (px - bx))
    width = int(max(dst_x)) - int(min(dst_x)) + 1
    height = int(max(dst_y)) - int(min(dst_y)) + 1
    return width, height


def max_crop_area(page_width: int | None, page_height: int | None) -> float:
    """The largest rectified crop area (px²) accepted for a line of this page."""
    return max(PAGE_AREA_FACTOR * (page_width or 0) * (page_height or 0), MAX_CROP_AREA_FLOOR)


def drop_reason(
    baseline: object,
    boundary: object,
    *,
    page_width: int | None = None,
    page_height: int | None = None,
) -> str | None:
    """Why this line must not be handed to kraken's extractor (``None`` = safe).

    The reasons map to the live failure classes: a too-short baseline raises
    inside kraken; a zero-length (float) baseline segment NaNs its coordinate
    normalisation; an oversize rectified extent is the OOM-kill class this
    module exists for. A *missing* boundary is deliberately not pre-dropped —
    kraken raises on it instantly and cheaply (``No boundary given``), the
    per-line crop fallback turns that into a dropped line, and the pipeline's
    cropper is injected so non-kraken croppers (and the offline fakes) may not
    need a boundary at all. The extent guard therefore fires only when there is
    a boundary to project.
    """
    bl = dedupe_points(baseline)
    if polyline_length(bl) < MIN_BASELINE_PX:
        return "short_baseline"
    poly = dedupe_points(boundary)
    if len(poly) < 3:
        return None  # kraken fails these fast; fakes don't need boundaries
    est = estimate_crop_size(bl, poly)
    if est is None:
        return "degenerate_baseline"
    if est[0] * est[1] > max_crop_area(page_width, page_height):
        return f"oversize_crop:{est[0]}x{est[1]}"
    return None


# A dewarped crop can be degenerate even when its stored geometry looks sane.
# The live corpus run produced a ~900×1 px sliver crop (an empty mask stripe):
# the recogniser's aspect-preserving resize to model input height multiplied
# its width by >100, and a single conv2d then allocated 5.3 GB — under Linux
# overcommit that OOM-kills the *machine*, not the process, so no in-process
# handler ever fires. Bounds on the actual crop raster:
MIN_CROP_SIDE_PX = 4  # nothing readable below this
MAX_CROP_ASPECT = 100.0  # real text lines observed up to ~90:1 on small scans


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    """``(width, height)`` from a PNG header, or ``None`` if not a PNG.

    Pure byte-peeking (IHDR is always the first chunk) — no imaging dependency,
    so the pipeline can judge crops without PIL.
    """
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    return None


def crop_drop_reason(data: bytes) -> str | None:
    """Why a dewarped crop must not reach the recogniser (``None`` = fine).

    Only PNG crops are judged (the pipeline's cropper emits PNG); anything else
    passes through to the engine's own transformed-width cap.
    """
    dims = png_dimensions(data)
    if dims is None:
        return None
    w, h = dims
    if min(w, h) < MIN_CROP_SIDE_PX or max(w, h) > MAX_CROP_ASPECT * min(w, h):
        return f"sliver_crop:{w}x{h}"
    return None


__all__ = [
    "MAX_CROP_AREA_FLOOR",
    "MAX_CROP_ASPECT",
    "MIN_BASELINE_PX",
    "MIN_CROP_SIDE_PX",
    "PAGE_AREA_FACTOR",
    "Point",
    "crop_drop_reason",
    "dedupe_points",
    "drop_reason",
    "estimate_crop_size",
    "max_crop_area",
    "png_dimensions",
    "polyline_length",
]
