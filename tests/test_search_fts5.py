"""SQLite FTS5 backend."""

from __future__ import annotations

from leibniz import db
from leibniz.search import open_backend
from leibniz.search.backend import SearchQuery
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import Fts5Backend, match_expression

W1 = "00068642"
W2 = "DE-611-HS-854976"


def _build(store_path, tmp_path) -> Fts5Backend:
    be = Fts5Backend(tmp_path / "search.sqlite")
    conn = db.connect(store_path)
    n = be.rebuild(iter_page_docs(conn), meta={"stats": corpus_stats(conn)})
    conn.close()
    assert n == 3
    return be


def test_match_expression() -> None:
    assert match_expression(["calcul", "ut", 'a"b']) == '"calcul"* "ut" "ab"'


def test_build_and_search(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    assert be.count() == 3
    res = be.search(SearchQuery(q="Calculemus"))
    assert res.total == 1 and res.backend == "fts5"
    hit = res.hits[0]
    assert hit.page_id == f"{W1}:0001" and hit.label == "1r"
    assert "<mark>Calculemus</mark>" in hit.snippet
    assert hit.to_dict()["set"] == "LeibnizHandschriften"


def test_orthography_folding_and_prefix(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    assert be.search(SearchQuery(q="ut sit")).hits[0].page_id == f"{W1}:0002"  # 'vt' on the page
    assert be.search(SearchQuery(q="Jesus")).total == 1  # 'Jeſus'
    assert be.search(SearchQuery(q="combinat")).total == 1  # prefix
    assert be.search(SearchQuery(q="grace")).total == 1  # 'grâce'


def test_filters_and_paging(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    assert be.search(SearchQuery(q="de", set_name="LeibnizBriefwechsel")).total == 1
    assert be.search(SearchQuery(q="de", lang="fr")).hits[0].work_id == W2
    assert be.search(SearchQuery(q="de", min_conf=0.85)).total == 1
    assert be.search(SearchQuery(q="de", work_id=W1)).total == 1
    assert be.search(SearchQuery(q="de", stratum="heavy_revision")).total == 0
    paged = be.search(SearchQuery(q="de", limit=1, page=2))
    assert paged.total == 2 and len(paged.hits) == 1 and paged.page == 2


def test_title_and_aa_reference_match(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    assert be.search(SearchQuery(q="LBr 464")).hits[0].work_id == W2
    assert be.search(SearchQuery(q="AA VI,4 N. 109")).total == 2


def test_empty_query_and_missing_index(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    assert be.search(SearchQuery(q="   ")).total == 0
    missing = Fts5Backend(tmp_path / "nope.sqlite")
    assert missing.search(SearchQuery(q="x")).total == 0
    assert missing.meta() == {} and missing.count() == 0


def test_meta_and_open_backend(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    meta = be.meta()
    assert meta["n_docs"] == 3 and meta["stats"]["pages"] == 4 and meta["built_at"]
    again = open_backend("fts5", path=str(tmp_path / "search.sqlite"))
    assert again.count() == 3
