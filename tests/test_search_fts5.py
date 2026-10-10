"""SQLite FTS5 backend."""

from __future__ import annotations

import random

from leibniz import db
from leibniz.search import open_backend
from leibniz.search.backend import SearchQuery
from leibniz.search.documents import corpus_stats, iter_page_docs
from leibniz.search.fts5 import Fts5Backend, match_expression, match_query
from leibniz.search.normalize import parse_query

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


def test_match_query() -> None:
    assert match_query(parse_query("Calculemus ut")) == match_expression(["calculemus", "ut"])
    assert match_query(parse_query('"arte combinatoria" de')) == '"arte combinatoria" "de"'
    assert match_query(parse_query('de -"la nature" -grâce')) == (
        '("de") NOT ("la nature" OR "grace")'
    )


def test_phrases_and_exclusions(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)

    def pages(q: str) -> list[str]:
        return sorted(h.page_id for h in be.search(SearchQuery(q=q)).hits)

    p1, p2, q1 = f"{W1}:0001", f"{W1}:0002", f"{W2}:0001"
    assert pages('"arte combinatoria"') == [p1]
    assert pages('"combinatoria arte"') == []  # the order is part of the phrase
    assert pages("„ut sit veritas“") == [p2]  # folded inside quotes: the page reads 'vt'
    assert pages("de") == [p1, q1]
    assert pages("de -nature") == pages('de -"la nature"') == [p1]
    assert pages('de -"nature la"') == [p1, q1]  # an excluded phrase is excluded in order
    assert pages("combinat") == [p1] and pages('"combinat"') == []  # quoted: exact, no prefix
    assert be.search(SearchQuery(q="-de")).total == 0  # exclusions alone select nothing
    hit = be.search(SearchQuery(q='"Calculemus inquit"')).hits[0]
    assert hit.snippet.startswith("<mark>Calculemus inquit</mark>")
    # quoted references still find their work: FTS5 folds those columns too
    assert pages('"AA VI,4 N. 109"') == [p1, p2]
    assert pages('"LBr. 464"') == [q1]


def test_hostile_queries_never_reach_fts5_as_syntax(store_path, tmp_path) -> None:
    """Quotes of every kind, minus signs, FTS5's own operators and punctuation:
    whatever is typed, the MATCH stays well-formed and the search answers."""
    be = _build(store_path, tmp_path)
    rng = random.Random(1646)
    pieces = list("abde \"\u201c\u201d\u201e\u201f\u00ab\u00bb-*^:+(){}[],.;'\u2019&|~\\/")
    pieces += ["NOT", "OR", "AND", "NEAR", "de", "-de", '"la', "q;"]
    pieces += ["\u00ad", "\u200b", "\u0301"]  # soft hyphen, ZWSP, combining acute
    for _ in range(3000):
        q = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 14)))
        assert be.search(SearchQuery(q=q)).total >= 0, q


def test_all_words_by_default_any_word_on_request(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    # "Calculemus" is on 1r only, "grâce" on the Briefwechsel page only
    assert be.search(SearchQuery(q="Calculemus grace")).total == 0
    broad = be.search(SearchQuery(q="Calculemus grace", match="any"))
    assert broad.total == 2 and broad.match == "any"
    assert match_query(parse_query("a b"), any_word=True) == '("a" OR "b")'
    assert match_query(parse_query('"arte combinatoria" de'), any_word=True) == (
        '("arte combinatoria" OR "de")'
    )


def test_control_characters_are_no_query(store_path, tmp_path) -> None:
    be = _build(store_path, tmp_path)
    for q in ("Calculemus\x00", "\x00", 'Calc"\x00"ulemus', "\x07de\x1b"):
        assert be.search(SearchQuery(q=q)).total >= 0, repr(q)
    assert be.search(SearchQuery(q="Calculemus\x00")).total == 1


def test_paging_stops_at_the_reachable_depth() -> None:
    from leibniz.search.backend import MAX_REACHABLE, SearchResult, max_page

    q = SearchQuery(q="de", page=10_000, limit=20).normalized()
    assert q.page == max_page(20) == MAX_REACHABLE // 20 and q.offset < MAX_REACHABLE
    assert SearchQuery(q="de", page=3, limit=30).normalized().page == 3
    big = SearchResult("de", 97_633, 1, 20, 3, "fts5", [])
    assert big.to_dict()["reachable"] == MAX_REACHABLE and big.to_dict()["total"] == 97_633
