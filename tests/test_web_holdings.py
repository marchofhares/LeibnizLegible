"""What the Arbeitskatalog export adds to the site (A3b): the holdings page and
API, the coverage wording, the links out and the Ordnungsvermerk on a record."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.catalog import arbeitskatalog as ak
from leibniz.catalog import crosswalk
from leibniz.web import api
from leibniz.web.api import STATIC_DIR, create_app

FIXTURES = Path(__file__).parent / "fixtures" / "arbeitskatalog"
W1 = "00068642"
W2 = "DE-611-HS-854976"


def _client(store_path: Path) -> TestClient:
    return TestClient(create_app(store_path, search=None, static_dir=STATIC_DIR))


def _import(store_path: Path) -> None:
    """The fixture export into the fixture store, as `--write` would."""
    conn = db.connect(store_path)
    records = ak.records_from_export(ak.read_export(FIXTURES))
    ak.write_import(conn, records, export_date="2026-10-21", csv_dir=FIXTURES)
    conn.close()


def _link(store_path: Path, rec: db.KatalogRecord) -> None:
    conn = db.connect(store_path)
    db.upsert_katalog_record(conn, rec)
    crosswalk.build_crosswalk(conn)
    conn.commit()
    conn.close()


def test_coverage_before_and_after_the_import(store_path) -> None:
    c = _client(store_path)
    assert c.get("/api/stats").json()["katalog"] == {"records": 1, "refreshed": None}
    assert c.get(f"/api/works/{W1}").json()["katalog_coverage"] == {"records": 1, "refreshed": None}
    assert c.get("/api/contents", params={"q": "praefatio"}).json()["katalog"]["refreshed"] is None
    _import(store_path)
    c = _client(store_path)
    assert c.get("/api/stats").json()["katalog"] == {"records": 30, "refreshed": "2026-10-21"}
    body = c.get(f"/api/works/{W1}").json()
    assert body["katalog_coverage"] == {"records": 30, "refreshed": "2026-10-21"}
    # the two records on LH 4, 6, 18 replaced the fixture's k-109, by their GWLB links
    assert sorted(r["record_id"] for r in body["katalog"]) == ["41800", "59095"]
    assert body["katalog"][0]["match_method"] == "gwlb_link"
    assert body["katalog"][0]["title"] == "[Praefatio operis ad instaurationem scientiarum]"
    assert body["katalog"][0]["holding"] == "Hannover NLB"
    assert body["katalog"][0]["url_ms"] is None  # the GWLB's own link is the work


def test_holdings_api_and_page(store_path) -> None:
    c = _client(store_path)
    partial = c.get("/api/holdings")
    assert (
        partial.status_code == 200
        and partial.headers["cache-control"] == api.DAY_CACHE["Cache-Control"]
    )
    assert partial.json()["refreshed"] is None and partial.json()["records"] == 1
    _import(store_path)
    c = _client(store_path)
    body = c.get("/api/holdings").json()
    assert body["refreshed"] == "2026-10-21" and body["records"] == 30
    assert body["by_holding"][0] == {"holding": "Hannover NLB", "records": 23}
    assert body["by_place"][0] == {"place": "Hannover", "records": 24}
    assert body["gwlb_links"] == {"id": 19, "PPN": 1} and body["with_url"] == 26
    assert body["by_domain"][0] == {"domain": "digitale-sammlungen.gwlb.de", "records": 20}
    assert (body["works"], body["works_with_records"], body["works_without_records"]) == (2, 1, 1)
    assert body["by_set"] == [
        {"set": "LeibnizBriefwechsel", "works": 1, "with_records": 0},
        {"set": "LeibnizHandschriften", "works": 1, "with_records": 1},
    ]
    assert "CC BY 4.0" in body["attribution"]
    page = c.get("/holdings")
    assert page.status_code == 200
    assert "<title>Where Leibniz&#x27;s papers lie — Leibniz Legible</title>" in page.text
    assert 'property="og:url" content="https://leibnizlegible.com/holdings"' in page.text
    assert "by holding institution" in page.text  # the description meta
    get = c.get("/openapi.json").json()["paths"]["/api/holdings"]["get"]
    assert "by_holding" in get["description"] and get["summary"]
    # the viewer: a view, a route, the strings in both languages
    assert "holdings" in (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert (STATIC_DIR / "views" / "holdings.js").exists()
    strings = (STATIC_DIR / "i18n.js").read_text(encoding="utf-8")
    for key in (
        "holdings.heading",
        "holdings.byHolding.h",
        "holdings.label.printed",
        "about.what.holdings",
        "about.what.scope.whole",
        "browse.filter.noneAnywhere.whole",
        "work.katalog.partial.whole",
        "work.katalog.copy",
        "work.katalog.pdf",
        "work.katalog.ov",
    ):
        assert strings.count(f"'{key}':") == 2, key
    about = (STATIC_DIR / "views" / "about.js").read_text(encoding="utf-8")
    assert 'href="/holdings"' in about and "about.what.scope.whole" in about


def test_the_work_page_says_the_whole_catalogue_once_imported(store_path) -> None:
    c = _client(store_path)
    before = c.get(f"/work/{W2}").text
    assert "this site holds part of the Arbeitskatalog so far; search it for" in before
    _import(store_path)
    c = _client(store_path)
    after = c.get(f"/work/{W2}").text
    assert (
        "<p>No catalogue record is linked to this work, and this site holds the whole "
        "Arbeitskatalog, refreshed 2026-10-21; search it for <a href=" in after
    )
    assert "holds part of" not in after
    # llms.txt and the README say the same
    llms = c.get("/llms.txt").text
    assert "the whole Arbeitskatalog as the Arbeitsstelle exported it on 2026-10-21" in llms
    assert "`GET /api/holdings`" in llms and "/holdings" in llms
    readme = (STATIC_DIR.parents[3] / "README.md").read_text(encoding="utf-8")
    assert "the whole Arbeitskatalog as" in readme and "holdings page" in readme


def test_a_record_carries_the_links_out_and_the_ordnungsvermerk(store_path) -> None:
    # a record of LH 4, 6, 18 as the export writes one: a copy elsewhere, the
    # edition's PDF, an Ordnungsvermerk (the crosswalk places it by shelfmark)
    rec = db.KatalogRecord(
        record_id="90001",
        metadata={
            "titel": "[Exzerpt aus Adamus Bremensis]",
            "textart": "Aufz.; eigh.",
            "signatur": "LH 4, 6, 18 Bl. 2",
            "url_ms": "https://gallica.bnf.fr/ark:/12148/bpt6k50030x/f32.item",
            "holding": "Hannover NLB",
            "ordnungsvermerk": "Geograph observ.",
            "ordnungsvermerk_norm": "Geographica",
            "ordnungsvermerk_title": "Geographie",
            "ordnungsnummer": "1150",
            "aa_pdf": {
                "url": "https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/I17B.pdf#page=270",
                "page": 270,
                "host": "www.gwlb.de",
            },
        },
        shelfmark_refs=["LH 4, 6, 18 Bl. 2"],
        aa_refs=[{"series": 1, "volume": 17, "piece": "403", "source": "aa_column"}],
    )
    muenster = db.KatalogRecord(
        record_id="90002",
        metadata={
            "titel": "Leibniz an Oldenburg",
            "signatur": "LH 4, 6, 18 Bl. 1",
            "aa_pdf": {
                "url": "https://www.uni-muenster.de/Leibniz/DatenII1/II1_B.pdf#nameddest=130_a",
                "page": 425,
                "host": "www.uni-muenster.de",
            },
            "url_ms": "https://digitale-sammlungen.gwlb.de/resolve?id=00068642",
        },
        shelfmark_refs=["LH 4, 6, 18 Bl. 1"],
        aa_refs=[{"series": 2, "volume": 1, "piece": "130a", "source": "aa_column"}],
    )
    _link(store_path, rec)
    _link(store_path, muenster)
    c = _client(store_path)
    records = {r["record_id"]: r for r in c.get(f"/api/works/{W1}").json()["katalog"]}
    r = records["90001"]
    assert r["url_ms"] == "https://gallica.bnf.fr/ark:/12148/bpt6k50030x/f32.item"
    assert r["url_ms_domain"] == "gallica.bnf.fr"
    assert r["aa_pdf"] == {
        "url": "https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/I17B.pdf#page=270",
        "page": 270,
        "volume": "AA I,17",
        "where": "Repositorium des Leibniz-Archivs",
        "terms": "CC BY-NC 4.0",
        "channel": "gwlb",
    }
    assert r["ordnungsvermerk"] == {
        "name": "Geographica",
        "written": "Geograph observ.",
        "title": "Geographie",
        "komplex": None,
        "epoche": None,
        "nummer": "1150",
    }
    # the Münster files sit behind a permission page: no PDF link; a GWLB link is the work
    m = records["90002"]
    assert m["aa_pdf"] is None and m["url_ms"] is None and m["ordnungsvermerk"] is None
    # the server-rendered page and the piece's text header carry the same
    page = c.get(f"/work/{W1}").text
    assert (
        '<a href="https://gallica.bnf.fr/ark:/12148/bpt6k50030x/f32.item" rel="noopener">'
        "Digitised copy at gallica.bnf.fr</a>" in page
    )
    assert (
        'rel="noopener">In the Akademie-Ausgabe: AA I,17, p. 270 (PDF, Repositorium des '
        "Leibniz-Archivs, CC BY-NC 4.0)</a>" in page
    )
    assert "Ordnungsvermerk: Geographica (Geographie)" in page
    assert "uni-muenster.de" not in page
    text = c.get("/api/records/90001/text").text
    assert (
        "# Digitised copy (gallica.bnf.fr): https://gallica.bnf.fr/ark:/12148/bpt6k50030x/f32.item"
        in text
    )
    assert (
        "# In the Akademie-Ausgabe: AA I,17, p. 270 (PDF, Repositorium des Leibniz-Archivs, "
        "CC BY-NC 4.0): https://www.gwlb.de/" in text
    )
    assert "# Ordnungsvermerk: Geographica (Geographie)" in text
    # the Faszikel index: the Ordnungsvermerk level is searched and shown
    found = c.get("/api/contents", params={"q": "geographie"}).json()
    assert found["total"] == 1 and found["works"][0]["work_id"] == W1
    match = found["works"][0]["matches"][0]
    assert match["record_id"] == "90001"
    assert match["ordnungsvermerk"] == {
        "name": "Geographica",
        "written": "Geograph observ.",
        "title": "Geographie",
        "komplex": None,
        "epoche": None,
        "nummer": "1150",
    }
    assert c.get("/api/contents", params={"q": "geographica"}).json()["total"] == 1
    # the viewer renders them
    work_js = (STATIC_DIR / "views" / "work.js").read_text(encoding="utf-8")
    assert (
        "record.url_ms" in work_js
        and "record.aa_pdf" in work_js
        and "record.ordnungsvermerk" in work_js
    )
    browse_js = (STATIC_DIR / "views" / "browse.js").read_text(encoding="utf-8")
    assert "m.ordnungsvermerk" in browse_js and "noneAnywhere.whole" in browse_js


def test_record_rows_and_labels() -> None:
    rows = api._record_rows(
        {
            "record_id": "1",
            "title": "t",
            "url_ms": "https://x.example/1",
            "url_ms_domain": "x.example",
            "aa_pdf": {
                "url": "https://p.example/a.pdf",
                "page": None,
                "volume": "AA V,1250",
                "where": "Leibniz-Edition Potsdam I",
                "terms": "CC BY-NC 4.0",
            },
            "ordnungsvermerk": {"name": "Gentes", "title": None},
        }
    )
    assert rows[-3:] == [
        "Digitised copy (x.example): https://x.example/1",
        "In the Akademie-Ausgabe: AA V,1250 (PDF, Leibniz-Edition Potsdam I, CC BY-NC 4.0): https://p.example/a.pdf",
        "Ordnungsvermerk: Gentes",
    ]
