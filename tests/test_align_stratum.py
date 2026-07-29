"""Tests for the stratum heuristic (offline)."""

from __future__ import annotations

from leibniz.align.stratum import classify_page, classify_piece, stratum_from_textart
from leibniz.db import PageStats


def _ps(**kw) -> PageStats:
    base = dict(page_id="p", n_lines=15, line_height_cv=0.1, n_overlaps=0, n_short_lines=0)
    base.update(kw)
    return PageStats(**base)


def test_textart_mapping() -> None:
    assert stratum_from_textart("Reinschrift") == "fair_copy"
    assert stratum_from_textart("Konzept mit Korrekturen") == "heavy_revision"
    assert stratum_from_textart("Abschrift") == "fair_copy"
    assert stratum_from_textart("Auszug") == "scrap"
    assert stratum_from_textart("Brief") is None
    assert stratum_from_textart(None) is None


def test_classify_page_strata() -> None:
    assert classify_page(_ps(n_lines=0)) == "unknown"
    assert classify_page(_ps(n_lines=2)) == "scrap"
    assert classify_page(_ps(n_lines=15, line_height_cv=0.1, n_overlaps=0, n_short_lines=0)) == (
        "fair_copy"
    )
    # two heavy signals: high CV + many short lines
    assert classify_page(_ps(n_lines=20, line_height_cv=0.5, n_short_lines=8)) == "heavy_revision"
    # many overlaps alone (>= half the lines) → heavy
    assert classify_page(_ps(n_lines=10, n_overlaps=6)) == "heavy_revision"
    # a middling page: moderate CV, one signal → light revision
    assert classify_page(_ps(n_lines=15, line_height_cv=0.35, n_short_lines=1)) == "light_revision"


def test_classify_piece_agreement_high_confidence() -> None:
    r = classify_piece([_ps()], textart="Reinschrift")
    assert r.stratum == "fair_copy"
    assert r.agree and r.confidence >= 0.9


def test_classify_piece_seg_only() -> None:
    r = classify_piece([_ps(n_lines=20, line_height_cv=0.5, n_short_lines=8)], textart=None)
    assert r.stratum == "heavy_revision"
    assert r.katalog_stratum is None


def test_classify_piece_disagreement_blends_one_step() -> None:
    # katalog says draft, layout says clean → one step toward severe = light_revision
    r = classify_piece([_ps()], textart="Konzept")
    assert r.stratum == "light_revision"
    assert not r.agree and r.confidence == 0.5


def test_classify_piece_aggregates_pages() -> None:
    pages = [_ps(n_lines=10, line_height_cv=0.5, n_short_lines=5) for _ in range(3)]
    r = classify_piece(pages, textart=None)
    assert r.n_pages == 3 and r.n_lines == 30
    assert r.stratum == "heavy_revision"


def test_classify_piece_empty_is_unknown() -> None:
    r = classify_piece([], textart=None)
    assert r.stratum == "unknown" and r.confidence == 0.0
