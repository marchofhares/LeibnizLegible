"""Tests for the page-level scoring (LT1 Task 2): the PHILIUMM references from PAGE XML
(columns included), the page CER both ways, the kraken line cut and join, the line diff,
the page reader kind of the letter-pool metric on a fixture store, and the two set blocks."""

from __future__ import annotations

import io
import json
import random
from pathlib import Path

import pytest

from leibniz import db
from leibniz.align import kurrent_pilot as P
from leibniz.align import letterpool_eval as E
from leibniz.align.letterpool_set import text_sha256
from leibniz.htr import metrics
from leibniz.htr import pageread as R
from leibniz.htr import pagescore as S

pytest.importorskip("numpy")
pytest.importorskip("PIL")

NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
LINES = ["Mechanici scriptores plerique olim", "non nisi de quinque Machinis", "Fundamentalibus"]


def _page_xml(width: int = 1000, height: int = 800, extra_right: str | None = "Am Rande") -> str:
    def line(i: int, text: str, x0: int, x1: int, y: int) -> str:
        return (
            f'<TextLine id="l{i}"><Coords points="{x0},{y} {x1},{y} {x1},{y + 40} {x0},{y + 40}"/>'
            f'<Baseline points="{x0},{y + 30} {x1},{y + 30}"/>'
            f"<TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>"
        )

    body = "".join(line(i, t, 50, 450, 100 + 80 * i) for i, t in enumerate(LINES))
    body += (
        '<TextLine id="empty"><Coords points="50,400 450,400 450,440 50,440"/>'
        "<TextEquiv><Unicode></Unicode></TextEquiv></TextLine>"
    )
    right = line(9, extra_right, 600, 950, 100) if extra_right else ""
    return (
        f'<PcGts xmlns="{NS}"><Page imageFilename="p.jpg" imageWidth="{width}" '
        f'imageHeight="{height}">'
        f'<TextRegion id="r0" custom="structure {{type:MainZone;}}">{body}</TextRegion>'
        f'<TextRegion id="r1" custom="structure {{type:MarginTextZone;}}">{right}</TextRegion>'
        "</Page></PcGts>"
    )


def _jpeg(w: int, h: int) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), (220, 210, 190)).save(buf, format="JPEG")
    return buf.getvalue()


def _val_dir(tmp_path: Path) -> Path:
    d = tmp_path / "val"
    d.mkdir()
    (d / "P1.xml").write_text(_page_xml(), encoding="utf-8")
    (d / "P1.jpg").write_bytes(_jpeg(1000, 800))
    (d / "P2.xml").write_text(_page_xml(extra_right=None), encoding="utf-8")
    (d / "P2.jpg").write_bytes(_jpeg(1000, 800))
    return d


# --------------------------------------------------------------------------- #
# References
# --------------------------------------------------------------------------- #


def test_page_ref_in_document_order_and_by_column(tmp_path: Path) -> None:
    d = _val_dir(tmp_path)
    whole = S.page_ref("P1", d / "P1.xml", page_id="philiumm:P1")
    assert whole.lines == LINES + ["Am Rande"] and whole.indices == [0, 1, 2, 4]
    assert (whole.width, whole.height) == (1000, 800)
    left = S.page_ref("P1", d / "P1.xml", page_id="philiumm:P1", column="left")
    right = S.page_ref("P1", d / "P1.xml", page_id="philiumm:P1", column="right")
    assert left.lines == LINES and right.lines == ["Am Rande"] and right.indices == [4]
    rows = [
        R.PageRow("philiumm:P1", "philiumm", "hf:val/P1.jpg", ref="P1"),
        R.PageRow("philiumm:P2", "philiumm", "hf:val/P2.jpg", column="left", ref="P2"),
        R.PageRow("philiumm:P9", "philiumm", "hf:val/P9.jpg", ref="P9"),
        R.PageRow("W:0001", "pool"),
    ]
    refs, missing = S.philiumm_refs(rows, d)
    assert set(refs) == {("philiumm:P1", "whole"), ("philiumm:P2", "left")}
    assert missing == ["philiumm:P9"]


# --------------------------------------------------------------------------- #
# Distances and page scores
# --------------------------------------------------------------------------- #


def test_global_distance_matches_the_harness_on_short_and_long_strings() -> None:
    rng = random.Random(7)
    for _ in range(100):
        a = "".join(rng.choice("abc ") for _ in range(rng.randint(0, 12)))
        b = "".join(rng.choice("abc ") for _ in range(rng.randint(0, 12)))
        assert S.global_distance(a, b) == metrics.edit_distance(a, b)
    long_a = ("lorem ipsum dolor sit amet " * 12).strip()
    long_b = long_a.replace("dolor", "color").replace("amet", "amte")
    assert len(long_a) * len(long_b) >= 40_000
    assert S.global_distance(long_a, long_b) == metrics.edit_distance(long_a, long_b)
    assert S.line_similarity("abcd", "abcd") == 1.0 and S.line_similarity("", "") == 1.0
    assert S.line_similarity("abcd", "abxd") == pytest.approx(0.75)


def test_score_page_and_pooled_both_ways() -> None:
    ref = S.PageRef("philiumm:P1", "whole", "P1", LINES, [0, 1, 2])
    perfect = S.score_page(ref, "\n".join(LINES), status="ok", model="m")
    assert perfect.cer == 0.0 and perfect.n_hyp_lines == 3 and perfect.ok
    noisy = S.score_page(ref, "\n".join(LINES).replace("e", ""), status="ok", model="m")
    assert 0 < noisy.cer < 0.3 and noisy.hyp_chars < noisy.ref_chars
    failed = S.score_page(ref, "partial text", status="runaway", model="m")
    assert failed.cer == 1.0 and failed.hyp_chars == 0 and not failed.ok  # charged in full
    charged = S.pooled_pages([perfect, failed])
    omitted = S.pooled_pages([perfect, failed], failed="omit")
    assert charged["pages"] == 2 and charged["failed"] == 1 and charged["cer"] == 0.5
    assert omitted["pages"] == 1 and omitted["cer"] == 0.0 and omitted["failed"] == 1
    assert charged["cer_lo"] <= charged["cer"] <= charged["cer_hi"]
    assert charged["page_cer_max"] == 1.0 and charged["page_cer_min"] == 0.0
    agg = S.aggregate_pages([perfect, failed, noisy])
    assert set(agg["m"]) == {"philiumm"} and agg["m"]["philiumm"]["charged"]["pages"] == 3
    assert agg["m"]["philiumm"]["omitted"]["pages"] == 2


def test_score_model_marks_unread_pages_and_every_policy() -> None:
    ref = S.PageRef("philiumm:P1", "whole", "P1", LINES, [0, 1, 2])
    ref2 = S.PageRef("philiumm:P2", "whole", "P2", LINES, [0, 1, 2])
    readings = {("philiumm:P1", "whole"): {"status": "ok", "text": "\n".join(LINES)}}
    scores = S.score_model({ref.key: ref, ref2.key: ref2}, readings, "m")
    assert len(scores) == 2 * len(S.POLICIES)
    statuses = {(s.page_id, s.status) for s in scores}
    assert statuses == {("philiumm:P1", "ok"), ("philiumm:P2", "unread")}
    assert S.status_counts(
        {
            ("a", "whole"): {"status": "ok", "first_status": "refused", "attempts": 2},
            ("b", "whole"): {"status": "runaway", "first_status": "runaway", "attempts": 2},
        }
    ) == {"final": {"ok": 1, "runaway": 1}, "first": {"refused": 1, "runaway": 1}, "retried": 2}
    usage = S.usage_totals(
        {
            ("a", "whole"): {
                "engine": "gemini",
                "attempts": 2,
                "usage": {"input": 1000, "output": 300, "reasoning": 100},
                "cost": 0.01,
                "ms": 2000,
                "image": {"width": 1178, "height": 2000},
                "settings": {"reasoning": "low"},
            }
        }
    )
    assert usage["calls"] == 2 and usage["input_tokens"] == 1000 and usage["engine"] == "gemini"
    assert usage["long_side_max"] == 2000 and usage["seconds"] == 2.0


# --------------------------------------------------------------------------- #
# The kraken model's lines
# --------------------------------------------------------------------------- #


def test_cut_page_lines_and_join_the_dump_back_into_pages(tmp_path: Path) -> None:
    d = _val_dir(tmp_path)
    out = tmp_path / "lines"
    n = S.cut_page_lines(d, out)
    assert n == 7  # 4 lines with text on P1, 3 on P2 (the empty line is skipped)
    assert (out / "P1__000.png").exists() and (out / "P1__004.gt.txt").read_text() == "Am Rande\n"
    assert S.cut_page_lines(d, out) == 0  # kept
    dump = tmp_path / "dump.jsonl"
    rows = [
        {"line_id": f"line:P1__{i:03d}", "hyp": t.upper()}
        for i, t in zip([0, 1, 2], LINES, strict=True)
    ]
    rows.append({"line_id": "line:P1__004", "hyp": "AM RANDE"})
    dump.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    hyps = S.read_line_dump(dump)
    ref_whole = S.page_ref("P1", d / "P1.xml", page_id="philiumm:P1")
    ref_left = S.page_ref("P1", d / "P1.xml", page_id="philiumm:P1", column="left")
    ref_p2 = S.page_ref("P2", d / "P2.xml", page_id="philiumm:P2")
    texts, covered = S.kraken_page_texts(
        hyps, {ref_whole.key: ref_whole, ref_left.key: ref_left, ref_p2.key: ref_p2}
    )
    assert texts[ref_whole.key] == "\n".join(t.upper() for t in LINES) + "\nAM RANDE"
    assert texts[ref_left.key] == "\n".join(t.upper() for t in LINES)
    assert texts[ref_p2.key] == "\n\n" and covered == 4 + 3  # P2 uncovered: empty lines
    scored = S.score_texts({ref_whole.key: ref_whole}, texts, "kraken")
    head = next(s for s in scored if s.policy == "philiumm")
    assert head.status == "ok" and head.cer > 0  # case differs under the headline policy
    lenient = next(s for s in scored if s.policy == "lenient")
    assert lenient.cer == 0.0


# --------------------------------------------------------------------------- #
# The line diff
# --------------------------------------------------------------------------- #


def test_align_lines_pairs_similar_lines_and_gaps_the_rest() -> None:
    ref = ["Hochgeehrter Herr", "vnd bedancke mich", "haben zukommen lassen"]
    hyp = [
        "Hochgeehrter Herr",
        "an invented line here",
        "vnd bedanke mich",
        "haben zukommen lassen",
    ]
    path = S.align_lines(ref, hyp)
    assert (0, 0) in path and (1, 2) in path and (2, 3) in path and (None, 1) in path
    assert S.align_lines([], ["x"]) == [(None, 0)] and S.align_lines(["x"], []) == [(0, None)]


def test_diff_lines_counts_right_wrong_invented_dropped_and_length() -> None:
    ref = ["Hochgeehrter Herr", "vnd bedancke mich", "haben zukommen lassen", "es ist aber"]
    a = [
        "Hochgeehrter Herr",
        "vnd bedanke mich",
        "completely different words",
        "haben zukommen lassen",
    ]
    b = ["Hochgeehrter Herr", "vnd bedancke mich", "haben zukommen lasen"]
    d = S.diff_lines(ref, a, b)
    assert (d.ref_lines, d.a_lines, d.b_lines) == (4, 4, 3)
    assert d.both_right == 1  # the first line
    assert d.only_b_right == 1  # vnd bedancke mich: b exact, a one letter off
    assert d.only_a_right == 1  # haben zukommen lassen: a exact, b one letter off
    assert d.both_wrong == 1  # es ist aber: both dropped
    assert d.a_invented == 1 and d.a_dropped == 1 and d.b_invented == 0 and d.b_dropped == 1
    assert d.a_near == 3 and d.b_near == 3
    dd = d.as_dict()
    assert dd["a_length_ratio"] == pytest.approx(d.a_chars / d.ref_chars)
    total = S.diff_total([d, d])
    assert total.pages == 2 and total.both_right == 2 and total.as_dict()["b_dropped"] == 2


# --------------------------------------------------------------------------- #
# The pool: the page reader kind on a fixture store
# --------------------------------------------------------------------------- #

LINES_A = [
    "An Herrn von Boineburg",
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
    import csv

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


def _page_rows(model: str, *, fail_page: str | None = None) -> dict[tuple[str, str], dict]:
    texts = {
        "W:0001": "\n".join(LINES_A[:2]),
        "W:0002": "\n".join(LINES_A[2:]),
        "W:0003": "\n".join(LINES_B),
    }
    out = {}
    for pid, text in texts.items():
        status = "runaway" if pid == fail_page else "ok"
        out[(pid, "whole")] = {
            "page_id": pid,
            "set": "pool",
            "column": "whole",
            "model": model,
            "engine": "echo",
            "status": status,
            "first_status": status,
            "attempts": 2 if status != "ok" else 1,
            "text": text if status == "ok" else "partial",
            "usage": {"input": 100, "output": 20, "reasoning": 0},
            "cost": 0.001,
            "ms": 1500.0,
            "image": {"width": 1000, "height": 1500},
            "settings": {"reasoning": "low", "max_tokens": 4000, "temperature": 0.0},
        }
    return out


def test_machine_text_concatenates_page_readings_in_order() -> None:
    lines = [P.PilotLine(f"W:0001:{k:03d}", "W:0001", k, None, None, "x", 0.9) for k in range(2)]
    lines += [P.PilotLine(f"W:0002:{k:03d}", "W:0002", k, None, None, "x", 0.9) for k in range(2)]
    pages = S.pool_page_readings(_page_rows("m"), "m")
    assert isinstance(pages, E.PageReadings) and pages["W:0001"].model == "m"
    mt = E.machine_text(lines, pages, page_ids=["W:0001", "W:0002"])
    assert mt.text == " ".join(LINES_A) and mt.n_lines == 4 and mt.n_read == 4
    assert [h.ref for h in mt.lines] == [
        "W:0001:page:000",
        "W:0001:page:001",
        "W:0002:page:000",
        "W:0002:page:001",
    ]
    # a failed page is one empty line, so the page still counts
    failed = S.pool_page_readings(_page_rows("m", fail_page="W:0002"), "m")
    mt2 = E.machine_text(lines, failed, page_ids=["W:0001", "W:0002"])
    assert mt2.text == " ".join(LINES_A[:2]) and mt2.n_lines == 3 and mt2.n_read == 2
    # without page ids the pages come from the stored lines
    assert E.machine_text(lines, pages).text == mt.text
    info = E.reader_info("page:m", pages, "—", {"1714-1": lines})
    assert info.lines_read == 4 and info.ms_per_line is None and info.model == "m"


def test_score_pool_on_the_fixture_store_both_ways_with_the_diff(tmp_path: Path) -> None:
    store = tmp_path / "inv.sqlite"
    _seed(store)
    csv_path, texts_path = _frozen(tmp_path)
    letters = E.load_set(csv_path, texts_path)
    page_list = [
        R.PageRow("W:0001", "pool", letter_id="1714-1", hand="L", half="selection"),
        R.PageRow("W:0002", "pool", letter_id="1714-1", hand="L", half="selection"),
        R.PageRow("W:0003", "pool", letter_id="1714-2", hand="K/k", half="test"),
    ]
    # a line reader on disk: v1's lines with every 'e' dropped
    readings_dir = tmp_path / "readings"
    from leibniz.align.audit_reach import open_readonly

    conn = open_readonly(store)
    try:
        v1 = E.v1_for_set(conn, letters)
        P.append_readings(
            readings_dir,
            "k3-trocr",
            [
                P.Reading(lid, r.text.replace("e", ""), 0.5, "k3@1", "cuda", 10.0)
                for lid, r in v1.items()
            ],
        )
        block = S.score_pool(
            conn,
            letters,
            page_list,
            {"good": _page_rows("good"), "bad": _page_rows("bad", fail_page="W:0003")},
            pool_readings_dir=readings_dir,
            line_readers=["k3-trocr", "k3-kraken"],
            diff_reader="k3-trocr",
            seed=1,
        )
    finally:
        conn.close()
    assert block["draw"]["letters"] == 2 and block["draw"]["pages"] == 3
    assert block["draw"]["pages_L"] == 2 and block["draw"]["pages_K"] == 1
    agg = block["aggregate"]
    assert set(agg) == {"v1", "k3-trocr", "page:good", "page:bad"}  # k3-kraken: nothing on disk
    assert agg["page:good"]["philiumm"]["all"]["cer"] == 0.0
    assert agg["v1"]["philiumm"]["all"]["cer"] == 0.0
    assert agg["k3-trocr"]["philiumm"]["all"]["cer"] > 0
    bad = agg["page:bad"]["philiumm"]
    assert (
        bad["all"]["cer"] > 0
        and bad["hand"]["L"]["cer"] == 0.0
        and bad["hand"]["K/k"]["cer"] == 1.0
    )
    assert block["failed_pages"] == ["W:0003"] and block["omitted"]["letters"] == 1
    assert (
        block["omitted"]["aggregate"]["page:bad"]["philiumm"]["all"]["cer"] == 0.0
    )  # the failed letter left out
    assert block["statuses"]["bad"]["final"] == {"ok": 2, "runaway": 1}
    assert block["usage"]["good"]["pages"] == 3 and block["usage"]["good"]["cost"] == pytest.approx(
        0.003
    )
    diffs = {d["a"]: d for d in block["diff"]}
    assert set(diffs) == {"page:good", "page:bad"} and diffs["page:good"]["b"] == "k3-trocr"
    counts = diffs["page:good"]["counts"]
    assert (
        counts["ref_lines"] + diffs["page:good"]["declined_lines"] == 6
    )  # every stored line accounted for
    assert (
        counts["only_a_right"] >= 1 and counts["only_b_right"] == 0
    )  # the page model has the exact lines
    readers = {r["reader"]: r for r in block["readers"]}
    assert readers["page:good"]["lines_read"] == 6 and readers["k3-trocr"]["lines_read"] == 6
    letters_scored = [s for s in block["letters_scored"] if s["reader"] == "page:bad"]
    assert len(letters_scored) == 2 and all("text" not in s for s in letters_scored)


def test_score_philiumm_block_with_a_kraken_dump(tmp_path: Path) -> None:
    d = _val_dir(tmp_path)
    rows = [
        R.PageRow("philiumm:P1", "philiumm", "hf:val/P1.jpg", ref="P1"),
        R.PageRow("philiumm:P2", "philiumm", "hf:val/P2.jpg", ref="P2"),
    ]
    refs, missing = S.philiumm_refs(rows, d)
    readings = {
        ("philiumm:P1", "whole"): {
            "status": "ok",
            "text": "\n".join(LINES + ["Am Rande"]),
            "attempts": 1,
            "usage": {"input": 1, "output": 1},
            "cost": 0.0,
            "ms": 1.0,
            "image": {"width": 1, "height": 1},
            "engine": "echo",
            "settings": {},
        },
        ("philiumm:P2", "whole"): {
            "status": "refused",
            "first_status": "refused",
            "text": "",
            "attempts": 2,
            "usage": {"input": 2, "output": 0},
            "cost": 0.0,
            "ms": 1.0,
            "image": {"width": 1, "height": 1},
            "engine": "echo",
            "settings": {},
        },
    }
    hyps = {f"P1__{i:03d}": t for i, t in zip([0, 1, 2], LINES, strict=True)}
    hyps["P1__004"] = "Am Rand"
    hyps |= {f"P2__{i:03d}": t for i, t in zip([0, 1, 2], LINES, strict=True)}
    block = S.score_philiumm(
        refs, {"m": readings}, missing=missing, kraken_hyps=hyps, kraken_dump="d.jsonl"
    )
    assert block["pages"] == 2 and block["calls"] == 2 and block["ref_lines"] == 7
    agg = block["aggregate"]
    kr = next(k for k in agg if k.startswith("philiumm-kraken"))
    assert agg["m"]["philiumm"]["charged"]["cer"] == pytest.approx(
        0.5, abs=0.2
    )  # P2 charged in full
    assert (
        agg["m"]["philiumm"]["omitted"]["cer"] == 0.0
        and agg["m"]["philiumm"]["omitted"]["pages"] == 1
    )
    assert 0 < agg[kr]["philiumm"]["charged"]["cer"] < 0.05 and block["kraken"]["covered"] == 7
    assert block["statuses"]["m"]["final"] == {"ok": 1, "refused": 1}
    diff = block["diff"][0]["counts"]
    assert (
        diff["pages"] == 1 and diff["ref_lines"] == 4 and diff["only_a_right"] == 1
    )  # Am Rande vs Am Rand
    assert block["pages_scored"] and all("text" not in r for r in block["pages_scored"])
    sf = S.ScoreFile(philiumm=block)
    path = sf.save(tmp_path / "scores.json")
    assert S.ScoreFile.load(path).philiumm["pages"] == 2
