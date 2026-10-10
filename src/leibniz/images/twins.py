"""Scans registered twice ("twins"), and the two-page spreads among them.

The GWLB photographs an unfolded sheet side by side — two folio pages in one
image — and registers that image under both folio labels: the outer side as
``1r`` and ``2v``, the inner side as ``1v`` and ``2r``. Each label gets its own
copy of the file, and the copies differ only in the caption the library stamps
in a corner ("Signatur: … - 2v"), so their checksums never agree while their
sizes almost do. The corpus run read every such image once per label: search
showed the same page twice, the exports doubled, and a spread was shown as one
folio.

A probe of 27 works (2026-10, LBr, LH and Marginalien, 25 groups checked byte
for byte) found the rule this module applies:

* **Candidates.** Same work, same width × height, file sizes within
  ``max(1 KB, 0.1 %)`` of each other (twins differed by at most 602 bytes,
  other pages of the same size by at least 15 KB), and one recto and one verso
  among them: every twin pair seen was one ``r`` and one ``v``. A third
  registration of the same scan joins a pair; groups beyond three are not
  formed.
* **Confirmation.** The twins were segmented separately but are one image, so
  their lines lie in the same places: at least half the lines of one must meet
  a line of the other at IoU ≥ 0.8 (twins measured 0.87–1.00, other pages
  0.00–0.11). A group none of whose members has lines to compare is left as it
  is — nothing is folded on the size of a file alone.
* **Spread or fold.** A confirmed pair of one recto and one verso in a
  landscape image is a spread: the verso is the left half, the recto the right
  (the catalogue's incipits sit on the right half of the outer sides, and no
  counterexample was found). The fold is the middle of the least-covered run
  of columns between 40 % and 60 % of the width, or the middle of the image
  where two or more lines cross that whole band; a line with at least 20 % of
  its width on each side crosses the fold — the segmenter merged two lines —
  and is shown on both halves and indexed once, on the recto. Where more than
  10 % of the lines cross, or the group is a triple, or the image is upright,
  the group is folded instead: one registration (the one with the most lines)
  carries the text, the others point to it.

The groups are found where the lines are read anyway — the index build
(:func:`leibniz.search.documents.iter_page_docs`) — and written beside the
store as a small JSON file (:class:`TwinIndex`) that the web application reads
at start. ``leibniz images twins`` writes the same file without an index build.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz import db

TWIN_BYTES = 1024  # file sizes within this many bytes …
TWIN_SHARE = 0.001  # … or this share of the larger, whichever is more
MAX_GROUP = 3  # registrations of one scan (1r/2v/3v was the most seen)
LINE_IOU = 0.8  # two boxes are the same line at this intersection over union
LINE_AGREEMENT = 0.5  # share of the fewer lines that must meet a line of the other
FOLD_BAND = (0.40, 0.60)  # where the fold of a spread is looked for, by width
CROSS_SIDE = 0.20  # a line with this share of its width on each side crosses the fold
MAX_CROSSING = 0.10  # more lines than this crossing the fold: fold the group, do not split
FORMAT_VERSION = 1

_SIDE = re.compile(r"(\d+)\s*([rv])\b", re.IGNORECASE)


def leaf_side(label: str | None) -> str | None:
    """``"r"`` or ``"v"`` for a folio label that names one side (``12r``, ``3 v``);
    ``None`` for anything else (``1r-2v``, a page number, no label)."""
    sides = {side.lower() for _, side in _SIDE.findall(label or "")}
    return sides.pop() if len(sides) == 1 else None


def _close(a: int, b: int) -> bool:
    return abs(a - b) <= max(TWIN_BYTES, TWIN_SHARE * max(a, b))


@dataclass(frozen=True, slots=True)
class Registration:
    """One page row as the twin rule reads it."""

    page_id: str
    work_id: str
    seq: int
    label: str | None
    width: int | None
    height: int | None
    n_bytes: int | None

    @classmethod
    def of(cls, page: db.Page) -> Registration:
        return cls(
            page.id, page.work_id, page.seq, page.label, page.width, page.height, page.n_bytes
        )


def candidate_groups(regs: Iterable[Registration]) -> list[tuple[Registration, ...]]:
    """Registrations that may be one scan: same work and size, file sizes within
    tolerance, a recto and a verso. Pairs are matched closest sizes first; a
    third registration within tolerance of both members of a pair joins it.
    Each group is in canvas order."""
    buckets: dict[tuple[str, int, int], list[Registration]] = defaultdict(list)
    for reg in regs:
        if reg.width and reg.height and reg.n_bytes and leaf_side(reg.label):
            buckets[(reg.work_id, reg.width, reg.height)].append(reg)
    out: list[tuple[Registration, ...]] = []
    for members in buckets.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda r: (r.n_bytes, r.seq))
        edges: list[tuple[int, int, int, int, int]] = []
        for i, a in enumerate(members):
            for j in range(i + 1, len(members)):
                b = members[j]
                if not _close(a.n_bytes or 0, b.n_bytes or 0):
                    break
                if leaf_side(a.label) != leaf_side(b.label):
                    edges.append((abs((a.n_bytes or 0) - (b.n_bytes or 0)), a.seq, b.seq, i, j))
        edges.sort()
        group_of: dict[int, list[int]] = {}
        groups: list[list[int]] = []
        for _, _, _, i, j in edges:
            if i in group_of or j in group_of:
                continue
            group = [i, j]
            groups.append(group)
            group_of[i] = group_of[j] = group
        for k, reg in enumerate(members):
            if k in group_of:
                continue
            for group in groups:
                if len(group) < MAX_GROUP and all(
                    _close(reg.n_bytes or 0, members[m].n_bytes or 0) for m in group
                ):
                    group.append(k)
                    group_of[k] = group
                    break
        out.extend(tuple(sorted((members[m] for m in g), key=lambda r: r.seq)) for g in groups)
    return sorted(out, key=lambda g: (g[0].work_id, g[0].seq))


# ---- lines ------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Box:
    """A line's bounding box in image pixels."""

    line_seq: int
    x: float
    y: float
    w: float
    h: float

    @property
    def centre(self) -> float:
        return self.x + self.w / 2


def line_box(line: db.Line) -> Box | None:
    """The box of a line's polygon, else of its baseline; ``None`` without geometry."""
    pts = [
        (float(p[0]), float(p[1]))
        for p in (line.polygon or line.baseline or [])
        if isinstance(p, list | tuple) and len(p) >= 2
    ]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return Box(line.line_seq, min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def boxes(lines: Iterable[db.Line]) -> list[Box]:
    return [b for ln in lines if (b := line_box(ln)) is not None]


def _iou(a: Box, b: Box) -> float:
    ix = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
    iy = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
    inter = ix * iy
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union > 0 else 0.0


def agreement(a: Sequence[Box], b: Sequence[Box]) -> float:
    """The share of the fewer boxes that meet a box of the other set at
    :data:`LINE_IOU`; 0 where either set is empty."""
    few, many = (a, b) if len(a) <= len(b) else (b, a)
    if not few:
        return 0.0
    hits = sum(1 for x in few if any(_iou(x, y) >= LINE_IOU for y in many))
    return hits / len(few)


def crosses(box: Box, fold_x: float) -> bool:
    """Whether a line lies across the fold, with :data:`CROSS_SIDE` of its width
    on each side."""
    if box.w <= 0:
        return False
    return min(fold_x - box.x, box.x + box.w - fold_x) >= CROSS_SIDE * box.w


def find_fold(found: Sequence[Box], width: int) -> int:
    """The fold of a spread: the middle of the longest least-covered run of
    columns in :data:`FOLD_BAND`, nearest the centre of the image among equals;
    the middle of the image where two or more lines cover every column."""
    lo, hi = int(FOLD_BAND[0] * width), int(FOLD_BAND[1] * width)
    if hi <= lo:
        return width // 2
    diff = [0] * (hi - lo + 1)
    for b in found:
        start, end = max(int(b.x), lo), min(int(b.x + b.w), hi)
        if start < end:
            diff[start - lo] += 1
            diff[end - lo] -= 1
    cover: list[int] = []
    run = 0
    for step in diff[:-1]:
        run += step
        cover.append(run)
    least = min(cover)
    if least >= 2:
        return width // 2
    best: tuple[int, float, int] | None = None  # (length, -distance to centre, middle)
    i = 0
    while i < len(cover):
        if cover[i] != least:
            i += 1
            continue
        j = i
        while j + 1 < len(cover) and cover[j + 1] == least:
            j += 1
        middle = lo + (i + j) // 2
        key = (j - i + 1, -abs(middle - width / 2), middle)
        if best is None or key[:2] > best[:2]:
            best = key
        i = j + 1
    return best[2] if best else width // 2


# ---- groups ------------------------------------------------------------------ #


@dataclass(slots=True)
class TwinGroup:
    """Registrations of one scan, confirmed by their lines.

    ``kind`` is ``"spread"`` (two folio pages side by side: ``left`` is the
    verso's page id, ``right`` the recto's, ``fold_x`` the fold in image
    pixels) or ``"fold"`` (``primary`` carries the text; ``reason`` says why
    the group was not split). ``n_lines`` is, per page, the lines it shows.
    """

    work_id: str
    kind: str
    pages: list[str]
    labels: list[str | None]
    width: int
    height: int
    fold_x: int | None = None
    left: str | None = None
    right: str | None = None
    primary: str | None = None
    reason: str = ""
    n_lines: dict[str, int] = field(default_factory=dict)  # lines each page shows
    n_once: dict[str, int] = field(default_factory=dict)  # … and carries in index and exports
    mean_conf: dict[str, float | None] = field(default_factory=dict)  # over the lines shown

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, "", {})}

    def describe(self, page_id: str) -> str:
        """One sentence for the page, as the exports and the server-rendered
        page give it."""
        others = ", ".join(f"fol. {label or pid}" for pid, label in self.others(page_id))
        if self.kind == "spread":
            half = "left" if self.side(page_id) == "left" else "right"
            return (
                f"One image of two folio pages side by side, registered by the library under "
                f"both labels (also {others}); this page is its {half} half."
            )
        primary = self.primary or self.pages[0]
        if page_id == primary:
            return f"The same scan is also registered as {others}; its text is given once, here."
        label = self.label_of(primary)
        return f"The same scan as fol. {label or primary} ({primary}), where its text is given."

    @classmethod
    def from_dict(cls, raw: Mapping) -> TwinGroup:
        return cls(
            work_id=str(raw["work_id"]),
            kind=str(raw["kind"]),
            pages=[str(p) for p in raw["pages"]],
            labels=[None if lab is None else str(lab) for lab in raw.get("labels", [])],
            width=int(raw.get("width") or 0),
            height=int(raw.get("height") or 0),
            fold_x=raw.get("fold_x"),
            left=raw.get("left"),
            right=raw.get("right"),
            primary=raw.get("primary"),
            reason=str(raw.get("reason") or ""),
            n_lines={str(k): int(v) for k, v in (raw.get("n_lines") or {}).items()},
            n_once={str(k): int(v) for k, v in (raw.get("n_once") or {}).items()},
            mean_conf={
                str(k): None if v is None else float(v)
                for k, v in (raw.get("mean_conf") or {}).items()
            },
        )

    def label_of(self, page_id: str) -> str | None:
        return self.labels[self.pages.index(page_id)] if page_id in self.pages else None

    def others(self, page_id: str) -> list[tuple[str, str | None]]:
        """The group's other registrations, ``(page_id, label)``, in canvas order."""
        return [(p, lab) for p, lab in zip(self.pages, self.labels, strict=True) if p != page_id]

    def side(self, page_id: str) -> str | None:
        """``"left"`` or ``"right"`` for a spread's pages, else ``None``."""
        if self.kind != "spread":
            return None
        return "left" if page_id == self.left else "right" if page_id == self.right else None

    def own_lines(
        self, page_id: str, lines: Sequence[db.Line], *, for_index: bool = False
    ) -> list[tuple[db.Line, bool]]:
        """The lines that are this page's in the group, each with whether it
        crosses the fold. A spread page keeps the lines whose centre lies on its
        half, and the lines across the fold — on both halves for reading, on the
        recto only ``for_index``; a line without geometry goes to the recto. A
        fold keeps every line on every page: the page shows its own reading,
        and only the index and the exports leave the others out."""
        side = self.side(page_id)
        if side is None or self.fold_x is None:
            return [(ln, False) for ln in lines]
        out: list[tuple[db.Line, bool]] = []
        for ln in lines:
            box = line_box(ln)
            if box is None:
                if side == "right":
                    out.append((ln, False))
                continue
            across = crosses(box, self.fold_x)
            on_left = box.centre < self.fold_x
            if across:
                if side == "right" or not for_index:
                    out.append((ln, True))
            elif on_left == (side == "left"):
                out.append((ln, False))
        return out

    def carries_text(self, page_id: str) -> bool:
        """Whether the index and the exports list this page's text: every page
        of a spread (its half), only the primary of a fold."""
        return self.kind == "spread" or page_id == self.primary


def decide(
    members: Sequence[Registration], lines: Mapping[str, Sequence[db.Line]]
) -> TwinGroup | None:
    """Confirm a candidate group by its lines and decide spread or fold;
    ``None`` where the lines disagree or there are none to compare."""
    found = {m.page_id: boxes(lines.get(m.page_id, ())) for m in members}
    source = max(members, key=lambda m: (len(found[m.page_id]), -m.seq))
    reference = found[source.page_id]
    if not reference:
        return None
    for m in members:
        if m is not source and agreement(found[m.page_id], reference) < LINE_AGREEMENT:
            return None
    first = members[0]
    width, height = int(first.width or 0), int(first.height or 0)
    group = TwinGroup(
        work_id=first.work_id,
        kind="fold",
        pages=[m.page_id for m in members],
        labels=[m.label for m in members],
        width=width,
        height=height,
        primary=source.page_id,
    )
    sides = [leaf_side(m.label) for m in members]
    if len(members) != 2:
        group.reason = f"one scan registered {len(members)} times"
    elif width < height:
        group.reason = "an upright image: one page, registered twice"
    elif sorted(sides) != ["r", "v"]:
        group.reason = "not one recto and one verso"
    else:
        fold = find_fold(reference, width)
        n_crossing = sum(1 for b in reference if crosses(b, fold))
        if n_crossing > MAX_CROSSING * len(reference):
            group.reason = f"{n_crossing} of {len(reference)} lines run across the fold"
        else:
            verso = members[sides.index("v")].page_id
            recto = members[sides.index("r")].page_id
            group.kind, group.fold_x, group.left, group.right = "spread", fold, verso, recto
            group.primary, group.reason = None, ""
    for m in members:
        own = list(lines.get(m.page_id, ()))
        shown = group.own_lines(m.page_id, own)
        confs = [ln.conf for ln, _ in shown if ln.conf is not None]
        group.n_lines[m.page_id] = len(shown)
        group.mean_conf[m.page_id] = round(sum(confs) / len(confs), 4) if confs else None
        group.n_once[m.page_id] = (
            len(group.own_lines(m.page_id, own, for_index=True))
            if group.carries_text(m.page_id)
            else 0
        )
    return group


@dataclass(slots=True)
class TwinStats:
    """What a pass found: the candidates, the groups their lines confirmed
    (spreads and folds), and the registrations those groups hold."""

    works: int = 0
    candidates: int = 0
    spreads: int = 0
    folds: int = 0
    registrations: int = 0

    @property
    def groups(self) -> int:
        return self.spreads + self.folds

    @property
    def unconfirmed(self) -> int:
        return self.candidates - self.groups

    @property
    def second_registrations(self) -> int:
        """Pages that are another registration of a scan already counted."""
        return self.registrations - self.groups

    def add(self, group: TwinGroup) -> None:
        if group.kind == "spread":
            self.spreads += 1
        else:
            self.folds += 1
        self.registrations += len(group.pages)

    def to_dict(self) -> dict:
        return {
            "works": self.works,
            "candidates": self.candidates,
            "groups": self.groups,
            "spreads": self.spreads,
            "folds": self.folds,
            "unconfirmed": self.unconfirmed,
            "registrations": self.registrations,
            "second_registrations": self.second_registrations,
        }


def resolve_work(
    pages: Sequence[db.Page],
    read_lines: Callable[[str], Sequence[db.Line]],
    stats: TwinStats | None = None,
) -> tuple[list[TwinGroup], dict[str, list[db.Line]]]:
    """The confirmed groups of one work's pages, and the lines read to confirm
    them (by page id, so a caller that needs them again need not re-read)."""
    candidates = candidate_groups(Registration.of(p) for p in pages)
    read: dict[str, list[db.Line]] = {}
    groups: list[TwinGroup] = []
    for members in candidates:
        for m in members:
            if m.page_id not in read:
                read[m.page_id] = [ln for ln in read_lines(m.page_id) if ln.text]
        group = decide(members, read)
        if group is not None:
            groups.append(group)
            if stats is not None:
                stats.add(group)
    if stats is not None:
        stats.works += 1
        stats.candidates += len(candidates)
    return groups, read


# ---- the file the web application reads --------------------------------------- #


class TwinIndex:
    """The confirmed groups by page id, as the web application and the exports
    consult them; empty where no file was written."""

    def __init__(
        self, groups: Iterable[TwinGroup] = (), stats: Mapping | None = None, built_at: str = ""
    ) -> None:
        self.groups = list(groups)
        self.stats = dict(stats or {})
        self.built_at = built_at
        self.by_page: dict[str, TwinGroup] = {p: g for g in self.groups for p in g.pages}

    def __bool__(self) -> bool:
        return bool(self.groups)

    def get(self, page_id: str) -> TwinGroup | None:
        return self.by_page.get(page_id)

    def to_dict(self) -> dict:
        return {
            "version": FORMAT_VERSION,
            "built_at": self.built_at,
            "rule": {
                "bytes": TWIN_BYTES,
                "share": TWIN_SHARE,
                "line_iou": LINE_IOU,
                "line_agreement": LINE_AGREEMENT,
                "fold_band": list(FOLD_BAND),
                "cross_side": CROSS_SIDE,
                "max_crossing": MAX_CROSSING,
            },
            "stats": self.stats,
            "groups": [g.to_dict() for g in self.groups],
        }

    def write(self, path: str | Path) -> Path:
        """Write atomically (a temporary file, then a rename), so a reader never
        sees half a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        return path

    @classmethod
    def load(cls, path: str | Path | None) -> TwinIndex:
        """The file at ``path``; an empty index where there is none or it cannot be read."""
        if path is None:
            return cls()
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(raw, dict) or raw.get("version") != FORMAT_VERSION:
            return cls()
        groups = [TwinGroup.from_dict(g) for g in raw.get("groups") or []]
        return cls(groups, raw.get("stats"), str(raw.get("built_at") or ""))


def find_twins(
    conn: sqlite3.Connection,
    *,
    work_ids: Iterable[str] | None = None,
    progress: Callable[[str], None] | None = None,
) -> TwinIndex:
    """One pass over the store, work by work, reading lines for the candidate
    pages only (the latest run per line, as the viewer shows them)."""
    from leibniz.search.documents import latest_lines

    stats = TwinStats()
    groups: list[TwinGroup] = []
    ids = (
        list(work_ids)
        if work_ids is not None
        else [r[0] for r in conn.execute("SELECT gwlb_object_id FROM works ORDER BY 1")]
    )
    for work_id in ids:
        found, _ = resolve_work(
            db.get_pages(conn, work_id), lambda pid: latest_lines(conn, pid), stats
        )
        groups.extend(found)
        if progress is not None:
            progress(work_id)
    built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return TwinIndex(groups, stats.to_dict(), built)


def render_report(found: TwinIndex) -> str:
    """A short Markdown account of a pass: the counts, then per work family."""
    s = found.stats
    by_family: dict[str, dict[str, int]] = defaultdict(lambda: {"spread": 0, "fold": 0, "pages": 0})
    for g in found.groups:
        family = "DE-611-HS (static)" if g.work_id.startswith("DE-611-HS") else "GWLB object ids"
        by_family[family][g.kind] += 1
        by_family[family]["pages"] += len(g.pages)
    lines = [
        "# Scans registered more than once",
        "",
        "_Generated by `leibniz images twins` (or `leibniz index build`). A candidate is a set "
        "of pages of one work with the same image size, file sizes within "
        f"max({TWIN_BYTES} bytes, {TWIN_SHARE:.1%}), and a recto and a verso among their "
        f"labels; it is confirmed when at least {LINE_AGREEMENT:.0%} of the lines of one meet "
        f"a line of the other at IoU ≥ {LINE_IOU}. See `src/leibniz/images/twins.py`._",
        "",
        f"- **Built:** {found.built_at}",
        f"- **Works:** {s.get('works', 0):,}",
        f"- **Candidates:** {s.get('candidates', 0):,}",
        f"- **Confirmed:** {s.get('groups', 0):,} — {s.get('spreads', 0):,} spreads split at "
        f"the fold, {s.get('folds', 0):,} folded onto one page",
        f"- **Left as they are (lines disagree, or none to compare):** {s.get('unconfirmed', 0):,}",
        f"- **Pages in confirmed groups:** {s.get('registrations', 0):,}, of which "
        f"{s.get('second_registrations', 0):,} are a second registration of a scan",
        "",
        "| Work ids | Spreads | Folded | Pages |",
        "|---|---:|---:|---:|",
    ]
    for family, t in sorted(by_family.items()):
        lines.append(f"| {family} | {t['spread']:,} | {t['fold']:,} | {t['pages']:,} |")
    return "\n".join(lines) + "\n"


TWINS_ENV = "LEIBNIZ_TWINS_PATH"


def twins_path_for(
    backend: str, index_path: str | Path, db_path: str | Path, meili_index: str
) -> Path:
    """Where the twins file sits unless ``LEIBNIZ_TWINS_PATH`` says otherwise:
    beside the index it was built with — ``search.sqlite`` → ``search.twins.json``
    for FTS5, ``<store dir>/<index uid>.twins.json`` for Meilisearch — so a
    staging index built from the same store never overwrites the live one's."""
    explicit = os.environ.get(TWINS_ENV)
    if explicit:
        return Path(explicit)
    if backend == "meili":
        return Path(db_path).parent / f"{meili_index}.twins.json"
    return Path(index_path).with_suffix(".twins.json")


def dedup_stats(stats: Mapping, found: TwinStats, lines_indexed: int) -> dict:
    """The corpus figures once each scan is counted once: ``images`` (page
    images less the second registrations of a scan) and ``lines_once`` (the
    lines the index holds, each scan's lines once), with what was found."""
    pages = int(stats.get("pages") or 0)
    return {
        "images": pages - found.second_registrations,
        "lines_once": lines_indexed,
        "twins": found.to_dict(),
    }


__all__ = [
    "CROSS_SIDE",
    "FOLD_BAND",
    "LINE_AGREEMENT",
    "LINE_IOU",
    "MAX_CROSSING",
    "MAX_GROUP",
    "TWIN_BYTES",
    "TWINS_ENV",
    "TWIN_SHARE",
    "Box",
    "Registration",
    "TwinGroup",
    "TwinIndex",
    "TwinStats",
    "agreement",
    "boxes",
    "candidate_groups",
    "crosses",
    "decide",
    "dedup_stats",
    "find_fold",
    "find_twins",
    "leaf_side",
    "line_box",
    "render_report",
    "resolve_work",
    "twins_path_for",
]
