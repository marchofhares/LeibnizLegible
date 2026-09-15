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

Heavy steps (HTR, segmentation, vision extraction) import their stacks lazily and
skip gracefully when a key/model is absent, per COMMON CONTEXT.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from leibniz.align.report import GATE_PRECISION

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
