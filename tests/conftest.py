"""Shared fixtures: a small, realistic seeded store for the D-phase tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from leibniz import db

W1 = "00068642"  # IIIF-served Handschriften work
W2 = "DE-611-HS-854976"  # static-JPEG Briefwechsel work


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


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    path = tmp_path / "inventory.sqlite"
    seed_store(path)
    return path
