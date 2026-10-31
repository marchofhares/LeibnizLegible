"""Enrich stage — language per page and per line, the per-page stratum heuristic.

Language identification: :mod:`leibniz.enrich.langid`, the stopword identifier
(K1), built for edition text; :mod:`leibniz.enrich.pagelang` runs it over every
page's machine text, measures it against the census's pieces and finds the
German pages (K4, Task 1; ``leibniz enrich page-lang``). The per-line
identification with a ``mixed`` label for code-switched lines and the per-page
stratum label derived from segmentation stats + katalog type — the field is
named ``stratum_heuristic`` on purpose, honesty in naming (SPECS §6) — are
C4's.
"""
