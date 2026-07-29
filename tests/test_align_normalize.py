"""Tests for alignment-time normalization + the folded→original offset map (offline)."""

from __future__ import annotations

from leibniz.align.normalize import (
    DEFAULT_NORM,
    DIPLOMATIC_NORM,
    AlignNorm,
    normalize,
    normalize_indexed,
)


def test_basic_folds() -> None:
    # casefold, u/v, i/j, long-s, ligature, ampersand, punctuation, whitespace.
    assert normalize("Quæ ſunt & vivunt.") == "quae sunt et uiuunt"
    assert normalize("J.-J. iustè") == "i i iuste"


def test_deletion_tokens_dropped() -> None:
    # struck 'xx' runs vanish (they have no edition counterpart).
    assert normalize("motus xx gravia") == "motus grauia"
    assert normalize("a xxx b") == "a b"
    # but a real word containing 'xx' is not eaten (token-bounded).
    assert "exxon" in normalize("Exxon")  # not a bounded xx run


def test_diplomatic_norm_keeps_deletions() -> None:
    # the diplomatic condition preserves 'xx' (present on both sides).
    assert "xx" in normalize("motus xx gravia", DIPLOMATIC_NORM)


def test_offset_map_length_matches() -> None:
    folded, src = normalize_indexed("Quæ ſunt, & vivunt!")
    assert len(folded) == len(src)
    # src indices are non-decreasing (monotonic projection back to the original).
    assert all(src[i] <= src[i + 1] for i in range(len(src) - 1))


def test_offset_map_slices_original() -> None:
    original = "Quæ ſunt & uiuunt"
    folded, src = normalize_indexed(original)
    # the folded prefix "quae" (4 chars) came from the original "Quæ" (3 chars).
    assert folded.startswith("quae")
    assert original[src[0] : src[3] + 1] == "Quæ"


def test_ampersand_expands_both_output_chars_point_at_source() -> None:
    folded, src = normalize_indexed("a & b")
    # '&' -> 'et'; both 'e' and 't' point at the single source index of '&'.
    i = folded.index("et")
    assert src[i] == src[i + 1]


def test_options_toggle() -> None:
    keep_punct = AlignNorm(name="p", drop_punctuation=False, collapse_whitespace=False)
    assert normalize("a,b", keep_punct) == "a,b"
    no_uv = DEFAULT_NORM.with_options(fold_uv=False)
    assert normalize("vivunt", no_uv) == "vivunt"


def test_empty_and_whitespace() -> None:
    assert normalize("") == ""
    assert normalize("   \n\t  ") == ""
    assert normalize("a\n\n  b") == "a b"
