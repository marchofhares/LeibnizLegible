"""Tests for P1 Task 1: the aligner on PHILIUMM's worked example (offline fixture)."""

from __future__ import annotations

import csv
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from leibniz.align.philiumm import sample as S
from leibniz.align.philiumm.fetch import ALIGNER_COMMIT, SAMPLE_FILES, fetch_sample, raw_url
from leibniz.cli import app
from leibniz.net import PoliteClient

FIX = Path(__file__).parent / "fixtures" / "philiumm_sample"
runner = CliRunner()


def test_load_sample_reads_text_pages_output_and_report() -> None:
    smp = S.load_sample(FIX)
    assert smp.files == ["a.xml", "b.xml"] and smp.commit == ALIGNER_COMMIT
    assert smp.gt_text.startswith("Mechanici") and len(smp.htr["a.xml"].lines) == 5
    assert S.their_totals(smp)["nb_gt_aligned"] == 5
    assert len(S.their_line_scores(smp)) == 5  # 0.93, 0.71, 0.9, 0.52, 0.88
    assert S.their_aligned_above(smp, 0.7) == 4 and S.their_aligned_above(smp, 0.5) == 5
    with pytest.raises(FileNotFoundError):
        S.load_sample(FIX / "GT")


def test_similarities_are_their_formula_and_this_projects_fold() -> None:
    assert S.raw_similarity("abc", "abd") == pytest.approx(1 - 1 / 3)
    assert S.raw_similarity("", "") == 1.0 and S.raw_similarity("a", "") == 0.0
    assert S.raw_similarity("Jay", "J’ay") < 1.0 < 1.01  # raw keeps the apostrophe
    assert S.folded_similarity("niſi", "nisi") == 1.0  # the fold does not


def test_configurations_buckets_and_their_columns() -> None:
    smp = S.load_sample(FIX)
    confs = {c.label: c for c in S.run_configurations(smp)}
    assert set(confs) == {
        "file:a.xml",
        "file:b.xml",
        "concat:a.xml + b.xml",
        "concat:b.xml + a.xml",
        "regions",
    }
    a = S.compare(confs["file:a.xml"], smp)
    assert a.counts["a.xml"] == {
        "both_same": 1,
        "both_different": 1,
        "ours_only": 1,
        "theirs_only": 0,
        "neither": 2,
    }
    by_id = {p.line_id: p for p in a.pairs}
    assert by_id["stamp"].bucket == "neither"  # the library stamp: no one aligns it
    assert by_id["a2"].bucket == "both_different"  # their word window vs our slice
    assert by_id["a3"].bucket == "ours_only" and by_id["a3"].ours.startswith("Vectem")
    # the HTR line "de quinque Machinis Fundamentalibus ut" is closer to our slice than to
    # their window "Machinis Fundamentalibus, ut Vectem, Trochleam"
    assert by_id["a2"].sim_htr_ours > by_id["a2"].sim_htr_theirs
    assert S.witness_tally(a) == (1, 0, 0)
    b = S.compare(confs["file:b.xml"], smp)
    assert b.counts["b.xml"]["both_same"] == 2 and b.counts["b.xml"]["theirs_only"] == 1
    assert {p.line_id: p.theirs for p in b.pairs}[
        "b2"
    ] == "Am Rande:"  # their window grabbed a marker
    # order matters when both files are one piece: the text order mints more
    fwd, rev = confs["concat:a.xml + b.xml"], confs["concat:b.xml + a.xml"]
    assert fwd.n_minted == 5 and rev.n_minted == 3
    assert {ln.file for ln in fwd.lines} == {"a.xml", "b.xml"}
    regions = confs["regions"]
    assert regions.n_minted == 5 and regions.n_minted_above(S.THEIR_FILTER_SIM) == 5
    k = S.compare(regions, smp)
    assert {bk: k.total(bk) for bk in S.BUCKETS} == {
        "both_same": 3,
        "both_different": 1,
        "ours_only": 1,
        "theirs_only": 1,
        "neither": 2,
    }
    rows = S.their_csv_rows(regions)
    assert [r["filename"] for r in rows] == ["a.xml", "b.xml", "TOTAL"]
    assert rows[-1]["nb_gt_aligned"] == 5 and rows[-1]["pct_gt_aligned"] == 62.5
    assert rows[0]["nb_low_conf"] == "n/a"


def test_outputs_and_render(tmp_path: Path) -> None:
    smp = S.load_sample(FIX)
    confs = S.run_configurations(smp)
    comps = [S.compare(c, smp) for c in confs]
    n = S.write_comparison_csv(comps[-1], tmp_path / "c.csv")
    with (tmp_path / "c.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert n == 8 and rows[1]["bucket"] == "both_same" and rows[1]["sim_ours_theirs"] == "1.000"
    assert rows[1]["sim_htr_ours"] == rows[1]["sim_htr_theirs"] != ""
    md = S.render(smp, confs, comps, threshold=0.6, max_pairs=2, comparison_csv=tmp_path / "c.csv")
    assert "9d2ee4e500e0" in md and "| regions | 8 | 5 | 62.5 % |" in md
    assert "8 HTR lines, 5 replaced by edition text (62.5 %)" in md
    assert "### Where they differ — file:a.xml" in md and "Agreement is not correctness" in md
    summ = S.summary(smp, confs, comps, threshold=0.6)
    assert summ["theirs"]["nb_gt_aligned"] == 5 and summ["configurations"][-1]["n_minted"] == 5
    assert summ["their_aligned_raw_ge_0_7"] == 4 and "| regions | MainZone |" in md
    assert summ["comparisons"][-1]["both_different_witness"] == {
        "ours_closer": 1,
        "theirs_closer": 0,
        "tie": 0,
    }
    assert "closer to this project's slice on 1" in md
    S.write_summary(summ, tmp_path / "s.json")
    assert (tmp_path / "s.json").exists()


def test_fetch_sample_is_cache_first_and_pinned(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, content=b"<x/>" if request.url.path.endswith(".xml") else b"t")

    client = PoliteClient(
        client=httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0
    )
    dest = tmp_path / "sample"
    paths = fetch_sample(dest, client=client, files=SAMPLE_FILES[:3])
    assert len(paths) == 3 and all(p.exists() for p in paths) and len(calls) == 3
    assert calls[0] == raw_url(SAMPLE_FILES[0]) and ALIGNER_COMMIT in calls[0]
    assert (dest / "COMMIT").read_text(encoding="utf-8").strip() == ALIGNER_COMMIT
    fetch_sample(dest, client=client, files=SAMPLE_FILES[:3])
    assert len(calls) == 3  # nothing re-fetched
    (dest / "COMMIT").write_text("0000000000000000\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        fetch_sample(dest, client=client, files=SAMPLE_FILES[:3])


def test_philiumm_sample_cli_offline(tmp_path: Path) -> None:
    out = tmp_path / "reports" / "alignment-sample.md"
    res = runner.invoke(
        app, ["align", "philiumm-sample", "--offline", "--dest", str(FIX), "--out", str(out)]
    )
    assert res.exit_code == 0, res.stdout
    flat = " ".join(res.stdout.split())
    assert "theirs 8 lines, 5 aligned (62.5 %)" in flat and "regions 5/8 minted" in flat
    assert out.exists() and out.with_suffix(".json").exists()
    assert (FIX / "comparison.csv").exists()
    (FIX / "comparison.csv").unlink()  # the fixture directory stays as committed
