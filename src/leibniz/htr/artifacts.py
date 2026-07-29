"""Fetch & cache the PHILIUMM benchmark artifacts (Phase B1).

Three CC BY 4.0 artifacts, cached under ``data/`` (gitignored):

* the **HTR model** — Zenodo record ``21457538``
  (``FoNDUE-GD_v2_ft_Leibniz.safetensors`` + its ketos configs / file lists),
* the **validation ground truth** — the ``val`` split of HuggingFace
  ``DenisaB/htr_leibniz_dataset_v1`` (1,878 pre-extracted line/text pairs, one
  parquet file),
* the **segmentation model** — Zenodo record ``21537859`` (not needed to score
  pre-segmented lines, but fetched/recorded for provenance and Phase B2/C1).

Downloads are **cache-first** (an existing file of the expected size is kept) and
streamed to disk so the 300 MB parquet never sits in memory. Each artifact's DOI
/ URL and license is recorded so :mod:`leibniz.htr.report` can cite provenance.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from leibniz.net import default_user_agent

# --------------------------------------------------------------------------- #
# Artifact registry (verify live before relying on; record drift in STATUS.md)
# --------------------------------------------------------------------------- #

ZENODO_HTR_RECORD = "21457538"
ZENODO_SEG_RECORD = "21537859"
HF_DATASET = "DenisaB/htr_leibniz_dataset_v1"

MODELS_DIR = Path("data/models/philiumm-htr")
SEG_DIR = Path("data/models/philiumm-seg")
GT_DIR = Path("data/gt/philiumm-val")

MODEL_FILE = "FoNDUE-GD_v2_ft_Leibniz.safetensors"
# Small companions worth caching next to the weights (configs + line lists).
MODEL_AUX_FILES = (
    "metadata.json",
    "stage1_noisy.yml",
    "stage2_clean.yml",
    "val_clean.lst",
    "train_clean.lst",
    "train_noisy.lst",
)
VAL_PARQUET = "val-00000-of-00001.parquet"

LICENSE = "CC BY 4.0"
ATTRIBUTION = (
    "HTR model, segmentation model and ground truth © ERC PHILIUMM project "
    "(Denisa-Florina Bumba, Laboratoire SPHERE, Université Paris Cité – CNRS; "
    "ERC grant 101020985), CC BY 4.0. Model: doi:10.5281/zenodo.21457538; "
    "segmentation: doi:10.5281/zenodo.21537859; ground truth: "
    "huggingface.co/datasets/DenisaB/htr_leibniz_dataset_v1."
)


def _zenodo_url(record: str, filename: str) -> str:
    return f"https://zenodo.org/records/{record}/files/{filename}?download=1"


def _hf_url(dataset: str, path: str) -> str:
    return f"https://huggingface.co/datasets/{dataset}/resolve/main/{path}?download=1"


@dataclass(slots=True)
class ArtifactPaths:
    """Where the fetched artifacts live on disk."""

    model: Path
    val_parquet: Path

    @property
    def model_present(self) -> bool:
        return self.model.exists() and self.model.stat().st_size > 0

    @property
    def val_present(self) -> bool:
        return self.val_parquet.exists() and self.val_parquet.stat().st_size > 0


def artifact_paths(models_dir: Path = MODELS_DIR, gt_dir: Path = GT_DIR) -> ArtifactPaths:
    """Resolve the on-disk locations of the model + val split (no I/O)."""
    return ArtifactPaths(
        model=Path(models_dir) / MODEL_FILE, val_parquet=Path(gt_dir) / VAL_PARQUET
    )


# --------------------------------------------------------------------------- #
# Streaming, cache-first download
# --------------------------------------------------------------------------- #


def download_file(
    url: str,
    dest: Path,
    *,
    client=None,
    user_agent: str | None = None,
    chunk_size: int = 1 << 20,
    progress: Callable[[int], None] | None = None,
) -> Path:
    """Stream ``url`` to ``dest`` (cache-first: skip a non-empty existing file).

    Uses ``httpx`` streaming so large files never load into memory. A partial
    download goes to ``dest.part`` and is renamed on success, so an interrupted
    fetch never leaves a truncated file that looks complete.
    """
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    ua = user_agent or default_user_agent()

    owns = client is None
    if client is None:
        import httpx

        client = httpx.Client(timeout=120.0, follow_redirects=True, headers={"User-Agent": ua})
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as fh:
                for chunk in resp.iter_bytes(chunk_size):
                    fh.write(chunk)
                    if progress is not None:
                        progress(len(chunk))
        tmp.replace(dest)
    finally:
        if owns:
            client.close()
        if tmp.exists():
            tmp.unlink()
    return dest


def fetch_model(
    *, models_dir: Path = MODELS_DIR, client=None, aux: bool = True, progress=None
) -> Path:
    """Fetch the PHILIUMM HTR model (+ small config/aux files) from Zenodo."""
    models_dir = Path(models_dir)
    model_path = download_file(
        _zenodo_url(ZENODO_HTR_RECORD, MODEL_FILE),
        models_dir / MODEL_FILE,
        client=client,
        progress=progress,
    )
    if aux:
        for fn in MODEL_AUX_FILES:
            download_file(_zenodo_url(ZENODO_HTR_RECORD, fn), models_dir / fn, client=client)
    return model_path


def fetch_val_split(*, gt_dir: Path = GT_DIR, client=None, progress=None) -> Path:
    """Fetch the val-split parquet (1,878 line/text pairs) from HuggingFace."""
    return download_file(
        _hf_url(HF_DATASET, f"data/{VAL_PARQUET}"),
        Path(gt_dir) / VAL_PARQUET,
        client=client,
        progress=progress,
    )


__all__ = [
    "ATTRIBUTION",
    "GT_DIR",
    "HF_DATASET",
    "LICENSE",
    "MODELS_DIR",
    "MODEL_FILE",
    "VAL_PARQUET",
    "ZENODO_HTR_RECORD",
    "ZENODO_SEG_RECORD",
    "ArtifactPaths",
    "artifact_paths",
    "download_file",
    "fetch_model",
    "fetch_val_split",
]
