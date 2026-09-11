"""Volume ingestion: fetch a §70 volume's text layer, extract, cache (Phase C2).

``ingest_volume`` turns one registered :class:`~leibniz.align.volumes_sources.
EditionSource` into a per-piece reading-text JSON under ``data/editions/text/``
(cache-first at both stages: the raw hOCR/PDF under ``data/editions/{kind}/``
and the extracted JSON). ``build_edition_cache`` then joins those piece texts
to the katalog: every record whose AA column cites ``series,volume N.piece``
gets that piece's text, keyed by ``record_id`` — the ``{record_id: text}`` file
``leibniz align factory`` consumes. ``cross_source_qa`` compares two
independent sources of the same volume (an IA Tesseract layer vs the GWLB
ABBYY layer) piece by piece with :func:`~leibniz.align.volumes.assess_extraction`
— a per-volume extraction-error estimate that costs no API call.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align import edition as E
from leibniz.align.volumes import ExtractionQA, assess_extraction
from leibniz.align.volumes_sources import EditionSource

DEFAULT_EDITIONS_DIR = Path("data/editions")
_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}


def volume_label(series: int, volume: int) -> str:
    return f"{_ROMAN.get(series, str(series))},{volume}"


def text_path(source: EditionSource, editions_dir: Path = DEFAULT_EDITIONS_DIR) -> Path:
    """Where a source's extracted piece texts are cached."""
    part = f"-{source.part}" if source.part else ""
    name = f"{volume_label(source.series, source.volume)}{part}-{source.kind}.json"
    return editions_dir / "text" / name


def raw_path(source: EditionSource, editions_dir: Path = DEFAULT_EDITIONS_DIR) -> Path:
    return editions_dir / source.kind / source.local_name


@dataclass(slots=True)
class IngestResult:
    """Outcome of ingesting one source."""

    source: EditionSource
    status: str  # extracted | cached | skipped:<reason>
    n_pieces: int = 0
    n_chars: int = 0
    n_pages: int = 0
    n_reading_pages: int = 0
    n_anomalies: int = 0
    path: Path | None = None


def fetch_raw(source: EditionSource, *, client, editions_dir: Path = DEFAULT_EDITIONS_DIR) -> Path:
    """Download the source's text layer (cache-first) via the polite client."""
    path = raw_path(source, editions_dir)
    if path.exists() and path.stat().st_size > 0:
        return path
    if not source.url:
        raise ValueError(f"{source.kind} source has no fetchable URL")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = client.get_bytes(source.url)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path


def _pages_of(source: EditionSource, raw: Path) -> Iterable[E.PageText]:
    if source.text_layer == "hocr":
        return E.iter_hocr_pages(raw)
    return E.iter_pdf_pages(raw)


def volume_to_dict(source: EditionSource, vol: E.VolumeText) -> dict:
    return {
        "volume": volume_label(source.series, source.volume),
        "series": source.series,
        "volume_no": source.volume,
        "source": asdict(source),
        "sizes": asdict(vol.sizes) if vol.sizes else None,
        "n_pages": vol.n_pages,
        "n_eligible_pages": vol.n_eligible_pages,
        "n_reading_pages": vol.n_reading_pages,
        "n_apparatus_lines": vol.n_apparatus_lines,
        "n_editorial_lines": vol.n_editorial_lines,
        "anomalies": vol.anomalies,
        "pieces": {
            k: {
                "text": p.text,
                "pages": p.pages,
                "printed_pages": p.printed_pages,
                "n_chars": p.n_chars,
            }
            for k, p in sorted(vol.pieces.items(), key=lambda kv: (E._piece_num(kv[0]) or 0, kv[0]))
        },
    }


def ingest_volume(
    source: EditionSource,
    *,
    client=None,
    editions_dir: Path = DEFAULT_EDITIONS_DIR,
    force: bool = False,
    raw: Path | None = None,
) -> IngestResult:
    """Fetch (if needed), extract and cache one source's reading text.

    ``raw`` bypasses fetching (tests / an operator-supplied file). Returns
    ``cached`` when the extracted JSON already exists and ``force`` is not set.
    """
    out = text_path(source, editions_dir)
    if out.exists() and not force:
        data = json.loads(out.read_text(encoding="utf-8"))
        return IngestResult(
            source,
            "cached",
            n_pieces=len(data["pieces"]),
            n_chars=sum(p["n_chars"] for p in data["pieces"].values()),
            n_pages=data["n_pages"],
            n_reading_pages=data["n_reading_pages"],
            n_anomalies=len(data["anomalies"]),
            path=out,
        )
    if not source.text_layer:
        return IngestResult(source, f"skipped:{source.kind}")
    if raw is None:
        cached = raw_path(source, editions_dir)
        if cached.exists() and cached.stat().st_size > 0:
            raw = cached
        elif client is None:
            return IngestResult(source, "skipped:not_downloaded")
        else:
            raw = fetch_raw(source, client=client, editions_dir=editions_dir)
    vol = E.extract_volume(_pages_of(source, raw))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(volume_to_dict(source, vol), ensure_ascii=False, indent=0), encoding="utf-8"
    )
    return IngestResult(
        source,
        "extracted",
        n_pieces=len(vol.pieces),
        n_chars=vol.n_chars,
        n_pages=vol.n_pages,
        n_reading_pages=vol.n_reading_pages,
        n_anomalies=len(vol.anomalies),
        path=out,
    )


def load_volume_texts(path: Path) -> dict[str, str]:
    """``{piece: text}`` from an extracted-volume JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: v["text"] for k, v in data["pieces"].items()}


def piece_key(piece: str) -> str:
    """Normalise a katalog piece id to the print's numbering: ``"014"`` → ``"14"``."""
    p = piece.strip()
    i = 0
    while i < len(p) and p[i].isdigit():
        i += 1
    num, tail = p[:i].lstrip("0") or "0", p[i:]
    return f"{num}{tail}"


@dataclass(slots=True)
class CacheStats:
    """Bookkeeping for :func:`build_edition_cache`."""

    records_with_text: int = 0
    records_cited_no_text: int = 0
    by_volume: dict[str, int] = field(default_factory=dict)
    volumes_without_source: dict[str, int] = field(default_factory=dict)


def build_edition_cache(
    conn,
    volume_texts: dict[tuple[int, int], dict[str, str]],
    *,
    min_chars: int = 40,
) -> tuple[dict[str, str], CacheStats]:
    """Join extracted piece texts to katalog records → ``{record_id: text}``.

    A record citing several pieces gets them concatenated in citation order (a
    witness that carries two printed pieces). A sub-piece (``130a``) falls back
    to its parent (``130``) when the print numbers only the parent. Texts
    shorter than ``min_chars`` are treated as missing.
    """
    cache: dict[str, str] = {}
    stats = CacheStats()
    for rec in db.iter_katalog_records(conn):
        parts: list[str] = []
        cited_missing = False
        for ref in rec.aa_refs:
            if ref.get("source") != "aa_column":
                continue
            key = (ref.get("series"), ref.get("volume"))
            if key not in volume_texts:
                if key[0] is not None:
                    vl = volume_label(key[0], key[1])
                    stats.volumes_without_source[vl] = stats.volumes_without_source.get(vl, 0) + 1
                continue
            texts = volume_texts[key]
            pk = piece_key(str(ref.get("piece", "")))
            text = texts.get(pk) or texts.get(pk.rstrip("abcdefghijklmnopqrstuvwxyz")) or ""
            if len(text) >= min_chars:
                parts.append(text)
                vl = volume_label(key[0], key[1])
                stats.by_volume[vl] = stats.by_volume.get(vl, 0) + 1
            else:
                cited_missing = True
        if parts:
            cache[rec.record_id] = "\n".join(parts)
            stats.records_with_text += 1
        elif cited_missing:
            stats.records_cited_no_text += 1
    return cache, stats


def cross_source_qa(
    a: dict[str, str],
    b: dict[str, str],
    *,
    flag_cer: float = 0.10,
    max_pieces: int = 40,
    max_chars: int = 600,
) -> tuple[ExtractionQA, int]:
    """Two independent extractions of one volume, compared piece by piece.

    Returns the :class:`ExtractionQA` over a deterministic sample of the pieces
    both sources found (every ``n/max_pieces``-th piece, the first ``max_chars``
    characters of each — the CER is a quadratic DP, so whole volumes are not
    compared verbatim), plus the number of pieces only one source found (a
    boundary-detection miss on one side, counted separately from text
    disagreement).
    """
    common = sorted(set(a) & set(b), key=lambda k: (E._piece_num(k) or 0, k))
    only_one = len(set(a) ^ set(b))
    step = max(1, len(common) // max_pieces)
    sample = common[::step][:max_pieces]
    pairs = [(a[k][:max_chars], b[k][:max_chars]) for k in sample]
    return assess_extraction(pairs, flag_cer=flag_cer), only_one


ProgressFn = Callable[[IngestResult], None]


__all__ = [
    "DEFAULT_EDITIONS_DIR",
    "CacheStats",
    "IngestResult",
    "build_edition_cache",
    "cross_source_qa",
    "fetch_raw",
    "ingest_volume",
    "load_volume_texts",
    "piece_key",
    "raw_path",
    "text_path",
    "volume_label",
    "volume_to_dict",
]
