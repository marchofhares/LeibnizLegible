"""The mixed-letters measure (K4 Task 2) on a tiny per-letter CSV and set."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from leibniz.align import letterpool_mixed as M
from leibniz.cli import app

GERMAN = (
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten vnd bedancke mich daß Sie mir die "
    "Nachricht so bald haben zukommen lassen; es ist aber nicht zu zweiffeln daß der Herr alß "
    "ein verständiger Mann die Sache wol vberlegen wird."
)
MIXED = (
    "Hochgeehrter Herr, ich habe dero Schreiben erhalten vnd bedancke mich. Vir amplissime, "
    "literas tuas accepi quibus de rebus mathematicis ad me scripsisti; ego vero puto non esse "
    "dubitandum quod haec omnia ex principiis nostris deduci possint."
)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    testset = tmp_path / "testset.jsonl"
    testset.write_text(
        "".join(
            json.dumps({"letter_id": lid, "text": text}) + "\n"
            for lid, text in (("1708-1", GERMAN), ("1708-2", MIXED), ("1709-3", GERMAN))
        ),
        encoding="utf-8",
    )
    letters = tmp_path / "letters.csv"
    cols = ["letter_id", "year", "siglum", "half", "reader", "policy", "n_lines", "n_read"]
    cols += ["ref_chars", "hyp_chars", "edits", "cer", "span_start", "span_end"]
    rows = [
        ("1708-1", "v1", 10, 100, 40),
        ("1708-2", "v1", 20, 200, 60),
        ("1709-3", "v1", 10, 100, 50),
        ("1708-1", "k3-trocr", 10, 100, 20),
        ("1708-2", "k3-trocr", 20, 200, 50),
        ("1709-3", "k3-trocr", 10, 100, 30),
    ]
    with letters.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for lid, reader, n_lines, ref, edits in rows:
            for policy in ("philiumm", "strict"):
                e = edits if policy == "philiumm" else edits + 5
                w.writerow(
                    [lid, lid[:4], "L", "test", reader, policy, n_lines, n_lines, ref, ref, e]
                    + [round(e / ref, 4), 0, ref]
                )
    return letters, testset


def test_letter_mixes_group_the_letters() -> None:
    mixes = M.letter_mixes({"a": GERMAN, "b": MIXED})
    assert mixes["a"].group == "german" and mixes["a"].lang == "de"
    assert mixes["b"].group == "mixed" and mixes["b"].lafr_share >= 0.25


def test_scores_gains_and_cost(tmp_path: Path) -> None:
    letters, testset = _fixture(tmp_path)
    summ, paths = M.run(letters_csv=letters, testset=testset, reports_dir=tmp_path / "reports")
    assert summ["by_group"] == {"mixed": 1, "german": 2}
    by = {(s["group"], s["reader"]): s for s in summ["scores"]}
    assert by[("german", "v1")]["cer"] == 0.45 and by[("german", "k3-trocr")]["cer"] == 0.25
    assert by[("mixed", "v1")]["cer"] == 0.3 and by[("mixed", "k3-trocr")]["cer"] == 0.25
    assert by[("german", "v1")]["letters"] == 2 and by[("german", "v1")]["lines"] == 20
    assert summ["gain"] == {"mixed": 0.05, "german": 0.2}
    assert summ["cost"] == 0.15
    md = paths["k4-mixed-letters.md"].read_text(encoding="utf-8")
    assert "**1 mixed letters, 2 German ones**" in md
    assert "**15.0 %** of CER" in md
    assert GERMAN[:20] not in md  # numbers only, never the pool's text
    assert json.loads(paths["k4-mixed-letters.json"].read_text(encoding="utf-8"))["cost"] == 0.15


def test_cli_letterpool_mixed(tmp_path: Path) -> None:
    letters, testset = _fixture(tmp_path)
    res = CliRunner().invoke(
        app,
        [
            "align",
            "letterpool-mixed",
            "--letters-csv",
            str(letters),
            "--testset",
            str(testset),
            "--reports-dir",
            str(tmp_path / "reports"),
        ],
    )
    assert res.exit_code == 0, res.output
    assert "letterpool-mixed" in res.output
    assert (tmp_path / "reports" / "k4-mixed-letters.md").exists()
    res = CliRunner().invoke(
        app,
        ["align", "letterpool-mixed", "--letters-csv", str(letters), "--testset", str(testset)]
        + ["--readers", "v1,nope", "--reports-dir", str(tmp_path / "r2")],
    )
    assert res.exit_code != 0
