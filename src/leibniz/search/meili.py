"""Meilisearch search backend (Phase D1) — the production index.

Spoken to over plain ``httpx`` (no SDK; the project's habit for thin clients):
an index of page documents with the folded text as the primary searchable
attribute, typo tolerance on, filters on set/language/stratum/confidence/work.
The build replaces the index wholesale (drop → create → settings → documents,
each awaited through Meilisearch's task queue) so re-indexing is idempotent.
``docker compose up -d meilisearch`` runs one locally (see ``docker-compose.yml``).
"""

from __future__ import annotations

import time
from collections.abc import Iterable

import httpx

from leibniz.search.backend import SearchHit, SearchQuery, SearchResult
from leibniz.search.documents import PageDoc
from leibniz.search.normalize import fold, query_terms
from leibniz.search.snippet import make_snippet

DEFAULT_MEILI_URL = "http://127.0.0.1:7700"
DEFAULT_INDEX_UID = "leibniz_pages"

SETTINGS = {
    "searchableAttributes": ["folded", "title", "shelfmarks", "aa_refs", "label"],
    "filterableAttributes": ["set_name", "lang", "stratum", "mean_conf", "work_id"],
    "sortableAttributes": ["mean_conf", "seq"],
    "typoTolerance": {"enabled": True, "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8}},
    "pagination": {"maxTotalHits": 10000},
}

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
    def _wait(self, resp: httpx.Response, *, timeout: float = 600.0) -> dict:
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
                if status != "succeeded":
                    raise RuntimeError(f"Meilisearch task {uid} {status}: {task.get('error')}")
                return task
            if time.monotonic() > deadline:
                raise TimeoutError(f"Meilisearch task {uid} still {status} after {timeout}s")
            time.sleep(0.2)

    @property
    def _meta_uid(self) -> str:
        return f"{self.index_uid}_meta"

    # -- build ------------------------------------------------------------- #
    def rebuild(
        self, docs: Iterable[PageDoc], *, meta: dict | None = None, batch: int = 2000
    ) -> int:
        for uid in (self.index_uid, self._meta_uid):
            r = self.client.delete(f"/indexes/{uid}")
            if r.status_code != 404:
                self._wait(r)
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
        f: list[str] = []
        if q.set_name:
            f.append(f'set_name = "{q.set_name}"')
        if q.lang:
            f.append(f'lang = "{q.lang}"')
        if q.stratum:
            f.append(f'stratum = "{q.stratum}"')
        if q.min_conf is not None:
            f.append(f"mean_conf >= {q.min_conf}")
        if q.work_id:
            f.append(f'work_id = "{q.work_id}"')
        return f

    def search(self, query: SearchQuery) -> SearchResult:
        q = query.normalized()
        t0 = time.perf_counter()
        terms = query_terms(q.q)
        if not terms:
            return SearchResult(q.q, 0, q.page, q.limit, 0, self.name, [])
        body = {
            "q": " ".join(terms),
            "limit": q.limit,
            "offset": q.offset,
            "attributesToRetrieve": RETRIEVE,
        }
        flt = self._filter(q)
        if flt:
            body["filter"] = flt
        r = self.client.post(f"/indexes/{self.index_uid}/search", json=body)
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
                snippet=make_snippet(h.get("text"), terms),
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
        return SearchResult(q.q, total, q.page, q.limit, took, self.name, hits)

    # -- introspection ----------------------------------------------------- #
    def meta(self) -> dict:
        r = self.client.get(f"/indexes/{self._meta_uid}/documents/meta")
        if r.status_code != 200:
            return {}
        d = r.json()
        d.pop("doc_id", None)
        return d

    def count(self) -> int:
        r = self.client.get(f"/indexes/{self.index_uid}/stats")
        if r.status_code != 200:
            return 0
        return int(r.json().get("numberOfDocuments", 0))


__all__ = ["DEFAULT_INDEX_UID", "DEFAULT_MEILI_URL", "SETTINGS", "MeiliBackend", "doc_id"]
