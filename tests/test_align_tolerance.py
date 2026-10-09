"""Tests for the aligner noise-tolerance study (K1 Task 1); offline, on fixtures."""

from __future__ import annotations

import json
import random
from pathlib import Path

from typer.testing import CliRunner

from leibniz.align import evaluate as E
from leibniz.align import tolerance as T
from leibniz.align.align import AlignedLine, AlignmentResult
from leibniz.cli import app

runner = CliRunner()

_WORDS = (
    "deus mundus ratio natura corpus anima mens veritas motus quies spatium tempus "
    "principium causa substantia monas harmonia lex ordo numerus figura vis potentia "
    "actus forma materia infinitum unum ens bonum verum pulchrum"
).split()


def _synthetic_lines(n: int, *, seed: int = 7, words: int = 7) -> list[T.ReproLine]:
    """Pseudo-Latin lines whose machine text is the gold with a little noise."""
    rng = random.Random(seed)
    out: list[T.ReproLine] = []
    for i in range(n):
        ref = " ".join(rng.choice(_WORDS) for _ in range(words))
        hyp, _ = T.corrupt_line(ref, 0.04, rng)
        out.append(T.ReproLine(f"v:{i:04d}", ref, hyp))
    return out


# --------------------------------------------------------------------------- #
# The corruption model
# --------------------------------------------------------------------------- #


def test_corrupt_zero_rate_is_identity() -> None:
    text = "Mechanici scriptores plerique olim, non nisi de quinque Machinis"
    assert T.corrupt_line(text, 0.0, random.Random(1)) == (text, 0)


def test_corrupt_is_deterministic_under_a_seed() -> None:
    text = "ut vocant loquebantur, Vecte, Cuneo, Axe in Peritrochio"
    a = T.corrupt_line(text, 0.3, random.Random(5))
    b = T.corrupt_line(text, 0.3, random.Random(5))
    assert a == b
    assert a[0] != text and a[1] > 0


def test_corrupt_fires_nested_positions_as_the_rate_grows() -> None:
    # The same seed draws the same uniforms per position, so a higher rate fires
    # a superset of positions: the op count never drops.
    text = "primum mobile et causa efficiens omnium rerum naturalium"
    counts = [T.corrupt_line(text, r, random.Random(11))[1] for r in (0.1, 0.2, 0.4, 0.8, 1.0)]
    assert counts == sorted(counts)
    assert counts[-1] == len(text)


def test_substitutions_come_from_the_confusion_table() -> None:
    # Force every position to fire with a substitution (kind < OP_SUBSTITUTE) and
    # check each output letter sits in its source letter's row.
    class _Rng:
        def __init__(self) -> None:
            self.calls = 0

        def random(self) -> float:
            self.calls += 1
            k = self.calls % 3  # 1: fire, 2: kind, 0: pick
            return {1: 0.0, 2: 0.0, 0: 0.5}[k]

    text = "monas"
    out, n_ops = T.corrupt_line(text, 1.0, _Rng())  # type: ignore[arg-type]
    assert n_ops == len(text)
    i = 0
    for ch in text:
        row = T.CONFUSIONS[ch]
        hit = next(t for t in sorted(row, key=len, reverse=True) if out.startswith(t, i))
        i += len(hit)
    assert i == len(out)


def test_space_fires_as_a_merged_word_space() -> None:
    class _Rng:
        def random(self) -> float:
            return 0.0

    out, n_ops = T.corrupt_line(" ", 1.0, _Rng())  # type: ignore[arg-type]
    assert out == "" and n_ops == 1


def test_merge_consumes_the_next_character() -> None:
    # kind in the merge bucket, pair "in" → "m"
    seq = iter([0.0, 0.85, 0.0, 0.9, 0.9, 0.9])

    class _Rng:
        def random(self) -> float:
            return next(seq)

    out, n_ops = T.corrupt_line("in", 1.0, _Rng())  # type: ignore[arg-type]
    assert out == "m" and n_ops == 1


def test_calibrate_reaches_the_target() -> None:
    lines = _synthetic_lines(60)
    refs = [ln.ref for ln in lines]
    hyps = [ln.hyp for ln in lines]
    base = T.corpus_cer(refs, hyps)
    assert base < 0.10
    for target in (0.20, 0.40):
        rate, cer = T.calibrate_rate(refs, hyps, target, seed=3)
        assert 0 < rate < 1
        assert abs(cer - target) < 0.02
        corrupted, _ = T.corrupt_all(hyps, rate, seed=3, target=target)
        assert abs(T.corpus_cer(refs, corrupted) - cer) < 1e-9  # the same stream


def test_calibrate_below_base_returns_zero_rate() -> None:
    lines = _synthetic_lines(30)
    refs = [ln.ref for ln in lines]
    hyps = [ln.hyp for ln in lines]
    rate, cer = T.calibrate_rate(refs, hyps, 0.0, seed=1)
    assert rate == 0.0 and cer == T.corpus_cer(refs, hyps)


def test_op_mix_counts_each_kind() -> None:
    mix = T.op_mix(["abcd", "xyz"], ["abd", "xyzz"])
    assert mix == {"match": 6, "substitution": 0, "deletion": 1, "insertion": 1}


# --------------------------------------------------------------------------- #
# The harness: factory gate
# --------------------------------------------------------------------------- #


def test_summarize_factory_gate_refuses_bursts() -> None:
    lines = [
        E.LineEval("a", "x", "x", "x", 0.9, True, 1.0),
        E.LineEval("b", "y", "y", "y plus a burst", 0.9, False, 0.4, burst=True),
    ]
    cfg = E.EvalConfig(label="t", threshold=0.5)
    plain = E.summarize(lines, cfg)
    gated = E.summarize(lines, cfg, factory_gate=True)
    assert plain.n_aligned == 2 and plain.precision == 0.5
    assert gated.n_aligned == 1 and gated.precision == 1.0


def test_evaluate_piece_flags_a_burst(monkeypatch) -> None:
    # The flag is the factory's rule on the aligner's counts: more edition-only
    # characters inserted into the line than max(MAX_INSERT_FLOOR, its length).
    golds = ["prima linea", "secunda linea", "tertia linea"]
    piece = E.Piece("p", [E.GoldLine(f"v:{i}", g, b"") for i, g in enumerate(golds)])
    htr = {f"v:{i}": g for i, g in enumerate(golds)}

    def fake_align(htr_lines, edition_text, **kw):
        lines = []
        for k, ln in enumerate(htr_lines):
            n_ins = 40 if k == 1 else 0
            lines.append(
                AlignedLine(
                    ref=ln.ref,
                    htr_text=ln.text,
                    edition_text=golds[k],
                    align_conf=1.0,
                    n_htr_chars=len(ln.text),
                    n_matched=len(ln.text),
                    aligned=n_ins == 0,
                    n_inserted=n_ins,
                )
            )
        return AlignmentResult(lines, kw.get("threshold", 0.6), "align-default", 0, 0)

    monkeypatch.setattr(E, "align_piece", fake_align)
    cfg = E.EvalConfig(label="clean", threshold=0.5)
    evals = E.evaluate_piece(piece, htr, cfg)
    assert [le.burst for le in evals] == [False, True, False]
    assert E.summarize(evals, cfg).n_aligned == 3
    assert E.summarize(evals, cfg, factory_gate=True).n_aligned == 2


# --------------------------------------------------------------------------- #
# Levels, break-even, the report
# --------------------------------------------------------------------------- #


def test_run_level_base_and_corrupted() -> None:
    lines = _synthetic_lines(40)
    base = T.run_level(lines, None, lines_per_piece=10, thresholds={"fair_copy": 0.55})
    hard = T.run_level(lines, 0.5, lines_per_piece=10, thresholds={"fair_copy": 0.55})
    assert base.n_pieces == 4 and base.n_lines == 40
    assert base.rate == 0.0 and base.n_ops == 0
    assert hard.cer_written > base.cer_written
    assert hard.mean_conf < base.mean_conf
    assert hard.by_stratum["fair_copy"].yield_rate <= base.by_stratum["fair_copy"].yield_rate
    assert base.by_stratum["fair_copy"].threshold == 0.55


def test_break_even_interpolates_between_levels() -> None:
    def lv(cer: float, y: float, p: float) -> T.LevelResult:
        o = T.StratumOutcome(
            "fair_copy", 0.55, 100, int(y * 100), int(y * p * 100), y, p, None, None
        )
        return T.LevelResult("l", cer, 0.1, 0, cer, cer, 100, 4, 0.5, 0.5, 0, {"fair_copy": o})

    levels = [lv(0.1, 0.9, 0.99), lv(0.3, 0.7, 0.96), lv(0.5, 0.3, 0.80)]
    be_y = T.break_even(levels, "fair_copy", "yield", 0.5)
    assert be_y.cer_before == 0.3 and be_y.cer_at == 0.5
    assert abs(be_y.cer_interpolated - 0.4) < 1e-9
    be_p = T.break_even(levels, "fair_copy", "precision", 0.95)
    assert be_p.cer_before == 0.3 and be_p.cer_at == 0.5
    assert 0.3 < be_p.cer_interpolated < 0.5
    held = T.break_even(levels[:2], "fair_copy", "yield", 0.5)
    assert held.cer_at is None and "holds through" in held.describe()
    gone = T.break_even(levels, "fair_copy", "yield", 0.95)
    assert gone.cer_before is None and "already under" in gone.describe()


def test_run_tolerance_and_reports(tmp_path: Path) -> None:
    lines = _synthetic_lines(50)
    res = T.run_tolerance(
        lines,
        levels=(0.2, 0.5),
        lines_per_piece=10,
        thresholds={"fair_copy": 0.55, "scrap": 0.80},
        source="fixture",
    )
    assert [lv.label for lv in res.levels] == ["base", "cer20", "cer50"]
    cers = [lv.cer_written for lv in res.levels]
    assert cers == sorted(cers)
    assert {be.metric for be in res.break_evens} == {"yield", "precision"}
    assert len(res.break_evens) == 4
    md, js = T.write_reports(res, tmp_path)
    text = md.read_text(encoding="utf-8")
    assert "# Aligner noise tolerance" in text
    assert "## Break-even" in text and "scrap (0.80)" in text
    assert "None" not in text
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data["n_lines"] == 50 and len(data["levels"]) == 3
    assert data["model"]["merges"]["in"] == "m"
    assert data["levels"][1]["target_cer"] == 0.2


def test_cli_kurrent_tolerance(tmp_path: Path) -> None:
    lines = _synthetic_lines(30)
    src = tmp_path / "lines.jsonl"
    src.write_text(
        "\n".join(
            json.dumps({"line_id": ln.line_id, "ref": ln.ref, "hyp": ln.hyp}) for ln in lines
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "align",
            "kurrent-tolerance",
            "--lines",
            str(src),
            "--levels",
            "30",
            "--lines-per-piece",
            "10",
            "--workers",
            "1",
            "--out-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "cer30" in result.output and "break-even" in result.output
    assert (out_dir / "align-tolerance.md").exists()
    assert (out_dir / "align-tolerance.json").exists()
