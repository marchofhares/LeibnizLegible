"""The browse index: where a work goes, what it is called, in what order.

The synthetic tests cover each rule; the last test runs the three live fixtures
(``tests/fixtures/*_live.json``: the works table, the letter convolutes'
sender/addressee pairs as ``browse.CORRESPONDENTS_SQL`` returns them, and the
ids of the works with catalogue records, exported read-only from the corpus
store on 2026-10-06) and holds the headline shape.
"""

from __future__ import annotations

import json
from pathlib import Path

from leibniz.db import Work
from leibniz.web import browse
from leibniz.web.browse import Correspondence as C

FIXTURES = Path(__file__).parent / "fixtures"
LH, LBR, MARG = "LeibnizHandschriften", "LeibnizBriefwechsel", "LeibnizMarginalien"
MATH = "Leibniz-Handschriften zur Mathematik"


def work(wid: str, set_name: str, marks, title: str | None = None, pages: int = 2) -> Work:
    marks = [marks] if isinstance(marks, str) else list(marks or [])
    return Work(wid, set_name, title=title, shelfmarks=marks, n_canvases=pages)


def family(families: list[browse.Family], key: str) -> browse.Family:
    return next(f for f in families if f.key == key)


def section(families: list[browse.Family], fam: str, key: str) -> browse.Section:
    return next(s for s in family(families, fam).sections if s.key == key)


# ---- order ------------------------------------------------------------------- #


def test_natural_key_numbers_by_value_and_before_letters() -> None:
    marks = ["3 A 8", "10, 1", "3, 5", "2, 1", "3 B 1", "3", "3, 10", "3a"]
    assert sorted(marks, key=browse.natural_key) == [
        "2, 1",
        "3",
        "3, 5",
        "3, 10",
        "3a",
        "3 A 8",
        "3 B 1",
        "10, 1",
    ]
    assert browse.natural_key("7 A") == browse.natural_key("7a") < browse.natural_key("7b")
    # a Roman numeral counts as its number only on request
    assert browse.natural_key("III, 2", roman=True) == browse.natural_key("3, 2")
    assert browse.natural_key("7 C") > browse.natural_key("7 B")


# ---- LH ---------------------------------------------------------------------- #


def test_lh_section_is_the_first_part_and_named_by_its_titles() -> None:
    works = [
        work("a", LH, "LH 35, 3 A 8", f"{MATH} LH 35, 3 A 8", pages=12),
        work("b", LH, "LH 35, 10, 1", f"{MATH} LH 35, 10, 1"),
        work("c", LH, "LH 35, 3, 5", f"{MATH} LH 35, 3, 5"),
        work("d", LH, "LH 35, 2, 1", "Leibniz_Handschriften zur Mathematik LH 35, 2, 1"),
        work("e", LH, ["LH 35, 3 B 1", "LH35, 3 B 1"], f"{MATH} LH 35, 3 B 1"),
        work("t", LH, "LH 1, 19", "Leibniz-Handschriften zur Theologie LH 1, 19"),
        work(
            "g", LH, "LH 23, 2, 21", "Leibniz-Handschriften zu Braunschweig-Lüneburg LH 23, 2, 21"
        ),
    ]
    families = browse.build_index(works)
    assert [f.key for f in families] == ["LH"]
    lh = families[0]
    assert [(s.key, s.anchor, s.label) for s in lh.sections] == [
        ("1", "lh-1", "Theologie"),
        ("23", "lh-23", "Braunschweig-Lüneburg"),
        ("35", "lh-35", "Mathematik"),
    ]
    math = lh.sections[2]
    assert math.title == "LH 35 · Mathematik" and (math.n_works, math.n_pages) == (5, 20)
    # natural order of the remaining parts: 2 before 10, numbers before letters
    assert [e.label for e in math.entries] == [
        "LH 35, 2, 1",
        "LH 35, 3, 5",
        "LH 35, 3 A 8",
        "LH 35, 3 B 1",
        "LH 35, 10, 1",
    ]
    assert math.entries[3].shelfmarks == ("LH 35, 3 B 1", "LH35, 3 B 1")
    assert (lh.n_works, lh.n_pages) == (7, 24)


def test_lh_roman_numeral_shelfmarks_and_part_letters() -> None:
    works = [
        work("r1", LH, "LH XXXV, III, 2"),
        work("r2", LH, "LH XXXV, 3, 10"),
        work("r3", LH, "LH XXXV, II, 1"),
        work("iv", LH, "LH IV, 6, 18", "LH 4,6,18"),
        # part letters that happen to be Roman numerals stay letters
        *(work(f"p{x}", LH, f"LH 1, 3, 7 {x}") for x in "MLKIDCBA"),
        work("p0", LH, "LH 1, 3, 7"),
        work("p8", LH, ["LH 1, 3, 8 A", "LH 1, 3, 8a"]),
    ]
    families = browse.build_index(works)
    assert [s.key for s in family(families, "LH").sections] == ["1", "4", "35"]
    assert [e.shelfmark for e in section(families, "LH", "35").entries] == [
        "LH XXXV, II, 1",
        "LH XXXV, III, 2",
        "LH XXXV, 3, 10",
    ]
    assert [e.shelfmark for e in section(families, "LH", "1").entries] == [
        "LH 1, 3, 7",
        *(f"LH 1, 3, 7 {x}" for x in "ABCDIKLM"),
        "LH 1, 3, 8 A",
    ]
    # no phrase in any title: the section falls back to its number
    four = section(families, "LH", "4")
    assert (four.label, four.title, four.entries[0].label) == ("LH 4", "LH 4", "LH IV, 6, 18")


def test_lh_label_needs_a_majority_and_entries_keep_their_own_phrase() -> None:
    head = "Leibniz-Handschriften"
    works = [
        work("a", LH, "LH 37, 1", f"{head} zur Akustik LH 37, 1"),
        work("b", LH, "LH 37, 2", f"{head} zur Optik und Dioptrik LH 37, 2"),
        work("c", LH, "LH 37, 3", f"{head} zur Physica LH 37, 3"),
        work("v1", LH, "LH 42, 1", f"{head} Varia LH 42, 1"),
        work("v2", LH, "LH 42, 2", f"{head} Varia LH 42, 2"),
        work("v3", LH, "LH 42, 3", f"{head} Varia LH 42, 3"),
        work(
            "v4", LH, "LH 42, 4", "Handschriften des 18. Jahrhunderts zur Rechenmaschine LH 42, 4"
        ),
        work("v5", LH, "LH 42, 5", f"{head} LH 42, 5"),
    ]
    families = browse.build_index(works)
    physics = section(families, "LH", "37")
    assert (physics.label, physics.title) == ("LH 37", "LH 37")
    assert [e.label for e in physics.entries] == [
        "LH 37, 1 · Akustik",
        "LH 37, 2 · Optik und Dioptrik",
        "LH 37, 3 · Physica",
    ]
    varia = section(families, "LH", "42")  # three of five titles agree
    assert varia.title == "LH 42 · Varia"
    assert [e.label for e in varia.entries] == [
        "LH 42, 1",
        "LH 42, 2",
        "LH 42, 3",
        "LH 42, 4 · Handschriften des 18. Jahrhunderts zur Rechenmaschine",
        "LH 42, 5",
    ]


def test_section_phrase_reads_the_librarys_titles() -> None:
    phrase = browse.section_phrase
    assert phrase("Leibniz-Handschriften zur Mathematik LH 35, 3 A 8") == "Mathematik"
    assert phrase("Leibniz-Handschriften zu Braunschweig-Lüneburg LH 23, 2, 21") == (
        "Braunschweig-Lüneburg"
    )
    assert phrase("Leibniz-Handschriften zur Ad vitam Leibnitii LH 41, 3") == "Ad vitam Leibnitii"
    assert phrase("Leibniz-Handschriften Ad vitam Leibnitii LH 41, 1") == "Ad vitam Leibnitii"
    assert phrase("Leibniz- Handschriften zur Medizin LH 3, 5") == "Medizin"
    assert phrase("Leibnitz-Handschriften zur Philosophie LH 4, 1") == "Philosophie"
    assert phrase("Leibniz-Hanschriften zu Philosophie LH 4, 2") == "Philosophie"
    assert phrase("Leibniz-Handschriften LH 4, 3") is None
    assert phrase("LH 4,6,18") is None and phrase("Nachlass Gottfried Wilhelm Leibniz") is None
    assert phrase(None) is None


# ---- LBr --------------------------------------------------------------------- #


def test_correspondent_names_strip_source_tags_and_split_run_together_cells() -> None:
    names = browse.correspondent_names
    assert names("Oldenburg (KorrespDB) (GND)") == ["Oldenburg"]
    assert names("Jablonski,D.E. (KorrespDB) (GND)") == ["Jablonski, D.E."]
    assert names("Wolfenbüttel,Rudolf August v. (KorrespDB) (GND)") == [
        "Wolfenbüttel, Rudolf August v."
    ]
    assert names("Bartholin, C. (KorrespDB)") == ["Bartholin, C."]
    # a tag that is not a source belongs to the name
    assert names("Leopold I. (Kaiser) (KorrespDB) (GND)") == ["Leopold I. (Kaiser)"]
    assert names("Görtz,Fr.W.v. (Schlitz) (KorrespDB) (GND)") == ["Görtz, Fr.W.v. (Schlitz)"]
    # several people in one cell
    assert names("Brand,H. (KorrespDB) (GND)Leibniz (GND)") == ["Brand, H.", "Leibniz"]
    assert names(
        "Sophie (KorrespDB) (GND)Orléans,Elisabeth Charlotte v. (KorrespDB) (GND)u.a."
    ) == [
        "Sophie",
        "Orléans, Elisabeth Charlotte v.",
    ]
    # doubt marks and blanks
    assert names("Ilgen ?") == ["Ilgen"] and names("Krebs (?) (KorrespDB)") == ["Krebs"]
    assert names("Leibniz (GND)?") == ["Leibniz"]
    assert names("?") == [] and names(None) == [] and names("") == []


def test_correspondent_is_the_name_most_often_beside_leibniz() -> None:
    rows = [
        C("Oldenburg (KorrespDB) (GND)", "Leibniz (GND)", 30, "Heinrich Oldenburg an Leibniz"),
        C("Leibniz (GND)", "Oldenburg (KorrespDB) (GND)", 18, "Leibniz an Heinrich Oldenburg"),
        C("Leibniz (GND)", "Tschirnhaus (KorrespDB) (GND)", 3, None),
        C("?", "Leibniz (GND)", 40, None),
        C(None, None, 50, None),
    ]
    assert browse.correspondent(rows) == "Oldenburg"
    assert browse.correspondent_weights(rows) == {"Oldenburg": 48, "Tschirnhaus": 3}
    # his relations are not himself
    kin = [C("Leibniz,J.Fr. (KorrespDB) (GND)", "Leibniz (GND)", 5, None)]
    assert browse.correspondent(kin) == "Leibniz, J.Fr."
    # of equals, the first named; a bare surname counts with its one fuller form
    assert browse.correspondent([C("Brice (KorrespDB) (GND)Acad.Franç.", "Leibniz", 1)]) == "Brice"
    split = [
        C("Molanus (KorrespDB) (GND)", "Leibniz (GND)", 22),
        C("Eckhard,A. (KorrespDB) (GND)", "Leibniz (GND)", 16),
        C("Leibniz (GND)", "Eckhard", 13),
    ]
    assert browse.correspondent(split) == "Eckhard, A."
    two = [C("Meier,G. (GND)", "Leibniz", 3), C("Meier,J. (GND)", "Leibniz", 2), C("Meier", "?", 9)]
    assert browse.correspondent(two) == "Meier"  # two fuller forms: not merged


def test_correspondent_falls_back_to_the_record_title_then_to_nothing() -> None:
    only_leibniz = [C("Leibniz (GND)", None, 2, "Leibniz an Jean Baptiste Colbert")]
    assert browse.correspondent(only_leibniz) == "Jean Baptiste Colbert"
    assert browse.correspondent([C("Leibniz (GND)", "?", 1, "Magnus Hesenthaler an Leibniz")]) == (
        "Magnus Hesenthaler"
    )
    assert browse.correspondent([C("?", "Leibniz", 1, "? [Königsegg] an Leibniz: Bericht")]) == (
        "Königsegg"
    )
    for titel in ("Leibniz an -- (?)", "In Luparam.", "Kurfürst Ernst August für Leibniz", None):
        assert browse.correspondent([C("Leibniz (GND)", "?", 3, titel)]) is None
    assert browse.correspondent([C(None, None, 2, "[Aufz. betr. ein chines. Brettspiel]")]) is None
    assert browse.correspondent([]) is None


def test_lbr_one_section_in_two_orders() -> None:
    works = [
        work("f20", LBR, "LBr. F 20"),
        work("w695", LBR, "LBr. 695", "Nachlass Gottfried Wilhelm Leibniz", pages=120),
        work("w292a", LBR, "LBr. 292a"),
        work("w2", LBR, "LBr. 2"),
        work("w827", LBR, "L Br. 827"),  # the label spelled apart
        work("f3", LBR, "Lbr. F 3"),
        work("w82", LBR, "LBr. 82"),
        work("w10", LBR, "LBr . 10"),
        work("w292", LBR, "LBr. 292"),
        work("w726", LH, "LBr. 726", "Nachlass Gottfried Wilhelm Leibniz"),  # filed with the LH
        work("w57", LBR, "LBr. 57, 2"),
    ]
    rows = {
        "w2": [C("Abercromby (KorrespDB)", "Leibniz (GND)", 3)],
        "w10": [C("Leibniz (GND)", "Alvensleben,J.Fr. (KorrespDB) (GND)", 30)],
        "w82": [C("Böhmer,J.Chr. (KorrespDB) (GND)", "Leibniz (GND)", 30)],
        "w292": [C("Leibniz (GND)", None, 4, "Leibniz an Paul von Fuchs")],
        "w695": [C("Oldenburg (KorrespDB) (GND)", "Leibniz (GND)", 48)],
        "w726": [C("Philipp,Chr. (KorrespDB) (GND)", "Leibniz (GND)", 83)],
        "f20": [C("Hessen-Rheinfels,Ernst v. (KorrespDB) (GND)", "Leibniz (GND)", 303)],
        "w57": [C("Leibniz (GND)", None, 1, None)],
    }
    families = browse.build_index(works, rows, with_records=rows.keys())
    assert [f.key for f in families] == ["LBr"]
    lbr = families[0].sections[0]
    assert (lbr.key, lbr.anchor, lbr.n_works, lbr.n_pages) == ("LBr", "lbr", 11, 140)
    # by number: plain numbers (292a after 292), then the lettered, by letter then number
    assert lbr.by_number == [
        "w2", "w10", "w57", "w82", "w292", "w292a", "w695", "w726", "w827", "f3", "f20",
    ]  # fmt: skip
    # by name, accents ignored; the unnamed last, by number, under their bare shelfmark
    assert [(e.label, e.shelfmark) for e in lbr.entries] == [
        ("Abercromby", "LBr. 2"),
        ("Alvensleben, J.Fr.", "LBr . 10"),
        ("Böhmer, J.Chr.", "LBr. 82"),
        ("Hessen-Rheinfels, Ernst v.", "LBr. F 20"),
        ("Oldenburg", "LBr. 695"),
        ("Paul von Fuchs", "LBr. 292"),
        ("Philipp, Chr.", "LBr. 726"),
        ("LBr. 57, 2", "LBr. 57, 2"),
        ("LBr. 292a", "LBr. 292a"),
        ("L Br. 827", "L Br. 827"),
        ("Lbr. F 3", "Lbr. F 3"),
    ]
    flags = {e.work_id: e.has_katalog for e in lbr.entries}
    assert flags["w57"] and flags["w695"] and not flags["w292a"] and not flags["w827"]
    assert lbr.entries[4].title == "Nachlass Gottfried Wilhelm Leibniz"


def test_a_name_out_of_alphabetical_place_is_withheld() -> None:
    run = [
        {"Abercromby": 3},
        {"Hessen-Rheinfels, Ernst v.": 10, "Arnauld": 4},  # the forwarder outweighs the writer
        {"Avemann, H.": 36},
        {"Ursinus v.Bär": 7},  # filed under Bär
        {"Mencke, O.": 4, "Bernoulli, Joh.": 1},
        {"Mencke, O.": 3, "Braun, J.": 1},  # neither fits between Bernoulli and Bernstorff
        {"Bernstorff": 25},
        {"Böckler": 3},  # filed as Boeckler
        {"Bogdan": 2},
        {"Crusen": 11},
        {"Chuno": 60},  # the shelf spells him Cuneau: out of order, but well attested
        {"Cunningham, A": 4},
        {"Schmidt, J.A.": 1},
        {},
        {"Jablonski, D.E.": 62},  # J is interfiled with I …
        {"Ilgen": 6},
        {"Juncker": 3},
        {"Kotzebue, J.F.": 3},
        {"Crafft, J.D.": 170, "Krafft": 1},  # … and Crafft is filed as Krafft
        {"Schreckh, C.": 20, "Kraus": 18},
        {"Krebs": 1},
        {"Stoeteroggen": 3},
        {"DesVignoles": 24},  # filed under V
        {"Dionysius Werlensis": 2},
    ]
    assert browse.names_in_order(run) == [
        "Abercromby",
        "Arnauld",
        "Avemann, H.",
        "Ursinus v.Bär",
        "Bernoulli, Joh.",
        None,
        "Bernstorff",
        "Böckler",
        "Bogdan",
        "Crusen",
        "Chuno",
        "Cunningham, A",
        None,
        None,
        "Jablonski, D.E.",
        "Ilgen",
        "Juncker",
        "Kotzebue, J.F.",
        "Crafft, J.D.",
        "Kraus",
        "Krebs",
        "Stoeteroggen",
        "DesVignoles",
        "Dionysius Werlensis",
    ]
    assert browse.names_in_order([]) == []
    # a well-attested name whose initial does not fit stays out
    helmont = [{"Heldt": 1}, {"Motzfeld": 20}, {"Hennenberg": 6}, {"Hertel": 68}]
    assert browse.names_in_order(helmont) == ["Heldt", None, "Hennenberg", "Hertel"]


def test_lbr_order_check_runs_over_the_numbers_and_spares_the_f_series() -> None:
    works = [
        work("w5", LBR, "LBr. 5"),
        work("w16", LBR, "LBr. 16"),
        work("w21", LBR, "LBr. 21"),
        work("w461", LBR, "LBr. 461"),
        work("w467", LBR, "LBr. 467"),
        work("w468", LBR, "LBr. 468"),
        work("w1028", LBR, "LBr. 1028"),
        work("f20", LBR, "LBr. F 20"),
        work("f27", LBR, "LBr. F 27"),
        work("f30", LBR, "LBr. F 30"),
    ]
    landgrave = "Hessen-Rheinfels,Ernst v. (KorrespDB) (GND)"
    rows = {
        "w5": [C("Hamrath (KorrespDB)", "Leibniz (GND)", 2), C("Addison", "Leibniz (GND)", 1)],
        "w16": [C(landgrave, "Leibniz (GND)", 10), C("Arnauld (GND)", landgrave, 4)],
        "w21": [C("Avemann,H. (KorrespDB)", "Leibniz (GND)", 36)],
        "w461": [C("Kelner (KorrespDB)", "Leibniz (GND)", 3)],
        "w467": [C("Avemann,H. (KorrespDB)", "Leibniz (GND)", 1)],
        "w468": [C("Kevel (KorrespDB)", "Leibniz (GND)", 1)],
        "w1028": [C("Zunner (KorrespDB)", "Leibniz (GND)", 21)],
        "f20": [C(landgrave, "Leibniz (GND)", 303)],
        "f27": [C("Sophie Charlotte (KorrespDB) (GND)", "Leibniz (GND)", 87)],
        "f30": [C(landgrave, "Leibniz (GND)", 1)],
    }
    lbr = browse.build_index(works, rows, rows.keys())[0].sections[0]
    labels = {e.work_id: e.label for e in lbr.entries}
    assert labels == {
        "w5": "Addison",
        "w16": "Arnauld",
        "w21": "Avemann, H.",
        "w461": "Kelner",
        "w467": "LBr. 467",  # Avemann's letter in somebody else's convolute
        "w468": "Kevel",
        "w1028": "Zunner",
        "f20": "Hessen-Rheinfels, Ernst v.",
        "f27": "Sophie Charlotte",
        "f30": "LBr. F 30",  # one name, two F convolutes: it stays with the fuller one
    }
    assert [e.work_id for e in lbr.entries][-2:] == ["w467", "f30"]


# ---- Marg, Other --------------------------------------------------------------- #


def test_marg_by_number_with_the_title_cut_at_a_word() -> None:
    long = (
        "[Pandectarum Sive Partitionum universalium Conradi Gesneri Tigurini, medici & "
        "philosophiae professoris. libri XXI] PANDECTARVM SIVE || Partitionum uniuersalium"
    )
    works = [
        work("m230b", MARG, ["Leibn. Marg. 230, Stück 10", "Leibn. Marg. 230"], "Zehntes"),
        work("m64b", MARG, "Leibn. Marg. 64:2, Stück 1", long, pages=774),
        work("m9", MARG, ["Leibn. Marg. 9", "ZEN Leibn. Marg. 9"], "Mithridates Gesneri"),
        work("m230a", MARG, "Leibn. Marg. 230, Stück 2", "Zweites"),
        work("m64a", MARG, "Leibn. Marg. 64:1", "Erstes"),
        work("m40", MARG, ["ZEN Leibn. Marg. 40", "Leibn. Marg. 40"], None),
        work("m0", MARG, "Leibn. Marg. 0,1, Stück 3", "Besoldi"),
    ]
    families = browse.build_index(works)
    assert [f.key for f in families] == ["Marg"]
    marg = families[0].sections[0]
    assert (marg.key, marg.anchor, marg.label) == ("Marg", "marg", "Marginalien")
    assert [e.shelfmark for e in marg.entries] == [
        "Leibn. Marg. 0,1, Stück 3",
        "Leibn. Marg. 9",
        "ZEN Leibn. Marg. 40",
        "Leibn. Marg. 64:1",
        "Leibn. Marg. 64:2, Stück 1",
        "Leibn. Marg. 230, Stück 2",
        "Leibn. Marg. 230, Stück 10",
    ]
    cut = marg.entries[4]
    assert cut.title == long and cut.label != long
    assert cut.label.endswith("…") and 100 < len(cut.label) <= browse.TITLE_LIMIT + 1
    assert long.startswith(cut.label[:-1]) and long[len(cut.label) - 1] in " ,."  # a word boundary
    assert marg.entries[2].label == "ZEN Leibn. Marg. 40"  # no title: the shelfmark
    assert browse.truncate("short title") == "short title"
    assert browse.truncate("x" * 300) == "x" * browse.TITLE_LIMIT + "…"


def test_everything_else_is_other_one_section_per_set() -> None:
    works = [
        work("l1", "Leibnitiana", "LH XXXV, I, 17, Bl. 1 - 17", "De Constructione"),
        work("l2", "Leibnitiana", ["Ms XXIII, 23a", "MS XXIII, 23a"], "Leibnitii Protogaea"),
        work("l3", "Leibnitiana", "Ms IV, 313", "Handschriftenbestand Ms"),
        work("r1", "leibniz-rekonstruktionen", "1729805", "Rekonstruktion Nr. 1729805"),
        work("r2", "leibniz-rekonstruktionen", None, "Rekonstruktionen", pages=0),
        work("h1", LH, "Ms IV, 471 : G-M", "Handschriftenbestand Ms"),
        work("h2", LH, [], "Nachlass Gottfried Wilhelm Leibniz", pages=0),
        work("h3", LH, "LK-MOW Leibniz 10", "Ein Konvolut"),
        work("h4", LH, "Ms IV, 471 : A-F", "Handschriftenbestand Ms"),
        work("m1", MARG, "Nm-A 605", "Traite Du Triangle Arithmetique"),
        work("m2", MARG, [], "La Vie De Monsieur Des-Cartes", pages=0),
        work("m3", MARG, [], "Geometria", pages=0),
        work("x1", "SomethingNew", "X 1", None),
        work("ok", LH, "LH 35, 1, 1", f"{MATH} LH 35, 1, 1"),
    ]
    families = browse.build_index(works)
    assert [f.key for f in families] == ["LH", "Other"]
    other = family(families, "Other")
    assert [(s.key, s.anchor, s.label) for s in other.sections] == [
        ("Leibnitiana", "other-leibnitiana", "Leibnitiana"),
        (LH, "other-leibnizhandschriften", "Leibniz-Handschriften (LH)"),
        (MARG, "other-leibnizmarginalien", "Leibniz-Marginalien"),
        ("leibniz-rekonstruktionen", "other-leibniz-rekonstruktionen", "Leibniz-Rekonstruktionen"),
        ("SomethingNew", "other-somethingnew", "SomethingNew"),
    ]
    by_key = {s.key: s for s in other.sections}
    # the small sets keep their works together, LH shelfmark or not; by shelfmark string
    assert [e.work_id for e in by_key["Leibnitiana"].entries] == ["l1", "l3", "l2"]
    # the works without a shelfmark last, by title
    assert [e.work_id for e in by_key[LH].entries] == ["h3", "h4", "h1", "h2"]
    assert [e.work_id for e in by_key[MARG].entries] == ["m1", "m3", "m2"]
    assert [(e.shelfmark, e.label) for e in by_key["leibniz-rekonstruktionen"].entries] == [
        ("1729805", "Rekonstruktion Nr. 1729805"),
        ("", "Rekonstruktionen"),
    ]
    assert by_key["SomethingNew"].entries[0].label == "X 1"  # no title: the shelfmark
    assert other.n_works == 13 and family(families, "LH").n_works == 1


# ---- the shapes the API serves ------------------------------------------------- #


def _small() -> list[browse.Family]:
    works = [
        work("a", LH, "LH 35, 3 A 8", f"{MATH} LH 35, 3 A 8", pages=12),
        work("b", LBR, "LBr. 695", "Nachlass Gottfried Wilhelm Leibniz", pages=120),
        work("c", LBR, "LBr. F 20", "Nachlass Gottfried Wilhelm Leibniz", pages=30),
        work("d", MARG, "Leibn. Marg. 64:1", "Pandectarum", pages=700),
        work("e", "Leibnitiana", "LH XLII,5", "Aufzeichnungen zur Rechenmaschine", pages=136),
        work("f", LH, "LBr. 726", "Nachlass Gottfried Wilhelm Leibniz", pages=226),
    ]
    rows = {"b": [C("Oldenburg (KorrespDB) (GND)", "Leibniz (GND)", 48)]}
    return browse.build_index(works, rows, with_records={"a", "b"})


def test_rows_tree_and_places() -> None:
    families = _small()
    rows = browse.rows(families)
    assert [r["work_id"] for r in rows] == ["a", "b", "c", "d", "e", "f"]
    assert rows[0] == {
        "work_id": "a",
        "set": LH,
        "title": f"{MATH} LH 35, 3 A 8",
        "shelfmark": "LH 35, 3 A 8",
        "shelfmarks": ["LH 35, 3 A 8"],
        "family": "LH",
        "section": "35",
        "section_label": "Mathematik",
        "label": "LH 35, 3 A 8",
        "n_canvases": 12,
        "has_katalog": True,
    }
    assert [(r["family"], r["section"], r["label"]) for r in rows[1:]] == [
        ("LBr", "LBr", "Oldenburg"),
        ("LBr", "LBr", "LBr. F 20"),
        ("Marg", "Marg", "Pandectarum"),
        ("Other", "Leibnitiana", "Aufzeichnungen zur Rechenmaschine"),
        ("LBr", "LBr", "LBr. 726"),
    ]
    tree = browse.tree(families)
    assert [g["family"] for g in tree] == list(browse.FAMILIES)
    assert [g["name"] for g in tree] == [
        "Handschriften (LH)",
        "Briefwechsel (LBr)",
        "Marginalien",
        "Other",
    ]
    assert tree[0]["sections"] == [
        {
            "section": "35",
            "anchor": "lh-35",
            "label": "Mathematik",
            "title": "LH 35 · Mathematik",
            "n_works": 1,
            "n_pages": 12,
            "entries": ["a"],
        }
    ]
    letters = tree[1]["sections"][0]
    assert letters["entries"] == ["b", "f", "c"] and letters["by_number"] == ["b", "f", "c"]
    assert (tree[1]["n_works"], tree[1]["n_pages"]) == (3, 376)
    assert "by_number" not in tree[2]["sections"][0]
    # every work once
    listed = [w for g in tree for s in g["sections"] for w in s["entries"]]
    assert sorted(listed) == [r["work_id"] for r in rows]
    places = browse.places(families)
    assert places["a"] == {
        "family": "LH",
        "section": "35",
        "anchor": "lh-35",
        "label": "Mathematik",
        "title": "LH 35 · Mathematik",
    }
    assert places["f"]["anchor"] == "lbr" and places["e"]["anchor"] == "other-leibnitiana"


def test_select_narrows_to_a_set_or_a_family() -> None:
    families = _small()
    letters = browse.select(families, family="LBr")
    assert [f.key for f in letters] == ["LBr"] and letters[0].n_works == 3
    in_lh_set = browse.select(families, set_name=LH)
    assert [(f.key, [e.work_id for s in f.sections for e in s.entries]) for f in in_lh_set] == [
        ("LH", ["a"]),
        ("LBr", ["f"]),
    ]
    assert in_lh_set[1].sections[0].by_number == ["f"]
    # a section keeps its name when its works are narrowed
    assert in_lh_set[0].sections[0].title == "LH 35 · Mathematik"
    assert browse.select(families, set_name=LH, family="Marg") == []
    assert browse.select(families, set_name="nope") == []
    assert [f.n_works for f in families] == [1, 3, 1, 1]  # the full tree is untouched


# ---- the live rows ------------------------------------------------------------- #


def _live() -> tuple[list[Work], dict[str, list[C]], set[str]]:
    def load(name: str) -> list[dict]:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    works = [
        Work(
            r["gwlb_object_id"],
            r["set_name"],
            title=r["title"],
            shelfmarks=json.loads(r["shelfmarks"]) if r["shelfmarks"] else [],
            n_canvases=r["n_canvases"],
        )
        for r in load("works_live.json")
    ]
    correspondents = browse.group_correspondents(load("lbr_correspondents_live.json"))
    with_records = {r["work_id"] for r in load("crosswalk_works_live.json")}
    return works, correspondents, with_records


def test_live_fixtures_headline_shape() -> None:
    works, correspondents, with_records = _live()
    assert len(works) == 2225 and len(with_records) == 1197
    families = browse.build_index(works, correspondents, with_records)

    # every work lands in exactly one entry
    placed = [e.work_id for f in families for s in f.sections for e in s.entries]
    assert len(placed) == len(set(placed)) == len(works)
    assert {f.key: f.n_works for f in families} == {
        "LH": 750,
        "LBr": 1060,
        "Marg": 370,
        "Other": 45,
    }
    assert sum(f.n_pages for f in families) == sum(w.n_canvases or 0 for w in works) == 236795

    # the LH sections, each under the phrase its titles agree on
    lh = family(families, "LH")
    present = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 19, 20, 21, 23, 24, 25, 27]
    present += [34, 35, 36, 37, 38, 39, 40, 41, 42]
    assert [int(s.key) for s in lh.sections] == present
    titles = {s.key: s.title for s in lh.sections}
    assert titles["1"] == "LH 1 · Theologie" and titles["35"] == "LH 35 · Mathematik"
    assert titles["23"] == "LH 23 · Braunschweig-Lüneburg" and titles["4"] == "LH 4 · Philosophie"
    assert titles["41"] == "LH 41 · Ad vitam Leibnitii"
    assert [t for t in titles.values() if " · " not in t] == ["LH 37", "LH 42"]  # no majority
    assert section(families, "LH", "35").n_works == 303
    theology = [e.shelfmark for e in section(families, "LH", "1").entries]
    at = theology.index("LH 1, 3, 7 A")
    assert theology[at : at + 12] == [f"LH 1, 3, 7 {x}" for x in "ABCDEFGHIKLM"]

    # the letters: who got a correspondent, and that the well-known ones are right
    lbr = family(families, "LBr").sections[0]
    by_mark = {e.shelfmark: e for e in lbr.entries}
    named = [e for e in lbr.entries if e.label != e.shelfmark]
    share = len(named) / lbr.n_works
    linked = sum(e.has_katalog for e in lbr.entries)
    print(
        f"\nLBr: {len(named)} of {lbr.n_works} convolutes carry a correspondent "
        f"({share:.1%}); {linked} have catalogue records ({linked / lbr.n_works:.1%})"
    )
    assert linked == 744 and 0.60 < share < linked / lbr.n_works
    assert lbr.entries[: len(named)] == named and lbr.entries[0].label == "Abercromby"
    assert len(lbr.by_number) == 1060 and by_mark["LBr. 1"].work_id == lbr.by_number[0]
    assert by_mark["LBr. F 35"].work_id == lbr.by_number[-1]
    expected = {
        "LBr. 695": "Oldenburg",
        "LBr. 228": "Eckhart, J.G.",
        "LBr. 16": "Arnauld",
        "LBr. 57, 1": "Bernoulli, Joh.",
        "LBr. 57, 2": "LBr. 57, 2",  # only third-party letters are linked: unnamed
        "LBr. 389": "Helmont",
        "LBr. 501": "Crafft, J.D.",
        "LBr. 886": "Spinoza",
        "LBr. 726": "Philipp, Chr.",  # filed in the manuscripts' set
        "L Br. 827": "L Br. 827",  # no records: its shelfmark, in the letters all the same
        "LBr. F 20": "Hessen-Rheinfels, Ernst v.",
    }
    assert {mark: by_mark[mark].label for mark in expected} == expected
    assert by_mark["LBr. 726"].set_name == LH

    marg = family(families, "Marg").sections[0]
    assert marg.entries[0].shelfmark == "Leibn. Marg. 0" and marg.n_pages == 103274
    assert max(len(e.label) for e in marg.entries) <= browse.TITLE_LIMIT + 1
    other = {s.key: s.n_works for s in family(families, "Other").sections}
    assert other == {
        "Leibnitiana": 12,
        LH: 5,
        MARG: 26,
        "leibniz-rekonstruktionen": 2,
    }
