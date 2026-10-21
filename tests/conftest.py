"""Shared fixtures: a small, realistic seeded store for the D-phase tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from leibniz import db
from leibniz.images.fetch import cache_relpath

W1 = "00068642"  # IIIF-served Handschriften work
W2 = "DE-611-HS-854976"  # static-JPEG Briefwechsel work
W3 = "00069377"  # German Handschriften work (Phase G1: the fragment pack)
W4 = "DE-611-HS-870001"  # German letter, static (no GWLB canvas)
PACK_FIXTURES = Path(__file__).parent / "fixtures" / "pack"
K2_READER_SOURCE = (
    "AA IV,3 N.41 (§70-expired AA reading text; channel {channel}; reader "
    "trocr-kurrent-xvi-xvii; katalog k-4101)"
)


def seed_store(path: Path | str) -> None:
    """Populate a store with two works, four pages, lines, runs, katalog + GT."""
    conn = db.init_db(path)
    db.upsert_work(
        conn,
        db.Work(
            W1,
            "LeibnizHandschriften",
            title="LH 4,6,18",
            shelfmarks=["LH IV, 6, 18"],
            manifest_url=f"https://digitale-sammlungen.gwlb.de/content/{W1}/manifest.json",
            n_canvases=3,
        ),
    )
    db.upsert_work(
        conn,
        db.Work(W2, "LeibnizBriefwechsel", title="LBr. 464", shelfmarks=["LBr. 464"], n_canvases=1),
    )
    svc = f"https://digitale-sammlungen.gwlb.de/iiif/{W1}/ptif/{{seq}}.ptif"
    for seq, label, status in (
        (1, "1r", "recognized"),
        (2, "1v", "recognized"),
        (3, "2r", "skipped"),
    ):
        db.upsert_page(
            conn,
            db.Page(
                work_id=W1,
                seq=seq,
                canvas_id=f"https://digitale-sammlungen.gwlb.de/content/{W1}/canvas/{seq}",
                image_service_url=svc.format(seq=seq),
                image_url=f"https://digitale-sammlungen.gwlb.de/content/{W1}/jpgs/default/{seq:08d}.jpg",
                thumb_url=f"https://digitale-sammlungen.gwlb.de/content/{W1}/jpgs/thumbs/{seq:08d}.jpg",
                delivery="iiif",
                label=label,
                width=2000,
                height=2500,
                status=status,
                skip_reason="no_lines" if status == "skipped" else None,
            ),
        )
    db.upsert_page(
        conn,
        db.Page(
            work_id=W2,
            seq=1,
            image_url=f"https://digitale-sammlungen.gwlb.de/content/{W2}/jpgs/default/00000001.jpg",
            thumb_url=f"https://digitale-sammlungen.gwlb.de/content/{W2}/jpgs/thumbs/00000001.jpg",
            delivery="static",
            width=1800,
            height=2400,
            status="recognized",
        ),
    )
    seg = db.start_run(conn, "segment", model="blla_ft_leibniz_v1")
    rec = db.start_run(conn, "recognize", model="FoNDUE-GD_v2_ft_Leibniz@v1", git_sha="abc123")
    rec2 = db.start_run(conn, "recognize", model="leibniz-htr-v2@v2", git_sha="def456")
    db.finish_run(conn, rec, n_input=3, n_ok=3, n_failed=0)
    db.finish_run(conn, rec2, n_input=1, n_ok=1, n_failed=0)

    def line(
        pid: str, seq: int, text: str, conf: float, lang: str | None, run: int, y: int
    ) -> None:
        db.insert_line(
            conn,
            db.Line(
                page_id=pid,
                line_seq=seq,
                baseline=[[100, y], [1900, y]],
                polygon=[[100, y - 40], [1900, y - 40], [1900, y + 20], [100, y + 20]],
                run_id=seg,
                status="machine",
            ),
        )
        db.set_line_recognition(conn, pid, seq, text=text, conf=conf, model="htr@v1", run_id=run)
        if lang:
            conn.execute(
                "UPDATE lines SET lang = ? WHERE page_id = ? AND line_seq = ? AND run_id = ?",
                (lang, pid, seq, run),
            )

    p1, p2, q1 = f"{W1}:0001", f"{W1}:0002", f"{W2}:0001"
    line(p1, 0, "Calculemus, inquit Leibnitius", 0.91, "la", rec, 200)
    line(p1, 1, "de arte combinatoria <b>", 0.72, "la", rec, 320)
    line(p1, 2, "quae praecesserunt", 0.55, None, rec, 440)
    # a later run re-read line 0 of page 1: the viewer/index must show this one
    conn.execute(
        "INSERT INTO lines (line_id, page_id, line_seq, baseline, polygon, text, conf, model, "
        "run_id, status, lang) VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, 'machine', 'la')",
        (
            db.line_id(p1, 0),
            p1,
            "[[100, 200], [1900, 200]]",
            "[[100, 160], [1900, 160], [1900, 220], [100, 220]]",
            "Calculemus inquit Leibnitius.",
            0.95,
            "leibniz-htr-v2@v2",
            rec2,
        ),
    )
    line(p2, 0, "vt sit veritas in rebus", 0.88, "la", rec, 200)
    line(p2, 1, "Jeſus Christus", 0.81, "la", rec, 320)
    line(q1, 0, "La Monadologie et les principes", 0.9, "fr", rec, 200)
    line(q1, 1, "de la nature et de la grâce", 0.86, "fr", rec, 320)
    db.upsert_page_stats(conn, db.PageStats(page_id=p1, n_lines=3, run_id=seg))
    db.upsert_page_stats(conn, db.PageStats(page_id=p2, n_lines=2, run_id=seg))
    db.set_page_stratum(conn, p2, "fair_copy")
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="k-109",
            metadata={
                "title": "Praefatio operis ad instaurationem scientiarum",
                "incipit": "Mihi si dicendum",
                "datum": "1679",
                "gwlb_ids": [W1],
            },
            shelfmark_refs=["LH IV, 6, 18 Bl. 1-2"],
            aa_refs=[{"series": 6, "volume": "4", "piece": "109"}],
        ),
    )
    db.upsert_crosswalk(conn, db.CrosswalkMatch("k-109", W1, "gwlb_link", 1.0))
    conn.executemany(
        "INSERT INTO gt_lines (line_image_ref, text, source, stratum, align_conf, license_bucket) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                f"{p1}#xywh=100,160,1800,60",
                "Calculemus, inquit Leibnitius",
                "AA VI,4 N.109",
                "fair_copy",
                0.93,
                "open",
            ),
            (
                f"{p2}#xywh=100,160,1800,60",
                "ut sit veritas in rebus",
                "AA VI,4 N.109",
                "fair_copy",
                0.9,
                "open",
            ),
            (
                f"{q1}#xywh=100,160,1800,60",
                "La Monadologie",
                "transkriptionspool",
                "fair_copy",
                0.8,
                "nc",
            ),
        ],
    )
    conn.commit()
    conn.close()


def seed_german(path: Path | str) -> None:
    """German rows on top of :func:`seed_store` (Phase G1): the fragment pack's
    inputs beside ``tests/fixtures/pack/`` (two pieces, ten Bern readings).

    W3 (piece k-4101, AA IV,3, Leibniz's own draft, heavy revision) has two
    cached pages and one not cached; W4 (piece k-4402, AA IV,4 — not §70-free
    until 2027-01-01 — a correspondent's letter, light revision) one cached
    static page without a GWLB canvas. The lines carry lang 'de'; one was
    re-read by a later run. ``gt_lines`` gains K2's reader-minted rows — a
    truth on each reading, a both-wrong, one both readings fold to, one in
    the Potsdam (NC) channel — and one row minted from the v1 text.
    """
    conn = db.connect(path)
    db.upsert_work(
        conn,
        db.Work(
            W3,
            "LeibnizHandschriften",
            title="LH XXIII, 2",
            shelfmarks=["LH XXIII, 2"],
            manifest_url=f"https://digitale-sammlungen.gwlb.de/content/{W3}/manifest.json",
            n_canvases=3,
        ),
    )
    db.upsert_work(
        conn, db.Work(W4, "LeibnizBriefwechsel", title="LBr. 870", shelfmarks=["LBr. 870"])
    )
    for seq, label, cached in ((1, "1r", True), (2, "1v", True), (3, "2r", False)):
        db.upsert_page(
            conn,
            db.Page(
                work_id=W3,
                seq=seq,
                canvas_id=f"https://digitale-sammlungen.gwlb.de/content/{W3}/canvas/{seq}",
                image_service_url=f"https://digitale-sammlungen.gwlb.de/iiif/{W3}/ptif/{seq}.ptif",
                image_url=f"https://digitale-sammlungen.gwlb.de/content/{W3}/jpgs/default/{seq:08d}.jpg",
                delivery="iiif",
                label=label,
                width=2000,
                height=2500,
                status="recognized",
                local_path=cache_relpath(W3, seq) if cached else None,
                sha256="0" * 64 if cached else None,
            ),
        )
    db.upsert_page(
        conn,
        db.Page(
            work_id=W4,
            seq=1,
            image_url=f"https://digitale-sammlungen.gwlb.de/content/{W4}/jpgs/default/00000001.jpg",
            delivery="static",
            width=1800,
            height=2400,
            status="recognized",
            local_path=cache_relpath(W4, 1),
            sha256="1" * 64,
        ),
    )
    seg = db.start_run(conn, "segment", model="blla_ft_leibniz_v1")
    rec = db.start_run(conn, "recognize", model="FoNDUE-GD_v2_ft_Leibniz@v1", git_sha="abc123")
    rec2 = db.start_run(conn, "recognize", model="leibniz-htr-v2@v2", git_sha="def456")
    mint = db.start_run(conn, "gt_factory", model="retro-aligner+trocr-kurrent-xvi-xvii")
    for run in (rec, rec2, mint):
        db.finish_run(conn, run, n_input=1, n_ok=1, n_failed=0)

    def line(
        pid: str, seq: int, text: str, conf: float, y: int, *, x0: int = 100, poly: bool = True
    ) -> None:
        polygon = [[x0, y - 40], [1900, y - 40], [1900, y + 20], [x0, y + 20]]
        db.insert_line(
            conn,
            db.Line(
                page_id=pid,
                line_seq=seq,
                baseline=[[x0, y], [1900, y]],
                polygon=polygon if poly else None,
                run_id=seg,
                status="machine",
            ),
        )
        db.set_line_recognition(
            conn, pid, seq, text=text, conf=conf, model="FoNDUE-GD_v2_ft_Leibniz@v1", run_id=rec
        )
        conn.execute("UPDATE lines SET lang = 'de' WHERE page_id = ? AND line_seq = ?", (pid, seq))

    p1, p2, p3, q1 = f"{W3}:0001", f"{W3}:0002", f"{W3}:0003", f"{W4}:0001"
    line(p1, 0, "Ich habe Ew. Excellenz schreiben", 0.62, 200, x0=5)  # the box clamps at 0
    line(p1, 1, "die Sache wegen der Müntze", 0.55, 320)
    line(p1, 2, "und  so weiter  fort", 0.70, 440)  # the reading differs in spaces only
    line(p1, 3, "Vnd daß solches geschehen", 0.58, 560)
    line(p1, 4, "ja", 0.40, 680)  # too short
    line(p2, 0, "Seiner Churfürstl. Durchl. zu Braunschweig", 0.66, 200, poly=False)  # baseline
    line(p2, 1, "so ich vernomen habe", 0.50, 320)
    line(p2, 2, "Datum Hannover den 3. Martii 1680", 0.80, 440)  # the reading is empty
    line(p2, 3, "Ewer Excellenz gehorsamster Diener", 0.77, 560)  # no reading
    line(p2, 4, "und weil nun die gantze Sache auff der Cammer beruhet so ist es", 0.52, 680)
    line(p3, 0, "Leibniz", 0.90, 200)  # its page is not cached
    line(q1, 0, "Mein Herr, ich habe dero Schreiben", 0.61, 200)
    # a later run re-read line 1 of page 2: the pack takes this row (latest_lines)
    conn.execute(
        "INSERT INTO lines (line_id, page_id, line_seq, baseline, polygon, text, conf, model, "
        "run_id, status, lang) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, 'machine', 'de')",
        (
            db.line_id(p2, 1),
            p2,
            "[[100, 320], [1900, 320]]",
            "[[100, 280], [1900, 280], [1900, 340], [100, 340]]",
            "so ich vernommen habe",
            0.71,
            "leibniz-htr-v2@v2",
            rec2,
        ),
    )
    open_ia = K2_READER_SOURCE.format(channel="ia")
    conn.executemany(
        "INSERT INTO gt_lines (line_image_ref, text, source, stratum, align_conf, "
        "license_bucket, record_id) VALUES (?, ?, ?, ?, ?, 'open', ?)",
        [
            # the Bern reading is the truth under the fold
            (
                db.line_id(p1, 0),
                "Ich habe Ew. Excellenz Schreiben erhalten",
                open_ia,
                "heavy_revision",
                0.88,
                "k-4101",
            ),
            # neither reading is
            (
                db.line_id(p1, 1),
                "in der Sache wegen der Müntz-Ordnung",
                open_ia,
                "heavy_revision",
                0.74,
                "k-4101",
            ),
            # both readings fold to it ("Vnd"/"und", "daß"): no gold
            (
                db.line_id(p1, 3),
                "und daß solches geschehen",
                open_ia,
                "heavy_revision",
                0.91,
                "k-4101",
            ),
            # the Potsdam channel: the NC deposit, never gold
            (
                db.line_id(p2, 0),
                "Seiner Churfürstl. Durchl. zu Braunschweig und",
                K2_READER_SOURCE.format(channel="potsdam"),
                "heavy_revision",
                0.86,
                "k-4101",
            ),
            # the v1 reading (the later run's) is the truth
            (db.line_id(p2, 1), "so ich vernommen habe", open_ia, "heavy_revision", 0.83, "k-4101"),
            # minted from the v1 text, no reader: never gold (a row of a 2027 mint)
            (
                db.line_id(q1, 0),
                "Mein Herr, ich habe dero Schreiben",
                "AA IV,4 N.2 (§70-expired AA reading text; channel ia; katalog k-4402)",
                "light_revision",
                0.9,
                "k-4402",
            ),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    path = tmp_path / "inventory.sqlite"
    seed_store(path)
    return path


@pytest.fixture
def german_store_path(store_path: Path) -> Path:
    """The fixture store with the German rows of :func:`seed_german` added."""
    seed_german(store_path)
    return store_path
