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
from collections.abc import Mapping
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
        "resized": (account.get("log") or {}).get("resized"),
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
    train_lines: int,
    val_lines: int,
    plan_epochs_trocr: float,
    plan_epochs_kraken: int,
    rented_note: str = "",
) -> dict:
    t = trocr_pilot_summary(trocr, plan_epochs=plan_epochs_trocr)
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
    "WEEK_HOURS",
    "build_pilots",
    "count_lines",
    "kraken_pilot_summary",
    "load_json",
    "render_pilots",
    "trocr_pilot_summary",
    "write_pilots",
]
