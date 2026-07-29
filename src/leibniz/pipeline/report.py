"""Render the C1 pipeline report from the store (``reports/htr-v1-sample.md``).

Everything the report states about a run is derived from the ``pages`` /
``lines`` / ``page_stats`` / ``runs`` tables, so ``leibniz pipeline report``
regenerates the numeric sections after any (sample or full-corpus) run. The
prose is templated; the numbers are queried, so a figure in the report is always
traceable to the store that produced it.

Sections: pipeline coverage (status histogram), throughput (from ``runs``),
per-line confidence distribution, per-set breakdown, segmentation-quality signal
(the ``page_stats`` distributions that feed the C2/C4 stratum heuristic), and the
skip/failure taxonomy.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from leibniz import db

_CONF_BUCKETS: tuple[tuple[float, float, str], ...] = (
    (0.0, 0.5, "< 0.50"),
    (0.5, 0.7, "0.50–0.70"),
    (0.7, 0.8, "0.70–0.80"),
    (0.8, 0.9, "0.80–0.90"),
    (0.9, 1.01, "≥ 0.90"),
)


@dataclass(slots=True)
class SetBreakdown:
    """Per primary-set pipeline state."""

    set_name: str
    by_status: dict[str, int] = field(default_factory=dict)
    n_lines: int = 0
    mean_lines_per_page: float = 0.0

    @property
    def total(self) -> int:
        return sum(self.by_status.values())


@dataclass(slots=True)
class SampleReport:
    """Structured summary of the pipeline state, rendered to markdown."""

    generated_at: str
    status_counts: dict[str, int]
    n_pages_total: int
    n_lines: int
    n_lines_recognized: int
    conf_mean: float | None
    conf_median: float | None
    conf_hist: list[tuple[str, int]]
    by_set: list[SetBreakdown]
    seg_summary: dict[str, float]
    skip_reasons: list[tuple[str, int]]
    runs: list[dict]
    overlap_offenders: list[tuple[str, int, int]]  # (page_id, n_lines, n_overlaps)
    seg_model: str
    htr_model: str
    notes: str = ""


def _skip_reason_key(reason: str | None) -> str:
    if not reason:
        return "unspecified"
    return reason.split(":", 1)[0].strip()


def gather_report(
    conn,
    *,
    generated_at: str,
    seg_model: str = "philiumm-seg",
    htr_model: str = "philiumm-htr",
    notes: str = "",
) -> SampleReport:
    """Query the store into a :class:`SampleReport` (no rendering)."""
    status_counts = db.status_histogram(conn)
    n_pages_total = sum(status_counts.values())
    n_lines = db.count_lines(conn)
    n_lines_recognized = db.count_lines(conn, recognized=True)

    confs = [row[0] for row in conn.execute("SELECT conf FROM lines WHERE conf IS NOT NULL")]
    conf_mean = statistics.fmean(confs) if confs else None
    conf_median = statistics.median(confs) if confs else None
    conf_hist = [(label, sum(1 for c in confs if lo <= c < hi)) for lo, hi, label in _CONF_BUCKETS]

    by_set = _set_breakdowns(conn)
    seg_summary = _seg_summary(conn)
    overlap_offenders = [
        (row[0], row[1], row[2])
        for row in conn.execute(
            "SELECT page_id, n_lines, n_overlaps FROM page_stats "
            "WHERE n_overlaps > 0 ORDER BY n_overlaps DESC, n_lines DESC LIMIT 10"
        )
    ]

    skip_counts: dict[str, int] = {}
    for row in conn.execute("SELECT skip_reason FROM pages WHERE status = 'skipped'"):
        key = _skip_reason_key(row[0])
        skip_counts[key] = skip_counts.get(key, 0) + 1
    skip_reasons = sorted(skip_counts.items(), key=lambda kv: -kv[1])

    runs = [
        {
            "run_id": r["run_id"],
            "stage": r["stage"],
            "model": r["model"],
            "n_input": r["n_input"],
            "n_ok": r["n_ok"],
            "n_failed": r["n_failed"],
        }
        for r in conn.execute(
            "SELECT * FROM runs WHERE stage IN ('segment','recognize') ORDER BY run_id"
        )
    ]

    return SampleReport(
        generated_at=generated_at,
        status_counts=status_counts,
        n_pages_total=n_pages_total,
        n_lines=n_lines,
        n_lines_recognized=n_lines_recognized,
        conf_mean=conf_mean,
        conf_median=conf_median,
        conf_hist=conf_hist,
        by_set=by_set,
        seg_summary=seg_summary,
        skip_reasons=skip_reasons,
        runs=runs,
        overlap_offenders=overlap_offenders,
        seg_model=seg_model,
        htr_model=htr_model,
        notes=notes,
    )


def _set_breakdowns(conn) -> list[SetBreakdown]:
    out: dict[str, SetBreakdown] = {}
    for row in conn.execute(
        "SELECT w.set_name, p.status, COUNT(*) FROM pages p "
        "JOIN works w ON w.gwlb_object_id = p.work_id GROUP BY w.set_name, p.status"
    ):
        bd = out.setdefault(row[0], SetBreakdown(set_name=row[0]))
        bd.by_status[row[1]] = row[2]
    for row in conn.execute(
        "SELECT w.set_name, COALESCE(SUM(ps.n_lines),0), COALESCE(AVG(ps.n_lines),0) "
        "FROM page_stats ps JOIN pages p ON p.page_id = ps.page_id "
        "JOIN works w ON w.gwlb_object_id = p.work_id GROUP BY w.set_name"
    ):
        if row[0] in out:
            out[row[0]].n_lines = int(row[1])
            out[row[0]].mean_lines_per_page = float(row[2])
    return [out[k] for k in sorted(out)]


def _seg_summary(conn) -> dict[str, float]:
    row = conn.execute(
        "SELECT COUNT(*), AVG(n_lines), AVG(region_coverage), AVG(line_height_cv), "
        "AVG(n_overlaps), AVG(n_short_lines), "
        "SUM(CASE WHEN n_overlaps > 0 THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN n_short_lines > 0 THEN 1 ELSE 0 END) FROM page_stats"
    ).fetchone()
    n = row[0] or 0
    return {
        "n_pages": n,
        "mean_lines": row[1] or 0.0,
        "mean_coverage": row[2] or 0.0,
        "mean_cv": row[3] or 0.0,
        "mean_overlaps": row[4] or 0.0,
        "mean_short": row[5] or 0.0,
        "pct_with_overlap": (100.0 * (row[6] or 0) / n) if n else 0.0,
        "pct_with_short": (100.0 * (row[7] or 0) / n) if n else 0.0,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def render_report(rep: SampleReport) -> str:
    """Render the full ``reports/htr-v1-sample.md`` deliverable from a gathered report.

    The prose (architecture, segmentation-quality rationale, operator runbook,
    per-set taxonomy) is templated; the numeric sections are queried from the
    store, so re-running ``leibniz pipeline report`` after a sample or corpus run
    refreshes the numbers in place. Until a recognition run has happened the
    numeric sections read zero and a *Status of the live run* note explains why —
    that note self-removes once pages are recognised.
    """
    started = rep.n_lines > 0 or rep.status_counts.get("recognized", 0) > 0
    lines: list[str] = []
    A = lines.append
    A("# HTR v1 — corpus segmentation + recognition pipeline (Phase C1)")
    A("")
    A(
        f"_Leibniz Legible, Phase C1. Generated {rep.generated_at}. Deliverable of "
        "PROMPTS C1 (SPECS §3, §4.5, §6, §9). Numeric sections are queried from the "
        "store by `leibniz pipeline report`; prose is templated._"
    )
    A("")
    _render_architecture(A)
    _render_coverage(A, rep)
    _render_throughput(A, rep)
    _render_confidence(A, rep)
    _render_per_set(A, rep)
    _render_seg_quality(A, rep)
    _render_taxonomy(A, rep)
    if not started:
        _render_deferred_note(A, rep)
    _render_runbook(A)
    if rep.notes:
        A(rep.notes)
        A("")
    return "\n".join(lines)


def _render_architecture(A) -> None:
    A("## What the pipeline does")
    A("")
    A(
        "Two idempotent, resumable stages advance every page through a status machine "
        "on the `pages` table: `pending → segmented → recognized`, with genuine "
        "failures diverted to `skipped` **with a reason** (SPECS §3)."
    )
    A("")
    A(
        "- **`segment`** runs the PHILIUMM baseline segmenter over each cached page, "
        "writes every line's **geometry** (baseline + polygon) to `lines` with "
        "`status='machine'` and no text yet, and computes a per-page "
        "**segmentation-statistics** row in `page_stats`."
    )
    A(
        "- **`recognize`** crops each stored line from its geometry — without re-running "
        "the neural segmenter — runs the PHILIUMM HTR model (the B1-reproduced 7.95 % CER "
        "model), and fills each line's **text** + per-line **confidence**, repointing the "
        "line's run/model at the recognition run (the text's provenance, SPECS §4.5)."
    )
    A("")
    A(
        "Both stages are status-driven & resumable (commit per page), idempotent "
        "(`--redo` re-processes; re-segmentation clears old lines), fault-tolerant "
        "(a bad page is skipped-with-reason and logged, never fatal), "
        "provenance-complete (one `runs` row per batch: model@version, params, git SHA, "
        "counts, wall time), engine-agnostic (segmenter/recogniser injected, so kraken "
        "stays optional), and GPU-aware (`--device`, `--batch-size`; CPU fallback). "
        "`--sample N` caps a run for the dev slice."
    )
    A("")


def _render_coverage(A, rep: SampleReport) -> None:
    A("## Pipeline coverage")
    A("")
    A(f"- **Pages in scope:** {rep.n_pages_total:,}")
    for status in ("pending", "segmented", "recognized", "skipped"):
        n = rep.status_counts.get(status, 0)
        pct = (100.0 * n / rep.n_pages_total) if rep.n_pages_total else 0.0
        A(f"- **{status}:** {n:,} ({pct:.1f}%)")
    A(
        f"- **Lines:** {rep.n_lines:,} segmented · {rep.n_lines_recognized:,} recognised "
        f"(text + confidence)."
    )
    A("")


def _render_throughput(A, rep: SampleReport) -> None:
    if not rep.runs:
        return
    A("## Throughput")
    A("")
    A("| Run | Stage | Model | Input | OK | Failed |")
    A("| ---: | --- | --- | ---: | ---: | ---: |")
    for r in rep.runs:
        A(
            f"| {r['run_id']} | {r['stage']} | {r['model'] or '—'} | "
            f"{r['n_input'] or 0:,} | {r['n_ok'] or 0:,} | {r['n_failed'] or 0:,} |"
        )
    A("")


def _render_confidence(A, rep: SampleReport) -> None:
    A("## Per-line confidence")
    A("")
    if rep.conf_mean is not None:
        A(f"Mean {rep.conf_mean:.3f} · median {rep.conf_median:.3f} over recognised lines.")
        A("")
        A("| Confidence | Lines |")
        A("| --- | ---: |")
        for label, n in rep.conf_hist:
            A(f"| {label} | {n:,} |")
    else:
        A("_No recognised lines with confidence yet (run `leibniz pipeline recognize`)._")
    A("")


def _render_per_set(A, rep: SampleReport) -> None:
    A("## Per set")
    A("")
    if rep.by_set:
        A("| Set | Pages | Segmented | Recognized | Skipped | Mean lines/pg |")
        A("| --- | ---: | ---: | ---: | ---: | ---: |")
        for bd in rep.by_set:
            A(
                f"| {bd.set_name} | {bd.total:,} | {bd.by_status.get('segmented', 0):,} | "
                f"{bd.by_status.get('recognized', 0):,} | {bd.by_status.get('skipped', 0):,} | "
                f"{bd.mean_lines_per_page:.1f} |"
            )
    else:
        A("_No pages processed yet._")
    A("")


def _render_seg_quality(A, rep: SampleReport) -> None:
    A("## Segmentation quality — measured, because it is the known risk")
    A("")
    A(
        "Segmentation is the unsolved half of the corpus (SPECS §9: layered revisions, "
        "marginalia, snippets). C1 measures it per page rather than fixing it blindly: "
        "`page_stats` records `n_lines`/`n_regions`, `region_coverage`, line-height "
        "mean/median/CV (irregular spacing = revised-draft signature), `n_overlaps` "
        "(boxes overlapping ≥30 % — layered revisions / marginalia), and `n_short_lines` "
        "(< 40 % of median width — interlinear insertions / snippets). These are the raw "
        "signal the stratum heuristic reads in C2 (per piece) and C4 (per page)."
    )
    A("")
    s = rep.seg_summary
    if s.get("n_pages"):
        A(
            f"Over {int(s['n_pages']):,} segmented pages: mean "
            f"**{s['mean_lines']:.1f} lines/page**, mean region coverage "
            f"**{s['mean_coverage']:.1%}**, mean line-height CV **{s['mean_cv']:.2f}**. "
            f"**{s['pct_with_overlap']:.1f}%** of pages have overlapping line boxes; "
            f"**{s['pct_with_short']:.1f}%** have short lines."
        )
        A("")
        if rep.overlap_offenders:
            A("Worst-overlap pages (segmentation-risk candidates for inspection):")
            A("")
            A("| Page | Lines | Overlaps |")
            A("| --- | ---: | ---: |")
            for pid, nl, ov in rep.overlap_offenders:
                A(f"| `{pid}` | {nl} | {ov} |")
            A("")
    else:
        A("_No segmentation stats yet (run `leibniz pipeline segment`)._")
    A("")


def _render_taxonomy(A, rep: SampleReport) -> None:
    A("## Skip / failure taxonomy")
    A("")
    if rep.skip_reasons:
        A("| Reason | Pages |")
        A("| --- | ---: |")
        for reason, n in rep.skip_reasons:
            A(f"| {reason} | {n:,} |")
    else:
        A("_No skips recorded._")
    A("")
    A(
        "Anticipated per-set difficulty (quantified once the run completes): "
        "**Marginalien** (44 % of pages) is the hard case — annotated printed books whose "
        "HTR target is the marginal hand, not the printed body (needs zone separation, "
        "STATUS Open Q #5); **Handschriften** carries the layered-revision drafts "
        "(high line-height CV / overlaps / short lines); **Briefwechsel** fair copies are "
        "the clean stratum; German/Kurrent (~15 % of the corpus) is transcribed but at far "
        "higher CER (Latin+French model) — a C4 per-language honesty item, not a skip."
    )
    A("")


def _render_deferred_note(A, rep: SampleReport) -> None:
    A("## Status of the live run")
    A("")
    A(
        "The numeric sections above read zero because the segment/recognize stages need "
        "the optional kraken+torch stack (a multi-GB install plus the PHILIUMM model "
        "files) **and** the local image cache (the A2 full pull is ~365 GB and, like all "
        "`data/`, is gitignored, so it does not travel between sessions); no GPU is "
        "attached in this build environment. Rather than fabricate throughput and "
        "confidence numbers, the pipeline was **built and fully offline-tested** here, and "
        "the sample + corpus runs are the operator commands below — `leibniz pipeline "
        "report` refreshes every number the moment they run."
    )
    A("")
    A(
        "**Machinery verification (this session).** The complete state machine was "
        "exercised end-to-end against fake segmenter/recogniser objects and synthetic page "
        "images: `pending → segmented → recognized` with geometry + text + confidence + "
        "provenance stored, per-page segmentation stats computed, blank pages skipped with "
        "a reason, a raising segmenter isolated to its page, crop/line-count drift handled "
        "as a logged partial, `--redo` without duplicating lines, `--sample`/`--set` "
        "scoping, and `runs` bookkeeping — plus unit tests of the segmentation-stats "
        "geometry on hand-built fair-copy / overlapping / interlinear / blank pages. All "
        "pipeline tests pass; the kraken-absent CLI guard exits cleanly with an install hint."
    )
    A("")


def _render_runbook(A) -> None:
    A("## Operator runbook")
    A("")
    A("```bash")
    A("# 1. Install the heavy stack and fetch the PHILIUMM models (CC BY 4.0).")
    A("uv pip install kraken pyarrow            # the `bench` extra")
    A("leibniz bench fetch                      # HTR model + val split")
    A("")
    A("# 2. Pull a ~500-page dev slice spanning all sets (if not already cached).")
    A("leibniz images fetch --set LeibnizHandschriften --limit 150")
    A("leibniz images fetch --set LeibnizBriefwechsel  --limit 150")
    A("leibniz images fetch --set LeibnizMarginalien   --limit 150")
    A("leibniz images fetch --set Leibnitiana          --limit 50")
    A("")
    A("# 3. Run the pipeline on the sample (GPU if available).")
    A("leibniz pipeline segment   --sample 500 --device cuda")
    A("leibniz pipeline recognize --sample 500 --device cuda --batch-size 32")
    A("leibniz pipeline status")
    A("leibniz pipeline report                  # refreshes this file")
    A("")
    A("# 4. Full corpus (documented; resumable — checkpoint across invocations):")
    A("leibniz pipeline segment   --device cuda")
    A("leibniz pipeline recognize --device cuda --batch-size 32")
    A("leibniz pipeline report")
    A("```")
    A("")
    A("### GPU-hour and cost estimate (full corpus, one pass)")
    A("")
    A(
        "Preliminary, to be calibrated by the sample run's measured pages/hour (recorded "
        "in `runs` wall-time): ~3–6 s/page combined (segment + recognize) on a modern GPU "
        "→ 236,795 pages ≈ **~260 GPU-hours** per pass (range ~120–330 by GPU class / page "
        "size / line density) ≈ **$65–330** at $0.5–1.5/GPU-hour. C1 (v1) and C4 (v2) are "
        "two passes; SPECS §4.2 budgets 150–300 GPU-hours total. CPU-only is fine for the "
        "sample, impractical for the corpus."
    )
    A("")
    A("### Reproduce / regenerate")
    A("")
    A("```")
    A("leibniz pipeline segment [--set S] [--work ID] [--sample N] [--redo] [--device D]")
    A("leibniz pipeline recognize [--sample N] [--redo] [--device D] [--batch-size B]")
    A("leibniz pipeline status")
    A("leibniz pipeline report --out reports/htr-v1-sample.md")
    A("```")
    A("")
    A(
        "Models: segmentation `blla_ft_leibniz_v1` (doi:10.5281/zenodo.21537859) + HTR "
        "`FoNDUE-GD_v2_ft_Leibniz` (doi:10.5281/zenodo.21457538), both PHILIUMM, CC BY 4.0."
    )
    A("")


__all__ = [
    "SampleReport",
    "SetBreakdown",
    "gather_report",
    "render_report",
]
