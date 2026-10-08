"""Tests for the PAGE XML reader (offline, on the philiumm_sample fixture)."""

from __future__ import annotations

from pathlib import Path

from leibniz.align.pagexml import parse_page_xml, parse_points, region_type

FIX = Path(__file__).parent / "fixtures" / "philiumm_sample"


def test_region_type_and_points() -> None:
    assert region_type("structure {type:MainZone;}") == "MainZone"
    assert region_type("structure {type:GraphicZone-formula;}") == "GraphicZone-formula"
    assert region_type(None) is None and region_type("readingOrder {index:0;}") is None
    assert parse_points("10,20 30,40 x,y 5.5,6.9") == [(10, 20), (30, 40), (5, 6)]
    assert parse_points(None) == []


def test_parse_page_xml_lines_in_document_order() -> None:
    doc = parse_page_xml(FIX / "HTR" / "a.xml")
    assert (doc.image_filename, doc.width, doc.height) == ("a.jpg", 1000, 800)
    assert doc.regions == [("r0", "DigitizationArtefactZone"), ("r1", "MainZone")]
    assert [ln.id for ln in doc.lines] == ["stamp", "a1", "a2", "a3", "a4"]
    assert [ln.index for ln in doc.lines] == [0, 1, 2, 3, 4]
    stamp = doc.lines[0]
    assert stamp.region_id == "r0" and stamp.region_type == "DigitizationArtefactZone"
    assert stamp.text == "LEIBNIZ BIBLIOTHEK HANNOVER" and stamp.conf == 0.5
    assert stamp.coords == [(10, 710), (400, 710), (400, 760), (10, 760)]
    assert stamp.baseline == [(10, 750), (400, 750)]
    assert doc.lines[4].text == "" and doc.lines[4].conf is None  # empty Unicode
    assert [ln.id for ln in doc.lines_of("r1")] == ["a1", "a2", "a3", "a4"]
    assert doc.texts()[1].startswith("Mechanici")


def test_parse_page_xml_from_bytes_and_string_without_geometry() -> None:
    xml = (
        '<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">'
        '<Page imageFilename="x.jpg"><TextRegion id="r9"><TextLine id="l">'
        '<TextEquiv passim_skipped="low_conf:0.4"><Unicode>abc</Unicode></TextEquiv>'
        "</TextLine><TextLine id='m'/></TextRegion></Page></PcGts>"
    )
    for src in (xml, xml.encode("utf-8")):
        doc = parse_page_xml(src)
        assert doc.width is None and len(doc.lines) == 2
        assert doc.lines[0].text == "abc" and doc.lines[0].attributes == {
            "passim_skipped": "low_conf:0.4"
        }
        assert doc.lines[1].text == "" and doc.lines[1].coords == []
        assert doc.regions == [("r9", None)]


def test_their_output_keeps_ids_and_scores() -> None:
    theirs = parse_page_xml(FIX / "htr_replaced_gt" / "a.xml")
    by = {ln.id: ln for ln in theirs.lines}
    assert by["a1"].text.startswith("Mechanici") and by["a1"].conf == 0.93
    assert by["a3"].text == "" and by["stamp"].text == ""
