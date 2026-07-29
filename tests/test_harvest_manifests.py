"""Tests for IIIF manifest harvest — parsing (v2/quirky/v3) and orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from leibniz import db
from leibniz.harvest import manifests

FIXDIR = Path(__file__).parent / "fixtures" / "manifests"
REAL = (FIXDIR / "00068642.json").read_bytes()
QUIRKY = (FIXDIR / "quirky.json").read_bytes()
V3 = (FIXDIR / "v3_minimal.json").read_bytes()


class FakeManifestClient:
    """Serves manifest bytes by URL; a bytes value that isn't JSON forces a failure."""

    def __init__(self, by_url: dict[str, bytes]) -> None:
        self.by_url = by_url
        self.calls: list[str] = []

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:  # noqa: ARG002
        self.calls.append(url)
        return self.by_url[url]


class ExplodingClient:
    def get_bytes(self, url: str, params: dict | None = None) -> bytes:  # noqa: ARG002
        raise AssertionError("network hit but cache should have served this")


# -- Parsing ---------------------------------------------------------------- #


def test_parse_real_manifest() -> None:
    canvases = manifests.parse_manifest(json.loads(REAL))
    assert len(canvases) == 4
    c = canvases[0]
    assert c.seq == 1
    assert c.label == "1r"
    assert (c.width, c.height) == (2008, 2561)
    assert c.canvas_id.endswith("/canvas/00000001")
    assert (
        c.image_service_url
        == "https://digitale-sammlungen.gwlb.de/iiif/00068642/ptif/00000001.ptif"
    )


def test_parse_quirky_manifest_degrades_gracefully() -> None:
    canvases = manifests.parse_manifest(json.loads(QUIRKY))
    assert len(canvases) == 2
    assert canvases[0].image_service_url is not None
    # Second canvas has empty images → no service, no dimensions, but still a row.
    assert canvases[1].image_service_url is None
    assert canvases[1].width is None and canvases[1].height is None
    assert canvases[1].seq == 2


def test_parse_v3_manifest_fallback() -> None:
    canvases = manifests.parse_manifest(json.loads(V3))
    assert len(canvases) == 1
    c = canvases[0]
    assert c.label == "1r"
    assert (c.width, c.height) == (1500, 2000)
    assert c.image_service_url == "https://example.org/iiif/v3work/image/1"


def test_parse_empty_manifest() -> None:
    assert manifests.parse_manifest({}) == []


def test_to_page_is_pending_with_derived_id() -> None:
    canvas = manifests.parse_manifest(json.loads(REAL))[0]
    page = manifests.to_page("00068642", canvas)
    assert page.id == "00068642:0001"
    assert page.status == "pending"
    assert page.image_service_url.endswith("00000001.ptif")


# -- Orchestration ---------------------------------------------------------- #


def _seed(conn, object_id: str, manifest_url: str, n_canvases: int) -> None:
    db.upsert_work(
        conn,
        db.Work(
            gwlb_object_id=object_id,
            set_name="LeibnizHandschriften",
            manifest_url=manifest_url,
            n_canvases=n_canvases,
        ),
    )


def test_harvest_manifests_populates_pages(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, "00068642", "https://gwlb/m/00068642.json", 4)
    client = FakeManifestClient({"https://gwlb/m/00068642.json": REAL})

    stats = manifests.harvest_manifests(conn, client=client, cache_dir=tmp_path / "m")

    assert stats.pages == 4
    assert db.count_pages(conn) == 4
    pages = db.get_pages(conn, "00068642")
    assert [p.seq for p in pages] == [1, 2, 3, 4]
    assert pages[0].width == 2008
    assert not stats.count_mismatches  # 4 == n_canvases
    conn.close()


def test_harvest_manifests_flags_count_mismatch(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, "00068642", "https://gwlb/m/00068642.json", 3)  # METS said 3, manifest has 4
    client = FakeManifestClient({"https://gwlb/m/00068642.json": REAL})
    stats = manifests.harvest_manifests(conn, client=client, cache_dir=tmp_path / "m")
    assert stats.count_mismatches == [("00068642", 3, 4)]
    conn.close()


def test_harvest_manifests_categorises_no_manifest(tmp_path) -> None:
    # A non-JSON body (what a 302-to-viewer redirect yields) is "no manifest",
    # not a hard failure — the static-JPEG-only majority of the corpus.
    conn = db.init_db(":memory:")
    _seed(conn, "good", "https://gwlb/m/good.json", 4)
    _seed(conn, "static", "https://gwlb/m/static.json", 1)
    client = FakeManifestClient(
        {"https://gwlb/m/good.json": REAL, "https://gwlb/m/static.json": b""}
    )
    stats = manifests.harvest_manifests(conn, client=client, cache_dir=tmp_path / "m")
    assert stats.pages == 4  # only the good work's canvases
    assert stats.no_manifest == ["static"]
    assert stats.failures == []
    # The non-manifest body must not be cached.
    assert not (tmp_path / "m" / "static.json").exists()
    conn.close()


def test_harvest_manifests_reports_hard_failure(tmp_path) -> None:
    conn = db.init_db(":memory:")
    db.upsert_work(conn, db.Work(gwlb_object_id="nomurl", set_name="LeibnizHandschriften"))
    stats = manifests.harvest_manifests(
        conn, client=FakeManifestClient({}), cache_dir=tmp_path / "m"
    )
    assert [oid for oid, _ in stats.failures] == ["nomurl"]  # no manifest_url → failure
    assert stats.no_manifest == []
    conn.close()


def test_harvest_manifests_cache_first(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, "00068642", "https://gwlb/m/00068642.json", 4)
    manifests.harvest_manifests(
        conn,
        client=FakeManifestClient({"https://gwlb/m/00068642.json": REAL}),
        cache_dir=tmp_path / "m",
    )
    assert (tmp_path / "m" / "00068642.json").exists()

    # Re-run: cache serves it, network must not be touched.
    conn2 = db.init_db(":memory:")
    _seed(conn2, "00068642", "https://gwlb/m/00068642.json", 4)
    stats = manifests.harvest_manifests(conn2, client=ExplodingClient(), cache_dir=tmp_path / "m")
    assert stats.cached == 1 and stats.fetched == 0
    assert db.count_pages(conn2) == 4
    conn.close()
    conn2.close()


def test_harvest_manifests_slice_by_works(tmp_path) -> None:
    conn = db.init_db(":memory:")
    _seed(conn, "a", "https://gwlb/m/a.json", 4)
    _seed(conn, "b", "https://gwlb/m/b.json", 4)
    client = FakeManifestClient({"https://gwlb/m/a.json": REAL})
    only_a = [db.get_work(conn, "a")]
    stats = manifests.harvest_manifests(conn, client=client, works=only_a, cache_dir=tmp_path / "m")
    assert stats.works == 1
    assert client.calls == ["https://gwlb/m/a.json"]
    conn.close()
