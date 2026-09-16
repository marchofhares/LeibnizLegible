"""The serving layer (Phases D1/D2): a FastAPI JSON API, IIIF Presentation 3
manifests + W3C annotation pages carrying the transcriptions (deliverable D7),
and the static viewer under ``static/`` (vanilla ES modules, no build step).

``leibniz serve`` runs it; :func:`leibniz.web.api.create_app` builds it for
tests. Images are never proxied or rehosted — the viewer and the manifests
point at the GWLB's own image services (SPECS §3.4).
"""

from __future__ import annotations
