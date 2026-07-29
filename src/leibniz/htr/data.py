"""Loaders that turn on-disk ground truth into :class:`~leibniz.htr.bench.LinePair`s.

The harness input contract is a list of ``(line image, reference text)`` pairs; a
loader's whole job is to produce that list from whatever a GT set ships as. Two
formats matter for Phase B1:

* **HuggingFace parquet** (:func:`load_parquet_pairs`) — the PHILIUMM
  ``DenisaB/htr_leibniz_dataset_v1`` splits are parquet with a ``text`` string
  column and an ``image`` column (an HF ``Image`` feature: a struct of
  ``{bytes, path}``). Each row is one *already-extracted* (polygon-cropped,
  dewarped) line — exactly what a recogniser consumes. Needs ``pyarrow`` (lazy
  import; part of the optional ``bench`` extra).
* **image + sidecar-text directory** (:func:`load_image_text_dir`) — Kraken's own
  training convention: ``foo.png`` next to ``foo.gt.txt``. Dependency-free, so
  the harness tests use a handful of tiny fixtures with no heavy wheels.

Both return plain :class:`LinePair`s; :func:`subsample` draws a deterministic
random slice (for the "Claude on 100–200 lines" comparison) without touching the
wall-clock RNG the project forbids in reproducible runs.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from pathlib import Path

from leibniz.htr.bench import LinePair

# Sidecar text extensions tried, in order, for an image in load_image_text_dir.
_TEXT_SIDECARS = (".gt.txt", ".txt")
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")


def load_parquet_pairs(
    path: str | Path,
    *,
    text_col: str = "text",
    image_col: str = "image",
    id_prefix: str = "val",
    limit: int | None = None,
    skip_empty: bool = True,
) -> list[LinePair]:
    """Load ``(image bytes, text)`` rows from a HuggingFace-style parquet file.

    The ``image`` column may be an HF ``Image`` struct (``{bytes, path}``) or raw
    ``binary``; both are handled. Rows with empty reference text are skipped by
    default (the noisy split leaves unaligned lines blank — they are not valid
    evaluation atoms). ``pyarrow`` is imported lazily so the core package has no
    heavy dependency.
    """
    try:
        import pyarrow.parquet as pq
    except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
        raise ModuleNotFoundError(
            "reading parquet ground truth needs pyarrow — install the bench extra: "
            "`uv pip install pyarrow` (or `pip install leibniz-legible[bench]`)."
        ) from exc

    path = Path(path)
    pairs: list[LinePair] = []
    pf = pq.ParquetFile(str(path))
    idx = 0
    for batch in pf.iter_batches(batch_size=256, columns=[text_col, image_col]):
        cols = batch.to_pydict()
        for text, image in zip(cols[text_col], cols[image_col], strict=True):
            i = idx
            idx += 1
            ref = text or ""
            if skip_empty and not ref.strip():
                continue
            data = _image_cell_bytes(image)
            if data is None:
                continue
            pairs.append(
                LinePair(
                    line_id=f"{id_prefix}:{i:05d}",
                    reference=ref,
                    image_bytes_=data,
                    meta={"row": i, "source": path.name},
                )
            )
            if limit is not None and len(pairs) >= limit:
                return pairs
    return pairs


def _image_cell_bytes(cell: object) -> bytes | None:
    """Extract raw image bytes from a parquet image cell (struct or bytes)."""
    if cell is None:
        return None
    if isinstance(cell, (bytes, bytearray)):
        return bytes(cell)
    if isinstance(cell, dict):
        b = cell.get("bytes")
        return bytes(b) if b is not None else None
    return None


def load_image_text_dir(
    directory: str | Path,
    *,
    id_prefix: str = "line",
    limit: int | None = None,
    lang_map: dict[str, str] | None = None,
) -> list[LinePair]:
    """Pair every image in ``directory`` with its sidecar transcription.

    Follows Kraken's training-data convention: ``NAME.png`` (or any image
    extension) is transcribed by ``NAME.gt.txt`` (preferred) or ``NAME.txt``.
    Images without a sidecar are skipped. ``lang_map`` optionally assigns a
    per-line language by stem (for the language breakdown). Dependency-free —
    this is the loader the offline tests exercise.
    """
    directory = Path(directory)
    lang_map = lang_map or {}
    pairs: list[LinePair] = []
    for img in sorted(directory.iterdir()):
        if img.suffix.lower() not in _IMAGE_EXTS or _is_sidecar(img):
            continue
        text_path = _find_sidecar(img)
        if text_path is None:
            continue
        ref = text_path.read_text(encoding="utf-8").strip("\n")
        pairs.append(
            LinePair(
                line_id=f"{id_prefix}:{img.stem}",
                reference=ref,
                image_path=img,
                lang=lang_map.get(img.stem),
                meta={"image": img.name, "text": text_path.name},
            )
        )
        if limit is not None and len(pairs) >= limit:
            break
    return pairs


def _is_sidecar(path: Path) -> bool:
    return path.name.endswith(".gt.txt") or path.suffix == ".txt"


def _find_sidecar(image: Path) -> Path | None:
    for ext in _TEXT_SIDECARS:
        cand = image.with_name(image.stem + ext)
        if cand.exists():
            return cand
    return None


def subsample(pairs: Sequence[LinePair], n: int, *, seed: int = 12345) -> list[LinePair]:
    """Deterministically draw ``n`` pairs at random (all of them if ``n`` ≥ len).

    Used for the LLM comparison on a 100–200 line subsample; seeded so the same
    subset is drawn every run (the harness must be reproducible).
    """
    if n >= len(pairs):
        return list(pairs)
    rng = random.Random(seed)
    return [pairs[i] for i in sorted(rng.sample(range(len(pairs)), n))]


__all__ = [
    "load_image_text_dir",
    "load_parquet_pairs",
    "subsample",
]
