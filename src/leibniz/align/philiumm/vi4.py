"""Cross-compare A VI,4 with PHILIUMM's noisy training split (P1 Task 2).

PHILIUMM's dataset ``DenisaBumba/htr_leibniz_dataset_v1`` (Hugging Face,
CC BY 4.0 as obtained) carries 735 ``train/noisy`` pages whose PAGE XML lines
hold edition text aligned from A VI,4 by their Passim pipeline (blank where
nothing aligned), 248 ``train/clean`` hand-corrected pages and 27 ``val``
pages. This project minted ground truth for the same manuscripts from the
same edition with its own aligner (C2). Four steps, one CLI:

* **fetch** — the noisy split's XML files, cache-first, at most one request a
  second, and the Hub's file listing (which names all 1,010 pages).
* **match** — a file name is a shelfmark plus a folio: ``LH_1_12_2_0124r`` is
  LH 1, 12, 2 Bl. 124r; ``LH_1_20_0063r-0062v`` an opening that shows 63r and
  62v. The shelfmark finds the work through ``works.shelfmarks`` (the store
  spells them ``LH 1, 3, 7 A`` and ``LH 1, 3, 7a``, both tried), the folio
  finds the page through ``pages.label`` (the C2 resolver's index). Their lines
  meet this project's by geometry: their ``Coords`` are scaled from their image
  size to the page's, and lines are paired greedily, one to one, by the
  intersection over union of their bounding boxes. An opening is laid out as
  two canvases side by side, scaled to a common height, in whichever order
  pairs more area, or as one canvas when the store holds the sheet scan once.
* **compare** — on every paired line, their aligned text against this
  project's minted text, the HTR reading as a third witness, under this
  project's fold: agree (≥ 0.9), near (0.7–0.9), disagree (< 0.7), this
  project only, theirs only, neither; per stratum, per file, by zone.
* **sheet** — the disagreements as a hand-audit sheet through the C2 crop
  machinery, with both texts shown, downloading verdicts in the C2 CSV shape.

Agreement between two aligners fed the same edition text is not correctness:
both can share the edition's reading and both can share a mistake; the sheet
is where a person decides.
"""

from __future__ import annotations

import csv
import json
import random
import re
import sqlite3
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align import dp
from leibniz.align.audit import AuditLine, lines_for_refs, write_sheet
from leibniz.align.normalize import normalize
from leibniz.align.pagexml import PageDocument, PageLine, parse_page_xml
from leibniz.align.resolve import build_folio_index, parse_folio_label
from leibniz.catalog.shelfmarks import signature_keys
from leibniz.net import PoliteClient, default_user_agent

HF_DATASET = "DenisaBumba/htr_leibniz_dataset_v1"
HF_API = f"https://huggingface.co/api/datasets/{HF_DATASET}"
SPLITS = {"noisy": "train/noisy/", "clean": "train/clean/", "val": "val/"}
LISTING_NAME = "hf-files.json"
MATCH_NAME = "vi4-match.json"
AGREE_SIM = 0.9
NEAR_SIM = 0.7
IOU_DEFAULT = 0.5
IOU_SENSITIVITY = (0.3, 0.5, 0.7)
BUCKETS = ("agree", "near", "disagree", "ours_only", "theirs_only", "neither")

# --------------------------------------------------------------------------- #
# Listing and fetch
# --------------------------------------------------------------------------- #


def hf_file_url(path: str, *, revision: str = "main") -> str:
    return f"https://huggingface.co/datasets/{HF_DATASET}/resolve/{revision}/{path}"


def fetch_listing(dest: Path, *, client: PoliteClient | None = None) -> dict:
    """The Hub's file listing (``siblings``) and revision, cached as ``hf-files.json``."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / LISTING_NAME
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    own = client is None
    client = client or PoliteClient(user_agent=default_user_agent())
    try:
        meta = client.get_json(HF_API)
    finally:
        if own:
            client.close()
    listing = {
        "dataset": HF_DATASET,
        "sha": meta.get("sha"),
        "lastModified": meta.get("lastModified"),
        "license": (meta.get("cardData") or {}).get("license"),
        "files": sorted(s["rfilename"] for s in meta.get("siblings", [])),
    }
    path.write_text(json.dumps(listing, indent=1) + "\n", encoding="utf-8")
    return listing


def split_files(listing: dict, split: str, *, suffix: str = ".xml") -> list[str]:
    prefix = SPLITS[split]
    return [f for f in listing["files"] if f.startswith(prefix) and f.endswith(suffix)]


def fetch_noisy(
    dest: Path,
    *,
    client: PoliteClient | None = None,
    listing: dict | None = None,
    progress: Callable[[int, int, str], None] | None = None,
    limit: int | None = None,
) -> tuple[int, int]:
    """Download ``train/noisy/*.xml`` into ``dest/noisy/`` (skip what is there).

    Returns ``(fetched, present)``. Resumable: a run that stops leaves the files
    it got, the next run fetches the rest.
    """
    dest = Path(dest)
    listing = listing or fetch_listing(dest, client=client)
    files = split_files(listing, "noisy")
    if limit is not None:
        files = files[:limit]
    out_dir = dest / "noisy"
    out_dir.mkdir(parents=True, exist_ok=True)
    missing = [f for f in files if not (out_dir / Path(f).name).exists()]
    own = client is None
    client = client or PoliteClient(user_agent=default_user_agent())
    fetched = 0
    try:
        for k, rel in enumerate(missing, start=1):
            if progress:
                progress(k, len(missing), rel)
            data = client.get_bytes(hf_file_url(rel, revision=listing.get("sha") or "main"))
            (out_dir / Path(rel).name).write_bytes(data)
            fetched += 1
    finally:
        if own:
            client.close()
    return fetched, len(files) - len(missing) + fetched


# --------------------------------------------------------------------------- #
# File names → shelfmark + folios
# --------------------------------------------------------------------------- #

_NAME_RE = re.compile(
    r"^(?P<family>LH|LBr)_(?P<rest>.+?)_(?P<f1>\d{4})(?P<s1>[rv])?(?:-(?P<f2>\d{4})(?P<s2>[rv])?)?$"
)


@dataclass(slots=True)
class FileName:
    """A dataset file name read as shelfmark + folio(s)."""

    name: str  # without the extension
    split: str
    family: str | None = None
    tokens: tuple[str, ...] = ()
    folios: list[tuple[int, str]] = field(default_factory=list)  # (number, side or "")
    note: str = ""

    @property
    def parsed(self) -> bool:
        return self.family is not None and bool(self.folios)

    @property
    def is_opening(self) -> bool:
        return len(self.folios) == 2

    def candidate_keys(self) -> list[str]:
        """Match keys to try against ``signature_keys(work.shelfmarks)``:
        the tokens as written, letter parts joined to the number before them
        (``7, A`` → ``7a``) and letter parts split off (``7B`` → ``7, b``)."""
        if self.family is None:
            return []
        toks = [t.lower() for t in self.tokens]
        keys: list[str] = [f"{self.family} {','.join(toks)}"]
        joined: list[str] = []
        for t in toks:
            if joined and re.fullmatch(r"[a-z]", t) and re.fullmatch(r"\d+", joined[-1]):
                joined[-1] = joined[-1] + t
            else:
                joined.append(t)
        keys.append(f"{self.family} {','.join(joined)}")
        split: list[str] = []
        for t in toks:
            m = re.fullmatch(r"(\d+)([a-z])", t)
            if m:
                split.extend([m.group(1), m.group(2)])
            else:
                split.append(t)
        keys.append(f"{self.family} {','.join(split)}")
        out: list[str] = []
        for k in keys:
            if k not in out:
                out.append(k)
        return out


def parse_name(name: str, split: str = "noisy") -> FileName:
    stem = name.rsplit("/", 1)[-1]
    stem = stem[:-4] if stem.endswith(".xml") else stem
    m = _NAME_RE.match(stem)
    if m is None:
        return FileName(stem, split, note="name is not <shelfmark>_<folio>")
    folios = [(int(m.group("f1")), m.group("s1") or "")]
    if m.group("f2"):
        folios.append((int(m.group("f2")), m.group("s2") or ""))
    note = "" if all(s for _, s in folios) else "a folio without a side letter"
    return FileName(stem, split, m.group("family"), tuple(m.group("rest").split("_")), folios, note)


def work_index(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """``signature key -> work ids`` over every work's shelfmarks."""
    out: dict[str, list[str]] = {}
    for w in db.iter_works(conn):
        for key in signature_keys(w.shelfmarks):
            out.setdefault(key, []).append(w.gwlb_object_id)
    return out


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #

Box = tuple[float, float, float, float]


def bbox(points: Sequence) -> Box | None:
    pts = [(float(p[0]), float(p[1])) for p in (points or []) if len(p) >= 2]
    if len(pts) < 2:
        return None
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs), min(ys), max(xs), max(ys)


def iou(a: Box, b: Box) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    area = lambda r: max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])  # noqa: E731
    union = area(a) + area(b) - inter
    return inter / union if union > 0 else 0.0


@dataclass(slots=True)
class Placement:
    """Where one of this project's pages sits inside their image."""

    page_id: str
    x0: float  # left edge in their image's pixels
    x1: float
    scale: float  # their pixels → page pixels (same in x and y)


def placements_for(
    their_w: int, their_h: int, pages: Sequence[db.Page], *, order: Sequence[int]
) -> list[Placement] | None:
    """Lay the pages side by side in ``order``, scaled to their image's height;
    ``None`` when the widths do not add up (within 15 %)."""
    if not pages or not their_w or not their_h:
        return None
    chosen = [pages[i] for i in order]
    if any(not p.width or not p.height for p in chosen):
        return None
    out: list[Placement] = []
    x = 0.0
    for p in chosen:
        s = p.height / their_h  # page px per their px
        w_theirs = p.width / s
        out.append(Placement(p.id, x, x + w_theirs, s))
        x += w_theirs
    if abs(x - their_w) > 0.15 * their_w:
        return None
    return out


def project(box: Box, pl: Placement) -> Box:
    """A box in their image's pixels → the placed page's pixels."""
    return (
        (box[0] - pl.x0) * pl.scale,
        box[1] * pl.scale,
        (box[2] - pl.x0) * pl.scale,
        box[3] * pl.scale,
    )


@dataclass(slots=True)
class LinePair:
    their_id: str
    their_index: int
    zone: str | None
    page_id: str
    line_seq: int
    iou: float

    @property
    def ref(self) -> str:
        return f"{self.page_id}:{self.line_seq:03d}"


def recognised_lines(conn: sqlite3.Connection, page_id: str) -> dict[int, tuple[list, str | None]]:
    """``line_seq -> (polygon, text)`` from the run that produced the recognised
    text (the row ``audit.line_geometry`` takes), else the latest geometry."""
    best: dict[int, tuple[int, list, str | None]] = {}
    for row in conn.execute(
        "SELECT line_seq, run_id, polygon, text FROM lines WHERE page_id = ?", (page_id,)
    ):
        seq = row["line_seq"]
        rank = (1 if row["text"] is not None else 0, row["run_id"] or 0)
        cur = best.get(seq)
        if cur is None or rank > cur[0]:
            best[seq] = (rank, json.loads(row["polygon"]) if row["polygon"] else [], row["text"])
    return {k: (v[1], v[2]) for k, v in best.items()}


def pair_lines(
    their_lines: Sequence[PageLine],
    placements: Sequence[Placement],
    ours: dict[str, dict[int, tuple[list, str | None]]],
    *,
    threshold: float = IOU_DEFAULT,
) -> list[LinePair]:
    """Greedy one-to-one pairing by bounding-box IoU above ``threshold``."""
    cands: list[tuple[float, int, str, int]] = []
    for ln in their_lines:
        tb = bbox(ln.coords)
        if tb is None:
            continue
        cx = (tb[0] + tb[2]) / 2
        pl = next((p for p in placements if p.x0 <= cx < p.x1), None)
        if pl is None:
            pl = placements[-1] if cx >= placements[-1].x1 else placements[0]
        pb = project(tb, pl)
        for seq, (poly, _text) in ours.get(pl.page_id, {}).items():
            ob = bbox(poly)
            if ob is None:
                continue
            v = iou(pb, ob)
            if v >= threshold:
                cands.append((v, ln.index, pl.page_id, seq))
    cands.sort(key=lambda c: (-c[0], c[1], c[3]))
    used_theirs: set[int] = set()
    used_ours: set[tuple[str, int]] = set()
    by_index = {ln.index: ln for ln in their_lines}
    out: list[LinePair] = []
    for v, idx, page_id, seq in cands:
        if idx in used_theirs or (page_id, seq) in used_ours:
            continue
        used_theirs.add(idx)
        used_ours.add((page_id, seq))
        ln = by_index[idx]
        out.append(LinePair(ln.id, idx, ln.region_type, page_id, seq, round(v, 4)))
    out.sort(key=lambda p: p.their_index)
    return out


# --------------------------------------------------------------------------- #
# match
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class FileMatch:
    name: str
    split: str
    # matched | resolved (pages found, no XML needed: clean and val) | unparsed | no_work |
    # ambiguous_work | no_page | no_layout | no_xml (a noisy file whose XML is not fetched)
    status: str
    work_ids: list[str] = field(default_factory=list)
    page_ids: list[str] = field(default_factory=list)
    layout: str = ""  # "single", "two canvases (A|B)", "one scan"
    notes: list[str] = field(default_factory=list)
    their_lines: int = 0
    our_lines: int = 0
    pairs: list[LinePair] = field(default_factory=list)
    pairs_at: dict[str, int] = field(default_factory=dict)  # IoU threshold -> pairs


def resolve_pages(conn: sqlite3.Connection, fn: FileName, index: dict[str, list[str]]) -> FileMatch:
    """Work and pages for a file name, with every reason a step can fail."""
    fm = FileMatch(fn.name, fn.split, "matched")
    if not fn.parsed:
        fm.status = "unparsed"
        fm.notes.append(fn.note)
        return fm
    works: list[str] = []
    for key in fn.candidate_keys():
        for w in index.get(key, []):
            if w not in works:
                works.append(w)
    if not works:
        fm.status = "no_work"
        fm.notes.append(f"no work has a shelfmark key in {fn.candidate_keys()}")
        return fm
    if len(works) > 1:
        fm.status = "ambiguous_work"
        fm.notes.append(f"{len(works)} works share the key; each is tried for the folio")
    fm.work_ids = works
    indexes = {w: build_folio_index(conn, w) for w in works}
    for num, side in fn.folios:
        found: list[db.Page] = []
        for w in works:
            pages = indexes[w].get(num, [])
            if side:
                pages = [p for p in pages if _side(p.label) == side] or pages
            if pages:
                found = pages
                break
        if not found:
            fm.notes.append(
                f"no page labelled {num}{side}; " + _folio_coverage(conn, works, indexes)
            )
            continue
        if len(found) > 1:
            fm.notes.append(f"{len(found)} pages labelled {num}{side}; the first taken")
        fm.page_ids.append(found[0].id)
    if not fm.page_ids:
        fm.status = "no_page"
    return fm


def _side(label: str | None) -> str:
    ref = parse_folio_label(label)
    return ref.side if ref else ""


def _folio_coverage(
    conn: sqlite3.Connection, works: Sequence[str], indexes: dict[str, dict[int, list[db.Page]]]
) -> str:
    """What folios the candidate works do carry, for the report's unresolved list."""
    parts: list[str] = []
    for w in works:
        idx = indexes[w]
        n_pages = len(db.get_pages(conn, w))
        labelled = sum(len(v) for v in idx.values())
        if idx:
            parts.append(f"{w} has folios {min(idx)}–{max(idx)} on {labelled} of {n_pages} pages")
        else:
            parts.append(f"{w} has no folio labels on its {n_pages} pages")
    return "; ".join(parts)


def minted_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """``page_id -> open-bucket minted lines`` over the whole store, in one pass."""
    out: dict[str, int] = {}
    for row in conn.execute("SELECT line_image_ref FROM gt_lines WHERE license_bucket = 'open'"):
        page_id = row[0].rpartition(":")[0]
        out[page_id] = out.get(page_id, 0) + 1
    return out


def match_file(
    conn: sqlite3.Connection,
    fn: FileName,
    doc: PageDocument | None,
    index: dict[str, list[str]],
    *,
    threshold: float = IOU_DEFAULT,
    minted: dict[str, int] | None = None,
) -> FileMatch:
    fm = resolve_pages(conn, fn, index)
    if fm.status in ("unparsed", "no_work", "no_page"):
        return fm
    if doc is None:
        fm.status = "no_xml" if fn.split == "noisy" else "resolved"
        return fm
    fm.their_lines = len(doc.lines)
    pages = [p for pid in fm.page_ids if (p := db.get_page(conn, pid)) is not None]
    ours = {p.id: recognised_lines(conn, p.id) for p in pages}
    fm.our_lines = sum(len(v) for v in ours.values())
    their_w, their_h = doc.width or 0, doc.height or 0
    candidates: list[tuple[str, list[Placement]]] = []
    if len(pages) == 2 and (_same_scan(pages[0], pages[1]) or _same_size(pages[0], pages[1])):
        # The store registers the sheet scan once per folio label (Open Q #19): their
        # opening is that scan, so one page carries every line of both folios. The C2
        # factory saw the twin registrations as duplicate lines and minted each passage
        # on one of them: take the registration that carries the minted lines (ties:
        # the lower canvas sequence), or the comparison counts its empty twin.
        counts = {p.id: (minted or {}).get(p.id, 0) for p in pages}
        pick = max(pages, key=lambda p: (counts[p.id], -p.seq))
        pl = placements_for(their_w, their_h, [pick], order=[0])
        if pl:
            candidates.append(("one scan (registered under both labels)", pl))
            fm.notes.append(
                "both folio labels point at the same scan; "
                + ", ".join(f"{p.id} carries {counts[p.id]} minted lines" for p in pages)
                + f"; {pick.id} taken"
            )
    if len(pages) == 2 and not candidates:
        for order, label in (
            ([0, 1], "two canvases (first|second)"),
            ([1, 0], "two canvases (second|first)"),
        ):
            pl = placements_for(their_w, their_h, pages, order=order)
            if pl:
                candidates.append((label, pl))
        if not candidates:
            # one of the two canvases alone may be what they segmented
            for i, p in enumerate(pages):
                pl = placements_for(their_w, their_h, [p], order=[0])
                if pl:
                    candidates.append(
                        (f"single ({'first' if i == 0 else 'second'} folio only)", pl)
                    )
    elif len(pages) == 1:
        pl = placements_for(their_w, their_h, pages, order=[0])
        if pl:
            candidates.append(("single", pl))
        else:
            # the page may be one half of their opening: try it on either side
            p = pages[0]
            if p.width and p.height and their_h:
                s = p.height / their_h
                w = p.width / s
                candidates.append(("left half", [Placement(p.id, 0.0, w, s)]))
                candidates.append(("right half", [Placement(p.id, their_w - w, their_w, s)]))
    if not candidates:
        fm.status = "no_layout"
        fm.notes.append(f"their image {their_w}×{their_h} fits no arrangement of the pages")
        return fm
    best: tuple[float, str, list[LinePair]] | None = None
    for label, pl in candidates:
        pairs = pair_lines(doc.lines, pl, ours, threshold=threshold)
        score = sum(p.iou for p in pairs)
        if best is None or score > best[0]:
            best = (score, label, pairs)
        fm.pairs_at[label] = len(pairs)
    assert best is not None
    fm.layout, fm.pairs = best[1], best[2]
    fm.status = "matched"  # a shared key is a note, not a failure, once lines are paired
    chosen = next(pl for label, pl in candidates if label == best[1])
    for t in IOU_SENSITIVITY:
        fm.pairs_at[f"iou≥{t}"] = len(pair_lines(doc.lines, chosen, ours, threshold=t))
    return fm


def _same_scan(a: db.Page, b: db.Page) -> bool:
    if a.sha256 and b.sha256:
        return a.sha256 == b.sha256
    return bool(a.local_path) and a.local_path == b.local_path


def _same_size(a: db.Page, b: db.Page) -> bool:
    return bool(a.width and a.height) and (a.width, a.height) == (b.width, b.height)


def run_match(
    conn: sqlite3.Connection,
    dest: Path,
    *,
    threshold: float = IOU_DEFAULT,
    progress: Callable[[int, int, str], None] | None = None,
) -> list[FileMatch]:
    """Match every file of every split (the noisy XML read when present)."""
    listing = json.loads((Path(dest) / LISTING_NAME).read_text(encoding="utf-8"))
    index = work_index(conn)
    minted = minted_counts(conn)
    out: list[FileMatch] = []
    todo: list[tuple[str, str]] = []
    for split in ("noisy", "clean", "val"):
        todo.extend((split, f) for f in split_files(listing, split))
    for k, (split, rel) in enumerate(todo, start=1):
        if progress:
            progress(k, len(todo), rel)
        fn = parse_name(rel, split)
        doc = None
        if split == "noisy":
            xml = Path(dest) / "noisy" / Path(rel).name
            if xml.exists():
                doc = parse_page_xml(xml)
        out.append(match_file(conn, fn, doc, index, threshold=threshold, minted=minted))
    return out


def write_match(matches: Sequence[FileMatch], path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "name": m.name,
            "split": m.split,
            "status": m.status,
            "work_ids": m.work_ids,
            "page_ids": m.page_ids,
            "layout": m.layout,
            "notes": m.notes,
            "their_lines": m.their_lines,
            "our_lines": m.our_lines,
            "pairs_at": m.pairs_at,
            "pairs": [
                [p.their_id, p.their_index, p.zone, p.page_id, p.line_seq, p.iou] for p in m.pairs
            ],
        }
        for m in matches
    ]
    Path(path).write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def read_match(path: Path) -> list[FileMatch]:
    out: list[FileMatch] = []
    for d in json.loads(Path(path).read_text(encoding="utf-8")):
        out.append(
            FileMatch(
                d["name"],
                d["split"],
                d["status"],
                d["work_ids"],
                d["page_ids"],
                d["layout"],
                d["notes"],
                d["their_lines"],
                d["our_lines"],
                [LinePair(*p) for p in d["pairs"]],
                d["pairs_at"],
            )
        )
    return out


def match_summary(matches: Sequence[FileMatch]) -> dict:
    by_status: dict[str, dict[str, int]] = {}
    for m in matches:
        by_status.setdefault(m.split, {})
        by_status[m.split][m.status] = by_status[m.split].get(m.status, 0) + 1
    noisy = [m for m in matches if m.split == "noisy" and m.status == "matched"]
    layouts: dict[str, int] = {}
    for m in noisy:
        layouts[m.layout] = layouts.get(m.layout, 0) + 1
    sens = {f"iou≥{t}": sum(m.pairs_at.get(f"iou≥{t}", 0) for m in noisy) for t in IOU_SENSITIVITY}
    return {
        "files": len(matches),
        "by_split_status": by_status,
        "resolved": sum(
            1 for m in matches if m.status in ("matched", "resolved", "ambiguous_work")
        ),
        "noisy_matched": len(noisy),
        "their_lines": sum(m.their_lines for m in noisy),
        "our_lines": sum(m.our_lines for m in noisy),
        "pairs": sum(len(m.pairs) for m in noisy),
        "pairs_by_iou": sens,
        "layouts": layouts,
        # every page heldout_pages.csv lists, all three splits: before 2026-10 this
        # was the matched noisy files' pages alone (1,149), while the CSV — the file
        # C3 reads — holds 1,472, the clean and val pages PHILIUMM trained and
        # validated on among them
        "pages": heldout_page_ids(matches),
        "pages_by_split": {
            split: len({pid for m in matches if m.split == split for pid in m.page_ids})
            for split in sorted({m.split for m in matches})
        },
        "unresolved": [
            {"name": m.name, "split": m.split, "status": m.status, "notes": m.notes}
            for m in matches
            if m.status not in ("matched", "resolved", "ambiguous_work")
        ],
    }


def heldout_page_ids(matches: Sequence[FileMatch]) -> list[str]:
    """The distinct pages :func:`write_heldout` lists: every page any file of any
    split resolved to, sorted — what C3 must keep out of its evaluation set."""
    return sorted({pid for m in matches for pid in m.page_ids})


def write_heldout(matches: Sequence[FileMatch], path: Path) -> int:
    """``reports/philiumm/heldout_pages.csv``: this project's page ids for every
    file of every split that resolved — the pages C3 must keep out of its
    evaluation set — one row per (file, page)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["page_id", "work_id", "file", "split", "status"])
        for m in matches:
            for pid in m.page_ids:
                w.writerow([pid, pid.rpartition(":")[0], m.name, m.split, m.status])
                n += 1
    return n


# --------------------------------------------------------------------------- #
# compare
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Judged:
    file: str
    ref: str
    their_id: str
    zone: str | None
    iou: float
    stratum: str  # the minted line's stratum, or "unminted"
    htr: str
    ours: str
    theirs: str
    bucket: str
    sim: float | None  # folded, ours vs theirs
    sim_htr_ours: float | None
    sim_htr_theirs: float | None
    align_conf: float | None


def _fsim(a: str, b: str) -> float:
    fa, fb = normalize(a), normalize(b)
    if not fa and not fb:
        return 1.0
    if not fa or not fb:
        return 0.0
    return dp.similarity(fa, fb)


def judge(conn: sqlite3.Connection, matches: Sequence[FileMatch], dest: Path) -> list[Judged]:
    """Every paired line of the noisy split, bucketed."""
    out: list[Judged] = []
    for m in matches:
        if m.split != "noisy" or m.status != "matched" or not m.pairs:
            continue
        xml = Path(dest) / "noisy" / f"{m.name}.xml"
        if not xml.exists():
            continue
        doc = parse_page_xml(xml)
        theirs_by = {ln.id: ln for ln in doc.lines}
        ours_by_page = {pid: recognised_lines(conn, pid) for pid in m.page_ids}
        minted = _minted_for_pages(conn, m.page_ids)
        for p in m.pairs:
            t = theirs_by.get(p.their_id)
            their_text = (t.text if t is not None else "").strip()
            _poly, htr = ours_by_page.get(p.page_id, {}).get(p.line_seq, ([], None))
            row = minted.get(p.ref)
            our_text = (row[0] if row else "").strip()
            stratum = row[1] if row else "unminted"
            conf = row[2] if row else None
            sim = None
            if our_text and their_text:
                sim = _fsim(our_text, their_text)
                bucket = (
                    "agree" if sim >= AGREE_SIM else ("near" if sim >= NEAR_SIM else "disagree")
                )
            elif our_text:
                bucket = "ours_only"
            elif their_text:
                bucket = "theirs_only"
            else:
                bucket = "neither"
            out.append(
                Judged(
                    m.name,
                    p.ref,
                    p.their_id,
                    p.zone,
                    p.iou,
                    stratum,
                    htr or "",
                    our_text,
                    their_text,
                    bucket,
                    sim,
                    _fsim(htr or "", our_text) if our_text and htr else None,
                    _fsim(htr or "", their_text) if their_text and htr else None,
                    conf,
                )
            )
    return out


def _minted_for_pages(
    conn: sqlite3.Connection, page_ids: Iterable[str]
) -> dict[str, tuple[str, str, float | None]]:
    out: dict[str, tuple[str, str, float | None]] = {}
    for pid in page_ids:
        for row in conn.execute(
            "SELECT line_image_ref, text, stratum, align_conf FROM gt_lines "
            "WHERE license_bucket = 'open' AND line_image_ref LIKE ? ORDER BY id",
            (f"{pid}:%",),
        ):
            out[row["line_image_ref"]] = (
                row["text"],
                row["stratum"] or "unknown",
                row["align_conf"],
            )
    return out


def tally(rows: Sequence[Judged], key: Callable[[Judged], str]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        k = key(r)
        out.setdefault(k, {b: 0 for b in BUCKETS})[r.bucket] += 1
    return out


def witness(rows: Sequence[Judged], bucket: str = "disagree") -> tuple[int, int, int]:
    ours = theirs = tie = 0
    for r in rows:
        if r.bucket != bucket or r.sim_htr_ours is None or r.sim_htr_theirs is None:
            continue
        if abs(r.sim_htr_ours - r.sim_htr_theirs) < 1e-9:
            tie += 1
        elif r.sim_htr_ours > r.sim_htr_theirs:
            ours += 1
        else:
            theirs += 1
    return ours, theirs, tie


def coverage(rows: Sequence[Judged]) -> dict:
    """Files on which this project minted nothing at all, against files where it
    minted something: the share of *theirs only* that is coverage, not alignment."""
    by_file: dict[str, dict[str, int]] = tally(rows, lambda r: r.file)
    minted = {
        f: c["agree"] + c["near"] + c["disagree"] + c["ours_only"] for f, c in by_file.items()
    }
    none = sorted(f for f in by_file if minted[f] == 0)
    some = sorted(f for f in by_file if minted[f] > 0)
    prefix = lambda f: "_".join(f.split("_")[:3])  # noqa: E731  (LH_1_3 …)
    by_prefix: dict[str, dict[str, int]] = {}
    for f in by_file:
        d = by_prefix.setdefault(prefix(f), {"files": 0, "without_mint": 0})
        d["files"] += 1
        d["without_mint"] += int(minted[f] == 0)
    return {
        "files": len(by_file),
        "files_without_mint": len(none),
        "their_lines_on_files_without_mint": sum(
            by_file[f]["agree"]
            + by_file[f]["near"]
            + by_file[f]["disagree"]
            + by_file[f]["theirs_only"]
            for f in none
        ),
        "on_files_with_mint": {b: sum(by_file[f][b] for f in some) for b in BUCKETS},
        "by_shelfmark": dict(sorted(by_prefix.items())),
        "files_without_mint_list": none,
    }


def compare_summary(matches: Sequence[FileMatch], rows: Sequence[Judged]) -> dict:
    total = {b: sum(1 for r in rows if r.bucket == b) for b in BUCKETS}
    return {
        "coverage": coverage(rows),
        "match": match_summary(matches),
        "judged": len(rows),
        "total": total,
        "by_stratum": tally(rows, lambda r: r.stratum),
        "by_zone": tally(rows, lambda r: r.zone or "—"),
        "by_file": tally(rows, lambda r: r.file),
        "witness_disagree": dict(
            zip(("ours_closer", "theirs_closer", "tie"), witness(rows), strict=True)
        ),
        "witness_near": dict(
            zip(("ours_closer", "theirs_closer", "tie"), witness(rows, "near"), strict=True)
        ),
    }


def write_judged(rows: Sequence[Judged], path: Path, *, limit: int | None = None) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "file",
                "ref",
                "their_id",
                "zone",
                "iou",
                "stratum",
                "bucket",
                "sim",
                "sim_htr_ours",
                "sim_htr_theirs",
                "align_conf",
                "htr",
                "ours",
                "theirs",
            ]
        )
        for r in rows:
            if limit is not None and n >= limit:
                break
            w.writerow(
                [
                    r.file,
                    r.ref,
                    r.their_id,
                    r.zone or "",
                    f"{r.iou:.3f}",
                    r.stratum,
                    r.bucket,
                    "" if r.sim is None else f"{r.sim:.3f}",
                    "" if r.sim_htr_ours is None else f"{r.sim_htr_ours:.3f}",
                    "" if r.sim_htr_theirs is None else f"{r.sim_htr_theirs:.3f}",
                    "" if r.align_conf is None else f"{r.align_conf:.3f}",
                    r.htr,
                    r.ours,
                    r.theirs,
                ]
            )
            n += 1
    return n


def disagreement_sample(rows: Sequence[Judged], *, n: int = 500, seed: int = 0) -> list[Judged]:
    """A reproducible sample of the lines both aligned differently (``disagree``,
    then ``near``), spread over the files."""
    pool = [r for r in rows if r.bucket == "disagree"] + [r for r in rows if r.bucket == "near"]
    rng = random.Random(seed)
    rng.shuffle(pool)
    return sorted(pool[:n], key=lambda r: (r.file, r.ref))


def _pct(k: int, n: int) -> str:
    return "—" if not n else f"{100 * k / n:.1f} %"


def render(
    matches: Sequence[FileMatch], rows: Sequence[Judged], summ: dict, *, listing: dict
) -> str:
    ms = summ["match"]
    out: list[str] = []
    A = out.append
    A("# A VI,4 under two aligners: PHILIUMM's noisy split against this project's mint")
    A("")
    A(
        f"Their dataset `{HF_DATASET}` (Hugging Face, revision "
        f"`{(listing.get('sha') or '?')[:12]}`, licence as listed: "
        f"{listing.get('license') or '?'}): {len(split_files(listing, 'noisy'))} "
        f"noisy, {len(split_files(listing, 'clean'))} clean and {len(split_files(listing, 'val'))} "
        f"val PAGE XML files, named by shelfmark and folio. The noisy lines carry edition text "
        f"aligned from A VI,4 by their Passim pipeline (blank where nothing aligned); this "
        f"project's `gt_lines` carry the slices its own aligner minted from the same edition."
    )
    A("")
    A("## Matching their files to this project's pages")
    A("")
    A(
        "| split | files | matched (lines paired) | resolved (pages only) | ambiguous work | "
        "no work | no page | no layout | unparsed | no xml |"
    )
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for split in ("noisy", "clean", "val"):
        c = ms["by_split_status"].get(split, {})
        n = sum(c.values())
        A(
            f"| {split} | {n} | {c.get('matched', 0)} | {c.get('resolved', 0)} | "
            f"{c.get('ambiguous_work', 0)} | {c.get('no_work', 0)} | {c.get('no_page', 0)} | "
            f"{c.get('no_layout', 0)} | {c.get('unparsed', 0)} | {c.get('no_xml', 0)} |"
        )
    A("")
    A(
        f"{len(ms['pages'])} distinct pages of this project resolve from the three splits "
        f"(`heldout_pages.csv`; the clean and val files are resolved to pages only, their XML "
        f"is not needed). On the {ms['noisy_matched']} matched noisy files: "
        f"{ms['their_lines']:,} of their lines, {ms['our_lines']:,} of this project's (both "
        f"folio registrations of a sheet scan counted), "
        f"**{ms['pairs']:,} paired** by bounding-box IoU ≥ {IOU_DEFAULT} (at "
        + ", ".join(f"≥ {t}: {ms['pairs_by_iou'].get(f'iou≥{t}', 0):,}" for t in IOU_SENSITIVITY)
        + "). Layouts chosen: "
        + ", ".join(f"{k} {v}" for k, v in sorted(ms["layouts"].items()))
        + "."
    )
    if ms["unresolved"]:
        A("")
        A(f"{len(ms['unresolved'])} files did not resolve:")
        A("")
        for u in ms["unresolved"][:40]:
            A(
                f"- `{u['name']}` ({u['split']}): {u['status']}"
                + (f" — {'; '.join(u['notes'])}" if u["notes"] else "")
            )
        if len(ms["unresolved"]) > 40:
            A(f"- … and {len(ms['unresolved']) - 40} more (in `vi4-summary.json`)")
    A("")
    A("## The paired lines, judged")
    A("")
    A(
        f"For each paired line, their aligned text against this project's minted text under this "
        f"project's fold: *agree* ≥ {AGREE_SIM}, *near* {NEAR_SIM}–{AGREE_SIM}, "
        f"*disagree* < {NEAR_SIM}; "
        f"*ours only* (this project minted the line, theirs is blank), *theirs only*, *neither*."
    )
    A("")
    t = summ["total"]
    n = summ["judged"]
    A("| group | lines | " + " | ".join(BUCKETS) + " |")
    A("|---|---:|" + "---:|" * len(BUCKETS))
    A(f"| **all** | {n} | " + " | ".join(f"{t[b]} ({_pct(t[b], n)})" for b in BUCKETS) + " |")
    for title, table in (("stratum", summ["by_stratum"]), ("zone", summ["by_zone"])):
        for k in sorted(table):
            c = table[k]
            nn = sum(c.values())
            A(
                f"| {title}: {k} | {nn} | "
                + " | ".join(f"{c[b]} ({_pct(c[b], nn)})" for b in BUCKETS)
                + " |"
            )
    A("")
    w, wn = summ["witness_disagree"], summ["witness_near"]
    A(
        f"On the *disagree* lines the HTR reading of the strip is closer to this project's text on "
        f"{w['ours_closer']}, to theirs on {w['theirs_closer']}, equally close on {w['tie']}; "
        f"on the *near* lines {wn['ours_closer']} / {wn['theirs_closer']} / {wn['tie']}. The HTR "
        f"is a noisy "
        f"witness, not a judge."
    )
    A("")
    cov = summ.get("coverage")
    if cov:
        A("")
        A("## Coverage: pages where this project minted nothing")
        A("")
        A(
            f"On {cov['files_without_mint']} of the {cov['files']} judged files this project "
            f"minted no line at all; their text covers "
            f"{cov['their_lines_on_files_without_mint']:,} paired lines there, all counted "
            f"*theirs only* above. That part of the gap is coverage — a piece the "
            f"C2 factory did not localize, had no edition text for, or declined whole — not "
            f"alignment. On the files where it minted something: "
            + ", ".join(f"{b} {cov['on_files_with_mint'][b]:,}" for b in BUCKETS)
            + "."
        )
        A("")
        A("| shelfmark | files | without a minted line |")
        A("|---|---:|---:|")
        for k, d in cov["by_shelfmark"].items():
            A(
                f"| {k.replace('_', ' ', 1).replace('_', ', ')} | {d['files']} | "
                f"{d['without_mint']} |"
            )
    A("")
    A(
        "What agreement does not prove: both aligners were fed the same edition text, so a shared "
        "reading is the edition's, not the page's, and a shared mistake looks like agreement. "
        "A line both leave blank is not thereby wrong. The disagreements are the lines worth a "
        "person's look (`philiumm-disagreements.html`, verdicts in the C2 CSV shape)."
    )
    A("")
    A("## Per file")
    A("")
    A("| file | lines | " + " | ".join(BUCKETS) + " |")
    A("|---|---:|" + "---:|" * len(BUCKETS))
    for f in sorted(summ["by_file"]):
        c = summ["by_file"][f]
        nn = sum(c.values())
        A(f"| {f} | {nn} | " + " | ".join(str(c[b]) for b in BUCKETS) + " |")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# sheet
# --------------------------------------------------------------------------- #


def build_disagreement_sheet(
    conn: sqlite3.Connection,
    rows: Sequence[Judged],
    *,
    images_root: Path,
    out_dir: Path,
    n: int = 300,
    seed: int = 0,
) -> tuple[Path, int]:
    """The disagreements as a hand-audit sheet (crops from the image cache)."""
    sample = disagreement_sample(rows, n=n, seed=seed)
    lines: list[AuditLine] = lines_for_refs(conn, [r.ref for r in sample])
    by_ref = {r.ref: r for r in sample}
    for ln in lines:
        r = by_ref[ln.ref]
        ln.alt_text = r.theirs
        ln.alt_label = "PHILIUMM"
        if not ln.gt_text:
            ln.gt_text = r.ours
    sheet = write_sheet(
        conn,
        lines,
        images_root=images_root,
        out_dir=out_dir,
        html_name="philiumm-disagreements.html",
        csv_name="philiumm-disagreements-lines.csv",
        seed=seed,
        title="Where two aligners disagree — A VI,4",
    )
    return sheet.html_path, sheet.n_with_crops


__all__ = [
    "AGREE_SIM",
    "BUCKETS",
    "HF_DATASET",
    "IOU_DEFAULT",
    "IOU_SENSITIVITY",
    "NEAR_SIM",
    "FileMatch",
    "FileName",
    "Judged",
    "LinePair",
    "Placement",
    "bbox",
    "build_disagreement_sheet",
    "compare_summary",
    "coverage",
    "disagreement_sample",
    "fetch_listing",
    "fetch_noisy",
    "heldout_page_ids",
    "hf_file_url",
    "iou",
    "judge",
    "match_file",
    "match_summary",
    "minted_counts",
    "pair_lines",
    "parse_name",
    "placements_for",
    "read_match",
    "render",
    "resolve_pages",
    "run_match",
    "split_files",
    "witness",
    "work_index",
    "write_heldout",
    "write_judged",
    "write_match",
]
