"""Tests for the `leibniz bench` CLI (offline, via typer's runner)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from leibniz.htr import bench
from leibniz.htr import cli as bench_cli
from leibniz.htr.bench import EchoEngine

runner = CliRunner()


def test_protocol_command() -> None:
    result = runner.invoke(bench_cli.app, ["protocol"])
    assert result.exit_code == 0
    assert bench.PROTOCOL_VERSION in result.stdout
    assert "philiumm" in result.stdout


def test_repro_guards_missing_artifacts(tmp_path) -> None:
    result = runner.invoke(
        bench_cli.app,
        ["repro", "--models", str(tmp_path / "m"), "--gt", str(tmp_path / "g")],
    )
    assert result.exit_code == 1
    assert "Missing artifacts" in result.stdout


def test_fetch_command_monkeypatched(monkeypatch, tmp_path) -> None:
    model = tmp_path / "m" / "model.safetensors"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"WEIGHTS")
    val = tmp_path / "g" / "val.parquet"
    val.parent.mkdir(parents=True)
    val.write_bytes(b"PARQUET")

    monkeypatch.setattr(bench_cli.artifacts, "fetch_model", lambda **kw: model)
    monkeypatch.setattr(bench_cli.artifacts, "fetch_val_split", lambda **kw: val)
    result = runner.invoke(bench_cli.app, ["fetch", "--models", str(model.parent)])
    assert result.exit_code == 0
    assert "model" in result.stdout


def test_run_command_on_dir_with_echo(monkeypatch, tmp_path) -> None:
    d = tmp_path / "lines"
    d.mkdir()
    (d / "a.png").write_bytes(b"IMGA")
    (d / "a.gt.txt").write_text("hello world", encoding="utf-8")
    (d / "b.png").write_bytes(b"IMGB")
    (d / "b.gt.txt").write_text("foo bar", encoding="utf-8")

    # Perfect engine keyed by the fixture bytes.
    mapping = {b"IMGA": "hello world", b"IMGB": "foo bar"}
    monkeypatch.setattr(bench_cli, "_build_engine", lambda name, model: EchoEngine(mapping))

    out = tmp_path / "dump.jsonl"
    result = runner.invoke(bench_cli.app, ["run", str(d), "--out", str(out)])
    assert result.exit_code == 0
    assert "CER 0.00%" in result.stdout
    assert out.exists()
    assert len(out.read_text(encoding="utf-8").splitlines()) == 2


def test_run_command_empty_dir_exits(tmp_path) -> None:
    d = tmp_path / "empty"
    d.mkdir()
    result = runner.invoke(bench_cli.app, ["run", str(d)])
    assert result.exit_code == 1
    assert "No line pairs" in result.stdout


def test_read_dataset_splits_parses_card(tmp_path) -> None:
    card = tmp_path / "DATASET_README.md"
    card.write_text(
        "features:\n"
        "  splits:\n"
        "  - name: train_clean\n    num_bytes: 100\n    num_examples: 18254\n"
        "  - name: val\n    num_bytes: 50\n    num_examples: 1878\n"
        "language:\n- la\n- fr\n",
        encoding="utf-8",
    )
    out = bench_cli._read_dataset_splits(tmp_path)
    assert out["splits"]["val"] == 1878
    assert out["splits"]["train_clean"] == 18254
    assert out["languages"] == ["la", "fr"]


def test_read_dataset_splits_fallback(tmp_path) -> None:
    out = bench_cli._read_dataset_splits(tmp_path)  # no card present
    assert out["splits"] == bench_cli._KNOWN_SPLITS


def test_read_model_meta(tmp_path) -> None:
    (tmp_path / "metadata.json").write_text('{"accuracy": "0.92"}', encoding="utf-8")
    assert bench_cli._read_model_meta(tmp_path)["accuracy"] == "0.92"
    assert bench_cli._read_model_meta(tmp_path / "nope") == {}


def test_build_engine_unknown() -> None:
    import pytest
    import typer

    with pytest.raises(typer.BadParameter):
        bench_cli._build_engine("bogus", Path("x"))


def test_make_llm_engine_unknown() -> None:
    import pytest
    import typer

    with pytest.raises(typer.BadParameter):
        bench_cli._make_llm_engine("bogus", None)


def test_llm_key_present(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert bench_cli._llm_key_present("openai") is False
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    assert bench_cli._llm_key_present("openai") is True
    assert bench_cli._llm_key_present("anthropic") is False  # checks the right var


def test_run_llm_comparison_skips_without_key(monkeypatch) -> None:
    from leibniz.htr.bench import LinePair

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pairs = [LinePair(line_id=str(i), reference="x y", image_bytes_=b"I") for i in range(3)]
    hyps = ["x y", "x y", "x y"]
    results, kraken_sub = bench_cli._run_llm_comparison(
        pairs, hyps, llm_n=3, engine_name="openai", models=["gpt-4o"]
    )
    assert results == []  # no key -> no LLM rows
    assert kraken_sub is not None  # kraken subsample still scored


def test_raw_hyps_cache_roundtrip(tmp_path) -> None:
    from leibniz.htr.bench import LinePair

    pairs = [
        LinePair(line_id="a", reference="r1", image_bytes_=b""),
        LinePair(line_id="b", reference="r2", image_bytes_=b""),
    ]
    cache = tmp_path / "hyps.jsonl"
    bench_cli._dump_raw_hyps(cache, pairs, ["hyp one", "hyp two"])
    assert bench_cli._load_raw_hyps(cache, pairs) == ["hyp one", "hyp two"]

    # Missing cache -> None (triggers fresh inference).
    assert bench_cli._load_raw_hyps(tmp_path / "absent.jsonl", pairs) is None

    # Cache not covering all current pairs -> None (never scores a stale subset).
    more = [*pairs, LinePair(line_id="c", reference="r3", image_bytes_=b"")]
    assert bench_cli._load_raw_hyps(cache, more) is None


def test_resolve_llm_spec_engine_prefixes() -> None:
    # Bare ids ride the default engine.
    assert bench_cli._resolve_llm_spec("openai", "gpt-4o") == ("openai", "gpt-4o")
    assert bench_cli._resolve_llm_spec("anthropic", None) == ("anthropic", None)
    # An engine prefix overrides the default (mixed panels).
    assert bench_cli._resolve_llm_spec("openai", "gemini:gemini-3.8-flash") == (
        "gemini",
        "gemini-3.8-flash",
    )
    assert bench_cli._resolve_llm_spec("gemini", "openai:gpt-5.6-luna") == (
        "openai",
        "gpt-5.6-luna",
    )
    # A bare "engine:" selects that engine's default model.
    assert bench_cli._resolve_llm_spec("openai", "anthropic:") == ("anthropic", None)
    # Unknown prefixes are part of the model id, not an engine.
    assert bench_cli._resolve_llm_spec("openai", "ft:gpt-4o:acme") == ("openai", "ft:gpt-4o:acme")


def test_llm_key_present_gemini(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert not bench_cli._llm_key_present("gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "g")
    assert bench_cli._llm_key_present("gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "g2")
    assert bench_cli._llm_key_present("gemini")
