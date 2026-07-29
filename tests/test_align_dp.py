"""Tests for the Needleman-Wunsch aligner with traceback (offline)."""

from __future__ import annotations

import pytest

from leibniz.align import dp


def test_distance_matches_levenshtein() -> None:
    assert dp.align("kitten", "sitting").distance == 3
    assert dp.align("", "").distance == 0
    assert dp.align("abc", "").distance == 3
    assert dp.align("", "abc").distance == 3


def test_traceback_reconstructs_both_sequences() -> None:
    al = dp.align("abcx", "abddx")
    # every a index and b index appears exactly once across the op stream.
    a_idx = sorted(i for k, i, j in al.ops if i >= 0)
    b_idx = sorted(j for k, i, j in al.ops if j >= 0)
    assert a_idx == list(range(4))
    assert b_idx == list(range(5))


def test_match_positions_are_exact() -> None:
    al = dp.align("hello", "hello")
    assert al.distance == 0
    assert al.n_match == 5
    assert al.b_to_a() == [0, 1, 2, 3, 4]


def test_free_b_ends_skips_overhang() -> None:
    # b has a junk prefix and suffix; free ends make them cost nothing.
    al = dp.align("abcdef", "zzzabcdefyy", free_b_ends=True)
    assert al.distance == 0
    b2a = al.b_to_a()
    # the 'a' of the core (b index 3) maps to a index 0.
    assert b2a[3] == 0


def test_free_a_ends_skips_overhang() -> None:
    al = dp.align("zzabcde", "abcde", free_a_ends=True)
    assert al.distance == 0


def test_both_free_ends_is_degenerate_zero() -> None:
    # documents WHY align_piece never enables both: everything freed → distance 0.
    al = dp.align("abcdef", "ghijkl", free_a_ends=True, free_b_ends=True)
    assert al.distance == 0


def test_similarity() -> None:
    assert dp.similarity("hello", "hello") == 1.0
    assert dp.similarity("", "") == 1.0
    assert dp.similarity("abcd", "abxd") == 0.75
    assert 0.0 <= dp.similarity("totally", "different") <= 1.0


def test_max_cells_guard() -> None:
    with pytest.raises(ValueError, match="max_cells"):
        dp.align("a" * 100, "b" * 100, max_cells=50)
