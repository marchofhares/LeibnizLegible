"""Row generators + writers for the datasets (Phase D3; the first releases, REL1).

* ``inventory``      (D1, CC0 + CC BY katalog) — works, pages, crosswalk, katalog records
* ``transcriptions`` (D2, CC BY 4.0) — one row per recognised line, the current row
  under the store's rule (corrections, then a scoped run, then the newest), with the
  full §4.5 provenance tuple, NC-derived rows excluded; and, since REL1, the four
  inventory tables beside the lines, so one record carries D2 with D1 inside it
* ``gt``             (D3, CC BY 4.0) — the open deposit of the retro-aligned ground
  truth: lines whose edition text came through a channel with no terms of its own
* ``gt-nc``          (D3, CC BY-NC 4.0) — the NC-derived deposit: lines whose text came
  through a channel with non-commercial terms (the Potsdam Reihe IV PDFs, the GWLB
  repository's PDFs), released separately since 2026-10 (SPECS §7, amendment of
  2026-10-21)

The deposit of a ``gt_lines`` row follows from the channel(s) its ``source`` names
and its licence bucket, through the licence registry
(:func:`leibniz.legal.deposit_for`); a row of a channel the registry does not
release (the letter pool) goes to neither deposit, and the cards count what each
deposit holds by channel and what was left out.

Rows stream from the store, opened read-only by the CLI, and are written a chunk
at a time without a chunk ever being held whole (the lines are 13 million rows of
geometry); Parquet needs ``pyarrow`` (the ``release`` extra), JSONL needs nothing.
Every file's row count and sha256 land in ``MANIFEST.json``, and so does everything
a card states as a number — the lines by model and run, the pages by language, the
deposit census, the scored audit — so that ``leibniz release cards`` re-renders the
cards (with the DOIs, once reserved) from the manifests alone, without the store.
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import sqlite3
import time
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz import __version__, db, legal
from leibniz.align.audit import load_audit_summary
from leibniz.align.pairs import channels_from_source, reader_from_source
from leibniz.release.cards import write_record_files
from leibniz.web.geometry import line_bbox

DATASETS = ("inventory", "transcriptions", "gt", "gt-nc")
GT_DATASETS = {"gt": "open", "gt-nc": "nc"}  # dataset → D3 deposit
DEFAULT_OUT = Path("data/release")
DEFAULT_CHUNK_ROWS = 1_000_000
MANIFEST_VERSION = 2  # 2 (REL1): `tables`, `counts`, `corpus`, `audit`, `deposit_census`
# A verified ground-truth line names its judge in `source` (K3b-prep's audit-apply).
VERIFIED_MARK = "verified leibniz-edition"

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
    tally: Callable[[], Tally] | None = None  # counts the rows as they are written


class Tally:
    """Counts over the rows of one table as they stream to the files; its
    :meth:`summary` goes into ``MANIFEST.json`` under ``counts`` and is what the
    card quotes — a card's numbers are the export's, never a second query's."""

    def add(self, row: dict) -> None:  # pragma: no cover — interface
        raise NotImplementedError

    def summary(self) -> dict:  # pragma: no cover — interface
        raise NotImplementedError


class LinesTally(Tally):
    """The transcription lines by model, by run, by language and by status, and
    the pages that carry a line."""

    def __init__(self) -> None:
        self.by_model: Counter[str] = Counter()
        self.by_run: Counter[tuple[int, str]] = Counter()
        self.by_lang: Counter[str] = Counter()
        self.by_status: Counter[str] = Counter()
        self.by_set: Counter[str] = Counter()
        self.pages = 0
        self._page: str | None = None

    def add(self, row: dict) -> None:
        model = row.get("model") or "(none)"
        self.by_model[model] += 1
        self.by_run[(int(row.get("run_id") or 0), model)] += 1
        self.by_lang[row.get("lang") or "(none)"] += 1
        self.by_status[row.get("status") or "(none)"] += 1
        self.by_set[row.get("set") or "(none)"] += 1
        if row.get("page_id") != self._page:  # rows come grouped by page
            self._page = row.get("page_id")
            self.pages += 1

    def summary(self) -> dict:
        return {
            "by_model": dict(self.by_model.most_common()),
            "by_run": [
                {"run_id": run, "model": model, "lines": n}
                for (run, model), n in sorted(self.by_run.items(), key=lambda kv: -kv[1])
            ],
            "by_lang": dict(self.by_lang.most_common()),
            "by_status": dict(self.by_status.most_common()),
            "by_set": dict(self.by_set.most_common()),
            "pages_with_lines": self.pages,
        }


class GtTally(Tally):
    """A deposit's lines by channel, by stratum and by reader, and the verified ones."""

    def __init__(self) -> None:
        self.by_channel: Counter[str] = Counter()
        self.by_stratum: Counter[str] = Counter()
        self.by_reader: Counter[str] = Counter()
        self.verified = 0
        self.verified_by_channel: Counter[str] = Counter()

    def add(self, row: dict) -> None:
        source = row.get("source")
        label = channel_label(source)
        self.by_channel[label] += 1
        self.by_stratum[row.get("stratum") or "unknown"] += 1
        self.by_reader[reader_from_source(source) or "v1"] += 1
        if VERIFIED_MARK in (source or ""):
            self.verified += 1
            self.verified_by_channel[label] += 1

    def summary(self) -> dict:
        return {
            "by_channel": dict(sorted(self.by_channel.items())),
            "by_stratum": dict(sorted(self.by_stratum.items())),
            "by_reader": dict(self.by_reader.most_common()),
            "verified": self.verified,
            "verified_by_channel": dict(sorted(self.verified_by_channel.items())),
        }


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
    counts: dict[str, dict] = field(default_factory=dict)  # table → its tally's summary
    corpus: dict | None = None  # the store at export time (works, pages, by language…)
    audit: dict | None = None  # the scored hand audit, for the ground-truth cards
    deposit_census: dict | None = None  # what each D3 deposit holds, by channel

    def manifest(self) -> dict:
        return {
            "manifest_version": MANIFEST_VERSION,
            "dataset": self.dataset,
            "format": self.fmt,
            "generated_at": self.generated_at,
            "generator": f"leibniz-legible {__version__} (leibniz release export)",
            "git_sha": self.git_sha,
            "row_counts": self.row_counts,
            "tables": [t.name for t in TABLES[self.dataset]],
            "counts": self.counts,
            "corpus": self.corpus,
            "audit": self.audit,
            "deposit_census": self.deposit_census,
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


TRANSCRIPTIONS_SQL = """
    SELECT l.*, p.work_id, w.set_name, p.image_url, p.image_service_url, p.canvas_id,
           p.width AS p_width, p.height AS p_height
      FROM lines l INDEXED BY ix_lines_page
     CROSS JOIN pages p ON p.page_id = l.page_id
     CROSS JOIN works w ON w.gwlb_object_id = p.work_id
     WHERE l.text IS NOT NULL AND l.text != ''
     ORDER BY l.page_id
"""


def iter_transcriptions(conn: sqlite3.Connection) -> Iterator[dict]:
    """Recognised lines, one per ``(page, line_seq)`` — the current row under the
    store's rule (:func:`leibniz.db.current_lines`: corrections, then a scoped
    run, then the newest), NC rows excluded.

    The rows are read page by page along the ``lines`` index on ``page_id``
    (``CROSS JOIN`` pins that order), so SQLite sorts nothing — the table is
    millions of rows of geometry and a sort of it would be gigabytes of temporary
    file — and Python holds one page's rows at a time: of each line's rows the one
    of the highest rank ``(precedence, run id)`` is written, in reading order.
    """
    prec = db.run_precedences(conn)
    run_at = {
        int(r[0]): (r[2] or r[1])
        for r in conn.execute("SELECT run_id, started_at, finished_at FROM runs")
    }

    def flush(rows: dict[int, tuple[tuple[int, int], dict]]) -> Iterator[dict]:
        for seq in sorted(rows):
            yield rows[seq][1]

    page: str | None = None
    best: dict[int, tuple[tuple[int, int], dict]] = {}
    for r in conn.execute(TRANSCRIPTIONS_SQL):
        source = _j(r["source"])
        if _is_nc(source):
            continue
        if r["page_id"] != page:
            yield from flush(best)
            page, best = r["page_id"], {}
        run = r["run_id"] or 0
        rank = (prec.get(run, 0), run)
        seen = best.get(r["line_seq"])
        if seen is not None and seen[0] > rank:
            continue
        line = db._line_from_row(r)
        bbox = line_bbox(
            line, db.Page(work_id=r["work_id"], seq=0, width=r["p_width"], height=r["p_height"])
        )
        best[line.line_seq] = (
            rank,
            {
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
                "run_at": run_at.get(run),
                "image_uri": r["image_service_url"] or r["image_url"],
                "canvas_id": r["canvas_id"],
                "region_xywh": f"{bbox['x']},{bbox['y']},{bbox['w']},{bbox['h']}" if bbox else None,
                "baseline": line.baseline or [],
                "polygon": line.polygon or [],
                "source": source,
            },
        )
    yield from flush(best)


def gt_deposit(source: str | None, license_bucket: str) -> str | None:
    """The D3 deposit of one ``gt_lines`` row (``"open"``, ``"nc"`` or ``None``)."""
    return legal.deposit_for(channels_from_source(source), license_bucket)


def channel_label(source: str | None) -> str:
    """The channel(s) a row's source names, as one label (``"ia"``, ``"ia+gwlb"``,
    ``"(not recorded)"``)."""
    return "+".join(channels_from_source(source)) or "(not recorded)"


def _iter_gt_deposit(conn: sqlite3.Connection, deposit: str) -> Iterator[dict]:
    """The ground truth of one deposit, one line of text per row: rows minted before
    2026-10 can carry the edition print's own line break inside a manuscript
    line, and a line's ground truth is one line (the factory now mints it so)."""
    cur = conn.execute("SELECT * FROM gt_lines ORDER BY id")
    for r in cur:
        if gt_deposit(r["source"], r["license_bucket"]) != deposit:
            continue
        yield {
            "gt_id": r["id"],
            "line_image_ref": r["line_image_ref"],
            "text": " ".join((r["text"] or "").split()),
            "source": r["source"],
            "stratum": r["stratum"],
            "align_conf": r["align_conf"],
            "license_bucket": r["license_bucket"],
        }


def iter_gt(conn: sqlite3.Connection) -> Iterator[dict]:
    """The open deposit (CC BY 4.0): open-bucket rows whose channels carry no terms."""
    yield from _iter_gt_deposit(conn, "open")


def iter_gt_nc(conn: sqlite3.Connection) -> Iterator[dict]:
    """The NC-derived deposit (CC BY-NC 4.0): rows read through an NC channel."""
    yield from _iter_gt_deposit(conn, "nc")


def gt_deposit_census(conn: sqlite3.Connection) -> dict:
    """What each deposit holds, by channel label, and what no deposit takes —
    ``{"open": {label: n}, "nc": {...}, "none": {...}, "rows": total}``. One pass
    over ``gt_lines``; the cards quote it."""
    census: dict = {"open": {}, "nc": {}, "none": {}, "rows": 0}
    cur = conn.execute("SELECT source, license_bucket FROM gt_lines")
    for source, bucket in cur:
        dep = gt_deposit(source, bucket) or "none"
        label = channel_label(source)
        census[dep][label] = census[dep].get(label, 0) + 1
        census["rows"] += 1
    return census


INVENTORY_TABLES: list[TableSpec] = [
    TableSpec("works", WORKS_SCHEMA, iter_works),
    TableSpec("pages", PAGES_SCHEMA, iter_pages),
    TableSpec("crosswalk", CROSSWALK_SCHEMA, iter_crosswalk),
    TableSpec("katalog_records", KATALOG_SCHEMA, iter_katalog),
]
INVENTORY_TABLE_NAMES = tuple(t.name for t in INVENTORY_TABLES)

TABLES: dict[str, list[TableSpec]] = {
    "inventory": INVENTORY_TABLES,
    # D2 with D1 inside it (REL1; the operator's answer of 2026-11-16): the record of
    # the transcriptions carries the inventory tables beside the lines.
    "transcriptions": [
        TableSpec("lines", LINES_SCHEMA, iter_transcriptions, LinesTally),
        *INVENTORY_TABLES,
    ],
    "gt": [TableSpec("gt_lines", GT_SCHEMA, iter_gt, GtTally)],
    "gt-nc": [TableSpec("gt_lines", GT_SCHEMA, iter_gt_nc, GtTally)],
}


def store_summary(conn: sqlite3.Connection) -> dict:
    """The store at export time, cheaply (no scan of ``lines``): works, pages by
    status, pages by language (K4's ``page_lang``), the reading runs with their
    scope, the catalogue records and the export they were refreshed from (``None``
    while the store holds the website's records), the ground-truth rows. The
    lines themselves are counted as they are written (:class:`LinesTally`)."""
    from leibniz.catalog.holdings import catalog_refreshed

    by_status = dict(conn.execute("SELECT status, COUNT(*) FROM pages GROUP BY status").fetchall())
    scope = "scope" if db.has_column(conn, "runs", "scope") else "NULL"
    runs = [
        {"run_id": int(r[0]), "stage": r[1], "model": r[2], "scope": r[3], "finished_at": r[4]}
        for r in conn.execute(
            f"SELECT run_id, stage, model, {scope}, finished_at FROM runs "
            "WHERE stage IN ('recognize', 'crowd') ORDER BY run_id"
        )
    ]
    return {
        "works": db.count_works(conn),
        "pages": db.count_pages(conn),
        "pages_recognized": int(by_status.get("recognized", 0)),
        "pages_skipped": int(by_status.get("skipped", 0)),
        "pages_by_lang": db.count_page_lang(conn) if db.has_table(conn, "page_lang") else {},
        "reading_runs": runs,
        "katalog": {
            "records": db.count_katalog_records(conn),
            "refreshed": catalog_refreshed(conn),
        },
        "gt_lines": int(conn.execute("SELECT COUNT(*) FROM gt_lines").fetchone()[0]),
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


def _chunks(rows: Iterable[dict], size: int) -> Iterator[Iterator[dict]]:
    """The rows as successive iterators of at most ``size`` rows, none of them
    materialised: a chunk of a million line rows is gigabytes of Python objects,
    and the desktop's budget for one job is 6 GB. Each chunk must be consumed
    before the next is asked for (the writers do)."""
    it = iter(rows)
    for head in it:
        yield itertools.chain([head], itertools.islice(it, max(size, 1) - 1))


def _tallied(rows: Iterable[dict], tally: Tally | None) -> Iterator[dict]:
    for row in rows:
        if tally is not None:
            tally.add(row)
        yield row


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
    dois: dict | None = None,
) -> DatasetExport:
    """Write one dataset (files + MANIFEST.json + README.md + the Zenodo metadata)
    to ``out_root/leibniz-<dataset>``. ``stats`` is the store at export time
    (:func:`store_summary`; computed here when not given); ``dois`` the reserved
    DOIs, where there are any yet (``leibniz release cards`` writes them later)."""
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
    is_gt = dataset in GT_DATASETS
    exp = DatasetExport(
        dataset=dataset,
        out_dir=out_dir,
        fmt=fmt,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        git_sha=git_sha,
        corpus=stats if stats is not None else store_summary(conn),
        audit=load_audit_summary() if is_gt else None,
        deposit_census=gt_deposit_census(conn) if is_gt else None,
    )
    ext = "parquet" if fmt == "parquet" else "jsonl.gz"
    # a re-export into the same folder must not leave an older run's extra chunks
    for stale in out_dir.glob(f"*-[0-9][0-9][0-9][0-9].{ext}"):
        stale.unlink()
    write = write_parquet if fmt == "parquet" else write_jsonl
    for table in TABLES[dataset]:
        tally = table.tally() if table.tally else None
        total = 0
        part = 0
        for chunk in _chunks(_tallied(table.rows(conn), tally), chunk_rows):
            part += 1
            path = out_dir / f"{table.name}-{part:04d}.{ext}"
            n = write(path, chunk, table.schema)
            total += n
            exp.files.append(FileRecord(path.name, n, path.stat().st_size, _sha256(path)))
        if part == 0:  # an empty table still gets an (empty) file so the schema ships
            path = out_dir / f"{table.name}-0001.{ext}"
            write(path, iter([]), table.schema)
            exp.files.append(FileRecord(path.name, 0, path.stat().st_size, _sha256(path)))
        exp.row_counts[table.name] = total
        if tally is not None:
            exp.counts[table.name] = tally.summary()
    manifest = exp.manifest()
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_record_files(out_root, dataset, manifest, dois=dois)
    return exp


def export_all(
    conn: sqlite3.Connection,
    out_root: Path,
    *,
    datasets: tuple[str, ...] = DATASETS,
    fmt: str = "parquet",
    chunk_rows: int = DEFAULT_CHUNK_ROWS,
    stats: dict | None = None,
    dois: dict | None = None,
) -> list[DatasetExport]:
    sha = db.git_sha()
    stats = stats if stats is not None else store_summary(conn)
    return [
        export_dataset(
            conn, d, out_root, fmt=fmt, chunk_rows=chunk_rows, git_sha=sha, stats=stats, dois=dois
        )
        for d in datasets
    ]


__all__ = [
    "DATASETS",
    "DEFAULT_CHUNK_ROWS",
    "DEFAULT_OUT",
    "GT_DATASETS",
    "INVENTORY_TABLES",
    "INVENTORY_TABLE_NAMES",
    "MANIFEST_VERSION",
    "TABLES",
    "VERIFIED_MARK",
    "DatasetExport",
    "FileRecord",
    "GtTally",
    "LinesTally",
    "TableSpec",
    "Tally",
    "channel_label",
    "export_all",
    "export_dataset",
    "gt_deposit",
    "gt_deposit_census",
    "iter_crosswalk",
    "iter_gt",
    "iter_gt_nc",
    "iter_katalog",
    "iter_pages",
    "iter_transcriptions",
    "iter_works",
    "store_summary",
    "write_jsonl",
    "write_parquet",
]
