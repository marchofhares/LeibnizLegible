"""Corpus recognition stage (Phase C1).

``recognize_pages`` walks the ``segmented`` pages, crops each stored line from its
geometry (no re-segmentation — :meth:`PageSegmenter.crop_lines`), runs the HTR
model, and fills each line's ``text`` + per-line ``conf`` (SPECS §4.5), advancing
the page to ``recognized``. Same posture as the segment stage: status-driven,
resumable, idempotent, per-page fault tolerance, one ``runs`` row per batch.

Two objects are injected: a *cropper* (the :class:`~leibniz.layout.segment.PageSegmenter`,
used only for its pure-geometry line extraction) and a *recogniser* (the
:class:`~leibniz.htr.engines.KrakenEngine`, exposing ``transcribe_conf``). Tests
pass fakes for both, so the module imports and runs without kraken/torch.
"""

from __future__ import annotations

import signal
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from leibniz import db
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT, local_relpath
from leibniz.layout.segment import SegLine, SegmentedPage
from leibniz.pipeline import geometry
from leibniz.pipeline.segment import in_shard

_REDO_STATUSES = ("segmented", "recognized")

# Wall-clock caps on the crop calls — the final backstop: geometry the guards
# don't anticipate must cost a line (or at worst a page), never stall the run.
# Cropping is pure geometry and normally takes well under a second per line.
CROP_PAGE_DEADLINE_S = 120.0
CROP_LINE_DEADLINE_S = 30.0


class Cropper(Protocol):
    """Extracts line images from a page + its stored segmentation."""

    def crop_lines(self, image: bytes, page: SegmentedPage) -> list[bytes]: ...


class Recognizer(Protocol):
    """Transcribes line images to ``(text, confidence)`` pairs, in order."""

    version: str

    def transcribe_conf(self, images: Sequence[bytes]) -> list[tuple[str, float | None]]: ...


@dataclass(slots=True)
class RecognizeResult:
    """Outcome of one recognition batch."""

    run_id: int
    considered: int = 0
    recognized: int = 0
    skipped: int = 0
    n_lines: int = 0
    seconds: float = 0.0
    failures: list[tuple[str, str]] = field(default_factory=list)


ProgressFn = Callable[[str, str], None]


# Point sanitizer shared with the geometry guards (also imported by tests).
_dedupe_pts = geometry.dedupe_points


@contextmanager
def _crop_deadline(seconds: float):
    """Raise ``TimeoutError`` if the wrapped crop outlives ``seconds`` (SIGALRM).

    The live corpus run was killed twice by the OS while kraken/PIL chewed on
    one page's pathological geometry — an in-process stall no exception handler
    can see. A wall-clock alarm converts any residual stall into an exception
    the per-line/per-page fault tolerance already handles. No-op off the main
    thread or where SIGALRM is unavailable; the pipeline is single-threaded on
    POSIX, where this is exact.
    """
    if (
        seconds <= 0
        or not hasattr(signal, "SIGALRM")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return

    def _timeout(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"crop exceeded {seconds:.0f}s deadline")

    old = signal.signal(signal.SIGALRM, _timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old)


def _page_to_segmentation(page: db.Page, lines: Sequence[db.Line]) -> SegmentedPage:
    """Rebuild a :class:`SegmentedPage` from stored line geometry, for cropping."""
    seg_lines = [
        SegLine(
            index=ln.line_seq,
            baseline=_dedupe_pts(ln.baseline),
            boundary=_dedupe_pts(ln.polygon),
        )
        for ln in lines
    ]
    return SegmentedPage(lines=seg_lines, width=page.width or 0, height=page.height or 0)


def _crop_lines_tolerant(
    cropper: Cropper, image: bytes, page: db.Page, croppable: Sequence[db.Line]
) -> tuple[list[bytes], list[db.Line]]:
    """Crop all lines at once; on failure retry line-by-line, dropping poison lines.

    Geometry the sanitizers don't anticipate must cost the *line*, not the page
    (and never the run): if the whole-page crop raises, each line is re-cropped
    alone and only the ones that still raise (or yield no crop) are dropped —
    they stay untranscribed, like degenerate baselines. Returns the crops and
    the lines they correspond to, in order.
    """
    try:
        with _crop_deadline(CROP_PAGE_DEADLINE_S):
            return (
                cropper.crop_lines(image, _page_to_segmentation(page, croppable)),
                list(croppable),
            )
    except Exception:  # noqa: BLE001 — isolate the poison line(s) below
        crops: list[bytes] = []
        kept: list[db.Line] = []
        for ln in croppable:
            try:
                with _crop_deadline(CROP_LINE_DEADLINE_S):
                    out = cropper.crop_lines(image, _page_to_segmentation(page, [ln]))
            except Exception:  # noqa: BLE001 — this line is the poison; drop it
                continue
            if len(out) == 1:
                crops.append(out[0])
                kept.append(ln)
        return crops, kept


def _work_pages(
    conn,
    *,
    set_name: str | None,
    work_ids: Sequence[str] | None,
    redo: bool,
    sample: int | None,
    shard: tuple[int, int] | None = None,
) -> Iterator[db.Page]:
    statuses = _REDO_STATUSES if redo else ("segmented",)
    yielded = 0
    for status in statuses:
        for page in db.iter_pages_by_status(
            conn, status, set_name=set_name, work_ids=work_ids, require_cached=True
        ):
            if not in_shard(page.work_id, shard):
                continue
            yield page
            yielded += 1
            if sample is not None and yielded >= sample:
                return


def recognize_pages(
    conn,
    cropper: Cropper,
    recognizer: Recognizer,
    *,
    model_version: str | None = None,
    images_root: Path = DEFAULT_IMAGES_ROOT,
    set_name: str | None = None,
    work_ids: Sequence[str] | None = None,
    redo: bool = False,
    sample: int | None = None,
    shard: tuple[int, int] | None = None,
    progress: ProgressFn | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> RecognizeResult:
    """Recognise segmented pages, filling line text + confidence (one run)."""
    images_root = Path(images_root)
    from leibniz.pipeline.segment import preflight_images_root

    preflight_images_root(conn, images_root, status=_REDO_STATUSES[0] if redo else "segmented")
    version = model_version or getattr(recognizer, "version", "philiumm-htr")
    run_id = db.start_run(
        conn,
        "recognize",
        model=version,
        params={
            "set": set_name,
            "work_ids": list(work_ids) if work_ids else None,
            "redo": redo,
            "sample": sample,
            "shard": list(shard) if shard else None,
        },
        git_sha=db.git_sha(),
    )
    result = RecognizeResult(run_id=run_id)
    t0 = monotonic()
    for page in _work_pages(
        conn, set_name=set_name, work_ids=work_ids, redo=redo, sample=sample, shard=shard
    ):
        result.considered += 1
        outcome = _recognize_one(
            conn,
            cropper,
            recognizer,
            page,
            run_id=run_id,
            version=version,
            images_root=images_root,
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
        n_ok=result.recognized,
        n_failed=result.skipped,
    )
    return result


def _recognize_one(
    conn,
    cropper: Cropper,
    recognizer: Recognizer,
    page: db.Page,
    *,
    run_id: int,
    version: str,
    images_root: Path,
    result: RecognizeResult,
) -> str:
    target = images_root / (page.local_path or local_relpath(page))
    if not target.exists():
        db.set_page_status(conn, page.id, "skipped", skip_reason="image_missing")
        result.skipped += 1
        result.failures.append((page.id, "image_missing"))
        return "image_missing"

    lines = db.iter_lines_for_page(conn, page.id)
    if not lines:  # segmented flag but no geometry — inconsistent; re-segment needed
        db.set_page_status(conn, page.id, "skipped", skip_reason="no_geometry")
        result.skipped += 1
        result.failures.append((page.id, "no_geometry"))
        return "no_geometry"

    # Drop lines whose stored geometry would sink kraken's extractor — raise
    # (sub-5px baseline), NaN (zero-length segment), or an OOM-scale rectified
    # allocation (see :mod:`leibniz.pipeline.geometry`) — *before* cropping.
    # Order is preserved, so the surviving crops still map 1:1 to their
    # line_seq; dropped lines are left untranscribed, with per-line reasons.
    croppable: list[db.Line] = []
    guard_dropped: list[tuple[int, str]] = []
    for ln in lines:
        reason = _line_drop_reason(ln, page)
        if reason is None:
            croppable.append(ln)
        else:
            guard_dropped.append((ln.line_seq, reason))
    if not croppable:
        db.set_page_status(conn, page.id, "skipped", skip_reason="no_croppable_lines")
        result.skipped += 1
        result.failures.append((page.id, "no_croppable_lines"))
        return "no_croppable_lines"

    try:
        image = target.read_bytes()
        crops, kept = _crop_lines_tolerant(cropper, image, page, croppable)
        # A crop can be degenerate even when its stored geometry looked sane —
        # the live killer was a ~900×1 sliver whose aspect-preserving resize to
        # model height made one conv2d allocate 5.3 GB. Judge the actual crop
        # raster before the recogniser sees it.
        sane_crops: list[bytes] = []
        sane_kept: list[db.Line] = []
        # Not strict: crop-count drift (fewer crops than lines) is an accepted
        # condition — unpaired lines simply stay untranscribed, as before.
        for crop, ln in zip(crops, kept, strict=False):
            crop_reason = geometry.crop_drop_reason(crop)
            if crop_reason is None:
                sane_crops.append(crop)
                sane_kept.append(ln)
            else:
                guard_dropped.append((ln.line_seq, crop_reason))
        crops, kept = sane_crops, sane_kept
        if not crops:
            raise ValueError("no line survived polygon extraction")
        preds = recognizer.transcribe_conf(crops)
    except Exception as exc:  # noqa: BLE001 — tolerate & log per-page failures
        reason = f"recognize_error: {type(exc).__name__}: {exc}"
        db.set_page_status(conn, page.id, "skipped", skip_reason=reason[:300])
        result.skipped += 1
        result.failures.append((page.id, reason[:300]))
        return "error"

    # Align on the shorter list and record the shortfall rather than mis-pairing.
    n = min(len(kept), len(preds))
    for ln, (text, conf) in zip(kept[:n], preds[:n], strict=True):
        db.set_line_recognition(
            conn,
            page.id,
            ln.line_seq,
            text=text,
            conf=conf,
            model=version,
            run_id=run_id,
            source={"stage": "recognize", "htr_model": version, "htr_run": run_id},
        )
    result.n_lines += n
    n_untranscribed = len(lines) - n
    if n_untranscribed:
        note = f"{n_untranscribed}/{len(lines)} line(s) not transcribed"
        if guard_dropped:
            detail = "; ".join(f"line {seq}: {r}" for seq, r in guard_dropped[:4])
            note += f" ({detail})"
        result.failures.append((page.id, note))
    db.set_page_status(conn, page.id, "recognized")
    result.recognized += 1
    return "recognized"


# Re-exported for existing callers/tests; the implementation lives in geometry.
MIN_BASELINE_PX = geometry.MIN_BASELINE_PX


def _line_drop_reason(line: db.Line, page: db.Page) -> str | None:
    """Why the crop guards refuse this stored line (``None`` = handed to the cropper)."""
    return geometry.drop_reason(
        line.baseline, line.polygon, page_width=page.width, page_height=page.height
    )


def audit_page(conn, page: db.Page) -> list[dict]:
    """Per-line geometry audit of a page: exactly what the crop guards will do.

    Pure DB reads + arithmetic (no kraken/PIL) — the operator's first tool when
    a page skips, stalls, or dies: it names the poison line and the crop size
    kraken would have tried to allocate for it.
    """
    rows: list[dict] = []
    for ln in db.iter_lines_for_page(conn, page.id):
        bl = geometry.dedupe_points(ln.baseline)
        poly = geometry.dedupe_points(ln.polygon)
        est = geometry.estimate_crop_size(bl, poly) if len(poly) >= 3 else None
        rows.append(
            {
                "line_seq": ln.line_seq,
                "n_baseline_pts": len(bl),
                "baseline_px": round(geometry.polyline_length(bl), 1),
                "n_boundary_pts": len(poly),
                "est_crop": f"{est[0]}×{est[1]}" if est else None,
                "est_mpx": round(est[0] * est[1] / 1e6, 2) if est else None,
                "verdict": _line_drop_reason(ln, page) or "ok",
            }
        )
    return rows


__all__ = [
    "Cropper",
    "ProgressFn",
    "RecognizeResult",
    "Recognizer",
    "audit_page",
    "recognize_pages",
]
