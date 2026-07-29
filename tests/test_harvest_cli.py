"""CLI-level tests for `leibniz harvest` (offline: census + guard paths only)."""

from __future__ import annotations

from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app

runner = CliRunner()


def test_harvest_help_lists_commands() -> None:
    result = runner.invoke(app, ["harvest", "--help"])
    assert result.exit_code == 0
    for cmd in ("oai", "manifests", "census"):
        assert cmd in result.stdout


def test_census_command_writes_report(tmp_path) -> None:
    db_path = tmp_path / "inv.sqlite"
    conn = db.init_db(db_path)
    db.upsert_work(
        conn,
        db.Work(
            gwlb_object_id="00068642",
            set_name="LeibnizHandschriften",
            shelfmarks=["LH 4, 6, 18"],
            metadata={"leibniz_sets": ["LeibnizHandschriften"]},
            n_canvases=4,
        ),
    )
    conn.commit()
    conn.close()

    out = tmp_path / "census.md"
    result = runner.invoke(app, ["harvest", "census", "--db", str(db_path), "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "# Corpus census" in text
    assert "00068642" in text  # the single work shows up as the largest


def test_manifests_command_with_no_works_is_graceful(tmp_path) -> None:
    db_path = tmp_path / "empty.sqlite"
    db.init_db(db_path).close()
    result = runner.invoke(app, ["harvest", "manifests", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No matching works" in result.stdout
