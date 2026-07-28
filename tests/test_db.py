"""Tests for the SQLite store: schema init, id scheme, and works/pages helpers.

Runs entirely against a temp DB (or ``:memory:``); no network, no fixtures.
"""

from __future__ import annotations

import sqlite3

import pytest

from leibniz import db


def test_init_db_is_idempotent(tmp_path) -> None:
    path = tmp_path / "inventory.sqlite"
    conn = db.init_db(path)
    conn.close()
    # Second call on an existing store must not raise and must keep the schema.
    conn = db.init_db(path)
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in db.TABLE_NAMES:
        assert table in names
    conn.close()


def test_foreign_keys_enabled() -> None:
    conn = db.init_db(":memory:")
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


def test_page_and_line_id_scheme() -> None:
    # SPECS §4.4: page = "{object}:{seq:04d}", line = page + ":{line_seq:03d}".
    assert db.page_id("00068642", 7) == "00068642:0007"
    assert db.line_id("00068642:0007", 12) == "00068642:0007:012"


def test_work_roundtrip() -> None:
    conn = db.init_db(":memory:")
    work = db.Work(
        gwlb_object_id="00068642",
        set_name="LeibnizHandschriften",
        title="A quarto convolute",
        shelfmarks=["LH XXXV, 3, 5", "LH XXXV, 3, 6"],
        metadata={"language": "la", "genre": "manuscript"},
        manifest_url="https://digitale-sammlungen.gwlb.de/content/00068642/manifest.json",
        n_canvases=42,
    )
    db.upsert_work(conn, work)

    got = db.get_work(conn, "00068642")
    assert got == work  # dataclass equality, incl. parsed JSON fields
    assert db.count_works(conn) == 1
    assert db.get_work(conn, "does-not-exist") is None
    conn.close()


def test_work_upsert_updates_in_place() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften", title="old"))
    db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften", title="new"))
    assert db.count_works(conn) == 1
    assert db.get_work(conn, "00068642").title == "new"
    conn.close()


def test_page_roundtrip_and_derived_id() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften"))
    page = db.Page(
        work_id="00068642",
        seq=7,
        canvas_id="canvas-7",
        image_service_url="https://digitale-sammlungen.gwlb.de/iiif/00068642/00000007",
        width=2008,
        height=2561,
    )
    assert page.id == "00068642:0007"
    db.upsert_page(conn, page)

    got = db.get_page(conn, "00068642:0007")
    assert got == page
    assert got.status == "pending"  # default
    assert db.count_pages(conn) == 1
    conn.close()


def test_pages_for_work_are_ordered() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften"))
    for seq in (3, 1, 2):
        db.upsert_page(conn, db.Page(work_id="00068642", seq=seq))
    pages = db.get_pages(conn, "00068642")
    assert [p.seq for p in pages] == [1, 2, 3]
    conn.close()


def test_page_status_check_constraint() -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften"))
    with pytest.raises(sqlite3.IntegrityError):
        db.upsert_page(conn, db.Page(work_id="00068642", seq=1, status="bogus"))
    conn.close()


def test_page_foreign_key_enforced() -> None:
    conn = db.init_db(":memory:")
    # No such work -> FK violation on the page insert.
    with pytest.raises(sqlite3.IntegrityError):
        db.upsert_page(conn, db.Page(work_id="missing", seq=1))
    conn.close()


def test_open_db_context_manager(tmp_path) -> None:
    path = tmp_path / "inventory.sqlite"
    with db.open_db(path) as conn:
        db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften"))
    # Reopen: the commit on context exit persisted the row.
    with db.open_db(path) as conn:
        assert db.count_works(conn) == 1
