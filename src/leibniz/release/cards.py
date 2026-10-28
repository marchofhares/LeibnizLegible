"""Dataset cards (Phase D3): the README that ships inside every export.

Each card states the schema, the provenance chain, the licence and the
attribution strings, the known error rates, and the anti-contamination note
SPECS §3.5 demands: *machine output — do not ingest as verified text*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from leibniz import legal
from leibniz.align.audit import audit_sentence
from leibniz.web import attribution as attr

if TYPE_CHECKING:  # pragma: no cover
    from leibniz.release.export import DatasetExport, TableSpec

# The licence of each card comes from the licence registry (legal.OUTPUTS), so a
# card can never say something the registry does not; ``why`` is quoted under it.
CARD_META = {
    "inventory": {
        "title": "leibniz-inventory — page-level inventory of the digitized Leibniz Nachlass",
        "license": legal.output("inventory").licence,
        "output": "inventory",
        "summary": (
            "The canonical page-level inventory (deliverable D1): every GWLB work "
            "(object) with its shelfmarks and IIIF manifest, every page image with its "
            "canvas, delivery mode and image URLs, the crosswalk to the Leibniz-Katalog "
            "records, and the katalog records themselves. Metadata only — no images."
        ),
    },
    "transcriptions": {
        "title": "leibniz-transcriptions — machine transcription of the Leibniz Nachlass",
        "license": legal.output("transcriptions").licence,
        "output": "transcriptions",
        "summary": (
            "One row per recognised manuscript line (deliverable D2): the machine text, "
            "its confidence, the model and run that produced it, its status, and the "
            "image region it was read from. This is machine output with honest labels — "
            "Vorausedition-grade, subordinate to the Akademie-Ausgabe, not an edition."
        ),
    },
    "gt": {
        "title": "leibniz-gt — retro-aligned ground truth (the open deposit)",
        "license": (
            f"{legal.output('gt-open').licence} (the open deposit: lines whose edition text "
            "came through a channel with no terms of its own; the NC-derived lines are the "
            "separate deposit leibniz-gt-nc)"
        ),
        "output": "gt-open",
        "summary": (
            "Line image references paired with the reading text of §70-expired "
            "Akademie-Ausgabe volumes, minted by forced alignment onto machine "
            "transcriptions (deliverable D3), with the stratum and alignment confidence "
            "per line. Precision is estimated, not verified: see the audit note."
        ),
    },
    "gt-nc": {
        "title": "leibniz-gt-nc — retro-aligned ground truth (the NC-derived deposit)",
        "license": (
            f"{legal.output('gt-nc').licence} (the NC-derived deposit: lines whose edition "
            "text came through a channel with non-commercial terms; the rest is the deposit "
            "leibniz-gt)"
        ),
        "output": "gt-nc",
        "summary": (
            "Line image references paired with the reading text of §70-expired "
            "Akademie-Ausgabe volumes, read from copies whose publishers state "
            "non-commercial terms (deliverable D3, the second deposit), minted by forced "
            "alignment onto machine transcriptions, with the stratum and alignment "
            "confidence per line. Precision is estimated, not verified: see the audit note."
        ),
    },
}

# The NC deposit names the publishers whose copies its text was read from.
GT_NC_ATTRIBUTION = (
    "Edition text (the NC channels): Gottfried Wilhelm Leibniz, Sämtliche Schriften und "
    "Briefe (Akademie-Ausgabe) — Reihe IV from the text files of the Leibniz-Edition Potsdam "
    "(Berlin-Brandenburgische Akademie der Wissenschaften), CC BY-NC 4.0 as stated in writing "
    "on 2026-10-12; Reihe I from the volume PDFs of the GWLB's Repositorium des "
    "Leibniz-Archivs, CC BY-NC 4.0. Only the constituted reading text was read, and only "
    "from volumes whose §70 term has run out."
)

ANTI_CONTAMINATION = (
    "**Machine output — do not ingest as verified text.** Every row carries the model, "
    "run, confidence and status that produced it (SPECS §4.5). Lines with `status = "
    "'machine'` are unreviewed HTR output; `aligned` lines were matched to a printed "
    "edition; `corrected` lines carry a human or crowd correction; only `verified` lines "
    "were checked by a named expert. Nothing in this release is an edition of Leibniz."
)

ERROR_RATES = (
    "Measured character error rate of the model on the PHILIUMM validation split "
    "(1,878 Latin/French lines): **7.95 %** (95 % CI 7.49–8.46), word error rate 27.0 %. "
    "German pages are read by a second model, the project's own Kurrent model "
    "(`k3-trocr@runs-615-epoch-5`, a TrOCR model fine-tuned from the Bern Kurrent model on "
    "edition text; Phase K3/K4): on a frozen pool of 134 German letters of 1708–1716 "
    "(18,815 recognised lines, the GWLB Leibniz-Archiv's checked transcriptions as the "
    "reference) its character error rate is **28.6 %** (95 % CI 24.6–32.5) against 46.6 % "
    "for the Latin/French model on the same lines; in Leibniz's own hand 36.7 % against "
    "53.7 %. Each line names the model that read it (`model`). "
    "See `reports/philiumm-repro.md` and `reports/kurrent/k3-letterpool/letterpool-eval.md`."
)

# The card's audit paragraph without numbers, for an export run where no scored
# audit summary exists. Where one does (`leibniz align audit-score` writes
# reports/gt-audit/audit-summary.json), :func:`gt_audit_note` quotes it; until
# 2026-10 this constant still read "97.5 % … preliminary (20 of 200)" after the
# audit had been scored.
GT_AUDIT_NOTE = (
    "The minted lines' precision is measured by a stratified hand audit "
    "(`reports/gt-audit.md`). Treat `align_conf` as the per-line signal."
)

GT_PROVENANCE_NOTE = (
    "Each row's `source` names the printed piece(s) its text was read from, the free "
    "copy of the volume it was read from where the factory recorded it (`channel ia`, "
    "`gwlb` or `potsdam`; the terms of each channel are in "
    "`src/leibniz/align/volumes_sources.py`), and the catalogue record (`katalog <id>`)."
)


def _bare_licence(output_key: str) -> str:
    """The output's licence name alone (``"CC0 1.0"``, ``"CC BY-NC 4.0"``), for the
    citation line."""
    return legal.output(output_key).licence.split(" ·")[0].split(" (")[0]


def licence_section(dataset: str, census: dict | None = None) -> list[str]:
    """The card's licence paragraph(s): the registry's reason, and for a ground-truth
    deposit what it holds by channel (from :func:`leibniz.release.export.gt_deposit_census`)
    and what no deposit takes."""
    meta = CARD_META[dataset]
    out_ = legal.output(meta["output"])
    lines = ["## Licence", "", f"**{out_.licence}.** {out_.why}.", ""]
    if dataset in ("gt", "gt-nc") and census is not None:
        deposit = "open" if dataset == "gt" else "nc"
        held = census.get(deposit) or {}
        other = "nc" if deposit == "open" else "open"
        other_n = sum((census.get(other) or {}).values())
        none_n = sum((census.get("none") or {}).values())
        if held:
            by = " · ".join(f"`{ch}` {n:,}" for ch, n in sorted(held.items()))
            lines.append(
                f"Channels in this deposit (the `channel` each row's `source` names), lines: {by}."
            )
        else:
            lines.append("This deposit holds no lines in this export.")
        lines.append(
            f"Left to the other deposit (`leibniz-gt{'-nc' if deposit == 'open' else ''}`): "
            f"{other_n:,} lines; released in neither (a channel the registry does not release, "
            f"or an nc-bucket row without a channel): {none_n:,} of {census.get('rows', 0):,} rows."
        )
        lines.append("")
        lines.append(
            "The registry: `src/leibniz/legal.py` (`leibniz legal licences`); the channels' "
            "terms as the factory recorded them: `src/leibniz/align/volumes_sources.py`."
        )
        lines.append("")
    return lines


def gt_audit_note(summary: dict | None) -> str:
    """The audit paragraph, quoting the scored audit where its summary exists."""
    sentence = audit_sentence(summary)
    if sentence is None:
        return GT_AUDIT_NOTE
    return f"{sentence} Treat `align_conf` as the per-line signal."


def _schema_table(tables: list[TableSpec]) -> str:
    out: list[str] = []
    for t in tables:
        out.append(f"### `{t.name}`\n")
        out.append("| column | type |\n| --- | --- |")
        for name, typ in t.schema:
            out.append(f"| `{name}` | {typ} |")
        out.append("")
    return "\n".join(out)


def render_card(
    dataset: str,
    tables: list[TableSpec],
    exp: DatasetExport,
    *,
    stats: dict | None = None,
    audit_summary: dict | None = None,
    deposit_census: dict | None = None,
) -> str:
    meta = CARD_META[dataset]
    is_gt = dataset in ("gt", "gt-nc")
    lines = [
        f"# {meta['title']}",
        "",
        f"_Generated {exp.generated_at} by `leibniz release export` "
        f"(format: {exp.fmt}; git {exp.git_sha or 'n/a'}). DOI: to be assigned at deposit._",
        "",
        meta["summary"],
        "",
        f"**License:** {meta['license']}",
        "",
        "## Attribution",
        "",
        f"- {attr.IMAGES}",
        f"- {attr.KATALOG}",
        f"- {attr.TRANSCRIPTIONS}",
        *([f"- {GT_NC_ATTRIBUTION}"] if dataset == "gt-nc" else []),
        "",
        *licence_section(dataset, deposit_census),
        "## Provenance",
        "",
        "- Images: GWLB digital collections, harvested via OAI-PMH/METS and IIIF "
        "(`leibniz harvest`); page ids are `{gwlb_object_id}:{canvas_seq:04d}`.",
        "- Catalogue: Leibniz-Katalog records scraped politely and joined by the "
        "katalog's own GWLB links (`leibniz catalog`).",
        f"- HTR: PHILIUMM segmentation model (doi:{attr.PHILIUMM_SEG_DOI}) and recognition "
        f"model {attr.PHILIUMM_MODEL} (doi:{attr.PHILIUMM_MODEL_DOI}), run corpus-wide by "
        "`leibniz pipeline` (Phase C1).",
        "- Ground truth: §70-expired Akademie-Ausgabe reading text (only the constituted "
        "text; never introductions, apparatus or commentary) retro-aligned onto the machine "
        "lines by `leibniz align factory` (Phase C2).",
        "",
        "## Row counts",
        "",
    ]
    for name, n in exp.row_counts.items():
        lines.append(f"- `{name}`: {n:,}")
    if stats:
        lines += [
            "",
            "Corpus at export time: "
            f"{stats.get('works', 0):,} works · {stats.get('pages', 0):,} pages · "
            f"{stats.get('pages_recognized', 0):,} recognised · {stats.get('lines', 0):,} lines.",
        ]
    lines += [
        "",
        "## Schema",
        "",
        _schema_table(tables),
        "## Known error rates",
        "",
        ERROR_RATES,
        "",
    ]
    if is_gt:
        lines += [gt_audit_note(audit_summary), "", GT_PROVENANCE_NOTE, ""]
    lines += [
        "## Use with care",
        "",
        ANTI_CONTAMINATION,
        "",
        "## Citation",
        "",
        f"{attr.PROJECT_NAME} ({exp.generated_at[:4]}). {meta['title'].split(' — ')[0]}. "
        f"{attr.PROJECT_URL}. Licensed {_bare_licence(meta['output'])}.",
        "",
        "Files, row counts and SHA-256 checksums are listed in `MANIFEST.json`.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "ANTI_CONTAMINATION",
    "CARD_META",
    "ERROR_RATES",
    "GT_AUDIT_NOTE",
    "GT_NC_ATTRIBUTION",
    "GT_PROVENANCE_NOTE",
    "gt_audit_note",
    "licence_section",
    "render_card",
]
