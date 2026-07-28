"""Enrich stage — per-line language ID + per-page stratum heuristic.

Language identification (fast classifier — lingua/fasttext class — with a
``mixed`` label for code-switched lines; la/fr/de are the classes that matter)
and a per-page stratum label derived from segmentation stats + katalog type,
calibrated against the GT audit. The field is named ``stratum_heuristic`` on
purpose — honesty in naming (SPECS §6).

Implemented in Phase C4.
"""
