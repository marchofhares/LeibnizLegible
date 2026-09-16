"""Dataset cards (Phase D3): the README that ships inside every export.

Each card states the schema, the provenance chain, the licence and the
attribution strings, the known error rates, and the anti-contamination note
SPECS §3.5 demands: *machine output — do not ingest as verified text*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from leibniz.web import attribution as attr

if TYPE_CHECKING:  # pragma: no cover
    from leibniz.release.export import DatasetExport, TableSpec

CARD_META = {
    "inventory": {
        "title": "leibniz-inventory — page-level inventory of the digitized Leibniz Nachlass",
        "license": "CC0 1.0 (inventory) · katalog records CC BY 4.0 (BBAW/TELOTA)",
        "summary": (
            "The canonical page-level inventory (deliverable D1): every GWLB work "
            "(object) with its shelfmarks and IIIF manifest, every page image with its "
            "canvas, delivery mode and image URLs, the crosswalk to the Leibniz-Katalog "
            "records, and the katalog records themselves. Metadata only — no images."
        ),
    },
    "transcriptions": {
        "title": "leibniz-transcriptions — machine transcription of the Leibniz Nachlass",
        "license": "CC BY 4.0",
        "summary": (
            "One row per recognised manuscript line (deliverable D2): the machine text, "
            "its confidence, the model and run that produced it, its status, and the "
            "image region it was read from. This is machine output with honest labels — "
            "Vorausedition-grade, subordinate to the Akademie-Ausgabe, not an edition."
        ),
    },
    "gt": {
        "title": "leibniz-gt — retro-aligned ground truth (open bucket)",
        "license": "CC BY 4.0 (open bucket only; NC-derived pairs are never exported)",
        "summary": (
            "Line image references paired with the reading text of §70-expired "
            "Akademie-Ausgabe volumes, minted by forced alignment onto machine "
            "transcriptions (deliverable D3), with the stratum and alignment confidence "
            "per line. Precision is estimated, not verified: see the audit note."
        ),
    },
}

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
    "German/Kurrent lines are transcribed by the same Latin/French model and are expected "
    "to be far worse; they are unmeasured until the per-language pass (Phase C4). "
    "See `reports/philiumm-repro.md`."
)

GT_AUDIT_NOTE = (
    "The minted lines' precision was measured at 97.5 % on favourable material in the "
    "prototype (`reports/alignment-prototype.md`); the corpus mint's hand audit is "
    "preliminary (20 of 200 lines judged; `reports/gt-audit.md`) and the precision gate "
    "is deferred to the fine-tuning ablation. Treat `align_conf` as the per-line signal."
)


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
    dataset: str, tables: list[TableSpec], exp: DatasetExport, *, stats: dict | None = None
) -> str:
    meta = CARD_META[dataset]
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
        "",
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
    if dataset == "gt":
        lines += [GT_AUDIT_NOTE, ""]
    lines += [
        "## Use with care",
        "",
        ANTI_CONTAMINATION,
        "",
        "## Citation",
        "",
        f"{attr.PROJECT_NAME} ({exp.generated_at[:4]}). {meta['title'].split(' — ')[0]}. "
        f"{attr.PROJECT_URL}. Licensed {meta['license'].split(' ·')[0]}.",
        "",
        "Files, row counts and SHA-256 checksums are listed in `MANIFEST.json`.",
        "",
    ]
    return "\n".join(lines)


__all__ = ["ANTI_CONTAMINATION", "CARD_META", "ERROR_RATES", "GT_AUDIT_NOTE", "render_card"]
