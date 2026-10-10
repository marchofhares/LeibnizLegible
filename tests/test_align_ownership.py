"""The GT factory's record ownership, sides and one-piece-per-record (2026-10).

Before: minting a piece cleared every minted line on its pages, so two pieces
sharing a folio erased each other's lines; ``--resume`` skipped a piece when a
neighbour had minted on a shared page; ``Bl. 5v`` took all of folio 5; and a
record citing two volumes was minted once per citation, labelled by whichever
shard wrote last.
"""

from __future__ import annotations

from datetime import date

from leibniz import db
from leibniz.align import factory as F
from leibniz.align.pairs import (
    GtPair,
    ensure_gt_ownership,
    has_record_column,
    insert_gt_pairs,
    record_id_from_source,
    replace_record_pairs,
)
from leibniz.align.volumes import PieceRef, enumerate_pieces

TODAY = date(2026, 10, 10)
FOLIO_TEXT = {
    # folio → (recto lines, verso lines); A's letter ends on 165r, B's starts on 165v
    164: (["prima linea epistolae alpha", "secunda linea alpha"], ["tertia alpha", "quarta alpha"]),
    165: (["quinta alpha finis"], ["incipit beta epistola", "beta secunda linea"]),
    166: (["beta tertia linea", "beta finis vale"], ["nihil hic scriptum"]),
}


def _seed(conn) -> None:
    """One work, folios 164–166, two records: A on Bl. 164–165r, B on Bl. 165v–166r."""
    db.upsert_work(conn, db.Work("W", "LeibnizBriefwechsel"))
    rid = db.start_run(conn, "recognize", model="htr")
    seq = 0
    for folio, sides in FOLIO_TEXT.items():
        for side, texts in zip(("r", "v"), sides, strict=True):
            seq += 1
            db.upsert_page(conn, db.Page(work_id="W", seq=seq, label=f"{folio}{side}"))
            pid = f"W:{seq:04d}"
            for k, t in enumerate(texts):
                db.insert_line(
                    conn,
                    db.Line(
                        page_id=pid, line_seq=k, run_id=rid, status="machine", text=t, conf=0.9
                    ),
                )
    for rec, sig, piece in (("A", "LBr 1 Bl. 164-165r", "10"), ("B", "LBr 1 Bl. 165v-166r", "11")):
        db.upsert_katalog_record(
            conn,
            db.KatalogRecord(
                record_id=rec,
                metadata={"textart": "Abf.; eigh."},
                shelfmark_refs=[sig],
                aa_refs=[{"series": 1, "volume": 6, "piece": piece, "source": "aa_column"}],
            ),
        )
        db.upsert_crosswalk(conn, db.CrosswalkMatch(rec, "W", "gwlb_link", 1.0))
    conn.commit()


TEXTS = {
    "A": "prima linea epistolae alpha secunda linea alpha tertia alpha quarta alpha "
    "quinta alpha finis",
    "B": "incipit beta epistola beta secunda linea beta tertia linea beta finis vale",
}


def _rows(conn) -> list[tuple[str, str, str]]:
    return [
        (r["line_image_ref"], r["record_id"], r["text"])
        for r in conn.execute("SELECT * FROM gt_lines ORDER BY line_image_ref, record_id")
    ]


def test_sides_keep_neighbours_apart_and_both_records_keep_their_lines() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    by_id = {p.record_id: p for p in pieces}
    assert by_id["A"].folio_sides == ("", "r") and by_id["B"].folio_sides == ("v", "r")
    stats = F.run_factory(
        conn, config=F.FactoryConfig(today=TODAY), edition_text_for=F.dict_provider(TEXTS)
    )
    assert stats.pieces_minted == 2
    rows = _rows(conn)
    # A owns 164r–165r (5 lines), B owns 165v–166r (4 lines); 166v is no one's
    assert [r for r in rows if r[1] == "A"] and [r for r in rows if r[1] == "B"]
    assert {r[0] for r in rows if r[1] == "A"} == {
        "W:0001:000",
        "W:0001:001",
        "W:0002:000",
        "W:0002:001",
        "W:0003:000",
    }
    assert {r[0] for r in rows if r[1] == "B"} == {
        "W:0004:000",
        "W:0004:001",
        "W:0005:000",
        "W:0005:001",
    }
    # re-minting A leaves B's rows untouched (the old rule cleared every line on A's pages)
    before_b = [r for r in rows if r[1] == "B"]
    F.mint_piece(conn, by_id["A"], TEXTS["A"], F.FactoryConfig(today=TODAY))
    assert [r for r in _rows(conn) if r[1] == "B"] == before_b


def test_resume_skips_a_record_by_its_own_rows_not_a_neighbours() -> None:
    conn = db.init_db(":memory:")
    _seed(conn)
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    a = next(p for p in pieces if p.record_id == "A")
    F.run_factory(
        conn,
        config=F.FactoryConfig(today=TODAY),
        edition_text_for=F.dict_provider({"A": TEXTS["A"]}),
        pieces=[a],
    )
    stats = F.run_factory(
        conn,
        config=F.FactoryConfig(today=TODAY),
        edition_text_for=F.dict_provider(TEXTS),
        resume=True,
    )
    statuses = {r.piece.record_id: r.status for r in stats.results}
    assert statuses == {"A": "skipped:already_minted", "B": "minted"}


def _pair(ref: str, rid: str, conf: float, text: str) -> GtPair:
    return GtPair(
        ref,
        text,
        f"AA I,6 N.1 (§70-expired AA reading text; katalog {rid})",
        "fair_copy",
        conf,
        "open",
        rid,
    )


def test_a_contested_line_goes_to_the_higher_confidence_whatever_the_order() -> None:
    def final(order: list[str]) -> list[tuple[str, str, str]]:
        conn = db.init_db(":memory:")
        ensure_gt_ownership(conn)
        pairs = {
            "X": [_pair("P:0001:000", "X", 0.8, "x-text"), _pair("P:0001:001", "X", 0.9, "x2")],
            "Y": [_pair("P:0001:000", "Y", 0.95, "y-text")],
            "Z": [_pair("P:0001:001", "Z", 0.9, "z2")],  # a tie with X: the lower id keeps it
        }
        for rid in order:
            replace_record_pairs(conn, rid, pairs[rid])
        return _rows(conn)

    one = final(["X", "Y", "Z"])
    assert one == final(["Z", "Y", "X"]) == final(["Y", "X", "Z"])
    assert one == [("P:0001:000", "Y", "y-text"), ("P:0001:001", "X", "x2")]


def test_ensure_gt_ownership_backfills_an_older_store() -> None:
    conn = db.connect(":memory:")
    conn.executescript(
        "CREATE TABLE gt_lines (id INTEGER PRIMARY KEY, line_image_ref TEXT NOT NULL, "
        "text TEXT NOT NULL, source TEXT NOT NULL, stratum TEXT, align_conf REAL, "
        "license_bucket TEXT NOT NULL)"
    )
    assert not has_record_column(conn)
    insert_gt_pairs(conn, [_pair("P:0001:000", "41800", 0.9, "t")])  # no column yet: still writes
    conn.execute(
        "INSERT INTO gt_lines (line_image_ref, text, source, stratum, align_conf, "
        "license_bucket) VALUES ('B2#xywh=0,0,1,1', 't', 'B2 prototype', 'unknown', 0.9, 'open')"
    )
    assert ensure_gt_ownership(conn) == 1  # the factory row; the prototype row names no record
    assert has_record_column(conn)
    assert ensure_gt_ownership(conn) == 0  # idempotent
    ids = {r["line_image_ref"]: r["record_id"] for r in conn.execute("SELECT * FROM gt_lines")}
    assert ids == {"P:0001:000": "41800", "B2#xywh=0,0,1,1": None}
    names = {r[1] for r in conn.execute("PRAGMA index_list(gt_lines)")}
    assert {"ix_gt_ref", "ix_gt_record"} <= names


def test_record_id_from_source() -> None:
    assert record_id_from_source("AA VI,4 N.109 (§70-expired AA reading text; katalog 41800)") == (
        "41800"
    )
    assert (
        record_id_from_source(
            "AA I,9 N.12 (§70-expired AA reading text; channel gwlb; katalog k-7)"
        )
        == "k-7"
    )
    assert record_id_from_source("B2 prototype") is None


def _piece(series: int, volume: int, piece: str = "1") -> PieceRef:
    return PieceRef("R", series, volume, piece, "W", "LBr 1 Bl. 1", (1, 1), None, None, None)


def test_select_text_pieces_mints_a_record_once_under_the_volume_its_text_came_from() -> None:
    pieces = [_piece(1, 5, "7"), _piece(1, 6, "123"), _piece(1, 7, "4")]
    refs = {
        "R": [
            {"series": 1, "volume": 6, "piece": "123", "channel": "ia"},
            {"series": 1, "volume": 7, "piece": "4", "channel": "gwlb"},
        ]
    }
    (only,) = F.select_text_pieces(pieces, refs)
    assert only.volume_label == "I,6" and only.piece == "123"
    assert only.aa_label == "AA I,6 N.123 + I,7 N.4"
    assert only.channel == "gwlb+ia"
    assert F.source_string(only) == (
        "AA I,6 N.123 + I,7 N.4 (§70-expired AA reading text; channel gwlb+ia; katalog R)"
    )
    # a --volume run that did not enumerate the text's volume leaves the record to that run
    assert F.select_text_pieces([_piece(1, 5, "7")], refs) == []
    # an older cache without refs: the first citation, as before
    assert F.select_text_pieces(pieces, {}) == [pieces[0]]
