"""Scans registered twice (twins) and spreads: the rule, the index, the site."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from leibniz import db
from leibniz.images import twins
from leibniz.images.twins import Registration, TwinIndex
from leibniz.search.documents import iter_page_docs
from leibniz.web.api import create_app

LBR = "DE-611-HS-9000001"  # a letter convolute whose outer side is registered as 1r and 2v
W, H = 3000, 2000  # a landscape image: two folio pages side by side

LEFT = [(100, 1300, "Monsieur, j'ay receu la vostre")]  # the verso: 2v
RIGHT = [(1700, 2900, "Hannover ce 3 de Mars 1690")]  # the recto: 1r


def _reg(pid: str, label: str, n_bytes: int, *, w: int = W, h: int = H) -> Registration:
    return Registration(pid, "X", int(pid.rsplit(":", 1)[1]), label, w, h, n_bytes)


def _line(page_id: str, seq: int, x0: int, x1: int, y: int, text: str) -> db.Line:
    return db.Line(
        page_id=page_id,
        line_seq=seq,
        polygon=[[x0, y - 30], [x1, y - 30], [x1, y + 20], [x0, y + 20]],
        baseline=[[x0, y], [x1, y]],
        text=text,
        conf=0.9,
        model="htr@v1",
        run_id=1,
        status="machine",
        lang="fr",
    )


def _side_lines(page_id: str, rows: int = 4, *, across: int = 0) -> list[db.Line]:
    """``rows`` lines on each half, the same on every registration, and
    ``across`` lines the segmenter ran over the fold."""
    out: list[db.Line] = []
    seq = 0
    for r in range(rows):
        y = 200 + r * 120
        for x0, x1, text in (*LEFT, *RIGHT):
            out.append(_line(page_id, seq, x0, x1, y, f"{text} {r}"))
            seq += 1
    for r in range(across):
        out.append(_line(page_id, seq, 900, 2100, 1500 + r * 100, f"across {r}"))
        seq += 1
    return out


# ---- the rule ------------------------------------------------------------------ #


def test_leaf_side() -> None:
    assert twins.leaf_side("12r") == "r" and twins.leaf_side("3 v") == "v"
    assert twins.leaf_side("1r-2v") is None and twins.leaf_side("S. 12") is None
    assert twins.leaf_side(None) is None and twins.leaf_side("1ra") is None


def test_candidates_need_size_bytes_and_a_recto_and_a_verso() -> None:
    a, b = _reg("X:0001", "1r", 1_000_000), _reg("X:0004", "2v", 1_000_400)
    assert twins.candidate_groups([a, b]) == [(a, b)]
    # the same side twice, too far apart in bytes, another size: none of them
    assert twins.candidate_groups([a, _reg("X:0002", "1v", 1_000_100)]) == [
        (a, _reg("X:0002", "1v", 1_000_100))
    ]
    assert twins.candidate_groups([a, _reg("X:0003", "3r", 1_000_100)]) == []
    assert twins.candidate_groups([a, _reg("X:0004", "2v", 1_016_000)]) == []
    assert twins.candidate_groups([a, _reg("X:0004", "2v", 1_000_100, w=2999)]) == []
    # no window: a partner 29 canvases away is still a partner
    far = _reg("X:0030", "14v", 1_000_200)
    assert twins.candidate_groups([a, far]) == [(a, far)]


def test_closest_sizes_pair_first_and_a_third_registration_joins() -> None:
    a = _reg("X:0001", "1r", 1_000_000)
    b = _reg("X:0002", "2v", 1_000_050)
    c = _reg("X:0003", "3v", 1_000_900)
    d = _reg("X:0009", "9r", 2_000_000)
    e = _reg("X:0010", "10v", 2_000_010)
    groups = twins.candidate_groups([c, a, d, b, e])
    assert groups == [(a, b, c), (d, e)]


def test_fold_is_the_empty_gutter_or_the_middle() -> None:
    found = twins.boxes(_side_lines("X:0001"))
    assert 1300 <= twins.find_fold(found, W) <= 1700
    crossed = twins.boxes(_side_lines("X:0001", across=3))
    assert twins.find_fold(crossed, W) == W // 2  # three lines cross the whole band
    assert twins.find_fold([], W) in range(1200, 1801)


def test_a_line_crosses_with_a_fifth_on_each_side() -> None:
    box = twins.Box(0, 1000, 0, 1000, 50)
    assert twins.crosses(box, 1500) and twins.crosses(box, 1200)
    assert not twins.crosses(box, 1150) and not twins.crosses(box, 1900)


def test_a_spread_is_split_verso_left_recto_right() -> None:
    r, v = _reg("X:0001", "1r", 1_000_000), _reg("X:0002", "2v", 1_000_300)
    lines = {"X:0001": _side_lines("X:0001"), "X:0002": _side_lines("X:0002")}
    group = twins.decide((r, v), lines)
    assert group is not None and group.kind == "spread"
    assert (group.left, group.right) == ("X:0002", "X:0001")
    left = [ln.text for ln, _ in group.own_lines("X:0002", lines["X:0002"])]
    right = [ln.text for ln, _ in group.own_lines("X:0001", lines["X:0001"])]
    assert left and all(t.startswith("Monsieur") for t in left)
    assert right and all(t.startswith("Hannover") for t in right)
    assert group.n_lines == {"X:0001": 4, "X:0002": 4} == group.n_once


def test_a_line_across_the_fold_shows_on_both_halves_and_counts_once() -> None:
    r, v = _reg("X:0001", "1r", 1_000_000), _reg("X:0002", "2v", 1_000_300)
    lines = {pid: _side_lines(pid, rows=12, across=1) for pid in ("X:0001", "X:0002")}
    group = twins.decide((r, v), lines)
    assert group is not None and group.kind == "spread"
    shown_left = group.own_lines("X:0002", lines["X:0002"])
    assert [t for ln, t in shown_left if t] and any(ln.text == "across 0" for ln, _ in shown_left)
    indexed_left = group.own_lines("X:0002", lines["X:0002"], for_index=True)
    assert all(ln.text != "across 0" for ln, _ in indexed_left)
    assert group.n_lines["X:0002"] == 13 and group.n_once["X:0002"] == 12
    assert group.n_once["X:0001"] == 13


def test_too_many_lines_across_the_fold_fold_the_group() -> None:
    r, v = _reg("X:0001", "1r", 1_000_000), _reg("X:0002", "2v", 1_000_300)
    lines = {pid: _side_lines(pid, rows=2, across=3) for pid in ("X:0001", "X:0002")}
    group = twins.decide((r, v), lines)
    assert group is not None and group.kind == "fold" and "across the fold" in group.reason
    assert group.carries_text(group.primary) and group.n_once[group.primary] == 7
    other = next(p for p in group.pages if p != group.primary)
    assert not group.carries_text(other) and group.n_once[other] == 0


def test_triples_and_upright_images_are_folded() -> None:
    regs = (
        _reg("X:0001", "1r", 1_000_000),
        _reg("X:0002", "2v", 1_000_300),
        _reg("X:0003", "3v", 1_000_500),
    )
    lines = {r.page_id: _side_lines(r.page_id) for r in regs}
    triple = twins.decide(regs, lines)
    assert triple is not None and triple.kind == "fold" and "3 times" in triple.reason
    upright = twins.decide(
        (_reg("X:0001", "1r", 10, w=H, h=W), _reg("X:0002", "2v", 10, w=H, h=W)), lines
    )
    assert upright is not None and upright.kind == "fold" and "upright" in upright.reason


def test_nothing_is_folded_on_file_sizes_alone() -> None:
    r, v = _reg("X:0001", "1r", 1_000_000), _reg("X:0002", "2v", 1_000_300)
    other = [_line("X:0002", 0, 400, 800, 1200, "quite another page")]
    assert twins.decide((r, v), {"X:0001": _side_lines("X:0001"), "X:0002": other}) is None
    assert twins.decide((r, v), {"X:0001": [], "X:0002": []}) is None
    assert twins.decide((r, v), {"X:0001": _side_lines("X:0001"), "X:0002": []}) is None


def test_the_file_round_trips_and_a_missing_one_is_empty(tmp_path: Path) -> None:
    r, v = _reg("X:0001", "1r", 1_000_000), _reg("X:0002", "2v", 1_000_300)
    lines = {pid: _side_lines(pid) for pid in ("X:0001", "X:0002")}
    group = twins.decide((r, v), lines)
    path = TwinIndex([group], {"groups": 1}, "2026-10-10T00:00:00Z").write(tmp_path / "t.json")
    back = TwinIndex.load(path)
    assert back.get("X:0002") == group and back.stats == {"groups": 1}
    assert not TwinIndex.load(tmp_path / "missing.json") and not TwinIndex.load(None)
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    assert not TwinIndex.load(tmp_path / "bad.json")


def test_where_the_file_goes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(twins.TWINS_ENV, raising=False)
    store = Path("/var/lib/x/inventory.sqlite")
    assert twins.twins_path_for("fts5", Path("/var/lib/x/search.sqlite"), store, "u") == Path(
        "/var/lib/x/search.twins.json"
    )
    assert twins.twins_path_for("meili", Path("ignored"), store, "pages_staging") == Path(
        "/var/lib/x/pages_staging.twins.json"
    )
    monkeypatch.setenv(twins.TWINS_ENV, "/tmp/elsewhere.json")
    assert twins.twins_path_for("meili", Path("x"), store, "u") == Path("/tmp/elsewhere.json")


# ---- the store, the index and the site ------------------------------------------- #


def _add_letters(store_path: Path, *, rows: int = 4, across: int = 0, third: bool = False) -> None:
    """A letter convolute: canvas 1 (1r) and canvas 2 (2v) are one scan of the
    outer side; canvas 3 (1v) is a page of its own."""
    conn = db.connect(store_path)
    db.upsert_work(
        conn,
        db.Work(LBR, "LeibnizBriefwechsel", title="LBr. 999", shelfmarks=["LBr. 999"]),
    )
    pages = [(1, "1r", 1_200_000), (2, "2v", 1_200_350), (3, "1v", 1_300_000)]
    if third:
        pages.append((4, "3v", 1_200_500))
    for seq, label, n_bytes in pages:
        page = db.Page(
            work_id=LBR,
            seq=seq,
            label=label,
            width=W,
            height=H,
            image_url=f"https://example.test/{seq}.jpg",
            delivery="static",
            status="recognized",
        )
        db.upsert_page(conn, page)
        conn.execute("UPDATE pages SET n_bytes = ? WHERE page_id = ?", (n_bytes, page.id))
        lines = (
            _side_lines(page.id, rows=rows, across=across)
            if seq != 3
            else [_line(page.id, 0, 300, 2600, 900, "a page of its own")]
        )
        for ln in lines:
            db.insert_line(conn, ln)
    conn.commit()
    conn.close()


def test_the_index_holds_each_half_once(store_path: Path) -> None:
    _add_letters(store_path)
    conn = db.connect(store_path)
    found: list[twins.TwinGroup] = []
    stats = twins.TwinStats()
    docs = {d.page_id: d for d in iter_page_docs(conn, twins_out=found, twin_stats=stats)}
    conn.close()
    assert [g.kind for g in found] == ["spread"] and stats.spreads == 1
    assert stats.second_registrations == 1
    verso, recto = docs[f"{LBR}:0002"], docs[f"{LBR}:0001"]
    assert verso.n_lines == 4 and "Monsieur" in verso.text and "Hannover" not in verso.text
    assert recto.n_lines == 4 and "Hannover" in recto.text and "Monsieur" not in recto.text
    assert docs[f"{LBR}:0003"].text == "a page of its own"


def test_a_fold_is_indexed_on_one_page_naming_the_others(store_path: Path) -> None:
    _add_letters(store_path, third=True)
    conn = db.connect(store_path)
    found: list[twins.TwinGroup] = []
    docs = {d.page_id: d for d in iter_page_docs(conn, twins_out=found)}
    conn.close()
    assert [g.kind for g in found] == ["fold"]
    primary = found[0].primary
    assert sorted(docs[primary].also) == ["2v", "3v"] and "fol 3v" in docs[primary].meta_text()
    assert {f"{LBR}:0002", f"{LBR}:0004"}.isdisjoint(docs)


def test_find_twins_writes_what_the_index_build_finds(store_path: Path, tmp_path: Path) -> None:
    _add_letters(store_path)
    conn = db.connect(store_path)
    found = twins.find_twins(conn)
    conn.close()
    assert found.stats["spreads"] == 1 and found.stats["candidates"] == 1
    assert found.get(f"{LBR}:0001").side(f"{LBR}:0001") == "right"
    assert "1 spreads split" in twins.render_report(found)


def _app(store_path: Path, tmp_path: Path) -> TestClient:
    conn = db.connect(store_path)
    path = twins.find_twins(conn).write(tmp_path / "twins.json")
    conn.close()
    return TestClient(create_app(store_path, search=None, static_dir=None, twins_path=path))


def test_a_spread_page_shows_its_half(store_path: Path, tmp_path: Path) -> None:
    _add_letters(store_path, rows=12, across=1)  # one line in 25 across the fold
    c = _app(store_path, tmp_path)
    verso = c.get(f"/api/pages/{LBR}:0002").json()
    texts = [ln["text"] for ln in verso["lines"]]
    assert all(not t.startswith("Hannover") for t in texts) and "across 0" in texts
    assert [ln["crosses_fold"] for ln in verso["lines"]].count(True) == 1
    assert verso["twin"]["kind"] == "spread" and verso["twin"]["side"] == "left"
    assert verso["twin"]["others"] == [{"page_id": f"{LBR}:0001", "label": "1r"}]
    assert 1300 <= verso["twin"]["fold_x"] <= 1700
    assert verso["stats"]["n_lines"] == 13
    work = c.get(f"/api/works/{LBR}").json()
    counts = {p["label"]: p["n_lines"] for p in work["pages"]}
    assert counts == {"1r": 13, "2v": 13, "1v": 1}
    assert work["pages"][2].get("twin") is None
    ann = c.get(f"/annotations/{LBR}:0001").json()
    assert all(not a["body"]["value"].startswith("Monsieur") for a in ann["items"])


def test_exports_give_each_line_once(store_path: Path, tmp_path: Path) -> None:
    _add_letters(store_path, rows=12, across=1)
    c = _app(store_path, tmp_path)
    page = c.get(f"/api/pages/{LBR}:0002/text").text
    assert "# Scan: One image of two folio pages side by side" in page
    assert "left half" in page and "Hannover" not in page
    work = c.get(f"/api/works/{LBR}/text").text
    body = [row for row in work.splitlines() if row and not row.startswith("#")]
    assert len(body) == 12 + 13 + 1  # verso half, recto half with the line across, page 1v
    assert body.count("across 0") == 1
    assert "# Lines: 26 recognised on 3 of 3 pages" in work


def test_a_fold_exports_its_text_once_and_points_to_it(store_path: Path, tmp_path: Path) -> None:
    _add_letters(store_path, third=True)
    c = _app(store_path, tmp_path)
    work = c.get(f"/api/works/{LBR}/text").text
    assert work.count("Monsieur, j'ay receu la vostre 0") == 1
    assert "# The same scan as fol. 1r" in work
    secondary = c.get(f"/api/pages/{LBR}:0004").json()
    assert secondary["twin"]["kind"] == "fold" and secondary["twin"]["is_primary"] is False
    assert secondary["stats"]["n_lines"] == 8  # the page still shows its own reading


def test_without_a_twins_file_every_page_is_its_own(store_path: Path) -> None:
    _add_letters(store_path)
    c = TestClient(create_app(store_path, search=None, static_dir=None, twins_path=None))
    verso = c.get(f"/api/pages/{LBR}:0002").json()
    assert verso["twin"] is None and verso["stats"]["n_lines"] == 8


def test_the_index_build_writes_the_twins_and_counts_each_scan_once(
    store_path: Path, tmp_path: Path
) -> None:
    from typer.testing import CliRunner

    from leibniz.cli import app
    from leibniz.search.fts5 import Fts5Backend

    _add_letters(store_path)
    index = tmp_path / "search.sqlite"
    runner = CliRunner()
    r = runner.invoke(app, ["index", "build", "--db", str(store_path), "--index", str(index)])
    assert r.exit_code == 0, r.stdout
    assert "1 confirmed (1 spreads, 0 folded)" in r.stdout
    written = TwinIndex.load(tmp_path / "search.twins.json")
    assert written.stats["spreads"] == 1 and written.get(f"{LBR}:0002") is not None
    stats = Fts5Backend(index).meta()["stats"]
    assert stats["scans"] == stats["pages"] - 1  # 2v is a second registration of 1r's scan
    assert stats["lines_once"] == 7 + 4 + 4 + 1  # the fixture's 7 lines, the halves, page 1v
    assert stats["twins"]["second_registrations"] == 1
    # what the About page reads: the figures reach /api/stats beside the image origin,
    # which has had the key "images" since the mirror (the first draft wrote its
    # count there, and /api/stats overwrote it)
    app_ = create_app(
        store_path,
        search=Fts5Backend(index),
        static_dir=None,
        twins_path=tmp_path / "search.twins.json",
    )
    served = TestClient(app_).get("/api/stats").json()
    assert served["scans"] == stats["scans"] and served["lines_once"] == stats["lines_once"]
    assert served["twins"]["second_registrations"] == 1
    assert served["images"]["origin"] == "gwlb"
    # a partial build leaves the file alone
    (tmp_path / "search.twins.json").unlink()
    args = ["index", "build", "--db", str(store_path), "--index", str(index), "--work", LBR]
    r = runner.invoke(app, args)
    assert r.exit_code == 0 and "partial build" in r.stdout
    assert not (tmp_path / "search.twins.json").exists()


def test_images_twins_command(store_path: Path, tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from leibniz.cli import app

    _add_letters(store_path)
    out, report = tmp_path / "t.json", tmp_path / "twins.md"
    args = ["images", "twins", "--db", str(store_path), "--out", str(out), "--report", str(report)]
    r = CliRunner().invoke(app, args)
    assert r.exit_code == 0, r.stdout
    assert TwinIndex.load(out).stats["groups"] == 1 and "1 spreads split" in report.read_text()
