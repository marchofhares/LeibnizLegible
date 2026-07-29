"""``leibniz bench`` — the HTR evaluation harness CLI (Phase B1; deliverable D5).

Subcommands:

* ``leibniz bench fetch`` — download & cache the PHILIUMM artifacts (model + val
  split) under ``data/`` (gitignored).
* ``leibniz bench protocol`` — print the frozen evaluation protocol.
* ``leibniz bench run`` — evaluate one engine on one dataset (generic; JSONL +
  JSON out). The reusable harness entry point.
* ``leibniz bench repro`` — the full PHILIUMM reproduction: Kraken on the val
  split under every normalization policy, optional Claude comparison, writing
  ``reports/philiumm-repro.md`` and the STATUS.md gate verdict.

The kraken + torch stack is an optional dependency, imported lazily; ``fetch``,
``protocol`` and the metrics/harness all work without it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich.console import Console

from leibniz import db
from leibniz.htr import artifacts, bench, data, metrics, report
from leibniz.htr.report import ReproReport

app = typer.Typer(
    help="Benchmark harness (B1): fetch artifacts, run engines, reproduce PHILIUMM CER.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

DEFAULT_REPORT = Path("reports/philiumm-repro.md")
DEFAULT_LINES_DUMP = Path("reports/philiumm-repro.lines.jsonl")
# Raw (un-normalized) hypotheses cache: lets the report be re-rendered/re-scored
# under any policy without re-running inference. Under data/ (gitignored).
DEFAULT_HYPS_CACHE = Path("data/bench/philiumm-repro.hyps.jsonl")
# Known dataset splits (fallback if the cached dataset card can't be parsed).
_KNOWN_SPLITS = {"train_clean": 18254, "train_noisy": 43372, "val": 1878}


# --------------------------------------------------------------------------- #
# fetch / protocol
# --------------------------------------------------------------------------- #


@app.command()
def fetch(
    models_dir: Path = typer.Option(artifacts.MODELS_DIR, "--models", help="Model cache dir."),
    gt_dir: Path = typer.Option(artifacts.GT_DIR, "--gt", help="Ground-truth cache dir."),
    skip_val: bool = typer.Option(
        False, "--skip-val", help="Fetch only the model, not the val split."
    ),
) -> None:
    """Download & cache the PHILIUMM model and val split (cache-first, CC BY)."""
    console.print(
        f"[bold]bench fetch[/bold] — {artifacts.LICENSE}; artifacts under {models_dir}, {gt_dir}"
    )
    model_path = artifacts.fetch_model(models_dir=models_dir)
    console.print(f"  model: [green]{model_path}[/green] ({model_path.stat().st_size:,} bytes)")
    if not skip_val:
        console.print("  val split (~300 MB) …")
        val_path = artifacts.fetch_val_split(gt_dir=gt_dir)
        console.print(f"  val:   [green]{val_path}[/green] ({val_path.stat().st_size:,} bytes)")
    console.print("Next: [cyan]leibniz bench repro[/cyan] (needs the kraken+torch stack).")


@app.command()
def protocol() -> None:
    """Print the frozen evaluation protocol (what makes numbers comparable)."""
    console.print(f"[bold]Frozen protocol {bench.PROTOCOL_VERSION}[/bold]")
    for k, v in bench.PROTOCOL.items():
        console.print(f"  [cyan]{k}[/cyan]: {v}")
    console.print("\n[bold]Normalization policies[/bold]")
    for name, pol in metrics.POLICIES.items():
        console.print(f"  [cyan]{name}[/cyan]: {pol.describe()}")


# --------------------------------------------------------------------------- #
# run (generic engine × dataset)
# --------------------------------------------------------------------------- #


@app.command()
def run(
    data_path: Path = typer.Argument(..., help="Parquet (text+image) or a dir of image+.gt.txt."),
    engine: str = typer.Option("kraken", "--engine", "-e", help="kraken | anthropic."),
    model: Path | None = typer.Option(None, "--model", help="Model path (kraken engine)."),
    policy: str = typer.Option("philiumm", "--policy", "-p", help="Normalization policy."),
    limit: int | None = typer.Option(None, "--limit", help="Cap lines evaluated."),
    out: Path | None = typer.Option(None, "--out", help="Write JSONL per-line dump here."),
    batch_size: int = typer.Option(8, "--batch-size", help="Engine batch size."),
) -> None:
    """Evaluate one engine on one dataset and print CER/WER (generic harness)."""
    pairs = _load_pairs(data_path, limit=limit)
    if not pairs:
        console.print(f"[red]No line pairs loaded from {data_path}.[/red]")
        raise typer.Exit(code=1)
    pol = metrics.get_policy(policy)
    eng = _build_engine(engine, model)
    console.print(f"[bold]run[/bold] {eng.name}@{eng.version} on {len(pairs):,} lines [{pol.name}]")
    result = bench.evaluate(pairs, eng, policy=pol, batch_size=batch_size, dataset=str(data_path))
    console.print(result.summary())
    if out is not None:
        bench.dump_lines_jsonl(result, out)
        console.print(f"per-line dump → [green]{out}[/green]")


# --------------------------------------------------------------------------- #
# repro (the gate)
# --------------------------------------------------------------------------- #


@app.command()
def repro(
    models_dir: Path = typer.Option(artifacts.MODELS_DIR, "--models", help="Model cache dir."),
    gt_dir: Path = typer.Option(artifacts.GT_DIR, "--gt", help="Ground-truth cache dir."),
    out: Path = typer.Option(DEFAULT_REPORT, "--out", help="Report markdown path."),
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="SQLite store (run record)."),
    limit: int | None = typer.Option(None, "--limit", help="Cap val lines (dev; default all)."),
    batch_size: int = typer.Option(8, "--batch-size", help="Kraken batch size."),
    with_llm: bool = typer.Option(False, "--with-llm", help="Also run a VLM on a subsample."),
    llm_n: int = typer.Option(150, "--llm-n", help="Subsample size for the LLM comparison."),
    llm_engine: str = typer.Option("anthropic", "--llm-engine", help="anthropic | openai."),
    llm_model: list[str] | None = typer.Option(
        None, "--llm-model", help="VLM model id(s); repeatable for a panel. Default per engine."
    ),
    reuse_hyps: bool = typer.Option(
        False, "--reuse-hyps", help="Skip inference; re-score cached raw hypotheses."
    ),
    model_version: str | None = typer.Option(None, "--model-version", help="Label for the model."),
) -> None:
    """Reproduce the PHILIUMM CER on the val split and write the gate report."""
    paths = artifacts.artifact_paths(models_dir, gt_dir)
    if not reuse_hyps and (not paths.model_present or not paths.val_present):
        console.print(
            "[red]Missing artifacts.[/red] Run [cyan]leibniz bench fetch[/cyan] first "
            f"(model present={paths.model_present}, val present={paths.val_present})."
        )
        raise typer.Exit(code=1)

    model_meta = _read_model_meta(models_dir)
    dataset_splits = _read_dataset_splits(gt_dir)

    console.print(f"[bold]bench repro[/bold] — loading val split from {paths.val_parquet.name}")
    pairs = data.load_parquet_pairs(paths.val_parquet, limit=limit)
    console.print(f"  {len(pairs):,} line pairs")

    version = model_version or artifacts.MODEL_FILE.rsplit(".", 1)[0]
    cached = _load_raw_hyps(DEFAULT_HYPS_CACHE, pairs) if reuse_hyps else None
    if cached is not None:
        hyps, seconds = cached, 0.0
        console.print(f"  [yellow]reusing {len(hyps):,} cached hypotheses[/yellow] (no inference)")
    else:
        engine = _build_engine("kraken", paths.model)
        version = model_version or engine.version
        console.print(f"  transcribing with kraken@{version} (CPU, batch {batch_size}) …")
        hyps, seconds = bench.transcribe_pairs(pairs, engine, batch_size=batch_size)
        console.print(f"  done in {seconds:.0f}s")
        _dump_raw_hyps(DEFAULT_HYPS_CACHE, pairs, hyps)

    kraken_by_policy: dict[str, bench.EvalResult] = {}
    for name in ("philiumm", "lenient", "strict"):
        res = bench.score_hypotheses(
            pairs,
            hyps,
            engine_name="kraken",
            engine_version=version,
            policy=metrics.get_policy(name),
            seconds=seconds,
            dataset=paths.val_parquet.name,
        )
        kraken_by_policy[name] = res
        console.print(f"  [{name}] {res.summary()}")

    llm_results: list = []
    kraken_sub = None
    key_present = _llm_key_present(llm_engine)
    if with_llm:
        llm_results, kraken_sub = _run_llm_comparison(
            pairs, hyps, llm_n=llm_n, engine_name=llm_engine, models=llm_model or None
        )

    rep = ReproReport(
        generated_at=db.utcnow_iso(),
        kraken_by_policy=kraken_by_policy,
        model_meta=model_meta,
        dataset_splits=dataset_splits,
        n_val=len(pairs),
        llm_results=llm_results,
        kraken_on_subsample=kraken_sub,
        subsample_n=llm_n if llm_results else 0,
        key_present=key_present,
    )
    markdown = report.render_repro_report(rep)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    bench.dump_lines_jsonl(kraken_by_policy["philiumm"], DEFAULT_LINES_DUMP)

    _record_run(db_path, version, kraken_by_policy["philiumm"])

    primary = kraken_by_policy["philiumm"]
    reproduced, verdict = report.gate_verdict(primary.cer.point * 100)
    console.print(f"\n[bold]{'✅' if reproduced else '⚠️'} {verdict}[/bold]")
    console.print(f"report → [green]{out}[/green] · per-line → [green]{DEFAULT_LINES_DUMP}[/green]")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _load_pairs(path: Path, *, limit: int | None) -> list[data.LinePair]:
    path = Path(path)
    if path.is_dir():
        return data.load_image_text_dir(path, limit=limit)
    return data.load_parquet_pairs(path, limit=limit)


def _dump_raw_hyps(path: Path, pairs, hyps: list[str]) -> None:
    """Cache raw (un-normalized) hypotheses keyed by line id, for re-scoring."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for p, h in zip(pairs, hyps, strict=True):
            fh.write(json.dumps({"line_id": p.line_id, "hyp": h}, ensure_ascii=False) + "\n")


def _load_raw_hyps(path: Path, pairs) -> list[str] | None:
    """Load cached raw hypotheses aligned to ``pairs`` by line id, or None.

    Returns None (triggering fresh inference) if the cache is absent or does not
    cover exactly the current pair set — never silently scores a stale subset.
    """
    path = Path(path)
    if not path.exists():
        return None
    by_id: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            by_id[row["line_id"]] = row["hyp"]
    if not all(p.line_id in by_id for p in pairs):
        return None
    return [by_id[p.line_id] for p in pairs]


def _build_engine(name: str, model: Path | None):
    if name == "kraken":
        from leibniz.htr.engines import KrakenEngine

        if model is None:
            model = artifacts.artifact_paths().model
        return KrakenEngine(str(model))
    if name == "anthropic":
        from leibniz.htr.engines import AnthropicEngine

        return AnthropicEngine()
    if name == "openai":
        from leibniz.htr.engines import OpenAIEngine

        return OpenAIEngine()
    raise typer.BadParameter(f"unknown engine {name!r} (kraken | anthropic | openai)")


def _make_llm_engine(engine_name: str, model: str | None):
    """Construct a VLM engine (anthropic|openai), optionally for a specific model."""
    if engine_name == "anthropic":
        from leibniz.htr.engines import AnthropicEngine

        return AnthropicEngine(model=model) if model else AnthropicEngine()
    if engine_name == "openai":
        from leibniz.htr.engines import OpenAIEngine

        return OpenAIEngine(model=model) if model else OpenAIEngine()
    raise typer.BadParameter(f"unknown --llm-engine {engine_name!r} (anthropic | openai)")


def _run_llm_comparison(pairs, hyps, *, llm_n: int, engine_name: str, models: list[str] | None):
    """Run one or more VLMs on a seeded subsample; score them + kraken on the same lines.

    Returns ``(list[LLMComparison], kraken_subsample_result)``. Each model is a
    row; token usage/cost is captured from the engine where available. A missing
    key or a per-model failure is logged and skipped, never fatal.
    """
    from leibniz.htr.engines import MissingKeyError
    from leibniz.htr.report import LLMComparison

    subset = data.subsample(pairs, llm_n)
    idx = {p.line_id: i for i, p in enumerate(pairs)}
    sub_hyps_kraken = [hyps[idx[p.line_id]] for p in subset]
    kraken_sub = bench.score_hypotheses(
        subset,
        sub_hyps_kraken,
        engine_name="kraken",
        engine_version="philiumm",
        policy=metrics.PHILIUMM_POLICY,
        dataset="val-subsample",
    )

    results: list = []
    for model in models or [None]:
        try:
            eng = _make_llm_engine(engine_name, model)
        except MissingKeyError as exc:
            console.print(f"  [yellow]LLM comparison skipped: {exc}[/yellow]")
            break  # no key ⇒ none of the models will run
        try:
            with eng:
                console.print(f"  {engine_name} ({eng.version}) on {len(subset)} lines …")
                llm_hyps, secs = bench.transcribe_pairs(subset, eng)
            res = bench.score_hypotheses(
                subset,
                llm_hyps,
                engine_name=engine_name,
                engine_version=eng.version,
                policy=metrics.PHILIUMM_POLICY,
                seconds=secs,
                dataset="val-subsample",
            )
            results.append(
                LLMComparison(
                    result=res,
                    input_tokens=getattr(eng, "usage_input", 0),
                    output_tokens=getattr(eng, "usage_output", 0),
                    cost_usd=getattr(eng, "cost", None),
                )
            )
            console.print(f"    → {res.summary()}")
        except Exception as exc:  # noqa: BLE001 — one bad model can't sink the panel
            console.print(f"  [red]{engine_name}:{model or 'default'} failed: {exc}[/red]")
    return results, kraken_sub


def _llm_key_present(engine_name: str) -> bool:
    import os

    var = "OPENAI_API_KEY" if engine_name == "openai" else "ANTHROPIC_API_KEY"
    return bool(os.environ.get(var))


def _read_model_meta(models_dir: Path) -> dict:
    meta_path = Path(models_dir) / "metadata.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _read_dataset_splits(gt_dir: Path) -> dict:
    """Parse split sizes from the cached dataset card, falling back to knowns."""
    readme = Path(gt_dir) / "DATASET_README.md"
    splits: dict[str, int] = {}
    langs: list[str] = []
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for name, num in re.findall(
            r"name:\s*(\w+)\s*\n\s*num_bytes:.*?\n\s*num_examples:\s*(\d+)", text
        ):
            splits[name] = int(num)
        m = re.search(r"language:\s*\n((?:\s*-\s*\w+\s*\n)+)", text)
        if m:
            langs = re.findall(r"-\s*(\w+)", m.group(1))
    return {"splits": splits or _KNOWN_SPLITS, "languages": langs or ["la", "fr"]}


def _record_run(db_path: Path, model_version: str, result: bench.EvalResult) -> None:
    conn = db.init_db(db_path)
    run_id = db.start_run(
        conn,
        "bench_repro",
        model=f"kraken@{model_version}",
        params={
            "protocol": bench.PROTOCOL_VERSION,
            "policy": result.policy.name,
            "cer": result.cer.point,
            "wer": result.wer.point,
            "dataset": result.dataset,
        },
        git_sha=db.git_sha(),
    )
    db.finish_run(conn, run_id, n_input=result.n_lines, n_ok=result.n_lines, n_failed=0)
    conn.close()


__all__ = ["app"]
