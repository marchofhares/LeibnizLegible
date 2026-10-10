"""Meilisearch search backend (Phase D1) — the production index.

Spoken to over plain ``httpx`` (no SDK; the project's habit for thin clients):
an index of page documents with the folded text as the primary searchable
attribute, typo tolerance on, filters on set/language/stratum/confidence/work.
The build replaces the index wholesale (drop → create → settings → documents,
each awaited through Meilisearch's task queue) so re-indexing is idempotent.
``docker compose up -d meilisearch`` runs one locally (see ``docker-compose.yml``).
Quoted phrases and exclusions use Meilisearch's own ``"…"`` and ``-`` syntax
(exclusions need Meilisearch ≥ 1.8); see :func:`meili_query` for the order.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable

import httpx

from leibniz.search.backend import (
    MAX_REACHABLE,
    SearchHit,
    SearchQuery,
    SearchQueryError,
    SearchResult,
)
from leibniz.search.documents import PageDoc
from leibniz.search.normalize import ParsedQuery, fold, parse_query
from leibniz.search.snippet import make_snippet

DEFAULT_MEILI_URL = "http://127.0.0.1:7700"
DEFAULT_INDEX_UID = "leibniz_pages"

SETTINGS = {
    # the text, then what names the page (title, shelfmarks, AA references,
    # folio), both folded the same way as the query (PageDoc.meta_text)
    "searchableAttributes": ["folded", "meta_folded"],
    "filterableAttributes": ["set_name", "lang", "stratum", "mean_conf", "work_id"],
    "sortableAttributes": ["mean_conf", "seq"],
    # "exactness" before proximity: the word as typed outranks a word it is the
    # beginning of — "monas" before "Monasteris" (Meilisearch's default order
    # ranks exactness last, behind proximity and attribute).
    "rankingRules": ["words", "typo", "exactness", "proximity", "attribute", "sort"],
    "typoTolerance": {"enabled": True, "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8}},
    "pagination": {"maxTotalHits": MAX_REACHABLE},
}

# Values that reach a filter expression only ever come from these shapes: a set
# name (letters and hyphens), a work id (8 digits, or DE-611-HS-…).
_FILTER_SAFE = {"set_name": r"[A-Za-z][A-Za-z0-9_-]*", "work_id": r"[A-Za-z0-9][A-Za-z0-9_-]*"}

RETRIEVE = [
    "page_id",
    "work_id",
    "seq",
    "label",
    "set_name",
    "title",
    "shelfmarks",
    "n_lines",
    "mean_conf",
    "lang",
    "stratum",
    "thumb_url",
    "text",
]


def doc_id(page_id: str) -> str:
    """Meilisearch primary keys allow only ``[A-Za-z0-9_-]``; page ids carry ``:``."""
    return page_id.replace(":", "_")


def meili_query(query: ParsedQuery) -> str:
    """The ``q`` Meilisearch is sent: exclusions (``-word``, ``-"a b"``), then
    ``"phrases"``, then the plain words exactly as before.

    The order is load-bearing: Meilisearch reads only the first ten terms of a
    query (a phrase or an exclusion is one) and matches the last word as a
    prefix, so operators placed after the words could be dropped and would
    cost the last word its prefix match. Folded tokens carry no quotes or
    minus signs, so the syntax added here is the only syntax in ``q``.
    """
    parts = [f'-"{" ".join(p)}"' if len(p) > 1 else f"-{p[0]}" for p in query.excluded]
    parts += [f'"{" ".join(p)}"' for p in query.phrases]
    parts += query.words
    return " ".join(parts)


class MeiliBackend:
    name = "meili"

    def __init__(
        self,
        url: str = DEFAULT_MEILI_URL,
        key: str | None = None,
        *,
        index_uid: str = DEFAULT_INDEX_UID,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.index_uid = index_uid
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        self.client = client or httpx.Client(base_url=self.url, headers=headers, timeout=timeout)
        if client is not None and key:
            self.client.headers["Authorization"] = f"Bearer {key}"

    # -- task helpers ------------------------------------------------------ #
    def _wait(
        self, resp: httpx.Response, *, timeout: float = 600.0, ignore: tuple[str, ...] = ()
    ) -> dict:
        """Await the task ``resp`` enqueued; raise unless it succeeded or failed
        with an error code in ``ignore``."""
        resp.raise_for_status()
        body = resp.json()
        uid = body.get("taskUid", body.get("uid"))
        if uid is None:
            return body
        deadline = time.monotonic() + timeout
        while True:
            task = self.client.get(f"/tasks/{uid}").json()
            status = task.get("status")
            if status in ("succeeded", "failed", "canceled"):
                if status == "failed" and (task.get("error") or {}).get("code") in ignore:
                    return task
                if status != "succeeded":
                    raise RuntimeError(f"Meilisearch task {uid} {status}: {task.get('error')}")
                return task
            if time.monotonic() > deadline:
                raise TimeoutError(f"Meilisearch task {uid} still {status} after {timeout}s")
            time.sleep(0.2)

    @property
    def _meta_uid(self) -> str:
        return f"{self.index_uid}_meta"

    def push_settings(self) -> dict:
        """Apply :data:`SETTINGS` to the live index without rebuilding it — enough
        for a ranking or a typo rule; a new document field needs :meth:`rebuild`.

        Refuses when the index's documents lack a field the settings search:
        pushed onto an index built before ``meta_folded`` existed, they would
        stop titles and shelfmarks from matching until the next rebuild.
        """
        r = self.client.get(f"/indexes/{self.index_uid}/stats")
        r.raise_for_status()
        fields = r.json().get("fieldDistribution") or {}
        missing = [a for a in SETTINGS["searchableAttributes"] if a not in fields]
        if missing:
            raise RuntimeError(
                f"index {self.index_uid} has no field {', '.join(missing)}: rebuild it "
                "(`leibniz index build`), which applies the settings as well"
            )
        return self._wait(self.client.patch(f"/indexes/{self.index_uid}/settings", json=SETTINGS))

    # -- build ------------------------------------------------------------- #
    def rebuild(
        self, docs: Iterable[PageDoc], *, meta: dict | None = None, batch: int = 2000
    ) -> int:
        for uid in (self.index_uid, self._meta_uid):
            # Deleting an index is a task; on a fresh server (first build) that
            # task fails with index_not_found, which is exactly what we want.
            r = self.client.delete(f"/indexes/{uid}")
            if r.status_code != 404:
                self._wait(r, ignore=("index_not_found",))
            self._wait(self.client.post("/indexes", json={"uid": uid, "primaryKey": "doc_id"}))
        self._wait(self.client.patch(f"/indexes/{self.index_uid}/settings", json=SETTINGS))
        n = 0
        pending: list[dict] = []

        def flush() -> None:
            nonlocal n
            if not pending:
                return
            self._wait(self.client.post(f"/indexes/{self.index_uid}/documents", json=pending))
            n += len(pending)
            pending.clear()

        for d in docs:
            row = d.to_dict()
            row["doc_id"] = doc_id(d.page_id)
            row["folded"] = fold(d.text)
            row["meta_folded"] = fold(d.meta_text())
            pending.append(row)
            if len(pending) >= batch:
                flush()
        flush()
        info = dict(meta or {})
        info.update(
            {
                "doc_id": "meta",
                "backend": self.name,
                "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "n_docs": n,
            }
        )
        self._wait(self.client.post(f"/indexes/{self._meta_uid}/documents", json=[info]))
        return n

    # -- query ------------------------------------------------------------- #
    @staticmethod
    def _filter(q: SearchQuery) -> list[str]:
        """The filter clauses, every value checked and quoted: a quote in a set
        name or a work id once rewrote the expression, and Meilisearch's refusal
        came back as "search backend unavailable" (2026-10)."""
        f: list[str] = []
        if q.set_name:
            f.append(f"set_name = {_quoted('set_name', q.set_name)}")
        if q.lang:
            f.append(f"lang = {_quoted('lang', q.lang)}")
        if q.stratum:
            f.append(f"stratum = {_quoted('stratum', q.stratum)}")
        if q.min_conf is not None:
            f.append(f"mean_conf >= {float(q.min_conf)}")
        if q.work_id:
            f.append(f"work_id = {_quoted('work_id', q.work_id)}")
        return f

    def search(self, query: SearchQuery) -> SearchResult:
        q = query.normalized()
        t0 = time.perf_counter()
        parsed = parse_query(q.q)
        if not parsed.searchable:
            return SearchResult(q.q, 0, q.page, q.limit, 0, self.name, [])
        body = {
            "q": meili_query(parsed),
            "limit": q.limit,
            "offset": q.offset,
            "attributesToRetrieve": RETRIEVE,
            # "last" drops words from the end when results run short: the
            # broader net, offered as match=any
            "matchingStrategy": "all" if q.match == "all" else "last",
        }
        flt = self._filter(q)
        if flt:
            body["filter"] = flt
        r = self.client.post(f"/indexes/{self.index_uid}/search", json=body)
        if 400 <= r.status_code < 500:
            try:
                message = r.json().get("message")
            except ValueError:
                message = None
            refused = f"the search index refused the query ({r.status_code})"
            raise SearchQueryError(message or refused)
        r.raise_for_status()
        data = r.json()
        hits = [
            SearchHit(
                page_id=h["page_id"],
                work_id=h["work_id"],
                seq=h["seq"],
                label=h.get("label"),
                set_name=h["set_name"],
                title=h.get("title"),
                shelfmarks=list(h.get("shelfmarks") or []),
                snippet=make_snippet(h.get("text"), list(parsed.words), phrases=parsed.phrases),
                n_lines=h.get("n_lines", 0),
                mean_conf=h.get("mean_conf"),
                lang=h.get("lang", "unknown"),
                stratum=h.get("stratum", "unknown"),
                thumb_url=h.get("thumb_url"),
                score=h.get("_rankingScore"),
            )
            for h in data.get("hits", [])
        ]
        total = int(data.get("estimatedTotalHits", data.get("totalHits", len(hits))))
        took = int(data.get("processingTimeMs", (time.perf_counter() - t0) * 1000))
        return SearchResult(q.q, total, q.page, q.limit, took, self.name, hits, match=q.match)

    # -- introspection ----------------------------------------------------- #
    def meta(self) -> dict:
        """Build metadata, or ``{}`` when the index is absent or the server unreachable."""
        try:
            r = self.client.get(f"/indexes/{self._meta_uid}/documents/meta")
        except httpx.HTTPError:
            return {}
        if r.status_code != 200:
            return {}
        d = r.json()
        d.pop("doc_id", None)
        return d

    def count(self) -> int:
        try:
            r = self.client.get(f"/indexes/{self.index_uid}/stats")
        except httpx.HTTPError:
            return 0
        if r.status_code != 200:
            return 0
        return int(r.json().get("numberOfDocuments", 0))

    def health(self) -> bool:
        """Meilisearch answers ``/health`` (no key needed) and the index exists."""
        try:
            if self.client.get("/health", timeout=3.0).status_code != 200:
                return False
            return (
                self.client.get(f"/indexes/{self.index_uid}/stats", timeout=3.0).status_code == 200
            )
        except httpx.HTTPError:
            return False


def _quoted(field_name: str, value: str) -> str:
    """A filter value, checked against its field's shape and quoted for Meilisearch."""
    shape = _FILTER_SAFE.get(field_name)
    if shape is not None and re.fullmatch(shape, value) is None:
        raise SearchQueryError(f"not a valid {field_name}: {value!r}")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


__all__ = [
    "DEFAULT_INDEX_UID",
    "DEFAULT_MEILI_URL",
    "SETTINGS",
    "MeiliBackend",
    "doc_id",
    "meili_query",
]
