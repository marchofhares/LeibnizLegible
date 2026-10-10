"""Go to what a scholar cites: shelfmarks with folios, AA numbers, ids."""

from __future__ import annotations

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.web import lookup as L
from leibniz.web.api import create_app

W1 = "00068642"  # LH IV, 6, 18 — pages 1r, 1v, 2r; record k-109 (AA VI,4 N. 109) on Bl. 1-2
W2 = "DE-611-HS-854976"  # LBr. 464


def _client(store_path) -> TestClient:
    return TestClient(create_app(store_path, search=None, static_dir=None))


def test_aa_references_parse_in_the_ways_they_are_written() -> None:
    for text in ("A VI, 4 N. 109", "AA VI,4 N.109", "A 6 4 Nr 109", "aa vi, 4, n. 109"):
        assert L.parse_aa(text) == L.AaRef(6, "4", "109"), text
    assert L.parse_aa("AA II, 1 N. 130 a") == L.AaRef(2, "1", "130a")
    assert L.parse_aa("A VI, 4") == L.AaRef(6, "4", None)
    for text in ("A XII, 4 N. 1", "Arnauld", "LH IV, 6, 18", "A VI"):
        assert L.parse_aa(text) is None, text
    assert L.AaRef(6, "4", "109").label == "AA VI,4 N. 109"


def test_a_shelfmark_with_its_folio_goes_to_the_page(store_path) -> None:
    c = _client(store_path)
    for q in ("LH IV, 6, 18 Bl. 1v", "LH 4,6,18 Bl. 1 v", "lh 4, 6, 18 bl. 1v"):
        body = c.get("/api/lookup", params={"q": q}).json()
        assert body["kind"] == "shelfmark", q
        (target,) = body["targets"]
        assert target["url"] == f"/page/{W1}:0002" and target["label"].endswith("fol. 1v")
    span = c.get("/api/lookup", params={"q": "LH IV, 6, 18 Bl. 1-2"}).json()["targets"][0]
    assert span["page_id"] == f"{W1}:0001" and "to fol. 2r (3 pages)" in span["label"]


def test_a_shelfmark_alone_goes_to_the_work_and_a_section_to_the_index(store_path) -> None:
    c = _client(store_path)
    body = c.get("/api/lookup", params={"q": "LH IV, 6, 18"}).json()
    assert [t["url"] for t in body["targets"]] == [f"/work/{W1}"]
    section = c.get("/api/lookup", params={"q": "LH 4"}).json()
    assert section["targets"][0] == {
        "kind": "section",
        "url": "/browse#lh-4",
        "label": "LH 4",
    }
    assert section["more"] == 1
    letters = c.get("/api/lookup", params={"q": "LBr. 464 Bl. 3"}).json()
    assert letters["targets"][0]["kind"] == "work" and "no page" in letters["targets"][0]["detail"]
    nowhere = c.get("/api/lookup", params={"q": "LH 99, 1"}).json()
    assert nowhere["kind"] == "shelfmark" and nowhere["targets"] == []
    assert "no digitized work" in nowhere["reason"]


def test_an_aa_number_goes_to_the_piece_on_its_scan(store_path) -> None:
    c = _client(store_path)
    body = c.get("/api/lookup", params={"q": "A VI, 4 N. 109"}).json()
    assert body["kind"] == "aa"
    (target,) = body["targets"]
    assert target["url"] == f"/page/{W1}:0001"
    assert target["label"] == "AA VI,4 N. 109: LH IV, 6, 18, Bl. 1–2"
    assert target["text_url"] == f"/api/records/k-109/text?work={W1}"
    assert target["detail"] == "Praefatio operis ad instaurationem scientiarum"
    vol = c.get("/api/lookup", params={"q": "A VI, 4"}).json()
    assert vol["targets"] == [] and "add the piece" in vol["reason"]
    none = c.get("/api/lookup", params={"q": "A II, 1 N. 5"}).json()
    assert none["targets"] == [] and "no catalogue record" in none["reason"]


def test_ids_and_words(store_path) -> None:
    c = _client(store_path)
    assert c.get("/api/lookup", params={"q": W1}).json()["targets"][0]["url"] == f"/work/{W1}"
    page = c.get("/api/lookup", params={"q": f"{W1}:0003"}).json()["targets"][0]
    assert page["url"] == f"/page/{W1}:0003" and page["label"] == "fol. 2r"
    words = c.get("/api/lookup", params={"q": "calculemus"}).json()
    assert words == {"query": "calculemus", "kind": None, "targets": [], "reason": None, "more": 0}
    assert c.get("/api/lookup", params={"q": ""}).status_code == 422


def test_the_aa_index_files_numbers_and_strings_alike(store_path) -> None:
    conn = db.connect(store_path)
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="k-int",
            aa_refs=[{"series": 2, "volume": 1, "piece": "130a"}],
        ),
    )
    index = L.build_aa_index(conn)
    conn.close()
    assert index[(6, "4", "109")] == ["k-109"] and index[(2, "1", "130a")] == ["k-int"]
