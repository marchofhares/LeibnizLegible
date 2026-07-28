"""Web stage — FastAPI service, frontend, and IIIF v3 annotations.

The thin serving layer (SPECS §4.1): a FastAPI app (``api.py``) exposing
``/search``, ``/works/{id}``, ``/pages/{id}``, ``/manifests/{id}``, and a
vanilla-TS/Vite frontend with an OpenSeadragon viewer that loads tiles
**directly from GWLB's IIIF Image API** — images are never rehosted or proxied.
``/manifests/{id}`` serves IIIF Presentation 3 manifests with W3C annotation
pages carrying our per-line transcriptions (deliverable D7). NC-derived text is
never displayed.

API in Phase D1; viewer + IIIF annotations in D2.
"""
