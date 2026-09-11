# HTR v1 — corpus segmentation + recognition pipeline (Phase C1)

_Leibniz Legible, Phase C1. Generated 2026-09-11T14:20:39Z. Deliverable of PROMPTS C1 (SPECS §3, §4.5, §6, §9). Numeric sections are queried from the store by `leibniz pipeline report`; prose is templated._

## What the pipeline does

Two idempotent, resumable stages advance every page through a status machine on the `pages` table: `pending → segmented → recognized`, with genuine failures diverted to `skipped` **with a reason** (SPECS §3).

- **`segment`** runs the PHILIUMM baseline segmenter over each cached page, writes every line's **geometry** (baseline + polygon) to `lines` with `status='machine'` and no text yet, and computes a per-page **segmentation-statistics** row in `page_stats`.
- **`recognize`** crops each stored line from its geometry — without re-running the neural segmenter — runs the PHILIUMM HTR model (the B1-reproduced 7.95 % CER model), and fills each line's **text** + per-line **confidence**, repointing the line's run/model at the recognition run (the text's provenance, SPECS §4.5).

Both stages are status-driven & resumable (commit per page), idempotent (`--redo` re-processes; re-segmentation clears old lines), fault-tolerant (a bad page is skipped-with-reason and logged, never fatal), provenance-complete (one `runs` row per batch: model@version, params, git SHA, counts, wall time), engine-agnostic (segmenter/recogniser injected, so kraken stays optional), and GPU-aware (`--device`, `--batch-size`; CPU fallback). `--sample N` caps a run for the dev slice.

## Pipeline coverage

- **Pages in scope:** 236,795
- **pending:** 16 (0.0%)
- **segmented:** 0 (0.0%)
- **recognized:** 236,210 (99.8%)
- **skipped:** 569 (0.2%)
- **Lines:** 13,521,583 segmented · 13,508,625 recognised (text + confidence).

## Throughput

| Run | Stage | Model | Input | OK | Failed |
| ---: | --- | --- | ---: | ---: | ---: |
| 4 | segment | blla_ft_leibniz_v1_0.4750 | 500 | 498 | 2 |
| 5 | recognize | FoNDUE-GD_v2_ft_Leibniz | 498 | 0 | 498 |
| 6 | recognize | FoNDUE-GD_v2_ft_Leibniz | 498 | 413 | 85 |
| 7 | recognize | FoNDUE-GD_v2_ft_Leibniz | 498 | 0 | 498 |
| 8 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 9 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 10 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 11 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 12 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 13 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 14 | recognize | FoNDUE-GD_v2_ft_Leibniz | 431 | 55 | 376 |
| 15 | recognize | FoNDUE-GD_v2_ft_Leibniz | 374 | 374 | 0 |
| 17 | segment | blla_ft_leibniz_v1_0.4750 | 102 | 100 | 2 |
| 18 | recognize | FoNDUE-GD_v2_ft_Leibniz | 100 | 0 | 100 |
| 19 | recognize | FoNDUE-GD_v2_ft_Leibniz | 100 | 100 | 0 |
| 21 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 22 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 24 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 25 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 27 | segment | blla_ft_leibniz_v1_0.4750 | 234,628 | 0 | 234,628 |
| 28 | recognize | FoNDUE-GD_v2_ft_Leibniz | 1,341 | 0 | 1,341 |
| 29 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 30 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 31 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 32 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 33 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 34 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 35 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 36 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 37 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 38 | segment | blla_ft_leibniz_v1_0.4750 | 46,930 | 46,857 | 73 |
| 39 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 40 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 41 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 42 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 43 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 44 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 45 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 46 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 47 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 48 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 50 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 51 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 52 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 53 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 54 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 55 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 56 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 57 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 58 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 59 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 60 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 61 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 62 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 63 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 64 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 65 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 66 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 67 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 68 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 69 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 70 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 71 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 72 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 73 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 74 | recognize | FoNDUE-GD_v2_ft_Leibniz | 199,243 | 199,236 | 7 |
| 75 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 76 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 77 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 78 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 79 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10,560 | 10,560 | 0 |
| 80 | recognize | FoNDUE-GD_v2_ft_Leibniz | 882 | 882 | 0 |
| 81 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 82 | recognize | FoNDUE-GD_v2_ft_Leibniz | 4,701 | 4,701 | 0 |
| 83 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 84 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 85 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 86 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 87 | recognize | FoNDUE-GD_v2_ft_Leibniz | 1,363 | 1,363 | 0 |
| 88 | recognize | FoNDUE-GD_v2_ft_Leibniz | 316 | 316 | 0 |
| 89 | recognize | FoNDUE-GD_v2_ft_Leibniz | 100 | 100 | 0 |
| 90 | recognize | FoNDUE-GD_v2_ft_Leibniz | 101 | 101 | 0 |
| 91 | recognize | FoNDUE-GD_v2_ft_Leibniz | 48 | 48 | 0 |
| 92 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 93 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 94 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 95 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 96 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 97 | recognize | FoNDUE-GD_v2_ft_Leibniz | 40 | 40 | 0 |
| 98 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 99 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 100 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 101 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 102 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 103 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 104 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 105 | recognize | FoNDUE-GD_v2_ft_Leibniz | 42 | 42 | 0 |
| 106 | recognize | FoNDUE-GD_v2_ft_Leibniz | 36 | 36 | 0 |
| 107 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 108 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 109 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 110 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 111 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 112 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 113 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 114 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 115 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 116 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 117 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 118 | recognize | FoNDUE-GD_v2_ft_Leibniz | 40 | 40 | 0 |
| 119 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 120 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 121 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 122 | recognize | FoNDUE-GD_v2_ft_Leibniz | 40 | 40 | 0 |
| 123 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 124 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 125 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 126 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 127 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 128 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 129 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 130 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 131 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 132 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 133 | recognize | FoNDUE-GD_v2_ft_Leibniz | 40 | 40 | 0 |
| 134 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 135 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 136 | recognize | FoNDUE-GD_v2_ft_Leibniz | 124 | 124 | 0 |
| 137 | recognize | FoNDUE-GD_v2_ft_Leibniz | 105 | 105 | 0 |
| 138 | recognize | FoNDUE-GD_v2_ft_Leibniz | 72 | 72 | 0 |
| 139 | recognize | FoNDUE-GD_v2_ft_Leibniz | 97 | 97 | 0 |
| 140 | recognize | FoNDUE-GD_v2_ft_Leibniz | 147 | 147 | 0 |
| 141 | recognize | FoNDUE-GD_v2_ft_Leibniz | 82 | 82 | 0 |
| 142 | recognize | FoNDUE-GD_v2_ft_Leibniz | 44 | 44 | 0 |
| 143 | recognize | FoNDUE-GD_v2_ft_Leibniz | 36 | 36 | 0 |
| 144 | recognize | FoNDUE-GD_v2_ft_Leibniz | 28 | 28 | 0 |
| 145 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 146 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 147 | recognize | FoNDUE-GD_v2_ft_Leibniz | 45 | 45 | 0 |
| 148 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 149 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 150 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 151 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 152 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 153 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 154 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 155 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 156 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 157 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 158 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 159 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 160 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 161 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 162 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 163 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 164 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 165 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 166 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 167 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 168 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 169 | recognize | FoNDUE-GD_v2_ft_Leibniz | 134 | 134 | 0 |
| 170 | recognize | FoNDUE-GD_v2_ft_Leibniz | 69 | 69 | 0 |
| 171 | recognize | FoNDUE-GD_v2_ft_Leibniz | 44 | 44 | 0 |
| 172 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 173 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 174 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 175 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 176 | recognize | FoNDUE-GD_v2_ft_Leibniz | 28 | 28 | 0 |
| 177 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 178 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 179 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 180 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 181 | recognize | FoNDUE-GD_v2_ft_Leibniz | 38 | 38 | 0 |
| 182 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 183 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 184 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 185 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 186 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 187 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 188 | recognize | FoNDUE-GD_v2_ft_Leibniz | 36 | 36 | 0 |
| 189 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 190 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 191 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 192 | recognize | FoNDUE-GD_v2_ft_Leibniz | 36 | 36 | 0 |
| 193 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 194 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 195 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 196 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 197 | recognize | FoNDUE-GD_v2_ft_Leibniz | 58 | 58 | 0 |
| 198 | recognize | FoNDUE-GD_v2_ft_Leibniz | 54 | 54 | 0 |
| 199 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 200 | recognize | FoNDUE-GD_v2_ft_Leibniz | 40 | 40 | 0 |
| 201 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 202 | recognize | FoNDUE-GD_v2_ft_Leibniz | 40 | 40 | 0 |
| 203 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 204 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 205 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 206 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 207 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 208 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 209 | recognize | FoNDUE-GD_v2_ft_Leibniz | 52 | 52 | 0 |
| 210 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 211 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 212 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 213 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 214 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 215 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 216 | recognize | FoNDUE-GD_v2_ft_Leibniz | 64 | 0 | 64 |
| 217 | recognize | FoNDUE-GD_v2_ft_Leibniz | 59 | 59 | 0 |
| 218 | recognize | FoNDUE-GD_v2_ft_Leibniz | 61 | 61 | 0 |
| 219 | recognize | FoNDUE-GD_v2_ft_Leibniz | 75 | 75 | 0 |
| 220 | recognize | FoNDUE-GD_v2_ft_Leibniz | 66 | 66 | 0 |
| 221 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 222 | recognize | FoNDUE-GD_v2_ft_Leibniz | 52 | 52 | 0 |
| 223 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 224 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 225 | recognize | FoNDUE-GD_v2_ft_Leibniz | 48 | 48 | 0 |
| 226 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 227 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 228 | recognize | FoNDUE-GD_v2_ft_Leibniz | 39 | 39 | 0 |
| 229 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 230 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 231 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 232 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 233 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |
| 234 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 235 | recognize | FoNDUE-GD_v2_ft_Leibniz | 47 | 47 | 0 |
| 236 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 237 | segment | blla_ft_leibniz_v1_0.4750 | 154 | 154 | 0 |
| 238 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 239 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 240 | recognize | FoNDUE-GD_v2_ft_Leibniz | 46 | 46 | 0 |
| 241 | recognize | FoNDUE-GD_v2_ft_Leibniz | 43 | 43 | 0 |
| 242 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 243 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 244 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 245 | recognize | FoNDUE-GD_v2_ft_Leibniz | 37 | 37 | 0 |
| 246 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 247 | recognize | FoNDUE-GD_v2_ft_Leibniz | 35 | 35 | 0 |
| 248 | recognize | FoNDUE-GD_v2_ft_Leibniz | 34 | 34 | 0 |
| 249 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 250 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 251 | recognize | FoNDUE-GD_v2_ft_Leibniz | 73 | 73 | 0 |
| 252 | segment | blla_ft_leibniz_v1_0.4750 | 1,781 | 1,781 | 0 |
| 253 | segment | blla_ft_leibniz_v1_0.4750 | 3,548 | 3,544 | 4 |
| 254 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 255 | segment | blla_ft_leibniz_v1_0.4750 | 0 | 0 | 0 |
| 256 | recognize | FoNDUE-GD_v2_ft_Leibniz | 32 | 32 | 0 |
| 257 | recognize | FoNDUE-GD_v2_ft_Leibniz | 33 | 33 | 0 |
| 258 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 259 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 260 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 261 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 262 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 263 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 264 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 265 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 266 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 267 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 268 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 269 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 270 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 271 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 272 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 273 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 274 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 275 | recognize | FoNDUE-GD_v2_ft_Leibniz | 49 | 49 | 0 |
| 276 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 277 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 278 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 279 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 280 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 281 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 282 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 283 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 284 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 285 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 286 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 287 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 288 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 289 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 290 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 291 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 292 | recognize | FoNDUE-GD_v2_ft_Leibniz | 16 | 16 | 0 |
| 293 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 294 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 295 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 296 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 297 | recognize | FoNDUE-GD_v2_ft_Leibniz | 28 | 28 | 0 |
| 298 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 299 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 300 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 301 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 302 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 303 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 304 | recognize | FoNDUE-GD_v2_ft_Leibniz | 31 | 31 | 0 |
| 305 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 306 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 307 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 308 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 309 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 310 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 311 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 312 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 313 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 314 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 315 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 316 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 317 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 318 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 319 | recognize | FoNDUE-GD_v2_ft_Leibniz | 15 | 15 | 0 |
| 320 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 321 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 322 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 323 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 324 | recognize | FoNDUE-GD_v2_ft_Leibniz | 17 | 17 | 0 |
| 325 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 326 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 327 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 328 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 329 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 330 | recognize | FoNDUE-GD_v2_ft_Leibniz | 28 | 28 | 0 |
| 331 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 332 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 333 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 334 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 335 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 336 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 337 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 338 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 339 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 340 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 341 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 342 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 343 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 344 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 345 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 346 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 347 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 348 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 349 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 350 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 351 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 352 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 353 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 354 | recognize | FoNDUE-GD_v2_ft_Leibniz | 28 | 28 | 0 |
| 355 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 356 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 357 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 358 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 359 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 360 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 361 | recognize | FoNDUE-GD_v2_ft_Leibniz | 48 | 48 | 0 |
| 362 | recognize | FoNDUE-GD_v2_ft_Leibniz | 41 | 41 | 0 |
| 363 | recognize | FoNDUE-GD_v2_ft_Leibniz | 28 | 28 | 0 |
| 364 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 365 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 366 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 367 | recognize | FoNDUE-GD_v2_ft_Leibniz | 17 | 17 | 0 |
| 368 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 369 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 370 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 371 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 372 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 373 | recognize | FoNDUE-GD_v2_ft_Leibniz | 30 | 30 | 0 |
| 374 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 375 | recognize | FoNDUE-GD_v2_ft_Leibniz | 26 | 26 | 0 |
| 376 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 377 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 378 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 379 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 380 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 381 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 382 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 383 | recognize | FoNDUE-GD_v2_ft_Leibniz | 29 | 29 | 0 |
| 384 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 385 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 386 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 387 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 388 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 389 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 390 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 391 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 392 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 393 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 394 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 395 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 396 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 397 | recognize | FoNDUE-GD_v2_ft_Leibniz | 23 | 23 | 0 |
| 398 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 399 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 400 | recognize | FoNDUE-GD_v2_ft_Leibniz | 27 | 27 | 0 |
| 401 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 402 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 403 | recognize | FoNDUE-GD_v2_ft_Leibniz | 25 | 25 | 0 |
| 404 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 405 | recognize | FoNDUE-GD_v2_ft_Leibniz | 20 | 20 | 0 |
| 406 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 407 | recognize | FoNDUE-GD_v2_ft_Leibniz | 24 | 24 | 0 |
| 408 | recognize | FoNDUE-GD_v2_ft_Leibniz | 22 | 22 | 0 |
| 409 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 410 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 411 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 412 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 413 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 414 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 415 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 416 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 417 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 418 | recognize | FoNDUE-GD_v2_ft_Leibniz | 8 | 8 | 0 |
| 419 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 420 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 421 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 422 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 423 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 424 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 425 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 426 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 427 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 428 | recognize | FoNDUE-GD_v2_ft_Leibniz | 8 | 8 | 0 |
| 429 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 430 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 431 | recognize | FoNDUE-GD_v2_ft_Leibniz | 8 | 8 | 0 |
| 432 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 433 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 434 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 435 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 436 | recognize | FoNDUE-GD_v2_ft_Leibniz | 15 | 15 | 0 |
| 437 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 438 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 439 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 440 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 441 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 442 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 443 | recognize | FoNDUE-GD_v2_ft_Leibniz | 8 | 8 | 0 |
| 444 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 445 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 446 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 447 | recognize | FoNDUE-GD_v2_ft_Leibniz | 18 | 18 | 0 |
| 448 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 449 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 450 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 451 | recognize | FoNDUE-GD_v2_ft_Leibniz | 19 | 19 | 0 |
| 452 | recognize | FoNDUE-GD_v2_ft_Leibniz | 21 | 21 | 0 |
| 453 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 454 | recognize | FoNDUE-GD_v2_ft_Leibniz | 15 | 15 | 0 |
| 455 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 456 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 457 | recognize | FoNDUE-GD_v2_ft_Leibniz | 15 | 15 | 0 |
| 458 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 459 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 460 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 461 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 462 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 463 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 464 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 465 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 466 | recognize | FoNDUE-GD_v2_ft_Leibniz | 15 | 15 | 0 |
| 467 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 468 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 469 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 470 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 471 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 472 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 473 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 474 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 475 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 476 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 477 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 478 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 479 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 480 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 481 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 482 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 483 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 484 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 485 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 486 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 487 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 488 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 489 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 490 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 491 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 492 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 493 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 494 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 495 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 496 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 497 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 498 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 499 | recognize | FoNDUE-GD_v2_ft_Leibniz | 14 | 14 | 0 |
| 500 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 501 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 502 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 503 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 504 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 505 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 506 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 507 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 508 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 509 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 510 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 511 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 512 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 513 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 514 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 515 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 516 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 517 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 518 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 519 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 520 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 521 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 522 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 523 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 524 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 525 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 526 | recognize | FoNDUE-GD_v2_ft_Leibniz | 8 | 8 | 0 |
| 527 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 528 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 529 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 530 | recognize | FoNDUE-GD_v2_ft_Leibniz | 17 | 17 | 0 |
| 531 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 532 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 533 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 534 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 535 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 536 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 537 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 538 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 539 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 540 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 541 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 542 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 543 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 544 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 545 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 546 | recognize | FoNDUE-GD_v2_ft_Leibniz | 11 | 11 | 0 |
| 547 | recognize | FoNDUE-GD_v2_ft_Leibniz | 9 | 9 | 0 |
| 548 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 549 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 550 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 551 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 552 | recognize | FoNDUE-GD_v2_ft_Leibniz | 7 | 7 | 0 |
| 553 | recognize | FoNDUE-GD_v2_ft_Leibniz | 10 | 10 | 0 |
| 554 | recognize | FoNDUE-GD_v2_ft_Leibniz | 8 | 8 | 0 |
| 555 | recognize | FoNDUE-GD_v2_ft_Leibniz | 12 | 12 | 0 |
| 556 | recognize | FoNDUE-GD_v2_ft_Leibniz | 13 | 13 | 0 |
| 557 | recognize | FoNDUE-GD_v2_ft_Leibniz | 15 | 15 | 0 |
| 558 | recognize | FoNDUE-GD_v2_ft_Leibniz | 6 | 6 | 0 |
| 559 | recognize | FoNDUE-GD_v2_ft_Leibniz | 0 | 0 | 0 |

## Per-line confidence

Mean 0.847 · median 0.914 over recognised lines.

| Confidence | Lines |
| --- | ---: |
| < 0.50 | 856,403 |
| 0.50–0.70 | 1,020,971 |
| 0.70–0.80 | 1,173,391 |
| 0.80–0.90 | 2,629,598 |
| ≥ 0.90 | 7,144,691 |

## Per set

| Set | Pages | Segmented | Recognized | Skipped | Mean lines/pg |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leibnitiana | 1,768 | 0 | 1,764 | 4 | 64.5 |
| LeibnizBriefwechsel | 72,284 | 0 | 72,136 | 148 | 54.0 |
| LeibnizHandschriften | 58,828 | 0 | 58,656 | 156 | 78.3 |
| LeibnizMarginalien | 103,887 | 0 | 103,626 | 261 | 47.2 |
| leibniz-rekonstruktionen | 28 | 0 | 28 | 0 | 26.1 |

## Segmentation quality — measured, because it is the known risk

Segmentation is the unsolved half of the corpus (SPECS §9: layered revisions, marginalia, snippets). C1 measures it per page rather than fixing it blindly: `page_stats` records `n_lines`/`n_regions`, `region_coverage`, line-height mean/median/CV (irregular spacing = revised-draft signature), `n_overlaps` (boxes overlapping ≥30 % — layered revisions / marginalia), and `n_short_lines` (< 40 % of median width — interlinear insertions / snippets). These are the raw signal the stratum heuristic reads in C2 (per piece) and C4 (per page).

Over 236,752 segmented pages: mean **57.1 lines/page**, mean region coverage **35.5%**, mean line-height CV **0.22**. **92.2%** of pages have overlapping line boxes; **95.9%** have short lines.

Worst-overlap pages (segmentation-risk candidates for inspection):

| Page | Lines | Overlaps |
| --- | ---: | ---: |
| `00068783:0010` | 198 | 652 |
| `00068783:0019` | 198 | 652 |
| `00068208:0020` | 183 | 647 |
| `00068208:0021` | 183 | 647 |
| `00068369:0409` | 199 | 635 |
| `00068369:0444` | 199 | 635 |
| `00068602:0004` | 200 | 624 |
| `00068602:0005` | 200 | 624 |
| `00068760:0050` | 197 | 620 |
| `00068760:0051` | 197 | 618 |


## Skip / failure taxonomy

| Reason | Pages |
| --- | ---: |
| no_lines | 469 |
| recognize_error | 70 |
| oversize_image | 20 |
| segment_error | 7 |
| no_croppable_lines | 3 |

Anticipated per-set difficulty (quantified once the run completes): **Marginalien** (44 % of pages) is the hard case — annotated printed books whose HTR target is the marginal hand, not the printed body (needs zone separation, STATUS Open Q #5); **Handschriften** carries the layered-revision drafts (high line-height CV / overlaps / short lines); **Briefwechsel** fair copies are the clean stratum; German/Kurrent (~15 % of the corpus) is transcribed but at far higher CER (Latin+French model) — a C4 per-language honesty item, not a skip.

## Operator runbook

```bash
# 1. Install the heavy stack and fetch the PHILIUMM models (CC BY 4.0).
uv pip install kraken pyarrow            # the `bench` extra
leibniz bench fetch                      # HTR model + val split

# 2. Pull a ~500-page dev slice spanning all sets (if not already cached).
leibniz images fetch --set LeibnizHandschriften --limit 150
leibniz images fetch --set LeibnizBriefwechsel  --limit 150
leibniz images fetch --set LeibnizMarginalien   --limit 150
leibniz images fetch --set Leibnitiana          --limit 50

# 3. Run the pipeline on the sample (GPU if available).
leibniz pipeline segment   --sample 500 --device cuda
leibniz pipeline recognize --sample 500 --device cuda --batch-size 32
leibniz pipeline status
leibniz pipeline report                  # refreshes this file

# 4. Full corpus (documented; resumable — checkpoint across invocations):
leibniz pipeline segment   --device cuda
leibniz pipeline recognize --device cuda --batch-size 32
leibniz pipeline report
```

### GPU-hour and cost estimate (full corpus, one pass)

Preliminary, to be calibrated by the sample run's measured pages/hour (recorded in `runs` wall-time): ~3–6 s/page combined (segment + recognize) on a modern GPU → 236,795 pages ≈ **~260 GPU-hours** per pass (range ~120–330 by GPU class / page size / line density) ≈ **$65–330** at $0.5–1.5/GPU-hour. C1 (v1) and C4 (v2) are two passes; SPECS §4.2 budgets 150–300 GPU-hours total. CPU-only is fine for the sample, impractical for the corpus.

### Reproduce / regenerate

```
leibniz pipeline segment [--set S] [--work ID] [--sample N] [--redo] [--device D]
leibniz pipeline recognize [--sample N] [--redo] [--device D] [--batch-size B]
leibniz pipeline status
leibniz pipeline report --out reports/htr-v1-sample.md
```

Models: segmentation `blla_ft_leibniz_v1` (doi:10.5281/zenodo.21537859) + HTR `FoNDUE-GD_v2_ft_Leibniz` (doi:10.5281/zenodo.21457538), both PHILIUMM, CC BY 4.0.
