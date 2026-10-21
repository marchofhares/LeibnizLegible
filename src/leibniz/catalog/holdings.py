"""Where Leibniz's papers lie: the holding institution of a catalogue record,
read from its shelfmark, and the holdings report (Phase A3b).

The Arbeitskatalog writes a shelfmark as the holding institution's own, with a
place and an institution in front — ``London BL Add.Mss. 4294 Bl. 67-70``,
``Hannover NLA Hann. 93 Nr. 456`` — except for the collections of the
Gottfried Wilhelm Leibniz Bibliothek (the Niedersächsische Landesbibliothek,
``Hannover NLB`` in the catalogue's own words), which it writes bare: ``LH``,
``LBr``, ``LBrF``, ``LK``, ``LK-MOW`` and the library's ``Ms`` manuscripts.
Some records name no manuscript at all: a printed book or journal is the only
witness (``Acta Eruditorum, 1686, S. 161-163``), the piece is in private hands
(``(Privatbesitz) [Ippenburg]``), or its whereabouts are not stated.

:func:`holding_of` reads one shelfmark with a token table built from the
export of 21 October 2026 (70,405 records, 873 distinct prefixes before the
first digit): the place names the catalogue uses, the abbreviations and words
that name an institution, and the connectors inside a name (``Bibl. de la
Sorbonne``). A shelfmark the table does not know is filed by its place alone
(``Wiesentheid``), and a shelfmark with no place in front as a printed witness.
The holdings report counts records by that reading, digitised copies by the
domain of ``URL_Ms``, and the GWLB works with and without records.
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from leibniz import db
from leibniz.catalog import KATALOG_ATTRIBUTION

GWLB = "Hannover NLB"
PRINTED = "(printed witness, no manuscript named)"
PRIVATE = "(private collection)"
UNLOCATED = "(whereabouts not stated)"
NO_SHELFMARK = "(no shelfmark)"

# The collections the catalogue writes without a place: the GWLB's.
_NLB_FAMILIES = frozenset({"LH", "LBr", "LBrF", "Lbr", "LK", "LK-MOW", "Ms", "MS"})

# The places the catalogue puts before an institution (the export's own first
# tokens, read one by one). A place written in two tokens is listed as such.
PLACES: frozenset[str] = frozenset(
    {
        "Altenburg",
        "Amsterdam",
        "Augsburg",
        "Basel",
        "Berlin",
        "Berlin-Charlottenburg",
        "Berlin-Marienfelde",
        "Bologna",
        "Braunschweig",
        "Breslau",
        "Bruxelles",
        "Budapest",
        "Bückeburg",
        "Cambridge",
        "Cambridge/Mass.",
        "Celle",
        "Clausthal",
        "Cologny-Genève",
        "Darmstadt",
        "Dresden",
        "Erfurt",
        "Erlangen",
        "Eybach",
        "Firenze",
        "Forlì",
        "Frankfurt/M.",
        "Freiberg",
        "Gartow",
        "Genève",
        "Gotha",
        "Göttingen",
        "Göttweih",
        "Greifswald",
        "Halle",
        "Hamburg",
        "Hannover",
        "Heiligenkreuz",
        "Honfleur",
        "Jena",
        "Karlsruhe",
        "Kassel",
        "Kemnay",
        "Kiel",
        "Kopenhagen",
        "Leiden",
        "Leipzig",
        "Linköping",
        "London",
        "Lyon",
        "Mantua",
        "Marburg",
        "Mariemont",
        "Meißendorf",
        "Modena",
        "Moskva",
        "München",
        "Münster",
        "Neuchâtel",
        "Nürnberg",
        "Oldenburg",
        "Osnabrück",
        "Oxford",
        "Paris",
        "Parma",
        "Potsdam",
        "Regensburg",
        "Roma",
        "Rouen",
        "Schlitz",
        "Schlobitten",
        "Schwerin",
        "St.Andrews",
        "St.Petersburg",
        "Stockholm",
        "Tartu",
        "Templin",
        "Uppsala",
        "Utrecht",
        "Venezia",
        "Warszawa",
        "Weimar",
        "Wernigerode",
        "Wien",
        "Wiesentheid",
        "Wisentheid",
        "Wolfenbüttel",
        "Wroclaw",
        "Zierow/Meckl.",
        "Zürich",
        "Zwickau",
    }
)
TWO_WORD_PLACES: tuple[str, ...] = ("Den Haag", "New York", "La Courneuve")

# An institution's abbreviation: two capitals in one token (UB, StUB, HAB,
# GStA, BBAW, ÖStA, Bibl.Vallicelliana, Publ.Rec.Office). Taken as the first
# word of an institution, or after an adjective ("Hessisches StA").
_ABBREVIATION = re.compile(r"^(?=(?:[^A-ZÄÖÜ]*[A-ZÄÖÜ]){2})[A-ZÄÖÜ][\w.\-/'’]*$")
# Words that begin an institution's name (matched case-blind at the start).
_INSTITUTION_PREFIXES: tuple[str, ...] = (
    "bibl",
    "biblio",
    "arch",
    "museum",
    "mus.",
    "gymn",
    "univ",
    "académ",
    "academ",
    "society",
    "observatoire",
    "institut",
    "instiut",
    "library",
    "office",
    "publ.rec",
    "stiftung",
    "forschungsstelle",
    "akademie",
    "royal",
    "bodl",
    "trinity",
    "harvard",
    "lambeth",
    "wellcome",
    "ministère",
    "kestner",
    "ratsbibl",
    "zentralbibl",
    "oberbergamt",
    "gemeente",
    "archief",
    "hofbibl",
    "staatsbibl",
    "landesbibl",
    "stadtbibl",
    "nationalbibl",
    "leibniz-forschungsstelle",
)
# ... and that end one ("Hauptstaatsarchiv", "Goertzisches", "Culemannsche").
_INSTITUTION_SUFFIXES: tuple[str, ...] = (
    "archiv",
    "bibl.",
    "bibliothek",
    "museum",
    "akademie",
    "sche",
    "sches",
    "stiftungen",
    "gymn.",
)
# Adjectives and qualifiers inside a name, as the catalogue writes them.
_ADJECTIVES: frozenset[str] = frozenset(
    {
        "gräfl.",
        "graf",
        "kaiserl.",
        "bayerische",
        "bayerisches",
        "hessisches",
        "thür.",
        "historisches",
        "freies",
        "brand.-preuß.",
        "franckesche",
        "stadtgeschichtliches",
        "rossijskaja",
        "het",
        "utrechts",
        "joach.",
        "stifts-",
        "nationale",
        "nazionale",
        "royale",
        "municipales",
        "municipale",
        "estense",
        "palat.",
        "vat.",
        "vatic.",
        "angelica",
        "riccard.",
        "medicea",
        "com.",
        "storico",
        "gén.",
        "étr.",
        "publ.",
        "publique",
        "diplomatiques",
        "lidén",
        "saltykov-ščedrin-bibl.",
        "ráday-bibl.",
        "ambrosiana",
    }
)
# A connector inside a name takes the word after it ("Bibl. de la Sorbonne").
_CONNECTORS: frozenset[str] = frozenset(
    {
        "de",
        "la",
        "le",
        "les",
        "des",
        "du",
        "di",
        "del",
        "of",
        "u.",
        "und",
        "et",
        "&",
        "d.",
        "der",
        "the",
        "och",
        "en",
        "van",
        "pour",
        "l'",
        "l’",
    }
)
_UNLOCATED_FIRST: frozenset[str] = frozenset(
    {
        "?",
        "verbleib",
        "(nicht",
        "(verbleib",
        "(verschollen)",
        "(s.note)",
        "[s.note]",
        "[s.",
        "(in:",
        "(lnachlaß)",
        "(ohne",
    }
)


def _clean(text: str | None) -> str:
    return " ".join((text or "").split())


def _bare(token: str) -> str:
    return token.rstrip(",;:")


def _is_institution_word(token: str, *, first: bool, after_adjective: bool) -> bool:
    bare = _bare(token)
    low = bare.casefold()
    if low in _ADJECTIVES:
        return True
    if low.startswith(_INSTITUTION_PREFIXES) or low.endswith(_INSTITUTION_SUFFIXES):
        return True
    return bool((first or after_adjective) and _ABBREVIATION.match(bare))


def _institution(tokens: list[str]) -> str:
    """The institution's name at the head of ``tokens`` (the shelfmark after its
    place), or ``""`` when no token names one."""
    out: list[str] = []
    i = 0
    after_adjective = False
    while i < len(tokens):
        tok = tokens[i]
        low = _bare(tok).casefold()
        if low in _CONNECTORS and out and i + 1 < len(tokens):
            # "Bibl. de la Sorbonne": the connectors and the name they lead to
            while i + 1 < len(tokens) and _bare(tokens[i]).casefold() in _CONNECTORS:
                out.append(tokens[i])
                i += 1
            out.append(tokens[i])
            i += 1
            after_adjective = False
            continue
        if not _is_institution_word(tok, first=not out, after_adjective=after_adjective):
            break
        out.append(tok)
        after_adjective = low in _ADJECTIVES
        i += 1
        # "Arch.di Stato", "Bibl.de la Ville": a connector glued to the word
        tail = low.rsplit(".", 1)[-1]
        if tail in _CONNECTORS and i < len(tokens):
            while i + 1 < len(tokens) and _bare(tokens[i]).casefold() in _CONNECTORS:
                out.append(tokens[i])
                i += 1
            out.append(tokens[i])
            i += 1
    return _bare(" ".join(out))


def _place(tokens: list[str]) -> tuple[str, list[str]] | None:
    """The place at the head of ``tokens`` and what follows it, or ``None``."""
    if not tokens:
        return None
    if len(tokens) >= 2:
        pair = f"{_bare(tokens[0])} {_bare(tokens[1])}"
        if pair in TWO_WORD_PLACES:
            return pair, tokens[2:]
    head = _bare(tokens[0])
    if head in PLACES:
        return head, tokens[1:]
    return None


def holding_of(signature: str | None) -> str:
    """The holding institution a shelfmark names, as ``Place Institution``
    (``London BL``, ``Hannover NLA``), :data:`GWLB` for the library's own
    collections, the place alone where the table knows no institution after it,
    and one of :data:`PRINTED`, :data:`PRIVATE`, :data:`UNLOCATED` and
    :data:`NO_SHELFMARK` where the shelfmark names no holding."""
    text = _clean(signature)
    if not text:
        return NO_SHELFMARK
    tokens = text.split()
    first = _bare(tokens[0])
    if first.rstrip(".") in _NLB_FAMILIES:
        return GWLB
    if first.startswith(("(Privatbesitz", "Privatbesitz")):
        return PRIVATE
    if first.casefold() in _UNLOCATED_FIRST:
        return UNLOCATED
    if first.startswith(("(", "[")):  # "(Berlin, Henrici Auktion 1920 …)": seen at a sale
        inner = holding_of(text.lstrip("([").rstrip(")]"))
        return inner if " " in inner and not inner.startswith("(") else UNLOCATED
    placed = _place(tokens)
    if placed is None:
        return PRINTED
    place, rest = placed
    if place == "Hannover" and rest and _bare(rest[0]) == "NLB":
        return GWLB
    institution = _institution(rest)
    return f"{place} {institution}" if institution else place


def place_of(holding: str) -> str:
    """The place of a holding (``London BL`` → ``London``); a label in
    parentheses is its own place."""
    if holding.startswith("("):
        return holding
    for pair in TWO_WORD_PLACES:
        if holding.startswith(pair):
            return pair
    return holding.split(" ", 1)[0]


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #

GWLB_HOST = "digitale-sammlungen.gwlb.de"
_GWLB_LINK = re.compile(r"resolve\?(id|PPN)=")


@dataclass(slots=True)
class SetCoverage:
    set_name: str
    works: int
    with_records: int


@dataclass(slots=True)
class HoldingsData:
    """What the holdings report and ``/api/holdings`` say."""

    generated_at: str
    source: str
    records: int
    by_holding: list[tuple[str, int]]
    by_place: list[tuple[str, int]]
    with_url: int
    by_domain: list[tuple[str, int]]
    gwlb_links: dict[str, int]
    refreshed: str | None = None
    works: int | None = None
    works_with_records: int | None = None
    by_set: list[SetCoverage] = field(default_factory=list)

    @property
    def works_without_records(self) -> int | None:
        if self.works is None or self.works_with_records is None:
            return None
        return self.works - self.works_with_records

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "source": self.source,
            "refreshed": self.refreshed,
            "records": self.records,
            "by_holding": [{"holding": h, "records": n} for h, n in self.by_holding],
            "by_place": [{"place": p, "records": n} for p, n in self.by_place],
            "with_url": self.with_url,
            "by_domain": [{"domain": d, "records": n} for d, n in self.by_domain],
            "gwlb_links": dict(self.gwlb_links),
            "works": self.works,
            "works_with_records": self.works_with_records,
            "works_without_records": self.works_without_records,
            "by_set": [
                {"set": s.set_name, "works": s.works, "with_records": s.with_records}
                for s in self.by_set
            ],
            "attribution": KATALOG_ATTRIBUTION,
        }


def record_holding(rec: db.KatalogRecord) -> str:
    """A record's holding: as imported, or read from its shelfmark."""
    holding = rec.metadata.get("holding") if rec.metadata else None
    if holding:
        return str(holding)
    return holding_of(rec.shelfmark_refs[0] if rec.shelfmark_refs else None)


def record_url(rec: db.KatalogRecord) -> str | None:
    """The record's link to a digitised copy (``URL_Ms``), where it has one."""
    url = rec.metadata.get("url_ms") if rec.metadata else None
    return str(url).strip() or None if url else None


def domain_of(url: str) -> str:
    host = urlsplit(url).netloc.casefold() if "://" in url else ""
    return host or "(no host)"


def holdings_from_records(
    records: Iterable[db.KatalogRecord], *, generated_at: str, source: str
) -> HoldingsData:
    """The catalogue side of the report, from the records alone."""
    holdings: Counter[str] = Counter()
    domains: Counter[str] = Counter()
    links: Counter[str] = Counter()
    n = with_url = 0
    for rec in records:
        n += 1
        holdings[record_holding(rec)] += 1
        url = record_url(rec)
        if url:
            with_url += 1
            domains[domain_of(url)] += 1
            m = _GWLB_LINK.search(url)
            if m and GWLB_HOST in url:
                links[m.group(1)] += 1
    places: Counter[str] = Counter()
    for holding, count in holdings.items():
        places[place_of(holding)] += count
    return HoldingsData(
        generated_at=generated_at,
        source=source,
        records=n,
        by_holding=sorted(holdings.items(), key=lambda kv: (-kv[1], kv[0])),
        by_place=sorted(places.items(), key=lambda kv: (-kv[1], kv[0])),
        with_url=with_url,
        by_domain=sorted(domains.items(), key=lambda kv: (-kv[1], kv[0])),
        gwlb_links=dict(links),
    )


def catalog_refreshed(conn: sqlite3.Connection) -> str | None:
    """The export date of the latest finished Arbeitskatalog import, or ``None``
    where the store holds the website's records (the scrape)."""
    import json

    row = conn.execute(
        "SELECT params FROM runs WHERE stage = 'catalog_import_access' "
        "AND finished_at IS NOT NULL ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    if row is None or not row[0]:
        return None
    try:
        return json.loads(row[0]).get("export_date") or None
    except (json.JSONDecodeError, AttributeError):
        return None


def holdings_from_store(conn: sqlite3.Connection, *, generated_at: str) -> HoldingsData:
    """The whole report from the store: the records, and the works beside them."""
    refreshed = catalog_refreshed(conn)
    source = (
        f"the Arbeitskatalog export of {refreshed}, imported into the store"
        if refreshed
        else "the catalogue records the store holds (the website's records)"
    )
    data = holdings_from_records(
        db.iter_katalog_records(conn), generated_at=generated_at, source=source
    )
    data.refreshed = refreshed
    matched = db.matched_work_ids(conn)
    by_set: dict[str, list[int]] = {}
    total = 0
    for work in db.iter_works(conn):
        total += 1
        row = by_set.setdefault(work.set_name or "(no set)", [0, 0])
        row[0] += 1
        row[1] += int(work.gwlb_object_id in matched)
    data.works = total
    data.works_with_records = sum(1 for w in matched if w)
    data.by_set = [SetCoverage(s, w, m) for s, (w, m) in sorted(by_set.items())]
    return data


def _pct(part: int, whole: int) -> str:
    return f"{100.0 * part / whole:.1f} %" if whole else "–"


def render_holdings_md(data: HoldingsData, *, min_records: int = 20) -> str:
    """``reports/holdings.md``: the tables, and how they were read."""
    lines = [
        "# Where Leibniz's papers lie — the Arbeitskatalog by holding institution",
        "",
        f"_Leibniz Legible, Phase A3b. Generated {data.generated_at} from {data.source}. "
        "Records, not pages; a record is one piece (a letter, a draft, a note) in one "
        "witness, so a convolute of many pieces counts many times and a lost or printed "
        "witness counts too._",
        "",
        f"> {KATALOG_ATTRIBUTION}",
        "",
        "## Records by holding institution",
        "",
        f"{data.records:,} records. The holding is read from the shelfmark's prefix "
        "(`leibniz.catalog.holdings.holding_of`): the GWLB's collections (LH, LBr, LBrF, LK, "
        "Ms) are written bare and filed under its own name in the catalogue, "
        f"`{GWLB}`; everything else begins with a place and an institution. "
        f"Holdings with fewer than {min_records} records are summed as *other*.",
        "",
        "| Holding | Records | Share |",
        "| --- | ---: | ---: |",
    ]
    tail_n = tail_count = 0
    for holding, count in data.by_holding:
        if count >= min_records:
            lines.append(f"| {holding} | {count:,} | {_pct(count, data.records)} |")
        else:
            tail_n += 1
            tail_count += count
    if tail_n:
        lines.append(
            f"| *other ({tail_n:,} holdings with fewer than {min_records} records)* | "
            f"{tail_count:,} | {_pct(tail_count, data.records)} |"
        )
    lines += [
        "",
        "### By place",
        "",
        "| Place | Records |",
        "| --- | ---: |",
    ]
    rest = 0
    for place, count in data.by_place:
        if count >= min_records:
            lines.append(f"| {place} | {count:,} |")
        else:
            rest += count
    if rest:
        lines.append(f"| *other places* | {rest:,} |")
    lines += [
        "",
        "## Digitised copies, by the domain of the catalogue's link (`URL_Ms`)",
        "",
        f"{data.with_url:,} of {data.records:,} records link a digitised copy "
        f"({_pct(data.with_url, data.records)}). The GWLB's links resolve to its digital "
        f"collections by object id (`resolve?id=`: {data.gwlb_links.get('id', 0):,}) or by "
        f"PPN (`resolve?PPN=`: {data.gwlb_links.get('PPN', 0):,}); both are this site's work "
        "ids. The other domains are other libraries' and archives' viewers and finding aids, "
        "not necessarily page images.",
        "",
        "| Domain | Records |",
        "| --- | ---: |",
    ]
    rest = 0
    for domain, count in data.by_domain:
        if count >= min_records:
            lines.append(f"| {domain} | {count:,} |")
        else:
            rest += count
    if rest:
        lines.append(f"| *other domains* | {rest:,} |")
    lines += ["", "## The GWLB's digitised works with and without catalogue records", ""]
    if data.works is None:
        lines.append(
            "_Not available from the export alone: the works table is the store's. "
            "`leibniz catalog holdings --db …` after the import renders this section._"
        )
    else:
        lines += [
            f"{data.works_with_records:,} of {data.works:,} works carry at least one record "
            f"through the crosswalk ({_pct(data.works_with_records or 0, data.works)}); "
            f"{data.works_without_records:,} carry none.",
            "",
            "| Set | Works | With records | Without |",
            "| --- | ---: | ---: | ---: |",
        ]
        for s in data.by_set:
            lines.append(
                f"| {s.set_name} | {s.works:,} | {s.with_records:,} | "
                f"{s.works - s.with_records:,} |"
            )
    lines += [
        "",
        "## Method",
        "",
        "- A record's holding is its shelfmark's prefix read against a token table built from "
        "the export (the place names the catalogue uses, the abbreviations and words that name "
        "an institution, the connectors inside a name); a prefix the table does not know is "
        f"filed by its place alone, and a shelfmark with no place in front as `{PRINTED}`.",
        f"- `{PRIVATE}`: the catalogue writes *Privatbesitz*; `{UNLOCATED}`: a whereabouts in "
        "parentheses, a question mark or *Verbleib unbekannt*; "
        f"`{NO_SHELFMARK}`: an empty shelfmark.",
        "- Digitised copies are the catalogue's `URL_Ms` links counted by host; whether a link "
        "opens page images, a finding aid or a catalogue record differs by host and is not "
        "checked here.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "GWLB",
    "NO_SHELFMARK",
    "PLACES",
    "PRINTED",
    "PRIVATE",
    "UNLOCATED",
    "HoldingsData",
    "SetCoverage",
    "catalog_refreshed",
    "domain_of",
    "holding_of",
    "holdings_from_records",
    "holdings_from_store",
    "place_of",
    "record_holding",
    "record_url",
    "render_holdings_md",
]
