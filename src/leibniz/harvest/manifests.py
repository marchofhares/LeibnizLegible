"""IIIF manifest harvest — GWLB Presentation manifests → the ``pages`` table.

For each harvested work we fetch its IIIF Presentation **2.0** manifest
(``…/content/{id}/manifest.json``), cache the raw JSON under
``data/manifests/{id}.json``, and parse each canvas into a
:class:`~leibniz.db.Page`: sequence, canvas id, folio label, pixel dimensions,
and the **IIIF Image API service base** (``resource.service.@id``) that A2 will
append ``/full/full/0/default.jpg`` to for delivery derivatives, and D2 will
point OpenSeadragon at directly (we never rehost images, SPECS §3/§4).

The physical structMap page count already captured during the OAI harvest
(``works.n_canvases``) equals the manifest canvas count (verified on 00068642:
4 == 4), so the corpus page total — the A1 gate — does not depend on this stage.
This stage exists to lay down the per-page rows (with image-service URLs and
dimensions the METS lacks) that A2 downloads from and D1/D2 serve; it also
cross-checks each work's canvas count against ``n_canvases`` and flags drift.

Cache-first and resumable: a work whose manifest is already cached is re-parsed
offline; ``force`` re-fetches. Parsing is defensive — a canvas missing a
service, dimensions, or a whole manifest missing its sequence degrades to a
logged skip, never a crash.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.net import PoliteClient

DEFAULT_CACHE_DIR = Path("data/manifests")


@dataclass(slots=True)
class ParsedCanvas:
    """One canvas lifted from an IIIF manifest."""

    seq: int
    canvas_id: str | None
    label: str | None
    width: int | None
    height: int | None
    image_service_url: str | None
    image_url: str | None


def _as_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _label(value: object) -> str | None:
    """IIIF labels are sometimes a plain string, sometimes a language map/list."""
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    if isinstance(value, list) and value:
        return _label(value[0])
    if isinstance(value, dict):
        # v3 language map {"@value": "1r"} or {"none": ["1r"]}
        if "@value" in value:
            return _label(value["@value"])
        for v in value.values():
            got = _label(v)
            if got:
                return got
    return None


def _canvas_v2(canvas: dict, seq: int) -> ParsedCanvas:
    image_service_url = None
    image_url = None
    images = canvas.get("images") or []
    if images:
        resource = (images[0] or {}).get("resource") or {}
        image_url = resource.get("@id")
        service = resource.get("service") or {}
        if isinstance(service, list):
            service = service[0] if service else {}
        image_service_url = service.get("@id") if isinstance(service, dict) else None
    return ParsedCanvas(
        seq=seq,
        canvas_id=canvas.get("@id"),
        label=_label(canvas.get("label")),
        width=_as_int(canvas.get("width")),
        height=_as_int(canvas.get("height")),
        image_service_url=image_service_url,
        image_url=image_url,
    )


def _canvas_v3(canvas: dict, seq: int) -> ParsedCanvas:
    image_service_url = None
    image_url = None
    for page in canvas.get("items") or []:
        for anno in page.get("items") or []:
            body = anno.get("body") or {}
            if isinstance(body, list):
                body = body[0] if body else {}
            image_url = image_url or body.get("id")
            services = body.get("service") or []
            if isinstance(services, dict):
                services = [services]
            if services:
                svc = services[0]
                image_service_url = image_service_url or svc.get("@id") or svc.get("id")
    return ParsedCanvas(
        seq=seq,
        canvas_id=canvas.get("id"),
        label=_label(canvas.get("label")),
        width=_as_int(canvas.get("width")),
        height=_as_int(canvas.get("height")),
        image_service_url=image_service_url,
        image_url=image_url,
    )


def parse_manifest(manifest: dict) -> list[ParsedCanvas]:
    """Parse canvases from an IIIF Presentation 2.0 (or, defensively, 3.0) manifest.

    Sequence numbers are 1-based canvas positions (the canonical presentation
    order), matching the ``{id}:{seq:04d}`` page-id scheme.
    """
    canvases: list[ParsedCanvas] = []
    sequences = manifest.get("sequences")
    if sequences:  # Presentation 2.0
        raw = []
        for sequence in sequences:
            raw.extend(sequence.get("canvases") or [])
        canvases = [_canvas_v2(c or {}, i) for i, c in enumerate(raw, start=1)]
    elif manifest.get("items"):  # Presentation 3.0 fallback
        canvases = [_canvas_v3(c or {}, i) for i, c in enumerate(manifest["items"], start=1)]
    return canvases


def to_page(object_id: str, canvas: ParsedCanvas) -> db.Page:
    """Map a :class:`ParsedCanvas` onto a pending :class:`~leibniz.db.Page` row."""
    return db.Page(
        work_id=object_id,
        seq=canvas.seq,
        canvas_id=canvas.canvas_id,
        image_service_url=canvas.image_service_url,
        width=canvas.width,
        height=canvas.height,
        status="pending",
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ManifestStats:
    """Bookkeeping returned by :func:`harvest_manifests`."""

    works: int = 0
    fetched: int = 0
    cached: int = 0
    pages: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)
    count_mismatches: list[tuple[str, int, int]] = field(default_factory=list)


ProgressFn = Callable[[str, int], None]


def _cache_path(cache_dir: Path, object_id: str) -> Path:
    safe = object_id.replace("/", "_").replace(os.sep, "_")
    return cache_dir / f"{safe}.json"


def harvest_manifests(
    conn,
    *,
    client: PoliteClient,
    works: Sequence[db.Work] | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    force: bool = False,
    progress: ProgressFn | None = None,
) -> ManifestStats:
    """Fetch/parse each work's IIIF manifest into ``pages`` (cache-first).

    ``works`` restricts the pull to a slice (e.g. one set, or a dev sample); the
    default is every work in the store. Per-work failures are collected, not
    raised, so one bad manifest never sinks a corpus run.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    if works is None:
        works = list(db.iter_works(conn))

    stats = ManifestStats()
    for work in works:
        stats.works += 1
        path = _cache_path(cache_dir, work.gwlb_object_id)
        try:
            if path.exists() and not force:
                raw = path.read_bytes()
                stats.cached += 1
            else:
                if not work.manifest_url:
                    raise ValueError("work has no manifest_url")
                raw = client.get_bytes(work.manifest_url)
                path.write_bytes(raw)
                stats.fetched += 1
            manifest = json.loads(raw)
            canvases = parse_manifest(manifest)
        except Exception as exc:  # noqa: BLE001 — collect, don't abort the corpus
            stats.failures.append((work.gwlb_object_id, f"{type(exc).__name__}: {exc}"))
            continue

        for canvas in canvases:
            db.upsert_page(conn, to_page(work.gwlb_object_id, canvas))
        stats.pages += len(canvases)
        if work.n_canvases is not None and work.n_canvases != len(canvases):
            stats.count_mismatches.append((work.gwlb_object_id, work.n_canvases, len(canvases)))
        conn.commit()
        if progress is not None:
            progress(work.gwlb_object_id, len(canvases))
    return stats


__all__ = [
    "DEFAULT_CACHE_DIR",
    "ManifestStats",
    "ParsedCanvas",
    "harvest_manifests",
    "parse_manifest",
    "to_page",
]
