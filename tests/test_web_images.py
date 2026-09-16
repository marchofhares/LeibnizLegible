"""The image mirror switch: URLs, the API, the manifests, provenance, the shell stamp."""

from __future__ import annotations

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import Fts5Backend
from leibniz.web import attribution as attr
from leibniz.web.api import STATIC_DIR, create_app
from leibniz.web.images import ImageSource

W1 = "00068642"
W2 = "DE-611-HS-854976"
MIRROR = "https://images.example.org"


def _mark_cached(store_path, *page_ids: str) -> None:
    conn = db.connect(store_path)
    for pid in page_ids:
        work_id, seq = pid.rsplit(":", 1)
        db.mark_page_fetched(
            conn,
            pid,
            local_path=f"{work_id}/{int(seq):04d}.jpg",
            n_bytes=1234,
            sha256="0" * 64,
            width=2000,
            height=2500,
        )
    conn.commit()
    conn.close()


def _client(store_path, tmp_path, *, mirror: str | None = MIRROR, static=None) -> TestClient:
    be = Fts5Backend(tmp_path / "search.sqlite")
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn), meta={"stats": corpus_stats(conn)})
    conn.close()
    return TestClient(create_app(store_path, search=be, static_dir=static, image_base_url=mirror))


def test_image_source_urls(store_path) -> None:
    _mark_cached(store_path, f"{W1}:0001")
    conn = db.connect(store_path)
    cached = db.get_page(conn, f"{W1}:0001")
    uncached = db.get_page(conn, f"{W1}:0002")
    conn.close()
    off = ImageSource(None)
    assert not off.mirrored and off.origin == "gwlb"
    assert off.image_url(cached) == cached.image_url and off.resolve(cached) is cached
    on = ImageSource(MIRROR + "/")  # trailing slash tolerated
    assert on.base_url == MIRROR and on.origin == "mirror"
    assert on.image_url(cached) == f"{MIRROR}/{W1}/0001.jpg"
    assert on.thumb_url(cached) == f"{MIRROR}/thumbs/{W1}/0001.jpg"
    assert on.thumb_url_for(W2, 7, "x") == f"{MIRROR}/thumbs/{W2}/0007.jpg"
    shown = on.resolve(cached)
    assert shown.delivery == "static" and shown.image_service_url is None
    assert shown.image_url == f"{MIRROR}/{W1}/0001.jpg" and shown.width == 2000
    assert on.source_url(cached) == cached.image_service_url  # provenance: the GWLB
    # never cached → still the GWLB, untouched
    assert on.resolve(uncached) is uncached and on.image_url(uncached) == uncached.image_url


def test_api_with_mirror(store_path, tmp_path) -> None:
    _mark_cached(store_path, f"{W1}:0001", f"{W1}:0002", f"{W2}:0001")
    c = _client(store_path, tmp_path)
    p = c.get(f"/api/pages/{W1}:0001").json()
    assert p["delivery"] == "static" and p["image_service_url"] is None
    assert p["image_url"] == f"{MIRROR}/{W1}/0001.jpg"
    assert p["thumb_url"] == f"{MIRROR}/thumbs/{W1}/0001.jpg"
    assert p["image_origin"] == "mirror"
    assert p["source_image_url"].startswith("https://digitale-sammlungen.gwlb.de/iiif/")
    assert p["attribution"]["images"] == attr.IMAGES_MIRROR
    # the skipped page was never cached: GWLB, as before
    s = c.get(f"/api/pages/{W1}:0003").json()
    assert s["image_origin"] == "gwlb" and s["delivery"] == "iiif"
    w = c.get(f"/api/works/{W1}").json()
    assert w["pages"][0]["thumb_url"] == f"{MIRROR}/thumbs/{W1}/0001.jpg"
    assert w["pages"][2]["thumb_url"].startswith("https://digitale-sammlungen.gwlb.de/")
    hits = c.get("/api/search", params={"q": "calculemus"}).json()["hits"]
    assert hits[0]["thumb_url"] == f"{MIRROR}/thumbs/{W1}/0001.jpg"
    stats = c.get("/api/stats").json()
    assert stats["images"] == {"origin": "mirror", "base_url": MIRROR}


def test_api_without_mirror_is_unchanged(store_path, tmp_path) -> None:
    _mark_cached(store_path, f"{W1}:0001")
    c = _client(store_path, tmp_path, mirror=None)
    p = c.get(f"/api/pages/{W1}:0001").json()
    assert p["delivery"] == "iiif" and p["image_origin"] == "gwlb"
    assert (
        p["image_service_url"].endswith("/1.ptif")
        and p["source_image_url"] == p["image_service_url"]
    )
    assert p["attribution"]["images"] == attr.IMAGES
    assert c.get("/api/stats").json()["images"] == {"origin": "gwlb", "base_url": None}


def test_manifest_and_annotations_with_mirror(store_path, tmp_path) -> None:
    _mark_cached(store_path, f"{W1}:0001")
    c = _client(store_path, tmp_path)
    m = c.get(f"/manifests/{W1}").json()
    body = m["items"][0]["items"][0]["items"][0]["body"]
    assert body["id"] == f"{MIRROR}/{W1}/0001.jpg" and "service" not in body
    assert body["width"] == 2000 and body["height"] == 2500
    src = next(x for x in m["items"][0]["metadata"] if x["label"]["en"] == ["Source image (GWLB)"])
    assert src["value"]["none"][0].startswith("https://digitale-sammlungen.gwlb.de/iiif/")
    assert attr.IMAGES_MIRROR in m["requiredStatement"]["value"]["en"]
    # uncached canvases keep the GWLB service and carry no source row
    canvas2 = m["items"][1]
    assert "service" in canvas2["items"][0]["items"][0]["body"]
    assert all(x["label"]["en"] != ["Source image (GWLB)"] for x in canvas2["metadata"])
    # provenance in the annotations names the GWLB image whatever is displayed
    a = c.get(f"/annotations/{W1}:0001").json()
    assert a["items"][0]["leibniz:imageUri"].startswith("https://digitale-sammlungen.gwlb.de/iiif/")
    assert a["leibniz:attribution"]["images"] == attr.IMAGES_MIRROR


def test_shell_is_stamped_with_the_image_origin(store_path, tmp_path) -> None:
    on = _client(store_path, tmp_path, static=STATIC_DIR)
    r = on.get("/")
    assert r.status_code == 200 and 'data-image-origin="mirror"' in r.text
    assert r.headers["Cache-Control"] == "no-cache" and r.headers["ETag"]
    assert on.get("/", headers={"If-None-Match": r.headers["ETag"]}).status_code == 304
    off = _client(store_path, tmp_path, mirror=None, static=STATIC_DIR)
    assert 'data-image-origin="gwlb"' in off.get(f"/page/{W1}:0001").text
