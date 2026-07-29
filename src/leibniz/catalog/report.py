"""Render ``reports/crosswalk.md`` — the A3 deliverable.

Computes, from the current store, match-rate by set and by method, GWLB-link
resolution quality, and a sample of unmatched records with reasons — written as
a standalone, honest artifact (the target is ≥80% of works matched; we report
whatever the scraped coverage actually yields).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from leibniz import db
from leibniz.catalog import KATALOG_ATTRIBUTION
from leibniz.catalog.shelfmarks import normalize_signature, signature_keys


@dataclass(slots=True)
class SetCoverage:
    set_name: str
    works: int
    matched: int

    @property
    def pct(self) -> float:
        return (100.0 * self.matched / self.works) if self.works else 0.0


@dataclass(slots=True)
class CrosswalkReport:
    generated_at: str
    n_records: int
    n_links: int
    records_matched: int
    records_unmatched: int
    n_works: int
    works_matched: int
    method_counts: dict[str, int]
    gwlb_link_unresolved: int
    coverage_by_set: list[SetCoverage]
    unmatched_foreign: list[tuple[str, str]]  # (record_id, signatur)
    unmatched_with_shelfmark: list[tuple[str, str]]
    sample_queries: list[dict] = field(default_factory=list)
    capped_queries: list[str] = field(default_factory=list)

    @property
    def works_pct(self) -> float:
        return (100.0 * self.works_matched / self.n_works) if self.n_works else 0.0

    @property
    def record_match_pct(self) -> float:
        return (100.0 * self.records_matched / self.n_records) if self.n_records else 0.0


def compute_crosswalk_report(
    conn,
    *,
    generated_at: str,
    sample_queries: list[dict] | None = None,
    capped_queries: list[str] | None = None,
) -> CrosswalkReport:
    """Compute every crosswalk statistic from ``katalog_records`` × ``crosswalk``."""
    n_records = db.count_katalog_records(conn)
    n_links = db.count_crosswalk(conn)
    matched_records = {
        r[0] for r in conn.execute("SELECT DISTINCT katalog_record_id FROM crosswalk")
    }
    method_counts = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT match_method, COUNT(*) FROM crosswalk GROUP BY match_method"
        )
    }

    known_work_ids = {w.gwlb_object_id for w in db.iter_works(conn)}
    matched_work_ids = db.matched_work_ids(conn)

    coverage: list[SetCoverage] = []
    for row in conn.execute(
        "SELECT set_name, COUNT(*) FROM works GROUP BY set_name ORDER BY set_name"
    ):
        set_name, total = row[0], row[1]
        matched = conn.execute(
            "SELECT COUNT(DISTINCT c.work_id) FROM crosswalk c "
            "JOIN works w ON w.gwlb_object_id = c.work_id WHERE w.set_name = ?",
            (set_name,),
        ).fetchone()[0]
        coverage.append(SetCoverage(set_name, total, matched))

    # Pass over records for GWLB-link resolution quality + unmatched samples.
    gwlb_unresolved = 0
    unmatched_foreign: list[tuple[str, str]] = []
    unmatched_with_shelfmark: list[tuple[str, str]] = []
    for rec in db.iter_katalog_records(conn):
        gwlb_unresolved += sum(1 for oid in rec.gwlb_ids if oid not in known_work_ids)
        if rec.record_id in matched_records:
            continue
        signatur = rec.shelfmark_refs[0] if rec.shelfmark_refs else ""
        if signature_keys(rec.shelfmark_refs):
            if len(unmatched_with_shelfmark) < 12:
                unmatched_with_shelfmark.append((rec.record_id, signatur))
        elif len(unmatched_foreign) < 12:
            unmatched_foreign.append((rec.record_id, signatur))

    return CrosswalkReport(
        generated_at=generated_at,
        n_records=n_records,
        n_links=n_links,
        records_matched=len(matched_records),
        records_unmatched=n_records - len(matched_records),
        n_works=len(known_work_ids),
        works_matched=len(matched_work_ids),
        method_counts=method_counts,
        gwlb_link_unresolved=gwlb_unresolved,
        coverage_by_set=coverage,
        unmatched_foreign=unmatched_foreign,
        unmatched_with_shelfmark=unmatched_with_shelfmark,
        sample_queries=sample_queries or [],
        capped_queries=capped_queries or [],
    )


def _fmt(n: int) -> str:
    return f"{n:,}"


def render_crosswalk_report(r: CrosswalkReport) -> str:
    """Render :class:`CrosswalkReport` as ``reports/crosswalk.md``."""
    lines: list[str] = []
    add = lines.append

    add("# Katalog crosswalk — Ritter-Katalog ↔ GWLB works (Phase A3)")
    add("")
    add(
        f"_Leibniz Legible, Phase A3. Generated {r.generated_at}. Joins the BBAW "
        "Arbeitskatalog der Leibniz-Edition (Ritter-Katalog) to our harvested works "
        "so every scan links to its scholarly record and (where catalogued) its AA "
        "volume/piece._"
    )
    add("")
    add(f"> {KATALOG_ATTRIBUTION}")
    add("")

    # -- Scope / method --------------------------------------------------- #
    add("## What this measures")
    add("")
    add(
        "The katalog has **no public API** and caps every query at "
        f"{_fmt(5000)} rows, so a full enumeration of its >70,200 records is an "
        "operator-scale job (see *Operator command*). This run scraped a **bounded "
        "sample** and matched it against all "
        f"{_fmt(r.n_works)} harvested works, by two methods:"
    )
    add("")
    add(
        "- **`gwlb_link` (conf 1.0)** — the record's *Signatur* cell links to the "
        "scan as `…/resolve?id={object_id}`; that id is our works key. Authoritative."
    )
    add(
        "- **`shelfmark` (conf 0.7)** — no link, but the record's signature "
        "normalises to the same key as a work's shelfmark (Roman/Arabic, spacing, "
        "and leaf-suffix tolerant)."
    )
    add("")
    if r.sample_queries:
        qs = ", ".join(
            "`" + "&".join(f"{k}={v}" for k, v in q.items()) + "`" for q in r.sample_queries
        )
        add(f"Sample queries this run: {qs}.")
        add("")

    # -- Headline --------------------------------------------------------- #
    add("## Headline")
    add("")
    add(f"- **Katalog records scraped:** {_fmt(r.n_records)}")
    add(
        f"- **Records matched to a work:** {_fmt(r.records_matched)} "
        f"({r.record_match_pct:.1f}% of scraped)"
    )
    add(f"- **Crosswalk links written:** {_fmt(r.n_links)}")
    add(
        f"- **Distinct works matched:** {_fmt(r.works_matched)} / {_fmt(r.n_works)} "
        f"(**{r.works_pct:.1f}%** of the corpus)"
    )
    by_method = ", ".join(f"{m}: {_fmt(c)}" for m, c in sorted(r.method_counts.items()))
    add(f"- **Links by method:** {by_method or '—'}")
    if r.gwlb_link_unresolved:
        add(
            f"- **GWLB links to non-harvested objects:** {_fmt(r.gwlb_link_unresolved)} "
            "(out-of-scope holdings or non-Leibniz sets — expected, not an error)."
        )
    add("")
    add(
        f"> The ≥80%-of-works target is a **full-scrape** goal. This sample covers "
        f"{r.works_pct:.1f}% of works; the per-set table shows where the sampled "
        "queries landed. Record→work resolution via GWLB links is the quality "
        "signal to read here, not absolute corpus coverage."
    )
    add("")

    # -- Coverage by set -------------------------------------------------- #
    add("## Work coverage by set")
    add("")
    add("| Primary set | Works | Matched | % matched |")
    add("| --- | ---: | ---: | ---: |")
    for c in r.coverage_by_set:
        add(f"| {c.set_name} | {_fmt(c.works)} | {_fmt(c.matched)} | {c.pct:.1f}% |")
    add(
        f"| **All** | **{_fmt(r.n_works)}** | **{_fmt(r.works_matched)}** | "
        f"**{r.works_pct:.1f}%** |"
    )
    add("")

    # -- Unmatched samples ------------------------------------------------ #
    add("## Unmatched records (samples, with reasons)")
    add("")
    add(
        "Two reasons a scraped record has no work: it belongs to a **non-Hannover "
        "holding** (British Library, Cambridge, Paris — out of Tier-1 scope), or it "
        "carries a **Leibniz signature we didn't match** (a work outside the sample, "
        "or a normaliser gap — the latter is the actionable bucket)."
    )
    add("")
    add("**Foreign / out-of-scope holdings:**")
    add("")
    for rid, sig in r.unmatched_foreign[:8]:
        add(f"- `{rid}` — {sig or '(no signature)'}")
    if not r.unmatched_foreign:
        add("- _(none in the sample)_")
    add("")
    add("**Leibniz signature, unmatched (work not in sample, or a normaliser gap):**")
    add("")
    for rid, sig in r.unmatched_with_shelfmark[:8]:
        key = normalize_signature(sig).key
        add(f"- `{rid}` — {sig} → key `{key}`")
    if not r.unmatched_with_shelfmark:
        add("- _(none in the sample)_")
    add("")
    if r.capped_queries:
        add(
            f"⚠️ **Capped queries** (hit the {_fmt(5000)}-row limit, so their slice "
            f"is truncated — narrow them): {', '.join('`' + q + '`' for q in r.capped_queries)}."
        )
        add("")

    # -- Operator command ------------------------------------------------- #
    add("## Operator command (full scrape)")
    add("")
    add(
        "The full crosswalk needs every katalog record. Because of the 5000-row "
        "cap, enumerate in sub-cap slices and let the scraper flag any that still "
        "cap out (then narrow those):"
    )
    add("")
    add("```")
    add("# Correspondence: one slice per AA volume (Reihe × Band)")
    add("leibniz catalog scrape --reihe 1 --bd 1   # … sweep all volumes")
    add("# Manuscripts / Marginalia: by signature prefix, deepened on a cap warning")
    add("leibniz catalog scrape --sign 'LH 1'  --sign 'LH 2'  # …")
    add("leibniz catalog crosswalk && leibniz catalog report")
    add("```")
    add("")
    add(
        "Estimate: ~70k records over sub-cap queries at ≤1 req/s ≈ a few hours of "
        "polite crawling; a TELOTA data dump (SPECS §8) would replace it outright."
    )
    add("")

    add("## Method & caveats")
    add("")
    add(
        "- **Source:** live scrape of `leibniz-katalog.bbaw.de` (server-rendered; "
        "raw HTML cached under `data/katalog/`). No API; 5000-row result cap; no "
        "pagination."
    )
    add(
        "- **Join key:** the GWLB `resolve?id=` link is exact; the shelfmark method "
        "is a normalised-string fallback and can mis-group shared base signatures "
        "(the multi-volume Marginalien; STATUS Open Q #4)."
    )
    add(
        "- **Honesty:** absolute work-coverage here is bounded by the sample, not by "
        "the crosswalk's accuracy. Re-run after the full scrape for the real number."
    )
    return "\n".join(lines) + "\n"


__all__ = [
    "CrosswalkReport",
    "SetCoverage",
    "compute_crosswalk_report",
    "render_crosswalk_report",
]
