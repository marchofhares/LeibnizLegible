"""Tests for the retro-aligner (boundary projection), offline."""

from __future__ import annotations

from leibniz.align.align import HtrLine, align_piece


def _htr(*texts: str) -> list[HtrLine]:
    return [HtrLine(ref=f"L{i:02d}", text=t) for i, t in enumerate(texts)]


def test_clean_projection_splits_edition_by_line() -> None:
    htr = _htr(
        "Mechanici ſcriptores plerique olim non niſi",
        "de quinque Machinis Fundamentalibus ut",
    )
    edition = "Mechanici scriptores plerique olim, non nisi de quinque Machinis Fundamentalibus, ut"
    res = align_piece(htr, edition, threshold=0.5)
    assert res.n_aligned == 2
    assert "Mechanici" in res.lines[0].edition_text
    assert "Fundamentalibus" in res.lines[1].edition_text
    # no original edition character is lost between the two lines.
    joined = res.lines[0].edition_text + res.lines[1].edition_text
    assert joined.replace(" ", "") == edition.replace(" ", "")


def test_hyphenation_rejoins_split_word() -> None:
    htr = _htr("de quinque Machinis industri-", "ae atque experientiae artificum")
    edition = "de quinque Machinis industriae atque experientiae artificum"
    res = align_piece(htr, edition, threshold=0.5)
    # the split word 'industri-/ae' is cut at the line break: line0 ends 'industri'.
    assert res.lines[0].edition_text.rstrip().endswith("industri")
    assert res.lines[1].edition_text.lstrip().startswith("ae")


def test_confidence_never_exceeds_one() -> None:
    htr = _htr("perfect match line one", "perfect match line two")
    edition = "perfect match line one perfect match line two"
    res = align_piece(htr, edition, threshold=0.5)
    assert all(0.0 <= ln.align_conf <= 1.0 for ln in res.lines)


def test_omitted_line_is_not_minted() -> None:
    # the middle line has no counterpart in the edition → it must not be aligned,
    # and must not steal neighbour text (precision protection).
    htr = _htr("prima linea textus", "LINEA DELETA IGNORANDA", "tertia linea textus")
    edition = "prima linea textus tertia linea textus"
    res = align_piece(htr, edition, threshold=0.6)
    assert res.lines[0].aligned and res.lines[2].aligned
    assert not res.lines[1].aligned
    assert res.lines[1].align_conf < 0.6


def test_edition_overhang_is_free() -> None:
    htr = _htr("cognitio nihil aliud est")
    edition = "PROLOGUS OMITTENDUS cognitio nihil aliud est quam SEQUENS TEXTUS"
    res = align_piece(htr, edition, threshold=0.5, free_edition_ends=True)
    assert res.n_aligned == 1
    assert "cognitio nihil aliud est" in res.lines[0].edition_text


def test_empty_inputs() -> None:
    res = align_piece(_htr("some text"), "", threshold=0.5)
    assert res.n_aligned == 0
    res2 = align_piece([], "some edition text", threshold=0.5)
    assert res2.n_lines == 0


def test_yield_rate() -> None:
    htr = _htr("alpha beta gamma", "delta epsilon zeta")
    edition = "alpha beta gamma delta epsilon zeta"
    res = align_piece(htr, edition, threshold=0.5)
    assert res.yield_rate == 1.0
