"""Tests for the repro-report renderer and gate verdict (offline)."""

from __future__ import annotations

from leibniz.htr import bench, metrics, report
from leibniz.htr.bench import EchoEngine, LinePair
from leibniz.htr.report import ReproReport


def _kraken_by_policy(pairs, mapping):
    eng = EchoEngine(mapping)
    hyps, _ = bench.transcribe_pairs(pairs, eng)
    return {
        name: bench.score_hypotheses(
            pairs,
            hyps,
            engine_name="kraken",
            engine_version="philiumm",
            policy=metrics.get_policy(name),
            n_resamples=20,
        )
        for name in ("philiumm", "lenient", "strict")
    }


# -- gate verdict ----------------------------------------------------------- #


def test_gate_verdict_reproduced_within_tolerance() -> None:
    ok, text = report.gate_verdict(8.5)  # claimed 8.33, within 1 point
    assert ok and "REPRODUCED" in text


def test_gate_verdict_better_when_lower() -> None:
    ok, text = report.gate_verdict(5.0)
    assert ok and "better" in text.lower()


def test_gate_verdict_not_reproduced_when_far_worse() -> None:
    ok, text = report.gate_verdict(15.0)
    assert not ok and "NOT REPRODUCED" in text


# -- render ----------------------------------------------------------------- #


def test_render_report_no_language_labels_branch() -> None:
    pairs = [
        LinePair(line_id="a", reference="hello world", image_bytes_=b"A"),
        LinePair(line_id="b", reference="lorem ipsum", image_bytes_=b"B"),
    ]
    kbp = _kraken_by_policy(pairs, {b"A": "hello world", b"B": "lorem ipsum"})
    rep = ReproReport(
        generated_at="2026-07-29T00:00:00Z",
        kraken_by_policy=kbp,
        model_meta={"accuracy": "0.9205", "graphemes": list("abc"), "script": ["Latn"]},
        dataset_splits={"splits": {"val": 1878}, "languages": ["la", "fr"]},
        n_val=2,
    )
    md = report.render_repro_report(rep)
    assert "PHILIUMM reproduction" in md
    assert "Gate verdict" in md
    assert "no per-line language labels" in md  # honest branch
    assert "7.95%" in md  # 1 - 0.9205 self-consistency note
    assert bench.PROTOCOL_VERSION in md
    assert "character-perfect" in md


def test_render_report_with_language_and_llm() -> None:
    pairs = [
        LinePair(line_id="a", reference="alpha beta", image_bytes_=b"A", lang="la"),
        LinePair(line_id="b", reference="gamma delta", image_bytes_=b"B", lang="fr"),
    ]
    kbp = _kraken_by_policy(pairs, {b"A": "alpha beta", b"B": "gXmma delta"})
    llm = bench.evaluate(pairs, EchoEngine({b"A": "alpha", b"B": "gamma delta"}), n_resamples=20)
    llm.engine = "anthropic"
    kraken_sub = kbp["philiumm"]
    rep = ReproReport(
        generated_at="t",
        kraken_by_policy=kbp,
        n_val=2,
        anthropic=llm,
        kraken_on_subsample=kraken_sub,
        subsample_n=2,
        key_present=True,
    )
    md = report.render_repro_report(rep)
    assert "Per-language breakdown" in md
    assert "| la |" in md and "| fr |" in md
    assert "Frontier-LLM comparison" in md
    assert "zero-shot" in md.lower()


def test_render_report_llm_not_run_branch() -> None:
    pairs = [LinePair(line_id="a", reference="x y", image_bytes_=b"A")]
    kbp = _kraken_by_policy(pairs, {b"A": "x y"})
    rep = ReproReport(generated_at="t", kraken_by_policy=kbp, n_val=1, key_present=False)
    md = report.render_repro_report(rep)
    assert "Not run" in md and "ANTHROPIC_API_KEY" in md
