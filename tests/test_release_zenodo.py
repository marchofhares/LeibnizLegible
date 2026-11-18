"""Zenodo up to the draft (REL1 Task 3): reserve, upload, never publish. No network:
the API is a mock transport answering in the shapes of tests/fixtures/zenodo/."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

from leibniz import db
from leibniz.release import cards as C
from leibniz.release import state as S
from leibniz.release import zenodo as Z
from leibniz.release.export import export_dataset

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "tests/fixtures/zenodo"
TOKEN = "t0ken-never-printed"


def _fixture(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class FakeZenodo:
    """The deposit API as the fixtures shape it: one draft, a bucket, a file list."""

    def __init__(self, *, fail_first_put: int = 0, corrupt: str | None = None) -> None:
        self.requests: list[tuple[str, str]] = []
        self.files: dict[str, bytes] = {}
        self.metadata: dict | None = None
        self.created = 0
        self.fail_first_put = fail_first_put
        self.corrupt = corrupt
        self.submitted = False
        self.auth: set[str] = set()

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append((request.method, request.url.path))
        self.auth.add(request.headers.get("authorization", ""))
        path = request.url.path
        dep = _fixture("create.json")
        dep["submitted"] = self.submitted
        if request.method == "POST" and path == "/api/deposit/depositions":
            self.created += 1
            return httpx.Response(201, json=dep)
        if path == "/api/deposit/depositions/542201":
            if request.method == "PUT":
                self.metadata = json.loads(request.content)["metadata"]
            return httpx.Response(200, json=dep)
        if request.method == "GET" and path == "/api/deposit/depositions/542201/files":
            row = _fixture("files-list.json")[0]
            return httpx.Response(
                200,
                json=[
                    {
                        **row,
                        "filename": k,
                        "filesize": len(v),
                        "checksum": hashlib.md5(v).hexdigest(),
                    }
                    for k, v in self.files.items()
                ],
            )
        if request.method == "PUT" and path.startswith("/api/files/"):
            if self.fail_first_put:
                self.fail_first_put -= 1
                return httpx.Response(502, text="bad gateway")
            name = path.rsplit("/", 1)[1]
            body = request.read()
            assert request.headers["content-length"] == str(len(body))  # not chunked
            stored = body[:-1] if self.corrupt == name else body
            self.files[name] = stored
            answer = _fixture("file-put.json")
            answer.update(
                key=name, size=len(stored), checksum="md5:" + hashlib.md5(stored).hexdigest()
            )
            return httpx.Response(200, json=answer)
        return httpx.Response(404, json={"status": 404, "message": "not found"})

    def api(self, **kwargs) -> Z.Zenodo:
        client = httpx.Client(transport=httpx.MockTransport(self.handler))
        return Z.Zenodo(
            TOKEN,
            base=Z.SANDBOX,
            client=client,
            log=lambda _m: None,
            sleep=lambda _s: None,
            **kwargs,
        )


@pytest.fixture
def release_root(store_path, tmp_path) -> Path:
    out = tmp_path / "release"
    conn = db.connect(store_path)
    export_dataset(conn, "gt", out, fmt="jsonl")
    conn.close()
    return out


def test_reserve_creates_one_draft_prints_the_doi_and_records_it(release_root) -> None:
    fake = FakeZenodo()
    lines: list[str] = []
    doi = Z.reserve(release_root, "gt", fake.api(), log=lines.append)
    assert doi == "10.5072/zenodo.542201" and any(doi in line for line in lines)
    release = S.load_release(release_root)
    assert release["dois"] == {"gt": doi}
    assert release["zenodo"]["gt"]["deposition"] == 542201
    assert release["zenodo"]["gt"]["bucket"].startswith("https://sandbox.zenodo.org/api/files/")
    assert fake.requests == [("POST", "/api/deposit/depositions")]  # nothing uploaded
    assert fake.auth == {f"Bearer {TOKEN}"}
    assert TOKEN not in (release_root / S.RELEASE_FILE).read_text()
    assert not any(TOKEN in line for line in lines)
    # a second run does not create a second draft
    again = Z.reserve(release_root, "gt", fake.api(), log=lines.append)
    assert again == doi and fake.created == 1


def test_upload_refuses_a_card_without_the_reserved_doi(release_root) -> None:
    fake = FakeZenodo()
    with pytest.raises(Z.ZenodoError, match="reserve step first"):
        Z.upload(release_root, "gt", fake.api())
    Z.reserve(release_root, "gt", fake.api(), log=lambda _m: None)
    with pytest.raises(Z.ZenodoError, match="does not carry doi:10.5072/zenodo.542201"):
        Z.upload(release_root, "gt", fake.api())
    assert not fake.files


def test_upload_writes_metadata_and_files_and_stops_before_publishing(release_root) -> None:
    fake = FakeZenodo()
    Z.reserve(release_root, "gt", fake.api(), log=lambda _m: None)
    C.rerender(release_root)  # the DOI into the card and the deposit file
    lines: list[str] = []
    report = Z.upload(release_root, "gt", fake.api(), log=lines.append)
    folder = release_root / "leibniz-gt"
    assert sorted(fake.files) == sorted(p.name for p in folder.iterdir())
    for name, body in fake.files.items():  # byte for byte
        assert body == (folder / name).read_bytes()
    assert report.uploaded == ["README.md", "MANIFEST.json", "gt_lines-0001.jsonl.gz"]
    assert report.skipped == [] and report.bytes_sent == sum(len(b) for b in fake.files.values())
    assert fake.metadata["license"] == "cc-by-4.0" and fake.metadata["upload_type"] == "dataset"
    assert fake.metadata["communities"] == [{"identifier": "leibniz"}]
    assert not any("publish" in path for _m, path in fake.requests)
    assert "NOT published" in lines[-1] and "publish it in the browser" in lines[-1]
    # run again: nothing is sent twice
    before = len([r for r in fake.requests if r[1].startswith("/api/files/")])
    report2 = Z.upload(release_root, "gt", fake.api(), log=lines.append)
    assert report2.uploaded == [] and len(report2.skipped) == 3
    assert len([r for r in fake.requests if r[1].startswith("/api/files/")]) == before


def test_upload_resumes_after_a_changed_file_and_retries_a_5xx(release_root) -> None:
    fake = FakeZenodo(fail_first_put=2)
    Z.reserve(release_root, "gt", fake.api(), log=lambda _m: None)
    C.rerender(release_root)
    report = Z.upload(release_root, "gt", fake.api(), log=lambda _m: None)
    assert len(report.uploaded) == 3  # two 502s were retried
    # the card is re-rendered (a sibling's DOI arrives, a creator is named): the card
    # alone goes up again, and the metadata is written afresh
    release = S.load_release(release_root)
    release["creators"] = [{"name": "Family, Given"}]
    S.set_doi(release, "gt-nc", "10.5072/zenodo.542999")
    S.save_release(release_root, release)
    C.rerender(release_root)
    report2 = Z.upload(release_root, "gt", fake.api(), log=lambda _m: None)
    assert report2.uploaded == ["README.md"] and len(report2.skipped) == 2
    assert fake.metadata["creators"] == [{"name": "Family, Given"}]


def test_upload_checks_size_and_checksum_and_the_drafts_state(release_root) -> None:
    fake = FakeZenodo(corrupt="MANIFEST.json")
    Z.reserve(release_root, "gt", fake.api(), log=lambda _m: None)
    C.rerender(release_root)
    with pytest.raises(Z.ZenodoError, match="MANIFEST.json: sent .* bytes, Zenodo holds"):
        Z.upload(release_root, "gt", fake.api(), log=lambda _m: None)
    published = FakeZenodo()
    published.submitted = True
    with pytest.raises(Z.ZenodoError, match="is published; this script edits drafts"):
        Z.upload(release_root, "gt", published.api(), log=lambda _m: None)
    # a file the deposit file lists and the folder lacks stops the run before any request
    (release_root / "leibniz-gt" / "gt_lines-0001.jsonl.gz").unlink()
    idle = FakeZenodo()
    with pytest.raises(Z.ZenodoError, match="is not there"):
        Z.upload(release_root, "gt", idle.api(), log=lambda _m: None)
    assert idle.requests == []


def test_the_recorded_refusal_is_reported_as_zenodo_words_it() -> None:
    """Zenodo's real answer to a call without a token (recorded 2026-11-17)."""
    body = _fixture("create-unauthorized.json")
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403, json=body)))
    api = Z.Zenodo("wrong", client=client, log=lambda _m: None, sleep=lambda _s: None)
    with pytest.raises(Z.ZenodoError, match="HTTP 403 — Permission denied."):
        api.create({"title": "x"})


def test_dry_run_sends_nothing_and_needs_no_token(release_root) -> None:
    def boom(request: httpx.Request) -> httpx.Response:  # pragma: no cover — must not run
        raise AssertionError(f"a dry run sent {request.method} {request.url}")

    lines: list[str] = []
    api = Z.Zenodo(
        None,
        client=httpx.Client(transport=httpx.MockTransport(boom)),
        dry_run=True,
        log=lines.append,
    )
    assert Z.reserve(release_root, "gt", api, log=lines.append) is None
    Z.upload(release_root, "gt", api, log=lines.append)
    text = "\n".join(lines)
    assert "DRY RUN  POST https://zenodo.org/api/deposit/depositions" in text
    assert "DRY RUN  PUT" in text and "gt_lines-0001.jsonl.gz" in text
    assert not (release_root / S.RELEASE_FILE).exists()  # nothing recorded either


def test_the_token_comes_from_the_environment_only() -> None:
    assert Z.token_from_env({"ZENODO_TOKEN": " abc "}) == "abc"
    with pytest.raises(Z.ZenodoError, match="ZENODO_TOKEN is not set"):
        Z.token_from_env({})
    with pytest.raises(Z.ZenodoError):
        Z.Zenodo(None)  # no token, not a dry run
    source = (REPO / "tools/release/zenodo_deposit.py").read_text()
    assert "--token" not in source and "token_from_env" in source


def test_limits_are_checked_before_anything_is_sent(tmp_path) -> None:
    (tmp_path / "a").write_text("x")
    many = {"files": [{"name": f"f{i}", "path": "a"} for i in range(101)]}
    with pytest.raises(Z.ZenodoError, match="at most 100"):
        Z.local_files(tmp_path, many)
    twice = {"files": [{"name": "same", "path": "a"}, {"name": "same", "path": "a"}]}
    with pytest.raises(Z.ZenodoError, match="share a name"):
        Z.local_files(tmp_path, twice)


def test_the_tool_runs_a_dry_run_from_the_command_line(release_root, capsys, monkeypatch) -> None:
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    spec = importlib.util.spec_from_file_location(
        "zenodo_deposit", REPO / "tools/release/zenodo_deposit.py"
    )
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    args = ["--root", str(release_root), "--record", "gt"]
    assert tool.main(["reserve", *args, "--dry-run"]) == 0
    assert tool.main(["upload", *args, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN  POST https://zenodo.org/api/deposit/depositions" in out
    # without --dry-run and without a token it stops, with a reason, before any request
    assert tool.main(["reserve", *args]) == 1
    assert "ZENODO_TOKEN is not set" in capsys.readouterr().err
