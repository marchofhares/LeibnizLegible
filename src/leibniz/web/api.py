"""The JSON API + viewer host (Phases D1/D2).

Routes (all read-only; the store is opened per request, read-only):

* ``GET /api/search``          — typo-/orthography-tolerant page search (D1)
* ``GET /api/works/{id}``      — a work: pages, katalog records, attribution
* ``GET /api/pages/{id}``      — a page: lines with geometry, text, confidence,
  status and provenance (SPECS §4.5), prev/next
* ``GET /api/stats``           — corpus counts for the About page
* ``GET /manifests/{work}``    — IIIF Presentation 3 manifest (D7)
* ``GET /annotations/{page}``  — W3C AnnotationPage with the page's lines (D7)
* ``GET /healthz``             — liveness for the process manager / uptime monitor
* ``/``, ``/search``, ``/work/…``, ``/page/…``, ``/about`` — the viewer shell,
  stamped per route with its title, description, canonical URL and, for a work
  or a page, a server-rendered summary (the catalogue entries, the page list,
  the machine text) so crawlers and readers without JavaScript see the content
* ``/robots.txt``, ``/sitemap.xml``, ``/llms.txt``, ``/favicon.ico`` — the
  static viewer's discovery files

Build it with :func:`create_app`; ``leibniz serve`` wraps it in uvicorn. The
public-deployment middleware (gzip, CORS for the IIIF consumers, a per-client
rate limit, security headers) is applied here so every way of running the app
gets it, whatever sits in front.
"""

from __future__ import annotations

import hashlib
import html
import json
import sqlite3
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

from leibniz import __version__, db
from leibniz.search.backend import SearchBackend, SearchQuery
from leibniz.search.documents import (
    ROMAN,
    aa_ref_label,
    corpus_stats,
    latest_lines,
    line_summaries_by_page,
)
from leibniz.web import attribution as attr
from leibniz.web import iiif
from leibniz.web.geometry import baseline_points, line_bbox, polygon_points
from leibniz.web.images import ImageSource
from leibniz.web.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

STATIC_DIR = Path(__file__).parent / "static"
INDEX_ROUTES = ("/", "/search", "/about", "/work/{work_id}", "/page/{page_id}")
CACHE_HEADERS = {"Cache-Control": "public, max-age=300"}
NO_STORE = {"Cache-Control": "no-store"}
DAY_CACHE = {"Cache-Control": "public, max-age=86400"}

# The public origin written into the shell (canonical, og:url, og:image, the
# structured data). ``create_app(base_url=…)`` rewrites it for another host.
SITE_URL = "https://leibnizlegible.com"
SITE_TITLE = "Leibniz Legible"
SITE_DESCRIPTION = (
    "An access layer for the digitized Leibniz Nachlass: machine transcription with "
    "per-line confidence and provenance, searchable and browsable. Not an edition."
)
SSR_MARK = "<!--ll:ssr-->"
SSR_MAX_LINES = 400


def _open(db_path: str | Path) -> sqlite3.Connection:
    """A read-only connection to the store (``mode=ro`` + ``query_only``): the
    serving process can never write, whatever a bug or a request does."""
    if str(db_path) == ":memory:":
        return db.connect(db_path)
    p = Path(db_path)
    if not p.exists():
        raise HTTPException(503, f"store not found: {db_path}")
    conn = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


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
                # A series without a volume is the katalog's "assigned to Reihe N,
                # not yet published there" — the honest signal for "unprinted in
                # the AA", to be read together with ``drucke`` (other printings).
                "aa_planned": sorted(
                    {
                        f"AA {ROMAN.get(int(r['series']), str(r['series']))}"
                        for r in aa_refs
                        if r.get("series") is not None and r.get("volume") is None
                    }
                ),
                "drucke": meta.get("drucke") or None,
                "url": meta.get("url") or meta.get("record_url"),
                "match_method": r["match_method"],
                "match_conf": r["match_conf"],
                "page_range": r["page_range"],
            }
        )
    return out


def _page_summary(page: db.Page, summary: tuple[int, float | None] | None) -> dict:
    """One row of a work's page list; ``summary`` comes from
    :func:`line_summaries_by_page` (one query for the whole work)."""
    n_lines, mean_conf = summary if summary is not None else (0, None)
    return {
        "page_id": page.id,
        "seq": page.seq,
        "label": page.label,
        "thumb_url": page.thumb_url,
        "status": page.status,
        "skip_reason": page.skip_reason,
        "n_lines": n_lines,
        "mean_conf": mean_conf,
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


def _esc(text: object) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def _stamp_shell(
    shell: str,
    *,
    path: str,
    title: str | None = None,
    description: str | None = None,
    ssr: str = "",
    site: str = SITE_URL,
) -> str:
    """Stamp the viewer shell for one route: ``<title>``, the description metas,
    the canonical/og:url, and the server-rendered block at :data:`SSR_MARK`.

    The shell's site-wide strings are literal in ``index.html`` (so the file is
    valid on its own); this replaces exactly those literals.
    """
    out = shell
    if site != SITE_URL:
        out = out.replace(SITE_URL, site)
    url = f"{site}{path}"
    out = out.replace(f'href="{site}/"', f'href="{url}"', 1)  # canonical
    og_url = 'property="og:url" content="'
    out = out.replace(f'{og_url}{site}/"', f'{og_url}{url}"', 1)
    if title:
        full = f"{title} — {SITE_TITLE}"
        out = out.replace(f"<title>{SITE_TITLE}</title>", f"<title>{_esc(full)}</title>", 1)
        for key in ('property="og:title" content="', 'name="twitter:title" content="'):
            out = out.replace(f'{key}{SITE_TITLE}"', f'{key}{_esc(full)}"', 1)
    if description:
        out = out.replace(f'content="{SITE_DESCRIPTION}"', f'content="{_esc(description)}"')
    return out.replace(SSR_MARK, ssr, 1)


def _ssr_work(work: db.Work, pages: list, katalog: list[dict], gwlb_url: str) -> tuple:
    """(title, description, html) for a work's server-rendered summary."""
    title = work.title or work.gwlb_object_id
    marks = ", ".join(work.shelfmarks or [])
    n = len(pages)
    description = (
        f"{title}{' (' + marks + ')' if marks else ''}: {n:,} page images of the Leibniz "
        f"Nachlass, machine-transcribed with per-line confidence. Not an edition."
    )
    parts = [
        '<article class="panel ssr" id="ssr">',
        f"<h1>{_esc(title)}</h1>",
        f"<p>{_esc(marks)}</p>" if marks else "",
        f"<p>{_esc(work.set_name or '')} · {n:,} page images · "
        f'<a href="{_esc(gwlb_url)}">Original at the GWLB</a> · '
        f'<a href="/manifests/{_esc(work.gwlb_object_id)}">IIIF manifest</a></p>',
    ]
    if katalog:
        items = []
        for rec in katalog:
            bits = [rec.get("title") or rec.get("record_id") or ""]
            if rec.get("date"):
                bits.append(str(rec["date"]))
            if rec.get("aa_labels"):
                bits.append(", ".join(rec["aa_labels"]))
            elif rec.get("aa_planned"):
                bits.append(", ".join(rec["aa_planned"]) + " (assigned, not yet published)")
            if rec.get("drucke"):
                bits.append("Other printings: " + str(rec["drucke"]))
            items.append(f"<li>{_esc(' · '.join(b for b in bits if b))}</li>")
        parts.append("<h2>Catalogue records (Arbeitskatalog der Leibniz-Edition, CC BY 4.0)</h2>")
        parts.append("<ul>" + "".join(items) + "</ul>")
    if pages:
        links = "".join(
            f'<li><a href="/page/{_esc(p.id)}">{_esc(p.label or p.seq)}</a></li>' for p in pages
        )
        parts.append("<h2>Pages</h2>")
        parts.append(f'<ol class="ssr__pages">{links}</ol>')
    parts.append(f"<p>{_esc(attr.HONESTY)}</p></article>")
    return title, description, "".join(parts)


def _ssr_page(
    page: db.Page,
    work: db.Work | None,
    lines: list,
    image_url: str | None,
    gwlb_url: str,
    prev_id: str | None,
    next_id: str | None,
) -> tuple[str, str, str]:
    """(title, description, html) for a page's server-rendered machine text."""
    work_title = (work.title if work else None) or page.work_id
    label = page.label or f"page {page.seq}"
    title = f"{work_title}, fol. {label}"
    texts = [ln.text for ln in lines if ln.text]
    confs = [ln.conf for ln in lines if ln.conf is not None and ln.text]
    mean = f"{sum(confs) / len(confs):.2f}" if confs else "n/a"
    blurb = " ".join(texts)[:180].rstrip()
    description = (
        f"Machine transcription of {work_title}, fol. {label} ({len(texts)} lines, mean "
        f"confidence {mean}). {blurb}"
    ).strip()
    nav = []
    if prev_id:
        nav.append(f'<a rel="prev" href="/page/{_esc(prev_id)}">Previous page</a>')
    nav.append(f'<a href="/work/{_esc(page.work_id)}">All pages of this work</a>')
    if next_id:
        nav.append(f'<a rel="next" href="/page/{_esc(next_id)}">Next page</a>')
    shown = texts[:SSR_MAX_LINES]
    body = "".join(f"<li>{_esc(t)}</li>" for t in shown)
    rest = len(texts) - len(shown)
    more = f"<p>… {rest} more lines in the API.</p>" if rest else ""
    html_out = (
        '<article class="panel ssr" id="ssr">'
        f"<h1>{_esc(title)}</h1>"
        f"<p>{_esc(attr.HONESTY)} Mean line confidence on this page: {_esc(mean)}.</p>"
        f'<p><a href="{_esc(gwlb_url)}">Original at the GWLB</a>'
        + (f' · <a href="{_esc(image_url)}">Page image</a>' if image_url else "")
        + f' · <a href="/annotations/{_esc(page.id)}">Annotations (IIIF)</a></p>'
        f"<nav>{' · '.join(nav)}</nav>"
        f'<h2>The machine reads it as</h2><ol class="ssr__lines">{body}</ol>{more}'
        "</article>"
    )
    return title, description, html_out


def _sitemap_xml(site: str, work_ids: list[str]) -> str:
    urls = [f"{site}/", f"{site}/search", f"{site}/about"] + [f"{site}/work/{w}" for w in work_ids]
    body = "".join(f"<url><loc>{_esc(u)}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + "</urlset>"
    )


def create_app(
    db_path: str | Path = db.DEFAULT_DB_PATH,
    *,
    search: SearchBackend | None = None,
    static_dir: Path | None = STATIC_DIR,
    base_url: str | None = None,
    rate_limit: float = 0.0,
    rate_burst: int = 40,
    security_headers: bool = True,
    cors: bool = True,
    image_base_url: str | None = None,
) -> FastAPI:
    """Build the FastAPI application over a store (+ optional search backend).

    ``rate_limit`` is requests/second per client on the API, manifest and
    annotation routes (``0`` = off, the default for tests; ``leibniz serve``
    turns it on). ``cors`` opens the read-only JSON routes to other origins so
    IIIF viewers elsewhere can load the manifests (deliverable D7).
    ``image_base_url`` switches page images to the operator's mirror of the
    image cache (:mod:`leibniz.web.images`); unset, they come from the GWLB.
    """
    app = FastAPI(
        title="Leibniz Legible API",
        version=__version__,
        description=(
            "Machine transcriptions of the digitized Leibniz Nachlass with per-line "
            "confidence and provenance. Not an edition."
        ),
        # /openapi.json stays; the Swagger and ReDoc pages load from a CDN that the
        # CSP (script-src 'self') blocks, so they would render blank.
        docs_url=None,
        redoc_url=None,
    )
    state: dict = {"stats": None}
    images = ImageSource(image_base_url)

    # Middleware. The last one added is the outermost: headers on every response,
    # then CORS (so a 429 still carries the CORS headers a browser needs to read
    # it), then the rate limit, then gzip on the giants (a 3,500-page work is
    # ~1 MB of JSON before compression).
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    if rate_limit and rate_limit > 0:
        app.add_middleware(RateLimitMiddleware, rate=rate_limit, burst=rate_burst)
    if cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
            max_age=86400,
        )
    if security_headers:
        app.add_middleware(SecurityHeadersMiddleware)

    def base(request: Request) -> str:
        return (base_url or str(request.base_url)).rstrip("/")

    # ---- operations -------------------------------------------------------- #
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> JSONResponse:
        """Liveness: 200 while the store is present (search may be degraded)."""
        store_ok = str(db_path) == ":memory:" or Path(db_path).exists()
        search_ok = search.health() if search is not None else None
        body = {
            "status": "ok" if store_ok and search_ok is not False else "degraded",
            "version": __version__,
            "store": store_ok,
            "search": {"backend": search.name, "ok": search_ok} if search is not None else None,
        }
        return JSONResponse(body, status_code=200 if store_ok else 503, headers=NO_STORE)

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
            stats["images"] = {"origin": images.origin, "base_url": images.base_url}
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
        try:
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
        except httpx.HTTPError as exc:  # Meilisearch down or restarting
            raise HTTPException(503, "search backend unavailable; try again shortly") from exc
        if images.mirrored:  # the index stored the GWLB thumbnails; the mirror has its own
            for hit in res.hits:
                hit.thumb_url = images.thumb_url_for(hit.work_id, hit.seq, hit.thumb_url)
        return JSONResponse(res.to_dict(), headers=CACHE_HEADERS)

    @app.get("/api/works/{work_id}")
    def api_work(work_id: str) -> JSONResponse:
        conn = _open(db_path)
        try:
            work = db.get_work(conn, work_id)
            if work is None:
                raise HTTPException(404, f"work {work_id} not found")
            pages = db.get_pages(conn, work_id)
            summaries = line_summaries_by_page(conn, work_id)
            body = {
                "work_id": work.gwlb_object_id,
                "set": work.set_name,
                "title": work.title,
                "shelfmarks": list(work.shelfmarks or []),
                "manifest_url": work.manifest_url,
                "gwlb_url": attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id),
                "n_canvases": work.n_canvases,
                "iiif_manifest": f"/manifests/{work.gwlb_object_id}",
                "pages": [_page_summary(images.resolve(p), summaries.get(p.id)) for p in pages],
                "katalog": _katalog_for_work(conn, work_id),
                "attribution": attr.attribution(images.mirrored),
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
            shown = images.resolve(page)  # display fields; ``page`` stays the provenance
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
                "delivery": shown.delivery,
                "image_service_url": shown.image_service_url,
                "image_url": shown.image_url,
                "thumb_url": shown.thumb_url,
                "image_origin": "mirror" if shown is not page else "gwlb",
                "source_image_url": images.source_url(page),
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
                "attribution": attr.attribution(images.mirrored),
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
            counts = {pid: n for pid, (n, _) in line_summaries_by_page(conn, work_id).items()}
            sources = (
                {p.id: images.source_url(p) for p in pages if images.is_mirrored(p)}
                if images.mirrored
                else None
            )
            body = iiif.build_manifest(
                work,
                [images.resolve(p) for p in pages],
                base_url=base(request),
                line_counts=counts,
                images_mirrored=images.mirrored,
                sources=sources,
            )
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
            body = iiif.build_annotation_page(
                page,
                lines,
                base_url=base(request),
                run_dates=dates,
                images_mirrored=images.mirrored,
            )
        finally:
            conn.close()
        return JSONResponse(body, media_type="application/ld+json", headers=CACHE_HEADERS)

    # ---- viewer (D2) ------------------------------------------------------ #
    index_html = static_dir / "index.html" if static_dir else None
    if index_html is not None and index_html.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # The shell is read once and stamped with where images come from
        # (``<html data-image-origin>``), so the viewer's attribution and About
        # text need no extra request. Each route then stamps its own title,
        # description, canonical URL and — for works and pages — a
        # server-rendered summary in place of ``<!--ll:ssr-->``, so that search
        # engines, answer engines and readers without JavaScript get the
        # content; app.js replaces it on boot. Every variant carries its own
        # ETag and is revalidated on every load (``no-cache``) so a deploy shows
        # at once; /static/* may be cached by the proxy (see deploy/Caddyfile).
        shell = index_html.read_text(encoding="utf-8").replace(
            'data-image-origin="gwlb"', f'data-image-origin="{images.origin}"'
        )
        site = (base_url or SITE_URL).rstrip("/")

        def respond(request: Request, body: str, status: int = 200) -> Response:
            etag = f'"{hashlib.sha256(body.encode()).hexdigest()[:20]}"'
            headers = {"Cache-Control": "no-cache", "ETag": etag}
            if request.headers.get("if-none-match") == etag:
                return Response(status_code=304, headers=headers)
            return Response(body, status_code=status, media_type="text/html", headers=headers)

        def serve_index(request: Request) -> Response:
            return respond(request, _stamp_shell(shell, path="/", site=site))

        def serve_search(request: Request) -> Response:
            return respond(request, _stamp_shell(shell, path="/search", title="Search", site=site))

        def serve_about(request: Request) -> Response:
            return respond(request, _stamp_shell(shell, path="/about", title="About", site=site))

        def serve_index_work(work_id: str, request: Request) -> Response:
            conn = _open(db_path)
            try:
                work = db.get_work(conn, work_id)
                if work is None:
                    body = _stamp_shell(
                        shell, path=f"/work/{work_id}", title="Not found", site=site
                    )
                    return respond(request, body, status=404)
                pages = db.get_pages(conn, work_id)
                katalog = _katalog_for_work(conn, work_id)
            finally:
                conn.close()
            gwlb_url = attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id)
            title, description, ssr = _ssr_work(work, pages, katalog, gwlb_url)
            body = _stamp_shell(
                shell,
                path=f"/work/{work_id}",
                title=title,
                description=description,
                ssr=ssr,
                site=site,
            )
            return respond(request, body)

        def serve_index_page(page_id: str, request: Request) -> Response:
            conn = _open(db_path)
            try:
                page = db.get_page(conn, page_id)
                if page is None:
                    body = _stamp_shell(
                        shell, path=f"/page/{page_id}", title="Not found", site=site
                    )
                    return respond(request, body, status=404)
                work = db.get_work(conn, page.work_id)
                lines = latest_lines(conn, page_id)
                neighbours = conn.execute(
                    "SELECT page_id, seq FROM pages WHERE work_id = ? AND seq IN (?, ?)",
                    (page.work_id, page.seq - 1, page.seq + 1),
                ).fetchall()
            finally:
                conn.close()
            prev_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq - 1), None)
            next_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq + 1), None)
            shown = images.resolve(page)
            gwlb_url = attr.GWLB_RESOLVE.format(work_id=page.work_id)
            title, description, ssr = _ssr_page(
                page, work, lines, shown.image_url, gwlb_url, prev_id, next_id
            )
            body = _stamp_shell(
                shell,
                path=f"/page/{page_id}",
                title=title,
                description=description,
                ssr=ssr,
                site=site,
            )
            return respond(request, body)

        handlers = {
            "/search": serve_search,
            "/about": serve_about,
            "/work/{work_id}": serve_index_work,
            "/page/{page_id}": serve_index_page,
        }
        for route in INDEX_ROUTES:
            app.add_api_route(
                route, handlers.get(route, serve_index), methods=["GET"], include_in_schema=False
            )

        # Discovery files at the root: the favicon browsers request blindly, the
        # sitemap (one URL per work; the work pages link every page), llms.txt.
        favicon = static_dir / "favicon.ico"
        if favicon.exists():

            def serve_favicon() -> FileResponse:
                return FileResponse(favicon, media_type="image/x-icon", headers=DAY_CACHE)

            app.add_api_route(
                "/favicon.ico", serve_favicon, methods=["GET"], include_in_schema=False
            )

        llms = static_dir / "llms.txt"
        if llms.exists():

            def serve_llms() -> FileResponse:
                return FileResponse(llms, media_type="text/plain", headers=DAY_CACHE)

            app.add_api_route("/llms.txt", serve_llms, methods=["GET"], include_in_schema=False)

        def serve_sitemap() -> Response:
            if state.get("sitemap") is None:
                conn = _open(db_path)
                try:
                    ids = [w.gwlb_object_id for w in db.iter_works(conn)]
                finally:
                    conn.close()
                state["sitemap"] = _sitemap_xml(site, sorted(ids))
            return Response(state["sitemap"], media_type="application/xml", headers=DAY_CACHE)

        app.add_api_route("/sitemap.xml", serve_sitemap, methods=["GET"], include_in_schema=False)

        robots = static_dir / "robots.txt"
        if robots.exists():

            def serve_robots() -> FileResponse:
                return FileResponse(robots, media_type="text/plain", headers=CACHE_HEADERS)

            app.add_api_route("/robots.txt", serve_robots, methods=["GET"], include_in_schema=False)

    return app


__all__ = ["INDEX_ROUTES", "STATIC_DIR", "create_app"]
