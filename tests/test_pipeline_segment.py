"""Tests for the corpus segmentation stage (offline; fake segmenter)."""

from __future__ import annotations

from pathlib import Path

from leibniz import db
from leibniz.layout.segment import SegLine, SegmentedPage
from leibniz.pipeline.segment import segment_pages


class FakeSegmenter:
    """Segments by reading a line count out of the last image byte.

    Emits evenly spaced rectangular lines so :mod:`leibniz.pipeline.stats` has
    real geometry to measure. A byte of 0 → a blank page (no lines). A byte of
    255 → raises, exercising the per-page failure path.
    """

    def segment(self, image: bytes) -> SegmentedPage:
        n = image[-1]
        if n == 255:
            raise RuntimeError("boom")
        lines = [
            SegLine(
                index=i,
                baseline=[(50, 140 + i * 120), (1950, 140 + i * 120)],
                boundary=[
                    (50, 100 + i * 120),
                    (1950, 100 + i * 120),
                    (1950, 180 + i * 120),
                    (50, 180 + i * 120),
                ],
            )
            for i in range(n)
        ]
        return SegmentedPage(lines=lines, width=2000, height=2500, n_regions=1 if n else 0)


def _seed(tmp_path: Path, spec: list[tuple[str, int]]) -> tuple[object, Path]:
    """Create a DB + cached fake images; ``spec`` = [(work_id, line_count), ...]."""
    images = tmp_path / "images"
    conn = db.init_db(":memory:")
    for i, (wid, nlines) in enumerate(spec):
        db.upsert_work(conn, db.Work(wid, "LeibnizHandschriften"))
        rel = f"{wid}/0001.jpg"
        p = images / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"JPEG" + bytes([nlines]))
        db.upsert_page(
            conn,
            db.Page(
                work_id=wid,
                seq=1,
                image_url="u",
                width=2000,
                height=2500,
                local_path=rel,
                n_bytes=p.stat().st_size,
                sha256=f"sha{i}",
            ),
        )
    conn.commit()
    return conn, images


def test_segment_happy_path_and_stats(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 3), ("W2", 5)])
    result = segment_pages(conn, FakeSegmenter(), images_root=images)
    assert result.segmented == 2
    assert result.n_lines == 8
    assert db.count_pages_by_status(conn, "segmented") == 2
    # geometry + stats stored
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert len(lines) == 3
    assert lines[0].polygon is not None and lines[0].text is None
    ps = db.get_page_stats(conn, "W1:0001")
    assert ps.n_lines == 3 and ps.run_id == result.run_id
    # run recorded with counts
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (result.run_id,)).fetchone()
    assert row["stage"] == "segment" and row["n_ok"] == 2


def test_blank_page_skipped_with_reason(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 0)])
    result = segment_pages(conn, FakeSegmenter(), images_root=images)
    assert result.segmented == 0 and result.skipped == 1
    page = db.get_page(conn, "W1:0001")
    assert page.status == "skipped" and page.skip_reason == "no_lines"
    # even a blank page gets a (zero-line) stats row
    assert db.get_page_stats(conn, "W1:0001").n_lines == 0


def test_segmenter_error_is_isolated(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 3), ("BAD", 255), ("W3", 2)])
    result = segment_pages(conn, FakeSegmenter(), images_root=images)
    assert result.segmented == 2  # the good pages still processed
    assert any("boom" in reason for _pid, reason in result.failures)
    assert db.get_page(conn, "BAD:0001").status == "skipped"


def test_missing_image_file_skipped(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 3)])
    (images / "W1/0001.jpg").unlink()
    result = segment_pages(conn, FakeSegmenter(), images_root=images)
    assert result.skipped == 1
    assert db.get_page(conn, "W1:0001").skip_reason == "image_missing"


def test_idempotent_resume_and_redo(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 3), ("W2", 4)])
    segment_pages(conn, FakeSegmenter(), images_root=images)
    # A second run finds nothing pending.
    again = segment_pages(conn, FakeSegmenter(), images_root=images)
    assert again.considered == 0
    # --redo re-processes and does not duplicate lines.
    redo = segment_pages(conn, FakeSegmenter(), images_root=images, redo=True)
    assert redo.segmented == 2
    assert len(db.iter_lines_for_page(conn, "W1:0001")) == 3  # not 6


def test_sample_caps_pages(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 2), ("W2", 2), ("W3", 2)])
    result = segment_pages(conn, FakeSegmenter(), images_root=images, sample=2)
    assert result.considered == 2
    assert db.count_pages_by_status(conn, "pending") == 1


def test_set_filter(tmp_path) -> None:
    conn, images = _seed(tmp_path, [("W1", 2)])
    db.upsert_work(conn, db.Work("B1", "LeibnizBriefwechsel"))
    rel = "B1/0001.jpg"
    p = images / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"JPEG" + bytes([3]))
    db.upsert_page(
        conn,
        db.Page(
            work_id="B1",
            seq=1,
            image_url="u",
            width=2000,
            height=2500,
            local_path=rel,
            sha256="shaB",
        ),
    )
    conn.commit()
    result = segment_pages(
        conn, FakeSegmenter(), images_root=images, set_name="LeibnizBriefwechsel"
    )
    assert result.segmented == 1
    assert db.get_page(conn, "W1:0001").status == "pending"  # other set untouched
