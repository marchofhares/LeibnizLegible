"""Download, verify, and summarise the local image cache (Phase A2).

``fetch_images`` pulls each page's delivery derivative (``pages.image_url``, the
METS ``DEFAULT`` JPEG) into ``data/images/{object_id}/{seq:04d}.jpg`` and records
path + size + sha256 + dimensions in the ``pages`` manifest. It is:

* **resumable / cache-first** — a page already recorded with a matching file on
  disk is skipped; a re-run only fetches what's missing (``--redo`` re-pulls),
* **integrity-checked** — a truncated download (no JPEG EOI, or below a floor)
  is retried before the page is recorded as failed, and
* **polite** — every request goes through :class:`~leibniz.net.PoliteClient`
  (identified UA, ≤1 req/s/host, backoff). With a single GWLB host and that
  rate cap, throughput is bounded by ``--min-interval``, not by parallelism, so
  the fetcher is deliberately sequential (SPECS §7.4).

``verify_images`` re-checks the cache (existence, size, optionally re-hash) and
reports gaps; ``image_stats`` rolls up counts/bytes/dimensions for the census.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.images.jpeg import is_complete_jpeg, jpeg_dimensions

DEFAULT_IMAGES_ROOT = Path("data/images")
# A complete JPEG below this many bytes is almost certainly an error stub, not a
# real page scan (true thumbnails are ~3–4 KB; delivery derivatives are ≫ that).
MIN_IMAGE_BYTES = 1024


class IntegrityError(RuntimeError):
    """A download never arrived as a complete JPEG within the retry budget."""


ProgressFn = Callable[[str, bool], None]  # (page_id, fetched?)


# --------------------------------------------------------------------------- #
# Paths / hashing
# --------------------------------------------------------------------------- #


def cache_relpath(work_id: str, seq: int) -> str:
    """Cache path for a page, relative to the images root: ``{oid}/{seq:04d}.jpg``.

    Mirrors the canonical page-id scheme (``{object_id}:{seq:04d}``) so a file on
    disk maps back to its row unambiguously. The image mirror
    (:mod:`leibniz.web.images`) uses the same layout, so the bucket is the
    cache directory as it is.
    """
    safe = work_id.replace("/", "_").replace(os.sep, "_")
    return f"{safe}/{seq:04d}.jpg"


def local_relpath(page: db.Page) -> str:
    """:func:`cache_relpath` for a page row."""
    return cache_relpath(page.work_id, page.seq)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- #
# Fetch
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class FetchStats:
    """Bookkeeping returned by :func:`fetch_images`."""

    considered: int = 0
    fetched: int = 0
    skipped: int = 0
    bytes: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)


def _download_valid(
    client,
    url: str,
    *,
    min_bytes: int,
    integrity_retries: int,
    sleep: Callable[[float], None],
) -> bytes:
    """GET ``url`` and return the bytes only if a complete JPEG arrives.

    Retries a truncated/short body ``integrity_retries`` times (the polite client
    separately handles transient HTTP status/transport errors). Raises
    :class:`IntegrityError` if every attempt is incomplete.
    """
    last = ""
    for attempt in range(integrity_retries + 1):
        data = client.get_bytes(url)
        if len(data) >= min_bytes and is_complete_jpeg(data):
            return data
        last = f"incomplete/too-small ({len(data)} bytes)"
        if attempt < integrity_retries:
            sleep(2.0 * (attempt + 1))
    raise IntegrityError(last)


def fetch_images(
    conn,
    *,
    client,
    images_root: Path = DEFAULT_IMAGES_ROOT,
    set_name: str | None = None,
    work_ids: Sequence[str] | None = None,
    redo: bool = False,
    limit: int | None = None,
    min_bytes: int = MIN_IMAGE_BYTES,
    integrity_retries: int = 2,
    sleep: Callable[[float], None] = time.sleep,
    progress: ProgressFn | None = None,
) -> FetchStats:
    """Cache delivery derivatives for pages, resumable and integrity-checked.

    ``set_name``/``work_ids`` slice the pull (a dev corpus); ``limit`` caps the
    number of pages this invocation downloads (the rest stay pending for a later
    run). ``redo`` re-pulls pages already recorded. Failures are collected, never
    fatal, so one bad page can't abort a large pull.
    """
    images_root = Path(images_root)
    stats = FetchStats()
    # Walk every delivery target (cheap DB scan); the cache-first check below is
    # what makes a re-run skip already-downloaded pages — so `skipped` is honest
    # and a page whose file went missing self-heals by being re-fetched.
    for page in db.iter_fetch_pages(
        conn, set_name=set_name, work_ids=work_ids, only_unfetched=False
    ):
        stats.considered += 1
        target = images_root / local_relpath(page)

        # Cache-first: an already-recorded page with a matching file is skipped.
        if (
            not redo
            and page.is_cached
            and target.exists()
            and target.stat().st_size == page.n_bytes
        ):
            stats.skipped += 1
            continue

        if page.image_url is None:  # defensive; iter_fetch_pages already filters
            continue
        try:
            data = _download_valid(
                client,
                page.image_url,
                min_bytes=min_bytes,
                integrity_retries=integrity_retries,
                sleep=sleep,
            )
        except Exception as exc:  # noqa: BLE001 — collect and continue the pull
            stats.failures.append((page.id, f"{type(exc).__name__}: {exc}"))
            if progress is not None:
                progress(page.id, False)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        dims = jpeg_dimensions(data)
        db.mark_page_fetched(
            conn,
            page.id,
            local_path=local_relpath(page),
            n_bytes=len(data),
            sha256=sha256_hex(data),
            width=dims[0] if dims else None,
            height=dims[1] if dims else None,
        )
        conn.commit()
        stats.fetched += 1
        stats.bytes += len(data)
        if progress is not None:
            progress(page.id, True)
        if limit is not None and stats.fetched >= limit:
            break
    return stats


# --------------------------------------------------------------------------- #
# Verify
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class VerifyStats:
    """Bookkeeping returned by :func:`verify_images`."""

    recorded: int = 0
    ok: int = 0
    missing_file: list[str] = field(default_factory=list)
    size_mismatch: list[str] = field(default_factory=list)
    checksum_mismatch: list[str] = field(default_factory=list)
    unfetched: int = 0  # pages with a delivery URL but not yet cached (gaps)


def verify_images(
    conn,
    *,
    images_root: Path = DEFAULT_IMAGES_ROOT,
    set_name: str | None = None,
    work_ids: Sequence[str] | None = None,
    deep: bool = False,
    progress: ProgressFn | None = None,
) -> VerifyStats:
    """Re-check the cache against the manifest and report gaps.

    Every recorded page is checked for file existence and size; ``deep`` also
    re-hashes the bytes and compares the sha256. Pages that *should* be cached
    (have a delivery URL) but aren't are counted as ``unfetched`` — the pull's
    remaining work.
    """
    images_root = Path(images_root)
    stats = VerifyStats()
    for page in db.iter_fetch_pages(
        conn, set_name=set_name, work_ids=work_ids, only_unfetched=False
    ):
        if not page.is_cached:
            stats.unfetched += 1
            continue
        stats.recorded += 1
        target = images_root / (page.local_path or local_relpath(page))
        if not target.exists():
            stats.missing_file.append(page.id)
        elif target.stat().st_size != page.n_bytes:
            stats.size_mismatch.append(page.id)
        elif deep and sha256_hex(target.read_bytes()) != page.sha256:
            stats.checksum_mismatch.append(page.id)
        else:
            stats.ok += 1
        if progress is not None:
            progress(page.id, True)
    return stats


# --------------------------------------------------------------------------- #
# Stats (feeds reports/census.md)
# --------------------------------------------------------------------------- #

# Megapixel buckets for the dimensions histogram.
_MP_BUCKETS: tuple[tuple[float, float | None, str], ...] = (
    (0.0, 1.0, "< 1 MP"),
    (1.0, 3.0, "1–3 MP"),
    (3.0, 5.0, "3–5 MP"),
    (5.0, 8.0, "5–8 MP"),
    (8.0, 12.0, "8–12 MP"),
    (12.0, None, "≥ 12 MP"),
)


@dataclass(slots=True)
class ImageStats:
    """Roll-up of the image cache for the census report."""

    fetched: int
    fetch_targets: int
    total_bytes: int
    by_set: dict[str, tuple[int, int]]  # set -> (fetched, target)
    delivery: dict[str, int]  # 'iiif'/'static' -> fetched count
    mp_histogram: list[tuple[str, int]]
    n_with_dims: int
    min_dims: tuple[int, int] | None
    max_dims: tuple[int, int] | None
    mean_bytes: float

    @property
    def est_full_corpus_bytes(self) -> float:
        """Projected size of a full-corpus pull at the observed mean page size."""
        return self.mean_bytes * self.fetch_targets


def image_stats(conn) -> ImageStats:
    """Compute image-cache statistics from the ``pages`` manifest."""
    fetched = db.count_pages_fetched(conn)
    targets = db.count_fetch_targets(conn)
    total_bytes = db.sum_page_bytes(conn)

    by_set: dict[str, tuple[int, int]] = {}
    for row in conn.execute("SELECT DISTINCT set_name FROM works ORDER BY set_name"):
        s = row[0]
        by_set[s] = (
            db.count_pages_fetched(conn, set_name=s),
            db.count_fetch_targets(conn, set_name=s),
        )

    delivery: dict[str, int] = {}
    for row in conn.execute(
        "SELECT delivery, COUNT(*) FROM pages WHERE sha256 IS NOT NULL GROUP BY delivery"
    ):
        delivery[row[0] or "unknown"] = row[1]

    dims = conn.execute(
        "SELECT width, height FROM pages WHERE sha256 IS NOT NULL "
        "AND width IS NOT NULL AND height IS NOT NULL"
    ).fetchall()
    mps = [(w * h) / 1_000_000 for w, h in dims]
    hist = [
        (label, sum(1 for m in mps if m >= lo and (hi is None or m < hi)))
        for lo, hi, label in _MP_BUCKETS
    ]
    min_dims = min(dims, key=lambda d: d[0] * d[1]) if dims else None
    max_dims = max(dims, key=lambda d: d[0] * d[1]) if dims else None

    return ImageStats(
        fetched=fetched,
        fetch_targets=targets,
        total_bytes=total_bytes,
        by_set=by_set,
        delivery=delivery,
        mp_histogram=hist,
        n_with_dims=len(dims),
        min_dims=tuple(min_dims) if min_dims else None,
        max_dims=tuple(max_dims) if max_dims else None,
        mean_bytes=(total_bytes / fetched) if fetched else 0.0,
    )


def human_bytes(n: float) -> str:
    step = 1024.0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < step or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= step
    return f"{n:.1f} TB"


# Marker delimiting the census section this stage owns, so re-running replaces it.
CENSUS_MARKER = "<!-- images-stats -->"


def render_stats_section(stats: ImageStats, *, generated_at: str) -> str:
    """Render the image-cache section appended to ``reports/census.md``."""
    lines: list[str] = [CENSUS_MARKER, "", "## Image cache (Phase A2)"]
    add = lines.append
    add("")
    add(
        f"_Generated {generated_at}. Local delivery-derivative cache for the "
        "segmentation/HTR pipeline; images are never rehosted (the public viewer "
        "loads GWLB IIIF directly, SPECS §3/§4)._"
    )
    add("")
    pct = (100.0 * stats.fetched / stats.fetch_targets) if stats.fetch_targets else 0.0
    add(
        f"- **Cached:** {stats.fetched:,} / {stats.fetch_targets:,} pages "
        f"({pct:.1f}%), {human_bytes(stats.total_bytes)} on disk."
    )
    if stats.fetched:
        add(f"- **Mean page size:** {human_bytes(stats.mean_bytes)}.")
        add(
            f"- **Projected full-corpus pull:** ≈ "
            f"{human_bytes(stats.est_full_corpus_bytes)} for all "
            f"{stats.fetch_targets:,} pages at the observed mean."
        )
        if stats.min_dims and stats.max_dims:
            add(
                f"- **Dimensions (of {stats.n_with_dims:,} measured):** "
                f"{stats.min_dims[0]}×{stats.min_dims[1]} … "
                f"{stats.max_dims[0]}×{stats.max_dims[1]} px."
            )
    add("")
    if stats.fetched:
        add("| Primary set | Cached | Target | % |")
        add("| --- | ---: | ---: | ---: |")
        for s, (f, t) in stats.by_set.items():
            p = f"{(100.0 * f / t):.1f}%" if t else "—"
            add(f"| {s} | {f:,} | {t:,} | {p} |")
        add("")
        add("| Dimensions | Cached pages |")
        add("| --- | ---: |")
        for label, n in stats.mp_histogram:
            add(f"| {label} | {n:,} |")
        add("")
        if stats.delivery:
            split = ", ".join(f"{k}: {v:,}" for k, v in sorted(stats.delivery.items()))
            add(f"Delivery mode of cached pages — {split}.")
            add("")
    return "\n".join(lines) + "\n"


def append_stats_to_census(census_path: Path, section: str) -> None:
    """Append (or replace) the image-cache section in ``reports/census.md``.

    Idempotent: an existing ``<!-- images-stats -->`` section is replaced, so
    re-running ``images stats`` doesn't stack duplicate sections.
    """
    census_path = Path(census_path)
    body = census_path.read_text(encoding="utf-8") if census_path.exists() else ""
    idx = body.find(CENSUS_MARKER)
    if idx != -1:
        body = body[:idx].rstrip() + "\n"
    else:
        body = body.rstrip() + "\n\n" if body else ""
    census_path.parent.mkdir(parents=True, exist_ok=True)
    census_path.write_text(body + "\n" + section, encoding="utf-8")


__all__ = [
    "cache_relpath",
    "DEFAULT_IMAGES_ROOT",
    "MIN_IMAGE_BYTES",
    "FetchStats",
    "ImageStats",
    "IntegrityError",
    "VerifyStats",
    "append_stats_to_census",
    "fetch_images",
    "human_bytes",
    "image_stats",
    "local_relpath",
    "render_stats_section",
    "sha256_hex",
    "verify_images",
]
