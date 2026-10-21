"""Tests for the training modules' bookkeeping (K3 Task 2): no torch, no kraken."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from leibniz.htr import train_kraken as K
from leibniz.htr import train_trocr as T

# --------------------------------------------------------------------------- #
# TrOCR
# --------------------------------------------------------------------------- #


def test_settings_key_names_the_knobs() -> None:
    assert T.Settings().key == "adafactor-b8"
    s = T.Settings(
        optimizer="adamw",
        freeze_encoder=True,
        grad_checkpointing=True,
        fp16=True,
        batch_size=4,
        accumulate=2,
    )
    assert s.key == "adamw-frozen-encoder-grad-ckpt-fp16-b4-x2"
    assert s.as_dict()["key"] == s.key
    assert T.PILOT_SETTINGS[0].optimizer == "adamw" and not T.PILOT_SETTINGS[0].freeze_encoder


def test_extrapolate_and_schedule() -> None:
    e = T.extrapolate(
        10.0, train_lines=36_000, epochs=2, val_lines=3_600, val_lines_per_s=10.0, evals=2
    )
    assert abs(e["train_hours"] - 2.0) < 1e-9 and abs(e["val_hours"] - 0.2) < 1e-9
    assert abs(e["days"] - 2.2 / 24) < 1e-9
    assert T.extrapolate(None, train_lines=1, epochs=1)["days"] is None
    assert T.lr_at(0, base=1e-4, warmup=10, total=100) == 1e-5
    assert T.lr_at(10, base=1e-4, warmup=10, total=100) == 1e-4
    assert abs(T.lr_at(100, base=1e-4, warmup=10, total=100) - 1e-5) < 1e-12
    assert T.lr_at(5, base=1e-4, warmup=0, total=0) == 1e-4


def test_epoch_order_is_seeded_per_epoch() -> None:
    a = T.epoch_order(10, 0, 1)
    assert a == T.epoch_order(10, 0, 1) and sorted(a) == list(range(10))
    assert a != T.epoch_order(10, 1, 1)


def test_read_list_and_stage_samples(tmp_path: Path) -> None:
    root = tmp_path / "set"
    rows = []
    for i, (split, page, screen, reader) in enumerate(
        [
            ("train", "P1", [], "v1"),
            ("train", "P1", ["ratio_high"], "trocr"),
            ("train", "P2", [], "trocr"),
            ("val", "P3", [], "trocr"),
        ]
    ):
        d = root / split / page
        d.mkdir(parents=True, exist_ok=True)
        img = d / f"{i:03d}.png"
        img.write_bytes(b"png")
        img.with_suffix(".gt.txt").write_text(f"line {i}\n", encoding="utf-8")
        rows.append(
            {
                "image": f"{split}/{page}/{i:03d}.png",
                "screen": screen,
                "reader": reader,
                "group": "other" if i else "leibniz",
            }
        )
    (root / "train" / "P2" / "orphan.png").write_bytes(b"png")  # no sidecar: skipped
    lst = root / "train.txt"
    listed = [str(root / r["image"]) for r in rows if r["image"].startswith("train")]
    listed.append(str(root / "train/P2/orphan.png"))
    lst.write_text("".join(ln + "\n" for ln in listed), encoding="utf-8")
    samples = T.read_list(lst)
    assert [s.text for s in samples] == ["line 0", "line 1", "line 2"]
    assert samples[0].line_id == "P1:000"
    kept = T.stage_samples(samples, rows, drop_screen=True)
    assert [s.text for s in kept] == ["line 0", "line 2"]
    assert [s.text for s in T.stage_samples(samples, rows, readers=["v1"])] == ["line 0"]
    assert [s.text for s in T.stage_samples(samples, rows, groups=["leibniz"])] == ["line 0"]


def test_state_round_trip_and_choose_best(tmp_path: Path) -> None:
    st = T.TrainState(
        epoch=2,
        step=40,
        best_cer=0.2,
        best_epoch=1,
        history=[{"epoch": 0, "cer": 0.3}, {"epoch": 1, "cer": 0.2}, {"epoch": 2, "cer": 0.2}],
    )
    p = tmp_path / "state.json"
    T.write_state(p, st)
    back = T.read_state(p)
    assert back is not None and back.epoch == 2 and back.best_cer == 0.2
    assert T.read_state(tmp_path / "none.json") is None
    assert T.choose_best(st.history)["epoch"] == 1
    assert T.choose_best([{"epoch": 0}]) is None


def test_pilot_row_drops_the_hypotheses(tmp_path: Path) -> None:
    row = T.PilotRow(settings={"key": "x"}, status="ok", val={"cer": 0.1, "hyps": {"a": "b"}})
    d = row.as_dict()
    assert "hyps" not in d["val"] and d["val"]["cer"] == 0.1
    p = T.write_pilot(tmp_path / "pilot.json", [row], {"n": 1})
    assert json.loads(p.read_text(encoding="utf-8"))["rows"][0]["status"] == "ok"


# --------------------------------------------------------------------------- #
# kraken
# --------------------------------------------------------------------------- #


def test_ketos_command_carries_the_settings(tmp_path: Path) -> None:
    s = K.KetosSettings(batch_size=8, lr=2e-4, epochs=1, quit="fixed", augment=True)
    cmd = K.ketos_command(s, train_list="t.txt", val_list="v.txt", out_dir=tmp_path / "o")
    assert cmd[0] == "ketos" and "train" in cmd
    joined = " ".join(cmd)
    assert "-t t.txt" in joined and "-e v.txt" in joined
    assert "--resize union" in joined and "-u NFD" in joined and "-B 8" in joined
    assert "-r 0.0002" in joined and "-q fixed" in joined and "-N 1" in joined
    assert "--augment" in cmd and "--normalize-whitespace" in cmd
    assert f"-i {K.DEFAULT_BASE}" in joined
    assert f"-o {tmp_path / 'o' / 'checkpoints'}" in joined and "--checkpoint-path" not in joined
    assert s.key == "ketos-b8-lr0.0002-union-augment"


def test_subset_list_is_seeded(tmp_path: Path) -> None:
    src = tmp_path / "train.txt"
    src.write_text("".join(f"/x/{i}.png\n" for i in range(100)), encoding="utf-8")
    a = K.subset_list(src, tmp_path / "a.txt", n=10, seed=1).read_text(encoding="utf-8")
    b = K.subset_list(src, tmp_path / "b.txt", n=10, seed=1).read_text(encoding="utf-8")
    assert a == b and len(a.splitlines()) == 10
    assert a != K.subset_list(src, tmp_path / "c.txt", n=10, seed=2).read_text(encoding="utf-8")


def test_checkpoints_best_weights_and_epoch_times(tmp_path: Path) -> None:
    d = tmp_path / "run" / "checkpoints"
    d.mkdir(parents=True)
    now = time.time()
    for ep, metric, dt in ((0, 0.8012, -300), (1, 0.8500, -200), (2, 0.8400, -100)):
        p = d / f"checkpoint_{ep:02d}-{metric:.4f}.ckpt"
        p.write_bytes(b"")
        os.utime(p, (now + dt, now + dt))
    (d / "best_0.8500.safetensors").write_bytes(b"w")
    cks = K.read_checkpoints(tmp_path / "run")
    assert [c.epoch for c in cks] == [0, 1, 2] and cks[1].val_metric == 0.85
    assert [round(t) for t in K.epoch_times(cks)] == [100, 100]
    bw = K.best_weights(tmp_path / "run")
    assert bw is not None and bw[1] == 0.85 and bw[0].name == "best_0.8500.safetensors"
    assert K.best_weights(tmp_path / "nothing") is None
    dest = K.install_best(tmp_path / "run", tmp_path / "run" / "best.safetensors")
    assert dest is not None and dest.read_bytes() == b"w"


def test_parse_log_and_account(tmp_path: Path) -> None:
    text = (
        "Loading from checkpoint x.safetensors.\n"
        "INFO Resizing codec to include 32 new code points.\n"
        "Epoch 0: 100%|████| 100/100 [00:10<00:00]\n"
        "Converting best model run/checkpoints/checkpoint_01-0.8500.ckpt (score: 0.8500) to "
        "weights file run/checkpoints/best_0.8500.safetensors\n"
    )
    parsed = K.parse_log(text)
    assert parsed["resized"] == 32 and parsed["best"]["score"] == 0.85
    assert parsed["best"]["weights"].endswith("best_0.8500.safetensors")
    s = K.KetosSettings()
    acc = K.account(tmp_path / "run", s, ["ketos", "train"], text)
    assert acc.best is None and acc.log["resized"] == 32
    p = K.write_account(tmp_path / "acc.json", acc)
    assert json.loads(p.read_text(encoding="utf-8"))["settings"]["key"] == s.key


def test_score_weights_with_a_stub_engine(tmp_path: Path) -> None:
    class Echo:
        def transcribe(self, images):
            return ["abc" for _ in images]

    imgs = []
    for i, text in enumerate(["abc", "abd"]):
        p = tmp_path / f"{i}.png"
        p.write_bytes(b"x")
        imgs.append(T.Sample(p, text))
    sc = K.score_weights("w", imgs, engine_factory=lambda _w: Echo())
    assert sc["n"] == 2 and abs(sc["cer"] - 1 / 6) < 1e-9 and sc["exact"] == 1
