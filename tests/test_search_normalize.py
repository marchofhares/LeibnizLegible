"""Search folding + snippets (pure)."""

from __future__ import annotations

import random
import re

from leibniz.search.bench import DEFAULT_QUERIES
from leibniz.search.normalize import (
    MAX_QUERY_TERMS,
    QUOTE_CHARS,
    ParsedQuery,
    fold,
    fold_indexed,
    parse_query,
    query_terms,
)
from leibniz.search.snippet import make_snippet, term_spans, to_original_spans


def test_fold_early_modern_variants() -> None:
    assert fold("Vt ſit Jeſus, & Calcvlemvs!") == "ut sit iesus et calculemus"
    assert fold("grâce Ærarium") == "grace aerarium"


def test_fold_keeps_struck_text_and_offsets() -> None:
    folded, src = fold_indexed("xx Ab")
    assert folded == "xx ab"
    assert src == [0, 1, 2, 3, 4]


def test_query_terms_dedupes_and_caps() -> None:
    assert query_terms("  Vt, ut; UT ") == ["ut"]
    terms = query_terms(" ".join(f"w{i}" for i in range(30)))
    assert len(terms) == 12


def test_term_spans_prefix_rule() -> None:
    folded = "calculemus inquit ut sit"
    assert term_spans(folded, ["calcul"]) == [(0, 10)]
    assert term_spans(folded, ["ut"]) == [(18, 20)]  # exact only for short terms
    assert term_spans(folded, ["in"]) == []


def test_snippet_marks_original_text_and_escapes_html() -> None:
    text = "Calculemus, inquit <Leibnitius> & alii"
    snip = make_snippet(text, ["calcul", "et"])
    assert snip.startswith("<mark>Calculemus</mark>,")
    assert "&lt;Leibnitius&gt;" in snip
    assert "<mark>&amp;</mark>" in snip  # '&' folds to 'et'


def test_snippet_window_adds_ellipses() -> None:
    text = " ".join(["lorem"] * 80) + " calculemus " + " ".join(["ipsum"] * 80)
    snip = make_snippet(text, ["calculemus"], width=120)
    assert snip.startswith("…") and snip.endswith("…")
    assert "<mark>calculemus</mark>" in snip
    assert len(snip) < 200


def test_to_original_spans_clips() -> None:
    assert to_original_spans([(0, 3), (5, 2)], [0, 1, 2], 3) == [(0, 3)]


def _query_terms_before_operators(query: str) -> list[str]:
    """How queries were read before quotes and minus meant anything (kept as the reference)."""
    seen: set[str] = set()
    terms: list[str] = []
    for tok in fold(query).split():
        if tok and tok not in seen:
            seen.add(tok)
            terms.append(tok)
        if len(terms) >= 12:
            break
    return terms


def test_queries_without_operators_parse_exactly_as_before() -> None:
    rng = random.Random(1716)
    alphabet = list("abcdeiju vVJſ&,.;:!?()[]*^+<>/\\'’-–—éâßæœ0123456789\t")
    alphabet += ["q;", "\u0301", "\u00ad"]  # brevigraph, combining mark, soft hyphen
    queries = list(DEFAULT_QUERIES)
    while len(queries) < len(DEFAULT_QUERIES) + 2000:
        q = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        if not any(c in QUOTE_CHARS for c in q) and not re.search(r"(?:^|\s)-\S", q):
            queries.append(q)
    for q in queries:
        assert parse_query(q) == ParsedQuery(words=tuple(_query_terms_before_operators(q))), q


def test_parse_query_reads_quotes_and_minus() -> None:
    p = parse_query('Vt "harmonia praestabilita" -mundus -"de la" leibniz')
    assert p.words == ("ut", "leibniz")
    assert p.phrases == (("harmonia", "praestabilita"),)
    assert p.excluded == (("mundus",), ("de", "la"))
    # typographic quotes too, folded inside; an unclosed quote runs to the end
    for q in ("„Vt sit“", "“vt sit”", "«vt sit»", "»Vt sit«", '"vt sit'):
        assert parse_query(q).phrases == (("ut", "sit"),), q
    # a minus excludes only where it starts a word
    assert parse_query("Braunschweig-Lüneburg").words == ("braunschweig", "luneburg")
    assert parse_query("deus - mundus") == ParsedQuery(words=("deus", "mundus"))
    assert parse_query("-Braunschweig-Lüneburg x").excluded == (("braunschweig", "luneburg"),)
    # exclusions alone select nothing; empty quotes are nothing
    assert not parse_query("-mundus").searchable
    assert not parse_query('"" -"a"').searchable
    # repeats collapse; past the cap, exclusions and phrases keep their places
    assert parse_query('"a b" "A B" a a') == ParsedQuery(words=("a",), phrases=(("a", "b"),))
    many = parse_query(" ".join(f"w{i}" for i in range(20)) + ' -x "y z"')
    assert many.excluded == (("x",),) and many.phrases == (("y", "z"),)
    assert many.words == tuple(f"w{i}" for i in range(MAX_QUERY_TERMS - 2))
    assert query_terms('"a b" c -d') == ["c"]


def test_snippet_marks_a_phrase_as_one_run() -> None:
    text = "Calculemus, inquit Leibnitius: calculemus!"
    snip = make_snippet(text, [], phrases=[("calculemus", "inquit")])
    assert snip == "<mark>Calculemus, inquit</mark> Leibnitius: calculemus!"
    # a quoted word is exact: no prefix match
    assert "<mark>" not in make_snippet("calculemus", [], phrases=[("calcul",)])
    # a word inside a marked phrase is not marked twice
    assert make_snippet("ut sit veritas", ["sit"], phrases=[("ut", "sit")]) == (
        "<mark>ut sit</mark> veritas"
    )
    assert term_spans("a b a b", [], phrases=[("a", "b"), ("b", "a")]) == [(0, 7)]
