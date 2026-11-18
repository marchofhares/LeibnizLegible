"""The zone census sample (P1 Task 3): pages drawn from the store, their
scans linked into one folder for PHILIUMM's pipeline.

Blocks (``reports/layout/sample.csv``, column ``block``):

* ``briefwechsel`` and ``handschriften`` — the two strata of the 400. The
  stratum field the P1 prompt names (``page_stats.stratum_heuristic``) is
  NULL on every page (C4 has not run), so the fallback is the OAI set: the
  correspondence and the Handschriften, equal numbers, LH 35 works left to
  their own block. The Leibnitiana (12 works) and the reconstruction set
  (28 pages) are not strata.
* ``lh35`` — pages of works with an LH 35 shelfmark (the mathematics).
* ``marginalien`` — pages of the annotated printed books, a quota of
  German print among them (``page_lang`` says ``de``: the Fraktur question
  of M1's print trial) and the rest across the other languages by their
  share.
* ``philiumm-test`` — her 18 test pages that resolve to GWLB scans, her own
  held-out set.
* ``extra`` — named pages.

Within a block the pages are spread over the works: the works are shuffled
under the seed and visited round by round, one page a work a round, so no
convolute dominates and no scan's twin registration is drawn beside it.
Every page is recognised (v1 lines exist) and cached, and outside the
exclusion list (PHILIUMM's HTR pages, her layout training pages).

The images are symlinks named ``<work>_<seq>.jpg`` (the page id with ``_``
for ``:``, which Windows file systems refuse): the pipeline names its
outputs by the stem. :func:`downscale_images` writes the copies the pipeline
actually reads: rfdetr 1.8.0 upsamples the masks of all 300 queries to the
input image before thresholding, so a 10–20 megapixel scan spills the 6 GB
card; a copy with a bounded long side keeps the model's own input (it
resizes to 1,272 px anyway) and the census scales the results back.
"""

from __future__ import annotations

import csv
import json
import random
import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align.audit_reach import MARGINALIEN_SET, is_lh35

SET_BRIEFWECHSEL = "LeibnizBriefwechsel"
SET_HANDSCHRIFTEN = "LeibnizHandschriften"
LANGS = ("la", "fr", "de", "mixed", "unknown")


@dataclass(slots=True)
class Candidate:
    page_id: str
    work_id: str
    seq: int
    set_name: str
    shelfmarks: list[str]
    label: str | None
    width: int | None
    height: int | None
    local_path: str | None
    lang: str | None  # page_lang's verdict, None when the table has no row


@dataclass(slots=True)
class SamplePage:
    page_id: str
    block: str
    sub: str  # the language for the Marginalien block, else ""
    work_id: str
    set_name: str
    shelfmark: str
    label: str
    width: int | None
    height: int | None
    n_lines: int
    local_path: str
    file: str


def file_name(page_id: str) -> str:
    """``00068371:0219`` → ``00068371_0219.jpg``."""
    return page_id.replace(":", "_") + ".jpg"


def page_id_of(file: str) -> str:
    """The inverse of :func:`file_name` (``_`` → ``:`` at the last underscore)."""
    stem = file.rsplit("/", 1)[-1]
    stem = stem[:-4] if stem.lower().endswith(".jpg") else stem
    work, _, seq = stem.rpartition("_")
    return f"{work}:{seq}"


def eligible(conn: sqlite3.Connection) -> list[Candidate]:
    """Every recognised, cached page with its work and language."""
    has_lang = db.has_table(conn, "page_lang")
    lang_join = "LEFT JOIN page_lang pl ON pl.page_id = p.page_id" if has_lang else ""
    lang_col = "pl.lang" if has_lang else "NULL"
    rows = conn.execute(
        f"""
        SELECT p.page_id, p.work_id, p.seq, w.set_name, w.shelfmarks, p.label, p.width,
               p.height, p.local_path, {lang_col} AS lang
        FROM pages p JOIN works w ON w.gwlb_object_id = p.work_id {lang_join}
        WHERE p.status = 'recognized' AND p.local_path IS NOT NULL
        ORDER BY p.page_id
        """
    )
    out: list[Candidate] = []
    for r in rows:
        out.append(
            Candidate(
                r["page_id"],
                r["work_id"],
                r["seq"],
                r["set_name"],
                json.loads(r["shelfmarks"]) if r["shelfmarks"] else [],
                r["label"],
                r["width"],
                r["height"],
                r["local_path"],
                r["lang"],
            )
        )
    return out


def round_robin(cands: Sequence[Candidate], n: int, rng: random.Random) -> list[Candidate]:
    """``n`` pages spread over the works: the works shuffled, one page a work a
    round (the page chosen at random within the work), round after round."""
    by_work: dict[str, list[Candidate]] = defaultdict(list)
    for c in cands:
        by_work[c.work_id].append(c)
    works = sorted(by_work)
    rng.shuffle(works)
    for w in works:
        rng.shuffle(by_work[w])
    out: list[Candidate] = []
    while len(out) < n and any(by_work.values()):
        for w in works:
            if len(out) >= n:
                break
            if by_work[w]:
                out.append(by_work[w].pop())
    return out


def allocate(counts: Mapping[str, int], n: int) -> dict[str, int]:
    """``n`` shared by largest remainder in proportion to ``counts`` (a key
    never gets more than it has)."""
    total = sum(counts.values())
    if total == 0 or n <= 0:
        return {k: 0 for k in counts}
    quotas = {k: min(v, int(n * v / total)) for k, v in counts.items()}
    rest = n - sum(quotas.values())
    order = sorted(counts, key=lambda k: (-(n * counts[k] / total - int(n * counts[k] / total)), k))
    for k in order:
        if rest <= 0:
            break
        if quotas[k] < counts[k]:
            quotas[k] += 1
            rest -= 1
    return quotas


@dataclass(slots=True)
class SamplePlan:
    n_strata: int = 400
    n_lh35: int = 100
    n_marginalien: int = 100
    marginalien_german: int = 30
    seed: int = 0
    exclude: set[str] = field(default_factory=set)
    named: dict[str, list[str]] = field(default_factory=dict)  # block -> page ids


def draw(conn: sqlite3.Connection, plan: SamplePlan) -> tuple[list[SamplePage], dict]:
    """The sample under the plan, and the notes of what was drawn from what."""
    rng = random.Random(plan.seed)
    cands = eligible(conn)
    taken: set[str] = set(plan.exclude)
    for ids in plan.named.values():
        taken.update(ids)
    pool = [c for c in cands if c.page_id not in taken]
    notes: dict = {"eligible": len(cands), "excluded": len(cands) - len(pool), "blocks": {}}

    def strat(c: Candidate) -> str | None:
        if is_lh35(c.shelfmarks):
            return "lh35"
        if c.set_name == SET_BRIEFWECHSEL:
            return "briefwechsel"
        if c.set_name == SET_HANDSCHRIFTEN:
            return "handschriften"
        if c.set_name == MARGINALIEN_SET:
            return "marginalien"
        return None

    groups: dict[str, list[Candidate]] = defaultdict(list)
    for c in pool:
        s = strat(c)
        if s:
            groups[s].append(c)

    chosen: list[tuple[Candidate, str, str]] = []
    half = plan.n_strata // 2
    for block, n in (
        ("briefwechsel", half),
        ("handschriften", plan.n_strata - half),
        ("lh35", plan.n_lh35),
    ):
        got = round_robin(groups[block], n, rng)
        chosen.extend((c, block, "") for c in got)
        notes["blocks"][block] = {
            "pool_pages": len(groups[block]),
            "pool_works": len({c.work_id for c in groups[block]}),
            "drawn": len(got),
            "works": len({c.work_id for c in got}),
        }
    marg = groups["marginalien"]
    german = [c for c in marg if c.lang == "de"]
    others = [c for c in marg if c.lang != "de"]
    n_de = min(plan.marginalien_german, plan.n_marginalien)
    got_de = round_robin(german, n_de, rng)
    counts = {
        lang: sum(1 for c in others if (c.lang or "unknown") == lang)
        for lang in LANGS
        if lang != "de"
    }
    quotas = allocate(counts, plan.n_marginalien - len(got_de))
    got_other: list[tuple[Candidate, str]] = []
    for lang, q in quotas.items():
        got = round_robin([c for c in others if (c.lang or "unknown") == lang], q, rng)
        got_other.extend((c, lang) for c in got)
    chosen.extend((c, "marginalien", "de") for c in got_de)
    chosen.extend((c, "marginalien", lang) for c, lang in got_other)
    notes["blocks"]["marginalien"] = {
        "pool_pages": len(marg),
        "pool_works": len({c.work_id for c in marg}),
        "pool_by_lang": {"de": len(german), **counts},
        "quotas": {"de": n_de, **quotas},
        "drawn": len(got_de) + len(got_other),
        "works": len({c.work_id for c, _ in got_other} | {c.work_id for c in got_de}),
    }
    by_id = {c.page_id: c for c in cands}
    for block, ids in plan.named.items():
        n_ok = 0
        for pid in ids:
            c = by_id.get(pid)
            if c is None:
                notes.setdefault("named_missing", []).append(f"{block}:{pid}")
                continue
            chosen.append((c, block, ""))
            n_ok += 1
        notes["blocks"][block] = {"named": len(ids), "drawn": n_ok}

    out: list[SamplePage] = []
    seen: set[str] = set()
    for c, block, sub in chosen:
        if c.page_id in seen:
            continue
        seen.add(c.page_id)
        n_lines = conn.execute(
            "SELECT COUNT(DISTINCT line_seq) FROM lines WHERE page_id = ?", (c.page_id,)
        ).fetchone()[0]
        out.append(
            SamplePage(
                c.page_id,
                block,
                sub,
                c.work_id,
                c.set_name,
                c.shelfmarks[0] if c.shelfmarks else "",
                c.label or "",
                c.width,
                c.height,
                int(n_lines),
                c.local_path or "",
                file_name(c.page_id),
            )
        )
    order = {"briefwechsel": 0, "handschriften": 1, "lh35": 2, "marginalien": 3}
    out.sort(key=lambda s: (order.get(s.block, 9), s.block, s.page_id))
    notes["pages"] = len(out)
    notes["seed"] = plan.seed
    return out, notes


FIELDS = (
    "page_id",
    "block",
    "sub",
    "work_id",
    "set_name",
    "shelfmark",
    "label",
    "width",
    "height",
    "n_lines",
    "local_path",
    "file",
)


def write_sample(rows: Sequence[SamplePage], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: getattr(r, k) for k in FIELDS})


def read_sample(path: Path) -> list[SamplePage]:
    out: list[SamplePage] = []
    with Path(path).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.append(
                SamplePage(
                    row["page_id"],
                    row["block"],
                    row.get("sub", ""),
                    row["work_id"],
                    row["set_name"],
                    row["shelfmark"],
                    row["label"],
                    int(row["width"]) if row.get("width") else None,
                    int(row["height"]) if row.get("height") else None,
                    int(row["n_lines"] or 0),
                    row["local_path"],
                    row["file"],
                )
            )
    return out


def link_images(
    rows: Iterable[SamplePage], images_root: Path, dest: Path, *, copy: bool = False
) -> tuple[int, list[str]]:
    """Symlink (or copy) each page's cached scan into ``dest`` under its sample
    file name; returns the count made and the pages whose scan is missing."""
    import shutil

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    made, missing = 0, []
    for r in rows:
        src = Path(images_root) / r.local_path
        if not src.exists():
            missing.append(r.page_id)
            continue
        target = dest / r.file
        if target.is_symlink() or target.exists():
            target.unlink()
        if copy:
            shutil.copyfile(src, target)
        else:
            target.symlink_to(src.resolve())
        made += 1
    return made, missing


def downscale_images(
    rows: Iterable[SamplePage],
    images_root: Path,
    dest: Path,
    *,
    long_side: int = 1600,
    quality: int = 92,
) -> tuple[int, int, list[str]]:
    """Write each page's scan into ``dest`` under its sample file name with the
    long side at most ``long_side`` pixels (a scan already smaller is copied
    as it is), skipping files already there; returns ``(written, present,
    missing page ids)``. Pillow, lazily."""
    from PIL import Image

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    written, present, missing = 0, 0, []
    for r in rows:
        src = Path(images_root) / r.local_path
        target = dest / r.file
        if target.exists():
            present += 1
            continue
        if not src.exists():
            missing.append(r.page_id)
            continue
        with Image.open(src) as im:
            w, h = im.size
            scale = long_side / max(w, h)
            if scale < 1.0:
                im = im.convert("RGB").resize(
                    (max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.LANCZOS
                )
                im.save(target, "JPEG", quality=quality)
            else:
                import shutil

                shutil.copyfile(src, target)
        written += 1
    return written, present, missing


__all__ = [
    "FIELDS",
    "LANGS",
    "Candidate",
    "SamplePage",
    "SamplePlan",
    "allocate",
    "downscale_images",
    "draw",
    "eligible",
    "file_name",
    "link_images",
    "page_id_of",
    "read_sample",
    "round_robin",
    "write_sample",
]
