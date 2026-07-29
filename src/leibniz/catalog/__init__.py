"""Katalog crosswalk stage — join the BBAW Ritter-Katalog to our works (Phase A3).

The Arbeitskatalog der Leibniz-Edition (https://leibniz-katalog.bbaw.de/, the
"Ritter-Katalog") is the metadata spine of the whole field: >70,200 records with
shelfmark, dating, correspondent, incipit, Akademie-Ausgabe volume/piece refs,
and — crucially — outbound links to the GWLB scans. This stage scrapes those
records (no public API), parses them into ``katalog_records``, and builds the
``crosswalk`` linking each record to our ``works``: primarily via the katalog's
own GWLB links, secondarily via normalized shelfmark strings.

Submodules: :mod:`~leibniz.catalog.shelfmarks` (robust signature normaliser),
:mod:`~leibniz.catalog.scrape` (polite scraper + row parser),
:mod:`~leibniz.catalog.crosswalk` (matcher), :mod:`~leibniz.catalog.report`
(``reports/crosswalk.md``), :mod:`~leibniz.catalog.cli` (``leibniz catalog``).
"""

# The katalog is CC BY 4.0 (covers database rights). Every export or surface that
# reuses its data must carry this attribution (SPECS §7.1). Stored here as the
# single source of truth so scraper, crosswalk, and future dataset cards agree.
KATALOG_ATTRIBUTION = (
    "Data from the Arbeitskatalog der Leibniz-Edition (Ritter-Katalog), "
    "Berlin-Brandenburgische Akademie der Wissenschaften (TELOTA), "
    "https://leibniz-katalog.bbaw.de/ — licensed CC BY 4.0."
)

__all__ = ["KATALOG_ATTRIBUTION"]
