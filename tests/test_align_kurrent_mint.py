"""Tests for K2's mint: the dry run, the rule, the write, the sheets (seeded store, offline)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import kurrent_mint as M
from leibniz.align.factory import FactoryConfig
from leibniz.align.kurrent_pilot import Reading, append_readings, open_readonly
from leibniz.align.pairs import GtPair, insert_gt_pairs, reader_from_source
from leibniz.cli import app

pytest.importorskip("PIL")
runner = CliRunner()
TODAY = date(2026, 7, 29)
READER = "trocr-kurrent-xvi-xvii"
# Bl. 1 of LBr 10 (pages 1 and 2): a German piece, four lines
GERMAN = [
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten",
    "vnd bedancke mich daß Sie mir die Nachricht so bald",
    "haben zukommen lassen; es ist aber nicht zu zweiffeln",
    "daß der Herr von Boineburg alß ein verständiger Mann",
]
# Bl. 2 (pages 3 and 4): a second German piece the v1 text already reads well
SECOND = [
    "Durchleuchtigster Fürst, gnädigster Herr, Ew. Durchl.",
    "gnädigstes Schreiben habe ich mit gebührender Ehrerbietung",
    "empfangen vnd daraus ersehen was dieselbe begehren",
    "worauf ich in Unterthänigkeit zu antworten nicht ermangeln",
]


def _page_image(path: Path, n_lines: int) -> None:
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (600, 60 * n_lines + 40), "white")
    draw = ImageDraw.Draw(im)
    for k in range(n_lines):
        top = 20 + 60 * k
        draw.rectangle((40, top + 10, 560, top + 40), fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="JPEG")


def _seed(db_path: Path, images_root: Path) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W", "LeibnizBriefwechsel", shelfmarks=["LBr 10"]))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    texts = {1: GERMAN[:2], 2: GERMAN[2:], 3: SECOND[:2], 4: SECOND[2:]}
    for seq, lab in enumerate(["1r", "1v", "2r", "2v"], start=1):
        pid = f"W:{seq:04d}"
        local = f"W/{seq:04d}.jpg"
        db.upsert_page(
            conn, db.Page(work_id="W", seq=seq, label=lab, status="recognized", local_path=local)
        )
        _page_image(images_root / local, len(texts[seq]))
        for k, text in enumerate(texts[seq]):
            top = 20 + 60 * k
            poly = [[40, top + 10], [560, top + 10], [560, top + 40], [40, top + 40]]
            db.insert_line(
                conn,
                db.Line(
                    page_id=pid,
                    line_seq=k,
                    polygon=poly,
                    baseline=[[40, top + 38], [560, top + 38]],
                    run_id=seg,
                    status="machine",
                ),
            )
            # v1 reads the second piece right and the first as noise
            v1 = text if seq >= 3 else "xxxx yyyy zzzz"
            db.set_line_recognition(conn, pid, k, text=v1, conf=0.8, model="htr", run_id=rec)
        db.upsert_page_stats(
            conn,
            db.PageStats(
                page_id=pid,
                n_lines=2,
                run_id=seg,
                line_height_cv=0.1,
                n_overlaps=0,
                n_short_lines=0,
            ),
        )
    for rid, sig, textart, absender in (
        ("g1", "LBr 10 Bl. 1", "Konz., eigh.", "Leibniz (GND)"),
        ("g2", "LBr 10 Bl. 2", "Abf.", "Boineburg (GND)"),
    ):
        db.upsert_katalog_record(
            conn,
            db.KatalogRecord(
                record_id=rid,
                metadata={"textart": textart, "titel": f"record {rid}", "absender": absender},
                shelfmark_refs=[sig],
                aa_refs=[{"series": 1, "volume": 3, "piece": rid}],
            ),
        )
        db.upsert_crosswalk(conn, db.CrosswalkMatch(rid, "W", "gwlb_link", 1.0))
    # the stored mint (the C2c re-mint from the v1 text): g2 fully, g1 nothing
    src2 = "AA I,3 N.g2 (§70-expired AA reading text; channel ia; katalog g2)"
    insert_gt_pairs(
        conn,
        [
            GtPair(
                f"W:{3 + k // 2:04d}:{k % 2:03d}", SECOND[k], src2, "fair_copy", 0.95, "open", "g2"
            )
            for k in range(4)
        ],
    )
    conn.commit()
    conn.close()


def _rows() -> list[dict]:
    return [
        {
            "record_id": "g1",
            "work_id": "W",
            "aa_label": "AA I,3 N.g1",
            "volume_label": "I,3",
            "stratum": "fair_copy",
            "hand": "own",
            "leibniz_hand": True,
            "language": "de",
            "page_ids": ["W:0001", "W:0002"],
            "n_lines": 4,
            "textart": "Konz., eigh.",
        },
        {
            "record_id": "g2",
            "work_id": "W",
            "aa_label": "AA I,3 N.g2",
            "volume_label": "I,3",
            "stratum": "fair_copy",
            "hand": "other",
            "leibniz_hand": False,
            "language": "de",
            "page_ids": ["W:0003", "W:0004"],
            "n_lines": 4,
            "textart": "Abf.",
        },
        # a record with no catalogue record in the store: skipped, counted
        {
            "record_id": "g9",
            "work_id": None,
            "aa_label": "AA I,3 N.g9",
            "volume_label": "I,3",
            "stratum": "unknown",
            "hand": "none",
            "leibniz_hand": False,
            "language": "mixed",
            "page_ids": [],
            "n_lines": 0,
        },
    ]


def _cache(path: Path) -> Path:
    rows = [
        {
            "record_id": "g1",
            "text": " ".join(GERMAN),
            "refs": [{"series": 1, "volume": 3, "piece": "g1", "channel": "ia"}],
        },
        {
            "record_id": "g2",
            "text": " ".join(SECOND),
            "refs": [{"series": 1, "volume": 3, "piece": "g2", "channel": "ia"}],
        },
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


def _readings(readings_dir: Path, *, second_noisy: bool = True) -> dict[str, Reading]:
    """The Bern reader: the first piece read right, the second as noise (or right)."""
    rows = []
    for k, text in enumerate(GERMAN):
        rows.append(Reading(f"W:{1 + k // 2:04d}:{k % 2:03d}", text, 0.9, READER, "cuda", 50.0))
    for k, text in enumerate(SECOND):
        bern = "qqqq wwww" if second_noisy else text
        rows.append(Reading(f"W:{3 + k // 2:04d}:{k % 2:03d}", bern, 0.4, READER, "cuda", 50.0))
    append_readings(readings_dir, READER, rows)
    return {r.line_id: r for r in rows}


def test_decide_is_the_rule() -> None:
    assert M.decide(3, 2, None, READER) == "bern"
    assert M.decide(2, 2, None, READER) == "stored"  # a tie keeps the stored mint
    assert M.decide(0, 2, None, READER) == "stored"
    assert M.decide(0, 0, None, READER) == "none"
    assert M.decide(5, 0, None, READER) == "bern"
    # the reader's own earlier rows are replaced by its new ones, whatever the counts
    assert M.decide(1, 7, READER, READER) == "bern"
    assert M.decide(0, 7, READER, READER) == "stored"
    assert M.decide(1, 7, "other-reader", READER) == "stored"


def test_dry_run_decides_per_piece_and_writes_files(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    from leibniz.align.ingest import load_edition_cache, load_edition_refs

    cache_path = _cache(tmp_path / "cache.jsonl")
    cache, refs = load_edition_cache(cache_path), load_edition_refs(cache_path)
    readings = _readings(tmp_path / "readings")
    conn = open_readonly(db_path)
    try:
        run = M.dry_run(conn, _rows(), cache, readings, reader=READER, refs=refs, today=TODAY)
        by = {d.record_id: d for d in run.decisions}
        assert set(by) == {"g1", "g2", "g9"}
        g1, g2, g9 = by["g1"], by["g2"], by["g9"]
        assert g1.status == "minted" and g1.stratum == "fair_copy" and g1.threshold == 0.55
        assert g1.n_pages == 2 and g1.n_lines == 4 and g1.n_read == 4
        assert g1.bern_minted == 4 and g1.stored_minted == 0 and g1.winner == "bern"
        assert g1.hand == "own" and g1.leibniz_hand and g1.language == "de"
        assert g1.bern_mean_conf is not None and g1.bern_mean_conf > 0.9
        assert g2.status == "minted" and g2.stored_minted == 4 and g2.stored_reader is None
        assert g2.bern_minted < g2.stored_minted and g2.winner == "stored"
        assert g2.stored_mean_conf == pytest.approx(0.95) and not g2.leibniz_hand
        assert g9.status == "skipped:no_piece" and g9.winner == "none" and g9.n_lines == 0
        assert set(run.pairs) == {"g1"} and len(run.pairs["g1"]) == 4
        pair = run.pairs["g1"][0]
        assert pair.record_id == "g1" and reader_from_source(pair.source) == READER
        assert pair.source.endswith("; katalog g1)") and "channel ia" in pair.source
        assert (run.german_before, run.german_after) == (4, 8)
        assert run.store_rows_before == 4 and run.store_rows_after == 8
        # files
        dec_path = M.write_decisions(tmp_path / "decisions.jsonl", run)
        back = {d.record_id: d for d in M.load_decisions(dec_path)}
        assert back["g1"].winner == "bern" and back["g1"].bern_minted == 4
        s = M.summary(run, plan={"n_pages": 4, "n_lines": 8}, stats={"lines_done": 8})
        assert s["won"] == {"bern": 1, "stored": 1, "none": 1}
        assert s["mint"]["german_after"] == 8 and s["mint"]["bern_rows_after"] == 4
        assert s["by_stratum"]["fair_copy"]["pieces"] == 2
        assert s["by_hand"]["own"]["won_bern"] == 1 and s["leibniz_hand"]["after_minted"] == 4
        assert s["by_language"]["de"]["lines"] == 8 and "mixed" not in s["by_language"]
        assert s["piece_skips"] == {"no_piece": 1}
        paths = M.write_outputs(run, reports_dir=tmp_path / "reports", plan=None, stats=None)
        text = paths["report"].read_text(encoding="utf-8")
        assert "# K2:" in text and "**4 → 8**" in text and "None" not in text
        assert "No reading-job statistics" in text
        assert paths["by_volume"].read_text(encoding="utf-8").count("\n") == 2  # header + I,3
        assert paths["pieces"].read_text(encoding="utf-8").count("\n") == 4
        summ = json.loads(paths["summary"].read_text(encoding="utf-8"))
        assert summ["reader"] == READER and summ["won"]["bern"] == 1
        # the side-by-side: the four new lines, with crops and both readings
        page = M.side_by_side(conn, run, readings, images_root=images, n=3, seed=1)
        assert page.count("data:image/png;base64,") == 3
        assert "Bern reading" in page and "v1 reading" in page and "xxxx yyyy zzzz" in page
        assert len(M.new_lines(run, M.stored_refs(conn))) == 4
    finally:
        conn.close()


def test_write_mint_replaces_only_the_won_pieces_and_is_idempotent(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    from leibniz.align.ingest import load_edition_cache, load_edition_refs

    cache_path = _cache(tmp_path / "cache.jsonl")
    cache, refs = load_edition_cache(cache_path), load_edition_refs(cache_path)
    readings = _readings(tmp_path / "readings")
    conn = db.init_db(db_path)
    cfg = FactoryConfig(today=TODAY)
    run = M.dry_run(
        conn, _rows(), cache, readings, reader=READER, refs=refs, today=TODAY, config=cfg
    )
    ws = M.write_mint(conn, run, config=cfg)
    conn.commit()
    assert ws.pieces == 1 and ws.written_pieces == 1 and ws.rows_written == 4
    assert ws.rows_removed == 0 and ws.rows_won == 0 and ws.rows_lost == 0 and not ws.errors
    rows = conn.execute("SELECT record_id, source FROM gt_lines ORDER BY id").fetchall()
    assert len(rows) == 8
    assert sum(1 for r in rows if reader_from_source(r[1]) == READER) == 4
    assert all(r[0] == "g2" for r in rows if reader_from_source(r[1]) is None)
    run_row = conn.execute(
        "SELECT stage, model, params, n_ok FROM runs WHERE run_id = ?", (ws.run_id,)
    ).fetchone()
    assert run_row["stage"] == "gt_factory" and run_row["model"] == f"retro-aligner+{READER}"
    params = json.loads(run_row["params"])
    assert params["reader"] == READER and params["rule"] == M.RULE and run_row["n_ok"] == 1
    assert params["stratum_thresholds"]["fair_copy"] == 0.55
    # again: the reader's own rows are replaced, the count holds; on resume nothing is written
    run2 = M.dry_run(
        conn, _rows(), cache, readings, reader=READER, refs=refs, today=TODAY, config=cfg
    )
    g1 = next(d for d in run2.decisions if d.record_id == "g1")
    assert g1.stored_reader == READER and g1.stored_minted == 4 and g1.winner == "bern"
    ws2 = M.write_mint(conn, run2, config=cfg)
    assert ws2.rows_removed == 4 and ws2.rows_written == 4
    assert conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0] == 8
    ws3 = M.write_mint(conn, run2, config=cfg, resume=True)
    assert ws3.skipped_resume == 1 and ws3.written_pieces == 0
    # the v1 factory leaves the reader's piece alone; a v1 re-mint of g2 keeps g2's rows
    from leibniz.align import factory as F
    from leibniz.align.volumes import enumerate_pieces

    pieces, _ = enumerate_pieces(conn, today=TODAY)
    by_rec = {p.record_id: p for p in F.select_text_pieces(pieces, refs)}
    res = F.mint_piece(conn, by_rec["g1"], cache["g1"], cfg)
    assert res.status == "skipped:reader_minted"
    res2 = F.mint_piece(conn, by_rec["g2"], cache["g2"], cfg)
    assert res2.minted and res2.n_minted == 4
    assert conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0] == 8
    # the audit sheet from the reader's rows, bilingual
    html_path, csv_path, by_stratum = M.build_audit_sheet(
        conn, readings, reader=READER, images_root=images, out_dir=tmp_path / "audit", n=3, seed=2
    )
    page = html_path.read_text(encoding="utf-8")
    assert by_stratum == {"fair_copy": 3} and page.count("data:image/png;base64,") == 3
    assert "richtig" in page and "unlesbar" in page and "Deutsch." in page
    assert f"{READER} (0.90)" in page and "value='correct'" in page
    assert csv_path.read_text(encoding="utf-8").count("\n") == 4
    english = M.build_audit_sheet(
        conn,
        readings,
        reader=READER,
        images_root=images,
        out_dir=tmp_path / "audit-en",
        n=2,
        seed=2,
        bilingual=False,
    )
    assert "richtig" not in english[0].read_text(encoding="utf-8")
    conn.close()


def test_cli_kurrent_mint_dry_run_write_and_audit(tmp_path: Path) -> None:
    db_path, images = tmp_path / "inv.sqlite", tmp_path / "images"
    _seed(db_path, images)
    cache = _cache(tmp_path / "cache.jsonl")
    readings_dir = tmp_path / "readings"
    _readings(readings_dir)
    (readings_dir / "plan.json").write_text(
        json.dumps(
            {
                "n_pages": 4,
                "n_pages_census": 4,
                "n_pages_resolver": 4,
                "n_lines": 8,
                "pages": ["W:0001"],
            }
        ),
        encoding="utf-8",
    )
    german = tmp_path / "german.jsonl"
    german.write_text("\n".join(json.dumps(r) for r in _rows()), encoding="utf-8")
    common = [
        "align",
        "kurrent-mint",
        "--db",
        str(db_path),
        "--german",
        str(german),
        "--edition-cache",
        str(cache),
        "--readings-dir",
        str(readings_dir),
        "--images",
        str(images),
        "--decisions",
        str(tmp_path / "dec.jsonl"),
        "--side-by-side",
        str(tmp_path / "side.html"),
        "--reports-dir",
        str(tmp_path / "reports"),
        "--today",
        TODAY.isoformat(),
        "--n-side",
        "2",
    ]
    result = runner.invoke(app, common)
    assert result.exit_code == 0, result.output
    assert "dry run" in result.output and "Bern 1" in result.output and "4 → 8" in result.output
    assert (tmp_path / "side.html").exists() and (tmp_path / "dec.jsonl").exists()
    text = (tmp_path / "reports" / "k2-mint.md").read_text(encoding="utf-8")
    assert "The reading job's pages: 4" in text
    assert db.init_db(db_path).execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0] == 4
    result = runner.invoke(app, [*common, "--write"])
    assert result.exit_code == 0, result.output
    assert "written" in result.output and "gt_lines now 8 rows" in result.output
    assert "difference +0" in result.output
    assert (readings_dir / "write-stats.json").exists()
    result = runner.invoke(
        app, [*common, "--audit", "--audit-n", "2", "--audit-dir", str(tmp_path / "au")]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "au" / "k2-audit.html").exists() and "2 lines" in result.output
    result = runner.invoke(app, [*common, "--readings-dir", str(tmp_path / "nothing")])
    assert result.exit_code != 0
