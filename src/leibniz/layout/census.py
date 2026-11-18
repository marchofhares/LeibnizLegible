"""The layout-zone census (P1 Task 3): PHILIUMM's v2 zones over the sample,
against this project's v1 lines.

Per page: the zones by class (and the share of the page each census group
covers), whether the page has any figure, formula or margin zone, where the
v1 lines fall (the group a line lies mostly in, by its pixels: main, margin,
numbering, figure, formula, artefact, or outside every zone), the pipeline's
own final lines by region type, and the v1 lines matched to the pipeline's
lines by polygon IoU (0.5, with 0.3 and 0.7 for the sensitivity). Per block
and over all: the same, aggregated. Prose is templated from the numbers;
nothing here is typed in.

The v1 lines are the store's current lines (one row per ``line_seq``: the
geometry is the segmentation run's whatever reader's text is current), in
the scan's pixels. The pipeline saw a copy of the scan downscaled to its
working size (rfdetr 1.8.0 upsamples the masks of its 300 queries to the
input image before thresholding, which spills the 6 GB card at the scans'
10–20 megapixels), so its zones and lines are scaled back to the scan's
pixels by the ratio of the page row's size to the image size the pipeline
recorded, per axis; the ratio is kept per page.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz import db
from leibniz.layout import zones as Z
from leibniz.layout.sample import SamplePage

IOU_MAIN = 0.5
IOU_SENSITIVITY = (0.3, 0.5, 0.7)
GROUPS = Z.GROUP_ORDER
LINE_GROUPS = GROUPS + ("outside",)
BLOCK_ORDER = ("briefwechsel", "handschriften", "lh35", "marginalien", "philiumm-test", "extra")
BLOCK_LABEL = {
    "briefwechsel": "Briefwechsel (correspondence)",
    "handschriften": "Handschriften (LH, without LH 35)",
    "lh35": "LH 35 (mathematics)",
    "marginalien": "Marginalien (annotated printed books)",
    "philiumm-test": "PHILIUMM's test pages",
    "extra": "named extra",
}


@dataclass(slots=True)
class PageCensus:
    page_id: str
    block: str
    sub: str
    work_id: str
    label: str
    file: str
    status: str  # ok | no_detections | no_final_lines
    image_width: int | None = None
    image_height: int | None = None
    size_agrees: bool | None = None  # pages.width/height == the image the pipeline saw
    scale: float | None = None  # scan pixels per pipeline pixel (x; y is within rounding)
    zones: dict[str, int] = field(default_factory=dict)  # class -> count
    zone_conf: dict[str, float] = field(default_factory=dict)  # class -> mean confidence
    area: dict[str, float] = field(default_factory=dict)  # group -> share of the page covered
    v1_lines: int = 0
    v1_by_group: dict[str, int] = field(default_factory=dict)
    their_lines: int = 0
    their_by_group: dict[str, int] = field(default_factory=dict)
    matched: dict[str, int] = field(default_factory=dict)  # "0.5" -> pairs
    matched_iou_mean: float | None = None

    def has(self, group: str) -> bool:
        return any(Z.zone_group(c) == group for c, n in self.zones.items() if n)


def _polygon_of(line: db.Line) -> list[Z.Point]:
    pts = line.polygon or []
    if len(pts) >= 3:
        return [(int(p[0]), int(p[1])) for p in pts]
    base = line.baseline or []
    if len(base) >= 2:  # a thin box around the baseline
        xs = [int(p[0]) for p in base]
        ys = [int(p[1]) for p in base]
        return [
            (min(xs), min(ys) - 10),
            (max(xs), min(ys) - 10),
            (max(xs), max(ys) + 4),
            (min(xs), max(ys) + 4),
        ]
    return []


def census_page(
    conn: sqlite3.Connection,
    sp: SamplePage,
    results_dir: Path,
    *,
    precedences: Mapping[int, int] | None = None,
) -> PageCensus:
    stem = Path(sp.file).stem
    pc = PageCensus(sp.page_id, sp.block, sp.sub, sp.work_id, sp.label, sp.file, "ok")
    pred = Path(results_dir) / "01_predictions_json" / "rf-detr" / f"{stem}.json"
    regions_xml = Z.find_output(results_dir, "03_regions_xml", stem)
    final_xml = Z.find_output(results_dir, "10_fixed_lines", stem)
    zones: list[Z.Zone] = []
    width = height = None
    if pred.exists():
        width, height, zones = Z.read_predictions_json(pred)
    elif regions_xml is not None:
        page = Z.read_page_xml(regions_xml)
        width, height, zones = page.width, page.height, page.zones
    else:
        pc.status = "no_detections"
    if (width is None or height is None) and regions_xml is not None:
        page = Z.read_page_xml(regions_xml)
        width, height = page.width, page.height
    pc.image_width, pc.image_height = width, height
    sx = sy = 1.0
    page_w, page_h = width, height
    if sp.width and sp.height and width and height:
        pc.size_agrees = (sp.width, sp.height) == (width, height)
        if not pc.size_agrees:
            sx, sy = sp.width / width, sp.height / height
            page_w, page_h = sp.width, sp.height
        pc.scale = round(sx, 4)
    zones = [z for z in zones if len(z.polygon) >= 3]
    if (sx, sy) != (1.0, 1.0):
        for z in zones:
            z.polygon = Z.scale_points(z.polygon, sx, sy)
    pc.zones = dict(Counter(z.cls or "?" for z in zones))
    confs: dict[str, list[float]] = defaultdict(list)
    for z in zones:
        if z.conf is not None:
            confs[z.cls or "?"].append(z.conf)
    pc.zone_conf = {c: round(sum(v) / len(v), 4) for c, v in confs.items()}

    lines = db.current_lines(conn, sp.page_id, precedences=precedences)
    polys = [p for p in (_polygon_of(ln) for ln in lines) if p]
    pc.v1_lines = len(polys)
    if page_w and page_h and zones:
        masks = Z.GroupMasks(page_w, page_h, zones)
        pc.area = {g: round(masks.area_share(g), 4) for g in GROUPS if g in masks.masks}
        homes = Counter(Z.home_group(masks.shares(p)) for p in polys)
    else:
        homes = Counter({"outside": len(polys)}) if polys else Counter()
    pc.v1_by_group = {g: homes.get(g, 0) for g in LINE_GROUPS if homes.get(g, 0)}

    if final_xml is not None:
        final = Z.read_page_xml(final_xml)
        theirs = [ln for ln in final.lines if len(ln.polygon) >= 3]
        pc.their_lines = len(theirs)
        pc.their_by_group = dict(Counter(ln.group for ln in theirs))
        if polys and theirs:
            their_polys = [
                Z.scale_points(ln.polygon, sx, sy) if (sx, sy) != (1.0, 1.0) else ln.polygon
                for ln in theirs
            ]
            for t in IOU_SENSITIVITY:
                pairs = Z.pair_by_iou(polys, their_polys, threshold=t)
                pc.matched[str(t)] = len(pairs)
                if t == IOU_MAIN and pairs:
                    pc.matched_iou_mean = round(sum(v for _, _, v in pairs) / len(pairs), 4)
    elif pc.status == "ok":
        pc.status = "no_final_lines"
    return pc


def census(
    conn: sqlite3.Connection, sample: Sequence[SamplePage], results_dir: Path, *, progress=None
) -> list[PageCensus]:
    prec = db.run_precedences(conn)
    out: list[PageCensus] = []
    for k, sp in enumerate(sample, start=1):
        if progress:
            progress(k, len(sample), sp.page_id)
        out.append(census_page(conn, sp, Path(results_dir), precedences=prec))
    return out


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


def _share(k: int, n: int) -> float | None:
    return round(k / n, 4) if n else None


def aggregate(pages: Sequence[PageCensus]) -> dict:
    n = len(pages)
    classes = sorted({c for p in pages for c in p.zones})
    zones_total = {c: sum(p.zones.get(c, 0) for p in pages) for c in classes}
    pages_with = {c: sum(1 for p in pages if p.zones.get(c, 0)) for c in classes}
    conf = {}
    for c in classes:
        vals = [p.zone_conf[c] for p in pages if c in p.zone_conf]
        conf[c] = round(sum(vals) / len(vals), 4) if vals else None
    v1 = sum(p.v1_lines for p in pages)
    v1_by = {g: sum(p.v1_by_group.get(g, 0) for p in pages) for g in LINE_GROUPS}
    theirs = sum(p.their_lines for p in pages)
    their_by = {g: sum(p.their_by_group.get(g, 0) for p in pages) for g in LINE_GROUPS}
    matched = {t: sum(p.matched.get(str(t), 0) for p in pages) for t in IOU_SENSITIVITY}
    ratios = [
        p.their_lines / p.v1_lines
        for p in pages
        if p.v1_lines and p.their_lines is not None and p.status == "ok"
    ]
    ious = [p.matched_iou_mean for p in pages if p.matched_iou_mean is not None]
    return {
        "pages": n,
        "pages_ok": sum(1 for p in pages if p.status == "ok"),
        "pages_no_detections": sum(1 for p in pages if p.status == "no_detections"),
        "pages_no_final_lines": sum(1 for p in pages if p.status == "no_final_lines"),
        "size_agrees": sum(1 for p in pages if p.size_agrees),
        "size_differs": sum(1 for p in pages if p.size_agrees is False),
        "zones": {
            c: {
                "total": zones_total[c],
                "per_page": round(zones_total[c] / n, 3) if n else None,
                "pages_with": pages_with[c],
                "pages_with_share": _share(pages_with[c], n),
                "conf_mean": conf[c],
            }
            for c in classes
        },
        "pages_with_group": {
            g: {"pages": (k := sum(1 for p in pages if p.has(g))), "share": _share(k, n)}
            for g in GROUPS
        },
        "area_mean": {
            g: round(statistics.fmean([p.area.get(g, 0.0) for p in pages]), 4) if n else None
            for g in GROUPS
        },
        "v1_lines": v1,
        "v1_by_group": {g: {"lines": v1_by[g], "share": _share(v1_by[g], v1)} for g in LINE_GROUPS},
        "v1_in_figure_or_formula": {
            "lines": v1_by["figure"] + v1_by["formula"],
            "share": _share(v1_by["figure"] + v1_by["formula"], v1),
        },
        "their_lines": theirs,
        "their_by_group": {
            g: {"lines": their_by[g], "share": _share(their_by[g], theirs)} for g in LINE_GROUPS
        },
        "their_to_v1": round(theirs / v1, 4) if v1 else None,
        "their_to_v1_median_page": round(statistics.median(ratios), 4) if ratios else None,
        "matched": {
            str(t): {
                "pairs": matched[t],
                "share_of_v1": _share(matched[t], v1),
                "share_of_theirs": _share(matched[t], theirs),
            }
            for t in IOU_SENSITIVITY
        },
        "matched_iou_mean": round(statistics.fmean(ious), 4) if ious else None,
    }


def summarize(pages: Sequence[PageCensus], meta: Mapping | None = None) -> dict:
    blocks: dict[str, list[PageCensus]] = defaultdict(list)
    for p in pages:
        blocks[p.block].append(p)
    out = {
        "generated": date.today().isoformat(),
        "meta": dict(meta or {}),
        "all": aggregate(pages),
        "blocks": {b: aggregate(blocks[b]) for b in BLOCK_ORDER if b in blocks},
    }
    for b in sorted(set(blocks) - set(BLOCK_ORDER)):
        out["blocks"][b] = aggregate(blocks[b])
    marg = blocks.get("marginalien", [])
    if marg:
        by_lang: dict[str, list[PageCensus]] = defaultdict(list)
        for p in marg:
            by_lang[p.sub or "unknown"].append(p)
        out["marginalien_by_lang"] = {lang: aggregate(by_lang[lang]) for lang in sorted(by_lang)}
    return out


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

CSV_FIELDS = (
    "page_id",
    "block",
    "sub",
    "work_id",
    "label",
    "file",
    "status",
    "image_width",
    "image_height",
    "size_agrees",
    "scale",
    "zones_total",
    "zones",
    "area",
    "v1_lines",
    "v1_by_group",
    "their_lines",
    "their_by_group",
    "matched_0.3",
    "matched_0.5",
    "matched_0.7",
    "matched_iou_mean",
)


def _kv(d: Mapping) -> str:
    return " ".join(f"{k}={v}" for k, v in sorted(d.items()))


def write_per_page(pages: Sequence[PageCensus], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_FIELDS)
        for p in pages:
            w.writerow(
                [
                    p.page_id,
                    p.block,
                    p.sub,
                    p.work_id,
                    p.label,
                    p.file,
                    p.status,
                    p.image_width,
                    p.image_height,
                    "" if p.size_agrees is None else ("yes" if p.size_agrees else "no"),
                    "" if p.scale is None else p.scale,
                    sum(p.zones.values()),
                    _kv(p.zones),
                    _kv(p.area),
                    p.v1_lines,
                    _kv(p.v1_by_group),
                    p.their_lines,
                    _kv(p.their_by_group),
                    p.matched.get("0.3", ""),
                    p.matched.get("0.5", ""),
                    p.matched.get("0.7", ""),
                    "" if p.matched_iou_mean is None else p.matched_iou_mean,
                ]
            )


def write_summary(summary: Mapping, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{100 * x:.1f} %"


def _n(x: int | float | None) -> str:
    if x is None:
        return "–"
    return f"{x:,}" if isinstance(x, int) else f"{x:,.2f}"


def _label(block: str) -> str:
    return "**all**" if block == "all" else BLOCK_LABEL.get(block, block)


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _setting(meta: Mapping, n_pages: int, generated: str) -> str:
    model = meta.get("model", "DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2")
    sha = str(meta.get("checkpoint_sha256", "?"))[:12]
    rev = str(meta.get("card_revision", "?"))[:12]
    commit = str(meta.get("pipeline_commit", "?"))[:12]
    return (
        f"PHILIUMM's RF-DETR-Seg model `{model}` (checkpoint `{meta.get('checkpoint', '?')}`, "
        f"SHA-256 `{sha}…`, card revision `{rev}`, licence "
        f"{meta.get('licence', 'CC BY-NC 4.0 on the card')}), run through her own pipeline "
        f"(GitLab commit `{commit}`) at resolution {meta.get('resolution', '?')} px and "
        f"detection threshold {meta.get('threshold', '?')}, over {_n(n_pages)} pages of this "
        f"project's store ({meta.get('sample', 'reports/layout/sample.csv')}), on {generated}. "
        "The kraken baselines inside her zones are the pipeline's bundled model, byte-identical "
        "to this project's v1 segmenter. The v1 lines are the store's current lines, in the "
        "scan's pixels; the pipeline's zones and lines are scaled back from the image size it "
        "worked on (the table below says where that size was the scan's)."
    )


def _sample_table(order: Sequence[str], blocks: Mapping, allb: Mapping) -> list[str]:
    L = [
        "| block | pages | with detections | with final lines | pipeline image at scan size |",
        "|---|---:|---:|---:|---:|",
    ]
    for b in [*order, "all"]:
        a = allb if b == "all" else blocks[b]
        detected = a["pages"] - a["pages_no_detections"]
        final = detected - a["pages_no_final_lines"]
        sized = a["size_agrees"] + a["size_differs"]
        L.append(
            _row(
                [
                    _label(b),
                    _n(a["pages"]),
                    _n(detected),
                    _n(final),
                    f"{_n(a['size_agrees'])} of {_n(sized)}",
                ]
            )
        )
    return L


def _zones_table(
    order: Sequence[str], blocks: Mapping, allb: Mapping, classes: Sequence[str]
) -> list[str]:
    L = [_row(["block", *classes]), "|---|" + "---:|" * len(classes)]
    for b in [*order, "all"]:
        a = allb if b == "all" else blocks[b]
        cells = [_label(b)]
        for c in classes:
            z = a["zones"].get(c)
            cells.append(
                "–" if z is None else f"{z['per_page']:.2f} · {_pct(z['pages_with_share'])}"
            )
        L.append(_row(cells))
    return L


def _groups_table(order: Sequence[str], blocks: Mapping, allb: Mapping) -> list[str]:
    L = [
        "| block | any figure zone | any formula zone | any margin zone | any main zone "
        "| page area under main · margin · figure · formula |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for b in [*order, "all"]:
        a = allb if b == "all" else blocks[b]
        g = a["pages_with_group"]
        ar = a["area_mean"]
        cells = [_label(b)]
        for grp in ("figure", "formula", "margin", "main"):
            cells.append(f"{_pct(g[grp]['share'])} ({_n(g[grp]['pages'])})")
        areas = [_pct(ar[g]) for g in ("main", "margin", "figure", "formula")]
        cells.append(" · ".join(areas))
        L.append(_row(cells))
    return L


def _v1_table(order: Sequence[str], blocks: Mapping, allb: Mapping) -> list[str]:
    groups = ("main", "margin", "numbering", "figure", "formula", "artefact", "outside")
    L = [
        "| block | v1 lines | main | margin | numbering | figure | formula | artefact | outside "
        "| **in figure or formula** |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for b in [*order, "all"]:
        a = allb if b == "all" else blocks[b]
        v = a["v1_by_group"]
        ff = a["v1_in_figure_or_formula"]
        cells = [_label(b), _n(a["v1_lines"])]
        cells.extend(f"{_n(v[g]['lines'])} ({_pct(v[g]['share'])})" for g in groups)
        cells.append(f"**{_n(ff['lines'])} ({_pct(ff['share'])})**")
        L.append(_row(cells))
    return L


def _marginalien_rows(a: Mapping, label: str) -> str:
    v = a["v1_by_group"]
    t = a["their_by_group"]
    other = a["v1_lines"] - v["main"]["lines"] - v["margin"]["lines"]
    return _row(
        [
            label,
            _n(a["pages"]),
            _n(a["v1_lines"]),
            f"{_n(v['main']['lines'])} ({_pct(v['main']['share'])})",
            f"{_n(v['margin']['lines'])} ({_pct(v['margin']['share'])})",
            _n(other),
            _n(a["their_lines"]),
            f"{_n(t['main']['lines'])} · {_n(t['margin']['lines'])}",
        ]
    )


def _match_table(order: Sequence[str], blocks: Mapping, allb: Mapping) -> list[str]:
    L = [
        "| block | v1 lines | their lines | theirs ÷ v1 | median per page | matched at IoU ≥ 0.5 "
        "| of v1 | of theirs | at ≥ 0.3 | at ≥ 0.7 | mean IoU of pairs |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for b in [*order, "all"]:
        a = allb if b == "all" else blocks[b]
        m5, m3, m7 = a["matched"]["0.5"], a["matched"]["0.3"], a["matched"]["0.7"]
        L.append(
            _row(
                [
                    _label(b),
                    _n(a["v1_lines"]),
                    _n(a["their_lines"]),
                    _n(a["their_to_v1"]),
                    _n(a["their_to_v1_median_page"]),
                    _n(m5["pairs"]),
                    _pct(m5["share_of_v1"]),
                    _pct(m5["share_of_theirs"]),
                    _n(m3["pairs"]),
                    _n(m7["pairs"]),
                    _n(a["matched_iou_mean"]),
                ]
            )
        )
    return L


_CAVEATS = (
    "- The zones are a model's output, not a judgement: the card gives validation AP 0.91 for "
    "MainZone, 0.62 for MarginTextZone, 0.55 for GraphicZone-figure and 0.08–0.19 for the three "
    "formula classes, so a formula count here is a lower bound of unknown tightness and a margin "
    "count carries that class's error.",
    "- A v1 line inside a figure or formula zone is a line the HTR read where there is no running "
    "text; the share is the part of the v1 text that a zone-aware pipeline would not have read.",
    "- Their line count against v1's compares two runs of one baseline model: the difference is "
    "the masking, the merge into zones, the clipping and the splitting, not a second segmenter.",
    "- The sample is drawn by work, not by page: a page from a long convolute weighs as much as a "
    "page from a short one.",
    "- Nothing here was measured against hand-drawn zones; the 18 test pages are her held-out "
    "set, judged by her, not here.",
)


def render(summary: Mapping) -> str:
    meta = summary.get("meta", {})
    blocks = summary["blocks"]
    allb = summary["all"]
    order = [b for b in BLOCK_ORDER if b in blocks] + [b for b in blocks if b not in BLOCK_ORDER]
    classes = sorted(allb["zones"])
    L: list[str] = []
    L.append("# Layout-zone census: PHILIUMM's v2 segmentation model over a sample of the Nachlass")
    L.append("")
    L.append(_setting(meta, allb["pages"], summary.get("generated", "")))
    L.append("")
    L.append("## The sample")
    L.append("")
    L.extend(_sample_table(order, blocks, allb))
    L.append("")
    L.append("## Zones per class")
    L.append("")
    L.append(
        "Zones per page (mean), and the share of pages with at least one zone of the class. "
        "The classes are the ones the model emitted."
    )
    L.append("")
    L.extend(_zones_table(order, blocks, allb, classes))
    L.append("")
    confs = [
        f"{c} {allb['zones'][c]['conf_mean']:.2f}"
        for c in classes
        if allb["zones"][c]["conf_mean"] is not None
    ]
    L.append("Mean detection confidence per class, over all pages: " + ", ".join(confs) + ".")
    L.append("")
    L.append("## Pages with a figure, a formula, a margin zone")
    L.append("")
    L.extend(_groups_table(order, blocks, allb))
    L.append("")
    L.append("## Where the v1 lines fall")
    L.append("")
    L.append(
        f"A v1 line is counted in the zone group that holds at least {int(Z.INSIDE_SHARE * 100)} % "
        "of its pixels (the largest such group); `outside` is a line no group holds to that share "
        "— outside every zone, or split between zones."
    )
    L.append("")
    L.extend(_v1_table(order, blocks, allb))
    L.append("")
    if "marginalien_by_lang" in summary:
        L.append("### The Marginalien: printed body against notes")
        L.append("")
        L.append(
            "On the annotated printed books, `MainZone` is the printed body and `MarginTextZone` "
            "the handwritten notes (the model was trained on manuscripts, not on print: the count "
            "is what it emits there). By the language the K4 pass gave the page's v1 text (`de` is "
            "German print, the Fraktur question):"
        )
        L.append("")
        L.append(
            "| language | pages | v1 lines | in main (print body) | in margin (notes) | elsewhere "
            "| their final lines | in main · in margin |"
        )
        L.append("|---|---:|---:|---:|---:|---:|---:|---|")
        m = summary["marginalien_by_lang"]
        for lang in sorted(m):
            L.append(_marginalien_rows(m[lang], lang))
        L.append(_marginalien_rows(blocks["marginalien"], "**all**"))
        L.append("")
    L.append("## v1 lines against the pipeline's final lines")
    L.append("")
    L.append(
        "The pipeline's final lines (`10_fixed_lines`) are the same kraken model's baselines run "
        "on the binarised scan with figure, formula and artefact zones erased, merged into the "
        "zones, clipped to their region and split where they crossed two. Matched: greedy "
        "one-to-one pairs by polygon IoU."
    )
    L.append("")
    L.extend(_match_table(order, blocks, allb))
    L.append("")
    by_type = [
        f"{g} {_n(allb['their_by_group'][g]['lines'])}"
        for g in GROUPS
        if allb["their_by_group"][g]["lines"]
    ]
    L.append("Their final lines by region type, over all pages: " + ", ".join(by_type) + ".")
    L.append("")
    L.append("## What this does and does not show")
    L.append("")
    L.extend(_CAVEATS)
    L.append("")
    L.append(
        "Files: `zone-census-summary.json` (every number above), `zone-census-per-page.csv` "
        "(one row a page), `sample.csv` (the sample), `philiumm-layout-pages.csv` (her training "
        "pages, kept out)."
    )
    return "\n".join(L) + "\n"


def pages_to_json(pages: Iterable[PageCensus]) -> list[dict]:
    return [asdict(p) for p in pages]


__all__ = [
    "BLOCK_LABEL",
    "BLOCK_ORDER",
    "CSV_FIELDS",
    "IOU_MAIN",
    "IOU_SENSITIVITY",
    "PageCensus",
    "aggregate",
    "census",
    "census_page",
    "render",
    "summarize",
    "write_per_page",
    "write_summary",
]
