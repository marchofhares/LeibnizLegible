"""The JSON API + viewer host, end to end over a seeded store (no server)."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from urllib.robotparser import RobotFileParser

import httpx
import pytest
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from leibniz import db
from leibniz.search.documents import corpus_stats, iter_page_docs, latest_lines
from leibniz.search.fts5 import Fts5Backend
from leibniz.web import api
from leibniz.web import attribution as attr
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


def test_search_phrases_and_exclusions(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, static=STATIC_DIR)
    body = c.get("/api/search", params={"q": '"arte combinatoria"'}).json()
    assert body["total"] == 1 and "<mark>arte combinatoria</mark>" in body["hits"][0]["snippet"]
    assert c.get("/api/search", params={"q": "de -nature"}).json()["total"] == 1
    r = c.get("/api/search", params={"q": "-de"})
    assert r.status_code == 200 and r.json()["total"] == 0
    params = c.get("/openapi.json").json()["paths"]["/api/search"]["get"]["parameters"]
    assert "quotes" in next(p for p in params if p["name"] == "q")["description"]
    assert '"double quotes"' in c.get("/llms.txt").text


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
    assert re.search(r'<script src="/static/boot\.js\?v=[0-9a-f]{12}"></script>', r.text)
    assert "<script>" not in r.text
    assert "no-js" in c.get("/static/boot.js").text
    robots = c.get("/robots.txt")
    assert robots.status_code == 200 and robots.headers["content-type"].startswith("text/plain")
    assert "Disallow: /manifests/" in robots.text


def test_shell_is_stamped_per_route_and_serves_discovery_files(store_path, tmp_path) -> None:
    c = TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))
    home = c.get("/").text
    assert '<link rel="canonical" href="https://leibnizlegible.com/"' in home
    assert 'property="og:image" content="https://leibnizlegible.com/static/og.png"' in home
    assert "<!--ll:ssr-->" not in home and "<script>" not in home
    about = c.get("/about")
    assert "<title>About — Leibniz Legible</title>" in about.text
    assert 'href="https://leibnizlegible.com/about"' in about.text
    # a work: title, description, catalogue and page links rendered server side
    w = c.get(f"/work/{W1}")
    assert w.status_code == 200 and 'id="ssr"' in w.text and f'href="/page/{W1}:0001"' in w.text
    assert f'href="https://leibnizlegible.com/work/{W1}"' in w.text
    # a page: the machine text is in the HTML, with its own ETag
    p = c.get(f"/page/{W1}:0001")
    assert p.status_code == 200 and "The machine reads it as" in p.text
    assert p.headers["ETag"] != w.headers["ETag"]
    again = c.get(f"/page/{W1}:0001", headers={"If-None-Match": p.headers["ETag"]})
    assert again.status_code == 304
    # unknown ids are real 404s that still carry the shell for the viewer
    assert c.get("/work/nope").status_code == 404 and "Leibniz Legible" in c.get("/work/nope").text
    assert c.get("/page/nope:0001").status_code == 404
    # discovery files
    assert c.get("/favicon.ico").headers["content-type"].startswith("image/")
    assert c.get("/llms.txt").text.startswith("# Leibniz Legible")
    sm = c.get("/sitemap.xml")
    assert sm.headers["content-type"].startswith("application/xml")
    assert f"<loc>https://leibnizlegible.com/work/{W1}</loc>" in sm.text
    assert "Sitemap: https://leibnizlegible.com/sitemap.xml" in c.get("/robots.txt").text
    assert c.get("/openapi.json").status_code == 200 and c.get("/docs").status_code == 404


def test_shell_uses_base_url_when_given(store_path, tmp_path) -> None:
    c = TestClient(
        create_app(store_path, search=None, static_dir=STATIC_DIR, base_url="https://x.org")
    )
    assert 'href="https://x.org/about"' in c.get("/about").text
    assert "<loc>https://x.org/</loc>" in c.get("/sitemap.xml").text


def test_shell_names_the_game_only_when_switched_on(store_path, tmp_path) -> None:
    game = "https://calculemus.leibnizlegible.com"
    off = TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))
    for route in ("/", "/about"):
        text = off.get(route).text
        # "e.g. calculemus" in the search box is Leibniz's word, not the game
        assert "data-calculemus-url" not in text and "Calculemus" not in text and game not in text
    on = TestClient(
        create_app(store_path, search=None, static_dir=STATIC_DIR, calculemus_url=game + "/")
    )
    for route in ("/", "/about"):
        assert f'data-calculemus-url="{game}"' in on.get(route).text  # trailing slash stripped


# ---- plain-text exports ----------------------------------------------------- #


def _texts(store_path: Path, page_id: str) -> list[str]:
    """What /api/pages shows for a page: the latest run per line, lines with text."""
    conn = db.connect(store_path)
    try:
        return [ln.text for ln in latest_lines(conn, page_id) if ln.text]
    finally:
        conn.close()


def _split(text: str) -> tuple[list[str], list[str]]:
    """(header lines, body lines) of an export: the header ends at the first blank line."""
    head, _, body = text.partition("\n\n")
    return head.split("\n"), body.splitlines()


def test_page_text_export(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get(f"/api/pages/{W1}:0001/text")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/plain; charset=utf-8"
    # the id's colon is not a file-name character everywhere (Windows)
    assert r.headers["content-disposition"] == (
        'attachment; filename="leibniz-legible_00068642_0001.txt"'
    )
    assert r.headers["cache-control"] == api.CACHE_HEADERS["Cache-Control"]
    head, body = _split(r.text)
    assert all(row.startswith("# ") for row in head)
    # the header, in the documented order
    expected = [
        "# Leibniz Legible — https://leibnizlegible.com",
        f"# Page: https://leibnizlegible.com/page/{W1}:0001",
        "# Title: LH 4,6,18 (shelfmark LH IV, 6, 18)",
        f"# Folio 1r, page id {W1}:0001",
        f"# Original at the GWLB: https://digitale-sammlungen.gwlb.de/resolve?id={W1}",
        f"# Source image: https://digitale-sammlungen.gwlb.de/iiif/{W1}/ptif/1.ptif",
        "# Model: leibniz-htr-v2@v2, run 3",  # the re-read line: the later run first
        "# Model: FoNDUE-GD_v2_ft_Leibniz@v1, run 2",
        "# Lines: 3 recognised, mean confidence 0.74",
        f"# {attr.HONESTY}",
        f"# {attr.TEXT_LICENCE}",
        f"# {attr.WORDING_RULE}",
    ]
    at = [next(i for i, row in enumerate(head) if row.startswith(e)) for e in expected]
    assert at == sorted(at)
    assert "— 1 line, status machine" in head[at[6]] and "— 2 lines" in head[at[7]]
    assert 'say "the machine reads it as …", never "Leibniz wrote"' in r.text
    # the body is exactly what /api/pages shows, in reading order
    assert body == _texts(store_path, f"{W1}:0001")
    assert body == [ln["text"] for ln in c.get(f"/api/pages/{W1}:0001").json()["lines"]]
    assert body[0] == "Calculemus inquit Leibnitius."  # the later run's reading


def test_page_text_export_tsv(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get(f"/api/pages/{W1}:0001/text", params={"format": "tsv"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/tab-separated-values; charset=utf-8"
    assert r.headers["content-disposition"].endswith('filename="leibniz-legible_00068642_0001.tsv"')
    head, body = _split(r.text)
    txt_head, _ = _split(c.get(f"/api/pages/{W1}:0001/text").text)
    assert head[: len(txt_head)] == txt_head  # the same header, plus the column note
    assert body[0].split("\t") == ["line_id", "line_seq", "conf", "status", "text"]
    rows = [row.split("\t") for row in body[1:]]
    assert all(len(row) == 5 for row in rows)
    assert [row[0] for row in rows] == [f"{W1}:0001:000", f"{W1}:0001:001", f"{W1}:0001:002"]
    assert [row[1] for row in rows] == ["0", "1", "2"]
    assert [row[2] for row in rows] == ["0.95", "0.72", "0.55"]
    assert {row[3] for row in rows} == {"machine"}
    assert [row[4] for row in rows] == _texts(store_path, f"{W1}:0001")


def test_page_text_export_of_a_page_without_text(store_path, tmp_path) -> None:
    r = _client(store_path, tmp_path).get(f"/api/pages/{W1}:0003/text")
    head, body = _split(r.text)
    assert r.status_code == 200 and body == []
    assert "# Lines: 0 recognised (skipped: no_lines)" in head
    assert not any(row.startswith("# Model:") for row in head)


def test_text_export_keeps_one_output_line_per_line(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    conn.execute(
        "UPDATE lines SET text = ? WHERE page_id = ? AND line_seq = 1",
        ("ab\tcd\nef", f"{W2}:0001"),
    )
    conn.commit()
    conn.close()
    c = _client(store_path, tmp_path)
    _, body = _split(c.get(f"/api/pages/{W2}:0001/text").text)
    assert body == ["La Monadologie et les principes", "ab\tcd ef"]
    _, rows = _split(c.get(f"/api/pages/{W2}:0001/text", params={"format": "tsv"}).text)
    assert rows[2].split("\t")[1:] == ["1", "0.86", "machine", "ab cd ef"]


def test_work_text_export(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get(f"/api/works/{W1}/text")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/plain; charset=utf-8"
    assert r.headers["content-disposition"] == 'attachment; filename="leibniz-legible_00068642.txt"'
    assert "content-length" not in r.headers  # streamed
    head, body = _split(r.text)
    assert f"# Work: https://leibnizlegible.com/work/{W1}" in head
    assert "# Lines: 5 recognised on 2 of 3 pages, mean confidence 0.78" in head
    for line in (attr.HONESTY, attr.TEXT_LICENCE, attr.WORDING_RULE):
        assert f"# {line}" in head
    # one heading per page, in canvas order
    headings = [row for row in body if row.startswith("## ")]
    assert headings == [
        f"## Folio 1r — {W1}:0001",
        f"## Folio 1v — {W1}:0002",
        f"## Folio 2r — {W1}:0003",
    ]
    blocks = {}
    for row in body:
        if row.startswith("## "):
            blocks[row.rsplit(" — ", 1)[1]] = current = []
        elif row:
            current.append(row)
    for pid in (f"{W1}:0001", f"{W1}:0002"):
        assert [row for row in blocks[pid] if not row.startswith("# ")] == _texts(store_path, pid)
        assert blocks[pid][0].startswith("# Source image: https://digitale-sammlungen.gwlb.de/")
    assert blocks[f"{W1}:0001"][1].startswith("# Model: leibniz-htr-v2@v2, run 3")
    # a page without recognised text is a one-line note
    assert blocks[f"{W1}:0003"] == ["# No recognised text on this page (skipped: no_lines)."]
    # a page with no folio label is named by its canvas
    other = c.get(f"/api/works/{W2}/text", params={"format": "tsv"})
    assert other.headers["content-type"] == "text/tab-separated-values; charset=utf-8"
    _, rows = _split(other.text)
    assert rows[0] == "\t".join(api.TSV_COLUMNS) and f"## Canvas 1 — {W2}:0001" in rows
    data = [row.split("\t") for row in rows[1:] if not row.startswith("#")]
    assert [row[4] for row in data] == _texts(store_path, f"{W2}:0001")


def test_work_text_export_streams_page_by_page(store_path, monkeypatch) -> None:
    read: list[str] = []

    def counting(conn, page_id):
        read.append(page_id)
        return latest_lines(conn, page_id)

    monkeypatch.setattr(api, "latest_lines", counting)
    conn = db.connect(store_path)
    work, pages = db.get_work(conn, W1), db.get_pages(conn, W1)
    summaries = api.line_summaries_by_page(conn, W1)
    conn.close()
    chunks = api._work_text(store_path, api.SITE_URL, work, pages, summaries, "txt")
    assert next(chunks).startswith("# Leibniz Legible") and read == []  # header before any page
    rest = list(chunks)
    assert len(rest) == len(pages) and read == [p.id for p in pages]
    assert rest[0].startswith(f"## Folio 1r — {W1}:0001") and rest[1].startswith("\n## Folio 1v")
    # the route hands that generator to a streaming response
    app = create_app(store_path, search=None, static_dir=None)
    route = next(r for r in app.routes if getattr(r, "path", "") == "/api/works/{work_id}/text")
    assert isinstance(route.endpoint(work_id=W1, fmt="txt"), StreamingResponse)


def test_text_exports_404_and_formats(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    assert c.get("/api/pages/nope:0001/text").status_code == 404
    assert c.get("/api/works/nope/text").status_code == 404
    assert c.get("/api/works/nope/text").json() == {"detail": "work nope not found"}
    assert c.get(f"/api/pages/{W1}:0001/text", params={"format": "xml"}).status_code == 422
    # the JSON routes the exports nest under are not shadowed
    assert c.get(f"/api/pages/{W1}:0001").headers["content-type"] == "application/json"
    assert c.get(f"/api/works/{W1}").json()["work_id"] == W1


def test_text_exports_are_documented_and_crawlable(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, static=STATIC_DIR)
    spec = c.get("/openapi.json").json()["paths"]
    for path in ("/api/pages/{page_id}/text", "/api/works/{work_id}/text"):
        get = spec[path]["get"]
        assert get["summary"] and "format" in [p["name"] for p in get["parameters"]]
        assert {"text/plain", "text/tab-separated-values"} <= set(
            get["responses"]["200"]["content"]
        )
        assert "404" in get["responses"]
    robots = RobotFileParser()
    robots.parse(c.get("/robots.txt").text.splitlines())
    for url in (f"/api/pages/{W1}:0001/text", f"/api/works/{W1}/text"):
        assert robots.can_fetch("*", f"https://leibnizlegible.com{url}")
    assert not robots.can_fetch("*", f"https://leibnizlegible.com/manifests/{W1}")
    llms = c.get("/llms.txt").text
    assert "/api/pages/{page_id}/text" in llms and "/api/works/{work_id}/text" in llms


def test_server_rendered_pages_link_the_text_exports(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, static=STATIC_DIR)
    page = c.get(f"/page/{W1}:0001").text
    assert f'<a href="/api/pages/{W1}:0001/text" download>Download text</a>' in page
    skipped = c.get(f"/page/{W1}:0003").text  # nothing to download
    assert f"/api/pages/{W1}:0003/text" not in skipped and "Download text" not in skipped
    work = c.get(f"/work/{W1}").text
    assert f'<a href="/api/works/{W1}/text" download>Download the text of this work</a>' in work


# ---- the browse index (W3) ----------------------------------------------------- #


def _link_letters(store_path: Path) -> None:
    """Three catalogue records on the letter convolute W2, as the katalog writes them."""
    conn = db.connect(store_path)
    for rid, absender, adressat, titel in (
        ("k-1", "Hansen (KorrespDB) (GND)", "Leibniz (GND)", "Friedrich Adolf Hansen an Leibniz"),
        ("k-2", "Leibniz (GND)", "Hansen (KorrespDB) (GND)", "Leibniz an Friedrich Adolf Hansen"),
        ("k-3", "Leibniz (GND)", "Tschirnhaus (KorrespDB) (GND)", "Leibniz an Tschirnhaus"),
    ):
        meta = {"absender": absender, "adressat": adressat, "titel": titel, "gwlb_ids": [W2]}
        db.upsert_katalog_record(conn, db.KatalogRecord(record_id=rid, metadata=meta))
        db.upsert_crosswalk(conn, db.CrosswalkMatch(rid, W2, "gwlb_link", 1.0))
    conn.commit()
    conn.close()


def test_works_list_rows_and_groups(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    r = c.get("/api/works")
    assert r.status_code == 200 and r.headers["content-type"] == "application/json"
    assert r.headers["cache-control"] == api.DAY_CACHE["Cache-Control"]
    body = r.json()
    assert (body["n_works"], body["n_pages"]) == (2, 4)
    assert set(body["attribution"]) == {"images", "katalog", "transcriptions"}
    assert "machine transcriptions, not an edition" in body["note"]
    manuscript, letters = body["works"]  # by work id
    assert manuscript == {
        "work_id": W1,
        "set": "LeibnizHandschriften",
        "title": "LH 4,6,18",
        "shelfmark": "LH IV, 6, 18",
        "shelfmarks": ["LH IV, 6, 18"],
        "family": "LH",
        "section": "4",  # the Roman numeral read as its number
        "section_label": "LH 4",  # no phrase in the fixture's title
        "label": "LH IV, 6, 18",
        "n_canvases": 3,
        "has_katalog": True,
    }
    assert (letters["work_id"], letters["family"], letters["section"]) == (W2, "LBr", "LBr")
    assert letters["label"] == "LBr. 464" and letters["has_katalog"] is False  # no records
    assert [(g["family"], g["name"], g["n_works"], g["n_pages"]) for g in body["groups"]] == [
        ("LH", "Handschriften (LH)", 1, 3),
        ("LBr", "Briefwechsel (LBr)", 1, 1),
    ]
    assert body["groups"][0]["sections"] == [
        {
            "section": "4",
            "anchor": "lh-4",
            "label": "LH 4",
            "title": "LH 4",
            "n_works": 1,
            "n_pages": 3,
            "entries": [W1],
        }
    ]
    lbr = body["groups"][1]["sections"][0]
    assert (lbr["anchor"], lbr["entries"], lbr["by_number"]) == ("lbr", [W2], [W2])


def test_works_list_names_letters_by_correspondent_once_per_process(store_path, tmp_path) -> None:
    _link_letters(store_path)
    c = _client(store_path, tmp_path)
    letters = c.get("/api/works").json()["works"][1]
    assert letters["label"] == "Hansen" and letters["has_katalog"] is True
    assert letters["shelfmark"] == "LBr. 464" and letters["section_label"] == "Briefwechsel (LBr)"
    # built on first use and kept: the works table changes only with a corpus run
    conn = db.connect(store_path)
    db.upsert_work(conn, db.Work("NEW", "LeibnizMarginalien", shelfmarks=["Leibn. Marg. 9"]))
    conn.commit()
    conn.close()
    assert c.get("/api/works").json()["n_works"] == 2
    assert c.get("/api/works", params={"family": "Marg"}).json()["n_works"] == 0
    fresh = _client(store_path, tmp_path)  # a restart sees the new work
    assert [g["family"] for g in fresh.get("/api/works").json()["groups"]] == ["LH", "LBr", "Marg"]


def test_works_list_filters(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    letters = c.get("/api/works", params={"set": "LeibnizBriefwechsel"})
    assert letters.headers["cache-control"] == api.DAY_CACHE["Cache-Control"]
    assert [w["work_id"] for w in letters.json()["works"]] == [W2]
    assert [g["family"] for g in letters.json()["groups"]] == ["LBr"]
    manuscripts = c.get("/api/works", params={"family": "LH"}).json()
    assert [w["work_id"] for w in manuscripts["works"]] == [W1] and manuscripts["n_pages"] == 3
    both = c.get("/api/works", params={"family": "LH", "set": "LeibnizBriefwechsel"}).json()
    assert both["works"] == [] and both["groups"] == [] and both["n_works"] == 0
    assert c.get("/api/works", params={"set": "nope"}).json()["works"] == []
    assert c.get("/api/works", params={"family": "Marg"}).json()["groups"] == []
    assert c.get("/api/works", params={"family": "nope"}).status_code == 422


def test_works_list_does_not_shadow_the_work_routes(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path)
    assert "groups" in c.get("/api/works").json()
    one = c.get(f"/api/works/{W1}").json()
    assert one["work_id"] == W1 and "groups" not in one and len(one["pages"]) == 3
    # the work says where it sits in the index: the work page's way back
    assert one["browse"] == {
        "family": "LH",
        "section": "4",
        "anchor": "lh-4",
        "label": "LH 4",
        "title": "LH 4",
    }
    assert c.get(f"/api/works/{W2}").json()["browse"]["anchor"] == "lbr"
    text = c.get(f"/api/works/{W1}/text")
    assert text.status_code == 200 and text.headers["content-type"].startswith("text/plain")
    assert c.get("/api/works/nope").status_code == 404
    slash = c.get("/api/works/")  # redirected to the list, never read as an empty id
    assert slash.status_code == 200 and "groups" in slash.json()


def test_works_list_is_documented_and_crawlable(store_path, tmp_path) -> None:
    c = _client(store_path, tmp_path, static=STATIC_DIR)
    get = c.get("/openapi.json").json()["paths"]["/api/works"]["get"]
    assert get["summary"] and {p["name"] for p in get["parameters"]} == {"set", "family"}
    lines = c.get("/robots.txt").text.splitlines()
    assert "Allow: /api/works" in lines and "Allow: /api/works/" in lines
    assert lines.index("Allow: /api/works") < lines.index("Disallow: /api/")
    robots = RobotFileParser()
    robots.parse(lines)
    for url in ("/api/works", "/api/works?family=LBr", f"/api/works/{W1}", "/browse"):
        assert robots.can_fetch("*", f"https://leibnizlegible.com{url}"), url
    assert not robots.can_fetch("*", "https://leibnizlegible.com/api/other")
    llms = c.get("/llms.txt").text
    assert "`GET /api/works`:" in llms and "https://leibnizlegible.com/browse" in llms


def test_browse_page_is_server_rendered_with_a_link_per_work(store_path, tmp_path) -> None:
    _link_letters(store_path)
    c = TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))
    r = c.get("/browse")
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-cache"
    assert "<title>Browse by shelfmark — Leibniz Legible</title>" in r.text
    assert '<link rel="canonical" href="https://leibnizlegible.com/browse"' in r.text
    assert 'id="ssr"' in r.text and "<!--ll:ssr-->" not in r.text
    # every family and section, each under its anchor, and a link per work
    assert "<h2>Handschriften (LH)</h2>" in r.text and "<h2>Briefwechsel (LBr)</h2>" in r.text
    assert '<details id="lh-4"><summary>LH 4 (1 work, 3 page images)</summary>' in r.text
    assert (
        '<details id="lbr"><summary>Briefwechsel (LBr) (1 work, 1 page image)</summary>' in r.text
    )
    assert f'<li><a href="/work/{W1}">LH IV, 6, 18</a></li>' in r.text
    assert f'<li><a href="/work/{W2}">Hansen</a> · LBr. 464</li>' in r.text
    assert "machine transcriptions, not an edition" in r.text
    # the shell's nav knows the page; the stamped body is revalidated like the others
    assert '<a href="/browse" data-nav="browse" data-i18n="nav.browse">Browse</a>' in r.text
    again = c.get("/browse", headers={"If-None-Match": r.headers["ETag"]})
    assert again.status_code == 304
    assert "<loc>https://leibnizlegible.com/browse</loc>" in c.get("/sitemap.xml").text


def test_work_page_links_back_into_the_browse_index(store_path, tmp_path) -> None:
    c = TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))
    work = c.get(f"/work/{W1}").text
    assert (
        '<nav aria-label="Breadcrumb"><a href="/browse">Browse</a> › '
        '<a href="/browse#lh-4">LH 4</a></nav>' in work
    )
    letters = c.get(f"/work/{W2}").text
    assert '<a href="/browse#lbr">Briefwechsel (LBr)</a>' in letters


# ---- asset versioning --------------------------------------------------------- #


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def test_shell_names_its_assets_by_content_hash(store_path, tmp_path) -> None:
    c = TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))
    for route in ("/", "/about", f"/work/{W1}", f"/page/{W1}:0001"):
        text = c.get(route).text
        for name in api.VERSIONED_ASSETS:
            assert f'"/static/{name}?v={_digest(STATIC_DIR / name)}"' in text, (route, name)
            assert f'"/static/{name}"' not in text
    versioned = f"/static/style.css?v={_digest(STATIC_DIR / 'style.css')}"
    assert c.get(versioned).text == (STATIC_DIR / "style.css").read_text(encoding="utf-8")


def test_asset_versions_follow_the_file_content(store_path, tmp_path) -> None:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text(
        '<!doctype html><html lang="en"><title>Leibniz Legible</title>'
        '<link rel="stylesheet" href="/static/style.css" />'
        '<script src="/static/boot.js"></script>'
        '<script type="module" src="/static/app.js"></script></html>',
        encoding="utf-8",
    )
    for name in api.VERSIONED_ASSETS:
        (static / name).write_text(f"/* {name} v1 */", encoding="utf-8")

    def versions(client: TestClient) -> dict[str, str]:
        found = re.findall(
            r'/static/(style\.css|boot\.js|app\.js)\?v=([0-9a-f]{12})"', client.get("/").text
        )
        return dict(found)

    before = TestClient(create_app(store_path, search=None, static_dir=static))
    first = versions(before)
    assert first == {name: _digest(static / name) for name in api.VERSIONED_ASSETS}
    (static / "style.css").write_text("/* style.css v2 */", encoding="utf-8")
    assert versions(before) == first  # computed once, at startup
    after = versions(TestClient(create_app(store_path, search=None, static_dir=static)))
    assert after["style.css"] != first["style.css"]
    assert after["style.css"] == _digest(static / "style.css")
    assert after["boot.js"] == first["boot.js"] and after["app.js"] == first["app.js"]
