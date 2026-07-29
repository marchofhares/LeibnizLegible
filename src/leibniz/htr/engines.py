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
import os
import time
from collections.abc import Callable, Sequence

# --------------------------------------------------------------------------- #
# Kraken (local inference)
# --------------------------------------------------------------------------- #

# Recognition preprocessing constants, chosen to match how the PHILIUMM model was
# trained/evaluated (a baseline model on polygon-extracted lines).
KRAKEN_PADDING = 16
KRAKEN_VALID_NORM = False  # baseline models normalise height without box-centering


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
        # accelerator='cpu' wants an int device count, not a device string.
        accelerator = "cpu" if self.device == "cpu" else "auto"
        dev = 1 if self.device == "cpu" else self.device
        cfg = RecognitionInferenceConfig(
            device=dev,
            accelerator=accelerator,
            precision="32-true",
            num_line_workers=0,
            padding=self.padding,
            bidi_reordering=False,
        )
        model.prepare_for_inference(cfg)
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

    def _transcribe_batch(self, tensors: list) -> list[str]:
        torch = self._torch
        max_len = max(t.shape[2] for t in tensors)
        seqs = torch.stack([torch.nn.functional.pad(t, (0, max_len - t.shape[2])) for t in tensors])
        lens = torch.LongTensor([t.shape[2] for t in tensors])
        preds, _olens = self._model._rec_predict(seqs, lens)
        return ["".join(tok[0] for tok in pred) for pred in preds]

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        """Transcribe pre-extracted line images (raw bytes) to text, in order."""
        from PIL import Image

        self._ensure_loaded()
        out: list[str] = []
        buf: list = []
        for data in images:
            im = Image.open(io.BytesIO(data))
            im.load()
            buf.append(self._transforms(im))
            if len(buf) >= self.batch_size:
                out.extend(self._transcribe_batch(buf))
                buf.clear()
        if buf:
            out.extend(self._transcribe_batch(buf))
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
    """

    name = "anthropic"

    def __init__(
        self,
        *,
        model: str = DEFAULT_ANTHROPIC_MODEL,
        api_key: str | None = None,
        prompt: str = DEFAULT_PROMPT,
        max_tokens: int = 256,
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
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._sleep = sleep
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

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    def _one(self, data: bytes) -> str:
        media_type = _sniff_media_type(data)
        b64 = base64.standard_b64encode(data).decode("ascii")
        body = {
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
                        {"type": "text", "text": self.prompt},
                    ],
                }
            ],
        }
        attempt = 0
        while True:
            resp = self._client.post(ANTHROPIC_URL, headers=self._headers(), json=body)
            if resp.status_code in (429, 500, 502, 503, 529) and attempt < self.max_retries:
                attempt += 1
                self._sleep(2.0**attempt)
                continue
            resp.raise_for_status()
            return _extract_text(resp.json())

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        out: list[str] = []
        for i, data in enumerate(images):
            if i and self.min_interval:
                self._sleep(self.min_interval)
            out.append(self._one(data))
        return out


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
}


def estimate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """USD cost estimate from token usage, or ``None`` if the model isn't priced.

    Matches ``model`` against the price table by longest known prefix (so
    ``gpt-4o-2024-08-06`` prices as ``gpt-4o``). Estimate only — see
    :data:`OPENAI_PRICES`.
    """
    rate = OPENAI_PRICES.get(model)
    if rate is None:
        keys = sorted((k for k in OPENAI_PRICES if model.startswith(k)), key=len, reverse=True)
        if not keys:
            return None
        rate = OPENAI_PRICES[keys[0]]
    return input_tokens * rate[0] / 1e6 + output_tokens * rate[1] / 1e6


class OpenAIEngine:
    """OpenAI GPT vision zero-shot line transcription (Chat Completions, httpx).

    Mirrors :class:`AnthropicEngine`: same terse diplomatic prompt, same graceful
    skip (:class:`MissingKeyError`) when no ``OPENAI_API_KEY`` is available. Sends
    each line image as a high-detail ``data:`` image URL and accumulates token
    ``usage`` across the batch (``usage_input`` / ``usage_output``) so the run can
    report exact cost. ``name`` is ``openai``; ``version`` is the model id.
    """

    name = "openai"

    def __init__(
        self,
        *,
        model: str = DEFAULT_OPENAI_MODEL,
        api_key: str | None = None,
        prompt: str = DEFAULT_PROMPT,
        max_tokens: int = 256,
        detail: str = "high",
        temperature: float | None = 0.0,
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
        self.version = model
        self.model = model
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.detail = detail
        self.temperature = temperature
        self.min_interval = min_interval
        self.max_retries = max_retries
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

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}", "content-type": "application/json"}

    def _one(self, data: bytes) -> str:
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
                        {"type": "text", "text": self.prompt},
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
        attempt = 0
        while True:
            resp = self._client.post(OPENAI_URL, headers=self._headers(), json=body)
            if resp.status_code in (429, 500, 502, 503, 529) and attempt < self.max_retries:
                attempt += 1
                self._sleep(2.0**attempt)
                continue
            resp.raise_for_status()
            return self._parse(resp.json())

    def _parse(self, payload: dict) -> str:
        usage = payload.get("usage") or {}
        self.usage_input += int(usage.get("prompt_tokens", 0))
        self.usage_output += int(usage.get("completion_tokens", 0))
        choices = payload.get("choices") or [{}]
        return (choices[0].get("message", {}).get("content") or "").strip()

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        out: list[str] = []
        for i, data in enumerate(images):
            if i and self.min_interval:
                self._sleep(self.min_interval)
            out.append(self._one(data))
        return out


__all__ = [
    "ANTHROPIC_URL",
    "DEFAULT_ANTHROPIC_MODEL",
    "DEFAULT_OPENAI_MODEL",
    "DEFAULT_PROMPT",
    "OPENAI_PRICES",
    "OPENAI_URL",
    "AnthropicEngine",
    "KrakenEngine",
    "MissingKeyError",
    "OpenAIEngine",
    "estimate_openai_cost",
]
