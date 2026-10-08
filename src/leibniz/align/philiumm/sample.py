"""This project's aligner on PHILIUMM's worked example, line by line against
theirs (P1 Task 1).

Their pipeline (``passim seriatim --linewise``, a filter, a sliding-window
second pass) writes, for each HTR line, the best *window of whole edition
words* and scores it with a Levenshtein similarity on the raw text,
``1 − distance ÷ max(len)``. This project's aligner projects the edition text
onto the lines by global alignment of the folded strings and mints a
*character slice* of the edition per line, scored by the fraction of the
line's folded characters the alignment matched (``align_conf``).

Four ways of feeding the example to this aligner are run, all with the full
edition text and ``free_edition_ends=True`` (the text may overhang the lines):

* **per file** — every line of one PAGE file in document order, as their run
  takes a file; each image is one side of a bifolium, so ``0002v-0001r``
  holds folios 2v and 1r, which are not adjacent in the text, and a single
  monotone alignment can place only one of them;
* **both files concatenated**, in either order, as the prompt asked;
* **per region** — each ``TextRegion`` (a page's main zone, a margin) as its
  own piece against the whole text: the unit at which the text is contiguous.

Every configuration reports its lines in their CSV's columns (``nb_gt_aligned``
= minted, ``nb_no_alignment`` = declined; their filter columns are not
applicable), the count of minted lines that also pass a raw Levenshtein
similarity of 0.7 between the HTR line and the minted slice — their formula,
the value the dataset card gives for the noisy split's filter — and the
line-by-line comparison with their output: both aligned and the same text
(folded similarity ≥ 0.9), both aligned but different, this project only,
theirs only, neither. Agreement between two aligners fed the same edition text
is not correctness: both can share a mistake, and a line both decline is not
thereby wrong.
"""

from __future__ import annotations

import csv
import json
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz.align import dp
from leibniz.align.align import DEFAULT_THRESHOLD, HtrLine, align_piece
from leibniz.align.normalize import normalize
from leibniz.align.pagexml import PageDocument, PageLine, parse_page_xml
from leibniz.align.philiumm.fetch import ALIGNER_COMMIT, COMMIT_MARKER, GITLAB_PROJECT

SAME_TEXT_SIM = 0.9  # folded similarity above which two aligned texts are "the same"
THEIR_FILTER_SIM = 0.7  # the dataset card's Levenshtein filter on the noisy split
THEIR_MIN_SIM = 0.5  # their --min_sim default (README): the weakest match they keep
BUCKETS = ("both_same", "both_different", "ours_only", "theirs_only", "neither")


@dataclass(slots=True)
class Sample:
    """The worked example as loaded from disk."""

    gt_text: str
    htr: dict[str, PageDocument]  # file name -> HTR lines
    theirs: dict[str, PageDocument]  # file name -> their aligned output
    their_report: list[dict[str, str]]  # rows of alignment_report.csv (incl. TOTAL)
    commit: str | None

    @property
    def files(self) -> list[str]:
        return sorted(self.htr)


def load_sample(sample_dir: Path) -> Sample:
    """Read ``GT/*.txt`` (one file), ``HTR/*.xml``, ``htr_replaced_gt/*.xml`` and
    ``alignment_report.csv`` from a directory laid out like their repository."""
    sample_dir = Path(sample_dir)
    gt_files = sorted((sample_dir / "GT").glob("*.txt"))
    if len(gt_files) != 1:
        raise FileNotFoundError(f"expected one GT/*.txt under {sample_dir}, found {len(gt_files)}")
    gt_text = gt_files[0].read_text(encoding="utf-8")
    htr = {p.name: parse_page_xml(p) for p in sorted((sample_dir / "HTR").glob("*.xml"))}
    if not htr:
        raise FileNotFoundError(f"no HTR/*.xml under {sample_dir}")
    theirs = {
        p.name: parse_page_xml(p) for p in sorted((sample_dir / "htr_replaced_gt").glob("*.xml"))
    }
    report: list[dict[str, str]] = []
    csv_path = sample_dir / "alignment_report.csv"
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as fh:
            report = list(csv.DictReader(fh))
    marker = sample_dir / COMMIT_MARKER
    commit = marker.read_text(encoding="utf-8").strip() if marker.exists() else None
    return Sample(gt_text, htr, theirs, report, commit)


@dataclass(slots=True)
class LineOutcome:
    """One HTR line under one configuration."""

    file: str
    line_id: str
    index: int
    region_id: str
    region_type: str | None
    htr_text: str
    minted: str  # "" when the aligner declined the line
    align_conf: float
    sim_raw: float | None = None  # their formula, raw text (NFC), HTR vs minted
    sim_folded: float | None = None  # this project's fold, HTR vs minted

    @property
    def aligned(self) -> bool:
        return bool(self.minted)


@dataclass(slots=True)
class Configuration:
    label: str
    description: str
    lines: list[LineOutcome]

    @property
    def n_lines(self) -> int:
        return len(self.lines)

    @property
    def n_minted(self) -> int:
        return sum(1 for ln in self.lines if ln.aligned)

    def n_minted_above(self, sim: float) -> int:
        return sum(1 for ln in self.lines if ln.aligned and (ln.sim_raw or 0.0) >= sim)

    def by_file(self) -> dict[str, list[LineOutcome]]:
        out: dict[str, list[LineOutcome]] = {}
        for ln in self.lines:
            out.setdefault(ln.file, []).append(ln)
        return out


def raw_similarity(a: str, b: str) -> float:
    """Their ``levenshtein_similarity``: ``1 − d ÷ max(len)`` on the raw text (NFC)."""
    a, b = unicodedata.normalize("NFC", a.strip()), unicodedata.normalize("NFC", b.strip())
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return dp.similarity(a, b)


def folded_similarity(a: str, b: str) -> float:
    fa, fb = normalize(a), normalize(b)
    if not fa and not fb:
        return 1.0
    if not fa or not fb:
        return 0.0
    return dp.similarity(fa, fb)


def align_lines(
    pieces: Sequence[tuple[str, Sequence[PageLine]]],
    gt_text: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[LineOutcome]:
    """Align each ``(file, lines)`` piece against the whole edition text."""
    out: list[LineOutcome] = []
    for file, lines in pieces:
        if not lines:
            continue
        htr = [HtrLine(ref=f"{file}#{ln.id}", text=ln.text) for ln in lines]
        res = align_piece(htr, gt_text, threshold=threshold, free_edition_ends=True)
        for ln, al in zip(lines, res.lines, strict=True):
            minted = al.edition_text.strip() if al.aligned else ""
            out.append(
                LineOutcome(
                    file=file,
                    line_id=ln.id,
                    index=ln.index,
                    region_id=ln.region_id,
                    region_type=ln.region_type,
                    htr_text=ln.text,
                    minted=minted,
                    align_conf=al.align_conf,
                    sim_raw=raw_similarity(ln.text, minted) if minted else None,
                    sim_folded=folded_similarity(ln.text, minted) if minted else None,
                )
            )
    return out


def run_configurations(
    sample: Sample, *, threshold: float = DEFAULT_THRESHOLD
) -> list[Configuration]:
    files = sample.files
    confs: list[Configuration] = []
    for f in files:
        confs.append(
            Configuration(
                f"file:{f}",
                f"every line of {f} in document order, one piece (their per-file run)",
                align_lines([(f, sample.htr[f].lines)], sample.gt_text, threshold=threshold),
            )
        )
    if len(files) > 1:
        for order in (files, list(reversed(files))):
            pieces = [(f, sample.htr[f].lines) for f in order]
            # one spine across the files: concatenate as a single piece
            joined: list[PageLine] = []
            for _f, lines in pieces:
                joined.extend(lines)
            res = align_lines([("+".join(order), joined)], sample.gt_text, threshold=threshold)
            # give each outcome back its file name
            k = 0
            for f, lines in pieces:
                for _ in lines:
                    res[k].file = f
                    k += 1
            confs.append(
                Configuration(
                    "concat:" + " + ".join(order),
                    "both files as one piece, in this order",
                    res,
                )
            )
    region_pieces: list[tuple[str, Sequence[PageLine]]] = []
    for f in files:
        doc = sample.htr[f]
        for rid, _ in doc.regions:
            lines = doc.lines_of(rid)
            if lines:
                region_pieces.append((f, lines))
    confs.append(
        Configuration(
            "regions",
            "each TextRegion of each file as its own piece against the whole text",
            align_lines(region_pieces, sample.gt_text, threshold=threshold),
        )
    )
    return confs


def their_csv_rows(conf: Configuration) -> list[dict[str, object]]:
    """Their report's columns from this project's outcome (filters not applicable)."""
    rows: list[dict[str, object]] = []
    by = conf.by_file()
    for f in sorted(by):
        rows.append(_their_row(f, by[f]))
    rows.append(_their_row("TOTAL", conf.lines))
    return rows


def _their_row(name: str, lines: Sequence[LineOutcome]) -> dict[str, object]:
    n = len(lines)
    minted = sum(1 for ln in lines if ln.aligned)

    def pct(k: int) -> float:
        return round(100 * k / n, 1) if n else 0.0

    return {
        "filename": name,
        "nb_htr_lines": n,
        "nb_gt_aligned": minted,
        "pct_gt_aligned": pct(minted),
        "nb_low_conf": "n/a",
        "nb_ratio_too_low": "n/a",
        "nb_ratio_too_high": "n/a",
        "nb_no_alignment": n - minted,
        "pct_no_alignment": pct(n - minted),
        "nb_window_passages": "n/a",
        "nb_fallback_lines": "n/a",
    }


@dataclass(slots=True)
class Pair:
    file: str
    line_id: str
    index: int
    region_type: str | None
    bucket: str
    htr_text: str
    ours: str
    theirs: str
    their_conf: float | None
    sim_ours_theirs: float | None  # folded, when both aligned
    sim_htr_ours: float | None = None  # folded similarity of the HTR reading to each text
    sim_htr_theirs: float | None = None


@dataclass(slots=True)
class Comparison:
    label: str
    pairs: list[Pair]
    counts: dict[str, dict[str, int]] = field(default_factory=dict)  # file -> bucket -> n

    def total(self, bucket: str) -> int:
        return sum(c.get(bucket, 0) for c in self.counts.values())


def compare(conf: Configuration, sample: Sample) -> Comparison:
    """Bucket every HTR line by what the two aligners did with it."""
    theirs_by: dict[str, dict[str, PageLine]] = {
        f: {ln.id: ln for ln in doc.lines} for f, doc in sample.theirs.items()
    }
    pairs: list[Pair] = []
    counts: dict[str, dict[str, int]] = {}
    for ln in conf.lines:
        t = theirs_by.get(ln.file, {}).get(ln.line_id)
        their_text = (t.text if t is not None else "").strip()
        their_conf = t.conf if t is not None else None
        sim = None
        if ln.aligned and their_text:
            sim = folded_similarity(ln.minted, their_text)
            bucket = "both_same" if sim >= SAME_TEXT_SIM else "both_different"
        elif ln.aligned:
            bucket = "ours_only"
        elif their_text:
            bucket = "theirs_only"
        else:
            bucket = "neither"
        counts.setdefault(ln.file, {b: 0 for b in BUCKETS})[bucket] += 1
        pairs.append(
            Pair(
                ln.file,
                ln.line_id,
                ln.index,
                ln.region_type,
                bucket,
                ln.htr_text,
                ln.minted,
                their_text,
                their_conf,
                sim,
                folded_similarity(ln.htr_text, ln.minted) if ln.aligned else None,
                folded_similarity(ln.htr_text, their_text) if their_text else None,
            )
        )
    return Comparison(conf.label, pairs, counts)


def witness_tally(comp: Comparison) -> tuple[int, int, int]:
    """On the lines both aligned differently: how many times the HTR reading is
    closer to this project's text, to theirs, or equally close (folded)."""
    ours = theirs = tie = 0
    for p in comp.pairs:
        if p.bucket != "both_different" or p.sim_htr_ours is None or p.sim_htr_theirs is None:
            continue
        if abs(p.sim_htr_ours - p.sim_htr_theirs) < 1e-9:
            tie += 1
        elif p.sim_htr_ours > p.sim_htr_theirs:
            ours += 1
        else:
            theirs += 1
    return ours, theirs, tie


def their_line_scores(sample: Sample) -> list[float]:
    """The per-line score their output carries on every aligned line (``TextEquiv/@conf``)."""
    return [
        ln.conf
        for doc in sample.theirs.values()
        for ln in doc.lines
        if ln.text.strip() and ln.conf is not None
    ]


def their_aligned_above(sample: Sample, sim: float) -> int:
    return sum(1 for c in their_line_scores(sample) if c >= sim)


def their_totals(sample: Sample) -> dict[str, object] | None:
    """The TOTAL row of their committed CSV, as numbers."""
    for r in sample.their_report:
        if r.get("filename") == "TOTAL":
            return {k: _num(v) for k, v in r.items()}
    return None


def _num(v: str) -> object:
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


# --------------------------------------------------------------------------- #
# Outputs
# --------------------------------------------------------------------------- #


def write_comparison_csv(comp: Comparison, path: Path) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "file",
                "index",
                "line_id",
                "region_type",
                "bucket",
                "htr_text",
                "ours",
                "theirs",
                "their_conf",
                "sim_ours_theirs",
                "sim_htr_ours",
                "sim_htr_theirs",
            ]
        )
        for p in comp.pairs:
            w.writerow(
                [
                    p.file,
                    p.index,
                    p.line_id,
                    p.region_type or "",
                    p.bucket,
                    p.htr_text,
                    p.ours,
                    p.theirs,
                    "" if p.their_conf is None else f"{p.their_conf:.3f}",
                    "" if p.sim_ours_theirs is None else f"{p.sim_ours_theirs:.3f}",
                    "" if p.sim_htr_ours is None else f"{p.sim_htr_ours:.3f}",
                    "" if p.sim_htr_theirs is None else f"{p.sim_htr_theirs:.3f}",
                ]
            )
    return len(comp.pairs)


def summary(
    sample: Sample,
    confs: Sequence[Configuration],
    comps: Sequence[Comparison],
    *,
    threshold: float,
) -> dict:
    return {
        "commit": sample.commit,
        "threshold": threshold,
        "gt_chars": len(sample.gt_text),
        "files": {f: len(doc.lines) for f, doc in sample.htr.items()},
        "theirs": their_totals(sample),
        "their_aligned_scored": len(their_line_scores(sample)),
        "their_aligned_raw_ge_0_7": their_aligned_above(sample, THEIR_FILTER_SIM),
        "their_aligned_raw_ge_0_5": their_aligned_above(sample, THEIR_MIN_SIM),
        "configurations": [
            {
                "label": c.label,
                "n_lines": c.n_lines,
                "n_minted": c.n_minted,
                "n_minted_raw_ge_0_7": c.n_minted_above(THEIR_FILTER_SIM),
                "n_minted_raw_ge_0_5": c.n_minted_above(THEIR_MIN_SIM),
                "their_columns": their_csv_rows(c),
            }
            for c in confs
        ],
        "comparisons": [
            {
                "label": k.label,
                "by_file": k.counts,
                "total": {b: k.total(b) for b in BUCKETS},
                "both_different_witness": dict(
                    zip(("ours_closer", "theirs_closer", "tie"), witness_tally(k), strict=True)
                ),
            }
            for k in comps
        ],
    }


def _pct(k: int, n: int) -> str:
    return "—" if not n else f"{100 * k / n:.1f} %"


def _cell(text: str, limit: int = 64) -> str:
    t = text.replace("|", "\\|").replace("\n", " ")
    return t if len(t) <= limit else t[: limit - 1] + "…"


def render(
    sample: Sample,
    confs: Sequence[Configuration],
    comps: Sequence[Comparison],
    *,
    threshold: float,
    max_pairs: int = 40,
    comparison_csv: Path | None = None,
) -> str:
    out: list[str] = []
    A = out.append
    A("# PHILIUMM's worked example under this project's aligner")
    A("")
    commit = sample.commit or ALIGNER_COMMIT
    A(
        f"Their repository `{GITLAB_PROJECT}` "
        f"at commit `{commit[:12]}`: the edition reading text "
        f"({len(sample.gt_text):,} characters), the HTR lines of "
        + ", ".join(f"`{f}` ({len(doc.lines)} lines)" for f, doc in sorted(sample.htr.items()))
        + ", and their aligned output."
    )
    A("")
    tt = their_totals(sample)
    if tt:
        A(
            f"**Their run, from the committed `alignment_report.csv`:** {tt['nb_htr_lines']} HTR "
            f"lines, "
            f"{tt['nb_gt_aligned']} replaced by edition text ({tt['pct_gt_aligned']} %), "
            f"{tt['nb_no_alignment']} without a match, {tt['nb_low_conf']} blanked by the "
            f"confidence "
            f"gate, {tt['nb_ratio_too_low']} + {tt['nb_ratio_too_high']} by the word-ratio gates; "
            f"{tt['nb_window_passages']} Passim passages, {tt['nb_fallback_lines']} fallback "
            "lines. Settings, from their README: defaults `--conf_threshold 0.0` (no per-line "
            "gate, which the "
            "zero in `nb_low_conf` confirms), `--min_token_ratio 0.4`, `--max_token_ratio 2.5`, "
            "`--min_sim 0.5`; the usage example runs `--conf_threshold 0.7`, and the dataset card "
            "states the noisy split was filtered at Levenshtein ≥ 0.7. Their per-line score is "
            "`1 − Levenshtein ÷ max(len)` on the raw text between the HTR line and the best "
            "window of "
            "whole edition words (`src/filter_passim_results.py`). Their output carries that score "
            f"on every aligned line: {their_aligned_above(sample, THEIR_FILTER_SIM)} of the "
            f"{len(their_line_scores(sample))} scored lines reach 0.7 and "
            f"{their_aligned_above(sample, THEIR_MIN_SIM)} reach 0.5 — the rows to set against "
            "the "
            "*raw ≥ 0.7* and *raw ≥ 0.5* columns below."
        )
        A("")
    A(
        f"**This project's aligner:** the whole edition text projected onto the lines by global "
        f"alignment of the folded strings (`align_piece`, `free_edition_ends=True`), a line minted "
        f"when ≥ {threshold:.2f} of its folded characters are matched (`align_conf`); the minted "
        f"text is a character slice of the edition. *raw ≥ 0.7* applies their formula and the "
        f"dataset card's cut to the HTR line and its minted slice; *raw ≥ 0.5* their "
        f"`--min_sim`. "
        f"A minted line with a hyphen kept carries one character the edition lacks."
    )
    A("")
    A("## Yield under four ways of feeding the example")
    A("")
    A("| configuration | lines | minted | yield | minted, raw ≥ 0.7 | minted, raw ≥ 0.5 |")
    A("|---|---:|---:|---:|---:|---:|")
    for c in confs:
        A(
            f"| {c.label} | {c.n_lines} | {c.n_minted} | {_pct(c.n_minted, c.n_lines)} | "
            f"{c.n_minted_above(THEIR_FILTER_SIM)} "
            f"({_pct(c.n_minted_above(THEIR_FILTER_SIM), c.n_lines)}) | "
            f"{c.n_minted_above(THEIR_MIN_SIM)} "
            f"({_pct(c.n_minted_above(THEIR_MIN_SIM), c.n_lines)}) |"
        )
    A("")
    A(
        "*per file*: one piece per PAGE file, as their run takes a file. Each image is one side of "
        "a bifolium: `0002r-0001v` shows folios 1v and 2r, adjacent in the text; `0002v-0001r` "
        "shows 2v and 1r, the end and the start of the passage, which one monotone alignment "
        "cannot both place. *concat*: both files as one piece, in either order. *regions*: each "
        "`TextRegion` (a main zone, a margin) as its own piece against the whole text — the "
        "unit at "
        "which the text is contiguous, and the one the comparison below uses for its best case."
    )
    A("")
    A("## In their CSV's columns")
    A("")
    for c in confs:
        A(f"**{c.label}**")
        A("")
        A(
            "| filename | nb_htr_lines | nb_gt_aligned | pct_gt_aligned | nb_no_alignment | "
            "pct_no_alignment |"
        )
        A("|---|---:|---:|---:|---:|---:|")
        for r in their_csv_rows(c):
            A(
                f"| {r['filename']} | {r['nb_htr_lines']} | {r['nb_gt_aligned']} | "
                f"{r['pct_gt_aligned']} | "
                f"{r['nb_no_alignment']} | {r['pct_no_alignment']} |"
            )
        A("")
    A("The confidence and word-ratio columns of their report have no counterpart here (n/a).")
    A("")
    A("## Line by line against their output")
    A("")
    A(
        f"For every HTR line: *both same* — both aligned it and the texts agree at folded "
        f"similarity ≥ {SAME_TEXT_SIM}; *both different* — both aligned it, the texts differ; "
        f"*ours only*; "
        f"*theirs only*; *neither*."
    )
    A("")
    A(
        "| configuration | file | lines | both same | both different | ours only | theirs only | "
        "neither |"
    )
    A("|---|---|---:|---:|---:|---:|---:|---:|")
    for k in comps:
        for f in sorted(k.counts):
            c = k.counts[f]
            n = sum(c.values())
            A(
                f"| {k.label} | {f} | {n} | "
                + " | ".join(f"{c[b]} ({_pct(c[b], n)})" for b in BUCKETS)
                + " |"
            )
        n = len(k.pairs)
        A(
            f"| {k.label} | **all** | {n} | "
            + " | ".join(f"{k.total(b)} ({_pct(k.total(b), n)})" for b in BUCKETS)
            + " |"
        )
    A("")
    A("By zone type (SegmOnto, from the regions' `custom` attribute), all files:")
    A("")
    A(
        "| configuration | zone | lines | both same | both different | ours only | theirs only | "
        "neither |"
    )
    A("|---|---|---:|---:|---:|---:|---:|---:|")
    for k in comps:
        zones: dict[str, dict[str, int]] = {}
        for p in k.pairs:
            z = zones.setdefault(p.region_type or "—", {b: 0 for b in BUCKETS})
            z[p.bucket] += 1
        for zname in sorted(zones):
            c = zones[zname]
            n = sum(c.values())
            A(
                f"| {k.label} | {zname} | {n} | "
                + " | ".join(f"{c[b]} ({_pct(c[b], n)})" for b in BUCKETS)
                + " |"
            )
    A("")
    A(
        "Agreement is not correctness: two aligners fed the same edition text can share a mistake, "
        "and a line both decline (the library stamp, a page number, a line the edition omits) is "
        "not thereby wrong. What the comparison shows is where the two methods make different "
        "calls, which is where a human look pays. One witness is on the sheet, though: on a line "
        "both aligned differently, the HTR reading of the strip is closer to one of the two texts. "
        + "; ".join(
            f"*{k.label}*: closer to this project's slice on {w[0]}, to their window on {w[1]}, "
            f"equally close on {w[2]} of {k.total('both_different')}"
            for k in comps
            for w in [witness_tally(k)]
        )
        + ". A slice that runs on past the window where the HTR reads more words is the usual case."
    )
    for k in comps:
        diff = [p for p in k.pairs if p.bucket in ("both_different", "ours_only", "theirs_only")]
        if not diff:
            continue
        A("")
        A(f"### Where they differ — {k.label}")
        A("")
        shown = diff[:max_pairs]
        A(
            f"{len(diff)} lines; the first {len(shown)} below"
            + (f", all in `{comparison_csv}`." if comparison_csv else ".")
        )
        A("")
        A(
            "| file | # | zone | bucket | HTR line | this project | theirs | their score | "
            "HTR↔ours | HTR↔theirs |"
        )
        A("|---|---:|---|---|---|---|---|---:|---:|---:|")
        for p in shown:
            tc = "—" if p.their_conf is None else f"{p.their_conf:.2f}"
            ho = "—" if p.sim_htr_ours is None else f"{p.sim_htr_ours:.2f}"
            ht = "—" if p.sim_htr_theirs is None else f"{p.sim_htr_theirs:.2f}"
            A(
                f"| {p.file.replace('.xml', '')} | {p.index} | {p.region_type or '—'} | "
                f"{p.bucket} | {_cell(p.htr_text)} | {_cell(p.ours) or '—'} | "
                f"{_cell(p.theirs) or '—'} | {tc} | "
                f"{ho} | {ht} |"
            )
    return "\n".join(out) + "\n"


def write_summary(summ: dict, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(summ, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


__all__ = [
    "BUCKETS",
    "SAME_TEXT_SIM",
    "THEIR_FILTER_SIM",
    "THEIR_MIN_SIM",
    "Comparison",
    "Configuration",
    "LineOutcome",
    "Pair",
    "Sample",
    "align_lines",
    "compare",
    "folded_similarity",
    "load_sample",
    "raw_similarity",
    "render",
    "run_configurations",
    "summary",
    "their_aligned_above",
    "their_csv_rows",
    "their_line_scores",
    "their_totals",
    "witness_tally",
    "write_comparison_csv",
    "write_summary",
]
