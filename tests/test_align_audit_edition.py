"""A judge's table with a transcription column (K3b-prep): the conversion to the
C2 verdict shape, the precision under the fold by stratum and group, and the
verified lines written into the fixture store. Every row here is synthetic: the
Edition's own text is not in the repository."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from tests.conftest import K2_READER_SOURCE, W3, W4
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import audit_edition as E
from leibniz.align import audit_patterns as P
from leibniz.align.audit import read_verdicts, score_by_group, score_verdicts
from leibniz.align.pairs import (
    channels_from_source,
    count_reader_rows,
    reader_from_source,
    record_id_from_source,
)
from leibniz.cli import app
from leibniz.release import export

runner = CliRunner()
READER = "trocr-kurrent-xvi-xvii"

# ref suffix, stratum, group, minted text, HTR text
SHEET = [
    ("000", "heavy_revision", "leibniz_hand", "Ich habe Ew. Excellenz Schreiben erhalten", "x"),
    ("001", "heavy_revision", "leibniz_hand", "und daß solches geschehen", "vnd das solches"),
    ("002", "heavy_revision", "leibniz_hand", "die Sache wegen der Müntze", "die Sach"),
    ("003", "fair_copy", "other_hands", "Seiner Durchlaucht zu Braunschweig", "Durchl zu"),
    ("004", "fair_copy", "other_hands", "so ich vernommen habe", "so ich vernomen"),
    (
        "005",
        "scrap",
        "other_hands",
        "Datum Hannover den dritten Martii",
        "Datum Hanover den 3 Marti",
    ),
    ("006", "light_revision", "other_hands", "Ewer Excellenz gehorsamster Diener", "Ewer"),
    ("007", "light_revision", "leibniz_hand", "und weil nun die gantze Sache", "und weil"),
]
# ref suffix → (verdict, transcription, note): the convention's cases
TABLE = {
    "000": ("correct", "", ""),
    "001": ("", "Und daß solches geschehen,", "Komma"),  # the fold removes the difference
    "002": ("", "ganz anderer Text steht hier", ""),  # another line
    "003": ("boundary", "Durchlaucht zu Braunschweig und", ""),
    "004": ("boundary", "", ""),
    "005": ("wrong", "", "crop and text do not match"),
    "006": ("unreadable", "", "a larger excerpt, please"),
    "007": ("", "", ""),
}


def _ref(k: str) -> str:
    return f"L:0001:{k}"


def _write_sheet(tmp_path: Path, *, table: dict | None = None) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    lines = tmp_path / "k2-audit-lines.csv"
    with lines.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["ref", "stratum", "align_conf", "folio", "gt_text", "htr_text", "image", "group"]
        )
        for k, stratum, group, gt, htr in SHEET:
            w.writerow([_ref(k), stratum, "0.800", "1r", gt, htr, "yes", group])
    src = tmp_path / "k2-audit-verdicts-edition.csv"
    with src.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(E.EDITION_COLUMNS)
        strata = {k: s for k, s, *_ in SHEET}
        for k, (verdict, text, note) in (table or TABLE).items():
            w.writerow([_ref(k), strata.get(k, "scrap"), verdict, text, note])
    return src, lines


def _convert(tmp_path: Path) -> tuple[Path, Path, Path]:
    src, lines = _write_sheet(tmp_path)
    out, corr = tmp_path / "k2-audit-verdicts.csv", tmp_path / "k2-audit-corrections.csv"
    conv = E.convert(E.read_table(src), E.read_lines(lines))
    E.write_verdicts(out, conv)
    E.write_corrections(corr, conv)
    return out, corr, lines


# --------------------------------------------------------------------------- #
# Task 1: the conversion
# --------------------------------------------------------------------------- #


def test_convert_maps_the_conventions_cases(tmp_path: Path) -> None:
    src, lines = _write_sheet(tmp_path)
    conv = E.convert(E.read_table(src), E.read_lines(lines))
    by = {r.ref[-3:]: r for r in conv.rows}
    # a verdict given stays, with or without a text beside it
    assert [by[k].verdict for k in ("000", "003", "004", "005", "006")] == [
        "correct",
        "boundary",
        "boundary",
        "wrong",
        "unreadable",
    ]
    assert by["005"].note == "crop and text do not match"
    # a transcription without a verdict counts as wrong; the note is kept, the phrase appended
    assert by["001"].verdict == "wrong" and by["001"].verdict_in == ""
    assert by["001"].note == f"Komma; {E.CONVERTED_PHRASE}"
    assert by["002"].verdict == "wrong" and by["002"].note == E.CONVERTED_PHRASE
    # neither: unjudged
    assert by["007"].verdict == "" and by["007"].note == ""
    assert conv.tally() == {
        "correct": 1,
        "boundary": 1,
        "boundary + transcription": 1,
        "transcription, no verdict (→ wrong)": 2,
        "wrong": 1,
        "unreadable": 1,
        "blank": 1,
    }
    groups = conv.tally_by_group()
    assert groups["leibniz_hand"] == {
        "correct": 1,
        "transcription, no verdict (→ wrong)": 2,
        "blank": 1,
    }
    assert sum(groups["other_hands"].values()) == 4
    assert [r.ref[-3:] for r in conv.corrections] == ["001", "002", "003"]
    assert conv.not_in_table == [] and conv.stratum_differs == []


def test_convert_writes_the_c2_shape_and_the_corrections_file(tmp_path: Path) -> None:
    out, corr, lines = _convert(tmp_path)
    rows = read_verdicts(out)
    assert list(rows[0]) == ["ref", "stratum", "verdict", "note"] and len(rows) == 8
    score = score_verdicts(rows)
    assert score.n_unjudged == 1 and score.pooled.n_judged == 7
    assert (score.pooled.correct, score.pooled.boundary, score.pooled.wrong) == (1, 2, 3)
    by_group = score_by_group(rows, lines)
    assert by_group["leibniz_hand"].wrong == 2 and by_group["other_hands"].unreadable == 1
    with corr.open(encoding="utf-8") as fh:
        got = list(csv.DictReader(fh))
    assert list(got[0]) == list(E.CORRECTION_COLUMNS) and len(got) == 3
    first = got[0]
    assert first["ref"] == _ref("001") and first["group"] == "leibniz_hand"
    assert first["gt_text"] == "und daß solches geschehen"
    assert first["transcription"] == "Und daß solches geschehen,"
    assert first["folded_similarity"] == "1.000" and first["note"] == "Komma"  # the judge's note
    assert float(got[1]["folded_similarity"]) < 0.5
    assert E.read_corrections(corr) == {
        _ref("001"): "Und daß solches geschehen,",
        _ref("002"): "ganz anderer Text steht hier",
        _ref("003"): "Durchlaucht zu Braunschweig und",
    }


def test_convert_makes_the_transcription_one_line_and_reads_the_sheets_labels(
    tmp_path: Path,
) -> None:
    table = {"000": ("correct · richtig", "", ""), "001": (" ", "Und  daß\nsolches ", "")}
    src, lines = _write_sheet(tmp_path, table=table)
    conv = E.convert(E.read_table(src), E.read_lines(lines))
    assert conv.rows[0].verdict == "correct"
    assert conv.rows[1].transcription == "Und daß solches" and conv.rows[1].verdict == "wrong"
    assert len(conv.not_in_table) == 6
    assert [E.parse_verdict(v) for v in ("Grenze", "FALSCH", "unreadable · unlesbar", "")] == [
        "boundary",
        "wrong",
        "unreadable",
        "",
    ]


def test_convert_refuses_a_table_that_does_not_fit_the_sheet(tmp_path: Path) -> None:
    table = {"000": ("maybe", "", ""), "999": ("correct", "", "")}
    src, lines = _write_sheet(tmp_path, table=table)
    with pytest.raises(ValueError) as err:
        E.convert(E.read_table(src), E.read_lines(lines))
    msg = str(err.value)
    assert "not a verdict: 'maybe'" in msg and f"{_ref('999')} is not on the sheet" in msg
    twice = [{"ref": _ref("000"), "verdict": "correct", "transcription": ""}] * 2
    with pytest.raises(ValueError, match="in the table twice"):
        E.convert(twice, E.read_lines(lines))
    bad = tmp_path / "bad.csv"
    bad.write_text("ref,stratum,verdict,note\nx,scrap,correct,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="transcription"):
        E.read_table(bad)


def test_cli_audit_convert_prints_the_tally(tmp_path: Path) -> None:
    src, lines = _write_sheet(tmp_path)
    out, corr = tmp_path / "out.csv", tmp_path / "corr.csv"
    args = ["align", "audit-convert", str(src), "--lines", str(lines), "--out", str(out)]
    res = runner.invoke(app, [*args, "--corrections", str(corr)])
    assert res.exit_code == 0, res.stdout
    text = " ".join(res.stdout.split())
    assert "8 rows" in text and "(3 transcriptions)" in text
    assert "transcription, no verdict (→ wrong): 2" in text and "blank: 1" in text
    assert "leibniz_hand (4): correct 1, transcription, no verdict (→ wrong) 2, blank 1" in text
    assert len(read_verdicts(out)) == 8 and len(E.read_corrections(corr)) == 3
    # the output may not be one of the inputs
    res = runner.invoke(app, [*args, "--corrections", str(src)])
    assert res.exit_code != 0 and len(E.read_table(src)) == 8


# --------------------------------------------------------------------------- #
# Task 2: under the fold
# --------------------------------------------------------------------------- #


def test_fold_scores_by_stratum_and_group(tmp_path: Path) -> None:
    out, corr, lines = _convert(tmp_path)
    rep = E.fold_scores(read_verdicts(out), E.read_lines(lines), E.read_corrections(corr))
    p = rep.pooled
    assert (p.n_judged, p.n_scored, p.correct, p.boundary) == (7, 6, 1, 2)
    assert (p.corrected_ok, p.corrected_below, p.wrong, p.unreadable) == (1, 1, 1, 1)
    assert p.strict == pytest.approx(1 / 6) and p.usable == pytest.approx(3 / 6)
    assert p.fold == pytest.approx(2 / 6) and p.fold_usable == pytest.approx(4 / 6)
    assert p.fold_ci is not None and p.fold_ci[0] < 2 / 6 < p.fold_ci[1]
    own, other = rep.by_group["leibniz_hand"], rep.by_group["other_hands"]
    assert (own.n_judged, own.correct, own.corrected_ok, own.corrected_below) == (3, 1, 1, 1)
    assert own.strict == pytest.approx(1 / 3) and own.fold == pytest.approx(2 / 3)
    assert (other.n_judged, other.boundary, other.wrong, other.unreadable) == (4, 2, 1, 1)
    assert other.strict == 0.0 and other.usable == pytest.approx(2 / 3)
    assert list(rep.by_stratum) == ["fair_copy", "light_revision", "heavy_revision", "scrap"]
    assert rep.by_stratum["heavy_revision"].corrected_ok == 1
    assert rep.by_stratum["light_revision"].n_scored == 0  # its one judged line is unreadable
    assert rep.by_stratum["light_revision"].strict is None
    # the factory's thresholds, by the row's stratum; a boundary line with a text is measured
    # but stays a boundary line
    rows = {r.ref[-3:]: r for r in rep.corrected}
    assert rows["001"].threshold == 0.72 and rows["001"].ok
    assert rows["003"].threshold == 0.55 and rows["003"].verdict == "boundary"
    assert E.threshold_for("nowhere") == 0.60
    md = "\n".join(E.render_fold(rep))
    assert "## Under the fold" in md and "| leibniz_hand | 3 | 1 | 0 | 1 | 1 | 0 | 0 |" in md
    assert "heavy_revision 0.72" in md and "Of the boundary lines, 1 carry" in md
    summ = E.fold_summary(rep)
    assert summ["by_group"]["leibniz_hand"]["under_the_fold"] == pytest.approx(2 / 3)
    assert summ["pooled"]["corrected_at_or_above_threshold"] == 1
    # a threshold of one's own moves the line across
    strict = E.fold_scores(
        read_verdicts(out),
        E.read_lines(lines),
        {_ref("001"): "und das solche geschehen"},
        thresholds={"heavy_revision": 0.99},
    )
    assert strict.pooled.corrected_ok == 0 and strict.pooled.corrected_below == 1
    assert strict.pooled.wrong == 2  # 002 has no text in this mapping: it stays wrong


def test_patterns_read_the_judges_whole_line(tmp_path: Path) -> None:
    out, corr, lines = _convert(tmp_path)
    rows = P.classify_rows(read_verdicts(out), P.read_lines_csv(lines), E.read_corrections(corr))
    by = {r.ref[-3:]: r for r in rows}
    assert by["001"].pattern == "normalization" and by["001"].from_line
    assert by["002"].pattern == "other" and "misaligned" in by["002"].signals
    assert not by["002"].undecided  # measured, not left for the override file
    assert by["003"].pattern == "boundary-letter"
    assert by["005"].pattern == "other" and by["005"].undecided  # no text: a person settles it
    assert by["000"].pattern == "correct" and not by["000"].from_line
    # the conversion's phrase is not read as a keyword of any rule
    assert by["002"].signals == ["misaligned"]
    table = P.corrections_table(rows)
    assert [r.ref[-3:] for r in table] == ["001", "002", "003"]
    assert table[0].sim_folded == 1.0 and table[0].sim_raw < 1.0
    md = "\n".join(P.render_corrections(table, whole_lines=True))
    assert "The judge's lines against the minted text" in md and "floor" not in md.split("\n")[0]
    assert "Whole lines from the judge" in "\n".join(P.render_patterns(rows, strata=()))


@pytest.mark.parametrize(
    ("minted", "judged", "signal"),
    [
        ("und daß solches geschehen", "und daß solches geschehen", "identical"),
        ("die Sache wegen der Müntz", "die Sache wegen der Müntz-", "hyphen"),
        ("die Sache wegen der Müntze", "Sache wegen der Müntze", "boundary-letter"),  # "die"
        ("die Sache wegen der Müntze", "die Sache wegen der Müntze und so", "boundary-word"),
        (
            "xcellenz Schreiben erhalten habe",
            "Excellenz Schreiben erhalten habe",
            "boundary-letter",
        ),
        ("die Sache wegen der Müntze", "die Sache der Müntze", "addition"),
        ("die Sache wegen der Müntze", "die Sache wegen der alten Müntze", "omission"),
        ("die Sache wegen der Müntze", "die Sach wegen der Müntze", "reading"),
        ("die Sache wegen der Müntze", "die Sache wegen der Ordnung", "boundary-word"),
        ("die Sache wegen der Müntze nun", "die Sache gantz der Müntze nun", "word"),
        ("die Sache wegen der Müntze", "Die Sache, wegen der Müntze.", "normalization"),
        ("die Sache wegen der Müntze", "etwas völlig anderes", "misaligned"),
    ],
)
def test_line_signals(minted: str, judged: str, signal: str) -> None:
    assert [name for name, _ in P.line_signals(minted, judged)] == [signal]


def test_a_hyphen_at_the_lines_end_names_the_line_even_on_a_wrong_verdict() -> None:
    # the word the mint gives whole is broken on the strip: a hyphen and a boundary slip
    both = P.line_signals("wegen der Müntze", "wegen der Müntz-")
    assert [name for name, _ in both] == ["hyphen", "boundary-letter"]
    row = P.classify("r", "scrap", "wrong", E.CONVERTED_PHRASE, "der Müntz", "", line="der Müntz-")
    assert row.pattern == "hyphen" and row.signals == ["hyphen"]
    # without the judge's line the same verdict is left to the HTR witness, as before
    old = P.classify("r", "scrap", "wrong", "", "der Müntz", "der Müntz-")
    assert old.pattern == "other" and not old.from_line


def _score_args(tmp_path: Path, out: Path, corr: Path, lines: Path) -> list[str]:
    return [
        "align",
        "audit-score",
        str(out),
        "--lines",
        str(lines),
        "--corrections",
        str(corr),
        "--weights",
        "fair_copy=10,light_revision=20,heavy_revision=60,scrap=10",
        "--weights-source",
        "the test",
    ]


def test_cli_audit_score_with_corrections_leaves_the_c2_files_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out, corr, lines = _convert(tmp_path / "data")
    # the C2 audit's files, where the command's defaults point
    work = tmp_path / "repo"
    c2_md, c2_json = work / "reports" / "gt-audit.md", work / "reports/gt-audit/audit-summary.json"
    c2_json.parent.mkdir(parents=True)
    c2_md.write_text("the C2 audit\n", encoding="utf-8")
    c2_json.write_text('{"c2": true}\n', encoding="utf-8")
    monkeypatch.chdir(work)
    args = _score_args(tmp_path, out, corr, lines)
    # the defaults are the C2 audit's: the three paths must be named
    res = runner.invoke(app, args)
    assert res.exit_code != 0
    assert "--out" in res.output and "--summary" in res.output and "--overrides" in res.output
    md, js = Path("reports/kurrent/k2-audit.md"), Path("reports/kurrent/k2-audit-summary.json")
    ov = Path("reports/kurrent/k2-audit-pattern-overrides.csv")
    named = ["--out", str(md), "--summary", str(js), "--overrides", str(ov)]
    res = runner.invoke(app, [*args, *named, "--title", "K2 sheet, judged by the Edition"])
    assert res.exit_code == 0, res.output
    assert c2_md.read_text(encoding="utf-8") == "the C2 audit\n"
    assert c2_json.read_text(encoding="utf-8") == '{"c2": true}\n'
    assert not (out.parent / "gt-audit-pattern-overrides.csv").exists()
    assert sorted(p.name for p in (work / "reports").rglob("*") if p.is_file()) == [
        "audit-summary.json",
        "gt-audit.md",
        "k2-audit-pattern-overrides.csv",
        "k2-audit-summary.json",
        "k2-audit.md",
    ]
    text = md.read_text(encoding="utf-8")
    assert text.startswith("# K2 sheet, judged by the Edition\n")
    assert "## Under the fold" in text and "## By group" in text
    assert "The judge's lines against the minted text" in text
    assert "| other_hands | 4 | 0 | 2 | 0 | 0 | 1 | 1 |" in text
    summ = json.loads(js.read_text(encoding="utf-8"))
    fold = summ["under_the_fold"]
    assert summ["corrections"] == corr.name and fold["thresholds"]["scrap"] == 0.80
    own = fold["by_group"]["leibniz_hand"]
    assert own["strict"] == pytest.approx(1 / 3) and own["usable"] == pytest.approx(1 / 3)
    assert own["under_the_fold"] == pytest.approx(2 / 3)
    assert len(own["under_the_fold_interval"]) == 2
    assert summ["n_judged"] == 7  # the C2 figures are still there, on the strict reading
    # the one undecided row (a wrong without a text) went to the named override file
    assert ov.read_text(encoding="utf-8").splitlines() == ["ref,pattern,why", f"{_ref('005')},,"]
    flat = " ".join(res.output.split())
    assert "under the fold leibniz_hand: strict 33.3 %" in flat
    # the judge's file is an input: the measured table is written beside it, never over it
    before = corr.read_bytes()
    res = runner.invoke(app, [*args, *named, "--corrections-out", str(corr)])
    assert res.exit_code == 0, res.output
    assert corr.read_bytes() == before
    assert corr.with_name(corr.stem + "-measured.csv").exists()


def test_cli_audit_score_defaults_are_unchanged_without_corrections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out, _corr, lines = _convert(tmp_path / "data")
    monkeypatch.chdir(tmp_path)
    res = runner.invoke(
        app, ["align", "audit-score", str(out), "--lines", str(lines), "--weights", "scrap=1"]
    )
    assert res.exit_code == 0, res.output
    md = (tmp_path / "reports" / "gt-audit.md").read_text(encoding="utf-8")
    assert md.startswith("# GT hand audit — C2 precision gate\n") and "Under the fold" not in md
    assert "under_the_fold" not in json.loads(
        (tmp_path / "reports/gt-audit/audit-summary.json").read_text(encoding="utf-8")
    )
    assert "Corrections in the notes" in md


def test_audit_score_weights_from_a_readers_rows(german_store_path: Path, tmp_path: Path) -> None:
    out, _corr, lines = _convert(tmp_path)
    args = ["align", "audit-score", str(out), "--lines", str(lines), "--db", str(german_store_path)]
    md, js = tmp_path / "a.md", tmp_path / "a.json"
    res = runner.invoke(
        app, [*args, "--out", str(md), "--summary", str(js), "--weights-reader", READER]
    )
    assert res.exit_code == 0, res.output
    summ = json.loads(js.read_text(encoding="utf-8"))
    # the fixture's five reader rows are all heavy_revision; the v1 rows carry no weight
    assert summ["by_stratum"]["heavy_revision"]["weight"] == 1.0
    assert summ["by_stratum"]["fair_copy"]["weight"] == 0.0
    assert f"the rows minted on {READER}" in summ["weights_source"]


def test_a_sheet_of_the_editions_shape_scores_as_status_says(tmp_path: Path) -> None:
    """200 synthetic rows in the counts of the table returned on 2026-11-06 (76 correct,
    21 boundary, 20 of them with a text, 98 texts without a verdict, 1 wrong, 3
    unreadable, 1 blank): the tally, and the strict and usable figures STATUS.md
    quotes from those counts (39 % and 49 %)."""
    kinds = (
        [("correct", False)] * 76
        + [("boundary", True)] * 20
        + [("boundary", False)]
        + [("", True)] * 98
        + [("wrong", False)]
        + [("unreadable", False)] * 3
        + [("", False)]
    )
    lines: dict[str, dict[str, str]] = {}
    table: list[dict[str, str]] = []
    for k, (verdict, with_text) in enumerate(kinds):
        ref = f"S:{k // 20 + 1:04d}:{k % 20:03d}"
        minted = f"synthetische Zeile Nummer {k} des Blattes"
        group = "leibniz_hand" if k % 2 else "other_hands"
        lines[ref] = {"ref": ref, "stratum": "heavy_revision", "gt_text": minted, "group": group}
        # every third text differs only in what the fold removes, the others in a word
        text = (minted.capitalize() + "," if k % 3 == 0 else minted + " mehr") if with_text else ""
        table.append({"ref": ref, "verdict": verdict, "transcription": text, "note": ""})
    conv = E.convert(table, lines)
    assert len(conv.rows) == 200 and len(conv.corrections) == 118
    assert conv.tally() == {
        "correct": 76,
        "boundary": 1,
        "boundary + transcription": 20,
        "transcription, no verdict (→ wrong)": 98,
        "wrong": 1,
        "unreadable": 3,
        "blank": 1,
    }
    rows = [{"ref": r.ref, "stratum": r.stratum, "verdict": r.verdict} for r in conv.rows]
    rep = E.fold_scores(rows, lines, {r.ref: r.transcription for r in conv.corrections})
    p = rep.pooled
    assert (p.n_judged, p.n_scored, p.correct, p.boundary) == (199, 196, 76, 21)
    assert p.corrected_ok + p.corrected_below == 98 and (p.wrong, p.unreadable) == (1, 3)
    assert f"{100 * p.strict:.0f} %" == "39 %" and f"{100 * p.usable:.0f} %" == "49 %"
    assert p.fold >= p.strict and p.fold_usable >= p.usable
    assert sum(g.n_judged for g in rep.by_group.values()) == 199


# --------------------------------------------------------------------------- #
# Task 3: the verified lines into the store
# --------------------------------------------------------------------------- #

IA = K2_READER_SOURCE.format(channel="ia")
POTSDAM = K2_READER_SOURCE.format(channel="potsdam")
MARK = "verified leibniz-edition 2026-11-06"


def test_verified_source_keeps_every_parser_reading_the_row() -> None:
    src = E.verified_source(IA, by="leibniz-edition", on="2026-11-06")
    assert src == (
        "AA IV,3 N.41 (§70-expired AA reading text; channel ia; reader "
        f"trocr-kurrent-xvi-xvii; {MARK}; katalog k-4101)"
    )
    assert reader_from_source(src) == READER and record_id_from_source(src) == "k-4101"
    assert channels_from_source(src) == ("ia",) and E.verified_from_source(src) == MARK[9:]
    assert f"; reader {READER};" in src  # the K2 sheet's and the trainset's LIKE pattern
    # idempotent, and a corrected line's channel is replaced, not added
    assert E.verified_source(src, by="leibniz-edition", on="2026-11-06") == src
    corr = E.verified_source(POTSDAM, by="leibniz-edition", on="2026-11-06", channel="edition-x")
    assert channels_from_source(corr) == ("edition-x",) and corr.count("channel") == 1
    assert corr.endswith(f"; reader {READER}; {MARK}; katalog k-4101)")
    assert E.verified_source(corr, by="leibniz-edition", on="2026-11-06", channel="edition-x") == (
        corr
    )
    # a joined channel, a row without a channel, a row without the factory's parenthesis
    joined = "AA I,9 N.1 (§70-expired AA reading text; channel ia+gwlb; katalog 7)"
    assert E.verified_source(joined, by="b", on="2026-01-01", channel="c") == (
        "AA I,9 N.1 (§70-expired AA reading text; channel c; verified b 2026-01-01; katalog 7)"
    )
    bare = "AA I,9 N.1 (§70-expired AA reading text; reader r; katalog 7)"
    assert E.verified_source(bare, by="b", on="2026-01-01", channel="c") == (
        "AA I,9 N.1 (§70-expired AA reading text; channel c; reader r; verified b 2026-01-01; "
        "katalog 7)"
    )
    assert E.verified_source("AA VI,4 N.109", by="b", on="2026-01-01") == (
        "AA VI,4 N.109 (verified b 2026-01-01)"
    )
    assert E.verified_from_source(IA) is None


def _apply_files(store: Path, tmp_path: Path) -> tuple[Path, Path, Path]:
    """A judged sheet over the fixture store's German rows, plus one more Potsdam row."""
    p1, p2, p3, q1 = f"{W3}:0001", f"{W3}:0002", f"{W3}:0003", f"{W4}:0001"
    conn = db.connect(store)
    conn.execute(
        "INSERT INTO gt_lines (line_image_ref, text, source, stratum, align_conf, "
        "license_bucket, record_id) VALUES (?, ?, ?, 'heavy_revision', 0.8, 'open', 'k-4101')",
        (db.line_id(p2, 4), "und weil nun die gantze Sache auff der Cammer beruhet", POTSDAM),
    )
    conn.commit()
    stored = {r[0]: r[1] for r in conn.execute("SELECT line_image_ref, text FROM gt_lines")}
    conn.close()
    # ref → (verdict, the judge's text, group)
    judged = {
        db.line_id(p1, 0): ("correct", "", "leibniz_hand"),
        db.line_id(p1, 1): ("", "in der Sach wegen der Müntz Ordnung", "leibniz_hand"),
        db.line_id(p1, 3): ("boundary", "Vnd daß solches geschehen sey", "leibniz_hand"),
        db.line_id(p2, 0): ("correct", "", "other_hands"),  # the Potsdam channel
        db.line_id(p2, 1): ("boundary", "", "other_hands"),
        db.line_id(p2, 4): (
            "",
            "vnd weil nun die gantze Sach auff der Cammer beruhet",
            "other_hands",
        ),
        db.line_id(q1, 0): ("unreadable", "", "other_hands"),
        db.line_id(p1, 2): ("correct", "", "leibniz_hand"),  # not minted: no row
        db.line_id(p3, 0): ("wrong", "", "other_hands"),
        db.line_id(p1, 4): ("", "", "leibniz_hand"),
    }
    lines = tmp_path / "lines.csv"
    with lines.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "gt_text", "htr_text", "group"])
        for ref, (_v, _t, group) in judged.items():
            w.writerow([ref, "heavy_revision", stored.get(ref, "und so weiter fort"), "", group])
    table = tmp_path / "edition.csv"
    with table.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(E.EDITION_COLUMNS)
        for ref, (verdict, text, _g) in judged.items():
            w.writerow([ref, "heavy_revision", verdict, text, ""])
    out, corr = tmp_path / "verdicts.csv", tmp_path / "corrections.csv"
    conv = E.convert(E.read_table(table), E.read_lines(lines))
    E.write_verdicts(out, conv)
    E.write_corrections(corr, conv)
    return out, corr, lines


def _gt_rows(store: Path) -> list[tuple]:
    conn = db.connect(store)
    try:
        return [tuple(r) for r in conn.execute("SELECT * FROM gt_lines ORDER BY id")]
    finally:
        conn.close()


def _report_counts(store: Path) -> dict:
    """What gt-report counts: lines by bucket, by stratum and by reader — and the
    report itself, rendered from the store."""
    from datetime import date

    from leibniz.align.report_gt import gather_gt, render_gt

    conn = db.connect(store)
    try:
        rep = gather_gt(
            conn,
            today=date(2026, 11, 17),
            editions_dir=store.parent / "no-editions",
            edition_cache=store.parent / "no-cache.jsonl",
            audit_summary=None,
        )
        return {
            "report": render_gt(rep),
            "bucket": dict(
                conn.execute("SELECT license_bucket, COUNT(*) FROM gt_lines GROUP BY 1").fetchall()
            ),
            "stratum": dict(
                conn.execute("SELECT stratum, COUNT(*) FROM gt_lines GROUP BY 1").fetchall()
            ),
            "reader": count_reader_rows(conn),
            "runs": conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
        }
    finally:
        conn.close()


def test_plan_apply_is_a_dry_run(german_store_path: Path, tmp_path: Path) -> None:
    out, corr, lines = _apply_files(german_store_path, tmp_path)
    before = _gt_rows(german_store_path)
    conn = db.connect(german_store_path)
    plan = E.plan_apply(conn, read_verdicts(out), E.read_lines(lines), E.read_corrections(corr))
    conn.close()
    assert plan.by_class() == {"correct": 2, "boundary": 1, "corrected": 2}
    assert {k: len(v) for k, v in plan.skipped.items()} == {
        "unjudged": 1,
        "wrong, no text given": 1,
        "unreadable": 1,
        "boundary without a transcription": 1,
        "no row in gt_lines": 1,
    }
    assert len(plan.changes) == 5 and sum(1 for r in plan.rows if r.text_changes) == 3
    assert plan.channel_changes() == {
        ("ia", "edition-k2-audit"): 2,
        ("potsdam", "edition-k2-audit"): 1,
    }
    # a confirmed line keeps its deposit; a corrected Potsdam line moves to the open one
    assert plan.deposits() == {("nc", "nc"): 1, ("nc", "open"): 1, ("open", "open"): 3}
    by = {r.ref: r for r in plan.rows}
    confirmed = by[db.line_id(f"{W3}:0002", 0)]
    assert confirmed.verdict == "correct" and confirmed.licence == "CC BY-NC 4.0"
    assert confirmed.text == confirmed.old_text and MARK in confirmed.source
    moved = by[db.line_id(f"{W3}:0002", 4)]
    assert moved.verdict == "corrected" and moved.licence == "CC BY 4.0"
    assert moved.text.startswith("vnd weil") and not moved.drifted
    assert by[db.line_id(f"{W3}:0001", 3)].verdict == "boundary"
    assert E.group_tally(plan.rows) == {
        "leibniz_hand": {"correct": 1, "corrected": 1, "boundary": 1},
        "other_hands": {"correct": 1, "corrected": 1},
    }
    assert _gt_rows(german_store_path) == before
    text = "\n".join(E.render_plan(plan))
    assert "verified lines: 5 of 10 on the sheet" in text and "dry run" in text
    assert "channel potsdam → edition-k2-audit: 1" in text
    assert "deposit: 1 moves from nc to open (CC BY 4.0)" in text
    assert "deposit: 1 stays in nc (CC BY-NC 4.0)" in text


def test_cli_audit_apply_dry_run_write_and_idempotence(
    german_store_path: Path, tmp_path: Path
) -> None:
    out, corr, lines = _apply_files(german_store_path, tmp_path)
    verified = tmp_path / "reports" / "k3b-verified.csv"
    args = [
        "align",
        "audit-apply",
        "--verdicts",
        str(out),
        "--lines",
        str(lines),
        "--corrections",
        str(corr),
        "--db",
        str(german_store_path),
        "--out",
        str(verified),
    ]
    before, counts = _gt_rows(german_store_path), _report_counts(german_store_path)
    res = runner.invoke(app, args)
    assert res.exit_code == 0, res.output
    flat = " ".join(res.output.split())
    assert "dry run" in flat and "rows to change: 5 (text replaced on 3;" in flat
    assert "not verified — boundary without a transcription: 1" in flat
    assert "leibniz_hand: correct 1, corrected 1, boundary 1" in flat
    assert _gt_rows(german_store_path) == before and _report_counts(german_store_path) == counts
    with verified.open(encoding="utf-8") as fh:
        got = list(csv.DictReader(fh))
    assert list(got[0]) == list(E.VERIFIED_COLUMNS) and len(got) == 5
    assert {r["verified_by"] for r in got} == {"leibniz-edition 2026-11-06"}
    by = {r["ref"]: r for r in got}
    one = by[db.line_id(f"{W3}:0001", 1)]
    assert one["verdict"] == "corrected" and one["text"] == "in der Sach wegen der Müntz Ordnung"
    assert one["licence"] == "CC BY 4.0" and one["group"] == "leibniz_hand"
    kept = by[db.line_id(f"{W3}:0001", 0)]  # the minted text where unchanged
    assert (
        kept["verdict"] == "correct" and kept["text"] == "Ich habe Ew. Excellenz Schreiben erhalten"
    )
    assert by[db.line_id(f"{W3}:0002", 0)]["licence"] == "CC BY-NC 4.0"

    # the write: one runs row, the rows updated in place, the report's counts unchanged
    res = runner.invoke(app, [*args, "--write"])
    assert res.exit_code == 0, res.output
    after = _report_counts(german_store_path)
    assert after == {**counts, "runs": counts["runs"] + 1}
    rows = _gt_rows(german_store_path)
    assert len(rows) == len(before) and [r[0] for r in rows] == [r[0] for r in before]
    assert sum(1 for a, b in zip(before, rows, strict=True) if a != b) == 5
    conn = db.connect(german_store_path)
    run = conn.execute("SELECT * FROM runs ORDER BY run_id DESC LIMIT 1").fetchone()
    assert run["stage"] == "gt_audit" and run["model"] == "leibniz-edition-k2-audit"
    assert run["finished_at"] and (run["n_input"], run["n_ok"], run["n_failed"]) == (5, 5, 0)
    params = json.loads(run["params"])
    assert params["by_class"] == {"correct": 2, "boundary": 1, "corrected": 2}
    assert params["text_replacements"] == 3 and len(params["inputs"]["verdicts.csv"]) == 64
    assert f"written under run {run['run_id']}" in " ".join(res.output.split())
    stored = {
        r["line_image_ref"]: r
        for r in conn.execute("SELECT * FROM gt_lines WHERE record_id = 'k-4101'")
    }
    fixed = stored[db.line_id(f"{W3}:0001", 1)]
    assert fixed["text"] == "in der Sach wegen der Müntz Ordnung"
    assert fixed["source"] == (
        "AA IV,3 N.41 (§70-expired AA reading text; channel edition-k2-audit; reader "
        f"trocr-kurrent-xvi-xvii; {MARK}; katalog k-4101)"
    )
    assert fixed["align_conf"] == 0.74 and fixed["license_bucket"] == "open"
    untouched = stored[db.line_id(f"{W3}:0002", 1)]  # boundary without a text
    assert "verified" not in untouched["source"] and untouched["text"] == "so ich vernommen habe"
    # the export: a corrected row in the open deposit, the confirmed Potsdam row in the NC one
    open_rows = {r["line_image_ref"]: r for r in export.iter_gt(conn)}
    nc_rows = {r["line_image_ref"]: r for r in export.iter_gt_nc(conn)}
    moved = db.line_id(f"{W3}:0002", 4)
    assert moved in open_rows and moved not in nc_rows
    assert open_rows[moved]["text"].startswith("vnd weil nun die gantze Sach auff")
    assert "channel edition-k2-audit" in open_rows[moved]["source"]
    confirmed = db.line_id(f"{W3}:0002", 0)
    assert confirmed in nc_rows and confirmed not in open_rows
    assert (
        MARK in nc_rows[confirmed]["source"] and "channel potsdam" in nc_rows[confirmed]["source"]
    )
    assert open_rows[db.line_id(f"{W3}:0001", 0)]["text"].startswith("Ich habe Ew. Excellenz")
    census = export.gt_deposit_census(conn)
    assert census["open"]["edition-k2-audit"] == 3 and census["nc"] == {"potsdam": 1}
    conn.close()

    # again: nothing changes, no second run, and the command says so
    res = runner.invoke(app, [*args, "--write"])
    assert res.exit_code == 0, res.output
    assert "nothing to change" in " ".join(res.output.split())
    assert _gt_rows(german_store_path) == rows and _report_counts(german_store_path) == after
    with verified.open(encoding="utf-8") as fh:
        assert list(csv.DictReader(fh)) == got  # the same verified lines from the written store


def test_apply_leaves_a_confirmed_line_whose_text_moved(
    german_store_path: Path, tmp_path: Path
) -> None:
    out, corr, lines = _apply_files(german_store_path, tmp_path)
    conn = db.connect(german_store_path)
    conn.execute(
        "UPDATE gt_lines SET text = 'ein anderer Text' WHERE line_image_ref = ?",
        (db.line_id(f"{W3}:0001", 0),),
    )
    conn.execute(  # a second row on a corrected line's ref
        "INSERT INTO gt_lines (line_image_ref, text, source, stratum, align_conf, "
        "license_bucket) VALUES (?, 'x', 'manual', 'scrap', 0.5, 'nc')",
        (db.line_id(f"{W3}:0001", 1),),
    )
    conn.execute(
        "UPDATE gt_lines SET text = 'neu gemünzt' WHERE line_image_ref = ?",
        (db.line_id(f"{W3}:0001", 3),),
    )
    conn.commit()
    plan = E.plan_apply(conn, read_verdicts(out), E.read_lines(lines), E.read_corrections(corr))
    assert plan.skipped["the stored text is not the sheet's"] == [db.line_id(f"{W3}:0001", 0)]
    assert plan.skipped["more than one row in gt_lines"] == [db.line_id(f"{W3}:0001", 1)]
    # a corrected line takes the judge's text whatever the store held, and is listed
    drifted = [r.ref for r in plan.rows if r.drifted]
    assert drifted == [db.line_id(f"{W3}:0001", 3)]
    # a row that moves between the plan and the write stops the write whole
    conn.execute("UPDATE gt_lines SET text = 'noch einmal' WHERE id = ?", (plan.rows[-1].gt_id,))
    conn.commit()
    n_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    with pytest.raises(RuntimeError, match="changed since the plan"):
        E.apply_plan(conn, plan)
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == n_runs
    assert not conn.execute("SELECT 1 FROM gt_lines WHERE source LIKE '%verified%'").fetchone()
    conn.close()


def test_cli_audit_apply_refuses_what_it_cannot_parse(
    german_store_path: Path, tmp_path: Path
) -> None:
    out, corr, lines = _apply_files(german_store_path, tmp_path)
    base = ["align", "audit-apply", "--verdicts", str(out), "--lines", str(lines)]
    base += ["--corrections", str(corr), "--out", str(tmp_path / "v.csv")]
    for extra in (
        ["--db", str(tmp_path / "nope.sqlite")],
        ["--db", str(german_store_path), "--channel", "no-such-channel"],
        ["--db", str(german_store_path), "--verified-on", "6 November"],
        ["--db", str(german_store_path), "--verified-by", "two words"],
    ):
        res = runner.invoke(app, [*base, *extra])
        assert res.exit_code != 0, extra
    assert not (tmp_path / "nope.sqlite").exists() and not (tmp_path / "v.csv").exists()
