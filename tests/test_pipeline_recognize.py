"""Tests for the corpus recognition stage (offline; fake cropper + recogniser)."""

from __future__ import annotations

import time
import warnings
from pathlib import Path

import pytest

from leibniz import db
from leibniz.layout.segment import SegLine, SegmentedPage, _pil_transform_warnings_as_errors
from leibniz.pipeline.recognize import _dedupe_pts, audit_page, recognize_pages
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
    assert any("not transcribed" in r for _pid, r in result.failures)
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


def test_degenerate_baseline_skips_line_not_whole_page(tmp_path) -> None:
    # One sub-5px baseline (what makes kraken raise "Baseline length below minimum
    # 5px") must cost that line only — the page's other lines still recognise.
    images = tmp_path / "images"
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("W1", "LeibnizHandschriften"))
    rel = "W1/0001.jpg"
    p = images / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"JPEG")
    db.upsert_page(
        conn,
        db.Page(
            work_id="W1",
            seq=1,
            image_url="u",
            width=2000,
            height=2500,
            local_path=rel,
            sha256="s",
            status="segmented",
        ),
    )
    rid = db.start_run(conn, "segment", model="seg")
    for seq, baseline in (
        (0, [[50, 140], [1950, 140]]),  # good
        (1, [[50, 260], [51, 261]]),  # ~1.4px — degenerate
        (2, [[50, 380], [1950, 380]]),  # good
    ):
        db.insert_line(
            conn,
            db.Line(
                page_id="W1:0001", line_seq=seq, baseline=baseline, run_id=rid, status="machine"
            ),
        )
    conn.commit()

    result = recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images)
    assert result.recognized == 1  # page recognised, NOT skipped
    assert result.n_lines == 2  # only the two good lines transcribed
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert lines[0].text is not None
    assert lines[1].text is None  # degenerate line left untranscribed
    assert lines[2].text is not None
    assert db.get_page(conn, "W1:0001").status == "recognized"


def _seed_one_page(
    tmp_path: Path,
    baselines: list[list[list[float]]],
    polygons: list[list[list[float]] | None] | None = None,
):
    """One segmented page with hand-built line geometry (no FakeSegmenter pass)."""
    images = tmp_path / "images"
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work("W1", "LeibnizHandschriften"))
    rel = "W1/0001.jpg"
    p = images / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"JPEG")
    db.upsert_page(
        conn,
        db.Page(
            work_id="W1",
            seq=1,
            image_url="u",
            width=2000,
            height=2500,
            local_path=rel,
            sha256="s",
            status="segmented",
        ),
    )
    rid = db.start_run(conn, "segment", model="seg")
    for seq, baseline in enumerate(baselines):
        db.insert_line(
            conn,
            db.Line(
                page_id="W1:0001",
                line_seq=seq,
                baseline=baseline,
                polygon=polygons[seq] if polygons else None,
                run_id=rid,
                status="machine",
            ),
        )
    conn.commit()
    return conn, images


def test_dedupe_pts_collapses_same_pixel_points() -> None:
    # A zero-length segment (exact or sub-pixel duplicate) is what becomes the
    # zero-width dewarping quad PIL NaNs out on; total length can't see it.
    assert _dedupe_pts([[50, 140], [50, 140], [1950, 140]]) == [(50.0, 140.0), (1950.0, 140.0)]
    assert _dedupe_pts([[50, 140], [50.4, 140.2], [1950, 140]]) == [(50.0, 140.0), (1950.0, 140.0)]
    assert _dedupe_pts(None) == []


class RecordingCropper(FakeSegmenter):
    """Captures the SegmentedPage the pipeline hands to crop_lines."""

    def __init__(self) -> None:
        self.pages: list[SegmentedPage] = []

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        self.pages.append(page)
        return super().crop_lines(image, page)


def test_duplicate_baseline_points_sanitized_before_cropping(tmp_path) -> None:
    conn, images = _seed_one_page(
        tmp_path,
        [[[50, 140], [50.4, 140.2], [1950, 140]]],  # sub-pixel duplicate
    )
    cropper = RecordingCropper()
    result = recognize_pages(conn, cropper, FakeRecognizer(), images_root=images)
    assert result.recognized == 1 and result.n_lines == 1
    assert cropper.pages[0].lines[0].baseline == [(50.0, 140.0), (1950.0, 140.0)]
    assert db.iter_lines_for_page(conn, "W1:0001")[0].text is not None


class PoisonLineCropper(FakeSegmenter):
    """Raises whenever the crop batch contains line index 1 (the poison line).

    Mimics the live failure: kraken's ``extract_polygons`` dying on one line's
    degenerate quad geometry, whether cropped with the page or alone.
    """

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        if any(ln.index == 1 for ln in page.lines):
            raise RuntimeError("zero-width quad")
        return super().crop_lines(image, page)


def test_poison_line_costs_the_line_not_the_page(tmp_path) -> None:
    good = [[50, 140], [1950, 140]]
    conn, images = _seed_one_page(tmp_path, [good, [[50, 260], [1950, 260]], good])
    result = recognize_pages(conn, PoisonLineCropper(), FakeRecognizer(), images_root=images)
    assert result.recognized == 1 and result.skipped == 0
    assert result.n_lines == 2  # poison line dropped by the per-line fallback
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert lines[0].text is not None
    assert lines[1].text is None  # the poison line, left untranscribed
    assert lines[2].text is not None
    assert db.get_page(conn, "W1:0001").status == "recognized"
    assert any("not transcribed" in r for _pid, r in result.failures)


class AlwaysPoisonCropper(FakeSegmenter):
    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        raise RuntimeError("zero-width quad")


def test_all_lines_poison_skips_page_with_reason(tmp_path) -> None:
    conn, images = _seed_one_page(tmp_path, [[[50, 140], [1950, 140]]])
    result = recognize_pages(conn, AlwaysPoisonCropper(), FakeRecognizer(), images_root=images)
    assert result.recognized == 0 and result.skipped == 1
    page = db.get_page(conn, "W1:0001")
    assert page.status == "skipped"
    assert "no line survived polygon extraction" in page.skip_reason


def test_pil_transform_warning_guard_escalates_only_pil() -> None:
    # The PIL-attributed RuntimeWarning must raise (a NaN'd transform never
    # yields a usable crop; unraised it can hang the C rasterizer)…
    with pytest.raises(RuntimeWarning), _pil_transform_warnings_as_errors():
        warnings.warn_explicit(
            "divide by zero encountered in divide",
            RuntimeWarning,
            "PIL/Image.py",
            3045,
            module="PIL.Image",
        )
    # …while the same warning from anywhere else stays a warning.
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        with _pil_transform_warnings_as_errors():
            warnings.warn_explicit(
                "benign elsewhere", RuntimeWarning, "numpy/core.py", 1, module="numpy.core"
            )
    assert len(rec) == 1


# Geometry whose rectified extents kraken would turn into a giant allocation
# (the OOM-kill class): axially deep inside a segment, far perpendicular.
_POISON_BL = [[0, 0], [1900, 0], [1900, 1]]
_POISON_POLY = [[5, -9000], [1800, 9000], [30, 10]]


def test_oversize_geometry_costs_the_line_not_the_page(tmp_path) -> None:
    sane = [[50, 140], [1950, 140]]
    conn, images = _seed_one_page(tmp_path, [sane, _POISON_BL], polygons=[None, _POISON_POLY])
    result = recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=images)
    assert result.recognized == 1 and result.skipped == 0
    assert result.n_lines == 1  # the oversize line was guarded out before cropping
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert lines[0].text is not None
    assert lines[1].text is None
    assert any("oversize_crop" in r for _pid, r in result.failures)


class HangingCropper(FakeSegmenter):
    """Stalls in crop_lines, standing in for an in-process kraken/PIL freeze."""

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        time.sleep(5)
        return super().crop_lines(image, page)


def test_crop_deadline_converts_stall_to_skip(tmp_path, monkeypatch) -> None:
    from leibniz.pipeline import recognize as rec_mod

    monkeypatch.setattr(rec_mod, "CROP_PAGE_DEADLINE_S", 0.05)
    monkeypatch.setattr(rec_mod, "CROP_LINE_DEADLINE_S", 0.05)
    conn, images = _seed_one_page(tmp_path, [[[50, 140], [1950, 140]]])
    result = recognize_pages(conn, HangingCropper(), FakeRecognizer(), images_root=images)
    assert result.skipped == 1 and result.recognized == 0
    page = db.get_page(conn, "W1:0001")
    assert page.status == "skipped"
    assert "no line survived polygon extraction" in page.skip_reason


def test_wrong_images_root_aborts_before_marking(tmp_path) -> None:
    # An omitted/mistyped --images once mass-marked 235k cached pages as
    # image_missing; with ≥5 cached pages and zero files present, abort instead.
    conn, images = _seed_segmented(tmp_path, [(f"W{i}", 2) for i in range(1, 7)])
    with pytest.raises(FileNotFoundError, match="wrong --images root"):
        recognize_pages(conn, FakeSegmenter(), FakeRecognizer(), images_root=tmp_path / "nowhere")
    assert db.count_pages_by_status(conn, "segmented") == 6  # statuses untouched


def _seed_pending_cached(tmp_path, n: int = 6):
    images = tmp_path / "images"
    conn = db.init_db(":memory:")
    for i in range(1, n + 1):
        wid = f"W{i}"
        db.upsert_work(conn, db.Work(wid, "LeibnizHandschriften"))
        rel = f"{wid}/0001.jpg"
        p = images / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"JPEG\x02")
        db.upsert_page(
            conn, db.Page(work_id=wid, seq=1, image_url="u", local_path=rel, sha256=f"s{i}")
        )
    conn.commit()
    return conn, images


def test_segment_wrong_images_root_aborts(tmp_path) -> None:
    conn, images = _seed_pending_cached(tmp_path)
    with pytest.raises(FileNotFoundError, match="wrong --images root"):
        segment_pages(conn, FakeSegmenter(), images_root=tmp_path / "nowhere")
    assert db.count_pages_by_status(conn, "pending") == 6  # statuses untouched


def test_oversize_image_skipped_with_reason(tmp_path, monkeypatch) -> None:
    from leibniz.pipeline import segment as segment_mod

    conn, images = _seed_pending_cached(tmp_path, n=1)
    monkeypatch.setattr(segment_mod, "jpeg_dimensions", lambda data: (12000, 11000))  # 132 MPx
    result = segment_pages(conn, FakeSegmenter(), images_root=images)
    assert result.segmented == 0 and result.skipped == 1
    page = db.get_page(conn, "W1:0001")
    assert page.status == "skipped"
    assert page.skip_reason == "oversize_image:12000x11000"


def test_shards_are_disjoint_and_complete(tmp_path) -> None:
    # 3 workers each running their shard must together make exactly one full
    # pass: every page done once, none twice, none missed.
    conn, images = _seed_pending_cached(tmp_path, n=12)
    total = 0
    for i in range(3):
        r = segment_pages(conn, FakeSegmenter(), images_root=images, shard=(i, 3))
        total += r.considered
    assert total == 12
    assert db.count_pages_by_status(conn, "segmented") == 12
    # A re-run of any shard finds nothing left.
    again = segment_pages(conn, FakeSegmenter(), images_root=images, shard=(0, 3))
    assert again.considered == 0


def test_recognize_shard_matches_segment_shard(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [(f"W{i}", 2) for i in range(1, 7)])
    done = 0
    for i in range(2):
        r = recognize_pages(
            conn, FakeSegmenter(), FakeRecognizer(), images_root=images, shard=(i, 2)
        )
        done += r.recognized
    assert done == 6
    assert db.count_pages_by_status(conn, "recognized") == 6


def test_audit_page_names_the_poison_line(tmp_path) -> None:
    sane = [[50, 140], [1950, 140]]
    conn, images = _seed_one_page(tmp_path, [sane, _POISON_BL], polygons=[None, _POISON_POLY])
    rows = audit_page(conn, db.get_page(conn, "W1:0001"))
    assert rows[0]["verdict"] == "ok"
    assert rows[1]["verdict"].startswith("oversize_crop")
    assert rows[1]["est_mpx"] > 24  # would dwarf the 24 MPx floor / 20 MPx page cap


def _png(w: int, h: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + (13).to_bytes(4, "big")
        + b"IHDR"
        + w.to_bytes(4, "big")
        + h.to_bytes(4, "big")
        + b"\x00" * 5
    )


class SliverCropper(FakeSegmenter):
    """Emits a real-header PNG sliver for line 1, normal fake crops otherwise.

    Mimics the live killer: geometry looked sane, but the dewarped crop was a
    ~900×1 mask stripe that would explode the recogniser's conv allocation.
    """

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]:
        return [_png(900, 1) if ln.index == 1 else f"crop{ln.index}".encode() for ln in page.lines]


def test_sliver_crop_dropped_before_recognition(tmp_path) -> None:
    conn, images = _seed_segmented(tmp_path, [("W1", 3)])
    result = recognize_pages(conn, SliverCropper(), FakeRecognizer(), images_root=images)
    assert result.recognized == 1 and result.skipped == 0
    assert result.n_lines == 2  # the sliver never reached the recogniser
    lines = db.iter_lines_for_page(conn, "W1:0001")
    assert lines[0].text is not None
    assert lines[1].text is None
    assert lines[2].text is not None
    assert any("sliver_crop:900x1" in r for _pid, r in result.failures)
