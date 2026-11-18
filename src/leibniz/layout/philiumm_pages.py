"""PHILIUMM's layout training pages → this project's page ids (P1 Task 3).

Her dataset ``DenisaBumba/layout-leibniz-dataset-v2`` (Hugging Face, CC BY
4.0) carries the originals under ``original/train``, ``original/valid`` and
``original/test`` with a COCO ``_annotations.coco.json`` in each folder; the
``train/`` and ``valid/`` folders hold the augmented copies. The census
sample must stay outside the train and valid pages, and her 18 test pages
may enter it as a named block.

The names are Roboflow's: ``<stem>_jpg.rf.<hash>.jpg``. The stem is a
shelfmark and folio as the HTR dataset's files are (``LH_35_1_14_0065r``,
an opening ``LH_35_1_3_0023r-0017v``), the same with an ``img_`` prefix and
unpadded folio numbers (``img_LH_35_5_25_1v``, sometimes with ``_g``/``_d``
for the left or right half of an opening), a Göttingen manuscript
(``8_cod_ms_philos_140_0002``: not the GWLB's, so never in the store), an
eScriptorium page id (``0001_page_12210614_docId_307926``) or a bare folio
(``3r``). The last two are matched by the image's size, which the COCO file
states, against ``pages.width``/``height``; when several pages share the
size, the original is downloaded and compared with each candidate's cached
scan as a small greyscale thumbnail.

Everything read from the Hub is cached under ``data/philiumm/layout-dataset/``
and fetched politely (one request a second, the project's User-Agent).
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import db
from leibniz.align.philiumm.vi4 import FileName, resolve_pages, work_index
from leibniz.net import PoliteClient, default_user_agent

HF_DATASET = "DenisaBumba/layout-leibniz-dataset-v2"
HF_API = f"https://huggingface.co/api/datasets/{HF_DATASET}"
SPLITS = {"train": "original/train", "valid": "original/valid", "test": "original/test"}
ANNOTATIONS = "_annotations.coco.json"
LISTING_NAME = "hf-files.json"
GOETTINGEN = "cod_ms_philos"

_RF = re.compile(r"^(?P<stem>.+?)_(?:jpg|jpeg|png)\.rf\.[0-9a-f]+\.(?:jpg|jpeg|png)$", re.I)
_SHELFMARK = re.compile(
    r"^(?:img_)?(?P<family>LH|LBr)_(?P<rest>.+?)_(?P<f1>\d{1,4})(?P<s1>[rv])?"
    r"(?:-(?P<f2>\d{1,4})(?P<s2>[rv])?)?(?:_(?P<half>[gd]))?$"
)
_ESCRIPTORIUM = re.compile(r"^\d+_page_(?P<page>\d+)_docId_(?P<doc>\d+)$")
_FOLIO = re.compile(r"^\d{1,4}[rv]$")


def hf_file_url(path: str, *, revision: str = "main") -> str:
    return f"https://huggingface.co/datasets/{HF_DATASET}/resolve/{revision}/{path}"


def fetch_listing(dest: Path, *, client: PoliteClient | None = None) -> dict:
    """The Hub's file listing and revision, cached as ``hf-files.json``."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / LISTING_NAME
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    own = client is None
    client = client or PoliteClient(user_agent=default_user_agent())
    try:
        meta = client.get_json(HF_API)
    finally:
        if own:
            client.close()
    listing = {
        "dataset": HF_DATASET,
        "sha": meta.get("sha"),
        "lastModified": meta.get("lastModified"),
        "license": (meta.get("cardData") or {}).get("license"),
        "files": sorted(s["rfilename"] for s in meta.get("siblings", [])),
    }
    path.write_text(json.dumps(listing, indent=1) + "\n", encoding="utf-8")
    return listing


def fetch_annotations(
    dest: Path, listing: dict, *, client: PoliteClient | None = None
) -> dict[str, Path]:
    """The three COCO files, cached as ``<split>_annotations.coco.json``."""
    dest = Path(dest)
    out: dict[str, Path] = {}
    own = client is None
    client = client or PoliteClient(user_agent=default_user_agent())
    try:
        for split, folder in SPLITS.items():
            rel = f"{folder}/{ANNOTATIONS}"
            if rel not in listing["files"]:
                continue
            path = dest / f"{split}_{ANNOTATIONS}"
            if not path.exists():
                data = client.get_bytes(hf_file_url(rel, revision=listing.get("sha") or "main"))
                path.write_bytes(data)
            out[split] = path
    finally:
        if own:
            client.close()
    return out


@dataclass(slots=True)
class CocoImage:
    split: str
    file_name: str
    width: int
    height: int
    n_annotations: int = 0


def read_coco(path: Path, split: str) -> tuple[list[CocoImage], dict[int, str]]:
    """The images of a COCO file (with their annotation counts) and its
    category names."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    counts: dict[int, int] = {}
    for a in data.get("annotations", []):
        counts[a["image_id"]] = counts.get(a["image_id"], 0) + 1
    images = [
        CocoImage(
            split, im["file_name"], int(im["width"]), int(im["height"]), counts.get(im["id"], 0)
        )
        for im in data.get("images", [])
    ]
    cats = {int(c["id"]): c["name"] for c in data.get("categories", [])}
    return images, cats


# --------------------------------------------------------------------------- #
# Names
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class DatasetName:
    """A dataset file name read: its stem and what kind of name it is."""

    file_name: str
    stem: str
    kind: str  # shelfmark | goettingen | escriptorium | folio | other
    shelfmark: FileName | None = None
    half: str | None = None  # "g" (left) or "d" (right) half of an opening
    note: str = ""


def stem_of(file_name: str) -> str:
    base = file_name.rsplit("/", 1)[-1]
    m = _RF.match(base)
    if m:
        return m.group("stem")
    return re.sub(r"\.(?:jpg|jpeg|png|xml)$", "", base, flags=re.I)


def parse_dataset_name(file_name: str, split: str = "train") -> DatasetName:
    stem = stem_of(file_name)
    m = _SHELFMARK.match(stem)
    if m:
        folios = [(int(m.group("f1")), m.group("s1") or "")]
        if m.group("f2"):
            folios.append((int(m.group("f2")), m.group("s2") or ""))
        note = "" if all(s for _, s in folios) else "a folio without a side letter"
        fn = FileName(
            stem, split, m.group("family"), tuple(m.group("rest").split("_")), folios, note
        )
        half = m.group("half")
        if half:
            note = (
                note + "; " if note else ""
            ) + f"the {'left' if half == 'g' else 'right'} half of an opening"
        return DatasetName(file_name, stem, "shelfmark", fn, half, note)
    if GOETTINGEN in stem.lower():
        return DatasetName(
            file_name, stem, "goettingen", note="Göttingen, Cod. Ms. philos. 140: not a GWLB scan"
        )
    if _ESCRIPTORIUM.match(stem):
        return DatasetName(
            file_name, stem, "escriptorium", note="an eScriptorium page id; matched by image size"
        )
    if _FOLIO.match(stem):
        return DatasetName(file_name, stem, "folio", note="a bare folio; matched by image size")
    return DatasetName(
        file_name, stem, "other", note="name of no known shape; matched by image size"
    )


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class PageMatch:
    file_name: str
    stem: str
    split: str
    kind: str
    width: int
    height: int
    # matched | size-matched | thumbnail-matched | not-gwlb | no_work | no_page |
    # ambiguous | unmatched
    status: str
    page_ids: list[str] = field(default_factory=list)
    work_ids: list[str] = field(default_factory=list)
    size_agrees: bool | None = None  # their image size == the page's size (single pages)
    ratio_agrees: bool | None = None  # the aspect ratios agree within 2 % (a rescaled copy)
    notes: list[str] = field(default_factory=list)


def size_candidates(conn: sqlite3.Connection, width: int, height: int) -> list[db.Page]:
    rows = conn.execute(
        "SELECT * FROM pages WHERE width = ? AND height = ? ORDER BY page_id", (width, height)
    ).fetchall()
    return [db._page_from_row(r) for r in rows]


def _grey_thumb(data: bytes, size: tuple[int, int] = (24, 32)):
    import io

    from PIL import Image

    with Image.open(io.BytesIO(data)) as im:
        small = im.convert("L").resize(size)
        flat = getattr(small, "get_flattened_data", None)  # Pillow 11+; getdata goes in 14
        return list(flat() if flat is not None else small.getdata())


def thumb_distance(a: Sequence[int], b: Sequence[int]) -> float:
    """Mean absolute grey difference of two equal-sized thumbnails (0–255)."""
    if not a or len(a) != len(b):
        return 255.0
    return sum(abs(x - y) for x, y in zip(a, b, strict=True)) / len(a)


def _same_ratio(w: int | None, h: int | None, w2: int, h2: int, tol: float = 0.02) -> bool:
    if not w or not h or not w2 or not h2:
        return False
    return abs(w / h - w2 / h2) <= tol * (w2 / h2)


def match_by_image(
    name: DatasetName,
    image: CocoImage,
    conn: sqlite3.Connection,
    *,
    images_root: Path | None,
    fetch_original: Callable[[str], bytes] | None,
    max_candidates: int = 12,
    candidates: Sequence[db.Page] | None = None,
) -> PageMatch:
    """A page for a name that is no shelfmark: the pages of the image's size,
    then (several) the closest cached scan to the downloaded original. With
    ``candidates`` (the pages of a work known by name but without folio
    labels) the pages of the image's shape are compared instead."""
    pm = PageMatch(
        image.file_name, name.stem, image.split, name.kind, image.width, image.height, "unmatched"
    )
    if candidates is None:
        cands = size_candidates(conn, image.width, image.height)
        if not cands:
            pm.notes.append(f"no page of {image.width}×{image.height}")
            return pm
    else:
        exact = [p for p in candidates if (p.width, p.height) == (image.width, image.height)]
        cands = exact or [
            p for p in candidates if _same_ratio(p.width, p.height, image.width, image.height)
        ]
        if not cands:
            pm.notes.append(f"no page of the shape {image.width}×{image.height} in the work")
            return pm
        pm.notes.append(
            f"{len(exact)} pages of that size in the work"
            if exact
            else f"{len(cands)} pages of that shape in the work"
        )
    if len(cands) == 1:
        pm.status, pm.page_ids, pm.work_ids = "size-matched", [cands[0].id], [cands[0].work_id]
        pm.size_agrees = True
        pm.notes.append("one page of that size")
        return pm
    pm.notes.append(f"{len(cands)} pages of that size")
    if fetch_original is None or images_root is None or len(cands) > max_candidates:
        pm.status = "ambiguous"
        pm.page_ids = [p.id for p in cands[:max_candidates]]
        return pm
    try:
        ref = _grey_thumb(fetch_original(f"{SPLITS[image.split]}/{image.file_name}"))
    except Exception as exc:  # network or decode
        pm.status = "ambiguous"
        pm.page_ids = [p.id for p in cands]
        pm.notes.append(f"original not compared: {exc}")
        return pm
    scored: list[tuple[float, db.Page]] = []
    for p in cands:
        path = Path(images_root) / (p.local_path or f"{p.work_id}/{p.seq:04d}.jpg")
        if not path.exists():
            continue
        try:
            scored.append((thumb_distance(ref, _grey_thumb(path.read_bytes())), p))
        except Exception:  # an unreadable cache file
            continue
    scored.sort(key=lambda t: t[0])
    if not scored:
        pm.status = "ambiguous"
        pm.page_ids = [p.id for p in cands]
        pm.notes.append("no candidate's scan is cached")
        return pm
    best = scored[0]
    pm.notes.append("thumbnail distance " + ", ".join(f"{p.id} {d:.1f}" for d, p in scored[:3]))
    ties = [p for d, p in scored if d <= best[0] + 1.0]
    rest = [d for d, _ in scored if d > best[0] + 1.0]
    if best[0] <= 12.0 and (not rest or rest[0] >= 2 * max(best[0], 1.0)):
        # equal distances are one scan registered under two labels (W5's twins)
        pm.status = "thumbnail-matched"
        pm.page_ids = [p.id for p in ties]
        pm.work_ids = sorted({p.work_id for p in ties})
        pm.size_agrees = (ties[0].width, ties[0].height) == (image.width, image.height)
        pm.ratio_agrees = _same_ratio(ties[0].width, ties[0].height, image.width, image.height)
        if len(ties) > 1:
            pm.notes.append(f"{len(ties)} registrations of the same scan, all taken")
    else:
        pm.status = "ambiguous"
        pm.page_ids = [p.id for _, p in scored[:3]]
    return pm


def match_images(
    conn: sqlite3.Connection,
    images: Sequence[CocoImage],
    *,
    index: dict[str, list[str]] | None = None,
    images_root: Path | None = None,
    fetch_original: Callable[[str], bytes] | None = None,
) -> list[PageMatch]:
    """Every image of the COCO files → a :class:`PageMatch`."""
    index = index if index is not None else work_index(conn)
    out: list[PageMatch] = []
    for im in images:
        name = parse_dataset_name(im.file_name, im.split)
        if name.kind == "goettingen":
            out.append(
                PageMatch(
                    im.file_name,
                    name.stem,
                    im.split,
                    name.kind,
                    im.width,
                    im.height,
                    "not-gwlb",
                    notes=[name.note],
                )
            )
            continue
        if name.kind != "shelfmark" or name.shelfmark is None:
            out.append(
                match_by_image(
                    name, im, conn, images_root=images_root, fetch_original=fetch_original
                )
            )
            continue
        fm = resolve_pages(conn, name.shelfmark, index)
        if fm.status == "no_work" and len(name.shelfmark.tokens) > 1:
            # LH_35_4_20_14_0006v: the store's work is LH 35, 4, 20 (the piece
            # number is hers); try the key without its last token once
            shorter = FileName(
                name.shelfmark.name,
                name.shelfmark.split,
                name.shelfmark.family,
                name.shelfmark.tokens[:-1],
                list(name.shelfmark.folios),
                name.shelfmark.note,
            )
            fm2 = resolve_pages(conn, shorter, index)
            if fm2.status != "no_work":
                fm2.notes.insert(
                    0, f"the shelfmark's last part ({name.shelfmark.tokens[-1]}) dropped"
                )
                fm = fm2
        pm = PageMatch(
            im.file_name,
            name.stem,
            im.split,
            name.kind,
            im.width,
            im.height,
            fm.status,
            list(fm.page_ids),
            list(fm.work_ids),
            notes=list(fm.notes),
        )
        if name.note:
            pm.notes.insert(0, name.note)
        if fm.page_ids and fm.status in ("matched", "ambiguous_work"):
            pm.status = "matched"
            if len(fm.page_ids) == 1:
                page = db.get_page(conn, fm.page_ids[0])
                if page is not None and page.width and page.height:
                    pm.size_agrees = (page.width, page.height) == (im.width, im.height)
                    pm.ratio_agrees = _same_ratio(page.width, page.height, im.width, im.height)
        elif fm.status == "no_page" and fm.work_ids:
            # the work is known but carries no folio labels: match the scan itself
            pages = [p for w in fm.work_ids for p in db.get_pages(conn, w)]
            by_image = match_by_image(
                name,
                im,
                conn,
                images_root=images_root,
                fetch_original=fetch_original,
                candidates=pages,
            )
            by_image.kind = name.kind
            by_image.notes = pm.notes + by_image.notes
            pm = by_image
        out.append(pm)
    return out


def write_pages_csv(matches: Sequence[PageMatch], path: Path) -> int:
    """One row per dataset image: ``file, split, kind, status, page_ids, work_ids,
    width, height, size_agrees, note``; the page ids ``;``-joined."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "file",
                "split",
                "kind",
                "status",
                "page_ids",
                "work_ids",
                "width",
                "height",
                "size_agrees",
                "ratio_agrees",
                "note",
            ]
        )
        for m in sorted(matches, key=lambda m: (m.split, m.stem)):
            w.writerow(
                [
                    m.stem,
                    m.split,
                    m.kind,
                    m.status,
                    ";".join(m.page_ids),
                    ";".join(m.work_ids),
                    m.width,
                    m.height,
                    "" if m.size_agrees is None else ("yes" if m.size_agrees else "no"),
                    "" if m.ratio_agrees is None else ("yes" if m.ratio_agrees else "no"),
                    " | ".join(m.notes),
                ]
            )
    return len(matches)


def read_pages_csv(path: Path, *, splits: Sequence[str] | None = None) -> set[str]:
    """The page ids of the rows (optionally of some splits only)."""
    out: set[str] = set()
    with Path(path).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if splits and row["split"] not in splits:
                continue
            out.update(p for p in row["page_ids"].split(";") if p)
    return out


def summary(
    matches: Sequence[PageMatch], listing: dict | None = None, cats: dict | None = None
) -> dict:
    by_split: dict[str, dict[str, int]] = {}
    pages_by_split: dict[str, set[str]] = {}
    for m in matches:
        d = by_split.setdefault(m.split, {})
        d[m.status] = d.get(m.status, 0) + 1
        pages_by_split.setdefault(m.split, set()).update(m.page_ids)
    single = [m for m in matches if m.size_agrees is not None and m.status == "matched"]
    return {
        "dataset": HF_DATASET,
        "revision": (listing or {}).get("sha"),
        "license": (listing or {}).get("license"),
        "categories": sorted((cats or {}).values()),
        "images": len(matches),
        "by_split": by_split,
        "pages_by_split": {k: len(v) for k, v in pages_by_split.items()},
        "pages_train_valid": len(
            pages_by_split.get("train", set()) | pages_by_split.get("valid", set())
        ),
        "pages_test": len(pages_by_split.get("test", set())),
        "size_check": {
            "single_pages_resolved_by_name": len(single),
            "size_agrees": sum(1 for m in single if m.size_agrees),
            "ratio_agrees": sum(1 for m in single if m.ratio_agrees),
        },
    }


__all__ = [
    "ANNOTATIONS",
    "HF_DATASET",
    "SPLITS",
    "CocoImage",
    "DatasetName",
    "PageMatch",
    "fetch_annotations",
    "fetch_listing",
    "match_by_image",
    "match_images",
    "parse_dataset_name",
    "read_coco",
    "read_pages_csv",
    "size_candidates",
    "stem_of",
    "summary",
    "thumb_distance",
    "write_pages_csv",
]
