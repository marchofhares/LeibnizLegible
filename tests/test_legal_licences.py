"""The licence registry (Phase L1): every entry dated and licensed, the nc rule of
``align/pairs.py`` and the factory's channels in agreement with it, the outputs
table behind every public surface, and ``leibniz legal`` on the terminal."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz import legal
from leibniz.align import pairs
from leibniz.align.volumes_sources import CHANNEL_TERMS
from leibniz.cli import app
from leibniz.db import LICENSE_BUCKETS

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()

# The entries the L1 prompt names, by key.
REQUIRED = {
    "philiumm-htr-model",
    "philiumm-seg-model",
    "philiumm-dataset",
    "philiumm-code",
    "fondue-gd-base",
    "mccatmus",
    "trocr-kurrent-xvi-xvii",
    "trocr-kurrent-xix",
    "trocr-hanse-xvii",
    "trocr-hanse-xvi",
    "dresden-1673",
    "dresden-1673-tei",
    "dresden-1665",
    "bullinger-htr",
    "gwlb-images",
    "arbeitskatalog",
    "bodemann-correspsearch",
    "kalliope",
    "letterpool",
    "edition-ia",
    "edition-gwlb",
    "edition-potsdam",
    "edition-muenster",
    "reihe-viii-tei",
    "hme-leibniz",
    "gallicorpora-plus",
    "yaltai",
    "dfine-kraken",
    "ultralytics-yolo",
    "nantes-hmer",
    "ppocr-v6",
}


def test_every_entry_has_a_licence_string_and_a_date() -> None:
    assert REQUIRED <= set(legal.ARTIFACTS), REQUIRED - set(legal.ARTIFACTS)
    keys = [a.key for a in legal.LICENCES]
    assert len(keys) == len(set(keys))
    for a in legal.LICENCES:
        assert a.name and a.source and a.version and a.built, a.key
        assert isinstance(a.obtained.licence, str) and a.obtained.licence.strip(), a.key
        assert isinstance(a.obtained.seen, date) and a.obtained.seen <= legal.REGISTRY_DATE, a.key
        if a.current is not None:
            assert a.current.licence.strip() and isinstance(a.current.seen, date), a.key
            assert a.obtained.seen <= a.current.seen <= legal.REGISTRY_DATE, a.key
            if a.current.since is not None:
                assert a.current.since <= a.current.seen, a.key
        assert a.bucket in legal.BUCKETS, a.key
        # a deposit is a property of an edition channel, nothing else
        assert (a.deposit is None) or (a.channel is not None), a.key
        # nothing built from it ⇒ bucket none; an nc entry never feeds the open deposit
        if not a.used:
            assert a.bucket in ("none", "nc", "open"), a.key
        if a.bucket == "nc":
            assert a.deposit != "open", a.key


def test_the_philiumm_relicensing_is_recorded_as_a_change_with_dates() -> None:
    for key in ("philiumm-htr-model", "philiumm-seg-model"):
        a = legal.artifact(key)
        assert a.obtained.licence == "CC BY 4.0" and a.obtained.seen == date(2026, 7, 29)
        assert a.changed and a.licence_now.licence == "CC BY-NC 4.0"
        assert a.current is not None and a.current.since == date(2026, 10, 15)
        assert a.current.seen == date(2026, 10, 21)
        assert a.bucket == "open"  # the machine output stays CC BY
    ds = legal.artifact("philiumm-dataset")
    assert not ds.changed and ds.licence_now.licence == "CC BY 4.0"
    # the Arbeitskatalog and the Potsdam channel carry the statement in writing
    for key, lic in (("arbeitskatalog", "CC BY 4.0"), ("edition-potsdam", "CC BY-NC 4.0")):
        a = legal.artifact(key)
        assert a.current is not None and a.current.licence.startswith(lic), key
        assert "2026-10-12" in a.current.licence and a.current.since == date(2026, 10, 12)
    # the Göttingen series stay as obtained, with a dated ask
    gwlb = legal.artifact("edition-gwlb")
    assert gwlb.current is None and gwlb.obtained.licence == "CC BY-NC 4.0"
    assert "Göttingen" in gwlb.asked and "2026-10-21" in gwlb.asked
    # the tools run beside the repository: nothing imported, nothing derived
    for key in ("gallicorpora-plus", "yaltai", "dfine-kraken", "ultralytics-yolo", "nantes-hmer"):
        a = legal.artifact(key)
        assert a.kind == "tool" and a.bucket == "none" and not a.used, key
    assert "GPL-3.0" in legal.artifact("yaltai").obtained.licence
    assert "AGPL-3.0" in legal.artifact("ultralytics-yolo").obtained.licence
    pool = legal.artifact("letterpool")
    assert pool.bucket == "nc" and pool.deposit is None and "evaluation only" in pool.built
    assert legal.artifact("kalliope").obtained.licence == "none stated"
    assert "CC BY-SA 4.0" == legal.artifact("bullinger-htr").obtained.licence


def test_the_nc_rule_in_pairs_agrees_with_the_registry() -> None:
    """``GtPair`` admits the buckets the registry's open and nc entries name; the
    factory's default bucket (``open``) is what the registry says for every edition
    channel whose text is §70-free; the letter pool is nc and never released."""
    assert set(LICENSE_BUCKETS) == {"open", "nc"}
    assert {a.bucket for a in legal.LICENCES} - {"none"} <= set(LICENSE_BUCKETS)
    with pytest.raises(ValueError):
        pairs.GtPair("P:0001:000", "x", "src", "fair_copy", 0.9, "none")
    for key in ("edition-ia", "edition-gwlb", "edition-potsdam"):
        a = legal.artifact(key)
        assert a.bucket == "open", key  # §70-free reading text: the factory's gate
        assert a.channel in legal.CHANNELS
    assert legal.artifact("letterpool").bucket == "nc"
    # every channel the factory can write is known to the registry
    assert set(CHANNEL_TERMS) - {"none"} <= set(legal.CHANNELS)
    # the deposit each channel leads to
    assert legal.CHANNELS["ia"].deposit == "open"
    assert legal.CHANNELS["gwlb"].deposit == "nc"
    assert legal.CHANNELS["potsdam"].deposit == "nc"
    assert legal.CHANNELS["muenster"].deposit is None
    assert legal.CHANNELS["letterpool"].deposit is None


@pytest.mark.parametrize(
    ("source", "bucket", "deposit"),
    [
        ("AA I,9 N.12 (§70-expired AA reading text; channel ia; katalog 4711)", "open", "open"),
        ("AA IV,1 N.3 (§70-expired AA reading text; channel potsdam; katalog 1)", "open", "nc"),
        ("AA I,3 N.7 (§70-expired AA reading text; channel gwlb; katalog 2)", "open", "nc"),
        ("AA I,9 N.12 (§70-expired AA reading text; channel ia+gwlb; katalog 3)", "open", "nc"),
        (
            "AA I,3 N.7 (§70-expired AA reading text; channel ia; "
            "reader trocr-kurrent-xvi-xvii; katalog R7)",
            "open",
            "open",
        ),
        ("AA VI,4 N.109", "open", "open"),  # minted before the channel was recorded
        ("AA VI,4 N.109", "nc", None),
        ("letter 1714 N.12 (Transkriptionspool; channel letterpool)", "nc", None),
        ("AA II,1 N.1 (channel muenster; katalog 9)", "open", None),
        ("AA II,1 N.1 (channel unknown-key; katalog 9)", "open", None),
    ],
)
def test_deposit_follows_the_channel(source: str, bucket: str, deposit: str | None) -> None:
    assert legal.deposit_for(pairs.channels_from_source(source), bucket) == deposit


def test_channels_from_source() -> None:
    assert pairs.channels_from_source("x (channel ia; katalog 1)") == ("ia",)
    assert pairs.channels_from_source("x (…; channel ia+gwlb; reader r; katalog 1)") == (
        "ia",
        "gwlb",
    )
    assert pairs.channels_from_source("AA VI,4 N.109") == ()
    assert pairs.channels_from_source(None) == ()


def test_the_outputs_table_matches_the_owners_scheme() -> None:
    assert legal.output("code").licence == "Apache-2.0"
    assert legal.output("transcriptions").licence == "CC BY 4.0"
    assert legal.deposit_licence("open") == "CC BY 4.0"
    assert legal.deposit_licence("nc") == "CC BY-NC 4.0"
    assert legal.output("model-v2").licence == "CC BY-NC 4.0"
    assert legal.output("model-k3-trocr").licence.startswith("CC BY 4.0")
    assert legal.output("model-k3-ppocr").licence.startswith("CC BY 4.0")
    assert "obtained under CC BY 4.0" in legal.output("transcriptions").why
    # K4: READER and its readings (the amendment of 2026-10-26)
    assert legal.output("readings-de").licence == "CC BY 4.0"
    assert "READER" in legal.output("model-k3-trocr").name
    assert "I agree to go with TrOCR." in legal.output("model-k3-trocr").decided
    readers = legal.site_readers()
    assert readers["v1"]["readings_licence"] == "CC BY 4.0"
    assert readers["v1"]["model_licence"] == "CC BY-NC 4.0"  # the relicensing of 2026-10-15
    assert readers["v1"]["model_licence_obtained"] == "CC BY 4.0"
    assert readers["de"] == {
        "reader": "k3-trocr",
        "version": "k3-trocr@runs-615-epoch-5",
        "model": legal.output("model-k3-trocr").name,
        "model_licence": "CC BY 4.0",
        "base": legal.artifact("trocr-kurrent-xvi-xvii").name,
        "base_licence": "MIT",
        "readings_licence": "CC BY 4.0",
        "output": "readings-de",
    }
    for o in legal.OUTPUTS:
        assert o.why and o.decided, o.key
        assert set(o.inputs) <= set(legal.ARTIFACTS), o.key
    # the code's licence is the one pyproject declares
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = { text = "Apache-2.0" }' in pyproject


def test_legal_licences_command_prints_the_table() -> None:
    res = runner.invoke(app, ["legal", "licences", "--format", "tsv"])
    assert res.exit_code == 0, res.output
    lines = res.stdout.splitlines()
    assert lines[0].split("\t") == list(legal.LICENCE_COLUMNS)
    keys = {line.split("\t")[0] for line in lines[1:]}
    assert keys == set(legal.ARTIFACTS)
    row = next(line for line in lines if line.startswith("philiumm-htr-model\t")).split("\t")
    assert row[5] == "CC BY 4.0" and row[6] == "2026-07-29"
    assert row[7] == "CC BY-NC 4.0" and row[8] == "2026-10-21"

    res = runner.invoke(app, ["legal", "licences"])
    assert res.exit_code == 0 and "Third-party artifacts" in res.stdout

    res = runner.invoke(app, ["legal", "licences", "--format", "json", "--key", "letterpool"])
    assert res.exit_code == 0
    (row_j,) = json.loads(res.stdout)
    assert row_j["key"] == "letterpool" and row_j["bucket"] == "nc"

    res = runner.invoke(app, ["legal", "licences", "--key", "nope"])
    assert res.exit_code != 0

    res = runner.invoke(app, ["legal", "outputs", "--format", "tsv"])
    assert res.exit_code == 0 and "model-v2\t" in res.stdout and "CC BY-NC 4.0" in res.stdout

    res = runner.invoke(app, ["legal", "volumes", "--today", "2026-12-31", "--format", "tsv"])
    assert res.exit_code == 0
    assert re.search(r"^I,17\t2001\t2027-01-01\tno", res.stdout, flags=re.M)
    assert re.search(r"^I,16\t2000\t2026-01-01\tyes", res.stdout, flags=re.M)


def test_the_release_checklist_carries_the_lawyer_memo_questions() -> None:
    memo = (ROOT / "reports" / "release-checklist.md").read_text(encoding="utf-8")
    assert "Lawyer memo" in memo
    for needle in (
        "irrevocab",  # CC BY 4.0 §2(a)(1) for copies already obtained
        "weights licence",  # the status of model output
        "ShareAlike",  # Bullinger, from K1
        "§ 70",  # NC terms on a PDF reaching §70-free text
        "Potsdam",  # redistribution of lines derived from the Potsdam PDFs
        "§ 71",  # the first-publication right
        "AGPL",  # data produced by GPL/AGPL tools beside an Apache-2.0 codebase
    ):
        assert needle in memo, needle


def test_specs_says_what_the_registry_says() -> None:
    specs = (ROOT / "SPECS.md").read_text(encoding="utf-8")
    assert "released separately under CC BY-NC" in specs
    assert "Amendment of 2026-10-21" in specs
    d4 = next(line for line in specs.splitlines() if line.startswith("| D4 "))
    assert legal.output("model-v2").licence in d4
