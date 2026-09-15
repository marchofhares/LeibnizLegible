"""Tests for the GT factory orchestrator (offline; dict-backed edition text)."""

from __future__ import annotations

from datetime import date

from leibniz import db
from leibniz.align import factory as F
from leibniz.align.pairs import count_gt_lines
from leibniz.align.volumes import enumerate_pieces

TODAY = date(2026, 7, 29)
LINE_TEXTS = ["prima linea textus latini", "secunda pars sententiae", "tertia et ultima pars"]


def _seed_piece(
    conn,
    *,
    record_id: str = "REC1",
    textart: str = "Reinschrift",
    cv: float = 0.1,
    overlaps: int = 0,
    short: int = 0,
    recognized: bool = True,
    folios=(164, 165),
    linked: bool = True,
) -> None:
    """Seed one localizable piece: work + folios + recognised lines + katalog + link."""
    db.upsert_work(conn, db.Work("W", "LeibnizHandschriften"))
    labels = ["163r", "163v", "164r", "164v", "165r", "165v"]
    for i, lab in enumerate(labels, start=1):
        db.upsert_page(conn, db.Page(work_id="W", seq=i, label=lab, status="recognized"))
    rid = db.start_run(conn, "segment", model="seg")
    for seq in (3, 4, 5, 6):  # folios 164, 165
        pid = f"W:{seq:04d}"
        for k, t in enumerate(LINE_TEXTS):
            db.insert_line(conn, db.Line(page_id=pid, line_seq=k, run_id=rid, status="machine"))
            if recognized:
                db.set_line_recognition(conn, pid, k, text=t, conf=0.9, model="htr", run_id=rid)
        db.upsert_page_stats(
            conn,
            db.PageStats(
                page_id=pid,
                n_lines=3,
                line_height_cv=cv,
                n_overlaps=overlaps,
                n_short_lines=short,
                run_id=rid,
            ),
        )
    sig = f"LH 4, 6, 18 Bl. {folios[0]}-{folios[1]}"
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id=record_id,
            metadata={"textart": textart},
            shelfmark_refs=[sig],
            aa_refs=[{"series": 6, "volume": 4, "piece": "109"}],
        ),
    )
    if linked:
        db.upsert_crosswalk(conn, db.CrosswalkMatch(record_id, "W", "gwlb_link", 1.0))
    conn.commit()


def _edition() -> str:
    return " ".join(LINE_TEXTS * 4)


def test_mint_piece_happy_path() -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn)
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    cfg = F.FactoryConfig(today=TODAY)
    result = F.mint_piece(conn, pieces[0], _edition(), cfg)
    assert result.minted
    assert result.stratum == "fair_copy"
    assert result.n_htr_lines == 12
    assert result.n_minted == 12
    assert count_gt_lines(conn, license_bucket="open") == 12


def test_run_factory_aggregates_and_records_run() -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)
    stats = F.run_factory(conn, config=cfg, edition_text_for=F.dict_provider({"REC1": _edition()}))
    assert stats.pieces_seen == 1 and stats.pieces_minted == 1
    assert stats.lines_minted == 12
    assert stats.by_volume == {"VI,4": 12}
    assert stats.by_series == {"VI": 12}
    assert stats.by_stratum == {"fair_copy": 12}
    row = conn.execute("SELECT stage, n_ok FROM runs WHERE run_id = ?", (stats.run_id,)).fetchone()
    assert row["stage"] == "gt_factory" and row["n_ok"] == 1


def test_draft_gets_higher_threshold() -> None:
    conn = db.init_db(":memory:")
    # heavy-revision layout + Konzept type → draft stratum → higher threshold
    _seed_piece(conn, textart="Konzept", cv=0.5, overlaps=6, short=2)
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    cfg = F.FactoryConfig(today=TODAY)
    result = F.mint_piece(conn, pieces[0], _edition(), cfg, insert=False)
    assert result.stratum == "heavy_revision"
    assert result.threshold == cfg.stratum_thresholds["heavy_revision"]
    assert result.threshold > cfg.stratum_thresholds["fair_copy"]


def test_skip_reasons() -> None:
    from leibniz.align.volumes import PieceRef

    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)
    # not localizable: a piece with no folio range
    p_noloc = PieceRef("R", 6, 4, "1", "W", "LH 4,6,18", None, "Reinschrift", "gwlb_link", 1.0)
    assert F.mint_piece(conn, p_noloc, _edition(), cfg).status == "skipped:not_localizable"
    # no edition text
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    assert F.mint_piece(conn, pieces[0], "", cfg).status == "skipped:no_edition_text"


def test_no_htr_lines_skipped() -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn, recognized=False)  # segmented but not recognised
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    cfg = F.FactoryConfig(today=TODAY)
    assert F.mint_piece(conn, pieces[0], _edition(), cfg).status == "skipped:no_htr_lines"


def test_remint_is_idempotent() -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)
    prov = F.dict_provider({"REC1": _edition()})
    F.run_factory(conn, config=cfg, edition_text_for=prov)
    first = count_gt_lines(conn)
    F.run_factory(conn, config=cfg, edition_text_for=prov)  # re-run
    assert count_gt_lines(conn) == first  # not doubled


def test_nc_bucket_never_open() -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn)
    pieces, _ = enumerate_pieces(conn, today=TODAY)
    cfg = F.FactoryConfig(today=TODAY, license_bucket="nc")
    F.mint_piece(conn, pieces[0], _edition(), cfg)
    assert count_gt_lines(conn, license_bucket="open") == 0
    assert count_gt_lines(conn, license_bucket="nc") == 12


def test_shard_pieces_is_a_disjoint_cover() -> None:
    from leibniz.align.volumes import PieceRef

    pieces = [PieceRef(str(i), 1, 1, str(i), None, None, None, None, None, None) for i in range(10)]
    shards = [F.shard_pieces(pieces, (i, 3)) for i in range(3)]
    assert sorted(p.record_id for s in shards for p in s) == sorted(p.record_id for p in pieces)
    assert len(shards[0]) == 4 and len(shards[1]) == 3 and len(shards[2]) == 3
    assert F.shard_pieces(pieces, None) is pieces


def test_resume_skips_already_minted_piece() -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)
    prov = F.dict_provider({"REC1": _edition()})
    first = F.run_factory(conn, config=cfg, edition_text_for=prov)
    assert first.lines_minted == 12
    again = F.run_factory(conn, config=cfg, edition_text_for=prov, resume=True)
    assert again.lines_minted == 0 and again.skips == {"already_minted": 1}
    assert count_gt_lines(conn) == 12


def test_piece_error_is_recorded_and_run_continues(monkeypatch) -> None:
    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)

    def boom(*_a, **_kw):
        raise MemoryError("simulated aligner blow-up")

    monkeypatch.setattr(F, "align_piece", boom)
    stats = F.run_factory(conn, config=cfg, edition_text_for=F.dict_provider({"REC1": _edition()}))
    assert stats.pieces_seen == 1 and stats.pieces_minted == 0
    assert stats.skips == {"error:MemoryError": 1}
    assert stats.results[0].status == "skipped:error:MemoryError"
    assert count_gt_lines(conn) == 0
    row = conn.execute("SELECT n_failed FROM runs WHERE run_id = ?", (stats.run_id,)).fetchone()
    assert row["n_failed"] == 1


def test_write_pairs_retries_a_lock_collision(monkeypatch) -> None:
    import sqlite3

    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)
    calls = {"n": 0}
    real_delete = F.delete_gt_for_refs

    def flaky_delete(c, refs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise sqlite3.OperationalError("database is locked")
        return real_delete(c, refs)

    monkeypatch.setattr(F, "delete_gt_for_refs", flaky_delete)
    monkeypatch.setattr(F.time, "sleep", lambda _s: None)
    stats = F.run_factory(conn, config=cfg, edition_text_for=F.dict_provider({"REC1": _edition()}))
    assert calls["n"] == 2
    assert stats.pieces_minted == 1 and stats.lines_minted == 12
    assert count_gt_lines(conn) == 12
    assert not conn.in_transaction  # the failed attempt was rolled back cleanly


def test_write_pairs_gives_up_after_retries(monkeypatch) -> None:
    import sqlite3

    conn = db.init_db(":memory:")
    _seed_piece(conn)
    cfg = F.FactoryConfig(today=TODAY)

    def always_locked(c, refs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(F, "delete_gt_for_refs", always_locked)
    monkeypatch.setattr(F.time, "sleep", lambda _s: None)
    stats = F.run_factory(conn, config=cfg, edition_text_for=F.dict_provider({"REC1": _edition()}))
    assert stats.skips == {"error:OperationalError": 1}
    assert count_gt_lines(conn) == 0
    assert not conn.in_transaction
