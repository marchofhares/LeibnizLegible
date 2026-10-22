# K3: the timing pilots

Two candidates timed on this GPU (GTX 1660 Ti, 6 GB) over bounded runs of the training set (55,596 training lines, 3,133 validation lines) and extrapolated to the full plan. Generated 2026-10-21.

## (a) TrOCR from the Bern checkpoint

The memory probe first: every setting on the same 2,000 training lines under a hard allocator cap of 4,000 MiB for the process (an allocation past it fails in-process instead of spilling into host memory under WSL2).

| setting | status | lines | seconds | lines/s | peak MiB | six epochs |
|---|---|---:|---:|---:|---:|---:|
| adamw-b8 | oom | 0 | 0 | — | 3,988 | — |
| adafactor-b8 | oom | 0 | 0 | — | 3,988 | — |
| adamw-frozen-encoder-b8 | oom | 0 | 0 | — | 4,000 | — |
| adafactor-frozen-encoder-b8 | ok | 2,000 | 244 | 8.19 | 3,988 | 11.3 h |
| adafactor-grad-ckpt-b8 | ok | 2,000 | 563 | 3.55 | 3,436 | 26.1 h |
| adafactor-fp16-b8 | oom | 0 | 0 | — | 4,000 | — |
| adafactor-grad-ckpt-fp16-b8 | ok | 2,000 | 2052 | 0.97 | 4,000 | 4.0 days |
| adafactor-b4-x2 | oom | 0 | 0 | — | 3,930 | — |
| adafactor-frozen-encoder-b16 | ok | 2,000 | 195 | 10.23 | 3,956 | 9.1 h |

Then the 20,000-line epochs with the validation set scored:

Base `dh-unibe/trocr-kurrent-XVI-XVII`; up to 20,000 lines per setting; the validation set scored after each run; the projection for 6 epochs over the training lines, validation passes included.

| setting | status | lines | seconds | lines/s | peak MiB | val CER | val lines/s | full plan |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| adafactor-frozen-encoder-b8 | ok | 20,000 | 2428 | 8.24 | 3,488 | 18.78 % | 8.6 | 11.9 h |
| adafactor-grad-ckpt-b8 | ok | 20,000 | 5636 | 3.55 | 3,496 | 13.67 % | 8.6 | 26.7 h |

Fastest feasible setting: **adafactor-frozen-encoder-b8**; lowest validation CER after the pilot run: **adafactor-grad-ckpt-b8**.

## (b) kraken from the PHILIUMM checkpoint

`ketos train` from `data/models/philiumm-htr/FoNDUE-GD_v2_ft_Leibniz.safetensors` with `--resize union` (the codec grew by 20 code points), `-u NFD`, batch 4, learning rate 0.0001, one fixed epoch over 20,000 lines.

| | value |
|---|---:|
| epoch wall time | 2876 s |
| lines/s (training, validation included) | 6.95 |
| peak MiB | 2,776 |
| kraken's validation accuracy | 0.7676 |
| validation CER (philiumm policy, the project's engine) | 24.74 % |
| validation lines/s (inference) | 46.0 |
| full plan (30 epochs) | 2.8 days |

## Against the week

The prompt holds the plan to a week on this GPU (168 h): **within**.
