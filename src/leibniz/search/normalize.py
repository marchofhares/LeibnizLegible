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

Folding turns every quotation mark and minus sign into a space, so the two
operators the search box offers are read off the raw query first
(:func:`parse_query`): ``"…"`` for words that must stand exactly so and in that
order, a leading ``-`` for words or phrases a page must not contain. Each word
and phrase is then folded on its own, so *vt* still finds *ut* inside quotes. A
query without either operator parses to exactly the words it always had.
Pure and offline.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from leibniz.align.normalize import AlignNorm, normalize_indexed

# The aligner's recipe minus the struck-text elision: a search index must keep
# every word the machine read, struck or not (the deletion tokens exist for
# edition comparison only).
SEARCH_NORM = AlignNorm(name="search-fold", deletion_tokens=())

MAX_QUERY_TERMS = 12

# What opens and closes a quoted phrase: the ASCII double quote and the
# typographic ones German („…“), English (“…”) and French («…», »…«) keyboards
# and phone autocorrect produce. No single quotes: ’ is also the apostrophe
# (*l’homme*).
QUOTE_CHARS = frozenset('"\u201c\u201d\u201e\u201f\u00ab\u00bb')


@dataclass(frozen=True, slots=True)
class ParsedQuery:
    """A query as the backends match it.

    ``words`` are the ordinary terms (typo-tolerant in Meilisearch, prefix-matched
    from three characters in FTS5); ``phrases`` are quoted runs of words that must
    stand exactly so and in this order (one quoted word is one exact word);
    ``excluded`` are the words and runs (``-word``, ``-"…"``) a page must not
    contain. All folded.
    """

    words: tuple[str, ...] = ()
    phrases: tuple[tuple[str, ...], ...] = ()
    excluded: tuple[tuple[str, ...], ...] = ()

    @property
    def searchable(self) -> bool:
        """There is something to look for; exclusions alone select nothing."""
        return bool(self.words or self.phrases)


def fold_indexed(text: str | None) -> tuple[str, list[int]]:
    """Fold ``text`` for indexing/matching, with the folded→original offset map."""
    return normalize_indexed(text or "", SEARCH_NORM)


def fold(text: str | None) -> str:
    """Folded form only."""
    return fold_indexed(text)[0]


def parse_query(query: str | None) -> ParsedQuery:
    """Read ``"phrases"`` and ``-exclusions`` off the raw query; fold everything.

    A quotation mark opens a phrase and the next one closes it; an unclosed
    phrase runs to the end. A ``-`` excludes only where it starts a word or a
    phrase (``-mundus``, ``-"anno 1676"``), so *Braunschweig-Lüneburg* and a
    free-standing dash read as they always did. A word that folds into several
    (``-Braunschweig-Lüneburg``) is excluded as the run it spells. Words and
    phrases are de-duplicated, order kept, and the clauses capped at
    :data:`MAX_QUERY_TERMS` with exclusions and phrases first in line.
    """
    # A control character (a NUL above all) is no letter of any query; FTS5
    # read a NUL inside a quoted token as the end of the string and answered
    # 500 (2026-10).
    text = "".join(
        " " if unicodedata.category(ch) == "Cc" and not ch.isspace() else ch for ch in (query or "")
    )
    words: list[str] = []
    phrases: list[tuple[str, ...]] = []
    excluded: list[tuple[str, ...]] = []
    i, n = 0, len(text)
    while i < n:
        if text[i].isspace():
            i += 1
            continue
        negate = text[i] == "-" and i + 1 < n and not text[i + 1].isspace()
        if negate:
            i += 1
        if text[i] in QUOTE_CHARS:
            end = i + 1
            while end < n and text[end] not in QUOTE_CHARS:
                end += 1
            run = tuple(fold(text[i + 1 : end]).split())
            if run:
                (excluded if negate else phrases).append(run)
            i = end + 1
            continue
        end = i
        while end < n and not text[end].isspace() and text[end] not in QUOTE_CHARS:
            end += 1
        tokens = tuple(fold(text[i:end]).split())
        if negate and tokens:
            excluded.append(tokens)
        elif not negate:
            words.extend(tokens)
        i = end
    excluded = _unique(excluded)[:MAX_QUERY_TERMS]
    phrases = _unique(phrases)[: MAX_QUERY_TERMS - len(excluded)]
    words = _unique(words)[: MAX_QUERY_TERMS - len(excluded) - len(phrases)]
    return ParsedQuery(tuple(words), tuple(phrases), tuple(excluded))


def _unique[T](items: list[T]) -> list[T]:
    """``items`` without repeats, first occurrence kept."""
    return list(dict.fromkeys(items))


def query_terms(query: str | None) -> list[str]:
    """The query's plain words: folded, de-duplicated, in order, capped (:func:`parse_query`)."""
    return list(parse_query(query).words)


__all__ = [
    "MAX_QUERY_TERMS",
    "QUOTE_CHARS",
    "SEARCH_NORM",
    "ParsedQuery",
    "fold",
    "fold_indexed",
    "parse_query",
    "query_terms",
]
