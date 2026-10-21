"""The holding institution read from a shelfmark, and the holdings report (A3b)."""

from __future__ import annotations

from pathlib import Path

from leibniz import db
from leibniz.catalog import arbeitskatalog as ak
from leibniz.catalog import crosswalk, holdings

FIXTURES = Path(__file__).parent / "fixtures" / "arbeitskatalog"


def test_the_gwlb_collections_are_written_bare() -> None:
    for mark in (
        "LH 35, 3 Bl. 1",
        "LBr. 464 Bl. 1",
        "LBrF 1 Bl. 219-220",
        "LK-MOW Ursinus 1",
        "Ms 13, 869, 1 Bl. 88",
        "Hannover NLB Leibn. Marg. 196",
        "Hannover NLB T-A 1",
    ):
        assert holdings.holding_of(mark) == holdings.GWLB, mark


def test_place_and_institution_from_the_token_table() -> None:
    cases = {
        "Hannover NLA Hann. 153 Acc. 2018/55 Nr. 76 Bl. 111": "Hannover NLA",
        "London BL Add.Mss. 4294 Bl. 67-70": "London BL",
        "London RS Letterbook Suppl.II B-C S.544": "London RS",
        "Paris BN fonds fr. 9502 Bl. 17": "Paris BN",
        "Paris Bibl. de la Sorbonne, fonds Victor Cousin MSVC 4/38": "Paris Bibl. de la Sorbonne",
        "Paris Académie des Sciences Arch. 2 B/25": "Paris Académie des Sciences Arch.",
        "Den Haag KB Cod. 72 H 17": "Den Haag KB",
        "Göttingen StUB Hschr. Philos. 140 Bl. 24-25": "Göttingen StUB",
        "Wolfenbüttel HAB Cod. Guelf. Leibn. 1, 36": "Wolfenbüttel HAB",
        "Berlin GStA BPH Rep. 1": "Berlin GStA",
        "Darmstadt Hessisches StA F 1": "Darmstadt Hessisches StA",
        "Wiesentheid Gräfl. Schönbornsches Archiv Fasz. Leibniz Bl. 9": (
            "Wiesentheid Gräfl. Schönbornsches Archiv"
        ),
        "Wiesentheid 1672, 1 Bl. 128-130": "Wiesentheid",
        "Utrecht Het Utrechts Archief 215": "Utrecht Het Utrechts Archief",
        "Lyon Bibl.de la Ville (Verlust)": "Lyon Bibl.de la Ville",
        "Templin Bibl. des Joachimsthalschen Gymnasiums Oe VIII 111b": (
            "Templin Bibl. des Joachimsthalschen Gymnasiums"
        ),
        "(Erlangen UB Ms 1": "Erlangen UB",
        "Kemnay, Kemnay House, Aberdeenshire 3": "Kemnay",
    }
    for mark, holding in cases.items():
        assert holdings.holding_of(mark) == holding, mark


def test_no_manuscript_named() -> None:
    assert holdings.holding_of("") == holdings.NO_SHELFMARK
    assert holdings.holding_of(None) == holdings.NO_SHELFMARK
    assert holdings.holding_of("Acta Eruditorum, 1686, S. 161-163 (März)") == holdings.PRINTED
    assert holdings.holding_of("Kortholt, Epistolae 4 S. 251-253") == holdings.PRINTED
    assert holdings.holding_of("(Privatbesitz) [Ippenburg] 3") == holdings.PRIVATE
    assert holdings.holding_of("Privatbesitz, Depositum in: Wernigerode 1") == holdings.PRIVATE
    assert holdings.holding_of("(nicht gefunden)") == holdings.UNLOCATED
    assert holdings.holding_of("?") == holdings.UNLOCATED
    assert holdings.holding_of("(Berlin, Henrici Auktion 1920") == holdings.UNLOCATED


def test_place_of() -> None:
    assert holdings.place_of("London BL") == "London"
    assert holdings.place_of("Den Haag KB") == "Den Haag"
    assert holdings.place_of(holdings.PRINTED) == holdings.PRINTED


def _fixture_records() -> list[db.KatalogRecord]:
    return ak.records_from_export(ak.read_export(FIXTURES))


def test_report_from_the_export_fixture() -> None:
    data = holdings.holdings_from_records(
        _fixture_records(), generated_at="2026-10-21T00:00:00Z", source="the fixture"
    )
    assert data.records == 30 and data.works is None
    assert data.by_holding[0] == (holdings.GWLB, 23)
    assert dict(data.by_holding)["Hannover NLA"] == 1
    assert dict(data.by_holding)["London BL"] == 1
    assert dict(data.by_holding)["Oxford Bodl."] == 1
    assert dict(data.by_holding)[holdings.PRINTED] == 3  # Acta Eruditorum, Monathlicher Auszug
    assert dict(data.by_place)["Hannover"] == 24  # the NLB and the NLA
    assert data.gwlb_links == {"id": 19, "PPN": 1}
    domains = dict(data.by_domain)
    assert domains["digitale-sammlungen.gwlb.de"] == 20
    assert {"www.arcinsys.niedersachsen.de", "gallica.bnf.fr", "soeg.kb.dk"} <= set(domains)
    assert data.with_url == sum(domains.values())
    md = holdings.render_holdings_md(data, min_records=1)
    assert "| Hannover NLB | 23 | 76.7 % |" in md
    assert "| gallica.bnf.fr | 1 |" in md
    assert "Not available from the export alone" in md
    assert "licensed CC BY 4.0" in md
    body = data.to_dict()
    assert body["by_holding"][0] == {"holding": holdings.GWLB, "records": 23}
    assert body["works"] is None and body["attribution"]


def test_report_from_a_store_adds_the_works(tmp_path) -> None:
    conn = db.init_db(tmp_path / "inv.sqlite")
    db.upsert_work(conn, db.Work("00068642", "LeibnizHandschriften", shelfmarks=["LH IV, 6, 18"]))
    db.upsert_work(
        conn, db.Work("1665058609", "LeibnizMarginalien", shelfmarks=["Leibn. Marg. 196"])
    )
    db.upsert_work(conn, db.Work("00000001", "LeibnizBriefwechsel", shelfmarks=["LBr. 1"]))
    records = _fixture_records()
    assert holdings.catalog_refreshed(conn) is None
    ak.write_import(conn, records, export_date="2026-10-21", csv_dir=FIXTURES)
    assert holdings.catalog_refreshed(conn) == "2026-10-21"
    data = holdings.holdings_from_store(conn, generated_at="2026-10-21T00:00:00Z")
    conn.close()
    assert data.refreshed == "2026-10-21" and "2026-10-21" in data.source
    assert (data.works, data.works_with_records, data.works_without_records) == (3, 2, 1)
    assert [(s.set_name, s.works, s.with_records) for s in data.by_set] == [
        ("LeibnizBriefwechsel", 1, 0),
        ("LeibnizHandschriften", 1, 1),
        ("LeibnizMarginalien", 1, 1),
    ]
    md = holdings.render_holdings_md(data)
    assert "2 of 3 works carry at least one record" in md
    assert "| LeibnizBriefwechsel | 1 | 0 | 1 |" in md


def test_record_holding_falls_back_to_the_shelfmark() -> None:
    old = db.KatalogRecord("k", metadata={"titel": "x"}, shelfmark_refs=["London BL Add. 1"])
    assert holdings.record_holding(old) == "London BL"
    new = db.KatalogRecord("k", metadata={"holding": "Gotha FB"}, shelfmark_refs=["Gotha FB A 1"])
    assert holdings.record_holding(new) == "Gotha FB"
    assert holdings.record_url(old) is None
    assert crosswalk.CONF_GWLB_LINK == 1.0  # the import rebuilds with the A3 confidences
