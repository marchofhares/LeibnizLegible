"""K3 Task 4: the validation breakdown, the error composition and the normalization tax.

The letter pool (K2b's metric, `align/letterpool_eval.py`) and Dresden (K1's
`bench kurrent-smoke`) are scored by their own code; this module scores what
those do not: a model's hypotheses on the frozen validation set, by stratum,
hand group and reader (the manifest's tags), with the composition of its
errors — substitutions, insertions and deletions from a Levenshtein backtrace
— and, on any set, the **normalization tax**: the CER under the harness's
``philiumm`` policy against the CER after the aligner's fold
(:func:`leibniz.align.normalize.normalize`: case, u/v, i/j, accents and
punctuation folded, the abbreviations expanded). The difference is what a
diplomatic scorer charges for the edition's conventions the model learned
(the C3 prompt's tax): on the validation set, whose reference is the
edition's own text, it is near zero by construction; on Dresden, whose
reference is diplomatic, it is the tax itself.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass

from leibniz.align.normalize import normalize as fold
from leibniz.htr import metrics

GROUP_KEYS = ("stratum", "group", "reader", "hand")


def edit_ops(ref: str, hyp: str) -> tuple[int, int, int]:
    """``(substitutions, insertions, deletions)`` of one Levenshtein alignment.

    Insertions are characters the hypothesis has beyond the reference, deletions
    characters of the reference the hypothesis lacks; the sum is the edit
    distance :func:`leibniz.htr.metrics.edit_distance` reports. Ties resolve
    towards substitutions, then deletions.
    """
    n, m = len(ref), len(hyp)
    if n == 0:
        return 0, m, 0
    if m == 0:
        return 0, 0, n
    prev = list(range(m + 1))
    rows = [prev]
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            cur[j] = min(prev[j - 1] + cost, prev[j] + 1, cur[j - 1] + 1)
        rows.append(cur)
        prev = cur
    sub = ins = dele = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            if rows[i][j] == rows[i - 1][j - 1] + cost:
                sub += cost
                i, j = i - 1, j - 1
                continue
        if i > 0 and rows[i][j] == rows[i - 1][j] + 1:
            dele += 1
            i -= 1
            continue
        ins += 1
        j -= 1
    return sub, ins, dele


@dataclass(slots=True)
class Composition:
    lines: int = 0
    ref_chars: int = 0
    edits: int = 0
    sub: int = 0
    ins: int = 0
    dele: int = 0
    exact: int = 0

    @property
    def cer(self) -> float | None:
        return (self.edits / self.ref_chars) if self.ref_chars else None

    def add(self, score: metrics.LineScore, ops: tuple[int, int, int]) -> None:
        self.lines += 1
        self.ref_chars += score.ref_chars
        self.edits += score.char_edits
        self.sub += ops[0]
        self.ins += ops[1]
        self.dele += ops[2]
        self.exact += int(score.char_edits == 0)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["del"] = d.pop("dele")
        d["cer"] = self.cer
        total = max(1, self.sub + self.ins + self.dele)
        d["sub_share"] = self.sub / total
        d["ins_share"] = self.ins / total
        d["del_share"] = self.dele / total
        return d


def score_with_ops(
    refs: Mapping[str, str],
    hyps: Mapping[str, str],
    policy: metrics.NormPolicy = metrics.PHILIUMM_POLICY,
) -> dict[str, tuple[metrics.LineScore, tuple[int, int, int]]]:
    """Every reference line scored against the hypothesis (missing → empty), with
    its edit operations, under ``policy``."""
    out: dict[str, tuple[metrics.LineScore, tuple[int, int, int]]] = {}
    for lid, ref in refs.items():
        sc = metrics.score_line(ref, hyps.get(lid, ""), policy, line_id=lid)
        out[lid] = (sc, edit_ops(sc.ref, sc.hyp))
    return out


def breakdown(
    scored: Mapping[str, tuple[metrics.LineScore, tuple[int, int, int]]],
    tags: Mapping[str, Mapping[str, str]],
    *,
    keys: Sequence[str] = GROUP_KEYS,
) -> dict:
    """Pooled composition overall and per tag value (stratum, hand group, reader, hand)."""
    overall = Composition()
    by: dict[str, dict[str, Composition]] = {k: {} for k in keys}
    for lid, (sc, ops) in scored.items():
        overall.add(sc, ops)
        t = tags.get(lid, {})
        for k in keys:
            v = str(t.get(k, "unknown"))
            by[k].setdefault(v, Composition()).add(sc, ops)
    return {
        "overall": overall.as_dict(),
        "by": {k: {v: c.as_dict() for v, c in sorted(d.items())} for k, d in by.items()},
    }


def bootstrap(
    scored: Mapping[str, tuple[metrics.LineScore, tuple[int, int, int]]],
    *,
    seed: int = 12345,
    n_resamples: int = 1000,
) -> dict:
    iv = metrics.bootstrap_ci(
        [sc for sc, _ in scored.values()], metric="cer", seed=seed, n_resamples=n_resamples
    )
    return {"cer": iv.point, "cer_lo": iv.lo, "cer_hi": iv.hi, "n": len(scored)}


def normalization_tax(
    refs: Mapping[str, str],
    hyps: Mapping[str, str],
    *,
    policy: metrics.NormPolicy = metrics.PHILIUMM_POLICY,
    fold_fn: Callable[[str], str] = fold,
) -> dict:
    """CER under ``policy`` against CER after the aligner's fold on both sides; the
    difference is the tax a diplomatic scorer charges for the edition's conventions."""
    policy_scores = [
        metrics.score_line(r, hyps.get(k, ""), policy, line_id=k) for k, r in refs.items()
    ]
    folded_scores = [
        metrics.score_line(fold_fn(r), fold_fn(hyps.get(k, "")), metrics.STRICT_POLICY, line_id=k)
        for k, r in refs.items()
    ]
    a, b = metrics.cer(policy_scores), metrics.cer(folded_scores)
    return {
        "policy": policy.name,
        "cer_policy": a,
        "cer_folded": b,
        "tax": a - b,
        "lines": len(refs),
    }


def manifest_tags(rows: Iterable[Mapping], *, split: str = "val") -> dict[str, dict[str, str]]:
    """``line id -> tags`` for the manifest rows of a split (the id as the training
    files name it: ``<page>:<seq>``)."""
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        if r.get("split") != split or not r.get("image"):
            continue
        lid = f"{r['page_id']}:{int(r['line_seq']):03d}"
        out[lid] = {k: str(r.get(k, "")) for k in GROUP_KEYS}
        out[lid]["text"] = r.get("text", "")
    return out


def refs_from_tags(tags: Mapping[str, Mapping[str, str]]) -> dict[str, str]:
    return {lid: t["text"] for lid, t in tags.items()}


def disagreements(
    refs: Mapping[str, str],
    a: Mapping[str, str],
    b: Mapping[str, str],
    *,
    policy=metrics.PHILIUMM_POLICY,
) -> dict:
    """Where two readers disagree, how often either is exactly right (the number the
    C3 amendment asks for, per set): lines where the two hypotheses differ, and of
    those the share where a, b or either equals the reference under ``policy``."""
    n = diff = a_right = b_right = either = 0
    for lid, ref in refs.items():
        n += 1
        ha = metrics.normalize(a.get(lid, ""), policy)
        hb = metrics.normalize(b.get(lid, ""), policy)
        if ha == hb:
            continue
        diff += 1
        r = metrics.normalize(ref, policy)
        ra, rb = ha == r, hb == r
        a_right += ra
        b_right += rb
        either += ra or rb
    return {
        "lines": n,
        "disagree": diff,
        "a_exact": a_right,
        "b_exact": b_right,
        "either_exact": either,
        "either_share": (either / diff) if diff else None,
    }


def worst_lines(
    scored: Mapping[str, tuple[metrics.LineScore, tuple[int, int, int]]], n: int = 20
) -> list[dict]:
    rows = sorted(scored.items(), key=lambda kv: -kv[1][0].cer)[:n]
    return [
        {"line_id": lid, "cer": sc.cer, "ref": sc.ref, "hyp": sc.hyp, "ops": list(ops)}
        for lid, (sc, ops) in rows
    ]


def summarize_counts(d: Mapping[str, Composition]) -> Counter:
    return Counter({k: v.lines for k, v in d.items()})


__all__ = [
    "GROUP_KEYS",
    "Composition",
    "bootstrap",
    "breakdown",
    "disagreements",
    "edit_ops",
    "manifest_tags",
    "normalization_tax",
    "refs_from_tags",
    "score_with_ops",
    "worst_lines",
]
