"""Tests for the corpus recognition stage (offline; fake cropper + recogniser)."""

from __future__ import annotations

from pathlib import Path

from leibniz import db
from leibniz.layout.segment import SegLine, SegmentedPage
from leibniz.pipeline.recognize import recognize_pages
from leibniz.pipeline.segment import segment_pages


class FakeSegmenter:
    """Segment + crop. Line count encoded in the last image byte."""

    def segment(self, image: bytes) -> SegmentedPage:
        n = image[-1]
        lines = [
            SegLine(index=i, baseline=[(50, 140 + i * 120), (1950, 140 + i * 120)], boundary=[])
            for i in range(n)
        ]
        return SegmentedPage(lines=lines, width=2000, height=2500, n_regions=1 if n else 0)

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        return [f"crop{ln.index}".encode() for ln in page.lines]


class ShortCropper(FakeSegmenter):
    """Returns one fewer crop than lines, to test count-drift handling."""

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        return [f"crop{ln.index}".encode() for ln in page.lines][:-1]


class FakeRecognizer:
    version = "philiumm-htr@v1"

    def __init__(self, *, boom: bool = False) -> None:
        self.boom = boom

    def transcribe_conf(self, images):
        if self.boom:
            raise RuntimeError("htr exploded")
        return [(f"text {img.decode()}", 0.9) for img in images]


def _seed_segmented(tmp_path: Path, spec: list[tuple[str, int]]):
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
                sha256=f"sha{i}",
            ),
        )
    conn.commit()
    segment_pages(conn, FakeSegmenter(), images_root=images)
    return conn, images


def test_recognize_fills_text_conf_and_provenance(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [("W1", 3)])
    result = recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images)
    assert result.recognized == 1 and result.n_lines == 3
    assert db.count_pages_by_status(conn, "recognized") == 1
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert lines[0].text == "text crop0"
    assert lines[0].conf == 0.9
    assert lines[0].model == "philiumm-htr@v1"
    # run_id repoints at the recognition run (text provenance, SPECS §4.5)
    assert lines[0].run_id == result.run_id
    assert lines[0].source["stage"] == "recognize"


def test_recognizer_error_isolated(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [("W1", 3), ("W2", 2)])
    result = recognize_pages(conn, FakeSegmenter(), FakeRecognizer(boom=True), images_root=images)
    assert result.recognized == 0 and result.skipped == 2
    assert all("htr exploded" in r for _pid, r in result.failures)
    # text never written on failure
    assert db.iter_lines_for_page(conn, "W1:0001")[0].text is None


def test_crop_count_drift_is_partial_not_fatal(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [("W1", 4)])
    result = recognize_pages(conn, ShortCropper(), FakeRecognizer(), images_root=images)
    assert result.recognized == 1
    assert result.n_lines == 3  # one line unrecognised
    assert any("partial" in r for _pid, r in result.failures)
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert lines[3].text is None  # last line left untranscribed


def test_recognize_resume_and_redo(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [("W1", 3), ("W2", 2)])
    recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images)
    again = recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images)
    assert again.considered == 0  # nothing left segmented
    redo = recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images, redo=True)
    assert redo.recognized == 2


def test_full_state_machine_histogram(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [("W1", 3), ("W2", 2), ("W3", 4)])
    recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images)
    assert db.status_histogram(conn) == {"recognized": 3}
    assert db.count_lines(conn, recognized=True) == 9
