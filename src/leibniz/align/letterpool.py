"""The GWLB letter pool: fetch the checked volumes and parse them into letters (K2b, Task 1).

The Leibniz-Archiv of the GWLB publishes *Transkriptionen des
Leibniz-Briefwechsels <year> für die Leibniz-Akademie-Ausgabe*, one PDF a
year, checked ("überprüft") for 1708 to 1716 — transcriptions made from the
originals for the edition, independently of every model in this project. They
are the honest German test set: selected by no reader, from years the
§70-expired volumes do not reach.

**The licence rule (SPECS §1.4, §7.3).** The pool is CC BY-NC 4.0: nc-bucket
material, read for internal evaluation under the TDM rules and nothing else —
never on the website, never in a release, never in a committed file, never in
training, never for choosing a checkpoint. The PDFs live under
``data/external/letterpool/`` and everything extracted from them under
``data/kurrent/letterpool/`` (both gitignored); the committed sources file
carries versions, dates, checksums and the citation each volume asks for, and
the reports carry numbers, letter numbers and shelfmarks only.

Two halves live here. The **fetch**: the year's repository page names the
newest version of its PDF, which is downloaded politely, cache-first, and
recorded with its SHA-256 in ``reports/kurrent/letterpool-sources.json``. The
**parser**: pdfplumber gives every character's size and position; the volumes
are set with EDMAC like the Academy edition, so a handful of layout rules
recover each letter — its number and heading (``2. GEORG LUDEWIG RÖMELING AN
LEIBNIZ``, set in capitals), the editorial dateline under it, the small-type
*Überlieferung* block naming the witness (its siglum, kind, shelfmark and
leaves), and the reading text in body type — while the running head, the
margin line numbers (every fifth typeset line, outside the text block) and
the notes at the page foot are dropped. The text layer decomposes umlauts, so
everything is NFC first. Editorial square brackets go the way the C2b flags
describe them: a supplied letter or mark keeps its content (``salutare[s]`` →
``salutares``), a bracketed insertion that stands on its own (an identified
name, a reference) is not on the page and goes entirely.
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz.align.edition import join_lines
from leibniz.catalog.shelfmarks import Signature, normalize_signature
from leibniz.enrich.langid import classify
from leibniz.net import PoliteClient

CHECKED_YEARS: tuple[int, ...] = tuple(range(1708, 1717))
BASE_URL = "https://www.gwlb.de"
PAGE_URL = (
    BASE_URL
    + "/leibniz/digitale-ressourcen/repositorium-des-leibniz-archivs/laa-transkriptionen-{year}"
)
LICENCE = "CC BY-NC 4.0"
LICENCE_BUCKET = "nc"
DEFAULT_POOL_DIR = Path("data/external/letterpool")
DEFAULT_SOURCES = Path("reports/kurrent/letterpool-sources.json")
DEFAULT_LETTERS_DIR = Path("data/kurrent/letterpool")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")

# The GWLB's Leibniz collections: a witness there can be placed on the store's
# scans (Task 2); any other holding cannot.
PLACEABLE_FAMILIES: frozenset[str] = frozenset({"LBr", "LH", "LK", "Marg"})

# --------------------------------------------------------------------------- #
# The fetch
# --------------------------------------------------------------------------- #

_PDF_RE = re.compile(
    r"(/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen(\d{4})-v(\d+)\.pdf)"
)
_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}
_DATE_RE = re.compile(r"(\d{1,2})\.\s*([A-Za-zäöü]+)\s*(\d{4})")


def german_date(text: str) -> str | None:
    """``"3. November 2020"`` → ``"2020-11-03"``; ``None`` if no date is found."""
    m = _DATE_RE.search(text or "")
    if m is None:
        return None
    month = _MONTHS.get(m.group(2).lower())
    if month is None:
        return None
    return date(int(m.group(3)), month, int(m.group(1))).isoformat()


def _plain(html_text: str) -> str:
    """The page's text with the tags gone and the whitespace collapsed."""
    import html as html_lib

    text = re.sub(r"<[^>]+>", " ", html_text)
    return " ".join(html_lib.unescape(text).split())


@dataclass(slots=True)
class VolumeInfo:
    """What a year's repository page says about its newest PDF."""

    year: int
    version: int
    url: str
    page_url: str
    title: str
    published: str | None  # ISO date (Erscheinungsdatum)
    citation: str  # the Zitierhinweis, as the page prints it
    bibkey: str | None
    size_note: str | None  # "2.97 MB", as the page prints it
    licence: str


def parse_year_page(html_text: str, year: int, *, page_url: str | None = None) -> VolumeInfo:
    """The newest ``LAA-Transkriptionen<year>-v<N>.pdf`` and the page's metadata.

    Raises :class:`ValueError` when the page names no PDF for the year.
    """
    found = [(int(v), path) for path, y, v in _PDF_RE.findall(html_text) if int(y) == year]
    if not found:
        raise ValueError(f"no LAA-Transkriptionen{year}-v<N>.pdf link on the page")
    version, path = max(found)
    text = _plain(html_text)
    title_m = re.search(
        rf"(Transkriptionen des Leibniz-Briefwechsels {year} für die Leibniz-Akademie-Ausgabe"
        r"(?: \([^)]*\))?)",
        text,
    )
    title = title_m.group(1) if title_m else f"Transkriptionen des Leibniz-Briefwechsels {year}"
    pub_m = re.search(r"Erscheinungsdatum:\s*(.{0,40}?)\s+Download", text)
    published = german_date(pub_m.group(1)) if pub_m else None
    cit_m = re.search(r"Bibliographische Angaben\s+(.{0,600}?)\s+BibLaTeX", text)
    citation = cit_m.group(1).strip() if cit_m else title
    key_m = re.search(r"@Online\{([^,\s]+),", html_text)
    size_m = re.search(r"Dokument \(\.PDF,\s*([\d.,]+\s*[KMG]B)\)", text)
    lic_m = re.search(r"\((CC BY[^)]*)\)", text)
    return VolumeInfo(
        year=year,
        version=version,
        url=BASE_URL + path,
        page_url=page_url or PAGE_URL.format(year=year),
        title=title,
        published=published,
        citation=citation,
        bibkey=key_m.group(1) if key_m else None,
        size_note=size_m.group(1) if size_m else None,
        licence=lic_m.group(1) if lic_m else LICENCE,
    )


@dataclass(slots=True)
class VolumeSource:
    """One fetched volume, as recorded in ``letterpool-sources.json`` (no text)."""

    year: int
    version: int
    title: str
    published: str | None
    url: str
    page_url: str
    file: str  # path relative to the repository root
    bytes: int
    sha256: str
    n_pages: int | None
    citation: str
    bibkey: str | None
    licence: str
    fetched: str  # ISO date of the download (or of the verification)

    @property
    def path(self) -> Path:
        return Path(self.file)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_page_count(path: Path) -> int | None:
    """The PDF's page count through pdfplumber; ``None`` without the ``gt`` extra."""
    try:
        import pdfplumber
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return None
    with pdfplumber.open(str(path)) as pdf:
        return len(pdf.pages)


def load_sources(path: Path | str = DEFAULT_SOURCES) -> list[VolumeSource]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [VolumeSource(**row) for row in data.get("volumes", [])]


def write_sources(sources: Sequence[VolumeSource], path: Path | str = DEFAULT_SOURCES) -> Path:
    """The committed registry: versions, dates, checksums, citations — no text."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "what": (
            "The GWLB Leibniz-Archiv's checked transcriptions of the Leibniz correspondence "
            "(Transkriptionen des Leibniz-Briefwechsels <year> für die "
            "Leibniz-Akademie-Ausgabe, überprüft), the K2b test set's source. One PDF a year, "
            "the newest version the year's repository page names."
        ),
        "licence": LICENCE,
        "licence_bucket": LICENCE_BUCKET,
        "use": (
            "internal evaluation only (SPECS §1.4 and §7.3, TDM): never on the website, never "
            "in a release, never in a committed file, never in training, never for choosing a "
            "checkpoint. The PDFs and everything extracted from them stay under data/ "
            "(gitignored)."
        ),
        "volumes": [asdict(s) for s in sorted(sources, key=lambda s: s.year)],
    }
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def fetch_volumes(
    years: Iterable[int] = CHECKED_YEARS,
    *,
    dest_dir: Path | str = DEFAULT_POOL_DIR,
    sources_path: Path | str = DEFAULT_SOURCES,
    client: PoliteClient | None = None,
    today: date | None = None,
    log: Callable[[str], None] | None = None,
) -> list[VolumeSource]:
    """Fetch the checked years' newest PDFs, cache-first, and record them.

    For each year the repository page is read (one polite request), the newest
    version's PDF is downloaded unless a file of that version already sits in
    ``dest_dir`` with the SHA-256 the registry recorded, and the registry row is
    rewritten with the checksum, the size, the page count and the citation.
    Years already recorded at the page's newest version are verified, not
    fetched again.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    known = {s.year: s for s in load_sources(sources_path)}
    owns = client is None
    client = client or PoliteClient()
    out: list[VolumeSource] = []
    stamp = (today or date.today()).isoformat()
    try:
        for year in years:
            page_url = PAGE_URL.format(year=year)
            info = parse_year_page(client.get_text(page_url), year, page_url=page_url)
            path = dest_dir / f"LAA-Transkriptionen{year}-v{info.version}.pdf"
            prior = known.get(year)
            if (
                path.exists()
                and prior is not None
                and prior.version == info.version
                and sha256_of(path) == prior.sha256
            ):
                if log:
                    log(f"{year}: v{info.version} already fetched and verified ({path})")
                src = VolumeSource(**asdict(prior))
            else:
                data = client.get_bytes(info.url)
                if not data.startswith(b"%PDF"):
                    raise ValueError(f"{info.url} did not return a PDF")
                tmp = path.with_suffix(".pdf.part")
                tmp.write_bytes(data)
                tmp.replace(path)
                src = VolumeSource(
                    year=year,
                    version=info.version,
                    title=info.title,
                    published=info.published,
                    url=info.url,
                    page_url=info.page_url,
                    file=str(path),
                    bytes=len(data),
                    sha256=sha256_of(path),
                    n_pages=pdf_page_count(path),
                    citation=info.citation,
                    bibkey=info.bibkey,
                    licence=info.licence,
                    fetched=stamp,
                )
                if log:
                    log(
                        f"{year}: v{info.version} fetched, {src.bytes:,} bytes, "
                        f"{src.n_pages} pages, sha256 {src.sha256[:12]}…"
                    )
            out.append(src)
    finally:
        if owns:
            client.close()
    write_sources(out, sources_path)
    return out


# --------------------------------------------------------------------------- #
# The page model and the PDF reader
# --------------------------------------------------------------------------- #

# Glyphs the text layer names by CID: the angle brackets of the maths font are
# kept (editorial remarks stand between them); the rest — integral signs, the
# odd astronomical symbol, letters of a Greek font — are dropped.
_CID_MAP = {"(cid:104)": "⟨", "(cid:105)": "⟩"}
_CID_RE = re.compile(r"\(cid:\d+\)")
# The text layer writes an umlaut as the base vowel followed by a spacing
# diaeresis (U+00A8), which NFC never composes: "U¨berlieferung".
_SPACING_DIAERESIS_RE = re.compile(r"([AEIOUYaeiouy])¨")
TOKEN_GAP = 3.0  # points of white between characters that separate two tokens


def clean_text(text: str) -> str:
    """NFC with the spacing diaeresis composed, the CID glyphs resolved, whitespace collapsed."""
    for cid, glyph in _CID_MAP.items():
        text = text.replace(cid, glyph)
    text = _CID_RE.sub("", text)
    text = _SPACING_DIAERESIS_RE.sub(lambda m: m.group(1) + "̈", text)
    return " ".join(unicodedata.normalize("NFC", text).split())


@dataclass(slots=True)
class PoolLine:
    """One typeset line: its text (NFC), box, type size, font and token edges.

    ``lead_x1`` is where the first token ends and ``tail_x0`` where the last one
    begins, so a margin line number glued to the line by the extractor can be
    told from the text by its position outside the text block.
    """

    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    size: float
    font: str
    lead_x1: float
    tail_x0: float
    italic: float = 0.0  # share of characters in an italic font

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    def as_row(self) -> list:
        return [
            self.text,
            round(self.x0, 1),
            round(self.x1, 1),
            round(self.top, 1),
            round(self.bottom, 1),
            self.size,
            self.font,
            round(self.lead_x1, 1),
            round(self.tail_x0, 1),
            round(self.italic, 3),
        ]

    @classmethod
    def from_row(cls, row: Sequence) -> PoolLine:
        return cls(*row)


@dataclass(slots=True)
class PoolPage:
    """All lines of one PDF page, in reading order."""

    index: int  # 0-based PDF page index
    width: float
    height: float
    lines: list[PoolLine] = field(default_factory=list)


def _font_family(name: str) -> str:
    return (name or "").split("+", 1)[-1]


def _token_edges(chars: Sequence[dict]) -> tuple[float, float]:
    """``(x1 of the first token, x0 of the last token)`` from a line's characters."""
    xs = [(float(c["x0"]), float(c["x1"])) for c in chars if str(c.get("text", "")).strip()]
    if not xs:
        return 0.0, 0.0
    xs.sort()
    lead_x1 = xs[-1][1]
    for (_a0, a1), (b0, _b1) in zip(xs, xs[1:], strict=False):
        if b0 - a1 > TOKEN_GAP:
            lead_x1 = a1
            break
    tail_x0 = xs[0][0]
    for (_a0, a1), (b0, _b1) in zip(xs, xs[1:], strict=False):
        if b0 - a1 > TOKEN_GAP:
            tail_x0 = b0
    return lead_x1, tail_x0


def iter_pdf_pages(path: str | Path, *, x_tolerance: float = 2.0) -> Iterator[PoolPage]:
    """Stream a volume's pages as :class:`PoolPage` (needs ``pdfplumber``)."""
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise ModuleNotFoundError("iter_pdf_pages needs pdfplumber (`uv sync --extra gt`)") from exc
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            lines: list[PoolLine] = []
            for ln in page.extract_text_lines(x_tolerance=x_tolerance, return_chars=True):
                text = clean_text(ln["text"])
                if not text:
                    continue
                chars = ln["chars"]
                sizes = Counter(round(float(c.get("size", 0.0)), 1) for c in chars)
                fonts = Counter(_font_family(c.get("fontname", "")) for c in chars)
                italic = sum(n for f, n in fonts.items() if "Italic" in f or "Oblique" in f)
                lead_x1, tail_x0 = _token_edges(chars)
                lines.append(
                    PoolLine(
                        text=text,
                        x0=float(ln["x0"]),
                        x1=float(ln["x1"]),
                        top=float(ln["top"]),
                        bottom=float(ln["bottom"]),
                        size=sizes.most_common(1)[0][0] if sizes else 0.0,
                        font=fonts.most_common(1)[0][0] if fonts else "",
                        lead_x1=lead_x1,
                        tail_x0=tail_x0,
                        italic=italic / max(1, len(chars)),
                    )
                )
            yield PoolPage(index=i, width=float(page.width), height=float(page.height), lines=lines)


def write_page_cache(pages: Iterable[PoolPage], path: str | Path) -> int:
    """The extracted pages as JSONL (under ``data/``, never committed); returns the count."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8") as fh:
        for pg in pages:
            row = {
                "i": pg.index,
                "w": round(pg.width, 2),
                "h": round(pg.height, 2),
                "lines": [ln.as_row() for ln in pg.lines],
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_page_cache(path: str | Path) -> list[PoolPage]:
    out: list[PoolPage] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        out.append(
            PoolPage(
                index=int(row["i"]),
                width=float(row["w"]),
                height=float(row["h"]),
                lines=[PoolLine.from_row(r) for r in row["lines"]],
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #

HEAD_ZONE = 0.09  # the running head sits above this fraction of the page height
SMALL_GAP = 0.8  # a line whose size is this many points under the body size is small type
MARGIN_SLACK = 3.0  # points outside the text block before a number is a margin number
DATELINE_WIDTH = 0.7  # a dateline is shorter than this share of the text block
NOTE_GAP = 1.4  # a gap this many pitches wide separates the notes at the foot
NOTE_RUN_MAX = 6  # a body-type note at the foot is at most this many lines


@dataclass(frozen=True, slots=True)
class PoolLayout:
    """A volume's learned geometry: type sizes, the text block, the leading."""

    body_size: float
    small_below: float  # size < small_below is small type (apparatus, Überlieferung)
    body_x0: float
    body_x1: float
    pitch: float

    def small(self, ln: PoolLine) -> bool:
        return ln.size < self.small_below

    @property
    def body_width(self) -> float:
        return self.body_x1 - self.body_x0


def _mode(counter: Counter) -> float | None:
    return float(counter.most_common(1)[0][0]) if counter else None


def learn_layout(pages: Sequence[PoolPage]) -> PoolLayout:
    """Type sizes and the text block, learned over the whole volume.

    The body size is the character-weighted mode over long lines; the text
    block's edges are the modes of the long body lines' ``x0`` and ``x1``; the
    pitch is the median gap between consecutive body lines.
    """
    sizes: Counter = Counter()
    for pg in pages:
        for ln in pg.lines:
            if len(ln.text) >= 20 and ln.size > 0:
                sizes[ln.size] += len(ln.text)
    body = _mode(sizes) or 12.0
    small_below = body - SMALL_GAP
    x0s: Counter = Counter()
    x1s: Counter = Counter()
    gaps: list[float] = []
    for pg in pages:
        body_lines = [
            ln
            for ln in pg.lines
            if ln.size >= small_below
            and ln.top > HEAD_ZONE * pg.height
            and ln.width > 0.6 * pg.width
        ]
        for ln in body_lines:
            x0s[round(ln.x0)] += 1
            x1s[round(ln.x1)] += 1
        tops = sorted(ln.top for ln in body_lines)
        gaps.extend(
            b - a for a, b in zip(tops, tops[1:], strict=False) if 0.5 * body < b - a < 2.5 * body
        )
    body_x0 = _mode(x0s) or 0.0
    body_x1 = _mode(x1s) or (max((ln.x1 for pg in pages for ln in pg.lines), default=0.0))
    pitch = statistics.median(gaps) if gaps else 1.4 * body
    return PoolLayout(body, small_below, body_x0, body_x1, pitch)


_DIGITS_RE = re.compile(r"^\d{1,3}$")


def strip_margin_number(ln: PoolLine, layout: PoolLayout) -> str:
    """The line's text without a margin line number glued to either end.

    EDMAC numbers every fifth typeset line in the outer margin; the extractor
    merges the number into the line it counts. A leading digit token ending
    left of the text block, or a trailing one beginning right of it, is that
    number and goes; a number inside the block is text.
    """
    toks = ln.text.split()
    if len(toks) >= 2 and _DIGITS_RE.match(toks[0]) and ln.lead_x1 < layout.body_x0 - MARGIN_SLACK:
        toks = toks[1:]
    if len(toks) >= 2 and _DIGITS_RE.match(toks[-1]) and ln.tail_x0 > layout.body_x1 + MARGIN_SLACK:
        toks = toks[:-1]
    if (
        len(toks) == 1
        and _DIGITS_RE.match(toks[0])
        and (
            ln.lead_x1 < layout.body_x0 - MARGIN_SLACK or ln.tail_x0 > layout.body_x1 + MARGIN_SLACK
        )
    ):
        return ""
    return " ".join(toks)


HEADING_RE = re.compile(r"^(\d{1,4})\.\s+(\S.*)$")
CAPS_SHARE = 0.6
_HEAD_NUM_RE = re.compile(r"\bN\.\s*(\d{1,4})\b")
_LOWER_RE = re.compile(r"[a-zäöüßéèàç]")
_YEAR_RE = re.compile(r"\b1[67]\d\d\b")
PENDING_MAX = 4  # body-size lines allowed between a heading and its Überlieferung block


def _caps_share(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    return sum(ch.isupper() for ch in letters) / len(letters) if len(letters) >= 4 else 0.0


def heading_match(text: str) -> tuple[str, str] | None:
    """``("2", "GEORG LUDEWIG RÖMELING AN LEIBNIZ")`` for a letter heading, else ``None``.

    A heading is the letter's number, a full stop and a title set in capitals;
    a table-of-contents entry (``2. Georg Ludewig Römeling an Leibniz … 4``)
    carries lowercase and never passes.
    """
    m = HEADING_RE.match(text.strip())
    if not m:
        return None
    title = m.group(2)
    if _caps_share(title) < CAPS_SHARE:
        return None
    return m.group(1), title


def is_caps_line(text: str) -> bool:
    """A wrapped heading's second line: capitals, no lowercase letter."""
    return _caps_share(text) >= CAPS_SHARE and not _LOWER_RE.search(text)


def head_number(head_small: str) -> str | None:
    """The letter number the running head names, from its small-type lines.

    EDMAC sets ``N.52`` at the outer edge: first on a verso (``N.40 … 49``),
    last on a recto (``… 15. November 1709 N.52``); a ``Beilage zu N. 47`` in
    the head's title is not the page's number.
    """
    m = re.match(r"N\.\s*(\d{1,4})\b", head_small) or re.search(r"N\.\s*(\d{1,4})\s*$", head_small)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
# Letters
# --------------------------------------------------------------------------- #

_UEBERLIEFERUNG_RE = re.compile(r"Überlieferung:\s*(.*)", re.DOTALL)
_WITNESS_RE = re.compile(r"^\s*([A-Za-z])(\d)?\s+(.*)$", re.DOTALL)
_KIND_RE = re.compile(
    r"^((?:[Vv]erworfene\s+)?(?:Abfertigung|Konzept|Teilkonzept|Abschrift|Teilabschrift|"
    r"Reinschrift|Auszug|Erstdruck|Teildruck|Druck|Nachdruck|Entwurf))\b\.?\s*"
)


def _split_kind(rest: str) -> tuple[str | None, str]:
    """``"Abfertigung: LBr.98 …"`` → ``("Abfertigung", "LBr.98 …")``; the kind may also
    stand without its colon (``"Abfertigung LBr.840 …"``) or be missing (``"LBr.234 …"``)."""
    head, sep, tail = rest.partition(":")
    if sep and len(head) <= 60 and not re.search(r"\bBl\b|\bLBr|\bLH\b|\bLK\b", head):
        return " ".join(head.split()) or None, tail.strip()
    km = _KIND_RE.match(rest)
    if km:
        return km.group(1), rest[km.end() :].strip()
    return None, rest.strip()


_BLATT_END_RE = re.compile(
    r"\bBl\.?\s*\d+\s*[a-z]?\s*[rv]?o?°?(?:\s*[-–]\s*\d+\s*[a-z]?\s*[rv]?o?°?)?", re.IGNORECASE
)
_SHARED_RE = re.compile(r"\bvon\s+N\.\s*\d+")
_PAREN_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")


@dataclass(slots=True)
class Witness:
    """The first witness of a letter's *Überlieferung* block."""

    siglum: str | None  # L, l, K, k, A, E, …
    kind: str | None  # Abfertigung, Konzept, Abschrift, …
    shelfmark: str | None  # as printed, up to the leaves ("LBr.98 (Bothmer) Bl.1–2")
    family: str | None  # LBr | LH | LK | Marg | None
    key: str | None  # the crosswalk's signature key ("LBr 98")
    blatt: str | None  # "1–2"
    shared: bool  # the block names a second text on the leaves ("Auf Bl.4vo L von N.69")
    shared_note: str | None
    label: str | None = (
        None  # the siglum with its number where several witnesses are printed ("L1")
    )

    @property
    def placeable(self) -> bool:
        return self.family in PLACEABLE_FAMILIES and self.blatt is not None


def _signature(shelfmark: str) -> Signature:
    """The shelfmark normalised with its parentheses and brackets gone (``LBr.98 (Bothmer)
    Bl.1–2``, ``LK-MOW Behrens10 [früher: LBr.46] Bl.352``: the A3 normaliser cuts at a
    parenthesis, which here sits before the leaves, and a bracket would enter the key)."""
    return normalize_signature(" ".join(_PAREN_RE.sub(" ", shelfmark).split()))


def parse_witness(block: str) -> Witness:
    """The first witness named by an *Überlieferung* block, and whether the leaves are shared."""
    none = Witness(None, None, None, None, None, None, False, None)
    m = _UEBERLIEFERUNG_RE.search(block or "")
    if m is None:
        return none
    rest = m.group(1).strip()
    w = _WITNESS_RE.match(rest)
    shared_m = _SHARED_RE.search(rest)
    shared_note = None
    if shared_m:
        lo = max(0, shared_m.start() - 40)
        shared_note = rest[lo : shared_m.end() + 10].strip()
    if w is None:
        return Witness(None, None, None, None, None, None, bool(shared_m), shared_note)
    siglum = w.group(1)
    kind, tail = _split_kind(w.group(3))
    bm = _BLATT_END_RE.search(tail)
    if bm:
        shelfmark = tail[: bm.end()].strip()
    else:
        shelfmark = re.split(r"\.\s", tail, maxsplit=1)[0].strip()
    sig = _signature(shelfmark)
    return Witness(
        siglum=siglum,
        kind=kind,
        shelfmark=shelfmark or None,
        family=sig.family,
        key=sig.key,
        blatt=sig.blatt,
        shared=bool(shared_m),
        shared_note=shared_note,
        label=siglum + (w.group(2) or ""),
    )


# A letter printed in several drafts carries each draft under its label on a
# line of its own: ⟨L1⟩ … ⟨L2⟩ …; only the first witness's draft is on its leaves.
_SEGMENT_RE = re.compile(r"^⟨([A-Za-z]\d?)⟩$")


def split_segments(lines: Sequence[str]) -> list[tuple[str | None, list[str]]]:
    """``[(label, lines), …]``: the text cut at its draft markers (one unlabelled
    segment when there are none)."""
    out: list[tuple[str | None, list[str]]] = []
    label: str | None = None
    cur: list[str] = []
    for line in lines:
        m = _SEGMENT_RE.match(line.strip())
        if m:
            if cur or label is not None:
                out.append((label, cur))
            label, cur = m.group(1), []
        else:
            cur.append(line)
    out.append((label, cur))
    return out


# A bracket group attached to a word (no space on at least one side) supplies a
# letter or a mark the scribe left out: the content stays, the brackets go. A
# group standing on its own is the editor's insertion — an identified name, a
# reference, a supplied word — and goes entirely; so does an angle-bracket
# group, the editor's remark on the manuscript ("⟨Darüber von Leibniz' Hand:⟩").
_ATTACHED_BRACKET_RE = re.compile(
    r"(?<=[^\s\[])\[([^\[\]\s]{1,6})\]|\[([^\[\]\s]{1,6})\](?=[^\s\]])"
)
_STANDALONE_BRACKET_RE = re.compile(r"\s?\[[^\[\]]*\]")
_ANGLE_RE = re.compile(r"\s?⟨[^⟨⟩]*⟩")


def strip_brackets(text: str) -> tuple[str, dict[str, int]]:
    """Editorial brackets resolved; returns the text and what was done.

    ``salutare[s]`` → ``salutares``; ``couvents[,]`` → ``couvents,``;
    ``Monsr de Ludolf [Georg Melchior von Ludolf]`` → ``Monsr de Ludolf``;
    ``⟨Darüber von Leibniz' Hand:⟩ resp.`` → ``resp.``. A bracket left over
    (an unmatched one, or the outer one of a nested pair) goes as well.
    """
    counts = {"attached": 0, "standalone": 0, "angle": 0, "stray": 0}

    def _angle(m: re.Match) -> str:
        counts["angle"] += 1
        return ""

    out = _ANGLE_RE.sub(_angle, text)

    def _attached(m: re.Match) -> str:
        counts["attached"] += 1
        return m.group(1) if m.group(1) is not None else m.group(2)

    out = _ATTACHED_BRACKET_RE.sub(_attached, out)

    def _standalone(m: re.Match) -> str:
        counts["standalone"] += 1
        return ""

    while True:  # nested groups: the innermost first, until none is left
        new = _STANDALONE_BRACKET_RE.sub(_standalone, out)
        if new == out:
            break
        out = new
    counts["stray"] = out.count("[") + out.count("]") + out.count("⟨") + out.count("⟩")
    out = re.sub(r"[\[\]⟨⟩]", "", out)
    return " ".join(out.split()), counts


@dataclass(slots=True)
class Letter:
    """One letter of a volume, as parsed: heading, witness, reading text."""

    year: int
    number: str  # as printed in the heading (the source's own numbering, jumps included)
    heading: str
    place_date: str | None
    editorial: str  # the small-type block under the heading, joined
    witness: Witness
    lines: list[str]  # the typeset lines of the reading text, margin numbers gone
    pages: list[int]  # 0-based PDF page indices the text sits on
    text: str = ""  # the reading text: lines joined, brackets resolved
    language: str = "unknown"
    lang_score: float = 0.0
    n_small_dropped: int = 0  # small-type lines inside the body (dropped)
    brackets: dict[str, int] = field(default_factory=dict)
    seq: int = 0  # 1-based position in the volume
    subtitle: str | None = None  # editorial lines between heading and block ("Beilage zu N.5")
    id_suffix: str = ""  # set when the printed number repeats within the volume
    segments: list[str] = field(default_factory=list)  # draft labels printed (⟨L1⟩, ⟨L2⟩ …)
    segment: str | None = None  # the draft kept: the first witness's, else the first printed

    @property
    def letter_id(self) -> str:
        return f"{self.year}-{self.number}{self.id_suffix}"

    @property
    def n_chars(self) -> int:
        return len(self.text)

    def finish(self) -> None:
        """Join the lines, keep one draft where several are printed, resolve the
        brackets, name the language."""
        parts = split_segments(self.lines)
        labelled = [(lab, seg) for lab, seg in parts if lab is not None]
        if labelled:
            self.segments = [lab for lab, _ in labelled]
            want = self.witness.label
            lab, seg = next(((l_, s_) for l_, s_ in labelled if l_ == want), labelled[0])
            self.segment = lab
            self.lines = [*parts[0][1], *seg] if parts[0][0] is None else list(seg)
        joined = join_lines(self.lines)
        text, counts = strip_brackets(" ".join(joined.split("\n")))
        self.text = text
        self.brackets = counts
        lang = classify(text)
        self.language = lang.lang
        self.lang_score = round(lang.score, 4)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["letter_id"] = self.letter_id
        d["n_chars"] = self.n_chars
        d["placeable"] = self.witness.placeable
        return d


@dataclass(slots=True)
class ParseResult:
    """A volume's letters and what the classifier dropped on the way."""

    year: int
    letters: list[Letter]
    n_pages: int
    n_head_lines: int = 0
    n_note_lines: int = 0
    n_margin_numbers: int = 0
    n_pre_block_lines: int = 0  # dateline and subtitle lines between heading and block
    anomalies: list[str] = field(default_factory=list)
    layout: PoolLayout | None = None


def split_notes(lines: Sequence[PoolLine], texts: Sequence[str], layout: PoolLayout) -> int:
    """The index where the notes at the page foot begin (``len(lines)`` if none).

    Scanning up from the bottom, runs of small type are notes, and a short run
    of body type is a note when its first line opens with a line-number key
    and sits under a gap or under a small-type run (EDMAC sets some notes in
    body type; one may wrap onto a second line). An *Überlieferung* line stops
    the scan: it and what follows are a heading's editorial block, not notes.
    """
    n = len(lines)
    cut = n
    i = n - 1
    while i >= 0:
        if layout.small(lines[i]):
            cut = i
            i -= 1
            continue
        j = i  # the body-type run lines[j..i]
        while j >= 0 and not layout.small(lines[j]) and not re.match(r"^\d{1,3}\s", texts[j]):
            j -= 1
        if j < 0 or layout.small(lines[j]) or i - j + 1 > NOTE_RUN_MAX:
            break
        while (  # several notes, each with its key, stand one under the other
            j >= 1
            and not layout.small(lines[j - 1])
            and re.match(r"^\d{1,3}\s", texts[j - 1])
            and i - j + 2 <= NOTE_RUN_MAX
        ):
            j -= 1
        gap = lines[j].top - lines[j - 1].top if j >= 1 else 0.0
        above_small = j >= 1 and layout.small(lines[j - 1])
        if above_small or gap > NOTE_GAP * layout.pitch:
            cut = j
            i = j - 1
            continue
        break
    # An Überlieferung line inside the suffix: from it on, the lines are a
    # heading's editorial block, not notes — except a trailing run that opens
    # with a line-number key after a gap, which is the notes under the block.
    for u in range(cut, n):
        if texts[u].startswith("Überlieferung"):
            for j in range(u + 1, n):
                gap = lines[j].top - lines[j - 1].top
                if gap > NOTE_GAP * layout.pitch and re.match(r"^\d{1,3}\s", texts[j]):
                    return j
            return n
    return cut


class _Builder:
    """The state machine that folds a volume's pages into letters.

    States: ``before`` the first heading; ``heading`` (the heading's own lines
    and the body-size lines under it — the dateline, a subtitle, "Beilage zu
    N.5" — held pending until the small-type *Überlieferung* line arrives);
    ``editorial`` (the small-type block); ``body`` (the reading text, until the
    next heading). A heading is structural — a number, a full stop and a title
    in capitals — and is accepted whatever its number: the volumes' own
    numbering jumps and repeats in places, and every such place is recorded as
    an anomaly rather than silently re-synchronised.
    """

    def __init__(self, year: int, layout: PoolLayout) -> None:
        self.year = year
        self.layout = layout
        self.result = ParseResult(year=year, letters=[], n_pages=0, layout=layout)
        self.current: Letter | None = None
        self.state = "before"  # before | heading | editorial | body
        self.editorial_lines: list[str] = []
        self.pending: list[str] = []  # body-size lines between the heading and the block
        self.numbers: Counter = Counter()

    def _flush_pending(self, *, as_body: bool) -> None:
        """The lines held since the heading: editorial (dateline, subtitle) or, when no
        block followed, the dateline and then reading text."""
        cur = self.current
        if cur is None or not self.pending:
            self.pending = []
            return
        rest: list[str] = []
        for text in self.pending:
            if cur.place_date is None and _YEAR_RE.search(re.sub(r"[\[\]]", "", text)):
                cur.place_date = text
            elif as_body:
                rest.append(text)
            else:
                cur.subtitle = f"{cur.subtitle} {text}" if cur.subtitle else text
        self.result.n_pre_block_lines += len(self.pending) - len(rest)
        cur.lines.extend(rest)
        self.pending = []

    def _finish_current(self) -> None:
        cur = self.current
        if cur is None:
            return
        self._flush_pending(as_body=True)
        cur.editorial = " ".join(self.editorial_lines)
        cur.witness = parse_witness(cur.editorial)
        cur.finish()
        self.result.letters.append(cur)
        self.current = None
        self.editorial_lines = []

    def _start(self, number: str, title: str, page: int) -> None:
        self._finish_current()
        prev = self.result.letters[-1] if self.result.letters else None
        if prev is not None and int(number) != int(prev.number) + 1:
            self.result.anomalies.append(f"page {page}: heading N.{number} follows N.{prev.number}")
        self.numbers[number] += 1
        suffix = f"-{self.numbers[number]}" if self.numbers[number] > 1 else ""
        if suffix:
            self.result.anomalies.append(f"page {page}: heading N.{number} printed again")
        self.current = Letter(
            year=self.year,
            number=number,
            heading=title,
            place_date=None,
            editorial="",
            witness=Witness(None, None, None, None, None, None, False, None),
            lines=[],
            pages=[page],
            seq=len(self.result.letters) + 1,
            id_suffix=suffix,
        )
        self.state = "heading"

    def feed(self, page: PoolPage) -> None:
        lay = self.layout
        res = self.result
        res.n_pages += 1
        head_zone = HEAD_ZONE * page.height
        head_lines = [ln for ln in page.lines if ln.top < head_zone]
        head_text = " ".join(ln.text for ln in head_lines)
        res.n_head_lines += len(head_lines)
        if "inhaltsverzeichnis" in head_text.lower():
            return
        body = [ln for ln in page.lines if ln.top >= head_zone]
        texts: list[str] = []
        kept: list[PoolLine] = []
        for ln in body:
            text = strip_margin_number(ln, lay)
            if text != ln.text:
                res.n_margin_numbers += 1
            if text:
                kept.append(ln)
                texts.append(clean_text(text))
        cut = split_notes(kept, texts, lay)
        res.n_note_lines += len(kept) - cut
        kept, texts = kept[:cut], texts[:cut]
        touched: set[str] = set()
        for ln, text in zip(kept, texts, strict=True):
            hm = heading_match(text) if not lay.small(ln) else None
            if hm is not None:
                self._start(hm[0], hm[1], page.index)
                touched.add(hm[0])
                continue
            if self.current is None:
                continue
            cur = self.current
            touched.add(cur.number)
            if page.index not in cur.pages:
                cur.pages.append(page.index)
            small = lay.small(ln)
            if self.state == "heading":
                if small and text.startswith("Überlieferung"):
                    self._flush_pending(as_body=False)
                    self.state = "editorial"
                elif small:
                    continue  # a margin number or superscript on its own line
                elif not self.pending and is_caps_line(text):
                    cur.heading += " " + text
                    continue
                elif len(self.pending) < PENDING_MAX:
                    self.pending.append(text)
                    continue
                else:
                    self._flush_pending(as_body=True)
                    self.state = "body"
            if self.state == "editorial":
                if small:
                    self.editorial_lines.append(text)
                    continue
                self.state = "body"
            if small:
                cur.n_small_dropped += 1
                if text.startswith("Überlieferung"):
                    res.anomalies.append(
                        f"page {page.index}: an Überlieferung line inside the body of "
                        f"N.{cur.number} (a heading missed?)"
                    )
                continue
            cur.lines.append(text)
        hn = head_number(" ".join(clean_text(ln.text) for ln in head_lines if lay.small(ln)))
        if hn and touched and hn not in touched:
            res.anomalies.append(
                f"page {page.index}: running head N.{hn} over "
                f"N.{', N.'.join(sorted(touched, key=int))}"
            )

    def close(self) -> ParseResult:
        self._finish_current()
        return self.result


def parse_volume(year: int, pages: Sequence[PoolPage]) -> ParseResult:
    """All letters of one volume from its extracted pages."""
    layout = learn_layout(pages)
    builder = _Builder(year, layout)
    for page in pages:
        builder.feed(page)
    return builder.close()


# --------------------------------------------------------------------------- #
# Files and the report
# --------------------------------------------------------------------------- #


def write_letters(result: ParseResult, path: str | Path) -> Path:
    """The volume's letters as JSONL under ``data/`` (text included: never committed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for letter in result.letters:
            fh.write(json.dumps(letter.as_dict(), ensure_ascii=False) + "\n")
    return p


def read_letters(path: str | Path) -> list[Letter]:
    out: list[Letter] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        row.pop("letter_id", None)
        row.pop("n_chars", None)
        row.pop("placeable", None)
        row["witness"] = Witness(**row["witness"])
        out.append(Letter(**row))
    return out


SIGLA = ("L", "l", "K", "k")


def summarize(results: Sequence[ParseResult]) -> dict:
    """Counts per year and in all: letters by language, siglum, placeability — no text."""
    years = []
    for res in results:
        letters = res.letters
        by_lang = Counter(ltr.language for ltr in letters)
        by_siglum = Counter(
            ltr.witness.siglum if ltr.witness.siglum in SIGLA else "other" for ltr in letters
        )
        years.append(
            {
                "year": res.year,
                "pages": res.n_pages,
                "letters": len(letters),
                "by_language": dict(sorted(by_lang.items())),
                "by_siglum": {s: by_siglum.get(s, 0) for s in (*SIGLA, "other")},
                "placeable": sum(1 for ltr in letters if ltr.witness.placeable),
                "german_placeable": sum(
                    1 for ltr in letters if ltr.language == "de" and ltr.witness.placeable
                ),
                "german_placeable_by_siglum": {
                    s: sum(
                        1
                        for ltr in letters
                        if ltr.language == "de"
                        and ltr.witness.placeable
                        and ltr.witness.siglum == s
                    )
                    for s in SIGLA
                },
                "shared_leaves": sum(1 for ltr in letters if ltr.witness.shared),
                "multi_draft": sum(1 for ltr in letters if ltr.segments),
                "chars": sum(ltr.n_chars for ltr in letters),
                "margin_numbers": res.n_margin_numbers,
                "note_lines": res.n_note_lines,
                "small_dropped_in_body": sum(ltr.n_small_dropped for ltr in letters),
                "brackets": {
                    k: sum(ltr.brackets.get(k, 0) for ltr in letters)
                    for k in ("attached", "standalone", "angle")
                },
                "anomalies": list(res.anomalies),
                "body_size": res.layout.body_size if res.layout else None,
            }
        )
    total = {
        "letters": sum(y["letters"] for y in years),
        "pages": sum(y["pages"] for y in years),
        "by_language": dict(sum((Counter(y["by_language"]) for y in years), Counter())),
        "by_siglum": {s: sum(y["by_siglum"][s] for y in years) for s in (*SIGLA, "other")},
        "placeable": sum(y["placeable"] for y in years),
        "german_placeable": sum(y["german_placeable"] for y in years),
        "german_placeable_by_siglum": {
            s: sum(y["german_placeable_by_siglum"][s] for y in years) for s in SIGLA
        },
        "shared_leaves": sum(y["shared_leaves"] for y in years),
        "multi_draft": sum(y["multi_draft"] for y in years),
        "chars": sum(y["chars"] for y in years),
        "anomalies": sum(len(y["anomalies"]) for y in years),
    }
    return {"years": years, "total": total}


def render_parse_report(summary: dict, sources: Sequence[VolumeSource]) -> str:
    """``letterpool-parse.md``: the pool as parsed, numbers only."""
    out: list[str] = []
    out.append("# The GWLB letter pool, parsed (K2b Task 1)")
    out.append("")
    t = summary["total"]
    out.append(
        f"{t['letters']:,} letters on {t['pages']:,} PDF pages of the checked volumes "
        f"({', '.join(str(s.year) for s in sources)}), parsed from the text layer: the running "
        "head, the margin line numbers and the notes at the page foot dropped, each letter's "
        "number, heading, dateline, *Überlieferung* block and reading text kept apart. "
        "Language per letter by the K1 stopword identifier; the siglum is the first witness's "
        "(L Leibniz's hand, l his scribe, K the correspondent's hand, k the correspondent's "
        "scribe; *other*: a copy, a print, none named); *placeable*: the first witness is in "
        "the GWLB's Leibniz collections (LBr, LH, LK, Marg) with a `Bl.` range. The pool is "
        f"{LICENCE} ({LICENCE_BUCKET} bucket): this report carries counts, no text."
    )
    out.append("")
    out.append("## Per year")
    out.append("")
    out.append(
        "| year | pages | letters | de | fr | la | mixed | unknown | L | l | K | k | other | "
        "placeable | de & placeable (L / l / K / k) | shared leaves | chars | anomalies |"
    )
    out.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|"
    )
    for y in summary["years"]:
        bl, bs, gp = y["by_language"], y["by_siglum"], y["german_placeable_by_siglum"]
        out.append(
            f"| {y['year']} | {y['pages']} | {y['letters']} | {bl.get('de', 0)} | "
            f"{bl.get('fr', 0)} | {bl.get('la', 0)} | {bl.get('mixed', 0)} | "
            f"{bl.get('unknown', 0)} | {bs['L']} | {bs['l']} | {bs['K']} | {bs['k']} | "
            f"{bs['other']} | {y['placeable']} | {y['german_placeable']} "
            f"({gp['L']} / {gp['l']} / {gp['K']} / {gp['k']}) | {y['shared_leaves']} | "
            f"{y['chars']:,} | {len(y['anomalies'])} |"
        )
    bl, bs, gp = t["by_language"], t["by_siglum"], t["german_placeable_by_siglum"]
    out.append(
        f"| **all** | {t['pages']:,} | {t['letters']:,} | {bl.get('de', 0)} | {bl.get('fr', 0)} | "
        f"{bl.get('la', 0)} | {bl.get('mixed', 0)} | {bl.get('unknown', 0)} | {bs['L']} | "
        f"{bs['l']} | {bs['K']} | {bs['k']} | {bs['other']} | {t['placeable']} | "
        f"{t['german_placeable']} ({gp['L']} / {gp['l']} / {gp['K']} / {gp['k']}) | "
        f"{t['shared_leaves']} | {t['chars']:,} | {t['anomalies']} |"
    )
    out.append("")
    out.append("## What the classifier dropped")
    out.append("")
    out.append(
        "| year | margin numbers stripped | note lines at the foot | small-type lines inside "
        "bodies | brackets attached / standalone / angle | multi-draft letters |"
    )
    out.append("|---|---:|---:|---:|---:|---:|")
    for y in summary["years"]:
        out.append(
            f"| {y['year']} | {y['margin_numbers']:,} | {y['note_lines']:,} | "
            f"{y['small_dropped_in_body']:,} | {y['brackets']['attached']:,} / "
            f"{y['brackets']['standalone']:,} / {y['brackets'].get('angle', 0):,} | "
            f"{y['multi_draft']} |"
        )
    anomalies = [(y["year"], a) for y in summary["years"] for a in y["anomalies"]]
    out.append("")
    out.append("## Anomalies")
    out.append("")
    if not anomalies:
        out.append(
            "None: every heading followed its predecessor by one and every running head agreed."
        )
    else:
        out.append(
            f"{len(anomalies)} places where a heading did not follow its predecessor by one or "
            "the running head named another letter (the parser carried on; the letters around "
            "them are to be checked by eye):"
        )
        out.append("")
        for year, a in anomalies[:60]:
            out.append(f"- {year}: {a}")
        if len(anomalies) > 60:
            out.append(f"- … and {len(anomalies) - 60} more")
    out.append("")
    out.append("## Sources")
    out.append("")
    for s in sources:
        out.append(f"- {s.citation} — version {s.version}, {s.n_pages} pages, `{s.url}`")
    out.append("")
    return "\n".join(out)


__all__ = [
    "CHECKED_YEARS",
    "DEFAULT_LETTERS_DIR",
    "DEFAULT_POOL_DIR",
    "DEFAULT_REPORTS_DIR",
    "DEFAULT_SOURCES",
    "HEAD_ZONE",
    "LICENCE",
    "LICENCE_BUCKET",
    "PAGE_URL",
    "PLACEABLE_FAMILIES",
    "SIGLA",
    "Letter",
    "ParseResult",
    "PoolLayout",
    "PoolLine",
    "PoolPage",
    "VolumeInfo",
    "VolumeSource",
    "Witness",
    "clean_text",
    "fetch_volumes",
    "german_date",
    "heading_match",
    "is_caps_line",
    "iter_pdf_pages",
    "learn_layout",
    "load_sources",
    "parse_volume",
    "parse_witness",
    "parse_year_page",
    "pdf_page_count",
    "read_letters",
    "read_page_cache",
    "render_parse_report",
    "sha256_of",
    "split_notes",
    "strip_brackets",
    "strip_margin_number",
    "summarize",
    "write_letters",
    "write_page_cache",
    "write_sources",
]
