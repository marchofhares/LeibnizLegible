"""Tests for the GWLB letter pool (K2b Task 1): the fetch on a mock transport, the
page model, the layout rules, the parser on synthetic pages and on a small
synthetic PDF built here (no pool text in the repository), and the report."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from leibniz.align import letterpool as LP
from leibniz.cli import app
from leibniz.net import PoliteClient

runner = CliRunner()

# --------------------------------------------------------------------------- #
# A synthetic volume: two pages in the pool's geometry (A4, body 12 pt at x 49,
# the Überlieferung block at 9.6 pt, margin numbers outside the text block).
# --------------------------------------------------------------------------- #

W, H = 595.276, 841.89
BODY = [
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten vnd bin",
    "dero Diener; bedancke mich daß Sie mir die Nachricht zukommen las-",
    "sen; es ist nicht zu zweiffeln daß der Herr von Boineburg [Johann",
    "Christian von Boineburg] alß ein verständiger Mann salutare[s] saget",
]
FRENCH = [
    "Monsieur, je vous remercie de vostre lettre et je suis avec respect",
    "vostre tres humble et tres obeissant serviteur Leibniz",
]


def _line(text, x0, top, size, font="Helvetica", *, width=None, lead_x1=None, tail_x0=None):
    w = width if width is not None else 0.5 * size * len(text)
    return LP.PoolLine(
        text=text,
        x0=x0,
        x1=x0 + w,
        top=top,
        bottom=top + size,
        size=size,
        font=font,
        lead_x1=lead_x1 if lead_x1 is not None else min(x0 + w, x0 + 0.5 * size * 6),
        tail_x0=tail_x0 if tail_x0 is not None else x0 + w - 0.5 * size * 6,
    )


def synthetic_pages() -> list[LP.PoolPage]:
    """The two pages as the extractor would deliver them."""
    p1 = [
        _line("1. HANS MUSTER AN LEIBNIZ", 49.0, 160.0, 12.0),
        _line("Hannover, 1. Januar 1714.", 66.0, 180.0, 12.0),
        _line(
            "U¨berlieferung: K Abfertigung: LBr.98 (Muster) Bl.1–2. 4o. 3 S. Auf Bl.2vo L von N.3.",
            96.8,
            220.0,
            9.6,
        ),
        _line(BODY[0], 72.9, 300.0, 12.0, width=435.0),
        _line(BODY[1], 49.0, 316.7, 12.0, width=459.0),
        _line(BODY[2], 49.0, 333.4, 12.0, width=459.0),
        # the fourth typeset line carries a margin number on the right
        _line(BODY[3] + " 5", 49.0, 350.1, 12.0, width=482.9, tail_x0=522.4),
        _line("3 zweiffeln K, korr. Hrsg.", 72.9, 663.3, 9.6, font="Helvetica-Oblique"),
    ]
    p2 = [
        _line("4", 49.0, 61.0, 10.8),
        _line("hans muster an leibniz,", 122.1, 57.7, 12.0, font="HelveticaCaps"),
        _line("1. Januar 1714 N.2", 346.4, 61.0, 10.8),
        # a margin number glued on the left
        _line("10 Letzte Zeile des ersten Briefes.", 25.1, 93.5, 12.0, lead_x1=36.0, width=300),
        _line("2. LEIBNIZ AN HANS MUSTER", 49.0, 200.0, 12.0),
        _line("Hannover, 2. Januar 1714.", 66.0, 219.1, 12.0),
        _line("U¨berlieferung: L Konzept: LBr.98 Bl.3. 4o. 1 S.", 96.8, 260.0, 9.6),
        _line(FRENCH[0], 72.9, 300.0, 12.0, width=435.0),
        _line(FRENCH[1], 49.0, 316.7, 12.0, width=300.0),
    ]
    return [LP.PoolPage(0, W, H, p1), LP.PoolPage(1, W, H, p2)]


def _pdf_escape(text: str) -> bytes:
    raw = text.encode("cp1252")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def synthetic_pdf() -> bytes:
    """The same two pages as a real PDF (Helvetica, WinAnsi), for pdfplumber.

    Every text run is placed at ``(x, top)`` in the pool's geometry; the
    running head, margin numbers and the note sit where EDMAC puts them.
    """
    pages = [
        [
            (49.0, 160.0, 12.0, "1. HANS MUSTER AN LEIBNIZ"),
            (66.0, 180.0, 12.0, "Hannover, 1. Januar 1714."),
            (
                96.8,
                220.0,
                9.6,
                "U¨berlieferung: K Abfertigung: LBr.98 (Muster) Bl.1–2. 4o. 3 S. "
                "Auf Bl.2vo L von N.3.",
            ),
            (72.9, 300.0, 12.0, BODY[0]),
            (49.0, 316.7, 12.0, BODY[1]),
            (49.0, 333.4, 12.0, BODY[2]),
            (49.0, 350.1, 12.0, BODY[3]),
            (522.4, 350.1, 12.0, "5"),
            (72.9, 663.3, 9.6, "3 zweiffeln K, korr. Hrsg."),
        ],
        [
            (49.0, 61.0, 10.8, "4"),
            (122.1, 57.7, 12.0, "hans muster an leibniz,"),
            (346.4, 61.0, 10.8, "1. Januar 1714 N.2"),
            (25.1, 93.5, 12.0, "10"),
            (49.0, 93.5, 12.0, "Letzte Zeile des ersten Briefes."),
            (49.0, 200.0, 12.0, "2. LEIBNIZ AN HANS MUSTER"),
            (66.0, 219.1, 12.0, "Hannover, 2. Januar 1714."),
            (96.8, 260.0, 9.6, "U¨berlieferung: L Konzept: LBr.98 Bl.3. 4o. 1 S."),
            (72.9, 300.0, 12.0, FRENCH[0]),
            (49.0, 316.7, 12.0, FRENCH[1]),
        ],
    ]
    objs: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    }
    kids = []
    next_id = 4
    for runs in pages:
        pid, cid = next_id, next_id + 1
        next_id += 2
        kids.append(pid)
        parts = [b"BT"]
        for x, top, size, text in runs:
            y = H - top - size
            parts.append(
                f"/F1 {size} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm (".encode() + _pdf_escape(text) + b") Tj"
            )
        parts.append(b"ET")
        stream = b"\n".join(parts)
        objs[cid] = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
        objs[pid] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.276 841.89] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % cid
        )
    objs[2] = (
        b"<< /Type /Pages /Kids ["
        + b" ".join(b"%d 0 R" % k for k in kids)
        + b"] /Count %d >>" % len(kids)
    )
    out = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for oid in sorted(objs):
        offsets[oid] = len(out)
        out += b"%d 0 obj\n" % oid + objs[oid] + b"\nendobj\n"
    xref = len(out)
    n = max(objs) + 1
    out += b"xref\n0 %d\n0000000000 65535 f \n" % n
    for oid in range(1, n):
        out += b"%010d 00000 n \n" % offsets[oid]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref)
    return bytes(out)


# --------------------------------------------------------------------------- #
# The fetch
# --------------------------------------------------------------------------- #

YEAR_PAGE = """<html><body>
<h1>Transkriptionen des Leibniz-Briefwechsels 1714 für die Leibniz-Akademie-Ausgabe (überprüft)</h1>
<a href="/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1714-v1.pdf">v1</a>
<a href="/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1714-v2.pdf">v2</a>
<p>Erscheinungsdatum: 3.&nbsp;November 2020 Download: Dokument (.PDF, 2.97&nbsp;MB) | Metadaten</p>
<p>Lizenz: Creative Commons Namensnennung-Nicht kommerziell&nbsp;4.0 International
(CC&nbsp;BY-NC&nbsp;4.0) Abstract</p>
<p>Bibliographische Angaben Transkriptionen des Leibniz-Briefwechsels 1714 für die
Leibniz-Akademie-Ausgabe (überprüft). Version 2. Hannover, 3. November 2020. BibLaTeX
@Online{LAA-Transkriptionen1714-v2, title = {x}}</p></body></html>"""


def test_parse_year_page_takes_the_newest_version_and_the_metadata() -> None:
    info = LP.parse_year_page(YEAR_PAGE, 1714)
    assert info.version == 2
    assert info.url.endswith("/LAA-Transkriptionen1714-v2.pdf")
    assert info.published == "2020-11-03"
    assert info.title.startswith("Transkriptionen des Leibniz-Briefwechsels 1714")
    assert info.citation.startswith("Transkriptionen des") and "Version 2" in info.citation
    assert info.bibkey == "LAA-Transkriptionen1714-v2"
    assert info.size_note == "2.97 MB" and info.licence == "CC BY-NC 4.0"
    with pytest.raises(ValueError):
        LP.parse_year_page("<html>no pdf here</html>", 1714)


def test_german_date() -> None:
    assert LP.german_date("28. Oktober 2020") == "2020-10-28"
    assert LP.german_date("3. November 2020") == "2020-11-03"
    assert LP.german_date("sometime") is None


def test_fetch_volumes_is_cache_first_and_records_checksums(tmp_path: Path) -> None:
    pdf = synthetic_pdf()
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("-v2.pdf"):
            return httpx.Response(200, content=pdf)
        if "laa-transkriptionen-1714" in request.url.path:
            return httpx.Response(200, text=YEAR_PAGE)
        return httpx.Response(404)

    def client() -> PoliteClient:
        return PoliteClient(
            client=httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0
        )

    dest = tmp_path / "pool"
    sources = tmp_path / "sources.json"
    rows = LP.fetch_volumes(
        [1714], dest_dir=dest, sources_path=sources, client=client(), today=date(2026, 10, 19)
    )
    assert [r.year for r in rows] == [1714] and rows[0].version == 2
    assert (dest / "LAA-Transkriptionen1714-v2.pdf").read_bytes() == pdf
    assert rows[0].sha256 == LP.sha256_of(dest / "LAA-Transkriptionen1714-v2.pdf")
    assert rows[0].bytes == len(pdf) and rows[0].fetched == "2026-10-19"
    doc = json.loads(sources.read_text(encoding="utf-8"))
    assert doc["licence"] == "CC BY-NC 4.0" and doc["licence_bucket"] == "nc"
    assert doc["volumes"][0]["bibkey"] == "LAA-Transkriptionen1714-v2"
    assert all("Hochgeehrter" not in v for v in map(str, doc["volumes"]))  # no text
    # the second run reads the page, verifies the file and fetches no PDF
    n = len(calls)
    LP.fetch_volumes([1714], dest_dir=dest, sources_path=sources, client=client())
    assert [c for c in calls[n:] if c.endswith(".pdf")] == []


# --------------------------------------------------------------------------- #
# Text and layout rules
# --------------------------------------------------------------------------- #


def test_clean_text_composes_the_spacing_diaeresis_and_drops_cid_glyphs() -> None:
    assert LP.clean_text("U¨berlieferung:  vu¨es") == "Überlieferung: vües"
    assert LP.clean_text("a (cid:104)x(cid:105) b (cid:82) c") == "a ⟨x⟩ b c"
    assert LP.clean_text("Gnädiger") == "Gnädiger"  # NFC still composes U+0308


def test_heading_match_and_caps_lines() -> None:
    assert LP.heading_match("2. GEORG LUDEWIG RÖMELING AN LEIBNIZ") == (
        "2",
        "GEORG LUDEWIG RÖMELING AN LEIBNIZ",
    )
    assert (
        LP.heading_match("193. Johann Friedrich Hodann an Leibniz 28. Juli 1714 ..... 290") is None
    )
    assert LP.heading_match("Hannover, 1. Januar 1714.") is None
    assert LP.is_caps_line("GRÜNDUNGSGESCHICHTE DER WESTFÄLISCHEN BISTÜMER")
    assert not LP.is_caps_line("Hannover d. 1t. Jan. 1714.")


def test_head_number_reads_the_outer_edge_not_a_beilage_title() -> None:
    assert LP.head_number("N.48 Beilage zu N. 47 75") == "48"
    assert LP.head_number("15. November 1709 N.52") == "52"
    assert LP.head_number("Beilage zu N. 513 N.515") == "515"
    assert LP.head_number("4 1. Januar 1714") is None


def test_learn_layout_and_margin_numbers() -> None:
    pages = synthetic_pages()
    lay = LP.learn_layout(pages)
    assert (
        lay.body_size == 12.0 and lay.small(pages[0].lines[2]) and not lay.small(pages[0].lines[3])
    )
    assert lay.body_x0 == 49.0
    assert LP.strip_margin_number(pages[0].lines[6], lay) == BODY[3]
    assert LP.strip_margin_number(pages[1].lines[3], lay) == "Letzte Zeile des ersten Briefes."
    # a number inside the text block is text
    inner = _line("Sie haben 1000 Thaler bekommen 15", 49.0, 400.0, 12.0, width=200, tail_x0=230)
    assert LP.strip_margin_number(inner, lay) == inner.text
    lone = _line("25", 25.1, 500.0, 8.4, width=9.5, lead_x1=34.6, tail_x0=25.1)
    assert LP.strip_margin_number(lone, lay) == ""


def test_split_notes_keeps_an_ueberlieferung_block_at_the_foot() -> None:
    pages = synthetic_pages()
    lay = LP.learn_layout(pages)
    lines = pages[0].lines
    texts = [LP.clean_text(ln.text) for ln in lines]
    assert LP.split_notes(lines, texts, lay) == len(lines) - 1  # the note alone
    # a heading whose block is the last thing on the page: not notes
    foot = [
        _line("2. LEIBNIZ AN HANS MUSTER", 49.0, 500.0, 12.0),
        _line("Hannover, 2. Januar 1714.", 66.0, 519.1, 12.0),
        _line("Überlieferung:", 96.8, 560.0, 9.6),
        _line("L Konzept: LBr.98 Bl.3. 4o. 1 S.", 96.8, 574.8, 9.6),
        _line("1 Konzept K, korr. Hrsg.", 72.9, 663.3, 9.6),
    ]
    assert LP.split_notes(foot, [ln.text for ln in foot], lay) == 4


def test_parse_witness() -> None:
    w = LP.parse_witness("Überlieferung: K Abfertigung: LBr.98 (Bothmer) Bl.1–2. 4o. 3 S.")
    assert (w.siglum, w.kind, w.shelfmark) == ("K", "Abfertigung", "LBr.98 (Bothmer) Bl.1–2")
    assert (w.family, w.key, w.blatt, w.shared, w.placeable) == (
        "LBr",
        "LBr 98",
        "1–2",
        False,
        True,
    )
    w = LP.parse_witness(
        "Überlieferung: L1 Konzept: LH XIII Bl.157–158. 1 Bog. 4o. — Auf Bl.157vo–158 L von N.243."
    )
    assert (w.siglum, w.family, w.key, w.blatt, w.shared) == ("L", "LH", "LH 13", "157–158", True)
    assert "von N.243" in (w.shared_note or "")
    w = LP.parse_witness(
        "Überlieferung: K Abfertigung: Hannover GWLB Ms XXIII 720a,2 Bl.3–4. 1 Bog."
    )
    assert w.siglum == "K" and w.family is None and not w.placeable
    w = LP.parse_witness("Überlieferung: K Abfertigung LBr.840 Bl.148–149. 8o.")  # no colon
    assert (w.siglum, w.kind, w.key, w.blatt) == ("K", "Abfertigung", "LBr 840", "148–149")
    w = LP.parse_witness("Überlieferung: K LBr.234 Bl.40–41. 1 Bog.")  # no kind
    assert (w.siglum, w.kind, w.key) == ("K", None, "LBr 234")
    w = LP.parse_witness("Überlieferung: E Erstdruck: Dutens, Opera, 1768, S.5.")
    assert w.siglum == "E" and not w.placeable
    assert LP.parse_witness("").siglum is None


def test_strip_brackets() -> None:
    text, counts = LP.strip_brackets(
        "je serois quasi [d’]avis que le Pere [N.A. Cima] soit salutare[s] et couvents[,] icy "
        "[N.31863]. ⟨Darüber von Leibniz’ Hand:⟩ resp. Gotha [1715]] fin"
    )
    assert (
        text
        == "je serois quasi d’avis que le Pere soit salutares et couvents, icy. resp. Gotha fin"
    )
    assert counts == {"attached": 3, "standalone": 3, "angle": 1, "stray": 1}


# --------------------------------------------------------------------------- #
# The parser
# --------------------------------------------------------------------------- #


def _check_volume(res: LP.ParseResult) -> None:
    assert [ltr.number for ltr in res.letters] == ["1", "2"]
    one, two = res.letters
    assert one.heading == "HANS MUSTER AN LEIBNIZ" and one.place_date == "Hannover, 1. Januar 1714."
    assert one.editorial.startswith("Überlieferung: K Abfertigung: LBr.98 (Muster) Bl.1–2.")
    assert (one.witness.siglum, one.witness.key, one.witness.blatt) == ("K", "LBr 98", "1–2")
    assert one.witness.shared and one.witness.placeable
    assert one.pages == [0, 1] and one.language == "de"
    assert one.text == (
        "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten vnd bin dero Diener; bedancke "
        "mich daß Sie mir die Nachricht zukommen lassen; es ist nicht zu zweiffeln daß der Herr "
        "von Boineburg alß ein verständiger Mann salutares saget Letzte Zeile des ersten Briefes."
    )
    assert one.brackets["attached"] == 1 and one.brackets["standalone"] == 1
    assert two.place_date == "Hannover, 2. Januar 1714." and two.language == "fr"
    assert (two.witness.siglum, two.witness.kind, two.witness.blatt) == ("L", "Konzept", "3")
    assert two.text == " ".join(FRENCH) and two.pages == [1]
    assert res.n_note_lines == 1 and res.n_margin_numbers == 2 and res.anomalies == []
    assert one.letter_id == "1714-1" and two.seq == 2


def test_parse_volume_on_synthetic_pages() -> None:
    _check_volume(LP.parse_volume(1714, synthetic_pages()))


def test_split_notes_takes_a_two_line_body_type_note() -> None:
    pages = synthetic_pages()
    lay = LP.learn_layout(pages)
    foot = [
        _line("je suis.", 49.0, 547.1, 12.0, width=150),
        _line("Caroline", 464.2, 569.9, 12.0, width=44),
        _line("2 ⟨Durch⟩ N.B. Ob die einge-", 78.9, 643.0, 12.0, width=430),
        _line("bundene ... lassen", 49.0, 661.4, 12.0, width=96),
    ]
    assert LP.split_notes(foot, [ln.text for ln in foot], lay) == 2
    # a numbered text line with no gap above it is text
    body = [
        _line("Es ist nothig daß man dahin bedacht sey, wie künfftiges jahr", 49.0, 93.5, 12.0),
        _line("10 Thaler kosten die Bücher, und ist es nicht viel.", 49.0, 110.2, 12.0),
    ]
    assert LP.split_notes(body, [ln.text for ln in body], lay) == 2


def test_finish_keeps_the_first_witness_draft_of_a_multi_draft_letter() -> None:
    letter = LP.Letter(
        year=1715,
        number="549",
        heading="LEIBNIZ AN KAISER KARL VI.",
        place_date=None,
        editorial="Überlieferung: L1 Konzept: LH XLI 9 Bl.151. 2o. L2 Konzept: LH XLI 9 Bl.92.",
        witness=LP.parse_witness(
            "Überlieferung: L1 Konzept: LH XLI 9 Bl.151. 2o. L2 Konzept: LH XLI 9 Bl.92."
        ),
        lines=[
            "⟨L1⟩",
            "Allerdurchleuchtigster Kayser",
            "erster Entwurf",
            "⟨L2⟩",
            "zweyter Entwurf",
        ],
        pages=[792],
    )
    assert letter.witness.label == "L1"
    letter.finish()
    assert letter.segments == ["L1", "L2"] and letter.segment == "L1"
    assert letter.text == "Allerdurchleuchtigster Kayser erster Entwurf"
    assert LP.split_segments(["a", "b"]) == [(None, ["a", "b"])]


def test_parse_volume_records_numbering_jumps_and_repeats() -> None:
    pages = synthetic_pages()
    pages[1].lines[4] = _line("1. LEIBNIZ AN HANS MUSTER", 49.0, 200.0, 12.0)
    res = LP.parse_volume(1714, pages)
    assert [ltr.letter_id for ltr in res.letters] == ["1714-1", "1714-1-2"]
    assert any("printed again" in a for a in res.anomalies)
    assert any("follows N.1" in a for a in res.anomalies)


def test_page_cache_round_trip(tmp_path: Path) -> None:
    pages = synthetic_pages()
    path = tmp_path / "pages.jsonl"
    assert LP.write_page_cache(pages, path) == 2
    back = LP.read_page_cache(path)
    assert [ln.text for ln in back[0].lines] == [ln.text for ln in pages[0].lines]
    assert back[1].lines[3].lead_x1 == 36.0
    _check_volume(LP.parse_volume(1714, back))


def test_letters_round_trip_and_summary(tmp_path: Path) -> None:
    res = LP.parse_volume(1714, synthetic_pages())
    path = LP.write_letters(res, tmp_path / "letters-1714.jsonl")
    back = LP.read_letters(path)
    assert [ltr.letter_id for ltr in back] == ["1714-1", "1714-2"]
    assert back[0].witness.key == "LBr 98" and back[0].text == res.letters[0].text
    summary = LP.summarize([res])
    y = summary["years"][0]
    assert y["letters"] == 2 and y["by_language"] == {"de": 1, "fr": 1}
    assert y["by_siglum"] == {"L": 1, "l": 0, "K": 1, "k": 0, "other": 0}
    assert y["placeable"] == 2 and y["german_placeable"] == 1 and y["shared_leaves"] == 1
    assert summary["total"]["german_placeable_by_siglum"]["K"] == 1
    src = LP.VolumeSource(
        1714,
        1,
        "T",
        "2020-11-03",
        "u",
        "p",
        "f",
        1,
        "sha",
        2,
        "Citation. Version 1.",
        "k",
        "CC BY-NC 4.0",
        "2026-10-19",
    )
    md = LP.render_parse_report(summary, [src])
    assert "| 1714 | 2 | 2 | 1 | 1 | 0 |" in md and "Citation. Version 1." in md
    assert "Hochgeehrter" not in md  # numbers only


# --------------------------------------------------------------------------- #
# Through a real PDF and the CLI
# --------------------------------------------------------------------------- #


def test_iter_pdf_pages_reads_the_synthetic_pdf(tmp_path: Path) -> None:
    pytest.importorskip("pdfplumber")
    pdf = tmp_path / "LAA-Transkriptionen1714-v1.pdf"
    pdf.write_bytes(synthetic_pdf())
    pages = list(LP.iter_pdf_pages(pdf))
    assert len(pages) == 2 and LP.pdf_page_count(pdf) == 2
    texts = [ln.text for ln in pages[0].lines]
    assert texts[0] == "1. HANS MUSTER AN LEIBNIZ"
    assert texts[2].startswith("Überlieferung: K Abfertigung: LBr.98 (Muster) Bl.1–2.")
    assert texts[6].endswith(BODY[3] + " 5")  # the margin number glued onto the line
    assert pages[0].lines[6].tail_x0 > 515
    glued = next(ln for ln in pages[1].lines if "Letzte Zeile" in ln.text)
    assert glued.text.startswith("10 Letzte Zeile") and glued.lead_x1 < 45
    head = " ".join(ln.text for ln in pages[1].lines if ln.top < LP.HEAD_ZONE * H and ln.size < 11)
    assert LP.head_number(head) == "2"
    _check_volume(LP.parse_volume(1714, pages))


def test_letterpool_parse_cli(tmp_path: Path) -> None:
    pytest.importorskip("pdfplumber")
    pdf = tmp_path / "pool" / "LAA-Transkriptionen1714-v1.pdf"
    pdf.parent.mkdir()
    pdf.write_bytes(synthetic_pdf())
    sources = tmp_path / "sources.json"
    LP.write_sources(
        [
            LP.VolumeSource(
                1714,
                1,
                "T",
                "2020-11-03",
                "u",
                "p",
                str(pdf),
                pdf.stat().st_size,
                LP.sha256_of(pdf),
                2,
                "Citation. Version 1.",
                "k",
                "CC BY-NC 4.0",
                "2026-10-19",
            )
        ],
        sources,
    )
    letters_dir = tmp_path / "letters"
    reports = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "align",
            "letterpool-parse",
            "--sources",
            str(sources),
            "--letters-dir",
            str(letters_dir),
            "--reports-dir",
            str(reports),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "2 letters" in result.output
    assert (letters_dir / "pages-1714.jsonl").exists()
    back = LP.read_letters(letters_dir / "letters-1714.jsonl")
    assert [ltr.letter_id for ltr in back] == ["1714-1", "1714-2"]
    summary = json.loads((reports / "letterpool-parse.json").read_text(encoding="utf-8"))
    assert summary["total"]["letters"] == 2 and summary["total"]["german_placeable"] == 1
    assert "Hochgeehrter" not in (reports / "letterpool-parse.md").read_text(encoding="utf-8")
