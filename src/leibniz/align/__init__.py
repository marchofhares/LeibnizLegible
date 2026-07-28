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
"""
