"""Meilisearch backend against a fake server (httpx MockTransport)."""

from __future__ import annotations

import json

import httpx
import pytest

from leibniz import db
from leibniz.search.backend import SearchQuery
from leibniz.search.documents import iter_page_docs
from leibniz.search.meili import MeiliBackend, doc_id

W1 = "00068642"
W2 = "DE-611-HS-854976"


class FakeMeili:
    """Just enough of the Meilisearch HTTP API for rebuild/search/meta/count."""

    def __init__(self) -> None:
        self.indexes: dict[str, dict[str, dict]] = {}
        self.settings: dict[str, dict] = {}
        self.tasks = 0
        self.task_state: dict[int, dict] = {}
        self.calls: list[str] = []

    def _task(self, status: str = "succeeded", error: dict | None = None) -> httpx.Response:
        self.tasks += 1
        self.task_state[self.tasks] = {"uid": self.tasks, "status": status, "error": error}
        return httpx.Response(202, json={"taskUid": self.tasks, "status": "enqueued"})

    def handler(self, request: httpx.Request) -> httpx.Response:
        path, method = request.url.path, request.method
        self.calls.append(f"{method} {path}")
        assert request.headers.get("Authorization") == "Bearer secret"
        if path == "/health":
            return httpx.Response(200, json={"status": "available"})
        if path.startswith("/tasks/"):
            uid = int(path.rsplit("/", 1)[1])
            return httpx.Response(200, json=self.task_state[uid])
        if method == "DELETE" and path.startswith("/indexes/"):
            uid = path.split("/")[2]
            if uid not in self.indexes:
                # Meilisearch 1.x: the delete is a task, and it fails on a
                # missing index (a 404 was the pre-1.0 behaviour).
                return self._task(
                    "failed", {"code": "index_not_found", "message": f"Index `{uid}` not found."}
                )
            del self.indexes[uid]
            return self._task()
        if method == "POST" and path == "/indexes":
            self.indexes[json.loads(request.content)["uid"]] = {}
            return self._task()
        if method == "PATCH" and path.endswith("/settings"):
            self.settings[path.split("/")[2]] = json.loads(request.content)
            return self._task()
        if method == "POST" and path.endswith("/documents"):
            uid = path.split("/")[2]
            for d in json.loads(request.content):
                self.indexes[uid][d["doc_id"]] = d
            return self._task()
        if method == "POST" and path.endswith("/search"):
            uid = path.split("/")[2]
            body = json.loads(request.content)
            q = body["q"]
            hits = [d for d in self.indexes[uid].values() if q.split()[0] in d["folded"]]
            for f in body.get("filter", []):
                key, _, val = f.partition(" = ")
                if val:
                    hits = [d for d in hits if str(d.get(key)) == val.strip('"')]
                elif ">=" in f:
                    key, val = f.split(" >= ")
                    hits = [d for d in hits if (d.get(key) or 0) >= float(val)]
            return httpx.Response(
                200,
                json={
                    "hits": hits[body["offset"] : body["offset"] + body["limit"]],
                    "estimatedTotalHits": len(hits),
                    "processingTimeMs": 3,
                },
            )
        if method == "GET" and "/documents/" in path:
            uid, did = path.split("/")[2], path.rsplit("/", 1)[1]
            doc = self.indexes.get(uid, {}).get(did)
            return httpx.Response(200, json=doc) if doc else httpx.Response(404, json={})
        if method == "GET" and path.endswith("/stats"):
            uid = path.split("/")[2]
            if uid not in self.indexes:
                return httpx.Response(404, json={"code": "index_not_found"})
            return httpx.Response(200, json={"numberOfDocuments": len(self.indexes[uid])})
        return httpx.Response(500, json={"unexpected": path})


@pytest.fixture
def fake() -> FakeMeili:
    return FakeMeili()


def _backend(fake: FakeMeili) -> MeiliBackend:
    client = httpx.Client(base_url="http://meili.test", transport=httpx.MockTransport(fake.handler))
    return MeiliBackend("http://meili.test", "secret", client=client)


def test_doc_id() -> None:
    assert doc_id("00068642:0007") == "00068642_0007"


def test_rebuild_search_meta_count(store_path, fake) -> None:
    be = _backend(fake)
    conn = db.connect(store_path)
    n = be.rebuild(iter_page_docs(conn), meta={"stats": {"pages": 4}})
    conn.close()
    assert n == 3 and be.count() == 3
    # the first build on a fresh server: both deletes failed with index_not_found and were ignored
    failed = [t for t in fake.task_state.values() if t["status"] == "failed"]
    assert len(failed) == 2 and all(t["error"]["code"] == "index_not_found" for t in failed)
    # a second build (indexes exist now) deletes them for real
    conn = db.connect(store_path)
    assert be.rebuild(iter_page_docs(conn), meta={"stats": {"pages": 4}}) == 3
    conn.close()
    assert fake.settings["leibniz_pages"]["typoTolerance"]["enabled"] is True
    assert "POST /indexes" in fake.calls and "PATCH /indexes/leibniz_pages/settings" in fake.calls

    res = be.search(SearchQuery(q="Calculemus"))
    assert res.total == 1 and res.backend == "meili" and res.took_ms == 3
    assert res.hits[0].page_id == f"{W1}:0001" and "<mark>Calculemus</mark>" in res.hits[0].snippet
    assert be.search(SearchQuery(q="de", lang="fr")).total == 1
    assert be.search(SearchQuery(q="de", min_conf=0.85)).total == 1
    meta = be.meta()
    assert meta["n_docs"] == 3 and meta["stats"]["pages"] == 4 and "doc_id" not in meta
    assert be.health() is True


def test_unreachable_server_degrades_without_raising() -> None:
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    be = MeiliBackend(
        "http://meili.test",
        client=httpx.Client(base_url="http://meili.test", transport=httpx.MockTransport(refused)),
    )
    assert be.meta() == {} and be.count() == 0 and be.health() is False
    with pytest.raises(httpx.HTTPError):  # search itself still raises; the API maps it to 503
        be.search(SearchQuery(q="calculemus"))


def test_health_false_when_index_missing(fake) -> None:
    assert _backend(fake).health() is False  # server up, no index yet


def test_task_failure_raises(store_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/tasks/"):
            return httpx.Response(200, json={"status": "failed", "error": {"message": "boom"}})
        if request.method == "DELETE":
            return httpx.Response(404, json={})
        return httpx.Response(202, json={"taskUid": 1})

    be = MeiliBackend(
        "http://meili.test",
        client=httpx.Client(base_url="http://meili.test", transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(RuntimeError, match="boom"):
        be.rebuild([])
