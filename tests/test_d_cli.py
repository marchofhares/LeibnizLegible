"""CLI-level tests for `leibniz index`, `leibniz release`, `leibniz serve --check`."""

from __future__ import annotations

import json

import httpx
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app
from leibniz.search.documents import iter_page_docs
from leibniz.search.fts5 import Fts5Backend
from leibniz.web.api import create_app

runner = CliRunner()


def test_help_lists_new_groups() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("index", "release", "serve"):
        assert name in result.stdout


def test_index_build_status_query(store_path, tmp_path) -> None:
    index = tmp_path / "search.sqlite"
    r = runner.invoke(app, ["index", "build", "--db", str(store_path), "--index", str(index)])
    assert r.exit_code == 0, r.stdout
    assert "Indexed 3 pages" in r.stdout
    r = runner.invoke(app, ["index", "status", "--index", str(index)])
    assert r.exit_code == 0 and "documents: 3" in r.stdout and "2 works" in r.stdout
    r = runner.invoke(app, ["index", "query", "calculemus", "--index", str(index)])
    assert r.exit_code == 0 and "1 hits" in r.stdout


def _fake_meili(seen: list[str]):
    """A Meilisearch that answers just enough for a build and a status call,
    recording every path it is asked for."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        seen.append(f"{request.method} {path}")
        if path.startswith("/tasks/"):
            return httpx.Response(200, json={"uid": 1, "status": "succeeded"})
        if path.endswith("/documents/meta"):
            return httpx.Response(200, json={"doc_id": "meta", "n_docs": 3, "built_at": "now"})
        if path.endswith("/stats"):
            return httpx.Response(200, json={"numberOfDocuments": 3})
        return httpx.Response(202, json={"taskUid": 1, "status": "enqueued"})

    return handler


def test_index_meili_index_option_and_env(store_path, monkeypatch) -> None:
    seen: list[str] = []
    transport = httpx.MockTransport(_fake_meili(seen))
    real_client = httpx.Client  # the patch below replaces httpx.Client itself
    monkeypatch.setattr(
        "leibniz.search.meili.httpx.Client", lambda **kw: real_client(transport=transport, **kw)
    )
    args = ["index", "build", "--db", str(store_path), "--backend", "meili", "--no-stats"]
    r = runner.invoke(app, [*args, "--meili-index", "leibniz_pages_staging"])
    assert r.exit_code == 0, r.stdout
    assert "Indexed 3 pages" in r.stdout
    touched = {p.split("/")[2] for p in seen if p.split(" ")[1].startswith("/indexes/")}
    assert touched == {"leibniz_pages_staging", "leibniz_pages_staging_meta"}
    seen.clear()
    r = runner.invoke(app, ["index", "status", "--backend", "meili", "--meili-index", "other"])
    assert r.exit_code == 0 and "(other)" in r.stdout and "documents: 3" in r.stdout
    assert all("/indexes/other" in p for p in seen if "/indexes/" in p)
    # the environment names the index when the option does not; the default otherwise
    seen.clear()
    monkeypatch.setenv("LEIBNIZ_MEILI_INDEX", "from_env")
    assert runner.invoke(app, ["index", "status", "--backend", "meili"]).exit_code == 0
    assert any("/indexes/from_env/" in p for p in seen)
    seen.clear()
    monkeypatch.delenv("LEIBNIZ_MEILI_INDEX")
    assert runner.invoke(app, ["index", "status", "--backend", "meili"]).exit_code == 0
    assert any("/indexes/leibniz_pages/" in p for p in seen)


def test_serve_check_takes_the_meili_index(store_path, monkeypatch) -> None:
    monkeypatch.setenv("LEIBNIZ_DB_PATH", str(store_path))
    monkeypatch.setenv("LEIBNIZ_SEARCH_BACKEND", "meili")
    monkeypatch.setenv("LEIBNIZ_MEILI_INDEX", "leibniz_pages_staging")
    r = runner.invoke(app, ["serve", "--check"])
    assert r.exit_code == 0, r.stdout
    assert "/api/search" in r.stdout


def test_index_bad_backend(store_path, tmp_path) -> None:
    r = runner.invoke(app, ["index", "build", "--db", str(store_path), "--backend", "solr"])
    assert r.exit_code != 0


def test_release_export_jsonl(store_path, tmp_path) -> None:
    out = tmp_path / "rel"
    r = runner.invoke(
        app,
        [
            "release",
            "export",
            "--db",
            str(store_path),
            "--out",
            str(out),
            "--format",
            "jsonl",
            "--dataset",
            "gt",
            "--no-stats",
        ],
    )
    assert r.exit_code == 0, r.stdout
    assert (out / "leibniz-gt" / "README.md").exists()
    r = runner.invoke(app, ["release", "export", "--db", str(store_path), "--dataset", "bogus"])
    assert r.exit_code != 0


def test_release_checklist_prints() -> None:
    r = runner.invoke(app, ["release", "checklist"])
    assert r.exit_code == 0


def test_serve_check_lists_routes(store_path, tmp_path) -> None:
    r = runner.invoke(
        app,
        ["serve", "--db", str(store_path), "--backend", "none", "--check"],
    )
    assert r.exit_code == 0, r.stdout
    for route in ("/api/search", "/api/pages/{page_id}", "/manifests/{work_id}"):
        assert route in r.stdout


def test_serve_check_reads_env(store_path, monkeypatch) -> None:
    monkeypatch.setenv("LEIBNIZ_DB_PATH", str(store_path))
    monkeypatch.setenv("LEIBNIZ_SEARCH_BACKEND", "none")
    r = runner.invoke(app, ["serve", "--check"])
    assert r.exit_code == 0, r.stdout
    for route in ("/healthz", "/robots.txt", "/api/works/{work_id}"):
        assert route in r.stdout


def test_serve_bad_backend(store_path) -> None:
    r = runner.invoke(app, ["serve", "--db", str(store_path), "--backend", "solr", "--check"])
    assert r.exit_code != 0


def test_index_bench(store_path, tmp_path, monkeypatch) -> None:
    be = Fts5Backend(tmp_path / "search.sqlite")
    conn = db.connect(store_path)
    be.rebuild(iter_page_docs(conn))
    conn.close()
    served = create_app(store_path, search=be, static_dir=None)
    monkeypatch.setattr("leibniz.search.cli.httpx.Client", lambda **kw: TestClient(served))
    r = runner.invoke(app, ["index", "bench", "--n", "5", "--json"])
    assert r.exit_code == 0, r.stdout
    res = json.loads(r.stdout)
    assert res["ok"] == 5 and res["pass"] is True
    r = runner.invoke(app, ["index", "bench", "--n", "3"])
    assert r.exit_code == 0 and "PASS" in r.stdout
    # no index behind the server → every search 503s → the criterion fails → exit 1
    monkeypatch.setattr(
        "leibniz.search.cli.httpx.Client",
        lambda **kw: TestClient(create_app(store_path, search=None, static_dir=None)),
    )
    r = runner.invoke(app, ["index", "bench", "--n", "2"])
    assert r.exit_code == 1 and "FAIL" in r.stdout
