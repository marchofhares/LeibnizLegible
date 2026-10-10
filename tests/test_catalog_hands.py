"""The shared hand rule (2026-10): the reach census and the K1 census agree."""

from __future__ import annotations

import pytest

from leibniz.catalog.hands import hand_from_textart, is_leibniz_hand, is_leibniz_name


@pytest.mark.parametrize(
    ("textart", "hand"),
    [
        ("Abf., eigh.", "own"),
        ("Konz.; eigh.", "own"),
        ("eigh. Konz.", "own"),
        ("Abf.; eigh. Aufschr.", "partial"),
        ("Abschr.; eigh. Korr.", "partial"),
        ("Abf.", "other"),
        ("", "none"),
        (None, "none"),
    ],
)
def test_hand_from_textart(textart: str | None, hand: str) -> None:
    assert hand_from_textart(textart) == hand


@pytest.mark.parametrize(
    ("name", "is_him"),
    [
        ("Leibniz (GND)", True),
        ("Leibniz", True),
        ("Leibniz, Gottfried Wilhelm", True),
        ("Leibniz,J.F. (KorrespDB) (GND)", False),  # his half-brother, not him
        ("Leibniz, Johann Friedrich", False),
        ("Bernoulli,Joh. (KorrespDB) (GND)", False),
        ("", False),
        (None, False),
    ],
)
def test_is_leibniz_name(name: str | None, is_him: bool) -> None:
    assert is_leibniz_name(name) is is_him


def test_is_leibniz_hand() -> None:
    assert is_leibniz_hand("own", None)  # a writing: no sender
    assert is_leibniz_hand("own", "Leibniz (GND)")
    assert not is_leibniz_hand("own", "Leibniz,J.F. (KorrespDB) (GND)")
    assert not is_leibniz_hand("partial", "Leibniz (GND)")  # only the address is his
