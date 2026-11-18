"""The language models of R1 (Task 2): selection, hold-out, normalisation, the build.

The store is the fixture store of ``conftest.py`` with its German rows; the
edition cache is ``tests/fixtures/decoding/edition_cache.jsonl``. KenLM's
programs are replaced by a scripted runner; the test at the end runs the real
``lmplz`` and ``build_binary`` where they are to be found and decodes with the
model they write.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz.align.audit_reach import open_readonly
from leibniz.align.volumes import expired_volume_index
from leibniz.htr import cli as bench_cli
from leibniz.htr import decoding as D
from leibniz.htr import lm as L

CACHE = Path(__file__).parent / "fixtures" / "decoding" / "edition_cache.jsonl"
TODAY = date(2026, 11, 17)
runner = CliRunner()


def fake_kenlm(cmd, **_kw):
    """lmplz and build_binary, scripted: an ARPA header with the corpus's size, a
    one-byte binary; the commands are what the tests look at."""
    name = Path(cmd[0]).name
    if name == "lmplz":
        corpus = Path(cmd[cmd.index("--text") + 1])
        arpa = Path(cmd[cmd.index("--arpa") + 1])
        n = len(corpus.read_text(encoding="utf-8").splitlines())
        arpa.write_text(f"\\data\\\nngram 1={n}\nngram 2={2 * n}\n\n\\1-grams:\n", encoding="utf-8")
    else:
        Path(cmd[2]).write_bytes(b"\x00")
    return subprocess.CompletedProcess(cmd, 0, "", "")


@pytest.fixture
def kenlm_bin(tmp_path: Path) -> Path:
    """A directory with two files named like KenLM's programs (never executed)."""
    d = tmp_path / "kenlm-bin"
    d.mkdir()
    for name in ("lmplz", "build_binary"):
        (d / name).write_text("", encoding="utf-8")
    return d


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def build(store: Path, tmp_path: Path, kenlm_bin: Path, **kw):
    conn = open_readonly(store)
    try:
        return L.build(
            conn,
            cache=CACHE,
            out_dir=tmp_path / "lm",
            today=TODAY,
            heldout=kw.pop("heldout", tmp_path / "none.csv"),
            pool=kw.pop("pool", tmp_path / "none.csv"),
            val_pieces=kw.pop("val_pieces", tmp_path / "none.csv"),
            audits=kw.pop("audits", ()),
            bin_dir=kenlm_bin,
            run=kw.pop("run", fake_kenlm),
            **kw,
        )
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# normalisation
# --------------------------------------------------------------------------- #


def test_normalize_line_keeps_what_a_diplomatic_reader_writes() -> None:
    assert L.normalize_line("  Vt  sit\tveritas, in rebus. ") == "Vt sit veritas, in rebus."
    assert L.normalize_line("Müntz-Ord­nung") == "Müntz-Ordnung"  # NFC, soft hyphen gone
    assert L.normalize_line("Müntz", form="NFD") == "Müntz"
    assert L.normalize_line("Jeſus & Chriſtus-") == "Jeſus & Chriſtus-"  # nothing done to hyphens
    # the aligner's fold is the other variant
    assert L.normalize_line("Vt sit Veritas, in rébus!", fold="align") == "ut sit ueritas in rebus"
    with pytest.raises(ValueError):
        L.normalize_line("x", fold="other")


def test_wrap_text_cuts_running_text_at_spaces() -> None:
    text = "aaa bbb ccc ddd eee\nfff " + "g" * 12 + " hh"
    assert L.wrap_text(text, 8) == ["aaa bbb", "ccc ddd", "eee", "fff", "g" * 12, "hh"]
    assert L.wrap_text(text, 0) == text.splitlines()
    assert all(len(x) <= 48 for x in L.wrap_text("word " * 200, 48))


def test_corpus_line_is_characters_with_the_space_named() -> None:
    assert L.corpus_line("ut sit") == "u t <space> s i t"
    assert L.corpus_line("a b") == "a <U+00A0> b"


# --------------------------------------------------------------------------- #
# the legal gate
# --------------------------------------------------------------------------- #


def test_the_gate_wants_a_free_volume_and_an_open_channel() -> None:
    expired = expired_volume_index(TODAY)
    assert L.volume_key("IV,3") == (4, "3") and L.volume_key("I,Suppl") == (1, "Suppl")
    assert L.volume_key("transkriptionspool") is None and L.volume_key(None) is None
    assert L.gate([(4, "3")], ("ia",), expired) is None
    assert L.gate([(4, "3")], (), expired) is None  # no channel recorded: by the bucket
    assert L.gate([(4, "4")], ("ia",), expired) == "not_70_expired"
    assert L.gate([(4, "1")], ("potsdam",), expired) == "nc_channel"
    assert L.gate([(1, "1")], ("ia", "gwlb"), expired) == "nc_channel"
    assert L.gate([(1, "1")], ("letterpool",), expired) == "channel_not_released"
    assert L.gate([(1, "1")], ("unheard-of",), expired) == "channel_not_released"
    assert L.gate([None], ("ia",), expired) == "no_volume"
    assert L.gate([], ("ia",), expired) == "no_volume"


def test_read_edition_keeps_the_open_records_and_counts_the_rest() -> None:
    pieces, left = L.read_edition(CACHE, expired_volume_index(TODAY))
    assert set(pieces) == {"k-109", "k-4101", "k-fr1", "k-val", "k-short"}
    assert dict(left) == {"not_70_expired": 1, "nc_channel": 2, "no_refs": 1}
    assert all(len(line) <= L.WRAP for p in pieces.values() for line in p.edition)
    # on the first day of 2027 IV,4 is free and its record comes in
    later, left27 = L.read_edition(CACHE, expired_volume_index(date(2027, 1, 1)))
    assert "k-4402" in later and "not_70_expired" not in left27


def test_read_gt_takes_the_open_deposit_only(german_store_path: Path) -> None:
    conn = open_readonly(german_store_path)
    try:
        by_record, left, on_page = L.read_gt(conn, expired_volume_index(TODAY))
    finally:
        conn.close()
    # k-4101's four rows of the ia channel; its Potsdam row, k-4402's row of a volume not
    # yet free, the pool's nc row and the two rows without a record are left out
    assert set(by_record) == {"k-4101"} and len(by_record["k-4101"]) == 4
    assert "Seiner Churfürstl. Durchl. zu Braunschweig und" not in by_record["k-4101"]
    assert dict(left) == {
        "nc_channel": 1,
        "not_70_expired": 1,
        "nc_bucket": 1,
        "no_record": 2,
    }
    # every row with a record counts for the hold-out, whatever its bucket
    assert {r for recs in on_page.values() for r in recs} == {"k-4101", "k-4402"}
    assert L.page_of("00069377:0001:003") == "00069377:0001"
    assert L.page_of("00068642:0001#xywh=100,160,1800,60") == "00068642:0001"
    assert L.page_of("nothing") is None and L.page_of(None) is None


# --------------------------------------------------------------------------- #
# the build
# --------------------------------------------------------------------------- #


def test_build_writes_two_models_and_says_what_each_saw(
    german_store_path: Path, tmp_path: Path, kenlm_bin: Path
) -> None:
    res = build(german_store_path, tmp_path, kenlm_bin)
    s = res.summary
    la_fr, de = res.models["la_fr"], res.models["de"]
    # Latin and French: k-109, k-fr1 and k-val from the edition; no minted row is usable
    assert la_fr["records"] == 3 and set(la_fr["by_source"]) == {"edition"}
    # German: k-4101 from the edition and its four minted lines
    assert de["by_source"]["gt"] == {"lines": 4, "chars": 123, "records": 1}
    assert de["by_source"]["edition"]["records"] == 1 and de["records"] == 1
    assert s["other_language_records"] == 1  # k-short
    assert s["edition"]["left_out"] == {"nc_channel": 2, "no_refs": 1, "not_70_expired": 1}
    assert s["holdout"]["records"] == 0
    for m in (la_fr, de):
        stem = Path(m["arpa"]).with_suffix("")
        corpus = stem.with_suffix(".corpus.txt").read_text(encoding="utf-8").splitlines()
        assert len(corpus) == m["lines"] and any("<space>" in x for x in corpus)
        assert m["chars"] == sum(len(x.split(" ")) for x in corpus)
        assert Path(m["binary"]).exists()
        assert "-o 6" in m["lmplz"]["command"] and "-S 2G" in m["lmplz"]["command"]
        assert m["ngrams"] == {1: m["lines"], 2: 2 * m["lines"]}
        side = json.loads(stem.with_suffix(".json").read_text(encoding="utf-8"))
        assert side["fold"] == "none" and side["order"] == 6 and side["form"] == "NFC"
        assert D.lm_meta(m["binary"])["group"] == m["group"]
    # the German text is in the German file and nowhere else
    de_text = Path(de["arpa"]).with_suffix(".corpus.txt").read_text(encoding="utf-8")
    la_text = Path(la_fr["arpa"]).with_suffix(".corpus.txt").read_text(encoding="utf-8")
    assert "M ü n t z" in de_text and "M ü n t z" not in la_text
    assert "C a l c u l e m u s" in la_text and "j ' a y" in la_text
    # the pieces left out are in neither
    for gone in ("s a l u t a r i a", "V e r g n ü g e n", "s u c c e s s u r a"):
        assert gone not in de_text and gone not in la_text


def test_the_evaluation_sets_pieces_are_held_out_whole(
    german_store_path: Path, tmp_path: Path, kenlm_bin: Path
) -> None:
    # K3's validation pieces by record; the letter pool by page, through a minted row
    # (k-4101 on the German work) and through the factory's placement alone (k-109 has
    # no minted row that names it); a PHILIUMM page of a split; a judged audit line.
    val = write_csv(tmp_path / "val.csv", ["unit", "record_id"], [["k-val", "k-val"]])
    pool = write_csv(
        tmp_path / "pool.csv", ["letter_id", "page_ids"], [["1700-1", "00068642:0001 X:0001"]]
    )
    heldout = write_csv(
        tmp_path / "heldout.csv", ["page_id", "split"], [["00069377:0001", "val"], ["X:2", "noisy"]]
    )
    res = build(german_store_path, tmp_path, kenlm_bin, val_pieces=val, pool=pool, heldout=heldout)
    assert res.holdout.reasons == {
        "k-val": {"k3-val"},
        "k-109": {"letterpool"},
        "k-4101": {"philiumm:val"},
    }
    h = res.summary["holdout"]
    assert h["by_reason"] == {"k3-val": 1, "letterpool": 1, "philiumm:val": 1}
    assert h["sets"] == {"k3-val": 1, "letterpool": 2, "philiumm:noisy": 1, "philiumm:val": 1}
    assert h["left_out"]["gt"] == {"records": 1, "lines": 4}
    assert h["left_out"]["edition"]["records"] == 3
    # what is left: the French letter alone; no German model is written
    assert res.models["la_fr"]["records"] == 1 and res.models["de"]["lines"] == 0
    assert res.models["de"]["arpa"] is None
    text = Path(res.models["la_fr"]["arpa"]).with_suffix(".corpus.txt").read_text("utf-8")
    assert "C a l c u l e m u s" not in text and "j ' a y" in text
    paths = L.write_outputs(res, tmp_path / "reports")
    rows = list(csv.DictReader(paths["holdout"].open(encoding="utf-8")))
    assert {r["record_id"]: r["reasons"] for r in rows}["k-109"] == "letterpool"
    report = paths["report"].read_text(encoding="utf-8")
    assert "3 records are held out whole" in report and "the letter pool's pages" in report
    assert "PHILIUMM's pages, split `val`" in report and "not written" in report

    # without the placement k-109 is not found: only a minted row could name it
    res2 = build(
        german_store_path,
        tmp_path,
        kenlm_bin,
        val_pieces=val,
        pool=pool,
        heldout=heldout,
        place=False,
    )
    assert "k-109" not in res2.holdout and "k-4101" in res2.holdout

    # a judged line holds its piece out
    conn = open_readonly(german_store_path)
    ref = conn.execute(
        "SELECT line_image_ref FROM gt_lines WHERE record_id = 'k-4101' LIMIT 1"
    ).fetchone()[0]
    conn.close()
    audit = write_csv(tmp_path / "audit.csv", ["ref", "verdict"], [[ref, "correct"]])
    res3 = build(german_store_path, tmp_path, kenlm_bin, audits=[audit])
    assert res3.holdout.reasons == {"k-4101": {"audit"}}


def test_sources_fold_extras_and_the_readers_tokens(
    german_store_path: Path, tmp_path: Path, kenlm_bin: Path
) -> None:
    only_gt = build(german_store_path, tmp_path, kenlm_bin, sources=["gt"])
    assert only_gt.models["la_fr"]["lines"] == 0
    assert only_gt.models["de"]["by_source"] == {"gt": {"lines": 4, "chars": 123, "records": 1}}

    folded = build(german_store_path, tmp_path, kenlm_bin, fold="align", wrap=0)
    text = Path(folded.models["la_fr"]["arpa"]).with_suffix(".corpus.txt").read_text("utf-8")
    assert "c a l c u l e m u s" in text and "," not in text and "C" not in text
    assert folded.models["la_fr"]["fold"] == "align"
    assert D.DecoderSpec(kind="prefix-beam", lm=folded.models["la_fr"]["arpa"]).resolved_fold() == (
        "align"
    )

    extra = tmp_path / "mine.txt"
    extra.write_text("Dieses ist ein Zusatz\n\nund noch einer\n", encoding="utf-8")
    table = D.TokenTable.from_chars(list(" abcdefghiklmnoprstuvwzDIEMSZ.,"))
    tokens = table.write(tmp_path / "tokens.txt")
    with_extra = build(
        german_store_path, tmp_path, kenlm_bin, extras={"mine": ("de", extra)}, tokens=tokens
    )
    de = with_extra.models["de"]
    assert de["by_source"]["extra:mine"] == {"lines": 2, "chars": 35, "records": 0}
    assert with_extra.summary["extras"]["mine"]["group"] == "de"
    oc = de["outside_codec"]
    assert oc["characters"] > 0 and 0 < oc["share"] < 1
    assert "ü" in {ch for ch, _ in oc["most"]}
    report = L.render_report(with_extra.summary)
    assert "extra:mine" in report and "against the reader's tokens" in report
    with pytest.raises(ValueError, match="unknown group"):
        build(german_store_path, tmp_path, kenlm_bin, extras={"mine": ("xx", extra)})
    with pytest.raises(ValueError, match="unknown sources"):
        build(german_store_path, tmp_path, kenlm_bin, sources=["pool"])
    with pytest.raises(ValueError, match="unknown form"):
        build(german_store_path, tmp_path, kenlm_bin, form="NFKC")


def test_lmplz_falls_back_on_too_little_text_and_failures_are_loud(
    tmp_path: Path, kenlm_bin: Path, monkeypatch
) -> None:
    calls: list[list[str]] = []

    def picky(cmd, **_kw):
        calls.append(list(cmd))
        if "--discount_fallback" not in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "BadDiscountException: discount ...")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    corpus = tmp_path / "c.txt"
    corpus.write_text("a b\n", encoding="utf-8")
    info = L.estimate(corpus, tmp_path / "c.arpa", bin_dir=kenlm_bin, run=picky)
    assert info["discount_fallback"] and info["command"].endswith("--discount_fallback")
    assert len(calls) == 2

    def broken(cmd, **_kw):
        return subprocess.CompletedProcess(cmd, 2, "", "no space left on device")

    with pytest.raises(RuntimeError, match="no space left"):
        L.estimate(corpus, tmp_path / "c.arpa", bin_dir=kenlm_bin, run=broken)
    with pytest.raises(RuntimeError, match="build_binary failed"):
        L.binarize(tmp_path / "c.arpa", tmp_path / "c.bin", bin_dir=kenlm_bin, run=broken)
    # nowhere to be found
    monkeypatch.delenv("KENLM_BIN", raising=False)
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    with pytest.raises(L.KenLMMissing, match="lmplz not found"):
        L.find_tool("lmplz")
    monkeypatch.setenv("KENLM_BIN", str(kenlm_bin))
    assert L.find_tool("lmplz") == kenlm_bin / "lmplz"


def test_lm_build_cli(
    german_store_path: Path, tmp_path: Path, kenlm_bin: Path, monkeypatch
) -> None:
    monkeypatch.setattr(subprocess, "run", fake_kenlm)
    args = [
        "lm-build",
        "--db",
        str(german_store_path),
        "--cache",
        str(CACHE),
        "--out",
        str(tmp_path / "lm"),
        "--heldout",
        str(tmp_path / "none.csv"),
        "--pool",
        str(tmp_path / "none.csv"),
        "--val-pieces",
        str(tmp_path / "none.csv"),
        "--audit",
        str(tmp_path / "none.csv"),
        "--kenlm-bin",
        str(kenlm_bin),
        "--today",
        "2026-11-17",
        "--reports-dir",
        str(tmp_path / "reports"),
    ]
    result = runner.invoke(bench_cli.app, args)
    assert result.exit_code == 0, result.output
    assert "Latin and French" in result.output and "German" in result.output
    summary = json.loads((tmp_path / "reports" / "lm-build.json").read_text(encoding="utf-8"))
    assert summary["order"] == 6 and summary["models"]["de"]["records"] == 1
    assert (tmp_path / "lm" / "la-fr.arpa").exists() and (tmp_path / "lm" / "de.bin").exists()
    md = (tmp_path / "reports" / "lm-build.md").read_text(encoding="utf-8")
    assert "What each model saw" in md and "The held-out pieces" in md
    # no store, a malformed --extra, no KenLM
    missing = runner.invoke(bench_cli.app, ["lm-build", "--db", str(tmp_path / "no.sqlite")])
    assert missing.exit_code == 1
    bad = runner.invoke(bench_cli.app, [*args, "--extra", "mine"])
    assert bad.exit_code == 2
    monkeypatch.delenv("KENLM_BIN", raising=False)
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    none = runner.invoke(bench_cli.app, [*args[:-10], "--reports-dir", str(tmp_path / "r2")])
    assert none.exit_code == 1 and "not found" in " ".join(none.output.split())


# --------------------------------------------------------------------------- #
# the real thing, where KenLM's programs are installed
# --------------------------------------------------------------------------- #


def test_a_toy_model_from_the_fixture_store_decodes(
    german_store_path: Path, tmp_path: Path
) -> None:
    try:
        L.find_tool("lmplz")
        L.find_tool("build_binary")
    except L.KenLMMissing:
        pytest.skip("KenLM's lmplz and build_binary are not installed")
    conn = open_readonly(german_store_path)
    try:
        res = L.build(
            conn,
            cache=CACHE,
            out_dir=tmp_path / "lm",
            order=3,
            today=TODAY,
            heldout=tmp_path / "none.csv",
            pool=tmp_path / "none.csv",
            val_pieces=tmp_path / "none.csv",
            audits=(),
        )
    finally:
        conn.close()
    la = res.models["la_fr"]
    assert la["lmplz"]["discount_fallback"] in (True, False)
    arpa = D.ArpaLM.load(la["arpa"])
    assert arpa.order == 3 and la["ngrams"][1] == len(arpa.vocab)
    # the model prefers the text it saw to the same letters shuffled
    seen = [D.lm_token(c) for c in "quod enim"]
    assert arpa.sentence(seen) > arpa.sentence(list(reversed(seen))) + 2.0

    # a near-tie between "quod" and "qvod": greedy reads the v, the model the u
    chars = sorted({c for c in "quod enim v"})
    table = D.TokenTable.from_chars(chars)
    lab = {c: i + 1 for i, c in enumerate(chars)}

    def frame(dist: dict) -> list[float]:
        named = {(0 if k is None else lab[k]): v for k, v in dist.items()}
        rest = (1.0 - sum(named.values())) / (len(table) - len(named))
        return [named.get(i, rest) for i in range(len(table))]

    frames: list[list[float]] = []
    for ch in "quod enim":
        dist = {"u": 0.46, "v": 0.50} if ch == "u" else {ch: 0.97}
        frames += [frame(dist), frame(dist), frame({None: 0.97})]
    assert D.decode_greedy(frames, table).text == "qvod enim"
    assert D.decode_prefix_beam(frames, table, arpa, lm_weight=1.5).text == "quod enim"
    try:
        beam = D.Decoder(D.BEAM_LM, table, lm=la["binary"], lm_weight=1.5)
    except ModuleNotFoundError:
        return  # flashlight-text is not installed: the prefix beam has proved the path
    assert beam.decode_frames(frames).text == "quod enim"
