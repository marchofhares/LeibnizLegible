"""Tests for artifact URL building and cache-first streaming download (offline)."""

from __future__ import annotations

from contextlib import contextmanager

from leibniz.htr import artifacts


def test_url_builders() -> None:
    u = artifacts._zenodo_url("21457538", "model.safetensors")
    assert "records/21457538/files/model.safetensors" in u and u.endswith("download=1")
    h = artifacts._hf_url(artifacts.HF_DATASET, "data/val.parquet")
    assert "resolve/main/data/val.parquet" in h


def test_artifact_paths(tmp_path) -> None:
    paths = artifacts.artifact_paths(tmp_path / "m", tmp_path / "g")
    assert paths.model.name == artifacts.MODEL_FILE
    assert not paths.model_present and not paths.val_present
    paths.model.parent.mkdir(parents=True)
    paths.model.write_bytes(b"x")
    assert paths.model_present


class _StreamResp:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    def raise_for_status(self) -> None:
        pass

    def iter_bytes(self, chunk_size):  # noqa: ARG002
        yield from self._chunks


class _StreamClient:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.calls = 0

    @contextmanager
    def stream(self, method, url):  # noqa: ARG002
        self.calls += 1
        yield _StreamResp(self.chunks)


def test_download_file_streams_and_is_cache_first(tmp_path) -> None:
    dest = tmp_path / "sub" / "file.bin"
    client = _StreamClient([b"abc", b"def"])
    out = artifacts.download_file("http://x/file", dest, client=client)
    assert out.read_bytes() == b"abcdef"
    assert client.calls == 1
    assert not (tmp_path / "sub" / "file.bin.part").exists()  # temp cleaned up

    # Second call: file already present and non-empty -> no new stream.
    out2 = artifacts.download_file("http://x/file", dest, client=client)
    assert out2 == dest
    assert client.calls == 1  # unchanged: cache-first skip


def test_fetch_model_uses_injected_client(tmp_path) -> None:
    client = _StreamClient([b"WEIGHTS"])
    path = artifacts.fetch_model(models_dir=tmp_path, client=client, aux=False)
    assert path.read_bytes() == b"WEIGHTS"
    assert path.name == artifacts.MODEL_FILE


def test_attribution_mentions_dois_and_license() -> None:
    assert "CC BY 4.0" in artifacts.ATTRIBUTION
    assert artifacts.ZENODO_HTR_RECORD in artifacts.ATTRIBUTION
    assert artifacts.ZENODO_SEG_RECORD in artifacts.ATTRIBUTION
