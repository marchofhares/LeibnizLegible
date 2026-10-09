"""TrOCR line reader (Phase K1): the bootstrap candidates for German Kurrent.

A TrOCR model (Li et al. 2021) is a vision encoder with a text decoder that
reads **one line image per call**; the Hub holds Kurrent fine-tunes of it
(dh-unibe/trocr-kurrent-XVI-XVII, fgho/trocr-hanseXVII-kurrent, …) which
this project tests as readers for its German stratum before training
anything. :class:`TrOCREngine` wraps one of them behind both of the project's
reader protocols, the shape :class:`~leibniz.htr.engines.KrakenEngine` has:

* the bench harness's :class:`~leibniz.htr.bench.Engine` — ``transcribe`` over
  line image bytes → texts, ``name`` and ``version``;
* the pipeline's :class:`~leibniz.pipeline.recognize.Recognizer` —
  ``transcribe_conf`` → ``(text, confidence or None)`` per line.

The confidence is the mean probability of the generated tokens (greedy
decoding, the per-step log-probabilities from ``compute_transition_scores``),
a number in ``[0, 1]`` comparable in spirit to kraken's mean character
confidence, not in scale: a token is a sub-word, not a character.

transformers and torch are the optional ``kurrent`` + ``bench`` extras and are
imported lazily; the loader and the image decoder are injectable, so the
engine's logic is tested on a stub without either. Weights go to
``data/models/hf`` (gitignored) on first use, cache-first, inference files
only: the checkpoints' optimizer states are never fetched.
"""

from __future__ import annotations

import io
import math
import re
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from pathlib import Path

HF_CACHE_DIR = Path("data/models/hf")

# Which files a TrOCR checkpoint needs at inference: the configs, the tokenizer
# files (vocab.json + merges.txt or tokenizer.json), the processor config, the
# weights. Everything else in a training checkpoint (optimizer.pt, scheduler,
# rng state, a duplicate pytorch_model.bin) stays on the Hub.
INFERENCE_PATTERNS: tuple[str, ...] = ("*.json", "*.txt", "model.safetensors")

Loader = Callable[[str, Path, str], tuple[object, object]]
Decoder = Callable[[bytes], object]


def snapshot(model_id: str, cache_dir: Path | str = HF_CACHE_DIR) -> Path:
    """Fetch a checkpoint's inference files into ``cache_dir`` (cache-first)."""
    from huggingface_hub import snapshot_download

    return Path(
        snapshot_download(
            repo_id=model_id, cache_dir=str(cache_dir), allow_patterns=list(INFERENCE_PATTERNS)
        )
    )


def load_pretrained(model_id: str, cache_dir: Path, device: str) -> tuple[object, object]:
    """The production loader: processor + model from the Hub cache, on ``device``."""
    try:
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
        raise ModuleNotFoundError(
            "TrOCREngine needs transformers and torch (the optional kurrent + bench "
            "extras): `uv sync --extra bench --extra gt --extra kurrent`."
        ) from exc
    local = snapshot(model_id, cache_dir)
    processor = TrOCRProcessor.from_pretrained(str(local))
    model = VisionEncoderDecoderModel.from_pretrained(str(local))
    model.eval()
    if device != "cpu" and not torch.cuda.is_available():
        device = "cpu"
    model.to(device)
    return processor, model


def decode_rgb(data: bytes) -> object:
    """Line image bytes → an RGB PIL image (TrOCR's processor wants three channels)."""
    from PIL import Image

    im = Image.open(io.BytesIO(data))
    im.load()
    return im.convert("RGB")


def mean_token_prob(ids: Sequence[int], logps: Sequence[float], skip: set[int]) -> float | None:
    """Mean probability of the generated tokens, special tokens left out.

    ``ids`` are the generated token ids (without the decoder-start token) and
    ``logps`` their log-probabilities, as ``compute_transition_scores`` returns
    them; padding after the end-of-sequence token is in ``skip``. ``None`` when
    nothing was generated.
    """
    probs = [math.exp(lp) for tid, lp in zip(ids, logps, strict=False) if tid not in skip]
    return sum(probs) / len(probs) if probs else None


def _special_ids(model: object) -> set[int]:
    out: set[int] = set()
    for cfg_name in ("config", "generation_config"):
        cfg = getattr(model, cfg_name, None)
        if cfg is None:
            continue
        for attr in ("pad_token_id", "eos_token_id", "bos_token_id", "decoder_start_token_id"):
            value = getattr(cfg, attr, None)
            if isinstance(value, int):
                out.add(value)
    return out


class TrOCREngine:
    """A TrOCR line reader behind the bench and pipeline protocols."""

    name = "trocr"

    def __init__(
        self,
        model_id: str,
        *,
        version: str | None = None,
        device: str = "cpu",
        batch_size: int = 8,
        cache_dir: Path | str = HF_CACHE_DIR,
        max_new_tokens: int = 160,
        clean_up_spaces: bool = True,
        loader: Loader | None = None,
        decode: Decoder | None = None,
    ) -> None:
        self.model_id = model_id
        self.version = version or model_id
        self.device = device
        self.batch_size = max(1, batch_size)
        self.cache_dir = Path(cache_dir)
        self.max_new_tokens = max_new_tokens
        # The Kurrent fine-tunes were trained on labels that set a space before
        # every punctuation mark ("Wardt die ,"), a Transkribus export convention,
        # and they reproduce it. A diplomatic scorer charges each such space as
        # an insertion against ground truth written the usual way, and the
        # aligner folds punctuation away regardless, so the engine tidies them
        # (:func:`tidy`) unless told not to; the smoke-test report says so.
        self.clean_up_spaces = clean_up_spaces
        self._loader = loader or load_pretrained
        self._decode = decode or decode_rgb
        self._processor: object | None = None
        self._model: object | None = None
        self._skip: set[int] = set()

    # -- lazy heavy setup --------------------------------------------------- #

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        self._processor, self._model = self._loader(self.model_id, self.cache_dir, self.device)
        self._skip = _special_ids(self._model)
        dev = getattr(self._model, "device", None)
        if dev is not None:
            self.device = str(dev)

    # -- inference ---------------------------------------------------------- #

    def transcribe(self, images: Sequence[bytes]) -> list[str]:
        """Transcribe line images (raw bytes) to text, in order."""
        return [t for t, _ in self._run(images)]

    def transcribe_conf(self, images: Sequence[bytes]) -> list[tuple[str, float | None]]:
        """Transcribe line images to ``(text, mean token probability)``, in order."""
        return self._run(images)

    def _run(self, images: Sequence[bytes]) -> list[tuple[str, float | None]]:
        self._ensure_loaded()
        assert self._processor is not None and self._model is not None
        try:
            import torch

            guard = torch.inference_mode
        except ModuleNotFoundError:  # the stub path
            guard = nullcontext
        out: list[tuple[str, float | None]] = []
        for start in range(0, len(images), self.batch_size):
            batch = [self._decode(data) for data in images[start : start + self.batch_size]]
            with guard():
                out.extend(self._generate(batch))
        return out

    def _generate(self, pil_images: list) -> list[tuple[str, float | None]]:
        processor, model = self._processor, self._model
        inputs = processor(images=pil_images, return_tensors="pt")  # type: ignore[operator]
        pixel = inputs.pixel_values
        if hasattr(pixel, "to"):
            pixel = pixel.to(getattr(model, "device", self.device))
        gen = model.generate(  # type: ignore[attr-defined]
            pixel,
            max_new_tokens=self.max_new_tokens,
            num_beams=1,
            do_sample=False,
            output_scores=True,
            return_dict_in_generate=True,
        )
        texts = processor.batch_decode(  # type: ignore[attr-defined]
            gen.sequences,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=self.clean_up_spaces,
        )
        scores = model.compute_transition_scores(  # type: ignore[attr-defined]
            gen.sequences, gen.scores, normalize_logits=True
        )
        ids_rows = _rows(gen.sequences)
        lp_rows = _rows(scores)
        result: list[tuple[str, float | None]] = []
        for text, ids, lps in zip(texts, ids_rows, lp_rows, strict=True):
            # sequences carry the decoder-start token first; the scores do not
            conf = mean_token_prob(ids[1:], lps, self._skip)
            result.append((tidy(text) if self.clean_up_spaces else text.strip(), conf))
        return result


_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?)\]])")
_SPACE_AFTER_OPEN = re.compile(r"([(\[])\s+")


def tidy(text: str) -> str:
    """Collapse whitespace and close the gap a BPE reader leaves around punctuation."""
    text = " ".join(text.split())
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    return _SPACE_AFTER_OPEN.sub(r"\1", text)


def _rows(value: object) -> list[list]:
    """A tensor (or a nested list) as a list of rows."""
    tolist = getattr(value, "tolist", None)
    return list(tolist()) if callable(tolist) else [list(r) for r in value]  # type: ignore[union-attr]


__all__ = [
    "HF_CACHE_DIR",
    "INFERENCE_PATTERNS",
    "TrOCREngine",
    "decode_rgb",
    "load_pretrained",
    "mean_token_prob",
    "snapshot",
    "tidy",
]
