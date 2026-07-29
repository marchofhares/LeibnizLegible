"""HTR stage — recognition, benchmarking, and fine-tuning.

Kraken-stack handwritten-text recognition: run the PHILIUMM model (Zenodo
10.5281/zenodo.21457538, self-reported CER 8.33%) and, later, the fine-tuned
``leibniz-htr-v2``. Houses the engine-agnostic evaluation harness (deliverable
D5), a first-class deliverable, not a helper.

Modules (Phase B1):

* ``metrics`` — CER/WER, the named normalization policy, bootstrap CIs.
* ``bench`` — the harness: ``LinePair`` input, the ``Engine`` protocol,
  ``evaluate`` / ``score_hypotheses``, ``EvalResult``, the frozen protocol.
* ``engines`` — ``KrakenEngine`` (local, lazy heavy imports) + ``AnthropicEngine``
  (Claude vision via httpx; skips without a key).
* ``data`` — loaders (HF parquet val split, image+sidecar-text dir).
* ``artifacts`` — fetch/cache the PHILIUMM model + val split (cache-first).
* ``report`` — render ``reports/philiumm-repro.md`` + the gate verdict.
* ``cli`` — ``leibniz bench {fetch,protocol,run,repro}``.

Nothing heavy (kraken, torch, pyarrow) is imported at package load; those are the
optional ``bench`` extra, pulled in lazily by the adapters/loaders that need them.
Corpus recognition lands in C1; fine-tune in C3.
"""
