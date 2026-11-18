"""The measured figures a card quotes, read from the committed reports (REL1).

A card never carries a number typed into it: the German reader's error rates come
from ``reports/kurrent/k3-eval.json`` (K3), the page-level comparison with the
frontier models from ``reports/htr/page-llm.json`` (LT1), the language pass's
coverage from ``reports/kurrent/k4-reading.json`` (K4). Where a report is missing
(a wheel without the repository's ``reports/``) the card names the report and
quotes nothing. The Latin/French model's figure is B1's
(``reports/philiumm-repro.md``), kept as the constant it has been since D3 and
pinned to the report by a test.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[3] / "reports"
K3_EVAL = "kurrent/k3-eval.json"
K4_READING = "kurrent/k4-reading.json"
PAGE_LLM = "htr/page-llm.json"

# B1 (2026-08): the PHILIUMM model on its validation split, as reports/philiumm-repro.md
# states it; tests/test_release_cards.py checks the three figures against the report.
B1_VAL_LINES = 1878
B1_CER = "7.95 %"
B1_CER_INTERVAL = "7.49–8.46"
B1_WER = "27.0 %"

# The reader's name in the reports, and the names LT1's table prints for each row.
READER = "k3-trocr"
LT1_ROWS: tuple[tuple[str, str], ...] = (
    ("k3-trocr", "k3-trocr (this release's German reader; line by line)"),
    ("k3-kraken", "k3-kraken (the kraken candidate; not released)"),
    ("page:gemini-4-argon", "Gemini 4 Argon (whole pages)"),
    ("page:gemini-3.1-pro-preview", "Gemini 3.1 Pro (whole pages)"),
    ("page:claude-fable-5-1", "Claude Fable 5.1 (whole pages)"),
    ("trocr-kurrent-xvi-xvii", "the Bern Kurrent model as it came"),
    ("v1", "the Latin/French model (PHILIUMM) on the same German letters"),
)


def _load(rel: str, root: Path | None = None) -> dict | None:
    path = (root or REPORTS) / rel
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def pct(x: float | None, digits: int = 1) -> str:
    """``0.2861`` → ``"28.6 %"`` (``"—"`` for a missing figure)."""
    return "—" if x is None else f"{100 * x:.{digits}f} %"


def interval(lo: float | None, hi: float | None) -> str:
    return "" if lo is None or hi is None else f"{100 * lo:.1f}–{100 * hi:.1f}"


@dataclass(frozen=True, slots=True)
class Cer:
    """One error rate with its bootstrap interval, as a report states it."""

    cer: float | None = None
    lo: float | None = None
    hi: float | None = None

    @classmethod
    def of(cls, node: dict | None) -> Cer:
        node = node or {}
        return cls(node.get("cer"), node.get("cer_lo"), node.get("cer_hi"))

    def __str__(self) -> str:
        return pct(self.cer)

    @property
    def with_interval(self) -> str:
        iv = interval(self.lo, self.hi)
        return f"{pct(self.cer)} ({iv})" if iv else pct(self.cer)


@dataclass(frozen=True, slots=True)
class Reader:
    """K3's numbers for the German reader (``reports/kurrent/k3-eval.json``)."""

    pool: Cer = Cer()  # the letter pool, all letters
    pool_leibniz: Cer = Cer()  # Leibniz's own hand (L)
    pool_others: Cer = Cer()  # the correspondents' hands (K/k)
    pool_test: Cer = Cer()  # the test half
    pool_letters: int | None = None
    pool_lines: int | None = None
    v1_pool: Cer = Cer()  # the Latin/French model on the same letters
    v1_pool_leibniz: Cer = Cer()
    base_pool: Cer = Cer()  # the Bern model as it came
    validation: Cer = Cer()
    validation_lines: int | None = None
    dresden: Cer = Cer()
    dresden_lines: int | None = None
    train_lines: int | None = None
    best_epoch: int | None = None
    epochs: int | None = None
    generated: str | None = None


@dataclass(frozen=True, slots=True)
class PageTest:
    """LT1's letter-pool table (``reports/htr/page-llm.json``): one row per reader."""

    letters: int | None = None
    pages: int | None = None
    rows: tuple[tuple[str, Cer, Cer, Cer], ...] = ()  # label, all, Leibniz's, the others'
    philiumm_pages: int | None = None
    philiumm_best: tuple[str, Cer] | None = None  # the best page model on Latin/French
    date: str | None = None


@dataclass(frozen=True, slots=True)
class Coverage:
    """K4's language pass (``reports/kurrent/k4-reading.json``)."""

    threshold: str | None = None
    precision: float | None = None
    recall: float | None = None
    german_pages: int | None = None  # pages the pass calls German
    pages: int | None = None  # pages the pass labelled
    pages_read: int | None = None  # of the German pages, those the reader read
    lines_read: int | None = None
    rows_written: int | None = None
    run_id: int | None = None
    model: str | None = None
    batch_size: int | None = None  # the reading job's settings (K4)
    dtype: str | None = None
    use_cache: bool | None = None
    max_new_tokens: int | None = None
    ms_per_line: float | None = None


@dataclass(frozen=True, slots=True)
class Measured:
    reader: Reader | None = None
    page_test: PageTest | None = None
    coverage: Coverage | None = None
    missing: tuple[str, ...] = field(default_factory=tuple)


def load_reader(root: Path | None = None) -> Reader | None:
    d = _load(K3_EVAL, root)
    if not d:
        return None
    m = (d.get("models") or {}).get(READER)
    if not m:
        return None
    pool = m.get("pool") or {}
    hand = pool.get("hand") or {}
    base = d.get("baselines") or {}
    v1 = (base.get("v1") or {}).get("pool") or {}
    val = m.get("validation") or {}
    trained = m.get("trained") or {}
    dresden = m.get("dresden") or {}
    return Reader(
        pool=Cer.of(pool.get("all")),
        pool_leibniz=Cer.of(hand.get("L")),
        pool_others=Cer.of(hand.get("K/k")),
        pool_test=Cer.of(pool.get("test")),
        pool_letters=(pool.get("all") or {}).get("letters"),
        pool_lines=(pool.get("all") or {}).get("lines"),
        v1_pool=Cer.of(v1.get("all")),
        v1_pool_leibniz=Cer.of((v1.get("hand") or {}).get("L")),
        base_pool=Cer.of(((base.get("trocr-kurrent-xvi-xvii") or {}).get("pool") or {}).get("all")),
        validation=Cer.of(val.get("bootstrap") or (val.get("breakdown") or {}).get("overall")),
        validation_lines=((val.get("breakdown") or {}).get("overall") or {}).get("lines"),
        dresden=Cer.of(dresden),
        dresden_lines=dresden.get("n_lines"),
        train_lines=(d.get("trainset") or {}).get("train_lines"),
        best_epoch=trained.get("best_epoch"),
        epochs=trained.get("epoch"),
        generated=d.get("generated"),
    )


def load_page_test(root: Path | None = None) -> PageTest | None:
    d = _load(PAGE_LLM, root)
    if not d:
        return None
    pool = d.get("pool") or {}
    agg = pool.get("aggregate") or {}
    rows = []
    for key, label in LT1_ROWS:
        node = (agg.get(key) or {}).get("philiumm")
        if not node:
            continue
        hand = node.get("hand") or {}
        rows.append(
            (label, Cer.of(node.get("all")), Cer.of(hand.get("L")), Cer.of(hand.get("K/k")))
        )
    ph = d.get("philiumm") or {}
    best: tuple[str, Cer] | None = None
    for model, node in (ph.get("aggregate") or {}).items():
        c = Cer.of(((node or {}).get("philiumm") or {}).get("charged"))
        if c.cer is not None and (best is None or c.cer < (best[1].cer or 9)):
            best = (model, c)
    draw = pool.get("draw") or {}
    return PageTest(
        letters=draw.get("letters"),
        pages=draw.get("pages"),
        rows=tuple(rows),
        philiumm_pages=ph.get("pages"),
        philiumm_best=best,
        date=((d.get("generated") or {}).get("date") or "")[:10] or None,
    )


def load_coverage(root: Path | None = None) -> Coverage | None:
    d = _load(K4_READING, root)
    if not d:
        return None
    cov = d.get("coverage") or {}
    imp = d.get("import") or {}
    settings = (d.get("job") or {}).get("settings") or {}
    return Coverage(
        threshold=cov.get("threshold"),
        precision=cov.get("precision"),
        recall=cov.get("recall"),
        german_pages=cov.get("german_pages"),
        pages=cov.get("pages"),
        pages_read=imp.get("pages_written"),
        lines_read=imp.get("lines"),
        rows_written=imp.get("rows_written"),
        run_id=imp.get("run_id"),
        model=imp.get("model"),
        batch_size=settings.get("batch_size"),
        dtype=settings.get("dtype"),
        use_cache=settings.get("use_cache"),
        max_new_tokens=settings.get("max_new_tokens"),
        ms_per_line=(d.get("job") or {}).get("ms_per_line"),
    )


def load_measured(root: Path | None = None) -> Measured:
    """Everything the cards quote, with the reports that could not be read."""
    reader, page_test, coverage = load_reader(root), load_page_test(root), load_coverage(root)
    missing = tuple(
        f"reports/{rel}"
        for rel, got in ((K3_EVAL, reader), (PAGE_LLM, page_test), (K4_READING, coverage))
        if got is None
    )
    return Measured(reader, page_test, coverage, missing)


__all__ = [
    "B1_CER",
    "B1_CER_INTERVAL",
    "B1_VAL_LINES",
    "B1_WER",
    "LT1_ROWS",
    "REPORTS",
    "Cer",
    "Coverage",
    "Measured",
    "PageTest",
    "Reader",
    "interval",
    "load_coverage",
    "load_measured",
    "load_page_test",
    "load_reader",
    "pct",
]
