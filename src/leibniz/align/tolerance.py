"""How much HTR noise the retro-aligner tolerates (Phase K1, Task 1).

The Kurrent track needs this number before it chooses a bootstrap reader. The
factory (:mod:`leibniz.align.factory`) mints a line when the aligner's
confidence — the fraction of the line's folded HTR characters that the global
alignment matched exactly — clears the stratum's threshold. A reader that reads
Kurrent at 30 % CER hands the aligner three to four times the noise the PHILIUMM
model makes on Latin (7.95 % on the validation split, B1). Does the aligner
still find the lines, and are the slices it mints still right?

The B2 harness (:mod:`leibniz.align.evaluate`) answers that on real data: the
PHILIUMM validation split, its gold text concatenated into a stand-in edition
text, pieces of 25 consecutive lines, the machine text aligned and every
projected slice graded against the line's known truth. Here the machine text is
the *recorded* HTR output of the B1 reproduction
(``reports/philiumm-repro.lines.jsonl``, 1,878 lines in validation order), so
no model and no image is needed, and it is **corrupted further on the HTR
side** to reach a target character error rate against the gold: substitutions
from a table of visually confusable letters, dropped and doubled minims, two
minims merged into one letter, merged and split word spaces, dropped letters.
The corruption rate is calibrated per level so that the achieved CER —
micro-averaged over all lines, measured with the B1 scorer's edit distance —
meets the target; the *folded* CER, after the aligner's own normalisation, is
reported beside it, because u/v, i/j, case, accents and punctuation never reach
the aligner.

Yield and precision are then read at the factory's per-stratum thresholds with
the factory's own gate (confidence, a non-empty slice, no edition-only burst),
and the break-even CER — where yield falls under 50 % and where precision falls
under the 95 % gate — is interpolated between the tested levels.

Pure and offline; the tests run the whole chain on fixtures.
"""

from __future__ import annotations

import json
import random
import statistics
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from pathlib import Path

from leibniz.align import dp
from leibniz.align import evaluate as E
from leibniz.align.factory import STRATUM_THRESHOLDS
from leibniz.align.normalize import DEFAULT_NORM, normalize
from leibniz.align.report import GATE_PRECISION
from leibniz.htr.metrics import edit_distance

DEFAULT_LINES = Path("reports/philiumm-repro.lines.jsonl")
DEFAULT_OUT_DIR = Path("reports/kurrent")
DEFAULT_LEVELS: tuple[float, ...] = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60)
DEFAULT_SEED = 20261009
LINES_PER_PIECE = 25
YIELD_FLOOR = 0.50  # the break-even question: where does yield fall under half?
PRECISION_FLOOR = GATE_PRECISION  # and where under the factory's 95 % gate?
CORRECT_SIM = 0.90  # the B2 harness's grade: folded similarity of slice vs gold

# --------------------------------------------------------------------------- #
# The corruption model
# --------------------------------------------------------------------------- #

# Directed confusion table: a fired letter is replaced by one of its listed
# look-alikes, drawn uniformly. Chosen for a 17th-century cursive hand read by a
# line recogniser: the minim group (u n m i r), the round letters (a o e c), the
# long-s family (s f l t), ascender and descender look-alikes (b h k; g q p y),
# and the capitals and digits recognisers confuse. Multi-character targets are
# the *split* minims ("m" read as "in", "u" as "ii"); the reverse merges live
# in :data:`MERGES`.
CONFUSIONS: dict[str, tuple[str, ...]] = {
    "a": ("o", "e", "u", "n"),
    "b": ("h", "l", "d", "p"),
    "c": ("e", "o", "t", "r"),
    "d": ("a", "cl", "b", "o"),
    "e": ("c", "o", "a", "i"),
    "f": ("s", "l", "t"),
    "g": ("q", "y", "s", "j"),
    "h": ("b", "k", "li", "n"),
    "i": ("l", "j", "t", "r", "e"),
    "j": ("i", "g", "y"),
    "k": ("h", "l", "b"),
    "l": ("i", "t", "b", "f"),
    "m": ("n", "in", "ni", "rn", "nn"),
    "n": ("u", "r", "m", "ri", "ii"),
    "o": ("a", "c", "e", "u"),
    "p": ("q", "b", "y"),
    "q": ("g", "p", "y"),
    "r": ("t", "n", "c", "i"),
    "s": ("f", "l", "r", "z", "x"),
    "t": ("r", "l", "c", "f"),
    "u": ("n", "v", "a", "ii"),
    "v": ("u", "b", "r"),
    "w": ("vv", "uu", "m"),
    "x": ("z", "s", "r"),
    "y": ("g", "j", "p", "ij"),
    "z": ("x", "s", "y"),
    "A": ("R", "N", "H"),
    "B": ("R", "P", "E"),
    "C": ("G", "O", "E"),
    "D": ("O", "Q", "P"),
    "E": ("F", "B", "C"),
    "F": ("E", "P", "T"),
    "G": ("C", "O", "Q"),
    "H": ("N", "M", "K"),
    "I": ("J", "L", "T"),
    "J": ("I", "L", "T"),
    "K": ("H", "R", "X"),
    "L": ("I", "T", "E"),
    "M": ("N", "H", "W"),
    "N": ("M", "H", "A"),
    "O": ("Q", "D", "C"),
    "P": ("B", "R", "F"),
    "Q": ("O", "G", "D"),
    "R": ("B", "P", "K"),
    "S": ("Z", "G", "L"),
    "T": ("I", "F", "L"),
    "U": ("V", "W", "N"),
    "V": ("U", "W", "Y"),
    "W": ("V", "U", "M"),
    "X": ("K", "Y", "Z"),
    "Y": ("V", "X", "T"),
    "Z": ("S", "X", "L"),
    "0": ("o", "O", "6"),
    "1": ("l", "I", "7"),
    "2": ("z", "Z", "7"),
    "3": ("5", "8", "B"),
    "4": ("9", "A", "1"),
    "5": ("s", "S", "3"),
    "6": ("0", "b", "G"),
    "7": ("1", "T", "2"),
    "8": ("3", "B", "0"),
    "9": ("4", "g", "q"),
}

# A fired punctuation mark is dropped or swapped for another mark.
PUNCTUATION_CONFUSIONS: tuple[str, ...] = (".", ",", ";", ":", "-", "'")

# Two characters a reader runs together into one: the merged minims and the
# other pairs whose strokes join in a cursive hand.
MERGES: dict[str, str] = {
    "in": "m",
    "ni": "m",
    "rn": "m",
    "nn": "m",
    "ii": "u",
    "ri": "n",
    "cl": "d",
    "vv": "w",
    "uu": "w",
    "li": "h",
    "ij": "y",
}

# The share of each operation among fired letter positions. Substitution
# dominates, as it does in the recorded errors of the B1 reproduction (the
# report measures that mix beside this one); a dropped letter or minim, a
# doubled one, two characters merged into one and a word split in two are the
# rest. A fired *space* is always a merged word space; a fired combining mark
# is always a dropped accent.
OP_SUBSTITUTE = 0.50
OP_DELETE = 0.15
OP_INSERT = 0.15
OP_MERGE = 0.10
OP_SPLIT = 0.10
assert abs(OP_SUBSTITUTE + OP_DELETE + OP_INSERT + OP_MERGE + OP_SPLIT - 1.0) < 1e-9


def _pick(options: Sequence[str], u: float) -> str:
    return options[min(int(u * len(options)), len(options) - 1)]


def corrupt_line(text: str, rate: float, rng: random.Random) -> tuple[str, int]:
    """Corrupt one line of machine text at a per-character ``rate``.

    Returns ``(corrupted, n_ops)``. Three uniforms are drawn for *every*
    character of the input, whether or not the position fires, so under one
    seed a higher rate fires a superset of a lower rate's positions with the
    same operations — what lets :func:`calibrate_rate` bisect on the rate.
    """
    out: list[str] = []
    n_ops = 0
    skip_next = False
    n = len(text)
    for i, ch in enumerate(text):
        fire, kind, pick = rng.random(), rng.random(), rng.random()
        if skip_next:  # consumed by a merge; its uniforms are drawn and dropped
            skip_next = False
            continue
        if fire >= rate:
            out.append(ch)
            continue
        n_ops += 1
        if ch == " ":
            continue  # a merged word space
        if unicodedata.combining(ch):
            continue  # a dropped accent
        targets = CONFUSIONS.get(ch)
        if targets is None:
            if unicodedata.category(ch)[0] in ("P", "S"):
                if kind < 0.5:
                    continue  # dropped mark
                others = tuple(m for m in PUNCTUATION_CONFUSIONS if m != ch)
                out.append(_pick(others, pick))
            # any other character (a stray glyph) is dropped
            continue
        if kind < OP_SUBSTITUTE:
            out.append(_pick(targets, pick))
        elif kind < OP_SUBSTITUTE + OP_DELETE:
            pass  # dropped letter or minim
        elif kind < OP_SUBSTITUTE + OP_DELETE + OP_INSERT:
            out.append(ch)
            out.append(ch)  # doubled letter or minim
        elif kind < OP_SUBSTITUTE + OP_DELETE + OP_INSERT + OP_MERGE:
            pair = text[i : i + 2]
            merged = MERGES.get(pair)
            if merged is not None:
                out.append(merged)
                skip_next = True
            else:
                out.append(_pick(targets, pick))
        else:
            inside_word = bool(out) and out[-1] != " " and i + 1 < n and text[i + 1] != " "
            if inside_word:
                out.append(" ")  # a split word
                out.append(ch)
            else:
                out.append(_pick(targets, pick))
    return "".join(out), n_ops


def corpus_cer(refs: Sequence[str], hyps: Sequence[str]) -> float:
    """Micro-averaged CER: total character edits ÷ total reference characters."""
    edits = sum(edit_distance(r, h) for r, h in zip(refs, hyps, strict=True))
    chars = sum(len(r) for r in refs)
    return edits / chars if chars else 0.0


def level_rng(seed: int, target: float | None) -> random.Random:
    """One deterministic stream per (seed, level), independent of the others."""
    return random.Random(f"{seed}:{'base' if target is None else round(target * 1000)}")


def corrupt_all(
    hyps: Sequence[str], rate: float, *, seed: int, target: float | None
) -> tuple[list[str], int]:
    """Corrupt every line with the level's stream; return the texts and the op count."""
    rng = level_rng(seed, target)
    out: list[str] = []
    n_ops = 0
    for h in hyps:
        c, k = corrupt_line(h, rate, rng)
        out.append(c)
        n_ops += k
    return out, n_ops


def calibrate_rate(
    refs: Sequence[str],
    hyps: Sequence[str],
    target: float,
    *,
    seed: int,
    tol: float = 0.0005,
    max_iter: int = 16,
    sample_every: int = 1,
) -> tuple[float, float]:
    """Find the per-character rate whose achieved CER meets ``target``.

    Bisection on the rate: :func:`corrupt_line` fires a nested set of positions
    as the rate grows, so the achieved CER is monotone in it up to the rare edit
    that happens to repair an existing HTR error. ``sample_every`` calibrates on
    every n-th line (the pure-Python edit distance is the cost); the caller
    measures the exact CER on all lines afterwards. Returns ``(rate, cer)``,
    ``(0.0, base_cer)`` when the base text already exceeds the target.
    """
    sub_refs = list(refs[::sample_every])
    if not sub_refs:
        return 0.0, 0.0

    def cer_at(rate: float) -> float:
        # The stream must be the one the full run uses, so corrupt every line in
        # order and keep the sampled ones.
        rng = level_rng(seed, target)
        kept: list[str] = []
        for idx, h in enumerate(hyps):
            c, _ = corrupt_line(h, rate, rng)
            if idx % sample_every == 0:
                kept.append(c)
        return corpus_cer(sub_refs, kept)

    base = cer_at(0.0)
    if base >= target:
        return 0.0, base
    lo, hi = 0.0, 1.0
    cer_hi = cer_at(1.0)
    if cer_hi <= target:
        return 1.0, cer_hi
    rate, cer = hi, cer_hi
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        c = cer_at(mid)
        if abs(c - target) < abs(cer - target):
            rate, cer = mid, c
        if abs(c - target) <= tol:
            break
        if c < target:
            lo = mid
        else:
            hi = mid
    return rate, cer


# --------------------------------------------------------------------------- #
# The recorded machine text
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ReproLine:
    """One line of the B1 reproduction dump: id, gold reference, machine text."""

    line_id: str
    ref: str
    hyp: str


def load_repro_lines(path: Path | str, *, max_lines: int | None = None) -> list[ReproLine]:
    """Read the repro dump (``line_id``, ``ref``, ``hyp`` per row) in file order."""
    out: list[ReproLine] = []
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            row = json.loads(raw)
            out.append(ReproLine(str(row["line_id"]), str(row["ref"]), str(row.get("hyp", ""))))
            if max_lines is not None and len(out) >= max_lines:
                break
    return out


class _GoldPair:
    """The shape :func:`leibniz.align.evaluate.build_pieces` consumes; no image."""

    __slots__ = ("line_id", "reference")

    def __init__(self, line_id: str, reference: str) -> None:
        self.line_id = line_id
        self.reference = reference

    def image_bytes(self) -> bytes:
        return b""


def build_pieces(lines: Sequence[ReproLine], *, lines_per_piece: int = LINES_PER_PIECE) -> list:
    """Pieces of consecutive lines in file order (validation order), via the B2 harness."""
    return E.build_pieces(
        [_GoldPair(ln.line_id, ln.ref) for ln in lines], lines_per_piece=lines_per_piece
    )


def op_mix(refs: Sequence[str], hyps: Sequence[str]) -> dict[str, int]:
    """Count the edit operations between reference and machine text, by kind.

    The exact alignment's substitutions, deletions (reference characters the
    machine text lacks) and insertions (machine characters the reference lacks),
    with the matched characters — the real error profile the corruption model is
    set beside in the report.
    """
    counts = {"match": 0, "substitution": 0, "deletion": 0, "insertion": 0}
    names = {dp.MATCH: "match", dp.SUB: "substitution", dp.DEL: "deletion", dp.INS: "insertion"}
    for r, h in zip(refs, hyps, strict=True):
        if not r and not h:
            continue
        for kind, _i, _j in dp.align(r, h).ops:
            counts[names[kind]] += 1
    return counts


# --------------------------------------------------------------------------- #
# One level: corrupt, align, grade at every stratum threshold
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class StratumOutcome:
    """Yield and precision at one stratum's threshold, under the factory's gate."""

    stratum: str
    threshold: float
    n_lines: int
    n_minted: int
    n_correct: int
    yield_rate: float
    precision: float
    # the best yield any threshold would give while holding the 95 % gate
    yield_at_gate: float | None
    threshold_at_gate: float | None


@dataclass(slots=True)
class LevelResult:
    """Everything measured at one corruption level."""

    label: str
    target_cer: float | None  # None for the uncorrupted base
    rate: float
    n_ops: int
    cer_written: float  # against the gold, as the strings stand (the B1 scorer)
    cer_folded: float  # after the aligner's normalisation
    n_lines: int
    n_pieces: int
    mean_conf: float
    median_conf: float
    n_correct_any: int  # lines whose slice matches the gold, before any threshold
    by_stratum: dict[str, StratumOutcome] = field(default_factory=dict)


def _level_label(target: float | None) -> str:
    return "base" if target is None else f"cer{round(target * 100):02d}"


def run_level(
    lines: Sequence[ReproLine],
    target: float | None,
    *,
    seed: int = DEFAULT_SEED,
    lines_per_piece: int = LINES_PER_PIECE,
    thresholds: Mapping[str, float] | None = None,
    sample_every: int = 1,
) -> LevelResult:
    """Corrupt the machine text to ``target`` CER, align every piece, grade every line."""
    thresholds = dict(STRATUM_THRESHOLDS if thresholds is None else thresholds)
    refs = [ln.ref for ln in lines]
    hyps = [ln.hyp for ln in lines]
    if target is None:
        rate = 0.0
        corrupted, n_ops = list(hyps), 0
    else:
        rate, _ = calibrate_rate(refs, hyps, target, seed=seed, sample_every=sample_every)
        corrupted, n_ops = corrupt_all(hyps, rate, seed=seed, target=target)
    cer_written = corpus_cer(refs, corrupted)
    cer_folded = corpus_cer(
        [normalize(r, DEFAULT_NORM) for r in refs], [normalize(c, DEFAULT_NORM) for c in corrupted]
    )

    pieces = build_pieces(lines, lines_per_piece=lines_per_piece)
    htr = {ln.line_id: c for ln, c in zip(lines, corrupted, strict=True)}
    cfg = E.EvalConfig(label=_level_label(target), correct_sim=CORRECT_SIM, seed=seed)
    evals = [le for pc in pieces for le in E.evaluate_piece(pc, htr, cfg)]
    confs = [le.align_conf for le in evals]

    by_stratum: dict[str, StratumOutcome] = {}
    for stratum, thr in thresholds.items():
        s = E.summarize(
            evals, replace(cfg, threshold=thr), precision_target=GATE_PRECISION, factory_gate=True
        )
        by_stratum[stratum] = StratumOutcome(
            stratum=stratum,
            threshold=thr,
            n_lines=s.n_lines,
            n_minted=s.n_aligned,
            n_correct=s.n_correct_aligned,
            yield_rate=s.yield_rate,
            precision=s.precision,
            yield_at_gate=s.yield_at_precision,
            threshold_at_gate=s.best_threshold_at_precision,
        )
    return LevelResult(
        label=cfg.label,
        target_cer=target,
        rate=rate,
        n_ops=n_ops,
        cer_written=cer_written,
        cer_folded=cer_folded,
        n_lines=len(evals),
        n_pieces=len(pieces),
        mean_conf=statistics.fmean(confs) if confs else 0.0,
        median_conf=statistics.median(confs) if confs else 0.0,
        n_correct_any=sum(1 for le in evals if le.correct),
        by_stratum=by_stratum,
    )


# --------------------------------------------------------------------------- #
# Break-even
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class BreakEven:
    """Where a metric first falls under its floor along the CER axis.

    ``cer_before`` is the highest tested CER still at or above the floor and
    ``cer_at`` the first below it; ``cer_interpolated`` is the linear crossing
    between the two. ``cer_at`` is ``None`` when the floor holds through the
    whole range; ``cer_before`` is ``None`` when even the base fails it.
    """

    stratum: str
    threshold: float
    metric: str
    floor: float
    cer_before: float | None
    value_before: float | None
    cer_at: float | None
    value_at: float | None
    cer_interpolated: float | None

    def describe(self) -> str:
        if self.cer_at is None:
            assert self.cer_before is not None
            return f"holds through {_pct(self.cer_before)} CER"
        if self.cer_before is None:
            return f"already under the floor at {_pct(self.cer_at)} CER"
        return (
            f"between {_pct(self.cer_before)} and {_pct(self.cer_at)} CER, "
            f"≈ {_pct(self.cer_interpolated)} interpolated"
        )


def break_even(levels: Sequence[LevelResult], stratum: str, metric: str, floor: float) -> BreakEven:
    """Scan the levels by achieved CER and find the first one under ``floor``."""
    ordered = sorted(levels, key=lambda lv: lv.cer_written)
    thr = ordered[0].by_stratum[stratum].threshold
    getter: Callable[[StratumOutcome], float] = (
        (lambda o: o.yield_rate) if metric == "yield" else (lambda o: o.precision)
    )
    prev: tuple[float, float] | None = None
    for lv in ordered:
        val = getter(lv.by_stratum[stratum])
        if val < floor:
            if prev is None:
                return BreakEven(stratum, thr, metric, floor, None, None, lv.cer_written, val, None)
            x0, y0 = prev
            x1, y1 = lv.cer_written, val
            x = x1 if y1 == y0 else x0 + (floor - y0) * (x1 - x0) / (y1 - y0)
            return BreakEven(stratum, thr, metric, floor, x0, y0, x1, y1, x)
        prev = (lv.cer_written, val)
    assert prev is not None
    return BreakEven(stratum, thr, metric, floor, prev[0], prev[1], None, None, None)


# --------------------------------------------------------------------------- #
# The whole run
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ToleranceResult:
    """The report's data: inputs, the real error mix, every level, the break-evens."""

    source: str
    n_lines: int
    n_pieces: int
    lines_per_piece: int
    seed: int
    base_cer: float
    real_op_mix: dict[str, int]
    levels: list[LevelResult]
    break_evens: list[BreakEven]
    generated: str = field(default_factory=lambda: date.today().isoformat())

    def as_dict(self) -> dict:
        d = asdict(self)
        d["model"] = {
            "operations": {
                "substitute": OP_SUBSTITUTE,
                "delete": OP_DELETE,
                "insert": OP_INSERT,
                "merge": OP_MERGE,
                "split_word": OP_SPLIT,
                "space": "always a merged word space",
                "combining_mark": "always a dropped accent",
            },
            "confusions": {k: list(v) for k, v in CONFUSIONS.items()},
            "merges": dict(MERGES),
            "punctuation": list(PUNCTUATION_CONFUSIONS),
        }
        d["floors"] = {"yield": YIELD_FLOOR, "precision": PRECISION_FLOOR}
        d["correct_sim"] = CORRECT_SIM
        return d


def _run_level_job(args: tuple) -> LevelResult:
    lines, target, seed, lpp, thresholds, sample_every = args
    return run_level(
        lines,
        target,
        seed=seed,
        lines_per_piece=lpp,
        thresholds=thresholds,
        sample_every=sample_every,
    )


def run_tolerance(
    lines: Sequence[ReproLine],
    *,
    levels: Sequence[float] = DEFAULT_LEVELS,
    seed: int = DEFAULT_SEED,
    lines_per_piece: int = LINES_PER_PIECE,
    thresholds: Mapping[str, float] | None = None,
    sample_every: int = 1,
    workers: int = 1,
    source: str = str(DEFAULT_LINES),
) -> ToleranceResult:
    """Run the base and every target level; compute the break-evens per stratum."""
    thresholds = dict(STRATUM_THRESHOLDS if thresholds is None else thresholds)
    targets: list[float | None] = [None, *sorted(levels)]
    jobs = [(list(lines), t, seed, lines_per_piece, thresholds, sample_every) for t in targets]
    if workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
            results = list(pool.map(_run_level_job, jobs))
    else:
        results = [_run_level_job(j) for j in jobs]
    refs = [ln.ref for ln in lines]
    hyps = [ln.hyp for ln in lines]
    break_evens = [
        break_even(results, stratum, metric, floor)
        for stratum in thresholds
        for metric, floor in (("yield", YIELD_FLOOR), ("precision", PRECISION_FLOOR))
    ]
    return ToleranceResult(
        source=source,
        n_lines=len(lines),
        n_pieces=results[0].n_pieces if results else 0,
        lines_per_piece=lines_per_piece,
        seed=seed,
        base_cer=results[0].cer_written if results else 0.0,
        real_op_mix=op_mix(refs, hyps),
        levels=results,
        break_evens=break_evens,
    )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _pct(x: float | None, digits: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{digits}f} %"


def _n(x: int) -> str:
    return f"{x:,}"


def _confusion_rows(keys: Sequence[str]) -> str:
    return "; ".join(f"{k} → {', '.join(CONFUSIONS[k])}" for k in keys)


def render_report(res: ToleranceResult) -> str:
    """The Markdown report, every number from ``res``."""
    lv0 = res.levels[0]
    strata = list(lv0.by_stratum)
    out: list[str] = []
    out.append("# Aligner noise tolerance: how much HTR error the factory survives")
    out.append("")
    out.append(
        f"{_n(res.n_lines)} lines of the PHILIUMM validation split in validation order "
        f"(`{res.source}`, the B1 reproduction's recorded machine text, CER "
        f"{_pct(res.base_cer, 2)} against the gold), in {_n(res.n_pieces)} pieces of "
        f"{res.lines_per_piece} consecutive lines; the gold text of each piece, joined with "
        "spaces, stands in for the edition's reading text. At each level the machine text is "
        f"corrupted further (seed {res.seed}; the model below) until its CER against the gold "
        "meets the target, then every piece is aligned by the B2 harness exactly as the factory "
        "aligns a piece. A line is **minted** when it clears the factory's gate at the stratum's "
        "threshold (confidence ≥ threshold, a non-empty slice, no edition-only burst) and "
        f"**correct** when its minted slice matches the line's gold at folded similarity ≥ "
        f"{CORRECT_SIM:.2f}. Yield is minted ÷ all lines; precision is correct ÷ minted. The "
        "confidence is a similarity to the edition text, so the gate that protects precision "
        "here is the same one the Kurrent pilot (Task 4) reads as a ground-truth-free measure "
        "of a reader."
    )
    out.append("")
    out.append("## The corruption model")
    out.append("")
    out.append(
        "Every character of the machine text fires with the level's probability. A fired "
        "letter or digit is replaced by a look-alike from the table below "
        f"({_pct(OP_SUBSTITUTE, 0)}), dropped ({_pct(OP_DELETE, 0)}: a lost letter or minim), "
        f"doubled ({_pct(OP_INSERT, 0)}: a minim too many), merged with the next character "
        f"where the pair is one a cursive hand runs together ({_pct(OP_MERGE, 0)}: *in*, *ni*, "
        "*rn*, *nn* → *m*; *ii* → *u*; *ri* → *n*; *cl* → *d*; *vv*, *uu* → *w*; *li* → *h*; "
        f"*ij* → *y*), or split off from its word by a space ({_pct(OP_SPLIT, 0)}). A fired "
        "space is a merged word space; a fired accent is "
        "dropped; a fired punctuation mark is dropped or swapped. Substitutions are drawn "
        "uniformly from the letter's row. The rate is calibrated per level by bisection; the "
        "achieved CER is measured on all lines with the B1 scorer's edit distance."
    )
    out.append("")
    out.append("| letter | read as |")
    out.append("|---|---|")
    for k, v in CONFUSIONS.items():
        if k.islower():
            out.append(f"| {k} | {', '.join(v)} |")
    caps = [k for k in CONFUSIONS if k.isupper()]
    digs = [k for k in CONFUSIONS if k.isdigit()]
    out.append(f"| capitals | {_confusion_rows(caps)} |")
    out.append(f"| digits | {_confusion_rows(digs)} |")
    out.append("")
    mix = res.real_op_mix
    n_err = mix["substitution"] + mix["deletion"] + mix["insertion"]
    if n_err:
        out.append(
            "For comparison, the recorded machine text's own errors against the gold "
            f"({_n(n_err)} edits on {_n(mix['match'] + mix['substitution'] + mix['deletion'])} "
            f"gold characters) are {_pct(mix['substitution'] / n_err)} substitutions, "
            f"{_pct(mix['deletion'] / n_err)} deletions (gold characters the reader lost) and "
            f"{_pct(mix['insertion'] / n_err)} insertions (characters the reader added)."
        )
        out.append("")
    out.append("## Achieved error per level")
    out.append("")
    out.append(
        "| level | target | rate | operations | CER as written | CER after the aligner's fold | "
        "mean confidence | median | lines correct before any threshold |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for lv in res.levels:
        share = lv.n_correct_any / lv.n_lines if lv.n_lines else 0.0
        out.append(
            f"| {lv.label} | {_pct(lv.target_cer, 0)} | {lv.rate:.4f} | {_n(lv.n_ops)} | "
            f"**{_pct(lv.cer_written)}** | {_pct(lv.cer_folded)} | {lv.mean_conf:.3f} | "
            f"{lv.median_conf:.3f} | {_n(lv.n_correct_any)} ({_pct(share)}) |"
        )
    out.append("")
    out.append("## Yield at the factory's thresholds")
    out.append("")
    head = " | ".join(f"{s} ({lv0.by_stratum[s].threshold:.2f})" for s in strata)
    out.append(f"| level | CER | {head} |")
    out.append("|---|---:|" + "---:|" * len(strata))
    for lv in res.levels:
        cells = " | ".join(
            f"{_pct(lv.by_stratum[s].yield_rate)} ({_n(lv.by_stratum[s].n_minted)})" for s in strata
        )
        out.append(f"| {lv.label} | {_pct(lv.cer_written)} | {cells} |")
    out.append("")
    out.append("## Precision of the minted lines at the factory's thresholds")
    out.append("")
    out.append(f"| level | CER | {head} |")
    out.append("|---|---:|" + "---:|" * len(strata))
    for lv in res.levels:
        cells = " | ".join(
            f"{_pct(lv.by_stratum[s].precision)} ({_n(lv.by_stratum[s].n_correct)})" for s in strata
        )
        out.append(f"| {lv.label} | {_pct(lv.cer_written)} | {cells} |")
    out.append("")
    out.append(
        "The best yield any single threshold would give while holding precision at the 95 % "
        "gate (a sweep in steps of 0.02; the same for every stratum, since the threshold is "
        "the only thing that differs between them):"
    )
    out.append("")
    out.append("| level | CER | yield at ≥ 95 % precision | threshold |")
    out.append("|---|---:|---:|---:|")
    for lv in res.levels:
        o = lv.by_stratum[strata[0]]
        thr = "—" if o.threshold_at_gate is None else f"{o.threshold_at_gate:.2f}"
        out.append(f"| {lv.label} | {_pct(lv.cer_written)} | {_pct(o.yield_at_gate)} | {thr} |")
    out.append("")
    out.append("## Break-even")
    out.append("")
    out.append(
        f"Where yield falls under {_pct(YIELD_FLOOR, 0)} and where precision falls under the "
        f"{_pct(PRECISION_FLOOR, 0)} gate, per stratum threshold, read along the achieved CER "
        "of the levels; the crossing is interpolated linearly between the last level above the "
        "floor and the first below it."
    )
    out.append("")
    out.append(
        f"| stratum (threshold) | yield < {_pct(YIELD_FLOOR, 0)} | "
        f"precision < {_pct(PRECISION_FLOOR, 0)} |"
    )
    out.append("|---|---|---|")
    for s in strata:
        be = {b.metric: b for b in res.break_evens if b.stratum == s}
        out.append(
            f"| {s} ({lv0.by_stratum[s].threshold:.2f}) | {be['yield'].describe()} | "
            f"{be['precision'].describe()} |"
        )
    out.append("")
    out.append("## What this measures, and what it does not")
    out.append("")
    out.append(
        "- The text is Latin and French and the base errors are a Latin-trained reader's; the "
        "corruption adds a cursive hand's confusions to it. German lines are longer-worded and "
        "a Kurrent reader's errors will have their own shape, but the aligner sees only folded "
        "characters, so the character error rate is the quantity that carries over."
    )
    out.append(
        "- The corruption is spread uniformly over the characters. A real reader's errors "
        "cluster on hard lines and hard words: at the same corpus CER, clustered noise leaves "
        "more lines clean (kinder to yield) and ruins others wholesale (harsher on the "
        "boundaries of their neighbours). The uniform case is the smooth middle, not a bound."
    )
    out.append(
        "- The reference is the gold itself joined into one text — the diplomatic upper "
        "bound. A real edition adds its own divergence on top (B2 measured 3 and 6 %), and "
        "pieces the edition omits or interleaves (C2b, P1) are not modelled here."
    )
    out.append(
        "- The thresholds are the factory's, set for the PHILIUMM model's noise. The sweep "
        "table says what a different threshold would buy at each level."
    )
    if n_err:
        out.append(
            "- The model is heavier on substitutions than the recorded errors "
            f"({_pct(OP_SUBSTITUTE, 0)} of fired letters against "
            f"{_pct(mix['substitution'] / n_err)} of the real edits) and lighter on dropped "
            f"characters ({_pct(OP_DELETE, 0)} dropped plus {_pct(OP_MERGE, 0)} merged against "
            f"{_pct(mix['deletion'] / n_err)}). A character the reader drops leaves the spine "
            "and costs the confidence nothing, where a substituted one counts against it; so at "
            "the same CER this noise is the harder case for the gate, and the break-even figures "
            "are on the conservative side."
        )
    out.append("")
    return "\n".join(out)


def write_reports(res: ToleranceResult, out_dir: Path | str) -> tuple[Path, Path]:
    """Write ``align-tolerance.md`` and ``align-tolerance.json`` under ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / "align-tolerance.md"
    js = out_dir / "align-tolerance.json"
    md.write_text(render_report(res), encoding="utf-8")
    js.write_text(json.dumps(res.as_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    return md, js


__all__ = [
    "CONFUSIONS",
    "DEFAULT_LEVELS",
    "DEFAULT_LINES",
    "DEFAULT_OUT_DIR",
    "DEFAULT_SEED",
    "MERGES",
    "BreakEven",
    "LevelResult",
    "ReproLine",
    "StratumOutcome",
    "ToleranceResult",
    "break_even",
    "build_pieces",
    "calibrate_rate",
    "corpus_cer",
    "corrupt_all",
    "corrupt_line",
    "load_repro_lines",
    "op_mix",
    "render_report",
    "run_level",
    "run_tolerance",
    "write_reports",
]
