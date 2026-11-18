#!/usr/bin/env bash
# PHILIUMM's layout pipeline in an environment of its own (P1 Task 3, DQ1
# 2026-11-17): the clone without LFS content, a Python 3.12 venv, the v2
# checkpoints from the Hub with their digests checked, a config of this
# project's own pointing at the EMA checkpoint. Her repository is never
# modified; everything bulky lives under $LAYOUT_BULK (D:) behind symlinks
# from data/philiumm/.
#
#   tools/philiumm-layout-env.sh            # make or refresh everything
#   LAYOUT_BULK=/mnt/d/leibniz-layout tools/philiumm-layout-env.sh
#
# Prints a diagnosis and exits non-zero at the first step that fails.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BULK=${LAYOUT_BULK:-/mnt/d/leibniz-layout}
ENV=$ROOT/data/philiumm/rfdetr-env
PIPE=$BULK/rfdetr-pipeline
MODELS=$BULK/models
REPO=https://gitlab.com/eman8/scripts/htr-ocr/scripts-pour-le-pretraitement-des-corpus-pour-escriptorium.git
HF=https://huggingface.co/DenisaBumba/rfdetr-instance-segmentation-leibniz-manuscripts-v2/resolve/main
HF_REVISION=4a5c7d93e8a6da1b4e01794c35e24113c2405c28   # the card as read 2026-11-17
UA="leibniz-legible/0.1 (+https://github.com/marchofhares/leibnizlegible; oofriss@gmail.com)"
PY=${LAYOUT_PYTHON:-3.12}
# The two checkpoints: size and SHA-256 as the Hub's LFS metadata and the
# pipeline's LFS pointers both state them (read 2026-11-17).
declare -A SHA=(
  [checkpoint_best_ema_v2.pth]=ba76c8e592886c39f69ef1b2093a4fc74eff1e14a84e191ee606e1e84aa9bb4a
  [checkpoint_best_regular_v2.pth]=67124b59114ca0d8e3c52fad07ad85a3623f1892d0bb5d7773774f9e5b3429ab
)
declare -A SIZE=(
  [checkpoint_best_ema_v2.pth]=149710503
  [checkpoint_best_regular_v2.pth]=299221359
)

step() { echo; echo "== $(date -Is) $*"; }
fail() { echo; echo "!! FAILED at: $*"; echo "   diagnosis: see the lines above; the step can be rerun, every step is idempotent"; exit 1; }

step "disk before (C: is the budget for anything under /)"
df -h /mnt/c "$BULK" 2>/dev/null || df -h /mnt/c /mnt/d
vhd_before=$(df -B1 / | awk 'NR==2{print $3}')

step "folders and symlinks"
mkdir -p "$BULK" "$MODELS" "$ROOT/data/philiumm" || fail "mkdir under $BULK"
for pair in "rfdetr-pipeline:$PIPE" "models:$MODELS"; do
  name=${pair%%:*}; target=${pair#*:}
  link=$ROOT/data/philiumm/$name
  if [ -L "$link" ]; then
    [ "$(readlink "$link")" = "$target" ] || fail "data/philiumm/$name points elsewhere: $(readlink "$link")"
  elif [ -e "$link" ]; then
    fail "data/philiumm/$name exists and is not a symlink"
  else
    ln -s "$target" "$link" || fail "symlink data/philiumm/$name"
  fi
  echo "data/philiumm/$name -> $target"
done

step "her repository (clone without LFS content: only the .pth files are LFS, and those come from the Hub)"
if [ -d "$PIPE/.git" ]; then
  echo "already cloned; not touched (fetch only)"
  git -C "$PIPE" fetch -q origin 2>&1 | tail -2
else
  GIT_LFS_SKIP_SMUDGE=1 git clone -q "$REPO" "$PIPE" || fail "git clone"
fi
sha=$(git -C "$PIPE" rev-parse HEAD) || fail "git rev-parse"
date_=$(git -C "$PIPE" log -1 --format=%cI)
echo "commit $sha ($date_) $(git -C "$PIPE" log -1 --format=%s)"
printf 'commit %s\ndate %s\nurl %s\nlicence none stated in the repository (read %s)\n' "$sha" "$date_" "$REPO" "$(date -I)" > "$ROOT/data/philiumm/rfdetr-pipeline.COMMIT"
git -C "$PIPE" status --porcelain | grep -q . && echo "WARNING: her working tree is not clean" || echo "her working tree is clean"

step "the bundled model files: digests (plain blobs) and LFS pointers (.pth)"
(
  cd "$PIPE" || exit 1
  for f in models/htr/*.safetensors models/segmentation/baselines/*; do
    [ -f "$f" ] && sha256sum "$f"
  done
  for f in models/segmentation/zones/*.pth; do
    if head -c 7 "$f" | grep -q version; then echo "$(awk '/oid sha256/{sub("sha256:","",$2); print $2}' "$f")  $f (LFS pointer, size $(awk '/^size/{print $2}' "$f"))"; else sha256sum "$f"; fi
  done
) | tee "$ROOT/data/philiumm/rfdetr-pipeline.models.sha256"
v1_ours=$ROOT/data/models/philiumm-seg/blla_ft_leibniz_v1_0.4750.safetensors
if [ -f "$v1_ours" ] && [ -f "$PIPE/models/segmentation/baselines/best_0.4750.safetensors" ]; then
  a=$(sha256sum "$v1_ours" | cut -d' ' -f1); b=$(sha256sum "$PIPE/models/segmentation/baselines/best_0.4750.safetensors" | cut -d' ' -f1)
  [ "$a" = "$b" ] && echo "best_0.4750.safetensors == this project's blla_ft_leibniz_v1_0.4750 (same SHA-256)" || echo "best_0.4750.safetensors differs from this project's v1 segmenter ($a vs $b)"
fi

step "the v2 checkpoints from the Hub (cache-first; revision $HF_REVISION)"
echo "$HF_REVISION" > "$MODELS/REVISION"
for f in checkpoint_best_ema_v2.pth checkpoint_best_regular_v2.pth; do
  dst=$MODELS/$f
  if [ -f "$dst" ] && [ "$(stat -c %s "$dst")" = "${SIZE[$f]}" ] && [ "$(sha256sum "$dst" | cut -d' ' -f1)" = "${SHA[$f]}" ]; then
    echo "$f present, digest ok"; continue
  fi
  echo "downloading $f (${SIZE[$f]} bytes)"
  curl -sS -L -A "$UA" -C - --retry 3 -o "$dst" "$HF/$f" || fail "download $f"
  got=$(sha256sum "$dst" | cut -d' ' -f1)
  if [ "$got" != "${SHA[$f]}" ]; then rm -f "$dst"; fail "digest of $f: got $got, expected ${SHA[$f]} (file removed)"; fi
  echo "$f ok ($got)"
done
(cd "$MODELS" && sha256sum checkpoint_best_ema_v2.pth checkpoint_best_regular_v2.pth > SHA256SUMS)

step "the Python environment (uv venv, Python $PY)"
if [ ! -x "$ENV/bin/python" ]; then
  uv venv --python "$PY" "$ENV" || fail "uv venv"
fi
"$ENV/bin/python" --version
# Her requirements.txt (inference_sdk==1.2.7 supervision==0.28.0 rfdetr==1.8.0
# opencv-python==4.10.0.84 lxml==6.1.0 kraken==7.0.2 numpy==2.3.5) does not
# resolve as written: rfdetr 1.8.0 needs supervision>=0.29. kraken 7.0.2 pins
# torch<=2.10; the torch this card is proven on is 2.12.0 (.venv-k1, K4), which
# kraken 7.0.3 accepts. Everything else as she pins it.
uv pip install --python "$ENV/bin/python" \
  "torch==2.12.0" "torchvision==0.27.0" \
  "rfdetr==1.8.0" "supervision>=0.29" "inference_sdk==1.2.7" \
  "opencv-python==4.10.0.84" "lxml==6.1.0" "kraken==7.0.3" "numpy==2.3.5" \
  || fail "uv pip install (see uv's resolution message above)"
"$ENV/bin/python" - <<'PY' || fail "import smoke test"
import importlib.metadata as m
import torch
names = ["torch", "torchvision", "rfdetr", "supervision", "inference_sdk", "opencv-python", "lxml", "kraken", "numpy", "transformers", "shapely"]
for n in names:
    try:
        print(f"  {n} {m.version(n)}")
    except m.PackageNotFoundError:
        print(f"  {n} MISSING")
print("  torch cuda", torch.version.cuda, "available", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
import rfdetr, supervision, cv2, kraken  # noqa: F401
from rfdetr import RFDETRSegNano  # noqa: F401
print("  imports ok")
PY
"$ENV/bin/kraken" --version || fail "kraken on the venv's PATH"

step "the runtime root on the VHD: the model files her relative paths name (reads from D: over the share crawl while the backup chore reads it)"
RUNTIME=$ROOT/data/philiumm/rfdetr-runtime
mkdir -p "$RUNTIME/models/segmentation/zones" "$RUNTIME/models/segmentation/baselines" || fail "mkdir runtime"
ema=$RUNTIME/models/segmentation/zones/checkpoint_best_ema_v2.pth
if [ ! -f "$ema" ] || [ "$(sha256sum "$ema" | cut -d' ' -f1)" != "${SHA[checkpoint_best_ema_v2.pth]}" ]; then
  cp "$MODELS/checkpoint_best_ema_v2.pth" "$ema" || fail "copy of the EMA checkpoint to the VHD"
fi
[ "$(sha256sum "$ema" | cut -d' ' -f1)" = "${SHA[checkpoint_best_ema_v2.pth]}" ] || fail "digest of the VHD copy"
# her kraken step's baseline model is byte-identical to this project's v1 segmenter (checked above)
ln -sfn "$v1_ours" "$RUNTIME/models/segmentation/baselines/best_0.4750.safetensors"
echo "runtime root $RUNTIME: the EMA checkpoint (copy, digest ok), best_0.4750.safetensors -> $v1_ours"

step "the config: hers with the model path pointing at the EMA checkpoint in the runtime root"
"$ENV/bin/python" - "$PIPE/config_local.json" "$ema" "$ROOT/data/philiumm/config_v2_ema.json" <<'PY' || fail "config"
import json, sys
hers = json.load(open(sys.argv[1]))
mine = dict(hers)
mine["model_path"] = sys.argv[2]
json.dump(mine, open(sys.argv[3], "w"), indent=2)
print(json.dumps(mine, indent=2))
print("the only change from her config_local.json: model_path", hers.get("model_path"), "->", sys.argv[2])
PY

step "disk after"
df -h /mnt/c "$BULK" 2>/dev/null || df -h /mnt/c /mnt/d
vhd_after=$(df -B1 / | awk 'NR==2{print $3}')
echo "the VHD grew by $(( (vhd_after - vhd_before) / 1048576 )) MiB (hardlinks into uv's cache count once)"
du -sh "$PIPE" "$MODELS" 2>/dev/null
echo
echo "== done $(date -Is)"
