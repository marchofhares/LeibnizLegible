"""Tests for `runs` bookkeeping helpers added by the harvest stage."""

from __future__ import annotations

import re

from leibniz import db


def test_utcnow_iso_format() -> None:
    stamp = db.utcnow_iso()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp)


def test_start_and_finish_run_roundtrip() -> None:
    conn = db.init_db(":memory:")
    run_id = db.start_run(
        conn,
        "harvest_oai",
        params={"sets": ["LeibnizHandschriften"], "force": False},
        git_sha="deadbeef",
    )
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    assert row["stage"] == "harvest_oai"
    assert row["git_sha"] == "deadbeef"
    assert '"sets"' in row["params"]
    assert row["started_at"] is not None
    assert row["finished_at"] is None

    db.finish_run(conn, run_id, n_input=756, n_ok=755, n_failed=1)
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    assert (row["n_input"], row["n_ok"], row["n_failed"]) == (756, 755, 1)
    assert row["finished_at"] is not None
    conn.close()


def test_stage_runs_record_the_images_root(tmp_path) -> None:
    """The store is the only thing that remembers where the image cache lives.

    `pages.local_path` is relative to a root nothing else records, and the cache
    is too large to sit beside the store, so without this a later pass has to
    guess which disk holds 400 GB of JPEGs.
    """
    import json

    from leibniz import db

    conn = db.init_db(tmp_path / "inv.sqlite")
    for stage in ("segment", "recognize", "images_fetch"):
        db.start_run(conn, stage, params={"images_root": "/mnt/d/leibniz/images"})
    rows = conn.execute("SELECT stage, params FROM runs ORDER BY run_id").fetchall()
    assert {r["stage"] for r in rows} == {"segment", "recognize", "images_fetch"}
    for r in rows:
        assert json.loads(r["params"])["images_root"] == "/mnt/d/leibniz/images"
    conn.close()
