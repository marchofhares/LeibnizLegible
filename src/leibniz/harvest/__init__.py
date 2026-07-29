"""Harvest stage — OAI-PMH + IIIF → canonical inventory (Phase A1).

Populates ``works`` (from OAI-PMH ``ListRecords`` over the five GWLB Leibniz
sets, METS/MODS parsed for object id, shelfmark(s), title, manifest URL, and the
physical page count) and ``pages`` (from each work's IIIF Presentation manifest:
canvas seq/id, image-service URL, dimensions). Raw XML/JSON is cached under
``data/oai/`` and ``data/manifests/`` so parsing can be re-run offline.
Resumable, cache-first, polite (SPECS §7.4, enforced in :mod:`leibniz.net`).

Deliverable: ``reports/census.md`` — the first real page count.

Submodules: :mod:`~leibniz.harvest.oai`, :mod:`~leibniz.harvest.manifests`,
:mod:`~leibniz.harvest.shelfmarks`, :mod:`~leibniz.harvest.census`,
:mod:`~leibniz.harvest.cli`.
"""

from leibniz.harvest.census import compute_census, render_census
from leibniz.harvest.manifests import harvest_manifests, parse_manifest
from leibniz.harvest.oai import harvest_oai, parse_response

__all__ = [
    "compute_census",
    "harvest_manifests",
    "harvest_oai",
    "parse_manifest",
    "parse_response",
    "render_census",
]
