"""Tests for the GT loaders (offline; parquet path guarded on pyarrow)."""

from __future__ import annotations

import pytest

from leibniz.htr import data


def _make_line_dir(tmp_path):
    d = tmp_path / "lines"
    d.mkdir()
    (d / "l1.png").write_bytes(b"IMG1")
    (d / "l1.gt.txt").write_text("prima linea\n", encoding="utf-8")
    (d / "l2.png").write_bytes(b"IMG2")
    (d / "l2.txt").write_text("secunda linea", encoding="utf-8")  # plain .txt sidecar
    (d / "l3.png").write_bytes(b"IMG3")  # no sidecar -> skipped
    return d


def test_load_image_text_dir_pairs_and_skips(tmp_path) -> None:
    d = _make_line_dir(tmp_path)
    pairs = data.load_image_text_dir(d)
    ids = [p.line_id for p in pairs]
    assert ids == ["line:l1", "line:l2"]  # l3 skipped (no sidecar)
    assert pairs[0].reference == "prima linea"
    assert pairs[0].image_bytes() == b"IMG1"
    assert pairs[1].reference == "secunda linea"


def test_load_image_text_dir_limit_and_langmap(tmp_path) -> None:
    d = _make_line_dir(tmp_path)
    pairs = data.load_image_text_dir(d, limit=1, lang_map={"l1": "la"})
    assert len(pairs) == 1
    assert pairs[0].lang == "la"


def test_subsample_deterministic_and_capped() -> None:
    from leibniz.htr.bench import LinePair

    pairs = [LinePair(line_id=str(i), reference="x", image_bytes_=b"") for i in range(100)]
    a = data.subsample(pairs, 10, seed=1)
    b = data.subsample(pairs, 10, seed=1)
    assert [p.line_id for p in a] == [p.line_id for p in b]  # deterministic
    assert len(a) == 10
    # ids returned in ascending index order
    assert [int(p.line_id) for p in a] == sorted(int(p.line_id) for p in a)
    # n >= len returns everything
    assert len(data.subsample(pairs, 500)) == 100


def test_image_cell_bytes_variants() -> None:
    assert data._image_cell_bytes(None) is None
    assert data._image_cell_bytes(b"raw") == b"raw"
    assert data._image_cell_bytes({"bytes": b"x", "path": None}) == b"x"
    assert data._image_cell_bytes({"bytes": None}) is None


def test_load_parquet_pairs_roundtrip(tmp_path) -> None:
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq

    # Build a tiny HF-style parquet: text column + image struct {bytes, path}.
    texts = ["alpha", "", "gamma"]  # middle row empty -> skipped by default
    imgs = [
        {"bytes": b"A", "path": None},
        {"bytes": b"B", "path": None},
        {"bytes": b"C", "path": None},
    ]
    table = pa.table({"text": pa.array(texts), "image": pa.array(imgs)})
    path = tmp_path / "val.parquet"
    pq.write_table(table, path)

    pairs = data.load_parquet_pairs(path)
    assert [p.reference for p in pairs] == ["alpha", "gamma"]  # empty skipped
    assert pairs[0].image_bytes() == b"A"
    assert pairs[0].line_id == "val:00000"
    assert pairs[1].line_id == "val:00002"  # original row index preserved

    # skip_empty=False keeps the blank row; limit caps.
    keep = data.load_parquet_pairs(path, skip_empty=False)
    assert len(keep) == 3
    assert len(data.load_parquet_pairs(path, limit=1)) == 1
