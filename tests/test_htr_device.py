"""Tests for the kraken device-string mapping (regression: the 'cuda' crash).

The GPU branch of :class:`leibniz.htr.engines.KrakenEngine` passed a bare "cuda"
string where kraken wants an int device count, so kraken's ``int("cuda")`` raised
`ValueError: invalid literal for int() with base 10: 'cuda'` on the first real
CUDA run. :func:`_accel_device` fixes the mapping; these lock it down offline (no
kraken/torch import — the function is pure).
"""

from __future__ import annotations

from leibniz.htr.engines import _accel_device, _tok_conf


def test_cpu() -> None:
    assert _accel_device("cpu") == ("cpu", 1)


def test_cuda_is_not_stringified() -> None:
    # The regression: must NOT return the bare "cuda" string as the device.
    accel, dev = _accel_device("cuda")
    assert accel == "cuda"
    assert dev == 1
    assert not isinstance(dev, str)


def test_gpu_alias() -> None:
    assert _accel_device("gpu") == ("cuda", 1)


def test_cuda_with_index() -> None:
    assert _accel_device("cuda:0") == ("cuda", [0])
    assert _accel_device("cuda:2") == ("cuda", [2])


def test_mps() -> None:
    assert _accel_device("mps") == ("mps", 1)


def test_unknown_falls_back_to_auto() -> None:
    assert _accel_device("something-weird") == ("auto", 1)


def test_none_and_empty_default_to_cpu() -> None:
    assert _accel_device("") == ("cpu", 1)
    assert _accel_device(None) == ("cpu", 1)  # type: ignore[arg-type]


def test_case_insensitive() -> None:
    assert _accel_device("CUDA") == ("cuda", 1)
    assert _accel_device("Cuda:1") == ("cuda", [1])


# -- _tok_conf: pull the [0,1] confidence out of a kraken token ---------------- #


def test_tok_conf_finds_probability_after_cut_position() -> None:
    # (grapheme, cut_position_px, confidence) — the real kraken shape that broke.
    assert _tok_conf(("a", 152, 0.91)) == 0.91


def test_tok_conf_two_field_token() -> None:
    assert _tok_conf(("x", 0.5)) == 0.5


def test_tok_conf_ignores_pixel_positions() -> None:
    # No field in [0,1] → None, never the ~150 pixel value that caused the bug.
    assert _tok_conf(("a", 152)) is None
    assert _tok_conf(("a", 100, 2000)) is None


def test_tok_conf_span_then_conf() -> None:
    # A (start,end) span field is non-scalar and skipped; the 0.8 is picked.
    assert _tok_conf(("a", (10, 30), 0.8)) == 0.8


def test_tok_conf_no_numeric_fields() -> None:
    assert _tok_conf(("a",)) is None
