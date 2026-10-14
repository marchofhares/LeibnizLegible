"""Links out: the catalogue record, the edition's volumes, the late letters."""

from __future__ import annotations

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.web import links
from leibniz.web.api import create_app

W1 = "00068642"


def test_a_catalogue_record_is_found_by_id_and_number() -> None:
    assert links.katalog_record_url("41800") == (
        "https://leibniz-katalog.bbaw.de/de/extended-search?id=41800"
    )
    assert links.katalog_record_url("1820", 35028) == (
        "https://leibniz-katalog.bbaw.de/de/extended-search?id=1820&katnr=35028"
    )


def test_volumes_link_where_they_can_be_read() -> None:
    own = links.aa_volume_link(1, 26)
    assert own["kind"] == "volume" and own["url"].endswith("/laa-bd-i-26")
    assert own["label"] == (
        "AA I,26: the volume in the Repositorium des Leibniz-Archivs (CC BY-NC 4.0)"
    )
    # I,10 has no page of its own there (an unknown address shows the index)
    assert links.aa_volume_link(1, 10)["url"] == "https://www.leibnizedition.de/de/reihen/reihe-i/"
    assert links.aa_volume_link("6", "4")["where"] == "Leibniz-Forschungsstelle Münster"
    assert links.aa_volume_link(4, 3)["url"] == "https://leibnizp1.bbaw.de/de/edition"
    assert links.aa_volume_link(3, 7)["url"].endswith("/laa-bd-iii-7")
    assert links.aa_volume_link(9, 1) is None and links.aa_volume_link(1, None) is None


def test_late_letters_point_to_the_transcriptions_of_their_year() -> None:
    assert links.transcriptions_link("1709 Jan. 3")["url"].endswith("/laa-transkriptionen-1709")
    assert links.transcriptions_link("[1716?]")["year"] == 1716
    assert links.transcriptions_link("1707") is None and links.transcriptions_link(None) is None


def test_the_work_page_carries_the_links_out(store_path) -> None:
    conn = db.connect(store_path)
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="k-late",
            metadata={
                "titel": "Leibniz an Bernoulli",
                "datum": "1710 Febr. 2",
                "absender": "Leibniz (GND)",
                "adressat": "Bernoulli (GND)",
                "katnr": "4711",
            },
            shelfmark_refs=["LH IV, 6, 18 Bl. 2"],
            aa_refs=[{"series": 3}],
        ),
    )
    db.upsert_crosswalk(conn, db.CrosswalkMatch("k-late", W1, "shelfmark", 0.5))
    conn.commit()
    conn.close()
    c = TestClient(create_app(store_path, search=None, static_dir=None))
    records = {r["record_id"]: r for r in c.get(f"/api/works/{W1}").json()["katalog"]}
    piece = records["k-109"]
    assert piece["url"] == "https://leibniz-katalog.bbaw.de/de/extended-search?id=k-109"
    assert piece["gwlb_url"] == f"https://digitale-sammlungen.gwlb.de/resolve?id={W1}&page=1"
    assert [link["name"] for link in piece["aa_links"]] == ["AA VI,4"]
    assert piece["transcriptions"] is None  # edited, and not a letter
    late = records["k-late"]
    assert late["url"].endswith("id=k-late&katnr=4711")
    assert late["transcriptions"]["year"] == 1710 and late["aa_links"] == []
    text = c.get("/api/records/k-109/text").text
    assert "# Record in the Leibniz-Katalog: https://leibniz-katalog.bbaw.de/" in text
    assert "# AA VI,4: its series at Leibniz-Forschungsstelle Münster" in text
