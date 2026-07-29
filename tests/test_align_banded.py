"""Tests for the banded aligner (offline): exactness vs the full DP + scaling."""

from __future__ import annotations

import random

from leibniz.align import dp


def _mutate(s: str, rate: float, rng: random.Random, alph: str) -> str:
    out: list[str] = []
    for ch in s:
        r = rng.random()
        if r < rate:
            k = rng.random()
            if k < 0.5:
                out.append(rng.choice(alph))
            elif k < 0.75:
                continue
            else:
                out.append(rng.choice(alph))
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


def test_banded_matches_full_wide_band() -> None:
    rng = random.Random(11)
    alph = "abcdefg "
    for _ in range(300):
        n = rng.randint(1, 60)
        a = "".join(rng.choice(alph) for _ in range(n))
        b = _mutate(a, 0.2, rng, alph)
        for fa, fb in [(False, False), (False, True), (True, False)]:
            full = dp.align(a, b, free_a_ends=fa, free_b_ends=fb)
            bnd = dp.align_banded(a, b, band=200, free_a_ends=fa, free_b_ends=fb)
            assert full.distance == bnd.distance


def test_banded_exact_narrow_band_on_near_parallel() -> None:
    # The retro-alignment regime: ~8% edit noise → path hugs the diagonal, so a
    # narrow band is still exact.
    rng = random.Random(5)
    alph = "abcdefghij "
    fails = 0
    for _ in range(150):
        n = rng.randint(60, 250)
        a = "".join(rng.choice(alph) for _ in range(n))
        b = _mutate(a, 0.08, rng, alph)
        full = dp.align(a, b, free_b_ends=True)
        bnd = dp.align_banded(a, b, band=32, free_b_ends=True)
        fails += full.distance != bnd.distance
    assert fails == 0


def test_banded_handles_length_difference() -> None:
    # A long insertion in b: band auto-widens to cover |n-m|.
    a = "the quick brown fox"
    b = "the quick" + " very " * 20 + "brown fox"
    full = dp.align(a, b, free_b_ends=True)
    bnd = dp.align_banded(a, b, band=8, free_b_ends=True)
    assert bnd.distance == full.distance


def test_banded_ops_reconstruct_sequences() -> None:
    a = "abcdefabcdef"
    b = "abXdefabcdef"
    al = dp.align_banded(a, b, band=16)
    # walking the op stream must reproduce both strings
    ra = "".join(a[i] for k, i, j in al.ops if k in (dp.MATCH, dp.SUB, dp.DEL))
    rb = "".join(b[j] for k, i, j in al.ops if k in (dp.MATCH, dp.SUB, dp.INS))
    assert ra == a and rb == b


def test_banded_empty_inputs() -> None:
    assert dp.align_banded("", "abc").distance == 3
    assert dp.align_banded("abc", "").distance == 3
    assert dp.align_banded("", "").distance == 0
