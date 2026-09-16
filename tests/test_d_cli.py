"""CLI-level tests for `leibniz index`, `leibniz release`, `leibniz serve --check`."""

from __future__ import annotations

import json

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
