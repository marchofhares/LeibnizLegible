"""Corpus segmentation stage (Phase C1).

``segment_pages`` walks the ``pages`` table by status and turns every cached page
image into an ordered list of line geometries, storing each in ``lines`` (with
``status='machine'`` and no text yet) plus a per-page :mod:`~leibniz.pipeline.stats`
record in ``page_stats``. It is:

* **status-driven & resumable** — processes ``pending`` pages (``--redo`` also
  re-does ``segmented``/``recognized``/``skipped`` ones), commits per page, so an
  interrupted run resumes exactly where it stopped;
* **idempotent** — re-segmenting a page first clears its old lines;
* **fault-tolerant** — a page whose image is missing or whose segmentation raises
  is marked ``skipped`` with a reason and logged, never aborting the batch
  (SPECS §3: the remainder is enumerated with reasons);
* **provenance-complete** — the whole batch is one ``runs`` row (segmenter
  model@version, params, git SHA, counts, wall time).

The segmenter is injected (a :class:`~leibniz.layout.segment.PageSegmenter` in
production, a trivial fake in tests), so this module imports without kraken.
"""

from __future__ import annotations

import time
import zlib
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from leibniz import db
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT, local_relpath
from leibniz.images.jpeg import jpeg_dimensions
from leibniz.layout.segment import SegmentedPage
from leibniz.pipeline.stats import compute_seg_stats

# Statuses re-processed by --redo (a full resegment of the selection).
_REDO_STATUSES = ("pending", "segmented", "recognized", "skipped")

# Pages above this pixel count are skipped (with a reason) rather than
# segmented: the corpus contains ~120 MP foldout scans (vs ≤12 MP typical) that
# balloon to >1 GB of working arrays in blla and can OOM an 8 GB box; their
# layouts (maps, foldouts) segment poorly anyway. Just under PIL's 89.5 MP
# decompression-bomb warning threshold. Enumerated for a future high-memory pass.
MAX_SEGMENT_PIXELS = 80_000_000


def preflight_images_root(conn, images_root: Path, *, status: str) -> None:
    """Abort before marking anything when the images root itself looks wrong.

    A run launched without ``--images`` once turned 235k cached pages into
    ``image_missing`` skips in one pass. Every sampled page is *recorded* as
    cached (``sha256`` present), so if not one of their files exists under the
    root, the root — not the corpus — is what's missing; raise instead of
    letting the per-page skip path shred the status column.
    """
    images_root = Path(images_root)
    sample = list(db.iter_pages_by_status(conn, status, require_cached=True, limit=25))
    if len(sample) < 5:
        return  # too few to distinguish a missing root from a missing file
    if any((images_root / (p.local_path or local_relpath(p))).exists() for p in sample):
        return
    raise FileNotFoundError(
        f"none of the first {len(sample)} cached '{status}' pages exist under "
        f"{images_root} — wrong --images root? (their manifest says they were downloaded)"
    )


class Segmenter(Protocol):
    """Anything that turns a page image (bytes) into a :class:`SegmentedPage`."""

    def segment(self, image: bytes) -> SegmentedPage: ...


@dataclass(slots=True)
class SegmentResult:
    """Outcome of one segmentation batch."""

    run_id: int
    considered: int = 0
    segmented: int = 0
    skipped: int = 0
    n_lines: int = 0
    seconds: float = 0.0
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def mean_lines(self) -> float:
        return self.n_lines / self.segmented if self.segmented else 0.0


ProgressFn = Callable[[str, str], None]  # (page_id, outcome)


def in_shard(work_id: str, shard: tuple[int, int] | None) -> bool:
    """True if ``work_id`` belongs to shard ``(index, count)`` (``None`` = all).

    Stable across processes and runs (crc32, not Python's salted ``hash``), and
    keyed on the *work* so one work's folios never split across workers. N
    shards are disjoint and cover everything — parallel operators each pass
    ``--shard i/N`` and the union is exactly one full pass.
    """
    if shard is None:
        return True
    index, count = shard
    return zlib.crc32(work_id.encode("utf-8")) % count == index


# Work-list batch size. Batches are fully materialised and their cursor closed
# BEFORE any page is processed: an open read cursor on the writing connection
# pins a WAL snapshot, and the first write after any *other* worker commits
# then fails instantly with "database is locked" (snapshot upgrade — the busy
# timeout can't help). Small closed batches are what make --shard workers and
# a concurrent recogniser able to write side by side.
WORK_CHUNK = 400


def _work_pages(
    conn,
    *,
    set_name: str | None,
    work_ids: Sequence[str] | None,
    redo: bool,
    sample: int | None,
    shard: tuple[int, int] | None = None,
) -> Iterator[db.Page]:
    """The resumable segmentation work list (cached pages awaiting segmentation)."""
    statuses = _REDO_STATUSES if redo else ("pending",)
    yielded = 0
    for status in statuses:
        after: tuple[str, int] | None = None
        while True:
            batch = list(
                db.iter_pages_by_status(
                    conn,
                    status,
                    set_name=set_name,
                    work_ids=work_ids,
                    require_cached=True,
                    limit=WORK_CHUNK,
                    after=after,
                )
            )
            if not batch:
                break
            # Keyset cursor advances over the raw batch (pre-shard-filter), so a
            # worker whose shard is sparse here still terminates.
            after = (batch[-1].work_id, batch[-1].seq)
            for page in batch:
                if not in_shard(page.work_id, shard):
                    continue
                yield page
                yielded += 1
                if sample is not None and yielded >= sample:
                    return


def segment_pages(
    conn,
    segmenter: Segmenter,
    *,
    model_version: str = "philiumm-seg",
    images_root: Path = DEFAULT_IMAGES_ROOT,
    set_name: str | None = None,
    work_ids: Sequence[str] | None = None,
    redo: bool = False,
    sample: int | None = None,
    shard: tuple[int, int] | None = None,
    min_lines: int = 1,
    progress: ProgressFn | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> SegmentResult:
    """Segment cached pages into ``lines`` geometry + ``page_stats`` (one run).

    ``sample`` caps how many pages this invocation processes (spanning the
    selection in ``(work, seq)`` order); ``min_lines`` is the floor below which a
    page is treated as blank/cover and marked ``skipped`` (a page that yields no
    lines is enumerated with a reason, not silently dropped).
    """
    images_root = Path(images_root)
    preflight_images_root(conn, images_root, status=(_REDO_STATUSES if redo else ("pending",))[0])
    run_id = db.start_run(
        conn,
        "segment",
        model=model_version,
        params={
            "set": set_name,
            "work_ids": list(work_ids) if work_ids else None,
            "redo": redo,
            "sample": sample,
            "shard": list(shard) if shard else None,
        },
        git_sha=db.git_sha(),
    )
    result = SegmentResult(run_id=run_id)
    t0 = monotonic()
    for page in _work_pages(
        conn, set_name=set_name, work_ids=work_ids, redo=redo, sample=sample, shard=shard
    ):
        result.considered += 1
        outcome = _segment_one(
            conn,
            segmenter,
            page,
            run_id=run_id,
            model_version=model_version,
            images_root=images_root,
            min_lines=min_lines,
            result=result,
        )
        conn.commit()
        if progress is not None:
            progress(page.id, outcome)
    result.seconds = monotonic() - t0
    db.finish_run(
        conn,
        run_id,
        n_input=result.considered,
        n_ok=result.segmented,
        n_failed=result.skipped,
    )
    return result


def _segment_one(
    conn,
    segmenter: Segmenter,
    page: db.Page,
    *,
    run_id: int,
    model_version: str,
    images_root: Path,
    min_lines: int,
    result: SegmentResult,
) -> str:
    """Segment one page, updating the store; return a short outcome tag."""
    target = images_root / (page.local_path or local_relpath(page))
    if not target.exists():
        db.set_page_status(conn, page.id, "skipped", skip_reason="image_missing")
        result.skipped += 1
        result.failures.append((page.id, "image_missing"))
        return "image_missing"

    image = target.read_bytes()
    dims = jpeg_dimensions(image)
    if dims is not None and dims[0] * dims[1] > MAX_SEGMENT_PIXELS:
        reason = f"oversize_image:{dims[0]}x{dims[1]}"
        db.set_page_status(conn, page.id, "skipped", skip_reason=reason)
        result.skipped += 1
        result.failures.append((page.id, reason))
        return "oversize_image"

    try:
        seg = segmenter.segment(image)
    except Exception as exc:  # noqa: BLE001 — one bad page never sinks the batch
        reason = f"segment_error: {type(exc).__name__}: {exc}"
        db.set_page_status(conn, page.id, "skipped", skip_reason=reason[:300])
        result.skipped += 1
        result.failures.append((page.id, reason[:300]))
        return "error"

    # Idempotent: drop any prior lines before writing the fresh segmentation.
    db.delete_lines_for_page(conn, page.id)
    for ln in seg.lines:
        db.insert_line(
            conn,
            db.Line(
                page_id=page.id,
                line_seq=ln.index,
                baseline=[list(p) for p in ln.baseline] or None,
                polygon=[list(p) for p in ln.boundary] or None,
                run_id=run_id,
                status="machine",
                source={"stage": "segment", "seg_model": model_version, "seg_run": run_id},
            ),
        )
    stats = compute_seg_stats(seg, n_regions=seg.n_regions)
    db.upsert_page_stats(
        conn,
        db.PageStats(
            page_id=page.id,
            run_id=run_id,
            n_lines=stats.n_lines,
            n_regions=stats.n_regions,
            region_coverage=stats.region_coverage,
            mean_line_height=stats.mean_line_height,
            median_line_height=stats.median_line_height,
            line_height_cv=stats.line_height_cv,
            n_overlaps=stats.n_overlaps,
            n_short_lines=stats.n_short_lines,
            metrics=stats.as_metrics(),
        ),
    )
    result.n_lines += stats.n_lines

    if stats.n_lines < min_lines:
        db.set_page_status(conn, page.id, "skipped", skip_reason="no_lines")
        result.skipped += 1
        return "no_lines"
    db.set_page_status(conn, page.id, "segmented")
    result.segmented += 1
    return "segmented"


__all__ = [
    "MAX_SEGMENT_PIXELS",
    "ProgressFn",
    "SegmentResult",
    "Segmenter",
    "preflight_images_root",
    "segment_pages",
]
