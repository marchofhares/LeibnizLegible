"""How far the audit's failure patterns reach across the whole mint (C2b, Task 3).

The 200-line audit named the patterns (``audit_patterns.py``); this census asks,
for every open-bucket minted line, which of them it can carry, from what the
store already holds — no image, no model:

* **hyphen** — the HTR text of the line ends in a hyphen mark while the minted
  text ends in a letter: the word was split and the C2 mint dropped the mark
  (the re-mint with ``keep_hyphen`` restores exactly these).
* **math** — the minted text is dense in mathematical characters (the audit's
  cut); counted per volume, with Reihe III and the LH 35 pieces called out,
  since inline algebra in prose escapes the density and the note is not there.
* **addition** (a proxy, and said so) — the line's page shows the layout
  signature of heavy revision: an overlap or a short-line fraction above the
  cuts ``align/stratum.py`` uses for ``heavy_revision``. The audit found
  additions rendered inline *on such pages*; the proxy marks the pages, not
  the lines.
* **hand** — the catalogue record the line was minted from says, in its
  ``Textart``, that the piece itself is autograph (*eigenhändig*):
  ``Abf., eigh.``, ``Konz.; eigh.`` — the rule of
  :func:`leibniz.catalog.hands.hand_from_textart`, shared with the K1 census.
  An ``eigh.`` that qualifies a part only (``Abf.; eigh. Aufschr.``, a scribe's
  copy with an autograph address) does not count; before 2026-10 it did, and
  the shares "in Leibniz's own hand" included those copies. For a letter the
  author is the sender, so ``eigh`` alone counts a correspondent's hand on a
  letter Leibniz received; ``leibniz`` narrows it to the lines whose record
  names no sender (a writing) or names Leibniz himself as the sender
  (:func:`~leibniz.catalog.hands.is_leibniz_name`: not a namesake). Shares
  per stratum and per volume are of the lines whose record has a Textart.
* **Marginalien** — the line's work is in the Marginalien set (annotated
  printed books), where the body text is print, not Leibniz.
* **bracket** — the minted text carries an editorial bracket, the leak the
  audit saw on seven lines.

The store is opened read-only; every per-line flag goes to a JSONL file for C3
(``data/gt/flags.jsonl``, gitignored) and the counts to ``reports/gt-audit/``.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz.align.audit import split_ref
from leibniz.align.audit_patterns import (
    ends_in_letter,
    has_bracket,
    htr_ends_hyphenated,
    is_math_dense,
)
from leibniz.align.stratum import HEAVY_MIN_OVERLAP_FRAC, HEAVY_MIN_SHORT_FRAC
from leibniz.catalog.hands import hand_from_textart, is_leibniz_hand
from leibniz.catalog.shelfmarks import normalize_signature

FLAGS = ("hyphen", "math", "addition", "eigh", "leibniz", "marginalien", "bracket", "lh35")
HAND_FLAGS = ("eigh", "leibniz")  # shares of the lines whose record has a Textart
MARGINALIEN_SET = "LeibnizMarginalien"

# "AA VI,4 N.109 (§70-expired AA reading text; katalog k-109)"; the audit's test
# seed writes "N. 109" with a space.
_SOURCE_RE = re.compile(r"AA\s+(?P<vol>[IVX]+,\s*\S+?)\s+N\.\s*\S+.*?katalog\s+(?P<rec>[^)\s]+)")


def open_readonly(path: str | Path) -> sqlite3.Connection:
    """A ``mode=ro`` + ``query_only`` connection: the census can never write."""
    p = Path(path)
    if str(path) == ":memory:":
        raise ValueError("the reach census needs a store file")
    if not p.exists():
        raise FileNotFoundError(f"store not found: {path}")
    conn = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def parse_source(source: str) -> tuple[str | None, str | None]:
    """``(volume label, record id)`` from a factory source string."""
    m = _SOURCE_RE.search(source or "")
    if m is None:
        return None, None
    return " ".join(m.group("vol").split()).replace(", ", ","), m.group("rec")


def series_of(volume: str | None) -> str | None:
    return volume.split(",", 1)[0] if volume else None


def is_lh35(shelfmarks: Iterable[str]) -> bool:
    for s in shelfmarks:
        sig = normalize_signature(s)
        if sig.family == "LH" and sig.parts and sig.parts[0] == "35":
            return True
    return False


@dataclass(slots=True)
class ReachLine:
    ref: str
    stratum: str
    volume: str | None
    record_id: str | None
    work_id: str
    flags: list[str] = field(default_factory=list)
    eigh: bool | None = None  # None: no Textart on the record


@dataclass(slots=True)
class ReachCensus:
    lines: list[ReachLine]
    n_pages: int
    n_records: int
    n_records_with_textart: int
    n_skipped: int = 0  # rows whose line_image_ref is not "{page_id}:{line_seq:03d}"

    @property
    def n(self) -> int:
        return len(self.lines)


def _group(lines: Sequence[ReachLine], key: str) -> dict[str, list[ReachLine]]:
    out: dict[str, list[ReachLine]] = {}
    for ln in lines:
        k = getattr(ln, key) or "unknown"
        out.setdefault(k, []).append(ln)
    return out


def census(conn: sqlite3.Connection) -> ReachCensus:
    """Flag every open-bucket minted line (see the module docstring)."""
    rows = conn.execute(
        "SELECT line_image_ref, text, stratum, source FROM gt_lines "
        "WHERE license_bucket = 'open' ORDER BY id"
    ).fetchall()
    htr_cache: dict[str, dict[int, str]] = {}
    page_flags: dict[str, bool] = {}
    work_info: dict[str, tuple[bool, bool]] = {}
    textart: dict[str, tuple[str | None, str | None]] = {}  # record -> (Textart, sender)
    out: list[ReachLine] = []
    skipped = 0
    for r in rows:
        ref, text, stratum, source = (
            r["line_image_ref"],
            r["text"] or "",
            r["stratum"] or "unknown",
            r["source"] or "",
        )
        try:
            page_id, seq = split_ref(ref)
        except ValueError:  # an older reference form (the B2 prototype's "#xywh")
            skipped += 1
            continue
        work_id = page_id.rpartition(":")[0]
        volume, rec = parse_source(source)
        if page_id not in htr_cache:
            htr_cache[page_id] = _htr_texts(conn, page_id)
            page_flags[page_id] = _heavy_layout(conn, page_id)
        if work_id not in work_info:
            work_info[work_id] = _work_flags(conn, work_id)
        if rec is not None and rec not in textart:
            textart[rec] = _textart(conn, rec)
        htr = htr_cache[page_id].get(seq)
        flags: list[str] = []
        if htr_ends_hyphenated(htr) and ends_in_letter(text):
            flags.append("hyphen")
        if is_math_dense(text):
            flags.append("math")
        if page_flags[page_id]:
            flags.append("addition")
        ta, sender = textart.get(rec, (None, None)) if rec is not None else (None, None)
        hand = hand_from_textart(ta) if ta else None
        eigh = None if not ta else hand == "own"
        if eigh:
            flags.append("eigh")
            if is_leibniz_hand(hand, sender):
                flags.append("leibniz")
        marg, lh35 = work_info[work_id]
        if marg:
            flags.append("marginalien")
        if lh35:
            flags.append("lh35")
        if has_bracket(text):
            flags.append("bracket")
        out.append(ReachLine(ref, stratum, volume, rec, work_id, flags, eigh))
    return ReachCensus(
        lines=out,
        n_pages=len(htr_cache),
        n_records=len(textart),
        n_records_with_textart=sum(1 for v in textart.values() if v[0]),
        n_skipped=skipped,
    )


def _htr_texts(conn: sqlite3.Connection, page_id: str) -> dict[int, str]:
    """``line_seq -> recognised text`` for a page: the latest run that carries text
    (the row ``audit.line_geometry`` takes)."""
    out: dict[int, tuple[int, str]] = {}
    for row in conn.execute(
        "SELECT line_seq, run_id, text FROM lines WHERE page_id = ? AND text IS NOT NULL",
        (page_id,),
    ):
        seq, run = row["line_seq"], row["run_id"] or 0
        if seq not in out or run > out[seq][0]:
            out[seq] = (run, row["text"])
    return {k: v[1] for k, v in out.items()}


def _heavy_layout(conn: sqlite3.Connection, page_id: str) -> bool:
    row = conn.execute(
        "SELECT n_lines, n_overlaps, n_short_lines FROM page_stats WHERE page_id = ?", (page_id,)
    ).fetchone()
    if row is None or not row["n_lines"]:
        return False
    n = row["n_lines"]
    return (row["n_overlaps"] or 0) / n >= HEAVY_MIN_OVERLAP_FRAC or (
        row["n_short_lines"] or 0
    ) / n >= HEAVY_MIN_SHORT_FRAC


def _work_flags(conn: sqlite3.Connection, work_id: str) -> tuple[bool, bool]:
    row = conn.execute(
        "SELECT set_name, shelfmarks FROM works WHERE gwlb_object_id = ?", (work_id,)
    ).fetchone()
    if row is None:
        return False, False
    shelfmarks = json.loads(row["shelfmarks"]) if row["shelfmarks"] else []
    return row["set_name"] == MARGINALIEN_SET, is_lh35(shelfmarks)


def _textart(conn: sqlite3.Connection, record_id: str) -> tuple[str | None, str | None]:
    """The record's ``(Textart, Absender)``; ``None`` for a missing field."""
    row = conn.execute(
        "SELECT metadata FROM katalog_records WHERE record_id = ?", (record_id,)
    ).fetchone()
    if row is None or not row["metadata"]:
        return None, None
    meta = json.loads(row["metadata"])
    ta, sender = meta.get("textart"), meta.get("absender")
    return (str(ta) if ta else None), (str(sender) if sender else None)


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #


def _table(groups: dict[str, list[ReachLine]], *, order: Sequence[str] | None = None) -> list[dict]:
    keys = [k for k in (order or []) if k in groups] + sorted(
        k for k in groups if k not in (order or [])
    )
    rows = []
    for k in keys:
        ls = groups[k]
        n = len(ls)
        with_ta = sum(1 for ln in ls if ln.eigh is not None)
        row = {"key": k, "n": n, "with_textart": with_ta}
        for f in FLAGS:
            c = sum(1 for ln in ls if f in ln.flags)
            row[f] = c
            denom = with_ta if f in HAND_FLAGS else n
            row[f + "_share"] = (c / denom) if denom else None
        rows.append(row)
    return rows


def summary(c: ReachCensus, *, strata: Sequence[str]) -> dict:
    all_rows = _table({"all": list(c.lines)})
    return {
        "n_lines": c.n,
        "n_pages": c.n_pages,
        "n_records": c.n_records,
        "n_records_with_textart": c.n_records_with_textart,
        "n_skipped": c.n_skipped,
        "flags": FLAGS,
        "all": all_rows[0] if all_rows else {},
        "by_stratum": _table(_group(c.lines, "stratum"), order=strata),
        "by_volume": _table(_group(c.lines, "volume")),
    }


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.1f} %"


def render(c: ReachCensus, *, strata: Sequence[str], flags_path: Path | None) -> str:
    s = summary(c, strata=strata)
    out: list[str] = []
    A = out.append
    A("# Reach of the audit's patterns across the mint")
    A("")
    A(
        f"{c.n:,} open-bucket minted lines on {c.n_pages:,} pages, from {c.n_records:,} "
        f"catalogue records ({c.n_records_with_textart:,} with a Textart). Read-only over the "
        f"store; per-line flags in `{flags_path}`."
        if flags_path
        else f"{c.n:,} open-bucket minted lines on {c.n_pages:,} pages."
    )
    if c.n_skipped:
        A("")
        A(
            f"{c.n_skipped:,} open-bucket rows carry a reference that is not "
            f"`{{page_id}}:{{line_seq:03d}}` and were skipped."
        )
    A("")
    A(
        "*hyphen*: HTR line ends in a hyphen mark, minted text in a letter (what the re-mint "
        "with `keep_hyphen` changes). *math*: the audit's density cut (misses inline algebra in "
        "prose). *addition*: a proxy — the line's page has an overlap or short-line fraction at "
        "the heavy-revision cut; it marks pages where inline additions were seen, not the "
        "lines. *eigh*: the record's Textart says the piece is in its author's own hand — on a "
        "letter Leibniz received, the correspondent's. *leibniz*: of those, the records that name "
        "no sender (a writing) or Leibniz as the sender (his draft or letter): Leibniz's own "
        "hand. Both shares are of the lines whose record has a Textart. *marginalien*: the work "
        "is an annotated printed book. "
        "*bracket*: an editorial bracket in the minted text. *lh35*: the work's shelfmark is "
        "LH 35."
    )
    A("")
    head = "| group | lines | " + " | ".join(FLAGS) + " |"
    sep = "|---|---:|" + "---:|" * len(FLAGS)

    def rows(table: list[dict], label: str) -> None:
        A(f"## By {label}")
        A("")
        A(head)
        A(sep)
        for r in table:
            cells = [f"{r[f]:,} ({_pct(r[f + '_share'])})" for f in FLAGS]
            A(f"| {r['key']} | {r['n']:,} | " + " | ".join(cells) + " |")
        A("")

    rows([{**s["all"], "key": "**all**"}], "all lines")
    rows(s["by_stratum"], "stratum")
    rows(s["by_volume"], "volume (Reihe,Band)")
    A(
        "Reihe III (mathematical, scientific and technical correspondence) and the LH 35 pieces "
        "are where the math flag should concentrate; a low share there says the density cut "
        "under-counts, not that the volumes have no formulae."
    )
    return "\n".join(out) + "\n"


def write_flags(c: ReachCensus, path: Path) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with Path(path).open("w", encoding="utf-8") as fh:
        for ln in c.lines:
            rec = {
                "ref": ln.ref,
                "stratum": ln.stratum,
                "volume": ln.volume,
                "record": ln.record_id,
                "flags": ln.flags,
            }
            if ln.eigh is not None:
                rec["eigh"] = ln.eigh
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


__all__ = [
    "FLAGS",
    "ReachCensus",
    "ReachLine",
    "census",
    "is_lh35",
    "open_readonly",
    "parse_source",
    "render",
    "series_of",
    "summary",
    "write_flags",
]
