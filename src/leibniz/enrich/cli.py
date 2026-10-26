"""``leibniz enrich`` — the enrich stage's commands (SPECS §4.1).

* ``page-lang`` — which pages are German (Phase K4, Task 1): every recognised
  page's machine text classified with the stopword identifier, the result
  measured against the census's pieces, the threshold set for precision, the
  German page list and the report written. The store is read-only here; the
  ``page_lang`` table is written by Task 4's command.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console

from leibniz.db import DEFAULT_DB_PATH

app = typer.Typer(help="Enrich: language per page, strata.", no_args_is_help=True)
_console = Console()


@app.command("page-lang")
def page_lang(
    db_path: str = typer.Option(
        str(DEFAULT_DB_PATH), "--db", help="SQLite store path (opened read-only)."
    ),
    out: Path = typer.Option(
        Path("data/kurrent/page-lang.jsonl"), "--out", help="One row per recognised page."
    ),
    pages_out: Path = typer.Option(
        Path("data/kurrent/german-pages.txt"),
        "--pages-out",
        help="The German pages, one id a line (the reading job's input).",
    ),
    edition_cache: Path = typer.Option(
        Path("data/gt/edition_cache.jsonl"),
        "--edition-cache",
        help="The C2 edition cache: the census's pieces, the labelled set of the measure.",
    ),
    reports_dir: Path = typer.Option(
        Path("reports/kurrent"), "--reports-dir", help="page-lang.md, .json, -works.csv."
    ),
    today: str = typer.Option(None, "--today", help="ISO date for §70 expiry (default: today)."),
    precision_target: float = typer.Option(
        0.95, "--precision-target", help="The threshold is the best recall at or above it."
    ),
    min_hits: int = typer.Option(
        None, "--min-hits", help="Fix the threshold instead of picking it: German stopwords."
    ),
    min_score: float = typer.Option(
        None, "--min-score", help="Fix the threshold: the German share of the stopword hits."
    ),
    min_tokens: int = typer.Option(
        None, "--min-tokens", help="Fix the threshold: tokens on the page."
    ),
    no_measure: bool = typer.Option(
        False, "--no-measure", help="Skip the census labels (no edition cache): classify only."
    ),
    reuse: bool = typer.Option(
        False,
        "--reuse",
        help="Read the rows from --out instead of classifying the store again (a new "
        "threshold or report on the same pass).",
    ),
    list_exclude_set: list[str] = typer.Option(
        None,
        "--list-exclude-set",
        help="Leave this collection's German pages out of --pages-out (the verdicts stay); "
        "repeatable.",
    ),
) -> None:
    """Which pages are German: classify, measure, set the threshold, list (K4 Task 1)."""
    from leibniz.align.audit_reach import open_readonly
    from leibniz.align.ingest import load_edition_cache
    from leibniz.enrich import pagelang as P

    t = date.fromisoformat(today) if today else date.today()

    def _log(msg: str) -> None:
        _console.print(f"{datetime.now():%H:%M:%S} {msg}")

    conn = open_readonly(db_path)
    try:
        if reuse and out.exists():
            rows = P.read_jsonl(out)
            _log(f"{len(rows):,} rows read from {out}")
        else:
            _log("classifying every recognised page's machine text…")
            rows = P.classify_pages(
                conn, progress=lambda k, n: _log(f"  {k:,}/{n:,} pages") if k % 25000 == 0 else None
            )
            _log(f"{len(rows):,} pages classified")
        labels = None
        sweep_rows: list[P.Measure] = []
        chosen = default = None
        if not no_measure:
            if not edition_cache.exists():
                raise typer.BadParameter(f"no edition cache at {edition_cache}; or --no-measure")
            cache = load_edition_cache(edition_cache)
            labels = P.census_labels(conn, cache, today=t)
            _log(
                f"labels: {labels.n_pages.get('de', 0):,} German pages, "
                f"{labels.n_pages.get('la_fr', 0):,} Latin and French, "
                f"{labels.n_pages.get('both', 0):,} both, {labels.n_pages.get('other', 0):,} other"
            )
            sweep_rows = P.sweep(rows, labels)
            default = P.measure(rows, labels, P.Threshold())
            chosen = P.pick(sweep_rows, target=precision_target)
        if min_hits is not None or min_score is not None or min_tokens is not None:
            base = chosen.threshold if chosen else P.Threshold()
            threshold = P.Threshold(
                base.min_hits if min_hits is None else min_hits,
                base.min_score if min_score is None else min_score,
                base.min_tokens if min_tokens is None else min_tokens,
            )
            if labels is not None:
                chosen = P.measure(rows, labels, threshold)
        else:
            threshold = chosen.threshold if chosen else P.Threshold()
        counts = P.mark_german(rows, threshold, labels)
        works = P.tally_works(conn, rows)
    finally:
        conn.close()
    P.write_jsonl(out, rows)
    _, n_listed = P.write_page_list(pages_out, rows, exclude_sets=list_exclude_set or [])
    summ = P.summary(
        rows,
        labels=labels,
        sweep_rows=sweep_rows,
        chosen=chosen,
        threshold=threshold,
        default=default,
        target=precision_target,
        works=works,
        today=t,
    )
    paths = P.write_reports(summ, works, reports_dir=reports_dir)
    _console.print(
        f"[bold]page-lang[/bold] {summ['pages']:,} pages · "
        + " · ".join(f"{k} {v:,}" for k, v in summ["by_lang"].items())
    )
    if chosen is not None:
        _console.print(
            f"  threshold {threshold.key}: precision {chosen.precision:.1%}, "
            f"recall {chosen.recall:.1%} on {chosen.tp + chosen.fp + chosen.fn + chosen.tn:,} "
            f"labelled pages ({chosen.fp:,} Latin or French pages called German)"
        )
    elif labels is not None:
        _console.print(
            f"  no threshold of the grid reaches a precision of {precision_target:.0%}; "
            f"the identifier's own verdict is used ({threshold.key})"
        )
    _console.print(
        f"  German pages {summ['german_pages']:,} ({json.dumps(counts)}), lines "
        f"{summ['german_lines']:,}; {n_listed:,} listed in {pages_out}"
        + (f" ({', '.join(list_exclude_set)} left out)" if list_exclude_set else "")
        + f"; {out}, "
        + ", ".join(str(p) for p in paths.values())
    )


__all__ = ["app"]
