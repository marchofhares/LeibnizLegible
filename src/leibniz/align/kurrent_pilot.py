"""The Kurrent pilot: candidate readers on Leibniz's own German, without ground truth (K1 Task 4).

No German ground truth exists for the Nachlass, so no reader can be scored on
it. What *can* be measured is what the factory would do with each reader: the
aligner's confidence is a similarity between a line's machine text and the
edition's reading text, and a line is minted when it clears the stratum's
threshold. Read the same German pieces with every candidate, align each
reader's text to the piece's edition text as a **dry run** (nothing written
to ``gt_lines``, nothing to the store), and the yield at the factory's own
gate is a ground-truth-free measure of how well the reader reads Leibniz's
German. Five Latin or French control pieces must show the opposite ordering,
the Latin-trained baseline winning; if they do not, the method is broken and
the report says so.

The pieces come from the census (``data/kurrent/german_pieces.jsonl``), spread
over volumes, strata and hands, with resolved canvases; the lines are the
stored v1 geometry; the crops come from the page-image cache through the audit
module's crop machinery (the polygon masked, no downscaling). Every reading a
reader produces lives in ``data/kurrent/pilot-readings/<reader>.jsonl`` — one
row per line, resumable — never in the store: the recognise stage would
overwrite the v1 row in place. The stored v1 text itself is read as the reader
``v1``: the factory's own result on these pieces, for free.

The side-by-side page (``data/kurrent/pilot-side-by-side.html``) shows thirty
German line crops with every reader's text, for the operator's eye: does any
reader produce German words? The answer is recorded verbatim in the report.
"""

from __future__ import annotations

import base64
import csv
import gc
import html
import json
import random
import sqlite3
import statistics
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz import db
from leibniz.align.align import HtrLine, align_piece
from leibniz.align.audit import CROP_PAD, crop_from_image, crop_line
from leibniz.align.audit_reach import open_readonly
from leibniz.align.factory import STRATUM_THRESHOLDS, page_stats_for_pages
from leibniz.align.resolve import index_pages, select_folios
from leibniz.align.stratum import classify_piece
from leibniz.align.volumes import enumerate_pieces
from leibniz.enrich.langid import classify
from leibniz.images.fetch import local_relpath

DEFAULT_GERMAN = Path("data/kurrent/german_pieces.jsonl")
DEFAULT_READINGS_DIR = Path("data/kurrent/pilot-readings")
DEFAULT_SIDE_BY_SIDE = Path("data/kurrent/pilot-side-by-side.html")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
DEFAULT_BOOTSTRAP = Path("reports/kurrent/bootstrap-candidates.json")
DEFAULT_IMAGES_ROOT = Path("/mnt/d/leibniz-images")
N_GERMAN = 20
N_CONTROL = 5
MAX_PAGES = 3
SIDE_BY_SIDE_LINES = 30
SEED = 20261009
V1 = "v1"  # the stored machine text, the factory's own reader
BASELINE = "philiumm"
# A Task 3 candidate joins the pilot when its Dresden CER is at most this share
# of the PHILIUMM baseline's — "well below", said in advance.
QUALIFY_RATIO = 2 / 3


# --------------------------------------------------------------------------- #
# Pieces
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PilotPiece:
    """One piece in the pilot: where it is and what the census said about it."""

    record_id: str
    work_id: str
    aa_label: str
    volume_label: str
    stratum: str
    hand: str
    leibniz_hand: bool
    language: str
    score: float
    page_ids: list[str]  # the pages read (capped)
    n_pages_total: int
    role: str  # german | control
    textart: str | None = None
    datum: str | None = None
    titel: str | None = None

    @property
    def threshold(self) -> float:
        return STRATUM_THRESHOLDS.get(self.stratum, STRATUM_THRESHOLDS["unknown"])


def load_german_pieces(path: Path | str = DEFAULT_GERMAN) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                rows.append(json.loads(raw))
    return rows


def _piece_from_row(row: Mapping, *, role: str, max_pages: int) -> PilotPiece:
    pages = list(row["page_ids"])
    return PilotPiece(
        record_id=str(row["record_id"]),
        work_id=str(row["work_id"]),
        aa_label=str(row.get("aa_label", "")),
        volume_label=str(row.get("volume_label", "")),
        stratum=str(row.get("stratum", "unknown")),
        hand=str(row.get("hand", "none")),
        leibniz_hand=bool(row.get("leibniz_hand", False)),
        language=str(row.get("language", "")),
        score=float(row.get("score", 0.0)),
        page_ids=pages[:max_pages],
        n_pages_total=len(pages),
        role=role,
        textart=row.get("textart"),
        datum=row.get("datum"),
        titel=row.get("titel"),
    )


def select_german(
    rows: Sequence[Mapping],
    *,
    n: int = N_GERMAN,
    seed: int = SEED,
    max_pages: int = MAX_PAGES,
    min_lines: int = 20,
) -> list[PilotPiece]:
    """Twenty German pieces spread over strata, hands and volumes, reproducibly.

    Eligible: a work, pages and at least ``min_lines`` recognised lines. The
    pieces are dealt round-robin over the (stratum, hand) cells that exist,
    preferring a volume not yet drawn inside each cell, so a reader is judged on
    drafts and fair copies, on Leibniz's hand and on secretaries', on several
    volumes — not on one convolute.
    """
    rng = random.Random(seed)
    eligible = [
        r
        for r in rows
        if r.get("work_id") and r.get("page_ids") and r.get("n_lines", 0) >= min_lines
    ]
    cells: dict[tuple[str, str], list[Mapping]] = defaultdict(list)
    for r in eligible:
        cells[(str(r.get("stratum")), str(r.get("hand")))].append(r)
    for members in cells.values():
        rng.shuffle(members)
    # Leibniz's own hand first among the cells, then the larger cells
    order = sorted(
        cells,
        key=lambda c: (-sum(1 for r in cells[c] if r.get("leibniz_hand")), -len(cells[c]), c),
    )
    chosen: list[Mapping] = []
    seen_volumes: dict[tuple[str, str], set[str]] = defaultdict(set)
    while len(chosen) < n and any(cells.values()):
        for cell in order:
            members = cells[cell]
            if not members:
                continue
            pick = next(
                (m for m in members if m.get("volume_label") not in seen_volumes[cell]), members[0]
            )
            members.remove(pick)
            seen_volumes[cell].add(str(pick.get("volume_label")))
            chosen.append(pick)
            if len(chosen) >= n:
                break
    return [_piece_from_row(r, role="german", max_pages=max_pages) for r in chosen]


def select_controls(
    conn: sqlite3.Connection,
    cache: Mapping[str, str],
    *,
    n: int = N_CONTROL,
    seed: int = SEED,
    max_pages: int = MAX_PAGES,
    min_lines: int = 20,
    min_score: float = 0.9,
    today: date | None = None,
) -> list[PilotPiece]:
    """Latin or French pieces with lines, drawn reproducibly from the factory's pieces.

    The two languages alternate as far as the draw allows, so the control is
    not one language's.
    """
    pieces, _ = enumerate_pieces(conn, today=today or date.today())
    rng = random.Random(seed + 1)
    candidates = [p for p in pieces if p.localizable and p.record_id in cache]
    rng.shuffle(candidates)
    indexes: dict[str, dict[int, list[db.Page]]] = {}
    found: dict[str, list[PilotPiece]] = {"la": [], "fr": []}
    want = {"la": (n + 1) // 2, "fr": n // 2}
    for piece in candidates:
        if all(len(found[lg]) >= want[lg] for lg in found):
            break
        lang = classify(cache[piece.record_id])
        if (
            lang.lang not in found
            or lang.score < min_score
            or len(found[lang.lang]) >= want[lang.lang]
        ):
            continue
        assert piece.work_id is not None and piece.folio_range is not None
        index = indexes.get(piece.work_id)
        if index is None:
            index = index_pages(db.get_pages(conn, piece.work_id))
            indexes[piece.work_id] = index
        pages = select_folios(
            index,
            piece.work_id,
            *piece.folio_range,
            side_lo=piece.folio_sides[0],
            side_hi=piece.folio_sides[1],
        ).pages
        if not pages:
            continue
        page_ids = [pg.id for pg in pages]
        n_lines = sum(
            conn.execute(
                "SELECT COUNT(*) FROM lines WHERE page_id = ? AND text IS NOT NULL", (pid,)
            ).fetchone()[0]
            for pid in page_ids
        )
        if n_lines < min_lines:
            continue
        stratum = classify_piece(page_stats_for_pages(conn, pages), textart=piece.textart).stratum
        rec = db.get_katalog_record(conn, piece.record_id)
        meta = rec.metadata if rec is not None else {}
        found[lang.lang].append(
            PilotPiece(
                record_id=piece.record_id,
                work_id=piece.work_id,
                aa_label=piece.aa_label,
                volume_label=piece.volume_label,
                stratum=stratum,
                hand="",
                leibniz_hand=False,
                language=lang.lang,
                score=round(lang.score, 4),
                page_ids=page_ids[:max_pages],
                n_pages_total=len(page_ids),
                role="control",
                textart=piece.textart,
                datum=str(meta.get("datum") or "") or None,
                titel=str(meta.get("titel") or "") or None,
            )
        )
    out: list[PilotPiece] = []
    for la, fr in zip(found["la"], found["fr"], strict=False):
        out.extend((la, fr))
    longer = found["la"] if len(found["la"]) > len(found["fr"]) else found["fr"]
    out.extend(longer[min(len(found["la"]), len(found["fr"])) :])
    return out[:n]


# --------------------------------------------------------------------------- #
# Lines and crops
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PilotLine:
    """One stored line of a pilot page: id, geometry, the v1 reading."""

    line_id: str
    page_id: str
    line_seq: int
    polygon: list | None
    baseline: list | None
    v1_text: str | None
    v1_conf: float | None


def page_lines(
    conn: sqlite3.Connection, page_id: str, *, sample: int | None = None
) -> list[PilotLine]:
    """The page's recognised lines in reading order (the first ``sample`` with --sample)."""
    out: list[PilotLine] = []
    for ln in db.iter_lines_for_page(conn, page_id):
        if ln.text is None:
            continue
        out.append(
            PilotLine(
                line_id=ln.id,
                page_id=page_id,
                line_seq=ln.line_seq,
                polygon=ln.polygon,
                baseline=ln.baseline,
                v1_text=ln.text,
                v1_conf=ln.conf,
            )
        )
        if sample is not None and len(out) >= sample:
            break
    return out


def page_image_path(conn: sqlite3.Connection, page_id: str, images_root: Path) -> Path | None:
    page = db.get_page(conn, page_id)
    if page is None:
        return None
    path = Path(images_root) / (page.local_path or local_relpath(page))
    return path if path.exists() else None


def crop(image_path: Path, line: PilotLine) -> bytes | None:
    """The reader's crop: the polygon masked, full resolution, the audit's padding."""
    return crop_line(
        image_path, line.polygon, line.baseline, pad=CROP_PAD, max_width=None, mask_polygon=True
    )


def crop_all(image_path: Path, lines: Sequence[PilotLine]) -> list[tuple[PilotLine, bytes]]:
    """The reader's crops for one page, the page image decoded once."""
    from PIL import Image

    out: list[tuple[PilotLine, bytes]] = []
    with Image.open(image_path) as im:
        im.load()
        for ln in lines:
            try:
                png = crop_from_image(
                    im, ln.polygon, ln.baseline, pad=CROP_PAD, max_width=None, mask_polygon=True
                )
            except OSError:
                png = None
            if png is not None:
                out.append((ln, png))
    return out


# --------------------------------------------------------------------------- #
# Readings (resumable JSONL per reader)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Reading:
    line_id: str
    text: str
    conf: float | None
    model: str
    device: str
    ms: float


def readings_path(readings_dir: Path | str, reader: str) -> Path:
    return Path(readings_dir) / f"{reader}.jsonl"


def load_readings(readings_dir: Path | str, reader: str) -> dict[str, Reading]:
    path = readings_path(readings_dir, reader)
    out: dict[str, Reading] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            row = json.loads(raw)
            out[row["line_id"]] = Reading(
                row["line_id"],
                row["text"],
                row.get("conf"),
                row.get("model", ""),
                row.get("device", ""),
                float(row.get("ms", 0.0)),
            )
    return out


def append_readings(readings_dir: Path | str, reader: str, rows: Iterable[Reading]) -> None:
    path = readings_path(readings_dir, reader)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")


def read_pieces(
    conn: sqlite3.Connection,
    pieces: Sequence[PilotPiece],
    reader: str,
    engine_factory: Callable[[], object],
    *,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    readings_dir: Path | str = DEFAULT_READINGS_DIR,
    sample: int | None = None,
    batch_size: int = 8,
    log: Callable[[str], None] | None = None,
) -> dict[str, Reading]:
    """Read every line of the pieces' pages with one reader, resuming from its JSONL.

    The engine is built only when a line is still unread. Crops are cut page by
    page (one image open per page); a page whose image is not cached, or a line
    without geometry, is skipped and counted in the log.
    """
    have = load_readings(readings_dir, reader)
    engine = None
    model = device = ""
    n_new = n_skipped = 0
    for piece in pieces:
        for page_id in piece.page_ids:
            lines = [
                ln for ln in page_lines(conn, page_id, sample=sample) if ln.line_id not in have
            ]
            if not lines:
                continue
            path = page_image_path(conn, page_id, Path(images_root))
            if path is None:
                n_skipped += len(lines)
                if log:
                    log(
                        f"{reader}: page image not cached for {page_id}; {len(lines)} lines skipped"
                    )
                continue
            try:
                crops = crop_all(path, lines)
            except OSError as exc:  # an unreadable cache file
                n_skipped += len(lines)
                if log:
                    log(f"{reader}: {page_id} image unreadable ({exc}); {len(lines)} lines skipped")
                continue
            n_skipped += len(lines) - len(crops)
            if not crops:
                continue
            if engine is None:
                engine = engine_factory()
                model = str(getattr(engine, "version", getattr(engine, "name", reader)))
                device = str(getattr(engine, "device", ""))
            rows: list[Reading] = []
            for start in range(0, len(crops), batch_size):
                chunk = crops[start : start + batch_size]
                t0 = time.monotonic()
                if hasattr(engine, "transcribe_conf"):
                    out = engine.transcribe_conf([png for _, png in chunk])
                else:
                    out = [(t, None) for t in engine.transcribe([png for _, png in chunk])]
                ms = 1000.0 * (time.monotonic() - t0) / max(1, len(chunk))
                for (ln, _), (text, conf) in zip(chunk, out, strict=True):
                    rows.append(Reading(ln.line_id, text, conf, model, device, round(ms, 1)))
            append_readings(readings_dir, reader, rows)
            for r in rows:
                have[r.line_id] = r
            n_new += len(rows)
            if log:
                log(f"{reader}: {page_id} {len(rows)} lines ({len(have):,} so far)")
    if log:
        log(f"{reader}: {n_new:,} lines read now, {n_skipped:,} skipped, {len(have):,} in the file")
    release(engine)
    return have


def release(engine: object) -> None:
    """Drop a reader's model and give its GPU memory back before the next reader loads.

    Three TrOCR checkpoints held at once filled the 6 GB card on the first pilot
    run; the caching allocator keeps what a dead model used until told.
    """
    if engine is None:
        return
    for attr in ("_model", "_processor"):
        if hasattr(engine, attr):
            try:
                setattr(engine, attr, None)
            except AttributeError:
                pass
    del engine
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ModuleNotFoundError:
        pass


def v1_readings(
    conn: sqlite3.Connection, pieces: Sequence[PilotPiece], *, sample: int | None = None
) -> dict[str, Reading]:
    """The stored machine text as a reader (the factory's own)."""
    out: dict[str, Reading] = {}
    for piece in pieces:
        for page_id in piece.page_ids:
            for ln in page_lines(conn, page_id, sample=sample):
                out[ln.line_id] = Reading(
                    ln.line_id, ln.v1_text or "", ln.v1_conf, V1, "store", 0.0
                )
    return out


# --------------------------------------------------------------------------- #
# The dry-run alignment
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PieceYield:
    """One piece under one reader: the factory's gate, nothing written."""

    record_id: str
    role: str
    reader: str
    volume_label: str
    stratum: str
    hand: str
    leibniz_hand: bool
    threshold: float
    n_lines: int
    n_read: int  # lines the reader produced a non-empty text for
    n_aligned: int
    mean_conf: float
    mean_conf_aligned: float | None

    @property
    def yield_rate(self) -> float | None:
        return self.n_aligned / self.n_lines if self.n_lines else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d["yield"] = self.yield_rate
        return d


def dry_run_piece(
    piece: PilotPiece,
    lines: Sequence[PilotLine],
    reader: str,
    readings: Mapping[str, Reading],
    edition_text: str,
) -> PieceYield:
    """Align one reader's text for one piece to its edition text at the factory's threshold."""
    htr = [
        HtrLine(ref=ln.line_id, text=readings[ln.line_id].text if ln.line_id in readings else "")
        for ln in lines
    ]
    result = align_piece(htr, edition_text, threshold=piece.threshold)
    confs = [al.align_conf for al in result.lines]
    aligned = [al.align_conf for al in result.lines if al.aligned]
    return PieceYield(
        record_id=piece.record_id,
        role=piece.role,
        reader=reader,
        volume_label=piece.volume_label,
        stratum=piece.stratum,
        hand=piece.hand,
        leibniz_hand=piece.leibniz_hand,
        threshold=piece.threshold,
        n_lines=len(lines),
        n_read=sum(1 for h in htr if h.text.strip()),
        n_aligned=len(aligned),
        mean_conf=statistics.fmean(confs) if confs else 0.0,
        mean_conf_aligned=statistics.fmean(aligned) if aligned else None,
    )


def dry_run(
    conn: sqlite3.Connection,
    pieces: Sequence[PilotPiece],
    readers: Mapping[str, Mapping[str, Reading]],
    cache: Mapping[str, str],
    *,
    sample: int | None = None,
) -> list[PieceYield]:
    out: list[PieceYield] = []
    for piece in pieces:
        text = cache.get(piece.record_id, "")
        lines = [ln for pid in piece.page_ids for ln in page_lines(conn, pid, sample=sample)]
        for reader, readings in readers.items():
            out.append(dry_run_piece(piece, lines, reader, readings, text))
    return out


# --------------------------------------------------------------------------- #
# Aggregation and the verdict
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ReaderSummary:
    reader: str
    german_lines: int
    german_aligned: int
    german_yield: float | None
    german_mean_conf: float
    control_lines: int
    control_aligned: int
    control_yield: float | None
    control_mean_conf: float
    by_stratum: dict[str, dict] = field(default_factory=dict)
    by_hand: dict[str, dict] = field(default_factory=dict)
    read_lines: int = 0
    ms_per_line: float | None = None
    device: str = ""
    model: str = ""


def summarize_readers(
    yields: Sequence[PieceYield], readers: Mapping[str, Mapping[str, Reading]]
) -> list[ReaderSummary]:
    out: list[ReaderSummary] = []
    for reader in readers:
        rows = [y for y in yields if y.reader == reader]
        ger = [y for y in rows if y.role == "german"]
        ctl = [y for y in rows if y.role == "control"]

        def pool(group: Sequence[PieceYield]) -> tuple[int, int, float | None, float]:
            n = sum(y.n_lines for y in group)
            a = sum(y.n_aligned for y in group)
            conf = (sum(y.mean_conf * y.n_lines for y in group) / n) if n else 0.0
            return n, a, (a / n if n else None), conf

        gn, ga, gy, gc = pool(ger)
        cn, ca, cy, cc = pool(ctl)

        def by(
            key: Callable[[PieceYield], str], rows_: Sequence[PieceYield] = ger
        ) -> dict[str, dict]:
            groups: dict[str, list[PieceYield]] = defaultdict(list)
            for y in rows_:
                groups[key(y)].append(y)
            res = {}
            for k, g in sorted(groups.items()):
                n, a, yl, conf = pool(g)
                res[k] = {
                    "pieces": len(g),
                    "lines": n,
                    "aligned": a,
                    "yield": yl,
                    "mean_conf": conf,
                }
            return res

        reads = readers[reader]
        ms = [r.ms for r in reads.values() if r.ms > 0]
        dev = next((r.device for r in reads.values() if r.device), "")
        model = next((r.model for r in reads.values() if r.model), reader)
        out.append(
            ReaderSummary(
                reader=reader,
                german_lines=gn,
                german_aligned=ga,
                german_yield=gy,
                german_mean_conf=gc,
                control_lines=cn,
                control_aligned=ca,
                control_yield=cy,
                control_mean_conf=cc,
                by_stratum=by(lambda y: y.stratum),
                by_hand=by(lambda y: y.hand or "control"),
                read_lines=len(reads),
                ms_per_line=statistics.fmean(ms) if ms else None,
                device=dev,
                model=model,
            )
        )
    return out


# Licences under which a reader may be built on (K2 runs the factory with it).
# "none stated" is evaluate-only: its number is reported, it is never chosen.
BUILDABLE_LICENCES: frozenset[str] = frozenset({"MIT", "CC BY 4.0", "Apache-2.0", "CC0"})


@dataclass(slots=True)
class Verdict:
    best_reader: str | None  # the best among the readers K2 may build on
    best_german_yield: float | None
    baseline_german_yield: float | None
    controls_consistent: bool  # the baseline (or v1) wins the controls
    control_winner: str | None
    note: str
    best_any_reader: str | None = None  # the best by yield, licence aside
    best_any_yield: float | None = None
    licence_note: str = ""


def verdict(
    summaries: Sequence[ReaderSummary], licences: Mapping[str, str] | None = None
) -> Verdict:
    """The reader with the highest German yield K2 may build on, and whether the controls behave.

    ``licences`` maps a reader to its licence; a reader whose licence is not in
    :data:`BUILDABLE_LICENCES` (the two Hub models that state none) is ranked
    but never chosen. Without the map every reader may be chosen.
    """
    by = {s.reader: s for s in summaries}
    candidates = [s for s in summaries if s.reader != V1 and s.german_yield is not None]
    best_any = max(candidates, key=lambda s: s.german_yield or 0.0, default=None)
    buildable = [
        s
        for s in candidates
        if licences is None or licences.get(s.reader, "") in BUILDABLE_LICENCES
    ]
    best = max(buildable, key=lambda s: s.german_yield or 0.0, default=None)
    licence_note = ""
    if best_any is not None and best is not None and best_any.reader != best.reader:
        licence_note = (
            f"`{best_any.reader}` has the highest German yield ({best_any.german_yield:.1%}) but "
            f"states no licence ({licences.get(best_any.reader, '?') if licences else '?'}): "
            f"evaluated, not built on; `{best.reader}` "
            f"({licences.get(best.reader, '?') if licences else '?'}) is the reader K2 may use"
        )
    elif best_any is not None and best is None:
        licence_note = (
            f"`{best_any.reader}` has the highest German yield ({best_any.german_yield:.1%}) but "
            "no reader with a licence to build on took part"
        )
    with_controls = [s for s in summaries if s.control_yield is not None and s.control_lines]
    ctl_best = max(with_controls, key=lambda s: s.control_yield or 0.0, default=None)
    base = by.get(BASELINE) or by.get(V1)
    consistent = bool(ctl_best is not None and ctl_best.reader in (BASELINE, V1))
    if not with_controls:
        note = "no control pieces were read; the ordering check could not run"
        consistent = False
    elif consistent:
        note = f"the Latin-trained baseline ({ctl_best.reader}) wins the control pieces as it must"  # type: ignore[union-attr]
    else:
        note = (
            f"the controls are won by {ctl_best.reader}, not the baseline: the method is broken "  # type: ignore[union-attr]
            "or the controls are not Latin and French; the German ordering is not to be trusted"
        )
    return Verdict(
        best_reader=best.reader if best else None,
        best_german_yield=best.german_yield if best else None,
        baseline_german_yield=base.german_yield if base else None,
        controls_consistent=consistent,
        control_winner=ctl_best.reader if ctl_best else None,
        note=note,
        best_any_reader=best_any.reader if best_any else None,
        best_any_yield=best_any.german_yield if best_any else None,
        licence_note=licence_note,
    )


def qualifying_readers(
    bootstrap_json: Path | str = DEFAULT_BOOTSTRAP, *, ratio: float = QUALIFY_RATIO
) -> list[str]:
    """Task 3 candidates at or under ``ratio`` × the baseline's Dresden CER, plus the baseline."""
    path = Path(bootstrap_json)
    if not path.exists():
        return [BASELINE]
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = {r["key"]: r for r in data.get("results", []) if r.get("status") == "ok"}
    base = rows.get(BASELINE)
    if base is None:
        return [BASELINE]
    base_cer = base["scores"]["philiumm"]["cer"]
    out = [BASELINE]
    for key, r in rows.items():
        if key == BASELINE:
            continue
        if r["scores"]["philiumm"]["cer"] <= ratio * base_cer:
            out.append(key)
    return out


# --------------------------------------------------------------------------- #
# The side-by-side page
# --------------------------------------------------------------------------- #


def side_by_side(
    conn: sqlite3.Connection,
    pieces: Sequence[PilotPiece],
    readers: Mapping[str, Mapping[str, Reading]],
    *,
    images_root: Path | str = DEFAULT_IMAGES_ROOT,
    n: int = SIDE_BY_SIDE_LINES,
    seed: int = SEED,
    sample: int | None = None,
) -> str:
    """Thirty German line crops with every reader's text, as one HTML page."""
    rng = random.Random(seed)
    pool: list[tuple[PilotPiece, PilotLine]] = []
    for piece in pieces:
        if piece.role != "german":
            continue
        for pid in piece.page_ids:
            for ln in page_lines(conn, pid, sample=sample):
                if any(ln.line_id in r and r[ln.line_id].text.strip() for r in readers.values()):
                    pool.append((piece, ln))
    chosen = rng.sample(pool, min(n, len(pool))) if pool else []
    chosen.sort(key=lambda t: (t[0].record_id, t[1].line_id))
    order = list(readers)
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<title>Kurrent pilot — side by side</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:1.5rem;max-width:1400px}"
        "img{max-width:100%;display:block;border:1px solid #ccc;margin:.4rem 0}"
        "table{border-collapse:collapse;width:100%;margin-bottom:1.6rem}"
        "td,th{border:1px solid #ddd;padding:.25rem .5rem;text-align:left;vertical-align:top}"
        "th{width:14rem;background:#f5f5f5;font-weight:600}"
        ".meta{color:#555;font-size:.9rem}</style></head><body>",
        "<h1>Kurrent pilot — thirty German lines, every reader's text</h1>",
        f"<p class='meta'>{len(chosen)} lines drawn (seed {seed}) from the pilot's German pieces; "
        "the crop is the stored v1 geometry, the polygon masked. Readers: "
        + ", ".join(html.escape(r) for r in order)
        + ". <b>Question for the operator:</b> does any reader produce German words?</p>",
    ]
    for k, (piece, ln) in enumerate(chosen, start=1):
        path = page_image_path(conn, ln.page_id, Path(images_root))
        png = crop(path, ln) if path is not None else None
        img = (
            f"<img alt='line {html.escape(ln.line_id)}' "
            f"src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}'>"
            if png
            else "<p class='meta'>(no crop: page image not cached)</p>"
        )
        parts.append(
            f"<h2>{k}. {html.escape(ln.line_id)}</h2>"
            f"<p class='meta'>{html.escape(piece.aa_label)} · "
            f"katalog {html.escape(piece.record_id)} · {html.escape(piece.stratum)} · hand "
            f"{html.escape(piece.hand)}{' · Leibniz' if piece.leibniz_hand else ''} · "
            f"{html.escape(piece.textart or '')}</p>{img}<table>"
        )
        for reader in order:
            r = readers[reader].get(ln.line_id)
            text = html.escape(r.text) if r else "<i>(not read)</i>"
            conf = f" <span class='meta'>({r.conf:.2f})</span>" if r and r.conf is not None else ""
            parts.append(f"<tr><th>{html.escape(reader)}</th><td>{text}{conf}</td></tr>")
        parts.append("</table>")
    parts.append("</body></html>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PilotResult:
    pieces: list[PilotPiece]
    yields: list[PieceYield]
    summaries: list[ReaderSummary]
    verdict: Verdict
    readers: list[str]
    sample: int | None
    max_pages: int
    operator_verdict: str | None = None
    generated: str = field(default_factory=lambda: date.today().isoformat())

    def as_dict(self) -> dict:
        return {
            "generated": self.generated,
            "readers": self.readers,
            "sample": self.sample,
            "max_pages": self.max_pages,
            "pieces": [asdict(p) for p in self.pieces],
            "summaries": [asdict(s) for s in self.summaries],
            "verdict": asdict(self.verdict),
            "operator_verdict": self.operator_verdict,
        }


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{d}f} %"


def _n(x: int) -> str:
    return f"{x:,}"


def render_report(res: PilotResult) -> str:
    german = [p for p in res.pieces if p.role == "german"]
    controls = [p for p in res.pieces if p.role == "control"]
    out: list[str] = []
    out.append("# The Kurrent pilot: candidate readers on Leibniz's own German")
    out.append("")
    out.append(
        f"{len(german)} German pieces from the census (`data/kurrent/german_pieces.jsonl`), spread "
        f"over {len({p.volume_label for p in german})} volumes, the strata and the hands, "
        f"{sum(1 for p in german if p.leibniz_hand)} of them in Leibniz's own hand; "
        f"{len(controls)} Latin or French control pieces. Pages capped at {res.max_pages} per piece"
        + (f", the first {res.sample} lines of each page" if res.sample else "")
        + f". Readers: {', '.join(f'`{r}`' for r in res.readers)}; `{V1}` is the stored machine "
        "text of the corpus run (the factory's own reader), the others read the same lines afresh "
        "from the page images (the v1 geometry, the polygon masked). Each reader's text is aligned "
        "to the piece's edition text as a dry run at the factory's per-stratum threshold; "
        "**yield** is the share of lines that clear the factory's gate, **confidence** the "
        "aligner's matched fraction. Nothing was written to the store."
    )
    out.append("")
    out.append("## Yield at the factory's gate")
    out.append("")
    out.append(
        "| reader | German lines | aligned | **German yield** | mean conf | control lines | "
        "aligned | "
        "control yield | mean conf | ms/line | device |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for s in sorted(res.summaries, key=lambda s: -(s.german_yield or 0.0)):
        out.append(
            f"| {s.reader} | {_n(s.german_lines)} | {_n(s.german_aligned)} | "
            f"**{_pct(s.german_yield)}** | "
            f"{s.german_mean_conf:.3f} | {_n(s.control_lines)} | {_n(s.control_aligned)} | "
            f"{_pct(s.control_yield)} | {s.control_mean_conf:.3f} | "
            f"{'—' if s.ms_per_line is None else f'{s.ms_per_line:.0f}'} | {s.device or '—'} |"
        )
    out.append("")
    v = res.verdict
    out.append("## The control check")
    out.append("")
    out.append(
        f"The control pieces are won by `{v.control_winner}`: {v.note}."
        if v.control_winner
        else v.note
    )
    out.append("")
    out.append("## German yield by stratum and by hand")
    out.append("")
    strata = sorted({k for s in res.summaries for k in s.by_stratum})
    out.append("| reader | " + " | ".join(strata) + " |")
    out.append("|---|" + "---:|" * len(strata))
    for s in res.summaries:
        cells = []
        for st in strata:
            row = s.by_stratum.get(st)
            cells.append(f"{_pct(row['yield'])} ({_n(row['lines'])})" if row else "—")
        out.append(f"| {s.reader} | " + " | ".join(cells) + " |")
    out.append("")
    hands = sorted({k for s in res.summaries for k in s.by_hand})
    leibniz = [y for y in res.yields if y.role == "german" and y.leibniz_hand]
    with_l = bool(leibniz)
    out.append(
        "| reader | "
        + " | ".join(hands)
        + (" | of them in Leibniz's own hand |" if with_l else " |")
    )
    out.append("|---|" + "---:|" * (len(hands) + int(with_l)))
    for s in res.summaries:
        cells = []
        for h in hands:
            row = s.by_hand.get(h)
            cells.append(f"{_pct(row['yield'])} ({_n(row['lines'])})" if row else "—")
        if with_l:
            mine = [y for y in leibniz if y.reader == s.reader]
            n = sum(y.n_lines for y in mine)
            a = sum(y.n_aligned for y in mine)
            cells.append(f"{_pct(a / n if n else None)} ({_n(n)})")
        out.append(f"| {s.reader} | " + " | ".join(cells) + " |")
    out.append("")
    out.append(
        "*own*: the piece is in its author's own hand (the catalogue's *eigh.* on the piece "
        "itself), whoever the author is — on a letter Leibniz received, the correspondent's; "
        "*partial*: only an address, a correction or a postscript is autograph; *other*: a "
        "scribe's hand. The last column narrows *own* to the pieces whose author is Leibniz "
        f"({len({y.record_id for y in leibniz})} pieces, marked (L) below)."
        if with_l
        else "*own*: the piece is in its author's own hand (the catalogue's *eigh.* on the "
        "piece itself), whoever the author is; *partial*: only an address, a correction or a "
        "postscript is autograph; *other*: a scribe's hand."
    )
    out.append("")
    out.append("## The pieces")
    out.append("")
    out.append(
        "| role | record | AA | volume | stratum | hand | pages read / total | lines | "
        + " | ".join(res.readers)
        + " |"
    )
    out.append("|---|---|---|---|---|---|---:|---:|" + "---:|" * len(res.readers))
    for p in res.pieces:
        rows = {y.reader: y for y in res.yields if y.record_id == p.record_id and y.role == p.role}
        n_lines = next((y.n_lines for y in rows.values()), 0)
        cells = " | ".join(_pct(rows[r].yield_rate) if r in rows else "—" for r in res.readers)
        out.append(
            f"| {p.role} | {p.record_id} | {p.aa_label} | {p.volume_label} | {p.stratum} | "
            f"{p.hand or p.language}{' (L)' if p.leibniz_hand else ''} | {len(p.page_ids)} / "
            f"{p.n_pages_total} | {_n(n_lines)} | {cells} |"
        )
    out.append("")
    out.append("## The operator's look")
    out.append("")
    out.append(
        "`data/kurrent/pilot-side-by-side.html` shows thirty German line crops with every reader's "
        "text. Asked whether any reader produces German words, the operator said: "
        + (f"“{res.operator_verdict}”" if res.operator_verdict else "*(not yet recorded)*")
    )
    out.append("")
    out.append("## Verdict for K2")
    out.append("")
    if v.best_reader is None:
        out.append(
            "No reader with a licence to build on could be ranked."
            + (f" {v.licence_note}." if v.licence_note else "")
        )
    else:
        out.append(
            f"The reader K2 should use is **`{v.best_reader}`** at "
            f"**{_pct(v.best_german_yield)}** of the German pieces' lines at the factory's gate "
            f"(the `{BASELINE}` baseline: {_pct(v.baseline_german_yield)}). "
            + (f"{v.licence_note}. " if v.licence_note else "")
            + (
                "The control pieces order as they must, so the German ordering can be trusted as "
                "far as a ground-truth-free measure goes."
                if v.controls_consistent
                else "The control check failed: see above before reading anything into the "
                "ordering."
            )
        )
    out.append("")
    out.append("## What this measures, and what it does not")
    out.append("")
    out.append(
        "- Yield is minted lines over all lines of the piece's pages; a piece's pages may carry "
        "other hands and other texts, and the edition text may omit or reorder what the page "
        "holds (C2b, P1), so no reader reaches 100 % and the absolute numbers are the factory's, "
        "not the readers'. The ordering between readers on the same lines is the measurement."
    )
    out.append(
        "- A high confidence says the machine text matches the edition's letters; it does not say "
        "the slice landed on the right line. The C2b audit found one misaligned line in 185 with "
        "the baseline; a reader with far noisier text could do worse at the boundaries, which the "
        "tolerance study (Task 1) bounds."
    )
    out.append(
        "- The crops are bounding boxes with the polygon masked, not kraken's dewarped extraction; "
        "`v1` was read the corpus run's way, the others this way, so `philiumm` against `v1` is "
        "the price of the crop."
    )
    out.append("")
    return "\n".join(out)


def read_yields(path: Path | str) -> list[PieceYield]:
    """The per-piece, per-reader rows :func:`write_outputs` wrote to ``pilot-yield.csv``."""
    out: list[PieceYield] = []
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out.append(
                PieceYield(
                    record_id=r["record_id"],
                    role=r["role"],
                    reader=r["reader"],
                    volume_label=r["volume"],
                    stratum=r["stratum"],
                    hand=r["hand"],
                    leibniz_hand=r["leibniz_hand"] == "1",
                    threshold=float(r["threshold"]),
                    n_lines=int(r["n_lines"]),
                    n_read=int(r["n_read"]),
                    n_aligned=int(r["n_aligned"]),
                    mean_conf=float(r["mean_conf"]),
                    mean_conf_aligned=(
                        float(r["mean_conf_aligned"]) if r["mean_conf_aligned"] else None
                    ),
                )
            )
    return out


def result_from_files(
    summary_path: Path | str, yields_path: Path | str, *, operator_verdict: str | None = None
) -> PilotResult:
    """A finished pilot rebuilt from its own files, to re-render the report without
    the store, the images or the readings (an operator's verdict added later).

    The two files must come from one run: each reader's German and control line
    and aligned counts in the yields must equal the summary's, or this refuses.
    The committed 2026-10-09 report was re-rendered for the verdict with the
    default page cap (3) over readings taken with a cap of 2, so its counts mixed
    two selections; the re-render path below cannot.
    """
    d = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    yields = read_yields(yields_path)
    summaries = [ReaderSummary(**s) for s in d["summaries"]]
    for s in summaries:
        for role, lines, aligned in (
            ("german", s.german_lines, s.german_aligned),
            ("control", s.control_lines, s.control_aligned),
        ):
            rows = [y for y in yields if y.reader == s.reader and y.role == role]
            got = (sum(y.n_lines for y in rows), sum(y.n_aligned for y in rows))
            if got != (lines, aligned):
                raise ValueError(
                    f"{yields_path} and {summary_path} are not one run: {s.reader} {role} "
                    f"lines/aligned {got} in the yields, {(lines, aligned)} in the summary"
                )
    return PilotResult(
        pieces=[PilotPiece(**p) for p in d["pieces"]],
        yields=yields,
        summaries=summaries,
        verdict=Verdict(**d["verdict"]),
        readers=list(d["readers"]),
        sample=d.get("sample"),
        max_pages=int(d["max_pages"]),
        operator_verdict=operator_verdict
        if operator_verdict is not None
        else d.get("operator_verdict"),
        generated=d.get("generated") or date.today().isoformat(),
    )


def uncovered_pages(
    conn: sqlite3.Connection,
    pieces: Sequence[PilotPiece],
    readings: Mapping[str, Reading],
    *,
    sample: int | None = None,
) -> list[str]:
    """Selected pages with recognised lines but no reading in ``readings``: what a
    ``--no-read`` re-render would count as unread (so as not aligned)."""
    read_pages = {line_id.rpartition(":")[0] for line_id in readings}
    missing: list[str] = []
    for piece in pieces:
        for pid in piece.page_ids:
            if pid not in read_pages and page_lines(conn, pid, sample=sample):
                missing.append(pid)
    return missing


def write_outputs(
    res: PilotResult,
    *,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> dict[str, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "report": reports_dir / "pilot.md",
        "summary": reports_dir / "pilot-summary.json",
        "yields": reports_dir / "pilot-yield.csv",
    }
    paths["report"].write_text(render_report(res), encoding="utf-8")
    paths["summary"].write_text(
        json.dumps(res.as_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with paths["yields"].open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "record_id",
                "role",
                "reader",
                "volume",
                "stratum",
                "hand",
                "leibniz_hand",
                "threshold",
                "n_lines",
                "n_read",
                "n_aligned",
                "yield",
                "mean_conf",
                "mean_conf_aligned",
            ]
        )
        for y in res.yields:
            w.writerow(
                [
                    y.record_id,
                    y.role,
                    y.reader,
                    y.volume_label,
                    y.stratum,
                    y.hand,
                    int(y.leibniz_hand),
                    f"{y.threshold:.2f}",
                    y.n_lines,
                    y.n_read,
                    y.n_aligned,
                    "" if y.yield_rate is None else f"{y.yield_rate:.4f}",
                    f"{y.mean_conf:.4f}",
                    "" if y.mean_conf_aligned is None else f"{y.mean_conf_aligned:.4f}",
                ]
            )
    return paths


__all__ = [
    "BASELINE",
    "DEFAULT_GERMAN",
    "DEFAULT_IMAGES_ROOT",
    "DEFAULT_READINGS_DIR",
    "DEFAULT_SIDE_BY_SIDE",
    "QUALIFY_RATIO",
    "V1",
    "PieceYield",
    "PilotLine",
    "PilotPiece",
    "PilotResult",
    "Reading",
    "ReaderSummary",
    "Verdict",
    "append_readings",
    "crop",
    "dry_run",
    "dry_run_piece",
    "load_german_pieces",
    "load_readings",
    "open_readonly",
    "page_lines",
    "qualifying_readers",
    "read_pieces",
    "read_yields",
    "render_report",
    "result_from_files",
    "select_controls",
    "select_german",
    "side_by_side",
    "summarize_readers",
    "uncovered_pages",
    "v1_readings",
    "verdict",
    "write_outputs",
]
