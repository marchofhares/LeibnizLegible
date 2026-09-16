"""``leibniz index bench`` — search latency against a running server.

SPECS §3.3 sets the bar: **p95 under 500 ms** for typo-tolerant full-text
search. This measures it the way a user meets it — over HTTP, through the
whole path (proxy, app, backend, snippet rendering) — and reports the backend's
own ``took_ms`` beside the wall clock so a slow proxy or a slow store shows up
as the difference. The built-in query list mixes Latin, French and German
vocabulary from the Nachlass, names, and a few deliberate misspellings for the
typo tolerance; pass ``--queries`` for a list drawn from real search logs.
"""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

import httpx

P95_CRITERION_MS = 500
DEFAULT_RATE = 8.0  # launches per second — under the app's default per-client limit of 10/s

DEFAULT_QUERIES: tuple[str, ...] = (
    "calculemus",
    "monade",
    "harmonia praestabilita",
    "characteristica universalis",
    "scientia generalis",
    "ars combinatoria",
    "infinitesimal",
    "differentialis",
    "calculus",
    "dynamica",
    "vis viva",
    "substantia",
    "veritas",
    "ratio sufficiens",
    "Deus optimus",
    "Newton",
    "Bernoulli",
    "Arnauld",
    "Spinoza",
    "Descartes",
    "Malebranche",
    "Huygens",
    "Oldenburg",
    "Hobbes",
    "Bayle",
    "Locke",
    "Clarke",
    "Bossuet",
    "Sophie Charlotte",
    "Hannover",
    "Wolfenbüttel",
    "Braunschweig",
    "Bibliothek",
    "Bergwerk",
    "Harz",
    "Rechenmaschine",
    "dyadica",
    "China",
    "lingua",
    "historia",
    "jus naturae",
    "Theodicée",
    "principes de la nature",
    "la raison",
    "gnädigster Herr",
    "Durchlaucht",
    # misspellings and old orthography — what the typo tolerance is for
    "calculemvs",
    "monadologie",
    "Leibnitz",
    "Newtonus",
)


def percentiles(samples: Sequence[float]) -> dict[str, float]:
    """``p50``/``p95``/``max`` by nearest rank (``0.0`` for no samples)."""
    if not samples:
        return {"p50": 0.0, "p95": 0.0, "max": 0.0}
    s = sorted(samples)

    def rank(p: float) -> float:
        return s[max(0, min(len(s) - 1, math.ceil(p / 100.0 * len(s)) - 1))]

    return {"p50": round(rank(50), 1), "p95": round(rank(95), 1), "max": round(s[-1], 1)}


def bench_search(
    client: httpx.Client,
    queries: Sequence[str] = DEFAULT_QUERIES,
    *,
    n: int = 200,
    limit: int = 20,
    concurrency: int = 1,
    rate: float = DEFAULT_RATE,
) -> dict:
    """Run ``n`` searches (cycling through ``queries``) and report latency percentiles.

    ``client`` is any :class:`httpx.Client` whose base URL is the server (a
    Starlette ``TestClient`` works too). Launches are paced to ``rate`` per
    second (``0`` = as fast as possible), because the app itself limits a
    client to 10 requests/second by default and an unpaced run would mostly
    measure its own ``429``s; those are counted apart as ``rate_limited`` and
    never enter the percentiles. Returns wall-clock and backend percentiles in
    milliseconds, the counts, and ``pass`` against :data:`P95_CRITERION_MS`
    (no transport/server errors, p95 under the bar).
    """
    qs = [q.strip() for q in queries if q and q.strip()] or list(DEFAULT_QUERIES)
    n = max(1, int(n))
    concurrency = max(1, int(concurrency))
    interval = 1.0 / rate if rate and rate > 0 else 0.0
    start = time.perf_counter()

    def one(i: int) -> tuple[float | None, int | None, str]:
        if interval:
            delay = start + i * interval - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
        t0 = time.perf_counter()
        try:
            r = client.get("/api/search", params={"q": qs[i % len(qs)], "limit": limit})
        except httpx.HTTPError:
            return None, None, "error"
        ms = (time.perf_counter() - t0) * 1000.0
        if r.status_code == 429:
            return None, None, "limited"
        if r.status_code != 200:
            return None, None, "error"
        try:
            took = int(r.json().get("took_ms") or 0)
        except (ValueError, AttributeError):
            took = 0
        return ms, took, "ok"

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(one, range(n)))
    wall = [w for w, _, k in results if k == "ok" and w is not None]
    took = [t for _, t, k in results if k == "ok" and t is not None]
    limited = sum(1 for _, _, k in results if k == "limited")
    errors = sum(1 for _, _, k in results if k == "error")
    p = percentiles(wall)
    return {
        "n": n,
        "ok": len(wall),
        "errors": errors,
        "rate_limited": limited,
        "concurrency": concurrency,
        "rate": rate,
        "queries": len(qs),
        "wall_ms": p,
        "backend_ms": percentiles(took),
        "criterion_p95_ms": P95_CRITERION_MS,
        "pass": bool(wall) and errors == 0 and p["p95"] < P95_CRITERION_MS,
    }


__all__ = ["DEFAULT_QUERIES", "DEFAULT_RATE", "P95_CRITERION_MS", "bench_search", "percentiles"]
