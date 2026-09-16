"""The JSON API + viewer host, end to end over a seeded store (no server)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from leibniz import db
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import Fts5Backend
from leibniz.web import api
from leibniz.web.api import INDEX_ROUTES, STATIC_DIR, create_app

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


def test_healthz(store_path, tmp_path) -> None:
    r = _client(store_path, tmp_path).get("/healthz")
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    assert r.json() == {
        "status": "ok",
        "version": r.json()["version"],
        "store": True,
        "search": {"backend": "fts5", "ok": True},
    }
    assert _client(store_path, tmp_path, search=False).get("/healthz").json()["search"] is None
    missing = TestClient(create_app(tmp_path / "nope.sqlite", search=None, static_dir=None))
    assert missing.get("/healthz").status_code == 503
    assert missing.get(f"/api/works/{W1}").status_code == 503


class _Down:
    """A search backend whose server is unreachable."""

    name = "meili"

    def search(self, query):
        raise httpx.ConnectError("connection refused")

    def meta(self) -> dict:
        return {}

    def count(self) -> int:
        return 0

    def health(self) -> bool:
        return False


def test_search_backend_down_is_503_and_health_degraded(store_path, tmp_path) -> None:
    c = TestClient(create_app(store_path, search=_Down(), static_dir=None))
    r = c.get("/api/search", params={"q": "x"})
    assert r.status_code == 503 and "unavailable" in r.json()["detail"]
    h = c.get("/healthz")
    assert h.status_code == 200 and h.json()["status"] == "degraded"
    assert h.json()["search"] == {"backend": "meili", "ok": False}
    # stats fall back to a live scan of the store when the index has none
    assert c.get("/api/stats").json()["pages_recognized"] == 3


def test_work_page_summaries_agree_with_page_endpoint(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    w = c.get(f"/api/works/{W1}").json()
    assert [(p["n_lines"], p["mean_conf"]) for p in w["pages"]] == [
        (3, round((0.95 + 0.72 + 0.55) / 3, 4)),  # the re-read line 0 counts once, at 0.95
        (2, round((0.88 + 0.81) / 2, 4)),
        (0, None),  # skipped page: no lines
    ]
    for p in w["pages"]:
        stats = c.get(f"/api/pages/{p['page_id']}").json()["stats"]
        assert (p["n_lines"], p["mean_conf"]) == (stats["n_lines"], stats["mean_conf"])
    m = c.get(f"/manifests/{W1}").json()
    counts = [
        next(
            (
                x["value"]["en"][0]
                for x in cv["metadata"]
                if x["label"]["en"] == ["Transcribed lines"]
            ),
            None,
        )
        for cv in m["items"]
    ]
    assert counts == ["3", "2", None]


def test_store_is_opened_read_only(store_path) -> None:
    conn = api._open(store_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM works").fetchone()[0] == 2
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO runs (stage) VALUES ('x')")
    finally:
        conn.close()


def test_security_headers_cors_and_gzip(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get(f"/api/works/{W1}", headers={"Origin": "https://mirador.example"})
    assert r.headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["access-control-allow-origin"] == "*"
    m = c.get(f"/manifests/{W1}", headers={"Accept-Encoding": "gzip"})
    assert m.headers.get("content-encoding") == "gzip" and m.json()["type"] == "Manifest"
    plain = TestClient(create_app(store_path, search=None, static_dir=None, security_headers=False))
    assert "Content-Security-Policy" not in plain.get(f"/api/works/{W1}").headers


def test_rate_limit_wired_into_app(store_path, tmp_path) -> None:
    c = TestClient(create_app(store_path, search=None, static_dir=None, rate_limit=1, rate_burst=2))
    assert [c.get(f"/api/works/{W1}").status_code for _ in range(3)] == [200, 200, 429]
    assert c.get("/healthz").status_code == 200  # operations routes are never limited


def test_real_static_dir_serves_shell_boot_script_and_robots(store_path, tmp_path) -> None:
    c = TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))
    r = c.get("/")
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-cache"
    assert '<script src="/static/boot.js"></script>' in r.text and "<script>" not in r.text
    assert "no-js" in c.get("/static/boot.js").text
    robots = c.get("/robots.txt")
    assert robots.status_code == 200 and robots.headers["content-type"].startswith("text/plain")
    assert "Disallow: /manifests/" in robots.text
