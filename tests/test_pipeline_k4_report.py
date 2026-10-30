"""The K4 reading report (Task 4) from the job's files: numbers only, no store."""

# ruff: noqa: E501  (the fixture log and CSV carry the job's own long lines)

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from leibniz.cli import app
from leibniz.pipeline import k4_report as K
from leibniz.pipeline.k4_report import read_job_log

LOG = """# launch 1 2026-10-28T09:50:13-04:00
kurrent-read 24,078 pages from data/kurrent/german-pages.txt, 1,539,721
recognised lines; reader k3-trocr; device cuda
10:00:13 k3-trocr: 4,700/1,539,721 lines done (4,700 this run, 0 skipped) · 28,200 lines/h · 128 ms/line · ETA 2d 6h · pages 70/24,078
\tMaximum resident set size (kbytes): 2291072
\tElapsed (wall clock) time (h:mm:ss or m:ss): 1:02:03
READ-EXIT 137 launch 1 2026-10-28T10:52:16-04:00
# relaunch 1 of 5 in 60 s after exit 137 2026-10-28T10:52:16-04:00
# launch 2 2026-10-28T10:53:16-04:00
11:03:16 k3-trocr: 30,000/1,539,721 lines done (1,000 this run, 2 skipped) · 28,000 lines/h · 129 ms/line · ETA 2d 5h · pages 480/24,078
\tMaximum resident set size (kbytes): 2200000
\tElapsed (wall clock) time (h:mm:ss or m:ss): 52:10:00
READ-EXIT 0 launch 2 2026-10-30T15:03:16-04:00
READ-DONE exit 0 after 2 launch(es) 2026-10-30T15:03:16-04:00
"""

GUARD = """# guard start 2026-10-28T09:50:16-04:00 pattern=[k]urrent-read --db limit=5900MiB ram_floor=2500MiB
1793195431,1290,6,8877
1793195436,5697,99,7493
1793195441,4100,4,7600
# guard kill 2026-10-28T10:52:10-04:00: used 5950 MiB > 5900 MiB
# guard end 2026-10-28T10:52:20-04:00
# guard start 2026-10-28T10:53:19-04:00 pattern=[k]urrent-read --db limit=5900MiB ram_floor=2500MiB
1793199200,4500,5,7700
# guard end 2026-10-30T15:03:20-04:00
"""

STATS = {
    "reader": "k3-trocr",
    "model": "k3-trocr@runs-615-epoch-5",
    "device": "cuda",
    "settings": {"batch_size": 16, "use_cache": True},
    "pages_total": 24078,
    "pages_done": 24078,
    "lines_total": 1539721,
    "lines_before": 30000,
    "lines_read": 1509719,
    "lines_done": 1539719,
    "lines_left": 0,
    "skipped": {"no_image": 2},
    "n_skipped": 2,
    "seconds": 187800.0,
    "model_seconds": 180000.0,
    "ms_per_line": 124.4,
    "lines_per_hour": 28942.0,
    "started": "2026-10-28T14:53:16+00:00",
    "updated": "2026-10-30T19:03:16+00:00",
    "finished": True,
}

IMPORT = {
    "pages": 24078,
    "pages_done_before": 0,
    "pages_written": 24070,
    "pages_without_readings": 8,
    "lines": 1539721,
    "rows_written": 1500000,
    "empty_readings": 39717,
    "lines_without_reading": 4,
    "orphan_readings": 0,
    "narrow_px": 80,
    "narrow_lines": 252286,
    "narrow_rows": 250000,
    "model": "k3-trocr@runs-615-epoch-5",
    "scope": "de",
    "run_id": 700,
    "dry_run": False,
    "by_set": {
        "LeibnizBriefwechsel": {
            "pages": 14455,
            "lines": 900000,
            "rows": 880000,
            "narrow_lines": 150000,
        },
        "LeibnizHandschriften": {
            "pages": 9604,
            "lines": 639721,
            "rows": 620000,
            "narrow_lines": 102286,
        },
    },
    "under_run": [24070, 1500000],
    "store": {"db": 19143570432, "wal": 0},
}


PAGE_LANG = {
    "pages": 236210,
    "german_pages": 30797,
    "chosen": {"key": "hits≥2 score≥0.3 tokens≥8", "precision": 0.9523, "recall": 0.7453},
}


def _files(tmp_path: Path) -> dict[str, Path]:
    d = tmp_path / "k4"
    d.mkdir()
    (d / "page-lang.json").write_text(json.dumps(PAGE_LANG), encoding="utf-8")
    (d / "k4-read.log").write_text(LOG, encoding="utf-8")
    (d / "guard.csv").write_text(GUARD, encoding="utf-8")
    (d / "k3-trocr.stats.json").write_text(json.dumps(STATS), encoding="utf-8")
    (d / "import.json").write_text(json.dumps(IMPORT), encoding="utf-8")
    names = ("k4-read.log", "guard.csv", "k3-trocr.stats.json", "import.json", "page-lang.json")
    return {k: d / k for k in names}


def test_read_job_log(tmp_path: Path) -> None:
    f = _files(tmp_path)
    log = K.read_job_log(f["k4-read.log"])
    assert len(log.launches) == 2 and len(log.relaunches) == 1
    assert log.relaunches[0] == {"n": 1, "after_exit": 137, "at": "2026-10-28T10:52:16-04:00"}
    assert [e["code"] for e in log.exits] == [137, 0]
    assert log.max_rss_kb == [2291072, 2200000] and log.peak_rss_kb == 2291072
    assert log.wall == ["1:02:03", "52:10:00"]
    assert log.done == {"code": 0, "launches": 2, "at": "2026-10-30T15:03:16-04:00"}
    assert log.first_progress.startswith("10:00:13 k3-trocr: 4,700/1,539,721")
    assert log.last_progress.startswith("11:03:16")
    assert K.read_job_log(tmp_path / "none.log").launches == []


def test_read_guard_csv(tmp_path: Path) -> None:
    f = _files(tmp_path)
    g = K.read_guard_csv(f["guard.csv"])
    assert g.samples == 4 and g.starts == 2
    assert g.peak_used_mib == 5697 and g.min_avail_mib == 7493
    assert g.mean_util_pct == 28.5
    assert len(g.kills) == 1 and "5950 MiB" in g.kills[0]


def test_gather_and_render(tmp_path: Path) -> None:
    f = _files(tmp_path)
    summ = K.gather(
        stats_path=f["k3-trocr.stats.json"],
        log_path=f["k4-read.log"],
        guard_path=f["guard.csv"],
        import_summary_path=f["import.json"],
        page_lang_path=f["page-lang.json"],
        store_before=17143570432,
        today="2026-10-31",
    )
    md = K.render(summ)
    assert (
        "threshold hits≥2 score≥0.3 tokens≥8; on the census's pieces precision 95.2 %, recall 74.5 %"
        in md
    )
    assert "30,797 pages called German of 236,210" in md and "keeps v1's text" in md
    assert "| pages | 24,078 of 24,078 |" in md
    assert "| launches · relaunches | 2 · 1 |" in md
    assert (
        "| peak host RSS (`/usr/bin/time -v`, launches that ended on their own) | 2,291,072 KB |"
        in md
    )
    assert "| card peak (nvidia-smi, Xwayland included) | 5,697 MiB |" in md
    assert "| crops under 80 px | 252,286 lines, 250,000 of them with a row |" in md
    assert "| store after | 19,143,570,432 bytes (+2,000,000,000 bytes), WAL 0 |" in md
    assert "| LeibnizBriefwechsel | 14,455 | 900,000 | 880,000 | 150,000 |" in md
    assert "Open question 32" in md
    paths = K.write_report(summ, out=tmp_path / "out" / "k4-reading.md")
    assert paths["md"].exists() and json.loads(paths["json"].read_text())["store_before"]
    # without the import: the section says so, nothing breaks
    bare = K.render(
        K.gather(stats_path=None, log_path=None, guard_path=None, import_summary_path=None)
    )
    assert "(not written yet)" in bare and "(no stats file)" in bare


def test_cli_k4_report(tmp_path: Path) -> None:
    f = _files(tmp_path)
    out = tmp_path / "r" / "k4-reading.md"
    res = CliRunner().invoke(
        app,
        [
            "pipeline",
            "k4-report",
            "--stats",
            str(f["k3-trocr.stats.json"]),
            "--log",
            str(f["k4-read.log"]),
            "--guard",
            str(f["guard.csv"]),
            "--import-summary",
            str(f["import.json"]),
            "--page-lang",
            str(f["page-lang.json"]),
            "--out",
            str(out),
            "--today",
            "2026-10-31",
        ],
    )
    assert res.exit_code == 0, res.output
    assert out.exists() and out.with_suffix(".json").exists()
    assert "Generated 2026-10-31" in out.read_text(encoding="utf-8")


def test_wrapped_progress_lines_are_joined(tmp_path):
    log = tmp_path / "k4-read.log"
    log.write_text(
        "# launch 1 2026-10-28T09:50:13-04:00\n"
        "10:00:35 k3-trocr: 5,771/1,539,721 lines done (5,771 this run, 0 \n"
        "skipped) · 34,327 lines/h · 105 ms/line · ETA 44h 41m · pages 107/24,078\n"
        "  finished: k3-trocr: 1,539,721/1,539,721 lines done (1,172,917 this run, 0 \n"
        "skipped) · 39,666 lines/h · 91 ms/line · ETA 0s · pages 24,078/24,078; stats \n"
    )
    parsed = read_job_log(log)
    assert parsed.first_progress == (
        "10:00:35 k3-trocr: 5,771/1,539,721 lines done (5,771 this run, 0 skipped) · "
        "34,327 lines/h · 105 ms/line · ETA 44h 41m · pages 107/24,078"
    )
    assert parsed.last_progress.endswith("ETA 0s · pages 24,078/24,078")
    assert "; stats" not in parsed.last_progress
