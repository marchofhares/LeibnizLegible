"""Harvest stage — OAI-PMH + IIIF → canonical inventory.

Populates ``works`` (from OAI-PMH ListRecords over the GWLB sets, METS/MODS
parsed for object id, shelfmark(s), title, manifest URL) and ``pages`` (from
each work's IIIF Presentation manifest: canvas seq/id, image-service URL,
dimensions). Raw XML/JSON is cached under ``data/oai/`` and ``data/manifests/``
so parsing can be re-run offline. Resumable, cache-first, polite (SPECS §7.4).

Implemented in Phase A1.
"""
