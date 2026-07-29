"""Minimal, dependency-free JPEG inspection.

A2 caches JPEG delivery derivatives and needs two things from the bytes without
pulling in Pillow (the C-phase kraken stack brings its own imaging; A0 keeps deps
tiny): a **truncation check** (did the whole image arrive?) and the **pixel
dimensions** (the METS has none for static-JPEG works, so we read them off the
file). Both come from walking JPEG marker segments — a few dozen lines, fully
testable offline on tiny fixtures.
"""

from __future__ import annotations

# Start-of-Frame markers carry the dimensions. C4 (DHT), C8 (JPG), CC (DAC) sit
# in the 0xC0–0xCF range but are *not* frame headers, so they're excluded.
_SOF_EXCLUDED = frozenset({0xC4, 0xC8, 0xCC})
# Standalone markers that have no length field / payload.
_STANDALONE = frozenset({0x01, *range(0xD0, 0xDA)})  # TEM, RST0–7, SOI, EOI


def is_jpeg(data: bytes) -> bool:
    """True if ``data`` begins with the JPEG SOI marker (``FF D8``)."""
    return len(data) >= 2 and data[0] == 0xFF and data[1] == 0xD8


def is_complete_jpeg(data: bytes) -> bool:
    """True if ``data`` is a JPEG that both starts with SOI and ends with EOI.

    A truncated download (connection dropped mid-stream) keeps the SOI but lacks
    the trailing ``FF D9`` EOI — this is the integrity signal A2 retries on.
    Trailing padding bytes after EOI are tolerated.
    """
    if not is_jpeg(data):
        return False
    end = len(data)
    while end >= 2 and data[end - 1] in (0x00, 0xFF):
        end -= 1  # trim padding
    return end >= 2 and data[end - 2] == 0xFF and data[end - 1] == 0xD9


def jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return ``(width, height)`` in pixels from a JPEG's SOF, or ``None``.

    Scans marker segments for the first Start-of-Frame header rather than
    decoding pixels. Returns ``None`` for non-JPEG or malformed data.
    """
    if not is_jpeg(data):
        return None
    n = len(data)
    i = 2
    while i < n - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        while i < n and data[i] == 0xFF:  # collapse fill bytes
            i += 1
        if i >= n:
            break
        marker = data[i]
        i += 1
        if marker in _STANDALONE:
            continue
        if i + 1 >= n:
            break
        seg_len = (data[i] << 8) | data[i + 1]
        if seg_len < 2:
            break
        if 0xC0 <= marker <= 0xCF and marker not in _SOF_EXCLUDED:
            # SOF payload: precision(1), height(2), width(2) — after the 2 length bytes.
            if i + 6 < n:
                height = (data[i + 3] << 8) | data[i + 4]
                width = (data[i + 5] << 8) | data[i + 6]
                return (width, height)
            return None
        i += seg_len
    return None


__all__ = ["is_complete_jpeg", "is_jpeg", "jpeg_dimensions"]
