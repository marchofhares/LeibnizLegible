"""CLI-level tests for `leibniz images` (offline: pages/stats/verify + guards)."""

from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app

runner = CliRunner()
FIX = Path(__file__).parent / "fixtures" / "mets" / "listrecords_filesec.xml"


def test_images_help_lists_commands() -> None:
    result = runner.invoke(app, ["images", "--help"])
    assert result.exit_code == 0
    for cmd in ("pages", "fetch", "verify", "stats"):
        assert cmd in result.stdout


def _seed_db_and_cache(tmp_path: Path) -> tuple[Path, Path]:
    db_path = tmp_path / "inv.sqlite"
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("IIIF-001", "LeibnizHandschriften", n_canvases=2))
    db.upsert_work(conn, db.Work("STATIC-002", "LeibnizBriefwechsel", n_canvases=2))
    conn.commit()
    conn.close()
    cache = tmp_path / "oai"
    (cache / "LeibnizHandschriften").mkdir(parents=True)
    shutil.copy(FIX, cache / "LeibnizHandschriften" / "page_0001.xml")
    return db_path, cache


def test_pages_command_populates_offline(tmp_path) -> None:
    db_path, cache = _seed_db_and_cache(tmp_path)
    result = runner.invoke(
        app, ["images", "pages", "--db", str(db_path), "--oai-cache", str(cache)]
    )
    assert result.exit_code == 0
    assert "pages: 4" in result.stdout
    conn = db.connect(db_path)
    assert db.count_pages(conn) == 4
    conn.close()


def test_pages_command_errors_without_cache(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    db.init_db(db_path).close()
    result = runner.invoke(
        app, ["images", "pages", "--db", str(db_path), "--oai-cache", str(tmp_path / "empty")]
    )
    assert result.exit_code == 1
    assert "No cached OAI XML" in result.stdout


def test_fetch_command_no_targets_is_graceful(tmp_path) -> None:
    db_path = tmp_path / "empty.sqlite"
    db.init_db(db_path).close()
    result = runner.invoke(app, ["images", "fetch", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No fetch targets" in result.stdout


def test_stats_command_appends_to_census(tmp_path) -> None:
    db_path, cache = _seed_db_and_cache(tmp_path)
    runner.invoke(app, ["images", "pages", "--db", str(db_path), "--oai-cache", str(cache)])
    out = tmp_path / "census.md"
    out.write_text("# Census\n", encoding="utf-8")
    result = runner.invoke(app, ["images", "stats", "--db", str(db_path), "--out", str(out)])
    assert result.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert "Image cache (Phase A2)" in text
    # 0 fetched, 4 targets — the section still renders coverage honestly.
    assert "0 / 4 pages" in text or "0/4" in result.stdout
