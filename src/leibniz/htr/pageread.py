"""The page-level reader: whole pages to a frontier vision model, one page a call (LT1, Task 1).

The protocol is the colleague's, adopted in the LT1 prompt: the whole page
image (one column at a time where the list says so), temperature 0, reasoning
off or at the lowest setting the API allows, one prompt for every model in the
spirit of Humphries' recipe (:data:`PAGE_PROMPT`), ``max_tokens`` about 4,000,
the image downscaled to a stated long side. A refusal, an empty answer or a
runaway (the output cap hit) is recorded as such and retried once; every
call's usage and estimated cost is logged; the run resumes page by page from
its JSONL.

What travels: only page images, and only the GWLB's public-domain scans (the
store's pages through the image cache or the public mirror; PHILIUMM's val
pages, the same scans, from the dataset's Hub repository). No reference text
ever goes to an API, and no API output is a training label.

The module is pure orchestration over :mod:`leibniz.htr.engines`; the tests
drive it with a scripted engine and fixture images (no network in pytest).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

from leibniz.htr import engines as ENG
from leibniz.images.fetch import cache_relpath

# --------------------------------------------------------------------------- #
# The protocol's constants
# --------------------------------------------------------------------------- #

# One prompt for every model: the manuscript page, line by line, nothing else.
PAGE_PROMPT = (
    "Transcribe every line of this manuscript page in reading order, one output line per "
    "manuscript line, character by character: exactly the characters written, with the "
    "original spelling, abbreviations, accents and punctuation. No commentary, no "
    "translation, no expansion of abbreviations, no headings or notes of your own — "
    "output the transcription and nothing else."
)
DEFAULT_LONG_SIDE = 2000
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TIMEOUT = 300.0  # seconds a page call may take before the deadline fires
DEFAULT_MIRROR = "https://images.leibnizlegible.com"
HF_DATASET = "DenisaBumba/htr_leibniz_dataset_v1"
HF_RESOLVE = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/"
DEFAULT_OUT_DIR = Path("data/bench/page-llm")
DEFAULT_IMAGE_CACHE = DEFAULT_OUT_DIR / "images"
DEFAULT_VAL_PAGES = Path("data/gt/philiumm-val-pages")
DEFAULT_PAGE_LISTS = Path("reports/htr")
COLUMNS: tuple[str, ...] = ("whole", "left", "right")
SETS: tuple[str, ...] = ("philiumm", "pool")
STATUSES: tuple[str, ...] = ("ok", "refused", "empty", "runaway", "error")
PAGE_LIST_FIELDS: tuple[str, ...] = (
    "page_id",
    "set",
    "source",
    "column",
    "letter_id",
    "hand",
    "half",
    "work_id",
    "seq",
    "ref",
)
# The lowest reasoning setting each API allows (the documentation read 2026-10-28):
# Claude 5 models think always, ``effort low`` is the floor; Gemini 3.x Pro and
# Gemini 4 Argon take ``thinking_level low`` and have no off; OpenAI's chain
# starts at ``none`` and steps down to what the model accepts.
REASONING_DEFAULTS: dict[str, str] = {"anthropic": "low", "gemini": "low", "openai": "none"}
API_ENGINES: tuple[str, ...] = ("anthropic", "gemini", "openai")
POOL_PAGES = 100
POOL_SEED = 20261028
PROMPT_TOKENS_ASSUMED = 90  # the prompt's own tokens, for the dry run's estimate


# --------------------------------------------------------------------------- #
# Page lists
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PageRow:
    """One row of a page list: what to read and where its image comes from.

    ``source`` is ``store`` (the page's image by the cache layout
    ``{work}/{seq:04d}.jpg`` under an images root or the public mirror),
    ``hf:<path>`` (a file of the PHILIUMM dataset's Hub repository), a local
    path or an ``http(s)`` URL. ``column`` is ``whole``, ``left`` or ``right``
    (a page with two columns, or an opening, is read a half at a time). ``ref``
    locates the reference: the PAGE XML stem for a PHILIUMM page, empty for a
    pool page (the letter's text is the reference there).
    """

    page_id: str
    set: str
    source: str = "store"
    column: str = "whole"
    letter_id: str = ""
    hand: str = ""
    half: str = ""
    work_id: str = ""
    seq: int | None = None
    ref: str = ""

    def __post_init__(self) -> None:
        if self.set not in SETS:
            raise ValueError(f"{self.page_id}: set must be one of {SETS}, not {self.set!r}")
        if self.column not in COLUMNS:
            raise ValueError(
                f"{self.page_id}: column must be one of {COLUMNS}, not {self.column!r}"
            )
        if self.source == "store" and (not self.work_id or self.seq is None):
            work, seq = split_page_id(self.page_id)
            self.work_id = self.work_id or work
            self.seq = seq if self.seq is None else self.seq

    @property
    def key(self) -> tuple[str, str]:
        return (self.page_id, self.column)


def split_page_id(page_id: str) -> tuple[str, int]:
    """``"{work}:{seq:04d}"`` → ``(work, seq)``; a non-store id gives ``(id, 0)``."""
    work, sep, seq = page_id.rpartition(":")
    if sep and seq.isdigit():
        return work, int(seq)
    return page_id, 0


def read_page_list(path: Path | str) -> list[PageRow]:
    rows: list[PageRow] = []
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            seq = (r.get("seq") or "").strip()
            rows.append(
                PageRow(
                    page_id=r["page_id"].strip(),
                    set=(r.get("set") or "pool").strip(),
                    source=(r.get("source") or "store").strip(),
                    column=(r.get("column") or "whole").strip() or "whole",
                    letter_id=(r.get("letter_id") or "").strip(),
                    hand=(r.get("hand") or "").strip(),
                    half=(r.get("half") or "").strip(),
                    work_id=(r.get("work_id") or "").strip(),
                    seq=int(seq) if seq else None,
                    ref=(r.get("ref") or "").strip(),
                )
            )
    return rows


def write_page_list(rows: Sequence[PageRow], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(PAGE_LIST_FIELDS))
        w.writeheader()
        for r in rows:
            d = asdict(r)
            d["seq"] = "" if r.seq is None else r.seq
            w.writerow(d)
    return path


def is_opening(stem: str) -> bool:
    """A PHILIUMM file name whose folio part names two sides (``LH_35_1_27_0009v-0008r``)."""
    tail = stem.rsplit("_", 1)[-1]
    return "-" in tail


def philiumm_rows(
    files: Iterable[str],
    heldout: Mapping[str, Sequence[str]] | None = None,
    *,
    split_openings: bool = True,
) -> list[PageRow]:
    """Page-list rows for the dataset's val pages: one per file, or a ``left`` and a
    ``right`` row where the file is an opening (two folios on one scan) and
    ``split_openings`` holds — one column at a time, as the protocol says.

    ``files`` are Hub paths (``val/LH_1_2_1_0004r.jpg``) or bare stems;
    ``heldout`` maps a stem to the store pages it resolved to (the P1 census),
    carried for the record — the image itself comes from the Hub.
    """
    heldout = heldout or {}
    out: list[PageRow] = []
    for f in sorted(set(files)):
        stem = Path(f).stem
        rel = f if "/" in f else f"val/{stem}.jpg"
        if not rel.endswith(".jpg"):
            rel = str(Path(rel).with_suffix(".jpg"))
        pages = list(heldout.get(stem, ()))
        work = pages[0].rpartition(":")[0] if len(pages) == 1 else ""
        seq = split_page_id(pages[0])[1] if len(pages) == 1 else None
        columns = ("left", "right") if split_openings and is_opening(stem) else ("whole",)
        for col in columns:
            out.append(
                PageRow(
                    page_id=f"philiumm:{stem}",
                    set="philiumm",
                    source=f"hf:{rel}",
                    column=col,
                    work_id=work,
                    seq=seq,
                    ref=stem,
                )
            )
    return out


def read_heldout(path: Path | str) -> dict[str, list[str]]:
    """``reports/philiumm/heldout_pages.csv`` → ``{file stem: [store page ids]}`` (val split)."""
    out: dict[str, list[str]] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("split") == "val":
                out.setdefault(r["file"], []).append(r["page_id"])
    return out


def hand_class(siglum: str) -> str:
    """``L``/``l`` → ``L`` (Leibniz's hand and his scribe's), ``K``/``k`` → ``K/k``."""
    return "L" if siglum in ("L", "l") else "K/k"


def draw_pool_pages(
    letters: Sequence[Mapping],
    *,
    n_pages: int = POOL_PAGES,
    seed: int = POOL_SEED,
) -> list[PageRow]:
    """About ``n_pages`` pool pages, drawn seeded from the frozen set, whole letters at a time.

    Half the pages from letters in Leibniz's hand (``L``), half from the
    correspondents' (``K/k``); within a hand the selection and test halves
    alternate; a letter joins with all its pages (the pool's metric scores a
    letter against every line on its pages, so a letter read in part would be
    charged for the pages not read) and is skipped when it would overshoot its
    hand's budget. ``letters`` are the rows of ``letterpool-testset.csv``.
    """
    rng = random.Random(seed)
    budget = {"L": n_pages // 2, "K/k": n_pages - n_pages // 2}
    cells: dict[tuple[str, str], list[Mapping]] = {}
    for r in letters:
        cells.setdefault((hand_class(r["siglum"]), r["half"]), []).append(r)
    for members in cells.values():
        members.sort(key=lambda r: r["letter_id"])
        rng.shuffle(members)
    used: dict[str, int] = {"L": 0, "K/k": 0}
    chosen: list[Mapping] = []
    order = [("L", "selection"), ("K/k", "selection"), ("L", "test"), ("K/k", "test")]
    progress = True
    while progress:
        progress = False
        for cell in order:
            hand = cell[0]
            members = cells.get(cell, [])
            pick = next(
                (
                    m
                    for m in members
                    if used[hand] + len(str(m["page_ids"]).split()) <= budget[hand]
                ),
                None,
            )
            if pick is None:
                continue
            members.remove(pick)
            used[hand] += len(str(pick["page_ids"]).split())
            chosen.append(pick)
            progress = True
    chosen.sort(key=lambda r: (int(r["year"]), str(r["letter_id"])))
    out: list[PageRow] = []
    for r in chosen:
        for pid in str(r["page_ids"]).split():
            work, seq = split_page_id(pid)
            out.append(
                PageRow(
                    page_id=pid,
                    set="pool",
                    source="store",
                    letter_id=str(r["letter_id"]),
                    hand=hand_class(r["siglum"]),
                    half=str(r["half"]),
                    work_id=work,
                    seq=seq,
                )
            )
    return out


def read_testset_rows(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- #
# Images: where they come from, how they are prepared
# --------------------------------------------------------------------------- #


def image_url(row: PageRow, *, mirror: str = DEFAULT_MIRROR) -> str | None:
    """The page's public URL: the Hub for a dataset file, the mirror for a store page."""
    if row.source.startswith("hf:"):
        return HF_RESOLVE + row.source[3:]
    if row.source.startswith(("http://", "https://")):
        return row.source
    if row.source == "store" and row.seq is not None:
        return f"{mirror.rstrip('/')}/{cache_relpath(row.work_id, row.seq)}"
    return None


def cache_name(row: PageRow) -> str:
    """Where a fetched image lands under the cache: the store layout, or the Hub path."""
    if row.source.startswith("hf:"):
        return row.source[3:]
    if row.source == "store" and row.seq is not None:
        return cache_relpath(row.work_id, row.seq)
    return hashlib.sha256(row.source.encode("utf-8")).hexdigest()[:16] + ".jpg"


@dataclass(slots=True)
class ImageStore:
    """Resolves a row's image bytes: a local root first, then the cache, then a fetch.

    ``images_root`` is the operator's page cache (``/mnt/d/leibniz-images`` on the
    desktop) and ``val_pages`` the directory ``page-fetch`` fills with the Hub's
    val files; ``cache_dir`` keeps what ``fetch`` (a polite GET returning bytes)
    downloads, so a second reader never fetches the page again.
    """

    images_root: Path | None = None
    val_pages: Path | None = None
    cache_dir: Path | None = None
    fetch: Callable[[str], bytes] | None = None
    mirror: str = DEFAULT_MIRROR
    fetched: int = 0

    def local_path(self, row: PageRow) -> Path | None:
        candidates: list[Path] = []
        if row.source.startswith("hf:") and self.val_pages is not None:
            candidates.append(Path(self.val_pages) / Path(row.source[3:]).name)
        if row.source == "store" and self.images_root is not None and row.seq is not None:
            candidates.append(Path(self.images_root) / cache_relpath(row.work_id, row.seq))
        if not row.source.startswith(("hf:", "http://", "https://")) and row.source != "store":
            candidates.append(Path(row.source))
        if self.cache_dir is not None:
            candidates.append(Path(self.cache_dir) / cache_name(row))
        return next((p for p in candidates if p.exists()), None)

    def get(self, row: PageRow) -> bytes:
        path = self.local_path(row)
        if path is not None:
            return path.read_bytes()
        url = image_url(row, mirror=self.mirror)
        if url is None or self.fetch is None:
            raise FileNotFoundError(f"{row.page_id}: no image on disk and nothing to fetch from")
        data = self.fetch(url)
        self.fetched += 1
        if self.cache_dir is not None:
            target = Path(self.cache_dir) / cache_name(row)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(target)
        return data


@dataclass(slots=True)
class Prepared:
    """The image as sent: JPEG bytes at the protocol's size, with the sizes recorded."""

    data: bytes
    width: int
    height: int
    orig_width: int
    orig_height: int
    column: str = "whole"

    @property
    def n_bytes(self) -> int:
        return len(self.data)


def prepare_image(
    data: bytes, *, long_side: int = DEFAULT_LONG_SIDE, column: str = "whole", quality: int = 92
) -> Prepared:
    """The half the column names (or the whole page), downscaled so the long side is at most
    ``long_side`` px (never upscaled), re-encoded as JPEG."""
    from PIL import Image

    with Image.open(io.BytesIO(data)) as im:
        im.load()
        ow, oh = im.size
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        if column == "left":
            im = im.crop((0, 0, ow // 2, oh))
        elif column == "right":
            im = im.crop((ow // 2, 0, ow, oh))
        elif column != "whole":
            raise ValueError(f"unknown column {column!r}")
        w, h = im.size
        if max(w, h) > long_side:
            s = long_side / max(w, h)
            im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True)
        return Prepared(buf.getvalue(), im.size[0], im.size[1], ow, oh, column)


def estimate_input_tokens(engine: str, width: int, height: int) -> int:
    """The image's tokens by the API's documented rule, plus the prompt's (an estimate)."""
    if engine == "anthropic":
        img = ENG.anthropic_image_tokens(width, height)
    elif engine == "gemini":
        img = ENG.gemini_image_tokens(width, height)
    else:
        img = ENG.openai_image_tokens(width, height)
    return img + PROMPT_TOKENS_ASSUMED


def estimate_cost(engine: str, model: str, input_tokens: int, output_tokens: int) -> float | None:
    if engine == "anthropic":
        return ENG.estimate_anthropic_cost(model, input_tokens, output_tokens)
    if engine == "gemini":
        return ENG.estimate_gemini_cost(model, input_tokens, output_tokens)
    if engine == "openai":
        return ENG.estimate_openai_cost(model, input_tokens, output_tokens)
    return 0.0


# --------------------------------------------------------------------------- #
# Engines for the page protocol
# --------------------------------------------------------------------------- #


def build_engine(
    engine: str,
    model: str | None,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
    reasoning: str | None = None,
    temperature: float | None = 0.0,
    api_key: str | None = None,
    client=None,
):
    """An API engine set for the page protocol: the page prompt, the token cap, the
    lowest reasoning setting (or ``reasoning``), temperature 0 where the API takes it.

    ``echo`` builds the offline stub the tests use (``model`` names its version).
    """
    level = reasoning or REASONING_DEFAULTS.get(engine)
    if engine == "anthropic":
        return ENG.AnthropicEngine(
            model=model or ENG.DEFAULT_ANTHROPIC_MODEL,
            prompt=PAGE_PROMPT,
            max_tokens=max_tokens,
            effort=level,
            temperature=None,  # the current Claude models reject the parameter
            timeout=timeout,
            api_key=api_key,
            client=client,
        )
    if engine == "gemini":
        return ENG.GeminiEngine(
            model=model or ENG.DEFAULT_GEMINI_MODEL,
            prompt=PAGE_PROMPT,
            max_tokens=max_tokens,
            thinking_level=level,
            temperature=temperature,
            timeout=timeout,
            api_key=api_key,
            client=client,
        )
    if engine == "openai":
        return ENG.OpenAIEngine(
            model=model or ENG.DEFAULT_OPENAI_MODEL,
            prompt=PAGE_PROMPT,
            max_tokens=max_tokens,
            reasoning_effort=level,
            temperature=temperature,
            timeout=timeout,
            api_key=api_key,
            client=client,
        )
    if engine == "echo":
        from leibniz.htr.bench import EchoEngine

        eng = EchoEngine(default="")
        eng.version = model or "0"
        return eng
    raise ValueError(f"unknown engine {engine!r} (anthropic | gemini | openai | echo)")


def call_engine(engine, data: bytes, prompt: str = PAGE_PROMPT) -> ENG.ApiReply:
    """One page through an engine: its ``reply`` when it has one, else ``transcribe``."""
    reply = getattr(engine, "reply", None)
    if callable(reply):
        return reply(data, prompt=prompt)
    text = engine.transcribe([data])[0]
    return ENG.ApiReply(text=text, stop="end")


def engine_settings(engine) -> dict:
    fn = getattr(engine, "settings", None)
    return dict(fn()) if callable(fn) else {}


def status_of(reply: ENG.ApiReply) -> str:
    """``refused`` | ``runaway`` | ``empty`` | ``ok`` from one reply, in that precedence."""
    if reply.stop == "refusal":
        return "refused"
    if reply.stop == "length":
        return "runaway"
    if not reply.text.strip():
        return "empty"
    return "ok"


def split_lines(text: str) -> list[str]:
    """The answer's lines: split on newlines, stripped, the empty ones dropped."""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# --------------------------------------------------------------------------- #
# Readings on disk (resumable JSONL, one file per model)
# --------------------------------------------------------------------------- #


def slug(model: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in model)


def readings_path(out_dir: Path | str, model: str) -> Path:
    return Path(out_dir) / f"{slug(model)}.jsonl"


def load_readings(path: Path | str) -> dict[tuple[str, str], dict]:
    """The rows of a readings file keyed by ``(page_id, column)``; a later row for the
    same key replaces an earlier one (a page read again)."""
    path = Path(path)
    out: dict[tuple[str, str], dict] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            row = json.loads(raw)
            out[(row["page_id"], row.get("column", "whole"))] = row
    return out


def page_texts(readings: Mapping[tuple[str, str], Mapping]) -> dict[str, str]:
    """``{page_id: text}`` of a model's readings, the columns of a page joined in order
    (left, then right), a page that did not read (status not ``ok``) as the empty string."""
    by_page: dict[str, dict[str, str]] = {}
    for (pid, col), row in readings.items():
        by_page.setdefault(pid, {})[col] = row.get("text", "") if row.get("status") == "ok" else ""
    out: dict[str, str] = {}
    for pid, cols in by_page.items():
        parts = [cols[c] for c in COLUMNS if c in cols]
        out[pid] = "\n".join(p for p in parts if p)
    return out


def failed_pages(readings: Mapping[tuple[str, str], Mapping]) -> set[str]:
    """The page ids with at least one column whose final status is not ``ok``."""
    return {pid for (pid, _col), row in readings.items() if row.get("status") != "ok"}


def _append(path: Path, row: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- #
# The read
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ReadStats:
    """What one run did: pages read now, skipped as done, the statuses, the cost."""

    model: str
    engine: str
    read: int = 0
    skipped: int = 0
    failed_images: int = 0
    statuses: dict[str, int] = field(default_factory=dict)
    retried: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float = 0.0
    stopped_at_cap: bool = False
    seconds: float = 0.0


def read_pages(
    rows: Sequence[PageRow],
    engine,
    out_path: Path | str,
    *,
    images: ImageStore,
    engine_name: str,
    long_side: int = DEFAULT_LONG_SIDE,
    prompt: str = PAGE_PROMPT,
    max_cost: float | None = None,
    redo: str = "none",
    log: Callable[[str], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    min_interval: float = 0.5,
    now: Callable[[], str] | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> ReadStats:
    """Read every row not yet in ``out_path`` with ``engine``; one call a page (a column),
    the failed statuses retried once, every call's usage and cost logged; stops when the
    estimated cost reaches ``max_cost``. ``redo``: ``none`` (resume), ``failed`` (read
    the pages whose last status is not ok again), ``all``.
    """
    out_path = Path(out_path)
    model = str(getattr(engine, "version", getattr(engine, "name", "?")))
    have = load_readings(out_path)
    stats = ReadStats(model=model, engine=engine_name)
    settings = engine_settings(engine)
    settings["long_side"] = long_side
    settings["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    now = now or (lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    first = True
    for row in rows:
        done = have.get(row.key)
        if done is not None and (
            redo == "none" or (redo == "failed" and done.get("status") == "ok")
        ):
            stats.skipped += 1
            continue
        if max_cost is not None and stats.cost >= max_cost:
            stats.stopped_at_cap = True
            if log:
                log(f"{model}: the cost cap of {max_cost:.2f} USD is reached; stopping")
            break
        try:
            raw = images.get(row)
            prepared = prepare_image(raw, long_side=long_side, column=row.column)
        except Exception as exc:  # noqa: BLE001 — a page without an image is counted, not fatal
            stats.failed_images += 1
            if log:
                log(f"{model}: {row.page_id} [{row.column}] no image ({exc}); skipped")
            continue
        if not first and min_interval:
            sleep(min_interval)
        first = False
        t0 = monotonic()
        attempts: list[dict] = []
        reply: ENG.ApiReply | None = None
        status = "error"
        error = ""
        n_in = n_out = n_reason = 0
        for k in range(2):  # the protocol's one retry
            code: int | None = None
            try:
                reply = call_engine(engine, prepared.data, prompt)
                status = status_of(reply)
                error = ""
                n_in += reply.input_tokens
                n_out += reply.output_tokens
                n_reason += reply.reasoning_tokens or 0
            except httpx.HTTPStatusError as exc:
                reply, status = None, "error"
                code = exc.response.status_code
                error = f"HTTP {code}: {exc}"[:300]
            except Exception as exc:  # noqa: BLE001 — an API error is a recorded status
                reply, status = None, "error"
                error = f"{type(exc).__name__}: {exc}"[:300]
            attempts.append({"status": status, "error": error})
            if status == "ok":
                break
            if code is not None and 400 <= code < 500 and code != 429:
                break  # the request itself is refused; a second try would not change it
            if k == 0:
                stats.retried += 1
        ms = 1000.0 * (monotonic() - t0)
        cost = estimate_cost(engine_name, model, n_in, n_out) or 0.0
        text = reply.text if reply else ""
        record = {
            "page_id": row.page_id,
            "set": row.set,
            "column": row.column,
            "letter_id": row.letter_id,
            "hand": row.hand,
            "half": row.half,
            "engine": engine_name,
            "model": model,
            "settings": settings,
            "image": {
                "width": prepared.width,
                "height": prepared.height,
                "orig_width": prepared.orig_width,
                "orig_height": prepared.orig_height,
                "bytes": prepared.n_bytes,
            },
            "text": text,
            "lines": split_lines(text) if status == "ok" else [],
            "status": status,
            "first_status": attempts[0]["status"],
            "attempts": len(attempts),
            "stop": reply.stop if reply else "",
            "error": error,
            "usage": {"input": n_in, "output": n_out, "reasoning": n_reason},
            "cost": round(cost, 6),
            "ms": round(ms, 1),
            "when": now(),
        }
        _append(out_path, record)
        have[row.key] = record
        stats.read += 1
        stats.statuses[status] = stats.statuses.get(status, 0) + 1
        stats.input_tokens += n_in
        stats.output_tokens += n_out
        stats.reasoning_tokens += n_reason
        stats.cost += cost
        stats.seconds += ms / 1000.0
        if log:
            log(
                f"{model}: {row.page_id} [{row.column}] {status} · {len(record['lines'])} lines · "
                f"{n_in}+{n_out} tokens · {cost:.4f} USD · {ms / 1000:.1f} s"
                + (f" · {error}" if error else "")
            )
    if log:
        log(
            f"{model}: {stats.read} pages read now, {stats.skipped} already on disk, "
            f"{stats.failed_images} without an image; statuses {stats.statuses}; "
            f"{stats.input_tokens:,} in + {stats.output_tokens:,} out tokens, "
            f"{stats.cost:.2f} USD"
        )
    return stats


# --------------------------------------------------------------------------- #
# The dry run: what a read would cost
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Plan:
    engine: str
    model: str
    long_side: int
    pages: dict[str, int]
    calls: int
    already_read: int
    input_tokens: int
    output_tokens_assumed: int
    cost: float | None
    rate: tuple[float, float] | None
    image_sizes_known: int
    reasoning: str

    def as_dict(self) -> dict:
        return asdict(self)


def plan_read(
    rows: Sequence[PageRow],
    engine_name: str,
    model: str,
    *,
    out_path: Path | str | None = None,
    images: ImageStore | None = None,
    long_side: int = DEFAULT_LONG_SIDE,
    output_tokens_per_page: int = 1500,
    reasoning: str | None = None,
) -> Plan:
    """The calls a read would make and their cost at the pricing tables.

    Input tokens follow each API's documented image rule on the prepared size
    (the real size where the image is on disk, else a page of ``long_side`` by
    two thirds of it); the output tokens are an assumption the caller states
    (``output_tokens_per_page``: the transcription plus the thinking the API
    bills as output). The run itself records the APIs' own usage.
    """
    have = load_readings(out_path) if out_path else {}
    todo = [r for r in rows if r.key not in have]
    n_in = 0
    known = 0
    for r in todo:
        w, h = round(long_side * 2 / 3), long_side
        if images is not None:
            path = images.local_path(r)
            if path is not None:
                try:
                    from PIL import Image

                    with Image.open(path) as im:
                        ow, oh = im.size
                    if r.column != "whole":
                        ow //= 2
                    s = min(1.0, long_side / max(ow, oh))
                    w, h = max(1, round(ow * s)), max(1, round(oh * s))
                    known += 1
                except Exception:  # noqa: BLE001 — an unreadable file keeps the assumption
                    pass
        n_in += estimate_input_tokens(engine_name, w, h)
    n_out = output_tokens_per_page * len(todo)
    if engine_name == "anthropic":
        rate = ENG._prefix_rate(ENG.ANTHROPIC_PRICES, model)
    elif engine_name == "gemini":
        rate = ENG._prefix_rate(ENG.GEMINI_PRICES, model)
    elif engine_name == "openai":
        rate = ENG._prefix_rate(ENG.OPENAI_PRICES, model)
    else:
        rate = (0.0, 0.0)
    pages: dict[str, int] = {}
    for r in todo:
        pages[r.set] = pages.get(r.set, 0) + 1
    return Plan(
        engine=engine_name,
        model=model,
        long_side=long_side,
        pages=pages,
        calls=len(todo),
        already_read=len(rows) - len(todo),
        input_tokens=n_in,
        output_tokens_assumed=n_out,
        cost=estimate_cost(engine_name, model, n_in, n_out) if rate else None,
        rate=rate,
        image_sizes_known=known,
        reasoning=reasoning or REASONING_DEFAULTS.get(engine_name, "—"),
    )


# --------------------------------------------------------------------------- #
# The Hub's val pages (PHILIUMM, CC BY 4.0): fetch, resumable, polite
# --------------------------------------------------------------------------- #


def val_files(listing_files: Iterable[str], *, suffix: str = ".jpg") -> list[str]:
    """The ``val/`` files of a Hub listing with ``suffix`` (the P1 listing's ``files``)."""
    return sorted(f for f in listing_files if f.startswith("val/") and f.endswith(suffix))


def fetch_val_pages(
    files: Iterable[str],
    dest: Path | str,
    fetch: Callable[[str], bytes],
    *,
    log: Callable[[str], None] | None = None,
) -> tuple[int, int]:
    """Download the val pages' ``.jpg`` and ``.xml`` into ``dest`` (what is there is kept).
    Returns ``(fetched, present)``."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    wanted: list[str] = []
    for f in files:
        stem = Path(f).stem
        wanted.extend((f"val/{stem}.jpg", f"val/{stem}.xml"))
    fetched = 0
    for rel in sorted(set(wanted)):
        target = dest / Path(rel).name
        if target.exists() and target.stat().st_size > 0:
            continue
        data = fetch(HF_RESOLVE + rel)
        tmp = target.with_suffix(target.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(target)
        fetched += 1
        if log:
            log(f"fetched {rel} ({len(data):,} bytes)")
    return fetched, len(set(wanted))


__all__ = [
    "API_ENGINES",
    "COLUMNS",
    "DEFAULT_IMAGE_CACHE",
    "DEFAULT_LONG_SIDE",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MIRROR",
    "DEFAULT_OUT_DIR",
    "DEFAULT_PAGE_LISTS",
    "DEFAULT_TIMEOUT",
    "DEFAULT_VAL_PAGES",
    "HF_RESOLVE",
    "PAGE_LIST_FIELDS",
    "PAGE_PROMPT",
    "POOL_PAGES",
    "POOL_SEED",
    "REASONING_DEFAULTS",
    "SETS",
    "STATUSES",
    "ImageStore",
    "PageRow",
    "Plan",
    "Prepared",
    "ReadStats",
    "build_engine",
    "cache_name",
    "call_engine",
    "draw_pool_pages",
    "estimate_cost",
    "estimate_input_tokens",
    "failed_pages",
    "fetch_val_pages",
    "hand_class",
    "image_url",
    "is_opening",
    "load_readings",
    "page_texts",
    "philiumm_rows",
    "plan_read",
    "prepare_image",
    "read_heldout",
    "read_page_list",
    "read_pages",
    "read_testset_rows",
    "readings_path",
    "slug",
    "split_lines",
    "split_page_id",
    "status_of",
    "val_files",
    "write_page_list",
]
