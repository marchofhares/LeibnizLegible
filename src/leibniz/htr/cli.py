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
* ``leibniz bench kurrent-smoke`` — the Kurrent bootstrap readers ranked on the
  Dresden lines of the Kurrent Trace package (K1 Task 3).
* ``leibniz bench train-set`` — the training set of a fine-tune (K3; C3 reuses
  it): the minted lines selected, tagged, screened, split into a frozen
  page-disjoint validation set and training, and cut into Kraken's
  image + ``.gt.txt`` format (``htr/trainset.py``).
* ``leibniz bench train-trocr`` — fine-tune a TrOCR checkpoint on it: the
  timing pilot over the memory settings (``--pilot``), or the staged,
  resumable training with checkpoints chosen on the validation set
  (``htr/train_trocr.py``).
* ``leibniz bench train-kraken`` — the same for a kraken model through
  ``ketos train`` (``htr/train_kraken.py``): the command printed and started
  in the background, its checkpoints read back, the best weights scored
  with the project's metric.

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
    llm_engine: str = typer.Option(
        "anthropic",
        "--llm-engine",
        help="anthropic | openai | gemini — the default engine for --llm-model entries.",
    ),
    llm_model: list[str] | None = typer.Option(
        None,
        "--llm-model",
        help="VLM model id(s); repeatable for a panel; 'engine:model' mixes engines.",
    ),
    llm_max_tokens: int = typer.Option(
        256,
        "--llm-max-tokens",
        help="VLM completion cap. Thinking models (gpt-5.x, gemini-3.x) spend "
        "reasoning tokens inside it — raise it or their answers truncate.",
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
    panel_engines = {_resolve_llm_spec(llm_engine, m)[0] for m in llm_model or [None]}
    key_present = any(_llm_key_present(e) for e in panel_engines)
    if with_llm:
        llm_results, kraken_sub = _run_llm_comparison(
            pairs,
            hyps,
            llm_n=llm_n,
            engine_name=llm_engine,
            models=llm_model or None,
            max_tokens=llm_max_tokens,
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


# --------------------------------------------------------------------------- #
# kurrent-smoke (K1 Task 3): the bootstrap readers ranked on Dresden
# --------------------------------------------------------------------------- #


@app.command("kurrent-smoke")
def kurrent_smoke(
    package: Path = typer.Option(
        None, "--package", help="The Kurrent Trace package directory (default: data/external/…)."
    ),
    candidates: str = typer.Option(
        None, "--candidates", help="Comma-separated candidate keys (default: every default one)."
    ),
    device: str = typer.Option("auto", "--device", help="auto | cpu | cuda | cuda:N."),
    batch_size: int = typer.Option(8, "--batch-size", help="Lines per model call."),
    limit: int | None = typer.Option(None, "--limit", help="Cap the Dresden lines (dev)."),
    force: bool = typer.Option(False, "--force", help="Read again even where readings are cached."),
    vision: bool = typer.Option(
        True, "--vision/--no-vision", help="Add the zero-shot vision row when a key is set."
    ),
    vision_n: int = typer.Option(150, "--vision-n", help="Subsample for the vision row."),
    smoke_dir: Path = typer.Option(None, "--smoke-dir", help="Where raw readings are cached."),
    reports_dir: Path = typer.Option(None, "--reports-dir", help="Where the two reports go."),
    dtype: str = typer.Option(
        None,
        "--dtype",
        help="TrOCR readers: float32 (the default) or float16 (K2's throughput check; use a "
        "--smoke-dir of its own, the cache is keyed by reader).",
    ),
    kv_cache: bool = typer.Option(
        False,
        "--kv-cache",
        help="TrOCR readers: turn the decoder's key/value cache on (the checkpoints' generation "
        "config switches it off); K2's throughput check.",
    ),
) -> None:
    """Read the Dresden Kurrent lines with every candidate reader and rank them (K1 Task 3)."""
    from leibniz.htr import kurrent as K

    if dtype not in (None, "float32", "float16"):
        raise typer.BadParameter("--dtype must be float32 or float16")
    pkg = package or K.DEFAULT_PACKAGE
    smoke = smoke_dir or K.DEFAULT_SMOKE_DIR
    reports = reports_dir or K.DEFAULT_REPORTS_DIR
    keys = (
        [k.strip() for k in candidates.split(",") if k.strip()]
        if candidates
        else [k for k, c in K.CANDIDATES.items() if c.default]
    )
    unknown = [k for k in keys if k not in K.CANDIDATES]
    if unknown:
        raise typer.BadParameter(f"unknown candidates {unknown}; known: {sorted(K.CANDIDATES)}")
    pairs = K.load_dresden(pkg, limit=limit)
    dev = K.pick_device(device)
    console.print(
        f"[bold]kurrent-smoke[/bold] {len(pairs):,} Dresden lines from {pkg}; candidates "
        f"{', '.join(keys)}; device {dev}"
    )
    factory = None
    if dtype or kv_cache:
        factory = lambda c: K.build_engine(  # noqa: E731 — a one-line closure over the knobs
            c, device=dev, batch_size=batch_size, dtype=dtype, use_cache=True if kv_cache else None
        )
        console.print(
            f"  TrOCR settings: dtype {dtype or 'float32'}, "
            f"kv cache {'on' if kv_cache else 'default'}"
        )
    res = K.run_smoke(
        pairs,
        [K.CANDIDATES[k] for k in keys],
        device=dev,
        batch_size=batch_size,
        smoke_dir=smoke,
        package_dir=pkg,
        force=force,
        vision=vision,
        vision_n=vision_n,
        engine_factory=factory,
        log=lambda msg: console.print(f"  {msg}"),
    )
    for r in sorted(res.results, key=lambda r: r.scores.get("philiumm", {}).get("cer", 9.0)):
        if r.status != "ok":
            console.print(f"  [yellow]{r.key}[/yellow]: {r.status}")
            continue
        sc = r.scores["philiumm"]
        console.print(
            f"  [bold]{r.key}[/bold]: CER {sc['cer']:.1%} ({sc['cer_lo']:.1%}–{sc['cer_hi']:.1%}) "
            f"· lenient {r.scores['lenient']['cer']:.1%} · strict {r.scores['strict']['cer']:.1%} "
            f"· package reading {r.package['reading_long_s_and_whitespace']['cer']:.1%} "
            f"· {r.ms_per_line:.0f} ms/line on {r.device}{' (cached)' if r.cached else ''}"
        )
    if res.vision is not None and res.vision.status == "ok":
        v = res.vision
        console.print(
            f"  [bold]{v.key}[/bold]: CER {v.scores['philiumm']['cer']:.1%} on {v.n_lines} lines"
        )
    md, js = K.write_reports(res, reports)
    console.print(f"wrote {md} and {js}")


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


_LLM_ENGINES = ("anthropic", "openai", "gemini")


def _resolve_llm_spec(default_engine: str, spec: str | None) -> tuple[str, str | None]:
    """Split an optional ``engine:`` prefix off a ``--llm-model`` value.

    ``"gemini:gemini-3.8-flash"`` → ``("gemini", "gemini-3.8-flash")``; a bare id
    (or an unknown prefix — model ids never collide with the engine names) rides
    the default engine.
    """
    if spec:
        prefix, sep, rest = spec.partition(":")
        if sep and prefix in _LLM_ENGINES:
            return prefix, rest or None
    return default_engine, spec


def _make_llm_engine(engine_name: str, model: str | None, *, max_tokens: int | None = None):
    """Construct a VLM engine (anthropic|openai|gemini), optionally for a specific model."""
    kwargs: dict = {}
    if model:
        kwargs["model"] = model
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if engine_name == "anthropic":
        from leibniz.htr.engines import AnthropicEngine

        return AnthropicEngine(**kwargs)
    if engine_name == "openai":
        from leibniz.htr.engines import OpenAIEngine

        return OpenAIEngine(**kwargs)
    if engine_name == "gemini":
        from leibniz.htr.engines import GeminiEngine

        return GeminiEngine(**kwargs)
    raise typer.BadParameter(f"unknown --llm-engine {engine_name!r} (anthropic | openai | gemini)")


def _run_llm_comparison(
    pairs,
    hyps,
    *,
    llm_n: int,
    engine_name: str,
    models: list[str] | None,
    max_tokens: int | None = None,
):
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
    warned: set[str] = set()
    for spec in models or [None]:
        eng_name, model = _resolve_llm_spec(engine_name, spec)
        try:
            eng = _make_llm_engine(eng_name, model, max_tokens=max_tokens)
        except MissingKeyError as exc:
            if eng_name not in warned:
                warned.add(eng_name)
                console.print(f"  [yellow]{eng_name} comparison skipped: {exc}[/yellow]")
            continue
        try:
            with eng:
                console.print(f"  {eng_name} ({eng.version}) on {len(subset)} lines …")
                llm_hyps, secs = bench.transcribe_pairs(subset, eng)
            res = bench.score_hypotheses(
                subset,
                llm_hyps,
                engine_name=eng_name,
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
            console.print(f"  [red]{eng_name}:{model or 'default'} failed: {exc}[/red]")
    return results, kraken_sub


def _llm_key_present(engine_name: str) -> bool:
    import os

    if engine_name == "gemini":
        return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
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


# --------------------------------------------------------------------------- #
# train-set (K3 Task 1; C3 reuses it)
# --------------------------------------------------------------------------- #


@app.command("train-set")
def train_set(
    db_path: str = typer.Option(
        "data/inventory.sqlite", "--db", help="SQLite store (opened read-only)."
    ),
    records: Path | None = typer.Option(
        None,
        "--records",
        help="JSONL or CSV naming the records whose rows are taken (``record_id`` per row); "
        "default: the K1 census's German pieces. ``--all`` takes every open-bucket row.",
    ),
    take_all: bool = typer.Option(False, "--all", help="Every open-bucket row (C3)."),
    name: str = typer.Option("k3", "--name", help="The set's name (reports and the output dir)."),
    out: Path | None = typer.Option(None, "--out", help="Output root; default data/train/<name>."),
    images: Path = typer.Option(
        Path("/mnt/d/leibniz-images"), "--images", help="The page-image cache root."
    ),
    readings: list[str] = typer.Option(
        None,
        "--readings",
        help="``reader=path`` of a reader's JSONL, for the screen's ratio on its rows "
        "(repeatable); default: K2's trocr-kurrent-xvi-xvii readings.",
    ),
    flags: Path = typer.Option(
        Path("data/gt/flags.jsonl"), "--flags", help="The reach census's flags (v1 rows)."
    ),
    heldout: Path = typer.Option(
        Path("reports/philiumm/heldout_pages.csv"), "--heldout", help="PHILIUMM's held-out pages."
    ),
    pool: Path = typer.Option(
        Path("reports/kurrent/letterpool-testset.csv"), "--pool", help="The letter pool's set."
    ),
    audit: list[Path] = typer.Option(
        None,
        "--audit",
        help="CSV of judged lines (a ``ref`` column) kept out of training (repeatable); "
        "default: K2's audit sheet and the PHILIUMM verdicts.",
    ),
    val_pieces: Path | None = typer.Option(
        None,
        "--val-pieces",
        help="The frozen validation pieces (reused when present); default "
        "reports/kurrent/<name>-val-pieces.csv.",
    ),
    redraw: bool = typer.Option(False, "--redraw", help="Ignore a frozen validation file."),
    val_share: float = typer.Option(0.05, "--val-share", help="Validation share of the lines."),
    seed: int = typer.Option(20261021, "--seed", help="The draw's seed."),
    sample: int | None = typer.Option(
        None,
        "--sample",
        help="Cut only a seeded sample of N lines into <out>/sample/ and project the disk; "
        "the validation pieces are drawn and frozen, no manifest is written.",
    ),
    no_crops: bool = typer.Option(False, "--no-crops", help="Manifest and report only."),
    workers: int = typer.Option(0, "--workers", help="Process workers for the crops (0: inline)."),
    reports_dir: Path = typer.Option(
        Path("reports/kurrent"), "--reports-dir", help="Where the report and the JSON go."
    ),
) -> None:
    """Build the training set of a fine-tune from the minted lines (K3 Task 1)."""
    from leibniz.align.audit_reach import open_readonly
    from leibniz.htr import trainset as T

    out_root = out or Path("data/train") / name
    rec_ids = None if take_all else T.read_record_ids(records or T.DEFAULT_RECORDS)
    specs = readings or [f"trocr-kurrent-xvi-xvii={T.DEFAULT_READINGS}"]
    reader_texts: dict[str, dict[str, str]] = {}
    for spec in specs:
        key, _, path = spec.partition("=")
        if not path:
            raise typer.BadParameter(f"--readings wants reader=path, got {spec!r}")
        reader_texts[key.strip()] = T.load_readings_text(path.strip())
    vp = val_pieces or reports_dir / f"{name}-val-pieces.csv"
    conn = open_readonly(db_path)
    try:
        ts = T.build(
            conn,
            record_ids=rec_ids,
            readings=reader_texts,
            flags=T.load_flags(flags),
            heldout=T.pages_from_csv(heldout),
            pool=T.pages_from_csv(pool),
            audit=T.refs_from_csvs(audit or T.DEFAULT_AUDITS),
            val_pieces=None if redraw else vp,
            share=val_share,
            seed=seed,
            name=name,
            log=lambda m: console.print(f"  {m}"),
        )
        s = T.summarize(ts)
        console.print(
            f"[bold]train-set[/bold] {s['selection']['rows']:,} rows on "
            f"{s['selection']['records']:,} records; excluded {s['exclusions']['total']:,} "
            f"({', '.join(f'{k} {v:,}' for k, v in s['exclusions']['by_reason'].items())}); "
            f"kept {s['kept']['lines']:,} — train {s['splits']['train']['lines']:,}, "
            f"val {s['splits']['val']['lines']:,} "
            f"({'frozen' if ts.val_frozen else f'drawn, seed {seed}'}); pages on both sides "
            f"{s['pages_shared_between_splits']}"
        )
        b = ts.band
        console.print(
            f"  screen: band ratio {b.ratio_lo:.2f}–{b.ratio_hi:.2f} "
            f"(median {b.ratio_median:.2f}), conf ≥ {b.conf_lo:.3f}, "
            f"from {b.n:,} Latin and French v1 rows"
        )
        for g, v in ts.screen["by_group"].items():
            share = v["outside_share"]
            console.print(
                f"    {g}: {v['n']:,} lines, {v['outside']:,} outside "
                f"({'—' if share is None else f'{100 * share:.1f} %'}): "
                + ", ".join(f"{k} {n:,}" for k, n in v["outside_by"].items())
            )
        if ts.screen["stop"]:
            console.print(
                "  [red]STOP:[/red] more than one Leibniz-hand line in ten falls outside the band"
            )
        if sample:
            ts.estimate = T.estimate_disk(
                conn,
                ts.lines,
                n=sample,
                images_root=images,
                out_root=out_root / "sample",
                seed=seed,
                workers=workers,
            )
            e = ts.estimate
            per = e["bytes_per_line"]
            proj = e["projected_bytes"]
            kb = "—" if per is None else f"{per / 1024:.1f} KB"
            gb = "—" if proj is None else f"{proj / 1e9:.2f} GB"
            console.print(
                f"  sample: {e['cut']:,} of {e['sampled']:,} cut, {kb} a line; projected {gb} "
                f"for {e['kept_lines']:,} lines"
            )
        elif not no_crops:
            jobs = T.crop_jobs(conn, ts.lines, images, out_root)
            console.print(f"  cutting {len(jobs):,} pages into {out_root} ({workers} workers)")
            ts.crops = T.cut_crops(jobs, ts.lines, workers=workers, log=lambda m: console.print(m))
            console.print(f"  crops: {ts.crops['by_status']} · {ts.crops['bytes'] / 1e9:.2f} GB")
    finally:
        conn.close()
    if sample:
        reports_dir.mkdir(parents=True, exist_ok=True)
        s = T.summarize(ts)
        (reports_dir / f"{name}-trainset.md").write_text(T.render_report(s), encoding="utf-8")
        (reports_dir / f"{name}-trainset.json").write_text(
            json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        if not ts.val_frozen:
            T.write_val_pieces(vp, ts.lines)
        console.print(
            f"  wrote {reports_dir / f'{name}-trainset.md'} and the validation pieces {vp}"
        )
        return
    paths = T.write_outputs(ts, out_root=out_root, reports_dir=reports_dir, val_pieces=vp)
    for k, p in paths.items():
        console.print(f"  wrote {k}: {p}")


# --------------------------------------------------------------------------- #
# train-trocr / train-kraken (K3 Tasks 2 and 3)
# --------------------------------------------------------------------------- #


def _record_training_run(
    db_path: str, stage: str, model: str, params: dict, *, n_input: int
) -> int | None:
    """One runs row for a training (the only write K3 makes to the store); ``None``
    when no store is given."""
    if not db_path:
        return None
    conn = db.init_db(db_path)
    try:
        run_id = db.start_run(conn, stage, model=model, params=params, git_sha=db.git_sha())
        conn.commit()
    finally:
        conn.close()
    console.print(f"  runs row {run_id} opened ({stage}, {model})")
    return run_id


def _finish_training_run(db_path: str, run_id: int | None, *, n_input: int, n_ok: int) -> None:
    if not db_path or run_id is None:
        return
    conn = db.init_db(db_path)
    try:
        db.finish_run(conn, run_id, n_input=n_input, n_ok=n_ok, n_failed=0)
        conn.commit()
    finally:
        conn.close()
    console.print(f"  runs row {run_id} finished")


@app.command("train-trocr")
def train_trocr(
    base: str = typer.Option(
        "dh-unibe/trocr-kurrent-XVI-XVII", "--base", help="Hub id or local checkpoint directory."
    ),
    train_root: Path = typer.Option(
        Path("data/train/k3"), "--train-root", help="The training set (train.txt, val.txt)."
    ),
    out: Path = typer.Option(Path("data/models/k3/trocr"), "--out", help="Artefacts root."),
    pilot: bool = typer.Option(False, "--pilot", help="Time the settings on a bounded run."),
    pilot_lines: int = typer.Option(20_000, "--pilot-lines", help="Lines per pilot setting."),
    settings_keys: str = typer.Option(
        None,
        "--settings",
        help="Comma-separated setting keys to run (pilot: default every PILOT_SETTINGS row; "
        "training: one key, default adafactor-b8).",
    ),
    pilot_val: bool = typer.Option(
        True, "--pilot-val/--no-pilot-val", help="Score the validation set after each pilot run."
    ),
    val_limit: int | None = typer.Option(
        None, "--val-limit", help="Score only the first N validation lines (pilot)."
    ),
    epochs: int = typer.Option(6, "--epochs", help="Epochs of the full training."),
    plan_epochs: float = typer.Option(6.0, "--plan-epochs", help="Epochs the pilot projects."),
    batch_size: int | None = typer.Option(None, "--batch-size", help="Override the batch size."),
    lr: float | None = typer.Option(None, "--lr", help="Override the learning rate."),
    accumulate: int | None = typer.Option(None, "--accumulate", help="Gradient accumulation."),
    drop_screen: bool = typer.Option(
        False, "--drop-screen", help="The ablation: leave out the lines the screen flagged."
    ),
    device: str = typer.Option("auto", "--device", help="auto | cpu | cuda | cuda:N."),
    seed: int = typer.Option(20261021, "--seed", help="The epoch order's seed."),
    patience: int = typer.Option(3, "--patience", help="Epochs without gain before stopping."),
    db_path: str = typer.Option(
        "", "--db", help="Store for the runs row of a full training (none by default)."
    ),
    log_path: Path | None = typer.Option(None, "--log", help="Append the loop's lines here."),
    max_mib: int | None = typer.Option(
        4500,
        "--max-mib",
        help="The loop fails a run whose reserved GPU memory passes this (WSL2 spills past the "
        "card into host memory instead of failing; 0 disables).",
    ),
) -> None:
    """Fine-tune a TrOCR checkpoint on the training set (K3 Task 2a pilot / Task 3)."""
    from leibniz.htr import kurrent as K
    from leibniz.htr import train_trocr as T

    dev = K.pick_device(device)
    limit = max_mib or None
    train = T.read_list(train_root / "train.txt")
    val = T.read_list(train_root / "val.txt")
    if drop_screen:
        manifest = _read_manifest_rows(train_root / "manifest.jsonl")
        before = len(train)
        train = T.stage_samples(train, manifest, drop_screen=True)
        console.print(f"  ablation: {before - len(train):,} screened lines left out")
    if val_limit:
        val = val[:val_limit]
    console.print(
        f"[bold]train-trocr[/bold] base {base}; {len(train):,} training lines, {len(val):,} "
        f"validation lines; device {dev}"
    )

    def _log(msg: str) -> None:
        console.print(f"  {msg}")
        if log_path:
            with Path(log_path).open("a", encoding="utf-8") as fh:
                fh.write(msg + "\n")

    def _override(s: T.Settings) -> T.Settings:
        kw = {}
        if batch_size:
            kw["batch_size"] = batch_size
        if lr:
            kw["lr"] = lr
        if accumulate:
            kw["accumulate"] = accumulate
        return T.Settings(**{**s.as_dict_plain(), **kw}) if kw else s

    all_settings = {s.key: s for s in T.PILOT_SETTINGS}
    if pilot:
        keys = (
            [k.strip() for k in settings_keys.split(",") if k.strip()]
            if settings_keys
            else list(all_settings)
        )
        unknown = [k for k in keys if k not in all_settings]
        if unknown:
            raise typer.BadParameter(f"unknown settings {unknown}; known: {sorted(all_settings)}")
        rows = []
        out.mkdir(parents=True, exist_ok=True)
        pilot_path = out / "pilot.json"
        for key in keys:
            s = _override(all_settings[key])
            _log(f"pilot {s.key}: up to {pilot_lines:,} lines")
            row = T.pilot_setting(
                base,
                s,
                train,
                device=dev,
                max_lines=pilot_lines,
                val=val if pilot_val else None,
                log=_log,
                plan_lines=len(train),
                plan_epochs=plan_epochs,
                memory_limit_mib=limit,
            )
            rows.append(row)
            v = row.val or {}
            _log(
                f"pilot {s.key}: {row.status}; {row.lines:,} lines in {row.seconds:.0f} s "
                f"({row.lines_per_s or 0:.2f} lines/s), peak {row.peak_mib} MiB"
                + (f"; val CER {100 * v['cer']:.2f} %" if v.get("cer") is not None else "")
                + (
                    f"; projected {row.projection['days']:.1f} days for {plan_epochs:g} epochs"
                    if row.projection and row.projection.get("days") is not None
                    else ""
                )
            )
            T.write_pilot(
                pilot_path,
                rows,
                {
                    "base": base,
                    "device": dev,
                    "pilot_lines": pilot_lines,
                    "train_lines": len(train),
                    "val_lines": len(val),
                    "plan_epochs": plan_epochs,
                },
            )
        console.print(f"  wrote {pilot_path}")
        return
    key = settings_keys or "adafactor-b8"
    if key not in all_settings:
        raise typer.BadParameter(f"unknown settings {key!r}; known: {sorted(all_settings)}")
    s = _override(all_settings[key])
    params = {
        "base": base,
        "settings": s.as_dict(),
        "epochs": epochs,
        "train_lines": len(train),
        "val_lines": len(val),
        "drop_screen": drop_screen,
        "seed": seed,
    }
    run_id = _record_training_run(
        db_path, "htr_train", f"trocr-k3@{base}", params, n_input=len(train)
    )
    state = T.train(
        base,
        out,
        train_samples=train,
        val_samples=val,
        settings=s,
        device=dev,
        epochs=epochs,
        seed=seed,
        log=_log,
        patience=patience,
        memory_limit_mib=limit,
    )
    _finish_training_run(db_path, run_id, n_input=len(train), n_ok=len(train))
    best = T.choose_best(state.history)
    console.print(
        f"  done: best epoch {best['epoch'] if best else '—'}, val CER {100 * best['cer']:.2f} %"
        if best
        else "  done: no epoch finished"
    )


def _read_manifest_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                rows.append(json.loads(raw))
    return rows


@app.command("train-kraken")
def train_kraken(
    base: Path = typer.Option(
        Path("data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors"),
        "--base",
        help="The kraken weights to start from.",
    ),
    train_root: Path = typer.Option(
        Path("data/train/k3"), "--train-root", help="The training set (train.txt, val.txt)."
    ),
    out: Path = typer.Option(Path("data/models/k3/kraken"), "--out", help="Artefacts root."),
    pilot: bool = typer.Option(False, "--pilot", help="One fixed epoch on a subset of lines."),
    pilot_lines: int = typer.Option(20_000, "--pilot-lines", help="Lines of the pilot subset."),
    epochs: int = typer.Option(-1, "--epochs", help="Fixed epochs; -1 for early stopping."),
    lag: int = typer.Option(5, "--lag", help="Early stopping: evaluations without gain."),
    batch_size: int = typer.Option(16, "--batch-size", help="ketos -B."),
    accumulate: int = typer.Option(
        1, "--accumulate", help="ketos --accumulate-grad-batches (effective batch = -B × this)."
    ),
    lr: float = typer.Option(1e-4, "--lr", help="ketos -r."),
    augment: bool = typer.Option(False, "--augment", help="ketos --augment."),
    freeze_backbone: int = typer.Option(0, "--freeze-backbone", help="ketos --freeze-backbone."),
    precision: str = typer.Option("32-true", "--precision", help="ketos --precision."),
    workers: int = typer.Option(4, "--workers", help="ketos --workers."),
    ketos: str = typer.Option(
        "ketos", "--ketos", help="The ketos executable (a side environment's for PP-OCRv6)."
    ),
    device: str = typer.Option("cuda:0", "--device", help="ketos -d."),
    seed: int = typer.Option(20261021, "--seed", help="ketos -s and the subset's seed."),
    drop_screen: bool = typer.Option(
        False, "--drop-screen", help="The ablation: leave out the lines the screen flagged."
    ),
    start: bool = typer.Option(
        False, "--start", help="Start ketos in the background (else print the command only)."
    ),
    account: bool = typer.Option(
        False, "--account", help="Read a finished run back: checkpoints, best weights, score."
    ),
    score_device: str = typer.Option("auto", "--score-device", help="For --account's scoring."),
    peak_mib: int | None = typer.Option(
        None, "--peak-mib", help="The GPU's peak memory sampled while it ran (for --account)."
    ),
    db_path: str = typer.Option(
        "", "--db", help="Store for the runs row of a started training (none by default)."
    ),
    log_path: Path | None = typer.Option(None, "--log", help="ketos' output file."),
) -> None:
    """Fine-tune the PHILIUMM kraken model on the training set through ketos (K3 2b / 3)."""
    from leibniz.htr import kurrent as KU
    from leibniz.htr import train_kraken as K

    s = K.KetosSettings(
        base=str(base),
        ketos=ketos,
        batch_size=batch_size,
        accumulate=accumulate,
        lr=lr,
        epochs=1 if pilot else epochs,
        quit="fixed" if pilot or epochs > 0 else "early",
        lag=lag,
        augment=augment,
        freeze_backbone=freeze_backbone,
        precision=precision,
        workers=workers,
        device=device,
        seed=seed,
    )
    out.mkdir(parents=True, exist_ok=True)
    train_list = train_root / "train.txt"
    val_list = train_root / "val.txt"
    if drop_screen or pilot:
        lines = [ln for ln in train_list.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if drop_screen:
            manifest = _read_manifest_rows(train_root / "manifest.jsonl")
            screened = {
                str(train_root / r["image"]) for r in manifest if r.get("image") and r.get("screen")
            }
            before = len(lines)
            lines = [ln for ln in lines if ln not in screened]
            console.print(f"  ablation: {before - len(lines):,} screened lines left out")
        sub = out / ("pilot-train.txt" if pilot else "train.txt")
        sub.write_text("".join(ln + "\n" for ln in lines), encoding="utf-8")
        train_list = sub
        if pilot:
            train_list = K.subset_list(sub, out / "pilot-train.txt", n=pilot_lines, seed=seed)
    cmd = K.ketos_command(s, train_list=train_list, val_list=val_list, out_dir=out)
    log_file = log_path or out / "ketos.log"
    if account:
        text = Path(log_file).read_text(encoding="utf-8") if Path(log_file).exists() else ""
        run_info = (
            json.loads((out / "run.json").read_text(encoding="utf-8"))
            if (out / "run.json").exists()
            else {}
        )
        acc = K.account(
            out,
            s,
            cmd,
            text,
            train_list=train_list,
            started=run_info.get("started"),
            peak_mib=peak_mib,
        )
        if acc.best:
            val = K.read_list(val_list)
            dev = KU.pick_device(score_device)
            console.print(f"  scoring {acc.best['weights']} on {len(val):,} lines ({dev})")
            acc.score = K.score_weights(acc.best["weights"], val, device=dev)
            K.install_best(out, out / "best.safetensors")
            (out / "best-val-hyps.json").write_text(
                json.dumps(acc.score["hyps"], ensure_ascii=False, indent=0), encoding="utf-8"
            )
        p = K.write_account(out / "account.json", acc)
        console.print(
            f"  checkpoints {len(acc.checkpoints)}; epoch seconds "
            f"{[round(t) for t in acc.epoch_seconds]}; run seconds "
            f"{'—' if acc.run_seconds is None else round(acc.run_seconds)}; "
            f"{acc.pilot_lines} lines; best {acc.best}; "
            + (f"val CER {100 * acc.score['cer']:.2f} %" if acc.score else "no score")
        )
        console.print(f"  wrote {p}")
        return
    console.print("[bold]train-kraken[/bold] " + " ".join(cmd))
    if not start:
        console.print("  (not started: pass --start to run it in the background)")
        return
    params = {"settings": s.as_dict(), "command": cmd, "pilot": pilot, "drop_screen": drop_screen}
    run_id = _record_training_run(db_path, "htr_train", f"kraken-k3@{base.name}", params, n_input=0)
    import os as _os
    import time as _time

    proc = K.run(cmd, log_path=log_file)
    (out / "run.json").write_text(
        json.dumps(
            {
                "pid": proc.pid,
                "command": cmd,
                "log": str(log_file),
                "run_id": run_id,
                "started": _time.time(),
                # the allocator settings the job inherits (K3 runs with
                # expandable segments against fragmentation on the 6 GB card)
                "env": {k: v for k, v in _os.environ.items() if k.startswith("PYTORCH_CUDA_ALLOC")},
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    console.print(f"  started pid {proc.pid}; log {log_file}; account with --account when done")


@app.command("k3-report")
def k3_report(
    which: str = typer.Argument("pilots", help="pilots (Task 2)."),
    train_root: Path = typer.Option(Path("data/train/k3"), "--train-root"),
    trocr_pilot: Path = typer.Option(Path("data/models/k3/trocr/pilot.json"), "--trocr-pilot"),
    kraken_account: Path = typer.Option(
        Path("data/models/k3/kraken-pilot/account.json"), "--kraken-account"
    ),
    plan_epochs_trocr: float = typer.Option(6.0, "--plan-epochs-trocr"),
    plan_epochs_kraken: int = typer.Option(30, "--plan-epochs-kraken"),
    rented_note: str = typer.Option("", "--rented-note", help="A sentence on renting."),
    reports_dir: Path = typer.Option(Path("reports/kurrent"), "--reports-dir"),
) -> None:
    """Render a K3 report from the artefacts' JSON (numbers only)."""
    from leibniz.htr import k3_report as R

    if which != "pilots":
        raise typer.BadParameter("only 'pilots' is rendered here")
    s = R.build_pilots(
        trocr=R.load_json(trocr_pilot),
        kraken=R.load_json(kraken_account),
        train_lines=R.count_lines(train_root / "train.txt"),
        val_lines=R.count_lines(train_root / "val.txt"),
        plan_epochs_trocr=plan_epochs_trocr,
        plan_epochs_kraken=plan_epochs_kraken,
        rented_note=rented_note,
    )
    paths = R.write_pilots(s, reports_dir)
    console.print(
        f"  fastest TrOCR setting {s['trocr_fastest']}, best CER {s['trocr_best_cer']}; "
        f"kraken {s['kraken'].get('status')}; over a week: {s['over_a_week']}"
    )
    for k, p in paths.items():
        console.print(f"  wrote {k}: {p}")


__all__ = ["app"]
