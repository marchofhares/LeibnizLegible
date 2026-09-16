"""Search-time text folding (Phase D1).

The index folds both the indexed text and the query onto the same lossy
alphabet the retro-aligner uses (:mod:`leibniz.align.normalize`): case,
diacritics, u≡v, i≡j, long-s, ligatures, the commonest Latin brevigraphs,
punctuation → space. Early-modern orthography varies freely on exactly these
axes (*vt* for *ut*, *ſed*, *Jesu*/*Iesu*), so folding at both ends is what lets
a query for *calculemus* find *Calculemus* and *calcvlemvs* alike; Meilisearch's
typo tolerance adds the rest (SPECS D1, "synonyms file for common early-modern
spelling variants (u/v, i/j, ſ/s) if the normalization doesn't already cover
them" — it does, at index time, for both backends).

The folded→original offset map from :func:`normalize_indexed` is what lets the
snippet renderer mark hits in the *original* text (:mod:`leibniz.search.snippet`).
Pure and offline.
"""

from __future__ import annotations

from leibniz.align.normalize import AlignNorm, normalize_indexed

# The aligner's recipe minus the struck-text elision: a search index must keep
# every word the machine read, struck or not (the deletion tokens exist for
# edition comparison only).
SEARCH_NORM = AlignNorm(name="search-fold", deletion_tokens=())

MAX_QUERY_TERMS = 12


def fold_indexed(text: str | None) -> tuple[str, list[int]]:
    """Fold ``text`` for indexing/matching, with the folded→original offset map."""
    return normalize_indexed(text or "", SEARCH_NORM)


def fold(text: str | None) -> str:
    """Folded form only."""
    return fold_indexed(text)[0]


def query_terms(query: str | None) -> list[str]:
    """Folded, de-duplicated query tokens (order kept; capped at :data:`MAX_QUERY_TERMS`)."""
    seen: set[str] = set()
    terms: list[str] = []
    for tok in fold(query).split():
        if tok and tok not in seen:
            seen.add(tok)
            terms.append(tok)
        if len(terms) >= MAX_QUERY_TERMS:
            break
    return terms


__all__ = ["MAX_QUERY_TERMS", "SEARCH_NORM", "fold", "fold_indexed", "query_terms"]
