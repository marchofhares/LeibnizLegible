"""The K4 reading report: what the job and the import did, in numbers (K4, Task 4).

One page of numbers for ``reports/kurrent/k4-reading.md`` (and ``.json``),
gathered from the files the job and the import leave behind, never from the
store: the job's stats file (``<reader>.stats.json`` beside the readings),
its log (the launches, relaunches and exits of ``run-read.sh``, and
``/usr/bin/time -v``'s peak resident set per launch), the guard's CSV (the
card's peak, the host's floor, any kill) and the import's summary JSON
(rows by collection, the empty readings, the narrow crops the operator's
decision of 28 October asked to count for K3b). The page-language table of
Checkpoint A stays in ``reports/kurrent/page-lang.md``; this report links
it.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_OUT = Path("reports/kurrent/k4-reading.md")

_RSS = re.compile(r"Maximum resident set size \(kbytes\): (\d+)")
_WALL = re.compile(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)")
_EXIT = re.compile(r"^READ-EXIT (\d+) launch (\d+) (\S+)")
_LAUNCH = re.compile(r"^# launch (\d+) (\S+)")
_RELAUNCH = re.compile(r"^# relaunch (\d+) of (\d+) in 60 s after exit (\d+) (\S+)")
_DONE = re.compile(r"^READ-DONE exit (\d+) after (\d+) launch\(es\) (\S+)")


@dataclass(slots=True)
class JobLog:
    """What ``run-read.sh`` and ``/usr/bin/time -v`` wrote to the job's log."""

    launches: list[str] = field(default_factory=list)  # timestamps
    relaunches: list[dict] = field(default_factory=list)  # {n, after_exit, at}
    exits: list[dict] = field(default_factory=list)  # {code, launch, at}
    max_rss_kb: list[int] = field(default_factory=list)  # per launch that ended on its own
    wall: list[str] = field(default_factory=list)  # /usr/bin/time's h:mm:ss, the same launches
    done: dict | None = None  # {code, launches, at}
    first_progress: str | None = None
    last_progress: str | None = None

    @property
    def peak_rss_kb(self) -> int | None:
        return max(self.max_rss_kb) if self.max_rss_kb else None

    def as_dict(self) -> dict:
        return {
            "launches": self.launches,
            "relaunches": self.relaunches,
            "exits": self.exits,
            "max_rss_kb": self.max_rss_kb,
            "peak_rss_kb": self.peak_rss_kb,
            "wall": self.wall,
            "done": self.done,
            "first_progress": self.first_progress,
            "last_progress": self.last_progress,
        }


def read_job_log(path: Path | str) -> JobLog:
    out = JobLog()
    p = Path(path)
    if not p.exists():
        return out
    prev = ""
    with p.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if m := _LAUNCH.match(line):
                out.launches.append(m.group(2))
            elif m := _RELAUNCH.match(line):
                out.relaunches.append(
                    {"n": int(m.group(1)), "after_exit": int(m.group(3)), "at": m.group(4)}
                )
            elif m := _EXIT.match(line):
                out.exits.append(
                    {"code": int(m.group(1)), "launch": int(m.group(2)), "at": m.group(3)}
                )
            elif m := _DONE.match(line):
                out.done = {"code": int(m.group(1)), "launches": int(m.group(2)), "at": m.group(3)}
            elif m := _RSS.search(line):
                out.max_rss_kb.append(int(m.group(1)))
            elif m := _WALL.search(line):
                out.wall.append(m.group(1))
            elif " lines/h · " in line:
                # the job's log wraps a progress line over two physical lines
                text = line.strip()
                if "lines done" not in text and "lines done" in prev:
                    text = prev.strip() + " " + text
                text = text.split("; stats", 1)[0]
                if out.first_progress is None:
                    out.first_progress = text
                out.last_progress = text
            prev = line
    return out


@dataclass(slots=True)
class GuardSummary:
    """The guard's CSV: samples of the card and the host while the job ran."""

    samples: int = 0
    peak_used_mib: int | None = None
    mean_util_pct: float | None = None
    min_avail_mib: int | None = None
    kills: list[str] = field(default_factory=list)
    starts: int = 0

    def as_dict(self) -> dict:
        return {
            "samples": self.samples,
            "peak_used_mib": self.peak_used_mib,
            "mean_util_pct": self.mean_util_pct,
            "min_avail_mib": self.min_avail_mib,
            "kills": self.kills,
            "starts": self.starts,
        }


def read_guard_csv(path: Path | str) -> GuardSummary:
    out = GuardSummary()
    p = Path(path)
    if not p.exists():
        return out
    utils: list[float] = []
    with p.open(encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.reader(fh):
            if not row:
                continue
            if row[0].startswith("# guard kill"):
                out.kills.append(",".join(row).strip())
                continue
            if row[0].startswith("# guard start"):
                out.starts += 1
                continue
            if row[0].startswith("#"):
                continue
            try:
                used, util, avail = int(row[1]), float(row[2]), int(row[3])
            except (IndexError, ValueError):
                continue
            out.samples += 1
            out.peak_used_mib = used if out.peak_used_mib is None else max(out.peak_used_mib, used)
            out.min_avail_mib = (
                avail if out.min_avail_mib is None else min(out.min_avail_mib, avail)
            )
            utils.append(util)
    if utils:
        out.mean_util_pct = round(sum(utils) / len(utils), 1)
    return out


def _load(path: Path | str | None) -> dict:
    if path is None:
        return {}
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def gather(
    *,
    stats_path: Path | str | None,
    log_path: Path | str | None,
    guard_path: Path | str | None,
    import_summary_path: Path | str | None,
    page_lang_path: Path | str | None = None,
    store_before: int | None = None,
    today: str = "",
) -> dict:
    """Everything the report prints, as one JSON-ready dict."""
    stats = _load(stats_path)
    imp = _load(import_summary_path)
    pl = _load(page_lang_path)
    chosen = pl.get("chosen") or {}
    coverage = (
        {
            "threshold": chosen.get("key"),
            "precision": chosen.get("precision"),
            "recall": chosen.get("recall"),
            "german_pages": pl.get("german_pages"),
            "pages": pl.get("pages"),
        }
        if pl
        else {}
    )
    log = read_job_log(log_path) if log_path else JobLog()
    guard = read_guard_csv(guard_path) if guard_path else GuardSummary()
    return {
        "date": today,
        "job": stats,
        "log": log.as_dict(),
        "guard": guard.as_dict(),
        "import": imp,
        "coverage": coverage,
        "store_before": store_before,
    }


def _n(x) -> str:
    return "—" if x is None else f"{x:,}"


def _pct(x) -> str:
    return "—" if x is None else f"{float(x) * 100:.1f} %"


def _hours(seconds) -> str:
    if not seconds:
        return "—"
    h = float(seconds) / 3600.0
    return f"{h:.1f} h"


def _pace(job: Mapping) -> str:
    ms, lph = job.get("ms_per_line"), job.get("lines_per_hour")
    left = f"{ms:.1f} ms a line" if ms else "—"
    right = f"{lph:,.0f} lines/h" if lph else "—"
    return f"{left} · {right}"


def render(summ: Mapping) -> str:
    job, log, guard, imp = summ["job"], summ["log"], summ["guard"], summ["import"]
    L: list[str] = []
    a = L.append

    def row(label: str, value: object) -> None:
        a(f"| {label} | {value} |")

    a("# K4 — the German pages read by READER, and written beside v1")
    a("")
    a(
        f"Generated {summ.get('date') or '—'}. The page-language pass and its measure "
        "(pages by language, the threshold, precision and recall) are in "
        "`reports/kurrent/page-lang.md`; the cost of reading mixed pages whole is in "
        "`reports/kurrent/k4-mixed-letters.md`."
    )
    a("")
    a("## The reading job")
    a("")
    if job:
        settings = job.get("settings") or {}
        skipped = job.get("skipped") or {}
        a("| | |")
        a("|---|---:|")
        row("reader · model", f"{job.get('reader', '—')} · {job.get('model', '—')}")
        row(
            "device · batch · cache",
            f"{job.get('device', '—')} · {_n(settings.get('batch_size'))} · "
            f"{settings.get('use_cache', '—')}",
        )
        row("pages", f"{_n(job.get('pages_done'))} of {_n(job.get('pages_total'))}")
        row("lines on them", _n(job.get("lines_total")))
        row("lines read (this file)", _n(job.get("lines_done")))
        row("of which in the last launch", _n(job.get("lines_read")))
        reasons = ", ".join(f"{k} {v:,}" for k, v in skipped.items()) or "none"
        row("skipped", f"{_n(job.get('n_skipped'))} ({reasons})")
        row("pace (last launch)", _pace(job))
        row(
            "wall (last launch)",
            f"{_hours(job.get('seconds'))} (in the engine {_hours(job.get('model_seconds'))})",
        )
        row(
            "started · updated · finished",
            f"{job.get('started', '—')} · {job.get('updated', '—')} · {job.get('finished', '—')}",
        )
    else:
        a("(no stats file)")
    cov = summ.get("coverage") or {}
    if cov:
        a("")
        a(
            f"**What the re-read covers.** The job's pages are the German pages the language "
            f"pass over the machine text found (`leibniz enrich page-lang`, threshold "
            f"{cov.get('threshold')}; on the census's pieces precision "
            f"{_pct(cov.get('precision'))}, recall {_pct(cov.get('recall'))}, so about three "
            f"quarters of the German pages by that measure; {_n(cov.get('german_pages'))} pages "
            f"called German of {_n(cov.get('pages'))}, the printed Marginalien left out of the "
            f"job). A German page the pass missed keeps v1's text (the operator, 28 October); "
            f"a second pass is the next round's item (STATUS.md, Next)."
        )
    a("")
    a("### Launches, memory, the guard")
    a("")
    a("| | |")
    a("|---|---:|")
    row("launches · relaunches", f"{len(log['launches'])} · {len(log['relaunches'])}")
    if log["relaunches"]:
        row("relaunched after exits", ", ".join(str(r["after_exit"]) for r in log["relaunches"]))
    exits = ", ".join(f"{e['code']}@{e['launch']}" for e in log["exits"]) or "—"
    row("exits (code, launch)", exits)
    # the guard's pkill -f matches the time wrapper too: a killed launch leaves no summary
    row(
        "peak host RSS (`/usr/bin/time -v`, launches that ended on their own)",
        f"{_n(log['peak_rss_kb'])} KB",
    )
    row("wall per launch that ended on its own", ", ".join(log["wall"]) or "—")
    row("guard samples · starts", f"{_n(guard['samples'])} · {guard['starts']}")
    row("card peak (nvidia-smi, Xwayland included)", f"{_n(guard['peak_used_mib'])} MiB")
    util = guard["mean_util_pct"]
    row("GPU utilisation, mean", f"{'—' if util is None else util} %")
    row("host MemAvailable, minimum", f"{_n(guard['min_avail_mib'])} MiB")
    row("guard kills", len(guard["kills"]))
    if log["first_progress"]:
        a("")
        a(f"First progress line: `{log['first_progress']}`")
    if log["last_progress"]:
        a("")
        a(f"Last progress line: `{log['last_progress']}`")
    a("")
    a("## The write (Task 4)")
    a("")
    if imp:
        a("| | |")
        a("|---|---:|")
        row(
            "run",
            f"{_n(imp.get('run_id'))} (stage recognize, model {imp.get('model', '—')}, "
            f"scope {imp.get('scope', '—')})",
        )
        row(
            "pages in the list",
            f"{_n(imp.get('pages'))} (without readings {_n(imp.get('pages_without_readings'))})",
        )
        row("lines considered", _n(imp.get("lines")))
        row(
            "rows written",
            f"{_n(imp.get('rows_written'))} on {_n(imp.get('pages_written'))} pages",
        )
        row("empty readings (no row)", _n(imp.get("empty_readings")))
        row("lines without a reading", _n(imp.get("lines_without_reading")))
        row("orphan readings", _n(imp.get("orphan_readings")))
        row(
            f"crops under {imp.get('narrow_px', 80)} px",
            f"{_n(imp.get('narrow_lines'))} lines, {_n(imp.get('narrow_rows'))} of them with a row",
        )
        under = imp.get("under_run")
        if under:
            row("under the run after", f"{_n(under[0])} pages, {_n(under[1])} rows")
        store = imp.get("store") or {}
        if store:
            before = summ.get("store_before")
            grown = f" (+{store['db'] - before:,} bytes)" if before else ""
            row("store after", f"{_n(store.get('db'))} bytes{grown}, WAL {_n(store.get('wal'))}")
        by = imp.get("by_set") or {}
        if by:
            a("")
            a("| collection | pages | lines | rows | crops under 80 px |")
            a("|---|---:|---:|---:|---:|")
            for name, t in sorted(by.items()):
                a(
                    f"| {name or '(no set)'} | {_n(t.get('pages'))} | {_n(t.get('lines'))} | "
                    f"{_n(t.get('rows'))} | {_n(t.get('narrow_lines'))} |"
                )
        a("")
        a(
            "Every non-empty reading got a row, the narrow crops included (the operator's "
            "decision of 28 October): the letter-pool number was measured on all crops, and "
            "one run per page keeps K3b's replacement simple. The narrow crops are "
            "segmentation fragments either way — READER returns a single character on most of "
            "them — and their count is Open question 32 for K3b's segmentation measurement "
            "(STATUS.md)."
        )
    else:
        a("(not written yet)")
    a("")
    return "\n".join(L)


def write_report(summ: Mapping, *, out: Path | str = DEFAULT_OUT) -> dict[str, Path]:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    js = out.with_suffix(".json")
    out.write_text(render(summ), encoding="utf-8")
    js.write_text(json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"md": out, "json": js}


__all__ = [
    "DEFAULT_OUT",
    "GuardSummary",
    "JobLog",
    "gather",
    "read_guard_csv",
    "read_job_log",
    "render",
    "write_report",
]
