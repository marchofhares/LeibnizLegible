"""Thumbnails for the mirror, and the mirror check (offline: fixture JPEG + fake HTTP)."""

from __future__ import annotations

import shutil
from pathlib import Path

import httpx
from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app
from leibniz.images.thumbs import build_thumbnails, check_mirror, make_thumbnail

FIX = Path(__file__).parent / "fixtures" / "images" / "thumb_sample.jpg"  # 118 × 150
runner = CliRunner()


def _store(tmp_path: Path) -> tuple[Path, Path]:
    """A store with two cached pages (one file present, one missing) and one uncached."""
    db_path = tmp_path / "inv.sqlite"
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("00000001", "LeibnizHandschriften", n_canvases=3))
    for seq in (1, 2, 3):
        db.upsert_page(conn, db.Page(work_id="00000001", seq=seq))
    images = tmp_path / "images"
    (images / "00000001").mkdir(parents=True)
    shutil.copy(FIX, images / "00000001" / "0001.jpg")
    db.mark_page_fetched(
        conn,
        "00000001:0001",
        local_path="00000001/0001.jpg",
        n_bytes=FIX.stat().st_size,
        sha256="x",
        width=118,
        height=150,
    )
    db.mark_page_fetched(
        conn,
        "00000001:0002",
        local_path="00000001/0002.jpg",
        n_bytes=10,
        sha256="y",
        width=1,
        height=1,
    )
    conn.commit()
    conn.close()
    return db_path, images


def test_make_thumbnail_keeps_aspect(tmp_path) -> None:
    out = tmp_path / "t.jpg"
    assert make_thumbnail(FIX, out, width=59) == (59, 75)
    assert out.exists() and not out.with_name("t.jpg.part").exists()
    from PIL import Image

    with Image.open(out) as im:
        assert im.size == (59, 75) and im.format == "JPEG"
    # never upscaled
    assert make_thumbnail(FIX, tmp_path / "u.jpg", width=1000) == (118, 150)


def test_build_thumbnails_is_resumable(tmp_path) -> None:
    db_path, images = _store(tmp_path)
    out = tmp_path / "thumbs"
    conn = db.connect(db_path)
    seen: list[tuple[str, str]] = []
    s = build_thumbnails(
        conn, images, out, width=40, workers=1, progress=lambda p, o: seen.append((p, o))
    )
    assert (s.made, s.skipped, s.missing, s.failed) == (1, 0, 1, 0)
    assert (out / "00000001" / "0001.jpg").exists() and not (out / "00000001" / "0002.jpg").exists()
    assert ("00000001:0002", "missing") in seen
    s2 = build_thumbnails(conn, images, out, width=40, workers=2)
    assert (s2.made, s2.skipped, s2.missing) == (0, 1, 1)
    s3 = build_thumbnails(conn, images, out, width=40, workers=1, redo=True)
    assert s3.made == 1
    conn.close()


def test_check_mirror_reports_missing_and_sizes(tmp_path) -> None:
    db_path, _ = _store(tmp_path)
    size = FIX.stat().st_size

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD"
        path = request.url.path
        if path == "/00000001/0001.jpg":
            return httpx.Response(200, headers={"content-length": str(size)})
        if path == "/thumbs/00000001/0001.jpg":
            return httpx.Response(200, headers={"content-length": "999"})
        if path == "/00000001/0002.jpg":
            return httpx.Response(200, headers={"content-length": "11"})  # wrong size
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    conn = db.connect(db_path)
    rep = check_mirror(conn, "https://img.example/", client=client, sample=0)
    assert rep.checked == 2 and rep.ok == 1
    assert rep.size_mismatch == ["00000001:0002"] and rep.missing == []
    assert rep.thumbs_checked == 2 and rep.thumbs_missing == ["00000001:0002"]
    assert rep.complete is False and rep.to_dict()["complete"] is False
    rep2 = check_mirror(conn, "https://img.example", client=client, sample=1, thumbs=False, seed=1)
    assert rep2.checked == 1 and rep2.thumbs_checked == 0
    conn.close()


def test_cli_thumbs_and_check_mirror(tmp_path, monkeypatch) -> None:
    db_path, images = _store(tmp_path)
    out = tmp_path / "thumbs"
    r = runner.invoke(
        app,
        [
            "images",
            "thumbs",
            "--db",
            str(db_path),
            "--images",
            str(images),
            "--out",
            str(out),
            "--width",
            "40",
            "--workers",
            "1",
        ],
    )
    # one source present, one recorded-but-absent → exit 1, and it says so
    assert r.exit_code == 1, r.stdout
    assert "1 made" in r.stdout and "1 source files missing" in r.stdout
    assert "have no file under" in r.stdout

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-length": str(FIX.stat().st_size)})

    real_client = httpx.Client  # the attribute patched below is httpx's own
    monkeypatch.setattr(
        "leibniz.images.cli.httpx.Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler)),
    )
    r = runner.invoke(
        app,
        [
            "images",
            "check-mirror",
            "--db",
            str(db_path),
            "--base-url",
            "https://img.example",
            "--sample",
            "0",
        ],
    )
    # page 2's manifest says 10 bytes; the fake answers the fixture size → one mismatch → exit 1
    assert r.exit_code == 1 and "1 size mismatches" in r.stdout and "mirror incomplete" in r.stdout
    r = runner.invoke(
        app,
        [
            "images",
            "check-mirror",
            "--db",
            str(db_path),
            "--base-url",
            "https://img.example",
            "--sample",
            "0",
            "--json",
        ],
    )
    assert r.exit_code == 1 and '"complete": false' in r.stdout


def test_preflight_rejects_a_wrong_images_root(tmp_path) -> None:
    """A root holding none of the cached pages is the root's fault, not the cache's."""
    import pytest

    from leibniz.images.thumbs import build_thumbnails, preflight_images_root

    db_path = tmp_path / "inv.sqlite"
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("00000001", "LeibnizHandschriften", n_canvases=10))
    for seq in range(1, 11):
        db.upsert_page(conn, db.Page(work_id="00000001", seq=seq))
        db.mark_page_fetched(
            conn,
            f"00000001:{seq:04d}",
            local_path=f"00000001/{seq:04d}.jpg",
            n_bytes=1,
            sha256="x",
            width=1,
            height=1,
        )
    conn.commit()
    empty = tmp_path / "nowhere"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="wrong --images root"):
        preflight_images_root(conn, empty)
    with pytest.raises(FileNotFoundError):
        build_thumbnails(conn, empty, tmp_path / "t")
    # the CLI turns it into a clean message and exit 2, not a traceback
    r = runner.invoke(
        app,
        [
            "images",
            "thumbs",
            "--db",
            str(db_path),
            "--images",
            str(empty),
            "--out",
            str(tmp_path / "t"),
        ],
    )
    flat = " ".join(r.stdout.split())  # rich wraps the message across lines
    assert r.exit_code == 2 and "wrong --images root" in flat
    # fewer than five cached pages cannot distinguish the two cases: stay quiet
    conn.execute("UPDATE pages SET local_path = NULL WHERE seq > 3")
    conn.commit()
    preflight_images_root(conn, empty)
    conn.close()
