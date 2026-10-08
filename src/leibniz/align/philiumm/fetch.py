"""Fetch PHILIUMM's alignment worked example, cache-first, at a pinned commit.

The repository (GitLab, no licence file as of the pinned commit) holds one
worked example: the edition reading text of LH I 3,4 Bl. 1–2 (from A VI,4),
two PAGE XML files of HTR lines — each image is one side of the bifolium, so
``0002r-0001v`` shows folios 1v and 2r and ``0002v-0001r`` shows 2v and 1r —
their aligned output (the same files with the matched edition text written
into each line's ``Unicode``, blank where nothing matched) and the CSV report
of that run. Only these files are fetched, by raw URL at the commit named
below, into a directory under ``data/`` (gitignored); nothing from the
repository is copied into this one.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from leibniz.net import PoliteClient, default_user_agent

GITLAB_PROJECT = "eman8/scripts/htr-ocr/alignement-verite-de-terrain-et-transcriptions"
# main as read on 2026-10-08: "Delete temporary files", committed 2026-09-21.
ALIGNER_COMMIT = "9d2ee4e500e049ea3a9767d695bde6c24d1c31d7"
GT_FILE = "GT/LH_1_3_4_0001-0002_1.txt"
HTR_FILES = ("HTR/LH_1_3_4_0002r-0001v.xml", "HTR/LH_1_3_4_0002v-0001r.xml")
THEIR_OUTPUT_FILES = (
    "htr_replaced_gt/LH_1_3_4_0002r-0001v.xml",
    "htr_replaced_gt/LH_1_3_4_0002v-0001r.xml",
)
REPORT_FILE = "alignment_report.csv"
README_FILE = "README.md"
SAMPLE_FILES = (GT_FILE, *HTR_FILES, *THEIR_OUTPUT_FILES, REPORT_FILE, README_FILE)
COMMIT_MARKER = "COMMIT"  # written beside the files: which commit they came from


def raw_url(path: str, *, commit: str = ALIGNER_COMMIT) -> str:
    return f"https://gitlab.com/{GITLAB_PROJECT}/-/raw/{commit}/{path}"


def fetch_sample(
    dest: Path,
    *,
    client: PoliteClient | None = None,
    commit: str = ALIGNER_COMMIT,
    files: tuple[str, ...] = SAMPLE_FILES,
    progress: Callable[[str], None] | None = None,
) -> list[Path]:
    """Download the sample files that are not yet under ``dest``; return all paths.

    A file already on disk is never re-fetched. The commit the files were taken
    from is recorded in ``dest/COMMIT``; a different commit on disk raises, so
    two runs never mix revisions.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / COMMIT_MARKER
    if marker.exists():
        seen = marker.read_text(encoding="utf-8").strip()
        if seen != commit:
            raise RuntimeError(
                f"{dest} holds files from commit {seen[:12]}, not {commit[:12]}; "
                "move it aside to fetch another revision"
            )
    else:
        marker.write_text(commit + "\n", encoding="utf-8")
    missing = [p for p in files if not (dest / p).exists()]
    if missing:
        own = client is None
        client = client or PoliteClient(user_agent=default_user_agent())
        try:
            for rel in missing:
                url = raw_url(rel, commit=commit)
                if progress:
                    progress(f"fetch {url}")
                data = client.get_bytes(url)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        finally:
            if own:
                client.close()
    return [dest / p for p in files]


__all__ = [
    "ALIGNER_COMMIT",
    "GITLAB_PROJECT",
    "GT_FILE",
    "HTR_FILES",
    "REPORT_FILE",
    "SAMPLE_FILES",
    "THEIR_OUTPUT_FILES",
    "fetch_sample",
    "raw_url",
]
