"""CLI-level tests for `leibniz index`, `leibniz release`, `leibniz serve --check`."""

from __future__ import annotations

from typer.testing import CliRunner

from leibniz.cli import app

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
