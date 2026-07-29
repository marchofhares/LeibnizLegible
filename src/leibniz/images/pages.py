"""Derive per-page delivery URLs from the GWLB METS ``fileSec`` (offline).

This is the page-population step deferred from A1 (STATUS Open Q #2). The OAI
ListRecords XML we already cached under ``data/oai/`` embeds, for every record,
a METS ``fileSec`` listing each page's image files by ``USE`` group
(``THUMBS`` / ``DEFAULT`` / ``MAX`` JPEGs, ``DOWNLOAD`` PDFs) plus a physical
``structMap`` whose ``page`` divisions carry ``ORDER``/``ORDERLABEL`` and file
pointers. Joining the two yields, per page and **without any network**:

* ``image_url``   — the ``DEFAULT`` (falling back to ``MAX``) JPEG: the delivery
  derivative A2 downloads. Present for the whole corpus, IIIF and static alike.
* ``thumb_url``   — the ``THUMBS`` JPEG.
* ``image_service_url`` — the IIIF Image API base (``…/iiif/{id}/ptif/{seq}.ptif``),
  constructed only for works whose METS carries ``mods:identifier[@type='iiif']``
  (kept for D2 deep-zoom; a lower bound on IIIF availability, per STATUS).
* ``delivery``    — ``'iiif'`` or ``'static'``.

Where a ``fileSec`` entry is missing, the URL is reconstructed from the verified
GWLB convention (``…/content/{id}/jpgs/default/{seq:08d}.jpg``), so a quirky
record still yields a usable row rather than a hole.
"""

from __future__ import annotations

from collections.abc import Callable, Container
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from leibniz import db
from leibniz.harvest.oai import CONTENT_BASE, NS
from leibniz.harvest.oai import DEFAULT_CACHE_DIR as OAI_CACHE_DIR

# IIIF Image API base for the constructed service URL (pyramid TIFF per canvas).
IIIF_BASE = "https://digitale-sammlungen.gwlb.de/iiif"
_XLINK_HREF = "{http://www.w3.org/1999/xlink}href"

# fileSec USE groups, in preference order, that hold the full delivery JPEG.
_DELIVERY_USES = ("DEFAULT", "MAX")


@dataclass(slots=True)
class PageImage:
    """One page's image URLs, derived from a METS record."""

    seq: int
    order_label: str | None
    image_url: str | None
    thumb_url: str | None
    image_service_url: str | None
    delivery: str  # 'iiif' | 'static'

    def to_page(self, object_id: str) -> db.Page:
        """Map onto a pending :class:`~leibniz.db.Page` (derivation fields only)."""
        return db.Page(
            work_id=object_id,
            seq=self.seq,
            image_service_url=self.image_service_url,
            image_url=self.image_url,
            thumb_url=self.thumb_url,
            delivery=self.delivery,
            label=self.order_label,  # METS ORDERLABEL = folio label (C2 resolver)
            status="pending",
        )


def _filesec(mets_el: etree._Element) -> dict[str, tuple[str, str]]:
    """Map ``file@ID -> (USE, href)`` from the METS ``fileSec``."""
    out: dict[str, tuple[str, str]] = {}
    for f in mets_el.xpath(".//mets:fileSec//mets:file", namespaces=NS):
        fid = f.get("ID")
        parent = f.getparent()
        use = (parent.get("USE") if parent is not None else None) or ""
        flocat = f.find("mets:FLocat", NS)
        href = flocat.get(_XLINK_HREF) if flocat is not None else None
        if fid and href:
            out[fid] = (use.upper(), href)
    return out


def iter_page_images(mets_el: etree._Element, object_id: str) -> list[PageImage]:
    """Derive per-page image URLs from one record's ``<mets:mets>`` element.

    Returns one :class:`PageImage` per physical ``page`` division, in ``ORDER``.
    An empty physical structMap (container/anchor records) yields ``[]``.
    """
    files = _filesec(mets_el)
    has_iiif = mets_el.find(".//mods:identifier[@type='iiif']", NS) is not None
    delivery = "iiif" if has_iiif else "static"

    phys = mets_el.find(".//mets:structMap[@TYPE='PHYSICAL']", NS)
    if phys is None:
        return []

    pages: list[PageImage] = []
    for i, div in enumerate(phys.xpath(".//mets:div[@TYPE='page']", namespaces=NS), start=1):
        try:
            seq = int(div.get("ORDER"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            seq = i
        by_use: dict[str, str] = {}
        for fp in div.xpath("mets:fptr", namespaces=NS):
            hit = files.get(fp.get("FILEID"))
            if hit is not None:
                by_use[hit[0]] = hit[1]

        image_url = next((by_use[u] for u in _DELIVERY_USES if u in by_use), None)
        thumb_url = by_use.get("THUMBS")
        # Reconstruct from the verified convention if the fileSec was incomplete.
        if image_url is None:
            image_url = f"{CONTENT_BASE}/{object_id}/jpgs/default/{seq:08d}.jpg"
        if thumb_url is None:
            thumb_url = f"{CONTENT_BASE}/{object_id}/jpgs/thumbs/{seq:08d}.jpg"
        service = f"{IIIF_BASE}/{object_id}/ptif/{seq:08d}.ptif" if has_iiif else None

        pages.append(
            PageImage(
                seq=seq,
                order_label=div.get("ORDERLABEL"),
                image_url=image_url,
                thumb_url=thumb_url,
                image_service_url=service,
                delivery=delivery,
            )
        )
    return pages


# --------------------------------------------------------------------------- #
# Orchestration — populate `pages` from the cached OAI XML (offline)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class DeriveStats:
    """Bookkeeping returned by :func:`populate_pages_from_cache`."""

    works: int = 0
    pages: int = 0
    static_pages: int = 0
    iiif_pages: int = 0
    zero_page_works: int = 0


ProgressFn = Callable[[str, int], None]


def _iter_cached_records(cache_dir: Path):
    """Yield ``(object_id, mets_element)`` for every record in the OAI cache.

    Reads the raw ListRecords XML pages (``data/oai/{set}/page_*.xml``) that the
    A1 harvest wrote. A work recurs across overlapping sets; de-duplication is
    the caller's job.
    """
    for xml_path in sorted(cache_dir.glob("*/page_*.xml")):
        try:
            root = etree.fromstring(xml_path.read_bytes())
        except etree.XMLSyntaxError:
            continue
        for rec in root.xpath(".//oai:record", namespaces=NS):
            header = rec.find("oai:header", NS)
            if header is None or (header.get("status") or "").lower() == "deleted":
                continue
            ident = header.findtext("oai:identifier", namespaces=NS)
            mets_el = rec.find(".//mets:mets", NS)
            if ident and mets_el is not None:
                yield ident.strip(), mets_el


def populate_pages_from_cache(
    conn,
    *,
    cache_dir: Path = OAI_CACHE_DIR,
    include: Container[str] | None = None,
    progress: ProgressFn | None = None,
) -> DeriveStats:
    """Populate ``pages`` for every cached work from its METS ``fileSec`` (offline).

    Idempotent and safe to re-run against a populated store: :func:`db.upsert_page`
    preserves any download manifest already recorded. ``include`` restricts
    derivation to a set of object ids (a dev slice); ``None`` does the whole
    corpus. Each object is processed once even though it recurs across sets.
    """
    cache_dir = Path(cache_dir)
    stats = DeriveStats()
    seen: set[str] = set()
    for object_id, mets_el in _iter_cached_records(cache_dir):
        if object_id in seen:
            continue
        if include is not None and object_id not in include:
            continue
        seen.add(object_id)
        if db.get_work(conn, object_id) is None:
            continue  # a page's FK requires the work; skip orphans defensively
        images = iter_page_images(mets_el, object_id)
        stats.works += 1
        if not images:
            stats.zero_page_works += 1
        for img in images:
            db.upsert_page(conn, img.to_page(object_id))
            stats.pages += 1
            if img.delivery == "iiif":
                stats.iiif_pages += 1
            else:
                stats.static_pages += 1
        conn.commit()
        if progress is not None:
            progress(object_id, len(images))
    return stats


__all__ = [
    "CONTENT_BASE",
    "IIIF_BASE",
    "DeriveStats",
    "PageImage",
    "iter_page_images",
    "populate_pages_from_cache",
]
