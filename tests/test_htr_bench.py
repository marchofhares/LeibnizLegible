"""Tests for the harness orchestration (offline, via EchoEngine)."""

from __future__ import annotations

import json

import pytest

from leibniz.htr import bench, metrics
from leibniz.htr.bench import EchoEngine, LinePair


def _pairs() -> list[LinePair]:
    return [
        LinePair(line_id="a", reference="hello world", image_bytes_=b"IMG_A"),
        LinePair(line_id="b", reference="foo bar baz", image_bytes_=b"IMG_B"),
        LinePair(line_id="c", reference="lorem ipsum", image_bytes_=b"IMG_C"),
    ]


def test_linepair_image_bytes_from_bytes_and_path(tmp_path) -> None:
    p = LinePair(line_id="x", reference="r", image_bytes_=b"DATA")
    assert p.image_bytes() == b"DATA"
    f = tmp_path / "l.png"
    f.write_bytes(b"ONDISK")
    p2 = LinePair(line_id="y", reference="r", image_path=f)
    assert p2.image_bytes() == b"ONDISK"
    with pytest.raises(ValueError):
        LinePair(line_id="z", reference="r").image_bytes()


def test_evaluate_perfect_score() -> None:
    pairs = _pairs()
    mapping = {p.image_bytes_: p.reference for p in pairs}
    result = bench.evaluate(pairs, EchoEngine(mapping), n_resamples=50)
    assert result.n_lines == 3
    assert result.cer.point == 0.0
    assert result.wer.point == 0.0
    assert result.engine == "echo"


def test_evaluate_known_errors() -> None:
    pairs = _pairs()
    # Engine returns empty for every line -> every reference char is a deletion.
    result = bench.evaluate(pairs, EchoEngine(default=""), n_resamples=50)
    assert result.cer.point == 1.0  # all reference characters missing


def test_transcribe_once_score_many_policies() -> None:
    pairs = [LinePair(line_id="a", reference="Café", image_bytes_=b"IMG")]
    eng = EchoEngine({b"IMG": "cafe"})  # lowercased + no accent
    hyps, _secs = bench.transcribe_pairs(pairs, eng)
    strict = bench.score_hypotheses(
        pairs, hyps, engine_name="e", engine_version="0", policy=metrics.STRICT_POLICY
    )
    lenient = bench.score_hypotheses(
        pairs, hyps, engine_name="e", engine_version="0", policy=metrics.LENIENT_POLICY
    )
    assert strict.cer.point > 0.0  # case + diacritic differences count
    assert lenient.cer.point == 0.0  # folded away


def test_evaluate_length_mismatch_raises() -> None:
    class BadEngine:
        name = "bad"
        version = "0"

        def transcribe(self, images):
            return ["only one"]  # wrong count

    with pytest.raises(ValueError):
        bench.evaluate(_pairs(), BadEngine())


def test_batch_size_chunks_calls() -> None:
    class CountingEngine:
        name = "count"
        version = "0"

        def __init__(self):
            self.batches = 0

        def transcribe(self, images):
            self.batches += 1
            return ["" for _ in images]

    eng = CountingEngine()
    bench.evaluate(_pairs(), eng, batch_size=2)  # 3 lines / 2 => 2 batches
    assert eng.batches == 2


def test_worst_and_language_breakdown() -> None:
    pairs = [
        LinePair(line_id="a", reference="perfect", image_bytes_=b"A", lang="la"),
        LinePair(line_id="b", reference="wrongish", image_bytes_=b"B", lang="fr"),
    ]
    eng = EchoEngine({b"A": "perfect", b"B": "zzzzzzzz"})
    result = bench.evaluate(pairs, eng, n_resamples=20)
    worst = result.worst(1)
    assert worst[0].line_id == "b"  # the wrong one ranks first
    langs = {b.lang: b for b in result.by_language}
    assert set(langs) == {"la", "fr"}
    assert langs["la"].cer == 0.0
    assert langs["fr"].cer > 0.0


def test_dump_lines_jsonl_and_result_to_dict(tmp_path) -> None:
    pairs = _pairs()
    result = bench.evaluate(pairs, EchoEngine(default=""), n_resamples=20)
    out = tmp_path / "dump.jsonl"
    bench.dump_lines_jsonl(result, out)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    assert set(rows[0]) >= {"line_id", "ref", "hyp", "char_edits", "cer"}

    d = bench.result_to_dict(result)
    assert d["n_lines"] == 3
    assert d["policy"]["name"] == "philiumm"
    assert "cer" in d and "point" in d["cer"]


def test_protocol_frozen_fields() -> None:
    assert bench.PROTOCOL["version"] == bench.PROTOCOL_VERSION
    assert "micro" in bench.PROTOCOL["aggregation"]
    assert bench.PROTOCOL["default_policy"] == "philiumm"


def test_summary_string() -> None:
    result = bench.evaluate(_pairs(), EchoEngine(default=""), n_resamples=20)
    s = result.summary()
    assert "echo@0" in s and "CER" in s and "WER" in s
