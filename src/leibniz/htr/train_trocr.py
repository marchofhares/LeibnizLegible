"""Fine-tune a TrOCR checkpoint on the training set (K3 Task 2a and Task 3).

A plain PyTorch loop over a :class:`~transformers.VisionEncoderDecoderModel`
(the Bern Kurrent checkpoint, MIT): no Trainer, so nothing new joins the
``kurrent`` extra. The data are the training set's files
(:mod:`leibniz.htr.trainset`: ``<split>/<page>/<seq>.png`` + ``.gt.txt``,
listed in ``train.txt`` and ``val.txt``); the processor resizes every crop to
the checkpoint's 384 × 384 and the tokenizer (byte-level BPE) encodes the
text as it is (NFC, the checkpoint's own form).

**Memory.** A 334 M-parameter model does not fine-tune with AdamW in 6 GB
(weights 1.3 GB + gradients 1.3 GB + two moments 2.7 GB before any
activation), so the loop offers the knobs the prompt names, each measured by
the pilot: ``optimizer="adafactor"`` (factored second moments, no first
moment; transformers' own), ``freeze_encoder`` (the ViT's 86 M parameters
frozen, gradients and states only for the decoder), ``grad_checkpointing``
(activations recomputed in the backward pass) and ``fp16`` (autocast with a
gradient scaler; the GTX 1660 Ti has no tensor cores, so this may be slower,
as K2 found for inference). The pilot (:func:`pilot`) times each setting on
a bounded number of steps, records the GPU's peak memory and lines per
second, and extrapolates to the full plan; :func:`train` runs the staged,
resumable training whose checkpoints are chosen on the validation set by
CER under the harness's ``philiumm`` policy (greedy decoding through
:class:`~leibniz.htr.trocr.TrOCREngine`'s path, so the number is the one the
evaluation will measure).

torch, transformers and Pillow are imported lazily; the loop's bookkeeping
(the settings, the schedule, the budget arithmetic, the log rows, the
checkpoint choice) is tested without them.
"""

from __future__ import annotations

import json
import math
import random
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from leibniz.htr import metrics

DEFAULT_BASE = "dh-unibe/trocr-kurrent-XVI-XVII"
DEFAULT_TRAIN_ROOT = Path("data/train/k3")
DEFAULT_OUT = Path("data/models/k3/trocr")
OPTIMIZERS = ("adamw", "adafactor")
PILOT_LINES = 20_000
MAX_TARGET_TOKENS = (
    128  # the checkpoint's decoder was trained to 128; the longest line is far under
)


@dataclass(slots=True)
class Settings:
    """One training configuration (the pilot's rows differ in these)."""

    optimizer: str = "adafactor"
    freeze_encoder: bool = False
    grad_checkpointing: bool = False
    fp16: bool = False
    batch_size: int = 8
    lr: float = 5e-5
    accumulate: int = 1  # gradient accumulation steps
    weight_decay: float = 0.0
    warmup_steps: int = 200
    max_target_tokens: int = MAX_TARGET_TOKENS

    @property
    def key(self) -> str:
        parts = [self.optimizer]
        if self.freeze_encoder:
            parts.append("frozen-encoder")
        if self.grad_checkpointing:
            parts.append("grad-ckpt")
        if self.fp16:
            parts.append("fp16")
        parts.append(f"b{self.batch_size}")
        if self.accumulate > 1:
            parts.append(f"x{self.accumulate}")
        return "-".join(parts)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["key"] = self.key
        return d

    def as_dict_plain(self) -> dict:
        """The fields alone (what the constructor takes)."""
        return asdict(self)


# The pilot's candidate settings, in the order the prompt names them: AdamW on
# every parameter first (to show the memory), then each remedy on its own and
# the combinations a 6 GB card is likely to need.
PILOT_SETTINGS: tuple[Settings, ...] = (
    Settings(optimizer="adamw"),
    Settings(optimizer="adafactor"),
    Settings(optimizer="adamw", freeze_encoder=True),
    Settings(optimizer="adafactor", freeze_encoder=True),
    Settings(optimizer="adafactor", grad_checkpointing=True),
    Settings(optimizer="adafactor", fp16=True),
    Settings(optimizer="adafactor", grad_checkpointing=True, fp16=True),
)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Sample:
    image: Path
    text: str

    @property
    def line_id(self) -> str:
        return f"{self.image.parent.name}:{self.image.stem}"


def read_list(path: Path | str) -> list[Sample]:
    """The samples a split list names (one image path per line; the sidecar beside it)."""
    out: list[Sample] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        img = Path(raw)
        gt = img.with_suffix(".gt.txt")
        if not gt.exists():
            continue
        out.append(Sample(img, gt.read_text(encoding="utf-8").rstrip("\n")))
    return out


def filter_samples(samples: Sequence[Sample], keep: Callable[[Sample], bool]) -> list[Sample]:
    return [s for s in samples if keep(s)]


def epoch_order(n: int, epoch: int, seed: int) -> list[int]:
    """A seeded shuffle per epoch, so a resumed run sees the same order."""
    idx = list(range(n))
    random.Random(seed + epoch).shuffle(idx)
    return idx


# --------------------------------------------------------------------------- #
# Budget arithmetic (tested without torch)
# --------------------------------------------------------------------------- #


def extrapolate(
    lines_per_s: float | None,
    *,
    train_lines: int,
    epochs: float,
    val_lines: int = 0,
    val_lines_per_s: float | None = None,
    evals: int = 0,
) -> dict:
    """Hours for ``epochs`` over ``train_lines`` at the measured pace, plus the
    validation passes; ``None`` where the pace is unknown."""
    if not lines_per_s:
        return {"train_hours": None, "val_hours": None, "total_hours": None, "days": None}
    train_h = train_lines * epochs / lines_per_s / 3600.0
    val_h = (val_lines * evals / val_lines_per_s / 3600.0) if val_lines_per_s and evals else 0.0
    total = train_h + val_h
    return {
        "train_hours": train_h,
        "val_hours": val_h,
        "total_hours": total,
        "days": total / 24.0,
    }


def lr_at(step: int, *, base: float, warmup: int, total: int) -> float:
    """Linear warm-up then linear decay to a tenth (a plain schedule, no library)."""
    if warmup > 0 and step < warmup:
        return base * (step + 1) / warmup
    if total <= warmup:
        return base
    frac = (step - warmup) / max(1, total - warmup)
    return base * max(0.1, 1.0 - 0.9 * frac)


# --------------------------------------------------------------------------- #
# The loop
# --------------------------------------------------------------------------- #


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_model(base: str | Path, *, cache_dir: Path | str | None = None):
    """The processor and the model from a Hub id or a local directory (K3's own
    checkpoints), through the engine's loader so the checkpoint's quirks
    (``max_length``, the cache flag) are handled once."""
    from leibniz.htr.trocr import HF_CACHE_DIR, load_pretrained

    processor, model = load_pretrained(str(base), Path(cache_dir or HF_CACHE_DIR), "cpu")
    return processor, model


def _gpu_peak_mib() -> int | None:
    try:
        import torch

        if torch.cuda.is_available():
            return int(torch.cuda.max_memory_reserved() // (1024 * 1024))
    except ModuleNotFoundError:
        pass
    return None


def _gpu_reset_peak() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()
    except ModuleNotFoundError:
        pass


def memory_fraction(limit_mib: int | None, total_mib: int | None) -> float | None:
    """The share of the card a process may reserve for ``limit_mib`` of ``total_mib``."""
    if not limit_mib or not total_mib or total_mib <= 0:
        return None
    return min(1.0, limit_mib / total_mib)


def cap_memory(limit_mib: int | None, device: str) -> float | None:
    """Make the caching allocator refuse allocations past ``limit_mib`` on the device,
    so a run that would spill into host memory under WSL2 raises
    :class:`torch.OutOfMemoryError` in-process instead (the pilot's rows depend on it:
    the AdamW-on-everything setting of 21 October reached 5.7 GB in one burst before
    any check could run). Returns the fraction set, or ``None``."""
    if not limit_mib or not device.startswith("cuda"):
        return None
    import torch

    if not torch.cuda.is_available():
        return None
    idx = torch.device(device).index or 0
    total = torch.cuda.get_device_properties(idx).total_memory // (1024 * 1024)
    frac = memory_fraction(limit_mib, total)
    if frac is not None:
        torch.cuda.set_per_process_memory_fraction(frac, idx)
    return frac


def build_optimizer(model, settings: Settings):
    import torch

    params = [p for p in model.parameters() if p.requires_grad]
    if settings.optimizer == "adamw":
        return torch.optim.AdamW(params, lr=settings.lr, weight_decay=settings.weight_decay)
    if settings.optimizer == "adafactor":
        from transformers.optimization import Adafactor

        return Adafactor(
            params,
            lr=settings.lr,
            scale_parameter=False,
            relative_step=False,
            warmup_init=False,
            weight_decay=settings.weight_decay,
        )
    raise ValueError(f"unknown optimizer {settings.optimizer!r}; choose from {OPTIMIZERS}")


def prepare_model(model, settings: Settings, device: str):
    """Freeze, checkpoint, move; return the model on the device in train mode."""
    if settings.freeze_encoder:
        for p in model.encoder.parameters():
            p.requires_grad_(False)
    if settings.grad_checkpointing:
        model.gradient_checkpointing_enable()
        # checkpointing needs the inputs' grad path open when the encoder is frozen
        if hasattr(model, "enable_input_require_grads"):
            try:
                model.enable_input_require_grads()
            except Exception:  # pragma: no cover - model-dependent
                pass
    model.config.use_cache = False
    model.to(device)
    model.train()
    return model


def encode_batch(processor, samples: Sequence[Sample], *, max_tokens: int, device: str):
    """Pixel values and labels (padding as -100) for a batch; the images decoded here."""
    from PIL import Image

    images = []
    for s in samples:
        with Image.open(s.image) as im:
            im.load()
            images.append(im.convert("RGB"))
    pixel = processor(images=images, return_tensors="pt").pixel_values
    tok = processor.tokenizer
    enc = tok(
        [s.text for s in samples],
        padding=True,
        truncation=True,
        max_length=max_tokens,
        return_tensors="pt",
    )
    labels = enc.input_ids.clone()
    labels[enc.attention_mask == 0] = -100
    return pixel.to(device), labels.to(device)


@dataclass(slots=True)
class StepLog:
    step: int
    epoch: float
    loss: float
    lr: float
    lines: int
    seconds: float
    peak_mib: int | None

    def as_dict(self) -> dict:
        return asdict(self)


def train_steps(
    model,
    processor,
    samples: Sequence[Sample],
    settings: Settings,
    *,
    device: str,
    max_steps: int | None = None,
    max_lines: int | None = None,
    epochs: float = 1.0,
    seed: int = 20261021,
    log: Callable[[str], None] | None = None,
    log_every: int = 50,
    on_epoch_end: Callable[[int, int], None] | None = None,
    start_epoch: int = 0,
    start_step: int = 0,
    optimizer=None,
    total_steps: int | None = None,
    stop_check: Callable[[], bool] | None = None,
    memory_limit_mib: int | None = None,
) -> tuple[list[StepLog], dict]:
    """The optimisation loop: ``epochs`` passes over ``samples`` (or until
    ``max_steps`` / ``max_lines``), seeded order, gradient accumulation, the
    linear schedule, autocast and scaling when ``fp16``. Returns the step log and
    the tally (lines, seconds, peak MiB, steps). ``memory_limit_mib`` raises
    :class:`torch.OutOfMemoryError` once the process's reserved GPU memory passes
    it: under WSL2 an allocation past the card spills into host memory instead of
    failing (K2), and the machine crashed that way on 21 October, so the loop
    fails itself first."""
    import torch

    opt = optimizer or build_optimizer(model, settings)
    scaler = torch.amp.GradScaler("cuda") if settings.fp16 and device.startswith("cuda") else None
    n = len(samples)
    steps_per_epoch = math.ceil(n / (settings.batch_size * settings.accumulate))
    total = total_steps or int(math.ceil(steps_per_epoch * epochs))
    if max_steps is not None:
        total = min(total, start_step + max_steps)
    if max_lines is not None:
        total = min(
            total, start_step + math.ceil(max_lines / (settings.batch_size * settings.accumulate))
        )
    warmup = min(settings.warmup_steps, max(1, total // 10))  # a short run warms up in a tenth
    logs: list[StepLog] = []
    step = start_step
    lines_done = 0
    t0 = time.perf_counter()
    _gpu_reset_peak()
    stop = False
    epoch = start_epoch
    while not stop and epoch < math.ceil(epochs) + start_epoch:
        order = epoch_order(n, epoch, seed)
        micro = 0
        opt.zero_grad(set_to_none=True)
        running = 0.0
        count = 0
        for start in range(0, n, settings.batch_size):
            if max_lines is not None and lines_done >= max_lines:
                stop = True
                break
            if stop_check is not None and stop_check():
                stop = True
                break
            batch = [samples[i] for i in order[start : start + settings.batch_size]]
            pixel, labels = encode_batch(
                processor, batch, max_tokens=settings.max_target_tokens, device=device
            )
            if scaler is not None:
                with torch.autocast("cuda", dtype=torch.float16):
                    out = model(pixel_values=pixel, labels=labels)
                loss = out.loss / settings.accumulate
                scaler.scale(loss).backward()
            else:
                out = model(pixel_values=pixel, labels=labels)
                loss = out.loss / settings.accumulate
                loss.backward()
            running += float(loss.detach()) * settings.accumulate
            count += 1
            lines_done += len(batch)
            micro += 1
            if micro % settings.accumulate != 0:
                continue
            lr = lr_at(step, base=settings.lr, warmup=warmup, total=total)
            for g in opt.param_groups:
                g["lr"] = lr
            if scaler is not None:
                scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            if scaler is not None:
                scaler.step(opt)
                scaler.update()
            else:
                opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if memory_limit_mib is not None:
                peak = _gpu_peak_mib()
                if peak is not None and peak > memory_limit_mib:
                    raise torch.OutOfMemoryError(
                        f"reserved {peak} MiB exceeds the {memory_limit_mib} MiB limit "
                        "(the loop's own guard against WSL2's spill into host memory)"
                    )
            if step % log_every == 0 or step == total:
                row = StepLog(
                    step=step,
                    epoch=epoch + start / n,
                    loss=running / max(1, count),
                    lr=lr,
                    lines=lines_done,
                    seconds=time.perf_counter() - t0,
                    peak_mib=_gpu_peak_mib(),
                )
                logs.append(row)
                if log:
                    log(
                        f"step {row.step}/{total} epoch {row.epoch:.2f} loss {row.loss:.4f} "
                        f"lr {row.lr:.2e} {row.lines:,} lines {row.seconds:.0f} s "
                        f"peak {row.peak_mib} MiB"
                    )
                running, count = 0.0, 0
            if step >= total:
                stop = True
                break
        if on_epoch_end is not None and not stop:
            on_epoch_end(epoch, step)
        epoch += 1
    seconds = time.perf_counter() - t0
    return logs, {
        "lines": lines_done,
        "seconds": seconds,
        "lines_per_s": (lines_done / seconds) if seconds else None,
        "peak_mib": _gpu_peak_mib(),
        "steps": step - start_step,
        "epochs_done": epoch - start_epoch,
        "optimizer": opt,
    }


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def validate(
    model,
    processor,
    samples: Sequence[Sample],
    *,
    device: str,
    batch_size: int = 16,
    max_new_tokens: int = 160,
    policy: metrics.NormPolicy = metrics.PHILIUMM_POLICY,
    log: Callable[[str], None] | None = None,
) -> dict:
    """Greedy decoding over the validation samples through the engine's path, scored
    under ``policy``; the lines sorted by width so a batch's steps match."""
    import torch

    from leibniz.htr.trocr import TrOCREngine, _drop_checkpoint_max_length

    _drop_checkpoint_max_length(model)  # the engine's loader does this; the pair is handed over
    engine = TrOCREngine(
        "local",
        device=device,
        batch_size=batch_size,
        max_new_tokens=max_new_tokens,
        use_cache=True,
    )
    engine._processor, engine._model = processor, model  # the loaded pair, no loader
    engine._skip = _special_ids(model)
    model.eval()
    model.config.use_cache = True
    from PIL import Image

    t0 = time.perf_counter()
    hyps: dict[int, str] = {}
    with torch.inference_mode():
        for start in range(0, len(samples), batch_size * 8):
            chunk = list(range(start, min(len(samples), start + batch_size * 8)))
            images = []
            for i in chunk:
                with Image.open(samples[i].image) as im:
                    im.load()
                    images.append(im.convert("RGB"))
            order = sorted(range(len(chunk)), key=lambda j: -images[j].width)
            out = engine.transcribe_images([images[j] for j in order])
            for j, (text, _conf) in zip(order, out, strict=True):
                hyps[chunk[j]] = text
            if log and (start // (batch_size * 8)) % 10 == 0:
                log(f"  validated {len(hyps):,} of {len(samples):,}")
    seconds = time.perf_counter() - t0
    scores = [
        metrics.score_line(s.text, hyps[i], policy, line_id=s.line_id)
        for i, s in enumerate(samples)
    ]
    model.train()
    model.config.use_cache = False
    return {
        "n": len(samples),
        "cer": metrics.cer(scores),
        "wer": metrics.wer(scores),
        "exact": sum(1 for sc in scores if sc.char_edits == 0),
        "seconds": seconds,
        "lines_per_s": (len(samples) / seconds) if seconds else None,
        "policy": policy.name,
        "hyps": {s.line_id: hyps[i] for i, s in enumerate(samples)},
    }


def _special_ids(model) -> set[int]:
    from leibniz.htr.trocr import _special_ids as ids

    return ids(model)


# --------------------------------------------------------------------------- #
# The pilot
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PilotRow:
    settings: dict
    status: str  # ok | oom | skipped:<why>
    lines: int = 0
    seconds: float = 0.0
    lines_per_s: float | None = None
    peak_mib: int | None = None
    steps: int = 0
    val: dict | None = None
    projection: dict | None = None
    error: str = ""

    def as_dict(self) -> dict:
        d = asdict(self)
        if d.get("val"):
            d["val"] = {k: v for k, v in d["val"].items() if k != "hyps"}
        return d


def pilot_setting(
    base: str | Path,
    settings: Settings,
    train: Sequence[Sample],
    *,
    device: str,
    max_lines: int,
    val: Sequence[Sample] | None = None,
    log: Callable[[str], None] | None = None,
    plan_lines: int = 0,
    plan_epochs: float = 1.0,
    memory_limit_mib: int | None = None,
) -> PilotRow:
    """Load the base, train ``max_lines`` lines under ``settings`` (an out-of-memory
    error is a result, not a crash), score the validation set if given, project."""
    import torch

    row = PilotRow(settings=settings.as_dict(), status="ok")
    cap_memory(memory_limit_mib, device)
    processor, model = load_model(base)
    model = prepare_model(model, settings, device)
    try:
        logs, tally = train_steps(
            model,
            processor,
            train,
            settings,
            device=device,
            max_lines=max_lines,
            epochs=1.0,
            log=log,
            memory_limit_mib=memory_limit_mib,
        )
    except torch.OutOfMemoryError as exc:
        row.status = "oom"
        row.error = str(exc).splitlines()[0][:200]
        row.peak_mib = _gpu_peak_mib()
        del model
        _gpu_reset_peak()
        return row
    row.lines, row.seconds = tally["lines"], tally["seconds"]
    row.lines_per_s, row.peak_mib, row.steps = (
        tally["lines_per_s"],
        tally["peak_mib"],
        tally["steps"],
    )
    if val:
        try:
            v = validate(model, processor, val, device=device, log=log)
            row.val = v
        except torch.OutOfMemoryError as exc:
            row.val = {"error": str(exc).splitlines()[0][:200]}
    val_rate = (row.val or {}).get("lines_per_s") if row.val else None
    row.projection = extrapolate(
        row.lines_per_s,
        train_lines=plan_lines or len(train),
        epochs=plan_epochs,
        val_lines=len(val or ()),
        val_lines_per_s=val_rate,
        evals=int(math.ceil(plan_epochs)),
    )
    del model
    _gpu_reset_peak()
    return row


def write_pilot(path: Path | str, rows: Sequence[PilotRow], meta: Mapping) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"meta": dict(meta), "rows": [r.as_dict() for r in rows]}, indent=1),
        encoding="utf-8",
    )
    return p


# --------------------------------------------------------------------------- #
# Full training: staged, resumable, checkpoints chosen on the validation set
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class TrainState:
    """What a resumed run needs: where it was, and the best so far."""

    epoch: int = 0
    step: int = 0
    best_cer: float | None = None
    best_epoch: int | None = None
    history: list[dict] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    started: str = field(default_factory=_now)
    finished: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def read_state(path: Path | str) -> TrainState | None:
    p = Path(path)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return TrainState(**{k: v for k, v in d.items() if k in TrainState.__slots__})  # type: ignore[attr-defined]


def write_state(path: Path | str, state: TrainState) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.part")
    tmp.write_text(json.dumps(state.as_dict(), indent=1), encoding="utf-8")
    tmp.replace(p)


def choose_best(history: Sequence[Mapping]) -> Mapping | None:
    """The epoch with the lowest validation CER (the earliest on a tie)."""
    best = None
    for h in history:
        if h.get("cer") is None:
            continue
        if best is None or h["cer"] < best["cer"]:
            best = h
    return best


def train(
    base: str | Path,
    out: Path | str,
    *,
    train_samples: Sequence[Sample],
    val_samples: Sequence[Sample],
    settings: Settings,
    device: str,
    epochs: int,
    seed: int = 20261021,
    log: Callable[[str], None] | None = None,
    patience: int = 3,
    stop_file: Path | str | None = None,
    memory_limit_mib: int | None = None,
) -> TrainState:
    """Epoch by epoch: train, validate, save the epoch's weights when its CER is the
    best so far (``<out>/best/``, a loadable checkpoint), record the history in
    ``<out>/state.json``; resumes from the last completed epoch's weights
    (``<out>/last/``) when the state says so. Stops early after ``patience``
    epochs without improvement, or when ``stop_file`` appears."""
    import torch

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cap_memory(memory_limit_mib, device)
    state_path = out_dir / "state.json"
    state = read_state(state_path)
    resume_from: str | Path = base
    if state is not None and state.epoch > 0 and (out_dir / "last").exists():
        resume_from = out_dir / "last"
        if log:
            log(f"resuming after epoch {state.epoch} from {resume_from}")
    else:
        state = TrainState(settings=settings.as_dict())
    processor, model = load_model(resume_from)
    model = prepare_model(model, settings, device)
    optimizer = build_optimizer(model, settings)
    steps_per_epoch = math.ceil(len(train_samples) / (settings.batch_size * settings.accumulate))
    total_steps = steps_per_epoch * epochs
    stop_path = Path(stop_file) if stop_file else out_dir / "STOP"
    no_gain = 0
    for epoch in range(state.epoch, epochs):
        if stop_path.exists():
            if log:
                log(f"stop file {stop_path} found; stopping before epoch {epoch}")
            break
        if log:
            log(f"epoch {epoch} of {epochs}: {len(train_samples):,} lines, {steps_per_epoch} steps")
        _logs, tally = train_steps(
            model,
            processor,
            train_samples,
            settings,
            device=device,
            epochs=1.0,
            seed=seed,
            log=log,
            start_epoch=epoch,
            start_step=state.step,
            optimizer=optimizer,
            total_steps=total_steps,
            stop_check=stop_path.exists,
            memory_limit_mib=memory_limit_mib,
        )
        state.step += tally["steps"]
        v = validate(model, processor, val_samples, device=device, log=log)
        row = {
            "epoch": epoch,
            "step": state.step,
            "lines": tally["lines"],
            "seconds": tally["seconds"],
            "lines_per_s": tally["lines_per_s"],
            "peak_mib": tally["peak_mib"],
            "cer": v["cer"],
            "wer": v["wer"],
            "exact": v["exact"],
            "val_seconds": v["seconds"],
            "at": _now(),
        }
        state.history.append(row)
        improved = state.best_cer is None or v["cer"] < state.best_cer
        if improved:
            state.best_cer, state.best_epoch = v["cer"], epoch
            no_gain = 0
            save_checkpoint(model, processor, out_dir / "best", settings=settings, epoch=epoch)
            (out_dir / "best" / "val-hyps.json").write_text(
                json.dumps(v["hyps"], ensure_ascii=False, indent=0), encoding="utf-8"
            )
        else:
            no_gain += 1
        save_checkpoint(model, processor, out_dir / "last", settings=settings, epoch=epoch)
        state.epoch = epoch + 1
        write_state(state_path, state)
        if log:
            log(
                f"epoch {epoch} done: val CER {100 * v['cer']:.2f} % "
                f"({'best' if improved else f'no gain, {no_gain} of {patience}'}), "
                f"{tally['lines_per_s']:.2f} lines/s, peak {tally['peak_mib']} MiB"
            )
        if no_gain >= patience:
            if log:
                log(f"no improvement for {patience} epochs; stopping")
            break
        if tally["epochs_done"] == 0:  # the stop file interrupted the epoch
            break
    state.finished = _now()
    write_state(state_path, state)
    del model
    _gpu_reset_peak()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    return state


def save_checkpoint(model, processor, path: Path | str, *, settings: Settings, epoch: int) -> Path:
    """A loadable checkpoint: the weights, the configs, the processor, and a note of
    the settings and the epoch (the base's generation config comes along)."""
    p = Path(path)
    tmp = p.with_name(p.name + ".part")
    if tmp.exists():
        import shutil

        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    model.config.use_cache = True
    model.save_pretrained(tmp, safe_serialization=True)
    model.config.use_cache = False
    processor.save_pretrained(tmp)
    (tmp / "k3-training.json").write_text(
        json.dumps({"settings": settings.as_dict(), "epoch": epoch, "saved": _now()}, indent=1),
        encoding="utf-8",
    )
    if p.exists():
        import shutil

        shutil.rmtree(p)
    tmp.replace(p)
    return p


def stage_samples(
    samples: Sequence[Sample],
    manifest: Iterable[Mapping],
    *,
    drop_screen: bool = False,
    readers: Sequence[str] | None = None,
    groups: Sequence[str] | None = None,
) -> list[Sample]:
    """The samples a manifest filter keeps (the ablation without a class: lines the
    screen put outside the band, a reader's rows, a hand group)."""
    by_image: dict[str, Mapping] = {}
    for row in manifest:
        if row.get("image"):
            by_image[Path(row["image"]).as_posix()] = row
    out: list[Sample] = []
    for s in samples:
        key = "/".join(s.image.parts[-3:])
        row = by_image.get(key)
        if row is None:
            out.append(s)
            continue
        if drop_screen and row.get("screen"):
            continue
        if readers is not None and row.get("reader") not in readers:
            continue
        if groups is not None and row.get("group") not in groups:
            continue
        out.append(s)
    return out


__all__ = [
    "DEFAULT_BASE",
    "DEFAULT_OUT",
    "DEFAULT_TRAIN_ROOT",
    "MAX_TARGET_TOKENS",
    "OPTIMIZERS",
    "PILOT_LINES",
    "PILOT_SETTINGS",
    "PilotRow",
    "Sample",
    "Settings",
    "StepLog",
    "TrainState",
    "build_optimizer",
    "cap_memory",
    "choose_best",
    "encode_batch",
    "epoch_order",
    "extrapolate",
    "filter_samples",
    "load_model",
    "lr_at",
    "memory_fraction",
    "pilot_setting",
    "prepare_model",
    "read_list",
    "read_state",
    "save_checkpoint",
    "stage_samples",
    "train",
    "train_steps",
    "validate",
    "write_pilot",
    "write_state",
]
