"""``leibniz pack check`` (Phase G1): a pack against the contract — the schema
(header, keys, enums, 'open' only, two candidates) and the rules it cannot say
(gold consistency, distinct candidates, each line once) — and the validator's
own refusal of schema keywords it does not enforce."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz.align.audit_reach import open_readonly
from leibniz.cli import app
from leibniz.pack import check as C
from leibniz.pack import fragments as F

FIXTURES = Path(__file__).parent / "fixtures" / "pack"
runner = CliRunner()


@pytest.fixture
def good_pack(german_store_path: Path, tmp_path: Path) -> Path:
    conn = open_readonly(german_store_path)
    try:
        pack = F.build_pack(
            conn,
            F.load_pieces(FIXTURES / "german_pieces.jsonl"),
            F.load_readings(FIXTURES / "trocr-kurrent-xvi-xvii.jsonl"),
            today=date(2026, 10, 22),
            gold_rate=1.0,
            bad_gold_share=0.5,
        )
    finally:
        conn.close()
    return F.write_pack(tmp_path / "good.jsonl", pack)


def _lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def _write(path: Path, objs: list) -> Path:
    path.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in objs), "utf-8")
    return path


def _doctor(good: Path, tmp_path: Path, change) -> C.CheckReport:
    objs = _lines(good)
    change(objs)
    return C.check_fragment_pack(_write(tmp_path / "doctored.jsonl", objs))


def test_the_schemas_load_and_use_only_enforced_keywords() -> None:
    for path in (C.FRAGMENT_SCHEMA, C.JUDGMENT_SCHEMA):
        schema = C.load_schema(path)
        assert {"header", "row"} <= set(schema["$defs"])
    with pytest.raises(C.SchemaError, match="pattern"):
        C.assert_supported({"type": "string", "pattern": "^a"})
    with pytest.raises(C.SchemaError, match="local references"):
        C.assert_supported({"$ref": "https://example.org/x.json"})


def test_the_validator() -> None:
    schema = {
        "$defs": {"n": {"type": "integer", "minimum": 0}},
        "type": "object",
        "additionalProperties": False,
        "required": ["a", "b"],
        "properties": {
            "a": {"$ref": "#/$defs/n"},
            "b": {"enum": ["x", "y"]},
            "c": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string"}},
            "d": {"const": 1},
            "e": {"type": "number", "maximum": 1},
        },
    }
    assert C.validate({"a": 0, "b": "x", "c": ["s"], "d": 1, "e": 0.5}, schema) == []
    errs = C.validate({"a": -1, "b": "z", "c": [], "d": True, "e": 2, "f": 0}, schema)
    assert errs == [
        "$: unexpected key 'f'",
        "$.a: -1 is under the minimum 0",
        '$.b: must be one of "x", "y", got "z"',
        "$.c: 0 item(s), at least 1 wanted",
        "$.d: must be 1, got true",  # JSON true is not 1
        "$.e: 2 is over the maximum 1",
    ]
    assert C.validate({"b": "x", "a": True}, schema) == ["$.a: expected integer, got boolean true"]
    assert C.validate({"a": 1}, schema) == ["$: missing 'b'"]


def test_a_good_pack_passes(good_pack: Path) -> None:
    report = C.check_fragment_pack(good_pack)
    assert report.ok, report.errors
    assert len(report.rows) == 5
    assert (
        report.counts["gold"],
        report.counts["gold truth"],
        report.counts["gold both_wrong"],
    ) == (
        3,
        2,
        1,
    )
    text = "\n".join(C.report_lines(report))
    assert "OK — fragment pack, schema_version 1" in text
    assert "rows 5; gold 3 (truth 2, both wrong 1)" in text


def test_a_doctored_nc_row_fails(good_pack: Path, tmp_path: Path) -> None:
    def to_nc(objs: list) -> None:
        objs[2]["license_bucket"] = "nc"

    report = _doctor(good_pack, tmp_path, to_nc)
    assert not report.ok
    assert report.errors == ['line 3: $.license_bucket: must be "open", got "nc"']
    res = runner.invoke(app, ["pack", "check", str(tmp_path / "doctored.jsonl")])
    assert res.exit_code == 1
    assert "FAILED — 1 error(s) in 5 row(s)" in res.output
    assert "license_bucket" in res.output


@pytest.mark.parametrize(
    ("change", "want"),
    [
        (
            lambda o: o[1]["candidates"].append(dict(o[1]["candidates"][0], cand_id="c-x")),
            "3 item(s), at most 2 allowed",
        ),
        (lambda o: o[1]["candidates"].pop(), "1 item(s), at least 2 wanted"),
        (
            lambda o: o[1]["candidates"][1].update(cand_id=o[1]["candidates"][0]["cand_id"]),
            "the cand_ids repeat",
        ),
        (
            lambda o: o[1]["candidates"][1].update(text=" " + o[1]["candidates"][0]["text"] + " "),
            "the same after whitespace normalisation",
        ),
        (
            lambda o: o[1]["gold"].update(truth_cand_id="c-nowhere"),  # row 1 is a gold row
            "is not one of the candidates",
        ),
        (
            lambda o: o[1]["gold"].update(both_wrong=True),  # … with a truth already
            "exactly one of truth_cand_id | both_wrong: true",
        ),
        (lambda o: o[1]["gold"].pop("truth_cand_id"), "exactly one of truth_cand_id"),
        (
            lambda o: o[3].update(gold={"is_gold": False, "both_wrong": True}),
            "is_gold is false but the row names",
        ),
        (lambda o: o[1].update(n_chars=1), "the longer candidate has"),
        (lambda o: o[1]["image"].pop("page_image_url"), "a static image needs page_image_url"),
        (lambda o: o[1]["candidates"][0].update(source="guess"), "must be one of"),
        (lambda o: o[1].update(extra=1), "unexpected key 'extra'"),
        (lambda o: o[1]["provenance"].pop("model"), "missing 'model'"),
        (lambda o: o[2].update(line_id=o[1]["line_id"]), 'line_id "00069377:0001:000" again'),
        (lambda o: o[0].update(schema_version=2), "$.schema_version: must be 1, got 2"),
        (lambda o: o[1].update(line_id="00069377:1:0"), "is not a line id"),
        (lambda o: o[1].update(page_id="00069377:0002"), "not the page and work of"),
        (lambda o: o.pop(0), "the first line must be the header"),
        (lambda o: o.append(o[0]), "a second header"),
    ],
)
def test_contract_violations_fail(good_pack: Path, tmp_path: Path, change, want: str) -> None:
    report = _doctor(good_pack, tmp_path, change)
    assert not report.ok
    assert any(want in e for e in report.errors), report.errors


def test_the_good_pack_rows_are_as_the_fixture_says(good_pack: Path) -> None:
    rows = _lines(good_pack)[1:]
    gold = [r for r in rows if r["gold"]["is_gold"]]
    assert rows[0]["line_id"] == "00069377:0001:000" and rows[0]["gold"]["is_gold"]
    assert len(gold) == 3


def test_nan_blank_lines_and_empty_files_fail(good_pack: Path, tmp_path: Path) -> None:
    raw = good_pack.read_text(encoding="utf-8").splitlines()
    raw[1] = raw[1].replace('"machine_conf": 0.62', '"machine_conf": NaN')
    bad = tmp_path / "nan.jsonl"
    bad.write_text("\n".join(raw) + "\n", encoding="utf-8")
    report = C.check_fragment_pack(bad)
    assert any("not JSON: NaN is not JSON" in e for e in report.errors)
    blank = tmp_path / "blank.jsonl"
    blank.write_text(raw[0] + "\n\n", encoding="utf-8")
    assert any("blank line" in e for e in C.check_fragment_pack(blank).errors)
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    assert not C.check_fragment_pack(empty).ok


def test_judgment_packs_are_checked_too(tmp_path: Path) -> None:
    good = FIXTURES / "judgments.jsonl"
    report = C.check_judgment_pack(good)
    assert report.ok, report.errors
    assert (report.counts["converged"], report.counts["both_rejected"]) == (3, 1)
    res = runner.invoke(app, ["pack", "check", "--judgments", str(good)])
    assert res.exit_code == 0, res.output
    objs = _lines(good)
    objs[1].pop("winning_text")  # a converged row without its winner
    objs[4]["winning_text"] = "x"  # a both_rejected row with one
    objs[2]["method"] = "majority"
    objs[3]["line_id"] = "nowhere"  # the import splits it into page and line
    report = C.check_judgment_pack(_write(tmp_path / "bad.jsonl", objs))
    assert not report.ok
    text = "\n".join(report.errors)
    assert "a converged row needs winning_text" in text
    assert "a both_rejected row names a winner (winning_text)" in text
    assert '$.method: must be "crowd_ab_v1"' in text
    assert '"nowhere" is not a line id' in text
