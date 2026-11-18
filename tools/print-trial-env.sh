#!/usr/bin/env bash
# The print trial's own environment (M1 Task 1b, DQ1 2026-11-17): kraken 7.1
# with the D-FINE plug-in, the LADaS region model (Apache-2.0) and the
# Gallicorpora+ print model (CC0 repository) under data/print/. Nothing goes
# into .venv or the project's dependencies; the torch wheels are the ones
# uv's cache already holds (the card is proven on them).
#
#   tools/print-trial-env.sh            # make or refresh; idempotent
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
ENV=$ROOT/data/print/dfine-env
MODELS=$ROOT/data/print/models
PY=${PRINT_PYTHON:-3.12}
UA="leibniz-legible/0.1 (+https://github.com/marchofhares/leibnizlegible; oofriss@gmail.com)"
LADAS_DOI=10.5281/zenodo.18715364
LADAS_FILE=ladas_l.safetensors
LADAS_MD5=06aa34eacb02fe49642f8838d49501db        # the Zenodo record, read 2026-11-17
GALLI_URL="https://github.com/Gallicorpora/Segmentation-and-HTR-Models/releases/download/1.0.0/Gallicorpora%2B_best.mlmodel"
GALLI_FILE="Gallicorpora+_best.mlmodel"
GALLI_SHA=b7261e804394fe883e351f17b599d4c86417db3e69f67c091eb31665fcc660b3   # read 2026-11-17

step() { echo; echo "== $(date -Is) $*"; }
fail() { echo; echo "!! FAILED at: $*"; exit 1; }

step "disk before"
df -h /mnt/c | tail -1
vhd_before=$(df -B1 / | awk 'NR==2{print $3}')
mkdir -p "$MODELS" || fail mkdir

step "the Python environment (uv venv, Python $PY): kraken 7.1 + dfine-kraken, torch 2.12.0 from the cache"
[ -x "$ENV/bin/python" ] || uv venv --python "$PY" "$ENV" || fail "uv venv"
uv pip install --python "$ENV/bin/python" "torch==2.12.0" "torchvision==0.27.0" "kraken==7.1.1" "dfine-kraken==0.4.4" \
  || fail "uv pip install (see uv's message above)"
"$ENV/bin/python" - <<'PY' || fail "import smoke test"
import importlib.metadata as m
import torch
for n in ["torch", "kraken", "dfine-kraken", "coremltools", "lightning", "numpy"]:
    try:
        print(f"  {n} {m.version(n)}")
    except m.PackageNotFoundError:
        print(f"  {n} MISSING")
print("  torch cuda", torch.version.cuda, "available", torch.cuda.is_available())
import dfine  # noqa: F401
print("  imports ok")
PY
"$ENV/bin/kraken" --version || fail "kraken"

step "the LADaS D-FINE large region model ($LADAS_DOI): the Zenodo file by curl (kraken get would start a torch process beside a running job)"
if [ ! -f "$MODELS/$LADAS_FILE" ] || [ "$(md5sum "$MODELS/$LADAS_FILE" | cut -d' ' -f1)" != "$LADAS_MD5" ]; then
  curl -sS -L -A "$UA" --retry 3 -o "$MODELS/$LADAS_FILE" "https://zenodo.org/records/18715364/files/$LADAS_FILE?download=1" || fail "download of $LADAS_FILE"
  curl -sS -L -A "$UA" --retry 3 -o "$MODELS/ladas_l.README.md" "https://zenodo.org/records/18715364/files/README.md?download=1" || true
fi
got=$(md5sum "$MODELS/$LADAS_FILE" | cut -d' ' -f1)
[ "$got" = "$LADAS_MD5" ] || fail "md5 of $LADAS_FILE: $got, expected $LADAS_MD5"
echo "$LADAS_FILE md5 ok ($got, $(stat -c %s "$MODELS/$LADAS_FILE") bytes)"

step "Gallicorpora+ (release 1.0.0)"
if [ ! -f "$MODELS/$GALLI_FILE" ] || [ "$(sha256sum "$MODELS/$GALLI_FILE" | cut -d' ' -f1)" != "$GALLI_SHA" ]; then
  curl -sS -L -A "$UA" --retry 3 -o "$MODELS/$GALLI_FILE" "$GALLI_URL" || fail "download of Gallicorpora+"
fi
got=$(sha256sum "$MODELS/$GALLI_FILE" | cut -d' ' -f1)
[ "$got" = "$GALLI_SHA" ] || fail "digest of $GALLI_FILE: $got"
echo "$GALLI_FILE sha256 ok"
(cd "$MODELS" && sha256sum "$LADAS_FILE" "$GALLI_FILE" > SHA256SUMS)

if [ -z "${PRINT_SKIP_LOAD_TEST:-}" ]; then
step "can kraken 7.1 load the CoreML model? (else the OCR step converts it with ketos convert)"
"$ENV/bin/python" - "$MODELS/$GALLI_FILE" <<'PY' || echo "  (load failed; the OCR step converts with ketos convert)"
import sys
from kraken.lib import models
m = models.load_any(sys.argv[1])
print("  loaded:", type(m).__name__, "seg type", getattr(m, "seg_type", "?"))
PY
fi

step "disk after"
df -h /mnt/c | tail -1
vhd_after=$(df -B1 / | awk 'NR==2{print $3}')
echo "the VHD grew by $(( (vhd_after - vhd_before) / 1048576 )) MiB"
echo "== done $(date -Is)"
