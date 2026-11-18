"""Zones and lines as PHILIUMM's layout pipeline writes them, and the pixel
geometry the zone census needs (P1 Task 3).

The pipeline (``main_pipeline.py`` of their GitLab repository) writes, for a
page image ``<stem>.jpg``:

* ``01_predictions_json/rf-detr/<stem>.json`` — RF-DETR-Seg's detections:
  ``class``, ``confidence`` and ``points`` (the mask's largest polygon, or the
  box when the mask gave none);
* ``03_regions_xml/<stem>_regions.xml`` — the same zones as PAGE XML
  ``TextRegion`` elements with ``custom="structure {type:<class>;}"`` and a
  ``Coords`` polygon, no lines;
* ``10_fixed_lines/<stem>*.xml`` — the final PAGE XML: the kraken baselines
  merged into the zones, polygons simplified, margin zones cut out of main
  zones, lines clipped to their region and split where they crossed two.

Geometry is pixel geometry. A polygon's area is the shoelace formula; what
two polygons share is counted by rasterizing both on a bounding box (Pillow
draws, ``histogram`` counts), exact to the pixel and free of any geometry
library. Pillow is the ``gt`` extra's dependency and is imported lazily, so
reading the files needs lxml only.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from leibniz.align.pagexml import parse_points, region_type

Point = tuple[int, int]
Box = tuple[int, int, int, int]  # x0, y0, x1, y1 (exclusive)

# The eight classes the v2 model was trained on (its card, read 2026-11-16),
# grouped for the census. The v1 names are kept so a v1 run reads too.
GROUPS: dict[str, str] = {
    "MainZone": "main",
    "MarginTextZone": "margin",
    "NumberingZone": "numbering",
    "DigitizationArtefactZone": "artefact",
    "GraphicZone-figure": "figure",
    "MathsRegion-complex": "formula",
    "MathsRegion-inline": "formula",
    "MathsRegion-standard": "formula",  # the dataset's COCO name for the inline class
    "MathsRegion-strikethrough": "formula",
    "GraphicZone-formula": "formula",
    "GraphicZone-formula-inline": "formula",
    "GraphicZone-formula-strikethrough": "formula",
    "GraphicZone-formula-complex": "formula",
}
GROUP_ORDER = ("main", "margin", "numbering", "figure", "formula", "artefact", "other")
INSIDE_SHARE = 0.5  # a line "lies mostly inside" a zone group at this share of its pixels


def zone_group(cls: str | None) -> str:
    """The census group of a class name: ``main``, ``margin``, ``numbering``,
    ``figure``, ``formula``, ``artefact`` or ``other``."""
    if cls is None:
        return "other"
    if cls in GROUPS:
        return GROUPS[cls]
    low = cls.lower()
    if "math" in low or "formula" in low:
        return "formula"
    if "graphic" in low or "figure" in low:
        return "figure"
    return "other"


@dataclass(slots=True)
class Zone:
    """One detected zone: its class as the model named it, its polygon, and
    the detection confidence where the source carries one."""

    id: str
    cls: str | None
    polygon: list[Point] = field(default_factory=list)
    conf: float | None = None

    @property
    def group(self) -> str:
        return zone_group(self.cls)


@dataclass(slots=True)
class ZoneLine:
    """One ``TextLine`` of the final PAGE XML, with the region it sits in."""

    id: str
    region_id: str
    region_type: str | None
    polygon: list[Point] = field(default_factory=list)
    baseline: list[Point] = field(default_factory=list)

    @property
    def group(self) -> str:
        return zone_group(self.region_type)


@dataclass(slots=True)
class LayoutPage:
    """A PAGE XML file of the pipeline: its zones (regions) and lines."""

    image: str | None
    width: int | None
    height: int | None
    zones: list[Zone]
    lines: list[ZoneLine]


# --------------------------------------------------------------------------- #
# Reading the pipeline's files
# --------------------------------------------------------------------------- #


def _local(el: etree._Element) -> str:
    return etree.QName(el).localname


def _child(el: etree._Element, name: str) -> etree._Element | None:
    for c in el:
        if isinstance(c.tag, str) and _local(c) == name:
            return c
    return None


def read_page_xml(source: Path | str | bytes) -> LayoutPage:
    """Read a PAGE XML file of the pipeline (any PAGE namespace): the regions
    with their polygons and types, the lines with their region."""
    if isinstance(source, bytes):
        root = etree.fromstring(source)
    elif isinstance(source, str) and source.lstrip().startswith("<"):
        root = etree.fromstring(source.encode("utf-8"))
    else:
        root = etree.parse(str(source)).getroot()
    page = next(
        (el for el in root.iter() if isinstance(el.tag, str) and _local(el) == "Page"), None
    )
    image = page.get("imageFilename") if page is not None else None
    width = _int(page.get("imageWidth")) if page is not None else None
    height = _int(page.get("imageHeight")) if page is not None else None
    zones: list[Zone] = []
    lines: list[ZoneLine] = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        name = _local(el)
        if name == "TextRegion":
            coords = _child(el, "Coords")
            zones.append(
                Zone(
                    el.get("id") or f"r{len(zones)}",
                    region_type(el.get("custom")),
                    parse_points(coords.get("points") if coords is not None else None),
                )
            )
        elif name == "TextLine":
            region = el.getparent()
            while region is not None and not (
                isinstance(region.tag, str) and _local(region) == "TextRegion"
            ):
                region = region.getparent()
            coords = _child(el, "Coords")
            baseline = _child(el, "Baseline")
            lines.append(
                ZoneLine(
                    el.get("id") or f"l{len(lines)}",
                    (region.get("id") if region is not None else None) or "",
                    region_type(region.get("custom")) if region is not None else None,
                    parse_points(coords.get("points") if coords is not None else None),
                    parse_points(baseline.get("points") if baseline is not None else None),
                )
            )
    return LayoutPage(image, width, height, zones, lines)


def read_predictions_json(
    source: Path | str | bytes | dict,
) -> tuple[int | None, int | None, list[Zone]]:
    """The detections of ``01_predictions_json/rf-detr/<stem>.json``: the image
    size and one :class:`Zone` per prediction, with its confidence."""
    if isinstance(source, dict):
        data = source
    elif isinstance(source, bytes):
        data = json.loads(source.decode("utf-8"))
    elif isinstance(source, str) and source.lstrip().startswith("{"):
        data = json.loads(source)
    else:
        data = json.loads(Path(source).read_text(encoding="utf-8"))
    image = data.get("image") or {}
    zones: list[Zone] = []
    for i, pred in enumerate(data.get("predictions") or []):
        pts = [(int(p["x"]), int(p["y"])) for p in (pred.get("points") or []) if "x" in p]
        if not pts and all(k in pred for k in ("x", "y", "width", "height")):
            x0, y0 = pred["x"] - pred["width"] / 2, pred["y"] - pred["height"] / 2
            x1, y1 = pred["x"] + pred["width"] / 2, pred["y"] + pred["height"] / 2
            pts = [(int(x0), int(y0)), (int(x1), int(y0)), (int(x1), int(y1)), (int(x0), int(y1))]
        conf = pred.get("confidence")
        zones.append(
            Zone(
                f"p{i}",
                (pred.get("class") or "").strip() or None,
                pts,
                float(conf) if conf is not None else None,
            )
        )
    return _int(image.get("width")), _int(image.get("height")), zones


def _int(v) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


_STEM_SUFFIXES = ("_regions", "_baselines", "_mask", "_merged", "_simplified", "_fixed")


def stem_of(path: Path | str) -> str:
    """The page stem of a pipeline output file: ``<stem>_regions.xml`` →
    ``<stem>``; a bare ``<stem>.xml`` stays."""
    stem = Path(path).stem
    for suf in _STEM_SUFFIXES:
        if stem.endswith(suf):
            return stem[: -len(suf)]
    return stem


def find_output(results_dir: Path, step: str, stem: str, suffix: str = ".xml") -> Path | None:
    """The one output file of ``step`` for ``stem`` (``<stem>.xml`` or
    ``<stem>_<anything>.xml``), or ``None``."""
    folder = Path(results_dir) / step
    if not folder.is_dir():
        return None
    exact = folder / f"{stem}{suffix}"
    if exact.exists():
        return exact
    hits = sorted(p for p in folder.glob(f"{re.escape(stem)}_*{suffix}") if stem_of(p) == stem)
    hits = hits or sorted(p for p in folder.glob(f"{stem}*{suffix}") if stem_of(p) == stem)
    return hits[0] if hits else None


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #


def polygon_area(pts: Sequence[Sequence[float]]) -> float:
    """The shoelace area of a polygon given as a point sequence (0 for < 3)."""
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x0, y0 = pts[i][0], pts[i][1]
        x1, y1 = pts[(i + 1) % n][0], pts[(i + 1) % n][1]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def bbox(pts: Sequence[Sequence[float]]) -> Box | None:
    """Integer bounding box ``(x0, y0, x1, y1)``, ``x1``/``y1`` exclusive."""
    if not pts:
        return None
    xs = [int(p[0]) for p in pts]
    ys = [int(p[1]) for p in pts]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def box_iou(a: Box, b: Box) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    area = lambda r: max(0, r[2] - r[0]) * max(0, r[3] - r[1])  # noqa: E731
    union = area(a) + area(b) - inter
    return inter / union if union > 0 else 0.0


def scale_points(pts: Iterable[Sequence[float]], sx: float, sy: float) -> list[Point]:
    return [(int(round(p[0] * sx)), int(round(p[1] * sy))) for p in pts]


def _draw(size: tuple[int, int], polygons: Iterable[Sequence[Point]], offset: tuple[int, int]):
    """A mode-``L`` mask of ``size`` with the polygons (shifted by ``-offset``)
    filled 255. Pillow is imported here, lazily."""
    from PIL import Image, ImageDraw

    img = Image.new("L", size, 0)
    draw = ImageDraw.Draw(img)
    ox, oy = offset
    for poly in polygons:
        pts = [(x - ox, y - oy) for x, y in poly]
        if len(pts) >= 3:
            draw.polygon(pts, fill=255)
        elif len(pts) == 2:
            draw.line(pts, fill=255, width=1)
    return img


def _count(img) -> int:
    return img.histogram()[255]


def overlap_pixels(a: Sequence[Point], b: Sequence[Point]) -> tuple[int, int, int]:
    """``(shared, area_a, area_b)`` in pixels, both polygons rasterized on
    their union box."""
    from PIL import ImageChops

    ba, bb = bbox(a), bbox(b)
    if ba is None or bb is None:
        return 0, _count(_draw_one(a)) if ba else 0, _count(_draw_one(b)) if bb else 0
    x0, y0 = min(ba[0], bb[0]), min(ba[1], bb[1])
    x1, y1 = max(ba[2], bb[2]), max(ba[3], bb[3])
    size = (max(1, x1 - x0), max(1, y1 - y0))
    ma = _draw(size, [a], (x0, y0))
    mb = _draw(size, [b], (x0, y0))
    return _count(ImageChops.darker(ma, mb)), _count(ma), _count(mb)


def _draw_one(poly: Sequence[Point]):
    b = bbox(poly)
    assert b is not None
    return _draw((max(1, b[2] - b[0]), max(1, b[3] - b[1])), [poly], (b[0], b[1]))


def polygon_iou(a: Sequence[Point], b: Sequence[Point]) -> float:
    """Intersection over union of two pixel polygons (0 when either is empty
    or their boxes are apart)."""
    ba, bb = bbox(a), bbox(b)
    if ba is None or bb is None or box_iou(ba, bb) == 0.0:
        return 0.0
    inter, area_a, area_b = overlap_pixels(a, b)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


class GroupMasks:
    """The zones of one page rasterized once per group (``group_of`` names a
    zone's group from its class; the census grouping by default), so that
    any line's share inside a group is one small crop and count."""

    def __init__(
        self,
        width: int,
        height: int,
        zones: Iterable[Zone],
        *,
        max_side: int = 4096,
        group_of: Callable[[str | None], str] = zone_group,
    ):
        self.width, self.height = max(1, int(width)), max(1, int(height))
        self.scale = min(1.0, max_side / max(self.width, self.height))
        self.size = (
            max(1, int(round(self.width * self.scale))),
            max(1, int(round(self.height * self.scale))),
        )
        by_group: dict[str, list[list[Point]]] = {}
        for z in zones:
            if len(z.polygon) >= 3:
                by_group.setdefault(group_of(z.cls), []).append(
                    scale_points(z.polygon, self.scale, self.scale)
                )
        self.masks = {g: _draw(self.size, polys, (0, 0)) for g, polys in by_group.items()}
        self.pixels = {g: _count(m) for g, m in self.masks.items()}

    def area_share(self, group: str) -> float:
        """The share of the page's pixels the group's zones cover (their union)."""
        return self.pixels.get(group, 0) / (self.size[0] * self.size[1])

    def shares(self, polygon: Sequence[Point]) -> dict[str, float]:
        """For one line polygon (page pixels): the share of its pixels inside
        each group's zones."""
        from PIL import ImageChops

        pts = (
            scale_points(polygon, self.scale, self.scale)
            if self.scale != 1.0
            else [(int(x), int(y)) for x, y in polygon]
        )
        b = bbox(pts)
        if b is None or not self.masks:
            return {}
        x0, y0 = max(0, b[0]), max(0, b[1])
        x1, y1 = min(self.size[0], b[2]), min(self.size[1], b[3])
        if x1 <= x0 or y1 <= y0:
            return {}
        line = _draw((x1 - x0, y1 - y0), [pts], (x0, y0))
        n = _count(line)
        if n == 0:
            return {}
        out: dict[str, float] = {}
        for g, m in self.masks.items():
            crop = m.crop((x0, y0, x1, y1))
            out[g] = _count(ImageChops.darker(line, crop)) / n
        return out


def home_group(shares: dict[str, float], *, threshold: float = INSIDE_SHARE) -> str:
    """The group a line lies mostly in (the largest share at or above the
    threshold), else ``outside``."""
    if not shares:
        return "outside"
    g, s = max(shares.items(), key=lambda kv: kv[1])
    return g if s >= threshold else "outside"


def pair_by_iou(
    ours: Sequence[Sequence[Point]], theirs: Sequence[Sequence[Point]], *, threshold: float = 0.5
) -> list[tuple[int, int, float]]:
    """Greedy one-to-one pairs ``(i, j, iou)`` between two polygon lists, best
    IoU first, at or above ``threshold``; boxes that do not meet are skipped
    before any rasterizing."""
    boxes_a = [bbox(p) for p in ours]
    boxes_b = [bbox(p) for p in theirs]
    cands: list[tuple[float, int, int]] = []
    for i, ba in enumerate(boxes_a):
        if ba is None:
            continue
        for j, bb in enumerate(boxes_b):
            if bb is None or box_iou(ba, bb) <= 0.0:
                continue
            v = polygon_iou(ours[i], theirs[j])
            if v >= threshold:
                cands.append((v, i, j))
    cands.sort(reverse=True)
    used_a: set[int] = set()
    used_b: set[int] = set()
    out: list[tuple[int, int, float]] = []
    for v, i, j in cands:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        out.append((i, j, v))
    return out


__all__ = [
    "GROUP_ORDER",
    "GROUPS",
    "INSIDE_SHARE",
    "GroupMasks",
    "LayoutPage",
    "Zone",
    "ZoneLine",
    "bbox",
    "box_iou",
    "find_output",
    "home_group",
    "overlap_pixels",
    "pair_by_iou",
    "polygon_area",
    "polygon_iou",
    "read_page_xml",
    "read_predictions_json",
    "scale_points",
    "stem_of",
    "zone_group",
]
