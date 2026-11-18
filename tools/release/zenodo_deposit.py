#!/usr/bin/env python3
"""Zenodo, up to the draft (REL1): reserve a record's DOI, then upload its files.

    python tools/release/zenodo_deposit.py reserve --root /mnt/d/leibniz-release/2026-11-20 \\
        --record transcriptions [--dry-run] [--sandbox]
    python tools/release/zenodo_deposit.py upload  --root … --record transcriptions [--dry-run]

``reserve`` creates the draft, prints the DOI Zenodo reserves and writes it into
RELEASE.json at the root; ``leibniz release cards --out <root>`` then puts it into
the cards; ``upload`` writes the metadata and the files onto the draft (resumable:
run it again after an interruption) and stops. **It never publishes**: the operator
reads the draft in the browser and publishes it there.

The token is read from the environment variable ZENODO_TOKEN and from nowhere
else; ``--dry-run`` prints every request instead of sending it and needs no
token. The logic and its tests: src/leibniz/release/zenodo.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from leibniz.release import state as S
from leibniz.release import zenodo as Z


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("step", choices=("reserve", "upload"))
    parser.add_argument("--root", required=True, type=Path, help="the release root")
    parser.add_argument("--record", required=True, choices=S.RECORDS)
    parser.add_argument("--dry-run", action="store_true", help="print the requests; send nothing")
    parser.add_argument("--sandbox", action="store_true", help="sandbox.zenodo.org (test DOIs)")
    parser.add_argument(
        "--new", action="store_true", help="reserve: create a draft although one is recorded"
    )
    args = parser.parse_args(argv)
    try:
        token = None if args.dry_run else Z.token_from_env()
        api = Z.Zenodo(token, base=Z.SANDBOX if args.sandbox else Z.BASE, dry_run=args.dry_run)
        if args.step == "reserve":
            Z.reserve(args.root, args.record, api, new=args.new)
        else:
            Z.upload(args.root, args.record, api)
    except Z.ZenodoError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
