"""The budget of the two index files (ARCH2, 2026-11-19).

``STATUS.md`` and ``PROMPTS.md`` are indexes: a session writes its record in its own
file under ``status/`` and its prompt goes to ``prompts/`` (``status/README.md`` has the
rule). Before that every session appended to the two files, and they grew without
bound. These tests fail when an index outgrows its budget or names a file that is not
there; each message says what to do.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
STATUS = REPO / "STATUS.md"
PROMPTS = REPO / "PROMPTS.md"

STATUS_MAX_LINES = 600
STATUS_MAX_BYTES = 80_000
PROMPTS_MAX_LINES = 400
LAST_UPDATED_MAX_BULLETS = 5

CURE = (
    "Move the text to the session's phase file under status/ (a prompt as run to "
    "prompts/) and keep one line with a pointer here; never raise the number in passing. "
    "See status/README.md."
)

# A file under status/ or prompts/ named in running text, such as status/2026-10-21-k3.md:
# not a placeholder (status/<yyyy-mm-dd>-<slug>.md) and not a path inside another folder.
NAMED_FILE = re.compile(r"(?<![\w./-])(?:status|prompts)/[\w.-]+\.md\b")


def lines_of(path: Path) -> list[str]:
    """The file's lines as ``wc -l`` counts them: split at newlines and nothing else."""
    text = path.read_text(encoding="utf-8")
    return text.removesuffix("\n").split("\n") if text else []


def last_updated_bullets(lines: list[str]) -> list[str]:
    """The bullets under the ``_Last updated:_`` line, up to the first other text."""
    start = next((i for i, line in enumerate(lines) if line.startswith("_Last updated")), None)
    if start is None:
        return []
    bullets: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("- "):
            bullets.append(line)
        elif line.strip():
            break
    return bullets


def named_files(text: str) -> set[str]:
    """Every ``status/….md`` and ``prompts/….md`` path the text names."""
    return set(NAMED_FILE.findall(text))


@pytest.mark.parametrize(
    ("path", "limit"),
    [(STATUS, STATUS_MAX_LINES), (PROMPTS, PROMPTS_MAX_LINES)],
    ids=["STATUS.md", "PROMPTS.md"],
)
def test_an_index_stays_within_its_line_budget(path: Path, limit: int) -> None:
    count = len(lines_of(path))
    assert count <= limit, f"{path.name} has {count:,} lines; its budget is {limit:,}. {CURE}"


def test_status_stays_within_its_byte_budget() -> None:
    size = len(STATUS.read_bytes())
    assert size <= STATUS_MAX_BYTES, (
        f"STATUS.md has {size:,} bytes; its budget is {STATUS_MAX_BYTES:,}. {CURE}"
    )


def test_last_updated_has_at_most_five_bullets() -> None:
    bullets = last_updated_bullets(lines_of(STATUS))
    assert bullets, (
        "STATUS.md has no bullet under a line that starts with '_Last updated': the head "
        "carries the newest sessions there, one short bullet each. See status/README.md."
    )
    assert len(bullets) <= LAST_UPDATED_MAX_BULLETS, (
        f"'Last updated' in STATUS.md has {len(bullets)} bullets; it keeps the newest "
        f"{LAST_UPDATED_MAX_BULLETS}. Drop the oldest: its session's record is in its phase "
        "file under status/. See status/README.md."
    )


@pytest.mark.parametrize("path", [STATUS, PROMPTS], ids=["STATUS.md", "PROMPTS.md"])
def test_every_phase_and_prompt_file_an_index_names_exists(path: Path) -> None:
    named = named_files(path.read_text(encoding="utf-8"))
    assert named, (
        f"{path.name} names no file under status/ or prompts/: it is the index of those "
        "files. See status/README.md."
    )
    missing = sorted(name for name in named if not (REPO / name).is_file())
    assert not missing, (
        f"{path.name} names {len(missing)} file(s) that do not exist: {', '.join(missing)}. "
        "Write the file (a session's record goes to status/<yyyy-mm-dd>-<slug>.md, its "
        "prompt to prompts/ under the same name) or correct the name. See status/README.md."
    )


def test_the_helpers_read_what_the_rule_describes() -> None:
    head = [
        "# STATUS",
        "",
        "_Last updated:_",
        "",
        "- 2026-11-19: the newest → `status/2026-11-19-arch2.md`",
        "- 2026-11-18: the one before",
        "",
        "_A line that is not a bullet ends the list._",
        "",
        "- a bullet further down belongs to another list",
    ]
    assert [b[2:12] for b in last_updated_bullets(head)] == ["2026-11-19", "2026-11-18"]
    assert last_updated_bullets(["# no such line", "- a bullet"]) == []

    text = (
        "see `status/2026-10-21-k3.md`, prompts/2026-11-17-r1.md and (status/README.md); "
        "a new file is status/<yyyy-mm-dd>-<slug>.md or prompts/<the same name>.md; "
        "reports/status/x.md and STATUS-archive.md are not under the two folders."
    )
    assert named_files(text) == {
        "status/2026-10-21-k3.md",
        "prompts/2026-11-17-r1.md",
        "status/README.md",
    }
