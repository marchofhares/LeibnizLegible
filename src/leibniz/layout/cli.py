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


# --------------------------------------------------------------------------- #
# M1 Task 1b — the print trial
# --------------------------------------------------------------------------- #

trial_app = typer.Typer(
    help="M1 Task 1b: the print trial on the Marginalien block.", no_args_is_help=True
)
app.add_typer(trial_app, name="print-trial")

PRINT_DIR = Path("data/print")
PRINT_REPORTS = Path("reports/marginalia")
PRINT_PAGES_CSV = PRINT_REPORTS / "print-trial-pages.csv"
PRINT_ZONES = PRINT_DIR / "zones"
PRINT_PILOT = PRINT_DIR / "trial.json"


@trial_app.command("pages")
def trial_pages(
    sample_csv: Path = typer.Option(SAMPLE_CSV, "--sample"),
    out: Path = typer.Option(PRINT_PAGES_CSV, "--out"),
    images_dir: Path = typer.Option(
        SAMPLE_DIR / "images-2000", "--images-dir", help="The census's downscaled copies."
    ),
    link_dir: Path = typer.Option(
        PRINT_DIR / "images-2000", "--link-dir", help="Where the trial's copies are linked."
    ),
) -> None:
    """The 100 Marginalien pages of the census sample, listed, their copies linked."""
    from leibniz.layout import print_trial as T
    from leibniz.layout.sample import read_sample

    rows = [r for r in read_sample(sample_csv) if r.block == "marginalien"]
    T.write_pages_csv(rows, out)
    link_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in rows:
        src = (images_dir / r.file).resolve()
        dst = link_dir / r.file
        if src.exists():
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            dst.symlink_to(src)
            n += 1
    by_type = {}
    for r in rows:
        by_type[T.type_of(r.sub)] = by_type.get(T.type_of(r.sub), 0) + 1
    _console.print(f"{len(rows)} pages ({by_type}) → {out}; {n} copies linked into {link_dir}")


@trial_app.command("census")
def trial_census(
    zones_dir: Path = typer.Option(PRINT_ZONES, "--zones", help="kraken's PAGE XML per page."),
    pages_csv: Path = typer.Option(SAMPLE_CSV, "--sample"),
    philiumm_results: Path = typer.Option(
        Path("data/philiumm/layout-results"), "--philiumm", help="P1's results (the comparison)."
    ),
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db"),
    out: Path = typer.Option(PRINT_PILOT, "--out", help="The per-page results (JSON)."),
    lines_csv: Path = typer.Option(PRINT_DIR / "print-trial-lines.csv", "--lines-csv"),
) -> None:
    """Zones per class, the printed-body share, the lines' calls by both models."""
    from leibniz.layout import print_trial as T
    from leibniz.layout.sample import read_sample

    conn = _ro(db_path)
    rows = [r for r in read_sample(pages_csv) if r.block == "marginalien"]
    pages = T.trial(
        conn,
        rows,
        zones_dir,
        philiumm_results=philiumm_results if philiumm_results.exists() else None,
        progress=lambda k, n, pid: _console.print(f"  {k}/{n} {pid}") if k % 25 == 0 else None,
    )
    T.write_json(T.pages_to_json(pages), out)
    T.write_lines_csv(pages, lines_csv)
    summ = T.summarize(pages)
    a = summ["all"]
    _console.print(
        f"{a['pages']} pages, {a['pages_with_zones']} with zones; v1 lines {a['v1_lines']}, "
        f"in print {a['v1_by_group']['print']['lines']} ({a['print_body_share_of_lines']}), "
        f"in manuscript zones {a['v1_by_group']['manuscript']['lines']}; "
        f"pages with a manuscript zone {a['pages_with_manuscript_zone']}; "
        f"IoU lines/print zones mean {a['iou_lines_print_mean']}; "
        f"PHILIUMM same call {a['philiumm']['same_call']}"
    )
    _console.print(f"wrote {out} and {lines_csv}")


@trial_app.command("sheet")
def trial_sheet(
    trial_json: Path = typer.Option(PRINT_PILOT, "--trial"),
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db"),
    images: Path = typer.Option(Path(DEFAULT_IMAGES_ROOT), "--images"),
    out_html: Path = typer.Option(PRINT_DIR / "print-sheet.html", "--out"),
    lines_out: Path = typer.Option(PRINT_DIR / "print-sheet-lines.csv", "--lines-out"),
    per_type: int = typer.Option(25, "--per-type"),
    seed: int = typer.Option(0, "--seed"),
) -> None:
    """The sheet of 50 printed lines (25 roman, 25 Fraktur) for the operator."""
    from leibniz.layout import print_trial as T

    conn = _ro(db_path)
    pages = _trial_pages_from_json(trial_json, conn)
    lines = T.select_sheet_lines(pages, per_type=per_type, seed=seed)
    crops = T.crops_for(conn, lines, images)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(T.render_sheet(lines, crops, seed=seed), encoding="utf-8")
    T.write_sheet_lines(lines, lines_out)
    by = {}
    for ln in lines:
        by[ln.print_type] = by.get(ln.print_type, 0) + 1
    _console.print(
        f"{len(lines)} lines ({by}), {sum(1 for v in crops.values() if v)} crops → "
        f"{out_html.resolve()} ; the list in {lines_out}"
    )


def _trial_pages_from_json(path: Path, conn):
    """The per-page results back from JSON, their lines re-read from the store
    (the JSON leaves the per-line calls out; the lines CSV carries them)."""
    import csv as _csv

    from leibniz.layout import print_trial as T

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    pages = []
    for d in data:
        pt = T.PageTrial(
            d["page_id"],
            d["work_id"],
            d["label"],
            d["lang"],
            d["print_type"],
            d["file"],
            d["status"],
            d.get("scale"),
            d.get("zones", {}),
            d.get("area", {}),
            d.get("v1_lines", 0),
            d.get("v1_by_group", {}),
            d.get("v1_by_philiumm", {}),
            d.get("agreement", {}),
            d.get("iou_lines_print"),
            d.get("iou_print_models"),
        )
        pages.append(pt)
    lines_csv = Path(path).with_name("print-trial-lines.csv")
    if lines_csv.exists():
        by_page = {p.page_id: p for p in pages}
        with lines_csv.open(encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                p = by_page.get(r["page_id"])
                if p is not None:
                    p.lines.append(
                        T.LineCall(
                            int(r["ref"].rsplit(":", 1)[1]),
                            r["ladas"],
                            r["philiumm"],
                            r["v1_text"],
                            float(r["conf"]) if r["conf"] else None,
                        )
                    )
    return pages


@trial_app.command("ocr-input")
def trial_ocr_input(
    trial_json: Path = typer.Option(PRINT_PILOT, "--trial"),
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db"),
    images: Path = typer.Option(Path(DEFAULT_IMAGES_ROOT), "--images"),
    out_dir: Path = typer.Option(PRINT_DIR / "ocr-input", "--out-dir"),
) -> None:
    """One PAGE XML per page with the v1 lines inside print zones, for kraken ocr."""
    from leibniz import db
    from leibniz.images.fetch import local_relpath
    from leibniz.layout import print_trial as T

    conn = _ro(db_path)
    pages = _trial_pages_from_json(trial_json, conn)
    prec = db.run_precedences(conn)
    n_pages = n_lines = 0
    for pt in pages:
        if pt.status != "ok":
            continue
        page = db.get_page(conn, pt.page_id)
        if page is None:
            continue
        img = images / (page.local_path or local_relpath(page))
        n = T.write_ocr_input(
            conn, pt, img, out_dir / f"{Path(pt.file).stem}.xml", precedences=prec
        )
        n_pages += 1
        n_lines += n
    _console.print(f"{n_pages} PAGE XML files, {n_lines} printed-body lines → {out_dir}")


@trial_app.command("cer")
def trial_cer(
    transcriptions: Path = typer.Option(..., "--transcriptions", help="The operator's CSV."),
    lines_csv: Path = typer.Option(PRINT_DIR / "print-sheet-lines.csv", "--lines"),
    ocr_dir: Path = typer.Option(PRINT_DIR / "ocr", "--ocr", help="kraken's OCR output per page."),
    out: Path = typer.Option(PRINT_DIR / "print-cer.json", "--out"),
    policy: str = typer.Option("philiumm", "--policy"),
) -> None:
    """The CER of Gallicorpora+ and of v1 on the sheet's lines, roman and Fraktur apart."""
    from leibniz.layout import print_trial as T

    lines = T.read_sheet_lines(lines_csv)
    refs = T.read_transcriptions(transcriptions)
    ocr: dict[str, str] = {}
    for xml in sorted(Path(ocr_dir).glob("*.xml")):
        ocr.update(T.read_ocr_texts(xml))
    v1 = {ln.ref: ln.v1_text for ln in lines}
    result = {
        "transcriptions": str(transcriptions),
        "gallicorpora": T.score(refs, ocr, lines, policy=policy),
        "v1": T.score(refs, v1, lines, policy=policy),
    }
    T.write_json(result, out)
    _console.print(json.dumps(result, indent=1, ensure_ascii=False))


@trial_app.command("report")
def trial_report(
    trial_json: Path = typer.Option(PRINT_PILOT, "--trial"),
    cer_json: Path = typer.Option(PRINT_DIR / "print-cer.json", "--cer"),
    db_path: str = typer.Option(str(DEFAULT_DB_PATH), "--db"),
    reports_dir: Path = typer.Option(PRINT_REPORTS, "--reports-dir"),
    meta_json: Path = typer.Option(PRINT_DIR / "trial-meta.json", "--meta"),
    ocr_dir: Path = typer.Option(PRINT_DIR / "ocr", "--ocr"),
) -> None:
    """reports/marginalia/print-trial.md with the decision, the summary JSON, the per-page CSV."""
    from leibniz.layout import print_report as R
    from leibniz.layout import print_trial as T

    conn = _ro(db_path)
    pages = _trial_pages_from_json(trial_json, conn)
    meta = json.loads(meta_json.read_text(encoding="utf-8")) if meta_json.exists() else {}
    cer = json.loads(cer_json.read_text(encoding="utf-8")) if cer_json.exists() else None
    summ = T.summarize(pages, meta)
    summ["cer"] = cer
    summ["ocr_lines"] = sum(len(T.read_ocr_texts(x)) for x in sorted(Path(ocr_dir).glob("*.xml")))
    summ["fraktur_share_corpus"] = R.fraktur_share(conn)
    reports_dir.mkdir(parents=True, exist_ok=True)
    T.write_per_page(pages, reports_dir / "print-trial-per-page.csv")
    T.write_json(summ, reports_dir / "print-trial-summary.json")
    (reports_dir / "print-trial.md").write_text(R.render(summ), encoding="utf-8")
    _console.print(f"wrote {reports_dir / 'print-trial.md'}; decision: {R.decision(summ)[0]}")
