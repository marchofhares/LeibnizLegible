"""Tests for the GT hand-audit sheet + scorer (offline; synthetic page image)."""

from __future__ import annotations

import csv
from pathlib import Path

from typer.testing import CliRunner

from leibniz import db
from leibniz.align import audit
from leibniz.align.pairs import GtPair, insert_gt_pairs
from leibniz.cli import app

runner = CliRunner()
SOURCE = "AA VI,4 N. 109 (§70-expired AA reading text; katalog R1)"


def _seed(db_path: Path, images_root: Path, *, with_image: bool = True) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W", "LeibnizHandschriften"))
    db.upsert_page(
        conn,
        db.Page(
            work_id="W",
            seq=1,
            label="12r",
            status="recognized",
            local_path="W/0001.jpg",
            width=400,
            height=300,
        ),
    )
    rid = db.start_run(conn, "segment", model="seg")
    strata = ["fair_copy", "light_revision", "heavy_revision", "scrap"]
    pairs = []
    for k in range(8):
        y = 20 + 30 * k
        db.insert_line(
            conn,
            db.Line(
                page_id="W:0001",
                line_seq=k,
                polygon=[[10, y], [390, y], [390, y + 22], [10, y + 22]],
                baseline=[[10, y + 18], [390, y + 18]],
                run_id=rid,
                status="machine",
            ),
        )
        db.set_line_recognition(
            conn, "W:0001", k, text=f"htr text {k}", conf=0.9, model="htr", run_id=rid
        )
        pairs.append(
            GtPair(
                line_image_ref=f"W:0001:{k:03d}",
                text=f"gt text {k}",
                source=SOURCE,
                stratum=strata[k % 4],
                align_conf=0.8 + k / 100,
                license_bucket="open",
            )
        )
    insert_gt_pairs(conn, pairs)
    conn.commit()
    conn.close()
    if with_image:
        from PIL import Image

        (images_root / "W").mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (400, 300), "white").save(images_root / "W" / "0001.jpg")


def test_allocate_equal_split_capped_by_supply() -> None:
    alloc = audit.allocate({"fair_copy": 5, "light_revision": 1000, "heavy_revision": 1000}, 100)
    assert alloc["fair_copy"] == 5
    assert sum(alloc.values()) == 100
    assert abs(alloc["light_revision"] - alloc["heavy_revision"]) <= 1
    assert audit.allocate({}, 10) == {}
    assert audit.allocate({"scrap": 3}, 10) == {"scrap": 3}


def test_crop_box_pads_and_clamps() -> None:
    box = audit.crop_box([[10, 20], [390, 20], [390, 42], [10, 42]], None, width=400, height=300)
    assert box == (0, 8, 400, 54)
    # baseline only → a band above the baseline
    box2 = audit.crop_box(None, [[100, 100], [200, 100]], width=400, height=300, pad=10)
    assert box2 is not None and box2[1] < 100 < box2[3]
    assert audit.crop_box(None, None, width=10, height=10) is None


def test_build_sheet_with_crops(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    conn = db.connect(db_path)
    sheet = audit.build_sheet(conn, images_root=images, out_dir=tmp_path / "audit", n=4, seed=1)
    conn.close()
    assert len(sheet.lines) == 4 and sheet.n_with_crops == 4
    assert sheet.by_stratum == {
        "fair_copy": 1,
        "light_revision": 1,
        "heavy_revision": 1,
        "scrap": 1,
    }
    page = sheet.html_path.read_text(encoding="utf-8")
    assert page.count("data:image/png;base64,") == 4
    for ln in sheet.lines:
        assert ln.ref in page and ln.htr_text and ln.htr_text.startswith("htr text")
        assert ln.label == "12r"
    with sheet.csv_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 4 and all(r["image"] == "yes" for r in rows)
    # the draw is reproducible
    conn = db.connect(db_path)
    again = audit.sample_lines(conn, 4, seed=1)
    conn.close()
    assert [ln.ref for ln in again] == [ln.ref for ln in sheet.lines]


def test_build_sheet_without_cached_images_lists_the_reason(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images, with_image=False)
    conn = db.connect(db_path)
    sheet = audit.build_sheet(conn, images_root=images, out_dir=tmp_path / "audit", n=3)
    conn.close()
    assert sheet.n_with_crops == 0
    assert all("not cached" in ln.image_note for ln in sheet.lines)
    assert "no image:" in sheet.html_path.read_text(encoding="utf-8")


def test_wilson_interval() -> None:
    lo, hi = audit.wilson(48, 50)
    assert 0.86 < lo < 0.92 and 0.98 < hi <= 1.0
    assert audit.wilson(0, 0) == (0.0, 1.0)


def test_score_verdicts_weighted_and_rendered() -> None:
    rows = (
        [{"ref": f"a{k}", "stratum": "fair_copy", "verdict": "correct"} for k in range(10)]
        + [{"ref": f"b{k}", "stratum": "heavy_revision", "verdict": "correct"} for k in range(7)]
        + [{"ref": "b7", "stratum": "heavy_revision", "verdict": "boundary"}]
        + [{"ref": "b8", "stratum": "heavy_revision", "verdict": "wrong"}]
        + [{"ref": "b9", "stratum": "heavy_revision", "verdict": "unreadable"}]
        + [{"ref": "c0", "stratum": "scrap", "verdict": ""}]
    )
    score = audit.score_verdicts(rows, {"fair_copy": 100, "heavy_revision": 900})
    fc, hr = score.by_stratum["fair_copy"], score.by_stratum["heavy_revision"]
    assert fc.precision == 1.0 and hr.n_scored == 9 and abs(hr.precision - 7 / 9) < 1e-9
    assert abs(hr.usable - 8 / 9) < 1e-9 and hr.unreadable == 1
    assert score.n_unjudged == 1
    assert abs(score.weighted_precision - (0.1 * 1.0 + 0.9 * 7 / 9)) < 1e-9
    assert score.passes_gate is False
    md = audit.render_score(score)
    assert "FAIL" in md and "| fair_copy | 10 | 10 |" in md and "heavy_revision" in md


def test_audit_cli_roundtrip(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    out_dir = tmp_path / "audit"
    res = runner.invoke(
        app,
        [
            "align",
            "audit-sheet",
            "--db",
            str(db_path),
            "--images",
            str(images),
            "--out",
            str(out_dir),
            "--n",
            "4",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "4 with image strips" in res.stdout
    # the auditor's download, copied next to the sheet's CSV (as the runbook says)
    verdicts = out_dir / "gt-audit-verdicts.csv"
    with (out_dir / "gt-audit-lines.csv").open(encoding="utf-8") as fh:
        lines = list(csv.DictReader(fh))
    with verdicts.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "verdict", "note"])
        for r in lines:
            w.writerow([r["ref"], r["stratum"], "correct", ""])
    md = tmp_path / "gt-audit.md"
    res2 = runner.invoke(
        app, ["align", "audit-score", str(verdicts), "--db", str(db_path), "--out", str(md)]
    )
    assert res2.exit_code == 0, res2.stdout
    assert "PASS" in res2.stdout
    assert "100.0 %" in md.read_text(encoding="utf-8")
    assert "contradict" not in res2.stdout

    # a "wrong" on a line whose HTR reading agrees with the minted text (0.8 here:
    # "gt text k" vs "htr text k") is flagged for a second look
    with verdicts.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "verdict", "note"])
        for k, r in enumerate(lines):
            w.writerow([r["ref"], r["stratum"], "wrong" if k == 0 else "correct", ""])
    res3 = runner.invoke(
        app, ["align", "audit-score", str(verdicts), "--db", str(db_path), "--out", str(md)]
    )
    assert res3.exit_code == 0, res3.stdout
    assert "1 verdicts contradict" in res3.stdout
    text = md.read_text(encoding="utf-8")
    assert "Second witness" in text and lines[0]["ref"] in text and "likely the same line" in text


def test_text_evidence_flags_only_contradictions(tmp_path: Path) -> None:
    lines_csv = tmp_path / "gt-audit-lines.csv"
    with lines_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "align_conf", "folio", "gt_text", "htr_text", "image"])
        w.writerow(
            ["a", "fair_copy", "0.9", "", "la difficulté demeure", "la diffienete demeuve", "yes"]
        )
        w.writerow(["b", "fair_copy", "0.9", "", "prier de vouloir bien", "sur", "yes"])
        w.writerow(["c", "fair_copy", "0.9", "", "gran spina al quore", "granspina alouore", "yes"])
    rows = [
        {"ref": "a", "stratum": "fair_copy", "verdict": "wrong"},  # agrees → re-check
        {"ref": "b", "stratum": "fair_copy", "verdict": "correct"},  # disagrees → re-check
        {"ref": "c", "stratum": "fair_copy", "verdict": "correct"},  # agrees → fine
        {"ref": "zzz", "stratum": "fair_copy", "verdict": "correct"},  # not on the sheet
    ]
    ev = audit.text_evidence(rows, lines_csv)
    assert [e.ref for e in ev] == ["a", "b", "c"]
    assert ev[0].recheck and "same line" in ev[0].recheck
    assert ev[1].recheck and "only" in ev[1].recheck
    assert ev[2].recheck is None
