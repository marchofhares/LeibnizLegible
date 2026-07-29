"""Quantitative evaluation of the retro-aligner against known gold (Phase B2).

The gate question — *does retro-alignment yield ≥60% of lines at ≥95%
precision?* — needs a number, and a number needs a ground truth we can check the
aligner against. We have one: the PHILIUMM validation split is real Leibniz line
images with **gold diplomatic transcriptions**, in reading order. That lets us
build a controlled but honest test of the projection mechanism:

* group consecutive val lines into a *piece* (a real multi-line passage);
* form a **reference** = the concatenation of that piece's gold line texts
  (optionally perturbed to model an edition's residual divergence — see
  :func:`build_reference`), a continuous text with no line breaks, exactly like
  an edition reading text;
* run the **real** PHILIUMM HTR over the line images to get noisy machine text;
* align the reference to those HTR lines and project it back onto the lines;
* because we know each line's true reference contribution, we can score every
  projected slice **exactly**: a line is *correct* when its projected edition
  text matches the line's true text.

Then *yield* = fraction of lines the aligner mints (confidence ≥ threshold) and
*precision* = fraction of minted lines that are correct. Sweeping the threshold
traces the yield/precision trade-off the gate is stated in.

What this measures cleanly: the projection mechanism under **real HTR noise**,
with orthographic edition/diplomatic divergence folded away (which the aligner's
normalizer does in reality too). What it does *not* capture — segmentation
errors, apparatus bleed-through, and the true (unmodeled) edition emendations —
is measured by the live end-to-end run (:mod:`leibniz.align.prototype`). The two
together bracket the honest answer; the report states which number is which.

Needs the ``bench`` extra only for the HTR pass; the scoring itself is pure.
"""

from __future__ import annotations

import json
import random
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz.align import dp
from leibniz.align.align import HtrLine, align_piece
from leibniz.align.normalize import DEFAULT_NORM, AlignNorm, normalize


@dataclass(slots=True)
class GoldLine:
    """One evaluation line: its id, gold diplomatic text, and image bytes."""

    line_id: str
    gold: str
    image: bytes


@dataclass(slots=True)
class Piece:
    """A contiguous run of gold lines standing in for one edition piece."""

    piece_id: str
    lines: list[GoldLine]


@dataclass(slots=True)
class LineEval:
    """Per-line outcome after aligning one piece."""

    line_id: str
    gold: str  # true reference text for this line ("" if edition-omitted)
    htr: str
    projected: str  # the aligner's projected edition slice
    align_conf: float
    correct: bool  # projected ≈ true reference for this line
    slice_sim: float  # folded similarity(projected, true)
    mintable: bool = True  # False = this line is absent from the edition text


@dataclass(slots=True)
class EvalConfig:
    """Frozen knobs for one evaluation condition (recorded in the report)."""

    label: str
    ref_char_perturb: float = 0.0  # residual edition divergence, char rate
    ref_drop_rate: float = 0.0  # fraction of lines the edition omits (deletions)
    threshold: float = 0.60
    correct_sim: float = 0.90  # projected is 'correct' if folded sim ≥ this
    seed: int = 20260729
    norm_name: str = DEFAULT_NORM.name


# --------------------------------------------------------------------------- #
# Piece construction
# --------------------------------------------------------------------------- #


def build_pieces(
    pairs: Sequence,
    *,
    lines_per_piece: int = 25,
    max_pieces: int | None = None,
    max_lines: int | None = None,
) -> list[Piece]:
    """Chunk ordered ``LinePair``s (from the val loader) into pieces.

    ``pairs`` are consumed in file order, which the PHILIUMM val split keeps in
    manuscript reading order, so each chunk is a genuine consecutive passage.
    ``max_lines`` caps the HTR work for a fast run.
    """
    pieces: list[Piece] = []
    buf: list[GoldLine] = []
    seen = 0
    for p in pairs:
        if max_lines is not None and seen >= max_lines:
            break
        buf.append(GoldLine(line_id=p.line_id, gold=p.reference, image=p.image_bytes()))
        seen += 1
        if len(buf) >= lines_per_piece:
            pieces.append(Piece(piece_id=f"piece{len(pieces):03d}", lines=buf))
            buf = []
            if max_pieces is not None and len(pieces) >= max_pieces:
                return pieces
    if buf and (max_pieces is None or len(pieces) < max_pieces):
        pieces.append(Piece(piece_id=f"piece{len(pieces):03d}", lines=buf))
    return pieces


# --------------------------------------------------------------------------- #
# Reference construction (the stand-in edition text)
# --------------------------------------------------------------------------- #


def build_reference(
    gold_lines: Sequence[str],
    *,
    char_perturb: float = 0.0,
    drop_rate: float = 0.0,
    seed: int = 0,
) -> tuple[str, list[str], list[bool]]:
    """Build a continuous reference from per-line gold; return truth + mintability.

    With ``char_perturb == 0`` and ``drop_rate == 0`` the reference is the gold
    concatenated with single spaces (the *diplomatic upper bound*: only HTR noise
    stands between the aligner and a perfect split). ``char_perturb`` applies that
    fraction of near-variant character edits to each line, modelling the residual
    divergence a real edition adds *on top of* the orthographic differences the
    normalizer already folds away — an emendation here, an unexpanded brevigraph
    there. ``drop_rate`` **omits** that fraction of lines from the reference
    entirely, modelling manuscript lines the edition does not print (struck-out
    passages, marginalia): the aligner must mint *nothing* for them, so this is
    the condition that actually tests whether confidence protects precision.

    Returns ``(reference, true_lines, mintable)``. ``true_lines[i]`` is the
    (possibly perturbed) text line *i* should receive, or ``""`` if it was
    dropped; ``mintable[i]`` is ``False`` for dropped lines (a correct aligner
    emits nothing for them). Ground truth stays exact under both transforms.
    """
    rng = random.Random(seed)
    kept: list[str] = []
    true_lines: list[str] = []
    mintable: list[bool] = []
    for text in gold_lines:
        if drop_rate > 0 and rng.random() < drop_rate:
            true_lines.append("")
            mintable.append(False)
            continue
        t = _perturb(text, char_perturb, rng) if char_perturb > 0 else text
        true_lines.append(t)
        mintable.append(True)
        kept.append(t)
    return " ".join(kept), true_lines, mintable


_PERTURB_ALPHABET = "aeioutmnrslc"


def _perturb(text: str, rate: float, rng: random.Random) -> str:
    """Apply ~``rate`` per-character near-variant edits (sub/ins/del)."""
    out: list[str] = []
    for ch in text:
        r = rng.random()
        if ch != " " and r < rate:
            kind = rng.random()
            if kind < 0.6:  # substitute a nearby letter
                out.append(rng.choice(_PERTURB_ALPHABET))
            elif kind < 0.8:  # delete
                continue
            else:  # insert then keep
                out.append(rng.choice(_PERTURB_ALPHABET))
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


# --------------------------------------------------------------------------- #
# HTR (real inference, cached)
# --------------------------------------------------------------------------- #


def run_htr_cached(
    pieces: Sequence[Piece], model_path: str, *, cache: Path, batch_size: int = 16
) -> dict[str, str]:
    """Transcribe every line of every piece with the PHILIUMM model, cached.

    Returns ``{line_id: htr_text}``. The HTR pass is the only slow, heavy-stack
    step; its output is cached to ``cache`` (JSON) keyed by line id so re-running
    the evaluation to iterate on the aligner or the report costs no inference.
    """
    cache = Path(cache)
    have: dict[str, str] = {}
    if cache.exists():
        have = json.loads(cache.read_text(encoding="utf-8"))
    todo: list[GoldLine] = [ln for pc in pieces for ln in pc.lines if ln.line_id not in have]
    if todo:
        from leibniz.htr.engines import KrakenEngine

        eng = KrakenEngine(model_path, batch_size=batch_size)
        hyps = eng.transcribe([ln.image for ln in todo])
        for ln, h in zip(todo, hyps, strict=True):
            have[ln.line_id] = h
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
    return have


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


def evaluate_piece(
    piece: Piece,
    htr: dict[str, str],
    cfg: EvalConfig,
    *,
    norm: AlignNorm = DEFAULT_NORM,
) -> list[LineEval]:
    """Align one piece and grade every line against its true reference text."""
    reference, true_lines, mintable = build_reference(
        [ln.gold for ln in piece.lines],
        char_perturb=cfg.ref_char_perturb,
        drop_rate=cfg.ref_drop_rate,
        seed=cfg.seed,
    )
    htr_lines = [HtrLine(ref=ln.line_id, text=htr.get(ln.line_id, "")) for ln in piece.lines]
    result = align_piece(htr_lines, reference, norm=norm, threshold=cfg.threshold)

    out: list[LineEval] = []
    for al, true_text, can_mint in zip(result.lines, true_lines, mintable, strict=True):
        # A dropped line is 'correct' only if the aligner mints nothing for it;
        # a kept line is correct when its projection matches the true text.
        if not can_mint:
            correct = not al.edition_text.strip()
            sim = 1.0 if correct else 0.0
        else:
            sim = dp.similarity(normalize(al.edition_text, norm), normalize(true_text, norm))
            correct = sim >= cfg.correct_sim
        out.append(
            LineEval(
                line_id=al.ref,
                gold=true_text,
                htr=al.htr_text,
                projected=al.edition_text,
                align_conf=al.align_conf,
                correct=correct,
                slice_sim=sim,
                mintable=can_mint,
            )
        )
    return out


@dataclass(slots=True)
class EvalSummary:
    """Aggregate outcome of an evaluation condition over all pieces."""

    label: str
    n_lines: int
    n_mintable: int  # lines actually present in the reference (n_lines − dropped)
    n_aligned: int
    n_correct_aligned: int
    n_false_positive: int  # minted lines the edition never contained (drop test)
    threshold: float
    ref_char_perturb: float
    ref_drop_rate: float
    yield_rate: float  # minted ÷ ALL manuscript lines (the gate's coverage)
    precision: float  # correct ÷ minted
    # yield achievable while holding precision ≥ target, found by threshold sweep
    best_threshold_at_precision: float | None = None
    yield_at_precision: float | None = None
    per_line: list[LineEval] = field(default_factory=list)

    def as_report_dict(self) -> dict:
        d = asdict(self)
        d.pop("per_line")
        return d


def summarize(
    lines: Sequence[LineEval], cfg: EvalConfig, *, precision_target: float = 0.95
) -> EvalSummary:
    """Aggregate per-line evals into yield/precision, plus a threshold sweep.

    ``yield_rate`` (minted ÷ all lines) and ``precision`` (correct ÷ minted) are
    reported at ``cfg.threshold``; the sweep additionally finds the *lowest*
    confidence threshold whose precision still meets ``precision_target`` and
    reports the yield there — i.e. the best yield obtainable at the gate's
    precision bar. ``n_false_positive`` counts minted lines the edition never
    contained (only possible under a drop condition) — the precision killers the
    confidence signal exists to suppress.
    """
    n = len(lines)
    n_mintable = sum(1 for ln in lines if ln.mintable)
    aligned = [ln for ln in lines if ln.align_conf >= cfg.threshold and ln.projected.strip()]
    n_aligned = len(aligned)
    n_correct = sum(1 for ln in aligned if ln.correct)
    n_false_pos = sum(1 for ln in aligned if not ln.mintable)
    yield_rate = n_aligned / n if n else 0.0
    precision = n_correct / n_aligned if n_aligned else 0.0

    best_t: float | None = None
    best_yield: float | None = None
    for t in [i / 100 for i in range(0, 101, 2)]:
        sel = [ln for ln in lines if ln.align_conf >= t and ln.projected.strip()]
        if not sel:
            continue
        prec = sum(1 for ln in sel if ln.correct) / len(sel)
        if prec >= precision_target:
            y = len(sel) / n if n else 0.0
            if best_yield is None or y > best_yield:
                best_yield = y
                best_t = t
    return EvalSummary(
        label=cfg.label,
        n_lines=n,
        n_mintable=n_mintable,
        n_aligned=n_aligned,
        n_correct_aligned=n_correct,
        n_false_positive=n_false_pos,
        threshold=cfg.threshold,
        ref_char_perturb=cfg.ref_char_perturb,
        ref_drop_rate=cfg.ref_drop_rate,
        yield_rate=yield_rate,
        precision=precision,
        best_threshold_at_precision=best_t,
        yield_at_precision=best_yield,
        per_line=list(lines),
    )


__all__ = [
    "EvalConfig",
    "EvalSummary",
    "GoldLine",
    "LineEval",
    "Piece",
    "build_pieces",
    "build_reference",
    "evaluate_piece",
    "run_htr_cached",
    "summarize",
]
