"""Whose hand a catalogue piece is in, from its ``Textart`` and its sender.

One rule for every census (the C2b reach census, the K1 German census, C3's
strata by hand), so their shares measure the same thing. The catalogue writes
the document type and the hand together: ``Abf., eigh.`` is a letter as sent,
in its author's own hand; ``Konz.; eigh.`` an autograph draft; but ``Abf.;
eigh. Aufschr.`` is a scribe's fair copy whose *address* alone is autograph,
and ``eigh. Korr.`` a scribe's text with autograph corrections. The C2b census
counted every ``eigh.`` as the author's hand (2026-10), so its share of lines
"in Leibniz's own hand" included the scribes' copies; the K1 census already
told them apart.

* :func:`hand_from_textart` — ``own`` (the piece itself is autograph),
  ``partial`` (only an address, a correction, a postscript or a signature
  is), ``other`` (no ``eigh.`` at all), ``none`` (no Textart).
* :func:`is_leibniz_name` — the sender is Gottfried Wilhelm Leibniz himself,
  as the catalogue names him (``Leibniz (GND)``), not a namesake such as his
  half-brother Johann Friedrich (``Leibniz,J.F.``), whom a substring test took
  for him.
* :func:`is_leibniz_hand` — the piece is autograph and its author is Leibniz:
  a letter he sent, or a writing (no sender).
"""

from __future__ import annotations

import re

HANDS: tuple[str, ...] = ("own", "partial", "other", "none")

# Textart abbreviations that name the document itself, so "eigh. <one of these>"
# says the whole piece is autograph (as "eigh." alone does); "eigh." before any
# other word (Aufschr., Anschr., Korr., Nachschr., Zusatz, Unterschr., Verm.)
# qualifies that part only.
DOCUMENT_TYPES: frozenset[str] = frozenset(
    {"abf", "konz", "reinschr", "abschr", "ausz", "mf", "entw", "aufz", "notiz", "text", "exz"}
)

# The catalogue's authority markers after a name: "Leibniz (GND)",
# "Fuchs,P. (KorrespDB) (GND)".
_MARKERS = re.compile(r"\((?:GND|KorrespDB)\)", re.IGNORECASE)
_LEIBNIZ_FORMS: frozenset[str] = frozenset(
    {
        "leibniz",
        "leibniz, gottfried wilhelm",
        "leibniz,gottfried wilhelm",
        "leibniz, g. w.",
        "leibniz,g.w.",
        "leibniz, g.w.",
        "gottfried wilhelm leibniz",
        "g. w. leibniz",
        "g.w. leibniz",
    }
)


def hand_from_textart(textart: str | None) -> str:
    """``own`` | ``partial`` | ``other`` | ``none`` from the catalogue's Textart."""
    if textart is None or not textart.strip():
        return "none"
    t = textart.lower()
    if "eigh" not in t:
        return "other"
    for raw in t.replace(";", ",").split(","):
        seg = raw.strip()
        if not seg.startswith("eigh"):
            continue
        rest = seg[4:].lstrip(".").strip()
        if not rest or rest.split()[0].rstrip(".") in DOCUMENT_TYPES:
            return "own"
    return "partial"


def is_leibniz_name(name: str | None) -> bool:
    """Whether a catalogue name is Gottfried Wilhelm Leibniz himself."""
    if not name:
        return False
    plain = " ".join(_MARKERS.sub(" ", name).split()).rstrip(",").casefold()
    return plain in _LEIBNIZ_FORMS


def is_leibniz_hand(hand: str | None, absender: str | None) -> bool:
    """The piece is in its author's own hand, and the author is Leibniz (a
    letter he sent, or a writing with no sender)."""
    return hand == "own" and (not absender or is_leibniz_name(absender))


__all__ = [
    "DOCUMENT_TYPES",
    "HANDS",
    "hand_from_textart",
    "is_leibniz_hand",
    "is_leibniz_name",
]
