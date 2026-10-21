"""A pack against its contract — ``leibniz pack check`` (Phase G1).

The contract between this project and Calculemus is the game's SPECS §6.6
(schema_version 1, JSONL, one object per line), mirrored here as two JSON
schemas: ``fragment_pack.schema.json`` (Leibniz Legible ⇒ game) and
``judgment_pack.schema.json`` (game ⇒ Leibniz Legible). Every fragment pack
is checked before it leaves the desktop; every judgment pack is checked
before ``leibniz pack judgments`` reads a row of it.

Two layers. The schema says what each object holds: the header first, the
keys and their types, the enums, ``license_bucket`` 'open' and nothing else,
exactly two candidates, no key the contract does not name. The rules the
schema cannot say come after it, per row: the two candidates distinct, a
gold row with exactly one of ``truth_cand_id`` and ``both_wrong: true`` (and
its truth among the row's candidates), a static image with its URL, the
length the row claims; across rows, each fragment and each line once. A row
the schema rejects is not looked at further, so a fault is reported once.

The validator is this module's own: the keywords the two schemas use and no
others (:data:`KEYWORDS`). A schema that names any other keyword is refused
when it loads, so nothing in it can go unchecked; the project adds no
dependency for it (the desktop environments run ``uv run --no-sync``).
``NaN`` and ``Infinity``, which Python's JSON reader accepts and the JSON
standard does not, are refused too.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent
FRAGMENT_SCHEMA = SCHEMA_DIR / "fragment_pack.schema.json"
JUDGMENT_SCHEMA = SCHEMA_DIR / "judgment_pack.schema.json"
SCHEMA_VERSION = 1
FRAGMENT_HEADER = "fragment_pack_header"
JUDGMENT_HEADER = "judgment_pack_header"
MAX_SHOWN = 50  # errors printed by the command; the report keeps them all
# This project's canonical line id: "{work_id}:{seq:04d}:{line_seq:03d}" (SPECS §4.4).
LINE_ID = re.compile(r"(?P<page>(?P<work>[^:\s]+):\d{4}):\d{3}")

# The JSON Schema keywords this validator enforces, and the annotations it reads past.
KEYWORDS = frozenset(
    {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "enum",
        "const",
        "minimum",
        "maximum",
        "minLength",
        "minItems",
        "maxItems",
        "items",
        "$ref",
    }
)
ANNOTATIONS = frozenset({"$schema", "$id", "$defs", "$comment", "title", "description"})


class SchemaError(ValueError):
    """A schema uses a keyword this validator does not enforce."""


# --------------------------------------------------------------------------- #
# The validator (a subset of JSON Schema 2020-12)
# --------------------------------------------------------------------------- #


def load_schema(path: Path | str) -> dict:
    """A schema from disk, refused if it names a keyword :data:`KEYWORDS` lacks."""
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    assert_supported(schema)
    return schema


def assert_supported(schema: Mapping, where: str = "#") -> None:
    """Raise :class:`SchemaError` for any keyword the validator would skip."""
    for key, value in schema.items():
        if key not in KEYWORDS and key not in ANNOTATIONS:
            raise SchemaError(f"{where}: unsupported keyword {key!r}")
        if key == "$defs" or key == "properties":
            for name, sub in value.items():
                assert_supported(sub, f"{where}/{key}/{name}")
        elif key == "items":
            assert_supported(value, f"{where}/items")
        elif key == "additionalProperties" and not isinstance(value, bool):
            raise SchemaError(f"{where}: additionalProperties must be true or false")
        elif key == "$ref" and not str(value).startswith("#/$defs/"):
            raise SchemaError(f"{where}: only local references (#/$defs/…) are supported")


def _is_type(value: object, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if name == "string":
        return isinstance(value, str)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "null":
        return value is None
    raise SchemaError(f"unknown type {name!r}")


def _resolve(ref: str, root: Mapping) -> Mapping:
    name = ref.removeprefix("#/$defs/")
    try:
        return root["$defs"][name]
    except KeyError as exc:
        raise SchemaError(f"unresolved reference {ref!r}") from exc


def _equal(a: object, b: object) -> bool:
    """JSON equality: ``1`` is not ``true``, as Python's ``==`` would have it."""
    return type(a) is type(b) and a == b


def validate(
    instance: object, schema: Mapping, root: Mapping | None = None, path: str = "$"
) -> list[str]:
    """The ways ``instance`` fails ``schema``, one message each (empty when it passes)."""
    root = schema if root is None else root
    if "$ref" in schema:
        return validate(instance, _resolve(schema["$ref"], root), root, path)
    errors: list[str] = []
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(instance, n) for n in names):
            want = " or ".join(names)
            return [f"{path}: expected {want}, got {_kind(instance)} {_show(instance)}"]
    if "const" in schema and not _equal(instance, schema["const"]):
        errors.append(f"{path}: must be {_show(schema['const'])}, got {_show(instance)}")
    if "enum" in schema and not any(_equal(instance, v) for v in schema["enum"]):
        allowed = ", ".join(_show(v) for v in schema["enum"])
        errors.append(f"{path}: must be one of {allowed}, got {_show(instance)}")
    if _is_type(instance, "number"):
        if not math.isfinite(instance):  # type: ignore[arg-type]
            errors.append(f"{path}: must be a finite number")
        if "minimum" in schema and instance < schema["minimum"]:  # type: ignore[operator]
            errors.append(f"{path}: {instance} is under the minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:  # type: ignore[operator]
            errors.append(f"{path}: {instance} is over the maximum {schema['maximum']}")
    if isinstance(instance, str) and len(instance) < schema.get("minLength", 0):
        errors.append(f"{path}: shorter than {schema['minLength']} character(s)")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: {len(instance)} item(s), at least {schema['minItems']} wanted")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: {len(instance)} item(s), at most {schema['maxItems']} allowed")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", ()):
            if key not in instance:
                errors.append(f"{path}: missing {key!r}")
        if schema.get("additionalProperties", True) is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: unexpected key {key!r}")
        for key, sub in props.items():
            if key in instance:
                errors += validate(instance[key], sub, root, f"{path}.{key}")
    return errors


def _kind(value: object) -> str:
    return {
        bool: "boolean",
        int: "integer",
        float: "number",
        str: "string",
        list: "array",
        dict: "object",
        type(None): "null",
    }.get(type(value), type(value).__name__)


def _show(value: object, limit: int = 60) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --------------------------------------------------------------------------- #
# Reading a pack
# --------------------------------------------------------------------------- #


def _refuse_constant(name: str) -> float:
    raise ValueError(f"{name} is not JSON")


def parse_line(raw: str) -> object:
    """One JSONL line, ``NaN``/``Infinity`` refused."""
    return json.loads(raw, parse_constant=_refuse_constant)


def read_jsonl(path: Path | str) -> Iterable[tuple[int, str]]:
    """``(line number, text)`` for every line of the file, from 1; a final
    newline ends the last line, it does not open another."""
    with Path(path).open(encoding="utf-8") as fh:
        for n, raw in enumerate(fh, start=1):
            yield n, raw.rstrip("\n").rstrip("\r")


@dataclass(slots=True)
class CheckReport:
    """What :func:`check_fragment_pack` / :func:`check_judgment_pack` found."""

    path: str
    kind: str
    header: dict | None = None
    rows: list[dict] = field(default_factory=list)  # the rows that passed, in order
    raws: list[str] = field(default_factory=list)  # their lines as read, in the same order
    line_nos: list[int] = field(default_factory=list)  # and their line numbers
    n_rows: int = 0  # rows read, passed or not
    errors: list[str] = field(default_factory=list)
    counts: Counter = field(default_factory=Counter)

    @property
    def ok(self) -> bool:
        return not self.errors and self.header is not None

    def error(self, line: int, message: str) -> None:
        self.errors.append(f"line {line}: {message}")


def _read_pack(path: Path | str, kind: str, schema: Mapping, header_kind: str) -> CheckReport:
    """Header and rows through the schema; the rows that pass are kept."""
    report = CheckReport(path=str(path), kind=kind)
    header_def = {"$ref": "#/$defs/header"}
    row_def = {"$ref": "#/$defs/row"}
    first = True
    for n, raw in read_jsonl(path):
        if not raw.strip():
            report.error(n, "blank line (one JSON object per line)")
            continue
        try:
            obj = parse_line(raw)
        except ValueError as exc:
            report.error(n, f"not JSON: {exc}")
            first = False
            continue
        if first:
            first = False
            if not isinstance(obj, dict) or obj.get("kind") != header_kind:
                report.error(n, f"the first line must be the header (kind {header_kind!r})")
            else:
                errs = validate(obj, header_def, schema)
                for e in errs:
                    report.error(n, e)
                if not errs:
                    report.header = obj
                continue
        report.n_rows += 1
        if isinstance(obj, dict) and obj.get("kind") == header_kind:
            report.error(n, "a second header")
            continue
        errs = validate(obj, row_def, schema)
        for e in errs:
            report.error(n, e)
        if not errs:
            report.rows.append(obj)  # type: ignore[arg-type]
            report.raws.append(raw)
            report.line_nos.append(n)
    if first:
        report.errors.append("line 1: the file is empty (a header and its rows wanted)")
    return report


def _keep(report: CheckReport, keep: list[bool]) -> None:
    """Drop the rows a later rule rejected, keeping the three lists in step."""
    report.rows = [r for r, k in zip(report.rows, keep, strict=True) if k]
    report.raws = [r for r, k in zip(report.raws, keep, strict=True) if k]
    report.line_nos = [n for n, k in zip(report.line_nos, keep, strict=True) if k]


# --------------------------------------------------------------------------- #
# Fragment packs
# --------------------------------------------------------------------------- #


def line_id_errors(line_id: str) -> list[str]:
    """A line id not in this project's canonical form (SPECS §4.4)."""
    if LINE_ID.fullmatch(line_id):
        return []
    return [f"$.line_id: {_show(line_id)} is not a line id ('{{work}}:{{seq:04d}}:{{line:03d}}')"]


def fragment_row_errors(row: Mapping) -> list[str]:
    """The contract's rules for one row that the schema cannot state."""
    errors = line_id_errors(row["line_id"])
    m = LINE_ID.fullmatch(row["line_id"])
    if m and (row["page_id"], row["work_id"]) != (m["page"], m["work"]):
        errors.append(f"$.page_id/$.work_id: not the page and work of {_show(row['line_id'])}")
    cands = row["candidates"]
    ids = [c["cand_id"] for c in cands]
    if len(cands) != 2:
        errors.append(f"$.candidates: exactly 2 wanted, got {len(cands)}")
    if len(set(ids)) != len(ids):
        errors.append("$.candidates: the cand_ids repeat")
    texts = [" ".join(c["text"].split()) for c in cands]
    if len(set(texts)) != len(texts):
        errors.append("$.candidates: the texts are the same after whitespace normalisation")
    if row["license_bucket"] != "open":
        errors.append(f"$.license_bucket: must be 'open', got {_show(row['license_bucket'])}")
    gold = row["gold"]
    truth = gold.get("truth_cand_id")
    both_wrong = gold.get("both_wrong") is True
    if gold["is_gold"]:
        if (truth is not None) == both_wrong:
            errors.append(
                "$.gold: a gold row carries exactly one of truth_cand_id | both_wrong: true"
            )
        if truth is not None and truth not in ids:
            errors.append(f"$.gold.truth_cand_id: {_show(truth)} is not one of the candidates")
    elif truth is not None or both_wrong:
        errors.append("$.gold: is_gold is false but the row names a truth or both_wrong")
    image = row["image"]
    if image["delivery"] == "static" and "page_image_url" not in image:
        errors.append("$.image: a static image needs page_image_url")
    if image["delivery"] == "iiif" and "service_url" not in image:
        errors.append("$.image: an IIIF image needs service_url")
    longest = max((len(c["text"]) for c in cands), default=0)
    if row["n_chars"] != longest:
        errors.append(f"$.n_chars: {row['n_chars']}, but the longer candidate has {longest}")
    return errors


def check_fragment_pack(path: Path | str, schema: Mapping | None = None) -> CheckReport:
    """A fragment pack against the contract: the schema, then the row rules,
    then each fragment and each line once. ``counts`` tallies what passed."""
    schema = schema if schema is not None else load_schema(FRAGMENT_SCHEMA)
    report = _read_pack(path, "fragment", schema, FRAGMENT_HEADER)
    seen_fragments: dict[str, int] = {}
    seen_lines: dict[str, int] = {}
    keep: list[bool] = []
    for row, n in zip(report.rows, report.line_nos, strict=True):
        errs = fragment_row_errors(row)
        for e in errs:
            report.error(n, e)
        for key, seen in (("fragment_id", seen_fragments), ("line_id", seen_lines)):
            if row[key] in seen:
                report.error(n, f"{key} {_show(row[key])} again (first on line {seen[row[key]]})")
            else:
                seen[row[key]] = n
        keep.append(not errs)
        if errs:
            continue
        gold = row["gold"]
        report.counts["rows ok"] += 1
        report.counts[f"lang {row['lang']}"] += 1
        report.counts[f"stratum {row['stratum']}"] += 1
        report.counts[f"first {row['candidates'][0]['source']}"] += 1
        if gold["is_gold"]:
            report.counts["gold"] += 1
            report.counts["gold both_wrong" if gold.get("both_wrong") else "gold truth"] += 1
    _keep(report, keep)
    return report


# --------------------------------------------------------------------------- #
# Judgment packs
# --------------------------------------------------------------------------- #


def judgment_row_errors(row: Mapping) -> list[str]:
    """The contract's rules for one judgment the schema cannot state."""
    if bad := line_id_errors(row["line_id"]):
        return bad
    winner = [k for k in ("winning_cand_id", "winning_text", "winning_source") if k in row]
    if row["retirement"] == "converged":
        missing = [k for k in ("winning_cand_id", "winning_text") if k not in row]
        if missing:
            return [f"$: a converged row needs {', '.join(missing)}"]
        if not row["winning_text"].strip():
            return ["$.winning_text: empty"]
    elif winner:
        return [f"$: a both_rejected row names a winner ({', '.join(winner)})"]
    return []


def check_judgment_pack(path: Path | str, schema: Mapping | None = None) -> CheckReport:
    """A judgment pack against the contract; ``rows`` keeps the rows that pass,
    ``raws`` their lines as read (the import stores them verbatim)."""
    schema = schema if schema is not None else load_schema(JUDGMENT_SCHEMA)
    report = _read_pack(path, "judgment", schema, JUDGMENT_HEADER)
    keep: list[bool] = []
    for row, n in zip(report.rows, report.line_nos, strict=True):
        errs = judgment_row_errors(row)
        for e in errs:
            report.error(n, e)
        keep.append(not errs)
        if not errs:
            report.counts[row["retirement"]] += 1
    _keep(report, keep)
    return report


def report_lines(report: CheckReport, *, max_shown: int = MAX_SHOWN) -> list[str]:
    """The verdict as the command prints it."""
    head = report.header or {}
    if report.ok:
        c = report.counts
        out = [
            f"{report.path}: OK — {report.kind} pack, schema_version {head.get('schema_version')}, "
            f"pack_id {head.get('pack_id')}, built {head.get('built_at')}"
        ]
        if report.kind == "fragment":
            out.append(
                f"rows {len(report.rows):,}; gold {c['gold']:,} (truth {c['gold truth']:,}, "
                f"both wrong {c['gold both_wrong']:,}); license_bucket 'open' on every row"
            )
            for prefix in ("lang", "stratum", "first"):
                parts = [
                    f"{k.split(' ', 1)[1]} {v:,}"
                    for k, v in sorted(c.items())
                    if k.startswith(prefix + " ")
                ]
                label = "first candidate" if prefix == "first" else prefix
                out.append(f"{label}: " + " · ".join(parts))
        else:
            out.append(
                f"rows {len(report.rows):,}: converged {report.counts['converged']:,}, "
                f"both_rejected {report.counts['both_rejected']:,}"
            )
        return out
    out = [f"{report.path}: FAILED — {len(report.errors):,} error(s) in {report.n_rows:,} row(s)"]
    out += [f"  {e}" for e in report.errors[:max_shown]]
    if len(report.errors) > max_shown:
        out.append(f"  … and {len(report.errors) - max_shown:,} more")
    return out


__all__ = [
    "ANNOTATIONS",
    "FRAGMENT_HEADER",
    "FRAGMENT_SCHEMA",
    "JUDGMENT_HEADER",
    "JUDGMENT_SCHEMA",
    "KEYWORDS",
    "LINE_ID",
    "SCHEMA_VERSION",
    "CheckReport",
    "SchemaError",
    "assert_supported",
    "check_fragment_pack",
    "check_judgment_pack",
    "fragment_row_errors",
    "judgment_row_errors",
    "line_id_errors",
    "load_schema",
    "parse_line",
    "report_lines",
    "validate",
]
