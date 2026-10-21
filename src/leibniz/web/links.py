"""Links out (2026-10): where a reader goes from a piece to what the scholarship
holds about it — the catalogue record, the volume of the Akademie-Ausgabe, the
Leibniz-Archiv's transcriptions of the late letters. (The exact folio at the
GWLB is :func:`leibniz.web.attribution.gwlb_page_url`.)

Every address here was checked live on 2026-10-10. Two traps decided the shape:

* The Leibniz-Katalog has no page per record. Its extended search takes an
  ``id`` that it matches as a *substring* (``id=1820`` answers 17 records);
  the record's catalogue number (``katnr``) beside it narrows that to one.
* The GWLB's repository answers an unknown address with its index page and a
  200, so a volume is linked only where its own page was seen: Reihe I
  volumes 3, 9, 11, 12, 14–27, Reihe III 5–9, Reihe VII 3–8 (CC BY-NC 4.0).
* The same search takes ``sign_ol`` and matches it as a substring of the
  record's Signatur, so a work's shelfmark finds the records on its folios
  whether or not this site holds them. The catalogue spells a shelfmark its
  own way, and the search is a plain substring match, so the spelling must be
  its: Arabic numerals throughout (its Signatur column says so: "Römische
  Zahlen werden als arabische wiedergegeben"), ``LBr`` *without* the period
  the library writes, ``Leibn. Marg.``, the F series run together as
  ``LBrF 20``, ``, Stück 1`` and ``175:1`` as the library has them. Checked
  live on 2026-10-21: ``LH 4, 6, 18`` answers the two records on its folios,
  ``LBr 464`` eleven and ``LBr. 464`` none, ``Leibn. Marg. 196`` one,
  ``LBrF 1`` the F series, ``Leibn. Marg. 135`` its four Stücke.
  :func:`katalog_spelling` turns the library's ``LH IV, 6, 18`` / ``LBr. 464``
  into the catalogue's.

Other volumes go to the page that offers them — the Potsdam Arbeitsstellen
(Reihe IV, VIII), the Münster Forschungsstelle (Reihe II, VI: a permission
page) — or to their series at leibnizedition.de.
"""

from __future__ import annotations

import re
from urllib.parse import urlencode

from leibniz.catalog.shelfmarks import roman_to_int, split_family

KATALOG_SEARCH = "https://leibniz-katalog.bbaw.de/de/extended-search"
GWLB_REPOSITORY = "https://www.gwlb.de/leibniz/digitale-ressourcen/repositorium-des-leibniz-archivs"
EDITION_SERIES = "https://www.leibnizedition.de/de/reihen/reihe-{roman}/"
ROMAN = {1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v", 6: "vi", 7: "vii", 8: "viii"}

# The volumes with their own page in the GWLB repository (checked one by one).
REPOSITORY_VOLUMES: dict[int, frozenset[int]] = {
    1: frozenset({3, 9, 11, 12, *range(14, 28)}),
    3: frozenset(range(5, 10)),
    7: frozenset(range(3, 9)),
}
SERIES_PAGES: dict[int, tuple[str, str, str]] = {
    # series: (url, who offers it, on what terms)
    4: ("https://leibnizp1.bbaw.de/de/edition", "Leibniz-Edition Potsdam I", "non-commercial use"),
    8: (
        "https://leibnizp2.bbaw.de/de/leibniz-online",
        "Leibniz-Edition Potsdam II",
        "CC BY-NC 4.0",
    ),
    2: (
        "https://www.uni-muenster.de/Leibniz/seite5.html",
        "Leibniz-Forschungsstelle Münster",
        "online after accepting its terms",
    ),
    6: (
        "https://www.uni-muenster.de/Leibniz/seite5.html",
        "Leibniz-Forschungsstelle Münster",
        "online after accepting its terms",
    ),
}
# The Leibniz-Archiv's checked transcriptions of the letters not yet edited.
TRANSCRIPTION_YEARS = range(1708, 1717)


# How the catalogue writes each family's label in its Signatur field.
KATALOG_LABELS = {"LH": "LH", "LBr": "LBr", "Marg": "Leibn. Marg.", "LK": "LK"}
# The library's run-together or lower-cased "LH35", "Lh 35" (a few works).
_LH_LABEL = re.compile(r"^L[Hh](?=\s*\d)")
# A leaf reference and what follows it: the search is for the work.
_LEAF = re.compile(r"\bBl(?:att|\.|\b)", re.IGNORECASE)
# The F series of the correspondence, as the library writes its tail: "F 20".
_F_SERIES = re.compile(r"^F\.?\s*(?=\d)", re.IGNORECASE)


def katalog_spelling(shelfmark: str) -> str | None:
    """A work's shelfmark as the Leibniz-Katalog writes it in its Signatur
    field — the string its ``sign_ol`` search matches as a substring — or
    ``None`` when :mod:`leibniz.catalog.shelfmarks` finds no family in it (a
    foreign signature: the British Library's, a Hanover ``Ms``).

    The family label takes the catalogue's form (``LBr``, ``Leibn. Marg.``),
    a group that is one Roman numeral becomes Arabic (``LH IV, 6, 18`` →
    ``LH 4, 6, 18``; a letter after a number, ``7 C``, is a sub-part and
    stays), the groups are joined with ``, ``, and a leaf reference (``Bl.``),
    a parenthesis or a page (``S.``) and what follows them are dropped, since
    the search is for the work's records on every folio.
    """
    text = _LH_LABEL.sub("LH ", " ".join((shelfmark or "").split()))
    family, tail = split_family(text)
    if family is None:
        return None
    tail = tail.split("(", 1)[0]
    tail = re.split(r"\bS\.\s", tail, maxsplit=1)[0]
    tail = _LEAF.split(tail, maxsplit=1)[0]
    groups = [g for g in (" ".join(g.split()) for g in tail.split(",")) if g]
    if not groups:
        return None
    groups = [str(n) if (n := roman_to_int(g)) is not None else g for g in groups]
    label = KATALOG_LABELS[family]
    if family == "LBr" and _F_SERIES.match(groups[0]):
        label, groups[0] = "LBrF", _F_SERIES.sub("", groups[0])
    elif family == "LK" and groups[0].upper().startswith("MOW"):
        label, groups[0] = "LK-MOW", groups[0][3:].strip()
        if not groups[0]:
            groups = groups[1:]
    return " ".join(part for part in (label, ", ".join(groups)) if part)


def katalog_search_url(shelfmark: str) -> str | None:
    """The Leibniz-Katalog's extended search for every record whose Signatur
    contains the shelfmark, in the catalogue's spelling; ``None`` for a
    shelfmark of no family. Stands in for the records this site does not hold."""
    spelled = katalog_spelling(shelfmark)
    if spelled is None:
        return None
    return f"{KATALOG_SEARCH}?{urlencode({'sign_ol': spelled})}"


def katalog_record_url(record_id: str, katnr: object = None) -> str:
    """The record in the Leibniz-Katalog's extended search; the catalogue number
    makes the substring match on ``id`` unique."""
    params = {"id": str(record_id)}
    if katnr not in (None, ""):
        params["katnr"] = str(katnr).strip()
    return f"{KATALOG_SEARCH}?{urlencode(params)}"


def aa_volume_link(series: object, volume: object) -> dict | None:
    """Where a volume of the Akademie-Ausgabe can be read or found:
    ``{"url", "label", "kind"}`` (``volume`` its own page, ``series`` a page that
    lists it), or ``None`` for a reference that names no volume."""
    try:
        s, v = int(str(series)), int(str(volume))
    except (TypeError, ValueError):
        return None
    roman = ROMAN.get(s)
    if roman is None or v < 1:
        return None
    name = f"AA {roman.upper()},{v}"

    def link(url: str, kind: str, where: str, terms: str = "") -> dict:
        label = (
            f"{name}: the volume in the {where}"
            if kind == "volume"
            else f"{name}: its series at {where}"
        )
        return {
            "url": url,
            "kind": kind,
            "name": name,
            "where": where,
            "terms": terms,
            "label": f"{label} ({terms})" if terms else label,
        }

    if v in REPOSITORY_VOLUMES.get(s, ()):
        return link(
            f"{GWLB_REPOSITORY}/laa-bd-{roman}-{v}",
            "volume",
            "Repositorium des Leibniz-Archivs",
            "CC BY-NC 4.0",
        )
    if s in SERIES_PAGES:
        url, where, terms = SERIES_PAGES[s]
        return link(url, "series", where, terms)
    return link(EDITION_SERIES.format(roman=roman), "series", "leibnizedition.de")


def year_of(date: object) -> int | None:
    """The first four-digit year in a catalogue date ("1709 Jan. 3", "[1712?]")."""
    m = re.search(r"\b(1[67]\d\d)\b", str(date or ""))
    return int(m.group(1)) if m else None


def transcriptions_link(date: object) -> dict | None:
    """For a letter of 1708–1716, the Leibniz-Archiv's checked transcriptions of
    that year (a pre-edition, CC BY-NC 4.0); ``None`` otherwise."""
    year = year_of(date)
    if year is None or year not in TRANSCRIPTION_YEARS:
        return None
    return {
        "url": f"{GWLB_REPOSITORY}/laa-transkriptionen-{year}",
        "label": f"The Leibniz-Archiv's transcriptions of the letters of {year} (pre-edition)",
        "year": year,
    }


__all__ = [
    "REPOSITORY_VOLUMES",
    "TRANSCRIPTION_YEARS",
    "KATALOG_LABELS",
    "aa_volume_link",
    "katalog_record_url",
    "katalog_search_url",
    "katalog_spelling",
    "transcriptions_link",
    "year_of",
]
