"""Tests for the C1 report gatherer/renderer (offline)."""

from __future__ import annotations

from pathlib import Path

from leibniz import db
from leibniz.layout.segment import SegLine, SegmentedPage
from leibniz.pipeline import report as R
from leibniz.pipeline.recognize import recognize_pages
from leibniz.pipeline.segment import segment_pages


class Fake:
    version = "philiumm-htr@v1"

    def segment(self, image: bytes) -> SegmentedPage:
        n = image[-1]
        lines = [
            SegLine(index=i, baseline=[(50, 140 + i * 120), (1950, 140 + i * 120)], boundary=[])
            for i in range(n)
        ]
        return SegmentedPage(lines=lines, width=2000, height=2500, n_regions=1 if n else 0)

    def crop_lines(self, image, page):
        return [b"x" for _ in page.lines]

    def transcribe_conf(self, images):
        return [("lorem ipsum", 0.85) for _ in images]


def _run_pipeline(tmp_path: Path):
    images = tmp_path / "images"
    conn = db.init_db(":memory:")
    spec = [
        ("H1", "LeibnizHandschriften", 3),
        ("H2", "LeibnizHandschriften", 0),
        ("B1", "LeibnizBriefwechsel", 4),
    ]
    for i, (wid, setn, n) in enumerate(spec):
        db.upsert_work(conn, db.Work(wid, setn))
        rel = f"{wid}/0001.jpg"
        p = images / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"J" + bytes([n]))
        db.upsert_page(
            conn,
            db.Page(
                work_id=wid,
                seq=1,
                image_url="u",
                width=2000,
                height=2500,
                local_path=rel,
                sha256=f"s{i}",
            ),
        )
    conn.commit()
    segment_pages(conn, Fake(), images_root=images)
    recognize_pages(conn, Fake(), Fake(), images_root=images)
    return conn


def test_gather_and_render(tmp_path) -> None:
    conn = _run_pipeline(tmp_path)
    rep = R.gather_report(conn, generated_at="2026-07-29T00:00:00Z")
    assert rep.status_counts.get("recognized") == 2
    assert rep.status_counts.get("skipped") == 1  # the blank page
    assert rep.n_lines_recognized == 7
    assert rep.conf_mean is not None
    md = R.render_report(rep)
    assert "# HTR v1 — corpus segmentation + recognition pipeline (Phase C1)" in md
    assert "Pipeline coverage" in md
    assert "Segmentation quality" in md
    assert "no_lines" in md  # skip taxonomy surfaces the blank page
    # per-set table present
    assert "LeibnizBriefwechsel" in md and "LeibnizHandschriften" in md


def test_render_empty_db_is_graceful() -> None:
    conn = db.init_db(":memory:")
    rep = R.gather_report(conn, generated_at="2026-07-29T00:00:00Z")
    md = R.render_report(rep)
    assert "No recognised lines" in md
    assert "No pages processed yet" in md
    conn.close()
