"""K2's mint: the factory over the Bern Kurrent reader's text, piece by piece (Tasks 2 and 3).

What the factory mints is always the edition's text, never the reader's: the
reader's text is what each manuscript line is *aligned on*, and a reader that
knows Kurrent places more of a German piece's lines at the factory's gate than
the store's v1 reading does (K1's pilot: 20.2 % against 16.4 % of the lines).
This module runs the factory's own alignment (:func:`leibniz.align.factory.mint_piece`,
the per-stratum thresholds, the aligner's defaults) over the K2 readings
(``data/kurrent/k2-readings/<reader>.jsonl``) for every German piece of the
census, as a **dry run** first, and sets it beside what ``gt_lines`` holds for
the piece's record today — the C2c re-mint from the v1 text, read by
``record_id`` as W5 asks.

**The rule: one reader per piece.** Two alignments of one piece draw their
line boundaries differently; mixing them would duplicate or drop words at the
seams. So the Bern mint replaces the stored one where it mints *more* lines at
the same gate, and the stored mint stays everywhere else (a tie keeps it). A
piece whose rows already name this reader is the reader's own earlier mint
and is replaced by its new one (idempotent).

**The write** (Task 3, after a backup and the operator's go) goes through
:func:`~leibniz.align.factory.write_record` — one ``BEGIN IMMEDIATE``
transaction per piece, the record's own rows replaced, a line two records
mint kept for the higher alignment confidence — under one ``runs`` row whose
model names the aligner and the reader. The rows carry the factory's source
string with the reader named *before* ``katalog``
(:func:`~leibniz.align.factory.source_string`), so every consumer that reads
the record id up to the closing parenthesis still does, and
:func:`~leibniz.align.pairs.reader_from_source` tells the rows apart. The
factory's guard (``skipped:reader_minted``) and ``gt-reset`` then leave them
alone when the v1 text is minted again.

Reports go to ``reports/kurrent/`` (small, rendered from the data); the
per-piece decisions, the side-by-side page and the audit sheet stay under
``data/kurrent/`` (gitignored). The store is opened read-only for everything
but the write.
"""

from __future__ import annotations

import base64
import csv
import html
import json
import random
import sqlite3
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz import db
from leibniz.align.align import HtrLine
from leibniz.align.audit import (
    DEFAULT_HELP_HTML,
    AuditLine,
    attach_images,
    sample_lines,
    write_sheet,
)
from leibniz.align.factory import (
    FactoryConfig,
    PieceResult,
    mint_piece,
    with_write_lock,
    write_record,
)
from leibniz.align.kurrent_pilot import (
    DEFAULT_IMAGES_ROOT,
    Reading,
    crop,
    load_readings,
    page_image_path,
    page_lines,
)
from leibniz.align.kurrent_read import (
    DEFAULT_READER,
    DEFAULT_READINGS_DIR,
    german_piece_refs,
    load_stats,
    resolve_pages,
)
from leibniz.align.pairs import GtPair, ensure_gt_ownership, reader_from_source, record_readers
from leibniz.align.volumes import PieceRef
from leibniz.catalog.hands import hand_from_textart, is_leibniz_hand

DEFAULT_DECISIONS = Path("data/kurrent/k2-decisions.jsonl")
DEFAULT_SIDE_BY_SIDE = Path("data/kurrent/k2-side-by-side.html")
DEFAULT_AUDIT_DIR = Path("data/kurrent")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
SIDE_BY_SIDE_LINES = 40
AUDIT_LINES = 200
SEED = 20261020
RULE = (
    "one reader per piece: the reader's mint replaces the stored one where it mints more "
    "lines at the same per-stratum gate; elsewhere the stored mint stays (a tie keeps it); "
    "a piece whose rows name this reader is re-minted by it"
)
STRATA = ("fair_copy", "light_revision", "heavy_revision", "scrap", "unknown")
HANDS = ("own", "partial", "other", "none")


# --------------------------------------------------------------------------- #
# The decision per piece
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PieceDecision:
    """One German piece: the reader's dry run beside the stored mint, and the winner."""

    record_id: str
    aa_label: str
    volume_label: str
    status: str  # minted | skipped:<reason>
    stratum: str = "unknown"
    threshold: float = 0.0
    hand: str = "none"
    leibniz_hand: bool = False
    language: str = ""
    textart: str | None = None
    n_pages: int = 0
    n_lines: int = 0  # recognised lines on the piece's pages
    n_read: int = 0  # of them with a non-empty reading by the reader
    bern_minted: int = 0
    bern_conf_sum: float = 0.0
    stored_minted: int = 0
    stored_conf_sum: float = 0.0
    stored_reader: str | None = None  # None: the v1 text; "mixed": several sources
    winner: str = "none"  # bern | stored | none

    @property
    def bern_yield(self) -> float | None:
        return self.bern_minted / self.n_lines if self.n_lines else None

    @property
    def stored_yield(self) -> float | None:
        return self.stored_minted / self.n_lines if self.n_lines else None

    @property
    def bern_mean_conf(self) -> float | None:
        return self.bern_conf_sum / self.bern_minted if self.bern_minted else None

    @property
    def stored_mean_conf(self) -> float | None:
        return self.stored_conf_sum / self.stored_minted if self.stored_minted else None

    @property
    def after_minted(self) -> int:
        """The piece's minted lines once the rule is applied."""
        return self.bern_minted if self.winner == "bern" else self.stored_minted

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(
            bern_yield=self.bern_yield,
            stored_yield=self.stored_yield,
            bern_mean_conf=self.bern_mean_conf,
            stored_mean_conf=self.stored_mean_conf,
            after_minted=self.after_minted,
        )
        return d


def decide(bern_minted: int, stored_minted: int, stored_reader: str | None, reader: str) -> str:
    """The rule (:data:`RULE`) as a function: ``bern`` | ``stored`` | ``none``."""
    if stored_reader == reader:
        return "bern" if bern_minted else ("stored" if stored_minted else "none")
    if bern_minted > stored_minted:
        return "bern"
    return "stored" if stored_minted else "none"


def stored_mint(conn: sqlite3.Connection, record_id: str) -> tuple[int, float, str | None]:
    """``(rows, sum of align_conf, reader)`` of the record's rows in ``gt_lines`` today;
    the reader is ``None`` for the v1 text, ``"mixed"`` where the rows disagree."""
    rows = conn.execute(
        "SELECT align_conf, source FROM gt_lines WHERE record_id = ?", (record_id,)
    ).fetchall()
    readers = {reader_from_source(r[1]) for r in rows}
    reader = None
    if len(readers) == 1:
        reader = next(iter(readers))
    elif readers:
        reader = "mixed"
    return len(rows), sum(float(r[0] or 0.0) for r in rows), reader


def reader_text_for(
    readings: Mapping[str, Reading],
) -> Callable[[Sequence[HtrLine]], list[HtrLine]]:
    """The factory's ``reader_text``: the same lines, the reader's text where it read them."""

    def swap(lines: Sequence[HtrLine]) -> list[HtrLine]:
        out: list[HtrLine] = []
        for ln in lines:
            r = readings.get(ln.ref)
            out.append(HtrLine(ref=ln.ref, text=r.text if r is not None else "", meta=ln.meta))
        return out

    return swap


def _absender(conn: sqlite3.Connection, record_id: str) -> str | None:
    rec = db.get_katalog_record(conn, record_id)
    if rec is None:
        return None
    value = rec.metadata.get("absender")
    return str(value) if value else None


def dry_run_piece(
    conn: sqlite3.Connection,
    row: Mapping,
    piece: PieceRef | None,
    text: str,
    readings: Mapping[str, Reading],
    *,
    reader: str,
    config: FactoryConfig,
) -> tuple[PieceDecision, list[GtPair]]:
    """One census row: the factory's dry run on the reader's text, the stored mint, the winner."""
    rid = str(row["record_id"])
    hand = hand_from_textart(piece.textart if piece is not None else row.get("textart"))
    dec = PieceDecision(
        record_id=rid,
        aa_label=piece.aa_label if piece is not None else str(row.get("aa_label") or ""),
        volume_label=piece.volume_label
        if piece is not None
        else str(row.get("volume_label") or ""),
        status="skipped:no_piece",
        hand=hand,
        leibniz_hand=is_leibniz_hand(hand, _absender(conn, rid)),
        language=str(row.get("language") or ""),
        textart=piece.textart if piece is not None else row.get("textart"),
    )
    dec.stored_minted, dec.stored_conf_sum, dec.stored_reader = stored_mint(conn, rid)
    pairs: list[GtPair] = []
    if piece is not None:
        result: PieceResult = mint_piece(
            conn,
            piece,
            text,
            config,
            insert=False,
            reader=reader,
            reader_text=reader_text_for(readings),
            keep_pairs=True,
        )
        dec.status = result.status
        dec.stratum = result.stratum
        dec.threshold = result.threshold
        dec.n_pages = result.n_canvases
        dec.n_lines = result.n_htr_lines
        if result.minted:
            pairs = result.pairs
            dec.bern_minted = len(pairs)
            dec.bern_conf_sum = sum(p.align_conf for p in pairs)
        pages = resolve_pages(conn, piece)
        dec.n_read = sum(
            1
            for pid in pages
            for ln in page_lines(conn, pid)
            if ln.line_id in readings and readings[ln.line_id].text.strip()
        )
    dec.winner = decide(dec.bern_minted, dec.stored_minted, dec.stored_reader, reader)
    return dec, pairs


@dataclass(slots=True)
class DryRun:
    decisions: list[PieceDecision]
    pairs: dict[str, list[GtPair]]  # record → the reader's pairs (minted pieces only)
    reader: str
    thresholds: dict[str, float]
    store_rows_before: int  # every row of gt_lines before the write
    seconds: float = 0.0

    @property
    def german_before(self) -> int:
        return sum(d.stored_minted for d in self.decisions)

    @property
    def german_after(self) -> int:
        return sum(d.after_minted for d in self.decisions)

    @property
    def store_rows_after(self) -> int:
        """What the store should hold after the write, before the ownership rule speaks
        (a line two records mint goes to the higher confidence, so the written count may
        differ by a few)."""
        return self.store_rows_before - self.german_before + self.german_after


def dry_run(
    conn: sqlite3.Connection,
    rows: Sequence[Mapping],
    cache: Mapping[str, str],
    readings: Mapping[str, Reading],
    *,
    reader: str = DEFAULT_READER,
    refs: Mapping[str, Sequence[Mapping]] | None = None,
    today: date | None = None,
    config: FactoryConfig | None = None,
    progress: Callable[[PieceDecision], None] | None = None,
) -> DryRun:
    """Every census row through :func:`dry_run_piece`; nothing written."""
    t0 = time.monotonic()
    config = config or FactoryConfig(today=today or date.today())
    pieces = german_piece_refs(conn, (str(r["record_id"]) for r in rows), refs=refs, today=today)
    before = conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0]
    out = DryRun([], {}, reader, dict(config.stratum_thresholds), before)
    seen: set[str] = set()
    for row in rows:
        rid = str(row["record_id"])
        if rid in seen:
            continue  # the census lists a record once per citation; the factory mints it once
        seen.add(rid)
        dec, pairs = dry_run_piece(
            conn, row, pieces.get(rid), cache.get(rid, ""), readings, reader=reader, config=config
        )
        out.decisions.append(dec)
        if pairs:
            out.pairs[rid] = pairs
        if progress is not None:
            progress(dec)
    out.seconds = time.monotonic() - t0
    return out


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Tally:
    pieces: int = 0
    minted_pieces: int = 0  # pieces the dry run could align (not skipped)
    lines: int = 0
    read: int = 0
    bern_minted: int = 0
    bern_conf_sum: float = 0.0
    stored_minted: int = 0
    stored_conf_sum: float = 0.0
    won_bern: int = 0
    won_stored: int = 0
    won_none: int = 0
    after_minted: int = 0
    after_bern: int = 0  # of the lines after the rule, those aligned on the reader's text

    def add(self, d: PieceDecision) -> None:
        self.pieces += 1
        self.minted_pieces += int(d.status == "minted")
        self.lines += d.n_lines
        self.read += d.n_read
        self.bern_minted += d.bern_minted
        self.bern_conf_sum += d.bern_conf_sum
        self.stored_minted += d.stored_minted
        self.stored_conf_sum += d.stored_conf_sum
        if d.winner == "bern":
            self.won_bern += 1
            self.after_bern += d.bern_minted
        elif d.winner == "stored":
            self.won_stored += 1
        else:
            self.won_none += 1
        self.after_minted += d.after_minted

    @property
    def bern_yield(self) -> float | None:
        return self.bern_minted / self.lines if self.lines else None

    @property
    def stored_yield(self) -> float | None:
        return self.stored_minted / self.lines if self.lines else None

    @property
    def after_yield(self) -> float | None:
        return self.after_minted / self.lines if self.lines else None

    @property
    def bern_conf(self) -> float | None:
        return self.bern_conf_sum / self.bern_minted if self.bern_minted else None

    @property
    def stored_conf(self) -> float | None:
        return self.stored_conf_sum / self.stored_minted if self.stored_minted else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(
            bern_yield=self.bern_yield,
            stored_yield=self.stored_yield,
            after_yield=self.after_yield,
            bern_conf=self.bern_conf,
            stored_conf=self.stored_conf,
        )
        return d


def tally_by(
    decisions: Iterable[PieceDecision], key: Callable[[PieceDecision], str]
) -> dict[str, Tally]:
    out: dict[str, Tally] = {}
    for d in decisions:
        out.setdefault(key(d), Tally()).add(d)
    return out


def _volume_key(label: str) -> tuple[int, int, str]:
    roman = {"I": 1, "II": 2, "III": 3, "IV": 4, "VI": 6, "VII": 7}
    series, _, vol = label.partition(",")
    try:
        return roman.get(series, 99), int(vol), label
    except ValueError:
        return roman.get(series, 99), 999, label


def summary(run: DryRun, *, plan: Mapping | None, stats: Mapping | None) -> dict:
    """Every number of the report, from the decisions and the reading job's files."""
    decs = run.decisions
    aligned = [d for d in decs if d.status == "minted"]
    skips: dict[str, int] = {}
    for d in decs:
        if d.status != "minted":
            reason = d.status.split(":", 1)[-1]
            skips[reason] = skips.get(reason, 0) + 1
    return {
        "reader": run.reader,
        "rule": RULE,
        "thresholds": run.thresholds,
        "pieces": len(decs),
        "pieces_aligned": len(aligned),
        "piece_skips": skips,
        "reading": {
            "plan": dict(plan) if plan else None,
            "job": dict(stats) if stats else None,
        },
        "all": Tally.as_dict(_all(decs)),
        "by_stratum": {
            k: t.as_dict()
            for k, t in _ordered(tally_by(aligned, lambda d: d.stratum), STRATA).items()
        },
        "by_hand": {
            k: t.as_dict() for k, t in _ordered(tally_by(aligned, lambda d: d.hand), HANDS).items()
        },
        "leibniz_hand": Tally.as_dict(_all(d for d in aligned if d.leibniz_hand)),
        "by_language": {
            k: t.as_dict()
            for k, t in sorted(tally_by(aligned, lambda d: d.language or "?").items())
        },
        "by_volume": {
            k: t.as_dict()
            for k, t in sorted(
                tally_by(aligned, lambda d: d.volume_label).items(),
                key=lambda kv: _volume_key(kv[0]),
            )
        },
        "won": {
            "bern": sum(1 for d in decs if d.winner == "bern"),
            "stored": sum(1 for d in decs if d.winner == "stored"),
            "none": sum(1 for d in decs if d.winner == "none"),
        },
        "mint": {
            "german_before": run.german_before,
            "german_after": run.german_after,
            "store_before": run.store_rows_before,
            "store_after_expected": run.store_rows_after,
            "bern_rows_after": sum(d.bern_minted for d in decs if d.winner == "bern"),
            "stored_rows_after": sum(d.stored_minted for d in decs if d.winner == "stored"),
            "stored_rows_replaced": sum(d.stored_minted for d in decs if d.winner == "bern"),
        },
        "seconds": round(run.seconds, 1),
    }


def _all(decs: Iterable[PieceDecision]) -> Tally:
    t = Tally()
    for d in decs:
        t.add(d)
    return t


def _ordered(groups: Mapping[str, Tally], order: Sequence[str]) -> dict[str, Tally]:
    out = {k: groups[k] for k in order if k in groups}
    out.update({k: v for k, v in sorted(groups.items()) if k not in out})
    return out


# --------------------------------------------------------------------------- #
# Files: decisions, reports, CSVs
# --------------------------------------------------------------------------- #


def write_decisions(path: Path | str, run: DryRun) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for d in run.decisions:
            fh.write(json.dumps(d.as_dict(), ensure_ascii=False) + "\n")
    return path


def load_decisions(path: Path | str) -> list[PieceDecision]:
    out: list[PieceDecision] = []
    fields = {f for f in PieceDecision.__slots__}  # type: ignore[attr-defined]
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if raw.strip():
            row = json.loads(raw)
            out.append(PieceDecision(**{k: v for k, v in row.items() if k in fields}))
    return out


def pairs_path_for(decisions: Path | str) -> Path:
    """The reader's pairs beside the decisions: ``k2-decisions.jsonl`` → ``k2-pairs.jsonl``."""
    d = Path(decisions)
    return d.with_name(
        d.name.replace("decisions", "pairs") if "decisions" in d.name else d.stem + "-pairs.jsonl"
    )


def write_pairs(path: Path | str, run: DryRun) -> Path:
    """Every pair of the dry run (minted pieces, won or not), one JSON row each, so the
    write of Task 3 can use exactly what the report of Task 2 described."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for rid, pairs in run.pairs.items():
            for pr in pairs:
                fh.write(
                    json.dumps(
                        {
                            "record_id": rid,
                            "ref": pr.line_image_ref,
                            "text": pr.text,
                            "source": pr.source,
                            "stratum": pr.stratum,
                            "align_conf": pr.align_conf,
                            "license_bucket": pr.license_bucket,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    return path


def load_pairs(path: Path | str) -> dict[str, list[GtPair]]:
    out: dict[str, list[GtPair]] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if raw.strip():
            r = json.loads(raw)
            out.setdefault(r["record_id"], []).append(
                GtPair(
                    r["ref"],
                    r["text"],
                    r["source"],
                    r["stratum"],
                    float(r["align_conf"]),
                    r["license_bucket"],
                    r["record_id"],
                )
            )
    return out


def load_run(
    conn: sqlite3.Connection,
    decisions_path: Path | str,
    pairs_path: Path | str,
    *,
    reader: str,
    thresholds: Mapping[str, float],
) -> DryRun:
    """A dry run rebuilt from its two files for the write, checked against the store:
    the rows on the German records must be what the dry run saw, else the store moved
    since the report and this refuses."""
    decisions = load_decisions(decisions_path)
    pairs = load_pairs(pairs_path)
    before = conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0]
    run = DryRun(decisions, pairs, reader, dict(thresholds), before)
    for d in decisions:
        if d.winner == "bern" and d.record_id not in pairs:
            raise ValueError(
                f"{pairs_path} holds no pairs for {d.record_id}, which the rule gives to the reader"
            )
        n, _conf, who = stored_mint(conn, d.record_id)
        if (n, who) != (d.stored_minted, d.stored_reader):
            raise ValueError(
                f"the store moved since the dry run: record {d.record_id} holds {n} rows "
                f"({who or 'v1'}) now, {d.stored_minted} ({d.stored_reader or 'v1'}) then; "
                "run the dry run again"
            )
    return run


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{100 * x:.{d}f} %"


def _conf(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def _n(x: int | None) -> str:
    return "—" if x is None else f"{x:,}"


def _tally_row(label: str, t: Mapping) -> str:
    return (
        f"| {label} | {_n(t['pieces'])} | {_n(t['lines'])} | {_n(t['read'])} | "
        f"{_n(t['stored_minted'])} | {_pct(t['stored_yield'])} | {_conf(t['stored_conf'])} | "
        f"{_n(t['bern_minted'])} | **{_pct(t['bern_yield'])}** | {_conf(t['bern_conf'])} | "
        f"{_n(t['won_bern'])} | {_n(t['won_stored'])} | {_n(t['after_minted'])} | "
        f"{_pct(t['after_yield'])} |"
    )


_TALLY_HEAD = (
    "| group | pieces | lines | read | v1 minted | v1 yield | v1 conf | Bern minted | "
    "**Bern yield** | Bern conf | won: Bern | won: v1 | after K2 | yield after |"
)
_TALLY_SEP = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"


def render_report(s: Mapping, *, generated: str | None = None) -> str:
    """``reports/kurrent/k2-mint.md`` from :func:`summary`."""
    out: list[str] = []
    A = out.append
    reader = s["reader"]
    A("# K2: the German pieces minted from the Bern Kurrent reading")
    A("")
    A(
        f"The factory's alignment over the readings of `{reader}` for every German piece of the "
        "census (`data/kurrent/german_pieces.jsonl`), at the per-stratum thresholds "
        f"({', '.join(f'{k} {v:.2f}' for k, v in s['thresholds'].items())}) with the aligner's "
        "defaults (hyphens kept), the edition text from the cache — as a dry run, nothing "
        "written — beside what `gt_lines` holds for each piece's record today (the C2c re-mint "
        f"from the stored v1 text, read by `record_id`). **The rule:** {s['rule']}. What the "
        "factory mints is the edition's text in either case; the reader only decides where a "
        f"line is placed. Generated {generated or date.today().isoformat()}."
    )
    A("")
    A("## Lines read and skipped")
    A("")
    job = (s.get("reading") or {}).get("job")
    plan = (s.get("reading") or {}).get("plan")
    if plan:
        A(
            f"The reading job's pages: {_n(plan.get('n_pages'))} (the census's "
            f"{_n(plan.get('n_pages_census'))} and the factory's "
            f"{_n(plan.get('n_pages_resolver'))} "
            f"placement, united), {_n(plan.get('n_lines'))} recognised lines once each."
        )
    if job:
        A(
            f"Read: **{_n(job.get('lines_done'))}** of {_n(job.get('lines_total'))}; skipped "
            f"{_n(job.get('n_skipped'))}"
            + (
                " ("
                + ", ".join(f"{k} {v:,}" for k, v in sorted((job.get("skipped") or {}).items()))
                + ")"
                if job.get("skipped")
                else ""
            )
            + f"; left unread {_n(job.get('lines_left'))}. Model `{job.get('model')}` on "
            f"`{job.get('device')}`, settings "
            f"{json.dumps(job.get('settings') or {}, ensure_ascii=False)}; "
            f"the last run {job.get('lines_per_hour') and f'{job["lines_per_hour"]:,.0f}'} lines/h."
        )
    else:
        A("No reading-job statistics were found beside the readings.")
    t = s["all"]
    A(
        f"On the pieces: {_n(s['pieces'])} records, {_n(s['pieces_aligned'])} aligned"
        + (
            " (skipped: "
            + ", ".join(f"{k} {v:,}" for k, v in sorted(s["piece_skips"].items()))
            + ")"
            if s["piece_skips"]
            else ""
        )
        + f"; {_n(t['lines'])} lines on their pages (a page two pieces share counts for each), "
        f"{_n(t['read'])} of them with a reading by the reader "
        f"({_pct(t['read'] / t['lines'] if t['lines'] else None)})."
    )
    A("")
    A("## Yield at the factory's gate")
    A("")
    A(
        "*v1*: the rows `gt_lines` holds for the record today (the C2c re-mint from the stored "
        "text); *Bern*: the dry run over the reader's text; *conf*: the aligner's mean matched "
        "fraction over the minted lines; *won*: pieces the rule gives to each; *after K2*: the "
        "piece's lines once the rule is applied."
    )
    A("")
    A(_TALLY_HEAD)
    A(_TALLY_SEP)
    A(_tally_row("**all German records** (the skipped ones with 0 lines)", t))
    for k, tt in s["by_stratum"].items():
        A(_tally_row(k, tt))
    A("")
    A("### By hand")
    A("")
    A(
        "*own*: the piece is in its author's own hand (the catalogue's *eigh.* on the piece, "
        "`catalog/hands.py`); *partial*: an address, a correction or a postscript only; *other*: "
        "a scribe's; *Leibniz's hand*: *own* with no sender or Leibniz as sender."
    )
    A("")
    A(_TALLY_HEAD)
    A(_TALLY_SEP)
    for k, tt in s["by_hand"].items():
        A(_tally_row(k, tt))
    A(_tally_row("**Leibniz's hand**", s["leibniz_hand"]))
    A("")
    A("### By language")
    A("")
    A(_TALLY_HEAD)
    A(_TALLY_SEP)
    for k, tt in s["by_language"].items():
        A(_tally_row({"de": "German", "mixed": "mixed, German leading"}.get(k, k), tt))
    A("")
    A("### By volume")
    A("")
    A("`k2-mint-by-volume.csv` has the same rows.")
    A("")
    A(_TALLY_HEAD)
    A(_TALLY_SEP)
    for k, tt in s["by_volume"].items():
        A(_tally_row(k, tt))
    A("")
    A("## The pieces won by each reader")
    A("")
    w = s["won"]
    A(
        f"Of {_n(s['pieces'])} German records, the rule gives **{_n(w['bern'])}** to the Bern "
        f"reading, **{_n(w['stored'])}** keep the v1 mint, and {_n(w['none'])} mint nothing under "
        "either (no lines at the gate, or no piece to align)."
    )
    A("")
    A("## The mint after K2, against before")
    A("")
    m = s["mint"]
    A(
        f"Lines minted on the German records: **{_n(m['german_before'])} → "
        f"{_n(m['german_after'])}** "
        f"({_n(m['bern_rows_after'])} aligned on the Bern reading on the pieces it won, replacing "
        f"{_n(m['stored_rows_replaced'])} v1 rows there; {_n(m['stored_rows_after'])} v1 rows stay "
        f"on the pieces it did not win). The whole store: {_n(m['store_before'])} rows before, "
        f"**{_n(m['store_after_expected'])} expected** after the write — before the factory's "
        "ownership rule speaks (a line two records mint goes to the higher alignment "
        "confidence, so the written count can differ by a few; Task 3 reports the difference)."
    )
    A("")
    A("## The training set this leaves for K3")
    A("")
    A(
        f"After the write, the German pieces carry {_n(m['german_after'])} minted lines: "
        f"{_n(m['bern_rows_after'])} whose source names `reader {reader}` (select them by "
        f"`gt_lines.source LIKE '%; reader {reader};%'`, or by `record_id` from "
        "`data/kurrent/k2-decisions.jsonl`, `winner = bern`) and "
        f"{_n(m['stored_rows_after'])} from the v1 text on the pieces the rule left as they were "
        "(`winner = stored`). By stratum and by hand, the *after K2* column above; Leibniz's own "
        f"hand: {_n(s['leibniz_hand']['after_minted'])} lines on {_n(s['leibniz_hand']['pieces'])} "
        f"pieces ({_n(s['leibniz_hand']['after_bern'])} of them on the Bern reading)."
    )
    A("")
    A("## What this measures, and what it does not")
    A("")
    A(
        "- Yield is minted lines over all recognised lines on the piece's pages; the pages carry "
        "other hands and other texts, and the edition omits or reorders what the page holds, so "
        "no reader reaches 100 %. The *v1* and *Bern* columns are measured on the same lines; the "
        "ordering is the measurement."
    )
    A(
        "- The stored mint's lines were counted by `record_id` (the factory's ownership rule "
        "already applied: a line two records mint belongs to one); the dry run's pairs are the "
        "piece's own, before that rule. The expected store count is therefore an expectation."
    )
    A(
        "- A high alignment confidence says the reader's text matches the edition's letters on "
        "that line; it does not say the slice landed on the right line, and TrOCR errs fluently. "
        "The side-by-side page (`data/kurrent/k2-side-by-side.html`) and the audit sheet "
        "(`data/kurrent/k2-audit.html`) are for that."
    )
    A("")
    return "\n".join(out)


def write_outputs(
    run: DryRun,
    *,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
    plan: Mapping | None = None,
    stats: Mapping | None = None,
) -> dict[str, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    s = summary(run, plan=plan, stats=stats)
    generated = date.today().isoformat()
    s["generated"] = generated
    paths = {
        "report": reports_dir / "k2-mint.md",
        "summary": reports_dir / "k2-mint.json",
        "by_volume": reports_dir / "k2-mint-by-volume.csv",
        "pieces": reports_dir / "k2-mint-pieces.csv",
    }
    paths["report"].write_text(render_report(s, generated=generated), encoding="utf-8")
    paths["summary"].write_text(
        json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    cols = [
        "pieces",
        "lines",
        "read",
        "stored_minted",
        "stored_yield",
        "stored_conf",
        "bern_minted",
        "bern_yield",
        "bern_conf",
        "won_bern",
        "won_stored",
        "won_none",
        "after_minted",
        "after_yield",
        "after_bern",
    ]
    with paths["by_volume"].open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["volume", *cols])
        for vol, t in s["by_volume"].items():
            w.writerow([vol, *(_csv(t[c]) for c in cols)])
    with paths["pieces"].open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "record_id",
                "aa_label",
                "volume",
                "status",
                "stratum",
                "threshold",
                "hand",
                "leibniz_hand",
                "language",
                "n_pages",
                "n_lines",
                "n_read",
                "stored_minted",
                "stored_conf",
                "stored_reader",
                "bern_minted",
                "bern_conf",
                "winner",
                "after_minted",
            ]
        )
        for d in run.decisions:
            w.writerow(
                [
                    d.record_id,
                    d.aa_label,
                    d.volume_label,
                    d.status,
                    d.stratum,
                    f"{d.threshold:.2f}",
                    d.hand,
                    int(d.leibniz_hand),
                    d.language,
                    d.n_pages,
                    d.n_lines,
                    d.n_read,
                    d.stored_minted,
                    _csv(d.stored_mean_conf),
                    d.stored_reader or "v1",
                    d.bern_minted,
                    _csv(d.bern_mean_conf),
                    d.winner,
                    d.after_minted,
                ]
            )
    return paths


def _csv(x: object) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


# --------------------------------------------------------------------------- #
# The side-by-side page (Task 2)
# --------------------------------------------------------------------------- #


def stored_refs(conn: sqlite3.Connection) -> set[str]:
    """Every line a row of ``gt_lines`` covers today (any record)."""
    return {r[0] for r in conn.execute("SELECT line_image_ref FROM gt_lines")}


def new_lines(run: DryRun, have: set[str]) -> list[tuple[PieceDecision, GtPair]]:
    """The reader's pairs on the pieces it won whose line no stored row covers today:
    what K2 adds to the mint."""
    by_rec = {d.record_id: d for d in run.decisions}
    out: list[tuple[PieceDecision, GtPair]] = []
    for rid, pairs in run.pairs.items():
        d = by_rec[rid]
        if d.winner != "bern":
            continue
        out.extend((d, p) for p in pairs if p.line_image_ref not in have)
    return out


def side_by_side(
    conn: sqlite3.Connection,
    run: DryRun,
    readings: Mapping[str, Reading],
    *,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    n: int = SIDE_BY_SIDE_LINES,
    seed: int = SEED,
) -> str:
    """``n`` newly minted lines, seeded: the crop, the minted text, the Bern and the v1 reading."""
    rng = random.Random(seed)
    pool = new_lines(run, stored_refs(conn))
    if len(pool) < n:  # not enough new lines: fall back to every line the reader minted
        by_rec = {d.record_id: d for d in run.decisions}
        pool = [
            (by_rec[rid], p)
            for rid, pairs in run.pairs.items()
            if by_rec[rid].winner == "bern"
            for p in pairs
        ]
    chosen = rng.sample(pool, min(n, len(pool))) if pool else []
    chosen.sort(key=lambda t: (t[0].record_id, t[1].line_image_ref))
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<title>K2 — newly minted German lines, side by side</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:1.5rem;max-width:1400px}"
        "img{max-width:100%;display:block;border:1px solid #ccc;margin:.4rem 0}"
        "table{border-collapse:collapse;width:100%;margin-bottom:1.6rem}"
        "td,th{border:1px solid #ddd;padding:.25rem .5rem;text-align:left;vertical-align:top}"
        "th{width:16rem;background:#f5f5f5;font-weight:600}"
        ".meta{color:#555;font-size:.9rem}.gt{font-family:Georgia,serif;font-size:1.1rem}</style>"
        "</head><body>",
        f"<h1>K2 — {len(chosen)} newly minted German lines</h1>",
        f"<p class='meta'>Drawn with seed {seed} from the lines the Bern reading "
        f"(<code>{html.escape(run.reader)}</code>) lets the factory mint on the pieces it won and "
        "that no stored row covers today. Each line: the crop (the stored v1 geometry, the polygon "
        "masked), the <b>minted text</b> (the edition's, projected onto the line), the Bern "
        "reading the alignment rested on, and the stored v1 reading for comparison. "
        "<b>Question for the operator:</b> is the minted text the text of the strip?</p>",
    ]
    for k, (d, pair) in enumerate(chosen, start=1):
        page_id = pair.line_image_ref.rpartition(":")[0]
        ln = next((x for x in page_lines(conn, page_id) if x.line_id == pair.line_image_ref), None)
        path = page_image_path(conn, page_id, Path(images_root))
        png = crop(path, ln) if (path is not None and ln is not None) else None
        img = (
            f"<img alt='line {html.escape(pair.line_image_ref)}' "
            f"src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'>"
            if png
            else "<p class='meta'>(no crop: page image not cached)</p>"
        )
        r = readings.get(pair.line_image_ref)
        bern = html.escape(r.text) if r else "<i>(not read)</i>"
        bconf = f" <span class='meta'>({r.conf:.2f})</span>" if r and r.conf is not None else ""
        v1 = html.escape(ln.v1_text or "") if ln is not None else ""
        parts.append(
            f"<h2>{k}. {html.escape(pair.line_image_ref)}</h2>"
            f"<p class='meta'>{html.escape(d.aa_label)} · katalog {html.escape(d.record_id)} · "
            f"{html.escape(d.stratum)} (threshold {d.threshold:.2f}) · hand {html.escape(d.hand)}"
            f"{' · Leibniz' if d.leibniz_hand else ''} · {html.escape(d.textart or '')} · "
            f"align conf {pair.align_conf:.2f}</p>{img}<table>"
            f"<tr><th>minted text (the edition's)</th>"
            f"<td class='gt'>{html.escape(pair.text)}</td></tr>"
            f"<tr><th>Bern reading</th><td>{bern}{bconf}</td></tr>"
            f"<tr><th>v1 reading (stored)</th><td>{v1}</td></tr></table>"
        )
    parts.append("</body></html>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# The write (Task 3)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class WriteStats:
    run_id: int
    pieces: int = 0  # pieces the rule gave to the reader
    written_pieces: int = 0
    skipped_resume: int = 0
    rows_removed: int = 0  # the records' earlier rows (v1 or an earlier reader mint)
    rows_written: int = 0
    rows_won: int = 0
    rows_lost: int = 0
    errors: dict[str, int] = field(default_factory=dict)
    seconds: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


def write_mint(
    conn: sqlite3.Connection,
    run: DryRun,
    *,
    config: FactoryConfig,
    resume: bool = False,
    progress: Callable[[PieceDecision, object], None] | None = None,
) -> WriteStats:
    """Replace the rows of every piece the rule gives to the reader with the reader's pairs.

    One ``runs`` row (stage ``gt_factory``, model ``retro-aligner+<reader>``, the
    reader, the thresholds and the rule in its params); then, piece by piece,
    :func:`~leibniz.align.factory.write_record` (one ``BEGIN IMMEDIATE``
    transaction each). Idempotent: a record's own rows are replaced. With
    ``resume``, a record whose rows all name this reader already is skipped.
    """
    t0 = time.monotonic()
    params = {
        "reader": run.reader,
        "stratum_thresholds": run.thresholds,
        "license_bucket": config.license_bucket,
        "rule": RULE,
        "resume": resume,
        "ownership": "record",
        "pieces": sum(1 for d in run.decisions if d.winner == "bern"),
    }
    run_id = with_write_lock(
        conn,
        lambda: db.start_run(
            conn,
            "gt_factory",
            model=f"retro-aligner+{run.reader}",
            params=params,
            git_sha=db.git_sha(),
        ),
    )
    with_write_lock(conn, lambda: ensure_gt_ownership(conn))
    stats = WriteStats(run_id=run_id)
    for d in run.decisions:
        if d.winner != "bern":
            continue
        stats.pieces += 1
        if resume and record_readers(conn, d.record_id) == {run.reader}:
            stats.skipped_resume += 1
            continue
        pairs = run.pairs.get(d.record_id, [])
        try:
            rw = write_record(conn, d.record_id, pairs)
        except Exception as exc:  # noqa: BLE001 — one bad piece must not end the write
            conn.rollback()
            key = type(exc).__name__
            stats.errors[key] = stats.errors.get(key, 0) + 1
            continue
        stats.written_pieces += 1
        stats.rows_removed += rw.removed
        stats.rows_written += rw.written
        stats.rows_won += rw.won
        stats.rows_lost += rw.lost
        if progress is not None:
            progress(d, rw)
    with_write_lock(
        conn,
        lambda: db.finish_run(
            conn,
            run_id,
            n_input=stats.pieces,
            n_ok=stats.written_pieces,
            n_failed=stats.pieces - stats.written_pieces - stats.skipped_resume,
        ),
    )
    stats.seconds = time.monotonic() - t0
    return stats


# --------------------------------------------------------------------------- #
# The audit sheet (Finish)
# --------------------------------------------------------------------------- #

AUDIT_HELP_HTML = (
    "<div class='help'><p><b>English.</b> For each line, compare the <b>minted text</b> (the "
    "edition's text, placed on this strip) with the <b>image strip</b> and pick one:<br>"
    "<b>correct</b> — the text is what is written on this strip (spelling modernised, "
    "abbreviations expanded and punctuation changed are fine);<br>"
    "<b>boundary</b> — it is this line, but the text starts or ends a word or more early or "
    "late;<br>"
    "<b>wrong</b> — it is another line's text, or garbage;<br>"
    "<b>unreadable</b> — you cannot tell. The grey lines are machine readings of the same strip "
    "(the Kurrent reader the alignment rested on, and the older Latin-trained one), for "
    "orientation only — they are not the text under judgement. Your choices are saved in this "
    "browser as you go; when done, click <b>Download verdicts</b>.</p>"
    "<p><b>Deutsch.</b> Vergleichen Sie für jede Zeile den <b>zugeordneten Text</b> (den Text "
    "der Edition, auf diesen Zeilenausschnitt gelegt) mit dem <b>Bildstreifen</b> und wählen "
    "Sie:<br>"
    "<b>richtig</b> (correct) — der Text ist, was auf diesem Streifen steht (modernisierte "
    "Schreibung, aufgelöste Abkürzungen und geänderte Zeichensetzung sind in Ordnung);<br>"
    "<b>Grenze</b> (boundary) — es ist diese Zeile, aber der Text beginnt oder endet ein Wort "
    "oder mehr zu früh oder zu spät;<br>"
    "<b>falsch</b> (wrong) — es ist der Text einer anderen Zeile, oder Unsinn;<br>"
    "<b>unlesbar</b> (unreadable) — Sie können es nicht entscheiden. Die grauen Zeilen sind "
    "maschinelle Lesungen desselben Streifens (der Kurrent-Leser, auf dem die Zuordnung ruht, "
    "und der ältere, auf Latein trainierte), nur zur Orientierung — nicht sie werden beurteilt. "
    "Ihre Urteile werden in diesem Browser gespeichert; am Ende klicken Sie <b>Download "
    "verdicts</b>.</p></div>"
)
AUDIT_GROUPS = {"own": "leibniz_hand", "other": "other_hands"}  # the lines CSV's `group`
AUDIT_SPLIT_NOTE = (
    "<p><b>English.</b> Half of the lines are in Leibniz's own hand and half in other hands, "
    "mixed; the sheet does not say which. "
    "<b>Deutsch.</b> Die Hälfte der Zeilen stammt von Leibniz' eigener Hand, die Hälfte von "
    "anderen Händen, gemischt; das Blatt sagt nicht, welche.</p>"
)
AUDIT_SPLIT_NOTE_EN = (
    "<p>Half of the lines are in Leibniz's own hand and half in other hands, mixed; the sheet "
    "does not say which.</p>"
)
AUDIT_VERDICT_LABELS = {
    "correct": "correct · richtig",
    "boundary": "boundary · Grenze",
    "wrong": "wrong · falsch",
    "unreadable": "unreadable · unlesbar",
}


def build_audit_sheet(
    conn: sqlite3.Connection,
    readings: Mapping[str, Reading],
    *,
    reader: str = DEFAULT_READER,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    out_dir: Path | str = DEFAULT_AUDIT_DIR,
    n: int = AUDIT_LINES,
    seed: int = SEED,
    bilingual: bool = True,
    leibniz_hand_ids: Iterable[str] | None = None,
) -> tuple[Path, Path, dict[str, int], dict[str, int]]:
    """``data/kurrent/k2-audit.html`` and its lines CSV: ``n`` of the reader's minted lines,
    seeded, equal per stratum, through the C2 sheet machinery — the crop, the minted
    text, the Bern reading and the v1 reading; verdicts download as the C2 CSV
    (``ref, stratum, verdict, note``). Labels in German beside English by default.

    With ``leibniz_hand_ids`` (the records in Leibniz's own hand) the draw is stratified
    by hand: half the lines from those records' rows, half from every other record's,
    each half equal per stratum under the same seed, the two mixed under the seed again;
    the lines CSV's ``group`` column (``leibniz_hand`` / ``other_hands``) tells them
    apart, the sheet itself does not. Returns the paths and the counts by stratum and
    by group."""
    own_ids = sorted({str(r) for r in leibniz_hand_ids}) if leibniz_hand_ids else []
    if own_ids:
        half = n // 2
        own = sample_lines(conn, half, seed=seed, reader=reader, record_ids=own_ids)
        rest = sample_lines(
            conn, n - half, seed=seed, reader=reader, record_ids=own_ids, exclude_records=True
        )
        for ln in own:
            ln.group = AUDIT_GROUPS["own"]
        for ln in rest:
            ln.group = AUDIT_GROUPS["other"]
        lines: list[AuditLine] = [*own, *rest]
        random.Random(seed).shuffle(lines)
    else:
        lines = sample_lines(conn, n, seed=seed, reader=reader)
    attach_images(conn, lines, Path(images_root))
    for ln in lines:
        r = readings.get(ln.ref)
        ln.alt_text = r.text if r is not None else "—"
        ln.alt_label = f"{reader}" + (f" ({r.conf:.2f})" if r and r.conf is not None else "")
    sheet = write_sheet(
        conn,
        lines,
        images_root=Path(images_root),
        out_dir=Path(out_dir),
        html_name="k2-audit.html",
        csv_name="k2-audit-lines.csv",
        seed=seed,
        title="K2 — German lines minted from the Kurrent reading · deutsche Zeilen, "
        "aus der Kurrent-Lesung zugeordnet",
        help_html=_audit_help(bilingual, split=bool(own_ids)),
        verdict_labels=AUDIT_VERDICT_LABELS if bilingual else None,
        attach=False,
    )
    by_group: dict[str, int] = {}
    for ln in lines:
        if ln.group:
            by_group[ln.group] = by_group.get(ln.group, 0) + 1
    return sheet.html_path, sheet.csv_path, sheet.by_stratum, by_group


def _audit_help(bilingual: bool, *, split: bool) -> str | None:
    """The sheet's instructions: bilingual or the C2 default, plus the hand-split note."""
    if not split:
        return AUDIT_HELP_HTML if bilingual else None
    if bilingual:
        head, sep, tail = AUDIT_HELP_HTML.rpartition("</div>")
        return head + AUDIT_SPLIT_NOTE + sep + tail
    head, sep, tail = DEFAULT_HELP_HTML.rpartition("</div>")
    return (
        (head + AUDIT_SPLIT_NOTE_EN + sep + tail)
        if sep
        else DEFAULT_HELP_HTML + AUDIT_SPLIT_NOTE_EN
    )


def _count(conn: sqlite3.Connection, where: str, params: Sequence = ()) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM gt_lines WHERE {where}", params).fetchone()[0])


def _in(ids: Sequence[str]) -> str:
    return "(" + (",".join("?" * len(ids)) if ids else "NULL") + ")"


def account_write(
    conn: sqlite3.Connection,
    decisions: Sequence[PieceDecision],
    pairs: Mapping[str, Sequence[GtPair]],
    *,
    reader: str = DEFAULT_READER,
) -> dict:
    """Where the dry run's pairs went, read from the store after the write (read-only).

    The dry run counted each piece's pairs; the factory's ownership rule keeps one row
    per line, so a line two won pieces both mint is written once, and a line another
    record's row holds at a higher alignment confidence stays with that record. This
    accounts for every pair of the won pieces: now a reader row, now a v1 row of
    another record, or a duplicate claim; and counts the store by record group.
    """
    like = f"%; reader {reader};%"
    reader_sql = "source LIKE ?"
    won = sorted(d.record_id for d in decisions if d.winner == "bern")
    german = sorted(d.record_id for d in decisions)
    own = sorted(d.record_id for d in decisions if d.leibniz_hand)
    rid = "CAST(record_id AS TEXT)"
    out: dict = {
        "reader": reader,
        "gt_lines": _count(conn, "1"),
        "distinct_refs": int(
            conn.execute("SELECT COUNT(DISTINCT line_image_ref) FROM gt_lines").fetchone()[0]
        ),
        "reader_rows": _count(conn, reader_sql, (like,)),
        "german_rows": _count(conn, f"{rid} IN {_in(german)}", german),
        "won_rows": _count(conn, f"{rid} IN {_in(won)}", won),
        "won_rows_reader": _count(conn, f"{rid} IN {_in(won)} AND {reader_sql}", (*won, like)),
        "won_rows_v1": _count(conn, f"{rid} IN {_in(won)} AND NOT ({reader_sql})", (*won, like)),
        "reader_rows_outside_won": _count(
            conn, f"{reader_sql} AND {rid} NOT IN {_in(won)}", (like, *won)
        ),
        "leibniz_hand_rows": _count(conn, f"{rid} IN {_in(own)}", own),
        "leibniz_hand_rows_reader": _count(
            conn, f"{rid} IN {_in(own)} AND {reader_sql}", (*own, like)
        ),
        "n_won_pieces": len(won),
        "n_german_records": len(german),
        "n_leibniz_hand_records": len(own),
    }
    out["reader_rows_by_stratum"] = {
        (r[0] or "unknown"): r[1]
        for r in conn.execute(
            f"SELECT stratum, COUNT(*) FROM gt_lines WHERE {reader_sql} GROUP BY stratum", (like,)
        )
    }
    out["german_rows_by_stratum"] = {
        (r[0] or "unknown"): r[1]
        for r in conn.execute(
            f"SELECT stratum, COUNT(*) FROM gt_lines WHERE {rid} IN {_in(german)} GROUP BY stratum",
            german,
        )
    }
    # the won pieces' pairs
    claims: dict[str, int] = {}
    best: dict[str, float] = {}
    n_pairs = 0
    for r in won:
        for pr in pairs.get(r, []):
            n_pairs += 1
            claims[pr.line_image_ref] = claims.get(pr.line_image_ref, 0) + 1
            best[pr.line_image_ref] = max(best.get(pr.line_image_ref, 0.0), pr.align_conf or 0.0)
    refs = sorted(claims)
    out["won_pairs"] = n_pairs
    out["won_pairs_distinct_refs"] = len(refs)
    out["refs_claimed_twice"] = sum(1 for c in claims.values() if c > 1)
    out["excess_claims"] = sum(c - 1 for c in claims.values() if c > 1)
    held_reader = held_v1 = held_v1_german = 0
    v1_margins: list[float] = []
    gset = set(german)
    for i in range(0, len(refs), 900):
        chunk = refs[i : i + 900]
        rows = conn.execute(
            f"SELECT line_image_ref, source, record_id, align_conf FROM gt_lines "
            f"WHERE line_image_ref IN {_in(chunk)}",
            chunk,
        ).fetchall()
        for ref, source, record_id, conf in rows:
            if f"; reader {reader};" in (source or ""):
                held_reader += 1
            else:
                held_v1 += 1
                if str(record_id) in gset:
                    held_v1_german += 1
                v1_margins.append(float(conf or 0.0) - best.get(ref, 0.0))
    out["refs_now_reader_row"] = held_reader
    out["refs_now_v1_row"] = held_v1
    out["refs_now_v1_row_german"] = held_v1_german
    out["refs_now_no_row"] = len(refs) - held_reader - held_v1
    out["v1_margin_mean"] = sum(v1_margins) / len(v1_margins) if v1_margins else None
    out["v1_ties"] = sum(1 for m in v1_margins if abs(m) < 1e-9)
    run = conn.execute(
        "SELECT run_id, started_at, finished_at, n_input, n_ok, n_failed, git_sha FROM runs "
        "WHERE stage = 'gt_factory' AND model = ? ORDER BY run_id DESC LIMIT 1",
        (f"retro-aligner+{reader}",),
    ).fetchone()
    out["run"] = (
        dict(
            zip(
                ("run_id", "started_at", "finished_at", "n_input", "n_ok", "n_failed", "git_sha"),
                run,
                strict=True,
            )
        )
        if run
        else None
    )
    return out


def render_write_report(
    acc: Mapping, stats: Mapping | None, *, generated: str | None = None
) -> str:
    """``reports/kurrent/k2-write.md``: the write's own counters and the store's account."""
    n = lambda x: "—" if x is None else f"{x:,}"  # noqa: E731
    A: list[str] = []
    A.append("# K2: the write, accounted")
    A.append("")
    A.append(
        f"The reader `{acc['reader']}`'s rows after `leibniz align kurrent-mint --write`, read "
        "from the store read-only, against the dry run's pairs. Generated "
        f"{generated or date.today().isoformat()}."
    )
    run = acc.get("run")
    if run:
        A.append("")
        A.append(
            f"The runs row: **run {run['run_id']}**, {run['started_at']} → {run['finished_at']}, "
            f"{n(run['n_input'])} pieces in, {n(run['n_ok'])} written, {n(run['n_failed'])} "
            f"failed, code `{(run['git_sha'] or '')[:7]}`."
        )
    if stats:
        A.append("")
        A.append("## The write's counters")
        A.append("")
        A.append(
            f"{n(stats.get('written_pieces'))} of {n(stats.get('pieces'))} pieces written "
            f"({n(stats.get('skipped_resume'))} skipped on resume); rows removed "
            f"**{n(stats.get('rows_removed'))}**, written **{n(stats.get('rows_written'))}**; the "
            f"ownership rule: {n(stats.get('rows_won'))} lines won from another record's row, "
            f"{n(stats.get('rows_lost'))} pairs lost to one; {stats.get('seconds', 0):.0f} s; "
            f"`gt_lines` after the write {n(stats.get('gt_lines_after'))} rows."
        )
    A.append("")
    A.append("## The store after the write")
    A.append("")
    A.append("| count | rows |")
    A.append("|---|---:|")
    A.append(f"| `gt_lines` | {n(acc['gt_lines'])} |")
    A.append(f"| distinct line references (one row per line) | {n(acc['distinct_refs'])} |")
    A.append(f"| rows whose source names the reader | {n(acc['reader_rows'])} |")
    A.append(
        f"| rows on the {n(acc['n_german_records'])} German records | {n(acc['german_rows'])} |"
    )
    A.append(
        f"| rows on the {n(acc['n_won_pieces'])} pieces the rule gave to the reader | "
        f"{n(acc['won_rows'])} (reader {n(acc['won_rows_reader'])}, v1 {n(acc['won_rows_v1'])}) |"
    )
    A.append(f"| reader rows outside those pieces | {n(acc['reader_rows_outside_won'])} |")
    A.append(
        f"| rows on the {n(acc['n_leibniz_hand_records'])} records in Leibniz's own hand | "
        f"{n(acc['leibniz_hand_rows'])} (reader {n(acc['leibniz_hand_rows_reader'])}) |"
    )
    A.append("")
    A.append("| stratum | reader rows | rows on the German records |")
    A.append("|---|---:|---:|")
    for st in STRATA:
        a, b = acc["reader_rows_by_stratum"].get(st), acc["german_rows_by_stratum"].get(st)
        if a or b:
            A.append(f"| {st} | {n(a or 0)} | {n(b or 0)} |")
    A.append("")
    A.append("## Where the won pieces' pairs went")
    A.append("")
    A.append(
        f"The dry run's **{n(acc['won_pairs'])} pairs** on the won pieces name "
        f"**{n(acc['won_pairs_distinct_refs'])} distinct lines**: "
        f"{n(acc['refs_claimed_twice'])} lines were claimed by two or more won pieces sharing a "
        f"page ({n(acc['excess_claims'])} claims beyond the first). Of the distinct lines, "
        f"**{n(acc['refs_now_reader_row'])}** are the reader's rows now; "
        f"**{n(acc['refs_now_v1_row'])}** stayed with a v1 row of another record "
        f"({n(acc['refs_now_v1_row_german'])} of them German pieces the rule left to v1) whose "
        f"alignment confidence was higher or tied"
        + (
            f" (mean margin {acc['v1_margin_mean']:+.3f}; {n(acc['v1_ties'])} ties, where the "
            "lower record id keeps the line)"
            if acc.get("v1_margin_mean") is not None
            else ""
        )
        + f"; {n(acc['refs_now_no_row'])} have no row. Every line is in `gt_lines` once."
    )
    A.append("")
    return "\n".join(A)


def write_write_report(
    acc: Mapping, stats: Mapping | None, *, reports_dir: Path | str = DEFAULT_REPORTS_DIR
) -> tuple[Path, Path]:
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    md, js = reports / "k2-write.md", reports / "k2-write.json"
    md.write_text(render_write_report(acc, stats), encoding="utf-8")
    js.write_text(
        json.dumps({"account": acc, "stats": stats}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return md, js


def readings_for(readings_dir: Path | str = DEFAULT_READINGS_DIR, reader: str = DEFAULT_READER):
    return load_readings(readings_dir, reader)


__all__ = [
    "AUDIT_GROUPS",
    "AUDIT_LINES",
    "AUDIT_VERDICT_LABELS",
    "DEFAULT_DECISIONS",
    "DEFAULT_SIDE_BY_SIDE",
    "RULE",
    "SEED",
    "SIDE_BY_SIDE_LINES",
    "DryRun",
    "PieceDecision",
    "Tally",
    "WriteStats",
    "account_write",
    "build_audit_sheet",
    "decide",
    "dry_run",
    "dry_run_piece",
    "load_decisions",
    "load_pairs",
    "load_run",
    "load_stats",
    "new_lines",
    "reader_text_for",
    "readings_for",
    "render_report",
    "render_write_report",
    "side_by_side",
    "stored_mint",
    "stored_refs",
    "summary",
    "tally_by",
    "pairs_path_for",
    "write_decisions",
    "write_mint",
    "write_outputs",
    "write_pairs",
    "write_write_report",
]
