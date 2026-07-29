"""Tests for METS fileSec → pages derivation (offline)."""

from __future__ import annotations

import shutil
from pathlib import Path

from lxml import etree

from leibniz import db
from leibniz.harvest.oai import NS
from leibniz.images import pages as P

FIX = Path(__file__).parent / "fixtures" / "mets" / "listrecords_filesec.xml"


def _mets(object_id: str) -> etree._Element:
    root = etree.fromstring(FIX.read_bytes())
    for rec in root.xpath(".//oai:record", namespaces=NS):
        if rec.findtext(".//oai:identifier", namespaces=NS) == object_id:
            return rec.find(".//mets:mets", NS)
    raise AssertionError(f"no record {object_id}")


# -- iter_page_images ------------------------------------------------------- #


def test_iiif_record_uses_default_and_constructs_service() -> None:
    imgs = P.iter_page_images(_mets("IIIF-001"), "IIIF-001")
    assert [i.seq for i in imgs] == [1, 2]
    assert all(i.delivery == "iiif" for i in imgs)
    p1 = imgs[0]
    assert p1.image_url.endswith("/content/IIIF-001/jpgs/default/00000001.jpg")
    assert p1.thumb_url.endswith("/content/IIIF-001/jpgs/thumbs/00000001.jpg")
    assert (
        p1.image_service_url
        == "https://digitale-sammlungen.gwlb.de/iiif/IIIF-001/ptif/00000001.ptif"
    )
    assert p1.order_label == "1r"


def test_static_record_falls_back_to_max_then_reconstructs() -> None:
    imgs = P.iter_page_images(_mets("STATIC-002"), "STATIC-002")
    assert [i.seq for i in imgs] == [1, 2]
    assert all(i.delivery == "static" for i in imgs)
    assert all(i.image_service_url is None for i in imgs)
    # Page 1 had a MAX jpg but no DEFAULT → image_url is the MAX href.
    assert imgs[0].image_url.endswith("/content/STATIC-002/jpgs/max/00000001.jpg")
    # Page 2 had neither DEFAULT nor MAX in the fileSec → reconstructed by convention.
    assert imgs[1].image_url.endswith("/content/STATIC-002/jpgs/default/00000002.jpg")


def test_empty_physical_structmap_yields_no_pages() -> None:
    mets = etree.fromstring(b'<mets:mets xmlns:mets="http://www.loc.gov/METS/"></mets:mets>')
    assert P.iter_page_images(mets, "X") == []


# -- populate_pages_from_cache --------------------------------------------- #


def _seed_cache(tmp_path: Path) -> Path:
    cache = tmp_path / "oai"
    (cache / "LeibnizHandschriften").mkdir(parents=True)
    shutil.copy(FIX, cache / "LeibnizHandschriften" / "page_0001.xml")
    return cache


def test_populate_pages_from_cache_all(tmp_path) -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("IIIF-001", "LeibnizHandschriften", n_canvases=2))
    db.upsert_work(conn, db.Work("STATIC-002", "LeibnizBriefwechsel", n_canvases=2))
    cache = _seed_cache(tmp_path)

    stats = P.populate_pages_from_cache(conn, cache_dir=cache)
    assert stats.works == 2
    assert stats.pages == 4
    assert stats.iiif_pages == 2 and stats.static_pages == 2
    assert db.count_pages(conn) == 4
    assert db.count_fetch_targets(conn) == 4  # every page got an image_url
    conn.close()


def test_populate_skips_orphan_and_respects_include(tmp_path) -> None:
    conn = db.init_db(":memory:")
    # Only seed the IIIF work; STATIC-002 has no work row → skipped (FK-safe).
    db.upsert_work(conn, db.Work("IIIF-001", "LeibnizHandschriften", n_canvases=2))
    cache = _seed_cache(tmp_path)

    stats = P.populate_pages_from_cache(conn, cache_dir=cache, include={"IIIF-001"})
    assert stats.works == 1
    assert db.count_pages(conn) == 2
    assert db.get_pages(conn, "IIIF-001")[0].delivery == "iiif"
    conn.close()


def test_populate_preserves_download_manifest_on_rerun(tmp_path) -> None:
    # Re-deriving must not wipe an already-recorded download (upsert COALESCE).
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("IIIF-001", "LeibnizHandschriften", n_canvases=2))
    cache = _seed_cache(tmp_path)
    P.populate_pages_from_cache(conn, cache_dir=cache, include={"IIIF-001"})
    db.mark_page_fetched(
        conn,
        "IIIF-001:0001",
        local_path="IIIF-001/0001.jpg",
        n_bytes=999,
        sha256="deadbeef",
        width=800,
        height=1000,
    )
    # Re-run derivation over the same work.
    P.populate_pages_from_cache(conn, cache_dir=cache, include={"IIIF-001"})
    page = db.get_page(conn, "IIIF-001:0001")
    assert page.sha256 == "deadbeef" and page.n_bytes == 999  # preserved
    assert (page.width, page.height) == (800, 1000)  # preserved
    conn.close()
