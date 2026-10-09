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

from leibniz.align import anchored, dp
from leibniz.align.normalize import DEFAULT_NORM, AlignNorm, normalize_indexed

# Characters that, at the end of an HTR line, signal a word split across the line
# break (so the fragments should be rejoined without a word boundary). Early-
# modern hyphens are various; also handles the double-oblique "=" convention.
_HYPHENS = ("-", "¬", "=", "‐", "‑", "­")
HYPHENS = _HYPHENS  # public alias (the audit and the reach census test the same set)

# Default: a line must have at least this fraction of its characters matched by
# the alignment to be minted. Tuned on the B2 eval; overridable per call/run.
DEFAULT_THRESHOLD = 0.60

# A line is also refused when the alignment inserts more edition characters into
# it than max(this floor, the line's own folded length): the matched fraction
# cannot see an edition-only burst (an apparatus block the extractor left in,
# a passage the scribe never wrote) glued to an otherwise well-matched line,
# but its slice would carry that burst into the ground truth.
MAX_INSERT_FLOOR = 12


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
    aligned: bool  # align_conf >= threshold, and no edition-only burst
    n_inserted: int = 0  # folded edition chars projected here with no HTR counterpart
    # The hyphen character re-attached to this line's slice because the scribe
    # split a word here and ``keep_hyphen`` was on ("" when nothing was kept).
    kept_hyphen: str = ""

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
    keep_hyphen: bool = True,
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

    ``keep_hyphen`` (with ``dehyphenate``) puts the scribe's hyphen back: when
    the rejoined word is cut between two lines by the projection, the earlier
    line's slice ends with the very hyphen character the HTR line showed (an
    ``=`` stays an ``=``) and the next line's slice starts with the rest of the
    word as before. The slice then carries one character the edition does not
    have, but the line image does — the PHILIUMM audit of 2026-10-07 found the
    missing line-end hyphen the most frequent fault of the minted text. The
    line records it in :attr:`AlignedLine.kept_hyphen`. Off, the behaviour is
    the C2 mint's: the word fragment without its hyphen.
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
    #    edition-only insertions inherit the current line context. Insertions
    #    before the first / after the last HTR hit are the free edition overhang
    #    (whatever the extractor put around the piece) and belong to no line.
    line_first_orig: list[int | None] = [None] * len(htr_lines)
    line_last_orig: list[int] = [-1] * len(htr_lines)
    n_matched = [0] * len(htr_lines)
    n_inserted = [0] * len(htr_lines)
    first_hit, last_hit = _hit_span(alignment.ops)
    cur_line = 0
    for pos, (kind, i, j) in enumerate(alignment.ops):
        if kind in (dp.MATCH, dp.SUB):
            cur_line = line_of[i]
            if kind == dp.MATCH and not is_joiner[i]:
                n_matched[cur_line] += 1
            _assign(line_first_orig, line_last_orig, cur_line, ed_src[j])
        elif kind == dp.INS and first_hit < pos < last_hit:  # edition char, no HTR counterpart
            n_inserted[cur_line] += 1
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

    kept = _kept_hyphens(htr_lines, edition_text, slice_for) if dehyphenate and keep_hyphen else {}
    lines: list[AlignedLine] = []
    for i, ln in enumerate(htr_lines):
        if i in slice_for:
            s, e = slice_for[i]
            ed_slice = edition_text[s:e] + kept.get(i, "")
        else:
            ed_slice = ""
        denom = max(1, htr_folded_len[i])
        conf = n_matched[i] / denom
        burst = n_inserted[i] > max(MAX_INSERT_FLOOR, htr_folded_len[i])
        lines.append(
            AlignedLine(
                ref=ln.ref,
                htr_text=ln.text,
                edition_text=ed_slice,
                align_conf=conf,
                n_htr_chars=htr_folded_len[i],
                n_matched=n_matched[i],
                aligned=conf >= threshold and bool(ed_slice.strip()) and not burst,
                n_inserted=n_inserted[i],
                kept_hyphen=kept.get(i, ""),
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
    """Align the HTR spine to the folded edition, anchored+banded when large.

    Small pieces use the exact full-matrix DP; once the table would exceed the
    ``dp`` cell guard (long multi-page pieces — the case B2 flagged as blocking
    C2), the anchor-guided chunked aligner takes over: it localizes the spine in
    the edition text by shared k-grams first, so an edition passage far longer
    than the spine costs a fixed band, not the whole matrix (the C2 OOM). The
    switch is transparent to the projection logic.
    """
    if (len(a) + 1) * (len(b) + 1) <= dp.DEFAULT_MAX_CELLS:
        return dp.align(a, b, free_a_ends=free_a, free_b_ends=free_b)
    return anchored.align_anchored(a, b, free_a_ends=free_a, free_b_ends=free_b)


def _hit_span(ops: Sequence[tuple[str, int, int]]) -> tuple[int, int]:
    """Op-stream positions of the first and last MATCH/SUB (``(-1, -1)`` if none).

    Insertions outside this span are the edition's free overhang, not text that
    belongs to any manuscript line.
    """
    first = last = -1
    for pos, (kind, _i, _j) in enumerate(ops):
        if kind in (dp.MATCH, dp.SUB):
            if first < 0:
                first = pos
            last = pos
    return first, last


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


def _kept_hyphens(
    htr_lines: Sequence[HtrLine], edition_text: str, slice_for: dict[int, tuple[int, int]]
) -> dict[int, str]:
    """Which lines get their scribal hyphen back, and which character.

    A line qualifies when its HTR text ends in a hyphen mark, it and the next
    line both received a slice, the two slices are adjacent in the edition
    partition, and the cut falls inside a word (a letter on both sides of it).
    A hyphen-like mark that the projection placed at a word boundary (a dash
    closing a sentence, a line whose last word the edition reads differently)
    stays dropped: the slice ends in a space or punctuation there.
    """
    out: dict[int, str] = {}
    for i in range(len(htr_lines) - 1):
        if i not in slice_for or (i + 1) not in slice_for:
            continue
        text = htr_lines[i].text.rstrip()
        if not _ends_hyphenated(text):
            continue
        s, e = slice_for[i]
        s2, e2 = slice_for[i + 1]
        left, right = edition_text[s:e], edition_text[s2:e2]
        if e == s2 and left and right and left[-1].isalpha() and right[0].isalpha():
            out[i] = text[-1]
    return out


__all__ = [
    "DEFAULT_THRESHOLD",
    "HYPHENS",
    "MAX_INSERT_FLOOR",
    "AlignedLine",
    "AlignmentResult",
    "HtrLine",
    "align_piece",
]
