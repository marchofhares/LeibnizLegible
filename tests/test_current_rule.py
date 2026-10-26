"""The one precedence every reader of ``lines`` uses (K4, Task 2), on fixtures.

A run scoped to a language (K4's Kurrent run, ``de``) wins on the lines it
read over every unscoped run, whatever their age; a line the scoped run did
not write shows the newest unscoped row; a corrections run (the crowd
judgments) outranks both; among runs of one kind the newest wins, as before.
Every reader — ``latest_lines``, the SQL probe, the index documents, the API,
the export, the stats, the judgments importer — must agree.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tests.conftest import W1, W2

from leibniz import db
from leibniz.pack import judgments
from leibniz.release.export import iter_transcriptions
from leibniz.search.documents import (
    corpus_stats,
    iter_page_docs,
    latest_lines,
    line_summaries_by_page,
    page_lang_of,
)

P1, P2, Q1 = f"{W1}:0001", f"{W1}:0002", f"{W2}:0001"


def _geometry(conn: sqlite3.Connection, page_id: str, seq: int) -> tuple[list, list]:
    row = conn.execute(
        "SELECT baseline, polygon FROM lines WHERE page_id = ? AND line_seq = ? LIMIT 1",
        (page_id, seq),
    ).fetchone()
    return json.loads(row["baseline"]), json.loads(row["polygon"])


def _add_row(
    conn: sqlite3.Connection,
    page_id: str,
    seq: int,
    *,
    run: int,
    text: str,
    conf: float,
    model: str,
    status: str = "machine",
    lang: str | None = None,
) -> None:
    baseline, polygon = _geometry(conn, page_id, seq)
    db.insert_line(
        conn,
        db.Line(
            page_id=page_id,
            line_seq=seq,
            baseline=baseline,
            polygon=polygon,
            text=text,
            conf=conf,
            model=model,
            run_id=run,
            status=status,
            lang=lang,
        ),
    )


def _scoped_store(store_path: Path) -> tuple[sqlite3.Connection, int, int]:
    """The fixture store with a German run on page 1 of W1 (lines 0 and 2, not
    1) written BEFORE a newer unscoped v3 run that re-reads line 0 of page 1
    and line 0 of Q1."""
    conn = db.connect(store_path)
    de = db.start_run(conn, "recognize", model="k3-trocr@runs-615-epoch-5", scope="de")
    _add_row(conn, P1, 0, run=de, text="Calculemus sagt Leibniz", conf=0.8, model="k3", lang="de")
    _add_row(conn, P1, 2, run=de, text="was vorhergieng", conf=0.7, model="k3", lang="de")
    v3 = db.start_run(conn, "recognize", model="leibniz-htr-v3@v3")
    _add_row(conn, P1, 0, run=v3, text="Calculemus inquit Leibnitius!", conf=0.97, model="v3")
    _add_row(conn, Q1, 0, run=v3, text="La Monadologie, et les principes", conf=0.93, model="v3")
    db.finish_run(conn, de, n_input=2, n_ok=2, n_failed=0)
    db.finish_run(conn, v3, n_input=2, n_ok=2, n_failed=0)
    conn.commit()
    return conn, de, v3


def test_migration_adds_runs_scope_and_the_page_lang_table(tmp_path: Path) -> None:
    path = tmp_path / "old.sqlite"
    conn = db.connect(path)
    conn.executescript(
        "CREATE TABLE runs (run_id INTEGER PRIMARY KEY, stage TEXT NOT NULL, model TEXT, "
        "params TEXT, started_at TEXT, finished_at TEXT, n_input INTEGER, n_ok INTEGER, "
        "n_failed INTEGER, git_sha TEXT);"
    )
    conn.commit()
    conn.close()
    conn = db.init_db(path)
    assert "scope" in {r[1] for r in conn.execute("PRAGMA table_info(runs)")}
    assert conn.execute("SELECT COUNT(*) FROM page_lang").fetchone()[0] == 0
    conn.close()
    db.init_db(path).close()  # idempotent


def test_run_precedence() -> None:
    assert db.run_precedence("recognize", None) == 0
    assert db.run_precedence("recognize", "de") == 1
    assert db.run_precedence("crowd", None) == 2
    assert db.run_precedence("crowd", "de") == 2


def test_scoped_run_wins_over_a_newer_unscoped_one_per_line(store_path: Path) -> None:
    conn, de, v3 = _scoped_store(store_path)
    assert db.run_precedences(conn) == {de: 1}
    lines = latest_lines(conn, P1)
    assert [(ln.line_seq, ln.run_id) for ln in lines] == [(0, de), (1, 2), (2, de)]
    assert lines[0].text == "Calculemus sagt Leibniz" and lines[0].lang == "de"
    assert lines[1].text == "de arte combinatoria <b>"  # the line the German run did not write
    # the unscoped page follows the newest run as before
    assert latest_lines(conn, Q1)[0].run_id == v3
    # a citation pinned to a run before the German one reads the page as it was
    pinned = latest_lines(conn, P1, as_of_run=3)
    assert [ln.run_id for ln in pinned] == [3, 2, 2]
    assert pinned[0].text == "Calculemus inquit Leibnitius."


def test_corrections_outrank_the_scoped_run(store_path: Path) -> None:
    conn, de, _v3 = _scoped_store(store_path)
    crowd = db.start_run(conn, "crowd", model="calculemus@abc")
    _add_row(conn, P1, 0, run=crowd, text="Calculemus, sagt Leibniz.", conf=1.0, model="c")
    conn.execute("UPDATE lines SET status = 'corrected' WHERE run_id = ?", (crowd,))
    conn.commit()
    assert db.run_precedences(conn) == {de: 1, crowd: 2}
    assert latest_lines(conn, P1)[0].text == "Calculemus, sagt Leibniz."
    # the importer's view of the machine row is the scoped one, not the newest
    row = judgments.machine_row(conn, P1, 0)
    assert row["run_id"] == de and row["text"] == "Calculemus sagt Leibniz"


def test_the_probe_matches_the_python_rule(store_path: Path) -> None:
    conn, _de, _v3 = _scoped_store(store_path)
    for work in (W1, W2):
        got = line_summaries_by_page(conn, work)
        for page in db.get_pages(conn, work):
            lines = [ln for ln in latest_lines(conn, page.id) if ln.text]
            if not lines:
                assert page.id not in got
                continue
            confs = [ln.conf for ln in lines if ln.conf is not None]
            assert got[page.id] == (len(lines), round(sum(confs) / len(confs), 4))
    assert got[Q1] == (2, round((0.93 + 0.86) / 2, 4))


def test_export_and_stats_follow_the_rule(store_path: Path) -> None:
    conn, de, v3 = _scoped_store(store_path)
    rows = {(r["page_id"], r["line_seq"]): r for r in iter_transcriptions(conn)}
    assert rows[(P1, 0)]["run_id"] == de and rows[(P1, 0)]["lang"] == "de"
    assert rows[(P1, 1)]["run_id"] == 2
    assert rows[(P1, 2)]["run_id"] == de
    assert rows[(Q1, 0)]["run_id"] == v3
    assert len(rows) == 7
    stats = corpus_stats(conn)
    assert stats["lines"] == 7 and db.count_current_lines(conn) == 7
    assert sum(stats["conf_histogram"].values()) == 7
    assert stats["models"] == {"htr@v1": 4, "k3": 2, "v3": 1}


def test_the_index_takes_the_page_language_from_page_lang(store_path: Path) -> None:
    conn, de, _v3 = _scoped_store(store_path)
    enrich = db.start_run(conn, "enrich", model="langid")
    db.upsert_page_lang(
        conn,
        db.PageLangRow(P1, "de", score=0.8, n_tokens=12, evidence="machine", run_id=enrich),
    )
    db.upsert_page_lang(conn, db.PageLangRow(Q1, "fr", score=1.0, n_tokens=12, run_id=enrich))
    conn.commit()
    assert db.get_page_lang(conn, P1).evidence == "machine"
    assert db.get_page_lang(conn, P2) is None
    assert db.page_langs_for_work(conn, W1) == {P1: "de"}
    assert db.count_page_lang(conn) == {"de": 1, "fr": 1}
    docs = {d.page_id: d for d in iter_page_docs(conn)}
    assert docs[P1].lang == "de"  # the table's verdict
    assert docs[P2].lang == "la"  # no row: the lines' majority, as before
    assert docs[Q1].lang == "fr"
    assert docs[P1].text.startswith("Calculemus sagt Leibniz\nde arte combinatoria")
    assert page_lang_of(conn, P2, latest_lines(conn, P2)) == "la"
    assert page_lang_of(conn, P1, [], page_langs={}) == "unknown"
    # an upsert replaces the row
    db.upsert_page_lang(conn, db.PageLangRow(P1, "mixed", run_id=enrich))
    assert db.get_page_lang(conn, P1).lang == "mixed"
    assert corpus_stats(conn)["pages_by_lang"] == {"fr": 1, "mixed": 1}
