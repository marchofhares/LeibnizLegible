"""Search index + query layer (Phase D1, SPECS §3.3 / §4.1).

One document per recognised page (its lines concatenated, plus work, shelfmark,
folio label, katalog references and per-page aggregates), folded onto the
early-modern-tolerant comparison alphabet shared with the retro-aligner, behind
one small backend interface:

* :class:`leibniz.search.fts5.Fts5Backend` — SQLite FTS5, the dev/fallback
  backend (single file, no server; prefix matching on folded text);
* :class:`leibniz.search.meili.MeiliBackend` — Meilisearch over plain httpx
  (typo tolerance out of the box; the production backend, SPECS §4.2).

Both build from the canonical store with :func:`leibniz.search.documents.iter_page_docs`
and answer :class:`leibniz.search.backend.SearchQuery` with the same
:class:`leibniz.search.backend.SearchResult`, so the API and the CLI never know
which one is behind them.
"""

from __future__ import annotations

from leibniz.search.backend import SearchBackend, SearchHit, SearchQuery, SearchResult

__all__ = ["SearchBackend", "SearchHit", "SearchQuery", "SearchResult", "open_backend"]


def open_backend(
    kind: str,
    *,
    path: str | None = None,
    meili_url: str | None = None,
    meili_key: str | None = None,
) -> SearchBackend:
    """Instantiate a backend by name (``fts5`` or ``meili``)."""
    if kind == "fts5":
        from leibniz.search.fts5 import DEFAULT_INDEX_PATH, Fts5Backend

        return Fts5Backend(path or DEFAULT_INDEX_PATH)
    if kind == "meili":
        from leibniz.search.meili import DEFAULT_MEILI_URL, MeiliBackend

        return MeiliBackend(meili_url or DEFAULT_MEILI_URL, meili_key)
    raise ValueError(f"unknown search backend {kind!r} (expected 'fts5' or 'meili')")
