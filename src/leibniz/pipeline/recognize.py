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

import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from leibniz import db
from leibniz.images.fetch import DEFAULT_IMAGES_ROOT, local_relpath
from leibniz.layout.segment import SegLine, SegmentedPage

_REDO_STATUSES = ("segmented", "recognized")


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


def _dedupe_pts(pts: object) -> list[tuple[float, float]]:
    """Drop consecutive points that collapse onto the same integer pixel.

    kraken's polygon extractor slices its dewarping mesh per baseline segment; a
    (sub-)pixel-length segment becomes a zero-width transform quad, which PIL
    turns into NaN coefficients (``1.0 / w`` divide-by-zero) and can then hang
    the C rasterizer — observed live as a page that stalls the whole run. The
    overall polyline *length* check can't catch this (a zero-length segment adds
    nothing to the total), so collapse the points themselves; at raster
    resolution this is loss-free.
    """
    out: list[tuple[float, float]] = []
    for p in pts or []:  # type: ignore[union-attr]
        q = (float(p[0]), float(p[1]))
        if not out or (int(out[-1][0]), int(out[-1][1])) != (int(q[0]), int(q[1])):
            out.append(q)
    return out


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
        return cropper.crop_lines(image, _page_to_segmentation(page, croppable)), list(croppable)
    except Exception:  # noqa: BLE001 — isolate the poison line(s) below
        crops: list[bytes] = []
        kept: list[db.Line] = []
        for ln in croppable:
            try:
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
) -> Iterator[db.Page]:
    statuses = _REDO_STATUSES if redo else ("segmented",)
    yielded = 0
    for status in statuses:
        for page in db.iter_pages_by_status(
            conn, status, set_name=set_name, work_ids=work_ids, require_cached=True
        ):
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
    progress: ProgressFn | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> RecognizeResult:
    """Recognise segmented pages, filling line text + confidence (one run)."""
    images_root = Path(images_root)
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
        },
        git_sha=db.git_sha(),
    )
    result = RecognizeResult(run_id=run_id)
    t0 = monotonic()
    for page in _work_pages(conn, set_name=set_name, work_ids=work_ids, redo=redo, sample=sample):
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

    # Drop degenerate lines (sub-5px baselines) *before* cropping: kraken's polygon
    # extractor raises `Baseline length below minimum 5px` on them, which would
    # otherwise sink the whole page. Order is preserved, so the surviving crops
    # still map 1:1 to their line_seq; dropped lines are simply left untranscribed.
    croppable = [ln for ln in lines if _croppable(ln)]
    if not croppable:
        db.set_page_status(conn, page.id, "skipped", skip_reason="no_croppable_lines")
        result.skipped += 1
        result.failures.append((page.id, "no_croppable_lines"))
        return "no_croppable_lines"

    try:
        image = target.read_bytes()
        crops, kept = _crop_lines_tolerant(cropper, image, page, croppable)
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
        result.failures.append(
            (page.id, f"{n_untranscribed}/{len(lines)} line(s) not transcribed (degenerate/crop)")
        )
    db.set_page_status(conn, page.id, "recognized")
    result.recognized += 1
    return "recognized"


# Minimum baseline length (px) kraken's polygon extractor accepts; shorter lines
# raise and are skipped rather than allowed to fail the whole page.
MIN_BASELINE_PX = 5.0


def _baseline_length(baseline: object) -> float:
    """Total polyline length of a baseline (0.0 if absent or a single point)."""
    if not baseline or len(baseline) < 2:  # type: ignore[arg-type]
        return 0.0
    total = 0.0
    pts = list(baseline)  # type: ignore[arg-type]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:], strict=False):
        total += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return total


def _croppable(line: db.Line) -> bool:
    """True if a line's *sanitized* baseline is long enough for kraken to crop it."""
    return _baseline_length(_dedupe_pts(line.baseline)) >= MIN_BASELINE_PX


__all__ = ["Cropper", "ProgressFn", "RecognizeResult", "Recognizer", "recognize_pages"]
