"""Tests for the page-level reader (LT1 Task 1): page lists, the pool draw, image
preparation, the image store, the resumable read with its one retry and its cost cap,
the dry-run plan and the Hub fetch — offline, a scripted engine, PIL-made images."""

from __future__ import annotations

import io
import json
from pathlib import Path

import httpx
import pytest

from leibniz.htr import engines as ENG
from leibniz.htr import pageread as R

pytest.importorskip("PIL")

TESTSET = Path("reports/kurrent/letterpool-testset.csv")


def _jpeg(w: int, h: int, color=(200, 190, 160)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Page lists
# --------------------------------------------------------------------------- #


def test_page_row_fills_work_and_seq_and_validates() -> None:
    r = R.PageRow(page_id="DE-611-HS-859659:0003", set="pool")
    assert (r.work_id, r.seq) == ("DE-611-HS-859659", 3)
    assert R.image_url(r) == "https://images.leibnizlegible.com/DE-611-HS-859659/0003.jpg"
    with pytest.raises(ValueError):
        R.PageRow(page_id="x", set="other")
    with pytest.raises(ValueError):
        R.PageRow(page_id="x", set="pool", column="middle")


def test_page_list_roundtrip(tmp_path: Path) -> None:
    rows = [
        R.PageRow(
            "philiumm:LH_1_2_1_0004r", "philiumm", "hf:val/LH_1_2_1_0004r.jpg", ref="LH_1_2_1_0004r"
        ),
        R.PageRow("W:0001", "pool", letter_id="1714-1", hand="L", half="selection"),
    ]
    path = R.write_page_list(rows, tmp_path / "list.csv")
    back = R.read_page_list(path)
    assert back == rows
    assert R.image_url(back[0]) == R.HF_RESOLVE + "val/LH_1_2_1_0004r.jpg"
    assert R.cache_name(back[0]) == "val/LH_1_2_1_0004r.jpg"
    assert R.cache_name(back[1]) == "W/0001.jpg"


def test_philiumm_rows_split_openings_and_carry_the_store_page() -> None:
    files = [
        "val/LH_1_2_1_0004r.jpg",
        "val/LH_35_1_27_0009v-0008r.jpg",
        "val/0006_page_1_docId_2.jpg",
    ]
    held = {"LH_1_2_1_0004r": ["00068282:0007"], "LH_35_1_27_0009v-0008r": ["a:0018", "a:0015"]}
    rows = R.philiumm_rows(files, held)
    by = {(r.page_id, r.column): r for r in rows}
    assert len(rows) == 4
    single = by[("philiumm:LH_1_2_1_0004r", "whole")]
    assert (single.work_id, single.seq, single.ref) == ("00068282", 7, "LH_1_2_1_0004r")
    assert ("philiumm:LH_35_1_27_0009v-0008r", "left") in by
    assert ("philiumm:LH_35_1_27_0009v-0008r", "right") in by
    assert by[("philiumm:LH_35_1_27_0009v-0008r", "left")].work_id == ""  # two pages: none named
    assert by[("philiumm:0006_page_1_docId_2", "whole")].source == "hf:val/0006_page_1_docId_2.jpg"
    whole = R.philiumm_rows(files, held, split_openings=False)
    assert len(whole) == 3 and all(r.column == "whole" for r in whole)
    assert R.is_opening("LH_4_7C_0107r-0108v") and not R.is_opening("LH_38_0139v")


def test_read_heldout_keeps_the_val_split_only(tmp_path: Path) -> None:
    p = tmp_path / "heldout.csv"
    p.write_text(
        "page_id,work_id,file,split,status\n"
        "a:0001,a,F1,val,resolved\na:0002,a,F1,val,resolved\nb:0001,b,F2,noisy,matched\n",
        encoding="utf-8",
    )
    assert R.read_heldout(p) == {"F1": ["a:0001", "a:0002"]}


def test_draw_pool_pages_is_seeded_balanced_and_whole_letters() -> None:
    letters = R.read_testset_rows(TESTSET)
    rows = R.draw_pool_pages(letters, n_pages=100, seed=20261028)
    assert len(rows) == 100
    assert sum(1 for r in rows if r.hand == "L") == 50
    assert sum(1 for r in rows if r.hand == "K/k") == 50
    assert {r.half for r in rows} == {"selection", "test"}
    by_letter = {r["letter_id"]: r for r in letters}
    for lid in {r.letter_id for r in rows}:
        drawn = [r.page_id for r in rows if r.letter_id == lid]
        assert drawn == by_letter[lid]["page_ids"].split()  # every page of the letter, in order
    assert R.draw_pool_pages(letters, n_pages=100, seed=20261028) == rows  # seeded
    assert R.draw_pool_pages(letters, n_pages=100, seed=1) != rows


# --------------------------------------------------------------------------- #
# Images
# --------------------------------------------------------------------------- #


def test_prepare_image_downscales_and_crops_columns() -> None:
    data = _jpeg(3000, 4000)
    p = R.prepare_image(data, long_side=1000)
    assert (p.width, p.height, p.orig_width, p.orig_height) == (750, 1000, 3000, 4000)
    assert p.data[:3] == b"\xff\xd8\xff" and p.n_bytes > 0
    left = R.prepare_image(data, long_side=1000, column="left")
    assert (left.width, left.height) == (375, 1000) and left.column == "left"
    small = R.prepare_image(_jpeg(400, 300), long_side=1000)
    assert (small.width, small.height) == (400, 300)  # never upscaled
    with pytest.raises(ValueError):
        R.prepare_image(data, column="middle")


def test_estimate_input_tokens_follows_each_api_rule() -> None:
    a = R.estimate_input_tokens("anthropic", 1178, 2000)
    assert a == ENG.anthropic_image_tokens(1178, 2000) + R.PROMPT_TOKENS_ASSUMED
    assert ENG.anthropic_image_tokens(1178, 2000) == 43 * 72  # ⌈1178/28⌉ × ⌈2000/28⌉
    assert ENG.anthropic_image_tokens(3840, 2160) <= ENG.ANTHROPIC_MAX_VISUAL_TOKENS
    assert ENG.gemini_image_tokens(300, 300) == 258
    assert ENG.gemini_image_tokens(960, 540) == 258 * 6  # the documentation's own example
    assert ENG.openai_image_tokens(1024, 1024) == 85 + 170 * 4
    assert ENG.openai_image_tokens(1024, 1024, detail="low") == 85


def test_image_store_prefers_local_then_cache_then_fetch(tmp_path: Path) -> None:
    root = tmp_path / "images"
    (root / "W").mkdir(parents=True)
    (root / "W" / "0001.jpg").write_bytes(b"LOCAL")
    calls: list[str] = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        return b"FETCHED"

    store = R.ImageStore(images_root=root, cache_dir=tmp_path / "cache", fetch=fetch)
    assert store.get(R.PageRow("W:0001", "pool")) == b"LOCAL"
    assert store.get(R.PageRow("W:0002", "pool")) == b"FETCHED"
    assert calls == ["https://images.leibnizlegible.com/W/0002.jpg"]
    assert (tmp_path / "cache" / "W" / "0002.jpg").read_bytes() == b"FETCHED"
    assert store.get(R.PageRow("W:0002", "pool")) == b"FETCHED" and len(calls) == 1  # cached
    hf = R.PageRow("philiumm:X", "philiumm", "hf:val/X.jpg", ref="X")
    assert store.get(hf) == b"FETCHED" and calls[-1] == R.HF_RESOLVE + "val/X.jpg"
    (tmp_path / "val").mkdir()
    (tmp_path / "val" / "X.jpg").write_bytes(b"VAL")
    store2 = R.ImageStore(val_pages=tmp_path / "val")
    assert store2.get(hf) == b"VAL"
    with pytest.raises(FileNotFoundError):
        R.ImageStore().get(R.PageRow("W:0009", "pool"))


# --------------------------------------------------------------------------- #
# The read
# --------------------------------------------------------------------------- #


class _Scripted:
    """A page engine with a scripted reply per call (text, stop) and usage."""

    name = "scripted"

    def __init__(self, replies, version="m-1") -> None:
        self.replies = list(replies)
        self.version = version
        self.calls: list[tuple[bytes, str]] = []

    def settings(self) -> dict:
        return {"max_tokens": 4000, "temperature": 0.0, "reasoning": "low"}

    def reply(self, data: bytes, *, prompt: str | None = None) -> ENG.ApiReply:
        self.calls.append((data, prompt or ""))
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        text, stop = item
        return ENG.ApiReply(text=text, stop=stop, input_tokens=1000, output_tokens=200)


def _rows(n: int) -> list[R.PageRow]:
    return [
        R.PageRow(f"W:{i:04d}", "pool", letter_id="L1", hand="L", half="test")
        for i in range(1, n + 1)
    ]


def _store(tmp_path: Path, n: int) -> R.ImageStore:
    root = tmp_path / "images" / "W"
    root.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        (root / f"{i:04d}.jpg").write_bytes(_jpeg(600, 900, (100 + i, 100, 100)))
    return R.ImageStore(images_root=tmp_path / "images")


def test_read_pages_records_retries_and_resumes(tmp_path: Path) -> None:
    rows = _rows(4)
    store = _store(tmp_path, 4)
    eng = _Scripted(
        [
            ("alpha\nbeta", "end"),  # page 1 ok
            ("", "refusal"),  # page 2 refused, then ok on the retry
            ("gamma", "end"),
            ("delta delta", "length"),  # page 3 runaway twice
            ("delta delta", "length"),
            ("", "end"),  # page 4 empty twice
            ("   ", "end"),
        ]
    )
    out = tmp_path / "out" / "m-1.jsonl"
    stats = R.read_pages(
        rows, eng, out, images=store, engine_name="echo", long_side=500, sleep=lambda s: None
    )
    assert stats.read == 4 and stats.retried == 3 and stats.skipped == 0
    assert stats.statuses == {"ok": 2, "runaway": 1, "empty": 1}
    assert stats.input_tokens == 7000 and stats.output_tokens == 1400
    got = R.load_readings(out)
    assert [got[(f"W:{i:04d}", "whole")]["status"] for i in range(1, 5)] == [
        "ok",
        "ok",
        "runaway",
        "empty",
    ]
    two = got[("W:0002", "whole")]
    assert two["first_status"] == "refused" and two["attempts"] == 2 and two["lines"] == ["gamma"]
    assert two["usage"] == {"input": 2000, "output": 400, "reasoning": 0}
    one = got[("W:0001", "whole")]
    assert one["lines"] == ["alpha", "beta"] and one["image"]["width"] == 333
    assert one["image"]["orig_width"] == 600 and one["settings"]["long_side"] == 500
    assert one["settings"]["prompt_sha256"] and one["engine"] == "echo" and one["model"] == "m-1"
    assert got[("W:0003", "whole")]["text"] == "delta delta"  # the runaway's partial text kept
    assert R.page_texts(got) == {
        "W:0001": "alpha\nbeta",
        "W:0002": "gamma",
        "W:0003": "",
        "W:0004": "",
    }
    assert R.failed_pages(got) == {"W:0003", "W:0004"}
    assert all(c[1] == R.PAGE_PROMPT for c in eng.calls)
    # A second run reads nothing; --redo failed reads the two failed pages again.
    again = R.read_pages(
        rows, _Scripted([]), out, images=store, engine_name="echo", sleep=lambda s: None
    )
    assert again.read == 0 and again.skipped == 4
    redo = R.read_pages(
        rows,
        _Scripted([("eps", "end"), ("zeta", "end")]),
        out,
        images=store,
        engine_name="echo",
        redo="failed",
        sleep=lambda s: None,
    )
    assert redo.read == 2 and redo.skipped == 2
    got2 = R.load_readings(out)
    assert got2[("W:0003", "whole")]["status"] == "ok" and got2[("W:0004", "whole")]["lines"] == [
        "zeta"
    ]
    assert len(out.read_text(encoding="utf-8").splitlines()) == 6  # append-only


def test_read_pages_stops_at_the_cost_cap_and_skips_missing_images(tmp_path: Path) -> None:
    rows = _rows(3) + [R.PageRow("W:0009", "pool")]
    store = _store(tmp_path, 3)
    eng = _Scripted([("a", "end")] * 4, version="gemini-3.1-pro-preview")
    stats = R.read_pages(
        rows,
        eng,
        tmp_path / "o.jsonl",
        images=store,
        engine_name="gemini",
        max_cost=0.003,
        sleep=lambda s: None,
    )
    # One call costs 1000 × 2.00 + 200 × 12.00 per 1M = 0.0044 USD: the second page is never called.
    assert stats.read == 1 and stats.stopped_at_cap and stats.cost == pytest.approx(0.0044)
    stats2 = R.read_pages(
        rows, eng, tmp_path / "o.jsonl", images=store, engine_name="gemini", sleep=lambda s: None
    )
    assert stats2.read == 2 and stats2.failed_images == 1 and stats2.skipped == 1


def test_read_pages_records_an_api_error_and_does_not_retry_a_4xx(tmp_path: Path) -> None:
    rows = _rows(2)
    store = _store(tmp_path, 2)
    req = httpx.Request("POST", "https://api.example/x")
    e400 = httpx.HTTPStatusError("bad", request=req, response=httpx.Response(400, request=req))
    e503 = httpx.HTTPStatusError("busy", request=req, response=httpx.Response(503, request=req))
    eng = _Scripted([e400, e503, ("fine", "end")])
    stats = R.read_pages(
        rows, eng, tmp_path / "o.jsonl", images=store, engine_name="echo", sleep=lambda s: None
    )
    got = R.load_readings(tmp_path / "o.jsonl")
    assert (
        got[("W:0001", "whole")]["status"] == "error" and got[("W:0001", "whole")]["attempts"] == 1
    )
    assert "HTTP 400" in got[("W:0001", "whole")]["error"]
    assert got[("W:0002", "whole")]["status"] == "ok" and got[("W:0002", "whole")]["attempts"] == 2
    assert stats.statuses == {"error": 1, "ok": 1} and stats.retried == 1


def test_status_of_split_lines_and_call_engine_fallback() -> None:
    assert R.status_of(ENG.ApiReply("x", "refusal")) == "refused"
    assert R.status_of(ENG.ApiReply("x", "length")) == "runaway"
    assert R.status_of(ENG.ApiReply("  \n", "end")) == "empty"
    assert R.status_of(ENG.ApiReply("x", "end")) == "ok"
    assert R.split_lines(" a \n\n b\r\nc ") == ["a", "b", "c"]
    from leibniz.htr.bench import EchoEngine

    rep = R.call_engine(EchoEngine({b"img": "echoed"}), b"img")
    assert (rep.text, rep.stop) == ("echoed", "end")
    assert ENG.classify_stop("end_turn") == "end" and ENG.classify_stop("max_tokens") == "length"
    assert (
        ENG.classify_stop("content_filter") == "refusal" and ENG.classify_stop("??") == "other:??"
    )


def test_plan_read_estimates_from_known_sizes_and_the_assumption(tmp_path: Path) -> None:
    rows = _rows(2)
    store = _store(tmp_path, 1)  # only page 1 is on disk
    plan = R.plan_read(rows, "anthropic", "claude-fable-5-1", images=store, long_side=1000)
    assert plan.calls == 2 and plan.image_sizes_known == 1 and plan.rate == (10.0, 50.0)
    known = R.estimate_input_tokens("anthropic", 600, 900)  # on disk, under the long side: as is
    assumed = R.estimate_input_tokens("anthropic", 667, 1000)  # not on disk: 2/3 × 1000 by 1000
    assert plan.input_tokens == known + assumed and plan.output_tokens_assumed == 3000
    assert plan.cost == pytest.approx(plan.input_tokens * 10 / 1e6 + 3000 * 50 / 1e6)
    assert plan.reasoning == "low" and plan.pages == {"pool": 2}
    out = tmp_path / "r.jsonl"
    out.write_text(json.dumps({"page_id": "W:0001", "column": "whole", "status": "ok"}) + "\n")
    plan2 = R.plan_read(rows, "openai", "gpt-5.5", out_path=out, reasoning="none")
    assert plan2.calls == 1 and plan2.already_read == 1 and plan2.reasoning == "none"
    assert R.plan_read(rows, "openai", "unknown-model").cost is None


def test_build_engine_sets_the_page_protocol(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    a = R.build_engine("anthropic", "claude-fable-5-1", max_tokens=4000)
    assert a.prompt == R.PAGE_PROMPT and a.effort == "low" and a.temperature is None
    assert a.settings()["reasoning"] == "effort low" and a.max_tokens == 4000
    g = R.build_engine("gemini", "gemini-3.1-pro-preview")
    assert g.thinking_level == "low" and g.temperature == 0.0 and g.reasoning_effort is None
    assert "thinking_level low" in g.settings()["reasoning"]
    o = R.build_engine("openai", "gpt-5.5", reasoning="minimal")
    assert o.reasoning_effort == "minimal" and o.temperature == 0.0
    e = R.build_engine("echo", "stub")
    assert e.version == "stub"
    with pytest.raises(ValueError):
        R.build_engine("kraken", None)
    for eng in (a, g, o):
        eng.close()


def test_fetch_val_pages_is_resumable(tmp_path: Path) -> None:
    urls: list[str] = []

    def fetch(url: str) -> bytes:
        urls.append(url)
        return b"DATA"

    got, present = R.fetch_val_pages(["val/A.jpg", "val/B.jpg"], tmp_path / "val", fetch)
    assert (got, present) == (4, 4)
    assert sorted(p.name for p in (tmp_path / "val").iterdir()) == [
        "A.jpg",
        "A.xml",
        "B.jpg",
        "B.xml",
    ]
    assert urls[0] == R.HF_RESOLVE + "val/A.jpg"
    got2, present2 = R.fetch_val_pages(["val/A.jpg", "val/B.jpg"], tmp_path / "val", fetch)
    assert (got2, present2) == (0, 4) and len(urls) == 4
    assert R.val_files(["val/A.jpg", "val/A.xml", "train/clean/x.jpg"]) == ["val/A.jpg"]
    assert R.slug("gemini-3.1-pro-preview") == "gemini-3.1-pro-preview" and R.slug("a/b") == "a_b"
