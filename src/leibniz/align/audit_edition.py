"""A judge's table with a transcription column: converted, scored under the fold,
written into the store (K3b-prep, 2026-11-17).

The Leibniz-Edition's Arbeitsstelle judged K2's 200-line sheet and returned it
(2026-11-06) with the sheet's columns and one of its own, the correct text of
the whole line. Its convention is stricter than the sheet's: *correct* only
where the minted text is completely right; where anything was wrong, **no
verdict** and the line's text in ``transcription``; *boundary* for a slip at an
edge (usually with the text too); *wrong* where crop and text do not match;
*unreadable*; ``note`` for comments only. Three steps turn that table into what
the rest of the project reads:

* :func:`convert` (``leibniz align audit-convert``) — the table
  (``ref, stratum, verdict, transcription, note``) becomes the C2 verdict CSV
  (``ref, stratum, verdict, note``) that :func:`leibniz.align.audit.read_verdicts`
  takes: a verdict given stays, a transcription without a verdict counts as
  *wrong* (its note says so), a row with neither stays unjudged; and a
  corrections file (``ref, stratum, group, gt_text, transcription,
  folded_similarity, note``) for every row with a transcription.
* :func:`fold_scores` (``leibniz align audit-score --corrections``) — the
  precision the strict verdicts hide. A line the judge re-wrote because of an
  accent, a capital or a comma is *wrong* under the convention above and right
  under the aligner's fold, so each corrected line is measured: the folded
  similarity between the minted text and the judge's text, against the
  factory's acceptance threshold for the line's stratum
  (:data:`leibniz.align.factory.STRATUM_THRESHOLDS`). At or above it the minted
  text is as close to the line as the factory asks of a reading, and the line
  counts as right under the fold. Three precisions, each with a Wilson
  interval: *strict* (correct as written), *usable* (boundary counted), *under
  the fold* (correct or corrected at or above the threshold); a fourth column
  counts the boundary lines on top of the third.
* :func:`plan_apply` / :func:`apply_plan` (``leibniz align audit-apply``) — the
  verified lines into ``gt_lines``: a confirmed line keeps its text and gains
  ``; verified <by> <date>`` in its source; a corrected line gets the judge's
  text, the mark, and ``channel edition-k2-audit`` in place of the channel it
  had, since the text is now the judge's own (CC BY 4.0 by the Edition's
  answer of 2026-11-16) whatever copy the minted text was read through. The
  reader mark and ``katalog <id>`` stay, the latter last, so every parser of
  the source string still reads the row. A dry run unless told to write; the
  write is one transaction with a ``runs`` row and changes nothing a second
  time.

Nothing here needs a model, an image or the network. The judge's text is the
judge's: these functions carry it, they never alter it beyond making it one
line (runs of whitespace become one space).
"""

from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db, legal
from leibniz.align import dp
from leibniz.align.align import DEFAULT_THRESHOLD
from leibniz.align.audit import STRATA, VERDICTS, wilson
from leibniz.align.factory import STRATUM_THRESHOLDS, with_write_lock
from leibniz.align.normalize import normalize
from leibniz.align.pairs import channels_from_source, collapse_whitespace

CONVERTED_PHRASE = (
    "converted: a transcription without a verdict counts as wrong; "
    "the Edition's text is in the corrections file"
)
EDITION_COLUMNS = ("ref", "stratum", "verdict", "transcription", "note")
CORRECTION_COLUMNS = (
    "ref",
    "stratum",
    "group",
    "gt_text",
    "transcription",
    "folded_similarity",
    "note",
)
# The sheet's bilingual labels and their German halves, should a judge's table
# carry them in place of the CSV's values.
_VERDICT_ALIASES = {
    "correct": "correct",
    "richtig": "correct",
    "boundary": "boundary",
    "grenze": "boundary",
    "wrong": "wrong",
    "falsch": "wrong",
    "unreadable": "unreadable",
    "unlesbar": "unreadable",
}
UNGROUPED = "ungrouped"


def parse_verdict(raw: str | None) -> str:
    """A table cell as one of the four verdicts, or ``""`` for an empty cell.

    Reads the CSV's values, the sheet's labels (``correct · richtig``) and their
    German halves; anything else raises ``ValueError`` — a verdict the scorer
    would silently drop must stop the conversion instead."""
    cell = " ".join((raw or "").split()).lower()
    if not cell:
        return ""
    for part in (cell, *(p.strip() for p in cell.split("·"))):
        if part in _VERDICT_ALIASES:
            return _VERDICT_ALIASES[part]
    raise ValueError(f"not a verdict: {raw!r}")


def folded_similarity(minted: str, corrected: str) -> float:
    """Similarity of two readings of one line under the aligner's fold (accents,
    case, u/v, i/j and punctuation folded away), as the audit's second witness
    computes it: ``0.0`` where either side folds to nothing."""
    g, c = normalize(minted or ""), normalize(corrected or "")
    return dp.similarity(g, c) if g and c else 0.0


def read_table(path: Path | str) -> list[dict[str, str]]:
    """The judge's table as rows; it must carry ``ref``, ``verdict`` and
    ``transcription`` (``stratum`` and ``note`` may be absent)."""
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = {"ref", "verdict", "transcription"} - set(reader.fieldnames or ())
        if missing:
            raise ValueError(
                f"{path}: the table needs the columns ref, verdict and transcription "
                f"(missing: {', '.join(sorted(missing))})"
            )
        return [dict(r) for r in reader]


def read_lines(path: Path | str) -> dict[str, dict[str, str]]:
    """The sheet's lines CSV by ref."""
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        return {r["ref"]: r for r in csv.DictReader(fh)}


# --------------------------------------------------------------------------- #
# Task 1: the conversion
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ConvertedRow:
    """One row of the judge's table, with what the two output files carry."""

    ref: str
    stratum: str
    group: str
    verdict_in: str  # the judge's verdict, or ""
    verdict: str  # the C2 verdict: the judge's, "wrong" for a bare transcription, or ""
    transcription: str  # one line of text, or ""
    note_in: str
    note: str  # the note the C2 CSV carries
    gt_text: str

    @property
    def klass(self) -> str:
        """The convention's case this row is (the tally's key)."""
        if not self.verdict_in:
            return "transcription, no verdict (→ wrong)" if self.transcription else "blank"
        return self.verdict_in + (" + transcription" if self.transcription else "")

    @property
    def similarity(self) -> float | None:
        if not self.transcription:
            return None
        return folded_similarity(self.gt_text, self.transcription)


CLASS_ORDER = (
    "correct",
    "correct + transcription",
    "boundary",
    "boundary + transcription",
    "transcription, no verdict (→ wrong)",
    "wrong",
    "wrong + transcription",
    "unreadable",
    "unreadable + transcription",
    "blank",
)


@dataclass(slots=True)
class Conversion:
    rows: list[ConvertedRow]
    n_lines: int  # lines on the sheet
    not_in_table: list[str] = field(default_factory=list)  # sheet lines the table lacks
    stratum_differs: list[str] = field(default_factory=list)  # the sheet's stratum was kept

    @property
    def corrections(self) -> list[ConvertedRow]:
        return [r for r in self.rows if r.transcription]

    def tally(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            out[r.klass] = out.get(r.klass, 0) + 1
        return {k: out[k] for k in CLASS_ORDER if k in out}

    def tally_by_group(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in self.rows:
            g = out.setdefault(r.group or UNGROUPED, {})
            g[r.klass] = g.get(r.klass, 0) + 1
        return {name: {k: g[k] for k in CLASS_ORDER if k in g} for name, g in sorted(out.items())}


def convert(
    table: Sequence[Mapping[str, str]], lines: Mapping[str, Mapping[str, str]]
) -> Conversion:
    """The judge's table against the sheet's lines CSV.

    Raises ``ValueError`` where the two do not belong together (a ref the sheet
    does not have, a ref judged twice) or a verdict cell is not a verdict; the
    message names every such row."""
    problems: list[str] = []
    seen: set[str] = set()
    rows: list[ConvertedRow] = []
    differs: list[str] = []
    for k, r in enumerate(table, start=2):  # the CSV's line number, header = 1
        ref = (r.get("ref") or "").strip()
        if not ref:
            if any((v or "").strip() for v in r.values()):
                problems.append(f"line {k}: no ref")
            continue
        if ref in seen:
            problems.append(f"line {k}: {ref} is in the table twice")
            continue
        seen.add(ref)
        ln = lines.get(ref)
        if ln is None:
            problems.append(f"line {k}: {ref} is not on the sheet")
            continue
        try:
            verdict_in = parse_verdict(r.get("verdict"))
        except ValueError as exc:
            problems.append(f"line {k}: {ref}: {exc}")
            continue
        transcription = collapse_whitespace(r.get("transcription") or "")
        note_in = (r.get("note") or "").strip()
        sheet_stratum = (ln.get("stratum") or "").strip()
        stratum = sheet_stratum or (r.get("stratum") or "").strip() or "unknown"
        if sheet_stratum and (r.get("stratum") or "").strip() not in ("", sheet_stratum):
            differs.append(ref)
        verdict, note = verdict_in, note_in
        if not verdict_in and transcription:
            verdict = "wrong"
            note = f"{note_in}; {CONVERTED_PHRASE}" if note_in else CONVERTED_PHRASE
        rows.append(
            ConvertedRow(
                ref=ref,
                stratum=stratum,
                group=(ln.get("group") or "").strip(),
                verdict_in=verdict_in,
                verdict=verdict,
                transcription=transcription,
                note_in=note_in,
                note=note,
                gt_text=ln.get("gt_text") or "",
            )
        )
    if problems:
        raise ValueError("the table and the sheet do not fit:\n  " + "\n  ".join(problems))
    return Conversion(
        rows=rows,
        n_lines=len(lines),
        not_in_table=[ref for ref in lines if ref not in seen],
        stratum_differs=differs,
    )


def write_verdicts(path: Path | str, conv: Conversion) -> Path:
    """The C2 verdict CSV (``ref, stratum, verdict, note``), in the table's order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "verdict", "note"])
        for r in conv.rows:
            w.writerow([r.ref, r.stratum, r.verdict, r.note])
    return path


def write_corrections(path: Path | str, conv: Conversion) -> Path:
    """The corrections file: every row with a transcription, the minted text beside it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(CORRECTION_COLUMNS)
        for r in conv.corrections:
            w.writerow(
                [
                    r.ref,
                    r.stratum,
                    r.group,
                    r.gt_text,
                    r.transcription,
                    f"{r.similarity:.3f}",
                    r.note_in,
                ]
            )
    return path


def read_corrections(path: Path | str) -> dict[str, str]:
    """``ref → the judge's text of the whole line`` from a corrections file (rows
    without a transcription are left out)."""
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not {"ref", "transcription"} <= set(reader.fieldnames or ()):
            raise ValueError(f"{path}: a corrections file needs the columns ref and transcription")
        out: dict[str, str] = {}
        for r in reader:
            text = collapse_whitespace(r.get("transcription") or "")
            if text:
                out[(r.get("ref") or "").strip()] = text
        return out


# --------------------------------------------------------------------------- #
# Task 2: precision under the fold
# --------------------------------------------------------------------------- #


def threshold_for(stratum: str, thresholds: Mapping[str, float] | None = None) -> float:
    """The factory's acceptance threshold for a stratum (its default for an unknown one)."""
    return (thresholds or STRATUM_THRESHOLDS).get(stratum, DEFAULT_THRESHOLD)


@dataclass(slots=True)
class FoldScore:
    """Judged lines of one stratum or group, by what the judge said and the fold measured."""

    name: str
    n_judged: int = 0
    correct: int = 0  # correct as written
    boundary: int = 0
    corrected_ok: int = 0  # re-written by the judge, folded similarity ≥ the threshold
    corrected_below: int = 0  # re-written, below it
    wrong: int = 0  # wrong, no text given
    unreadable: int = 0

    @property
    def n_scored(self) -> int:
        """Judged lines the judge could read (``unreadable`` is left out, as in C2)."""
        return self.n_judged - self.unreadable

    def _rate(self, k: int) -> float | None:
        return k / self.n_scored if self.n_scored else None

    def _ci(self, k: int) -> tuple[float, float] | None:
        return wilson(k, self.n_scored) if self.n_scored else None

    @property
    def strict(self) -> float | None:
        return self._rate(self.correct)

    @property
    def usable(self) -> float | None:
        return self._rate(self.correct + self.boundary)

    @property
    def fold(self) -> float | None:
        return self._rate(self.correct + self.corrected_ok)

    @property
    def fold_usable(self) -> float | None:
        return self._rate(self.correct + self.corrected_ok + self.boundary)

    @property
    def strict_ci(self) -> tuple[float, float] | None:
        return self._ci(self.correct)

    @property
    def usable_ci(self) -> tuple[float, float] | None:
        return self._ci(self.correct + self.boundary)

    @property
    def fold_ci(self) -> tuple[float, float] | None:
        return self._ci(self.correct + self.corrected_ok)

    @property
    def fold_usable_ci(self) -> tuple[float, float] | None:
        return self._ci(self.correct + self.corrected_ok + self.boundary)

    def as_dict(self) -> dict:
        def ci(x: tuple[float, float] | None) -> list[float] | None:
            return list(x) if x else None

        return {
            "judged": self.n_judged,
            "scored": self.n_scored,
            "correct": self.correct,
            "boundary": self.boundary,
            "corrected_at_or_above_threshold": self.corrected_ok,
            "corrected_below_threshold": self.corrected_below,
            "wrong": self.wrong,
            "unreadable": self.unreadable,
            "strict": self.strict,
            "strict_interval": ci(self.strict_ci),
            "usable": self.usable,
            "usable_interval": ci(self.usable_ci),
            "under_the_fold": self.fold,
            "under_the_fold_interval": ci(self.fold_ci),
            "under_the_fold_usable": self.fold_usable,
            "under_the_fold_usable_interval": ci(self.fold_usable_ci),
        }


@dataclass(slots=True)
class FoldRow:
    """One corrected line, measured."""

    ref: str
    stratum: str
    group: str
    verdict: str
    similarity: float
    threshold: float

    @property
    def ok(self) -> bool:
        return self.similarity >= self.threshold


@dataclass(slots=True)
class FoldReport:
    by_stratum: dict[str, FoldScore]
    by_group: dict[str, FoldScore]
    pooled: FoldScore
    thresholds: dict[str, float]
    corrected: list[FoldRow]  # every line with a judge's text, whatever its verdict
    not_on_sheet: list[str] = field(default_factory=list)  # corrections for refs off the sheet


def fold_scores(
    verdict_rows: Sequence[Mapping[str, str]],
    lines: Mapping[str, Mapping[str, str]],
    corrections: Mapping[str, str],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> FoldReport:
    """Tally the judged lines by stratum and by the lines CSV's group.

    A *correct* or *boundary* verdict keeps its class, with or without a text
    beside it; a *wrong* with the judge's text is a corrected line and falls on
    one side of its stratum's threshold; a *wrong* without one stays wrong."""
    th = dict(thresholds or STRATUM_THRESHOLDS)
    by_stratum: dict[str, FoldScore] = {}
    by_group: dict[str, FoldScore] = {}
    pooled = FoldScore("all")
    measured: list[FoldRow] = []
    for r in verdict_rows:
        ref = (r.get("ref") or "").strip()
        verdict = (r.get("verdict") or "").strip().lower()
        ln = lines.get(ref)
        if verdict not in VERDICTS or ln is None:
            continue
        stratum = ((r.get("stratum") or ln.get("stratum") or "unknown").strip()) or "unknown"
        group = (ln.get("group") or "").strip()
        text = corrections.get(ref)
        field_name = verdict
        if text is not None:
            row = FoldRow(
                ref=ref,
                stratum=stratum,
                group=group,
                verdict=verdict,
                similarity=folded_similarity(ln.get("gt_text") or "", text),
                threshold=threshold_for(stratum, th),
            )
            measured.append(row)
            if verdict == "wrong":
                field_name = "corrected_ok" if row.ok else "corrected_below"
        targets = [pooled, by_stratum.setdefault(stratum, FoldScore(stratum))]
        if group:
            targets.append(by_group.setdefault(group, FoldScore(group)))
        for s in targets:
            s.n_judged += 1
            setattr(s, field_name, getattr(s, field_name) + 1)
    order = [s for s in STRATA if s in by_stratum] + sorted(set(by_stratum) - set(STRATA))
    return FoldReport(
        by_stratum={s: by_stratum[s] for s in order},
        by_group=dict(sorted(by_group.items())),
        pooled=pooled,
        thresholds=th,
        corrected=measured,
        not_on_sheet=sorted(ref for ref in corrections if ref not in lines),
    )


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.1f} %"


def _ci(x: tuple[float, float] | None) -> str:
    return "—" if x is None else f"{100 * x[0]:.0f}–{100 * x[1]:.0f} %"


def _fold_row(label: str, s: FoldScore) -> str:
    return (
        f"| {label} | {s.n_judged} | {s.correct} | {s.boundary} | {s.corrected_ok} | "
        f"{s.corrected_below} | {s.wrong} | {s.unreadable} | {_pct(s.strict)} ({_ci(s.strict_ci)}) "
        f"| {_pct(s.usable)} ({_ci(s.usable_ci)}) | {_pct(s.fold)} ({_ci(s.fold_ci)}) | "
        f"{_pct(s.fold_usable)} ({_ci(s.fold_usable_ci)}) |"
    )


_FOLD_HEAD = (
    "| {key} | judged | correct as written | boundary | corrected, ≥ threshold | "
    "corrected, below | wrong | unreadable | strict | usable | under the fold | "
    "under the fold, boundary counted |"
)
_FOLD_SEP = "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|"


def render_fold(rep: FoldReport) -> list[str]:
    """The report's section "Under the fold" (markdown lines)."""
    out: list[str] = []
    A = out.append
    A("## Under the fold")
    A("")
    th = ", ".join(f"{k} {v:.2f}" for k, v in rep.thresholds.items())
    n_corr = rep.pooled.corrected_ok + rep.pooled.corrected_below
    A(
        f"The judge wrote out the line's text wherever the minted text was not completely right "
        f"and gave such a line no verdict; the conversion counts it as *wrong*. {n_corr} of the "
        f"judged lines are of that kind. For each, the folded similarity between the minted text "
        f"and the judge's text was computed (the aligner's fold: accents, case, u/v, i/j and "
        f"punctuation folded away) and set against the factory's acceptance threshold for the "
        f"line's stratum ({th}). At or above it the minted text is as close to the line as the "
        f"factory asks of a reading, and the line counts as right under the fold "
        f"({rep.pooled.corrected_ok} lines); below it, it does not "
        f"({rep.pooled.corrected_below})."
    )
    A("")
    A(_FOLD_HEAD.format(key="stratum"))
    A(_FOLD_SEP)
    for name, s in rep.by_stratum.items():
        A(_fold_row(name, s))
    A(_fold_row("**all**", rep.pooled))
    if rep.by_group:
        A("")
        A(_FOLD_HEAD.format(key="group"))
        A(_FOLD_SEP)
        for name, s in rep.by_group.items():
            A(_fold_row(name, s))
    A("")
    A(
        "*strict* = correct as written ÷ scored; *usable* = (correct + boundary) ÷ scored; "
        "*under the fold* = (correct + corrected at or above the threshold) ÷ scored; the last "
        "column adds the boundary lines to that. Scored = judged − unreadable. Intervals are "
        "Wilson 95 %. A *boundary* line stays a boundary line whatever its text measures, and a "
        "*wrong* without a text stays wrong. The rows are pooled, not weighted: the draw was "
        "equal per stratum within each group."
    )
    with_text = [r for r in rep.corrected if r.verdict == "boundary"]
    if with_text:
        ok = sum(1 for r in with_text if r.ok)
        A("")
        A(
            f"Of the boundary lines, {len(with_text)} carry the judge's text; {ok} of them fold "
            f"to the minted text at or above their stratum's threshold."
        )
    if rep.not_on_sheet:
        A("")
        A(
            f"{len(rep.not_on_sheet)} corrections name a line that is not on the sheet and were "
            f"not counted: " + ", ".join(f"`{r}`" for r in rep.not_on_sheet[:10])
        )
    return out


def fold_summary(rep: FoldReport) -> dict:
    """The section in numbers, for the summary JSON."""
    return {
        "thresholds": rep.thresholds,
        "pooled": rep.pooled.as_dict(),
        "by_stratum": {k: v.as_dict() for k, v in rep.by_stratum.items()},
        "by_group": {k: v.as_dict() for k, v in rep.by_group.items()},
    }


# --------------------------------------------------------------------------- #
# Task 3: the verified lines into the store
# --------------------------------------------------------------------------- #

VERIFIED_BY = "leibniz-edition"
VERIFIED_ON = "2026-11-06"
AUDIT_CHANNEL = "edition-k2-audit"
RUN_STAGE = "gt_audit"
RUN_MODEL = "leibniz-edition-k2-audit"
DEFAULT_VERIFIED_CSV = Path("reports/kurrent/k3b-verified.csv")
VERIFIED_COLUMNS = ("ref", "group", "stratum", "verdict", "text", "verified_by", "licence")
NOT_RELEASED = "not released"

_SOURCE_RE = re.compile(r"^(.*)\((.*)\)\s*$", re.DOTALL)
_VERIFIED_RE = re.compile(r";\s*verified\s+([^;)]+)")


def verified_from_source(source: str | None) -> str | None:
    """Who verified a row and when (``"leibniz-edition 2026-11-06"``), or ``None``."""
    m = _VERIFIED_RE.search(source or "")
    return m.group(1).strip() if m else None


def verified_source(source: str, *, by: str, on: str, channel: str | None = None) -> str:
    """A row's source with the verification written in — idempotent.

    ``"AA IV,3 N.41 (§70-expired AA reading text; channel ia; reader R; katalog 7)"``
    becomes ``"… (§70-expired AA reading text; channel ia; reader R; verified
    leibniz-edition 2026-11-06; katalog 7)"``: the mark stands before ``katalog``,
    which stays last. With ``channel`` the channel the row had is replaced by it
    (a corrected line: the text is no longer the copy's); a row that named none
    gains it before the reader. A source without the factory's parenthesis gets
    one."""
    m = _SOURCE_RE.match(source or "")
    head, inner = (m.group(1).rstrip(), m.group(2)) if m else ((source or "").strip(), "")
    parts = [p.strip() for p in inner.split(";") if p.strip()]
    parts = [p for p in parts if not p.startswith("verified ")]

    def first(prefixes: tuple[str, ...]) -> int:
        return next((i for i, p in enumerate(parts) if p.startswith(prefixes)), len(parts))

    if channel:
        at = first(("channel ",))
        if at < len(parts):
            parts[at] = f"channel {channel}"
        else:
            parts.insert(first(("reader ", "katalog ")), f"channel {channel}")
    parts.insert(first(("katalog ",)), f"verified {by} {on}")
    return f"{head} ({'; '.join(parts)})" if head else f"({'; '.join(parts)})"


@dataclass(slots=True)
class ApplyRow:
    """One verified line: what the store holds and what it would hold."""

    ref: str
    group: str
    stratum: str
    verdict: str  # correct | boundary | corrected
    gt_id: int
    old_text: str
    text: str
    old_source: str
    source: str
    license_bucket: str
    drifted: bool = False  # the stored text is neither the sheet's nor the judge's

    @property
    def corrected(self) -> bool:
        return self.verdict != "correct"

    @property
    def text_changes(self) -> bool:
        return self.text != self.old_text

    @property
    def changed(self) -> bool:
        return self.text_changes or self.source != self.old_source

    @property
    def old_channel(self) -> str:
        return "+".join(channels_from_source(self.old_source)) or "(not recorded)"

    @property
    def channel(self) -> str:
        return "+".join(channels_from_source(self.source)) or "(not recorded)"

    @property
    def old_deposit(self) -> str | None:
        return legal.deposit_for(channels_from_source(self.old_source), self.license_bucket)

    @property
    def deposit(self) -> str | None:
        return legal.deposit_for(channels_from_source(self.source), self.license_bucket)

    @property
    def licence(self) -> str:
        return legal.deposit_licence(self.deposit) if self.deposit else NOT_RELEASED


SKIP_REASONS = (
    "unjudged",
    "wrong, no text given",
    "unreadable",
    "boundary without a transcription",
    "no row in gt_lines",
    "more than one row in gt_lines",
    "the stored text is not the sheet's",
)


@dataclass(slots=True)
class ApplyPlan:
    rows: list[ApplyRow]
    skipped: dict[str, list[str]]  # reason → refs
    by: str
    on: str
    channel: str
    n_table: int = 0

    @property
    def changes(self) -> list[ApplyRow]:
        return [r for r in self.rows if r.changed]

    def by_class(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            out[r.verdict] = out.get(r.verdict, 0) + 1
        return {k: out[k] for k in ("correct", "boundary", "corrected") if k in out}

    def channel_changes(self) -> dict[tuple[str, str], int]:
        out: dict[tuple[str, str], int] = {}
        for r in self.rows:
            if r.old_channel != r.channel:
                key = (r.old_channel, r.channel)
                out[key] = out.get(key, 0) + 1
        return dict(sorted(out.items()))

    def deposits(self) -> dict[tuple[str, str], int]:
        """``(deposit today, deposit after) → rows`` over the verified lines."""
        out: dict[tuple[str, str], int] = {}
        for r in self.rows:
            key = (r.old_deposit or "none", r.deposit or "none")
            out[key] = out.get(key, 0) + 1
        return dict(sorted(out.items()))

    def summary(self) -> dict:
        return {
            "verified_by": f"{self.by} {self.on}",
            "channel": self.channel,
            "table_rows": self.n_table,
            "verified": len(self.rows),
            "by_class": self.by_class(),
            "rows_to_change": len(self.changes),
            "text_replacements": sum(1 for r in self.rows if r.text_changes),
            "channel_changes": {f"{a} → {b}": n for (a, b), n in self.channel_changes().items()},
            "deposits": {f"{a} → {b}": n for (a, b), n in self.deposits().items()},
            "drifted": sorted(r.ref for r in self.rows if r.drifted),
            "skipped": {k: len(v) for k, v in self.skipped.items()},
        }


def plan_apply(
    conn: sqlite3.Connection,
    verdict_rows: Sequence[Mapping[str, str]],
    lines: Mapping[str, Mapping[str, str]],
    corrections: Mapping[str, str],
    *,
    by: str = VERIFIED_BY,
    on: str = VERIFIED_ON,
    channel: str = AUDIT_CHANNEL,
) -> ApplyPlan:
    """What ``audit-apply`` would write, read-only.

    A line is verified where the judge called it *correct* (the minted text
    stands) or gave its text (the judge's text stands, whatever the verdict:
    *boundary*, or none, which the conversion made *wrong*); a *boundary*
    without a text, a *wrong* without one and an *unreadable* are not. The row
    is the one ``gt_lines`` row on the line's ref. A confirmed line whose
    stored text is no longer the sheet's is left alone and listed: the verdict
    was on the text the sheet showed."""
    plan = ApplyPlan(rows=[], skipped={}, by=by, on=on, channel=channel, n_table=len(verdict_rows))

    def skip(reason: str, ref: str) -> None:
        plan.skipped.setdefault(reason, []).append(ref)

    for r in verdict_rows:
        ref = (r.get("ref") or "").strip()
        verdict = (r.get("verdict") or "").strip().lower()
        ln = lines.get(ref) or {}
        judged_text = collapse_whitespace(ln.get("gt_text") or "")
        new_text = corrections.get(ref)
        if verdict not in VERDICTS:
            skip("unjudged", ref)
            continue
        if verdict == "unreadable":
            skip("unreadable", ref)
            continue
        if new_text is None and verdict == "wrong":
            skip("wrong, no text given", ref)
            continue
        if new_text is None and verdict == "boundary":
            skip("boundary without a transcription", ref)
            continue
        found = conn.execute(
            "SELECT id, text, source, stratum, license_bucket FROM gt_lines "
            "WHERE line_image_ref = ? ORDER BY id",
            (ref,),
        ).fetchall()
        if not found:
            skip("no row in gt_lines", ref)
            continue
        if len(found) > 1:
            skip("more than one row in gt_lines", ref)
            continue
        row = found[0]
        stored = collapse_whitespace(row["text"] or "")
        if new_text is None or new_text == judged_text:  # confirmed as written
            klass, text = "correct", row["text"]
            if stored != judged_text:
                skip("the stored text is not the sheet's", ref)
                continue
            source = verified_source(row["source"], by=by, on=on)
            drifted = False
        else:
            klass = "boundary" if verdict == "boundary" else "corrected"
            text = new_text
            source = verified_source(row["source"], by=by, on=on, channel=channel)
            drifted = stored not in (judged_text, new_text)
        plan.rows.append(
            ApplyRow(
                ref=ref,
                group=(ln.get("group") or "").strip(),
                stratum=row["stratum"] or (ln.get("stratum") or "unknown"),
                verdict=klass,
                gt_id=row["id"],
                old_text=row["text"],
                text=text,
                old_source=row["source"],
                source=source,
                license_bucket=row["license_bucket"],
                drifted=drifted,
            )
        )
    plan.skipped = {k: plan.skipped[k] for k in SKIP_REASONS if k in plan.skipped}
    return plan


def write_verified_csv(path: Path | str, plan: ApplyPlan) -> Path:
    """``reports/kurrent/k3b-verified.csv``: the verified lines, the minted text
    where it stands and the judge's where it was corrected, with the licence of
    the deposit each row goes to."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    who = f"{plan.by} {plan.on}"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(VERIFIED_COLUMNS)
        for r in plan.rows:
            w.writerow([r.ref, r.group, r.stratum, r.verdict, r.text, who, r.licence])
    return path


def file_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply_plan(
    conn: sqlite3.Connection, plan: ApplyPlan, *, inputs: Mapping[str, str] | None = None
) -> int | None:
    """Write the plan's changes: one ``BEGIN IMMEDIATE`` transaction holding every
    row's update and the ``runs`` row (stage ``gt_audit``, finished, the counts
    and the input files' digests in its params). Returns the run id, or
    ``None`` where the store already holds every verified row as planned —
    then nothing is written, not even a run."""
    changes = plan.changes
    if not changes:
        return None

    def write() -> int:
        for r in changes:
            cur = conn.execute(
                "UPDATE gt_lines SET text = ?, source = ? WHERE id = ? AND text = ? AND source = ?",
                (r.text, r.source, r.gt_id, r.old_text, r.old_source),
            )
            if cur.rowcount != 1:  # the row moved under the plan: write nothing
                raise RuntimeError(f"gt_lines row {r.gt_id} ({r.ref}) changed since the plan")
        return db.record_run(
            conn,
            RUN_STAGE,
            model=RUN_MODEL,
            params={**plan.summary(), "inputs": dict(inputs or {})},
            git_sha=db.git_sha(),
            n_input=len(plan.rows),
            n_ok=len(changes),
            n_failed=0,
        )

    try:
        return with_write_lock(conn, write)
    except RuntimeError:
        conn.rollback()
        raise


def render_plan(plan: ApplyPlan, *, written: int | None = None, write: bool = False) -> list[str]:
    """The dry run's (or the write's) account, as plain lines for the console."""
    out: list[str] = []
    A = out.append
    classes = ", ".join(f"{k} {v}" for k, v in plan.by_class().items()) or "none"
    A(f"verified lines: {len(plan.rows)} of {plan.n_table} on the sheet ({classes})")
    A(
        f"rows to change: {len(plan.changes)} "
        f"(text replaced on {sum(1 for r in plan.rows if r.text_changes)}; "
        f"the mark '; verified {plan.by} {plan.on}' on every one)"
    )
    for (a, b), n in plan.channel_changes().items():
        A(f"  channel {a} → {b}: {n}")
    for (a, b), n in plan.deposits().items():
        moved = "stays in" if a == b else f"moves from {a} to"
        lic = legal.deposit_licence(b) if b != "none" else NOT_RELEASED
        A(f"  deposit: {n} {moved} {b} ({lic})")
    drifted = [r.ref for r in plan.rows if r.drifted]
    if drifted:
        A(
            f"  {len(drifted)} corrected lines whose stored text is no longer the sheet's "
            f"(the judge's text replaces it all the same): " + ", ".join(drifted[:8])
        )
    for reason, refs in plan.skipped.items():
        A(f"not verified — {reason}: {len(refs)}" + (f" ({', '.join(refs[:6])})" if refs else ""))
    if not write:
        A("dry run: the store was opened read-only and nothing was written")
    elif written is None:
        A("nothing to change: the store already holds every verified row as planned")
    else:
        A(f"written under run {written} (stage {RUN_STAGE}, model {RUN_MODEL})")
    return out


def group_tally(rows: Iterable[ApplyRow]) -> dict[str, dict[str, int]]:
    """Verified lines by the lines CSV's group and class."""
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        g = out.setdefault(r.group or UNGROUPED, {})
        g[r.verdict] = g.get(r.verdict, 0) + 1
    return dict(sorted(out.items()))


__all__ = [
    "AUDIT_CHANNEL",
    "CONVERTED_PHRASE",
    "CORRECTION_COLUMNS",
    "DEFAULT_VERIFIED_CSV",
    "EDITION_COLUMNS",
    "RUN_MODEL",
    "RUN_STAGE",
    "VERIFIED_BY",
    "VERIFIED_ON",
    "ApplyPlan",
    "ApplyRow",
    "Conversion",
    "ConvertedRow",
    "FoldReport",
    "FoldRow",
    "FoldScore",
    "apply_plan",
    "convert",
    "file_sha256",
    "fold_scores",
    "fold_summary",
    "folded_similarity",
    "group_tally",
    "parse_verdict",
    "plan_apply",
    "read_corrections",
    "read_lines",
    "read_table",
    "render_fold",
    "render_plan",
    "threshold_for",
    "verified_from_source",
    "verified_source",
    "write_corrections",
    "write_verdicts",
    "write_verified_csv",
]
