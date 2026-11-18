"""``RELEASE.json`` — what a release folder knows beyond its exports (REL1).

It sits at the release root beside the dataset folders and holds what is decided
or obtained after the export: the DOI each record reserved (written by
``tools/release/zenodo_deposit.py reserve``, or by ``leibniz release cards --doi``),
the Hugging Face namespace, the creators the Zenodo records name. ``leibniz
release cards`` re-renders every card and every record's Zenodo metadata from
the manifests and this file, so a DOI reaches the cards without the store being
read again. No token is ever written here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RELEASE_FILE = "RELEASE.json"
# The records of the first releases: three datasets and the model. The inventory
# (D1) rides inside the transcriptions record (the operator, 2026-11-16).
RECORDS = ("transcriptions", "gt", "gt-nc", "model")
MODEL_NAME = "leibniz-kurrent-trocr"  # the model's public name (the operator, 2026-11-16)
DEFAULT_CREATORS = [{"name": "Leibniz Legible"}]
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def clean_doi(value: str) -> str:
    """``https://doi.org/10.5281/zenodo.1`` or ``doi:10.5281/…`` → the bare DOI;
    ``ValueError`` for anything that is not one."""
    doi = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix) :]
    if not _DOI_RE.match(doi):
        raise ValueError(f"not a DOI: {value!r}")
    return doi


def load_release(root: Path) -> dict:
    """The release state at ``root`` (an empty one where the file is absent)."""
    path = Path(root) / RELEASE_FILE
    state: dict = {}
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
    state.setdefault("dois", {})
    state.setdefault("zenodo", {})
    state.setdefault("hf", {})
    state.setdefault("creators", [])
    return state


def save_release(root: Path, state: dict) -> Path:
    path = Path(root) / RELEASE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def set_doi(state: dict, record: str, doi: str) -> None:
    if record not in RECORDS:
        raise ValueError(f"unknown record {record!r}; expected one of {RECORDS}")
    state.setdefault("dois", {})[record] = clean_doi(doi)


def dois(state: dict | None) -> dict[str, str]:
    """Record → DOI, for the records that have one."""
    return {k: v for k, v in ((state or {}).get("dois") or {}).items() if v}


def creators(state: dict | None) -> list[dict]:
    """The creators of the Zenodo records: the release state's, else the project."""
    return list((state or {}).get("creators") or DEFAULT_CREATORS)


def hf_namespace(state: dict | None) -> str | None:
    return ((state or {}).get("hf") or {}).get("namespace") or None


def folder_name(record: str, state: dict | None = None) -> str:
    """The folder of a record under the release root."""
    if record == "model":
        return (state or {}).get("model_name") or MODEL_NAME
    return f"leibniz-{record}"


__all__ = [
    "DEFAULT_CREATORS",
    "MODEL_NAME",
    "RECORDS",
    "RELEASE_FILE",
    "clean_doi",
    "creators",
    "dois",
    "folder_name",
    "hf_namespace",
    "load_release",
    "save_release",
    "set_doi",
]
