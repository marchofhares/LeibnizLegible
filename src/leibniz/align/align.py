"""Retro-alignment: project edition reading text onto HTR line images (Phase B2).

This is the core of the ground-truth-factory bet (SPECS §1.4, §6): if a
§70-expired edition's *reading text* can be split back onto the manuscript lines
it transcribes, every (line image, edition text) pair becomes a training example
— the way the Bullinger project minted 165k lines.

The method is **forced alignment by boundary projection**:

1. Concatenate the HTR machine text of the manuscript lines, in reading order,
   into one "spine", remembering which line every character came from. This
   spine carries the line structure (the manuscript knows where each line ends);
   the edition text does not.
2. Fold both the spine and the edition text to the lossy comparison alphabet
   (:mod:`leibniz.align.normalize`), so the edition's silent expansions and
   orthographic regularisation stop looking like errors.
3. Globally align the two folded strings (:mod:`leibniz.align.dp`), free at the
   ends so an over- or under-extracted edition passage overhangs harmlessly.
4. Walk the alignment: each edition character inherits the manuscript line of the
   HTR character it lands on. That partitions the edition text at the line
   boundaries — and, via the folded→original offset map, we hand back a slice of
   the **original** edition text (accents and capitals intact) per line.
5. Score each line by the fraction of its HTR characters the alignment actually
   matched; threshold it to decide which pairs are trustworthy enough to mint.

Emitting the *original* edition slice (not the folded one) matters: the folded
form is only a matching device; the ground truth we keep is the edition's own
constituted text.

Everything here is pure and offline; the HTR text and edition text come in as
strings, so the aligner is tested without models or images.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from leibniz.align import dp
from leibniz.align.normalize import DEFAULT_NORM, AlignNorm, normalize_indexed

# Characters that, at the end of an HTR line, signal a word split across the line
# break (so the fragments should be rejoined without a word boundary). Early-
# modern hyphens are various; also handles the double-oblique "=" convention.
_HYPHENS = ("-", "¬", "=", "‐", "‑", "­")

# Default: a line must have at least this fraction of its characters matched by
# the alignment to be minted. Tuned on the B2 eval; overridable per call/run.
DEFAULT_THRESHOLD = 0.60


@dataclass(slots=True)
class HtrLine:
    """One segmented manuscript line: its image reference and HTR machine text."""

    ref: str  # image reference: canonical line id, or a local path
    text: str  # HTR output (diplomatic, noisy)
    meta: dict = field(default_factory=dict)


@dataclass(slots=True)
class AlignedLine:
    """A manuscript line with the edition text projected onto it.

    ``edition_text`` is a slice of the *original* edition string (the minted
    ground truth). ``align_conf`` is the fraction of the line's folded HTR
    characters the global alignment matched exactly — the gate/threshold signal.
    """

    ref: str
    htr_text: str
    edition_text: str
    align_conf: float
    n_htr_chars: int  # folded HTR length (the confidence denominator)
    n_matched: int  # folded HTR chars matched exactly to the edition
    aligned: bool  # align_conf >= threshold

    @property
    def edition_text_stripped(self) -> str:
        return self.edition_text.strip()


@dataclass(slots=True)
class AlignmentResult:
    """The per-line alignment of one piece (a letter / a run of pages)."""

    lines: list[AlignedLine]
    threshold: float
    norm_name: str
    global_distance: int
    edition_chars: int

    @property
    def n_lines(self) -> int:
        return len(self.lines)

    @property
    def n_aligned(self) -> int:
        return sum(1 for ln in self.lines if ln.aligned)

    @property
    def yield_rate(self) -> float:
        """Fraction of manuscript lines minted (aligned above threshold)."""
        return self.n_aligned / self.n_lines if self.lines else 0.0

    def aligned_lines(self) -> list[AlignedLine]:
        return [ln for ln in self.lines if ln.aligned]


def align_piece(
    htr_lines: Sequence[HtrLine],
    edition_text: str,
    *,
    norm: AlignNorm = DEFAULT_NORM,
    threshold: float = DEFAULT_THRESHOLD,
    free_edition_ends: bool = True,
    free_htr_ends: bool = False,
    dehyphenate: bool = True,
) -> AlignmentResult:
    """Align one edition passage to an ordered list of HTR lines.

    ``htr_lines`` must already be in manuscript reading order (across pages, if
    the piece spans several). ``edition_text`` is the constituted reading text
    for exactly that extent. Returns per-line projected edition slices with
    confidences; ``threshold`` decides the ``aligned`` flag and the yield.

    ``free_edition_ends`` frees the edition (``b``) overhang, so an
    over-extracted edition passage hangs off the ends for free — the common,
    safe case. **Do not enable both** ``free_edition_ends`` and ``free_htr_ends``
    together: with every end free the optimal alignment is the degenerate
    "align nothing, free everything" at distance 0, which dumps the whole edition
    onto one line. Stray header/marginal HTR lines are handled by the confidence
    threshold instead, not by freeing the HTR ends. ``dehyphenate`` rejoins words
    the scribe split across a line break when the earlier line ends in a hyphen.
    """
    # 1. Build the folded HTR spine + a per-character line map. ``is_joiner``
    #    marks the inter-line separator spaces so they carry line context for the
    #    projection but do not count toward a line's matched-fraction (they are
    #    not the line's own characters — else confidence could exceed 1.0).
    spine_chars: list[str] = []
    line_of: list[int] = []  # line index for each folded spine char
    is_joiner: list[bool] = []
    htr_folded_len: list[int] = [0] * len(htr_lines)
    for idx, line in enumerate(htr_lines):
        folded, _src = normalize_indexed(line.text, norm)
        htr_folded_len[idx] = len(folded)
        for ch in folded:
            spine_chars.append(ch)
            line_of.append(idx)
            is_joiner.append(False)
        # Join to the next line: no separator if this line ends hyphenated
        # (the word continues), else a single space (a word boundary).
        if idx < len(htr_lines) - 1:
            if not (dehyphenate and _ends_hyphenated(line.text)):
                spine_chars.append(" ")
                line_of.append(idx)  # the joiner belongs to the line it follows
                is_joiner.append(True)
    spine = "".join(spine_chars)

    # 2. Fold the edition, keeping folded→original offsets.
    ed_folded, ed_src = normalize_indexed(edition_text, norm)

    # 3. Global alignment of spine (a) to folded edition (b).
    if not spine or not ed_folded:
        lines = [
            AlignedLine(ln.ref, ln.text, "", 0.0, htr_folded_len[i], 0, False)
            for i, ln in enumerate(htr_lines)
        ]
        return AlignmentResult(lines, threshold, norm.name, 0, len(edition_text))

    alignment = _align_spine(spine, ed_folded, free_a=free_htr_ends, free_b=free_edition_ends)

    # 4. Projection: every edition char inherits the line of the HTR char it hit;
    #    edition-only insertions inherit the current line context.
    line_first_orig: list[int | None] = [None] * len(htr_lines)
    line_last_orig: list[int] = [-1] * len(htr_lines)
    n_matched = [0] * len(htr_lines)
    cur_line = 0
    for kind, i, j in alignment.ops:
        if kind in (dp.MATCH, dp.SUB):
            cur_line = line_of[i]
            if kind == dp.MATCH and not is_joiner[i]:
                n_matched[cur_line] += 1
            _assign(line_first_orig, line_last_orig, cur_line, ed_src[j])
        elif kind == dp.INS:  # edition char with no HTR counterpart
            _assign(line_first_orig, line_last_orig, cur_line, ed_src[j])
        # DEL (HTR char with no edition) contributes nothing to the projection.

    # 5. Partition the ORIGINAL edition text contiguously at line starts, so no
    #    original character (incl. dropped punctuation) is lost between lines.
    starts = [
        (line_first_orig[i], i) for i in range(len(htr_lines)) if line_first_orig[i] is not None
    ]
    starts.sort()
    slice_for: dict[int, tuple[int, int]] = {}
    for pos, (start, li) in enumerate(starts):
        assert start is not None
        if pos + 1 < len(starts):
            end = starts[pos + 1][0]
            assert end is not None
        else:
            end = max(line_last_orig[i] for i in range(len(htr_lines))) + 1
        slice_for[li] = (start, end)

    lines: list[AlignedLine] = []
    for i, ln in enumerate(htr_lines):
        if i in slice_for:
            s, e = slice_for[i]
            ed_slice = edition_text[s:e]
        else:
            ed_slice = ""
        denom = max(1, htr_folded_len[i])
        conf = n_matched[i] / denom
        lines.append(
            AlignedLine(
                ref=ln.ref,
                htr_text=ln.text,
                edition_text=ed_slice,
                align_conf=conf,
                n_htr_chars=htr_folded_len[i],
                n_matched=n_matched[i],
                aligned=conf >= threshold and bool(ed_slice.strip()),
            )
        )
    return AlignmentResult(
        lines=lines,
        threshold=threshold,
        norm_name=norm.name,
        global_distance=alignment.distance,
        edition_chars=len(edition_text),
    )


def _align_spine(a: str, b: str, *, free_a: bool, free_b: bool) -> dp.Alignment:
    """Align the HTR spine to the folded edition, banded when the piece is large.

    Small pieces use the exact full-matrix DP; once the table would exceed the
    ``dp`` cell guard (long multi-page pieces — the case B2 flagged as blocking
    C2), fall back to the banded aligner, which is O(len·band) and exact for these
    near-parallel strings. The switch is transparent to the projection logic.
    """
    if (len(a) + 1) * (len(b) + 1) <= dp.DEFAULT_MAX_CELLS:
        return dp.align(a, b, free_a_ends=free_a, free_b_ends=free_b)
    return dp.align_banded(a, b, free_a_ends=free_a, free_b_ends=free_b)


def _assign(first: list[int | None], last: list[int], li: int, orig_idx: int) -> None:
    """Record that original-edition offset ``orig_idx`` belongs to line ``li``."""
    if first[li] is None or orig_idx < first[li]:  # type: ignore[operator]
        first[li] = orig_idx
    if orig_idx > last[li]:
        last[li] = orig_idx


def _ends_hyphenated(text: str) -> bool:
    """True if the (right-stripped) line text ends with a hyphen-like mark."""
    t = text.rstrip()
    return bool(t) and t[-1] in _HYPHENS


__all__ = [
    "DEFAULT_THRESHOLD",
    "AlignedLine",
    "AlignmentResult",
    "HtrLine",
    "align_piece",
]
