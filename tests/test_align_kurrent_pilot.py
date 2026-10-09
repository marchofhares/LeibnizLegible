"""Tests for the Kurrent pilot (seeded store, synthetic page images, scripted readers)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import kurrent_pilot as P
from leibniz.cli import app

pytest.importorskip("PIL")
runner = CliRunner()
TODAY = date(2026, 7, 29)

GERMAN_LINES = [
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten",
    "vnd bedancke mich daß Sie mir die Nachricht so bald",
    "haben zukommen lassen; es ist aber nicht zu zweiffeln",
    "daß der Herr von Boineburg alß ein verständiger Mann",
]
LATIN_LINES = [
    "Vir amplissime, literas tuas accepi quibus de rebus",
    "mathematicis ad me scripsisti; ego vero puto non esse",
    "dubitandum quod haec omnia ex principiis nostris deduci",
    "possint, ut etiam tibi ostendam cum primum licebit",
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
    # pages 1-2: the German piece (Bl. 1); pages 3-4: the Latin piece (Bl. 2)
    texts = {1: GERMAN_LINES[:2], 2: GERMAN_LINES[2:], 3: LATIN_LINES[:2], 4: LATIN_LINES[2:]}
    for seq, lab in enumerate(["1r", "1v", "2r", "2v"], start=1):
        pid = f"W:{seq:04d}"
        local = f"W/{seq:04d}.jpg"
        db.upsert_page(
            conn,
            db.Page(work_id="W", seq=seq, label=lab, status="recognized", local_path=local),
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
            # the stored v1 text: the Latin read right, the German read as noise
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
    for rid, sig, textart in (
        ("g1", "LBr 10 Bl. 1", "Abf., eigh."),
        ("l1", "LBr 10 Bl. 2", "Konz."),
    ):
        db.upsert_katalog_record(
            conn,
            db.KatalogRecord(
                record_id=rid,
                metadata={"textart": textart, "titel": f"record {rid}"},
                shelfmark_refs=[sig],
                aa_refs=[{"series": 1, "volume": 3, "piece": rid}],
            ),
        )
        db.upsert_crosswalk(conn, db.CrosswalkMatch(rid, "W", "gwlb_link", 1.0))
    conn.commit()
    conn.close()


def _german_rows() -> list[dict]:
    return [
        {
            "record_id": "g1",
            "work_id": "W",
            "aa_label": "AA I,3 N.g1",
            "volume_label": "I,3",
            "stratum": "fair_copy",
            "hand": "own",
            "leibniz_hand": False,
            "language": "de",
            "score": 1.0,
            "page_ids": ["W:0001", "W:0002"],
            "n_lines": 4,
            "textart": "Abf., eigh.",
        },
        {  # not eligible: no lines
            "record_id": "g2",
            "work_id": "W",
            "aa_label": "AA I,3 N.g2",
            "volume_label": "I,3",
            "stratum": "unknown",
            "hand": "other",
            "leibniz_hand": False,
            "language": "de",
            "score": 0.9,
            "page_ids": [],
            "n_lines": 0,
        },
    ]


def _cache(path: Path) -> Path:
    rows = [
        {"record_id": "g1", "text": " ".join(GERMAN_LINES)},
        {"record_id": "l1", "text": " ".join(LATIN_LINES)},
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


class _Scripted:
    """A reader that returns the gold text of each line, in reading order per page."""

    name = "scripted"
    version = "scripted@1"
    device = "cpu"

    def __init__(self, texts: list[str]) -> None:
        self.texts = list(texts)
        self.calls = 0

    def transcribe_conf(self, images):
        self.calls += 1
        out = []
        for _ in images:
            out.append((self.texts.pop(0), 0.95))
        return out


def test_select_german_prefers_eligible_pieces_and_caps_pages() -> None:
    picked = P.select_german(_german_rows(), n=5, max_pages=1, min_lines=1)
    assert [p.record_id for p in picked] == ["g1"]
    assert picked[0].page_ids == ["W:0001"] and picked[0].n_pages_total == 2
    assert picked[0].threshold == 0.55 and picked[0].role == "german"


def test_select_german_spreads_over_cells() -> None:
    rows = []
    for i in range(12):
        rows.append(
            {
                "record_id": f"r{i}",
                "work_id": "W",
                "volume_label": f"I,{3 + i % 4}",
                "stratum": ["fair_copy", "heavy_revision", "light_revision"][i % 3],
                "hand": ["own", "other"][i % 2],
                "leibniz_hand": i % 4 == 0,
                "language": "de",
                "score": 1.0,
                "page_ids": ["W:0001"],
                "n_lines": 30,
            }
        )
    picked = P.select_german(rows, n=6, seed=1)
    assert len(picked) == 6 and len({p.record_id for p in picked}) == 6
    assert len({(p.stratum, p.hand) for p in picked}) >= 4  # several cells
    assert P.select_german(rows, n=6, seed=1) == picked  # reproducible


def test_pilot_end_to_end(tmp_path: Path) -> None:
    db_path = tmp_path / "inv.sqlite"
    images = tmp_path / "images"
    _seed(db_path, images)
    from leibniz.align.ingest import load_edition_cache

    cache = load_edition_cache(_cache(tmp_path / "cache.jsonl"))
    german = P.select_german(_german_rows(), n=1, min_lines=1)
    conn = P.open_readonly(db_path)
    try:
        controls = P.select_controls(conn, cache, n=1, min_lines=1, today=TODAY)
        assert [c.record_id for c in controls] == ["l1"] and controls[0].language == "la"
        pieces = [*german, *controls]
        readings_dir = tmp_path / "readings"
        gold = _Scripted(GERMAN_LINES + LATIN_LINES)
        got = P.read_pieces(
            conn,
            pieces,
            "good",
            lambda: gold,
            images_root=images,
            readings_dir=readings_dir,
            batch_size=3,
        )
        assert len(got) == 8 and got["W:0001:000"].text == GERMAN_LINES[0]
        assert got["W:0001:000"].conf == 0.95 and got["W:0001:000"].model == "scripted@1"
        assert (readings_dir / "good.jsonl").exists()
        # resumable: nothing left to read, the engine is never built
        again = P.read_pieces(
            conn, pieces, "good", lambda: 1 / 0, images_root=images, readings_dir=readings_dir
        )
        assert len(again) == 8
        v1 = P.v1_readings(conn, pieces)
        assert v1["W:0003:000"].text == LATIN_LINES[0] and v1["W:0001:000"].text == "xxxx yyyy zzzz"
        readers = {"good": got, P.V1: v1}
        yields = P.dry_run(conn, pieces, readers, cache)
        by = {(y.record_id, y.reader): y for y in yields}
        assert by[("g1", "good")].yield_rate == 1.0
        assert by[("g1", P.V1)].n_aligned == 0  # noise against German text
        assert by[("l1", P.V1)].yield_rate == 1.0
        summaries = P.summarize_readers(yields, readers)
        s = {x.reader: x for x in summaries}
        assert s["good"].german_yield == 1.0 and s[P.V1].german_yield == 0.0
        assert s[P.V1].control_yield == 1.0
        assert s["good"].by_stratum["fair_copy"]["lines"] == 4
        v = P.verdict(summaries)
        assert v.best_reader == "good" and v.best_german_yield == 1.0
        assert v.control_winner in ("good", P.V1)  # the perfect reader ties the baseline
        page = P.side_by_side(conn, pieces, readers, images_root=images, n=3, seed=1)
        assert page.count("data:image/png;base64,") == 3
        assert GERMAN_LINES[0] in page or GERMAN_LINES[1] in page
        res = P.PilotResult(
            pieces=pieces,
            yields=yields,
            summaries=summaries,
            verdict=v,
            readers=["good", P.V1],
            sample=None,
            max_pages=3,
            operator_verdict="yes, the first reader gives German words",
        )
    finally:
        conn.close()
    paths = P.write_outputs(res, reports_dir=tmp_path / "reports")
    text = paths["report"].read_text(encoding="utf-8")
    assert "# The Kurrent pilot" in text and "yes, the first reader gives German words" in text
    assert "None" not in text
    assert paths["yields"].read_text(encoding="utf-8").count("\n") == 1 + len(yields)
    summ = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert summ["verdict"]["best_reader"] == "good"


def test_qualifying_readers_from_bootstrap_json(tmp_path: Path) -> None:
    path = tmp_path / "bootstrap-candidates.json"
    path.write_text(
        json.dumps(
            {
                "results": [
                    {"key": "philiumm", "status": "ok", "scores": {"philiumm": {"cer": 0.30}}},
                    {"key": "good", "status": "ok", "scores": {"philiumm": {"cer": 0.15}}},
                    {"key": "meh", "status": "ok", "scores": {"philiumm": {"cer": 0.25}}},
                    {"key": "broken", "status": "skipped:x", "scores": {}},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert P.qualifying_readers(path) == ["philiumm", "good"]
    assert P.qualifying_readers(tmp_path / "missing.json") == ["philiumm"]


def test_cli_kurrent_pilot_with_echo(tmp_path: Path) -> None:
    db_path = tmp_path / "inv.sqlite"
    images = tmp_path / "images"
    _seed(db_path, images)
    cache = _cache(tmp_path / "cache.jsonl")
    german = tmp_path / "german.jsonl"
    german.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in _german_rows()), encoding="utf-8"
    )
    result = runner.invoke(
        app,
        [
            "align",
            "kurrent-pilot",
            "--db",
            str(db_path),
            "--german",
            str(german),
            "--edition-cache",
            str(cache),
            "--images",
            str(images),
            "--readers",
            "echo",
            "--n-german",
            "1",
            "--n-control",
            "1",
            "--min-lines",
            "1",
            "--device",
            "cpu",
            "--today",
            TODAY.isoformat(),
            "--readings-dir",
            str(tmp_path / "readings"),
            "--side-by-side",
            str(tmp_path / "side.html"),
            "--reports-dir",
            str(tmp_path / "reports"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "verdict" in result.output
    assert (tmp_path / "reports" / "pilot.md").exists()
    assert (tmp_path / "reports" / "pilot-yield.csv").exists()
    assert (tmp_path / "side.html").exists()
    assert (tmp_path / "readings" / "echo.jsonl").exists()
