"""``leibniz align audit-sheet-k2`` (K3b-prep, Task 4): a further sheet of the
reader's minted lines — by hand, without the lines, records and pages already
used, with the neighbouring lines for context — on the fixture store's German
rows."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest
from tests.conftest import K2_READER_SOURCE, PACK_FIXTURES, W3, W4
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import audit
from leibniz.align import kurrent_mint as M
from leibniz.cli import app
from leibniz.images.fetch import cache_relpath

runner = CliRunner()
READER = "trocr-kurrent-xvi-xvii"
P1, P2, Q1 = f"{W3}:0001", f"{W3}:0002", f"{W4}:0001"
JPEG, PNG = "data:image/jpeg;base64,", "data:image/png;base64,"


@pytest.fixture
def sheet(german_store_path: Path, tmp_path: Path) -> dict:
    """The fixture store with the correspondent's letter minted by the reader too,
    its three cached page images, and the decisions that tell the hands apart."""
    from PIL import Image

    conn = db.connect(german_store_path)
    conn.execute(
        "UPDATE gt_lines SET source = ? WHERE record_id = 'k-4402'",
        (K2_READER_SOURCE.format(channel="ia").replace("k-4101", "k-4402"),),
    )
    conn.commit()
    conn.close()
    images = tmp_path / "images"
    for work, seq, size in ((W3, 1, (2000, 2500)), (W3, 2, (2000, 2500)), (W4, 1, (1800, 2400))):
        path = images / cache_relpath(work, seq)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, (250, 240, 220)).save(path)
    decisions = tmp_path / "k2-decisions.jsonl"
    rows = [
        M.PieceDecision("k-4101", "AA IV,3 N.41", "IV,3", "minted", leibniz_hand=True, hand="own"),
        M.PieceDecision("k-4402", "AA IV,4 N.2", "IV,4", "minted", hand="other"),
    ]
    decisions.write_text("".join(json.dumps(d.as_dict()) + "\n" for d in rows), encoding="utf-8")
    common = [
        "align",
        "audit-sheet-k2",
        "--db",
        str(german_store_path),
        "--readings-dir",
        str(PACK_FIXTURES),
        "--images",
        str(images),
        "--decisions",
        str(decisions),
        "--out",
        str(tmp_path / "sheets"),
    ]
    return {"store": german_store_path, "images": images, "args": common, "tmp": tmp_path}


def _csv(path: Path, header: str, *rows: str) -> Path:
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def _lines(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_sample_lines_takes_refs_and_pages_out_of_the_pool(sheet: dict) -> None:
    conn = db.connect(sheet["store"])
    try:
        every = audit.sample_lines(conn, 10, seed=3, reader=READER)
        assert len(every) == 6
        cut = audit.sample_lines(
            conn, 10, seed=3, reader=READER, exclude_refs=[db.line_id(P1, 0)], exclude_pages=[P2]
        )
        assert sorted(ln.ref for ln in cut) == [
            db.line_id(P1, 1),
            db.line_id(P1, 3),
            db.line_id(Q1, 0),
        ]
        # the same draw for the same seed, and an exclusion that names nothing excludes nothing
        again = audit.sample_lines(
            conn, 10, seed=3, reader=READER, exclude_refs=[db.line_id(P1, 0)], exclude_pages=[P2]
        )
        assert [ln.ref for ln in again] == [ln.ref for ln in cut]
        none = audit.sample_lines(conn, 10, seed=3, reader=READER, exclude_pages=["nowhere:0001"])
        assert sorted(ln.ref for ln in none) == sorted(ln.ref for ln in every)
        # equal per stratum over what is left: one stratum's lines gone, the other fills the sheet
        two = audit.sample_lines(conn, 2, seed=3, reader=READER, exclude_pages=[Q1])
        assert {ln.stratum for ln in two} == {"heavy_revision"}
    finally:
        conn.close()
    assert audit.page_of_ref(db.line_id(P1, 7)) == P1
    assert audit.page_of_ref(f"{P1}#xywh=1,2,3,4") == P1


def test_cli_own_hand_with_exclusions_and_context(sheet: dict) -> None:
    tmp = sheet["tmp"]
    first = _csv(tmp / "k2-audit-lines.csv", "ref,stratum", f"{db.line_id(P1, 0)},heavy_revision")
    val = _csv(tmp / "k3-val-pieces.csv", "unit,record_id,volume", "k-9,k-9,IV 3")
    pool = _csv(
        tmp / "letterpool-testset.csv", "letter_id,page_ids,n_pages", f"1708-1,{P2} X:0001,2"
    )
    held = _csv(tmp / "heldout_pages.csv", "page_id,work_id", "Y:0002,Y")
    args = [*sheet["args"], "--hand", "own", "--n", "3", "--context", "1"]
    args += ["--exclude-refs", str(first), "--exclude-records", str(val)]
    args += ["--exclude-pages", str(pool), "--exclude-pages", str(held)]
    res = runner.invoke(app, args)
    assert res.exit_code == 0, res.output
    out = " ".join(res.output.split())
    assert "(2 lines: heavy_revision 2; by hand leibniz_hand 2)" in out
    assert "hand own, context 1" in out and "1 lines, 1 records, 3 pages" in out
    assert "2 lines drawn of the 3 asked" in out
    rows = _lines(tmp / "sheets" / "k3b-audit-lines.csv")
    assert sorted(r["ref"] for r in rows) == [db.line_id(P1, 1), db.line_id(P1, 3)]
    assert {r["group"] for r in rows} == {"leibniz_hand"} and {r["image"] for r in rows} == {"yes"}
    page = (tmp / "sheets" / "k3b-audit.html").read_text(encoding="utf-8")
    # each line's own strip, and one neighbour above and one below it
    assert page.count(PNG) == 2 and page.count(JPEG) == 4
    assert page.count("alt='the line before'") == 2 and page.count("alt='the line after'") == 2
    item = page.split("<div class='item'")[1]
    assert (
        item.index("the line before")
        < item.index("alt='line image'")
        < item.index("the line after")
    )
    # the help text, bilingual: the verdict is for the middle strip; where a correction goes
    assert "your verdict is for the middle strip" in page
    assert "Ihr Urteil gilt dem mittleren Streifen" in page
    assert "as the whole line's text in a column of its own" in page
    assert "als Text der ganzen Zeile in einer eigenen Spalte" in page
    assert "Half of the lines" not in page and "richtig" in page
    # the field for it, and a download in the shape audit-convert reads
    assert page.count("<input class='transcription'") == 2
    assert "[['ref','stratum','verdict','transcription','note']]" in page
    assert "data-seed='k3b-audit-20261020' data-name='k3b-audit-20261020'" in page
    assert f"{READER} (0.77)" in page  # the reader's reading beside the minted text
    # a second sheet never overwrites one that is there
    res = runner.invoke(app, args)
    assert res.exit_code != 0 and "another --name" in " ".join(res.output.split())
    res = runner.invoke(app, [*args, "--force", "--n", "1", "--context", "0", "--english-only"])
    assert res.exit_code == 0, res.output
    english = (tmp / "sheets" / "k3b-audit.html").read_text(encoding="utf-8")
    assert english.count(PNG) == 1 and JPEG not in english and "middle strip" not in english
    assert "column of its own" in english and "Deutsch." not in english


def test_cli_other_hand_and_both(sheet: dict) -> None:
    tmp = sheet["tmp"]
    res = runner.invoke(app, [*sheet["args"], "--hand", "other", "--name", "others", "--n", "4"])
    assert res.exit_code == 0, res.output
    rows = _lines(tmp / "sheets" / "others-lines.csv")
    assert [(r["ref"], r["group"]) for r in rows] == [(db.line_id(Q1, 0), "other_hands")]
    res = runner.invoke(app, [*sheet["args"], "--name", "both", "--n", "4", "--seed", "5"])
    assert res.exit_code == 0, res.output
    out = " ".join(res.output.split())
    assert "by hand leibniz_hand 2, other_hands 1" in out
    page = (tmp / "sheets" / "both.html").read_text(encoding="utf-8")
    assert "Half of the lines" in page and JPEG not in page and "middle strip" not in page
    # the records of a validation set leave both halves
    val = _csv(tmp / "val.csv", "record_id", "k-4402")
    res = runner.invoke(
        app, [*sheet["args"], "--name", "noval", "--n", "4", "--exclude-records", str(val)]
    )
    assert res.exit_code == 0, res.output
    assert {r["group"] for r in _lines(tmp / "sheets" / "noval-lines.csv")} == {"leibniz_hand"}
    # the K2 sheet's own name is taken once it is there
    (tmp / "sheets" / "k2-audit.html").write_text("the first sheet", encoding="utf-8")
    res = runner.invoke(app, [*sheet["args"], "--name", "k2-audit"])
    assert res.exit_code != 0
    assert (tmp / "sheets" / "k2-audit.html").read_text(encoding="utf-8") == "the first sheet"


def test_cli_explicit_refs_with_context(sheet: dict) -> None:
    tmp = sheet["tmp"]
    refs = _csv(
        tmp / "refs.csv", "ref,why", f"{db.line_id(P1, 1)},unreadable", f"{db.line_id(P2, 2)},x"
    )
    res = runner.invoke(
        app, [*sheet["args"], "--refs", str(refs), "--context", "2", "--name", "three-lines"]
    )
    assert res.exit_code == 0, res.output
    out = " ".join(res.output.split())
    assert "the 2 lines of" in out and "2 line(s) of context each" in out
    rows = _lines(tmp / "sheets" / "three-lines-lines.csv")
    assert [r["ref"] for r in rows] == [db.line_id(P1, 1), db.line_id(P2, 2)]  # the list's order
    assert [r["stratum"] for r in rows] == ["heavy_revision", "unminted"]
    assert [r["group"] for r in rows] == ["leibniz_hand", ""]
    page = (tmp / "sheets" / "three-lines.html").read_text(encoding="utf-8")
    # P1:001 has one line before it and two after; P2:002 two and two
    items = page.split("<div class='item'")[1:]
    assert [it.count("the line before") for it in items] == [1, 2]
    assert [it.count("the line after") for it in items] == [2, 2]
    assert page.count(PNG) == 2
    # the strips are greyscale JPEGs of the audit's crop
    import base64
    import io

    from PIL import Image

    strip = base64.b64decode(re.search(JPEG + r"([A-Za-z0-9+/=]+)", page).group(1))
    with Image.open(io.BytesIO(strip)) as im:
        assert im.mode == "L" and im.format == "JPEG" and im.width == audit.CROP_MAX_WIDTH


def test_cli_refuses_what_it_cannot_use(sheet: dict) -> None:
    tmp = sheet["tmp"]
    bad = _csv(tmp / "bad.csv", "line,stratum", "x,y")
    for extra in (
        ["--hand", "his"],
        ["--context", "-1"],
        ["--name", "a/b"],
        ["--exclude-refs", str(bad)],
        ["--exclude-pages", str(bad)],
        ["--refs", str(bad)],
        ["--readings-dir", str(tmp / "nothing")],
        ["--hand", "own", "--decisions", str(tmp / "no-decisions.jsonl")],
    ):
        res = runner.invoke(app, [*sheet["args"], *extra])
        assert res.exit_code != 0, extra
    assert not (tmp / "sheets").exists()


def test_build_audit_sheet_by_hand_needs_the_hands(sheet: dict) -> None:
    conn = db.connect(sheet["store"])
    try:
        with pytest.raises(ValueError, match="own hand"):
            M.build_audit_sheet(conn, {}, hand="own", out_dir=sheet["tmp"] / "x")
        with pytest.raises(ValueError, match="hand must be"):
            M.build_audit_sheet(conn, {}, hand="his", out_dir=sheet["tmp"] / "x")
    finally:
        conn.close()
    assert M.read_csv_column([], ("ref",)) == set()
