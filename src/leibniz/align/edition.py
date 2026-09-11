"""Reading-text extraction from a §70-expired volume's text layer (Phase C2).

The GT factory needs, per printed piece, the constituted **reading text** and
nothing else (SPECS §7.2). Two page-text sources are read here:

* **hOCR** — the OCR the Internet Archive ships with its public-domain volume
  scans (``{id}_hocr.html``): one ``ocr_page`` per leaf, every ``ocr_line`` with a
  bounding box and an ``x_size`` (line height ≈ type size).
* **PDF text layer** — the edition's own PDFs (born-digital from Potsdam; ABBYY
  OCR in the GWLB repositorium), read through ``pdfplumber`` (font size per
  character).

Both become the same :class:`PageText` (lines with position + size), so one
layout classifier serves all sources. The Akademie-Ausgabe page is regular
enough for that classifier to be a handful of rules:

* the **running head** sits in the top zone and carries ``N. <piece>`` — the
  number of the *last* piece on the page — plus the printed page number;
* the **reading text** is the larger type; the **apparatus** (variants,
  editorial commentary) is the smaller type, stair-stepped at the *bottom*;
* a **piece heading** is ``<num>. TITLE IN CAPS`` in the reading zone; the
  editorial dateline and *Überlieferung* block that follow it are indented or
  set small — the reading text resumes at the first line back on the body
  margin;
* every fifth line carries a **margin line number** (``5``, ``10``, …), which
  OCR sometimes glues onto the line it counts.

The result per page is a list of events — ``("heading", "20")`` /
``("line", text)`` — which :func:`assemble_pieces` folds into one text per
piece across pages, carrying the current piece over page breaks and recording
the pages (anchors) each piece occupies. Everything is pure and offline-testable
on synthetic :class:`PageText` fixtures; the readers are thin.

Precision over recall throughout: a dropped reading line costs one training
pair, an editorial line leaked into the GT is a licensing *and* correctness bug.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Page text model
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class TextLine:
    """One physical text line with its box and (relative) type size."""

    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    size: float


@dataclass(slots=True)
class PageText:
    """All lines of one page/leaf, any order (the classifier sorts)."""

    index: int  # 0-based leaf index in the source (IA leaf / PDF page)
    width: float
    height: float
    lines: list[TextLine] = field(default_factory=list)
    exact_sizes: bool = False  # PDF text layer (exact points) vs OCR estimate (jittered)


# --------------------------------------------------------------------------- #
# Readers
# --------------------------------------------------------------------------- #

_BBOX_RE = re.compile(r"bbox (\d+) (\d+) (\d+) (\d+)")
_XSIZE_RE = re.compile(r"x_size ([\d.]+)")
_LINE_CLASSES = ("ocr_line", "ocr_header", "ocr_textfloat", "ocr_caption")


def iter_hocr_pages(path: str | Path) -> Iterator[PageText]:
    """Stream the pages of a (Tesseract-style) hOCR file as :class:`PageText`.

    Uses ``lxml.etree.iterparse`` over ``ocr_page`` divs so a 50 MB volume file
    never sits in memory whole. Lines without a parseable ``x_size`` get size 0
    (they are treated as small — i.e. never as reading text).
    """
    from lxml import etree

    for _event, div in etree.iterparse(str(path), events=("end",), tag="div", html=True):
        if div.get("class") != "ocr_page":
            continue
        m = _BBOX_RE.search(div.get("title", ""))
        width, height = (float(m.group(3)), float(m.group(4))) if m else (0.0, 0.0)
        idx_m = re.search(r"ppageno (\d+)", div.get("title", ""))
        index = int(idx_m.group(1)) if idx_m else 0
        lines: list[TextLine] = []
        for span in div.iter("span"):
            if span.get("class") not in _LINE_CLASSES:
                continue
            title = span.get("title", "")
            bm = _BBOX_RE.search(title)
            if bm is None:
                continue
            sm = _XSIZE_RE.search(title)
            text = " ".join(span.xpath("string()").split())
            if not text:
                continue
            x0, y0, x1, y1 = (float(g) for g in bm.groups())
            lines.append(TextLine(text, x0, x1, y0, y1, float(sm.group(1)) if sm else 0.0))
        yield PageText(index=index, width=width, height=height, lines=lines)
        div.clear()
        while div.getprevious() is not None:
            del div.getparent()[0]


def _pdf_stream(path: str | Path):
    """The PDF bytes from ``%PDF`` on — some servers prepend a CMS header block."""
    import io

    data = Path(path).read_bytes()
    start = data.find(b"%PDF")
    return io.BytesIO(data[start:] if start > 0 else data)


def iter_pdf_pages(path: str | Path, *, x_tolerance: float = 2.0) -> Iterator[PageText]:
    """Stream a PDF's text layer as :class:`PageText` (needs ``pdfplumber``).

    ``x_tolerance`` is the word-gap threshold; the born-digital Potsdam volumes
    need a tight one (2 pt) or words run together. Size per line = the modal
    character size on that line.
    """
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise ModuleNotFoundError(
            "iter_pdf_pages needs pdfplumber (`uv sync --extra gt`)."
        ) from exc
    with pdfplumber.open(_pdf_stream(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            lines: list[TextLine] = []
            for ln in page.extract_text_lines(x_tolerance=x_tolerance, return_chars=True):
                text = " ".join(ln["text"].split())
                if not text:
                    continue
                sizes = Counter(round(float(c.get("size", 0.0)), 1) for c in ln["chars"])
                size = sizes.most_common(1)[0][0] if sizes else 0.0
                lines.append(
                    TextLine(text, ln["x0"], ln["x1"], ln["top"], ln["bottom"], float(size))
                )
            yield PageText(
                index=i,
                width=float(page.width),
                height=float(page.height),
                lines=lines,
                exact_sizes=True,
            )


# --------------------------------------------------------------------------- #
# Layout classification
# --------------------------------------------------------------------------- #

# "N. 20" / "N. 13. 14" in the running head: the head lists the pieces that
# START on the page (or the one continuing, if none starts). OCR may split
# digits ("N. 1 1"), read 1 as I/l, or glue the section title on.
HEAD_PIECE_RE = re.compile(r"\bN\s*[.,]?\s*((?:[\dIil]{1,3}\s*[.,]?\s*)+)")
_HEAD_TOKEN_RE = re.compile(r"[\dIil]{1,3}")
# "20. LEIBNIZ AN FRANZ KUCKUCK" — number, dot/comma, then a title set in caps.
# OCR renders "1." as "i."/"l." often enough to allow it in the number, and an
# ABBYY layer renders small-caps surnames in lowercase ("5. CHILIAN Schrader AN
# LEIBNIZ"), so the title is checked by its share of uppercase letters
# (:func:`heading_match`) rather than by "no lowercase at all" — an enumerated
# reading line ("1. Que la…") still never passes.
HEADING_RE = re.compile(r"^([\dIil]{1,3})\s*([a-z])?\s*[.,]\s+([A-ZÄÖÜÉÈÀ].{3,})$")
HEADING_CAPS_SHARE = 0.6
_OCR_DIGITS = str.maketrans({"I": "1", "i": "1", "l": "1", "o": "0", "O": "0"})


def heading_match(text: str) -> tuple[str, str] | None:
    """``("13", "")`` for a piece heading line, else ``None``.

    The number may be OCR'd (``i.``, ``II.``); a *capital* Roman prefix is left
    to the caller (``roman``) because ``"I. HAUS BRAUNSCHWEIG…"`` is a section
    title, not piece 1 — it is a heading only when the running head confirms it.
    Returns the digit-translated number and the sub-letter.
    """
    m = HEADING_RE.match(text.strip())
    if not m:
        return None
    title = m.group(3)
    letters = [ch for ch in title if ch.isalpha()]
    if len(letters) < 4 or sum(ch.isupper() for ch in letters) / len(letters) < HEADING_CAPS_SHARE:
        return None
    num = m.group(1).translate(_OCR_DIGITS).lstrip("0") or "0"
    return num, m.group(2) or ""


def _roman_prefix(text: str) -> bool:
    return bool(re.match(r"^[IVX]{1,3}\s*[.,]", text.strip()))


_YEAR_RE = re.compile(r"\b1[67]\d\d\b")
_MARGIN_TOKENS = frozenset(
    {"5", "10", "15", "20", "25", "30", "35", "40", "45", "50"}
    | {"io", "1o", "i5", "ij", "2o", "3o", "4o", "zo", "jo", "ro", "IO", "so"}
)
_MARGIN_LINE_RE = re.compile(r"^[\dilIjoOzZsS ]{1,3}$")
# The vocabulary of the editorial *Überlieferung* block (witness descriptions:
# sigla, shelfmarks, leaves, seals, prints) — used only while a piece's body has
# not started yet, where such a line is a continuation of that block.
_WITNESS_VOCAB_RE = re.compile(
    r"\b(Bl\.|Bog\.|Gedr\.|Teildr\.|Teildruck|Druckvorlage|Aufschrift|Siegel|Postverm|"
    r"Bibl\.\s*verm|Konzept|Abfertigung|Abschrift|Reinschrift|Eigh\.|eigh\.|LBr\.?|LH\b|"
    r"Auszug|Nachdruck|Erstdruck|Handexemplar|Überlieferung|Ueberlieferung|Druck nach|"
    r"Handschriften:|Drucke:)"
)
# Editorial lines that are dropped wherever they occur: a whole line in
# brackets (dateline, editor's note) or a witness statement.
_EDITORIAL_LINE_RE = re.compile(r"^\[.*\]\.?$|^(Druck nach|Überlieferung|Ueberlieferung)\b")

# Fallback fraction of the body size below which a line counts as "small type"
# (used only when a volume shows no second type-size cluster).
SMALL_RATIO = 0.90
# The running-head zone: top of the page; head fragments share one baseline.
HEAD_ZONE = 0.12
HEAD_BASELINE = 0.02


@dataclass(slots=True)
class PageReading:
    """The classifier's verdict on one page."""

    index: int
    head_pieces: list[str]  # piece numbers in the running head (those starting here)
    printed_page: int | None
    head_text: str | None  # the running head's text (for section/back-matter detection)
    events: list[tuple[str, str]] = field(default_factory=list)  # ("heading"|"line", value)
    n_apparatus: int = 0  # lines dropped as apparatus/commentary
    n_editorial: int = 0  # lines dropped as headings/datelines/Überlieferung/small
    ended_awaiting: bool = False  # a heading's editorial block ran to the page end

    @property
    def head_piece(self) -> str | None:
        """The newest piece on the page per the running head (``None`` if unparsed)."""
        return self.head_pieces[-1] if self.head_pieces else None

    @property
    def reading_lines(self) -> list[str]:
        return [v for k, v in self.events if k == "line"]

    @property
    def headings(self) -> list[str]:
        return [v for k, v in self.events if k == "heading"]

    @property
    def eligible(self) -> bool:
        """A page can carry reading text only if it is a numbered-piece page."""
        return bool(self.head_pieces) or bool(self.headings)


def _weighted_mode(values: Iterable[tuple[float, int]]) -> float | None:
    acc: Counter = Counter()
    for v, w in values:
        acc[v] += w
    return acc.most_common(1)[0][0] if acc else None


def body_size(lines: Sequence[TextLine], height: float) -> float:
    """The reading-text type size: char-weighted mode over long lines up top."""
    long_lines = [ln for ln in lines if len(ln.text) >= 20 and ln.top < 0.75 * height]
    pool = long_lines or [ln for ln in lines if len(ln.text) >= 20] or list(lines)
    mode = _weighted_mode((round(ln.size * 2) / 2, len(ln.text)) for ln in pool if ln.size > 0)
    return float(mode) if mode else 0.0


@dataclass(frozen=True, slots=True)
class TypeSizes:
    """A volume's learned type sizes: body, apparatus (if any) and the cut between."""

    body: float
    apparatus: float | None
    threshold: float  # a line with size < threshold is "small type"
    indent: float | None = None  # paragraph indent as a fraction of page width


def size_threshold(
    pages: Sequence[PageText], *, min_share: float = 0.08, min_gap: float | None = None
) -> TypeSizes:
    """Learn body vs apparatus type size from a whole volume's size histogram.

    The two dominant, char-weighted size clusters are the reading text (largest
    weight) and the apparatus/commentary (the next cluster clearly below it, at
    least ``min_share`` of the body's weight). The cut is their midpoint — which
    is what makes an ABBYY layer at 10 pt / 9.5 pt separable as reliably as
    Tesseract's 41 px / 33 px. "Clearly below" depends on the source: a PDF
    text layer carries exact sizes (a 3 % gap is real), an OCR ``x_size`` is an
    estimate that jitters by a pixel or two (a neighbouring bin is the body
    itself, so a 10 % gap is required). Without a second cluster the cut falls
    back to ``SMALL_RATIO × body``.
    """
    hist: Counter = Counter()
    exact = all(pg.exact_sizes for pg in pages) if pages else False
    if min_gap is None:
        min_gap = 0.03 if exact else 0.10
    for pg in pages:
        for ln in pg.lines:
            if ln.size > 0 and len(ln.text) >= 4:
                hist[round(ln.size * 2) / 2] += len(ln.text)
    if not hist:
        return TypeSizes(0.0, None, 0.0)
    # The reading text is the *larger* type among the heavy clusters: a volume
    # with as much commentary as text (Reihe III) must not elect the small one.
    top_w = hist.most_common(1)[0][1]
    body = max(sz for sz, w in hist.items() if w >= 0.5 * top_w)
    body_w = hist[body]
    below = [
        (sz, w) for sz, w in hist.items() if sz < (1 - min_gap) * body and w >= min_share * body_w
    ]
    if not below:
        return TypeSizes(float(body), None, SMALL_RATIO * body)
    apparatus = max(below, key=lambda t: t[1])[0]
    return TypeSizes(float(body), float(apparatus), (body + apparatus) / 2.0)


def indent_offset(pages: Sequence[PageText]) -> float | None:
    """The paragraph indent (fraction of page width), learned over the volume.

    Per page, the offset of each line's ``x0`` from that page's body margin is
    binned; the modal offset between 1 % and 7 % of the width is the indent.
    Learning it volume-wide keeps an editorial block (indented differently)
    from posing as the paragraph indent on the page where a piece opens.
    """
    hist: Counter = Counter()
    for pg in pages:
        W = pg.width or 1.0
        lines = [ln for ln in pg.lines if ln.text.strip()]
        if len(lines) < 5:
            continue
        body_x0, _ = _margins(lines, W)
        for ln in lines:
            off = (ln.x0 - body_x0) / W
            if 0.01 < off < 0.07:
                hist[round(off, 3)] += 1
    if not hist:
        return None
    return hist.most_common(1)[0][0]


def learn_layout(pages: Sequence[PageText]) -> TypeSizes:
    """Type sizes + paragraph indent for a whole volume (the two-pass prelude)."""
    sizes = size_threshold(pages)
    return TypeSizes(sizes.body, sizes.apparatus, sizes.threshold, indent_offset(pages))


def _looks_like_running_head(text: str, *, first: bool) -> bool:
    """Is this top-zone line a running-head fragment?

    The section title in the head (``"I. HAUS BRAUNSCHWEIG-LÜNEBURG 1690—1691"``)
    is Roman-numbered; a piece heading (``"13. GOTTFRIED CHRISTIAN OTTO AN
    LEIBNIZ"``) is digit-numbered — that is the only tell when the head is missing
    and the heading is the first line, so a digit-numbered heading never opens
    a head; later fragments are gated by the baseline band instead.
    """
    if first and text[:1].isdigit() and heading_match(text) and not HEAD_PIECE_RE.search(text):
        return False
    if HEAD_PIECE_RE.search(text):
        return True
    if re.fullmatch(r"[\divxlcIVXLC]{1,5}", text.strip()):
        return True  # a bare page number
    return len(text) >= 6 and not re.search(r"[a-zäöüéèàß]", text)  # caps section title


def head_pieces_of(text: str) -> list[str]:
    """Piece numbers listed in a running head: ``"N. 13. 14"`` → ``["13", "14"]``.

    Roman-looking OCR of digits (``II`` for 11) is mapped back; a trailing token
    that is really the section title's Roman numeral (``"N. 9 I. HAUS …"``) is
    dropped; split digits (``"N. 1 1"``) are rejoined.
    """
    m = HEAD_PIECE_RE.search(text)
    if not m:
        return []
    raw = m.group(1)
    tokens = _HEAD_TOKEN_RE.findall(raw)
    after = text[m.end() :].lstrip()
    if len(tokens) > 1 and after[:1].isalpha() and not any(ch.isdigit() for ch in tokens[-1]):
        tokens = tokens[:-1]  # "I." of the section title, not a piece
    nums = [t.translate(_OCR_DIGITS) for t in tokens]
    if len(nums) >= 2 and all(len(n) == 1 for n in nums) and nums == nums[:1] * len(nums):
        nums = ["".join(nums)]  # "N. 1 1" → 11
    return [n.lstrip("0") or "0" for n in nums]


def _printed_page_of(fragments: Sequence[str]) -> int | None:
    """The printed page number from the head fragments (a bare number wins)."""
    for f in fragments:
        t = f.strip().translate(_OCR_DIGITS)
        if re.fullmatch(r"\d{1,4}", t) and int(t) < 1500:
            return int(t)
    for f in fragments:
        t = re.sub(r"N\s*[.,]?\s*(?:[\dIil]{1,3}\s*[.,]?\s*)+", " ", f)
        for m in (re.match(r"\s*(\d{1,4})\b", t), re.search(r"\b(\d{1,4})\s*$", t)):
            if m and int(m.group(1)) < 1500:
                return int(m.group(1))
    return None


def _is_margin_number(ln: TextLine, width: float) -> bool:
    t = ln.text.strip()
    if not _MARGIN_LINE_RE.fullmatch(t):
        return False
    narrow = (ln.x1 - ln.x0) < 0.06 * width
    at_margin = ln.x0 < 0.16 * width or ln.x1 > 0.84 * width
    return narrow and at_margin


def _strip_margin_tokens(text: str, ln: TextLine, body_x0: float, width: float) -> str:
    toks = text.split()
    if len(toks) >= 2 and toks[0] in _MARGIN_TOKENS and ln.x0 < body_x0 - 0.012 * width:
        toks = toks[1:]
    if len(toks) >= 2 and toks[-1] in _MARGIN_TOKENS:
        toks = toks[:-1]
    return " ".join(toks)


def _looks_like_dateline(text: str) -> bool:
    t = text.strip()
    if t.startswith("[") or t.endswith("]"):
        return True
    return bool(_YEAR_RE.search(t)) and len(t) < 90


def _line_pitch(lines: Sequence[TextLine]) -> float:
    """Median vertical distance between consecutive lines (the leading)."""
    tops = sorted(ln.top for ln in lines)
    gaps = sorted(b - a for a, b in zip(tops, tops[1:], strict=False) if b - a > 0)
    if not gaps:
        return float("inf")
    return gaps[len(gaps) // 2]


def _margins(lines: Sequence[TextLine], width: float) -> tuple[float, float]:
    """(body left margin, paragraph-indent x) from the long lines' x0 modes."""
    step = max(width * 0.005, 1e-6)
    longs = [ln for ln in lines if (ln.x1 - ln.x0) > 0.55 * width]
    pool = longs or list(lines)
    mode = _weighted_mode((round(ln.x0 / step), 1) for ln in pool)
    body_x0 = mode * step if mode is not None else min((ln.x0 for ln in lines), default=0.0)
    cands = Counter(
        round(ln.x0 / step)
        for ln in lines
        if body_x0 + 0.01 * width < ln.x0 < body_x0 + 0.07 * width
    )
    indent = cands.most_common(1)[0][0] * step if cands else body_x0 + 0.04 * width
    return body_x0, indent


def classify_page(
    page: PageText,
    *,
    sizes: TypeSizes | None = None,
    small_ratio: float = SMALL_RATIO,
    awaiting_body: bool = False,
) -> PageReading:
    """Split one page into running head / reading text / apparatus / editorial.

    ``sizes`` (from :func:`size_threshold` over the whole volume) fixes the
    body/apparatus cut; without it the cut is ``small_ratio`` × this page's own
    body size (fine for a lone page, fragile on an editorial-heavy one).
    ``awaiting_body`` carries over from a previous page whose heading's
    editorial block (dateline, *Überlieferung*) ran past the page end.
    """
    lines = sorted((ln for ln in page.lines if ln.text.strip()), key=lambda ln: (ln.top, ln.x0))
    H, W = page.height or 1.0, page.width or 1.0
    threshold = sizes.threshold if sizes is not None else small_ratio * body_size(lines, H)

    def small(ln: TextLine) -> bool:
        return ln.size < threshold

    # 1. Running head: fragments in the top zone sharing the first one's baseline.
    #    Margin line numbers are dropped here too — they carry no text and would
    #    derail the apparatus scan below.
    head_frags: list[str] = []
    head_top: float | None = None
    keep: list[TextLine] = []
    for ln in lines:
        t = ln.text.strip()
        in_zone = ln.top < HEAD_ZONE * H and (
            head_top is None or ln.top <= head_top + HEAD_BASELINE * H
        )
        if in_zone and not keep and _looks_like_running_head(t, first=head_top is None):
            head_frags.append(t)
            head_top = ln.top if head_top is None else head_top
            continue
        if _is_margin_number(ln, W):
            continue
        keep.append(ln)
    head_pieces: list[str] = []
    for f in head_frags:
        head_pieces = head_pieces or head_pieces_of(f)
    printed = _printed_page_of(head_frags)
    head_text = " ".join(head_frags) if head_frags else None

    # 2. The apparatus block: small-type lines contiguous at the bottom. A
    #    body-sized line is absorbed into the block when it is sandwiched
    #    between small lines, or sits right below a block gap (the apparatus
    #    is set off from the text by more than a line pitch).
    pitch = _line_pitch(keep)
    cut = len(keep)
    i = len(keep) - 1
    while i >= 0:
        if small(keep[i]):
            cut = i
        elif cut < len(keep) and i >= 1:
            gap = keep[i].top - keep[i - 1].top
            if small(keep[i - 1]) or gap > 1.6 * pitch:
                cut = i
            else:
                break
        else:
            break
        i -= 1
    reading, apparatus = keep[:cut], keep[cut:]
    n_apparatus = len(apparatus)

    # 3. Inside the reading zone (margins learned from body-size lines only, so
    #    a long editorial block cannot pose as the text margin).
    body_x0, indent_x0 = _margins([ln for ln in reading if not small(ln)] or reading, W)
    if sizes is not None and sizes.indent is not None:
        indent_x0 = body_x0 + sizes.indent * W
    tol = 0.015 * W
    events: list[tuple[str, str]] = []
    n_editorial = 0
    # after a heading: skip editorial lines until the body margin
    for ln in reading:
        t = ln.text.strip()
        glued_margin_no = t.split()[0] in _MARGIN_TOKENS and ln.x0 < body_x0 - 0.012 * W
        hm = heading_match(t)
        if hm:
            num, sub = hm
            confirmed = num in head_pieces
            # A heading is body-sized or larger (OCR size jitter is overruled by
            # the running head); a capital-Roman prefix is a section title unless
            # the head confirms that piece is on this page.
            if (not small(ln) or confirmed) and (confirmed or not _roman_prefix(t)):
                events.append(("heading", f"{num}{sub}"))
                awaiting_body = True
                continue
        # A glued margin number wrecks the OCR size estimate; trust the position.
        # A line with no lowercase letter is a title, sub-heading or bare number —
        # never a line of running reading text.
        if (
            (small(ln) and not glued_margin_no)
            or _EDITORIAL_LINE_RE.match(t)
            or not re.search(r"[a-zäöüéèàß]", t)
        ):
            n_editorial += 1
            continue
        if awaiting_body:
            on_margin = (
                abs(ln.x0 - body_x0) <= tol or abs(ln.x0 - indent_x0) <= tol or glued_margin_no
            )
            has_lower = bool(re.search(r"[a-zäöüéèàß]", t))
            if (
                not on_margin
                or not has_lower
                or _looks_like_dateline(t)
                or _WITNESS_VOCAB_RE.search(t)
            ):
                n_editorial += 1
                continue
            awaiting_body = False
        t = _strip_margin_tokens(t, ln, body_x0, W)
        if t:
            events.append(("line", t))
    return PageReading(
        index=page.index,
        head_pieces=head_pieces,
        printed_page=printed,
        head_text=head_text,
        events=events,
        n_apparatus=n_apparatus,
        n_editorial=n_editorial,
        ended_awaiting=awaiting_body,
    )


# --------------------------------------------------------------------------- #
# Piece assembly across pages
# --------------------------------------------------------------------------- #

_HYPHEN_END = re.compile(r"[\-¬­‐‑]$")


def join_lines(lines: Sequence[str]) -> str:
    """Join reading lines, rejoining words the print hyphenated at a line end."""
    out: list[str] = []
    pending: str | None = None
    for raw in lines:
        t = raw.strip()
        if not t:
            continue
        if pending is not None:
            if t[:1].islower():
                t = pending + t
            else:
                out.append(pending + "-")
            pending = None
        if _HYPHEN_END.search(t) and len(t) > 1:
            pending = _HYPHEN_END.sub("", t)
            continue
        out.append(t)
    if pending is not None:
        out.append(pending)
    return "\n".join(out)


def _piece_num(piece: str) -> int | None:
    m = re.match(r"(\d+)", piece)
    return int(m.group(1)) if m else None


@dataclass(slots=True)
class PieceText:
    """One printed piece's reading text and the pages (anchors) it spans."""

    piece: str
    lines: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)  # 0-based source page indices
    printed_pages: list[int] = field(default_factory=list)

    @property
    def text(self) -> str:
        return join_lines(self.lines)

    @property
    def n_chars(self) -> int:
        return len(self.text)


@dataclass(slots=True)
class VolumeText:
    """The assembled reading text of one volume, keyed by piece number."""

    pieces: dict[str, PieceText] = field(default_factory=dict)
    n_pages: int = 0
    n_eligible_pages: int = 0  # numbered-piece pages
    n_reading_pages: int = 0  # pages that contributed at least one reading line
    n_apparatus_lines: int = 0
    n_editorial_lines: int = 0
    anomalies: list[str] = field(default_factory=list)
    sizes: TypeSizes | None = None

    @property
    def n_chars(self) -> int:
        return sum(p.n_chars for p in self.pieces.values())


def assemble_pieces(pages: Iterable[PageReading], *, max_jump: int = 3) -> VolumeText:
    """Fold classified pages into per-piece reading text with page anchors.

    The current piece carries across page breaks: text before the first heading
    on a page belongs to it, an in-body heading switches to the new piece. The
    running head lists the pieces *starting* on the page (or the one continuing
    if none starts), which makes it the cross-check: a listed piece with no
    heading found means a boundary we cannot place, so the text after the last
    found heading is dropped rather than misattributed; a head naming a single
    piece that differs from the current one is a heading missed earlier — the
    page is dropped and the current piece re-synchronised. Headings on a page
    with no numbered head count only as a small forward step (that keeps tables
    of contents, indices and sigla lists out), and a heading far from the
    current piece is a false one. Pages before the first piece contribute
    nothing.
    """
    vol = VolumeText()
    current: str | None = None
    prev_head: str | None = None  # the previous page's head, for re-synchronisation
    prev_eligible = False  # the previous page was a piece page
    for pr in pages:
        vol.n_pages += 1
        vol.n_apparatus_lines += pr.n_apparatus
        vol.n_editorial_lines += pr.n_editorial
        cp = _piece_num(current or "")

        def _step_ok(candidate: str, cp: int | None = cp, lo: int = 0) -> bool:
            n = _piece_num(candidate)
            return n is not None and (cp is None or lo <= n - cp <= max_jump)

        headings = pr.headings
        if not pr.head_pieces and not any(
            _step_ok(h, cp if cp is not None else 0) for h in headings
        ):
            # No numbered head, no plausible heading: front/back matter — unless
            # the volume is set without running heads (a bare page number, or
            # nothing, up top) and we are mid-piece: then the page continues it.
            bare = pr.head_text is None or bool(
                re.fullmatch(r"[\divxlcIVXLC .]+", pr.head_text.strip())
            )
            if current is None or not prev_eligible or not bare:
                prev_eligible = False
                continue
        vol.n_eligible_pages += 1
        piece = current
        skip_lines = False
        if pr.head_pieces and not headings:
            named = pr.head_pieces[-1]
            if current is not None and _piece_num(named) == cp:
                pass  # plain continuation
            elif current is None or _step_ok(named):
                # A piece changed without a heading we could see: its start is
                # somewhere on this or the previous page — drop, re-synchronise.
                if current is not None:
                    vol.anomalies.append(f"page {pr.index}: missed heading for N.{named}")
                    skip_lines = True
                piece = named
            elif named == prev_head:
                # Two consecutive pages agree on a piece far from `current`: we
                # were the ones out of step (a garbled head earlier) — re-sync.
                vol.anomalies.append(f"page {pr.index}: re-synchronised to N.{named}")
                piece = named
            else:
                vol.anomalies.append(f"page {pr.index}: head N.{named} vs current {current}")
        found = {_piece_num(h) for h in headings}
        unplaced: list[str] = []
        if headings:
            for h in pr.head_pieces:
                if _piece_num(h) in found:
                    continue
                if _step_ok(h, lo=-2):
                    unplaced.append(h)
                else:  # an OCR-garbled head number: ignore, never re-sync to it
                    vol.anomalies.append(f"page {pr.index}: garbled head N.{h}")
        if unplaced:
            vol.anomalies.append(f"page {pr.index}: no heading found for N.{unplaced[0]}")
        last_heading_idx = max(
            (i for i, (k, _v) in enumerate(pr.events) if k == "heading"), default=-1
        )
        contributed = False
        for ei, (kind, value) in enumerate(pr.events):
            if kind == "heading":
                # A heading the head corroborates is accepted whatever the step;
                # otherwise it must be a small step from the current piece.
                if value in pr.head_pieces or _step_ok(value, _piece_num(piece or ""), lo=-2):
                    piece = value
                else:
                    vol.anomalies.append(f"page {pr.index}: implausible heading {value}")
                continue
            if piece is None or skip_lines or (unplaced and ei > last_heading_idx):
                continue
            pt = vol.pieces.setdefault(piece, PieceText(piece))
            pt.lines.append(value)
            if not pt.pages or pt.pages[-1] != pr.index:
                pt.pages.append(pr.index)
                if pr.printed_page is not None:
                    pt.printed_pages.append(pr.printed_page)
            contributed = True
        if contributed:
            vol.n_reading_pages += 1
        prev_eligible = True
        # The newest piece the head names is where the next page continues.
        current = unplaced[-1] if unplaced else piece
        prev_head = pr.head_pieces[-1] if pr.head_pieces else None
    return vol


def extract_volume(pages: Iterable[PageText]) -> VolumeText:
    """Classify every page and assemble the volume's per-piece reading text.

    Two passes: the volume's type sizes are learned first (so an editorial-heavy
    page cannot pass its apparatus off as body text), then every page is
    classified against them.
    """
    materialized = list(pages)
    sizes = learn_layout(materialized)
    vol = assemble_pieces(classify_pages(materialized, sizes=sizes))
    vol.sizes = sizes
    return vol


def classify_pages(pages: Iterable[PageText], *, sizes: TypeSizes | None) -> Iterator[PageReading]:
    """Classify pages in order, carrying the awaiting-body state across breaks."""
    awaiting = False
    for page in pages:
        pr = classify_page(page, sizes=sizes, awaiting_body=awaiting)
        awaiting = pr.ended_awaiting
        yield pr


__all__ = [
    "HEAD_PIECE_RE",
    "HEADING_RE",
    "PageReading",
    "PageText",
    "PieceText",
    "TextLine",
    "TypeSizes",
    "VolumeText",
    "assemble_pieces",
    "body_size",
    "classify_page",
    "classify_pages",
    "extract_volume",
    "head_pieces_of",
    "heading_match",
    "indent_offset",
    "iter_hocr_pages",
    "iter_pdf_pages",
    "join_lines",
    "learn_layout",
    "size_threshold",
]
