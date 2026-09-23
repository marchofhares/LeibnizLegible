"""Sheet-side duplicate detection: fixture JPEG copied, recompressed and flipped."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app
from leibniz.images.duplicates import dhash, find_duplicates, hamming, render_report

FIX = Path(__file__).parent / "fixtures" / "images" / "thumb_sample.jpg"
runner = CliRunner()
pytest.importorskip("PIL")


def _store(tmp_path: Path) -> tuple[Path, Path]:
    from PIL import Image, ImageOps

    db_path = tmp_path / "inv.sqlite"
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("00000001", "LeibnizHandschriften", n_canvases=5))
    thumbs = tmp_path / "thumbs" / "00000001"
    thumbs.mkdir(parents=True)
    # 1: the fixture; 2: a different picture (flipped); 3: a recompressed copy of 1
    # (the second folio label of the same sheet-side); 4: a copy of 2; 5: no thumbnail.
    shutil.copy(FIX, thumbs / "0001.jpg")
    with Image.open(FIX) as im:
        ImageOps.flip(im).save(thumbs / "0002.jpg", quality=70)
        im.convert("RGB").save(thumbs / "0003.jpg", quality=55)
    shutil.copy(thumbs / "0002.jpg", thumbs / "0004.jpg")
    for seq in range(1, 6):
        db.upsert_page(conn, db.Page(work_id="00000001", seq=seq, label=f"{(seq + 1) // 2}r"))
        db.mark_page_fetched(
            conn,
            f"00000001:{seq:04d}",
            local_path=f"00000001/{seq:04d}.jpg",
            n_bytes=1,
            sha256="x",
            width=118,
            height=150,
        )
    conn.commit()
    conn.close()
    return db_path, tmp_path / "thumbs"


def test_dhash_is_stable_under_recompression_and_distinguishes_pictures(tmp_path) -> None:
    db_path, thumbs = _store(tmp_path)
    a, b, c = (dhash(thumbs / "00000001" / f"{n:04d}.jpg") for n in (1, 2, 3))
    assert hamming(a, c) <= 4
    assert hamming(a, b) > 8


def test_find_duplicates_pairs_the_sheet_sides(tmp_path) -> None:
    db_path, thumbs = _store(tmp_path)
    conn = db.init_db(db_path)
    try:
        stats = find_duplicates(conn, thumbs, window=3, max_distance=4)
    finally:
        conn.close()
    pairs = {(p.page_a, p.page_b) for p in stats.pairs}
    assert pairs == {("00000001:0001", "00000001:0003"), ("00000001:0002", "00000001:0004")}
    assert stats.pages_hashed == 4 and stats.pages_missing == 1 and stats.works == 1
    assert len(stats.pages_in_pairs) == 4
    report = render_report(stats, window=3, max_distance=4)
    assert "Duplicate pairs:** 2" in report and "LeibnizHandschriften" in report


def test_cli_duplicates_writes_report_and_pairs(tmp_path) -> None:
    db_path, thumbs = _store(tmp_path)
    report = tmp_path / "duplicates.md"
    pairs = tmp_path / "pairs.jsonl"
    r = runner.invoke(
        app,
        [
            "images",
            "duplicates",
            "--db",
            str(db_path),
            "--thumbs",
            str(thumbs),
            "--window",
            "3",
            "--report",
            str(report),
            "--pairs",
            str(pairs),
        ],
    )
    assert r.exit_code == 0, r.output
    assert "2 duplicate pairs" in r.output
    assert report.exists() and len(pairs.read_text().splitlines()) == 2
