"""The character n-gram of R1, built from text the project may use (Task 2).

``leibniz bench lm-build`` writes two KenLM models — one from Latin and French
text, one from German — for the decoders of :mod:`leibniz.htr.decoding`.

**What text.** Two sources, both of the open deposit and nothing else:

* ``edition`` — the reading text in the C2 edition cache
  (``data/gt/edition_cache.jsonl``) of every record whose printed pieces all
  stand in a §70-free volume and were read through a channel the licence
  registry places in the open deposit (:func:`leibniz.legal.deposit_for`). A
  record whose cache line names no piece, a channel with non-commercial terms
  (Potsdam, the GWLB repository) or a volume still protected is left out and
  counted.
* ``gt`` — the minted lines of ``gt_lines`` in the open bucket, under the same
  two tests read off each row's ``source``.

The letter pool, the Dresden lines and the PHILIUMM dataset are evaluation
material and are never a source here; an operator may add plain text of their
own (``--extra name=file``), which the report then names.

**What is held out.** Every document of the evaluation sets, by piece: a
record is dropped whole, from both sources, when it is one of K3's validation
pieces, when a judged audit line belongs to it, or when it stands on a held-out
page — the pages of ``reports/philiumm/heldout_pages.csv`` (PHILIUMM's training
and held-out pages as the store has them) and the letter pool's pages. "Stands
on" is decided twice and joined: by the minted rows on the page, and by the
factory's own placement of every piece with an edition text (the K1 census's
walk). Dresden has no piece in the edition.

**How it is normalised.** To the reader's conventions, not the aligner's lossy
ones: a Unicode form (NFC, or NFD for a codec of decomposed marks), control
and format characters dropped, whitespace collapsed; case, accents and
punctuation kept, because a diplomatic reader writes them and the model must
score them. Nothing is done to hyphens: a minted line keeps the line-end
hyphen the scribe wrote (C2c's rule) and the edition's running text had the
print's hyphenation undone at ingest. ``--fold align`` builds the other
variant, on the aligner's fold (case, accents, u/v, i/j, punctuation gone);
the decoder then queries it through the same fold, label by label. One line is
one sentence: a minted line as it is, the edition's running text cut at word
boundaries into lines of a manuscript line's length (``--wrap``), so that the
model's beginning and end of line are a manuscript's and not a paragraph's.

**How it is estimated.** KenLM's ``lmplz`` (modified Kneser-Ney, interpolated)
on the lines as characters separated by spaces, the space written ``<space>``
(PyLaia's recipe); the ARPA file is kept beside ``build_binary``'s binary, and
a sidecar JSON beside both says which text the model saw. KenLM is LGPL: the
two programs are run, never imported or copied.

The store is opened read-only by the CLI; everything here is deterministic.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from leibniz import legal
from leibniz.align.audit_reach import parse_source
from leibniz.align.pairs import channels_from_source, record_id_from_source
from leibniz.htr import decoding

DEFAULT_CACHE = Path("data/gt/edition_cache.jsonl")
DEFAULT_OUT = Path("data/lm/r1")
DEFAULT_REPORTS_DIR = Path("reports/decoding")
DEFAULT_HELDOUT = Path("reports/philiumm/heldout_pages.csv")
DEFAULT_POOL = Path("reports/kurrent/letterpool-testset.csv")
DEFAULT_VAL_PIECES = Path("reports/kurrent/k3-val-pieces.csv")
DEFAULT_AUDITS: tuple[Path, ...] = (
    Path("data/kurrent/k2-audit-lines.csv"),
    Path("reports/gt-audit/gt-audit-verdicts-philiumm.csv"),
)
ORDER = 6
WRAP = 48  # characters: a manuscript line's length (K3's training lines: median 46)
MIN_LINE_CHARS = 2
SOURCES = ("edition", "gt")
# The two models, by the census's groups (enrich/pagelang.piece_group): German,
# or mixed with German leading, against Latin and French. A piece the stopword
# lists cannot place ("other": too short, or mixed without German) goes to
# neither model and is counted.
GROUPS = ("la_fr", "de")
GROUP_FILES = {"la_fr": "la-fr", "de": "de"}
GROUP_NAMES = {"la_fr": "Latin and French", "de": "German"}
FORMS = ("NFC", "NFD")
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
_WS = re.compile(r"\s+")


# --------------------------------------------------------------------------- #
# Normalisation and the corpus line
# --------------------------------------------------------------------------- #


def normalize_line(text: str, *, form: str = "NFC", fold: str = "none") -> str:
    """One line on the model's alphabet (the module docstring's rules)."""
    if fold == "align":
        from leibniz.align.normalize import normalize

        return unicodedata.normalize(form, normalize(text))
    if fold != "none":
        raise ValueError(f"unknown fold {fold!r} (known: {', '.join(decoding.FOLDS)})")
    text = unicodedata.normalize(form, text)
    kept = [
        " " if ch.isspace() else ch
        for ch in text
        if ch.isspace() or unicodedata.category(ch)[0] != "C"
    ]
    return _WS.sub(" ", "".join(kept)).strip()


def wrap_text(text: str, width: int) -> list[str]:
    """Running text as lines of at most ``width`` characters, cut at spaces (a longer
    word stays whole); ``width <= 0`` returns the text's own lines."""
    out: list[str] = []
    for para in text.splitlines():
        if width <= 0:
            out.append(para)
            continue
        line = ""
        for word in para.split():
            if line and len(line) + 1 + len(word) > width:
                out.append(line)
                line = word
            else:
                line = f"{line} {word}" if line else word
        if line:
            out.append(line)
    return out


def corpus_line(line: str) -> str:
    """A normalised line as KenLM reads it: its characters separated by spaces, the
    space as ``<space>``."""
    return " ".join(decoding.lm_token(ch) for ch in line)


# --------------------------------------------------------------------------- #
# The legal gate, the same for both sources
# --------------------------------------------------------------------------- #


def volume_key(label: str | None) -> tuple[int, str] | None:
    """``"IV,3"`` → ``(4, "3")``, the key of ``expired_volume_index``."""
    if not label or "," not in label:
        return None
    series, volume = label.split(",", 1)
    n = _ROMAN.get(series.strip())
    return (n, volume.strip()) if n else None


def gate(
    volumes: Iterable[tuple[int, str] | None],
    channels: Sequence[str],
    expired: Mapping[tuple[int, str], object],
) -> str | None:
    """Why a text is left out, or ``None`` when it may be used: every volume
    §70-free on the day, and the open deposit by the registry's channels."""
    vols = list(volumes)
    if not vols or any(v is None for v in vols):
        return "no_volume"
    if any(v not in expired for v in vols):
        return "not_70_expired"
    deposit = legal.deposit_for(channels, "open")
    if deposit == "nc":
        return "nc_channel"
    if deposit != "open":
        return "channel_not_released"
    return None


# --------------------------------------------------------------------------- #
# The two sources
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Piece:
    """One record's usable text: its lines by source, before normalisation."""

    record_id: str
    edition: list[str] = field(default_factory=list)
    gt: list[str] = field(default_factory=list)
    edition_text: str = ""
    group: str = "other"
    lang: str = "unknown"


def iter_cache(path: Path | str) -> Iterator[tuple[str, str, list[dict]]]:
    """``(record_id, text, refs)`` from the edition cache (``.jsonl``)."""
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                obj = json.loads(raw)
                yield str(obj["record_id"]), str(obj.get("text") or ""), list(obj.get("refs") or [])


def _ref_channels(refs: Sequence[Mapping]) -> tuple[str, ...] | None:
    """The channels a cache line's pieces were read through; ``None`` when a piece
    names none (the text cannot be placed in a deposit)."""
    out: list[str] = []
    for ref in refs:
        ch = ref.get("channel")
        if not ch:
            return None
        out.extend(str(ch).split("+"))
    return tuple(dict.fromkeys(out))


def read_edition(
    path: Path | str, expired: Mapping[tuple[int, str], object], *, wrap: int = WRAP
) -> tuple[dict[str, Piece], Counter]:
    """The edition cache's usable records, and the count of the rest by reason."""
    pieces: dict[str, Piece] = {}
    left: Counter = Counter()
    for rid, text, refs in iter_cache(path):
        if not text.strip():
            left["empty"] += 1
            continue
        if not refs:
            left["no_refs"] += 1
            continue
        channels = _ref_channels(refs)
        if channels is None:
            left["no_channel"] += 1
            continue
        why = gate(
            [
                (int(r["series"]), str(r["volume"])) if r.get("series") is not None else None
                for r in refs
            ],
            channels,
            expired,
        )
        if why:
            left[why] += 1
            continue
        pieces[rid] = Piece(rid, edition=wrap_text(text, wrap), edition_text=text)
    return pieces, left


def page_of(ref: str | None) -> str | None:
    """The page of a ``line_image_ref``: ``work:seq:line`` (the factory's rows) or an
    older ``work:seq#xywh=…``."""
    base = str(ref or "").split("#", 1)[0]
    if base.count(":") == 1:
        return base
    return base.rsplit(":", 1)[0] if base.count(":") == 2 else None


def read_gt(
    conn, expired: Mapping[tuple[int, str], object]
) -> tuple[dict[str, list[str]], Counter, dict[str, set[str]]]:
    """The open-bucket minted lines by record, the count of the rows left out by
    reason, and — over **every** row, whatever its bucket — the records with a row
    on each page (for the hold-out)."""
    by_record: dict[str, list[str]] = defaultdict(list)
    left: Counter = Counter()
    on_page: dict[str, set[str]] = defaultdict(set)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(gt_lines)")}
    rec_col = "record_id" if "record_id" in cols else "NULL"
    sql = (
        f"SELECT line_image_ref, text, source, license_bucket, {rec_col} FROM gt_lines ORDER BY id"
    )
    for ref, text, source, bucket, rec in conn.execute(sql):
        rid = str(rec) if rec else record_id_from_source(source)
        page = page_of(ref)
        if rid and page:
            on_page[page].add(rid)
        if bucket != "open":
            left["nc_bucket"] += 1
            continue
        if not rid:
            left["no_record"] += 1
            continue
        volume, _rec = parse_source(source or "")
        why = gate([volume_key(volume)], channels_from_source(source), expired)
        if why:
            left[why] += 1
            continue
        by_record[rid].append(text or "")
    return dict(by_record), left, dict(on_page)


def read_extra(path: Path | str) -> list[str]:
    """Plain text of the operator's own, one line a sentence (``.txt``), or the
    ``text`` column of a parquet file."""
    p = Path(path)
    if p.suffix == ".parquet":
        import pyarrow.parquet as pq

        return [t or "" for t in pq.read_table(str(p), columns=["text"]).column("text").to_pylist()]
    return p.read_text(encoding="utf-8").splitlines()


# --------------------------------------------------------------------------- #
# The hold-out
# --------------------------------------------------------------------------- #


def pages_by_split(path: Path | str) -> dict[str, set[str]]:
    """Page ids of a CSV by its ``split`` column (``"pages"`` where it has none); a
    ``page_id`` column or a space-separated ``page_ids`` one."""
    p = Path(path)
    out: dict[str, set[str]] = defaultdict(set)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("split") or "pages").strip() or "pages"
            if row.get("page_id"):
                out[key].add(row["page_id"].strip())
            if row.get("page_ids"):
                out[key].update(row["page_ids"].split())
    return dict(out)


def column_values(path: Path | str, column: str) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    with p.open(encoding="utf-8", newline="") as fh:
        return {(row.get(column) or "").strip() for row in csv.DictReader(fh) if row.get(column)}


def placed_pages(conn, record_ids: Iterable[str], *, today: date) -> dict[str, set[str]]:
    """The pages the factory places each of the records on (the K1 census's walk:
    the resolver, one folio index per work); a record it cannot place has none."""
    from leibniz import db
    from leibniz.align.resolve import index_pages, select_folios
    from leibniz.align.volumes import enumerate_pieces

    wanted = set(record_ids)
    pieces, _stats = enumerate_pieces(conn, today=today)
    indexes: dict[str, dict] = {}
    out: dict[str, set[str]] = defaultdict(set)
    for piece in pieces:
        if piece.record_id not in wanted or not piece.localizable:
            continue
        index = indexes.get(piece.work_id)
        if index is None:
            index = indexes[piece.work_id] = index_pages(db.get_pages(conn, piece.work_id))
        pages = select_folios(
            index,
            piece.work_id,
            *piece.folio_range,
            side_lo=piece.folio_sides[0],
            side_hi=piece.folio_sides[1],
        ).pages
        out[piece.record_id].update(p.id for p in pages)
    return dict(out)


@dataclass(slots=True)
class Holdout:
    """The pieces kept out of every model, each with the reasons."""

    reasons: dict[str, set[str]] = field(default_factory=dict)  # record → reasons
    sets: dict[str, int] = field(default_factory=dict)  # reason → pages or ids given

    def add(self, record_id: str, reason: str) -> None:
        self.reasons.setdefault(record_id, set()).add(reason)

    def __contains__(self, record_id: str) -> bool:
        return record_id in self.reasons

    def by_reason(self) -> dict[str, int]:
        c: Counter = Counter()
        for rs in self.reasons.values():
            c.update(rs)
        return dict(sorted(c.items()))


def build_holdout(
    conn,
    *,
    page_sets: Mapping[str, set[str]],
    record_sets: Mapping[str, set[str]],
    audit_refs: set[str],
    on_page: Mapping[str, set[str]],
    placed: Mapping[str, set[str]],
) -> Holdout:
    """Join the evaluation sets into the records to hold out.

    ``page_sets`` and ``record_sets`` map a reason to its pages or record ids;
    ``on_page`` is the minted rows' record per page, ``placed`` the factory's
    placement of each record with an edition text.
    """
    hold = Holdout()
    for reason, recs in record_sets.items():
        hold.sets[reason] = len(recs)
        for rid in recs:
            hold.add(rid, reason)
    page_reason: dict[str, set[str]] = defaultdict(set)
    for reason, pages in page_sets.items():
        hold.sets[reason] = len(pages)
        for pid in pages:
            page_reason[pid].add(reason)
    for pid, reasons in page_reason.items():
        for rid in on_page.get(pid, ()):
            for reason in reasons:
                hold.add(rid, reason)
    for rid, pages in placed.items():
        for pid in pages:
            for reason in page_reason.get(pid, ()):
                hold.add(rid, reason)
    if audit_refs:
        hold.sets["audit"] = len(audit_refs)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(gt_lines)")}
        rec_col = "record_id" if "record_id" in cols else "NULL"
        for ref, source, rec in conn.execute(
            f"SELECT line_image_ref, source, {rec_col} FROM gt_lines"
        ):
            if ref in audit_refs:
                rid = str(rec) if rec else record_id_from_source(source)
                if rid:
                    hold.add(rid, "audit")
    return hold


# --------------------------------------------------------------------------- #
# The corpus of one model
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Corpus:
    """The lines one model is estimated on, and what they are."""

    group: str
    lines: list[str] = field(default_factory=list)
    by_source: dict[str, dict[str, int]] = field(default_factory=dict)
    records: set[str] = field(default_factory=set)
    alphabet: Counter = field(default_factory=Counter)
    dropped_short: int = 0

    def add(
        self, source: str, record_id: str | None, raw: Iterable[str], *, form: str, fold: str
    ) -> None:
        tally = self.by_source.setdefault(source, {"lines": 0, "chars": 0, "records": 0})
        n_before = tally["lines"]
        for text in raw:
            line = normalize_line(text, form=form, fold=fold)
            if len(line) < MIN_LINE_CHARS:
                self.dropped_short += 1
                continue
            self.lines.append(line)
            self.alphabet.update(line)
            tally["lines"] += 1
            tally["chars"] += len(line)
        if record_id is not None and tally["lines"] > n_before:
            tally["records"] += 1
            self.records.add(record_id)

    @property
    def n_chars(self) -> int:
        return sum(len(x) for x in self.lines)

    def write(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for line in self.lines:
                fh.write(corpus_line(line) + "\n")
        return p


def classify_pieces(pieces: Mapping[str, Piece]) -> None:
    """Give every piece its census group, from its edition text where it has one,
    else from its minted lines."""
    from leibniz.enrich.pagelang import piece_group

    for piece in pieces.values():
        text = piece.edition_text or "\n".join(piece.gt)
        piece.group, piece.lang = piece_group(text)


def build_corpora(
    pieces: Mapping[str, Piece],
    hold: Holdout,
    *,
    sources: Sequence[str] = SOURCES,
    form: str = "NFC",
    fold: str = "none",
    extras: Mapping[str, tuple[str, Sequence[str]]] | None = None,
) -> tuple[dict[str, Corpus], dict]:
    """The two corpora, and the tally of what stayed out (held out, unplaced language).

    ``extras`` maps a name to ``(group, lines)``: the operator's own text.
    """
    corpora = {g: Corpus(g) for g in GROUPS}
    out = {"held_out": {s: {"records": 0, "lines": 0} for s in SOURCES}, "other_language": 0}
    for rid in sorted(pieces):
        piece = pieces[rid]
        if rid in hold:
            for s in SOURCES:
                lines = getattr(piece, s)
                if lines:
                    out["held_out"][s]["records"] += 1
                    out["held_out"][s]["lines"] += len(lines)
            continue
        if piece.group not in corpora:
            out["other_language"] += 1
            continue
        for s in sources:
            lines = getattr(piece, s)
            if lines:
                corpora[piece.group].add(s, rid, lines, form=form, fold=fold)
    for name, (group, lines) in (extras or {}).items():
        if group not in corpora:
            raise ValueError(f"--extra {name}: unknown group {group!r} ({' | '.join(GROUPS)})")
        corpora[group].add(f"extra:{name}", None, lines, form=form, fold=fold)
    return corpora, out


# --------------------------------------------------------------------------- #
# KenLM: lmplz and build_binary, run beside the repository
# --------------------------------------------------------------------------- #


class KenLMMissing(RuntimeError):
    """``lmplz`` or ``build_binary`` is not to be found."""


def find_tool(name: str, bin_dir: Path | str | None = None) -> Path:
    """A KenLM program: in ``bin_dir``, in ``$KENLM_BIN``, else on the PATH."""
    for d in (bin_dir, os.environ.get("KENLM_BIN")):
        if d and (Path(d) / name).exists():
            return Path(d) / name
    found = shutil.which(name)
    if found:
        return Path(found)
    raise KenLMMissing(
        f"{name} not found (looked in --kenlm-bin, $KENLM_BIN and the PATH): build KenLM's "
        "lmplz and build_binary from its source distribution (the R1 entry in STATUS.md has "
        "the commands)"
    )


Runner = Callable[..., subprocess.CompletedProcess]


def estimate(
    corpus: Path,
    arpa: Path,
    *,
    order: int = ORDER,
    bin_dir: Path | str | None = None,
    memory: str = "2G",
    tmp: Path | str | None = None,
    run: Runner | None = None,
) -> dict:
    """``lmplz``: modified Kneser-Ney, interpolated, of ``order``, to an ARPA file.

    A corpus too small for the discounts to be estimated (a fixture, a toy
    model) makes lmplz stop; it is then run again with ``--discount_fallback``
    and the result says so.
    """
    run = run or subprocess.run
    lmplz = find_tool("lmplz", bin_dir)
    cmd = [str(lmplz), "-o", str(order), "-S", memory, "--text", str(corpus), "--arpa", str(arpa)]
    if tmp is not None:
        Path(tmp).mkdir(parents=True, exist_ok=True)
        cmd += ["-T", str(tmp)]
    proc = run(cmd, capture_output=True, text=True)
    fallback = False
    if proc.returncode != 0 and "discount" in (proc.stderr or "").lower():
        fallback = True
        proc = run([*cmd, "--discount_fallback"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"lmplz failed ({proc.returncode}): {(proc.stderr or '')[-600:]}")
    return {
        "command": " ".join(cmd) + (" --discount_fallback" if fallback else ""),
        "discount_fallback": fallback,
    }


def binarize(
    arpa: Path, binary: Path, *, bin_dir: Path | str | None = None, run: Runner | None = None
) -> dict:
    """``build_binary``: the ARPA file as KenLM's probing binary, kept beside it."""
    run = run or subprocess.run
    tool = find_tool("build_binary", bin_dir)
    cmd = [str(tool), str(arpa), str(binary)]
    proc = run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"build_binary failed ({proc.returncode}): {(proc.stderr or '')[-600:]}")
    return {"command": " ".join(cmd)}


def arpa_counts(path: Path | str) -> dict[int, int]:
    """``{order: n-grams}`` from an ARPA file's header."""
    out: dict[int, int] = {}
    with Path(path).open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("ngram "):
                n, _, count = line[6:].partition("=")
                out[int(n)] = int(count)
            elif line.endswith("-grams:"):
                break
    return out


# --------------------------------------------------------------------------- #
# The whole build
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class BuildResult:
    summary: dict
    models: dict[str, dict]
    holdout: Holdout


def build(
    conn,
    *,
    cache: Path | str = DEFAULT_CACHE,
    out_dir: Path | str = DEFAULT_OUT,
    order: int = ORDER,
    sources: Sequence[str] = SOURCES,
    form: str = "NFC",
    fold: str = "none",
    wrap: int = WRAP,
    today: date | None = None,
    heldout: Path | str = DEFAULT_HELDOUT,
    pool: Path | str = DEFAULT_POOL,
    val_pieces: Path | str = DEFAULT_VAL_PIECES,
    audits: Sequence[Path | str] = DEFAULT_AUDITS,
    holdout_records: Path | str | None = None,
    extras: Mapping[str, tuple[str, Path | str]] | None = None,
    tokens: Path | str | None = None,
    bin_dir: Path | str | None = None,
    memory: str = "2G",
    place: bool = True,
    run: Runner | None = None,
    log: Callable[[str], None] | None = None,
) -> BuildResult:
    """Select, hold out, normalise, estimate: the two models and their record."""
    from leibniz.align.volumes import expired_volume_index
    from leibniz.htr.trainset import refs_from_csvs

    say = log or (lambda _m: None)
    today = today or date.today()
    if form not in FORMS:
        raise ValueError(f"unknown form {form!r} ({' | '.join(FORMS)})")
    unknown = [s for s in sources if s not in SOURCES]
    if unknown:
        raise ValueError(f"unknown sources {unknown} ({' | '.join(SOURCES)})")
    expired = expired_volume_index(today)

    pieces: dict[str, Piece] = {}
    left_edition: Counter = Counter()
    cache = Path(cache)
    if cache.exists():
        pieces, left_edition = read_edition(cache, expired, wrap=wrap)
    say(f"edition cache: {len(pieces):,} usable records; left out {dict(left_edition)}")
    gt, left_gt, on_page = read_gt(conn, expired)
    for rid, lines in gt.items():
        pieces.setdefault(rid, Piece(rid)).gt = lines
    say(f"gt_lines: {sum(len(v) for v in gt.values()):,} open lines on {len(gt):,} records")
    classify_pieces(pieces)

    page_sets: dict[str, set[str]] = {}
    for split, pages in pages_by_split(heldout).items():
        page_sets[f"philiumm:{split}"] = pages
    pool_pages = set().union(*pages_by_split(pool).values()) if Path(pool).exists() else set()
    if pool_pages:
        page_sets["letterpool"] = pool_pages
    record_sets: dict[str, set[str]] = {}
    val = column_values(val_pieces, "record_id")
    if val:
        record_sets["k3-val"] = val
    if holdout_records:
        record_sets["given"] = column_values(holdout_records, "record_id")
    placed = placed_pages(conn, pieces, today=today) if place else {}
    hold = build_holdout(
        conn,
        page_sets=page_sets,
        record_sets=record_sets,
        audit_refs=refs_from_csvs([p for p in audits if Path(p).exists()]),
        on_page=on_page,
        placed=placed,
    )
    say(f"held out: {len(hold.reasons):,} records ({hold.by_reason()})")

    extra_lines = {
        name: (group, read_extra(path)) for name, (group, path) in (extras or {}).items()
    }
    corpora, stayed = build_corpora(
        pieces, hold, sources=sources, form=form, fold=fold, extras=extra_lines
    )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    codec_names = (
        set(decoding.TokenTable.read(tokens, fold=fold).names) if tokens is not None else None
    )
    models: dict[str, dict] = {}
    for group, corpus in corpora.items():
        stem = out_dir / GROUP_FILES[group]
        info: dict = {
            "group": group,
            "name": GROUP_NAMES[group],
            "order": order,
            "form": form,
            "fold": fold,
            "wrap": wrap,
            "built": today.isoformat(),
            "lines": len(corpus.lines),
            "chars": corpus.n_chars,
            "records": len(corpus.records),
            "by_source": corpus.by_source,
            "alphabet": len(corpus.alphabet),
            "dropped_short": corpus.dropped_short,
            "arpa": None,
            "binary": None,
        }
        if codec_names is not None:
            outside = {
                ch: n
                for ch, n in corpus.alphabet.items()
                if decoding.lm_token(ch) not in codec_names
            }
            info["outside_codec"] = {
                "characters": len(outside),
                "occurrences": sum(outside.values()),
                "share": (sum(outside.values()) / corpus.n_chars) if corpus.n_chars else None,
                "most": [[ch, n] for ch, n in sorted(outside.items(), key=lambda kv: -kv[1])[:20]],
            }
        if not corpus.lines:
            say(f"{group}: no text: no model written")
            models[group] = info
            continue
        text_path = corpus.write(stem.with_suffix(".corpus.txt"))
        arpa = stem.with_suffix(".arpa")
        info["lmplz"] = estimate(
            text_path,
            arpa,
            order=order,
            bin_dir=bin_dir,
            memory=memory,
            tmp=out_dir / "tmp",
            run=run,
        )
        info["build_binary"] = binarize(arpa, stem.with_suffix(".bin"), bin_dir=bin_dir, run=run)
        info["arpa"] = str(arpa)
        info["binary"] = str(stem.with_suffix(".bin"))
        info["ngrams"] = arpa_counts(arpa) if arpa.exists() else {}
        stem.with_suffix(".json").write_text(
            json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        say(f"{group}: {info['lines']:,} lines, {info['chars']:,} characters → {arpa}")
        models[group] = info

    shutil.rmtree(out_dir / "tmp", ignore_errors=True)  # lmplz's sorting files

    summary = {
        "generated": today.isoformat(),
        "order": order,
        "form": form,
        "fold": fold,
        "wrap": wrap,
        "sources": list(sources),
        "cache": str(cache),
        "edition": {
            "usable_records": sum(1 for p in pieces.values() if p.edition),
            "left_out": dict(sorted(left_edition.items())),
        },
        "gt": {
            "open_lines": sum(len(v) for v in gt.values()),
            "records": len(gt),
            "left_out": dict(sorted(left_gt.items())),
        },
        "holdout": {
            "records": len(hold.reasons),
            "by_reason": hold.by_reason(),
            "sets": dict(sorted(hold.sets.items())),
            "placed_records": len(placed),
            "left_out": stayed["held_out"],
        },
        "other_language_records": stayed["other_language"],
        "extras": {
            name: {"group": group, "path": str(path)}
            for name, (group, path) in (extras or {}).items()
        },
        "models": models,
    }
    return BuildResult(summary=summary, models=models, holdout=hold)


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


def _n(x: int | None) -> str:
    return "—" if x is None else f"{x:,}"


_LEFT_OUT = {
    "empty": "no text",
    "no_refs": "the cache line names no printed piece",
    "no_channel": "a piece without a recorded channel",
    "no_volume": "no volume to test",
    "not_70_expired": "a volume not yet §70-free",
    "nc_channel": "a channel with non-commercial terms (the NC deposit)",
    "channel_not_released": "a channel the registry releases in no deposit",
    "nc_bucket": "the nc bucket",
    "no_record": "no record named",
}
_REASONS = {
    "k3-val": "K3's validation pieces",
    "letterpool": "the letter pool's pages",
    "audit": "a judged audit line",
    "given": "named by the operator",
}


def _reason(key: str) -> str:
    if key.startswith("philiumm:"):
        return f"PHILIUMM's pages, split `{key.split(':', 1)[1]}`"
    return _REASONS.get(key, key)


def render_report(summary: Mapping) -> str:
    s = summary
    out = [
        "# R1 — the language models (`leibniz bench lm-build`)",
        "",
        f"_Generated {s['generated']}. Character {s['order']}-grams, KenLM `lmplz` (modified "
        f"Kneser-Ney, interpolated); text normalised to {s['form']}"
        + (
            ", the aligner's fold applied"
            if s["fold"] == "align"
            else ", case, accents and punctuation kept"
        )
        + (
            f"; the edition's running text cut into lines of at most {s['wrap']} characters at "
            "word boundaries"
            if s["wrap"] > 0
            else "; the edition's text in its own lines"
        )
        + "; a minted line as it stands, its line-end hyphen included. Sources: "
        + ", ".join(f"`{x}`" for x in s["sources"])
        + "._",
        "",
        "## What each model saw",
        "",
        "| Model | Lines | Characters | Records | Alphabet | "
        + " | ".join(f"`{x}` lines · characters · records" for x in _source_keys(s))
        + " | n-grams by order |",
        "| --- | ---: | ---: | ---: | ---: | "
        + " | ".join("---" for _ in _source_keys(s))
        + " | --- |",
    ]
    for _group, m in s["models"].items():
        cells = []
        for key in _source_keys(s):
            t = m["by_source"].get(key)
            cells.append(
                "—" if not t else f"{_n(t['lines'])} · {_n(t['chars'])} · {_n(t['records'])}"
            )
        grams = " · ".join(
            f"{k}: {_n(v)}"
            for k, v in sorted((m.get("ngrams") or {}).items(), key=lambda kv: int(kv[0]))
        )
        out.append(
            f"| {m['name']} (`{Path(m['arpa']).name if m['arpa'] else 'not written'}`) | "
            f"{_n(m['lines'])} | {_n(m['chars'])} | {_n(m['records'])} | {_n(m['alphabet'])} | "
            + " | ".join(cells)
            + f" | {grams or '—'} |"
        )
    out += [
        "",
        "Both sources are text of the open deposit: every printed piece in a §70-free volume, "
        "read through a channel the licence registry places there (`legal.deposit_for`). The "
        "letter pool, the Dresden lines and the PHILIUMM dataset are evaluation material and "
        "are in neither model.",
        "",
        "## What was left out",
        "",
        f"- **The edition cache** (`{s['cache']}`): {_n(s['edition']['usable_records'])} records "
        "usable; left out "
        + (
            "; ".join(
                f"{_n(n)} — {_LEFT_OUT.get(k, k)}" for k, n in s["edition"]["left_out"].items()
            )
            or "none"
        )
        + ".",
        f"- **`gt_lines`**: {_n(s['gt']['open_lines'])} usable lines on {_n(s['gt']['records'])} "
        "records; rows left out "
        + (
            "; ".join(f"{_n(n)} — {_LEFT_OUT.get(k, k)}" for k, n in s["gt"]["left_out"].items())
            or "none"
        )
        + ".",
        f"- **A language neither model takes**: {_n(s['other_language_records'])} record(s) the "
        "stopword lists place in neither group (too short, or mixed without German leading).",
        "",
        "## The held-out pieces",
        "",
        f"{_n(s['holdout']['records'])} records are held out whole, from both sources "
        f"({_n(s['holdout']['left_out']['edition']['records'])} with edition text, "
        f"{_n(s['holdout']['left_out']['edition']['lines'])} lines; "
        f"{_n(s['holdout']['left_out']['gt']['records'])} with minted lines, "
        f"{_n(s['holdout']['left_out']['gt']['lines'])} lines). A record can have several reasons.",
        "",
        "| Evaluation set | Pages or ids given | Records held out |",
        "| --- | ---: | ---: |",
    ]
    for key in sorted(set(s["holdout"]["sets"]) | set(s["holdout"]["by_reason"])):
        out.append(
            f"| {_reason(key)} | {_n(s['holdout']['sets'].get(key))} | "
            f"{_n(s['holdout']['by_reason'].get(key, 0))} |"
        )
    out += [
        "",
        "A record stands on a held-out page when a minted row of it does, or when the factory's "
        f"placement puts it there ({_n(s['holdout']['placed_records'])} records with usable text "
        "placed). The Dresden lines are not Leibniz's and have no piece in the edition; the "
        "record ids are in `lm-holdout-pieces.csv`.",
    ]
    for _group, m in s["models"].items():
        oc = m.get("outside_codec")
        if oc:
            share = "—" if oc["share"] is None else f"{100 * oc['share']:.3f} %"
            most = ", ".join(f"`{ch}` {_n(n)}" for ch, n in oc["most"][:12])
            out += [
                "",
                f"**{m['name']}, against the reader's tokens:** {_n(oc['characters'])} characters "
                f"of the text are not in the codec ({_n(oc['occurrences'])} occurrences, {share} "
                f"of the characters): {most or 'none'}. The reader cannot write them; the model "
                "keeps them as context.",
            ]
    if s.get("extras"):
        out += [
            "",
            "**Text added by the operator:** "
            + "; ".join(f"`{k}` ({v['group']}: `{v['path']}`)" for k, v in s["extras"].items())
            + ".",
        ]
    out += [
        "",
        "## How to read it",
        "",
        "The models are estimated from the edition's constituted text, which expands "
        "abbreviations and regularises u/v and i/j where the manuscript does not; a diplomatic "
        "reader's line and this text differ by those conventions, so the gain is measured, not "
        "assumed (R1 Task 3, on PHILIUMM's validation split). The commands, as run:",
        "",
    ]
    for _group, m in s["models"].items():
        if m.get("lmplz"):
            out.append(
                f"- `{m['lmplz']['command']}`"
                + (
                    " (the discounts could not be estimated on so little text: KenLM's fallback)"
                    if m["lmplz"]["discount_fallback"]
                    else ""
                )
            )
            out.append(f"- `{m['build_binary']['command']}`")
    return "\n".join(out) + "\n"


def _source_keys(summary: Mapping) -> list[str]:
    keys: list[str] = []
    for m in summary["models"].values():
        for k in m["by_source"]:
            if k not in keys:
                keys.append(k)
    return keys or list(summary["sources"])


def write_outputs(
    result: BuildResult, reports_dir: Path | str = DEFAULT_REPORTS_DIR
) -> dict[str, Path]:
    """``lm-build.md``, ``lm-build.json`` and ``lm-holdout-pieces.csv``."""
    d = Path(reports_dir)
    d.mkdir(parents=True, exist_ok=True)
    md = d / "lm-build.md"
    js = d / "lm-build.json"
    held = d / "lm-holdout-pieces.csv"
    md.write_text(render_report(result.summary), encoding="utf-8")
    js.write_text(json.dumps(result.summary, ensure_ascii=False, indent=1), encoding="utf-8")
    with held.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id", "reasons"])
        for rid in sorted(result.holdout.reasons):
            w.writerow([rid, " ".join(sorted(result.holdout.reasons[rid]))])
    return {"report": md, "json": js, "holdout": held}


__all__ = [
    "DEFAULT_CACHE",
    "DEFAULT_OUT",
    "GROUPS",
    "ORDER",
    "SOURCES",
    "WRAP",
    "BuildResult",
    "Corpus",
    "Holdout",
    "KenLMMissing",
    "Piece",
    "arpa_counts",
    "binarize",
    "build",
    "build_corpora",
    "build_holdout",
    "corpus_line",
    "estimate",
    "find_tool",
    "gate",
    "normalize_line",
    "pages_by_split",
    "placed_pages",
    "read_edition",
    "read_extra",
    "read_gt",
    "render_report",
    "volume_key",
    "wrap_text",
    "write_outputs",
]
