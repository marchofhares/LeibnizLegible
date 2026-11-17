"""The Hugging Face mirror, scripted (REL1): a record's folder to a dataset or model
repository, the README first, the Parquet files as they are, private until the
operator flips it.

``tools/release/hf_upload.py`` is the entry point; the logic lives here so that it
is tested. The mirror takes the transcriptions (with the inventory), the open
ground-truth deposit and the model — **never the NC-derived deposit**, which is
on Zenodo only under its own licence, and that is refused here by name and by the
card's licence. The repository is created private, an existing public one is
refused unless the operator says so, and making it public is the operator's click
once the DOIs are on the site. The token comes from the environment
(``HF_TOKEN``) and is handed to the client explicitly, so the library's token
file is never read; ``--dry-run`` prints what would be sent and needs neither
the token nor the library. Files go up one commit each, and a file the repository
already holds with the same size (and SHA-256, where the Hub states one) is
skipped, so an interrupted run is run again and resumes.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from leibniz.release import state as S

TOKEN_ENV = "HF_TOKEN"
MIRRORED = ("transcriptions", "gt", "model")  # the NC deposit is not mirrored
REPO_TYPE = {"transcriptions": "dataset", "gt": "dataset", "model": "model"}
NC_MARKERS = ("cc-by-nc", "CC BY-NC")
# Never part of a mirror: the Zenodo zip and deposit files, upload caches, partial files.
IGNORED_SUFFIXES = (".zip", ".zenodo.json", ".part", ".lock")


class HubError(RuntimeError):
    """A refusal or a check that failed; the message says what."""


def token_from_env(env: dict | None = None) -> str:
    """The access token, from the environment only (never the library's token file)."""
    token = (os.environ if env is None else env).get(TOKEN_ENV, "").strip()
    if not token:
        raise HubError(
            f"{TOKEN_ENV} is not set: export it in this window (a token with write access to "
            "the namespace), or run with --dry-run"
        )
    return token


def make_api(token: str):
    """The Hub client, with the token given explicitly."""
    try:
        from huggingface_hub import HfApi
    except ModuleNotFoundError as exc:  # pragma: no cover — environment-dependent
        raise HubError("huggingface_hub is not installed (uv sync --extra release)") from exc
    return HfApi(token=token)


@dataclass(slots=True)
class HubReport:
    repo_id: str
    repo_type: str
    uploaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    bytes_sent: int = 0
    private: bool = True


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def folder_files(folder: Path) -> list[Path]:
    """The files of a record's folder that go to the mirror, README.md first."""
    folder = Path(folder)
    if not (folder / "README.md").is_file():
        raise HubError(f"{folder} has no README.md: not a record's folder")
    files = [
        p
        for p in sorted(folder.iterdir())
        if p.is_file() and not p.name.startswith(".") and not p.name.endswith(IGNORED_SUFFIXES)
    ]
    return sorted(files, key=lambda p: (p.name != "README.md", p.name))


def check_not_nc(record: str, folder: Path) -> None:
    """The NC-derived deposit never goes to the mirror: refused by its name, by its
    manifest and by its card's licence, whatever the folder is called."""
    if record not in MIRRORED:
        raise HubError(
            f"{record!r} is not mirrored on Hugging Face (mirrored: {', '.join(MIRRORED)}); "
            "the NC-derived deposit is on Zenodo only"
        )
    manifest = folder / "MANIFEST.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("dataset") == "gt-nc":
            raise HubError(f"{folder} is the NC-derived deposit: Zenodo only")
        if data.get("dataset") not in (None, record):
            raise HubError(f"{folder} holds {data.get('dataset')!r}, not {record!r}")
    head = (folder / "README.md").read_text(encoding="utf-8")[:2000]
    if any(f"license: {m}" in head or f"**License:** {m}" in head for m in NC_MARKERS):
        raise HubError(f"{folder}'s card states a non-commercial licence: Zenodo only")


def remote_files(api, repo_id: str, repo_type: str) -> dict[str, dict]:
    """What the repository holds: name → size and, for a large file, its SHA-256."""
    info = api.repo_info(repo_id, repo_type=repo_type, files_metadata=True)
    out: dict[str, dict] = {}
    for sib in getattr(info, "siblings", None) or []:
        lfs = getattr(sib, "lfs", None)
        sha = getattr(lfs, "sha256", None) if lfs is not None else None
        if isinstance(lfs, dict):
            sha = lfs.get("sha256")
        out[sib.rfilename] = {"size": getattr(sib, "size", None), "sha256": sha}
    return out


def upload_folder(
    root: Path,
    record: str,
    namespace: str,
    *,
    api=None,
    dry_run: bool = False,
    allow_public: bool = False,
    log: Callable[[str], None] = print,
) -> HubReport:
    """Mirror one record's folder to ``<namespace>/<folder>``: create the repository
    private (or find it), upload README.md, then the other files; resumable."""
    root = Path(root)
    release = S.load_release(root)
    name = S.folder_name(record, release)
    folder = root / name
    if not folder.is_dir():
        raise HubError(f"{folder} not found")
    check_not_nc(record, folder)
    if not namespace or "/" in namespace:
        raise HubError("the namespace is a user or an organisation name, without a slash")
    repo_id, repo_type = f"{namespace}/{name}", REPO_TYPE[record]
    files = folder_files(folder)
    report = HubReport(repo_id, repo_type)
    total = sum(p.stat().st_size for p in files)
    if dry_run:
        log(f"DRY RUN  create_repo {repo_id} (type {repo_type}, private, exist_ok)")
        for p in files:
            log(f"DRY RUN  upload_file {p.name} ({p.stat().st_size:,} bytes) → {repo_id}")
        log(f"DRY RUN  {len(files)} files, {total:,} bytes; nothing sent")
        return report
    if api is None:
        raise HubError("no client: pass api, or run with --dry-run")
    api.create_repo(repo_id, repo_type=repo_type, private=True, exist_ok=True)
    info = api.repo_info(repo_id, repo_type=repo_type)
    report.private = bool(getattr(info, "private", False))
    if not report.private and not allow_public:
        raise HubError(
            f"{repo_id} exists and is public: this script uploads to a private repository "
            "the operator makes public afterwards (--allow-public to add files to it as it is)"
        )
    there = remote_files(api, repo_id, repo_type)
    for p in files:
        size = p.stat().st_size
        held = there.get(p.name)
        # a large file is skipped where the Hub states its SHA-256 and it is the local
        # one; a small file (the card, the manifest) is sent again: a size vouches for nothing
        if held and held.get("sha256") and held.get("size") == size:
            if held["sha256"] == _sha256(p):
                report.skipped.append(p.name)
                log(f"  {p.name}: already in {repo_id}, identical ({size:,} bytes)")
                continue
        api.upload_file(
            path_or_fileobj=str(p),
            path_in_repo=p.name,
            repo_id=repo_id,
            repo_type=repo_type,
            commit_message=f"{name}: {p.name}",
        )
        report.uploaded.append(p.name)
        report.bytes_sent += size
        log(f"  {p.name}: uploaded ({size:,} bytes)")
    after = remote_files(api, repo_id, repo_type)
    for p in files:
        held = after.get(p.name)
        if not held or held.get("size") not in (None, p.stat().st_size):
            raise HubError(f"{p.name}: not in {repo_id} with its size after the upload")
    release.setdefault("hf", {})["namespace"] = namespace
    release["hf"].setdefault("repos", {})[record] = repo_id
    S.save_release(root, release)
    state = (
        "PRIVATE: make it public in its settings when the DOIs are on the site"
        if report.private
        else "public"
    )
    log(
        f"{repo_id}: {len(report.uploaded)} uploaded, {len(report.skipped)} already there, "
        f"{report.bytes_sent:,} bytes sent; the repository is {state}."
    )
    return report


__all__ = [
    "MIRRORED",
    "REPO_TYPE",
    "TOKEN_ENV",
    "HubError",
    "HubReport",
    "check_not_nc",
    "folder_files",
    "make_api",
    "remote_files",
    "token_from_env",
    "upload_folder",
]
