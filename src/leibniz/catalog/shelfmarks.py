"""Robust Leibniz shelfmark normalisation — the crosswalk's secondary key (A3).

The census (A1) has a *coarse* family classifier (:mod:`leibniz.harvest.shelfmarks`);
this is the real thing A3 needs: a normaliser that maps the many written forms of
a signature onto one canonical key, so a katalog record's signature can be matched
to a work's ``shelfLocator`` even when the two spell it differently.

The variation seen in live GWLB METS and katalog rows:

* **Roman vs Arabic** first group — ``LH XXXV, 3, 5`` == ``LH 35, 3, 5``.
* **Punctuation / spacing** — ``LBr. 57,1`` == ``LBr 57, 1``.
* **Leaf suffix** — ``LBr. 703 Bl. 28`` is a folio *within* work ``LBr 703``; the
  ``Bl.`` part is captured separately so it never blocks a work-level match.
* **Location prefixes** — ``ZEN Leibn. Marg. 47`` (the ``ZEN`` shelf prefix), the
  ``LK-MOW`` subfamily, alphanumeric sub-parts (``LH 35, 13, 2c``).

Families recognised: ``LH`` (Handschriften), ``LBr`` (Briefwechsel), ``Marg``
(Leibn. Marg.), ``LK`` (Konvolut / LK-MOW). Anything else (British Library,
Paris, …) normalises to ``family=None`` and never produces a match key.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

# Family label patterns, matched in priority order (most specific first). Each
# captures nothing itself; the numeric tail is whatever follows the label.
_FAMILY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Marg", re.compile(r"Leibn\.?\s*Marg\.?", re.IGNORECASE)),
    ("LBr", re.compile(r"\bLBr\b\.?", re.IGNORECASE)),
    ("LK", re.compile(r"\bLK\b[-\s]?", re.IGNORECASE)),
    ("LH", re.compile(r"\bLH\b\.?")),  # case-sensitive: the signature, not a word
)

# A leaf/folio reference: "Bl. 28", "Blatt 12", "Bl. 67-70", "Bl. 12r".
_BLATT = re.compile(
    r"\bBl(?:att|\.|\b)\.?\s*([0-9]+[a-z]?(?:\s*[-–]\s*[0-9]+[a-z]?)?)", re.IGNORECASE
)

_ROMAN_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)
_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def roman_to_int(token: str) -> int | None:
    """Convert a Roman-numeral token to an int, or ``None`` if it isn't valid.

    Validates by round-tripping (``int → canonical Roman == input``), so stray
    letter-strings that merely happen to use ``I/V/X/L/C/D/M`` (or malformed
    numerals like ``IIII``) are rejected rather than silently mis-parsed.
    """
    if not token or not _ROMAN_RE.match(token):
        return None
    s = token.upper()
    total, prev = 0, 0
    for ch in reversed(s):
        val = _ROMAN_VALUES[ch.lower()]
        total += -val if val < prev else val
        prev = max(prev, val)
    return total if _int_to_roman(total) == s else None


def _int_to_roman(n: int) -> str:
    table = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    out = []
    for value, sym in table:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)


@dataclass(frozen=True, slots=True)
class Signature:
    """A parsed shelfmark: its family, canonical parts, and any leaf reference."""

    raw: str
    family: str | None
    parts: tuple[str, ...]
    blatt: str | None = None

    @property
    def key(self) -> str | None:
        """Canonical work-level match key (``"LH 35,3,5"``), or ``None`` if foreign.

        Excludes the leaf reference, so two records on different folios of the same
        work share a key. ``None`` (unrecognised family, or a family with no numeric
        tail) never matches anything — a deliberate guard against false positives.
        """
        if self.family is None or not self.parts:
            return None
        return f"{self.family} {','.join(self.parts)}"


def _norm_token(token: str) -> str | None:
    """Normalise one component: Roman→Arabic, lowered, punctuation stripped."""
    t = token.strip().strip(".,;:()").strip()
    if not t:
        return None
    as_roman = roman_to_int(t)
    if as_roman is not None:
        return str(as_roman)
    return t.lower()


def normalize_signature(raw: str) -> Signature:
    """Parse one shelfmark string into a canonical :class:`Signature`."""
    text = " ".join((raw or "").split())
    family = None
    tail = ""
    best = len(text) + 1
    for fam, pat in _FAMILY_PATTERNS:
        m = pat.search(text)
        if m is not None and m.start() < best:
            family, tail, best = fam, text[m.end() :], m.start()
    if family is None:
        return Signature(raw=raw, family=None, parts=())

    # Work-level normalisation: a parenthetical note or a page reference ("S."
    # Seite) points *inside* a work, not at it — drop them so the key stays
    # work-level and stray prose can't leak into it. Leaf ("Bl.") refs are
    # captured below, not dropped; part markers ("Stück") are kept, since a Stück
    # is itself a distinct work (STATUS Open Q #4).
    tail = tail.split("(", 1)[0]
    tail = re.split(r"\bS\.\s", tail, maxsplit=1)[0]

    blatt = None
    bm = _BLATT.search(tail)
    if bm is not None:
        blatt = re.sub(r"\s*", "", bm.group(1))
        tail = tail[: bm.start()] + " " + tail[bm.end() :]

    tokens = re.split(r"[,\s]+", tail.strip())
    parts = tuple(p for p in (_norm_token(t) for t in tokens) if p)
    return Signature(raw=raw, family=family, parts=parts, blatt=blatt)


def signature_key(raw: str) -> str | None:
    """Convenience: the canonical match key for one shelfmark string."""
    return normalize_signature(raw).key


def signature_keys(shelfmarks: Iterable[str]) -> set[str]:
    """All distinct match keys across a work's (possibly variant) shelfmarks."""
    return {k for s in shelfmarks if (k := signature_key(s)) is not None}


__all__ = [
    "Signature",
    "normalize_signature",
    "roman_to_int",
    "signature_key",
    "signature_keys",
]
