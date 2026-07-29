"""Polite scraper + row parser for the BBAW Ritter-Katalog (Phase A3).

The katalog is a server-rendered Laravel app with **no public API** (SPECS §1.2).
Its structure, inspected live 2026-07-29 (document here so the scrape is
reproducible):

* Search endpoints, both GET, returning a full HTML page (no JSON):
  ``/de/global-search?q=…`` (free text) and ``/de/extended-search?…`` (fielded:
  ``sign_ol`` signature, ``reihe``/``bd``/``nr`` = AA series/volume/piece,
  ``datum_ab``/``datum_bis``, ``absender_oder_adressat``, ``id_hannover``, …).
* Results are one big HTML ``<table>`` (23 columns: Id, Kat.-Nr., **Signatur**,
  Titel, Incipit, Datum, **Akademie Ausgabe**, Sigle, Absender, Adressat,
  Absendeort, Textart, Format/Umfang, …, **Wortlaut**, Drucke, Bemerkungen,
  **Bezüge zu anderen Textzeugen**, …). The **Signatur** cell links out to the
  GWLB scan as ``…/resolve?id={gwlb_object_id}`` — the join key to our ``works``.
* **The result set is capped at 5000 rows** per query (measured). Enumeration
  therefore partitions into sub-5000 slices (by AA volume, signature prefix,
  date range); a query that returns exactly the cap is flagged as truncated.

There is no pagination (``?page=`` is ignored). Raw HTML is cached under
``data/katalog/`` so parsing re-runs offline. Attribution: CC BY 4.0
(``leibniz.catalog.KATALOG_ATTRIBUTION``).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from lxml import html as lxml_html

from leibniz import db

KATALOG_BASE = "https://leibniz-katalog.bbaw.de"
GLOBAL_SEARCH = f"{KATALOG_BASE}/de/global-search"
EXTENDED_SEARCH = f"{KATALOG_BASE}/de/extended-search"
DEFAULT_CACHE_DIR = Path("data/katalog")

# Server-side result cap (rows per query), measured live 2026-07-29.
RESULT_CAP = 5000

# A GWLB scan link in a record: "…/resolve?id={object_id}". The id is exactly our
# works PK (both 8-digit and DE-611-HS-… shapes occur).
GWLB_RESOLVE_RE = re.compile(r"resolve\?id=([A-Za-z0-9][\w\-]*)")

# Result-table column header (German) → the field name we store it under.
_HEADER_FIELDS: dict[str, str] = {
    "Id": "record_id",
    "Kat.-Nr.": "katnr",
    "Signatur": "signatur",
    "Titel": "titel",
    "Incipit": "incipit",
    "Datum": "datum",
    "Akademie Ausgabe": "aa",
    "Sigle": "sigle",
    "Absender": "absender",
    "Adressat": "adressat",
    "Absendeort": "ort",
    "Textart": "textart",
    "Format und Umfang": "umfang",
    "Wortlaut": "wortlaut",
    "Drucke": "drucke",
    "Bemerkungen": "bemerkungen",
    "Bezüge zu anderen Textzeugen": "bezuege",
}

# AA reference in the "Akademie Ausgabe" column: "2 | 1.130 / a …" → II,1 N.130a.
_AA_COLUMN_RE = re.compile(r"(\d+)\s*\|\s*(\d+)\.(\d+)(?:\s*/\s*([a-z]))?")
# AA reference in the "Bezüge" column: "II,1 N.130a = III,1 N.89".
_AA_BEZUEGE_RE = re.compile(r"\b([IVX]+),\s*(\d+)\s*N\.?\s*(\d+[a-z]?)")
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def parse_aa_refs(aa_column: str, bezuege: str) -> list[dict]:
    """Parse Akademie-Ausgabe references from the two columns that carry them."""
    refs: list[dict] = []
    seen: set[tuple] = set()

    def _add(series: int, volume: int, piece: str, source: str) -> None:
        key = (series, volume, piece)
        if key not in seen:
            seen.add(key)
            refs.append({"series": series, "volume": volume, "piece": piece, "source": source})

    for m in _AA_COLUMN_RE.finditer(aa_column or ""):
        series, volume, num = int(m.group(1)), int(m.group(2)), m.group(3)
        piece = f"{num}{m.group(4)}" if m.group(4) else num
        _add(series, volume, piece, "aa_column")
    for m in _AA_BEZUEGE_RE.finditer(bezuege or ""):
        series = _ROMAN.get(m.group(1))
        if series is not None:
            _add(series, int(m.group(2)), m.group(3), "bezuege")
    return refs


def _results_table(doc) -> object | None:
    """The record table = the ``<table>`` with the most header cells (23)."""
    tables = doc.xpath("//table[.//th]")
    return max(tables, key=lambda t: len(t.xpath(".//th")), default=None)


def parse_result_table(content: bytes | str) -> list[db.KatalogRecord]:
    """Parse a katalog search-result page into :class:`~leibniz.db.KatalogRecord`\\ s.

    Robust to column reordering (fields are keyed by header text, not position)
    and to junk rows (a row without an ``Id`` is skipped). GWLB object ids are
    lifted from every ``resolve?id=`` link in the row, so the crosswalk join key
    survives even if the site moves the link between cells.
    """
    doc = lxml_html.fromstring(content)
    tbl = _results_table(doc)
    if tbl is None:
        return []
    headers = [_clean(th.text_content()) for th in tbl.xpath(".//tr[th]/th")]
    if not headers:
        headers = [_clean(th.text_content()) for th in tbl.xpath(".//th")]
    idx = {_HEADER_FIELDS[h]: i for i, h in enumerate(headers) if h in _HEADER_FIELDS}

    records: list[db.KatalogRecord] = []
    for tr in tbl.xpath(".//tr[td]"):
        cells = tr.xpath("./td")
        if not cells:
            continue
        # Field name → cell text, resolved by header position (robust to reordering).
        f = {name: _clean(cells[i].text_content()) for name, i in idx.items() if i < len(cells)}

        record_id = f.get("record_id", "")
        if not record_id:
            continue  # header echo / spacer row

        row_html = lxml_html.tostring(tr, encoding="unicode")
        gwlb_ids = list(dict.fromkeys(GWLB_RESOLVE_RE.findall(row_html)))

        signatur = f.get("signatur", "")
        aa_refs = parse_aa_refs(f.get("aa", ""), f.get("bezuege", ""))
        wortlaut = f.get("wortlaut") or None

        metadata = {
            "katnr": f.get("katnr", ""),
            "signatur": signatur,
            "titel": f.get("titel", ""),
            "incipit": f.get("incipit", ""),
            "datum": f.get("datum", ""),
            "sigle": f.get("sigle", ""),
            "absender": f.get("absender", ""),
            "adressat": f.get("adressat", ""),
            "ort": f.get("ort", ""),
            "textart": f.get("textart", ""),
            "umfang": f.get("umfang", ""),
            "drucke": f.get("drucke", ""),
            "gwlb_ids": gwlb_ids,
        }
        records.append(
            db.KatalogRecord(
                record_id=record_id,
                metadata={k: v for k, v in metadata.items() if v},
                shelfmark_refs=[signatur] if signatur else [],
                aa_refs=aa_refs,
                transcription_snippet=wortlaut,
            )
        )
    return records


def result_count_hint(content: bytes | str) -> int | None:
    """The record count the page reports (``"229 Treffer"``), if present."""
    text = content.decode("utf-8", "replace") if isinstance(content, bytes) else content
    m = re.search(r"([\d.]+)\s*(?:Treffer|Ergebnis)", text)
    return int(m.group(1).replace(".", "")) if m else None


# --------------------------------------------------------------------------- #
# Enumeration / orchestration
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ScrapeStats:
    """Bookkeeping returned by :func:`scrape`."""

    queries: int = 0
    fetched: int = 0
    cached: int = 0
    records: int = 0
    with_gwlb_link: int = 0
    capped_queries: list[str] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)


ProgressFn = Callable[[str, int], None]


def query_endpoint(params: Mapping[str, str]) -> str:
    """Global search for a bare ``q``; the fielded endpoint otherwise."""
    return GLOBAL_SEARCH if set(params) <= {"q"} else EXTENDED_SEARCH


def query_slug(params: Mapping[str, str]) -> str:
    """A filesystem-safe cache key for a query's parameters."""
    raw = "_".join(f"{k}-{params[k]}" for k in sorted(params))
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw) or "all"


def default_sample_queries() -> list[dict[str, str]]:
    """A small, sub-cap set of queries spanning sets — the session's live sample.

    AA-volume slices (correspondence, → Briefwechsel/Handschriften works) plus a
    couple of signature-prefix slices (Handschriften, Marginalien). Each is well
    under the 5000-row cap. The *full* enumeration (all ~70k records) is an
    operator job — see the crosswalk report.
    """
    return [
        {"reihe": "1", "bd": "1"},
        {"reihe": "1", "bd": "2"},
        {"reihe": "2", "bd": "1"},
        {"reihe": "3", "bd": "1"},
        {"sign_ol": "LH 35"},
        {"sign_ol": "Leibn. Marg. 1"},
    ]


def scrape(
    conn,
    *,
    client,
    queries: Sequence[Mapping[str, str]],
    cache_dir: Path = DEFAULT_CACHE_DIR,
    force: bool = False,
    progress: ProgressFn | None = None,
) -> ScrapeStats:
    """Fetch/parse a list of katalog queries into ``katalog_records`` (cache-first).

    Each query is a dict of search params. Raw HTML is cached under ``cache_dir``;
    a cached query is re-parsed offline unless ``force``. A query whose result
    count hits :data:`RESULT_CAP` is recorded in ``capped_queries`` (its slice is
    too broad — narrow it), never silently truncated.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    stats = ScrapeStats()
    for params in queries:
        stats.queries += 1
        slug = query_slug(params)
        path = cache_dir / f"{slug}.html"
        try:
            if path.exists() and not force:
                content, from_cache = path.read_bytes(), True
            else:
                content = client.get_bytes(query_endpoint(params), params=dict(params))
                path.write_bytes(content)
                from_cache = False
        except Exception as exc:  # noqa: BLE001 — collect, continue the sweep
            stats.failures.append((slug, f"{type(exc).__name__}: {exc}"))
            continue

        stats.cached += int(from_cache)
        stats.fetched += int(not from_cache)
        records = parse_result_table(content)
        if len(records) >= RESULT_CAP:
            stats.capped_queries.append(slug)
        for rec in records:
            db.upsert_katalog_record(conn, rec)
            stats.records += 1
            if rec.gwlb_ids:
                stats.with_gwlb_link += 1
        conn.commit()
        if progress is not None:
            progress(slug, len(records))
    return stats


__all__ = [
    "DEFAULT_CACHE_DIR",
    "EXTENDED_SEARCH",
    "GLOBAL_SEARCH",
    "GWLB_RESOLVE_RE",
    "KATALOG_BASE",
    "RESULT_CAP",
    "ScrapeStats",
    "default_sample_queries",
    "parse_aa_refs",
    "parse_result_table",
    "query_endpoint",
    "query_slug",
    "result_count_hint",
    "scrape",
]
