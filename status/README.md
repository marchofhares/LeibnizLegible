# status/ — the rule every session follows

_Written by ARCH2 on 2026-11-19. STATUS.md and PROMPTS.md were the two files
every session appended to, and parallel sessions collided in them at every
merge. From now on each session writes its own files and the two are indexes._

## Reading

- `STATUS.md` is the index. Read it in full; it is short on purpose.
- Then read the phase files your prompt names. "The K3 entry" means
  `status/2026-10-21-k3.md`: the phase table in `STATUS.md` maps every name to
  its file. Inside a phase file, what an older text calls "the Phase log" and
  "under Next" are the sections "Phase log" and "Hand-over".
- Entries before 2026-10-19 are in `STATUS-archive.md`, the prompts run before
  ARCH1 in `PROMPTS-archive.md`.
- An open question is one line in `STATUS.md` and its full text in
  `status/open-questions.md`. The divergences recorded to 2026-11-18 are in
  `status/divergences-to-2026-11-18.md`.

## Writing

- A session writes its whole record in ONE file,
  `status/<yyyy-mm-dd>-<slug>.md`: the day it starts, the phase id in lower
  case. A session that continues a phase writes on in that phase's file.
- The file has four sections, "Current state", "Phase log", "Divergences" and
  "Hand-over", and is kept current after every task, so that a fresh session
  can take over from it.
- Where an older prompt, the session preamble or a comment in the code says
  "write the entry in STATUS.md", "prepend your entry to Current state and the
  Phase log" or "record it under Divergences", it means this file.
- In `STATUS.md` a session touches only:
  - its row in the phase table (a new row at the top);
  - one bullet at the top of "Last updated", 200 characters at most, dropping
    the oldest beyond five;
  - the Key-numbers rows it changed;
  - the Open-questions index lines it adds or closes (the full text goes to
    `status/open-questions.md`; numbers are permanent and never reused);
  - its items in "Next": done items removed, new ones one or two lines each,
    with a pointer to the hand-over that carries the commands.
- The prompt as run goes, verbatim, to `prompts/<the same name>.md`, with a
  row in the table of `PROMPTS.md`. Where an older prompt says "append the
  prompt verbatim to PROMPTS.md", it means that file.
- Names of individuals stay out of every file: the role and the date.

## The budget

`STATUS.md` holds at most 600 lines and 80,000 bytes and `PROMPTS.md` at most
400 lines; "Last updated" has at most five bullets; every `status/` and
`prompts/` file the two name exists. `tests/test_status_budget.py` fails
otherwise. The cure is to move text into the phase file, never to raise the
number in passing.

## Merges

Two sessions on different branches now meet only in the phase table's top
rows, the "Last updated" bullets and "Next". On a conflict keep both sides'
lines, the newer above, and drop the oldest bullet beyond five.

## Records

`STATUS-archive.md`, `PROMPTS-archive.md` and the frozen files in this folder
(`divergences-to-2026-11-18.md`, `last-updated-to-2026-11-18.md`,
`next-earlier.md`) are records: nothing is appended to them. The phase files
dated before 2026-11-19 hold each phase's text as ARCH2 moved it, verbatim; a
session that continues such a phase adds below what is there.
