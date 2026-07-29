"""CLI-level tests for `leibniz catalog` (offline: guards + report writing)."""

from __future__ import annotations

from typer.testing import CliRunner

from leibniz import db
from leibniz.catalog import crosswalk as X
from leibniz.cli import app

runner = CliRunner()


def test_catalog_help_lists_commands() -> None:
    result = runner.invoke(app, ["catalog", "--help"])
    assert result.exit_code == 0
    for cmd in ("scrape", "crosswalk", "report"):
        assert cmd in result.stdout


def test_scrape_without_query_exits(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    db.init_db(db_path).close()
    result = runner.invoke(app, ["catalog", "scrape", "--db", str(db_path)])
    assert result.exit_code == 1
    assert "Nothing to scrape" in result.stdout


def test_crosswalk_without_records_is_graceful(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    db.init_db(db_path).close()
    result = runner.invoke(app, ["catalog", "crosswalk", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No katalog records" in result.stdout


def test_report_command_writes_file(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("00068199", "LeibnizHandschriften", shelfmarks=["LH 35, 13, 2c"]))
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            "342", metadata={"gwlb_ids": ["00068199"]}, shelfmark_refs=["LH 35, 13, 2c"]
        ),
    )
    X.build_crosswalk(conn)
    conn.commit()
    conn.close()

    out = tmp_path / "crosswalk.md"
    result = runner.invoke(app, ["catalog", "report", "--db", str(db_path), "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "# Katalog crosswalk" in text
    assert "100.0%" in text  # the one work is matched
