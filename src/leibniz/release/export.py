"""Row generators + writers for the three datasets (Phase D3).

* ``inventory``      (D1, CC0 + CC BY katalog) — works, pages, crosswalk, katalog records
* ``transcriptions`` (D2, CC BY 4.0) — one row per recognised line, latest run per
  line, with the full §4.5 provenance tuple; NC-derived rows excluded
* ``gt``             (D3, CC BY 4.0) — the retro-aligned ground truth, open bucket only

Rows stream from the store; Parquet needs ``pyarrow`` (the ``release`` extra),
JSONL needs nothing. Every file's row count and sha256 land in ``MANIFEST.json``.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz import __version__, db
from leibniz.release.cards import render_card
from leibniz.web.geometry import line_bbox

DATASETS = ("inventory", "transcriptions", "gt")
DEFAULT_OUT = Path("data/release")
DEFAULT_CHUNK_ROWS = 1_000_000

# Arrow-ish logical types, mapped by the parquet writer; JSONL ignores them.
Schema = list[tuple[str, str]]

WORKS_SCHEMA: Schema = [
    ("work_id", "string"),
    ("set", "string"),
    ("title", "string"),
    ("shelfmarks", "json"),
    ("manifest_url", "string"),
    ("n_canvases", "int64"),
    ("metadata", "json"),
]
PAGES_SCHEMA: Schema = [
    ("page_id", "string"),
    ("work_id", "string"),
    ("seq", "int64"),
    ("canvas_id", "string"),
    ("label", "string"),
    ("image_service_url", "string"),
    ("image_url", "string"),
    ("thumb_url", "string"),
    ("delivery", "string"),
    ("width", "int64"),
    ("height", "int64"),
    ("status", "string"),
    ("skip_reason", "string"),
]
CROSSWALK_SCHEMA: Schema = [
    ("katalog_record_id", "string"),
    ("work_id", "string"),
    ("page_range", "string"),
    ("match_method", "string"),
    ("match_conf", "double"),
]
KATALOG_SCHEMA: Schema = [
    ("record_id", "string"),
    ("shelfmark_refs", "json"),
    ("aa_refs", "json"),
    ("metadata", "json"),
]
LINES_SCHEMA: Schema = [
    ("line_id", "string"),
    ("page_id", "string"),
    ("work_id", "string"),
    ("set", "string"),
    ("line_seq", "int64"),
    ("text", "string"),
    ("conf", "double"),
    ("status", "string"),
    ("lang", "string"),
    ("model", "string"),
    ("run_id", "int64"),
    ("run_at", "string"),
    ("image_uri", "string"),
    ("canvas_id", "string"),
    ("region_xywh", "string"),
    ("baseline", "json"),
    ("polygon", "json"),
    ("source", "json"),
]
GT_SCHEMA: Schema = [
    ("gt_id", "int64"),
    ("line_image_ref", "string"),
    ("text", "string"),
    ("source", "string"),
    ("stratum", "string"),
    ("align_conf", "double"),
    ("license_bucket", "string"),
]


@dataclass(slots=True)
class TableSpec:
    name: str
    schema: Schema
    rows: Callable[[sqlite3.Connection], Iterator[dict]]


@dataclass(slots=True)
class FileRecord:
    path: str
    rows: int
    bytes: int
    sha256: str


@dataclass(slots=True)
class DatasetExport:
    dataset: str
    out_dir: Path
    fmt: str
    files: list[FileRecord] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    generated_at: str = ""
    git_sha: str | None = None

    def manifest(self) -> dict:
        return {
            "dataset": self.dataset,
            "format": self.fmt,
            "generated_at": self.generated_at,
            "generator": f"leibniz-legible {__version__} (leibniz release export)",
            "git_sha": self.git_sha,
            "row_counts": self.row_counts,
            "files": [asdict(f) for f in self.files],
        }


# --------------------------------------------------------------------------- #
# Row generators
# --------------------------------------------------------------------------- #


def _j(value: object) -> object:
    return json.loads(value) if isinstance(value, str) and value else (value or None)


def iter_works(conn: sqlite3.Connection) -> Iterator[dict]:
    for w in db.iter_works(conn):
        yield {
            "work_id": w.gwlb_object_id,
            "set": w.set_name,
            "title": w.title,
            "shelfmarks": list(w.shelfmarks or []),
            "manifest_url": w.manifest_url,
            "n_canvases": w.n_canvases,
            "metadata": w.metadata or {},
        }


def iter_pages(conn: sqlite3.Connection) -> Iterator[dict]:
    cur = conn.execute("SELECT * FROM pages ORDER BY work_id, seq")
    for r in cur:
        yield {
            "page_id": r["page_id"],
            "work_id": r["work_id"],
            "seq": r["seq"],
            "canvas_id": r["canvas_id"],
            "label": r["label"],
            "image_service_url": r["image_service_url"],
            "image_url": r["image_url"],
            "thumb_url": r["thumb_url"],
            "delivery": r["delivery"],
            "width": r["width"],
            "height": r["height"],
            "status": r["status"],
            "skip_reason": r["skip_reason"],
        }


def iter_crosswalk(conn: sqlite3.Connection) -> Iterator[dict]:
    cur = conn.execute("SELECT * FROM crosswalk ORDER BY work_id, katalog_record_id")
    for r in cur:
        yield {
            "katalog_record_id": r["katalog_record_id"],
            "work_id": r["work_id"],
            "page_range": r["page_range"],
            "match_method": r["match_method"],
            "match_conf": r["match_conf"],
        }


def iter_katalog(conn: sqlite3.Connection) -> Iterator[dict]:
    cur = conn.execute("SELECT * FROM katalog_records ORDER BY record_id")
    for r in cur:
        yield {
            "record_id": r["record_id"],
            "shelfmark_refs": _j(r["shelfmark_refs"]) or [],
            "aa_refs": _j(r["aa_refs"]) or [],
            "metadata": _j(r["metadata"]) or {},
        }


def _is_nc(source: dict | None) -> bool:
    return bool(source) and str(source.get("license_bucket", "")).lower() == "nc"


def iter_transcriptions(conn: sqlite3.Connection) -> Iterator[dict]:
    """Recognised lines, one per ``(page, line_seq)`` (latest run), NC rows excluded."""
    cur = conn.execute(
        """
        SELECT l.*, p.work_id, w.set_name, p.image_url, p.image_service_url, p.canvas_id,
               p.width AS p_width, p.height AS p_height, r.started_at, r.finished_at
          FROM lines l
          JOIN pages p ON p.page_id = l.page_id
          JOIN works w ON w.gwlb_object_id = p.work_id
          LEFT JOIN runs r ON r.run_id = l.run_id
         WHERE l.text IS NOT NULL AND l.text != ''
         ORDER BY l.page_id, l.line_seq, l.run_id
        """
    )
    pending: dict | None = None
    key: tuple[str, int] | None = None
    for r in cur:
        source = _j(r["source"])
        if _is_nc(source):
            continue
        line = db._line_from_row(r)
        page = db.Page(work_id=r["work_id"], seq=0, width=r["p_width"], height=r["p_height"])
        bbox = line_bbox(line, page)
        row = {
            "line_id": line.id,
            "page_id": line.page_id,
            "work_id": r["work_id"],
            "set": r["set_name"],
            "line_seq": line.line_seq,
            "text": line.text,
            "conf": line.conf,
            "status": line.status,
            "lang": line.lang,
            "model": line.model,
            "run_id": line.run_id,
            "run_at": r["finished_at"] or r["started_at"],
            "image_uri": r["image_service_url"] or r["image_url"],
            "canvas_id": r["canvas_id"],
            "region_xywh": f"{bbox['x']},{bbox['y']},{bbox['w']},{bbox['h']}" if bbox else None,
            "baseline": line.baseline or [],
            "polygon": line.polygon or [],
            "source": source,
        }
        k = (line.page_id, line.line_seq)
        if key is not None and k != key and pending is not None:
            yield pending
        key, pending = k, row  # rows are ordered by run_id, so the last one wins
    if pending is not None:
        yield pending


def iter_gt(conn: sqlite3.Connection) -> Iterator[dict]:
    cur = conn.execute("SELECT * FROM gt_lines WHERE license_bucket = 'open' ORDER BY id")
    for r in cur:
        yield {
            "gt_id": r["id"],
            "line_image_ref": r["line_image_ref"],
            "text": r["text"],
            "source": r["source"],
            "stratum": r["stratum"],
            "align_conf": r["align_conf"],
            "license_bucket": r["license_bucket"],
        }


TABLES: dict[str, list[TableSpec]] = {
    "inventory": [
        TableSpec("works", WORKS_SCHEMA, iter_works),
        TableSpec("pages", PAGES_SCHEMA, iter_pages),
        TableSpec("crosswalk", CROSSWALK_SCHEMA, iter_crosswalk),
        TableSpec("katalog_records", KATALOG_SCHEMA, iter_katalog),
    ],
    "transcriptions": [TableSpec("lines", LINES_SCHEMA, iter_transcriptions)],
    "gt": [TableSpec("gt_lines", GT_SCHEMA, iter_gt)],
}


# --------------------------------------------------------------------------- #
# Writers
# --------------------------------------------------------------------------- #


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(row: dict, schema: Schema) -> dict:
    out = {}
    for name, _typ in schema:
        out[name] = row.get(name)
    return out


def write_jsonl(path: Path, rows: Iterator[dict], schema: Schema) -> int:
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(_jsonable(row, schema), ensure_ascii=False))
            f.write("\n")
            n += 1
    return n


def _arrow_schema(schema: Schema):
    import pyarrow as pa

    kinds = {
        "string": pa.string(),
        "json": pa.string(),
        "int64": pa.int64(),
        "double": pa.float64(),
    }
    return pa.schema([pa.field(name, kinds[typ]) for name, typ in schema])


def _arrow_row(row: dict, schema: Schema) -> dict:
    out = {}
    for name, typ in schema:
        v = row.get(name)
        if typ == "json":
            v = json.dumps(v, ensure_ascii=False) if v is not None else None
        out[name] = v
    return out


def write_parquet(path: Path, rows: Iterator[dict], schema: Schema, *, batch: int = 50_000) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    aschema = _arrow_schema(schema)
    n = 0
    buf: list[dict] = []
    with pq.ParquetWriter(path, aschema, compression="zstd") as writer:
        for row in rows:
            buf.append(_arrow_row(row, schema))
            if len(buf) >= batch:
                writer.write_batch(pa.RecordBatch.from_pylist(buf, schema=aschema))
                n += len(buf)
                buf.clear()
        if buf:
            writer.write_batch(pa.RecordBatch.from_pylist(buf, schema=aschema))
            n += len(buf)
    return n


def _chunks(rows: Iterator[dict], size: int) -> Iterator[list[dict]]:
    chunk: list[dict] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def export_dataset(
    conn: sqlite3.Connection,
    dataset: str,
    out_root: Path,
    *,
    fmt: str = "parquet",
    chunk_rows: int = DEFAULT_CHUNK_ROWS,
    git_sha: str | None = None,
    stats: dict | None = None,
) -> DatasetExport:
    """Write one dataset (files + MANIFEST.json + README.md) to ``out_root/leibniz-<dataset>``."""
    if dataset not in TABLES:
        raise ValueError(f"unknown dataset {dataset!r}; expected one of {DATASETS}")
    if fmt not in ("parquet", "jsonl"):
        raise ValueError("fmt must be 'parquet' or 'jsonl'")
    if fmt == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ModuleNotFoundError as exc:  # pragma: no cover — environment-dependent
            raise RuntimeError(
                "Parquet export needs pyarrow (uv sync --extra release); use --format jsonl"
            ) from exc
    out_dir = out_root / f"leibniz-{dataset}"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = DatasetExport(
        dataset=dataset,
        out_dir=out_dir,
        fmt=fmt,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        git_sha=git_sha,
    )
    ext = "parquet" if fmt == "parquet" else "jsonl.gz"
    for table in TABLES[dataset]:
        total = 0
        part = 0
        for chunk in _chunks(table.rows(conn), chunk_rows):
            part += 1
            path = out_dir / f"{table.name}-{part:04d}.{ext}"
            if fmt == "parquet":
                n = write_parquet(path, iter(chunk), table.schema)
            else:
                n = write_jsonl(path, iter(chunk), table.schema)
            total += n
            exp.files.append(FileRecord(path.name, n, path.stat().st_size, _sha256(path)))
        if part == 0:  # an empty table still gets an (empty) file so the schema ships
            path = out_dir / f"{table.name}-0001.{ext}"
            if fmt == "parquet":
                write_parquet(path, iter([]), table.schema)
            else:
                write_jsonl(path, iter([]), table.schema)
            exp.files.append(FileRecord(path.name, 0, path.stat().st_size, _sha256(path)))
        exp.row_counts[table.name] = total
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(exp.manifest(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "README.md").write_text(
        render_card(dataset, TABLES[dataset], exp, stats=stats), encoding="utf-8"
    )
    return exp


def export_all(
    conn: sqlite3.Connection,
    out_root: Path,
    *,
    datasets: tuple[str, ...] = DATASETS,
    fmt: str = "parquet",
    chunk_rows: int = DEFAULT_CHUNK_ROWS,
    stats: dict | None = None,
) -> list[DatasetExport]:
    sha = db.git_sha()
    return [
        export_dataset(conn, d, out_root, fmt=fmt, chunk_rows=chunk_rows, git_sha=sha, stats=stats)
        for d in datasets
    ]


__all__ = [
    "DATASETS",
    "DEFAULT_CHUNK_ROWS",
    "DEFAULT_OUT",
    "TABLES",
    "DatasetExport",
    "FileRecord",
    "TableSpec",
    "export_all",
    "export_dataset",
    "iter_crosswalk",
    "iter_gt",
    "iter_katalog",
    "iter_pages",
    "iter_transcriptions",
    "iter_works",
    "write_jsonl",
    "write_parquet",
]
