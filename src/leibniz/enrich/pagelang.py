"""Which pages are German: the stopword identifier over every page's machine text (K4, Task 1).

The website shows German pages through a Latin-trained model's reading (v1),
and the K1 census found the edition's German pieces on 5,874 of the Nachlass's
pages — the pieces the §70-expired volumes print, a fraction of the German in
the collection. K4 re-reads every German page with a Kurrent reader, so the
German pages have to be found first, from the only text every page has: the
v1 machine text. This module classifies it with :mod:`leibniz.enrich.langid`
(built for clean edition text, so measured here before it is trusted) and
hands the result to the index (the ``page_lang`` table, Task 2), the reading
job (the page list, Task 3) and the store (Task 4).

The method. For every recognised page the current machine text — the newest
run's row per line, the rule of :func:`leibniz.search.documents.latest_lines`,
text columns only — is joined line by line and classified; the verdict
(``la`` | ``fr`` | ``de`` | ``mixed`` | ``unknown``), the leading language's
share of the stopword hits (the *score*), the hit counts and the token count
are kept per page. A page is called German by a :class:`Threshold` over the
leading language, its hit count, its score and the token count; the default
threshold is the identifier's own verdict (``lang == "de"``: two hits, a
share of 0.65, eight tokens).

The measure. The census's pieces are the labelled set: the pages of the
German pieces (German, or mixed with German leading, the K2 definition) are
the positives, the pages of the Latin and French pieces the negatives, a page
both groups claim and the pages of the other pieces (mixed otherwise,
unknown) set aside. Precision and recall for German are computed at every
threshold of a grid, and the threshold is chosen for precision: a German
verdict on a Latin page costs a Kurrent reading of a Latin page, which is
worse than v1's, while a missed German page keeps the reading it has. The
labels are the edition's, not the page's — a German piece can carry a Latin
address or quotation on one of its pages — so the measured precision is a
floor. The census's own German pages are German by the edition's text
whatever the machine text says: the page set for the reading job is the
threshold's pages joined with them, each page's evidence recorded
(``machine``, ``edition`` or ``both``).

Outputs: ``data/kurrent/page-lang.jsonl`` (one row per recognised page: the
verdict, the score, the counts, the German flag and its evidence),
``reports/kurrent/page-lang.md`` + ``.json`` (the measure, the sweep, the
threshold, the German pages and lines by collection) and
``page-lang-works.csv`` (the same by convolute). The store is opened by the
caller; nothing here writes to it (Task 4 writes the table).
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz import db
from leibniz.enrich.langid import DOMINANT, MIN_HITS, MIN_TOKENS, classify

DEFAULT_OUT = Path("data/kurrent/page-lang.jsonl")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
VERDICTS: tuple[str, ...] = ("la", "fr", "de", "mixed", "unknown")
GROUPS: tuple[str, ...] = ("de", "la_fr", "other", "both")
PRECISION_TARGET = 0.95
SWEEP_HITS: tuple[int, ...] = (2, 3, 4, 5, 6, 8, 10, 15, 20)
SWEEP_SCORES: tuple[float, ...] = (0.5, 0.6, 0.65, 0.7, 0.8, 0.9, 0.95)
SWEEP_TOKENS: tuple[int, ...] = (8, 20, 40)
TOP_WORKS = 40


# --------------------------------------------------------------------------- #
# The verdict per page
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PageLang:
    """One recognised page: the identifier's verdict on its current machine text."""

    page_id: str
    work_id: str
    set_name: str
    lang: str  # la | fr | de | mixed | unknown
    score: float  # the leading language's share of the stopword hits
    n_tokens: int
    n_lines: int  # lines with text
    top: str | None
    second: str | None
    hits: dict[str, int] = field(default_factory=dict)
    german: bool = False  # the chosen threshold's verdict, joined with the census
    evidence: str | None = None  # machine | edition | both

    def as_row(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Mapping) -> PageLang:
        return cls(
            page_id=row["page_id"],
            work_id=row["work_id"],
            set_name=row["set_name"],
            lang=row["lang"],
            score=float(row["score"]),
            n_tokens=int(row["n_tokens"]),
            n_lines=int(row["n_lines"]),
            top=row.get("top"),
            second=row.get("second"),
            hits=dict(row.get("hits") or {}),
            german=bool(row.get("german", False)),
            evidence=row.get("evidence"),
        )


def current_texts(conn: sqlite3.Connection, page_id: str) -> list[str]:
    """The page's current machine text, one string per line with text.

    The newest run per line, as :func:`leibniz.search.documents.latest_lines`
    chooses it (``NULL`` run ids count as 0), but reading the text columns
    only: the geometry of 13.5 million rows is not decoded for a language pass.
    """
    rows = conn.execute(
        "SELECT line_seq, COALESCE(run_id, 0) AS run, text FROM lines"
        " WHERE page_id = ? AND text IS NOT NULL AND text != ''"
        " ORDER BY line_seq, run",
        (page_id,),
    )
    best: dict[int, str] = {}
    for seq, _run, text in rows:  # ordered by run: the last row per line wins
        best[seq] = text
    return [best[k] for k in sorted(best)]


def classify_pages(
    conn: sqlite3.Connection,
    *,
    progress: Callable[[int, int], None] | None = None,
    every: int = 5000,
) -> list[PageLang]:
    """Every recognised page classified on its current machine text, in page order."""
    sets = {w.gwlb_object_id: w.set_name for w in db.iter_works(conn)}
    pages = conn.execute(
        "SELECT page_id, work_id FROM pages WHERE status = 'recognized' ORDER BY page_id"
    ).fetchall()
    out: list[PageLang] = []
    total = len(pages)
    for k, (pid, wid) in enumerate(pages, start=1):
        texts = current_texts(conn, pid)
        r = classify("\n".join(texts))
        out.append(
            PageLang(
                page_id=pid,
                work_id=wid,
                set_name=sets.get(wid, ""),
                lang=r.lang,
                score=round(r.score, 4),
                n_tokens=r.n_tokens,
                n_lines=len(texts),
                top=r.top,
                second=r.second,
                hits=dict(r.hits),
            )
        )
        if progress is not None and (k % every == 0 or k == total):
            progress(k, total)
    return out


def write_jsonl(path: Path | str, rows: Iterable[PageLang]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r.as_row(), ensure_ascii=False) + "\n")
    return path


def read_jsonl(path: Path | str) -> list[PageLang]:
    out: list[PageLang] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(PageLang.from_row(json.loads(line)))
    return out


# --------------------------------------------------------------------------- #
# The threshold
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Threshold:
    """When a page's verdict counts as German: the leading language is German
    with at least ``min_hits`` German stopwords, a share of at least
    ``min_score`` of all hits, and ``min_tokens`` tokens on the page. The
    defaults are the identifier's own rule for ``lang == "de"``."""

    min_hits: int = MIN_HITS
    min_score: float = DOMINANT
    min_tokens: int = MIN_TOKENS

    def german(self, r: PageLang) -> bool:
        return (
            r.top == "de"
            and r.hits.get("de", 0) >= self.min_hits
            and r.score >= self.min_score
            and r.n_tokens >= self.min_tokens
        )

    @property
    def key(self) -> str:
        return f"hits≥{self.min_hits} score≥{self.min_score:g} tokens≥{self.min_tokens}"

    def as_dict(self) -> dict:
        return {
            "min_hits": self.min_hits,
            "min_score": self.min_score,
            "min_tokens": self.min_tokens,
        }


# --------------------------------------------------------------------------- #
# The labelled set: the census's pieces
# --------------------------------------------------------------------------- #


def piece_group(text: str) -> tuple[str, str]:
    """A piece's census group from its edition text: ``(group, verdict)`` where the
    group is ``de`` (German, or mixed with German leading — what K2 took),
    ``la_fr`` or ``other``."""
    r = classify(text)
    if r.lang == "de" or (r.lang == "mixed" and r.top == "de"):
        return "de", r.lang
    if r.lang in ("la", "fr"):
        return "la_fr", r.lang
    return "other", r.lang


@dataclass(slots=True)
class Labels:
    """The census's pieces placed on pages: per page its group (``de`` | ``la_fr``
    | ``other`` | ``both`` where German and Latin/French pieces share it) and,
    where one language's pieces alone claim it, that language."""

    group: dict[str, str] = field(default_factory=dict)
    lang: dict[str, str] = field(default_factory=dict)
    n_pieces: dict[str, int] = field(default_factory=dict)  # placed pieces by group
    n_pages: dict[str, int] = field(default_factory=dict)  # pages by group

    def positives(self) -> set[str]:
        return {p for p, g in self.group.items() if g == "de"}

    def negatives(self) -> set[str]:
        return {p for p, g in self.group.items() if g == "la_fr"}


def census_labels(conn: sqlite3.Connection, cache: Mapping[str, str], *, today: date) -> Labels:
    """Place every localizable piece with an edition text, as the K1 census did
    (the factory's resolver, one folio index per work), and label its pages."""
    from leibniz.align.resolve import index_pages, select_folios
    from leibniz.align.volumes import enumerate_pieces

    pieces, _stats = enumerate_pieces(conn, today=today)
    groups: dict[str, set[str]] = defaultdict(set)
    langs: dict[str, set[str]] = defaultdict(set)
    indexes: dict[str, dict[int, list[db.Page]]] = {}
    n_pieces: Counter[str] = Counter()
    for piece in pieces:
        text = cache.get(piece.record_id)
        if text is None or not piece.localizable:
            continue
        assert piece.work_id is not None and piece.folio_range is not None
        group, verdict = piece_group(text)
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
        if not pages:
            continue
        n_pieces[group] += 1
        for p in pages:
            groups[p.id].add(group)
            langs[p.id].add(verdict)
    labels = Labels(n_pieces=dict(n_pieces))
    for pid, gs in groups.items():
        if "de" in gs and "la_fr" in gs:
            labels.group[pid] = "both"
        elif "de" in gs:
            labels.group[pid] = "de"
        elif "la_fr" in gs:
            labels.group[pid] = "la_fr"
        else:
            labels.group[pid] = "other"
        if len(langs[pid]) == 1:
            labels.lang[pid] = next(iter(langs[pid]))
    labels.n_pages = dict(Counter(labels.group.values()))
    return labels


# --------------------------------------------------------------------------- #
# The measure
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Measure:
    """Precision and recall for German at one threshold over the labelled pages."""

    threshold: Threshold
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else None

    @property
    def n_called(self) -> int:
        return self.tp + self.fp

    def as_dict(self) -> dict:
        return {
            "threshold": self.threshold.as_dict(),
            "key": self.threshold.key,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "tn": self.tn,
            "precision": None if self.precision is None else round(self.precision, 4),
            "recall": None if self.recall is None else round(self.recall, 4),
        }


def measure(rows: Sequence[PageLang], labels: Labels, threshold: Threshold) -> Measure:
    pos, neg = labels.positives(), labels.negatives()
    tp = fp = fn = tn = 0
    for r in rows:
        if r.page_id in pos:
            if threshold.german(r):
                tp += 1
            else:
                fn += 1
        elif r.page_id in neg:
            if threshold.german(r):
                fp += 1
            else:
                tn += 1
    return Measure(threshold, tp, fp, fn, tn)


def sweep(
    rows: Sequence[PageLang],
    labels: Labels,
    *,
    hits: Sequence[int] = SWEEP_HITS,
    scores: Sequence[float] = SWEEP_SCORES,
    tokens: Sequence[int] = SWEEP_TOKENS,
) -> list[Measure]:
    """Precision and recall at every threshold of the grid, one row per threshold."""
    return [measure(rows, labels, Threshold(h, s, t)) for t in tokens for s in scores for h in hits]


def pick(measures: Sequence[Measure], *, target: float = PRECISION_TARGET) -> Measure | None:
    """The threshold for precision: of those at or above ``target``, the one with
    the highest recall (ties: the fewest constraints — lower hits, lower score,
    fewer tokens); ``None`` when no threshold of the grid reaches the target."""
    ok = [m for m in measures if m.precision is not None and m.precision >= target]
    if not ok:
        return None
    return max(
        ok,
        key=lambda m: (
            m.recall or 0.0,
            -m.threshold.min_hits,
            -m.threshold.min_score,
            -m.threshold.min_tokens,
        ),
    )


def confusion(rows: Sequence[PageLang], labels: Labels) -> dict[str, dict[str, int]]:
    """The identifier's verdict against the pieces' language, over the pages one
    language's pieces alone claim: ``{piece lang: {verdict: pages}}``."""
    out: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        lab = labels.lang.get(r.page_id)
        if lab is not None:
            out[lab][r.lang] += 1
    return {k: dict(v) for k, v in out.items()}


# --------------------------------------------------------------------------- #
# The German pages
# --------------------------------------------------------------------------- #


def mark_german(
    rows: Sequence[PageLang], threshold: Threshold, labels: Labels | None = None
) -> dict[str, int]:
    """Set every row's ``german`` flag and ``evidence``: the threshold's verdict on
    the machine text, joined with the census's German pages (the edition's
    text). Returns the counts by evidence."""
    edition = labels.positives() if labels is not None else set()
    counts: Counter[str] = Counter()
    for r in rows:
        machine = threshold.german(r)
        by_edition = r.page_id in edition
        if machine and by_edition:
            r.german, r.evidence = True, "both"
        elif machine:
            r.german, r.evidence = True, "machine"
        elif by_edition:
            r.german, r.evidence = True, "edition"
        else:
            r.german, r.evidence = False, None
        if r.german:
            counts[r.evidence or ""] += 1
    return dict(counts)


def german_page_ids(rows: Iterable[PageLang]) -> list[str]:
    return [r.page_id for r in rows if r.german]


def write_page_list(path: Path | str, rows: Iterable[PageLang]) -> Path:
    """The German pages, one id a line (the reading job's input)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{pid}\n" for pid in german_page_ids(rows)), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# The summary and the report
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class WorkTally:
    work_id: str
    set_name: str
    title: str | None
    shelfmark: str | None
    pages: int = 0  # recognised pages
    lines: int = 0  # lines with text
    german_pages: int = 0
    german_lines: int = 0
    by_lang: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def tally_works(conn: sqlite3.Connection, rows: Sequence[PageLang]) -> list[WorkTally]:
    works = {w.gwlb_object_id: w for w in db.iter_works(conn)}
    out: dict[str, WorkTally] = {}
    for r in rows:
        t = out.get(r.work_id)
        if t is None:
            w = works.get(r.work_id)
            t = WorkTally(
                r.work_id,
                r.set_name,
                w.title if w else None,
                (w.shelfmarks[0] if w and w.shelfmarks else None),
            )
            out[r.work_id] = t
        t.pages += 1
        t.lines += r.n_lines
        t.by_lang[r.lang] = t.by_lang.get(r.lang, 0) + 1
        if r.german:
            t.german_pages += 1
            t.german_lines += r.n_lines
    return sorted(out.values(), key=lambda t: (-t.german_pages, -t.german_lines, t.work_id))


def summary(
    rows: Sequence[PageLang],
    *,
    labels: Labels | None,
    sweep_rows: Sequence[Measure],
    chosen: Measure | None,
    threshold: Threshold,
    default: Measure | None,
    target: float,
    works: Sequence[WorkTally],
    today: date,
) -> dict:
    by_lang = Counter(r.lang for r in rows)
    by_set: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for r in rows:
        s = by_set[r.set_name]
        s["pages"] += 1
        s["lines"] += r.n_lines
        if r.german:
            s["german_pages"] += 1
            s["german_lines"] += r.n_lines
    evidence = Counter(r.evidence for r in rows if r.german)
    de_scores = sorted(r.score for r in rows if r.german and r.evidence != "edition")
    out = {
        "generated": date.today().isoformat(),
        "today": today.isoformat(),
        "pages": len(rows),
        "pages_with_text": sum(1 for r in rows if r.n_lines),
        "lines": sum(r.n_lines for r in rows),
        "by_lang": {k: by_lang.get(k, 0) for k in VERDICTS},
        "threshold": threshold.as_dict(),
        "threshold_key": threshold.key,
        "precision_target": target,
        "german_pages": sum(1 for r in rows if r.german),
        "german_lines": sum(r.n_lines for r in rows if r.german),
        "german_by_evidence": {k: evidence.get(k, 0) for k in ("machine", "edition", "both")},
        "german_score_quartiles": (
            [de_scores[len(de_scores) // 4], de_scores[len(de_scores) // 2], de_scores[-1]]
            if de_scores
            else []
        ),
        "by_set": {k: dict(v) for k, v in sorted(by_set.items())},
        "works_with_german": sum(1 for t in works if t.german_pages),
        "works": [t.as_dict() for t in works[:TOP_WORKS]],
    }
    if labels is not None:
        out["labels"] = {
            "pieces_by_group": labels.n_pieces,
            "pages_by_group": labels.n_pages,
            "pages_measured": len(
                [r for r in rows if labels.group.get(r.page_id) in ("de", "la_fr")]
            ),
            "positives": len(labels.positives()),
            "negatives": len(labels.negatives()),
        }
        out["default"] = default.as_dict() if default else None
        out["chosen"] = chosen.as_dict() if chosen else None
        out["sweep"] = [m.as_dict() for m in sweep_rows]
        out["confusion"] = confusion(rows, labels)
    return out


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{d}f} %"


def _n(x: int | None) -> str:
    return "—" if x is None else f"{x:,}"


def render(summ: Mapping) -> str:
    L: list[str] = []
    a = L.append
    a("# Which pages are German: the identifier on the machine text")
    a("")
    a(
        f"Every recognised page's current machine text (the newest run per line, v1 today) "
        f"classified with `leibniz.enrich.langid` — {_n(summ['pages'])} pages, "
        f"{_n(summ['lines'])} lines with text ({_n(summ['pages_with_text'])} pages carry any). "
        f"A page counts as German at the threshold **{summ['threshold_key']}** on the leading "
        f"language's stopword hits, their share of all hits and the page's tokens; the "
        f"threshold is set for precision (target {_pct(summ['precision_target'], 0)}) on the "
        f"census's pieces, see below. Generated {summ['generated']}; the store read-only."
    )
    a("")
    a("## The verdicts")
    a("")
    a("| verdict | pages |")
    a("|---|---:|")
    for k in VERDICTS:
        a(f"| {k} | {_n(summ['by_lang'][k])} |")
    a("")
    ev = summ["german_by_evidence"]
    a(
        f"**German pages: {_n(summ['german_pages'])}, with {_n(summ['german_lines'])} lines** — "
        f"by the machine text alone {_n(ev['machine'])}, by the edition's text alone (the "
        f"census's German pieces, whatever the machine text says) {_n(ev['edition'])}, by both "
        f"{_n(ev['both'])}."
    )
    q = summ.get("german_score_quartiles") or []
    if q:
        a("")
        a(
            f"Scores of the pages called German on their machine text: first quartile "
            f"{q[0]:.2f}, median {q[1]:.2f}, maximum {q[2]:.2f}."
        )
    if "labels" in summ:
        lab = summ["labels"]
        a("")
        a("## The measure, on the census's pieces")
        a("")
        a(
            f"The labelled set: the pages of the census's pieces placed by the factory's "
            f"resolver — German pieces (German, or mixed with German leading) "
            f"{_n(lab['pieces_by_group'].get('de', 0))} pieces on "
            f"{_n(lab['pages_by_group'].get('de', 0))} pages (the positives), Latin and French "
            f"pieces {_n(lab['pieces_by_group'].get('la_fr', 0))} on "
            f"{_n(lab['pages_by_group'].get('la_fr', 0))} pages (the negatives); set aside: "
            f"{_n(lab['pages_by_group'].get('both', 0))} pages both groups claim and "
            f"{_n(lab['pages_by_group'].get('other', 0))} pages of the other pieces (mixed "
            f"otherwise, unknown; {_n(lab['pieces_by_group'].get('other', 0))} pieces). "
            f"{_n(lab['pages_measured'])} of the labelled pages are recognised and measured. "
            f"The labels are the pieces', not the pages' — a German piece can carry a Latin "
            f"address or quotation on one page — so the precision below is a floor."
        )
        a("")
        d, c = summ.get("default"), summ.get("chosen")
        a("| threshold | called German | true | false | missed | precision | recall |")
        a("|---|---:|---:|---:|---:|---:|---:|")
        if d:
            a(
                f'| the identifier\'s own verdict (`lang == "de"`: {d["key"]}) | '
                f"{_n(d['tp'] + d['fp'])} | {_n(d['tp'])} | {_n(d['fp'])} | {_n(d['fn'])} | "
                f"{_pct(d['precision'])} | {_pct(d['recall'])} |"
            )
        if c:
            a(
                f"| **chosen: {c['key']}** | {_n(c['tp'] + c['fp'])} | {_n(c['tp'])} | "
                f"{_n(c['fp'])} | {_n(c['fn'])} | **{_pct(c['precision'])}** | "
                f"**{_pct(c['recall'])}** |"
            )
        else:
            a(
                f"| no threshold of the grid reaches a precision of "
                f"{_pct(summ['precision_target'], 0)} | | | | | | |"
            )
        a("")
        a(
            "The sweep (hits = German stopwords on the page; score = their share of all "
            "stopword hits; tokens = the page's tokens):"
        )
        a("")
        a("| hits ≥ | score ≥ | tokens ≥ | called German | false | precision | recall |")
        a("|---:|---:|---:|---:|---:|---:|---:|")
        for m in summ["sweep"]:
            t = m["threshold"]
            a(
                f"| {t['min_hits']} | {t['min_score']:g} | {t['min_tokens']} | "
                f"{_n(m['tp'] + m['fp'])} | {_n(m['fp'])} | {_pct(m['precision'])} | "
                f"{_pct(m['recall'])} |"
            )
        a("")
        a(
            "The identifier's verdict against the pieces' language, over the pages one "
            "language's pieces alone claim (rows: the piece's language from the edition text; "
            "columns: the verdict on the machine text):"
        )
        a("")
        a("| piece | " + " | ".join(VERDICTS) + " | pages |")
        a("|---|" + "---:|" * (len(VERDICTS) + 1))
        conf = summ["confusion"]
        for lab in VERDICTS:
            row = conf.get(lab)
            if not row:
                continue
            a(
                f"| {lab} | "
                + " | ".join(_n(row.get(v, 0)) for v in VERDICTS)
                + f" | {_n(sum(row.values()))} |"
            )
    a("")
    a("## German pages and lines by collection")
    a("")
    a("| collection | pages | lines | German pages | German lines | share of pages |")
    a("|---|---:|---:|---:|---:|---:|")
    for name, s in summ["by_set"].items():
        gp = s.get("german_pages", 0)
        a(
            f"| {name} | {_n(s['pages'])} | {_n(s['lines'])} | {_n(gp)} | "
            f"{_n(s.get('german_lines', 0))} | {_pct(gp / s['pages'] if s['pages'] else None)} |"
        )
    a("")
    a("## By convolute")
    a("")
    a(
        f"{_n(summ['works_with_german'])} convolutes carry a German page; the {TOP_WORKS} with "
        f"the most, the whole table in `page-lang-works.csv`:"
    )
    a("")
    a("| work | collection | shelfmark | pages | German pages | German lines |")
    a("|---|---|---|---:|---:|---:|")
    for t in summ["works"]:
        if not t["german_pages"]:
            break
        a(
            f"| {t['work_id']} | {t['set_name']} | {t['shelfmark'] or t['title'] or ''} | "
            f"{_n(t['pages'])} | {_n(t['german_pages'])} | {_n(t['german_lines'])} |"
        )
    a("")
    return "\n".join(L)


def write_works_csv(path: Path | str, works: Sequence[WorkTally]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["work_id", "set_name", "title", "shelfmark", "pages", "lines", "german_pages"]
    cols += ["german_lines", *VERDICTS]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for t in works:
            w.writerow(
                [
                    t.work_id,
                    t.set_name,
                    t.title or "",
                    t.shelfmark or "",
                    t.pages,
                    t.lines,
                    t.german_pages,
                    t.german_lines,
                    *(t.by_lang.get(v, 0) for v in VERDICTS),
                ]
            )
    return path


def write_reports(
    summ: Mapping, works: Sequence[WorkTally], *, reports_dir: Path | str = DEFAULT_REPORTS_DIR
) -> dict[str, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    md = reports_dir / "page-lang.md"
    js = reports_dir / "page-lang.json"
    md.write_text(render(summ), encoding="utf-8")
    js.write_text(json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cs = write_works_csv(reports_dir / "page-lang-works.csv", works)
    return {"page-lang.md": md, "page-lang.json": js, "page-lang-works.csv": cs}


__all__ = [
    "DEFAULT_OUT",
    "DEFAULT_REPORTS_DIR",
    "GROUPS",
    "PRECISION_TARGET",
    "VERDICTS",
    "Labels",
    "Measure",
    "PageLang",
    "Threshold",
    "WorkTally",
    "census_labels",
    "classify_pages",
    "confusion",
    "current_texts",
    "german_page_ids",
    "mark_german",
    "measure",
    "pick",
    "piece_group",
    "read_jsonl",
    "render",
    "summary",
    "sweep",
    "tally_works",
    "write_jsonl",
    "write_page_list",
    "write_reports",
    "write_works_csv",
]
