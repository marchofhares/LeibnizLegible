"""The cards of the first releases (REL1): true to the store, to the registry and
to the committed reports; re-rendered with the DOIs from the manifests alone."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from leibniz import db, legal
from leibniz.release import cards as C
from leibniz.release import measured as M
from leibniz.release import state as S
from leibniz.release.export import VERIFIED_MARK, export_all, export_dataset

REPO = Path(__file__).resolve().parents[1]
REAL_AUDIT = {
    "n_rows": 200,
    "n_judged": 199,
    "n_scored": 185,
    "gate": 0.95,
    "weighted_precision": 0.7234,
    "weighted_usable": 0.9218,
    "passes_gate": False,
}


@pytest.fixture
def exported(german_store_path, tmp_path, monkeypatch):
    """The fixture store with the German rows, exported as JSONL with the real
    audit's figures."""
    import leibniz.release.export as E

    monkeypatch.setattr(E, "load_audit_summary", lambda: REAL_AUDIT)
    conn = db.connect(german_store_path)
    out = tmp_path / "release"
    export_all(conn, out, fmt="jsonl")
    return out, conn


def _card(out: Path, dataset: str) -> str:
    return (out / f"leibniz-{dataset}" / "README.md").read_text(encoding="utf-8")


def _front(card: str) -> dict:
    yaml = pytest.importorskip("yaml")
    assert card.startswith("---\n")
    return yaml.safe_load(card.split("---\n")[1])


# ---- the numbers come from the committed reports -------------------------------- #


def test_the_committed_audit_summary_is_the_audit_not_a_test_run() -> None:
    """Until 2026-11 the suite wrote its own 8-line audit over the committed summary
    and the cards (and reports/gt-factory.md) quoted "8 of 8 … 95.0 % … passes"."""
    summary = json.loads((REPO / "reports/gt-audit/audit-summary.json").read_text())
    assert summary["verdicts"] == "gt-audit-verdicts-philiumm.csv"
    assert (summary["n_rows"], summary["n_judged"], summary["n_scored"]) == (200, 199, 185)
    assert round(summary["weighted_precision"], 3) == 0.723 and not summary["passes_gate"]
    assert round(summary["weighted_usable"], 3) == 0.922
    factory = (REPO / "reports/gt-factory.md").read_text(encoding="utf-8")
    assert "8 of 8 sampled" not in factory and "199 of 200 sampled lines" in factory


def test_measured_figures_are_the_reports() -> None:
    m = M.load_measured()
    assert m.missing == ()
    r = m.reader
    # the three figures the operator's note names, as K3's report carries them
    assert str(r.pool) == "28.6 %" and str(r.pool_leibniz) == "36.7 %"
    assert M.pct(r.validation.cer, 2) == "11.84 %"
    assert (r.pool_letters, r.pool_lines, r.validation_lines) == (134, 18815, 3133)
    assert str(r.v1_pool) == "46.6 %" and str(r.v1_pool_leibniz) == "53.7 %"
    labels = [row[0] for row in m.page_test.rows]
    assert labels[0].startswith("k3-trocr") and any("Gemini 4 Argon" in x for x in labels)
    assert (m.page_test.letters, m.page_test.pages) == (34, 98)
    cov = m.coverage
    assert M.pct(cov.precision) == "95.2 %" and M.pct(cov.recall) == "74.5 %"
    assert (cov.german_pages, cov.pages_read, cov.rows_written) == (30797, 24078, 1539688)
    assert (cov.run_id, cov.model) == (617, legal.READER_DE_VERSION)
    assert (cov.batch_size, cov.dtype, cov.use_cache, cov.max_new_tokens) == (
        16,
        "float32",
        True,
        160,
    )
    # B1's constants are the report's
    b1 = (REPO / "reports/philiumm-repro.md").read_text(encoding="utf-8")
    assert f"7.95% (95% CI {M.B1_CER_INTERVAL})" in b1 and "1,878 lines" in b1
    assert M.B1_CER == "7.95 %" and "27.04%" in b1 and M.B1_WER == "27.0 %"


def test_a_missing_report_is_named_and_nothing_is_quoted(tmp_path) -> None:
    m = M.load_measured(tmp_path)
    assert m.reader is None and len(m.missing) == 3
    text = "\n".join(C.error_rates(m))
    assert "28.6" not in text and "reports/kurrent/k3-eval.md" in text
    assert "7.95 %" in text  # B1's stays: it is pinned to its report above


# ---- the transcriptions card ---------------------------------------------------- #


def test_transcriptions_card_names_both_models_per_line(exported) -> None:
    out, _ = exported
    card = _card(out, "transcriptions")
    manifest = json.loads((out / "leibniz-transcriptions" / "MANIFEST.json").read_text())
    by_model = manifest["counts"]["lines"]["by_model"]
    assert "`model`" in card and "`run_id`" in card
    for name, n in by_model.items():  # every model of the export, with the export's count
        assert f"| `{name}` | {n:,} |" in card
    r = legal.site_readers()
    # the German reader with its licence stamps from the registry: model, base, readings
    assert legal.READER_DE_VERSION in card
    assert (
        f"the model {r['de']['model_licence']}, its base {r['de']['base_licence']}, its "
        f"readings {r['de']['readings_licence']}" in card
    )
    assert "obtained under CC BY 4.0, published by its makers under CC BY-NC 4.0" in card
    # K3's and LT1's numbers, each with what it was measured on
    assert "**28.6 %** (95 % CI 24.6–32.5)" in card and "134 German letters" in card
    assert "in Leibniz's own hand **36.7 %**" in card and "**11.84 %**" in card
    assert "3,133 lines of edition text" in card
    assert "LT1, 2026-10-30" in card and "34 letters, 98 pages" in card
    assert "| Gemini 4 Argon (whole pages) | 24.2 % (17.3–31.5) |" in card
    assert "| k3-trocr (this release's German reader; line by line) | 26.9 % (21.9–31.9) |" in card
    assert "**7.95 %** (95 % CI 7.49–8.46)" in card
    # the language pass and its coverage; the Marginalien excepted
    assert "about three quarters of the German pages" in card
    assert "precision of 95.2 % and a recall of 74.5 %" in card
    assert "Marginalien" in card and "keeps the first model's text" in card
    assert "do not ingest as verified text" in card


def test_transcriptions_card_carries_the_inventory_with_its_own_licence_lines(exported) -> None:
    out, _ = exported
    card = _card(out, "transcriptions")
    rows = {m.group(1): m.group(2) for m in re.finditer(r"\| `(\w+)` \|.*\| ([^|]+) \|\n", card)}
    assert rows["lines"] == "CC BY 4.0"
    assert rows["works"] == rows["pages"] == rows["crosswalk"] == "CC0 1.0"
    assert rows["katalog_records"] == "CC BY 4.0"
    # the store holds the website's records here: the credit says so, not "export of …"
    assert "Arbeitskatalog der Leibniz-Edition, Leibniz-Edition Potsdam I (BBAW), CC BY 4.0" in card
    assert "the records read from the catalogue's website" in card
    assert "export of 19 October 2026" not in card
    assert "The inventory tables in this record: **CC0 1.0" in card


def test_katalog_credit_is_the_registry_line_once_the_export_is_imported() -> None:
    credit = legal.arbeitskatalog_credit()["text"]
    imported = {"corpus": {"katalog": {"records": 70405, "refreshed": "2026-10-19"}}}
    assert C.katalog_credit(imported).startswith(credit)
    scraped = {"corpus": {"katalog": {"records": 24916, "refreshed": None}}}
    assert "export of" not in C.katalog_credit(scraped)
    assert "a part of the catalogue" in C.katalog_credit(scraped)


def test_front_matter_is_the_hub_card_metadata(exported) -> None:
    out, _ = exported
    want = {
        "transcriptions": "cc-by-4.0",
        "gt": "cc-by-4.0",
        "gt-nc": "cc-by-nc-4.0",
        "inventory": "cc0-1.0",
    }
    for dataset, licence in want.items():
        card = _card(out, dataset)
        front = _front(card)
        assert front["license"] == licence
        assert front["language"] == ["la", "fr", "de"]
        assert front["task_categories"] == ["image-to-text"]
        assert front["size_categories"] == ["n<1K"] and front["pretty_name"]
        configs = {c["config_name"]: c for c in front["configs"]}
        assert next(iter(configs.values())).get("default") is True
        for cfg in configs.values():
            assert cfg["data_files"] == f"{cfg['config_name']}-*.jsonl.gz"
        # the Markdown below the front matter is the Zenodo README
        assert card.split("---\n", 2)[2].startswith("# leibniz-")
    assert set(_front(_card(out, "transcriptions"))["configs"][0]) >= {"config_name", "data_files"}
    assert C.size_category(12_947_584) == "10M<n<100M" and C.size_category(333_680) == "100K<n<1M"
    assert C.licence_id("CC BY 4.0 (if released)") == "cc-by-4.0"
    assert C.licence_id("Apache-2.0") == "apache-2.0" and C.licence_id("MIT") == "mit"


# ---- the ground-truth cards ------------------------------------------------------ #


def test_both_gt_cards_state_the_audit_as_it_stands(exported) -> None:
    out, _ = exported
    for dataset in ("gt", "gt-nc"):
        card = _card(out, dataset)
        assert "## Audit" in card
        # C2b's precision, with its judge and what it was measured on
        assert "199 of 200 sampled lines (185 scored" in card
        assert "precision 72.3 % as written, which fails the 95 % gate" in card
        assert "92.2 %" in card and "the PHILIUMM team (2026-10-07)" in card
        assert "re-mint of 2026-10-20" in card and "has not been judged again" in card
        # K2's sheet with its judge and the counts of STATUS.md's entry of 2026-11-16
        assert "the Leibniz-Edition's Arbeitsstelle, Potsdam (returned 2026-11-06)" in card
        assert "76 were confirmed as written, 21 marked as a slip at an edge" in card
        assert "98 returned with a corrected transcription and no verdict" in card
        assert "1 judged wrong, 3 unreadable and 1 left blank" in card
        assert "118 corrected transcriptions" in card
        # no precision figure for the German lines before K3b has scored the sheet
        assert "scored in the project's next Kurrent phase (K3b)" in card
        assert "39 %" not in card and "preliminary" not in card
        assert "do not ingest as verified text" in card


def test_k2_audit_note_points_at_the_report_once_it_is_committed() -> None:
    assert "`reports/kurrent/k2-audit.md`" in C.k2_audit_note(report_exists=True)
    assert "scored in the project's next" not in C.k2_audit_note(report_exists=True)
    k = C.K2_AUDIT  # the sheet's lines add up
    judged = (
        k["correct"]
        + k["boundary"]
        + k["transcribed_no_verdict"]
        + k["wrong"]
        + k["unreadable"]
        + k["blank"]
    )
    assert judged == k["lines"] == 200


def test_open_card_says_the_verified_subset_follows_until_the_store_has_it(exported) -> None:
    out, _ = exported
    card = _card(out, "gt")
    assert "**A verified subset follows in the next version**" in card
    assert "This version holds no verified line." in card
    assert "This deposit holds no verified line." in _card(out, "gt-nc")


def test_verified_lines_are_counted_from_the_export_and_credited(tmp_path) -> None:
    """K3b-prep's code is on main: a corrected line carries `channel
    edition-k2-audit` and goes to the open deposit, a confirmed line keeps its
    channel; the sources here are written by `audit_edition.verified_source`, and
    the count is the export's."""
    from leibniz.align import audit_edition as A
    from leibniz.align.pairs import GtPair, insert_gt_pairs

    def verified(source: str, *, corrected: bool) -> str:
        return A.verified_source(
            source,
            by=A.VERIFIED_BY,
            on=A.VERIFIED_ON,
            channel=A.AUDIT_CHANNEL if corrected else None,
        )

    ia = (
        "AA IV,3 N.41 (§70-expired AA reading text; channel ia; reader "
        "trocr-kurrent-xvi-xvii; katalog k-1)"
    )
    potsdam = "AA IV,1 N.2 (§70-expired AA reading text; channel potsdam; katalog k-2)"
    assert VERIFIED_MARK in verified(ia, corrected=False)  # the mark the tally reads
    conn = db.init_db(":memory:")
    insert_gt_pairs(
        conn,
        [
            GtPair(
                "P:0001:000",
                "corrected by the Edition",
                verified(potsdam, corrected=True),  # was Potsdam's copy: now the Edition's text
                "heavy_revision",
                1.0,
                "open",
            ),
            GtPair(
                "P:0001:001", "confirmed", verified(ia, corrected=False), "fair_copy", 0.9, "open"
            ),
            GtPair("P:0001:002", "unjudged", ia, "fair_copy", 0.9, "open"),
            GtPair(
                "P:0002:000",
                "confirmed, potsdam",
                verified(potsdam, corrected=False),
                "scrap",
                0.9,
                "open",
            ),
        ],
    )
    exp = export_dataset(conn, "gt", tmp_path, fmt="jsonl")
    assert exp.row_counts == {"gt_lines": 3}
    assert exp.counts["gt_lines"]["verified"] == 2
    assert exp.counts["gt_lines"]["verified_by_channel"] == {"edition-k2-audit": 1, "ia": 1}
    card = _card(tmp_path, "gt")
    assert "**2 lines of this deposit are verified**" in card
    assert (
        "confirmed or corrected by the Leibniz-Edition's Arbeitsstelle, Potsdam (returned" in card
    )
    assert "1 of them the Edition's own corrected text" in card and "1 confirmed as minted" in card
    assert "released under CC BY 4.0 (the licence registry's `edition-k2-audit`)" in card
    assert "- Verified lines: confirmed or corrected by the Leibniz-Edition's Arbeitsstelle" in card
    assert "follows in the next version" not in card and "`edition-k2-audit` 1" in card
    meta = json.loads((tmp_path / "leibniz-gt.zenodo.json").read_text())["metadata"]
    assert "Verified lines: confirmed or corrected by" in meta["description"]
    nc = export_dataset(conn, "gt-nc", tmp_path, fmt="jsonl")
    assert nc.counts["gt_lines"]["verified"] == 1  # a confirmed NC line stays in the NC deposit
    assert "**1 lines of this deposit are verified**" in _card(tmp_path, "gt-nc")


def test_the_verified_credit_is_the_wording_the_registry_prescribes() -> None:
    """The registry's entry names no credit line yet: its note says the wording is
    to be confirmed and what stands until then. The card uses exactly that, never
    the entry's own name (an artifact's description, not a credit)."""
    entry = legal.artifact("edition-k2-audit")
    assert entry.channel == C.VERIFIED_CHANNEL and entry.deposit == "open"
    assert "credit wording is to be confirmed" in entry.notes
    assert "until then: " + C.VERIFIED_CREDIT_FALLBACK in entry.notes
    assert C.verified_credit() == "the Leibniz-Edition's Arbeitsstelle, Potsdam"
    assert C.verified_licence() == "CC BY 4.0" == entry.obtained.licence
    note = C.verified_note("gt", {"verified": 0})
    assert (
        "by the Leibniz-Edition's Arbeitsstelle, Potsdam (returned 2026-11-06; CC BY 4.0)" in note
    )
    assert entry.name not in note


# ---- DOIs, and the Zenodo record -------------------------------------------------- #


def test_cards_are_rerendered_with_the_dois_without_the_store(exported) -> None:
    out, conn = exported
    conn.close()
    before = _card(out, "transcriptions")
    assert "DOI: to be assigned at deposit" in before
    release = S.load_release(out)
    S.set_doi(release, "transcriptions", "https://doi.org/10.5072/zenodo.1001")
    S.set_doi(release, "gt", "10.5072/zenodo.1002")
    S.set_doi(release, "gt-nc", "doi:10.5072/zenodo.1003")
    S.set_doi(release, "model", "10.5072/zenodo.1004")
    release["hf"]["namespace"] = "leibniz-legible"
    S.save_release(out, release)
    assert C.rerender(out) == ["inventory", "transcriptions", "gt", "gt-nc"]
    card = _card(out, "transcriptions")
    assert "DOI: [10.5072/zenodo.1001](https://doi.org/10.5072/zenodo.1001)" in card
    assert "https://doi.org/10.5072/zenodo.1001. Licensed CC BY 4.0." in card
    assert "https://huggingface.co/datasets/leibniz-legible/leibniz-transcriptions" in card
    for other in ("10.5072/zenodo.1002", "10.5072/zenodo.1003", "10.5072/zenodo.1004"):
        assert other in card  # its siblings
    nc = _card(out, "gt-nc")
    assert "the NC-derived deposit is on Zenodo only" in nc and "huggingface.co" not in nc
    # the same manifest, the same numbers: only the DOI lines moved
    strip = re.compile(r"zenodo\.100\d|DOI: [^\n]*|- (Beside it|Mirror|This record)[^\n]*\n")
    assert strip.sub("", card).count("| `") == strip.sub("", before).count("| `")
    with pytest.raises(ValueError):
        S.set_doi(release, "transcriptions", "not a doi")
    with pytest.raises(ValueError):
        S.set_doi(release, "inventory", "10.5072/zenodo.1")  # no record of its own


def test_zenodo_metadata_is_the_checklists(exported) -> None:
    out, _ = exported
    by = {
        d: json.loads((out / f"leibniz-{d}.zenodo.json").read_text())
        for d in ("transcriptions", "gt", "gt-nc")
    }
    assert not (out / "leibniz-inventory.zenodo.json").exists()  # D1 rides inside D2
    for record in by.values():
        meta = record["metadata"]
        assert meta["upload_type"] == "dataset" and meta["prereserve_doi"] is True
        assert meta["communities"] == [{"identifier": "leibniz"}]
        assert meta["keywords"] == [
            "leibniz",
            "nachlass",
            "handwritten text recognition",
            "htr",
            "iiif",
            "digital humanities",
            "ground truth",
            "machine transcription",
        ]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta["version"])
        assert meta["creators"] == [{"name": "Leibniz Legible"}]
        assert "do not ingest as verified text" in meta["description"]
        assert "<strong>" in meta["description"] and "**" not in meta["description"]
        rel = {(r["relation"], r["identifier"]) for r in meta["related_identifiers"]}
        assert ("isSupplementTo", "https://github.com/marchofhares/leibnizlegible") in rel
        assert ("isDocumentedBy", "10.5281/zenodo.22782813") in rel
        names = [f["name"] for f in record["files"]]
        assert names[:2] == ["README.md", "MANIFEST.json"] and len(set(names)) == len(names)
        assert all((out / f["path"]).is_file() for f in record["files"])
    t = by["transcriptions"]["metadata"]
    assert t["license"] == "cc-by-4.0"
    assert {(r["relation"], r["identifier"]) for r in t["related_identifiers"]} == {
        ("isSupplementTo", "https://github.com/marchofhares/leibnizlegible"),
        ("isDerivedFrom", "10.5281/zenodo.21457538"),
        ("isDerivedFrom", "10.5281/zenodo.21537859"),
        ("isDocumentedBy", "10.5281/zenodo.22782813"),
    }
    # the model's terms as obtained and as published, in the registry's wording
    assert (
        "obtained under CC BY 4.0; published by its makers under CC BY-NC 4.0" in t["description"]
    )
    assert "since 2026-10-15" in t["description"]
    for d, licence in (("gt", "cc-by-4.0"), ("gt-nc", "cc-by-nc-4.0")):
        g = by[d]["metadata"]
        assert g["license"] == licence
        assert {(r["relation"], r["identifier"]) for r in g["related_identifiers"]} == {
            ("isSupplementTo", "https://github.com/marchofhares/leibnizlegible"),
            ("isDerivedFrom", "10.5281/zenodo.21622297"),
            ("isDocumentedBy", "10.5281/zenodo.22782819"),
            ("isDocumentedBy", "10.5281/zenodo.22782813"),
        }
    assert "Leibniz-Edition Potsdam" in by["gt-nc"]["metadata"]["description"]


def test_release_cards_cli_sets_dois_creators_and_namespace(exported) -> None:
    from typer.testing import CliRunner

    from leibniz.cli import app

    out, conn = exported
    conn.close()
    r = CliRunner().invoke(
        app,
        [
            "release",
            "cards",
            "--out",
            str(out),
            "--doi",
            "gt=10.5072/zenodo.2002",
            "--hf-namespace",
            "leibniz-legible",
            "--creator",
            "Family, Given|0000-0002-1825-0097",
        ],
    )
    assert r.exit_code == 0, r.output
    release = S.load_release(out)
    assert release["dois"] == {"gt": "10.5072/zenodo.2002"}
    assert release["creators"] == [{"name": "Family, Given", "orcid": "0000-0002-1825-0097"}]
    meta = json.loads((out / "leibniz-gt.zenodo.json").read_text())["metadata"]
    assert meta["creators"][0]["orcid"] == "0000-0002-1825-0097"
    assert "10.5072/zenodo.2002" in _card(out, "gt")
    assert "For Part C" not in r.output  # one DOI of four
    full = CliRunner().invoke(
        app,
        [
            "release",
            "cards",
            "--out",
            str(out),
            "--doi",
            "transcriptions=10.5072/zenodo.2001",
            "--doi",
            "gt-nc=10.5072/zenodo.2003",
            "--doi",
            "model=10.5072/zenodo.2004",
        ],
    )
    line = next(x for x in full.output.splitlines() if x.startswith("For Part C"))
    assert "transcriptions=10.5072/zenodo.2001 gt=10.5072/zenodo.2002" in line
    assert "model=10.5072/zenodo.2004 · hf=leibniz-legible · version=20" in line
    bad = CliRunner().invoke(app, ["release", "cards", "--out", str(out), "--doi", "gt"])
    assert bad.exit_code != 0
    empty = CliRunner().invoke(app, ["release", "cards", "--out", str(out / "nowhere")])
    assert empty.exit_code != 0
