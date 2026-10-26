"""Tests for the page-language pass (K4 Task 1): offline, on the fixture store."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from tests.conftest import W1, W2, W3, W4
from typer.testing import CliRunner

from leibniz import db
from leibniz.cli import app
from leibniz.enrich import pagelang as P

LATIN = (
    "Vir amplissime, literas tuas accepi quibus de rebus mathematicis ad me scripsisti; ego vero "
    "puto non esse dubitandum quod haec omnia ex principiis nostris deduci possint."
)
GERMAN = (
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten vnd bedancke mich daß Sie mir die "
    "Nachricht so bald haben zukommen lassen; es ist aber nicht zu zweiffeln."
)


def _row(pid: str, top: str | None, hits: dict[str, int], n_tokens: int = 50) -> P.PageLang:
    total = sum(hits.values())
    score = hits.get(top, 0) / total if top and total else 0.0
    lang = top if top and score >= 0.65 and hits.get(top, 0) >= 2 and n_tokens >= 8 else "unknown"
    return P.PageLang(pid, "w", "s", lang, round(score, 4), n_tokens, 10, top, None, dict(hits))


def test_current_texts_take_the_newest_run_per_line(store_path: Path) -> None:
    conn = db.connect(store_path)
    texts = P.current_texts(conn, f"{W1}:0001")
    assert texts[0] == "Calculemus inquit Leibnitius."  # the v2 row, not the v1 one
    assert len(texts) == 3
    assert P.current_texts(conn, f"{W1}:0003") == []  # a skipped page: no text


def test_classify_pages_on_the_fixture_store(german_store_path: Path) -> None:
    conn = db.connect(german_store_path)
    rows = P.classify_pages(conn)
    by_id = {r.page_id: r for r in rows}
    assert all(r.n_lines >= 0 for r in rows)
    # the German draft and the German letter read German on their machine text
    assert by_id[f"{W3}:0001"].lang == "de"
    assert by_id[f"{W3}:0001"].top == "de"
    assert by_id[f"{W3}:0002"].lang == "de"
    # the German letter's one line is six tokens: too short for a verdict
    assert by_id[f"{W4}:0001"].lang == "unknown"
    assert by_id[f"{W4}:0001"].top == "de"
    assert by_id[f"{W4}:0001"].set_name == "LeibnizBriefwechsel"
    # the French page reads French; the short Latin pages carry too few hits
    assert by_id[f"{W2}:0001"].lang == "fr"
    assert by_id[f"{W1}:0001"].lang == "unknown"
    assert f"{W1}:0003" not in by_id  # not recognised
    # the rows survive the JSONL round trip
    out = german_store_path.parent / "page-lang.jsonl"
    P.write_jsonl(out, rows)
    back = P.read_jsonl(out)
    assert [r.as_row() for r in back] == [r.as_row() for r in rows]


def test_threshold_rule() -> None:
    t = P.Threshold()
    assert t.german(_row("a", "de", {"de": 5, "la": 1}))
    assert not t.german(_row("b", "la", {"de": 1, "la": 5}))
    assert not t.german(_row("c", "de", {"de": 1}))  # one hit is not enough
    assert not t.german(_row("d", "de", {"de": 3, "la": 3}))  # no dominance
    assert not t.german(_row("e", "de", {"de": 3}, n_tokens=4))  # too short
    strict = P.Threshold(min_hits=6, min_score=0.9, min_tokens=20)
    assert not strict.german(_row("a", "de", {"de": 5, "la": 1}))
    assert strict.german(_row("f", "de", {"de": 9, "fr": 1}))
    assert strict.key == "hits≥6 score≥0.9 tokens≥20"


def test_measure_sweep_and_pick(tmp_path: Path) -> None:
    rows = [
        _row("p1", "de", {"de": 8}),  # German, clear
        _row("p2", "de", {"de": 2, "la": 1}),  # German, weak
        _row("p3", "la", {"la": 6}),  # Latin, clear
        _row("p4", "de", {"de": 2, "la": 1}),  # Latin page that reads German weakly
        _row("p5", "fr", {"fr": 5}),  # French
        _row("p6", "de", {"de": 3}),  # a page no piece labels
    ]
    labels = P.Labels(group={"p1": "de", "p2": "de", "p3": "la_fr", "p4": "la_fr", "p5": "la_fr"})
    m = P.measure(rows, labels, P.Threshold())
    assert (m.tp, m.fp, m.fn, m.tn) == (2, 1, 0, 2)
    assert m.precision == 2 / 3 and m.recall == 1.0
    strict = P.measure(rows, labels, P.Threshold(min_hits=3))
    assert (strict.tp, strict.fp, strict.fn, strict.tn) == (1, 0, 1, 3)
    assert strict.precision == 1.0 and strict.recall == 0.5
    grid = P.sweep(rows, labels, hits=(2, 3), scores=(0.65,), tokens=(8,))
    assert [g.threshold.min_hits for g in grid] == [2, 3]
    chosen = P.pick(grid, target=0.95)
    assert chosen is not None and chosen.threshold.min_hits == 3
    assert P.pick(grid, target=0.9) is chosen
    assert P.pick(grid[:1], target=0.9) is None
    # the German flag: the threshold's pages joined with the census's
    counts = P.mark_german(rows, P.Threshold(min_hits=3), labels)
    flags = {r.page_id: (r.german, r.evidence) for r in rows}
    assert flags["p1"] == (True, "both")
    assert flags["p2"] == (True, "edition")  # the edition says German, the machine text not
    assert flags["p6"] == (True, "machine")
    assert flags["p3"] == (False, None) and flags["p4"] == (False, None)
    assert counts == {"both": 1, "edition": 1, "machine": 1}
    assert P.german_page_ids(rows) == ["p1", "p2", "p6"]
    listed, n = P.write_page_list(tmp_path / "pages.txt", rows, exclude_sets=["s"])
    assert n == 0 and listed.read_text(encoding="utf-8") == ""
    listed, n = P.write_page_list(tmp_path / "pages.txt", rows)
    assert n == 3 and listed.read_text(encoding="utf-8").split() == ["p1", "p2", "p6"]
    assert P.confusion(rows, P.Labels(lang={"p1": "de", "p3": "la", "p4": "la"})) == {
        "de": {"de": 1},
        "la": {"la": 1, "de": 1},
    }


def test_piece_group() -> None:
    assert P.piece_group(GERMAN) == ("de", "de")
    assert P.piece_group(LATIN) == ("la_fr", "la")
    assert P.piece_group("1680") == ("other", "unknown")


def test_census_labels_on_the_fixture_store(store_path: Path) -> None:
    conn = db.connect(store_path)
    # the fixture's record k-109 (AA VI,4 N. 109, LH IV, 6, 18 Bl. 1-2) is §70-free and
    # covers the work's three pages (1r, 1v, 2r), the skipped one included
    pages = {f"{W1}:0001", f"{W1}:0002", f"{W1}:0003"}
    labels = P.census_labels(conn, {"k-109": LATIN}, today=date(2026, 10, 26))
    assert labels.group == dict.fromkeys(pages, "la_fr")
    assert labels.lang == dict.fromkeys(pages, "la")
    assert labels.n_pieces == {"la_fr": 1}
    assert labels.n_pages == {"la_fr": 3}
    assert labels.negatives() == pages and not labels.positives()
    german = P.census_labels(conn, {"k-109": GERMAN}, today=date(2026, 10, 26))
    assert german.positives() == pages


def test_summary_and_report(german_store_path: Path, tmp_path: Path) -> None:
    conn = db.connect(german_store_path)
    rows = P.classify_pages(conn)
    labels = P.Labels(group={f"{W3}:0001": "de", f"{W3}:0002": "de", f"{W1}:0001": "la_fr"})
    labels.n_pieces, labels.n_pages = {"de": 1, "la_fr": 1}, {"de": 2, "la_fr": 1}
    grid = P.sweep(rows, labels, hits=(2, 4), scores=(0.65, 0.9), tokens=(8,))
    chosen = P.pick(grid, target=0.95)
    threshold = chosen.threshold if chosen else P.Threshold()
    P.mark_german(rows, threshold, labels)
    works = P.tally_works(conn, rows)
    assert works[0].work_id == W3 and works[0].german_pages == 2
    summ = P.summary(
        rows,
        labels=labels,
        sweep_rows=grid,
        chosen=chosen,
        threshold=threshold,
        default=P.measure(rows, labels, P.Threshold()),
        target=0.95,
        works=works,
        today=date(2026, 10, 26),
    )
    assert summ["pages"] == len(rows) and summ["german_pages"] == 2
    assert summ["by_set"]["LeibnizHandschriften"]["german_pages"] == 2
    assert summ["by_set"]["LeibnizBriefwechsel"].get("german_pages", 0) == 0
    assert summ["labels"]["positives"] == 2
    paths = P.write_reports(summ, works, reports_dir=tmp_path)
    md = paths["page-lang.md"].read_text(encoding="utf-8")
    assert "## The measure, on the census's pieces" in md
    assert "## German pages and lines by collection" in md
    assert "| LeibnizHandschriften |" in md
    assert json.loads(paths["page-lang.json"].read_text(encoding="utf-8"))["german_pages"] == 2
    csv_text = paths["page-lang-works.csv"].read_text(encoding="utf-8")
    assert csv_text.splitlines()[0].startswith("work_id,set_name,title,shelfmark,pages")
    assert f"{W3}," in csv_text


def test_cli_page_lang_without_the_cache(german_store_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "page-lang.jsonl"
    pages = tmp_path / "german-pages.txt"
    res = CliRunner().invoke(
        app,
        [
            "enrich",
            "page-lang",
            "--db",
            str(german_store_path),
            "--out",
            str(out),
            "--pages-out",
            str(pages),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--no-measure",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "page-lang" in res.output
    assert pages.read_text(encoding="utf-8").split() == [f"{W3}:0001", f"{W3}:0002"]
    assert (tmp_path / "reports" / "page-lang.md").exists()
    assert len(P.read_jsonl(out)) == 7
    # the same pass re-read with a fixed threshold: one page clears twelve German hits
    res = CliRunner().invoke(
        app,
        [
            "enrich",
            "page-lang",
            "--db",
            str(german_store_path),
            "--out",
            str(out),
            "--pages-out",
            str(pages),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--no-measure",
            "--reuse",
            "--min-hits",
            "12",
            "--list-exclude-set",
            "LeibnizBriefwechsel",
        ],
    )
    assert res.exit_code == 0, res.output
    assert pages.read_text(encoding="utf-8").split() == [f"{W3}:0002"]
    assert "LeibnizBriefwechsel left out" in res.output
