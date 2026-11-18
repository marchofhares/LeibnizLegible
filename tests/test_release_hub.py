"""The Hugging Face mirror (REL1 Task 3) against a stand-in client: no network, no
token file."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from leibniz import db
from leibniz.release import hub as H
from leibniz.release import state as S
from leibniz.release.export import export_dataset

REPO = Path(__file__).resolve().parents[1]


class FakeHub:
    """What the script needs of ``huggingface_hub.HfApi``, recording the calls."""

    def __init__(self, *, private: bool = True) -> None:
        self.calls: list[tuple] = []
        self.files: dict[str, bytes] = {}
        self.private = private
        self.created: dict | None = None

    def create_repo(self, repo_id, *, repo_type, private, exist_ok):
        self.created = {"repo_id": repo_id, "repo_type": repo_type, "private": private}
        self.calls.append(("create_repo", repo_id, repo_type, private, exist_ok))

    def repo_info(self, repo_id, *, repo_type, files_metadata=False):
        siblings = [
            SimpleNamespace(
                rfilename=name,
                size=len(body),
                # the Hub states a SHA-256 for a large file only
                lfs=SimpleNamespace(sha256=hashlib.sha256(body).hexdigest())
                if name.endswith((".gz", ".parquet", ".safetensors"))
                else None,
            )
            for name, body in self.files.items()
        ]
        return SimpleNamespace(private=self.private, siblings=siblings)

    def upload_file(self, *, path_or_fileobj, path_in_repo, repo_id, repo_type, commit_message):
        self.files[path_in_repo] = Path(path_or_fileobj).read_bytes()
        self.calls.append(("upload_file", path_in_repo, repo_id, repo_type))


@pytest.fixture
def release_root(store_path, tmp_path) -> Path:
    out = tmp_path / "release"
    conn = db.connect(store_path)
    for dataset in ("transcriptions", "gt", "gt-nc"):
        export_dataset(conn, dataset, out, fmt="jsonl")
    conn.close()
    return out


def test_readme_first_then_the_files_into_a_private_dataset_repo(release_root) -> None:
    hub = FakeHub()
    report = H.upload_folder(
        release_root, "transcriptions", "leibniz-legible", api=hub, log=lambda _m: None
    )
    assert hub.created == {
        "repo_id": "leibniz-legible/leibniz-transcriptions",
        "repo_type": "dataset",
        "private": True,
    }
    uploads = [c[1] for c in hub.calls if c[0] == "upload_file"]
    assert uploads[0] == "README.md"
    folder = release_root / "leibniz-transcriptions"
    assert sorted(uploads) == sorted(p.name for p in folder.iterdir())
    for name, body in hub.files.items():  # as they are
        assert body == (folder / name).read_bytes()
    assert report.private and report.repo_type == "dataset" and len(report.uploaded) == 7
    assert S.load_release(release_root)["hf"] == {
        "namespace": "leibniz-legible",
        "repos": {"transcriptions": "leibniz-legible/leibniz-transcriptions"},
    }
    # run again: the data files are skipped by their SHA-256, the small text files re-sent
    again = H.upload_folder(
        release_root, "transcriptions", "leibniz-legible", api=hub, log=lambda _m: None
    )
    assert sorted(again.uploaded) == ["MANIFEST.json", "README.md"]
    assert len(again.skipped) == 5


def test_the_nc_deposit_is_never_mirrored(release_root) -> None:
    hub = FakeHub()
    with pytest.raises(H.HubError, match="Zenodo only"):
        H.upload_folder(release_root, "gt-nc", "leibniz-legible", api=hub)
    # nor under another record's name: the manifest and the card's licence both refuse
    (release_root / "leibniz-gt").rename(release_root / "leibniz-gt.aside")
    (release_root / "leibniz-gt-nc").rename(release_root / "leibniz-gt")
    with pytest.raises(H.HubError, match="NC-derived deposit"):
        H.upload_folder(release_root, "gt", "leibniz-legible", api=hub)
    (release_root / "leibniz-gt" / "MANIFEST.json").unlink()
    with pytest.raises(H.HubError, match="non-commercial licence"):
        H.upload_folder(release_root, "gt", "leibniz-legible", api=hub)
    assert hub.calls == []


def test_an_existing_public_repo_is_refused_unless_allowed(release_root) -> None:
    hub = FakeHub(private=False)
    with pytest.raises(H.HubError, match="exists and is public"):
        H.upload_folder(release_root, "gt", "leibniz-legible", api=hub, log=lambda _m: None)
    assert not hub.files
    report = H.upload_folder(
        release_root, "gt", "leibniz-legible", api=hub, allow_public=True, log=lambda _m: None
    )
    assert not report.private and hub.files


def test_the_model_goes_to_a_model_repo_without_the_zip(tmp_path) -> None:
    from tests.test_release_model import K3_CARD, NAME, _checkpoint

    from leibniz.release.model import build_package

    out = tmp_path / "o"
    build_package(_checkpoint(tmp_path / "best"), K3_CARD, NAME, out)
    hub = FakeHub()
    H.upload_folder(out, "model", "leibniz-legible", api=hub, log=lambda _m: None)
    assert hub.created["repo_type"] == "model"
    assert hub.created["repo_id"] == f"leibniz-legible/{NAME}"
    assert "model.safetensors" in hub.files and "LICENSE" in hub.files
    assert not any(n.endswith(".zip") for n in hub.files)


def test_dry_run_needs_no_client_and_sends_nothing(release_root) -> None:
    lines: list[str] = []
    H.upload_folder(release_root, "gt", "leibniz-legible", dry_run=True, log=lines.append)
    assert (
        lines[0]
        == "DRY RUN  create_repo leibniz-legible/leibniz-gt (type dataset, private, exist_ok)"
    )
    assert lines[1].startswith("DRY RUN  upload_file README.md")
    assert "nothing sent" in lines[-1]
    with pytest.raises(H.HubError, match="no client"):
        H.upload_folder(release_root, "gt", "leibniz-legible")
    with pytest.raises(H.HubError, match="namespace"):
        H.upload_folder(release_root, "gt", "a/b", dry_run=True)


def test_the_token_comes_from_the_environment_only(release_root, capsys, monkeypatch) -> None:
    assert H.token_from_env({"HF_TOKEN": " hf_x "}) == "hf_x"
    with pytest.raises(H.HubError, match="HF_TOKEN is not set"):
        H.token_from_env({})
    source = (REPO / "tools/release/hf_upload.py").read_text()
    assert "--token" not in source and "token_from_env" in source
    monkeypatch.delenv("HF_TOKEN", raising=False)
    spec = importlib.util.spec_from_file_location("hf_upload", REPO / "tools/release/hf_upload.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    args = ["--root", str(release_root), "--record", "gt", "--namespace", "leibniz-legible"]
    assert tool.main([*args, "--dry-run"]) == 0
    assert "DRY RUN  create_repo leibniz-legible/leibniz-gt" in capsys.readouterr().out
    assert tool.main(args) == 1  # no token: it stops before any client exists
    assert "HF_TOKEN is not set" in capsys.readouterr().err
    assert (
        tool.main(
            ["--root", str(release_root), "--record", "gt-nc", "--namespace", "x", "--dry-run"]
        )
        == 1
    )
    assert "Zenodo only" in capsys.readouterr().err


def test_the_real_client_takes_the_token_explicitly() -> None:
    pytest.importorskip("huggingface_hub")
    api = H.make_api("hf_explicit")
    assert api.token == "hf_explicit"
