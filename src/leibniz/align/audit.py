"""Hand audit of minted ground truth (the C2 gate): sample → sheet → score.

The factory measures its own *yield*; it cannot measure its *precision* — whether
the edition text it projected onto a line image is the text of that line. B2
measured 97.5 % on favourable material against PHILIUMM's diplomatic GT; the
corpus-scale mint has no such reference, so the gate is a human look at a
stratified sample of the minted lines (SPECS §6: the operator hand-audits ~200
lines before any training).

* :func:`build_sheet` draws ``n`` minted lines, **equal numbers per stratum**
  (a proportional draw would give the rare fair copies a handful of lines and
  say nothing about them), cuts each line's image from the cached page by its
  segmentation polygon, and writes one self-contained HTML page: crop, minted
  text, the HTR machine text for comparison, and a verdict per line —
  *correct* (the minted text is this line's text), *boundary* (right line, but
  the slice starts or ends a word or more off), *wrong* (another line, or
  garbage), *unreadable* (the auditor cannot tell). Verdicts survive a reload
  (browser storage) and download as a CSV.
* :func:`score_verdicts` reads that CSV back: per-stratum precision with a
  Wilson 95 % interval, plus the corpus-weighted precision (each stratum
  weighted by its share of ``gt_lines``), rendered as ``reports/gt-audit.md``.

Nothing here needs a model or the network; the crops need the A2 image cache
(``--images``), and a line whose page is not cached is listed without an image.
"""

from __future__ import annotations

import base64
import csv
import html
import io
import json
import math
import random
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align.report import GATE_PRECISION
from leibniz.images.fetch import local_relpath

STRATA = ("fair_copy", "light_revision", "heavy_revision", "scrap", "unknown")
VERDICTS = ("correct", "boundary", "wrong", "unreadable")
DEFAULT_N = 200
CROP_PAD = 12  # pixels of context around the line polygon
CROP_MAX_WIDTH = 1400  # downscale wider crops so the sheet stays light


@dataclass(slots=True)
class AuditLine:
    """One sampled minted line, with what the auditor needs to judge it."""

    ref: str
    page_id: str
    line_seq: int
    stratum: str
    align_conf: float | None
    gt_text: str
    htr_text: str | None
    source: str
    label: str | None = None  # folio label of the page
    crop_png: bytes | None = None
    image_note: str = ""


@dataclass(slots=True)
class AuditSheet:
    """What :func:`build_sheet` wrote."""

    lines: list[AuditLine]
    html_path: Path
    csv_path: Path
    by_stratum: dict[str, int] = field(default_factory=dict)

    @property
    def n_with_crops(self) -> int:
        return sum(1 for ln in self.lines if ln.crop_png is not None)


def allocate(available: dict[str, int], n: int) -> dict[str, int]:
    """Split ``n`` draws equally over the strata that have lines, capped by supply.

    A stratum short of its equal share gives its remainder to the others, so the
    sheet still holds ``n`` lines when the corpus allows it.
    """
    strata = [s for s in STRATA if available.get(s, 0) > 0]
    alloc = dict.fromkeys(strata, 0)
    remaining = n
    open_strata = list(strata)
    while remaining > 0 and open_strata:
        share = max(1, remaining // len(open_strata))
        progressed = False
        for s in list(open_strata):
            take = min(share, available[s] - alloc[s], remaining)
            if take <= 0:
                open_strata.remove(s)
                continue
            alloc[s] += take
            remaining -= take
            progressed = True
            if alloc[s] >= available[s]:
                open_strata.remove(s)
            if remaining == 0:
                break
        if not progressed:
            break
    return {s: k for s, k in alloc.items() if k}


def sample_lines(conn: sqlite3.Connection, n: int = DEFAULT_N, *, seed: int = 0) -> list[AuditLine]:
    """Draw ``n`` minted lines, equal per stratum, reproducibly for ``seed``."""
    counts = {
        (row[0] or "unknown"): row[1]
        for row in conn.execute("SELECT stratum, COUNT(*) FROM gt_lines GROUP BY stratum")
    }
    rng = random.Random(seed)
    out: list[AuditLine] = []
    for stratum, k in allocate(counts, n).items():
        where = "stratum IS NULL" if stratum == "unknown" else "stratum = ?"
        params: tuple = () if stratum == "unknown" else (stratum,)
        ids = [r[0] for r in conn.execute(f"SELECT id FROM gt_lines WHERE {where}", params)]
        for gid in sorted(rng.sample(ids, k)):
            row = conn.execute(
                "SELECT line_image_ref, text, source, stratum, align_conf "
                "FROM gt_lines WHERE id = ?",
                (gid,),
            ).fetchone()
            page_id, seq = split_ref(row["line_image_ref"])
            out.append(
                AuditLine(
                    ref=row["line_image_ref"],
                    page_id=page_id,
                    line_seq=seq,
                    stratum=row["stratum"] or "unknown",
                    align_conf=row["align_conf"],
                    gt_text=row["text"],
                    htr_text=None,
                    source=row["source"],
                )
            )
    return out


def split_ref(ref: str) -> tuple[str, int]:
    """``"{page_id}:{line_seq:03d}"`` → ``(page_id, line_seq)`` (the canonical line id)."""
    page_id, _, seq = ref.rpartition(":")
    return page_id, int(seq)


def line_geometry(
    conn: sqlite3.Connection, page_id: str, line_seq: int
) -> tuple[list | None, list | None, str | None]:
    """The line's ``(polygon, baseline, text)`` from its latest recognised row."""
    row = conn.execute(
        """
        SELECT polygon, baseline, text FROM lines
         WHERE page_id = ? AND line_seq = ?
         ORDER BY (text IS NOT NULL) DESC, run_id DESC LIMIT 1
        """,
        (page_id, line_seq),
    ).fetchone()
    if row is None:
        return None, None, None
    polygon = json.loads(row["polygon"]) if row["polygon"] else None
    baseline = json.loads(row["baseline"]) if row["baseline"] else None
    return polygon, baseline, row["text"]


def crop_box(
    polygon: Sequence | None,
    baseline: Sequence | None,
    *,
    width: int,
    height: int,
    pad: int = CROP_PAD,
) -> tuple[int, int, int, int] | None:
    """Pixel box ``(left, top, right, bottom)`` around the line, padded and clamped."""
    pts = [(float(p[0]), float(p[1])) for p in (polygon or []) if len(p) >= 2]
    if len(pts) < 2:
        base = [(float(p[0]), float(p[1])) for p in (baseline or []) if len(p) >= 2]
        if len(base) < 2:
            return None
        xs = [x for x, _ in base]
        ys = [y for _, y in base]
        # no polygon: take a generous band about the baseline (ascenders above)
        box = (min(xs), min(ys) - 4 * pad, max(xs), max(ys) + 1.5 * pad)
    else:
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        box = (min(xs), min(ys), max(xs), max(ys))
    left = max(0, int(box[0] - pad))
    top = max(0, int(box[1] - pad))
    right = min(width, int(math.ceil(box[2] + pad)))
    bottom = min(height, int(math.ceil(box[3] + pad)))
    if right - left < 2 or bottom - top < 2:
        return None
    return left, top, right, bottom


def crop_line(
    image_path: Path, polygon: Sequence | None, baseline: Sequence | None
) -> bytes | None:
    """PNG bytes of the line's crop from the cached page image (``None`` if impossible)."""
    from PIL import Image  # kraken's dependency; imported here so the store code stays light

    with Image.open(image_path) as im:
        box = crop_box(polygon, baseline, width=im.width, height=im.height)
        if box is None:
            return None
        crop = im.crop(box)
        if crop.width > CROP_MAX_WIDTH:
            scale = CROP_MAX_WIDTH / crop.width
            crop = crop.resize((CROP_MAX_WIDTH, max(1, int(crop.height * scale))))
        buf = io.BytesIO()
        crop.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()


def attach_images(conn: sqlite3.Connection, lines: Sequence[AuditLine], images_root: Path) -> None:
    """Fill each line's HTR text and crop from the store + image cache, in place."""
    for ln in lines:
        polygon, baseline, text = line_geometry(conn, ln.page_id, ln.line_seq)
        ln.htr_text = text
        page = db.get_page(conn, ln.page_id)
        if page is None:
            ln.image_note = "page not in the store"
            continue
        ln.label = page.label
        path = Path(images_root) / (page.local_path or local_relpath(page))
        if not path.exists():
            ln.image_note = f"page image not cached ({path.name})"
            continue
        if polygon is None and baseline is None:
            ln.image_note = "line has no geometry"
            continue
        try:
            ln.crop_png = crop_line(path, polygon, baseline)
        except OSError as exc:  # a truncated or unreadable cache file
            ln.image_note = f"image unreadable: {exc}"
            continue
        if ln.crop_png is None:
            ln.image_note = "line geometry outside the image"


def build_sheet(
    conn: sqlite3.Connection,
    *,
    images_root: Path,
    out_dir: Path,
    n: int = DEFAULT_N,
    seed: int = 0,
) -> AuditSheet:
    """Sample, crop, and write ``gt-audit.html`` + ``gt-audit-lines.csv`` into ``out_dir``."""
    lines = sample_lines(conn, n, seed=seed)
    attach_images(conn, lines, images_root)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "gt-audit.html"
    csv_path = out_dir / "gt-audit-lines.csv"
    html_path.write_text(render_sheet(lines, seed=seed), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "align_conf", "folio", "gt_text", "htr_text", "image"])
        for ln in lines:
            w.writerow(
                [
                    ln.ref,
                    ln.stratum,
                    "" if ln.align_conf is None else f"{ln.align_conf:.3f}",
                    ln.label or "",
                    ln.gt_text,
                    ln.htr_text or "",
                    "yes" if ln.crop_png else ln.image_note,
                ]
            )
    by_stratum: dict[str, int] = {}
    for ln in lines:
        by_stratum[ln.stratum] = by_stratum.get(ln.stratum, 0) + 1
    return AuditSheet(lines=lines, html_path=html_path, csv_path=csv_path, by_stratum=by_stratum)


_SHEET_CSS = """
body{font-family:system-ui,sans-serif;margin:1.5rem auto;max-width:1500px;
  padding:0 1rem;color:#222}
h1{font-size:1.4rem}
.help{background:#f4f4f0;border-left:4px solid #b59a3a;padding:.6rem 1rem;margin:1rem 0}
.item{border:1px solid #ccc;border-radius:6px;padding:.8rem 1rem;margin:1rem 0;background:#fff}
.item.done{border-color:#7a5}
.meta{font-size:.8rem;color:#666;margin-bottom:.4rem}
img{max-width:100%;border:1px solid #ddd;background:#fff;display:block;margin:.4rem 0}
.gt{font-size:1.15rem;font-family:Georgia,serif;margin:.4rem 0}
.htr{font-size:.9rem;color:#777;font-family:monospace}
.noimg{color:#a33;font-style:italic}
.verdicts{margin:.5rem 0}
.verdicts label{margin-right:1.2rem;cursor:pointer}
.note{width:60%;max-width:600px}
#toolbar{position:sticky;top:0;background:#fff;padding:.6rem 0;
  border-bottom:1px solid #ddd;z-index:2}
button{font-size:1rem;padding:.4rem .9rem;cursor:pointer}
"""

_SHEET_JS = """
const KEY = 'leibniz-gt-audit-' + document.body.dataset.seed;
function load(){
  try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){ return {}; }
}
function save(state){ try { localStorage.setItem(KEY, JSON.stringify(state)); } catch(e){} }
function refresh(){
  const state = load(); let done = 0;
  const items = document.querySelectorAll('.item');
  items.forEach(it => {
    const v = state[it.dataset.ref];
    it.classList.toggle('done', !!(v && v.verdict));
    if (v && v.verdict) done++;
  });
  document.getElementById('count').textContent = done + ' / ' + items.length + ' judged';
}
document.addEventListener('change', ev => {
  const it = ev.target.closest('.item'); if (!it) return;
  const state = load(); const cur = state[it.dataset.ref] || {};
  if (ev.target.type === 'radio') cur.verdict = ev.target.value;
  if (ev.target.classList.contains('note')) cur.note = ev.target.value;
  state[it.dataset.ref] = cur; save(state); refresh();
});
function restore(){
  const state = load();
  document.querySelectorAll('.item').forEach(it => {
    const v = state[it.dataset.ref]; if (!v) return;
    if (v.verdict) {
      const r = it.querySelector('input[value="' + v.verdict + '"]');
      if (r) r.checked = true;
    }
    if (v.note) it.querySelector('.note').value = v.note;
  });
  refresh();
}
function quote(c){ return '"' + String(c).replace(/"/g, '""') + '"'; }
function download(){
  const state = load(); const rows = [['ref','stratum','verdict','note']];
  document.querySelectorAll('.item').forEach(it => {
    const v = state[it.dataset.ref] || {};
    rows.push([it.dataset.ref, it.dataset.stratum, v.verdict || '', v.note || '']);
  });
  const csv = rows.map(r => r.map(quote).join(',')).join('\\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv'}));
  a.download = 'gt-audit-verdicts.csv'; a.click();
}
document.getElementById('dl').addEventListener('click', download);
restore();
"""


def render_sheet(lines: Sequence[AuditLine], *, seed: int = 0) -> str:
    """The self-contained audit page (crops inlined as data URIs)."""
    parts: list[str] = []
    A = parts.append
    A("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    A("<title>Leibniz Legible — GT hand audit</title>")
    A(f"<style>{_SHEET_CSS}</style></head><body data-seed='{seed}'>")
    A("<h1>Ground-truth hand audit</h1>")
    A(
        "<div class='help'>For each line, compare the <b>minted text</b> with the "
        "<b>image strip</b> and pick one:<br>"
        "<b>correct</b> — the text is what is written on this strip (spelling "
        "modernised, abbreviations expanded and punctuation changed are fine);<br>"
        "<b>boundary</b> — it is this line, but the text starts or ends a word or "
        "more early or late;<br>"
        "<b>wrong</b> — it is another line's text, or garbage;<br>"
        "<b>unreadable</b> — you cannot tell. The grey line is the machine "
        "reading of the same strip, for orientation only. Your choices are saved "
        "in this browser as you go; when done, click <b>Download verdicts</b>.</div>"
    )
    A("<div id='toolbar'><button id='dl'>Download verdicts (CSV)</button> ")
    A("<span id='count'></span></div>")
    for k, ln in enumerate(lines, start=1):
        ref = html.escape(ln.ref)
        A(f"<div class='item' data-ref='{ref}' data-stratum='{html.escape(ln.stratum)}'>")
        conf = "" if ln.align_conf is None else f" · conf {ln.align_conf:.2f}"
        folio = f" · fol. {html.escape(ln.label)}" if ln.label else ""
        A(
            f"<div class='meta'>#{k} · {ref} · {html.escape(ln.stratum)}{conf}{folio} · "
            f"{html.escape(ln.source)}</div>"
        )
        if ln.crop_png is not None:
            b64 = base64.b64encode(ln.crop_png).decode("ascii")
            A(f"<img src='data:image/png;base64,{b64}' alt='line image'>")
        else:
            A(f"<div class='noimg'>no image: {html.escape(ln.image_note or 'unknown')}</div>")
        A(f"<div class='gt'>{html.escape(ln.gt_text)}</div>")
        A(f"<div class='htr'>HTR: {html.escape(ln.htr_text or '—')}</div>")
        A("<div class='verdicts'>")
        for v in VERDICTS:
            A(f"<label><input type='radio' name='v-{k}' value='{v}'> {v}</label>")
        A("</div>")
        A("<input class='note' placeholder='note (optional)'>")
        A("</div>")
    A(f"<script>{_SHEET_JS}</script></body></html>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Scoring the returned verdicts
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class StratumScore:
    stratum: str
    n_judged: int = 0
    correct: int = 0
    boundary: int = 0
    wrong: int = 0
    unreadable: int = 0
    weight: float = 0.0  # share of gt_lines in this stratum

    @property
    def n_scored(self) -> int:
        """Lines that received a usable verdict (``unreadable`` is excluded)."""
        return self.correct + self.boundary + self.wrong

    @property
    def precision(self) -> float | None:
        return self.correct / self.n_scored if self.n_scored else None

    @property
    def usable(self) -> float | None:
        """Correct or merely boundary-off (still a weak training pair)."""
        return (self.correct + self.boundary) / self.n_scored if self.n_scored else None

    @property
    def interval(self) -> tuple[float, float] | None:
        return wilson(self.correct, self.n_scored) if self.n_scored else None


@dataclass(slots=True)
class AuditScore:
    by_stratum: dict[str, StratumScore]
    n_rows: int
    n_unjudged: int
    gate: float = GATE_PRECISION

    @property
    def pooled(self) -> StratumScore:
        tot = StratumScore("all")
        for s in self.by_stratum.values():
            tot.n_judged += s.n_judged
            tot.correct += s.correct
            tot.boundary += s.boundary
            tot.wrong += s.wrong
            tot.unreadable += s.unreadable
        return tot

    @property
    def weighted_precision(self) -> float | None:
        """Precision expected over the whole mint: strata weighted by their line share."""
        num = den = 0.0
        for s in self.by_stratum.values():
            if s.precision is not None and s.weight > 0:
                num += s.weight * s.precision
                den += s.weight
        return num / den if den else None

    @property
    def passes_gate(self) -> bool | None:
        p = self.weighted_precision
        return None if p is None else p >= self.gate


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for ``k`` successes in ``n`` trials."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def read_verdicts(path: Path) -> list[dict[str, str]]:
    """Rows of the downloaded verdict CSV (``ref, stratum, verdict, note``)."""
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if "ref" not in r or "verdict" not in r:
            raise ValueError("verdict CSV needs 'ref' and 'verdict' columns")
    return rows


def score_verdicts(
    rows: Sequence[dict[str, str]], weights: dict[str, int] | None = None
) -> AuditScore:
    """Tally verdict rows into per-stratum scores; ``weights`` are gt_lines counts."""
    by: dict[str, StratumScore] = {}
    unjudged = 0
    for r in rows:
        stratum = (r.get("stratum") or "unknown").strip() or "unknown"
        verdict = (r.get("verdict") or "").strip().lower()
        s = by.setdefault(stratum, StratumScore(stratum))
        if verdict not in VERDICTS:
            unjudged += 1
            continue
        s.n_judged += 1
        setattr(s, verdict, getattr(s, verdict) + 1)
    total = float(sum((weights or {}).values())) or 0.0
    for stratum, s in by.items():
        s.weight = ((weights or {}).get(stratum, 0) / total) if total else 1.0 / len(by)
    return AuditScore(by_stratum=by, n_rows=len(rows), n_unjudged=unjudged)


def render_score(score: AuditScore, *, sheet_note: str = "") -> str:
    """``reports/gt-audit.md``."""
    out: list[str] = []
    A = out.append
    A("# GT hand audit — C2 precision gate")
    A("")
    if sheet_note:
        A(sheet_note)
        A("")
    pooled = score.pooled
    wp = score.weighted_precision
    A(
        f"**{score.n_rows} lines on the sheet · {pooled.n_judged} judged · "
        f"{score.n_unjudged} left blank · {pooled.unreadable} unreadable.**"
    )
    A("")
    if wp is not None:
        verdict = "PASS" if score.passes_gate else "FAIL"
        A(
            f"**Corpus-weighted precision: {100 * wp:.1f} %** (strata weighted by their "
            f"share of minted lines) — gate ≥ {100 * score.gate:.0f} %: **{verdict}**."
        )
    else:
        A("No scored lines yet — fill in the sheet and download the verdicts.")
    A("")
    A("| stratum | judged | correct | boundary | wrong | precision | 95 % CI | usable | weight |")
    A("|---|---:|---:|---:|---:|---:|---|---:|---:|")
    for stratum in [*STRATA, *sorted(set(score.by_stratum) - set(STRATA))]:
        s = score.by_stratum.get(stratum)
        if s is None:
            continue
        p = "—" if s.precision is None else f"{100 * s.precision:.1f} %"
        ci = "—" if s.interval is None else f"{100 * s.interval[0]:.0f}–{100 * s.interval[1]:.0f} %"
        u = "—" if s.usable is None else f"{100 * s.usable:.1f} %"
        A(
            f"| {stratum} | {s.n_scored} | {s.correct} | {s.boundary} | {s.wrong} | {p} | {ci} | "
            f"{u} | {100 * s.weight:.1f} % |"
        )
    pp = "—" if pooled.precision is None else f"{100 * pooled.precision:.1f} %"
    pci = (
        "—"
        if pooled.interval is None
        else f"{100 * pooled.interval[0]:.0f}–{100 * pooled.interval[1]:.0f} %"
    )
    pu = "—" if pooled.usable is None else f"{100 * pooled.usable:.1f} %"
    A(
        f"| **pooled (unweighted)** | {pooled.n_scored} | {pooled.correct} | {pooled.boundary} | "
        f"{pooled.wrong} | {pp} | {pci} | {pu} | |"
    )
    A("")
    A(
        "*precision* = correct ÷ (correct + boundary + wrong); *usable* also counts "
        "boundary-off lines (the right line, a word or more off at an end). Intervals "
        "are Wilson 95 %. Equal numbers were drawn per stratum, so the pooled row "
        "over-represents the rare strata; the weighted figure is the one to read."
    )
    return "\n".join(out) + "\n"


__all__ = [
    "DEFAULT_N",
    "STRATA",
    "VERDICTS",
    "AuditLine",
    "AuditScore",
    "AuditSheet",
    "StratumScore",
    "allocate",
    "build_sheet",
    "crop_box",
    "read_verdicts",
    "render_score",
    "render_sheet",
    "sample_lines",
    "score_verdicts",
    "wilson",
]
