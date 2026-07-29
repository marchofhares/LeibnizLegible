"""Tests for CER/WER metrics, normalization policy, and bootstrap CIs (offline)."""

from __future__ import annotations

import unicodedata

import pytest

from leibniz.htr import metrics
from leibniz.htr.metrics import NormPolicy

# -- edit distance ---------------------------------------------------------- #


def test_edit_distance_basics() -> None:
    assert metrics.edit_distance("", "") == 0
    assert metrics.edit_distance("abc", "abc") == 0
    assert metrics.edit_distance("abc", "") == 3
    assert metrics.edit_distance("", "abc") == 3
    assert metrics.edit_distance("kitten", "sitting") == 3  # classic Levenshtein
    assert metrics.edit_distance("flaw", "lawn") == 2


def test_edit_distance_on_word_tokens() -> None:
    # Word-level distance: one substitution.
    assert metrics.edit_distance(["a", "b", "c"], ["a", "x", "c"]) == 1
    assert metrics.edit_distance(["a", "b"], ["a", "b", "c"]) == 1


# -- normalization ---------------------------------------------------------- #


def test_normalize_whitespace_and_strip() -> None:
    p = NormPolicy(name="t", unicode_form=None, collapse_whitespace=True, strip=True)
    assert metrics.normalize("  a   b\tc \n", p) == "a b c"


def test_normalize_strip_only_preserves_internal_whitespace() -> None:
    p = NormPolicy(name="t", unicode_form=None, collapse_whitespace=False, strip=True)
    assert metrics.normalize("  a   b  ", p) == "a   b"


def test_normalize_nfd_vs_nfc_changes_length_but_folds_equal() -> None:
    s = "é"  # single codepoint (NFC)
    nfd = NormPolicy(name="d", unicode_form="NFD")
    nfc = NormPolicy(name="c", unicode_form="NFC")
    # NFD decomposes é -> e + combining acute (2 codepoints).
    assert len(metrics.normalize(s, nfd)) == 2
    assert len(metrics.normalize(s, nfc)) == 1
    # Both sides normalized the same way compare equal regardless of input form.
    a = unicodedata.normalize("NFC", "café")
    b = unicodedata.normalize("NFD", "café")
    assert metrics.normalize(a, nfd) == metrics.normalize(b, nfd)


def test_normalize_strip_diacritics_and_casefold() -> None:
    assert metrics.normalize("CafÉ", metrics.LENIENT_POLICY) == "cafe"


def test_policy_rejects_bad_unicode_form() -> None:
    with pytest.raises(ValueError):
        NormPolicy(name="bad", unicode_form="NFZ")


def test_get_policy_and_presets() -> None:
    assert metrics.get_policy("philiumm") is metrics.PHILIUMM_POLICY
    assert metrics.get_policy("strict").unicode_form == "NFC"
    with pytest.raises(KeyError):
        metrics.get_policy("nope")


def test_policy_describe_is_human_readable() -> None:
    assert "NFD" in metrics.PHILIUMM_POLICY.describe()
    assert "casefold" in metrics.LENIENT_POLICY.describe()


# -- line scoring & aggregation --------------------------------------------- #


def test_score_line_perfect_and_errors() -> None:
    s = metrics.score_line("hello world", "hello world", metrics.PHILIUMM_POLICY)
    assert s.char_edits == 0 and s.cer == 0.0
    assert s.word_edits == 0 and s.wer == 0.0

    s2 = metrics.score_line("hello world", "hallo world", metrics.PHILIUMM_POLICY)
    assert s2.char_edits == 1
    assert s2.ref_chars == len("hello world")
    assert s2.word_edits == 1  # one word wrong of two
    assert s2.ref_words == 2


def test_score_line_empty_reference_guard() -> None:
    s = metrics.score_line("", "", metrics.PHILIUMM_POLICY)
    assert s.cer == 0.0 and s.wer == 0.0
    s2 = metrics.score_line("", "spurious", metrics.PHILIUMM_POLICY)
    assert s2.cer == 1.0  # empty ref, non-empty hyp -> full error


def test_cer_wer_micro_average() -> None:
    scores = [
        metrics.score_line("abcd", "abcd", metrics.PHILIUMM_POLICY),  # 0/4
        metrics.score_line("abcd", "abXd", metrics.PHILIUMM_POLICY),  # 1/4
    ]
    # micro CER = (0 + 1) / (4 + 4) = 0.125
    assert metrics.cer(scores) == pytest.approx(0.125)
    # macro CER = mean(0, 0.25) = 0.125 here (equal lengths) — check the func runs.
    assert metrics.macro_cer(scores) == pytest.approx(0.125)


def test_cer_normalization_matters() -> None:
    # Case-only difference: strict counts it, lenient folds it away.
    strict = metrics.score_line("Abc", "abc", metrics.STRICT_POLICY)
    lenient = metrics.score_line("Abc", "abc", metrics.LENIENT_POLICY)
    assert strict.char_edits == 1
    assert lenient.char_edits == 0


# -- bootstrap -------------------------------------------------------------- #


def test_bootstrap_ci_deterministic_and_brackets_point() -> None:
    scores = [
        metrics.score_line("abcdefghij", "abcdefghij", metrics.PHILIUMM_POLICY) for _ in range(20)
    ]
    scores += [
        metrics.score_line("abcdefghij", "abcdefXhij", metrics.PHILIUMM_POLICY) for _ in range(20)
    ]
    a = metrics.bootstrap_ci(scores, metric="cer", n_resamples=200, seed=7)
    b = metrics.bootstrap_ci(scores, metric="cer", n_resamples=200, seed=7)
    assert (a.lo, a.point, a.hi) == (b.lo, b.point, b.hi)  # deterministic
    assert a.lo <= a.point <= a.hi
    assert 0.0 <= a.lo and a.hi <= 1.0


def test_bootstrap_ci_empty() -> None:
    iv = metrics.bootstrap_ci([], metric="cer", n_resamples=10)
    assert iv.point == 0.0 and iv.lo == 0.0 and iv.hi == 0.0


def test_interval_as_pct() -> None:
    iv = metrics.Interval(point=0.08, lo=0.07, hi=0.09, confidence=0.95, n_resamples=100)
    p, lo, hi = iv.as_pct()
    assert (round(p, 1), round(lo, 1), round(hi, 1)) == (8.0, 7.0, 9.0)
