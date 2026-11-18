"""The zone census (offline): one page on the fixtures, the aggregation, the report."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.conftest import W1

from leibniz import db
from leibniz.layout import census as C
from leibniz.layout.sample import SamplePage

FIX = Path(__file__).parent / "fixtures" / "layout"


def _results(tmp_path: Path, stem: str) -> Path:
    results = tmp_path / "results"
    (results / "01_predictions_json" / "rf-detr").mkdir(parents=True)
    (results / "03_regions_xml").mkdir()
    (results / "10_fixed_lines").mkdir()
    shutil.copy(FIX / "page_a.json", results / "01_predictions_json" / "rf-detr" / f"{stem}.json")
    shutil.copy(FIX / "page_a_regions.xml", results / "03_regions_xml" / f"{stem}_regions.xml")
    shutil.copy(FIX / "page_a_fixed.xml", results / "10_fixed_lines" / f"{stem}.xml")
    return results


def test_census_page_on_fixture(store_path: Path, tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    conn = db.connect(store_path)
    pid = f"{W1}:0001"
    # the store says 2000×2500, the pipeline saw a 1000×1400 copy: its zones and
    # lines are scaled back (×2 in x, ×1.7857 in y) to the scan's pixels
    sx, sy = 2.0, 2500 / 1400
    conn.execute("DELETE FROM lines WHERE page_id = ?", (pid,))
    run = db.start_run(conn, "segment", model="t")
    polys = [
        [[120, 120], [880, 120], [880, 160], [120, 160]],  # in the main zone (= their l0)
        [[150, 1100], [450, 1100], [450, 1150], [150, 1150]],  # in the figure
        [[650, 1020], [850, 1020], [850, 1080], [650, 1080]],  # in the formula box
        [[950, 1200], [990, 1200], [990, 1300], [950, 1300]],  # outside every zone
    ]
    for i, poly in enumerate(polys):
        scaled = [[round(x * sx), round(y * sy)] for x, y in poly]
        db.insert_line(
            conn, db.Line(pid, i, polygon=scaled, text="x", conf=0.9, model="m", run_id=run)
        )
    conn.commit()
    stem = f"{W1}_0001"
    results = _results(tmp_path, stem)
    sp = SamplePage(
        pid,
        "handschriften",
        "",
        W1,
        "LeibnizHandschriften",
        "LH IV, 6, 18",
        "1r",
        2000,
        2500,
        4,
        "x",
        f"{stem}.jpg",
    )
    pc = C.census_page(conn, sp, results)
    assert pc.status == "ok" and (pc.image_width, pc.image_height) == (1000, 1400)
    assert pc.size_agrees is False and pc.scale == 2.0
    assert pc.zones == {
        "MainZone": 1,
        "MarginTextZone": 1,
        "GraphicZone-figure": 1,
        "MathsRegion-inline": 1,
    }
    assert pc.zone_conf["MainZone"] == 0.95
    assert pc.has("figure") and pc.has("formula") and pc.has("margin") and not pc.has("artefact")
    assert pc.v1_lines == 4
    assert pc.v1_by_group == {"main": 1, "figure": 1, "formula": 1, "outside": 1}
    assert pc.their_lines == 3 and pc.their_by_group == {"main": 2, "margin": 1}
    assert pc.matched == {"0.3": 1, "0.5": 1, "0.7": 1}
    assert pc.matched_iou_mean is not None and pc.matched_iou_mean > 0.9
    assert pc.area["main"] == pytest.approx(0.458, abs=0.01)

    # a page the pipeline never saw
    sp2 = SamplePage(
        f"{W1}:0002",
        "handschriften",
        "",
        W1,
        "LeibnizHandschriften",
        "",
        "1v",
        2000,
        2500,
        0,
        "x",
        f"{W1}_0002.jpg",
    )
    pc2 = C.census_page(conn, sp2, results)
    assert pc2.status == "no_detections" and pc2.zones == {} and pc2.their_lines == 0
    assert pc2.v1_lines > 0 and pc2.v1_by_group == {"outside": pc2.v1_lines}

    pages = [pc, pc2]
    summ = C.summarize(pages, {"checkpoint": "ema.pth", "threshold": 0.4, "resolution": 1272})
    a = summ["all"]
    assert a["pages"] == 2 and a["pages_ok"] == 1 and a["pages_no_detections"] == 1
    assert a["zones"]["MainZone"] == {
        "total": 1,
        "per_page": 0.5,
        "pages_with": 1,
        "pages_with_share": 0.5,
        "conf_mean": 0.95,
    }
    assert a["pages_with_group"]["figure"] == {"pages": 1, "share": 0.5}
    assert a["v1_in_figure_or_formula"]["lines"] == 2
    assert a["matched"]["0.5"]["pairs"] == 1
    assert a["their_to_v1"] == pytest.approx(3 / a["v1_lines"], abs=0.001)
    assert summ["blocks"]["handschriften"]["pages"] == 2 and "marginalien_by_lang" not in summ

    csv_path = tmp_path / "per-page.csv"
    C.write_per_page(pages, csv_path)
    lines = csv_path.read_text().splitlines()
    assert lines[0].startswith("page_id,block,sub,work_id,label,file,status") and len(lines) == 3
    assert ",no,2.0," in lines[1] and "figure=1" in lines[1] and "MainZone=1" in lines[1]
    md = C.render(summ)
    assert md.startswith("# Layout-zone census") and "ema.pth" in md and "| **all** |" in md
    assert "## Where the v1 lines fall" in md and "What this does and does not show" in md
    C.write_summary(summ, tmp_path / "s.json")
    assert (tmp_path / "s.json").exists()


def test_marginalien_section_and_block_order() -> None:
    pages = []
    for i, (lang, v1, main, margin) in enumerate((("de", 10, 7, 2), ("la", 20, 15, 4))):
        pc = C.PageCensus(
            f"M:{i:04d}", "marginalien", lang, "M", "1r", f"M_{i:04d}.jpg", "ok", 100, 100, True
        )
        pc.zones = {"MainZone": 1, "MarginTextZone": 1}
        pc.v1_lines = v1
        pc.v1_by_group = {"main": main, "margin": margin, "outside": v1 - main - margin}
        pc.their_lines = v1
        pc.their_by_group = {"main": main, "margin": margin, "outside": v1 - main - margin}
        pc.matched = {"0.3": v1, "0.5": v1 - 1, "0.7": v1 - 2}
        pages.append(pc)
    extra = C.PageCensus("E:0001", "extra", "", "E", "", "E_0001.jpg", "no_detections")
    summ = C.summarize([extra, *pages])
    assert list(summ["blocks"]) == ["marginalien", "extra"]
    m = summ["marginalien_by_lang"]
    assert m["de"]["v1_by_group"]["main"] == {"lines": 7, "share": 0.7}
    assert summ["blocks"]["marginalien"]["v1_by_group"]["margin"]["lines"] == 6
    md = C.render(summ)
    assert "### The Marginalien: printed body against notes" in md
    assert "| de | 2 |" not in md and "| de | 1 |" in md
    assert "named extra" in md
