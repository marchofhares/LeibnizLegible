# K3: renting a 24 GB card for Task 3 — the arithmetic, before any spending

Written at Checkpoint B (2026-10-21) as the K3 prompt and the operator's note
of 21 October ask: the plan does **not** exceed a week on this GPU, so this
note exists for the operator's other rule — rent a 24 GB card if it saves
more than two days — and because a 24 GB card changes *what* can be trained,
not only how long it takes. Nothing has been rented; the "would" numbers
below are assumptions, marked as such, not measurements.

## What this GPU does (measured, `reports/kurrent/k3-pilots.md`)

| job | pace on the GTX 1660 Ti (6 GB) | six epochs / thirty epochs |
|---|---:|---:|
| TrOCR, whole model, Adafactor + gradient checkpointing, batch 8 | 3.55 lines/s | 26.7 h |
| TrOCR, frozen encoder, Adafactor, batch 8 | 8.24 lines/s | 11.9 h |
| kraken from PHILIUMM, batch 4 × 4, two loader workers (loader-bound, 16 % GPU use) | 6.95 lines/s all-in | 2.8 days (30 epochs; early stopping will stop sooner) |

The card cannot run AdamW on the whole model, nor Adafactor on the whole
model without checkpointing (out of memory at the 4,000 MiB cap the process
may use beside the desktop's 1.2 GB), nor half precision at a useful pace.

## What a rental would change (assumptions)

- **TrOCR.** A 24 GB card runs the whole model under AdamW at batch 16–32
  without checkpointing. If a current 24 GB card is taken as three to five
  times this one per step and checkpointing's recomputation (about 2.3× here)
  falls away, six epochs would take roughly 2–4 h instead of 26.7 h: **about
  one day saved**, and a better optimiser than Adafactor.
- **kraken.** The pace here is the loader's (PNG decoding and the line
  transforms on the CPU; 16 % GPU use), so a rented *card* changes little; a
  rented *machine* with more cores and NVMe storage, with 8 loader workers,
  might run an epoch in under an hour instead of 2.2: **one to two days saved
  over a thirty-epoch run**, fewer if early stopping ends it early here too.
- Total: of the order of two days, on the operator's threshold, with the
  uncertainty of assumptions on both sides. The firmer argument for renting is
  the first bullet's second half: the model trained, not the days.

## What to rent, and the cost (prices found 21 October 2026; verify before renting)

An RTX 4090 (24 GB) on a marketplace or community tier: RunPod Community Cloud
about $0.34/h (Secure Cloud about $0.74/h), Vast.ai offers from $0.20/h with a
median near $0.48/h (prices move hourly), Salad about $0.33/h; Lambda does not
list the card. Take a machine with at least 8 vCPUs, 32 GB RAM and 60 GB of
fast disk. At $0.5/h: the TrOCR training (4 h) ≈ $2; the kraken training
(a day) ≈ $12; a day of slack ≈ $12 — **under $50 in all**, well inside
SPECS §10's $300–1,000 GPU line. The risk is operational, not financial: a
preemptible instance stopped mid-run, data transfer time, and a different
CUDA stack to debug.

## How to move the data and run (exact commands)

```bash
# on the desktop: the crops (9.4 GB), the frozen split lists and the manifest, the bases
tar -C data/train -cf - k3 | zstd -T8 -3 > /mnt/d/leibniz-train/k3-trainset.tar.zst   # about 9 GB
rsync -avP /mnt/d/leibniz-train/k3-trainset.tar.zst data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors <rented>:/workspace/
# on the rented machine (Ubuntu, CUDA 12.x or 13.x, Python 3.12)
git clone https://github.com/marchofhares/leibnizlegible && cd leibnizlegible && git checkout k3-kurrent-model
uv venv .venv-k1 --python 3.12 && UV_PROJECT_ENVIRONMENT=.venv-k1 uv sync --extra bench --extra gt --extra kurrent
mkdir -p data/train && tar -C data/train -xf - < <(zstd -d -c /workspace/k3-trainset.tar.zst)
mkdir -p data/models/philiumm-htr && cp /workspace/FoNDUE-GD_v2_ft_Leibniz.safetensors data/models/philiumm-htr/
# TrOCR, the whole model under AdamW (the pilot's loop; --max-mib 0 lifts the cap on a 24 GB card)
export UV_PROJECT_ENVIRONMENT=.venv-k1
nohup uv run leibniz bench train-trocr --settings adamw-b8 --batch-size 16 --epochs 6 --max-mib 0 --out data/models/k3/trocr --log logs/k3-trocr.log > logs/k3-trocr.out 2>&1 &
# kraken, eight loader workers
nohup uv run leibniz bench train-kraken --batch-size 16 --workers 8 --epochs -1 --lag 5 --out data/models/k3/kraken --start --log logs/k3-kraken.log &
# afterwards: tar data/models/k3 back to the desktop's /mnt/d/leibniz-train/k3/ and run Task 4 there
```

The runs rows (one per training, SPECS §4.5) are written on the desktop
store afterwards from the trainings' accounts, not from the rented machine.
