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


def _page_to_segmentation(page: db.Page, lines: Sequence[db.Line]) -> SegmentedPage:
    """Rebuild a :class:`SegmentedPage` from stored line geometry, for cropping."""
    seg_lines = [
        SegLine(
            index=ln.line_seq,
            baseline=[tuple(p) for p in (ln.baseline or [])],
            boundary=[tuple(p) for p in (ln.polygon or [])],
        )
        for ln in lines
    ]
    return SegmentedPage(lines=seg_lines, width=page.width or 0, height=page.height or 0)


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

    try:
        image = target.read_bytes()
        seg_page = _page_to_segmentation(page, lines)
        crops = cropper.crop_lines(image, seg_page)
        preds = recognizer.transcribe_conf(crops)
    except Exception as exc:  # noqa: BLE001 — tolerate & log per-page failures
        reason = f"recognize_error: {type(exc).__name__}: {exc}"
        db.set_page_status(conn, page.id, "skipped", skip_reason=reason[:300])
        result.skipped += 1
        result.failures.append((page.id, reason[:300]))
        return "error"

    # Crop/line-count drift is possible if geometry and cropper disagree; align on
    # the shorter list and record the shortfall rather than mis-pairing text.
    n = min(len(lines), len(preds))
    for ln, (text, conf) in zip(lines[:n], preds[:n], strict=True):
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
    if n < len(lines):
        result.failures.append((page.id, f"partial: {n}/{len(lines)} lines recognised"))
    db.set_page_status(conn, page.id, "recognized")
    result.recognized += 1
    return "recognized"


__all__ = ["Cropper", "ProgressFn", "RecognizeResult", "Recognizer", "recognize_pages"]
