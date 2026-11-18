"""``leibniz release check`` (REL1): the checklist's checks, on a fixture export."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app
from leibniz.release import cards as C
from leibniz.release import state as S
from leibniz.release.check import check_release
from leibniz.release.export import export_all


@pytest.fixture
def root(german_store_path, tmp_path) -> Path:
    out = tmp_path / "release"
    conn = db.connect(german_store_path)
    export_all(conn, out, fmt="jsonl")
    conn.close()
    return out


def _failed(rep) -> list[str]:
    return [text for ok, text in rep.lines if not ok]


def test_a_fresh_export_passes_every_check(root) -> None:
    rep = check_release(root)
    assert rep.failures == 0, _failed(rep)
    texts = [t for _ok, t in rep.lines]
    assert any("gt and gt-nc are disjoint" in t for t in texts)
    assert any("no line with an nc-bucket source (0 found)" in t for t in texts)
    assert any("+ released in neither" in t and "= the store's gt_lines" in t for t in texts)
    assert any("no DOI reserved yet, and the card says so" in t for t in texts)


def test_the_counts_are_compared_with_the_sites_stats(root) -> None:
    manifest = json.loads((root / "leibniz-transcriptions" / "MANIFEST.json").read_text())
    by_model = manifest["counts"]["lines"]["by_model"]
    live = {
        "lines": manifest["row_counts"]["lines"],
        "models": by_model,
        "pages_by_lang": manifest["corpus"]["pages_by_lang"],
    }
    assert check_release(root, stats=live).failures == 0
    off = {**live, "lines": live["lines"] + 1}
    rep = check_release(root, stats=off)
    assert rep.failures == 1 and "/api/stats lines" in _failed(rep)[0]


def test_a_changed_file_an_nc_line_and_a_misplaced_row_fail(root) -> None:
    lines = root / "leibniz-transcriptions" / "lines-0001.jsonl.gz"
    rows = [json.loads(x) for x in gzip.open(lines, "rt", encoding="utf-8") if x.strip()]
    rows[0]["source"] = {"license_bucket": "nc"}
    with gzip.open(lines, "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    failed = _failed(check_release(root))
    assert any("differs from its manifest entry" in t for t in failed)
    assert any("no line with an nc-bucket source (1 found)" in t for t in failed)
    # the NC deposit's rows under the open deposit's name are caught row by row
    (root / "leibniz-gt" / "gt_lines-0001.jsonl.gz").write_bytes(
        (root / "leibniz-gt-nc" / "gt_lines-0001.jsonl.gz").read_bytes()
    )
    failed = _failed(check_release(root))
    assert any("gt: every row belongs to the open deposit" in t for t in failed)
    assert any("gt and gt-nc are disjoint" in t for t in failed)


def test_a_reserved_doi_must_be_in_the_card(root) -> None:
    release = S.load_release(root)
    S.set_doi(release, "gt", "10.5072/zenodo.2002")
    S.save_release(root, release)
    failed = _failed(check_release(root))
    assert failed == ["gt: the card carries doi:10.5072/zenodo.2002"]
    C.rerender(root)
    assert check_release(root).failures == 0


def test_the_model_package_is_checked_against_its_manifest_and_its_zip(root, tmp_path) -> None:
    from tests.test_release_model import K3_CARD, NAME, _checkpoint

    from leibniz.release.model import build_package

    build_package(_checkpoint(tmp_path / "best"), K3_CARD, NAME, root)
    assert check_release(root).failures == 0
    (root / NAME / "config.json").write_text("{}")  # changed after packaging
    failed = _failed(check_release(root))
    assert any("model:" in t and "config.json" in t for t in failed)
    (root / f"{NAME}.zip").unlink()
    assert any(f"{NAME}.zip is missing" in t for t in _failed(check_release(root)))


def test_release_check_cli(root, tmp_path) -> None:
    ok = CliRunner().invoke(app, ["release", "check", "--out", str(root)])
    assert ok.exit_code == 0 and "0 failed" in ok.output
    stats = tmp_path / "stats.json"
    stats.write_text(json.dumps({"lines": 1, "models": {}, "pages_by_lang": {}}))
    bad = CliRunner().invoke(app, ["release", "check", "--out", str(root), "--stats", str(stats)])
    assert bad.exit_code == 2 and "FAIL" in bad.output  # the lines, the lines by model
    empty = CliRunner().invoke(app, ["release", "check", "--out", str(tmp_path / "nothing")])
    assert empty.exit_code == 1
