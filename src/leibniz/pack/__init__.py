"""The Calculemus seam (Phase G1): fragment packs out, judgment packs in.

Calculemus, the game deployed beside the site, asks players which of two
readings of a manuscript line the image bears out. Its SPECS §6.6 freezes the
contract for both repositories (schema_version 1, JSONL, one object per line);
``fragment_pack.schema.json`` and ``judgment_pack.schema.json`` here mirror it.

* :mod:`leibniz.pack.fragments` — ``leibniz pack fragments``: German A/B pairs
  (the stored v1 text against K2's Bern reading) from the store, read-only,
  with gold rows from K2's reader-minted ground truth in the open deposit.
* :mod:`leibniz.pack.check` — ``leibniz pack check``: a pack against the
  contract, run on every pack before it leaves the desktop.
* :mod:`leibniz.pack.judgments` — ``leibniz pack judgments``: the game's
  converged judgments as ``corrected`` lines (dry run unless ``--write``),
  the both-rejected lines as the Scriptorium queue (``reports/scriptorium-queue.md``).

NOTES.md section B has the rescope this serves; SPECS §11 records the seam.
"""
