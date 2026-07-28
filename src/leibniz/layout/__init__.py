"""Layout stage — page segmentation (baselines + zones).

Runs Kraken baseline segmentation (PHILIUMM segmentation model, Zenodo
10.5281/zenodo.21537859; RF-DETR zones as backup) to produce per-line polygons
and baselines plus SegmOnto region zones. Computes per-page segmentation stats
(line count, region coverage, overlap anomalies) — the known-risk metric that
feeds the stratum heuristic (SPECS §6).

Implemented in Phase C1.
"""
