"""The model package (REL1 Task 2), on a tiny stand-in checkpoint."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import legal
from leibniz.cli import app
from leibniz.release import model as R
from leibniz.release import state as S

REPO = Path(__file__).resolve().parents[1]
K3_CARD = REPO / "reports/kurrent/k3-model-card-trocr.md"
NAME = "leibniz-kurrent-trocr"


def _checkpoint(path: Path) -> Path:
    """A stand-in for data/models/k3/trocr/best: the files save_checkpoint writes,
    and the leftovers a training folder can hold."""
    path.mkdir(parents=True)
    (path / "config.json").write_text('{"model_type": "vision-encoder-decoder"}')
    (path / "generation_config.json").write_text('{"use_cache": false, "num_beams": 4}')
    (path / "model.safetensors").write_bytes(b"\x00weights\x00" * 4096)
    (path / "preprocessor_config.json").write_text("{}")
    (path / "tokenizer_config.json").write_text("{}")
    (path / "vocab.json").write_text('{"a": 0}')
    (path / "merges.txt").write_text("#version: 0.2\n")
    (path / "special_tokens_map.json").write_text("{}")
    (path / "k3-training.json").write_text('{"epoch": 5}')
    (path / "optimizer.pt").write_bytes(b"not for release")  # left out
    (path / "trainer_state.json").write_text("{}")  # left out
    (path / "checkpoint-100").mkdir()  # left out
    return path


def test_package_holds_the_inference_files_and_nothing_else(tmp_path) -> None:
    weights = _checkpoint(tmp_path / "best")
    out = tmp_path / "release"
    pkg = R.build_package(weights, K3_CARD, NAME, out)
    folder = out / NAME
    names = sorted(p.name for p in folder.iterdir())
    assert "optimizer.pt" not in names and "trainer_state.json" not in names
    assert {"README.md", "LICENSE", "MANIFEST.json", "model.safetensors", "config.json"} <= set(
        names
    )
    assert pkg.left_out == ["optimizer.pt", "trainer_state.json", "checkpoint-100/"]
    manifest = json.loads((folder / "MANIFEST.json").read_text())
    assert manifest["model"] == NAME and manifest["reader"] == legal.READER_DE_VERSION
    assert manifest["licence"] == "CC BY 4.0" and manifest["left_out"] == pkg.left_out
    for f in manifest["files"]:  # sizes and SHA-256 are the files'
        path = folder / f["path"]
        assert path.stat().st_size == f["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == f["sha256"]
    listed = {f["path"] for f in manifest["files"]}
    assert "model.safetensors" in listed and "LICENSE" in listed and "README.md" not in listed
    # the zip for Zenodo: the folder, weights stored, nothing left out inside
    with zipfile.ZipFile(out / f"{NAME}.zip") as z:
        inside = z.namelist()
        assert f"{NAME}/model.safetensors" in inside and f"{NAME}/README.md" in inside
        assert not any("optimizer" in n for n in inside)
        assert z.getinfo(f"{NAME}/model.safetensors").compress_type == zipfile.ZIP_STORED
        assert z.read(f"{NAME}/model.safetensors") == (folder / "model.safetensors").read_bytes()
    assert not (out / f"{NAME}.zip.part").exists()
    assert S.load_release(out)["model_name"] == NAME


def test_readme_is_the_k3_card_brought_to_the_finish(tmp_path) -> None:
    pkg = R.build_package(_checkpoint(tmp_path / "best"), K3_CARD, NAME, tmp_path / "o")
    readme = (pkg.folder / "README.md").read_text(encoding="utf-8")
    assert pkg.card_markers_missing == []
    yaml = pytest.importorskip("yaml")
    front = yaml.safe_load(readme.split("---\n")[1])
    assert front["license"] == "cc-by-4.0" and front["library_name"] == "transformers"
    assert front["base_model"] == "dh-unibe/trocr-kurrent-XVI-XVII"
    assert front["pipeline_tag"] == "image-to-text" and front["language"] == ["de"]
    assert f"# {NAME} — a Kurrent reader" in readme and "(draft)" not in readme
    # K3's numbers stand as K3 wrote them …
    assert "| letter pool, all 134 letters | 28.61 % |" in readme
    assert "| validation set | 11.84 % |" in readme
    # … with LT1's table beside them
    assert "## Against whole-page reading by frontier vision models (LT1)" in readme
    assert "| Gemini 4 Argon (whole pages) | 24.2 % (17.3–31.5) |" in readme
    assert "34 letters (98 pages)" in readme
    # the K4 run it reads on the site
    assert "run 617 (`k3-trocr@runs-615-epoch-5`, scoped to German pages)" in readme
    assert "1,539,688 lines on 24,078 pages" in readme and "batch 16" in readme
    # the licence as the registry decides it
    assert "- **Licence of this model:** CC BY 4.0." in readme
    assert legal.output("model-k3-trocr").why in readme
    assert "open (CC BY 4.0 in this project's release" not in readme  # the draft's line
    # … and what "no NC input" means is said, not left for the reader to find
    assert "read from files whose publishers state non-commercial terms" in readme
    assert "published in the NC-derived deposit `leibniz-gt-nc`" in readme
    assert "a question in the project's lawyer memo" in readme
    assert "91 ms a line in that job" in readme
    # the usage with transformers and the decoder's cache
    assert "VisionEncoderDecoderModel.from_pretrained(repo)" in readme
    assert "use_cache=True" in readme and "key/value cache off" in readme
    assert "max_new_tokens=160" in readme and "num_beams=1" in readme
    # the training lines' precision: unmeasured until the audit is scored
    assert "**Precision of the training lines: unmeasured until the audit is scored.**" in readme
    assert "the Leibniz-Edition's Arbeitsstelle, Potsdam (returned 2026-11-06)" in readme
    assert "awaits its judge" not in readme
    assert "do not ingest as verified text" in readme
    assert "DOI: to be assigned at deposit" in readme


def test_licence_file_names_the_licence_and_carries_the_bases_notice(tmp_path) -> None:
    pkg = R.build_package(_checkpoint(tmp_path / "best"), K3_CARD, NAME, tmp_path / "o")
    text = (pkg.folder / "LICENSE").read_text(encoding="utf-8")
    assert "CC BY 4.0 (SPDX: cc-by-4.0)" in text
    assert "https://creativecommons.org/licenses/by/4.0/legalcode" in text
    assert "MIT License" in text and "Digital Humanities Center, University of Bern" in text
    assert "The above copyright notice and this permission notice shall be included" in text
    assert legal.output("model-k3-trocr").why in text


def test_dois_reach_the_card_the_citation_and_the_deposit_file(tmp_path) -> None:
    out = tmp_path / "o"
    release = S.load_release(out)
    S.set_doi(release, "model", "10.5072/zenodo.1004")
    S.set_doi(release, "transcriptions", "10.5072/zenodo.1001")
    release["hf"]["namespace"] = "leibniz-legible"
    release["creators"] = [{"name": "Family, Given", "orcid": "0000-0002-1825-0097"}]
    pkg = R.build_package(_checkpoint(tmp_path / "best"), K3_CARD, NAME, out, release=release)
    readme = (pkg.folder / "README.md").read_text(encoding="utf-8")
    assert "DOI: [10.5072/zenodo.1004](https://doi.org/10.5072/zenodo.1004)" in readme
    assert "https://doi.org/10.5072/zenodo.1004. Licensed CC BY 4.0." in readme
    assert 'repo = "leibniz-legible/leibniz-kurrent-trocr"' in readme
    assert "10.5072/zenodo.1001" in readme  # its readings
    record = json.loads((out / f"{NAME}.zenodo.json").read_text())
    meta = record["metadata"]
    assert record["record"] == "model" and meta["license"] == "cc-by-4.0"
    assert meta["upload_type"] == "other"  # the deposit API has no "model"
    assert meta["creators"][0]["orcid"] == "0000-0002-1825-0097"
    assert {(r["relation"], r["identifier"]) for r in meta["related_identifiers"]} == {
        ("isSupplementTo", "https://github.com/marchofhares/leibnizlegible"),
        ("isDerivedFrom", "https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII"),
        ("isDocumentedBy", "10.5281/zenodo.22782813"),
    }
    assert [f["name"] for f in record["files"]] == [
        "README.md",
        "LICENSE",
        "MANIFEST.json",
        f"{NAME}.zip",
    ]
    assert all((out / f["path"]).is_file() for f in record["files"])
    assert "28.6 %" in meta["description"] and "do not ingest" in meta["description"]


def test_a_card_that_changed_shape_still_yields_the_finished_statements(tmp_path) -> None:
    readme, missing = R.finish_card("Some other card.\n\n## Error rates\n", name=NAME)
    assert len(missing) == 3
    assert readme.count(f"# {NAME} — a Kurrent reader") == 1
    assert "## Data statement, brought up to date" in readme
    assert "unmeasured until the audit is scored" in readme and "use_cache=True" in readme


def test_refusals(tmp_path) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "config.json").write_text("{}")
    (bad / "pytorch_model.bin").write_bytes(b"x")  # no safetensors: refused
    with pytest.raises(R.ModelPackageError, match="model.safetensors"):
        R.checkpoint_files(bad)
    with pytest.raises(R.ModelPackageError, match="not a folder"):
        R.checkpoint_files(tmp_path / "missing")
    no_tok = tmp_path / "no-tok"
    no_tok.mkdir()
    for n in R.REQUIRED:
        (no_tok / n).write_text("{}")
    with pytest.raises(R.ModelPackageError, match="tokenizer"):
        R.checkpoint_files(no_tok)
    with pytest.raises(R.ModelPackageError, match="card"):
        R.build_package(_checkpoint(tmp_path / "best"), tmp_path / "no-card.md", NAME, tmp_path)


def test_release_model_cli(tmp_path) -> None:
    weights = _checkpoint(tmp_path / "best")
    out = tmp_path / "o"
    r = CliRunner().invoke(
        app,
        [
            "release",
            "model",
            "--weights",
            str(weights),
            "--card",
            str(K3_CARD),
            "--name",
            NAME,
            "--out",
            str(out),
            "--doi",
            "model=10.5072/zenodo.1004",
        ],
    )
    assert r.exit_code == 0, r.output
    assert "left out" in r.output and "optimizer.pt" in r.output
    assert (out / NAME / "model.safetensors").exists() and (out / f"{NAME}.zip").exists()
    assert "10.5072/zenodo.1004" in (out / NAME / "README.md").read_text()
    # the weights folder is read, never written
    assert sorted(p.name for p in weights.iterdir()) == sorted(
        [
            "checkpoint-100",
            "config.json",
            "generation_config.json",
            "k3-training.json",
            "merges.txt",
            "model.safetensors",
            "optimizer.pt",
            "preprocessor_config.json",
            "special_tokens_map.json",
            "tokenizer_config.json",
            "trainer_state.json",
            "vocab.json",
        ]
    )
    bad = CliRunner().invoke(
        app, ["release", "model", "--weights", str(tmp_path / "none"), "--out", str(out)]
    )
    assert bad.exit_code != 0
