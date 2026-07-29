"""Corpus-scale batch pipeline (Phase C1).

Two idempotent, resumable, status-driven stages over the ``pages`` table:

    pending ──[segment]──▶ segmented ──[recognize]──▶ recognized
                     └────────────────[skipped + reason]

* :mod:`leibniz.pipeline.segment` runs the PHILIUMM baseline segmenter over every
  cached page, stores each line's geometry (baseline/polygon) in ``lines`` with
  ``status='machine'`` and text still empty, and computes per-page segmentation
  statistics (:mod:`leibniz.pipeline.stats`) into ``page_stats`` — the layout
  signal the C2/C4 stratum heuristic reads.
* :mod:`leibniz.pipeline.recognize` crops each segmented line from its stored
  geometry, runs the PHILIUMM HTR model, and fills in ``text`` + per-line
  ``conf``, repointing the line's run/model at the recognition run (SPECS §4.5).

Both stages are engine-agnostic: they take a segmenter / recogniser object (the
kraken-backed :class:`~leibniz.layout.segment.PageSegmenter` and
:class:`~leibniz.htr.engines.KrakenEngine` in production; trivial fakes in the
offline tests), record every batch in ``runs`` with the git SHA, tolerate and log
per-page failures without dying, and support ``--redo``/``--sample``. The heavy
kraken/torch stack lives behind those injected objects, so this package and its
whole test-suite import and run without it.
"""

from __future__ import annotations
