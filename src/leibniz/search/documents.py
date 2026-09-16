"""Index documents from the canonical store (Phase D1).

One :class:`PageDoc` per page with recognised text: the page's lines in reading
order (the latest recognition run per line), the work's title/shelfmarks/set,
the folio label, per-page aggregates (line count, mean confidence, majority
language, the C4 stratum heuristic when present) and the katalog records the
crosswalk attaches to the work, rendered as AA references so a query like
``"I,3 N. 12"`` finds the piece. Pure reads; no writes to the store.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field

from leibniz import db

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}


@dataclass(slots=True)
class PageDoc:
    """One search document (a recognised page)."""

    page_id: str
    work_id: str
    seq: int
    label: str | None
    set_name: str
    title: str | None
    shelfmarks: list[str]
    text: str
    n_lines: int
    mean_conf: float | None
    lang: str
    stratum: str
    thumb_url: str | None
    katalog: list[str] = field(default_factory=list)
    aa_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def latest_lines(conn: sqlite3.Connection, page_id: str) -> list[db.Line]:
    """A page's lines in reading order, one per ``line_seq`` (latest run wins).

    ``lines`` is unique on ``(page_id, line_seq, run_id)``, so a page re-run by a
    later model (C4) may carry two rows per line; the viewer and the index show
    the most recent recognition and keep the older rows as provenance.
    """
    best: dict[int, db.Line] = {}
    for line in db.iter_lines_for_page(conn, page_id):
        cur = best.get(line.line_seq)
        if cur is None or (line.run_id or 0) >= (cur.run_id or 0):
            best[line.line_seq] = line
    return [best[k] for k in sorted(best)]


def line_summaries_by_page(
    conn: sqlite3.Connection, work_id: str
) -> dict[str, tuple[int, float | None]]:
    """Per page of a work, ``(n_lines, mean_conf)`` over the latest run per line — one query.

    The same rule as :func:`latest_lines` (latest run wins — ``NULL`` run ids
    count as 0 — then only lines with text) for a whole work at once, so the
    work and manifest endpoints run one query instead of one per page. A line
    row is current when no row of the same ``(page_id, line_seq)`` has a
    higher run id; the ``NOT EXISTS`` probe uses the table's covering unique
    index and measured fastest of five plans on a synthetic 3,500-page work
    (180 ms against 228 ms for the per-page loop; ``GROUP BY``/window forms
    were slower). Pages without recognised text are absent from the result.
    """
    rows = conn.execute(
        """
        SELECT l.page_id, COUNT(*) AS n, AVG(l.conf) AS c
          FROM lines l
         WHERE l.page_id IN (SELECT page_id FROM pages WHERE work_id = ?)
           AND l.text IS NOT NULL AND l.text != ''
           AND NOT EXISTS (SELECT 1 FROM lines x
                            WHERE x.page_id = l.page_id AND x.line_seq = l.line_seq
                              AND COALESCE(x.run_id, 0) > COALESCE(l.run_id, 0))
         GROUP BY l.page_id
        """,
        (work_id,),
    ).fetchall()
    return {
        r["page_id"]: (int(r["n"]), round(r["c"], 4) if r["c"] is not None else None) for r in rows
    }


def aa_ref_label(ref: dict) -> str | None:
    """Render a katalog AA reference (``{series, volume, piece}``) as ``AA I,3 N. 12``."""
    series = ref.get("series")
    volume = ref.get("volume")
    piece = ref.get("piece")
    if series is None or volume is None:
        return None
    try:
        s = ROMAN.get(int(series), str(series))
    except (TypeError, ValueError):
        s = str(series)
    out = f"AA {s},{volume}"
    if piece not in (None, ""):
        out += f" N. {piece}"
    return out


def katalog_by_work(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Work id → its crosswalked katalog records (record id, AA refs, match)."""
    out: dict[str, list[dict]] = defaultdict(list)
    cur = conn.execute(
        """
        SELECT c.work_id, c.katalog_record_id, c.match_method, c.match_conf,
               k.aa_refs, k.metadata, k.shelfmark_refs
          FROM crosswalk c
          JOIN katalog_records k ON k.record_id = c.katalog_record_id
         ORDER BY c.work_id, c.match_conf DESC, c.katalog_record_id
        """
    )
    for row in cur:
        aa_refs = json.loads(row["aa_refs"]) if row["aa_refs"] else []
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        out[row["work_id"]].append(
            {
                "record_id": row["katalog_record_id"],
                "match_method": row["match_method"],
                "match_conf": row["match_conf"],
                "aa_refs": aa_refs,
                "aa_labels": [lab for r in aa_refs if (lab := aa_ref_label(r))],
                "metadata": meta,
            }
        )
    return dict(out)


def _majority_lang(lines: list[db.Line]) -> str:
    counts = Counter(ln.lang for ln in lines if ln.lang)
    if not counts:
        return "unknown"
    lang, _ = counts.most_common(1)[0]
    return lang if lang in db.LINE_LANGS else "unknown"


def page_doc(
    conn: sqlite3.Connection,
    page: db.Page,
    work: db.Work,
    *,
    katalog: list[dict] | None = None,
    stratum: str | None = None,
) -> PageDoc | None:
    """Build the document for one page, or ``None`` if it has no recognised text."""
    lines = [ln for ln in latest_lines(conn, page.id) if ln.text]
    if not lines:
        return None
    confs = [ln.conf for ln in lines if ln.conf is not None]
    mean_conf = round(sum(confs) / len(confs), 4) if confs else None
    if stratum is None:
        ps = db.get_page_stats(conn, page.id)
        stratum = ps.stratum_heuristic if ps and ps.stratum_heuristic else "unknown"
    recs = katalog or []
    return PageDoc(
        page_id=page.id,
        work_id=work.gwlb_object_id,
        seq=page.seq,
        label=page.label,
        set_name=work.set_name,
        title=work.title,
        shelfmarks=list(work.shelfmarks or []),
        text="\n".join(ln.text or "" for ln in lines),
        n_lines=len(lines),
        mean_conf=mean_conf,
        lang=_majority_lang(lines),
        stratum=stratum if stratum in db.GT_STRATA else "unknown",
        thumb_url=page.thumb_url,
        katalog=[r["record_id"] for r in recs],
        aa_refs=sorted({lab for r in recs for lab in r["aa_labels"]}),
    )


def iter_page_docs(
    conn: sqlite3.Connection,
    *,
    set_name: str | None = None,
    work_id: str | None = None,
    limit: int | None = None,
) -> Iterator[PageDoc]:
    """Yield a document for every recognised page (optionally one set / work)."""
    kat = katalog_by_work(conn)
    n = 0
    sql = "SELECT * FROM works"
    params: list[object] = []
    if work_id:
        sql += " WHERE gwlb_object_id = ?"
        params.append(work_id)
    elif set_name:
        sql += " WHERE set_name = ?"
        params.append(set_name)
    sql += " ORDER BY gwlb_object_id"
    works = [db._work_from_row(r) for r in conn.execute(sql, params)]
    for work in works:
        for page in db.get_pages(conn, work.gwlb_object_id):
            if page.status != "recognized":
                continue
            doc = page_doc(conn, page, work, katalog=kat.get(work.gwlb_object_id))
            if doc is None:
                continue
            yield doc
            n += 1
            if limit is not None and n >= limit:
                return


CONF_BANDS: tuple[tuple[str, float, float], ...] = (
    ("lt_0.5", -1.0, 0.5),
    ("0.5_0.7", 0.5, 0.7),
    ("0.7_0.8", 0.7, 0.8),
    ("0.8_0.9", 0.8, 0.9),
    ("ge_0.9", 0.9, 2.0),
)


def corpus_stats(conn: sqlite3.Connection) -> dict:
    """Corpus-wide counts for the About page / ``/api/stats`` (one full scan)."""
    hist = conn.execute("SELECT status, COUNT(*) FROM pages GROUP BY status").fetchall()
    by_status = {row[0]: row[1] for row in hist}
    conf_hist: dict[str, int] = {}
    for key, lo, hi in CONF_BANDS:
        conf_hist[key] = conn.execute(
            "SELECT COUNT(*) FROM lines WHERE text IS NOT NULL AND text != '' "
            "AND conf IS NOT NULL AND conf >= ? AND conf < ?",
            (lo, hi),
        ).fetchone()[0]
    model = conn.execute(
        "SELECT model FROM lines WHERE model IS NOT NULL "
        "GROUP BY model ORDER BY COUNT(*) DESC LIMIT 1"
    ).fetchone()
    return {
        "works": db.count_works(conn),
        "pages": db.count_pages(conn),
        "pages_recognized": by_status.get("recognized", 0),
        "pages_skipped": by_status.get("skipped", 0),
        "lines": db.count_lines(conn, recognized=True),
        "conf_histogram": conf_hist,
        "model": model[0] if model else None,
    }


__all__ = [
    "CONF_BANDS",
    "PageDoc",
    "aa_ref_label",
    "corpus_stats",
    "iter_page_docs",
    "katalog_by_work",
    "latest_lines",
    "line_summaries_by_page",
    "page_doc",
]
