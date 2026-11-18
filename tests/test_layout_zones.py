"""The pipeline's files and the pixel geometry of the zone census (offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

from leibniz.layout import zones as Z

FIX = Path(__file__).parent / "fixtures" / "layout"


def test_zone_groups() -> None:
    assert Z.zone_group("MainZone") == "main"
    assert Z.zone_group("MarginTextZone") == "margin"
    assert Z.zone_group("MathsRegion-strikethrough") == "formula"
    assert Z.zone_group("MathsRegion-standard") == "formula"  # the dataset's COCO name
    assert Z.zone_group("GraphicZone-formula-inline") == "formula"  # the v1 name
    assert Z.zone_group("GraphicZone-figure") == "figure"
    assert Z.zone_group("DigitizationArtefactZone") == "artefact"
    assert Z.zone_group("SomethingNew") == "other" and Z.zone_group(None) == "other"


def test_read_regions_xml() -> None:
    page = Z.read_page_xml(FIX / "page_a_regions.xml")
    assert (page.image, page.width, page.height) == ("page_a.jpg", 1000, 1400)
    assert [z.cls for z in page.zones] == [
        "MainZone",
        "MarginTextZone",
        "GraphicZone-figure",
        "MathsRegion-inline",
    ]
    assert page.zones[0].polygon == [(100, 100), (900, 100), (900, 900), (100, 900)]
    assert page.zones[3].group == "formula" and page.lines == []


def test_read_fixed_lines() -> None:
    page = Z.read_page_xml(FIX / "page_a_fixed.xml")
    assert len(page.zones) == 2 and len(page.lines) == 3
    assert [ln.region_type for ln in page.lines] == ["MainZone", "MainZone", "MarginTextZone"]
    assert page.lines[2].group == "margin"
    assert page.lines[0].baseline == [(120, 150), (880, 150)]
    assert page.lines[0].polygon[0] == (120, 120)


def test_read_predictions_json_with_confidence_and_box_fallback() -> None:
    w, h, zones = Z.read_predictions_json(FIX / "page_a.json")
    assert (w, h) == (1000, 1400) and len(zones) == 4
    assert zones[0].cls == "MainZone" and zones[0].conf == 0.95
    # a prediction without points falls back to its box
    assert zones[3].cls == "MathsRegion-inline"
    assert zones[3].polygon == [(600, 1000), (900, 1000), (900, 1100), (600, 1100)]


def test_stem_and_find_output(tmp_path: Path) -> None:
    assert Z.stem_of("x/00068371_0219_regions.xml") == "00068371_0219"
    assert Z.stem_of("00068371_0219_baselines.xml") == "00068371_0219"
    assert Z.stem_of("00068371_0219.xml") == "00068371_0219"
    (tmp_path / "10_fixed_lines").mkdir()
    (tmp_path / "10_fixed_lines" / "00068371_0219.xml").write_text("<a/>")
    (tmp_path / "03_regions_xml").mkdir()
    (tmp_path / "03_regions_xml" / "00068371_0219_regions.xml").write_text("<a/>")
    assert Z.find_output(tmp_path, "10_fixed_lines", "00068371_0219").name == "00068371_0219.xml"
    assert Z.find_output(tmp_path, "03_regions_xml", "00068371_0219").name.endswith("_regions.xml")
    assert Z.find_output(tmp_path, "03_regions_xml", "00068371_0220") is None
    assert Z.find_output(tmp_path, "07_merged_xml", "00068371_0219") is None


def test_polygon_area_and_boxes() -> None:
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert Z.polygon_area(square) == 100.0
    assert Z.polygon_area([(0, 0), (1, 1)]) == 0.0
    assert Z.bbox(square) == (0, 0, 11, 11)
    assert Z.bbox([]) is None
    assert Z.box_iou((0, 0, 10, 10), (5, 0, 15, 10)) == pytest.approx(1 / 3)
    assert Z.box_iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0
    assert Z.scale_points([(10, 20)], 0.5, 0.5) == [(5, 10)]


def test_pixel_overlap_and_iou() -> None:
    pytest.importorskip("PIL")
    a = [(0, 0), (100, 0), (100, 100), (0, 100)]
    b = [(50, 0), (150, 0), (150, 100), (50, 100)]
    inter, area_a, area_b = Z.overlap_pixels(a, b)
    assert area_a == area_b == 101 * 101  # Pillow fills the boundary pixels too
    assert inter == 51 * 101
    assert Z.polygon_iou(a, b) == pytest.approx(51 / 151, abs=0.01)
    assert Z.polygon_iou(a, [(500, 500), (600, 500), (600, 600)]) == 0.0
    assert Z.polygon_iou(a, a) == 1.0


def test_group_masks_and_home_group() -> None:
    pytest.importorskip("PIL")
    page = Z.read_page_xml(FIX / "page_a_regions.xml")
    masks = Z.GroupMasks(page.width, page.height, page.zones)
    assert set(masks.masks) == {"main", "margin", "figure", "formula"}
    assert masks.area_share("main") == pytest.approx(801 * 801 / (1000 * 1400), abs=0.002)
    line_in_main = [(120, 120), (880, 120), (880, 160), (120, 160)]
    shares = masks.shares(line_in_main)
    assert shares["main"] == 1.0 and shares.get("figure", 0.0) == 0.0
    assert Z.home_group(shares) == "main"
    line_in_figure = [(150, 1100), (450, 1100), (450, 1150), (150, 1150)]
    assert Z.home_group(masks.shares(line_in_figure)) == "figure"
    straddling = [(850, 150), (950, 150), (950, 180), (850, 180)]  # half in main, half out
    s = masks.shares(straddling)
    assert 0.4 < s["main"] < 0.6 and Z.home_group(s) == "main"  # 0.5 counts as inside
    outside = [(950, 1200), (990, 1200), (990, 1300), (950, 1300)]
    assert Z.home_group(masks.shares(outside)) == "outside"
    assert Z.home_group({}) == "outside"


def test_group_masks_downscale_large_page() -> None:
    pytest.importorskip("PIL")
    zones = [Z.Zone("r0", "MainZone", [(0, 0), (8000, 0), (8000, 8000), (0, 8000)])]
    masks = Z.GroupMasks(8000, 8000, zones, max_side=4096)
    assert masks.scale == pytest.approx(0.512) and masks.size == (4096, 4096)
    assert masks.area_share("main") == 1.0
    assert Z.home_group(masks.shares([(100, 100), (700, 100), (700, 200), (100, 200)])) == "main"


def test_pair_by_iou_is_greedy_and_one_to_one() -> None:
    pytest.importorskip("PIL")
    ours = [
        [(0, 0), (100, 0), (100, 20), (0, 20)],
        [(0, 50), (100, 50), (100, 70), (0, 70)],
        [(0, 500), (100, 500), (100, 520), (0, 520)],
    ]
    theirs = [
        [(0, 52), (100, 52), (100, 72), (0, 72)],  # ≈ ours[1]
        [(0, 0), (100, 0), (100, 20), (0, 20)],  # == ours[0]
        [(0, 2), (100, 2), (100, 22), (0, 22)],  # a second claim on ours[0]
    ]
    pairs = Z.pair_by_iou(ours, theirs, threshold=0.5)
    assert sorted((i, j) for i, j, _ in pairs) == [(0, 1), (1, 0)]
    assert all(v >= 0.5 for _, _, v in pairs)
    assert Z.pair_by_iou(ours, theirs, threshold=0.99) == [(0, 1, 1.0)]
    assert Z.pair_by_iou([], theirs) == []
