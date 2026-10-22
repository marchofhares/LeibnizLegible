"""The Arbeitskatalog from the Access export (A3b): one row → the website
parser's record, proved on the records the website itself served."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from leibniz import db
from leibniz.catalog import arbeitskatalog as ak
from leibniz.catalog import crosswalk
from leibniz.catalog.holdings import GWLB, PRINTED
from leibniz.cli import app

FIXTURES = Path(__file__).parent / "fixtures" / "arbeitskatalog"
runner = CliRunner()


def _rows() -> dict[str, dict[str, str]]:
    return {r["ID"]: r for r in ak.read_table(FIXTURES / "ritter.csv")}


def _records() -> dict[str, db.KatalogRecord]:
    return {r.record_id: r for r in ak.records_from_export(ak.read_export(FIXTURES))}


# ---- the cells, as the website renders them ----------------------------------- #


def test_katnr_cell() -> None:
    assert ak.katnr_cell("Cc2", "1505", "C") == "Cc2 1505/C"
    assert ak.katnr_cell("K", "22257", "") == "K 22257"
    assert ak.katnr_cell("", "57273", "") == "57273"
    assert ak.katnr_cell("K", "", "") == ""


def test_date_cell() -> None:
    assert ak.date_cell("16760827") == "1676-08-27"
    assert ak.date_cell("16770500") == "1677-05"
    assert ak.date_cell("17070000") == "1707"
    assert ak.date_cell("16930006") == "1693"  # a day without a month is dropped with it
    assert ak.date_cell("169760113") == "169760113"  # nine digits: as the website, verbatim
    assert ak.date_cell("1700") == "1700"  # the website prints nothing; the year is kept
    assert ak.date_cell("") == ""
    assert ak.date_cell("16991208", "991128") == "1699-12-08 (99-11-28)"
    assert ak.date_cell("17051127", "51116") == "1705-11-27 (05-11-16)"  # Access lost the zero
    assert ak.date_cell("", "991128") == ""
    # the second date drops its zero parts as the first does (397 records in the
    # operator's dry run of 2026-10-22 read "(93-06-00)" on the website as "(93-06)")
    assert ak.date_cell("16930629", "930600") == "1693-06-29 (93-06)"
    assert ak.date_cell("16990000", "990000") == "1699 (99)"
    assert ak.date_cell("17000114", "000104") == "1700-01-14 (00-01-04)"


def test_umfang_cell() -> None:
    assert ak.umfang_cell("4", "4") == "Quart, 4 Seiten/Spalten"
    assert ak.umfang_cell("4", "6.1999998") == "Quart, 6.2 Seiten/Spalten"
    assert ak.umfang_cell("2", "4") == "Folio, 4 Seiten/Spalten"
    assert ak.umfang_cell("16", "1") == "Sedez, 1 Seite/Spalte"
    assert ak.umfang_cell("12", "1") == "Duodez, 1 Seite/Spalte"
    assert ak.umfang_cell("24", "1") == "Vigesimoquart, 1 Seite/Spalte"
    assert ak.umfang_cell("32", "1") == "32°, 1 Seite/Spalte"  # the website prints "°"
    assert ak.umfang_cell("", "1") == "1 Seite/Spalte"
    assert ak.umfang_cell("4", "") == "Quart"
    assert ak.umfang_cell("", "0") == ""
    assert ak.umfang_cell("", "") == ""
    assert ak.umfang_cell("4", "0.5") == "Quart, 0.5 Seiten/Spalten"
    assert ak.umfang_cell("", "3.25") == "3.25 Seiten/Spalten"


def test_aa_cell_and_refs() -> None:
    assert ak.aa_cell("8", "3", "44") == "8 | 3.044"
    assert ak.aa_cell("5", "1250", "7") == "5 | 1250.007"
    assert (
        ak.aa_cell("2", "1", "130", "a Teildr.", "2 (1988)")
        == "2 | 1.130 / a Teildr. Aufl. 2 (1988)"
    )
    assert (
        ak.aa_cell("1", "17", "155", "Beil.zu N.154 (tlw.)") == "1 | 17.155 / Beil.zu N.154 (tlw.)"
    )
    assert ak.aa_cell("4", "", "") == "4"
    assert ak.aa_cell("6", "5", "") == "6"  # a volume without a piece: the series alone
    assert ak.aa_cell("", "", "") == ""
    refs = ak.aa_refs_for("8", "3", "44", "", "", "")
    assert refs == [{"series": 8, "volume": 3, "piece": "044", "source": "aa_column"}]
    refs = ak.aa_refs_for(
        "2", "1", "130", "a Teildr.", "2 (1988)", "II,1 N.130a (tlw.) = III,1 N.89"
    )
    assert refs == [
        {"series": 2, "volume": 1, "piece": "130a", "source": "aa_column"},
        {"series": 3, "volume": 1, "piece": "89", "source": "bezuege"},
    ]
    # a series alone: assigned to the edition, not yet published (the API's aa_planned)
    assert ak.aa_refs_for("4", "", "", "", "", "A:42667") == [
        {"series": 4, "volume": None, "piece": None, "source": "aa_column"}
    ]
    assert ak.aa_refs_for("9", "", "", "", "", "") == []  # not a series of the edition
    assert ak.aa_refs_for("0", "", "", "", "", "") == []


def test_wortlaut_text() -> None:
    raw = (
        "&xs+83196&x{Rainaldus<app2c>Rainaldus ._._. p._869: vgl._<sc>F._Ughelli</sc>, "
        "<i>Italia sacra</i></app2c> Coloniensis A[rchie]piscopus &xs-83196&x{p._869[.]<app2c/>"
    )
    assert ak.wortlaut_text(raw) == "Rainaldus Coloniensis A[rchie]piscopus p. 869[.]"
    assert (
        ak.wortlaut_text("(apud ^<_-_^>) <i>Tunica</i> <s>gone</s>") == "(apud < - >) Tunica gone"
    )
    assert ak.wortlaut_text("a[.]</p> <p>^<vid^> et") == "a[.] <vid> et"
    assert ak.wortlaut_text('<persName key="1">Lotharii</persName> Saxonis') == "Lotharii Saxonis"
    assert ak.wortlaut_text("") is None and ak.wortlaut_text("  ") is None


def test_gwlb_ids_of() -> None:
    assert ak.gwlb_ids_of("https://digitale-sammlungen.gwlb.de/resolve?id=00068534") == ["00068534"]
    assert ak.gwlb_ids_of("https://digitale-sammlungen.gwlb.de/resolve?id=DE-611-HS-3617045") == [
        "DE-611-HS-3617045"
    ]
    assert ak.gwlb_ids_of("https://digitale-sammlungen.gwlb.de/resolve?PPN=1665058609") == [
        "1665058609"
    ]
    assert (
        ak.gwlb_ids_of("https://www.arcinsys.niedersachsen.de/arcinsys/detailAction?detailid=v1")
        == []
    )
    assert ak.gwlb_ids_of("") == []
    assert ak.is_gwlb_url("https://digitale-sammlungen.gwlb.de/resolve?PPN=1")
    assert not ak.is_gwlb_url("https://gallica.bnf.fr/ark:/12148/x") and not ak.is_gwlb_url(None)


# ---- the fixture, row by row ----------------------------------------------------- #


def test_the_export_reads_with_the_csv_module() -> None:
    export = ak.read_export(FIXTURES)
    assert export.counts["ritter.csv"] == 30 and export.counts["pdf_url.csv"] == 21
    assert {"OV_mit_Infos.csv", "OV_mit_Inhalt.csv", "Faszikel_Ms_mit_Infos.csv"} <= set(
        export.counts
    )
    assert len(export.ids) == 30
    rows = _rows()
    assert "\r\n" in rows["33"]["BEZUG"]  # a multi-line field, read whole


def test_the_record_carries_the_website_keys_and_the_new_ones() -> None:
    recs = _records()
    r = recs["33"]
    assert r.metadata["katnr"] == "Cc2 1505/C"
    assert r.metadata["signatur"] == "London BL Add.Mss. 4294 Bl. 67-70"
    assert r.shelfmark_refs == ["London BL Add.Mss. 4294 Bl. 67-70"]
    assert r.metadata["datum"] == "1676-08-27" and r.metadata["sigle"] == "L2"
    # the names as the website shows them, through the persons table; the ids beside
    assert r.metadata["absender"] == "Leibniz (GND)"
    assert r.metadata["adressat"] == "Oldenburg (KorrespDB) (GND)"
    assert r.metadata["absender_gnd"] == ["118571249"] and "absender_korrespdb" not in r.metadata
    assert r.metadata["adressat_gnd"] == ["119115719"]
    assert r.metadata["adressat_korrespdb"] == ["666"]
    assert r.metadata["ort"] == "Paris" and r.metadata["textart"] == "Abf., eigh."
    assert r.metadata["umfang"] == "Quart, 6.2 Seiten/Spalten"
    assert r.metadata["aa"] == "2 | 1.130 / a Teildr. Aufl. 2 (1988)"
    assert r.metadata["drucke"].startswith(
        "-E2: Turnbull, Corresp. of Newton 2 (1960), S.57-64. -E3:"
    )
    assert r.metadata["bezuege"].startswith("II,1 N.130a (tlw.) = III,1 N.89 A:38960=Cc2_1505A")
    assert r.metadata["bemerkungen"].startswith('-Komplex "Math.Briefe 1676"')
    assert r.metadata["holding"] == "London BL" and "url_ms" not in r.metadata
    assert r.metadata["last_change"] == "Pe 2010-11-01; Pe 2006-09-17"
    assert r.aa_refs[0] == {"series": 2, "volume": 1, "piece": "130a", "source": "aa_column"}
    # the Münster PDF of II,1 N.130a: its own row (UNr a), the printed page
    assert r.metadata["aa_pdf"] == {
        "url": "https://www.uni-muenster.de/Leibniz/DatenII1/II1_B.pdf#nameddest=130_a",
        "page": 425,
        "host": "www.uni-muenster.de",
    }
    assert r.transcription_snippet is None
    # the Marginalien: a PPN link is the work id; the series alone is planned
    m = recs["1585"]
    assert m.gwlb_ids == ["1665058609"] and m.metadata["holding"] == GWLB
    assert m.metadata["url_ms"] == "https://digitale-sammlungen.gwlb.de/resolve?PPN=1665058609"
    assert m.aa_refs == [{"series": 5, "volume": None, "piece": None, "source": "aa_column"}]
    assert "datum" not in m.metadata and "umfang" not in m.metadata
    # a Landesarchiv record: no catalogue number, a link out, a nine-digit date
    n = recs["70639"]
    assert "katnr" not in n.metadata and n.metadata["holding"] == "Hannover NLA"
    assert n.metadata["url_ms"].startswith("https://www.arcinsys.niedersachsen.de/")
    assert n.gwlb_ids == [] and n.metadata["datum"] == "169760113"
    # a printed witness
    assert recs["63135"].metadata["holding"] == PRINTED
    assert recs["63135"].metadata["umfang"] == "Quart"
    # an excerpt with its Ordnungsvermerk, from the slip and the OV tables
    o = recs["63431"]
    assert o.metadata["ordnungsvermerk"] == "Geograph observ."
    assert o.metadata["ordnungsvermerk_norm"] == "Geographica"
    assert o.metadata["ordnungsvermerk_title"] == "Geographie"
    assert o.metadata["ordnungsnummer"] == "1150"
    assert (
        o.metadata["aa_pdf"]["host"] == "leibniz-potsdam.bbaw.de"
        and o.metadata["aa_pdf"]["page"] is None
    )
    assert o.transcription_snippet.startswith(
        "Marachi sunt populi Slavorum qui sunt ab oriente Boëmorum"
    )
    # the double date, the Reihe I PDF with its printed page
    d = recs["24633"]
    assert d.metadata["datum"] == "1699-12-08 (99-11-28)"
    assert (
        d.metadata["aa_pdf"]["url"].endswith("I17B.pdf#page=270")
        and d.metadata["aa_pdf"]["page"] == 270
    )
    assert recs["39739"].metadata["aa_pdf"]["page"] == 464
    assert recs["22250"].metadata["aa_pdf"]["url"].endswith("I17A.pdf#page=299")
    # identical-with: another record, never the record itself
    assert recs["46308"].metadata["identisch_mit"] == "46307"
    assert "identisch_mit" not in recs["33"].metadata


def test_the_monadologie_records_are_found_by_shelfmark() -> None:
    recs = _records()
    mon = {rid: r for rid, r in recs.items() if r.metadata.get("titel") == "[La Monadologie]"}
    assert {r.metadata["signatur"] for r in mon.values()} == {
        "LH 4, 1, 1a Bl. 1-6",
        "LH 4, 1, 1b Bl. 1-10",
        "LH 4, 1, 1b Bl. 1/1-16/1",
    }
    # the numbers Open question 27 quoted are the pieces' catalogue numbers, not record ids
    assert {r.metadata["katnr"] for r in mon.values()} == {"39739", "39743", "39744"}
    assert set(mon) == {"54786", "55406", "55407"}
    assert recs["39739"].metadata["titel"].startswith("[De centro potentiae")


# ---- the proof against the website's own rendering ------------------------------- #


def test_the_mapping_reproduces_the_website() -> None:
    site = ak.load_site_records(FIXTURES / "site_records_live.json")
    new = _records()
    both = sorted(set(site) & set(new), key=int)
    assert len(both) == 21
    cmp = ak.compare_records([site[rid] for rid in both], new)
    assert cmp.compared == 21 and cmp.missing_in_export == [] and cmp.new_in_export == 9
    for key in ak.THRESHOLD_KEYS:
        assert cmp.pct(key) == 100.0, (key, cmp.keys[key].counts)
    assert cmp.hand_changes == [] and cmp.settled
    exact = {k: a.counts["exact"] for k, a in cmp.keys.items()}
    assert exact["textart"] == exact["signatur"] == exact["titel"] == exact["incipit"] == 21
    assert exact["katnr"] == exact["sigle"] == exact["ort"] == exact["wortlaut"] == 21
    # the website prints nothing for a four-digit year (28335) and nothing at all
    # for 64358's date; the export has both: nothing to judge the mapping by
    assert cmp.keys["datum"].counts == {"exact": 19, "export_adds": 2}
    # the website's copy of 22579 names the series alone; the export the piece
    assert cmp.keys["aa"].counts == {"exact": 20, "export_adds": 1}
    # the names: the website's link texts reproduced through the persons table
    assert cmp.keys["absender"].counts == {"exact": 21}
    assert cmp.keys["adressat"].counts == {"exact": 21}
    # "°" for a 32° format on the website: the parser lost the code; the two
    # copies' printings edited apart
    assert cmp.keys["umfang"].counts == {"exact": 20, "markup": 1}
    assert cmp.keys["drucke"].counts == {"exact": 18, "other": 3}
    assert cmp.keys["gwlb_ids"].counts == {"exact": 20, "export_adds": 1}  # the PPN link
    table = ak.render_comparison(cmp)
    assert "| datum ✱ | 19 | 0 | 0 | 0 | 2 | 0 | 0 | 100.0 % |" in table
    assert "| umfang | 20 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0 % |" in table
    assert "lost as markup on umfang 1 records." in table
    assert "same answer before and after on 21 of 21 records." in table
    assert "Mapping: **settled**." in table


def test_classify() -> None:
    assert ak.classify("titel", "a", "a") == "exact"
    assert ak.classify("titel", "a  b", "a b") == "whitespace"
    assert ak.classify("absender", "Leibniz (GND)", "Leibniz") == "markers"
    assert ak.classify("adressat", "Fuchs,P. (KorrespDB) (GND)", "Fuchs,P.") == "markers"
    assert ak.classify("absender", "Leibniz", "Leibniz (GND)") == "markers"
    assert ak.classify("titel", "Leibniz (GND)", "Leibniz") == "other"
    assert ak.classify("datum", "", "1700") == "export_adds"
    assert ak.classify("incipit", "Si qvis", "") == "export_lacks"
    assert ak.classify("aa", (("1", "2", "3", "aa_column"),), ()) == "export_lacks"
    # a genuine edit stays "other"
    assert ak.classify("datum", "1698", "1700-01-14 (00-01-04)") == "other"


def test_the_website_lost_what_it_read_as_markup() -> None:
    """Text in angle brackets the website's HTML parser dropped: the store's
    value is the export's with every <…> segment gone; the export's is kept."""
    assert ak.classify("titel", "onometria rationalis", "<Trig>onometria rationalis") == "markup"
    assert ak.classify("incipit", "… Bergambt", "… <bey dem> Bergambt") == "markup"
    assert ak.classify("textart", "Abf., eigh.;", "Abf., eigh.; <prs. Anschr.>") == "markup"
    assert ak.classify("umfang", "°, 1 Seite/Spalte", "43°, 1 Seite/Spalte") == "markup"
    assert ak.website_lost_markup("umfang", "43°, 2 Seiten/Spalten") == "°, 2 Seiten/Spalten"
    assert ak.classify("titel", "a b", "a <x> c") == "other"
    old = db.KatalogRecord("1", metadata={"titel": "onometria", "textart": "Abf.;"})
    new = db.KatalogRecord("1", metadata={"titel": "<Trig>onometria", "textart": "Abf.; <prs.>"})
    cmp = ak.compare_records([old], {"1": new})
    assert cmp.keys["titel"].counts == {"markup": 1} and cmp.pct("titel") == 100.0
    assert "lost as markup on titel 1, textart 1 records." in ak.render_comparison(cmp)


def test_names_as_website() -> None:
    index = ak.build_person_index(
        [
            {"korr": "Leibniz", "pers_name": "", "gnd": "118571249", "idhannover": ""},
            {"korr": "Ilgen", "pers_name": "Ilgen, Rüdiger", "gnd": "1", "idhannover": "22"},
        ]
    )
    assert ak.names_as_website("Leibniz", index) == ("Leibniz (GND)", ["118571249"], [])
    assert ak.names_as_website("Leibniz | Ilgen", index) == (
        "Leibniz (GND)Ilgen (KorrespDB) (GND)",
        ["118571249", "1"],
        ["22"],
    )
    assert ak.names_as_website("?", index) == ("?", [], [])  # not in the table: bare
    assert ak.names_as_website("", index) == ("", [], [])
    assert ak.names_as_website("Leibniz | Ilgen", None) == ("Leibniz | Ilgen", [], [])


def test_a_lost_incipit_is_not_settled_and_a_changed_hand_is_listed() -> None:
    old = db.KatalogRecord("1", metadata={"textart": "Abf., eigh.", "titel": "t", "incipit": "x"})
    new = db.KatalogRecord("1", metadata={"textart": "Abf.", "titel": "t"})
    cmp = ak.compare_records([old], {"1": new})
    assert cmp.keys["incipit"].counts == {"export_lacks": 1}
    assert cmp.keys["textart"].counts == {"other": 1} and cmp.pct("textart") == 0.0
    assert cmp.hand_changes == [("1", "own", "other", True, False)]
    assert not cmp.settled
    assert "hand own → other, Leibniz's own True → False" in ak.render_comparison(cmp)
    # a hand change alone does not block: the export's fuller Textart decides
    old = db.KatalogRecord("2", metadata={"textart": "Abf.; eigh.", "titel": "t"})
    new = db.KatalogRecord("2", metadata={"textart": "Abf.; eigh. <Aufschr.>", "titel": "t"})
    cmp = ak.compare_records([old], {"2": new})
    assert cmp.hand_changes == [("2", "own", "partial", True, False)] and cmp.settled
    assert "listed, not blocking" in ak.render_comparison(cmp)


def test_a_renumbered_record_is_mapped_by_katnr_and_shelfmark() -> None:
    """The Access master renumbers or merges a few records between the website's
    half-yearly imports: a store id the export lacks maps to the export's record
    with the same Kat.-Nr. and shelfmark, else the same Kat.-Nr. where unique,
    else the row whose Identisch_mit or mergenr names it."""
    export = ak.read_export(FIXTURES)
    new = {r.record_id: r for r in ak.records_from_export(export)}
    old = [
        # 41800 under another id: Kat.-Nr. 53823 and LH 4, 6, 18 Bl. 1
        db.KatalogRecord("99001", metadata={"katnr": "53823", "signatur": "LH 4, 6, 18 Bl. 1"}),
        # 59095 by Kat.-Nr. alone (the shelfmark respelled)
        db.KatalogRecord("99002", metadata={"katnr": "81115", "signatur": "LH IV, 6, 18 Bl. 2"}),
        # 46308's Identisch_mit names 46307
        db.KatalogRecord("46307", metadata={"katnr": "x", "signatur": "LBrF 1 Bl. 219-220"}),
        db.KatalogRecord("99003", metadata={"katnr": "no such", "signatur": "nowhere"}),
    ]
    rows = [*export.ritter, {"ID": "99009", "mergenr": "99004"}]
    new["99009"] = db.KatalogRecord("99009", metadata={"katnr": "z", "titel": "merged"})
    old.append(db.KatalogRecord("99004", metadata={}))
    mapped = {r.old_id: (r.new_id, r.how) for r in ak.remap_missing(old, new, rows)}
    assert mapped == {
        "99001": ("41800", "Kat.-Nr. and shelfmark"),
        "99002": ("59095", "Kat.-Nr."),
        "46307": ("46308", "Identisch_mit"),
        "99003": (None, "no match"),
        "99004": ("99009", "mergenr"),
    }
    cmp = ak.compare_records(old, new, rows)
    assert cmp.compared == 4 and cmp.missing_in_export == ["99003"] and cmp.unmapped == ["99003"]
    assert cmp.store_records == 5 and cmp.new_in_export == len(new) - 4
    table = ak.render_comparison(cmp)
    assert "compared with the export: 4 (of them 4 under another id)" in table
    assert "- 99001 (Kat.-Nr. 53823, LH 4, 6, 18 Bl. 1): → 41800 by Kat.-Nr. and shelfmark" in table
    assert "- 99003 (Kat.-Nr. no such, nowhere): no match in the export" in table


# ---- the store ------------------------------------------------------------------- #


def _seed(path: Path) -> None:
    """A store as the website parser filled it: the live records and three works."""
    conn = db.init_db(path)
    for wid, set_name, marks in (
        ("00068642", "LeibnizHandschriften", ["LH IV, 6, 18"]),
        ("1665058609", "LeibnizMarginalien", ["Leibn. Marg. 196"]),
        ("00068534", "LeibnizHandschriften", ["LH XXXVII, 5"]),
    ):
        db.upsert_work(conn, db.Work(wid, set_name, shelfmarks=marks))
    for rec in ak.load_site_records(FIXTURES / "site_records_live.json").values():
        db.upsert_katalog_record(conn, rec)
    crosswalk.build_crosswalk(conn)
    conn.commit()
    conn.close()


def test_missing_references_stop_the_write(tmp_path) -> None:
    path = tmp_path / "inv.sqlite"
    _seed(path)
    conn = db.connect(path)
    export_ids = set(_records())
    # the website's records 10270 and 51898 are not in the fixture export: unreferenced, fine
    assert ak.missing_references(conn, export_ids) == {}
    db.upsert_crosswalk(conn, db.CrosswalkMatch("51898", "00068642", "shelfmark", 0.7))
    conn.execute(
        "INSERT INTO gt_lines (line_image_ref, text, source, license_bucket, record_id) "
        "VALUES ('x', 'y', 'z', 'open', '10270')"
    )
    conn.commit()
    assert ak.missing_references(conn, export_ids) == {
        "crosswalk": ["51898"],
        "gt_lines": ["10270"],
    }
    conn.close()
    result = runner.invoke(
        app,
        [
            "catalog",
            "import-access",
            "--db",
            str(path),
            "--csv-dir",
            str(FIXTURES),
            "--export-date",
            "2026-10-19",
            "--write",
        ],
    )
    assert result.exit_code == 1 and "STOP" in result.stdout and "Nothing written" in result.stdout
    assert "gt_lines.record_id" in result.stdout and "10270" in result.stdout
    conn = db.connect(path)
    assert db.count_katalog_records(conn) == 23
    # a crosswalk-only reference is dropped by the rebuild, with a line, no stop
    conn.execute("DELETE FROM gt_lines WHERE record_id = '10270'")
    conn.commit()
    conn.close()
    result = runner.invoke(
        app,
        [
            "catalog",
            "import-access",
            "--db",
            str(path),
            "--csv-dir",
            str(FIXTURES),
            "--export-date",
            "2026-10-19",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "crosswalk: record 51898 is not in the export; its links are dropped" in " ".join(
        result.stdout.split()
    )


def test_write_replaces_the_records_and_rebuilds_the_crosswalk(tmp_path) -> None:
    path = tmp_path / "inv.sqlite"
    _seed(path)
    conn = db.connect(path)
    assert db.count_katalog_records(conn) == 23
    links_before = db.count_crosswalk(conn)
    records = list(_records().values())
    stats = ak.write_import(conn, records, export_date="2026-10-19", csv_dir=FIXTURES)
    assert stats.records_written == 30 and stats.records_deleted == ["10270", "51898"]
    assert db.count_katalog_records(conn) == 30
    assert db.get_katalog_record(conn, "10270") is None
    # the links: LH 4, 6, 18 by its two records' GWLB links, Marg. 196 by PPN, LH 37, 5 by id
    by_work: dict[str, set[str]] = {}
    for m in db.iter_crosswalk(conn):
        by_work.setdefault(m.work_id, set()).add(m.katalog_record_id)
        assert m.match_method == "gwlb_link"
    assert by_work == {
        "00068642": {"41800", "59095"},
        "1665058609": {"1585"},
        "00068534": {"39739"},
    }
    assert stats.links == 4 and links_before == 2  # 39739 by id, 1585 by shelfmark
    assert (stats.works, stats.works_with_records, stats.works_without_records) == (3, 3, 0)
    assert stats.records_per_work == {
        "1": 2,
        "2–5": 1,
        "6–20": 0,
        "21–100": 0,
        "101–500": 0,
        "over 500": 0,
    }
    assert stats.max_records_on_a_work == 2
    assert stats.outside_gwlb == 6 and dict(stats.outside_gwlb_by_domain)["gallica.bnf.fr"] == 1
    assert stats.without_url == 4
    text = ak.render_import_stats(stats)
    assert "30 records written, 2 deleted" in text and "URL_Ms outside the GWLB: 6 records" in text
    run = conn.execute(
        "SELECT stage, params, finished_at FROM runs WHERE run_id = ?", (stats.run_id,)
    ).fetchone()
    assert run["stage"] == "catalog_import_access" and run["finished_at"]
    assert json.loads(run["params"])["export_date"] == "2026-10-19"
    # the record as the readers see it: the website parser's keys, the new ones beside them
    rec = db.get_katalog_record(conn, "1585")
    assert rec.metadata["titel"].startswith("[Marg. in: Dal Pozzo") and rec.gwlb_ids == [
        "1665058609"
    ]
    # idempotent: the same again changes nothing
    again = ak.write_import(conn, records, export_date="2026-10-19", csv_dir=FIXTURES)
    assert again.records_deleted == [] and again.links == 4 and db.count_katalog_records(conn) == 30
    cmp = ak.compare_records(db.iter_katalog_records(conn), {r.record_id: r for r in records})
    assert cmp.compared == 30 and all(a.counts == {"exact": 30} for a in cmp.keys.values())
    assert json.loads(run["params"]).get("remapped") == {}
    conn.close()


def test_cli_dry_run_then_write(tmp_path) -> None:
    path = tmp_path / "inv.sqlite"
    _seed(path)
    base = [
        "catalog",
        "import-access",
        "--db",
        str(path),
        "--csv-dir",
        str(FIXTURES),
        "--export-date",
        "2026-10-19",
    ]
    result = runner.invoke(app, base)
    assert result.exit_code == 0, result.stdout
    out = result.stdout
    assert "ritter.csv 30" in out and "30 rows mapped to records" in out
    assert "compared with the export: 21" in out and "Mapping: **settled**." in out
    assert "Dry run: nothing written" in out
    conn = db.connect(path)
    assert db.count_katalog_records(conn) == 23
    conn.close()
    result = runner.invoke(app, [*base, "--report", str(tmp_path / "agreement.md"), "--write"])
    assert result.exit_code == 0, result.stdout
    assert "30 records written, 2 deleted" in result.stdout
    assert "| textart ✱ | 21 |" in (tmp_path / "agreement.md").read_text(encoding="utf-8")
    # the second dry run compares the store with itself: every key exact on 30
    result = runner.invoke(app, base)
    assert "compared with the export: 30" in result.stdout
    assert "| signatur ✱ | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0 % |" in result.stdout
    # without the export directory
    result = runner.invoke(
        app,
        [
            "catalog",
            "import-access",
            "--db",
            str(path),
            "--csv-dir",
            str(tmp_path / "nowhere"),
            "--export-date",
            "2026-10-19",
        ],
    )
    assert result.exit_code == 1 and "nowhere" in result.stdout


def test_cli_holdings_from_the_export_and_from_the_store(tmp_path) -> None:
    out = tmp_path / "holdings.md"
    result = runner.invoke(
        app,
        [
            "catalog",
            "holdings",
            "--csv-dir",
            str(FIXTURES),
            "--export-date",
            "2026-10-19",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.stdout
    text = out.read_text(encoding="utf-8")
    assert (
        "the Arbeitskatalog export of 2026-10-19" in text
        and "Not available from the export alone" in text
    )
    path = tmp_path / "inv.sqlite"
    _seed(path)
    runner.invoke(
        app,
        [
            "catalog",
            "import-access",
            "--db",
            str(path),
            "--csv-dir",
            str(FIXTURES),
            "--export-date",
            "2026-10-19",
            "--write",
        ],
    )
    result = runner.invoke(app, ["catalog", "holdings", "--db", str(path), "--out", str(out)])
    assert result.exit_code == 0, result.stdout
    text = out.read_text(encoding="utf-8")
    assert "imported into the store" in text and "3 of 3 works carry at least one record" in text
    assert "works 3/3 with records" in result.stdout
