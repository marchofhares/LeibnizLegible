"""German census of the edition pieces (Phase K1, Task 2).

About 15 % of the Nachlass is German, written in Kurrent, and the HTR model the
corpus run used reads Kurrent as noise. The C2 factory minted its 297k lines
from the §70-expired volumes against that model's machine text, so the
hypothesis is that the German pieces were *declined* rather than minted — the
German ground truth is still unmade, in pieces the factory has already
localized. This census tests that and hands K2 its input.

For every record of the C2 edition cache the reading text is classified by
:mod:`leibniz.enrich.langid` (``la`` | ``fr`` | ``de`` | ``mixed`` | ``unknown``
with a dominance score). The records are joined to the factory's pieces
(:func:`leibniz.align.volumes.enumerate_pieces`), each piece to its canvases
(the C2 resolver, one folio index per work), its recognised v1 lines (the rows
the factory gathers: ``lines.text`` not null) and its minted lines (``gt_lines``
whose ``source`` names ``katalog <record_id>``). The stratum is the factory's
own — :func:`leibniz.align.stratum.classify_piece` over the pages'
``page_stats`` plus the Textart; ``page_stats.stratum_heuristic`` is NULL under
C1 and is never read. Whose hand the piece is in comes from the Textart's
``eigh.`` (*eigenhändig*): ``own`` when the mark qualifies the piece itself
(``Abf., eigh.``, ``Konz.; eigh.``), ``partial`` when it qualifies only an
address, a correction or a postscript (``Abf.; eigh. Aufschr.``), ``other``
when there is no mark, ``none`` when the record has no Textart. Leibniz's own
hand is ``own`` on a record that names no sender or Leibniz as the sender (the
C2b rule).

Outputs: ``reports/kurrent/census.md`` (prose templated from the numbers),
``census-summary.json``, ``census-by-volume.csv``, the committed
``german_pieces_index.csv`` (no page lists) and, for K2,
``data/kurrent/german_pieces.jsonl`` with the page ids. The store is opened
``mode=ro`` + ``query_only``; nothing is written to it.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz import db
from leibniz.align.audit import split_ref
from leibniz.align.audit_reach import open_readonly, parse_source
from leibniz.align.factory import page_stats_for_pages
from leibniz.align.normalize import normalize
from leibniz.align.resolve import index_pages, select_folios
from leibniz.align.stratum import classify_piece
from leibniz.align.volumes import PieceRef, enumerate_pieces
from leibniz.catalog.hands import HANDS, hand_from_textart, is_leibniz_hand
from leibniz.enrich.langid import LangResult, classify, count_hits, tokens

LANGS: tuple[str, ...] = ("la", "fr", "de", "mixed", "unknown")
STRATA: tuple[str, ...] = ("fair_copy", "light_revision", "heavy_revision", "scrap", "unknown")
LATIN_FRENCH: tuple[str, ...] = ("la", "fr")


@dataclass(slots=True)
class MintTally:
    """The factory's minted lines of one record: how many, how confident, what language.

    The language is read off the *minted text* (the edition's slice, so correct
    text) with the stopword lists alone, no length rule: ``de`` when the text
    carries German stopwords and no Latin or French ones, ``lafr`` the reverse,
    ``both`` when it carries both, ``neither`` when it carries none (short lines,
    names, dates, numbers). On a German piece, a minted line reading ``lafr`` is
    an address, a title or a quotation in Latin script — what a Latin-trained
    reader can read; ``de`` is a Kurrent line the aligner accepted.
    """

    n: int = 0
    conf_sum: float = 0.0
    de: int = 0
    lafr: int = 0
    both: int = 0
    neither: int = 0
    # folded lengths, as the aligner's confidence counts them: the machine text
    # the line was aligned on, and the minted slice
    htr_chars: int = 0
    text_chars: int = 0

    def add(self, conf: float | None, text: str | None, htr_text: str | None = None) -> None:
        self.n += 1
        self.conf_sum += conf or 0.0
        self.htr_chars += len(normalize(htr_text or ""))
        self.text_chars += len(normalize(text or ""))
        hits, _n = count_hits(tokens(text or ""))
        has_de = hits["de"] > 0
        has_lafr = hits["la"] + hits["fr"] > 0
        if has_de and has_lafr:
            self.both += 1
        elif has_de:
            self.de += 1
        elif has_lafr:
            self.lafr += 1
        else:
            self.neither += 1

    @property
    def conf_mean(self) -> float | None:
        return self.conf_sum / self.n if self.n else None

    @property
    def htr_chars_mean(self) -> float | None:
        return self.htr_chars / self.n if self.n else None

    @property
    def text_chars_mean(self) -> float | None:
        return self.text_chars / self.n if self.n else None


def _current_text(conn: sqlite3.Connection, ref: str) -> str | None:
    """The line's current machine text (the highest run), or ``None``."""
    try:
        page_id_, seq = split_ref(ref)
    except (ValueError, IndexError):
        return None
    row = conn.execute(
        "SELECT text FROM lines WHERE page_id = ? AND line_seq = ? ORDER BY run_id DESC LIMIT 1",
        (page_id_, seq),
    ).fetchone()
    return None if row is None else row[0]


def minted_by_record(conn: sqlite3.Connection) -> dict[str, MintTally]:
    """Minted lines per catalogue record, from the factory's ``gt_lines.source``.

    Each minted line also fetches the machine text it was aligned on, so the
    tally can say how long the lines were that the aligner accepted.
    """
    out: dict[str, MintTally] = defaultdict(MintTally)
    rows = conn.execute("SELECT source, align_conf, text, line_image_ref FROM gt_lines").fetchall()
    for source, conf, text, ref in rows:
        _vol, rec = parse_source(source or "")
        if rec is not None:
            out[rec].add(conf, text, _current_text(conn, ref or ""))
    return dict(out)


def count_recognised_lines(conn: sqlite3.Connection, page_ids: list[str]) -> int:
    """The lines the factory would gather on these pages: a text was recognised."""
    n = 0
    for pid in page_ids:
        row = conn.execute(
            "SELECT COUNT(*) FROM lines WHERE page_id = ? AND text IS NOT NULL", (pid,)
        ).fetchone()
        n += int(row[0])
    return n


@dataclass(slots=True)
class PieceCensus:
    """One piece of the edition cache, placed and classified."""

    record_id: str
    work_id: str | None
    aa_label: str
    volume_label: str
    series: int
    piece: str
    signature: str | None
    folio_range: list[int] | None
    textart: str | None
    hand: str
    leibniz_hand: bool
    absender: str | None
    adressat: str | None
    datum: str | None
    titel: str | None
    localizable: bool
    page_ids: list[str]
    n_pages: int
    n_lines: int
    n_minted: int
    stratum: str
    language: str
    top: str | None
    second: str | None
    score: float
    coverage: float
    n_tokens: int
    hits: dict[str, int]
    n_chars: int
    minted_conf_mean: float | None
    minted_de: int
    minted_lafr: int
    minted_both: int
    minted_neither: int
    minted_htr_chars: int
    minted_text_chars: int

    @property
    def german(self) -> bool:
        """What K2 takes: German, or mixed with German leading."""
        return self.language == "de" or (self.language == "mixed" and self.top == "de")

    @property
    def yield_rate(self) -> float | None:
        return self.n_minted / self.n_lines if self.n_lines else None


@dataclass(slots=True)
class CensusResult:
    """Everything the census measured."""

    today: str
    n_cache_records: int
    cache_languages: dict[str, int]  # every cache record, by language
    n_pieces_enumerated: int
    n_pieces_without_text: int
    pieces: list[PieceCensus]
    generated: str = field(default_factory=lambda: date.today().isoformat())


def census(
    conn: sqlite3.Connection,
    cache: Mapping[str, str],
    *,
    today: date,
    progress: Callable[[int, int], None] | None = None,
) -> CensusResult:
    """Classify the cache, join it to the pieces, place and count every piece."""
    langs: dict[str, LangResult] = {rid: classify(text) for rid, text in cache.items()}
    cache_langs = Counter(r.lang for r in langs.values())
    for lang in LANGS:
        cache_langs.setdefault(lang, 0)

    pieces, _stats = enumerate_pieces(conn, today=today)
    minted = minted_by_record(conn)
    indexes: dict[str, dict[int, list[db.Page]]] = {}
    out: list[PieceCensus] = []
    without_text = 0
    total = len(pieces)
    for k, piece in enumerate(pieces, start=1):
        if progress is not None and (k % 500 == 0 or k == total):
            progress(k, total)
        text = cache.get(piece.record_id)
        if text is None:
            without_text += 1
            continue
        out.append(_place(conn, piece, text, langs[piece.record_id], minted, indexes))
    return CensusResult(
        today=today.isoformat(),
        n_cache_records=len(cache),
        cache_languages=dict(cache_langs),
        n_pieces_enumerated=total,
        n_pieces_without_text=without_text,
        pieces=out,
    )


def _place(
    conn: sqlite3.Connection,
    piece: PieceRef,
    text: str,
    lang: LangResult,
    minted: Mapping[str, MintTally],
    indexes: dict[str, dict[int, list[db.Page]]],
) -> PieceCensus:
    pages: list[db.Page] = []
    if piece.localizable:
        assert piece.work_id is not None and piece.folio_range is not None
        index = indexes.get(piece.work_id)
        if index is None:
            index = index_pages(db.get_pages(conn, piece.work_id))
            indexes[piece.work_id] = index
        pages = select_folios(
            index,
            piece.work_id,
            *piece.folio_range,
            side_lo=piece.folio_sides[0],
            side_hi=piece.folio_sides[1],
        ).pages
    page_ids = [p.id for p in pages]
    n_lines = count_recognised_lines(conn, page_ids) if page_ids else 0
    stratum = (
        classify_piece(page_stats_for_pages(conn, pages), textart=piece.textart).stratum
        if pages
        else "unknown"
    )
    rec = db.get_katalog_record(conn, piece.record_id)
    meta = rec.metadata if rec is not None else {}
    absender = _str_or_none(meta.get("absender"))
    hand = hand_from_textart(piece.textart)
    mint = minted.get(piece.record_id, MintTally())
    return PieceCensus(
        record_id=piece.record_id,
        work_id=piece.work_id,
        aa_label=piece.aa_label,
        volume_label=piece.volume_label,
        series=piece.series,
        piece=piece.piece,
        signature=piece.signature,
        folio_range=list(piece.folio_range) if piece.folio_range else None,
        textart=piece.textart,
        hand=hand,
        leibniz_hand=is_leibniz_hand(hand, absender),
        absender=absender,
        adressat=_str_or_none(meta.get("adressat")),
        datum=_str_or_none(meta.get("datum")),
        titel=_str_or_none(meta.get("titel")),
        localizable=piece.localizable,
        page_ids=page_ids,
        n_pages=len(page_ids),
        n_lines=n_lines,
        n_minted=mint.n,
        stratum=stratum,
        language=lang.lang,
        top=lang.top,
        second=lang.second,
        score=round(lang.score, 4),
        coverage=round(lang.coverage, 4),
        n_tokens=lang.n_tokens,
        hits=dict(lang.hits),
        n_chars=len(text),
        minted_conf_mean=None if mint.conf_mean is None else round(mint.conf_mean, 4),
        minted_de=mint.de,
        minted_lafr=mint.lafr,
        minted_both=mint.both,
        minted_neither=mint.neither,
        minted_htr_chars=mint.htr_chars,
        minted_text_chars=mint.text_chars,
    )


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Tally:
    """Pieces, pages, lines and minted lines for one group of pieces."""

    pieces: int = 0
    localizable: int = 0
    with_lines: int = 0
    pages: int = 0
    lines: int = 0
    minted: int = 0
    minted_conf_sum: float = 0.0
    minted_de: int = 0
    minted_lafr: int = 0
    minted_both: int = 0
    minted_neither: int = 0
    minted_htr_chars: int = 0
    minted_text_chars: int = 0

    def add(self, pc: PieceCensus) -> None:
        self.pieces += 1
        self.localizable += int(pc.localizable)
        self.with_lines += int(pc.n_lines > 0)
        self.pages += pc.n_pages
        self.lines += pc.n_lines
        self.minted += pc.n_minted
        self.minted_conf_sum += (pc.minted_conf_mean or 0.0) * pc.n_minted
        self.minted_de += pc.minted_de
        self.minted_lafr += pc.minted_lafr
        self.minted_both += pc.minted_both
        self.minted_neither += pc.minted_neither
        self.minted_htr_chars += pc.minted_htr_chars
        self.minted_text_chars += pc.minted_text_chars

    @property
    def yield_rate(self) -> float | None:
        return self.minted / self.lines if self.lines else None

    @property
    def minted_conf_mean(self) -> float | None:
        return self.minted_conf_sum / self.minted if self.minted else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d.pop("minted_conf_sum")
        d["yield"] = self.yield_rate
        d["minted_conf_mean"] = self.minted_conf_mean
        d["minted_htr_chars_mean"] = self.minted_htr_chars / self.minted if self.minted else None
        d["minted_text_chars_mean"] = self.minted_text_chars / self.minted if self.minted else None
        for key in ("de", "lafr", "both", "neither"):
            d[f"minted_{key}_share"] = (
                getattr(self, f"minted_{key}") / self.minted if self.minted else None
            )
        return d


def tally_by(pieces: list[PieceCensus], key: Callable[[PieceCensus], str]) -> dict[str, Tally]:
    out: dict[str, Tally] = defaultdict(Tally)
    for pc in pieces:
        out[key(pc)].add(pc)
    return dict(out)


def _lang_group(pc: PieceCensus) -> str:
    """``de`` (German, or mixed with German leading) | ``la_fr`` | ``other``."""
    if pc.german:
        return "de"
    if pc.language in LATIN_FRENCH:
        return "la_fr"
    return "other"


def _normalise_textart(textart: str | None) -> str:
    if not textart or not textart.strip():
        return "(none)"
    return " ".join(textart.replace(";", ",").split())


def summary(res: CensusResult) -> dict:
    """The JSON summary: overall, by volume, by Textart, by hand, by stratum, for K2."""
    pcs = res.pieces
    by_lang = tally_by(pcs, lambda pc: pc.language)
    by_group = tally_by(pcs, _lang_group)
    german = [pc for pc in pcs if pc.german]
    by_volume: dict[str, dict] = {}
    for vol in sorted({pc.volume_label for pc in pcs}, key=_volume_key):
        vp = [pc for pc in pcs if pc.volume_label == vol]
        by_volume[vol] = {
            "pieces": len(vp),
            "languages": {lang: t.pieces for lang, t in tally_by(vp, lambda p: p.language).items()},
            "groups": {g: t.as_dict() for g, t in tally_by(vp, _lang_group).items()},
            "german_leibniz_hand": sum(1 for pc in vp if pc.german and pc.leibniz_hand),
        }
    textart_counter = Counter(_normalise_textart(pc.textart) for pc in pcs)
    by_textart = {
        ta: {
            lang: t.pieces
            for lang, t in tally_by(
                [pc for pc in pcs if _normalise_textart(pc.textart) == ta], lambda p: p.language
            ).items()
        }
        for ta, _n in textart_counter.most_common(20)
    }
    by_hand = {
        hand: {
            lang: t.pieces
            for lang, t in tally_by(
                [pc for pc in pcs if pc.hand == hand], lambda p: p.language
            ).items()
        }
        for hand in HANDS
    }
    leibniz = {
        lang: sum(1 for pc in pcs if pc.leibniz_hand and pc.language == lang) for lang in LANGS
    }
    german_by_stratum = {s: t.as_dict() for s, t in tally_by(german, lambda p: p.stratum).items()}
    by_stratum_group = {
        s: {
            g: t.as_dict()
            for g, t in tally_by([pc for pc in pcs if pc.stratum == s], _lang_group).items()
        }
        for s in STRATA
    }
    german_by_hand = {h: t.as_dict() for h, t in tally_by(german, lambda p: p.hand).items()}
    scores = sorted(pc.score for pc in pcs if pc.language == "de")
    stratum_signal = sum(
        1 for pc in pcs if classify_piece([], textart=pc.textart).katalog_stratum is not None
    )
    return {
        "generated": res.generated,
        "today": res.today,
        "cache_records": res.n_cache_records,
        "cache_languages": res.cache_languages,
        "pieces_enumerated": res.n_pieces_enumerated,
        "pieces_without_text": res.n_pieces_without_text,
        "pieces_with_text": len(pcs),
        "by_language": {lang: t.as_dict() for lang, t in by_lang.items()},
        "by_group": {g: t.as_dict() for g, t in by_group.items()},
        "german_pieces": len(german),
        "german_localizable": sum(1 for pc in german if pc.localizable),
        "german_with_lines": sum(1 for pc in german if pc.n_lines),
        "german_pages": sum(pc.n_pages for pc in german),
        "german_lines": sum(pc.n_lines for pc in german),
        "german_minted": sum(pc.n_minted for pc in german),
        "german_leibniz_hand": sum(1 for pc in german if pc.leibniz_hand),
        "german_leibniz_hand_lines": sum(pc.n_lines for pc in german if pc.leibniz_hand),
        "german_score_quartiles": statistics.quantiles(scores, n=4) if len(scores) >= 4 else scores,
        "german_by_stratum": german_by_stratum,
        "by_stratum_group": by_stratum_group,
        "german_by_hand": german_by_hand,
        "by_volume": by_volume,
        "by_textart": by_textart,
        "by_hand": by_hand,
        "leibniz_hand_by_language": leibniz,
        "pieces_with_katalog_stratum_signal": stratum_signal,
    }


def _volume_key(label: str) -> tuple[int, int, str]:
    roman = {"I": 1, "II": 2, "III": 3, "IV": 4, "VI": 6, "VII": 7}
    series, _, vol = label.partition(",")
    try:
        return (roman.get(series, 99), int(vol), "")
    except ValueError:
        return (roman.get(series, 99), 999, vol)


# --------------------------------------------------------------------------- #
# Rendering and files
# --------------------------------------------------------------------------- #


def _pct(x: float | None, digits: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{digits}f} %"


def _n(x: int) -> str:
    return f"{x:,}"


def _share(part: int, whole: int) -> str:
    return f"{_n(part)} ({_pct(part / whole)})" if whole else f"{_n(part)}"


def _row(cells: list[object]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _sep(n: int, *, first_left: int = 1) -> str:
    return "|" + "---|" * first_left + "---:|" * (n - first_left)


def _lang_cells(langs: Mapping[str, int]) -> list[object]:
    return [_n(langs.get(lang, 0)) for lang in LANGS]


def _conf(x: object) -> str:
    return "—" if x is None else f"{float(x):.3f}"  # type: ignore[arg-type]


def _mint_cells(t: Mapping[str, object]) -> list[object]:
    cells: list[object] = [_n(int(t["minted"])), _conf(t["minted_conf_mean"])]  # type: ignore[call-overload]
    for key in ("de", "lafr", "both", "neither"):
        share = t[f"minted_{key}_share"]
        cells.append(f"{_n(int(t[f'minted_{key}']))} ({_pct(share)})")  # type: ignore[call-overload,arg-type]
    cells.append(_chars(t["minted_htr_chars_mean"]))
    cells.append(_chars(t["minted_text_chars_mean"]))
    return cells


def _chars(x: object) -> str:
    return "—" if x is None else f"{float(x):.1f}"  # type: ignore[arg-type]


def _tally_cells(t: Mapping[str, object]) -> list[object]:
    return [
        _n(int(t["pieces"])),  # type: ignore[call-overload]
        _n(int(t["localizable"])),  # type: ignore[call-overload]
        _n(int(t["with_lines"])),  # type: ignore[call-overload]
        _n(int(t["pages"])),  # type: ignore[call-overload]
        _n(int(t["lines"])),  # type: ignore[call-overload]
        _n(int(t["minted"])),  # type: ignore[call-overload]
        _pct(t["yield"]),  # type: ignore[arg-type]
    ]


def render(
    res: CensusResult,
    summ: dict,
    *,
    snippets: int = 4,
    cache: Mapping[str, str] | None = None,
) -> str:
    """The Markdown report; every number from ``summ`` and ``res``."""
    pcs = res.pieces
    g = summ["by_group"]
    empty = Tally().as_dict()
    de, lafr = g.get("de", empty), g.get("la_fr", empty)
    bl = summ["by_language"]
    n_text = max(1, summ["pieces_with_text"])
    out: list[str] = []
    out.append("# German census of the edition pieces")
    out.append("")
    out.append(
        f"{_n(summ['cache_records'])} records of the C2 edition cache, each classified by the "
        "stopword identifier (`leibniz.enrich.langid`: Latin, French, German, mixed, unknown, with "
        "the leading language's share of the stopword hits as its score). "
        f"{_n(summ['pieces_enumerated'])} §70 pieces enumerated on {res.today}; "
        f"{_n(summ['pieces_with_text'])} of them have a text in the cache and are the pieces "
        f"below ({_n(summ['pieces_without_text'])} have none). A piece is placed on its canvases "
        "by the C2 resolver; its lines are the recognised v1 lines on those pages, its minted "
        "lines the `gt_lines` the factory wrote for its record, its stratum the factory's "
        "(layout statistics plus Textart); yield is minted ÷ lines. Read-only over the store."
    )
    out.append("")
    out.append("## The hypothesis")
    out.append("")
    out.append(
        f"German pieces (German, or mixed with German leading): **{_n(de['pieces'])}** of "
        f"{_n(summ['pieces_with_text'])} ({_pct(de['pieces'] / n_text)}), "
        f"{_n(de['localizable'])} localizable, {_n(de['with_lines'])} with recognised lines on "
        f"**{_n(de['pages'])} pages, {_n(de['lines'])} lines**; the factory minted "
        f"**{_n(de['minted'])}** lines on them (yield {_pct(de['yield'])}). Latin and French "
        f"pieces: {_n(lafr['pieces'])}, {_n(lafr['with_lines'])} with lines on "
        f"{_n(lafr['pages'])} pages, {_n(lafr['lines'])} lines, **{_n(lafr['minted'])}** minted "
        f"(yield {_pct(lafr['yield'])})."
    )
    out.append("")
    head = ["group", "pieces", "localizable", "with lines", "pages", "lines", "minted", "yield"]
    out.append(_row(head))
    out.append(_sep(len(head)))
    labels = (
        ("de", "German (de, or mixed with de leading)"),
        ("la_fr", "Latin and French"),
        ("other", "other (mixed otherwise, unknown)"),
    )
    for key, label in labels:
        t = g.get(key)
        if t is not None:
            out.append(_row([label, *_tally_cells(t)]))
    out.append("")
    out.append(
        "What the factory minted on them, without ground truth: the aligner's confidence of the "
        "minted lines, and the language the minted text's stopwords give it — `de` German "
        "stopwords only, `la/fr` Latin or French only, `both`, `neither` (short lines, names, "
        "dates, figures). A minted line on a German piece whose text reads `la/fr` is an "
        "address, a title, a quotation: Latin script, what the Latin-trained model can read. "
        "The last two columns are the mean folded length of the machine text the line was "
        "aligned on and of the minted slice: a high confidence on a short machine text is the "
        "aligner's freedom, not the reader's skill."
    )
    out.append("")
    head = [
        "group",
        "minted",
        "mean confidence",
        "de",
        "la/fr",
        "both",
        "neither",
        "machine chars",
        "minted chars",
    ]
    out.append(_row(head))
    out.append(_sep(len(head)))
    for key, label in labels:
        t = g.get(key)
        if t is not None:
            out.append(_row([label, *_mint_cells(t)]))
    out.append("")
    out.append(
        "Stratum by stratum (the factory's threshold rises from fair copy to scrap, and the "
        "German pieces are mostly drafts):"
    )
    out.append("")
    head = [
        "stratum",
        "de pieces",
        "de lines",
        "de minted",
        "de yield",
        "de mean conf",
        "la+fr pieces",
        "la+fr lines",
        "la+fr minted",
        "la+fr yield",
        "la+fr mean conf",
    ]
    out.append(_row(head))
    out.append(_sep(len(head)))
    for s in STRATA:
        groups = summ["by_stratum_group"].get(s, {})
        gde = groups.get("de", empty)
        glf = groups.get("la_fr", empty)
        if not gde["pieces"] and not glf["pieces"]:
            continue
        out.append(
            _row(
                [
                    s,
                    _n(gde["pieces"]),
                    _n(gde["lines"]),
                    _n(gde["minted"]),
                    _pct(gde["yield"]),
                    _conf(gde["minted_conf_mean"]),
                    _n(glf["pieces"]),
                    _n(glf["lines"]),
                    _n(glf["minted"]),
                    _pct(glf["yield"]),
                    _conf(glf["minted_conf_mean"]),
                ]
            )
        )
    out.append("")
    out.append("## Pieces by language")
    out.append("")
    head = ["language", "cache records", *head[1:]]
    out.append(_row(head))
    out.append(_sep(len(head)))
    for lang in LANGS:
        t = bl.get(lang, empty)
        out.append(_row([lang, _n(summ["cache_languages"].get(lang, 0)), *_tally_cells(t)]))
    q = summ["german_score_quartiles"]
    if len(q) == 3:
        out.append("")
        out.append(
            f"Dominance scores of the pieces classified `de`: quartiles {q[0]:.2f} / {q[1]:.2f} / "
            f"{q[2]:.2f} (the cut is 0.65; a `mixed` piece has a runner-up at ≥ 0.25)."
        )
    out.append("")
    out.append("## By volume")
    out.append("")
    head = [
        "volume",
        "pieces",
        *LANGS,
        "de pages",
        "de lines",
        "de minted",
        "de yield",
        "la+fr lines",
        "la+fr minted",
        "la+fr yield",
        "de in Leibniz's hand",
    ]
    out.append(_row(head))
    out.append(_sep(len(head)))
    for vol, row in summ["by_volume"].items():
        gde = row["groups"].get("de", empty)
        glf = row["groups"].get("la_fr", empty)
        out.append(
            _row(
                [
                    vol,
                    _n(row["pieces"]),
                    *_lang_cells(row["languages"]),
                    _n(gde["pages"]),
                    _n(gde["lines"]),
                    _n(gde["minted"]),
                    _pct(gde["yield"]),
                    _n(glf["lines"]),
                    _n(glf["minted"]),
                    _pct(glf["yield"]),
                    _n(row["german_leibniz_hand"]),
                ]
            )
        )
    out.append("")
    out.append("## German pieces by stratum and by hand")
    out.append("")
    head = ["stratum", "pieces", "localizable", "with lines", "pages", "lines", "minted", "yield"]
    out.append(_row(head))
    out.append(_sep(len(head)))
    for s in STRATA:
        t = summ["german_by_stratum"].get(s)
        if t is not None:
            out.append(_row([s, *_tally_cells(t)]))
    out.append("")
    head[0] = "hand (Textart)"
    out.append(_row(head))
    out.append(_sep(len(head)))
    for h in HANDS:
        t = summ["german_by_hand"].get(h)
        if t is not None:
            out.append(_row([h, *_tally_cells(t)]))
    out.append("")
    out.append(
        f"German pieces in Leibniz's own hand (`eigh.` on the piece, no sender or Leibniz as "
        f"sender): **{_n(summ['german_leibniz_hand'])}** with "
        f"{_n(summ['german_leibniz_hand_lines'])} recognised lines. *own*: the Textart's `eigh.` "
        "qualifies the piece; *partial*: only an address, correction or postscript; *other*: no "
        "mark; *none*: no Textart."
    )
    out.append("")
    out.append("## Language by Textart and by hand (all pieces)")
    out.append("")
    head = ["Textart", "pieces", *LANGS]
    out.append(_row(head))
    out.append(_sep(len(head)))
    for ta, langs in summ["by_textart"].items():
        out.append(_row([ta, _n(sum(langs.values())), *_lang_cells(langs)]))
    out.append("")
    head[0] = "hand"
    out.append(_row(head))
    out.append(_sep(len(head)))
    for h in HANDS:
        langs = summ["by_hand"].get(h, {})
        out.append(_row([h, _n(sum(langs.values())), *_lang_cells(langs)]))
    lb = summ["leibniz_hand_by_language"]
    out.append(_row(["Leibniz's hand", _n(sum(lb.values())), *_lang_cells(lb)]))
    out.append("")
    out.append(
        f"The factory's Textart rule (`stratum_from_textart`) recognises a document class on "
        f"{_n(summ['pieces_with_katalog_stratum_signal'])} of the {_n(len(pcs))} pieces: the "
        "catalogue writes `Abf.`, `Konz.`, `Abschr.`, `Ausz.`, `Reinschr.`, which the rule's "
        "full-word keys do not match, so the stratum came from the layout statistics alone."
    )
    if cache is not None and snippets:
        out.append("")
        out.append("## A look at the classification")
        out.append("")
        out.append(
            "The first characters of a few pieces per class (the §70-expired reading text, "
            "as the cache holds it), to judge the identifier by eye:"
        )
        out.append("")
        for lang in ("de", "mixed", "unknown"):
            for pc in [pc for pc in pcs if pc.language == lang][:snippets]:
                snippet = " ".join(cache.get(pc.record_id, "").split())[:110]
                out.append(
                    f"- `{lang}` {pc.score:.2f} — {pc.aa_label}, katalog {pc.record_id} "
                    f"({pc.textart or 'no Textart'}): “{snippet}…”"
                )
        out.append("")
    out.append("## What this measures, and what it does not")
    out.append("")
    out.append(
        "- The language is the edition text's, piece by piece. A German letter quoting Latin for a "
        "third of its length is `de`; a German piece whose cache text carries a bled-in German "
        "editorial note stays `de`; a Latin piece with such a note gains German hits and, when "
        "short, can read `mixed`. The snippets above are the check."
    )
    out.append(
        "- Lines are the recognised v1 lines on the piece's canvases, counted the way the factory "
        "gathered them; pieces sharing a page share its lines. Minted lines are keyed to the "
        "record through the factory's `source` string."
    )
    out.append(
        "- The hand is the catalogue's word, read by a rule; `partial` and `other` say nothing "
        "about who wrote the body, and a letter Leibniz received in its sender's own hand is "
        "`own` but not Leibniz's."
    )
    out.append("")
    return "\n".join(out)


def german_rows(res: CensusResult) -> list[PieceCensus]:
    """The German pieces, for K2: `de`, or `mixed` with German leading."""
    return [pc for pc in res.pieces if pc.german]


def write_outputs(
    res: CensusResult,
    *,
    reports_dir: Path | str,
    data_dir: Path | str,
    cache: Mapping[str, str] | None = None,
) -> dict[str, Path]:
    """Write the report, the summary, the volume CSV, the K2 JSONL and its index CSV."""
    reports_dir = Path(reports_dir)
    data_dir = Path(data_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    summ = summary(res)
    paths = {
        "report": reports_dir / "census.md",
        "summary": reports_dir / "census-summary.json",
        "by_volume": reports_dir / "census-by-volume.csv",
        "index": reports_dir / "german_pieces_index.csv",
        "pieces": data_dir / "german_pieces.jsonl",
    }
    paths["report"].write_text(render(res, summ, cache=cache), encoding="utf-8")
    paths["summary"].write_text(
        json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with paths["by_volume"].open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "volume",
                "pieces",
                "la",
                "fr",
                "de",
                "mixed",
                "unknown",
                "de_pieces_group",
                "de_localizable",
                "de_with_lines",
                "de_pages",
                "de_lines",
                "de_minted",
                "de_yield",
                "lafr_pieces",
                "lafr_lines",
                "lafr_minted",
                "lafr_yield",
                "de_leibniz_hand",
            ]
        )
        for vol, row in summ["by_volume"].items():
            langs = row["languages"]
            gde = row["groups"].get("de", Tally().as_dict())
            glf = row["groups"].get("la_fr", Tally().as_dict())
            w.writerow(
                [
                    vol,
                    row["pieces"],
                    langs.get("la", 0),
                    langs.get("fr", 0),
                    langs.get("de", 0),
                    langs.get("mixed", 0),
                    langs.get("unknown", 0),
                    gde["pieces"],
                    gde["localizable"],
                    gde["with_lines"],
                    gde["pages"],
                    gde["lines"],
                    gde["minted"],
                    _csv_float(gde["yield"]),
                    glf["pieces"],
                    glf["lines"],
                    glf["minted"],
                    _csv_float(glf["yield"]),
                    row["german_leibniz_hand"],
                ]
            )
    german = german_rows(res)
    with paths["pieces"].open("w", encoding="utf-8") as fh:
        for pc in german:
            fh.write(json.dumps(asdict(pc), ensure_ascii=False) + "\n")
    index_fields = [
        "record_id",
        "work_id",
        "aa_label",
        "signature",
        "folio_range",
        "localizable",
        "n_pages",
        "n_lines",
        "n_minted",
        "stratum",
        "hand",
        "leibniz_hand",
        "language",
        "top",
        "score",
        "textart",
        "absender",
        "adressat",
        "datum",
    ]
    with paths["index"].open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(index_fields)
        for pc in german:
            d = asdict(pc)
            d["folio_range"] = "-".join(str(x) for x in pc.folio_range) if pc.folio_range else ""
            w.writerow([d[f] if d[f] is not None else "" for f in index_fields])
    return paths


def _csv_float(x: float | None) -> str:
    return "" if x is None else f"{x:.4f}"


__all__ = [
    "HANDS",
    "LANGS",
    "STRATA",
    "CensusResult",
    "MintTally",
    "PieceCensus",
    "Tally",
    "census",
    "count_recognised_lines",
    "german_rows",
    "hand_from_textart",
    "is_leibniz_hand",
    "minted_by_record",
    "open_readonly",
    "render",
    "summary",
    "tally_by",
    "write_outputs",
]
