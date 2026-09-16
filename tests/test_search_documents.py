"""Index documents from the store."""

from __future__ import annotations

from leibniz import db
from leibniz.search.documents import aa_ref_label, corpus_stats, iter_page_docs, latest_lines

W1 = "00068642"
W2 = "DE-611-HS-854976"


def test_latest_run_wins(store_path) -> None:
    conn = db.connect(store_path)
    lines = latest_lines(conn, f"{W1}:0001")
    assert [ln.line_seq for ln in lines] == [0, 1, 2]
    assert lines[0].text == "Calculemus inquit Leibnitius."
    assert lines[0].model == "leibniz-htr-v2@v2"


def test_docs_cover_recognised_pages_only(store_path) -> None:
    conn = db.connect(store_path)
    docs = list(iter_page_docs(conn))
    assert [d.page_id for d in docs] == [f"{W1}:0001", f"{W1}:0002", f"{W2}:0001"]
    d1 = docs[0]
    assert d1.text.startswith("Calculemus inquit Leibnitius.\n")
    assert d1.n_lines == 3 and d1.lang == "la" and d1.stratum == "unknown"
    assert d1.aa_refs == ["AA VI,4 N. 109"] and d1.katalog == ["k-109"]
    assert docs[1].stratum == "fair_copy"
    assert docs[2].lang == "fr" and docs[2].set_name == "LeibnizBriefwechsel"


def test_docs_filters(store_path) -> None:
    conn = db.connect(store_path)
    assert len(list(iter_page_docs(conn, set_name="LeibnizBriefwechsel"))) == 1
    assert len(list(iter_page_docs(conn, work_id=W1))) == 2
    assert len(list(iter_page_docs(conn, limit=1))) == 1


def test_aa_ref_label() -> None:
    assert aa_ref_label({"series": 1, "volume": "3", "piece": "12"}) == "AA I,3 N. 12"
    assert aa_ref_label({"series": "6", "volume": "4"}) == "AA VI,4"
    assert aa_ref_label({"volume": "4"}) is None


def test_corpus_stats(store_path) -> None:
    conn = db.connect(store_path)
    s = corpus_stats(conn)
    assert s["works"] == 2 and s["pages"] == 4
    assert s["pages_recognized"] == 3 and s["pages_skipped"] == 1
    assert s["lines"] == 8  # 7 lines + the re-read line (a second row)
    assert sum(s["conf_histogram"].values()) == 8
    assert s["model"] == "htr@v1"
