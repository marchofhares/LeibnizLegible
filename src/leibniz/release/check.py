"""``leibniz release check`` — the checklist's checks on a release folder (REL1).

Reads what was exported, never the store: every file against its manifest (rows,
SHA-256), the transcriptions' counts against themselves and, where the operator
saves the site's ``/api/stats`` to a file, against the live figures; no NC-sourced
line among the transcriptions; every ground-truth row in the deposit the registry
sends it to, the two deposits disjoint and adding up with what neither takes; the
cards carrying their DOIs and the anti-contamination note. One line per check,
``PASS`` or ``FAIL``; the command's exit code is the number of failures (capped).
Parquet files are read a batch at a time.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from leibniz.release import state as S
from leibniz.release.export import GT_DATASETS, gt_deposit

ANTI_CONTAMINATION_MARK = "do not ingest as verified text"
STALE_MARKS = ("8 of 8 sampled", "preliminary (20 of 200)")


@dataclass(slots=True)
class Report:
    lines: list[tuple[bool, str]] = field(default_factory=list)

    def add(self, ok: bool, text: str) -> bool:
        self.lines.append((bool(ok), text))
        return bool(ok)

    @property
    def failures(self) -> int:
        return sum(1 for ok, _ in self.lines if not ok)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_column_rows(path: Path, columns: list[str]) -> Iterator[dict]:
    """The rows of one export file, the named columns only, a batch at a time."""
    if path.name.endswith(".jsonl.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    yield {c: row.get(c) for c in columns}
        return
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(batch_size=50_000, columns=columns):
        yield from batch.to_pylist()


def _manifest(root: Path, dataset: str) -> dict | None:
    path = root / f"leibniz-{dataset}" / "MANIFEST.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _is_nc_source(value: object) -> bool:
    if isinstance(value, str):
        try:
            value = json.loads(value) if value else None
        except json.JSONDecodeError:
            return False
    return isinstance(value, dict) and str(value.get("license_bucket", "")).lower() == "nc"


def check_files(root: Path, dataset: str, manifest: dict, rep: Report) -> None:
    folder = root / f"leibniz-{dataset}"
    bad: list[str] = []
    per_table: dict[str, int] = {}
    for f in manifest.get("files") or []:
        path = folder / f["path"]
        if not path.is_file():
            bad.append(f"{f['path']} missing")
            continue
        if path.stat().st_size != f["bytes"] or _sha256(path) != f["sha256"]:
            bad.append(f"{f['path']} differs from its manifest entry")
        table = f["path"].rsplit("-", 1)[0]
        per_table[table] = per_table.get(table, 0) + int(f["rows"])
    rep.add(
        not bad,
        f"{dataset}: {len(manifest.get('files') or [])} files present with the manifest's "
        f"size and SHA-256" + (f" — {'; '.join(bad[:4])}" if bad else ""),
    )
    rc = manifest.get("row_counts") or {}
    rep.add(
        per_table == {k: int(v) for k, v in rc.items()},
        f"{dataset}: the files' rows add up to the manifest's row counts "
        + ", ".join(f"{k} {v:,}" for k, v in rc.items()),
    )


def check_transcriptions(root: Path, manifest: dict, rep: Report, stats: dict | None) -> None:
    folder = root / "leibniz-transcriptions"
    counts = (manifest.get("counts") or {}).get("lines") or {}
    rows = int((manifest.get("row_counts") or {}).get("lines", 0))
    by_model = {k: int(v) for k, v in (counts.get("by_model") or {}).items()}
    rep.add(
        sum(by_model.values()) == rows,
        f"transcriptions: the lines by model add up to the lines ({rows:,}): "
        + " · ".join(f"{k} {v:,}" for k, v in by_model.items()),
    )
    n = nc = unlabeled = 0
    for f in manifest.get("files") or []:
        if not f["path"].startswith("lines-"):
            continue
        for row in iter_column_rows(folder / f["path"], ["model", "run_id", "status", "source"]):
            n += 1
            nc += _is_nc_source(row.get("source"))
            unlabeled += not (row.get("model") and row.get("run_id") and row.get("status"))
    rep.add(n == rows, f"transcriptions: {n:,} line rows read back from the files")
    rep.add(nc == 0, f"transcriptions: no line with an nc-bucket source ({nc:,} found)")
    rep.add(
        unlabeled == 0,
        f"transcriptions: every line carries model, run_id and status ({unlabeled:,} without)",
    )
    if stats is not None:
        live_lines = int(stats.get("lines") or 0)
        live_models = {k: int(v) for k, v in (stats.get("models") or {}).items()}
        rep.add(
            live_lines == rows,
            f"transcriptions: lines {rows:,} = the site's /api/stats lines {live_lines:,}",
        )
        rep.add(
            live_models == by_model,
            "transcriptions: lines by model = the site's /api/stats models "
            + " · ".join(f"{k} {v:,}" for k, v in live_models.items()),
        )
        live_pages = {k: int(v) for k, v in (stats.get("pages_by_lang") or {}).items()}
        mine = {
            k: int(v)
            for k, v in ((manifest.get("corpus") or {}).get("pages_by_lang") or {}).items()
        }
        rep.add(mine == live_pages, "transcriptions: pages by language = the site's /api/stats")


def check_gt(root: Path, rep: Report) -> None:
    ids: dict[str, set[int]] = {}
    census: dict | None = None
    corpus_rows: int | None = None
    for dataset, deposit in GT_DATASETS.items():
        manifest = _manifest(root, dataset)
        if manifest is None:
            continue
        census = manifest.get("deposit_census") or census
        corpus_rows = (manifest.get("corpus") or {}).get("gt_lines", corpus_rows)
        folder = root / f"leibniz-{dataset}"
        seen: set[int] = set()
        wrong = not_open = 0
        for f in manifest.get("files") or []:
            for row in iter_column_rows(folder / f["path"], ["gt_id", "source", "license_bucket"]):
                seen.add(int(row["gt_id"]))
                not_open += row.get("license_bucket") != "open"
                wrong += gt_deposit(row.get("source"), row.get("license_bucket")) != deposit
        ids[dataset] = seen
        rep.add(
            wrong == 0,
            f"{dataset}: every row belongs to the {deposit} deposit by its channel "
            f"({len(seen):,} rows, {wrong:,} misplaced)",
        )
        rep.add(not_open == 0, f"{dataset}: every row is open-bucket ({not_open:,} are not)")
    if len(ids) == 2:
        overlap = len(ids["gt"] & ids["gt-nc"])
        rep.add(overlap == 0, f"gt and gt-nc are disjoint by gt_id ({overlap:,} shared)")
        if census:
            neither = sum((census.get("none") or {}).values())
            total = len(ids["gt"]) + len(ids["gt-nc"]) + neither
            rep.add(
                total == int(census.get("rows", -1)) and (corpus_rows in (None, total)),
                f"gt {len(ids['gt']):,} + gt-nc {len(ids['gt-nc']):,} + released in neither "
                f"{neither:,} = the store's gt_lines {int(census.get('rows', 0)):,}",
            )


def check_cards(root: Path, rep: Report, release: dict) -> None:
    dois = S.dois(release)
    for record in S.RECORDS:
        folder = root / S.folder_name(record, release)
        card = folder / "README.md"
        if not card.exists():
            continue
        text = card.read_text(encoding="utf-8")
        rep.add(text.startswith("---\n"), f"{record}: the card opens with the Hub front matter")
        rep.add(
            ANTI_CONTAMINATION_MARK in text,
            f"{record}: the card carries the anti-contamination note",
        )
        stale = [m for m in STALE_MARKS if m in text]
        rep.add(
            not stale,
            f"{record}: the card quotes no stand-in audit" + (f" ({stale})" if stale else ""),
        )
        if record in dois:
            rep.add(dois[record] in text, f"{record}: the card carries doi:{dois[record]}")
        else:
            rep.add(
                "to be assigned at deposit" in text,
                f"{record}: no DOI reserved yet, and the card says so",
            )
        deposit = root / f"{S.folder_name(record, release)}.zenodo.json"
        if deposit.exists():
            data = json.loads(deposit.read_text(encoding="utf-8"))
            missing = [
                f["path"] for f in data.get("files") or [] if not (root / f["path"]).is_file()
            ]
            rep.add(
                not missing,
                f"{record}: the deposit file's {len(data.get('files') or [])} files are there"
                + (f" — missing {missing[:3]}" if missing else ""),
            )


def check_model(root: Path, rep: Report, release: dict) -> None:
    """The model package: its files against its manifest, and the zip against both."""
    import zipfile

    name = S.folder_name("model", release)
    folder = root / name
    path = folder / "MANIFEST.json"
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    bad = [
        f["path"]
        for f in manifest.get("files") or []
        if not (folder / f["path"]).is_file()
        or (folder / f["path"]).stat().st_size != f["bytes"]
        or _sha256(folder / f["path"]) != f["sha256"]
    ]
    rep.add(
        not bad,
        f"model: {len(manifest.get('files') or [])} files present with the manifest's size and "
        "SHA-256" + (f" — {bad[:4]}" if bad else ""),
    )
    zip_path = root / f"{name}.zip"
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as z:
            inside = {i.filename: i.file_size for i in z.infolist()}
        want = {f"{name}/{f['path']}": f["bytes"] for f in manifest.get("files") or []}
        want[f"{name}/README.md"] = (folder / "README.md").stat().st_size
        differ = [k for k, v in want.items() if inside.get(k) != v]
        rep.add(
            not differ,
            f"model: {zip_path.name} holds the folder's files at their sizes"
            + (f" — {differ[:3]} differ: build the package again" if differ else ""),
        )
    else:
        rep.add(
            False, f"model: {zip_path.name} is missing (leibniz release model without --no-zip)"
        )


def check_release(root: Path, *, stats: dict | None = None) -> Report:
    """Every check on the release folder ``root``; ``stats`` is the site's
    ``/api/stats`` answer, where the operator saved one."""
    root = Path(root)
    rep = Report()
    release = S.load_release(root)
    found = False
    for dataset in ("inventory", "transcriptions", "gt", "gt-nc"):
        manifest = _manifest(root, dataset)
        if manifest is None:
            continue
        found = True
        check_files(root, dataset, manifest, rep)
        if dataset == "transcriptions":
            check_transcriptions(root, manifest, rep, stats)
    rep.add(found, f"a dataset folder with a MANIFEST.json lies under {root}")
    check_gt(root, rep)
    check_model(root, rep, release)
    check_cards(root, rep, release)
    return rep


__all__ = ["Report", "check_release", "iter_column_rows"]
