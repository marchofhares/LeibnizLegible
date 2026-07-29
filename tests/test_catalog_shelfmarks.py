"""Tests for the robust shelfmark normaliser — against messy real signatures."""

from __future__ import annotations

import pytest

from leibniz.catalog import shelfmarks as sm

# -- Roman numerals --------------------------------------------------------- #


@pytest.mark.parametrize(
    ("token", "expected"),
    [("XXXV", 35), ("XLII", 42), ("XV", 15), ("I", 1), ("VI", 6), ("iv", 4)],
)
def test_roman_to_int_valid(token: str, expected: int) -> None:
    assert sm.roman_to_int(token) == expected


@pytest.mark.parametrize("token", ["MoW", "IIII", "abc", "", "2c", "VC"])
def test_roman_to_int_rejects_non_roman(token: str) -> None:
    assert sm.roman_to_int(token) is None


# -- Normalisation: the load-bearing equivalences --------------------------- #


def test_roman_and_arabic_first_group_match() -> None:
    a = sm.normalize_signature("LH XXXV, 3, 5")
    b = sm.normalize_signature("LH 35, 3, 5")
    assert a.family == "LH" and a.parts == ("35", "3", "5")
    assert a.key == b.key == "LH 35,3,5"


def test_punctuation_and_spacing_normalised() -> None:
    assert sm.signature_key("LBr. 57,1") == sm.signature_key("LBr 57, 1") == "LBr 57,1"


def test_blatt_is_captured_and_excluded_from_key() -> None:
    s = sm.normalize_signature("LBr. 703 Bl. 28")
    assert s.family == "LBr" and s.parts == ("703",)
    assert s.blatt == "28"
    assert s.key == "LBr 703"  # leaf does not block a work-level match


def test_blatt_range_and_alphanumeric_subpart() -> None:
    s = sm.normalize_signature("LH 35, 13, 2c Bl. 64")
    assert s.parts == ("35", "13", "2c")
    assert s.blatt == "64"
    assert s.key == "LH 35,13,2c"


def test_all_roman_groups_converted() -> None:
    assert sm.signature_key("LH XXXV, XV, I") == "LH 35,15,1"
    assert sm.signature_key("LH XLII,5") == "LH 42,5"


def test_marginalien_family_and_zen_prefix() -> None:
    assert sm.signature_key("Leibn. Marg. 11") == "Marg 11"
    # A shelf-location prefix before the signature must not defeat recognition.
    assert sm.signature_key("ZEN Leibn. Marg. 47") == "Marg 47"


def test_lk_mow_subfamily() -> None:
    s = sm.normalize_signature("LK-MOW 12")
    assert s.family == "LK"
    assert s.key == "LK mow,12"


def test_seite_page_reference_dropped_from_key() -> None:
    # "S." (Seite) is a page *within* a Marginalien work — excluded from the key.
    assert sm.signature_key("Leibn. Marg. 10, 1, S. 154-166") == "Marg 10,1"
    assert sm.signature_key("Leibn. Marg. 10, 1, S. 167-169") == "Marg 10,1"


def test_parenthetical_note_dropped_from_key() -> None:
    # Descriptive prose in parentheses must not leak (stray words) into the key.
    s = sm.normalize_signature("Leibn. Marg. 10, 1, S. 172-178 (L' Handexpl. d. Erstdr.)")
    assert s.key == "Marg 10,1"


def test_stueck_part_is_kept_as_distinct_work() -> None:
    # A Stück is its own work (Open Q #4), so it stays in the key.
    assert sm.signature_key("Leibn. Marg. 16, Stück 2") == "Marg 16,stück,2"
    assert sm.signature_key("Leibn. Marg. 16, Stück 1") == "Marg 16,stück,1"


def test_foreign_signature_has_no_key() -> None:
    s = sm.normalize_signature("London BL Add.Mss. 4294 Bl. 67-70")
    assert s.family is None
    assert s.key is None  # never matches a Hannover work


def test_empty_and_garbage() -> None:
    assert sm.normalize_signature("").key is None
    assert sm.normalize_signature("   ").key is None
    assert sm.signature_key("Paris, BnF") is None


# -- Aggregation across a work's shelfmarks --------------------------------- #


def test_signature_keys_dedupes_variant_spellings() -> None:
    # GWLB stores the same signature twice, Roman and Arabic — one key results.
    keys = sm.signature_keys(["LH XXXV, 3, 5", "LH 35, 3, 5"])
    assert keys == {"LH 35,3,5"}


def test_signature_keys_drops_foreign() -> None:
    keys = sm.signature_keys(["LBr. 57,1", "London BL 4294"])
    assert keys == {"LBr 57,1"}
