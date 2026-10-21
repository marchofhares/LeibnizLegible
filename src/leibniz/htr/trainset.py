"""The training set of a fine-tune (K3; C3 reuses it): minted lines as files, tagged.

One tool serves both fine-tunes. It takes the rows of ``gt_lines`` the caller
selects (K3: the rows on the German records of the census; C3: every
open-bucket row), applies the exclusions the C2b audit taught (``math`` and
``bracket`` lines, Marginalien works, the PHILIUMM held-out pages, the
letter-pool pages, the judged audit lines), draws a **validation set before
any training and freezes it** — whole pieces, joined over the pages they
share so that no page sits on both sides, stratified by stratum and hand —
and cuts every kept line through the pilot's crop (the polygon masked, the
audit's padding, no downscaling) into ``<out>/<split>/<page>/<seq>.png`` with
a ``.gt.txt`` beside it, Kraken's training format, which the TrOCR loader
reads as well. ``manifest.jsonl`` carries every row, kept or excluded, with
its tags: the record, the volume, the stratum, the hand (Leibniz's own under
``catalog/hands.py``'s strict rule, against the rest) and the reader whose
text the line was aligned on (K2's reader rows against the v1-minted rows),
so that a later verdict on the audit sheet can drop a class of lines without
rebuilding the crops; its ``screen`` field says why a line falls outside the
band below, so the ablation without that class is a filter on the manifest.

**The screen** (the operator's note of 21 October): no judge has read K2's
lines yet, so before training each reader line is given two figures — the
aligner's confidence and the ratio of the minted text's length to the
reading's length — and the lines are summarised by hand group against the
band the v1-minted Latin and French lines occupy (their central 95 % in both
figures). A line outside the band is not thereby wrong (a long edition slice
on a short reading, or the reverse, is what a misplaced line looks like, but
also what an abbreviation-heavy line looks like); the share outside the band
per group, and the twenty worst ids, go into STATUS.md, and more than about
one Leibniz-hand line in ten outside the band stops the phase before the
timing pilots.

Everything here is offline and deterministic (seeded draws); the store is
opened read-only by the CLI. Pillow is the only heavy import and it is
lazy; the tests run the whole chain on a seeded store with synthetic pages.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz.align.audit import CROP_PAD, crop_image, line_geometry, split_ref
from leibniz.align.audit_patterns import has_bracket, is_math_dense
from leibniz.align.audit_reach import MARGINALIEN_SET, parse_source
from leibniz.align.pairs import READER_SQL, reader_from_source
from leibniz.catalog.hands import hand_from_textart, is_leibniz_hand
from leibniz.images.fetch import cache_relpath

DEFAULT_OUT = Path("data/train/k3")
DEFAULT_IMAGES_ROOT = Path("/mnt/d/leibniz-images")
DEFAULT_RECORDS = Path("data/kurrent/german_pieces.jsonl")
DEFAULT_READINGS = Path("data/kurrent/k2-readings/trocr-kurrent-xvi-xvii.jsonl")
DEFAULT_FLAGS = Path("data/gt/flags.jsonl")
DEFAULT_HELDOUT = Path("reports/philiumm/heldout_pages.csv")
DEFAULT_POOL = Path("reports/kurrent/letterpool-testset.csv")
DEFAULT_AUDITS: tuple[Path, ...] = (
    Path("data/kurrent/k2-audit-lines.csv"),
    Path("reports/gt-audit/gt-audit-verdicts-philiumm.csv"),
)
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
DEFAULT_NAME = "k3"
SEED = 20261021
VAL_SHARE = 0.05
BAND = (0.025, 0.975)  # the central 95 %
STOP_SHARE = 0.10  # more than this share of Leibniz-hand lines outside the band stops the phase
V1 = "v1"
STRATA = ("fair_copy", "light_revision", "heavy_revision", "scrap", "unknown")
GROUPS = ("leibniz", "other")
SPLITS = ("train", "val")
# Symbols no manuscript line carries: the OCR layer of a free copy leaked them
# into the minted text (``©``, ``™``, ``■`` in a formula, a bullet).
NOISE_CHARS = frozenset("©®™■□•")
# The edition's angle brackets (a conjectural supplement) — the bracket flag's
# square brackets by another name.
ANGLE_CHARS = frozenset("〈〉⟨⟩")
EXCLUSIONS = (
    "heldout_page",
    "pool_page",
    "marginalien",
    "math",
    "bracket",
    "noise",
    "audit",
    "bad_ref",
    "no_geometry",
    "no_image",
    "no_crop",
)


# --------------------------------------------------------------------------- #
# Rows
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class TrainLine:
    """One minted line with its tags; ``split`` and ``reason`` say where it went."""

    ref: str
    page_id: str
    line_seq: int
    record_id: str
    volume: str
    stratum: str
    hand: str  # own | partial | other | none (catalog/hands.py)
    group: str  # leibniz | other (the strict rule)
    reader: str  # "v1" or the reader key the source names
    align_conf: float
    text: str
    machine_text: str | None = None  # the text the line was aligned on
    ratio: float | None = None  # len(text) / len(machine_text), whitespace collapsed
    flags: list[str] = field(default_factory=list)
    screen: list[str] = field(default_factory=list)  # why the line is outside the band
    unit: str = ""  # the page-joined piece group
    split: str = ""  # train | val | excluded
    reason: str = ""  # the exclusion, where excluded
    image: str = ""  # the crop's path relative to the output root, once cut
    n_chars: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def read_record_ids(path: Path | str) -> list[str]:
    """Record ids from a JSONL (``record_id`` per row; the census file) or a CSV."""
    p = Path(path)
    out: list[str] = []
    seen: set[str] = set()
    if p.suffix == ".csv":
        with p.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                rid = str(row.get("record_id") or "").strip()
                if rid and rid not in seen:
                    seen.add(rid)
                    out.append(rid)
        return out
    for raw in p.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            rid = str(json.loads(raw).get("record_id") or "").strip()
            if rid and rid not in seen:
                seen.add(rid)
                out.append(rid)
    return out


def _collapsed_len(text: str) -> int:
    return len(" ".join(text.split()))


def load_rows(conn, record_ids: Sequence[str] | None = None) -> list[TrainLine]:
    """The open-bucket rows of ``gt_lines`` (of the records given, else all), untagged."""
    sql = (
        "SELECT line_image_ref, text, source, stratum, align_conf, record_id "
        "FROM gt_lines WHERE license_bucket = 'open'"
    )
    params: list = []
    if record_ids is not None:
        marks = ",".join("?" * len(record_ids))
        sql += f" AND record_id IN ({marks})"
        params = list(record_ids)
    out: list[TrainLine] = []
    for r in conn.execute(sql + " ORDER BY id", params):
        ref, text, source = r[0], r[1] or "", r[2] or ""
        volume, rec = parse_source(source)
        rid = str(r[5] or rec or "")
        try:
            page_id, seq = split_ref(ref)
        except ValueError:
            page_id, seq = "", -1
        out.append(
            TrainLine(
                ref=ref,
                page_id=page_id,
                line_seq=seq,
                record_id=rid,
                volume=volume or "",
                stratum=r[3] or "unknown",
                hand="none",
                group="other",
                reader=reader_from_source(source) or V1,
                align_conf=float(r[4] or 0.0),
                text=text,
                n_chars=_collapsed_len(text),
            )
        )
    return out


def record_hands(conn, record_ids: Iterable[str]) -> dict[str, tuple[str, bool]]:
    """``record_id -> (hand, Leibniz's own)`` from the catalogue's Textart and sender."""
    out: dict[str, tuple[str, bool]] = {}
    for rid in set(record_ids):
        row = conn.execute(
            "SELECT metadata FROM katalog_records WHERE record_id = ?", (rid,)
        ).fetchone()
        meta = json.loads(row[0]) if row is not None and row[0] else {}
        ta = meta.get("textart")
        hand = hand_from_textart(str(ta) if ta else None)
        sender = meta.get("absender")
        out[rid] = (hand, is_leibniz_hand(hand, str(sender) if sender else None))
    return out


def tag_hands(lines: Sequence[TrainLine], hands: Mapping[str, tuple[str, bool]]) -> None:
    for ln in lines:
        hand, leibniz = hands.get(ln.record_id, ("none", False))
        ln.hand = hand
        ln.group = "leibniz" if leibniz else "other"


def v1_texts(conn, pages: Iterable[str]) -> dict[str, str]:
    """``ref -> the store's v1 text`` for every recognised line of the pages (the row
    with text from the latest run, as the audit and the reach census take it)."""
    out: dict[str, str] = {}
    for pid in set(pages):
        best: dict[int, tuple[int, str]] = {}
        for row in conn.execute(
            "SELECT line_seq, run_id, text FROM lines WHERE page_id = ? AND text IS NOT NULL",
            (pid,),
        ):
            seq, run = row[0], row[1] or 0
            if seq not in best or run > best[seq][0]:
                best[seq] = (run, row[2])
        for seq, (_run, text) in best.items():
            out[f"{pid}:{seq:03d}"] = text
    return out


def load_readings_text(path: Path | str) -> dict[str, str]:
    """``line id -> text`` from a reader's JSONL (K2's readings)."""
    out: dict[str, str] = {}
    p = Path(path)
    if not p.exists():
        return out
    with p.open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                row = json.loads(raw)
                out[row["line_id"]] = row.get("text") or ""
    return out


def attach_machine_text(
    lines: Sequence[TrainLine], v1: Mapping[str, str], readers: Mapping[str, Mapping[str, str]]
) -> None:
    """The text each line was aligned on, and the length ratio against it."""
    for ln in lines:
        src = v1 if ln.reader == V1 else readers.get(ln.reader, {})
        mt = src.get(ln.ref)
        ln.machine_text = mt
        if mt is None:
            ln.ratio = None
            continue
        den = _collapsed_len(mt)
        ln.ratio = (ln.n_chars / den) if den else (math.inf if ln.n_chars else None)


# --------------------------------------------------------------------------- #
# Exclusions
# --------------------------------------------------------------------------- #


def load_flags(path: Path | str) -> dict[str, list[str]]:
    p = Path(path)
    out: dict[str, list[str]] = {}
    if not p.exists():
        return out
    with p.open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                row = json.loads(raw)
                out[row["ref"]] = list(row.get("flags") or [])
    return out


def pages_from_csv(path: Path | str) -> set[str]:
    """Page ids from a CSV with a ``page_id`` column or a space-separated ``page_ids`` one."""
    p = Path(path)
    out: set[str] = set()
    if not p.exists():
        return out
    with p.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("page_id"):
                out.add(row["page_id"].strip())
            if row.get("page_ids"):
                out.update(row["page_ids"].split())
    return out


def refs_from_csvs(paths: Iterable[Path | str]) -> set[str]:
    out: set[str] = set()
    for path in paths:
        p = Path(path)
        if not p.exists():
            continue
        with p.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("ref"):
                    out.add(row["ref"].strip())
    return out


def marginalien_works(conn, work_ids: Iterable[str]) -> set[str]:
    out: set[str] = set()
    for wid in set(work_ids):
        row = conn.execute("SELECT set_name FROM works WHERE gwlb_object_id = ?", (wid,)).fetchone()
        if row is not None and row[0] == MARGINALIEN_SET:
            out.add(wid)
    return out


def flag_lines(
    lines: Sequence[TrainLine],
    *,
    flags: Mapping[str, Sequence[str]],
    heldout: set[str],
    pool: set[str],
    marginalien: set[str],
    audit: set[str],
) -> None:
    """Every line's flags (the reach census's for v1 rows, the same patterns run over
    the reader rows) and, where one applies, its exclusion — the first in
    :data:`EXCLUSIONS` order."""
    for ln in lines:
        f: list[str] = []
        if ln.reader == V1 and ln.ref in flags:
            f.extend(x for x in flags[ln.ref] if x in ("math", "bracket"))
        else:
            if is_math_dense(ln.text):
                f.append("math")
            if has_bracket(ln.text):
                f.append("bracket")
        if any(ch in ANGLE_CHARS for ch in ln.text) and "bracket" not in f:
            f.append("bracket")
        if any(ch in NOISE_CHARS for ch in ln.text):
            f.append("noise")
        if ln.page_id in heldout:
            f.append("heldout_page")
        if ln.page_id in pool:
            f.append("pool_page")
        if ln.page_id.rpartition(":")[0] in marginalien:
            f.append("marginalien")
        if ln.ref in audit:
            f.append("audit")
        if not ln.page_id or ln.line_seq < 0:
            f.append("bad_ref")
        ln.flags = f
        reason = next((x for x in EXCLUSIONS if x in f), "")
        if reason:
            ln.split, ln.reason = "excluded", reason


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


def _quantile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    pos = q * (len(xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


@dataclass(slots=True)
class Band:
    """The central 95 % of the reference lines in both figures."""

    n: int
    ratio_lo: float
    ratio_hi: float
    ratio_median: float
    conf_lo: float
    conf_median: float

    def as_dict(self) -> dict:
        return asdict(self)


def band_of(ratios: Sequence[float], confs: Sequence[float], q: tuple[float, float] = BAND) -> Band:
    finite = [r for r in ratios if r is not None and math.isfinite(r)]
    return Band(
        n=len(finite),
        ratio_lo=_quantile(finite, q[0]) or 0.0,
        ratio_hi=_quantile(finite, q[1]) or 0.0,
        ratio_median=_quantile(finite, 0.5) or 0.0,
        conf_lo=_quantile(list(confs), q[0]) or 0.0,
        conf_median=_quantile(list(confs), 0.5) or 0.0,
    )


def reference_band(conn, exclude_records: Iterable[str]) -> Band:
    """The band from the v1-minted rows outside the given records (the Latin and
    French mint): the ratio of the minted text to the store's v1 text."""
    excl = set(exclude_records)
    rows = conn.execute(
        "SELECT line_image_ref, text, align_conf, record_id FROM gt_lines "
        f"WHERE license_bucket = 'open' AND NOT ({READER_SQL})"
    ).fetchall()
    rows = [r for r in rows if str(r[3] or "") not in excl]
    pages: set[str] = set()
    for r in rows:
        try:
            pages.add(split_ref(r[0])[0])
        except ValueError:
            continue
    v1 = v1_texts(conn, pages)
    ratios: list[float] = []
    confs: list[float] = []
    for r in rows:
        mt = v1.get(r[0])
        if mt is None:
            continue
        den = _collapsed_len(mt)
        num = _collapsed_len(r[1] or "")
        if den:
            ratios.append(num / den)
        confs.append(float(r[2] or 0.0))
    return band_of(ratios, confs)


def outside(ln: TrainLine, band: Band) -> list[str]:
    """Why a line falls outside the band: ``ratio_low``, ``ratio_high``, ``no_reading``,
    ``conf_low``; empty inside."""
    why: list[str] = []
    if ln.ratio is None:
        why.append("no_reading")
    elif ln.ratio < band.ratio_lo:
        why.append("ratio_low")
    elif ln.ratio > band.ratio_hi:
        why.append("ratio_high")
    if ln.align_conf < band.conf_lo:
        why.append("conf_low")
    return why


def _finite(x: float | None, d: int = 3) -> float | None:
    return None if x is None or not math.isfinite(x) else round(x, d)


def screen(
    lines: Sequence[TrainLine], band: Band, *, reader: str | None = None, worst_n: int = 20
) -> dict:
    """The reader's lines (every reader but v1 when ``reader`` is None) that no flag
    excluded — the lines that would be trained on — by hand group against the band;
    the share outside per group and the worst ids."""
    chosen = [
        ln
        for ln in lines
        if (ln.reader != V1 if reader is None else ln.reader == reader) and not ln.reason
    ]
    by_group: dict[str, dict] = {}
    for g in GROUPS:
        gl = [ln for ln in chosen if ln.group == g]
        ratios = [ln.ratio for ln in gl if ln.ratio is not None and math.isfinite(ln.ratio)]
        confs = [ln.align_conf for ln in gl]
        why = Counter()
        n_out = 0
        for ln in gl:
            w = outside(ln, band)
            if w:
                n_out += 1
                why.update(w)
        by_group[g] = {
            "n": len(gl),
            "ratio_p2_5": _quantile(ratios, BAND[0]),
            "ratio_median": _quantile(ratios, 0.5),
            "ratio_p97_5": _quantile(ratios, BAND[1]),
            "conf_p2_5": _quantile(confs, BAND[0]),
            "conf_median": _quantile(confs, 0.5),
            "outside": n_out,
            "outside_share": (n_out / len(gl)) if gl else None,
            "outside_by": dict(sorted(why.items())),
        }

    # the worst: the farthest outside the ratio band (in log units), then the lowest confidence
    def badness(ln: TrainLine) -> tuple[float, float]:
        if ln.ratio is None or not math.isfinite(ln.ratio) or ln.ratio <= 0:
            return (math.inf, -ln.align_conf)
        lr = math.log(ln.ratio)
        lo = math.log(band.ratio_lo) if band.ratio_lo > 0 else -math.inf
        hi = math.log(band.ratio_hi) if band.ratio_hi > 0 else math.inf
        dist = max(0.0, lo - lr, lr - hi)
        return (dist, -ln.align_conf)

    worst = sorted((ln for ln in chosen if outside(ln, band)), key=badness, reverse=True)[:worst_n]
    v1_lines = [ln for ln in lines if ln.reader == V1 and not ln.reason]
    v1_out = sum(1 for ln in v1_lines if outside(ln, band))
    leib = by_group.get("leibniz", {})
    return {
        "band": band.as_dict(),
        "reader": reader or "every reader but v1",
        "by_group": by_group,
        "v1_rows": {
            "n": len(v1_lines),
            "outside": v1_out,
            "outside_share": (v1_out / len(v1_lines)) if v1_lines else None,
        },
        "worst": [
            {
                "ref": ln.ref,
                "group": ln.group,
                "record_id": ln.record_id,
                "stratum": ln.stratum,
                "ratio": _finite(ln.ratio),
                "conf": round(ln.align_conf, 3),
                "why": outside(ln, band),
                "n_chars": ln.n_chars,
                "machine_chars": _collapsed_len(ln.machine_text or ""),
            }
            for ln in worst
        ],
        "stop_share": STOP_SHARE,
        "stop": bool(leib.get("outside_share") is not None and leib["outside_share"] > STOP_SHARE),
    }


# --------------------------------------------------------------------------- #
# Units and the validation draw
# --------------------------------------------------------------------------- #


def units_of(lines: Sequence[TrainLine]) -> dict[str, str]:
    """``record_id -> unit``: records joined over the pages they share (union-find);
    the unit is named after its smallest record id."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    first_on_page: dict[str, str] = {}
    for ln in lines:
        find(ln.record_id)
        other = first_on_page.setdefault(ln.page_id, ln.record_id)
        if other != ln.record_id:
            union(other, ln.record_id)
    return {rid: find(rid) for rid in parent}


def _cell(ln: TrainLine) -> tuple[str, str]:
    return ln.stratum, ln.group


def draw_validation(
    lines: Sequence[TrainLine], *, share: float = VAL_SHARE, seed: int = SEED
) -> tuple[set[str], dict]:
    """The validation units, drawn seeded: per (stratum, hand group) cell, units
    whose majority of kept lines sits in the cell are shuffled and taken until the
    cell's quota of lines (``share`` of its kept lines) is met, a unit skipped when
    it would overshoot the quota by more than half of it (or 50 lines), the
    smallest unit taken if nothing fits; a cell with a single unit keeps it in
    training and says so. Returns the unit ids and the draw's account."""
    kept = [ln for ln in lines if ln.split != "excluded"]
    unit_lines: dict[str, list[TrainLine]] = defaultdict(list)
    for ln in kept:
        unit_lines[ln.unit].append(ln)
    unit_cell: dict[str, tuple[str, str]] = {}
    for u, ls in unit_lines.items():
        cnt = Counter(_cell(x) for x in ls)
        unit_cell[u] = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    cells: dict[tuple[str, str], list[str]] = defaultdict(list)
    for u, c in unit_cell.items():
        cells[c].append(u)
    cell_lines: Counter = Counter(_cell(ln) for ln in kept)
    rng = random.Random(seed)
    val: set[str] = set()
    account: dict[str, dict] = {}
    for c in sorted(cells):
        us = sorted(cells[c])
        rng.shuffle(us)
        quota = round(share * cell_lines[c])
        taken: list[str] = []
        got = 0
        note = ""
        if len(us) < 2:
            note = "a single unit: kept in training"
        else:
            slack = max(50, quota // 2)
            for u in us:
                if got >= quota:
                    break
                size = len(unit_lines[u])
                if got + size <= quota + slack:
                    taken.append(u)
                    got += size
            if not taken:
                u = min(us, key=lambda x: len(unit_lines[x]))
                taken.append(u)
                got = len(unit_lines[u])
                note = "no unit fit the quota: the smallest taken"
        val.update(taken)
        account[f"{c[0]}/{c[1]}"] = {
            "stratum": c[0],
            "group": c[1],
            "lines": cell_lines[c],
            "units": len(us),
            "quota": quota,
            "val_units": len(taken),
            "val_lines_of_cell_units": got,
            "note": note,
        }
    return val, {"share": share, "seed": seed, "cells": account}


def apply_split(lines: Sequence[TrainLine], val_units: set[str]) -> None:
    for ln in lines:
        if ln.split == "excluded":
            continue
        ln.split = "val" if ln.unit in val_units else "train"


VAL_COLUMNS = ("unit", "record_id", "volume", "stratum", "group", "n_lines")


def write_val_pieces(path: Path | str, lines: Sequence[TrainLine]) -> Path:
    """The frozen validation pieces: one row per record of a validation unit."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows: dict[str, dict] = {}
    for ln in lines:
        if ln.split != "val":
            continue
        r = rows.setdefault(
            ln.record_id,
            {
                "unit": ln.unit,
                "record_id": ln.record_id,
                "volume": ln.volume,
                "stratum": ln.stratum,
                "group": ln.group,
                "n_lines": 0,
            },
        )
        r["n_lines"] += 1
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=VAL_COLUMNS)
        w.writeheader()
        for r in sorted(rows.values(), key=lambda r: (r["unit"], r["record_id"])):
            w.writerow(r)
    return p


def read_val_pieces(path: Path | str) -> set[str]:
    """The record ids of a frozen validation set (empty when the file is absent)."""
    p = Path(path)
    if not p.exists():
        return set()
    with p.open(encoding="utf-8", newline="") as fh:
        return {row["record_id"] for row in csv.DictReader(fh) if row.get("record_id")}


# --------------------------------------------------------------------------- #
# Crops
# --------------------------------------------------------------------------- #


def crop_relpath(ln: TrainLine) -> str:
    return f"{ln.split}/{ln.page_id}/{ln.line_seq:03d}.png"


def _cut_page(job: tuple) -> list[tuple[str, str, int]]:
    """One page's crops, in a worker: ``(ref, status, bytes)`` per line; the status
    ``ok`` or an exclusion reason. The page image is decoded once."""
    image_path, out_root, items = job
    from PIL import Image

    out: list[tuple[str, str, int]] = []
    if image_path is None or not Path(image_path).exists():
        return [(ref, "no_image", 0) for ref, *_ in items]
    try:
        im = Image.open(image_path)
        im.load()
    except OSError:
        return [(ref, "no_image", 0) for ref, *_ in items]
    with im:
        for ref, polygon, baseline, text, rel in items:
            if not polygon and not baseline:
                out.append((ref, "no_geometry", 0))
                continue
            try:
                crop = crop_image(
                    im, polygon, baseline, pad=CROP_PAD, max_width=None, mask_polygon=True
                )
            except OSError:
                crop = None
            if crop is None:
                out.append((ref, "no_crop", 0))
                continue
            target = Path(out_root) / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".png.part")
            crop.save(tmp, format="PNG", optimize=True)
            tmp.replace(target)
            target.with_suffix(".gt.txt").write_text(text + "\n", encoding="utf-8")
            out.append((ref, "ok", target.stat().st_size))
    return out


def page_image_paths(conn, pages: Iterable[str], images_root: Path | str) -> dict[str, Path | None]:
    out: dict[str, Path | None] = {}
    for pid in set(pages):
        row = conn.execute(
            "SELECT work_id, seq, local_path FROM pages WHERE page_id = ?", (pid,)
        ).fetchone()
        if row is None:
            out[pid] = None
            continue
        rel = row[2] or cache_relpath(row[0], row[1])
        p = Path(images_root) / rel
        out[pid] = p if p.exists() else None
    return out


def crop_jobs(
    conn, lines: Sequence[TrainLine], images_root: Path | str, out_root: Path | str
) -> list[tuple]:
    """One job per page for :func:`_cut_page`, over the kept lines; a line's geometry is
    the row the audit takes."""
    by_page: dict[str, list[TrainLine]] = defaultdict(list)
    for ln in lines:
        if ln.split in SPLITS:
            by_page[ln.page_id].append(ln)
    paths = page_image_paths(conn, by_page, images_root)
    jobs: list[tuple] = []
    for pid in sorted(by_page):
        items = []
        for ln in by_page[pid]:
            polygon, baseline, _text = line_geometry(conn, pid, ln.line_seq)
            items.append((ln.ref, polygon, baseline, ln.text, crop_relpath(ln)))
        path = paths.get(pid)
        jobs.append((str(path) if path else None, str(out_root), items))
    return jobs


def cut_crops(
    jobs: Sequence[tuple],
    lines: Sequence[TrainLine],
    *,
    workers: int = 0,
    log: Callable[[str], None] | None = None,
    every: int = 200,
) -> dict:
    """Run the jobs (inline, or in a process pool with ``workers`` > 0) and mark every
    line with its crop path or its exclusion. Returns the tally."""
    by_ref = {ln.ref: ln for ln in lines}
    tally: Counter = Counter()
    n_bytes = 0
    done = 0

    def take(results: Iterable[tuple[str, str, int]]) -> None:
        nonlocal n_bytes
        for ref, status, size in results:
            ln = by_ref[ref]
            if status == "ok":
                ln.image = crop_relpath(ln)
                n_bytes += size
            else:
                ln.split, ln.reason = "excluded", status
                ln.flags.append(status)
            tally[status] += 1

    if workers and workers > 0:
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(max_workers=workers) as pool:
            for results in pool.map(_cut_page, jobs, chunksize=4):
                take(results)
                done += 1
                if log and done % every == 0:
                    log(f"  {done:,} of {len(jobs):,} pages cut, {tally['ok']:,} crops")
    else:
        for job in jobs:
            take(_cut_page(job))
            done += 1
            if log and done % every == 0:
                log(f"  {done:,} of {len(jobs):,} pages cut, {tally['ok']:,} crops")
    return {"pages": len(jobs), "by_status": dict(sorted(tally.items())), "bytes": n_bytes}


def estimate_disk(
    conn,
    lines: Sequence[TrainLine],
    *,
    n: int,
    images_root: Path | str,
    out_root: Path | str,
    seed: int = SEED,
    workers: int = 0,
) -> dict:
    """Cut a seeded sample of ``n`` kept lines into ``out_root`` and project the disk."""
    kept = [ln for ln in lines if ln.split in SPLITS]
    rng = random.Random(seed)
    sample = rng.sample(kept, min(n, len(kept)))
    # copies, so the sample's statuses do not touch the real lines
    copies = [TrainLine(**ln.as_dict()) for ln in sample]
    jobs = crop_jobs(conn, copies, images_root, out_root)
    tally = cut_crops(jobs, copies, workers=workers)
    ok = tally["by_status"].get("ok", 0)
    per_line = (tally["bytes"] / ok) if ok else None
    return {
        "sampled": len(copies),
        "cut": ok,
        "bytes": tally["bytes"],
        "bytes_per_line": per_line,
        "kept_lines": len(kept),
        "projected_bytes": (per_line * len(kept)) if per_line else None,
        "by_status": tally["by_status"],
    }


# --------------------------------------------------------------------------- #
# The build
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class TrainSet:
    name: str
    lines: list[TrainLine]
    band: Band
    screen: dict
    draw: dict
    val_frozen: bool  # the validation pieces were read from a frozen file
    crops: dict = field(default_factory=dict)
    estimate: dict | None = None
    records: int = 0
    generated: str = field(default_factory=lambda: date.today().isoformat())


def build(
    conn,
    *,
    record_ids: Sequence[str] | None,
    readings: Mapping[str, Mapping[str, str]],
    flags: Mapping[str, Sequence[str]],
    heldout: set[str],
    pool: set[str],
    audit: set[str],
    val_pieces: Path | str | None = None,
    share: float = VAL_SHARE,
    seed: int = SEED,
    band: Band | None = None,
    name: str = DEFAULT_NAME,
    log: Callable[[str], None] | None = None,
) -> TrainSet:
    """Select, tag, flag, screen and split; no crop is cut here."""
    lines = load_rows(conn, record_ids)
    if log:
        log(f"{len(lines):,} open-bucket rows selected")
    tag_hands(lines, record_hands(conn, (ln.record_id for ln in lines)))
    pages = {ln.page_id for ln in lines if ln.page_id}
    attach_machine_text(lines, v1_texts(conn, pages), readings)
    works = {ln.page_id.rpartition(":")[0] for ln in lines if ln.page_id}
    flag_lines(
        lines,
        flags=flags,
        heldout=heldout,
        pool=pool,
        marginalien=marginalien_works(conn, works),
        audit=audit,
    )
    if band is None:
        band = reference_band(conn, [ln.record_id for ln in lines])
    for ln in lines:
        ln.screen = outside(ln, band)
    sc = screen(lines, band)
    units = units_of(lines)
    for ln in lines:
        ln.unit = units.get(ln.record_id, ln.record_id)
    frozen = read_val_pieces(val_pieces) if val_pieces else set()
    if frozen:
        val_units = {units[r] for r in frozen if r in units}
        draw = {"share": share, "seed": seed, "cells": {}, "frozen_from": str(val_pieces)}
    else:
        val_units, draw = draw_validation(lines, share=share, seed=seed)
    apply_split(lines, val_units)
    return TrainSet(
        name=name,
        lines=lines,
        band=band,
        screen=sc,
        draw=draw,
        val_frozen=bool(frozen),
        records=len({ln.record_id for ln in lines}),
    )


# --------------------------------------------------------------------------- #
# Summary and outputs
# --------------------------------------------------------------------------- #


def _table(lines: Iterable[TrainLine], key: Callable[[TrainLine], str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for ln in lines:
        d = out.setdefault(key(ln), {"lines": 0, "chars": 0, "records": set()})
        d["lines"] += 1
        d["chars"] += ln.n_chars
        d["records"].add(ln.record_id)
    return {
        k: {"lines": v["lines"], "chars": v["chars"], "records": len(v["records"])}
        for k, v in sorted(out.items())
    }


def summarize(ts: TrainSet) -> dict:
    lines = ts.lines
    kept = [ln for ln in lines if ln.split in SPLITS]
    by_split = {s: [ln for ln in lines if ln.split == s] for s in SPLITS}
    excluded = [ln for ln in lines if ln.split == "excluded"]
    pages_train = {ln.page_id for ln in by_split["train"]}
    pages_val = {ln.page_id for ln in by_split["val"]}
    return {
        "name": ts.name,
        "generated": ts.generated,
        "selection": {
            "rows": len(lines),
            "records": ts.records,
            "pages": len({ln.page_id for ln in lines if ln.page_id}),
            "by_reader": _table(lines, lambda ln: ln.reader),
            "by_group": _table(lines, lambda ln: ln.group),
        },
        "exclusions": {
            "total": len(excluded),
            "by_reason": dict(sorted(Counter(ln.reason for ln in excluded).items())),
            "by_reason_and_reader": dict(
                sorted(Counter(f"{ln.reason}/{ln.reader}" for ln in excluded).items())
            ),
            "flag_counts": dict(sorted(Counter(f for ln in lines for f in ln.flags).items())),
        },
        "kept": {
            "lines": len(kept),
            "records": len({ln.record_id for ln in kept}),
            "pages": len({ln.page_id for ln in kept}),
            "units": len({ln.unit for ln in kept}),
            "chars": sum(ln.n_chars for ln in kept),
        },
        "splits": {
            s: {
                "lines": len(ls),
                "records": len({ln.record_id for ln in ls}),
                "pages": len({ln.page_id for ln in ls}),
                "units": len({ln.unit for ln in ls}),
                "chars": sum(ln.n_chars for ln in ls),
                "by_stratum": _table(ls, lambda ln: ln.stratum),
                "by_group": _table(ls, lambda ln: ln.group),
                "by_reader": _table(ls, lambda ln: ln.reader),
                "by_hand": _table(ls, lambda ln: ln.hand),
                "by_cell": _table(ls, lambda ln: f"{ln.stratum}/{ln.group}"),
            }
            for s, ls in by_split.items()
        },
        "pages_shared_between_splits": len(pages_train & pages_val),
        "val_frozen": ts.val_frozen,
        "draw": ts.draw,
        "screen": ts.screen,
        "crops": ts.crops,
        "estimate": ts.estimate,
    }


def write_manifest(ts: TrainSet, out_root: Path | str) -> dict[str, Path]:
    """``manifest.jsonl`` (every row), ``train.txt`` and ``val.txt`` (the crops' paths,
    one per line, as ketos reads them) under the output root."""
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {"manifest": root / "manifest.jsonl"}
    with paths["manifest"].open("w", encoding="utf-8") as fh:
        for ln in ts.lines:
            fh.write(json.dumps(ln.as_dict(), ensure_ascii=False) + "\n")
    for s in SPLITS:
        p = root / f"{s}.txt"
        with p.open("w", encoding="utf-8") as fh:
            for ln in ts.lines:
                if ln.split == s and ln.image:
                    fh.write(str(root / ln.image) + "\n")
        paths[s] = p
    return paths


def read_manifest(path: Path | str) -> list[TrainLine]:
    fields = set(TrainLine.__slots__)  # type: ignore[attr-defined]
    out: list[TrainLine] = []
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                row = json.loads(raw)
                out.append(TrainLine(**{k: v for k, v in row.items() if k in fields}))
    return out


def _n(x: int | None) -> str:
    return "—" if x is None else f"{x:,}"


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{100 * x:.{d}f} %"


def _f(x: float | None, d: int = 2) -> str:
    return "—" if x is None else f"{x:.{d}f}"


def _gb(x: float | None) -> str:
    return "—" if x is None else f"{x / 1e9:.2f} GB"


def render_report(s: Mapping) -> str:
    """The training-set report, from the summary."""
    name = s["name"]
    L: list[str] = [
        f"# {name.upper()}: the training set",
        "",
        f"The minted lines selected for the fine-tune, tagged, screened and split; crops under "
        f"`data/train/{name}/`, every row in its `manifest.jsonl`. Generated {s['generated']}.",
        "",
        "## Selection",
        "",
        f"**{_n(s['selection']['rows'])} open-bucket rows** on {_n(s['selection']['records'])} "
        f"records and {_n(s['selection']['pages'])} pages.",
        "",
        "| reader | lines | records | characters |",
        "|---|---:|---:|---:|",
    ]
    for k, v in s["selection"]["by_reader"].items():
        L.append(f"| {k} | {_n(v['lines'])} | {_n(v['records'])} | {_n(v['chars'])} |")
    L += ["", "| hand group | lines | records | characters |", "|---|---:|---:|---:|"]
    for k, v in s["selection"]["by_group"].items():
        L.append(f"| {k} | {_n(v['lines'])} | {_n(v['records'])} | {_n(v['chars'])} |")
    L += [
        "",
        "## Exclusions",
        "",
        f"{_n(s['exclusions']['total'])} rows excluded, the first reason that applies in the order "
        "held-out page, letter-pool page, Marginalien, math, bracket, noise, audit, then the "
        "crop's failure.",
        "",
        "| reason | rows |",
        "|---|---:|",
    ]
    for k, v in s["exclusions"]["by_reason"].items():
        L.append(f"| {k} | {_n(v)} |")
    L += [
        "",
        "By reason and reader: "
        + ", ".join(f"{k} {_n(v)}" for k, v in s["exclusions"]["by_reason_and_reader"].items())
        + ".",
        "",
    ]
    sc = s["screen"]
    b = sc["band"]
    L += [
        "## The screen",
        "",
        f"The band the v1-minted Latin and French lines occupy ({_n(b['n'])} rows): the ratio of "
        f"the minted text's length to the v1 reading's between **{_f(b['ratio_lo'])} and "
        f"{_f(b['ratio_hi'])}** (median {_f(b['ratio_median'])}), the alignment confidence at or "
        f"above **{_f(b['conf_lo'], 3)}** (median {_f(b['conf_median'], 3)}). A reader line is "
        "outside the band when its ratio against the reader's own reading, or its confidence, "
        "falls outside.",
        "",
        "| group | lines | ratio p2.5 / median / p97.5 | conf p2.5 / median | outside | share "
        "| by |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for g, v in sc["by_group"].items():
        by = ", ".join(f"{k} {_n(n)}" for k, n in v["outside_by"].items())
        L.append(
            f"| {g} | {_n(v['n'])} | {_f(v['ratio_p2_5'])} / {_f(v['ratio_median'])} / "
            f"{_f(v['ratio_p97_5'])} | {_f(v['conf_p2_5'], 3)} / {_f(v['conf_median'], 3)} | "
            f"{_n(v['outside'])} | {_pct(v['outside_share'])} | {by} |"
        )
    v1 = sc["v1_rows"]
    L += [
        "",
        f"The v1-minted rows of the same records, for comparison: {_n(v1['outside'])} of "
        f"{_n(v1['n'])} outside ({_pct(v1['outside_share'])}).",
        "",
        f"**Stop rule:** more than {_pct(sc['stop_share'], 0)} of the Leibniz-hand lines outside "
        f"stops the phase at Checkpoint A — **{'STOP' if sc['stop'] else 'not triggered'}**.",
        "",
        "The twenty worst reader lines (farthest outside the ratio band, then the lowest "
        "confidence):",
        "",
        "| ref | group | record | stratum | ratio | conf | why | minted / reading chars |",
        "|---|---|---|---|---:|---:|---|---:|",
    ]
    for w in sc["worst"]:
        L.append(
            f"| `{w['ref']}` | {w['group']} | {w['record_id']} | {w['stratum']} | "
            f"{_f(w['ratio'], 3)} | {_f(w['conf'], 3)} | {', '.join(w['why'])} | "
            f"{w['n_chars']} / {w['machine_chars']} |"
        )
    k = s["kept"]
    L += [
        "",
        "## The split",
        "",
        f"Kept: **{_n(k['lines'])} lines** on {_n(k['records'])} records, {_n(k['pages'])} pages, "
        f"{_n(k['units'])} units (records joined over shared pages), {_n(k['chars'])} characters. "
        + (
            "The validation pieces were read from the frozen file "
            f"`{s['draw'].get('frozen_from')}`."
            if s["val_frozen"]
            else f"The validation set was drawn with seed {s['draw']['seed']} at "
            f"{_pct(s['draw']['share'], 0)} of the lines per (stratum, hand group) cell."
        ),
        f" Pages on both sides: **{s['pages_shared_between_splits']}**.",
        "",
        "| split | lines | records | pages | units | characters |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for sp, v in s["splits"].items():
        L.append(
            f"| {sp} | {_n(v['lines'])} | {_n(v['records'])} | {_n(v['pages'])} | "
            f"{_n(v['units'])} | {_n(v['chars'])} |"
        )
    L += [
        "",
        "By stratum and hand group (train / val lines, the validation share):",
        "",
        "| cell | train | val | val share |",
        "|---|---:|---:|---:|",
    ]
    cells = sorted(set(s["splits"]["train"]["by_cell"]) | set(s["splits"]["val"]["by_cell"]))
    for c in cells:
        t = s["splits"]["train"]["by_cell"].get(c, {}).get("lines", 0)
        v = s["splits"]["val"]["by_cell"].get(c, {}).get("lines", 0)
        L.append(f"| {c} | {_n(t)} | {_n(v)} | {_pct(v / (t + v) if t + v else None)} |")
    L += ["", "By reader (train / val):", "", "| reader | train | val |", "|---|---:|---:|"]
    readers = sorted(set(s["splits"]["train"]["by_reader"]) | set(s["splits"]["val"]["by_reader"]))
    for r in readers:
        t = s["splits"]["train"]["by_reader"].get(r, {}).get("lines", 0)
        v = s["splits"]["val"]["by_reader"].get(r, {}).get("lines", 0)
        L.append(f"| {r} | {_n(t)} | {_n(v)} |")
    if s["draw"].get("cells"):
        L += [
            "",
            "The draw, cell by cell:",
            "",
            "| cell | lines | units | quota | val units | val lines | note |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for c, v in s["draw"]["cells"].items():
            L.append(
                f"| {c} | {_n(v['lines'])} | {_n(v['units'])} | {_n(v['quota'])} | "
                f"{_n(v['val_units'])} | {_n(v['val_lines_of_cell_units'])} | {v['note']} |"
            )
    est = s.get("estimate")
    if est:
        L += [
            "",
            "## Disk, from the sample",
            "",
            f"{_n(est['cut'])} of {_n(est['sampled'])} sampled lines cut: {_gb(est['bytes'])}, "
            f"**{_f((est['bytes_per_line'] or 0) / 1024, 1)} KB a line**; projected for "
            f"{_n(est['kept_lines'])} kept lines: **{_gb(est['projected_bytes'])}**.",
        ]
    cr = s.get("crops")
    if cr:
        L += [
            "",
            "## The crops",
            "",
            f"{_n(cr['pages'])} pages cut; by status: "
            + ", ".join(f"{k} {_n(v)}" for k, v in cr["by_status"].items())
            + f"; {_gb(cr['bytes'])} on disk (the PNGs; the sidecars beside them).",
        ]
    L += [
        "",
        "## What this is, and is not",
        "",
        "- The text is the edition's reading text as the factory minted it (NFC; the scribe's "
        "line-end mark kept as `¬` since C2b): abbreviations expanded, u/v and i/j as the edition "
        "prints them. A model trained on it learns the edition's conventions, not a diplomatic "
        "transcription (the C3 prompt's normalization tax).",
        "- The precision of the reader-placed lines is unmeasured: K2's audit sheet awaits its "
        "judge. The screen above is a length-and-confidence check, not a reading.",
        "- The validation set chooses checkpoints; it is drawn from the same mint, so it shares "
        "the mint's biases. The honest German error rate is the letter pool's (K2b), never "
        "trained on.",
        "",
    ]
    return "\n".join(L)


def write_outputs(
    ts: TrainSet,
    *,
    out_root: Path | str = DEFAULT_OUT,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
    val_pieces: Path | str | None = None,
) -> dict[str, Path]:
    """The manifest and split lists under the output root; the report, its JSON and the
    frozen validation pieces under the reports directory."""
    paths = write_manifest(ts, out_root)
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    summary = summarize(ts)
    paths["report"] = reports / f"{ts.name}-trainset.md"
    paths["report"].write_text(render_report(summary), encoding="utf-8")
    paths["json"] = reports / f"{ts.name}-trainset.json"
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    vp = Path(val_pieces) if val_pieces else reports / f"{ts.name}-val-pieces.csv"
    if not ts.val_frozen:
        paths["val_pieces"] = write_val_pieces(vp, ts.lines)
    else:
        paths["val_pieces"] = vp
    return paths


__all__ = [
    "BAND",
    "DEFAULT_AUDITS",
    "DEFAULT_FLAGS",
    "DEFAULT_HELDOUT",
    "DEFAULT_IMAGES_ROOT",
    "DEFAULT_NAME",
    "DEFAULT_OUT",
    "DEFAULT_POOL",
    "DEFAULT_READINGS",
    "DEFAULT_RECORDS",
    "DEFAULT_REPORTS_DIR",
    "EXCLUSIONS",
    "GROUPS",
    "SEED",
    "SPLITS",
    "STOP_SHARE",
    "VAL_SHARE",
    "Band",
    "TrainLine",
    "TrainSet",
    "apply_split",
    "band_of",
    "build",
    "crop_jobs",
    "crop_relpath",
    "cut_crops",
    "draw_validation",
    "estimate_disk",
    "flag_lines",
    "load_flags",
    "load_readings_text",
    "load_rows",
    "outside",
    "pages_from_csv",
    "read_manifest",
    "read_record_ids",
    "read_val_pieces",
    "reference_band",
    "refs_from_csvs",
    "render_report",
    "screen",
    "summarize",
    "units_of",
    "v1_texts",
    "write_manifest",
    "write_outputs",
    "write_val_pieces",
]
