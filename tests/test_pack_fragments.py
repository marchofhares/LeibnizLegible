"""The fragment pack (Phase G1): the selection rules, the §70 refusal, the gold
rules, the box, and ``leibniz pack fragments`` end to end — on the fixture
store's German rows (``conftest.seed_german``) and tests/fixtures/pack/. The
gold-first draw (G1b) — the gold among all the eligible lines, the floor under
the shorter reading, the strata's weights, the shuffled order — on synthetic
eligible sets."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
from leibniz.align import audit
from leibniz.align.audit_reach import open_readonly
from leibniz.cli import app
from leibniz.pack import check as C
from leibniz.pack import fragments as F

FIXTURES = Path(__file__).parent / "fixtures" / "pack"
PIECES = FIXTURES / "german_pieces.jsonl"
READINGS = FIXTURES / "trocr-kurrent-xvi-xvii.jsonl"
W3 = "00069377"
W4 = "DE-611-HS-870001"
BEFORE_IV4 = date(2026, 10, 22)  # AA IV,4 (2001) is §70-free from 2027-01-01
AFTER_IV4 = date(2027, 1, 2)
runner = CliRunner()


def _build(store: Path, today: date = BEFORE_IV4, **kw) -> F.Pack:
    conn = open_readonly(store)
    try:
        return F.build_pack(
            conn,
            F.load_pieces(PIECES),
            F.load_readings(READINGS),
            today=today,
            built_at="2026-10-22T08:00:00Z",
            git_sha="0" * 40,
            **kw,
        )
    finally:
        conn.close()


def _rows(pack: F.Pack) -> dict[str, dict]:
    return {r["line_id"]: r for r in pack.rows}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


def test_pieces_carry_the_strict_hand_and_the_volume() -> None:
    a, b = F.load_pieces(PIECES)
    assert (a.record_id, a.volumes, a.stratum, a.language) == (
        "k-4101",
        ((4, "3"),),
        "heavy_revision",
        "de",
    )
    assert a.leibniz_hand  # own hand, no sender: his writing
    assert (b.record_id, b.volumes, b.language, b.leibniz_hand) == (
        "k-4402",
        ((4, "4"),),
        "mixed",
        False,
    )
    # the strict rule: an autograph letter of someone else is not his hand
    row = {"record_id": "1", "hand": "own", "absender": "Schreiber, Johann (GND)"}
    assert not F.piece_from_row(row).leibniz_hand
    assert F.piece_from_row({**row, "absender": "Leibniz (GND)"}).leibniz_hand
    assert not F.piece_from_row({**row, "hand": "partial", "absender": None}).leibniz_hand


def test_a_record_cited_twice_merges(tmp_path: Path) -> None:
    rows = [
        {"record_id": "7", "series": 1, "volume_label": "I,16", "page_ids": ["w:0001"]},
        {"record_id": "7", "series": 1, "volume_label": "I,17", "page_ids": ["w:0002"]},
        {"record_id": "12", "series": 1, "volume_label": "I,3", "page_ids": []},
    ]
    path = tmp_path / "pieces.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    seven, twelve = F.load_pieces(path)  # numeric order: 7 before 12
    assert (seven.record_id, twelve.record_id) == ("7", "12")
    assert seven.page_ids == ("w:0001", "w:0002")
    assert seven.volumes == ((1, "16"), (1, "17"))
    # every citation must be free: I,17 is not until 2027
    from leibniz.align.volumes import expired_volume_index

    assert not F.piece_expired(seven, expired_volume_index(BEFORE_IV4))
    assert F.piece_expired(seven, expired_volume_index(AFTER_IV4))
    assert F.piece_expired(twelve, expired_volume_index(BEFORE_IV4))


def test_readings_load_as_written() -> None:
    readings = F.load_readings(READINGS)
    assert len(readings) == 10
    r = readings[f"{W3}:0001:000"]
    assert (r.text, r.conf, r.model) == (
        "Ich habe Ew. Excellenz Schreiben erhalten",
        0.81,
        "dh-unibe/trocr-kurrent-XVI-XVII",
    )


def test_only_the_readers_rows_with_their_deposits(german_store_path: Path) -> None:
    conn = open_readonly(german_store_path)
    rows = F.load_reader_rows(conn)
    conn.close()
    # the five reader-minted rows; the v1-minted row of W4 is not among them
    assert sorted(rows) == [
        f"{W3}:0001:000",
        f"{W3}:0001:001",
        f"{W3}:0001:003",
        f"{W3}:0002:000",
        f"{W3}:0002:001",
    ]
    assert rows[f"{W3}:0002:000"].deposit == "nc"  # the Potsdam channel
    assert {r.deposit for k, r in rows.items() if k != f"{W3}:0002:000"} == {"open"}
    assert rows[f"{W3}:0001:000"].aa_ref == "AA IV,3 N.41"
    assert rows[f"{W3}:0001:000"].record_id == "k-4101"


# --------------------------------------------------------------------------- #
# The box
# --------------------------------------------------------------------------- #


def test_the_box_is_the_audits_crop() -> None:
    poly = [[100, 160], [1900, 160], [1900, 220], [100, 220]]
    # pad 12 on every side
    assert F.bbox_of(poly, None, width=2000, height=2500) == {"x": 88, "y": 148, "w": 1824, "h": 84}
    # clamped at the page's edges
    edge = [[5, 3], [1995, 3], [1995, 2498], [5, 2498]]
    assert F.bbox_of(edge, None, width=2000, height=2500) == {"x": 0, "y": 0, "w": 2000, "h": 2500}
    # no polygon: a band about the baseline, 4 pads above, 1.5 below (then the pad)
    base = [[100, 200], [1900, 200]]
    assert F.bbox_of(None, base, width=2000, height=2500) == {"x": 88, "y": 140, "w": 1824, "h": 90}
    assert F.bbox_of(None, None, width=2000, height=2500) is None
    assert F.bbox_of([[10, 10]], None, width=2000, height=2500) is None  # one point is no line


# --------------------------------------------------------------------------- #
# Gold
# --------------------------------------------------------------------------- #


def test_the_fold_names_the_truth() -> None:
    v = F.fold_verdict
    assert (
        v("Ich habe schreiben", "Ich habe Schreiben erhalten", "ich habe schreiben, erhalten")
        == "alt"
    )
    assert v("so ich vernommen habe", "so ich vernomen habe", "So ich vernommen habe.") == "v1"
    assert v("die Müntze", "die Münze", "der Müntz-Ordnung") == "both_wrong"
    assert v("Vnd daß", "und daß", "und dass") == "ambiguous"  # u/v, ß: both fold to it
    assert v("a b", "a c", "…") == "unfoldable"


@pytest.mark.parametrize(
    ("n_rows", "n_truth", "n_bad", "rate", "share", "want"),
    [
        (2000, 1000, 300, 0.25, 0.25, (375, 125)),  # the caps bind
        (2000, 100, 300, 0.25, 0.25, (100, 33)),  # the truths run short: both-wrong ≤ 25 %
        (2000, 600, 0, 0.25, 0.25, (500, 0)),  # no both-wrong to give
        (2000, 0, 300, 0.25, 0.25, (0, 0)),  # both-wrong alone is never 25 % of the gold
        (5, 2, 1, 0.25, 0.25, (1, 0)),  # floor(1.25) = 1 gold row
        (5, 2, 1, 1.0, 0.5, (2, 1)),
        (0, 5, 5, 0.25, 0.25, (0, 0)),
        (2000, 1000, 300, 0.25, 0.5, (250, 250)),  # the default share: half and half
        (2000, 100, 300, 0.25, 0.5, (100, 100)),  # as many both-wrong as truths, no more
        (2000, 400, 30, 0.25, 0.5, (400, 30)),  # the both-wrong run short: the truths fill
    ],
)
def test_gold_counts(n_rows, n_truth, n_bad, rate, share, want) -> None:
    t, b = F.gold_counts(n_rows, n_truth, n_bad, rate, share)
    assert (t, b) == want
    assert t + b <= rate * n_rows + 1e-9
    assert b <= share * (t + b) + 1e-9


def test_gold_on_the_fixture(german_store_path: Path) -> None:
    pack = _build(german_store_path, gold_rate=1.0, bad_gold_share=0.5)
    rows = _rows(pack)
    by_cand = {lid: {c["cand_id"]: c["source"] for c in r["candidates"]} for lid, r in rows.items()}
    g0 = rows[f"{W3}:0001:000"]["gold"]  # the Bern reading is the minted text
    assert g0["is_gold"] and by_cand[f"{W3}:0001:000"][g0["truth_cand_id"]] == "model_alt"
    assert g0["source"] == "aa_aligned" and g0["align_conf"] == 0.88
    g1 = rows[f"{W3}:0002:001"]["gold"]  # the later run's v1 reading is
    assert by_cand[f"{W3}:0002:001"][g1["truth_cand_id"]] == "htr_best"
    assert rows[f"{W3}:0001:001"]["gold"] == {
        "is_gold": True,
        "both_wrong": True,
        "source": "aa_aligned",
        "align_conf": 0.74,
    }
    # both readings fold to the minted text: no gold
    assert rows[f"{W3}:0001:003"]["gold"] == {"is_gold": False}
    assert pack.gold.verdicts[f"{W3}:0001:003"] == "ambiguous"
    # gold rows are 'aligned', the others 'machine'
    assert {r["provenance"]["status"] for r in rows.values() if r["gold"]["is_gold"]} == {"aligned"}
    assert rows[f"{W3}:0001:003"]["provenance"]["status"] == "machine"


def test_the_nc_channel_is_never_gold(german_store_path: Path) -> None:
    pack = _build(german_store_path, gold_rate=1.0, bad_gold_share=1.0)
    row = _rows(pack)[f"{W3}:0002:000"]
    # the Bern reading equals the Potsdam row's text, and still: no gold
    assert row["gold"] == {"is_gold": False}
    assert f"{W3}:0002:000" not in pack.gold.verdicts
    assert pack.gold.withheld == 1
    # nor does the NC row lend the line its AA label
    assert "aa_ref" not in row["provenance"]
    assert row["provenance"]["status"] == "machine"


def test_a_v1_minted_row_is_never_gold(german_store_path: Path) -> None:
    pack = _build(german_store_path, today=AFTER_IV4, gold_rate=1.0, bad_gold_share=1.0)
    row = _rows(pack)[f"{W4}:0001:000"]
    assert row["gold"] == {"is_gold": False}
    assert row["provenance"]["katalog_record_id"] == "k-4402"  # the piece's
    assert "aa_ref" not in row["provenance"]


def test_the_default_caps(german_store_path: Path) -> None:
    assert (F.DEFAULT_GOLD_RATE, F.DEFAULT_BAD_GOLD_SHARE) == (0.25, 0.5)
    pack = _build(german_store_path)  # 0.25 of 5 rows: one gold row, no both-wrong
    gold = [r for r in pack.rows if r["gold"]["is_gold"]]
    assert len(pack.rows) == 5 and len(gold) == 1
    assert "truth_cand_id" in gold[0]["gold"]
    # every row gold if it can be: the two truths carry one both-wrong at the default share
    full = _build(german_store_path, gold_rate=1.0)
    assert (len(full.gold.truth), len(full.gold.both_wrong)) == (2, 1)


# --------------------------------------------------------------------------- #
# Rows and the §70 refusal
# --------------------------------------------------------------------------- #


def test_rows_and_skips_on_the_fixture(german_store_path: Path) -> None:
    pack = _build(german_store_path)
    assert sorted(_rows(pack)) == [
        f"{W3}:0001:000",
        f"{W3}:0001:001",
        f"{W3}:0001:003",
        f"{W3}:0002:000",
        f"{W3}:0002:001",
    ]
    assert dict(pack.pool.skipped) == {
        "no_image": 1,  # W3's third page is not cached
        "same_text": 1,  # differs in spaces only
        "too_short": 1,
        "empty_reading": 1,
        "no_reading": 1,
        "too_long": 1,
        "not_70_expired": 1,  # W4: AA IV,4
    }
    assert (pack.pool.pages, pack.pool.pages_found, pack.pool.pages_no_image) == (4, 4, 1)
    assert pack.pool.lines == 12
    row = _rows(pack)[f"{W3}:0001:000"]
    assert row["image"] == {
        "delivery": "static",
        "page_image_url": f"https://images.leibnizlegible.com/{W3}/0001.jpg",
        "bbox": {"x": 0, "y": 148, "w": 1912, "h": 84},  # the polygon starts at x=5
        "canvas_id": f"https://digitale-sammlungen.gwlb.de/content/{W3}/canvas/1",
        "folio_label": "1r",
    }
    assert (row["stratum"], row["lang"], row["machine_conf"], row["n_chars"]) == (
        "heavy_revision",
        "de",
        0.62,
        41,
    )
    assert (row["demand_weight"], row["license_bucket"]) == (1.0, "open")
    prov = row["provenance"]
    assert prov["image_uri"] == (
        f"https://digitale-sammlungen.gwlb.de/content/{W3}/jpgs/default/00000001.jpg"
    )
    assert (prov["model"], prov["model_alt"]) == (
        "FoNDUE-GD_v2_ft_Leibniz@v1",
        "dh-unibe/trocr-kurrent-XVI-XVII",
    )
    assert (prov["shelfmark"], prov["katalog_record_id"], prov["aa_ref"]) == (
        "LH XXIII, 2",
        "k-4101",
        "AA IV,3 N.41",
    )
    assert prov["run_at"]
    assert row["attribution"] == F.attribution_lines()
    # the baseline-only line gets the band about its baseline
    assert _rows(pack)[f"{W3}:0002:000"]["image"]["bbox"] == {
        "x": 88,
        "y": 140,
        "w": 1824,
        "h": 90,
    }


def test_the_floor_under_the_shorter_reading() -> None:
    assert F.DEFAULT_MIN_RATIO == 0.5
    assert F.lopsided("a", "ein langes Stück Text", 0.5)
    assert F.lopsided("vier", "neun Zeichen"[:9], 0.5)  # 4 of 9: under half
    assert not F.lopsided("fünf5", "zehn Zeich", 0.5)  # 5 of 10: half is enough
    assert not F.lopsided("ein langes Stück Text", "ein langes Stück", 0.5)
    assert not F.lopsided("a", "ein langes Stück Text", 0.0)  # no floor
    assert not F.lopsided("abc", "abcdefghij" * 3, 0.1)  # 3 of 30 at 0.1: no rounding slip
    assert "lopsided" in F.SKIP_REASONS
    assert F.SKIP_REASONS.index("lopsided") == F.SKIP_REASONS.index("too_long") + 1


def test_a_lopsided_pair_is_skipped(german_store_path: Path) -> None:
    line = f"{W3}:0001:001"  # v1 "die Sache wegen der Müntze" (26)
    readings = F.load_readings(READINGS)
    readings[line] = F.Reading(text="die Sache", conf=0.2, model=readings[line].model)  # 9
    conn = open_readonly(german_store_path)
    try:
        kw = dict(today=BEFORE_IV4, built_at="2026-10-22T08:00:00Z", git_sha="0" * 40)
        pack = F.build_pack(conn, F.load_pieces(PIECES), readings, **kw)
        loose = F.build_pack(conn, F.load_pieces(PIECES), readings, min_ratio=0.0, **kw)
        strict = F.build_pack(conn, F.load_pieces(PIECES), readings, min_ratio=0.99, **kw)
    finally:
        conn.close()
    assert line not in _rows(pack) and pack.pool.skipped["lopsided"] == 1
    assert len(pack.rows) == 4 and pack.params["min_ratio"] == 0.5
    assert line in _rows(loose) and "lopsided" not in loose.pool.skipped  # the window alone
    # the window's own skips come first: a line is counted under the first rule it fails
    assert strict.pool.skipped["too_short"] == 1 and strict.pool.skipped["too_long"] == 1
    assert strict.pool.skipped["lopsided"] == 5 - len(strict.rows)
    assert any("lopsided" in ln for ln in F.summary_lines(pack))


def test_the_v1_text_is_the_row_latest_lines_shows(german_store_path: Path) -> None:
    row = _rows(_build(german_store_path))[f"{W3}:0002:001"]
    v1 = next(c for c in row["candidates"] if c["source"] == "htr_best")
    assert v1["text"] == "so ich vernommen habe"  # the later run's, not "vernomen"
    assert v1["prior_conf"] == 0.71 == row["machine_conf"]
    assert row["provenance"]["model"] == "leibniz-htr-v2@v2"


def test_the_store_as_an_earlier_run_left_it(german_store_path: Path) -> None:
    line = f"{W3}:0002:001"
    now = _build(german_store_path)
    assert now.params["as_of_run"] is None and line in _rows(now)
    # the later run re-read the line; the store as the run before it left it shows
    # the first reading, which is the Bern model's word for word: no pair
    later = _rows(now)[line]["provenance"]["model"]
    conn = open_readonly(german_store_path)
    (run,) = conn.execute(
        "SELECT run_id FROM lines WHERE line_id = ? AND model = ?", (line, later)
    ).fetchone()
    conn.close()
    then = _build(german_store_path, as_of_run=run - 1)
    assert line not in _rows(then) and then.pool.skipped["same_text"] == 2
    assert {r["provenance"]["model"] for r in then.rows} == {"FoNDUE-GD_v2_ft_Leibniz@v1"}
    assert len(then.rows) == 4 and then.pool.lines == now.pool.lines
    said = "\n".join(F.summary_lines(then))
    assert f"the store as run {run - 1} left it" in said
    assert "the stored reading (htr_best), by model: FoNDUE-GD_v2_ft_Leibniz@v1 4" in said
    said = "\n".join(F.summary_lines(now))
    assert "the reading the site shows of each" in said
    assert "by model: FoNDUE-GD_v2_ft_Leibniz@v1 4 · leibniz-htr-v2@v2 1" in said


def test_only_the_records_listed(german_store_path: Path) -> None:
    whole = _build(german_store_path, today=AFTER_IV4)
    assert len(whole.rows) == 6 and whole.pool.listed is None
    assert whole.params["only_records"] is None
    # the correspondent's letter alone: its page, its line
    one = _build(german_store_path, today=AFTER_IV4, only_records={"k-4402"})
    assert sorted(_rows(one)) == [f"{W4}:0001:000"]
    assert (one.pool.pieces, one.pool.pages, one.pool.lines) == (1, 1, 1)
    assert (one.pool.listed, one.pool.listed_unknown) == (1, 0) and not one.pool.skipped
    assert one.gold.n_gold == 0 and not one.gold.verdicts  # its row was minted from v1
    # the draft alone, with a record the census does not have beside it
    draft = _build(german_store_path, today=AFTER_IV4, only_records=["k-4101", "k-0000"])
    assert sorted(_rows(draft)) == sorted(k for k in _rows(whole) if k.startswith(W3))
    assert (draft.pool.pieces, draft.pool.pages, draft.pool.lines) == (1, 3, 11)
    assert (draft.pool.listed, draft.pool.listed_unknown) == (2, 1)
    assert draft.params["only_records"] == 2
    assert draft.gold.verdicts == {
        k: v for k, v in whole.gold.verdicts.items() if k in _rows(draft)
    }
    said = "\n".join(F.summary_lines(draft))
    assert "Pieces: 1 records on 3 pages" in said
    assert "only the 2 records listed (1 of them not among the German pieces)" in said
    assert "only the" not in "\n".join(F.summary_lines(whole))
    # nothing listed that the census knows: no page is read
    none = _build(german_store_path, today=AFTER_IV4, only_records={"k-0000"})
    assert not none.rows and (none.pool.pieces, none.pool.pages, none.pool.lines) == (0, 0, 0)


def test_a_shared_page_s_lines_stay_with_their_piece(
    german_store_path: Path, tmp_path: Path
) -> None:
    # a second piece on the draft's first page, with the lower record id: the lines a
    # reader-minted row gives to k-4101 stay its own, the other two go to the newcomer
    rows = [json.loads(ln) for ln in PIECES.read_text(encoding="utf-8").splitlines()]
    guest = {**rows[0], "record_id": "k-0001", "page_ids": [f"{W3}:0001"]}
    path = tmp_path / "pieces.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in [*rows, guest]), encoding="utf-8")
    pieces = F.load_pieces(path)
    conn = open_readonly(german_store_path)
    try:
        kw = dict(today=BEFORE_IV4, built_at="2026-10-22T08:00:00Z", git_sha="0" * 40)
        readings = F.load_readings(READINGS)
        mine = F.build_pack(conn, pieces, readings, only_records={"k-4101"}, **kw)
        guests = F.build_pack(conn, pieces, readings, only_records={"k-0001"}, **kw)
        both = F.build_pack(conn, pieces, readings, only_records={"k-0001", "k-4101"}, **kw)
    finally:
        conn.close()
    assert len(mine.rows) == 5 and {r["provenance"]["katalog_record_id"] for r in mine.rows} == {
        "k-4101"
    }
    # the two lines without a minted row are the guest's: not looked at further
    assert mine.pool.skipped["other_record"] == 2
    assert "same_text" not in mine.pool.skipped and "too_short" not in mine.pool.skipped
    # the guest's page alone is read; three of its five lines are k-4101's
    assert (guests.pool.pieces, guests.pool.pages, guests.pool.lines) == (1, 1, 5)
    assert dict(guests.pool.skipped) == {"other_record": 3, "same_text": 1, "too_short": 1}
    assert not guests.rows
    assert "other_record" not in both.pool.skipped and len(both.rows) == 5
    assert F.SKIP_REASONS.index("other_record") == F.SKIP_REASONS.index("twin_elsewhere") + 1
    assert any("another piece's line" in ln for ln in F.summary_lines(mine))


def test_k3_s_validation_pieces_are_a_list_of_records() -> None:
    from leibniz.align.kurrent_mint import read_csv_column

    listed = read_csv_column(
        [Path(__file__).parents[1] / "reports" / "kurrent" / "k3-val-pieces.csv"], ("record_id",)
    )
    assert len(listed) == 98 and all(r.isdigit() for r in listed)  # K3: 98 records, 92 units


def test_the_section_70_refusal(german_store_path: Path) -> None:
    before = _build(german_store_path, today=BEFORE_IV4)
    assert f"{W4}:0001:000" not in _rows(before)
    assert before.pool.skipped["not_70_expired"] == 1
    after = _build(german_store_path, today=AFTER_IV4)
    row = _rows(after)[f"{W4}:0001:000"]
    assert after.pool.skipped["not_70_expired"] == 0
    assert (row["lang"], row["stratum"]) == ("mixed", "light_revision")
    # a static work: the GWLB has no canvas, the site's manifest does
    assert row["image"]["canvas_id"] == f"https://leibnizlegible.com/manifests/{W4}/canvas/1"
    assert row["image"]["folio_label"] == "1"  # no label: the canvas position
    # handed a refused line anyway, the row builder raises
    e = next(e for e in after.selected if e.line_id == f"{W4}:0001:000")
    from leibniz.align.volumes import expired_volume_index
    from leibniz.web.images import ImageSource

    with pytest.raises(F.Refused):
        F.build_row(
            e,
            gold=None,
            seed=0,
            image_source=ImageSource(F.DEFAULT_IMAGE_BASE_URL),
            expired=expired_volume_index(BEFORE_IV4),
            attribution=F.attribution_lines(),
        )


def test_a_scan_registered_twice_gives_each_line_once(german_store_path: Path) -> None:
    # W5's twins: W3's two pages become one upright scan registered under 1r and
    # 1v (file sizes within the tolerance, the lines in the same places) — a
    # fold, whose text the first registration carries, as the index counts it
    conn = db.connect(german_store_path)
    for seq, size in ((1, 1_500_000), (2, 1_500_300)):
        conn.execute("UPDATE pages SET n_bytes = ? WHERE page_id = ?", (size, f"{W3}:{seq:04d}"))
    conn.commit()
    conn.close()
    pack = _build(german_store_path)
    assert sorted(_rows(pack)) == [f"{W3}:0001:000", f"{W3}:0001:001", f"{W3}:0001:003"]
    assert pack.pool.skipped["twin_elsewhere"] == 5  # every line of the second registration
    assert "no_reading" not in pack.pool.skipped  # W3:0002's lines were not looked at


def test_a_crowd_row_takes_the_line_out(german_store_path: Path) -> None:
    conn = db.connect(german_store_path)
    run = db.start_run(conn, "crowd", model="crowd_ab_v1@abc")
    conn.execute(
        "INSERT INTO lines (line_id, page_id, line_seq, text, conf, model, run_id, status) "
        "VALUES (?, ?, 1, 'die Sache wegen der Münze', 0.9, 'crowd_ab_v1@abc', ?, 'corrected')",
        (f"{W3}:0001:001", f"{W3}:0001", run),
    )
    conn.commit()
    conn.close()
    pack = _build(german_store_path)
    assert f"{W3}:0001:001" not in _rows(pack)
    assert pack.pool.skipped["already_corrected"] == 1


def test_the_candidates_order_is_drawn_per_line() -> None:
    firsts = Counter(F.v1_first(f"w:0001:{i:03d}", 7) for i in range(400))
    assert 150 < firsts[True] < 250  # both orders, near half each
    assert all(F.v1_first("w:0001:000", 7) == F.v1_first("w:0001:000", 7) for _ in range(3))
    assert F.cand_id("l", "htr_best", "a") != F.cand_id("l", "model_alt", "a")
    assert F.fragment_id("l", "a", "b") != F.fragment_id("l", "a", "c")


def test_the_pack_is_reproducible(german_store_path: Path) -> None:
    a = _build(german_store_path, seed=3)
    b = _build(german_store_path, seed=3)
    assert a.rows == b.rows and a.header == b.header
    assert a.header["pack_id"].startswith("ll-fragments-2026-10-22-s3-")
    assert [e.line_id for e in a.selected] == [r["line_id"] for r in a.rows]


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #


def _eligible(n_by: dict[tuple[str, bool], int]) -> list[F.Eligible]:
    page = db.Page(work_id="w", seq=1, width=100, height=100, local_path="w/0001.jpg")
    out = []
    i = 0
    for (stratum, own), n in n_by.items():
        piece = F.Piece(
            record_id=f"{stratum}-{own}",
            work_id="w",
            volumes=((4, "3"),),
            aa_label=None,
            stratum=stratum,
            hand="own" if own else "other",
            leibniz_hand=own,
            language="de",
            signature="LH 1",
            page_ids=("w:0001",),
        )
        for _ in range(n):
            out.append(
                F.Eligible(
                    line_id=f"w:0001:{i:05d}",
                    page=page,
                    line_seq=i,
                    v1_text="abcdefghijk",
                    v1_conf=0.5,
                    v1_model="m@1",
                    v1_run_id=1,
                    run_at="2026-01-01T00:00:00Z",
                    alt_text="abcdefghijx",
                    alt_conf=0.5,
                    alt_model="bern",
                    piece=piece,
                    bbox={"x": 0, "y": 0, "w": 10, "h": 10},
                    shelfmark="LH 1",
                )
            )
            i += 1
    return out


def test_selection_is_equal_per_stratum_and_keeps_his_hand() -> None:
    # his lines (6 % overall) all in heavy revision, the biggest stratum
    pool = _eligible(
        {
            ("fair_copy", False): 300,
            ("light_revision", False): 2000,
            ("heavy_revision", False): 3000,
            ("heavy_revision", True): 400,
            ("scrap", False): 900,
        }
    )
    share = 400 / len(pool)
    picked = F.select_lines(pool, limit=400, seed=1)
    assert len(picked) == 400
    by = Counter(e.stratum for e in picked)
    assert by == {"fair_copy": 100, "light_revision": 100, "heavy_revision": 100, "scrap": 100}
    own = sum(e.leibniz_hand for e in picked)
    assert own / len(picked) >= share  # at least his natural share …
    assert own == -(-400 * 400 // len(pool))  # … and here exactly its ceiling
    assert len({e.line_id for e in picked}) == 400
    assert [e.line_id for e in picked] == sorted(e.line_id for e in picked)
    again = F.select_lines(pool, limit=400, seed=1)
    assert [e.line_id for e in again] == [e.line_id for e in picked]
    other = F.select_lines(pool, limit=400, seed=2)
    assert [e.line_id for e in other] != [e.line_id for e in picked]


def test_selection_gives_a_short_stratum_s_remainder_away() -> None:
    pool = _eligible({("fair_copy", False): 10, ("heavy_revision", True): 50, ("scrap", False): 90})
    picked = F.select_lines(pool, limit=90, seed=0)
    by = Counter(e.stratum for e in picked)
    assert by["fair_copy"] == 10 and sum(by.values()) == 90
    assert len(F.select_lines(pool, limit=10_000, seed=0)) == len(pool)  # all, when fewer


def test_leibniz_quotas_meet_the_target_where_room_is() -> None:
    quotas = {"light_revision": 10, "heavy_revision": 10}
    own = {"light_revision": 0, "heavy_revision": 8}
    sizes = {"light_revision": 50, "heavy_revision": 50}
    assert F.leibniz_quotas(quotas, own, sizes, 0) == {"light_revision": 0, "heavy_revision": 2}
    assert F.leibniz_quotas(quotas, own, sizes, 5) == {"light_revision": 0, "heavy_revision": 5}
    assert F.leibniz_quotas(quotas, own, sizes, 20) == {"light_revision": 0, "heavy_revision": 8}


# --------------------------------------------------------------------------- #
# The gold-first draw (G1b), on synthetic eligible sets
# --------------------------------------------------------------------------- #

TRUTH, BAD, SAME, NC = "truth", "bad", "same", "nc"


def _pool(spec: dict[tuple[str, bool], dict[str, int]]) -> list[F.Eligible]:
    """Eligible lines with canonical ids, per ``(stratum, own hand)``: ``n``
    lines, of which the first ``truth`` carry an open reader-minted row equal
    to the Bern reading, the next ``bad`` one equal to neither, the next
    ``same`` one both readings fold to, the next ``nc`` a withheld one."""
    out = []
    i = 0
    for (stratum, own), counts in spec.items():
        piece = F.Piece(
            record_id=f"{stratum}-{own}",
            work_id="w",
            volumes=((4, "3"),),
            aa_label=None,
            stratum=stratum,
            hand="own" if own else "other",
            leibniz_hand=own,
            language="de",
            signature="LH 1",
            page_ids=(),
        )
        kinds = [k for k in (TRUTH, BAD, SAME, NC) for _ in range(counts.get(k, 0))]
        for j in range(counts["n"]):
            seq, line = i // 1000 + 1, i % 1000
            page = db.Page(
                work_id="w",
                seq=seq,
                image_url=f"https://example.org/w/{seq}.jpg",
                width=2000,
                height=2500,
                local_path=f"w/{seq:04d}.jpg",
            )
            line_id = f"w:{seq:04d}:{line:03d}"
            kind = kinds[j] if j < len(kinds) else None
            v1, alt = (
                ("Vnd daß etwas", "und daß etwas")
                if kind == SAME
                else ("abcdefghijk", "abcdefghijx")
            )
            minted = {TRUTH: alt, BAD: "ganz anderer Text", SAME: "und dass etwas"}.get(kind)
            gt = minted and F.GtRow(
                gt_id=i,
                line_id=line_id,
                text=minted,
                source="AA IV,3 N.41 (reader trocr-kurrent-xvi-xvii)",
                align_conf=0.9,
                license_bucket="open",
                record_id=piece.record_id,
                deposit="open",
                aa_ref="AA IV,3 N.41",
            )
            out.append(
                F.Eligible(
                    line_id=line_id,
                    page=page,
                    line_seq=line,
                    v1_text=v1,
                    v1_conf=0.5,
                    v1_model="m@1",
                    v1_run_id=1,
                    run_at="2026-01-01T00:00:00Z",
                    alt_text=alt,
                    alt_conf=0.5,
                    alt_model="bern",
                    piece=piece,
                    bbox={"x": 0, "y": 0, "w": 10, "h": 10},
                    shelfmark="LH 1",
                    gt=gt or None,
                    gt_withheld=kind == NC,
                )
            )
            i += 1
    return out


# the first real pack's shape: gold candidates thin in a pool mostly heavy revision
THIN = {
    ("fair_copy", False): {"n": 50, "truth": 2, "bad": 3},
    ("light_revision", False): {"n": 2000, "truth": 60, "bad": 150, "nc": 200},
    ("heavy_revision", False): {"n": 5000, "truth": 120, "bad": 300, "same": 4, "nc": 400},
    ("heavy_revision", True): {"n": 500, "truth": 10, "bad": 40},
    ("scrap", False): {"n": 450, "truth": 8, "bad": 30},
}


def _kinds(selected: list[F.Eligible], gold: F.GoldPlan) -> Counter:
    return Counter((e.stratum, gold.kind(e.line_id)) for e in selected if gold.kind(e.line_id))


def test_gold_first_reaches_the_cap_where_the_random_draw_did_not() -> None:
    pool = _pool(THIN)  # 8,000 lines; 200 truths and 523 both-wrong among them
    selected, gold = F.draw(pool, limit=400, seed=20261117)
    assert len(selected) == 400 == len({e.line_id for e in selected})
    assert (gold.cap, gold.n_gold) == (100, 100)  # 0.25 × 400, reached
    assert (len(gold.truth), len(gold.both_wrong)) == (50, 50)  # half both-wrong at the most
    assert gold.lines <= {e.line_id for e in selected}  # every gold line is a row
    assert all(gold.kind(k) == "alt" for k in gold.truth)
    assert all(gold.verdicts[k] == "both_wrong" for k in gold.both_wrong)
    assert Counter(gold.verdicts.values()) == {"alt": 200, "both_wrong": 523, "ambiguous": 4}
    assert gold.withheld == 600  # among the eligible
    # G1's draw — the lines first, the gold among them — on the same pool and seed
    blind = F.select_lines(pool, limit=400, seed=20261117)
    found = Counter(gold.verdicts.get(e.line_id) for e in blind)
    assert found["alt"] < 25 and found["alt"] + found["both_wrong"] < 100


def test_the_gold_is_what_the_supply_allows() -> None:
    few = {("heavy_revision", False): {"n": 3000, "truth": 10, "bad": 400}}
    _, gold = F.draw(_pool(few), limit=400, seed=1)
    assert (len(gold.truth), len(gold.both_wrong)) == (10, 10)  # no more both-wrong than truths
    _, gold = F.draw(_pool(few), limit=400, seed=1, bad_share=0.25)
    assert (len(gold.truth), len(gold.both_wrong)) == (10, 3)
    _, gold = F.draw(_pool(few), limit=400, seed=1, bad_share=0.0)
    assert (len(gold.truth), len(gold.both_wrong)) == (10, 0)
    _, gold = F.draw(_pool(few), limit=400, seed=1, gold_rate=0.0)
    assert gold.n_gold == 0 == gold.cap
    # ambiguous and withheld lines are never gold, however much room there is
    none = {("light_revision", False): {"n": 100, "same": 30, "nc": 30}}
    selected, gold = F.draw(_pool(none), limit=100, seed=1, gold_rate=1.0)
    assert len(selected) == 100 and gold.n_gold == 0 and gold.withheld == 30
    # a pool smaller than the limit: the cap is a share of the rows there are
    selected, gold = F.draw(_pool(THIN)[:40], limit=2000, seed=1)
    assert len(selected) == 40 and gold.cap == 10


@pytest.mark.parametrize("share", [0.0, 0.1, 0.25, 0.5, 1.0])
@pytest.mark.parametrize("rate", [0.05, 0.25, 0.6])
def test_the_caps_hold(rate: float, share: float) -> None:
    selected, gold = F.draw(_pool(THIN), limit=600, seed=5, gold_rate=rate, bad_share=share)
    assert len(selected) == 600
    assert gold.n_gold <= rate * 600 + 1e-9
    assert len(gold.both_wrong) <= share * gold.n_gold + 1e-9
    assert not gold.truth & gold.both_wrong


def test_the_gold_is_spread_over_the_strata_and_the_strata_filled_around_it() -> None:
    selected, gold = F.draw(_pool(THIN), limit=400, seed=3)
    rows = Counter(e.stratum for e in selected)
    # the equal allocation, as G1 drew it: fair copy gives all it has, the rest share
    assert rows == {"fair_copy": 50, "light_revision": 117, "heavy_revision": 117, "scrap": 116}
    kinds = _kinds(selected, gold)
    # 50 truths: fair copy has 2 and scrap 8, the other two share the rest
    assert [kinds[s, "alt"] for s in audit.STRATA[:4]] == [2, 20, 20, 8]
    # 50 both-wrong: fair copy has 3, the other three share the rest (16, 16, 15)
    assert [kinds[s, "both_wrong"] for s in audit.STRATA[:4]] == [3, 16, 16, 15]
    # gold where the supply is, and still every stratum at its number
    heavy = {("heavy_revision", False): {"n": 600, "truth": 300, "bad": 300}}
    pool = _pool({**heavy, ("light_revision", False): {"n": 600}, ("scrap", False): {"n": 600}})
    selected, gold = F.draw(pool, limit=600, seed=3)
    assert Counter(e.stratum for e in selected) == dict.fromkeys(
        ("light_revision", "heavy_revision", "scrap"), 200
    )
    assert _kinds(selected, gold) == {
        ("heavy_revision", "alt"): 75,
        ("heavy_revision", "both_wrong"): 75,
    }
    # a stratum whose gold alone is over its share keeps its gold; the others give way
    selected, gold = F.draw(pool, limit=600, seed=3, gold_rate=0.5)
    assert gold.n_gold == 300
    assert Counter(e.stratum for e in selected) == {
        "light_revision": 150,
        "heavy_revision": 300,
        "scrap": 150,
    }


def test_his_hand_keeps_its_share_with_the_gold_counted_in() -> None:
    pool = _pool(THIN)
    n_own = sum(e.leibniz_hand for e in pool)  # 500 of 8,000
    selected, gold = F.draw(pool, limit=400, seed=11)
    own = sum(e.leibniz_hand for e in selected)
    assert own >= -(-n_own * 400 // len(pool)) == 25
    own_gold = sum(e.leibniz_hand for e in selected if gold.kind(e.line_id))
    assert 0 < own_gold < own  # some of his lines are gold, and the fill made up the rest
    # all the gold in his hand: the fill adds none of his beyond the stratum's own share
    his = {
        ("heavy_revision", True): {"n": 100, "truth": 50, "bad": 50},
        ("heavy_revision", False): {"n": 900},
    }
    selected, gold = F.draw(_pool(his), limit=200, seed=11)
    assert gold.n_gold == 50 and sum(e.leibniz_hand for e in selected) >= 50


def test_the_strata_weights() -> None:
    w = F.parse_strata("fair_copy=0.35,light_revision=0.35,heavy_revision=0.2,scrap=0.1")
    assert w == {"fair_copy": 0.35, "light_revision": 0.35, "heavy_revision": 0.2, "scrap": 0.1}
    assert F.parse_strata(" scrap = 1 , heavy_revision=3,") == {"scrap": 1.0, "heavy_revision": 3.0}
    for bad in (
        "fair=1",  # no such stratum
        "fair_copy",  # no weight
        "fair_copy=x",
        "fair_copy=-1",
        "fair_copy=nan",
        "fair_copy=1,fair_copy=2",
        "fair_copy=0,scrap=0",  # nothing to draw
        "",
    ):
        with pytest.raises(ValueError):
            F.parse_strata(bad)
    big = dict.fromkeys(("fair_copy", "light_revision", "heavy_revision", "scrap"), 10_000)
    assert F.allocate(big, 2000, weights=w) == {
        "fair_copy": 700,
        "light_revision": 700,
        "heavy_revision": 400,
        "scrap": 200,
    }
    # relative weights: 7 : 7 : 4 : 2 is the same split
    sevens = F.parse_strata("fair_copy=7,light_revision=7,heavy_revision=4,scrap=2")
    assert F.allocate(big, 2000, weights=sevens) == F.allocate(big, 2000, weights=w)
    # the real pool's shape: fair copy short, its surplus to the others 0.35 : 0.2 : 0.1
    real = {"fair_copy": 55, "light_revision": 18_904, "heavy_revision": 59_345, "scrap": 1_149}
    got = F.allocate(real, 2000, weights=w)
    assert got == {"fair_copy": 55, "light_revision": 1047, "heavy_revision": 599, "scrap": 299}
    assert sum(got.values()) == 2000
    # a stratum the weights leave out gives no row; nor does one named with 0
    assert F.allocate({**big, "unknown": 500}, 2000, weights=w).get("unknown") is None
    assert F.allocate(big, 100, weights={"scrap": 1.0, "fair_copy": 0.0}) == {"scrap": 100}
    # fewer lines than asked: all there are, in the strata drawn
    assert F.allocate({"scrap": 30, "unknown": 50}, 100, weights={"scrap": 1.0}) == {"scrap": 30}
    # the floor: gold already drawn in a stratum stays, the others give way
    # (600 by 0.35 : 0.35 : 0.2 is 233⅓, 233⅓, 133⅓: the spare row to the first)
    assert F.allocate(big, 1000, weights=w, floor={"scrap": 400}) == {
        "fair_copy": 234,
        "light_revision": 233,
        "heavy_revision": 133,
        "scrap": 400,
    }


def test_the_equal_allocation_is_the_audits() -> None:
    real = {"fair_copy": 55, "light_revision": 18_904, "heavy_revision": 59_345, "scrap": 1_149}
    # the first real pack's strata (STATUS.md, the G1 entry)
    assert F.allocate(real, 2000) == {
        "fair_copy": 55,
        "light_revision": 649,
        "heavy_revision": 648,
        "scrap": 648,
    }
    rng = random.Random(17)
    for _ in range(2000):
        avail = {s: rng.choice((0, 1, 2, 7, 40, 300, 5000)) for s in audit.STRATA}
        n = rng.choice((1, 2, 3, 5, 10, 99, 400, 2000, 20_000))
        assert F.allocate(avail, n) == audit.allocate(avail, n), (avail, n)


def test_the_allocation_keeps_its_bounds() -> None:
    rng = random.Random(23)
    for _ in range(2000):
        avail = {s: rng.choice((0, 1, 3, 20, 150, 4000)) for s in audit.STRATA}
        weights = {s: rng.choice((0.0, 0.05, 0.1, 0.35, 1.0, 3.0)) for s in audit.STRATA}
        if not any(weights.values()):
            continue
        floor = {s: rng.randrange(0, avail[s] + 1) // rng.choice((1, 2, 10)) for s in audit.STRATA}
        open_to = [s for s in audit.STRATA if weights[s] > 0 and avail[s]]
        n = sum(floor[s] for s in open_to) + rng.choice((0, 1, 5, 60, 900, 9000))
        got = F.allocate(avail, n, weights=weights, floor=floor)
        assert set(got) <= set(open_to)
        assert sum(got.values()) == min(n, sum(avail[s] for s in open_to))
        assert all(floor[s] <= got.get(s, 0) <= avail[s] for s in open_to)


def test_the_draw_follows_the_weights() -> None:
    w = F.parse_strata("fair_copy=0.35,light_revision=0.35,heavy_revision=0.2,scrap=0.1")
    pool = _pool(THIN)
    selected, gold = F.draw(pool, limit=400, seed=9, weights=w)
    # fair copy has 50 of its 140; the rest by 0.35 : 0.2 : 0.1
    assert Counter(e.stratum for e in selected) == {
        "fair_copy": 50,
        "light_revision": 188,
        "heavy_revision": 108,
        "scrap": 54,
    }
    assert gold.n_gold == 100 and len(gold.both_wrong) == 50
    kinds = _kinds(selected, gold)
    assert [kinds[s, "alt"] for s in audit.STRATA[:4]] == [2, 26, 15, 7]  # the truths by weight too
    # a stratum left out gives no row and no gold, and its lines are not in the supply
    two = F.parse_strata("fair_copy=1,light_revision=1")
    selected, gold = F.draw(pool, limit=400, seed=9, weights=two)
    assert Counter(e.stratum for e in selected) == {"fair_copy": 50, "light_revision": 350}
    assert Counter(gold.verdicts.values()) == {"alt": 62, "both_wrong": 153}
    assert (len(gold.truth), len(gold.both_wrong), gold.withheld) == (50, 50, 200)


def test_the_draw_is_the_seeds() -> None:
    pool = _pool(THIN)
    a, gold_a = F.draw(pool, limit=400, seed=4)
    b, gold_b = F.draw(list(reversed(pool)), limit=400, seed=4)  # whatever order they come in
    assert [e.line_id for e in a] == [e.line_id for e in b]
    assert (gold_a.truth, gold_a.both_wrong) == (gold_b.truth, gold_b.both_wrong)
    c, gold_c = F.draw(pool, limit=400, seed=5)
    assert {e.line_id for e in c} != {e.line_id for e in a} and gold_c.lines != gold_a.lines
    # shuffled: not the line order, and the gold neither at the head nor in a run
    ids = [e.line_id for e in a]
    assert ids != sorted(ids)
    is_gold = [e.line_id in gold_a.lines for e in a]
    assert 10 < sum(is_gold[:200]) < 90  # 100 gold rows in 400: about half in each half
    assert not all(is_gold[:20]) and any(is_gold[:100])
    # without gold, the lines are the ones G1's draw picked for the seed
    plain, none = F.draw(pool, limit=400, seed=4, gold_rate=0.0)
    assert none.n_gold == 0
    assert sorted(e.line_id for e in plain) == [
        e.line_id for e in F.select_lines(pool, limit=400, seed=4)
    ]


def test_a_drawn_pack_checks(tmp_path: Path) -> None:
    from leibniz.web.images import ImageSource

    pool = _pool(THIN)
    kw = dict(limit=400, seed=20261117, gold_rate=0.25, bad_share=0.5)
    w = F.parse_strata("fair_copy=0.35,light_revision=0.35,heavy_revision=0.2,scrap=0.1")
    for name, weights in (("equal", None), ("weighted", w)):
        selected, gold = F.draw(pool, weights=weights, **kw)
        rows = F.build_rows(
            selected,
            gold,
            seed=kw["seed"],
            today=BEFORE_IV4,
            image_source=ImageSource(F.DEFAULT_IMAGE_BASE_URL),
        )
        header = F.pack_header(
            rows,
            today=BEFORE_IV4,
            seed=kw["seed"],
            run_ids={1, 609},
            built_at="2026-11-17T08:00:00Z",
            git_sha="0" * 40,
        )
        pack = F.Pack(
            header=header,
            rows=rows,
            pool=F.Pool(eligible=pool),
            selected=selected,
            gold=gold,
            params={},
        )
        out = F.write_pack(tmp_path / f"{name}.jsonl", pack)
        report = C.check_fragment_pack(out)
        assert report.ok, report.errors[:5]
        assert len(report.rows) == 400
        assert (report.counts["gold"], report.counts["gold truth"]) == (100, 50)
        assert report.counts["gold both_wrong"] == 50
        assert {r["line_id"] for r in rows if r["gold"]["is_gold"]} == gold.lines
        by = {r["line_id"]: r for r in rows}
        for k in gold.truth:  # the truth is the Bern reading's candidate
            truth = by[k]["gold"]["truth_cand_id"]
            src = {c["cand_id"]: c["source"] for c in by[k]["candidates"]}
            assert src[truth] == "model_alt" and by[k]["provenance"]["status"] == "aligned"
        assert all(by[k]["gold"].get("both_wrong") is True for k in gold.both_wrong)
        # nothing but the gold object tells a gold row from another
        plain = [r for r in rows if not r["gold"]["is_gold"]]
        assert {tuple(r) for r in rows} == {tuple(r) for r in plain}
        assert [r["line_id"] for r in rows] != sorted(r["line_id"] for r in rows)


def test_length_bins() -> None:
    assert F.length_bins([10, 19, 20, 49, 50], 10, 50) == [
        ("10–19", 2),
        ("20–29", 1),
        ("30–39", 0),
        ("40–50", 2),
    ]
    assert F.length_bins([12, 47], 12, 47) == [
        ("12–19", 1),
        ("20–29", 0),
        ("30–39", 0),
        ("40–47", 1),
    ]


# --------------------------------------------------------------------------- #
# The command
# --------------------------------------------------------------------------- #


def test_the_command_writes_a_pack_that_checks(german_store_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "packs" / "fragments.jsonl"
    before = _sha(german_store_path)
    res = runner.invoke(
        app,
        [
            "pack",
            "fragments",
            "--db",
            str(german_store_path),
            "--readings",
            str(READINGS),
            "--pieces",
            str(PIECES),
            "--today",
            "2026-10-22",
            "--seed",
            "20261022",
            "--out",
            str(out),
        ],
    )
    assert res.exit_code == 0, res.output
    for want in (
        "Eligible: 5 lines",
        "not_70_expired",
        "refused: not §70-free on 2026-10-22",
        "lopsided                   0 (the shorter reading under 0.5 of the longer)",
        "the longer of the two: 10–19 0 · 20–29 3 · 30–39 0 · 40–50 2",
        "Gold: 1 of 5 rows",
        "Leibniz's own hand (strict rule): pool 5 (100.0 %) → pack 5 (100.0 %)",
        "withheld: 1",
        "the store was opened read-only",
    ):
        assert want in res.output, want
    assert _sha(german_store_path) == before  # read-only: not a byte changed
    lines = out.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["kind"] == "fragment_pack_header"
    assert len(lines) == 6
    assert not (out.parent / "fragments.jsonl.part").exists()
    res = runner.invoke(app, ["pack", "check", str(out)])
    assert res.exit_code == 0, res.output
    assert "OK — fragment pack, schema_version 1" in res.output
    report = C.check_fragment_pack(out)
    assert report.ok and report.counts["gold"] == 1


def test_the_command_takes_the_floor_and_the_weights(
    german_store_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "fragments.jsonl"
    base = [
        "pack",
        "fragments",
        "--db",
        str(german_store_path),
        "--readings",
        str(READINGS),
        "--pieces",
        str(PIECES),
        "--today",
        "2027-01-02",  # W4's light-revision line is free
        "--out",
        str(out),
    ]
    res = runner.invoke(
        app, [*base, "--strata", "light_revision=3,heavy_revision=1", "--limit", "4"]
    )
    assert res.exit_code == 0, res.output
    for want in (
        "strata by weight: light_revision 0.75 · heavy_revision 0.25",
        "the gold drawn first",
        "Gold supply, among the eligible lines of the strata drawn: 4",
        "Gold: 1 of 4 rows",
        "cap 0.5 of the gold",
    ):
        assert want in res.output, want
    report = C.check_fragment_pack(out)
    # the one light-revision line, and three of heavy revision's five in its place
    assert report.ok and report.counts["stratum light_revision"] == 1
    assert report.counts["stratum heavy_revision"] == 3
    res = runner.invoke(app, [*base, "--strata", "scrap=1"])  # no such lines: an empty pack
    assert res.exit_code == 0 and "Selected: 0" in res.output
    res = runner.invoke(app, [*base, "--min-ratio", "0.99"])
    assert res.exit_code == 0 and "lopsided" in res.output
    listed = tmp_path / "val-pieces.csv"
    listed.write_text('unit,record_id,volume\nk-4402,k-4402,"IV,4"\n', encoding="utf-8")
    res = runner.invoke(app, [*base, "--only-records", str(listed)])
    assert res.exit_code == 0, res.output
    assert (
        "Pieces: 1 records on 1 pages" in res.output and "only the 1 records listed" in res.output
    )
    report = C.check_fragment_pack(out)
    assert report.ok and [r["line_id"] for r in report.rows] == [f"{W4}:0001:000"]
    nobody = tmp_path / "nobody.csv"
    nobody.write_text("record_id\n999\n", encoding="utf-8")
    no_column = tmp_path / "no-column.csv"
    no_column.write_text("unit,volume\n1,2\n", encoding="utf-8")
    empty = tmp_path / "empty.csv"
    empty.write_text("record_id\n", encoding="utf-8")
    for bad in (nobody, no_column, empty, tmp_path / "missing.csv"):
        res = runner.invoke(app, [*base, "--only-records", str(bad)])
        assert res.exit_code != 0, bad
    res = runner.invoke(app, [*base, "--as-of-run", "1"])  # before any German line was read
    assert res.exit_code == 0 and "the store as run 1 left it" in res.output
    assert "Eligible: 0 lines" in res.output
    for bad in (["--strata", "fair=1"], ["--strata", "scrap=0"], ["--min-ratio", "1.5"]):
        res = runner.invoke(app, [*base, *bad])
        assert res.exit_code != 0, bad


def test_the_command_refuses_missing_inputs(german_store_path: Path, tmp_path: Path) -> None:
    res = runner.invoke(
        app,
        ["pack", "fragments", "--db", str(german_store_path), "--readings", str(tmp_path / "x")],
    )
    assert res.exit_code != 0
    res = runner.invoke(
        app,
        [
            "pack",
            "fragments",
            "--db",
            str(german_store_path),
            "--readings",
            str(READINGS),
            "--pieces",
            str(PIECES),
            "--today",
            "22.10.2026",
        ],
    )
    assert res.exit_code != 0


def test_the_site_url_is_the_apis() -> None:
    from leibniz.web.api import SITE_URL

    assert F.SITE_URL == SITE_URL
