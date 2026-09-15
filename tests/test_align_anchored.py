"""Tests for the anchor-guided chunked aligner (offline): localization + bounds."""

from __future__ import annotations

import random

import pytest

from leibniz.align import anchored, dp
from leibniz.align.align import HtrLine, align_piece

ALPH = "abcdefghijklmnopqrstuvwxyz "


def _text(rng: random.Random, n: int) -> str:
    # word-like random text (spaces every 3-9 chars) so k-grams are specific
    out: list[str] = []
    while len(out) < n:
        out.extend(rng.choice(ALPH[:-1]) for _ in range(rng.randint(3, 9)))
        out.append(" ")
    return "".join(out[:n])


def _mutate(s: str, rate: float, rng: random.Random) -> str:
    out: list[str] = []
    for ch in s:
        r = rng.random()
        if r < rate:
            k = rng.random()
            if k < 0.5:
                out.append(rng.choice(ALPH))
            elif k < 0.75:
                continue
            else:
                out.append(rng.choice(ALPH))
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


def _roundtrip(al: dp.Alignment, a: str, b: str) -> None:
    ra = "".join(a[i] for k, i, j in al.ops if k in (dp.MATCH, dp.SUB, dp.DEL))
    rb = "".join(b[j] for k, i, j in al.ops if k in (dp.MATCH, dp.SUB, dp.INS))
    assert ra == a and rb == b


def test_find_anchors_locates_spine_in_long_edition() -> None:
    rng = random.Random(1)
    edition = _text(rng, 20_000)
    start = 12_000
    spine = _mutate(edition[start : start + 1_500], 0.10, rng)
    anchors = anchored.find_anchors(spine, edition)
    assert len(anchors) > 50
    # every anchor is a true shared k-gram, the chain is strictly increasing, and
    # it sits on the diagonal of the embedded slice (± the mutation drift).
    for (i0, j0), (i1, j1) in zip(anchors, anchors[1:], strict=False):
        assert i0 < i1 and j0 < j1
    for i, j in anchors:
        assert spine[i : i + anchored.DEFAULT_K] == edition[j : j + anchored.DEFAULT_K]
        assert abs((j - i) - start) < 150


def test_anchored_matches_full_dp_on_near_parallel_with_chunking() -> None:
    rng = random.Random(7)
    a = _text(rng, 1_200)
    b = _mutate(a, 0.08, rng)
    full = dp.align(a, b, free_b_ends=True)
    # tiny chunks so several cut anchors and chunk joins are exercised
    anc = anchored.align_anchored(a, b, free_b_ends=True, chunk_rows=150, band=32)
    assert anc.distance == full.distance
    _roundtrip(anc, a, b)


def test_anchored_localizes_spine_in_much_longer_edition() -> None:
    rng = random.Random(3)
    edition = _text(rng, 30_000)
    start = 21_000
    spine = _mutate(edition[start : start + 900], 0.10, rng)
    full = dp.align(spine, edition, free_b_ends=True)
    anc = anchored.align_anchored(spine, edition, free_b_ends=True, band=48)
    assert anc.distance == full.distance
    _roundtrip(anc, spine, edition)
    hits = [j for k, _i, j in anc.ops if k == dp.MATCH]
    assert start - 50 <= min(hits) and max(hits) <= start + 1_000


def test_anchored_handles_spine_longer_than_edition() -> None:
    # the folio range carries more manuscript than the edition passage covers
    rng = random.Random(9)
    spine = _text(rng, 6_000)
    edition = _mutate(spine[2_000:3_200], 0.08, rng)
    full = dp.align(spine, edition, free_b_ends=True)
    anc = anchored.align_anchored(spine, edition, free_b_ends=True, band=48)
    # The full DP shaves a few edits by scattering chance matches over the
    # uncovered manuscript; the band keeps every match inside the covered slice.
    assert anc.distance <= full.distance * 1.01
    _roundtrip(anc, spine, edition)
    hits = [i for k, i, _j in anc.ops if k == dp.MATCH]
    # Unit-cost ties let the last few edition characters scatter as chance
    # matches over the uncovered tail; the band caps that at ``band`` characters
    # (the full DP scatters without bound — its hit span starts at row 83).
    assert sum(1_950 <= i <= 3_250 for i in hits) >= len(hits) - 48


def test_null_alignment_when_nothing_is_shared_and_band_too_big() -> None:
    a = "a" * 2_000
    b = "b" * 20_000
    al = anchored.align_anchored(a, b, free_b_ends=True, max_cells=1_000_000)
    assert al.n_match == 0
    _roundtrip(al, a, b)
    assert al.distance == len(a)  # every HTR char deleted, the edition overhang free


def test_band_memory_stays_bounded_for_long_edition_text() -> None:
    # The C2 OOM shape: a short spine, a 120k-character edition text. The full
    # matrix would be ~360M cells; the anchored path must stay in a fixed band.
    rng = random.Random(21)
    edition = _text(rng, 120_000)
    start = 70_000
    spine = _mutate(edition[start : start + 3_000], 0.12, rng)
    cells_seen: list[int] = []
    orig = dp.align_in_band

    def spy(a, b, lo, hi, **kw):  # type: ignore[no-untyped-def]
        cells_seen.append(sum(h - lo_ + 1 for lo_, h in zip(lo, hi, strict=True)))
        return orig(a, b, lo, hi, **kw)

    dp_align_in_band = anchored.dp.align_in_band
    try:
        anchored.dp.align_in_band = spy  # type: ignore[assignment]
        al = anchored.align_anchored(spine, edition, free_b_ends=True)
    finally:
        anchored.dp.align_in_band = dp_align_in_band  # type: ignore[assignment]
    assert cells_seen and max(cells_seen) < 3_001 * (2 * dp.DEFAULT_BAND + 2)
    assert al.n_match > 2_000
    _roundtrip(al, spine, edition)


def test_align_in_band_guards() -> None:
    with pytest.raises(ValueError, match="max_cells"):
        dp.align_in_band("abcd", "abcd", [0] * 5, [4] * 5, max_cells=10)
    with pytest.raises(ValueError, match="do not touch"):
        dp.align_in_band("abcd", "abcdefgh", [0, 0, 5, 5, 5], [1, 1, 8, 8, 8])
    with pytest.raises(ValueError, match="corner"):
        dp.align_in_band("abcd", "abcd", [0] * 5, [3] * 5)


def test_align_banded_refuses_huge_length_difference() -> None:
    # The old behaviour widened the band to |n-m| — the whole matrix. Now the
    # cell guard refuses it instead of allocating gigabytes.
    with pytest.raises(ValueError, match="max_cells"):
        dp.align_banded("a" * 500, "b" * 40_000, free_b_ends=True, max_cells=1_000_000)


def test_choose_cuts_only_inside_matched_runs() -> None:
    # consecutive anchors on one diagonal form a run; an isolated anchor does not
    run = [(i, i + 10) for i in range(100, 130)]
    lone = [(400, 900)]
    run2 = [(i, i + 500) for i in range(700, 720)]
    cuts = anchored.choose_cuts(run + lone + run2, chunk_rows=200)
    assert cuts and all(c in run2 for c in cuts)
    assert (400, 900) not in cuts


def test_align_piece_routes_large_pieces_through_anchored_path() -> None:
    rng = random.Random(5)
    edition = _text(rng, 60_000)
    start = 30_000
    body = edition[start : start + 4_000]
    # cut the manuscript passage into ~55-char lines with 10% HTR noise
    lines = [
        HtrLine(ref=f"L{k:03d}", text=_mutate(body[p : p + 55], 0.10, rng))
        for k, p in enumerate(range(0, len(body), 55))
    ]
    res = align_piece(lines, edition, threshold=0.6)
    assert res.yield_rate > 0.8
    minted = res.aligned_lines()
    # the projected slices are the embedded passage, not the free overhang
    assert all(start - 60 <= edition.find(ln.edition_text.strip()) for ln in minted[:3])
    assert all(len(ln.edition_text) < 120 for ln in minted)
