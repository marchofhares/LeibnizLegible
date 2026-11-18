"""``leibniz layout`` — the layout stage's commands (P1 Task 3, 2026-11-17).

* ``philiumm-pages`` — PHILIUMM's layout training pages resolved to this
  project's page ids (``reports/layout/philiumm-layout-pages.csv``).
* ``sample`` — the zone census sample drawn from the store, its scans linked
  into one folder for her pipeline (``reports/layout/sample.csv``).
* ``zone-census`` — the census over the pipeline's results
  (``reports/layout/zone-census.md``, ``-summary.json``, ``-per-page.csv``).

The store is opened read-only everywhere here.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import typer
from rich.console import Console

from leibniz.db import DEFAULT_DB_PATH
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT

app = typer.Typer(help="Layout: zones, the census sample, the zone census.", no_args_is_help=True)
_console = Console()

REPORTS = Path("reports/layout")
DATASET_DIR = Path("data/philiumm/layout-dataset")
SAMPLE_DIR = Path("data/philiumm/layout-sample")
HELDOUT = Path("reports/philiumm/heldout_pages.csv")
PAGES_CSV = REPORTS / "philiumm-layout-pages.csv"
SAMPLE_CSV = REPORTS / "sample.csv"


def _ro(path: str) -> sqlite3.Connection:
    p = Path(path)
    if not p.exists():
        raise typer.BadParameter(f"no store at {p}")
    conn = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = 1")
    return conn


@app.command("philiumm-pages")
def philiumm_pages(
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db", help="SQLite store (read-only)."),
    images: Path = typer.Option(
        Path(DEFAULT_IMAGES_ROOT), "--images", help="The page-image cache."
    ),
    dataset_dir: Path = typer.Option(
        DATASET_DIR, "--dataset-dir", help="Where the Hub's listing and COCO files are cached."
    ),
    out: Path = typer.Option(PAGES_CSV, "--out", help="The CSV: one row per dataset image."),
    no_images: bool = typer.Option(
        False, "--no-images", help="Never download an original to settle a size tie."
    ),
) -> None:
    """Her layout dataset's pages (train, valid, test) → this project's page ids."""
    from leibniz.layout import philiumm_pages as P
    from leibniz.net import PoliteClient, default_user_agent

    conn = _ro(db_path)
    with PoliteClient(user_agent=default_user_agent()) as client:
        listing = P.fetch_listing(dataset_dir, client=client)
        files = P.fetch_annotations(dataset_dir, listing, client=client)
        images_all: list[P.CocoImage] = []
        cats: dict[int, str] = {}
        for split, path in files.items():
            ims, c = P.read_coco(path, split)
            images_all.extend(ims)
            cats.update(c)
        _console.print(
            f"revision {listing.get('sha')}, licence {listing.get('license')}: "
            f"{len(images_all)} originals in {len(files)} splits"
        )

        def fetch_original(rel: str) -> bytes:
            cache = dataset_dir / "originals" / Path(rel).name
            if cache.exists():
                return cache.read_bytes()
            data = client.get_bytes(P.hf_file_url(rel, revision=listing.get("sha") or "main"))
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(data)
            return data

        matches = P.match_images(
            conn,
            images_all,
            images_root=images,
            fetch_original=None if no_images else fetch_original,
        )
    P.write_pages_csv(matches, out)
    summ = P.summary(matches, listing, cats)
    (out.with_name(out.stem + "-summary.json")).write_text(
        json.dumps(summ, indent=1) + "\n", encoding="utf-8"
    )
    _console.print(json.dumps(summ["by_split"], indent=1))
    check = summ["size_check"]
    _console.print(
        f"pages: train+valid {summ['pages_train_valid']} (kept out of the sample), "
        f"test {summ['pages_test']}; size check on single pages resolved by name: "
        f"{check['size_agrees']} of {check['single_pages_resolved_by_name']} agree"
    )
    for m in matches:
        if m.status not in ("matched", "size-matched", "thumbnail-matched", "not-gwlb"):
            _console.print(f"  {m.split}/{m.stem}: {m.status} — {' | '.join(m.notes)}")
    _console.print(f"wrote {out}")


@app.command("sample")
def sample(
    n: int = typer.Option(400, "--n", help="Pages in the two strata together."),
    seed: int = typer.Option(0, "--seed"),
    n_lh35: int = typer.Option(100, "--lh35", help="Pages of the LH 35 block."),
    n_marginalien: int = typer.Option(100, "--marginalien", help="Pages of the Marginalien block."),
    marginalien_german: int = typer.Option(
        30, "--marginalien-german", help="German-print pages among them."
    ),
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db", help="SQLite store (read-only)."),
    images: Path = typer.Option(
        Path(DEFAULT_IMAGES_ROOT), "--images", help="The page-image cache."
    ),
    out_dir: Path = typer.Option(
        SAMPLE_DIR, "--out-dir", help="The sample folder; the scans are linked into its images/."
    ),
    csv_out: Path = typer.Option(SAMPLE_CSV, "--csv", help="The sample list."),
    exclude: list[Path] = typer.Option(
        [HELDOUT, PAGES_CSV],
        "--exclude",
        help="CSV files whose page ids stay out (a page_id or page_ids column).",
    ),
    test_block: Path = typer.Option(
        PAGES_CSV,
        "--test-block",
        help="Her pages CSV; its test split is the philiumm-test block (none: skip).",
    ),
    extra: list[str] = typer.Option(
        ["DE-611-HS-971383:0035"], "--extra", help="Named extra pages."
    ),
    copy: bool = typer.Option(False, "--copy", help="Copy the scans instead of linking them."),
) -> None:
    """Draw the census sample and link its scans into one folder."""
    from leibniz.layout import sample as S
    from leibniz.layout.philiumm_pages import read_pages_csv

    conn = _ro(db_path)
    excluded: set[str] = set()
    for path in exclude:
        if not path.exists():
            _console.print(f"[yellow]exclusion file missing: {path}[/yellow]")
            continue
        before = len(excluded)
        with path.open(encoding="utf-8") as fh:
            import csv as _csv

            for row in _csv.DictReader(fh):
                if "page_ids" in row:
                    excluded.update(p for p in row["page_ids"].split(";") if p)
                elif "page_id" in row:
                    excluded.add(row["page_id"])
        _console.print(
            f"excluded from {path}: {len(excluded) - before} new ids ({len(excluded)} in all)"
        )
    named: dict[str, list[str]] = {}
    if test_block and Path(test_block).exists():
        named["philiumm-test"] = sorted(read_pages_csv(test_block, splits=["test"]))
    if extra:
        named["extra"] = list(extra)
    plan = S.SamplePlan(n, n_lh35, n_marginalien, marginalien_german, seed, excluded, named)
    rows, notes = S.draw(conn, plan)
    S.write_sample(rows, csv_out)
    made, missing = S.link_images(rows, images, out_dir / "images", copy=copy)
    notes["linked"] = made
    notes["missing_scans"] = missing
    (out_dir / "sample-notes.json").write_text(json.dumps(notes, indent=1) + "\n", encoding="utf-8")
    (csv_out.with_name(csv_out.stem + "-notes.json")).write_text(
        json.dumps(notes, indent=1) + "\n", encoding="utf-8"
    )
    _console.print(json.dumps(notes, indent=1))
    _console.print(
        f"{len(rows)} pages → {csv_out}; {made} scans linked into {out_dir / 'images'}"
        + (f"; MISSING {len(missing)}" if missing else "")
    )


@app.command("downscale")
def downscale(
    long_side: int = typer.Option(1600, "--long", help="The long side of the copies, in pixels."),
    sample_csv: Path = typer.Option(SAMPLE_CSV, "--sample", help="The sample list."),
    images: Path = typer.Option(
        Path(DEFAULT_IMAGES_ROOT), "--images", help="The page-image cache."
    ),
    out_dir: Path = typer.Option(
        None, "--out-dir", help="Default: data/philiumm/layout-sample/images-<long>."
    ),
    blocks: list[str] = typer.Option([], "--block", help="Only these blocks (default: all)."),
) -> None:
    """Write the downscaled copies of the sample's scans that the pipeline reads."""
    from leibniz.layout.sample import downscale_images, read_sample

    rows = read_sample(sample_csv)
    if blocks:
        rows = [r for r in rows if r.block in blocks]
    dest = out_dir or (SAMPLE_DIR / f"images-{long_side}")
    written, present, missing = downscale_images(rows, images, dest, long_side=long_side)
    size = sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
    _console.print(
        f"{written} written, {present} already there, {len(missing)} scans missing → {dest} "
        f"({size / 2**20:.0f} MiB)"
    )
    if missing:
        _console.print("missing: " + ", ".join(missing[:20]))


@app.command("zone-census")
def zone_census(
    results: Path = typer.Option(
        Path("data/philiumm/layout-results"),
        "--results",
        help="The pipeline's results folder (01_…, 03_…, 10_…).",
    ),
    sample_csv: Path = typer.Option(SAMPLE_CSV, "--sample", help="The sample list."),
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db", help="SQLite store (read-only)."),
    reports_dir: Path = typer.Option(REPORTS, "--reports-dir"),
    config: Path = typer.Option(
        Path("data/philiumm/config_v2_ema.json"),
        "--config",
        help="The config the pipeline ran with (recorded).",
    ),
    sums: Path = typer.Option(
        Path("data/philiumm/models/SHA256SUMS"),
        "--sums",
        help="The checkpoints' digests (recorded).",
    ),
    revision: Path = typer.Option(
        Path("data/philiumm/models/REVISION"), "--revision", help="The card's revision (recorded)."
    ),
    commit_file: Path = typer.Option(
        Path("data/philiumm/rfdetr-pipeline.COMMIT"),
        "--commit",
        help="Her repository's commit (recorded).",
    ),
    blocks: list[str] = typer.Option([], "--block", help="Only these blocks (default: all)."),
) -> None:
    """The zone census over the pipeline's results, per page, per block and over all."""
    from leibniz.layout import census as C
    from leibniz.layout.sample import read_sample

    conn = _ro(db_path)
    rows = read_sample(sample_csv)
    if blocks:
        rows = [r for r in rows if r.block in blocks]
    meta: dict = {"sample": str(sample_csv), "results": str(results)}
    if config.exists():
        cfg = json.loads(config.read_text(encoding="utf-8"))
        meta.update(
            checkpoint=Path(cfg.get("model_path", "")).name,
            resolution=cfg.get("resolution"),
            threshold=cfg.get("confidence_threshold"),
            class_thresholds=cfg.get("class_thresholds"),
        )
    if sums.exists():
        for line in sums.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            if name.strip() == meta.get("checkpoint"):
                meta["checkpoint_sha256"] = digest
    if revision.exists():
        meta["card_revision"] = revision.read_text(encoding="utf-8").strip()
    if commit_file.exists():
        for line in commit_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("commit "):
                meta["pipeline_commit"] = line.split()[1]
    meta.setdefault("model", "DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2")
    meta.setdefault("licence", "CC BY-NC 4.0 (the card, read 2026-11-16)")

    def progress(k: int, n_: int, pid: str) -> None:
        if k % 50 == 0 or k == n_:
            _console.print(f"  {k}/{n_} {pid}")

    pages = C.census(conn, rows, results, progress=progress)
    summary = C.summarize(pages, meta)
    reports_dir.mkdir(parents=True, exist_ok=True)
    C.write_per_page(pages, reports_dir / "zone-census-per-page.csv")
    C.write_summary(summary, reports_dir / "zone-census-summary.json")
    (reports_dir / "zone-census.md").write_text(C.render(summary), encoding="utf-8")
    a = summary["all"]
    ff = a["v1_in_figure_or_formula"]
    _console.print(
        f"{a['pages']} pages ({a['pages_ok']} with detections and final lines); "
        f"zones {sum(z['total'] for z in a['zones'].values())}; v1 lines {a['v1_lines']}, "
        f"in figure or formula {ff['lines']} ({ff['share']}); their lines {a['their_lines']} "
        f"(÷ v1 {a['their_to_v1']}); matched at 0.5: {a['matched']['0.5']['pairs']}"
    )
    for b, bl in summary["blocks"].items():
        _console.print(
            f"  {b}: {bl['pages']} pages, v1 {bl['v1_lines']}, theirs {bl['their_lines']}, "
            f"in fig/formula {bl['v1_in_figure_or_formula']['lines']}, "
            f"pages with margin {bl['pages_with_group']['margin']['pages']}"
        )
    _console.print(f"wrote {reports_dir / 'zone-census.md'}")
