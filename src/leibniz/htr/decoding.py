"""Decoding a CTC recogniser's posteriors: greedy, a KenLM beam, a prefix beam (Phase R1).

kraken 7 decodes greedily and nothing else. Its hook is clean, though: the
recogniser hands each batch's softmax matrix — ``(N, C, W)``, label 0 the CTC
blank, after ``logits / temperature`` — to a decoder callable and reads back,
per line, ``(label, start, end, confidence)`` tuples which its codec turns into
characters. This module is that callable, three times, behind one interface:

* ``greedy`` — best-path decoding, kraken's own rule restated (argmax per
  frame, runs collapsed, blanks dropped; a character's confidence the highest
  posterior of its run). :class:`~leibniz.htr.engines.KrakenEngine` leaves
  kraken's own function in place for it, so today's text and confidence are
  unchanged bit for bit; the copy here exists for the tests and for matrices
  read back from disk.
* ``beam-lm`` — flashlight-text's lexicon-free beam search with a KenLM
  character n-gram, PyLaia's recipe (Tarride et al., ICDAR 2024): every codec
  label a token, the space among them as ``<space>`` and given to the decoder
  as its silence token, the blank ``<ctc>``; the hypothesis score is the
  path's log-probability plus ``lm_weight`` times the model's log10
  probability of the character sequence, the end of the line included. Needs
  the optional ``decode`` extra (flashlight-text, kenlm, numpy).
* ``prefix-beam`` — a CTC prefix beam search of the project's own, in plain
  Python, over the same n-gram interface (:class:`NGramLM`): the fallback
  where the extra is absent and the reference the tests run. It sums over the
  alignments of a prefix where flashlight keeps the best one, so the two agree
  on the text wherever the posterior is peaked and may differ on a near-tie.

Every decoder returns a :class:`DecodeResult` — the text, the decoder's own
score, and one posterior per character, taken the same way for all three (the
highest posterior of the character's label inside the frames the chosen
alignment gives it) — so a line's confidence is **one function over them**,
:func:`line_confidence`: the mean per-character posterior, SPECS §4.5's
confidence as the pipeline has stored it since C1. Calibration (R1 Task 4)
maps that figure; :func:`retemper` gives the posteriors any other softmax
temperature without a second pass through the network.

The language model's tokens are the codec's characters under a naming rule
(:func:`lm_token`); a model built on folded text (``leibniz bench lm-build
--fold align``) is queried through the same fold, label by label
(:func:`fold_char`), so that a diplomatic reader can be scored by a model of
the edition's regularised spelling without being pushed towards it in case,
accents or u/v.

Pure Python throughout, numpy and flashlight imported lazily by the one
decoder that needs them; importing this module costs nothing.
"""

from __future__ import annotations

import json
import math
import unicodedata
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

BLANK = 0
BLANK_TOKEN = "<ctc>"
SPACE_TOKEN = "<space>"
UNK_TOKEN = "<unk>"
BOS_TOKEN = "<s>"
EOS_TOKEN = "</s>"
LN10 = math.log(10.0)
NEG_INF = float("-inf")
_FLOOR = 1e-30  # a zero posterior's stand-in before the logarithm

GREEDY = "greedy"
BEAM_LM = "beam-lm"
PREFIX_BEAM = "prefix-beam"
KINDS = (GREEDY, BEAM_LM, PREFIX_BEAM)

# PyLaia's recipe as published (lexicon-free, LM weight 1.5) on torchaudio's
# defaults for the flashlight decoder (beam 50, threshold 50, every token
# considered, no silence bonus, hypotheses merged by maximum).
DEFAULT_LM_WEIGHT = 1.5
DEFAULT_BEAM = 50
DEFAULT_BEAM_THRESHOLD = 50.0
# The prefix beam's own pruning: a label enters a frame's candidates when its
# posterior reaches this floor (the blank and the frame's best label always do).
PREFIX_TOKEN_MIN_PROB = 1e-4
PREFIX_BEAM_TOKENS = 12

FOLDS = ("none", "align")


# --------------------------------------------------------------------------- #
# The result, and the one confidence over it
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class DecodeResult:
    """One line as a decoder read it.

    ``score`` is the decoder's own figure, a natural logarithm: for ``greedy``
    the best path's log-probability; for the beams the acoustic log score
    (flashlight: of the best alignment; the prefix beam: of all alignments of
    the text) plus ``lm_weight`` times ``lm_score``, the language model's log10
    probability of the tokens and the end of the line. ``char_scores`` holds one
    posterior in ``[0, 1]`` per label, ``spans`` the first and last frame of
    each; ``n_frames`` lets a caller put the score on a per-frame footing.
    """

    text: str
    score: float
    char_scores: list[float]
    labels: list[int] = field(default_factory=list)
    spans: list[tuple[int, int]] = field(default_factory=list)
    am_score: float | None = None
    lm_score: float | None = None
    n_frames: int = 0

    def as_kraken(self) -> list[tuple[int, int, int, float]]:
        """kraken's decoder output for this line: ``(label, start, end, confidence)``."""
        return [
            (lab, s, e, c)
            for lab, (s, e), c in zip(self.labels, self.spans, self.char_scores, strict=True)
        ]

    def as_tuple(self) -> tuple[str, float, list[float]]:
        """``(text, score, per-character scores)`` — the interface of R1 Task 1."""
        return self.text, self.score, list(self.char_scores)


def line_confidence(result: DecodeResult | Sequence[float] | None) -> float | None:
    """A line's confidence: the mean per-character posterior (SPECS §4.5).

    The same figure whichever decoder read the line; ``None`` for a line
    without characters, as the pipeline has stored it since C1.
    """
    if result is None:
        return None
    scores = result.char_scores if isinstance(result, DecodeResult) else list(result)
    return sum(scores) / len(scores) if scores else None


# --------------------------------------------------------------------------- #
# Posteriors: layouts and temperature
# --------------------------------------------------------------------------- #

Frames = Sequence[Sequence[float]]  # T frames × C labels, probabilities


def frames_of(output, seq_len: int | None = None) -> list[list[float]]:
    """kraken's ``(C, W)`` matrix of one line as ``W`` frames of ``C`` posteriors.

    Takes a torch tensor, a numpy array or nested sequences; ``seq_len`` cuts
    the padding a batch added.
    """
    rows = output.tolist() if hasattr(output, "tolist") else [list(r) for r in output]
    if not rows:
        return []
    width = len(rows[0]) if seq_len is None else min(int(seq_len), len(rows[0]))
    return [[row[t] for row in rows] for t in range(width)]


def retemper(frames: Frames, temperature: float) -> list[list[float]]:
    """The posteriors at another softmax temperature, from the posteriors at 1.

    ``softmax(logits / T)`` equals ``p ** (1 / T)`` renormalised, frame by
    frame, because ``log p`` is the logits up to a constant per frame: a
    calibration sweep needs the network once.
    """
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if temperature == 1.0:
        return [list(f) for f in frames]
    inv = 1.0 / temperature
    out: list[list[float]] = []
    for f in frames:
        powered = [max(p, _FLOOR) ** inv for p in f]
        z = sum(powered)
        out.append([p / z for p in powered])
    return out


def _log(p: float) -> float:
    return math.log(p if p > _FLOOR else _FLOOR)


def _logadd(a: float, b: float) -> float:
    if a == NEG_INF:
        return b
    if b == NEG_INF:
        return a
    hi, lo = (a, b) if a >= b else (b, a)
    return hi + math.log1p(math.exp(lo - hi))


# --------------------------------------------------------------------------- #
# Tokens: the codec's labels as characters and as language-model tokens
# --------------------------------------------------------------------------- #


def lm_token(char: str) -> str:
    """The language model's name for a character (or a codec entry of several).

    The space is ``<space>`` (PyLaia's recipe: the corpus is characters
    separated by spaces); anything KenLM's whitespace tokenizer would split or
    lose — other spaces, control characters, the empty string — is spelled by
    code point, ``<U+00A0>``; every other character is itself.
    """
    if char == " ":
        return SPACE_TOKEN
    reserved = (BLANK_TOKEN, SPACE_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN)
    if (
        not char
        or char in reserved
        or any(c.isspace() or unicodedata.category(c)[0] == "C" for c in char)
    ):
        return "<" + "_".join(f"U+{ord(c):04X}" for c in char) + ">"
    return char


def token_char(name: str) -> str:
    """The inverse of :func:`lm_token` (``<ctc>`` and ``<unk>`` read as the empty string)."""
    if name == SPACE_TOKEN:
        return " "
    if name in (BLANK_TOKEN, UNK_TOKEN):
        return ""
    if name.startswith("<U+") and name.endswith(">"):
        return "".join(chr(int(part[2:], 16)) for part in name[1:-1].split("_") if part)
    return name


def fold_char(char: str, fold: str = "none") -> str | None:
    """A character on the language model's alphabet, or ``None`` where it has none.

    ``none`` keeps the character. ``align`` is the aligner's fold
    (``align/normalize.py``: case, accents, u/v, i/j, long s) applied to the one
    character; a character the fold drops, turns into a space (punctuation) or
    spells with several letters (``&``, ``æ``, ``ß``) has no single token on
    the folded alphabet and is scored as the model's unknown token.
    """
    if fold == "none":
        return char
    if fold != "align":
        raise ValueError(f"unknown fold {fold!r} (known: {', '.join(FOLDS)})")
    if char == " ":
        return " "
    from leibniz.align.normalize import DEFAULT_NORM, normalize_indexed

    folded = normalize_indexed(char, DEFAULT_NORM.with_options(collapse_whitespace=False))[0]
    if len(folded) != 1 or folded.isspace():
        return None
    return folded


@dataclass(slots=True)
class TokenTable:
    """The recogniser's labels, each as the text it writes and as an LM token.

    ``chars[i]`` is what label ``i`` writes (empty for the blank and for a label
    that only occurs inside a multi-label entry of the codec); ``names[i]`` is
    its token in the language model (``<ctc>`` for the blank, ``<unk>`` where
    the model's alphabet has no single token for it).
    """

    chars: list[str]
    names: list[str]
    fold: str = "none"

    def __post_init__(self) -> None:
        if len(self.chars) != len(self.names):
            raise ValueError("chars and names differ in length")
        if not self.chars or self.names[BLANK] != BLANK_TOKEN:
            raise ValueError("label 0 must be the CTC blank")

    def __len__(self) -> int:
        return len(self.chars)

    @property
    def space(self) -> int | None:
        """The label of the space, or ``None`` for a codec without one."""
        try:
            return self.chars.index(" ")
        except ValueError:
            return None

    def text(self, labels: Iterable[int]) -> str:
        return "".join(self.chars[i] for i in labels)

    @classmethod
    def from_chars(cls, chars: Sequence[str], *, fold: str = "none") -> TokenTable:
        """A table for labels ``1..n`` writing ``chars`` (label 0 is added as the blank)."""
        table = [""] + list(chars)
        names = [BLANK_TOKEN]
        for ch in table[1:]:
            folded = fold_char(ch, fold) if ch else None
            names.append(lm_token(folded) if folded else UNK_TOKEN)
        return cls(table, names, fold)

    @classmethod
    def from_codec(cls, codec, *, fold: str = "none") -> TokenTable:
        """A table from a kraken ``PytorchCodec`` (its ``c2l`` map of entry → labels)."""
        c2l = getattr(codec, "c2l", None)
        if not c2l:
            raise ValueError("the codec has no c2l map")
        size = max(max(int(x) for x in labels) for labels in c2l.values() if len(labels)) + 1
        chars = [""] * size
        for entry, labels in c2l.items():
            if len(labels) == 1 and int(labels[0]) != BLANK:
                chars[int(labels[0])] = entry
        return cls.from_chars(chars[1:], fold=fold)

    def write(self, path: Path | str) -> Path:
        """The tokens file: one LM token a line, line ``i`` the token of label ``i``
        (line 0 ``<ctc>``, the space ``<space>``) — the file PyLaia and torchaudio read."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(self.names) + "\n", encoding="utf-8")
        return p

    @classmethod
    def read(cls, path: Path | str, *, fold: str = "none") -> TokenTable:
        """A table from a tokens file. Written without a fold, the file gives the
        characters back exactly; with one, the characters are the folded ones."""
        names = Path(path).read_text(encoding="utf-8").split("\n")
        if names and names[-1] == "":
            names.pop()
        return cls([token_char(n) for n in names], names, fold)


# --------------------------------------------------------------------------- #
# The n-gram interface, and a reader of ARPA files in plain Python
# --------------------------------------------------------------------------- #


@runtime_checkable
class NGramLM(Protocol):
    """A character n-gram as the decoders query it; every score is a log10 probability.

    ``start()`` is the state at the beginning of a line, ``score(state, token)``
    the next state and the token's conditional score, ``finish(state)`` the
    score of the line ending there.
    """

    order: int

    def start(self): ...

    def score(self, state, token: str) -> tuple[object, float]: ...

    def finish(self, state) -> float: ...


class ArpaLM:
    """A backoff n-gram read from an ARPA file, queried in plain Python.

    The reference implementation of :class:`NGramLM`: the same numbers KenLM
    gives (``tests/test_htr_decoding.py`` compares them where kenlm is
    installed), without the dependency. A token the file does not list is
    scored as ``<unk>``; a file without ``<unk>`` scores it at ``unk_floor``.
    """

    def __init__(
        self,
        ngrams: dict[tuple[str, ...], tuple[float, float]],
        order: int,
        *,
        unk_floor: float = -100.0,
    ) -> None:
        self.ngrams = ngrams
        self.order = order
        self.unk_floor = unk_floor
        self.vocab = {ng[0] for ng in ngrams if len(ng) == 1}

    @classmethod
    def load(cls, path: Path | str) -> ArpaLM:
        ngrams: dict[tuple[str, ...], tuple[float, float]] = {}
        order = 0
        n = 0
        with Path(path).open(encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if not line.strip():
                    continue
                if line.startswith("\\"):
                    head = line.strip()
                    if head.endswith("-grams:"):
                        n = int(head[1:].split("-", 1)[0])
                        order = max(order, n)
                    else:
                        n = 0
                    continue
                if n == 0:
                    continue
                parts = line.split("\t")
                words = tuple(parts[1].split(" "))
                backoff = float(parts[2]) if len(parts) > 2 and parts[2].strip() else 0.0
                ngrams[words] = (float(parts[0]), backoff)
        if not ngrams:
            raise ValueError(f"no n-grams read from {path}")
        return cls(ngrams, order)

    def start(self) -> tuple[str, ...]:
        return (BOS_TOKEN,)

    def _logp(self, context: tuple[str, ...], word: str) -> float:
        backoff = 0.0
        ctx = context
        while True:
            hit = self.ngrams.get(ctx + (word,))
            if hit is not None:
                return backoff + hit[0]
            if not ctx:
                return backoff + self.unk_floor
            ctx_hit = self.ngrams.get(ctx)
            if ctx_hit is not None:
                backoff += ctx_hit[1]
            ctx = ctx[1:]

    def score(self, state: tuple[str, ...], token: str) -> tuple[tuple[str, ...], float]:
        word = token if token in self.vocab else UNK_TOKEN
        ctx = state[-(self.order - 1) :] if self.order > 1 else ()
        new = (ctx + (word,))[-(self.order - 1) :] if self.order > 1 else ()
        return new, self._logp(ctx, word)

    def finish(self, state: tuple[str, ...]) -> float:
        ctx = state[-(self.order - 1) :] if self.order > 1 else ()
        return self._logp(ctx, EOS_TOKEN)

    def sentence(self, tokens: Sequence[str]) -> float:
        """log10 probability of a whole line, its end included."""
        state = self.start()
        total = 0.0
        for tok in tokens:
            state, s = self.score(state, tok)
            total += s
        return total + self.finish(state)


class KenLMModel:
    """The same interface over the ``kenlm`` module (ARPA or binary), where installed."""

    def __init__(self, path: Path | str) -> None:
        import kenlm  # the optional ``decode`` extra

        self._kenlm = kenlm
        self.model = kenlm.Model(str(path))
        self.order = int(self.model.order)

    def start(self):
        state = self._kenlm.State()
        self.model.BeginSentenceWrite(state)
        return state

    def score(self, state, token: str):
        out = self._kenlm.State()
        return out, float(self.model.BaseScore(state, token, out))

    def finish(self, state) -> float:
        out = self._kenlm.State()
        return float(self.model.BaseScore(state, EOS_TOKEN, out))


def load_lm(path: Path | str) -> NGramLM:
    """An n-gram for the prefix beam: kenlm where it is installed, else the ARPA reader
    (which cannot read a binary file and says so)."""
    p = Path(path)
    try:
        return KenLMModel(p)
    except ModuleNotFoundError:
        pass
    if p.suffix != ".arpa":
        arpa = p.with_suffix(".arpa")
        if not arpa.exists():
            raise ModuleNotFoundError(
                f"{p} is a KenLM binary and the kenlm module is not installed (the optional "
                "`decode` extra); the ARPA file beside it would do, and is missing"
            )
        p = arpa
    return ArpaLM.load(p)


# --------------------------------------------------------------------------- #
# Paths: from frame labels to characters, and the best alignment of a text
# --------------------------------------------------------------------------- #


def path_chars(
    path: Sequence[int], frames: Frames, *, offset: int = 0
) -> tuple[list[int], list[tuple[int, int]], list[float]]:
    """Collapse a frame-by-frame label path: the labels, their frame spans and, per
    label, the highest posterior of that label inside its span (kraken's rule)."""
    labels: list[int] = []
    spans: list[tuple[int, int]] = []
    scores: list[float] = []
    prev = BLANK
    for t, lab in enumerate(path):
        if lab != BLANK:
            p = float(frames[t][lab])
            if lab == prev:
                spans[-1] = (spans[-1][0], t + offset)
                if p > scores[-1]:
                    scores[-1] = p
            else:
                labels.append(lab)
                spans.append((t + offset, t + offset))
                scores.append(p)
        prev = lab
    return labels, spans, scores


def greedy_path(frames: Frames) -> list[int]:
    """The best label of every frame (the first of equals, as ``torch.max`` returns it)."""
    path = []
    for f in frames:
        best, best_p = 0, f[0]
        for i in range(1, len(f)):
            if f[i] > best_p:
                best, best_p = i, f[i]
        path.append(best)
    return path


def forced_path(frames: Frames, labels: Sequence[int]) -> list[int] | None:
    """The most probable CTC alignment of ``labels`` to the frames, as a label per
    frame; ``None`` when the frames cannot carry the labels (too few of them)."""
    n_frames = len(frames)
    if not labels:
        return [BLANK] * n_frames
    ext: list[int] = [BLANK]
    for lab in labels:
        ext.extend((lab, BLANK))
    n_states = len(ext)
    score = [NEG_INF] * n_states
    back: list[list[int]] = []
    if n_frames == 0:
        return None
    score[0] = _log(frames[0][BLANK])
    score[1] = _log(frames[0][ext[1]])
    back.append([0] * n_states)
    for t in range(1, n_frames):
        f = frames[t]
        new = [NEG_INF] * n_states
        ptr = [0] * n_states
        for s in range(n_states):
            best, arg = score[s], s
            if s >= 1 and score[s - 1] > best:
                best, arg = score[s - 1], s - 1
            if s >= 2 and ext[s] != BLANK and ext[s] != ext[s - 2] and score[s - 2] > best:
                best, arg = score[s - 2], s - 2
            if best > NEG_INF:
                new[s] = best + _log(f[ext[s]])
                ptr[s] = arg
        score = new
        back.append(ptr)
    end = n_states - 1 if score[n_states - 1] >= score[n_states - 2] else n_states - 2
    if score[end] == NEG_INF:
        return None
    path = [BLANK] * n_frames
    s = end
    for t in range(n_frames - 1, -1, -1):
        path[t] = ext[s]
        s = back[t][s]
    return path


# --------------------------------------------------------------------------- #
# The three decoders over one line's frames
# --------------------------------------------------------------------------- #


def decode_greedy(frames: Frames, table: TokenTable | None = None) -> DecodeResult:
    """Best-path decoding (kraken's ``greedy_decoder``, restated)."""
    path = greedy_path(frames)
    labels, spans, scores = path_chars(path, frames)
    am = sum(_log(float(frames[t][lab])) for t, lab in enumerate(path))
    return DecodeResult(
        text=table.text(labels) if table is not None else "",
        score=am,
        char_scores=scores,
        labels=labels,
        spans=spans,
        am_score=am,
        lm_score=None,
        n_frames=len(frames),
    )


def _candidates(frame: Sequence[float], *, min_prob: float, top: int) -> list[int]:
    """The labels a frame offers the prefix beam: the blank, the frame's best, and up
    to ``top`` labels at or above ``min_prob``."""
    idx = [i for i, p in enumerate(frame) if i != BLANK and p >= min_prob]
    if len(idx) > top:
        idx = sorted(idx, key=lambda i: -frame[i])[:top]
    if not idx and len(frame) > 1:
        idx = [max(range(1, len(frame)), key=lambda i: frame[i])]
    return idx


def decode_prefix_beam(
    frames: Frames,
    table: TokenTable,
    lm: NGramLM | None = None,
    *,
    lm_weight: float = DEFAULT_LM_WEIGHT,
    beam: int = DEFAULT_BEAM,
    token_min_prob: float = PREFIX_TOKEN_MIN_PROB,
    beam_tokens: int = PREFIX_BEAM_TOKENS,
) -> DecodeResult:
    """CTC prefix beam search with an optional character n-gram.

    Each kept prefix carries the log-probability of its alignments ending in a
    blank and ending in its last label; a prefix's rank is their sum plus
    ``lm_weight`` times the model's log10 probability of its tokens. At the
    end the model's end-of-line score is added. Without a model the search
    ranks by the CTC probability alone.
    """
    # prefix → [log p ending in blank, log p ending in a label, LM state, LM log10 sum]
    beams: dict[tuple[int, ...], list] = {(): [0.0, NEG_INF, lm.start() if lm else None, 0.0]}
    for frame in frames:
        log_blank = _log(frame[BLANK])
        cands = [
            (c, _log(frame[c]))
            for c in _candidates(frame, min_prob=token_min_prob, top=beam_tokens)
        ]
        nxt: dict[tuple[int, ...], list] = {}
        for prefix, (pb, pnb, state, lm_sum) in beams.items():
            total = _logadd(pb, pnb)
            slot = nxt.get(prefix)
            if slot is None:
                slot = nxt[prefix] = [NEG_INF, NEG_INF, state, lm_sum]
            slot[0] = _logadd(slot[0], total + log_blank)
            last = prefix[-1] if prefix else None
            for c, lp in cands:
                if c == last:
                    slot[1] = _logadd(slot[1], pnb + lp)  # the same label held
                    reach = pb + lp  # a new one only across a blank
                else:
                    reach = total + lp
                if reach == NEG_INF:
                    continue
                new = prefix + (c,)
                ext = nxt.get(new)
                if ext is None:
                    if lm is not None:
                        new_state, s = lm.score(state, table.names[c])
                        ext = nxt[new] = [NEG_INF, NEG_INF, new_state, lm_sum + s]
                    else:
                        ext = nxt[new] = [NEG_INF, NEG_INF, None, 0.0]
                ext[1] = _logadd(ext[1], reach)
        ranked = sorted(
            nxt.items(),
            key=lambda kv: _logadd(kv[1][0], kv[1][1]) + lm_weight * kv[1][3],
            reverse=True,
        )
        beams = dict(ranked[:beam])
    best: tuple[int, ...] = ()
    best_total = NEG_INF
    best_am = NEG_INF
    best_lm = 0.0
    for prefix, (pb, pnb, state, lm_sum) in beams.items():
        am = _logadd(pb, pnb)
        lm_all = lm_sum + (lm.finish(state) if lm is not None else 0.0)
        total = am + lm_weight * lm_all
        if total > best_total:
            best, best_total, best_am, best_lm = prefix, total, am, lm_all
    path = forced_path(frames, best)
    if path is None:  # cannot happen for a prefix the frames produced; stay honest if it does
        labels, spans, scores = list(best), [(0, 0)] * len(best), [0.0] * len(best)
    else:
        labels, spans, scores = path_chars(path, frames)
    return DecodeResult(
        text=table.text(labels),
        score=best_total,
        char_scores=scores,
        labels=labels,
        spans=spans,
        am_score=best_am,
        lm_score=best_lm if lm is not None else None,
        n_frames=len(frames),
    )


class FlashlightBeam:
    """flashlight-text's lexicon-free decoder with a KenLM model (the ``decode`` extra).

    The tokens are the table's names in label order, the blank label 0, the
    space the decoder's silence token (PyLaia's ``sil_token="<space>"``);
    flashlight's KenLM is LGPL code inside its wheel, linked, never copied
    here. Without ``lm_path`` the decoder runs on flashlight's ``ZeroLM``.
    """

    def __init__(
        self,
        table: TokenTable,
        lm_path: Path | str | None,
        *,
        lm_weight: float = DEFAULT_LM_WEIGHT,
        beam: int = DEFAULT_BEAM,
        beam_tokens: int | None = None,
        beam_threshold: float = DEFAULT_BEAM_THRESHOLD,
        sil_score: float = 0.0,
        log_add: bool = False,
    ) -> None:
        try:
            import numpy as np
            from flashlight.lib.text.decoder import (
                CriterionType,
                LexiconFreeDecoder,
                LexiconFreeDecoderOptions,
                ZeroLM,
            )
            from flashlight.lib.text.dictionary import Dictionary
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "the beam-lm decoder needs flashlight-text, kenlm and numpy (the optional "
                "`decode` extra: `uv sync --extra bench --extra decode`); the prefix-beam "
                "decoder runs without them"
            ) from exc
        if table.space is None:
            raise ValueError("the codec has no space: the lexicon-free decoder needs one")
        self._np = np
        self.table = table
        dictionary = Dictionary()
        for i, name in enumerate(table.names):
            dictionary.add_entry(name, i)
        if lm_path is not None:
            from flashlight.lib.text.decoder.kenlm import KenLM

            self._lm = KenLM(str(lm_path), dictionary)
        else:
            self._lm = ZeroLM()
        options = LexiconFreeDecoderOptions(
            int(beam),
            int(beam_tokens or len(table)),
            float(beam_threshold),
            float(lm_weight),
            float(sil_score),
            bool(log_add),
            CriterionType.CTC,
        )
        # The decoder keeps a reference to the LM it was built with only in C++:
        # hold it here too (torchaudio issue 3218).
        self._decoder = LexiconFreeDecoder(options, self._lm, table.space, BLANK, [])
        self.has_lm = lm_path is not None

    def decode(self, frames: Frames) -> DecodeResult:
        np = self._np
        probs = np.asarray(frames, dtype=np.float64)
        if probs.ndim != 2 or probs.shape[0] == 0:
            return DecodeResult("", 0.0, [], n_frames=0)
        emissions = np.ascontiguousarray(np.log(np.maximum(probs, _FLOOR)), dtype=np.float32)
        n_frames, n_tokens = emissions.shape
        results = self._decoder.decode(emissions.ctypes.data, n_frames, n_tokens)
        if not results:
            return decode_greedy(frames, self.table)
        best = results[0]
        # flashlight's tokens: the start silence, one label per frame, the end silence.
        path = [int(t) for t in best.tokens][1 : n_frames + 1]
        path = [BLANK if t < 0 else t for t in path]
        labels, spans, scores = path_chars(path, frames)
        return DecodeResult(
            text=self.table.text(labels),
            score=float(best.score),
            char_scores=scores,
            labels=labels,
            spans=spans,
            am_score=float(best.emittingModelScore),
            lm_score=float(best.lmScore) if self.has_lm else None,
            n_frames=n_frames,
        )


# --------------------------------------------------------------------------- #
# One interface: the Decoder kraken calls, and the spec an engine builds it from
# --------------------------------------------------------------------------- #


class Decoder:
    """A decoder behind one interface, and kraken's decoder callable.

    ``decode(output, seq_len)`` reads one line from kraken's ``(C, W)`` matrix,
    ``decode_frames`` from ``W × C`` frames; calling the object on a batch
    (``(N, C, W)`` and the lengths) answers in kraken's own shape and keeps the
    batch's :class:`DecodeResult`s in :attr:`last`, where the engine reads the
    scores kraken's tuples have no room for.
    """

    def __init__(
        self,
        kind: str = GREEDY,
        table: TokenTable | None = None,
        *,
        lm: Path | str | NGramLM | None = None,
        lm_weight: float = DEFAULT_LM_WEIGHT,
        beam: int = DEFAULT_BEAM,
        beam_tokens: int | None = None,
        beam_threshold: float = DEFAULT_BEAM_THRESHOLD,
        temperature: float = 1.0,
    ) -> None:
        if kind not in KINDS:
            raise ValueError(f"unknown decoder {kind!r} (known: {', '.join(KINDS)})")
        if kind != GREEDY and table is None:
            raise ValueError(f"the {kind} decoder needs the codec's tokens")
        self.kind = kind
        self.table = table
        self.lm_path = str(lm) if isinstance(lm, (str, Path)) else None
        self.lm_weight = lm_weight
        self.beam = beam
        self.beam_tokens = beam_tokens
        self.beam_threshold = beam_threshold
        # A second temperature, applied to the posteriors as handed over (the
        # network's own softmax temperature is the engine's; 1.0 leaves them).
        self.temperature = temperature
        self.last: list[DecodeResult] = []
        self._flashlight: FlashlightBeam | None = None
        self._lm: NGramLM | None = None
        if kind == BEAM_LM:
            if lm is not None and not isinstance(lm, (str, Path)):
                raise ValueError("beam-lm takes the path of a KenLM file")
            self._flashlight = FlashlightBeam(
                table,  # type: ignore[arg-type]
                lm,
                lm_weight=lm_weight,
                beam=beam,
                beam_tokens=beam_tokens,
                beam_threshold=beam_threshold,
            )
        elif kind == PREFIX_BEAM and lm is not None:
            self._lm = load_lm(lm) if isinstance(lm, (str, Path)) else lm

    # -- one line ----------------------------------------------------------- #

    def decode_frames(self, frames: Frames) -> DecodeResult:
        if self.temperature != 1.0:
            frames = retemper(frames, self.temperature)
        if self.kind == GREEDY:
            return decode_greedy(frames, self.table)
        if self.kind == BEAM_LM:
            assert self._flashlight is not None
            return self._flashlight.decode(frames)
        assert self.table is not None
        return decode_prefix_beam(
            frames,
            self.table,
            self._lm,
            lm_weight=self.lm_weight,
            beam=self.beam,
            beam_tokens=self.beam_tokens or PREFIX_BEAM_TOKENS,
        )

    def decode(self, output, seq_len: int | None = None) -> DecodeResult:
        return self.decode_frames(frames_of(output, seq_len))

    # -- kraken's protocol --------------------------------------------------- #

    def __call__(self, outputs, seq_lens=None) -> list[list[tuple[int, int, int, float]]]:
        shape = getattr(outputs, "shape", None)
        if shape is not None and len(shape) == 2:
            lines = [outputs]
        else:
            lines = list(outputs)
        if seq_lens is None:
            if len(lines) != 1:
                raise ValueError("seq_lens need to be set for batch decoding.")
            lens: list[int | None] = [None]
        else:
            lens = [
                int(x) for x in (seq_lens.tolist() if hasattr(seq_lens, "tolist") else seq_lens)
            ]
        self.last = [self.decode(line, n) for line, n in zip(lines, lens, strict=True)]
        return [r.as_kraken() for r in self.last]

    def params(self) -> dict:
        """The settings as a run's record carries them (``runs.params``)."""
        out: dict = {"decoder": self.kind}
        if self.kind != GREEDY:
            out.update(
                {
                    "lm": self.lm_path,
                    "lm_weight": self.lm_weight,
                    "beam": self.beam,
                    "fold": self.table.fold if self.table else "none",
                }
            )
            if self.kind == BEAM_LM:
                out["beam_threshold"] = self.beam_threshold
            if self.beam_tokens:
                out["beam_tokens"] = self.beam_tokens
        if self.temperature != 1.0:
            out["decoder_temperature"] = self.temperature
        return out


@dataclass(frozen=True, slots=True)
class DecoderSpec:
    """What the command line says about decoding, before a model's codec is known.

    ``build(codec)`` makes the :class:`Decoder` once the recogniser is loaded;
    the fold comes from the language model's sidecar (``<lm>.json``, written by
    ``leibniz bench lm-build``) unless given.
    """

    kind: str = GREEDY
    lm: str | None = None
    lm_weight: float = DEFAULT_LM_WEIGHT
    beam: int = DEFAULT_BEAM
    fold: str | None = None
    beam_tokens: int | None = None  # labels considered per frame (None: the decoder's default)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown decoder {self.kind!r} (known: {', '.join(KINDS)})")
        if self.kind == BEAM_LM and not self.lm:
            raise ValueError("--decoder beam-lm needs --lm PATH (a KenLM file)")

    @property
    def is_greedy(self) -> bool:
        return self.kind == GREEDY

    @property
    def suffix(self) -> str:
        """What a reader's key gains under this decoder (``""`` for greedy), so that
        its readings never share a file with the greedy ones."""
        return "" if self.is_greedy else f"+{self.kind}"

    def resolved_fold(self) -> str:
        if self.fold:
            return self.fold
        meta = lm_meta(self.lm) if self.lm else None
        return str((meta or {}).get("fold") or "none")

    def build(self, codec=None, *, table: TokenTable | None = None) -> Decoder:
        if self.is_greedy:
            return Decoder(GREEDY, table)
        if table is None:
            if codec is None:
                raise ValueError(f"the {self.kind} decoder needs the model's codec")
            table = TokenTable.from_codec(codec, fold=self.resolved_fold())
        return Decoder(
            self.kind,
            table,
            lm=self.lm,
            lm_weight=self.lm_weight,
            beam=self.beam,
            beam_tokens=self.beam_tokens,
        )

    def params(self) -> dict:
        out: dict = {"decoder": self.kind}
        if not self.is_greedy:
            out.update(
                {
                    "lm": self.lm,
                    "lm_weight": self.lm_weight,
                    "beam": self.beam,
                    "fold": self.resolved_fold(),
                }
            )
            if self.beam_tokens:
                out["beam_tokens"] = self.beam_tokens
        return out


def lm_meta(path: Path | str | None) -> dict | None:
    """The sidecar ``leibniz bench lm-build`` writes beside a model (``<stem>.json``:
    the order, the fold, the text it saw), or ``None``."""
    if not path:
        return None
    p = Path(path)
    for cand in (p.with_suffix(".json"), Path(str(p) + ".json")):
        if cand.exists():
            try:
                return json.loads(cand.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def spec_from_options(
    decoder: str | None,
    lm: Path | str | None = None,
    lm_weight: float | None = None,
    beam: int | None = None,
    *,
    beam_tokens: int | None = None,
    error: Callable[[str], Exception] = ValueError,
) -> DecoderSpec:
    """The spec of ``--decoder … --lm … --lm-weight … --beam …``, with the errors a
    command line should give."""
    kind = (decoder or GREEDY).strip().lower()
    if kind not in KINDS:
        raise error(f"unknown --decoder {decoder!r} ({' | '.join(KINDS)})")
    if kind == GREEDY:
        if lm is not None:
            raise error("--lm needs --decoder beam-lm or prefix-beam")
        return DecoderSpec()
    if kind == BEAM_LM and lm is None:
        raise error("--decoder beam-lm needs --lm PATH (a KenLM file)")
    if lm is not None and not Path(lm).exists():
        raise error(f"--lm {lm}: no such file")
    return DecoderSpec(
        kind=kind,
        lm=str(lm) if lm is not None else None,
        lm_weight=DEFAULT_LM_WEIGHT if lm_weight is None else float(lm_weight),
        beam=DEFAULT_BEAM if beam is None else int(beam),
        beam_tokens=int(beam_tokens) if beam_tokens else None,
    )


__all__ = [
    "BEAM_LM",
    "BLANK",
    "BLANK_TOKEN",
    "DEFAULT_BEAM",
    "DEFAULT_LM_WEIGHT",
    "FOLDS",
    "GREEDY",
    "KINDS",
    "PREFIX_BEAM",
    "SPACE_TOKEN",
    "UNK_TOKEN",
    "ArpaLM",
    "DecodeResult",
    "Decoder",
    "DecoderSpec",
    "FlashlightBeam",
    "KenLMModel",
    "NGramLM",
    "TokenTable",
    "decode_greedy",
    "decode_prefix_beam",
    "fold_char",
    "forced_path",
    "frames_of",
    "greedy_path",
    "line_confidence",
    "lm_meta",
    "lm_token",
    "load_lm",
    "path_chars",
    "retemper",
    "spec_from_options",
    "token_char",
]
