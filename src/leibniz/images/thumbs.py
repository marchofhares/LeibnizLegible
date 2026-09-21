"""Thumbnails for the image mirror, and a check that the mirror is complete.

``leibniz images thumbs`` derives one small JPEG per cached page, under the
same ``{work_id}/{seq:04d}.jpg`` layout as the cache, so ``thumbs/`` uploads
next to the images and the viewer's search results and page strips load
from the mirror too (:mod:`leibniz.web.images`). Pillow decodes at reduced
size straight from the JPEG's DCT (``Image.draft``), which makes the corpus a
matter of tens of minutes on a few cores rather than hours. Resumable:
existing thumbnails are skipped unless ``redo``.

``leibniz images check-mirror`` samples cached pages and ``HEAD``s their
mirror URLs, comparing sizes with the cache manifest in ``pages`` — the quick
end-to-end check after an upload (``rclone check`` is the full one).
"""

from __future__ import annotations

import multiprocessing
import random
import sqlite3
import warnings
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import httpx

DEFAULT_THUMBS_ROOT = Path("data/thumbs")
DEFAULT_WIDTH = 320
THUMBS_PREFIX = "thumbs"


def make_thumbnail(
    src: Path, dst: Path, *, width: int = DEFAULT_WIDTH, quality: int = 80
) -> tuple[int, int]:
    """Write ``dst`` as a JPEG at most ``width`` pixels wide (aspect kept); return its size."""
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:  # pragma: no cover — environment-dependent
        raise ModuleNotFoundError("Pillow is required: uv sync --extra gt") from exc
    with warnings.catch_warnings():
        # The corpus holds ~120-165 MP foldout scans, over Pillow's 89.5 MP
        # decompression-bomb threshold. That heuristic guards against hostile
        # uploads; these are our own cache, fetched from the library, and the
        # warning fires a few thousand times and buries the progress bar. The
        # limit itself stays on (Pillow still raises above 2x), so a genuinely
        # absurd file is still refused.
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        return _resize(Image, src, dst, width, quality)


def _resize(Image, src: Path, dst: Path, width: int, quality: int) -> tuple[int, int]:
    with Image.open(src) as im:
        im.draft("RGB", (width, width * 4))  # decode at a reduced scale, cheaply
        im = im.convert("RGB")
        w, h = im.size
        if w > width:
            im.thumbnail((width, max(1, round(h * width / w))), Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + ".part")
        im.save(tmp, "JPEG", quality=quality, optimize=True, progressive=True)
        tmp.replace(dst)
        return im.size


def cached_pages(
    conn: sqlite3.Connection, limit: int | None = None
) -> list[tuple[str, str, int | None]]:
    """``(page_id, local_path, n_bytes)`` for every page the cache holds."""
    sql = (
        "SELECT page_id, local_path, n_bytes FROM pages WHERE local_path IS NOT NULL "
        "ORDER BY page_id"
    )
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return [(r[0], r[1], r[2]) for r in conn.execute(sql).fetchall()]


def preflight_images_root(conn: sqlite3.Connection, images_root: Path, *, sample: int = 25) -> None:
    """Abort when the images root looks wrong, before statting a quarter-million files.

    The same guard as :func:`leibniz.pipeline.segment.preflight_images_root`, and
    for the same reason: a page carrying a ``local_path`` is *recorded* as
    downloaded, so if not one of a sample exists under the root, the root — not
    the cache — is what is missing. This bites easily, because a 395 GB image
    cache usually lives on a different disk from the 15 GB store, and the
    default root (``data/images``) sits next to the store.
    """
    rows = cached_pages(conn, limit=sample)
    if len(rows) < 5:
        return  # too few to tell a wrong root from a genuinely missing file
    if any((Path(images_root) / local_path).exists() for _pid, local_path, _n in rows):
        return
    raise FileNotFoundError(
        f"none of the first {len(rows)} cached pages exist under {images_root} — "
        "wrong --images root? The store says these pages were downloaded, so the "
        "cache is somewhere else (check your other disks; it is ~400 GB)."
    )


@dataclass(slots=True)
class ThumbStats:
    made: int = 0
    skipped: int = 0
    missing: int = 0
    failed: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.made + self.skipped + self.missing + self.failed


def _one(job: tuple[str, str, str, int]) -> tuple[str, str]:
    page_id, src, dst, width = job
    source, target = Path(src), Path(dst)
    if not source.exists():
        return page_id, "missing"
    try:
        make_thumbnail(source, target, width=width)
    except Exception:  # noqa: BLE001 — one bad JPEG must not stop the corpus
        return page_id, "failed"
    return page_id, "made"


def build_thumbnails(
    conn: sqlite3.Connection,
    images_root: Path,
    out_root: Path = DEFAULT_THUMBS_ROOT,
    *,
    width: int = DEFAULT_WIDTH,
    workers: int | None = None,
    redo: bool = False,
    progress: Callable[[str, str], None] | None = None,
) -> ThumbStats:
    """Derive thumbnails for every cached page (skipping existing ones unless ``redo``).

    Raises :class:`FileNotFoundError` when ``images_root`` holds none of the
    cached pages (see :func:`preflight_images_root`).
    """
    preflight_images_root(conn, images_root)
    stats = ThumbStats()
    jobs: list[tuple[str, str, str, int]] = []
    for page_id, local_path, _ in cached_pages(conn):
        target = out_root / local_path
        if not redo and target.exists() and target.stat().st_size > 0:
            stats.skipped += 1
            if progress:
                progress(page_id, "skipped")
            continue
        jobs.append((page_id, str(images_root / local_path), str(target), width))
    if not jobs:
        return stats
    results: Iterable[tuple[str, str]]
    if (workers or 1) <= 1:
        results = map(_one, jobs)
    else:
        # spawn, not fork: the CLI process is multi-threaded (rich's progress
        # bar), and forking a threaded process is deprecated for good reason.
        pool = ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context("spawn")
        )
        results = pool.map(_one, jobs, chunksize=32)
    for page_id, outcome in results:
        if outcome == "made":
            stats.made += 1
        elif outcome == "missing":
            stats.missing += 1
        else:
            stats.failed += 1
            if len(stats.failures) < 50:
                stats.failures.append(page_id)
        if progress:
            progress(page_id, outcome)
    if (workers or 1) > 1:
        pool.shutdown()
    return stats


@dataclass(slots=True)
class MirrorReport:
    checked: int = 0
    ok: int = 0
    missing: list[str] = field(default_factory=list)
    size_mismatch: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    thumbs_checked: int = 0
    thumbs_missing: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not (self.missing or self.size_mismatch or self.errors or self.thumbs_missing)

    def to_dict(self) -> dict:
        return {
            "checked": self.checked,
            "ok": self.ok,
            "missing": self.missing,
            "size_mismatch": self.size_mismatch,
            "errors": self.errors,
            "thumbs_checked": self.thumbs_checked,
            "thumbs_missing": self.thumbs_missing,
            "complete": self.complete,
        }


def check_mirror(
    conn: sqlite3.Connection,
    base_url: str,
    *,
    client: httpx.Client | None = None,
    sample: int = 500,
    thumbs: bool = True,
    seed: int = 0,
    concurrency: int = 8,
) -> MirrorReport:
    """``HEAD`` a random sample of cached pages on the mirror (``sample=0`` = all)."""
    base = base_url.rstrip("/")
    pages = cached_pages(conn)
    if sample and sample < len(pages):
        pages = random.Random(seed).sample(pages, sample)
    report = MirrorReport()
    own = client is None
    http = client or httpx.Client(timeout=20.0, follow_redirects=True)

    def head(url: str) -> tuple[int, int | None] | None:
        try:
            r = http.head(url)
        except httpx.HTTPError:
            return None
        length = r.headers.get("content-length")
        return r.status_code, (int(length) if length and length.isdigit() else None)

    def one(row: tuple[str, str, int | None]) -> tuple[str, str, str | None]:
        page_id, local_path, n_bytes = row
        res = head(f"{base}/{quote(local_path)}")
        if res is None:
            verdict = "error"
        elif res[0] == 404:
            verdict = "missing"
        elif res[0] != 200:
            verdict = "error"
        elif n_bytes is not None and res[1] is not None and res[1] != n_bytes:
            verdict = "size_mismatch"
        else:
            verdict = "ok"
        thumb = None
        if thumbs:
            t = head(f"{base}/{THUMBS_PREFIX}/{quote(local_path)}")
            thumb = "ok" if t is not None and t[0] == 200 else "missing"
        return page_id, verdict, thumb

    try:
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            for page_id, verdict, thumb in pool.map(one, pages):
                report.checked += 1
                if verdict == "ok":
                    report.ok += 1
                elif verdict == "missing":
                    report.missing.append(page_id)
                elif verdict == "size_mismatch":
                    report.size_mismatch.append(page_id)
                else:
                    report.errors.append(page_id)
                if thumb is not None:
                    report.thumbs_checked += 1
                    if thumb != "ok":
                        report.thumbs_missing.append(page_id)
    finally:
        if own:
            http.close()
    return report


__all__ = [
    "DEFAULT_THUMBS_ROOT",
    "preflight_images_root",
    "DEFAULT_WIDTH",
    "THUMBS_PREFIX",
    "MirrorReport",
    "ThumbStats",
    "build_thumbnails",
    "cached_pages",
    "check_mirror",
    "make_thumbnail",
]
