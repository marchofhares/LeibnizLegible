"""A reader's readings into the store as one scoped recognition run (K4, Task 4).

K2's reading job (``leibniz align kurrent-read``) writes a JSONL beside the
store, one row per line (``line_id, text, conf, model, device, ms``). This
module writes such a file into ``lines`` as **one run** of stage ``recognize``
with a language scope (``de``), one row per line the reader read, beside the
v1 row and never over it: the recognise stage's :func:`leibniz.db.set_line_recognition`
updates rows in place and is not used here. Each new row copies the current
unscoped row's geometry (the segmentation v1 was read on, so the viewer's
overlay sits on the same pixels), carries the reading's text and confidence,
the reader's ``name@version`` as its model, status ``machine``, ``lang`` the
scope, and a ``source`` naming the readings file and the row it was cut from.
An empty reading writes no row: the line keeps showing the unscoped row
(the amendment of 26 October), so no page is half blank.

Idempotent and resumable by page: the run is found by its model and scope
while unfinished and reused; a page whose rows the run already holds is
skipped; a second import of the same file under the same model adds nothing.
The dry run (the default) counts everything and writes nothing.

The narrow crops are counted as the pages go by (the operator's decision of
28 October: every non-empty reading is written, a crop under
:data:`NARROW_PX` pixels included, and their number goes into the K4 report
and an open question for K3b's segmentation measurement), so the report
needs no second pass over the geometry.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align.kurrent_pilot import PilotLine, page_lines
from leibniz.align.kurrent_read import crop_width

COMMIT_EVERY = 200  # pages per transaction
NARROW_PX = 80  # a crop narrower than this is a segmentation fragment either way


@dataclass(slots=True)
class ReadingRow:
    line_id: str
    text: str
    conf: float | None


def iter_readings(path: Path | str) -> Iterator[ReadingRow]:
    """Stream the readings file: one row per line, the file never held whole."""
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                row = json.loads(raw)
                yield ReadingRow(str(row["line_id"]), str(row.get("text") or ""), row.get("conf"))


def readings_by_page(path: Path | str) -> dict[str, dict[int, ReadingRow]]:
    """Page id → line_seq → the reading (the last row for a line wins, as the
    job's own resumable file reads it)."""
    out: dict[str, dict[int, ReadingRow]] = {}
    for r in iter_readings(path):
        page_id, _, seq = r.line_id.rpartition(":")
        try:
            out.setdefault(page_id, {})[int(seq)] = r
        except ValueError:
            continue
    return out


@dataclass(slots=True)
class ImportStats:
    pages: int = 0  # pages in the list
    pages_done_before: int = 0  # pages the run already held (resume)
    pages_written: int = 0
    pages_without_readings: int = 0
    lines: int = 0  # unscoped lines on the pages (what the job read)
    rows_written: int = 0
    empty_readings: int = 0  # a line read as empty: no row
    lines_without_reading: int = 0  # a line the file has no row for
    orphan_readings: int = 0  # a reading whose line has no unscoped row
    narrow_lines: int = 0  # lines whose crop is under NARROW_PX wide
    narrow_rows: int = 0  # of the rows written, those on such crops
    model: str = ""
    scope: str = ""
    run_id: int | None = None
    dry_run: bool = True
    by_set: dict[str, dict[str, int]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "pages": self.pages,
            "pages_done_before": self.pages_done_before,
            "pages_written": self.pages_written,
            "pages_without_readings": self.pages_without_readings,
            "lines": self.lines,
            "rows_written": self.rows_written,
            "empty_readings": self.empty_readings,
            "lines_without_reading": self.lines_without_reading,
            "orphan_readings": self.orphan_readings,
            "narrow_px": NARROW_PX,
            "narrow_lines": self.narrow_lines,
            "narrow_rows": self.narrow_rows,
            "model": self.model,
            "scope": self.scope,
            "run_id": self.run_id,
            "dry_run": self.dry_run,
            "by_set": self.by_set,
        }


def find_open_run(conn: sqlite3.Connection, *, model: str, scope: str) -> int | None:
    """An unfinished run of stage ``recognize`` with this model and scope (a
    resume), else ``None``."""
    if not db.has_column(conn, "runs", "scope"):
        return None
    row = conn.execute(
        "SELECT run_id FROM runs WHERE stage = 'recognize' AND model = ? AND scope = ?"
        " AND finished_at IS NULL ORDER BY run_id DESC LIMIT 1",
        (model, scope),
    ).fetchone()
    return None if row is None else int(row[0])


def pages_done(conn: sqlite3.Connection, run_id: int) -> set[str]:
    """The pages the run already holds rows for."""
    return {
        r[0] for r in conn.execute("SELECT DISTINCT page_id FROM lines WHERE run_id = ?", (run_id,))
    }


def new_rows(
    lines: Sequence[PilotLine],
    readings: Mapping[int, ReadingRow],
    *,
    model: str,
    run_id: int | None,
    scope: str,
    source: Mapping,
) -> tuple[list[db.Line], int, int]:
    """The rows to insert for one page: one per line with a non-empty reading,
    the unscoped row's geometry copied. Returns the rows, the empty readings
    and the lines without a reading."""
    out: list[db.Line] = []
    empty = missing = 0
    for ln in lines:
        r = readings.get(ln.line_seq)
        if r is None:
            missing += 1
            continue
        if not r.text.strip():
            empty += 1
            continue
        out.append(
            db.Line(
                page_id=ln.page_id,
                line_seq=ln.line_seq,
                baseline=ln.baseline,
                polygon=ln.polygon,
                text=r.text,
                conf=r.conf,
                model=model,
                run_id=run_id,
                status="machine",
                lang=scope,
                source=dict(source),
            )
        )
    return out, empty, missing


def import_readings(
    conn: sqlite3.Connection,
    *,
    readings_path: Path | str,
    page_ids: Sequence[str],
    model: str,
    scope: str = "de",
    reader: str,
    write: bool = False,
    git_sha: str | None = None,
    note: str | None = None,
    progress: Callable[[ImportStats], None] | None = None,
    every: int = 2000,
) -> ImportStats:
    """Write the readings of ``page_ids`` into the store as one scoped run (or
    count what a write would do, the default). See the module docstring."""
    readings = readings_by_page(readings_path)
    stats = ImportStats(pages=len(page_ids), model=model, scope=scope, dry_run=not write)
    sets = {w.gwlb_object_id: w.set_name for w in db.iter_works(conn)}
    run_id: int | None = None
    done: set[str] = set()
    if write:
        run_id = find_open_run(conn, model=model, scope=scope)
        if run_id is None:
            run_id = db.start_run(
                conn,
                "recognize",
                model=model,
                params={
                    "reader": reader,
                    "readings": str(readings_path),
                    "pages": len(page_ids),
                    "scope": scope,
                    "k4": True,
                    "note": note,
                },
                git_sha=git_sha,
                scope=scope,
            )
        done = pages_done(conn, run_id)
        stats.run_id = run_id
    source = {"stage": "recognize", "reader": reader, "readings": Path(readings_path).name}
    if run_id is not None:
        source["run"] = run_id
    pending = 0
    for k, pid in enumerate(page_ids, start=1):
        set_name = sets.get(pid.rpartition(":")[0], "")
        tally = stats.by_set.setdefault(set_name, Counter())
        tally["pages"] += 1
        if pid in done:
            stats.pages_done_before += 1
            tally["pages_done_before"] += 1
            continue
        lines = page_lines(conn, pid)
        stats.lines += len(lines)
        tally["lines"] += len(lines)
        page_readings = readings.get(pid)
        if not page_readings:
            stats.pages_without_readings += 1
            tally["pages_without_readings"] += 1
            stats.lines_without_reading += len(lines)
            continue
        rows, empty, missing = new_rows(
            lines, page_readings, model=model, run_id=run_id, scope=scope, source=source
        )
        stats.empty_readings += empty
        stats.lines_without_reading += missing
        seqs = {ln.line_seq for ln in lines}
        stats.orphan_readings += sum(1 for seq in page_readings if seq not in seqs)
        written = {row.line_seq for row in rows}
        for ln in lines:
            w = crop_width(ln.polygon, ln.baseline)
            if w is not None and w < NARROW_PX:
                stats.narrow_lines += 1
                tally["narrow_lines"] += 1
                if ln.line_seq in written:
                    stats.narrow_rows += 1
                    tally["narrow_rows"] += 1
        if write and rows:
            for row in rows:
                db.insert_line(conn, row)
            pending += 1
            if pending >= COMMIT_EVERY:
                conn.commit()
                pending = 0
        if rows:
            stats.rows_written += len(rows)
            stats.pages_written += 1
            tally["rows"] += len(rows)
            tally["pages_written"] += 1
        if progress is not None and (k % every == 0 or k == len(page_ids)):
            progress(stats)
    if write:
        conn.commit()
        assert run_id is not None
        # n_input: the lines this invocation considered; a resumed run's earlier
        # pages are in ``pages_done_before`` and in the rows the run holds
        db.finish_run(conn, run_id, n_input=stats.lines, n_ok=stats.rows_written, n_failed=0)
        conn.execute(
            "UPDATE runs SET params = json_patch(COALESCE(params, '{}'), ?) WHERE run_id = ?",
            (json.dumps({"import": stats.as_dict()}), run_id),
        )
        conn.commit()
    stats.by_set = {k: dict(v) for k, v in stats.by_set.items()}
    return stats


def rows_under_run(conn: sqlite3.Connection, run_id: int) -> tuple[int, int]:
    """``(pages, rows)`` the run holds in ``lines``."""
    r = conn.execute(
        "SELECT COUNT(DISTINCT page_id), COUNT(*) FROM lines WHERE run_id = ?", (run_id,)
    ).fetchone()
    return int(r[0]), int(r[1])


def store_size(path: Path | str) -> dict[str, int]:
    """The store's file sizes in bytes: the database, its WAL if present."""
    p = Path(path)
    out = {"db": p.stat().st_size if p.exists() else 0}
    wal = p.with_name(p.name + "-wal")
    out["wal"] = wal.stat().st_size if wal.exists() else 0
    return out


def summary_lines(stats: ImportStats) -> list[str]:
    what = "would write" if stats.dry_run else "wrote"
    L = [
        f"pages {stats.pages:,} (done before {stats.pages_done_before:,}, without readings "
        f"{stats.pages_without_readings:,}); lines {stats.lines:,}",
        f"{what} {stats.rows_written:,} rows on {stats.pages_written:,} pages; empty readings "
        f"{stats.empty_readings:,}, lines without a reading {stats.lines_without_reading:,}, "
        f"orphan readings {stats.orphan_readings:,}",
        f"crops under {NARROW_PX} px: {stats.narrow_lines:,} lines, {stats.narrow_rows:,} of "
        f"them with a row",
    ]
    if stats.run_id is not None:
        L.append(f"run {stats.run_id} (stage recognize, model {stats.model}, scope {stats.scope})")
    for name, t in sorted(stats.by_set.items()):
        L.append(
            f"  {name or '(no set)'}: pages {t.get('pages', 0):,}, lines {t.get('lines', 0):,}, "
            f"rows {t.get('rows', 0):,}, narrow {t.get('narrow_lines', 0):,}"
        )
    return L


__all__ = [
    "COMMIT_EVERY",
    "NARROW_PX",
    "ImportStats",
    "ReadingRow",
    "find_open_run",
    "import_readings",
    "iter_readings",
    "new_rows",
    "pages_done",
    "readings_by_page",
    "rows_under_run",
    "store_size",
    "summary_lines",
]
