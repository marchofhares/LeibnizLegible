"""Tests for the coarse shelfmark family classifier (census coverage)."""

from __future__ import annotations

import pytest

from leibniz.harvest import shelfmarks


@pytest.mark.parametrize(
    ("text", "family"),
    [
        ("LH 4, 6, 18", "LH"),
        ("LH XXXV, XV, I", "LH"),
        ("LH 35, I, 17, Bl. 1 - 17", "LH"),
        ("LBr. 102", "LBr"),
        ("LBr 57,1", "LBr"),
        ("LBr. 703 Bl. 28", "LBr"),
        ("Leibn. Marg. 11", "Marg"),
        ("ZEN Leibn. Marg. 47", "Marg"),
        ("LK-MOW Kaestner1", "LK"),
        ("1729805", "other"),
        ("Ms XX3", "other"),
        ("", None),
        ("   ", None),
    ],
)
def test_classify_shelfmark(text: str, family: str | None) -> None:
    assert shelfmarks.classify_shelfmark(text) == family


def test_work_family_none_when_no_shelfmarks() -> None:
    assert shelfmarks.work_family([]) is None


def test_work_family_prefers_recognised_over_other() -> None:
    assert shelfmarks.work_family(["some junk", "LBr. 5"]) == "LBr"


def test_work_family_other_when_present_but_unrecognised() -> None:
    assert shelfmarks.work_family(["1729805"]) == "other"


def test_work_family_specificity_order() -> None:
    # Marg outranks a bare LH-looking token if both somehow appear.
    assert shelfmarks.work_family(["LH 1", "Leibn. Marg. 2"]) == "Marg"
