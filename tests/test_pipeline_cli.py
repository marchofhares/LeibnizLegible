"""CLI-level tests for `leibniz pipeline` (offline: status/report + guards)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app

runner = CliRunner()


def test_pipeline_help_lists_commands() -> None:
    result = runner.invoke(app, ["pipeline", "--help"])
    assert result.exit_code == 0
    for cmd in ("segment", "recognize", "status", "report"):
        assert cmd in result.stdout


def _seed_recognized(db_path: Path) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W1", "LeibnizHandschriften"))
    db.upsert_page(
        conn, db.Page(work_id="W1", seq=1, image_url="u", sha256="s", status="recognized")
    )
    rid = db.start_run(conn, "segment", model="philiumm-seg")
    db.insert_line(conn, db.Line(page_id="W1:0001", line_seq=0, run_id=rid, status="machine"))
    db.set_line_recognition(conn, "W1:0001", 0, text="hi", conf=0.9, model="htr@1", run_id=rid)
    db.upsert_page_stats(conn, db.PageStats(page_id="W1:0001", n_lines=1, run_id=rid))
    conn.commit()
    conn.close()


def test_status_command(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed_recognized(db_path)
    result = runner.invoke(app, ["pipeline", "status", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "recognized" in result.stdout
    assert "1 recognised" in result.stdout or "1 recognised)" in result.stdout


def test_report_command_writes_markdown(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed_recognized(db_path)
    out = tmp_path / "htr-v1-sample.md"
    result = runner.invoke(app, ["pipeline", "report", "--db", str(db_path), "--out", str(out)])
    assert result.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert "HTR v1 — corpus segmentation" in text
    assert "Pipeline coverage" in text


def test_segment_without_kraken_exits_cleanly(tmp_path, monkeypatch) -> None:
    # Simulate the kraken stack being absent: `import kraken` must raise.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "kraken" or name.startswith("kraken."):
            raise ModuleNotFoundError("No module named 'kraken'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    db_path = tmp_path / "inv.sqlite"
    db.init_db(db_path).close()
    result = runner.invoke(app, ["pipeline", "segment", "--db", str(db_path)])
    assert result.exit_code == 1
    assert "kraken" in result.stdout
