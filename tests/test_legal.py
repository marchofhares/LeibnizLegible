"""Tests for the §70/§71 expiry registry.

Includes the boundary cases the build prompt names explicitly (I,17 free from
2027-01-01; VII,8 not free until 2050) and a consistency check that the registry
reproduces the "free today" list asserted in SPECS §1.4.
"""

from __future__ import annotations

from datetime import date

from leibniz import legal
from leibniz.legal import expired_volumes, get_volume, upcoming_expiries


def test_calendar_year_rule() -> None:
    # free_from = publication_year + 26, on 1 January (SPECS §1.4 / §69 UrhG).
    assert legal.FREE_AFTER_YEARS == 26
    v = get_volume(1, 17)
    assert v is not None
    assert v.first_publication_year == 2001
    assert v.free_from_year == 2027
    assert v.free_from == date(2027, 1, 1)


def test_boundary_i17_free_from_2027() -> None:
    v = get_volume(1, 17)
    assert v is not None
    assert v.free_from == date(2027, 1, 1)
    # Protected through the end of 2026, free on 2027-01-01.
    assert v.is_expired(date(2026, 12, 31)) is False
    assert v.is_expired(date(2027, 1, 1)) is True
    assert v not in expired_volumes(date(2026, 12, 31))
    assert v in expired_volumes(date(2027, 1, 1))


def test_boundary_vii8_not_until_2050() -> None:
    v = get_volume(7, 8)
    assert v is not None
    assert v.first_publication_year == 2024
    assert v.free_from == date(2050, 1, 1)
    assert v.is_expired(date(2049, 12, 31)) is False
    assert v.is_expired(date(2050, 1, 1)) is True
    # Nowhere near free today.
    assert v not in expired_volumes(date(2026, 7, 28))


def test_i16_is_free_today() -> None:
    # The other side of the I,16/I,17 boundary: I,16 (2000) freed 2026-01-01.
    v = get_volume(1, 16)
    assert v is not None
    assert v.free_from == date(2026, 1, 1)
    assert v.is_expired(date(2026, 7, 28)) is True


def test_ii1_dual_edition() -> None:
    # 1926 reading text long free; the 2006 Neubearbeitung is its own edition,
    # protected until 2032.
    first = get_volume(2, 1, edition="1926")
    revised = get_volume(2, 1, edition="2006")
    assert first is not None and revised is not None
    assert first.is_expired(date(2026, 7, 28)) is True
    assert revised.free_from == date(2032, 1, 1)
    assert revised.is_expired(date(2026, 7, 28)) is False
    assert first.label == "II,1 (1926)"
    assert revised.label == "II,1 (2006)"


def test_free_today_matches_specs_1_4() -> None:
    # SPECS §1.4: free today (published <=2000) =
    #   Reihe I,1-16 + Harz supplement; II,1 (1926 text); III,1-4; IV,1-3;
    #   VI,1-4 + VI,6; VII,1-2.
    expected = (
        {f"I,{n}" for n in range(1, 17)}
        | {"I,Suppl", "II,1 (1926)"}
        | {f"III,{n}" for n in (1, 2, 3, 4)}
        | {f"IV,{n}" for n in (1, 2, 3)}
        | {f"VI,{n}" for n in (1, 2, 3, 4, 6)}
        | {f"VII,{n}" for n in (1, 2)}
    )
    got = {v.label for v in expired_volumes(date(2026, 7, 28))}
    assert got == expected


def test_upcoming_expiries_2027_group() -> None:
    # SPECS §1.4: "2027: I,17 + IV,4".
    pending = upcoming_expiries(date(2026, 7, 28))
    assert pending  # something is still protected
    soonest_year = pending[0].free_from_year
    assert soonest_year == 2027
    group_2027 = {v.label for v in pending if v.free_from_year == 2027}
    assert group_2027 == {"I,17", "IV,4"}


def test_upcoming_expiries_2029_group() -> None:
    # SPECS §1.4: "2029: III,5 + VII,3".
    pending = upcoming_expiries(date(2026, 7, 28))
    group_2029 = {v.label for v in pending if v.free_from_year == 2029}
    assert group_2029 == {"III,5", "VII,3"}


def test_expired_and_protected_partition() -> None:
    # For any date, expired + protected exactly partition the registry.
    for d in (date(2020, 1, 1), date(2026, 7, 28), date(2030, 6, 1), date(2060, 1, 1)):
        exp = expired_volumes(d)
        prot = legal.protected_volumes(d)
        assert len(exp) + len(prot) == len(legal.REGISTRY)
        assert {v.key for v in exp}.isdisjoint({v.key for v in prot})


def test_registry_keys_are_unique() -> None:
    keys = [v.key for v in legal.REGISTRY]
    assert len(keys) == len(set(keys))


def test_expired_volumes_are_sorted() -> None:
    vols = expired_volumes(date(2026, 7, 28))
    # Reihe I comes before II/III/IV/VI/VII; check series ordering is stable.
    series_seen = [v.series for v in vols]
    assert series_seen == sorted(series_seen)
