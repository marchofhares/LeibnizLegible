"""Tests for K2's reading job (seeded store, synthetic page images, a stub reader)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import kurrent_read as R
from leibniz.align.kurrent_pilot import load_readings, open_readonly
from leibniz.cli import app

pytest.importorskip("PIL")
runner = CliRunner()
TODAY = date(2026, 7, 29)
TEXTS = {
    "W:0001": ["Hochgeehrter Herr, ich habe dero Schreiben", "vnd bedancke mich daß Sie mir"],
    "W:0002": ["haben zukommen lassen; es ist aber", "daß der Herr von Boineburg alß ein"],
    "W:0003": ["dritte Seite erste Zeile", "dritte Seite zweite Zeile", "dritte Seite dritte"],
}


def _page_image(path: Path, n_lines: int) -> None:
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (600, 60 * n_lines + 40), "white")
    draw = ImageDraw.Draw(im)
    for k in range(n_lines):
        top = 20 + 60 * k
        draw.rectangle((40, top + 10, 560, top + 40), fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="JPEG")


def _seed(db_path: Path, images_root: Path, *, image_for_page3: bool = True) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W", "LeibnizBriefwechsel", shelfmarks=["LBr 10"]))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    for seq, lab in enumerate(["1r", "1v", "2r"], start=1):
        pid = f"W:{seq:04d}"
        local = f"W/{seq:04d}.jpg"
        db.upsert_page(
            conn, db.Page(work_id="W", seq=seq, label=lab, status="recognized", local_path=local)
        )
        texts = TEXTS[pid]
        if seq != 3 or image_for_page3:
            _page_image(images_root / local, len(texts))
        for k, _text in enumerate(texts):
            top = 20 + 60 * k
            poly = [[40, top + 10], [560, top + 10], [560, top + 40], [40, top + 40]]
            # the last line of page 3 has no geometry at all
            geom = {} if (seq == 3 and k == 2) else {"polygon": poly, "baseline": [[40, top + 38]]}
            db.insert_line(
                conn, db.Line(page_id=pid, line_seq=k, run_id=seg, status="machine", **geom)
            )
            db.set_line_recognition(conn, pid, k, text="xxxx", conf=0.5, model="htr", run_id=rec)
        db.upsert_page_stats(conn, db.PageStats(page_id=pid, n_lines=len(texts), run_id=seg))
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="g1",
            metadata={"textart": "Abf., eigh."},
            shelfmark_refs=["LBr 10 Bl. 1"],
            aa_refs=[{"series": 1, "volume": 3, "piece": "g1"}],
        ),
    )
    db.upsert_crosswalk(conn, db.CrosswalkMatch("g1", "W", "gwlb_link", 1.0))
    conn.commit()
    conn.close()


def _rows() -> list[dict]:
    # the census placed g1 on the first page only; the resolver gives Bl. 1 = pages 1 and 2
    return [
        {
            "record_id": "g1",
            "work_id": "W",
            "volume_label": "I,3",
            "page_ids": ["W:0001"],
            "n_lines": 2,
        },
        {
            "record_id": "g2",
            "work_id": "W",
            "volume_label": "I,3",
            "page_ids": ["W:0003"],
            "n_lines": 3,
        },
    ]


class _Stub:
    """A reader on the in-memory protocol: returns the page's scripted text per crop width order."""

    name = "stub"
    version = "stub@1"
    device = "cpu"
    settings = {"model": "stub", "dtype": "float32"}

    def __init__(self) -> None:
        self.calls: list[int] = []
        self.timings: dict[str, float] = {}
        self.counts: dict[str, int] = {}
        self.profile = True

    def transcribe_images(self, images):
        self.calls.append(len(images))
        self.timings["generate"] = self.timings.get("generate", 0.0) + 0.01
        self.counts["steps"] = self.counts.get("steps", 0) + 5
        self.counts["tokens"] = self.counts.get("tokens", 0) + len(images)
        return [(f"line {im.width}x{im.height}", 0.9) for im in images]

    def transcribe_conf(self, pngs):
        self.timings["decode"] = self.timings.get("decode", 0.0) + 0.02
        return [("png line", 0.8) for _ in pngs]

    def reset_timings(self) -> None:
        self.timings = {}
        self.counts = {}


class _BytesOnly:
    name = "bytes"
    version = "bytes@1"
    device = "cpu"

    def transcribe(self, images):
        return ["b" for _ in images]


def test_plan_pages_unions_census_and_resolver(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    conn = open_readonly(db_path)
    try:
        plan = R.plan_pages(conn, _rows(), today=TODAY)
        assert plan.pages == ["W:0001", "W:0002", "W:0003"]
        assert plan.records_by_page == {"W:0001": ["g1"], "W:0002": ["g1"], "W:0003": ["g2"]}
        assert plan.n_records == 2 and plan.n_records_with_lines == 2
        assert plan.n_records_localizable_now == 1  # g2 has no catalogue record
        assert (plan.n_pages_census, plan.n_pages_resolver) == (2, 2)
        assert (plan.n_pages_only_census, plan.n_pages_only_resolver) == (1, 1)
        assert (plan.n_same, plan.n_narrowed, plan.n_widened, plan.n_other) == (0, 1, 1, 0)
        assert plan.n_lines == 7
        census_only = R.plan_pages(conn, _rows(), today=TODAY, resolve=False)
        assert census_only.pages == ["W:0001", "W:0003"] and census_only.n_lines == 5
        d = plan.as_dict()
        assert d["n_pages"] == 3 and "pages" not in d
    finally:
        conn.close()


def test_read_pages_reads_resumes_and_counts_skips(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images, image_for_page3=False)
    readings = tmp_path / "readings"
    conn = open_readonly(db_path)
    try:
        pages = ["W:0001", "W:0002", "W:0003"]
        stub = _Stub()
        logged: list[str] = []
        stats = R.read_pages(
            conn,
            pages,
            "stub",
            lambda: stub,
            images_root=images,
            readings_dir=readings,
            batch_size=3,
            log=logged.append,
            log_every_s=0.0,
        )
        assert stats.lines_total == 7 and stats.lines_read == 4 and stats.lines_before == 0
        assert stats.skipped == {"no_image": 3}  # page 3's image is not cached
        assert stats.pages_done == 3 and stats.lines_left == 0 and stats.finished
        assert stats.model == "stub@1" and stats.device == "cpu"
        assert stats.settings == {"model": "stub", "dtype": "float32", "batch_size": 3}
        assert stub.calls == [2, 2]  # one page at a time, batches of three
        have = load_readings(readings, "stub")
        assert sorted(have) == ["W:0001:000", "W:0001:001", "W:0002:000", "W:0002:001"]
        assert have["W:0001:000"].text.startswith("line ") and have["W:0001:000"].conf == 0.9
        assert have["W:0001:000"].model == "stub@1" and have["W:0001:000"].ms >= 0
        assert any("ETA" in m and "lines/h" in m for m in logged)
        saved = json.loads(R.stats_path(readings, "stub").read_text(encoding="utf-8"))
        assert saved["lines_done"] == 4 and saved["skipped"] == {"no_image": 3}
        assert R.load_skipped(readings, "stub") == {
            "W:0003:000": "no_image",
            "W:0003:001": "no_image",
            "W:0003:002": "no_image",
        }
        # a second run: nothing to read, the engine is never built
        again = R.read_pages(
            conn, pages, "stub", lambda: 1 / 0, images_root=images, readings_dir=readings
        )
        assert again.lines_before == 4 and again.lines_read == 0 and again.finished
        assert again.skipped == {"no_image": 3}
    finally:
        conn.close()


def test_read_pages_geometry_skips_max_lines_and_bytes_fallback(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    readings = tmp_path / "readings"
    conn = open_readonly(db_path)
    try:
        stats = R.read_pages(
            conn,
            ["W:0003"],
            "bytes",
            _BytesOnly,
            images_root=images,
            readings_dir=readings,
            batch_size=8,
        )
        assert stats.lines_read == 2 and stats.skipped == {"no_geometry": 1}
        assert stats.finished and stats.pages_done == 1
        have = load_readings(readings, "bytes")
        assert {r.text for r in have.values()} == {"b"} and have["W:0003:000"].conf is None
        capped = R.read_pages(
            conn,
            ["W:0001", "W:0002"],
            "capped",
            _Stub,
            images_root=images,
            readings_dir=readings,
            max_lines=3,
        )
        assert capped.lines_read == 3 and not capped.finished and capped.lines_left == 1
    finally:
        conn.close()


def test_sample_pages_spreads_and_covers(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    conn = open_readonly(db_path)
    try:
        pages = ["W:0001", "W:0002", "W:0003"]
        assert R.sample_pages(conn, pages, 100) == pages  # fewer lines than asked: all
        picked = R.sample_pages(conn, pages, 3)
        assert R.count_lines_on(conn, picked) >= 3 and set(picked) <= set(pages)
        assert R.sample_pages(conn, [], 3) == []
    finally:
        conn.close()


def test_profile_and_sweep_on_the_stub(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    conn = open_readonly(db_path)
    try:
        prof = R.profile_batch(
            conn, ["W:0001", "W:0002"], _Stub(), images_root=images, batch_size=3
        )
        assert prof["n_lines"] == 3 and prof["batch_size"] == 3
        assert set(prof["stages_before_ms"]) >= {"page_decode", "crop", "png_encode", "decode"}
        assert "generate" in prof["stages_after_ms"] and "png_encode" not in prof["stages_after_ms"]
        assert prof["ms_per_line_before"] > 0 and prof["ms_per_line_after"] > 0
        assert prof["generation_steps"] == 5 and prof["generated_tokens"] == 3
        settings = [R.SweepSetting(2), R.SweepSetting(4, "float16", True)]
        assert [s.key for s in settings] == ["b2-float32", "b4-float16-kv"]
        rows = R.sweep(
            conn,
            ["W:0001", "W:0002"],
            settings,
            lambda st: _Stub(),
            images_root=images,
            scratch_dir=tmp_path / "sweep",
            n_lines=3,
        )
        assert [r["key"] for r in rows] == ["b2-float32", "b4-float16-kv"]
        assert all(r["lines"] == 3 and r["lines_per_second"] > 0 for r in rows)
        assert (tmp_path / "sweep" / "b2-float32.jsonl").exists()
        text = R.render_read_report(
            plan=R.plan_pages(conn, _rows(), today=TODAY).as_dict(),
            profile=prof,
            sweep_rows=rows,
            dresden={
                "K1": None,
                "fp16": {
                    "cer": 0.075,
                    "cer_lo": 0.07,
                    "cer_hi": 0.08,
                    "lenient_cer": 0.05,
                    "strict_cer": 0.09,
                    "ms_per_line": 100.0,
                    "n_lines": 383,
                    "device": "cuda",
                },
            },
            chosen={**rows[1], "note": "chosen for the test"},
            stats=None,
        )
        assert "## The sweep" in text and "b4-float16-kv" in text and "7.5 %" in text
        assert "chosen for the test" in text and "None" not in text
    finally:
        conn.close()


def test_format_duration_and_progress_line() -> None:
    assert R.format_duration(None) == "—"
    assert R.format_duration(42) == "42s"
    assert R.format_duration(125) == "2m 05s"
    assert R.format_duration(3600 * 5 + 60 * 7) == "5h 07m"
    st = R.ReadStats(reader="r", lines_total=1000, lines_before=100, lines_read=200, seconds=100.0)
    st.skipped = {"no_image": 50}
    assert st.lines_done == 300 and st.lines_left == 650
    assert st.lines_per_hour == 7200.0 and st.ms_per_line == 500.0
    assert st.eta_seconds == pytest.approx(325.0)
    line = R.progress_line(st)
    assert "300/1,000 lines done" in line and "7,200 lines/h" in line and "ETA 5m 25s" in line
    assert R.ReadStats(reader="r").eta_seconds is None


def test_dresden_row_reads_a_smoke_json(tmp_path: Path) -> None:
    path = tmp_path / "bootstrap-candidates.json"
    path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "key": "trocr-kurrent-xvi-xvii",
                        "status": "ok",
                        "n_lines": 383,
                        "device": "cuda",
                        "ms_per_line": 120.0,
                        "scores": {
                            "philiumm": {"cer": 0.074, "cer_lo": 0.067, "cer_hi": 0.082},
                            "lenient": {"cer": 0.052},
                            "strict": {"cer": 0.09},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    row = R.dresden_row(path)
    assert row is not None and row["cer"] == 0.074 and row["lenient_cer"] == 0.052
    assert R.dresden_row(path, "philiumm") is None
    assert R.dresden_row(tmp_path / "missing.json") is None


def test_cli_kurrent_read_with_echo_then_report(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    german = tmp_path / "german.jsonl"
    german.write_text("\n".join(json.dumps(r) for r in _rows()), encoding="utf-8")
    readings = tmp_path / "readings"
    common = [
        "align",
        "kurrent-read",
        "--db",
        str(db_path),
        "--german",
        str(german),
        "--edition-cache",
        str(tmp_path / "none.jsonl"),
        "--images",
        str(images),
        "--reader",
        "echo",
        "--readings-dir",
        str(readings),
        "--today",
        TODAY.isoformat(),
        "--device",
        "cpu",
    ]
    result = runner.invoke(app, [*common, "--max-lines", "3", "--batch-size", "2"])
    assert result.exit_code == 0, result.output
    assert "3 pages" in result.output and "7 recognised" in result.output
    assert "stopped" in result.output
    plan = json.loads((readings / "plan.json").read_text(encoding="utf-8"))
    assert plan["n_pages"] == 3 and plan["pages"] == ["W:0001", "W:0002", "W:0003"]
    assert len(load_readings(readings, "echo")) == 3
    result = runner.invoke(app, common)
    assert result.exit_code == 0, result.output
    assert "finished" in result.output
    assert len(load_readings(readings, "echo")) == 6  # the line without geometry is skipped
    result = runner.invoke(app, [*common, "--report", "--reports-dir", str(tmp_path / "reports")])
    assert result.exit_code == 0, result.output
    text = (tmp_path / "reports" / "k2-read.md").read_text(encoding="utf-8")
    assert "## The pages" in text and "## The job" in text and "no_geometry 1" in text
    assert "None" not in text
