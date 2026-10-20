"""Place the pool's German letters on the store's pages and freeze the test set (K2b, Task 2).

A letter's first witness names a shelfmark with its leaves (``LBr.411 Bl.518–519``).
The crosswalk's signature keys (:func:`leibniz.catalog.crosswalk.build_work_key_index`)
name the work that carries the shelfmark, and the C2 resolver
(:mod:`leibniz.align.resolve`) turns the leaves into the work's canvases by their
folio labels — the rule the GT factory localized its pieces with and the web
layer places a catalogue record by. A letter is dropped, and counted by reason,
when the store has no work for its key, when no folio-labelled canvas lies in
its range, when its pages carry no recognised line, or when the *Überlieferung*
block names a second text on the leaves (``Auf Bl.4vo L von N.69``: the page
would charge a reader for text that is not in the reference).

The set is drawn seeded and stratified: every letter in Leibniz's hand (L) or
his scribe's (l), and a sample of the correspondents' letters (K, k) of about
the same size, allocated over siglum and year in proportion to what the pool
holds. It is then split once, seeded and stratified by siglum and year, into a
**selection half** (K3 and K4 may choose a reader on it and set a margin) and a
**test half** (reported only, never used for a choice). The frozen set is
``reports/kurrent/letterpool-testset.csv`` — letter, year, half, siglum,
shelfmark, leaves, pages, lines and the SHA-256 of each reference text, no text —
and the texts themselves under ``data/kurrent/letterpool/`` (gitignored, nc
bucket). The store is opened read-only; nothing here writes to it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sqlite3
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from leibniz import db
from leibniz.align.letterpool import LICENCE, LICENCE_BUCKET, SIGLA, Letter, read_letters
from leibniz.align.resolve import FolioSpan, index_pages, parse_bl_span, select_span
from leibniz.catalog.crosswalk import build_work_key_index

DEFAULT_LETTERS_DIR = Path("data/kurrent/letterpool")
DEFAULT_GERMAN_PIECES = Path("data/kurrent/german_pieces.jsonl")
DEFAULT_HELDOUT = Path("reports/philiumm/heldout_pages.csv")
DEFAULT_TESTSET_CSV = Path("reports/kurrent/letterpool-testset.csv")
DEFAULT_PLACEMENT_CSV = Path("reports/kurrent/letterpool-placement.csv")
DEFAULT_TEXTS = Path("data/kurrent/letterpool/testset.jsonl")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
SEED = 20261019
HALVES: tuple[str, ...] = ("selection", "test")
REASONS: tuple[str, ...] = ("placed", "no_work", "no_canvas", "no_lines", "shared")
OWN_SIGLA: tuple[str, ...] = ("L", "l")
CORRESPONDENT_SIGLA: tuple[str, ...] = ("K", "k")


# --------------------------------------------------------------------------- #
# Placement
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Placed:
    """One German letter against the store: where it sits, or why it does not."""

    letter_id: str
    year: int
    number: str
    siglum: str | None
    kind: str | None
    language: str
    shelfmark: str | None
    key: str | None
    blatt: str | None
    reason: str  # one of REASONS
    work_id: str | None = None
    page_ids: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    n_lines: int = 0
    n_chars: int = 0
    text_sha256: str = ""
    shared_note: str | None = None
    drawn: bool = False
    half: str | None = None

    @property
    def n_pages(self) -> int:
        return len(self.page_ids)

    @property
    def siglum_class(self) -> str:
        return self.siglum if self.siglum in SIGLA else "other"


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_recognised_lines(conn: sqlite3.Connection, page_ids: Iterable[str]) -> int:
    """Recognised lines (``lines.text`` not null) on the pages, as the factory gathers them."""
    total = 0
    for pid in page_ids:
        total += conn.execute(
            "SELECT COUNT(*) FROM lines WHERE page_id = ? AND text IS NOT NULL", (pid,)
        ).fetchone()[0]
    return total


class _FolioIndexes:
    """One folio index per work, built on first use (a convolute places many letters)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.cache: dict[str, dict[int, list[db.Page]]] = {}

    def get(self, work_id: str) -> dict[int, list[db.Page]]:
        if work_id not in self.cache:
            self.cache[work_id] = index_pages(db.get_pages(self.conn, work_id))
        return self.cache[work_id]


def place_letter(
    conn: sqlite3.Connection,
    letter: Letter,
    index: Mapping[str, Sequence[str]],
    folios: _FolioIndexes | None = None,
) -> Placed:
    """Place one letter: the work through its key, the pages through its leaves.

    Where a key names several works (a convolute digitised in parts), the first
    work whose folio labels cover the leaves wins. The reasons are tried in
    order — no work, no canvas, no recognised line, shared leaves — so a letter
    is counted once, under the first that applies.
    """
    w = letter.witness
    folios = folios or _FolioIndexes(conn)
    placed = Placed(
        letter_id=letter.letter_id,
        year=letter.year,
        number=letter.number,
        siglum=w.siglum,
        kind=w.kind,
        language=letter.language,
        shelfmark=w.shelfmark,
        key=w.key,
        blatt=w.blatt,
        reason="placed",
        n_chars=letter.n_chars,
        text_sha256=text_sha256(letter.text),
        shared_note=w.shared_note,
    )
    works = list(index.get(w.key or "", []))
    if not works:
        placed.reason = "no_work"
        return placed
    span: FolioSpan | None = parse_bl_span(w.blatt)
    if span is None:
        placed.reason = "no_canvas"
        return placed
    for wid in works:
        res = select_span(folios.get(wid), wid, span)
        if res.resolved:
            placed.work_id = wid
            placed.page_ids = [p.id for p in res.pages]
            placed.labels = [p.label or "" for p in res.pages]
            break
    if not placed.page_ids:
        placed.reason = "no_canvas"
        return placed
    placed.n_lines = count_recognised_lines(conn, placed.page_ids)
    if placed.n_lines == 0:
        placed.reason = "no_lines"
        return placed
    if w.shared:
        placed.reason = "shared"
    return placed


def german_letters(letters: Iterable[Letter]) -> tuple[list[Letter], list[Letter]]:
    """The letters whose language is German and whose first witness is placeable, and
    apart from them the mixed-language ones with a placeable witness (reported, not used)."""
    de: list[Letter] = []
    mixed: list[Letter] = []
    for ltr in letters:
        if not ltr.witness.placeable:
            continue
        if ltr.language == "de":
            de.append(ltr)
        elif ltr.language == "mixed":
            mixed.append(ltr)
    return de, mixed


def place_all(
    conn: sqlite3.Connection,
    letters: Sequence[Letter],
    *,
    index: Mapping[str, Sequence[str]] | None = None,
    log: Callable[[str], None] | None = None,
) -> list[Placed]:
    """Every German letter with a placeable witness against the store, in volume order."""
    index = build_work_key_index(conn) if index is None else index
    folios = _FolioIndexes(conn)
    out: list[Placed] = []
    for i, ltr in enumerate(letters, start=1):
        out.append(place_letter(conn, ltr, index, folios))
        if log and i % 100 == 0:
            log(f"{i} letters placed so far")
    return out


# --------------------------------------------------------------------------- #
# Disjointness against the training material
# --------------------------------------------------------------------------- #


def k2_pages(path: Path | str = DEFAULT_GERMAN_PIECES) -> set[str]:
    """The pages of K2's German pieces (the census's ``german_pieces.jsonl``)."""
    p = Path(path)
    if not p.exists():
        return set()
    pages: set[str] = set()
    for raw in p.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            pages.update(json.loads(raw).get("page_ids") or [])
    return pages


def heldout_pages(path: Path | str = DEFAULT_HELDOUT) -> set[str]:
    """The PHILIUMM held-out pages (``reports/philiumm/heldout_pages.csv``)."""
    p = Path(path)
    if not p.exists():
        return set()
    with p.open(encoding="utf-8", newline="") as fh:
        return {row["page_id"] for row in csv.DictReader(fh) if row.get("page_id")}


def overlaps(placed: Sequence[Placed], other: set[str]) -> dict[str, list[str]]:
    """``{letter_id: [shared page ids]}`` for the placed letters whose pages meet ``other``."""
    out: dict[str, list[str]] = {}
    for p in placed:
        if p.reason != "placed":
            continue
        hit = sorted(set(p.page_ids) & other)
        if hit:
            out[p.letter_id] = hit
    return out


# --------------------------------------------------------------------------- #
# The draw and the halves
# --------------------------------------------------------------------------- #


def allocate(sizes: Mapping[tuple, int], n: int) -> dict[tuple, int]:
    """Proportional allocation of ``n`` over cells by largest remainder (deterministic)."""
    total = sum(sizes.values())
    if total == 0 or n <= 0:
        return dict.fromkeys(sizes, 0)
    n = min(n, total)
    exact = {cell: n * size / total for cell, size in sizes.items()}
    quota = {cell: int(exact[cell]) for cell in sizes}
    left = n - sum(quota.values())
    order = sorted(sizes, key=lambda c: (-(exact[c] - quota[c]), c))
    for cell in order[:left]:
        quota[cell] += 1
    return quota


def draw(placed: Sequence[Placed], *, seed: int = SEED, n_kk: int | None = None) -> list[Placed]:
    """Mark the drawn letters: every L and l letter that placed, and a seeded sample of
    the K and k letters of the same size (``n_kk`` overrides it), allocated over
    the (siglum, year) cells in proportion to the pool. Returns the drawn letters
    in volume order."""
    rng = random.Random(seed)
    eligible = [p for p in placed if p.reason == "placed"]
    own = [p for p in eligible if p.siglum in OWN_SIGLA]
    corr = [p for p in eligible if p.siglum in CORRESPONDENT_SIGLA]
    n = len(own) if n_kk is None else n_kk
    cells: dict[tuple, list[Placed]] = defaultdict(list)
    for p in corr:
        cells[(p.siglum, p.year)].append(p)
    quota = allocate({cell: len(v) for cell, v in cells.items()}, n)
    chosen: list[Placed] = list(own)
    for cell in sorted(cells):
        members = sorted(cells[cell], key=lambda p: (p.year, p.number, p.letter_id))
        rng.shuffle(members)
        chosen.extend(members[: quota[cell]])
    for p in placed:
        p.drawn = False
    for p in chosen:
        p.drawn = True
    return [p for p in placed if p.drawn]


def split_halves(drawn: Sequence[Placed], *, seed: int = SEED) -> None:
    """Assign each drawn letter a half, once: within every (siglum, year) cell the
    letters are shuffled (seeded) and dealt alternately, the odd one out going
    to the side that has fewer so far."""
    rng = random.Random(seed + 1)
    cells: dict[tuple, list[Placed]] = defaultdict(list)
    for p in drawn:
        cells[(p.siglum, p.year)].append(p)
    counts = dict.fromkeys(HALVES, 0)
    for cell in sorted(cells):
        members = sorted(cells[cell], key=lambda p: (p.year, p.number, p.letter_id))
        rng.shuffle(members)
        first = min(HALVES, key=lambda h: (counts[h], h))
        order = (first, *(h for h in HALVES if h != first))
        for i, p in enumerate(members):
            p.half = order[i % len(order)]
            counts[p.half] += 1


# --------------------------------------------------------------------------- #
# Files
# --------------------------------------------------------------------------- #

TESTSET_COLUMNS = (
    "letter_id",
    "year",
    "number",
    "half",
    "siglum",
    "kind",
    "shelfmark",
    "leaves",
    "work_id",
    "page_ids",
    "n_pages",
    "n_lines",
    "n_chars",
    "text_sha256",
)


def write_testset(
    drawn: Sequence[Placed],
    letters_by_id: Mapping[str, Letter],
    *,
    csv_path: Path | str = DEFAULT_TESTSET_CSV,
    texts_path: Path | str = DEFAULT_TEXTS,
) -> tuple[Path, Path]:
    """The frozen set: the committed CSV without text, the texts under ``data/``."""
    csv_path, texts_path = Path(csv_path), Path(texts_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    texts_path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(drawn, key=lambda p: (p.year, int(p.number), p.letter_id))
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(TESTSET_COLUMNS)
        for p in rows:
            w.writerow(
                [
                    p.letter_id,
                    p.year,
                    p.number,
                    p.half or "",
                    p.siglum or "",
                    p.kind or "",
                    p.shelfmark or "",
                    p.blatt or "",
                    p.work_id or "",
                    " ".join(p.page_ids),
                    p.n_pages,
                    p.n_lines,
                    p.n_chars,
                    p.text_sha256,
                ]
            )
    with texts_path.open("w", encoding="utf-8") as fh:
        for p in rows:
            ltr = letters_by_id[p.letter_id]
            fh.write(
                json.dumps(
                    {
                        "letter_id": p.letter_id,
                        "year": p.year,
                        "number": p.number,
                        "half": p.half,
                        "siglum": p.siglum,
                        "shelfmark": p.shelfmark,
                        "leaves": p.blatt,
                        "work_id": p.work_id,
                        "page_ids": p.page_ids,
                        "labels": p.labels,
                        "n_lines": p.n_lines,
                        "heading": ltr.heading,
                        "place_date": ltr.place_date,
                        "text": ltr.text,
                        "text_sha256": p.text_sha256,
                        "licence": LICENCE,
                        "licence_bucket": LICENCE_BUCKET,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return csv_path, texts_path


def read_testset(csv_path: Path | str = DEFAULT_TESTSET_CSV) -> list[dict]:
    with Path(csv_path).open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["page_ids"] = r["page_ids"].split()
        r["year"] = int(r["year"])
        r["n_pages"] = int(r["n_pages"])
        r["n_lines"] = int(r["n_lines"])
        r["n_chars"] = int(r["n_chars"])
    return rows


def read_texts(texts_path: Path | str = DEFAULT_TEXTS) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for raw in Path(texts_path).read_text(encoding="utf-8").splitlines():
        if raw.strip():
            row = json.loads(raw)
            out[row["letter_id"]] = row
    return out


def write_placement(placed: Sequence[Placed], path: Path | str = DEFAULT_PLACEMENT_CSV) -> Path:
    """Every German letter's placement and reason (no text), for the record."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "letter_id",
                "year",
                "siglum",
                "key",
                "leaves",
                "reason",
                "work_id",
                "n_pages",
                "n_lines",
                "n_chars",
                "drawn",
                "half",
            ]
        )
        for r in placed:
            w.writerow(
                [
                    r.letter_id,
                    r.year,
                    r.siglum or "",
                    r.key or "",
                    r.blatt or "",
                    r.reason,
                    r.work_id or "",
                    r.n_pages,
                    r.n_lines,
                    r.n_chars,
                    int(r.drawn),
                    r.half or "",
                ]
            )
    return p


# --------------------------------------------------------------------------- #
# Summary and report
# --------------------------------------------------------------------------- #


def _by(rows: Iterable[Placed], key: Callable[[Placed], object]) -> dict:
    out: dict = {}
    for p in rows:
        k = str(key(p))
        d = out.setdefault(k, {"letters": 0, "pages": 0, "lines": 0, "chars": 0})
        d["letters"] += 1
        d["pages"] += p.n_pages
        d["lines"] += p.n_lines
        d["chars"] += p.n_chars
    return dict(sorted(out.items()))


def shared_pages(rows: Sequence[Placed]) -> dict:
    """Pages that two or more of the rows share (short notes on one leaf), as groups."""
    owner: dict[str, list[str]] = defaultdict(list)
    for p in rows:
        for pid in p.page_ids:
            owner[pid].append(p.letter_id)
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for pid, ids in sorted(owner.items()):
        if len(ids) > 1:
            groups[tuple(ids)].append(pid)
    return {
        "distinct_pages": len(owner),
        "groups": [{"letters": list(ids), "pages": pages} for ids, pages in groups.items()],
    }


def summarize(
    placed: Sequence[Placed],
    *,
    n_mixed: int,
    k2_overlap: Mapping[str, Sequence[str]],
    heldout_overlap: Mapping[str, Sequence[str]],
    seed: int,
) -> dict:
    """Counts only: placement by reason and siglum, the draw by siglum, year and half."""
    by_reason = {
        r: {
            s: sum(1 for p in placed if p.reason == r and p.siglum_class == s)
            for s in (*SIGLA, "other")
        }
        for r in REASONS
    }
    for r in REASONS:
        by_reason[r]["all"] = sum(by_reason[r].values())
    ok = [p for p in placed if p.reason == "placed"]
    drawn = [p for p in placed if p.drawn]
    halves = {h: [p for p in drawn if p.half == h] for h in HALVES}

    def totals(rows: Sequence[Placed]) -> dict:
        return {
            "letters": len(rows),
            "pages": sum(p.n_pages for p in rows),
            "lines": sum(p.n_lines for p in rows),
            "chars": sum(p.n_chars for p in rows),
        }

    return {
        "generated": date.today().isoformat(),
        "seed": seed,
        "german_letters": len(placed),
        "mixed_letters_apart": n_mixed,
        "by_reason": by_reason,
        "placed": {
            **totals(ok),
            "by_siglum": _by(ok, lambda p: p.siglum_class),
            "by_year": _by(ok, lambda p: p.year),
        },
        "disjointness": {
            "k2_german_pieces": {
                "letters": len(k2_overlap),
                "pages": sum(len(v) for v in k2_overlap.values()),
                "examples": dict(list(k2_overlap.items())[:10]),
            },
            "philiumm_heldout": {
                "letters": len(heldout_overlap),
                "pages": sum(len(v) for v in heldout_overlap.values()),
                "examples": dict(list(heldout_overlap.items())[:10]),
            },
        },
        "drawn": {
            **totals(drawn),
            "by_siglum": _by(drawn, lambda p: p.siglum_class),
            "by_year": _by(drawn, lambda p: p.year),
            "by_half": {h: totals(rows) for h, rows in halves.items()},
            "by_half_siglum": {
                h: _by(rows, lambda p: p.siglum_class) for h, rows in halves.items()
            },
            "by_half_year": {h: _by(rows, lambda p: p.year) for h, rows in halves.items()},
            "pages_shared_among_drawn": shared_pages(drawn),
        },
    }


def _n(x: int) -> str:
    return f"{x:,}"


def render_report(summary: dict) -> str:
    """``letterpool-set.md``: the placement, the drops, the draw and the halves, numbers only."""
    s = summary
    out: list[str] = []
    out.append("# The letter-pool test set: placement and draw (K2b Task 2)")
    out.append("")
    out.append(
        f"{_n(s['german_letters'])} German letters of the pool name a first witness in the "
        "GWLB's Leibniz collections with a `Bl.` range (the mixed-language letters with such a "
        f"witness, {s['mixed_letters_apart']}, are counted apart and not used). Each was placed "
        "the way the GT factory localizes a piece: the work through the crosswalk's signature "
        "keys, the pages through the C2 resolver's folio labels; the store was opened "
        "read-only. A letter is dropped under the first reason that applies: no work in the "
        "store for its shelfmark, no folio-labelled canvas in its range, no recognised line on "
        "its pages, or a second text on its leaves named by the *Überlieferung* block. The "
        f"draw (seed {s['seed']}) takes every letter in Leibniz's hand (L) or his scribe's (l) "
        "and a sample of the correspondents' letters (K, k) of the same size, allocated over "
        "siglum and year in proportion to the pool, and splits the set once, stratified by "
        "siglum and year, into a selection half (K3 and K4 may choose a reader on it) and a "
        "test half (reported only). The set is frozen in `letterpool-testset.csv` (no text) "
        f"and the texts under `data/kurrent/letterpool/` ({LICENCE}, {LICENCE_BUCKET} bucket)."
    )
    out.append("")
    out.append("## Placement by reason")
    out.append("")
    out.append("| reason | L | l | K | k | other | all |")
    out.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in REASONS:
        row = s["by_reason"][r]
        out.append(
            f"| {r} | {row['L']} | {row['l']} | {row['K']} | {row['k']} | {row['other']} | "
            f"**{row['all']}** |"
        )
    p = s["placed"]
    out.append("")
    out.append(
        f"Placed: **{_n(p['letters'])} letters on {_n(p['pages'])} pages with "
        f"{_n(p['lines'])} recognised lines** ({_n(p['chars'])} reference characters)."
    )
    out.append("")
    out.append("| year | placed letters | pages | lines |")
    out.append("|---|---:|---:|---:|")
    for year, row in p["by_year"].items():
        out.append(f"| {year} | {row['letters']} | {_n(row['pages'])} | {_n(row['lines'])} |")
    d = s["disjointness"]
    out.append("")
    out.append("## Disjointness")
    out.append("")
    out.append(
        f"Pages shared with K2's German pieces (`data/kurrent/german_pieces.jsonl`): "
        f"**{d['k2_german_pieces']['pages']}** on {d['k2_german_pieces']['letters']} letters. "
        f"Pages shared with the PHILIUMM held-out pages (`reports/philiumm/heldout_pages.csv`): "
        f"**{d['philiumm_heldout']['pages']}** on {d['philiumm_heldout']['letters']} letters."
    )
    for name, block in (("K2", d["k2_german_pieces"]), ("PHILIUMM", d["philiumm_heldout"])):
        if block["examples"]:
            out.append("")
            out.append(
                f"{name} overlaps (first ten): "
                + "; ".join(
                    f"`{lid}` {' '.join(pages)}" for lid, pages in block["examples"].items()
                )
            )
    dr = s["drawn"]
    out.append("")
    out.append("## The draw")
    out.append("")
    out.append(
        f"**{_n(dr['letters'])} letters, {_n(dr['pages'])} pages, {_n(dr['lines'])} recognised "
        f"lines, {_n(dr['chars'])} reference characters.**"
    )
    sp = dr["pages_shared_among_drawn"]
    out.append("")
    out.append(
        f"{_n(sp['distinct_pages'])} distinct pages; "
        + (
            f"{len(sp['groups'])} groups of drawn letters share pages (short pieces on one leaf: "
            + "; ".join(f"{', '.join(g['letters'])} on {len(g['pages'])}" for g in sp["groups"])
            + "). The metric's free prefix and suffix leave a neighbour's text uncharged."
            if sp["groups"]
            else "no two drawn letters share a page."
        )
    )
    out.append("")
    out.append("| siglum | letters | pages | lines | selection half | test half |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for sig, row in dr["by_siglum"].items():
        sel = dr["by_half_siglum"]["selection"].get(sig, {}).get("letters", 0)
        tst = dr["by_half_siglum"]["test"].get(sig, {}).get("letters", 0)
        out.append(
            f"| {sig} | {row['letters']} | {_n(row['pages'])} | {_n(row['lines'])} | "
            f"{sel} | {tst} |"
        )
    out.append("")
    out.append("| year | letters | pages | lines | selection half | test half |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for year, row in dr["by_year"].items():
        sel = dr["by_half_year"]["selection"].get(year, {}).get("letters", 0)
        tst = dr["by_half_year"]["test"].get(year, {}).get("letters", 0)
        out.append(
            f"| {year} | {row['letters']} | {_n(row['pages'])} | {_n(row['lines'])} | "
            f"{sel} | {tst} |"
        )
    out.append("")
    out.append("| half | letters | pages | lines | chars |")
    out.append("|---|---:|---:|---:|---:|")
    for h in HALVES:
        row = dr["by_half"][h]
        out.append(
            f"| {h} | {row['letters']} | {_n(row['pages'])} | {_n(row['lines'])} | "
            f"{_n(row['chars'])} |"
        )
    out.append("")
    out.append(
        "*lines* are the recognised lines of the C1 run on the letters' pages, every one "
        "(nothing filtered); the metric of Task 3 aligns each letter's reference text to their "
        "concatenation. *pages* count canvases; a leaf is two."
    )
    out.append("")
    return "\n".join(out)


def build_set(
    conn: sqlite3.Connection,
    letters: Sequence[Letter],
    *,
    seed: int = SEED,
    n_kk: int | None = None,
    german_pieces: Path | str = DEFAULT_GERMAN_PIECES,
    heldout: Path | str = DEFAULT_HELDOUT,
    log: Callable[[str], None] | None = None,
) -> tuple[list[Placed], dict]:
    """Place, check, draw, split: the placed letters (drawn ones marked) and the summary."""
    de, mixed = german_letters(letters)
    placed = place_all(conn, de, log=log)
    k2_ov = overlaps(placed, k2_pages(german_pieces))
    held_ov = overlaps(placed, heldout_pages(heldout))
    drawn = draw(placed, seed=seed, n_kk=n_kk)
    split_halves(drawn, seed=seed)
    summary = summarize(
        placed, n_mixed=len(mixed), k2_overlap=k2_ov, heldout_overlap=held_ov, seed=seed
    )
    return placed, summary


def load_all_letters(letters_dir: Path | str = DEFAULT_LETTERS_DIR) -> list[Letter]:
    out: list[Letter] = []
    for path in sorted(Path(letters_dir).glob("letters-*.jsonl")):
        out.extend(read_letters(path))
    return out


__all__ = [
    "CORRESPONDENT_SIGLA",
    "DEFAULT_GERMAN_PIECES",
    "DEFAULT_HELDOUT",
    "DEFAULT_LETTERS_DIR",
    "DEFAULT_PLACEMENT_CSV",
    "DEFAULT_TESTSET_CSV",
    "DEFAULT_TEXTS",
    "HALVES",
    "OWN_SIGLA",
    "REASONS",
    "SEED",
    "TESTSET_COLUMNS",
    "Placed",
    "allocate",
    "build_set",
    "count_recognised_lines",
    "draw",
    "german_letters",
    "heldout_pages",
    "k2_pages",
    "load_all_letters",
    "overlaps",
    "place_all",
    "place_letter",
    "read_testset",
    "read_texts",
    "render_report",
    "split_halves",
    "summarize",
    "text_sha256",
    "write_placement",
    "write_testset",
]
