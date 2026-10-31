"""The judgment pack: the game's verdicts back into the store (Phase G1).

Calculemus retires a fragment when its players converge on one of the two
readings (``converged``) or reject both (``both_rejected``); its judgment pack
carries one row per retired fragment (Calculemus SPECS §6.6, mirrored in
``judgment_pack.schema.json``). ``leibniz pack judgments`` checks the pack
whole against the contract first — a pack that fails is refused and nothing
is read from it — and then:

* imports each ``converged`` row as a **new** ``lines`` row: status
  ``corrected``, the winning text, the posterior as its confidence, the
  machine row's geometry and language, under a new ``runs`` row (stage
  ``crowd``, model ``crowd_ab_v1@<the game's git sha>``), with the judgment
  row verbatim as its ``source``. A row is never updated or deleted: the
  machine rows keep their runs, and the ``UNIQUE(page_id, line_seq, run_id)``
  key keeps the crowd's row beside them. A judgment the store already holds
  (the same line, the same ``decided_at``) is not imported again, so the
  import is idempotent; given the fragment pack the judgments answer
  (``--fragments``), a winner that is not one of the line's two candidates,
  word for word, is refused.
* renders the ``both_rejected`` rows into ``reports/scriptorium-queue.md`` —
  the line, its page, the two readings, the posterior, the date: the queue a
  person transcribes from the image later. One section per judgment pack;
  reading a pack again replaces its section, another pack adds its own.

A dry run unless ``--write``: the store is opened read-only and nothing is
written to it; ``--write`` imports in one transaction. The queue is rendered
either way (a report, not the store). What the site shows of a line is its
latest run (``search.documents.latest_lines``), so an imported judgment is
what the viewer, the index and the exports show next — until a later machine
run re-reads the page, which would show above it again (STATUS.md, G1).
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align.audit import split_ref

from .check import CheckReport

CROWD_STAGE = "crowd"
METHOD = "crowd_ab_v1"
DEFAULT_QUEUE = Path("reports/scriptorium-queue.md")
SITE_PAGE = "https://leibnizlegible.com/page/{page_id}"
# Why a converged judgment is not imported, in the order the rules apply.
SKIP_REASONS = (
    "duplicate_in_pack",  # the same line and decision twice in the pack
    "superseded_in_pack",  # a later decision for the same line in the pack
    "no_machine_row",  # the store has no machine reading of the line
    "already_imported",  # the store holds this decision (line, decided_at)
    "not_in_fragment_pack",  # with --fragments: the line is not in it
    "winner_not_a_candidate",  # … the winning cand_id is not the line's
    "winner_text_differs",  # … or its text is not the candidate's
)


@dataclass(slots=True)
class NewLine:
    """A ``corrected`` row to insert, beside the line's machine rows."""

    line_id: str
    page_id: str
    line_seq: int
    baseline: str | None  # JSON, as the machine row stores it
    polygon: str | None
    text: str
    conf: float  # the posterior
    lang: str | None
    source: str  # the judgment row, as read


@dataclass(slots=True)
class QueueEntry:
    """A line both readings of which the players rejected."""

    line_id: str
    page_id: str
    where: str  # "LH XXIII, 2, fol. 1r"
    readings: list[tuple[str, str]]  # (source, text), in the pack's order
    posterior: float
    decided_at: str


@dataclass(slots=True)
class ImportPlan:
    """What an import would do (the dry run) or did (``--write``)."""

    header: dict
    to_insert: list[NewLine] = field(default_factory=list)
    queue: list[QueueEntry] = field(default_factory=list)
    skipped: Counter = field(default_factory=Counter)
    n_rows: int = 0
    n_converged: int = 0
    n_both_rejected: int = 0
    fragments_pack_id: str | None = None


# --------------------------------------------------------------------------- #
# Reading the store
# --------------------------------------------------------------------------- #


def machine_row(conn: sqlite3.Connection, page_id: str, line_seq: int) -> sqlite3.Row | None:
    """The line's current machine row — the store's rule among the machine rows
    (a scoped run's before an unscoped one's, then the newest; K4) — by the
    ``(page_id, line_seq)`` index."""
    return conn.execute(
        f"WITH {db.run_rank_cte(conn)} SELECT l.* FROM lines l"
        " LEFT JOIN rk lr ON lr.run_id = l.run_id"
        " WHERE l.page_id = ? AND l.line_seq = ? AND l.status = 'machine'"
        " ORDER BY COALESCE(lr.prec, 0) DESC, COALESCE(l.run_id, 0) DESC LIMIT 1",
        (page_id, line_seq),
    ).fetchone()


def imported_decisions(conn: sqlite3.Connection, page_id: str, line_seq: int) -> set[str]:
    """The ``decided_at`` of every crowd judgment the store holds for the line."""
    out: set[str] = set()
    for (source,) in conn.execute(
        "SELECT source FROM lines WHERE page_id = ? AND line_seq = ? AND status = 'corrected'",
        (page_id, line_seq),
    ):
        try:
            row = json.loads(source) if source else None
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("method") == METHOD and row.get("decided_at"):
            out.add(str(row["decided_at"]))
    return out


def _where(conn: sqlite3.Connection, page_id: str) -> str:
    """The page as a reader finds it: the work's shelfmark and the folio."""
    page = db.get_page(conn, page_id)
    if page is None:
        return "not in the store"
    work = db.get_work(conn, page.work_id)
    shelfmark = next((s for s in (work.shelfmarks if work else []) if s), None)
    folio = f"fol. {page.label}" if page.label else f"canvas {page.seq}"
    return f"{shelfmark}, {folio}" if shelfmark else folio


# --------------------------------------------------------------------------- #
# The plan
# --------------------------------------------------------------------------- #


def _latest_per_line(rows: list[tuple[dict, str]], skipped: Counter) -> list[tuple[dict, str]]:
    """One converged judgment per line, the latest decision; the rest counted."""
    best: dict[str, tuple[dict, str]] = {}
    for row, raw in rows:
        cur = best.get(row["line_id"])
        if cur is None:
            best[row["line_id"]] = (row, raw)
        elif row["decided_at"] == cur[0]["decided_at"]:
            skipped["duplicate_in_pack"] += 1
        else:
            skipped["superseded_in_pack"] += 1
            if row["decided_at"] > cur[0]["decided_at"]:
                best[row["line_id"]] = (row, raw)
    return [best[k] for k in sorted(best)]


def plan_import(
    conn: sqlite3.Connection,
    report: CheckReport,
    *,
    fragments: Mapping[str, dict] | None = None,
    fragments_pack_id: str | None = None,
) -> ImportPlan:
    """What to import and what to queue, from a checked judgment pack; reads
    the store only. ``fragments`` maps line ids to the fragment pack's rows."""
    if not report.ok or report.header is None:
        raise ValueError("the judgment pack does not check: nothing is read from it")
    plan = ImportPlan(
        header=report.header, n_rows=len(report.rows), fragments_pack_id=fragments_pack_id
    )
    converged: list[tuple[dict, str]] = []
    queued: set[tuple[str, str]] = set()
    for row, raw in zip(report.rows, report.raws, strict=True):
        if row["retirement"] == "converged":
            plan.n_converged += 1
            converged.append((row, raw))
            continue
        plan.n_both_rejected += 1
        key = (row["line_id"], row["decided_at"])
        if key in queued:
            continue
        queued.add(key)
        plan.queue.append(_queue_entry(conn, row, fragments))
    for row, raw in _latest_per_line(converged, plan.skipped):
        line_id = row["line_id"]
        page_id, line_seq = split_ref(line_id)
        machine = machine_row(conn, page_id, line_seq)
        if machine is None:
            plan.skipped["no_machine_row"] += 1
            continue
        if row["decided_at"] in imported_decisions(conn, page_id, line_seq):
            plan.skipped["already_imported"] += 1
            continue
        if fragments is not None:
            reason = _winner_fault(row, fragments.get(line_id))
            if reason:
                plan.skipped[reason] += 1
                continue
        plan.to_insert.append(
            NewLine(
                line_id=line_id,
                page_id=page_id,
                line_seq=line_seq,
                baseline=machine["baseline"],
                polygon=machine["polygon"],
                text=row["winning_text"],
                conf=float(row["posterior"]),
                lang=machine["lang"],
                source=raw,
            )
        )
    plan.queue.sort(key=lambda q: (q.line_id, q.decided_at))
    return plan


def _winner_fault(row: Mapping, fragment: Mapping | None) -> str | None:
    """Why the winner is not the fragment pack's candidate, or ``None``."""
    if fragment is None:
        return "not_in_fragment_pack"
    cand = next((c for c in fragment["candidates"] if c["cand_id"] == row["winning_cand_id"]), None)
    if cand is None:
        return "winner_not_a_candidate"
    if cand["text"] != row["winning_text"]:
        return "winner_text_differs"
    return None


def _queue_entry(
    conn: sqlite3.Connection, row: Mapping, fragments: Mapping[str, dict] | None
) -> QueueEntry:
    line_id = row["line_id"]
    page_id, line_seq = split_ref(line_id)
    fragment = (fragments or {}).get(line_id)
    if fragment is not None:
        readings = [(c["source"], c["text"]) for c in fragment["candidates"]]
    else:
        machine = machine_row(conn, page_id, line_seq)
        readings = (
            [("htr_best", machine["text"])] if machine is not None and machine["text"] else []
        )
    return QueueEntry(
        line_id=line_id,
        page_id=page_id,
        where=_where(conn, page_id),
        readings=readings,
        posterior=float(row["posterior"]),
        decided_at=str(row["decided_at"]),
    )


# --------------------------------------------------------------------------- #
# The write
# --------------------------------------------------------------------------- #


def apply_import(
    conn: sqlite3.Connection, plan: ImportPlan, *, git_sha: str | None, params: Mapping
) -> int | None:
    """Insert the plan's rows under a new ``crowd`` run, in one transaction;
    the run id, or ``None`` when there is nothing to import (no run is opened)."""
    if not plan.to_insert:
        return None
    model = f"{METHOD}@{plan.header['game']['git_sha']}"
    n_failed = sum(v for k, v in plan.skipped.items() if k != "already_imported")
    with conn:
        cur = conn.execute(
            "INSERT INTO runs (stage, model, params, started_at, git_sha) VALUES (?, ?, ?, ?, ?)",
            (CROWD_STAGE, model, json.dumps(dict(params)), db.utcnow_iso(), git_sha),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            "INSERT INTO lines (line_id, page_id, line_seq, baseline, polygon, text, conf, "
            "model, run_id, status, lang, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'corrected', ?, ?)",
            [
                (
                    n.line_id,
                    n.page_id,
                    n.line_seq,
                    n.baseline,
                    n.polygon,
                    n.text,
                    n.conf,
                    model,
                    run_id,
                    n.lang,
                    n.source,
                )
                for n in plan.to_insert
            ],
        )
        conn.execute(
            "UPDATE runs SET finished_at = ?, n_input = ?, n_ok = ?, n_failed = ? WHERE run_id = ?",
            (db.utcnow_iso(), plan.n_converged, len(plan.to_insert), n_failed, run_id),
        )
    return run_id


# --------------------------------------------------------------------------- #
# The Scriptorium queue
# --------------------------------------------------------------------------- #

QUEUE_HEAD = """# Scriptorium queue

_Rendered by `leibniz pack judgments` (Phase G1) from the judgment packs of
Calculemus, one section per pack; do not edit by hand — reading a pack again
replaces its section._

Lines whose two machine readings the players rejected both
(`retirement: both_rejected`): neither matches the image, so a person
transcribes the line from it — the Scriptorium (NOTES.md, section B), not yet
built. `htr_best` is the site's machine text (v1), `model_alt` the second
reader's (the Bern Kurrent model, K2). Machine readings only, no edition text;
the posterior is the game's confidence in its verdict.
"""

_SECTION_RE = re.compile(r"<!-- pack:(?P<id>.+?) -->\n.*?<!-- /pack:(?P=id) -->\n?", re.DOTALL)
_MD_SPECIALS = str.maketrans(
    {
        "\\": "\\\\",
        "|": "\\|",
        "*": "\\*",
        "_": "\\_",
        "`": "\\`",
        "[": "\\[",
        "]": "\\]",
        "<": "&lt;",
        ">": "&gt;",
    }
)


def md_cell(text: str) -> str:
    """Text safe in a Markdown table cell, on one line."""
    return " ".join(str(text).split()).translate(_MD_SPECIALS)


def queue_section(plan: ImportPlan, *, file_label: str, read_on: str) -> str:
    """This judgment pack's section of the queue, between its markers."""
    pack_id = plan.header["pack_id"]
    game = plan.header["game"]["git_sha"]
    source = (
        f"the readings as the fragment pack `{plan.fragments_pack_id}` carried them"
        if plan.fragments_pack_id
        else "the store's machine reading only (the fragment pack was not given)"
    )
    n = len(plan.queue)
    out = [
        f"<!-- pack:{pack_id} -->",
        f"## Judgment pack `{pack_id}`",
        "",
        f"Built {plan.header['built_at']} by the game at `{game}`; read from `{file_label}` "
        f"on {read_on}; {source}. {n:,} line{'s' if n != 1 else ''}.",
        "",
    ]
    if plan.queue:
        out += [
            "| line | page | reading | reading | posterior | decided |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
        for q in plan.queue:
            cells = [f"{md_cell(text)} (`{src}`)" for src, text in q.readings]
            cells += ["—"] * (2 - len(cells))
            page = f"[`{q.page_id}`]({SITE_PAGE.format(page_id=q.page_id)}) {md_cell(q.where)}"
            out.append(
                f"| `{q.line_id}` | {page} | {cells[0]} | {cells[1]} | "
                f"{q.posterior:.3f} | {md_cell(q.decided_at)} |"
            )
    else:
        out.append("No line of this pack was rejected both ways.")
    out.append(f"<!-- /pack:{pack_id} -->")
    return "\n".join(out) + "\n"


def render_queue(existing: str | None, section: str, pack_id: str) -> str:
    """The queue file with this pack's section replaced, or added at the end."""
    sections = [(m.group("id"), m.group(0)) for m in _SECTION_RE.finditer(existing or "")]
    if any(sid == pack_id for sid, _ in sections):
        sections = [(sid, section if sid == pack_id else text) for sid, text in sections]
    else:
        sections.append((pack_id, section))
    body = "\n".join(text.rstrip("\n") + "\n" for _, text in sections)
    return QUEUE_HEAD + "\n" + body


def write_queue(path: Path | str, plan: ImportPlan, *, file_label: str, read_on: str) -> Path:
    """Render this pack's section into the queue file (created if absent)."""
    out = Path(path)
    existing = out.read_text(encoding="utf-8") if out.exists() else None
    section = queue_section(plan, file_label=file_label, read_on=read_on)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_queue(existing, section, plan.header["pack_id"]), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# What the command prints
# --------------------------------------------------------------------------- #


def summary_lines(plan: ImportPlan, *, wrote: bool, run_id: int | None) -> list[str]:
    """The plan, or the import, as the command prints it."""
    h = plan.header
    out = [
        f"Judgment pack {h['pack_id']} (built {h['built_at']}, game {h['game']['git_sha']}): "
        f"{plan.n_rows:,} rows — converged {plan.n_converged:,}, both_rejected "
        f"{plan.n_both_rejected:,}",
        (
            f"Fragment pack {plan.fragments_pack_id}: every winner checked against its candidates"
            if plan.fragments_pack_id
            else "No fragment pack given (--fragments): the winners are not checked against "
            "the candidates, and the queue shows the store's v1 reading only"
        ),
        f"Converged: {len(plan.to_insert):,} to import as 'corrected' lines",
    ]
    for reason in SKIP_REASONS:
        if plan.skipped.get(reason):
            out.append(f"  skipped {reason:<24} {plan.skipped[reason]:>7,}")
    n = len(plan.queue)
    out.append(f"Both rejected: {n:,} line{'s' if n != 1 else ''} for the Scriptorium queue")
    model = f"{METHOD}@{h['game']['git_sha']}"
    if wrote:
        out.append(
            f"Wrote {len(plan.to_insert):,} rows under run {run_id} (stage {CROWD_STAGE}, "
            f"model {model}); no machine row was changed."
            if run_id is not None
            else "Nothing to write: no run opened, the store unchanged."
        )
    else:
        out.append(
            "Dry run: the store was opened read-only and nothing was written to it; --write "
            f"imports the {len(plan.to_insert):,} rows under a new run ({model})."
        )
    return out


__all__ = [
    "CROWD_STAGE",
    "DEFAULT_QUEUE",
    "METHOD",
    "QUEUE_HEAD",
    "SKIP_REASONS",
    "ImportPlan",
    "NewLine",
    "QueueEntry",
    "apply_import",
    "imported_decisions",
    "machine_row",
    "md_cell",
    "plan_import",
    "queue_section",
    "render_queue",
    "summary_lines",
    "write_queue",
]
