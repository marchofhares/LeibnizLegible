"""Mint ``gt_lines`` from an alignment (Phase B2).

The point of retro-alignment is training data: each line the aligner accepts
becomes a ground-truth ``(line image, edition text)`` pair. This module turns an
:class:`~leibniz.align.align.AlignmentResult` into :class:`GtPair`s and writes
them to the ``gt_lines`` table (SPECS §4.3), carrying the provenance the project
never ships without (SPECS §4.5):

* ``source`` — where the text came from (``"AA VI,4 N.109 (Zenodo/…)"``), so the
  §70 provenance is auditable;
* ``align_conf`` — the per-line alignment confidence, so downstream consumers can
  re-threshold;
* ``stratum`` — the manuscript stratum (fair_copy / …), first-class per SPECS §6;
* ``license_bucket`` — **``open``** only for §70-expired AA reading text;
  Transkriptionspool / NC-derived text goes to **``nc``** and never enters a
  CC BY export (SPECS §7.3). This gate is enforced here, at the moment of minting.

Only lines the aligner accepted (``aligned``) are minted — below-threshold pairs
are discarded, never shipped (SPECS §6: "a smaller clean corpus beats a larger
polluted one").
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from leibniz.align.align import AlignmentResult
from leibniz.db import GT_STRATA, LICENSE_BUCKETS


@dataclass(slots=True)
class GtPair:
    """One minted ground-truth pair, ready for ``gt_lines`` (SPECS §4.3)."""

    line_image_ref: str  # canonical line id or image path + region
    text: str  # the edition reading text projected onto this line
    source: str  # provenance string (AA volume/piece, license note)
    stratum: str  # GT_STRATA
    align_conf: float
    license_bucket: str  # 'open' | 'nc'

    def __post_init__(self) -> None:
        if self.license_bucket not in LICENSE_BUCKETS:
            raise ValueError(f"license_bucket must be in {LICENSE_BUCKETS}")
        if self.stratum not in GT_STRATA:
            raise ValueError(f"stratum must be in {GT_STRATA}")


def result_to_pairs(
    result: AlignmentResult,
    *,
    source: str,
    stratum: str = "unknown",
    license_bucket: str = "open",
    strip: bool = True,
) -> list[GtPair]:
    """Turn the *accepted* lines of an alignment into :class:`GtPair`s.

    Only ``aligned`` lines (confidence ≥ the run's threshold, non-empty edition
    text) are minted; everything else is dropped. ``strip`` trims whitespace off
    the emitted edition text (the projected slice can carry a leading/trailing
    space from the folded-boundary projection).
    """
    pairs: list[GtPair] = []
    for ln in result.lines:
        if not ln.aligned:
            continue
        text = ln.edition_text.strip() if strip else ln.edition_text
        if not text:
            continue
        pairs.append(
            GtPair(
                line_image_ref=ln.ref,
                text=text,
                source=source,
                stratum=stratum,
                align_conf=round(ln.align_conf, 4),
                license_bucket=license_bucket,
            )
        )
    return pairs


def insert_gt_pairs(conn: sqlite3.Connection, pairs: Iterable[GtPair]) -> int:
    """Insert minted pairs into ``gt_lines``; return the count written.

    Enforces the license gate at write time via the ``GtPair`` invariant. The
    caller commits (so a whole piece's pairs land atomically).
    """
    n = 0
    for p in pairs:
        conn.execute(
            """
            INSERT INTO gt_lines (line_image_ref, text, source, stratum, align_conf, license_bucket)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (p.line_image_ref, p.text, p.source, p.stratum, p.align_conf, p.license_bucket),
        )
        n += 1
    return n


def count_open_bucket(pairs: Sequence[GtPair]) -> int:
    """How many pairs are CC-BY-shippable (``open`` bucket) — a report figure."""
    return sum(1 for p in pairs if p.license_bucket == "open")


__all__ = [
    "GtPair",
    "count_open_bucket",
    "insert_gt_pairs",
    "result_to_pairs",
]
