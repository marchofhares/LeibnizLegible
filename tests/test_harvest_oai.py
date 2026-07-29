"""Tests for OAI-PMH harvest — parsing quirks and cache-first orchestration.

All offline: parsing runs against fixture XML under ``tests/fixtures/oai/``, and
orchestration uses a fake client that serves those fixtures by request params.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from leibniz import db
from leibniz.harvest import oai

FIXDIR = Path(__file__).parent / "fixtures" / "oai"
PAGE1 = (FIXDIR / "listrecords_page1.xml").read_bytes()
PAGE2 = (FIXDIR / "listrecords_page2.xml").read_bytes()
ERROR_BADTOKEN = (FIXDIR / "error_badresumptiontoken.xml").read_bytes()


class FakeOaiClient:
    """Serves fixture pages keyed by the OAI verb params; records its calls."""

    def __init__(self, by_set: dict[str, bytes], by_token: dict[str, bytes]) -> None:
        self.by_set = by_set
        self.by_token = by_token
        self.calls: list[dict] = []

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:
        params = params or {}
        self.calls.append(params)
        if params.get("resumptionToken"):
            return self.by_token[params["resumptionToken"]]
        return self.by_set[params["set"]]


class ExplodingClient:
    """Any network use is a test failure (used to prove cache-first)."""

    def get_bytes(self, url: str, params: dict | None = None) -> bytes:  # noqa: ARG002
        raise AssertionError("network was hit but the cache should have served this")


# -- Parsing ---------------------------------------------------------------- #


def test_parse_page1_records_and_token() -> None:
    page = oai.parse_response(PAGE1)
    # 4 records present, but the deleted one (C) is dropped → 3 parsed.
    assert len(page.records) == 3
    assert page.resumption_token == "TOKEN_PAGE_2"
    assert page.complete_list_size == 5


def test_parse_record_8digit_with_iiif_and_dual_shelfmark() -> None:
    rec = oai.parse_response(PAGE1).records[0]
    assert rec.object_id == "00099001"
    assert rec.n_canvases == 2
    # Dual normalisation kept as distinct strings (A3 reconciles them).
    assert rec.shelfmarks == ["LH XXXV, 3, 5", "LH 35, 3, 5"]
    # iiif identifier present → used verbatim, and flagged as IIIF-served.
    assert rec.manifest_url.endswith("/content/00099001/manifest.json")
    assert rec.has_iiif is True
    assert rec.primary_set == "LeibnizHandschriften"
    assert rec.leibniz_sets == ["LeibnizHandschriften", "Leibnitiana"]
    assert rec.dating == "1680"
    assert rec.extent == "2 Bl."
    assert "Public Domain" in (rec.license or "")


def test_parse_record_de611_constructs_manifest_url() -> None:
    rec = oai.parse_response(PAGE1).records[1]
    assert rec.object_id == "DE-611-HS-900001"
    assert rec.n_canvases == 3
    assert rec.shelfmarks == ["LBr. 57"]
    # No iiif identifier → manifest URL constructed from the id, flagged non-IIIF.
    assert rec.manifest_url == f"{oai.CONTENT_BASE}/DE-611-HS-900001/manifest.json"
    assert rec.has_iiif is False
    assert rec.primary_set == "LeibnizBriefwechsel"


def test_parse_zero_canvas_anchor() -> None:
    rec = oai.parse_response(PAGE1).records[2]
    assert rec.object_id == "DE-611-BF-900002"
    assert rec.n_canvases == 0
    assert rec.shelfmarks == []
    assert rec.title == "Rekonstruktionen"
    assert rec.primary_set == "leibniz-rekonstruktionen"


def test_deleted_record_is_skipped() -> None:
    ids = [r.object_id for r in oai.parse_response(PAGE1).records]
    assert "00099099" not in ids


def test_parse_page2_marginalien_and_end_token() -> None:
    page = oai.parse_response(PAGE2)
    assert page.resumption_token is None  # empty token → end of list
    rec = page.records[0]
    assert rec.object_id == "733600001"
    assert rec.n_canvases == 1
    assert rec.primary_set == "LeibnizMarginalien"
    # License here comes from dv:license, not mods:accessCondition.
    assert "Public Domain" in (rec.license or "")


def test_parse_response_raises_on_oai_error() -> None:
    with pytest.raises(oai.OaiError) as exc:
        oai.parse_response(ERROR_BADTOKEN)
    assert exc.value.code == "badResumptionToken"


def test_to_work_maps_fields() -> None:
    rec = oai.parse_response(PAGE1).records[0]
    work = oai.to_work(rec, harvest_set="LeibnizHandschriften")
    assert work.gwlb_object_id == "00099001"
    assert work.set_name == "LeibnizHandschriften"
    assert work.n_canvases == 2
    assert work.metadata["leibniz_sets"] == ["LeibnizHandschriften", "Leibnitiana"]
    assert work.metadata["harvest_set"] == "LeibnizHandschriften"
    assert work.metadata["has_iiif_manifest"] is True


# -- Orchestration ---------------------------------------------------------- #


def test_harvest_oai_pages_and_persists(tmp_path) -> None:
    conn = db.init_db(":memory:")
    client = FakeOaiClient(
        by_set={"LeibnizHandschriften": PAGE1},
        by_token={"TOKEN_PAGE_2": PAGE2},
    )
    stats = oai.harvest_oai(
        conn,
        client=client,
        sets=["LeibnizHandschriften"],
        cache_dir=tmp_path / "oai",
    )
    # 3 parsed from page1 + 1 from page2 = 4 unique works, pages 2+3+0+1 = 6.
    assert db.count_works(conn) == 4
    total_pages = sum(w.n_canvases for w in db.iter_works(conn))
    assert total_pages == 6
    assert stats[0].records == 4
    assert stats[0].complete_list_size == 5
    # Two requests: initial set page + one token continuation.
    assert len(client.calls) == 2
    conn.close()


def test_harvest_oai_writes_cache(tmp_path) -> None:
    conn = db.init_db(":memory:")
    client = FakeOaiClient({"LeibnizHandschriften": PAGE1}, {"TOKEN_PAGE_2": PAGE2})
    oai.harvest_oai(conn, client=client, sets=["LeibnizHandschriften"], cache_dir=tmp_path / "oai")
    cached = sorted((tmp_path / "oai" / "LeibnizHandschriften").glob("page_*.xml"))
    assert [p.name for p in cached] == ["page_0001.xml", "page_0002.xml"]
    conn.close()


def test_harvest_oai_is_cache_first_on_rerun(tmp_path) -> None:
    conn = db.init_db(":memory:")
    client = FakeOaiClient({"LeibnizHandschriften": PAGE1}, {"TOKEN_PAGE_2": PAGE2})
    oai.harvest_oai(conn, client=client, sets=["LeibnizHandschriften"], cache_dir=tmp_path / "oai")

    # Re-run against a client that fails if the network is touched at all.
    conn2 = db.init_db(":memory:")
    stats = oai.harvest_oai(
        conn2,
        client=ExplodingClient(),
        sets=["LeibnizHandschriften"],
        cache_dir=tmp_path / "oai",
    )
    assert db.count_works(conn2) == 4
    assert stats[0].pages_read == 2 and stats[0].pages_fetched == 0
    conn.close()
    conn2.close()


def test_harvest_oai_handles_no_records_match(tmp_path) -> None:
    no_records = (
        b'<?xml version="1.0"?><OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
        b'<error code="noRecordsMatch">empty</error></OAI-PMH>'
    )
    conn = db.init_db(":memory:")
    client = FakeOaiClient({"EmptySet": no_records}, {})
    stats = oai.harvest_oai(conn, client=client, sets=["EmptySet"], cache_dir=tmp_path / "oai")
    assert stats[0].records == 0
    assert db.count_works(conn) == 0
    conn.close()


def test_harvest_oai_restarts_on_expired_token(tmp_path) -> None:
    # Simulate a resumed, interrupted set: page 1 is already cached (its token
    # is now stale), and the server rejects that token. Harvest must restart the
    # set from scratch (force re-fetch) and complete via a fresh self-contained page.
    set_dir = tmp_path / "oai" / "LeibnizHandschriften"
    set_dir.mkdir(parents=True)
    (set_dir / "page_0001.xml").write_bytes(PAGE1)  # cached, token=TOKEN_PAGE_2

    restart_page = (
        b'<?xml version="1.0"?><OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"'
        b' xmlns:mets="http://www.loc.gov/METS/" xmlns:mods="http://www.loc.gov/mods/v3">'
        b"<ListRecords><record><header><identifier>00088888</identifier>"
        b"<setSpec>LeibnizHandschriften</setSpec></header><metadata><mets:mets>"
        b'<mets:structMap TYPE="PHYSICAL"><mets:div TYPE="physSequence">'
        b'<mets:div TYPE="page"/></mets:div></mets:structMap>'
        b"</mets:mets></metadata></record>"
        b"<resumptionToken/></ListRecords></OAI-PMH>"
    )
    client = FakeOaiClient(
        by_set={"LeibnizHandschriften": restart_page},
        by_token={"TOKEN_PAGE_2": ERROR_BADTOKEN},
    )
    conn = db.init_db(":memory:")
    stats = oai.harvest_oai(
        conn, client=client, sets=["LeibnizHandschriften"], cache_dir=tmp_path / "oai"
    )
    # The forced restart re-fetched the set and completed without raising.
    assert db.get_work(conn, "00088888") is not None
    assert stats[0].pages_fetched >= 1
    conn.close()
