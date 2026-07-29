"""Tests for the aligner evaluation harness (offline; no models/HTR)."""

from __future__ import annotations

from leibniz.align import evaluate as E


class _Pair:
    """Minimal stand-in for a bench LinePair (no image bytes needed here)."""

    def __init__(self, line_id: str, reference: str) -> None:
        self.line_id = line_id
        self.reference = reference

    def image_bytes(self) -> bytes:
        return b""


def _pairs(n: int) -> list[_Pair]:
    return [_Pair(f"v:{i:03d}", f"gold text of line number {i}") for i in range(n)]


def test_build_pieces_chunks_in_order() -> None:
    pieces = E.build_pieces(_pairs(55), lines_per_piece=25)
    assert [len(p.lines) for p in pieces] == [25, 25, 5]
    assert pieces[0].lines[0].line_id == "v:000"


def test_build_reference_diplomatic_is_concatenation() -> None:
    gold = ["prima linea", "secunda linea", "tertia linea"]
    ref, true_lines, mintable = E.build_reference(gold)
    assert ref == "prima linea secunda linea tertia linea"
    assert true_lines == gold
    assert mintable == [True, True, True]


def test_build_reference_drop_omits_lines() -> None:
    gold = [f"line {i} words here" for i in range(20)]
    ref, true_lines, mintable = E.build_reference(gold, drop_rate=0.5, seed=1)
    n_dropped = mintable.count(False)
    assert 0 < n_dropped < 20
    # dropped lines have empty truth and are absent from the reference text.
    for t, m in zip(true_lines, mintable, strict=True):
        assert (t == "") == (not m)


def test_build_reference_perturb_changes_lines_but_tracks_truth() -> None:
    gold = ["a fairly long line of latin text here"] * 5
    ref, true_lines, mintable = E.build_reference(gold, char_perturb=0.2, seed=3)
    # perturbation altered at least one line; the reference is the join of truth.
    assert any(t != g for t, g in zip(true_lines, gold, strict=True))
    assert ref == " ".join(true_lines)


def test_evaluate_piece_perfect_htr() -> None:
    # If HTR == gold and reference == gold concat, every line aligns correctly.
    golds = ["prima linea textus", "secunda linea textus", "tertia linea textus"]
    piece = E.Piece("p", [E.GoldLine(f"v:{i}", g, b"") for i, g in enumerate(golds)])
    htr = {f"v:{i}": g for i, g in enumerate(golds)}
    cfg = E.EvalConfig(label="clean", threshold=0.5)
    lines = E.evaluate_piece(piece, htr, cfg)
    s = E.summarize(lines, cfg)
    assert s.yield_rate == 1.0
    assert s.precision == 1.0
    assert s.n_false_positive == 0


def test_summarize_counts_false_positives_under_omission() -> None:
    # A dropped line that gets minted is a false positive.
    lines = [
        E.LineEval("a", "x", "x", "x", 0.9, True, 1.0, mintable=True),
        E.LineEval("b", "", "junk", "smeared text", 0.9, False, 0.0, mintable=False),
    ]
    cfg = E.EvalConfig(label="t", threshold=0.5)
    s = E.summarize(lines, cfg)
    assert s.n_aligned == 2
    assert s.n_false_positive == 1
    assert s.precision == 0.5


def test_summarize_threshold_sweep_finds_precision_point() -> None:
    lines = [
        E.LineEval("a", "x", "x", "x", 0.95, True, 1.0),
        E.LineEval("b", "y", "y", "y", 0.90, True, 1.0),
        E.LineEval("c", "z", "z", "wrong", 0.40, False, 0.0),
    ]
    cfg = E.EvalConfig(label="t", threshold=0.5)
    s = E.summarize(lines, cfg, precision_target=0.95)
    # at threshold ≥ 0.5 the wrong low-conf line is excluded → precision 1.0.
    assert s.precision == 1.0
    assert s.yield_at_precision is not None
