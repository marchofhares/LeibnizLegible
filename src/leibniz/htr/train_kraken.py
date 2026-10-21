"""Fine-tune a kraken recognition model on the training set (K3 Task 2b and Task 3).

The fast candidate: ``ketos train`` from the PHILIUMM checkpoint
(``FoNDUE-GD_v2_ft_Leibniz.safetensors``, CC BY 4.0), its codec grown to the
training text's characters with ``--resize union`` (the umlauts decompose in
NFD onto marks the codec has; what it lacks are symbols), the ground truth
normalised to NFD at load (``-u NFD``, the form the checkpoint was trained
in) with whitespace normalised, the split lists of :mod:`leibniz.htr.trainset`
as ``-t`` and ``-e``. kraken is what C3 will use, so this module only builds
the command, runs it where asked (a background job: the CLI starts it under
nohup with a log), and reads what it leaves behind: lightning's checkpoints
``checkpoint_{epoch:02d}-{val_metric:.4f}.ckpt`` name each epoch's validation
accuracy (kraken's own, 1 − CER under its normalisation), and the best
weights are converted to ``best_<score>.safetensors`` at the end. The
project's number — CER under the harness's ``philiumm`` policy on the same
validation files — comes from :func:`score_weights`, through
:class:`~leibniz.htr.engines.KrakenEngine` as the evaluation will read.

Nothing here imports kraken at module level; the command builder, the log
and checkpoint readers and the budget arithmetic are tested offline.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from leibniz.htr import metrics
from leibniz.htr.train_trocr import Sample, read_list

DEFAULT_BASE = Path("data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors")
DEFAULT_OUT = Path("data/models/k3/kraken")
CKPT_RE = re.compile(r"checkpoint_(?P<epoch>\d+)-(?P<metric>[0-9.]+)\.ckpt$")
BEST_RE = re.compile(r"best_(?P<score>[0-9.]+)\.(?P<fmt>safetensors|mlmodel)$")
EPOCH_TIME_RE = re.compile(r"Epoch (?P<epoch>\d+):.*?(?P<pct>\d+)%.*?\[(?P<elapsed>[\d:]+)<")


@dataclass(slots=True)
class KetosSettings:
    """The knobs of a ``ketos train`` run (recorded in the runs row)."""

    base: str = str(DEFAULT_BASE)
    batch_size: int = 16
    lr: float = 1e-4
    epochs: int = -1  # -1: early stopping
    min_epochs: int = 0
    lag: int = 5
    quit: str = "early"  # early | fixed
    resize: str = "union"
    normalization: str = "NFD"
    normalize_whitespace: bool = True
    augment: bool = False
    optimizer: str = "AdamW"
    schedule: str = "cosine"
    warmup: int = 0
    weight_decay: float = 0.0
    freeze_backbone: int = 0
    precision: str = "32-true"
    workers: int = 4
    threads: int = 4
    device: str = "cuda:0"
    freq: float = 1.0
    seed: int = 20261021

    @property
    def key(self) -> str:
        parts = ["ketos", f"b{self.batch_size}", f"lr{self.lr:g}", self.resize]
        if self.augment:
            parts.append("augment")
        if self.freeze_backbone:
            parts.append(f"freeze{self.freeze_backbone}")
        if self.precision != "32-true":
            parts.append(self.precision)
        return "-".join(parts)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["key"] = self.key
        return d


def ketos_command(
    settings: KetosSettings,
    *,
    train_list: Path | str,
    val_list: Path | str,
    out_dir: Path | str,
    ketos: str = "ketos",
) -> list[str]:
    """The ``ketos train`` command line for the settings and the split lists."""
    out = Path(out_dir)
    cmd = [
        ketos,
        "-d",
        settings.device,
        "--precision",
        settings.precision,
        "--workers",
        str(settings.workers),
        "--threads",
        str(settings.threads),
        "-s",
        str(settings.seed),
        "train",
        "-f",
        "path",
        "-t",
        str(train_list),
        "-e",
        str(val_list),
        "-i",
        settings.base,
        "--resize",
        settings.resize,
        "-u",
        settings.normalization,
        "-B",
        str(settings.batch_size),
        "-r",
        f"{settings.lr:g}",
        "--optimizer",
        settings.optimizer,
        "--schedule",
        settings.schedule,
        "-w",
        f"{settings.weight_decay:g}",
        "-q",
        settings.quit,
        "-N",
        str(settings.epochs),
        "--min-epochs",
        str(settings.min_epochs),
        "--lag",
        str(settings.lag),
        "-F",
        f"{settings.freq:g}",
        "-o",
        str(out / "checkpoints"),
    ]
    if settings.warmup:
        cmd += ["--warmup", str(settings.warmup)]
    if settings.freeze_backbone:
        cmd += ["--freeze-backbone", str(settings.freeze_backbone)]
    cmd.append(
        "--normalize-whitespace" if settings.normalize_whitespace else "--no-normalize-whitespace"
    )
    cmd.append("--augment" if settings.augment else "--no-augment")
    return cmd


def subset_list(src: Path | str, dst: Path | str, *, n: int, seed: int) -> Path:
    """A seeded subset of a split list (the pilot's 20,000 lines), written to ``dst``."""
    import random

    lines = [ln for ln in Path(src).read_text(encoding="utf-8").splitlines() if ln.strip()]
    rng = random.Random(seed)
    rng.shuffle(lines)
    chosen = sorted(lines[:n])
    p = Path(dst)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(ln + "\n" for ln in chosen), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# What a run leaves behind
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Epoch:
    epoch: int
    val_metric: float  # kraken's validation accuracy (1 − its CER)
    path: str
    mtime: float


def read_checkpoints(out_dir: Path | str) -> list[Epoch]:
    """The epochs lightning saved (the best ten by kraken's metric), from their names."""
    d = Path(out_dir) / "checkpoints"
    out: list[Epoch] = []
    if not d.exists():
        return out
    for p in d.iterdir():
        m = CKPT_RE.search(p.name)
        if m:
            out.append(
                Epoch(int(m.group("epoch")), float(m.group("metric")), str(p), p.stat().st_mtime)
            )
    return sorted(out, key=lambda e: e.epoch)


def best_weights(out_dir: Path | str) -> tuple[Path, float] | None:
    """The converted best weights ``best_<score>.safetensors`` and their score."""
    d = Path(out_dir) / "checkpoints"
    if not d.exists():
        return None
    found: list[tuple[float, Path]] = []
    for p in d.iterdir():
        m = BEST_RE.search(p.name)
        if m:
            found.append((float(m.group("score")), p))
    if not found:
        return None
    score, path = max(found)
    return path, score


def epoch_times(checkpoints: Sequence[Epoch]) -> list[float]:
    """Seconds between consecutive checkpoints' modification times (an epoch's wall
    time, validation included, where the epochs are consecutive)."""
    by_epoch = {e.epoch: e.mtime for e in checkpoints}
    out: list[float] = []
    for k in sorted(by_epoch):
        if k - 1 in by_epoch:
            out.append(by_epoch[k] - by_epoch[k - 1])
    return out


def parse_log(text: str) -> dict:
    """What ketos' console log says: the codec resize, the best model line, errors."""
    out: dict = {"resized": None, "best": None, "errors": []}
    m = re.search(r"Resizing codec to include (\d+) new code points", text)
    if m:
        out["resized"] = int(m.group(1))
    m = re.search(r"Converting best model (\S+) \(score: ([0-9.]+)\) to weights file (\S+)", text)
    if m:
        out["best"] = {"checkpoint": m.group(1), "score": float(m.group(2)), "weights": m.group(3)}
    for line in text.splitlines():
        if "Error" in line or "error" in line[:40]:
            out["errors"].append(line.strip()[:200])
    return out


def run(
    cmd: Sequence[str],
    *,
    log_path: Path | str,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.Popen:
    """Start the command detached, its output to ``log_path``; the caller polls."""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fh = p.open("ab")
    return subprocess.Popen(
        list(cmd),
        stdout=fh,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        env=dict(env) if env else None,
        start_new_session=True,
    )


# --------------------------------------------------------------------------- #
# Scoring a checkpoint with the project's metric
# --------------------------------------------------------------------------- #


def score_weights(
    weights: Path | str,
    samples: Sequence[Sample],
    *,
    device: str = "cuda",
    batch_size: int = 16,
    policy: metrics.NormPolicy = metrics.PHILIUMM_POLICY,
    engine_factory: Callable[[str], object] | None = None,
) -> dict:
    """CER of a kraken weights file on the samples, through the project's engine and
    policy (the number the evaluation measures), with the pace."""
    if engine_factory is None:
        from leibniz.htr.engines import KrakenEngine

        engine = KrakenEngine(str(weights), device=device, batch_size=batch_size)
    else:
        engine = engine_factory(str(weights))
    images = [s.image.read_bytes() for s in samples]
    t0 = time.perf_counter()
    hyps = engine.transcribe(images)
    seconds = time.perf_counter() - t0
    scores = [
        metrics.score_line(s.text, h, policy, line_id=s.line_id)
        for s, h in zip(samples, hyps, strict=True)
    ]
    return {
        "n": len(samples),
        "cer": metrics.cer(scores),
        "wer": metrics.wer(scores),
        "exact": sum(1 for sc in scores if sc.char_edits == 0),
        "seconds": seconds,
        "lines_per_s": (len(samples) / seconds) if seconds else None,
        "policy": policy.name,
        "hyps": {s.line_id: h for s, h in zip(samples, hyps, strict=True)},
    }


@dataclass(slots=True)
class KetosRun:
    """A run's account, from its directory and log."""

    out_dir: str
    settings: dict
    command: list[str]
    checkpoints: list[dict] = field(default_factory=list)
    epoch_seconds: list[float] = field(default_factory=list)
    best: dict | None = None
    log: dict = field(default_factory=dict)
    score: dict | None = None  # the project's CER of the best weights
    pilot_lines: int | None = None  # lines in the training list the run used
    run_seconds: float | None = None  # start to the best weights' conversion
    peak_mib: int | None = None  # sampled from nvidia-smi while it ran, where given

    def as_dict(self) -> dict:
        d = asdict(self)
        if d.get("score"):
            d["score"] = {k: v for k, v in d["score"].items() if k != "hyps"}
        return d


def account(
    out_dir: Path | str,
    settings: KetosSettings,
    command: Sequence[str],
    log_text: str,
    *,
    train_list: Path | str | None = None,
    started: float | None = None,
    peak_mib: int | None = None,
) -> KetosRun:
    cks = read_checkpoints(out_dir)
    bw = best_weights(out_dir)
    n_lines = None
    if train_list is not None and Path(train_list).exists():
        n_lines = sum(
            1 for ln in Path(train_list).read_text(encoding="utf-8").splitlines() if ln.strip()
        )
    run_seconds = None
    if started is not None:
        end = bw[0].stat().st_mtime if bw else (cks[-1].mtime if cks else None)
        if end is not None:
            run_seconds = end - started
    return KetosRun(
        pilot_lines=n_lines,
        run_seconds=run_seconds,
        peak_mib=peak_mib,
        out_dir=str(out_dir),
        settings=settings.as_dict(),
        command=list(command),
        checkpoints=[asdict(c) for c in cks],
        epoch_seconds=epoch_times(cks),
        best={"weights": str(bw[0]), "score": bw[1]} if bw else None,
        log=parse_log(log_text),
    )


def install_best(out_dir: Path | str, dest: Path | str) -> Path | None:
    """Copy the best weights to a stable path (``<out>/best.safetensors``)."""
    bw = best_weights(out_dir)
    if bw is None:
        return None
    d = Path(dest)
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bw[0], d)
    return d


def write_account(path: Path | str, run_: KetosRun) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(run_.as_dict(), indent=1), encoding="utf-8")
    return p


__all__ = [
    "BEST_RE",
    "CKPT_RE",
    "DEFAULT_BASE",
    "DEFAULT_OUT",
    "Epoch",
    "KetosRun",
    "KetosSettings",
    "account",
    "best_weights",
    "epoch_times",
    "install_best",
    "ketos_command",
    "parse_log",
    "read_checkpoints",
    "read_list",
    "run",
    "score_weights",
    "subset_list",
    "write_account",
]
