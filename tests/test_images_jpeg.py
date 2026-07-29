"""Tests for the dependency-free JPEG inspector (dimensions + truncation)."""

from __future__ import annotations

from pathlib import Path

from leibniz.images import jpeg

SAMPLE = (Path(__file__).parent / "fixtures" / "images" / "thumb_sample.jpg").read_bytes()


def test_is_jpeg() -> None:
    assert jpeg.is_jpeg(SAMPLE)
    assert not jpeg.is_jpeg(b"not a jpeg")
    assert not jpeg.is_jpeg(b"")
    assert not jpeg.is_jpeg(b"\xff")  # too short


def test_dimensions_of_real_thumbnail() -> None:
    # A real GWLB delivery thumbnail (public domain); dims read straight off the SOF.
    assert jpeg.jpeg_dimensions(SAMPLE) == (118, 150)


def test_dimensions_none_for_non_jpeg() -> None:
    assert jpeg.jpeg_dimensions(b"PNG\x89 or whatever") is None
    assert jpeg.jpeg_dimensions(b"") is None


def test_complete_jpeg_true_for_whole_file() -> None:
    assert jpeg.is_complete_jpeg(SAMPLE)


def test_complete_jpeg_tolerates_trailing_padding() -> None:
    assert jpeg.is_complete_jpeg(SAMPLE + b"\x00\x00\xff")


def test_truncated_jpeg_is_incomplete() -> None:
    # A dropped connection keeps the SOI but loses the trailing EOI.
    assert jpeg.is_jpeg(SAMPLE[:200])
    assert not jpeg.is_complete_jpeg(SAMPLE[:200])


def test_empty_and_garbage_are_incomplete() -> None:
    assert not jpeg.is_complete_jpeg(b"")
    assert not jpeg.is_complete_jpeg(b"\xff\xd8plainly not finished")
