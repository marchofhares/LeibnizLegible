"""Tests for the stopword language identifier (offline, pure)."""

from __future__ import annotations

import pytest

from leibniz.enrich import langid as L

GERMAN = (
    "Hochgeehrter Herr, ich habe dero Schreiben wol erhalten vnd bedancke mich daß Sie mir die "
    "Nachricht so bald haben zukommen lassen; es ist aber nicht zu zweiffeln daß der Herr von "
    "Boineburg alß ein verständiger Mann die Sache wol vberlegen wird, wan er nur die Zeit darzu "
    "hat vnd nicht durch andere Geschäffte verhindert seyn solte."
)
LATIN = (
    "Vir amplissime, literas tuas accepi quibus de rebus mathematicis ad me scripsisti; ego vero "
    "puto non esse dubitandum quod haec omnia ex principiis nostris deduci possint, ut etiam tibi "
    "ostendam cum primum licebit."
)
FRENCH = (
    "Monsieur, j'ay receu la lettre que vous m'avez fait l'honneur de m'escrire, et je vous suis "
    "tres obligé de la peine que vous avez prise; il est vray que cette affaire ne peut pas estre "
    "achevée si tost, mais nous ferons ce qui sera possible."
)


def test_lists_are_disjoint() -> None:
    assert not (L.LATIN & L.FRENCH)
    assert not (L.LATIN & L.GERMAN)
    assert not (L.FRENCH & L.GERMAN)
    # the shared small words are in none of them
    for w in ("et", "est", "de", "in", "si", "non", "qui", "des", "die", "nos", "vos"):
        assert w not in L.LATIN | L.FRENCH | L.GERMAN


@pytest.mark.parametrize(
    ("text", "lang"),
    [(GERMAN, "de"), (LATIN, "la"), (FRENCH, "fr")],
)
def test_classifies_the_three_languages(text: str, lang: str) -> None:
    r = L.classify(text)
    assert r.lang == lang
    assert r.top == lang
    assert r.score >= L.DOMINANT
    assert r.hits[lang] >= L.MIN_HITS
    assert r.coverage > 0.3


def test_seventeenth_century_spellings_count_as_german() -> None:
    for w in ("vnd", "vndt", "daß", "seyn", "sey", "alß", "wan", "umb", "auff"):
        assert w in L.GERMAN


def test_french_elision_clitics_count_as_french() -> None:
    toks = L.tokens("j'ay qu'il l'on d'un n'est")
    assert toks == ["j'", "ay", "qu'", "il", "l'", "on", "d'", "un", "n'", "est"]
    hits, n = L.count_hits(toks)
    assert n == 10
    assert hits["fr"] >= 5 + 3  # five clitics plus ay, il, on, un


def test_short_text_is_unknown() -> None:
    r = L.classify("vnd daß der Herr")
    assert r.lang == "unknown"
    assert r.n_tokens < L.MIN_TOKENS
    assert r.top == "de"  # the evidence is still reported


def test_text_without_stopwords_is_unknown() -> None:
    r = L.classify("Hannover Leibniz Boineburg Mainz Paris London Amsterdam Berlin Wien")
    assert r.lang == "unknown"
    assert r.score == 0.0 and r.top is None


def test_balanced_mix_is_mixed() -> None:
    r = L.classify(GERMAN + " " + LATIN + " " + LATIN)
    assert r.lang == "mixed"
    assert {r.top, r.second} == {"de", "la"}
    assert r.score < L.DOMINANT


def test_dominant_language_wins_a_quotation() -> None:
    # a German letter quoting a Latin sentence stays German
    r = L.classify(GERMAN + " " + GERMAN + " " + LATIN)
    assert r.lang == "de"


def test_long_s_and_case_are_folded() -> None:
    assert L.tokens("Daß ſie ſeyn") == ["daß", "sie", "seyn"]
