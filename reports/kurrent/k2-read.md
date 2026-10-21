# K2: reading the German pieces with the Bern Kurrent reader

Reader `trocr-kurrent-xvi-xvii` over every recognised line on the pages of the census's German pieces (`data/kurrent/german_pieces.jsonl`), the pages being the union of the K1 census's placement and the factory's today; readings in `data/kurrent/k2-readings/` (gitignored), one resumable JSONL in the pilot's row format. Generated 2026-10-21.

## The pages

2,148 German records (1,665 with recognised lines in the census; 1,699 localizable under the factory today). Pages: census 4,734, resolver 4,745, union **4,807** (62 only in the census, 73 only in the resolver); the page set is the same for 1,901 records, narrower today for 217, wider for 25, otherwise different for 5; 25 records are minted under another volume today. **310,831 recognised lines** on the union (the census summed its pieces' lines, pages shared between pieces counted once per piece).

## Where a batch's time goes

One batch of 8 lines (batch size 8, settings {"model": "dh-unibe/trocr-kurrent-XVI-XVII", "batch_size": 8, "dtype": "float32", "use_cache": null, "max_new_tokens": 160, "clean_up_spaces": true}), after a warm-up call; milliseconds per line. *Before* is the pilot's path (the crop encoded to PNG, decoded again by the engine), *after* K2's (the crop handed over as an image).

| stage | before (ms/line) | after (ms/line) |
|---|---:|---:|
| page_decode | 15.2 | 15.2 |
| crop | 1.6 | 1.6 |
| png_encode | 11.4 | — |
| png_decode | 1.3 | — |
| processor | 8.0 | 7.7 |
| transfer | 0.4 | 0.4 |
| generate | 250.2 | 254.6 |
| postprocess | 0.5 | 0.4 |
| **total** | **289.3** | **280.3** |

Generation steps in the batch: 18 (the longest line sets them) for 62 generated tokens over the 8 lines.

## The sweep

The same lines, a sample spread over the job's pages, read with each setting into a scratch file; wall time includes decoding and cutting. The last column counts the readings a setting left identical to `b8-float32`'s on the lines both read.

| setting | batch | dtype | kv cache | lines | seconds | lines/s | ms/line | GPU peak MiB | identical / compared |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| b8-float32 | 8 | float32 | default | 2,000 | 627.8 | 3.19 | 313.9 | 2,418 | 2,000 / 2,000 |
| b16-float32 | 16 | float32 | default | 2,000 | 642.5 | 3.11 | 321.2 | 3,968 | 1,999 / 2,000 |
| b32-float32 | 32 | float32 | default | 2,000 | 678.4 | 2.95 | 339.2 | 6,412 | 2,000 / 2,000 |
| b8-float32-kv | 8 | float32 | on | 2,000 | 216.4 | 9.24 | 108.2 | 2,796 | 2,000 / 2,000 |
| b16-float32-kv | 16 | float32 | on | 2,000 | 187.4 | 10.67 | 93.7 | 4,018 | 2,000 / 2,000 |
| b32-float32-kv | 32 | float32 | on | 2,000 | 164.4 | 12.17 | 82.2 | 6,348 | 1,999 / 2,000 |
| b8-float16-kv | 8 | float16 | on | 2,000 | 726.2 | 2.75 | 363.1 | 1,460 | 1,961 / 2,000 |
| b16-float16-kv | 16 | float16 | on | 2,000 | 606.8 | 3.3 | 303.4 | 2,920 | 1,961 / 2,000 |
| b32-float16-kv | 32 | float16 | on | 2,000 | 540.2 | 3.7 | 270.1 | 5,612 | 1,961 / 2,000 |

## The Dresden check

`leibniz bench kurrent-smoke` for this reader alone, the 383 Kurrent Trace lines, CER under the `philiumm` policy with its 95 % bootstrap interval; a setting is taken only where the CER stays within 0.2 points of K1's.

The last column counts the lines a run read identically to the run *fp32, the checkpoint's defaults (K1's setting, re-read 2026-10-20)* did.

| run | CER | lenient | strict | ms/line | device | identical / compared |
|---|---|---:|---:|---:|---|---:|
| fp32, the checkpoint's defaults (K1's setting, re-read 2026-10-20) | 7.4 % (6.7 %–8.2 %) | 5.2 % | 7.5 % | 343 | cuda:0 | 383 / 383 |
| fp32, kv cache on | 7.4 % (6.7 %–8.2 %) | 5.2 % | 7.5 % | 111 | cuda:0 | 383 / 383 |
| fp16, kv cache on | 7.4 % (6.7 %–8.2 %) | 5.3 % | 7.5 % | 328 | cuda:0 | 378 / 383 |

## The setting

**b16-float32-kv**: batch 16, float32, kv cache on; 10.67 lines/s in the sweep → the job's 310,831 lines in about 8h 05m. Batch 32 reserved 6,348 MiB, past the card's 6,144 MiB (a GTX 1660 Ti; under WSL2 the allocation spills into shared system memory instead of failing), so batch 16 is the fastest setting that fits in 6 GB. The kv cache, which the checkpoint's generation config turns off so that every one of up to 160 steps re-encodes the whole prefix, leaves the Dresden readings identical to the checkpoint's defaults and changes 1 sweep reading in 2,000, as a change of batch size does without it; half precision is slower on this card, which has no tensor cores, and changes 2 % of the readings, so it is not taken.

## The job

Model `dh-unibe/trocr-kurrent-XVI-XVII` on `cuda`, settings {"model": "dh-unibe/trocr-kurrent-XVI-XVII", "batch_size": 16, "dtype": "float32", "use_cache": true, "max_new_tokens": 160, "clean_up_spaces": true}. Lines on the pages 310,831; read **310,831** (307,515 in the last run, 3,316 before it); skipped 0; left 0. Last run: 7h 26m wall, 7h 15m in the engine, 41,367 lines/h; pages 4,807/4,807; finished (started 2026-10-20T23:40:50+00:00, updated 2026-10-21T07:06:53+00:00).
