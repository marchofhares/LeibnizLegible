"""Dataset exports + cards (JSONL always; Parquet when pyarrow is present)."""

from __future__ import annotations

import gzip
import json

import pytest

from leibniz import db
from leibniz.release.export import DATASETS, export_all, export_dataset, iter_transcriptions

W1 = "00068642"
W2 = "DE-611-HS-854976"


def _rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_transcriptions_latest_run_and_nc_exclusion(store_path) -> None:
    conn = db.connect(store_path)
    rows = list(iter_transcriptions(conn))
    assert len(rows) == 7
    first = rows[0]
    assert first["line_id"] == f"{W1}:0001:000"
    assert first["text"] == "Calculemus inquit Leibnitius." and first["run_id"] == 3
    assert first["region_xywh"] == "100,160,1800,60" and first["image_uri"].endswith("/1.ptif")
    assert first["run_at"] and first["set"] == "LeibnizHandschriften"
    assert {r["work_id"] for r in rows} == {W1, W2}


def test_export_jsonl_all_datasets(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    out = tmp_path / "release"
    exports = export_all(
        conn, out, fmt="jsonl", stats={"works": 2, "pages": 4, "pages_recognized": 3, "lines": 8}
    )
    assert [e.dataset for e in exports] == list(DATASETS)
    inv = exports[0]
    assert inv.row_counts == {"works": 2, "pages": 4, "crosswalk": 1, "katalog_records": 1}
    manifest = json.loads((out / "leibniz-inventory" / "MANIFEST.json").read_text())
    assert manifest["row_counts"]["pages"] == 4 and manifest["files"][0]["sha256"]
    card = (out / "leibniz-inventory" / "README.md").read_text()
    assert (
        "CC0" in card and "Public Domain Mark" in card and "do not ingest as verified text" in card
    )
    lines = _rows(out / "leibniz-transcriptions" / "lines-0001.jsonl.gz")
    assert len(lines) == 7 and lines[0]["polygon"][0] == [100, 160]
    gt = _rows(out / "leibniz-gt" / "gt_lines-0001.jsonl.gz")
    assert len(gt) == 2 and all(r["license_bucket"] == "open" for r in gt)
    assert "preliminary" in (out / "leibniz-gt" / "README.md").read_text()


def test_export_chunks_and_empty_tables(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    conn.execute("DELETE FROM gt_lines")
    conn.commit()
    exp = export_dataset(conn, "transcriptions", tmp_path, fmt="jsonl", chunk_rows=3)
    assert [f.rows for f in exp.files] == [3, 3, 1]
    empty = export_dataset(conn, "gt", tmp_path, fmt="jsonl")
    assert empty.row_counts == {"gt_lines": 0} and len(empty.files) == 1


def test_export_rejects_unknown(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    with pytest.raises(ValueError):
        export_dataset(conn, "nope", tmp_path, fmt="jsonl")
    with pytest.raises(ValueError):
        export_dataset(conn, "gt", tmp_path, fmt="csv")


def test_export_parquet_roundtrip(store_path, tmp_path) -> None:
    pq = pytest.importorskip("pyarrow.parquet")
    conn = db.connect(store_path)
    exp = export_dataset(conn, "transcriptions", tmp_path, fmt="parquet")
    table = pq.read_table(tmp_path / "leibniz-transcriptions" / "lines-0001.parquet")
    assert table.num_rows == 7 and exp.row_counts["lines"] == 7
    row = table.slice(0, 1).to_pylist()[0]
    assert json.loads(row["polygon"])[0] == [100, 160] and row["conf"] == 0.95
