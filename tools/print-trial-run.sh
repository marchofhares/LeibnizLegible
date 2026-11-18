#!/usr/bin/env bash
# The print trial's two kraken runs (M1 Task 1b, 2026-11-17), each under a
# memory-capped scope with the GPU guard, one torch process at a time:
#
#   tools/print-trial-run.sh zones   # the LADaS D-FINE region model over the 100 copies → data/print/zones/
#   tools/print-trial-run.sh ocr     # Gallicorpora+ over the PAGE XML of the printed-body lines → data/print/ocr/
#
# Environment: PRINT_ENV, PRINT_DEVICE (cuda:0), PRINT_PRECISION (32-true),
# PRINT_MEM (6G), PRINT_GPU_LIMIT (5900), PRINT_BATCH (25 pages a kraken process).
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
STAGE=${1:?zones|ocr}
ENV=${PRINT_ENV:-$ROOT/data/print/dfine-env}
MODELS=$ROOT/data/print/models
DEVICE=${PRINT_DEVICE:-cuda:0}
PRECISION=${PRINT_PRECISION:-32-true}
MEM=${PRINT_MEM:-6G}
GPU_LIMIT=${PRINT_GPU_LIMIT:-5900}
BATCH=${PRINT_BATCH:-25}
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR"
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
KRAKEN=$ENV/bin/kraken
[ -x "$KRAKEN" ] || { echo "no kraken at $KRAKEN: run tools/print-trial-env.sh"; exit 1; }

run_batches() {
  # $1 = input dir, $2 = input glob, $3 = output dir, $4 = output suffix, $5... = the kraken command tail
  local in_dir=$1 glob=$2 out_dir=$3 suffix=$4; shift 4
  mkdir -p "$out_dir"
  local files=() f out
  for f in "$in_dir"/$glob; do
    [ -e "$f" ] || continue
    out=$out_dir/$(basename "${f%.*}")$suffix
    [ -f "$out" ] || files+=("$f")
  done
  echo "== $(date -Is) $STAGE: $(ls "$in_dir"/$glob 2>/dev/null | wc -l) inputs, ${#files[@]} to do, device $DEVICE, precision $PRECISION, batch $BATCH"
  local k=0
  while [ $k -lt ${#files[@]} ]; do
    local pairs=() i
    for ((i = k; i < k + BATCH && i < ${#files[@]}; i++)); do
      f=${files[$i]}
      pairs+=(-i "$f" "$out_dir/$(basename "${f%.*}")$suffix")
    done
    bash "$ROOT/tools/gpu-guard.sh" "dfine-env/bin/[k]raken" "$GPU_LIMIT" "$LOGDIR/print-trial-$STAGE-gpu.csv" 2 2500 &
    local guard=$!
    local t0=$(date +%s)
    systemd-run --user --scope -p "MemoryMax=$MEM" --quiet bash -c '
      /usr/bin/time -v "$@" 2> >(sed "s/^/[time] /" >&2)
      rc=$?
      cg=$(cut -d: -f3 /proc/self/cgroup)
      [ -r "/sys/fs/cgroup$cg/memory.peak" ] && echo "[cgroup] memory.peak $(( $(cat /sys/fs/cgroup$cg/memory.peak) / 1048576 )) MiB"
      exit $rc' _ "$KRAKEN" "${pairs[@]}" "$@"
    local rc=$?
    sleep 3; kill "$guard" 2>/dev/null; wait "$guard" 2>/dev/null
    local n=0
    for ((i = k; i < k + BATCH && i < ${#files[@]}; i++)); do
      f=${files[$i]}; [ -f "$out_dir/$(basename "${f%.*}")$suffix" ] && n=$((n + 1))
    done
    echo "== $(date -Is) batch from $k: $n written, kraken exit $rc, $(( $(date +%s) - t0 )) s"
    k=$((k + BATCH))
  done
  echo "== $(date -Is) $STAGE done: $(ls "$out_dir"/*"$suffix" 2>/dev/null | wc -l) outputs in $out_dir"
}

case $STAGE in
  zones)
    # regions only: the D-FINE model emits SegmOnto regions; the lines are the store's v1 lines
    run_batches "$ROOT/data/print/images-2000" "*.jpg" "$ROOT/data/print/zones" ".xml" \
      -x --device "$DEVICE" --precision "$PRECISION" segment -bl -i "$MODELS/ladas_l.safetensors"
    ;;
  ocr)
    MODEL=$MODELS/Gallicorpora+_best.mlmodel
    [ -f "$MODELS/gallicorpora_plus.safetensors" ] && MODEL=$MODELS/gallicorpora_plus.safetensors
    run_batches "$ROOT/data/print/ocr-input" "*.xml" "$ROOT/data/print/ocr" ".xml" \
      -f page -x --device "$DEVICE" --precision "$PRECISION" ocr -m "$MODEL"
    ;;
  *) echo "unknown stage $STAGE"; exit 2 ;;
esac
