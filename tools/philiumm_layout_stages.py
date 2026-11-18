#!/usr/bin/env python
"""Run PHILIUMM's layout pipeline one stage at a time, each stage its own
process (P1 Task 3, 2026-11-17).

``main_pipeline.py`` of her repository runs the ten steps in one process,
so the RF-DETR model and its CUDA context stay in memory while the kraken
subprocesses of step 6 run. On the 9.9 GB desktop one torch process lives at
a time: this driver calls her step functions with her arguments, one stage
per interpreter. Her kraken command names the baseline model by a path
relative to the working directory, so the driver runs in ``--runtime`` (a
folder holding ``models/segmentation/baselines/best_0.4750.safetensors``;
by default her repository's root) while her modules are imported from
``--pipeline``. Nothing of hers is modified or copied into this repository.

    python tools/philiumm_layout_stages.py --pipeline data/philiumm/rfdetr-pipeline \
        --input IMAGES --output RESULTS --config data/philiumm/config_v2_ema.json \
        --stage detect|regions|masks|binarize|masked|baselines|merge|simplify|
                fix-regions|fix-lines|all
        [--device cuda:0] [--precision 32-true|bf16-mixed] [--force] [--retry N]

Stages skip when their outputs exist, as her ``should_skip`` does; ``detect``
and ``baselines`` resume page by page (the pages without an output). The
``baselines`` stage runs her kraken command once per batch of pages
(``--batch``) instead of once a page, and again on the CPU for the pages the
card could not take. With ``--stage all`` every stage runs as a child
interpreter in order.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

STAGES = (
    "detect",
    "regions",
    "masks",
    "binarize",
    "masked",
    "baselines",
    "merge",
    "simplify",
    "fix-regions",
    "fix-lines",
)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def dirs(output: Path) -> dict[str, Path]:
    # her build_pipeline_dirs, repeated so the names stay hers
    return {
        "predictions": output / "01_predictions_json",
        "predictions_rfdetr": output / "01_predictions_json" / "rf-detr",
        "predictions_maths": output / "01_predictions_json" / "maths",
        "annotated": output / "02_annotated_images",
        "regions": output / "03_regions_xml",
        "masks": output / "04_masks",
        "binarized": output / "05_binarized",
        "masked": output / "05b_masked_for_baselines",
        "baselines": output / "06_baselines_and_htr",
        "merged": output / "07_merged_xml",
        "simplified_polygons": output / "08_simplified_pagexml",
        "fixed_regions": output / "09_fixed_region_overlaps",
        "fixed_lines": output / "10_fixed_lines",
    }


def has_outputs(d: Path) -> bool:
    return d.exists() and any(d.iterdir())


def images_in(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXT)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _release_cuda_cache_after_each_prediction() -> None:
    """Wrap rfdetr's ``predict`` so the CUDA caching allocator gives its blocks
    back after every page. The pages differ in shape, so the cache of one
    long process grows page by page; on the 6 GB card it met the guard's limit
    after eight pages of 2,000 px, while one page reserves 2.5 GB. A wrapper
    around a library call, nothing of hers changed."""
    try:
        import torch
        from rfdetr.detr import RFDETR
    except ImportError:
        return
    original = RFDETR.predict

    def predict(self, *args, **kwargs):
        try:
            return original(self, *args, **kwargs)
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    RFDETR.predict = predict


def _kraken_batch(
    pairs: list[tuple[Path, Path]], *, device: str, precision: str, kraken_cmd: str
) -> int:
    """Her kraken command (``kraken_segmentation_and_htr_v7.segment_page``),
    with every page of the batch as one ``-i in out`` pair, so the model
    loads once: the same flags, model path and text direction, one process
    instead of one a page (the operator's change 4 of 2026-11-17). Returns
    the exit status; kraken goes on past a page that fails and reports it."""
    cmd = [kraken_cmd]
    for src, dst in pairs:
        cmd += ["-i", str(src), str(dst)]
    cmd += [
        "-f",
        "page",
        "-x",
        "--device",
        device,
        "--precision",
        precision,
        "segment",
        "-bl",
        "-d",
        "horizontal-lr",
        "--remove-hlines",
        "-i",
        "models/segmentation/baselines/best_0.4750.safetensors",
    ]
    log(f"kraken on {len(pairs)} pages, device {device}, precision {precision}")
    proc = subprocess.Popen(cmd)

    def _stop(signum, _frame):  # a SIGTERM to the driver ends kraken too
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise SystemExit(128 + signum)

    previous = signal.signal(signal.SIGTERM, _stop)
    try:
        return proc.wait()
    finally:
        signal.signal(signal.SIGTERM, previous)


def run_baselines(a: argparse.Namespace, d: dict[str, Path]) -> None:
    """Her step 6 over all pages: kraken once per batch on the GPU, the pages
    it fails (or that stopped a batch) again on the CPU, resumable page by
    page. ``_baselines_state.json`` in the output folder remembers which
    pages were in a batch that did not finish, so a page that kills a batch
    (the card spilt) goes to the CPU the next time instead of killing it
    again."""
    import json

    from src.rfdetr2kraken.kraken_segmentation_and_htr_v7 import (
        kraken_cmd,
        patch_input_xml,
        strip_imgfilename_to_basename,
        strip_space_xmlpage,
    )

    if kraken_cmd is None:
        raise RuntimeError("kraken is not on PATH: put the venv's bin first")
    d["baselines"].mkdir(parents=True, exist_ok=True)
    state_path = d["baselines"] / "_baselines_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    culprits = set(state.get("culprits", []))
    failed_cpu = set(state.get("failed_cpu", []))
    # a batch that did not finish: its first page without an output stopped it
    for stems in state.get("open_batches", []):
        for stem in stems:
            if not (d["baselines"] / f"{stem}_baselines.xml").exists():
                culprits.add(stem)
                break
    state["open_batches"] = []

    def save() -> None:
        state["culprits"] = sorted(culprits)
        state["failed_cpu"] = sorted(failed_cpu)
        state_path.write_text(json.dumps(state, indent=1))

    region_files = sorted(d["regions"].glob("*_regions.xml"))
    todo = []
    for rx in region_files:
        stem = rx.name.removesuffix("_regions.xml")
        out = d["baselines"] / f"{stem}_baselines.xml"
        if (a.force or not out.exists()) and stem not in failed_cpu:
            todo.append((stem, rx, out))

    # the baseline model rescales every page to 1,800 px high, so a wide page
    # becomes a wide network input: at a width-to-height ratio of 3.4 kraken
    # took 5.3 GB of the 6 GB card (measured 2026-11-17); pages above the
    # ratio go to the CPU from the start
    def wide(stem: str) -> bool:
        img = d["masked"] / f"{stem}.jpg"
        try:
            from PIL import Image

            with Image.open(img) as im:
                w, h = im.size
        except Exception:
            return False
        return h > 0 and w / h > a.wide_ratio

    for stem, _, _ in todo:
        if stem not in culprits and wide(stem):
            culprits.add(stem)
            state.setdefault("wide", []).append(stem)
    gpu = [t for t in todo if t[0] not in culprits] if a.device != "cpu" else []
    cpu = [t for t in todo if t[0] in culprits] if a.device != "cpu" else todo
    log(
        f"baselines: {len(region_files)} region files, {len(region_files) - len(todo)} done, "
        f"{len(gpu)} for {a.device} ({a.precision}), {len(cpu)} for the cpu, "
        f"{len(failed_cpu)} failed before; batch {a.batch}"
    )

    def run(items, device: str, precision: str) -> list[str]:
        """Run the items in batches; return the stems without an output."""
        missing: list[str] = []
        for k in range(0, len(items), a.batch):
            chunk = items[k : k + a.batch]
            state["open_batches"] = [[stem for stem, _, _ in chunk]]
            save()
            tmp_pairs = [(patch_input_xml(rx, d["masked"]), out) for _, rx, out in chunk]
            t = time.time()
            try:
                rc = _kraken_batch(
                    tmp_pairs, device=device, precision=precision, kraken_cmd=kraken_cmd
                )
            finally:
                for tmp, _ in tmp_pairs:
                    tmp.unlink(missing_ok=True)
            state["open_batches"] = []
            n_ok = 0
            for stem, _, out in chunk:
                if out.exists():
                    strip_imgfilename_to_basename(out)
                    strip_space_xmlpage(out)
                    n_ok += 1
                else:
                    missing.append(stem)
            save()
            took = time.time() - t
            log(
                f"  batch {k // a.batch + 1}: {n_ok}/{len(chunk)} written in {took:.0f} s"
                f" (kraken exit {rc}; {took / max(1, len(chunk)):.1f} s a page)"
            )
        return missing

    missing_gpu = run(gpu, a.device, a.precision) if gpu else []
    culprits.update(missing_gpu)
    cpu_items = cpu + [t for t in gpu if t[0] in missing_gpu]
    if cpu_items:
        log(f"baselines: {len(cpu_items)} pages on the cpu (32-true)")
        failed_cpu.update(run(cpu_items, "cpu", "32-true"))
    save()
    done = sum(
        1
        for rx in region_files
        if (d["baselines"] / (rx.name.removesuffix("_regions.xml") + "_baselines.xml")).exists()
    )
    log(
        f"baselines: {done} of {len(region_files)} written; culprits (cpu next time) "
        f"{len(culprits)}; failed on the cpu too {len(failed_cpu)}"
    )
    if not done:
        raise SystemExit(2)


def run_stage(stage: str, a: argparse.Namespace) -> None:
    d = dirs(a.output)
    a.output.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if stage == "detect":
        from src.predictions.predict_choice import run_detection

        _release_cuda_cache_after_each_prediction()
        d["predictions_rfdetr"].mkdir(parents=True, exist_ok=True)
        done = {p.stem for p in d["predictions_rfdetr"].glob("*.json")}
        images = images_in(a.input)
        todo = images if a.force else [p for p in images if p.stem not in done]
        log(f"detect: {len(images)} images, {len(images) - len(todo)} done, {len(todo)} to do")
        if todo:
            if len(todo) == len(images):
                src_dir = a.input
            else:  # resume: her function reads a folder, so give it the rest as links
                src_dir = a.output / "_detect_todo"
                if src_dir.exists():
                    for p in src_dir.iterdir():
                        p.unlink()
                src_dir.mkdir(parents=True, exist_ok=True)
                for p in todo:
                    (src_dir / p.name).symlink_to(p.resolve())
            run_detection(
                input_dir=src_dir,
                json_dir=d["predictions_rfdetr"],
                annotated_dir=d["annotated"],
                config_path=a.config,
            )
            if src_dir != a.input:
                for p in src_dir.iterdir():
                    p.unlink()
                src_dir.rmdir()
    elif stage == "regions":
        from src.rfdetr2kraken.create_pagexml_regions_from_json import run_json_to_regions_xml

        if a.force or not has_outputs(d["regions"]):
            run_json_to_regions_xml(json_dir=d["predictions_rfdetr"], xml_dir=d["regions"])
        else:
            log("regions: outputs present, skipped")
    elif stage == "masks":
        from main_pipeline import ALLOWED_ZONES, EXCLUDED_MATH_ZONES
        from src.rfdetr2kraken.create_mask_png import run_masks_from_zones

        if a.force or not has_outputs(d["masks"]):
            run_masks_from_zones(
                json_dir=d["predictions_rfdetr"],
                math_json_dir=d["predictions_maths"],
                mask_dir=d["masks"],
                allowed=ALLOWED_ZONES,
                exclude=EXCLUDED_MATH_ZONES,
            )
        else:
            log("masks: outputs present, skipped")
    elif stage == "binarize":
        from src.rfdetr2kraken.binarize_images import run_binarization

        if a.force or not has_outputs(d["binarized"]):
            run_binarization(input_dir=a.input, output_dir=d["binarized"])
        else:
            log("binarize: outputs present, skipped")
    elif stage == "masked":
        from src.rfdetr2kraken.create_masked_images import run_masked_images

        if a.force or not has_outputs(d["masked"]):
            run_masked_images(
                images_dir=d["binarized"], masks_dir=d["masks"], output_dir=d["masked"]
            )
        else:
            log("masked: outputs present, skipped")
    elif stage == "baselines":
        run_baselines(a, d)
    elif stage == "merge":
        from src.rfdetr2kraken.merge_kraken_lines_back_into_my_regions import (
            merge_zone_types_and_lines_batch,
        )

        if a.force or not has_outputs(d["merged"]):
            merge_zone_types_and_lines_batch(
                regions_dir=d["regions"], baselines_dir=d["baselines"], output_dir=d["merged"]
            )
        else:
            log("merge: outputs present, skipped")
    elif stage == "simplify":
        from src.rfdetr2kraken.simplify_zones_polygons_xml import simplify_polygons_batch

        if a.force or not has_outputs(d["simplified_polygons"]):
            simplify_polygons_batch(
                input_dir=d["merged"], output_dir=d["simplified_polygons"], tolerance=15
            )
        else:
            log("simplify: outputs present, skipped")
    elif stage == "fix-regions":
        from src.postprocessing.fix_region_overlaps import fix_overlaps_batch

        if a.force or not has_outputs(d["fixed_regions"]):
            fix_overlaps_batch(input_dir=d["simplified_polygons"], output_dir=d["fixed_regions"])
        else:
            log("fix-regions: outputs present, skipped")
    elif stage == "fix-lines":
        from src.postprocessing.fix_lines_spanning_over_multiple_regions import fix_lines_batch

        if a.force or not has_outputs(d["fixed_lines"]):
            fix_lines_batch(input_dir=d["fixed_regions"], output_dir=d["fixed_lines"])
        else:
            log("fix-lines: outputs present, skipped")
    else:
        raise SystemExit(f"unknown stage {stage}")
    log(f"stage {stage} done in {time.time() - t0:.1f} s")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--pipeline", type=Path, required=True, help="her repository's root")
    ap.add_argument(
        "--runtime",
        type=Path,
        default=None,
        help="the working directory (its models/ tree is what her relative paths name); "
        "default: --pipeline",
    )
    ap.add_argument("--input", type=Path, required=True, help="the folder of page images")
    ap.add_argument("--output", type=Path, required=True, help="the results folder")
    ap.add_argument(
        "--config",
        type=Path,
        required=True,
        help="the local config (model path, resolution, threshold)",
    )
    ap.add_argument("--stage", choices=STAGES + ("all",), required=True)
    ap.add_argument("--device", default="cuda:0", help="kraken's device for the baselines stage")
    ap.add_argument(
        "--precision", default="32-true", help="kraken's precision for the baselines stage"
    )
    ap.add_argument("--force", action="store_true", help="redo a stage whose outputs exist")
    ap.add_argument(
        "--batch", type=int, default=25, help="pages per kraken process in the baselines stage"
    )
    ap.add_argument(
        "--wide-ratio",
        type=float,
        default=2.0,
        help="a page wider than this many times its height goes to the CPU in the baselines stage",
    )
    ap.add_argument(
        "--retry",
        type=int,
        default=0,
        help="with --stage all: relaunch a failed stage this many times",
    )
    a = ap.parse_args()
    a.pipeline = a.pipeline.resolve()
    a.input, a.output, a.config = a.input.resolve(), a.output.resolve(), a.config.resolve()
    a.runtime = (a.runtime or a.pipeline).resolve()
    if a.stage == "all":
        for stage in STAGES:
            attempt = 0
            while True:
                cmd = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--pipeline",
                    str(a.pipeline),
                    "--input",
                    str(a.input),
                    "--output",
                    str(a.output),
                    "--config",
                    str(a.config),
                    "--stage",
                    stage,
                    "--runtime",
                    str(a.runtime),
                    "--batch",
                    str(a.batch),
                    "--wide-ratio",
                    str(a.wide_ratio),
                    "--device",
                    a.device,
                    "--precision",
                    a.precision,
                ] + (["--force"] if a.force else [])
                log(f"== stage {stage} (attempt {attempt + 1})")
                rc = subprocess.call(cmd)
                if rc == 0:
                    break
                attempt += 1
                if attempt > a.retry:
                    raise SystemExit(f"stage {stage} failed with exit {rc}")
                log(f"stage {stage} exit {rc}; relaunch in 60 s")
                time.sleep(60)
        log("all stages done")
        return
    os.chdir(a.runtime)  # her relative model path resolves here
    sys.path.insert(0, str(a.pipeline))
    run_stage(a.stage, a)


if __name__ == "__main__":
    main()
