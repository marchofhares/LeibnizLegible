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


def test_a_search_by_shelfmark_takes_the_catalogue_spelling() -> None:
    """W6: the catalogue's ``sign_ol`` search is a substring match on its own
    spelling of a shelfmark (checked live 2026-10-21, one search per family)."""
    search = "https://leibniz-katalog.bbaw.de/de/extended-search?sign_ol="
    # LH: Arabic numerals, the groups joined with ", "; the library's Roman
    # section, its run-together "LH35" and its "Lh" are the same shelfmark
    assert links.katalog_spelling("LH IV, 6, 18") == "LH 4, 6, 18"
    assert links.katalog_search_url("LH IV, 6, 18") == search + "LH+4%2C+6%2C+18"
    assert links.katalog_search_url("LH 4, 6, 18") == search + "LH+4%2C+6%2C+18"
    assert links.katalog_spelling("LH35, 7, 3") == "LH 35, 7, 3"
    assert links.katalog_spelling("Lh 35, 4, 14") == "LH 35, 4, 14"
    assert links.katalog_spelling("LH 35,8, 17") == "LH 35, 8, 17"
    assert links.katalog_spelling("LH 35, 3 A 1") == "LH 35, 3 A 1"
    assert links.katalog_spelling("LH 1, 3, 7 C") == "LH 1, 3, 7 C"  # a sub-part, not a Roman 100
    assert links.katalog_spelling("LH IV, V, 10") == "LH 4, 5, 10"
    assert links.katalog_spelling("LH XXXV, I, 17, Bl. 1 - 17") == "LH 35, 1, 17"  # the work
    # LBr: the catalogue writes no period ("LBr 464 Bl. 1"; "LBr. 464" finds
    # nothing); the F series runs together ("LBrF 1 Bl. 3")
    assert links.katalog_spelling("LBr. 464") == "LBr 464"
    assert links.katalog_search_url("LBr. 464") == search + "LBr+464"
    assert links.katalog_spelling("LBr. 703 Bl. 28") == "LBr 703"
    assert links.katalog_spelling("LBr. 292a") == "LBr 292a"
    assert (
        links.katalog_spelling("LBr. F 1") == "LBrF 1"
        and links.katalog_spelling("LBrF 20") == "LBrF 20"
    )
    # Marg: the library's shelf prefix dropped; Stück and colon parts as the
    # catalogue has them ("Hannover NLB Leibn. Marg. 175:1, Stück 2")
    assert links.katalog_search_url("Leibn. Marg. 196") == search + "Leibn.+Marg.+196"
    assert links.katalog_spelling("ZEN Leibn. Marg. 40") == "Leibn. Marg. 40"
    assert links.katalog_spelling("Leibn. Marg. 175:1, Stück 2") == "Leibn. Marg. 175:1, Stück 2"
    assert links.katalog_spelling("LK-MOW 12") == "LK-MOW 12"
    # no family, no link
    for foreign in ("Ms XXIII, 23a", "Nm-A 605", "British Library Add. MS 4294", "", "LH", "   "):
        assert links.katalog_spelling(foreign) is None, foreign
        assert links.katalog_search_url(foreign) is None, foreign


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
