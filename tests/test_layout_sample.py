"""The census sample (offline, on the fixture store)."""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from tests.conftest import W1, W2

from leibniz import db
from leibniz.layout import sample as S


def _cand(
    pid: str, work: str, lang: str | None = None, set_name: str = "LeibnizHandschriften"
) -> S.Candidate:
    work_, _, seq = pid.partition(":")
    return S.Candidate(
        pid, work, int(seq), set_name, ["LH 1, 1"], "1r", 100, 100, f"{work}/{seq}.jpg", lang
    )


def test_file_names() -> None:
    assert S.file_name("00068371:0219") == "00068371_0219.jpg"
    assert S.file_name("DE-611-HS-971383:0035") == "DE-611-HS-971383_0035.jpg"
    assert S.page_id_of("DE-611-HS-971383_0035.jpg") == "DE-611-HS-971383:0035"
    assert S.page_id_of("x/00068371_0219") == "00068371:0219"


def test_allocate_largest_remainder() -> None:
    assert S.allocate({"la": 60, "fr": 30, "mixed": 10}, 10) == {"la": 6, "fr": 3, "mixed": 1}
    assert S.allocate({"la": 2, "fr": 1000}, 10) == {"la": 0, "fr": 10}  # the remainder decides
    assert S.allocate({"la": 1, "fr": 1}, 10) == {"la": 1, "fr": 1}  # never more than there is
    assert S.allocate({"la": 1, "fr": 1, "de": 1}, 2) == {"de": 1, "fr": 1, "la": 0}  # ties by key
    assert S.allocate({}, 5) == {} and S.allocate({"la": 3}, 0) == {"la": 0}


def test_round_robin_spreads_over_works() -> None:
    cands = [_cand(f"A:{i:04d}", "A") for i in range(10)] + [
        _cand(f"B:{i:04d}", "B") for i in range(2)
    ]
    cands += [_cand("C:0001", "C")]
    got = S.round_robin(cands, 5, random.Random(0))
    assert len(got) == 5
    works = [c.work_id for c in got]
    assert works[:3].count("A") == 1 and works[:3].count("B") == 1 and works[:3].count("C") == 1
    assert works.count("A") == 2 and works.count("B") == 2  # the second round
    assert len(S.round_robin(cands, 100, random.Random(0))) == 13  # the pool runs out
    assert S.round_robin(cands, 5, random.Random(1)) == S.round_robin(cands, 5, random.Random(1))


def test_draw_on_the_fixture_store(store_path: Path, tmp_path: Path) -> None:
    conn = db.connect(store_path)
    conn.execute("UPDATE pages SET local_path = work_id || '/' || printf('%04d', seq) || '.jpg'")
    conn.commit()
    plan = S.SamplePlan(n_strata=4, n_lh35=1, n_marginalien=2, marginalien_german=1, seed=0)
    rows, notes = S.draw(conn, plan)
    blocks = {r.block for r in rows}
    assert blocks == {"briefwechsel", "handschriften"}  # no LH 35, no Marginalien in the fixture
    assert notes["blocks"]["lh35"]["drawn"] == 0 and notes["blocks"]["marginalien"]["drawn"] == 0
    assert notes["blocks"]["handschriften"]["pool_pages"] == 2  # W1's two recognised pages
    assert [r.page_id for r in rows if r.block == "briefwechsel"] == [f"{W2}:0001"]
    hand = [r for r in rows if r.block == "handschriften"]
    assert (
        len(hand) == 2 and all(r.work_id == W1 for r in hand) and all(r.n_lines > 0 for r in hand)
    )
    # exclusions and named blocks
    plan2 = S.SamplePlan(
        n_strata=4,
        n_lh35=0,
        n_marginalien=0,
        seed=0,
        exclude={f"{W1}:0001"},
        named={"extra": [f"{W1}:0001", "nope:0001"]},
    )
    rows2, notes2 = S.draw(conn, plan2)
    assert [r.page_id for r in rows2 if r.block == "handschriften"] == [f"{W1}:0002"]
    assert [r.page_id for r in rows2 if r.block == "extra"] == [f"{W1}:0001"]
    assert notes2["named_missing"] == ["extra:nope:0001"] and notes2["excluded"] == 1
    # the CSV round-trips and the scans link under the sample names
    csv_path = tmp_path / "sample.csv"
    S.write_sample(rows2, csv_path)
    back = S.read_sample(csv_path)
    assert [(r.page_id, r.block, r.file) for r in back] == [
        (r.page_id, r.block, r.file) for r in rows2
    ]
    root = tmp_path / "images"
    for r in rows2:
        (root / r.local_path).parent.mkdir(parents=True, exist_ok=True)
        (root / r.local_path).write_bytes(b"jpg")
    (root / rows2[0].local_path).unlink()
    made, missing = S.link_images(rows2, root, tmp_path / "linked")
    assert made == len(rows2) - 1 and missing == [rows2[0].page_id]
    assert (tmp_path / "linked" / rows2[1].file).is_symlink()
    made, missing = S.link_images(rows2[1:], root, tmp_path / "copied", copy=True)
    assert made == len(rows2) - 1 and (tmp_path / "copied" / rows2[1].file).read_bytes() == b"jpg"


def test_marginalien_language_quotas() -> None:
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    db.init_db(":memory:")  # the schema helper needs a path; build the tables by hand instead
    conn.executescript(
        """
        CREATE TABLE works (gwlb_object_id TEXT PRIMARY KEY, set_name TEXT, shelfmarks TEXT);
        CREATE TABLE pages (page_id TEXT PRIMARY KEY, work_id TEXT, seq INTEGER, label TEXT,
                            width INTEGER, height INTEGER, status TEXT, local_path TEXT);
        CREATE TABLE page_lang (page_id TEXT PRIMARY KEY, lang TEXT);
        CREATE TABLE lines (page_id TEXT, line_seq INTEGER);
        CREATE TABLE runs (run_id INTEGER PRIMARY KEY, stage TEXT, scope TEXT);
        """
    )
    for w in range(6):
        conn.execute(
            "INSERT INTO works VALUES (?, 'LeibnizMarginalien', ?)", (f"M{w}", '["Leibn. Marg. 1"]')
        )
        for s in range(4):
            pid = f"M{w}:{s:04d}"
            lang = "de" if w < 2 else ("la" if s % 2 else "fr")
            conn.execute(
                "INSERT INTO pages VALUES (?, ?, ?, '1r', 10, 10, 'recognized', ?)",
                (pid, f"M{w}", s, f"M{w}/{s}.jpg"),
            )
            conn.execute("INSERT INTO page_lang VALUES (?, ?)", (pid, lang))
            conn.execute("INSERT INTO lines VALUES (?, 0)", (pid,))
    rows, notes = S.draw(
        conn, S.SamplePlan(n_strata=0, n_lh35=0, n_marginalien=6, marginalien_german=2, seed=3)
    )
    marg = [r for r in rows if r.block == "marginalien"]
    assert len(marg) == 6 and sum(1 for r in marg if r.sub == "de") == 2
    assert notes["blocks"]["marginalien"]["quotas"] == {
        "de": 2,
        "la": 2,
        "fr": 2,
        "mixed": 0,
        "unknown": 0,
    }
    assert all(r.work_id.startswith("M") for r in marg)
    assert len({r.work_id for r in marg if r.sub == "de"}) == 2  # one page a work first


def test_downscale_images(tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    from PIL import Image

    root = tmp_path / "cache"
    (root / "W").mkdir(parents=True)
    Image.new("RGB", (4000, 3000), (200, 200, 200)).save(root / "W" / "0001.jpg")
    Image.new("RGB", (800, 1000), (10, 10, 10)).save(root / "W" / "0002.jpg")
    rows = [
        S.SamplePage(
            "W:0001", "lh35", "", "W", "s", "", "1r", 4000, 3000, 1, "W/0001.jpg", "W_0001.jpg"
        ),
        S.SamplePage(
            "W:0002", "lh35", "", "W", "s", "", "1v", 800, 1000, 1, "W/0002.jpg", "W_0002.jpg"
        ),
        S.SamplePage(
            "W:0003", "lh35", "", "W", "s", "", "2r", 10, 10, 1, "W/0003.jpg", "W_0003.jpg"
        ),
    ]
    dest = tmp_path / "small"
    written, present, missing = S.downscale_images(rows, root, dest, long_side=1600)
    assert (written, present, missing) == (2, 0, ["W:0003"])
    with Image.open(dest / "W_0001.jpg") as im:
        assert im.size == (1600, 1200)  # 4000×3000 → the long side 1600
    with Image.open(dest / "W_0002.jpg") as im:
        assert im.size == (800, 1000)  # already smaller: copied as it is
    assert S.downscale_images(rows, root, dest, long_side=1600) == (0, 2, ["W:0003"])
