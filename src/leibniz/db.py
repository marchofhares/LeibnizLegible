"""Canonical store — SQLite schema and a thin typed access layer.

The whole pipeline shares one SQLite file (default ``data/inventory.sqlite``,
SPECS §4.3). No ORM: just ``sqlite3`` plus small typed helpers. Enums are TEXT
columns with ``CHECK`` constraints; JSON blobs are TEXT. Foreign keys are on.

Tables (SPECS §4.3): ``works``, ``pages``, ``lines``, ``katalog_records``,
``crosswalk``, ``gt_lines``, ``runs``.

ID scheme (SPECS §4.4, COMMON CONTEXT): a page id is
``"{gwlb_object_id}:{canvas_seq:04d}"`` (e.g. ``00068642:0007``) and a line id
is the page id plus ``":{line_seq:03d}"``. Shelfmarks are attributes, not keys.

The ``lines`` table is append-per-run: its natural key
``(page_id, line_seq, run_id)`` is unique, but the canonical ``line_id`` string
is *not* (the same physical line recurs across recognition runs). The
current-run-pointer vs. version-rows decision is deferred to Phase C4; A0 only
lays the table down.

At scaffold time (A0) only ``works`` and ``pages`` get typed insert/query
helpers — the stages that own the other tables add theirs as they land.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

# Default location of the canonical store (gitignored; see data/README.md).
DEFAULT_DB_PATH = Path("data/inventory.sqlite")

# Controlled vocabularies, mirrored by the CHECK constraints below. Exposed so
# callers and tests can reference them instead of hard-coding string literals.
PAGE_STATUSES = ("pending", "segmented", "recognized", "skipped")
LINE_STATUSES = ("machine", "aligned", "corrected", "verified")
LINE_LANGS = ("la", "fr", "de", "mixed", "unknown")
GT_STRATA = ("fair_copy", "light_revision", "heavy_revision", "scrap", "unknown")
LICENSE_BUCKETS = ("open", "nc")

TABLE_NAMES = (
    "works",
    "pages",
    "lines",
    "katalog_records",
    "crosswalk",
    "gt_lines",
    "runs",
)

# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS works (
    gwlb_object_id  TEXT PRIMARY KEY,           -- 8-digit GWLB object id
    set_name        TEXT NOT NULL,              -- OAI set (the SPECS 'set' field)
    title           TEXT,
    shelfmarks      TEXT,                        -- JSON array of shelfmark strings
    metadata        TEXT,                        -- JSON: METS/MODS-derived metadata
    manifest_url    TEXT,
    n_canvases      INTEGER
);

CREATE TABLE IF NOT EXISTS pages (
    page_id             TEXT PRIMARY KEY,        -- "{work_id}:{seq:04d}"
    work_id             TEXT NOT NULL REFERENCES works(gwlb_object_id),
    seq                 INTEGER NOT NULL,        -- canvas_seq (1-based)
    canvas_id           TEXT,
    image_service_url   TEXT,                    -- IIIF Image API service base
    width               INTEGER,
    height              INTEGER,
    status              TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','segmented','recognized','skipped')),
    skip_reason         TEXT,                    -- set when status='skipped'
    UNIQUE (work_id, seq)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY,
    stage       TEXT NOT NULL,                   -- harvest/segment/recognize/enrich/align/...
    model       TEXT,                            -- name@version
    params      TEXT,                            -- JSON
    started_at  TEXT,                            -- ISO-8601
    finished_at TEXT,
    n_input     INTEGER,
    n_ok        INTEGER,
    n_failed    INTEGER,
    git_sha     TEXT
);

CREATE TABLE IF NOT EXISTS lines (
    id          INTEGER PRIMARY KEY,             -- surrogate; line_id is not unique across runs
    line_id     TEXT NOT NULL,                   -- canonical "{page_id}:{line_seq:03d}"
    page_id     TEXT NOT NULL REFERENCES pages(page_id),
    line_seq    INTEGER NOT NULL,
    baseline    TEXT,                            -- JSON
    polygon     TEXT,                            -- JSON
    text        TEXT,
    conf        REAL,                            -- 0..1
    model       TEXT,                            -- name@version
    run_id      INTEGER REFERENCES runs(run_id),
    status      TEXT NOT NULL
                    CHECK (status IN ('machine','aligned','corrected','verified')),
    lang        TEXT CHECK (lang IN ('la','fr','de','mixed','unknown')),
    source      TEXT,                            -- JSON: who/what for non-machine statuses
    UNIQUE (page_id, line_seq, run_id)
);

CREATE TABLE IF NOT EXISTS katalog_records (
    record_id               TEXT PRIMARY KEY,
    metadata                TEXT,                -- JSON: katalog record fields
    shelfmark_refs          TEXT,                -- JSON array
    aa_refs                 TEXT,                -- JSON array of {series,volume,piece}
    transcription_snippet   TEXT
);

CREATE TABLE IF NOT EXISTS crosswalk (
    id                  INTEGER PRIMARY KEY,
    katalog_record_id   TEXT NOT NULL REFERENCES katalog_records(record_id),
    work_id             TEXT NOT NULL REFERENCES works(gwlb_object_id),
    page_range          TEXT,                    -- where derivable
    match_method        TEXT NOT NULL,           -- gwlb_link/shelfmark/manual/...
    match_conf          REAL,
    UNIQUE (katalog_record_id, work_id)
);

CREATE TABLE IF NOT EXISTS gt_lines (
    id              INTEGER PRIMARY KEY,
    line_image_ref  TEXT NOT NULL,               -- image URI + region (or local path)
    text            TEXT NOT NULL,
    source          TEXT NOT NULL,               -- AA volume/page | transkriptionspool | manual
    stratum         TEXT CHECK (stratum IN
                        ('fair_copy','light_revision','heavy_revision','scrap','unknown')),
    align_conf      REAL,
    license_bucket  TEXT NOT NULL CHECK (license_bucket IN ('open','nc'))
);

CREATE INDEX IF NOT EXISTS ix_pages_work    ON pages (work_id);
CREATE INDEX IF NOT EXISTS ix_pages_status  ON pages (status);
CREATE INDEX IF NOT EXISTS ix_lines_page    ON lines (page_id);
CREATE INDEX IF NOT EXISTS ix_lines_run     ON lines (run_id);
CREATE INDEX IF NOT EXISTS ix_cross_work    ON crosswalk (work_id);
CREATE INDEX IF NOT EXISTS ix_cross_record  ON crosswalk (katalog_record_id);
CREATE INDEX IF NOT EXISTS ix_gt_bucket     ON gt_lines (license_bucket);
"""


# --------------------------------------------------------------------------- #
# ID helpers
# --------------------------------------------------------------------------- #


def page_id(work_id: str, seq: int) -> str:
    """Canonical page id: ``"{work_id}:{seq:04d}"`` (SPECS §4.4)."""
    return f"{work_id}:{seq:04d}"


def line_id(page_id_: str, line_seq: int) -> str:
    """Canonical line id: page id plus ``":{line_seq:03d}"`` (SPECS §4.4)."""
    return f"{page_id_}:{line_seq:03d}"


# --------------------------------------------------------------------------- #
# Connection / init
# --------------------------------------------------------------------------- #


def connect(path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection with foreign keys on and ``Row`` access by name.

    ``":memory:"`` is accepted for tests. A file path's parent directory is
    created if missing.
    """
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create the schema if absent and return an open connection.

    Idempotent: every statement is ``IF NOT EXISTS``, so calling it on an
    existing store is a no-op that just hands back a connection.
    """
    conn = connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


@contextmanager
def open_db(path: str | Path = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    """Context manager wrapping :func:`init_db`; commits on exit, always closes."""
    conn = init_db(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Typed rows: works + pages (A0 scope)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Work:
    """A GWLB object (a work/convolute), keyed by its 8-digit object id."""

    gwlb_object_id: str
    set_name: str
    title: str | None = None
    shelfmarks: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    manifest_url: str | None = None
    n_canvases: int | None = None


@dataclass(slots=True)
class Page:
    """One canvas of a work. ``id`` is derived from ``work_id`` + ``seq``."""

    work_id: str
    seq: int
    canvas_id: str | None = None
    image_service_url: str | None = None
    width: int | None = None
    height: int | None = None
    status: str = "pending"
    skip_reason: str | None = None

    @property
    def id(self) -> str:
        """Canonical page id."""
        return page_id(self.work_id, self.seq)


def _work_from_row(row: sqlite3.Row) -> Work:
    return Work(
        gwlb_object_id=row["gwlb_object_id"],
        set_name=row["set_name"],
        title=row["title"],
        shelfmarks=json.loads(row["shelfmarks"]) if row["shelfmarks"] else [],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        manifest_url=row["manifest_url"],
        n_canvases=row["n_canvases"],
    )


def _page_from_row(row: sqlite3.Row) -> Page:
    return Page(
        work_id=row["work_id"],
        seq=row["seq"],
        canvas_id=row["canvas_id"],
        image_service_url=row["image_service_url"],
        width=row["width"],
        height=row["height"],
        status=row["status"],
        skip_reason=row["skip_reason"],
    )


def upsert_work(conn: sqlite3.Connection, work: Work) -> None:
    """Insert a work, or update it in place if the object id already exists.

    Cache-first harvesting re-runs against the same store, so writes are
    idempotent by design.
    """
    conn.execute(
        """
        INSERT INTO works
            (gwlb_object_id, set_name, title, shelfmarks, metadata, manifest_url, n_canvases)
        VALUES (:gwlb_object_id, :set_name, :title, :shelfmarks, :metadata,
                :manifest_url, :n_canvases)
        ON CONFLICT(gwlb_object_id) DO UPDATE SET
            set_name     = excluded.set_name,
            title        = excluded.title,
            shelfmarks   = excluded.shelfmarks,
            metadata     = excluded.metadata,
            manifest_url = excluded.manifest_url,
            n_canvases   = excluded.n_canvases
        """,
        {
            "gwlb_object_id": work.gwlb_object_id,
            "set_name": work.set_name,
            "title": work.title,
            "shelfmarks": json.dumps(work.shelfmarks) if work.shelfmarks else None,
            "metadata": json.dumps(work.metadata) if work.metadata else None,
            "manifest_url": work.manifest_url,
            "n_canvases": work.n_canvases,
        },
    )


def get_work(conn: sqlite3.Connection, gwlb_object_id: str) -> Work | None:
    """Fetch a work by object id, or ``None`` if absent."""
    row = conn.execute("SELECT * FROM works WHERE gwlb_object_id = ?", (gwlb_object_id,)).fetchone()
    return _work_from_row(row) if row is not None else None


def iter_works(conn: sqlite3.Connection, set_name: str | None = None) -> Iterator[Work]:
    """Iterate works, optionally filtered to one OAI set, ordered by id."""
    if set_name is None:
        cur = conn.execute("SELECT * FROM works ORDER BY gwlb_object_id")
    else:
        cur = conn.execute(
            "SELECT * FROM works WHERE set_name = ? ORDER BY gwlb_object_id",
            (set_name,),
        )
    for row in cur:
        yield _work_from_row(row)


def count_works(conn: sqlite3.Connection) -> int:
    """Total number of works."""
    return conn.execute("SELECT COUNT(*) FROM works").fetchone()[0]


def upsert_page(conn: sqlite3.Connection, page: Page) -> None:
    """Insert a page, or update it in place if ``(work_id, seq)`` already exists."""
    conn.execute(
        """
        INSERT INTO pages
            (page_id, work_id, seq, canvas_id, image_service_url, width, height,
             status, skip_reason)
        VALUES (:page_id, :work_id, :seq, :canvas_id, :image_service_url, :width,
                :height, :status, :skip_reason)
        ON CONFLICT(page_id) DO UPDATE SET
            canvas_id         = excluded.canvas_id,
            image_service_url = excluded.image_service_url,
            width             = excluded.width,
            height            = excluded.height,
            status            = excluded.status,
            skip_reason       = excluded.skip_reason
        """,
        {
            "page_id": page.id,
            "work_id": page.work_id,
            "seq": page.seq,
            "canvas_id": page.canvas_id,
            "image_service_url": page.image_service_url,
            "width": page.width,
            "height": page.height,
            "status": page.status,
            "skip_reason": page.skip_reason,
        },
    )


def get_page(conn: sqlite3.Connection, page_id_: str) -> Page | None:
    """Fetch a page by its canonical id, or ``None`` if absent."""
    row = conn.execute("SELECT * FROM pages WHERE page_id = ?", (page_id_,)).fetchone()
    return _page_from_row(row) if row is not None else None


def get_pages(conn: sqlite3.Connection, work_id: str) -> list[Page]:
    """All pages of a work, ordered by canvas sequence."""
    cur = conn.execute("SELECT * FROM pages WHERE work_id = ? ORDER BY seq", (work_id,))
    return [_page_from_row(row) for row in cur]


def count_pages(conn: sqlite3.Connection) -> int:
    """Total number of pages."""
    return conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
