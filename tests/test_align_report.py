"""Tests for the B2 report renderer (offline; pure)."""

from __future__ import annotations

from leibniz.align.evaluate import EvalSummary
from leibniz.align.report import (
    ReportData,
    compute_verdict,
    render_eval_table,
    render_report,
)


def _summary(label: str, yield_rate: float, precision: float, drop: float = 0.0) -> EvalSummary:
    return EvalSummary(
        label=label,
        n_lines=400,
        n_mintable=400,
        n_aligned=int(400 * yield_rate),
        n_correct_aligned=int(400 * yield_rate * precision),
        n_false_positive=0,
        threshold=0.6,
        ref_char_perturb=0.0,
        ref_drop_rate=drop,
        yield_rate=yield_rate,
        precision=precision,
        best_threshold_at_precision=0.6,
        yield_at_precision=yield_rate,
    )


def test_compute_verdict_passes_on_favorable() -> None:
    conds = [_summary("dip", 0.98, 0.975), _summary("omit", 0.5, 0.5, drop=0.15)]
    passed, detail = compute_verdict(conds)
    # the omission (drop>0) condition is excluded from the gate; favorable passes.
    assert passed is True
    assert "wide margin" in detail


def test_compute_verdict_fails_below_bar() -> None:
    conds = [_summary("weak", 0.4, 0.80)]
    passed, _ = compute_verdict(conds)
    assert passed is False


def test_render_eval_table_has_all_rows() -> None:
    conds = [_summary("a", 0.98, 0.97), _summary("b", 0.84, 0.92, drop=0.15)]
    table = render_eval_table(conds)
    assert table.count("\n") == 3  # header + separator + 2 rows
    assert "97.0%" in table and "84.0%" in table


def test_render_report_smoke() -> None:
    data = ReportData(
        generated_at="2026-07-29",
        policy_name="align-default",
        threshold=0.6,
        precision_target=0.95,
        n_pieces=16,
        lines_per_piece=25,
        htr_model="M",
        seg_model="S",
        conditions=[_summary("diplomatic", 0.988, 0.975)],
        component_proofs={"seg": "44 lines on a real page"},
        verdict="GO",
        verdict_detail="build C2.",
        extraction_note="ran live.",
    )
    md = render_report(data)
    assert "# Retro-alignment prototype" in md
    assert "GO — green-light C2" in md
    assert "44 lines on a real page" in md
    assert "## 5. Gate verdict" in md
