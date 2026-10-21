"""``leibniz pack judgments`` (Phase G1): the game's converged judgments as new
'corrected' lines beside the machine rows, idempotent on (line, decided_at);
the both-rejected lines as the Scriptorium queue — on the fixture store's
German rows and the fixture judgment pack (tests/fixtures/pack/judgments.jsonl)."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from leibniz.align.audit_reach import open_readonly
from leibniz.cli import app
from leibniz.pack import check as C
from leibniz.pack import fragments as F
from leibniz.pack import judgments as J
from leibniz.search.documents import latest_lines

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "pack"
JUDGMENTS = FIXTURES / "judgments.jsonl"
W3 = "00069377"
GAME_MODEL = "crowd_ab_v1@9f3c2e1"
runner = CliRunner()


@pytest.fixture
def fragment_pack(german_store_path: Path, tmp_path: Path) -> Path:
    """The fragment pack the fixture judgments answer (every gold rule on)."""
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
    return F.write_pack(tmp_path / "fragments.jsonl", pack)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _machine_rows(store: Path) -> list[tuple]:
    conn = open_readonly(store)
    rows = conn.execute(
        "SELECT id, line_id, run_id, text, conf, model, baseline, polygon, lang, source "
        "FROM lines WHERE status = 'machine' ORDER BY id"
    ).fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def _invoke(store: Path, queue: Path, *extra: str):
    return runner.invoke(
        app,
        ["pack", "judgments", "--in", str(JUDGMENTS), "--db", str(store), "--queue", str(queue)]
        + list(extra),
    )


def _plan(store: Path, fragments: dict | None = None, path: Path = JUDGMENTS) -> J.ImportPlan:
    conn = open_readonly(store)
    try:
        return J.plan_import(conn, C.check_judgment_pack(path), fragments=fragments)
    finally:
        conn.close()


def test_the_fixture_winners_are_the_packs_candidates() -> None:
    rows = [json.loads(x) for x in JUDGMENTS.read_text(encoding="utf-8").splitlines()[1:]]
    for row in rows:
        if row["retirement"] == "converged" and row["line_id"].startswith(W3):
            assert row["winning_cand_id"] == F.cand_id(
                row["line_id"], row["winning_source"], row["winning_text"]
            )


def test_the_dry_run_writes_nothing(german_store_path: Path, tmp_path: Path) -> None:
    before = _sha(german_store_path)
    queue = tmp_path / "queue.md"
    res = _invoke(german_store_path, queue)
    assert res.exit_code == 0, res.output
    assert _sha(german_store_path) == before
    for want in (
        "4 rows — converged 3, both_rejected 1",
        "Converged: 2 to import as 'corrected' lines",
        "skipped no_machine_row",
        "Both rejected: 1 line for the Scriptorium queue",
        "Dry run: the store was opened read-only",
        "No fragment pack given",
    ):
        assert want in res.output, want
    text = queue.read_text(encoding="utf-8")
    assert f"`{W3}:0001:001`" in text  # the both_rejected line
    assert "die Sache wegen der Müntze (`htr_best`) | —" in text  # without the pack: v1 only


def test_write_imports_converged_rows_beside_the_machine_rows(
    german_store_path: Path, fragment_pack: Path, tmp_path: Path
) -> None:
    machine_before = _machine_rows(german_store_path)
    res = _invoke(
        german_store_path, tmp_path / "q.md", "--write", "--fragments", str(fragment_pack)
    )
    assert res.exit_code == 0, res.output
    assert "Wrote 2 rows under run" in res.output
    assert _machine_rows(german_store_path) == machine_before  # never updated, never deleted
    conn = open_readonly(german_store_path)
    run = conn.execute("SELECT * FROM runs WHERE stage = 'crowd'").fetchall()
    assert len(run) == 1
    assert (run[0]["model"], run[0]["n_input"], run[0]["n_ok"], run[0]["n_failed"]) == (
        GAME_MODEL,
        3,
        2,
        1,
    )
    params = json.loads(run[0]["params"])
    assert params["judgment_pack"] == "calc-judgments-2026-11-05-01"
    assert params["fragment_pack"].startswith("ll-fragments-2026-10-22-")
    rows = conn.execute(
        "SELECT * FROM lines WHERE status = 'corrected' ORDER BY line_id"
    ).fetchall()
    assert [r["line_id"] for r in rows] == [f"{W3}:0001:000", f"{W3}:0002:001"]
    raw = JUDGMENTS.read_text(encoding="utf-8").splitlines()
    first = rows[0]
    assert first["text"] == "Ich habe Ew. Excellenz Schreiben erhalten"
    assert (first["conf"], first["model"], first["run_id"]) == (0.97, GAME_MODEL, run[0]["run_id"])
    assert first["source"] == raw[1]  # the judgment row verbatim
    assert first["lang"] == "de"
    machine = conn.execute(
        "SELECT baseline, polygon FROM lines WHERE line_id = ? AND status = 'machine'",
        (f"{W3}:0001:000",),
    ).fetchone()
    assert (first["baseline"], first["polygon"]) == (machine["baseline"], machine["polygon"])
    # the line now reads as the crowd decided, with its status and provenance
    shown = latest_lines(conn, f"{W3}:0001")[0]
    assert (shown.text, shown.status, shown.model) == (first["text"], "corrected", GAME_MODEL)
    assert shown.source["contributors"][0]["id_opaque"] == "p-7f2a"
    conn.close()


def test_the_import_is_idempotent(german_store_path: Path, tmp_path: Path) -> None:
    assert _invoke(german_store_path, tmp_path / "q.md", "--write").exit_code == 0
    after_first = _sha(german_store_path)
    res = _invoke(german_store_path, tmp_path / "q.md", "--write")
    assert res.exit_code == 0, res.output
    assert "skipped already_imported" in res.output
    assert "Nothing to write: no run opened" in res.output
    conn = open_readonly(german_store_path)
    assert conn.execute("SELECT COUNT(*) FROM runs WHERE stage = 'crowd'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM lines WHERE status = 'corrected'").fetchone()[0] == 2
    conn.close()
    assert _sha(german_store_path) == after_first
    plan = _plan(german_store_path)
    assert plan.skipped["already_imported"] == 2 and not plan.to_insert


def test_a_new_decision_for_a_judged_line_is_imported(
    german_store_path: Path, tmp_path: Path
) -> None:
    assert _invoke(german_store_path, tmp_path / "q.md", "--write").exit_code == 0
    rows = JUDGMENTS.read_text(encoding="utf-8").splitlines()
    later = json.loads(rows[1])
    later["decided_at"] = "2026-12-01T09:00:00Z"
    path = tmp_path / "later.jsonl"
    path.write_text(rows[0] + "\n" + json.dumps(later, ensure_ascii=False) + "\n", "utf-8")
    plan = _plan(german_store_path, path=path)
    assert [n.line_id for n in plan.to_insert] == [f"{W3}:0001:000"]


def test_in_pack_duplicates_keep_the_latest(german_store_path: Path, tmp_path: Path) -> None:
    rows = JUDGMENTS.read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[1])
    later = dict(first, decided_at="2026-11-06T00:00:00Z", posterior=0.99)
    objs = [json.loads(rows[0]), first, first, later]
    path = tmp_path / "dups.jsonl"
    path.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in objs), "utf-8")
    plan = _plan(german_store_path, path=path)
    assert [(n.line_id, n.conf) for n in plan.to_insert] == [(f"{W3}:0001:000", 0.99)]
    assert (plan.skipped["duplicate_in_pack"], plan.skipped["superseded_in_pack"]) == (1, 1)


def test_winners_are_checked_against_the_fragment_pack(
    german_store_path: Path, fragment_pack: Path
) -> None:
    frags = {r["line_id"]: r for r in C.check_fragment_pack(fragment_pack).rows}
    plan = _plan(german_store_path, frags)
    assert dict(plan.skipped) == {"no_machine_row": 1}  # the line the store lacks, only
    assert len(plan.to_insert) == 2
    other = dict(frags)
    row = dict(other[f"{W3}:0001:000"])
    row["candidates"] = [dict(c, text=c["text"] + " ?") for c in row["candidates"]]
    other[f"{W3}:0001:000"] = row
    assert _plan(german_store_path, other).skipped["winner_text_differs"] == 1
    row = dict(row, candidates=[dict(c, cand_id="c-else") for c in row["candidates"]])
    other[f"{W3}:0001:000"] = row
    assert _plan(german_store_path, other).skipped["winner_not_a_candidate"] == 1
    del other[f"{W3}:0001:000"]
    assert _plan(german_store_path, other).skipped["not_in_fragment_pack"] == 1


def test_a_pack_that_does_not_check_is_refused(german_store_path: Path, tmp_path: Path) -> None:
    rows = JUDGMENTS.read_text(encoding="utf-8").splitlines()
    bad = json.loads(rows[2])
    bad["retirement"] = "maybe"
    path = tmp_path / "bad.jsonl"
    path.write_text("\n".join([rows[0], rows[1], json.dumps(bad)]) + "\n", "utf-8")
    before = _sha(german_store_path)
    queue = tmp_path / "q.md"
    res = runner.invoke(
        app,
        [
            "pack",
            "judgments",
            "--in",
            str(path),
            "--db",
            str(german_store_path),
            "--queue",
            str(queue),
            "--write",
        ],
    )
    assert res.exit_code == 1
    assert "Refused: nothing was read from the pack." in res.output
    assert _sha(german_store_path) == before and not queue.exists()
    with pytest.raises(ValueError, match="does not check"):
        _plan(german_store_path, path=path)


def test_the_queue_has_one_section_per_pack(
    german_store_path: Path, fragment_pack: Path, tmp_path: Path
) -> None:
    queue = tmp_path / "scriptorium-queue.md"
    for _ in range(2):  # the same pack twice: one section
        res = _invoke(german_store_path, queue, "--fragments", str(fragment_pack))
        assert res.exit_code == 0, res.output
    text = queue.read_text(encoding="utf-8")
    assert text.startswith(J.QUEUE_HEAD)
    assert text.count("<!-- pack:calc-judgments-2026-11-05-01 -->") == 1
    row = next(x for x in text.splitlines() if x.startswith(f"| `{W3}:0001:001`"))
    # the line, its page, the two readings, the posterior, the date
    assert f"[`{W3}:0001`](https://leibnizlegible.com/page/{W3}:0001) LH XXIII, 2, fol. 1r" in row
    assert "die Sache wegen der Münze (`model_alt`)" in row
    assert "die Sache wegen der Müntze (`htr_best`)" in row
    assert "| 0.880 | 2026-11-05T08:13:30Z |" in row
    # another pack adds its section after the first, which stays as it was
    rows = JUDGMENTS.read_text(encoding="utf-8").splitlines()
    head = json.loads(rows[0])
    head["pack_id"] = "calc-judgments-2026-12-01-01"
    other = tmp_path / "other.jsonl"
    other.write_text(json.dumps(head) + "\n" + rows[1] + "\n", "utf-8")
    res = runner.invoke(
        app,
        [
            "pack",
            "judgments",
            "--in",
            str(other),
            "--db",
            str(german_store_path),
            "--queue",
            str(queue),
        ],
    )
    assert res.exit_code == 0, res.output
    again = queue.read_text(encoding="utf-8")
    assert again.index("calc-judgments-2026-11-05-01") < again.index("calc-judgments-2026-12-01-01")
    assert row in again
    assert "No line of this pack was rejected both ways." in again


def test_md_cell() -> None:
    assert J.md_cell("a | b <i>\n*c*_d_ [e]`f`") == (
        "a \\| b &lt;i&gt; \\*c\\*\\_d\\_ \\[e\\]\\`f\\`"
    )


def test_specs_records_the_seam() -> None:
    specs = (ROOT / "SPECS.md").read_text(encoding="utf-8")
    section = specs[specs.index("## 11. Out of scope") :]
    for want in (
        "leibniz pack fragments",
        "leibniz pack check",
        "leibniz pack judgments",
        "src/leibniz/pack/fragment_pack.schema.json",
        "src/leibniz/pack/judgment_pack.schema.json",
        "Calculemus SPECS §6.6",
    ):
        assert want in section, want
    assert C.FRAGMENT_SCHEMA.exists() and C.JUDGMENT_SCHEMA.exists()
