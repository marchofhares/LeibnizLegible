"""CER / WER with an explicit, documented normalization policy (Phase B1).

The single most important — and most silently abused — knob in HTR evaluation is
*text normalization*. Two papers reporting "8% CER" on the same predictions can
differ by several points purely in how they fold Unicode, whitespace, case, and
diacritics before the edit distance. This module makes that policy a first-class,
named, serialisable object so every number the project publishes carries the
recipe that produced it (SPECS §6: "the benchmark is a deliverable").

Core pieces
-----------
* :class:`NormPolicy` — the frozen recipe (Unicode form, whitespace, case,
  diacritics). Named presets below; :data:`PHILIUMM_POLICY` mirrors how the
  PHILIUMM model was *trained* (``normalization: NFD``, ``normalize_whitespace:
  true`` in its ketos config) so our reproduction is an apples-to-apples compare.
* :func:`edit_distance` — Levenshtein distance (pure Python, no dependency —
  the codebase writes its own primitives rather than pull heavy wheels).
* :func:`score_line` / :class:`LineScore` — per-line edit counts, the atoms both
  the corpus metric and the bootstrap resample over.
* :func:`cer` / :func:`wer` — micro-averaged (sum of edits ÷ sum of reference
  length), the standard corpus aggregation; macro variants provided too.
* :func:`bootstrap_ci` — non-parametric confidence interval by resampling lines,
  deterministic given a seed (scripts here forbid wall-clock RNG).

Everything is unicode-aware and offline; no I/O lives here.
"""

from __future__ import annotations

import random
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Normalization policy
# --------------------------------------------------------------------------- #

# Unicode normal forms we allow (or None to skip Unicode normalization).
_UNICODE_FORMS = frozenset({"NFC", "NFD", "NFKC", "NFKD"})


@dataclass(frozen=True, slots=True)
class NormPolicy:
    """A named, frozen text-normalization recipe applied before edit distance.

    The order of operations is fixed and documented (it matters): Unicode
    normalization → optional diacritic stripping → optional case folding →
    optional whitespace collapse → optional strip. ``name`` is carried into
    reports so a CER number is never divorced from the recipe that made it.

    Attributes:
        unicode_form: one of ``NFC``/``NFD``/``NFKC``/``NFKD`` or ``None``.
        collapse_whitespace: replace every run of whitespace with a single space.
        strip: strip leading/trailing whitespace (after collapse).
        lowercase: Unicode-aware case fold (``str.casefold``).
        strip_diacritics: drop combining marks (implies an internal NFD pass);
            fold "é"→"e", "ﬅ"-style ligatures are *not* touched (that's NFKC).
    """

    name: str
    unicode_form: str | None = "NFC"
    collapse_whitespace: bool = True
    strip: bool = True
    lowercase: bool = False
    strip_diacritics: bool = False

    def __post_init__(self) -> None:
        if self.unicode_form is not None and self.unicode_form not in _UNICODE_FORMS:
            raise ValueError(f"unicode_form must be one of {sorted(_UNICODE_FORMS)} or None")

    def apply(self, text: str) -> str:
        """Normalize ``text`` under this policy (pure, deterministic)."""
        return normalize(text, self)

    def describe(self) -> str:
        """One-line human description for report headers."""
        bits = [self.unicode_form or "no-unicode-norm"]
        if self.strip_diacritics:
            bits.append("strip-diacritics")
        if self.lowercase:
            bits.append("casefold")
        if self.collapse_whitespace:
            bits.append("collapse-ws")
        if self.strip:
            bits.append("strip")
        return " · ".join(bits)


def normalize(text: str, policy: NormPolicy) -> str:
    """Apply a :class:`NormPolicy` to ``text`` (see the class for the fixed order)."""
    if policy.unicode_form is not None:
        text = unicodedata.normalize(policy.unicode_form, text)
    if policy.strip_diacritics:
        # Decompose, drop combining marks, then leave in composed-ish form.
        text = "".join(
            ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)
        )
    if policy.lowercase:
        text = text.casefold()
    if policy.collapse_whitespace:
        text = " ".join(text.split())  # collapses runs to one space and strips ends
    elif policy.strip:
        text = text.strip()
    return text


# --------------------------------------------------------------------------- #
# Named presets (the frozen protocol's menu)
# --------------------------------------------------------------------------- #

# The project's default & headline number: mirrors the model's *training*
# normalization (NFD + whitespace collapse) so "our CER" and "their trained CER"
# are computed on the same footing. Case and diacritics are PRESERVED — a
# transcription that drops accents is genuinely worse, and folding them hides it.
PHILIUMM_POLICY = NormPolicy(
    name="philiumm",
    unicode_form="NFD",
    collapse_whitespace=True,
    strip=True,
    lowercase=False,
    strip_diacritics=False,
)

# A stricter, "how legible is it really" policy that folds case and diacritics —
# always reports a *lower* CER; shown alongside the headline to quantify the gap.
LENIENT_POLICY = NormPolicy(
    name="lenient",
    unicode_form="NFKD",
    collapse_whitespace=True,
    strip=True,
    lowercase=True,
    strip_diacritics=True,
)

# The strictest: NFC, exact whitespace beyond a trailing strip, nothing folded.
# Reports the *highest* CER; the honest upper bound.
STRICT_POLICY = NormPolicy(
    name="strict",
    unicode_form="NFC",
    collapse_whitespace=False,
    strip=True,
    lowercase=False,
    strip_diacritics=False,
)

POLICIES: dict[str, NormPolicy] = {
    p.name: p for p in (PHILIUMM_POLICY, LENIENT_POLICY, STRICT_POLICY)
}


def get_policy(name: str) -> NormPolicy:
    """Look up a named preset, or raise ``KeyError`` with the valid names."""
    try:
        return POLICIES[name]
    except KeyError:
        raise KeyError(f"unknown policy {name!r}; choose from {sorted(POLICIES)}") from None


# --------------------------------------------------------------------------- #
# Edit distance
# --------------------------------------------------------------------------- #


def edit_distance(a: Sequence[object], b: Sequence[object]) -> int:
    """Levenshtein distance between two sequences (unit substitution cost).

    Works on any equatable sequence — a ``str`` (character distance) or a list of
    word tokens (word distance). Two-row DP: O(len(a)·len(b)) time, O(len(b))
    space. Returns the minimum number of insertions/deletions/substitutions to
    turn ``a`` into ``b``.
    """
    if a is b or a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    curr = [0] * (lb + 1)
    for i in range(1, la + 1):
        curr[0] = i
        ai = a[i - 1]
        for j in range(1, lb + 1):
            cost = 0 if ai == b[j - 1] else 1
            curr[j] = min(
                prev[j] + 1,  # deletion
                curr[j - 1] + 1,  # insertion
                prev[j - 1] + cost,  # substitution / match
            )
        prev, curr = curr, prev
    return prev[lb]


# --------------------------------------------------------------------------- #
# Per-line scoring
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LineScore:
    """Edit counts for one (reference, hypothesis) pair under a fixed policy.

    Stores the *normalized* strings actually compared (so per-line dumps show
    exactly what the metric saw) plus the character/word edit counts and
    reference lengths — the atoms :func:`cer`/:func:`wer` and the bootstrap sum.
    """

    line_id: str
    ref: str  # normalized reference
    hyp: str  # normalized hypothesis
    char_edits: int
    ref_chars: int
    word_edits: int
    ref_words: int

    @property
    def cer(self) -> float:
        """Per-line CER (guards an empty reference: 0 edits→0.0, else 1.0)."""
        if self.ref_chars == 0:
            return 0.0 if self.char_edits == 0 else 1.0
        return self.char_edits / self.ref_chars

    @property
    def wer(self) -> float:
        if self.ref_words == 0:
            return 0.0 if self.word_edits == 0 else 1.0
        return self.word_edits / self.ref_words


def score_line(
    reference: str, hypothesis: str, policy: NormPolicy, *, line_id: str = ""
) -> LineScore:
    """Normalize both sides under ``policy`` and compute character/word edits."""
    ref = normalize(reference, policy)
    hyp = normalize(hypothesis, policy)
    ref_words = ref.split()
    hyp_words = hyp.split()
    return LineScore(
        line_id=line_id,
        ref=ref,
        hyp=hyp,
        char_edits=edit_distance(ref, hyp),
        ref_chars=len(ref),
        word_edits=edit_distance(ref_words, hyp_words),
        ref_words=len(ref_words),
    )


# --------------------------------------------------------------------------- #
# Corpus aggregation
# --------------------------------------------------------------------------- #


def cer(scores: Sequence[LineScore]) -> float:
    """Micro-averaged CER: Σ char_edits ÷ Σ ref_chars (the standard aggregation)."""
    total_ref = sum(s.ref_chars for s in scores)
    total_edits = sum(s.char_edits for s in scores)
    if total_ref == 0:
        return 0.0 if total_edits == 0 else 1.0
    return total_edits / total_ref


def wer(scores: Sequence[LineScore]) -> float:
    """Micro-averaged WER: Σ word_edits ÷ Σ ref_words."""
    total_ref = sum(s.ref_words for s in scores)
    total_edits = sum(s.word_edits for s in scores)
    if total_ref == 0:
        return 0.0 if total_edits == 0 else 1.0
    return total_edits / total_ref


def macro_cer(scores: Sequence[LineScore]) -> float:
    """Macro-averaged CER: mean of per-line CER (each line weighted equally).

    Reported alongside micro-CER because they diverge when line lengths vary —
    micro is length-weighted (the honest corpus number); macro reveals whether a
    few long lines are carrying the score.
    """
    return sum(s.cer for s in scores) / len(scores) if scores else 0.0


# --------------------------------------------------------------------------- #
# Bootstrap confidence interval
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Interval:
    """A point estimate with a bootstrap confidence interval (all in [0,1])."""

    point: float
    lo: float
    hi: float
    confidence: float
    n_resamples: int

    def as_pct(self) -> tuple[float, float, float]:
        """(point, lo, hi) as percentages, for report rendering."""
        return (self.point * 100, self.lo * 100, self.hi * 100)


def bootstrap_ci(
    scores: Sequence[LineScore],
    *,
    metric: str = "cer",
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 12345,
) -> Interval:
    """Non-parametric bootstrap CI for a corpus metric by resampling lines.

    Resamples the per-line ``(edits, ref_len)`` atoms with replacement
    ``n_resamples`` times, recomputing the micro-averaged ``metric`` (``"cer"``
    or ``"wer"``) each round, and returns the empirical percentile interval.
    Deterministic given ``seed`` (the harness must be reproducible; wall-clock
    RNG is explicitly disallowed in this project's scripts).
    """
    if metric == "cer":
        atoms = [(s.char_edits, s.ref_chars) for s in scores]
        point = cer(scores)
    elif metric == "wer":
        atoms = [(s.word_edits, s.ref_words) for s in scores]
        point = wer(scores)
    else:  # pragma: no cover - guarded by callers/CLI
        raise ValueError("metric must be 'cer' or 'wer'")

    n = len(atoms)
    if n == 0:
        return Interval(point=0.0, lo=0.0, hi=0.0, confidence=confidence, n_resamples=0)

    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(n_resamples):
        num = 0
        den = 0
        for _ in range(n):
            e, r = atoms[rng.randrange(n)]
            num += e
            den += r
        estimates.append((num / den) if den else (0.0 if num == 0 else 1.0))
    estimates.sort()
    alpha = (1.0 - confidence) / 2.0
    lo = estimates[max(0, int(alpha * n_resamples))]
    hi = estimates[min(n_resamples - 1, int((1.0 - alpha) * n_resamples))]
    return Interval(point=point, lo=lo, hi=hi, confidence=confidence, n_resamples=n_resamples)


__all__ = [
    "LENIENT_POLICY",
    "PHILIUMM_POLICY",
    "POLICIES",
    "STRICT_POLICY",
    "Interval",
    "LineScore",
    "NormPolicy",
    "bootstrap_ci",
    "cer",
    "edit_distance",
    "get_policy",
    "macro_cer",
    "normalize",
    "score_line",
    "wer",
]
