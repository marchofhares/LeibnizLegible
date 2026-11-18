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
and ``baselines`` resume page by page (the pages without an output). With
``--stage all`` every stage runs as a child interpreter in order.
"""

from __future__ import annotations

import argparse
import os
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


def run_stage(stage: str, a: argparse.Namespace) -> None:
    d = dirs(a.output)
    a.output.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if stage == "detect":
        from src.predictions.predict_choice import run_detection

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
        from src.rfdetr2kraken.kraken_segmentation_and_htr_v7 import kraken_cmd, segment_page

        if kraken_cmd is None:
            raise RuntimeError("kraken is not on PATH: put the venv's bin first")
        d["baselines"].mkdir(parents=True, exist_ok=True)
        region_files = sorted(d["regions"].glob("*_regions.xml"))
        todo = []
        for rx in region_files:
            stem = rx.name.removesuffix("_regions.xml")
            out = d["baselines"] / f"{stem}_baselines.xml"
            if a.force or not out.exists():
                todo.append((rx, out))
        log(
            f"baselines: {len(region_files)} region files, {len(region_files) - len(todo)} done, "
            f"{len(todo)} to do; device {a.device}, precision {a.precision}"
        )
        n_ok = n_err = 0
        for k, (rx, out) in enumerate(todo, start=1):
            t = time.time()
            try:
                segment_page(
                    regions_xml=rx,
                    output_xml=out,
                    images_dir=d["masked"],
                    device=a.device,
                    precision=a.precision,
                    htr_model=None,
                )
                n_ok += 1
                log(f"  {k}/{len(todo)} {out.name} in {time.time() - t:.1f} s")
            except Exception as exc:  # her batch loop prints and goes on; so does this
                n_err += 1
                log(f"  {k}/{len(todo)} {rx.name} FAILED: {exc}")
        log(f"baselines: {n_ok} written, {n_err} failed")
        if n_err and not n_ok:
            raise SystemExit(2)
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
