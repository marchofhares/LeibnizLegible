"""M1 Task 1b — the print trial on the Marginalien (2026-11-17).

The annotated printed books hold the printed body of a book and, in its
margins, Leibniz's handwritten notes. The v1 run read both with a model
trained on his hand. The trial asks what a print layout model and a print
OCR model make of 100 of those pages (the Marginalien block of P1 Task 3's
census sample, 30 of them German print, the Fraktur question):

* zones from kraken 7 with the D-FINE region model trained on LADaS (37
  SegmOnto classes, among them ``MarginTextZone-ManuscriptAddendum``, the
  handwritten addition in a printed margin), run on the 2,000 px copies the
  census pipeline read, the coordinates scaled back to the scan's pixels;
* the printed-body share: of the page's area under print zones, and of the
  v1 lines that lie mostly inside print zones (the same pixel rule as the
  census) — against PHILIUMM's v2 zones on the same pages, where ``MainZone``
  is the printed body and ``MarginTextZone`` the notes;
* the overlap (IoU) of the v1 lines inside print zones with the print zones;
* 50 printed lines, 25 roman and 25 Fraktur, cut for the operator to
  transcribe (``print-sheet.html`` under ``data/print/``), and the OCR of
  every printed-body line with Gallicorpora+ (kraken, French print of the
  16th to 19th century) through a PAGE XML of the v1 lines, so the CER of
  the print model and of v1's handwriting model are measured on the same
  lines once the transcriptions are in.

Nothing is written to the store. The decision for the report is (a) read
the print with a print model and show it as such, (b) flag print and never
read it, or (c) a Latin or Fraktur print model is needed first.
"""

from __future__ import annotations

import csv
import json
import random
import sqlite3
import statistics
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from lxml import etree

from leibniz import db
from leibniz.htr.metrics import LineScore, cer, get_policy, score_line
from leibniz.layout import zones as Z
from leibniz.layout.sample import SamplePage

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
MANUSCRIPT = {"MarginTextZone-ManuscriptAddendum"}
OTHER = {"DigitizationArtefactZone", "DamageZone", "StampZone", "StampZone-Sticker"}
PRINT_PREFIXES = (
    "MainZone",
    "MarginTextZone",  # -Notes, -ContinuedNotes: printed marginal notes
    "RunningTitleZone",
    "NumberingZone",
    "QuireMarksZone",
    "DropCapitalZone",
    "TitlePageZone",
    "TableZone",
    "FigureZone",
    "GraphicZone",
    "FormZone",
    "AdvertisementZone",
    "MusicZone",
)
GROUPS = ("print", "manuscript", "other")
LINE_GROUPS = GROUPS + ("outside",)
MIN_SHEET_CHARS = 15


def print_group(cls: str | None) -> str:
    """A LADaS SegmOnto class → ``print`` (the printed book), ``manuscript``
    (a handwritten addition) or ``other`` (stamps, artefacts, damage)."""
    if cls is None:
        return "other"
    if cls in MANUSCRIPT:
        return "manuscript"
    if cls in OTHER:
        return "other"
    if cls.startswith(PRINT_PREFIXES):
        return "print"
    return "other"


def philiumm_group(cls: str | None) -> str:
    """PHILIUMM's v2 class on a printed book → the same three groups: MainZone
    the printed body, MarginTextZone the notes, the rest other."""
    g = Z.zone_group(cls)
    return {"main": "print", "margin": "manuscript"}.get(g, "other")


def type_of(lang: str | None) -> str:
    """The print type a page's language implies: German print is Fraktur,
    Latin and French print roman (the Marginalien's books; the K4 pass's
    verdict on the v1 text)."""
    return "fraktur" if lang == "de" else "roman"


# --------------------------------------------------------------------------- #
# Per page
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class LineCall:
    """One v1 line on a trial page: where the two zone models put it."""

    line_seq: int
    ladas: str  # print | manuscript | other | outside
    philiumm: str  # print | manuscript | other | outside | "" (no PHILIUMM zones)
    text: str
    conf: float | None


@dataclass(slots=True)
class PageTrial:
    page_id: str
    work_id: str
    label: str
    lang: str
    print_type: str
    file: str
    status: str  # ok | no_zones
    scale: float | None = None
    zones: dict[str, int] = field(default_factory=dict)  # LADaS class -> count
    area: dict[str, float] = field(default_factory=dict)  # group -> share of the page
    v1_lines: int = 0
    v1_by_group: dict[str, int] = field(default_factory=dict)  # LADaS groups
    v1_by_philiumm: dict[str, int] = field(default_factory=dict)
    agreement: dict[str, int] = field(default_factory=dict)  # "ladas|philiumm" -> lines
    iou_lines_print: float | None = None  # v1 print lines (union) vs the print zones
    iou_print_models: float | None = None  # LADaS print zones vs PHILIUMM main zones
    lines: list[LineCall] = field(default_factory=list)


def _v1_polygon(line: db.Line) -> list[Z.Point]:
    pts = line.polygon or []
    if len(pts) >= 3:
        return [(int(p[0]), int(p[1])) for p in pts]
    base = line.baseline or []
    if len(base) >= 2:
        xs = [int(p[0]) for p in base]
        ys = [int(p[1]) for p in base]
        return [
            (min(xs), min(ys) - 10),
            (max(xs), min(ys) - 10),
            (max(xs), max(ys) + 4),
            (min(xs), max(ys) + 4),
        ]
    return []


def _scaled_zones(
    page: Z.LayoutPage, width: int | None, height: int | None
) -> tuple[list[Z.Zone], float | None]:
    """The page's zones in the scan's pixels (scaled from the image kraken saw)."""
    zones = [z for z in page.zones if len(z.polygon) >= 3]
    scale = None
    if (
        width
        and height
        and page.width
        and page.height
        and (page.width, page.height) != (width, height)
    ):
        sx, sy = width / page.width, height / page.height
        scale = round(sx, 4)
        for z in zones:
            z.polygon = Z.scale_points(z.polygon, sx, sy)
    return zones, scale


def _union_iou(
    size: tuple[int, int], a: Sequence[Sequence[Z.Point]], b: Sequence[Sequence[Z.Point]]
) -> float | None:
    """IoU of two sets of polygons as pixel unions on a page of ``size``."""
    if not a or not b:
        return None
    from PIL import ImageChops

    scale = min(1.0, 4096 / max(size))
    sz = (max(1, round(size[0] * scale)), max(1, round(size[1] * scale)))
    ma = Z._draw(sz, [Z.scale_points(p, scale, scale) for p in a], (0, 0))
    mb = Z._draw(sz, [Z.scale_points(p, scale, scale) for p in b], (0, 0))
    inter = Z._count(ImageChops.darker(ma, mb))
    union = Z._count(ImageChops.lighter(ma, mb))
    return round(inter / union, 4) if union else None


def trial_page(
    conn: sqlite3.Connection,
    sp: SamplePage,
    zones_xml: Path | None,
    *,
    philiumm_json: Path | None = None,
    precedences: Mapping[int, int] | None = None,
) -> PageTrial:
    pt = PageTrial(
        sp.page_id, sp.work_id, sp.label, sp.sub or "unknown", type_of(sp.sub), sp.file, "ok"
    )
    if zones_xml is None or not Path(zones_xml).exists():
        pt.status = "no_zones"
        lines = db.current_lines(conn, sp.page_id, precedences=precedences)
        pt.v1_lines = len([ln for ln in lines if _v1_polygon(ln)])
        return pt
    page = Z.read_page_xml(zones_xml)
    zones, pt.scale = _scaled_zones(page, sp.width, sp.height)
    width, height = (sp.width or page.width or 1), (sp.height or page.height or 1)
    pt.zones = dict(Counter(z.cls or "?" for z in zones))
    ladas_masks = Z.GroupMasks(width, height, zones, group_of=print_group)
    pt.area = {g: round(ladas_masks.area_share(g), 4) for g in GROUPS if g in ladas_masks.masks}
    phil_masks = None
    phil_print: list[Sequence[Z.Point]] = []
    if philiumm_json is not None and Path(philiumm_json).exists():
        pw, ph, pzones = Z.read_predictions_json(philiumm_json)
        pzones = [z for z in pzones if len(z.polygon) >= 3]
        if pw and ph and (pw, ph) != (width, height):
            for z in pzones:
                z.polygon = Z.scale_points(z.polygon, width / pw, height / ph)
        phil_masks = Z.GroupMasks(width, height, pzones, group_of=philiumm_group)
        phil_print = [z.polygon for z in pzones if philiumm_group(z.cls) == "print"]
    lines = db.current_lines(conn, sp.page_id, precedences=precedences)
    print_polys: list[Sequence[Z.Point]] = []
    for ln in lines:
        poly = _v1_polygon(ln)
        if not poly:
            continue
        g = Z.home_group(ladas_masks.shares(poly))
        pg = Z.home_group(phil_masks.shares(poly)) if phil_masks is not None else ""
        pt.lines.append(LineCall(ln.line_seq, g, pg, ln.text or "", ln.conf))
        if g == "print":
            print_polys.append(poly)
    pt.v1_lines = len(pt.lines)
    pt.v1_by_group = dict(Counter(lc.ladas for lc in pt.lines))
    if phil_masks is not None:
        pt.v1_by_philiumm = dict(Counter(lc.philiumm for lc in pt.lines))
        pt.agreement = dict(Counter(f"{lc.ladas}|{lc.philiumm}" for lc in pt.lines))
    ladas_print = [z.polygon for z in zones if print_group(z.cls) == "print"]
    pt.iou_lines_print = _union_iou((width, height), print_polys, ladas_print)
    if phil_print:
        pt.iou_print_models = _union_iou((width, height), ladas_print, phil_print)
    return pt


def trial(
    conn: sqlite3.Connection,
    pages: Sequence[SamplePage],
    zones_dir: Path,
    *,
    philiumm_results: Path | None = None,
    progress=None,
) -> list[PageTrial]:
    prec = db.run_precedences(conn)
    out: list[PageTrial] = []
    for k, sp in enumerate(pages, start=1):
        if progress:
            progress(k, len(pages), sp.page_id)
        stem = Path(sp.file).stem
        xml = Z.find_output(zones_dir, "", stem) if zones_dir else None
        pj = None
        if philiumm_results is not None:
            cand = Path(philiumm_results) / "01_predictions_json" / "rf-detr" / f"{stem}.json"
            pj = cand if cand.exists() else None
        out.append(trial_page(conn, sp, xml, philiumm_json=pj, precedences=prec))
    return out


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


def _share(k: int, n: int) -> float | None:
    return round(k / n, 4) if n else None


def aggregate(pages: Sequence[PageTrial]) -> dict:
    n = len(pages)
    ok = [p for p in pages if p.status == "ok"]
    classes = sorted({c for p in ok for c in p.zones})
    v1 = sum(p.v1_lines for p in ok)
    by = {g: sum(p.v1_by_group.get(g, 0) for g in [g] for p in ok) for g in LINE_GROUPS}
    with_phil = [p for p in ok if p.v1_by_philiumm]
    v1_phil = sum(p.v1_lines for p in with_phil)
    by_phil = {g: sum(p.v1_by_philiumm.get(g, 0) for p in with_phil) for g in LINE_GROUPS}
    agree: Counter = Counter()
    for p in with_phil:
        agree.update(p.agreement)
    same = sum(v for k, v in agree.items() if k.split("|")[0] == k.split("|")[1])
    ious = [p.iou_lines_print for p in ok if p.iou_lines_print is not None]
    ious_models = [p.iou_print_models for p in with_phil if p.iou_print_models is not None]
    return {
        "pages": n,
        "pages_with_zones": len(ok),
        "pages_with_philiumm_zones": len(with_phil),
        "zones": {
            c: {
                "total": sum(p.zones.get(c, 0) for p in ok),
                "pages_with": (k := sum(1 for p in ok if p.zones.get(c))),
                "pages_with_share": _share(k, len(ok)),
                "group": print_group(c),
            }
            for c in classes
        },
        "area_mean": {
            g: round(statistics.fmean([p.area.get(g, 0.0) for p in ok]), 4) if ok else None
            for g in GROUPS
        },
        "pages_with_manuscript_zone": (m := sum(1 for p in ok if p.area.get("manuscript"))),
        "pages_with_manuscript_zone_share": _share(m, len(ok)),
        "v1_lines": v1,
        "v1_by_group": {g: {"lines": by[g], "share": _share(by[g], v1)} for g in LINE_GROUPS},
        "print_body_share_of_lines": _share(by["print"], v1),
        "philiumm": {
            "v1_lines": v1_phil,
            "v1_by_group": {
                g: {"lines": by_phil[g], "share": _share(by_phil[g], v1_phil)} for g in LINE_GROUPS
            },
            "print_body_share_of_lines": _share(by_phil["print"], v1_phil),
            "agreement": dict(sorted(agree.items())),
            "same_call": {"lines": same, "share": _share(same, v1_phil)},
            "iou_print_models_mean": round(statistics.fmean(ious_models), 4)
            if ious_models
            else None,
        },
        "iou_lines_print_mean": round(statistics.fmean(ious), 4) if ious else None,
        "iou_lines_print_median": round(statistics.median(ious), 4) if ious else None,
    }


def summarize(pages: Sequence[PageTrial], meta: Mapping | None = None) -> dict:
    by_type: dict[str, list[PageTrial]] = defaultdict(list)
    for p in pages:
        by_type[p.print_type].append(p)
    return {
        "generated": date.today().isoformat(),
        "meta": dict(meta or {}),
        "all": aggregate(pages),
        "by_type": {t: aggregate(by_type[t]) for t in sorted(by_type)},
    }


# --------------------------------------------------------------------------- #
# The sheet and the OCR input
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class SheetLine:
    ref: str
    page_id: str
    line_seq: int
    print_type: str
    lang: str
    v1_text: str


def select_sheet_lines(
    pages: Sequence[PageTrial],
    *,
    per_type: int = 25,
    seed: int = 0,
    min_chars: int = MIN_SHEET_CHARS,
) -> list[SheetLine]:
    """``per_type`` printed-body lines of each type (roman, Fraktur), spread
    over the pages (one a page a round), v1 text of at least ``min_chars``
    characters so the line is a line of print and not a fragment."""
    rng = random.Random(seed)
    out: list[SheetLine] = []
    for t in ("roman", "fraktur"):
        by_page: dict[str, list[SheetLine]] = {}
        for p in pages:
            if p.print_type != t:
                continue
            cands = [
                SheetLine(
                    f"{p.page_id}:{lc.line_seq:03d}", p.page_id, lc.line_seq, t, p.lang, lc.text
                )
                for lc in p.lines
                if lc.ladas == "print" and len(lc.text.strip()) >= min_chars
            ]
            if cands:
                rng.shuffle(cands)
                by_page[p.page_id] = cands
        order = sorted(by_page)
        rng.shuffle(order)
        picked: list[SheetLine] = []
        while len(picked) < per_type and any(by_page.values()):
            for pid in order:
                if len(picked) >= per_type:
                    break
                if by_page[pid]:
                    picked.append(by_page[pid].pop())
        out.extend(picked)
    return out


def write_sheet_lines(lines: Sequence[SheetLine], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "page_id", "line_seq", "type", "lang", "v1_text"])
        for ln in lines:
            w.writerow([ln.ref, ln.page_id, ln.line_seq, ln.print_type, ln.lang, ln.v1_text])


def read_sheet_lines(path: Path) -> list[SheetLine]:
    out: list[SheetLine] = []
    with Path(path).open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append(
                SheetLine(
                    r["ref"], r["page_id"], int(r["line_seq"]), r["type"], r["lang"], r["v1_text"]
                )
            )
    return out


_SHEET_CSS = """
body{font:15px/1.4 system-ui,sans-serif;margin:1.5rem;max-width:1100px}
img{max-width:100%;display:block;border:1px solid #ccc;background:#fff}
.line{margin:1.2rem 0;padding:.6rem;border:1px solid #ddd;border-radius:6px}
.meta{color:#555;font-size:.85em}
input[type=text]{width:100%;font:16px/1.3 serif;padding:.3rem;margin-top:.4rem}
button{font-size:1em;padding:.4rem .9rem}
"""

_SHEET_JS = """
const KEY = 'print-sheet-' + document.body.dataset.seed;
const inputs = [...document.querySelectorAll('input[type=text]')];
try { const saved = JSON.parse(localStorage.getItem(KEY) || '{}');
  for (const i of inputs) if (saved[i.name] !== undefined) i.value = saved[i.name]; } catch (e) {}
function persist(){ const d = {}; for (const i of inputs) d[i.name] = i.value;
  try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }
inputs.forEach(i => i.addEventListener('input', persist));
function quote(s){ return '"' + String(s).replace(/"/g, '""') + '"'; }
function download(){
  const rows = [['ref','type','transcription']];
  for (const i of inputs) rows.push([i.name, i.dataset.type, i.value]);
  const csv = rows.map(r => r.map(quote).join(',')).join('\\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\\ufeff' + csv], {type: 'text/csv;charset=utf-8'}));
  a.download = 'print-sheet-transcriptions.csv'; a.click();
}
document.getElementById('dl').addEventListener('click', download);
"""


def render_sheet(
    lines: Sequence[SheetLine], crops: Mapping[str, bytes | None], *, seed: int = 0
) -> str:
    """The HTML sheet: each printed line as a crop with a text field; a button
    downloads ``ref, type, transcription`` as CSV (saved in the browser's
    storage meanwhile). The v1 reading is not shown, so it cannot lead the
    hand."""
    import base64
    import html

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<title>Print sheet: 50 printed lines of the Marginalien</title>",
        f"<style>{_SHEET_CSS}</style></head><body data-seed='{seed}'>",
        "<h1>Fifty printed lines</h1>",
        "<p>Type each line as printed, letter for letter: long s as ſ if you can, ligatures as "
        "they stand, abbreviations as written, the hyphen at a line's end kept. Leave a field "
        "empty for a crop that is not a line of print. Roman type first, then Fraktur. "
        "The fields are kept in this browser until you download the CSV.</p>",
        "<p><button id='dl'>Download the CSV</button></p>",
    ]
    for k, ln in enumerate(lines, start=1):
        png = crops.get(ln.ref)
        img = (
            f"<img src='data:image/png;base64,{base64.b64encode(png).decode('ascii')}' alt=''>"
            if png
            else "<p class='meta'>(no crop)</p>"
        )
        parts.append(
            f"<div class='line'><div class='meta'>{k}. {html.escape(ln.ref)} · {ln.print_type} · "
            f"page language {html.escape(ln.lang)}</div>{img}"
            f"<input type='text' name='{html.escape(ln.ref)}' data-type='{ln.print_type}' "
            "autocomplete='off' spellcheck='false'></div>"
        )
    parts.append(f"<script>{_SHEET_JS}</script></body></html>")
    return "\n".join(parts)


def crops_for(
    conn: sqlite3.Connection, lines: Sequence[SheetLine], images_root: Path
) -> dict[str, bytes | None]:
    """The lines' crops from the full-resolution cached scans, one page opened once."""
    from PIL import Image

    from leibniz.align.audit import crop_from_image, line_geometry
    from leibniz.images.fetch import local_relpath

    out: dict[str, bytes | None] = {}
    by_page: dict[str, list[SheetLine]] = defaultdict(list)
    for ln in lines:
        by_page[ln.page_id].append(ln)
    for pid, lns in by_page.items():
        page = db.get_page(conn, pid)
        if page is None:
            for ln in lns:
                out[ln.ref] = None
            continue
        path = Path(images_root) / (page.local_path or local_relpath(page))
        if not path.exists():
            for ln in lns:
                out[ln.ref] = None
            continue
        with Image.open(path) as im:
            for ln in lns:
                polygon, baseline, _ = line_geometry(conn, pid, ln.line_seq)
                out[ln.ref] = crop_from_image(im, polygon, baseline, max_width=1400)
    return out


def write_ocr_input(
    conn: sqlite3.Connection,
    pt: PageTrial,
    image_path: Path,
    out_xml: Path,
    *,
    groups: Iterable[str] = ("print",),
    precedences: Mapping[int, int] | None = None,
) -> int:
    """A PAGE XML of the page's v1 lines in the given LADaS groups (polygon and
    baseline, in the scan's pixels, ids ``{page_id}:{seq:03d}``) for
    ``kraken -f page … ocr``; returns the number of lines written."""
    wanted = {lc.line_seq for lc in pt.lines if lc.ladas in set(groups)}
    lines = [
        ln
        for ln in db.current_lines(conn, pt.page_id, precedences=precedences)
        if ln.line_seq in wanted
    ]
    page = db.get_page(conn, pt.page_id)
    root = etree.Element("PcGts", nsmap={None: PAGE_NS})
    pg = etree.SubElement(
        root,
        "Page",
        imageFilename=str(Path(image_path).resolve()),
        imageWidth=str(page.width if page and page.width else 0),
        imageHeight=str(page.height if page and page.height else 0),
    )
    region = etree.SubElement(pg, "TextRegion", id="print", custom="structure {type:MainZone;}")
    etree.SubElement(
        region,
        "Coords",
        points=" ".join(
            f"{x},{y}"
            for x, y in [
                (0, 0),
                (page.width or 0, 0),
                (page.width or 0, page.height or 0),
                (0, page.height or 0),
            ]
        ),
    )
    n = 0
    for ln in lines:
        poly = _v1_polygon(ln)
        if not poly:
            continue
        tl = etree.SubElement(region, "TextLine", id=f"{pt.page_id}:{ln.line_seq:03d}")
        etree.SubElement(tl, "Coords", points=" ".join(f"{x},{y}" for x, y in poly))
        base = ln.baseline or []
        if len(base) >= 2:
            etree.SubElement(
                tl, "Baseline", points=" ".join(f"{int(p[0])},{int(p[1])}" for p in base)
            )
        n += 1
    out_xml.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(root).write(
        str(out_xml), encoding="utf-8", xml_declaration=True, pretty_print=True
    )
    return n


def read_ocr_texts(xml_path: Path) -> dict[str, str]:
    """``line id → text`` of a kraken PAGE XML output."""
    from leibniz.align.pagexml import parse_page_xml

    doc = parse_page_xml(Path(xml_path))
    return {ln.id: ln.text for ln in doc.lines}


# --------------------------------------------------------------------------- #
# The CER
# --------------------------------------------------------------------------- #


# The operator's conventions for the sheet (18 November 2026): ſ, æ, u and v as
# printed, & as &, the line-end double hyphen written "-", abbreviation marks
# (ē, ã) present or not — so both sides are folded before scoring: the marks
# dropped, the hyphenation signs Gallicorpora+ writes (¬, ⸗) read as "-", the
# typographic apostrophe as the plain one. Nothing else is touched.
ABBREVIATION_MARKS = frozenset({"\u0304", "\u0303", "\u0305"})  # macron, tilde, overline
FOLDS = "abbreviation marks (macron, tilde, overline) dropped; ¬ and ⸗ read as -; ’ as '"


def fold_print_marks(text: str) -> str:
    """The print trial's fold of a transcription or a reading before the CER."""
    out = []
    for ch in unicodedata.normalize("NFD", text):
        if ch in ABBREVIATION_MARKS:
            continue
        out.append({"¬": "-", "⸗": "-", "’": "'"}.get(ch, ch))
    return unicodedata.normalize("NFC", "".join(out))


def read_transcriptions(path: Path) -> dict[str, str]:
    """The operator's CSV from the sheet (``ref, type, transcription``)."""
    out: dict[str, str] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if (r.get("transcription") or "").strip():
                out[r["ref"]] = r["transcription"]
    return out


def score(
    refs: Mapping[str, str],
    hyps: Mapping[str, str],
    lines: Sequence[SheetLine],
    *,
    policy: str = "philiumm",
    fold: bool = True,
) -> dict:
    """CER of ``hyps`` against the operator's ``refs`` over the sheet's lines,
    by print type and in all, under the named normalisation policy and, with
    ``fold``, the trial's fold of both sides (:func:`fold_print_marks`; the
    unfolded CER is kept beside it); the lines without a transcription or a
    hypothesis are counted, not scored, and a type without a scored line is
    listed as pending."""
    pol = get_policy(policy)
    scores: dict[str, list[LineScore]] = defaultdict(list)
    raw: dict[str, list[LineScore]] = defaultdict(list)
    missing = 0
    for ln in lines:
        ref = refs.get(ln.ref)
        if not ref:
            continue
        hyp = hyps.get(ln.ref)
        if hyp is None:
            missing += 1
            continue
        raw[ln.print_type].append(score_line(ref, hyp, pol, line_id=ln.ref))
        if fold:
            ref, hyp = fold_print_marks(ref), fold_print_marks(hyp)
        scores[ln.print_type].append(score_line(ref, hyp, pol, line_id=ln.ref))
    allscores = [s for v in scores.values() for s in v]
    allraw = [s for v in raw.values() for s in v]
    types = sorted({ln.print_type for ln in lines} | set(scores))
    return {
        "policy": pol.describe() + (f"; then {FOLDS}" if fold else ""),
        "lines_transcribed": sum(1 for ln in lines if refs.get(ln.ref)),
        "lines_scored": len(allscores),
        "lines_without_hypothesis": missing,
        "cer": round(cer(allscores), 4) if allscores else None,
        "cer_unfolded": round(cer(allraw), 4) if allraw else None,
        "by_type": {
            t: {
                "lines": len(scores.get(t, [])),
                "cer": round(cer(scores[t]), 4) if scores.get(t) else None,
                "cer_unfolded": round(cer(raw[t]), 4) if raw.get(t) else None,
                "pending": not scores.get(t),
            }
            for t in types
        },
        "lines": [
            {"ref": s.line_id, "type": t, "cer": round(s.cer, 4), "ref_text": s.ref, "hyp": s.hyp}
            for t, v in sorted(scores.items())
            for s in v
        ],
    }


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #


def write_pages_csv(pages: Sequence[SamplePage], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "page_id",
                "work_id",
                "shelfmark",
                "label",
                "lang",
                "print_type",
                "width",
                "height",
                "n_lines",
                "file",
            ]
        )
        for p in pages:
            w.writerow(
                [
                    p.page_id,
                    p.work_id,
                    p.shelfmark,
                    p.label,
                    p.sub,
                    type_of(p.sub),
                    p.width,
                    p.height,
                    p.n_lines,
                    p.file,
                ]
            )


def write_per_page(pages: Sequence[PageTrial], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "page_id",
                "lang",
                "print_type",
                "status",
                "scale",
                "zones",
                "area_print",
                "area_manuscript",
                "v1_lines",
                "v1_print",
                "v1_manuscript",
                "v1_other",
                "v1_outside",
                "philiumm_print",
                "philiumm_manuscript",
                "same_call",
                "iou_lines_print",
                "iou_print_models",
            ]
        )
        for p in pages:
            same = sum(v for k, v in p.agreement.items() if k.split("|")[0] == k.split("|")[1])
            w.writerow(
                [
                    p.page_id,
                    p.lang,
                    p.print_type,
                    p.status,
                    "" if p.scale is None else p.scale,
                    " ".join(f"{k}={v}" for k, v in sorted(p.zones.items())),
                    p.area.get("print", ""),
                    p.area.get("manuscript", ""),
                    p.v1_lines,
                    p.v1_by_group.get("print", 0),
                    p.v1_by_group.get("manuscript", 0),
                    p.v1_by_group.get("other", 0),
                    p.v1_by_group.get("outside", 0),
                    p.v1_by_philiumm.get("print", ""),
                    p.v1_by_philiumm.get("manuscript", ""),
                    same if p.agreement else "",
                    "" if p.iou_lines_print is None else p.iou_lines_print,
                    "" if p.iou_print_models is None else p.iou_print_models,
                ]
            )


def write_lines_csv(pages: Sequence[PageTrial], path: Path) -> None:
    """Every v1 line's call by both models (the bulky file, under data/)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "page_id", "print_type", "ladas", "philiumm", "conf", "v1_text"])
        for p in pages:
            for lc in p.lines:
                w.writerow(
                    [
                        f"{p.page_id}:{lc.line_seq:03d}",
                        p.page_id,
                        p.print_type,
                        lc.ladas,
                        lc.philiumm,
                        lc.conf,
                        lc.text,
                    ]
                )


def pages_to_json(pages: Iterable[PageTrial]) -> list[dict]:
    out = []
    for p in pages:
        d = asdict(p)
        d.pop("lines", None)
        out.append(d)
    return out


def write_json(obj, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


__all__ = [
    "GROUPS",
    "LINE_GROUPS",
    "LineCall",
    "PageTrial",
    "FOLDS",
    "SheetLine",
    "aggregate",
    "fold_print_marks",
    "crops_for",
    "philiumm_group",
    "print_group",
    "read_ocr_texts",
    "read_sheet_lines",
    "read_transcriptions",
    "render_sheet",
    "score",
    "select_sheet_lines",
    "summarize",
    "trial",
    "trial_page",
    "type_of",
    "write_lines_csv",
    "write_ocr_input",
    "write_pages_csv",
    "write_per_page",
    "write_sheet_lines",
    "write_json",
]
