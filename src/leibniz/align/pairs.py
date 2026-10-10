"""Mint ``gt_lines`` from an alignment (Phase B2).

The point of retro-alignment is training data: each line the aligner accepts
becomes a ground-truth ``(line image, edition text)`` pair. This module turns an
:class:`~leibniz.align.align.AlignmentResult` into :class:`GtPair`s and writes
them to the ``gt_lines`` table (SPECS §4.3), carrying the provenance the project
never ships without (SPECS §4.5):

* ``source`` — where the text came from (``"AA VI,4 N.109 (Zenodo/…)"``), so the
  §70 provenance is auditable;
* ``align_conf`` — the per-line alignment confidence, so downstream consumers can
  re-threshold;
* ``stratum`` — the manuscript stratum (fair_copy / …), first-class per SPECS §6;
* ``license_bucket`` — **``open``** only for §70-expired AA reading text;
  Transkriptionspool / NC-derived text goes to **``nc``** and never enters a
  CC BY export (SPECS §7.3). This gate is enforced here, at the moment of minting.

Only lines the aligner accepted (``aligned``) are minted — below-threshold pairs
are discarded, never shipped (SPECS §6: "a smaller clean corpus beats a larger
polluted one").

**Ownership (2026-10).** A minted row belongs to the catalogue record it was
minted from (``gt_lines.record_id``, also legible in ``source`` as ``katalog
<id>``). Re-minting a record replaces that record's rows and no others: two
pieces that share a folio no longer erase each other's lines, and a resumed
run skips a record only when the record itself is minted. Where two records
both mint one line, the higher alignment confidence keeps it (ties go to the
lower record id), whichever is minted first — so a full re-mint gives the same
store on any number of shards.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from leibniz.align.align import AlignmentResult
from leibniz.db import GT_STRATA, LICENSE_BUCKETS


@dataclass(slots=True)
class GtPair:
    """One minted ground-truth pair, ready for ``gt_lines`` (SPECS §4.3)."""

    line_image_ref: str  # canonical line id or image path + region
    text: str  # the edition reading text projected onto this line
    source: str  # provenance string (AA volume/piece, license note)
    stratum: str  # GT_STRATA
    align_conf: float
    license_bucket: str  # 'open' | 'nc'
    record_id: str | None = None  # the catalogue record that owns the row

    def __post_init__(self) -> None:
        if self.license_bucket not in LICENSE_BUCKETS:
            raise ValueError(f"license_bucket must be in {LICENSE_BUCKETS}")
        if self.stratum not in GT_STRATA:
            raise ValueError(f"stratum must be in {GT_STRATA}")


def collapse_whitespace(text: str) -> str:
    """One line of text: runs of whitespace (the print's line breaks among them)
    become one space, and the ends are trimmed."""
    return " ".join(text.split())


def result_to_pairs(
    result: AlignmentResult,
    *,
    source: str,
    stratum: str = "unknown",
    license_bucket: str = "open",
    strip: bool = True,
    record_id: str | None = None,
) -> list[GtPair]:
    """Turn the *accepted* lines of an alignment into :class:`GtPair`s.

    Only ``aligned`` lines (confidence ≥ the run's threshold, non-empty edition
    text) are minted; everything else is dropped. ``strip`` makes the emitted
    edition text one line: the projected slice can carry a leading/trailing
    space from the folded-boundary projection, and the print's own line breaks
    where a manuscript line spans two lines of the edition (65 of the 200
    audited lines carried a raw newline before 2026-10).
    """
    pairs: list[GtPair] = []
    for ln in result.lines:
        if not ln.aligned:
            continue
        text = collapse_whitespace(ln.edition_text) if strip else ln.edition_text
        if not text:
            continue
        pairs.append(
            GtPair(
                line_image_ref=ln.ref,
                text=text,
                source=source,
                stratum=stratum,
                align_conf=round(ln.align_conf, 4),
                license_bucket=license_bucket,
                record_id=record_id,
            )
        )
    return pairs


# The record a factory row was minted from: "… (…; katalog 41800)".
_RECORD_RE = re.compile(r"katalog\s+([^)\s]+)")


def record_id_from_source(source: str | None) -> str | None:
    """The catalogue record id a factory ``source`` string names, or ``None``."""
    m = _RECORD_RE.search(source or "")
    return m.group(1) if m else None


def has_record_column(conn: sqlite3.Connection) -> bool:
    """Whether this store's ``gt_lines`` carries the ``record_id`` column."""
    return any(row[1] == "record_id" for row in conn.execute("PRAGMA table_info(gt_lines)"))


def ensure_gt_ownership(conn: sqlite3.Connection) -> int:
    """Bring ``gt_lines`` up to record ownership, idempotently; return rows backfilled.

    Adds the ``record_id`` column where an older store lacks it, the indexes
    that make per-record replacement cheap (``line_image_ref``, ``record_id``),
    and fills ``record_id`` from ``source`` for rows minted before the column
    existed. A write path's job only (the factory calls it under its write
    lock): read-only consumers such as the index build never touch the schema.
    The caller commits.
    """
    if not has_record_column(conn):
        conn.execute("ALTER TABLE gt_lines ADD COLUMN record_id TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_gt_ref ON gt_lines (line_image_ref)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_gt_record ON gt_lines (record_id)")
    rows = conn.execute("SELECT id, source FROM gt_lines WHERE record_id IS NULL").fetchall()
    updates = [(rid, row[0]) for row in rows if (rid := record_id_from_source(row[1])) is not None]
    conn.executemany("UPDATE gt_lines SET record_id = ? WHERE id = ?", updates)
    return len(updates)


def insert_gt_pairs(conn: sqlite3.Connection, pairs: Iterable[GtPair]) -> int:
    """Insert minted pairs into ``gt_lines``; return the count written.

    Enforces the license gate at write time via the ``GtPair`` invariant. The
    caller commits (so a whole piece's pairs land atomically). A pair's
    ``record_id`` is written where the store has the column (any store a write
    path has opened since 2026-10; see :func:`ensure_gt_ownership`).
    """
    with_record = has_record_column(conn)
    n = 0
    for p in pairs:
        if with_record:
            conn.execute(
                """
                INSERT INTO gt_lines
                    (line_image_ref, text, source, stratum, align_conf, license_bucket, record_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p.line_image_ref,
                    p.text,
                    p.source,
                    p.stratum,
                    p.align_conf,
                    p.license_bucket,
                    p.record_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO gt_lines
                    (line_image_ref, text, source, stratum, align_conf, license_bucket)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (p.line_image_ref, p.text, p.source, p.stratum, p.align_conf, p.license_bucket),
            )
        n += 1
    return n


@dataclass(slots=True)
class RecordWrite:
    """What replacing one record's rows did."""

    removed: int = 0  # the record's own earlier rows, deleted
    written: int = 0  # pairs inserted
    won: int = 0  # lines taken over from another record (higher confidence)
    lost: int = 0  # pairs not written: another record holds the line more confidently


def _holds_against(rival_conf: float | None, rival_record: str | None, pair: GtPair) -> bool:
    """Whether a row already on the line keeps it against ``pair``: the higher
    alignment confidence wins, then the lower record id (a total order, so the
    outcome does not depend on which record is minted first)."""
    a, b = rival_conf or 0.0, pair.align_conf
    if a != b:
        return a > b
    return str(rival_record or "") < str(pair.record_id or "")


def replace_record_pairs(
    conn: sqlite3.Connection, record_id: str, pairs: Sequence[GtPair]
) -> RecordWrite:
    """Replace one record's minted rows with ``pairs``, leaving every other
    record's rows alone except a line it loses on confidence. The caller holds
    the write lock and commits; :func:`ensure_gt_ownership` has run."""
    out = RecordWrite()
    out.removed = conn.execute("DELETE FROM gt_lines WHERE record_id = ?", (record_id,)).rowcount
    keep: list[GtPair] = []
    for pair in pairs:
        rivals = conn.execute(
            "SELECT id, record_id, align_conf FROM gt_lines WHERE line_image_ref = ?",
            (pair.line_image_ref,),
        ).fetchall()
        if any(_holds_against(r[2], r[1], pair) for r in rivals):
            out.lost += 1
            continue
        if rivals:
            conn.executemany("DELETE FROM gt_lines WHERE id = ?", [(r[0],) for r in rivals])
            out.won += 1
        keep.append(pair)
    out.written = insert_gt_pairs(conn, keep)
    return out


def has_gt_for_record(conn: sqlite3.Connection, record_id: str) -> bool:
    """True if the record already owns minted rows (the factory's resume check)."""
    row = conn.execute("SELECT 1 FROM gt_lines WHERE record_id = ? LIMIT 1", (record_id,))
    return row.fetchone() is not None


def delete_minted(conn: sqlite3.Connection) -> dict[str, int]:
    """Delete every row a catalogue record owns — the factory's output — and
    return the counts removed by licence bucket; rows without an owner
    (ground truth imported from elsewhere) stay. For the one full re-mint: a
    re-mint replaces each record it mints, so a record the new rules no longer
    mint would keep its old rows. The caller holds the write lock and commits;
    :func:`ensure_gt_ownership` has run."""
    counts = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT license_bucket, COUNT(*) FROM gt_lines WHERE record_id IS NOT NULL "
            "GROUP BY license_bucket"
        )
    }
    conn.execute("DELETE FROM gt_lines WHERE record_id IS NOT NULL")
    return counts


def count_open_bucket(pairs: Sequence[GtPair]) -> int:
    """How many pairs are CC-BY-shippable (``open`` bucket) — a report figure."""
    return sum(1 for p in pairs if p.license_bucket == "open")


def delete_gt_for_refs(conn: sqlite3.Connection, refs: Iterable[str]) -> int:
    """Remove any ``gt_lines`` rows for these line image refs; return the count.

    The C2 factory's original replacement rule, kept for tools that clear a set
    of lines outright. The factory itself now replaces by record
    (:func:`replace_record_pairs`): clearing every line on a piece's pages also
    cleared a neighbouring piece's lines on a shared folio. The caller commits.
    """
    refs = list(refs)
    n = 0
    for ref in refs:
        cur = conn.execute("DELETE FROM gt_lines WHERE line_image_ref = ?", (ref,))
        n += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    return n


def has_gt_for_refs(conn: sqlite3.Connection, refs: Iterable[str]) -> bool:
    """True if any ``gt_lines`` row exists for these line image refs (resume check)."""
    refs = list(refs)
    for i in range(0, len(refs), 500):
        chunk = refs[i : i + 500]
        marks = ",".join("?" * len(chunk))
        row = conn.execute(
            f"SELECT 1 FROM gt_lines WHERE line_image_ref IN ({marks}) LIMIT 1", chunk
        ).fetchone()
        if row is not None:
            return True
    return False


def count_gt_lines(conn: sqlite3.Connection, *, license_bucket: str | None = None) -> int:
    """Total ``gt_lines`` rows, optionally within one license bucket."""
    if license_bucket is None:
        return conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM gt_lines WHERE license_bucket = ?", (license_bucket,)
    ).fetchone()[0]


__all__ = [
    "GtPair",
    "RecordWrite",
    "collapse_whitespace",
    "count_gt_lines",
    "count_open_bucket",
    "delete_gt_for_refs",
    "delete_minted",
    "ensure_gt_ownership",
    "has_gt_for_record",
    "has_gt_for_refs",
    "has_record_column",
    "insert_gt_pairs",
    "record_id_from_source",
    "replace_record_pairs",
    "result_to_pairs",
]
