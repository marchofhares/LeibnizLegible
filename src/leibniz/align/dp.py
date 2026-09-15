"""Character-level Needleman–Wunsch alignment with traceback (Phase B2).

:mod:`leibniz.htr.metrics` already has a Levenshtein *distance* (two-row DP, no
traceback) — enough to score CER, but retro-alignment needs the **path**: which
edition character lands on which HTR character, so line boundaries can be
projected from one onto the other. This module computes the full alignment and
returns the operation stream.

Design choices, all justified by the retro-alignment use case:

* **Levenshtein costs** (match 0, substitution/insertion/deletion 1). The two
  strings are the same text under different conventions plus HTR noise, so a
  unit-cost global alignment recovers the intended correspondence; fancier
  affine gaps buy nothing here and cost clarity.
* **Semi-global option** (``free_a_ends`` / ``free_b_ends``). When the edition
  passage extends a little beyond the scanned lines (or vice versa), the
  overhanging prefix/suffix should be skipped for free rather than forced into a
  garbage alignment. Free end-gaps on the longer side handle that.
* **Full matrix, pure Python** using :mod:`array` for the DP table. At prototype
  scale (a page or a short letter — a few thousand characters a side) this is a
  few tens of MB and well under a second to a few seconds. A ``max_cells`` guard
  refuses inputs that would blow memory, so :mod:`leibniz.align.align` falls
  back to the banded aligner instead of OOM-ing.
* **Banded variant** (:func:`align_in_band` / :func:`align_banded`): the DP
  restricted to a caller-supplied column window per row. It keeps two rolling
  distance rows and a one-byte-per-cell move table, so memory is the band area
  (not the full matrix), and it too refuses to exceed ``max_cells``. The
  anchor-guided, chunked driver on top of it lives in
  :mod:`leibniz.align.anchored`.

No dependencies; fully offline-testable.
"""

from __future__ import annotations

from array import array
from collections.abc import Sequence
from dataclasses import dataclass

# Operation kinds in the returned stream.
MATCH = "M"  # a[i] == b[j]
SUB = "S"  # a[i] != b[j] (both consumed)
DEL = "D"  # a[i] consumed, gap in b
INS = "I"  # b[j] consumed, gap in a

_INF = 1 << 30

# Refuse an alignment whose DP table would exceed this many cells (~4 bytes each
# in the two ``array('i')`` tables kept, plus one byte for the move table). ~30M
# cells ≈ 270 MB peak. Callers chunk larger inputs.
DEFAULT_MAX_CELLS = 30_000_000


@dataclass(slots=True)
class Alignment:
    """The result of aligning sequence ``a`` against sequence ``b``.

    ``ops`` is the edit script in left-to-right order; each entry is
    ``(kind, i, j)`` with ``i`` the index into ``a`` and ``j`` the index into
    ``b`` (``-1`` where that side has a gap). ``distance`` is the total edit cost
    under the chosen end-gap policy.
    """

    ops: list[tuple[str, int, int]]
    distance: int
    len_a: int
    len_b: int

    @property
    def n_match(self) -> int:
        return sum(1 for k, _, _ in self.ops if k == MATCH)

    def b_to_a(self) -> list[int]:
        """For each ``b`` index, the ``a`` index it aligns to (``-1`` if a gap)."""
        out = [-1] * self.len_b
        for kind, i, j in self.ops:
            if kind in (MATCH, SUB):
                out[j] = i
        return out

    def a_to_b(self) -> list[int]:
        """For each ``a`` index, the ``b`` index it aligns to (``-1`` if a gap)."""
        out = [-1] * self.len_a
        for kind, i, j in self.ops:
            if kind in (MATCH, SUB):
                out[i] = j
        return out


def align(
    a: str,
    b: str,
    *,
    free_a_ends: bool = False,
    free_b_ends: bool = False,
    max_cells: int = DEFAULT_MAX_CELLS,
) -> Alignment:
    """Globally align ``a`` to ``b`` (optionally free end-gaps), with traceback.

    ``free_a_ends`` makes leading/trailing **deletions** (unmatched ``a``) free;
    ``free_b_ends`` makes leading/trailing **insertions** (unmatched ``b``) free.
    Set the flag for whichever side may legitimately overhang — e.g.
    ``free_b_ends=True`` when the edition text ``b`` may cover more than the
    scanned HTR lines ``a``.

    Raises :class:`ValueError` if ``(len(a)+1)*(len(b)+1)`` exceeds ``max_cells``.
    """
    n, m = len(a), len(b)
    if (n + 1) * (m + 1) > max_cells:
        raise ValueError(
            f"alignment table {(n + 1) * (m + 1)} cells exceeds max_cells={max_cells}; "
            "chunk the input (see leibniz.align.align windowing)"
        )
    width = m + 1

    # DP distance table and a move table (0=diag, 1=up/del a, 2=left/ins b).
    dist = array("i", [0]) * ((n + 1) * width)
    move = bytearray((n + 1) * width)

    # First row: aligning "" to b[:j] is j insertions — free if free_b_ends.
    for j in range(1, width):
        dist[j] = 0 if free_b_ends else j
        move[j] = 2
    # First column: aligning a[:i] to "" is i deletions — free if free_a_ends.
    for i in range(1, n + 1):
        base = i * width
        dist[base] = 0 if free_a_ends else i
        move[base] = 1

    for i in range(1, n + 1):
        ai = a[i - 1]
        row = i * width
        prow = row - width
        for j in range(1, width):
            cost = 0 if ai == b[j - 1] else 1
            diag = dist[prow + j - 1] + cost
            up = dist[prow + j] + 1  # deletion of a[i-1]
            left = dist[row + j - 1] + 1  # insertion of b[j-1]
            best = diag
            mv = 0
            if up < best:
                best = up
                mv = 1
            if left < best:
                best = left
                mv = 2
            dist[row + j] = best
            move[row + j] = mv

    # Choose the traceback start under the end-gap policy.
    end_i, end_j = n, m
    best = dist[n * width + m]
    if free_b_ends:  # trailing b insertions free → best over last row
        for j in range(m + 1):
            if dist[n * width + j] < best:
                best = dist[n * width + j]
                end_i, end_j = n, j
    if free_a_ends:  # trailing a deletions free → best over last column
        for i in range(n + 1):
            if dist[i * width + m] < best:
                best = dist[i * width + m]
                end_i, end_j = i, m

    ops = _traceback(a, b, move, dist, width, end_i, end_j, free_a_ends, free_b_ends)
    return Alignment(ops=ops, distance=best, len_a=n, len_b=m)


def _traceback(
    a: str,
    b: str,
    move: bytearray,
    dist: array,
    width: int,
    i: int,
    j: int,
    free_a_ends: bool,
    free_b_ends: bool,
) -> list[tuple[str, int, int]]:
    """Walk the move table from ``(i, j)`` back to an origin, emitting ops."""
    ops: list[tuple[str, int, int]] = []
    # Trailing free gaps (b to the right of end_j, or a below end_i): unmatched,
    # emitted so the op stream still spans the whole sequence.
    for jj in range(len(b) - 1, j - 1, -1):
        ops.append((INS, -1, jj))
    for ii in range(len(a) - 1, i - 1, -1):
        ops.append((DEL, ii, -1))

    while i > 0 or j > 0:
        if i == 0:
            ops.append((INS, -1, j - 1))
            j -= 1
            continue
        if j == 0:
            ops.append((DEL, i - 1, -1))
            i -= 1
            continue
        mv = move[i * width + j]
        if mv == 0:
            kind = MATCH if a[i - 1] == b[j - 1] else SUB
            ops.append((kind, i - 1, j - 1))
            i -= 1
            j -= 1
        elif mv == 1:
            ops.append((DEL, i - 1, -1))
            i -= 1
        else:
            ops.append((INS, -1, j - 1))
            j -= 1
        # Leading free gaps: once we reach the free origin edge, stop paying.
        if free_b_ends and i == 0:
            while j > 0:
                ops.append((INS, -1, j - 1))
                j -= 1
            break
        if free_a_ends and j == 0:
            while i > 0:
                ops.append((DEL, i - 1, -1))
                i -= 1
            break

    ops.reverse()
    return ops


# Default half-bandwidth for banded alignment. A few hundred cells of slack about
# the expected diagonal is ample for HTR-spine ↔ edition-text (the same text
# under ~8% CER + minor edition divergence — the path never wanders far).
DEFAULT_BAND = 256

# The banded tables cost one byte per cell (move) plus two rolling rows, so the
# guard can be far more generous than the full matrix's; ~64M cells ≈ 64 MB.
DEFAULT_MAX_BAND_CELLS = 64_000_000


def align_in_band(
    a: str,
    b: str,
    lo: Sequence[int],
    hi: Sequence[int],
    *,
    free_a_start: bool = False,
    free_a_end: bool = False,
    free_b_start: bool = False,
    free_b_end: bool = False,
    max_cells: int = DEFAULT_MAX_BAND_CELLS,
) -> Alignment:
    """Needleman–Wunsch restricted to the cells ``lo[i] <= j <= hi[i]`` per row.

    The workhorse under :func:`align_banded` and
    :func:`leibniz.align.anchored.align_anchored`: the caller decides *where* the
    band lies (about the length-ratio diagonal, or about a chain of k-gram
    anchors); this computes the DP over exactly those cells with two rolling
    distance rows and a one-byte move entry per cell, so memory is the band's
    area, never the matrix's. The end-gap policy is split per side and per end
    (``free_b_start`` frees leading insertions, ``free_b_end`` trailing ones,
    likewise ``free_a_*`` for deletions) so a chunked driver can free only the
    outer ends of the outer chunks.

    Requirements on the band: ``len(lo) == len(hi) == len(a) + 1``,
    ``0 <= lo[i] <= hi[i] <= len(b)``, and consecutive rows must touch
    (``lo[i] <= hi[i-1] + 1``) so every row is reachable. When an end is not
    free the band must contain the corresponding corner cell (row 0 always
    prices leading insertions, so column 0 need not be in band). Cells outside
    the band are treated as unreachable; the alignment is exact iff the optimal
    path stays in-band. Raises :class:`ValueError` on a malformed band or when
    the band has more than ``max_cells`` cells.
    """
    n, m = len(a), len(b)
    if len(lo) != n + 1 or len(hi) != n + 1:
        raise ValueError("band rows must be len(a) + 1 long")
    cells = 0
    for i in range(n + 1):
        if not 0 <= lo[i] <= hi[i] <= m:
            raise ValueError(f"malformed band row {i}: lo={lo[i]} hi={hi[i]} m={m}")
        if i and lo[i] > hi[i - 1] + 1:
            raise ValueError(f"band rows {i - 1} and {i} do not touch")
        cells += hi[i] - lo[i] + 1
    if cells > max_cells:
        raise ValueError(f"banded alignment of {cells} cells exceeds max_cells={max_cells}")
    if not free_b_end and not free_a_end and hi[n] != m:
        raise ValueError("global end requires the band to contain the corner cell")

    move: list[bytearray] = [bytearray(hi[i] - lo[i] + 1) for i in range(n + 1)]

    # Row 0: aligning "" to b[:j] costs j insertions (free if free_b_start).
    row_lo, row_hi = lo[0], hi[0]
    prev: list[int] = [0 if free_b_start else j for j in range(row_lo, row_hi + 1)]
    mrow = move[0]
    for k in range(len(prev)):
        mrow[k] = 0 if row_lo + k == 0 else 2
    # Best cell in the last column, for a free a-end (trailing deletions free).
    best_col = _INF
    end_col_i = n
    if free_a_end and row_lo <= m <= row_hi:
        best_col = prev[m - row_lo]
        end_col_i = 0

    plo, phi = row_lo, row_hi
    for i in range(1, n + 1):
        ai = a[i - 1]
        row_lo, row_hi = lo[i], hi[i]
        width = row_hi - row_lo + 1
        # ``pv[k]`` is the previous row's value at column ``row_lo - 1 + k``
        # (INF outside the previous band), so diag = pv[k] and up = pv[k + 1].
        need_lo, need_hi = row_lo - 1, row_hi
        ov_lo, ov_hi = max(need_lo, plo), min(need_hi, phi)
        if ov_lo > ov_hi:
            pv = [_INF] * (need_hi - need_lo + 1)
        else:
            pv = (
                [_INF] * (ov_lo - need_lo)
                + prev[ov_lo - plo : ov_hi - plo + 1]
                + [_INF] * (need_hi - ov_hi)
            )
        cur = [0] * width
        mrow = move[i]
        k0 = 0
        left = _INF
        if row_lo == 0:  # column 0: aligning a[:i] to "" is i deletions
            left = 0 if free_a_start else i
            cur[0] = left
            mrow[0] = 1
            k0 = 1
        for k in range(k0, width):
            best = pv[k] + (0 if ai == b[row_lo + k - 1] else 1)
            mv = 0
            up = pv[k + 1] + 1
            if up < best:
                best, mv = up, 1
            left += 1
            if left < best:
                best, mv = left, 2
            cur[k] = best
            mrow[k] = mv
            left = best
        if free_a_end and row_lo <= m <= row_hi and cur[m - row_lo] < best_col:
            best_col = cur[m - row_lo]
            end_col_i = i
        prev, plo, phi = cur, row_lo, row_hi

    # Choose the traceback start under the end-gap policy (``prev`` is row n).
    end_i, end_j = n, m
    best = prev[m - plo] if plo <= m <= phi else _INF
    if free_b_end:  # trailing b insertions free → best over the last row
        for k, v in enumerate(prev):
            if v < best:
                best, end_j = v, plo + k
    if free_a_end and best_col < best:  # trailing a deletions free → best over column m
        best, end_i, end_j = best_col, end_col_i, m
    if best >= _INF:  # unreachable end: no in-band path (a malformed band)
        raise ValueError("no in-band alignment path reaches the end cell")

    ops = _traceback_banded(a, b, move, lo, hi, end_i, end_j)
    return Alignment(ops=ops, distance=best, len_a=n, len_b=m)


def align_banded(
    a: str,
    b: str,
    *,
    band: int = DEFAULT_BAND,
    free_a_ends: bool = False,
    free_b_ends: bool = False,
    max_cells: int = DEFAULT_MAX_BAND_CELLS,
) -> Alignment:
    """Banded Needleman–Wunsch about the length-ratio diagonal, with traceback.

    Computes the alignment only within a diagonal band of half-width ``band``
    about the *length-ratio* diagonal (column ``j ≈ i·m/n``), so it scales to
    piece-length inputs the full matrix (:func:`align`) would refuse. It is
    **exact iff the optimal path stays in-band** — true for near-parallel strings
    (the same text under HTR noise + minor edition divergence), which is exactly
    the retro-alignment regime (B2 report §4). The band is widened to at least
    cover the two strings' length difference, so a systematic length gap never
    pushes the path out of the band — which is why this is only safe for
    near-equal lengths: when one side is far longer, the widened band is the
    whole matrix again, and ``max_cells`` refuses it (the C2 OOM). For that case
    use :func:`leibniz.align.anchored.align_anchored`, which localizes the
    shorter side first.

    Same end-gap policy and op-stream contract as :func:`align`.
    """
    n, m = len(a), len(b)
    if n == 0 or m == 0:  # degenerate; the full DP is trivially cheap here
        return align(a, b, free_a_ends=free_a_ends, free_b_ends=free_b_ends)
    half = max(band, abs(n - m) + 8)
    lo = [0] * (n + 1)
    hi = [0] * (n + 1)
    for i in range(n + 1):
        center = round(i * m / n)
        lo[i] = max(0, center - half)
        hi[i] = min(m, center + half)
    return align_in_band(
        a,
        b,
        lo,
        hi,
        free_a_start=free_a_ends,
        free_a_end=free_a_ends,
        free_b_start=free_b_ends,
        free_b_end=free_b_ends,
        max_cells=max_cells,
    )


def _traceback_banded(
    a: str,
    b: str,
    move: list[bytearray],
    lo: Sequence[int],
    hi: Sequence[int],
    i: int,
    j: int,
) -> list[tuple[str, int, int]]:
    """Walk the banded move table back to the origin (mirrors :func:`_traceback`).

    Free leading gaps need no special case: once ``i`` or ``j`` hits 0 the
    remaining ops are gaps on the other side either way (their *cost* was decided
    by the distance rows). Trailing gaps beyond the chosen end cell are emitted
    first so the op stream spans both sequences.
    """
    ops: list[tuple[str, int, int]] = []
    for jj in range(len(b) - 1, j - 1, -1):
        ops.append((INS, -1, jj))
    for ii in range(len(a) - 1, i - 1, -1):
        ops.append((DEL, ii, -1))

    while i > 0 or j > 0:
        if i == 0:
            ops.append((INS, -1, j - 1))
            j -= 1
            continue
        if j == 0:
            ops.append((DEL, i - 1, -1))
            i -= 1
            continue
        mv = move[i][j - lo[i]] if lo[i] <= j <= hi[i] else 0  # off-band: prefer diag
        if mv == 0:
            kind = MATCH if a[i - 1] == b[j - 1] else SUB
            ops.append((kind, i - 1, j - 1))
            i -= 1
            j -= 1
        elif mv == 1:
            ops.append((DEL, i - 1, -1))
            i -= 1
        else:
            ops.append((INS, -1, j - 1))
            j -= 1

    ops.reverse()
    return ops


def similarity(a: str, b: str, **kw: object) -> float:
    """Normalized similarity in ``[0, 1]``: ``1 - distance / max(len)``.

    A quick scalar for "how alike are these two strings", used to score a
    projected line against its aligned reference slice. ``1.0`` is identical;
    ``0.0`` is maximally different. Empty vs empty is ``1.0``.
    """
    n, m = len(a), len(b)
    if n == 0 and m == 0:
        return 1.0
    d = align(a, b, **kw).distance  # type: ignore[arg-type]
    return max(0.0, 1.0 - d / max(n, m))


__all__ = [
    "DEFAULT_BAND",
    "DEFAULT_MAX_BAND_CELLS",
    "DEFAULT_MAX_CELLS",
    "DEL",
    "INS",
    "MATCH",
    "SUB",
    "Alignment",
    "align",
    "align_banded",
    "align_in_band",
    "similarity",
]
