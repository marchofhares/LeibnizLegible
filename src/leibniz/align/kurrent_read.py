"""K2's reading job: every line of the German pieces' pages, read by one Kurrent reader.

K1 chose the reader (`trocr-kurrent-xvi-xvii`, the Bern TrOCR model, MIT) on
a pilot of twenty pieces; K2 reads **every** recognised line on the pages of
the census's German pieces (``data/kurrent/german_pieces.jsonl``) with it, so
that the factory can mint the edition's text from a reading that knows
Kurrent. The readings go to ``data/kurrent/k2-readings/<reader>.jsonl`` in the
pilot's row format (``line_id, text, conf, model, device, ms``), one row per
line, appended page by page, resumable: a fresh run reads what the file does
not hold. Nothing here touches the store's ``lines`` table — K2 adds ground
truth, not a reading — and the store is opened read-only.

The pages are the union of two placements: the pages the K1 census put the
pieces on (its ``page_ids``) and the pages the factory's resolver gives the
same catalogue records today (W5's folio sides, the rebuilt edition cache),
so the mint of Task 3 finds a reading on every line it can place.

Throughput first (the amendment of 2026-10-10): the pilot read a line in 353
ms, most of it outside the model. Here each page image is decoded once, the
lines are cut in memory (:func:`leibniz.align.audit.crop_image`, the polygon
masked, as the pilot cut them) and handed to the engine as images, the
page's lines ordered by width so a batch's generation steps are spent on
lines of like length; :func:`profile_batch` says where the time goes and
:func:`sweep` measures lines per second at several batch sizes and
precisions on a sample of the job's own lines. Lines without geometry and
pages without a cached image are skipped and counted by reason; the skipped
line ids are kept beside the readings.
"""

from __future__ import annotations

import io
import json
import sqlite3
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

from leibniz.align.audit import CROP_PAD, crop_image
from leibniz.align.factory import select_text_pieces
from leibniz.align.kurrent_pilot import (
    DEFAULT_IMAGES_ROOT,
    PilotLine,
    Reading,
    append_readings,
    load_readings,
    page_image_path,
    page_lines,
    release,
)
from leibniz.align.resolve import resolve_canvases
from leibniz.align.volumes import PieceRef, enumerate_pieces

DEFAULT_READER = "trocr-kurrent-xvi-xvii"
DEFAULT_READINGS_DIR = Path("data/kurrent/k2-readings")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
LOG_EVERY_S = 180.0
SWEEP_LINES = 2000
SWEEP_BATCHES = (8, 16, 32)
SKIP_REASONS = ("no_image", "image_unreadable", "no_geometry", "outside_image")


# --------------------------------------------------------------------------- #
# The pages
# --------------------------------------------------------------------------- #


def german_piece_refs(
    conn: sqlite3.Connection,
    record_ids: Iterable[str],
    *,
    refs: Mapping[str, Sequence[Mapping]] | None = None,
    today: date | None = None,
) -> dict[str, PieceRef]:
    """The factory's piece for each catalogue record, as the factory would mint it
    today: one piece per record, under the volume its edition text came from
    (:func:`~leibniz.align.factory.select_text_pieces` with the cache's refs)."""
    wanted = set(record_ids)
    pieces, _ = enumerate_pieces(conn, today=today or date.today())
    if refs:
        pieces = select_text_pieces(pieces, refs)
    out: dict[str, PieceRef] = {}
    for p in pieces:
        if p.record_id in wanted and p.record_id not in out:
            out[p.record_id] = p
    return out


def resolve_pages(conn: sqlite3.Connection, piece: PieceRef) -> list[str]:
    """The page ids the factory's resolver gives a localizable piece (else none)."""
    if not piece.localizable:
        return []
    assert piece.work_id is not None and piece.folio_range is not None
    res = resolve_canvases(
        conn,
        piece.work_id,
        piece.folio_range[0],
        piece.folio_range[1],
        side_lo=piece.folio_sides[0],
        side_hi=piece.folio_sides[1],
    )
    return [pg.id for pg in res.pages]


@dataclass(slots=True)
class ReadPlan:
    """The pages the job reads, and how the two placements compare."""

    pages: list[str]  # ordered by work and canvas
    records_by_page: dict[str, list[str]]
    n_records: int
    n_records_with_lines: int  # census rows with recognised lines
    n_records_localizable_now: int
    n_pages_census: int
    n_pages_resolver: int
    n_pages_only_census: int
    n_pages_only_resolver: int
    n_same: int = 0  # records whose page set is the same under both placements
    n_narrowed: int = 0
    n_widened: int = 0
    n_other: int = 0
    n_moved_volume: int = 0
    n_lines: int = 0  # recognised lines on the pages

    @property
    def n_pages(self) -> int:
        return len(self.pages)

    def as_dict(self) -> dict:
        d = asdict(self)
        d.pop("pages")
        d.pop("records_by_page")
        d["n_pages"] = self.n_pages
        return d


def plan_pages(
    conn: sqlite3.Connection,
    rows: Sequence[Mapping],
    *,
    refs: Mapping[str, Sequence[Mapping]] | None = None,
    today: date | None = None,
    resolve: bool = True,
) -> ReadPlan:
    """The union of the census's pages and the factory's for the German pieces."""
    census: dict[str, set[str]] = {}
    volumes: dict[str, str] = {}
    for r in rows:
        rid = str(r["record_id"])
        census.setdefault(rid, set()).update(str(p) for p in r.get("page_ids") or [])
        volumes[rid] = str(r.get("volume_label") or "")
    resolver: dict[str, set[str]] = {rid: set() for rid in census}
    n_loc = n_moved = 0
    if resolve:
        for rid, piece in german_piece_refs(conn, census, refs=refs, today=today).items():
            if piece.localizable:
                n_loc += 1
            resolver[rid] = set(resolve_pages(conn, piece))
            if volumes.get(rid) and piece.volume_label != volumes[rid]:
                n_moved += 1
    records_by_page: dict[str, list[str]] = {}
    for rid in census:
        for pid in census[rid] | resolver[rid]:
            records_by_page.setdefault(pid, []).append(rid)
    pages = sorted(records_by_page)
    all_census = set().union(*census.values()) if census else set()
    all_res = set().union(*resolver.values()) if resolver else set()
    plan = ReadPlan(
        pages=pages,
        records_by_page={pid: sorted(v) for pid, v in records_by_page.items()},
        n_records=len(census),
        n_records_with_lines=sum(1 for r in rows if int(r.get("n_lines") or 0) > 0),
        n_records_localizable_now=n_loc,
        n_pages_census=len(all_census),
        n_pages_resolver=len(all_res),
        n_pages_only_census=len(all_census - all_res),
        n_pages_only_resolver=len(all_res - all_census),
        n_moved_volume=n_moved,
    )
    for rid in census:
        a, b = census[rid], resolver[rid]
        if a == b:
            plan.n_same += 1
        elif b < a:
            plan.n_narrowed += 1
        elif b > a:
            plan.n_widened += 1
        else:
            plan.n_other += 1
    plan.n_lines = count_lines_on(conn, pages)
    return plan


def plan_from_list(conn: sqlite3.Connection, page_ids: Sequence[str]) -> ReadPlan:
    """A plan over a page list given as it is (K4: the German pages of
    ``leibniz enrich page-lang``, one id a line), in the list's order, each page
    once; the census's placement counts stay zero."""
    seen: set[str] = set()
    pages = [pid for pid in page_ids if pid and not (pid in seen or seen.add(pid))]
    plan = ReadPlan(
        pages=pages,
        records_by_page={},
        n_records=0,
        n_records_with_lines=0,
        n_records_localizable_now=0,
        n_pages_census=0,
        n_pages_resolver=0,
        n_pages_only_census=0,
        n_pages_only_resolver=0,
    )
    plan.n_lines = count_lines_on(conn, pages)
    return plan


def read_page_list(path: Path | str) -> list[str]:
    """Page ids from a text file, one a line, blank lines and ``#`` comments skipped."""
    out: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def crop_width(polygon: Sequence | None, baseline: Sequence | None) -> int | None:
    """The width in pixels of a line's crop before padding: the polygon's box,
    else the baseline's extent; ``None`` without geometry."""
    for pts in (polygon, baseline):
        xs = [float(pt[0]) for pt in (pts or []) if isinstance(pt, (list, tuple)) and len(pt) >= 2]
        if xs:
            return int(max(xs) - min(xs))
    return None


def narrow_crops(
    conn: sqlite3.Connection, pages: Iterable[str], *, max_width: int = 80
) -> tuple[int, int]:
    """How many of the lines the job would read are crops narrower than
    ``max_width`` pixels (the pool's K3 kraken model returned nothing on most
    such crops), and the lines counted. One geometry read per page."""
    narrow = total = 0
    for pid in pages:
        for ln in page_lines(conn, pid):
            total += 1
            w = crop_width(ln.polygon, ln.baseline)
            if w is not None and w < max_width:
                narrow += 1
    return narrow, total


def count_lines_on(conn: sqlite3.Connection, pages: Iterable[str]) -> int:
    """The lines the job would read on these pages: a text was recognised. A
    line is counted once however many runs hold a row for it (K4)."""
    n = 0
    for pid in pages:
        n += conn.execute(
            "SELECT COUNT(DISTINCT line_seq) FROM lines WHERE page_id = ? AND text IS NOT NULL",
            (pid,),
        ).fetchone()[0]
    return n


# --------------------------------------------------------------------------- #
# Progress and the files beside the readings
# --------------------------------------------------------------------------- #


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class ReadStats:
    """What one run of the job did, written beside the readings as it goes."""

    reader: str
    model: str = ""
    device: str = ""
    settings: dict = field(default_factory=dict)
    pages_total: int = 0
    pages_done: int = 0  # pages with no line left to read (this run or before)
    lines_total: int = 0  # recognised lines on the pages
    lines_before: int = 0  # readings the file already held on these pages
    lines_read: int = 0  # read in this run
    skipped: dict[str, int] = field(default_factory=dict)
    seconds: float = 0.0  # wall time of this run
    model_seconds: float = 0.0  # of it, inside the engine
    started: str = field(default_factory=_now)
    updated: str = field(default_factory=_now)
    finished: bool = False

    @property
    def n_skipped(self) -> int:
        return sum(self.skipped.values())

    @property
    def lines_done(self) -> int:
        return self.lines_before + self.lines_read

    @property
    def lines_left(self) -> int:
        return max(0, self.lines_total - self.lines_done - self.n_skipped)

    @property
    def lines_per_hour(self) -> float | None:
        return (
            3600.0 * self.lines_read / self.seconds
            if self.seconds > 0 and self.lines_read
            else None
        )

    @property
    def ms_per_line(self) -> float | None:
        return 1000.0 * self.seconds / self.lines_read if self.lines_read else None

    @property
    def eta_seconds(self) -> float | None:
        rate = self.lines_per_hour
        return None if not rate else 3600.0 * self.lines_left / rate

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(
            n_skipped=self.n_skipped,
            lines_done=self.lines_done,
            lines_left=self.lines_left,
            lines_per_hour=self.lines_per_hour,
            ms_per_line=self.ms_per_line,
            eta_seconds=self.eta_seconds,
        )
        return d


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else (f"{m}m {s:02d}s" if m else f"{s}s")


def progress_line(stats: ReadStats) -> str:
    """One log line: lines done, lines per hour, the ETA."""
    rate = stats.lines_per_hour
    return (
        f"{stats.reader}: {stats.lines_done:,}/{stats.lines_total:,} lines done "
        f"({stats.lines_read:,} this run, {stats.n_skipped:,} skipped) · "
        f"{'—' if rate is None else f'{rate:,.0f}'} lines/h · "
        f"{'—' if stats.ms_per_line is None else f'{stats.ms_per_line:.0f}'} ms/line · "
        f"ETA {format_duration(stats.eta_seconds)} · "
        f"pages {stats.pages_done:,}/{stats.pages_total:,}"
    )


def stats_path(readings_dir: Path | str, reader: str) -> Path:
    return Path(readings_dir) / f"{reader}.stats.json"


def skipped_path(readings_dir: Path | str, reader: str) -> Path:
    return Path(readings_dir) / f"{reader}.skipped.jsonl"


def write_stats(readings_dir: Path | str, stats: ReadStats) -> Path:
    path = stats_path(readings_dir, stats.reader)
    path.parent.mkdir(parents=True, exist_ok=True)
    stats.updated = _now()
    tmp = path.with_suffix(".json.part")
    tmp.write_text(
        json.dumps(stats.as_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    tmp.replace(path)
    return path


def load_stats(readings_dir: Path | str, reader: str) -> dict | None:
    path = stats_path(readings_dir, reader)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def load_skipped(readings_dir: Path | str, reader: str) -> dict[str, str]:
    """``line_id → reason`` for the lines a previous run could not read."""
    path = skipped_path(readings_dir, reader)
    out: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                row = json.loads(raw)
                out[row["line_id"]] = row["reason"]
    return out


def write_skipped(readings_dir: Path | str, reader: str, skipped: Mapping[str, str]) -> None:
    path = skipped_path(readings_dir, reader)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".jsonl.part")
    with tmp.open("w", encoding="utf-8") as fh:
        for line_id in sorted(skipped):
            fh.write(json.dumps({"line_id": line_id, "reason": skipped[line_id]}) + "\n")
    tmp.replace(path)


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #


def open_page_image(path: Path):
    """The decoded page image (PIL), or ``None`` when the cache file is unreadable."""
    from PIL import Image

    try:
        im = Image.open(path)
        im.load()
    except OSError:
        return None
    return im


def crop_page(
    im, lines: Sequence[PilotLine]
) -> tuple[list[tuple[PilotLine, object]], dict[str, str]]:
    """The reader's crops of a page's lines, in memory, and the lines it could not cut.

    The crop is the pilot's: the polygon's box with the audit's padding, the
    polygon masked, no downscaling.
    """
    crops: list[tuple[PilotLine, object]] = []
    skipped: dict[str, str] = {}
    for ln in lines:
        if not ln.polygon and not ln.baseline:
            skipped[ln.line_id] = "no_geometry"
            continue
        img = crop_image(
            im, ln.polygon, ln.baseline, pad=CROP_PAD, max_width=None, mask_polygon=True
        )
        if img is None:
            skipped[ln.line_id] = "outside_image"
            continue
        crops.append((ln, img))
    return crops, skipped


def _png(im) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def read_crops(
    engine: object, crops: Sequence[tuple[PilotLine, object]], *, model: str, device: str
) -> tuple[list[Reading], float]:
    """One model call over the crops: the readings (ms per line is the call's share)
    and the seconds it took. An engine without the in-memory protocol gets PNGs."""
    images = [im for _, im in crops]
    t0 = time.perf_counter()
    if hasattr(engine, "transcribe_images"):
        out = engine.transcribe_images(images)  # type: ignore[attr-defined]
    elif hasattr(engine, "transcribe_conf"):
        out = engine.transcribe_conf([_png(im) for im in images])  # type: ignore[attr-defined]
    else:
        out = [(t, None) for t in engine.transcribe([_png(im) for im in images])]  # type: ignore[attr-defined]
    seconds = time.perf_counter() - t0
    ms = 1000.0 * seconds / max(1, len(crops))
    rows = [
        Reading(ln.line_id, text, conf, model, device, round(ms, 1))
        for (ln, _), (text, conf) in zip(crops, out, strict=True)
    ]
    return rows, seconds


def batched[T](items: Sequence[T], size: int) -> Iterable[Sequence[T]]:
    for start in range(0, len(items), max(1, size)):
        yield items[start : start + size]


def read_pages(
    conn: sqlite3.Connection,
    pages: Sequence[str],
    reader: str,
    engine_factory: Callable[[], object],
    *,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    readings_dir: Path | str = DEFAULT_READINGS_DIR,
    batch_size: int = 16,
    log: Callable[[str], None] | None = None,
    log_every_s: float = LOG_EVERY_S,
    max_lines: int | None = None,
    sort_by_width: bool = True,
) -> ReadStats:
    """Read every recognised line of ``pages`` that the reader's JSONL does not hold.

    Page by page: the image decoded once, the lines cut in memory, ordered by
    width (so a batch's generation steps go to lines of like length) and read
    in batches of ``batch_size``; the page's rows appended at once, so an
    interrupted run loses one page at most. The engine is built only when a
    line is still unread. Every ``log_every_s`` the log gets
    :func:`progress_line` and the stats file is rewritten; ``max_lines`` stops
    the run after that many new lines (the throughput sweep).
    """
    images_root = Path(images_root)
    have = load_readings(readings_dir, reader)
    skipped = load_skipped(readings_dir, reader)
    page_set = set(pages)
    stats = ReadStats(reader=reader, pages_total=len(pages))
    stats.lines_total = count_lines_on(conn, pages)
    stats.lines_before = sum(1 for lid in have if lid.rpartition(":")[0] in page_set)
    for lid in list(skipped):  # a skipped line is tried again; the reason is re-derived
        if lid.rpartition(":")[0] in page_set:
            del skipped[lid]
    engine = None
    model = device = ""
    t_start = last_log = time.perf_counter()

    def _skip(ids: Iterable[str], reason: str) -> None:
        for lid in ids:
            skipped[lid] = reason
            stats.skipped[reason] = stats.skipped.get(reason, 0) + 1

    def _flush(force: bool = False) -> None:
        nonlocal last_log
        now = time.perf_counter()
        if not force and now - last_log < log_every_s:
            return
        last_log = now
        stats.seconds = now - t_start
        write_stats(readings_dir, stats)
        write_skipped(readings_dir, reader, skipped)
        if log:
            log(progress_line(stats))

    for pid in pages:
        if max_lines is not None and stats.lines_read >= max_lines:
            break
        todo = [ln for ln in page_lines(conn, pid) if ln.line_id not in have]
        if not todo:
            stats.pages_done += 1
            continue
        path = page_image_path(conn, pid, images_root)
        if path is None:
            _skip((ln.line_id for ln in todo), "no_image")
            stats.pages_done += 1  # nothing left to read on it
            _flush()
            continue
        im = open_page_image(path)
        if im is None:
            _skip((ln.line_id for ln in todo), "image_unreadable")
            stats.pages_done += 1
            _flush()
            continue
        with im:
            crops, uncut = crop_page(im, todo)
        for lid, reason in uncut.items():
            _skip([lid], reason)
        if max_lines is not None:
            crops = crops[: max(0, max_lines - stats.lines_read)]
        if crops:
            if engine is None:
                engine = engine_factory()
                model = str(getattr(engine, "version", getattr(engine, "name", reader)))
                device = str(getattr(engine, "device", ""))
                stats.model, stats.device = model, device
                stats.settings = dict(getattr(engine, "settings", {}) or {})
                stats.settings.setdefault("batch_size", batch_size)
            if sort_by_width:
                crops.sort(key=lambda t: -t[1].width)
            rows: list[Reading] = []
            for chunk in batched(crops, batch_size):
                got, seconds = read_crops(engine, chunk, model=model, device=device)
                rows.extend(got)
                stats.model_seconds += seconds
            rows.sort(key=lambda r: r.line_id)
            append_readings(readings_dir, reader, rows)
            for r in rows:
                have[r.line_id] = r
            stats.lines_read += len(rows)
        if all(ln.line_id in have or ln.line_id in skipped for ln in todo):
            stats.pages_done += 1
        _flush()
    stats.seconds = time.perf_counter() - t_start
    stats.finished = stats.lines_left == 0
    _flush(force=True)
    release(engine)
    return stats


# --------------------------------------------------------------------------- #
# Where the time goes, and the sweep
# --------------------------------------------------------------------------- #


def sample_pages(conn: sqlite3.Connection, pages: Sequence[str], n_lines: int) -> list[str]:
    """Pages spread evenly over the plan that together hold at least ``n_lines``
    recognised lines (the throughput measurements' sample)."""
    if not pages:
        return []
    counts = {pid: count_lines_on(conn, [pid]) for pid in pages}
    total = sum(counts.values())
    if total <= n_lines:
        return list(pages)
    step = max(1, len(pages) * n_lines // total)
    chosen: list[str] = []
    got = 0
    for k in range(0, len(pages), step):
        pid = pages[k]
        if counts[pid] == 0:
            continue
        chosen.append(pid)
        got += counts[pid]
        if got >= n_lines:
            break
    # the stride may undershoot when lines cluster: top up with the pages after
    k = 1
    while got < n_lines and len(chosen) < len(pages):
        for pid in pages[k::step]:
            if pid not in chosen and counts[pid]:
                chosen.append(pid)
                got += counts[pid]
                if got >= n_lines:
                    break
        k += 1
    return sorted(chosen)


def first_crops(
    conn: sqlite3.Connection, pages: Sequence[str], n: int, *, images_root: Path | str
) -> tuple[list[tuple[PilotLine, object]], dict[str, float]]:
    """The first ``n`` cuttable lines of ``pages`` as crops, with the decoding and
    cutting seconds spent on them (the profile's image side)."""
    crops: list[tuple[PilotLine, object]] = []
    secs = {"page_decode": 0.0, "crop": 0.0}
    for pid in pages:
        if len(crops) >= n:
            break
        lines = page_lines(conn, pid)
        path = page_image_path(conn, pid, Path(images_root))
        if path is None or not lines:
            continue
        t0 = time.perf_counter()
        im = open_page_image(path)
        secs["page_decode"] += time.perf_counter() - t0
        if im is None:
            continue
        with im:
            t0 = time.perf_counter()
            got, _ = crop_page(im, lines[: n - len(crops)])
            secs["crop"] += time.perf_counter() - t0
        crops.extend(got)
    return crops[:n], secs


def profile_batch(
    conn: sqlite3.Connection,
    pages: Sequence[str],
    engine,
    *,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    batch_size: int = 8,
) -> dict:
    """Where a batch's time goes, the pilot's way and K2's way, on the same lines.

    The pilot cut each line to PNG and the engine decoded it again; K2 hands
    the crops over as images. Both paths are timed on one batch of
    ``batch_size`` lines after a warm-up call (the first call carries the
    model's CUDA set-up); the engine must be a :class:`TrOCREngine` built with
    ``profile=True`` (any engine with ``timings`` and ``reset_timings``).
    """
    crops, image_secs = first_crops(conn, pages, batch_size, images_root=images_root)
    n = len(crops)
    if n == 0:
        raise ValueError("no cuttable line on the given pages")
    images = [im for _, im in crops]
    pngs = [_png(im) for im in images]
    engine.transcribe_images(images)  # warm-up, not timed
    # the pilot's path: PNG bytes in, decoded by the engine
    engine.reset_timings()
    t0 = time.perf_counter()
    engine.transcribe_conf(pngs)
    before_total = time.perf_counter() - t0
    before = dict(engine.timings)
    before_counts = dict(engine.counts)
    t0 = time.perf_counter()
    for im in images:
        _png(im)
    encode_secs = time.perf_counter() - t0
    # K2's path: images in
    engine.reset_timings()
    t0 = time.perf_counter()
    engine.transcribe_images(images)
    after_total = time.perf_counter() - t0
    after = dict(engine.timings)
    after_counts = dict(engine.counts)

    def per_line(secs: Mapping[str, float]) -> dict[str, float]:
        return {k: round(1000.0 * v / n, 2) for k, v in secs.items()}

    image_side = per_line(image_secs)
    stages_before = {
        **image_side,
        "png_encode": round(1000.0 * encode_secs / n, 2),
        **per_line(before),
    }
    stages_after = {**image_side, **per_line(after)}
    return {
        "n_lines": n,
        "batch_size": batch_size,
        "settings": dict(getattr(engine, "settings", {}) or {}),
        "stages_before_ms": stages_before,
        "stages_after_ms": stages_after,
        "ms_per_line_before": round(
            1000.0 * (before_total + encode_secs + sum(image_secs.values())) / n, 1
        ),
        "ms_per_line_after": round(1000.0 * (after_total + sum(image_secs.values())) / n, 1),
        "generation_steps": after_counts.get("steps"),
        "generated_tokens": after_counts.get("tokens"),
        "generation_steps_before": before_counts.get("steps"),
    }


def _gpu_peak_mib() -> int | None:
    try:
        import torch

        if torch.cuda.is_available():
            return int(torch.cuda.max_memory_reserved() // 2**20)
    except ModuleNotFoundError:
        pass
    return None


def _gpu_reset_peak() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except ModuleNotFoundError:
        pass


@dataclass(slots=True)
class SweepSetting:
    batch_size: int
    dtype: str = "float32"
    use_cache: bool | None = None

    @property
    def key(self) -> str:
        return f"b{self.batch_size}-{self.dtype}{'-kv' if self.use_cache else ''}"


def sweep(
    conn: sqlite3.Connection,
    pages: Sequence[str],
    settings: Sequence[SweepSetting],
    engine_for: Callable[[SweepSetting], object],
    *,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    scratch_dir: Path | str,
    n_lines: int = SWEEP_LINES,
    log: Callable[[str], None] | None = None,
) -> list[dict]:
    """Lines per second for each setting on the same ``n_lines`` lines of ``pages``.

    Each setting reads into its own JSONL under ``scratch_dir`` (never the
    job's file), so a repeated sweep re-reads nothing it already has; the peak
    GPU memory reserved during the setting is recorded where torch sees a GPU.
    """
    out: list[dict] = []
    for st in settings:
        _gpu_reset_peak()
        stats = read_pages(
            conn,
            pages,
            st.key,
            lambda st=st: engine_for(st),
            images_root=images_root,
            readings_dir=scratch_dir,
            batch_size=st.batch_size,
            log=log,
            log_every_s=60.0,
            max_lines=n_lines,
        )
        row = {
            "key": st.key,
            "batch_size": st.batch_size,
            "dtype": st.dtype,
            "use_cache": st.use_cache,
            "lines": stats.lines_read,
            "seconds": round(stats.seconds, 1),
            "model_seconds": round(stats.model_seconds, 1),
            "lines_per_second": round(stats.lines_read / stats.seconds, 2)
            if stats.seconds
            else None,
            "ms_per_line": None if stats.ms_per_line is None else round(stats.ms_per_line, 1),
            "gpu_peak_mib": _gpu_peak_mib(),
            "device": stats.device,
            "already_read": stats.lines_before,
        }
        out.append(row)
        if log:
            log(
                f"sweep {st.key}: {row['lines']:,} lines in {row['seconds']} s → "
                f"{row['lines_per_second']} lines/s ({row['ms_per_line']} ms/line), "
                f"GPU peak {row['gpu_peak_mib']} MiB"
            )
    return out


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


def dresden_row(path: Path | str, reader: str = DEFAULT_READER) -> dict | None:
    """The reader's Dresden scores from a ``bootstrap-candidates.json`` (``kurrent-smoke``)."""
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    for r in data.get("results", []):
        if r.get("key") == reader and r.get("status") == "ok":
            sc = r["scores"]["philiumm"]
            return {
                "cer": sc["cer"],
                "cer_lo": sc["cer_lo"],
                "cer_hi": sc["cer_hi"],
                "lenient_cer": r["scores"]["lenient"]["cer"],
                "strict_cer": r["scores"]["strict"]["cer"],
                "ms_per_line": r.get("ms_per_line"),
                "n_lines": r.get("n_lines"),
                "device": r.get("device"),
                "hyps_path": _hyps_path(path, reader),
            }
    return None


def _hyps_path(path: Path | str, reader: str) -> str | None:
    """The ``<reader>.hyps.jsonl`` a kurrent-smoke run wrote next to its reports."""
    cand = Path(path).parent.parent / f"{reader}.hyps.jsonl"
    return str(cand) if cand.exists() else None


def _texts_of(path: Path | str | None, key: str, text_key: str) -> dict[str, str] | None:
    if path is None or not Path(path).exists():
        return None
    out: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r[key]] = r[text_key]
    return out


def _agree(base: Mapping[str, str] | None, mine: Mapping[str, str] | None) -> tuple:
    if base is None or mine is None:
        return None, None
    common = set(base) & set(mine)
    return len(common), sum(1 for k in common if base[k] == mine[k])


def sweep_agreement(
    scratch_dir: Path | str, rows: Sequence[Mapping], baseline_key: str | None = None
) -> list[dict]:
    """Each sweep row with ``compared`` and ``identical``: how many of its readings equal the
    baseline setting's on the same lines (the first row's setting unless named). The kv cache
    and half precision are taken only where the text stays the reader's."""
    scratch = Path(scratch_dir)
    base_key = baseline_key or (rows[0]["key"] if rows else None)
    base = _texts_of(scratch / f"{base_key}.jsonl", "line_id", "text") if base_key else None
    out: list[dict] = []
    for r in rows:
        compared, identical = _agree(
            base, _texts_of(scratch / f"{r['key']}.jsonl", "line_id", "text")
        )
        out.append({**r, "baseline": base_key, "compared": compared, "identical": identical})
    return out


def dresden_agreement(
    dresden: Mapping[str, Mapping | None], baseline: str | None = None
) -> dict[str, dict | None]:
    """Each Dresden row with ``compared`` and ``identical`` against the baseline run's
    hypotheses (the first run unless named), read from the ``hyps_path`` of each row."""
    labels = [k for k, v in dresden.items() if v is not None]
    base_label = baseline or (labels[0] if labels else None)
    base = _texts_of(dresden[base_label].get("hyps_path"), "line_id", "hyp") if base_label else None
    out: dict[str, dict | None] = {}
    for label, row in dresden.items():
        if row is None:
            out[label] = None
            continue
        compared, identical = _agree(base, _texts_of(row.get("hyps_path"), "line_id", "hyp"))
        out[label] = {**row, "baseline": base_label, "compared": compared, "identical": identical}
    return out


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{100 * x:.{d}f} %"


def _n(x: int | None) -> str:
    return "—" if x is None else f"{x:,}"


def _eta_text(plan: Mapping | None, chosen: Mapping) -> str:
    rate = chosen.get("lines_per_second")
    n = (plan or {}).get("n_lines")
    if not rate or not n:
        return "—"
    return format_duration(n / rate)


def render_read_report(
    *,
    plan: Mapping | None,
    profile: Mapping | None,
    sweep_rows: Sequence[Mapping],
    dresden: Mapping[str, Mapping | None],
    chosen: Mapping | None,
    stats: Mapping | None,
    reader: str = DEFAULT_READER,
    generated: str | None = None,
) -> str:
    """``reports/kurrent/k2-read.md``: the pages, the profile, the sweep, the Dresden
    check, the setting chosen and what the job did — numbers from the files only."""
    out: list[str] = []
    A = out.append
    A("# K2: reading the German pieces with the Bern Kurrent reader")
    A("")
    A(
        f"Reader `{reader}` over every recognised line on the pages of the census's German "
        "pieces (`data/kurrent/german_pieces.jsonl`), the pages being the union of the K1 "
        "census's placement and the factory's today; readings in "
        "`data/kurrent/k2-readings/` (gitignored), one resumable JSONL in the pilot's row "
        f"format. Generated {generated or date.today().isoformat()}."
    )
    if plan:
        A("")
        A("## The pages")
        A("")
        A(
            f"{_n(plan.get('n_records'))} German records ({_n(plan.get('n_records_with_lines'))} "
            f"with recognised lines in the census; {_n(plan.get('n_records_localizable_now'))} "
            "localizable under the factory today). Pages: census "
            f"{_n(plan.get('n_pages_census'))}, "
            f"resolver {_n(plan.get('n_pages_resolver'))}, union **{_n(plan.get('n_pages'))}** "
            f"({_n(plan.get('n_pages_only_census'))} only in the census, "
            f"{_n(plan.get('n_pages_only_resolver'))} only in the resolver); the page set is the "
            f"same for {_n(plan.get('n_same'))} records, narrower today for "
            f"{_n(plan.get('n_narrowed'))}, wider for {_n(plan.get('n_widened'))}, otherwise "
            f"different for {_n(plan.get('n_other'))}; {_n(plan.get('n_moved_volume'))} records "
            f"are minted under another volume today. **{_n(plan.get('n_lines'))} recognised "
            "lines** on the union (the census summed its pieces' lines, pages shared between "
            "pieces counted once per piece)."
        )
    if profile:
        A("")
        A("## Where a batch's time goes")
        A("")
        A(
            f"One batch of {profile.get('n_lines')} lines (batch size {profile.get('batch_size')}, "
            f"settings {json.dumps(profile.get('settings', {}), ensure_ascii=False)}), after a "
            "warm-up call; milliseconds per line. *Before* is the pilot's path (the crop encoded "
            "to PNG, decoded again by the engine), *after* K2's (the crop handed over as an "
            "image)."
        )
        A("")
        stages = list(
            dict.fromkeys(
                [*profile.get("stages_before_ms", {}), *profile.get("stages_after_ms", {})]
            )
        )
        A("| stage | before (ms/line) | after (ms/line) |")
        A("|---|---:|---:|")
        for st in stages:
            b = profile.get("stages_before_ms", {}).get(st)
            a = profile.get("stages_after_ms", {}).get(st)
            A(f"| {st} | {'—' if b is None else f'{b:.1f}'} | {'—' if a is None else f'{a:.1f}'} |")
        A(
            f"| **total** | **{profile.get('ms_per_line_before')}** | "
            f"**{profile.get('ms_per_line_after')}** |"
        )
        A("")
        A(
            f"Generation steps in the batch: {_n(profile.get('generation_steps'))} (the longest "
            f"line sets them) for {_n(profile.get('generated_tokens'))} generated tokens over the "
            f"{profile.get('n_lines')} lines."
        )
    if sweep_rows:
        A("")
        A("## The sweep")
        A("")
        agree = any(r.get("compared") is not None for r in sweep_rows)
        base = next((r.get("baseline") for r in sweep_rows if r.get("baseline")), None)
        A(
            "The same lines, a sample spread over the job's pages, read with each setting into a "
            "scratch file; wall time includes decoding and cutting."
            + (
                f" The last column counts the readings a setting left identical to `{base}`'s "
                "on the lines both read."
                if agree
                else ""
            )
        )
        A("")
        A(
            "| setting | batch | dtype | kv cache | lines | seconds | lines/s | ms/line | "
            "GPU peak MiB |" + (" identical / compared |" if agree else "")
        )
        A("|---|---:|---|---|---:|---:|---:|---:|---:|" + ("---:|" if agree else ""))
        for r in sweep_rows:
            A(
                f"| {r['key']} | {r['batch_size']} | {r['dtype']} | "
                f"{'on' if r.get('use_cache') else 'default'} | {_n(r.get('lines'))} | "
                f"{r.get('seconds')} | {r.get('lines_per_second')} | {r.get('ms_per_line')} | "
                f"{_n(r.get('gpu_peak_mib'))} |"
                + (f" {_n(r.get('identical'))} / {_n(r.get('compared'))} |" if agree else "")
            )
    if dresden:
        A("")
        A("## The Dresden check")
        A("")
        A(
            "`leibniz bench kurrent-smoke` for this reader alone, the 383 Kurrent Trace lines, "
            "CER under the `philiumm` policy with its 95 % bootstrap interval; a setting is "
            "taken only where the CER stays within 0.2 points of K1's."
        )
        A("")
        agree = any(r and r.get("compared") is not None for r in dresden.values())
        base = next((r.get("baseline") for r in dresden.values() if r and r.get("baseline")), None)
        if agree:
            A(f"The last column counts the lines a run read identically to the run *{base}* did.")
            A("")
        A(
            "| run | CER | lenient | strict | ms/line | device |"
            + (" identical / compared |" if agree else "")
        )
        A("|---|---|---:|---:|---:|---|" + ("---:|" if agree else ""))
        for label, row in dresden.items():
            if row is None:
                A(f"| {label} | — | — | — | — | — |" + (" — |" if agree else ""))
                continue
            A(
                f"| {label} | {_pct(row['cer'])} ({_pct(row['cer_lo'])}–{_pct(row['cer_hi'])}) | "
                f"{_pct(row['lenient_cer'])} | {_pct(row['strict_cer'])} | "
                f"{'—' if row.get('ms_per_line') is None else f'{row["ms_per_line"]:.0f}'} | "
                f"{row.get('device') or '—'} |"
                + (f" {_n(row.get('identical'))} / {_n(row.get('compared'))} |" if agree else "")
            )
    if chosen:
        A("")
        A("## The setting")
        A("")
        A(
            f"**{chosen.get('key')}**: batch {chosen.get('batch_size')}, {chosen.get('dtype')}, "
            f"kv cache {'on' if chosen.get('use_cache') else 'default'}; "
            f"{chosen.get('lines_per_second')} lines/s in the sweep → the job's "
            f"{_n(plan.get('n_lines') if plan else None)} lines in about "
            f"{_eta_text(plan, chosen)}. " + str(chosen.get("note") or "")
        )
    if stats:
        A("")
        A("## The job")
        A("")
        A(
            f"Model `{stats.get('model')}` on `{stats.get('device')}`, settings "
            f"{json.dumps(stats.get('settings', {}), ensure_ascii=False)}. "
            f"Lines on the pages {_n(stats.get('lines_total'))}; read "
            f"**{_n(stats.get('lines_done'))}** ({_n(stats.get('lines_read'))} in the last run, "
            f"{_n(stats.get('lines_before'))} before "
            f"it); skipped {_n(stats.get('n_skipped'))}"
            + (
                " (" + ", ".join(f"{k} {v:,}" for k, v in sorted(stats["skipped"].items())) + ")"
                if stats.get("skipped")
                else ""
            )
            + f"; left {_n(stats.get('lines_left'))}. Last run: "
            f"{format_duration(stats.get('seconds'))} "
            f"wall, {format_duration(stats.get('model_seconds'))} in the engine, "
            f"{'—' if stats.get('lines_per_hour') is None else f'{stats["lines_per_hour"]:,.0f}'} "
            f"lines/h; pages {_n(stats.get('pages_done'))}/{_n(stats.get('pages_total'))}; "
            f"{'finished' if stats.get('finished') else 'not finished'} "
            f"(started {stats.get('started')}, updated {stats.get('updated')})."
        )
    A("")
    return "\n".join(out)


def write_read_report(
    *,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
    plan: Mapping | None,
    profile: Mapping | None,
    sweep_rows: Sequence[Mapping],
    dresden: Mapping[str, Mapping | None],
    chosen: Mapping | None,
    stats: Mapping | None,
    reader: str = DEFAULT_READER,
) -> tuple[Path, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    md = reports_dir / "k2-read.md"
    js = reports_dir / "k2-read.json"
    generated = date.today().isoformat()
    md.write_text(
        render_read_report(
            plan=plan,
            profile=profile,
            sweep_rows=sweep_rows,
            dresden=dresden,
            chosen=chosen,
            stats=stats,
            reader=reader,
            generated=generated,
        ),
        encoding="utf-8",
    )
    js.write_text(
        json.dumps(
            {
                "generated": generated,
                "reader": reader,
                "plan": {k: v for k, v in plan.items() if k != "pages"} if plan else None,
                "profile": profile,
                "sweep": list(sweep_rows),
                "dresden": dresden,
                "chosen": chosen,
                "job": stats,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return md, js


__all__ = [
    "DEFAULT_READER",
    "DEFAULT_READINGS_DIR",
    "LOG_EVERY_S",
    "SKIP_REASONS",
    "SWEEP_BATCHES",
    "SWEEP_LINES",
    "ReadPlan",
    "ReadStats",
    "SweepSetting",
    "count_lines_on",
    "crop_page",
    "dresden_agreement",
    "dresden_row",
    "first_crops",
    "format_duration",
    "german_piece_refs",
    "load_skipped",
    "load_stats",
    "plan_pages",
    "profile_batch",
    "progress_line",
    "read_crops",
    "read_pages",
    "render_read_report",
    "resolve_pages",
    "sample_pages",
    "stats_path",
    "sweep",
    "sweep_agreement",
    "write_read_report",
    "write_stats",
]
