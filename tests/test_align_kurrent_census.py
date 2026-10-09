"""Tests for the German census of the edition pieces (seeded store, read-only; CLI)."""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import kurrent_census as K
from leibniz.align.pairs import GtPair, insert_gt_pairs
from leibniz.cli import app
from test_enrich_langid import FRENCH, GERMAN, LATIN

runner = CliRunner()
TODAY = date(2026, 7, 29)


def _seed(db_path: Path) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W", "LeibnizBriefwechsel", shelfmarks=["LBr 10"]))
    for i, lab in enumerate(["1r", "1v", "2r", "2v", "3r", "3v"], start=1):
        db.upsert_page(conn, db.Page(work_id="W", seq=i, label=lab, status="recognized"))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    for seq in range(1, 7):
        pid = f"W:{seq:04d}"
        for k in range(4):
            db.insert_line(conn, db.Line(page_id=pid, line_seq=k, run_id=seg, status="machine"))
            # the last line of every page stays unrecognised (text NULL)
            if k < 3:
                db.set_line_recognition(
                    conn, pid, k, text=f"linea {seq} {k}", conf=0.9, model="htr", run_id=rec
                )
        db.upsert_page_stats(
            conn,
            db.PageStats(
                page_id=pid,
                n_lines=3,
                run_id=seg,
                line_height_cv=0.1,
                n_overlaps=0,
                n_short_lines=0,
            ),
        )
    # Reihe I,3 (1923... expired): three records with a text, one without
    records = {
        "d1": ("LBr 10 Bl. 1-2", "Abf., eigh.", "Boineburg, J. C. von (GND)", "Leibniz (GND)"),
        "l1": ("LBr 10 Bl. 3", "Konz.; eigh.", "Leibniz (GND)", "Boineburg"),
        "f1": ("LBr 10 Bl. 1", "Abf.; eigh. Aufschr., Siegel", "Arnauld", "Leibniz"),
        "x1": ("LBr 10 Bl. 2", None, None, None),
    }
    for rid, (sig, textart, absender, adressat) in records.items():
        meta = {"titel": f"record {rid}"}
        if textart:
            meta["textart"] = textart
        if absender:
            meta["absender"] = absender
        if adressat:
            meta["adressat"] = adressat
        db.upsert_katalog_record(
            conn,
            db.KatalogRecord(
                record_id=rid,
                metadata=meta,
                shelfmark_refs=[sig],
                aa_refs=[{"series": 1, "volume": 3, "piece": rid}],
            ),
        )
        db.upsert_crosswalk(conn, db.CrosswalkMatch(rid, "W", "gwlb_link", 1.0))
    # the factory minted the Latin piece (3 lines) and one line of the German one
    pairs = [
        GtPair(
            "W:0005:000",
            "linea",
            "AA I,3 N.l1 (§70-expired AA reading text; katalog l1)",
            "fair_copy",
            0.9,
            "open",
        )
        for _ in range(1)
    ]
    pairs += [
        GtPair(
            f"W:0005:{k:03d}",
            "linea",
            "AA I,3 N.l1 (§70-expired AA reading text; katalog l1)",
            "fair_copy",
            0.9,
            "open",
        )
        for k in (1, 2)
    ]
    pairs.append(
        GtPair(
            "W:0001:000",
            "zeile",
            "AA I,3 N.d1 (§70-expired AA reading text; katalog d1)",
            "fair_copy",
            0.8,
            "open",
        )
    )
    insert_gt_pairs(conn, pairs)
    conn.commit()
    conn.close()


def _cache(path: Path) -> Path:
    rows = [
        {"record_id": "d1", "text": GERMAN + "\n" + GERMAN},
        {"record_id": "l1", "text": LATIN},
        {"record_id": "f1", "text": FRENCH},
        {"record_id": "zz", "text": LATIN},  # a cache record that is no piece
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("textart", "hand"),
    [
        ("Abf., eigh.", "own"),
        ("Konz.; eigh.", "own"),
        ("Reinschr., eigh.", "own"),
        ("MF, eigh.", "own"),
        ("eigh. Konz.", "own"),
        ("Abf.; eigh. Aufschr., Siegel", "partial"),
        ("Konz.; eigh. Anschr.", "partial"),
        ("Konz. mit eigh. Korr.", "partial"),
        ("Abf.", "other"),
        ("Abschr.", "other"),
        ("", "none"),
        (None, "none"),
    ],
)
def test_hand_from_textart(textart: str | None, hand: str) -> None:
    assert K.hand_from_textart(textart) == hand


def test_mint_tally_reads_the_minted_text() -> None:
    m = K.MintTally()
    m.add(0.9, "vnd daß der Herr", "vnd dass der herr")  # German stopwords
    m.add(0.7, "Monsieur je vous", "mons")  # French
    m.add(0.8, "quod enim und auch", None)  # both
    m.add(None, "Hannover 1690", "")  # neither
    assert (m.n, m.de, m.lafr, m.both, m.neither) == (4, 1, 1, 1, 1)
    assert m.conf_mean == pytest.approx(0.6)
    assert m.htr_chars == len("vnd dass der herr") + len("mons")
    assert m.text_chars_mean == pytest.approx(
        (
            len("vnd dass der herr")
            + len("monsieur je vous")
            + len("quod enim und auch")
            + len("hannover 1690")
        )
        / 4
    )


def test_leibniz_hand_rule() -> None:
    assert K.is_leibniz_hand("own", None)
    assert K.is_leibniz_hand("own", "Leibniz (GND)")
    assert not K.is_leibniz_hand("own", "Boineburg, J. C. von")
    assert not K.is_leibniz_hand("partial", "Leibniz")


def test_census_places_classifies_and_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed(db_path)
    cache_path = _cache(tmp_path / "cache.jsonl")
    from leibniz.align.ingest import load_edition_cache

    cache = load_edition_cache(cache_path)
    conn = K.open_readonly(db_path)
    try:
        res = K.census(conn, cache, today=TODAY)
    finally:
        conn.close()
    assert res.n_cache_records == 4
    assert res.cache_languages["la"] == 2 and res.cache_languages["de"] == 1
    assert res.n_pieces_enumerated == 4 and res.n_pieces_without_text == 1
    by_id = {pc.record_id: pc for pc in res.pieces}
    assert set(by_id) == {"d1", "l1", "f1"}
    d1 = by_id["d1"]
    assert d1.language == "de" and d1.german and d1.hand == "own" and not d1.leibniz_hand
    assert d1.page_ids == ["W:0001", "W:0002", "W:0003", "W:0004"]
    assert d1.n_lines == 12 and d1.n_minted == 1 and d1.stratum == "fair_copy"
    l1 = by_id["l1"]
    assert l1.language == "la" and l1.leibniz_hand and l1.n_lines == 6 and l1.n_minted == 3
    assert l1.yield_rate == 0.5
    assert l1.minted_conf_mean == 0.9 and l1.minted_neither == 3  # "linea" is no stopword
    assert l1.minted_htr_chars == 3 * len("linea 5 0")  # the machine text behind each line
    assert d1.minted_conf_mean == 0.8 and d1.minted_de == 0 and d1.minted_neither == 1
    f1 = by_id["f1"]
    assert f1.language == "fr" and f1.hand == "partial" and f1.n_minted == 0
    summ = K.summary(res)
    assert summ["german_pieces"] == 1 and summ["german_lines"] == 12 and summ["german_minted"] == 1
    assert summ["by_group"]["la_fr"]["lines"] == 12 and summ["by_group"]["la_fr"]["minted"] == 3
    assert summ["by_group"]["la_fr"]["minted_conf_mean"] == pytest.approx(0.9)
    assert summ["by_group"]["de"]["minted_neither_share"] == 1.0
    assert summ["by_stratum_group"]["fair_copy"]["de"]["lines"] == 12
    assert summ["by_volume"]["I,3"]["pieces"] == 3
    assert summ["by_hand"]["own"] == {"de": 1, "la": 1}
    assert summ["leibniz_hand_by_language"]["la"] == 1
    assert summ["pieces_with_katalog_stratum_signal"] == 0  # the abbreviations are not matched


def test_write_outputs_and_report(tmp_path: Path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed(db_path)
    from leibniz.align.ingest import load_edition_cache

    cache = load_edition_cache(_cache(tmp_path / "cache.jsonl"))
    conn = K.open_readonly(db_path)
    try:
        res = K.census(conn, cache, today=TODAY)
    finally:
        conn.close()
    paths = K.write_outputs(res, reports_dir=tmp_path / "r", data_dir=tmp_path / "d", cache=cache)
    text = paths["report"].read_text(encoding="utf-8")
    assert "# German census of the edition pieces" in text
    assert "## The hypothesis" in text and "## By volume" in text
    assert "None" not in text
    summ = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert summ["german_pieces"] == 1
    rows = list(csv.DictReader(paths["by_volume"].open(encoding="utf-8")))
    assert rows[0]["volume"] == "I,3" and rows[0]["de_lines"] == "12"
    pieces = [json.loads(row) for row in paths["pieces"].read_text(encoding="utf-8").splitlines()]
    assert len(pieces) == 1 and pieces[0]["record_id"] == "d1" and len(pieces[0]["page_ids"]) == 4
    index = list(csv.DictReader(paths["index"].open(encoding="utf-8")))
    assert index[0]["record_id"] == "d1" and "page_ids" not in index[0]
    assert index[0]["folio_range"] == "1-2"


def test_cli_kurrent_census(tmp_path: Path) -> None:
    db_path = tmp_path / "inv.sqlite"
    _seed(db_path)
    cache_path = _cache(tmp_path / "cache.jsonl")
    result = runner.invoke(
        app,
        [
            "align",
            "kurrent-census",
            "--db",
            str(db_path),
            "--edition-cache",
            str(cache_path),
            "--today",
            TODAY.isoformat(),
            "--reports-dir",
            str(tmp_path / "r"),
            "--data-dir",
            str(tmp_path / "d"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "German: 1 pieces" in result.output
    assert (tmp_path / "r" / "census.md").exists()
    assert (tmp_path / "d" / "german_pieces.jsonl").exists()
    # the store was not written to
    conn = db.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0] == 4
    conn.close()
