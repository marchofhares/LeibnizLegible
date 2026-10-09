"""Name the failure patterns behind a judged audit sheet (C2b, 2026-10-07).

The PHILIUMM team returned the 200-line hand audit (``align/audit.py``) with a
verdict per line and, on 86 lines, a note in English or French. A verdict says
*whether* the minted text is the line's text; the note says *why not*. This
module turns the pair into one named pattern per judged line, so the mint can
be measured for each pattern's reach (``audit_reach.py``) and C3 can exclude or
repair what the audit found.

Every rule reads only what the sheet carries — verdict, note, minted text, HTR
machine text — plus the aligner's own constants, so the module is pure and
tested on synthetic rows. The notes are free text, so the keyword rules match
conservatively; a row the rules cannot decide is ``other`` and goes to a
committed override CSV (``ref, pattern, why``) for a person to settle.

**One pattern per row, by precedence** (the first rule that fires wins; every
rule that fired is kept in ``signals``):

1. ``unreadable`` — the auditors could not tell.
2. ``addition`` — the note names an interlinear or marginal addition rendered
   inline (the edition prints the final state, the image shows a separate
   line), or, on a *wrong* verdict, the minted text exceeds the HTR reading
   in folded length by more than the aligner's insertion floor.
3. ``math`` — the note names a formula, or the minted text's density of
   mathematical characters is above the cut (:func:`math_density`).
4. ``bracket`` — an editorial bracket (``[``/``]``) leaked from the edition's
   apparatus or emendation into the minted text (``droit[e]``, ``[p. 76]``).
5. ``hyphen`` — the HTR line ends in a hyphen mark and the minted text ends in
   a letter (the word was split and the mint dropped the scribe's hyphen), or
   the note says the hyphen is missing. Named on *correct* verdicts only: a
   *boundary* line is named by its boundary, a *wrong* one by its cause; the
   signal is kept either way.
6. ``boundary-letter`` — the verdict is *boundary*, or a correction in the
   note differs from the minted text only at one end.
7. ``reading`` — the note gives a different reading of the same word in the
   middle of the line (``Casal`` for ``Casai``): an emendation or a disputed
   letter, not a misalignment.
8. ``normalization`` — the note objects to an accent, a capital, a comma or
   another mark the edition regularises (the reading text is not diplomatic),
   or a correction in the note is the minted word with a different accent or
   case (identical once folded), or the edit is a punctuation mark.
9. ``correct`` — a *correct* verdict with nothing else to say.
10. ``other`` — nothing above fired: on a *wrong* verdict, the one case left
    is a misaligned line.

The prompt that asked for this named ``hyphen``, ``boundary-letter``, ``math``,
``addition``, ``unreadable``, ``correct`` and ``other``; ``bracket``,
``normalization`` and ``reading`` were added because without them fifteen of the
sixteen *wrong* verdicts would have been ``other`` — and none of those fifteen
is a wrong line.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz.align import dp
from leibniz.align.align import HYPHENS, MAX_INSERT_FLOOR
from leibniz.align.normalize import normalize

PATTERNS = (
    "hyphen",
    "boundary-letter",
    "math",
    "addition",
    "bracket",
    "normalization",
    "reading",
    "unreadable",
    "correct",
    "other",
)
VERDICTS = ("correct", "boundary", "wrong", "unreadable")

# --- the math density cut (stated in the report) ----------------------------
# Operators and Greek letters are rare in prose, digits are not (dates, sums),
# so two cuts: operators + Greek alone, or all three together when at least one
# operator is present (a bare year is a date, not a formula). A single operator
# is never a formula (a short line with one "=" is prose, or a scribal line-end
# mark), and a hyphen mark closing the line is not counted at all.
MATH_OPS = set("+−–—=<>×÷·√∫∑∏∞±∝°′″^")
MATH_OPS_CUT = 0.10
MATH_ALL_CUT = 0.25
MATH_MIN_OPS = 2

# --- keyword sets (lower-cased, accents folded) ------------------------------
HYPHEN_WORDS = ("hyphen", "tiret", "trait d union")
MATH_WORDS = ("math", "formul", "equation", "cartesian", "algebra")
ADDITION_WORDS = (
    "addition",
    "ajout",
    "not visually on the same line",
    "separate line",
    "interlin",
    "marginal",
    "en marge",
)
NORMALIZATION_WORDS = (
    "accent",
    "moderni",
    "capital",
    "majuscule",
    "minuscule",
    "lower case",
    "lowercase",
    "upper case",
    "uppercase",
    "comma",
    "virgule",
    "punctuation",
    "ponctuation",
    "apostrophe",
    "spelling",
    "orthograph",
    "full stop",
    "semicolon",
    "symbol mismatch",
)
UNREADABLE_WORDS = ("cannot decipher", "cannot read", "can't read", "illisible")
# How many characters at an end still count as a boundary slip (the auditors'
# "a letter missing at the beginning or one added at the end"; ``l'`` is two).
BOUNDARY_MAX_CHARS = 3
# A correction is "the same word read differently" when its folded form is at
# least this similar to the minted word and the lengths are comparable; below
# that, the minted word is not the one on the line.
READING_MIN_SIM = 0.5
READING_MIN_LEN_RATIO = 0.6


def fold_note(note: str) -> str:
    """Lower-case, accent-free, single-spaced text for keyword matching."""
    t = unicodedata.normalize("NFD", note or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace("’", "'").replace("'", " ")
    return " ".join(t.lower().split())


def mentions(note: str, words: Iterable[str]) -> bool:
    folded = fold_note(note)
    return any(w in folded for w in words)


def math_density(text: str) -> tuple[float, float]:
    """``(operators + Greek, digits + operators + Greek)`` as shares of the
    non-space characters. A lone ``-`` counts as an operator only when it
    stands apart from words (``x - y``), since it is also the hyphen of prose;
    a hyphen mark closing the line is not counted at all."""
    core = text.rstrip()
    if core and core[-1] in HYPHENS:
        core = core[:-1]
    chars = [c for c in core if not c.isspace()]
    if not chars:
        return 0.0, 0.0
    ops = sum(1 for c in chars if c in MATH_OPS or "\u0370" <= c <= "\u03ff")
    ops += len(re.findall(r"(?:^|\s)-(?:\s|$)", core))
    digits = sum(1 for c in chars if c.isdigit())
    n = len(chars)
    return ops / n, (ops + digits) / n


def is_math_dense(text: str) -> bool:
    ops, all_ = math_density(text)
    n = len([c for c in text.rstrip() if not c.isspace()])
    if round(ops * n) < MATH_MIN_OPS:
        return False
    return ops >= MATH_OPS_CUT or all_ >= MATH_ALL_CUT


def ends_in_letter(text: str) -> bool:
    t = text.rstrip()
    return bool(t) and t[-1].isalpha()


def htr_ends_hyphenated(htr_text: str | None) -> bool:
    t = (htr_text or "").rstrip()
    return bool(t) and t[-1] in HYPHENS


def has_bracket(text: str) -> bool:
    return "[" in text or "]" in text


# --------------------------------------------------------------------------- #
# Corrections carried by the notes
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Correction:
    """One edit the note asks for.

    ``replace``: ``minted`` → ``corrected``; ``insert``: add ``corrected``;
    ``delete``: drop ``minted``; ``line``: ``corrected`` is the whole line as
    the auditors read it. ``where`` locates an insert or delete: ``start``,
    ``end``, ``before:<anchor>``, ``after:<anchor>`` or ``""`` (the fragment
    must then occur exactly once).
    """

    op: str
    minted: str
    corrected: str
    where: str = ""


_Q = r'"([^"]+)"'
_SEP = r"[;.]|$"  # a clause ends at a semicolon, a full stop or the note's end
_RE_LINE = re.compile(
    r'^\s*(?:correct boundary\s*:?\s*|we read\s*|should be\s*|it reads\s*)?"([^"]+)"[\s.]*$',
    re.IGNORECASE,
)
_RE_TRANSCRIBED = re.compile(_Q + r"\s*is transcribed as\s*" + _Q, re.IGNORECASE)
_RE_ARROW_MISSING = re.compile(_Q + r"\s*(?:->|→)\s*missing\s*" + _Q, re.IGNORECASE)
_RE_ARROW_LETTER = re.compile(
    _Q + r"\s*(?:->|→)\s*" + _Q + r"\s*(initial|first|last|final)\s+letter\s+missing", re.IGNORECASE
)
_RE_INSTEAD = re.compile(r"(?:we read\s*)?" + _Q + r"\s*instead of\s*" + _Q, re.IGNORECASE)
_RE_ARROW = re.compile(_Q + r"\s*(?:->|→|=>)\s*" + _Q)
_RE_ADDED = re.compile(r"added\s*" + _Q + r"(?:\s*after\s*" + _Q + r")?", re.IGNORECASE)
_RE_MISSING = re.compile(
    r"missing\s*(?:part of the word\s*)?"
    + _Q
    + r"(?:\s*(?:(?:at|in)(?:\s+the\s+(?:end|beginning|start)\s+(?:in|at))?(?:\s+the\s+word)?\s*"
    + _Q
    + r"|before\s*"
    + _Q
    + r"|after\s*"
    + _Q
    + r"|at the (end|beginning|start)))?",
    re.IGNORECASE,
)
_RE_MISSING_AT = re.compile(
    _Q + r"\s*(?:is\s*)?missing(?:\s*at the (beginning|start|end))?", re.IGNORECASE
)
_RE_NOT_SEE = re.compile(r"(?:do not|don't|cannot|can't) see\s*(?:the\s*)?" + _Q, re.IGNORECASE)
_RE_NOT_THERE = re.compile(
    r"(?:(just|last|final|first|initial)\s+)?"
    + _Q
    + r"\s*(?:(?:->|→)\s*)?(?:at the (?:end|beginning|start)(?: of the line)?\s*)?(?:is\s*)?"
    r"(?:should\s*(?:n[o']t|not)\b|shouldn't|not present|not on the line|not visually)",
    re.IGNORECASE,
)
_RE_NO = re.compile(
    r"(?:^|[;:,.]\s*|\s)no\s*" + _Q + r"(?:\s*at the (end|beginning|start))?", re.IGNORECASE
)
_RE_END = re.compile(r"at the end|last\b|final\b", re.IGNORECASE)
_RE_START = re.compile(r"at the (?:beginning|start)|first\b|initial\b", re.IGNORECASE)


def _position(clause: str) -> str:
    if _RE_END.search(clause):
        return "end"
    if _RE_START.search(clause):
        return "start"
    return ""


def _clause_after(text: str, end: int) -> str:
    """The rest of the clause after offset ``end`` (up to ``;`` or ``.``)."""
    m = re.search(_SEP, text[end:])
    return text[end : end + (m.start() if m else len(text) - end)]


def _without(word: str, part: str, minted_text: str, *, where: str = "") -> str | None:
    """``word`` with one occurrence of ``part`` removed — the occurrence whose
    result occurs in the minted text (``missing "s" at "oserois"`` → ``oseroi``)."""
    if where == "start" and word.startswith(part):
        return word[len(part) :]
    if where == "end" and word.endswith(part):
        return word[: -len(part)]
    cands: list[str] = []
    i = word.find(part)
    while i >= 0:
        cands.append(word[:i] + word[i + len(part) :])
        i = word.find(part, i + 1)
    for c in cands:
        if c and _locate(minted_text, c) is not None:
            return c
    return cands[0] if cands else None


def extract_corrections(note: str, minted_text: str = "") -> list[Correction]:
    """The edits a note spells out, conservatively (quoted fragments only).

    ``minted_text`` only helps disambiguate ``missing "s" at "oserois"``: which
    ``s`` of the word is the missing one.
    """
    text = (note or "").replace("“", '"').replace("”", '"')
    out: list[Correction] = []
    seen: set[tuple[str, str, str]] = set()

    def add(c: Correction) -> None:
        key = (c.op, c.minted, c.corrected)
        if key not in seen and (c.minted or c.corrected):
            seen.add(key)
            out.append(c)

    m = _RE_LINE.match(text)
    if m is not None:
        add(Correction("line", "", m.group(1)))
        return out

    consumed = text
    for m in _RE_TRANSCRIBED.finditer(text):  # "<read>" is transcribed as "<minted>"
        add(Correction("replace", m.group(2), m.group(1)))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_ARROW_LETTER.finditer(consumed):  # "Christus" -> "C" initial letter missing
        word, letter, which = m.groups()
        where = "start" if which.lower() in ("initial", "first") else "end"
        short = _without(word, letter, minted_text, where=where)
        if short:
            add(Correction("replace", short, word))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_ARROW_MISSING.finditer(consumed):  # "Roy" -> missing "y": minted "Ro"
        word, part = m.group(1), m.group(2)
        short = _without(word, part, minted_text)
        if short:
            add(Correction("replace", short, word))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_INSTEAD.finditer(consumed):  # "<read>" instead of "<minted>"
        add(Correction("replace", m.group(2), m.group(1)))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_ARROW.finditer(consumed):  # "<minted>" -> "<read>"
        add(Correction("replace", m.group(1), m.group(2)))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_ADDED.finditer(consumed):  # added "," after "inter se"
        frag, anchor = m.groups()
        add(Correction("delete", frag, "", f"after:{anchor}" if anchor else ""))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_MISSING.finditer(consumed):
        frag, within, before, after, pos = m.groups()
        clause = m.group(0)
        if within and frag in within:
            short = _without(within, frag, minted_text, where=_position(clause))
            if short:
                add(Correction("replace", short, within))
        elif before:
            add(Correction("insert", "", frag, f"before:{before}"))
        elif after:
            add(Correction("insert", "", frag, f"after:{after}"))
        elif pos:
            add(Correction("insert", "", frag, "end" if pos.lower() == "end" else "start"))
        else:
            add(Correction("insert", "", frag, _position(_clause_after(consumed, m.end()))))
        consumed = consumed.replace(clause, " ")
    for m in _RE_MISSING_AT.finditer(consumed):
        frag, pos = m.groups()
        add(Correction("insert", "", frag, "start" if pos and pos != "end" else (pos or "")))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_NOT_SEE.finditer(consumed):
        rest = _clause_after(consumed, m.end())
        am = re.match(r"\s*after\s*" + _Q, rest)
        where = f"after:{am.group(1)}" if am else _position(rest)
        add(Correction("delete", m.group(1), "", where))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_NOT_THERE.finditer(consumed):
        lead, frag = m.group(1), m.group(2)
        where = _position((lead or "") + " " + m.group(0) + _clause_after(consumed, m.end()))
        add(Correction("delete", frag, "", where))
        consumed = consumed.replace(m.group(0), " ")
    for m in _RE_NO.finditer(consumed):
        frag, pos = m.groups()
        add(Correction("delete", frag, "", _position(m.group(0)) or (pos or "").lower()))
    return out


def _variants(frag: str) -> list[str]:
    """The fragment as written and with the other apostrophe."""
    out = [frag]
    if "'" in frag:
        out.append(frag.replace("'", "’"))
    if "’" in frag:
        out.append(frag.replace("’", "'"))
    return out


def _locate(text: str, frag: str) -> str | None:
    """The spelling of ``frag`` that occurs exactly once in ``text``, or ``None``."""
    for v in _variants(frag):
        if v and text.count(v) == 1:
            return v
    return None


def _glue(a: str, b: str) -> str:
    """Join two pieces of text: a single letter continues a word, a word gets a space."""
    if not a or not b:
        return a + b
    if a[-1] in "'’-" or b[0] in "'’,.;:" or len(a) == 1 or len(b) == 1:
        return a + b
    return a + " " + b


def apply_correction(text: str, c: Correction) -> str | None:
    """``text`` with the edit applied, or ``None`` when the fragment cannot be
    located once and only once (the note is then kept, the line not corrected).
    Whitespace in ``text`` is collapsed first (a minted slice can span an
    edition line break)."""
    text = " ".join(text.split())
    if c.op == "line":
        return c.corrected
    if c.op == "insert":
        if c.where == "end":
            return _glue(text, c.corrected)
        if c.where == "start":
            return _glue(c.corrected, text)
        if c.where.startswith(("before:", "after:")):
            kind, anchor = c.where.split(":", 1)
            found = _locate(text, anchor)
            if found is None:
                return None
            repl = (c.corrected + " " + found) if kind == "before" else (found + " " + c.corrected)
            return text.replace(found, repl, 1)
        return None
    if c.op == "delete":
        frag = c.minted
        if c.where == "end":
            core = text.rstrip(" ,.;:")  # the mark after a dropped word goes with it
            for v in _variants(frag):
                if core.endswith(v):
                    return core[: -len(v)].rstrip()
            return None
        if c.where == "start":
            for v in _variants(frag):
                if text.startswith(v):
                    return text[len(v) :].lstrip()
            return None
        if c.where.startswith("after:"):
            anchor = _locate(text, c.where[6:])
            if anchor is None:
                return None
            i = text.index(anchor) + len(anchor)
            for v in _variants(frag):
                if text[i:].lstrip().startswith(v):
                    j = i + (len(text[i:]) - len(text[i:].lstrip()))
                    return " ".join((text[:j] + text[j + len(v) :]).split())
            return None
        found = _locate(text, frag)
        if found is None:
            return None
        return " ".join(text.replace(found, " ", 1).split())
    found = _locate(text, c.minted)
    if found is None:
        return None
    return text.replace(found, c.corrected, 1)


def _edge_extent(minted: str, corrected: str) -> int | None:
    """Characters by which ``corrected`` extends or shortens ``minted`` at one
    end (``None`` when the difference is not confined to an end)."""
    a, b = minted.strip(), corrected.strip()
    if a == b:
        return 0
    if b.startswith(a) or b.endswith(a):
        return len(b) - len(a)
    if a.startswith(b) or a.endswith(b):
        return len(a) - len(b)
    return None


def _is_punct_only(frag: str) -> bool:
    return bool(frag.strip()) and all(not ch.isalnum() for ch in frag.strip())


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PatternRow:
    ref: str
    stratum: str
    verdict: str
    pattern: str
    why: str
    signals: list[str] = field(default_factory=list)
    note: str = ""
    gt_text: str = ""
    htr_text: str = ""
    similarity: float = 0.0  # folded minted ↔ HTR
    corrections: list[Correction] = field(default_factory=list)
    overridden: bool = False

    @property
    def undecided(self) -> bool:
        return self.pattern == "other" and not self.overridden


def classify(
    ref: str,
    stratum: str,
    verdict: str,
    note: str,
    gt_text: str,
    htr_text: str | None,
) -> PatternRow:
    """One pattern for one judged line (see the module docstring for the rules)."""
    verdict = (verdict or "").strip().lower()
    note = note or ""
    htr = htr_text or ""
    g = normalize(gt_text)
    h = normalize(htr)
    sim = dp.similarity(g, h) if g and h else 0.0
    corrections = extract_corrections(note, gt_text)
    signals: list[str] = []
    reasons: dict[str, str] = {}

    def hit(name: str, why: str) -> None:
        if name not in signals:
            signals.append(name)
            reasons[name] = why

    if verdict == "unreadable":
        hit("unreadable", "the auditors could not tell")
    elif mentions(note, UNREADABLE_WORDS):
        hit("unreadable-note", "the note says part of the line could not be read")
    if mentions(note, ADDITION_WORDS):
        hit("addition", "the note names an addition rendered inline")
    elif verdict == "wrong" and len(g) - len(h) > MAX_INSERT_FLOOR:
        hit(
            "addition",
            f"minted text exceeds the HTR reading by {len(g) - len(h)} folded characters "
            f"(> insertion floor {MAX_INSERT_FLOOR})",
        )
    ops, all_ = math_density(gt_text)
    if mentions(note, MATH_WORDS):
        hit("math", "the note names a formula")
    elif is_math_dense(gt_text):
        hit("math", f"mathematical characters {100 * ops:.0f} % / with digits {100 * all_:.0f} %")
    if has_bracket(gt_text):
        hit("bracket", "an editorial bracket in the minted text")
    hy_mech = htr_ends_hyphenated(htr) and ends_in_letter(gt_text)
    hy_note = mentions(note, HYPHEN_WORDS)
    if hy_mech and hy_note:
        hit(
            "hyphen",
            f"HTR line ends in {htr.rstrip()[-1]!r}, the minted text in a letter; the note says so",
        )
    elif hy_mech:
        hit("hyphen", f"HTR line ends in {htr.rstrip()[-1]!r} and the minted text in a letter")
    elif hy_note:
        hit("hyphen-note", "the note names a missing hyphen the HTR did not read either")
    if verdict == "boundary":
        hit("boundary-letter", "boundary verdict")
    for c in corrections:
        frag = c.minted or c.corrected
        if c.op == "line":
            continue  # the whole line as read: measured in the corrections table
        if c.op == "replace":
            ext = _edge_extent(c.minted, c.corrected)
            fm, fc = normalize(c.minted), normalize(c.corrected)
            if ext is not None and 0 < ext <= BOUNDARY_MAX_CHARS:
                hit(
                    "boundary-letter",
                    f"{c.minted!r} → {c.corrected!r}: {ext} character(s) at an end",
                )
            elif fm == fc:
                hit("normalization", f"{c.minted!r} and {c.corrected!r} fold to the same word")
            elif ext is None:
                ratio = min(len(fm), len(fc)) / max(len(fm), len(fc), 1)
                if dp.similarity(fm, fc) >= READING_MIN_SIM and ratio >= READING_MIN_LEN_RATIO:
                    hit("reading", f"the note reads {c.corrected!r} for {c.minted!r}")
                else:
                    hit(
                        "misaligned",
                        f"the note reads {c.corrected!r} where the mint has {c.minted!r}",
                    )
        elif _is_punct_only(frag):
            hit(
                "normalization",
                f"a mark the edition {'added' if c.op == 'delete' else 'dropped'}: {frag!r}",
            )
        elif len(frag) <= BOUNDARY_MAX_CHARS and c.where in ("start", "end", ""):
            hit("boundary-letter", f"{c.op} {frag!r} at an end")
        elif c.where in ("start", "end"):
            hit("boundary-word", f"{c.op} {frag!r} at the {c.where}")
    if mentions(note, NORMALIZATION_WORDS):
        hit("normalization", "the note objects to a mark the edition regularises")
    if verdict == "correct":
        hit("correct", "correct verdict")

    pattern, why = _pick(verdict, signals, reasons)
    return PatternRow(
        ref=ref,
        stratum=stratum or "unknown",
        verdict=verdict,
        pattern=pattern,
        why=why,
        signals=signals,
        note=note,
        gt_text=gt_text,
        htr_text=htr,
        similarity=sim,
        corrections=corrections,
    )


_PRECEDENCE = (
    "unreadable",
    "addition",
    "math",
    "bracket",
    "hyphen",
    "hyphen-note",
    "boundary-letter",
    "boundary-word",
    "reading",
    "normalization",
    "correct",
)


def _pick(verdict: str, signals: Sequence[str], reasons: dict[str, str]) -> tuple[str, str]:
    for name in _PRECEDENCE:
        if name not in signals:
            continue
        if name in ("hyphen", "hyphen-note") and verdict != "correct":
            continue  # a boundary line is first a boundary line; on a wrong one it is incidental
        if name == "correct" and verdict != "correct":
            continue
        if name == "hyphen-note":
            return "hyphen", reasons[name]
        if name == "boundary-word":
            return "boundary-letter", reasons[name]
        return name, reasons[name]
    if "misaligned" in signals:
        return "other", reasons["misaligned"]
    return "other", "no rule applies"


def classify_rows(
    verdict_rows: Sequence[dict[str, str]], lines: dict[str, dict[str, str]]
) -> list[PatternRow]:
    """Classify every judged verdict row that is on the sheet (``lines`` by ref)."""
    out: list[PatternRow] = []
    for r in verdict_rows:
        verdict = (r.get("verdict") or "").strip().lower()
        ln = lines.get(r.get("ref", ""))
        if verdict not in VERDICTS or ln is None:
            continue
        out.append(
            classify(
                r["ref"],
                (r.get("stratum") or ln.get("stratum") or "unknown").strip(),
                verdict,
                r.get("note") or "",
                ln.get("gt_text") or "",
                ln.get("htr_text") or "",
            )
        )
    return out


def read_lines_csv(path: Path) -> dict[str, dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        return {r["ref"]: r for r in csv.DictReader(fh)}


def read_overrides(path: Path) -> dict[str, tuple[str, str]]:
    """``ref -> (pattern, why)`` from the committed override CSV."""
    if not Path(path).exists():
        return {}
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out: dict[str, tuple[str, str]] = {}
    for r in rows:
        pat = (r.get("pattern") or "").strip()
        if pat and pat not in PATTERNS:
            raise ValueError(f"override for {r.get('ref')!r} names unknown pattern {pat!r}")
        if pat:
            out[r["ref"]] = (pat, (r.get("why") or "").strip())
    return out


def apply_overrides(rows: Sequence[PatternRow], overrides: dict[str, tuple[str, str]]) -> int:
    n = 0
    for row in rows:
        if row.ref in overrides:
            pat, why = overrides[row.ref]
            row.pattern, row.why, row.overridden = pat, f"override: {why}", True
            n += 1
    return n


# --------------------------------------------------------------------------- #
# Corrections table: the normalization tax, measured
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class CorrectionRow:
    ref: str
    stratum: str
    verdict: str
    pattern: str
    minted_text: str
    edits: str  # human-readable list of the edits
    corrected_text: str  # "" when an edit could not be located
    sim_raw: float | None  # character similarity, accents and case kept
    sim_folded: float | None  # under the aligner's fold


def corrections_table(rows: Sequence[PatternRow]) -> list[CorrectionRow]:
    out: list[CorrectionRow] = []
    for row in rows:
        if not row.corrections:
            continue
        text: str | None = row.gt_text
        for c in row.corrections:
            text = apply_correction(text, c) if text is not None else None
        edits = "; ".join(_describe(c) for c in row.corrections)
        if text is None or text == row.gt_text:
            out.append(
                CorrectionRow(
                    row.ref,
                    row.stratum,
                    row.verdict,
                    row.pattern,
                    row.gt_text,
                    edits,
                    "",
                    None,
                    None,
                )
            )
            continue
        a, b = unicodedata.normalize("NFC", row.gt_text), unicodedata.normalize("NFC", text)
        sim_raw = dp.similarity(a, b)
        fa, fb = normalize(a), normalize(b)
        sim_folded = dp.similarity(fa, fb) if fa or fb else 1.0
        out.append(
            CorrectionRow(
                row.ref,
                row.stratum,
                row.verdict,
                row.pattern,
                row.gt_text,
                edits,
                text,
                sim_raw,
                sim_folded,
            )
        )
    return out


def _describe(c: Correction) -> str:
    if c.op == "line":
        return f"reads {c.corrected!r}"
    if c.op == "replace":
        return f"{c.minted!r} → {c.corrected!r}"
    if c.op == "insert":
        return f"+{c.corrected!r}" + (f" ({c.where})" if c.where else "")
    return f"−{c.minted!r}" + (f" ({c.where})" if c.where else "")


# --------------------------------------------------------------------------- #
# Counting and rendering
# --------------------------------------------------------------------------- #


def pattern_counts(rows: Sequence[PatternRow]) -> dict[str, dict[str, int]]:
    """``stratum -> pattern -> count`` (plus an ``all`` stratum)."""
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        for key in (row.stratum, "all"):
            out.setdefault(key, {})
            out[key][row.pattern] = out[key].get(row.pattern, 0) + 1
    return out


def by_verdict(rows: Sequence[PatternRow]) -> dict[str, dict[str, int]]:
    """``verdict -> pattern -> count``."""
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        out.setdefault(row.verdict, {})
        out[row.verdict][row.pattern] = out[row.verdict].get(row.pattern, 0) + 1
    return out


def write_patterns_csv(rows: Sequence[PatternRow], path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "stratum", "verdict", "pattern", "signals", "why", "similarity", "note"])
        for r in rows:
            w.writerow(
                [
                    r.ref,
                    r.stratum,
                    r.verdict,
                    r.pattern,
                    ";".join(r.signals),
                    r.why,
                    f"{r.similarity:.3f}",
                    r.note,
                ]
            )


def write_corrections_csv(rows: Sequence[CorrectionRow], path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "ref",
                "stratum",
                "verdict",
                "pattern",
                "minted_text",
                "edits",
                "corrected_text",
                "sim_raw",
                "sim_folded",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.ref,
                    r.stratum,
                    r.verdict,
                    r.pattern,
                    r.minted_text,
                    r.edits,
                    r.corrected_text,
                    "" if r.sim_raw is None else f"{r.sim_raw:.3f}",
                    "" if r.sim_folded is None else f"{r.sim_folded:.3f}",
                ]
            )


def write_override_template(rows: Sequence[PatternRow], path: Path) -> int:
    """Write the undecided rows to the override CSV if it does not exist yet."""
    und = [r for r in rows if r.undecided]
    p = Path(path)
    if p.exists() or not und:
        return len(und)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "pattern", "why"])
        for r in und:
            w.writerow([r.ref, "", ""])
    return len(und)


def _pct(k: int, n: int) -> str:
    return "—" if not n else f"{100 * k / n:.0f} %"


def render_patterns(rows: Sequence[PatternRow], *, strata: Sequence[str]) -> list[str]:
    """Markdown lines: the pattern table per stratum, by verdict, and the rules."""
    counts = pattern_counts(rows)
    bv = by_verdict(rows)
    present = [p for p in PATTERNS if any(counts[s].get(p) for s in counts)]
    out: list[str] = []
    A = out.append
    A("## Patterns: why a minted line is not the line's text")
    A("")
    n_notes = sum(1 for r in rows if r.note.strip())
    n_over = sum(1 for r in rows if r.overridden)
    A(
        f"One pattern per judged line, from the verdict, the note ({n_notes} lines carry one), "
        f"the minted text and the HTR reading, by the rules listed below ({n_over} "
        f"settled by the override file). Counts are lines; the share is of the stratum's "
        f"judged lines."
    )
    A("")
    A("| stratum | judged | " + " | ".join(present) + " |")
    A("|---|---:|" + "---:|" * len(present))
    order = [s for s in strata if s in counts] + sorted(set(counts) - set(strata) - {"all"})
    for s in [*order, "all"]:
        c = counts.get(s, {})
        n = sum(c.values())
        cells = [f"{c.get(p, 0)} ({_pct(c.get(p, 0), n)})" if c.get(p) else "0" for p in present]
        label = "**all**" if s == "all" else s
        A(f"| {label} | {n} | " + " | ".join(cells) + " |")
    A("")
    A("By verdict (what the auditors called the line, and what the pattern says it is):")
    A("")
    A("| verdict | n | " + " | ".join(present) + " |")
    A("|---|---:|" + "---:|" * len(present))
    for v in VERDICTS:
        c = bv.get(v)
        if not c:
            continue
        n = sum(c.values())
        A(
            f"| {v} | {n} | "
            + " | ".join(str(c.get(p, 0)) if c.get(p) else "0" for p in present)
            + " |"
        )
    A("")
    hy_any = sum(1 for r in rows if "hyphen-note" in r.signals or "hyphen" in r.signals)
    hy_mech = sum(1 for r in rows if "hyphen" in r.signals)
    hy_note_only = sum(1 for r in rows if "hyphen-note" in r.signals)
    hy_pat = sum(1 for r in rows if r.pattern == "hyphen")
    A(
        f"**Hyphens.** {hy_any} judged lines carry a hyphen signal ({hy_pat} named *hyphen*, "
        f"the rest *boundary* lines where the boundary comes first): on {hy_mech} the HTR line "
        f"ends in a hyphen mark the mint dropped (what `keep_hyphen` restores), on "
        f"{hy_note_only} the note says the hyphen is on the page but the HTR did not read it "
        f"either — those the fix cannot reach, since it keeps only what the HTR showed."
    )
    A("")
    A(
        "Rules, in order of precedence (the first that fires names the line; every rule that "
        "fired is in the per-line CSV):"
    )
    A("")
    A("1. *unreadable* — the verdict, or the note says the auditors could not read it.")
    A(
        f"2. *addition* — the note names an addition (keywords: {', '.join(ADDITION_WORDS)}), "
        f"or on a *wrong* verdict the minted text exceeds the HTR reading by more than "
        f"{MAX_INSERT_FLOOR} folded characters."
    )
    A(
        f"3. *math* — the note names a formula (keywords: {', '.join(MATH_WORDS)}), or "
        f"at least {MATH_MIN_OPS} mathematical operators or Greek letters make "
        f"≥ {100 * MATH_OPS_CUT:.0f} % of the minted text's non-space characters, or with "
        f"digits ≥ {100 * MATH_ALL_CUT:.0f} %. The "
        f"density misses inline algebra in prose (`ia yy x 2ax —` is 4 %); the note catches those."
    )
    A("4. *bracket* — the minted text carries an editorial bracket (`[` or `]`).")
    A(
        "5. *hyphen* — the HTR line ends in a hyphen mark and the minted text in a letter, or "
        "the note names a missing hyphen; on *correct* verdicts (a *boundary* line is named by "
        "its boundary, a *wrong* one by its cause)."
    )
    A(
        f"6. *boundary-letter* — a *boundary* verdict, or a correction in the note that differs "
        f"from the minted text by at most {BOUNDARY_MAX_CHARS} characters at one end."
    )
    A(
        f"7. *reading* — a correction in the middle of the line whose folded similarity to the "
        f"minted word is ≥ {READING_MIN_SIM} at a length ratio ≥ {READING_MIN_LEN_RATIO}: the "
        f"same word read differently."
    )
    A(
        "8. *normalization* — the note objects to an accent, capital, comma, apostrophe or "
        "spelling the edition regularises, a correction folds to the same word as the minted "
        "one, or the edit is a punctuation mark."
    )
    A("9. *correct* — a *correct* verdict with nothing else to say. 10. *other* — no rule fired.")
    return out


def render_corrections(table: Sequence[CorrectionRow]) -> list[str]:
    out: list[str] = []
    A = out.append
    A("## Corrections in the notes: the normalization tax, first sample")
    A("")
    located = [r for r in table if r.corrected_text]
    if not table:
        A("No note carries a correction.")
        return out
    A(
        f"{len(table)} notes spell out an edit to the minted text; on {len(located)} the edit "
        f"could be placed and the corrected line compared with the minted one. The table gives "
        f"the mean character distance minted → corrected per pattern, as written (accents and "
        f"case kept) and under the aligner's fold; the gap between the two columns is what the "
        f"fold hides and a diplomatic scorer charges: accents, capitals, punctuation. On the "
        f"*normalization* lines the folded distance is near zero by construction — that row is "
        f"the tax itself. These are the auditors' word-level corrections, not full "
        f"re-transcriptions, so every figure is a floor."
    )
    A("")
    A("| pattern | lines placed | mean distance, as written | mean distance, folded |")
    A("|---|---:|---:|---:|")
    groups: dict[str, list[CorrectionRow]] = {}
    for r in located:
        groups.setdefault(r.pattern, []).append(r)
    for pat in [*[p for p in PATTERNS if p in groups], "all"]:
        rs = located if pat == "all" else groups[pat]
        raw = [1 - r.sim_raw for r in rs if r.sim_raw is not None]
        fold = [1 - r.sim_folded for r in rs if r.sim_folded is not None]
        if not raw:
            continue
        label = "**all**" if pat == "all" else pat
        A(
            f"| {label} | {len(rs)} | {100 * sum(raw) / len(raw):.1f} % | "
            f"{100 * sum(fold) / len(fold):.1f} % |"
        )
    A("")
    A("| ref | stratum | verdict | pattern | minted text | edits | corrected text | raw | folded |")
    A("|---|---|---|---|---|---|---|---:|---:|")
    for r in table:
        raw = "—" if r.sim_raw is None else f"{r.sim_raw:.2f}"
        fold = "—" if r.sim_folded is None else f"{r.sim_folded:.2f}"
        A(
            f"| `{r.ref}` | {r.stratum} | {r.verdict} | {r.pattern} | {_cell(r.minted_text)} | "
            f"{_cell(r.edits)} | {_cell(r.corrected_text) or '(not placed)'} | {raw} | {fold} |"
        )
    return out


def _cell(text: str, limit: int = 60) -> str:
    t = text.replace("|", "\\|").replace("\n", " ")
    return t if len(t) <= limit else t[: limit - 1] + "…"


__all__ = [
    "BOUNDARY_MAX_CHARS",
    "MATH_ALL_CUT",
    "MATH_MIN_OPS",
    "MATH_OPS_CUT",
    "PATTERNS",
    "Correction",
    "CorrectionRow",
    "PatternRow",
    "apply_correction",
    "apply_overrides",
    "by_verdict",
    "classify",
    "classify_rows",
    "corrections_table",
    "extract_corrections",
    "math_density",
    "pattern_counts",
    "read_lines_csv",
    "read_overrides",
    "render_corrections",
    "render_patterns",
    "write_corrections_csv",
    "write_override_template",
    "write_patterns_csv",
]
