"""IIIF Presentation 3 manifests + annotation pages (pure builders)."""

from __future__ import annotations

from leibniz import db
from leibniz.search.documents import latest_lines
from leibniz.web import iiif

W1 = "00068642"
W2 = "DE-611-HS-854976"

BASE = "https://legible.example.org"


def test_manifest_shape(store_path) -> None:
    conn = db.connect(store_path)
    work = db.get_work(conn, W1)
    pages = db.get_pages(conn, W1)
    m = iiif.build_manifest(work, pages, base_url=BASE, line_counts={f"{W1}:0001": 3})
    assert m["@context"][0].endswith("/presentation/3/context.json")
    assert m["id"] == f"{BASE}/manifests/{W1}" and m["type"] == "Manifest"
    assert m["label"] == {"none": ["LH 4,6,18"]}
    assert len(m["items"]) == 3
    c0 = m["items"][0]
    assert c0["id"] == f"{BASE}/manifests/{W1}/canvas/1" and c0["width"] == 2000
    body = c0["items"][0]["items"][0]["body"]
    assert body["service"][0]["type"] == "ImageService2"
    assert body["service"][0]["id"].startswith("https://digitale-sammlungen.gwlb.de/iiif/")
    assert c0["annotations"][0]["id"] == f"{BASE}/annotations/{W1}:0001"
    assert any(md["value"]["en"] == ["3"] for md in c0["metadata"])
    assert m["seeAlso"][0]["id"].endswith("/manifest.json")
    assert "Public Domain Mark" in m["requiredStatement"]["value"]["en"][0]
    skipped = m["items"][2]
    assert any(md["label"]["en"] == ["Skip reason"] for md in skipped["metadata"])


def test_manifest_static_delivery(store_path) -> None:
    conn = db.connect(store_path)
    m = iiif.build_manifest(db.get_work(conn, W2), db.get_pages(conn, W2), base_url=BASE)
    body = m["items"][0]["items"][0]["items"][0]["body"]
    assert "service" not in body and body["id"].endswith("/jpgs/default/00000001.jpg")


def test_annotation_page(store_path) -> None:
    conn = db.connect(store_path)
    page = db.get_page(conn, f"{W1}:0001")
    lines = latest_lines(conn, page.id)
    ap = iiif.build_annotation_page(
        page, lines, base_url=BASE, run_dates={3: "2026-09-16T00:00:00Z"}
    )
    assert ap["type"] == "AnnotationPage" and ap["id"] == f"{BASE}/annotations/{W1}:0001"
    assert len(ap["items"]) == 3
    a0 = ap["items"][0]
    assert a0["motivation"] == "supplementing"
    assert a0["body"]["value"] == "Calculemus inquit Leibnitius." and a0["body"]["language"] == "la"
    assert a0["target"] == f"{BASE}/manifests/{W1}/canvas/1#xywh=100,160,1800,60"
    assert a0["leibniz:status"] == "machine" and a0["leibniz:confidence"] == 0.95
    assert (
        a0["leibniz:model"] == "leibniz-htr-v2@v2" and a0["leibniz:runAt"] == "2026-09-16T00:00:00Z"
    )
    assert a0["leibniz:polygon"][0] == [100, 160]
    assert ap["items"][2]["body"]["language"] == "und"
    assert "transcriptions" in ap["leibniz:attribution"]
