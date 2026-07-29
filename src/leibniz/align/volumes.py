"""§70-expired volume ingestion — the piece registry (Phase C2).

The GT factory scales B2 across every §70-expired AA volume (``legal.py``). Its
first question is *what are the pieces, and where is each one's scan?* — and the
answer is a **join we already have the parts for**:

    for each §70-expired volume (legal.expired_volumes)
      → katalog records whose AA reference cites that volume  (the pieces)
        → the GWLB work each piece's scan lives in            (the A3 crosswalk)
          → the canvases inside that work                     (the folio resolver)

So a piece is a katalog record; its edition text comes from the expired volume's
print (extracted per B2's :mod:`leibniz.align.pdftext`, apparatus excluded), and
its scan is localized by :mod:`leibniz.align.resolve`. This module builds that
piece list (:func:`enumerate_pieces`), holds the per-volume source registry
(:class:`VolumeSource`), and provides the **extraction-QA** bookkeeping the prompt
asks for (:func:`assess_extraction` — a spot-check error estimate over sampled
pages). The heavy, network+key steps (download the volume PDF, vision-extract the
reading text) live in :mod:`leibniz.align.pdftext` and the factory; the join and
the QA math here are pure and offline-testable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

from leibniz import db
from leibniz.align.resolve import folio_range_from_signature
from leibniz.htr.metrics import PHILIUMM_POLICY, score_line
from leibniz.legal import Volume, expired_volumes

# --------------------------------------------------------------------------- #
# Per-volume source registry (operator verifies the identifiers before a run)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class VolumeSource:
    """Where an expired volume's reading text can be extracted from.

    ``ia_id`` is an Internet Archive scan identifier and ``leibnizedition_url`` /
    ``repo_url`` the edition's own PDF homes (SPECS §1.4). ``has_text_layer`` picks
    the cheaper text-layer extraction over a vision pass. These identifiers are
    **operator-verified before a run** (they drift); the registry ships the ones
    confirmed at research time and is otherwise a documented TODO per volume.
    """

    series: int
    volume: int | str
    ia_id: str | None = None
    leibnizedition_url: str | None = None
    repo_url: str | None = None
    has_text_layer: bool = False
    note: str = ""

    @property
    def key(self) -> tuple[int, str]:
        return (self.series, str(self.volume))


# Starter registry. Deliberately small and honest: the AA PDFs are free via
# leibnizedition.de / rep.adw-goe.de (SPECS §1.4), but the exact per-volume IA
# ids / repo URLs must be confirmed live before a bulk pull, so most entries are
# left for the operator to fill. The factory skips a volume with no source.
VOLUME_SOURCES: dict[tuple[int, str], VolumeSource] = {
    (6, "4"): VolumeSource(
        6,
        4,
        leibnizedition_url="https://www.leibnizedition.de/",
        has_text_layer=False,
        note="Reihe VI,4 (1999, four parts A–D); the B2 prototype extracted N.109 here.",
    ),
    (1, "1"): VolumeSource(
        1,
        1,
        leibnizedition_url="https://www.leibnizedition.de/",
        note="Reihe I,1 (1923); correspondence, the favourable fair-copy stratum.",
    ),
    (2, "1"): VolumeSource(
        2,
        1,
        leibnizedition_url="https://www.leibnizedition.de/",
        note="Use the 1926 print (§70-free); NOT the 2006 Neubearbeitung (protected to 2032).",
    ),
}


def volume_source(series: int, volume: int | str) -> VolumeSource | None:
    """The registered source for a volume, or ``None`` if not yet configured."""
    return VOLUME_SOURCES.get((series, str(volume)))


def expired_volume_index(today: date) -> dict[tuple[int, str], Volume]:
    """``(series, volume) -> the expired edition`` for every §70-free volume.

    Keyed by ``(series, str(volume))`` so a katalog AA reference (series+volume)
    can be tested for §70-freeness in one lookup. When a volume has several
    editions (II,1: 1926 free, 2006 protected) the **expired** one is kept — the
    print the factory must extract from.
    """
    out: dict[tuple[int, str], Volume] = {}
    for v in expired_volumes(today):
        key = (v.series, str(v.volume))
        # keep the earliest-published expired edition (the one whose print is free)
        if key not in out or v.first_publication_year < out[key].first_publication_year:
            out[key] = v
    return out


# --------------------------------------------------------------------------- #
# Piece enumeration (the join)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PieceRef:
    """One AA piece to be aligned: its katalog record, work, and localization."""

    record_id: str
    series: int
    volume: int | str
    piece: str
    work_id: str | None
    signature: str | None
    folio_range: tuple[int, int] | None
    textart: str | None
    match_method: str | None
    match_conf: float | None

    @property
    def volume_label(self) -> str:
        roman = {1: "I", 2: "II", 3: "III", 4: "IV", 6: "VI", 7: "VII"}.get(
            self.series, str(self.series)
        )
        return f"{roman},{self.volume}"

    @property
    def aa_label(self) -> str:
        return f"AA {self.volume_label} N.{self.piece}"

    @property
    def localizable(self) -> bool:
        """True when we know the work *and* the folio range → resolvable canvases."""
        return self.work_id is not None and self.folio_range is not None


@dataclass(slots=True)
class EnumerationStats:
    """Bookkeeping for :func:`enumerate_pieces`."""

    records_scanned: int = 0
    pieces: int = 0
    with_work: int = 0
    with_folio_range: int = 0
    localizable: int = 0
    by_volume: dict[str, int] = field(default_factory=dict)


def enumerate_pieces(
    conn,
    *,
    today: date,
    series: int | None = None,
    volume: int | None = None,
) -> tuple[list[PieceRef], EnumerationStats]:
    """Enumerate the §70-expired pieces from the katalog × crosswalk × folios.

    Walks ``katalog_records``; for every AA reference that cites a §70-expired
    volume (optionally filtered to one ``series``/``volume``), emits a
    :class:`PieceRef` carrying the work id (best crosswalk link), the folio range
    (parsed from the record's signature), and the katalog text type. A record that
    cites several expired volumes yields one piece per citation.
    """
    expired = expired_volume_index(today)
    best_link = db.best_crosswalk_by_record(conn)
    pieces: list[PieceRef] = []
    stats = EnumerationStats()

    for rec in db.iter_katalog_records(conn):
        stats.records_scanned += 1
        signature = rec.shelfmark_refs[0] if rec.shelfmark_refs else None
        folio_range = folio_range_from_signature(signature)
        textart = rec.metadata.get("textart") if rec.metadata else None
        link = best_link.get(rec.record_id)
        seen: set[tuple[int, str]] = set()
        for ref in rec.aa_refs:
            s, v = ref.get("series"), ref.get("volume")
            if s is None or v is None:
                continue
            if (s, str(v)) not in expired:
                continue
            if series is not None and s != series:
                continue
            if volume is not None and v != volume:
                continue
            vk = (s, str(v))
            if vk in seen:
                continue
            seen.add(vk)
            piece = PieceRef(
                record_id=rec.record_id,
                series=s,
                volume=v,
                piece=str(ref.get("piece", "")),
                work_id=link.work_id if link else None,
                signature=signature,
                folio_range=folio_range,
                textart=textart,
                match_method=link.match_method if link else None,
                match_conf=link.match_conf if link else None,
            )
            pieces.append(piece)
            stats.pieces += 1
            stats.with_work += int(piece.work_id is not None)
            stats.with_folio_range += int(folio_range is not None)
            stats.localizable += int(piece.localizable)
            stats.by_volume[piece.volume_label] = stats.by_volume.get(piece.volume_label, 0) + 1
    return pieces, stats


# --------------------------------------------------------------------------- #
# Extraction QA (spot-check error estimate)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ExtractionQA:
    """A reading-text extraction-quality estimate over sampled pages.

    Computed by comparing the production extraction of a sampled page against a
    control (a second vision pass, or a manual transcription): pages whose two
    reading-texts diverge beyond ``flag_cer`` are flagged as unstable extractions
    (usually apparatus bleed-through or a missed column). ``error_rate`` is the
    flagged fraction — the number to report in the GT-factory card (SPECS §6).
    """

    n_sampled: int
    n_flagged: int
    n_empty_disagreements: int  # one pass found reading text, the other did not
    mean_disagreement_cer: float

    @property
    def error_rate(self) -> float:
        return self.n_flagged / self.n_sampled if self.n_sampled else 0.0

    @property
    def mean_agreement(self) -> float:
        return 1.0 - self.mean_disagreement_cer


def assess_extraction(pairs: Sequence[tuple[str, str]], *, flag_cer: float = 0.10) -> ExtractionQA:
    """Estimate extraction error from ``(production, control)`` page-text pairs.

    Each pair is two independent extractions of the same edition page. A page is
    *flagged* when the two disagree by more than ``flag_cer`` (character error
    rate under the frozen HTR normalization policy, so the estimate is comparable
    to the CER numbers elsewhere), or when exactly one pass returns empty (a
    reading-text / no-reading-text disagreement). Pure — no API calls.
    """
    n = len(pairs)
    if n == 0:
        return ExtractionQA(0, 0, 0, 0.0)
    flagged = 0
    empty_disagree = 0
    total_cer = 0.0
    for prod, control in pairs:
        prod_e, ctrl_e = not prod.strip(), not control.strip()
        if prod_e != ctrl_e:
            empty_disagree += 1
            flagged += 1
            total_cer += 1.0
            continue
        if prod_e and ctrl_e:
            continue  # both empty (a genuine no-reading-text page) — agreement
        cer = score_line(control, prod, PHILIUMM_POLICY).cer
        total_cer += cer
        if cer > flag_cer:
            flagged += 1
    return ExtractionQA(
        n_sampled=n,
        n_flagged=flagged,
        n_empty_disagreements=empty_disagree,
        mean_disagreement_cer=total_cer / n,
    )


__all__ = [
    "VOLUME_SOURCES",
    "EnumerationStats",
    "ExtractionQA",
    "PieceRef",
    "VolumeSource",
    "assess_extraction",
    "enumerate_pieces",
    "expired_volume_index",
    "volume_source",
]
