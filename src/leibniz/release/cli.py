"""``leibniz release`` — package the datasets and the model for deposit (Phase D3;
the first releases, REL1)."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from leibniz import db
from leibniz.release import state as S
from leibniz.release.export import (
    DATASETS,
    DEFAULT_CHUNK_ROWS,
    DEFAULT_OUT,
    export_all,
    store_summary,
)

app = typer.Typer(
    help="Releases (D3): export datasets + cards, package the model; print the checklist.",
    no_args_is_help=True,
)
console = Console()

CHECKLIST = Path("reports/release-checklist.md")
K3_CARD = Path("reports/kurrent/k3-model-card-trocr.md")


def _apply_release_options(
    out: Path, doi: list[str], hf_namespace: str | None, creator: list[str]
) -> dict:
    """Fold ``--doi``, ``--hf-namespace`` and ``--creator`` into ``RELEASE.json``."""
    release = S.load_release(out)
    changed = False
    for item in doi:
        record, sep, value = item.partition("=")
        if not sep:
            raise typer.BadParameter(f"--doi wants record=DOI, got {item!r}")
        try:
            S.set_doi(release, record.strip(), value)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        changed = True
    if hf_namespace:
        release["hf"]["namespace"] = hf_namespace.strip().strip("/")
        changed = True
    if creator:
        people = []
        for item in creator:
            parts = [p.strip() for p in item.split("|")]
            person = {"name": parts[0]}
            if len(parts) > 1 and parts[1]:
                person["orcid"] = parts[1]
            if len(parts) > 2 and parts[2]:
                person["affiliation"] = parts[2]
            people.append(person)
        release["creators"] = people
        changed = True
    if changed:
        S.save_release(out, release)
    return release


def _part_c_line(out: Path, release: dict) -> str:
    """The one line Part C is started with: the four DOIs, the namespace, the version."""
    import json

    dois = S.dois(release)
    version = ""
    manifest = out / "leibniz-transcriptions" / "MANIFEST.json"
    if manifest.exists():
        version = (json.loads(manifest.read_text(encoding="utf-8")).get("generated_at") or "")[:10]
    return (
        "For Part C: REL1 DOIs: "
        + " ".join(f"{r}={dois[r]}" for r in S.RECORDS)
        + f" · hf={S.hf_namespace(release) or '(not set)'} · version={version or '(unknown)'}"
    )


_DOI = typer.Option(
    [], "--doi", help="A reserved DOI as record=DOI (transcriptions, gt, gt-nc, model); repeat."
)
_HF = typer.Option(
    None, "--hf-namespace", help="The Hugging Face user or organisation the mirror lies under."
)
_CREATOR = typer.Option(
    [],
    "--creator",
    help='A creator of the Zenodo records as "Family, Given|ORCID|affiliation" (ORCID and '
    "affiliation optional); repeat. Kept in RELEASE.json at the release root, not in the repo.",
)


@app.command()
def export(
    db_path: Path = typer.Option(
        db.DEFAULT_DB_PATH, "--db", help="Canonical SQLite store (opened read-only)."
    ),
    out: Path = typer.Option(DEFAULT_OUT, "--out", help="Output root (one dir per dataset)."),
    fmt: str = typer.Option("parquet", "--format", help="parquet (needs pyarrow) or jsonl."),
    dataset: list[str] = typer.Option(
        [], "--dataset", help="Which datasets (inventory, transcriptions, gt, gt-nc); default all."
    ),
    chunk_rows: int = typer.Option(DEFAULT_CHUNK_ROWS, "--chunk-rows", help="Rows per file."),
    no_stats: bool = typer.Option(
        False, "--no-stats", help="Kept for old command lines; the store summary is cheap now."
    ),
    doi: list[str] = _DOI,
    hf_namespace: str = _HF,
    creator: list[str] = _CREATOR,
) -> None:
    """Write the dataset exports (files + MANIFEST.json + README card + deposit file).

    The store is opened read-only and nothing in it is changed. The lines are
    streamed page by page and written a chunk at a time, so the job's memory is a
    Parquet batch, not the table.
    """
    from leibniz.align.audit_reach import open_readonly

    chosen = tuple(dataset) if dataset else DATASETS
    unknown = [d for d in chosen if d not in DATASETS]
    if unknown:
        raise typer.BadParameter(f"unknown dataset(s) {unknown}; expected {DATASETS}")
    if not Path(db_path).exists():
        raise typer.BadParameter(f"store not found at {db_path}")
    release = _apply_release_options(out, doi, hf_namespace, creator)
    conn = open_readonly(db_path)
    try:
        exports = export_all(
            conn,
            out,
            datasets=chosen,
            fmt=fmt,
            chunk_rows=chunk_rows,
            stats=store_summary(conn),
            dois=S.dois(release),
        )
    finally:
        conn.close()
    table = Table(title="Exports")
    for col in ("dataset", "table", "rows", "files", "bytes"):
        table.add_column(col, justify="right" if col in ("rows", "files", "bytes") else "left")
    for exp in exports:
        for name, n in exp.row_counts.items():
            files = [f for f in exp.files if f.path.startswith(name + "-")]
            table.add_row(
                exp.dataset, name, f"{n:,}", str(len(files)), f"{sum(f.bytes for f in files):,}"
            )
    console.print(table)
    for exp in exports:
        by_model = (exp.counts.get("lines") or {}).get("by_model")
        if by_model:
            console.print(
                f"[bold]{exp.dataset}[/bold] lines by model: "
                + " · ".join(f"{m} {n:,}" for m, n in by_model.items())
            )
        gt = exp.counts.get("gt_lines")
        if gt:
            console.print(
                f"[bold]{exp.dataset}[/bold] by channel: "
                + " · ".join(f"{c} {n:,}" for c, n in gt["by_channel"].items())
                + f" · verified {gt['verified']:,}"
            )
    console.print(f"Written under [cyan]{out}[/cyan]. Next: [cyan]{CHECKLIST}[/cyan].")


@app.command()
def cards(
    out: Path = typer.Option(DEFAULT_OUT, "--out", help="The release root (the export's --out)."),
    doi: list[str] = _DOI,
    hf_namespace: str = _HF,
    creator: list[str] = _CREATOR,
) -> None:
    """Re-render every card and deposit file from the manifests (no store): run it
    after the DOIs are reserved, so each card carries its own DOI and its siblings'."""
    from leibniz.release.cards import rerender

    release = _apply_release_options(out, doi, hf_namespace, creator)
    done = rerender(out, release=release)
    if not done:
        raise typer.BadParameter(f"no dataset folder with a MANIFEST.json under {out}")
    dois = S.dois(release)
    for dataset in done:
        mark = f"doi:{dois[dataset]}" if dataset in dois else "no DOI yet"
        if dataset == "inventory":
            mark = "rides inside the transcriptions record"
        console.print(f"[bold]{dataset}[/bold]: card and deposit file re-rendered ({mark})")
    if "model" in dois and (out / S.folder_name("model", release)).is_dir():
        console.print(
            "The model's card is rendered by [cyan]leibniz release model[/cyan]: run it again "
            "so its README and zip carry the DOIs."
        )
    console.print(
        f"creators: {', '.join(c['name'] for c in S.creators(release))} · Hugging Face "
        f"namespace: {S.hf_namespace(release) or '(not set)'} · {out / S.RELEASE_FILE}"
    )
    if all(r in dois for r in S.RECORDS):
        console.print(_part_c_line(out, release), soft_wrap=True)


@app.command()
def model(
    weights: Path = typer.Option(..., "--weights", help="The TrOCR checkpoint's folder."),
    card: Path = typer.Option(K3_CARD, "--card", help="K3's model card (Markdown)."),
    name: str = typer.Option(S.MODEL_NAME, "--name", help="The model's public name."),
    out: Path = typer.Option(DEFAULT_OUT, "--out", help="The release root."),
    no_zip: bool = typer.Option(False, "--no-zip", help="Skip the zip (a card-only re-render)."),
    doi: list[str] = _DOI,
    hf_namespace: str = _HF,
    creator: list[str] = _CREATOR,
) -> None:
    """Package the German reader: the checkpoint's inference files, README (K3's
    card brought to the finish), LICENSE, MANIFEST.json, a zip for Zenodo and the
    record's deposit file. Reads the weights folder; writes under --out only."""
    from leibniz.release.model import ModelPackageError, build_package

    release = _apply_release_options(out, doi, hf_namespace, creator)
    try:
        pkg = build_package(weights, card, name, out, release=release, zip_it=not no_zip)
    except ModelPackageError as exc:
        raise typer.BadParameter(str(exc)) from exc
    table = Table(title=f"{name} ({pkg.bytes:,} bytes)")
    for col in ("file", "bytes", "sha256"):
        table.add_column(col, justify="right" if col == "bytes" else "left")
    for f in pkg.files:
        table.add_row(f["path"], f"{f['bytes']:,}", f["sha256"][:16] + "…")
    console.print(table)
    if pkg.left_out:
        console.print("left out (not inference files): " + ", ".join(pkg.left_out))
    if pkg.card_markers_missing:
        console.print(
            "[yellow]the card has changed shape: these lines of K3's card were not found and "
            "their finished statements were added under a heading of their own: "
            + "; ".join(pkg.card_markers_missing)
            + "[/yellow]"
        )
    mark = S.dois(release).get("model")
    console.print(
        f"Written [cyan]{pkg.folder}[/cyan]"
        + ("" if no_zip else f" and [cyan]{pkg.zip_path}[/cyan]")
        + f" ({'doi:' + mark if mark else 'no DOI yet: reserve it, then run this again'})."
    )


@app.command()
def check(
    out: Path = typer.Option(DEFAULT_OUT, "--out", help="The release root."),
    stats: Path = typer.Option(
        None,
        "--stats",
        help="The site's /api/stats saved to a file (curl -s https://…/api/stats > stats.json): "
        "the lines, the lines by model and the pages by language are compared with it.",
    ),
) -> None:
    """Run the checklist's checks on a release folder (reads the exports, not the
    store): files against manifests, counts against the site's, no NC line among the
    transcriptions, the deposits disjoint and complete, the cards and their DOIs."""
    import json

    from leibniz.release.check import check_release

    live = json.loads(stats.read_text(encoding="utf-8")) if stats else None
    rep = check_release(out, stats=live)
    for ok, text in rep.lines:
        console.print(f"[green]PASS[/green] {text}" if ok else f"[red]FAIL[/red] {text}")
    if live is None:
        console.print("(no --stats file: the counts were not compared with the site's)")
    console.print(
        f"{len(rep.lines) - rep.failures} passed, {rep.failures} failed"
        + ("" if rep.failures else ": the folder is as the checklist asks")
    )
    if rep.failures:
        raise typer.Exit(min(rep.failures, 100))


@app.command()
def checklist() -> None:
    """Print the release checklist (the operator's upload runbook)."""
    if CHECKLIST.exists():
        console.print(CHECKLIST.read_text(encoding="utf-8"))
    else:
        console.print(f"[yellow]{CHECKLIST} not found[/yellow]")


__all__ = ["app"]
