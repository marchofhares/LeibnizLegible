"""The browse index (Phase W3): the Nachlass by shelfmark family, section and convolute.

The third way in, beside search and a known address: start from the group a
shelfmark belongs to and walk down to the convolute, whose page lists the
folios. Everything here is a pure function of rows the store already holds —

* the ``works`` rows (:class:`leibniz.db.Work`),
* per letter convolute, the sender/addressee pairs of its linked catalogue
  records (:data:`CORRESPONDENTS_SQL`, one grouped query),
* the ids of the works that have catalogue records at all —

and :func:`build_index` returns the tree ``family → section → entry`` that
``GET /api/works`` and ``/browse`` serve. No store access, no I/O.

Where a work goes, as the 2,225 live rows (2026-10) required it:

* **Family** is that of the work's first shelfmark with a recognised label
  (:func:`~leibniz.catalog.shelfmarks.normalize_signature`), whatever OAI set
  the work sits in: ``LBr. 726`` is filed in the manuscripts' set and belongs
  with the letters. The two small sets (Leibnitiana, the reconstructions) are
  never spread over the series; they, and every work without a usable LH, LBr
  or Marg shelfmark, go to *Other*, one section per set.
* **LH**: the section is the first part (``LH 35``). Its label is the phrase
  the library's titles give it (*Mathematik* in "Leibniz-Handschriften zur
  Mathematik LH 35, 3 A 8") where more than half of the section's titles
  agree, else ``LH <n>``; an entry whose own phrase differs from the label
  carries it (``LH 37, 1 · Akustik``).
* **LBr**: one section; an entry is labelled with its correspondent — a name
  found beside Leibniz in the linked records' sender and addressee cells (else
  the *X* of a record titled "X an Leibniz" / "Leibniz an X"), and shown only
  if it fits the alphabetical order of the LBr numbers
  (:func:`names_in_order`: the linked records are not the whole convolute, and
  their most frequent name can be somebody else's); otherwise the bare
  shelfmark. Two orders: by name, and by number.
* **Marg**: one section, by number, the printed book's title cut to about 120
  characters.
* **Order** is natural (2 before 10, numbers before letters) and read from the
  shelfmark *as written*: the normaliser turns a lone C, D, I, L, M, V or X
  into a Roman numeral, which is right for ``LH XXXV, I, 17`` and wrong for the
  part letters of ``LH 1, 3, 7 C``. Letters stay letters unless the section
  itself is written in Roman numerals.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import NamedTuple

from leibniz.catalog.shelfmarks import normalize_signature, roman_to_int, split_family
from leibniz.db import Work

FAMILIES = ("LH", "LBr", "Marg", "Other")
# The archive's own words for the families; they stay German in both languages.
FAMILY_NAMES = {
    "LH": "Handschriften (LH)",
    "LBr": "Briefwechsel (LBr)",
    "Marg": "Marginalien",
    "Other": "Other",
}
# The viewer's names for the OAI sets (``set.*`` in static/i18n.js).
SET_LABELS = {
    "LeibnizHandschriften": "Leibniz-Handschriften (LH)",
    "LeibnizBriefwechsel": "Leibniz-Briefwechsel (LBr)",
    "LeibnizMarginalien": "Leibniz-Marginalien",
    "Leibnitiana": "Leibnitiana",
    "leibniz-rekonstruktionen": "Leibniz-Rekonstruktionen",
}
SMALL_SETS = frozenset({"Leibnitiana", "leibniz-rekonstruktionen"})
TITLE_LIMIT = 120
LEIBNIZ = "Leibniz"

# One row per (work, sender, addressee) over the catalogue records linked to the
# letter convolutes — the ``Briefwechsel`` set, and any work shelved as LBr
# elsewhere. ``tests/fixtures/lbr_correspondents_live.json`` is this query's
# result on the live store.
CORRESPONDENTS_SQL = """
SELECT c.work_id,
       json_extract(k.metadata, '$.absender') AS absender,
       json_extract(k.metadata, '$.adressat') AS adressat,
       COUNT(*) AS n_records,
       MIN(json_extract(k.metadata, '$.titel')) AS titel
  FROM crosswalk c
  JOIN katalog_records k ON k.record_id = c.katalog_record_id
  JOIN works w ON w.gwlb_object_id = c.work_id
 WHERE w.set_name = 'LeibnizBriefwechsel' OR w.shelfmarks LIKE '%LBr%'
 GROUP BY c.work_id, json_extract(k.metadata, '$.absender'),
          json_extract(k.metadata, '$.adressat')
 ORDER BY c.work_id, n_records DESC
"""


class Correspondence(NamedTuple):
    """One sender/addressee pair among a work's catalogue records, as the
    catalogue writes them (``"Oldenburg (KorrespDB) (GND)"``, ``"Leibniz (GND)"``),
    the number of records carrying it, and one of their titles."""

    absender: str | None
    adressat: str | None
    n_records: int = 1
    titel: str | None = None


@dataclass(frozen=True, slots=True)
class Entry:
    """One work in its section."""

    work_id: str
    set_name: str
    shelfmark: str  # the shelfmark that places it, as written ("" where none)
    shelfmarks: tuple[str, ...]
    label: str  # what names it in its section; never empty
    title: str
    n_canvases: int
    has_katalog: bool


@dataclass(slots=True)
class Section:
    """A group of works under one stable anchor (``lh-35``, ``lbr``, ``marg``,
    ``other-leibnitiana``)."""

    family: str
    key: str  # "35" | "LBr" | "Marg" | the set name
    anchor: str
    label: str
    entries: list[Entry] = field(default_factory=list)
    # LBr only: ``entries`` are in name order (the unnamed last, by number);
    # this is the same work ids in shelfmark order.
    by_number: list[str] | None = None

    @property
    def n_works(self) -> int:
        return len(self.entries)

    @property
    def n_pages(self) -> int:
        return sum(e.n_canvases for e in self.entries)

    @property
    def title(self) -> str:
        """``LH 35 · Mathematik``, ``LH 37``; elsewhere the label."""
        if self.family != "LH":
            return self.label
        name = f"LH {self.key}"
        return name if self.label == name else f"{name} · {self.label}"


@dataclass(slots=True)
class Family:
    key: str
    sections: list[Section] = field(default_factory=list)

    @property
    def name(self) -> str:
        return FAMILY_NAMES.get(self.key, self.key)

    @property
    def n_works(self) -> int:
        return sum(s.n_works for s in self.sections)

    @property
    def n_pages(self) -> int:
        return sum(s.n_pages for s in self.sections)


# ---- order ------------------------------------------------------------------- #

_RUNS = re.compile(r"\d+|[^\W\d_]+")
NaturalKey = tuple[tuple[int, int, str], ...]


def natural_key(text: str, *, roman: bool = False) -> NaturalKey:
    """A sort key over the digit and letter runs of ``text``: numbers by value
    and before letters, so ``2`` < ``10`` < ``a``, and ``7`` < ``7 A`` = ``7a``
    < ``7b``. With ``roman``, a run that is a Roman numeral counts as its number."""
    key: list[tuple[int, int, str]] = []
    for run in _RUNS.findall(text):
        if run.isdigit():
            key.append((0, int(run), ""))
        elif roman and (value := roman_to_int(run)) is not None:
            key.append((0, value, ""))
        else:
            key.append((1, 0, run.casefold()))
    return tuple(key)


def _fold(text: str) -> str:
    """Case- and accent-blind, for the alphabetical order of names."""
    plain = unicodedata.normalize("NFKD", text)
    return "".join(c for c in plain if not unicodedata.combining(c)).casefold().lstrip("([ ")


# ---- placing a work ---------------------------------------------------------- #

# "L Br. 827": one live shelfmark spells the label apart.
_SPACED_LBR = re.compile(r"\bL\s+Br\b")


class _Placed(NamedTuple):
    family: str  # LH | LBr | Marg
    mark: str  # the placing shelfmark, as written
    section: int | None  # LH: the first part
    order: NaturalKey


def _place(work: Work) -> _Placed | None:
    """Where the work's first usable shelfmark puts it; ``None`` → *Other*."""
    if work.set_name in SMALL_SETS:
        return None
    for raw in work.shelfmarks or ():
        mark = " ".join(str(raw).split())
        repaired = _SPACED_LBR.sub("LBr", mark)
        sig = normalize_signature(repaired)
        if sig.family not in ("LH", "LBr", "Marg") or not sig.parts:
            continue
        tail = split_family(repaired)[1].split("(", 1)[0]
        if sig.family != "LH":
            return _Placed(sig.family, mark, None, natural_key(tail))
        if not sig.parts[0].isdigit():
            continue
        runs = _RUNS.findall(tail)
        roman = bool(runs) and not runs[0].isdigit()
        return _Placed("LH", mark, int(sig.parts[0]), natural_key(tail, roman=roman))
    return None


def truncate(text: str, limit: int = TITLE_LIMIT) -> str:
    """``text`` on one line, cut at a word boundary near ``limit`` with an ellipsis."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit + 1)
    if cut < limit * 0.6:  # one very long word: cut inside it
        cut = limit
    return text[:cut].rstrip(" ,;:.-–—/|[(") + "…"


def _entry(work: Work, mark: str, label: str, with_records: Collection[str]) -> Entry:
    return Entry(
        work_id=work.gwlb_object_id,
        set_name=work.set_name,
        shelfmark=mark,
        shelfmarks=tuple(str(m) for m in work.shelfmarks or ()),
        label=label,
        title=" ".join((work.title or "").split()),
        n_canvases=work.n_canvases or 0,
        has_katalog=work.gwlb_object_id in with_records,
    )


# ---- LH: sections and their names -------------------------------------------- #

_LH_IN_TITLE = re.compile(r"\s+LH\s*[0-9IVXLC]")
_LH_TITLE_HEAD = re.compile(r"^Leibnit?z\s*[-_ ]\s*Hand?schriften\b\s*", re.IGNORECASE)
_PREPOSITION = re.compile(r"^(?:zur|zum|zu)\s+")


def section_phrase(title: str | None) -> str | None:
    """The section name a manuscript title carries: *Mathematik* out of
    "Leibniz-Handschriften zur Mathematik LH 35, 3 A 8"; ``None`` if it has none.

    Tolerates the catalogue's slips (``Leibniz_Handschriften``, ``Leibnitz-``,
    ``Hanschriften``, a missing "zur") and keeps the phrase as written.
    """
    text = " ".join((title or "").split())
    found = _LH_IN_TITLE.search(text)
    if found is None:
        return None
    head = _LH_TITLE_HEAD.sub("", text[: found.start()].strip(), count=1)
    return _PREPOSITION.sub("", head, count=1).strip() or None


def _lh_sections(
    placed: list[tuple[_Placed, Work]], with_records: Collection[str]
) -> list[Section]:
    by_section: dict[int, list[tuple[_Placed, Work]]] = {}
    for item in placed:
        by_section.setdefault(item[0].section or 0, []).append(item)
    sections = []
    for number in sorted(by_section):
        items = sorted(by_section[number], key=lambda it: (it[0].order, it[1].gwlb_object_id))
        phrases = {work.gwlb_object_id: section_phrase(work.title) for _, work in items}
        counts = Counter(p for p in phrases.values() if p)
        name = f"LH {number}"
        label = name
        if counts:
            top, n = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            if 2 * n > len(items):
                label = top
        entries = []
        for place, work in items:
            own = phrases[work.gwlb_object_id]
            text = f"{place.mark} · {own}" if own and own != label else place.mark
            entries.append(_entry(work, place.mark, text, with_records))
        sections.append(Section("LH", str(number), f"lh-{number}", label, entries))
    return sections


# ---- LBr: the correspondent ---------------------------------------------------- #

# The catalogue's link texts after a name; a cell naming several people runs
# them together ("Brand,H. (KorrespDB) (GND)Leibniz (GND)"), so they also
# separate the names. Other parentheses belong to the name ("Leopold I. (Kaiser)").
_SOURCE_TAGS = re.compile(r"(?:\s*\((?:KorrespDB|GND)\))+")
_NOT_A_NAME = frozenset({"", "?", "u.a.", "u. a."})
_AN_LEIBNIZ = re.compile(r"^(?P<x>.+?)\s+an\s+\[?Leibniz\]?(?=$|[\s:;,.(])")
_LEIBNIZ_AN = re.compile(r"^\[?Leibniz\]?\s+an\s+(?P<x>[^:;(]+)")


def _clean_name(piece: str) -> str:
    """A name without the catalogue's doubt marks ("Ilgen ?", "Krebs (?)")."""
    name = " ".join(piece.replace("(?)", " ").split()).rstrip("?").strip()
    return re.sub(r",(?=\S)", ", ", name)  # "Fuchs,P." → "Fuchs, P."


def correspondent_names(cell: str | None) -> list[str]:
    """The people named in one sender or addressee cell, source tags stripped."""
    names = (_clean_name(piece) for piece in _SOURCE_TAGS.split(cell or ""))
    return [name for name in names if name not in _NOT_A_NAME]


def names_as_written(cell: str | None) -> list[str]:
    """The people in one sender or addressee cell as the catalogue names them,
    for showing a record rather than for counting: its link texts gone,
    several people apart, ``Surname,Initials`` spaced — and its doubt kept:
    ``"Ilgen ?"``, ``"Leibniz ?"`` (the catalogue puts the mark after the link
    text), a lone ``"?"`` for an unknown hand, ``"u.a."`` for "and others"."""
    names: list[str] = []
    for piece in _SOURCE_TAGS.split(cell or ""):
        name = re.sub(r",(?=\S)", ", ", " ".join(piece.split()))
        if name in ("?", "(?)") and names and not names[-1].endswith("?"):
            names[-1] += " ?"
        elif name:
            names.append(name)
    return names


def _name_in_titel(titel: str | None) -> str | None:
    """The *X* of "X an Leibniz" or "Leibniz an X"."""
    text = " ".join((titel or "").split())
    found = _AN_LEIBNIZ.match(text) or _LEIBNIZ_AN.match(text)
    if found is None:
        return None
    name = _clean_name(found.group("x").strip(" []?"))
    if name == LEIBNIZ or not any(c.isalpha() for c in name):  # "Leibniz an -- (?)"
        return None
    return name


def correspondent_weights(rows: Iterable[Correspondence]) -> dict[str, int]:
    """Who a convolute's catalogue records name beside Leibniz, and in how many
    records, in order of first mention.

    Every name in the sender and addressee cells counts once per record; a
    bare surname is counted with the one fuller form of it in the same
    convolute ("Eckhard" with "Eckhard, A."). Where the cells name nobody
    else, the records' titles are asked instead ("X an Leibniz").
    """
    rows = list(rows)
    weights: dict[str, int] = {}
    for row in rows:
        named = dict.fromkeys(
            [*correspondent_names(row.absender), *correspondent_names(row.adressat)]
        )
        for name in named:
            if name != LEIBNIZ:
                weights[name] = weights.get(name, 0) + (row.n_records or 1)
    if not weights:
        for row in rows:
            if name := _name_in_titel(row.titel):
                weights[name] = weights.get(name, 0) + (row.n_records or 1)
    for bare in [name for name in weights if "," not in name]:
        fuller = [name for name in weights if name.startswith(f"{bare}, ")]
        if len(fuller) == 1:
            weights[fuller[0]] += weights.pop(bare)
    return weights


def correspondent(rows: Iterable[Correspondence]) -> str | None:
    """The name most often beside Leibniz in a convolute's records; of equals
    the one named first (in "Brice … Acad.Franç." the person stands before the
    body he writes for). ``None`` where the records name nobody."""
    weights = correspondent_weights(rows)
    return max(weights, key=weights.__getitem__) if weights else None


# The LBr numbers run alphabetically by correspondent (Bodemann's catalogue of
# 1889: 2 Abercromby … 1028 Zunner), so the shelfmark itself says roughly what
# the name must be. That matters because the linked records are not the whole
# convolute: where only a few third-party letters are linked, the most frequent
# name is somebody else's (LBr. 57, Johann Bernoulli's, would read "Mencke, O.").
RESCUE_RECORDS = 10
_PARTICLES = frozenset({"v", "von", "van", "de", "des", "du", "la", "le", "of", "und", "zu", "gen"})
_CAMEL = re.compile(r"(?<=[^\W\d_A-ZÀ-Þ])(?=[A-ZÀ-Þ])")
_GENANNT = re.compile(r"\bgen\.\s*(?:v\.\s*)?([^\W\d_]+)")
_UMLAUT_DIGRAPHS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue"})
_DIGRAPH_E = re.compile(r"(?<=[aou])e")


def _spellings(words: Sequence[str]) -> set[str]:
    """One filing word out of ``words``, in the three ways an umlaut is filed:
    as its vowel (Hörnigk as Hornigk), spelled out (Böckler as Boeckler), and
    a spelled-out one as its vowel (Stoeteroggen as Stoteroggen). J reads as
    I: the numbering interfiles them (444 Janulli, 447 Ilgen, 456 Juncker)."""
    plain = "".join(_fold(w) for w in words)
    spelled = "".join(_fold(w.casefold().translate(_UMLAUT_DIGRAPHS)) for w in words)
    return {s.replace("j", "i") for s in (plain, spelled, _DIGRAPH_E.sub("", plain))} - {""}


def _alphabet_keys(name: str) -> set[str]:
    """The spellings a name may be filed under: its surname as one word, each
    word of it ("Ursinus v.Bär" under B, "DesVignoles" under V), and the name
    after "gen." ("Sinold, J.Fr. gen.Schütz" under Sch)."""
    surname = re.sub(r"\([^)]*\)", " ", name.split(",", 1)[0])
    words = [w for w in _RUNS.findall(_CAMEL.sub(" ", surname)) if not w.isdigit()]
    keys = _spellings(words)
    for word in [*words, *_GENANNT.findall(name)]:
        if len(word) > 2 and word.casefold() not in _PARTICLES:
            keys |= _spellings([word])
    return keys


def _initials(keys: Iterable[str]) -> set[str]:
    """First letters, C and K as one (Crafft is filed as Krafft)."""
    letters = {key[0] for key in keys}
    return letters | {"c", "k"} if letters & {"c", "k"} else letters


def _heaviest_chain(elements: list[list[tuple[str, float, str]]]) -> list[tuple[str, str] | None]:
    """Per element at most one of its options ``(key, weight, name)``, chosen so
    that the keys never decrease down the list and the weights sum highest;
    returns ``(name, key)`` for the elements kept, ``None`` for those left out."""
    keys = sorted({key for options in elements for key, _, _ in options})
    rank = {key: i + 1 for i, key in enumerate(keys)}
    best: list[tuple[float, int]] = [(0.0, -1)] * (len(keys) + 1)  # Fenwick tree, prefix maxima
    steps: list[tuple[int, str, str, int]] = []  # (element, name, key, previous step)

    def upto(r: int) -> tuple[float, int]:
        found = (0.0, -1)
        while r > 0:
            found = max(found, best[r])
            r -= r & -r
        return found

    for i, options in enumerate(elements):
        reached = [(key, name, upto(rank[key]), weight) for key, weight, name in options]
        for key, name, (total, previous), weight in reached:  # after every query: one per element
            steps.append((i, name, key, previous))
            r, value = rank[key], (total + weight, len(steps) - 1)
            while r <= len(keys):
                best[r] = max(best[r], value)
                r += r & -r
    chosen: list[tuple[str, str] | None] = [None] * len(elements)
    at = upto(len(keys))[1]
    while at != -1:
        i, name, key, at = steps[at]
        chosen[i] = (name, key)
    return chosen


def names_in_order(candidates: Sequence[Mapping[str, int]]) -> list[str | None]:
    """One name per convolute of the numbered run, or ``None``.

    ``candidates`` are the convolutes in shelfmark order, each with its
    :func:`correspondent_weights`. Kept is the longest run of names that stays
    alphabetical down the numbers (more records, then the earlier mention,
    break ties), so a convolute's lesser name wins where its most frequent one
    is out of place: LBr. 16 reads Arnauld, not the landgrave who forwarded
    his letters. A most frequent name outside that run is shown all the same
    when at least :data:`RESCUE_RECORDS` records carry it and its initial fits
    between its neighbours' — the catalogue spells some names otherwise than
    the shelf does (Chuno / Cuneau, Crafft / Krafft). Everything else stays
    unnamed: a missing name is honest, a wrong one is not.
    """
    elements = [
        [
            (key, 1 + min(n, 99) / 100 - order / 1e6, name)
            for order, (name, n) in enumerate(weights.items())
            for key in sorted(_alphabet_keys(name))
        ]
        for weights in candidates
    ]
    chain = _heaviest_chain(elements)
    out: list[str | None] = [kept[0] if kept else None for kept in chain]
    anchors = [(i, kept[1][0]) for i, kept in enumerate(chain) if kept]
    for i, weights in enumerate(candidates):
        top = max(weights, key=weights.__getitem__) if weights else None
        if top is None or top == out[i] or weights[top] < RESCUE_RECORDS:
            continue
        low = max((letter for at, letter in anchors if at < i), default="a")
        high = min((letter for at, letter in anchors if at > i), default="z")
        if any(low <= letter <= high for letter in _initials(_alphabet_keys(top))):
            out[i] = top
    return out


def _lbr_section(
    placed: list[tuple[_Placed, Work]],
    correspondents: Mapping[str, Sequence[Correspondence]],
    with_records: Collection[str],
) -> Section:
    numbered = sorted(placed, key=lambda it: (it[0].order, it[1].gwlb_object_id))
    weights = [correspondent_weights(correspondents.get(w.gwlb_object_id, ())) for _, w in numbered]
    # The plain numbers (1 … 1028, with 33a and "57, 1") are the alphabetical
    # run. The F series, the princes by house and first name, has no one order
    # to hold a name against: it keeps its most frequent name, and a name that
    # would label two of its convolutes stays with the one that has more records.
    names: list[str | None] = [max(w, key=w.__getitem__) if w else None for w in weights]
    in_run = [i for i, (place, _) in enumerate(numbered) if place.order and place.order[0][0] == 0]
    for i, name in zip(in_run, names_in_order([weights[i] for i in in_run]), strict=True):
        names[i] = name
    home: dict[str, int] = {}
    for i in sorted(set(range(len(numbered))) - set(in_run)):
        name = names[i]
        if name is None:
            continue
        rival = home.get(name)
        if rival is None or weights[i][name] > weights[rival][name]:
            home[name] = i
            if rival is not None:
                names[rival] = None
        else:
            names[i] = None
    named: list[Entry] = []
    unnamed: list[Entry] = []
    for (place, work), name in zip(numbered, names, strict=True):
        entry = _entry(work, place.mark, name or place.mark, with_records)
        (named if name else unnamed).append(entry)
    order = {entry.work_id: i for i, entry in enumerate(named)}
    named.sort(key=lambda e: (_fold(e.label), order[e.work_id]))
    return Section(
        "LBr",
        "LBr",
        "lbr",
        FAMILY_NAMES["LBr"],
        named + unnamed,
        by_number=[work.gwlb_object_id for _, work in numbered],
    )


# ---- the tree ------------------------------------------------------------------ #


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def _other_sections(works: list[Work], with_records: Collection[str]) -> list[Section]:
    by_set: dict[str, list[Work]] = {}
    for work in works:
        by_set.setdefault(work.set_name, []).append(work)
    sections = []
    for set_name, members in by_set.items():
        entries = []
        for work in members:
            marks = [" ".join(str(m).split()) for m in work.shelfmarks or ()]
            mark = marks[0] if marks else ""
            label = truncate(work.title or "") or mark or work.gwlb_object_id
            entries.append(_entry(work, mark, label, with_records))
        # by shelfmark string; the works without one last, by title
        entries.sort(
            key=lambda e: (not e.shelfmark, natural_key(e.shelfmark), _fold(e.title), e.work_id)
        )
        label = SET_LABELS.get(set_name, set_name)
        sections.append(Section("Other", set_name, f"other-{_slug(set_name)}", label, entries))
    return sorted(sections, key=lambda s: _fold(s.label))


def build_index(
    works: Iterable[Work],
    correspondents: Mapping[str, Sequence[Correspondence]] | None = None,
    with_records: Collection[str] = (),
) -> list[Family]:
    """The tree family → section → entries; every work lands in exactly one entry.

    ``correspondents`` maps a work id to its :class:`Correspondence` rows
    (:data:`CORRESPONDENTS_SQL`); ``with_records`` is the ids of the works with
    any catalogue record. Families and sections without works are left out.
    """
    with_records = frozenset(with_records)
    placed: dict[str, list[tuple[_Placed, Work]]] = {"LH": [], "LBr": [], "Marg": []}
    other: list[Work] = []
    for work in works:
        place = _place(work)
        if place is None:
            other.append(work)
        else:
            placed[place.family].append((place, work))

    families = []
    if placed["LH"]:
        families.append(Family("LH", _lh_sections(placed["LH"], with_records)))
    if placed["LBr"]:
        families.append(
            Family("LBr", [_lbr_section(placed["LBr"], correspondents or {}, with_records)])
        )
    if placed["Marg"]:
        items = sorted(placed["Marg"], key=lambda it: (it[0].order, it[1].gwlb_object_id))
        entries = [
            _entry(work, place.mark, truncate(work.title or "") or place.mark, with_records)
            for place, work in items
        ]
        families.append(
            Family("Marg", [Section("Marg", "Marg", "marg", FAMILY_NAMES["Marg"], entries)])
        )
    if other:
        families.append(Family("Other", _other_sections(other, with_records)))
    return families


def group_correspondents(rows: Iterable[Mapping]) -> dict[str, list[Correspondence]]:
    """The rows of :data:`CORRESPONDENTS_SQL` (or of its JSON export), by work id."""
    out: dict[str, list[Correspondence]] = {}
    for row in rows:
        out.setdefault(row["work_id"], []).append(
            Correspondence(row["absender"], row["adressat"], row["n_records"] or 1, row["titel"])
        )
    return out


def select(
    families: Iterable[Family], *, set_name: str | None = None, family: str | None = None
) -> list[Family]:
    """The tree narrowed to one OAI set and/or one family; what empties is dropped."""
    out = []
    for fam in families:
        if family is not None and fam.key != family:
            continue
        sections = []
        for section in fam.sections:
            entries = [e for e in section.entries if set_name is None or e.set_name == set_name]
            if not entries:
                continue
            kept = {e.work_id for e in entries}
            by_number = section.by_number and [w for w in section.by_number if w in kept]
            sections.append(replace(section, entries=entries, by_number=by_number))
        if sections:
            out.append(Family(fam.key, sections))
    return out


# ---- the shapes the API serves ------------------------------------------------- #


def rows(families: Iterable[Family]) -> list[dict]:
    """One compact row per work, ordered by work id."""
    out = [
        {
            "work_id": entry.work_id,
            "set": entry.set_name,
            "title": entry.title,
            "shelfmark": entry.shelfmark,
            "shelfmarks": list(entry.shelfmarks),
            "family": fam.key,
            "section": section.key,
            "section_label": section.label,
            "label": entry.label,
            "n_canvases": entry.n_canvases,
            "has_katalog": entry.has_katalog,
        }
        for fam in families
        for section in fam.sections
        for entry in section.entries
    ]
    return sorted(out, key=lambda row: row["work_id"])


def tree(families: Iterable[Family]) -> list[dict]:
    """The groups as JSON: sections with their anchors and counts, and the work
    ids of their entries in order (the rows carry the rest)."""
    out = []
    for fam in families:
        sections = []
        for section in fam.sections:
            node = {
                "section": section.key,
                "anchor": section.anchor,
                "label": section.label,
                "title": section.title,
                "n_works": section.n_works,
                "n_pages": section.n_pages,
                "entries": [entry.work_id for entry in section.entries],
            }
            if section.by_number is not None:
                node["by_number"] = list(section.by_number)
            sections.append(node)
        out.append(
            {
                "family": fam.key,
                "name": fam.name,
                "n_works": fam.n_works,
                "n_pages": fam.n_pages,
                "sections": sections,
            }
        )
    return out


def places(families: Iterable[Family]) -> dict[str, dict]:
    """work id → where it sits (family, section, anchor, the section's title),
    for a work page's way back into the index."""
    return {
        entry.work_id: {
            "family": fam.key,
            "section": section.key,
            "anchor": section.anchor,
            "label": section.label,
            "title": section.title,
        }
        for fam in families
        for section in fam.sections
        for entry in section.entries
    }


__all__ = [
    "CORRESPONDENTS_SQL",
    "FAMILIES",
    "FAMILY_NAMES",
    "RESCUE_RECORDS",
    "SET_LABELS",
    "Correspondence",
    "Entry",
    "Family",
    "Section",
    "build_index",
    "correspondent",
    "correspondent_names",
    "correspondent_weights",
    "group_correspondents",
    "names_as_written",
    "names_in_order",
    "natural_key",
    "places",
    "rows",
    "section_phrase",
    "select",
    "tree",
    "truncate",
]
