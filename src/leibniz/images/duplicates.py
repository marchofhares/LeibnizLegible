"""Sheet-sides registered twice: find the page images that are the same scan.

In the GWLB's static-JPEG delivery a scan is one *side of an unfolded sheet*,
two folio pages side by side, and the METS registers that one image under
both folio labels (outer side ``1r`` + ``2v``, inner side ``1v`` + ``2r``). The
corpus run read every such image twice, so the page and line counts include
those repeats and search returns them as twin hits.

``leibniz images duplicates`` walks the thumbnails work by work, hashes each
one with a difference hash (8×8 gradients, 64 bits) and reports the pairs of
nearby pages (within ``window`` positions) whose hashes agree within
``max_distance`` bits. The output is a report for ``reports/`` and a JSONL of
pairs that the index build can use to fold twins into one hit.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from leibniz.images.thumbs import DEFAULT_THUMBS_ROOT

DEFAULT_WINDOW = 8
DEFAULT_MAX_DISTANCE = 4
HASH_SIZE = 8


def dhash(path: Path, *, size: int = HASH_SIZE) -> int:
    """A difference hash: ``size`` × ``size`` bits from horizontal gradients of a
    grey ``(size+1)`` × ``size`` downscale. Robust to JPEG recompression and to
    small size differences, which is all two copies of one scan differ by."""
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:  # pragma: no cover — environment-dependent
        raise ModuleNotFoundError("Pillow is required: uv sync --extra gt") from exc
    with Image.open(path) as im:
        im.draft("L", (size * 8, size * 8))
        small = im.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    px = list(
        small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata()
    )
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


@dataclass
class DuplicatePair:
    work_id: str
    page_a: str
    page_b: str
    distance: int

    def to_dict(self) -> dict:
        return {
            "work_id": self.work_id,
            "page_a": self.page_a,
            "page_b": self.page_b,
            "distance": self.distance,
        }


@dataclass
class DuplicateStats:
    works: int = 0
    pages_hashed: int = 0
    pages_missing: int = 0
    pairs: list[DuplicatePair] = field(default_factory=list)
    pages_in_pairs: set[str] = field(default_factory=set)
    by_set: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def n_pairs(self) -> int:
        return len(self.pairs)

    def to_dict(self) -> dict:
        return {
            "works": self.works,
            "pages_hashed": self.pages_hashed,
            "pages_missing": self.pages_missing,
            "pairs": self.n_pairs,
            "pages_in_pairs": len(self.pages_in_pairs),
            "by_set": self.by_set,
        }


def _pages_by_work(conn: sqlite3.Connection) -> dict[str, list[tuple[str, int, str, str]]]:
    rows = conn.execute(
        """
        SELECT p.work_id, p.page_id, p.seq, p.local_path, COALESCE(w.set_name, '')
          FROM pages p LEFT JOIN works w ON w.gwlb_object_id = p.work_id
         WHERE p.local_path IS NOT NULL
         ORDER BY p.work_id, p.seq
        """
    ).fetchall()
    out: dict[str, list[tuple[str, int, str, str]]] = defaultdict(list)
    for work_id, page_id, seq, local_path, set_name in rows:
        out[work_id].append((page_id, seq, local_path, set_name))
    return out


def find_duplicates(
    conn: sqlite3.Connection,
    thumbs_root: Path = DEFAULT_THUMBS_ROOT,
    *,
    window: int = DEFAULT_WINDOW,
    max_distance: int = DEFAULT_MAX_DISTANCE,
    works: Iterable[str] | None = None,
    progress: Callable[[str], None] | None = None,
) -> DuplicateStats:
    """Hash every thumbnail and pair up near-identical pages within ``window``
    positions of each other in the same work. Missing thumbnails are counted,
    not fatal."""
    thumbs_root = Path(thumbs_root)
    stats = DuplicateStats()
    wanted = set(works) if works is not None else None
    for work_id, pages in _pages_by_work(conn).items():
        if wanted is not None and work_id not in wanted:
            continue
        stats.works += 1
        set_name = pages[0][3] if pages else ""
        tally = stats.by_set.setdefault(set_name, {"pages": 0, "pages_in_pairs": 0, "pairs": 0})
        hashes: list[tuple[str, int | None]] = []
        for page_id, _seq, local_path, _set in pages:
            path = thumbs_root / local_path
            if not path.exists():
                stats.pages_missing += 1
                hashes.append((page_id, None))
                continue
            hashes.append((page_id, dhash(path)))
            stats.pages_hashed += 1
            tally["pages"] += 1
            if progress:
                progress(page_id)
        for i, (page_a, ha) in enumerate(hashes):
            if ha is None:
                continue
            for page_b, hb in hashes[i + 1 : i + 1 + window]:
                if hb is None:
                    continue
                d = hamming(ha, hb)
                if d <= max_distance:
                    stats.pairs.append(DuplicatePair(work_id, page_a, page_b, d))
                    tally["pairs"] += 1
                    for pid in (page_a, page_b):
                        if pid not in stats.pages_in_pairs:
                            stats.pages_in_pairs.add(pid)
                            tally["pages_in_pairs"] += 1
    return stats


def write_pairs(stats: DuplicateStats, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for pair in stats.pairs:
            fh.write(json.dumps(pair.to_dict()) + "\n")


def render_report(stats: DuplicateStats, *, window: int, max_distance: int) -> str:
    lines = [
        "# Duplicate page images (sheet-sides registered twice)",
        "",
        "_Generated by `leibniz images duplicates`. A pair is two pages of the same work, "
        f"at most {window} positions apart, whose 64-bit difference hashes differ by at most "
        f"{max_distance} bits — in practice one scan of an unfolded sheet registered under "
        "two folio labels._",
        "",
        f"- **Works scanned:** {stats.works:,}",
        f"- **Thumbnails hashed:** {stats.pages_hashed:,} ({stats.pages_missing:,} missing)",
        f"- **Duplicate pairs:** {stats.n_pairs:,}",
        f"- **Pages that are one half of a pair:** {len(stats.pages_in_pairs):,}",
    ]
    if stats.pages_hashed:
        share = len(stats.pages_in_pairs) / stats.pages_hashed
        lines.append(f"- **Share of hashed pages in a pair:** {share:.1%}")
    lines += [
        "",
        "| Set | Pages hashed | Pages in pairs | Pairs | Share |",
        "|---|---:|---:|---:|---:|",
    ]
    for set_name, t in sorted(stats.by_set.items()):
        share = t["pages_in_pairs"] / t["pages"] if t["pages"] else 0.0
        lines.append(
            f"| {set_name or '—'} | {t['pages']:,} | {t['pages_in_pairs']:,} | {t['pairs']:,} | "
            f"{share:.1%} |"
        )
    lines += [
        "",
        "Every page record still counts as the library's own page count; the distinct-scan "
        "count is the hashed pages minus one per pair. Line totals over the paired pages "
        "are counted twice in `lines`.",
    ]
    return "\n".join(lines) + "\n"


__all__ = [
    "DuplicatePair",
    "DuplicateStats",
    "dhash",
    "find_duplicates",
    "hamming",
    "render_report",
    "write_pairs",
]
