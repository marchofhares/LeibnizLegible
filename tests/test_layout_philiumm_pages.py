"""Her layout dataset's names and pages (offline, on the fixture store)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.conftest import W1, W2

from leibniz import db
from leibniz.layout import philiumm_pages as P


def test_stem_and_name_kinds() -> None:
    assert (
        P.stem_of("LH_35_1_14_0065r_jpg.rf.cdc6a5546a12ce681c06ff7f0afca3da.jpg")
        == "LH_35_1_14_0065r"
    )
    assert P.stem_of("original/test/3r_jpg.rf.abc.jpg") == "3r"
    assert P.stem_of("LH_35_1_14_0065r.jpg") == "LH_35_1_14_0065r"
    n = P.parse_dataset_name("LH_35_1_3_0023r-0017v_jpg.rf.a8d7.jpg", "test")
    assert n.kind == "shelfmark" and n.shelfmark is not None
    assert n.shelfmark.family == "LH" and n.shelfmark.tokens == ("35", "1", "3")
    assert n.shelfmark.folios == [(23, "r"), (17, "v")] and n.shelfmark.is_opening
    n = P.parse_dataset_name("img_LH_35_5_25_1v_jpg.rf.42f3.jpg")
    assert n.kind == "shelfmark" and n.shelfmark.folios == [(1, "v")] and n.half is None
    n = P.parse_dataset_name("img_LH_35_14_2_20v_g_jpg.rf.ab12.jpg")
    assert n.kind == "shelfmark" and n.half == "g" and "left half" in n.note
    assert n.shelfmark.folios == [(20, "v")]
    assert P.parse_dataset_name("8_cod_ms_philos_140_0002_jpg.rf.ce19.jpg").kind == "goettingen"
    assert (
        P.parse_dataset_name("0001_page_12210614_docId_307926_jpg.rf.05c0.jpg").kind
        == "escriptorium"
    )
    assert P.parse_dataset_name("3r_jpg.rf.083b.jpg").kind == "folio"
    assert P.parse_dataset_name("whatever.jpg").kind == "other"
    assert P.parse_dataset_name("LH_4_7B_2_0058v-0057r_jpg.rf.b205.jpg").shelfmark.tokens == (
        "4",
        "7B",
        "2",
    )


def test_read_coco(tmp_path: Path) -> None:
    coco = {
        "images": [
            {"id": 1, "file_name": "a_jpg.rf.1.jpg", "width": 100, "height": 200},
            {"id": 2, "file_name": "b_jpg.rf.2.jpg", "width": 300, "height": 400},
        ],
        "annotations": [{"id": 1, "image_id": 1}, {"id": 2, "image_id": 1}],
        "categories": [{"id": 3, "name": "MainZone"}, {"id": 4, "name": "MarginTextZone"}],
    }
    path = tmp_path / "c.json"
    path.write_text(json.dumps(coco))
    images, cats = P.read_coco(path, "test")
    assert [(i.file_name, i.width, i.height, i.n_annotations) for i in images] == [
        ("a_jpg.rf.1.jpg", 100, 200, 2),
        ("b_jpg.rf.2.jpg", 300, 400, 0),
    ]
    assert cats == {3: "MainZone", 4: "MarginTextZone"}


def test_match_images_on_the_fixture_store(store_path: Path) -> None:
    conn = db.connect(store_path)
    images = [
        P.CocoImage("test", "LH_4_6_18_0001r_jpg.rf.aa.jpg", 2000, 2500),  # W1's page 1 (label 1r)
        P.CocoImage("test", "LH_4_6_18_0001v_jpg.rf.ab.jpg", 1000, 1250),  # a rescaled copy
        P.CocoImage("train", "LH_9_9_9_0001r_jpg.rf.ac.jpg", 10, 10),  # no such work
        P.CocoImage("train", "8_cod_ms_philos_140_0002_jpg.rf.ad.jpg", 10, 10),
        P.CocoImage(
            "train", "0001_page_1_docId_1_jpg.rf.ae.jpg", 1800, 2400
        ),  # W2's size, one page
        P.CocoImage("train", "3r_jpg.rf.af.jpg", 7, 7),  # no page of that size
    ]
    out = P.match_images(conn, images, images_root=None, fetch_original=None)
    by = {m.stem: m for m in out}
    assert by["LH_4_6_18_0001r"].status == "matched" and by["LH_4_6_18_0001r"].page_ids == [
        f"{W1}:0001"
    ]
    assert by["LH_4_6_18_0001r"].size_agrees is True and by["LH_4_6_18_0001r"].ratio_agrees is True
    assert by["LH_4_6_18_0001v"].status == "matched" and by["LH_4_6_18_0001v"].size_agrees is False
    assert by["LH_4_6_18_0001v"].ratio_agrees is True
    assert by["LH_9_9_9_0001r"].status == "no_work"
    assert (
        by["8_cod_ms_philos_140_0002"].status == "not-gwlb"
        and by["8_cod_ms_philos_140_0002"].page_ids == []
    )
    assert by["0001_page_1_docId_1"].status == "size-matched" and by[
        "0001_page_1_docId_1"
    ].page_ids == [f"{W2}:0001"]
    assert by["3r"].status == "unmatched"
    summ = P.summary(out, {"sha": "abc", "license": "cc-by-4.0"}, {1: "MainZone"})
    assert summ["pages_test"] == 2 and summ["pages_train_valid"] == 1  # 1r and 1v are two pages
    assert summ["by_split"]["train"]["not-gwlb"] == 1
    assert summ["size_check"] == {
        "single_pages_resolved_by_name": 2,
        "size_agrees": 1,
        "ratio_agrees": 2,
    }


def test_dropped_shelfmark_part_and_pages_csv(store_path: Path, tmp_path: Path) -> None:
    conn = db.connect(store_path)
    # LH_4_6_18_7_0001r: the store's work is LH 4, 6, 18; the "7" is dropped once
    out = P.match_images(
        conn,
        [P.CocoImage("train", "LH_4_6_18_7_0001r_jpg.rf.aa.jpg", 2000, 2500)],
        images_root=None,
        fetch_original=None,
    )
    assert out[0].status == "matched" and out[0].page_ids == [f"{W1}:0001"]
    assert any("dropped" in n for n in out[0].notes)
    path = tmp_path / "pages.csv"
    assert P.write_pages_csv(out, path) == 1
    assert P.read_pages_csv(path) == {f"{W1}:0001"}
    assert P.read_pages_csv(path, splits=["test"]) == set()
    header = path.read_text().splitlines()[0]
    assert header.startswith(
        "file,split,kind,status,page_ids,work_ids,width,height,size_agrees,ratio_agrees"
    )


def test_thumbnail_distance() -> None:
    assert P.thumb_distance([0, 0], [0, 0]) == 0.0
    assert P.thumb_distance([0, 255], [255, 0]) == 255.0
    assert P.thumb_distance([], [1]) == 255.0


def test_match_by_image_with_candidates_and_thumbnails(store_path: Path, tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    from PIL import Image

    conn = db.connect(store_path)
    images_root = tmp_path / "images"
    (images_root / W1).mkdir(parents=True)
    # three pages of W1, all 2000×2500 in the store: cached scans of three greys
    for seq, grey in ((1, 40), (2, 120), (3, 200)):
        Image.new("L", (200, 250), grey).save(images_root / W1 / f"{seq:04d}.jpg")
    original = tmp_path / "orig.jpg"
    Image.new("L", (2000, 2500), 118).save(original)
    name = P.parse_dataset_name("3r_jpg.rf.af.jpg")
    im = P.CocoImage("train", "3r_jpg.rf.af.jpg", 2000, 2500)
    pages = db.get_pages(conn, W1)
    for p in pages:
        p.local_path = f"{W1}/{p.seq:04d}.jpg"
    pm = P.match_by_image(
        name,
        im,
        conn,
        images_root=images_root,
        fetch_original=lambda rel: original.read_bytes(),
        candidates=pages,
    )
    assert pm.status == "thumbnail-matched" and pm.page_ids == [f"{W1}:0002"]
    # without a way to fetch the original, several candidates stay ambiguous
    pm = P.match_by_image(
        name, im, conn, images_root=images_root, fetch_original=None, candidates=pages
    )
    assert pm.status == "ambiguous" and len(pm.page_ids) == 3
