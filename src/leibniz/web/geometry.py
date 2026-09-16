"""Line geometry helpers for the viewer and the annotations (pure)."""

from __future__ import annotations

from leibniz import db


def line_bbox(line: db.Line, page: db.Page | None = None) -> dict | None:
    """``{x, y, w, h}`` in full-image pixels from the polygon, else the baseline.

    A baseline-only line (no polygon) gets a band of ±2% of the page height
    around the baseline so it can still be targeted; ``None`` if no geometry.
    """
    pts = _points(line.polygon)
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        return {"x": int(x0), "y": int(y0), "w": max(1, int(x1 - x0)), "h": max(1, int(y1 - y0))}
    base = _points(line.baseline)
    if base:
        xs = [p[0] for p in base]
        ys = [p[1] for p in base]
        pad = max(8, int(0.02 * (page.height or 0))) if page and page.height else 20
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys) - pad, max(ys) + pad // 2
        return {
            "x": int(x0),
            "y": int(max(0, y0)),
            "w": max(1, int(x1 - x0)),
            "h": max(1, int(y1 - y0)),
        }
    return None


def _points(raw: object) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    if not isinstance(raw, list):
        return out
    for p in raw:
        if isinstance(p, list | tuple) and len(p) >= 2:
            try:
                out.append((float(p[0]), float(p[1])))
            except (TypeError, ValueError):
                continue
    return out


def polygon_points(line: db.Line) -> list[list[int]]:
    """Polygon as ``[[x, y], …]`` ints (empty if none)."""
    return [[int(x), int(y)] for x, y in _points(line.polygon)]


def baseline_points(line: db.Line) -> list[list[int]]:
    return [[int(x), int(y)] for x, y in _points(line.baseline)]


__all__ = ["baseline_points", "line_bbox", "polygon_points"]
