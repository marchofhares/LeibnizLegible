"""The letter-pool metric and the first measured German error rates (K2b, Task 3).

**The metric, letter by letter, nothing filtered.** A letter's reference text
(the pool's transcription, Task 1) is aligned to the concatenation, in reading
order, of *every* recognised line on the letter's pages (Task 2): machine text
before and after the letter — an address, an archival note, a neighbour on the
same leaf — is free, and everything inside the aligned span counts. That is
the infix (semi-global, edlib's "HW") alignment: the reference is consumed in
full, the machine text's prefix and suffix cost nothing, and the distance is
the least number of edits that turns some span of the machine text into the
reference. CER is that distance over the reference's length; it is computed as
a vectorised dynamic programme (one numpy row per reference character), so no
new dependency is needed, and checked against the full dynamic programme in
the tests. The number is honest in the sense the plan asked for: no aligner
chose the lines, so a reader is charged for every line it misreads, the ones
the factory's aligner would have declined included.

Four normalisation policies: the B1 harness's ``philiumm`` (NFD, whitespace
collapsed; case and diacritics kept — the headline), ``lenient`` (case and
diacritics folded) and ``strict`` (NFC; the lines are joined by single spaces
on both sides, so whitespace is not at issue here), and the Kurrent Trace
package's ``reading`` policy (NFC, the long s folded to s, whitespace
collapsed), under which K1 ranked the readers on Dresden. CER is pooled over
characters (Σ edits ÷ Σ reference characters) with a 95 % bootstrap interval
over letters (1,000 resamples, seed 12345 as in B1), and reported as a
per-letter distribution; per siglum, per year, per half (selection / test,
the amendment of 10 October) and over the whole set.

Beside it, labelled *selected*, the line-level CER over the lines the factory's
aligner accepts at its gate (``align_piece`` at the ``unknown`` stratum's
threshold): the number an aligner-filtered evaluation would report, shown so
the flattery of the selection can be seen.

The readers: ``v1``, the stored machine text of the corpus run (the German
error rate of what the website shows today, no GPU), and K1's candidates read
afresh through the pilot's crop machinery into
``data/kurrent/letterpool-readings/<reader>.jsonl`` (resumable, nothing to the
store). The pool is nc-bucket material: the reports carry numbers, letter
numbers and shelfmarks, never a reference text or a reading.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import statistics
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz.align import kurrent_pilot as P
from leibniz.align.align import HtrLine, align_piece
from leibniz.align.factory import STRATUM_THRESHOLDS
from leibniz.align.letterpool import LICENCE, LICENCE_BUCKET, VolumeSource, load_sources
from leibniz.align.letterpool_set import (
    DEFAULT_TESTSET_CSV,
    DEFAULT_TEXTS,
    HALVES,
    read_testset,
    read_texts,
    text_sha256,
)
from leibniz.htr import metrics
from leibniz.htr.kurrent import package_reading

DEFAULT_READINGS_DIR = Path("data/kurrent/letterpool-readings")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
DEFAULT_IMAGES_ROOT = Path("/mnt/d/leibniz-images")
V1 = P.V1
DEFAULT_READERS: tuple[str, ...] = (
    "philiumm",
    "trocr-kurrent-xvi-xvii",
    "trocr-hanse-xvi",
    "trocr-hanse-xvii",
)
EVALUATE_ONLY: frozenset[str] = frozenset({"trocr-hanse-xvi", "trocr-hanse-xvii"})
SELECTED_THRESHOLD = STRATUM_THRESHOLDS["unknown"]
BOOTSTRAP_SEED = 12345
BOOTSTRAP_RESAMPLES = 1000
HAND_CLASSES: dict[str, str] = {"L": "L", "l": "l", "K": "K/k", "k": "K/k"}

# --------------------------------------------------------------------------- #
# Policies
# --------------------------------------------------------------------------- #

Policy = Callable[[str], str]


def _b1(policy: metrics.NormPolicy) -> Policy:
    return lambda text: metrics.normalize(text, policy)


POLICIES: dict[str, Policy] = {
    "philiumm": _b1(metrics.PHILIUMM_POLICY),
    "lenient": _b1(metrics.LENIENT_POLICY),
    "strict": _b1(metrics.STRICT_POLICY),
    "reading": package_reading,
}
HEADLINE_POLICY = "philiumm"


# --------------------------------------------------------------------------- #
# The infix alignment
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Infix:
    """The best span of the text for the reference: its edit distance and bounds."""

    distance: int
    start: int
    end: int


def _hw_last_row(ref: str, text: str, *, free_prefix: bool = True):
    """The last row of the semi-global edit-distance table (``D[0][j] = 0``), vectorised.

    Row ``i`` from row ``i-1``: the diagonal and vertical moves element-wise,
    then the horizontal move as a cumulative minimum of ``E[j] - j`` (so
    ``D[i][j] = min_k≤j (E[k] + j - k)``), one numpy pass each.
    """
    import numpy as np

    m = len(text)
    codes = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
    js = np.arange(m + 1, dtype=np.int64)
    prev = np.zeros(m + 1, dtype=np.int64) if free_prefix else js.copy()
    e = np.empty(m + 1, dtype=np.int64)
    for i, ch in enumerate(ref, start=1):
        cost = (codes != ord(ch)).astype(np.int64)
        e[0] = i
        np.minimum(prev[:-1] + cost, prev[1:] + 1, out=e[1:])
        prev = js + np.minimum.accumulate(e - js)
    return prev


def infix_distance(ref: str, text: str, *, with_span: bool = True) -> Infix:
    """Edits to turn the cheapest span of ``text`` into ``ref``, with that span.

    The reference is consumed whole; the text's prefix and suffix are free. An
    empty reference costs nothing; an empty text costs the whole reference. The
    span's end is the first column attaining the minimum, its start the
    matching column of the reversed problem on ``text[:end]``, its start pinned at
    ``end``; among equal minima the longest span is taken. ``with_span=False`` skips the
    reverse pass and reports the span as ``(-1, -1)``: half the work when only the
    distance is wanted.
    """
    if not ref:
        return Infix(0, 0, 0)
    if not text:
        return Infix(len(ref), 0, 0)
    last = _hw_last_row(ref, text)
    if not with_span:
        return Infix(int(last.min()), -1, -1)
    end = len(last) - 1 - int(last[::-1].argmin())  # the last minimum: the longest span
    distance = int(last[end])
    back = _hw_last_row(ref[::-1], text[:end][::-1], free_prefix=False)  # pinned at end
    start = end - (len(back) - 1 - int(back[::-1].argmin()))
    return Infix(distance, start, end)


def infix_distance_reference(ref: str, text: str) -> int:
    """The same distance by the plain full table (the tests check the numpy row against it)."""
    n, m = len(ref), len(text)
    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == text[j - 1] else 1
            cur[j] = min(prev[j - 1] + cost, prev[j] + 1, cur[j - 1] + 1)
        prev = cur
    return min(prev)


# --------------------------------------------------------------------------- #
# The frozen set and the machine text
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class SetLetter:
    """One letter of the frozen set with its reference text (verified against the CSV)."""

    letter_id: str
    year: int
    number: str
    half: str
    siglum: str
    page_ids: list[str]
    n_lines: int
    n_chars: int
    text: str

    @property
    def hand(self) -> str:
        return HAND_CLASSES.get(self.siglum, "other")


def load_set(
    csv_path: Path | str = DEFAULT_TESTSET_CSV, texts_path: Path | str = DEFAULT_TEXTS
) -> list[SetLetter]:
    """The frozen set, each text checked against the CSV's SHA-256 (a changed text refuses)."""
    rows = read_testset(csv_path)
    texts = read_texts(texts_path)
    out: list[SetLetter] = []
    for r in rows:
        t = texts.get(r["letter_id"])
        if t is None:
            raise ValueError(f"{r['letter_id']} is in {csv_path} but not in {texts_path}")
        if text_sha256(t["text"]) != r["text_sha256"]:
            raise ValueError(
                f"{r['letter_id']}: the text in {texts_path} is not the frozen one "
                f"(SHA-256 differs from {csv_path})"
            )
        out.append(
            SetLetter(
                letter_id=r["letter_id"],
                year=r["year"],
                number=r["number"],
                half=r["half"],
                siglum=r["siglum"],
                page_ids=list(r["page_ids"]),
                n_lines=r["n_lines"],
                n_chars=r["n_chars"],
                text=t["text"],
            )
        )
    return out


@dataclass(slots=True)
class MachineText:
    """One reader's text for one letter: the lines in reading order, joined by spaces."""

    text: str
    n_lines: int
    n_read: int  # lines with a non-empty reading
    lines: list[HtrLine]


class PageReadings(dict):
    """A reader of the *page* kind (LT1): ``{page_id: Reading}``, the reading the text of
    the whole page as the model returned it, its lines separated by newlines.

    :func:`machine_text` recognises the kind and concatenates the pages of a
    letter in order, each page's lines becoming the letter's ``HtrLine`` rows, so
    the infix alignment, :func:`score_set`, :func:`pooled` and :func:`aggregate`
    run unchanged on it; a page without a reading (or read empty) contributes
    one empty line, so the page still counts in ``n_lines``.
    """


def page_lines_of(reading: P.Reading | None) -> list[str]:
    """A page reading's lines: split on newlines, stripped, the empty ones dropped."""
    if reading is None:
        return []
    return [ln.strip() for ln in reading.text.splitlines() if ln.strip()]


def set_lines(
    conn: sqlite3.Connection, letters: Sequence[SetLetter]
) -> dict[str, list[P.PilotLine]]:
    """The recognised lines of every letter's pages, in reading order, from the store."""
    out: dict[str, list[P.PilotLine]] = {}
    for ltr in letters:
        out[ltr.letter_id] = [ln for pid in ltr.page_ids for ln in P.page_lines(conn, pid)]
    return out


def machine_text(
    lines: Sequence[P.PilotLine],
    readings: Mapping[str, P.Reading],
    *,
    page_ids: Sequence[str] | None = None,
) -> MachineText:
    """The letter's machine text under one reader: the stored lines' readings in order,
    or — for a :class:`PageReadings` reader — the pages' texts in order (``page_ids``,
    else the pages the stored lines name)."""
    if isinstance(readings, PageReadings):
        pages = (
            list(page_ids)
            if page_ids is not None
            else list(dict.fromkeys(ln.page_id for ln in lines))
        )
        htr: list[HtrLine] = []
        for pid in pages:
            page_texts = page_lines_of(readings.get(pid))
            if not page_texts:
                htr.append(HtrLine(ref=f"{pid}:page", text=""))
                continue
            htr.extend(HtrLine(ref=f"{pid}:page:{k:03d}", text=t) for k, t in enumerate(page_texts))
    else:
        htr = [
            HtrLine(
                ref=ln.line_id, text=readings[ln.line_id].text if ln.line_id in readings else ""
            )
            for ln in lines
        ]
    texts = [h.text.strip() for h in htr]
    return MachineText(
        text=" ".join(t for t in texts if t),
        n_lines=len(htr),
        n_read=sum(1 for t in texts if t),
        lines=htr,
    )


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class LetterScore:
    """One letter under one reader and one policy: the atoms of every number reported."""

    letter_id: str
    year: int
    siglum: str
    hand: str
    half: str
    reader: str
    policy: str
    n_lines: int
    n_read: int
    ref_chars: int
    hyp_chars: int
    edits: int
    span_start: int
    span_end: int

    @property
    def cer(self) -> float:
        if self.ref_chars == 0:
            return 0.0 if self.edits == 0 else 1.0
        return self.edits / self.ref_chars

    @property
    def span_share(self) -> float:
        """The share of the machine text inside the aligned span (0 when no span was kept)."""
        if self.span_start < 0 or not self.hyp_chars:
            return 0.0
        return (self.span_end - self.span_start) / self.hyp_chars


def score_letter(
    letter: SetLetter, mt: MachineText, reader: str, policy: str, *, with_span: bool = True
) -> LetterScore:
    fn = POLICIES[policy]
    ref = fn(letter.text)
    hyp = fn(mt.text)
    res = infix_distance(ref, hyp, with_span=with_span)
    return LetterScore(
        letter_id=letter.letter_id,
        year=letter.year,
        siglum=letter.siglum,
        hand=letter.hand,
        half=letter.half,
        reader=reader,
        policy=policy,
        n_lines=mt.n_lines,
        n_read=mt.n_read,
        ref_chars=len(ref),
        hyp_chars=len(hyp),
        edits=res.distance,
        span_start=res.start,
        span_end=res.end,
    )


def score_set(
    letters: Sequence[SetLetter],
    lines: Mapping[str, Sequence[P.PilotLine]],
    readers: Mapping[str, Mapping[str, P.Reading]],
    *,
    policies: Iterable[str] = tuple(POLICIES),
    span_policies: Iterable[str] = (HEADLINE_POLICY,),
    log: Callable[[str], None] | None = None,
) -> list[LetterScore]:
    """Every letter under every reader and policy, nothing filtered; the aligned span is
    located only under ``span_policies`` (the distance needs one pass, the span two)."""
    out: list[LetterScore] = []
    pols = list(policies)
    spans = set(span_policies)
    for reader, readings in readers.items():
        for k, ltr in enumerate(letters, start=1):
            mt = machine_text(lines[ltr.letter_id], readings, page_ids=ltr.page_ids)
            for pol in pols:
                out.append(score_letter(ltr, mt, reader, pol, with_span=pol in spans))
            if log and k % 25 == 0:
                log(f"{reader}: {k} letters scored")
    return out


def pooled(
    scores: Sequence[LetterScore],
    *,
    seed: int = BOOTSTRAP_SEED,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict:
    """CER pooled over characters with a bootstrap interval over letters, and the per-letter
    distribution (the B1 harness's bootstrap, the letters as its atoms)."""
    atoms = [metrics.LineScore(s.letter_id, "", "", s.edits, s.ref_chars, 0, 0) for s in scores]
    ci = metrics.bootstrap_ci(atoms, metric="cer", n_resamples=n_resamples, seed=seed)
    cers = sorted(s.cer for s in scores)
    if len(cers) >= 2:
        q = statistics.quantiles(cers, n=4)
    elif cers:
        q = [cers[0]] * 3
    else:
        q = [0.0, 0.0, 0.0]
    return {
        "letters": len(scores),
        "lines": sum(s.n_lines for s in scores),
        "lines_read": sum(s.n_read for s in scores),
        "ref_chars": sum(s.ref_chars for s in scores),
        "edits": sum(s.edits for s in scores),
        "cer": ci.point,
        "cer_lo": ci.lo,
        "cer_hi": ci.hi,
        "letter_cer_mean": statistics.fmean(cers) if cers else 0.0,
        "letter_cer_q1": q[0],
        "letter_cer_median": q[1],
        "letter_cer_q3": q[2],
        "letter_cer_min": cers[0] if cers else 0.0,
        "letter_cer_max": cers[-1] if cers else 0.0,
        "span_share_mean": (
            statistics.fmean(s.span_share for s in scores if s.span_start >= 0)
            if any(s.span_start >= 0 for s in scores)
            else 0.0
        ),
    }


def aggregate(scores: Sequence[LetterScore]) -> dict:
    """``{reader: {policy: {"all": …, "half": {…}, "hand": {…}, "year": {…}}}}``."""
    by: dict[tuple[str, str], list[LetterScore]] = defaultdict(list)
    for s in scores:
        by[(s.reader, s.policy)].append(s)
    out: dict = {}
    for (reader, policy), rows in sorted(by.items()):
        block = {
            "all": pooled(rows),
            "half": {
                h: pooled([s for s in rows if s.half == h])
                for h in HALVES
                if any(s.half == h for s in rows)
            },
            "hand": {
                hand: pooled([s for s in rows if s.hand == hand])
                for hand in sorted({s.hand for s in rows})
            },
            "year": {
                str(y): pooled([s for s in rows if s.year == y])
                for y in sorted({s.year for s in rows})
            },
        }
        out.setdefault(reader, {})[policy] = block
    return out


# --------------------------------------------------------------------------- #
# The selected line-level number
# --------------------------------------------------------------------------- #


def selected_scores(
    letters: Sequence[SetLetter],
    lines: Mapping[str, Sequence[P.PilotLine]],
    readers: Mapping[str, Mapping[str, P.Reading]],
    *,
    threshold: float = SELECTED_THRESHOLD,
    policies: Iterable[str] = tuple(POLICIES),
) -> dict:
    """Line-level CER over the lines the factory's aligner accepts, per reader and policy —
    the flattered number, labelled as selected. Returns ``{reader: {"lines": n, "aligned": a,
    "yield": a/n, "policies": {policy: {"cer": …, "ref_chars": …, "edits": …}}}}``."""
    out: dict = {}
    pols = list(policies)
    for reader, readings in readers.items():
        n_lines = n_aligned = 0
        edits = dict.fromkeys(pols, 0)
        refs = dict.fromkeys(pols, 0)
        for ltr in letters:
            mt = machine_text(lines[ltr.letter_id], readings, page_ids=ltr.page_ids)
            res = align_piece(mt.lines, ltr.text, threshold=threshold)
            n_lines += res.n_lines
            for al in res.lines:
                if not al.aligned:
                    continue
                n_aligned += 1
                for pol in pols:
                    fn = POLICIES[pol]
                    ref, hyp = fn(al.edition_text), fn(al.htr_text)
                    edits[pol] += metrics.edit_distance(ref, hyp)
                    refs[pol] += len(ref)
        out[reader] = {
            "threshold": threshold,
            "lines": n_lines,
            "aligned": n_aligned,
            "yield": n_aligned / n_lines if n_lines else 0.0,
            "policies": {
                pol: {
                    "cer": edits[pol] / refs[pol] if refs[pol] else 0.0,
                    "ref_chars": refs[pol],
                    "edits": edits[pol],
                }
                for pol in pols
            },
        }
    return out


# --------------------------------------------------------------------------- #
# Readings
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ReaderInfo:
    reader: str
    model: str
    device: str
    lines_read: int
    ms_per_line: float | None
    licence: str
    evaluate_only: bool


def reader_info(
    reader: str,
    readings: Mapping[str, P.Reading],
    licence: str,
    lines: Mapping[str, Sequence[P.PilotLine]] | None = None,
) -> ReaderInfo:
    """A reader's model, device, pace and coverage; the lines read are counted per letter
    (a page two letters share counts for each) when the set's ``lines`` are given. For a
    page reader the lines read are the lines of its page texts and the pace is per page,
    reported as ``None`` here (the LT1 report carries the seconds a page)."""
    ms = [r.ms for r in readings.values() if r.ms > 0]
    if isinstance(readings, PageReadings):
        pages = (
            list(dict.fromkeys(ln.page_id for ls in lines.values() for ln in ls))
            if lines is not None
            else list(readings)
        )
        lines_read = sum(len(page_lines_of(readings.get(pid))) for pid in pages)
        pace = None
    elif lines is not None:
        lines_read = sum(
            1
            for ls in lines.values()
            for ln in ls
            if ln.line_id in readings and readings[ln.line_id].text.strip()
        )
        pace = statistics.fmean(ms) if ms else None
    else:
        lines_read = sum(1 for r in readings.values() if r.text.strip())
        pace = statistics.fmean(ms) if ms else None
    return ReaderInfo(
        reader=reader,
        model=next((r.model for r in readings.values() if r.model), reader),
        device=next((r.device for r in readings.values() if r.device), ""),
        lines_read=lines_read,
        ms_per_line=pace,
        licence=licence,
        evaluate_only=reader in EVALUATE_ONLY,
    )


@dataclass(slots=True)
class _Piece:
    """What the pilot's reader needs of a letter: its pages."""

    page_ids: list[str]


def read_set(
    conn: sqlite3.Connection,
    letters: Sequence[SetLetter],
    readers: Sequence[str],
    *,
    engine_factory: Callable[[str], object],
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    readings_dir: Path | str = DEFAULT_READINGS_DIR,
    batch_size: int = 8,
    sample: int | None = None,
    log: Callable[[str], None] | None = None,
    crop_cache: Path | str | None = None,
) -> dict[str, dict[str, P.Reading]]:
    """Read every line of the set's pages with each reader, resuming from its JSONL; with a
    crop cache the first reader cuts the lines and the others read the cuts."""
    pieces = [_Piece(list(ltr.page_ids)) for ltr in letters]
    out: dict[str, dict[str, P.Reading]] = {}
    for key in readers:
        out[key] = P.read_pieces(
            conn,
            pieces,
            key,
            lambda k=key: engine_factory(k),
            images_root=images_root,
            readings_dir=readings_dir,
            sample=sample,
            batch_size=batch_size,
            log=log,
            crop_cache=crop_cache,
        )
    return out


def readings_on_disk(
    readers: Sequence[str], readings_dir: Path | str = DEFAULT_READINGS_DIR
) -> dict[str, dict[str, P.Reading]]:
    out: dict[str, dict[str, P.Reading]] = {}
    for key in readers:
        got = P.load_readings(readings_dir, key)
        if got:
            out[key] = got
    return out


def v1_for_set(conn: sqlite3.Connection, letters: Sequence[SetLetter]) -> dict[str, P.Reading]:
    return P.v1_readings(conn, [_Piece(list(ltr.page_ids)) for ltr in letters])


# --------------------------------------------------------------------------- #
# Result, files and report
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class EvalResult:
    letters: int
    pages: int
    lines: int
    ref_chars: int
    by_half: dict
    readers: list[ReaderInfo]
    aggregate: dict
    selected: dict
    scores: list[LetterScore]
    sources: list[VolumeSource]
    generated: str = field(default_factory=lambda: date.today().isoformat())

    def as_dict(self) -> dict:
        return {
            "generated": self.generated,
            "set": {
                "letters": self.letters,
                "pages": self.pages,
                "lines": self.lines,
                "ref_chars": self.ref_chars,
                "by_half": self.by_half,
            },
            "metric": {
                "alignment": "infix (semi-global): reference consumed whole, machine prefix and "
                "suffix free; the concatenation of every recognised line on the letter's pages",
                "policies": {
                    "philiumm": metrics.PHILIUMM_POLICY.describe(),
                    "lenient": metrics.LENIENT_POLICY.describe(),
                    "strict": metrics.STRICT_POLICY.describe(),
                    "reading": "NFC · long s → s · collapse-ws (the Kurrent Trace package)",
                },
                "bootstrap": f"{BOOTSTRAP_RESAMPLES} resamples of letters, 95 % percentile "
                f"interval, seed {BOOTSTRAP_SEED}",
                "selected_threshold": SELECTED_THRESHOLD,
            },
            "readers": [asdict(r) for r in self.readers],
            "aggregate": self.aggregate,
            "selected": self.selected,
            "sources": [
                {"year": s.year, "version": s.version, "citation": s.citation, "url": s.url}
                for s in self.sources
            ],
            "licence": LICENCE,
            "licence_bucket": LICENCE_BUCKET,
        }


def build_result(
    letters: Sequence[SetLetter],
    lines: Mapping[str, Sequence[P.PilotLine]],
    readers: Mapping[str, Mapping[str, P.Reading]],
    *,
    licences: Mapping[str, str],
    sources: Sequence[VolumeSource] = (),
    log: Callable[[str], None] | None = None,
) -> EvalResult:
    scores = score_set(letters, lines, readers, log=log)
    by_half = {
        h: {
            "letters": sum(1 for ltr in letters if ltr.half == h),
            "pages": sum(len(ltr.page_ids) for ltr in letters if ltr.half == h),
            "lines": sum(len(lines[ltr.letter_id]) for ltr in letters if ltr.half == h),
            "ref_chars": sum(ltr.n_chars for ltr in letters if ltr.half == h),
        }
        for h in HALVES
    }
    return EvalResult(
        letters=len(letters),
        pages=sum(len(ltr.page_ids) for ltr in letters),
        lines=sum(len(lines[ltr.letter_id]) for ltr in letters),
        ref_chars=sum(ltr.n_chars for ltr in letters),
        by_half=by_half,
        readers=[reader_info(k, v, licences.get(k, "—"), lines) for k, v in readers.items()],
        aggregate=aggregate(scores),
        selected=selected_scores(letters, lines, readers),
        scores=scores,
        sources=list(sources),
    )


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{d}f} %"


def _ci(block: dict | None) -> str:
    if not block or not block.get("letters"):
        return "—"
    return f"**{_pct(block['cer'])}** ({_pct(block['cer_lo'])}–{_pct(block['cer_hi'])})"


def _n(x: int) -> str:
    return f"{x:,}"


def render_report(res: EvalResult) -> str:
    """``letterpool-eval.md``: numbers only, the pool cited with its versions."""
    out: list[str] = []
    readers = [r.reader for r in res.readers]
    out.append("# The German error rate on the letter-pool test set (K2b Task 3)")
    out.append("")
    out.append(
        f"**{_n(res.letters)} letters, {_n(res.pages)} pages, {_n(res.lines)} recognised lines, "
        f"{_n(res.ref_chars)} reference characters** — the frozen set of Task 2 "
        "(`letterpool-testset.csv`): every letter in Leibniz's hand that placed and a seeded "
        "sample of the correspondents' letters, split once into a selection half ("
        f"{res.by_half['selection']['letters']} letters, {_n(res.by_half['selection']['lines'])} "
        f"lines) and a test half ({res.by_half['test']['letters']} letters, "
        f"{_n(res.by_half['test']['lines'])} lines). The references are the GWLB "
        "Leibniz-Archiv's checked transcriptions (cited below), made from the originals for "
        "the edition and selected by no reader; they are CC BY-NC 4.0, nc bucket, so this "
        "report carries numbers and letter numbers only."
    )
    out.append("")
    out.append(
        "**The metric.** Each letter's reference text is aligned to the concatenation, in "
        "reading order, of every recognised line on its pages — an infix alignment: the "
        "reference is consumed whole, the machine text before and after it (an address, an "
        "archival note, a neighbour on the leaf) is free, and everything inside the aligned "
        "span counts. CER is the edit distance over the reference length, pooled over "
        f"characters, with a 95 % bootstrap interval over letters ({BOOTSTRAP_RESAMPLES} "
        f"resamples, seed {BOOTSTRAP_SEED}), and as a per-letter distribution. Policies: "
        "`philiumm` (NFD, whitespace collapsed; case and diacritics kept — the headline, the "
        "B1 harness's), `lenient` (case and diacritics folded), `strict` (NFC; the lines are "
        "joined by single spaces on both sides), `reading` (NFC, the long s folded to s, "
        "whitespace collapsed — the Kurrent Trace package's policy, as K1 scored Dresden). "
        "Nothing is filtered: a line a reader misreads counts whether or not the factory's "
        "aligner would have accepted it."
    )
    out.append("")
    out.append("## The readers")
    out.append("")
    out.append(
        "| reader | model | device | lines read of " + _n(res.lines) + " | ms/line | licence |"
    )
    out.append("|---|---|---|---:|---:|---|")
    for r in res.readers:
        out.append(
            f"| {r.reader} | {r.model} | {r.device or '—'} | {_n(r.lines_read)} | "
            f"{'—' if r.ms_per_line is None else f'{r.ms_per_line:.0f}'} | "
            f"{r.licence}{' (evaluate only)' if r.evaluate_only else ''} |"
        )
    out.append("")
    out.append(
        "`v1` is the stored machine text of the C1 corpus run (what the website shows today); "
        "the others read the same lines afresh from the page images through the pilot's crop "
        "machinery (the v1 geometry, the polygon masked, no downscaling). A line a reader "
        "returned empty counts as deleted."
    )
    out.append("")
    out.append("## CER pooled over characters, 95 % bootstrap interval over letters")
    out.append("")
    out.append(
        "| reader | `philiumm`, whole | selection half | test half | `lenient` | `strict` | "
        "`reading` |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|")
    agg = res.aggregate
    for reader in readers:
        head = agg[reader][HEADLINE_POLICY]
        out.append(
            f"| {reader} | {_ci(head['all'])} | {_ci(head['half'].get('selection'))} | "
            f"{_ci(head['half'].get('test'))} | {_pct(agg[reader]['lenient']['all']['cer'])} | "
            f"{_pct(agg[reader]['strict']['all']['cer'])} | "
            f"{_pct(agg[reader]['reading']['all']['cer'])} |"
        )
    out.append("")
    out.append("## By hand (`philiumm` policy; the `reading` policy in brackets)")
    out.append("")
    hands = sorted({h for r in readers for h in agg[r][HEADLINE_POLICY]["hand"]})
    out.append("| reader | " + " | ".join(hands) + " |")
    out.append("|---|" + "---:|" * len(hands))
    for reader in readers:
        cells = []
        for hand in hands:
            b = agg[reader][HEADLINE_POLICY]["hand"].get(hand)
            r_ = agg[reader]["reading"]["hand"].get(hand)
            cells.append(
                f"{_ci(b)} [{_pct(r_['cer'])}] · {b['letters']} letters, {_n(b['lines'])} lines"
                if b
                else "—"
            )
        out.append(f"| {reader} | " + " | ".join(cells) + " |")
    out.append("")
    out.append(
        "*L*: Leibniz's own hand (his drafts and fair copies); *K/k*: the correspondent's "
        "hand or the correspondent's scribe's."
    )
    out.append("")
    out.append("## By year (`philiumm` policy)")
    out.append("")
    years = sorted({y for r in readers for y in agg[r][HEADLINE_POLICY]["year"]})
    out.append("| reader | " + " | ".join(years) + " |")
    out.append("|---|" + "---:|" * len(years))
    for reader in readers:
        cells = []
        for y in years:
            b = agg[reader][HEADLINE_POLICY]["year"].get(y)
            cells.append(f"{_pct(b['cer'])} ({b['letters']})" if b else "—")
        out.append(f"| {reader} | " + " | ".join(cells) + " |")
    out.append("")
    out.append("## Per-letter distribution (`philiumm` policy)")
    out.append("")
    out.append("| reader | mean | min | Q1 | median | Q3 | max | machine text inside the span |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for reader in readers:
        b = agg[reader][HEADLINE_POLICY]["all"]
        out.append(
            f"| {reader} | {_pct(b['letter_cer_mean'])} | {_pct(b['letter_cer_min'])} | "
            f"{_pct(b['letter_cer_q1'])} | {_pct(b['letter_cer_median'])} | "
            f"{_pct(b['letter_cer_q3'])} | {_pct(b['letter_cer_max'])} | "
            f"{_pct(b['span_share_mean'])} |"
        )
    out.append("")
    out.append("## Selected: the line-level CER over the lines the factory's aligner accepts")
    out.append("")
    out.append(
        f"The same readings aligned line by line with `align_piece` at threshold "
        f"{SELECTED_THRESHOLD:.2f} (the factory's gate for a piece of unknown stratum); CER "
        "over the accepted lines only, the minted slice against the reader's line. This is "
        "what an aligner-filtered evaluation reports, and it is flattered by the selection: "
        "the aligner keeps the lines the reader already reads well."
    )
    out.append("")
    out.append(
        "| reader | lines | accepted | yield | `philiumm` CER, selected | `reading` CER, selected |"
    )
    out.append("|---|---:|---:|---:|---:|---:|")
    for reader in readers:
        s = res.selected.get(reader)
        if not s:
            continue
        out.append(
            f"| {reader} | {_n(s['lines'])} | {_n(s['aligned'])} | {_pct(s['yield'])} | "
            f"{_pct(s['policies']['philiumm']['cer'])} | {_pct(s['policies']['reading']['cer'])} |"
        )
    out.append("")
    out.append("## What this measures, and what it does not")
    out.append("")
    out.append(
        "- The reference is a checked transcription of the letter's own text; the pages carry "
        "more (an address, a note, a neighbour) and the infix alignment leaves that uncharged "
        "before and after the letter, but anything in the middle — a note the editor set "
        "aside, an insertion printed in the apparatus — is charged, as is a supplied "
        "letter the editor added in brackets, which the parser keeps (C2b's rule)."
    )
    out.append(
        "- The letters were chosen by no reader and nothing is filtered, so these are the "
        "error rates of reading Leibniz's German correspondence of 1708–1716 as it lies on "
        "the leaves — not of the lines a factory would mint. K3 reports its model's rate on "
        "this set and never tunes on it; the selection half is where a reader may be chosen."
    )
    out.append(
        "- The `philiumm` policy keeps case and diacritics; the `reading` policy folds the "
        "long s, which the Kurrent readers write and the transcription does not."
    )
    out.append("")
    out.append("## Sources")
    out.append("")
    for s in res.sources:
        out.append(f"- {s.citation} — version {s.version}, `{s.url}`")
    out.append("")
    return "\n".join(out)


def write_outputs(
    res: EvalResult, reports_dir: Path | str = DEFAULT_REPORTS_DIR
) -> dict[str, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "report": reports_dir / "letterpool-eval.md",
        "summary": reports_dir / "letterpool-eval.json",
        "letters": reports_dir / "letterpool-eval-letters.csv",
    }
    paths["report"].write_text(render_report(res), encoding="utf-8")
    paths["summary"].write_text(
        json.dumps(res.as_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with paths["letters"].open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "letter_id",
                "year",
                "siglum",
                "half",
                "reader",
                "policy",
                "n_lines",
                "n_read",
                "ref_chars",
                "hyp_chars",
                "edits",
                "cer",
                "span_start",
                "span_end",
            ]
        )
        for s in res.scores:
            w.writerow(
                [
                    s.letter_id,
                    s.year,
                    s.siglum,
                    s.half,
                    s.reader,
                    s.policy,
                    s.n_lines,
                    s.n_read,
                    s.ref_chars,
                    s.hyp_chars,
                    s.edits,
                    f"{s.cer:.4f}",
                    s.span_start,
                    s.span_end,
                ]
            )
    return paths


def default_sources(path: Path | str | None = None) -> list[VolumeSource]:
    return load_sources(path) if path else load_sources()


__all__ = [
    "BOOTSTRAP_RESAMPLES",
    "BOOTSTRAP_SEED",
    "DEFAULT_IMAGES_ROOT",
    "DEFAULT_READERS",
    "DEFAULT_READINGS_DIR",
    "DEFAULT_REPORTS_DIR",
    "EVALUATE_ONLY",
    "HAND_CLASSES",
    "HEADLINE_POLICY",
    "POLICIES",
    "SELECTED_THRESHOLD",
    "V1",
    "EvalResult",
    "Infix",
    "LetterScore",
    "MachineText",
    "PageReadings",
    "ReaderInfo",
    "SetLetter",
    "aggregate",
    "build_result",
    "default_sources",
    "infix_distance",
    "infix_distance_reference",
    "load_set",
    "machine_text",
    "page_lines_of",
    "pooled",
    "read_set",
    "reader_info",
    "readings_on_disk",
    "render_report",
    "score_letter",
    "score_set",
    "selected_scores",
    "set_lines",
    "v1_for_set",
    "write_outputs",
]
