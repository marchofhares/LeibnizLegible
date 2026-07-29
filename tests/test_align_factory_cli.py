"""CLI-level tests for the C2 align commands (pieces/factory/gt-report), offline."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from leibniz import db
from leibniz.align.pairs import count_gt_lines
from leibniz.cli import app

runner = CliRunner()
LINE_TEXTS = ["prima linea textus", "secunda pars sententiae", "tertia et ultima"]


def _seed(db_path: Path) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W", "LeibnizHandschriften"))
    for i, lab in enumerate(["163r", "164r", "164v", "165r"], start=1):
        db.upsert_page(conn, db.Page(work_id="W", seq=i, label=lab, status="recognized"))
    rid = db.start_run(conn, "segment", model="seg")
    for seq in (2, 3, 4):  # folios 164, 165
        pid = f"W:{seq:04d}"
        for k, t in enumerate(LINE_TEXTS):
            db.insert_line(conn, db.Line(page_id=pid, line_seq=k, run_id=rid, status="machine"))
            db.set_line_recognition(conn, pid, k, text=t, conf=0.9, model="htr", run_id=rid)
        db.upsert_page_stats(
            conn, db.PageStats(page_id=pid, n_lines=3, line_height_cv=0.1, run_id=rid)
        )
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="REC1",
            metadata={"textart": "Reinschrift"},
            shelfmark_refs=["LH 4, 6, 18 Bl. 164-165"],
            aa_refs=[{"series": 6, "volume": 4, "piece": "109"}],
        ),
    )
    db.upsert_crosswalk(conn, db.CrosswalkMatch("REC1", "W", "gwlb_link", 1.0))
    conn.commit()
    conn.close()


def test_pieces_command(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed(db_path)
    result = runner.invoke(app, ["align", "pieces", "--db", str(db_path), "--today", "2026-07-29"])
    assert result.exit_code == 0
    assert "localizable 1" in result.stdout
    assert "VI,4" in result.stdout


def test_factory_and_gt_report_commands(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed(db_path)
    cache = tmp_path / "edition.json"
    cache.write_text(json.dumps({"REC1": " ".join(LINE_TEXTS * 3)}), encoding="utf-8")
    res = runner.invoke(
        app, ["align", "factory", str(cache), "--db", str(db_path), "--today", "2026-07-29"]
    )
    assert res.exit_code == 0
    assert "minted" in res.stdout
    conn = db.connect(db_path)
    assert count_gt_lines(conn, license_bucket="open") == 9
    conn.close()

    out = tmp_path / "gt-factory.md"
    res2 = runner.invoke(
        app,
        ["align", "gt-report", "--db", str(db_path), "--out", str(out), "--today", "2026-07-29"],
    )
    assert res2.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert "GT factory" in text
    assert "VI,4" in text  # minted volume surfaces in the report
