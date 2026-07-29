"""Lightweight shelfmark family classification — for census coverage only.

A0's job here is narrow: given a work's ``mods:shelfLocator`` strings, decide
which Leibniz signature *family* it carries (LH / LBr / Leibn. Marg. / LK), so
``reports/census.md`` can state "how many works have a parseable LH/LBr
signature". This is deliberately **not** the robust normaliser A3 needs (that
one canonicalises ``LH 35, I, 17`` ↔ ``LH XXXV, I, 17`` for cross-walking to the
Ritter-Katalog and is specified in Phase A3). Keep this simple and permissive.

Signature families observed live in the GWLB METS (2026-07-28):
    LH   — Leibniz-Handschriften        "LH 4, 6, 18", "LH XLII,5", "LH XXXV, XV, I"
    LBr  — Leibniz-Briefwechsel         "LBr. 102", "LBr 57,1", "LBr. 703 Bl. 28"
    Marg — Leibniz-Marginalien          "Leibn. Marg. 11", "ZEN Leibn. Marg. 47"
    LK   — Leibniz-Konvolut / LK-MOW    "LK-MOW ..."
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# The families we count as a "parseable Leibniz signature". Priority order: the
# most specific pattern wins when a string could match more than one.
RECOGNISED = ("Marg", "LBr", "LK", "LH")

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Marg", re.compile(r"\bLeibn\.?\s*Marg", re.IGNORECASE)),
    ("LBr", re.compile(r"\bLBr\b", re.IGNORECASE)),
    ("LK", re.compile(r"\bLK[-\s]", re.IGNORECASE)),
    ("LH", re.compile(r"\bLH\b")),  # case-sensitive: 'LH' the signature, not words
)


def classify_shelfmark(shelfmark: str) -> str | None:
    """Return the signature family of one shelfmark string, or ``None``.

    ``None`` means "present but unrecognised" is *not* returned here — an empty
    string yields ``None``; a non-empty unrecognised string yields ``"other"``.
    """
    if not shelfmark or not shelfmark.strip():
        return None
    for family, pattern in _PATTERNS:
        if pattern.search(shelfmark):
            return family
    return "other"


def work_family(shelfmarks: Iterable[str]) -> str | None:
    """Best signature family across a work's shelfmarks.

    Returns a recognised family if any shelfmark matches one (most specific
    across the list wins), else ``"other"`` if there are shelfmarks but none
    parse, else ``None`` if the work has no shelfmark at all.
    """
    families = [f for f in (classify_shelfmark(s) for s in shelfmarks) if f is not None]
    if not families:
        return None
    for family in RECOGNISED:
        if family in families:
            return family
    return "other"


__all__ = ["RECOGNISED", "classify_shelfmark", "work_family"]
