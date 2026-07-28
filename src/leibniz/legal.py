"""Copyright-expiry registry for Akademie-Ausgabe (AA) reading text.

This module encodes, as structured data, which Leibniz Academy Edition volumes'
**constituted reading text** may be redistributed today, and when the rest
become free. It is the single machine-readable source of truth for the §70/§71
math the project must never get wrong (SPECS §1.4, §7.2).

The legal rule
--------------
German copyright grants two relevant 25-year neighbouring rights, both measured
from *first publication*:

* **§70 UrhG** — *wissenschaftliche Ausgaben*: the editorial achievement of a
  scientific edition (the constituted reading text, its ordering) is protected
  for 25 years.
* **§71 UrhG** — *editio princeps*: whoever first lawfully publishes a
  previously unpublished work that is itself out of copyright gets 25 years.
  Much of the Nachlass is first made public *in* the AA volumes, so this can
  attach to the text as well as to the edition.

Both terms are computed under the **calendar-year rule (§69 UrhG)**: the clock
starts at the *end* of the calendar year of publication. A volume published in
year *Y* is therefore protected through the end of *Y+25* and enters the public
domain on **1 January of Y+26**. One date per volume clears both §70 and §71,
because both run from the same first-publication event. Hence:

    free_from = date(first_publication_year + 26, 1, 1)

Worked anchors (all cross-checked against leibnizedition.de, July 2026):
    I,17  published 2001  -> free 2027-01-01
    VII,8 published 2024  -> free 2050-01-01

The hard rule (SPECS §7.2)
--------------------------
Only the *reading text* of an expired volume may be extracted or redistributed.
Editor introductions, apparatus, commentary, and indices are ordinary §2 works
(70 years p.m.a.) and are **never** touched, regardless of the volume's §70/§71
status. This registry says *when a volume's reading text is free*; it does not
license anything else in the book.

Re-editions restart the clock
-----------------------------
A genuinely reworked new edition (*Neubearbeitung*) is a fresh scientific
edition with its own 25-year term; a mere *durchgesehener Nachdruck* (reviewed
reprint) is not. Where a later reworked edition is itself already expired we
keep one entry; where it is still protected we list it separately so its date
is tracked. The load-bearing case is **II,1**: the 1926 text is long free, but
the 2006 *Neubearbeitung* is protected until 2032 — extract from the 1926 print.

Coverage & maintenance
----------------------
The registry lists every volume with a *confirmed* first-publication year
through the near-term expiry horizon (all volumes free today, all volumes
expiring by 2050 in the series we care about). It is deliberately not an
exhaustive catalogue of all ~60 AA volumes: later volumes are added as their
years are verified. The public domain grows every 1 January, so re-run
:func:`upcoming_expiries` rather than trusting a cached list. Re-verify against
leibnizedition.de before relying on any single date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# The calendar-year offset: 25-year term (§70/§71) + §69 rounding to the end of
# the publication year => public domain on 1 January of publication_year + 26.
FREE_AFTER_YEARS = 26

# Reihen (series) referenced by this registry, as Roman numerals.
_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 6: "VI", 7: "VII"}

# Attribution / usage reminder for anything that consumes expired reading text.
READING_TEXT_ONLY = (
    "Use only the constituted READING TEXT of an expired AA volume. Never "
    "extract or redistribute editor introductions, apparatus, commentary, or "
    "indices — those remain protected as ordinary §2 works (SPECS §7.2)."
)


@dataclass(frozen=True, slots=True)
class Volume:
    """One AA volume (or a distinct edition of one) and its expiry date.

    ``volume`` is usually an ``int`` but may be a string for non-numbered parts
    (e.g. the Reihe I Harz *Supplementband*), mirroring the AA's own
    bibliography. ``edition`` distinguishes re-editions of the same volume
    (e.g. II,1 ``"1926"`` vs ``"2006"``); ``None`` means the volume has a single
    edition.
    """

    series: int
    volume: int | str
    first_publication_year: int
    edition: str | None = None
    note: str | None = None

    @property
    def series_roman(self) -> str:
        return _ROMAN.get(self.series, str(self.series))

    @property
    def free_from_year(self) -> int:
        """Calendar year in which the reading text enters the public domain."""
        return self.first_publication_year + FREE_AFTER_YEARS

    @property
    def free_from(self) -> date:
        """Exact date the reading text becomes free (1 January of that year)."""
        return date(self.free_from_year, 1, 1)

    @property
    def label(self) -> str:
        """Human-readable id, e.g. ``"I,17"`` or ``"II,1 (1926)"``."""
        base = f"{self.series_roman},{self.volume}"
        return f"{base} ({self.edition})" if self.edition else base

    @property
    def key(self) -> tuple[int, str, str]:
        """Stable identity of this entry: (series, volume, edition)."""
        return (self.series, str(self.volume), self.edition or "")

    def is_expired(self, today: date) -> bool:
        """True if the reading text is redistributable on ``today``."""
        return today >= self.free_from


# --------------------------------------------------------------------------- #
# The registry
# --------------------------------------------------------------------------- #
# First-publication years verified against leibnizedition.de (the edition's own
# Forschungsstellen), cross-checked against gwlb.de, rep.adw-goe.de, and
# De Gruyter, July 2026. See STATUS.md for the audit trail and open questions.

REGISTRY: tuple[Volume, ...] = (
    # Reihe I — Allgemeiner politischer und historischer Briefwechsel
    Volume(1, 1, 1923),
    Volume(1, 2, 1927),
    Volume(1, 3, 1938),
    Volume(1, 4, 1950),
    Volume(1, 5, 1954),
    Volume(1, 6, 1957),
    Volume(1, 7, 1964),
    Volume(1, 8, 1970),
    Volume(1, 9, 1975),
    Volume(1, 10, 1979),
    Volume(1, 11, 1982),
    # I,13 (1987) appeared before I,12 (1990): volumes are numbered by the
    # period they cover, not publication order. Both long expired.
    Volume(1, 12, 1990),
    Volume(1, 13, 1987),
    Volume(1, 14, 1993),
    Volume(1, 15, 1998),
    Volume(1, 16, 2000),  # boundary: free 2026-01-01
    Volume(1, 17, 2001),  # boundary: protected until 2027-01-01
    Volume(
        1, "Suppl", 1991, note="Supplementband Harzbergbau (1692–1696); outside main numbering."
    ),
    # Reihe II — Philosophischer Briefwechsel
    Volume(
        2, 1, 1926, edition="1926", note="First edition (Darmstadt); reading text long expired."
    ),
    Volume(
        2,
        1,
        2006,
        edition="2006",
        note="Völlig neubearbeitete Auflage (Berlin) — a fresh scientific edition; "
        "protected until 2032. Extract from the 1926 print, not this one.",
    ),
    # Reihe III — Mathematischer, naturwissenschaftlicher u. technischer Briefwechsel
    Volume(3, 1, 1976, note="2nd ed. 1988 (also expired)."),
    Volume(3, 2, 1987),
    Volume(3, 3, 1991),
    Volume(3, 4, 1995),  # boundary
    Volume(3, 5, 2003),  # boundary: protected until 2029-01-01
    # Reihe IV — Politische Schriften
    Volume(4, 1, 1931, note="3rd ed. 1983 (also expired)."),
    Volume(4, 2, 1963, note="2nd ed. 1984 (also expired)."),
    Volume(4, 3, 1986),  # boundary
    Volume(4, 4, 2001),  # boundary: protected until 2027-01-01
    # Reihe VI — Philosophische Schriften  (VI,5 not yet in print as of 2026)
    Volume(6, 1, 1930, note="Durchgesehener Nachdruck 1990 (reprint does not restart the term)."),
    Volume(6, 2, 1966, note="Durchgesehener Nachdruck 1990."),
    Volume(6, 3, 1980, note="Source ±1yr (site reads 1981); legally immaterial, long expired."),
    Volume(6, 4, 1999, note="Issued in four parts A–D, all 1999."),
    Volume(6, 6, 1962, note="Nouveaux Essais; durchgesehener Nachdruck 1990."),
    # Reihe VII — Mathematische Schriften
    Volume(7, 1, 1990),
    Volume(7, 2, 1996),  # boundary
    Volume(7, 3, 2003),  # boundary: protected until 2029-01-01
    Volume(7, 4, 2008),
    Volume(7, 5, 2008, note="Companion to VII,4 (same year)."),
    Volume(7, 6, 2012),
    Volume(7, 7, 2019),
    Volume(7, 8, 2024),  # anchor: protected until 2050-01-01
)


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #


def _sort_key(v: Volume) -> tuple:
    numeric = isinstance(v.volume, int)
    return (
        v.series,
        0 if numeric else 1,
        v.volume if numeric else 0,
        str(v.volume),
        v.edition or "",
    )


def expired_volumes(today: date, registry: tuple[Volume, ...] = REGISTRY) -> list[Volume]:
    """Volumes whose reading text is redistributable on ``today``.

    "Usable" means the §70/§71 term has run out — i.e. ``today`` is on or after
    the volume's ``free_from`` date. The result is sorted by series then volume.
    """
    return sorted((v for v in registry if v.is_expired(today)), key=_sort_key)


def protected_volumes(today: date, registry: tuple[Volume, ...] = REGISTRY) -> list[Volume]:
    """The complement of :func:`expired_volumes`: still-protected volumes."""
    return sorted((v for v in registry if not v.is_expired(today)), key=_sort_key)


def upcoming_expiries(today: date, registry: tuple[Volume, ...] = REGISTRY) -> list[Volume]:
    """Still-protected volumes, soonest to expire first (then by series/volume).

    Handy for the "new expiries every 1 January" ticker (SPECS §1.4): the first
    group shares the nearest ``free_from`` date.
    """
    return sorted(
        (v for v in registry if not v.is_expired(today)),
        key=lambda v: (v.free_from_year, _sort_key(v)),
    )


def get_volume(
    series: int,
    volume: int | str,
    edition: str | None = None,
    registry: tuple[Volume, ...] = REGISTRY,
) -> Volume | None:
    """Look up one registry entry by (series, volume, edition), or ``None``."""
    for v in registry:
        if v.series == series and v.volume == volume and v.edition == edition:
            return v
    return None


__all__ = [
    "FREE_AFTER_YEARS",
    "READING_TEXT_ONLY",
    "REGISTRY",
    "Volume",
    "expired_volumes",
    "get_volume",
    "protected_volumes",
    "upcoming_expiries",
]
