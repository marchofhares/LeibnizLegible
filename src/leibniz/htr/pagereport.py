"""``reports/htr/page-llm.md`` + ``.json``: the page-level test written up (LT1, Task 3).

The report is rendered from ``page-llm.scores.json`` (what ``bench page-score``
leaves) and the readings' usage: the protocol and the settings per model, the
two sets and how they were drawn, the PHILIUMM page table beside the kraken
model, the pool table beside K2b's and K3's readers on the same letters (and
their whole-set numbers as the committed reports carry them, cited), the
refusals both ways, the usage and cost, the diff counts, and the two caveats.
Numbers only; nothing that reproduces a reference text or a model's output.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from leibniz.htr.pageread import DEFAULT_LONG_SIDE, DEFAULT_MAX_TOKENS, PAGE_PROMPT
from leibniz.htr.pagescore import GAP_COST, HEADLINE_POLICY, NEAR_CER

DEFAULT_REPORT = Path("reports/htr/page-llm.md")
DEFAULT_SCORES = Path("reports/htr/page-llm.scores.json")
K2B_EVAL = Path("reports/kurrent/letterpool-eval.json")
K3_EVAL = Path("reports/kurrent/k3-letterpool/letterpool-eval.json")
# The LLM rows of B1 (reports/philiumm-repro.md, 150 line crops, zero-shot), as published.
B1_LLM_ROWS: tuple[tuple[str, str], ...] = (
    ("Kraken (PHILIUMM, fine-tuned)", "8.19 %"),
    ("gpt-4.1", "36.60 %"),
    ("gpt-4o", "43.82 %"),
    ("gemini-3.8-flash", "55.11 %"),
    ("gpt-5.6-sol", "74.17 %"),
    ("gpt-5.6-luna", "76.24 %"),
    ("gpt-5.6-terra", "78.66 %"),
)


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{d}f} %"


def _ci(block: Mapping | None, key: str = "pages") -> str:
    if not block or not block.get(key):
        return "—"
    return f"**{_pct(block['cer'])}** ({_pct(block['cer_lo'])}–{_pct(block['cer_hi'])})"


def _n(x: int | float | None) -> str:
    return "—" if x is None else f"{x:,}"


def _usd(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f} USD"


def committed_pool_rows(paths: Mapping[str, Path] | None = None) -> dict[str, dict]:
    """The whole-set rows of K2b and K3 as their committed JSON carries them:
    ``{reader: {"all": …, "selection": …, "test": …, "L": …, "K/k": …}}`` under the
    headline policy."""
    paths = paths or {"k2b": K2B_EVAL, "k3": K3_EVAL}
    out: dict[str, dict] = {}
    for _label, path in paths.items():
        p = Path(path)
        if not p.exists():
            continue
        agg = json.loads(p.read_text(encoding="utf-8")).get("aggregate", {})
        for reader, pols in agg.items():
            head = pols.get(HEADLINE_POLICY) or {}
            if not head or reader in out:
                continue
            out[reader] = {
                "all": head.get("all"),
                "selection": (head.get("half") or {}).get("selection"),
                "test": (head.get("half") or {}).get("test"),
                "L": (head.get("hand") or {}).get("L"),
                "K/k": (head.get("hand") or {}).get("K/k"),
            }
    return out


def render(scores: Mapping, *, committed: Mapping[str, dict] | None = None) -> str:
    """The Markdown report from the score file's content."""
    phil = scores.get("philiumm") or {}
    pool = scores.get("pool") or {}
    gen = scores.get("generated") or {}
    models = sorted(set((phil.get("models") or {}) | (pool.get("models") or {})))
    out: list[str] = []
    out.append("# Frontier vision models on whole pages, against the project's readers (LT1)")
    out.append("")
    out.append(
        f"Generated {datetime.now(UTC).date().isoformat()}. The fair protocol a colleague "
        "proposed, adopted: whole pages, one page a call, the frontier models' answers "
        "scored with the same metric and policy as the project's line readers (B1's "
        "`philiumm` normalisation, K2b's letter-pool metric), so one number stands against "
        "another. The B1 numbers of September used line crops, which favour a line "
        "recogniser; this is the page-level test."
    )
    out.append("")
    out.append("## The protocol")
    out.append("")
    out.append(
        f"- One prompt for every model (SHA-256 prefix `{gen.get('prompt_sha256', '—')}`): "
        f"“{PAGE_PROMPT}”"
    )
    long_side = gen.get("long_side", DEFAULT_LONG_SIDE)
    max_tokens = gen.get("max_tokens", DEFAULT_MAX_TOKENS)
    out.append(
        f"- The page image downscaled to a long side of {long_side} px "
        "(JPEG, quality 92), a half at a time where the page list names a column (the "
        "PHILIUMM openings — two folios on one scan — are read as left and right); the "
        "sizes sent and the APIs' own token counts are in the readings."
    )
    out.append(
        f"- Temperature 0 where the API takes it; `max_tokens` {max_tokens}; "
        "reasoning off or at the lowest setting the API allows — the setting per model in "
        "the table below. A refusal, an empty answer or a runaway (the output cap reached) "
        "is recorded, retried once, and scored both ways: charged as 100 % error, and left out."
    )
    out.append(
        "- Only page images went to an API, and only the GWLB's public-domain scans (the "
        "pool's pages from the project's image cache; PHILIUMM's val pages from the "
        "dataset's Hub repository, CC BY 4.0). The pool's reference texts (CC BY-NC 4.0) "
        "never left the machine; no API output is a training label."
    )
    out.append("")
    out.append("## The models and their settings")
    out.append("")
    out.append(
        "| model | engine | reasoning | temperature | max_tokens | pages | calls | "
        "input tokens a page | output tokens a page | cost | seconds a page |"
    )
    out.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for m in models:
        u = _merge_usage((phil.get("usage") or {}).get(m), (pool.get("usage") or {}).get(m))
        s = u.get("settings") or {}
        pages = u.get("pages") or 0
        head = f"| {m} | {u.get('engine', '—')} | {s.get('reasoning', '—')} | "
        if not pages:
            out.append(head + "— | — | 0 | 0 | — | — | — | — |")
            continue
        temp = "not sent" if s.get("temperature") is None else s.get("temperature")
        out.append(
            head + f"{temp} | {s.get('max_tokens', '—')} | {_n(pages)} | {_n(u.get('calls'))} | "
            f"{_n(round(u['input_tokens'] / pages))} | {_n(round(u['output_tokens'] / pages))} | "
            f"{_usd(u.get('cost'))} | {(u.get('seconds', 0.0) / pages):.1f} |"
        )
    out.append("")
    out.append(
        "Output tokens include the thinking the APIs bill as output (Claude's thinking "
        "cannot be switched off on the current models and Gemini 3.x Pro and 4 Argon have no "
        "“off”, so *low* is the floor on both). The cost is the logged usage at the pricing "
        "tables in `htr/engines.py` (list rates on the day of the run, estimates)."
    )
    out.append("")
    # ---- PHILIUMM ------------------------------------------------------------ #
    out.append("## PHILIUMM's held-out pages (Latin and French)")
    out.append("")
    n_pages = phil.get("pages") or 0
    out.append(
        f"The dataset's `val` split — {_n(n_pages)} page{'s' if n_pages != 1 else ''} "
        f"({_n(phil.get('calls'))} calls: an opening is two) carrying "
        f"{_n(phil.get('ref_lines'))} reference lines and {_n(phil.get('ref_chars'))} reference "
        "characters under the headline policy. The reference of a page is the dataset's own "
        "PAGE XML for that scan, its lines in document order (the parquet the model was scored "
        "on in B1 carries text and image only, no page; the page is rebuilt from the XML the "
        "Hub publishes beside each scan). The dataset has no `test` split: `val` is its "
        "held-out split, the one B1 reproduced the model's CER on."
        + (
            f" Left out, no XML or image on disk: {', '.join(phil['missing'])}."
            if phil.get("missing")
            else ""
        )
    )
    out.append("")
    out.append(
        "Page CER: the edit distance between the page's reference and the model's answer, "
        "both as one string of lines joined by spaces, over the reference's length; pooled "
        "over pages (Σ edits ÷ Σ reference characters), 95 % bootstrap interval over pages "
        "(1,000 resamples, seed 12345), the per-page distribution beside it."
    )
    out.append("")
    out.append(
        "| reader | `philiumm`, failed pages charged | failed pages left out | failed | "
        "`lenient` | `strict` | `reading` | per-page median | per-page max |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for reader, pols in (phil.get("aggregate") or {}).items():
        head = pols.get(HEADLINE_POLICY) or {}
        ch, om = head.get("charged") or {}, head.get("omitted") or {}
        out.append(
            f"| {reader} | {_ci(ch)} | {_ci(om)} | {ch.get('failed', 0)} of {ch.get('pages', 0)} | "
            f"{_pct((pols.get('lenient') or {}).get('charged', {}).get('cer'))} | "
            f"{_pct((pols.get('strict') or {}).get('charged', {}).get('cer'))} | "
            f"{_pct((pols.get('reading') or {}).get('charged', {}).get('cer'))} | "
            f"{_pct(ch.get('page_cer_median'))} | {_pct(ch.get('page_cer_max'))} |"
        )
    out.append("")
    kr = phil.get("kraken") or {}
    if kr:
        out.append(
            f"The PHILIUMM kraken model's row is its own line readings of the same lines, joined "
            f"per page ({_n(kr.get('covered'))} of {_n(phil.get('ref_lines'))} reference lines "
            f"covered by the dump `{kr.get('dump', '—')}`), scored by the same page metric."
        )
    else:
        out.append(
            "The PHILIUMM kraken model's row is missing: no line dump of the val pages was "
            "given (`bench page-lines`, then `bench run … --engine kraken --out`, then "
            "`page-score --kraken-lines`). B1's per-line dump carries parquet row ids, "
            "which name no page, so it cannot stand in."
        )
    out.append("")
    out.append("For scale, B1's line-crop numbers (150 lines, zero-shot, September 2026):")
    out.append("")
    out.append("| engine (B1, line crops) | CER |")
    out.append("|---|---:|")
    for name, cer in B1_LLM_ROWS:
        out.append(f"| {name} | {cer} |")
    out.append("")
    # ---- the pool -------------------------------------------------------------- #
    out.append("## The GWLB letter pool (German, Kurrent)")
    out.append("")
    draw = pool.get("draw") or {}
    out.append(
        f"{_n(draw.get('letters'))} letters, {_n(draw.get('pages'))} pages of K2b's frozen set, "
        f"drawn seeded (seed {draw.get('seed', '—')}) whole letters at a time: "
        f"{_n(draw.get('pages_L'))} pages in Leibniz's hand and {_n(draw.get('pages_K'))} in "
        f"the correspondents', {_n(draw.get('letters_selection'))} letters of the selection half "
        f"and {_n(draw.get('letters_test'))} of the test half; {_n(pool.get('lines'))} recognised "
        f"lines, {_n(pool.get('ref_chars'))} reference characters. The metric is K2b's: each "
        "letter's reference aligned to the concatenation of everything read on its pages — for "
        "a page model, the page texts in order — an infix alignment, the reference consumed "
        "whole, machine text before and after it free; CER pooled over characters, 95 % "
        "bootstrap interval over letters. The readers of K2b and K3 are scored on the same "
        "letters from their readings on disk; their whole-set numbers (134 letters) stand in "
        "the last column as the committed reports carry them."
    )
    out.append("")
    out.append(
        "| reader | these letters, `philiumm` | selection half | test half | Leibniz's hand (L) | "
        "the correspondents' (K/k) | `reading` policy | whole set (134 letters, K2b / K3) |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    committed = committed if committed is not None else {}
    for reader, pols in (pool.get("aggregate") or {}).items():
        head = pols.get(HEADLINE_POLICY) or {}
        whole = (committed.get(reader) or {}).get("all")
        out.append(
            f"| {reader} | {_ci(head.get('all'), 'letters')} | "
            f"{_ci((head.get('half') or {}).get('selection'), 'letters')} | "
            f"{_ci((head.get('half') or {}).get('test'), 'letters')} | "
            f"{_ci((head.get('hand') or {}).get('L'), 'letters')} | "
            f"{_ci((head.get('hand') or {}).get('K/k'), 'letters')} | "
            f"{_pct(((pols.get('reading') or {}).get('all') or {}).get('cer'))} | "
            f"{_ci(whole, 'letters') if whole else '—'} |"
        )
    out.append("")
    omitted = pool.get("omitted") or {}
    if omitted.get("letters"):
        out.append(
            f"**Failed pages left out.** {_n(omitted['letters'])} of the {_n(draw.get('letters'))} "
            "letters have every page read by every page model; on those letters alone:"
        )
        out.append("")
        out.append("| reader | `philiumm` | Leibniz's hand (L) | the correspondents' (K/k) |")
        out.append("|---|---:|---:|---:|")
        for reader, pols in (omitted.get("aggregate") or {}).items():
            head = pols.get(HEADLINE_POLICY) or {}
            out.append(
                f"| {reader} | {_ci(head.get('all'), 'letters')} | "
                f"{_ci((head.get('hand') or {}).get('L'), 'letters')} | "
                f"{_ci((head.get('hand') or {}).get('K/k'), 'letters')} |"
            )
        out.append("")
    elif pool.get("aggregate"):
        out.append(
            "**Failed pages left out:** no letter was dropped — every page of every letter "
            "read on the first or the second attempt for every page model, so the table "
            "above is both ways at once."
        )
        out.append("")
    # ---- refusals ------------------------------------------------------------ #
    out.append("## Refusals, empty answers, runaways")
    out.append("")
    out.append(
        "| model | set | pages | ok | refused | empty | runaway | error | retried | "
        "ok on the second attempt |"
    )
    out.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for set_name, block in (("philiumm", phil), ("pool", pool)):
        for m in models:
            st = (block.get("statuses") or {}).get(m)
            if not st:
                continue
            final, first = st.get("final") or {}, st.get("first") or {}
            second = first.get("refused", 0) + first.get("empty", 0) + first.get("runaway", 0)
            second += first.get("error", 0)
            second -= sum(v for k, v in final.items() if k != "ok")
            cells = [str(final.get(k, 0)) for k in ("ok", "refused", "empty", "runaway", "error")]
            out.append(
                f"| {m} | {set_name} | {sum(final.values())} | " + " | ".join(cells) + " | "
                f"{st.get('retried', 0)} | {max(0, second)} |"
            )
    out.append("")
    out.append(
        "A page whose final status is not ok is charged as 100 % error in the first column "
        "of each table and left out in the second (the pool: the letter it belongs to is "
        "left out)."
    )
    out.append("")
    # ---- the diff --------------------------------------------------------------- #
    out.append("## The line diff: where exactly one reader is right")
    out.append("")
    out.append(
        "Each page model's lines and the line reader's lines are aligned to the same "
        "reference lines (a Needleman–Wunsch over lines: a pair costs its normalised edit "
        f"distance, a gap {GAP_COST}, so two lines under 30 % similar are not paired), under "
        "the headline policy. *Right* is an exact line; *near* within "
        f"{NEAR_CER:.0%} CER. *Invented*: the reader's lines matched to no reference line; "
        "*dropped*: reference lines the reader has no line for. On PHILIUMM's pages the "
        "reference lines are the dataset's; on the pool the factory's aligner cuts the "
        "letter's text into the line reader's lines (the lines it accepts at its gate), so "
        "the pool diff is measured on those lines only and the page model's lines are "
        "aligned to them."
    )
    out.append("")
    out.append(
        "| set | page model (a) | line reader (b) | ref lines | a lines | b lines | both right | "
        "only a right | only b right | both wrong | a near | b near | a invented | a dropped | "
        "b invented | b dropped | a length ratio | b length ratio |"
    )
    out.append(
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for set_name, block in (("philiumm", phil), ("pool", pool)):
        for row in block.get("diff") or []:
            d = row.get("counts") or {}
            lead = f"| {set_name} | {row.get('a')} | {row.get('b')} | "
            if d.get("a_length_ratio") is None:
                out.append(lead + " | ".join(["—"] * 15) + " |")
                continue
            keys = (
                "ref_lines",
                "a_lines",
                "b_lines",
                "both_right",
                "only_a_right",
                "only_b_right",
                "both_wrong",
                "a_near",
                "b_near",
                "a_invented",
                "a_dropped",
                "b_invented",
                "b_dropped",
            )
            cells = [_n(d.get(k)) for k in keys]
            cells += [f"{d['a_length_ratio']:.2f}", f"{d['b_length_ratio']:.2f}"]
            out.append(lead + " | ".join(cells) + " |")
    out.append("")
    # ---- caveats --------------------------------------------------------------- #
    out.append("## What this measures, and what it does not")
    out.append("")
    out.append(
        "- **The page sets are small.** PHILIUMM's held-out split is "
        f"{_n(phil.get('pages'))} pages and the pool draw {_n(draw.get('pages'))} pages of "
        f"{_n(draw.get('letters'))} letters; the intervals are wide, and a few refused or "
        "runaway pages move a model's number by points. The numbers are the first page-level "
        "ones, not the last."
    )
    out.append(
        "- **The pool's references are the GWLB's checked transcriptions of letters**, made "
        "for the edition, not a random sample of the Nachlass's German pages: letters of "
        "1708–1716, half of them in Leibniz's own hand by construction. The German number "
        "is the error rate on that material, as K2b's and K3's are."
    )
    out.append(
        "- The page models never saw the project's line segmentation; the line readers never "
        "saw the whole page. Where the diff shows invented and dropped lines, the page "
        "model's reading order and its line count are part of what is measured, as the "
        "colleague's protocol intends."
    )
    out.append(
        "- Reasoning could not be switched off on Claude or on Gemini 3.x Pro and 4 Argon; "
        "*low* is the floor, named per model above, and the thinking tokens are in the "
        "output count and the cost."
    )
    out.append("")
    return "\n".join(out)


def _merge_usage(*blocks: Mapping | None) -> dict:
    """The usage of a model over both sets, summed."""
    out: dict = {}
    for b in blocks:
        if not b:
            continue
        if not out:
            out = dict(b)
            continue
        for k in ("calls", "pages", "input_tokens", "output_tokens", "reasoning_tokens"):
            out[k] = int(out.get(k, 0)) + int(b.get(k, 0))
        out["cost"] = round(float(out.get("cost", 0.0)) + float(b.get("cost", 0.0)), 4)
        out["seconds"] = round(float(out.get("seconds", 0.0)) + float(b.get("seconds", 0.0)), 1)
    return out


def write_report(
    scores: Mapping,
    *,
    report_path: Path | str = DEFAULT_REPORT,
    committed: Mapping[str, dict] | None = None,
) -> tuple[Path, Path]:
    """Write ``page-llm.md`` and ``page-llm.json`` (the score file's content as rendered)."""
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    md = render(scores, committed=committed)
    report_path.write_text(md, encoding="utf-8")
    js = report_path.with_suffix(".json")
    payload = dict(scores)
    payload["committed_pool_rows"] = committed or {}
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report_path, js


__all__ = [
    "B1_LLM_ROWS",
    "DEFAULT_REPORT",
    "DEFAULT_SCORES",
    "K2B_EVAL",
    "K3_EVAL",
    "committed_pool_rows",
    "render",
    "write_report",
]
