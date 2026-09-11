"""Tests for the reading-text extractor (offline; synthetic page layouts)."""

from __future__ import annotations

from pathlib import Path

from leibniz.align import edition as E

W, H = 2400.0, 3300.0
BODY, SMALL = 41.0, 33.0


def _ln(text: str, top: float, *, x0: float = 275.0, size: float = BODY, x1: float | None = None):
    x1 = x1 if x1 is not None else min(W - 200.0, x0 + 9.0 * len(text))
    return E.TextLine(text, x0, x1, top, top + size * 1.2, size)


def _page(index: int, lines: list[E.TextLine]) -> E.PageText:
    return E.PageText(index=index, width=W, height=H, lines=lines)


def _letter_page(index: int, head: str, piece: str, title: str, body: list[str], *, page_no: str):
    """A typical AA letter page: head, heading, dateline, Überlieferung, body, apparatus."""
    lines = [
        _ln(page_no, 240, x0=280, size=37, x1=330),
        _ln("I. HAUS BRAUNSCHWEIG-LÜNEBURG 1690—1691", 238, x0=700, size=37),
        _ln(head, 241, x0=2100, size=37, x1=2200),
        _ln(f"{piece}. {title}", 392, x0=300),
        _ln("[Hannover, Mitte Dezember 1690.]", 462, x0=390),
        _ln("Überlieferung: L Konzept: LBr. 814 Bl. 6. 2 S.", 548, x0=500, size=SMALL),
    ]
    y = 700.0
    for i, t in enumerate(body):
        lines.append(_ln(t, y, x0=275.0 if i else 370.0))
        y += 69
    lines.append(_ln("5", 838, x0=230, size=27, x1=262))  # margin line number
    lines.append(_ln("2 d'icy auf Bl. 19 r° unten erg. L1", y + 150, x0=280, size=SMALL))
    lines.append(_ln("4 Beilagen waren wohl die Abschriften", y + 203, x0=280, size=SMALL))
    return _page(index, lines)


BODY_A = [
    "Weilen iezo diesen morgen auf gndsten befehl eine reise nach Hildesheim thun muß,",
    "und der Schlüterschen Herrn Erben brief mir erst gestern zu kommen, so habe in eil",
    "Cämmerer dieses zu vernehmen geben wollen, daß ich ja wohl fundiret das inte-",
    "resse der 100 thl. so sie von mir fordern mit dem interesse der 300 thl. 10",
]


def test_classify_letter_page_separates_zones() -> None:
    pg = _letter_page(58, "N. 10", "10", "LEIBNIZ AN FRANZ KUCKUCK", BODY_A, page_no="12")
    pr = E.classify_page(pg, sizes=E.TypeSizes(BODY, SMALL, 37.0))
    assert pr.head_pieces == ["10"]
    assert pr.printed_page == 12
    assert pr.headings == ["10"]
    text = pr.reading_lines
    assert text[0].startswith("Weilen iezo")  # body starts after dateline + Überlieferung
    assert not any("Überlieferung" in t or "Hannover, Mitte" in t for t in text)
    assert not any("Beilagen" in t or "d'icy" in t for t in text)  # apparatus gone
    assert text[-1].endswith("300 thl.")  # glued margin number "10" stripped
    assert pr.n_apparatus == 2


def test_head_pieces_parsing() -> None:
    assert E.head_pieces_of("N. 13. 14") == ["13", "14"]
    assert E.head_pieces_of("N. II. 12") == ["11", "12"]
    assert E.head_pieces_of("N. 9 I. HAUS BRAUNSCHWEIG-LÜNEBURG 1690—1691 II") == ["9"]
    assert E.head_pieces_of("N. 1 1") == ["11"]
    assert E.head_pieces_of("4 GEORGIUS ULICOVIUS LITHUANUS 1669 N.1") == ["1"]
    assert E.head_pieces_of("INHALTSVERZEICHNIS XIII") == []


def test_heading_match_shapes() -> None:
    assert E.heading_match("13. GOTTFRIED CHRISTIAN OTTO AN LEIBNIZ") == ("13", "")
    assert E.heading_match("5. CHILIAN Schrader AN LEIBNIZ") == ("5", "")  # small caps as lowercase
    assert E.heading_match("i. LEIBNIZ AN HERZOG ANTON ULRICH") == ("1", "")  # OCR'd 1
    assert E.heading_match("1. Que la verité soit connue") is None  # an enumerated reading line
    assert E.heading_match("(§. 1.) Demnach Ihre hochfürstl.") is None
    assert E.heading_match("130 a. LEIBNIZ AN ARNAULD") == ("130", "a")


def test_roman_section_title_is_not_a_heading_unless_confirmed() -> None:
    body = ["Nachdem E. Hochf. Durchl. geschwinde abreise mir die zeit nicht gelaßen habe ich"]
    toc = _page(
        11,
        [
            _ln("INHALTSVERZEICHNIS", 244, x0=947, size=31),
            _ln("I. HAUS BRAUNSCHWEIG-LÜNEBURG 1690—1691", 600, x0=300),
            _ln("1. Leibniz an Herzog Anton Ulrich Ende September 1690 . . . 3", 700, x0=235),
        ],
    )
    pr = E.classify_page(toc, sizes=E.TypeSizes(BODY, SMALL, 37.0))
    assert pr.head_pieces == [] and pr.headings == []
    # the same Roman-looking line IS a heading when the head confirms piece 11
    pg = _letter_page(59, "N. II. 12", "II", "LUDOLF HUGO AN LEIBNIZ", body, page_no="13")
    pr = E.classify_page(pg, sizes=E.TypeSizes(BODY, SMALL, 37.0))
    assert pr.head_pieces == ["11", "12"] and pr.headings == ["11"]


def test_size_threshold_learns_two_clusters() -> None:
    pages = [_letter_page(i, f"N. {i}", str(i), "A AN B", BODY_A, page_no=str(i)) for i in range(3)]
    sizes = E.size_threshold(pages)
    assert sizes.body == BODY and sizes.apparatus == SMALL
    assert SMALL < sizes.threshold < BODY
    # a single-cluster volume falls back to the ratio
    one = [_page(0, [_ln("x" * 40, 500), _ln("y" * 40, 600)])]
    assert E.size_threshold(one).apparatus is None


def test_assemble_carries_piece_across_pages_and_splits_at_headings() -> None:
    sizes = E.TypeSizes(BODY, SMALL, 37.0)
    p1 = _letter_page(58, "N. 10", "10", "LEIBNIZ AN FRANZ KUCKUCK", BODY_A, page_no="12")
    # page 59: piece 10 continues, then 11 starts (head lists the starter only)
    cont = ["gehabt und also durch solche billigmäßige compensation mein credit verhoffentlich"]
    p2 = _page(
        59,
        [
            _ln("13", 240, x0=280, size=37, x1=330),
            _ln("N. 11", 241, x0=2100, size=37, x1=2200),
            _ln(cont[0], 400),
            _ln("11. LUDOLF HUGO AN LEIBNIZ", 700, x0=300),
            _ln("Le Secrétaire de Lunebourg Mr Walter estant arrivé icy, et ayant apporté", 900),
            _ln("Zu N. 11: K antwortet auf einen nicht gefundenen Brief", 2900, size=SMALL),
        ],
    )
    vol = E.assemble_pieces(E.classify_page(p, sizes=sizes) for p in (p1, p2))
    assert set(vol.pieces) == {"10", "11"}
    assert vol.pieces["10"].pages == [58, 59]
    assert vol.pieces["10"].printed_pages == [12, 13]
    assert vol.pieces["10"].lines[-1] == cont[0]
    assert vol.pieces["11"].lines[0].startswith("Le Secrétaire")
    assert vol.n_eligible_pages == 2 and vol.n_reading_pages == 2 and vol.anomalies == []


def test_assemble_drops_unplaceable_tail_and_resyncs() -> None:
    sizes = E.TypeSizes(BODY, SMALL, 37.0)
    p1 = _letter_page(58, "N. 10", "10", "LEIBNIZ AN FRANZ KUCKUCK", BODY_A, page_no="12")
    # head says 11 and 12 start here but only 11's heading is legible
    p2 = _page(
        59,
        [
            _ln("N. 11. 12", 241, x0=2100, size=37, x1=2300),
            _ln("11. LUDOLF HUGO AN LEIBNIZ", 400, x0=300),
            _ln("Le Secrétaire de Lunebourg Mr Walter estant arrivé icy, et ayant apporté", 600),
            _ln("Vôtre Excellence aura sans doute reçeuë avec la derniere poste une lettre", 1600),
        ],
    )
    # page 60: plain continuation of 12
    p3 = _page(
        60,
        [
            _ln("N. 12", 241, x0=2100, size=37, x1=2200),
            _ln("donc encor des autres. Au reste je ne sçay rien, qui soit arrivé, qui me", 400),
        ],
    )
    vol = E.assemble_pieces(E.classify_page(p, sizes=sizes) for p in (p1, p2, p3))
    assert "11" not in vol.pieces  # its lines were unplaceable (12's start unknown)
    assert vol.pieces["12"].lines == [
        "donc encor des autres. Au reste je ne sçay rien, qui soit arrivé, qui me"
    ]
    assert any("no heading found for N.12" in a for a in vol.anomalies)


def test_front_matter_and_garbled_heads_contribute_nothing() -> None:
    sizes = E.TypeSizes(BODY, SMALL, 37.0)
    intro = _page(
        5,
        [
            _ln("EINLEITUNG", 244, x0=947, size=37),
            _ln("Der vorliegende Band enthält den Briefwechsel des Jahres 1690 und 1691", 500),
        ],
    )
    p1 = _letter_page(58, "N. 10", "10", "LEIBNIZ AN FRANZ KUCKUCK", BODY_A, page_no="12")
    garbled = _page(
        59,
        [
            _ln("N. 6", 241, x0=2100, size=37, x1=2200),  # OCR lost a digit of "N. 10"
            _ln("gehabt und also durch solche billigmäßige compensation mein credit", 400),
        ],
    )
    vol = E.assemble_pieces(E.classify_page(p, sizes=sizes) for p in (intro, p1, garbled))
    assert set(vol.pieces) == {"10"}
    assert vol.pieces["10"].pages == [58, 59]  # garbled head ignored, page kept on 10
    assert any("head N.6 vs current 10" in a for a in vol.anomalies)


def test_join_lines_rejoins_hyphenation() -> None:
    assert E.join_lines(
        ["quoyque peu impor¬", "tantes en elles mêmes", "Braunschweig-", "Lüneburg"]
    ) == ("quoyque peu importantes en elles mêmes\nBraunschweig-\nLüneburg")


def test_iter_hocr_pages_reads_lines_and_sizes(tmp_path: Path) -> None:
    hocr = """<html><body>
    <div class='ocr_page' title='bbox 0 0 2419 3347; ppageno 58'>
      <div class='ocr_carea'><p class='ocr_par'>
        <span class='ocr_line' title='bbox 275 254 321 290; x_size 33'>
          <span class='ocrx_word'>12</span></span>
        <span class='ocr_line' title='bbox 301 392 1167 440; x_size 41.2'>
          <span class='ocrx_word'>10.</span> <span class='ocrx_word'>LEIBNIZ</span></span>
      </p></div>
    </div></body></html>"""
    path = tmp_path / "v_hocr.html"
    path.write_text(hocr, encoding="utf-8")
    pages = list(E.iter_hocr_pages(path))
    assert len(pages) == 1
    pg = pages[0]
    assert (pg.index, pg.width, pg.height) == (58, 2419.0, 3347.0)
    assert [ln.text for ln in pg.lines] == ["12", "10. LEIBNIZ"]
    assert pg.lines[1].size == 41.2 and pg.lines[1].x0 == 301.0


def test_headless_layout_continues_piece_across_bare_page_numbers() -> None:
    """A volume set without running heads (only page numbers) still assembles."""
    sizes = E.TypeSizes(BODY, SMALL, 37.0)
    p1 = _page(
        10,
        [
            _ln("41", 130, x0=2100, x1=2160),
            _ln("2. URSACHEN WARUM CANNSTATT USW.", 500, x0=275),
            _ln("Demnach Ihre hochfürstl. Durchl. von Würtenberg löblichste gedancken", 700),
        ],
    )
    p2 = _page(
        11,
        [
            _ln("42", 130, x0=2100, x1=2160),  # bare page number, no "N." head
            _ln("schläge führet, wie dero von Gott ohne das mit allen guthen überschüttetes", 400),
        ],
    )
    index = _page(
        12,
        [
            _ln("SACHVERZEICHNIS", 130, x0=900, size=37),
            _ln("aphorismus: A S. 262.6 544.11 und weiter im text", 400),
        ],
    )
    vol = E.assemble_pieces(E.classify_page(p, sizes=sizes) for p in (p1, p2, index))
    assert list(vol.pieces) == ["2"]
    assert vol.pieces["2"].pages == [10, 11]  # the index page is not swept in
