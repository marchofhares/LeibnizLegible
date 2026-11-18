#!/usr/bin/env bash
# Run PHILIUMM's layout pipeline on a folder of page images, stage by stage
# (P1 Task 3, 2026-11-17): every stage its own process under a memory-capped
# systemd scope, the two torch stages (detect, baselines) with the GPU guard
# sampling the card, every stage's wall time and peak memory in the log.
#
#   tools/philiumm-layout-run.sh IMAGES RESULTS [LOG-NAME] [stage ...]
#
# Environment: LAYOUT_ENV (the venv), LAYOUT_PIPELINE (her clone),
# LAYOUT_RUNTIME (the working directory with the model files on the VHD),
# LAYOUT_CONFIG (the config), LAYOUT_MEM (MemoryMax, default 6G),
# LAYOUT_DEVICE (cuda:0), LAYOUT_PRECISION (32-true), LAYOUT_GPU_LIMIT (MiB,
# default 5900), LAYOUT_RETRY (relaunches of a failed stage, default 3).
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
IMAGES=${1:?images folder}
RESULTS=${2:?results folder}
NAME=${3:-philiumm-layout-run}
shift 3 2>/dev/null || shift $#
STAGES=("$@")
[ ${#STAGES[@]} -eq 0 ] && STAGES=(detect regions masks binarize masked baselines merge simplify fix-regions fix-lines)
ENV=${LAYOUT_ENV:-$ROOT/data/philiumm/rfdetr-env}
PIPE=${LAYOUT_PIPELINE:-$ROOT/data/philiumm/rfdetr-pipeline}
RUNTIME=${LAYOUT_RUNTIME:-$ROOT/data/philiumm/rfdetr-runtime}
[ -d "$RUNTIME" ] || RUNTIME=$PIPE
CONFIG=${LAYOUT_CONFIG:-$ROOT/data/philiumm/config_v2_ema.json}
MEM=${LAYOUT_MEM:-6G}
DEVICE=${LAYOUT_DEVICE:-cuda:0}
PRECISION=${LAYOUT_PRECISION:-16-mixed}
GPU_LIMIT=${LAYOUT_GPU_LIMIT:-5900}
RETRY=${LAYOUT_RETRY:-3}
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR" "$RESULTS"
export PATH="$ENV/bin:$PATH"
# the caching allocator: expandable segments fragment less across pages of different shapes
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
DRIVER=$ROOT/tools/philiumm_layout_stages.py
echo "== $(date -Is) run $NAME: images $IMAGES ($(ls "$IMAGES" | wc -l) files), results $RESULTS, config $CONFIG"
echo "   env $ENV, pipeline $PIPE ($(git -C "$PIPE" rev-parse --short HEAD 2>/dev/null)), runtime $RUNTIME, MemoryMax $MEM, device $DEVICE, precision $PRECISION"
for stage in "${STAGES[@]}"; do
  attempt=0
  while :; do
    attempt=$((attempt + 1))
    echo "== $(date -Is) stage $stage (attempt $attempt)"
    guard_pid=""
    case $stage in
      detect|baselines)
        # the GPU guard watches the stage's interpreter (the [p] keeps the guard
        # from matching its own command line) and kills it past the card limit
        # the pattern also names kraken itself (the baselines stage's child), so a
        # kill ends the process that holds the card and not only its parent
        bash "$ROOT/tools/gpu-guard.sh" "[p]hiliumm_layout_stages.py.*--stage $stage|rfdetr-env/bin/[k]raken" "$GPU_LIMIT" "$LOGDIR/$NAME-$stage-gpu.csv" 2 2500 &
        guard_pid=$!
        ;;
    esac
    systemd-run --user --scope -p "MemoryMax=$MEM" --quiet bash -c '
      /usr/bin/time -v "$@" 2> >(sed "s/^/[time] /" >&2)
      rc=$?
      cg=$(cut -d: -f3 /proc/self/cgroup)
      [ -r "/sys/fs/cgroup$cg/memory.peak" ] && echo "[cgroup] memory.peak $(cat /sys/fs/cgroup$cg/memory.peak) bytes ($(( $(cat /sys/fs/cgroup$cg/memory.peak) / 1048576 )) MiB) for the whole stage"
      exit $rc' _ "$ENV/bin/python" "$DRIVER" --pipeline "$PIPE" --input "$IMAGES" --output "$RESULTS" --config "$CONFIG" --stage "$stage" --runtime "$RUNTIME" --device "$DEVICE" --precision "$PRECISION"
    rc=$?
    [ -n "$guard_pid" ] && { sleep 3; kill "$guard_pid" 2>/dev/null; wait "$guard_pid" 2>/dev/null; }
    echo "== $(date -Is) stage $stage exit $rc"
    [ $rc -eq 0 ] && break
    if [ $attempt -gt $RETRY ]; then echo "== stage $stage failed $attempt times; stopping"; exit $rc; fi
    echo "== relaunch in 60 s"; sleep 60
  done
done
echo "== $(date -Is) run $NAME done"
