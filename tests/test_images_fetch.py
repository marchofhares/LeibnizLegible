"""Tests for the image fetcher / verifier / stats — offline via a fake client."""

from __future__ import annotations

from pathlib import Path

from leibniz import db
from leibniz.images import fetch

SAMPLE = (Path(__file__).parent / "fixtures" / "images" / "thumb_sample.jpg").read_bytes()
SAMPLE_SHA = fetch.sha256_hex(SAMPLE)


class FakeClient:
    """Serves the same JPEG bytes for every URL, counting calls per URL."""

    def __init__(self, body: bytes = SAMPLE) -> None:
        self.body = body
        self.calls: list[str] = []

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:  # noqa: ARG002
        self.calls.append(url)
        return self.body


class FlakyClient:
    """Returns a truncated body the first ``n_bad`` times, then the full JPEG."""

    def __init__(self, n_bad: int = 1) -> None:
        self.n_bad = n_bad
        self.calls = 0

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:  # noqa: ARG002
        self.calls += 1
        return SAMPLE if self.calls > self.n_bad else SAMPLE[:100]


def _seed(conn, object_id: str = "W", set_name: str = "LeibnizHandschriften", n: int = 3) -> None:
    db.upsert_work(conn, db.Work(object_id, set_name, n_canvases=n))
    base = "https://digitale-sammlungen.gwlb.de/content"
    for seq in range(1, n + 1):
        db.upsert_page(
            conn,
            db.Page(
                work_id=object_id,
                seq=seq,
                image_url=f"{base}/{object_id}/jpgs/default/{seq:08d}.jpg",
                delivery="static",
            ),
        )


# -- fetch ------------------------------------------------------------------ #


def test_fetch_downloads_checksums_and_reads_dims(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=2)
    stats = fetch.fetch_images(
        conn, client=FakeClient(), images_root=tmp_path, sleep=lambda _s: None
    )

    assert stats.fetched == 2 and stats.skipped == 0 and not stats.failures
    page = db.get_page(conn, "W:0001")
    assert page.is_cached
    assert page.sha256 == SAMPLE_SHA
    assert page.n_bytes == len(SAMPLE)
    assert (page.width, page.height) == (118, 150)  # read off the JPEG
    assert (tmp_path / "W" / "0001.jpg").read_bytes() == SAMPLE


def test_fetch_is_resumable(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=2)
    fetch.fetch_images(conn, client=FakeClient(), images_root=tmp_path, sleep=lambda _s: None)
    # Second run: everything already cached → nothing re-downloaded.
    client = FakeClient()
    stats = fetch.fetch_images(conn, client=client, images_root=tmp_path, sleep=lambda _s: None)
    assert stats.fetched == 0 and stats.skipped == 2
    assert client.calls == []


def test_fetch_redo_forces_redownload(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=1)
    fetch.fetch_images(conn, client=FakeClient(), images_root=tmp_path, sleep=lambda _s: None)
    client = FakeClient()
    stats = fetch.fetch_images(
        conn, client=client, images_root=tmp_path, redo=True, sleep=lambda _s: None
    )
    assert stats.fetched == 1 and client.calls  # re-hit the network


def test_fetch_limit_caps_downloads(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=5)
    stats = fetch.fetch_images(
        conn, client=FakeClient(), images_root=tmp_path, limit=2, sleep=lambda _s: None
    )
    assert stats.fetched == 2
    assert db.count_pages_fetched(conn) == 2


def test_fetch_set_and_work_filter(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, "A", "LeibnizHandschriften", n=2)
    _seed(conn, "B", "LeibnizBriefwechsel", n=2)
    stats = fetch.fetch_images(
        conn,
        client=FakeClient(),
        images_root=tmp_path,
        set_name="LeibnizBriefwechsel",
        sleep=lambda _s: None,
    )
    assert stats.fetched == 2
    assert db.count_pages_fetched(conn, set_name="LeibnizBriefwechsel") == 2
    assert db.count_pages_fetched(conn, set_name="LeibnizHandschriften") == 0


def test_fetch_integrity_retry_recovers_truncation(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=1)
    client = FlakyClient(n_bad=1)  # first body truncated, retry succeeds
    stats = fetch.fetch_images(
        conn, client=client, images_root=tmp_path, integrity_retries=2, sleep=lambda _s: None
    )
    assert stats.fetched == 1 and not stats.failures
    assert client.calls == 2


def test_fetch_records_failure_when_never_complete(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=1)
    client = FlakyClient(n_bad=99)  # always truncated
    stats = fetch.fetch_images(
        conn, client=client, images_root=tmp_path, integrity_retries=1, sleep=lambda _s: None
    )
    assert stats.fetched == 0
    assert len(stats.failures) == 1
    assert not db.get_page(conn, "W:0001").is_cached


# -- verify ----------------------------------------------------------------- #


def test_verify_detects_ok_missing_and_corrupt(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=3)
    fetch.fetch_images(conn, client=FakeClient(), images_root=tmp_path, sleep=lambda _s: None)

    # Corrupt one file (size mismatch) and delete another (missing).
    (tmp_path / "W" / "0002.jpg").write_bytes(b"short")
    (tmp_path / "W" / "0003.jpg").unlink()

    stats = fetch.verify_images(conn, images_root=tmp_path, deep=True)
    assert stats.recorded == 3
    assert stats.ok == 1
    assert stats.size_mismatch == ["W:0002"]
    assert stats.missing_file == ["W:0003"]


def test_verify_counts_unfetched_gaps(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, n=3)
    fetch.fetch_images(
        conn, client=FakeClient(), images_root=tmp_path, limit=1, sleep=lambda _s: None
    )
    stats = fetch.verify_images(conn, images_root=tmp_path)
    assert stats.recorded == 1
    assert stats.unfetched == 2  # two pages still have no cached image


# -- stats ------------------------------------------------------------------ #


def test_image_stats_and_census_section(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, "A", "LeibnizHandschriften", n=2)
    fetch.fetch_images(conn, client=FakeClient(), images_root=tmp_path, sleep=lambda _s: None)

    stats = fetch.image_stats(conn)
    assert stats.fetched == 2
    assert stats.fetch_targets == 2
    assert stats.total_bytes == 2 * len(SAMPLE)
    assert stats.n_with_dims == 2
    assert stats.max_dims == (118, 150)
    # Every measured page is < 1 MP (118×150), so that bucket holds them.
    hist = dict(stats.mp_histogram)
    assert hist["< 1 MP"] == 2

    section = fetch.render_stats_section(stats, generated_at="2026-07-29T00:00:00Z")
    assert "Image cache (Phase A2)" in section
    assert fetch.CENSUS_MARKER in section

    census = tmp_path / "census.md"
    census.write_text("# Census\n\nExisting content.\n", encoding="utf-8")
    fetch.append_stats_to_census(census, section)
    body = census.read_text(encoding="utf-8")
    assert "Existing content." in body
    assert body.count(fetch.CENSUS_MARKER) == 1

    # Re-append replaces, never stacks.
    fetch.append_stats_to_census(census, fetch.render_stats_section(stats, generated_at="later"))
    assert census.read_text(encoding="utf-8").count(fetch.CENSUS_MARKER) == 1


def test_human_bytes() -> None:
    assert fetch.human_bytes(512) == "512 B"
    assert fetch.human_bytes(2048) == "2.0 KB"
    assert fetch.human_bytes(5 * 1024 * 1024) == "5.0 MB"
