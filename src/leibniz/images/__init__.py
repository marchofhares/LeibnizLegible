"""Image-cache stage — local delivery-derivative cache for every page (Phase A2).

Downloads one JPEG delivery derivative per page into ``data/images/`` and records
it (path, size, sha256, dimensions) in the ``pages`` manifest — resumable,
integrity-checked, and polite (SPECS §7.4). We never rehost or re-serve these
images; the cache is an internal working store for the segmentation/HTR pipeline
(the public viewer, D2, loads tiles directly from GWLB's IIIF).

Delivery model (revises the A2 prompt per the STATUS "Major drift" note). SPECS
§1.1 assumed IIIF Image API tiles for the whole Nachlass, but only ~1/3 of works
are IIIF-served. The GWLB METS ``fileSec`` — already in the cached OAI
ListRecords XML — carries an authoritative ``DEFAULT`` JPEG URL
(``…/content/{id}/jpgs/default/{seq:08d}.jpg``) for **every** page, IIIF and
static alike. A2 therefore caches that uniform delivery derivative across all
~237k pages, deriving the per-page URLs offline from the METS. The IIIF Image
API service URL is retained per page (``pages.image_service_url``) for D2's
deep-zoom, but is not the cache source.

Submodules: :mod:`~leibniz.images.pages` (derive ``pages`` from cached METS),
:mod:`~leibniz.images.jpeg` (dependency-free dimension read),
:mod:`~leibniz.images.fetch` (download / verify / stats),
:mod:`~leibniz.images.cli` (``leibniz images``).
"""

from leibniz.images.fetch import fetch_images, image_stats, verify_images
from leibniz.images.pages import iter_page_images, populate_pages_from_cache

__all__ = [
    "fetch_images",
    "image_stats",
    "iter_page_images",
    "populate_pages_from_cache",
    "verify_images",
]
