"""Tests for the audit pattern rules and the correction parser (offline, synthetic rows)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from leibniz.align import audit_patterns as P


def _row(
    verdict: str,
    note: str = "",
    gt: str = "la difficulté demeure",
    htr: str = "la diffieulte demeure",
) -> P.PatternRow:
    return P.classify("W:0001:000", "fair_copy", verdict, note, gt, htr)


def test_precedence_and_each_rule() -> None:
    assert _row("unreadable").pattern == "unreadable"
    # addition by note, and by the insertion floor on a wrong verdict only
    assert _row("wrong", '"in melius auctam" is an addition').pattern == "addition"
    long = "indies in melius auctam restitui perfecte et opto et"
    assert _row("wrong", "", gt=long, htr="indies et").pattern == "addition"
    assert _row("boundary", "", gt=long, htr="indies et").pattern == "boundary-letter"
    # math by note, by operator density, and not by a bare year
    assert _row("wrong", "2 dimension math expression").pattern == "math"
    assert _row("wrong", "", gt="x\n+ 30e\n+ 3e\n-9e\n— e\n-", htr="X").pattern == "math"
    assert _row("correct", "", gt="ctobris 1691", htr="ctohis: 1691").pattern == "correct"
    assert _row("correct", "", gt="a = b sunt", htr="a = b sunt").pattern == "correct"  # one op
    # bracket leak
    assert _row("correct", "", gt="tirer [,] vous pourrez").pattern == "bracket"
    # hyphen: mechanical (HTR mark, minted letter) and by note; named on correct only
    assert _row("correct", "", gt="minis pro", htr="minis pro-").pattern == "hyphen"
    assert _row("correct", "", gt="minis pro=", htr="minis pro=").pattern == "correct"
    assert _row("correct", "missing hyphen at the end").pattern == "hyphen"
    assert _row("correct", "missing hyphen at the end").signals == ["hyphen-note", "correct"]
    b = _row(
        "boundary",
        'missing "hoc" before "divina"; missing hyphen at the end',
        gt="m divina",
        htr="hoi divina nega-",
    )
    assert b.pattern == "boundary-letter" and "hyphen" in b.signals  # mechanical, kept as a signal
    # boundary from the verdict, or from a one-end correction on a correct line
    assert _row("boundary").pattern == "boundary-letter"
    r = _row("correct", 'missing "r" at the end in "communiquer"', gt="rai pas de vous communique")
    assert r.pattern == "boundary-letter"
    # reading vs normalization vs misaligned, from a correction pair
    assert (
        _row("wrong", '"Casal" instead of "Casai"', gt="environs de Casai et").pattern == "reading"
    )
    assert (
        _row("wrong", '"envoyé" -> "envoye"', gt="je vous envoyé maintenant").pattern
        == "normalization"
    )
    assert _row("correct", 'no comma after "teste"').pattern == "normalization"
    m = _row("wrong", '"serviteur" instead of "érité"', gt="érité", htr="erviteur")
    assert m.pattern == "other" and m.undecided and "misaligned" in m.signals
    assert _row("correct").pattern == "correct"


def test_unreadable_note_does_not_override_a_verdict() -> None:
    r = _row(
        "boundary", '"imprimer" instead of "primer"; We cannot read the last word.', gt="primer ses"
    )
    assert r.pattern == "boundary-letter" and "unreadable-note" in r.signals


@pytest.mark.parametrize(
    ("note", "minted", "expected"),
    [
        ('"Casal" instead of "Casai"', "de Casai et", [("replace", "Casai", "Casal", "")]),
        (
            'We read "praevideatur" instead of "provideatur".',
            "Ecclesiae provideatur.",
            [("replace", "provideatur", "praevideatur", "")],
        ),
        ('"non era" -> "non erant"', "per se non era", [("replace", "non era", "non erant", "")]),
        ('"Roy"  -> missing "y"', "pauure Ro", [("replace", "Ro", "Roy", "")]),
        (
            '"Christus" -> "C" initial letter missing; last "o" should not be there.',
            "hristus secundum quod o",
            [("replace", "hristus", "Christus", ""), ("delete", "o", "", "end")],
        ),
        ('missing "s" at "oserois"', "si j’oseroi", [("replace", "oseroi", "oserois", "")]),
        (
            'missing "S" in "Schrijft", missing "n" at the end word "drucken"',
            "chrijft dat drucke",
            [("replace", "chrijft", "Schrijft", ""), ("insert", "", "n", "end")],
        ),
        (
            '"de" missing at the beginning; "de la quitter pour..."',
            "la quiter pour",
            [("insert", "", "de", "start")],
        ),
        (
            'Missing "hoc" before "divina sapientia"',
            "m divina sapientia",
            [("insert", "", "hoc", "before:divina sapientia")],
        ),
        (
            'added "," after "inter se", not present in the manuscript',
            "inter se, et cum",
            [("delete", ",", "", "after:inter se")],
        ),
        (
            'We do not see the "is" after "Porro"',
            "Porro is Plantae",
            [("delete", "is", "", "after:Porro")],
        ),
        (
            '"orbo" at the end of the line not present on the crop.',
            "de rege orbo,",
            [("delete", "orbo", "", "end")],
        ),
        ('just "d" should not appear at the end', "Tridentino d", [("delete", "d", "", "end")]),
        (
            '"n" at the beginning should not appear',
            "n gelindigkeit",
            [("delete", "n", "", "start")],
        ),
        (
            'no "su" at the beginning; no "Addit" at the end',
            "su Amuletorum. Addit",
            [("delete", "su", "", "start"), ("delete", "Addit", "", "end")],
        ),
        ('"serviteur", no "C".', "serviteur C", [("delete", "C", "", "")]),
        ('"eg" is transcribed as "ia"', "ia yy x", [("replace", "ia", "eg", "")]),
        (
            'correct boundary: "la bonne foy qu’il"',
            "la bonne foy qu’il a",
            [("line", "", "la bonne foy qu’il", "")],
        ),
        ("We do not add the accent if not present in the manuscript", "x", []),
        ('"habeamus" -> not sure we see the end of the word', "habeamus", []),
    ],
)
def test_extract_corrections(note: str, minted: str, expected: list) -> None:
    got = [(c.op, c.minted, c.corrected, c.where) for c in P.extract_corrections(note, minted)]
    assert got == expected


def test_apply_correction_places_edits_or_declines() -> None:
    assert (
        P.apply_correction("de Casai et", P.Correction("replace", "Casai", "Casal"))
        == "de Casal et"
    )
    assert (
        P.apply_correction("la quiter pour", P.Correction("insert", "", "de", "start"))
        == "de la quiter pour"
    )
    assert P.apply_correction("drucke", P.Correction("insert", "", "n", "end")) == "drucken"
    assert (
        P.apply_correction("de rege orbo,", P.Correction("delete", "orbo", "", "end")) == "de rege"
    )
    assert (
        P.apply_correction("inter se, et cum", P.Correction("delete", ",", "", "after:inter se"))
        == "inter se et cum"
    )
    assert (
        P.apply_correction("Porro\nis Plantae", P.Correction("delete", "is", "", "after:Porro"))
        == "Porro Plantae"
    )
    # the other apostrophe, and a fragment that occurs twice or not at all
    assert (
        P.apply_correction(
            "’observatoire, elle", P.Correction("replace", "'observatoire", "L'observatoire")
        )
        == "L'observatoire, elle"
    )
    assert P.apply_correction("et et", P.Correction("replace", "et", "ut")) is None
    assert P.apply_correction("abc", P.Correction("delete", "zzz", "")) is None
    assert P.apply_correction("abc", P.Correction("line", "", "xyz")) == "xyz"


def test_corrections_table_measures_raw_and_folded_tax() -> None:
    row = P.classify(
        "r1",
        "heavy_revision",
        "wrong",
        '"envoyé" -> "envoye"',
        "Et je vous envoyé maintenant",
        "et je vous envoye",
    )
    (t,) = P.corrections_table([row])
    assert t.corrected_text == "Et je vous envoye maintenant"
    assert t.sim_raw is not None and 0.9 < t.sim_raw < 1.0  # one accent
    assert t.sim_folded == 1.0  # invisible to the aligner's fold
    unplaced = P.classify(
        "r2", "scrap", "boundary", '"2 (Danebens" -> shouldn\'t be there', "mon 2 (Daneben", "mon"
    )
    (u,) = P.corrections_table([unplaced])
    assert u.corrected_text == "" and u.sim_raw is None


def test_overrides_and_csv_outputs(tmp_path: Path) -> None:
    rows = [
        P.classify("a", "scrap", "wrong", "", "x° etc. et area", "+xc et area"),
        P.classify("b", "scrap", "correct", "", "fort connu", "fort connu"),
    ]
    assert rows[0].pattern == "other" and rows[0].undecided
    ov = tmp_path / "overrides.csv"
    assert P.write_override_template(rows, ov) == 1
    with ov.open(encoding="utf-8") as fh:
        assert [r["ref"] for r in csv.DictReader(fh)] == ["a"]
    ov.write_text('ref,pattern,why\na,math,"a formula fragment"\n', encoding="utf-8")
    assert P.apply_overrides(rows, P.read_overrides(ov)) == 1
    assert rows[0].pattern == "math" and rows[0].overridden and not rows[0].undecided
    assert P.write_override_template(rows, ov) == 0  # nothing undecided, file untouched
    with pytest.raises(ValueError):
        P.read_overrides(_write(tmp_path / "bad.csv", "ref,pattern,why\na,nonsense,\n"))
    P.write_patterns_csv(rows, tmp_path / "p.csv")
    P.write_corrections_csv(P.corrections_table(rows), tmp_path / "c.csv")
    with (tmp_path / "p.csv").open(encoding="utf-8") as fh:
        got = list(csv.DictReader(fh))
    assert got[0]["pattern"] == "math" and got[1]["pattern"] == "correct"
    md = "\n".join(P.render_patterns(rows, strata=("fair_copy", "scrap")))
    assert "| scrap | 2 |" in md and "math" in md and "1 settled by the override file" in md
    assert "No note carries a correction" in "\n".join(P.render_corrections([]))


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_math_density_and_counts() -> None:
    ops, all_ = P.math_density("x - y = 2")
    assert ops > 0.1 and all_ > ops
    assert P.math_density("") == (0.0, 0.0)
    assert not P.is_math_dense("einen halben dach 13 g. 4")  # digits without an operator
    assert not P.is_math_dense("minis pro=") and P.is_math_dense("x + 30e = 0")
    rows = [_row("correct"), _row("boundary"), _row("unreadable")]
    counts = P.pattern_counts(rows)
    assert counts["all"] == {"correct": 1, "boundary-letter": 1, "unreadable": 1}
    assert counts["fair_copy"]["boundary-letter"] == 1
    assert P.by_verdict(rows)["boundary"] == {"boundary-letter": 1}
