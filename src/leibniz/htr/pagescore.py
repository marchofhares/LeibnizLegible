"""Page-level scoring of the frontier models against the project's readers (LT1, Task 2).

Three measurements, one policy (the B1 harness's ``philiumm`` normalisation,
the other three policies beside it):

* **PHILIUMM pages.** The reference of a val page is the dataset's own PAGE
  XML for that scan: its lines in document order, the empty ones dropped (the
  held-out split's lines, as the model's authors cut them; the parquet carries
  text and image only, no page, so the page is rebuilt from the XML the Hub
  publishes beside each scan). Page CER = the edit distance between the
  reference and the model's answer, both as one string of lines joined by
  spaces, over the reference's length; pooled over pages (Σ edits ÷ Σ
  reference characters) with a 95 % bootstrap interval over pages, and per
  page. A page whose call failed (refused, empty, runaway, error) is scored
  both ways: charged as 100 % error, and left out. The PHILIUMM kraken model's
  page CER comes from its own line readings of the same lines
  (:func:`cut_page_lines` cuts them for ``bench run``; :func:`kraken_page_texts`
  joins the dump back into pages).
* **The letter pool.** A reader kind *page* for :mod:`leibniz.align.letterpool_eval`
  (:class:`~leibniz.align.letterpool_eval.PageReadings`): the model's page text
  is attached to the page as a whole, ``machine_text`` concatenates the pages in
  order, and the infix alignment, the pooling and the aggregation run unchanged.
* **The line diff** the colleague proposes: the page model's lines and a line
  reader's lines aligned to the same reference lines (a Needleman–Wunsch over
  lines, a pair costing its normalised edit distance, a gap :data:`GAP_COST`, so
  two lines with under 30 % similarity are not paired), then the counts — both
  right, exactly one right, both wrong, the lines the page model invented and
  the lines it dropped, the length ratio.

Numbers only: no reference text and no model output lands in the committed files.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz.align import letterpool_eval as E
from leibniz.align.pagexml import PageLine, parse_page_xml
from leibniz.htr import metrics
from leibniz.htr.pageread import COLUMNS, PageRow, split_lines

HEADLINE_POLICY = E.HEADLINE_POLICY
POLICIES = E.POLICIES
BOOTSTRAP_SEED = E.BOOTSTRAP_SEED
BOOTSTRAP_RESAMPLES = E.BOOTSTRAP_RESAMPLES
GAP_COST = (
    0.35  # a pair costs 1 − similarity; two gaps cost 0.7: pairs under 30 % similar are not made
)
NEAR_CER = 0.10  # a line within this CER of its reference counts as "near"
LINE_ID_SEP = "__"  # <stem>__<index:03d>: the cut line files and their ids in a bench run dump


# --------------------------------------------------------------------------- #
# PHILIUMM references
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PageRef:
    """A PHILIUMM page's reference: its non-empty lines in document order (one column's
    where the row names one), with their XML indices for the line-reader join."""

    page_id: str
    column: str
    stem: str
    lines: list[str]
    indices: list[int]
    width: int | None = None
    height: int | None = None

    @property
    def key(self) -> tuple[str, str]:
        return (self.page_id, self.column)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def line_x_centre(line: PageLine) -> float | None:
    pts = line.coords or line.baseline
    if not pts:
        return None
    return sum(p[0] for p in pts) / len(pts)


def in_column(line: PageLine, column: str, width: int | None) -> bool:
    """Whether a line belongs to the column: by its x-centre against the page's midline
    (a line without geometry, or a page without a width, belongs to every column)."""
    if column == "whole" or not width:
        return True
    x = line_x_centre(line)
    if x is None:
        return True
    return x < width / 2 if column == "left" else x >= width / 2


def page_ref(stem: str, xml_path: Path | str, *, page_id: str, column: str = "whole") -> PageRef:
    doc = parse_page_xml(xml_path)
    lines: list[str] = []
    idx: list[int] = []
    for ln in doc.lines:
        if ln.text.strip() and in_column(ln, column, doc.width):
            lines.append(ln.text.strip())
            idx.append(ln.index)
    return PageRef(page_id, column, stem, lines, idx, doc.width, doc.height)


def philiumm_refs(
    rows: Sequence[PageRow], pages_dir: Path | str
) -> tuple[dict[tuple[str, str], PageRef], list[str]]:
    """The references of the list's PHILIUMM rows from ``pages_dir/<stem>.xml``; the rows
    whose XML is missing are returned by page id, left out and reported."""
    refs: dict[tuple[str, str], PageRef] = {}
    missing: list[str] = []
    for r in rows:
        if r.set != "philiumm":
            continue
        xml = Path(pages_dir) / f"{r.ref or r.page_id.split(':', 1)[-1]}.xml"
        if not xml.exists():
            missing.append(r.page_id)
            continue
        ref = page_ref(xml.stem, xml, page_id=r.page_id, column=r.column)
        refs[ref.key] = ref
    return refs, missing


# --------------------------------------------------------------------------- #
# Distances
# --------------------------------------------------------------------------- #


def global_distance(a: str, b: str) -> int:
    """Levenshtein distance of two long strings: the numpy row of the letter-pool metric
    (pinned at both ends) where both are long, the harness's pure DP otherwise."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) * len(b) < 40_000:
        return metrics.edit_distance(a, b)
    row = E._hw_last_row(a, b, free_prefix=False)
    return int(row[-1])


def line_similarity(a: str, b: str) -> float:
    """``1 − distance ÷ max length`` of two normalised lines (1.0 for two empty lines)."""
    if not a and not b:
        return 1.0
    return 1.0 - metrics.edit_distance(a, b) / max(len(a), len(b))


# --------------------------------------------------------------------------- #
# Page CER
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PageScore:
    """One page (a column) under one model and policy: the atoms of the page tables."""

    page_id: str
    column: str
    set: str
    model: str
    policy: str
    status: str  # ok | refused | empty | runaway | error | unread
    ref_chars: int
    hyp_chars: int
    edits: int
    n_ref_lines: int
    n_hyp_lines: int

    @property
    def cer(self) -> float:
        if self.ref_chars == 0:
            return 0.0 if self.edits == 0 else 1.0
        return self.edits / self.ref_chars

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def score_page(
    ref: PageRef,
    text: str,
    *,
    status: str,
    model: str,
    policy: str = HEADLINE_POLICY,
    set_name: str = "philiumm",
) -> PageScore:
    """The page under one policy; a page whose status is not ``ok`` is charged in full
    (its answer counts as empty) — :func:`pooled_pages` also drops it on request."""
    fn = POLICIES[policy]
    r = fn(" ".join(ref.lines))
    hyp_lines = split_lines(text) if status == "ok" else []
    h = fn(" ".join(hyp_lines))
    return PageScore(
        page_id=ref.page_id,
        column=ref.column,
        set=set_name,
        model=model,
        policy=policy,
        status=status,
        ref_chars=len(r),
        hyp_chars=len(h),
        edits=global_distance(r, h),
        n_ref_lines=len(ref.lines),
        n_hyp_lines=len(hyp_lines),
    )


def score_model(
    refs: Mapping[tuple[str, str], PageRef],
    readings: Mapping[tuple[str, str], Mapping],
    model: str,
    *,
    policies: Iterable[str] = tuple(POLICIES),
) -> list[PageScore]:
    """Every reference page under every policy for one model's readings (a page the
    model never read is ``unread`` and charged like a failure)."""
    out: list[PageScore] = []
    for key, ref in sorted(refs.items()):
        row = readings.get(key)
        status = str(row.get("status", "error")) if row else "unread"
        text = str(row.get("text", "")) if row else ""
        for pol in policies:
            out.append(score_page(ref, text, status=status, model=model, policy=pol))
    return out


def score_texts(
    refs: Mapping[tuple[str, str], PageRef],
    texts: Mapping[tuple[str, str], str],
    model: str,
    *,
    policies: Iterable[str] = tuple(POLICIES),
) -> list[PageScore]:
    """Like :func:`score_model` for a reader given as plain page texts (the kraken model's
    lines joined per page); a page without a text is ``unread``."""
    out: list[PageScore] = []
    for key, ref in sorted(refs.items()):
        text = texts.get(key)
        status = "ok" if text is not None else "unread"
        for pol in policies:
            out.append(score_page(ref, text or "", status=status, model=model, policy=pol))
    return out


def pooled_pages(
    scores: Sequence[PageScore],
    *,
    failed: str = "charge",
    seed: int = BOOTSTRAP_SEED,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict:
    """CER pooled over characters with a bootstrap interval over pages, and the per-page
    distribution. ``failed="charge"`` keeps the failed pages at 100 % error,
    ``"omit"`` drops them."""
    rows = list(scores) if failed == "charge" else [s for s in scores if s.ok]
    atoms = [metrics.LineScore(s.page_id, "", "", s.edits, s.ref_chars, 0, 0) for s in rows]
    ci = metrics.bootstrap_ci(atoms, metric="cer", n_resamples=n_resamples, seed=seed)
    cers = sorted(s.cer for s in rows)
    if len(cers) >= 2:
        q = statistics.quantiles(cers, n=4)
    elif cers:
        q = [cers[0]] * 3
    else:
        q = [0.0, 0.0, 0.0]
    return {
        "pages": len(rows),
        "failed": sum(1 for s in scores if not s.ok),
        "ref_chars": sum(s.ref_chars for s in rows),
        "hyp_chars": sum(s.hyp_chars for s in rows),
        "edits": sum(s.edits for s in rows),
        "ref_lines": sum(s.n_ref_lines for s in rows),
        "hyp_lines": sum(s.n_hyp_lines for s in rows),
        "cer": ci.point,
        "cer_lo": ci.lo,
        "cer_hi": ci.hi,
        "page_cer_mean": statistics.fmean(cers) if cers else 0.0,
        "page_cer_min": cers[0] if cers else 0.0,
        "page_cer_q1": q[0],
        "page_cer_median": q[1],
        "page_cer_q3": q[2],
        "page_cer_max": cers[-1] if cers else 0.0,
    }


def aggregate_pages(scores: Sequence[PageScore]) -> dict:
    """``{model: {policy: {"charged": …, "omitted": …}}}`` over the page scores."""
    by: dict[tuple[str, str], list[PageScore]] = {}
    for s in scores:
        by.setdefault((s.model, s.policy), []).append(s)
    out: dict = {}
    for (model, policy), rows in sorted(by.items()):
        out.setdefault(model, {})[policy] = {
            "charged": pooled_pages(rows, failed="charge"),
            "omitted": pooled_pages(rows, failed="omit"),
        }
    return out


def status_counts(readings: Mapping[tuple[str, str], Mapping]) -> dict:
    """The final and first statuses of a model's readings, and the retries."""
    final: dict[str, int] = {}
    first: dict[str, int] = {}
    retried = 0
    for row in readings.values():
        final[row.get("status", "?")] = final.get(row.get("status", "?"), 0) + 1
        f = row.get("first_status", row.get("status", "?"))
        first[f] = first.get(f, 0) + 1
        if int(row.get("attempts", 1)) > 1:
            retried += 1
    return {"final": final, "first": first, "retried": retried}


def usage_totals(readings: Mapping[tuple[str, str], Mapping]) -> dict:
    """Tokens, cost and time over a model's readings, and the image sizes sent."""
    rows = list(readings.values())
    n_in = sum(int((r.get("usage") or {}).get("input", 0)) for r in rows)
    n_out = sum(int((r.get("usage") or {}).get("output", 0)) for r in rows)
    n_reason = sum(int((r.get("usage") or {}).get("reasoning", 0) or 0) for r in rows)
    widths = [int((r.get("image") or {}).get("width", 0)) for r in rows]
    heights = [int((r.get("image") or {}).get("height", 0)) for r in rows]
    return {
        "engine": str(rows[0].get("engine", "")) if rows else "",
        "calls": sum(int(r.get("attempts", 1)) for r in rows),
        "pages": len(rows),
        "input_tokens": n_in,
        "output_tokens": n_out,
        "reasoning_tokens": n_reason,
        "cost": round(sum(float(r.get("cost", 0.0)) for r in rows), 4),
        "seconds": round(sum(float(r.get("ms", 0.0)) for r in rows) / 1000.0, 1),
        "input_tokens_per_page": round(n_in / len(rows), 1) if rows else 0.0,
        "output_tokens_per_page": round(n_out / len(rows), 1) if rows else 0.0,
        "long_side_max": max((max(w, h) for w, h in zip(widths, heights, strict=True)), default=0),
        "settings": dict(rows[0].get("settings") or {}) if rows else {},
    }


# --------------------------------------------------------------------------- #
# The PHILIUMM kraken model on the same lines
# --------------------------------------------------------------------------- #


def line_file_stem(stem: str, index: int) -> str:
    return f"{stem}{LINE_ID_SEP}{index:03d}"


def cut_page_lines(
    pages_dir: Path | str,
    out_dir: Path | str,
    *,
    stems: Iterable[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> int:
    """Cut every non-empty line of the val pages into Kraken's image + ``.gt.txt`` pair
    (``<stem>__<index>.png``) through the audit's crop machinery (the polygon masked, no
    downscaling), so ``bench run OUT_DIR --engine kraken --out DUMP.jsonl`` reads them.
    Returns the lines written (the pairs already there are kept)."""
    from PIL import Image

    from leibniz.align.audit import CROP_PAD, crop_from_image

    pages_dir, out_dir = Path(pages_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    xmls = sorted(pages_dir.glob("*.xml"))
    if stems is not None:
        wanted = set(stems)
        xmls = [x for x in xmls if x.stem in wanted]
    n = 0
    for xml in xmls:
        jpg = xml.with_suffix(".jpg")
        if not jpg.exists():
            if log:
                log(f"{xml.stem}: no image beside the XML; skipped")
            continue
        doc = parse_page_xml(xml)
        todo = [ln for ln in doc.lines if ln.text.strip() and ln.coords]
        if all((out_dir / f"{line_file_stem(xml.stem, ln.index)}.png").exists() for ln in todo):
            continue
        with Image.open(jpg) as im:
            im.load()
            for ln in todo:
                png_path = out_dir / f"{line_file_stem(xml.stem, ln.index)}.png"
                if png_path.exists():
                    continue
                png = crop_from_image(
                    im,
                    ln.coords,
                    ln.baseline or None,
                    pad=CROP_PAD,
                    max_width=None,
                    mask_polygon=True,
                )
                if png is None:
                    continue
                png_path.write_bytes(png)
                png_path.with_name(png_path.stem + ".gt.txt").write_text(
                    ln.text.strip() + "\n", encoding="utf-8"
                )
                n += 1
        if log:
            log(f"{xml.stem}: {len(todo)} lines")
    return n


def read_line_dump(path: Path | str) -> dict[str, str]:
    """A ``bench run --out`` dump (or the raw-hypothesis cache) as ``{line id: hypothesis}``;
    the normalised ``hyp`` is what the dump carries, the ``line:`` prefix dropped."""
    out: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        lid = str(row.get("line_id", ""))
        lid = lid.removeprefix("line:")
        out[lid] = str(row.get("hyp", ""))
    return out


def kraken_page_texts(
    hyps: Mapping[str, str], refs: Mapping[tuple[str, str], PageRef]
) -> tuple[dict[tuple[str, str], str], int]:
    """The line reader's page texts: its hypotheses for a page's reference lines, in
    order (a line without a hypothesis counts as empty); the second value is the number
    of reference lines the dump covers."""
    out: dict[tuple[str, str], str] = {}
    covered = 0
    for key, ref in refs.items():
        lines = []
        for i in ref.indices:
            h = hyps.get(line_file_stem(ref.stem, i))
            if h is not None:
                covered += 1
            lines.append(h or "")
        out[key] = "\n".join(lines)
    return out, covered


def kraken_page_lines(hyps: Mapping[str, str], ref: PageRef) -> list[str]:
    return [hyps.get(line_file_stem(ref.stem, i), "") for i in ref.indices]


# --------------------------------------------------------------------------- #
# The line diff
# --------------------------------------------------------------------------- #


def align_lines(
    ref: Sequence[str], hyp: Sequence[str], *, gap: float = GAP_COST
) -> list[tuple[int | None, int | None]]:
    """Needleman–Wunsch over lines: a pair costs ``1 − similarity``, a gap ``gap``; the
    path as ``(ref index | None, hyp index | None)`` pairs in order."""
    n, m = len(ref), len(hyp)
    inf = float("inf")
    cost = [[inf] * (m + 1) for _ in range(n + 1)]
    back: list[list[int]] = [[0] * (m + 1) for _ in range(n + 1)]  # 0 diag, 1 up (ref gap), 2 left
    cost[0][0] = 0.0
    for i in range(1, n + 1):
        cost[i][0] = i * gap
        back[i][0] = 1
    for j in range(1, m + 1):
        cost[0][j] = j * gap
        back[0][j] = 2
    sims = [[line_similarity(r, h) for h in hyp] for r in ref]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = cost[i - 1][j - 1] + (1.0 - sims[i - 1][j - 1])
            up = cost[i - 1][j] + gap
            left = cost[i][j - 1] + gap
            best = min(diag, up, left)
            cost[i][j] = best
            back[i][j] = 0 if best == diag else (1 if best == up else 2)
    path: list[tuple[int | None, int | None]] = []
    i, j = n, m
    while i > 0 or j > 0:
        b = back[i][j]
        if i > 0 and j > 0 and b == 0:
            path.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i > 0 and (b == 1 or j == 0):
            path.append((i - 1, None))
            i -= 1
        else:
            path.append((None, j - 1))
            j -= 1
    path.reverse()
    return path


@dataclass(slots=True)
class LineDiff:
    """Two readers' lines against the same reference lines, one page or many."""

    pages: int = 0
    ref_lines: int = 0
    a_lines: int = 0
    b_lines: int = 0
    both_right: int = 0
    only_a_right: int = 0
    only_b_right: int = 0
    both_wrong: int = 0
    a_near: int = 0  # a's line within NEAR_CER of its reference line
    b_near: int = 0
    a_invented: int = 0  # a's lines matched to no reference line
    a_dropped: int = 0  # reference lines a has no line for
    b_invented: int = 0
    b_dropped: int = 0
    ref_chars: int = 0
    a_chars: int = 0
    b_chars: int = 0

    def add(self, other: LineDiff) -> None:
        for k in self.__slots__:  # type: ignore[attr-defined]
            setattr(self, k, getattr(self, k) + getattr(other, k))

    def as_dict(self) -> dict:
        d = asdict(self)
        d["a_length_ratio"] = (self.a_chars / self.ref_chars) if self.ref_chars else None
        d["b_length_ratio"] = (self.b_chars / self.ref_chars) if self.ref_chars else None
        d["near_cer"] = NEAR_CER
        d["gap_cost"] = GAP_COST
        return d


def diff_lines(
    ref_lines: Sequence[str],
    a_lines: Sequence[str],
    b_lines: Sequence[str],
    *,
    policy: str = HEADLINE_POLICY,
) -> LineDiff:
    """One page: both readers' lines aligned to the reference lines, the counts."""
    fn = POLICIES[policy]
    ref = [fn(x) for x in ref_lines]
    a = [fn(x) for x in a_lines]
    b = [fn(x) for x in b_lines]
    d = LineDiff(pages=1, ref_lines=len(ref), a_lines=len(a), b_lines=len(b))
    d.ref_chars = sum(len(x) for x in ref)
    d.a_chars = sum(len(x) for x in a)
    d.b_chars = sum(len(x) for x in b)

    def matched(hyp: Sequence[str]) -> tuple[dict[int, str], int]:
        path = align_lines(ref, hyp)
        pairs: dict[int, str] = {}
        invented = 0
        for ri, hj in path:
            if ri is not None and hj is not None:
                pairs[ri] = hyp[hj]
            elif hj is not None:
                invented += 1
        return pairs, invented

    pa, d.a_invented = matched(a)
    pb, d.b_invented = matched(b)
    d.a_dropped = len(ref) - len(pa)
    d.b_dropped = len(ref) - len(pb)
    for i, r in enumerate(ref):
        ha, hb = pa.get(i), pb.get(i)
        ra = ha is not None and ha == r
        rb = hb is not None and hb == r
        if ha is not None and (metrics.edit_distance(r, ha) / max(1, len(r))) <= NEAR_CER:
            d.a_near += 1
        if hb is not None and (metrics.edit_distance(r, hb) / max(1, len(r))) <= NEAR_CER:
            d.b_near += 1
        if ra and rb:
            d.both_right += 1
        elif ra:
            d.only_a_right += 1
        elif rb:
            d.only_b_right += 1
        else:
            d.both_wrong += 1
    return d


def diff_total(diffs: Iterable[LineDiff]) -> LineDiff:
    total = LineDiff()
    for d in diffs:
        total.add(d)
    return total


# --------------------------------------------------------------------------- #
# The pool: page readers and the pool diff
# --------------------------------------------------------------------------- #


def pool_page_readings(readings: Mapping[tuple[str, str], Mapping], model: str) -> E.PageReadings:
    """A page reader for the letter-pool metric from one model's readings file: the
    page's text (its columns joined), a failed page as an empty text."""
    from leibniz.align import kurrent_pilot as P
    from leibniz.htr.pageread import page_texts

    ms_by_page: dict[str, float] = {}
    for (pid, _col), row in readings.items():
        ms_by_page[pid] = ms_by_page.get(pid, 0.0) + float(row.get("ms", 0.0))
    out = E.PageReadings()
    for pid, text in page_texts(readings).items():
        out[pid] = P.Reading(pid, text, None, model, "api", round(ms_by_page.get(pid, 0.0), 1))
    return out


def pool_letter_diff(
    letter: E.SetLetter,
    lines: Sequence,
    line_readings: Mapping[str, object],
    page_readings: E.PageReadings,
    *,
    threshold: float = E.SELECTED_THRESHOLD,
    policy: str = HEADLINE_POLICY,
) -> tuple[LineDiff, int]:
    """One letter: the line reader's lines aligned to the letter's text by the factory's
    aligner give the reference lines (the edition slices of the lines it accepts); the
    page model's lines (``a``) and the line reader's own (``b``) are then diffed against
    them. The second value is the number of stored lines the aligner declined (no
    reference line exists for them)."""
    from leibniz.align.align import HtrLine, align_piece

    htr = [
        HtrLine(
            ref=ln.line_id,
            text=line_readings[ln.line_id].text if ln.line_id in line_readings else "",
        )
        for ln in lines
    ]
    res = align_piece(htr, letter.text, threshold=threshold)
    ref_lines = [al.edition_text for al in res.lines if al.aligned]
    b_lines = [al.htr_text for al in res.lines if al.aligned]
    a_lines: list[str] = []
    for pid in letter.page_ids:
        r = page_readings.get(pid)
        if r is not None and r.text.strip():
            a_lines.extend(split_lines(r.text))
    declined = sum(1 for al in res.lines if not al.aligned)
    return diff_lines(ref_lines, a_lines, b_lines, policy=policy), declined


# --------------------------------------------------------------------------- #
# The two sets, scored
# --------------------------------------------------------------------------- #


def score_philiumm(
    refs: Mapping[tuple[str, str], PageRef],
    model_readings: Mapping[str, Mapping[tuple[str, str], Mapping]],
    *,
    missing: Sequence[str] = (),
    kraken_hyps: Mapping[str, str] | None = None,
    kraken_dump: str = "",
    kraken_name: str = "philiumm-kraken (line readings, joined)",
    policies: Iterable[str] = tuple(POLICIES),
) -> dict:
    """The PHILIUMM block of the score file: every page model's page scores, the kraken
    model's from its line dump, the aggregates, the statuses, the usage and the diffs."""
    pols = list(policies)
    scores: list[PageScore] = []
    for model, rd in model_readings.items():
        scores.extend(score_model(refs, rd, model, policies=pols))
    kraken_block: dict = {}
    kraken_texts: dict[tuple[str, str], str] = {}
    if kraken_hyps is not None:
        kraken_texts, covered = kraken_page_texts(kraken_hyps, refs)
        scores.extend(score_texts(refs, kraken_texts, kraken_name, policies=pols))
        kraken_block = {"name": kraken_name, "dump": kraken_dump, "covered": covered}
    diffs: list[dict] = []
    if kraken_hyps is not None:
        for model, rd in model_readings.items():
            total = LineDiff()
            for key, ref in sorted(refs.items()):
                row = rd.get(key)
                if not row or row.get("status") != "ok":
                    continue
                total.add(
                    diff_lines(
                        ref.lines,
                        split_lines(str(row.get("text", ""))),
                        kraken_page_lines(kraken_hyps, ref),
                    )
                )
            diffs.append({"a": model, "b": kraken_name, "counts": total.as_dict()})
    head_refs = [POLICIES[HEADLINE_POLICY](" ".join(r.lines)) for r in refs.values()]
    return {
        "models": {m: {"pages": len(rd)} for m, rd in model_readings.items()},
        "pages": len({k[0] for k in refs}),
        "calls": len(refs),
        "ref_lines": sum(len(r.lines) for r in refs.values()),
        "ref_chars": sum(len(t) for t in head_refs),
        "missing": list(missing),
        "aggregate": aggregate_pages(scores),
        "kraken": kraken_block,
        "statuses": {m: status_counts(rd) for m, rd in model_readings.items()},
        "usage": {m: usage_totals(rd) for m, rd in model_readings.items()},
        "diff": diffs,
        "pages_scored": page_scores_rows([s for s in scores if s.policy == HEADLINE_POLICY]),
    }


def score_pool(
    conn,
    letters_all: Sequence[E.SetLetter],
    page_rows: Sequence[PageRow],
    model_readings: Mapping[str, Mapping[tuple[str, str], Mapping]],
    *,
    pool_readings_dir: Path | str,
    line_readers: Sequence[str] = ("k3-trocr", "k3-kraken", "trocr-kurrent-xvi-xvii"),
    diff_reader: str = "k3-trocr",
    seed: int | None = None,
    log: Callable[[str], None] | None = None,
) -> dict:
    """The pool block of the score file: the drawn letters scored under every reader on
    disk (v1 from the store, the line readers from K2b's and K3's readings, the page models
    as :class:`~leibniz.align.letterpool_eval.PageReadings`) by K2b's metric, both ways for
    the failed pages, and the line diff of each page model against ``diff_reader``."""
    from dataclasses import asdict

    from leibniz.htr.pageread import failed_pages

    letter_ids = {r.letter_id for r in page_rows if r.set == "pool"}
    letters = [ltr for ltr in letters_all if ltr.letter_id in letter_ids]
    lines = E.set_lines(conn, letters)
    readers: dict[str, Mapping] = {E.V1: E.v1_for_set(conn, letters)}
    readers.update(E.readings_on_disk(list(line_readers), pool_readings_dir))
    page_readers = {f"page:{m}": pool_page_readings(rd, m) for m, rd in model_readings.items()}
    readers.update(page_readers)
    scores = E.score_set(letters, lines, readers, log=log)
    agg = E.aggregate(scores)
    failed: set[str] = set()
    for rd in model_readings.values():
        failed |= failed_pages(rd)
    ok_letters = [ltr for ltr in letters if not (set(ltr.page_ids) & failed)]
    ok_ids = {ltr.letter_id for ltr in ok_letters}
    omitted = (
        {
            "letters": len(ok_letters),
            "aggregate": E.aggregate([s for s in scores if s.letter_id in ok_ids]),
        }
        if len(ok_letters) < len(letters)
        else {"letters": len(letters), "aggregate": {}}
    )
    diffs: list[dict] = []
    if diff_reader in readers:
        for name, pr in page_readers.items():
            total = LineDiff()
            declined = 0
            for ltr in letters:
                d, n = pool_letter_diff(ltr, lines[ltr.letter_id], readers[diff_reader], pr)
                total.add(d)
                declined += n
            diffs.append(
                {"a": name, "b": diff_reader, "counts": total.as_dict(), "declined_lines": declined}
            )
    pages = [r for r in page_rows if r.set == "pool"]
    draw = {
        "letters": len(letters),
        "pages": len({r.page_id for r in pages}),
        "pages_L": len({r.page_id for r in pages if r.hand == "L"}),
        "pages_K": len({r.page_id for r in pages if r.hand == "K/k"}),
        "letters_selection": sum(1 for ltr in letters if ltr.half == "selection"),
        "letters_test": sum(1 for ltr in letters if ltr.half == "test"),
        "letters_L": sum(1 for ltr in letters if ltr.hand == "L"),
        "letters_K": sum(1 for ltr in letters if ltr.hand == "K/k"),
        "seed": seed,
        "letter_ids": sorted(letter_ids),
    }
    licences = {E.V1: "the store (the C1 run)"}
    try:
        from leibniz.htr import kurrent as K

        licences.update({k: K.CANDIDATES[k].licence for k in readers if k in K.CANDIDATES})
    except Exception:  # noqa: BLE001 — the licence column is informative only
        pass
    return {
        "models": {m: {"pages": len(rd)} for m, rd in model_readings.items()},
        "draw": draw,
        "lines": sum(len(v) for v in lines.values()),
        "ref_chars": sum(ltr.n_chars for ltr in letters),
        "readers": [
            asdict(E.reader_info(k, v, licences.get(k, "—"), lines)) for k, v in readers.items()
        ],
        "aggregate": agg,
        "omitted": omitted,
        "failed_pages": sorted(failed),
        "statuses": {m: status_counts(rd) for m, rd in model_readings.items()},
        "usage": {m: usage_totals(rd) for m, rd in model_readings.items()},
        "diff": diffs,
        "letters_scored": [
            {
                "letter_id": s.letter_id,
                "reader": s.reader,
                "hand": s.hand,
                "half": s.half,
                "ref_chars": s.ref_chars,
                "edits": s.edits,
                "cer": round(s.cer, 4),
                "n_lines": s.n_lines,
                "n_read": s.n_read,
            }
            for s in scores
            if s.policy == HEADLINE_POLICY
        ],
    }


# --------------------------------------------------------------------------- #
# Files
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ScoreFile:
    """``page-llm.scores.json``: what ``page-score`` leaves for ``page-report``, numbers only."""

    philiumm: dict = field(default_factory=dict)
    pool: dict = field(default_factory=dict)
    generated: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | str) -> ScoreFile:
        p = Path(path)
        if not p.exists():
            return cls()
        d = json.loads(p.read_text(encoding="utf-8"))
        return cls(
            philiumm=d.get("philiumm", {}), pool=d.get("pool", {}), generated=d.get("generated", {})
        )

    def save(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(
                {"philiumm": self.philiumm, "pool": self.pool, "generated": self.generated},
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        return p


def page_scores_rows(scores: Sequence[PageScore]) -> list[dict]:
    """The per-page rows for the score file (ids and numbers, no text)."""
    return [
        {
            "page_id": s.page_id,
            "column": s.column,
            "model": s.model,
            "policy": s.policy,
            "status": s.status,
            "ref_chars": s.ref_chars,
            "hyp_chars": s.hyp_chars,
            "edits": s.edits,
            "cer": round(s.cer, 4),
            "ref_lines": s.n_ref_lines,
            "hyp_lines": s.n_hyp_lines,
        }
        for s in scores
    ]


__all__ = [
    "BOOTSTRAP_RESAMPLES",
    "BOOTSTRAP_SEED",
    "COLUMNS",
    "GAP_COST",
    "HEADLINE_POLICY",
    "LINE_ID_SEP",
    "NEAR_CER",
    "POLICIES",
    "LineDiff",
    "PageRef",
    "PageScore",
    "ScoreFile",
    "aggregate_pages",
    "align_lines",
    "cut_page_lines",
    "diff_lines",
    "diff_total",
    "global_distance",
    "in_column",
    "kraken_page_lines",
    "kraken_page_texts",
    "line_file_stem",
    "line_similarity",
    "line_x_centre",
    "page_ref",
    "page_scores_rows",
    "philiumm_refs",
    "pool_letter_diff",
    "pool_page_readings",
    "pooled_pages",
    "read_line_dump",
    "score_model",
    "score_page",
    "score_philiumm",
    "score_pool",
    "score_texts",
    "status_counts",
    "usage_totals",
]
