"""The search backend contract (Phase D1): one query shape, one result shape.

The API (:mod:`leibniz.web.api`) and the CLI talk to a :class:`SearchBackend`
only; :mod:`leibniz.search.fts5` and :mod:`leibniz.search.meili` implement it.
Snippets are rendered by :mod:`leibniz.search.snippet` from the stored original
text so both backends return identical hit records.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Protocol

from leibniz.db import GT_STRATA, LINE_LANGS
from leibniz.search.documents import PageDoc

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass(slots=True)
class SearchQuery:
    """A search request: the query string plus the D1 filters."""

    q: str = ""
    set_name: str | None = None
    lang: str | None = None
    stratum: str | None = None
    min_conf: float | None = None
    work_id: str | None = None
    page: int = 1
    limit: int = DEFAULT_LIMIT

    def normalized(self) -> SearchQuery:
        """Clamp paging and drop filter values outside the known vocabularies."""
        page = max(1, int(self.page or 1))
        limit = max(1, min(MAX_LIMIT, int(self.limit or DEFAULT_LIMIT)))
        lang = self.lang if self.lang in LINE_LANGS else None
        stratum = self.stratum if self.stratum in GT_STRATA else None
        min_conf = None
        if self.min_conf is not None:
            min_conf = max(0.0, min(1.0, float(self.min_conf)))
        return SearchQuery(
            q=(self.q or "").strip(),
            set_name=(self.set_name or None),
            lang=lang,
            stratum=stratum,
            min_conf=min_conf,
            work_id=(self.work_id or None),
            page=page,
            limit=limit,
        )

    @property
    def offset(self) -> int:
        return (max(1, self.page) - 1) * max(1, self.limit)


@dataclass(slots=True)
class SearchHit:
    """One page hit, as the API returns it (``snippet`` is the only HTML)."""

    page_id: str
    work_id: str
    seq: int
    label: str | None
    set_name: str
    title: str | None
    shelfmarks: list[str]
    snippet: str
    n_lines: int
    mean_conf: float | None
    lang: str
    stratum: str
    thumb_url: str | None
    score: float | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["set"] = d.pop("set_name")
        return d


@dataclass(slots=True)
class SearchResult:
    query: str
    total: int
    page: int
    limit: int
    took_ms: int
    backend: str
    hits: list[SearchHit] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "total": self.total,
            "page": self.page,
            "limit": self.limit,
            "took_ms": self.took_ms,
            "backend": self.backend,
            "hits": [h.to_dict() for h in self.hits],
        }


class SearchBackend(Protocol):
    """What the API needs from an index."""

    name: str

    def rebuild(self, docs: Iterable[PageDoc], *, meta: dict | None = None) -> int:
        """Replace the index with ``docs``; return the number indexed."""

    def search(self, query: SearchQuery) -> SearchResult: ...

    def meta(self) -> dict:
        """Build-time metadata (built_at, n_docs, corpus stats …) or ``{}``."""

    def count(self) -> int: ...


__all__ = [
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "SearchBackend",
    "SearchHit",
    "SearchQuery",
    "SearchResult",
]
