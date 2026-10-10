"""Leibniz's letters by correspondent, date and place (2026-10).

The letter convolutes are numbered as Eduard Bodemann catalogued them in 1889
(*Der Briefwechsel des Gottfried Wilhelm Leibniz in der Königlichen
Öffentlichen Bibliothek zu Hannover*): ``LBr. 16`` is his No. 16, Arnauld, and
the princes' series ``LBr. F`` his sections of the princely houses. The
correspSearch service of the BBAW publishes that catalogue letter by letter —
sender, addressee, date and place, people by GND, places by GeoNames — under
CC BY 4.0, keyed by Bodemann's numbers: ``16.2`` is the second letter of
No. 16, ``I.6.1`` the first of ``LBr. F 6`` (section I), and a bare ``230`` a
convolute of one letter.

:func:`harvest` pages through the correspSearch API (ten letters a page, one
request a second, every page cached on disk so a run resumes), :func:`parse_tei`
reads a page, and :class:`LettersIndex` is the file the web application reads:
the letters, each filed under the shelfmark key of its convolute
(:func:`leibniz.catalog.shelfmarks.signature_key`), and per convolute who wrote,
when and from where. Nothing here touches the store.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lxml import etree

from leibniz.catalog.shelfmarks import signature_key

API = "https://correspsearch.net/api/v2.0/tei-xml.xql"
BODEMANN = "uuid-12d4f84d-302d-4a6a-b3c2-362e4c6f9207"  # correspSearch's id of the 1889 catalogue
LEIBNIZ_GND = "http://d-nb.info/gnd/118571249"
FORMAT_VERSION = 1
LETTERS_ENV = "LEIBNIZ_LETTERS_PATH"
SOURCE = {
    "name": "correspSearch",
    "url": "https://correspsearch.net/",
    "publisher": "Berlin-Brandenburgische Akademie der Wissenschaften",
    "provider": "Portal Der deutsche Brief im 18. Jahrhundert",
    "edition": (
        "Eduard Bodemann, Der Briefwechsel des Gottfried Wilhelm Leibniz in der Königlichen "
        "Öffentlichen Bibliothek zu Hannover, Hannover 1889"
    ),
    "licence": "CC BY 4.0",
    "licence_url": "https://creativecommons.org/licenses/by/4.0/",
}

TEI = "{http://www.tei-c.org/ns/1.0}"
_NS = {"t": "http://www.tei-c.org/ns/1.0"}
_HITS = re.compile(r"of\s+([\d,.]+)\s+hits")
# Bodemann's numbers: "16.2", "33a.1", "230" (a convolute of one letter), and the
# princely houses' "I.6.1" (section I, LBr. F 6, letter 1).
_PLAIN = re.compile(r"^(?P<num>\d+[a-z]?)(?:\.(?P<letter>\d+[a-z]?))?$")
_PRINCES = re.compile(r"^(?P<section>[IVX]+)\.(?P<num>\d+[a-z]?)(?:\.(?P<letter>\d+[a-z]?))?$")


@dataclass(frozen=True, slots=True)
class Party:
    name: str
    ref: str | None = None  # GND URI

    @property
    def is_leibniz(self) -> bool:
        return self.ref == LEIBNIZ_GND or (self.ref is None and self.name.startswith("Leibniz"))


@dataclass(frozen=True, slots=True)
class Place:
    name: str
    ref: str | None = None  # GeoNames URI


@dataclass(slots=True)
class Letter:
    """One letter as Bodemann lists it."""

    key: str  # Bodemann's number: "16.2", "I.6.1", "230"
    convolute: str | None  # the shelfmark key of its convolute: "LBr 16", "LBr f,6"
    senders: list[Party] = field(default_factory=list)
    addressees: list[Party] = field(default_factory=list)
    place: Place | None = None  # where it was written
    to_place: Place | None = None  # where it was received, where given
    when: str | None = None  # an exact day, ISO
    not_before: str | None = None
    not_after: str | None = None
    date_text: str | None = None  # as the catalogue gives it ("1697. 98")

    @property
    def year_from(self) -> int | None:
        return _year(self.when or self.not_before or self.not_after)

    @property
    def year_to(self) -> int | None:
        return _year(self.when or self.not_after or self.not_before)

    @property
    def correspondents(self) -> list[Party]:
        """The people on the letter other than Leibniz."""
        return [p for p in (*self.senders, *self.addressees) if not p.is_leibniz]

    @property
    def direction(self) -> str:
        """``"to"`` Leibniz, ``"from"`` him, or ``"other"`` (a letter in his
        papers between others)."""
        if any(p.is_leibniz for p in self.addressees):
            return "to"
        if any(p.is_leibniz for p in self.senders):
            return "from"
        return "other"

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, [], "")}

    @classmethod
    def from_dict(cls, raw: Mapping) -> Letter:
        def parties(items: object) -> list[Party]:
            return [Party(str(p["name"]), p.get("ref")) for p in items or []]  # type: ignore[union-attr]

        def place(item: Mapping | None) -> Place | None:
            return Place(str(item["name"]), item.get("ref")) if item else None

        return cls(
            key=str(raw["key"]),
            convolute=raw.get("convolute"),
            senders=parties(raw.get("senders")),
            addressees=parties(raw.get("addressees")),
            place=place(raw.get("place")),
            to_place=place(raw.get("to_place")),
            when=raw.get("when"),
            not_before=raw.get("not_before"),
            not_after=raw.get("not_after"),
            date_text=raw.get("date_text"),
        )


def _year(iso: str | None) -> int | None:
    m = re.match(r"^(\d{4})", iso or "")
    return int(m.group(1)) if m else None


def convolute_of(key: str) -> str | None:
    """The shelfmark key of the convolute a Bodemann number belongs to:
    ``"16.2"`` → ``"LBr 16"``, ``"I.6.1"`` → ``"LBr f,6"``; ``None`` for a
    number of another shape."""
    text = (key or "").strip()
    m = _PRINCES.match(text)
    if m is not None:
        return signature_key(f"LBr. F {m.group('num')}")
    m = _PLAIN.match(text)
    if m is not None:
        return signature_key(f"LBr. {m.group('num')}")
    return None


# ---- the API ------------------------------------------------------------------- #


def page_url(page: int, *, edition: str = BODEMANN) -> str:
    return f"{API}?e={edition}&x={page}"


def total_hits(xml: bytes | str) -> int | None:
    """The number of letters the API reports ("1-10 of 15439 hits")."""
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    for note in root.iterfind(".//t:notesStmt/t:note", _NS):
        m = _HITS.search(note.text or "")
        if m:
            return int(re.sub(r"[,.]", "", m.group(1)))
    return None


def _party(el: etree._Element) -> Party | None:
    name = " ".join((el.text or "").split())
    if not name:
        return None
    ref = (el.get("ref") or "").strip() or None
    return Party(name, ref)


def _place(el: etree._Element | None) -> Place | None:
    if el is None:
        return None
    name = " ".join((el.text or "").split())
    if not name:
        return None
    return Place(name, (el.get("ref") or "").strip() or None)


def parse_tei(xml: bytes | str) -> list[Letter]:
    """The letters of one API page."""
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    out: list[Letter] = []
    for desc in root.iterfind(".//t:correspDesc", _NS):
        key = (desc.get("key") or "").strip()
        if not key:
            continue
        letter = Letter(key=key, convolute=convolute_of(key))
        for action in desc.iterfind("t:correspAction", _NS):
            kind = action.get("type")
            people = [p for el in action.iterfind("t:persName", _NS) if (p := _party(el))]
            people += [p for el in action.iterfind("t:orgName", _NS) if (p := _party(el))]
            place = _place(action.find("t:placeName", _NS))
            date = action.find("t:date", _NS)
            if kind == "sent":
                letter.senders.extend(people)
                letter.place = letter.place or place
                if date is not None:
                    letter.when = date.get("when") or letter.when
                    letter.not_before = (
                        date.get("notBefore") or date.get("from") or letter.not_before
                    )
                    letter.not_after = date.get("notAfter") or date.get("to") or letter.not_after
                    letter.date_text = " ".join((date.text or "").split()) or letter.date_text
            elif kind == "received":
                letter.addressees.extend(people)
                letter.to_place = letter.to_place or place
        out.append(letter)
    return out


def harvest(
    get: Callable[[str], bytes],
    cache_dir: str | Path,
    *,
    edition: str = BODEMANN,
    progress: Callable[[int, int], None] | None = None,
) -> list[Letter]:
    """Every letter of ``edition``, page by page. Pages already in ``cache_dir``
    are read from there, so an interrupted run resumes where it stopped; ``get``
    fetches one URL (the project's polite client: one request a second)."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)

    def page(n: int) -> bytes:
        path = cache / f"page-{n:05d}.xml"
        if path.exists() and path.stat().st_size:
            return path.read_bytes()
        data = get(page_url(n, edition=edition))
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
        return data

    first = page(1)
    total = total_hits(first) or 0
    per_page = max(1, len(parse_tei(first)))
    n_pages = max(1, -(-total // per_page))
    letters: list[Letter] = []
    for n in range(1, n_pages + 1):
        found = parse_tei(first if n == 1 else page(n))
        letters.extend(found)
        if progress is not None:
            progress(n, n_pages)
        if not found and n > 1:
            break
    seen: set[str] = set()
    unique = []
    for letter in letters:  # a page boundary that shifted while paging repeats a letter
        if letter.key not in seen:
            seen.add(letter.key)
            unique.append(letter)
    return unique


# ---- per convolute ------------------------------------------------------------- #


def fold(text: str) -> str:
    """Case- and accent-blind, for matching names and places as typed."""
    plain = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in plain if not unicodedata.combining(c)).casefold()


@dataclass(slots=True)
class Convolute:
    """What Bodemann's letters say about one convolute."""

    key: str
    n_letters: int = 0
    correspondents: list[tuple[Party, int]] = field(default_factory=list)
    places: list[tuple[Place, int]] = field(default_factory=list)
    year_from: int | None = None
    year_to: int | None = None

    @property
    def correspondent(self) -> Party | None:
        """The person on most of the letters beside Leibniz."""
        return self.correspondents[0][0] if self.correspondents else None

    def to_dict(self, *, places: int = 8) -> dict:
        lead = self.correspondent
        return {
            "n_letters": self.n_letters,
            "correspondent": asdict(lead) if lead else None,
            "correspondents": [{**asdict(p), "n": n} for p, n in self.correspondents[:places]],
            "years": [self.year_from, self.year_to] if self.year_from else None,
            "places": [{**asdict(p), "n": n} for p, n in self.places[:places]],
        }


def summarize(letters: Iterable[Letter]) -> dict[str, Convolute]:
    """Per convolute key: its letters' people, places and years."""
    people: dict[str, Counter[Party]] = {}
    spots: dict[str, Counter[Place]] = {}
    out: dict[str, Convolute] = {}
    for letter in letters:
        if letter.convolute is None:
            continue
        conv = out.setdefault(letter.convolute, Convolute(letter.convolute))
        conv.n_letters += 1
        people.setdefault(conv.key, Counter()).update(letter.correspondents)
        if letter.place is not None:
            spots.setdefault(conv.key, Counter()).update([letter.place])
        for year in (letter.year_from, letter.year_to):
            if year is None:
                continue
            conv.year_from = year if conv.year_from is None else min(conv.year_from, year)
            conv.year_to = year if conv.year_to is None else max(conv.year_to, year)
    for key, conv in out.items():
        order = people.get(key, Counter())
        conv.correspondents = sorted(order.items(), key=lambda kv: (-kv[1], kv[0].name))
        where = spots.get(key, Counter())
        conv.places = sorted(where.items(), key=lambda kv: (-kv[1], kv[0].name))
    return out


# ---- the file the web application reads ------------------------------------------ #


@dataclass(frozen=True, slots=True)
class LetterQuery:
    who: str = ""  # a correspondent's name, any part of it
    place: str = ""
    year_from: int | None = None
    year_to: int | None = None
    direction: str = ""  # "to" | "from" | ""
    convolutes: tuple[str, ...] = ()  # shelfmark keys


class LettersIndex:
    """The letters by convolute, as the web application consults them; empty
    where no file was written."""

    def __init__(
        self, letters: Iterable[Letter] = (), built_at: str = "", source: Mapping | None = None
    ) -> None:
        self.letters = sorted(letters, key=_order)
        self.built_at = built_at
        self.source = dict(source or SOURCE)
        self.by_convolute: dict[str, list[Letter]] = {}
        for letter in self.letters:
            if letter.convolute:
                self.by_convolute.setdefault(letter.convolute, []).append(letter)
        self.convolutes = summarize(self.letters)

    def __bool__(self) -> bool:
        return bool(self.letters)

    def keys_for(self, shelfmark_keys: Iterable[str]) -> list[str]:
        """The convolute keys a work's shelfmarks name: its own, and for a part of
        a convolute (``LBr 57,1``) the convolute's (``LBr 57``)."""
        out: list[str] = []
        for key in shelfmark_keys:
            for candidate in (key, key.split(",", 1)[0] if key.startswith("LBr ") else key):
                if candidate in self.by_convolute and candidate not in out:
                    out.append(candidate)
        return out

    def search(self, q: LetterQuery) -> list[Letter]:
        who, where = fold(q.who).strip(), fold(q.place).strip()
        pool: Sequence[Letter] = (
            [ltr for key in q.convolutes for ltr in self.by_convolute.get(key, [])]
            if q.convolutes
            else self.letters
        )
        out = []
        for letter in pool:
            if who and not any(who in fold(p.name) for p in letter.correspondents):
                continue
            if where and not any(
                where in fold(p.name) for p in (letter.place, letter.to_place) if p is not None
            ):
                continue
            if q.year_from is not None and (letter.year_to or 0) < q.year_from:
                continue
            if q.year_to is not None and (letter.year_from or 9999) > q.year_to:
                continue
            if q.direction and letter.direction != q.direction:
                continue
            out.append(letter)
        return sorted(out, key=_order) if q.convolutes else out

    def to_dict(self) -> dict:
        return {
            "version": FORMAT_VERSION,
            "built_at": self.built_at,
            "source": self.source,
            "letters": [ltr.to_dict() for ltr in self.letters],
        }

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        return path

    @classmethod
    def load(cls, path: str | Path | None) -> LettersIndex:
        if path is None:
            return cls()
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(raw, dict) or raw.get("version") != FORMAT_VERSION:
            return cls()
        letters = [Letter.from_dict(x) for x in raw.get("letters") or []]
        return cls(letters, str(raw.get("built_at") or ""), raw.get("source"))


def _order(letter: Letter) -> tuple:
    """By date (undated last), then by Bodemann's number."""
    year = letter.year_from
    parts = tuple(
        (0, int(p), "") if p.isdigit() else (1, 0, p) for p in re.split(r"[.]", letter.key)
    )
    return (year is None, year or 0, letter.when or letter.not_before or "", parts)


def letters_path_for(db_path: str | Path) -> Path:
    """Where the letters file sits unless ``LEIBNIZ_LETTERS_PATH`` says otherwise:
    beside the store."""
    explicit = os.environ.get(LETTERS_ENV)
    if explicit:
        return Path(explicit)
    return Path(db_path).parent / "letters.json"


def built_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


__all__ = [
    "API",
    "BODEMANN",
    "LEIBNIZ_GND",
    "LETTERS_ENV",
    "SOURCE",
    "Convolute",
    "Letter",
    "LetterQuery",
    "LettersIndex",
    "Party",
    "Place",
    "built_now",
    "convolute_of",
    "fold",
    "harvest",
    "letters_path_for",
    "page_url",
    "parse_tei",
    "summarize",
    "total_hits",
]
