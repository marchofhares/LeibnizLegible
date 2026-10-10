"""Meilisearch backend against a fake server (httpx MockTransport)."""

from __future__ import annotations

import json
import random

import httpx
import pytest

from leibniz import db
from leibniz.search.backend import SearchQuery
from leibniz.search.documents import iter_page_docs
from leibniz.search.meili import MeiliBackend, doc_id, meili_query
from leibniz.search.normalize import parse_query

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
        self.searches: list[dict] = []
        self.swaps = 0

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
        if method == "GET" and path.startswith("/indexes/") and path.count("/") == 2:
            uid = path.split("/")[2]
            return httpx.Response(200 if uid in self.indexes else 404, json={"uid": uid})
        if method == "POST" and path == "/swap-indexes":
            for pair in json.loads(request.content):
                a, b = pair["indexes"]
                assert a in self.indexes and b in self.indexes, pair  # as Meilisearch requires
                self.indexes[a], self.indexes[b] = self.indexes[b], self.indexes[a]
                sa, sb = self.settings.get(a), self.settings.get(b)
                self.settings.pop(a, None)
                self.settings.pop(b, None)
                if sb is not None:
                    self.settings[a] = sb
                if sa is not None:
                    self.settings[b] = sa
            self.swaps += 1
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
            self.searches.append(body)
            for f in body.get("filter", []):
                if f.count('"') % 2:
                    return httpx.Response(
                        400, json={"code": "invalid_search_filter", "message": "bad filter"}
                    )
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
            docs = self.indexes[uid].values()
            fields: dict[str, int] = {}
            for d in docs:
                for k in d:
                    fields[k] = fields.get(k, 0) + 1
            return httpx.Response(
                200, json={"numberOfDocuments": len(self.indexes[uid]), "fieldDistribution": fields}
            )
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
    # the first build on a fresh server: the deletes of a leftover build pair
    # failed with index_not_found and were ignored
    failed = [t for t in fake.task_state.values() if t["status"] == "failed"]
    assert len(failed) == 2 and all(t["error"]["code"] == "index_not_found" for t in failed)
    # a second build swaps a new generation in
    conn = db.connect(store_path)
    assert be.rebuild(iter_page_docs(conn), meta={"stats": {"pages": 4}}) == 3
    conn.close()
    assert fake.settings["leibniz_pages"]["typoTolerance"]["enabled"] is True
    # the settings go to the index being built; the swap carries them live
    assert "POST /indexes" in fake.calls
    assert "PATCH /indexes/leibniz_pages__next/settings" in fake.calls

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


def test_operators_reach_meilisearch_first(store_path, fake) -> None:
    be = _backend(fake)
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    be.search(SearchQuery(q="Calculemus inquit"))
    be.search(SearchQuery(q='de -"la nature" „arte combinatoria“ Calculemus -grâce'))
    assert [s["q"] for s in fake.searches] == [
        "calculemus inquit",  # without operators: exactly as before
        '-"la nature" -grace "arte combinatoria" de calculemus',  # exclusions, phrases, words
    ]
    assert be.search(SearchQuery(q="-de")).total == 0
    assert len(fake.searches) == 2  # exclusions alone: nothing is sent


def test_meili_query_is_well_formed() -> None:
    """Folded words carry no quotes or minus signs, so whatever is typed, the only
    syntax in ``q`` is the syntax :func:`meili_query` adds."""
    rng = random.Random(1700)
    pieces = list("abde \"“”„«»-*:(),.;'’&\\/") + ["-de", '"la', "q;"]
    for _ in range(3000):
        typed = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 14)))
        parsed = parse_query(typed)
        if not parsed.searchable:
            continue
        q = meili_query(parsed)
        assert q.count('"') % 2 == 0 and '""' not in q, typed
        assert all(i == 0 or q[i - 1] == " " for i, c in enumerate(q) if c == "-"), typed
        terms = len(parsed.excluded) + len(parsed.phrases) + len(parsed.words)
        assert terms <= 12, typed


def test_words_must_all_match_unless_any_is_asked(store_path, fake) -> None:
    be = _backend(fake)
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    res = be.search(SearchQuery(q="Calculemus inquit"))
    assert fake.searches[-1]["matchingStrategy"] == "all" and res.match == "all"
    res = be.search(SearchQuery(q="Calculemus inquit", match="any"))
    assert fake.searches[-1]["matchingStrategy"] == "last" and res.match == "any"
    assert be.search(SearchQuery(q="x", match="bogus")).match == "all"


def test_metadata_is_folded_like_the_query(store_path, fake) -> None:
    """A title, shelfmark or AA reference is searched folded: "VI" meets "ui"."""
    be = _backend(fake)
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    doc = fake.indexes["leibniz_pages"][doc_id(f"{W1}:0001")]
    # "AA VI,4 N. 109", the title of the piece on this folio, folio 1r
    assert doc["meta_folded"].endswith(
        "aa ui 4 n 109 praefatio operis ad instaurationem scientiarum fol 1r"
    )
    assert fake.settings["leibniz_pages"]["searchableAttributes"] == ["folded", "meta_folded"]


def test_filter_values_are_checked_and_refusals_are_query_errors(store_path, fake) -> None:
    from leibniz.search.backend import SearchQueryError

    be = _backend(fake)
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    with pytest.raises(SearchQueryError, match="not a valid work_id"):
        be.search(SearchQuery(q="de", work_id='x" OR set_name = "y'))
    assert be.search(SearchQuery(q="de", work_id=W2)).total == 1
    # a refusal from the server (a 4xx) is the query's fault, not an outage
    be._filter = staticmethod(lambda q: ['work_id = "unbalanced'])  # type: ignore[method-assign]
    with pytest.raises(SearchQueryError, match="bad filter"):
        be.search(SearchQuery(q="de"))


def test_settings_push_refuses_an_index_built_without_the_fields(store_path, fake) -> None:
    be = _backend(fake)
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    assert be.push_settings()["status"] == "succeeded"
    for d in fake.indexes["leibniz_pages"].values():
        d.pop("meta_folded")
    with pytest.raises(RuntimeError, match="no field meta_folded"):
        be.push_settings()


def test_a_rebuild_fills_a_second_index_and_swaps_it_in(store_path, fake) -> None:
    """The live index answers throughout: the documents go into ``__next`` and
    one swap puts them live; the old generation is deleted after."""
    be = _backend(fake)
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))  # the first build: nothing live yet
    assert set(fake.indexes) == {"leibniz_pages", "leibniz_pages_meta"} and fake.swaps == 1
    assert len(fake.indexes["leibniz_pages"]) == 3
    fake.calls.clear()
    be.rebuild(iter_page_docs(conn, work_id=W2))  # a second build
    conn.close()
    assert fake.swaps == 2 and len(fake.indexes["leibniz_pages"]) == 1
    assert set(fake.indexes) == {"leibniz_pages", "leibniz_pages_meta"}
    # the live index was never deleted, and no document went into it directly
    assert "DELETE /indexes/leibniz_pages" not in fake.calls
    assert "POST /indexes/leibniz_pages/documents" not in fake.calls
    assert fake.settings["leibniz_pages"]["searchableAttributes"] == ["folded", "meta_folded"]
