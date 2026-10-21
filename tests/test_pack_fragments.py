"""The fragment pack (Phase G1): the selection rules, the §70 refusal, the gold
rules, the box, and ``leibniz pack fragments`` end to end — on the fixture
store's German rows (``conftest.seed_german``) and tests/fixtures/pack/."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import db
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
    pack = _build(german_store_path)  # 0.25 of 5 rows: one gold row, no both-wrong
    gold = [r for r in pack.rows if r["gold"]["is_gold"]]
    assert len(pack.rows) == 5 and len(gold) == 1
    assert "truth_cand_id" in gold[0]["gold"]


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


def test_the_v1_text_is_the_row_latest_lines_shows(german_store_path: Path) -> None:
    row = _rows(_build(german_store_path))[f"{W3}:0002:001"]
    v1 = next(c for c in row["candidates"] if c["source"] == "htr_best")
    assert v1["text"] == "so ich vernommen habe"  # the later run's, not "vernomen"
    assert v1["prior_conf"] == 0.71 == row["machine_conf"]
    assert row["provenance"]["model"] == "leibniz-htr-v2@v2"


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
