"""Engine-agnostic HTR evaluation harness (Phase B1; deliverable D5).

`leibniz-htr-bench` evaluates *any* line-transcription engine against a held-out
set of ``(line image, reference text)`` pairs under a **frozen, documented
protocol**, so numbers are comparable across engines and across time. Engines are
pluggable adapters (:mod:`leibniz.htr.engines`): a local Kraken model, Claude
vision via the API, or any object satisfying the :class:`Engine` protocol.

This module owns the *orchestration* and the *result object*; the metric math
lives in :mod:`leibniz.htr.metrics`, the data loaders in :mod:`leibniz.htr.data`,
and the adapters in :mod:`leibniz.htr.engines`. Keeping them apart is what lets
the whole thing be unit-tested offline with a trivial fake engine and a handful
of fixture images.

The frozen protocol
-------------------
A published CER is only meaningful with its protocol. :data:`PROTOCOL` pins the
choices that move the number: the default normalization policy, micro-averaging,
the bootstrap settings, and the input contract (pre-segmented single-line
images, one hypothesis per reference, order preserved). Bump
:data:`PROTOCOL_VERSION` only with a note in the report — old numbers stay
attributable to the protocol that produced them.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from leibniz.htr import metrics
from leibniz.htr.metrics import Interval, LineScore, NormPolicy

# --------------------------------------------------------------------------- #
# Frozen protocol
# --------------------------------------------------------------------------- #

PROTOCOL_VERSION = "b1-2026-07"

PROTOCOL: dict[str, object] = {
    "version": PROTOCOL_VERSION,
    "input": "pre-segmented single-line images paired 1:1 with reference text",
    "default_policy": metrics.PHILIUMM_POLICY.name,
    "default_policy_detail": metrics.PHILIUMM_POLICY.describe(),
    "aggregation": "micro-averaged (Σ edits ÷ Σ reference length)",
    "distance": "Levenshtein, unit substitution cost, unicode-codepoint tokens",
    "bootstrap": "1000 resamples of lines with replacement, 95% percentile CI, seed=12345",
    "notes": (
        "Reference text is the GT as distributed; no manual correction. Engine "
        "output is transcribed once, deterministically where the engine allows. "
        "CER/WER preserve case and diacritics under the default policy (folding "
        "them only lowers the number and hides real errors)."
    ),
}


# --------------------------------------------------------------------------- #
# Input contract
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class LinePair:
    """One evaluation atom: a line image and its reference transcription.

    The image is carried either as raw ``bytes`` (e.g. decoded from an HF parquet
    cell) or as a filesystem ``Path`` (a cropped line image on disk). Exactly one
    should be set; :meth:`image_bytes` resolves whichever is present so engines
    receive uniform bytes. ``lang`` is an optional per-line language label
    (``la``/``fr``/``de``/…) used for the per-language breakdown when the GT
    carries it; ``meta`` keeps loader-specific provenance (source file, region).
    """

    line_id: str
    reference: str
    image_bytes_: bytes | None = None
    image_path: Path | None = None
    lang: str | None = None
    meta: dict = field(default_factory=dict)

    def image_bytes(self) -> bytes:
        """Return the line image as bytes, reading from disk if needed."""
        if self.image_bytes_ is not None:
            return self.image_bytes_
        if self.image_path is not None:
            return Path(self.image_path).read_bytes()
        raise ValueError(f"line {self.line_id!r} has neither image bytes nor path")


@runtime_checkable
class Engine(Protocol):
    """A pluggable transcription engine.

    An engine turns a batch of single-line images into a list of transcription
    strings, **one per input, in the same order**. ``name`` and ``version`` are
    recorded in the result and the provenance schema (SPECS §4.5). Adapters may
    do local inference (Kraken) or call a remote API (Claude); the harness treats
    them identically.
    """

    name: str
    version: str

    def transcribe(self, images: Sequence[bytes]) -> list[str]: ...


# --------------------------------------------------------------------------- #
# Result object
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class LangBreakdown:
    """CER/WER for one language subset of the evaluation."""

    lang: str
    n_lines: int
    cer: float
    wer: float


@dataclass(slots=True)
class EvalResult:
    """Everything one evaluation produced — the report's single source of truth."""

    engine: str
    engine_version: str
    policy: NormPolicy
    protocol_version: str
    n_lines: int
    cer: Interval
    wer: Interval
    macro_cer: float
    scores: list[LineScore]
    by_language: list[LangBreakdown]
    seconds: float
    dataset: str = ""

    @property
    def cer_pct(self) -> float:
        return self.cer.point * 100

    @property
    def wer_pct(self) -> float:
        return self.wer.point * 100

    def summary(self) -> str:
        """A one-line headline for the CLI / logs."""
        c = self.cer.as_pct()
        w = self.wer.as_pct()
        return (
            f"{self.engine}@{self.engine_version} on {self.n_lines:,} lines "
            f"[{self.policy.name}]: CER {c[0]:.2f}% (95% CI {c[1]:.2f}–{c[2]:.2f}) · "
            f"WER {w[0]:.2f}% ({w[1]:.2f}–{w[2]:.2f})"
        )

    def worst(self, n: int = 20) -> list[LineScore]:
        """The ``n`` lines with the highest per-line CER — the error-analysis view."""
        return sorted(self.scores, key=lambda s: (-s.cer, -s.ref_chars))[:n]


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #


def _language_breakdown(
    pairs: Sequence[LinePair], scores: Sequence[LineScore]
) -> list[LangBreakdown]:
    """Per-language CER/WER, only for languages that carry a line label."""
    by: dict[str, list[LineScore]] = {}
    for pair, sc in zip(pairs, scores, strict=True):
        if pair.lang:
            by.setdefault(pair.lang, []).append(sc)
    out = [
        LangBreakdown(lang=lang, n_lines=len(ss), cer=metrics.cer(ss), wer=metrics.wer(ss))
        for lang, ss in sorted(by.items())
    ]
    return out


def transcribe_pairs(
    pairs: Sequence[LinePair],
    engine: Engine,
    *,
    batch_size: int = 0,
    monotonic=time.monotonic,
) -> tuple[list[str], float]:
    """Run ``engine`` over the pairs' images and return ``(hypotheses, seconds)``.

    Split out from :func:`evaluate` so an expensive engine (a neural HTR model)
    transcribes **once** and its output can then be scored under several
    normalization policies without re-running inference. ``batch_size`` chunks the
    calls (``0`` = a single call; adapters may batch internally regardless).
    """
    images = [p.image_bytes() for p in pairs]
    t0 = monotonic()
    if batch_size and batch_size > 0:
        hyps: list[str] = []
        for i in range(0, len(images), batch_size):
            hyps.extend(engine.transcribe(images[i : i + batch_size]))
    else:
        hyps = list(engine.transcribe(images))
    seconds = monotonic() - t0
    if len(hyps) != len(pairs):
        raise ValueError(
            f"engine returned {len(hyps)} hypotheses for {len(pairs)} inputs "
            "(an engine must return one transcription per line, in order)"
        )
    return hyps, seconds


def score_hypotheses(
    pairs: Sequence[LinePair],
    hyps: Sequence[str],
    *,
    engine_name: str,
    engine_version: str,
    policy: NormPolicy = metrics.PHILIUMM_POLICY,
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 12345,
    seconds: float = 0.0,
    dataset: str = "",
) -> EvalResult:
    """Score precomputed hypotheses against references under ``policy``.

    Micro-averaged CER/WER with a bootstrap CI; per-line scores retained for
    dumps and error analysis. Deterministic given the inputs and ``seed``.
    """
    scores = [
        metrics.score_line(p.reference, h, policy, line_id=p.line_id)
        for p, h in zip(pairs, hyps, strict=True)
    ]
    return EvalResult(
        engine=engine_name,
        engine_version=engine_version,
        policy=policy,
        protocol_version=PROTOCOL_VERSION,
        n_lines=len(pairs),
        cer=metrics.bootstrap_ci(
            scores, metric="cer", n_resamples=n_resamples, confidence=confidence, seed=seed
        ),
        wer=metrics.bootstrap_ci(
            scores, metric="wer", n_resamples=n_resamples, confidence=confidence, seed=seed
        ),
        macro_cer=metrics.macro_cer(scores),
        scores=scores,
        by_language=_language_breakdown(pairs, scores),
        seconds=seconds,
        dataset=dataset,
    )


def evaluate(
    pairs: Sequence[LinePair],
    engine: Engine,
    *,
    policy: NormPolicy = metrics.PHILIUMM_POLICY,
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 12345,
    batch_size: int = 0,
    dataset: str = "",
    monotonic=time.monotonic,
) -> EvalResult:
    """Transcribe ``pairs`` with ``engine`` and score under the frozen protocol.

    Convenience wrapper over :func:`transcribe_pairs` + :func:`score_hypotheses`
    for the single-policy case (tests, simple runs). Pure orchestration —
    deterministic given a deterministic engine.
    """
    hyps, seconds = transcribe_pairs(pairs, engine, batch_size=batch_size, monotonic=monotonic)
    return score_hypotheses(
        pairs,
        hyps,
        engine_name=engine.name,
        engine_version=engine.version,
        policy=policy,
        n_resamples=n_resamples,
        confidence=confidence,
        seed=seed,
        seconds=seconds,
        dataset=dataset,
    )


# --------------------------------------------------------------------------- #
# Per-line dumps (error analysis)
# --------------------------------------------------------------------------- #


def dump_lines_jsonl(result: EvalResult, path: str | Path) -> None:
    """Write one JSON object per line (id, normalized ref/hyp, edits, CER).

    This is the artifact error analysis actually reads: sortable, greppable, and
    it shows exactly the normalized strings the metric compared (so a surprising
    CER can be traced to a normalization or reference-quality issue, not guessed).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for s in result.scores:
            fh.write(
                json.dumps(
                    {
                        "line_id": s.line_id,
                        "ref": s.ref,
                        "hyp": s.hyp,
                        "char_edits": s.char_edits,
                        "ref_chars": s.ref_chars,
                        "cer": round(s.cer, 4),
                        "word_edits": s.word_edits,
                        "ref_words": s.ref_words,
                        "wer": round(s.wer, 4),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def result_to_dict(result: EvalResult) -> dict:
    """A JSON-serialisable summary of a result (no per-line rows) for run records."""
    return {
        "engine": result.engine,
        "engine_version": result.engine_version,
        "dataset": result.dataset,
        "protocol_version": result.protocol_version,
        "policy": {
            "name": result.policy.name,
            "detail": result.policy.describe(),
        },
        "n_lines": result.n_lines,
        "cer": {"point": result.cer.point, "lo": result.cer.lo, "hi": result.cer.hi},
        "wer": {"point": result.wer.point, "lo": result.wer.lo, "hi": result.wer.hi},
        "macro_cer": result.macro_cer,
        "seconds": result.seconds,
        "by_language": [
            {"lang": b.lang, "n_lines": b.n_lines, "cer": b.cer, "wer": b.wer}
            for b in result.by_language
        ],
    }


# --------------------------------------------------------------------------- #
# A trivial engine for tests / smoke runs
# --------------------------------------------------------------------------- #


class EchoEngine:
    """A degenerate engine that returns a fixed or mapped transcription.

    Useful for offline tests of the harness itself (perfect-score and
    known-error cases) without any model. Maps image bytes → text via a provided
    dict (keyed by bytes), else returns ``default`` for every line.
    """

    name = "echo"
    version = "0"

    def __init__(self, mapping: dict[bytes, str] | None = None, default: str = "") -> None:
        self._mapping = mapping or {}
        self._default = default

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        return [self._mapping.get(img, self._default) for img in images]


def iter_pairs(pairs: Iterable[LinePair]) -> list[LinePair]:
    """Materialise an iterable of pairs into a list (loaders may stream)."""
    return list(pairs)


__all__ = [
    "PROTOCOL",
    "PROTOCOL_VERSION",
    "EchoEngine",
    "Engine",
    "EvalResult",
    "LangBreakdown",
    "LinePair",
    "dump_lines_jsonl",
    "evaluate",
    "iter_pairs",
    "result_to_dict",
    "score_hypotheses",
    "transcribe_pairs",
]
