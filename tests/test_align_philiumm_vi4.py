"""Tests for P1 Task 2: A VI,4 under two aligners (seeded store, synthetic PAGE files)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align.pairs import GtPair, insert_gt_pairs
from leibniz.align.philiumm import vi4 as V
from leibniz.cli import app
from leibniz.net import PoliteClient

runner = CliRunner()
W = "00099001"  # LH 1, 20


def _page_xml(
    name: str, width: int, height: int, lines: list[tuple[str, int, int, int, int, str]]
) -> str:
    """A minimal PAGE file: lines as (id, x0, y0, x1, y1, text)."""
    body = "".join(
        f'<TextLine id="{lid}"><Coords points="{x0},{y0} {x1},{y0} {x1},{y1} {x0},{y1}"/>'
        f'<Baseline points="{x0},{y1 - 5} {x1},{y1 - 5}"/>'
        f'<TextEquiv conf="0.8"><Unicode>{text}</Unicode></TextEquiv></TextLine>'
        for lid, x0, y0, x1, y1, text in lines
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">'
        f'<Page imageFilename="{name}.jpg" imageWidth="{width}" imageHeight="{height}">'
        '<TextRegion id="r0" custom="structure {type:MainZone;}">'
        f'<Coords points="0,0 {width},0 {width},{height} 0,{height}"/>{body}'
        "</TextRegion></Page></PcGts>"
    )


def _seed(root: Path) -> tuple[Path, Path, Path]:
    """A store with one work (LH 1, 20), pages 62v / 63r / 64r, lines and minted text;
    a dataset cache dir with the listing and two noisy PAGE files; an image cache."""
    store, dest, images = root / "inv.sqlite", root / "philiumm", root / "images"
    conn = db.init_db(store)
    db.upsert_work(
        conn, db.Work(W, "LeibnizHandschriften", title="LH 1, 20", shelfmarks=["LH 1, 20"])
    )
    db.upsert_work(
        conn,
        db.Work("00099002", "LeibnizHandschriften", shelfmarks=["LH 1, 3, 7 A", "LH 1, 3, 7a"]),
    )
    # two works share the key LH 4,5,10: the folio is found in the second one
    db.upsert_work(conn, db.Work("00099003", "LeibnizHandschriften", shelfmarks=["LH 4, 5, 10"]))
    db.upsert_work(conn, db.Work("00099004", "LeibnizHandschriften", shelfmarks=["LH 4, 5, 10"]))
    db.upsert_page(conn, db.Page(work_id="00099003", seq=1, label="3r", status="recognized"))
    db.upsert_page(conn, db.Page(work_id="00099004", seq=1, label="48r", status="recognized"))
    from PIL import Image

    (images / W).mkdir(parents=True)
    for seq, label in ((1, "62v"), (2, "63r"), (3, "64r")):
        db.upsert_page(
            conn,
            db.Page(
                work_id=W,
                seq=seq,
                label=label,
                status="recognized",
                width=1000,
                height=1500,
                local_path=f"{W}/{seq:04d}.jpg",
            ),
        )
        Image.new("RGB", (1000, 1500), "white").save(images / W / f"{seq:04d}.jpg")
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    rec2 = db.start_run(conn, "recognize", model="htr@v2")

    def line(pid: str, seq: int, box: tuple[int, int, int, int], text: str, run: int = rec) -> None:
        x0, y0, x1, y1 = box
        db.insert_line(
            conn,
            db.Line(
                page_id=pid,
                line_seq=seq,
                polygon=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                baseline=[[x0, y1], [x1, y1]],
                run_id=seg,
                status="machine",
            ),
        )
        db.set_line_recognition(conn, pid, seq, text=text, conf=0.9, model="htr", run_id=run)

    p62, p63, p64 = f"{W}:0001", f"{W}:0002", f"{W}:0003"
    line(p62, 0, (100, 100, 900, 160), "prima linea sinistra")
    line(p62, 1, (100, 200, 900, 260), "secunda linea sinistra")
    line(p63, 0, (100, 100, 900, 160), "prima linea dextra")
    line(p63, 1, (100, 200, 900, 260), "secunda linea dextra")
    line(p63, 2, (100, 300, 900, 360), "tertia linea dextra")
    line(p64, 0, (100, 100, 900, 160), "folium sequens")
    # a later run re-read the same geometry: the census takes the latest text
    conn.execute(
        "INSERT INTO lines (line_id, page_id, line_seq, polygon, run_id, text, status) "
        "VALUES (?, ?, 0, ?, ?, ?, 'machine')",
        (
            db.line_id(p64, 0),
            p64,
            "[[100, 100], [900, 100], [900, 160], [100, 160]]",
            rec2,
            "folium sequens v2",
        ),
    )
    src = "AA VI,4 N.109 (§70-expired AA reading text; katalog k-1)"
    insert_gt_pairs(
        conn,
        [
            GtPair(f"{p62}:000", "Prima linea sinistra.", src, "fair_copy", 0.9, "open"),  # agree
            GtPair(
                f"{p62}:001", "Secunda linea, sinistra", src, "fair_copy", 0.9, "open"
            ),  # theirs blank → ours only
            GtPair(
                f"{p63}:000", "Prima linea dextra", src, "heavy_revision", 0.8, "open"
            ),  # disagree
            GtPair(
                f"{p63}:001", "Secunda linea dextra omnino", src, "heavy_revision", 0.8, "open"
            ),  # near
            GtPair(
                f"{p64}:000", "nc text", "transkriptionspool", "fair_copy", 0.8, "nc"
            ),  # nc: ignored
        ],
    )
    conn.commit()
    conn.close()

    noisy = dest / "noisy"
    noisy.mkdir(parents=True)
    # an opening: their image is the two canvases side by side (2000 × 1500), 63r named first
    # but laid out on the right (62v left): the matcher must find the order by itself
    (noisy / "LH_1_20_0063r-0062v.xml").write_text(
        _page_xml(
            "LH_1_20_0063r-0062v",
            2000,
            1500,
            [
                ("L0", 100, 100, 900, 160, "Prima linea sinistra."),
                ("L1", 100, 200, 900, 260, ""),
                ("R0", 1100, 100, 1900, 160, "Alia lectio prorsus diversa"),
                ("R1", 1100, 200, 1900, 260, "Secunda linea dextra"),
                ("R2", 1100, 300, 1900, 360, "Tertia linea dextra"),
                ("X", 1100, 1000, 1900, 1060, "a line this project never segmented"),
            ],
        ),
        encoding="utf-8",
    )
    # a single folio at half resolution: 500 × 750
    (noisy / "LH_1_20_0064r.xml").write_text(
        _page_xml("LH_1_20_0064r", 500, 750, [("S0", 50, 50, 450, 80, "Folium sequens")]),
        encoding="utf-8",
    )
    listing = {
        "dataset": V.HF_DATASET,
        "sha": "abc123def456",
        "license": "cc-by-4.0",
        "files": [
            "train/noisy/LH_1_20_0063r-0062v.xml",
            "train/noisy/LH_1_20_0063r-0062v.jpg",
            "train/noisy/LH_1_20_0064r.xml",
            "train/noisy/LH_1_20_0099r.xml",  # no such folio
            "train/noisy/LH_9_9_0001r.xml",  # no such work (no xml either)
            "train/clean/LH_1_20_0062v.xml",
            "val/0001_page_12210614_docId_307926.xml",  # unparsed
            "val/LH_1_3_7_A_0004v-0003r.xml",  # the letter-part work, no pages
            "val/LH_4_5_10_0048r.xml",  # shared key: the folio sits in the second work
            "val/LH_4_5_10_0099r.xml",  # shared key, no such folio anywhere
        ],
    }
    (dest / V.LISTING_NAME).write_text(json.dumps(listing), encoding="utf-8")
    return store, dest, images


def test_parse_name_and_candidate_keys() -> None:
    fn = V.parse_name("train/noisy/LH_1_12_2_0124r.xml", "noisy")
    assert (
        fn.parsed
        and fn.family == "LH"
        and fn.tokens == ("1", "12", "2")
        and fn.folios == [(124, "r")]
    )
    assert fn.candidate_keys()[0] == "LH 1,12,2" and not fn.is_opening
    op = V.parse_name("LH_1_20_0063r-0062v")
    assert op.is_opening and op.folios == [(63, "r"), (62, "v")]
    letters = V.parse_name("LH_1_3_7_A_0004v-0003r")
    assert letters.candidate_keys() == ["LH 1,3,7,a", "LH 1,3,7a"]
    glued = V.parse_name("LH_4_7B_3_0020r")
    assert glued.candidate_keys() == ["LH 4,7b,3", "LH 4,7,b,3"]
    assert not V.parse_name("0001_page_12210614_docId_307926").parsed
    noside = V.parse_name("LH_1_3_7_C_0001")
    assert noside.parsed and noside.folios == [(1, "")] and "side" in noside.note


def test_geometry_helpers() -> None:
    assert V.bbox([[0, 0], [10, 0], [10, 5], [0, 5]]) == (0, 0, 10, 5) and V.bbox([]) is None
    assert V.iou((0, 0, 10, 10), (5, 0, 15, 10)) == pytest.approx(1 / 3)
    assert V.iou((0, 0, 1, 1), (2, 2, 3, 3)) == 0.0
    a = db.Page(work_id=W, seq=1, width=1000, height=1500)
    b = db.Page(work_id=W, seq=2, width=1000, height=1500)
    pl = V.placements_for(2000, 1500, [a, b], order=[1, 0])
    assert [p.page_id for p in pl] == [b.id, a.id] and pl[1].x0 == 1000 and pl[0].scale == 1.0
    assert V.placements_for(2000, 1500, [a], order=[0]) is None  # widths do not add up
    half = V.placements_for(500, 750, [a], order=[0])
    assert half and half[0].scale == 2.0
    assert V.project((100, 100, 900, 160), V.Placement(a.id, 1000, 2000, 1.0)) == (
        -900,
        100,
        -100,
        160,
    )


def test_match_judge_render_and_sheet(tmp_path: Path) -> None:
    store, dest, images = _seed(tmp_path)
    from leibniz.align.audit_reach import open_readonly

    conn = open_readonly(store)
    matches = V.run_match(conn, dest)
    by = {m.name: m for m in matches}
    assert by["LH_1_20_0063r-0062v"].status == "matched"
    assert by["LH_1_20_0063r-0062v"].layout == "two canvases (second|first)"  # 62v left, 63r right
    pairs = {p.their_id: p for p in by["LH_1_20_0063r-0062v"].pairs}
    assert pairs["L0"].ref == f"{W}:0001:000" and pairs["R2"].ref == f"{W}:0002:002"
    assert "X" not in pairs and pairs["L0"].iou == pytest.approx(1.0)
    single = by["LH_1_20_0064r"]
    assert (
        single.status == "matched"
        and single.layout == "single"
        and single.pairs[0].ref == f"{W}:0003:000"
    )
    assert single.pairs_at["iou≥0.7"] == 1
    assert by["LH_1_20_0099r"].status == "no_page" and by["LH_9_9_0001r"].status == "no_work"
    assert by["0001_page_12210614_docId_307926"].status == "unparsed"
    assert by["LH_1_3_7_A_0004v-0003r"].status == "no_page" and by[
        "LH_1_3_7_A_0004v-0003r"
    ].work_ids == ["00099002"]
    assert "00099002 has no folio labels" in "; ".join(by["LH_1_3_7_A_0004v-0003r"].notes)
    shared = by["LH_4_5_10_0048r"]
    assert shared.status == "resolved" and shared.page_ids == ["00099004:0001"]
    assert shared.work_ids == ["00099003", "00099004"]
    missing = by["LH_4_5_10_0099r"]
    assert missing.status == "no_page" and "00099003 has folios 3–3" in "; ".join(missing.notes)
    assert "00099004 has folios 48–48 on 1 of 1 pages" in "; ".join(missing.notes)
    assert by["LH_1_20_0062v"].status == "resolved" and by["LH_1_20_0062v"].page_ids == [
        f"{W}:0001"
    ]
    V.write_match(matches, dest / V.MATCH_NAME)
    back = V.read_match(dest / V.MATCH_NAME)
    assert [m.name for m in back] == [m.name for m in matches] and back[0].pairs[0].iou == matches[
        0
    ].pairs[0].iou
    n = V.write_heldout(matches, tmp_path / "heldout.csv")
    with (tmp_path / "heldout.csv").open(encoding="utf-8") as fh:
        held = list(csv.DictReader(fh))
    assert n == len(held) == 5 and {h["page_id"] for h in held} == {
        f"{W}:0001",
        f"{W}:0002",
        f"{W}:0003",
        "00099004:0001",
    }
    summ = V.match_summary(matches)
    assert summ["resolved"] == 4 and {u["name"] for u in summ["unresolved"]} == {
        "LH_1_20_0099r",
        "LH_9_9_0001r",
        "0001_page_12210614_docId_307926",
        "LH_1_3_7_A_0004v-0003r",
        "LH_4_5_10_0099r",
    }
    assert (
        summ["noisy_matched"] == 2
        and summ["pairs"] == 6
        and summ["by_split_status"]["val"]["unparsed"] == 1
    )

    rows = V.judge(conn, matches, dest)
    buckets = {r.ref: r.bucket for r in rows}
    assert buckets[f"{W}:0001:000"] == "agree"
    assert buckets[f"{W}:0001:001"] == "ours_only"
    assert buckets[f"{W}:0002:000"] == "disagree"
    assert buckets[f"{W}:0002:001"] == "near"
    assert buckets[f"{W}:0002:002"] == "theirs_only"  # not minted, theirs has text
    assert buckets[f"{W}:0003:000"] == "theirs_only"  # the nc row is ignored
    v2 = next(r for r in rows if r.ref == f"{W}:0003:000")
    assert v2.htr == "folium sequens v2"
    cs = V.compare_summary(matches, rows)
    assert cs["total"]["agree"] == 1 and cs["by_stratum"]["heavy_revision"]["disagree"] == 1
    assert cs["witness_disagree"]["ours_closer"] == 1  # the HTR reads "prima linea dextra"
    md = V.render(matches, rows, cs, listing=json.loads((dest / V.LISTING_NAME).read_text()))
    assert "**6 paired**" in md and "| noisy | 4 | 2 | 0 |" in md and "did not resolve" in md
    assert V.write_judged(rows, tmp_path / "j.csv") == 6
    sample = V.disagreement_sample(rows, n=10)
    assert [r.bucket for r in sample] == ["disagree", "near"]
    html_path, with_crops = V.build_disagreement_sheet(
        conn, rows, images_root=images, out_dir=dest, n=10
    )
    text = html_path.read_text(encoding="utf-8")
    assert (
        with_crops == 2
        and "PHILIUMM: Alia lectio" in text
        and "Where two aligners disagree" in text
    )
    conn.close()


def test_fetch_listing_and_noisy_with_mock_transport(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path.startswith("/api/datasets/"):
            return httpx.Response(
                200,
                json={
                    "sha": "deadbeef",
                    "cardData": {"license": "cc-by-4.0"},
                    "siblings": [
                        {"rfilename": "train/noisy/LH_1_20_0064r.xml"},
                        {"rfilename": "val/x.xml"},
                    ],
                },
            )
        return httpx.Response(200, content=b"<x/>")

    client = PoliteClient(
        client=httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0
    )
    dest = tmp_path / "philiumm"
    listing = V.fetch_listing(dest, client=client)
    assert listing["sha"] == "deadbeef" and V.split_files(listing, "noisy") == [
        "train/noisy/LH_1_20_0064r.xml"
    ]
    assert V.fetch_listing(dest, client=client)["sha"] == "deadbeef" and len(calls) == 1  # cached
    fetched, present = V.fetch_noisy(dest, client=client, listing=listing)
    assert (fetched, present) == (1, 1) and (
        dest / "noisy" / "LH_1_20_0064r.xml"
    ).read_bytes() == b"<x/>"
    assert calls[-1] == V.hf_file_url("train/noisy/LH_1_20_0064r.xml", revision="deadbeef")
    assert (
        V.fetch_noisy(dest, client=client, listing=listing) == (0, 1) and len(calls) == 2
    )  # resumable


def test_vi4_cli_round_trip(tmp_path: Path) -> None:
    store, dest, images = _seed(tmp_path)
    reports = tmp_path / "reports"
    res = runner.invoke(
        app,
        [
            "align",
            "philiumm-vi4",
            "match",
            "--db",
            str(store),
            "--dest",
            str(dest),
            "--reports",
            str(reports),
        ],
    )
    assert res.exit_code == 0, res.stdout
    flat = " ".join(res.stdout.split())
    assert "6 pairs" in flat and (reports / "heldout_pages.csv").exists()
    res = runner.invoke(
        app,
        [
            "align",
            "philiumm-vi4",
            "compare",
            "--db",
            str(store),
            "--dest",
            str(dest),
            "--reports",
            str(reports),
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "agree 1" in " ".join(res.stdout.split()) and (reports / "vi4-crosscheck.md").exists()
    assert (reports / "vi4-disagreements-sample.csv").exists() and (
        dest / "vi4-double-witnessed.csv"
    ).exists()
    res = runner.invoke(
        app,
        [
            "align",
            "philiumm-vi4",
            "sheet",
            "--db",
            str(store),
            "--dest",
            str(dest),
            "--images",
            str(images),
            "--n",
            "5",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "2 lines with image strips" in " ".join(res.stdout.split())
    assert (dest / "philiumm-disagreements.html").exists()


def test_opening_registered_twice_is_one_scan(tmp_path: Path) -> None:
    """The store holds the sheet scan once per folio label (Open Q #19): their opening
    image has that scan's size, so one page carries every line of both folios."""
    store, dest, images = _seed(tmp_path)
    conn = db.connect(store)
    # make 62v and 63r the same 2000 × 1500 scan with the lines of both halves
    for seq in (1, 2):
        conn.execute(
            "UPDATE pages SET width = 2000, height = 1500 WHERE work_id = ? AND seq = ?", (W, seq)
        )
    conn.execute("DELETE FROM lines WHERE page_id IN (?, ?)", (f"{W}:0001", f"{W}:0002"))
    conn.execute("DELETE FROM gt_lines")
    # the factory minted the passage on the 62v registration (seq 1), not the first-named 63r
    insert_gt_pairs(
        conn,
        [
            GtPair(
                f"{W}:0001:001",
                "linea secunda",
                "AA VI,4 N.1 (…; katalog k-1)",
                "fair_copy",
                0.9,
                "open",
            )
        ],
    )
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    for pid in (f"{W}:0001", f"{W}:0002"):
        for seq, (x0, y0, x1, y1) in enumerate(
            ((100, 100, 900, 160), (1100, 100, 1900, 160), (1100, 200, 1900, 260))
        ):
            db.insert_line(
                conn,
                db.Line(
                    page_id=pid,
                    line_seq=seq,
                    polygon=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                    run_id=seg,
                    status="machine",
                ),
            )
            db.set_line_recognition(
                conn, pid, seq, text=f"line {seq}", conf=0.9, model="htr", run_id=rec
            )
    conn.commit()
    conn.close()
    from leibniz.align.audit_reach import open_readonly

    ro = open_readonly(store)
    by = {m.name: m for m in V.run_match(ro, dest)}
    ro.close()
    m = by["LH_1_20_0063r-0062v"]
    assert m.status == "matched" and m.layout.startswith("one scan")
    # the registration that carries the minted lines (62v, seq 1) is the one paired
    assert {p.ref for p in m.pairs} == {f"{W}:0001:000", f"{W}:0001:001", f"{W}:0001:002"}
    assert any("00099001:0001 carries 1 minted lines" in n for n in m.notes)
