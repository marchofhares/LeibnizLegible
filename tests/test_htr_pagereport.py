"""Tests for the LT1 report and the page-* CLI (offline: a scripted engine, PIL images)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz.htr import cli as bench_cli
from leibniz.htr import engines as ENG
from leibniz.htr import pageread as R
from leibniz.htr import pagereport as PR
from leibniz.htr import pagescore as S

pytest.importorskip("numpy")
pytest.importorskip("PIL")
runner = CliRunner()

NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
LINES = ["Mechanici scriptores plerique olim", "non nisi de quinque Machinis", "Fundamentalibus"]


def _xml() -> str:
    body = "".join(
        f'<TextLine id="l{i}"><Coords points="50,{100 + 80 * i} 450,{100 + 80 * i} '
        f'450,{140 + 80 * i} 50,{140 + 80 * i}"/>'
        f"<TextEquiv><Unicode>{t}</Unicode></TextEquiv></TextLine>"
        for i, t in enumerate(LINES)
    )
    return (
        f'<PcGts xmlns="{NS}"><Page imageFilename="p.jpg" imageWidth="1000" imageHeight="800">'
        f'<TextRegion id="r0" custom="structure {{type:MainZone;}}">{body}</TextRegion>'
        "</Page></PcGts>"
    )


def _jpeg(w: int, h: int) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), (220, 210, 190)).save(buf, format="JPEG")
    return buf.getvalue()


def _scores() -> dict:
    pooled = {
        "pages": 2,
        "failed": 1,
        "ref_chars": 100,
        "hyp_chars": 60,
        "edits": 50,
        "ref_lines": 6,
        "hyp_lines": 3,
        "cer": 0.5,
        "cer_lo": 0.1,
        "cer_hi": 0.9,
        "page_cer_mean": 0.5,
        "page_cer_min": 0.0,
        "page_cer_q1": 0.0,
        "page_cer_median": 0.5,
        "page_cer_q3": 1.0,
        "page_cer_max": 1.0,
    }
    letters = {"letters": 2, "cer": 0.3, "cer_lo": 0.2, "cer_hi": 0.4, "lines": 6}
    pol = {
        "all": letters,
        "half": {"selection": letters, "test": letters},
        "hand": {"L": letters, "K/k": letters},
    }
    usage = {
        "engine": "gemini",
        "calls": 3,
        "pages": 2,
        "input_tokens": 3000,
        "output_tokens": 900,
        "reasoning_tokens": 100,
        "cost": 0.0168,
        "seconds": 12.0,
        "settings": {"reasoning": "thinking_level low", "temperature": 0.0, "max_tokens": 4000},
    }
    diff = S.LineDiff(
        pages=1,
        ref_lines=3,
        a_lines=3,
        b_lines=3,
        both_right=1,
        only_a_right=1,
        both_wrong=1,
        ref_chars=90,
        a_chars=80,
        b_chars=85,
    ).as_dict()
    return {
        "philiumm": {
            "models": {"gemini-x": {"pages": 2}},
            "pages": 2,
            "calls": 2,
            "ref_lines": 6,
            "ref_chars": 100,
            "missing": [],
            "aggregate": {
                "gemini-x": {p: {"charged": pooled, "omitted": pooled} for p in S.POLICIES},
                "philiumm-kraken (line readings, joined)": {
                    p: {"charged": pooled, "omitted": pooled} for p in S.POLICIES
                },
            },
            "kraken": {"covered": 6, "dump": "d.jsonl"},
            "statuses": {
                "gemini-x": {
                    "final": {"ok": 1, "refused": 1},
                    "first": {"refused": 2},
                    "retried": 2,
                }
            },
            "usage": {"gemini-x": usage},
            "diff": [
                {"a": "gemini-x", "b": "philiumm-kraken (line readings, joined)", "counts": diff}
            ],
        },
        "pool": {
            "models": {"gemini-x": {"pages": 3}},
            "draw": {
                "letters": 2,
                "pages": 3,
                "pages_L": 2,
                "pages_K": 1,
                "letters_selection": 1,
                "letters_test": 1,
                "seed": 1,
            },
            "lines": 6,
            "ref_chars": 200,
            "aggregate": {
                "v1": {p: pol for p in S.POLICIES},
                "page:gemini-x": {p: pol for p in S.POLICIES},
            },
            "omitted": {"letters": 1, "aggregate": {"page:gemini-x": {p: pol for p in S.POLICIES}}},
            "failed_pages": ["W:0003"],
            "statuses": {
                "gemini-x": {
                    "final": {"ok": 2, "runaway": 1},
                    "first": {"ok": 2, "runaway": 1},
                    "retried": 1,
                }
            },
            "usage": {"gemini-x": usage},
            "diff": [{"a": "page:gemini-x", "b": "k3-trocr", "counts": diff, "declined_lines": 1}],
        },
        "generated": {"prompt_sha256": "abc123", "long_side": 2000, "max_tokens": 4000},
    }


def test_render_report_carries_the_tables_and_no_text(tmp_path: Path) -> None:
    committed = PR.committed_pool_rows()  # the committed K2b/K3 rows, if the files are there
    md = PR.render(_scores(), committed=committed)
    assert "## The protocol" in md and "abc123" in md and "2000 px" in md
    # the usage is summed over both sets (the fixture carries the same block twice)
    assert "| gemini-x | gemini | thinking_level low | 0.0 | 4000 | 4 | 6 |" in md
    assert "| gemini-x | **50.0 %** (10.0 %–90.0 %) | **50.0 %** (10.0 %–90.0 %) | 1 of 2 |" in md
    assert (
        "philiumm-kraken (line readings, joined)" in md and "6 of 6 reference lines covered" in md
    )
    assert "| page:gemini-x | **30.0 %** (20.0 %–40.0 %) |" in md
    assert (
        "| gemini-x | philiumm | 2 | 1 | 1 | 0 | 0 | 0 | 2 | 1 |" in md
    )  # refusals: one second-attempt ok
    assert (
        "| philiumm | gemini-x | philiumm-kraken (line readings, joined) | 3 | 3 | 3 | 1 | 1 | "
        "0 | 1 |" in md
    )
    assert "The page sets are small" in md and "GWLB's checked transcriptions of letters" in md
    assert "Mechanici" not in md
    if committed:
        assert "k3-trocr" in committed and committed["k3-trocr"]["all"]["letters"] == 134
        assert "| v1 |" in md
    paths = PR.write_report(
        _scores(), report_path=tmp_path / "r" / "page-llm.md", committed=committed
    )
    assert (
        paths[0].exists()
        and json.loads(paths[1].read_text(encoding="utf-8"))["pool"]["draw"]["pages"] == 3
    )


def test_render_without_the_kraken_row_and_without_the_pool() -> None:
    sc = _scores()
    sc["philiumm"]["kraken"] = {}
    sc["pool"] = {}
    md = PR.render(sc, committed={})
    assert "kraken model's row is missing" in md and "## The GWLB letter pool" in md


class _Pages:
    """A page engine answering the PAGE XML's lines for every call."""

    name = "scripted"
    version = "stub-1"

    def settings(self) -> dict:
        return {"max_tokens": 4000, "temperature": 0.0, "reasoning": "none"}

    def reply(self, data: bytes, *, prompt: str | None = None) -> ENG.ApiReply:
        return ENG.ApiReply(text="\n".join(LINES), stop="end", input_tokens=10, output_tokens=5)

    def close(self) -> None:
        pass


def test_page_cli_end_to_end_on_fixtures(tmp_path: Path, monkeypatch) -> None:
    val = tmp_path / "val"
    val.mkdir()
    for stem in ("P1", "P2"):
        (val / f"{stem}.xml").write_text(_xml(), encoding="utf-8")
        (val / f"{stem}.jpg").write_bytes(_jpeg(1000, 800))
    lists = tmp_path / "lists"
    res = runner.invoke(
        bench_cli.app,
        [
            "page-list",
            "--val-pages",
            str(val),
            "--out-dir",
            str(lists),
            "--n-pool",
            "6",
            "--seed",
            "3",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "PHILIUMM: 2 val pages" in res.stdout and (lists / "page-list-pool.csv").exists()
    pool_rows = R.read_page_list(lists / "page-list-pool.csv")
    assert 0 < len(pool_rows) <= 6 and all(r.set == "pool" for r in pool_rows)
    out = tmp_path / "readings"
    # the dry run prints the plan and makes no call
    res = runner.invoke(
        bench_cli.app,
        [
            "page-read",
            "--pages",
            str(lists / "page-list-philiumm.csv"),
            "--engine",
            "echo",
            "--model",
            "stub-1",
            "--val-pages",
            str(val),
            "--no-mirror",
            "--out",
            str(out),
            "--dry-run",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "2 calls to make" in res.stdout and not out.exists()
    monkeypatch.setattr(R, "build_engine", lambda *a, **k: _Pages())
    res = runner.invoke(
        bench_cli.app,
        [
            "page-read",
            "--pages",
            str(lists / "page-list-philiumm.csv"),
            "--engine",
            "echo",
            "--model",
            "stub-1",
            "--val-pages",
            str(val),
            "--no-mirror",
            "--out",
            str(out),
            "--long-side",
            "500",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "2 read" in res.stdout and (out / "stub-1.jsonl").exists()
    # the kraken side: cut the lines, fake a bench run dump, score, report
    lines_dir = tmp_path / "lines"
    res = runner.invoke(
        bench_cli.app, ["page-lines", "--val-pages", str(val), "--out", str(lines_dir)]
    )
    assert res.exit_code == 0 and "6 lines written" in res.stdout
    dump = tmp_path / "dump.jsonl"
    with dump.open("w", encoding="utf-8") as fh:
        for png in sorted(lines_dir.glob("*.png")):
            gt = png.with_name(png.stem + ".gt.txt").read_text(encoding="utf-8").strip()
            fh.write(
                json.dumps({"line_id": f"line:{png.stem}", "hyp": gt.replace("i", "l")}) + "\n"
            )
    scores = tmp_path / "scores.json"
    res = runner.invoke(
        bench_cli.app,
        [
            "page-score",
            "--set",
            "philiumm",
            "--pages",
            str(lists / "page-list-philiumm.csv"),
            "--readings",
            str(out),
            "--val-pages",
            str(val),
            "--kraken-lines",
            str(dump),
            "--scores",
            str(scores),
            "--split",
            "test",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert "stub-1" in res.stdout and "page CER 0.0 %" in res.stdout and scores.exists()
    sf = S.ScoreFile.load(scores)
    assert sf.philiumm["pages"] == 2 and sf.philiumm["kraken"]["covered"] == 6
    report = tmp_path / "reports" / "page-llm.md"
    res = runner.invoke(
        bench_cli.app, ["page-report", "--scores", str(scores), "--out", str(report)]
    )
    assert res.exit_code == 0, res.stdout
    md = report.read_text(encoding="utf-8")
    assert "| stub-1 | **0.0 %** (0.0 %–0.0 %) |" in md and report.with_suffix(".json").exists()
    assert "Mechanici" not in md
    # a bad --set and an empty readings dir are refused
    assert (
        runner.invoke(
            bench_cli.app,
            ["page-score", "--set", "x", "--pages", str(lists / "page-list-philiumm.csv")],
        ).exit_code
        != 0
    )
    res = runner.invoke(
        bench_cli.app,
        [
            "page-score",
            "--set",
            "pool",
            "--pages",
            str(lists / "page-list-pool.csv"),
            "--readings",
            str(tmp_path / "none"),
            "--scores",
            str(scores),
        ],
    )
    assert res.exit_code == 1 and "No readings" in res.stdout


def test_page_read_requires_a_model_for_an_api_engine(tmp_path: Path) -> None:
    lst = R.write_page_list([R.PageRow("W:0001", "pool")], tmp_path / "l.csv")
    res = runner.invoke(
        bench_cli.app, ["page-read", "--pages", str(lst), "--engine", "gemini", "--dry-run"]
    )
    assert res.exit_code != 0
