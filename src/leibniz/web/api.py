"""The JSON API + viewer host (Phases D1/D2).

Routes (all read-only; the store is opened per request, read-only):

* ``GET /api/search``          — typo-/orthography-tolerant page search (D1),
  with ``"exact phrases"`` and ``-exclusions``
* ``GET /api/works``           — every work as a compact row, and the browse tree
  (shelfmark family → section → works; :mod:`leibniz.web.browse`)
* ``GET /api/works/{id}``      — a work: pages, katalog records, attribution
* ``GET /api/pages/{id}``      — a page: lines with geometry, text, confidence,
  status and provenance (SPECS §4.5), prev/next
* ``GET /api/pages/{id}/text`` — the page's transcription as a plain-text (or
  ``?format=tsv``) download, its provenance in a ``# `` comment header
* ``GET /api/works/{id}/text`` — every page of a work in canvas order, streamed,
  one ``## Folio …`` block per page
* ``GET /api/records/{id}/text`` — a catalogue piece across the folios its
  shelfmark names, placed by the C2 resolver (:mod:`leibniz.web.pieces`), in
  the work export's layout under a header naming the record
* ``GET /api/stats``           — corpus counts for the About page
* ``GET /manifests/{work}``    — IIIF Presentation 3 manifest (D7)
* ``GET /annotations/{page}``  — W3C AnnotationPage with the page's lines (D7)
* ``GET /healthz``             — liveness for the process manager / uptime monitor
* ``/``, ``/search``, ``/browse``, ``/work/…``, ``/page/…``, ``/about`` — the
  viewer shell, stamped per route with its title, description, canonical URL
  and, for the browse index, a work or a page, a server-rendered summary (the
  whole index, the catalogue entries, the page list, the machine text) so
  crawlers and readers without JavaScript see the content
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
import re
import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)

from leibniz import __version__, db
from leibniz.images.twins import TwinGroup, TwinIndex
from leibniz.search.backend import (
    MATCH_MODES,
    MAX_REACHABLE,
    SearchBackend,
    SearchQuery,
    SearchQueryError,
)
from leibniz.search.documents import (
    ROMAN,
    aa_ref_label,
    corpus_stats,
    latest_lines,
    line_summaries_by_page,
)
from leibniz.web import attribution as attr
from leibniz.web import browse, iiif, pieces
from leibniz.web.geometry import baseline_points, line_bbox, polygon_points
from leibniz.web.images import ImageSource
from leibniz.web.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

STATIC_DIR = Path(__file__).parent / "static"
INDEX_ROUTES = ("/", "/search", "/browse", "/about", "/work/{work_id}", "/page/{page_id}")
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

# The plain-text exports: ``?format=`` → media type, and the TSV variant's columns.
TEXT_MEDIA = {"txt": "text/plain; charset=utf-8", "tsv": "text/tab-separated-values; charset=utf-8"}
TSV_COLUMNS = ("line_id", "line_seq", "conf", "status", "text")
# The header's last lines say how the body is laid out, for whoever parses it.
PAGE_LAYOUT = "After the first blank line: the recognised lines in reading order, one per line."
WORK_LAYOUT = (
    'After the first blank line, page by page: a "## Folio <label> — <page id>" line '
    '("## Canvas <n>" where no folio label is recorded), "# " lines naming its source image '
    "and model, then its recognised lines in reading order, one per line."
)
TSV_LAYOUT = (
    "Each recognised line is a tab-separated row (" + ", ".join(TSV_COLUMNS) + ") under the "
    "header row that opens the body."
)
TextFormat = Annotated[
    str,
    Query(
        alias="format",
        pattern="^(txt|tsv)$",
        description=(
            "`txt` (default): one recognised line per line of text; `tsv`: tab-separated "
            "`line_id`, `line_seq`, `conf`, `status`, `text` under a header row."
        ),
    ),
]
TEXT_RESPONSES: dict = {
    200: {
        "description": "UTF-8 text with a `# ` comment header (`?format=tsv`: tab-separated).",
        "content": {"text/tab-separated-values": {"schema": {"type": "string"}}},
    },
    404: {"description": "No such id."},
}
RECORD_RESPONSES: dict = {
    200: TEXT_RESPONSES[200],
    404: {
        "description": (
            "No such record, or a record that cannot be placed on the scan; the `detail` "
            "says which: the record is not linked to a digitized work, its shelfmark names "
            "no folio (`Bl.`) range, or no page of the work carries a folio label in that "
            "range."
        )
    },
}

# The proxy lets browsers cache /static/* for an hour (deploy/Caddyfile), so
# what the shell loads must change its address when its content does, or a
# deploy reaches returning readers late. The stylesheet and the boot script get
# a content hash in their URL (``?v=…``). The viewer's ES modules import each
# other by relative path, so they are versioned as one set: the shell loads
# ``app.js`` from ``/static/m/<build>/``, where ``<build>`` hashes every
# module, and each ``./i18n.js`` or ``../api.js`` resolves under the same
# prefix. A hash on ``app.js`` alone is not enough: after a deploy a returning
# reader ran the new ``app.js`` against a cached old ``i18n.js`` and ``api.js``
# (W3, 2026-10-06: "nav.browse" in the nav, "api.works is not a function").
VERSIONED_ASSETS = ("style.css", "boot.js")
MODULE_ENTRY = "app.js"
MODULES_PREFIX = "/static/m"


def _open(db_path: str | Path, *, any_thread: bool = False) -> sqlite3.Connection:
    """A read-only connection to the store (``mode=ro`` + ``query_only``): the
    serving process can never write, whatever a bug or a request does.

    ``any_thread`` is for a streamed response: Starlette advances a sync body
    generator on whichever worker thread is free, one step at a time, so the
    connection must not be pinned to the thread that opened it.
    """
    if str(db_path) == ":memory:":
        return db.connect(db_path)
    p = Path(db_path)
    if not p.exists():
        raise HTTPException(503, f"store not found: {db_path}")
    conn = sqlite3.connect(
        f"{p.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=not any_thread
    )
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


def _people(meta: dict) -> dict:
    """Who a catalogue record names: ``sender`` and ``addressee`` as the
    catalogue writes them (its link texts "(KorrespDB)", "(GND)" removed,
    several people apart, its doubt marks kept), and ``correspondent``, the
    people beside Leibniz — in a letter of his, the addressee, not himself."""
    cells = (meta.get("absender"), meta.get("adressat"))
    others = dict.fromkeys(
        name
        for cell in cells
        for name in browse.correspondent_names(cell)
        if name != browse.LEIBNIZ
    )
    return {
        "sender": browse.names_as_written(cells[0]),
        "addressee": browse.names_as_written(cells[1]),
        "correspondent": "; ".join(others) or meta.get("correspondent") or None,
    }


def _record_dict(rec: db.KatalogRecord) -> dict:
    """What the API says about a catalogue record, before its placement."""
    meta, aa_refs = rec.metadata, rec.aa_refs
    return {
        "record_id": rec.record_id,
        "title": meta.get("title") or meta.get("titel"),
        "incipit": meta.get("incipit"),
        "date": meta.get("datum") or meta.get("date"),
        **_people(meta),
        "place": meta.get("ort"),
        "textart": meta.get("textart"),
        "shelfmarks": list(rec.shelfmark_refs),
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
    }


def _katalog_for_work(
    conn: sqlite3.Connection, work_id: str, pages: list[db.Page] | None = None
) -> list[dict]:
    """A work's catalogue records with their crosswalk link and, where the C2
    resolver places a record on the work's folios (:mod:`leibniz.web.pieces`),
    ``text_url``, ``folio_label``, ``folio_range`` and ``n_pages``; a record
    that cannot be placed carries none of the four. ``pages`` spares a second
    read of the work's pages when the caller has them."""
    rows = conn.execute(
        """
        SELECT c.katalog_record_id, c.match_method, c.match_conf, c.page_range,
               k.metadata, k.aa_refs, k.shelfmark_refs
          FROM crosswalk c JOIN katalog_records k ON k.record_id = c.katalog_record_id
         WHERE c.work_id = ? ORDER BY c.match_conf DESC, c.katalog_record_id
        """,
        (work_id,),
    ).fetchall()
    if not rows:
        return []
    records = [
        db.KatalogRecord(
            record_id=r["katalog_record_id"],
            metadata=json.loads(r["metadata"]) if r["metadata"] else {},
            shelfmark_refs=json.loads(r["shelfmark_refs"]) if r["shelfmark_refs"] else [],
            aa_refs=json.loads(r["aa_refs"]) if r["aa_refs"] else [],
        )
        for r in rows
    ]
    placed = pieces.place_all(
        work_id, db.get_pages(conn, work_id) if pages is None else pages, records
    )
    out: list[dict] = []
    for r, rec in zip(rows, records, strict=True):
        entry = {
            **_record_dict(rec),
            "match_method": r["match_method"],
            "match_conf": r["match_conf"],
            "page_range": r["page_range"],
        }
        where = placed[rec.record_id]
        if isinstance(where, pieces.Placement):
            entry.update(
                {
                    # placed on this work, so the download serves what the
                    # link says (the record may be linked to more than one)
                    "text_url": f"/api/records/{rec.record_id}/text?work={work_id}",
                    "folio_label": where.folio_label,
                    "folio_range": [where.folio_lo, where.folio_hi],
                    "n_pages": len(where.pages),
                }
            )
        out.append(entry)
    return out


def _page_summary(
    page: db.Page, summary: tuple[int, float | None] | None, twin: TwinGroup | None = None
) -> dict:
    """One row of a work's page list; ``summary`` comes from
    :func:`line_summaries_by_page` (one query for the whole work). A page whose
    scan is registered more than once counts the lines it shows (a spread its
    half) and says so (``twin``)."""
    n_lines, mean_conf = summary if summary is not None else (0, None)
    if twin is not None and page.id in twin.n_lines:
        n_lines, mean_conf = twin.n_lines[page.id], twin.mean_conf.get(page.id)
    out = {
        "page_id": page.id,
        "seq": page.seq,
        "label": page.label,
        "thumb_url": page.thumb_url,
        "status": page.status,
        "skip_reason": page.skip_reason,
        "n_lines": n_lines,
        "mean_conf": mean_conf,
    }
    if twin is not None:
        out["twin"] = _twin_dict(twin, page.id)
    return out


def _twin_dict(group: TwinGroup, page_id: str) -> dict:
    """What a page says about the other registrations of its scan."""
    out: dict = {
        "kind": group.kind,
        "others": [{"page_id": pid, "label": label} for pid, label in group.others(page_id)],
        "note": group.describe(page_id),
    }
    if group.kind == "spread":
        out.update({"side": group.side(page_id), "fold_x": group.fold_x})
    else:
        out.update({"primary": group.primary, "is_primary": page_id == group.primary})
    return out


def _twin_lines(
    group: TwinGroup | None, page_id: str, lines: list[db.Line], *, once: bool = False
) -> tuple[list[db.Line], set[int]]:
    """The lines a page shows given its scan's group, and the ``line_seq`` of
    those that cross a spread's fold; ``once`` gives each line to one page only
    (the exports of several pages)."""
    if group is None:
        return lines, set()
    pairs = group.own_lines(page_id, lines, for_index=once)
    return [ln for ln, _ in pairs], {ln.line_seq for ln, across in pairs if across}


def _once_summaries(
    summaries: dict[str, tuple[int, float | None]], pages: list[db.Page], twins: TwinIndex
) -> dict[str, tuple[int, float | None]]:
    """Per-page summaries with each scan's lines counted once (a spread by its
    halves, a fold on its primary), for the line count of a several-page export."""
    out = dict(summaries)
    for page in pages:
        group = twins.get(page.id)
        if group is not None and page.id in group.n_once:
            n = group.n_once[page.id]
            if n:
                out[page.id] = (n, group.mean_conf.get(page.id))
            else:
                out.pop(page.id, None)
    return out


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


def _with_text(lines: list[db.Line]) -> list[db.Line]:
    """The lines a page shows, from :func:`latest_lines`: those with text."""
    return [ln for ln in lines if ln.text]


def _line_stats(lines: list[db.Line]) -> dict:
    """``n_lines`` and ``mean_conf`` over a page's lines with text."""
    confs = [ln.conf for ln in lines if ln.conf is not None]
    return {
        "n_lines": len(lines),
        "mean_conf": round(sum(confs) / len(confs), 4) if confs else None,
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
    # The path carries whatever id the request named — on a 404 an id the store
    # never had — so it is escaped like any other text (2026-10: a quote in it
    # closed the attribute, and the rest of the URL became markup on our page).
    url = _esc(f"{site}{path}")
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


def _crumbs(place: dict | None) -> str:
    """A work's way back into the browse index: "Browse › LH 35 · Mathematik"."""
    if not place:
        return ""
    return (
        '<nav aria-label="Breadcrumb"><a href="/browse">Browse</a> › '
        f'<a href="/browse#{_esc(place["anchor"])}">{_esc(place["title"])}</a></nav>'
    )


def _ssr_work(
    work: db.Work, pages: list, katalog: list[dict], gwlb_url: str, place: dict | None = None
) -> tuple:
    """(title, description, html) for a work's server-rendered summary; ``place``
    is where the work sits in the browse index (:func:`browse.places`)."""
    title = work.title or work.gwlb_object_id
    marks = ", ".join(work.shelfmarks or [])
    n = len(pages)
    description = (
        f"{title}{' (' + marks + ')' if marks else ''}: {n:,} page images of the Leibniz "
        f"Nachlass, machine-transcribed with per-line confidence. Not an edition."
    )
    download = (
        f' · <a href="/api/works/{_esc(work.gwlb_object_id)}/text" download>'
        "Download the text of this work</a>"
        if any(p.status == "recognized" for p in pages)
        else ""
    )
    parts = [
        '<article class="panel ssr" id="ssr">',
        _crumbs(place),
        f"<h1>{_esc(title)}</h1>",
        f"<p>{_esc(marks)}</p>" if marks else "",
        f"<p>{_esc(work.set_name or '')} · {n:,} page images · "
        f'<a href="{_esc(gwlb_url)}">Original at the GWLB</a> · '
        f'<a href="/manifests/{_esc(work.gwlb_object_id)}">IIIF manifest</a>{download}</p>',
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
            text = (
                f' · <a href="{_esc(rec["text_url"])}" download>Text of this piece '
                f"({_esc(rec['folio_label'])})</a>"
                if rec.get("text_url")
                else ""
            )
            items.append(f"<li>{_esc(' · '.join(b for b in bits if b))}{text}</li>")
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
    twin: TwinGroup | None = None,
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
    download = (
        f' · <a href="/api/pages/{_esc(page.id)}/text" download>Download text</a>' if texts else ""
    )
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
        + f' · <a href="/annotations/{_esc(page.id)}">Annotations (IIIF)</a>{download}</p>'
        f"<nav>{' · '.join(nav)}</nav>"
        + (f"<p>{_esc(twin.describe(page.id))}</p>" if twin is not None else "")
        + f'<h2>The machine reads it as</h2><ol class="ssr__lines">{body}</ol>{more}'
        "</article>"
    )
    return title, description, html_out


BROWSE_TITLE = "Browse by shelfmark"
BROWSE_NOTE = (
    "Titles and shelfmarks are the library's. Section names are cut from its titles. "
    "Correspondent names come from the linked records of the Arbeitskatalog der "
    "Leibniz-Edition (BBAW / TELOTA, CC BY 4.0), checked against the alphabetical order of "
    "the LBr numbers; where no record is linked yet, or the names do not fit that order, "
    "an entry shows its shelfmark only. The texts behind the links are machine "
    "transcriptions, not an edition."
)


def _counts(n_works: int, n_pages: int) -> str:
    return (
        f"{n_works:,} work{'' if n_works == 1 else 's'}, "
        f"{n_pages:,} page image{'' if n_pages == 1 else 's'}"
    )


def _ssr_browse_entry(family: str, entry: browse.Entry) -> str:
    """One work of the index: a link, and what else names it."""
    href = f"/work/{_esc(entry.work_id)}"
    if family in ("LH", "LBr"):  # the label is the shelfmark, or the correspondent
        rest = entry.shelfmark if entry.label != entry.shelfmark and family == "LBr" else ""
        text = entry.label
    else:  # the shelfmark, then the (cut) title
        text = entry.shelfmark or entry.label
        rest = entry.label if entry.shelfmark else ""
    return f'<li><a href="{href}">{_esc(text)}</a>{" · " + _esc(rest) if rest else ""}</li>'


def _ssr_browse(families: list[browse.Family]) -> tuple[str, str, str]:
    """(title, description, html) for the browse index: every family and
    section with a link per work, so crawlers and readers without JavaScript
    get the whole index (``<details>`` needs none)."""
    n_works = sum(f.n_works for f in families)
    n_pages = sum(f.n_pages for f in families)
    description = (
        f"The digitized Leibniz Nachlass by shelfmark: {n_works:,} works and {n_pages:,} page "
        "images. The manuscripts (LH) by section, the correspondence (LBr) by correspondent, "
        "the annotated books (Marginalien) by number; every entry opens the work and its folios."
    )
    parts = [
        '<article class="panel ssr" id="ssr">',
        "<h1>Browse the Nachlass by shelfmark</h1>",
        f"<p>{_counts(n_works, n_pages)}. {_esc(BROWSE_NOTE)}</p>",
    ]
    for family in families:
        parts.append(f"<h2>{_esc(family.name)}</h2>")
        parts.append(f"<p>{_counts(family.n_works, family.n_pages)}</p>")
        for section in family.sections:
            parts.append(
                f'<details id="{_esc(section.anchor)}"><summary>{_esc(section.title)} '
                f"({_counts(section.n_works, section.n_pages)})</summary>"
                '<ul class="ssr__index">'
            )
            parts.extend(_ssr_browse_entry(family.key, entry) for entry in section.entries)
            parts.append("</ul></details>")
    parts.append("</article>")
    return BROWSE_TITLE, description, "".join(parts)


def _sitemap_xml(site: str, work_ids: list[str]) -> str:
    urls = [f"{site}/", f"{site}/search", f"{site}/browse", f"{site}/about"]
    urls += [f"{site}/work/{w}" for w in work_ids]
    body = "".join(f"<url><loc>{_esc(u)}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + "</urlset>"
    )


def _modules_build(static_dir: Path) -> str:
    """One version for the viewer's ES modules as a set: the first 12 hex
    digits of a SHA-256 over every ``.js`` file outside ``vendor/``, names and
    contents. Any change to any of them is a new build."""
    digest = hashlib.sha256()
    for path in sorted(static_dir.rglob("*.js")):
        rel = path.relative_to(static_dir)
        if rel.parts[0] == "vendor":
            continue
        digest.update(rel.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()[:12]


def _version_assets(shell: str, static_dir: Path) -> str:
    """Make the shell name what it loads by content (once, at startup): ``?v=``
    and the first 12 hex digits of its SHA-256 on each of
    :data:`VERSIONED_ASSETS`, and the module entry under
    ``/static/m/<build>/`` (:func:`_modules_build`), from where its relative
    imports resolve to the same build."""
    for name in VERSIONED_ASSETS:
        asset = static_dir / name
        if asset.is_file():
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
            shell = shell.replace(f'"/static/{name}"', f'"/static/{name}?v={digest}"')
    if (static_dir / MODULE_ENTRY).is_file():
        entry = f"{MODULES_PREFIX}/{_modules_build(static_dir)}/{MODULE_ENTRY}"
        shell = shell.replace(f'"/static/{MODULE_ENTRY}"', f'"{entry}"')
    return shell


# ---- plain-text exports ---------------------------------------------------- #


def _text_headers(object_id: str, fmt: str) -> dict[str, str]:
    """The cache headers plus the download's name, ``leibniz-legible_<id>.<fmt>``.

    A page id's colon becomes ``_`` there: Windows refuses ``:`` in a file name
    (browsers rewrite it anyway; other clients would not).
    """
    name = re.sub(r"[^A-Za-z0-9._-]", "_", object_id)
    disposition = f'attachment; filename="leibniz-legible_{name}.{fmt}"'
    return {**CACHE_HEADERS, "Content-Disposition": disposition}


def _folio(page: db.Page) -> str:
    """``Folio 1r``, or ``Canvas 3`` where the METS records no folio label."""
    return f"Folio {page.label}" if page.label else f"Canvas {page.seq}"


def _why(page: db.Page) -> str:
    """Why a page has no text, as its status says (``skipped: no_lines``)."""
    return f"{page.status}: {page.skip_reason}" if page.skip_reason else page.status


def _title_row(work: db.Work | None, work_id: str) -> str:
    title = (work.title if work else None) or work_id
    marks = [m for m in (work.shelfmarks if work else []) if m and m not in title]
    if not marks:
        return f"Title: {title}"
    return f"Title: {title} (shelfmark{'s' if len(marks) > 1 else ''} {'; '.join(marks)})"


def _count_row(n_lines: int, mean_conf: float | None, where: str = "") -> str:
    mean = f"{mean_conf:.2f}" if mean_conf is not None else "not recorded"
    return f"Lines: {n_lines:,} recognised{where}, mean confidence {mean}"


def _run_rows(lines: list[db.Line], runs: dict[int | None, dict | None]) -> list[str]:
    """One ``Model: …, run …, <date> — n lines, status …`` row per recognition run
    behind ``lines``, newest first: one run as a rule, two where a later run
    re-read part of the page (``runs`` maps run id → :func:`_run_info`)."""
    groups: dict[int | None, list[db.Line]] = {}
    for ln in lines:
        groups.setdefault(ln.run_id, []).append(ln)
    rows = []
    for run_id in sorted(groups, key=lambda r: -1 if r is None else r, reverse=True):
        group = groups[run_id]
        info = runs.get(run_id) or {}
        model = info.get("model") or group[0].model or "not recorded"
        when = info.get("finished_at") or info.get("started_at") or "date not recorded"
        n = len(group)
        rows.append(
            f"Model: {model}, run {run_id if run_id is not None else 'not recorded'}, {when}"
            f" — {n:,} line{'' if n == 1 else 's'}, "
            f"status {', '.join(sorted({ln.status for ln in group}))}"
        )
    return rows


def _text_rows(lines: list[db.Line], fmt: str) -> list[str]:
    """The body: each line's text on one output line (a line break inside it,
    and in TSV a tab, becomes a space), or its TSV row."""
    texts = [" ".join((ln.text or "").splitlines()) for ln in lines]
    if fmt != "tsv":
        return texts
    return [
        "\t".join(
            (
                ln.id,
                str(ln.line_seq),
                "" if ln.conf is None else str(round(ln.conf, 4)),
                ln.status,
                text.replace("\t", " "),
            )
        )
        for ln, text in zip(lines, texts, strict=True)
    ]


def _head(rows: list[str], fmt: str) -> str:
    """The ``# `` comment header, the blank line, and in TSV the column row.

    Each row is one line: a title or an incipit can carry a line break, and a
    blank line inside the header would end it where a parser looks for the body.
    """
    out = "".join(f"# {' '.join(row.split())}\n" for row in rows) + "\n"
    return out + ("\t".join(TSV_COLUMNS) + "\n" if fmt == "tsv" else "")


def _page_text(
    site: str,
    page: db.Page,
    work: db.Work | None,
    lines: list[db.Line],
    runs: dict[int | None, dict | None],
    fmt: str,
    twin: TwinGroup | None = None,
) -> str:
    """One page's export; ``lines`` are its lines with text, as ``/api/pages`` shows them."""
    stats = _line_stats(lines)
    rows = [
        f"{attr.PROJECT_NAME} — {site}",
        f"Page: {site}/page/{page.id}",
        _title_row(work, page.work_id),
        f"{_folio(page)}, page id {page.id}",
        *([f"Scan: {twin.describe(page.id)}"] if twin is not None else []),
        f"Original at the GWLB: {attr.gwlb_page_url(page.work_id, page.seq)}",
        f"Source image: {ImageSource.source_url(page) or 'not recorded'}",
        *_run_rows(lines, runs),
        _count_row(stats["n_lines"], stats["mean_conf"])
        if lines
        else f"Lines: 0 recognised ({_why(page)})",
        attr.HONESTY,
        attr.TEXT_LICENCE,
        attr.WORDING_RULE,
        PAGE_LAYOUT,
        *([TSV_LAYOUT] if fmt == "tsv" else []),
    ]
    return _head(rows, fmt) + "".join(f"{row}\n" for row in _text_rows(lines, fmt))


def _pages_count_row(pages: list[db.Page], summaries: dict[str, tuple[int, float | None]]) -> str:
    """``Lines: n recognised on k of m pages, mean confidence c`` over the pages
    given, from the per-page summaries (``n`` and ``c`` weighted by lines)."""
    found = [summaries[p.id] for p in pages if p.id in summaries]
    n_lines = sum(n for n, _ in found)
    weighted = [(n, c) for n, c in found if c is not None]
    total = sum(n for n, _ in weighted)
    mean = sum(n * c for n, c in weighted) / total if total else None
    return _count_row(n_lines, mean, f" on {len(found):,} of {len(pages):,} pages")


def _page_chunks(
    db_path: str | Path, pages: list[db.Page], fmt: str, twins: TwinIndex | None = None
) -> Iterator[str]:
    """The body of a streamed export, one chunk per page in the order given.

    Each page is read with :func:`latest_lines` as it is sent, so a convolute
    of thousands of pages never sits in memory. The generator opens its own
    connection (Starlette steps it from worker threads) and closes it at the
    end, or when the client goes away and the generator is discarded.
    """
    conn = _open(db_path, any_thread=True)
    try:
        runs: dict[int | None, dict | None] = {}
        for i, page in enumerate(pages):
            block = [f"## {_folio(page)} — {page.id}"]
            group = twins.get(page.id) if twins is not None else None
            if group is not None and not group.carries_text(page.id):
                # a fold: the text is given once, on the scan's primary page
                block.append(f"# {group.describe(page.id)}")
                yield ("\n" if i else "") + "".join(f"{row}\n" for row in block)
                continue
            lines, _ = _twin_lines(
                group, page.id, _with_text(latest_lines(conn, page.id)), once=True
            )
            for run_id in {ln.run_id for ln in lines} - runs.keys():
                runs[run_id] = _run_info(conn, run_id)
            if group is not None:
                block.append(f"# Scan: {group.describe(page.id)}")
            if lines:
                block.append(f"# Source image: {ImageSource.source_url(page) or 'not recorded'}")
                block += [f"# {row}" for row in _run_rows(lines, runs)]
                block += _text_rows(lines, fmt)
            else:
                block.append(f"# No recognised text on this page ({_why(page)}).")
            yield ("\n" if i else "") + "".join(f"{row}\n" for row in block)
    finally:
        conn.close()


def _work_text(
    db_path: str | Path,
    site: str,
    work: db.Work,
    pages: list[db.Page],
    summaries: dict[str, tuple[int, float | None]],
    fmt: str,
    twins: TwinIndex | None = None,
) -> Iterator[str]:
    """A work's export: the header from the one :func:`line_summaries_by_page`
    query, then :func:`_page_chunks` over every page in canvas order. A scan
    registered more than once gives its lines once (``twins``)."""
    if twins is not None:
        summaries = _once_summaries(summaries, pages, twins)
    rows = [
        f"{attr.PROJECT_NAME} — {site}",
        f"Work: {site}/work/{work.gwlb_object_id}",
        _title_row(work, work.gwlb_object_id),
        f"Original at the GWLB: {attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id)}",
        _pages_count_row(pages, summaries),
        attr.HONESTY,
        attr.TEXT_LICENCE,
        attr.WORDING_RULE,
        WORK_LAYOUT,
        *([TSV_LAYOUT] if fmt == "tsv" else []),
    ]
    yield _head(rows, fmt)
    yield from _page_chunks(db_path, pages, fmt, twins)


def _record_rows(rec: dict) -> list[str]:
    """The header rows that describe a catalogue record: what the catalogue
    says about the piece, as the work page shows it."""
    rows = [f"Catalogue record: {rec['record_id']} — {rec.get('title') or 'no title'}"]
    if rec.get("incipit"):
        rows.append(f"Incipit: {rec['incipit']}")
    if rec.get("date"):
        rows.append(f"Date: {rec['date']}")
    people = [
        f"{label} {'; '.join(names)}"
        for label, names in (("Sender:", rec.get("sender")), ("Addressee:", rec.get("addressee")))
        if names
    ]
    if people:
        rows.append(" — ".join(people))
    if rec.get("aa_labels"):
        rows.append(f"Akademie-Ausgabe: {', '.join(rec['aa_labels'])}")
    elif rec.get("aa_planned"):
        rows.append(
            f"Akademie-Ausgabe: {', '.join(rec['aa_planned'])} (assigned, not yet published)"
        )
    if rec.get("drucke"):
        rows.append(f"Other printings: {rec['drucke']}")
    if rec.get("url"):
        rows.append(f"Record in the Leibniz-Katalog: {rec['url']}")
    return rows


def _record_text(
    db_path: str | Path,
    site: str,
    rec: dict,
    placed: pieces.Placement,
    work: db.Work | None,
    summaries: dict[str, tuple[int, float | None]],
    fmt: str,
    twins: TwinIndex | None = None,
) -> Iterator[str]:
    """A catalogue piece's export: the record, the work, the folio range and the
    canvases in the header, then :func:`_page_chunks` over the placed pages. A
    scan registered more than once gives its lines once (``twins``)."""
    pages = placed.pages
    if twins is not None:
        summaries = _once_summaries(summaries, pages, twins)
    seqs = [p.seq for p in pages]
    span = f"canvas {seqs[0]}" if len(seqs) == 1 else f"canvases {seqs[0]}–{seqs[-1]}"
    rows = [
        f"{attr.PROJECT_NAME} — {site}",
        f"Piece: {site}/api/records/{placed.record_id}/text",
        *_record_rows(rec),
        f"Work: {site}/work/{placed.work_id}",
        _title_row(work, placed.work_id),
        f"Folios: {placed.folio_label} (from the shelfmark {placed.signature}): "
        f"{len(pages):,} page{'' if len(pages) == 1 else 's'}, {span}, "
        f"page ids {pages[0].id} to {pages[-1].id}",
        f"Original at the GWLB: {attr.gwlb_page_url(placed.work_id, pages[0].seq)}",
        _pages_count_row(pages, summaries),
        attr.KATALOG,
        attr.HONESTY,
        attr.TEXT_LICENCE,
        attr.WORDING_RULE,
        WORK_LAYOUT,
        *([TSV_LAYOUT] if fmt == "tsv" else []),
    ]
    yield _head(rows, fmt)
    yield from _page_chunks(db_path, pages, fmt, twins)


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
    calculemus_url: str | None = None,
    twins_path: str | Path | None = None,
) -> FastAPI:
    """Build the FastAPI application over a store (+ optional search backend).

    ``rate_limit`` is requests/second per client on the API, manifest and
    annotation routes (``0`` = off, the default for tests; ``leibniz serve``
    turns it on). ``cors`` opens the read-only JSON routes to other origins so
    IIIF viewers elsewhere can load the manifests (deliverable D7).
    ``image_base_url`` switches page images to the operator's mirror of the
    image cache (:mod:`leibniz.web.images`); unset, they come from the GWLB.
    ``calculemus_url`` is the origin of the game built on this corpus, stamped
    into the viewer shell (``<html data-calculemus-url>``) so the About page
    can link to it; unset, nothing about the game reaches the HTML.
    ``twins_path`` is the file of scans registered more than once
    (:mod:`leibniz.images.twins`, written by the index build); without it every
    page shows and exports its own reading, as before.
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
    # The public origin the shell and the text exports cite (canonical URLs);
    # the manifests use the requesting host instead (``base``).
    site = (base_url or SITE_URL).rstrip("/")

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

    def browse_index() -> dict:
        """The browse tree with what is served from it, built on first use and
        kept for the life of the process: the works table and the catalogue
        links change only with a corpus run, and the app is restarted then."""
        if state.get("browse") is None:
            conn = _open(db_path)
            try:
                families = browse.build_index(
                    db.iter_works(conn),
                    browse.group_correspondents(conn.execute(browse.CORRESPONDENTS_SQL)),
                    db.matched_work_ids(conn),
                )
            finally:
                conn.close()
            state["browse"] = {
                "families": families,
                "places": browse.places(families),
                "titles": browse.display_titles(families),
            }
        return state["browse"]

    def twins() -> TwinIndex:
        """The scans registered more than once, read on first use and kept for
        the life of the process (the index build rewrites the file; restart)."""
        if state.get("twins") is None:
            state["twins"] = TwinIndex.load(twins_path)
        return state["twins"]

    def titled(work: db.Work | None) -> db.Work | None:
        """The work as it is shown: where the library's title is the generic
        one every letter convolute carries, the browse index's name for it
        (``LBr. 16 · Arnauld``); the store's row is untouched."""
        if work is None:
            return None
        shown = browse_index()["titles"].get(work.gwlb_object_id)
        return replace(work, title=shown) if shown and shown != work.title else work

    def works_body(families: list[browse.Family]) -> dict:
        return {
            "n_works": sum(f.n_works for f in families),
            "n_pages": sum(f.n_pages for f in families),
            "works": browse.rows(families),
            "groups": browse.tree(families),
            "note": BROWSE_NOTE,
            "attribution": attr.attribution(images.mirrored),
        }

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
        q: str = Query(
            "",
            max_length=500,
            description=(
                'Words match typo-tolerantly. "Double quotes" match the exact words in that '
                'order; a minus in front (-word, -"two words") leaves out pages containing it.'
            ),
        ),
        set: str | None = Query(  # noqa: A002 — the API's public name
            None, alias="set", pattern=r"^[A-Za-z][A-Za-z0-9_-]*$", max_length=64
        ),
        lang: str | None = None,
        stratum: str | None = None,
        min_conf: float | None = Query(None, ge=0.0, le=1.0),
        work: str | None = Query(None, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$", max_length=64),
        page: int = Query(
            1,
            ge=1,
            le=MAX_REACHABLE,
            description=f"1-based; no hit past the first {MAX_REACHABLE:,} can be paged to "
            "(`reachable` in the answer), and a page past them answers the last one.",
        ),
        limit: int = Query(20, ge=1, le=100),
        match: str = Query(
            "all",
            pattern="^(" + "|".join(MATCH_MODES) + ")$",
            description="`all` (default): a page must hold every word; `any`: one is enough.",
        ),
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
                    match=match,
                )
            )
        except SearchQueryError as exc:  # the query, not the index: say so
            raise HTTPException(400, str(exc)) from exc
        except httpx.HTTPError as exc:  # Meilisearch down or restarting
            raise HTTPException(503, "search backend unavailable; try again shortly") from exc
        titles = browse_index()["titles"]
        for hit in res.hits:  # the index holds the library's title; show the work's name
            hit.title = titles.get(hit.work_id, hit.title)
        if images.mirrored:  # the index stored the GWLB thumbnails; the mirror has its own
            for hit in res.hits:
                hit.thumb_url = images.thumb_url_for(hit.work_id, hit.seq, hit.thumb_url)
        return JSONResponse(res.to_dict(), headers=CACHE_HEADERS)

    @app.get(
        "/api/works",
        summary="Every work, by shelfmark family and section",
        description=(
            "The whole Nachlass as one list: `works` holds a compact row per work (`work_id`, "
            "`set`, `title`, `shelfmark`, `shelfmarks`, `family`, `section`, `section_label`, "
            "`label`, `n_canvases`, `has_katalog`), `groups` the browse tree — family (`LH`, "
            "`LBr`, `Marg`, `Other`) → section (with its `anchor` on `/browse`, its counts and "
            "the work ids of its `entries` in order; the letters also `by_number`). A letter "
            "convolute's `label` is its correspondent where the linked catalogue records name "
            "one that fits the alphabetical order of the LBr numbers, else its shelfmark."
        ),
    )
    def api_works(
        set: str | None = Query(  # noqa: A002 — the API's public name
            None, alias="set", description="Only the works of one OAI set, e.g. `Leibnitiana`."
        ),
        family: str | None = Query(
            None,
            pattern="^(LH|LBr|Marg|Other)$",
            description="Only one family: `LH`, `LBr`, `Marg` or `Other`.",
        ),
    ) -> Response:
        index = browse_index()
        if set is None and family is None:  # the whole list: rendered once
            if "json" not in index:
                index["json"] = JSONResponse(works_body(index["families"])).body
            return Response(index["json"], media_type="application/json", headers=DAY_CACHE)
        narrowed = browse.select(index["families"], set_name=set, family=family)
        return JSONResponse(works_body(narrowed), headers=DAY_CACHE)

    # /api/works/{work_id} does not shadow the list above, nor the list it: the
    # ``str`` convertor needs at least one character and never matches a slash.
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
                "title": titled(work).title,
                "library_title": work.title,
                "shelfmarks": list(work.shelfmarks or []),
                "manifest_url": work.manifest_url,
                "gwlb_url": attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id),
                "n_canvases": work.n_canvases,
                "iiif_manifest": f"/manifests/{work.gwlb_object_id}",
                "pages": [
                    _page_summary(images.resolve(p), summaries.get(p.id), twins().get(p.id))
                    for p in pages
                ],
                "katalog": _katalog_for_work(conn, work_id, pages),
                "attribution": attr.attribution(images.mirrored),
            }
        finally:
            conn.close()
        # where the work sits in the browse index: the work page's way back
        body["browse"] = browse_index()["places"].get(work.gwlb_object_id)
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
            twin = twins().get(page.id)
            # a spread page shows its half of the image; the lines across the fold on both
            recognised, across = _twin_lines(twin, page.id, _with_text(lines))
            run_dates = _run_dates(conn, {ln.run_id for ln in lines if ln.run_id is not None})
            neighbours = conn.execute(
                "SELECT page_id, seq FROM pages WHERE work_id = ? AND seq IN (?, ?)",
                (page.work_id, page.seq - 1, page.seq + 1),
            ).fetchall()
            prev_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq - 1), None)
            next_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq + 1), None)
            run_ids = [ln.run_id for ln in lines if ln.run_id is not None]
            shown = images.resolve(page)  # display fields; ``page`` stays the provenance
            body = {
                "page_id": page.id,
                "work_id": page.work_id,
                "work_title": titled(work).title if work else None,
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
                "source_image_service": images.service_url(page),
                "status": page.status,
                "skip_reason": page.skip_reason,
                "prev_page_id": prev_id,
                "next_page_id": next_id,
                "manifest_url": f"/manifests/{page.work_id}",
                "annotations_url": f"/annotations/{page.id}",
                "gwlb_url": attr.GWLB_RESOLVE.format(work_id=page.work_id),
                "gwlb_page_url": attr.gwlb_page_url(page.work_id, page.seq),
                "run": _run_info(conn, max(run_ids) if run_ids else None),
                "stats": _line_stats(recognised),
                "lines": [
                    {**_line_dict(ln, page, run_dates), "crosses_fold": ln.line_seq in across}
                    for ln in recognised
                ],
                "twin": _twin_dict(twin, page.id) if twin is not None else None,
                "honesty": attr.HONESTY,
                "attribution": attr.attribution(images.mirrored),
            }
        finally:
            conn.close()
        return JSONResponse(body, headers=CACHE_HEADERS)

    # ---- plain-text exports ------------------------------------------------ #
    # Nested under the JSON routes' prefixes: /robots.txt already admits them,
    # and the ``str`` path convertor never matches a slash, so neither shadows
    # /api/pages/{page_id} or /api/works/{work_id}.
    @app.get(
        "/api/pages/{page_id}/text",
        summary="A page's transcription as plain text",
        description=(
            "The machine transcription of one page as a download: a header of `# ` lines "
            "(page URL, work, folio, source image, model, run and run date, line count and "
            "mean confidence, the licence and the wording rule), a blank line, then the "
            "recognised lines in reading order — the lines `/api/pages/{page_id}` shows."
        ),
        response_class=PlainTextResponse,
        responses=TEXT_RESPONSES,
    )
    def api_page_text(page_id: str, fmt: TextFormat = "txt") -> Response:
        conn = _open(db_path)
        try:
            page = db.get_page(conn, page_id)
            if page is None:
                raise HTTPException(404, f"page {page_id} not found")
            work = db.get_work(conn, page.work_id)
            twin = twins().get(page.id)
            lines, _ = _twin_lines(twin, page.id, _with_text(latest_lines(conn, page_id)))
            runs = {run_id: _run_info(conn, run_id) for run_id in {ln.run_id for ln in lines}}
        finally:
            conn.close()
        body = _page_text(site, page, titled(work), lines, runs, fmt, twin)
        return Response(body, media_type=TEXT_MEDIA[fmt], headers=_text_headers(page.id, fmt))

    @app.get(
        "/api/works/{work_id}/text",
        summary="A work's transcription as plain text, page by page",
        description=(
            "Every page of a work in canvas order, streamed: the work's `# ` header, then "
            "per page a `## Folio <label> — <page_id>` line, its source image and model, "
            "and its recognised lines; a page without recognised text gets a one-line note."
        ),
        response_class=PlainTextResponse,
        responses=TEXT_RESPONSES,
    )
    def api_work_text(work_id: str, fmt: TextFormat = "txt") -> StreamingResponse:
        conn = _open(db_path)
        try:
            work = db.get_work(conn, work_id)
            if work is None:
                raise HTTPException(404, f"work {work_id} not found")
            pages = db.get_pages(conn, work_id)
            summaries = line_summaries_by_page(conn, work_id)
        finally:
            conn.close()
        return StreamingResponse(
            _work_text(db_path, site, titled(work), pages, summaries, fmt, twins()),
            media_type=TEXT_MEDIA[fmt],
            headers=_text_headers(work.gwlb_object_id, fmt),
        )

    # A catalogue record names a piece; its shelfmark's ``Bl.`` range places it
    # on the work's folios (leibniz.web.pieces). The route has no JSON sibling:
    # the records themselves travel with their work (/api/works/{work_id}).
    @app.get(
        "/api/records/{record_id}/text",
        summary="The text of a catalogue piece across its folios",
        description=(
            "The machine transcription of one piece of the Arbeitskatalog — a letter, a "
            "draft, a treatise — across the folios its shelfmark names, as a download in "
            "the work export's layout: a `# ` header naming the record (title, date, sender "
            "and addressee, Akademie-Ausgabe reference where known), the work, the folio "
            "range and the canvases, then one `## Folio <label> — <page_id>` block per page. "
            "The work's `katalog` entries in `/api/works/{work_id}` carry `text_url` where "
            "a record can be placed; a record that cannot be answers 404 with the reason."
        ),
        response_class=PlainTextResponse,
        responses=RECORD_RESPONSES,
    )
    def api_record_text(
        record_id: str,
        fmt: TextFormat = "txt",
        work: str | None = Query(
            None,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
            max_length=64,
            description="Place the record on this work (one it is linked to); default: its "
            "best-linked work that places it.",
        ),
    ) -> StreamingResponse:
        conn = _open(db_path)
        try:
            record = db.get_katalog_record(conn, record_id)
            if record is None:
                raise HTTPException(404, f"record {record_id} not found")
            placed = pieces.place_record(conn, record, work)
            if isinstance(placed, pieces.Unplaced):
                raise HTTPException(404, placed.reason)
            work = db.get_work(conn, placed.work_id)
            summaries = line_summaries_by_page(conn, placed.work_id)
        finally:
            conn.close()
        return StreamingResponse(
            _record_text(
                db_path, site, _record_dict(record), placed, titled(work), summaries, fmt, twins()
            ),
            media_type=TEXT_MEDIA[fmt],
            headers=_text_headers(f"record-{record_id}", fmt),
        )

    # ---- IIIF (D7) -------------------------------------------------------- #
    @app.get("/manifests/{work_id}")
    def manifest(work_id: str, request: Request) -> JSONResponse:
        conn = _open(db_path)
        try:
            work = db.get_work(conn, work_id)
            if work is None:
                raise HTTPException(404, f"work {work_id} not found")
            pages = db.get_pages(conn, work_id)
            if not pages:  # a manifest must paint at least one canvas
                raise HTTPException(404, f"work {work_id} has no page images")
            counts = {pid: n for pid, (n, _) in line_summaries_by_page(conn, work_id).items()}
            sources = (
                {p.id: images.source_url(p) for p in pages if images.is_mirrored(p)}
                if images.mirrored
                else None
            )
            body = iiif.build_manifest(
                titled(work),
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
            # a spread page's canvas is the whole image; its annotations, its half
            shown, _ = _twin_lines(twins().get(page.id), page.id, lines)
            body = iiif.build_annotation_page(
                page,
                shown,
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

        # The same files twice: under /static/m/<build>/ for the module set the
        # shell names (any build answers with the current files, so a shell
        # from just before a restart still gets one consistent set), and under
        # /static/ for everything else. The versioned mount must come first.
        app.mount(
            MODULES_PREFIX + "/{build}", StaticFiles(directory=str(static_dir)), name="modules"
        )
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # The shell is read once and stamped with where images come from
        # (``<html data-image-origin>``) and, only when the operator has switched
        # it on, the game's origin (``data-calculemus-url``; absent otherwise,
        # so nothing about it reaches the page), so the viewer's attribution
        # and About text need no extra request. Each route then stamps its own
        # title, description, canonical URL and — for works and pages — a
        # server-rendered summary in place of ``<!--ll:ssr-->``, so that search
        # engines, answer engines and readers without JavaScript get the
        # content; app.js replaces it on boot. Every variant carries its own
        # ETag and is revalidated on every load (``no-cache``) so a deploy shows
        # at once; /static/* may be cached for an hour (see deploy/Caddyfile),
        # so the shell names its stylesheet, its boot script and the build of
        # its modules by content (``_version_assets``).
        shell = index_html.read_text(encoding="utf-8").replace(
            'data-image-origin="gwlb"', f'data-image-origin="{images.origin}"'
        )
        game_url = (calculemus_url or "").strip().rstrip("/")
        if game_url:
            shell = shell.replace("<html ", f'<html data-calculemus-url="{_esc(game_url)}" ', 1)
        shell = _version_assets(shell, static_dir)

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

        def serve_browse(request: Request) -> Response:
            index = browse_index()
            if "html" not in index:  # 2,000-odd links: stamped once
                title, description, ssr = _ssr_browse(index["families"])
                index["html"] = _stamp_shell(
                    shell,
                    path="/browse",
                    title=title,
                    description=description,
                    ssr=ssr,
                    site=site,
                )
            return respond(request, index["html"])

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
                katalog = _katalog_for_work(conn, work_id, pages)
            finally:
                conn.close()
            gwlb_url = attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id)
            place = browse_index()["places"].get(work.gwlb_object_id)
            title, description, ssr = _ssr_work(titled(work), pages, katalog, gwlb_url, place)
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
                twin = twins().get(page.id)
                lines, _ = _twin_lines(twin, page.id, latest_lines(conn, page_id))
                neighbours = conn.execute(
                    "SELECT page_id, seq FROM pages WHERE work_id = ? AND seq IN (?, ?)",
                    (page.work_id, page.seq - 1, page.seq + 1),
                ).fetchall()
            finally:
                conn.close()
            prev_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq - 1), None)
            next_id = next((r["page_id"] for r in neighbours if r["seq"] == page.seq + 1), None)
            shown = images.resolve(page)
            gwlb_url = attr.gwlb_page_url(page.work_id, page.seq)
            title, description, ssr = _ssr_page(
                page, titled(work), lines, shown.image_url, gwlb_url, prev_id, next_id, twin
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
            "/browse": serve_browse,
            "/about": serve_about,
            "/work/{work_id}": serve_index_work,
            "/page/{page_id}": serve_index_page,
        }
        for route in INDEX_ROUTES:
            app.add_api_route(
                route, handlers.get(route, serve_index), methods=["GET"], include_in_schema=False
            )

        # Discovery files at the root: the favicon browsers request blindly, the
        # sitemap (the browse index and one URL per work; the work pages link
        # every page), llms.txt.
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
