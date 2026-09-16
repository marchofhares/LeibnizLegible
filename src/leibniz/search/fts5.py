"""SQLite FTS5 search backend (Phase D1) — the dev/fallback index.

One file (``data/search.sqlite`` by default): a ``docs`` table with the page
documents and a **contentless** FTS5 table over the folded text (plus title,
shelfmarks and AA references, weighted up in ``bm25``). Query tokens of three
or more characters match as prefixes, which together with the shared folding
gives orthography tolerance; true typo tolerance is Meilisearch's job
(:mod:`leibniz.search.meili`). Filters (set, language, stratum, minimum
confidence, work) are plain column predicates on ``docs``.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterable
from pathlib import Path

from leibniz.search.backend import SearchHit, SearchQuery, SearchResult
from leibniz.search.documents import PageDoc
from leibniz.search.normalize import fold, query_terms
from leibniz.search.snippet import PREFIX_MIN, make_snippet

DEFAULT_INDEX_PATH = "data/search.sqlite"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS docs (
    rowid       INTEGER PRIMARY KEY,
    page_id     TEXT NOT NULL UNIQUE,
    work_id     TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    label       TEXT,
    set_name    TEXT NOT NULL,
    title       TEXT,
    shelfmarks  TEXT NOT NULL,      -- JSON array
    n_lines     INTEGER NOT NULL,
    mean_conf   REAL,
    lang        TEXT NOT NULL,
    stratum     TEXT NOT NULL,
    thumb_url   TEXT,
    katalog     TEXT NOT NULL,      -- JSON array of record ids
    aa_refs     TEXT NOT NULL,      -- JSON array of "AA I,3 N. 12" labels
    text        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_docs_work    ON docs (work_id);
CREATE INDEX IF NOT EXISTS ix_docs_set     ON docs (set_name);
CREATE INDEX IF NOT EXISTS ix_docs_lang    ON docs (lang);
CREATE INDEX IF NOT EXISTS ix_docs_stratum ON docs (stratum);
CREATE INDEX IF NOT EXISTS ix_docs_conf    ON docs (mean_conf);
CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
    folded, title, shelfmarks, aa_refs,
    content='', tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""

# bm25 column weights: a hit in the title / shelfmark / AA reference outranks
# one in the body text (the body dominates by length otherwise).
_BM25 = "bm25(docs_fts, 1.0, 3.0, 3.0, 3.0)"


def match_expression(terms: list[str]) -> str:
    """FTS5 MATCH expression: quoted terms ANDed, prefix-matched from ``PREFIX_MIN``."""
    parts: list[str] = []
    for t in terms:
        t = t.replace('"', "")
        if not t:
            continue
        parts.append(f'"{t}"*' if len(t) >= PREFIX_MIN else f'"{t}"')
    return " ".join(parts)


class Fts5Backend:
    name = "fts5"

    def __init__(self, path: str | Path = DEFAULT_INDEX_PATH) -> None:
        self.path = Path(path)

    # -- connections ------------------------------------------------------- #
    def _connect(self) -> sqlite3.Connection:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure(self, conn: sqlite3.Connection) -> None:
        conn.executescript(SCHEMA_SQL)

    # -- build ------------------------------------------------------------- #
    def rebuild(
        self, docs: Iterable[PageDoc], *, meta: dict | None = None, batch: int = 500
    ) -> int:
        conn = self._connect()
        try:
            conn.executescript(
                "DROP TABLE IF EXISTS docs_fts; DROP TABLE IF EXISTS docs; "
                "DROP TABLE IF EXISTS meta;"
            )
            self._ensure(conn)
            n = 0
            pending: list[PageDoc] = []

            def flush() -> None:
                nonlocal n
                if not pending:
                    return
                with conn:
                    for d in pending:
                        cur = conn.execute(
                            """
                            INSERT INTO docs (page_id, work_id, seq, label, set_name, title,
                                              shelfmarks, n_lines, mean_conf, lang, stratum,
                                              thumb_url, katalog, aa_refs, text)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                d.page_id,
                                d.work_id,
                                d.seq,
                                d.label,
                                d.set_name,
                                d.title,
                                json.dumps(d.shelfmarks, ensure_ascii=False),
                                d.n_lines,
                                d.mean_conf,
                                d.lang,
                                d.stratum,
                                d.thumb_url,
                                json.dumps(d.katalog),
                                json.dumps(d.aa_refs, ensure_ascii=False),
                                d.text,
                            ),
                        )
                        conn.execute(
                            "INSERT INTO docs_fts (rowid, folded, title, shelfmarks, aa_refs) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (
                                cur.lastrowid,
                                fold(d.text),
                                fold(d.title),
                                fold(" ".join(d.shelfmarks)),
                                fold(" ".join(d.aa_refs)),
                            ),
                        )
                        n += 1
                pending.clear()

            for doc in docs:
                pending.append(doc)
                if len(pending) >= batch:
                    flush()
            flush()
            info = dict(meta or {})
            info.update(
                {
                    "backend": self.name,
                    "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "n_docs": n,
                }
            )
            with conn:
                for k, v in info.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (k, json.dumps(v))
                    )
            conn.execute("PRAGMA optimize")
            return n
        finally:
            conn.close()

    # -- query ------------------------------------------------------------- #
    @staticmethod
    def _filters(q: SearchQuery) -> tuple[str, list[object]]:
        clauses: list[str] = []
        params: list[object] = []
        if q.set_name:
            clauses.append("d.set_name = ?")
            params.append(q.set_name)
        if q.lang:
            clauses.append("d.lang = ?")
            params.append(q.lang)
        if q.stratum:
            clauses.append("d.stratum = ?")
            params.append(q.stratum)
        if q.min_conf is not None:
            clauses.append("d.mean_conf >= ?")
            params.append(q.min_conf)
        if q.work_id:
            clauses.append("d.work_id = ?")
            params.append(q.work_id)
        return (" AND " + " AND ".join(clauses)) if clauses else "", params

    def search(self, query: SearchQuery) -> SearchResult:
        q = query.normalized()
        t0 = time.perf_counter()
        terms = query_terms(q.q)
        empty = SearchResult(q.q, 0, q.page, q.limit, 0, self.name, [])
        if not terms:
            return empty
        if str(self.path) != ":memory:" and not self.path.exists():
            return empty
        match = match_expression(terms)
        where, params = self._filters(q)
        conn = self._connect()
        try:
            self._ensure(conn)
            total = conn.execute(
                "SELECT COUNT(*) FROM docs_fts f JOIN docs d ON d.rowid = f.rowid "
                f"WHERE docs_fts MATCH ?{where}",
                [match, *params],
            ).fetchone()[0]
            rows = conn.execute(
                f"SELECT d.*, {_BM25} AS score FROM docs_fts f JOIN docs d ON d.rowid = f.rowid "
                f"WHERE docs_fts MATCH ?{where} ORDER BY score LIMIT ? OFFSET ?",
                [match, *params, q.limit, q.offset],
            ).fetchall()
        finally:
            conn.close()
        hits = [
            SearchHit(
                page_id=r["page_id"],
                work_id=r["work_id"],
                seq=r["seq"],
                label=r["label"],
                set_name=r["set_name"],
                title=r["title"],
                shelfmarks=json.loads(r["shelfmarks"]),
                snippet=make_snippet(r["text"], terms),
                n_lines=r["n_lines"],
                mean_conf=r["mean_conf"],
                lang=r["lang"],
                stratum=r["stratum"],
                thumb_url=r["thumb_url"],
                score=round(-float(r["score"]), 4),
            )
            for r in rows
        ]
        took = int((time.perf_counter() - t0) * 1000)
        return SearchResult(q.q, int(total), q.page, q.limit, took, self.name, hits)

    # -- introspection ----------------------------------------------------- #
    def meta(self) -> dict:
        if str(self.path) != ":memory:" and not self.path.exists():
            return {}
        conn = self._connect()
        try:
            self._ensure(conn)
            return {r["key"]: json.loads(r["value"]) for r in conn.execute("SELECT * FROM meta")}
        finally:
            conn.close()

    def count(self) -> int:
        if str(self.path) != ":memory:" and not self.path.exists():
            return 0
        conn = self._connect()
        try:
            self._ensure(conn)
            return int(conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
        finally:
            conn.close()

    def health(self) -> bool:
        """The index file exists (``:memory:`` counts as present)."""
        return str(self.path) == ":memory:" or self.path.exists()


__all__ = ["DEFAULT_INDEX_PATH", "Fts5Backend", "match_expression"]
