"""Tests for the letter-pool test set (K2b Task 2): placement by reason on a seeded
fixture store, the disjointness check, the seeded draw and halves, the frozen files."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from leibniz import db
from leibniz.align import letterpool as LP
from leibniz.align import letterpool_set as S
from leibniz.cli import app

runner = CliRunner()


def _seed_store(path: Path) -> None:
    """Two works: LBr 10 (folios 1–3, lines on 1–2 only) and LH 4, 1 (folio 5, no lines)."""
    conn = db.init_db(path)
    db.upsert_work(conn, db.Work("W1", "LeibnizBriefwechsel", shelfmarks=["LBr. 10"]))
    db.upsert_work(conn, db.Work("W2", "LeibnizHandschriften", shelfmarks=["LH 4, 1"]))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    for seq, lab in enumerate(["1r", "1v", "2r", "2v", "3r", "3v"], start=1):
        db.upsert_page(conn, db.Page(work_id="W1", seq=seq, label=lab, status="recognized"))
        n = 3 if seq <= 4 else 0
        for k in range(n):
            pid = f"W1:{seq:04d}"
            db.insert_line(conn, db.Line(page_id=pid, line_seq=k, run_id=seg, status="machine"))
            db.set_line_recognition(
                conn, pid, k, text=f"zeile {k}", conf=0.9, model="h", run_id=rec
            )
    for seq, lab in enumerate(["5r", "5v"], start=1):
        db.upsert_page(conn, db.Page(work_id="W2", seq=seq, label=lab, status="recognized"))
    conn.commit()
    conn.close()


def _letter(
    year: int, number: str, siglum: str, shelfmark: str, text: str, *, lang="de", shared=False
) -> LP.Letter:
    block = f"Überlieferung: {siglum} Abfertigung: {shelfmark}. 4o. 2 S."
    if shared:
        block += " — Auf Bl.2vo L von N.9."
    ltr = LP.Letter(
        year=year,
        number=number,
        heading="JEMAND AN LEIBNIZ",
        place_date=f"Hannover, 1. Januar {year}.",
        editorial=block,
        witness=LP.parse_witness(block),
        lines=text.split("|"),
        pages=[1],
    )
    ltr.finish()
    ltr.language = lang  # the synthetic texts are short; the language is given
    return ltr


GERMAN = (
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten|vnd bedancke mich daß Sie es gesandt"
)
FRENCH = "Monsieur, je vous remercie de vostre lettre|et je suis vostre serviteur"


def _letters() -> list[LP.Letter]:
    return [
        _letter(1708, "1", "L", "LBr.10 Bl.1–2", GERMAN),  # placed, Leibniz's hand
        _letter(1708, "2", "K", "LBr.10 Bl.2", GERMAN),  # placed (2r, 2v)
        _letter(1709, "1", "K", "LBr.10 Bl.1", GERMAN),  # placed
        _letter(1709, "2", "k", "LBr.10 Bl.1v–2r", GERMAN),  # placed, two pages
        _letter(1709, "3", "K", "LBr.10 Bl.1", GERMAN, shared=True),  # shared
        _letter(1710, "1", "K", "LBr.99 Bl.1", GERMAN),  # no work
        _letter(1710, "2", "L", "LH IV 1 Bl.9", GERMAN),  # no canvas in range
        _letter(1710, "3", "K", "LH IV 1 Bl.5", GERMAN),  # no lines
        _letter(1710, "4", "l", "LBr.10 Bl.3", GERMAN),  # no lines (folio 3 has none)
        _letter(1710, "5", "K", "LBr.10 Bl.1", GERMAN, lang="mixed"),  # mixed: apart
        _letter(1710, "6", "K", "LBr.10 Bl.1", FRENCH, lang="fr"),  # French: not German
        _letter(1710, "7", "K", "Wien ÖNB cod. 12 Bl.1", GERMAN),  # not placeable at all
    ]


def test_place_letters_by_reason(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed_store(store)
    from leibniz.align.audit_reach import open_readonly

    conn = open_readonly(store)
    try:
        de, mixed = S.german_letters(_letters())
        assert [m.letter_id for m in mixed] == ["1710-5"]
        assert len(de) == 9  # the French and the Vienna letter are out
        placed = S.place_all(conn, de)
    finally:
        conn.close()
    by = {p.letter_id: p for p in placed}
    assert by["1708-1"].reason == "placed" and by["1708-1"].page_ids == [
        "W1:0001",
        "W1:0002",
        "W1:0003",
        "W1:0004",
    ]
    assert by["1708-1"].n_lines == 12 and by["1708-1"].labels == ["1r", "1v", "2r", "2v"]
    assert by["1708-2"].page_ids == ["W1:0003", "W1:0004"] and by["1708-2"].n_lines == 6
    assert by["1709-2"].page_ids == ["W1:0002", "W1:0003"]  # Bl. 1v–2r: the sides count
    assert by["1709-3"].reason == "shared" and "von N.9" in (by["1709-3"].shared_note or "")
    assert by["1710-1"].reason == "no_work"
    assert by["1710-2"].reason == "no_canvas" and by["1710-2"].key == "LH 4,1"
    assert by["1710-3"].reason == "no_lines" and by["1710-3"].page_ids == ["W2:0001", "W2:0002"]
    assert by["1710-4"].reason == "no_lines"
    assert by["1708-1"].text_sha256 == S.text_sha256(de[0].text) and by["1708-1"].n_chars > 0


def test_overlaps_and_allocation(tmp_path: Path) -> None:
    p = S.Placed(
        "1708-1",
        1708,
        "1",
        "L",
        None,
        "de",
        None,
        None,
        None,
        "placed",
        "W1",
        ["W1:0001", "W1:0002"],
    )
    q = S.Placed("1708-2", 1708, "2", "K", None, "de", None, None, None, "no_work")
    assert S.overlaps([p, q], {"W1:0002", "X:0001"}) == {"1708-1": ["W1:0002"]}
    pieces = tmp_path / "german_pieces.jsonl"
    pieces.write_text(
        json.dumps({"record_id": "r", "page_ids": ["W1:0001"]}) + "\n", encoding="utf-8"
    )
    assert S.k2_pages(pieces) == {"W1:0001"}
    held = tmp_path / "heldout.csv"
    held.write_text(
        "page_id,work_id,file,split,status\nW1:0002,W1,f,noisy,matched\n", encoding="utf-8"
    )
    assert S.heldout_pages(held) == {"W1:0002"}
    assert S.k2_pages(tmp_path / "missing.jsonl") == set()
    assert S.allocate({("K", 1708): 3, ("K", 1709): 1, ("k", 1709): 1}, 2) == {
        ("K", 1708): 1,
        ("K", 1709): 1,
        ("k", 1709): 0,
    }
    assert S.allocate({("K", 1708): 3}, 10) == {("K", 1708): 3}


def _placed_pool() -> list[S.Placed]:
    rows = []
    k = 0
    for year in (1708, 1709, 1710):
        for sig, n in (("L", 2), ("K", 6), ("k", 1)):
            for _i in range(n):
                k += 1
                rows.append(
                    S.Placed(
                        f"{year}-{k}",
                        year,
                        str(k),
                        sig,
                        "Abfertigung",
                        "de",
                        "LBr.1 Bl.1",
                        "LBr 1",
                        "1",
                        "placed",
                        "W",
                        [f"W:{k:04d}"],
                        ["1r"],
                        10,
                        100,
                        "x",
                    )
                )
    rows.append(S.Placed("1711-99", 1711, "99", "L", None, "de", None, None, None, "no_work"))
    return rows


def test_draw_takes_every_own_letter_and_a_matching_sample_then_splits() -> None:
    placed = _placed_pool()
    drawn = S.draw(placed, seed=7)
    own = [p for p in drawn if p.siglum == "L"]
    corr = [p for p in drawn if p.siglum in ("K", "k")]
    assert len(own) == 6 and len(corr) == 6  # six L placed, six correspondents drawn
    assert all(p.reason == "placed" for p in drawn)
    assert {p.year for p in corr} == {1708, 1709, 1710}  # spread over the years
    again = S.draw(_placed_pool(), seed=7)
    assert [p.letter_id for p in again] == [p.letter_id for p in drawn]  # reproducible
    other = S.draw(_placed_pool(), seed=8)
    assert [p.letter_id for p in other if p.siglum == "L"] == [p.letter_id for p in own]
    S.split_halves(drawn, seed=7)
    halves = {h: [p for p in drawn if p.half == h] for h in S.HALVES}
    assert len(halves["selection"]) == 6 and len(halves["test"]) == 6
    for year in (1708, 1709, 1710):
        sel = sum(1 for p in halves["selection"] if p.year == year and p.siglum == "L")
        assert sel == 1  # each (L, year) cell of two is split one and one
    assert (
        S.draw(placed, seed=7, n_kk=2)
        and sum(1 for p in placed if p.drawn and p.siglum != "L") == 2
    )


def test_build_set_writes_the_frozen_files_and_the_report(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed_store(store)
    from leibniz.align.audit_reach import open_readonly

    letters = _letters()
    pieces = tmp_path / "german_pieces.jsonl"
    pieces.write_text(
        json.dumps({"record_id": "r", "page_ids": ["W1:0003"]}) + "\n", encoding="utf-8"
    )
    conn = open_readonly(store)
    try:
        placed, summary = S.build_set(
            conn, letters, seed=3, german_pieces=pieces, heldout=tmp_path / "none.csv"
        )
    finally:
        conn.close()
    r = summary["by_reason"]
    assert r["placed"]["all"] == 4 and r["shared"]["all"] == 1 and r["no_work"]["all"] == 1
    assert r["no_canvas"]["all"] == 1 and r["no_lines"]["all"] == 2
    assert summary["mixed_letters_apart"] == 1 and summary["german_letters"] == 9
    assert summary["disjointness"]["k2_german_pieces"]["pages"] >= 1
    drawn = [p for p in placed if p.drawn]
    assert (
        sum(1 for p in drawn if p.siglum == "L") == 1
        and sum(1 for p in drawn if p.siglum in "Kk") == 1
    )
    assert {p.half for p in drawn} == {"selection", "test"}
    csv_path, texts_path = S.write_testset(
        drawn,
        {l_.letter_id: l_ for l_ in letters},
        csv_path=tmp_path / "set.csv",
        texts_path=tmp_path / "texts.jsonl",
    )
    rows = S.read_testset(csv_path)
    assert [r_["letter_id"] for r_ in rows] == sorted(p.letter_id for p in drawn)
    assert (
        rows[0]["page_ids"]
        and rows[0]["text_sha256"]
        and "Hochgeehrter" not in csv_path.read_text(encoding="utf-8")
    )
    texts = S.read_texts(texts_path)
    assert texts[rows[0]["letter_id"]]["text"].startswith("Hochgeehrter")
    assert S.text_sha256(texts[rows[0]["letter_id"]]["text"]) == rows[0]["text_sha256"]
    md = S.render_report(summary)
    assert "| placed |" in md and "selection half" in md and "Hochgeehrter" not in md
    placement = S.write_placement(placed, tmp_path / "placement.csv")
    assert placement.read_text(encoding="utf-8").count("\n") == 10  # header + 9 letters


def test_letterpool_set_cli(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed_store(store)
    letters_dir = tmp_path / "letters"
    letters_dir.mkdir()
    res = LP.ParseResult(year=1708, letters=_letters(), n_pages=1)
    LP.write_letters(res, letters_dir / "letters-1708.jsonl")
    out = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "align",
            "letterpool-set",
            "--db",
            str(store),
            "--letters-dir",
            str(letters_dir),
            "--german",
            str(tmp_path / "none.jsonl"),
            "--heldout",
            str(tmp_path / "none.csv"),
            "--testset",
            str(out / "testset.csv"),
            "--placement",
            str(out / "placement.csv"),
            "--texts",
            str(tmp_path / "texts.jsonl"),
            "--reports-dir",
            str(out),
            "--seed",
            "3",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "placed 4" in result.output and "shared 1" in result.output
    assert (out / "letterpool-set.md").exists() and (out / "letterpool-set.json").exists()
    assert len(S.read_testset(out / "testset.csv")) == 2
