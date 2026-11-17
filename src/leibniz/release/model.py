"""The model package (REL1, deliverable D4 for the German reader).

``leibniz release model --weights DIR --card FILE --name NAME --out ROOT`` copies
a TrOCR checkpoint's inference files (config, generation config, weights,
processor and tokenizer files — never an optimizer state) into ``ROOT/NAME/``
with a README, a LICENSE and a ``MANIFEST.json`` (sizes and SHA-256), zips the
folder for Zenodo, and writes the record's deposit file beside it.

The README is K3's model card (``reports/kurrent/k3-model-card-trocr.md``)
brought to the finish: its numbers as K3 measured them, LT1's page-level table
beside them, the K4 run the model's readings are on the site under, the licence
as the registry decides it, the usage with transformers (with the decoder's
cache switched on, which the checkpoint's generation config leaves off), and the
statement on the precision of the training lines as the audit stands.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from leibniz import __version__, db, legal
from leibniz.release import cards as C
from leibniz.release import measured as M
from leibniz.release import state as S
from leibniz.web import attribution as attr

# The files a checkpoint is read from; anything else in the folder (optimizer and
# scheduler states, a trainer's log, a second copy of the weights) stays behind
# and is listed as left out.
WEIGHTS = "model.safetensors"
REQUIRED = ("config.json", WEIGHTS, "preprocessor_config.json")
OPTIONAL = (
    "generation_config.json",
    "processor_config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.json",
    "merges.txt",
    "special_tokens_map.json",
    "added_tokens.json",
    "sentencepiece.bpe.model",
    "k3-training.json",  # the training settings and the epoch (htr/train_trocr.py)
)
TOKENIZER_FILES = ("tokenizer.json", "vocab.json", "sentencepiece.bpe.model")
GENERATED = ("README.md", "LICENSE", "MANIFEST.json")

# The base model's licence text, as its repository states it (the LICENSE file of
# https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII, read 2026-11-17). MIT
# asks that the notice travel with copies and substantial portions.
BASE_MIT_NOTICE = """MIT License

Copyright (c) 2023 Digital Humanities Center, University of Bern

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
LICENCE_URLS = {
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/legalcode",
    "CC BY-NC 4.0": "https://creativecommons.org/licenses/by-nc/4.0/legalcode",
}

USAGE = """```python
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

repo = "{repo}"  # or the folder this README lies in
processor = TrOCRProcessor.from_pretrained(repo)
model = VisionEncoderDecoderModel.from_pretrained(repo).eval()

# one line of German Kurrent, cut from the page along its line polygon
line = Image.open("line.png").convert("RGB")
pixels = processor(images=[line], return_tensors="pt").pixel_values
out = model.generate(
    pixels,
    max_new_tokens=160,
    num_beams=1,
    do_sample=False,
    use_cache=True,  # see below
)
print(processor.batch_decode(out, skip_special_tokens=True)[0])
```"""


class ModelPackageError(RuntimeError):
    """The weights folder is not a checkpoint this command can package."""


@dataclass(slots=True)
class ModelPackage:
    name: str
    folder: Path
    zip_path: Path
    files: list[dict] = field(default_factory=list)  # path, bytes, sha256
    left_out: list[str] = field(default_factory=list)
    card_markers_missing: list[str] = field(default_factory=list)
    generated_at: str = ""

    @property
    def bytes(self) -> int:
        return sum(f["bytes"] for f in self.files)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def checkpoint_files(weights: Path) -> tuple[list[str], list[str]]:
    """``(files to copy, files left out)`` of a checkpoint folder; refuses a folder
    without the weights as safetensors, a config, a processor or a tokenizer."""
    weights = Path(weights)
    if not weights.is_dir():
        raise ModelPackageError(f"{weights} is not a folder")
    present = sorted(p.name for p in weights.iterdir() if p.is_file())
    missing = [n for n in REQUIRED if n not in present]
    if missing:
        raise ModelPackageError(f"{weights} lacks {', '.join(missing)}")
    if not any(n in present for n in TOKENIZER_FILES):
        raise ModelPackageError(f"{weights} holds no tokenizer file ({', '.join(TOKENIZER_FILES)})")
    wanted = [n for n in (*REQUIRED, *OPTIONAL) if n in present]
    left = [n for n in present if n not in wanted]
    left += sorted(p.name + "/" for p in weights.iterdir() if p.is_dir())
    return wanted, left


def licence_text(model_licence: str, name: str) -> str:
    """The package's LICENSE file: the model's licence by name with the address of
    its legal code and the attribution it asks for, and the base model's MIT
    notice in full."""
    bare = C.bare_licence(model_licence)
    url = LICENCE_URLS.get(bare, "")
    base = legal.artifact("trocr-kurrent-xvi-xvii")
    return (
        f"{name}\n"
        f"{'=' * len(name)}\n\n"
        f"The weights and the files beside them in this folder are licensed under the\n"
        f"Creative Commons licence {bare} (SPDX: {C.licence_id(model_licence)}).\n"
        f"The legal code: {url}\n\n"
        f"Attribution: {attr.PROJECT_NAME} ({attr.PROJECT_URL}), the Kurrent reader\n"
        f"{legal.READER_DE_VERSION}, fine-tuned from {base.name}.\n\n"
        "Why this licence, as the project's licence registry records it\n"
        "(src/leibniz/legal.py, `leibniz legal outputs`):\n"
        f"{legal.output('model-k3-trocr').why}.\n\n"
        "The scans the training lines were cut from are the Gottfried Wilhelm Leibniz\n"
        "Bibliothek's, under the Public Domain Mark 1.0; the lines' text is the reading\n"
        "text of Akademie-Ausgabe volumes whose §70 term has run out.\n\n"
        "-----------------------------------------------------------------------------\n"
        f"The base model, {base.name}\n"
        f"({base.source}), is published under the MIT License;\n"
        "its notice, as its repository states it:\n\n"
        f"{BASE_MIT_NOTICE}"
    )


def model_front_matter(model_licence: str) -> str:
    base = legal.artifact("trocr-kurrent-xvi-xvii").source.removeprefix("https://huggingface.co/")
    return "\n".join(
        [
            "---",
            f"license: {C.licence_id(model_licence)}",
            "language:",
            "- de",
            "library_name: transformers",
            "pipeline_tag: image-to-text",
            f"base_model: {base}",
            "tags:",
            *[
                f"- {t}"
                for t in ("trocr", "htr", "handwritten-text-recognition", "kurrent", "leibniz")
            ],
            "metrics:",
            "- cer",
            "---",
            "",
        ]
    )


# The lines of K3's card this module rewrites, by how they begin.
_TITLE = "# Model card"
_PRECISION = "- **Precision of the training lines"
_LICENCE = "- **Licence of this model"


def finish_card(
    k3_card: str,
    *,
    name: str,
    release: dict | None = None,
    measured: M.Measured | None = None,
    generated_at: str = "",
) -> tuple[str, list[str]]:
    """K3's card brought to the finish; returns the README and the markers of the
    K3 card that were not found (a card that changed shape still yields a full
    README: the finished statements are then added under their own headings)."""
    m = measured if measured is not None else M.load_measured()
    licence = legal.output("model-k3-trocr").licence
    bare = C.bare_licence(licence)
    de = legal.site_readers()["de"]
    dois = S.dois(release)
    own = dois.get("model")
    repo = C.hf_repo("model", release) or name
    precision = (
        "- **Precision of the training lines: unmeasured until the audit is scored.** No "
        "verdict existed when this model was trained. " + C.k2_audit_note() + " The lines "
        "the Edition judged were never trained on."
    )
    nc_channels = [
        legal.artifact(k)
        for k in legal.output("model-k3-trocr").inputs
        if legal.artifact(k).deposit == "nc"
    ]
    licence_line = (
        f"- **Licence of this model:** {bare}. {legal.output('model-k3-trocr').why} "
        "(the licence registry, `src/leibniz/legal.py`). Its readings on the site and in "
        f"`leibniz-transcriptions` carry {de['readings_licence']}."
    )
    if nc_channels:
        licence_line += (
            ' To be plain about what "no NC input" means: the training lines\' text is '
            "reading text of Akademie-Ausgabe volumes whose §70 term has run out, which the "
            "project's scheme counts as open whatever copy it was read from; part of it was "
            "read from files whose publishers state non-commercial terms ("
            + "; ".join(a.name for a in nc_channels)
            + "), and those lines are published in the NC-derived deposit `leibniz-gt-nc` "
            "under CC BY-NC 4.0. Whether non-commercial terms on a file reach reading text "
            "free of §70 is a question in the project's lawyer memo "
            "(`reports/release-checklist.md` §6), not a position taken here."
        )
    found = {_TITLE: False, _PRECISION: False, _LICENCE: False}
    body: list[str] = []
    for line in k3_card.splitlines():
        if line.startswith(_TITLE) and not found[_TITLE]:
            found[_TITLE] = True
            body.append(f"# {name} — a Kurrent reader for Leibniz's German papers")
            body.append("")
            body.append(
                f"_`{legal.READER_DE_VERSION}` (K3's TrOCR model, `{de['reader']}`), packaged "
                f"{generated_at[:10]} by `leibniz release model`. "
                + (f"DOI: {C.doi_link(own)}._" if own else "DOI: to be assigned at deposit._")
            )
        elif line.startswith(_PRECISION) and not found[_PRECISION]:
            found[_PRECISION] = True
            body.append(precision)
        elif line.startswith(_LICENCE) and not found[_LICENCE]:
            found[_LICENCE] = True
            body.append(licence_line)
        else:
            body.append(line)
    missing = [k for k, v in found.items() if not v]
    extra: list[str] = []
    if _TITLE in missing:
        body.insert(0, f"# {name} — a Kurrent reader for Leibniz's German papers\n")
    if _PRECISION in missing or _LICENCE in missing:
        extra += ["", "## Data statement, brought up to date", ""]
        if _PRECISION in missing:
            extra.append(precision)
        if _LICENCE in missing:
            extra.append(licence_line)
    extra += ["", *_page_test_section(m), *_site_section(m), *_usage_section(repo)]
    extra += [
        "## Use with care",
        "",
        "**Machine output — do not ingest as verified text.** What this model writes is a "
        "machine's reading of a line"
        + (
            f", with a character error rate of {m.reader.pool} on Leibniz's German letters "
            f"({m.reader.pool_leibniz} in his own hand)"
            if m.reader is not None and m.reader.pool.cer is not None
            else ""
        )
        + "; label it as such wherever it goes, keep the model's name and version with the "
        'text, and say "the machine reads it as …", never "Leibniz wrote". Nothing this '
        "model produces is an edition of Leibniz.",
        "",
        "## Where this lives",
        "",
        (
            f"- This record: doi:{C.doi_link(own)} (Zenodo, community `{C.ZENODO_COMMUNITY}`)."
            if own
            else "- This record: Zenodo, DOI to be assigned at deposit."
        ),
    ]
    if C.hf_repo("model", release):
        extra.append(f"- Mirror: https://huggingface.co/{C.hf_repo('model', release)}.")
    if dois.get("transcriptions"):
        extra.append(
            f"- Its readings: `leibniz-transcriptions`, doi:{C.doi_link(dois['transcriptions'])}."
        )
    gt = [
        f"`leibniz-{key}` (doi:{C.doi_link(dois[key])})" for key in ("gt", "gt-nc") if dois.get(key)
    ]
    if gt:
        extra.append(
            "- Its training lines are among the ground truth, by the channel their text came "
            "through: " + " and ".join(gt) + "."
        )
    extra += [
        f"- Code: {attr.PROJECT_URL} (Apache-2.0; `src/leibniz/htr/train_trocr.py`, "
        "`src/leibniz/htr/trocr.py`); the reports: `reports/kurrent/k3-eval.md`, "
        "`reports/htr/page-llm.md`.",
        "",
        "## Citation",
        "",
        f"{attr.PROJECT_NAME} ({generated_at[:4]}). {name} ({legal.READER_DE_VERSION}; "
        f"version {generated_at[:10]}). "
        + (f"https://doi.org/{own}. " if own else f"{attr.PROJECT_URL}. ")
        + f"Licensed {bare}.",
        "",
        "Files, sizes and SHA-256 checksums are listed in `MANIFEST.json`.",
        "",
    ]
    return model_front_matter(licence) + "\n".join(body).rstrip() + "\n" + "\n".join(extra), missing


def _page_test_section(m: M.Measured) -> list[str]:
    pt = m.page_test
    if pt is None or not pt.rows:
        return [
            "## Against whole-page reading by frontier vision models (LT1)",
            "",
            "See `reports/htr/page-llm.md`.",
            "",
        ]
    return [
        "## Against whole-page reading by frontier vision models (LT1)",
        "",
        f"The table above is K3's (the whole pool, {m.reader.pool_letters if m.reader else '134'} "
        f"letters). LT1 ({pt.date}) put the model beside frontier vision models reading whole "
        f"pages, on {pt.letters} letters ({pt.pages} pages) of the same pool with the same "
        "metric, a failed page charged as wholly wrong; character error rate with its 95 % "
        "interval over letters (`reports/htr/page-llm.md`):",
        "",
        "| reader | these letters | Leibniz's hand | the correspondents' hands |",
        "| --- | ---: | ---: | ---: |",
        *[f"| {label} | {a.with_interval} | {b} | {c} |" for label, a, b, c in pt.rows],
        "",
        "The readers stand inside each other's intervals: parity on Leibniz's own hand, "
        "the page models ahead on the correspondents' cleaner hands, and their errors differ "
        "from this model's — a second reader, not a replacement. The sets are small; the "
        "letters are checked transcriptions of 1708–1716, not a random sample of the German "
        "pages.",
        "",
    ]


def _site_section(m: M.Measured) -> list[str]:
    cov = m.coverage
    head = ["## On the site (K4)", ""]
    if cov is None or not cov.run_id:
        return [
            *head,
            f"On https://leibnizlegible.com the German pages are read by this model "
            f"(`{legal.READER_DE_VERSION}`); see `reports/kurrent/k4-reading.md`.",
            "",
        ]
    return [
        *head,
        f"On https://leibnizlegible.com and in `leibniz-transcriptions` this model's readings "
        f"are run {cov.run_id} (`{cov.model}`, scoped to German pages): {cov.rows_written:,} "
        f"lines on {cov.pages_read:,} pages the language pass called German, read greedy "
        f"with the decoder's cache {'on' if cov.use_cache else 'as the checkpoint sets it'}, "
        f"at most {cov.max_new_tokens} new tokens, batch {cov.batch_size}, `{cov.dtype}` (the "
        "settings of the usage below)"
        + (f", at {cov.ms_per_line:.0f} ms a line in that job" if cov.ms_per_line else "")
        + ". The pass finds about three quarters of "
        f"the German pages by the census's measure (precision {M.pct(cov.precision)}, recall "
        f"{M.pct(cov.recall)}); a German page it missed is still read by the Latin/French "
        "model, and the annotated printed books were left to that model "
        "(`reports/kurrent/k4-reading.md`).",
        "",
    ]


def _usage_section(repo: str) -> list[str]:
    return [
        "## Usage",
        "",
        USAGE.format(repo=repo),
        "",
        "`use_cache=True` matters. The checkpoint's generation config comes from the base "
        "model and switches the decoder's key/value cache off, so without the argument every "
        "decoding step reads the whole prefix again: the same text, much more slowly. The "
        "numbers on this card and the readings on the site were made greedy (`num_beams=1`) "
        "with the cache on. The model reads one line at a time and knows nothing of the "
        "page: cut the lines first (the site's lines come from the PHILIUMM segmentation "
        f"model, doi:{attr.PHILIUMM_SEG_DOI}).",
        "",
    ]


def model_description_html(name: str, package_bytes: int) -> str:
    """The Zenodo description of the model record, from the card's own sentences."""
    de = legal.site_readers()["de"]
    bare = C.bare_licence(legal.output("model-k3-trocr").licence)
    r = M.load_reader()
    numbers = (
        f" On a frozen pool of {r.pool_letters} German letters of 1708–1716 its character "
        f"error rate is {r.pool} (95 % CI {M.interval(r.pool.lo, r.pool.hi)}), in Leibniz's "
        f"own hand {r.pool_leibniz}; on its validation set {M.pct(r.validation.cer, 2)}."
        if r is not None and r.pool.cer is not None
        else ""
    )
    parts = [
        f"`{name}` (`{legal.READER_DE_VERSION}`): a TrOCR model that reads German Kurrent of "
        f"Leibniz's papers line by line, fine-tuned from {de['base']} ({de['base_licence']}) "
        "on edition text of his German pieces placed on the GWLB's scans. It reads the "
        f"German pages of https://leibnizlegible.com.{numbers}",
        f"**Licence: {bare}.** {legal.output('model-k3-trocr').why}.",
        f"The record holds `{name}.zip` ({package_bytes:,} bytes unpacked: the weights as "
        "safetensors, the configs, the processor and tokenizer files, `LICENSE`, "
        "`MANIFEST.json` with SHA-256 checksums) and the card, `README.md`, with the data "
        "statement, the error rates and what they were measured on, and the usage.",
        "**Machine output — do not ingest as verified text.** What this model writes is a "
        "machine's reading, to be labelled as such; it is not an edition of Leibniz.",
    ]
    return "\n".join(f"<p>{C.md_inline(p)}</p>" for p in parts)


def build_package(
    weights: Path,
    card: Path,
    name: str,
    out_root: Path,
    *,
    release: dict | None = None,
    zip_it: bool = True,
) -> ModelPackage:
    """Copy the checkpoint's files into ``out_root/name``, write README, LICENSE and
    MANIFEST.json, zip the folder as ``out_root/name.zip`` and write the record's
    deposit file ``out_root/name.zenodo.json``."""
    weights, card, out_root = Path(weights), Path(card), Path(out_root)
    if not card.is_file():
        raise ModelPackageError(f"the card {card} is not a file")
    wanted, left = checkpoint_files(weights)
    if release is None:
        release = S.load_release(out_root)
    if release.get("model_name") not in (None, name):
        raise ModelPackageError(
            f"this release folder names its model {release['model_name']!r}, not {name!r}"
        )
    release["model_name"] = name
    folder = out_root / name
    folder.mkdir(parents=True, exist_ok=True)
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    pkg = ModelPackage(name, folder, out_root / f"{name}.zip", left_out=left)
    pkg.generated_at = generated_at
    for fname in wanted:
        shutil.copy2(weights / fname, folder / fname)
    readme, missing = finish_card(
        card.read_text(encoding="utf-8"), name=name, release=release, generated_at=generated_at
    )
    pkg.card_markers_missing = missing
    licence = legal.output("model-k3-trocr").licence
    (folder / "README.md").write_text(readme, encoding="utf-8")
    (folder / "LICENSE").write_text(licence_text(licence, name), encoding="utf-8")
    for fname in (*wanted, "LICENSE"):
        path = folder / fname
        pkg.files.append({"path": fname, "bytes": path.stat().st_size, "sha256": _sha256(path)})
    manifest = {
        "model": name,
        "reader": legal.READER_DE_VERSION,
        "base_model": legal.artifact("trocr-kurrent-xvi-xvii").source,
        "licence": C.bare_licence(licence),
        "generated_at": generated_at,
        "generator": f"leibniz-legible {__version__} (leibniz release model)",
        "git_sha": db.git_sha(),
        "card": str(card),
        "files": pkg.files,
        "left_out": left,
    }
    (folder / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if zip_it:
        write_zip(folder, pkg.zip_path, [*wanted, *GENERATED])
    record = C.zenodo_record(
        "model",
        title=f"{attr.PROJECT_NAME}: {name} — a Kurrent reader for Leibniz's German papers",
        description=model_description_html(name, pkg.bytes),
        licence=licence,
        version=generated_at[:10],
        folder=name,
        files=[
            {"name": "README.md", "path": f"{name}/README.md"},
            {"name": "LICENSE", "path": f"{name}/LICENSE"},
            {"name": "MANIFEST.json", "path": f"{name}/MANIFEST.json"},
            *([{"name": f"{name}.zip", "path": f"{name}.zip"}] if zip_it else []),
        ],
        release=release,
        upload_type="other",  # the deposit API has no "model"; set it in the browser
    )
    C.zenodo_path(out_root, "model", release).write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    S.save_release(out_root, release)
    return pkg


def write_zip(folder: Path, zip_path: Path, names: list[str]) -> None:
    """The package as one zip for Zenodo: the weights stored as they are (floats do
    not compress), the text files deflated; written beside the folder, atomically."""
    tmp = zip_path.with_name(zip_path.name + ".part")
    with zipfile.ZipFile(tmp, "w", allowZip64=True) as z:
        for fname in names:
            path = folder / fname
            method = zipfile.ZIP_STORED if fname == WEIGHTS else zipfile.ZIP_DEFLATED
            z.write(path, arcname=f"{folder.name}/{fname}", compress_type=method)
    tmp.replace(zip_path)


__all__ = [
    "BASE_MIT_NOTICE",
    "OPTIONAL",
    "REQUIRED",
    "USAGE",
    "ModelPackage",
    "ModelPackageError",
    "build_package",
    "checkpoint_files",
    "finish_card",
    "licence_text",
    "model_description_html",
    "model_front_matter",
    "write_zip",
]
