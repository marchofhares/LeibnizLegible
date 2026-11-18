"""The fragment pack: German A/B pairs for Calculemus (Phase G1; the draw G1b).

The game's contract (Calculemus SPECS §6.6, schema_version 1; mirrored in
``fragment_pack.schema.json`` beside this module) asks for one row per line:
the line's place on its page image, exactly two candidate readings, and — on
a share of the rows — a gold answer the game calibrates its players against.
For every line of K1's German pieces two machine readings exist: the stored
text (``lines``, the row :func:`~leibniz.search.documents.latest_lines`
shows) and K2's reading by the Bern Kurrent model (the readings JSONL), and
they disagree exactly where the site reads worst. This module turns them into
rows; ``leibniz pack fragments`` opens the store read-only and writes the pack.

The stored text is the one the site shows, whichever run wrote it: v1's when
G1 was built, and since K4 (run 617, 2026-10-30) the Leibniz Kurrent reader's
on the German pages that run read. ``as_of_run`` reads the store as an earlier
run left it (rows of later runs ignored), which pins the first candidate to
the reading shown then; the names below (``v1_text``, verdict ``v1``,
``V1_SOURCE``) mean that stored reading, the candidate ``htr_best``.
``only_records`` keeps the lines of the records listed and no others — K3's
validation pieces (``reports/kurrent/k3-val-pieces.csv``), whose lines the
Leibniz Kurrent reader was not trained on, so that its reading of a gold
line is not a reading of its own training text. A line on a page two pieces
share stays with its piece (below) and is skipped as ``other_record`` when
that piece is not listed.

* **Rows.** A line on a German piece's pages whose two readings are non-empty
  and differ after whitespace normalisation, the longer ``min_chars`` to
  ``max_chars`` characters and the shorter at least ``min_ratio`` of the
  longer (the floor, below), on a page the image mirror serves (a cached
  ``local_path``; the mirror is the cache's layout, so the polygons sit on its
  pixels), with geometry and complete provenance; a scan the library
  registered twice gives each line one row, as the index counts it
  (``images/twins.py``). The candidates' order is
  drawn per line under the seed. The page's stratum, the hand and the
  language are the piece's; a page two pieces share goes to the piece the
  line's reader-minted row names, else to the lower record id.
* **The §70 rule.** The pack is ``license_bucket 'open'`` only: a line whose
  piece's volume is not §70-free on ``today`` is refused (counted, and
  :func:`build_row` raises :class:`Refused` if handed one). A record the
  census cites in several volumes is refused unless every one is free.
* **The floor.** The length window bounds the longer reading; ``min_ratio``
  (0.5) bounds the shorter against it: a pair whose shorter reading is under
  half the longer is skipped as ``lopsided``. One reader gave up on such a
  line, and the pair asks a player nothing. A ratio rather than ``min_chars``
  on the shorter reading as well, because a failed reading is short against
  its line, not in itself: ten characters against fifty would pass a
  ten-character floor, and nine against eleven, a fair pair, would not. It is
  also the count the first pack was asked for (STATUS.md, Open question 30 h).
* **Gold, drawn first** (:func:`choose_gold`). A gold candidate is an
  eligible line with a row K2's reader minted (``reader
  trocr-kurrent-xvi-xvii`` in its source) that the licence registry places in
  the open deposit (``legal.deposit_for``: the NC channels, Potsdam and the
  GWLB repository, never). The candidate equal to the minted text under the
  aligner's fold (``align/normalize``) is the truth; neither equal, the row
  is gold with ``both_wrong``; both equal, the fold cannot tell them apart
  and the row is no gold. The gold is drawn among *all* the eligible lines,
  before the strata are filled: as many rows as the supply allows with at
  most ``gold_rate`` of the rows gold and at most ``bad_gold_share`` of the
  gold both-wrong (0.5: every truth so far is the Bern reading, and with half
  the gold both-wrong a player who always takes it is found out). The truths
  and the both-wrong rows are each spread over the strata as the rows are
  (below), a stratum short of them giving its share to the others, so the
  cap is reached whenever the supply allows. The minted text is the
  edition's normalised reading, so a both-wrong verdict can also mean an
  expansion the fold does not forgive — hence the cap.
* **Selection** (:func:`select_lines`). The strata are then filled to the
  limit around the gold: equal numbers per stratum by default, or the
  ``strata`` weights (:func:`parse_strata`; a stratum the weights leave out
  gives no row, gold included); a stratum short of lines gives its surplus to
  the others (:func:`allocate`), and a stratum whose gold alone is over its
  share keeps its gold. Leibniz's own hand (the strict rule,
  ``catalog/hands.py``) is kept at least at its share of the eligible lines,
  the gold counted in.
* **Order.** The rows stand in an order shuffled under the seed, so neither
  the gold nor a work sits at the head of the file; the pack says which rows
  are gold only in each row's ``gold`` object, which is the game's to keep
  from its players.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sqlite3
import statistics
from collections import Counter, defaultdict
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from fractions import Fraction
from pathlib import Path

from leibniz import db, legal
from leibniz.align import audit
from leibniz.align.kurrent_read import DEFAULT_READER
from leibniz.align.normalize import normalize
from leibniz.align.pairs import (
    READER_SQL,
    channels_from_source,
    collapse_whitespace,
    has_record_column,
    reader_from_source,
    record_id_from_source,
)
from leibniz.align.volumes import expired_volume_index
from leibniz.catalog.hands import is_leibniz_hand
from leibniz.db import GT_STRATA
from leibniz.images.twins import TwinGroup, resolve_work
from leibniz.search.documents import latest_lines
from leibniz.web import attribution as attr
from leibniz.web.iiif import canvas_id as site_canvas_id
from leibniz.web.images import ImageSource

from .check import FRAGMENT_HEADER, SCHEMA_VERSION

DEFAULT_READINGS = Path("data/kurrent/k2-readings") / f"{DEFAULT_READER}.jsonl"
DEFAULT_PIECES = Path("data/kurrent/german_pieces.jsonl")
DEFAULT_IMAGE_BASE_URL = "https://images.leibnizlegible.com"
# web.api.SITE_URL: a page the GWLB serves without a IIIF canvas (the static
# works) gets the canvas of this project's own manifest instead.
SITE_URL = "https://leibnizlegible.com"
DEFAULT_LIMIT = 2000
DEFAULT_GOLD_RATE = 0.25
DEFAULT_BAD_GOLD_SHARE = 0.5
DEFAULT_MIN_CHARS = 10
DEFAULT_MAX_CHARS = 50
DEFAULT_MIN_RATIO = 0.5  # the shorter reading against the longer
PACK_LANGS = ("de", "mixed")
V1_SOURCE = "htr_best"  # the stored v1 text
ALT_SOURCE = "model_alt"  # the Bern reading
GOLD_SOURCE = "aa_aligned"

# Why a line on a German piece's pages is not a row, in the order the rules
# are applied: a line is counted under the first rule it fails, so the §70
# refusals (last) are lines that would otherwise have been rows.
SKIP_REASONS = (
    "no_image",  # the page has no cached image (no local_path): the mirror lacks it
    "no_page_size",  # the page has no width/height to clamp the box to
    "twin_elsewhere",  # another registration of the same scan carries the line (W5)
    "other_record",  # only_records: the line's piece is not among the records listed
    "already_corrected",  # the row latest_lines shows is not machine text (a crowd row)
    "no_v1_text",
    "no_reading",  # the readings file has no row for the line
    "empty_reading",
    "same_text",  # the two readings agree after whitespace normalisation
    "too_short",  # the longer reading is under min_chars
    "too_long",  # … or over max_chars
    "lopsided",  # the shorter reading is under min_ratio of the longer
    "not_german",  # the piece's language is neither de nor mixed
    "no_provenance",  # the v1 row lacks its confidence or its run
    "no_geometry",  # no polygon or baseline to box
    "no_shelfmark",  # neither the work nor the piece names one
    "not_70_expired",  # refused: the piece's volume is not §70-free on the day
)
# Gold verdicts of a reader-minted row against the two candidates.
VERDICTS = ("v1", "alt", "both_wrong", "ambiguous", "unfoldable")


class Refused(ValueError):
    """A line whose piece's volume is not §70-free: never emitted."""


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Piece:
    """One German piece of K1's census (``german_pieces.jsonl``), by record."""

    record_id: str
    work_id: str | None
    volumes: tuple[tuple[int, str], ...]  # (series, volume) of every citation
    aa_label: str | None
    stratum: str
    hand: str
    leibniz_hand: bool  # catalog/hands.py, the strict rule
    language: str
    signature: str | None
    page_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Reading:
    """K2's reading of one line (the readings JSONL: line_id, text, conf, model, …)."""

    text: str
    conf: float | None
    model: str


@dataclass(frozen=True, slots=True)
class GtRow:
    """A ``gt_lines`` row K2's reader minted, with the deposit the registry gives it."""

    gt_id: int
    line_id: str
    text: str
    source: str
    align_conf: float | None
    license_bucket: str
    record_id: str | None
    deposit: str | None  # legal.deposit_for: "open", "nc" or None
    aa_ref: str | None  # the AA label the source opens with


def record_key(record_id: str) -> tuple[int, int, str]:
    """Catalogue record ids in numeric order where they are numbers."""
    return (0, int(record_id), "") if record_id.isdigit() else (1, 0, record_id)


def _volume_of(row: Mapping) -> tuple[int, str] | None:
    """``(series, volume)`` from the census's ``series`` and ``volume_label`` ("IV,3")."""
    label = str(row.get("volume_label") or "")
    series = row.get("series")
    if series is None or "," not in label:
        return None
    return int(series), label.split(",", 1)[1].strip()


def piece_from_row(row: Mapping) -> Piece:
    """One census row as a :class:`Piece`; the hand under the strict rule."""
    hand = str(row.get("hand") or "none")
    stratum = row.get("stratum")
    vol = _volume_of(row)
    return Piece(
        record_id=str(row["record_id"]),
        work_id=row.get("work_id"),
        volumes=(vol,) if vol else (),
        aa_label=row.get("aa_label"),
        stratum=stratum if stratum in GT_STRATA else "unknown",
        hand=hand,
        leibniz_hand=is_leibniz_hand(hand, row.get("absender")),
        language=str(row.get("language") or "unknown"),
        signature=row.get("signature"),
        page_ids=tuple(row.get("page_ids") or ()),
    )


def _iter_jsonl(path: Path | str) -> Iterator[dict]:
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                yield json.loads(raw)


def load_pieces(path: Path | str) -> list[Piece]:
    """The census's German pieces, one per record: the census lists a record
    once per citation, so the rows of one record merge (their pages united,
    their volumes kept; the first row's stratum, hand and language)."""
    merged: dict[str, Piece] = {}
    for row in _iter_jsonl(path):
        p = piece_from_row(row)
        cur = merged.get(p.record_id)
        if cur is None:
            merged[p.record_id] = p
        else:
            merged[p.record_id] = replace(
                cur,
                page_ids=tuple(dict.fromkeys(cur.page_ids + p.page_ids)),
                volumes=tuple(dict.fromkeys(cur.volumes + p.volumes)),
            )
    return sorted(merged.values(), key=lambda p: record_key(p.record_id))


def load_readings(path: Path | str) -> dict[str, Reading]:
    """``line_id → Reading`` from K2's readings JSONL (the last row of a line wins)."""
    out: dict[str, Reading] = {}
    models: dict[str, str] = {}
    for row in _iter_jsonl(path):
        model = str(row.get("model") or "")
        conf = row.get("conf")
        out[row["line_id"]] = Reading(
            text=str(row.get("text") or ""),
            conf=float(conf) if conf is not None else None,
            model=models.setdefault(model, model),
        )
    return out


def aa_label_from_source(source: str | None) -> str | None:
    """The AA label a factory source opens with (``"AA IV,3 N.41"``), or ``None``."""
    head = (source or "").split(" (", 1)[0].strip()
    return head if head.startswith("AA ") else None


def load_reader_rows(conn: sqlite3.Connection, reader: str = DEFAULT_READER) -> dict[str, GtRow]:
    """``line_id → GtRow`` for every ``gt_lines`` row the reader minted (K2),
    the deposit from the registry; a line minted twice keeps the higher
    alignment confidence (the factory keeps each line once)."""
    rec_col = ", record_id" if has_record_column(conn) else ""
    out: dict[str, GtRow] = {}
    sql = (
        "SELECT id, line_image_ref, text, source, align_conf, license_bucket"
        f"{rec_col} FROM gt_lines WHERE {READER_SQL}"
    )
    for r in conn.execute(sql):
        source = r["source"]
        if reader_from_source(source) != reader:
            continue
        rec = (r["record_id"] if rec_col else None) or record_id_from_source(source)
        row = GtRow(
            gt_id=int(r["id"]),
            line_id=r["line_image_ref"],
            text=r["text"],
            source=source,
            align_conf=r["align_conf"],
            license_bucket=r["license_bucket"],
            record_id=rec,
            deposit=legal.deposit_for(channels_from_source(source), r["license_bucket"]),
            aa_ref=aa_label_from_source(source),
        )
        cur = out.get(row.line_id)
        if cur is None or (row.align_conf or 0.0) > (cur.align_conf or 0.0):
            out[row.line_id] = row
    return out


def reader_mint_runs(conn: sqlite3.Connection, reader: str = DEFAULT_READER) -> list[int]:
    """The ``gt_factory`` runs that minted the reader's rows (K2: run 609)."""
    rows = conn.execute(
        "SELECT run_id FROM runs WHERE stage = 'gt_factory' AND model = ?",
        (f"retro-aligner+{reader}",),
    ).fetchall()
    return sorted(int(r[0]) for r in rows)


# --------------------------------------------------------------------------- #
# Pure rules
# --------------------------------------------------------------------------- #


def piece_expired(piece: Piece, index: Mapping[tuple[int, str], legal.Volume]) -> bool:
    """Every volume the piece is cited in is §70-free (``expired_volume_index``)."""
    return bool(piece.volumes) and all(v in index for v in piece.volumes)


def bbox_of(
    polygon: Sequence | None,
    baseline: Sequence | None,
    *,
    width: int,
    height: int,
    pad: int = audit.CROP_PAD,
) -> dict[str, int] | None:
    """The line's box in page pixels, ``{x, y, w, h}``: the audit's crop
    (:func:`~leibniz.align.audit.crop_box`, ``pad`` pixels of context, a band
    about the baseline where no polygon exists, clamped to the page)."""
    box = audit.crop_box(polygon, baseline, width=width, height=height, pad=pad)
    if box is None:
        return None
    left, top, right, bottom = box
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def fold_verdict(v1: str, alt: str, minted: str) -> str:
    """Which candidate the minted text names under the aligner's fold:
    ``v1`` | ``alt`` | ``both_wrong`` | ``ambiguous`` (both fold to it) |
    ``unfoldable`` (the minted text folds to nothing)."""
    target = normalize(minted)
    if not target:
        return "unfoldable"
    a, b = normalize(v1) == target, normalize(alt) == target
    if a and b:
        return "ambiguous"
    if a:
        return "v1"
    if b:
        return "alt"
    return "both_wrong"


def lopsided(v1: str, alt: str, min_ratio: float) -> bool:
    """The shorter reading is under ``min_ratio`` of the longer: one reader
    gave up on the line (the floor, module docstring)."""
    short, long = sorted((len(v1), len(alt)))
    return short + 1e-9 < min_ratio * long


def parse_strata(spec: str) -> dict[str, float]:
    """``"fair_copy=0.35,light_revision=0.35,heavy_revision=0.2,scrap=0.1"``
    as weights by stratum. The weights are relative (they need not sum to 1);
    a stratum left out or given 0 gives no row. Raises :class:`ValueError`
    for a name that is no stratum, a name twice, a weight that is no
    non-negative number, or no weight above 0."""
    out: dict[str, float] = {}
    for part in spec.split(","):
        if not part.strip():
            continue
        name, sep, value = part.partition("=")
        name = name.strip()
        if not sep or name not in audit.STRATA:
            raise ValueError(
                f"{part.strip()!r}: wanted <stratum>=<weight>, the stratum one of "
                f"{', '.join(audit.STRATA)}"
            )
        if name in out:
            raise ValueError(f"{name} is named twice")
        try:
            weight = float(value)
        except ValueError as exc:
            raise ValueError(f"{name}: {value.strip()!r} is not a number") from exc
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"{name}: the weight must be 0 or more, got {value.strip()}")
        out[name] = weight
    if not any(w > 0 for w in out.values()):
        raise ValueError("no stratum has a weight above 0")
    return out


def drawn_strata(weights: Mapping[str, float] | None) -> tuple[str, ...]:
    """The strata the draw takes rows from: all of them, or the weighted ones."""
    if weights is None:
        return audit.STRATA
    return tuple(s for s in audit.STRATA if weights.get(s, 0) > 0)


def allocate(
    available: Mapping[str, int],
    n: int,
    *,
    weights: Mapping[str, float] | None = None,
    floor: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """Split ``n`` draws over the strata that have lines: in proportion to
    ``weights`` (equal without them, and then ``audit.allocate``'s split),
    never more than a stratum has, never fewer than its ``floor`` (the gold
    already drawn there). A stratum short of its share gives the surplus to
    the others in the same proportion; a stratum whose floor is over its
    share keeps the floor and the others give way. Whole numbers by largest
    remainder, ties in the strata's order."""
    strata = [s for s in drawn_strata(weights) if available.get(s, 0) > 0]
    lo = {s: min(available[s], (floor or {}).get(s, 0)) for s in strata}
    w = {s: Fraction(str(weights[s])) if weights else Fraction(1) for s in strata}
    n = max(sum(lo.values()), min(n, sum(available[s] for s in strata)))
    pinned: dict[str, int] = {}
    free = list(strata)
    share: dict[str, Fraction] = {}
    while free:
        left = n - sum(pinned.values())
        total = sum(w[s] for s in free)
        share = {s: left * w[s] / total for s in free}
        over = {s: share[s] - available[s] for s in free if share[s] > available[s]}
        under = {s: lo[s] - share[s] for s in free if share[s] < lo[s]}
        if not over and not under:
            break
        # pin the side that is further out; the rest is shared out again
        if sum(over.values()) >= sum(under.values()):
            pinned.update({s: available[s] for s in over})
        else:
            pinned.update({s: lo[s] for s in under})
        free = [s for s in free if s not in pinned]
    alloc = dict(pinned)
    alloc.update({s: math.floor(share[s]) for s in free})
    spare = n - sum(alloc.values())
    by_remainder = sorted(free, key=lambda s: -(share[s] - alloc[s]))  # stable: strata order
    for s in by_remainder[:spare]:
        alloc[s] += 1
    return {s: alloc[s] for s in strata if alloc[s]}


def gold_counts(
    n_rows: int, n_truth: int, n_bad: int, gold_rate: float, bad_share: float
) -> tuple[int, int]:
    """``(truth, both_wrong)`` rows to mark gold: as many as the supply allows
    with at most ``gold_rate`` of the rows gold and at most ``bad_share`` of
    the gold both-wrong, the both-wrong share as near its cap as it can be."""
    cap = math.floor(gold_rate * n_rows + 1e-9)
    for n in range(min(cap, n_truth + n_bad), 0, -1):
        b = min(n_bad, math.floor(bad_share * n + 1e-9))
        if n - b <= n_truth:
            return n - b, b
    return 0, 0


def leibniz_quotas(
    quotas: Mapping[str, int], own: Mapping[str, int], sizes: Mapping[str, int], target: int
) -> dict[str, int]:
    """Lines in Leibniz's own hand to draw per stratum: each stratum's own
    share of its quota first, then one more at a time where most room is left
    until ``target`` is met (or no stratum has his lines to give)."""
    order = [s for s in audit.STRATA if s in quotas]
    cap = {s: min(quotas[s], own.get(s, 0)) for s in order}
    take = {
        s: min(cap[s], -(-quotas[s] * own.get(s, 0) // sizes[s])) if sizes[s] else 0 for s in order
    }
    need = target - sum(take.values())
    while need > 0:
        room = [(cap[s] - take[s], -i, s) for i, s in enumerate(order) if cap[s] > take[s]]
        if not room:
            break
        s = max(room)[2]
        take[s] += 1
        need -= 1
    return take


def v1_first(line_id: str, seed: int) -> bool:
    """The candidates' order for one line: drawn under the seed, independent
    of the other lines (adding a line changes no other row's order)."""
    return random.Random(f"{seed}:order:{line_id}").random() < 0.5


def _digest(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def cand_id(line_id: str, source: str, text: str) -> str:
    """A candidate's id: opaque, stable for the same line, source and text."""
    return "c-" + _digest(line_id, source, text)[:12]


def fragment_id(line_id: str, v1: str, alt: str) -> str:
    """A fragment's id: the line and its two readings (new readings, a new fragment)."""
    return "llf-" + _digest(line_id, v1, alt)[:16]


def attribution_lines() -> list[str]:
    """Credits every row carries: the images (the registry's ``gwlb-images``),
    the transcriptions' attribution line, the second reader (the registry's
    ``trocr-kurrent-xvi-xvii``) and the project's own line."""
    images = legal.artifact("gwlb-images")
    bern = legal.artifact("trocr-kurrent-xvi-xvii")
    pack = legal.output("transcriptions").licence
    return [
        f"Images: {images.name}, {attr.GWLB_NAME} — {images.source} — "
        f"{images.licence_now.licence}.",
        attr.TRANSCRIPTIONS,
        f"Second reading: {bern.name} — {bern.source}, {bern.version} — "
        f"{bern.licence_now.licence}.",
        f"Fragment pack: {attr.PROJECT_NAME} ({attr.PROJECT_URL}), {pack}. Two machine "
        "readings of a line; a judgment says which one the image bears out.",
    ]


# --------------------------------------------------------------------------- #
# The eligible lines
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Eligible:
    """A line that may become a row: both readings, the box, the provenance."""

    line_id: str
    page: db.Page
    line_seq: int
    v1_text: str
    v1_conf: float
    v1_model: str
    v1_run_id: int
    run_at: str
    alt_text: str
    alt_conf: float | None
    alt_model: str
    piece: Piece
    bbox: dict[str, int]
    shelfmark: str
    gt: GtRow | None = None  # the reader-minted row, open deposit only
    gt_withheld: bool = False  # a reader-minted row outside the open deposit

    @property
    def stratum(self) -> str:
        return self.piece.stratum

    @property
    def leibniz_hand(self) -> bool:
        return self.piece.leibniz_hand

    @property
    def n_chars(self) -> int:
        return max(len(self.v1_text), len(self.alt_text))


@dataclass(slots=True)
class Pool:
    """What :func:`gather` found on the German pieces' pages."""

    eligible: list[Eligible] = field(default_factory=list)
    skipped: Counter = field(default_factory=Counter)
    pieces: int = 0
    pages: int = 0  # the pieces' pages
    pages_found: int = 0  # … in the store
    pages_no_image: int = 0  # … without a cached image
    lines: int = 0  # lines on the pages found (one per line_seq, latest run)
    readings: int = 0  # rows in the readings file
    listed: int | None = None  # only_records: the records listed …
    listed_unknown: int = 0  # … and those of them that are no piece of the census


def owner_piece(on_page: Sequence[Piece], gt: GtRow | None) -> Piece:
    """The piece a line belongs to: the one its reader-minted row names, else
    the lowest record id among the pieces on the page."""
    if gt is not None and gt.record_id:
        for p in on_page:
            if p.record_id == gt.record_id:
                return p
    return min(on_page, key=lambda p: record_key(p.record_id))


def gather(
    conn: sqlite3.Connection,
    pieces: Sequence[Piece],
    readings: Mapping[str, Reading],
    reader_rows: Mapping[str, GtRow],
    *,
    today: date,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_ratio: float = DEFAULT_MIN_RATIO,
    as_of_run: int | None = None,
    only_records: Collection[str] | None = None,
) -> Pool:
    """Every line on the pieces' pages through the rules (:data:`SKIP_REASONS`);
    with ``as_of_run``, the store as that run left it; with ``only_records``,
    the pages of the records listed and, on them, those records' lines."""
    expired = expired_volume_index(today)
    ranks = db.run_precedences(conn)

    def shown(page_id: str) -> list[db.Line]:
        return latest_lines(conn, page_id, as_of_run=as_of_run, precedences=ranks)

    by_page: dict[str, list[Piece]] = defaultdict(list)
    for p in pieces:
        for pid in p.page_ids:
            by_page[pid].append(p)
    pool = Pool(pieces=len(pieces), pages=len(by_page), readings=len(readings))
    wanted = None if only_records is None else set(only_records)
    if wanted is not None:
        known = {p.record_id for p in pieces}
        pool.listed, pool.listed_unknown = len(wanted), len(wanted - known)
        pool.pieces = len(wanted & known)
        # every piece on a page still decides whose a line is; the pages are the listed ones'
        visit = {pid for pid, ps in by_page.items() if any(p.record_id in wanted for p in ps)}
        by_page = defaultdict(list, {pid: by_page[pid] for pid in visit})
        pool.pages = len(by_page)
    works: dict[str, db.Work | None] = {}
    twins: dict[str, TwinGroup] = {}  # page id → its group, the work's resolved once
    run_at: dict[int, str | None] = {}
    for page_id in sorted(by_page):
        page = db.get_page(conn, page_id)
        if page is None:
            continue
        pool.pages_found += 1
        lines = shown(page_id)
        pool.lines += len(lines)
        if not page.local_path or ImageSource.source_url(page) is None:
            pool.pages_no_image += 1
            pool.skipped["no_image"] += len(lines)
            continue
        if not page.width or not page.height:
            pool.skipped["no_page_size"] += len(lines)
            continue
        if page.work_id not in works:
            works[page.work_id] = db.get_work(conn, page.work_id)
            groups, _ = resolve_work(db.get_pages(conn, page.work_id), shown)
            twins.update({pid: g for g in groups for pid in g.pages})
        work = works[page.work_id]
        lines = _carried(twins.get(page_id), page_id, lines, pool)
        for ln in lines:
            if wanted is not None:
                owner = owner_piece(by_page[page_id], reader_rows.get(ln.id))
                if owner.record_id not in wanted:
                    pool.skipped["other_record"] += 1
                    continue
            reason, item = _examine(
                conn,
                ln,
                page,
                work,
                by_page[page_id],
                readings,
                reader_rows,
                expired,
                run_at,
                min_chars=min_chars,
                max_chars=max_chars,
                min_ratio=min_ratio,
            )
            if item is None:
                pool.skipped[reason] += 1
            else:
                pool.eligible.append(item)
    return pool


def _carried(
    twin: TwinGroup | None, page_id: str, lines: list[db.Line], pool: Pool
) -> list[db.Line]:
    """The lines this registration carries once, as the index and the exports
    count them (W5): a scan registered twice gives each line one row — a
    spread's half on its own page, a fold's text on its primary."""
    if twin is None:
        return lines
    if not twin.carries_text(page_id):
        pool.skipped["twin_elsewhere"] += len(lines)
        return []
    keep = {ln.line_seq for ln, _ in twin.own_lines(page_id, lines, for_index=True)}
    pool.skipped["twin_elsewhere"] += len(lines) - len(keep)
    return [ln for ln in lines if ln.line_seq in keep]


def _examine(
    conn: sqlite3.Connection,
    ln: db.Line,
    page: db.Page,
    work: db.Work | None,
    on_page: Sequence[Piece],
    readings: Mapping[str, Reading],
    reader_rows: Mapping[str, GtRow],
    expired: Mapping[tuple[int, str], legal.Volume],
    run_at: dict[int, str | None],
    *,
    min_chars: int,
    max_chars: int,
    min_ratio: float,
) -> tuple[str, Eligible | None]:
    """One line through the rules: ``(reason, None)`` or ``("", Eligible)``."""
    if ln.status != "machine":
        return "already_corrected", None
    v1 = collapse_whitespace(ln.text or "")
    if not v1:
        return "no_v1_text", None
    reading = readings.get(ln.id)
    if reading is None:
        return "no_reading", None
    alt = collapse_whitespace(reading.text)
    if not alt:
        return "empty_reading", None
    if v1 == alt:
        return "same_text", None
    longer = max(len(v1), len(alt))
    if longer < min_chars:
        return "too_short", None
    if longer > max_chars:
        return "too_long", None
    if lopsided(v1, alt, min_ratio):
        return "lopsided", None
    gt = reader_rows.get(ln.id)
    piece = owner_piece(on_page, gt)
    if piece.language not in PACK_LANGS:
        return "not_german", None
    if ln.conf is None or ln.run_id is None:
        return "no_provenance", None
    if ln.run_id not in run_at:
        row = conn.execute(
            "SELECT started_at, finished_at FROM runs WHERE run_id = ?", (ln.run_id,)
        ).fetchone()
        run_at[ln.run_id] = (row["finished_at"] or row["started_at"]) if row else None
    when = run_at[ln.run_id]
    if not when or not ln.model:
        return "no_provenance", None
    # the geometry is the segmentation's, copied onto every later reading of the line
    polygon, baseline, _ = audit.line_geometry(conn, page.id, ln.line_seq)
    box = bbox_of(polygon, baseline, width=int(page.width or 0), height=int(page.height or 0))
    if box is None:
        return "no_geometry", None
    shelfmark = next((s for s in (work.shelfmarks if work else []) if s), None) or piece.signature
    if not shelfmark:
        return "no_shelfmark", None
    if not piece_expired(piece, expired):
        return "not_70_expired", None
    open_gt = gt if gt is not None and gt.deposit == "open" else None
    return "", Eligible(
        line_id=ln.id,
        page=page,
        line_seq=ln.line_seq,
        v1_text=v1,
        v1_conf=float(ln.conf),
        v1_model=ln.model,
        v1_run_id=int(ln.run_id),
        run_at=when,
        alt_text=alt,
        alt_conf=reading.conf,
        alt_model=reading.model,
        piece=piece,
        bbox=box,
        shelfmark=shelfmark,
        gt=open_gt,
        gt_withheld=gt is not None and open_gt is None,
    )


# --------------------------------------------------------------------------- #
# Selection and gold
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class GoldPlan:
    """The gold verdicts on the eligible lines and the lines chosen as gold."""

    # line_id → VERDICTS, for every eligible line of the drawn strata with a
    # reader-minted row in the open deposit: the supply the gold is drawn from
    verdicts: dict[str, str] = field(default_factory=dict)
    truth: set[str] = field(default_factory=set)  # chosen, with a truth candidate
    both_wrong: set[str] = field(default_factory=set)  # chosen, both candidates wrong
    withheld: int = 0  # eligible lines whose reader row is outside the open deposit
    cap: int = 0  # the most gold rows gold_rate allows

    def kind(self, line_id: str) -> str | None:
        """``v1`` | ``alt`` | ``both_wrong`` for a gold row, else ``None``."""
        if line_id in self.truth:
            return self.verdicts[line_id]
        if line_id in self.both_wrong:
            return "both_wrong"
        return None

    @property
    def lines(self) -> set[str]:
        return self.truth | self.both_wrong

    @property
    def n_gold(self) -> int:
        return len(self.truth) + len(self.both_wrong)


def choose_gold(
    items: Sequence[Eligible],
    *,
    limit: int,
    seed: int,
    gold_rate: float,
    bad_share: float,
    weights: Mapping[str, float] | None = None,
) -> GoldPlan:
    """The gold, drawn first and among all the eligible lines (module
    docstring): :func:`gold_counts` of the rows the pack will have, the truths
    and the both-wrong rows each spread over the strata by :func:`allocate`
    and drawn under the seed, apart from the fill."""
    strata = drawn_strata(weights)
    pool = [e for e in items if e.stratum in strata]
    plan = GoldPlan(withheld=sum(1 for e in pool if e.gt_withheld))
    truth: dict[str, list[str]] = defaultdict(list)
    bad: dict[str, list[str]] = defaultdict(list)
    for e in sorted(pool, key=lambda e: e.line_id):
        if e.gt is None:
            continue
        verdict = fold_verdict(e.v1_text, e.alt_text, e.gt.text)
        plan.verdicts[e.line_id] = verdict
        if verdict in ("v1", "alt"):
            truth[e.stratum].append(e.line_id)
        elif verdict == "both_wrong":
            bad[e.stratum].append(e.line_id)
    n_rows = min(limit, len(pool))
    plan.cap = math.floor(gold_rate * n_rows + 1e-9)
    n_truth = sum(len(v) for v in truth.values())
    n_bad = sum(len(v) for v in bad.values())
    t, b = gold_counts(n_rows, n_truth, n_bad, gold_rate, bad_share)
    rng = random.Random(f"{seed}:gold")
    for supply, n, chosen in ((truth, t, plan.truth), (bad, b, plan.both_wrong)):
        take = allocate({s: len(v) for s, v in supply.items()}, n, weights=weights)
        for s in strata:
            chosen.update(rng.sample(supply[s], take.get(s, 0)))
    return plan


def select_lines(
    items: Sequence[Eligible],
    *,
    limit: int,
    seed: int,
    weights: Mapping[str, float] | None = None,
    gold: Collection[str] = (),
) -> list[Eligible]:
    """Up to ``limit`` lines, the ``gold`` lines (ids, already drawn) among
    them: the strata filled around the gold by :func:`allocate` (equal numbers
    per stratum, or ``weights``; a short stratum's remainder going to the
    others), Leibniz's own hand at least at its share of the eligible lines;
    drawn under the seed, in line order."""
    rng = random.Random(seed)
    strata = drawn_strata(weights)
    by_stratum: dict[str, list[Eligible]] = defaultdict(list)
    for e in sorted(items, key=lambda e: e.line_id):
        if e.stratum in strata:
            by_stratum[e.stratum].append(e)
    chosen = {s: [e for e in v if e.line_id in gold] for s, v in by_stratum.items()}
    rest = {s: [e for e in v if e.line_id not in gold] for s, v in by_stratum.items()}
    quotas = allocate(
        {s: len(v) for s, v in by_stratum.items()},
        limit,
        weights=weights,
        floor={s: len(v) for s, v in chosen.items()},
    )
    fill = {s: quotas[s] - len(chosen[s]) for s in quotas}
    n_pool = sum(len(v) for v in by_stratum.values())
    n_own = sum(1 for v in by_stratum.values() for e in v if e.leibniz_hand)
    n_sel = sum(quotas.values())
    target = min(n_own, -(-n_own * n_sel // n_pool)) if n_pool else 0
    target -= sum(1 for s in quotas for e in chosen[s] if e.leibniz_hand)
    own = {s: sum(1 for e in rest[s] if e.leibniz_hand) for s in quotas}
    take_own = leibniz_quotas(fill, own, {s: len(rest[s]) for s in quotas}, target)
    picked: list[Eligible] = []
    for s in audit.STRATA:
        if s not in quotas:
            continue
        mine = [e for e in rest[s] if e.leibniz_hand]
        others = [e for e in rest[s] if not e.leibniz_hand]
        k_own = take_own[s]
        k_other = fill[s] - k_own
        if k_other > len(others):  # too few other hands: more of his
            k_own += k_other - len(others)
            k_other = len(others)
        picked += chosen[s] + rng.sample(mine, k_own) + rng.sample(others, k_other)
    return sorted(picked, key=lambda e: e.line_id)


def draw(
    items: Sequence[Eligible],
    *,
    limit: int,
    seed: int,
    gold_rate: float = DEFAULT_GOLD_RATE,
    bad_share: float = DEFAULT_BAD_GOLD_SHARE,
    weights: Mapping[str, float] | None = None,
) -> tuple[list[Eligible], GoldPlan]:
    """The pack's lines in the pack's order, and the gold among them: the gold
    first (:func:`choose_gold`), the strata filled around it
    (:func:`select_lines`), the whole shuffled under the seed."""
    gold = choose_gold(
        items, limit=limit, seed=seed, gold_rate=gold_rate, bad_share=bad_share, weights=weights
    )
    selected = select_lines(items, limit=limit, seed=seed, weights=weights, gold=gold.lines)
    random.Random(f"{seed}:rows").shuffle(selected)
    return selected, gold


# --------------------------------------------------------------------------- #
# Rows and the pack
# --------------------------------------------------------------------------- #


def build_row(
    e: Eligible,
    *,
    gold: str | None,
    seed: int,
    image_source: ImageSource,
    expired: Mapping[tuple[int, str], legal.Volume],
    attribution: Sequence[str],
) -> dict:
    """One fragment row in the contract's order of keys. Refuses (raises
    :class:`Refused`) a line whose piece's volume is not §70-free."""
    if not piece_expired(e.piece, expired):
        raise Refused(f"{e.line_id}: the volume of record {e.piece.record_id} is not §70-free")
    v1 = {
        "cand_id": cand_id(e.line_id, V1_SOURCE, e.v1_text),
        "text": e.v1_text,
        "source": V1_SOURCE,
        "prior_conf": round(e.v1_conf, 4),
    }
    alt = {
        "cand_id": cand_id(e.line_id, ALT_SOURCE, e.alt_text),
        "text": e.alt_text,
        "source": ALT_SOURCE,
    }
    if e.alt_conf is not None:
        alt["prior_conf"] = round(e.alt_conf, 4)
    page = e.page
    image = {
        "delivery": "static",
        "page_image_url": image_source.image_url(page),
        "bbox": dict(e.bbox),
        "canvas_id": page.canvas_id or site_canvas_id(SITE_URL, page),
        "folio_label": page.label or str(page.seq),
    }
    gold_obj: dict = {"is_gold": False}
    if gold is not None:
        if e.gt is None:
            raise ValueError(f"{e.line_id}: gold needs a reader-minted row")
        gold_obj = {"is_gold": True}
        if gold == "both_wrong":
            gold_obj["both_wrong"] = True
        else:
            gold_obj["truth_cand_id"] = (v1 if gold == "v1" else alt)["cand_id"]
        gold_obj["source"] = GOLD_SOURCE
        if e.gt.align_conf is not None:
            gold_obj["align_conf"] = round(float(e.gt.align_conf), 4)
    provenance = {
        "image_uri": ImageSource.source_url(page),
        "model": e.v1_model,
        "model_alt": e.alt_model,
        "run_at": e.run_at,
        "status": "aligned" if gold is not None else "machine",
        "shelfmark": e.shelfmark,
        "katalog_record_id": (e.gt.record_id if e.gt and e.gt.record_id else e.piece.record_id),
    }
    if e.gt is not None and e.gt.aa_ref:
        provenance["aa_ref"] = e.gt.aa_ref
    if not e.alt_model:
        del provenance["model_alt"]
    return {
        "fragment_id": fragment_id(e.line_id, e.v1_text, e.alt_text),
        "line_id": e.line_id,
        "page_id": page.id,
        "work_id": page.work_id,
        "image": image,
        "candidates": [v1, alt] if v1_first(e.line_id, seed) else [alt, v1],
        "stratum": e.stratum,
        "lang": e.piece.language,
        "machine_conf": round(e.v1_conf, 4),
        "n_chars": e.n_chars,
        "demand_weight": 1.0,
        "license_bucket": "open",
        "gold": gold_obj,
        "provenance": provenance,
        "attribution": list(attribution),
    }


def build_rows(
    selected: Sequence[Eligible],
    gold: GoldPlan,
    *,
    seed: int,
    today: date,
    image_source: ImageSource,
) -> list[dict]:
    """The rows of the lines as drawn, in their order (:func:`build_row`)."""
    expired = expired_volume_index(today)
    credits = attribution_lines()
    return [
        build_row(
            e,
            gold=gold.kind(e.line_id),
            seed=seed,
            image_source=image_source,
            expired=expired,
            attribution=credits,
        )
        for e in selected
    ]


def pack_header(
    rows: Sequence[Mapping],
    *,
    today: date,
    seed: int,
    run_ids: Iterable[int],
    built_at: str | None = None,
    git_sha: str | None = None,
) -> dict:
    """The header line; the pack id names the day, the seed and the rows' digest."""
    digest = hashlib.sha256(
        "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows).encode("utf-8")
    ).hexdigest()
    return {
        "kind": FRAGMENT_HEADER,
        "schema_version": SCHEMA_VERSION,
        "pack_id": f"ll-fragments-{today.isoformat()}-s{seed}-{digest[:10]}",
        "built_at": built_at or db.utcnow_iso(),
        "source": {
            "repo": attr.PROJECT_URL,
            "git_sha": git_sha if git_sha is not None else db.git_sha(),
            "run_ids": sorted(set(run_ids)),
        },
    }


@dataclass(slots=True)
class Pack:
    """A built pack: the header and rows, and what went into them."""

    header: dict
    rows: list[dict]
    pool: Pool
    selected: list[Eligible]
    gold: GoldPlan
    params: dict


def build_pack(
    conn: sqlite3.Connection,
    pieces: Sequence[Piece],
    readings: Mapping[str, Reading],
    *,
    today: date,
    limit: int = DEFAULT_LIMIT,
    seed: int = 0,
    gold_rate: float = DEFAULT_GOLD_RATE,
    bad_gold_share: float = DEFAULT_BAD_GOLD_SHARE,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_ratio: float = DEFAULT_MIN_RATIO,
    strata: Mapping[str, float] | None = None,
    as_of_run: int | None = None,
    only_records: Collection[str] | None = None,
    image_base_url: str = DEFAULT_IMAGE_BASE_URL,
    reader: str = DEFAULT_READER,
    built_at: str | None = None,
    git_sha: str | None = None,
) -> Pack:
    """The whole pack from the store (read only), the pieces and the readings."""
    reader_rows = load_reader_rows(conn, reader)
    pool = gather(
        conn,
        pieces,
        readings,
        reader_rows,
        today=today,
        min_chars=min_chars,
        max_chars=max_chars,
        min_ratio=min_ratio,
        as_of_run=as_of_run,
        only_records=only_records,
    )
    selected, gold = draw(
        pool.eligible,
        limit=limit,
        seed=seed,
        gold_rate=gold_rate,
        bad_share=bad_gold_share,
        weights=strata,
    )
    image_source = ImageSource(image_base_url)
    rows = build_rows(selected, gold, seed=seed, today=today, image_source=image_source)
    run_ids = {e.v1_run_id for e in selected}
    if any(e.gt is not None for e in selected):
        run_ids |= set(reader_mint_runs(conn, reader))
    header = pack_header(
        rows, today=today, seed=seed, run_ids=run_ids, built_at=built_at, git_sha=git_sha
    )
    params = {
        "today": today.isoformat(),
        "limit": limit,
        "seed": seed,
        "gold_rate": gold_rate,
        "bad_gold_share": bad_gold_share,
        "min_chars": min_chars,
        "max_chars": max_chars,
        "min_ratio": min_ratio,
        "strata": dict(strata) if strata is not None else None,
        "as_of_run": as_of_run,
        "only_records": len(set(only_records)) if only_records is not None else None,
        "image_base_url": image_source.base_url,
        "reader": reader,
    }
    return Pack(header=header, rows=rows, pool=pool, selected=selected, gold=gold, params=params)


def write_pack(path: Path | str, pack: Pack) -> Path:
    """The pack as JSONL — the header, then the rows — written whole or not at all."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".part")
    with tmp.open("w", encoding="utf-8") as fh:
        for obj in (pack.header, *pack.rows):
            fh.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + "\n")
    os.replace(tmp, out)
    return out


# --------------------------------------------------------------------------- #
# What the command prints
# --------------------------------------------------------------------------- #


def _pct(k: int, n: int) -> str:
    return f"{100 * k / n:.1f} %" if n else "—"


def _lengths(texts: Sequence[str]) -> str:
    if not texts:
        return "none"
    ns = [len(t) for t in texts]
    return (
        f"min {min(ns)} · median {statistics.median(ns):g} · mean {statistics.fmean(ns):.1f} · "
        f"max {max(ns)}"
    )


def length_bins(values: Iterable[int], lo: int, hi: int, width: int = 10) -> list[tuple[str, int]]:
    """``(label, count)`` per ``width``-character bin from ``lo`` to ``hi``; the
    last bin closes at ``hi`` (``40–50`` for the defaults)."""
    starts = list(range(lo - lo % width, hi + 1, width))
    if len(starts) > 1 and starts[-1] == hi:
        starts.pop()  # the top value joins the bin below it
    counts = Counter()
    for v in values:
        i = max(0, min(len(starts) - 1, (v - starts[0]) // width))
        counts[i] += 1
    out = []
    for i, s in enumerate(starts):
        first = max(s, lo)
        last = hi if i == len(starts) - 1 else s + width - 1
        out.append((f"{first}–{last}", counts[i]))
    return out


def summary_lines(pack: Pack) -> list[str]:
    """What was selected and skipped and why, the lengths, the gold, the shares."""
    pool, sel, gold, p = pack.pool, pack.selected, pack.gold, pack.params
    only = (
        ""
        if pool.listed is None
        else f" — only the {pool.listed:,} records listed ({pool.listed_unknown:,} of them not "
        "among the German pieces)"
    )
    out = [
        f"Pieces: {pool.pieces:,} records on {pool.pages:,} pages ({pool.pages_found:,} in the "
        f"store; {pool.pages_no_image:,} without a cached image, their lines skipped){only}",
        f"Lines on those pages: {pool.lines:,} ("
        + (
            f"the store as run {p['as_of_run']} left it"
            if p.get("as_of_run") is not None
            else "the reading the site shows of each"
        )
        + f"); readings in the file: {pool.readings:,}",
        "Skipped, under the first rule each line failed:",
    ]
    for reason in SKIP_REASONS:
        n = pool.skipped.get(reason, 0)
        if n or reason in ("lopsided", "not_70_expired"):
            note = {
                "other_record": " (on a listed record's page, another piece's line)",
                "lopsided": f" (the shorter reading under {p['min_ratio']:g} of the longer)",
                "not_70_expired": f" (refused: not §70-free on {p['today']})",
            }.get(reason, "")
            out.append(f"  {reason:<18} {n:>9,}{note}")
    out.append(f"Eligible: {len(pool.eligible):,} lines")
    weights = p.get("strata")
    if weights:
        total = sum(weights.values())
        named = " · ".join(
            f"{s} {weights[s] / total:.3g}" for s in audit.STRATA if weights.get(s, 0) > 0
        )
        how = f"strata by weight: {named}; a stratum not named gives no row"
    else:
        how = "equal per stratum"
    out.append(
        f"Selected: {len(sel):,} (limit {p['limit']:,}, seed {p['seed']}; {how}; the gold drawn "
        "first, the strata filled around it; the rows shuffled under the seed)"
    )
    pool_strata = Counter(e.stratum for e in pool.eligible)
    sel_strata = Counter(e.stratum for e in sel)
    gold_strata = Counter(e.stratum for e in sel if gold.kind(e.line_id))
    for s in audit.STRATA:
        if pool_strata.get(s) or sel_strata.get(s):
            out.append(
                f"  {s:<15} pool {pool_strata[s]:>8,} ({_pct(pool_strata[s], len(pool.eligible))})"
                f" → pack {sel_strata[s]:>6,} ({_pct(sel_strata[s], len(sel))}), gold "
                f"{gold_strata[s]:,}"
            )
    n_pool = len(pool.eligible)
    own_pool = sum(1 for e in pool.eligible if e.leibniz_hand)
    own_sel = sum(1 for e in sel if e.leibniz_hand)
    out.append(
        f"  Leibniz's own hand (strict rule): pool {own_pool:,} ({_pct(own_pool, n_pool)})"
        f" → pack {own_sel:,} ({_pct(own_sel, len(sel))}); other hands pool "
        f"{n_pool - own_pool:,} → pack {len(sel) - own_sel:,}"
    )
    langs = Counter(e.piece.language for e in sel)
    out.append("  lang: " + " · ".join(f"{k} {v:,}" for k, v in sorted(langs.items())))
    models = Counter(e.v1_model for e in sel)
    out.append(
        "  the stored reading (htr_best), by model: "
        + (" · ".join(f"{m} {n:,}" for m, n in models.most_common()) or "—")
    )
    out.append("Candidate lengths (characters, whitespace normalised):")
    out.append(f"  htr_best (stored)   {_lengths([e.v1_text for e in sel])}")
    out.append(f"  model_alt (Bern)    {_lengths([e.alt_text for e in sel])}")
    bins = length_bins((e.n_chars for e in sel), p["min_chars"], p["max_chars"])
    out.append("  the longer of the two: " + " · ".join(f"{lab} {n:,}" for lab, n in bins))
    first_v1 = sum(1 for r in pack.rows if r["candidates"][0]["source"] == V1_SOURCE)
    out.append(
        f"  order: the stored reading first in {first_v1:,} rows, the Bern reading first in "
        f"{len(sel) - first_v1:,}"
    )
    v = Counter(gold.verdicts.values())
    out.append(
        f"Gold supply, among the eligible lines of the strata drawn: {len(gold.verdicts):,} with "
        f"a reader-minted row in the open deposit — one candidate equal under the fold "
        f"{v['v1'] + v['alt']:,} (stored {v['v1']:,}, Bern {v['alt']:,}), neither "
        f"{v['both_wrong']:,}, both {v['ambiguous']:,} (no gold), unfoldable {v['unfoldable']:,}"
    )
    by_line = {e.line_id: e.stratum for e in pool.eligible}
    supply = Counter((by_line[k], x) for k, x in gold.verdicts.items())
    out.append(
        "  by stratum, truth / both wrong: "
        + " · ".join(
            f"{s} {supply[s, 'v1'] + supply[s, 'alt']:,} / {supply[s, 'both_wrong']:,}"
            for s in audit.STRATA
            if pool_strata.get(s)
        )
    )
    out.append(
        f"Gold: {gold.n_gold:,} of {len(sel):,} rows ({_pct(gold.n_gold, len(sel))}; cap "
        f"{p['gold_rate']:g} × {len(sel):,} rows = {gold.cap:,}): truth {len(gold.truth):,}, "
        f"both wrong {len(gold.both_wrong):,} (cap {p['bad_gold_share']:g} of the gold)"
    )
    chosen = Counter(gold.verdicts[k] for k in gold.truth)
    out.append(
        f"  the truth is the stored reading in {chosen['v1']:,} rows, the Bern reading in "
        f"{chosen['alt']:,}"
    )
    kinds = Counter(
        (e.stratum, "bad" if e.line_id in gold.both_wrong else "truth")
        for e in sel
        if gold.kind(e.line_id)
    )
    out.append(
        "  by stratum, truth / both wrong: "
        + " · ".join(
            f"{s} {kinds[s, 'truth']:,} / {kinds[s, 'bad']:,}"
            for s in audit.STRATA
            if sel_strata.get(s)
        )
    )
    own_gold = sum(1 for e in sel if e.leibniz_hand and gold.kind(e.line_id))
    out.append(f"  in Leibniz's own hand: {own_gold:,} of the gold rows")
    spare = sum(1 for e in sel if e.gt is not None and not gold.kind(e.line_id))
    out.append(
        f"  rows with a reader-minted row in the open deposit that are not gold: {spare:,} "
        "(over the caps, both readings equal, or unfoldable)"
    )
    out.append(
        f"  withheld: {sum(1 for e in sel if e.gt_withheld):,} selected lines whose reader-minted "
        f"row is in the NC deposit (never gold); {gold.withheld:,} among the eligible"
    )
    out.append(f"Runs: {', '.join(str(r) for r in pack.header['source']['run_ids']) or '—'}")
    out.append(f"Pack: {pack.header['pack_id']} (schema_version {SCHEMA_VERSION})")
    return out


__all__ = [
    "ALT_SOURCE",
    "DEFAULT_BAD_GOLD_SHARE",
    "DEFAULT_GOLD_RATE",
    "DEFAULT_IMAGE_BASE_URL",
    "DEFAULT_LIMIT",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MIN_CHARS",
    "DEFAULT_MIN_RATIO",
    "DEFAULT_PIECES",
    "DEFAULT_READINGS",
    "GOLD_SOURCE",
    "PACK_LANGS",
    "SITE_URL",
    "SKIP_REASONS",
    "V1_SOURCE",
    "VERDICTS",
    "Eligible",
    "GoldPlan",
    "GtRow",
    "Pack",
    "Piece",
    "Pool",
    "Reading",
    "Refused",
    "aa_label_from_source",
    "allocate",
    "attribution_lines",
    "bbox_of",
    "build_pack",
    "build_row",
    "build_rows",
    "cand_id",
    "choose_gold",
    "draw",
    "drawn_strata",
    "fold_verdict",
    "fragment_id",
    "gather",
    "gold_counts",
    "leibniz_quotas",
    "length_bins",
    "load_pieces",
    "load_reader_rows",
    "load_readings",
    "lopsided",
    "owner_piece",
    "pack_header",
    "parse_strata",
    "piece_expired",
    "piece_from_row",
    "reader_mint_runs",
    "record_key",
    "select_lines",
    "summary_lines",
    "v1_first",
    "write_pack",
]
