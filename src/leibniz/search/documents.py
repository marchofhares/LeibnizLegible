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
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, field

from leibniz import db
from leibniz.align.resolve import folio_span_from_signature, index_pages, select_span
from leibniz.images.twins import TwinGroup, TwinStats, resolve_work

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
    # the folio labels the same scan is also registered under, where this
    # page carries the text for all of them (leibniz.images.twins, a fold)
    also: list[str] = field(default_factory=list)
    # the titles of the catalogue pieces whose folios this page carries
    pieces: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def meta_text(self) -> str:
        """What names the page besides its text: the work's title and shelfmarks,
        the catalogue's AA references, the folio label (and the labels the scan
        is also registered under). The index folds it as it folds the text, so
        "VI" (folded "ui") meets "AA VI,4 N. 109"; indexed as written, a quoted
        reference found nothing and an AA number few pages (STATUS Open
        question 21)."""
        parts = [self.title or "", *self.shelfmarks, *self.aa_refs, *self.pieces]
        parts += [f"fol {label}" for label in (self.label, *self.also) if label]
        return " ".join(p for p in parts if p)


def latest_lines(
    conn: sqlite3.Connection,
    page_id: str,
    *,
    as_of_run: int | None = None,
    precedences: Mapping[int, int] | None = None,
) -> list[db.Line]:
    """A page's current lines in reading order, one per ``line_seq``.

    ``lines`` is unique on ``(page_id, line_seq, run_id)``, so a page read by
    more than one run carries a row per run; the viewer and the index show one
    and keep the others as provenance. Which one is the store layer's rule
    (:func:`leibniz.db.current_lines`): a corrections run first, then a run
    scoped to a language (K4's Kurrent run on the German pages), then the
    newest unscoped run — so the name says *latest* and the rule says *current*,
    and C4's newer Latin-and-French run leaves the German pages alone.
    ``as_of_run`` reads the page as that run left it — rows of later runs
    ignored — which is what a citation pinned to a run (``?run=``) shows.
    """
    return db.current_lines(conn, page_id, as_of_run=as_of_run, precedences=precedences)


def line_summaries_by_page(
    conn: sqlite3.Connection, work_id: str
) -> dict[str, tuple[int, float | None]]:
    """Per page of a work, ``(n_lines, mean_conf)`` over the current row per line — one query.

    The same rule as :func:`latest_lines` (the store layer's precedence —
    corrections, then a scoped run, then the newest run; ``NULL`` run ids count
    as 0 — then only lines with text) for a whole work at once, so the work
    and manifest endpoints run one query instead of one per page. A line row
    is current when no row of the same ``(page_id, line_seq)`` outranks it
    (:func:`leibniz.db.current_predicate`); the ``NOT EXISTS`` probe walks the
    table's covering unique index and settles a rival's rank with one lookup
    in the small ``runs`` table. Measured on a synthetic 3,500-page work of
    57 lines a page (2026-10-26: a scoped run on every tenth page with every
    fifth line unwritten, a newer unscoped run on another tenth, 235,550
    rows; best of five): the run-id-only probe of 2026-09 154 ms, this
    ranked probe 227 ms, the per-page loop over ``latest_lines`` 1,683 ms
    (it decodes every row's geometry). Pages without recognised text are
    absent from the result.
    """
    rows = conn.execute(
        f"""
        WITH {db.run_rank_cte(conn)}
        SELECT l.page_id, COUNT(*) AS n, AVG(l.conf) AS c
          FROM lines l LEFT JOIN rk lr ON lr.run_id = l.run_id
         WHERE l.page_id IN (SELECT page_id FROM pages WHERE work_id = ?)
           AND l.text IS NOT NULL AND l.text != ''
           AND {db.current_predicate("l", "lr")}
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
                "shelfmark_refs": json.loads(row["shelfmark_refs"])
                if row["shelfmark_refs"]
                else [],
            }
        )
    return dict(out)


def _majority_lang(lines: list[db.Line]) -> str:
    counts = Counter(ln.lang for ln in lines if ln.lang)
    if not counts:
        return "unknown"
    lang, _ = counts.most_common(1)[0]
    return lang if lang in db.LINE_LANGS else "unknown"


def page_lang_of(
    conn: sqlite3.Connection,
    page_id: str,
    lines: list[db.Line],
    *,
    page_langs: Mapping[str, str] | None = None,
) -> str:
    """The language the index files a page under: the ``page_lang`` row where
    K4 wrote one (``page_langs`` is the work's rows read in one query, else
    the page's row is looked up), otherwise the majority of the lines' own
    ``lang`` (``unknown`` until C4 fills it)."""
    if page_langs is not None:
        lang = page_langs.get(page_id)
    else:
        row = db.get_page_lang(conn, page_id)
        lang = row.lang if row is not None else None
    if lang in db.LINE_LANGS:
        return lang
    return _majority_lang(lines)


def page_doc(
    conn: sqlite3.Connection,
    page: db.Page,
    work: db.Work,
    *,
    katalog: list[dict] | None = None,
    stratum: str | None = None,
    lines: list[db.Line] | None = None,
    twin: TwinGroup | None = None,
    pieces: list[str] | None = None,
    page_langs: Mapping[str, str] | None = None,
) -> PageDoc | None:
    """Build the document for one page, or ``None`` if it has no recognised text.

    ``lines`` are the page's current lines where the caller has read them
    already. ``twin`` is the page's group where its scan is registered more
    than once: a spread page indexes its own half, a fold indexes the text once,
    on its primary page, which names the other labels (``also``). ``page_langs``
    is the work's ``page_lang`` rows where the caller has read them.
    """
    if lines is None:
        lines = latest_lines(conn, page.id)
    lines = [ln for ln in lines if ln.text]
    also: list[str] = []
    if twin is not None:
        if not twin.carries_text(page.id):
            return None
        lines = [ln for ln, _ in twin.own_lines(page.id, lines, for_index=True)]
        if twin.kind == "fold":
            also = [label for _, label in twin.others(page.id) if label]
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
        lang=page_lang_of(conn, page.id, lines, page_langs=page_langs),
        stratum=stratum if stratum in db.GT_STRATA else "unknown",
        thumb_url=page.thumb_url,
        katalog=[r["record_id"] for r in recs],
        aa_refs=sorted({lab for r in recs for lab in r["aa_labels"]}),
        also=also,
        pieces=list(pieces or []),
    )


def iter_page_docs(
    conn: sqlite3.Connection,
    *,
    set_name: str | None = None,
    work_id: str | None = None,
    limit: int | None = None,
    twins_out: list[TwinGroup] | None = None,
    twin_stats: TwinStats | None = None,
) -> Iterator[PageDoc]:
    """Yield a document for every recognised page (optionally one set / work).

    Scans registered more than once are found work by work as the lines are
    read (:func:`leibniz.images.twins.resolve_work`) and indexed once: a spread
    as its two halves, a fold on one page. ``twins_out`` collects the groups
    and ``twin_stats`` counts them, for the file the web application reads.
    """
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
    prec = db.run_precedences(conn)
    for work in works:
        pages = db.get_pages(conn, work.gwlb_object_id)
        groups, read = resolve_work(
            pages, lambda pid: latest_lines(conn, pid, precedences=prec), twin_stats
        )
        if twins_out is not None:
            twins_out.extend(groups)
        twin_of = {pid: group for group in groups for pid in group.pages}
        records = kat.get(work.gwlb_object_id) or []
        on_page = records_by_page(work.gwlb_object_id, pages, records)
        page_langs = db.page_langs_for_work(conn, work.gwlb_object_id)
        for page in pages:
            if page.status != "recognized":
                continue
            here = on_page.get(page.id, [])
            doc = page_doc(
                conn,
                page,
                work,
                katalog=[r for r in records if r.get("_placed") is None] + here,
                lines=read.pop(page.id, None),
                twin=twin_of.get(page.id),
                pieces=[t for r in here if (t := piece_title(r))],
                page_langs=page_langs,
            )
            if doc is None:
                continue
            yield doc
            n += 1
            if limit is not None and n >= limit:
                return


def piece_title(record: dict) -> str | None:
    """A catalogue record's title, one line."""
    meta = record.get("metadata") or {}
    title = meta.get("titel") or meta.get("title")
    return " ".join(str(title).split()) if title else None


def records_by_page(
    work_id: str, pages: list[db.Page], records: list[dict]
) -> dict[str, list[dict]]:
    """The catalogue records of a work, by the pages their folios cover (the C2
    rule, :func:`leibniz.align.resolve.select_span`). A placed record is marked
    ``_placed``; one that cannot be placed stays the whole work's (its AA
    reference names every page, as before 2026-10)."""
    index = index_pages(pages)
    out: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        record.pop("_placed", None)
        span = next(
            (s for m in record.get("shelfmark_refs") or [] if (s := folio_span_from_signature(m))),
            None,
        )
        if span is None:
            continue
        found = select_span(index, work_id, span)
        if not found.resolved:
            continue
        record["_placed"] = True
        for page in found.pages:
            out[page.id].append(record)
    return dict(out)


CONF_BANDS: tuple[tuple[str, float, float], ...] = (
    ("lt_0.5", -1.0, 0.5),
    ("0.5_0.7", 0.5, 0.7),
    ("0.7_0.8", 0.7, 0.8),
    ("0.8_0.9", 0.8, 0.9),
    ("ge_0.9", 0.9, 2.0),
)


def corpus_stats(conn: sqlite3.Connection) -> dict:
    """Corpus-wide counts for the About page / ``/api/stats``: the lines the
    store shows under the rule (one row per line), their confidence histogram
    and the models by line count, each a scan of the ``lines`` table with the
    current-row predicate (:func:`leibniz.db.current_predicate`); the pages by
    language from ``page_lang`` (K4; empty before its write)."""
    hist = conn.execute("SELECT status, COUNT(*) FROM pages GROUP BY status").fetchall()
    by_status = {row[0]: row[1] for row in hist}
    current = (
        f"WITH {db.run_rank_cte(conn)} SELECT {{what}} FROM lines l"
        " LEFT JOIN rk lr ON lr.run_id = l.run_id"
        f" WHERE l.text IS NOT NULL AND l.text != '' AND {db.current_predicate('l', 'lr')}"
    )
    conf_hist: dict[str, int] = {}
    for key, lo, hi in CONF_BANDS:
        conf_hist[key] = conn.execute(
            current.format(what="COUNT(*)")
            + " AND l.conf IS NOT NULL AND l.conf >= ? AND l.conf < ?",
            (lo, hi),
        ).fetchone()[0]
    by_model = conn.execute(
        current.format(what="l.model, COUNT(*) AS n")
        + " AND l.model IS NOT NULL GROUP BY l.model ORDER BY n DESC"
    ).fetchall()
    return {
        "works": db.count_works(conn),
        "pages": db.count_pages(conn),
        "pages_recognized": by_status.get("recognized", 0),
        "pages_skipped": by_status.get("skipped", 0),
        "lines": db.count_current_lines(conn),
        "conf_histogram": conf_hist,
        "model": by_model[0][0] if by_model else None,
        "models": {r[0]: int(r[1]) for r in by_model},
        "pages_by_lang": db.count_page_lang(conn),
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
    "page_lang_of",
    "piece_title",
    "records_by_page",
]
