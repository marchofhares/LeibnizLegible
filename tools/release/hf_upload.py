#!/usr/bin/env python3
"""The Hugging Face mirror (REL1): one record's folder to a dataset or model repository.

    python tools/release/hf_upload.py --root /mnt/d/leibniz-release/2026-11-20 \\
        --record transcriptions --namespace <user-or-organisation> [--dry-run]

The repository ``<namespace>/<folder>`` is created private (or found), README.md
goes up first, then the other files as they are, one commit each; a file the
repository already holds with the same SHA-256 is skipped, so a run that was
interrupted is run again. The repository stays private until the operator makes
it public. Mirrored: transcriptions, gt, model — the NC-derived deposit (gt-nc)
is refused: it is on Zenodo only.

The token is read from the environment variable HF_TOKEN and from nowhere else
(the library's token file is not consulted); ``--dry-run`` prints what would be
sent and needs no token. The logic and its tests: src/leibniz/release/hub.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from leibniz.release import hub as H
from leibniz.release import state as S


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", required=True, type=Path, help="the release root")
    parser.add_argument("--record", required=True, choices=S.RECORDS)
    parser.add_argument(
        "--namespace", help="the Hub user or organisation (default: RELEASE.json's hf.namespace)"
    )
    parser.add_argument("--dry-run", action="store_true", help="print the plan; send nothing")
    parser.add_argument(
        "--allow-public", action="store_true", help="add files to a repository already public"
    )
    args = parser.parse_args(argv)
    try:
        namespace = args.namespace or S.hf_namespace(S.load_release(args.root))
        if not namespace:
            raise H.HubError("no namespace: pass --namespace (or set it with `release cards`)")
        api = None if args.dry_run else H.make_api(H.token_from_env())
        H.upload_folder(
            args.root,
            args.record,
            namespace,
            api=api,
            dry_run=args.dry_run,
            allow_public=args.allow_public,
        )
    except H.HubError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
