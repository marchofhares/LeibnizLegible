"""Tests for volume ingestion + the edition cache join (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from leibniz import db
from leibniz.align import ingest as I
from leibniz.align.volumes_sources import EditionSource, readable_sources, source_kind


def test_piece_key_normalisation() -> None:
    assert I.piece_key("014") == "14"
    assert I.piece_key("130a") == "130a"
    assert I.piece_key("7") == "7"


def test_sources_registry_shape() -> None:
    assert source_kind(1, 6) == "ia"
    assert source_kind(4, 1) == "potsdam"
    assert source_kind(1, 14) == "gwlb"
    assert source_kind(1, 13) == "none"
    assert readable_sources(1, 11)[0].url.startswith("https://archive.org/download/")
    assert readable_sources(1, 11)[1].kind == "gwlb"
    src = EditionSource(6, 4, "muenster", part="A–D")
    assert src.url is None and src.text_layer == "pdf" and "permission" in src.terms


def test_ingest_from_hocr_and_cache(tmp_path: Path) -> None:
    def span(bbox: str, size: int, text: str) -> str:
        return f"<span class='ocr_line' title='bbox {bbox}; x_size {size}'>{text}</span>"

    hocr = "\n".join(
        [
            "<html><body><div class='ocr_page' title='bbox 0 0 2400 3300; ppageno 0'>",
            span("2100 241 2200 280", 37, "N. 1"),
            span("300 392 1100 440", 41, "1. LEIBNIZ AN ARNAULD"),
            span("275 700 2100 750", 41, "Monsieur, je vous supplie de croire que rien ne me"),
            span("275 770 2100 820", 41, "davantage que la marque de vostre souvenir et de vostre"),
            span("280 2900 2100 2940", 33, "2 rien ne me touche erg. L"),
            "</div></body></html>",
        ]
    )
    raw = tmp_path / "x_hocr.html"
    raw.write_text(hocr, encoding="utf-8")
    src = EditionSource(2, 1, "ia", "x", 1)
    res = I.ingest_volume(src, raw=raw, editions_dir=tmp_path / "ed")
    assert res.status == "extracted" and res.n_pieces == 1
    data = json.loads(res.path.read_text(encoding="utf-8"))
    assert data["pieces"]["1"]["text"].startswith("Monsieur, je vous supplie")
    assert "erg. L" not in data["pieces"]["1"]["text"]
    # second call is served from the cache
    assert I.ingest_volume(src, raw=raw, editions_dir=tmp_path / "ed").status == "cached"
    assert I.load_volume_texts(res.path) == {"1": data["pieces"]["1"]["text"]}


def test_build_edition_cache_joins_katalog() -> None:
    conn = db.init_db(":memory:")
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="R1",
            aa_refs=[{"series": 2, "volume": 1, "piece": "001", "source": "aa_column"}],
        ),
    )
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="R2",
            aa_refs=[{"series": 2, "volume": 1, "piece": "5a", "source": "aa_column"}],
        ),
    )
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="R3",
            aa_refs=[{"series": 7, "volume": 2, "piece": "9", "source": "aa_column"}],
        ),
    )
    db.upsert_katalog_record(
        conn,
        db.KatalogRecord(
            record_id="R4", aa_refs=[{"series": 2, "volume": 1, "piece": "9", "source": "bezuege"}]
        ),
    )
    conn.commit()
    texts = {(2, 1): {"1": "x" * 50, "5": "y" * 50, "9": "short"}}
    cache, stats = I.build_edition_cache(conn, texts)
    assert set(cache) == {
        "R1",
        "R2",
    }  # 001 → 1; 5a falls back to 5; R3 has no source; R4 is a Bezug
    assert stats.records_with_text == 2 and stats.by_volume == {"II,1": 2}
    assert stats.volumes_without_source == {"VII,2": 1}


def test_cross_source_qa() -> None:
    a = {"1": "Monsieur je vous supplie de croire", "2": "que rien ne me touche", "3": "only here"}
    b = {"1": "Monsieur je vous supplie de croire", "2": "totally different text here indeed"}
    qa, only_one = I.cross_source_qa(a, b)
    assert qa.n_sampled == 2 and qa.n_flagged == 1 and only_one == 1
