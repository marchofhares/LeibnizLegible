"""Bodemann's letters from correspSearch: parsing, filing, the site."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from leibniz import db
from leibniz.catalog import letters as L
from leibniz.web.api import create_app

W2 = "DE-611-HS-854976"  # the fixture's LBr. 464

HEAD = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc>
<notesStmt><note>{first}-{last} of {total} hits</note></notesStmt></fileDesc>
<profileDesc>{body}</profileDesc></teiHeader></TEI>"""


def _letter(
    key: str, sender: str, sref: str, addressee: str, aref: str, date: str, place: str = ""
) -> str:
    where = f'<placeName ref="http://sws.geonames.org/1">{place}</placeName>' if place else ""
    return (
        f'<correspDesc key="{key}"><correspAction type="sent">'
        f'<persName ref="{sref}">{sender}</persName>{where}{date}</correspAction>'
        f'<correspAction type="received"><persName ref="{aref}">{addressee}</persName>'
        f"</correspAction></correspDesc>"
    )


LEIBNIZ = ("Leibniz, Gottfried Wilhelm", L.LEIBNIZ_GND)
HANSEN = ("Hansen, Friedrich Adolf", "http://d-nb.info/gnd/1")

PAGE_1 = HEAD.format(
    first=1,
    last=3,
    total=4,
    body=_letter(
        "464.1", *HANSEN, *LEIBNIZ, '<date when="1695-03-01">1. März 1695</date>', "Kopenhagen"
    )
    + _letter(
        "464.2",
        *LEIBNIZ,
        *HANSEN,
        '<date notBefore="1696-01-01" notAfter="1697-12-31">1696-97</date>',
        "Hannover",
    )
    + _letter(
        "I.6.1",
        *LEIBNIZ,
        "Braunschweig-Lüneburg, Christian von, Herzog",
        "http://d-nb.info/gnd/2",
        '<date notBefore="1697-01-01" notAfter="1698-12-31">1697. 98</date>',
    ),
)
PAGE_2 = HEAD.format(
    first=4,
    last=4,
    total=4,
    body=_letter(
        "230",
        "Kotzebue, Christian Ludwig",
        "http://d-nb.info/gnd/3",
        *LEIBNIZ,
        '<date when="1700-05-05">5. Mai 1700</date>',
        "Wien",
    ),
)


def test_bodemann_numbers_name_their_convolute() -> None:
    assert L.convolute_of("16.2") == "LBr 16"
    assert L.convolute_of("33a.1") == "LBr 33a"
    assert L.convolute_of("230") == "LBr 230"
    assert L.convolute_of("I.6.1") == "LBr f,6"
    assert L.convolute_of("IV.20.3") == "LBr f,20"
    assert L.convolute_of("x.y") is None


def test_a_page_parses_into_letters() -> None:
    found = L.parse_tei(PAGE_1)
    assert [ltr.key for ltr in found] == ["464.1", "464.2", "I.6.1"]
    first, second, prince = found
    assert first.direction == "to" and second.direction == "from"
    assert [p.name for p in first.correspondents] == ["Hansen, Friedrich Adolf"]
    assert first.place == L.Place("Kopenhagen", "http://sws.geonames.org/1")
    assert (first.when, first.year_from, first.year_to) == ("1695-03-01", 1695, 1695)
    assert (second.year_from, second.year_to, second.date_text) == (1696, 1697, "1696-97")
    assert prince.convolute == "LBr f,6" and prince.place is None
    assert L.total_hits(PAGE_1) == 4


def test_the_harvest_pages_through_and_resumes_from_its_cache(tmp_path: Path) -> None:
    pages = {1: PAGE_1, 2: PAGE_2}
    asked: list[str] = []

    def get(url: str) -> bytes:
        asked.append(url)
        return pages[int(url.rsplit("x=", 1)[1])].encode()

    found = L.harvest(get, tmp_path)
    assert [ltr.key for ltr in found] == ["464.1", "464.2", "I.6.1", "230"]
    assert len(asked) == 2 and asked[0] == L.page_url(1)
    again = L.harvest(get, tmp_path)  # everything is on disk now
    assert len(asked) == 2 and [ltr.key for ltr in again] == [ltr.key for ltr in found]


def test_convolutes_and_the_search(tmp_path: Path) -> None:
    index = L.LettersIndex(L.parse_tei(PAGE_1) + L.parse_tei(PAGE_2), "now")
    conv = index.convolutes["LBr 464"]
    assert conv.n_letters == 2 and (conv.year_from, conv.year_to) == (1695, 1697)
    assert conv.correspondent == L.Party(*HANSEN)
    assert [p.name for p, _ in conv.places] == ["Hannover", "Kopenhagen"]
    q = L.LetterQuery
    assert [ltr.key for ltr in index.search(q(who="hansen"))] == ["464.1", "464.2"]
    assert [ltr.key for ltr in index.search(q(place="wien"))] == ["230"]
    assert [ltr.key for ltr in index.search(q(year_from=1697, year_to=1699))] == ["464.2", "I.6.1"]
    assert [ltr.key for ltr in index.search(q(direction="to"))] == ["464.1", "230"]
    assert [ltr.key for ltr in index.search(q(convolutes=("LBr 464",)))] == ["464.1", "464.2"]
    assert index.keys_for(["LBr 464,1"]) == ["LBr 464"]  # a part of the convolute
    path = index.write(tmp_path / "letters.json")
    back = L.LettersIndex.load(path)
    assert [ltr.key for ltr in back.letters] == [ltr.key for ltr in index.letters]
    assert back.letters[0] == index.letters[0]
    assert not L.LettersIndex.load(tmp_path / "missing.json")


def _app(store_path: Path, tmp_path: Path) -> TestClient:
    path = L.LettersIndex(L.parse_tei(PAGE_1) + L.parse_tei(PAGE_2), "now").write(
        tmp_path / "letters.json"
    )
    return TestClient(create_app(store_path, search=None, static_dir=None, letters_path=path))


def test_the_works_list_names_an_unnamed_convolute_from_its_letters(store_path, tmp_path) -> None:
    conn = db.connect(store_path)
    db.upsert_work(
        conn,
        db.Work(
            W2,
            "LeibnizBriefwechsel",
            title="Nachlass Gottfried Wilhelm Leibniz",
            shelfmarks=["LBr. 464"],
        ),
    )
    conn.commit()
    conn.close()
    c = _app(store_path, tmp_path)
    row = next(w for w in c.get("/api/works").json()["works"] if w["work_id"] == W2)
    assert row["label"] == "Hansen, Friedrich Adolf"
    assert row["letters"]["years"] == [1695, 1697] and row["letters"]["n_letters"] == 2
    assert row["letters"]["correspondent"]["ref"] == "http://d-nb.info/gnd/1"
    assert c.get(f"/api/works/{W2}").json()["title"] == "LBr. 464 · Hansen, Friedrich Adolf"


def test_a_letter_convolute_lists_its_letters(store_path, tmp_path) -> None:
    c = _app(store_path, tmp_path)
    work = c.get(f"/api/works/{W2}").json()
    letters = work["letters"]
    assert letters["convolute"] == "LBr 464" and letters["n_items"] == 2
    assert [x["key"] for x in letters["items"]] == ["464.1", "464.2"]
    assert letters["source"]["licence"] == "CC BY 4.0"
    assert "letters" not in c.get("/api/works/00068642").json()


def test_letters_by_correspondent_date_and_place(store_path, tmp_path) -> None:
    c = _app(store_path, tmp_path)
    body = c.get("/api/letters", params={"who": "Hansen"}).json()
    assert body["total"] == 2 and [x["key"] for x in body["letters"]] == ["464.1", "464.2"]
    assert body["letters"][0]["works"] == [W2] and body["letters"][0]["direction"] == "to"
    assert c.get("/api/letters", params={"place": "Wien"}).json()["total"] == 1
    assert c.get("/api/letters", params={"from": 1697}).json()["total"] == 3
    assert c.get("/api/letters", params={"work": W2}).json()["total"] == 2
    assert c.get("/api/letters", params={"work": "00068642"}).json()["total"] == 0
    assert c.get("/api/letters", params={"from": 1200}).status_code == 422
    paged = c.get("/api/letters", params={"limit": 1, "page": 2}).json()
    assert paged["total"] == 4 and [x["key"] for x in paged["letters"]] == ["464.2"]


def test_without_a_letters_file_the_site_says_so(store_path) -> None:
    c = TestClient(create_app(store_path, search=None, static_dir=None, letters_path=None))
    assert c.get("/api/letters").status_code == 503
    assert "letters" not in c.get(f"/api/works/{W2}").json()
