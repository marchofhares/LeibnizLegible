"""Corpus census — turn the harvested ``works`` into ``reports/census.md``.

The census is the A1 deliverable and gate: the first real, published page count
of the digitized Leibniz Nachlass. Everything here is computed from the
``works`` table (each row carries ``n_canvases`` from the physical structMap, so
no image or manifest fetch is needed for the count) and rendered as a standalone
markdown artifact.

Two views are reported because the OAI sets overlap heavily (almost every record
is also in ``Leibnitiana``): a **primary-set** view that assigns each work to one
set and therefore sums to the true unique total, and an **OAI-membership** view
that counts a work in every set it belongs to and cross-checks against the
endpoint's own ``completeListSize``.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from leibniz import db
from leibniz.harvest.oai import LEIBNIZ_SETS
from leibniz.harvest.shelfmarks import RECOGNISED, work_family

# Set sizes the OAI endpoint reported for itself, verified live 2026-07-28 via
# ListIdentifiers completeListSize. Used only as a cross-check column.
OAI_COMPLETE_LIST_SIZE: dict[str, int] = {
    "LeibnizHandschriften": 756,
    "LeibnizBriefwechsel": 1060,
    "LeibnizMarginalien": 396,
    "Leibnitiana": 1823,
    "leibniz-rekonstruktionen": 2,
}

# Expected corpus band from SPECS §1 (~200k images); the gate checks against it.
GATE_BAND = (150_000, 250_000)

# Pages-per-work histogram buckets: (inclusive_low, inclusive_high | None, label).
_BUCKETS: tuple[tuple[int, int | None, str], ...] = (
    (0, 0, "0 (no canvases)"),
    (1, 1, "1"),
    (2, 2, "2"),
    (3, 5, "3–5"),
    (6, 10, "6–10"),
    (11, 20, "11–20"),
    (21, 50, "21–50"),
    (51, 100, "51–100"),
    (101, 200, "101–200"),
    (201, 500, "201–500"),
    (501, None, "501+"),
)


@dataclass(slots=True)
class WorkRow:
    """Flattened per-work data the census operates on."""

    object_id: str
    primary_set: str
    n_canvases: int
    title: str | None
    shelfmarks: list[str]
    leibniz_sets: list[str]


@dataclass(slots=True)
class SetStats:
    set_name: str
    oai_size: int | None
    membership_works: int  # counted in every set it belongs to (overlapping)
    primary_works: int  # counted once, under its primary set (dedup)
    primary_pages: int


@dataclass(slots=True)
class CensusData:
    generated_at: str
    n_works: int
    n_pages: int
    set_stats: list[SetStats]
    page_values: list[int]
    histogram: list[tuple[str, int]]
    largest: list[WorkRow]
    coverage_overall: dict[str, int]
    coverage_by_set: dict[str, dict[str, int]]
    zero_canvas: list[WorkRow]
    no_shelfmark: int
    duplicate_shelfmarks: list[tuple[str, list[str]]]
    multi_set_works: int

    @property
    def in_gate_band(self) -> bool:
        return GATE_BAND[0] <= self.n_pages <= GATE_BAND[1]


def _load_works(conn) -> list[WorkRow]:
    rows: list[WorkRow] = []
    for w in db.iter_works(conn):
        meta = w.metadata or {}
        rows.append(
            WorkRow(
                object_id=w.gwlb_object_id,
                primary_set=w.set_name,
                n_canvases=w.n_canvases or 0,
                title=w.title,
                shelfmarks=list(w.shelfmarks or []),
                leibniz_sets=list(meta.get("leibniz_sets") or []),
            )
        )
    return rows


def _histogram(values: list[int]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for low, high, label in _BUCKETS:
        n = sum(1 for v in values if v >= low and (high is None or v <= high))
        out.append((label, n))
    return out


def _coverage(rows: list[WorkRow]) -> dict[str, int]:
    """Count works by shelfmark family, plus 'none' for works with no shelfmark."""
    counts: dict[str, int] = {fam: 0 for fam in RECOGNISED}
    counts["other"] = 0
    counts["none"] = 0
    for r in rows:
        fam = work_family(r.shelfmarks)
        counts["none" if fam is None else fam] += 1
    return counts


def compute_census(conn, *, generated_at: str) -> CensusData:
    """Compute every census statistic from the ``works`` table."""
    rows = _load_works(conn)
    page_values = [r.n_canvases for r in rows]

    set_stats: list[SetStats] = []
    for s in LEIBNIZ_SETS:
        members = [r for r in rows if s in r.leibniz_sets]
        primary = [r for r in rows if r.primary_set == s]
        set_stats.append(
            SetStats(
                set_name=s,
                oai_size=OAI_COMPLETE_LIST_SIZE.get(s),
                membership_works=len(members),
                primary_works=len(primary),
                primary_pages=sum(r.n_canvases for r in primary),
            )
        )

    largest = sorted(rows, key=lambda r: r.n_canvases, reverse=True)[:15]

    coverage_by_set = {s: _coverage([r for r in rows if r.primary_set == s]) for s in LEIBNIZ_SETS}

    # Duplicate shelfmarks: the same exact signature string on more than one work.
    by_shelf: dict[str, list[str]] = {}
    for r in rows:
        for sm in r.shelfmarks:
            by_shelf.setdefault(sm, [])
            if r.object_id not in by_shelf[sm]:
                by_shelf[sm].append(r.object_id)
    duplicate_shelfmarks = sorted(
        ((sm, ids) for sm, ids in by_shelf.items() if len(ids) > 1),
        key=lambda kv: len(kv[1]),
        reverse=True,
    )

    return CensusData(
        generated_at=generated_at,
        n_works=len(rows),
        n_pages=sum(page_values),
        set_stats=set_stats,
        page_values=page_values,
        histogram=_histogram(page_values),
        largest=largest,
        coverage_overall=_coverage(rows),
        coverage_by_set=coverage_by_set,
        zero_canvas=[r for r in rows if r.n_canvases == 0],
        no_shelfmark=sum(1 for r in rows if not r.shelfmarks),
        duplicate_shelfmarks=duplicate_shelfmarks,
        multi_set_works=sum(1 for r in rows if len(r.leibniz_sets) > 1),
    )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _pct(part: int, whole: int) -> str:
    return f"{(100.0 * part / whole):.1f}%" if whole else "—"


def _fmt(n: int) -> str:
    return f"{n:,}"


def render_census(d: CensusData) -> str:
    v = sorted(d.page_values)
    nonzero = [x for x in v if x > 0]
    mean = statistics.mean(v) if v else 0
    median = statistics.median(v) if v else 0
    quartiles = statistics.quantiles(v, n=4) if len(v) >= 2 else [0, 0, 0]
    band_lo, band_hi = GATE_BAND

    lines: list[str] = []
    add = lines.append

    add("# Corpus census — digitized Leibniz Nachlass (GWLB Hannover)")
    add("")
    add(
        f"_Leibniz Legible, Phase A1. Generated {d.generated_at} from the OAI-PMH "
        "harvest of the five Leibniz sets at `digitale-sammlungen.gwlb.de`._"
    )
    add("")
    add(
        "This is, to our knowledge, the **first published page-image count** of the "
        "Hannover Leibniz Nachlass computed from the library's own metadata. Each "
        'work\'s page count is the number of `TYPE="page"` divisions in its METS '
        "*physical* structMap — equal to its IIIF manifest's canvas count (verified "
        "on object 00068642: 4 = 4), so the total needs no image download. Numbers "
        "will drift as the GWLB re-exports; regenerate with `leibniz harvest census`."
    )
    add("")

    # -- Headline ----------------------------------------------------------- #
    add("## Headline")
    add("")
    add(f"- **Unique works (objects):** {_fmt(d.n_works)}")
    add(f"- **Unique page images:** {_fmt(d.n_pages)}")
    verdict = "within" if d.in_gate_band else "**outside**"
    add(
        f"- **Gate:** the count is {verdict} the SPECS §1 expected band "
        f"({_fmt(band_lo)}–{_fmt(band_hi)} images)."
    )
    add("")
    if not d.in_gate_band:
        add(
            "> ⚠️ The total falls outside the expected band — investigate before A2 "
            "(see Method & caveats)."
        )
        add("")

    # -- Per set (dedup) ---------------------------------------------------- #
    add("## Works and pages per set")
    add("")
    add(
        "Each work is assigned to one **primary set** (priority: Handschriften → "
        "Briefwechsel → Marginalien → Rekonstruktionen → Leibnitiana), so these rows "
        "are disjoint and sum to the unique totals. The OAI sets themselves overlap "
        "(next table)."
    )
    add("")
    add("| Primary set | Works | Page images | % of pages |")
    add("| --- | ---: | ---: | ---: |")
    for s in d.set_stats:
        add(
            f"| {s.set_name} | {_fmt(s.primary_works)} | {_fmt(s.primary_pages)} "
            f"| {_pct(s.primary_pages, d.n_pages)} |"
        )
    add(f"| **Total (unique)** | **{_fmt(d.n_works)}** | **{_fmt(d.n_pages)}** | 100% |")
    add("")

    # -- OAI membership cross-check ---------------------------------------- #
    add("## OAI set membership (overlap cross-check)")
    add("")
    add(
        "A work counts once per set it belongs to here, so columns overlap and sum to "
        "more than the unique total. The **OAI size** column is the endpoint's own "
        "`completeListSize` (verified live 2026-07-28); **membership** is what we "
        "parsed and retained — they should match set-by-set."
    )
    add("")
    add("| OAI set | OAI size | Works (membership) | Works (primary) |")
    add("| --- | ---: | ---: | ---: |")
    for s in d.set_stats:
        oai = _fmt(s.oai_size) if s.oai_size is not None else "—"
        add(f"| {s.set_name} | {oai} | {_fmt(s.membership_works)} | {_fmt(s.primary_works)} |")
    add("")
    add(
        f"{_fmt(d.multi_set_works)} of {_fmt(d.n_works)} works "
        f"({_pct(d.multi_set_works, d.n_works)}) belong to more than one Leibniz set — "
        "the reason a naive sum of set sizes "
        f"({_fmt(sum(s.oai_size or 0 for s in d.set_stats))}) overcounts the "
        f"{_fmt(d.n_works)} real objects."
    )
    add("")

    # -- Distribution ------------------------------------------------------- #
    add("## Pages per work")
    add("")
    add(
        f"- Min {min(v) if v else 0} · Max {_fmt(max(v) if v else 0)} · "
        f"Mean {mean:.1f} · Median {median:.0f}"
    )
    add(f"- Quartiles (Q1/Q2/Q3): {quartiles[0]:.0f} / {quartiles[1]:.0f} / {quartiles[2]:.0f}")
    add(f"- Works with ≥1 canvas: {_fmt(len(nonzero))} of {_fmt(len(v))}")
    add("")
    add("| Pages per work | Works |")
    add("| --- | ---: |")
    for label, n in d.histogram:
        add(f"| {label} | {_fmt(n)} |")
    add("")
    add("### Largest works")
    add("")
    add("| Object id | Primary set | Pages | Shelfmark |")
    add("| --- | --- | ---: | --- |")
    for r in d.largest:
        sm = r.shelfmarks[0] if r.shelfmarks else "—"
        add(f"| {r.object_id} | {r.primary_set} | {_fmt(r.n_canvases)} | {sm} |")
    add("")

    # -- Shelfmark coverage ------------------------------------------------- #
    add("## Shelfmark coverage")
    add("")
    add(
        "How many works carry a parseable Leibniz signature (LH / LBr / Leibn. Marg. / "
        "LK). `other` = has a shelfmark that doesn't match those families; `none` = no "
        "`shelfLocator` at all. (Robust normalisation is Phase A3; this is the coarse "
        "family classifier.)"
    )
    add("")
    header_fams = [*RECOGNISED, "other", "none"]
    add("| Set | " + " | ".join(header_fams) + " | parseable % |")
    add("| --- | " + " | ".join(["---:"] * (len(header_fams) + 1)) + " |")
    for s in LEIBNIZ_SETS:
        cov = d.coverage_by_set[s]
        total = sum(cov.values())
        parseable = sum(cov[f] for f in RECOGNISED)
        cells = " | ".join(_fmt(cov[f]) for f in header_fams)
        add(f"| {s} | {cells} | {_pct(parseable, total)} |")
    cov = d.coverage_overall
    total = sum(cov.values())
    parseable = sum(cov[f] for f in RECOGNISED)
    cells = " | ".join(_fmt(cov[f]) for f in header_fams)
    add(f"| **All** | {cells} | **{_pct(parseable, total)}** |")
    add("")

    # -- Anomalies ---------------------------------------------------------- #
    add("## Anomalies")
    add("")
    add(
        f"- **Zero-canvas works:** {_fmt(len(d.zero_canvas))} "
        f"({_pct(len(d.zero_canvas), d.n_works)}). These are container/anchor records "
        "with no physical pages (e.g. multi-part parents)."
    )
    for r in d.zero_canvas[:8]:
        add(f"  - `{r.object_id}` ({r.primary_set}) — {r.title or 'untitled'}")
    add(
        f"- **Works with no shelfmark:** {_fmt(d.no_shelfmark)} "
        f"({_pct(d.no_shelfmark, d.n_works)})."
    )
    add(
        f"- **Shelfmark strings shared by >1 work:** {_fmt(len(d.duplicate_shelfmarks))} "
        "(exact-string; variant normalisations counted separately)."
    )
    for sm, ids in d.duplicate_shelfmarks[:8]:
        add(f"  - `{sm}` → {len(ids)} works ({', '.join(ids[:4])}{'…' if len(ids) > 4 else ''})")
    add("")

    # -- Method ------------------------------------------------------------- #
    add("## Method & caveats")
    add("")
    add(
        "- **Source:** OAI-PMH `ListRecords` (`metadataPrefix=mets`) over sets "
        "`LeibnizHandschriften`, `LeibnizBriefwechsel`, `LeibnizMarginalien`, "
        "`Leibnitiana`, `leibniz-rekonstruktionen`. Raw XML cached under `data/oai/`."
    )
    add(
        "- **Page count = physical structMap `page` divisions.** Cross-checked equal "
        "to IIIF canvas count on sampled objects; a per-work re-check runs during "
        "`leibniz harvest manifests` and any drift is reported there."
    )
    add(
        "- **Overlap is real, not double counting:** the same object appears under "
        "several sets; we dedup by object id. Marginalien are annotated *printed "
        "books* (hence high page counts), not autograph manuscripts — counted as "
        "page images all the same."
    )
    add(
        "- **Scope:** Hannover GWLB holdings only. Non-Hannover Leibniz materials and "
        "transmitted-light fragment scans are out of Tier-1 scope (SPECS §1.1)."
    )
    return "\n".join(lines) + "\n"


__all__ = [
    "GATE_BAND",
    "OAI_COMPLETE_LIST_SIZE",
    "CensusData",
    "SetStats",
    "WorkRow",
    "compute_census",
    "render_census",
]
