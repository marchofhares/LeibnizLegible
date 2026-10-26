"""Tests for the training-set tool (K3 Task 1): a seeded store, synthetic pages, offline."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align.audit_reach import open_readonly
from leibniz.align.pairs import GtPair, insert_gt_pairs
from leibniz.cli import app
from leibniz.htr import trainset as T

pytest.importorskip("PIL")
runner = CliRunner()
READER = "trocr-kurrent-xvi-xvii"


def _page_image(path: Path, n_lines: int) -> None:
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (600, 60 * n_lines + 40), "white")
    draw = ImageDraw.Draw(im)
    for k in range(n_lines):
        top = 20 + 60 * k
        draw.rectangle((40, top + 10, 560, top + 40), fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="JPEG")


def _source(label: str, rid: str, reader: str | None = None) -> str:
    by = f"; reader {reader}" if reader else ""
    return f"{label} (§70-expired AA reading text; channel ia{by}; katalog {rid})"


# Four records on three works. Record g1 (Leibniz's own hand, reader rows) on W pages 1-2;
# g2 (a scribe's, reader rows) on W page 3 and shares page 2 with g1 (so g1 and g2 are one
# unit); g3 (partial, v1 rows) on X pages 1-2; g4 (other, v1 rows) on Y page 1, a Marginalien
# work; plus the Latin reference rows of record l1 on Z pages 1-3 (v1).
RECORDS = {
    "g1": {"textart": "Konz.; eigh.", "absender": "Leibniz (GND)", "label": "AA I,9 N.1"},
    "g2": {"textart": "Abf.", "absender": "Fuchs,P. (GND)", "label": "AA I,9 N.2"},
    "g3": {"textart": "Abf.; eigh. Aufschr.", "absender": "Leibniz (GND)", "label": "AA I,9 N.3"},
    "g4": {"textart": "Konz.", "absender": None, "label": "AA I,9 N.4"},
    "l1": {"textart": "Abf.", "absender": "Leibniz (GND)", "label": "AA II,1 N.5"},
    "g5": {"textart": "Abf.", "absender": "Molanus (GND)", "label": "AA I,9 N.6"},
    "g6": {"textart": "Abf.", "absender": "Molanus (GND)", "label": "AA I,9 N.7"},
}
GERMAN = ["g1", "g2", "g3", "g4", "g5", "g6"]


def _seed(db_path: Path, images_root: Path) -> dict:
    conn = db.init_db(db_path)
    for wid, set_name in (
        ("W", "LeibnizBriefwechsel"),
        ("X", "LeibnizHandschriften"),
        ("Y", "LeibnizMarginalien"),
        ("Z", "LeibnizHandschriften"),
        ("V", "LeibnizBriefwechsel"),
        ("U", "LeibnizBriefwechsel"),
    ):
        db.upsert_work(conn, db.Work(wid, set_name, shelfmarks=[f"LBr {wid}"]))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    n_pages = {"W": 3, "X": 2, "Y": 1, "Z": 3, "V": 2, "U": 2}
    for wid, n in n_pages.items():
        for seq in range(1, n + 1):
            pid = f"{wid}:{seq:04d}"
            local = f"{wid}/{seq:04d}.jpg"
            db.upsert_page(
                conn,
                db.Page(
                    work_id=wid, seq=seq, label=f"{seq}r", status="recognized", local_path=local
                ),
            )
            if not (wid == "X" and seq == 2):  # X page 2 has no cached image
                _page_image(images_root / local, 4)
            for k in range(4):
                top = 20 + 60 * k
                poly = [[40, top + 10], [560, top + 10], [560, top + 40], [40, top + 40]]
                geom = (
                    {}
                    if (wid == "W" and seq == 3 and k == 3)
                    else {"polygon": poly, "baseline": [[40, top + 38]]}
                )
                db.insert_line(
                    conn, db.Line(page_id=pid, line_seq=k, run_id=seg, status="machine", **geom)
                )
                # the Latin reference pages: v1 texts whose lengths put the minted
                # text's ratio at 0.88–1.08, the band the German lines are held to
                v1 = "x" * (26, 24, 24, 24)[k] if wid == "Z" else "v1 text of " + "x" * (10 + k)
                db.set_line_recognition(conn, pid, k, text=v1, conf=0.5, model="htr", run_id=rec)
    for rid, meta in RECORDS.items():
        db.upsert_katalog_record(
            conn,
            db.KatalogRecord(
                record_id=rid,
                metadata={"textart": meta["textart"], "absender": meta["absender"]},
                shelfmark_refs=[],
                aa_refs=[],
            ),
        )
    pairs: list[GtPair] = []

    def gt(rid, ref, text, stratum, conf, reader=None):
        pairs.append(
            GtPair(
                ref, text, _source(RECORDS[rid]["label"], rid, reader), stratum, conf, "open", rid
            )
        )

    # g1: Leibniz's hand, reader rows on W:0001 (4 lines) and W:0002 (2 lines)
    for k in range(4):
        gt(
            "g1",
            f"W:0001:{k:03d}",
            f"Hochgeehrter Herr {k} ich habe",
            "heavy_revision",
            0.9,
            READER,
        )
    gt("g1", "W:0002:000", "vnd bedancke mich daß Sie mir", "heavy_revision", 0.95, READER)
    gt("g1", "W:0002:001", "a + b = c − d · x", "heavy_revision", 0.8, READER)  # math
    # g2: other hand, reader rows on W:0002 (2) and W:0003 (4)
    gt("g2", "W:0002:002", "haben zukommen lassen; es ist", "light_revision", 0.9, READER)
    gt("g2", "W:0002:003", "daß der Herr von [Boineburg]", "light_revision", 0.9, READER)
    for k in range(4):
        gt(
            "g2",
            f"W:0003:{k:03d}",
            f"zweite Seite Zeile {k} ganz lang und noch länger",
            "light_revision",
            0.85,
            READER,
        )
    # g3: partial, v1 rows on X pages 1-2
    for k in range(4):
        gt("g3", f"X:0001:{k:03d}", f"dritte Zeile {k} des Schreibers", "heavy_revision", 0.8)
    gt("g3", "X:0002:000", "auf der Seite ohne Bild", "heavy_revision", 0.8)
    # g4: Marginalien work
    gt("g4", "Y:0001:000", "am Rande notiert", "scrap", 0.9)
    # g5 and g6: two more scribes' letters (v1 rows), light revision, eight lines each, so
    # that the light_revision/other cell has three units to draw from
    for rid, wid in (("g5", "V"), ("g6", "U")):
        for seq in (1, 2):
            for k in range(4):
                gt(
                    rid,
                    f"{wid}:{seq:04d}:{k:03d}",
                    f"Brief des Schreibers {rid} Zeile {k}",
                    "light_revision",
                    0.85,
                )
    # l1: the Latin reference rows (v1), 12 lines
    for seq in range(1, 4):
        for k in range(4):
            gt(
                "l1",
                f"Z:{seq:04d}:{k:03d}",
                "textus latinus " + "y" * (8 + k),
                "fair_copy",
                0.9 + 0.02 * k,
            )
    insert_gt_pairs(conn, pairs)
    conn.commit()
    conn.close()
    # the reader's readings: a normal length on every reader line but W:0003:000 (very short)
    readings = {}
    for p in pairs:
        if "reader" in p.source:
            readings[p.line_image_ref] = (
                "a" if p.line_image_ref == "W:0003:000" else "r" * len(p.text)
            )
    return {"readings": readings}


def _files(tmp_path: Path, readings: dict) -> dict[str, Path]:
    d = tmp_path / "in"
    d.mkdir()
    rd = d / "readings.jsonl"
    rd.write_text(
        "".join(json.dumps({"line_id": k, "text": v}) + "\n" for k, v in readings.items()),
        encoding="utf-8",
    )
    fl = d / "flags.jsonl"
    fl.write_text(
        json.dumps({"ref": "X:0001:003", "flags": ["bracket", "addition"]}) + "\n",
        encoding="utf-8",
    )
    held = d / "heldout.csv"
    held.write_text(
        "page_id,work_id,file,split,status\nX:0001,X,f,noisy,matched\n", encoding="utf-8"
    )
    pool = d / "pool.csv"
    pool.write_text("letter_id,page_ids\n1708-1,Q:0001 Q:0002\n", encoding="utf-8")
    audit = d / "audit.csv"
    audit.write_text("ref,stratum,verdict,note\nW:0001:003,heavy_revision,,\n", encoding="utf-8")
    recs = d / "records.jsonl"
    recs.write_text("".join(json.dumps({"record_id": r}) + "\n" for r in GERMAN), encoding="utf-8")
    return {
        "readings": rd,
        "flags": fl,
        "heldout": held,
        "pool": pool,
        "audit": audit,
        "records": recs,
    }


def _build(tmp_path: Path, **kw) -> tuple[T.TrainSet, dict[str, Path]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "store.sqlite"
    images = tmp_path / "images"
    seeded = _seed(db_path, images)
    files = _files(tmp_path, seeded["readings"])
    conn = open_readonly(db_path)
    try:
        ts = T.build(
            conn,
            record_ids=GERMAN,
            readings={READER: T.load_readings_text(files["readings"])},
            flags=T.load_flags(files["flags"]),
            heldout=T.pages_from_csv(files["heldout"]),
            pool=T.pages_from_csv(files["pool"]),
            audit=T.refs_from_csvs([files["audit"]]),
            **kw,
        )
    finally:
        conn.close()
    files["db"] = db_path
    files["images"] = images
    return ts, files


def test_rows_tagged_by_hand_reader_and_volume(tmp_path: Path) -> None:
    ts, _ = _build(tmp_path)
    by = {ln.ref: ln for ln in ts.lines}
    assert len(ts.lines) == 34 and ts.records == 6
    g1 = by["W:0001:000"]
    assert (g1.hand, g1.group, g1.reader, g1.volume) == ("own", "leibniz", READER, "I,9")
    assert by["W:0003:000"].group == "other" and by["W:0003:000"].hand == "other"
    assert by["X:0001:000"].hand == "partial" and by["X:0001:000"].reader == "v1"
    # the machine text: the reader's reading on reader rows, the v1 text on v1 rows
    assert by["W:0001:000"].machine_text == "r" * by["W:0001:000"].n_chars
    assert by["X:0001:000"].machine_text.startswith("v1 text of")
    assert by["W:0003:000"].ratio is not None and by["W:0003:000"].ratio > 10


def test_exclusions_in_order(tmp_path: Path) -> None:
    ts, _ = _build(tmp_path)
    by = {ln.ref: ln for ln in ts.lines}
    assert by["W:0002:001"].reason == "math"  # the reader row screened by the pattern
    assert by["W:0002:003"].reason == "bracket"
    assert by["X:0001:003"].reason == "heldout_page"  # outranks its bracket flag
    assert "bracket" in by["X:0001:003"].flags
    assert by["Y:0001:000"].reason == "marginalien"
    assert by["W:0001:003"].reason == "audit"
    assert all(ln.reason == "heldout_page" for ln in ts.lines if ln.page_id == "X:0001")
    kept = [ln for ln in ts.lines if ln.split != "excluded"]
    assert len(kept) == 34 - 1 - 1 - 4 - 1 - 1


def test_band_and_screen(tmp_path: Path) -> None:
    ts, _ = _build(tmp_path)
    b = ts.band
    assert b.n == 12  # the Latin rows of l1, not the German records
    assert 0 < b.ratio_lo <= b.ratio_median <= b.ratio_hi
    sc = ts.screen
    assert set(sc["by_group"]) == {"leibniz", "other"}
    other = sc["by_group"]["other"]
    assert other["outside"] >= 1 and "ratio_high" in other["outside_by"]
    assert "conf_low" in other["outside_by"]  # g2's 0.85 lines under the Latin floor
    assert sc["worst"][0]["ref"] == "W:0003:000"
    by = {ln.ref: ln for ln in ts.lines}
    assert by["W:0003:000"].screen == ["ratio_high", "conf_low"]
    assert by["W:0001:000"].screen == []
    leib = sc["by_group"]["leibniz"]
    assert leib["n"] == 4 and leib["outside"] == 0  # the math and audit lines are not counted
    assert sc["stop"] is False
    band = T.band_of([1.0, 1.0, 1.0], [0.9, 0.9])
    assert T.outside(
        T.TrainLine("r", "p", 0, "x", "", "unknown", "own", "other", "v1", 0.5, "t", ratio=2.0),
        band,
    ) == ["ratio_high", "conf_low"]


def test_units_join_records_over_shared_pages(tmp_path: Path) -> None:
    ts, _ = _build(tmp_path)
    units = {ln.record_id: ln.unit for ln in ts.lines}
    assert units["g1"] == units["g2"] == "g1"
    assert units["g3"] == "g3" and units["g5"] == "g5" and units["g6"] == "g6"


def test_validation_is_page_disjoint_and_frozen(tmp_path: Path) -> None:
    ts, files = _build(tmp_path, share=0.5, seed=7)
    s = T.summarize(ts)
    assert s["pages_shared_between_splits"] == 0
    assert s["splits"]["val"]["lines"] > 0 and s["splits"]["train"]["lines"] > 0
    vp = tmp_path / "val.csv"
    T.write_val_pieces(vp, ts.lines)
    rows = list(csv.DictReader(vp.open(encoding="utf-8")))
    assert {r["record_id"] for r in rows} == {ln.record_id for ln in ts.lines if ln.split == "val"}
    # a second build reads the frozen pieces instead of drawing
    ts2, _ = _build(tmp_path / "again", share=0.5, seed=99, val_pieces=vp)
    assert ts2.val_frozen
    assert {ln.ref for ln in ts2.lines if ln.split == "val"} == {
        ln.ref for ln in ts.lines if ln.split == "val"
    }


def test_draw_is_deterministic_and_keeps_single_unit_cells() -> None:
    lines = []
    for u in range(6):
        for k in range(10):
            lines.append(
                T.TrainLine(
                    f"P{u}:{k:03d}",
                    f"P{u}",
                    k,
                    f"r{u}",
                    "I,1",
                    "heavy_revision",
                    "own",
                    "other",
                    "v1",
                    0.9,
                    "t",
                    unit=f"r{u}",
                    n_chars=1,
                )
            )
    lines.append(
        T.TrainLine(
            "Q:000",
            "Q",
            0,
            "s",
            "I,1",
            "fair_copy",
            "own",
            "leibniz",
            "v1",
            0.9,
            "t",
            unit="s",
            n_chars=1,
        )
    )
    a, acc = T.draw_validation(lines, share=0.2, seed=3)
    b, _ = T.draw_validation(lines, share=0.2, seed=3)
    assert a == b and len(a) >= 1
    assert acc["cells"]["fair_copy/leibniz"]["note"].startswith("a single unit")
    assert "s" not in a


def test_crops_written_in_kraken_format(tmp_path: Path) -> None:
    ts, files = _build(tmp_path, share=0.5, seed=7)
    out = tmp_path / "out"
    conn = open_readonly(files["db"])
    try:
        jobs = T.crop_jobs(conn, ts.lines, files["images"], out)
    finally:
        conn.close()
    tally = T.cut_crops(jobs, ts.lines, workers=0)
    assert tally["by_status"]["ok"] >= 5
    assert tally["by_status"].get("no_geometry") == 1  # W:0003:003
    assert tally["by_status"].get("no_image") == 1  # X:0002:000
    by = {ln.ref: ln for ln in ts.lines}
    assert by["W:0003:003"].reason == "no_geometry" and by["X:0002:000"].reason == "no_image"
    ok = [ln for ln in ts.lines if ln.image]
    for ln in ok:
        png = out / ln.image
        assert png.exists() and png.with_suffix(".gt.txt").read_text(encoding="utf-8") == (
            ln.text + "\n"
        )
        assert ln.image.startswith(f"{ln.split}/")
    paths = T.write_outputs(ts, out_root=out, reports_dir=tmp_path / "reports")
    listed = (out / "train.txt").read_text(encoding="utf-8").splitlines()
    assert listed and all(Path(p).exists() for p in listed)
    assert all("/train/" in p for p in listed)
    back = T.read_manifest(paths["manifest"])
    assert len(back) == len(ts.lines)
    report = paths["report"].read_text(encoding="utf-8")
    assert "## The screen" in report and "Pages on both sides: **0**" in report
    assert paths["val_pieces"].exists()
    # a later full run keeps the sample run's disk estimate
    prior = json.loads(paths["json"].read_text(encoding="utf-8"))
    prior["estimate"] = {
        "sampled": 3,
        "cut": 3,
        "bytes": 300,
        "bytes_per_line": 100.0,
        "kept_lines": 10,
        "projected_bytes": 1000.0,
    }
    paths["json"].write_text(json.dumps(prior), encoding="utf-8")
    ts.estimate = None
    paths = T.write_outputs(ts, out_root=out, reports_dir=tmp_path / "reports")
    assert "## Disk, from the sample" in paths["report"].read_text(encoding="utf-8")


def test_estimate_disk_projects_from_a_sample(tmp_path: Path) -> None:
    ts, files = _build(tmp_path)
    conn = open_readonly(files["db"])
    try:
        est = T.estimate_disk(
            conn, ts.lines, n=3, images_root=files["images"], out_root=tmp_path / "sample", seed=1
        )
    finally:
        conn.close()
    assert est["sampled"] == 3 and est["cut"] >= 1
    assert est["projected_bytes"] > 0 and math.isfinite(est["projected_bytes"])
    # the sample touched copies: the real lines keep their split
    assert all(ln.split in ("train", "val", "excluded") for ln in ts.lines)


def test_cli_train_set(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "store.sqlite"
    images = tmp_path / "images"
    seeded = _seed(db_path, images)
    files = _files(tmp_path, seeded["readings"])
    monkeypatch.chdir(tmp_path)
    args = [
        "bench",
        "train-set",
        "--db",
        str(db_path),
        "--records",
        str(files["records"]),
        "--images",
        str(images),
        "--readings",
        f"{READER}={files['readings']}",
        "--flags",
        str(files["flags"]),
        "--heldout",
        str(files["heldout"]),
        "--pool",
        str(files["pool"]),
        "--audit",
        str(files["audit"]),
        "--name",
        "t",
        "--out",
        str(tmp_path / "out"),
        "--reports-dir",
        str(tmp_path / "rep"),
        "--val-share",
        "0.5",
        "--seed",
        "7",
    ]
    res = runner.invoke(app, [*args, "--sample", "3"])
    assert res.exit_code == 0, res.output
    assert "sample:" in res.output and (tmp_path / "rep" / "t-val-pieces.csv").exists()
    assert not (tmp_path / "out" / "manifest.jsonl").exists()
    frozen = (tmp_path / "rep" / "t-val-pieces.csv").read_text(encoding="utf-8")
    res = runner.invoke(app, args)
    assert res.exit_code == 0, res.output
    flat = " ".join(res.output.split())  # an 80-column console wraps the lines
    assert "(frozen)" in flat and "wrote manifest" in flat
    assert (tmp_path / "rep" / "t-val-pieces.csv").read_text(encoding="utf-8") == frozen
    assert (tmp_path / "out" / "manifest.jsonl").exists()
    assert (tmp_path / "rep" / "t-trainset.md").exists()
