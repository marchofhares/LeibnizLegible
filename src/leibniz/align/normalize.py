"""Alignment-time text normalization (Phase B2).

Retro-alignment matches two transcriptions of the *same* manuscript that were
made under very different conventions:

* the **HTR machine text** — diplomatic, noisy (~8% CER), preserving the
  scribe's abbreviations, long-s, u/v and i/j allography, and page dirt;
* the **edition reading text** — a critical *constitution* of the text that
  silently expands abbreviations, regularises orthography, drops struck-out
  passages, and modernises punctuation.

If we char-aligned those two verbatim, every one of those systematic
differences would score as an "error" and drown the real signal. So before the
dynamic-programming aligner (:mod:`leibniz.align.dp`) ever runs, both sides are
folded onto a common, deliberately *lossy* comparison alphabet: case-folded,
diacritics stripped, u≡v and i≡j, long-s→s, a small list of the commonest Latin
brevigraphs expanded, ligatures broken, punctuation dropped, whitespace
collapsed. What survives is close to "the letters a reader would sound out",
which is what actually matches across the two conventions.

The one non-obvious requirement: the aligner must be able to hand back a slice
of the **original** edition text (accents, capitals, punctuation intact — that
is the ground truth we mint), even though it computed the alignment on the
folded form. So :func:`normalize_indexed` returns, alongside the folded string,
a ``src`` array mapping every folded character back to the index in the original
string it came from. :mod:`leibniz.align.align` uses it to project folded-space
line boundaries back onto original-space substrings.

Pure, deterministic, dependency-free — the whole module is offline-testable.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field, replace

# --------------------------------------------------------------------------- #
# Latin abbreviation / brevigraph expansion — a deliberately SMALL rule list
# --------------------------------------------------------------------------- #

# Multi-character folds applied on the *raw* string before decomposition. Keys
# are matched greedily longest-first. These are the high-frequency, low-ambiguity
# early-modern Latin abbreviations and ligatures; the point is not exhaustive
# expansion (that is a research project of its own — see the report's
# "normalization gaps" taxonomy) but to remove the handful of substitutions that
# otherwise cost an alignment several edits per line. Everything here maps to the
# *folded* comparison alphabet (lowercase, u for u/v, i for i/j), so e.g. "que"
# is stored as "que" and "et" as "et".
LATIN_ABBREVIATIONS: dict[str, str] = {
    # Ampersand & tironian et → "et"
    "&": "et",
    "⁊": "et",  # tironian et (U+204A)
    # Common ligatures (NFKD would split some of these, but not all fonts/points)
    "æ": "ae",  # æ
    "Æ": "ae",  # Æ
    "œ": "oe",  # œ
    "Œ": "oe",  # Œ
    "ß": "ss",  # ß (rare in Latin, common in the German stratum)
    # Long s and the r-rotunda, folded to their modern letters
    "ſ": "s",  # ſ long s
    "ꝛ": "r",  # ꝛ r rotunda
    # Enclitic -que written qₑ / q; / q: → "que"
    "q́": "que",
    "q;": "que",
    "q̣": "que",
}

# Combining marks that, over a letter, most often abbreviate a following nasal
# (m/n) or 'ur'/'us'/'is' — genuinely ambiguous. The prototype does NOT try to
# guess the expansion; it simply drops the mark (see ``strip_combining``) and
# lets the aligner absorb the one-character difference against the edition's
# spelled-out form. Which nasal it was is recorded nowhere reliable, so guessing
# would inject errors into minted ground truth. This choice is measured in the
# report (it is a real, bounded source of per-line edits).


@dataclass(frozen=True, slots=True)
class AlignNorm:
    """A frozen, named normalization recipe for the *alignment* comparison space.

    Distinct from :class:`leibniz.htr.metrics.NormPolicy` (which scores final
    CER and preserves case/diacritics on purpose): this one is intentionally
    lossy, because folding away systematic edition/diplomatic differences is the
    whole job. Order of operations is fixed and documented in :func:`_fold`.
    """

    name: str = "align-default"
    expand_abbreviations: bool = True
    fold_uv: bool = True  # u ≡ v  (early-modern allography)
    fold_ij: bool = True  # i ≡ j
    strip_combining: bool = True  # drop accents / brevigraph macrons & tildes
    lowercase: bool = True
    drop_punctuation: bool = True  # punctuation → space (edition repunctuates)
    collapse_whitespace: bool = True
    # Tokens the edition silently omits: struck-out passages are marked in the
    # PHILIUMM diplomatic GT as runs of 'x'. When comparing against an edition
    # reading text these have no counterpart; folding them to nothing lets the
    # aligner skip them cleanly instead of paying a deletion per struck word.
    deletion_tokens: tuple[str, ...] = ("xxx", "xx")
    abbreviations: dict[str, str] = field(default_factory=lambda: dict(LATIN_ABBREVIATIONS))

    def with_options(self, **kw: object) -> AlignNorm:
        """Return a copy with some fields overridden (keeps it frozen/hashable)."""
        return replace(self, **kw)  # type: ignore[arg-type]


# The default recipe used across the aligner and reported by name.
DEFAULT_NORM = AlignNorm()

# A conservative recipe that keeps struck-out 'xx' tokens (for the "diplomatic
# upper bound" evaluation condition where the reference is the diplomatic text
# verbatim, so the deletions are present on both sides and must NOT be dropped).
DIPLOMATIC_NORM = AlignNorm(name="align-diplomatic", deletion_tokens=())


# --------------------------------------------------------------------------- #
# The folding core
# --------------------------------------------------------------------------- #

_PUNCT_CATEGORIES = {"P", "S"}  # Unicode major categories: punctuation, symbol


def _is_punct(ch: str) -> bool:
    return unicodedata.category(ch)[0] in _PUNCT_CATEGORIES


def normalize_indexed(text: str, norm: AlignNorm = DEFAULT_NORM) -> tuple[str, list[int]]:
    """Fold ``text`` to the comparison alphabet, tracking source offsets.

    Returns ``(folded, src)`` where ``folded`` is the normalized string and
    ``src`` is a list of the same length: ``src[k]`` is the index into the
    *original* ``text`` that produced ``folded[k]``. Multi-character expansions
    (``&`` → ``et``) point every output character at the single source index;
    dropped characters (combining marks, extra whitespace) contribute nothing to
    ``src``. The map lets the aligner slice original text at folded-space
    boundaries (see :func:`leibniz.align.align.project_lines`).

    The fixed order (each step justified in the module docstring):
      1. optional abbreviation / ligature expansion (longest-match, on raw text),
      2. optional deletion-token elision (struck 'xx' runs → nothing),
      3. Unicode NFD decomposition,
      4. optional combining-mark strip,
      5. optional case fold,
      6. optional u≡v and i≡j fold,
      7. optional punctuation → space,
      8. optional whitespace collapse (runs → one space, ends trimmed).
    """
    out: list[str] = []
    src: list[int] = []

    # Steps 1-2 operate on the raw text and can consume multiple source chars or
    # emit multiple output chars, so they are done in a single left-to-right scan
    # that keeps ``src`` honest.
    abbrevs = norm.abbreviations if norm.expand_abbreviations else {}
    # Longest keys first so "q;" wins over "q", "xxx" over "xx".
    abbrev_keys = sorted(abbrevs, key=len, reverse=True)
    del_tokens = sorted(norm.deletion_tokens, key=len, reverse=True)

    i = 0
    n = len(text)
    while i < n:
        # deletion tokens: match on a word boundary-ish basis (case-insensitive
        # run of the marker), consume without emitting.
        matched = False
        for tok in del_tokens:
            if _matches_deletion(text, i, tok):
                i += len(tok)
                matched = True
                break
        if matched:
            continue
        # abbreviation / ligature expansion
        for key in abbrev_keys:
            if key and text.startswith(key, i):
                for ch in abbrevs[key]:
                    out.append(ch)
                    src.append(i)
                i += len(key)
                matched = True
                break
        if matched:
            continue
        out.append(text[i])
        src.append(i)
        i += 1

    # Steps 3-8 are per-character transforms on the (folded1, src1) stream.
    folded1 = out
    src1 = src

    # 3. NFD decomposition — expands each char to base + combining marks. Track
    #    offsets across the 1→many expansion.
    dec_chars: list[str] = []
    dec_src: list[int] = []
    for ch, s in zip(folded1, src1, strict=True):
        for d in unicodedata.normalize("NFD", ch):
            dec_chars.append(d)
            dec_src.append(s)

    final_chars: list[str] = []
    final_src: list[int] = []
    for ch, s in zip(dec_chars, dec_src, strict=True):
        # 4. strip combining marks
        if norm.strip_combining and unicodedata.combining(ch):
            continue
        # 5. case fold
        if norm.lowercase:
            ch = ch.lower()
        # 6. u/v and i/j folds (after lowercasing so both cases are covered)
        if norm.fold_uv and ch == "v":
            ch = "u"
        if norm.fold_ij and ch == "j":
            ch = "i"
        # 7. punctuation → space
        if norm.drop_punctuation and _is_punct(ch):
            ch = " "
        final_chars.append(ch)
        final_src.append(s)

    if not norm.collapse_whitespace:
        return "".join(final_chars), final_src

    # 8. collapse whitespace runs to a single space and trim ends, keeping src.
    coll_chars: list[str] = []
    coll_src: list[int] = []
    prev_space = True  # leading spaces are trimmed (start "in a space run")
    for ch, s in zip(final_chars, final_src, strict=True):
        if ch.isspace():
            if prev_space:
                continue
            coll_chars.append(" ")
            coll_src.append(s)
            prev_space = True
        else:
            coll_chars.append(ch)
            coll_src.append(s)
            prev_space = False
    # trailing space
    while coll_chars and coll_chars[-1] == " ":
        coll_chars.pop()
        coll_src.pop()
    return "".join(coll_chars), coll_src


def _matches_deletion(text: str, i: int, tok: str) -> bool:
    """True if ``tok`` (a run of the deletion marker) sits at ``i`` as a token.

    The PHILIUMM GT writes struck text as runs of lowercase 'x' delimited by
    whitespace/edges; we only elide such a run when it is bounded (so a genuine
    word containing 'xx' is not eaten). Matched case-insensitively.
    """
    seg = text[i : i + len(tok)]
    if seg.lower() != tok.lower():
        return False
    before = text[i - 1] if i > 0 else " "
    after = text[i + len(tok)] if i + len(tok) < len(text) else " "
    return not before.isalnum() and not after.isalnum()


def normalize(text: str, norm: AlignNorm = DEFAULT_NORM) -> str:
    """Folded form of ``text`` only (drops the source map). Convenience wrapper."""
    return normalize_indexed(text, norm)[0]


__all__ = [
    "DEFAULT_NORM",
    "DIPLOMATIC_NORM",
    "LATIN_ABBREVIATIONS",
    "AlignNorm",
    "normalize",
    "normalize_indexed",
]
