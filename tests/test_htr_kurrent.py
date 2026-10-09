"""Tests for the Kurrent smoke test (offline: a fixture package and the echo engine)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz.cli import app
from leibniz.htr import kurrent as K
from leibniz.htr.bench import EchoEngine, LinePair

runner = CliRunner()

LINES = [
    ("dresden1673-0001-tl_1", "Sonnabend, Den 21. Decembris, Wardt die", b"img-1"),
    ("dresden1673-0001-tl_2", "Hochfürſtl. Durchl. in der Kirchen", b"img-2"),
    ("dresden1673-0002-tl_1", "vnd nach gehaltener Predigt", b"img-3"),
]

# A stand-in for the package's scorer: the same two policies, printed as JSON.
_EVALUATE_PY = r"""
import json, sys, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def d(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        row = [i]
        for j, y in enumerate(b, 1):
            row.append(min(prev[j] + 1, row[-1] + 1, prev[j - 1] + (x != y)))
        prev = row
    return prev[-1]

def nfc(t):
    return unicodedata.normalize("NFC", t)

def rd(t):
    return " ".join(nfc(t).replace("ſ", "s").split())

def load(p):
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["id"]: r["text"] for r in rows}

refs = load(ROOT / "data/published_gt.jsonl")
preds = load(Path(sys.argv[1]))
out = {}
for name, f in (("strict_nfc", nfc), ("reading_long_s_and_whitespace", rd)):
    ce = cn = 0
    for k, r in refs.items():
        ce += d(f(r), f(preds[k]))
        cn += len(f(r))
    out[name] = {"cer": ce / cn}
print(json.dumps({"scores": out}))
"""


def _package(root: Path) -> Path:
    (root / "data").mkdir(parents=True)
    (root / "images" / "lines" / "dresden1673").mkdir(parents=True)
    (root / "reports").mkdir()
    (root / "scripts").mkdir()
    rows = []
    for i, (lid, text, img) in enumerate(LINES):
        rel = f"images/lines/dresden1673/{lid}.png"
        (root / rel).write_bytes(img)
        rows.append(
            {
                "id": lid,
                "text": text,
                "image_path": rel,
                "page_id": lid.rsplit("-", 1)[0],
                "document_id": "slub-Mscr-Dresd-K-117",
                "language_hint": "de",
                "annotation_license_applied": "CC-BY-NC-SA-4.0",
                "n": i,
            }
        )
    (root / "data" / "published_gt.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8"
    )
    (root / "reports" / "dataset-summary.json").write_text(
        json.dumps({"published_gt_lines": 3, "published_gt_pages": 2}), encoding="utf-8"
    )
    (root / "scripts" / "evaluate.py").write_text(_EVALUATE_PY, encoding="utf-8")
    return root


def test_load_dresden_pairs_crops_with_labels(tmp_path: Path) -> None:
    pkg = _package(tmp_path / "pkg")
    pairs = K.load_dresden(pkg)
    assert [p.line_id for p in pairs] == [lid for lid, _, _ in LINES]
    assert pairs[1].reference == LINES[1][1]
    assert pairs[0].image_bytes() == b"img-1"
    assert pairs[0].lang == "de" and pairs[0].meta["page_id"] == "dresden1673-0001"
    assert len(K.load_dresden(pkg, limit=2)) == 2
    with pytest.raises(FileNotFoundError):
        K.load_dresden(tmp_path / "nowhere")


def test_package_policies_match_the_package_definitions() -> None:
    assert K.package_strict("Hochfürſtl.") == "Hochfürſtl."
    assert K.package_reading("Hoch  fürſtl.\n") == "Hoch fürstl."


def test_package_scores_cer_wer_exact() -> None:
    pairs = [LinePair("a", "vnd daß", image_bytes_=b""), LinePair("b", "ſo iſt", image_bytes_=b"")]
    sc = K.package_scores(pairs, ["vnd daß", "so ist"])
    assert sc["strict_nfc"]["exact_lines"] == 1
    assert sc["strict_nfc"]["character_edits"] == 2  # the two long s
    assert sc["reading_long_s_and_whitespace"]["exact_lines"] == 2
    assert sc["reading_long_s_and_whitespace"]["cer"] == 0.0


def test_run_candidate_caches_and_scores(tmp_path: Path) -> None:
    pkg = _package(tmp_path / "pkg")
    pairs = K.load_dresden(pkg)
    smoke = tmp_path / "smoke"
    perfect = EchoEngine({img: text for _, text, img in LINES})
    cand = K.CANDIDATES["echo"]
    res = K.run_candidate(
        cand, pairs, smoke_dir=smoke, package_dir=pkg, engine_factory=lambda _c: perfect
    )
    assert res.status == "ok" and not res.cached and res.n_lines == 3 and res.n_empty == 0
    assert res.scores["philiumm"]["cer"] == 0.0 and res.scores["strict"]["cer"] == 0.0
    assert res.package["strict_nfc"]["exact_lines"] == 3
    assert res.package_script is not None
    assert res.package_script["scores"]["strict_nfc"]["cer"] == 0.0
    assert (smoke / "echo.hyps.jsonl").exists() and (smoke / "echo.meta.json").exists()
    # a second run reads the cache and never touches the engine
    res2 = K.run_candidate(
        cand, pairs, smoke_dir=smoke, package_dir=pkg, engine_factory=lambda _c: 1 / 0
    )
    assert res2.cached and res2.scores["philiumm"]["cer"] == 0.0
    # --force reads again; a failing reader is recorded, not raised
    res3 = K.run_candidate(
        cand, pairs, smoke_dir=smoke, package_dir=pkg, force=True, engine_factory=lambda _c: 1 / 0
    )
    assert res3.status.startswith("skipped:ZeroDivisionError")


def test_run_smoke_and_report_without_a_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    pkg = _package(tmp_path / "pkg")
    pairs = K.load_dresden(pkg)
    blank = EchoEngine(default="")
    res = K.run_smoke(
        pairs,
        [K.CANDIDATES["echo"]],
        smoke_dir=tmp_path / "smoke",
        package_dir=pkg,
        engine_factory=lambda _c: blank,
    )
    assert res.vision is None and res.n_lines == 3 and res.n_pages == 2
    r = res.results[0]
    assert r.n_empty == 3 and r.scores["philiumm"]["cer"] == 1.0
    md, js = K.write_reports(res, tmp_path / "reports")
    text = md.read_text(encoding="utf-8")
    assert "A ranking, not a benchmark" in text
    assert "No vision row" in text
    for _, ref, _ in LINES:
        assert ref not in text  # no Dresden text in a committed report
    payload = json.loads(js.read_text(encoding="utf-8"))
    assert payload["results"][0]["ms_per_line"] is not None


def test_vision_engine_none_without_keys() -> None:
    assert K.vision_engine({}) is None


def test_pick_device_keeps_an_explicit_request() -> None:
    assert K.pick_device("cpu") == "cpu"
    assert K.pick_device("cuda:1") == "cuda:1"
    assert K.pick_device("auto") in ("cpu", "cuda")


def test_cli_kurrent_smoke_with_echo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    pkg = _package(tmp_path / "pkg")
    result = runner.invoke(
        app,
        [
            "bench",
            "kurrent-smoke",
            "--package",
            str(pkg),
            "--candidates",
            "echo",
            "--device",
            "cpu",
            "--smoke-dir",
            str(tmp_path / "smoke"),
            "--reports-dir",
            str(tmp_path / "reports"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "echo" in result.output
    assert (tmp_path / "reports" / "bootstrap-candidates.md").exists()
    assert (tmp_path / "reports" / "bootstrap-candidates.json").exists()
