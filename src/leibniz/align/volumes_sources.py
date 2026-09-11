"""Where each §70-expired volume's reading text can be read from (Phase C2).

Verified live on 2026-09-11 against archive.org, leibnizedition.de, the GWLB
*Repositorium des Leibniz-Archivs*, the Potsdam Arbeitsstelle and the Münster
Forschungsstelle. Three kinds of source exist, and — because the *text* is §70-
free while the *channel* may carry its own terms — each entry records both what
it is and what the channel asks (SPECS §7.3, §7.7: relationship > rights):

* ``ia`` — a public-domain library scan on the Internet Archive (Trent
  University copies, no access restriction, Tesseract hOCR shipped): the
  unencumbered channel, preferred wherever it exists.
* ``gwlb`` — the Leibniz-Archiv's own PDF (ABBYY text layer) in the GWLB
  repositorium, published under **CC BY-NC 4.0**. The NC clause has nothing to
  attach to in §70-expired reading text, but the channel is a partner's; it is
  used here only where no IA scan exists and is flagged for the lawyer memo.
* ``potsdam`` — the Potsdam Arbeitsstelle's born-digital text PDFs of Reihe IV
  (clean text layer, no OCR); no terms stated on the page.
* ``muenster`` — the Münster Forschungsstelle's Internetausgaben (Reihe II, VI):
  the download page requires accepting that they "may not be used … without
  express written permission" of the Göttingen Academy — an **operator ask**,
  never auto-fetched.

Volumes with no free digital source at all are listed with ``kind="none"`` so
the report can say so; HathiTrust holds the 1923–1927 volumes as US-public-
domain (view restricted to US IPs) — another operator path.
"""

from __future__ import annotations

from dataclasses import dataclass

IA_DOWNLOAD = "https://archive.org/download"
GWLB_REPO = "https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs"
POTSDAM = "https://leibniz-potsdam.bbaw.de/fileadmin/Webdateien/bilder"

CHANNEL_TERMS: dict[str, str] = {
    "ia": "public-domain scan, no access restriction",
    "gwlb": "CC BY-NC 4.0 channel (text §70-free; flag for the lawyer memo)",
    "potsdam": "no terms stated (edition's own site)",
    "muenster": "written permission required (operator ask; not auto-fetched)",
    "none": "no free digital source found",
}


@dataclass(frozen=True, slots=True)
class EditionSource:
    """One digital source of one volume's print."""

    series: int
    volume: int
    kind: str  # ia | gwlb | potsdam | muenster | none
    ident: str = ""  # IA identifier / file name
    pages: int | None = None  # leaves (IA imagecount) or PDF pages
    part: str | None = None  # multi-part volumes (VI,4 A–D)
    note: str = ""

    @property
    def text_layer(self) -> str:
        """``hocr`` (IA) / ``pdf`` (text layer) / ``""`` (nothing to read)."""
        return {"ia": "hocr", "gwlb": "pdf", "potsdam": "pdf", "muenster": "pdf"}.get(self.kind, "")

    @property
    def url(self) -> str | None:
        if self.kind == "ia":
            return f"{IA_DOWNLOAD}/{self.ident}/{self.ident}_hocr.html"
        if self.kind == "gwlb":
            return f"{GWLB_REPO}/{self.ident}"
        if self.kind == "potsdam":
            return f"{POTSDAM}/{self.ident}"
        return None

    @property
    def local_name(self) -> str:
        if self.kind == "ia":
            return f"{self.ident}_hocr.html"
        return self.ident

    @property
    def terms(self) -> str:
        return CHANNEL_TERMS.get(self.kind, "")


def _ia(series: int, volume: int, ident: str, pages: int, part: str | None = None) -> EditionSource:
    return EditionSource(series, volume, "ia", ident, pages, part)


def _gwlb(series: int, volume: int, ident: str, pages: int | None = None) -> EditionSource:
    return EditionSource(series, volume, "gwlb", ident, pages)


# Preference-ordered sources per §70-expired volume (SPECS §1.4 list, as of 2026).
EDITION_SOURCES: dict[tuple[int, int], tuple[EditionSource, ...]] = {
    # Reihe I — Allgemeiner politischer und historischer Briefwechsel
    (1, 1): (EditionSource(1, 1, "none", note="1923; HathiTrust (US-PD) / TELOTA ask"),),
    (1, 2): (EditionSource(1, 2, "none", note="1927; HathiTrust (US-PD) / TELOTA ask"),),
    (1, 3): (_gwlb(1, 3, "LAA-BdI3.pdf"),),
    (1, 4): (EditionSource(1, 4, "none", note="1950; no free digital copy found"),),
    (1, 5): (EditionSource(1, 5, "none", note="1954; no free digital copy found"),),
    (1, 6): (_ia(1, 6, "samtlicheschrift0006leib_c2b3", 758),),
    (1, 7): (_ia(1, 7, "samtlicheschrift0007leib", 842),),
    (1, 8): (_ia(1, 8, "samtlicheschrift0008leib", 772),),
    (1, 9): (_ia(1, 9, "samtlicheschrift0009leib", 904), _gwlb(1, 9, "LAA-BdI9.pdf")),
    (1, 10): (_ia(1, 10, "samtlicheschrift0010leib", 894),),
    (1, 11): (_ia(1, 11, "samtlicheschrift0011leib", 974), _gwlb(1, 11, "LAA-BdI11.pdf", 965)),
    (1, 12): (_ia(1, 12, "samtlicheschrift0012leib", 954), _gwlb(1, 12, "LAA-BdI12.pdf")),
    (1, 13): (EditionSource(1, 13, "none", note="1987; not online at GWLB, not on IA"),),
    (1, 14): (_gwlb(1, 14, "LAA-BdI14.pdf"),),
    (1, 15): (_gwlb(1, 15, "LAA-BdI15.pdf"),),
    (1, 16): (_ia(1, 16, "samtlicheschrift0000leib_a6a0", 954), _gwlb(1, 16, "LAA-BdI16.pdf")),
    # Reihe II — Philosophischer Briefwechsel (the 1926 print; Münster's online
    # II,1 is the protected 2006 Neubearbeitung — never use it)
    (2, 1): (EditionSource(2, 1, "none", note="1926 print; HathiTrust (US-PD) / TELOTA ask"),),
    # Reihe III — Mathematischer, naturwissenschaftlicher und technischer Briefwechsel
    (3, 1): (_ia(3, 1, "samtlicheschrift0001leib_n3h6", 956),),
    (3, 2): (EditionSource(3, 2, "none", note="1987; no free digital copy found"),),
    (3, 3): (_ia(3, 3, "samtlicheschrift0003leib_i1c0", 966),),
    (3, 4): (_ia(3, 4, "samtlicheschrift0004leib", 826),),
    # Reihe IV — Politische Schriften (Potsdam born-digital text PDFs)
    (4, 1): (
        EditionSource(4, 1, "potsdam", "IV1text.pdf", 717),
        _ia(4, 1, "samtlicheschrift0001leib_l9t2", 834),
    ),
    (4, 2): (EditionSource(4, 2, "potsdam", "IV2text.pdf"),),
    (4, 3): (EditionSource(4, 3, "potsdam", "IV3text.pdf"),),
    # Reihe VI — Philosophische Schriften
    (6, 1): (_ia(6, 1, "samtlicheschrift0001leib", 616),),
    (6, 2): (EditionSource(6, 2, "none", note="1966; no free digital copy found"),),
    (6, 3): (_ia(6, 3, "samtlicheschrift0003leib", 794),),
    (6, 4): (
        _ia(6, 4, "samtlicheschrift0004leib_a8x0", 1106, part="A"),
        _ia(6, 4, "samtlicheschrift0000leib_e8w3", 510, part="B?"),
        _ia(6, 4, "samtlicheschrift0000leib_x5q7", 1026, part="C"),
        EditionSource(6, 4, "muenster", part="A–D", note="Internetausgabe; permission ask"),
    ),
    (6, 6): (_ia(6, 6, "samtlicheschrift0006leib", 652),),
    # Reihe VII — Mathematische Schriften
    (7, 1): (EditionSource(7, 1, "none", note="1990; not online at GWLB, not on IA"),),
    (7, 2): (EditionSource(7, 2, "none", note="1996; not online at GWLB, not on IA"),),
}


def sources_for(series: int, volume: int) -> tuple[EditionSource, ...]:
    """Preference-ordered sources for a volume (empty if unregistered)."""
    return EDITION_SOURCES.get((series, volume), ())


def readable_sources(series: int, volume: int) -> list[EditionSource]:
    """Sources with a fetchable text layer (IA hOCR, GWLB/Potsdam PDF)."""
    return [s for s in sources_for(series, volume) if s.url and s.text_layer]


def source_kind(series: int, volume: int) -> str:
    """The best available channel kind for a volume (``"none"`` if unreadable)."""
    rs = readable_sources(series, volume)
    return rs[0].kind if rs else "none"


__all__ = [
    "CHANNEL_TERMS",
    "EDITION_SOURCES",
    "EditionSource",
    "readable_sources",
    "source_kind",
    "sources_for",
]
