"""M1 Task 1b, the print trial (offline, on the fixture store and fixtures)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.conftest import W1

from leibniz import db
from leibniz.layout import print_report as R
from leibniz.layout import print_trial as T
from leibniz.layout.sample import SamplePage

FIX = Path(__file__).parent / "fixtures" / "layout"


def test_groups_and_types() -> None:
    assert T.print_group("MainZone-P") == "print"
    assert T.print_group("MarginTextZone-Notes") == "print"  # printed marginal notes
    assert T.print_group("MarginTextZone-ManuscriptAddendum") == "manuscript"
    assert T.print_group("StampZone") == "other" and T.print_group(None) == "other"
    assert T.print_group("RunningTitleZone") == "print" and T.print_group("MusicZone") == "print"
    assert T.philiumm_group("MainZone") == "print"
    assert T.philiumm_group("MarginTextZone") == "manuscript"
    assert T.philiumm_group("GraphicZone-figure") == "other"
    assert (
        T.type_of("de") == "fraktur" and T.type_of("la") == "roman" and T.type_of(None) == "roman"
    )


def _page(conn, pid: str, polys: list[list[list[int]]]) -> None:
    conn.execute("DELETE FROM lines WHERE page_id = ?", (pid,))
    run = db.start_run(conn, "segment", model="t")
    for i, poly in enumerate(polys):
        db.insert_line(
            conn,
            db.Line(
                pid,
                i,
                polygon=poly,
                text=f"printed line number {i} of the page",
                conf=0.8,
                model="m",
                run_id=run,
            ),
        )
    conn.commit()


def test_trial_page_sheet_and_ocr_input(store_path: Path, tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    from PIL import Image

    conn = db.connect(store_path)
    pid = f"{W1}:0001"  # 2000×2500 in the store; the fixture zones are at 1000×1250 → scale 2
    sx, sy = 2.0, 2.0
    polys = [
        [[120, 120], [680, 120], [680, 160], [120, 160]],  # print body
        [[120, 200], [680, 200], [680, 240], [120, 240]],  # print body
        [[730, 120], [980, 120], [980, 160], [730, 160]],  # the manuscript addendum
        [[120, 30], [680, 30], [680, 70], [120, 70]],  # the running title: print
        [[810, 1160], [980, 1160], [980, 1230], [810, 1230]],  # the stamp: other
        [[10, 1150], [90, 1150], [90, 1200], [10, 1200]],  # outside every zone
    ]
    _page(conn, pid, [[[round(x * sx), round(y * sy)] for x, y in p] for p in polys])
    zones_dir = tmp_path / "zones"
    zones_dir.mkdir()
    shutil.copy(FIX / "ladas_page.xml", zones_dir / f"{W1}_0001.xml")
    sp = SamplePage(
        pid,
        "marginalien",
        "la",
        W1,
        "LeibnizMarginalien",
        "Leibn. Marg. 1",
        "1r",
        2000,
        2500,
        6,
        f"{W1}/0001.jpg",
        f"{W1}_0001.jpg",
    )
    # PHILIUMM's zones for the comparison: a MainZone over the print body only
    phil = tmp_path / "phil"
    (phil / "01_predictions_json" / "rf-detr").mkdir(parents=True)
    import json as _json

    def pts(*xy):
        return [{"x": x, "y": y} for x, y in xy]

    predictions = [
        {
            "class": "MainZone",
            "confidence": 0.9,
            "points": pts((100, 100), (700, 100), (700, 1100), (100, 1100)),
        },
        {
            "class": "MarginTextZone",
            "confidence": 0.6,
            "points": pts((720, 100), (990, 100), (990, 600), (720, 600)),
        },
    ]
    (phil / "01_predictions_json" / "rf-detr" / f"{W1}_0001.json").write_text(
        _json.dumps({"image": {"width": 1000, "height": 1250}, "predictions": predictions})
    )
    pages = T.trial(conn, [sp], zones_dir, philiumm_results=phil)
    pt = pages[0]
    assert pt.status == "ok" and pt.scale == 2.0 and pt.print_type == "roman"
    assert pt.zones == {
        "MainZone-P": 1,
        "MarginTextZone-ManuscriptAddendum": 1,
        "RunningTitleZone": 1,
        "StampZone": 1,
    }
    assert pt.v1_lines == 6
    assert pt.v1_by_group == {"print": 3, "manuscript": 1, "other": 1, "outside": 1}
    assert pt.v1_by_philiumm == {"print": 2, "manuscript": 1, "outside": 3}
    assert pt.agreement["print|print"] == 2 and pt.agreement["manuscript|manuscript"] == 1
    assert (
        pt.iou_lines_print is not None and 0.05 < pt.iou_lines_print < 0.3
    )  # thin lines in a big zone
    assert pt.iou_print_models is not None and 0.8 < pt.iou_print_models <= 1.0
    assert pt.area["print"] == pytest.approx(0.52, abs=0.02) and pt.area[
        "manuscript"
    ] == pytest.approx(0.108, abs=0.01)

    summ = T.summarize(pages, {"works": 1})
    a = summ["all"]
    assert a["print_body_share_of_lines"] == 0.5 and a["pages_with_manuscript_zone"] == 1
    assert a["philiumm"]["same_call"] == {"lines": 4, "share": 0.6667}  # outside|outside counts
    assert "roman" in summ["by_type"] and summ["by_type"]["roman"]["pages"] == 1

    # a page without zones
    sp2 = SamplePage(
        f"{W1}:0002",
        "marginalien",
        "de",
        W1,
        "LeibnizMarginalien",
        "",
        "1v",
        2000,
        2500,
        0,
        "x",
        f"{W1}_0002.jpg",
    )
    pt2 = T.trial(conn, [sp2], zones_dir)[0]
    assert pt2.status == "no_zones" and pt2.print_type == "fraktur" and pt2.v1_lines > 0

    # the sheet: lines inside print zones with enough text, spread over pages
    lines = T.select_sheet_lines(pages, per_type=2, seed=1)
    assert len(lines) == 2 and {ln.print_type for ln in lines} == {"roman"}
    assert all(ln.ref.startswith(pid) for ln in lines)
    root = tmp_path / "images"
    (root / W1).mkdir(parents=True)
    Image.new("RGB", (2000, 2500), (230, 230, 230)).save(root / W1 / "0001.jpg")
    conn.execute("UPDATE pages SET local_path = ? WHERE page_id = ?", (f"{W1}/0001.jpg", pid))
    conn.commit()
    crops = T.crops_for(conn, lines, root)
    assert all(crops[ln.ref] for ln in lines)
    html = T.render_sheet(lines, crops, seed=1)
    assert html.count("<input type='text'") == 2 and "data:image/png;base64," in html
    assert "print-sheet-transcriptions.csv" in html
    T.write_sheet_lines(lines, tmp_path / "sheet.csv")
    back = T.read_sheet_lines(tmp_path / "sheet.csv")
    assert [b.ref for b in back] == [ln.ref for ln in lines]

    # the OCR input: the print lines only, ids in the canonical form
    n = T.write_ocr_input(conn, pt, root / W1 / "0001.jpg", tmp_path / "ocr-in" / "p.xml")
    assert n == 3
    from leibniz.layout.zones import read_page_xml

    doc = read_page_xml(tmp_path / "ocr-in" / "p.xml")
    assert len(doc.lines) == 3 and doc.lines[0].id == f"{pid}:000"
    assert doc.image.endswith("0001.jpg") and (doc.width, doc.height) == (2000, 2500)

    # the per-page CSV and the JSON round-trip
    T.write_per_page(pages, tmp_path / "pp.csv")
    assert (tmp_path / "pp.csv").read_text().count("\n") == 2
    T.write_lines_csv(pages, tmp_path / "lines.csv")
    assert (tmp_path / "lines.csv").read_text().count("\n") == 7
    T.write_json(T.pages_to_json(pages), tmp_path / "t.json")
    assert "lines" not in T.pages_to_json(pages)[0]


def test_score_and_decision(tmp_path: Path) -> None:
    lines = [
        T.SheetLine("P:0001:000", "P:0001", 0, "roman", "la", "Quod erat demonstrandum"),
        T.SheetLine("P:0001:001", "P:0001", 1, "roman", "la", "Tabula rasa"),
        T.SheetLine("P:0002:000", "P:0002", 0, "fraktur", "de", "Die Welt ist alles"),
        T.SheetLine("P:0002:001", "P:0002", 1, "fraktur", "de", "ohne Transkription"),
    ]
    csv_path = tmp_path / "t.csv"
    csv_path.write_text(
        "ref,type,transcription\n"
        'P:0001:000,roman,"Quod erat demonstrandum"\n'
        'P:0001:001,roman,"Tabula rasa"\n'
        'P:0002:000,fraktur,"Die Welt ist alles"\n'
        'P:0002:001,fraktur,""\n',
        encoding="utf-8",
    )
    refs = T.read_transcriptions(csv_path)
    assert len(refs) == 3  # the empty field is no transcription
    hyps = {
        "P:0001:000": "Quod erat demonstrandum",
        "P:0001:001": "Tabula raso",
        "P:0002:000": "Dir Wrlt ist alles",
    }
    s = T.score(refs, hyps, lines)
    assert (
        s["lines_transcribed"] == 3
        and s["lines_scored"] == 3
        and s["lines_without_hypothesis"] == 0
    )
    assert s["by_type"]["roman"]["cer"] == pytest.approx(1 / 34, abs=0.001)
    assert s["by_type"]["fraktur"]["cer"] == pytest.approx(2 / 18, abs=0.001)
    # the decision from the CER by type
    assert (
        R.decision(
            {
                "cer": {
                    "gallicorpora": {"by_type": {"roman": {"cer": 0.05}, "fraktur": {"cer": 0.08}}}
                }
            }
        )[0]
        == "a"
    )
    assert (
        R.decision(
            {
                "cer": {
                    "gallicorpora": {"by_type": {"roman": {"cer": 0.45}, "fraktur": {"cer": 0.6}}}
                }
            }
        )[0]
        == "c"
    )
    assert (
        R.decision(
            {
                "cer": {
                    "gallicorpora": {"by_type": {"roman": {"cer": 0.05}, "fraktur": {"cer": 0.6}}}
                }
            }
        )[0]
        == "a/c"
    )
    assert (
        R.decision(
            {"cer": {"gallicorpora": {"by_type": {"roman": {"cer": 0.2}, "fraktur": {"cer": 0.6}}}}}
        )[0]
        == "b"
    )
    assert R.decision({})[0] == "pending"


def test_report_renders_pending_and_with_cer(store_path: Path) -> None:
    conn = db.connect(store_path)
    pt = T.PageTrial(
        "M:0001",
        "M",
        "1r",
        "la",
        "roman",
        "M_0001.jpg",
        "ok",
        2.0,
        {"MainZone-P": 1},
        {"print": 0.5},
    )
    pt.v1_lines = 10
    pt.v1_by_group = {"print": 8, "manuscript": 2}
    pt.iou_lines_print = 0.2
    summ = T.summarize([pt], {"works": 1, "device": "cuda:0"})
    summ["fraktur_share_corpus"] = R.fraktur_share(conn)
    summ["ocr_lines"] = 8
    md = R.render(summ)
    assert md.startswith("# The print trial") and "**The decision waits for the CER" in md
    assert "| MainZone-P | print | 1 |" in md and "print-trial cer --transcriptions" in md
    summ["cer"] = {
        "transcriptions": "x.csv",
        "gallicorpora": {
            "policy": "p",
            "lines_transcribed": 50,
            "lines_scored": 50,
            "cer": 0.06,
            "by_type": {"roman": {"lines": 25, "cer": 0.04}, "fraktur": {"lines": 25, "cer": 0.08}},
        },
        "v1": {
            "policy": "p",
            "lines_transcribed": 50,
            "lines_scored": 50,
            "cer": 0.3,
            "by_type": {"roman": {"lines": 25, "cer": 0.25}, "fraktur": {"lines": 25, "cer": 0.35}},
        },
    }
    md = R.render(summ)
    assert (
        "(a) the printed body is read with a print model" in md
        and "| Gallicorpora+ (print) | 50 | 6.0 % | 4.0 % | 8.0 % |" in md
    )
    assert R.fraktur_share(conn) == {} or "pages" in R.fraktur_share(conn)
