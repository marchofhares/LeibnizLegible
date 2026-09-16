"""Hit snippets with ``<mark>`` highlighting on the *original* text (Phase D1).

Both backends match on folded text; the reader wants the machine's own reading
with the hits marked. So the snippet is computed here, once, from the original
page text: fold it with the offset map, find the tokens a query term matches
(whole token; a term of ≥ :data:`PREFIX_MIN` characters matches as a prefix,
mirroring the FTS5 query builder), map the folded spans back to original
offsets, cut a window around the first hit, and HTML-escape everything except
the ``<mark>`` tags. The output is the only HTML the API ever emits.
"""

from __future__ import annotations

from html import escape

from leibniz.search.normalize import fold_indexed

PREFIX_MIN = 3
DEFAULT_WIDTH = 240
ELLIPSIS = "…"


def term_spans(folded: str, terms: list[str], *, prefix: bool = True) -> list[tuple[int, int]]:
    """Folded-space ``[start, end)`` spans of tokens matching any term."""
    spans: list[tuple[int, int]] = []
    i, n = 0, len(folded)
    while i < n:
        if folded[i] == " ":
            i += 1
            continue
        j = i
        while j < n and folded[j] != " ":
            j += 1
        tok = folded[i:j]
        for t in terms:
            if tok == t or (prefix and len(t) >= PREFIX_MIN and tok.startswith(t)):
                spans.append((i, j))
                break
        i = j
    return spans


def to_original_spans(
    spans: list[tuple[int, int]], src: list[int], orig_len: int
) -> list[tuple[int, int]]:
    """Map folded spans to original-text spans via the offset map."""
    out: list[tuple[int, int]] = []
    for a, b in spans:
        if b <= a or a >= len(src):
            continue
        start = src[a]
        end = src[min(b, len(src)) - 1] + 1
        start, end = max(0, min(start, orig_len)), max(0, min(end, orig_len))
        if end > start:
            out.append((start, end))
    return out


def _window(text: str, spans: list[tuple[int, int]], width: int) -> tuple[int, int]:
    if not spans:
        return 0, min(len(text), width)
    first = spans[0][0]
    start = max(0, first - width // 3)
    end = min(len(text), start + width)
    start = max(0, min(start, end - width)) if end - start < width else start
    # snap to whitespace so words are not cut
    if start > 0:
        k = text.rfind(" ", max(0, start - 20), start)
        if k != -1:
            start = k + 1
    if end < len(text):
        k = text.find(" ", end, min(len(text), end + 20))
        if k != -1:
            end = k
    return start, end


def make_snippet(original: str | None, terms: list[str], *, width: int = DEFAULT_WIDTH) -> str:
    """Escaped snippet of ``original`` with matching tokens wrapped in ``<mark>``."""
    text = (original or "").replace("\n", " ")
    if not text:
        return ""
    folded, src = fold_indexed(text)
    spans = to_original_spans(term_spans(folded, terms), src, len(text))
    start, end = _window(text, spans, width)
    parts: list[str] = []
    if start > 0:
        parts.append(ELLIPSIS)
    cursor = start
    for a, b in spans:
        if b <= start or a >= end:
            continue
        a, b = max(a, start), min(b, end)
        if a > cursor:
            parts.append(escape(text[cursor:a]))
        parts.append(f"<mark>{escape(text[a:b])}</mark>")
        cursor = b
    if cursor < end:
        parts.append(escape(text[cursor:end]))
    if end < len(text):
        parts.append(ELLIPSIS)
    return "".join(parts)


__all__ = ["DEFAULT_WIDTH", "PREFIX_MIN", "make_snippet", "term_spans", "to_original_spans"]
