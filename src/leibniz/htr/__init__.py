"""HTR stage — recognition, benchmarking, and fine-tuning.

Kraken-stack handwritten-text recognition: run the PHILIUMM model (Zenodo
10.5281/zenodo.21457538, self-reported CER 8.33%) and, later, the fine-tuned
``leibniz-htr-v2``. Houses the engine-agnostic evaluation harness
(``bench.py``: pluggable ``kraken`` / ``anthropic`` adapters, CER/WER with
bootstrap CIs, frozen protocol) — a first-class deliverable (D5), not a helper.

Benchmark harness in Phase B1; corpus recognition in C1; fine-tune in C3.
"""
