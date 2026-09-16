"""`leibniz index bench` — latency percentiles over HTTP (here: the TestClient)."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.search.bench import DEFAULT_QUERIES, P95_CRITERION_MS, bench_search, percentiles
from leibniz.search.documents import iter_page_docs
from leibniz.search.fts5 import Fts5Backend
from leibniz.web.api import create_app


def _client(store_path, tmp_path, *, search: bool = True) -> TestClient:
    be = None
    if search:
        be = Fts5Backend(tmp_path / "search.sqlite")
        conn = db.connect(store_path)
        be.rebuild(iter_page_docs(conn))
        conn.close()
    return TestClient(create_app(store_path, search=be, static_dir=None))


def test_percentiles_nearest_rank() -> None:
    assert percentiles([]) == {"p50": 0.0, "p95": 0.0, "max": 0.0}
    assert percentiles([float(i) for i in range(1, 11)]) == {"p50": 5.0, "p95": 10.0, "max": 10.0}
    assert percentiles([3.0])["p95"] == 3.0


def test_bench_reports_and_passes(store_path, tmp_path) -> None:
    res = bench_search(
        _client(store_path, tmp_path), ["calculemus", "monade"], n=6, concurrency=2, rate=0
    )
    assert res["n"] == 6 and res["ok"] == 6 and res["errors"] == 0 and res["queries"] == 2
    assert res["rate_limited"] == 0 and res["rate"] == 0
    assert res["criterion_p95_ms"] == P95_CRITERION_MS and res["pass"] is True
    assert res["wall_ms"]["p95"] >= res["wall_ms"]["p50"] >= 0.0
    assert len(DEFAULT_QUERIES) >= 40 and all(q.strip() for q in DEFAULT_QUERIES)


def test_bench_counts_errors(store_path, tmp_path) -> None:
    res = bench_search(_client(store_path, tmp_path, search=False), n=3, rate=0)  # 503: no index
    assert res["ok"] == 0 and res["errors"] == 3 and res["pass"] is False


def test_bench_paces_and_counts_429_apart(store_path, tmp_path) -> None:
    be = Fts5Backend(tmp_path / "search.sqlite")
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    limited = TestClient(
        create_app(store_path, search=be, static_dir=None, rate_limit=1, rate_burst=2)
    )
    res = bench_search(limited, ["calculemus"], n=4, rate=0)  # burst of 2, then 429s
    assert res["ok"] == 2 and res["rate_limited"] == 2 and res["errors"] == 0
    assert res["pass"] is True  # the criterion is about latency; 429s are reported, not failures
    t0 = time.perf_counter()
    paced = bench_search(_client(store_path, tmp_path), ["monade"], n=4, rate=20)
    assert paced["ok"] == 4 and time.perf_counter() - t0 >= 3 / 20  # launches 0.05 s apart
