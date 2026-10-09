"""Tests for the reach census (seeded store, read-only; CLI round trip)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import audit_reach as R
from leibniz.align.pairs import GtPair, insert_gt_pairs
from leibniz.cli import app

runner = CliRunner()


def _seed(path: Path) -> None:
    conn = db.init_db(path)
    db.upsert_work(conn, db.Work("W1", "LeibnizHandschriften", shelfmarks=["LH XXXV, 3 A 8"]))
    db.upsert_work(conn, db.Work("W2", "LeibnizBriefwechsel", shelfmarks=["LBr. 464"]))
    db.upsert_work(conn, db.Work("M1", "LeibnizMarginalien", shelfmarks=["Leibn. Marg. 11"]))
    for w in ("W1", "W2", "M1"):
        db.upsert_page(conn, db.Page(work_id=w, seq=1, status="recognized", width=100, height=100))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    rec2 = db.start_run(conn, "recognize", model="htr@v2")

    def line(pid: str, seq: int, text: str, run: int = rec) -> None:
        db.insert_line(
            conn,
            db.Line(
                page_id=pid,
                line_seq=seq,
                polygon=[[0, 0], [9, 0], [9, 9], [0, 9]],
                run_id=seg,
                status="machine",
            ),
        )
        db.set_line_recognition(conn, pid, seq, text=text, conf=0.9, model="htr", run_id=run)

    line("W1:0001", 0, "minis pro-")  # hyphen: HTR mark, minted letter
    line("W1:0001", 1, "x + 30e = 0")  # math
    line("W1:0001", 2, "plain")
    line("W2:0001", 0, "etwas-")  # mark, but the minted text ends in a digit
    line("W2:0001", 1, "zwei")
    line("W2:0001", 2, "drei")
    line("M1:0001", 0, "marg")
    # a later run re-read W1 line 2 without a hyphen; the census takes the latest text
    conn.execute(
        "INSERT INTO lines (line_id, page_id, line_seq, run_id, text, status) "
        "VALUES (?, 'W1:0001', 2, ?, 'plain-', 'machine')",
        (db.line_id("W1:0001", 2), rec2),
    )
    db.upsert_page_stats(
        conn, db.PageStats(page_id="W1:0001", n_lines=10, run_id=seg, n_overlaps=0, n_short_lines=0)
    )
    db.upsert_page_stats(
        conn, db.PageStats(page_id="W2:0001", n_lines=10, run_id=seg, n_overlaps=3, n_short_lines=0)
    )
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            "k-1",
            metadata={"textart": "Konzept, eigh.", "absender": "Leibniz, Gottfried Wilhelm"},
            shelfmark_refs=[],
            aa_refs=[],
        ),
    )
    # a letter Leibniz received, in the correspondent's own hand
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            "k-4",
            metadata={"textart": "Abfertigung, eigh.", "absender": "Bernoulli, Johann"},
            shelfmark_refs=[],
            aa_refs=[],
        ),
    )
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord("k-2", metadata={"textart": "Abfertigung"}, shelfmark_refs=[], aa_refs=[]),
    )
    db.upsert_katalog_record(
        conn, db.KatalogRecord("k-3", metadata={}, shelfmark_refs=[], aa_refs=[])
    )
    src1 = "AA III,3 N.12 (§70-expired AA reading text; katalog k-1)"
    src2 = "AA I,7 N. 3 (§70-expired AA reading text; katalog k-2)"
    src3 = "AA VI,4 N.109 (§70-expired AA reading text; katalog k-3)"
    src4 = "AA I,8 N.5 (§70-expired AA reading text; katalog k-4)"
    insert_gt_pairs(
        conn,
        [
            GtPair("W1:0001:000", "minis pro", src1, "heavy_revision", 0.9, "open"),
            GtPair("W1:0001:001", "x + 30e = 0", src1, "heavy_revision", 0.9, "open"),
            GtPair("W1:0001:002", "plain words", src1, "scrap", 0.9, "open"),
            GtPair("W2:0001:000", "anno 1691", src2, "fair_copy", 0.9, "open"),
            GtPair("W2:0001:001", "droit[e] zwei", src2, "fair_copy", 0.9, "open"),
            GtPair("W2:0001:002", "drei", src4, "fair_copy", 0.9, "open"),
            GtPair("M1:0001:000", "marg", src3, "light_revision", 0.9, "open"),
            GtPair("M1:0001:000", "nc text", "transkriptionspool", "light_revision", 0.9, "nc"),
            # an older reference form (the B2 prototype's): skipped and counted, not a crash
            GtPair("W1:0001#xywh=0,0,9,9", "old form", src3, "fair_copy", 0.9, "open"),
        ],
    )
    conn.commit()
    conn.close()


def test_parse_source_and_lh35() -> None:
    assert R.parse_source("AA VI,4 N.109 (§70-expired AA reading text; katalog k-109)") == (
        "VI,4",
        "k-109",
    )
    assert R.parse_source("AA VI,4 N. 109 (§70-expired AA reading text; katalog R1)") == (
        "VI,4",
        "R1",
    )
    assert R.parse_source("transkriptionspool") == (None, None)
    assert R.series_of("III,3") == "III" and R.series_of(None) is None
    assert (
        R.is_lh35(["LH XXXV, 3 A 8"])
        and R.is_lh35(["LH 35,3,5"])
        and not R.is_lh35(["LH IV, 6, 18", "LBr. 35"])
    )


def test_census_flags(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed(store)
    conn = R.open_readonly(store)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM gt_lines")
    c = R.census(conn)
    conn.close()
    flags = {ln.ref: set(ln.flags) for ln in c.lines}
    assert c.n == 7 and c.n_pages == 3 and c.n_records == 4 and c.n_records_with_textart == 3
    assert c.n_skipped == 1
    assert flags["W1:0001:000"] == {"hyphen", "eigh", "leibniz", "lh35"}
    assert flags["W1:0001:001"] == {"math", "eigh", "leibniz", "lh35"}
    # the v2 reading ends in a hyphen
    assert flags["W1:0001:002"] == {"hyphen", "eigh", "leibniz", "lh35"}
    assert flags["W2:0001:000"] == {"addition"}  # the page's overlap fraction, not the line
    assert flags["W2:0001:001"] == {"addition", "bracket"}
    assert flags["W2:0001:002"] == {"addition", "eigh"}  # Bernoulli's hand, not Leibniz's
    assert flags["M1:0001:000"] == {"marginalien"}
    eigh = {ln.ref: ln.eigh for ln in c.lines}
    assert (
        eigh["W1:0001:000"] is True and eigh["W2:0001:000"] is False and eigh["M1:0001:000"] is None
    )
    s = R.summary(c, strata=("fair_copy", "light_revision", "heavy_revision", "scrap"))
    # hand shares are of the 6 lines whose record carries a Textart (k-1, k-2, k-4), not of all 7
    assert s["all"]["hyphen"] == 2 and s["all"]["with_textart"] == 6
    assert s["all"]["eigh"] == 4 and s["all"]["leibniz"] == 3 and s["all"]["leibniz_share"] == 0.5
    by_vol = {r["key"]: r for r in s["by_volume"]}
    assert by_vol["III,3"]["math"] == 1 and by_vol["I,7"]["addition"] == 2
    assert by_vol["I,8"]["eigh"] == 1 and by_vol["I,8"]["leibniz"] == 0
    md = R.render(c, strata=("fair_copy",), flags_path=Path("data/gt/flags.jsonl"))
    assert "| III,3 | 3 |" in md and "marginalien" in md and "1 open-bucket rows carry" in md


def test_audit_reach_cli(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed(store)
    out, flags = tmp_path / "reach", tmp_path / "flags.jsonl"
    res = runner.invoke(
        app,
        ["align", "audit-reach", "--db", str(store), "--out", str(out), "--flags-out", str(flags)],
    )
    assert res.exit_code == 0, res.stdout
    flat = " ".join(res.stdout.split())  # the console wraps long lines
    assert "7 lines on 3 pages" in flat and "1 rows with a non-canonical" in flat
    rows = [json.loads(line) for line in flags.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 7 and rows[0]["ref"] == "W1:0001:000" and "hyphen" in rows[0]["flags"]
    summ = json.loads((out / "reach-summary.json").read_text(encoding="utf-8"))
    assert summ["n_lines"] == 7 and (out / "reach.md").exists()
    res2 = runner.invoke(app, ["align", "audit-reach", "--db", str(tmp_path / "missing.sqlite")])
    assert res2.exit_code != 0
