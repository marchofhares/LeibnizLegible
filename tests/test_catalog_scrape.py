"""Tests for the katalog scraper: row parsing (real fixture) + orchestration."""

from __future__ import annotations

from pathlib import Path

from leibniz import db
from leibniz.catalog import scrape as S

FIX = Path(__file__).parent / "fixtures" / "katalog" / "results_sample.html"
HTML = FIX.read_bytes()


class FakeClient:
    """Serves the fixture HTML for any URL; records calls."""

    def __init__(self, body: bytes = HTML) -> None:
        self.body = body
        self.calls: list[tuple[str, dict | None]] = []

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:
        self.calls.append((url, params))
        return self.body


class ExplodingClient:
    def get_bytes(self, url: str, params: dict | None = None) -> bytes:  # noqa: ARG002
        raise AssertionError("network hit but cache should have served this")


# -- Parsing (real trimmed fixture) ----------------------------------------- #


def test_parse_result_table_extracts_records() -> None:
    recs = S.parse_result_table(HTML)
    assert len(recs) == 3
    by_id = {r.record_id: r for r in recs}
    # A GWLB-linked manuscript record.
    r = by_id["342"]
    assert r.gwlb_ids == ["00068199"]
    assert r.shelfmark_refs == ["LH 35, 13,  2c Bl.  64"] or r.shelfmark_refs[0].startswith("LH 35")
    assert r.metadata["titel"].startswith("Ex regulis")


def test_parse_extracts_gwlb_link_as_join_key() -> None:
    recs = S.parse_result_table(HTML)
    linked = [r for r in recs if r.gwlb_ids]
    assert linked, "fixture must contain at least one GWLB-linked record"
    assert all(oid and not oid.startswith("http") for r in linked for oid in r.gwlb_ids)


def test_parse_foreign_record_has_no_gwlb_link() -> None:
    recs = S.parse_result_table(HTML)
    r = next(r for r in recs if r.record_id == "33")
    assert r.gwlb_ids == []
    assert "London" in r.shelfmark_refs[0]


def test_result_count_hint() -> None:
    assert S.result_count_hint(HTML) == 3
    assert S.result_count_hint(b"<html>no count here</html>") is None


# -- AA reference parsing --------------------------------------------------- #


def test_parse_aa_refs_from_both_columns() -> None:
    refs = S.parse_aa_refs("2 | 1.130 / a Teildr. Aufl. 2 (1988)", "II,1 N.130a = III,1 N.89")
    keys = {(r["series"], r["volume"], r["piece"]) for r in refs}
    assert (2, 1, "130a") in keys  # from the AA column (letter appended)
    assert (3, 1, "89") in keys  # from the Bezüge column (Roman series)


def test_parse_aa_refs_empty() -> None:
    assert S.parse_aa_refs("", "") == []


# -- Query routing / slug --------------------------------------------------- #


def test_query_endpoint_routing() -> None:
    assert S.query_endpoint({"q": "Newton"}) == S.GLOBAL_SEARCH
    assert S.query_endpoint({"reihe": "2", "bd": "1"}) == S.EXTENDED_SEARCH


def test_query_slug_is_filesystem_safe() -> None:
    assert S.query_slug({"reihe": "2", "bd": "1"}) == "bd-1_reihe-2"
    assert "/" not in S.query_slug({"sign_ol": "LH 35/1"})


# -- Orchestration ---------------------------------------------------------- #


def test_scrape_populates_records_and_caches(tmp_path) -> None:
    conn = db.init_db(":memory:")
    client = FakeClient()
    stats = S.scrape(conn, client=client, queries=[{"q": "Newton"}], cache_dir=tmp_path / "kat")
    assert stats.records == 3
    assert stats.with_gwlb_link == 2
    assert stats.fetched == 1 and stats.cached == 0
    assert db.count_katalog_records(conn) == 3
    assert (tmp_path / "kat" / "q-Newton.html").exists()
    conn.close()


def test_scrape_is_cache_first(tmp_path) -> None:
    conn = db.init_db(":memory:")
    S.scrape(conn, client=FakeClient(), queries=[{"q": "Newton"}], cache_dir=tmp_path / "kat")
    # Re-run: the cache serves it, network must not be touched.
    conn2 = db.init_db(":memory:")
    stats = S.scrape(
        conn2, client=ExplodingClient(), queries=[{"q": "Newton"}], cache_dir=tmp_path / "kat"
    )
    assert stats.cached == 1 and stats.fetched == 0
    assert db.count_katalog_records(conn2) == 3
    conn.close()
    conn2.close()


def test_scrape_flags_capped_query(tmp_path) -> None:
    # A body whose parsed rows hit the cap must be flagged, not silently truncated.
    conn = db.init_db(":memory:")
    header = "<tr><th>Id</th><th>Signatur</th></tr>"
    rows = "".join(f"<tr><td>{i}</td><td>LH {i}</td></tr>" for i in range(S.RESULT_CAP))
    big = f"<html><body><table>{header}{rows}</table></body></html>".encode()
    stats = S.scrape(
        conn, client=FakeClient(big), queries=[{"sign_ol": "LH"}], cache_dir=tmp_path / "kat"
    )
    assert stats.capped_queries == ["sign_ol-LH"]
    conn.close()
