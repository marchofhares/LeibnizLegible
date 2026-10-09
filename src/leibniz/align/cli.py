"""``leibniz align`` — the retro-alignment stage CLI (Phase B2).

Subcommands:

* ``eval``    — measure aligner yield/precision on the PHILIUMM val split under
                real HTR (the §1 quantitative table); caches HTR, writes JSON.
* ``report``  — render ``reports/alignment-prototype.md`` from the eval JSON
                (and the live-run JSON, if present).
* ``extract`` — vision-LLM extraction of §70-expired edition reading text from an
                Internet Archive volume scan (apparatus excluded).
* ``run``     — the full end-to-end prototype on one piece: GWLB IIIF → segment →
                recognise → align to an edition-text file → mint ``gt_lines``.
* ``kurrent-tolerance`` — how much HTR noise the aligner tolerates (K1): the B2
                harness over the recorded B1 machine text, corrupted to target CERs.
* ``kurrent-census`` — the German census of the edition pieces (K1): language per
                record, canvases, v1 lines, minted lines, stratum and hand; read-only.
* ``kurrent-pilot`` — candidate readers on Leibniz's German as a factory dry run
                (K1): readings to JSONL, yield at the gate, the side-by-side page.

Heavy steps (HTR, segmentation, vision extraction) import their stacks lazily and
skip gracefully when a key/model is absent, per COMMON CONTEXT.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from leibniz.align.report import GATE_PRECISION
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT

app = typer.Typer(help="Retro-alignment: edition reading text → manuscript lines (Phase B2).")
_console = Console()

DEFAULT_HTR = "data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors"
DEFAULT_SEG = "data/models/philiumm-seg/blla_ft_leibniz_v1_0.4750.safetensors"
DEFAULT_VAL = "data/gt/philiumm-val/val-00000-of-00001.parquet"
DEFAULT_DB = "data/inventory.sqlite"
EVAL_JSON = Path("reports/alignment-eval.json")
RUN_JSON = Path("reports/alignment-run.json")

# The evaluation conditions (frozen so the number is reproducible).
_CONDITIONS = [
    ("diplomatic (HTR noise only)", 0.00, 0.00),
    ("edition-like divergence 3%", 0.03, 0.00),
    ("edition-like divergence 6%", 0.06, 0.00),
    ("edition omits 15% of lines", 0.00, 0.15),
    ("divergence 3% + omits 15%", 0.03, 0.15),
]


@app.command()
def eval(
    val: str = typer.Option(DEFAULT_VAL, help="PHILIUMM val parquet."),
    htr_model: str = typer.Option(DEFAULT_HTR, help="PHILIUMM HTR safetensors."),
    max_lines: int = typer.Option(400, help="Cap lines for a fast run."),
    lines_per_piece: int = typer.Option(25, help="Lines per synthetic piece."),
    threshold: float = typer.Option(0.60, help="Confidence threshold to mint."),
    out: Path = typer.Option(EVAL_JSON, help="Where to write the summaries JSON."),
) -> None:
    """Measure aligner yield/precision on the val split under real HTR."""
    from leibniz.align import evaluate as E
    from leibniz.htr.data import load_parquet_pairs

    pairs = load_parquet_pairs(val, limit=max_lines)
    pieces = E.build_pieces(pairs, lines_per_piece=lines_per_piece)
    _console.print(f"{len(pieces)} pieces, {sum(len(p.lines) for p in pieces)} lines; running HTR…")
    htr = E.run_htr_cached(pieces, htr_model, cache=Path("data/bench/b2_htr_cache.json"))

    summaries = []
    for label, perturb, drop in _CONDITIONS:
        cfg = E.EvalConfig(
            label=label, ref_char_perturb=perturb, ref_drop_rate=drop, threshold=threshold
        )
        lines = [ln for pc in pieces for ln in E.evaluate_piece(pc, htr, cfg)]
        s = E.summarize(lines, cfg, precision_target=GATE_PRECISION)
        summaries.append(s.as_report_dict())
        _console.print(
            f"  [bold]{label}[/bold]: yield {s.yield_rate:.1%}  precision {s.precision:.1%}  "
            f"false-mints {s.n_false_positive}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summaries, ensure_ascii=False, indent=1), encoding="utf-8")
    _console.print(f"wrote {out}")


@app.command("kurrent-tolerance")
def kurrent_tolerance(
    lines: Path = typer.Option(
        Path("reports/philiumm-repro.lines.jsonl"),
        help="The B1 reproduction dump: line_id, ref, hyp per row, in validation order.",
    ),
    levels: str = typer.Option("10,20,30,40,50,60", help="Target CERs in percent."),
    lines_per_piece: int = typer.Option(25, help="Consecutive lines per synthetic piece."),
    seed: int = typer.Option(20261009, help="Seed of the corruption streams."),
    max_lines: int | None = typer.Option(None, help="Cap lines for a fast run."),
    sample_every: int = typer.Option(
        1, help="Calibrate the rate on every n-th line (the achieved CER is measured on all)."
    ),
    workers: int = typer.Option(0, help="Processes over levels; 0 = one per level."),
    out_dir: Path = typer.Option(Path("reports/kurrent"), help="Where the two reports go."),
) -> None:
    """How much HTR noise the aligner tolerates (K1 Task 1): corrupt, align, grade."""
    import os

    from leibniz.align import tolerance as T

    targets = [float(x) / 100 for x in levels.split(",") if x.strip()]
    rows = T.load_repro_lines(lines, max_lines=max_lines)
    n_workers = workers if workers > 0 else min(len(targets) + 1, os.cpu_count() or 1)
    _console.print(
        f"{len(rows)} lines from {lines}; levels {', '.join(f'{t:.0%}' for t in targets)}; "
        f"{n_workers} worker(s)…"
    )
    res = T.run_tolerance(
        rows,
        levels=targets,
        seed=seed,
        lines_per_piece=lines_per_piece,
        sample_every=sample_every,
        workers=n_workers,
        source=str(lines),
    )
    for lv in res.levels:
        cells = "  ".join(
            f"{s}: {o.yield_rate:.1%}/{o.precision:.1%}" for s, o in lv.by_stratum.items()
        )
        _console.print(
            f"  [bold]{lv.label}[/bold] CER {lv.cer_written:.1%} (folded {lv.cer_folded:.1%}) "
            f"conf {lv.mean_conf:.3f} — yield/precision {cells}"
        )
    for be in res.break_evens:
        _console.print(f"  break-even {be.stratum} {be.metric} < {be.floor:.0%}: {be.describe()}")
    md, js = T.write_reports(res, out_dir)
    _console.print(f"wrote {md} and {js}")


@app.command("kurrent-census")
def kurrent_census(
    db_path: str = typer.Option(
        str(DEFAULT_DB), "--db", help="SQLite store path (opened read-only)."
    ),
    edition_cache: Path = typer.Option(
        Path("data/gt/edition_cache.jsonl"), "--edition-cache", help="The C2 edition cache."
    ),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    reports_dir: Path = typer.Option(
        Path("reports/kurrent"), "--reports-dir", help="census.md, the summary, the CSVs."
    ),
    data_dir: Path = typer.Option(
        Path("data/kurrent"), "--data-dir", help="german_pieces.jsonl (gitignored)."
    ),
    snippets: int = typer.Option(4, help="Edition-text snippets per class in the report."),
) -> None:
    """German census of the edition pieces (K1 Task 2): language, place, lines, mint, hand."""
    from datetime import date

    from leibniz.align import kurrent_census as K
    from leibniz.align.ingest import load_edition_cache

    t = date.fromisoformat(today) if today else date.today()
    cache = load_edition_cache(edition_cache)
    _console.print(f"{len(cache):,} edition-cache records; classifying and placing the pieces…")
    conn = K.open_readonly(db_path)
    try:
        res = K.census(
            conn,
            cache,
            today=t,
            progress=lambda k, n: _console.print(f"  {k:,}/{n:,} pieces"),
        )
    finally:
        conn.close()
    paths = K.write_outputs(
        res, reports_dir=reports_dir, data_dir=data_dir, cache=cache if snippets else None
    )
    summ = K.summary(res)
    g = summ["by_group"]
    de = g.get("de", {})
    lf = g.get("la_fr", {})
    _console.print(
        f"[bold]kurrent-census[/bold] {summ['pieces_with_text']:,} pieces with text "
        f"({summ['pieces_without_text']:,} without) · cache by language "
        + " · ".join(f"{k} {v:,}" for k, v in summ["cache_languages"].items())
    )
    if de:
        _console.print(
            f"  German: {de['pieces']:,} pieces, {de['pages']:,} pages, {de['lines']:,} lines, "
            f"{de['minted']:,} minted (yield {_fmt_pct(de['yield'])}); "
            f"Leibniz's hand {summ['german_leibniz_hand']:,} pieces"
        )
    if lf:
        _console.print(
            f"  Latin+French: {lf['pieces']:,} pieces, {lf['lines']:,} lines, {lf['minted']:,} "
            f"minted (yield {_fmt_pct(lf['yield'])})"
        )
    for name, path in paths.items():
        _console.print(f"  wrote {name}: {path}")


def _fmt_pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.1%}"


@app.command("kurrent-pilot")
def kurrent_pilot(
    db_path: str = typer.Option(
        str(DEFAULT_DB), "--db", help="SQLite store path (opened read-only)."
    ),
    german: Path = typer.Option(
        Path("data/kurrent/german_pieces.jsonl"), "--german", help="The census's German pieces."
    ),
    edition_cache: Path = typer.Option(
        Path("data/gt/edition_cache.jsonl"), "--edition-cache", help="The C2 edition cache."
    ),
    images: Path = typer.Option(
        Path("/mnt/d/leibniz-images"), "--images", help="The page-image cache root."
    ),
    readers: str = typer.Option(
        None,
        "--readers",
        help="Comma-separated reader keys (Task 3 candidates); default: the baseline plus every "
        "candidate at or under two thirds of its Dresden CER (bootstrap-candidates.json).",
    ),
    n_german: int = typer.Option(20, "--n-german", help="German pieces to read."),
    n_control: int = typer.Option(5, "--n-control", help="Latin or French control pieces."),
    max_pages: int = typer.Option(3, "--max-pages", help="Pages read per piece."),
    min_lines: int = typer.Option(20, "--min-lines", help="Least recognised lines for a piece."),
    sample: int | None = typer.Option(
        None, "--sample", help="Read only the first N lines of each page (slow devices)."
    ),
    device: str = typer.Option("auto", "--device", help="auto | cpu | cuda | cuda:N."),
    batch_size: int = typer.Option(8, "--batch-size", help="Lines per model call."),
    seed: int = typer.Option(20261009, "--seed", help="Seed of the piece and line draws."),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    readings_dir: Path = typer.Option(
        Path("data/kurrent/pilot-readings"),
        "--readings-dir",
        help="One resumable JSONL per reader.",
    ),
    side_by_side: Path = typer.Option(
        Path("data/kurrent/pilot-side-by-side.html"), "--side-by-side", help="The operator's page."
    ),
    reports_dir: Path = typer.Option(
        Path("reports/kurrent"), "--reports-dir", help="pilot.md etc."
    ),
    operator_verdict: str = typer.Option(
        None, "--operator-verdict", help="The operator's answer on the side-by-side page, verbatim."
    ),
    no_read: bool = typer.Option(
        False, "--no-read", help="Score the readings already on disk; read nothing new."
    ),
) -> None:
    """Candidate readers on Leibniz's German, as a factory dry run (K1 Task 4); nothing stored."""
    from datetime import date

    from leibniz.align import kurrent_pilot as P
    from leibniz.align.ingest import load_edition_cache
    from leibniz.htr import kurrent as K

    t = date.fromisoformat(today) if today else date.today()
    keys = (
        [k.strip() for k in readers.split(",") if k.strip()]
        if readers
        else P.qualifying_readers(reports_dir / "bootstrap-candidates.json")
    )
    unknown = [k for k in keys if k not in K.CANDIDATES and k != P.V1]
    if unknown:
        raise typer.BadParameter(f"unknown readers {unknown}; known: {sorted(K.CANDIDATES)}")
    dev = K.pick_device(device)
    rows = P.load_german_pieces(german)
    german_pieces = P.select_german(
        rows, n=n_german, seed=seed, max_pages=max_pages, min_lines=min_lines
    )
    cache = load_edition_cache(edition_cache)
    conn = P.open_readonly(db_path)
    try:
        controls = P.select_controls(
            conn, cache, n=n_control, seed=seed, max_pages=max_pages, min_lines=min_lines, today=t
        )
        pieces = [*german_pieces, *controls]
        _console.print(
            f"[bold]kurrent-pilot[/bold] {len(german_pieces)} German pieces + {len(controls)} "
            f"controls, {sum(len(p.page_ids) for p in pieces)} pages; readers {', '.join(keys)}; "
            f"device {dev}"
        )
        readings: dict[str, dict[str, P.Reading]] = {}
        for key in keys:
            if key == P.V1:
                continue
            cand = K.CANDIDATES[key]
            if no_read:
                readings[key] = P.load_readings(readings_dir, key)
                continue
            readings[key] = P.read_pieces(
                conn,
                pieces,
                key,
                lambda c=cand: K.build_engine(c, device=dev, batch_size=batch_size),
                images_root=images,
                readings_dir=readings_dir,
                sample=sample,
                batch_size=batch_size,
                log=lambda msg: _console.print(f"  {msg}"),
            )
        readings[P.V1] = P.v1_readings(conn, pieces, sample=sample)
        order = [k for k in keys if k != P.V1] + [P.V1]
        ordered = {k: readings[k] for k in order}
        yields = P.dry_run(conn, pieces, ordered, cache, sample=sample)
        summaries = P.summarize_readers(yields, ordered)
        res = P.PilotResult(
            pieces=pieces,
            yields=yields,
            summaries=summaries,
            verdict=P.verdict(summaries),
            readers=order,
            sample=sample,
            max_pages=max_pages,
            operator_verdict=operator_verdict,
        )
        side_by_side.parent.mkdir(parents=True, exist_ok=True)
        side_by_side.write_text(
            P.side_by_side(conn, pieces, ordered, images_root=images, seed=seed, sample=sample),
            encoding="utf-8",
        )
    finally:
        conn.close()
    for s_ in sorted(summaries, key=lambda s_: -(s_.german_yield or 0.0)):
        _console.print(
            f"  [bold]{s_.reader}[/bold]: German yield {_fmt_pct(s_.german_yield)} "
            f"(conf {s_.german_mean_conf:.3f}) · control yield {_fmt_pct(s_.control_yield)} "
            f"(conf {s_.control_mean_conf:.3f}) · {s_.read_lines:,} lines"
        )
    v = res.verdict
    _console.print(f"  verdict: best {v.best_reader} at {_fmt_pct(v.best_german_yield)}; {v.note}")
    paths = P.write_outputs(res, reports_dir=reports_dir)
    for name, path in paths.items():
        _console.print(f"  wrote {name}: {path}")
    _console.print(f"  wrote side-by-side: {side_by_side}")


@app.command()
def extract(
    ia_id: str = typer.Argument(..., help="Internet Archive item id of a §70-expired volume."),
    leaves: str = typer.Argument(..., help="Leaf range, e.g. '76-89'."),
    model: str = typer.Option("gpt-4o", help="Vision model."),
    engine: str = typer.Option("openai", help="openai | gemini (which vision endpoint)."),
    max_tokens: int = typer.Option(
        2000, help="Completion cap; thinking models spend reasoning tokens inside it."
    ),
    width: int = typer.Option(1700, help="Page image width."),
    out: Path = typer.Option(None, help="Write the reading text here (else stdout)."),
) -> None:
    """Vision-LLM extraction of edition reading text (apparatus excluded)."""
    import os

    from leibniz.align.pdftext import VisionEditionExtractor, fetch_ia_page_image
    from leibniz.htr.engines import GEMINI_URL, MissingKeyError
    from leibniz.net import PoliteClient

    kwargs: dict = {"model": model, "max_tokens": max_tokens}
    if engine == "gemini":
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            _console.print("[yellow]skipped: GEMINI_API_KEY (or GOOGLE_API_KEY) not set[/yellow]")
            raise typer.Exit(code=0)
        kwargs |= {"url": GEMINI_URL, "api_key": key}
    elif engine != "openai":
        raise typer.BadParameter(f"unknown --engine {engine!r} (openai | gemini)")

    lo, _, hi = leaves.partition("-")
    rng = range(int(lo), int(hi) + 1 if hi else int(lo) + 1)
    try:
        with PoliteClient() as c, VisionEditionExtractor(**kwargs) as ex:
            parts = []
            for leaf in rng:
                img = fetch_ia_page_image(ia_id, leaf, client=c, width=width)
                parts.append(ex.extract_page(img))
            cost = ex.usage_input, ex.usage_output
        text = "\n".join(p for p in parts if p.strip())
    except MissingKeyError as exc:
        _console.print(f"[yellow]skipped: {exc}[/yellow]")
        raise typer.Exit(code=0) from None
    _console.print(f"[dim]extracted {len(text)} chars; tokens in/out={cost}[/dim]")
    if out:
        out.write_text(text, encoding="utf-8")
        _console.print(f"wrote {out}")
    else:
        typer.echo(text)


@app.command()
def run(
    work: str = typer.Argument(..., help="GWLB object id."),
    canvases: str = typer.Argument(..., help="Canvas indices, e.g. '322-333' or '0,2,4'."),
    edition_text: Path = typer.Argument(..., help="File with the piece's reading text."),
    source: str = typer.Option(..., help="Provenance string for the minted GT."),
    stratum: str = typer.Option("unknown", help="fair_copy/light_revision/…"),
    license_bucket: str = typer.Option("open", help="open | nc"),
    htr_model: str = typer.Option(DEFAULT_HTR),
    seg_model: str = typer.Option(DEFAULT_SEG),
    threshold: float = typer.Option(0.60),
    db_path: str = typer.Option(None, help="If set, insert minted pairs into gt_lines here."),
    out: Path = typer.Option(RUN_JSON, help="Where to write the run JSON."),
) -> None:
    """Full prototype: fetch → segment → recognise → align → mint gt_lines."""
    from leibniz.align import prototype as P
    from leibniz.align.pairs import insert_gt_pairs, result_to_pairs

    idxs = _parse_indices(canvases)
    text = edition_text.read_text(encoding="utf-8")
    run = P.run_prototype(
        work_id=work,
        canvas_indices=idxs,
        edition_text=text,
        seg_model_path=seg_model,
        htr_model_path=htr_model,
        edition_source=source,
        threshold=threshold,
    )
    res = run.result
    _console.print(
        f"seg lines={run.n_seg_lines}  yield={res.yield_rate:.1%}  "
        f"minted={res.n_aligned}/{res.n_lines}"
    )
    pairs = result_to_pairs(res, source=source, stratum=stratum, license_bucket=license_bucket)
    if db_path:
        from leibniz.db import open_db

        with open_db(db_path) as conn:
            n = insert_gt_pairs(conn, pairs)
        _console.print(f"inserted {n} pairs into gt_lines ({db_path})")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "work": work,
                "canvas_indices": idxs,
                "n_seg_lines": run.n_seg_lines,
                "per_page_line_counts": run.per_page_line_counts,
                "yield": res.yield_rate,
                "n_aligned": res.n_aligned,
                "n_lines": res.n_lines,
                "edition_source": source,
                "edition_chars": run.edition_chars,
                "samples": [
                    {
                        "ref": ln.ref,
                        "conf": round(ln.align_conf, 3),
                        "aligned": ln.aligned,
                        "htr": ln.htr_text,
                        "edition": ln.edition_text.strip(),
                    }
                    for ln in res.lines
                ],
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    _console.print(f"wrote {out}")


@app.command()
def pieces(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path."),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    series: int = typer.Option(None, "--series", help="Restrict to one AA series."),
) -> None:
    """Enumerate the §70-expired, localizable pieces from the katalog × crosswalk."""
    from datetime import date

    from leibniz.align.volumes import enumerate_pieces
    from leibniz.db import open_db

    t = date.fromisoformat(today) if today else date.today()
    with open_db(db_path) as conn:
        _pcs, stats = enumerate_pieces(conn, today=t, series=series)
    _console.print(
        f"[bold]§70 pieces[/bold] {stats.pieces:,} · with work {stats.with_work:,} · "
        f"with folio range {stats.with_folio_range:,} · "
        f"[green]localizable {stats.localizable:,}[/green]"
    )
    for vol, n in sorted(stats.by_volume.items()):
        _console.print(f"  {vol:<8} {n:,}")


@app.command()
def factory(
    edition_cache: Path = typer.Argument(
        ..., help="The edition cache (.jsonl from `edition-cache`, or the older JSON object)."
    ),
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path."),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    license_bucket: str = typer.Option("open", help="open | nc."),
    series: int = typer.Option(None, "--series", help="Restrict to one AA series."),
    volume: int = typer.Option(None, "--volume", help="Restrict to one volume."),
    shard: str = typer.Option(
        None, "--shard", help="Mint shard i/N of the pieces (e.g. 3/12) — parallel workers."
    ),
    resume: bool = typer.Option(
        False, "--resume", help="Skip pieces that already carry gt_lines (continue a run)."
    ),
) -> None:
    """Mint gt_lines across the §70 pieces from a pre-extracted edition-text cache."""
    import time
    from datetime import date

    from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

    from leibniz.align.factory import FactoryConfig, dict_provider, run_factory, shard_pieces
    from leibniz.align.ingest import load_edition_cache
    from leibniz.align.volumes import enumerate_pieces
    from leibniz.db import open_db

    t = date.fromisoformat(today) if today else date.today()
    cfg = FactoryConfig(today=t, license_bucket=license_bucket)
    shard_t = _parse_shard(shard)
    with open_db(db_path) as conn:
        pieces, _enum = enumerate_pieces(conn, today=t, series=series, volume=volume)
        todo = shard_pieces(pieces, shard_t)
        # Stream the cache and keep only this shard's texts: N parallel workers
        # each parsing the whole cache at once is what exhausts a WSL VM's memory.
        cache = load_edition_cache(edition_cache, needed={p.record_id for p in todo})
        label = f"shard {shard}" if shard else "all pieces"
        _console.print(
            f"[bold]gt factory[/bold] → {len(todo):,} pieces ({label}; "
            f"{len(cache):,} records in the edition cache)"
        )
        minted = {"lines": 0, "done": 0}
        started = time.monotonic()

        def _log_line(force: bool = False) -> None:
            # Plain one-line progress for log files (nohup / redirected output).
            if force or minted["done"] % 25 == 0:
                mins = (time.monotonic() - started) / 60.0
                _console.print(
                    f"{label}: {minted['done']:,}/{len(todo):,} pieces · "
                    f"{minted['lines']:,} lines · {mins:,.1f} min"
                )

        with Progress(
            TextColumn("[cyan]minting"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TextColumn("{task.fields[lines]:,} lines"),
            console=_console,
            disable=not _console.is_terminal,
        ) as bar:
            task = bar.add_task("mint", total=len(todo), lines=0)

            def _tick(result) -> None:
                minted["lines"] += result.n_minted
                minted["done"] += 1
                bar.update(task, advance=1, lines=minted["lines"])
                if not _console.is_terminal:
                    _log_line()

            stats = run_factory(
                conn,
                config=cfg,
                edition_text_for=dict_provider(cache),
                series=series,
                volume=volume,
                pieces=todo,
                resume=resume,
                progress=_tick,
            )
        if not _console.is_terminal:
            _log_line(force=True)
    _console.print(
        f"[bold green]minted {stats.lines_minted:,} lines[/bold green] from "
        f"{stats.pieces_minted:,}/{stats.pieces_seen:,} pieces "
        f"({license_bucket} bucket)"
    )
    if stats.skips:
        _console.print(f"[yellow]skips:[/yellow] {dict(stats.skips)}")
    _console.print("Run [cyan]leibniz align gt-report[/cyan] to update reports/gt-factory.md.")


@app.command()
def ingest(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path."),
    editions_dir: Path = typer.Option(
        Path("data/editions"), "--editions", help="Raw text layers + extracted piece JSON."
    ),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    volume: list[str] = typer.Option(
        None, "--volume", help="Restrict to 'SERIES,VOLUME' (repeatable)."
    ),
    all_sources: bool = typer.Option(
        False, "--all-sources", help="Ingest every readable source (for cross-source QA)."
    ),
    force: bool = typer.Option(False, "--force", help="Re-extract even if cached."),
    no_fetch: bool = typer.Option(False, "--no-fetch", help="Only use already-downloaded files."),
) -> None:
    """Fetch + extract every §70-expired volume's reading text (cache-first)."""
    from datetime import date

    from leibniz.align.ingest import ingest_volume, volume_label
    from leibniz.align.volumes_sources import readable_sources
    from leibniz.legal import expired_volumes
    from leibniz.net import PoliteClient

    t = date.fromisoformat(today) if today else date.today()
    wanted = {tuple(int(x) for x in v.split(",")) for v in (volume or [])}
    targets = [
        (v.series, v.volume)
        for v in expired_volumes(t)
        if isinstance(v.volume, int) and (not wanted or (v.series, v.volume) in wanted)
    ]
    seen: set[tuple[int, int]] = set()
    with PoliteClient() as client:
        for series, vol in targets:
            if (series, vol) in seen:
                continue
            seen.add((series, vol))
            sources = readable_sources(series, vol)
            if not sources:
                _console.print(f"  {volume_label(series, vol):<7} [yellow]no readable source")
                continue
            for src in sources if all_sources else sources[:1]:
                try:
                    res = ingest_volume(
                        src,
                        client=None if no_fetch else client,
                        editions_dir=editions_dir,
                        force=force,
                    )
                except FileNotFoundError:
                    _console.print(f"  {volume_label(series, vol):<7} {src.kind}: not downloaded")
                    continue
                _console.print(
                    f"  {volume_label(series, vol):<7} {src.kind:<8} {res.status:<10} "
                    f"pieces {res.n_pieces:>4} · chars {res.n_chars:>9,} · "
                    f"reading pages {res.n_reading_pages}/{res.n_pages} · "
                    f"anomalies {res.n_anomalies}"
                )


@app.command(name="edition-cache")
def edition_cache(
    out: Path = typer.Argument(
        Path("data/gt/edition_cache.jsonl"),
        help="{record_id: text} cache; .jsonl = one record per line (streamable).",
    ),
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path."),
    editions_dir: Path = typer.Option(Path("data/editions"), "--editions"),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
) -> None:
    """Join the extracted volume texts to the katalog → the factory's edition cache."""
    from datetime import date

    from leibniz.align.ingest import (
        build_edition_cache,
        load_volume_texts,
        text_path,
        write_edition_cache,
    )
    from leibniz.align.volumes_sources import readable_sources
    from leibniz.db import open_db
    from leibniz.legal import expired_volumes

    t = date.fromisoformat(today) if today else date.today()
    texts: dict[tuple[int, int], dict[str, str]] = {}
    for v in expired_volumes(t):
        if not isinstance(v.volume, int):
            continue
        for src in readable_sources(v.series, v.volume):
            path = text_path(src, editions_dir)
            if path.exists():
                merged = texts.setdefault((v.series, v.volume), {})
                for piece, text in load_volume_texts(path).items():
                    merged.setdefault(piece, text)  # preferred source first
    with open_db(db_path) as conn:
        cache, stats = build_edition_cache(conn, texts)
    write_edition_cache(out, cache)
    _console.print(
        f"[bold green]{stats.records_with_text:,} records with reading text[/bold green] "
        f"({sum(len(v) for v in cache.values()):,} chars) → {out}; "
        f"{stats.records_cited_no_text:,} cite an ingested volume but no text was found"
    )
    for vol, n in sorted(stats.by_volume.items()):
        _console.print(f"  {vol:<7} {n:,}")
    if stats.volumes_without_source:
        _console.print(f"[yellow]no ingested source:[/yellow] {stats.volumes_without_source}")


@app.command(name="gt-report")
def gt_report(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path."),
    out: Path = typer.Option(Path("reports/gt-factory.md"), "--out", help="Report path."),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    editions_dir: Path = typer.Option(
        Path("data/editions"), "--editions", help="Extracted volume texts (ingest output)."
    ),
    edition_cache: Path = typer.Option(
        Path("data/gt/edition_cache.jsonl"), "--edition-cache", help="{record_id: text} cache."
    ),
) -> None:
    """(Re)write reports/gt-factory.md from the minted gt_lines + piece enumeration."""
    from datetime import date

    from leibniz.align.report_gt import gather_gt, render_gt
    from leibniz.db import open_db

    t = date.fromisoformat(today) if today else date.today()
    with open_db(db_path) as conn:
        rep = gather_gt(conn, today=t, editions_dir=editions_dir, edition_cache=edition_cache)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_gt(rep), encoding="utf-8")
    _console.print(f"[bold]gt-report[/bold] → {out} ({rep.n_open:,} open-bucket lines)")


@app.command(name="audit-sheet")
def audit_sheet(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path."),
    images_root: Path = typer.Option(
        DEFAULT_IMAGES_ROOT, "--images", help="Local image cache root (the C1 pipeline's --images)."
    ),
    out_dir: Path = typer.Option(
        Path("reports/gt-audit"), "--out", help="Directory for gt-audit.html + gt-audit-lines.csv."
    ),
    n: int = typer.Option(200, "--n", help="Lines to sample (equal numbers per stratum)."),
    seed: int = typer.Option(0, "--seed", help="Sampling seed (the draw is reproducible)."),
) -> None:
    """Write the hand-audit sheet: sampled minted lines with image strips + verdict buttons."""
    from leibniz.align.audit import build_sheet
    from leibniz.db import open_db

    with open_db(db_path) as conn:
        sheet = build_sheet(conn, images_root=images_root, out_dir=out_dir, n=n, seed=seed)
    _console.print(
        f"[bold]audit-sheet[/bold] → {sheet.html_path} ({len(sheet.lines)} lines, "
        f"{sheet.n_with_crops} with image strips; per stratum {dict(sheet.by_stratum)})"
    )
    if sheet.n_with_crops < len(sheet.lines):
        _console.print(
            f"[yellow]{len(sheet.lines) - sheet.n_with_crops} lines have no image strip — "
            f"check --images points at the C1 image cache ({images_root}).[/yellow]"
        )


def _parse_weights(spec: str) -> dict[str, int]:
    """``fair_copy=9913,light_revision=96175,…`` → ``{stratum: count}``."""
    out: dict[str, int] = {}
    for part in spec.split(","):
        if not part.strip():
            continue
        try:
            k, v = part.split("=", 1)
            out[k.strip()] = int(v.strip().replace("_", "").replace(" ", ""))
        except ValueError:
            raise typer.BadParameter(f"--weights wants stratum=count pairs, got {part!r}") from None
    if not out:
        raise typer.BadParameter("--weights is empty")
    return out


@app.command(name="audit-score")
def audit_score(
    verdicts: Path = typer.Argument(..., help="The downloaded gt-audit-verdicts.csv."),
    db_path: str = typer.Option(
        str(DEFAULT_DB), "--db", help="SQLite store path (stratum weights)."
    ),
    out: Path = typer.Option(Path("reports/gt-audit.md"), "--out", help="Markdown report path."),
    lines_csv: Path = typer.Option(
        None,
        "--lines",
        help="The sheet's gt-audit-lines.csv (default: next to the verdicts) — "
        "cross-checks every verdict against the HTR reading of the strip.",
    ),
    weights: str = typer.Option(
        None,
        "--weights",
        help="Stratum line counts as stratum=count pairs, for a machine without the store "
        "(e.g. the C2 mint's counts from reports/gt-factory.md); the store is then not opened.",
    ),
    weights_source: str = typer.Option(
        None, "--weights-source", help="Where the --weights counts come from (named in the report)."
    ),
    compare: Path = typer.Option(
        None,
        "--compare",
        help="A second verdict CSV on the same sheet (another auditor): the report gains "
        "an agreement section on the lines both judged.",
    ),
    compare_labels: str = typer.Option(
        "these verdicts,the other auditor", "--compare-labels", help="Two labels, comma-separated."
    ),
    patterns: bool = typer.Option(
        True,
        "--patterns/--no-patterns",
        help="Name a failure pattern per judged line (needs --lines).",
    ),
    overrides: Path = typer.Option(
        None,
        "--overrides",
        help="Override CSV (ref, pattern, why) for lines the rules cannot decide "
        "(default: gt-audit-pattern-overrides.csv next to the verdicts; written with the "
        "undecided refs when absent).",
    ),
    patterns_out: Path = typer.Option(
        None, "--patterns-out", help="Per-line pattern CSV (default: <verdicts stem>-patterns.csv)."
    ),
    corrections_out: Path = typer.Option(
        None,
        "--corrections-out",
        help="Corrections CSV (default: <verdicts stem>-corrections.csv).",
    ),
) -> None:
    """Score the hand-audit verdicts (precision per stratum + corpus-weighted)."""
    from leibniz.align import audit_patterns as P
    from leibniz.align.audit import (
        STRATA,
        read_verdicts,
        render_agreement,
        render_score,
        score_verdicts,
        text_evidence,
        verdict_agreement,
    )
    from leibniz.db import open_db

    rows = read_verdicts(verdicts)
    if lines_csv is None and (verdicts.parent / "gt-audit-lines.csv").exists():
        lines_csv = verdicts.parent / "gt-audit-lines.csv"
    evidence = text_evidence(rows, lines_csv) if lines_csv is not None else []
    if weights is not None:
        weight_counts = _parse_weights(weights)
        src = weights_source or "the command line"
        weight_note = (
            "stratum weights from "
            + src
            + " ("
            + ", ".join(f"{k} {v:,}" for k, v in weight_counts.items())
            + ")"
        )
    else:
        if not Path(db_path).exists():
            raise typer.BadParameter(
                f"store not found at {db_path}; pass --db, or --weights for a machine without it"
            )
        with open_db(db_path) as conn:
            weight_counts = {
                (r[0] or "unknown"): r[1]
                for r in conn.execute("SELECT stratum, COUNT(*) FROM gt_lines GROUP BY stratum")
            }
        weight_note = f"stratum weights from `{db_path}`"
    score = score_verdicts(rows, weight_counts)
    note = f"Verdicts from `{verdicts.name}` ({len(rows)} sheet lines); {weight_note}."
    sections: list[list[str]] = []
    if compare is not None:
        la, _, lb = compare_labels.partition(",")
        agr = verdict_agreement(
            rows, read_verdicts(compare), label_a=la.strip() or "A", label_b=lb.strip() or "B"
        )
        sections.append(render_agreement(agr))
        _console.print(
            f"[bold]agreement[/bold] with {compare.name}: {agr.n_same}/{agr.n} on the lines "
            "both judged"
        )
    n_undecided = 0
    if patterns and lines_csv is not None:
        prow = P.classify_rows(rows, P.read_lines_csv(lines_csv))
        ov_path = overrides or verdicts.parent / "gt-audit-pattern-overrides.csv"
        n_over = P.apply_overrides(prow, P.read_overrides(ov_path))
        n_undecided = P.write_override_template(prow, ov_path)
        p_out = patterns_out or verdicts.with_name(verdicts.stem + "-patterns.csv")
        c_out = corrections_out or verdicts.with_name(verdicts.stem + "-corrections.csv")
        P.write_patterns_csv(prow, p_out)
        table = P.corrections_table(prow)
        P.write_corrections_csv(table, c_out)
        sections.append(P.render_patterns(prow, strata=STRATA))
        sections.append(P.render_corrections(table))
        counts = P.pattern_counts(prow).get("all", {})
        _console.print(
            "[bold]patterns[/bold] "
            + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
            + f" → {p_out}; {len(table)} corrections → {c_out}; {n_over} overrides from "
            + ov_path.name
        )
        for r in prow:
            if r.undecided:
                _console.print(
                    f"[yellow]undecided[/yellow] {r.ref} ({r.stratum}, {r.verdict}): "
                    f"{r.note or 'no note'!s:.90}"
                )
        if n_undecided:
            _console.print(
                f"[yellow]{n_undecided} lines the rules cannot decide — settle them in {ov_path} "
                f"(ref, pattern, why) and re-run[/yellow]"
            )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_score(score, sheet_note=note, evidence=evidence, extra_sections=sections),
        encoding="utf-8",
    )
    flagged = sum(1 for e in evidence if e.recheck)
    if flagged:
        _console.print(
            f"[yellow]{flagged} verdicts contradict the machine reading — see {out}[/yellow]"
        )
    wp = score.weighted_precision
    if wp is None:
        _console.print(f"[yellow]no scored lines in {verdicts}[/yellow] → {out}")
    else:
        colour = "green" if score.passes_gate else "red"
        gate = f"{'PASS' if score.passes_gate else 'FAIL'} at ≥ {100 * score.gate:.0f} %"
        _console.print(
            f"[bold {colour}]weighted precision {100 * wp:.1f} % ({gate})[/bold {colour}] "
            f"· {score.pooled.n_judged} judged, {score.n_unjudged} blank → {out}"
        )


@app.command(name="audit-reach")
def audit_reach(
    db_path: str = typer.Option(
        str(DEFAULT_DB), "--db", help="SQLite store path (opened read-only)."
    ),
    out_dir: Path = typer.Option(
        Path("reports/gt-audit"), "--out", help="Directory for reach.md + reach-summary.json."
    ),
    flags_out: Path = typer.Option(
        Path("data/gt/flags.jsonl"),
        "--flags-out",
        help="Per-line flags for C3 (JSONL, gitignored).",
    ),
) -> None:
    """Measure the audit's failure patterns across every open-bucket minted line (read-only)."""
    import json

    from leibniz.align import audit_reach as R
    from leibniz.align.audit import STRATA

    conn = R.open_readonly(db_path)
    try:
        c = R.census(conn)
    finally:
        conn.close()
    out_dir.mkdir(parents=True, exist_ok=True)
    n_flags = R.write_flags(c, flags_out)
    (out_dir / "reach.md").write_text(
        R.render(c, strata=STRATA, flags_path=flags_out), encoding="utf-8"
    )
    summ = R.summary(c, strata=STRATA)
    (out_dir / "reach-summary.json").write_text(
        json.dumps(summ, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    a = summ["all"]
    _console.print(
        f"[bold]audit-reach[/bold] {c.n:,} lines on {c.n_pages:,} pages → {out_dir / 'reach.md'}; "
        f"{n_flags:,} flag rows → {flags_out}"
    )
    if c.n_skipped:
        _console.print(
            f"[yellow]{c.n_skipped:,} rows with a non-canonical reference skipped[/yellow]"
        )
    _console.print(
        "  "
        + " · ".join(
            f"{f} {a[f]:,} ({'—' if a[f + '_share'] is None else f'{100 * a[f + "_share"]:.1f} %'})"
            for f in R.FLAGS
        )
    )


@app.command(name="philiumm-sample")
def philiumm_sample(
    dest: Path = typer.Option(
        Path("data/philiumm/sample"), "--dest", help="Where their worked example is cached."
    ),
    out: Path = typer.Option(
        Path("reports/philiumm/alignment-sample.md"), "--out", help="Markdown report path."
    ),
    threshold: float = typer.Option(
        None, "--threshold", help="align_conf to mint (default: the aligner's)."
    ),
    offline: bool = typer.Option(
        False, "--offline", help="Use what is under --dest; fetch nothing."
    ),
    max_pairs: int = typer.Option(40, "--max-pairs", help="Differing lines listed per block."),
) -> None:
    """P1 Task 1: this project's aligner on PHILIUMM's worked example, against theirs."""
    from leibniz.align import philiumm as _ph  # noqa: F401  (package)
    from leibniz.align.align import DEFAULT_THRESHOLD
    from leibniz.align.philiumm import sample as S
    from leibniz.align.philiumm.fetch import fetch_sample

    thr = DEFAULT_THRESHOLD if threshold is None else threshold
    if not offline:
        fetch_sample(dest, progress=lambda m: _console.print(f"[dim]{m}[/dim]"))
    sample = S.load_sample(dest)
    confs = S.run_configurations(sample, threshold=thr)
    comps = [S.compare(c, sample) for c in confs]
    csv_path = dest / "comparison.csv"
    best = max(comps, key=lambda k: k.total("both_same") + k.total("ours_only"))
    S.write_comparison_csv(best, csv_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        S.render(sample, confs, comps, threshold=thr, max_pairs=max_pairs, comparison_csv=csv_path),
        encoding="utf-8",
    )
    S.write_summary(S.summary(sample, confs, comps, threshold=thr), out.with_suffix(".json"))
    tt = S.their_totals(sample)
    if tt:
        _console.print(
            f"[bold]theirs[/bold] {tt['nb_htr_lines']} lines, {tt['nb_gt_aligned']} aligned "
            f"({tt['pct_gt_aligned']} %) — alignment_report.csv at {sample.commit or '?'}"
        )
    for c, k in zip(confs, comps, strict=True):
        _console.print(
            f"[bold]{c.label}[/bold] {c.n_minted}/{c.n_lines} minted "
            f"({100 * c.n_minted / max(1, c.n_lines):.1f} %), raw ≥ 0.7: "
            f"{c.n_minted_above(S.THEIR_FILTER_SIM)} · vs theirs: "
            + ", ".join(f"{b} {k.total(b)}" for b in S.BUCKETS)
        )
    _console.print(f"→ {out}, {out.with_suffix('.json')}, {csv_path} (the {best.label} pairs)")
    diff = [p for p in best.pairs if p.bucket in ("both_different", "ours_only", "theirs_only")]
    for p in diff[:max_pairs]:
        _console.print(
            f"  [{p.bucket}] {p.file.replace('.xml', '')}#{p.index} HTR: {p.htr_text[:60]!r}\n"
            f"      ours:   {p.ours[:70]!r}\n      theirs: {p.theirs[:70]!r}"
        )


vi4_app = typer.Typer(help="P1 Task 2: A VI,4 under PHILIUMM's aligner and this project's.")
app.add_typer(vi4_app, name="philiumm-vi4")
VI4_DEST = Path("data/philiumm")
VI4_REPORTS = Path("reports/philiumm")


@vi4_app.command(name="fetch")
def vi4_fetch(
    dest: Path = typer.Option(VI4_DEST, "--dest", help="Cache directory (data/philiumm)."),
    limit: int = typer.Option(None, "--limit", help="Fetch at most this many files (a trial)."),
) -> None:
    """Their noisy split's PAGE XML files and the Hub listing, cache-first, 1 request/s."""
    from leibniz.align.philiumm import vi4 as V

    listing = V.fetch_listing(dest)
    n_noisy = len(V.split_files(listing, "noisy"))
    _console.print(
        f"[bold]listing[/bold] {listing['dataset']} @ {(listing.get('sha') or '?')[:12]}: "
        f"{len(listing['files'])} files, {n_noisy} noisy XML"
    )

    def progress(k: int, n: int, rel: str) -> None:
        if k == 1 or k % 25 == 0 or k == n:
            _console.print(f"[dim]{k}/{n} {rel}[/dim]")

    fetched, present = V.fetch_noisy(dest, listing=listing, progress=progress, limit=limit)
    _console.print(
        f"[bold]fetch[/bold] {fetched} fetched, {present}/{n_noisy} present under {dest / 'noisy'}"
    )


@vi4_app.command(name="match")
def vi4_match(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path (read-only)."),
    dest: Path = typer.Option(VI4_DEST, "--dest", help="Cache directory (data/philiumm)."),
    reports: Path = typer.Option(VI4_REPORTS, "--reports", help="Report directory."),
    threshold: float = typer.Option(None, "--iou", help="Bounding-box IoU to pair lines."),
) -> None:
    """File names → works and pages; their lines → this project's lines by geometry."""
    import json

    from leibniz.align.audit_reach import open_readonly
    from leibniz.align.philiumm import vi4 as V

    thr = V.IOU_DEFAULT if threshold is None else threshold
    conn = open_readonly(db_path)
    try:
        matches = V.run_match(
            conn,
            dest,
            threshold=thr,
            progress=lambda k, n, rel: (
                (k % 100 == 0 or k == n) and _console.print(f"[dim]{k}/{n}[/dim]")
            ),
        )
    finally:
        conn.close()
    V.write_match(matches, dest / V.MATCH_NAME)
    n_held = V.write_heldout(matches, reports / "heldout_pages.csv")
    summ = V.match_summary(matches)
    (reports / "vi4-match-summary.json").parent.mkdir(parents=True, exist_ok=True)
    (reports / "vi4-match-summary.json").write_text(
        json.dumps(summ, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _console.print(
        f"[bold]match[/bold] {summ['files']} files: "
        + "; ".join(
            f"{split} " + ", ".join(f"{k} {v}" for k, v in sorted(c.items()))
            for split, c in summ["by_split_status"].items()
        )
    )
    _console.print(
        f"  noisy: {summ['their_lines']:,} of their lines vs {summ['our_lines']:,} of ours on "
        f"{summ['noisy_matched']} files → {summ['pairs']:,} pairs at IoU ≥ {thr} "
        f"({', '.join(f'{k} {v:,}' for k, v in summ['pairs_by_iou'].items())}); "
        f"layouts {summ['layouts']}"
    )
    _console.print(
        f"  {len(summ['pages'])} held-out pages → {reports / 'heldout_pages.csv'} ({n_held} rows); "
        f"{len(summ['unresolved'])} files unresolved (see {reports / 'vi4-match-summary.json'})"
    )


@vi4_app.command(name="compare")
def vi4_compare(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path (read-only)."),
    dest: Path = typer.Option(VI4_DEST, "--dest", help="Cache directory (data/philiumm)."),
    reports: Path = typer.Option(VI4_REPORTS, "--reports", help="Report directory."),
    sample_rows: int = typer.Option(500, "--sample-rows", help="Rows in the committed sample CSV."),
) -> None:
    """Their aligned text vs this project's minted text on every paired line."""
    import json

    from leibniz.align.audit_reach import open_readonly
    from leibniz.align.philiumm import vi4 as V

    matches = V.read_match(dest / V.MATCH_NAME)
    listing = json.loads((dest / V.LISTING_NAME).read_text(encoding="utf-8"))
    conn = open_readonly(db_path)
    try:
        rows = V.judge(conn, matches, dest)
    finally:
        conn.close()
    summ = V.compare_summary(matches, rows)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "vi4-crosscheck.md").write_text(
        V.render(matches, rows, summ, listing=listing), encoding="utf-8"
    )
    (reports / "vi4-summary.json").write_text(
        json.dumps(summ, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    V.write_judged(rows, dest / "vi4-judged.csv")
    dis = [r for r in rows if r.bucket in ("disagree", "near", "ours_only", "theirs_only")]
    V.write_judged(dis, dest / "vi4-disagreements.csv")
    sample = V.disagreement_sample(rows, n=sample_rows)
    V.write_judged(sample, reports / "vi4-disagreements-sample.csv")
    V.write_judged([r for r in rows if r.ours and r.theirs], dest / "vi4-double-witnessed.csv")
    t = summ["total"]
    _console.print(
        f"[bold]compare[/bold] {summ['judged']:,} paired lines: "
        + ", ".join(f"{b} {t[b]:,}" for b in V.BUCKETS)
    )
    w = summ["witness_disagree"]
    _console.print(
        f"  on the disagreements the HTR is closer to ours {w['ours_closer']}, to theirs "
        f"{w['theirs_closer']}, tie {w['tie']} → {reports / 'vi4-crosscheck.md'}"
    )


@vi4_app.command(name="sheet")
def vi4_sheet(
    db_path: str = typer.Option(str(DEFAULT_DB), "--db", help="SQLite store path (read-only)."),
    dest: Path = typer.Option(VI4_DEST, "--dest", help="Cache directory (data/philiumm)."),
    images_root: Path = typer.Option(
        DEFAULT_IMAGES_ROOT, "--images", help="Local image cache root (the C1 pipeline's --images)."
    ),
    n: int = typer.Option(300, "--n", help="Lines on the sheet."),
    seed: int = typer.Option(0, "--seed", help="Sampling seed."),
) -> None:
    """A hand-audit sheet of the disagreements (both texts shown), crops from the cache."""
    import csv as _csv

    from leibniz.align.audit_reach import open_readonly
    from leibniz.align.philiumm import vi4 as V

    with (dest / "vi4-disagreements.csv").open(newline="", encoding="utf-8") as fh:
        raw = list(_csv.DictReader(fh))
    rows = [
        V.Judged(
            r["file"],
            r["ref"],
            r["their_id"],
            r["zone"] or None,
            float(r["iou"] or 0),
            r["stratum"],
            r["htr"],
            r["ours"],
            r["theirs"],
            r["bucket"],
            float(r["sim"]) if r["sim"] else None,
            float(r["sim_htr_ours"]) if r["sim_htr_ours"] else None,
            float(r["sim_htr_theirs"]) if r["sim_htr_theirs"] else None,
            float(r["align_conf"]) if r["align_conf"] else None,
        )
        for r in raw
    ]
    conn = open_readonly(db_path)
    try:
        html_path, with_crops = V.build_disagreement_sheet(
            conn, rows, images_root=images_root, out_dir=dest, n=n, seed=seed
        )
    finally:
        conn.close()
    _console.print(f"[bold]sheet[/bold] → {html_path} ({with_crops} lines with image strips)")


# NB: the ``reports/alignment-prototype.md`` deliverable is assembled from the
# ``eval`` output (its §1 numbers) plus this session's live-run facts, using the
# renderers in ``leibniz.align.report``; it is a curated report (like census.md /
# crosswalk.md), not a single-command regeneration, so there is no ``report``
# subcommand that could clobber it with a numbers-only skeleton.


def _parse_shard(spec: str | None) -> tuple[int, int] | None:
    """Parse ``--shard i/N`` (1-based, e.g. ``3/12``) into a 0-based ``(index, count)``."""
    if not spec:
        return None
    try:
        i_s, n_s = spec.split("/", 1)
        i, n = int(i_s), int(n_s)
    except ValueError:
        raise typer.BadParameter(f"--shard wants 'i/N' (e.g. 3/12), got {spec!r}") from None
    if n < 1 or not (1 <= i <= n):
        raise typer.BadParameter(f"--shard index must be between 1 and N, got {spec!r}")
    return (i - 1, n)


def _parse_indices(spec: str) -> list[int]:
    if "-" in spec and "," not in spec:
        lo, hi = spec.split("-")
        return list(range(int(lo), int(hi) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


__all__ = ["app"]
