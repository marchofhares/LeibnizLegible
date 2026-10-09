"""Bootstrap readers for Kurrent, smoke-tested on Dresden (Phase K1, Task 3).

The German stratum of the Nachlass has no ground truth, so no reader can be
*benchmarked* on it yet. What can be done is a ranking on the nearest public
Kurrent that exists: the Dresdner Hofdiarium 1673 lines of the Kurrent Trace
package (Stefan Beckert's ground truth, a chancery hand of Leibniz's own
decades, 383 pixel-exact line crops). Every candidate reader — the TrOCR
Kurrent fine-tunes from the Hub, McCATMuS from Zenodo, the project's PHILIUMM
baseline — reads the same 383 lines once; the raw output is cached under
``data/kurrent/smoke/`` and scored by the B1 harness under its three
normalisation policies (the Dresden conventions keep u/v as written and
distinguish the long s, so the policies that fold case and diacritics still
charge both), and by the package's own two scores (strict NFC; a reading
policy with the long s folded to s and whitespace collapsed), reimplemented
here on the same edit distance and, where the package's script is present,
run as well.

**This is a ranking, not a benchmark.** The Dresden lines are public and may
sit in a candidate's training set; the hand is a chancery's, not Leibniz's;
the number that matters for K2 is the pilot's German yield on Leibniz's own
pages (Task 4). The Dresden text is nc-bucket material (the package applies
CC BY-NC-SA 4.0 while Zenodo's field says CC BY 4.0): it is read for
scoring and never written into a committed report — the report carries
numbers, the per-line dumps stay under ``data/``.

Imports of the heavy stacks are lazy; the tests run the whole chain on the
``echo`` candidate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from leibniz.htr import bench, data, metrics
from leibniz.htr.bench import LinePair
from leibniz.htr.metrics import edit_distance

DEFAULT_PACKAGE = Path("data/external/kurrent-trace/Kurrent-Trace-v0.1")
DEFAULT_SMOKE_DIR = Path("data/kurrent/smoke")
DEFAULT_REPORTS_DIR = Path("reports/kurrent")
MCCATMUS_DIR = Path("data/models/mccatmus")
MCCATMUS_FILE = "McCATMuS_nfd_nofix_V1.mlmodel"
MCCATMUS_URL = f"https://zenodo.org/records/13788177/files/{MCCATMUS_FILE}?download=1"
PHILIUMM_MODEL = Path("data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors")
VISION_SUBSAMPLE = 150
VISION_SEED = 12345


@dataclass(frozen=True, slots=True)
class Candidate:
    """One reader under test: where it comes from and under what licence."""

    key: str
    kind: str  # kraken | trocr | echo
    source: str  # a model path (kraken) or a Hub repo id (trocr)
    licence: str
    origin: str
    note: str
    default: bool = True  # run when no --candidates is given


CANDIDATES: dict[str, Candidate] = {
    c.key: c
    for c in (
        Candidate(
            "philiumm",
            "kraken",
            str(PHILIUMM_MODEL),
            "CC BY 4.0",
            "Zenodo 10.5281/zenodo.21457538",
            "the project's baseline: FoNDUE-GD_v2 fine-tuned on Leibniz's Latin and French",
        ),
        Candidate(
            "mccatmus",
            "kraken",
            str(MCCATMUS_DIR / MCCATMUS_FILE),
            "CC BY 4.0",
            "Zenodo 10.5281/zenodo.13788177",
            "McCATMuS v1: 22 datasets, mostly French, some German; 16th–21st c.; CoreML",
        ),
        Candidate(
            "trocr-kurrent-xvi-xvii",
            "trocr",
            "dh-unibe/trocr-kurrent-XVI-XVII",
            "MIT",
            "https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII",
            "German Kurrent of the 16th–18th c., Swiss-biased; the card reports test CER 5.4 %",
        ),
        Candidate(
            "trocr-hanse-xvii",
            "trocr",
            "fgho/trocr-hanseXVII-kurrent",
            "none stated",
            "https://huggingface.co/fgho/trocr-hanseXVII-kurrent",
            "17th-c. north German administrative records; from the Bern model; evaluate only",
        ),
        Candidate(
            "trocr-hanse-xvi",
            "trocr",
            "fgho/trocr-hanseXVI-kurrent",
            "none stated",
            "https://huggingface.co/fgho/trocr-hanseXVI-kurrent",
            "16th-c. north German administrative records; from the Bern model; evaluate only",
        ),
        Candidate(
            "trocr-kurrent-xix",
            "trocr",
            "dh-unibe/trocr-kurrent",
            "MIT",
            "https://huggingface.co/dh-unibe/trocr-kurrent",
            "the 19th-century base of the XVI–XVII model; a reference, off by default",
            default=False,
        ),
        Candidate("echo", "echo", "", "—", "", "the offline stub the tests run", default=False),
    )
}


# --------------------------------------------------------------------------- #
# The Dresden set
# --------------------------------------------------------------------------- #


def load_dresden(
    package_dir: Path | str = DEFAULT_PACKAGE, *, limit: int | None = None
) -> list[LinePair]:
    """The package's published lines as bench pairs, in file order.

    ``data/published_gt.jsonl`` carries the text and the crop path per line; the
    crops and the labels sit in separate trees, which the image-plus-sidecar
    loader would never pair, hence this loader.
    """
    root = Path(package_dir)
    records = root / "data" / "published_gt.jsonl"
    if not records.exists():
        raise FileNotFoundError(f"no published_gt.jsonl under {root}")
    pairs: list[LinePair] = []
    with records.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            pairs.append(
                LinePair(
                    line_id=str(rec["id"]),
                    reference=str(rec["text"]),
                    image_path=root / rec["image_path"],
                    lang=rec.get("language_hint") or "de",
                    meta={
                        "page_id": rec.get("page_id"),
                        "document_id": rec.get("document_id"),
                        "licence": rec.get("annotation_license_applied"),
                    },
                )
            )
            if limit is not None and len(pairs) >= limit:
                break
    return pairs


def package_summary(package_dir: Path | str = DEFAULT_PACKAGE) -> dict:
    """The package's own dataset summary (counts and the licence conflict), if present."""
    path = Path(package_dir) / "reports" / "dataset-summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The package's two scores, reimplemented on the project's edit distance
# --------------------------------------------------------------------------- #


def package_strict(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def package_reading(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).replace("ſ", "s").split())


PACKAGE_POLICIES: dict[str, Callable[[str], str]] = {
    "strict_nfc": package_strict,
    "reading_long_s_and_whitespace": package_reading,
}


def package_scores(pairs: Sequence[LinePair], hyps: Sequence[str]) -> dict[str, dict]:
    """Micro-averaged CER and WER and exact lines under the package's two policies."""
    out: dict[str, dict] = {}
    for name, fn in PACKAGE_POLICIES.items():
        ce = cn = we = wn = exact = 0
        for pair, hyp in zip(pairs, hyps, strict=True):
            ref, h = fn(pair.reference), fn(hyp)
            ce += edit_distance(ref, h)
            cn += len(ref)
            we += edit_distance(ref.split(), h.split())
            wn += len(ref.split())
            exact += int(ref == h)
        out[name] = {
            "cer": ce / cn if cn else 0.0,
            "wer": we / wn if wn else 0.0,
            "exact_lines": exact,
            "character_edits": ce,
            "reference_characters": cn,
        }
    return out


def run_package_script(
    package_dir: Path | str, predictions: Path, *, python: str = sys.executable
) -> dict | None:
    """Run the package's own ``scripts/evaluate.py`` on a predictions file, if it exists.

    The script is untrusted data: it runs in isolated mode (``-I``) from the
    package directory and only its JSON output is read. ``None`` when the
    script is absent or fails.
    """
    script = Path(package_dir) / "scripts" / "evaluate.py"
    if not script.exists():
        return None
    try:
        proc = subprocess.run(
            [python, "-I", str(script), str(Path(predictions).resolve())],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------- #
# Engines
# --------------------------------------------------------------------------- #


def fetch_mccatmus(dest_dir: Path | str = MCCATMUS_DIR) -> Path:
    """The McCATMuS CoreML model from Zenodo (cache-first; 16 MB)."""
    from leibniz.htr.artifacts import download_file

    return download_file(MCCATMUS_URL, Path(dest_dir) / MCCATMUS_FILE)


def build_engine(cand: Candidate, *, device: str = "cpu", batch_size: int = 8):
    """The reader for a candidate; heavy stacks imported here, lazily."""
    if cand.kind == "kraken":
        from leibniz.htr.engines import KrakenEngine

        path = cand.source
        if cand.key == "mccatmus" and not Path(path).exists():
            fetch_mccatmus(Path(path).parent)
        return KrakenEngine(path, version=cand.key, device=device, batch_size=batch_size)
    if cand.kind == "trocr":
        from leibniz.htr.trocr import TrOCREngine

        return TrOCREngine(cand.source, device=device, batch_size=batch_size)
    if cand.kind == "echo":
        return bench.EchoEngine(default="")
    raise ValueError(f"unknown candidate kind {cand.kind!r}")


def pick_device(requested: str = "auto") -> str:
    """``cuda`` when torch sees a GPU, else ``cpu``; an explicit request is kept."""
    if requested != "auto":
        return requested
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ModuleNotFoundError:
        return "cpu"


# --------------------------------------------------------------------------- #
# One candidate: read (cached), score
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class CandidateResult:
    """What one reader did on the set."""

    key: str
    kind: str
    source: str
    licence: str
    origin: str
    note: str
    engine_name: str = ""
    engine_version: str = ""
    device: str = ""
    n_lines: int = 0
    seconds: float = 0.0
    cached: bool = False
    status: str = "ok"  # ok | skipped:<reason>
    n_empty: int = 0
    mean_conf: float | None = None
    scores: dict[str, dict] = field(default_factory=dict)  # B1 policy → cer/wer with CIs
    package: dict[str, dict] = field(default_factory=dict)  # the package's two policies
    package_script: dict | None = None  # the package's own script, where it ran

    @property
    def ms_per_line(self) -> float | None:
        return 1000.0 * self.seconds / self.n_lines if self.n_lines else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d["ms_per_line"] = self.ms_per_line
        return d


def _hyps_paths(smoke_dir: Path, key: str) -> tuple[Path, Path]:
    return smoke_dir / f"{key}.hyps.jsonl", smoke_dir / f"{key}.meta.json"


def load_cached_hyps(
    smoke_dir: Path, key: str, pairs: Sequence[LinePair]
) -> tuple[list[str], list[float | None], dict] | None:
    """Cached raw readings aligned to ``pairs`` by line id, or ``None`` if incomplete."""
    hyps_path, meta_path = _hyps_paths(smoke_dir, key)
    if not hyps_path.exists() or not meta_path.exists():
        return None
    by_id: dict[str, tuple[str, float | None]] = {}
    for raw in hyps_path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            row = json.loads(raw)
            by_id[row["line_id"]] = (row["hyp"], row.get("conf"))
    if not all(p.line_id in by_id for p in pairs):
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return [by_id[p.line_id][0] for p in pairs], [by_id[p.line_id][1] for p in pairs], meta


def save_hyps(
    smoke_dir: Path,
    key: str,
    pairs: Sequence[LinePair],
    hyps: Sequence[str],
    confs: Sequence[float | None],
    meta: dict,
) -> None:
    smoke_dir.mkdir(parents=True, exist_ok=True)
    hyps_path, meta_path = _hyps_paths(smoke_dir, key)
    with hyps_path.open("w", encoding="utf-8") as fh:
        for p, h, c in zip(pairs, hyps, confs, strict=True):
            fh.write(
                json.dumps({"line_id": p.line_id, "hyp": h, "conf": c}, ensure_ascii=False) + "\n"
            )
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def read_with(engine, pairs: Sequence[LinePair]) -> tuple[list[str], list[float | None], float]:
    """Run an engine over the pairs once: texts, confidences (where offered), seconds."""
    images = [p.image_bytes() for p in pairs]
    t0 = time.monotonic()
    if hasattr(engine, "transcribe_conf"):
        rows = engine.transcribe_conf(images)
        hyps = [t for t, _ in rows]
        confs: list[float | None] = [c for _, c in rows]
    else:
        hyps = list(engine.transcribe(images))
        confs = [None] * len(hyps)
    seconds = time.monotonic() - t0
    if len(hyps) != len(pairs):
        raise ValueError(f"{len(hyps)} readings for {len(pairs)} lines")
    return hyps, confs, seconds


def score_candidate(
    res: CandidateResult,
    pairs: Sequence[LinePair],
    hyps: Sequence[str],
    *,
    package_dir: Path | str | None,
    smoke_dir: Path,
) -> None:
    """Fill a result's scores: the B1 policies, the package's policies, its script."""
    for pol in metrics.POLICIES.values():
        ev = bench.score_hypotheses(
            pairs,
            hyps,
            engine_name=res.engine_name,
            engine_version=res.engine_version,
            policy=pol,
            seconds=res.seconds,
            dataset="dresden1673",
        )
        res.scores[pol.name] = {
            "cer": ev.cer.point,
            "cer_lo": ev.cer.lo,
            "cer_hi": ev.cer.hi,
            "wer": ev.wer.point,
            "wer_lo": ev.wer.lo,
            "wer_hi": ev.wer.hi,
            "macro_cer": ev.macro_cer,
        }
    res.package = package_scores(pairs, hyps)
    if package_dir is not None:
        preds = smoke_dir / f"{res.key}.predictions.jsonl"
        smoke_dir.mkdir(parents=True, exist_ok=True)
        with preds.open("w", encoding="utf-8") as fh:
            for p, h in zip(pairs, hyps, strict=True):
                fh.write(json.dumps({"id": p.line_id, "text": h}, ensure_ascii=False) + "\n")
        res.package_script = run_package_script(package_dir, preds)


def run_candidate(
    cand: Candidate,
    pairs: Sequence[LinePair],
    *,
    device: str = "cpu",
    batch_size: int = 8,
    smoke_dir: Path | str = DEFAULT_SMOKE_DIR,
    package_dir: Path | str | None = DEFAULT_PACKAGE,
    force: bool = False,
    engine_factory: Callable[[Candidate], object] | None = None,
    log: Callable[[str], None] | None = None,
) -> CandidateResult:
    """Read the set with one candidate (cached under ``smoke_dir``) and score it."""
    smoke_dir = Path(smoke_dir)
    res = CandidateResult(cand.key, cand.kind, cand.source, cand.licence, cand.origin, cand.note)
    res.n_lines = len(pairs)
    cached = None if force else load_cached_hyps(smoke_dir, cand.key, pairs)
    if cached is not None:
        hyps, confs, meta = cached
        res.cached = True
        res.engine_name = meta.get("engine_name", cand.kind)
        res.engine_version = meta.get("engine_version", cand.source)
        res.device = meta.get("device", "")
        res.seconds = float(meta.get("seconds", 0.0))
        if log:
            log(f"{cand.key}: {len(hyps)} cached readings")
    else:
        try:
            engine = (
                engine_factory(cand)
                if engine_factory
                else build_engine(cand, device=device, batch_size=batch_size)
            )
            hyps, confs, seconds = read_with(engine, pairs)
        except Exception as exc:  # noqa: BLE001 — one reader's failure must not end the run
            res.status = f"skipped:{type(exc).__name__}: {str(exc)[:200]}"
            if log:
                log(f"{cand.key}: {res.status}")
            return res
        res.engine_name = getattr(engine, "name", cand.kind)
        res.engine_version = getattr(engine, "version", cand.source)
        res.device = str(getattr(engine, "device", device))
        res.seconds = seconds
        save_hyps(
            smoke_dir,
            cand.key,
            pairs,
            hyps,
            confs,
            {
                "engine_name": res.engine_name,
                "engine_version": res.engine_version,
                "device": res.device,
                "seconds": seconds,
                "n_lines": len(pairs),
                "read_at": date.today().isoformat(),
            },
        )
        if log:
            log(f"{cand.key}: {len(hyps)} lines read in {seconds:.1f} s on {res.device}")
    res.n_empty = sum(1 for h in hyps if not h.strip())
    known = [c for c in confs if c is not None]
    res.mean_conf = sum(known) / len(known) if known else None
    score_candidate(res, pairs, hyps, package_dir=package_dir, smoke_dir=smoke_dir)
    return res


# --------------------------------------------------------------------------- #
# The vision row (optional, keyed)
# --------------------------------------------------------------------------- #


def vision_engine(env: dict | None = None):
    """An OpenAI or Anthropic vision engine when a key is set, else ``None``."""
    env = os.environ if env is None else env
    if env.get("OPENAI_API_KEY"):
        from leibniz.htr.engines import OpenAIEngine

        return OpenAIEngine(api_key=env["OPENAI_API_KEY"])
    if env.get("ANTHROPIC_API_KEY"):
        from leibniz.htr.engines import AnthropicEngine

        return AnthropicEngine(api_key=env["ANTHROPIC_API_KEY"])
    return None


def run_vision(
    pairs: Sequence[LinePair],
    *,
    n: int = VISION_SUBSAMPLE,
    seed: int = VISION_SEED,
    smoke_dir: Path | str = DEFAULT_SMOKE_DIR,
    package_dir: Path | str | None = DEFAULT_PACKAGE,
    engine=None,
    log: Callable[[str], None] | None = None,
) -> CandidateResult | None:
    """One zero-shot vision reading on a seeded subsample; ``None`` without a key."""
    engine = engine or vision_engine()
    if engine is None:
        if log:
            log("vision: no OPENAI_API_KEY or ANTHROPIC_API_KEY in the environment; skipped")
        return None
    sub = data.subsample(pairs, n, seed=seed)
    cand = Candidate(
        f"vision-{engine.name}",
        "vision",
        getattr(engine, "version", engine.name),
        "API output",
        "",
        f"zero-shot on a seeded subsample of {len(sub)} lines; only images are sent",
        default=False,
    )
    res = run_candidate(
        cand,
        sub,
        smoke_dir=smoke_dir,
        package_dir=None,
        engine_factory=lambda _c: engine,
        log=log,
    )
    cost = getattr(engine, "cost", None)
    if cost is not None:
        res.note += f"; cost ${cost:.2f}"
    return res


# --------------------------------------------------------------------------- #
# The whole smoke test, and its report
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class SmokeResult:
    package_dir: str
    n_lines: int
    n_pages: int
    device: str
    cuda: bool
    results: list[CandidateResult]
    vision: CandidateResult | None
    package_info: dict
    generated: str = field(default_factory=lambda: date.today().isoformat())

    def as_dict(self) -> dict:
        return {
            "generated": self.generated,
            "package_dir": self.package_dir,
            "n_lines": self.n_lines,
            "n_pages": self.n_pages,
            "device": self.device,
            "cuda": self.cuda,
            "package_info": self.package_info,
            "results": [r.as_dict() for r in self.results],
            "vision": self.vision.as_dict() if self.vision else None,
        }


def run_smoke(
    pairs: Sequence[LinePair],
    candidates: Sequence[Candidate],
    *,
    device: str = "cpu",
    batch_size: int = 8,
    smoke_dir: Path | str = DEFAULT_SMOKE_DIR,
    package_dir: Path | str = DEFAULT_PACKAGE,
    force: bool = False,
    vision: bool = True,
    vision_n: int = VISION_SUBSAMPLE,
    engine_factory: Callable[[Candidate], object] | None = None,
    log: Callable[[str], None] | None = None,
) -> SmokeResult:
    results = [
        run_candidate(
            c,
            pairs,
            device=device,
            batch_size=batch_size,
            smoke_dir=smoke_dir,
            package_dir=package_dir,
            force=force,
            engine_factory=engine_factory,
            log=log,
        )
        for c in candidates
    ]
    vis = (
        run_vision(pairs, n=vision_n, smoke_dir=smoke_dir, package_dir=None, log=log)
        if vision
        else None
    )
    try:
        import torch

        cuda = bool(torch.cuda.is_available())
    except ModuleNotFoundError:
        cuda = False
    return SmokeResult(
        package_dir=str(package_dir),
        n_lines=len(pairs),
        n_pages=len({p.meta.get("page_id") for p in pairs if p.meta.get("page_id")}),
        device=device,
        cuda=cuda,
        results=results,
        vision=vis,
        package_info=package_summary(package_dir),
    )


def _pct(x: float | None, d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{d}f} %"


def _ci(sc: dict | None) -> str:
    if not sc:
        return "—"
    return f"{_pct(sc['cer'])} ({_pct(sc['cer_lo'])}–{_pct(sc['cer_hi'])})"


def render_report(res: SmokeResult) -> str:
    """The Markdown report: numbers only, no Dresden text."""
    ok = [r for r in res.results if r.status == "ok"]
    ranked = sorted(ok, key=lambda r: r.scores["philiumm"]["cer"])
    out: list[str] = []
    out.append("# Bootstrap readers for Kurrent: a ranking on Dresden")
    out.append("")
    out.append(
        f"{res.n_lines:,} lines on {res.n_pages} pages of the Dresdner Hofdiarium 1673 "
        "(Mscr.Dresd.K.117, Stefan Beckert's ground truth as the Kurrent Trace v0.1 package "
        "cuts it), read once by every candidate and scored by the B1 harness under its three "
        "normalisation policies — `philiumm` (NFD, whitespace collapsed; case and diacritics "
        "kept), `lenient` (case and diacritics folded), `strict` (NFC, whitespace as written) — "
        "with a 95 % bootstrap interval, and by the package's two scores (strict NFC; a reading "
        "policy that folds the long s to s and collapses whitespace), reimplemented on the same "
        "edit distance and, where the package's own script ran, confirmed by it. "
        f"Device `{res.device}` (CUDA {'available' if res.cuda else 'not available'}); wall time "
        "per line includes image decoding and, for the first lines, model warm-up."
    )
    out.append("")
    out.append(
        "**A ranking, not a benchmark.** The Dresden lines are public and may sit in a "
        "candidate's training set; the hand is a chancery's of the 1670s, not Leibniz's or his "
        "correspondents'; and the text is nc-bucket material (the package applies CC BY-NC-SA "
        "4.0 where Zenodo says CC BY 4.0), so this report carries numbers only — the readings "
        "and the references stay under `data/kurrent/smoke/`. The number that decides K2 is "
        "the pilot's yield on Leibniz's own German pages (Task 4)."
    )
    out.append("")
    out.append("## Character error rate by policy")
    out.append("")
    out.append(
        "| candidate | CER philiumm (95 % CI) | CER lenient | CER strict | WER philiumm | "
        "package strict NFC | package reading | exact lines | empty outputs | mean conf | "
        "ms/line | device |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in ranked:
        ps, pr = r.package.get("strict_nfc", {}), r.package.get("reading_long_s_and_whitespace", {})
        out.append(
            f"| {r.key} | {_ci(r.scores.get('philiumm'))} | {_pct(r.scores['lenient']['cer'])} | "
            f"{_pct(r.scores['strict']['cer'])} | {_pct(r.scores['philiumm']['wer'])} | "
            f"{_pct(ps.get('cer'))} | {_pct(pr.get('cer'))} | {pr.get('exact_lines', 0)} | "
            f"{r.n_empty} | {'—' if r.mean_conf is None else f'{r.mean_conf:.3f}'} | "
            f"{'—' if r.ms_per_line is None else f'{r.ms_per_line:.0f}'} | {r.device} |"
        )
    if res.vision is not None and res.vision.status == "ok":
        v = res.vision
        vps = v.package.get("strict_nfc", {})
        vpr = v.package.get("reading_long_s_and_whitespace", {})
        out.append(
            f"| {v.key} ({v.n_lines} lines) | {_ci(v.scores.get('philiumm'))} | "
            f"{_pct(v.scores['lenient']['cer'])} | {_pct(v.scores['strict']['cer'])} | "
            f"{_pct(v.scores['philiumm']['wer'])} | {_pct(vps.get('cer'))} | "
            f"{_pct(vpr.get('cer'))} | {vpr.get('exact_lines', 0)} | {v.n_empty} | — | "
            f"{'—' if v.ms_per_line is None else f'{v.ms_per_line:.0f}'} | API |"
        )
    skipped = [r for r in res.results if r.status != "ok"]
    if skipped:
        out.append("")
        for r in skipped:
            out.append(f"- `{r.key}` did not run: {r.status}")
    if res.vision is None:
        out.append("")
        out.append(
            "No vision row: neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` was set when the "
            "smoke test ran."
        )
    script_rows = [r for r in ok if r.package_script]
    if script_rows:
        out.append("")
        out.append(
            "The package's own `scripts/evaluate.py` ran on the same readings; its strict and "
            "reading CER agree with the columns above to the printed precision for: "
            + ", ".join(
                f"`{r.key}`"
                for r in script_rows
                if abs(
                    r.package_script["scores"]["strict_nfc"]["cer"] - r.package["strict_nfc"]["cer"]
                )
                < 5e-4
                and abs(
                    r.package_script["scores"]["reading_long_s_and_whitespace"]["cer"]
                    - r.package["reading_long_s_and_whitespace"]["cer"]
                )
                < 5e-4
            )
            + "."
        )
    out.append("")
    out.append("## Licences and provenance")
    out.append("")
    out.append("| candidate | kind | source | licence | note |")
    out.append("|---|---|---|---|---|")
    for r in res.results:
        out.append(f"| {r.key} | {r.kind} | {r.origin or r.source} | {r.licence} | {r.note} |")
    out.append("")
    out.append(
        "The two `fgho` models state no licence on the Hub: they are evaluated here and nothing "
        "is built on them unless a licence appears. The Dresden text: see above. The crops' "
        "images carry the source's Public Domain Mark 1.0."
    )
    out.append("")
    out.append("## Reading the table")
    out.append("")
    out.append(
        "- The `philiumm` policy is the project's headline (the B1 reproduction's); `strict` is "
        "the honest upper bound; `lenient` says how much is case and accents. The Dresden "
        "conventions keep u/v as written and distinguish the long s, so the package's reading "
        "policy (long s folded) is the kindest to a reader trained on modern s."
    )
    out.append(
        "- Exact lines are under the package's reading policy. Empty outputs are lines a reader "
        "returned blank; they count as full deletions in every score."
    )
    out.append(
        "- Mean confidence is each reader's own: kraken's mean character posterior, TrOCR's mean "
        "token probability. They are not on one scale across readers."
    )
    out.append("")
    return "\n".join(out)


def write_reports(
    res: SmokeResult, reports_dir: Path | str = DEFAULT_REPORTS_DIR
) -> tuple[Path, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    md = reports_dir / "bootstrap-candidates.md"
    js = reports_dir / "bootstrap-candidates.json"
    md.write_text(render_report(res), encoding="utf-8")
    js.write_text(json.dumps(res.as_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return md, js


__all__ = [
    "CANDIDATES",
    "DEFAULT_PACKAGE",
    "DEFAULT_SMOKE_DIR",
    "PACKAGE_POLICIES",
    "Candidate",
    "CandidateResult",
    "SmokeResult",
    "build_engine",
    "fetch_mccatmus",
    "load_dresden",
    "package_scores",
    "pick_device",
    "render_report",
    "run_candidate",
    "run_package_script",
    "run_smoke",
    "run_vision",
    "vision_engine",
    "write_reports",
]
