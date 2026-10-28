"""Transcription engine adapters (Phase B1).

Two adapters satisfy the :class:`~leibniz.htr.bench.Engine` protocol:

* :class:`KrakenEngine` — local Kraken inference. Loads a model (CoreML
  ``.mlmodel`` or the newer safetensors container — the PHILIUMM model is the
  latter) and transcribes *pre-extracted* single-line images: the val GT ships
  already-cropped, polygon-dewarped lines, so the adapter runs the recognition
  network directly (``ImageInputTransforms`` with ``valid_norm=False``, the
  baseline-model preprocessing) rather than re-segmenting. Kraken + torch are a
  heavy, optional stack; every kraken symbol is imported lazily so this module —
  and the whole ``htr`` package — imports fine without them.
* :class:`AnthropicEngine` — Claude vision, zero-shot line transcription over the
  Messages API. Uses ``httpx`` (already a project dependency), so no SDK is
  added. **Skips gracefully without a key**: construction raises
  :class:`MissingKeyError` when ``ANTHROPIC_API_KEY`` is unset, which the CLI
  turns into a skip, honouring "everything runs without the key" (COMMON CONTEXT).

Neither adapter is imported at package load; the CLI constructs whichever the run
asks for. Offline tests drive the harness with ``bench.EchoEngine`` instead.
"""

from __future__ import annotations

import base64
import io
import math
import os
import signal
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass

import httpx

# --------------------------------------------------------------------------- #
# One API answer, as the page reader records it (LT1)
# --------------------------------------------------------------------------- #

# The APIs' own stop reasons, folded to four words the page reader can act on:
# ``end`` (the model stopped by itself), ``length`` (the output cap was hit — a
# runaway in the page protocol), ``refusal`` (a safety stop or a content filter),
# ``other:<raw>`` (anything else, kept verbatim).
_STOP_END = {"end_turn", "stop", "stop_sequence", "end"}
_STOP_LENGTH = {"max_tokens", "length"}
_STOP_REFUSAL = {
    "refusal",
    "content_filter",
    "safety",
    "recitation",
    "blocklist",
    "prohibited_content",
    "spii",
}


def classify_stop(raw: str | None) -> str:
    """``end`` | ``length`` | ``refusal`` | ``other:<raw>`` from an API's stop/finish reason."""
    r = (raw or "").strip()
    low = r.lower()
    if low in _STOP_END:
        return "end"
    if low in _STOP_LENGTH:
        return "length"
    if low in _STOP_REFUSAL:
        return "refusal"
    return f"other:{r}" if r else "other:"


@dataclass(slots=True)
class ApiReply:
    """What one call returned: the text, why the model stopped, what it cost in tokens.

    ``output_tokens`` is the API's completion count, which on a thinking model
    includes the reasoning tokens; ``reasoning_tokens`` is the API's own split
    of that count when it reports one (``None`` otherwise).
    """

    text: str
    stop: str
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int | None = None
    attempts: int = 1


def _prefix_rate(
    table: Mapping[str, tuple[float, float]], model: str
) -> tuple[float, float] | None:
    """The table's row for ``model`` by longest known prefix (a dated id → its family)."""
    rate = table.get(model)
    if rate is not None:
        return rate
    keys = sorted((k for k in table if model.startswith(k)), key=len, reverse=True)
    return table[keys[0]] if keys else None


# --------------------------------------------------------------------------- #
# Kraken (local inference)
# --------------------------------------------------------------------------- #

# Recognition preprocessing constants, chosen to match how the PHILIUMM model was
# trained/evaluated (a baseline model on polygon-extracted lines).
KRAKEN_PADDING = 16
KRAKEN_VALID_NORM = False  # baseline models normalise height without box-centering

# Widest transformed line accepted into the net, in px at the model's input
# height. The input transform preserves aspect ratio, so a degenerate ~900×1
# sliver crop resizes to >100k px wide — on the live corpus run a single conv2d
# then allocated 5.3 GB, which under Linux overcommit killed the machine rather
# than raising. Real text lines land around 1–3k px here; slivers beyond the
# cap yield ("", None) instead of entering the net.
MAX_TRANSFORMED_WIDTH = 10_000

# Bound on a batch's *padded* area, as ``n_lines × widest line`` width-units:
# every line in a batch is padded to the widest, so one wide line times a full
# batch multiplies conv memory (a 722 MB single alloc on the live validation
# run). 64k units ≈ a full batch of 16 × 4k-px lines; a wider line simply gets
# a smaller batch. Bounds peak memory on CPU and GPU alike.
MAX_BATCH_PADDED_WIDTH = 64_000


def _should_flush_before(
    n_buffered: int, max_w: int, next_w: int, cap: int = MAX_BATCH_PADDED_WIDTH
) -> bool:
    """True if adding a ``next_w``-wide line would blow the padded-batch budget."""
    return n_buffered > 0 and (n_buffered + 1) * max(max_w, next_w) > cap


def _tok_conf(tok: object) -> float | None:
    """Pull the per-character confidence (a probability in ``[0, 1]``) from a token.

    kraken's decoded tokens are ``(grapheme, …)`` where the trailing fields vary
    by version — kraken 7 emits ``(grapheme, start, end, confidence)``, older
    layouts a cut position or a span before the posterior. The posterior is
    always the *last* field, so scan from the end for the first scalar in
    ``[0, 1]`` (front-to-back scanning misread ``start == 0`` — the first token
    of every line — as a confidence of 0.0). Position fields other than an
    initial 0/1 are ≫ 1 and can't be mistaken for it; return ``None`` when no
    field qualifies, rather than a meaningless number. The original code
    averaged ``tok[1]``, the cut position — the ~150 "confidences" of the first
    real run (STATUS Open Q #15).
    """
    try:
        fields = list(tok)[1:]
    except TypeError:
        return None
    for v in reversed(fields):
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0:
            return float(v)
    return None


def _module_device(model: object):
    """Device of the model's first network parameter (``None`` if unknowable).

    kraken's ``_rec_predict`` runs ``model.nn`` on whatever tensors it is
    handed — it never moves them. After ``prepare_for_inference`` places the
    net on an accelerator, the caller must put its input batches on the same
    device (the live CUDA smoke failed every page on exactly this mismatch).
    """
    try:
        return next(model.nn.parameters()).device  # type: ignore[attr-defined]
    except (AttributeError, StopIteration, TypeError):
        return None


def _accel_device(device: str) -> tuple[str, object]:
    """Map a torch-style device string to kraken's ``(accelerator, device)`` pair.

    kraken's ``RecognitionInferenceConfig`` follows PyTorch-Lightning: ``accelerator``
    selects the hardware and ``device`` is a device **count** (int) or a list of
    device **indices** — never a bare ``"cuda"`` string. The original GPU branch
    passed the string through, so kraken's ``int("cuda")`` blew up on the first
    real CUDA run (there was no GPU in any build/CI environment to catch it). This
    pure mapping is unit-tested; the exact accelerator token ("cuda" vs "gpu") is
    what a live CUDA run confirms.

    ``"cpu"`` → ``("cpu", 1)`` · ``"cuda"``/``"gpu"`` → ``("cuda", 1)`` (one GPU) ·
    ``"cuda:2"`` → ``("cuda", [2])`` (index 2) · ``"mps"`` → ``("mps", 1)`` ·
    anything else → ``("auto", 1)``.
    """
    d = (device or "cpu").strip().lower()
    if d in ("cpu", ""):
        return "cpu", 1
    if ":" in d:  # e.g. "cuda:0" — a specific device index
        head, _, idx = d.rpartition(":")
        accel = "cuda" if head in ("cuda", "gpu", "") else head
        try:
            return accel, [int(idx)]
        except ValueError:
            return accel, 1
    if d in ("cuda", "gpu"):
        return "cuda", 1
    if d == "mps":
        return "mps", 1
    return "auto", 1


class KrakenEngine:
    """Local Kraken recognition over pre-extracted line images.

    Construct with a model path; :meth:`transcribe` takes raw image bytes and
    returns transcriptions. Batches lines (padding to the widest in each batch)
    for throughput on CPU. Deterministic: greedy CTC decode, temperature 1.0.
    """

    name = "kraken"

    def __init__(
        self,
        model_path: str,
        *,
        version: str | None = None,
        device: str = "cpu",
        padding: int = KRAKEN_PADDING,
        batch_size: int = 8,
    ) -> None:
        self.model_path = model_path
        self.version = version or _basename_stem(model_path)
        self.device = device
        self.padding = padding
        self.batch_size = max(1, batch_size)
        self._model = None
        self._transforms = None
        self._torch = None
        self._input_device = None  # where batches must live (set at model load)

    # -- lazy heavy setup --------------------------------------------------- #

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from kraken.configs import RecognitionInferenceConfig
            from kraken.lib.dataset import ImageInputTransforms
            from kraken.models.loaders import load_models
        except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
            raise ModuleNotFoundError(
                "KrakenEngine needs the kraken + torch stack (the optional bench "
                "extra). Install with `uv pip install kraken` in the run env; the "
                "harness itself and its tests do not require it."
            ) from exc

        self._torch = torch
        models = load_models(self.model_path, tasks=["recognition"])
        if not models:
            raise ValueError(f"no recognition model found in {self.model_path}")
        model = models[0]
        # Map our device string to kraken's (accelerator, device count/index) — a
        # bare "cuda" here would make kraken int() a non-number and crash.
        accelerator, dev = _accel_device(self.device)
        cfg = RecognitionInferenceConfig(
            device=dev,
            accelerator=accelerator,
            precision="32-true",
            num_line_workers=0,
            padding=self.padding,
            bidi_reordering=False,
        )
        model.prepare_for_inference(cfg)
        self._input_device = _module_device(model)
        batch, channels, height, width = model.input
        self._transforms = ImageInputTransforms(
            batch,
            height,
            width,
            channels,
            (self.padding, 0),
            valid_norm=KRAKEN_VALID_NORM,
            dtype=model._m_dtype,
        )
        self._model = model

    # -- inference ---------------------------------------------------------- #

    def _batch_tensors(self, tensors: list) -> tuple:
        """Pad to the widest, stack, and move the batch to the model's device.

        ``lens`` stays on CPU (sequence-packing wants CPU lengths); only the
        image batch follows the net onto its accelerator.
        """
        torch = self._torch
        max_len = max(t.shape[2] for t in tensors)
        seqs = torch.stack([torch.nn.functional.pad(t, (0, max_len - t.shape[2])) for t in tensors])
        if self._input_device is not None:
            seqs = seqs.to(self._input_device)
        lens = torch.LongTensor([t.shape[2] for t in tensors])
        return seqs, lens

    def _transcribe_batch(self, tensors: list) -> list[str]:
        seqs, lens = self._batch_tensors(tensors)
        preds, _olens = self._model._rec_predict(seqs, lens)
        return ["".join(tok[0] for tok in pred) for pred in preds]

    def _transcribe_batch_conf(self, tensors: list) -> list[tuple[str, float | None]]:
        """Like :meth:`_transcribe_batch` but also mean per-line CTC confidence."""
        seqs, lens = self._batch_tensors(tensors)
        preds, _olens = self._model._rec_predict(seqs, lens)
        out: list[tuple[str, float | None]] = []
        for pred in preds:
            text = "".join(tok[0] for tok in pred)
            confs = [c for tok in pred if (c := _tok_conf(tok)) is not None]
            out.append((text, sum(confs) / len(confs) if confs else None))
        return out

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        """Transcribe pre-extracted line images (raw bytes) to text, in order."""
        return [t for t, _ in self._run(images, with_conf=False)]

    def transcribe_conf(self, images: Sequence[bytes]) -> list[tuple[str, float | None]]:
        """Transcribe line images to ``(text, mean_confidence)`` pairs, in order.

        The corpus pipeline (:mod:`leibniz.pipeline.recognize`) stores the
        per-line confidence (SPECS §4.5); ``None`` when the model build does not
        expose posteriors.
        """
        return self._run(images, with_conf=True)

    def _run(self, images: Sequence[bytes], *, with_conf: bool) -> list[tuple[str, float | None]]:
        from PIL import Image

        self._ensure_loaded()
        out: list[tuple[str, float | None]] = []
        buf: list = []
        max_w = 0

        def flush() -> None:
            nonlocal max_w
            if not buf:
                return
            if with_conf:
                out.extend(self._transcribe_batch_conf(buf))
            else:
                out.extend((t, None) for t in self._transcribe_batch(buf))
            buf.clear()
            max_w = 0

        for data in images:
            im = Image.open(io.BytesIO(data))
            im.load()
            t = self._transforms(im)
            w = int(t.shape[2])
            if w > MAX_TRANSFORMED_WIDTH:
                flush()  # keep output order around the placeholder
                out.append(("", None))
                continue
            if _should_flush_before(len(buf), max_w, w):
                flush()
            buf.append(t)
            max_w = max(max_w, w)
            if len(buf) >= self.batch_size:
                flush()
        flush()
        return out


def _basename_stem(path: str) -> str:
    from pathlib import Path

    return Path(path).stem


# --------------------------------------------------------------------------- #
# Anthropic (Claude vision, remote)
# --------------------------------------------------------------------------- #

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Approximate list prices, USD per 1M tokens (input, output), for cost *estimates*
# only, as for OPENAI_PRICES below: the run reports the exact usage from each
# response. Read from the Claude API's model table on 2026-10-28 (the
# claude-api skill's cached table of 2026-10-06, the same figures).
ANTHROPIC_PRICES: dict[str, tuple[float, float]] = {
    "claude-fable-5-1": (10.00, 50.00),
    "claude-fable-5": (10.00, 50.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

# Claude's visual tokens: 28 × 28 px patches, the image first fitted into the
# model's tier — Claude 4.7 and later (Fable 5.1 among them): a long edge of
# at most 2,576 px and at most 4,784 visual tokens; larger images are downscaled
# server-side, aspect kept (the vision documentation, read 2026-10-28).
ANTHROPIC_PATCH_PX = 28
ANTHROPIC_MAX_LONG_EDGE = 2576
ANTHROPIC_MAX_VISUAL_TOKENS = 4784


def estimate_anthropic_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """USD cost estimate from token usage, or ``None`` if the model isn't priced."""
    rate = _prefix_rate(ANTHROPIC_PRICES, model)
    if rate is None:
        return None
    return input_tokens * rate[0] / 1e6 + output_tokens * rate[1] / 1e6


def anthropic_image_tokens(width: int, height: int) -> int:
    """Visual tokens Claude charges for an image of this size (the high-resolution tier).

    The image is scaled down, aspect kept, until its long edge is within
    :data:`ANTHROPIC_MAX_LONG_EDGE` and its patch count within
    :data:`ANTHROPIC_MAX_VISUAL_TOKENS`; the count is ``⌈w/28⌉ × ⌈h/28⌉``. An
    estimate for planning: the run records the API's own ``input_tokens``.
    """
    w, h = max(1, width), max(1, height)
    long_edge = max(w, h)
    if long_edge > ANTHROPIC_MAX_LONG_EDGE:
        s = ANTHROPIC_MAX_LONG_EDGE / long_edge
        w, h = max(1, round(w * s)), max(1, round(h * s))

    def patches(a: int, b: int) -> int:
        return math.ceil(a / ANTHROPIC_PATCH_PX) * math.ceil(b / ANTHROPIC_PATCH_PX)

    n = patches(w, h)
    while n > ANTHROPIC_MAX_VISUAL_TOKENS:
        s = math.sqrt(ANTHROPIC_MAX_VISUAL_TOKENS / n) * 0.995
        w, h = max(1, int(w * s)), max(1, int(h * s))
        n = patches(w, h)
    return n


# Zero-shot, image-grounded, and deliberately terse: we want the transcription
# only, no commentary or "I can't read this" hedging that would pollute the CER.
DEFAULT_PROMPT = (
    "This is a single line cropped from a 17th/early-18th-century Western "
    "handwritten manuscript (Leibniz; Latin or French, secretary hand). "
    "Transcribe it diplomatically: exactly the characters written, preserving "
    "original spelling, abbreviations, accents and punctuation. Do not translate, "
    "expand abbreviations, normalise, or add commentary. Output only the "
    "transcription of this one line, nothing else."
)


class MissingKeyError(RuntimeError):
    """Raised when the Anthropic engine is built without an API key available."""


class AnthropicEngine:
    """Claude vision zero-shot line transcription via the Messages API (httpx).

    Honours the project rule that everything runs without a key: if
    ``ANTHROPIC_API_KEY`` is unset (and none is passed), the constructor raises
    :class:`MissingKeyError`, which the CLI catches and reports as a skip. When a
    key is present, each line image is sent as a base64 image block with a terse
    diplomatic-transcription prompt; transient ``429``/``529`` responses are
    retried with backoff and requests are spaced by ``min_interval``.

    The page protocol (LT1) adds ``effort`` (``output_config.effort``: on the
    Claude 5 models thinking is always on and cannot be disabled — ``low`` is
    the lowest setting the API allows, the API's documentation read 2026-10-28)
    and leaves ``temperature`` unsent by default (the current models reject the
    parameter). Token usage accumulates in ``usage_input`` / ``usage_output``
    (the output count includes the thinking tokens); :attr:`cost` prices it.
    """

    name = "anthropic"

    def __init__(
        self,
        *,
        model: str = DEFAULT_ANTHROPIC_MODEL,
        api_key: str | None = None,
        prompt: str = DEFAULT_PROMPT,
        max_tokens: int = 256,
        effort: str | None = None,
        temperature: float | None = None,
        min_interval: float = 0.3,
        max_retries: int = 4,
        timeout: float = 120.0,
        client=None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise MissingKeyError(
                "ANTHROPIC_API_KEY not set — the Claude comparison is skipped "
                "(the harness runs fully without it)."
            )
        self._key = key
        self.version = model
        self.model = model
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.effort = effort
        self.temperature = temperature
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._deadline_s = timeout + 30.0
        self._sleep = sleep
        self.usage_input = 0
        self.usage_output = 0
        self._owns_client = client is None
        if client is None:
            import httpx

            self._client = httpx.Client(timeout=timeout)
        else:
            self._client = client

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> AnthropicEngine:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @property
    def cost(self) -> float | None:
        """Estimated USD cost of everything transcribed so far (or ``None``)."""
        return estimate_anthropic_cost(self.model, self.usage_input, self.usage_output)

    def settings(self) -> dict:
        """The sampling and reasoning settings as sent, for the run's record."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "reasoning": f"effort {self.effort}" if self.effort else "the model's default",
            "thinking": "always on (cannot be disabled on this API's current models)",
        }

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def _body(self, data: bytes, prompt: str) -> dict:
        media_type = _sniff_media_type(data)
        b64 = base64.standard_b64encode(data).decode("ascii")
        body: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }
        if self.effort:
            body["output_config"] = {"effort": self.effort}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        return body

    def reply(self, data: bytes, *, prompt: str | None = None) -> ApiReply:
        """One image, one call: the text, the stop reason and the usage."""
        body = self._body(data, prompt if prompt is not None else self.prompt)
        attempt = 0
        while True:
            try:
                with _call_deadline(self._deadline_s):
                    resp = self._client.post(ANTHROPIC_URL, headers=self._headers(), json=body)
            except _TRANSIENT_CALL_ERRORS:
                if attempt < self.max_retries:
                    attempt += 1
                    self._sleep(2.0**attempt)
                    continue
                raise
            if resp.status_code in (429, 500, 502, 503, 529) and attempt < self.max_retries:
                attempt += 1
                self._sleep(2.0**attempt)
                continue
            if (
                resp.status_code == 400
                and "temperature" in body
                and "temperature" in _error_message(resp)
            ):
                # The current models reject the parameter: drop it and go again.
                body.pop("temperature")
                self.temperature = None
                continue
            resp.raise_for_status()
            payload = resp.json()
            usage = payload.get("usage") or {}
            n_in = int(usage.get("input_tokens", 0))
            n_out = int(usage.get("output_tokens", 0))
            self.usage_input += n_in
            self.usage_output += n_out
            return ApiReply(
                text=_extract_text(payload),
                stop=classify_stop(payload.get("stop_reason")),
                input_tokens=n_in,
                output_tokens=n_out,
                attempts=attempt + 1,
            )

    def _one(self, data: bytes) -> str:
        return self.reply(data).text

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        out: list[str] = []
        for i, data in enumerate(images):
            if i and self.min_interval:
                self._sleep(self.min_interval)
            out.append(self._one(data))
        return out


def _error_message(resp) -> str:
    """The ``error.message`` of an API error response (lower-cased), or ``""``."""
    try:
        return str((resp.json().get("error") or {}).get("message") or "").lower()
    except Exception:
        return ""


def _sniff_media_type(data: bytes) -> str:
    """Guess an image media type from magic bytes (JPEG/PNG; default JPEG)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


def _extract_text(payload: dict) -> str:
    """Pull the concatenated text blocks out of a Messages API response."""
    parts = [
        block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text"
    ]
    return "".join(parts).strip()


# --------------------------------------------------------------------------- #
# OpenAI (GPT vision, remote)
# --------------------------------------------------------------------------- #

DEFAULT_OPENAI_MODEL = "gpt-4o"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Approximate list prices, USD per 1M tokens (input, output), for cost *estimates*
# only — OpenAI's prices and lineup change; the run reports EXACT token usage from
# each response, so the dollar figure is `usage × the rate below` and easy to
# re-derive against current pricing. Verify before quoting.
OPENAI_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-5": (1.25, 10.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5.1": (1.25, 10.00),
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-sol": (4.00, 20.00),
    "gpt-5.6-terra": (2.00, 12.00),
}

# The page protocol asks for reasoning off, or the lowest setting the API
# allows; OpenAI's ``reasoning_effort`` values are model-dependent ("none",
# "minimal", "low", … — the reasoning guide, read 2026-10-28), so a 400 on the
# requested value steps down this chain until one is accepted (``None`` = send
# nothing and take the model's default).
OPENAI_REASONING_FALLBACK: dict[str, str | None] = {
    "none": "minimal",
    "minimal": "low",
    "low": None,
}


def estimate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """USD cost estimate from token usage, or ``None`` if the model isn't priced.

    Matches ``model`` against the price table by longest known prefix (so
    ``gpt-4o-2024-08-06`` prices as ``gpt-4o``). Estimate only — see
    :data:`OPENAI_PRICES`.
    """
    rate = _prefix_rate(OPENAI_PRICES, model)
    if rate is None:
        return None
    return input_tokens * rate[0] / 1e6 + output_tokens * rate[1] / 1e6


def openai_image_tokens(width: int, height: int, *, detail: str = "high") -> int:
    """The Chat Completions image token rule for GPT-4o-class models (an estimate).

    ``high`` detail: the image fitted into 2048 × 2048, then its short side to
    768 px, 170 tokens per 512 × 512 tile plus 85; ``low``: 85.
    """
    if detail == "low":
        return 85
    w, h = max(1, width), max(1, height)
    s = min(1.0, 2048 / max(w, h))
    w, h = w * s, h * s
    s2 = 768 / min(w, h)
    if s2 < 1.0:
        w, h = w * s2, h * s2
    return 85 + 170 * math.ceil(w / 512) * math.ceil(h / 512)


def _param_error(resp) -> str | None:
    """The ``error.param`` of an API error response, if the body parses."""
    try:
        return (resp.json().get("error") or {}).get("param")
    except Exception:
        return None


# Errors worth a backoff-and-retry inside one call: httpx's own timeouts and
# transport failures, plus the TimeoutError our wall-clock deadline raises.
_TRANSIENT_CALL_ERRORS = (TimeoutError, httpx.TransportError)


@contextmanager
def _call_deadline(seconds: float):
    """Raise ``TimeoutError`` if one API call outlives ``seconds`` (SIGALRM).

    A live panel run hung for 30+ minutes inside ``ssl read`` waiting for
    response headers: the proxied connection died without FIN/RST and httpx's
    configured read timeout never fired on the tunneled socket. A wall-clock
    alarm converts any such stall into an exception the per-call retry loop
    handles. Mirrors ``pipeline.recognize._crop_deadline``; no-op off the main
    thread or where SIGALRM is unavailable.
    """
    if (
        seconds <= 0
        or not hasattr(signal, "SIGALRM")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return

    def _timeout(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"API call exceeded {seconds:.0f}s deadline")

    old = signal.signal(signal.SIGALRM, _timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old)


class OpenAIEngine:
    """OpenAI GPT vision zero-shot line transcription (Chat Completions, httpx).

    Mirrors :class:`AnthropicEngine`: same terse diplomatic prompt, same graceful
    skip (:class:`MissingKeyError`) when no ``OPENAI_API_KEY`` is available. Sends
    each line image as a high-detail ``data:`` image URL and accumulates token
    ``usage`` across the batch (``usage_input`` / ``usage_output``) so the run can
    report exact cost. ``name`` is ``openai``; ``version`` is the model id.

    The page protocol (LT1) adds ``reasoning_effort``: the value asked for is
    sent as is, and a 400 naming the parameter steps down
    :data:`OPENAI_REASONING_FALLBACK` (``none`` → ``minimal`` → ``low`` → the
    model's default) so a run never dies on a model that lacks a level; the
    value that was accepted is what :meth:`settings` reports.
    """

    name = "openai"

    def __init__(
        self,
        *,
        model: str = DEFAULT_OPENAI_MODEL,
        api_key: str | None = None,
        url: str = OPENAI_URL,
        prompt: str = DEFAULT_PROMPT,
        max_tokens: int = 256,
        detail: str = "high",
        temperature: float | None = 0.0,
        reasoning_effort: str | None = None,
        min_interval: float = 0.2,
        max_retries: int = 4,
        timeout: float = 120.0,
        client=None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise MissingKeyError(
                "OPENAI_API_KEY not set — the OpenAI comparison is skipped "
                "(the harness runs fully without it)."
            )
        self._key = key
        self.url = url
        self.version = model
        self.model = model
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.detail = detail
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._deadline_s = timeout + 30.0
        self._sleep = sleep
        self.usage_input = 0
        self.usage_output = 0
        self._owns_client = client is None
        if client is None:
            import httpx

            self._client = httpx.Client(timeout=timeout)
        else:
            self._client = client

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> OpenAIEngine:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @property
    def cost(self) -> float | None:
        """Estimated USD cost of everything transcribed so far (or ``None``)."""
        return estimate_openai_cost(self.model, self.usage_input, self.usage_output)

    def settings(self) -> dict:
        """The sampling and reasoning settings as sent, for the run's record."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "reasoning": (
                f"reasoning_effort {self.reasoning_effort}"
                if self.reasoning_effort
                else "the model's default (no reasoning_effort sent)"
            ),
            "detail": self.detail,
        }

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}", "content-type": "application/json"}

    def _body(self, data: bytes, prompt: str) -> dict:
        media_type = _sniff_media_type(data)
        b64 = base64.standard_b64encode(data).decode("ascii")
        body: dict = {
            "model": self.model,
            # `max_completion_tokens` is the current field (superseding max_tokens)
            # and is accepted across the GPT-4o/4.1/5 vision models.
            "max_completion_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64}",
                                "detail": self.detail,
                            },
                        },
                    ],
                }
            ],
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort
        self._extend_body(body)
        return body

    def _extend_body(self, body: dict) -> None:
        """A subclass's extra fields (Gemini's thinking level)."""

    def _step_down_reasoning(self, body: dict) -> bool:
        """After a 400 on ``reasoning_effort``: the next value of the chain into ``body``
        (or the field removed); False when nothing is left to try."""
        current = body.get("reasoning_effort")
        if current is None:
            return False
        nxt = OPENAI_REASONING_FALLBACK.get(current)
        if nxt is None:
            body.pop("reasoning_effort", None)
        else:
            body["reasoning_effort"] = nxt
        self.reasoning_effort = nxt
        return True

    def reply(self, data: bytes, *, prompt: str | None = None) -> ApiReply:
        """One image, one call: the text, the finish reason and the usage."""
        body = self._body(data, prompt if prompt is not None else self.prompt)
        attempt = 0
        while True:
            try:
                with _call_deadline(self._deadline_s):
                    resp = self._client.post(self.url, headers=self._headers(), json=body)
            except _TRANSIENT_CALL_ERRORS:
                if attempt < self.max_retries:
                    attempt += 1
                    self._sleep(2.0**attempt)
                    continue
                raise
            if resp.status_code in (429, 500, 502, 503, 529) and attempt < self.max_retries:
                attempt += 1
                self._sleep(2.0**attempt)
                continue
            if resp.status_code == 400:
                param = _param_error(resp)
                if "temperature" in body and param == "temperature":
                    # gpt-5.x-class models pin temperature to the default and 400 on
                    # any explicit value (verified live) — drop the field and go again.
                    body.pop("temperature")
                    self.temperature = None
                    continue
                if (
                    "reasoning_effort" in body
                    and (param == "reasoning_effort" or "reasoning_effort" in _error_message(resp))
                    and self._step_down_reasoning(body)
                ):
                    continue
            resp.raise_for_status()
            return self._parse(resp.json(), attempts=attempt + 1)

    def _one(self, data: bytes) -> str:
        return self.reply(data).text

    def _parse(self, payload: dict, *, attempts: int = 1) -> ApiReply:
        usage = payload.get("usage") or {}
        n_in = int(usage.get("prompt_tokens", 0))
        n_out = int(usage.get("completion_tokens", 0))
        self.usage_input += n_in
        self.usage_output += n_out
        details = usage.get("completion_tokens_details") or {}
        reasoning = details.get("reasoning_tokens")
        choices = payload.get("choices") or [{}]
        first = choices[0] if choices else {}
        return ApiReply(
            text=((first.get("message") or {}).get("content") or "").strip(),
            stop=classify_stop(first.get("finish_reason")),
            input_tokens=n_in,
            output_tokens=n_out,
            reasoning_tokens=int(reasoning) if reasoning is not None else None,
            attempts=attempts,
        )

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        out: list[str] = []
        for i, data in enumerate(images):
            if i and self.min_interval:
                self._sleep(self.min_interval)
            out.append(self._one(data))
        return out


# --------------------------------------------------------------------------- #
# Gemini (Google's OpenAI-compatible Chat Completions endpoint)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

# Same caveat as OPENAI_PRICES: approximate list rates for estimates only.
# gemini-3.8-flash is the introductory rate (through 2026-12-31; doubles
# 2027-01-01); thinking tokens bill at the output rate and are included in
# the API's reported completion_tokens. The 3.1 Pro and Argon rows were read
# from the Gemini API pricing page on 2026-10-28: 3.1 Pro's rate for prompts
# of at most 200k tokens (4.00 / 18.00 above that; a page is far below);
# gemini-4-argon's introductory rate through 2026-11-30 (4.00 / 20.00 from
# 2026-12-01 — a run after that date re-derives its cost from the logged usage).
GEMINI_PRICES: dict[str, tuple[float, float]] = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "gemini-4-argon": (2.00, 10.00),
}

# Gemini's image tokens (the image-understanding documentation, read
# 2026-10-28): an image within 384 × 384 px costs 258 tokens; a larger one is
# cut into 768 × 768 tiles of 258 tokens each, the tile count from the shorter
# side divided by 1.5 (their example: 960 × 540 → a unit of 360 → 3 × 2 = 6
# tiles). An estimate for planning; the run records the API's prompt_tokens.
GEMINI_TILE_TOKENS = 258


def gemini_image_tokens(width: int, height: int) -> int:
    """Gemini's documented tiling rule for an image of this size (an estimate)."""
    w, h = max(1, width), max(1, height)
    if w <= 384 and h <= 384:
        return GEMINI_TILE_TOKENS
    unit = max(1, min(w, h) // 1.5)
    return GEMINI_TILE_TOKENS * math.ceil(w / unit) * math.ceil(h / unit)


def estimate_gemini_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """USD cost estimate from token usage (longest-prefix match, like OpenAI's)."""
    rate = _prefix_rate(GEMINI_PRICES, model)
    if rate is None:
        return None
    return input_tokens * rate[0] / 1e6 + output_tokens * rate[1] / 1e6


class GeminiEngine(OpenAIEngine):
    """Gemini vision zero-shot line transcription via Google's OpenAI-compat endpoint.

    Verified live: the endpoint accepts the exact :class:`OpenAIEngine` request
    shape (data-URL image blocks, ``max_completion_tokens``, ``temperature``) and
    returns OpenAI-shaped ``usage``, so this is a thin subclass — Google's URL,
    ``GEMINI_API_KEY`` (or ``GOOGLE_API_KEY``), Gemini pricing. Thinking models
    spend reasoning tokens *inside* ``max_completion_tokens`` (they bill as
    output), so give them a generous cap or the visible answer truncates
    (observed on gemini-3.8-flash at the 256 default: finish_reason=length after
    6 visible tokens).

    The page protocol (LT1) adds ``thinking_level``: Gemini 3.x Pro and Gemini 4
    Argon take ``low`` | ``medium`` | ``high`` and have no "off" (the thinking
    documentation, read 2026-10-28); it travels in the endpoint's
    ``extra_body.google.thinking_config`` and cannot be combined with
    ``reasoning_effort``, so the engine sends one or the other.
    """

    name = "gemini"

    def __init__(
        self,
        *,
        model: str = DEFAULT_GEMINI_MODEL,
        api_key: str | None = None,
        url: str = GEMINI_URL,
        thinking_level: str | None = None,
        **kwargs,
    ) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise MissingKeyError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) not set — the Gemini comparison "
                "is skipped (the harness runs fully without it)."
            )
        super().__init__(model=model, api_key=key, url=url, **kwargs)
        self.thinking_level = thinking_level
        if thinking_level and self.reasoning_effort:
            raise ValueError("thinking_level and reasoning_effort cannot both be set")

    @property
    def cost(self) -> float | None:
        """Estimated USD cost of everything transcribed so far (or ``None``)."""
        return estimate_gemini_cost(self.model, self.usage_input, self.usage_output)

    def settings(self) -> dict:
        s = super().settings()
        if self.thinking_level:
            s["reasoning"] = f"thinking_level {self.thinking_level} (no off on this model family)"
        return s

    def _extend_body(self, body: dict) -> None:
        if self.thinking_level:
            cfg = {"thinking_level": self.thinking_level}
            body["extra_body"] = {"google": {"thinking_config": cfg}}


__all__ = [
    "ANTHROPIC_PRICES",
    "ANTHROPIC_URL",
    "DEFAULT_ANTHROPIC_MODEL",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_OPENAI_MODEL",
    "DEFAULT_PROMPT",
    "GEMINI_PRICES",
    "GEMINI_URL",
    "OPENAI_PRICES",
    "OPENAI_REASONING_FALLBACK",
    "OPENAI_URL",
    "AnthropicEngine",
    "ApiReply",
    "GeminiEngine",
    "KrakenEngine",
    "MissingKeyError",
    "OpenAIEngine",
    "anthropic_image_tokens",
    "classify_stop",
    "estimate_anthropic_cost",
    "estimate_gemini_cost",
    "estimate_openai_cost",
    "gemini_image_tokens",
    "openai_image_tokens",
]
