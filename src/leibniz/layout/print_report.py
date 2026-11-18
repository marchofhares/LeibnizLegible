"""The print trial's report (M1 Task 1b): ``reports/marginalia/print-trial.md``
from the trial's summary, with the decision the amendment of 13 October asks
for — (a) the print is read with a print model and shown as such, (b) print
is flagged and never read, (c) a Latin or Fraktur print model is needed
first. Prose templated from the numbers; the CER section says "pending"
until the operator's transcriptions are in.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence

from leibniz import db
from leibniz.align.audit_reach import MARGINALIEN_SET

# The thresholds of the decision, stated here and in the report.
CER_READABLE = 0.10  # a print model reads a type at or under this: (a) for that type
CER_UNUSABLE = 0.30  # above this the model's reading is noise: (c) for that type


def fraktur_share(conn: sqlite3.Connection) -> dict:
    """The Marginalien's German-print pages by the K4 language pass: the
    corpus's Fraktur share, as far as a page's language says its type."""
    if not db.has_table(conn, "page_lang"):
        return {}
    rows = conn.execute(
        """
        SELECT pl.lang, COUNT(*) AS n
        FROM page_lang pl JOIN pages p ON p.page_id = pl.page_id
        JOIN works w ON w.gwlb_object_id = p.work_id
        WHERE w.set_name = ?
        GROUP BY pl.lang
        """,
        (MARGINALIEN_SET,),
    ).fetchall()
    counts = {r["lang"]: int(r["n"]) for r in rows}
    total = sum(counts.values())
    return {
        "pages_by_lang": counts,
        "pages": total,
        "german_pages": counts.get("de", 0),
        "german_share": round(counts.get("de", 0) / total, 4) if total else None,
    }


def decision(summary: Mapping) -> tuple[str, str]:
    """``(letter, sentence)``: the decision from the CER by type; a type
    without a scored line is pending and the decision is provisional."""
    cer = (summary.get("cer") or {}).get("gallicorpora") or {}
    by_type = cer.get("by_type") or {}
    scored = {t: v["cer"] for t, v in by_type.items() if v.get("cer") is not None}
    pending = [t for t in ("roman", "fraktur") if t not in scored]
    if not scored:
        return (
            "pending",
            "The decision waits for the CER: the sheet of 50 printed lines is rendered, the "
            "transcriptions are not in; the zone numbers above stand on their own.",
        )
    verdicts = {
        t: ("a" if c <= CER_READABLE else ("b" if c <= CER_UNUSABLE else "c"))
        for t, c in scored.items()
    }
    parts = ", ".join(f"{t} {scored[t]:.1%} → ({v})" for t, v in sorted(verdicts.items()))
    words = {
        "a": "the printed body is read with a print model and shown as such",
        "b": "print is flagged and not read with this model",
        "c": "a print model for this material is needed first",
    }
    if len(set(verdicts.values())) == 1:
        letter = next(iter(verdicts.values()))
        sentence = f"({letter}) {words[letter]}: {parts} on the sheet."
    else:
        letter = "/".join(sorted(set(verdicts.values())))
        sentence = (
            f"split by type ({parts}): read the type the model reads at or under "
            f"{CER_READABLE:.0%} with it and show it as print; flag the other and read it only "
            "when a model for it exists."
        )
    if pending:
        letter += " (" + ", ".join(pending) + " pending)"
        sentence += (
            f" The {' and '.join(pending)} half of the sheet is not transcribed yet, so this "
            "holds for the type scored; the other type's decision follows its transcription."
        )
    return letter, sentence


def _pct(x) -> str:
    return "–" if x is None else f"{100 * float(x):.1f} %"


def _n(x) -> str:
    if x is None:
        return "–"
    return f"{x:,}" if isinstance(x, int) else f"{x:,.2f}"


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _setting(meta: Mapping, summary: Mapping) -> str:
    allb = summary["all"]
    return (
        f"M1 Task 1b, run {summary.get('generated', '')} on the desktop, the store read-only. "
        f"The pages are the Marginalien block of the zone census sample ({_n(allb['pages'])} "
        f"pages of {meta.get('works', '?')} annotated printed books, drawn one page a book, 30 "
        "of them German print by the K4 language pass, the Fraktur question). Zones: kraken "
        f"{meta.get('kraken', '7.1.1')} with the D-FINE large region model trained on LADaS "
        f"(37 SegmOnto classes, Apache-2.0; `{meta.get('ladas_model', 'ladas_l.safetensors')}`, "
        f"MD5 `{str(meta.get('ladas_md5', ''))[:12]}`), device {meta.get('device', 'cuda:0')}, "
        "on the census's 2,000 px copies, the coordinates scaled back to the scan. The "
        "printed-body lines are the store's v1 lines that lie mostly (half their pixels or "
        "more) inside a print zone; the OCR model is Gallicorpora+ (kraken, French print of "
        "the 16th to 19th century, release 1.0.0, CC0 repository) run through a PAGE XML of "
        "those lines on the full-resolution scan."
    )


def _zone_table(allb: Mapping) -> list[str]:
    L = ["| class | group | zones | pages with it |", "|---|---|---:|---:|"]
    for c, z in sorted(allb["zones"].items(), key=lambda kv: (-kv[1]["total"], kv[0])):
        pages = f"{_n(z['pages_with'])} ({_pct(z['pages_with_share'])})"
        L.append(_row([c, z["group"], _n(z["total"]), pages]))
    return L


def _share_table(types: Mapping, allb: Mapping) -> list[str]:
    L = [
        "| type | pages | v1 lines | in print zones | in manuscript zones | other zones | outside "
        "| IoU of the print lines with the print zones (mean · median) |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, a in [*sorted(types.items()), ("**all**", allb)]:
        v = a["v1_by_group"]
        L.append(
            _row(
                [
                    name,
                    _n(a["pages"]),
                    _n(a["v1_lines"]),
                    f"{_n(v['print']['lines'])} ({_pct(v['print']['share'])})",
                    f"{_n(v['manuscript']['lines'])} ({_pct(v['manuscript']['share'])})",
                    _n(v["other"]["lines"]),
                    _n(v["outside"]["lines"]),
                    f"{_n(a['iou_lines_print_mean'])} · {_n(a['iou_lines_print_median'])}",
                ]
            )
        )
    return L


def _philiumm_section(allb: Mapping) -> list[str]:
    ph = allb["philiumm"]
    if not ph["v1_lines"]:
        return []
    L = ["### Against PHILIUMM's v2 zones on the same pages", ""]
    L.append(
        "PHILIUMM's model (trained on manuscripts) calls `MainZone` where LADaS calls the "
        "printed body and `MarginTextZone` where LADaS calls a manuscript addendum. On the "
        f"{_n(ph['v1_lines'])} v1 lines of the pages both models saw: print by PHILIUMM "
        f"{_pct(ph['print_body_share_of_lines'])}, by LADaS "
        f"{_pct(allb['print_body_share_of_lines'])}; the same call on "
        f"{_n(ph['same_call']['lines'])} lines ({_pct(ph['same_call']['share'])}); the IoU of "
        f"the two models' print areas {_n(ph['iou_print_models_mean'])} (mean over pages)."
    )
    L.append("")
    L.append("| LADaS \\\\ PHILIUMM | lines |")
    L.append("|---|---:|")
    for k, v in sorted(ph["agreement"].items(), key=lambda kv: -kv[1]):
        a_, b_ = k.split("|")
        L.append(f"| {a_} \\\\ {b_ or 'none'} | {_n(v)} |")
    L.append("")
    return L


def _cer_section(summary: Mapping, meta: Mapping) -> list[str]:
    cer = summary.get("cer")
    L: list[str] = []
    if cer:
        L.append("| model | lines scored | CER (all) | roman | Fraktur |")
        L.append("|---|---:|---:|---:|---:|")
        rows = (("Gallicorpora+ (print)", "gallicorpora"), ("v1, the handwriting model", "v1"))
        for name, key in rows:
            r = cer.get(key) or {}
            bt = r.get("by_type", {})
            cells = [name, _n(r.get("lines_scored")), _pct(r.get("cer"))]
            for t in ("roman", "fraktur"):
                v = bt.get(t) or {}
                if v.get("cer") is None:
                    cells.append("pending")
                else:
                    cells.append(f"{_pct(v['cer'])} ({_n(v['lines'])} lines)")
            L.append(_row(cells))
        L.append("")
        g = cer.get("gallicorpora", {})
        v1 = cer.get("v1", {})
        L.append(
            f"Normalisation: {g.get('policy', '')}. The operator's transcriptions "
            f"({cer.get('transcriptions', '')}) are the reference; "
            f"{_n(g.get('lines_transcribed'))} of the 50 lines carry one. Without the fold the "
            f"CER is {_pct(g.get('cer_unfolded'))} for Gallicorpora+ and "
            f"{_pct(v1.get('cer_unfolded'))} for v1."
        )
    else:
        L.append(
            "**Pending.** The sheet of 50 printed lines (25 roman, 25 Fraktur) is at "
            f"`{meta.get('sheet', 'data/print/print-sheet.html')}`; Gallicorpora+ has read "
            f"{_n(summary.get('ocr_lines'))} printed-body lines. When the transcriptions are in:"
        )
        L.append("")
        L.append("```bash")
        L.append("uv run leibniz layout print-trial cer --transcriptions <the downloaded CSV>")
        L.append("uv run leibniz layout print-trial report")
        L.append("```")
    return L


_CAVEATS = (
    "- The LADaS model was trained on French print of the 17th century to the present; its "
    "per-class scores on its own test set are low for several classes (the README beside the "
    "model). A zone here is its guess.",
    "- The printed-body share is a share of v1 lines, which the handwriting segmenter drew; a "
    "printed line it split or merged counts as the segmenter left it.",
    "- Fifty lines decide the CER within a few points at best; the roman and Fraktur halves are "
    "25 lines each.",
    "- Nothing was written to the store; the tools' licences are in the registry "
    "(`leibniz legal licences`).",
)


def render(summary: Mapping) -> str:
    meta = summary.get("meta", {})
    allb = summary["all"]
    types = summary.get("by_type", {})
    _, sentence = decision(summary)
    L: list[str] = []
    L.append(
        "# The print trial: a print layout model and a print OCR model on 100 Marginalien pages"
    )
    L.append("")
    L.append(_setting(meta, summary))
    L.append("")
    L.append("## Decision")
    L.append("")
    L.append(f"**{sentence}**")
    L.append("")
    L.append("## Zones per class")
    L.append("")
    L.extend(_zone_table(allb))
    L.append("")
    L.append(
        f"Pages with zones: {_n(allb['pages_with_zones'])} of {_n(allb['pages'])}. Pages with a "
        "`MarginTextZone-ManuscriptAddendum` zone, the class for a handwritten addition in a "
        f"printed margin: {_n(allb['pages_with_manuscript_zone'])} "
        f"({_pct(allb['pages_with_manuscript_zone_share'])}). Mean page area under print zones "
        f"{_pct(allb['area_mean'].get('print'))}, under manuscript zones "
        f"{_pct(allb['area_mean'].get('manuscript'))}."
    )
    L.append("")
    L.append("## The printed-body share")
    L.append("")
    L.extend(_share_table(types, allb))
    L.append("")
    L.extend(_philiumm_section(allb))
    L.append("## The Fraktur share")
    L.append("")
    fs = summary.get("fraktur_share_corpus") or {}
    if fs:
        german = f"{_n(fs['german_pages'])} pages German ({_pct(fs['german_share'])})"
        L.append(
            f"Over the Marginalien in the store ({_n(fs['pages'])} pages with a language verdict), "
            f"the K4 pass calls {german}: "
            "German print in these books is Fraktur as a rule, Latin and French print roman, so "
            "that share is the corpus's Fraktur share as far as a page's language says its type. "
            "The sample holds 30 German pages on purpose."
        )
    L.append("")
    L.append("## The CER on 50 printed lines")
    L.append("")
    L.extend(_cer_section(summary, meta))
    L.append("")
    L.append("## What this does and does not show")
    L.append("")
    L.extend(_CAVEATS)
    L.append("")
    L.append(
        "Files: `print-trial-summary.json`, `print-trial-per-page.csv`, `print-trial-pages.csv`; "
        "the per-line calls under `data/print/print-trial-lines.csv`."
    )
    return "\n".join(L) + "\n"


__all__ = ["CER_READABLE", "CER_UNUSABLE", "decision", "fraktur_share", "render"]
