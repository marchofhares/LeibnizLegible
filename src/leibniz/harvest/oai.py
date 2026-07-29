"""OAI-PMH harvest — GWLB METS/MODS ``ListRecords`` → the ``works`` table.

The GWLB serves OAI-PMH 2.0 at ``https://digitale-sammlungen.gwlb.de/oai2/``
from a TYPO3/Kitodo (``dlf``) stack, ``metadataPrefix=mets`` (METS wrapping
MODS). We harvest the five Leibniz sets, cache every raw response page under
``data/oai/{set}/page_NNNN.xml`` (so parsing is re-runnable offline), and parse
each record into a :class:`~leibniz.db.Work`.

What the METS gives us (verified live 2026-07-28 against real records — see
``reports/crawl-posture.md`` and ``STATUS.md`` for drift notes):

* **object id** — the OAI ``<identifier>``. It is *not* always the 8-digit id
  SPECS §4.4 assumes: Handschriften/Leibnitiana use ``00068642``, Marginalien
  use a 9-digit VD17 id, Briefwechsel/Rekonstruktionen use ``DE-611-HS-...``.
  We store whatever the OAI id is — it is exactly what the content/IIIF URLs use.
* **manifest url** — ``mods:identifier[@type='iiif']`` when present (rare), else
  constructed as ``{content}/{id}/manifest.json`` (verified to resolve for both
  id shapes).
* **title** — ``mods:title`` of the logical descriptive section. Often generic
  ("Nachlass Gottfried Wilhelm Leibniz" for every Briefwechsel bundle), so the
  shelfmark, not the title, is the human identifier.
* **shelfmarks** — every distinct ``mods:shelfLocator``. One record may list the
  same signature twice (logical + physical dmdSec) and in two normalisations
  (``LH 35, I, 17`` and ``LH XXXV, I, 17``); we keep distinct strings and let
  the A3 normaliser reconcile them.
* **n_canvases** — the count of ``mets:div[@TYPE='page']`` in the *physical*
  structMap. This equals the IIIF manifest's canvas count (checked on 00068642:
  4 == 4), so the corpus page count — the A1 gate number — is obtainable from the
  OAI harvest alone, without fetching one manifest per work.

Set membership overlaps heavily (nearly every record is also in ``Leibnitiana``
and the generic ``Handschriften``/``Drucke`` sets), so a work's *primary* set is
assigned deterministically from its own ``setSpec`` list by priority, and the
census deduplicates by object id before reporting the real total.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from leibniz import db
from leibniz.net import PoliteClient

OAI_BASE = "https://digitale-sammlungen.gwlb.de/oai2/"
CONTENT_BASE = "https://digitale-sammlungen.gwlb.de/content"
DEFAULT_CACHE_DIR = Path("data/oai")

# The five Leibniz OAI sets, in *primary-set priority* order: the specific
# manuscript / letter / marginalia / reconstruction sets outrank the catch-all
# ``Leibnitiana``. A work in several sets is attributed to the first it matches.
LEIBNIZ_SETS: tuple[str, ...] = (
    "LeibnizHandschriften",
    "LeibnizBriefwechsel",
    "LeibnizMarginalien",
    "leibniz-rekonstruktionen",
    "Leibnitiana",
)
_SET_PRIORITY = {name: i for i, name in enumerate(LEIBNIZ_SETS)}

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "mets": "http://www.loc.gov/METS/",
    "mods": "http://www.loc.gov/mods/v3",
    "xlink": "http://www.w3.org/1999/xlink",
    "dv": "http://dfg-viewer.de/",
}


class OaiError(RuntimeError):
    """An OAI-PMH protocol ``<error>`` element (e.g. ``badResumptionToken``)."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(f"OAI error [{code}]: {message}".strip())
        self.code = code
        self.message = message


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ParsedRecord:
    """The fields we lift from one OAI/METS record."""

    object_id: str
    setspecs: list[str]
    title: str | None
    shelfmarks: list[str]
    manifest_url: str
    n_canvases: int
    has_iiif: bool = False  # METS carries mods:identifier[@type='iiif'] (has a manifest)
    datestamp: str | None = None
    dating: str | None = None
    extent: str | None = None
    license: str | None = None
    kitodo_project: str | None = None

    @property
    def leibniz_sets(self) -> list[str]:
        """This record's membership among the five Leibniz sets, priority-ordered."""
        return [s for s in LEIBNIZ_SETS if s in self.setspecs]

    @property
    def primary_set(self) -> str:
        """Deterministic owning set: highest-priority Leibniz set it belongs to."""
        ls = self.leibniz_sets
        return min(ls, key=lambda s: _SET_PRIORITY[s]) if ls else "unknown"


@dataclass(slots=True)
class OaiPage:
    """One ``ListRecords`` response: its records plus paging bookkeeping."""

    records: list[ParsedRecord]
    resumption_token: str | None
    complete_list_size: int | None


def _text(el: etree._Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    t = el.text.strip()
    return t or None


def _first(node: etree._Element, xpath: str) -> etree._Element | None:
    found = node.xpath(xpath, namespaces=NS)
    return found[0] if found else None


def _logical_mods(mets_el: etree._Element) -> etree._Element | None:
    """The MODS block that describes the whole object (not a physical page).

    Prefer the ``dmdSec`` referenced by the LOGICAL structMap's top div; fall
    back to the first ``dmdSec`` MODS that carries a title, then to any MODS.
    """
    dmdid = None
    top = _first(mets_el, ".//mets:structMap[@TYPE='LOGICAL']/mets:div")
    if top is not None:
        dmdid = top.get("DMDID")
    dmdsecs = mets_el.xpath(".//mets:dmdSec", namespaces=NS)
    if dmdid:
        for d in dmdsecs:
            if d.get("ID") == dmdid:
                mods = _first(d, ".//mods:mods")
                if mods is not None:
                    return mods
    fallback = None
    for d in dmdsecs:
        mods = _first(d, ".//mods:mods")
        if mods is None:
            continue
        if fallback is None:
            fallback = mods
        if _first(mods, ".//mods:titleInfo/mods:title") is not None:
            return mods
    return fallback


def _dedup(items: Iterable[str]) -> list[str]:
    seen: dict[str, None] = {}
    for it in items:
        if it and it not in seen:
            seen[it] = None
    return list(seen)


def parse_record(rec_el: etree._Element) -> ParsedRecord | None:
    """Parse one ``<record>``; return ``None`` for deleted/identifier-less records.

    Defensive by design (Kitodo METS has quirks): a record with no METS body or
    no physical structMap still yields a :class:`ParsedRecord` with
    ``n_canvases=0`` so the census can flag it as an anomaly rather than crash.
    """
    header = _first(rec_el, "oai:header")
    if header is None:
        return None
    if (header.get("status") or "").lower() == "deleted":
        return None
    object_id = _text(_first(header, "oai:identifier"))
    if not object_id:
        return None
    setspecs = _dedup(
        t for t in (_text(s) for s in header.xpath("oai:setSpec", namespaces=NS)) if t
    )
    datestamp = _text(_first(header, "oai:datestamp"))
    manifest_fallback = f"{CONTENT_BASE}/{object_id}/manifest.json"

    mets_el = _first(rec_el, ".//mets:mets")
    if mets_el is None:
        return ParsedRecord(
            object_id=object_id,
            setspecs=setspecs,
            title=None,
            shelfmarks=[],
            manifest_url=manifest_fallback,
            n_canvases=0,
            datestamp=datestamp,
        )

    mods = _logical_mods(mets_el)
    title = _text(_first(mods, ".//mods:titleInfo/mods:title")) if mods is not None else None
    shelfmarks = _dedup(
        t for t in (_text(e) for e in mets_el.xpath(".//mods:shelfLocator", namespaces=NS)) if t
    )
    iiif = _text(_first(mets_el, ".//mods:identifier[@type='iiif']"))
    kitodo_project = _text(_first(mets_el, ".//mods:identifier[@type='kitodo-project']"))
    dating = _text(_first(mets_el, ".//mods:originInfo/mods:dateCreated"))
    extent = _text(_first(mets_el, ".//mods:physicalDescription/mods:extent"))
    license_ = _text(_first(mets_el, ".//mods:accessCondition")) or _text(
        _first(mets_el, ".//dv:license")
    )

    phys = _first(mets_el, ".//mets:structMap[@TYPE='PHYSICAL']")
    n_canvases = (
        len(phys.xpath(".//mets:div[@TYPE='page']", namespaces=NS)) if phys is not None else 0
    )

    return ParsedRecord(
        object_id=object_id,
        setspecs=setspecs,
        title=title,
        shelfmarks=shelfmarks,
        manifest_url=iiif or manifest_fallback,
        n_canvases=n_canvases,
        has_iiif=iiif is not None,
        datestamp=datestamp,
        dating=dating,
        extent=extent,
        license=license_,
        kitodo_project=kitodo_project,
    )


def parse_response(xml: bytes | str) -> OaiPage:
    """Parse a ``ListRecords`` response into records + resumption bookkeeping.

    Raises :class:`OaiError` if the response carries an OAI ``<error>``.
    """
    root = etree.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    err = _first(root, ".//oai:error")
    if err is not None:
        raise OaiError(err.get("code") or "unknown", _text(err) or "")
    records = [
        pr for rec in root.xpath(".//oai:record", namespaces=NS) if (pr := parse_record(rec))
    ]
    tok_el = _first(root, ".//oai:resumptionToken")
    token = _text(tok_el)
    cls = None
    if tok_el is not None and tok_el.get("completeListSize"):
        try:
            cls = int(tok_el.get("completeListSize"))
        except (TypeError, ValueError):
            cls = None
    return OaiPage(records=records, resumption_token=token, complete_list_size=cls)


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #


def to_work(rec: ParsedRecord, harvest_set: str) -> db.Work:
    """Map a :class:`ParsedRecord` onto a :class:`~leibniz.db.Work` row."""
    return db.Work(
        gwlb_object_id=rec.object_id,
        set_name=rec.primary_set,
        title=rec.title,
        shelfmarks=rec.shelfmarks,
        metadata={
            "leibniz_sets": rec.leibniz_sets,
            "setspecs": rec.setspecs,
            "harvest_set": harvest_set,
            "has_iiif_manifest": rec.has_iiif,
            "datestamp": rec.datestamp,
            "dating": rec.dating,
            "extent": rec.extent,
            "license": rec.license,
            "kitodo_project": rec.kitodo_project,
        },
        manifest_url=rec.manifest_url,
        n_canvases=rec.n_canvases,
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class SetHarvest:
    """Per-set bookkeeping returned by :func:`harvest_oai`."""

    set_name: str
    complete_list_size: int | None = None
    pages_read: int = 0
    pages_fetched: int = 0
    records: int = 0


ProgressFn = Callable[[str, int, int | None], None]


def _page_path(cache_dir: Path, set_name: str, page_num: int) -> Path:
    return cache_dir / set_name / f"page_{page_num:04d}.xml"


def _harvest_set(
    set_name: str,
    *,
    conn,
    client: PoliteClient,
    cache_dir: Path,
    force: bool,
    limit_pages: int | None,
    progress: ProgressFn | None,
) -> SetHarvest:
    (cache_dir / set_name).mkdir(parents=True, exist_ok=True)
    stats = SetHarvest(set_name=set_name)
    token: str | None = None
    page_num = 0
    while True:
        page_num += 1
        if limit_pages is not None and page_num > limit_pages:
            break
        path = _page_path(cache_dir, set_name, page_num)
        if path.exists() and not force:
            xml = path.read_bytes()
            stats.pages_read += 1
        else:
            params = (
                {"verb": "ListRecords", "resumptionToken": token}
                if token
                else {"verb": "ListRecords", "metadataPrefix": "mets", "set": set_name}
            )
            xml = client.get_bytes(OAI_BASE, params=params)
            path.write_bytes(xml)
            stats.pages_fetched += 1

        try:
            page = parse_response(xml)
        except OaiError as exc:
            if exc.code == "noRecordsMatch":
                break
            # A stale continuation token (tokens expire ~30 min): re-fetch the
            # whole set live, overwriting its cache. Only possible when resuming
            # a set that was interrupted mid-way in an earlier session.
            if exc.code == "badResumptionToken" and not force:
                return _harvest_set(
                    set_name,
                    conn=conn,
                    client=client,
                    cache_dir=cache_dir,
                    force=True,
                    limit_pages=limit_pages,
                    progress=progress,
                )
            raise

        if stats.complete_list_size is None and page.complete_list_size is not None:
            stats.complete_list_size = page.complete_list_size
        for rec in page.records:
            db.upsert_work(conn, to_work(rec, set_name))
            stats.records += 1
        conn.commit()
        if progress is not None:
            progress(set_name, stats.records, stats.complete_list_size)

        token = page.resumption_token
        if not token:
            break
    return stats


def harvest_oai(
    conn,
    *,
    client: PoliteClient,
    sets: Iterable[str] = LEIBNIZ_SETS,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    force: bool = False,
    limit_pages: int | None = None,
    progress: ProgressFn | None = None,
) -> list[SetHarvest]:
    """Harvest each set's ``ListRecords`` pages into ``works`` (cache-first).

    Resumable: fully-cached sets are re-parsed offline (no network); an
    interrupted set continues from its last cached page's resumption token, and
    falls back to a fresh live re-harvest if that token has expired. ``force``
    ignores the cache; ``limit_pages`` caps pages per set (dev slices).
    """
    cache_dir = Path(cache_dir)
    return [
        _harvest_set(
            s,
            conn=conn,
            client=client,
            cache_dir=cache_dir,
            force=force,
            limit_pages=limit_pages,
            progress=progress,
        )
        for s in sets
    ]


__all__ = [
    "CONTENT_BASE",
    "DEFAULT_CACHE_DIR",
    "LEIBNIZ_SETS",
    "OAI_BASE",
    "OaiError",
    "OaiPage",
    "ParsedRecord",
    "SetHarvest",
    "harvest_oai",
    "parse_record",
    "parse_response",
    "to_work",
]
