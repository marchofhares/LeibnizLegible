"""GT factory orchestrator (Phase C2).

Scales the B2 retro-aligner across every §70-expired volume. For each piece
(:mod:`leibniz.align.volumes`) it runs the full chain:

    resolve canvases (folio range → pages)        [leibniz.align.resolve]
      → gather the piece's C1 HTR lines            [lines table, status='machine']
        → obtain the piece's §70 reading text      [injected extractor / pre-cache]
          → align (banded for long pieces)         [leibniz.align.align]
            → stratum-aware threshold + mint        [leibniz.align.stratum + pairs]
              → gt_lines (license_bucket, provenance)

The stratum sets the mint threshold per piece (B2: drafts need a higher bar than
fair copies — precision held, yield traded), and below-threshold lines are
discarded (SPECS §6: a smaller clean corpus beats a larger polluted one). The
license gate is enforced at mint time by :class:`~leibniz.align.pairs.GtPair`
(§70 → ``open``; Transkriptionspool → ``nc``, never in a CC BY export).

The one step that needs the network + an API key — extracting the reading text
from the volume PDF — is **injected** as an ``edition_text_for`` callable, so the
whole orchestration is offline-testable with a dict-backed provider; the
production provider wires :mod:`leibniz.align.pdftext`.
"""

from __future__ import annotations

import logging
import random
import sqlite3
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date

from leibniz import db
from leibniz.align.align import DEFAULT_THRESHOLD, HtrLine, align_piece
from leibniz.align.normalize import DEFAULT_NORM, AlignNorm
from leibniz.align.pairs import (
    GtPair,
    delete_gt_for_refs,
    has_gt_for_refs,
    insert_gt_pairs,
    result_to_pairs,
)
from leibniz.align.resolve import resolve_canvases
from leibniz.align.stratum import classify_piece
from leibniz.align.volumes import PieceRef, enumerate_pieces

# Mint threshold per stratum (B2 finding: drafts held to a higher bar). Fair
# copies clear comfortably; heavy revision / scrap trade yield for precision.
STRATUM_THRESHOLDS: dict[str, float] = {
    "fair_copy": 0.55,
    "light_revision": 0.62,
    "heavy_revision": 0.72,
    "scrap": 0.80,
    "unknown": 0.65,
}

# An edition-text provider returns a piece's constituted reading text, or None to
# skip (no source / no key / no page anchor).
EditionTextProvider = Callable[[PieceRef], str | None]

log = logging.getLogger(__name__)

# A piece's gt_lines are written in one IMMEDIATE transaction, retried on a
# lock collision. Six shard workers commit a piece each every few seconds; a
# deferred write that has to wait for another worker's commit then fails at
# once with "database is locked" (its WAL snapshot is stale — the busy timeout
# never gets a say). Taking the write lock first (BEGIN IMMEDIATE) lets the
# busy timeout queue the collision instead; the retries cover a timeout.
WRITE_RETRIES = 5
WRITE_BACKOFF_S = 0.5


@dataclass(slots=True)
class FactoryConfig:
    """Knobs for a factory run (recorded in the run params)."""

    today: date
    norm: AlignNorm = DEFAULT_NORM
    license_bucket: str = "open"
    stratum_thresholds: dict[str, float] = field(default_factory=lambda: dict(STRATUM_THRESHOLDS))

    def threshold_for(self, stratum: str) -> float:
        return self.stratum_thresholds.get(stratum, DEFAULT_THRESHOLD)


@dataclass(slots=True)
class PieceResult:
    """Outcome of minting one piece."""

    piece: PieceRef
    status: str  # minted | skipped:<reason>
    stratum: str = "unknown"
    threshold: float = 0.0
    n_canvases: int = 0
    n_htr_lines: int = 0
    n_minted: int = 0
    yield_rate: float = 0.0

    @property
    def minted(self) -> bool:
        return self.status == "minted"


@dataclass(slots=True)
class FactoryStats:
    """Aggregate outcome of a factory run."""

    run_id: int
    pieces_seen: int = 0
    pieces_minted: int = 0
    lines_minted: int = 0
    by_volume: dict[str, int] = field(default_factory=dict)
    by_series: dict[str, int] = field(default_factory=dict)
    by_stratum: dict[str, int] = field(default_factory=dict)
    skips: dict[str, int] = field(default_factory=dict)
    results: list[PieceResult] = field(default_factory=list)


def htr_lines_for_pages(conn, pages: Sequence[db.Page]) -> list[HtrLine]:
    """Gather the recognised C1 lines across a piece's pages, in reading order."""
    out: list[HtrLine] = []
    for page in pages:
        for ln in db.iter_lines_for_page(conn, page.id):
            if ln.text is None:
                continue  # segmented but not recognised — not usable yet
            out.append(
                HtrLine(
                    ref=ln.id,
                    text=ln.text,
                    meta={"page_id": page.id, "line_seq": ln.line_seq, "conf": ln.conf},
                )
            )
    return out


def page_stats_for_pages(conn, pages: Sequence[db.Page]) -> list[db.PageStats]:
    """The stored segmentation stats for a piece's pages (for the stratum)."""
    out: list[db.PageStats] = []
    for page in pages:
        ps = db.get_page_stats(conn, page.id)
        if ps is not None:
            out.append(ps)
    return out


def mint_piece(
    conn,
    piece: PieceRef,
    edition_text: str,
    config: FactoryConfig,
    *,
    insert: bool = True,
    resume: bool = False,
) -> PieceResult:
    """Resolve → gather HTR → align → stratum-threshold → mint one piece.

    Returns a :class:`PieceResult`; skips (with a reason) when the piece cannot be
    localized, has no recognised HTR lines, or no edition text. Idempotent when
    ``insert`` is set: existing ``gt_lines`` for this piece's line refs are cleared
    before the fresh mint. With ``resume``, a piece whose lines already carry
    ``gt_lines`` is skipped instead (an interrupted run picks up where it stopped).
    """
    if not piece.localizable:
        return PieceResult(piece, "skipped:not_localizable")
    assert piece.folio_range is not None and piece.work_id is not None
    res = resolve_canvases(conn, piece.work_id, piece.folio_range[0], piece.folio_range[1])
    if not res.pages:
        return PieceResult(piece, "skipped:no_canvases")
    htr = htr_lines_for_pages(conn, res.pages)
    if not htr:
        return PieceResult(piece, "skipped:no_htr_lines", n_canvases=len(res.pages))
    if not edition_text.strip():
        return PieceResult(piece, "skipped:no_edition_text", n_canvases=len(res.pages))
    if resume and has_gt_for_refs(conn, (ln.ref for ln in htr)):
        return PieceResult(piece, "skipped:already_minted", n_canvases=len(res.pages))

    stratum = classify_piece(page_stats_for_pages(conn, res.pages), textart=piece.textart).stratum
    threshold = config.threshold_for(stratum)
    alignment = align_piece(htr, edition_text, norm=config.norm, threshold=threshold)

    source = f"{piece.aa_label} (§70-expired AA reading text; katalog {piece.record_id})"
    pairs = result_to_pairs(
        alignment, source=source, stratum=stratum, license_bucket=config.license_bucket
    )
    if insert:
        write_pairs(conn, [ln.ref for ln in alignment.lines], pairs)
    return PieceResult(
        piece=piece,
        status="minted",
        stratum=stratum,
        threshold=threshold,
        n_canvases=len(res.pages),
        n_htr_lines=len(htr),
        n_minted=len(pairs),
        yield_rate=alignment.yield_rate,
    )


def write_pairs(
    conn,
    refs: Sequence[str],
    pairs: Sequence[GtPair],
    *,
    retries: int = WRITE_RETRIES,
    backoff_s: float = WRITE_BACKOFF_S,
) -> None:
    """Replace the ``gt_lines`` of these line refs with ``pairs``, atomically.

    One ``BEGIN IMMEDIATE`` transaction per piece (see ``WRITE_RETRIES``);
    a lock collision that outlives the busy timeout is retried with backoff,
    and the last failure propagates (the factory records it as
    ``skipped:error:OperationalError`` and moves on).
    """
    for attempt in range(1, retries + 1):
        try:
            conn.execute("BEGIN IMMEDIATE")
            delete_gt_for_refs(conn, refs)
            insert_gt_pairs(conn, pairs)
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            conn.rollback()
            if "lock" not in str(exc).lower() or attempt == retries:
                raise
            pause = backoff_s * attempt * (1 + random.random())  # noqa: S311 — jitter, not crypto
            log.warning(
                "gt_lines write locked (attempt %d/%d): %s; retrying", attempt, retries, exc
            )
            time.sleep(pause)


def run_factory(
    conn,
    *,
    config: FactoryConfig,
    edition_text_for: EditionTextProvider,
    series: int | None = None,
    volume: int | None = None,
    insert: bool = True,
    progress: Callable[[PieceResult], None] | None = None,
    pieces: Sequence[PieceRef] | None = None,
    shard: tuple[int, int] | None = None,
    resume: bool = False,
) -> FactoryStats:
    """Enumerate §70 pieces and mint each, recording one ``runs`` row.

    ``edition_text_for`` supplies each piece's reading text (production: extract
    from the volume PDF; tests: a dict). Aggregates minted-line counts by volume /
    series / stratum for the GT-factory report. ``pieces`` may be pre-enumerated
    (the CLI does, to size its progress bar); ``shard=(i, n)`` keeps every
    ``n``-th piece starting at ``i`` so parallel workers split one pass
    disjointly; ``resume`` skips pieces already minted.
    """
    run_id = db.start_run(
        conn,
        "gt_factory",
        model="retro-aligner",
        params={
            "series": series,
            "volume": volume,
            "license_bucket": config.license_bucket,
            "stratum_thresholds": config.stratum_thresholds,
            "shard": list(shard) if shard else None,
            "resume": resume,
        },
        git_sha=db.git_sha(),
    )
    if pieces is None:
        pieces, _enum = enumerate_pieces(conn, today=config.today, series=series, volume=volume)
    pieces = shard_pieces(pieces, shard)
    stats = FactoryStats(run_id=run_id)
    for piece in pieces:
        stats.pieces_seen += 1
        text = edition_text_for(piece) or ""
        try:
            result = mint_piece(conn, piece, text, config, insert=insert, resume=resume)
        except Exception as exc:  # noqa: BLE001 — one bad piece must not end the shard
            if insert:
                conn.rollback()
            log.warning(
                "piece %s (%s) failed: %s: %s",
                piece.record_id,
                piece.aa_label,
                type(exc).__name__,
                exc,
            )
            result = PieceResult(piece, f"skipped:error:{type(exc).__name__}")
        stats.results.append(result)
        if result.minted:
            stats.pieces_minted += 1
            stats.lines_minted += result.n_minted
            stats.by_volume[piece.volume_label] = (
                stats.by_volume.get(piece.volume_label, 0) + result.n_minted
            )
            skey = _series_roman(piece.series)
            stats.by_series[skey] = stats.by_series.get(skey, 0) + result.n_minted
            stats.by_stratum[result.stratum] = (
                stats.by_stratum.get(result.stratum, 0) + result.n_minted
            )
        else:
            reason = result.status.split(":", 1)[-1]
            stats.skips[reason] = stats.skips.get(reason, 0) + 1
        if progress is not None:
            progress(result)
    db.finish_run(
        conn,
        run_id,
        n_input=stats.pieces_seen,
        n_ok=stats.pieces_minted,
        n_failed=stats.pieces_seen - stats.pieces_minted,
    )
    return stats


def shard_pieces(pieces: Sequence[PieceRef], shard: tuple[int, int] | None) -> Sequence[PieceRef]:
    """Every ``n``-th piece starting at ``i`` for ``shard=(i, n)``; all if ``None``.

    Enumeration order is deterministic (katalog record order), so N workers
    passing ``(0, N) … (N-1, N)`` cover the piece list exactly once.
    """
    if shard is None:
        return pieces
    index, count = shard
    return [p for k, p in enumerate(pieces) if k % count == index]


def _series_roman(series: int) -> str:
    return {1: "I", 2: "II", 3: "III", 4: "IV", 6: "VI", 7: "VII"}.get(series, str(series))


def dict_provider(mapping: dict[str, str]) -> EditionTextProvider:
    """An edition-text provider backed by a ``{record_id: reading_text}`` dict.

    Used by tests and by a pre-extraction cache: extract all pieces' reading text
    once (vision pass, keyed by record id), then run the factory offline against
    the cache.
    """

    def provider(piece: PieceRef) -> str | None:
        return mapping.get(piece.record_id)

    return provider


__all__ = [
    "STRATUM_THRESHOLDS",
    "EditionTextProvider",
    "FactoryConfig",
    "FactoryStats",
    "PieceResult",
    "dict_provider",
    "htr_lines_for_pages",
    "mint_piece",
    "page_stats_for_pages",
    "run_factory",
    "shard_pieces",
]
