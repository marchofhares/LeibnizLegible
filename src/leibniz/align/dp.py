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
  refuses inputs that would blow memory, so :mod:`leibniz.align.align` can fall
  back to windowed alignment instead of OOM-ing. Banding is a documented future
  optimization, unnecessary at prototype scale.

No dependencies; fully offline-testable.
"""

from __future__ import annotations

from array import array
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
    dist = array("i", bytes(4 * (n + 1) * width))
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
# the length-ratio diagonal is ample for HTR-spine ↔ edition-text (the same text
# under ~8% CER + minor edition divergence — the path never wanders far).
DEFAULT_BAND = 256


def align_banded(
    a: str,
    b: str,
    *,
    band: int = DEFAULT_BAND,
    free_a_ends: bool = False,
    free_b_ends: bool = False,
) -> Alignment:
    """Banded Needleman–Wunsch — O(len·band) time and memory, with traceback.

    Computes the alignment only within a diagonal band of half-width ``band``
    about the *length-ratio* diagonal (column ``j ≈ i·m/n``), so it scales to
    piece-length inputs the full matrix (:func:`align`) would refuse. It is
    **exact iff the optimal path stays in-band** — true for near-parallel strings
    (the same text under HTR noise + minor edition divergence), which is exactly
    the retro-alignment regime (B2 report §4). The band is widened to at least
    cover the two strings' length difference, so a systematic length gap never
    pushes the path out of the band.

    Same end-gap policy and op-stream contract as :func:`align`.
    """
    n, m = len(a), len(b)
    if n == 0 or m == 0:  # degenerate; the full DP is trivially cheap here
        return align(a, b, free_a_ends=free_a_ends, free_b_ends=free_b_ends)
    half = max(band, abs(n - m) + 8)

    lo = [0] * (n + 1)
    hi = [0] * (n + 1)
    dist: list[array] = [array("i") for _ in range(n + 1)]
    move: list[bytearray] = [bytearray() for _ in range(n + 1)]
    for i in range(n + 1):
        center = round(i * m / n)
        lo[i] = max(0, center - half)
        hi[i] = min(m, center + half)
        width = hi[i] - lo[i] + 1
        dist[i] = array("i", bytes(4 * width))
        move[i] = bytearray(width)

    def gd(i: int, j: int) -> int:
        if i < 0 or j < 0 or j < lo[i] or j > hi[i]:
            return _INF
        return dist[i][j - lo[i]]

    for i in range(n + 1):
        ai = a[i - 1] if i > 0 else ""
        row_lo = lo[i]
        for j in range(row_lo, hi[i] + 1):
            k = j - row_lo
            if i == 0 and j == 0:
                dist[i][k] = 0
                move[i][k] = 0
            elif i == 0:
                dist[i][k] = 0 if free_b_ends else j
                move[i][k] = 2
            elif j == 0:
                dist[i][k] = 0 if free_a_ends else i
                move[i][k] = 1
            else:
                cost = 0 if ai == b[j - 1] else 1
                diag = gd(i - 1, j - 1) + cost
                up = gd(i - 1, j) + 1
                left = gd(i, j - 1) + 1
                best, mv = diag, 0
                if up < best:
                    best, mv = up, 1
                if left < best:
                    best, mv = left, 2
                dist[i][k] = best
                move[i][k] = mv

    end_i, end_j = n, m
    best = gd(n, m)
    if free_b_ends:
        for j in range(lo[n], hi[n] + 1):
            v = dist[n][j - lo[n]]
            if v < best:
                best, end_i, end_j = v, n, j
    if free_a_ends:
        for i in range(n + 1):
            if lo[i] <= m <= hi[i] and dist[i][m - lo[i]] < best:
                best, end_i, end_j = dist[i][m - lo[i]], i, m

    ops = _traceback_banded(a, b, move, lo, hi, end_i, end_j, free_a_ends, free_b_ends)
    return Alignment(ops=ops, distance=best, len_a=n, len_b=m)


def _traceback_banded(
    a: str,
    b: str,
    move: list[bytearray],
    lo: list[int],
    hi: list[int],
    i: int,
    j: int,
    free_a_ends: bool,
    free_b_ends: bool,
) -> list[tuple[str, int, int]]:
    """Walk the banded move table back to an origin (mirrors :func:`_traceback`)."""
    ops: list[tuple[str, int, int]] = []
    for jj in range(len(b) - 1, j - 1, -1):
        ops.append((INS, -1, jj))
    for ii in range(len(a) - 1, i - 1, -1):
        ops.append((DEL, ii, -1))

    def mget(i: int, j: int) -> int:
        if lo[i] <= j <= hi[i]:
            return move[i][j - lo[i]]
        return 0  # off-band on the optimal path shouldn't happen; prefer diag

    while i > 0 or j > 0:
        if i == 0:
            ops.append((INS, -1, j - 1))
            j -= 1
            continue
        if j == 0:
            ops.append((DEL, i - 1, -1))
            i -= 1
            continue
        mv = mget(i, j)
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
    "DEL",
    "INS",
    "MATCH",
    "SUB",
    "Alignment",
    "align",
    "align_banded",
    "similarity",
]
