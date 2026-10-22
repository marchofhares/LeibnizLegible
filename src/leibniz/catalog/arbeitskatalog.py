"""The Arbeitskatalog from the Arbeitsstelle's Access export (Phase A3b).

The Leibniz-Edition Potsdam provided the Arbeitskatalog's Access database on
21 October 2026 under CC BY 4.0 (``legal.py``, entry ``arbeitskatalog``),
exported with mdbtools as CSV files under ``data/external/arbeitskatalog/csv/``
(gitignored; a fixture of at most thirty rows per table under
``tests/fixtures/arbeitskatalog/``). ``ritter.csv`` is the catalogue, one row
per record, its ``ID`` the record id the website uses in its addresses; the
side tables add the edition's PDF per piece (``pdf_url``), the
Ordnungsvermerke of the historical excerpts (``OV_mit_Infos``,
``OV_mit_Inhalt``, ``Faszikel_Ms_mit_Infos``), persons and places.

This module maps one row to the :class:`~leibniz.db.KatalogRecord` the
website parser (:mod:`leibniz.catalog.scrape`) produced from the same record,
so every reader of ``katalog_records`` keeps working unchanged, and adds what
the export has and the website has not. **Which column feeds which key was
read off the website, not guessed**: on 21 October 2026, 23 records were
fetched from the catalogue's extended search (``id=`` and ``katnr=``) with the
project's polite client and parsed with the website parser, and their cells
compared with the export's columns. The rules, as the website renders them:

* ``Kat.-Nr.`` = ``KA KAT_NR/Zusatz`` (``Cc2 1505/C``, ``K 22257``, ``57273``);
  no ``KAT_NR``, no number.
* ``Signatur`` = ``SIGN`` with its runs of spaces folded (``LBr  629 Bl.  80``
  → ``LBr 629 Bl. 80``); ``SIGN_oL`` is the field the ``sign_ol`` search
  matches and differs in 920 rows; it stands in where ``SIGN`` is empty (18).
* ``Datum`` = ``JJJJMMTT`` as ``YYYY``, ``YYYY-MM`` or ``YYYY-MM-DD``, a
  ``00`` month or day dropped (``16770500`` → ``1677-05``, ``17070000`` →
  ``1707``, ``16930006`` → ``1693``), anything but eight digits verbatim
  (``169760113``); ``JJMMTT``, the date in the other calendar, follows in
  parentheses as ``(99-11-28)`` (zero-filled to six digits: Access dropped the
  leading zero of ``51116``; a ``00`` month or day dropped as in the first
  date, ``(93-06)``: the operator's dry run of 2026-10-22 found 397 records
  so).
* ``Akademie Ausgabe`` = ``REIHE | bd.nnn / UNr Aufl. Aufl(Jahr)`` with the
  piece number zero-filled to three digits (``8 | 3.044``, ``2 | 1.130 / a
  Teildr. Aufl. 2 (1988)``); a series without a piece shows the series alone
  (``4``). :func:`~leibniz.catalog.scrape.parse_aa_refs` reads that cell and
  ``BEZUG`` exactly as it read the website's, so the ``aa_refs`` agree; a
  series alone becomes a reference without a volume (the API's
  ``aa_planned``: assigned to the series, not yet published).
* ``Sigle`` = ``TZ``; ``Absendeort`` = ``ORT``; ``Textart`` = ``UEBERLFG``;
  ``Titel``, ``Incipit``, ``Drucke``, ``Bemerkungen``, ``Bezüge`` the columns
  of those names with line breaks folded to spaces.
* ``Absender``/``Adressat``: the export carries the catalogue's own strings,
  several names apart by ``|``; the website shows each name with its link
  texts, ``(KorrespDB)`` where the persons table (``pers_norm.csv``: ``korr``
  → ``pers_name``, ``gnd``, ``idhannover``) has a Leibniz-Connection id and
  ``(GND)`` where it has a GND, the names run together. Joined through that
  table the export reproduces the website's cells (46 of 46 on the live
  records), so the record carries the website's form, which every reader
  strips (``catalog/hands.py``, ``web/browse.py``), and the identifiers beside
  it as ``absender_gnd``, ``absender_korrespdb``, ``adressat_gnd``,
  ``adressat_korrespdb``. Without the persons table the bare strings stay.
* ``Format und Umfang`` = the format's name (``2`` Folio, ``4`` Quart, ``8``
  Oktav, ``12`` Duodez, ``16`` Sedez, ``24`` Vigesimoquart; the website prints
  a bare ``°`` for ``32``, this module ``32°``) and ``UMFANG`` rounded to two
  decimals (``6.1999998`` → ``6.2``) with ``Seite/Spalte`` for one and
  ``Seiten/Spalten`` otherwise; ``0`` is nothing.
* ``Wortlaut`` is the transcription without its markup: the ``&xs+NNNNN&x{``
  anchors removed, apparatus notes (``<app2a>…</app2a>``, ``<app2c>``, …)
  dropped with their content, other tags (``<i>``, ``<s>``, ``<sc>``,
  ``<persName>``, ``<p>``) stripped, ``_`` a space, ``^<`` ``^>`` angle
  brackets kept (``(apud ^<_-_^>)`` → ``(apud < - >)``).
* The GWLB link is ``URL_Ms`` where it resolves to the digital collections,
  by object id (``resolve?id=``, the website parser's
  :data:`~leibniz.catalog.scrape.GWLB_RESOLVE_RE`) or by PPN
  (``resolve?PPN=1665058609``, 416 rows: the Marginalien, whose work ids are
  PPNs).

New keys: ``holding`` (:func:`leibniz.catalog.holdings.holding_of`),
``url_ms``, ``ordnungsvermerk`` (as written on the slip),
``ordnungsvermerk_norm`` and, from the OV tables, ``ordnungsvermerk_title``
(its *Thema*), ``_komplex``, ``_epoche``; ``ordnungsnummer``;
``identisch_mit`` (another record of the same text, where it is not the record
itself); ``last_change`` (``Letzte_Aenderg``); ``aa_pdf`` (the edition's PDF
for the piece, with the printed page, from ``pdf_url``: the web layer decides
by the registry whether the host is public).

The website's parser lost what it read as HTML tags — ``<Trig>onometria``,
``<bey dem> Bergambt``, ``<prs. …>`` in a Textart, the format code before a
``°`` — so a store value that equals the export's with every ``<…>`` segment
removed counts as agreement ("website lost markup"); the export's value is
kept. The two copies have also been edited apart since the website's last
feed (a printing's wording, a date or a piece number the website's copy
lacks), and the Access master renumbers or merges a few records between
TELOTA's half-yearly imports: a store record whose id the export no longer
carries is mapped to the export's record with the same Kat.-Nr. and
shelfmark (else the same Kat.-Nr. where unique, else the record whose
``Identisch_mit`` or ``mergenr`` names it). The dry run of ``leibniz catalog
import-access`` reports all of that, with examples.
"""

from __future__ import annotations

import csv
import html
import json
import re
import sqlite3
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from leibniz import db
from leibniz.catalog import crosswalk as crosswalk_mod
from leibniz.catalog.hands import hand_from_textart, is_leibniz_hand
from leibniz.catalog.holdings import GWLB_HOST, domain_of, holding_of
from leibniz.catalog.scrape import GWLB_RESOLVE_RE, parse_aa_refs

RITTER = "ritter.csv"
PDF_URL = "pdf_url.csv"
PERS_NORM = "pers_norm.csv"
OV_INFOS = "OV_mit_Infos.csv"
OV_INHALT = "OV_mit_Inhalt.csv"
FASZIKEL = "Faszikel_Ms_mit_Infos.csv"
# Every table of the export, for the row counts the pre-flight records.
TABLES: tuple[str, ...] = (
    RITTER,
    PDF_URL,
    OV_INFOS,
    OV_INHALT,
    FASZIKEL,
    "Drucke.csv",
    "Handschriften.csv",
    "HAB.csv",
    "Orte.csv",
    "Orte_Hannover.csv",
    PERS_NORM,
    "personen_xlsx.csv",
    "Jahre.csv",
    "Ordnr.csv",
    "RegNr.csv",
    "Tabelle1.csv",
    "export.csv",
    "Bogen.csv",
    "Wasserzeichen.csv",
)

# The format codes and the names the website gives them (checked live).
FORMATS: dict[str, str] = {
    "2": "Folio",
    "4": "Quart",
    "8": "Oktav",
    "12": "Duodez",
    "16": "Sedez",
    "24": "Vigesimoquart",
}
# The series of the Akademie-Ausgabe; "0" and "9" in REIHE are not series.
AA_SERIES = frozenset("12345678")

# A GWLB link by PPN (the Marginalien): the PPN is the work id too.
GWLB_PPN_RE = re.compile(r"digitale-sammlungen\.gwlb\.de/resolve\?PPN=([A-Za-z0-9][\w\-]*)")

# The website's link texts after a name.
MARKERS_RE = re.compile(r"\s*\((?:KorrespDB|GND)\)")
# What the website's parser read as an HTML tag and lost.
MARKUP_RE = re.compile(r"<[^<>]*>")
# Several names in one cell of the export.
NAME_SEP_RE = re.compile(r"\s*\|\s*|\r?\n")

_XS_ANCHOR = re.compile(r"&xs[+-]?\d+&x\{")
_APPARATUS = re.compile(r"<(app\w*)\b[^<>]*>.*?</\1\s*>", re.DOTALL | re.IGNORECASE)
_TAG = re.compile(r"</?[A-Za-z][^<>]*>")
_LT, _GT = "\x00", "\x01"  # the transcription's own angle brackets, kept


def clean(text: object) -> str:
    """Whitespace folded, as the website parser folded a cell."""
    return " ".join(str(text or "").split())


# --------------------------------------------------------------------------- #
# Reading the export
# --------------------------------------------------------------------------- #


def read_table(path: Path | str) -> list[dict[str, str]]:
    """One CSV of the export as rows (multi-line text fields are quoted; the
    field size limit is raised for the long memo fields)."""
    csv.field_size_limit(sys.maxsize)
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@dataclass(slots=True)
class Export:
    """The export's tables, read once."""

    csv_dir: Path
    ritter: list[dict[str, str]]
    pdf_url: list[dict[str, str]] = field(default_factory=list)
    pers_norm: list[dict[str, str]] = field(default_factory=list)
    ov_infos: list[dict[str, str]] = field(default_factory=list)
    ov_inhalt: list[dict[str, str]] = field(default_factory=list)
    faszikel: list[dict[str, str]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def ids(self) -> set[str]:
        return {row["ID"].strip() for row in self.ritter if row.get("ID", "").strip()}


def read_export(csv_dir: Path | str) -> Export:
    """Read the export directory; ``ritter.csv`` is required, the rest optional."""
    csv_dir = Path(csv_dir)
    ritter_path = csv_dir / RITTER
    if not ritter_path.exists():
        raise FileNotFoundError(f"{ritter_path} not found: unpack the export there")
    export = Export(csv_dir=csv_dir, ritter=read_table(ritter_path))
    export.counts[RITTER] = len(export.ritter)
    for name, attr in (
        (PDF_URL, "pdf_url"),
        (PERS_NORM, "pers_norm"),
        (OV_INFOS, "ov_infos"),
        (OV_INHALT, "ov_inhalt"),
        (FASZIKEL, "faszikel"),
    ):
        path = csv_dir / name
        if path.exists():
            rows = read_table(path)
            setattr(export, attr, rows)
            export.counts[name] = len(rows)
    for name in TABLES:
        path = csv_dir / name
        if name not in export.counts and path.exists():
            export.counts[name] = len(read_table(path))
    return export


# --------------------------------------------------------------------------- #
# The cells, as the website renders them
# --------------------------------------------------------------------------- #


def katnr_cell(ka: str, kat_nr: str, zusatz: str) -> str:
    """``Kat.-Nr.``: ``KA KAT_NR/Zusatz``; nothing without a ``KAT_NR``."""
    number = clean(kat_nr)
    if not number:
        return ""
    out = " ".join(x for x in (clean(ka), number) if x)
    tail = clean(zusatz)
    return f"{out}/{tail}" if tail else out


def date_cell(jjjjmmtt: str, jjmmtt: str = "") -> str:
    """``Datum``: the digits as ``YYYY[-MM[-DD]]``, the other calendar's date
    in parentheses."""
    digits = clean(jjjjmmtt)
    if re.fullmatch(r"\d{8}", digits):
        year, month, day = digits[:4], digits[4:6], digits[6:8]
        out = year
        if month != "00":
            out += f"-{month}"
            if day != "00":
                out += f"-{day}"
    else:
        out = digits
    other = clean(jjmmtt)
    if other and out:
        if other.isdigit() and len(other) <= 6:
            other = other.zfill(6)
            year, month, day = other[:2], other[2:4], other[4:]
            other = year
            if month != "00":
                other += f"-{month}"
                if day != "00":
                    other += f"-{day}"
        out += f" ({other})"
    return out


def format_name(code: str) -> str:
    """The bibliographic format of a ``FORMAT`` code; ``""`` for none or ``0``."""
    code = clean(code)
    if not code or code == "0":
        return ""
    return FORMATS.get(code, f"{code}°")


def extent(umfang: str) -> str:
    """``UMFANG`` as the website prints it: ``6.2 Seiten/Spalten``, ``1 Seite/Spalte``."""
    text = clean(umfang)
    if not text:
        return ""
    try:
        value = round(float(text), 2)
    except ValueError:
        return text
    if value == 0:
        return ""
    number = f"{value:.2f}".rstrip("0").rstrip(".")
    unit = "Seite/Spalte" if number == "1" else "Seiten/Spalten"
    return f"{number} {unit}"


def umfang_cell(format_code: str, umfang: str) -> str:
    """``Format und Umfang``: the format's name and the extent, comma-joined."""
    return ", ".join(x for x in (format_name(format_code), extent(umfang)) if x)


def aa_cell(reihe: str, bd: str, nr: str, unr: str = "", aufl: str = "") -> str:
    """``Akademie Ausgabe``: ``REIHE | bd.nnn / UNr Aufl. …``, or the series alone."""
    series = clean(reihe)
    if not series:
        return ""
    out = series
    volume, number = clean(bd), clean(nr)
    if volume and number:
        out += f" | {volume}.{int(number):03d}" if number.isdigit() else f" | {volume}.{number}"
    tail = clean(unr)
    if tail:
        out += f" / {tail}"
    edition = clean(aufl)
    if edition:
        out += f" Aufl. {edition}"
    return out


def aa_refs_for(reihe: str, bd: str, nr: str, unr: str, aufl: str, bezug: str) -> list[dict]:
    """The record's Akademie-Ausgabe references: the website parser's reading
    of the cell and of ``BEZUG``, and the series alone where the cell names
    no piece (``volume`` and ``piece`` ``None``)."""
    refs = parse_aa_refs(aa_cell(reihe, bd, nr, unr, aufl), clean(bezug))
    series = clean(reihe)
    if series in AA_SERIES and not any(
        r.get("source") == "aa_column" and r.get("volume") is not None for r in refs
    ):
        refs.append({"series": int(series), "volume": None, "piece": None, "source": "aa_column"})
    return refs


PersonIndex = dict[str, dict[str, str]]


def build_person_index(rows: Iterable[Mapping[str, str]]) -> PersonIndex:
    """``korr`` (the catalogue's short name) → ``{"name", "gnd", "korrespdb"}``
    from ``pers_norm.csv``; the first row of a repeated name wins."""
    index: PersonIndex = {}
    for row in rows:
        korr = clean(row.get("korr"))
        if korr and korr not in index:
            index[korr] = {
                "name": clean(row.get("pers_name")),
                "gnd": clean(row.get("gnd")),
                "korrespdb": clean(row.get("idhannover")),
            }
    return index


def names_as_website(cell: str, index: PersonIndex | None) -> tuple[str, list[str], list[str]]:
    """A sender or addressee cell as the website shows it, and the identifiers
    behind it: each name with ``(KorrespDB)`` where the persons table has a
    Leibniz-Connection id and ``(GND)`` where it has a GND, the names run
    together as the website's cell reads; the GNDs and the KorrespDB ids in
    the names' order (one entry per name that has one). Without the table
    the names are the export's, ``|`` and all."""
    text = cell or ""
    if not text.strip():
        return "", [], []
    if index is None:
        return clean(text), [], []
    parts: list[str] = []
    gnds: list[str] = []
    ids: list[str] = []
    for raw in NAME_SEP_RE.split(text):
        name = clean(raw)
        if not name:
            continue
        person = index.get(name, {})
        shown = name
        if person.get("korrespdb"):
            shown += " (KorrespDB)"
            ids.append(person["korrespdb"])
        if person.get("gnd"):
            shown += " (GND)"
            gnds.append(person["gnd"])
        parts.append(shown)
    return "".join(parts), gnds, ids


def wortlaut_text(raw: str) -> str | None:
    """The transcription as the website shows it, its markup removed."""
    text = raw or ""
    if not text.strip():
        return None
    text = _XS_ANCHOR.sub("", text)
    text = _APPARATUS.sub("", text)
    text = text.replace("^<", _LT).replace("^>", _GT)
    text = _TAG.sub("", text)
    text = text.replace(_LT, "<").replace(_GT, ">").replace("_", " ")
    return clean(html.unescape(text)) or None


def gwlb_ids_of(url: str) -> list[str]:
    """The work ids a ``URL_Ms`` names: by object id, else by PPN."""
    text = url or ""
    return list(dict.fromkeys(GWLB_RESOLVE_RE.findall(text) or GWLB_PPN_RE.findall(text)))


def is_gwlb_url(url: str | None) -> bool:
    return bool(url) and GWLB_HOST in urlsplit(url).netloc.casefold()


# --------------------------------------------------------------------------- #
# The side tables
# --------------------------------------------------------------------------- #

PdfIndex = dict[tuple[str, str, str], list[dict[str, str]]]


def build_pdf_index(rows: Iterable[Mapping[str, str]]) -> PdfIndex:
    """``(reihe, bd, nr)`` → the ``pdf_url`` rows of that piece."""
    index: PdfIndex = {}
    for row in rows:
        key = (clean(row.get("reihe")), clean(row.get("bd")), clean(row.get("nr")))
        if all(key):
            index.setdefault(key, []).append(dict(row))
    return index


def _page_number(text: str) -> int | None:
    text = clean(text)
    return int(text) if text.isdigit() else None


def edition_pdf(row: Mapping[str, str], index: PdfIndex | None) -> dict | None:
    """The edition's PDF for the record's piece: ``{"url", "page", "host"}``.

    Among the piece's rows the one whose ``UNr`` the record's ``UNr`` begins
    with wins (``a`` for ``a Teildr.``), else the row without one, else the
    first; the first printed page where several rows name pages."""
    if not index:
        return None
    key = (clean(row.get("REIHE")), clean(row.get("bd")), clean(row.get("nr")))
    candidates = index.get(key) if all(key) else None
    if not candidates:
        return None
    unr = clean(row.get("UNr")).split(" ")[0] if clean(row.get("UNr")) else ""
    exact = [c for c in candidates if clean(c.get("UNr")) and unr and unr == clean(c.get("UNr"))]
    plain = [c for c in candidates if not clean(c.get("UNr"))]
    pool = exact or plain or candidates
    pool = sorted(
        pool,
        key=lambda c: (
            _page_number(c.get("Seite", "")) is None,
            _page_number(c.get("Seite", "")) or 0,
        ),
    )
    chosen = pool[0]
    url = clean(chosen.get("URL"))
    if not url:
        return None
    return {"url": url, "page": _page_number(chosen.get("Seite", "")), "host": domain_of(url)}


OvIndex = dict[str, dict[str, str]]


def build_ov_index(
    infos: Iterable[Mapping[str, str]], inhalt: Iterable[Mapping[str, str]]
) -> OvIndex:
    """``OV_normiert`` → what the two OV tables say of it (``komplex``,
    ``faszikel``, ``epoche``, ``jahr``, ``thema``, ``feller_ov``)."""
    index: OvIndex = {}
    for row in infos:
        name = clean(row.get("OV_normiert"))
        if name:
            entry = index.setdefault(name, {})
            for src, dst in (("OV_Komplex", "komplex"), ("Faszikel", "faszikel")):
                if clean(row.get(src)):
                    entry[dst] = clean(row.get(src))
    for row in inhalt:
        name = clean(row.get("OV_normiert"))
        if name:
            entry = index.setdefault(name, {})
            for src, dst in (
                ("Epoche", "epoche"),
                ("Jahr", "jahr"),
                ("Thema", "thema"),
                ("Feller_OV", "feller_ov"),
            ):
                if clean(row.get(src)):
                    entry[dst] = clean(row.get(src))
    return index


# --------------------------------------------------------------------------- #
# One row → one record
# --------------------------------------------------------------------------- #


def record_from_row(
    row: Mapping[str, str],
    *,
    pdf_index: PdfIndex | None = None,
    ov_index: OvIndex | None = None,
    person_index: PersonIndex | None = None,
) -> db.KatalogRecord:
    """Map one ``ritter`` row to the record the website parser would produce,
    plus the export's own keys (the module docstring has the rules)."""

    def cell(name: str) -> str:
        return clean(row.get(name))

    record_id = cell("ID")
    signatur = cell("SIGN") or cell("SIGN_oL")
    url_ms = (row.get("URL_Ms") or "").strip()
    gwlb_ids = gwlb_ids_of(url_ms)
    aa_refs = aa_refs_for(
        row.get("REIHE", ""),
        row.get("bd", ""),
        row.get("nr", ""),
        row.get("UNr", ""),
        row.get("Aufl(Jahr)", ""),
        row.get("BEZUG", ""),
    )
    identisch = cell("Identisch_mit")
    absender, absender_gnd, absender_ids = names_as_website(row.get("ABSENDER", ""), person_index)
    adressat, adressat_gnd, adressat_ids = names_as_website(row.get("ADRESSAT", ""), person_index)
    ov_norm = cell("Ordnungsvermerk_normiert")
    ov_info = (ov_index or {}).get(ov_norm, {}) if ov_norm else {}

    metadata: dict[str, object] = {
        "katnr": katnr_cell(row.get("KA", ""), row.get("KAT_NR", ""), row.get("Zusatz", "")),
        "signatur": signatur,
        "titel": cell("TITEL"),
        "incipit": cell("INCIPIT"),
        "datum": date_cell(row.get("JJJJMMTT", ""), row.get("JJMMTT", "")),
        "aa": aa_cell(
            row.get("REIHE", ""),
            row.get("bd", ""),
            row.get("nr", ""),
            row.get("UNr", ""),
            row.get("Aufl(Jahr)", ""),
        ),
        "sigle": cell("TZ"),
        "absender": absender,
        "adressat": adressat,
        "ort": cell("ORT"),
        "textart": cell("UEBERLFG"),
        "umfang": umfang_cell(row.get("FORMAT", ""), row.get("UMFANG", "")),
        "drucke": cell("DRUCKE"),
        "bemerkungen": cell("BEMERKGN"),
        "bezuege": cell("BEZUG"),
        "gwlb_ids": gwlb_ids,
        # the export's own
        "holding": holding_of(signatur),
        "url_ms": url_ms,
        "ordnungsvermerk": cell("Ordnungsvermerk"),
        "ordnungsvermerk_norm": ov_norm,
        "ordnungsvermerk_title": ov_info.get("thema", ""),
        "ordnungsvermerk_komplex": ov_info.get("komplex", ""),
        "ordnungsvermerk_epoche": ov_info.get("epoche", ""),
        "ordnungsnummer": cell("Ordnungsnummer"),
        "identisch_mit": identisch if identisch and identisch != record_id else "",
        "last_change": cell("Letzte_Aenderg"),
        "aa_pdf": edition_pdf(row, pdf_index),
        "absender_gnd": absender_gnd,
        "absender_korrespdb": absender_ids,
        "adressat_gnd": adressat_gnd,
        "adressat_korrespdb": adressat_ids,
    }
    return db.KatalogRecord(
        record_id=record_id,
        metadata={k: v for k, v in metadata.items() if v},
        shelfmark_refs=[signatur] if signatur else [],
        aa_refs=aa_refs,
        transcription_snippet=wortlaut_text(row.get("wortlaut", "")),
    )


def records_from_export(export: Export) -> list[db.KatalogRecord]:
    """Every row of ``ritter.csv`` as a record, side tables joined."""
    pdf_index = build_pdf_index(export.pdf_url)
    ov_index = build_ov_index(export.ov_infos, export.ov_inhalt)
    person_index = build_person_index(export.pers_norm) if export.pers_norm else None
    return [
        record_from_row(row, pdf_index=pdf_index, ov_index=ov_index, person_index=person_index)
        for row in export.ritter
        if clean(row.get("ID"))
    ]


# --------------------------------------------------------------------------- #
# The comparison with the records the store holds (the dry run)
# --------------------------------------------------------------------------- #

COMPARED_KEYS: tuple[str, ...] = (
    "katnr",
    "signatur",
    "titel",
    "incipit",
    "datum",
    "aa",
    "sigle",
    "absender",
    "adressat",
    "ort",
    "textart",
    "umfang",
    "wortlaut",
    "drucke",
    "gwlb_ids",
)
# The mapping is settled when these agree on at least 99 % of the records.
THRESHOLD_KEYS: tuple[str, ...] = ("textart", "signatur", "titel", "datum", "aa")
THRESHOLD_PCT = 99.0
CLASSES: tuple[str, ...] = (
    "exact",
    "whitespace",
    "markers",
    "markup",
    "export_adds",
    "export_lacks",
    "other",
)
AGREEING: frozenset[str] = frozenset({"exact", "whitespace", "markers", "markup"})
EXAMPLES_PER_CLASS = 3


def compared_value(rec: db.KatalogRecord, key: str) -> object:
    """A record's value under one compared key, old or new alike."""
    if key == "aa":  # the references with a volume, as the website parser made them
        return tuple(
            sorted(
                (
                    str(r.get("series")),
                    str(r.get("volume")),
                    str(r.get("piece")),
                    str(r.get("source")),
                )
                for r in rec.aa_refs
                if r.get("volume") is not None
            )
        )
    if key == "wortlaut":
        return rec.transcription_snippet or ""
    if key == "gwlb_ids":
        return tuple(rec.gwlb_ids)
    meta = rec.metadata or {}
    value = meta.get(key)
    if key == "titel" and value is None:
        value = meta.get("title")
    return "" if value is None else str(value)


def classify(key: str, old: object, new: object) -> str:
    """How the store's value and the export's compare under one key."""
    if old == new:
        return "exact"
    if not old and new:
        return "export_adds"
    if old and not new:
        return "export_lacks"
    if isinstance(old, str) and isinstance(new, str):
        if clean(old) == clean(new):
            return "whitespace"
        if key in ("absender", "adressat") and clean(MARKERS_RE.sub("", old)) == clean(
            MARKERS_RE.sub("", new)
        ):
            return "markers"
        if clean(old) == clean(website_lost_markup(key, new)):
            return "markup"
    return "other"


def website_lost_markup(key: str, value: str) -> str:
    """The export's value as the website's parser would have kept it: every
    ``<…>`` segment gone, and for the format the code before a bare ``°``."""
    text = MARKUP_RE.sub("", value)
    if key == "umfang":
        text = re.sub(r"\b\d+°", "°", text)
    return text


def _short(value: object, limit: int = 70) -> str:
    text = (
        " ".join(str(value).split())
        if not isinstance(value, tuple)
        else "; ".join(" ".join(map(str, v)) if isinstance(v, tuple) else str(v) for v in value)
    )
    return text if len(text) <= limit else text[: limit - 1] + "…"


@dataclass(slots=True)
class KeyAgreement:
    key: str
    counts: Counter = field(default_factory=Counter)
    examples: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)

    def note(self, cls: str, record_id: str, old: object, new: object) -> None:
        self.counts[cls] += 1
        if cls not in AGREEING:
            bucket = self.examples.setdefault(cls, [])
            if len(bucket) < EXAMPLES_PER_CLASS:
                bucket.append((record_id, _short(old), _short(new)))

    @property
    def agreeing(self) -> int:
        return sum(self.counts[c] for c in AGREEING)

    @property
    def judged(self) -> int:
        """The records that can judge the mapping: those where the website had
        a value (an empty store value proves nothing either way)."""
        return sum(self.counts.values()) - self.counts["export_adds"]

    @property
    def pct(self) -> float:
        return 100.0 * self.agreeing / self.judged if self.judged else 100.0


@dataclass(slots=True)
class Remap:
    """A store record the export no longer carries under its id, and where it went."""

    old_id: str
    new_id: str | None
    how: str  # "Kat.-Nr. and shelfmark" | "Kat.-Nr." | "Identisch_mit" | "mergenr" | "no match"
    katnr: str = ""
    signatur: str = ""


@dataclass(slots=True)
class Comparison:
    """The dry run's findings over the records the store holds."""

    store_records: int
    compared: int
    missing_in_export: list[str]
    new_in_export: int
    keys: dict[str, KeyAgreement]
    hand_changes: list[tuple[str, str, str, bool, bool]]
    remapped: list[Remap] = field(default_factory=list)

    def pct(self, key: str) -> float:
        return self.keys[key].pct

    @property
    def settled(self) -> bool:
        """Every threshold key agrees on ≥ 99 % of the records. The hand rule's
        changes are listed, not a fault of the mapping (the export's fuller
        Textart decides); a store record the export no longer carries is
        remapped or listed: the write drops it unless the ground truth
        references it, which :func:`missing_references` stops."""
        return all(self.pct(k) >= THRESHOLD_PCT for k in THRESHOLD_KEYS)

    @property
    def unmapped(self) -> list[str]:
        """The store's record ids the export carries under no id."""
        return [r.old_id for r in self.remapped if r.new_id is None]


def remap_missing(
    missing: Iterable[db.KatalogRecord],
    new_by_id: Mapping[str, db.KatalogRecord],
    rows: Iterable[Mapping[str, str]] = (),
) -> list[Remap]:
    """Where a store record went whose id the export no longer carries: the
    export's record with the same Kat.-Nr. and shelfmark, else the same
    Kat.-Nr. where it is unique, else the export row whose ``Identisch_mit``
    or ``mergenr`` names the old id; ``new_id`` None where nothing matches."""
    by_katnr: dict[str, list[str]] = {}
    by_both: dict[tuple[str, str], list[str]] = {}
    for rid, rec in new_by_id.items():
        katnr = clean(rec.metadata.get("katnr"))
        if katnr:
            by_katnr.setdefault(katnr, []).append(rid)
            by_both.setdefault((katnr, clean(rec.metadata.get("signatur"))), []).append(rid)
    by_identisch: dict[str, list[str]] = {}
    by_mergenr: dict[str, list[str]] = {}
    for row in rows:
        rid = clean(row.get("ID"))
        if clean(row.get("Identisch_mit")):
            by_identisch.setdefault(clean(row.get("Identisch_mit")), []).append(rid)
        if clean(row.get("mergenr")):
            by_mergenr.setdefault(clean(row.get("mergenr")), []).append(rid)
    out: list[Remap] = []
    for old in missing:
        katnr = clean(old.metadata.get("katnr"))
        signatur = clean(old.metadata.get("signatur")) or clean(
            old.shelfmark_refs[0] if old.shelfmark_refs else ""
        )
        found: tuple[str, str] | None = None
        if katnr and len(by_both.get((katnr, signatur), [])) == 1:
            found = (by_both[(katnr, signatur)][0], "Kat.-Nr. and shelfmark")
        elif katnr and len(by_katnr.get(katnr, [])) == 1:
            found = (by_katnr[katnr][0], "Kat.-Nr.")
        elif len(by_identisch.get(old.record_id, [])) == 1:
            found = (by_identisch[old.record_id][0], "Identisch_mit")
        elif len(by_mergenr.get(old.record_id, [])) == 1:
            found = (by_mergenr[old.record_id][0], "mergenr")
        if found is None:
            out.append(Remap(old.record_id, None, "no match", katnr, signatur))
        else:
            out.append(Remap(old.record_id, found[0], found[1], katnr, signatur))
    return out


def compare_records(
    store_records: Iterable[db.KatalogRecord],
    new_by_id: Mapping[str, db.KatalogRecord],
    rows: Iterable[Mapping[str, str]] = (),
) -> Comparison:
    """Compare every record the store holds with the export's row of the same
    id — or, where the export carries the record under another id
    (:func:`remap_missing`), with that row."""
    keys = {k: KeyAgreement(k) for k in COMPARED_KEYS}
    hand_changes: list[tuple[str, str, str, bool, bool]] = []
    n_store = compared = 0
    store_records = list(store_records)
    missing = [old for old in store_records if old.record_id not in new_by_id]
    remapped = remap_missing(missing, new_by_id, rows)
    target = {r.old_id: r.new_id for r in remapped if r.new_id is not None}
    for old in store_records:
        n_store += 1
        new = new_by_id.get(old.record_id) or new_by_id.get(target.get(old.record_id, ""))
        if new is None:
            continue
        compared += 1
        for key in COMPARED_KEYS:
            o, n = compared_value(old, key), compared_value(new, key)
            keys[key].note(classify(key, o, n), old.record_id, o, n)
        old_hand = hand_from_textart(str(old.metadata.get("textart") or "") or None)
        new_hand = hand_from_textart(str(new.metadata.get("textart") or "") or None)
        old_lz = is_leibniz_hand(old_hand, str(old.metadata.get("absender") or "") or None)
        new_lz = is_leibniz_hand(new_hand, str(new.metadata.get("absender") or "") or None)
        if old_hand != new_hand or old_lz != new_lz:
            hand_changes.append((old.record_id, old_hand, new_hand, old_lz, new_lz))
    return Comparison(
        store_records=n_store,
        compared=compared,
        missing_in_export=sorted(r.old_id for r in remapped if r.new_id is None),
        new_in_export=len(new_by_id) - compared,
        keys=keys,
        hand_changes=hand_changes,
        remapped=remapped,
    )


def render_comparison(cmp: Comparison) -> str:
    """The agreement table and its examples, as Markdown."""
    mapped = [r for r in cmp.remapped if r.new_id is not None]
    lines = [
        f"Records in the store: {cmp.store_records:,} · compared with the export: "
        f"{cmp.compared:,} (of them {len(mapped):,} under another id) · in the store but "
        f"not in the export: {len(cmp.unmapped):,} · in the export only (new): "
        f"{cmp.new_in_export:,}",
        "",
        "| Key | Exact | Whitespace | Markers only | Website lost markup | Export adds | "
        "Export lacks | Other | Agree |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in COMPARED_KEYS:
        k = cmp.keys[key]
        mark = " ✱" if key in THRESHOLD_KEYS else ""
        lines.append(
            f"| {key}{mark} | {k.counts['exact']:,} | {k.counts['whitespace']:,} | "
            f"{k.counts['markers']:,} | {k.counts['markup']:,} | {k.counts['export_adds']:,} | "
            f"{k.counts['export_lacks']:,} | {k.counts['other']:,} | {k.pct:.1f} % |"
        )
    lines += [
        "",
        "✱ the keys the mapping is judged on; settled at ≥ "
        f"{THRESHOLD_PCT:.0f} % each. *Agree* = exact, whitespace-only, the website's link "
        "texts only, or *website lost markup* (the store's value is the export's with every "
        "`<…>` segment gone, or a bare `°` for a format code: text the website's parser read "
        "as HTML tags; the export's value is kept), over the records where the website had a "
        "value. *Export adds*: the "
        "store had nothing and the export has a value (the website's copy lacks it, or the "
        "website parser had no rule for it: a PPN link) — it proves nothing about the "
        "mapping and is left out of the share; *export lacks*: the store has a value the "
        "export does not — counted against; *other*: both have a value and they differ (the "
        "two copies edited apart, or a mapping fault — read the examples) — counted against.",
        "",
    ]
    for key in COMPARED_KEYS:
        k = cmp.keys[key]
        for cls in ("other", "export_lacks", "export_adds"):
            for rid, old, new in k.examples.get(cls, []):
                lines.append(f"- `{key}` {cls} · {rid}: store `{old}` · export `{new}`")
    restored = [(key, cmp.keys[key].counts["markup"]) for key in COMPARED_KEYS]
    restored = [(key, n) for key, n in restored if n]
    if restored:
        lines += [
            "",
            "The export restores text the website's parser lost as markup on "
            + ", ".join(f"{key} {n:,}" for key, n in restored)
            + " records.",
        ]
    if cmp.remapped:
        lines += [
            "",
            f"Records in the store whose id the export no longer carries: {len(cmp.remapped):,} "
            "(the Access master renumbers or merges a few records between the website's "
            "half-yearly imports):",
        ]
        for r in cmp.remapped:
            where = f"→ {r.new_id} by {r.how}" if r.new_id else "no match in the export"
            what = ", ".join(x for x in (f"Kat.-Nr. {r.katnr}" if r.katnr else "", r.signatur) if x)
            lines.append(f"- {r.old_id} ({what or 'no Kat.-Nr., no shelfmark'}): {where}")
    lines += [
        "",
        f"The hand rule (`catalog/hands.py`) gives the same answer before and after on "
        f"{cmp.compared - len(cmp.hand_changes):,} of {cmp.compared:,} records"
        + (
            " (the export's fuller Textart decides; listed, not blocking):"
            if cmp.hand_changes
            else "."
        ),
    ]
    for rid, oh, nh, ol, nl in cmp.hand_changes:
        lines.append(f"- {rid}: hand {oh} → {nh}, Leibniz's own {ol} → {nl}")
    verdict = "settled" if cmp.settled else "NOT settled"
    lines += ["", f"Mapping: **{verdict}**."]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Before any write
# --------------------------------------------------------------------------- #


def referenced_record_ids(conn: sqlite3.Connection) -> dict[str, set[str]]:
    """The record ids other tables reference: the crosswalk's, and the ground
    truth's where the store has the ``record_id`` column (the factory adds it)."""
    out = {
        "crosswalk": {
            r[0] for r in conn.execute("SELECT DISTINCT katalog_record_id FROM crosswalk")
        }
    }
    columns = {r[1] for r in conn.execute("PRAGMA table_info(gt_lines)")}
    if "record_id" in columns:
        out["gt_lines"] = {
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT record_id FROM gt_lines "
                "WHERE record_id IS NOT NULL AND record_id != ''"
            )
        }
    return out


def missing_references(conn: sqlite3.Connection, export_ids: set[str]) -> dict[str, list[str]]:
    """Referenced record ids the export does not carry, by table. A ``gt_lines``
    entry stops the import (the ground truth's ownership would dangle); a
    ``crosswalk`` entry is remapped or dropped by the rebuild and only
    reported."""
    return {
        table: sorted(ids - export_ids)
        for table, ids in referenced_record_ids(conn).items()
        if ids - export_ids
    }


# --------------------------------------------------------------------------- #
# The write
# --------------------------------------------------------------------------- #

PER_WORK_BUCKETS: tuple[tuple[str, int, int], ...] = (
    ("1", 1, 1),
    ("2–5", 2, 5),
    ("6–20", 6, 20),
    ("21–100", 21, 100),
    ("101–500", 101, 500),
    ("over 500", 501, 10**9),
)


@dataclass(slots=True)
class ImportStats:
    """What ``--write`` did and found."""

    run_id: int
    records_written: int
    records_deleted: list[str]
    crosswalk: crosswalk_mod.CrosswalkStats
    links: int
    works: int
    works_with_records: int
    records_per_work: dict[str, int]
    max_records_on_a_work: int
    outside_gwlb: int
    outside_gwlb_by_domain: list[tuple[str, int]]
    without_url: int

    @property
    def works_without_records(self) -> int:
        return self.works - self.works_with_records


def _per_work_histogram(conn: sqlite3.Connection) -> tuple[dict[str, int], int]:
    rows = conn.execute(
        "SELECT work_id, COUNT(DISTINCT katalog_record_id) FROM crosswalk GROUP BY work_id"
    ).fetchall()
    hist = {label: 0 for label, _, _ in PER_WORK_BUCKETS}
    biggest = 0
    for _, n in rows:
        biggest = max(biggest, n)
        for label, lo, hi in PER_WORK_BUCKETS:
            if lo <= n <= hi:
                hist[label] += 1
                break
    return hist, biggest


def outside_gwlb(records: Iterable[db.KatalogRecord]) -> tuple[int, list[tuple[str, int]], int]:
    """How many records link a copy outside the GWLB, by domain; and how many link none."""
    domains: Counter[str] = Counter()
    none = 0
    for rec in records:
        url = str(rec.metadata.get("url_ms") or "").strip()
        if not url:
            none += 1
        elif not is_gwlb_url(url):
            domains[domain_of(url)] += 1
    return sum(domains.values()), sorted(domains.items(), key=lambda kv: (-kv[1], kv[0])), none


def write_import(
    conn: sqlite3.Connection,
    records: Sequence[db.KatalogRecord],
    *,
    export_date: str,
    csv_dir: Path | str,
    git_sha: str | None = None,
    progress=None,
    remapped: Sequence[Remap] | None = None,
) -> ImportStats:
    """Replace ``katalog_records`` by the export (upsert every row, delete what
    the export no longer has), rebuild the crosswalk from scratch — a record
    the export carries under another id (``remapped``) is linked under that
    id by its own links — and record the run. Idempotent: a second run writes
    the same rows and links.

    The caller has checked :func:`missing_references` and holds the operator's
    go; this function does not ask."""
    export_ids = {r.record_id for r in records}
    existing = {r[0] for r in conn.execute("SELECT record_id FROM katalog_records")}
    deleted = sorted(existing - export_ids)
    run_id = db.start_run(
        conn,
        "catalog_import_access",
        params={
            "export_date": export_date,
            "csv_dir": str(csv_dir),
            "records": len(records),
            "deleted": len(deleted),
            "remapped": {r.old_id: r.new_id for r in remapped or () if r.new_id},
        },
        git_sha=git_sha,
    )
    with conn:
        for rec in records:
            db.upsert_katalog_record(conn, rec)
        # the crosswalk references the records: cleared first, rebuilt below
        conn.execute("DELETE FROM crosswalk")
        if deleted:
            conn.executemany(
                "DELETE FROM katalog_records WHERE record_id = ?", [(rid,) for rid in deleted]
            )
    stats = crosswalk_mod.build_crosswalk(conn, progress=progress)
    db.finish_run(conn, run_id, n_input=len(records), n_ok=len(records), n_failed=0)
    hist, biggest = _per_work_histogram(conn)
    outside, by_domain, none = outside_gwlb(records)
    return ImportStats(
        run_id=run_id,
        records_written=len(records),
        records_deleted=deleted,
        crosswalk=stats,
        links=db.count_crosswalk(conn),
        works=db.count_works(conn),
        works_with_records=len(stats.works_matched),
        records_per_work=hist,
        max_records_on_a_work=biggest,
        outside_gwlb=outside,
        outside_gwlb_by_domain=by_domain,
        without_url=none,
    )


def render_import_stats(stats: ImportStats) -> str:
    lines = [
        f"Run {stats.run_id}: {stats.records_written:,} records written, "
        f"{len(stats.records_deleted):,} deleted (the store had them, the export has not).",
        f"Crosswalk rebuilt: {stats.links:,} links · records matched "
        f"{stats.crosswalk.records_matched:,}/{stats.crosswalk.records:,} · by method gwlb_link "
        f"{stats.crosswalk.gwlb_link_matches:,} (+{stats.crosswalk.gwlb_link_unresolved:,} "
        f"to objects not in the store) · shelfmark {stats.crosswalk.shelfmark_matches:,}.",
        f"Works: {stats.works_with_records:,} of {stats.works:,} carry a record, "
        f"{stats.works_without_records:,} none. Records per work (works in each band): "
        + ", ".join(f"{k}: {v:,}" for k, v in stats.records_per_work.items())
        + f"; the most on one work: {stats.max_records_on_a_work:,}.",
        f"URL_Ms outside the GWLB: {stats.outside_gwlb:,} records "
        f"({stats.without_url:,} link nothing); by domain: "
        + ", ".join(f"{d} {n:,}" for d, n in stats.outside_gwlb_by_domain[:12])
        + (" …" if len(stats.outside_gwlb_by_domain) > 12 else "")
        + ".",
    ]
    return "\n".join(lines)


def load_site_records(path: Path | str) -> dict[str, db.KatalogRecord]:
    """Records as the website parser produced them, from a JSON fixture
    (``record_id`` → ``{metadata, shelfmark_refs, aa_refs, transcription_snippet}``)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, db.KatalogRecord] = {}
    for rid, body in data.items():
        out[rid] = db.KatalogRecord(
            record_id=rid,
            metadata=dict(body.get("metadata") or {}),
            shelfmark_refs=list(body.get("shelfmark_refs") or []),
            aa_refs=list(body.get("aa_refs") or []),
            transcription_snippet=body.get("transcription_snippet"),
        )
    return out


__all__ = [
    "AA_SERIES",
    "CLASSES",
    "COMPARED_KEYS",
    "FORMATS",
    "GWLB_PPN_RE",
    "MARKERS_RE",
    "MARKUP_RE",
    "PERS_NORM",
    "TABLES",
    "THRESHOLD_KEYS",
    "THRESHOLD_PCT",
    "Comparison",
    "Export",
    "ImportStats",
    "KeyAgreement",
    "Remap",
    "aa_cell",
    "aa_refs_for",
    "build_ov_index",
    "build_pdf_index",
    "build_person_index",
    "classify",
    "clean",
    "compare_records",
    "compared_value",
    "date_cell",
    "edition_pdf",
    "extent",
    "format_name",
    "gwlb_ids_of",
    "is_gwlb_url",
    "katnr_cell",
    "load_site_records",
    "missing_references",
    "names_as_website",
    "outside_gwlb",
    "read_export",
    "read_table",
    "record_from_row",
    "records_from_export",
    "referenced_record_ids",
    "remap_missing",
    "render_comparison",
    "render_import_stats",
    "umfang_cell",
    "website_lost_markup",
    "wortlaut_text",
    "write_import",
]
