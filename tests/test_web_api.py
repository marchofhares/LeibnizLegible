"""The JSON API + viewer host, end to end over a seeded store (no server)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import Fts5Backend
from leibniz.web.api import INDEX_ROUTES, create_app

W1 = "00068642"
W2 = "DE-611-HS-854976"


def _client(store_path: Path, tmp_path: Path, *, search: bool = True, static: Path | None = None):
    be = None
    if search:
        be = Fts5Backend(tmp_path / "search.sqlite")
        conn = db.connect(store_path)
        be.rebuild(iter_page_docs(conn), meta={"stats": corpus_stats(conn)})
        conn.close()
    app = create_app(store_path, search=be, static_dir=static)
    return TestClient(app)


def test_stats(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    s = c.get("/api/stats").json()
    assert s["works"] == 2 and s["pages_recognized"] == 3 and s["backend"] == "fts5"
    assert s["version"] and s["index_built_at"]


def test_stats_without_index_computes_live(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, search=False)
    s = c.get("/api/stats").json()
    assert s["pages"] == 4 and s["backend"] is None


def test_search(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get("/api/search", params={"q": "calculemus"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1 and body["hits"][0]["page_id"] == f"{W1}:0001"
    assert body["hits"][0]["set"] == "LeibnizHandschriften"
    assert (
        c.get("/api/search", params={"q": "de", "set": "LeibnizBriefwechsel"}).json()["total"] == 1
    )
    assert c.get("/api/search", params={"q": "de", "min_conf": "0.85"}).json()["total"] == 1
    assert c.get("/api/search", params={"q": "de", "min_conf": "2"}).status_code == 422
    assert c.get("/api/search", params={"q": ""}).json()["total"] == 0


def test_search_unconfigured(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, search=False)
    assert c.get("/api/search", params={"q": "x"}).status_code == 503


def test_work(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    w = c.get(f"/api/works/{W1}").json()
    assert w["title"] == "LH 4,6,18" and w["iiif_manifest"] == f"/manifests/{W1}"
    assert [p["seq"] for p in w["pages"]] == [1, 2, 3]
    assert w["pages"][0]["n_lines"] == 3 and w["pages"][2]["skip_reason"] == "no_lines"
    assert w["katalog"][0]["aa_labels"] == ["AA VI,4 N. 109"]
    assert w["katalog"][0]["title"].startswith("Praefatio")
    assert set(w["attribution"]) == {"images", "katalog", "transcriptions"}
    assert c.get("/api/works/nope").status_code == 404


def test_page(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    p = c.get(f"/api/pages/{W1}:0001").json()
    assert p["delivery"] == "iiif" and p["image_service_url"].endswith("/1.ptif")
    assert p["prev_page_id"] is None and p["next_page_id"] == f"{W1}:0002"
    assert p["stats"]["n_lines"] == 3
    l0 = p["lines"][0]
    assert l0["text"] == "Calculemus inquit Leibnitius." and l0["conf"] == 0.95
    assert l0["bbox"] == {"x": 100, "y": 160, "w": 1800, "h": 60}
    assert l0["polygon"][0] == [100, 160] and l0["run_at"]
    assert p["run"]["model"] == "leibniz-htr-v2@v2"
    assert p["honesty"].startswith("Machine transcription")
    p2 = c.get(f"/api/pages/{W1}:0002").json()
    assert p2["prev_page_id"] == f"{W1}:0001" and p2["next_page_id"] == f"{W1}:0003"
    skipped = c.get(f"/api/pages/{W1}:0003").json()
    assert skipped["status"] == "skipped" and skipped["lines"] == []
    assert c.get("/api/pages/none:0001").status_code == 404


def test_manifest_and_annotations(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get(f"/manifests/{W1}")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/ld+json")
    m = r.json()
    assert m["id"] == f"http://testserver/manifests/{W1}" and len(m["items"]) == 3
    a = c.get(f"/annotations/{W1}:0001").json()
    assert a["type"] == "AnnotationPage" and len(a["items"]) == 3
    assert a["items"][0]["target"].startswith(f"http://testserver/manifests/{W1}/canvas/1#xywh=")
    assert c.get(f"/manifests/{W2}").json()["items"][0]["items"][0]["items"][0]["body"]["id"]
    assert c.get("/manifests/nope").status_code == 404
    assert c.get("/annotations/nope:0001").status_code == 404


def test_base_url_override(store_path, tmp_path) -> None:
    app = create_app(store_path, search=None, static_dir=None, base_url="https://x.org/")
    c = TestClient(app)
    assert c.get(f"/manifests/{W1}").json()["id"] == f"https://x.org/manifests/{W1}"


def test_static_viewer_routes(store_path, tmp_path) -> None:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text(
        "<!doctype html><title>Leibniz Legible</title>", encoding="utf-8"
    )
    (static / "app.js").write_text("console.log('ok')", encoding="utf-8")
    c = _client(store_path, tmp_path, static=static)
    for route in INDEX_ROUTES:
        url = route.replace("{work_id}", W1).replace("{page_id}", f"{W1}:0001")
        r = c.get(url)
        assert r.status_code == 200 and "Leibniz Legible" in r.text, url
    assert c.get("/static/app.js").text == "console.log('ok')"


def test_no_static_dir_means_api_only(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, static=tmp_path / "missing")
    assert c.get("/").status_code == 404
