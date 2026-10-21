"""Tests for K3's evaluation helpers (offline, no model)."""

from __future__ import annotations

from leibniz.htr import k3_eval as E
from leibniz.htr import metrics


def test_edit_ops_sum_to_the_distance() -> None:
    cases = [
        ("abc", "abc"),
        ("abc", "abd"),
        ("abc", "ab"),
        ("abc", "abcd"),
        ("", "xy"),
        ("xy", ""),
        ("kitten", "sitting"),
        ("daß er", "das er"),
        ("Herrn", "Hern"),
    ]
    for ref, hyp in cases:
        s, i, d = E.edit_ops(ref, hyp)
        assert s + i + d == metrics.edit_distance(ref, hyp), (ref, hyp)
    assert E.edit_ops("abc", "abd") == (1, 0, 0)
    assert E.edit_ops("abc", "ab") == (0, 0, 1)
    assert E.edit_ops("abc", "abcd") == (0, 1, 0)
    assert E.edit_ops("", "xy") == (0, 2, 0)


def test_breakdown_by_tags_and_composition() -> None:
    refs = {"p:000": "Hochgeehrter Herr", "p:001": "vnd daß", "q:000": "zu Hannover"}
    hyps = {"p:000": "Hochgeehrter Herr", "p:001": "vnd das", "q:000": "zu Hanover"}
    tags = {
        "p:000": {
            "stratum": "heavy_revision",
            "group": "leibniz",
            "reader": "trocr",
            "hand": "own",
        },
        "p:001": {
            "stratum": "heavy_revision",
            "group": "leibniz",
            "reader": "trocr",
            "hand": "own",
        },
        "q:000": {"stratum": "light_revision", "group": "other", "reader": "v1", "hand": "other"},
    }
    scored = E.score_with_ops(refs, hyps)
    b = E.breakdown(scored, tags)
    assert b["overall"]["lines"] == 3 and b["overall"]["exact"] == 1
    assert b["overall"]["edits"] == 2 and b["overall"]["sub"] == 1 and b["overall"]["del"] == 1
    assert b["by"]["group"]["leibniz"]["lines"] == 2 and b["by"]["reader"]["v1"]["lines"] == 1
    assert abs(b["by"]["group"]["other"]["cer"] - 1 / len("zu Hannover")) < 1e-9
    ci = E.bootstrap(scored, n_resamples=50)
    assert ci["n"] == 3 and ci["cer_lo"] <= ci["cer"] <= ci["cer_hi"]
    worst = E.worst_lines(scored, n=2)
    assert worst[0]["line_id"] == "p:001"


def test_normalization_tax_vanishes_under_the_fold() -> None:
    refs = {"a": "Jch habe & bin"}
    hyps = {"a": "Ich habe et bin"}  # the edition's conventions against a diplomatic reading
    t = E.normalization_tax(refs, hyps)
    assert t["cer_policy"] > 0 and t["cer_folded"] == 0.0 and abs(t["tax"] - t["cer_policy"]) < 1e-9


def test_manifest_tags_and_disagreements() -> None:
    rows = [
        {
            "split": "val",
            "image": "val/p/000.png",
            "page_id": "p",
            "line_seq": 0,
            "text": "abc",
            "stratum": "scrap",
            "group": "other",
            "reader": "v1",
            "hand": "other",
        },
        {"split": "train", "image": "train/p/001.png", "page_id": "p", "line_seq": 1, "text": "x"},
        {"split": "val", "image": "", "page_id": "p", "line_seq": 2, "text": "y"},
    ]
    tags = E.manifest_tags(rows)
    assert list(tags) == ["p:000"] and tags["p:000"]["stratum"] == "scrap"
    refs = E.refs_from_tags(tags)
    d = E.disagreements(refs, {"p:000": "abc"}, {"p:000": "abd"})
    assert d["disagree"] == 1 and d["a_exact"] == 1 and d["either_share"] == 1.0
    assert E.disagreements(refs, {"p:000": "abd"}, {"p:000": "abd"})["disagree"] == 0
