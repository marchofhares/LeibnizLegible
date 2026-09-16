"""Search folding + snippets (pure)."""

from __future__ import annotations

from leibniz.search.normalize import fold, fold_indexed, query_terms
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
