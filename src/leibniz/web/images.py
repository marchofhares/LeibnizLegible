"""Where the viewer's page images come from — the mirror switch.

By default the API hands the viewer and the manifests the GWLB's own URLs:
the IIIF image service where a work has one, otherwise the delivery JPEG the
METS names (SPECS §3.4). With ``LEIBNIZ_IMAGE_BASE_URL`` set, the operator
serves a **mirror of the delivery derivatives** instead: the A2 image cache
uploaded as it is, plus the thumbnails ``leibniz images thumbs`` derives —

    {base}/{work_id}/{seq:04d}.jpg          the delivery derivative, full size
    {base}/thumbs/{work_id}/{seq:04d}.jpg   its thumbnail

The layout is :func:`leibniz.images.fetch.cache_relpath`, so the bucket is
the cache directory, unchanged, and the line polygons — computed on those very
files — sit on the pixels they were read from. Pages that were never cached
(the sixteen behind broken delivery URLs) keep their GWLB URLs.

Provenance is untouched either way: the page API and the annotations keep
naming the GWLB URI as the source image (SPECS §4.5), and a mirrored manifest
carries it per canvas; the mirror only changes where the pixels are fetched
from. The decision is recorded in STATUS.md (Divergences), because SPECS
§3.4 and §7.1 say "never rehosted".
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from urllib.parse import quote

from leibniz import db
from leibniz.images.fetch import cache_relpath

THUMBS_PREFIX = "thumbs"


@dataclass(frozen=True, slots=True)
class ImageSource:
    """Resolves display URLs for pages: the mirror when configured, else the GWLB."""

    base_url: str | None = None

    def __post_init__(self) -> None:
        base = (self.base_url or "").strip().rstrip("/") or None
        object.__setattr__(self, "base_url", base)

    @property
    def mirrored(self) -> bool:
        return self.base_url is not None

    @property
    def origin(self) -> str:
        return "mirror" if self.mirrored else "gwlb"

    def is_mirrored(self, page: db.Page) -> bool:
        return self.mirrored and bool(page.local_path)

    def image_url(self, page: db.Page) -> str | None:
        if self.is_mirrored(page):
            return f"{self.base_url}/{quote(str(page.local_path))}"
        return page.image_url

    def thumb_url(self, page: db.Page) -> str | None:
        if self.is_mirrored(page):
            return f"{self.base_url}/{THUMBS_PREFIX}/{quote(str(page.local_path))}"
        return page.thumb_url

    def thumb_url_for(self, work_id: str, seq: int, fallback: str | None) -> str | None:
        """A search hit carries no ``local_path``; every indexed page was cached,
        so its thumbnail follows from the layout."""
        if not self.mirrored:
            return fallback
        return f"{self.base_url}/{THUMBS_PREFIX}/{quote(cache_relpath(work_id, seq))}"

    @staticmethod
    def source_url(page: db.Page) -> str | None:
        """The canonical GWLB image URI — provenance, whatever is displayed."""
        return page.image_service_url or page.image_url

    def resolve(self, page: db.Page) -> db.Page:
        """A copy of ``page`` whose display fields point at the mirror, as a
        static image (no IIIF service); the page itself when not mirrored."""
        if not self.is_mirrored(page):
            return page
        return replace(
            page,
            image_url=self.image_url(page),
            thumb_url=self.thumb_url(page),
            image_service_url=None,
            delivery="static",
        )


__all__ = ["THUMBS_PREFIX", "ImageSource"]
