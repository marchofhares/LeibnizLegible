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
    # extension contexts first, the Presentation context last (Presentation 3 §4.6)
    assert m["@context"][-1] == "http://iiif.io/api/presentation/3/context.json"
    assert m["@context"][0] == {"leibniz": iiif.LEIBNIZ_NS}
    assert m["id"] == f"{BASE}/manifests/{W1}" and m["type"] == "Manifest"
    assert m["label"] == {"none": ["LH 4,6,18"]}
    assert len(m["items"]) == 3
    c0 = m["items"][0]
    assert c0["id"] == f"{BASE}/manifests/{W1}/canvas/1" and c0["width"] == 2000
    body = c0["items"][0]["items"][0]["body"]
    # an Image API 2 service keeps its 2.x keys and names its profile by URI
    svc = body["service"][0]
    assert svc["@type"] == "ImageService2" and "type" not in svc and "id" not in svc
    assert svc["@id"].startswith("https://digitale-sammlungen.gwlb.de/iiif/")
    assert svc["profile"] == "http://iiif.io/api/image/2/level1.json"
    assert body["id"] == svc["@id"] + "/full/max/0/default.jpg"
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


def test_unknown_dimensions_are_left_out_not_null(store_path) -> None:
    conn = db.connect(store_path)
    work = db.get_work(conn, W1)
    page = db.get_pages(conn, W1)[0]
    page.width = page.height = None
    canvas = iiif.build_manifest(work, [page], base_url=BASE)["items"][0]
    body = canvas["items"][0]["items"][0]["body"]
    assert "width" not in canvas and "height" not in canvas
    assert "width" not in body and "height" not in body
    assert None not in canvas.values() and None not in body.values()
