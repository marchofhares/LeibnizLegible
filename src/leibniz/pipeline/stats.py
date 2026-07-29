"""Per-page segmentation statistics (Phase C1).

Segmentation quality is the known unsolved half of the corpus (layered revisions,
marginalia, snippets — SPECS §9). We can't fix it blindly, so C1 *measures* it:
for every segmented page it computes a small bag of layout statistics from the
line geometry and stores it in ``page_stats``. Those numbers do two jobs — they
surface the worst segmentation failures for inspection (a page with 200 tiny
overlapping "lines" is a layered draft the segmenter shredded), and they are the
raw signal the stratum heuristic reads in C2 (per piece) and C4 (per page): a
clean fair copy has a dozen evenly-spaced full-width lines; a heavy-revision draft
has irregular heights, short interlinear insertions, and overlapping boxes.

Everything here is pure geometry over :class:`~leibniz.layout.segment.SegmentedPage`
— no kraken, no images — so it is fully offline-testable. The metrics are
deliberately simple and honestly named; they are heuristic layout signal, not a
diplomatic judgement.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from leibniz.layout.segment import SegLine, SegmentedPage

# A line is "short" (interlinear insertion / snippet signal) if its width is below
# this fraction of the page's median line width.
SHORT_LINE_FRACTION = 0.4
# Two line boxes "overlap" (layered-revision / marginalia signal) when their
# intersection is at least this fraction of the smaller box's area.
OVERLAP_FRACTION = 0.30


@dataclass(slots=True)
class SegStats:
    """Layout statistics for one segmented page (mirrors ``db.PageStats``)."""

    n_lines: int
    n_regions: int
    region_coverage: float  # Σ line-polygon area ÷ page area, capped at 1.0
    mean_line_height: float
    median_line_height: float
    line_height_cv: float  # stdev ÷ mean of line heights (irregularity signal)
    n_overlaps: int
    n_short_lines: int
    page_width: int
    page_height: int
    extra: dict = field(default_factory=dict)

    def as_metrics(self) -> dict:
        """The full metric bag, for the ``page_stats.metrics`` JSON column."""
        return {
            "n_lines": self.n_lines,
            "n_regions": self.n_regions,
            "region_coverage": round(self.region_coverage, 4),
            "mean_line_height": round(self.mean_line_height, 2),
            "median_line_height": round(self.median_line_height, 2),
            "line_height_cv": round(self.line_height_cv, 4),
            "n_overlaps": self.n_overlaps,
            "n_short_lines": self.n_short_lines,
            "page_width": self.page_width,
            "page_height": self.page_height,
            **self.extra,
        }


def _bbox(line: SegLine) -> tuple[float, float, float, float] | None:
    pts = line.boundary or line.baseline
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def polygon_area(pts: list[tuple[float, float]]) -> float:
    """Absolute area of a (possibly open) polygon via the shoelace formula."""
    if len(pts) < 3:
        return 0.0
    s = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def _bbox_area(b: tuple[float, float, float, float]) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _intersection_area(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> float:
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)


def compute_seg_stats(page: SegmentedPage, *, n_regions: int = 0) -> SegStats:
    """Compute layout statistics for a segmented page (pure geometry).

    ``region_coverage`` is the summed line-polygon area over the page area,
    **capped at 1.0** — an approximation (overlapping polygons are double-counted,
    which is why it is capped rather than a true union), useful as a "how much of
    the page is text" signal. Heights come from line bounding boxes; ``line_height_cv``
    (stdev÷mean) flags the irregular line spacing typical of revised drafts.
    """
    page_area = float(page.width * page.height) if page.width and page.height else 0.0
    boxes = [b for b in (_bbox(ln) for ln in page.lines) if b is not None]
    n_lines = len(page.lines)

    if not boxes:
        return SegStats(
            n_lines=n_lines,
            n_regions=n_regions,
            region_coverage=0.0,
            mean_line_height=0.0,
            median_line_height=0.0,
            line_height_cv=0.0,
            n_overlaps=0,
            n_short_lines=0,
            page_width=page.width,
            page_height=page.height,
            extra={"n_lines_without_geometry": n_lines},
        )

    heights = [b[3] - b[1] for b in boxes]
    widths = [b[2] - b[0] for b in boxes]
    mean_h = statistics.fmean(heights)
    median_h = statistics.median(heights)
    cv = (statistics.pstdev(heights) / mean_h) if mean_h > 0 else 0.0

    # Coverage: prefer true polygon areas; fall back to bbox areas for
    # baseline-only lines. Cap the summed fraction at 1.0 (see docstring).
    covered = 0.0
    for ln, box in zip(
        (line for line in page.lines if _bbox(line) is not None), boxes, strict=True
    ):
        area = polygon_area(ln.boundary) if len(ln.boundary) >= 3 else _bbox_area(box)
        covered += area
    coverage = min(1.0, covered / page_area) if page_area > 0 else 0.0

    median_w = statistics.median(widths)
    short_thresh = SHORT_LINE_FRACTION * median_w if median_w > 0 else 0.0
    n_short = sum(1 for w in widths if w < short_thresh)

    n_overlaps = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            inter = _intersection_area(boxes[i], boxes[j])
            if inter <= 0:
                continue
            smaller = min(_bbox_area(boxes[i]), _bbox_area(boxes[j]))
            if smaller > 0 and inter / smaller >= OVERLAP_FRACTION:
                n_overlaps += 1

    return SegStats(
        n_lines=n_lines,
        n_regions=n_regions,
        region_coverage=coverage,
        mean_line_height=mean_h,
        median_line_height=median_h,
        line_height_cv=cv,
        n_overlaps=n_overlaps,
        n_short_lines=n_short,
        page_width=page.width,
        page_height=page.height,
        extra={"mean_line_width": round(statistics.fmean(widths), 2)},
    )


__all__ = [
    "OVERLAP_FRACTION",
    "SHORT_LINE_FRACTION",
    "SegStats",
    "compute_seg_stats",
    "polygon_area",
]
