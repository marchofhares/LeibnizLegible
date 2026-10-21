"""``leibniz pack`` — the Calculemus seam on the terminal (Phase G1).

``fragments`` builds a fragment pack from the store (read-only), K2's readings
and K1's German pieces; ``check`` validates a pack against the contract (run it
on every pack before it leaves the desktop); ``judgments`` imports the game's
judgment pack — a dry run unless ``--write`` — and renders the Scriptorium
queue. The logic lives in :mod:`leibniz.pack.fragments`,
:mod:`leibniz.pack.check` and :mod:`leibniz.pack.judgments`.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from leibniz import db
from leibniz.align.audit_reach import open_readonly

from . import check as C
from . import fragments as F
from . import judgments as J

app = typer.Typer(
    help="The Calculemus seam: fragment packs out (fragments, check), judgment packs in "
    "(judgments).",
    no_args_is_help=True,
)
console = Console()


def _day(value: str | None) -> date:
    if value is None:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(f"--today must be YYYY-MM-DD, got {value!r}") from exc


def _say(lines: list[str]) -> None:
    for line in lines:
        console.print(line, highlight=False, markup=False, soft_wrap=True)


@app.command()
def fragments(
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="The store, opened read-only."),
    readings: Path = typer.Option(
        F.DEFAULT_READINGS,
        "--readings",
        help="K2's readings JSONL (line_id, text, conf, model, …).",
    ),
    pieces: Path = typer.Option(
        F.DEFAULT_PIECES, "--pieces", help="K1's german_pieces.jsonl (stratum, hand, language)."
    ),
    image_base_url: str = typer.Option(
        F.DEFAULT_IMAGE_BASE_URL, "--image-base-url", help="The image mirror (static delivery)."
    ),
    limit: int = typer.Option(F.DEFAULT_LIMIT, "--limit", min=1, help="Rows at most."),
    seed: int = typer.Option(0, "--seed", help="Seed of the draw, the order and the gold."),
    gold_rate: float = typer.Option(
        F.DEFAULT_GOLD_RATE, "--gold-rate", min=0.0, max=1.0, help="Gold rows at most, a share."
    ),
    bad_gold_share: float = typer.Option(
        F.DEFAULT_BAD_GOLD_SHARE,
        "--bad-gold-share",
        min=0.0,
        max=1.0,
        help="Both-wrong rows at most, a share of the gold.",
    ),
    min_chars: int = typer.Option(F.DEFAULT_MIN_CHARS, "--min-chars", min=1),
    max_chars: int = typer.Option(F.DEFAULT_MAX_CHARS, "--max-chars", min=1),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="The pack (default packs/fragments-<today>.jsonl; packs/ is gitignored).",
    ),
    today: str | None = typer.Option(
        None, "--today", help="The day of the §70 check, YYYY-MM-DD (default: today)."
    ),
) -> None:
    """Build a fragment pack: German A/B pairs (v1 against the Bern reading), with gold."""
    day = _day(today)
    if min_chars > max_chars:
        raise typer.BadParameter("--min-chars is over --max-chars")
    for label, path in (("--readings", readings), ("--pieces", pieces)):
        if not path.exists():
            raise typer.BadParameter(f"{label}: {path} not found")
    target = out or Path("packs") / f"fragments-{day.isoformat()}.jsonl"
    t0 = time.perf_counter()
    conn = open_readonly(db_path)
    try:
        piece_rows = F.load_pieces(pieces)
        reading_rows = F.load_readings(readings)
        pack = F.build_pack(
            conn,
            piece_rows,
            reading_rows,
            today=day,
            limit=limit,
            seed=seed,
            gold_rate=gold_rate,
            bad_gold_share=bad_gold_share,
            min_chars=min_chars,
            max_chars=max_chars,
            image_base_url=image_base_url,
        )
    finally:
        conn.close()
    F.write_pack(target, pack)
    _say(F.summary_lines(pack))
    _say(
        [
            f"Wrote {target} ({len(pack.rows):,} rows and the header) in "
            f"{time.perf_counter() - t0:.1f} s; the store was opened read-only. "
            f"Next: leibniz pack check {target}"
        ]
    )


@app.command(name="check")
def check_pack(
    file: Path = typer.Argument(
        ..., help="A fragment pack (or, with --judgments, a judgment pack)."
    ),
    judgments: bool = typer.Option(
        False, "--judgments", help="Check a judgment pack (game ⇒ Leibniz Legible) instead."
    ),
) -> None:
    """Validate a pack against the contract (Calculemus SPECS §6.6, schema_version 1)."""
    if not file.exists():
        raise typer.BadParameter(f"{file} not found")
    report = C.check_judgment_pack(file) if judgments else C.check_fragment_pack(file)
    _say(C.report_lines(report))
    if not report.ok:
        raise typer.Exit(1)


@app.command()
def judgments(
    in_path: Path = typer.Option(..., "--in", help="The judgment pack (JSONL) from the game."),
    write: bool = typer.Option(
        False, "--write", help="Import into the store (default: a dry run, the store read-only)."
    ),
    db_path: Path = typer.Option(db.DEFAULT_DB_PATH, "--db", help="The store."),
    fragments_path: Path | None = typer.Option(
        None,
        "--fragments",
        help="The fragment pack the judgments answer: the queue's two readings, and every "
        "winner checked against its candidates.",
    ),
    queue: Path = typer.Option(J.DEFAULT_QUEUE, "--queue", help="The Scriptorium queue report."),
) -> None:
    """Import the game's converged judgments as 'corrected' lines; queue the both-rejected."""
    for label, path in (("--in", in_path), ("--db", db_path), ("--fragments", fragments_path)):
        if path is not None and not path.exists():
            raise typer.BadParameter(f"{label}: {path} not found")
    report = C.check_judgment_pack(in_path)
    if not report.ok:
        _say(C.report_lines(report) + ["Refused: nothing was read from the pack."])
        raise typer.Exit(1)
    frags: dict[str, dict] | None = None
    frag_id: str | None = None
    if fragments_path is not None:
        frag_report = C.check_fragment_pack(fragments_path)
        if not frag_report.ok:
            _say(C.report_lines(frag_report) + ["Refused: the fragment pack does not check."])
            raise typer.Exit(1)
        frags = {r["line_id"]: r for r in frag_report.rows}
        frag_id = frag_report.header["pack_id"] if frag_report.header else None
    conn = db.connect(db_path) if write else open_readonly(db_path)
    try:
        plan = J.plan_import(conn, report, fragments=frags, fragments_pack_id=frag_id)
        run_id = None
        if write:
            params = {
                "judgment_pack": plan.header["pack_id"],
                "file": in_path.name,
                "built_at": plan.header["built_at"],
                "fragment_pack": frag_id,
                "n_rows": plan.n_rows,
            }
            run_id = J.apply_import(conn, plan, git_sha=db.git_sha(), params=params)
    finally:
        conn.close()
    J.write_queue(queue, plan, file_label=in_path.name, read_on=date.today().isoformat())
    _say(J.summary_lines(plan, wrote=write, run_id=run_id))
    _say([f"Queue: {queue} (the section of {plan.header['pack_id']})"])
