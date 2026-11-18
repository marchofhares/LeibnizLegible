"""Dataset cards (Phase D3; the first releases, REL1): the README that ships
inside every export, and each record's Zenodo metadata.

Each card states the schema, the provenance chain, the licence and the
attribution strings, the known error rates, and the anti-contamination note
SPECS §3.5 demands: *machine output — do not ingest as verified text*. One file
serves both homes: its front matter is the Hugging Face card's metadata and the
Markdown below it is the README of the Zenodo record, whose description
(:func:`description_html`) is built from the same parts.

Where a card states a fact it takes it from one of three places and from nowhere
else: a licence from the licence registry (``leibniz.legal``), a count from the
export's ``MANIFEST.json`` (the rows as they were written), a measured figure
from a committed report (``leibniz.release.measured``). So ``leibniz release
cards`` can render every card again from the manifests — with the DOIs, once
they are reserved — without opening the store.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from leibniz import legal
from leibniz.align.audit import audit_sentence
from leibniz.release import measured as M
from leibniz.release import state as S
from leibniz.web import attribution as attr

# The licence of each card comes from the licence registry (legal.OUTPUTS), so a
# card can never say something the registry does not; ``why`` is quoted under it.
CARD_META = {
    "inventory": {
        "title": "leibniz-inventory — page-level inventory of the digitized Leibniz Nachlass",
        "pretty_name": "Leibniz Legible: page inventory of the Leibniz Nachlass",
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
        "title": (
            "leibniz-transcriptions — machine transcription of the Leibniz Nachlass, "
            "with the page inventory"
        ),
        "pretty_name": "Leibniz Legible: machine transcription of the Leibniz Nachlass",
        "license": legal.output("transcriptions").licence,
        "output": "transcriptions",
        "summary": (
            "One row per recognised manuscript line (deliverable D2): the machine text, "
            "its confidence, the model and run that produced it, its status, and the "
            "image region it was read from; and, in the same record, the page-level "
            "inventory the lines hang on (deliverable D1): works, pages, the catalogue "
            "records and the crosswalk between them. This is machine output with honest "
            "labels — Vorausedition-grade, subordinate to the Akademie-Ausgabe, not an "
            "edition."
        ),
    },
    "gt": {
        "title": "leibniz-gt — retro-aligned ground truth (the open deposit)",
        "pretty_name": "Leibniz Legible: retro-aligned ground truth (open deposit)",
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
        "pretty_name": "Leibniz Legible: retro-aligned ground truth (NC-derived deposit)",
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

# What each inventory table is, and the licence line it travels under: the
# project's own tables CC0, the catalogue records under the catalogue's CC BY.
INVENTORY_TABLE_NOTES = {
    "works": "every GWLB object: set, title, shelfmarks, IIIF manifest, canvas count",
    "pages": "every page image: canvas, folio label, image URLs, delivery mode, size, status",
    "crosswalk": "catalogue record ↔ work, with the match method and its confidence",
    "katalog_records": (
        "the records of the Arbeitskatalog der Leibniz-Edition the store holds: metadata, "
        "shelfmark and Akademie-Ausgabe references"
    ),
}
LINES_TABLE_NOTE = "one row per recognised line: the text, its reader, its place on the page"
GT_TABLE_NOTE = "one row per minted line: the line's place on the page and the edition's text"

# The NC deposit names the publishers whose copies its text was read from.
GT_NC_ATTRIBUTION = (
    "Edition text (the NC channels): Gottfried Wilhelm Leibniz, Sämtliche Schriften und "
    "Briefe (Akademie-Ausgabe) — Reihe IV from the text files of the Leibniz-Edition Potsdam "
    "(Berlin-Brandenburgische Akademie der Wissenschaften), CC BY-NC 4.0 as stated in writing "
    "on 2026-10-12; Reihe I from the volume PDFs of the GWLB's Repositorium des "
    "Leibniz-Archivs, CC BY-NC 4.0. Only the constituted reading text was read, and only "
    "from volumes whose §70 term has run out."
)
GT_OPEN_ATTRIBUTION = (
    "Edition text: Gottfried Wilhelm Leibniz, Sämtliche Schriften und Briefe "
    "(Akademie-Ausgabe), the constituted reading text of volumes whose §70 term has run "
    "out, read from public-domain library scans on the Internet Archive."
)

ANTI_CONTAMINATION = (
    "**Machine output — do not ingest as verified text.** Every row carries the model, "
    "run, confidence and status that produced it (SPECS §4.5). Lines with `status = "
    "'machine'` are unreviewed HTR output; `aligned` lines were matched to a printed "
    "edition; `corrected` lines carry a human or crowd correction; only `verified` lines "
    "were checked by a named expert. Nothing in this release is an edition of Leibniz."
)
# The same rule for a reader that is a training pipeline or a crawler.
ANTI_CONTAMINATION_TRAINING = (
    "If you train on this, keep the provenance columns with the text and say in your own "
    "data statement that it is machine transcription (or, for the ground truth, edition "
    'text placed by a machine); say "the machine reads it as …", never "Leibniz wrote".'
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
    "`src/leibniz/align/volumes_sources.py`), the reader whose text the line was aligned "
    "on where it was not the first model's (`reader trocr-kurrent-xvi-xvii`: the German "
    "pieces), and the catalogue record (`katalog <id>`)."
)

# K2's audit sheet, as the Leibniz-Edition's Arbeitsstelle returned it on
# 2026-11-06: the counts as STATUS.md's entry of 2026-11-16 gives them (counted
# from the returned table). The precision under the aligner's fold is K3b's
# Task 0; :func:`k2_audit_note` names its report once it is committed.
K2_AUDIT = {
    "lines": 200,
    "returned": "2026-11-06",
    "judge": "the Leibniz-Edition's Arbeitsstelle, Potsdam",
    "correct": 76,
    "boundary": 21,
    "transcribed_no_verdict": 98,
    "wrong": 1,
    "unreadable": 3,
    "blank": 1,
    "corrected_transcriptions": 118,
}
K2_AUDIT_REPORT = "reports/kurrent/k2-audit.md"
# The credit of the verified lines until the Edition confirms its wording (the
# operator's note of 2026-11-16); the registry's `edition-k2-audit` entry, once
# on main, takes its place.
VERIFIED_CREDIT_FALLBACK = "the Leibniz-Edition's Arbeitsstelle, Potsdam"
VERIFIED_CHANNEL = "edition-k2-audit"

KEYWORDS = (
    "leibniz",
    "nachlass",
    "handwritten text recognition",
    "htr",
    "iiif",
    "digital humanities",
    "ground truth",
    "machine transcription",
)
ZENODO_COMMUNITY = "leibniz"
# The project's reports on Zenodo (reports/release-checklist.md §4).
DOI_STATEMENT = "10.5281/zenodo.22782813"
DOI_CENSUS = "10.5281/zenodo.22782815"
DOI_B1 = "10.5281/zenodo.22782817"
DOI_GT_REPORT = "10.5281/zenodo.22782819"
DOI_PHILIUMM_DATASET = "10.5281/zenodo.21622297"

HF_LANGUAGES = ("la", "fr", "de")
HF_TAGS = {
    "transcriptions": ("htr", "handwritten-text-recognition", "manuscripts", "leibniz", "iiif"),
    "inventory": ("manuscripts", "leibniz", "iiif", "catalogue"),
    "gt": ("htr", "handwritten-text-recognition", "ground-truth", "manuscripts", "leibniz"),
    "gt-nc": ("htr", "handwritten-text-recognition", "ground-truth", "manuscripts", "leibniz"),
}
_SIZE_BANDS = (
    (1_000, "n<1K"),
    (10_000, "1K<n<10K"),
    (100_000, "10K<n<100K"),
    (1_000_000, "100K<n<1M"),
    (10_000_000, "1M<n<10M"),
    (100_000_000, "10M<n<100M"),
    (1_000_000_000, "100M<n<1B"),
)


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def bare_licence(text: str) -> str:
    """A licence line's name alone: ``"CC BY 4.0 (if released)"`` → ``"CC BY 4.0"``."""
    return text.split(" ·")[0].split(" (")[0].split(",")[0].strip()


def licence_id(text: str) -> str:
    """The SPDX-style id Zenodo and the Hub both take: ``"CC BY-NC 4.0"`` →
    ``"cc-by-nc-4.0"``, ``"CC0 1.0"`` → ``"cc0-1.0"``, ``"Apache-2.0"`` → ``"apache-2.0"``."""
    return bare_licence(text).lower().replace(" ", "-")


def _bare_licence(output_key: str) -> str:
    """The output's licence name alone (``"CC0 1.0"``, ``"CC BY-NC 4.0"``), for the
    citation line."""
    return bare_licence(legal.output(output_key).licence)


def size_category(n: int) -> str:
    """The Hub's ``size_categories`` band of a row count."""
    for bound, label in _SIZE_BANDS:
        if n < bound:
            return label
    return "n>1B"


def doi_link(doi: str) -> str:
    return f"[{doi}](https://doi.org/{doi})"


def _yaml(value: str) -> str:
    """A YAML scalar, quoted (JSON strings are YAML strings)."""
    return json.dumps(value, ensure_ascii=False)


def _main_table(dataset: str) -> str:
    return (
        "gt_lines"
        if dataset in ("gt", "gt-nc")
        else ("works" if dataset == "inventory" else "lines")
    )


def _ext(manifest: dict) -> str:
    return "parquet" if manifest.get("format", "parquet") == "parquet" else "jsonl.gz"


def table_licence(table: str, dataset: str) -> str:
    """The licence line of one table of a record, from the registry."""
    if table == "katalog_records":
        return legal.arbeitskatalog_credit()["licence"]
    if table in INVENTORY_TABLE_NOTES:
        return bare_licence(legal.output("inventory").licence)
    return bare_licence(legal.output(CARD_META[dataset]["output"]).licence)


def katalog_credit(manifest: dict) -> str:
    """The catalogue records' source line: the registry's credit where the store
    holds the Arbeitsstelle's export, and the honest other wording where it still
    holds the records read from the catalogue's website."""
    credit = legal.arbeitskatalog_credit()
    refreshed = ((manifest.get("corpus") or {}).get("katalog") or {}).get("refreshed")
    if refreshed:
        return f"{credit['text']} ({credit['catalogue']['url']})."
    return (
        f"Source: {credit['catalogue']['name']}, {credit['edition']['name']}, "
        f"{credit['licence']} ({credit['catalogue']['url']}): the records read from the "
        "catalogue's website, a part of the catalogue, not the whole of it."
    )


def hf_repo(record: str, release: dict | None) -> str | None:
    """The Hub repository a record is mirrored to, or ``None`` (the NC deposit is
    on Zenodo only; no namespace is known before the operator sets one)."""
    ns = S.hf_namespace(release)
    if not ns or record == "gt-nc" or record == "inventory":
        return None
    return f"{ns}/{S.folder_name(record, release)}"


# --------------------------------------------------------------------------- #
# The Hugging Face front matter
# --------------------------------------------------------------------------- #


def front_matter(dataset: str, manifest: dict) -> str:
    """The card's YAML front matter (Hub dataset-card metadata): licence, languages,
    size, task, the pretty name, and one config per table so the viewer reads each
    table with its own schema."""
    meta = CARD_META[dataset]
    rows = int((manifest.get("row_counts") or {}).get(_main_table(dataset), 0))
    tables = manifest.get("tables") or list(manifest.get("row_counts") or {})
    ext = _ext(manifest)
    out = [
        "---",
        f"license: {licence_id(legal.output(meta['output']).licence)}",
        "language:",
        *[f"- {lang}" for lang in HF_LANGUAGES],
        f"pretty_name: {_yaml(meta['pretty_name'])}",
        "size_categories:",
        f"- {size_category(rows)}",
        "task_categories:",
        "- image-to-text",
        "tags:",
        *[f"- {t}" for t in HF_TAGS[dataset]],
        "configs:",
    ]
    for i, name in enumerate(tables):
        out += [f"- config_name: {name}", f"  data_files: {_yaml(f'{name}-*.{ext}')}"]
        if i == 0:
            out.append("  default: true")
    out += ["---", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #


def licence_section(dataset: str, census: dict | None = None) -> list[str]:
    """The card's licence paragraph(s): the registry's reason, and for a ground-truth
    deposit what it holds by channel (from :func:`leibniz.release.export.gt_deposit_census`)
    and what no deposit takes."""
    meta = CARD_META[dataset]
    out_ = legal.output(meta["output"])
    lines = ["## Licence", "", f"**{out_.licence}.** {out_.why}.", ""]
    if dataset == "transcriptions":
        de = legal.output("readings-de")
        inv = legal.output("inventory")
        lines += [
            f"The German pages' readings: **{de.licence}.** {de.why}.",
            "",
            f"The inventory tables in this record: **{inv.licence}.** {inv.why}.",
            "",
        ]
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


def k2_audit_note(report_exists: bool | None = None) -> str:
    """K2's audit sheet as it came back: who judged it, under which convention, the
    counts; the precision only by pointing at the report that scores it, once that
    report is committed (K3b's Task 0), and "scored in K3b" until then."""
    if report_exists is None:
        report_exists = (M.REPORTS.parent / K2_AUDIT_REPORT).exists()
    k = K2_AUDIT
    scored = (
        f"The precision under the aligner's fold, by hand, is in `{K2_AUDIT_REPORT}`."
        if report_exists
        else "The precision under the aligner's fold is scored in the project's next "
        "Kurrent phase (K3b); until that report exists, treat the German lines' precision "
        "as unmeasured."
    )
    return (
        f"A sheet of {k['lines']} of the German lines, half of them in Leibniz's own hand, "
        f"was judged by {k['judge']} (returned {k['returned']}) under a stricter convention "
        "than the first audit's: *correct* only where the whole line was right as minted, "
        "and otherwise no verdict but the right text of the line written out. Of the "
        f"{k['lines']} lines, {k['correct']} were confirmed as written, {k['boundary']} "
        f"marked as a slip at an edge, {k['transcribed_no_verdict']} returned with a "
        f"corrected transcription and no verdict, {k['wrong']} judged wrong, "
        f"{k['unreadable']} unreadable and {k['blank']} left blank; "
        f"{k['corrected_transcriptions']} corrected transcriptions in all. Read strictly "
        "that is fewer lines right as written than the first audit found, under a standard "
        f"the first audit did not apply, so the two figures do not compare. {scored}"
    )


def verified_credit() -> str:
    """Who verified the verified lines. The registry's entry `edition-k2-audit`
    (K3b-prep, 2026-11-17) says the credit's wording is still to be confirmed and
    what stands until then; that wording is :data:`VERIFIED_CREDIT_FALLBACK`, and a
    test holds the constant to the registry's note. Once the Edition confirms a
    wording it is written into the registry and read from there."""
    return VERIFIED_CREDIT_FALLBACK


def verified_licence() -> str:
    """The licence the Edition's corrected lines are released under, from the
    registry's entry (CC BY 4.0, settled 2026-11-16)."""
    entry = legal.CHANNELS.get(VERIFIED_CHANNEL)
    return bare_licence(entry.obtained.licence) if entry is not None else "CC BY 4.0"


def verified_note(dataset: str, counts: dict | None) -> str:
    """The verified subset of a deposit, counted from the export; before the
    verified lines are in the store, the open card says they follow."""
    n = int((counts or {}).get("verified") or 0)
    if n:
        by = (counts or {}).get("verified_by_channel") or {}
        corrected = int(by.get(VERIFIED_CHANNEL) or 0)
        parts = (
            f", {corrected:,} of them the Edition's own corrected text (`channel "
            f"{VERIFIED_CHANNEL}`) and {n - corrected:,} confirmed as minted"
            if corrected
            else ""
        )
        return (
            f"**{n:,} lines of this deposit are verified**: lines of K2's audit sheet "
            f"confirmed or corrected by {verified_credit()} (returned {K2_AUDIT['returned']}; "
            f"their `source` carries `verified leibniz-edition {K2_AUDIT['returned']}`){parts}. "
            f"The corrected text is the Edition's own, released under {verified_licence()} "
            f"(the licence registry's `{VERIFIED_CHANNEL}`). "
            "They are the only lines of the ground truth a named expert has checked."
        )
    if dataset == "gt":
        return (
            "**A verified subset follows in the next version**: the lines of K2's audit "
            f"sheet confirmed or corrected by {verified_credit()} (returned "
            f"{K2_AUDIT['returned']}; {verified_licence()}). This version holds no verified line."
        )
    return "This deposit holds no verified line."


def audit_section(dataset: str, manifest: dict) -> list[str]:
    """Both ground-truth cards state the audit as it stands: the first audit's
    precision with what it was measured on, K2's sheet with its judge, the
    verified lines."""
    counts = (manifest.get("counts") or {}).get("gt_lines")
    first = gt_audit_note(manifest.get("audit"))
    lines = ["## Audit", ""]
    if manifest.get("audit"):
        lines += [
            f"**The lines minted on the first model's text (Latin, French).** {first} The "
            "sheet was judged by the PHILIUMM team (2026-10-07) on lines of the first mint "
            "(2026-09-16). The lines in this deposit are the re-mint of 2026-10-20, which "
            "keeps the scribe's line-end hyphen the first mint dropped — the audit's most "
            "frequent fault — and has not been judged again: a second sheet is drawn "
            "(`reports/gt-audit/round2/`) and unjudged. Read the figure as the precision of "
            "the method on the first mint, not as a measurement of this file.",
            "",
        ]
    else:
        lines += [first, ""]
    lines += [
        "**The German lines (rows whose `source` names a `reader`).** " + k2_audit_note(),
        "",
        verified_note(dataset, counts),
        "",
    ]
    return lines


def _schema_table(tables: list) -> str:
    out: list[str] = []
    for t in tables:
        out.append(f"### `{t.name}`\n")
        out.append("| column | type |\n| --- | --- |")
        for name, typ in t.schema:
            out.append(f"| `{name}` | {typ} |")
        out.append("")
    return "\n".join(out)


def contents_section(dataset: str, manifest: dict) -> list[str]:
    """What is in the record: one line per table with its rows, its files and its
    own licence line — the transcriptions record carries the inventory inside it."""
    rc = manifest.get("row_counts") or {}
    ext = _ext(manifest)
    lines = [
        "## What is in this record",
        "",
        "| table | rows | files | what | licence |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for name, n in rc.items():
        what = (
            LINES_TABLE_NOTE
            if name == "lines"
            else GT_TABLE_NOTE
            if name == "gt_lines"
            else INVENTORY_TABLE_NOTES.get(name, "")
        )
        lines.append(
            f"| `{name}` | {n:,} | `{name}-NNNN.{ext}` | {what} | {table_licence(name, dataset)} |"
        )
    lines.append("")
    if "katalog_records" in rc:
        lines += [f"The catalogue records: {katalog_credit(manifest)}", ""]
    lines += [
        "`MANIFEST.json` lists every file with its row count and SHA-256, and carries the "
        "counts this card quotes. No image is in this record: every row points at the "
        "GWLB's own scan.",
        "",
    ]
    return lines


def _run_scopes(manifest: dict) -> dict[int, str]:
    runs = (manifest.get("corpus") or {}).get("reading_runs") or []
    return {int(r["run_id"]): r["scope"] for r in runs if r.get("scope")}


def readers_section(manifest: dict, m: M.Measured) -> list[str]:
    """Who read what: both models named per line, the German reader with its
    licence stamps from the registry, the language pass and its coverage."""
    counts = (manifest.get("counts") or {}).get("lines") or {}
    by_model = counts.get("by_model") or {}
    scopes = _run_scopes(manifest)
    r = legal.site_readers()
    de, v1 = r["de"], r["v1"]
    lines = [
        "## Who read what",
        "",
        "Every line names the model that read it in `model` and the run in `run_id` "
        "(`run_at` is the run's date). Two models read this corpus, and each line is "
        "exported once, with the reading the store shows: a correction first, then a run "
        "scoped to a language, then the newest run. A page read by both models therefore "
        "carries the scoped run's text line by line, and a line that run did not write "
        "keeps the first model's.",
        "",
    ]
    if by_model:
        lines += ["| `model` | lines in this export |", "| --- | ---: |"]
        lines += [f"| `{name}` | {n:,} |" for name, n in by_model.items()]
        lines.append("")
    scoped = [
        f"run {row['run_id']} (`{row['model']}`, scope `{scopes[int(row['run_id'])]}`): "
        f"{row['lines']:,} lines"
        for row in counts.get("by_run") or []
        if int(row["run_id"]) in scopes
    ]
    if scoped:
        lines += ["Scoped runs in this export: " + "; ".join(scoped) + ".", ""]
    lines += [
        f"- **Latin, French and everything not called German:** {v1['model']} "
        f"(doi:{attr.PHILIUMM_MODEL_DOI}), on lines found by the PHILIUMM segmentation model "
        f"(doi:{attr.PHILIUMM_SEG_DOI}). The model's licence: obtained under "
        f"{v1['model_licence_obtained']}, published by its makers under {v1['model_licence']} "
        f"today; its readings here: {v1['readings_licence']}.",
        f"- **German pages:** `{de['version']}`, the project's own Kurrent reader "
        f"(`{de['reader']}`): a TrOCR model fine-tuned from {de['base']} on edition text of "
        "Leibniz's German pieces placed on the scans (K2's ground truth). Licences, from "
        f"the registry: the model {de['model_licence']}, its base {de['base_licence']}, its "
        f"readings {de['readings_licence']}.",
        "",
    ]
    cov = m.coverage
    if cov is not None and cov.recall is not None:
        left = (
            f" The pass called {cov.german_pages:,} pages German; the reader read "
            f"{cov.pages_read:,} of them ({cov.rows_written:,} lines written); the others are "
            "pages of the annotated printed books (the Marginalien collection) — print, which a "
            "handwriting model was not given, so they keep the first model's text."
            if cov.german_pages and cov.pages_read and cov.rows_written
            else ""
        )
        lines += [
            "**Which pages are German** was decided by a language pass over the first "
            f"model's text (`leibniz enrich page-lang`, threshold `{cov.threshold}`). Measured "
            "on the pages of the pieces whose language is known from the edition (the "
            f"census), the pass has a precision of {M.pct(cov.precision)} and a recall of "
            f"{M.pct(cov.recall)}: about three quarters of the German pages by that measure are "
            "read by the German reader, and a German page the pass missed keeps the first "
            f"model's text and says so in `model`.{left} (`reports/kurrent/page-lang.md`, "
            "`reports/kurrent/k4-reading.md`.)",
            "",
        ]
    else:
        lines += [
            "Which pages are German was decided by a language pass over the first model's "
            "text; its coverage is in `reports/kurrent/page-lang.md` and "
            "`reports/kurrent/k4-reading.md`. A German page the pass missed keeps the first "
            "model's text and says so in `model`; the annotated printed books (Marginalien) "
            "were left to the first model.",
            "",
        ]
    by_lang = (manifest.get("corpus") or {}).get("pages_by_lang") or {}
    if by_lang:
        lines += [
            "Pages by language of the pass, at export time: "
            + " · ".join(f"`{k}` {n:,}" for k, n in sorted(by_lang.items()))
            + ". The `lang` column of a line is the line's own label and may be empty.",
            "",
        ]
    return lines


def error_rates(m: M.Measured, *, table: bool = True) -> list[str]:
    """The known error rates, each with what it was measured on; the page-level
    comparison (LT1) as a table beside the German reader's numbers."""
    lines = [
        "## Known error rates",
        "",
        f"- **Latin and French** (`{attr.PHILIUMM_MODEL}`): character error rate "
        f"**{M.B1_CER}** (95 % CI {M.B1_CER_INTERVAL}), word error rate {M.B1_WER}, on the "
        f"{M.B1_VAL_LINES:,} lines of the PHILIUMM validation split, line crops "
        f"(`reports/philiumm-repro.md`; doi:{DOI_B1}).",
    ]
    r = m.reader
    if r is not None and r.pool.cer is not None:
        lines.append(
            f"- **German** (`{legal.READER_DE_VERSION}`): on a frozen pool of "
            f"{r.pool_letters} German letters of 1708–1716 ({r.pool_lines:,} recognised lines, "
            "nothing filtered; the reference is the GWLB Leibniz-Archiv's checked "
            f"transcriptions, never trained on) **{r.pool}** (95 % CI "
            f"{M.interval(r.pool.lo, r.pool.hi)}) against {r.v1_pool} for the Latin/French "
            f"model on the same letters; in Leibniz's own hand **{r.pool_leibniz}** (against "
            f"{r.v1_pool_leibniz}), in the correspondents' hands {r.pool_others}; on its "
            f"validation set ({r.validation_lines:,} lines of edition text, whole pieces held "
            f"out) **{M.pct(r.validation.cer, 2)}** (`reports/kurrent/k3-eval.md`). The "
            "letters are the honest figure; the validation set is the edition's reading text "
            "and flatters every reader."
        )
    else:
        lines.append(
            f"- **German** (`{legal.READER_DE_VERSION}`): see `reports/kurrent/k3-eval.md`."
        )
    lines.append("")
    pt = m.page_test
    if table and pt is not None and pt.rows:
        lines += [
            f"**Against frontier vision models reading whole pages** (LT1, {pt.date}): "
            f"{pt.letters} letters, {pt.pages} pages of the same pool, the same metric, a "
            "failed page charged as wholly wrong; character error rate with its 95 % "
            "interval over letters (`reports/htr/page-llm.md`).",
            "",
            "| reader | these letters | Leibniz's hand | the correspondents' hands |",
            "| --- | ---: | ---: | ---: |",
            *[f"| {label} | {a.with_interval} | {b} | {c} |" for label, a, b, c in pt.rows],
            "",
            "On these letters the project's reader and the page models stand inside each "
            "other's intervals: parity on Leibniz's own hand, the page models ahead on the "
            "correspondents' cleaner hands. The sets are small, and the letters are checked "
            "transcriptions of 1708–1716, not a random sample of the German pages.",
            "",
        ]
        if pt.philiumm_best is not None:
            name, c = pt.philiumm_best
            lines += [
                f"On PHILIUMM's {pt.philiumm_pages} held-out Latin and French pages the best "
                f"page model (`{name}`) read at {c.with_interval} page CER; the {M.B1_CER} "
                "above is the dedicated model's line-crop figure from B1 and was not "
                "measured on that harness.",
                "",
            ]
    return lines


def attribution_lines(dataset: str, manifest: dict | None = None) -> list[str]:
    """The attribution lines of a card; a deposit that holds verified lines (the
    manifest's count) credits their judge."""
    de = legal.site_readers()["de"]
    out = [f"- {attr.IMAGES}", f"- {attr.KATALOG}", f"- {attr.TRANSCRIPTIONS}"]
    if dataset in ("transcriptions", "gt", "gt-nc"):
        out.append(
            f"- German pages: {attr.PROJECT_NAME}, machine output of the project's Kurrent "
            f"reader `{de['version']}` ({de['model_licence']}), fine-tuned from {de['base']} "
            f"({de['base_licence']}). {de['readings_licence']}."
        )
    if dataset == "gt":
        out.append(f"- {GT_OPEN_ATTRIBUTION}")
    if dataset == "gt-nc":
        out.append(f"- {GT_NC_ATTRIBUTION}")
    gt_counts = ((manifest or {}).get("counts") or {}).get("gt_lines") or {}
    if dataset in ("gt", "gt-nc") and int(gt_counts.get("verified") or 0):
        out.append(
            f"- Verified lines: confirmed or corrected by {verified_credit()}, "
            f"{K2_AUDIT['returned']}; the corrected text {verified_licence()}."
        )
    return out


def where_section(dataset: str, release: dict | None) -> list[str]:
    """The record's DOI, its mirror, its siblings and the reports that document it."""
    dois = S.dois(release)
    lines = ["## Where this lives", ""]
    own = dois.get(dataset)
    lines.append(
        f"- This record: doi:{doi_link(own)} (Zenodo, community `{ZENODO_COMMUNITY}`)."
        if own
        else "- This record: Zenodo, DOI to be assigned at deposit."
    )
    repo = hf_repo(dataset, release)
    if repo:
        kind = "datasets/"
        lines.append(f"- Mirror: https://huggingface.co/{kind}{repo} (the same files and card).")
    elif dataset == "gt-nc":
        lines.append("- No mirror: the NC-derived deposit is on Zenodo only.")
    names = {
        "transcriptions": "the transcriptions with the inventory (`leibniz-transcriptions`)",
        "gt": "the open ground truth (`leibniz-gt`)",
        "gt-nc": "the NC-derived ground truth (`leibniz-gt-nc`)",
        "model": f"the German reader (`{S.folder_name('model', release)}`)",
    }
    for key, name in names.items():
        if key != dataset and dois.get(key):
            lines.append(f"- Beside it: {name}, doi:{doi_link(dois[key])}.")
    lines += [
        f"- Code: {attr.PROJECT_URL} (Apache-2.0); the site: https://leibnizlegible.com.",
        f"- Documented by: the project statement, doi:{doi_link(DOI_STATEMENT)}"
        + (
            f"; the retro-alignment report, doi:{doi_link(DOI_GT_REPORT)}."
            if dataset in ("gt", "gt-nc")
            else f"; the corpus census, doi:{doi_link(DOI_CENSUS)}; the reproduction of the "
            f"PHILIUMM model, doi:{doi_link(DOI_B1)}."
        ),
        "",
    ]
    return lines


# --------------------------------------------------------------------------- #
# The card
# --------------------------------------------------------------------------- #


def render_card(
    dataset: str,
    manifest: dict,
    *,
    release: dict | None = None,
    measured: M.Measured | None = None,
) -> str:
    """The card of one dataset from its manifest (``MANIFEST.json`` as a dict), the
    release state (DOIs, the Hub namespace) and the committed reports."""
    from leibniz.release.export import TABLES  # the schemas; export imports this module

    meta = CARD_META[dataset]
    m = measured if measured is not None else M.load_measured()
    is_gt = dataset in ("gt", "gt-nc")
    own = S.dois(release).get(dataset)
    generated = manifest.get("generated_at") or ""
    lines = [
        f"# {meta['title']}",
        "",
        f"_Generated {generated} by `leibniz release export` "
        f"(format: {manifest.get('format')}; git {manifest.get('git_sha') or 'n/a'}). "
        + (f"DOI: {doi_link(own)}._" if own else "DOI: to be assigned at deposit._"),
        "",
        meta["summary"],
        "",
        f"**License:** {meta['license']}",
        "",
        *contents_section(dataset, manifest),
    ]
    if dataset == "transcriptions":
        lines += readers_section(manifest, m)
    lines += [
        "## Attribution",
        "",
        *attribution_lines(dataset, manifest),
        "",
        *licence_section(dataset, manifest.get("deposit_census")),
        "## Provenance",
        "",
        "- Images: GWLB digital collections, harvested via OAI-PMH/METS and IIIF "
        "(`leibniz harvest`); page ids are `{gwlb_object_id}:{canvas_seq:04d}`.",
        "- Catalogue: the Leibniz-Katalog's records, joined to the scans by the catalogue's "
        "own GWLB links and by shelfmark (`leibniz catalog`).",
        f"- HTR: PHILIUMM segmentation model (doi:{attr.PHILIUMM_SEG_DOI}) and recognition "
        f"model {attr.PHILIUMM_MODEL} (doi:{attr.PHILIUMM_MODEL_DOI}), run corpus-wide by "
        "`leibniz pipeline` (Phase C1); the German pages read again by "
        f"`{legal.READER_DE_VERSION}` on the same lines (Phase K4).",
        "- Ground truth: §70-expired Akademie-Ausgabe reading text (only the constituted "
        "text; never introductions, apparatus or commentary) retro-aligned onto the machine "
        "lines by `leibniz align factory` (Phases C2, C2c, K2).",
        "",
        "## Row counts",
        "",
    ]
    for name, n in (manifest.get("row_counts") or {}).items():
        lines.append(f"- `{name}`: {n:,}")
    corpus = manifest.get("corpus") or {}
    if corpus:
        lines += [
            "",
            "The store at export time: "
            f"{corpus.get('works', 0):,} works · {corpus.get('pages', 0):,} page records · "
            f"{corpus.get('pages_recognized', 0):,} recognised.",
        ]
    lines += [
        "",
        "## Schema",
        "",
        _schema_table(TABLES[dataset]),
    ]
    if dataset != "inventory":
        lines += error_rates(m, table=dataset == "transcriptions")
    if is_gt:
        lines += [*audit_section(dataset, manifest), GT_PROVENANCE_NOTE, ""]
    lines += [
        "## Use with care",
        "",
        ANTI_CONTAMINATION,
        "",
        ANTI_CONTAMINATION_TRAINING,
        "",
        *where_section(dataset, release),
        "## Citation",
        "",
        f"{attr.PROJECT_NAME} ({generated[:4]}). {meta['title'].split(' — ')[0]} "
        f"(version {generated[:10]}). "
        + (f"https://doi.org/{own}. " if own else f"{attr.PROJECT_URL}. ")
        + f"Licensed {_bare_licence(meta['output'])}.",
        "",
        "Files, row counts and SHA-256 checksums are listed in `MANIFEST.json`.",
        "",
    ]
    return front_matter(dataset, manifest) + "\n".join(lines)


# --------------------------------------------------------------------------- #
# The Zenodo record: description and metadata
# --------------------------------------------------------------------------- #

_INLINE = (
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)"), r'<a href="\2">\1</a>'),
)


def md_inline(text: str) -> str:
    """The inline Markdown a card paragraph uses, as HTML (escaped first)."""
    out = html.escape(text, quote=False)
    for pattern, repl in _INLINE:
        out = pattern.sub(repl, out)
    return out


def _p(text: str) -> str:
    return f"<p>{md_inline(text)}</p>"


def _ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{md_inline(i.removeprefix('- '))}</li>" for i in items) + "</ul>"


def description_html(dataset: str, manifest: dict, *, release: dict | None = None) -> str:
    """The Zenodo description of a dataset record: the card's summary, what the
    record holds, its licence as the registry states it (with the model's terms as
    obtained and as published), the attribution lines and the anti-contamination
    note — the card's own sentences, as HTML."""
    meta = CARD_META[dataset]
    out_ = legal.output(meta["output"])
    rc = manifest.get("row_counts") or {}
    parts = [
        _p(meta["summary"]),
        _p(
            "In this record: "
            + "; ".join(
                f"`{name}` {n:,} rows ({table_licence(name, dataset)})" for name, n in rc.items()
            )
            + ". The full card is `README.md` among the files; `MANIFEST.json` lists every "
            "file with its row count and SHA-256."
        ),
        _p(f"**Licence: {out_.licence}.** {out_.why}."),
    ]
    if "katalog_records" in rc:
        parts.append(_p(f"The catalogue records: {katalog_credit(manifest)}"))
    parts += [
        "<p><strong>Attribution</strong></p>",
        _ul(attribution_lines(dataset, manifest)),
        _p(ANTI_CONTAMINATION),
        _p(ANTI_CONTAMINATION_TRAINING),
    ]
    return "\n".join(parts)


def related_identifiers(record: str) -> list[dict]:
    """The related identifiers of a record, exactly as the release checklist §2
    lists them (§3 for the model)."""
    rel = [{"relation": "isSupplementTo", "identifier": attr.PROJECT_URL, "scheme": "url"}]

    def doi(relation: str, value: str) -> dict:
        return {"relation": relation, "identifier": value, "scheme": "doi"}

    if record == "transcriptions":
        rel += [
            doi("isDerivedFrom", attr.PHILIUMM_MODEL_DOI),
            doi("isDerivedFrom", attr.PHILIUMM_SEG_DOI),
        ]
    elif record in ("gt", "gt-nc"):
        rel += [
            doi("isDerivedFrom", DOI_PHILIUMM_DATASET),
            doi("isDocumentedBy", DOI_GT_REPORT),
        ]
    elif record == "model":
        base = legal.artifact("trocr-kurrent-xvi-xvii")
        rel.append({"relation": "isDerivedFrom", "identifier": base.source, "scheme": "url"})
    rel.append(doi("isDocumentedBy", DOI_STATEMENT))
    return rel


def zenodo_record(
    record: str,
    *,
    title: str,
    description: str,
    licence: str,
    version: str,
    folder: str,
    files: list[dict],
    release: dict | None = None,
    upload_type: str = "dataset",
) -> dict:
    """One record's deposit file: the Zenodo metadata (the deposit API's fields) and
    the files to upload, each with its ``name`` in the record (Zenodo's files are
    flat) and its ``path`` under the release root."""
    return {
        "record": record,
        "folder": folder,
        "files": files,
        "metadata": {
            "upload_type": upload_type,
            "title": title,
            "description": description,
            "creators": S.creators(release),
            "access_right": "open",
            "license": licence_id(licence),
            "version": version,
            "publication_date": version,
            "keywords": list(KEYWORDS),
            "related_identifiers": related_identifiers(record),
            "communities": [{"identifier": ZENODO_COMMUNITY}],
            "prereserve_doi": True,
        },
    }


def zenodo_dataset_record(dataset: str, manifest: dict, *, release: dict | None = None) -> dict:
    meta = CARD_META[dataset]
    version = (manifest.get("generated_at") or "")[:10]
    folder = S.folder_name(dataset, release)
    names = ["README.md", "MANIFEST.json", *[f["path"] for f in manifest.get("files") or []]]
    return zenodo_record(
        dataset,
        title=f"{attr.PROJECT_NAME}: {meta['title']}",
        description=description_html(dataset, manifest, release=release),
        licence=legal.output(meta["output"]).licence,
        version=version,
        folder=folder,
        files=[{"name": n, "path": f"{folder}/{n}"} for n in names],
        release=release,
    )


def zenodo_path(out_root: Path, record: str, release: dict | None = None) -> Path:
    """Where a record's deposit file lies: beside its folder, never inside it (the
    folder is what gets uploaded)."""
    return Path(out_root) / f"{S.folder_name(record, release)}.zenodo.json"


def write_record_files(
    out_root: Path,
    dataset: str,
    manifest: dict,
    *,
    dois: dict | None = None,
    release: dict | None = None,
) -> None:
    """Write a dataset's ``README.md`` into its folder and, for a dataset that is a
    Zenodo record of its own, its deposit file beside the folder."""
    out_root = Path(out_root)
    if release is None:
        release = S.load_release(out_root)
    if dois:
        release = {**release, "dois": {**(release.get("dois") or {}), **dois}}
    folder = out_root / S.folder_name(dataset, release)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text(
        render_card(dataset, manifest, release=release), encoding="utf-8"
    )
    if dataset in S.RECORDS:
        zenodo_path(out_root, dataset, release).write_text(
            json.dumps(
                zenodo_dataset_record(dataset, manifest, release=release),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )


def rerender(out_root: Path, *, release: dict | None = None) -> list[str]:
    """Re-render every dataset card and deposit file under ``out_root`` from the
    manifests there (no store): what ``leibniz release cards`` does once the DOIs
    are reserved. Returns the datasets it found."""
    out_root = Path(out_root)
    if release is None:
        release = S.load_release(out_root)
    done: list[str] = []
    for dataset in CARD_META:
        path = out_root / f"leibniz-{dataset}" / "MANIFEST.json"
        if not path.exists():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        write_record_files(out_root, dataset, manifest, release=release)
        done.append(dataset)
    return done


__all__ = [
    "ANTI_CONTAMINATION",
    "ANTI_CONTAMINATION_TRAINING",
    "CARD_META",
    "GT_AUDIT_NOTE",
    "GT_NC_ATTRIBUTION",
    "GT_OPEN_ATTRIBUTION",
    "GT_PROVENANCE_NOTE",
    "K2_AUDIT",
    "KEYWORDS",
    "ZENODO_COMMUNITY",
    "attribution_lines",
    "audit_section",
    "bare_licence",
    "description_html",
    "doi_link",
    "error_rates",
    "front_matter",
    "gt_audit_note",
    "hf_repo",
    "k2_audit_note",
    "katalog_credit",
    "licence_id",
    "licence_section",
    "md_inline",
    "readers_section",
    "related_identifiers",
    "render_card",
    "rerender",
    "size_category",
    "table_licence",
    "verified_note",
    "write_record_files",
    "zenodo_dataset_record",
    "zenodo_path",
    "zenodo_record",
]
