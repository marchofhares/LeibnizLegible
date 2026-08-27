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
import subprocess
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


def utcnow_iso() -> str:
    """Current UTC time as an ISO-8601 string (second granularity, ``Z``)."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_sha() -> str | None:
    """The current ``git HEAD`` sha, or ``None`` outside a repo — for run provenance."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


# Default location of the canonical store (gitignored; see data/README.md).
DEFAULT_DB_PATH = Path("data/inventory.sqlite")

# Controlled vocabularies, mirrored by the CHECK constraints below. Exposed so
# callers and tests can reference them instead of hard-coding string literals.
PAGE_STATUSES = ("pending", "segmented", "recognized", "skipped")
DELIVERY_MODES = ("iiif", "static")  # how a work's page images are served (SPECS §1.1 drift)
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
    image_service_url   TEXT,                    -- IIIF Image API base (IIIF works; D2)
    image_url           TEXT,                    -- delivery JPEG (METS DEFAULT); A2 caches it
    thumb_url           TEXT,                    -- thumbnail URL (METS THUMBS jpg)
    delivery            TEXT,                    -- 'iiif' | 'static': how images are served (D2)
    label               TEXT,                    -- folio label (METS ORDERLABEL / canvas label; C2)
    width               INTEGER,
    height              INTEGER,
    status              TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','segmented','recognized','skipped')),
    skip_reason         TEXT,                    -- set when status='skipped'
    -- Image-cache manifest (A2), written by `leibniz images fetch`; kept orthogonal
    -- to the pipeline `status` (a page can be cached while still 'pending' HTR).
    local_path          TEXT,                    -- cached file, relative to the images root
    n_bytes             INTEGER,                 -- size on disk
    sha256              TEXT,                    -- content checksum (integrity + resume key)
    fetched_at          TEXT,                    -- ISO-8601 timestamp the file was cached
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

-- Per-page segmentation statistics (C1). Not in the SPECS §4.3 canonical list —
-- a C1 extension (recorded in STATUS): the layout metrics the corpus segmenter
-- computes per page, kept queryable because the C4 stratum heuristic (and the C2
-- per-piece one) reads them across the corpus. One row per page, keyed to the
-- segmentation run that produced it. ``stratum_heuristic`` is left NULL by C1 and
-- filled by C2/C4 (honest field name: it is a heuristic, not a judgement).
CREATE TABLE IF NOT EXISTS page_stats (
    page_id             TEXT PRIMARY KEY REFERENCES pages(page_id),
    run_id              INTEGER REFERENCES runs(run_id),
    n_lines             INTEGER NOT NULL,
    n_regions           INTEGER,
    region_coverage     REAL,       -- Σ line-polygon area ÷ page area (0..1)
    mean_line_height    REAL,
    median_line_height  REAL,
    line_height_cv      REAL,       -- stdev/mean of line heights (revision-layer signal)
    n_overlaps          INTEGER,    -- line pairs whose boxes overlap (marginalia/layers)
    n_short_lines       INTEGER,    -- unusually short lines (interlinear/snippet signal)
    stratum_heuristic   TEXT,       -- filled by C2/C4; NULL under C1
    metrics             TEXT        -- JSON: full metric bag (forward-compat)
);

CREATE INDEX IF NOT EXISTS ix_pages_work    ON pages (work_id);
CREATE INDEX IF NOT EXISTS ix_pages_status  ON pages (status);
CREATE INDEX IF NOT EXISTS ix_lines_page    ON lines (page_id);
CREATE INDEX IF NOT EXISTS ix_lines_run     ON lines (run_id);
CREATE INDEX IF NOT EXISTS ix_lines_status  ON lines (status);
CREATE INDEX IF NOT EXISTS ix_cross_work    ON crosswalk (work_id);
CREATE INDEX IF NOT EXISTS ix_cross_record  ON crosswalk (katalog_record_id);
CREATE INDEX IF NOT EXISTS ix_gt_bucket     ON gt_lines (license_bucket);
CREATE INDEX IF NOT EXISTS ix_pstats_run    ON page_stats (run_id);
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
    # Sharded pipeline workers (segment --shard i/N) commit per page from N
    # processes at once: WAL lets readers and the other writers proceed instead
    # of erroring, and the busy timeout queues briefly-colliding commits.
    # Both are no-ops for ":memory:" test connections.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


# Columns added to ``pages`` after A0 (the image-cache manifest, A2). Fresh DBs
# get them from SCHEMA_SQL; DBs created by an earlier phase are upgraded in place
# by :func:`_migrate` (SQLite ``CREATE TABLE IF NOT EXISTS`` never alters columns).
_PAGES_ADDED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("image_url", "TEXT"),
    ("thumb_url", "TEXT"),
    ("delivery", "TEXT"),
    ("label", "TEXT"),  # folio label (C2 piece→canvas resolver)
    ("local_path", "TEXT"),
    ("n_bytes", "INTEGER"),
    ("sha256", "TEXT"),
    ("fetched_at", "TEXT"),
)


def _migrate(conn: sqlite3.Connection) -> None:
    """Additively bring an existing store up to the current schema (idempotent).

    Only ``ADD COLUMN`` migrations, so it never rewrites or drops data: a DB
    harvested under the A1 schema keeps its ``works``/``pages`` rows and simply
    gains the A2 image-cache columns (all nullable, defaulting to NULL).
    """
    existing = {row[1] for row in conn.execute("PRAGMA table_info(pages)")}
    for name, decl in _PAGES_ADDED_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE pages ADD COLUMN {name} {decl}")


def init_db(path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create the schema if absent, migrate it forward, and return a connection.

    Idempotent: the DDL is all ``IF NOT EXISTS`` and :func:`_migrate` only adds
    missing columns, so calling it on a fresh, an A1-era, or an already-current
    store all converge on the same schema without data loss.
    """
    conn = connect(path)
    conn.executescript(SCHEMA_SQL)
    _migrate(conn)
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
    """One canvas of a work. ``id`` is derived from ``work_id`` + ``seq``.

    Carries three groups of fields: identity (``work_id``/``seq``), image
    delivery (``image_service_url`` for IIIF deep-zoom; ``image_url``/``thumb_url``
    the delivery derivatives A2 caches; ``delivery`` the mode), and the A2 cache
    manifest (``local_path``/``n_bytes``/``sha256``/``fetched_at``).
    """

    work_id: str
    seq: int
    canvas_id: str | None = None
    image_service_url: str | None = None
    image_url: str | None = None
    thumb_url: str | None = None
    delivery: str | None = None
    label: str | None = None
    width: int | None = None
    height: int | None = None
    status: str = "pending"
    skip_reason: str | None = None
    local_path: str | None = None
    n_bytes: int | None = None
    sha256: str | None = None
    fetched_at: str | None = None

    @property
    def id(self) -> str:
        """Canonical page id."""
        return page_id(self.work_id, self.seq)

    @property
    def is_cached(self) -> bool:
        """True once the delivery derivative is downloaded and checksummed."""
        return self.sha256 is not None


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
        image_url=row["image_url"],
        thumb_url=row["thumb_url"],
        delivery=row["delivery"],
        label=row["label"],
        width=row["width"],
        height=row["height"],
        status=row["status"],
        skip_reason=row["skip_reason"],
        local_path=row["local_path"],
        n_bytes=row["n_bytes"],
        sha256=row["sha256"],
        fetched_at=row["fetched_at"],
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
    """Insert a page, or update its *derivation* fields if it already exists.

    This is the write path for page *derivation* (from manifests or the METS
    ``fileSec``). On conflict it refreshes the image-delivery fields but, by
    design, **preserves** the A2 cache manifest (``local_path``/``n_bytes``/
    ``sha256``/``fetched_at``) and the pipeline ``status``/``skip_reason``, and
    uses ``COALESCE`` so a re-derivation that lacks a value never nulls out one
    already stored. Re-running ``harvest``/``images pages`` is therefore safe
    against a populated store — a downloaded image stays recorded.
    """
    conn.execute(
        """
        INSERT INTO pages
            (page_id, work_id, seq, canvas_id, image_service_url, image_url,
             thumb_url, delivery, label, width, height, status, skip_reason,
             local_path, n_bytes, sha256, fetched_at)
        VALUES (:page_id, :work_id, :seq, :canvas_id, :image_service_url, :image_url,
                :thumb_url, :delivery, :label, :width, :height, :status, :skip_reason,
                :local_path, :n_bytes, :sha256, :fetched_at)
        ON CONFLICT(page_id) DO UPDATE SET
            canvas_id         = COALESCE(excluded.canvas_id, pages.canvas_id),
            image_service_url = COALESCE(excluded.image_service_url, pages.image_service_url),
            image_url         = COALESCE(excluded.image_url, pages.image_url),
            thumb_url         = COALESCE(excluded.thumb_url, pages.thumb_url),
            delivery          = COALESCE(excluded.delivery, pages.delivery),
            label             = COALESCE(excluded.label, pages.label),
            width             = COALESCE(excluded.width, pages.width),
            height            = COALESCE(excluded.height, pages.height)
        """,
        {
            "page_id": page.id,
            "work_id": page.work_id,
            "seq": page.seq,
            "canvas_id": page.canvas_id,
            "image_service_url": page.image_service_url,
            "image_url": page.image_url,
            "thumb_url": page.thumb_url,
            "delivery": page.delivery,
            "label": page.label,
            "width": page.width,
            "height": page.height,
            "status": page.status,
            "skip_reason": page.skip_reason,
            "local_path": page.local_path,
            "n_bytes": page.n_bytes,
            "sha256": page.sha256,
            "fetched_at": page.fetched_at,
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


# --------------------------------------------------------------------------- #
# Image cache manifest (A2)
# --------------------------------------------------------------------------- #


def iter_fetch_pages(
    conn: sqlite3.Connection,
    *,
    set_name: str | None = None,
    work_ids: Sequence[str] | None = None,
    only_unfetched: bool = True,
) -> Iterator[Page]:
    """Iterate pages that have a delivery URL, for the image fetcher.

    Filters to a primary set (joins ``works``) and/or a list of works, and — by
    default — to pages **not yet cached** (``sha256 IS NULL``), the resumable
    work list. Pass ``only_unfetched=False`` to walk every target (e.g. for
    ``images verify``). Ordered by ``(work_id, seq)`` so a slice reads as
    contiguous folios.
    """
    sql = ["SELECT p.* FROM pages p"]
    params: list[object] = []
    where = ["p.image_url IS NOT NULL"]
    if set_name is not None:
        sql.append("JOIN works w ON w.gwlb_object_id = p.work_id")
        where.append("w.set_name = ?")
        params.append(set_name)
    if work_ids:
        placeholders = ",".join("?" * len(work_ids))
        where.append(f"p.work_id IN ({placeholders})")
        params.extend(work_ids)
    if only_unfetched:
        where.append("p.sha256 IS NULL")
    sql.append("WHERE " + " AND ".join(where))
    sql.append("ORDER BY p.work_id, p.seq")
    for row in conn.execute(" ".join(sql), params):
        yield _page_from_row(row)


def mark_page_fetched(
    conn: sqlite3.Connection,
    page_id_: str,
    *,
    local_path: str,
    n_bytes: int,
    sha256: str,
    width: int | None = None,
    height: int | None = None,
    fetched_at: str | None = None,
) -> None:
    """Record a downloaded delivery derivative in the ``pages`` manifest.

    ``width``/``height`` are backfilled only when provided (static-JPEG works
    have no dimensions in the METS, so the fetcher reads them from the file);
    ``COALESCE`` keeps any dimension already known from an IIIF manifest.
    """
    conn.execute(
        """
        UPDATE pages
           SET local_path = ?, n_bytes = ?, sha256 = ?, fetched_at = ?,
               width  = COALESCE(?, width),
               height = COALESCE(?, height)
         WHERE page_id = ?
        """,
        (local_path, n_bytes, sha256, fetched_at or utcnow_iso(), width, height, page_id_),
    )


def clear_page_fetch(conn: sqlite3.Connection, page_id_: str) -> None:
    """Forget a cached image (``--redo`` / a failed integrity check)."""
    conn.execute(
        "UPDATE pages SET local_path=NULL, n_bytes=NULL, sha256=NULL, fetched_at=NULL "
        "WHERE page_id = ?",
        (page_id_,),
    )


def count_fetch_targets(conn: sqlite3.Connection, *, set_name: str | None = None) -> int:
    """Pages that have a delivery URL (the denominator for cache coverage)."""
    if set_name is None:
        return conn.execute("SELECT COUNT(*) FROM pages WHERE image_url IS NOT NULL").fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM pages p JOIN works w ON w.gwlb_object_id = p.work_id "
        "WHERE p.image_url IS NOT NULL AND w.set_name = ?",
        (set_name,),
    ).fetchone()[0]


def count_pages_fetched(conn: sqlite3.Connection, *, set_name: str | None = None) -> int:
    """Pages whose delivery derivative is cached (``sha256`` present)."""
    if set_name is None:
        return conn.execute("SELECT COUNT(*) FROM pages WHERE sha256 IS NOT NULL").fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM pages p JOIN works w ON w.gwlb_object_id = p.work_id "
        "WHERE p.sha256 IS NOT NULL AND w.set_name = ?",
        (set_name,),
    ).fetchone()[0]


def sum_page_bytes(conn: sqlite3.Connection) -> int:
    """Total bytes of cached delivery derivatives."""
    row = conn.execute(
        "SELECT COALESCE(SUM(n_bytes), 0) FROM pages WHERE sha256 IS NOT NULL"
    ).fetchone()
    return int(row[0])


# --------------------------------------------------------------------------- #
# Run bookkeeping (SPECS §4.3 `runs`; provenance §4.5)
# --------------------------------------------------------------------------- #


def start_run(
    conn: sqlite3.Connection,
    stage: str,
    *,
    model: str | None = None,
    params: dict | None = None,
    git_sha: str | None = None,
) -> int:
    """Open a ``runs`` row for a pipeline invocation and return its id.

    Every stage that mutates the store records a run so counts, parameters, and
    the git SHA that produced them are auditable (the anti-contamination guarantee
    depends on this). Call :func:`finish_run` when the work completes.
    """
    cur = conn.execute(
        """
        INSERT INTO runs (stage, model, params, started_at, git_sha)
        VALUES (?, ?, ?, ?, ?)
        """,
        (stage, model, json.dumps(params) if params else None, utcnow_iso(), git_sha),
    )
    conn.commit()
    return int(cur.lastrowid)


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    n_input: int | None = None,
    n_ok: int | None = None,
    n_failed: int | None = None,
) -> None:
    """Stamp a ``runs`` row finished, with input/ok/failed counts."""
    conn.execute(
        """
        UPDATE runs
           SET finished_at = ?, n_input = ?, n_ok = ?, n_failed = ?
         WHERE run_id = ?
        """,
        (utcnow_iso(), n_input, n_ok, n_failed, run_id),
    )
    conn.commit()


# --------------------------------------------------------------------------- #
# Pipeline: page status, lines, and per-page segmentation stats (C1)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Line:
    """One segmented+recognised manuscript line (SPECS §4.3 ``lines``).

    Filled in two stages by the C1 pipeline: segmentation writes the geometry
    (``baseline``/``polygon``) with ``text``/``conf`` still ``None``; recognition
    fills ``text``/``conf`` and repoints ``run_id``/``model`` at the recognition
    run (the text's provenance, SPECS §4.5). The segmentation run is retained in
    ``source`` and in :class:`PageStats`.
    """

    page_id: str
    line_seq: int
    baseline: list | None = None
    polygon: list | None = None
    text: str | None = None
    conf: float | None = None
    model: str | None = None
    run_id: int | None = None
    status: str = "machine"
    lang: str | None = None
    source: dict | None = None

    @property
    def id(self) -> str:
        """Canonical line id (``{page_id}:{line_seq:03d}``)."""
        return line_id(self.page_id, self.line_seq)


def _line_from_row(row: sqlite3.Row) -> Line:
    return Line(
        page_id=row["page_id"],
        line_seq=row["line_seq"],
        baseline=json.loads(row["baseline"]) if row["baseline"] else None,
        polygon=json.loads(row["polygon"]) if row["polygon"] else None,
        text=row["text"],
        conf=row["conf"],
        model=row["model"],
        run_id=row["run_id"],
        status=row["status"],
        lang=row["lang"],
        source=json.loads(row["source"]) if row["source"] else None,
    )


def iter_pages_by_status(
    conn: sqlite3.Connection,
    status: str,
    *,
    set_name: str | None = None,
    work_ids: Sequence[str] | None = None,
    require_cached: bool = False,
    limit: int | None = None,
    after: tuple[str, int] | None = None,
) -> Iterator[Page]:
    """Iterate pages in a pipeline ``status``, the resumable work list.

    ``require_cached`` restricts to pages whose delivery image is downloaded
    (``sha256`` present) — the segment/recognise stages need the local image.
    Ordered ``(work_id, seq)`` so a slice reads as contiguous folios.

    ``after`` is a keyset cursor: only pages strictly beyond ``(work_id, seq)``
    are returned. The pipeline stages page through the work list in small,
    *closed* batches (``limit`` + ``after``) instead of holding one cursor open
    for the whole run: a long-lived read snapshot on a writing connection makes
    every write fail instantly with "database is locked" the moment any *other*
    worker commits (WAL snapshot upgrade — the busy timeout cannot help), which
    is exactly how the first concurrent corpus run died.
    """
    sql = ["SELECT p.* FROM pages p"]
    params: list[object] = []
    where = ["p.status = ?"]
    params.append(status)
    if set_name is not None:
        sql.append("JOIN works w ON w.gwlb_object_id = p.work_id")
        where.append("w.set_name = ?")
        params.append(set_name)
    if work_ids:
        placeholders = ",".join("?" * len(work_ids))
        where.append(f"p.work_id IN ({placeholders})")
        params.extend(work_ids)
    if require_cached:
        where.append("p.sha256 IS NOT NULL")
    if after is not None:
        where.append("(p.work_id > ? OR (p.work_id = ? AND p.seq > ?))")
        params.extend([after[0], after[0], after[1]])
    sql.append("WHERE " + " AND ".join(where))
    sql.append("ORDER BY p.work_id, p.seq")
    if limit is not None:
        sql.append("LIMIT ?")
        params.append(limit)
    for row in conn.execute(" ".join(sql), params):
        yield _page_from_row(row)


def count_pages_by_status(
    conn: sqlite3.Connection, status: str, *, set_name: str | None = None
) -> int:
    """Number of pages in a given pipeline ``status``."""
    if set_name is None:
        return conn.execute("SELECT COUNT(*) FROM pages WHERE status = ?", (status,)).fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM pages p JOIN works w ON w.gwlb_object_id = p.work_id "
        "WHERE p.status = ? AND w.set_name = ?",
        (status, set_name),
    ).fetchone()[0]


def status_histogram(conn: sqlite3.Connection) -> dict[str, int]:
    """``status -> page count`` across the corpus (pipeline coverage view)."""
    return {
        row[0]: row[1] for row in conn.execute("SELECT status, COUNT(*) FROM pages GROUP BY status")
    }


def set_page_status(
    conn: sqlite3.Connection, page_id_: str, status: str, *, skip_reason: str | None = None
) -> None:
    """Advance (or fail) a page's pipeline status. ``skip_reason`` for skips."""
    conn.execute(
        "UPDATE pages SET status = ?, skip_reason = ? WHERE page_id = ?",
        (status, skip_reason, page_id_),
    )


def insert_line(conn: sqlite3.Connection, line: Line) -> None:
    """Insert (or replace on the same run) a line row, geometry + optional text.

    Keyed by ``(page_id, line_seq, run_id)``; re-inserting the same physical line
    under the same run refreshes it. Segmentation writes geometry-only rows;
    :func:`set_line_recognition` later fills the text.
    """
    conn.execute(
        """
        INSERT INTO lines
            (line_id, page_id, line_seq, baseline, polygon, text, conf, model,
             run_id, status, lang, source)
        VALUES (:line_id, :page_id, :line_seq, :baseline, :polygon, :text, :conf,
                :model, :run_id, :status, :lang, :source)
        ON CONFLICT(page_id, line_seq, run_id) DO UPDATE SET
            baseline = excluded.baseline,
            polygon  = excluded.polygon,
            text     = excluded.text,
            conf     = excluded.conf,
            model    = excluded.model,
            status   = excluded.status,
            lang     = excluded.lang,
            source   = excluded.source
        """,
        {
            "line_id": line.id,
            "page_id": line.page_id,
            "line_seq": line.line_seq,
            "baseline": json.dumps(line.baseline) if line.baseline is not None else None,
            "polygon": json.dumps(line.polygon) if line.polygon is not None else None,
            "text": line.text,
            "conf": line.conf,
            "model": line.model,
            "run_id": line.run_id,
            "status": line.status,
            "lang": line.lang,
            "source": json.dumps(line.source, ensure_ascii=False) if line.source else None,
        },
    )


def set_line_recognition(
    conn: sqlite3.Connection,
    page_id_: str,
    line_seq: int,
    *,
    text: str,
    conf: float | None,
    model: str,
    run_id: int,
    lang: str | None = None,
    source: dict | None = None,
) -> None:
    """Fill a segmented line's transcription, repointing provenance at the run.

    ``run_id``/``model`` become the recognition run's (the text's provenance);
    the whole page's lines migrate together, so the ``(page_id, line_seq,
    run_id)`` key stays unique.
    """
    conn.execute(
        """
        UPDATE lines
           SET text = ?, conf = ?, model = ?, run_id = ?,
               lang = COALESCE(?, lang),
               source = COALESCE(?, source)
         WHERE page_id = ? AND line_seq = ?
        """,
        (
            text,
            conf,
            model,
            run_id,
            lang,
            json.dumps(source, ensure_ascii=False) if source else None,
            page_id_,
            line_seq,
        ),
    )


def delete_lines_for_page(conn: sqlite3.Connection, page_id_: str) -> None:
    """Remove a page's line rows (``--redo`` re-segmentation)."""
    conn.execute("DELETE FROM lines WHERE page_id = ?", (page_id_,))


def iter_lines_for_page(conn: sqlite3.Connection, page_id_: str) -> list[Line]:
    """A page's lines in reading order (``line_seq``)."""
    cur = conn.execute("SELECT * FROM lines WHERE page_id = ? ORDER BY line_seq", (page_id_,))
    return [_line_from_row(row) for row in cur]


def count_lines(conn: sqlite3.Connection, *, recognized: bool | None = None) -> int:
    """Total line rows; ``recognized=True`` counts only those with text."""
    if recognized is None:
        return conn.execute("SELECT COUNT(*) FROM lines").fetchone()[0]
    op = "IS NOT NULL" if recognized else "IS NULL"
    return conn.execute(f"SELECT COUNT(*) FROM lines WHERE text {op}").fetchone()[0]


@dataclass(slots=True)
class PageStats:
    """Per-page segmentation statistics (C1; feeds the C2/C4 stratum heuristic)."""

    page_id: str
    n_lines: int
    run_id: int | None = None
    n_regions: int | None = None
    region_coverage: float | None = None
    mean_line_height: float | None = None
    median_line_height: float | None = None
    line_height_cv: float | None = None
    n_overlaps: int | None = None
    n_short_lines: int | None = None
    stratum_heuristic: str | None = None
    metrics: dict = field(default_factory=dict)


def _page_stats_from_row(row: sqlite3.Row) -> PageStats:
    return PageStats(
        page_id=row["page_id"],
        n_lines=row["n_lines"],
        run_id=row["run_id"],
        n_regions=row["n_regions"],
        region_coverage=row["region_coverage"],
        mean_line_height=row["mean_line_height"],
        median_line_height=row["median_line_height"],
        line_height_cv=row["line_height_cv"],
        n_overlaps=row["n_overlaps"],
        n_short_lines=row["n_short_lines"],
        stratum_heuristic=row["stratum_heuristic"],
        metrics=json.loads(row["metrics"]) if row["metrics"] else {},
    )


def upsert_page_stats(conn: sqlite3.Connection, ps: PageStats) -> None:
    """Insert/replace a page's segmentation stats (idempotent re-segmentation)."""
    conn.execute(
        """
        INSERT INTO page_stats
            (page_id, run_id, n_lines, n_regions, region_coverage, mean_line_height,
             median_line_height, line_height_cv, n_overlaps, n_short_lines,
             stratum_heuristic, metrics)
        VALUES (:page_id, :run_id, :n_lines, :n_regions, :region_coverage,
                :mean_line_height, :median_line_height, :line_height_cv, :n_overlaps,
                :n_short_lines, :stratum_heuristic, :metrics)
        ON CONFLICT(page_id) DO UPDATE SET
            run_id             = excluded.run_id,
            n_lines            = excluded.n_lines,
            n_regions          = excluded.n_regions,
            region_coverage    = excluded.region_coverage,
            mean_line_height   = excluded.mean_line_height,
            median_line_height = excluded.median_line_height,
            line_height_cv     = excluded.line_height_cv,
            n_overlaps         = excluded.n_overlaps,
            n_short_lines      = excluded.n_short_lines,
            stratum_heuristic  = COALESCE(excluded.stratum_heuristic, page_stats.stratum_heuristic),
            metrics            = excluded.metrics
        """,
        {
            "page_id": ps.page_id,
            "run_id": ps.run_id,
            "n_lines": ps.n_lines,
            "n_regions": ps.n_regions,
            "region_coverage": ps.region_coverage,
            "mean_line_height": ps.mean_line_height,
            "median_line_height": ps.median_line_height,
            "line_height_cv": ps.line_height_cv,
            "n_overlaps": ps.n_overlaps,
            "n_short_lines": ps.n_short_lines,
            "stratum_heuristic": ps.stratum_heuristic,
            "metrics": json.dumps(ps.metrics, ensure_ascii=False) if ps.metrics else None,
        },
    )


def get_page_stats(conn: sqlite3.Connection, page_id_: str) -> PageStats | None:
    """Fetch a page's segmentation stats, or ``None``."""
    row = conn.execute("SELECT * FROM page_stats WHERE page_id = ?", (page_id_,)).fetchone()
    return _page_stats_from_row(row) if row is not None else None


def iter_page_stats(conn: sqlite3.Connection) -> Iterator[PageStats]:
    """Iterate all per-page segmentation stats, ordered by page id."""
    for row in conn.execute("SELECT * FROM page_stats ORDER BY page_id"):
        yield _page_stats_from_row(row)


def set_page_stratum(conn: sqlite3.Connection, page_id_: str, stratum: str) -> None:
    """Record a page's heuristic stratum label (C2/C4)."""
    conn.execute(
        "UPDATE page_stats SET stratum_heuristic = ? WHERE page_id = ?", (stratum, page_id_)
    )


# --------------------------------------------------------------------------- #
# Katalog records + crosswalk (A3)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class KatalogRecord:
    """One BBAW Ritter-Katalog record (SPECS §4.3 ``katalog_records``).

    ``metadata`` holds the full parsed row (title, incipit, dating, correspondent,
    place, extent, and the GWLB object ids extracted from its outbound links —
    ``metadata["gwlb_ids"]`` — which the crosswalk joins on). ``shelfmark_refs``
    is the record's signature string(s); ``aa_refs`` a list of
    ``{series, volume, piece, ...}`` Akademie-Ausgabe references.
    """

    record_id: str
    metadata: dict = field(default_factory=dict)
    shelfmark_refs: list[str] = field(default_factory=list)
    aa_refs: list[dict] = field(default_factory=list)
    transcription_snippet: str | None = None

    @property
    def gwlb_ids(self) -> list[str]:
        """GWLB object ids this record links to (the primary crosswalk key)."""
        return list(self.metadata.get("gwlb_ids") or [])


@dataclass(slots=True)
class CrosswalkMatch:
    """A katalog-record ↔ work link with its method and confidence (§4.3)."""

    katalog_record_id: str
    work_id: str
    match_method: str  # 'gwlb_link' | 'shelfmark' | 'manual' | ...
    match_conf: float
    page_range: str | None = None


def _katalog_from_row(row: sqlite3.Row) -> KatalogRecord:
    return KatalogRecord(
        record_id=row["record_id"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        shelfmark_refs=json.loads(row["shelfmark_refs"]) if row["shelfmark_refs"] else [],
        aa_refs=json.loads(row["aa_refs"]) if row["aa_refs"] else [],
        transcription_snippet=row["transcription_snippet"],
    )


def upsert_katalog_record(conn: sqlite3.Connection, rec: KatalogRecord) -> None:
    """Insert/replace a katalog record (idempotent re-scrape by ``record_id``)."""
    conn.execute(
        """
        INSERT INTO katalog_records
            (record_id, metadata, shelfmark_refs, aa_refs, transcription_snippet)
        VALUES (:record_id, :metadata, :shelfmark_refs, :aa_refs, :transcription_snippet)
        ON CONFLICT(record_id) DO UPDATE SET
            metadata              = excluded.metadata,
            shelfmark_refs        = excluded.shelfmark_refs,
            aa_refs               = excluded.aa_refs,
            transcription_snippet = excluded.transcription_snippet
        """,
        {
            "record_id": rec.record_id,
            "metadata": json.dumps(rec.metadata, ensure_ascii=False) if rec.metadata else None,
            "shelfmark_refs": json.dumps(rec.shelfmark_refs, ensure_ascii=False)
            if rec.shelfmark_refs
            else None,
            "aa_refs": json.dumps(rec.aa_refs, ensure_ascii=False) if rec.aa_refs else None,
            "transcription_snippet": rec.transcription_snippet,
        },
    )


def get_katalog_record(conn: sqlite3.Connection, record_id: str) -> KatalogRecord | None:
    """Fetch a katalog record by id, or ``None``."""
    row = conn.execute("SELECT * FROM katalog_records WHERE record_id = ?", (record_id,)).fetchone()
    return _katalog_from_row(row) if row is not None else None


def iter_katalog_records(conn: sqlite3.Connection) -> Iterator[KatalogRecord]:
    """Iterate all katalog records, ordered by id."""
    for row in conn.execute("SELECT * FROM katalog_records ORDER BY record_id"):
        yield _katalog_from_row(row)


def count_katalog_records(conn: sqlite3.Connection) -> int:
    """Total number of katalog records."""
    return conn.execute("SELECT COUNT(*) FROM katalog_records").fetchone()[0]


def upsert_crosswalk(conn: sqlite3.Connection, match: CrosswalkMatch) -> None:
    """Record a crosswalk link, keeping the **higher-confidence** method on conflict.

    A record and a work can be linked by more than one method (an explicit GWLB
    link *and* a matching shelfmark); the pair is unique, so we retain the most
    trustworthy one (``gwlb_link`` at conf 1.0 always wins over a shelfmark guess).
    """
    conn.execute(
        """
        INSERT INTO crosswalk
            (katalog_record_id, work_id, page_range, match_method, match_conf)
        VALUES (:rid, :wid, :page_range, :method, :conf)
        ON CONFLICT(katalog_record_id, work_id) DO UPDATE SET
            match_method = excluded.match_method,
            match_conf   = excluded.match_conf,
            page_range   = excluded.page_range
        WHERE excluded.match_conf > crosswalk.match_conf
        """,
        {
            "rid": match.katalog_record_id,
            "wid": match.work_id,
            "page_range": match.page_range,
            "method": match.match_method,
            "conf": match.match_conf,
        },
    )


def iter_crosswalk(conn: sqlite3.Connection) -> Iterator[CrosswalkMatch]:
    """Iterate all crosswalk links."""
    for row in conn.execute(
        "SELECT katalog_record_id, work_id, page_range, match_method, match_conf "
        "FROM crosswalk ORDER BY work_id, katalog_record_id"
    ):
        yield CrosswalkMatch(
            katalog_record_id=row["katalog_record_id"],
            work_id=row["work_id"],
            match_method=row["match_method"],
            match_conf=row["match_conf"],
            page_range=row["page_range"],
        )


def count_crosswalk(conn: sqlite3.Connection) -> int:
    """Total number of crosswalk links."""
    return conn.execute("SELECT COUNT(*) FROM crosswalk").fetchone()[0]


def matched_work_ids(conn: sqlite3.Connection) -> set[str]:
    """The set of work ids that have at least one crosswalk link."""
    return {row[0] for row in conn.execute("SELECT DISTINCT work_id FROM crosswalk")}


def best_crosswalk_by_record(conn: sqlite3.Connection) -> dict[str, CrosswalkMatch]:
    """Map each katalog record to its highest-confidence work link (C2 factory).

    A record can link to several works and by several methods; the GT factory
    wants the single most trustworthy work per piece, so this keeps the max-conf
    (ties broken by ``gwlb_link`` over ``shelfmark``) link per record.
    """
    best: dict[str, CrosswalkMatch] = {}
    for m in iter_crosswalk(conn):
        cur = best.get(m.katalog_record_id)
        if cur is None or m.match_conf > cur.match_conf:
            best[m.katalog_record_id] = m
    return best
