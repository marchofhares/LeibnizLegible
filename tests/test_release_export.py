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


def test_export_jsonl_all_datasets(store_path, tmp_path, monkeypatch) -> None:
    import leibniz.release.export as E

    summary = {
        "n_rows": 200,
        "n_judged": 199,
        "n_scored": 185,
        "gate": 0.95,
        "weighted_precision": 0.723,
        "weighted_usable": 0.922,
        "passes_gate": False,
    }
    monkeypatch.setattr(E, "load_audit_summary", lambda: summary)
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
    gt_card = (out / "leibniz-gt" / "README.md").read_text()
    # the scored audit, not the stale "97.5 % … preliminary (20 of 200)" of before 2026-10
    assert "precision 72.3 % as written, which fails the 95 % gate" in gt_card
    assert "92.2 %" in gt_card and "preliminary" not in gt_card and "97.5" not in gt_card
    assert "`channel ia`" in gt_card


def test_gt_card_without_a_scored_audit_quotes_no_number() -> None:
    from leibniz.release.cards import GT_AUDIT_NOTE, gt_audit_note

    assert gt_audit_note(None) == GT_AUDIT_NOTE
    assert not any(ch.isdigit() for ch in GT_AUDIT_NOTE)


def test_export_chunks_and_empty_tables(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    conn.execute("DELETE FROM gt_lines")
    conn.commit()
    exp = export_dataset(conn, "transcriptions", tmp_path, fmt="jsonl", chunk_rows=3)
    assert [f.rows for f in exp.files if f.path.startswith("lines-")] == [3, 3, 1]
    # the inventory rides inside the record (REL1), each table chunked the same way
    assert [f.rows for f in exp.files if f.path.startswith("pages-")] == [3, 1]
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


def test_gt_export_gives_each_line_one_line_of_text() -> None:
    from leibniz import db
    from leibniz.align.pairs import GtPair, insert_gt_pairs
    from leibniz.release.export import iter_gt

    conn = db.init_db(":memory:")
    insert_gt_pairs(
        conn, [GtPair("P:0001:000", "J'ay fait\ncorriger", "src", "fair_copy", 0.9, "open")]
    )
    (row,) = list(iter_gt(conn))
    assert row["text"] == "J'ay fait corriger"


def test_gt_export_keeps_reader_rows_labelled_by_source() -> None:
    from leibniz import db
    from leibniz.align.pairs import GtPair, insert_gt_pairs
    from leibniz.release.export import iter_gt

    k2 = "AA I,3 N.7 (§70-expired AA reading text; reader trocr-kurrent-xvi-xvii; katalog R7)"
    conn = db.init_db(":memory:")
    insert_gt_pairs(conn, [GtPair("P:0001:000", "vnd daß", k2, "fair_copy", 0.9, "open", "R7")])
    (row,) = list(iter_gt(conn))
    assert row["source"] == k2 and row["text"] == "vnd daß"


# ---- the two ground-truth deposits (L1) --------------------------------------- #


def _seed_channels(conn) -> None:
    from leibniz.align.pairs import GtPair, insert_gt_pairs

    def src(label: str, channel: str | None, rec: str, reader: str | None = None) -> str:
        via = f"; channel {channel}" if channel else ""
        by = f"; reader {reader}" if reader else ""
        return f"{label} (§70-expired AA reading text{via}{by}; katalog {rec})"

    insert_gt_pairs(
        conn,
        [
            GtPair("P:0001:000", "ia one", src("AA I,9 N.1", "ia", "1"), "fair_copy", 0.9, "open"),
            GtPair("P:0001:001", "ia two", src("AA I,9 N.1", "ia", "1"), "fair_copy", 0.9, "open"),
            GtPair(
                "P:0002:000", "potsdam", src("AA IV,1 N.2", "potsdam", "2"), "scrap", 0.9, "open"
            ),
            GtPair(
                "P:0003:000", "joined", src("AA I,9 N.3", "ia+gwlb", "3"), "fair_copy", 0.9, "open"
            ),
            GtPair(
                "P:0004:000",
                "vnd daß",
                src("AA I,3 N.4", "gwlb", "4", "trocr-kurrent-xvi-xvii"),
                "heavy_revision",
                0.8,
                "open",
            ),
            GtPair("P:0005:000", "old", "AA VI,4 N.109", "fair_copy", 0.9, "open"),
            GtPair(
                "P:0006:000", "pool", "letter 1714 N.1 (channel letterpool)", "unknown", 0.9, "nc"
            ),
        ],
    )


def test_gt_deposits_follow_the_channel_and_the_cards_count_them(tmp_path) -> None:
    from leibniz.release.export import (
        DATASETS,
        GT_DATASETS,
        export_dataset,
        gt_deposit_census,
        iter_gt,
        iter_gt_nc,
    )

    assert "gt-nc" in DATASETS and GT_DATASETS == {"gt": "open", "gt-nc": "nc"}
    conn = db.init_db(":memory:")
    _seed_channels(conn)
    open_rows = list(iter_gt(conn))
    nc_rows = list(iter_gt_nc(conn))
    assert [r["text"] for r in open_rows] == ["ia one", "ia two", "old"]
    assert [r["text"] for r in nc_rows] == ["potsdam", "joined", "vnd daß"]
    census = gt_deposit_census(conn)
    assert census == {
        "open": {"ia": 2, "(not recorded)": 1},
        "nc": {"potsdam": 1, "ia+gwlb": 1, "gwlb": 1},
        "none": {"letterpool": 1},
        "rows": 7,
    }

    exp_open = export_dataset(conn, "gt", tmp_path, fmt="jsonl")
    exp_nc = export_dataset(conn, "gt-nc", tmp_path, fmt="jsonl")
    assert exp_open.row_counts == {"gt_lines": 3} and exp_nc.row_counts == {"gt_lines": 3}
    assert exp_nc.out_dir.name == "leibniz-gt-nc"
    card = (tmp_path / "leibniz-gt" / "README.md").read_text()
    nc_card = (tmp_path / "leibniz-gt-nc" / "README.md").read_text()
    assert "**License:** CC BY 4.0 (the open deposit" in card
    assert "**License:** CC BY-NC 4.0 (the NC-derived deposit" in nc_card
    assert "`ia` 2" in card and "`(not recorded)` 1" in card
    assert "Left to the other deposit (`leibniz-gt-nc`): 3 lines" in card
    assert "released in neither" in card and "1 of 7 rows" in card
    assert "`potsdam` 1" in nc_card and "`gwlb` 1" in nc_card and "`ia+gwlb` 1" in nc_card
    assert "Left to the other deposit (`leibniz-gt`): 3 lines" in nc_card
    assert "stated in writing" in nc_card and "2026-10-12" in nc_card  # the Potsdam channel
    assert "Repositorium des Leibniz-Archivs" in nc_card
    for text in (card, nc_card):
        assert "## Licence" in text and "do not ingest as verified text" in text
        assert "`channel ia`" in text  # the provenance note names the channels
    # the citation line carries the deposit's licence alone
    assert "Licensed CC BY 4.0." in card and "Licensed CC BY-NC 4.0." in nc_card


def test_cards_take_their_licence_lines_from_the_registry() -> None:
    from leibniz import legal
    from leibniz.release.cards import CARD_META

    assert CARD_META["transcriptions"]["license"] == legal.output("transcriptions").licence
    assert CARD_META["inventory"]["license"] == legal.output("inventory").licence
    assert CARD_META["gt"]["license"].startswith(legal.deposit_licence("open") + " ")
    assert CARD_META["gt-nc"]["license"].startswith(legal.deposit_licence("nc") + " ")
    for meta in CARD_META.values():
        assert meta["output"] in {o.key for o in legal.OUTPUTS}


# ---- the first releases (REL1) -------------------------------------------------- #


def test_transcriptions_record_carries_the_inventory_and_its_counts(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    exp = export_dataset(conn, "transcriptions", tmp_path, fmt="jsonl")
    assert exp.row_counts == {
        "lines": 7,
        "works": 2,
        "pages": 4,
        "crosswalk": 1,
        "katalog_records": 1,
    }
    manifest = json.loads((tmp_path / "leibniz-transcriptions" / "MANIFEST.json").read_text())
    assert manifest["manifest_version"] == 2
    assert manifest["tables"] == ["lines", "works", "pages", "crosswalk", "katalog_records"]
    counts = manifest["counts"]["lines"]
    # the lines by model are counted as they are written: 6 of the first run, 1 re-read
    assert counts["by_model"] == {"htr@v1": 6, "leibniz-htr-v2@v2": 1}
    assert sum(counts["by_model"].values()) == manifest["row_counts"]["lines"]
    assert counts["pages_with_lines"] == 3 and counts["by_status"] == {"machine": 7}
    assert manifest["corpus"]["works"] == 2 and manifest["corpus"]["pages"] == 4
    assert manifest["corpus"]["katalog"] == {"records": 1, "refreshed": None}
    # one deposit file beside the folder, never inside it
    assert (tmp_path / "leibniz-transcriptions.zenodo.json").exists()
    assert not list((tmp_path / "leibniz-transcriptions").glob("*.zenodo.json"))


def test_transcriptions_are_read_along_the_page_index_without_a_sort(store_path) -> None:
    from leibniz.release.export import TRANSCRIPTIONS_SQL

    conn = db.connect(store_path)
    plan = " | ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + TRANSCRIPTIONS_SQL))
    assert "ix_lines_page" in plan
    assert "TEMP B-TREE" not in plan.upper()  # 13 million rows of geometry are not sorted


def test_chunks_are_streamed_not_held(tmp_path) -> None:
    from leibniz.release.export import _chunks

    seen: list[int] = []

    def rows():
        for i in range(7):
            seen.append(i)
            yield {"i": i}

    chunks = _chunks(rows(), 3)
    first = next(chunks)
    assert seen == [0]  # nothing beyond the head is pulled before the writer asks
    assert [r["i"] for r in first] == [0, 1, 2]
    assert [[r["i"] for r in c] for c in chunks] == [[3, 4, 5], [6]]


def test_a_scoped_run_exports_its_row_with_model_and_run(store_path, tmp_path) -> None:
    """K4's precedence in the export: a page with a scoped German run exports the
    scoped row on the lines that run wrote, the first model's on the others."""
    from tests.test_current_rule import P1, _scoped_store

    conn, de, v3 = _scoped_store(store_path)
    conn.commit()
    exp = export_dataset(conn, "transcriptions", tmp_path, fmt="jsonl")
    rows = {
        r["line_id"]: r for r in _rows(tmp_path / "leibniz-transcriptions" / "lines-0001.jsonl.gz")
    }
    scoped = rows[f"{P1}:000"]
    assert scoped["text"] == "Calculemus sagt Leibniz" and scoped["run_id"] == de
    assert scoped["model"] == "k3" and scoped["run_at"]
    assert rows[f"{P1}:001"]["run_id"] not in (de, v3)  # the scoped run did not write it
    by_run = {r["run_id"]: r for r in exp.counts["lines"]["by_run"]}
    assert by_run[de]["lines"] == 2
    card = (tmp_path / "leibniz-transcriptions" / "README.md").read_text()
    assert f"run {de} (`k3`, scope `de`): 2 lines" in card


def test_release_export_cli_opens_the_store_read_only(store_path, tmp_path) -> None:
    import hashlib

    from typer.testing import CliRunner

    from leibniz.cli import app

    before = hashlib.sha256(store_path.read_bytes()).hexdigest()
    r = CliRunner().invoke(
        app,
        [
            "release",
            "export",
            "--db",
            str(store_path),
            "--out",
            str(tmp_path / "o"),
            "--format",
            "jsonl",
        ],
    )
    assert r.exit_code == 0, r.output
    assert hashlib.sha256(store_path.read_bytes()).hexdigest() == before
    # a read-only connection to a WAL store may leave an empty -wal beside it, never a
    # written one
    wal = store_path.with_name(store_path.name + "-wal")
    assert not wal.exists() or wal.stat().st_size == 0
    missing = CliRunner().invoke(
        app, ["release", "export", "--db", str(tmp_path / "none.sqlite"), "--out", str(tmp_path)]
    )
    assert missing.exit_code != 0 and not (tmp_path / "none.sqlite").exists()
