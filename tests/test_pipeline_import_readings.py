"""The readings import (K4 Task 4) on the fixture store: one scoped run beside v1,
empty readings write no row, idempotent, resumable by page."""

from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import W3, W4
from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app
from leibniz.pipeline import import_readings as I
from leibniz.search.documents import latest_lines

P1, P2, Q1 = f"{W3}:0001", f"{W3}:0002", f"{W4}:0001"


def _readings(path: Path, rows: list[tuple[str, str, float | None]]) -> Path:
    path.write_text(
        "".join(
            json.dumps(
                {
                    "line_id": lid,
                    "text": text,
                    "conf": conf,
                    "model": "k3",
                    "device": "cpu",
                    "ms": 1,
                }
            )
            + "\n"
            for lid, text, conf in rows
        ),
        encoding="utf-8",
    )
    return path


def test_dry_run_counts_and_writes_nothing(german_store_path: Path, tmp_path: Path) -> None:
    readings = _readings(
        tmp_path / "k3.jsonl",
        [
            (f"{P1}:000", "Jch habe Ew. Excellenz Schreiben", 0.9),
            (f"{P1}:001", "", 0.1),  # empty: no row
            (f"{P1}:002", "vnd so weiter fort", 0.8),
            (f"{P1}:099", "orphan", 0.5),  # no such line
            (f"{Q1}:000", "Mein Herr", 0.7),
        ],
    )
    conn = db.connect(german_store_path)
    before = conn.execute("SELECT COUNT(*) FROM lines").fetchone()[0]
    stats = I.import_readings(
        conn, readings_path=readings, page_ids=[P1, P2, Q1], model="k3@v", reader="k3-trocr"
    )
    assert stats.dry_run and stats.run_id is None
    assert stats.pages == 3 and stats.pages_without_readings == 1  # P2
    assert stats.lines == 5 + 5 + 1
    assert stats.rows_written == 3 and stats.pages_written == 2
    assert stats.empty_readings == 1 and stats.orphan_readings == 1
    assert stats.lines_without_reading == 2 + 5  # P1's lines 3, 4; all of P2
    assert conn.execute("SELECT COUNT(*) FROM lines").fetchone()[0] == before
    assert stats.by_set["LeibnizHandschriften"]["rows"] == 2
    assert "would write 3 rows on 2 pages" in " ".join(I.summary_lines(stats))


def test_write_is_scoped_idempotent_and_resumable(german_store_path: Path, tmp_path: Path) -> None:
    readings = _readings(
        tmp_path / "k3.jsonl",
        [
            (f"{P1}:000", "Jch habe Ew. Excellenz Schreiben", 0.9),
            (f"{P1}:001", "   ", None),
            (f"{P1}:002", "vnd so weiter fort", 0.8),
            (f"{Q1}:000", "Mein Herr", 0.7),
        ],
    )
    conn = db.init_db(german_store_path)
    stats = I.import_readings(
        conn,
        readings_path=readings,
        page_ids=[P1, Q1],
        model="k3-trocr@runs-615-epoch-5",
        reader="k3-trocr",
        write=True,
        git_sha="abc",
    )
    run_id = stats.run_id
    assert run_id is not None and stats.rows_written == 3 and stats.empty_readings == 1
    run = conn.execute(
        "SELECT stage, model, scope, n_input, n_ok, params FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    assert tuple(run)[:5] == ("recognize", "k3-trocr@runs-615-epoch-5", "de", 6, 3)
    assert json.loads(run["params"])["import"]["rows_written"] == 3
    # the rows: beside v1, the geometry copied, lang de, the rule shows them
    rows = conn.execute(
        "SELECT line_seq, text, conf, model, status, lang, polygon, source FROM lines "
        "WHERE run_id = ? ORDER BY page_id, line_seq",
        (run_id,),
    ).fetchall()
    assert [(r["line_seq"], r["text"]) for r in rows] == [
        (0, "Jch habe Ew. Excellenz Schreiben"),
        (2, "vnd so weiter fort"),
        (0, "Mein Herr"),
    ]
    assert all(r["lang"] == "de" and r["status"] == "machine" for r in rows)
    v1 = conn.execute(
        "SELECT polygon FROM lines WHERE page_id = ? AND line_seq = 0 AND run_id != ?", (P1, run_id)
    ).fetchone()
    assert rows[0]["polygon"] == v1["polygon"]
    assert json.loads(rows[0]["source"])["reader"] == "k3-trocr"
    shown = latest_lines(conn, P1)
    assert [(ln.line_seq, ln.run_id == run_id) for ln in shown] == [
        (0, True),
        (1, False),  # the empty reading: v1's row shows
        (2, True),
        (3, False),
        (4, False),
    ]
    assert shown[1].text == "die Sache wegen der Müntze"
    assert I.rows_under_run(conn, run_id) == (2, 3)
    # again: nothing added, the same run finished twice is not reopened
    again = I.import_readings(
        conn,
        readings_path=readings,
        page_ids=[P1, Q1],
        model="k3-trocr@runs-615-epoch-5",
        reader="k3-trocr",
        write=True,
    )
    assert again.run_id != run_id  # a finished run is not reused …
    assert again.rows_written == 3  # … but insert_line upserts on (page, line, run)? no: new run
    total = conn.execute("SELECT COUNT(*) FROM lines WHERE lang = 'de' AND model LIKE 'k3%'")
    assert total.fetchone()[0] == 6


def test_resume_skips_pages_the_open_run_holds(german_store_path: Path, tmp_path: Path) -> None:
    readings = _readings(
        tmp_path / "k3.jsonl",
        [(f"{P1}:000", "Jch habe", 0.9), (f"{Q1}:000", "Mein Herr", 0.7)],
    )
    conn = db.init_db(german_store_path)
    # a first invocation that stopped after P1: its run is still open
    first = I.import_readings(
        conn, readings_path=readings, page_ids=[P1], model="k3@v", reader="k3-trocr", write=True
    )
    conn.execute("UPDATE runs SET finished_at = NULL WHERE run_id = ?", (first.run_id,))
    conn.commit()
    assert I.find_open_run(conn, model="k3@v", scope="de") == first.run_id
    second = I.import_readings(
        conn,
        readings_path=readings,
        page_ids=[P1, Q1],
        model="k3@v",
        reader="k3-trocr",
        write=True,
    )
    assert second.run_id == first.run_id
    assert second.pages_done_before == 1 and second.rows_written == 1
    assert I.rows_under_run(conn, first.run_id) == (2, 2)
    assert I.find_open_run(conn, model="k3@v", scope="de") is None


def test_narrow_crops_are_counted_and_written(german_store_path: Path, tmp_path: Path) -> None:
    """A crop under 80 px gets its row like any other (the operator, 28 October)
    and is counted for the K4 report."""
    conn = db.init_db(german_store_path)
    v1 = conn.execute(
        "SELECT run_id, model FROM lines WHERE page_id = ? AND line_seq = 0", (P1,)
    ).fetchone()
    conn.execute(
        "INSERT INTO lines (line_id, page_id, line_seq, baseline, polygon, text, conf, model, "
        "run_id, status, lang) VALUES (?, ?, 5, ?, ?, 'e', 0.3, ?, ?, 'machine', 'de')",
        (
            db.line_id(P1, 5),
            P1,
            "[[100, 800], [150, 800]]",
            "[[100, 760], [150, 760], [150, 820], [100, 820]]",  # 50 px wide
            v1["model"],
            v1["run_id"],
        ),
    )
    conn.commit()
    readings = _readings(
        tmp_path / "k3.jsonl", [(f"{P1}:000", "Jch habe", 0.9), (f"{P1}:005", "n", 0.2)]
    )
    stats = I.import_readings(
        conn, readings_path=readings, page_ids=[P1], model="k3@v", reader="k3-trocr", write=True
    )
    assert stats.lines == 6 and stats.rows_written == 2
    assert stats.narrow_lines == 1 and stats.narrow_rows == 1
    assert stats.by_set["LeibnizHandschriften"]["narrow_lines"] == 1
    assert stats.as_dict()["narrow_px"] == I.NARROW_PX == 80
    assert "crops under 80 px: 1 lines, 1 of them with a row" in " ".join(I.summary_lines(stats))
    row = conn.execute(
        "SELECT text FROM lines WHERE page_id = ? AND line_seq = 5 AND run_id = ?",
        (P1, stats.run_id),
    ).fetchone()
    assert row["text"] == "n"


def test_cli_import_readings(german_store_path: Path, tmp_path: Path) -> None:
    readings = _readings(tmp_path / "k3.jsonl", [(f"{P1}:000", "Jch habe", 0.9)])
    pages = tmp_path / "pages.txt"
    pages.write_text(f"{P1}\n{Q1}\n", encoding="utf-8")
    args = [
        "pipeline",
        "import-readings",
        "--db",
        str(german_store_path),
        "--readings",
        str(readings),
        "--pages",
        str(pages),
        "--model",
        "k3-trocr@runs-615-epoch-5",
        "--reader",
        "k3-trocr",
        "--summary",
        str(tmp_path / "summary.json"),
    ]
    res = CliRunner().invoke(app, args)
    assert res.exit_code == 0, res.output
    assert "dry run" in res.output
    assert json.loads((tmp_path / "summary.json").read_text())["rows_written"] == 1
    conn = db.connect(german_store_path)
    assert conn.execute("SELECT COUNT(*) FROM runs WHERE scope = 'de'").fetchone()[0] == 0
    conn.close()
    res = CliRunner().invoke(app, [*args, "--write", "--note", "the test"])
    assert res.exit_code == 0, res.output
    assert "WRITE" in res.output and "under run" in res.output
    conn = db.connect(german_store_path)
    assert conn.execute("SELECT COUNT(*) FROM runs WHERE scope = 'de'").fetchone()[0] == 1
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM lines WHERE lang = 'de' AND model LIKE 'k3%'"
        ).fetchone()[0]
        == 1
    )
