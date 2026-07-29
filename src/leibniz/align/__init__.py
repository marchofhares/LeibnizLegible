"""Align stage — retro-alignment GT factory.

Mints training data by aligning §70-expired Akademie-Ausgabe *reading text* to
manuscript line images (the Bullinger method). Character-level DP alignment
(Needleman-Wunsch / CTC-style) of machine HTR text against normalized edition
text, tolerant of hyphenation and a small Latin-abbreviation rule list; emits
(line image, edition text) pairs with per-line alignment confidence into
``gt_lines``. Below-threshold alignments are discarded, never shipped.

Reading text ONLY, from expired volumes (``leibniz.legal``); never apparatus,
introductions, or commentary (SPECS §7.2).

Prototype in Phase B2; scaled in C2.

Public API (the pure, offline-testable core — ``normalize``/``dp``/``align``/
``pairs`` — plus, importing lazily, the model-driven ``prototype`` and the
vision-LLM ``pdftext``):
"""

from leibniz.align.align import (
    AlignedLine,
    AlignmentResult,
    HtrLine,
    align_piece,
)
from leibniz.align.dp import Alignment, align, similarity
from leibniz.align.normalize import DEFAULT_NORM, AlignNorm, normalize, normalize_indexed
from leibniz.align.pairs import GtPair, insert_gt_pairs, result_to_pairs

__all__ = [
    "DEFAULT_NORM",
    "AlignNorm",
    "AlignedLine",
    "Alignment",
    "AlignmentResult",
    "GtPair",
    "HtrLine",
    "align",
    "align_piece",
    "insert_gt_pairs",
    "normalize",
    "normalize_indexed",
    "result_to_pairs",
    "similarity",
]
