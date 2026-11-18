"""Zenodo, scripted up to the draft (REL1): reserve a DOI, upload the files, stop.

``tools/release/zenodo_deposit.py`` is the entry point; the logic lives here so
that it is tested. Two steps per record, with the cards re-rendered between them:

1. ``reserve`` — create a draft deposition, read the DOI Zenodo reserves for it,
   print it and write it into ``RELEASE.json`` at the release root (with the
   deposition's id). Nothing is uploaded.
2. ``upload`` — put the record's metadata (its deposit file, written by ``leibniz
   release export`` / ``cards`` / ``model``) on the draft and upload the files,
   one at a time, skipping a file the draft already holds with the same size and
   MD5, checking every upload's size and MD5 against the local file, so a run
   that was interrupted is run again and resumes. Then it stops.

**Publishing is never done here**: the operator reads the draft in the browser
and presses the button. The token is read from the environment (``ZENODO_TOKEN``)
and from nowhere else, is sent as a header and never printed; ``--dry-run``
prints each request instead of sending it and needs no token. The API is the
deposit API of https://developers.zenodo.org/ as read on 2026-11-17: ``POST
/api/deposit/depositions``, ``PUT`` on the draft for its metadata, ``PUT
<links.bucket>/<name>`` for a file (50 GB a record, 100 files), ``GET …/files``.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from leibniz.release import state as S

BASE = "https://zenodo.org"
SANDBOX = "https://sandbox.zenodo.org"
TOKEN_ENV = "ZENODO_TOKEN"
MAX_FILES = 100  # a record's limit (developers.zenodo.org)
MAX_BYTES = 50 * 1000**3  # 50 GB a record
USER_AGENT = "leibniz-legible-release/1 (+https://github.com/marchofhares/leibnizlegible)"


class ZenodoError(RuntimeError):
    """A refusal, an error from the API, or a check that failed; the message says what."""


def token_from_env(env: dict | None = None) -> str:
    """The access token, from the environment only (never a file, never an option)."""
    token = (os.environ if env is None else env).get(TOKEN_ENV, "").strip()
    if not token:
        raise ZenodoError(
            f"{TOKEN_ENV} is not set: export it in this window (a personal access token "
            "with the scope deposit:write and nothing more: without deposit:actions it "
            "cannot publish), or run with --dry-run"
        )
    return token


def md5_of(path: Path) -> str:
    h = hashlib.md5()  # noqa: S324 — Zenodo's file checksum is MD5; integrity, not security
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _bare_md5(checksum: str | None) -> str:
    """``"md5:2942…"`` (the bucket API) or ``"2942…"`` (the files listing) → the hex."""
    return (checksum or "").split(":")[-1].lower()


@dataclass(slots=True)
class LocalFile:
    name: str  # the file's name in the record (flat: Zenodo has no folders)
    path: Path
    size: int


@dataclass(slots=True)
class UploadReport:
    record: str
    deposition: int | None
    doi: str | None
    uploaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # already on the draft, identical
    bytes_sent: int = 0
    html: str | None = None


class Zenodo:
    """A thin client of the deposit API. ``dry_run`` sends nothing: every request is
    printed through ``log`` and a stand-in answer returned."""

    def __init__(
        self,
        token: str | None,
        *,
        base: str = BASE,
        client: httpx.Client | None = None,
        dry_run: bool = False,
        log: Callable[[str], None] = print,
        retries: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not dry_run and not token:
            raise ZenodoError("a token is needed unless dry_run is set")
        self.base = base.rstrip("/")
        self.dry_run = dry_run
        self.log = log
        self.retries = retries
        self.sleep = sleep
        self._token = token
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(60.0, write=600.0, read=600.0), follow_redirects=False
        )

    # -- plumbing ----------------------------------------------------------- #

    def _headers(self, extra: dict | None = None) -> dict:
        headers = {"User-Agent": USER_AGENT, **(extra or {})}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _check(self, r: httpx.Response, what: str) -> dict | list:
        if r.status_code >= 400:
            try:
                body = r.json()
                detail = body.get("message") or body
                errors = body.get("errors")
                if errors:
                    detail = f"{detail} {json.dumps(errors, ensure_ascii=False)}"
            except (ValueError, AttributeError):
                detail = r.text[:300]
            raise ZenodoError(f"{what}: HTTP {r.status_code} — {detail}")
        return r.json() if r.content else {}

    def _send(self, method: str, url: str, what: str, **kwargs) -> dict | list:
        """One request, retried on a network error or a 5xx with a growing pause; a
        4xx is the API's answer and is raised at once."""
        for attempt in range(self.retries + 1):
            try:
                r = self._client.request(method, url, headers=self._headers(), **kwargs)
            except httpx.TransportError as exc:
                problem = str(exc) or type(exc).__name__
            else:
                if r.status_code < 500:
                    return self._check(r, what)
                problem = f"HTTP {r.status_code}"
            if attempt >= self.retries:
                raise ZenodoError(f"{what}: {problem} after {attempt + 1} attempts")
            self.log(f"  {what}: {problem}; retry {attempt + 1} of {self.retries}")
            self.sleep(min(60.0, 2.0 * 2**attempt))
        raise ZenodoError(f"{what}: gave up")  # pragma: no cover — the loop returns or raises

    # -- the API ------------------------------------------------------------ #

    def create(self, metadata: dict) -> dict:
        url = f"{self.base}/api/deposit/depositions"
        if self.dry_run:
            self.log(f"DRY RUN  POST {url}")
            self.log("         " + json.dumps({"metadata": _brief(metadata)}, ensure_ascii=False))
            return {}
        return self._send("POST", url, "create the draft", json={"metadata": metadata})  # type: ignore[return-value]

    def get(self, deposition: int) -> dict:
        url = f"{self.base}/api/deposit/depositions/{deposition}"
        if self.dry_run:
            self.log(f"DRY RUN  GET {url}")
            return {}
        return self._send("GET", url, "read the draft")  # type: ignore[return-value]

    def update(self, deposition: int, metadata: dict) -> dict:
        url = f"{self.base}/api/deposit/depositions/{deposition}"
        if self.dry_run:
            self.log(f"DRY RUN  PUT {url}")
            self.log("         " + json.dumps({"metadata": _brief(metadata)}, ensure_ascii=False))
            return {}
        return self._send("PUT", url, "write the metadata", json={"metadata": metadata})  # type: ignore[return-value]

    def files(self, deposition: int) -> list[dict]:
        url = f"{self.base}/api/deposit/depositions/{deposition}/files"
        if self.dry_run:
            self.log(f"DRY RUN  GET {url}")
            return []
        return self._send("GET", url, "list the draft's files")  # type: ignore[return-value]

    def put_file(self, bucket: str, f: LocalFile) -> dict:
        url = f"{bucket.rstrip('/')}/{f.name}"
        if self.dry_run:
            self.log(f"DRY RUN  PUT {url}  ({f.size:,} bytes from {f.path})")
            return {}
        what = f"upload {f.name}"
        for attempt in range(self.retries + 1):
            try:
                with f.path.open("rb") as fh:  # httpx reads the length from the file
                    r = self._client.put(
                        url,
                        content=fh,
                        headers=self._headers({"Content-Type": "application/octet-stream"}),
                    )
            except httpx.TransportError as exc:
                problem = str(exc) or type(exc).__name__
            else:
                if r.status_code < 500:
                    return self._check(r, what)  # type: ignore[return-value]
                problem = f"HTTP {r.status_code}"
            if attempt >= self.retries:
                raise ZenodoError(f"{what}: {problem} after {attempt + 1} attempts")
            self.log(f"  {what}: {problem}; retry {attempt + 1} of {self.retries}")
            self.sleep(min(60.0, 2.0 * 2**attempt))
        raise ZenodoError(f"{what}: gave up")  # pragma: no cover


def _brief(metadata: dict) -> dict:
    """The metadata with its description cut short, for a dry run's print."""
    out = dict(metadata)
    desc = out.get("description")
    if isinstance(desc, str) and len(desc) > 160:
        out["description"] = desc[:160] + f"… ({len(desc):,} characters)"
    return out


# --------------------------------------------------------------------------- #
# The two steps
# --------------------------------------------------------------------------- #


def load_deposit_file(root: Path, record: str, release: dict | None = None) -> dict:
    """A record's deposit file (``<root>/<folder>.zenodo.json``)."""
    path = Path(root) / f"{S.folder_name(record, release)}.zenodo.json"
    if not path.exists():
        raise ZenodoError(
            f"{path} not found: run `leibniz release export` (a dataset) or `leibniz release "
            "model` (the model) into this folder first"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def local_files(root: Path, deposit: dict) -> list[LocalFile]:
    """The files of a record as its deposit file lists them, each present and
    measured; the record's limits checked before anything is sent."""
    root = Path(root)
    out: list[LocalFile] = []
    for entry in deposit.get("files") or []:
        path = root / entry["path"]
        if not path.is_file():
            raise ZenodoError(f"{path} is listed in the deposit file and is not there")
        out.append(LocalFile(entry["name"], path, path.stat().st_size))
    names = [f.name for f in out]
    if len(set(names)) != len(names):
        raise ZenodoError("two files of the record share a name; Zenodo's files are flat")
    if len(out) > MAX_FILES:
        raise ZenodoError(f"{len(out)} files: a Zenodo record takes at most {MAX_FILES}")
    total = sum(f.size for f in out)
    if total > MAX_BYTES:
        raise ZenodoError(f"{total:,} bytes: a Zenodo record takes at most {MAX_BYTES:,}")
    return out


def reserved_doi(deposition: dict) -> str | None:
    doi = ((deposition.get("metadata") or {}).get("prereserve_doi") or {}).get("doi")
    return doi or None


def reserve(
    root: Path,
    record: str,
    api: Zenodo,
    *,
    new: bool = False,
    log: Callable[[str], None] = print,
) -> str | None:
    """Create the record's draft, reserve its DOI, print it and write it into
    ``RELEASE.json``. A record that already has a draft there is not given a
    second one (``new`` forces it). Returns the DOI (``None`` in a dry run)."""
    if record not in S.RECORDS:
        raise ZenodoError(f"unknown record {record!r}; expected one of {S.RECORDS}")
    root = Path(root)
    release = S.load_release(root)
    had = (release.get("zenodo") or {}).get(record)
    if had and not new:
        log(
            f"{record}: draft {had.get('deposition')} already reserved "
            f"doi:{release['dois'].get(record)} ({had.get('html')}); nothing created"
        )
        return release["dois"].get(record)
    # the title only: the full metadata is written at upload, from the final card
    title = f"Leibniz Legible: {S.folder_name(record, release)} (draft, reserved)"
    upload_type = "other" if record == "model" else "dataset"
    dep = api.create({"title": title, "upload_type": upload_type, "prereserve_doi": True})
    if api.dry_run:
        log(f"{record}: dry run — no draft created, no DOI reserved")
        return None
    doi = reserved_doi(dep)
    if not doi or not dep.get("id"):
        raise ZenodoError(
            f"{record}: the draft was created (id {dep.get('id')}) and Zenodo returned no "
            "reserved DOI; read it on the draft's page and record it with "
            f"`leibniz release cards --doi {record}=<doi>`"
        )
    links = dep.get("links") or {}
    release["dois"][record] = S.clean_doi(doi)
    release["zenodo"][record] = {
        "deposition": int(dep["id"]),
        "bucket": links.get("bucket"),
        "html": links.get("html") or links.get("latest_draft_html"),
        "base": api.base,
        "reserved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    S.save_release(root, release)
    log(f"{record}: draft {dep['id']} created; DOI reserved: {doi}")
    draft = release["zenodo"][record]["html"]
    log(f"{record}: written to {root / S.RELEASE_FILE}; the draft: {draft}")
    return doi


def upload(
    root: Path,
    record: str,
    api: Zenodo,
    *,
    log: Callable[[str], None] = print,
) -> UploadReport:
    """Put the metadata on the record's draft and upload its files; resumable; no
    publish. Refuses a card that does not carry the reserved DOI, a draft that is
    already published, and a DOI that is not the draft's."""
    root = Path(root)
    release = S.load_release(root)
    deposit = load_deposit_file(root, record, release)
    files = local_files(root, deposit)
    doi = (release.get("dois") or {}).get(record)
    held = (release.get("zenodo") or {}).get(record) or {}
    report = UploadReport(record, held.get("deposition"), doi, html=held.get("html"))
    if api.dry_run:
        dep_id = int(held.get("deposition") or 0)
        log(f"{record}: dry run — {len(files)} files, {sum(f.size for f in files):,} bytes")
        api.update(dep_id, deposit["metadata"])
        for f in files:
            api.put_file(held.get("bucket") or f"{api.base}/api/files/<bucket>", f)
        return report
    if not doi or not held.get("deposition"):
        raise ZenodoError(f"{record}: no draft in RELEASE.json — run the reserve step first")
    card = next((f for f in files if f.name == "README.md"), None)
    if card is None or doi not in card.path.read_text(encoding="utf-8"):
        raise ZenodoError(
            f"{record}: the card does not carry doi:{doi} — re-render it first "
            "(`leibniz release cards --out <root>`; the model: `leibniz release model …`)"
        )
    dep_id = int(held["deposition"])
    dep = api.get(dep_id)
    if dep.get("submitted") or dep.get("state") == "done":
        raise ZenodoError(f"{record}: deposition {dep_id} is published; this script edits drafts")
    theirs = reserved_doi(dep)
    if theirs and theirs != doi:
        raise ZenodoError(f"{record}: the draft's DOI is {theirs}, RELEASE.json says {doi}")
    bucket = (dep.get("links") or {}).get("bucket") or held.get("bucket")
    if not bucket:
        raise ZenodoError(f"{record}: the draft names no bucket to upload to")
    api.update(dep_id, deposit["metadata"])
    log(f"{record}: metadata written to draft {dep_id}")
    remote = {f["filename"]: f for f in api.files(dep_id)}
    for f in files:
        local_md5 = md5_of(f.path)
        there = remote.get(f.name)
        if (
            there
            and int(there.get("filesize") or -1) == f.size
            and _bare_md5(there.get("checksum")) == local_md5
        ):
            report.skipped.append(f.name)
            log(f"  {f.name}: already on the draft, identical ({f.size:,} bytes)")
            continue
        t0 = time.monotonic()
        answer = api.put_file(bucket, f)
        got_size, got_md5 = answer.get("size"), _bare_md5(answer.get("checksum"))
        if got_size is not None and int(got_size) != f.size:
            raise ZenodoError(f"{f.name}: sent {f.size:,} bytes, Zenodo holds {got_size:,}")
        if got_md5 and got_md5 != local_md5:
            raise ZenodoError(f"{f.name}: MD5 {local_md5} sent, Zenodo holds {got_md5}")
        report.uploaded.append(f.name)
        report.bytes_sent += f.size
        log(f"  {f.name}: uploaded ({f.size:,} bytes, {time.monotonic() - t0:.0f} s)")
    # the last word: the draft's own listing against the local files
    remote = {f["filename"]: f for f in api.files(dep_id)}
    for f in files:
        there = remote.get(f.name)
        if not there or int(there.get("filesize") or -1) != f.size:
            raise ZenodoError(f"{f.name}: not on the draft with its size after the upload")
    extra = sorted(set(remote) - {f.name for f in files})
    if extra:
        log(f"{record}: the draft holds files this export does not list: {', '.join(extra)}")
    log(
        f"{record}: {len(report.uploaded)} uploaded, {len(report.skipped)} already there, "
        f"{report.bytes_sent:,} bytes sent. NOT published: read the draft at "
        f"{report.html} and publish it in the browser."
    )
    return report


__all__ = [
    "BASE",
    "SANDBOX",
    "TOKEN_ENV",
    "LocalFile",
    "UploadReport",
    "Zenodo",
    "ZenodoError",
    "load_deposit_file",
    "local_files",
    "md5_of",
    "reserve",
    "reserved_doi",
    "token_from_env",
    "upload",
]
