"""Anchor-guided, chunked alignment for piece-length inputs (Phase C2).

:func:`leibniz.align.dp.align` is exact but quadratic, and
:func:`leibniz.align.dp.align_banded` only helps when the two strings are
near-equal in length: its band is widened to the whole length difference, so a
piece whose edition text is far longer than its HTR spine (an over-broad
extraction, a sub-piece served its parent record's text) turns the band back
into the full matrix — gigabytes for a single piece, which is what OOM-killed
the C2 shard workers. The fix is to find out *where* the spine lives in the
edition text before running any DP, and then to run the DP only there:

1. **Anchors.** Index the k-grams of the shorter string (``k`` = 8 folded
   characters), scan the longer one, and collect every shared k-gram as a
   candidate ``(i, j)``. Because both sides are folded to the same comparison
   alphabet, shared k-grams are exact local matches; under ~10 % HTR noise about
   a fifth of all positions still match, so a piece yields hundreds of them.
2. **Chain.** Keep the longest chain of candidates increasing in both ``i`` and
   ``j`` (a patience-sorting LIS). Spurious matches cannot join the chain unless
   they happen to sit between consecutive true anchors — and then they are near
   the true path by construction. A light neighbour check drops the rare
   isolated outlier.
3. **Band about the chain.** The expected column for every row is the
   piecewise-linear interpolation through the anchors (slope-1 extrapolation
   beyond the ends), and the DP runs in a fixed-width band about it. An edition
   overhang — however long — is simply outside the band.
4. **Chunks.** The chain also supplies cut points: every ~8k rows the alignment
   is split at a well-supported anchor (the path provably passes through a
   matched k-gram run) and each chunk is aligned on its own, so the move table
   never exceeds a few MB no matter how long the piece is. Only the outer ends
   of the outer chunks are free; the inner joins are global.

Everything is pure Python and offline; :mod:`leibniz.align.align` routes to it
whenever the full matrix would exceed its cell guard.
"""

from __future__ import annotations

from array import array
from bisect import bisect_left
from collections.abc import Sequence

from leibniz.align import dp

# k-gram length on the folded comparison alphabet (~27 symbols): long enough to
# be specific in a 100k-character volume passage, short enough to survive noise.
DEFAULT_K = 8
# A k-gram that occurs more often than this in the indexed string is too common
# to locate anything ("et quod ") and is ignored.
MAX_OCCURRENCES = 8
# Below this many chained anchors a piece is not localized; fall back.
MIN_ANCHORS = 4
# Rows per DP chunk; with the default band this is ~4 MB of move table.
CHUNK_ROWS = 8192

Anchor = tuple[int, int]


def find_anchors(
    a: str, b: str, *, k: int = DEFAULT_K, max_occ: int = MAX_OCCURRENCES
) -> list[Anchor]:
    """Chain of shared k-grams ``(i, j)`` (``a[i:i+k] == b[j:j+k]``), increasing in both.

    Indexes the shorter string and scans the longer, so memory is proportional to
    the shorter side. Returns the longest monotone chain with isolated outliers
    removed; empty when nothing is shared.
    """
    n, m = len(a), len(b)
    if n < k or m < k:
        return []
    swap = n > m  # index the shorter string; report anchors as (i in a, j in b)
    short, long_ = (b, a) if swap else (a, b)
    index: dict[str, list[int]] = {}
    for p in range(len(short) - k + 1):
        g = short[p : p + k]
        lst = index.get(g)
        if lst is None:
            index[g] = [p]
        elif len(lst) <= max_occ:
            lst.append(p)
    cands: list[Anchor] = []
    for q in range(len(long_) - k + 1):
        lst = index.get(long_[q : q + k])
        if lst is not None and len(lst) <= max_occ:
            if swap:
                cands.extend((q, p) for p in lst)
            else:
                cands.extend((p, q) for p in lst)
    del index
    if not cands:
        return []
    return _drop_outliers(_longest_chain(cands), tolerance=dp.DEFAULT_BAND)


def _longest_chain(cands: list[Anchor]) -> list[Anchor]:
    """Longest subsequence strictly increasing in both coordinates (patience LIS)."""
    # Sort by (i asc, j desc): a strictly increasing j-subsequence then uses at
    # most one candidate per i, i.e. is strictly increasing in i as well.
    cands.sort(key=lambda t: (t[0], -t[1]))
    tails_j: list[int] = []
    tails_idx: list[int] = []
    prev = array("i", [-1]) * len(cands)
    for idx, (_i, j) in enumerate(cands):
        pos = bisect_left(tails_j, j)
        if pos == len(tails_j):
            tails_j.append(j)
            tails_idx.append(idx)
        else:
            tails_j[pos] = j
            tails_idx[pos] = idx
        prev[idx] = tails_idx[pos - 1] if pos > 0 else -1
    chain: list[Anchor] = []
    idx = tails_idx[-1]
    while idx >= 0:
        chain.append(cands[idx])
        idx = prev[idx]
    chain.reverse()
    return chain


def _drop_outliers(chain: list[Anchor], *, tolerance: int) -> list[Anchor]:
    """Drop anchors whose diagonal agrees with neither neighbour's (isolated hits).

    A true anchor after a long edition-only passage jumps diagonal relative to its
    predecessor but agrees with its successor; a spurious one agrees with nobody.
    """
    if len(chain) < 2:
        return chain
    diag = [j - i for i, j in chain]
    keep: list[Anchor] = []
    for t, anc in enumerate(chain):
        agree_prev = t > 0 and abs(diag[t] - diag[t - 1]) <= tolerance
        agree_next = t + 1 < len(chain) and abs(diag[t + 1] - diag[t]) <= tolerance
        if agree_prev or agree_next:
            keep.append(anc)
    return keep


def band_centers(n: int, m: int, anchors: Sequence[Anchor]) -> array:
    """Expected column for every row ``0..n``: linear through the anchors.

    Beyond the first / last anchor the path is extrapolated with slope 1 (the
    two strings are the same text), clamped to ``[0, m]``. With no anchors this
    is the length-ratio diagonal.
    """
    centers = array("i", [0]) * (n + 1)
    if not anchors:
        for i in range(n + 1):
            centers[i] = round(i * m / n) if n else 0
        return centers
    i0, j0 = anchors[0]
    for i in range(0, min(i0, n) + 1):
        centers[i] = min(m, max(0, j0 - (i0 - i)))
    for (ia, ja), (ib, jb) in zip(anchors, anchors[1:], strict=False):
        span = ib - ia
        for i in range(ia + 1, ib + 1):
            centers[i] = min(m, max(0, ja + round((jb - ja) * (i - ia) / span)))
    il, jl = anchors[-1]
    for i in range(il + 1, n + 1):
        centers[i] = min(m, max(0, jl + (i - il)))
    return centers


def band_rows(
    centers: Sequence[int],
    j0: int,
    j1: int,
    *,
    half: int,
    corner_start: bool,
    corner_end: bool,
) -> tuple[list[int], list[int]]:
    """Per-row ``(lo, hi)`` column windows of one chunk, relative to ``j0``.

    ``centers`` are the absolute expected columns of the chunk's rows. Consecutive
    rows are made to touch (a jump wider than the band widens the row instead of
    disconnecting it), and the chunk's corner cells are forced in-band where the
    corresponding end is global.
    """
    mseg = j1 - j0
    lo: list[int] = []
    hi: list[int] = []
    for c in centers:
        cc = min(mseg, max(0, c - j0))
        lo.append(max(0, cc - half))
        hi.append(min(mseg, cc + half))
    for r in range(1, len(lo)):
        if lo[r] > hi[r - 1] + 1:
            lo[r] = hi[r - 1] + 1
    if corner_start:
        lo[0] = 0
    if corner_end:
        hi[-1] = mseg
        if lo[-1] > hi[-1]:
            lo[-1] = hi[-1]
    return lo, hi


def choose_cuts(anchors: Sequence[Anchor], *, chunk_rows: int, k: int = DEFAULT_K) -> list[Anchor]:
    """Anchors to split the DP at: about every ``chunk_rows`` rows, at a run.

    A cut must sit inside a matched run (its predecessor in the chain lies on
    the same diagonal within ``k`` rows), so the optimal path is known to pass
    through it and the chunks join exactly.
    """
    cuts: list[Anchor] = []
    last_i = 0
    for t in range(1, len(anchors)):
        i, j = anchors[t]
        if i - last_i < chunk_rows:
            continue
        pi, pj = anchors[t - 1]
        if i - pi <= k and (j - i) == (pj - pi):
            cuts.append((i, j))
            last_i = i
    return cuts


def align_anchored(
    a: str,
    b: str,
    *,
    band: int = dp.DEFAULT_BAND,
    free_a_ends: bool = False,
    free_b_ends: bool = False,
    chunk_rows: int = CHUNK_ROWS,
    max_cells: int = dp.DEFAULT_MAX_BAND_CELLS,
    anchors: Sequence[Anchor] | None = None,
) -> dp.Alignment:
    """Align ``a`` to ``b`` in chunks banded about their shared-k-gram chain.

    Same op-stream and end-gap contract as :func:`leibniz.align.dp.align`
    (``free_b_ends`` frees the edition overhang, etc.). ``anchors`` may be
    supplied (tests); by default :func:`find_anchors` computes them, retrying
    with shorter k-grams for noisy pieces. With too few anchors the pair is not
    localized: the length-ratio band of :func:`leibniz.align.dp.align_banded`
    is used if it fits ``max_cells``, otherwise the result is the null
    alignment (all gaps, nothing matched) — the projection then mints nothing
    from that piece rather than the worker dying.
    """
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return dp.align(a, b, free_a_ends=free_a_ends, free_b_ends=free_b_ends)
    if anchors is None:
        anchors = find_anchors(a, b)
        if len(anchors) < max(MIN_ANCHORS, min(n, m) // 400):
            anchors = find_anchors(a, b, k=DEFAULT_K - 2)
    if len(anchors) < MIN_ANCHORS:
        try:
            return dp.align_banded(
                a,
                b,
                band=band,
                free_a_ends=free_a_ends,
                free_b_ends=free_b_ends,
                max_cells=max_cells,
            )
        except ValueError:
            return null_alignment(a, b, free_a_ends=free_a_ends, free_b_ends=free_b_ends)

    centers = band_centers(n, m, anchors)
    points: list[Anchor] = [(0, 0), *choose_cuts(anchors, chunk_rows=chunk_rows), (n, m)]
    ops: list[tuple[str, int, int]] = []
    distance = 0
    last = len(points) - 2
    for s in range(len(points) - 1):
        (i0, j0), (i1, j1) = points[s], points[s + 1]
        sa, sb = a[i0:i1], b[j0:j1]
        fa_s, fa_e = free_a_ends and s == 0, free_a_ends and s == last
        fb_s, fb_e = free_b_ends and s == 0, free_b_ends and s == last
        if not sa or not sb:  # a degenerate chunk: pure gaps
            ops.extend((dp.DEL, i0 + t, -1) for t in range(len(sa)))
            ops.extend((dp.INS, -1, j0 + t) for t in range(len(sb)))
            if sa and not (fa_s or fa_e):
                distance += len(sa)
            if sb and not (fb_s or fb_e):
                distance += len(sb)
            continue
        lo, hi = band_rows(
            centers[i0 : i1 + 1],
            j0,
            j1,
            half=band,
            corner_start=not (fa_s or fb_s),
            corner_end=not (fa_e or fb_e),
        )
        part = dp.align_in_band(
            sa,
            sb,
            lo,
            hi,
            free_a_start=fa_s,
            free_a_end=fa_e,
            free_b_start=fb_s,
            free_b_end=fb_e,
            max_cells=max_cells,
        )
        ops.extend(
            (kind, i + i0 if i >= 0 else -1, j + j0 if j >= 0 else -1) for kind, i, j in part.ops
        )
        distance += part.distance
    return dp.Alignment(ops=ops, distance=distance, len_a=n, len_b=m)


def null_alignment(
    a: str, b: str, *, free_a_ends: bool = False, free_b_ends: bool = False
) -> dp.Alignment:
    """The all-gaps alignment (nothing matched): every ``a`` deleted, every ``b`` inserted."""
    ops: list[tuple[str, int, int]] = [(dp.DEL, i, -1) for i in range(len(a))]
    ops.extend((dp.INS, -1, j) for j in range(len(b)))
    distance = (0 if free_a_ends else len(a)) + (0 if free_b_ends else len(b))
    return dp.Alignment(ops=ops, distance=distance, len_a=len(a), len_b=len(b))


__all__ = [
    "CHUNK_ROWS",
    "DEFAULT_K",
    "MIN_ANCHORS",
    "align_anchored",
    "band_centers",
    "band_rows",
    "choose_cuts",
    "find_anchors",
    "null_alignment",
]
