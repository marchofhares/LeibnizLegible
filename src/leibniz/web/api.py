"""The JSON API + viewer host (Phases D1/D2).

Routes (all read-only; the store is opened per request):

* ``GET /api/search``          — typo-/orthography-tolerant page search (D1)
* ``GET /api/works/{id}``      — a work: pages, katalog records, attribution
* ``GET /api/pages/{id}``      — a page: lines with geometry, text, confidence,
  status and provenance (SPECS §4.5), prev/next
* ``GET /api/stats``           — corpus counts for the About page
* ``GET /manifests/{work}``    — IIIF Presentation 3 manifest (D7)
* ``GET /annotations/{page}``  — W3C AnnotationPage with the page's lines (D7)
* ``/``, ``/search``, ``/work/…``, ``/page/…``, ``/about`` — the static viewer

Build it with :func:`create_app`; ``leibniz serve`` wraps it in uvicorn.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse

from leibniz import __version__, db
from leibniz.search.backend import SearchBackend, SearchQuery
from leibniz.search.documents import aa_ref_label, corpus_stats, latest_lines
from leibniz.web import attribution as attr
from leibniz.web import iiif
from leibniz.web.geometry import baseline_points, line_bbox, polygon_points

STATIC_DIR = Path(__file__).parent / "static"
INDEX_ROUTES = ("/", "/search", "/about", "/work/{work_id}", "/page/{page_id}")
CACHE_HEADERS = {"Cache-Control": "public, max-age=300"}


def _open(db_path: str | Path) -> sqlite3.Connection:
    p = Path(db_path)
    if str(db_path) != ":memory:" and not p.exists():
        raise HTTPException(503, f"store not found: {db_path}")
    return db.connect(db_path)


def _run_dates(conn: sqlite3.Connection, run_ids: set[int]) -> dict[int, str]:
    if not run_ids:
        return {}
    marks = ",".join("?" for _ in run_ids)
    rows = conn.execute(
        f"SELECT run_id, started_at, finished_at FROM runs WHERE run_id IN ({marks})",
        list(run_ids),
    ).fetchall()
    return {r["run_id"]: (r["finished_at"] or r["started_at"] or "") for r in rows}


def _run_info(conn: sqlite3.Connection, run_id: int | None) -> dict | None:
    if run_id is None:
        return None
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        return None
    return {
        "run_id": row["run_id"],
        "stage": row["stage"],
        "model": row["model"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "git_sha": row["git_sha"],
    }


def _katalog_for_work(conn: sqlite3.Connection, work_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT c.katalog_record_id, c.match_method, c.match_conf, c.page_range,
               k.metadata, k.aa_refs, k.shelfmark_refs
          FROM crosswalk c JOIN katalog_records k ON k.record_id = c.katalog_record_id
         WHERE c.work_id = ? ORDER BY c.match_conf DESC, c.katalog_record_id
        """,
        (work_id,),
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        meta = json.loads(r["metadata"]) if r["metadata"] else {}
        aa_refs = json.loads(r["aa_refs"]) if r["aa_refs"] else []
        out.append(
            {
                "record_id": r["katalog_record_id"],
                "title": meta.get("title") or meta.get("titel"),
                "incipit": meta.get("incipit"),
                "date": meta.get("datum") or meta.get("date"),
                "correspondent": meta.get("absender") or meta.get("correspondent"),
                "place": meta.get("ort"),
                "textart": meta.get("textart"),
                "shelfmarks": json.loads(r["shelfmark_refs"]) if r["shelfmark_refs"] else [],
                "aa_refs": aa_refs,
                "aa_labels": [lab for ref in aa_refs if (lab := aa_ref_label(ref))],
                "url": meta.get("url") or meta.get("record_url"),
                "match_method": r["match_method"],
                "match_conf": r["match_conf"],
                "page_range": r["page_range"],
            }
        )
    return out


def _page_summary(conn: sqlite3.Connection, page: db.Page) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) AS n, AVG(conf) AS c FROM lines l WHERE l.page_id = ? "
        "AND l.text IS NOT NULL AND l.text != '' AND l.run_id = "
        "(SELECT MAX(run_id) FROM lines x WHERE x.page_id = l.page_id AND x.line_seq = l.line_seq)",
        (page.id,),
    ).fetchone()
    return {
        "page_id": page.id,
        "seq": page.seq,
        "label": page.label,
        "thumb_url": page.thumb_url,
        "status": page.status,
        "skip_reason": page.skip_reason,
        "n_lines": int(row["n"] or 0),
        "mean_conf": round(row["c"], 4) if row["c"] is not None else None,
    }


def _line_dict(ln: db.Line, page: db.Page, run_dates: dict[int, str]) -> dict:
    return {
        "line_id": ln.id,
        "line_seq": ln.line_seq,
        "text": ln.text,
        "conf": ln.conf,
        "status": ln.status,
        "lang": ln.lang,
        "model": ln.model,
        "run_id": ln.run_id,
        "run_at": run_dates.get(ln.run_id or -1),
        "baseline": baseline_points(ln),
        "polygon": polygon_points(ln),
        "bbox": line_bbox(ln, page),
        "source": ln.source,
    }


def create_app(
    db_path: str | Path = db.DEFAULT_DB_PATH,
    *,
    search: SearchBackend | None = None,
    static_dir: Path | None = STATIC_DIR,
    base_url: str | None = None,
) -> FastAPI:
    """Build the FastAPI application over a store (+ optional search backend)."""
    app = FastAPI(
        title="Leibniz Legible API",
        version=__version__,
        description=(
            "Machine transcriptions of the digitized Leibniz Nachlass with per-line "
            "confidence and provenance. Not an edition."
        ),
    )
    state: dict = {"stats": None}

    def base(request: Request) -> str:
        return (base_url or str(request.base_url)).rstrip("/")

    # ---- API ------------------------------------------------------------- #
    @app.get("/api/stats")
    def api_stats() -> JSONResponse:
        if state["stats"] is None:
            meta = search.meta() if search is not None else {}
            stats = meta.get("stats")
            if not stats:
                conn = _open(db_path)
                try:
                    stats = corpus_stats(conn)
                finally:
                    conn.close()
            stats = dict(stats)
            stats["version"] = __version__
            stats["backend"] = search.name if search is not None else None
            stats["index_built_at"] = meta.get("built_at")
            stats.setdefault("model", None)
            state["stats"] = stats
        return JSONResponse(state["stats"], headers=CACHE_HEADERS)

    @app.get("/api/search")
    def api_search(
        q: str = Query("", max_length=500),
        set: str | None = Query(None, alias="set"),  # noqa: A002 — the API's public name
        lang: str | None = None,
        stratum: str | None = None,
        min_conf: float | None = Query(None, ge=0.0, le=1.0),
        work: str | None = None,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
    ) -> JSONResponse:
        if search is None:
            raise HTTPException(503, "search index not configured (run `leibniz index build`)")
        res = search.search(
            SearchQuery(
                q=q,
                set_name=set,
                lang=lang,
                stratum=stratum,
                min_conf=min_conf,
                work_id=work,
                page=page,
                limit=limit,
            )
        )
        return JSONResponse(res.to_dict(), headers=CACHE_HEADERS)

    @app.get("/api/works/{work_id}")
    def api_work(work_id: str) -> JSONResponse:
        conn = _open(db_path)
        try:
            work = db.get_work(conn, work_id)
            if work is None:
                raise HTTPException(404, f"work {work_id} not found")
            pages = db.get_pages(conn, work_id)
            body = {
                "work_id": work.gwlb_object_id,
                "set": work.set_name,
                "title": work.title,
                "shelfmarks": list(work.shelfmarks or []),
                "manifest_url": work.manifest_url,
                "gwlb_url": attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id),
                "n_canvases": work.n_canvases,
                "iiif_manifest": f"/manifests/{work.gwlb_object_id}",
                "pages": [_page_summary(conn, p) for p in pages],
                "katalog": _katalog_for_work(conn, work_id),
                "attribution": attr.attribution(),
            }
        finally:
            conn.close()
        return JSONResponse(body, headers=CACHE_HEADERS)

    @app.get("/api/pages/{page_id}")
    def api_page(page_id: str) -> JSONResponse:
        conn = _open(db_path)
        try:
            page = db.get_page(conn, page_id)
            if page is None:
                raise HTTPException(404, f"page {page_id} not found")
            work = db.get_work(conn, page.work_id)
            lines = latest_lines(conn, page_id)
            run_dates = _run_dates(conn, {ln.run_id for ln in lines if ln.run_id is not None})
            neighbours = conn.execute(
                "SELECT page_id, seq FROM pages WHERE work_id = ? AND seq IN (?, ?)",
                (page.work_id, page.seq - 1, page.seq + 1),
            ).fetchall()
            prev_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq - 1), None)
            next_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq + 1), None)
            confs = [ln.conf for ln in lines if ln.conf is not None and ln.text]
            run_ids = [ln.run_id for ln in lines if ln.run_id is not None]
            body = {
                "page_id": page.id,
                "work_id": page.work_id,
                "work_title": work.title if work else None,
                "set": work.set_name if work else None,
                "shelfmarks": list(work.shelfmarks or []) if work else [],
                "seq": page.seq,
                "label": page.label,
                "canvas_id": page.canvas_id,
                "width": page.width,
                "height": page.height,
                "delivery": page.delivery,
                "image_service_url": page.image_service_url,
                "image_url": page.image_url,
                "thumb_url": page.thumb_url,
                "status": page.status,
                "skip_reason": page.skip_reason,
                "prev_page_id": prev_id,
                "next_page_id": next_id,
                "manifest_url": f"/manifests/{page.work_id}",
                "annotations_url": f"/annotations/{page.id}",
                "gwlb_url": attr.GWLB_RESOLVE.format(work_id=page.work_id),
                "run": _run_info(conn, max(run_ids) if run_ids else None),
                "stats": {
                    "n_lines": len([ln for ln in lines if ln.text]),
                    "mean_conf": round(sum(confs) / len(confs), 4) if confs else None,
                },
                "lines": [_line_dict(ln, page, run_dates) for ln in lines if ln.text],
                "honesty": attr.HONESTY,
                "attribution": attr.attribution(),
            }
        finally:
            conn.close()
        return JSONResponse(body, headers=CACHE_HEADERS)

    # ---- IIIF (D7) -------------------------------------------------------- #
    @app.get("/manifests/{work_id}")
    def manifest(work_id: str, request: Request) -> JSONResponse:
        conn = _open(db_path)
        try:
            work = db.get_work(conn, work_id)
            if work is None:
                raise HTTPException(404, f"work {work_id} not found")
            pages = db.get_pages(conn, work_id)
            counts = {
                r["page_id"]: r["n"]
                for r in conn.execute(
                    "SELECT l.page_id, COUNT(*) AS n FROM lines l WHERE l.page_id IN "
                    "(SELECT page_id FROM pages WHERE work_id = ?) AND l.text IS NOT NULL "
                    "AND l.run_id = (SELECT MAX(run_id) FROM lines x WHERE x.page_id = l.page_id "
                    "AND x.line_seq = l.line_seq) GROUP BY l.page_id",
                    (work_id,),
                )
            }
            body = iiif.build_manifest(work, pages, base_url=base(request), line_counts=counts)
        finally:
            conn.close()
        return JSONResponse(body, media_type="application/ld+json", headers=CACHE_HEADERS)

    @app.get("/annotations/{page_id}")
    def annotations(page_id: str, request: Request) -> JSONResponse:
        conn = _open(db_path)
        try:
            page = db.get_page(conn, page_id)
            if page is None:
                raise HTTPException(404, f"page {page_id} not found")
            lines = latest_lines(conn, page_id)
            dates = _run_dates(conn, {ln.run_id for ln in lines if ln.run_id is not None})
            body = iiif.build_annotation_page(page, lines, base_url=base(request), run_dates=dates)
        finally:
            conn.close()
        return JSONResponse(body, media_type="application/ld+json", headers=CACHE_HEADERS)

    # ---- viewer (D2) ------------------------------------------------------ #
    index_html = static_dir / "index.html" if static_dir else None
    if index_html is not None and index_html.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        def serve_index() -> FileResponse:
            return FileResponse(index_html, media_type="text/html")

        def serve_index_work(work_id: str) -> FileResponse:
            return serve_index()

        def serve_index_page(page_id: str) -> FileResponse:
            return serve_index()

        handlers = {"/work/{work_id}": serve_index_work, "/page/{page_id}": serve_index_page}
        for route in INDEX_ROUTES:
            app.add_api_route(
                route, handlers.get(route, serve_index), methods=["GET"], include_in_schema=False
            )

    return app


__all__ = ["INDEX_ROUTES", "STATIC_DIR", "create_app"]
