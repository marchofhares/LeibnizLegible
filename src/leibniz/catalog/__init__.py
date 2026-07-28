"""Catalog stage — BBAW Ritter-Katalog ingestion + crosswalk.

Ingests the Arbeitskatalog der Leibniz-Edition (https://leibniz-katalog.bbaw.de/,
>70,200 records, CC BY 4.0 — attribute BBAW/TELOTA) into ``katalog_records``,
either from a TELOTA data dump or a polite scraper (raw HTML cached under
``data/katalog/``). Builds ``crosswalk`` joining records to ``works`` via the
katalog's outbound GWLB links (primary) and normalized LH/LBr shelfmark strings
(secondary), storing match method + confidence.

Implemented in Phase A3.
"""
