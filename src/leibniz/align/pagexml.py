"""PAGE XML reading: the text lines of a page in reading order (P1).

PHILIUMM's HTR output and their aligned ground truth are PAGE XML files
(eScriptorium's export): ``TextRegion`` elements carrying a SegmOnto type in
``custom="structure {type:MainZone;}"``, each with ``TextLine`` elements that
hold ``Coords`` (a polygon), a ``Baseline`` and a ``TextEquiv/Unicode`` text
that may be empty or absent. Reading order here is **document order**: region
after region, line after line inside each — the order their own scripts use
(``root.findall('.//TextLine')``), so a line index means the same thing on
both sides of a comparison.

Pure: a path, bytes or a string in, dataclasses out; ``lxml`` is a core
dependency. Any PAGE namespace version is accepted (the local names are what
is matched).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

_TYPE_RE = re.compile(r"type\s*:\s*([A-Za-z0-9_-]+)")


@dataclass(slots=True)
class PageLine:
    """One ``TextLine``: its id, geometry, text and the region it sits in."""

    id: str
    index: int  # 0-based position in document order
    region_id: str
    region_type: str | None  # SegmOnto type from the region's ``custom`` attribute
    text: str  # "" when the line has no ``Unicode`` or it is empty
    coords: list[tuple[int, int]] = field(default_factory=list)
    baseline: list[tuple[int, int]] = field(default_factory=list)
    conf: float | None = None  # ``TextEquiv/@conf`` when present
    attributes: dict[str, str] = field(default_factory=dict)  # other TextEquiv attributes


@dataclass(slots=True)
class PageDocument:
    image_filename: str | None
    width: int | None
    height: int | None
    lines: list[PageLine]
    regions: list[tuple[str, str | None]]  # (id, type) in document order

    def lines_of(self, region_id: str) -> list[PageLine]:
        return [ln for ln in self.lines if ln.region_id == region_id]

    def texts(self) -> list[str]:
        return [ln.text for ln in self.lines]


def region_type(custom: str | None) -> str | None:
    """``"structure {type:MainZone;}"`` → ``"MainZone"`` (``None`` when absent)."""
    m = _TYPE_RE.search(custom or "")
    return m.group(1) if m else None


def parse_points(points: str | None) -> list[tuple[int, int]]:
    """``"10,20 30,40"`` → ``[(10, 20), (30, 40)]``; malformed pairs are skipped."""
    out: list[tuple[int, int]] = []
    for tok in (points or "").split():
        x, _, y = tok.partition(",")
        try:
            out.append((int(float(x)), int(float(y))))
        except ValueError:
            continue
    return out


def _local(el: etree._Element) -> str:
    return etree.QName(el).localname


def _child(el: etree._Element, name: str) -> etree._Element | None:
    for c in el:
        if isinstance(c.tag, str) and _local(c) == name:
            return c
    return None


def parse_page_xml(source: Path | str | bytes) -> PageDocument:
    """Read a PAGE XML file (a path, a string of XML, or bytes)."""
    if isinstance(source, bytes):
        root = etree.fromstring(source)
    elif isinstance(source, Path) or (
        isinstance(source, str) and not source.lstrip().startswith("<")
    ):
        root = etree.parse(str(source)).getroot()
    else:
        root = etree.fromstring(source.encode("utf-8"))
    page = next(
        (el for el in root.iter() if isinstance(el.tag, str) and _local(el) == "Page"), None
    )
    image = page.get("imageFilename") if page is not None else None
    width = _int(page.get("imageWidth")) if page is not None else None
    height = _int(page.get("imageHeight")) if page is not None else None

    regions: list[tuple[str, str | None]] = []
    lines: list[PageLine] = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        name = _local(el)
        if name == "TextRegion":
            regions.append((el.get("id") or f"r{len(regions)}", region_type(el.get("custom"))))
        elif name == "TextLine":
            region = _nearest_region(el)
            rid = (region.get("id") if region is not None else None) or ""
            rtype = region_type(region.get("custom")) if region is not None else None
            coords = _child(el, "Coords")
            baseline = _child(el, "Baseline")
            equiv = _child(el, "TextEquiv")
            text = ""
            conf = None
            attrs: dict[str, str] = {}
            if equiv is not None:
                uni = _child(equiv, "Unicode")
                text = (uni.text or "") if uni is not None else ""
                conf = _float(equiv.get("conf"))
                attrs = {k: v for k, v in equiv.attrib.items() if k != "conf"}
            lines.append(
                PageLine(
                    id=el.get("id") or f"l{len(lines)}",
                    index=len(lines),
                    region_id=rid,
                    region_type=rtype,
                    text=text,
                    coords=parse_points(coords.get("points") if coords is not None else None),
                    baseline=parse_points(baseline.get("points") if baseline is not None else None),
                    conf=conf,
                    attributes=attrs,
                )
            )
    return PageDocument(image, width, height, lines, regions)


def _nearest_region(el: etree._Element) -> etree._Element | None:
    parent = el.getparent()
    while parent is not None:
        if isinstance(parent.tag, str) and _local(parent) == "TextRegion":
            return parent
        parent = parent.getparent()
    return None


def _int(v: str | None) -> int | None:
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None


def _float(v: str | None) -> float | None:
    try:
        return float(v) if v is not None else None
    except ValueError:
        return None


__all__ = ["PageDocument", "PageLine", "parse_page_xml", "parse_points", "region_type"]
