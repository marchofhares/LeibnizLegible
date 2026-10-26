"""What reading a mixed page whole with the Kurrent reader costs (K4, Task 2).

Scribes switched script with language — German in Kurrent, Latin and French in
a Latin hand, often on one page — and K4 reads every German page whole with
READER, the Latin and French passages on it included. The letter pool (K2b's
frozen set) is the one place where that cost can be measured: every letter is
scored for v1 and for K3's readers by the same metric
(``reports/kurrent/k3-letterpool/letterpool-eval-letters.csv``, one row per
letter, reader and policy), and the letter's reference text says how much of
it is not German. A letter is *mixed* when the stopword identifier
(:mod:`leibniz.enrich.langid`) calls its reference text ``mixed`` or gives
Latin and French together at least :data:`leibniz.enrich.langid.MIXED_SHARE`
of its stopword hits; the rest are the German letters. Per group and reader
the pooled CER (edits over reference characters) and the per-letter median;
the cost is READER's gain over v1 on the mixed letters against its gain on
the German ones. A letter-level measure: the pool has no per-line reference,
so a per-line choice between the readings stays an open question. Numbers
only leave this module; the pool's text does not (SPECS §1.4, §7.3).
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz.enrich.langid import MIXED_SHARE, classify

DEFAULT_LETTERS_CSV = Path("reports/kurrent/k3-letterpool/letterpool-eval-letters.csv")
DEFAULT_TESTSET = Path("data/kurrent/letterpool/testset.jsonl")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
DEFAULT_READERS: tuple[str, ...] = ("v1", "k3-trocr")
DEFAULT_POLICY = "philiumm"
GROUPS: tuple[str, ...] = ("mixed", "german")


@dataclass(slots=True)
class LetterMix:
    """One letter's reference text as the identifier reads it."""

    letter_id: str
    lang: str
    lafr_share: float  # Latin and French hits over all stopword hits
    n_tokens: int
    hits: dict[str, int] = field(default_factory=dict)

    @property
    def group(self) -> str:
        return "mixed" if self.lang == "mixed" or self.lafr_share >= MIXED_SHARE else "german"


def letter_mixes(texts: Mapping[str, str]) -> dict[str, LetterMix]:
    """Letter id → its mix, from the reference texts."""
    out: dict[str, LetterMix] = {}
    for letter_id, text in texts.items():
        r = classify(text)
        total = sum(r.hits.values())
        lafr = (r.hits.get("la", 0) + r.hits.get("fr", 0)) / total if total else 0.0
        out[letter_id] = LetterMix(letter_id, r.lang, round(lafr, 4), r.n_tokens, dict(r.hits))
    return out


def load_testset_texts(path: Path | str) -> dict[str, str]:
    """Letter id → reference text from the frozen set's JSONL."""
    out: dict[str, str] = {}
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                out[str(row["letter_id"])] = str(row.get("text") or "")
    return out


def load_letter_scores(
    path: Path | str, *, readers: Sequence[str] = DEFAULT_READERS, policy: str = DEFAULT_POLICY
) -> dict[str, dict[str, dict]]:
    """Reader → letter id → its row of the per-letter CSV, for one policy."""
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["policy"] == policy and row["reader"] in readers:
                out[row["reader"]][row["letter_id"]] = row
    return dict(out)


@dataclass(slots=True)
class GroupScore:
    group: str
    reader: str
    letters: int
    lines: int
    ref_chars: int
    edits: int
    median_cer: float | None

    @property
    def cer(self) -> float | None:
        return self.edits / self.ref_chars if self.ref_chars else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d["cer"] = None if self.cer is None else round(self.cer, 4)
        return d


def score_groups(
    scores: Mapping[str, Mapping[str, Mapping]], mixes: Mapping[str, LetterMix]
) -> list[GroupScore]:
    """The pooled CER per group and reader, the letters common to every reader."""
    readers = list(scores)
    common = set(mixes)
    for reader in readers:
        common &= set(scores[reader])
    out: list[GroupScore] = []
    for group in GROUPS:
        ids = sorted(lid for lid in common if mixes[lid].group == group)
        for reader in readers:
            rows = [scores[reader][lid] for lid in ids]
            cers = [float(r["cer"]) for r in rows]
            out.append(
                GroupScore(
                    group,
                    reader,
                    len(rows),
                    sum(int(r["n_lines"]) for r in rows),
                    sum(int(r["ref_chars"]) for r in rows),
                    sum(int(r["edits"]) for r in rows),
                    round(statistics.median(cers), 4) if cers else None,
                )
            )
    return out


def summary(
    groups: Sequence[GroupScore],
    mixes: Mapping[str, LetterMix],
    *,
    readers: Sequence[str],
    policy: str,
    letters_csv: Path | str,
) -> dict:
    by = {(g.group, g.reader): g for g in groups}
    base, reader = readers[0], readers[-1]
    gains = {}
    for group in GROUPS:
        a, b = by.get((group, base)), by.get((group, reader))
        if a and b and a.cer is not None and b.cer is not None:
            gains[group] = round(a.cer - b.cer, 4)
    shares = sorted(m.lafr_share for m in mixes.values())
    return {
        "letters_csv": str(letters_csv),
        "policy": policy,
        "readers": list(readers),
        "letters": len(mixes),
        "by_group": {g: sum(1 for m in mixes.values() if m.group == g) for g in GROUPS},
        "mixed_rule": f"the identifier says mixed, or Latin and French hold ≥ {MIXED_SHARE:g} "
        "of the stopword hits",
        "lafr_share_quartiles": (
            [shares[len(shares) // 4], shares[len(shares) // 2], shares[3 * len(shares) // 4]]
            if shares
            else []
        ),
        "scores": [g.as_dict() for g in groups],
        "gain": gains,  # the base reader's CER minus the last reader's, per group
        "cost": (
            round(gains["german"] - gains["mixed"], 4)
            if "german" in gains and "mixed" in gains
            else None
        ),
    }


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{d}f} %"


def render(summ: Mapping) -> str:
    L: list[str] = []
    a = L.append
    readers = summ["readers"]
    a("# What reading a mixed page whole costs: the letter pool's mixed letters")
    a("")
    a(
        f"K4 reads every German page whole with the Kurrent reader, Latin and French "
        f"passages included. On the letter pool ({summ['letters']} letters, `{summ['policy']}` "
        f"policy, the per-letter scores of `{summ['letters_csv']}`) a letter is *mixed* when "
        f"{summ['mixed_rule']} of its reference text: **{summ['by_group']['mixed']} mixed "
        f"letters, {summ['by_group']['german']} German ones**. The Latin-and-French share of "
        f"the hits over the letters: quartiles "
        + " / ".join(f"{q:.2f}" for q in summ["lafr_share_quartiles"])
        + "."
    )
    a("")
    a("| group | reader | letters | lines | reference chars | CER (pooled) | median letter CER |")
    a("|---|---|---:|---:|---:|---:|---:|")
    for s in summ["scores"]:
        a(
            f"| {s['group']} | {s['reader']} | {s['letters']} | {s['lines']:,} | "
            f"{s['ref_chars']:,} | {_pct(s['cer'])} | {_pct(s['median_cer'])} |"
        )
    a("")
    g = summ["gain"]
    a(
        f"**The gain of {readers[-1]} over {readers[0]}** (pooled CER, points): on the German "
        f"letters {_pct(g.get('german'))}, on the mixed letters {_pct(g.get('mixed'))}; the "
        f"cost of reading the mixed letters whole is the difference, "
        f"**{_pct(summ['cost'])}** of CER. A letter-level measure: the pool has no per-line "
        "reference text, so what a per-line choice between the two readings would recover is "
        "an open question (STATUS.md)."
    )
    a("")
    return "\n".join(L)


def write_reports(summ: Mapping, *, reports_dir: Path | str = DEFAULT_REPORTS_DIR) -> dict:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    md = reports_dir / "k4-mixed-letters.md"
    js = reports_dir / "k4-mixed-letters.json"
    md.write_text(render(summ), encoding="utf-8")
    js.write_text(json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"k4-mixed-letters.md": md, "k4-mixed-letters.json": js}


def run(
    *,
    letters_csv: Path | str = DEFAULT_LETTERS_CSV,
    testset: Path | str = DEFAULT_TESTSET,
    readers: Sequence[str] = DEFAULT_READERS,
    policy: str = DEFAULT_POLICY,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> tuple[dict, dict]:
    mixes = letter_mixes(load_testset_texts(testset))
    scores = load_letter_scores(letters_csv, readers=readers, policy=policy)
    missing = [r for r in readers if r not in scores]
    if missing:
        raise ValueError(
            f"no rows for reader(s) {missing} under policy {policy!r} in {letters_csv}"
        )
    groups = score_groups(scores, mixes)
    summ = summary(groups, mixes, readers=readers, policy=policy, letters_csv=letters_csv)
    return summ, write_reports(summ, reports_dir=reports_dir)


__all__ = [
    "DEFAULT_LETTERS_CSV",
    "DEFAULT_POLICY",
    "DEFAULT_READERS",
    "DEFAULT_TESTSET",
    "GROUPS",
    "GroupScore",
    "LetterMix",
    "letter_mixes",
    "load_letter_scores",
    "load_testset_texts",
    "render",
    "run",
    "score_groups",
    "summary",
    "write_reports",
]
