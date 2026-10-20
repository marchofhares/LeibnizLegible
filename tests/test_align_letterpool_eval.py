"""Tests for the letter-pool metric (K2b Task 3): the infix alignment against the full
table, the policies, the pooling and bootstrap, the scoring of a fixture store with
scripted readers, the selected line-level number, the report and the CLI."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import kurrent_pilot as P
from leibniz.align import letterpool_eval as E
from leibniz.align.letterpool_set import text_sha256
from leibniz.cli import app

pytest.importorskip("numpy")
runner = CliRunner()


# --------------------------------------------------------------------------- #
# The infix alignment
# --------------------------------------------------------------------------- #


def test_infix_distance_matches_the_full_table_on_random_strings() -> None:
    rng = random.Random(20261019)
    alphabet = "ab c"
    for _ in range(300):
        ref = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 7)))
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 9)))
        got = E.infix_distance(ref, text)
        assert got.distance == E.infix_distance_reference(ref, text), (ref, text)
        assert 0 <= got.start <= got.end <= len(text)


def test_infix_distance_frees_the_prefix_and_suffix_and_finds_the_span() -> None:
    res = E.infix_distance("ABCD", "xxxABCDyyyy")
    assert (res.distance, res.start, res.end) == (0, 3, 7)
    res = E.infix_distance("ABCD", "xxxABXDyyyy")
    assert res.distance == 1 and (res.start, res.end) == (3, 7)
    assert E.infix_distance("", "anything") == E.Infix(0, 0, 0)
    assert E.infix_distance("abc", "") == E.Infix(3, 0, 0)
    # the whole reference is consumed: a reference longer than the text costs the difference
    assert E.infix_distance("abcdef", "abc").distance == 3
    # unicode beyond the BMP and combining marks are codepoints like any other
    assert E.infix_distance("ü", "ü").distance == 1  # the cheapest span is the u
    assert E.infix_distance("𝔘x", "a𝔘xb").distance == 0


def test_policies() -> None:
    assert E.POLICIES["reading"]("Daß  ſie") == "Daß sie"
    assert E.POLICIES["lenient"]("Daß Sie") == "dass sie"
    assert E.POLICIES["philiumm"]("Gnädiger  Herr") == "Gnädiger Herr"
    assert E.POLICIES["strict"]("x  y ") == "x  y"


# --------------------------------------------------------------------------- #
# Pooling
# --------------------------------------------------------------------------- #


def _score(lid: str, edits: int, ref: int, **kw) -> E.LetterScore:
    base = dict(
        letter_id=lid,
        year=1714,
        siglum="K",
        hand="K/k",
        half="test",
        reader="r",
        policy="philiumm",
        n_lines=10,
        n_read=10,
        ref_chars=ref,
        hyp_chars=ref + 5,
        edits=edits,
        span_start=2,
        span_end=ref + 2,
    )
    base.update(kw)
    return E.LetterScore(**base)


def test_pooled_and_aggregate_are_character_weighted_and_deterministic() -> None:
    scores = [_score("a", 10, 100), _score("b", 0, 300, siglum="L", hand="L", half="selection")]
    block = E.pooled(scores)
    assert block["letters"] == 2 and block["ref_chars"] == 400 and block["edits"] == 10
    assert block["cer"] == pytest.approx(0.025)
    assert block["letter_cer_mean"] == pytest.approx(0.05)
    assert block["cer_lo"] <= block["cer"] <= block["cer_hi"]
    assert E.pooled(scores) == block  # the bootstrap is seeded
    agg = E.aggregate(scores)
    assert set(agg["r"]["philiumm"]) == {"all", "half", "hand", "year"}
    assert agg["r"]["philiumm"]["hand"]["L"]["cer"] == 0.0
    assert agg["r"]["philiumm"]["half"]["test"]["letters"] == 1
    assert agg["r"]["philiumm"]["year"]["1714"]["letters"] == 2
    assert E.pooled([])["letters"] == 0 and E.pooled([_score("c", 3, 30)])["letter_cer_q1"] == 0.1


# --------------------------------------------------------------------------- #
# A fixture store with scripted readers
# --------------------------------------------------------------------------- #

LINES_A = [
    "An Herrn von Boineburg",  # the address: not in the reference
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten",
    "vnd bedancke mich daß Sie mir die Nachricht so bald",
    "haben zukommen lassen; es ist aber nicht zu zweiffeln",
]
LINES_B = [
    "Monsieur, je vous remercie de vostre lettre et je suis",
    "vostre tres humble et tres obeissant serviteur Leibniz",
]
REF_A = " ".join(LINES_A[1:])
REF_B = " ".join(LINES_B)


def _seed(db_path: Path) -> None:
    conn = db.init_db(db_path)
    db.upsert_work(conn, db.Work("W", "LeibnizBriefwechsel", shelfmarks=["LBr 10"]))
    seg = db.start_run(conn, "segment", model="seg")
    rec = db.start_run(conn, "recognize", model="htr@v1")
    texts = {1: LINES_A[:2], 2: LINES_A[2:], 3: LINES_B}
    for seq, lab in enumerate(["1r", "1v", "2r"], start=1):
        pid = f"W:{seq:04d}"
        db.upsert_page(conn, db.Page(work_id="W", seq=seq, label=lab, status="recognized"))
        for k, text in enumerate(texts[seq]):
            db.insert_line(conn, db.Line(page_id=pid, line_seq=k, run_id=seg, status="machine"))
            db.set_line_recognition(conn, pid, k, text=text, conf=0.9, model="h", run_id=rec)
    conn.commit()
    conn.close()


def _frozen(tmp_path: Path) -> tuple[Path, Path]:
    rows = [
        (
            "1714-1",
            1714,
            "1",
            "selection",
            "L",
            "Konzept",
            "LBr.10 Bl.1",
            "1",
            "W",
            "W:0001 W:0002",
            2,
            4,
            len(REF_A),
            text_sha256(REF_A),
        ),
        (
            "1714-2",
            1714,
            "2",
            "test",
            "K",
            "Abfertigung",
            "LBr.10 Bl.2",
            "2",
            "W",
            "W:0003",
            1,
            2,
            len(REF_B),
            text_sha256(REF_B),
        ),
    ]
    csv_path = tmp_path / "testset.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            (
                "letter_id year number half siglum kind shelfmark leaves work_id "
                "page_ids n_pages n_lines n_chars text_sha256"
            ).split()
        )
        w.writerows(rows)
    texts_path = tmp_path / "texts.jsonl"
    with texts_path.open("w", encoding="utf-8") as fh:
        for lid, text in (("1714-1", REF_A), ("1714-2", REF_B)):
            fh.write(json.dumps({"letter_id": lid, "text": text}) + "\n")
    return csv_path, texts_path


def _noisy(readings: dict[str, P.Reading]) -> dict[str, P.Reading]:
    """A reader that drops every 'e' and returns one line empty."""
    out = {}
    for lid, r in readings.items():
        text = "" if lid == "W:0002:001" else r.text.replace("e", "")
        out[lid] = P.Reading(lid, text, 0.5, "noisy@1", "cpu", 12.0)
    return out


def test_load_set_refuses_a_changed_text(tmp_path: Path) -> None:
    csv_path, texts_path = _frozen(tmp_path)
    letters = E.load_set(csv_path, texts_path)
    assert [ltr.letter_id for ltr in letters] == ["1714-1", "1714-2"]
    assert letters[0].hand == "L" and letters[1].hand == "K/k" and letters[0].half == "selection"
    texts_path.write_text(json.dumps({"letter_id": "1714-1", "text": "x"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        E.load_set(csv_path, texts_path)


def test_score_the_fixture_store_with_v1_and_a_noisy_reader(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed(store)
    csv_path, texts_path = _frozen(tmp_path)
    letters = E.load_set(csv_path, texts_path)
    from leibniz.align.audit_reach import open_readonly

    conn = open_readonly(store)
    try:
        lines = E.set_lines(conn, letters)
        v1 = E.v1_for_set(conn, letters)
    finally:
        conn.close()
    assert [ln.line_id for ln in lines["1714-1"]] == [
        "W:0001:000",
        "W:0001:001",
        "W:0002:000",
        "W:0002:001",
    ]
    readers = {"v1": v1, "noisy": _noisy(v1)}
    res = E.build_result(letters, lines, readers, licences={"v1": "store", "noisy": "—"})
    v1_all = res.aggregate["v1"]["philiumm"]["all"]
    assert v1_all["cer"] == 0.0  # the address before the letter is free; the text is exact
    assert v1_all["letters"] == 2 and v1_all["lines"] == 6 and v1_all["lines_read"] == 6
    s1 = next(
        s
        for s in res.scores
        if s.reader == "v1" and s.letter_id == "1714-1" and s.policy == "philiumm"
    )
    assert s1.span_start == len(LINES_A[0]) + 1 and s1.span_end == s1.hyp_chars
    noisy = res.aggregate["noisy"]["philiumm"]
    assert noisy["all"]["cer"] > 0 and noisy["all"]["lines_read"] == 5
    assert noisy["hand"]["L"]["letters"] == 1 and noisy["half"]["test"]["letters"] == 1
    assert res.aggregate["noisy"]["lenient"]["all"]["cer"] > 0
    sel = res.selected["v1"]
    assert (
        sel["lines"] == 6 and 0 < sel["aligned"] <= 6 and sel["policies"]["philiumm"]["cer"] == 0.0
    )
    assert res.readers[1].model == "noisy@1" and res.readers[1].ms_per_line == 12.0
    md = E.render_report(res)
    assert "| v1 |" in md and "| noisy |" in md and "selection half" in md
    assert "Hochgeehrter" not in md and "Boineburg" not in md  # numbers only
    paths = E.write_outputs(res, tmp_path / "reports")
    rows = list(csv.DictReader(paths["letters"].open(encoding="utf-8")))
    assert len(rows) == 2 * 2 * len(E.POLICIES)
    assert "Hochgeehrter" not in paths["summary"].read_text(encoding="utf-8")


def test_read_set_is_resumable_with_a_scripted_engine(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed(store)
    csv_path, texts_path = _frozen(tmp_path)
    letters = E.load_set(csv_path, texts_path)
    images = tmp_path / "images"
    # page images: the pilot's crop machinery needs a cached image per page
    from PIL import Image

    conn = db.connect(store)
    for seq in (1, 2, 3):
        local = f"W/{seq:04d}.jpg"
        (images / "W").mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (400, 200), "white").save(images / local)
        conn.execute(
            "UPDATE pages SET local_path = ? WHERE work_id = 'W' AND seq = ?", (local, seq)
        )
        conn.execute(
            "UPDATE lines SET polygon = ?, baseline = ? WHERE page_id = ?",
            (
                json.dumps([[10, 10], [390, 10], [390, 60], [10, 60]]),
                json.dumps([[10, 55], [390, 55]]),
                f"W:{seq:04d}",
            ),
        )
    conn.commit()
    conn.close()

    class Scripted:
        name = "scripted"
        version = "scripted@1"
        device = "cpu"

        def transcribe_conf(self, imgs):
            return [("gelesen", 0.9) for _ in imgs]

    from leibniz.align.audit_reach import open_readonly

    conn = open_readonly(store)
    try:
        got = E.read_set(
            conn,
            letters,
            ["echo"],
            engine_factory=lambda k: Scripted(),
            images_root=images,
            readings_dir=tmp_path / "readings",
            batch_size=4,
        )
        assert len(got["echo"]) == 6 and all(r.text == "gelesen" for r in got["echo"].values())
        again = E.read_set(
            conn,
            letters,
            ["echo"],
            engine_factory=lambda k: 1 / 0,
            images_root=images,
            readings_dir=tmp_path / "readings",
        )
        assert len(again["echo"]) == 6  # nothing left to read: the engine is never built
    finally:
        conn.close()
    assert set(E.readings_on_disk(["echo", "none"], tmp_path / "readings")) == {"echo"}


def test_letterpool_eval_cli(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed(store)
    csv_path, texts_path = _frozen(tmp_path)
    readings = tmp_path / "readings"
    readings.mkdir()
    P.append_readings(
        readings,
        "echo",
        [
            P.Reading(f"W:{p:04d}:{k:03d}", "x", None, "echo", "cpu", 1.0)
            for p, n in ((1, 2), (2, 2), (3, 2))
            for k in range(n)
        ],
    )
    out = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "align",
            "letterpool-eval",
            "--db",
            str(store),
            "--testset",
            str(csv_path),
            "--texts",
            str(texts_path),
            "--sources",
            str(tmp_path / "none.json"),
            "--readers",
            "echo",
            "--readings-dir",
            str(readings),
            "--reports-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "v1: CER 0.0%" in result.output and "echo: CER" in result.output
    summary = json.loads((out / "letterpool-eval.json").read_text(encoding="utf-8"))
    assert summary["set"]["letters"] == 2 and "echo" in summary["aggregate"]
    assert summary["aggregate"]["echo"]["philiumm"]["all"]["cer"] > 0.9
