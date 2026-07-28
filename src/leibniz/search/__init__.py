"""Search stage — full-text index build.

Builds the typo-tolerant search index (Meilisearch via docker-compose; SQLite
FTS5 as the dev fallback behind the same interface). One document per page
(concatenated line text, ids, shelfmark, katalog refs, language mix, stratum,
mean confidence) plus a piece-level rollup where the crosswalk allows. Typo
tolerance is the point — CER-noisy text needs fuzzy match — with a synonyms
file for early-modern spelling variants (u/v, i/j, ſ/s).

Implemented in Phase D1.
"""
