"""The K3 reports rendered from the training artefacts' JSON (Task 2: the pilots).

``reports/kurrent/k3-pilots.md`` + ``.json``: the TrOCR pilot's rows
(``data/models/k3/trocr/pilot.json``: per setting the status, lines, seconds,
lines per second, peak MiB, validation CER and the projection) beside the
kraken pilot's account (``data/models/k3/kraken-pilot/account.json``: the
epoch's seconds from the checkpoint times, kraken's validation accuracy, the
project's CER of the best weights), with the extrapolation to the full plan
and the week the prompt holds the plan to. Numbers only, from the files.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

DEFAULT_REPORTS_DIR = Path("reports/kurrent")
WEEK_HOURS = 7 * 24.0


def _f(x: float | None, d: int = 2) -> str:
    return "—" if x is None else f"{x:.{d}f}"


def _pct(x: float | None, d: int = 2) -> str:
    return "—" if x is None else f"{100 * x:.{d}f} %"


def _n(x: int | float | None) -> str:
    return "—" if x is None else f"{int(x):,}"


def _hours(x: float | None) -> str:
    if x is None:
        return "—"
    if x < 48:
        return f"{x:.1f} h"
    return f"{x / 24:.1f} days"


def load_json(path: Path | str) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def kraken_pilot_summary(account: Mapping | None, *, train_lines: int, plan_epochs: int) -> dict:
    """What the kraken pilot says: the epoch's wall time (from the checkpoint times,
    or the run's own seconds where recorded), the pace, the projection."""
    if not account:
        return {"status": "not run"}
    secs = list(account.get("epoch_seconds") or [])
    run_seconds = account.get("run_seconds")
    epoch_s = secs[-1] if secs else run_seconds
    pilot_lines = account.get("pilot_lines")
    pace = (pilot_lines / epoch_s) if (epoch_s and pilot_lines) else None
    proj_h = (train_lines * plan_epochs / pace / 3600.0) if pace else None
    score = account.get("score") or {}
    cks = account.get("checkpoints") or []
    return {
        "status": "ok" if cks else "no checkpoint",
        "settings": account.get("settings"),
        "pilot_lines": pilot_lines,
        "epoch_seconds": epoch_s,
        "lines_per_s": pace,
        "val_metric": cks[-1]["val_metric"] if cks else None,
        "val_cer": score.get("cer"),
        "val_lines_per_s": score.get("lines_per_s"),
        "peak_mib": account.get("peak_mib"),
        "resized": (account.get("codec") or {}).get("added")
        if account.get("codec")
        else (account.get("log") or {}).get("resized"),
        "projection_hours": proj_h,
        "plan_epochs": plan_epochs,
    }


def trocr_pilot_summary(pilot: Mapping | None, *, plan_epochs: float) -> dict:
    if not pilot:
        return {"status": "not run", "rows": []}
    rows = []
    for r in pilot.get("rows", []):
        v = r.get("val") or {}
        proj = r.get("projection") or {}
        rows.append(
            {
                "key": r["settings"]["key"],
                "status": r["status"],
                "lines": r.get("lines"),
                "seconds": r.get("seconds"),
                "lines_per_s": r.get("lines_per_s"),
                "peak_mib": r.get("peak_mib"),
                "val_cer": v.get("cer"),
                "val_lines_per_s": v.get("lines_per_s"),
                "projection_hours": proj.get("total_hours"),
                "error": r.get("error", ""),
            }
        )
    return {"status": "ok", "meta": pilot.get("meta", {}), "rows": rows, "plan_epochs": plan_epochs}


def build_pilots(
    *,
    trocr: Mapping | None,
    kraken: Mapping | None,
    trocr_probes: Sequence[Mapping | None] = (),
    train_lines: int,
    val_lines: int,
    plan_epochs_trocr: float,
    plan_epochs_kraken: int,
    rented_note: str = "",
) -> dict:
    t = trocr_pilot_summary(trocr, plan_epochs=plan_epochs_trocr)
    probe_rows: list[dict] = []
    for pr in trocr_probes:
        probe_rows.extend(trocr_pilot_summary(pr, plan_epochs=plan_epochs_trocr)["rows"])
    k = kraken_pilot_summary(kraken, train_lines=train_lines, plan_epochs=plan_epochs_kraken)
    feasible = [r for r in t["rows"] if r["status"] == "ok" and r["projection_hours"]]
    fastest = min(feasible, key=lambda r: r["projection_hours"]) if feasible else None
    best_cer = (
        min((r for r in feasible if r["val_cer"] is not None), key=lambda r: r["val_cer"])
        if feasible
        else None
    )
    return {
        "generated": date.today().isoformat(),
        "train_lines": train_lines,
        "val_lines": val_lines,
        "week_hours": WEEK_HOURS,
        "trocr": t,
        "trocr_probe": probe_rows,
        "kraken": k,
        "trocr_fastest": fastest["key"] if fastest else None,
        "trocr_best_cer": best_cer["key"] if best_cer else None,
        "over_a_week": bool(
            (fastest and fastest["projection_hours"] > WEEK_HOURS)
            or (k.get("projection_hours") or 0) > WEEK_HOURS
        ),
        "rented_note": rented_note,
    }


def render_pilots(s: Mapping) -> str:
    L: list[str] = [
        "# K3: the timing pilots",
        "",
        f"Two candidates timed on this GPU (GTX 1660 Ti, 6 GB) over bounded runs of the training "
        f"set ({_n(s['train_lines'])} training lines, {_n(s['val_lines'])} validation lines) and "
        f"extrapolated to the full plan. Generated {s['generated']}.",
        "",
        "## (a) TrOCR from the Bern checkpoint",
        "",
    ]
    probe = s.get("trocr_probe") or []
    if probe:
        L += [
            "The memory probe first: every setting on the same 2,000 training lines under a hard "
            "allocator cap of 4,000 MiB for the process (an allocation past it fails in-process "
            "instead of spilling into host memory under WSL2).",
            "",
            "| setting | status | lines | seconds | lines/s | peak MiB | six epochs |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for r in probe:
            L.append(
                f"| {r['key']} | {r['status']} | {_n(r['lines'])} | {_f(r['seconds'], 0)} | "
                f"{_f(r['lines_per_s'])} | {_n(r['peak_mib'])} | {_hours(r['projection_hours'])} |"
            )
        L += ["", "Then the 20,000-line epochs with the validation set scored:", ""]
    t = s["trocr"]
    if t["status"] != "ok":
        L.append("Not run.")
    else:
        meta = t.get("meta", {})
        L += [
            f"Base `{meta.get('base')}`; up to {_n(meta.get('pilot_lines'))} lines per setting; "
            f"the validation set scored after each run; the projection for "
            f"{t['plan_epochs']:g} epochs over the training lines, validation passes included.",
            "",
            "| setting | status | lines | seconds | lines/s | peak MiB | val CER | val lines/s "
            "| full plan |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in t["rows"]:
            L.append(
                f"| {r['key']} | {r['status']}{' (' + r['error'][:60] + ')' if r['error'] else ''}"
                f" | {_n(r['lines'])} | {_f(r['seconds'], 0)} | {_f(r['lines_per_s'])} | "
                f"{_n(r['peak_mib'])} | {_pct(r['val_cer'])} | {_f(r['val_lines_per_s'], 1)} | "
                f"{_hours(r['projection_hours'])} |"
            )
        L += [
            "",
            f"Fastest feasible setting: **{s['trocr_fastest'] or '—'}**; lowest validation CER "
            f"after the pilot run: **{s['trocr_best_cer'] or '—'}**.",
        ]
    L += ["", "## (b) kraken from the PHILIUMM checkpoint", ""]
    k = s["kraken"]
    if k["status"] == "not run":
        L.append("Not run.")
    else:
        st = k.get("settings") or {}
        L += [
            f"`ketos train` from `{st.get('base')}` with `--resize {st.get('resize')}` "
            f"(the codec grew by {_n(k.get('resized'))} code points), "
            f"`-u {st.get('normalization')}`, batch {st.get('batch_size')}, learning rate "
            f"{st.get('lr')}, one fixed epoch over {_n(k.get('pilot_lines'))} lines.",
            "",
            "| | value |",
            "|---|---:|",
            f"| epoch wall time | {_f(k.get('epoch_seconds'), 0)} s |",
            f"| lines/s (training, validation included) | {_f(k.get('lines_per_s'))} |",
            f"| peak MiB | {_n(k.get('peak_mib'))} |",
            f"| kraken's validation accuracy | {_f(k.get('val_metric'), 4)} |",
            "| validation CER (philiumm policy, the project's engine) | "
            f"{_pct(k.get('val_cer'))} |",
            f"| validation lines/s (inference) | {_f(k.get('val_lines_per_s'), 1)} |",
            f"| full plan ({k.get('plan_epochs')} epochs) | {_hours(k.get('projection_hours'))} |",
        ]
    L += [
        "",
        "## Against the week",
        "",
        f"The prompt holds the plan to a week on this GPU ({WEEK_HOURS:.0f} h): "
        f"**{'over' if s['over_a_week'] else 'within'}**."
        + (f" {s['rented_note']}" if s["rented_note"] else ""),
        "",
    ]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Model cards (Task 4): a draft per model, from the evaluation's JSON
# --------------------------------------------------------------------------- #

BASES = {
    "trocr": {
        "name": "dh-unibe/trocr-kurrent-XVI-XVII",
        "licence": "MIT",
        "origin": "https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII",
        "what": "a TrOCR vision-encoder–decoder fine-tuned on German Kurrent of the 16th–18th "
        "centuries (Bern; the card reports test CER 5.4 %)",
    },
    "kraken": {
        "name": "FoNDUE-GD_v2_ft_Leibniz.safetensors (PHILIUMM)",
        "licence": "CC BY 4.0",
        "origin": "Zenodo 10.5281/zenodo.21457538",
        "what": "the PHILIUMM project's kraken recognition model for Leibniz's Latin and "
        "French (FoNDUE-GD v2 fine-tuned; self-reported CER 8.33 %)",
    },
    "ppocr": {
        "name": "small-models-for-glam/kraken-ppocrv6-medium (medium.safetensors)",
        "licence": "Apache-2.0",
        "origin": "https://huggingface.co/small-models-for-glam/kraken-ppocrv6-medium",
        "what": "kraken's PP-OCRv6 medium recognition model (15.9 M parameters), trained on "
        "many printed and handwritten sets including German Kurrent ones and the Dresdner "
        "Hofdiarium",
    },
}


def render_model_card(c: Mapping) -> str:
    """A model card draft. ``c`` carries: ``key`` (trocr | kraken | ppocr), ``version``,
    ``path``, ``trained`` (the training's account: lines, epochs, settings, the best epoch),
    ``trainset`` (the k3-trainset summary), ``letterpool`` (the pool rows for this model:
    overall, test half, by hand, with intervals), ``validation`` (the breakdown),
    ``dresden`` (CER, or None), ``speed`` (ms per line and the projection), ``licence``
    (the result's licence as L1's registry decides, or "open"), ``precision_note``."""
    base = BASES[c["key"]]
    ts = c.get("trainset") or {}
    sel, ex, sc = ts.get("selection", {}), ts.get("exclusions", {}), ts.get("screen", {})
    lp = c.get("letterpool") or {}
    v = c.get("validation") or {}
    sp = c.get("speed") or {}
    tr = c.get("trained") or {}
    L = [
        f"# Model card (draft): {c['version']}",
        "",
        f"A Leibniz Kurrent reader for the German stratum of the Nachlass: {base['what']}, "
        f"fine-tuned on K2's German ground truth. **Machine output, not an edition**: the "
        "model's text is Vorausedition-grade machine transcription with per-line confidence "
        "and provenance, subordinate to the Akademie-Ausgabe; it is never a reading of record.",
        "",
        "## Data statement",
        "",
        f"- **Base model:** {base['name']} ({base['licence']}; {base['origin']}).",
        f"- **Training lines:** {_n(tr.get('train_lines'))} minted lines of the German pieces "
        f"of the §70-expired Akademie-Ausgabe volumes, placed on the GWLB's scans by the "
        f"factory ({_n(sel.get('rows'))} rows selected, {_n(ex.get('total'))} excluded: "
        + ", ".join(f"{k} {_n(n)}" for k, n in (ex.get("by_reason") or {}).items())
        + "); the text is the edition's reading text (CC BY 4.0 in this project's release as "
        "K2's lines are open-bucket), the images the GWLB's (Public Domain Mark 1.0). "
        "By reader: "
        + ", ".join(f"{k} {_n(d.get('lines'))}" for k, d in (sel.get("by_reader") or {}).items())
        + ".",
        f"- **Validation lines:** {_n(tr.get('val_lines'))}, whole pieces held out, page-disjoint, "
        "stratified by stratum and hand; checkpoints were chosen on them alone.",
        "- **Never trained on:** the GWLB letter pool (CC BY-NC 4.0; evaluation only), the "
        "Dresdner Hofdiarium lines of the Kurrent Trace package (nc; evaluation only), "
        "PHILIUMM's held-out pages, K2's audit sheet lines.",
        f"- **Precision of the training lines: unmeasured.** {c.get('precision_note', '')} The "
        "screen before training (the length ratio of the minted text to the reading and the "
        "alignment confidence against the band the Latin and French mint occupies) put "
        + ", ".join(
            f"{g} {_pct(d.get('outside_share'), 1)} of {_n(d.get('n'))} lines"
            for g, d in (sc.get("by_group") or {}).items()
        )
        + " outside the band.",
        f"- **Licence of this model:** {c.get('licence', 'open')}.",
        "",
        "## Training",
        "",
        f"- Settings: `{tr.get('settings_key', '—')}`; epochs {_n(tr.get('epochs'))}, the best "
        f"at epoch {_n(tr.get('best_epoch'))} (validation CER {_pct(tr.get('best_cer'))}).",
        f"- Hardware: one GTX 1660 Ti (6 GB) under WSL2; {_hours(tr.get('hours'))} of training.",
        "",
        "## Error rates",
        "",
        "| set | CER | 95 % interval | note |",
        "|---|---:|---|---|",
    ]
    for label, key in (
        ("letter pool, all 134 letters", "all"),
        ("letter pool, test half", "test"),
        ("letter pool, Leibniz's own hand (L)", "L"),
        ("letter pool, the correspondents' hands (K/k)", "K/k"),
    ):
        row = lp.get(key) or {}
        L.append(
            f"| {label} | {_pct(row.get('cer'))} | {_pct(row.get('cer_lo'))}–"
            f"{_pct(row.get('cer_hi'))} | unfiltered, philiumm policy |"
        )
    ov = v.get("overall") or {}
    L.append(
        f"| validation set | {_pct(ov.get('cer'))} | — | the edition's text as reference; "
        f"substitutions {_pct(ov.get('sub_share'))}, insertions {_pct(ov.get('ins_share'))}, "
        f"deletions {_pct(ov.get('del_share'))} of the edits |"
    )
    if c.get("dresden") is not None:
        d = c["dresden"]
        L.append(f"| Dresden (sanity) | {_pct(d.get('cer'))} | — | {d.get('note', '')} |")
    L += [
        "",
        "## Intended use",
        "",
        "Reading the German pages of the digitised Leibniz Nachlass line by line for search "
        "and browsing (K4), with every line labelled machine output and its confidence shown; "
        "not a substitute for the Akademie-Ausgabe, not for other hands or centuries without "
        "measurement.",
        "",
        "## Speed",
        "",
        f"{_f(sp.get('ms_per_line'), 0)} ms a line on the GTX 1660 Ti as K1 measured it; "
        f"reading every German page at K2's all-in throughput: {_hours(sp.get('german_hours'))}.",
        "",
    ]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# The evaluation report (Task 4): k3-eval.md + .json
# --------------------------------------------------------------------------- #

K2B_READERS = ("v1", "philiumm", "trocr-kurrent-xvi-xvii", "trocr-hanse-xvi", "trocr-hanse-xvii")
K3_MODELS = ("k3-trocr", "k3-kraken")
HEADLINE = "philiumm"
# K2's reading job: 310,831 lines on 4,807 pages of the German records in 26,762 s of wall
# time, 26,109 s of them the model's (reports/kurrent/k2-read.json) — the overhead of the
# image loading from D: and the crops is the difference, 2.1 ms a line.
K2_LINES = 310_831
K2_WALL_S = 26_762.054
K2_MODEL_S = 26_108.921


def pool_rows(lp: Mapping | None, reader: str, policy: str = HEADLINE) -> dict | None:
    """The letter pool's rows for one reader under one policy: all, the halves, the hands,
    the years (each ``{cer, cer_lo, cer_hi, letters, …}``)."""
    if not lp:
        return None
    agg = (lp.get("aggregate") or {}).get(reader) or {}
    block = agg.get(policy)
    if not block:
        return None
    return {
        "all": block.get("all"),
        "selection": (block.get("half") or {}).get("selection"),
        "test": (block.get("half") or {}).get("test"),
        "hand": block.get("hand") or {},
        "year": block.get("year") or {},
        "selected": (lp.get("selected") or {}).get(reader),
        "info": next((r for r in lp.get("readers", []) if r.get("reader") == reader), None),
    }


def projection(ms_per_line: float | None) -> dict | None:
    """Hours to read K2's lines at this model's pace, with K2's measured overhead."""
    if ms_per_line is None:
        return None
    overhead_ms = 1000.0 * (K2_WALL_S - K2_MODEL_S) / K2_LINES
    all_in = ms_per_line + overhead_ms
    return {
        "ms_per_line_model": ms_per_line,
        "ms_per_line_all_in": all_in,
        "lines": K2_LINES,
        "hours": K2_LINES * all_in / 1000.0 / 3600.0,
    }


def choice(models: Mapping[str, Mapping]) -> dict:
    """The rule the prompt sets, made concrete: the better selection-half CER wins unless
    the faster model's selection-half CER lies within the slower model's 95 % bootstrap
    interval there (the margin the report proposes), in which case speed decides."""
    rows = []
    for key, m in models.items():
        sel = ((m.get("pool") or {}).get("selection")) or {}
        sp = m.get("speed") or {}
        if sel.get("cer") is None:
            continue
        rows.append(
            (key, sel["cer"], sel.get("cer_lo"), sel.get("cer_hi"), sp.get("ms_per_line_model"))
        )
    if len(rows) < 2:
        return {
            "rule": "selection-half CER, speed within the margin",
            "winner": rows[0][0] if rows else None,
            "reason": "one model measured" if rows else "nothing measured",
        }
    rows.sort(key=lambda r: r[1])
    best, second = rows[0], rows[1]
    faster = min(rows, key=lambda r: r[4] if r[4] is not None else float("inf"))
    margin = (best[3] - best[1]) if best[3] is not None else None
    within = margin is not None and faster[0] != best[0] and faster[1] <= best[1] + margin
    winner = faster[0] if within else best[0]
    return {
        "rule": "the better letter-pool CER on the selection half, unless the faster model's "
        "selection-half CER lies within the better model's 95 % bootstrap interval there, in "
        "which case speed decides (every re-read of the German pages pays the speed difference)",
        "best_cer": {"model": best[0], "cer": best[1], "cer_lo": best[2], "cer_hi": best[3]},
        "runner_up": {"model": second[0], "cer": second[1]},
        "faster": {"model": faster[0], "ms_per_line": faster[4]},
        "margin": margin,
        "faster_within_margin": within,
        "winner": winner,
    }


def build_eval(
    *,
    k3_pool: Mapping | None,
    k2b_pool: Mapping | None,
    val_breakdowns: Mapping[str, Mapping | None],
    dresden: Mapping | None,
    disagreements: Mapping | None,
    trained: Mapping[str, Mapping],
    trainset: Mapping | None,
    ppocr_pilot: Mapping | None = None,
    ablation_note: str = "",
) -> dict:
    """Everything k3-eval.md says, from the files: the pool rows of K2b's readers and the K3
    models, the validation breakdowns, Dresden, the speeds and projections, the choice."""
    dres = {}
    for r in (dresden or {}).get("results", []) if dresden else []:
        dres[r["key"]] = {
            "cer": (r.get("scores") or {}).get(HEADLINE, {}).get("cer"),
            "cer_lo": (r.get("scores") or {}).get(HEADLINE, {}).get("cer_lo"),
            "cer_hi": (r.get("scores") or {}).get(HEADLINE, {}).get("cer_hi"),
            "ms_per_line": r.get("ms_per_line"),
            "n_lines": r.get("n_lines"),
            "status": r.get("status"),
        }
    models = {}
    for key in K3_MODELS:
        d = dres.get(key) or {}
        models[key] = {
            "pool": pool_rows(k3_pool, key),
            "validation": val_breakdowns.get(key),
            "dresden": d or None,
            "speed": projection(d.get("ms_per_line")),
            "trained": trained.get(key) or {},
        }
    baselines = {
        key: {"pool": pool_rows(k2b_pool, key), "dresden": dres.get(key)} for key in K2B_READERS
    }
    return {
        "generated": date.today().isoformat(),
        "headline_policy": HEADLINE,
        "models": models,
        "baselines": baselines,
        "disagreements": disagreements,
        "choice": choice(models),
        "trainset": {
            "train_lines": ((trainset or {}).get("splits") or {}).get("train", {}).get("lines"),
            "val_lines": ((trainset or {}).get("splits") or {}).get("val", {}).get("lines"),
            "screen": (trainset or {}).get("screen"),
        },
        "ppocr_pilot": ppocr_pilot,
        "ablation": ablation_note,
        "k2_throughput": {"lines": K2_LINES, "wall_s": K2_WALL_S, "model_s": K2_MODEL_S},
    }


def _cerci(block: Mapping | None) -> str:
    if not block or block.get("cer") is None:
        return "—"
    s = _pct(block["cer"], 1)
    if block.get("cer_lo") is not None:
        s += f" ({_pct(block['cer_lo'], 1)}–{_pct(block['cer_hi'], 1)})"
    return s


def render_eval(s: Mapping) -> str:
    L: list[str] = [
        "# K3: the evaluation, and the choice for K4",
        "",
        "Two Leibniz Kurrent models fine-tuned on K2's German mint "
        f"({_n(s['trainset']['train_lines'])} training lines; "
        f"{_n(s['trainset']['val_lines'])} validation lines, page-disjoint, for the "
        "checkpoints), measured where nothing was tuned: the GWLB letter pool (K2b's frozen set, "
        "its metric and code: the letter's reference against every recognised line on its pages, "
        "nothing filtered; CC BY-NC 4.0, numbers only), Dresden as a sanity check, the validation "
        f"set for the composition of the errors. CER under the `{s['headline_policy']}` policy "
        f"with 95 % bootstrap intervals over letters. Generated {s['generated']}.",
        "",
        "## The letter pool",
        "",
        "| reader | all 134 letters | selection half | test half | Leibniz's hand (L) "
        "| the correspondents' (K/k) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key in K2B_READERS:
        p = (s["baselines"].get(key) or {}).get("pool")
        if not p:
            continue
        L.append(
            f"| {key} (K2b) | {_cerci(p['all'])} | {_cerci(p['selection'])} | "
            f"{_cerci(p['test'])} | "
            f"{_cerci((p['hand'] or {}).get('L'))} | {_cerci((p['hand'] or {}).get('K/k'))} |"
        )
    for key in K3_MODELS:
        p = (s["models"][key] or {}).get("pool")
        if not p:
            L.append(f"| **{key}** | not read yet | | | | |")
            continue
        L.append(
            f"| **{key}** | **{_cerci(p['all'])}** | **{_cerci(p['selection'])}** | "
            f"**{_cerci(p['test'])}** | "
            f"{_cerci((p['hand'] or {}).get('L'))} | {_cerci((p['hand'] or {}).get('K/k'))} |"
        )
    years = sorted(
        {
            y
            for key in K3_MODELS
            for y in (((s["models"][key] or {}).get("pool") or {}).get("year") or {})
        }
    )
    if years:
        L += [
            "",
            "By year (the K3 models; letters per year as K2b drew them):",
            "",
            "| year | " + " | ".join(K3_MODELS) + " |",
            "|---|" + "---:|" * len(K3_MODELS),
        ]
        for y in years:
            L.append(
                f"| {y} | "
                + " | ".join(
                    _cerci(((s["models"][k].get("pool") or {}).get("year") or {}).get(y))
                    for k in K3_MODELS
                )
                + " |"
            )
    L += [
        "",
        "## The validation set (the mint's own text as reference)",
        "",
        "| model | CER (95 %) | Leibniz's hand | other hands | heavy | light | scrap "
        "| reader rows | v1 rows | sub / ins / del | tax |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for key in K3_MODELS:
        v = s["models"][key].get("validation")
        if not v:
            L.append(f"| {key} | — | | | | | | | | | |")
            continue
        b = v["breakdown"]
        o = b["overall"]
        by = b["by"]
        ci = v.get("bootstrap") or {}
        g = lambda d, k: _pct((d.get(k) or {}).get("cer"), 1)  # noqa: E731
        L.append(
            f"| {key} | {_pct(o['cer'], 2)} ({_pct(ci.get('cer_lo'), 2)}–"
            f"{_pct(ci.get('cer_hi'), 2)}) | {g(by['group'], 'leibniz')} | "
            f"{g(by['group'], 'other')} | {g(by['stratum'], 'heavy_revision')} | "
            f"{g(by['stratum'], 'light_revision')} | {g(by['stratum'], 'scrap')} | "
            f"{g(by['reader'], 'trocr-kurrent-xvi-xvii')} | {g(by['reader'], 'v1')} | "
            f"{_pct(o['sub_share'], 0)} / {_pct(o['ins_share'], 0)} / {_pct(o['del_share'], 0)} | "
            f"{100 * (v.get('tax') or {}).get('tax', 0):.1f} pts |"
        )
    d = s.get("disagreements")
    if d:
        L += [
            "",
            f"Where the two models disagree on a validation line ({_n(d['disagree'])} of "
            f"{_n(d['lines'])}), one of them is exactly right on {_pct(d['either_share'], 1)} "
            f"(k3-trocr {_n(d['a_exact'])}, k3-kraken {_n(d['b_exact'])}) — the number the C3 "
            "amendment asks for.",
        ]
    L += [
        "",
        "## Dresden (a chancery hand, a sanity check; nc, numbers only)",
        "",
        "| reader | CER (95 %) | ms a line |",
        "|---|---:|---:|",
    ]
    for key in list(K2B_READERS) + list(K3_MODELS):
        dr = (
            (s["baselines"].get(key) or {}).get("dresden")
            if key in K2B_READERS
            else (s["models"][key] or {}).get("dresden")
        )
        if dr:
            L.append(f"| {key} | {_cerci(dr)} | {_f(dr.get('ms_per_line'), 0)} |")
    L += [
        "",
        "## Speed, and the time to read every German page",
        "",
        "| model | ms a line (model, Dresden, as K1 measured) "
        "| all-in ms a line (K2's overhead added) | K2's 310,831 lines |",
        "|---|---:|---:|---:|",
    ]
    for key in K3_MODELS:
        sp = s["models"][key].get("speed")
        if sp:
            L.append(
                f"| {key} | {_f(sp['ms_per_line_model'], 0)} | "
                f"{_f(sp['ms_per_line_all_in'], 0)} | {_hours(sp['hours'])} |"
            )
    c = s["choice"]
    L += ["", "## The choice for K4", "", c["rule"] + ".", ""]
    if c.get("winner"):
        L += [
            f"- Best selection-half CER: **{c['best_cer']['model']}** at "
            f"{_pct(c['best_cer']['cer'], 1)} ({_pct(c['best_cer']['cer_lo'], 1)}–"
            f"{_pct(c['best_cer']['cer_hi'], 1)}); the runner-up "
            f"{c['runner_up']['model']} at {_pct(c['runner_up']['cer'], 1)}.",
            f"- The faster model: **{c['faster']['model']}** "
            f"({_f(c['faster']['ms_per_line'], 0)} ms a line); "
            f"within the margin ({_pct(c['margin'], 1) if c['margin'] is not None else '—'}): "
            f"**{'yes' if c['faster_within_margin'] else 'no'}**.",
            f"- **The rule's answer: {c['winner']}.** The choice is the operator's; recorded in "
            "STATUS.md.",
        ]
    pp = s.get("ppocr_pilot")
    if pp:
        L += [
            "",
            "## PP-OCRv6 (the amendment's other base), the pilot only",
            "",
            f"One epoch over {_n(pp.get('pilot_lines'))} lines in "
            f"{_hours((pp.get('run_seconds') or 0) / 3600)} at batch 1 with 16-step accumulation, "
            f"peak {_n(pp.get('peak_mib'))} MiB; kraken's validation accuracy "
            f"{_f((pp.get('checkpoints') or [{}])[-1].get('val_metric'), 4)} against the PHILIUMM "
            "pilot's 0.7676 after its epoch; the project's validation CER "
            f"{_pct((pp.get('score') or {}).get('cer'), 2)}. Trained on the Dresdner Hofdiarium, "
            "so Dresden cannot rank it; not trained in full in this round.",
        ]
    if s.get("ablation"):
        L += ["", "## The ablation", "", s["ablation"]]
    L += [
        "",
        "## What this is not",
        "",
        "- The precision of the training lines is unmeasured (K2's audit sheet awaits its "
        "judge); the "
        "screen's figures are in `k3-trainset.md`.",
        "- The validation set is the mint's own text, so its numbers carry the mint's "
        "conventions; the "
        "letter pool is the honest German error rate.",
        "",
    ]
    return "\n".join(L)


def write_eval(s: Mapping, reports_dir: Path | str = DEFAULT_REPORTS_DIR) -> dict[str, Path]:
    d = Path(reports_dir)
    d.mkdir(parents=True, exist_ok=True)
    md, js = d / "k3-eval.md", d / "k3-eval.json"
    md.write_text(render_eval(s), encoding="utf-8")
    js.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"md": md, "json": js}


def card_inputs(ev: Mapping, key: str, *, trainset: Mapping | None, licence: str = "open") -> dict:
    """What :func:`render_model_card` wants, from the evaluation JSON and the training set."""
    m = ev["models"][key]
    pool = m.get("pool") or {}
    tr = m.get("trained") or {}
    hist = tr.get("history") or []
    best = None
    for h in hist:
        if h.get("cer") is not None and (best is None or h["cer"] < best["cer"]):
            best = h
    if key == "k3-trocr":
        trained = {
            "train_lines": ev["trainset"].get("train_lines"),
            "val_lines": ev["trainset"].get("val_lines"),
            "settings_key": (tr.get("settings") or {}).get("key"),
            "epochs": tr.get("epoch"),
            "best_epoch": best["epoch"] if best else None,
            "best_cer": best["cer"] if best else None,
            "hours": sum(h.get("seconds", 0) + h.get("val_seconds", 0) for h in hist) / 3600.0
            if hist
            else None,
        }
    else:
        cks = tr.get("checkpoints") or []
        trained = {
            "train_lines": tr.get("pilot_lines") or ev["trainset"].get("train_lines"),
            "val_lines": ev["trainset"].get("val_lines"),
            "settings_key": (tr.get("settings") or {}).get("key"),
            "epochs": (cks[-1]["epoch"] + 1) if cks else None,
            "best_epoch": cks[-1]["epoch"] if cks else None,
            "best_cer": (tr.get("score") or {}).get("cer"),
            "hours": (tr.get("run_seconds") or 0) / 3600.0 if tr.get("run_seconds") else None,
        }
    hand = pool.get("hand") or {}
    sp = m.get("speed") or {}
    return {
        "key": "trocr" if key == "k3-trocr" else "kraken",
        "version": key,
        "path": "data/models/k3/trocr/best"
        if key == "k3-trocr"
        else "data/models/k3/kraken/best.safetensors",
        "trained": trained,
        "trainset": trainset or {},
        "letterpool": {
            "all": pool.get("all"),
            "test": pool.get("test"),
            "L": hand.get("L"),
            "K/k": hand.get("K/k"),
        },
        "validation": (m.get("validation") or {}).get("breakdown"),
        "dresden": (
            {
                "cer": m["dresden"].get("cer"),
                "note": "a 1673 chancery hand; a ranking, not a benchmark",
            }
            if m.get("dresden")
            else None
        ),
        "speed": {"ms_per_line": sp.get("ms_per_line_model"), "german_hours": sp.get("hours")},
        "licence": licence,
        "precision_note": "K2's 200-line audit sheet (half in Leibniz's own hand) awaits its judge "
        "at the Leibniz-Edition; no verdict existed when this model was trained.",
    }


def write_cards(
    ev: Mapping,
    *,
    trainset: Mapping | None,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
    licence: str = "open",
) -> dict[str, Path]:
    d = Path(reports_dir)
    d.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for key in K3_MODELS:
        if not ev["models"].get(key):
            continue
        p = d / f"k3-model-card-{key.removeprefix('k3-')}.md"
        p.write_text(
            render_model_card(card_inputs(ev, key, trainset=trainset, licence=licence)),
            encoding="utf-8",
        )
        out[key] = p
    return out


def write_pilots(s: Mapping, reports_dir: Path | str = DEFAULT_REPORTS_DIR) -> dict[str, Path]:
    d = Path(reports_dir)
    d.mkdir(parents=True, exist_ok=True)
    md = d / "k3-pilots.md"
    js = d / "k3-pilots.json"
    md.write_text(render_pilots(s), encoding="utf-8")
    js.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"md": md, "json": js}


def count_lines(path: Path | str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    return sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip())


__all__ = [
    "BASES",
    "K2B_READERS",
    "K3_MODELS",
    "build_eval",
    "card_inputs",
    "choice",
    "pool_rows",
    "projection",
    "render_eval",
    "write_cards",
    "write_eval",
    "WEEK_HOURS",
    "render_model_card",
    "build_pilots",
    "count_lines",
    "kraken_pilot_summary",
    "load_json",
    "render_pilots",
    "trocr_pilot_summary",
    "write_pilots",
]
