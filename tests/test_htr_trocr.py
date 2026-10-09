"""Tests for the TrOCR engine on a stub model (offline; no transformers, no torch)."""

from __future__ import annotations

import math

import pytest

from leibniz.htr.trocr import TrOCREngine, mean_token_prob, tidy

PAD, BOS, EOS = 1, 0, 2


class _Tensorish:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return [list(r) for r in self.rows]


class _Inputs:
    def __init__(self, pixel_values):
        self.pixel_values = pixel_values


class _Gen:
    def __init__(self, sequences, scores):
        self.sequences = _Tensorish(sequences)
        self.scores = scores


class _Config:
    pad_token_id = PAD
    eos_token_id = EOS
    bos_token_id = BOS
    decoder_start_token_id = EOS


class _StubModel:
    """Reads the 'image' (a short bytes tag) and emits a scripted token sequence."""

    config = _Config()
    device = "cpu"

    def __init__(self, script: dict[bytes, tuple[list[int], list[float]]]):
        self.script = script
        self.calls: list[int] = []

    def generate(self, pixel, **kw):
        assert kw["num_beams"] == 1 and kw["output_scores"] and kw["return_dict_in_generate"]
        self.calls.append(len(pixel))
        seqs, lps = [], []
        width = max(len(self.script[p][0]) for p in pixel)
        for p in pixel:
            ids, lp = self.script[p]
            seqs.append([EOS, *ids, *([PAD] * (width - len(ids)))])  # decoder start first
            lps.append([*lp, *([0.0] * (width - len(ids)))])
        self._lps = lps
        return _Gen(seqs, object())

    def compute_transition_scores(self, sequences, scores, normalize_logits=True):
        return _Tensorish(self._lps)


class _StubProcessor:
    def __init__(self, texts: dict[bytes, str]):
        self.texts = texts

    def __call__(self, images, return_tensors="pt"):
        return _Inputs(list(images))

    def batch_decode(self, sequences, skip_special_tokens=True, clean_up_tokenization_spaces=True):
        rows = sequences.tolist()
        # the stub recovers the text from the first generated id
        return [self.texts[tuple(r)] for r in rows]


def _engine(batch_size: int = 8) -> tuple[TrOCREngine, _StubModel]:
    script = {
        b"img1": ([11, 12, EOS], [math.log(0.9), math.log(0.8), math.log(0.99)]),
        b"img2": ([21, EOS], [math.log(0.5), math.log(0.9)]),
        b"img3": ([31, 32, 33, EOS], [math.log(1.0)] * 4),
    }
    model = _StubModel(script)
    texts = {}
    # keys are the full padded sequences the model emits (computed per batch width)
    processor = _StubProcessor(texts)

    def decode_rows(sequences, skip_special_tokens=True, clean_up_tokenization_spaces=True):
        out = []
        for r in sequences.tolist():
            first = r[1]
            out.append({11: "Sonnabend", 21: "Den", 31: "Decembris"}[first])
        return out

    processor.batch_decode = decode_rows  # type: ignore[method-assign]

    def loader(model_id, cache_dir, device):
        return processor, model

    eng = TrOCREngine(
        "dh-unibe/trocr-kurrent-XVI-XVII",
        batch_size=batch_size,
        loader=loader,
        decode=lambda b: b,
    )
    return eng, model


def test_version_defaults_to_the_model_id() -> None:
    eng, _ = _engine()
    assert eng.name == "trocr"
    assert eng.version == "dh-unibe/trocr-kurrent-XVI-XVII"
    assert eng._model is None  # nothing loaded until the first call


def test_transcribe_and_conf_in_order_and_in_batches() -> None:
    eng, model = _engine(batch_size=2)
    out = eng.transcribe_conf([b"img1", b"img2", b"img3"])
    assert [t for t, _ in out] == ["Sonnabend", "Den", "Decembris"]
    # mean probability over the generated tokens, EOS and padding left out
    assert out[0][1] == pytest.approx((0.9 + 0.8) / 2)
    assert out[1][1] == pytest.approx(0.5)
    assert out[2][1] == pytest.approx(1.0)
    assert model.calls == [2, 1]
    assert eng.transcribe([b"img2"]) == ["Den"]


def test_mean_token_prob_skips_specials_and_handles_empty() -> None:
    assert mean_token_prob([5, EOS, PAD], [math.log(0.5), 0.0, 0.0], {EOS, PAD}) == pytest.approx(
        0.5
    )
    assert mean_token_prob([EOS], [0.0], {EOS}) is None
    assert mean_token_prob([], [], set()) is None


def test_tidy_closes_the_space_before_punctuation() -> None:
    assert (
        tidy("Conradt , Den 3ten Decembris , Wardt die") == "Conradt, Den 3ten Decembris, Wardt die"
    )
    assert tidy("bekleidet : Der  Umbhang ( so ) .") == "bekleidet: Der Umbhang (so)."
    assert tidy("  vnd daß  ") == "vnd daß"
