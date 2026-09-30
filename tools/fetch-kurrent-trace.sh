#!/usr/bin/env bash
# tools/fetch-kurrent-trace.sh — fetch (or take a local copy of), verify and
# unpack the "Kurrent Trace v0.1" package into data/external/kurrent-trace/.
#
# The package (137 MB zip) holds 383 line crops + transcriptions from the
# Dresdner Hofdiarium 1673 (Stefan Beckert, Zenodo 10.5281/zenodo.15303243),
# 180 machine segments from two Leibniz pages (LH 35, 3 A 8, Bl. 22r–v), the
# original source files, and an offline validator. It is the Kurrent smoke-test
# set for the Kurrent track (STATUS: K1). Its Dresden text carries a licence
# conflict (Zenodo says CC BY 4.0, the README says CC BY-NC-SA 4.0) and is
# treated as nc-bucket material: internal evaluation only, never exported,
# never committed. data/ is gitignored, so nothing here touches git.
#
#   tools/fetch-kurrent-trace.sh --id <google-drive-file-id>     # download
#   tools/fetch-kurrent-trace.sh --zip ~/Downloads/Kurrent-Trace-v0.1.zip
#
# Idempotent: a zip that already verifies is not downloaded again; an unpacked
# package that passes the sanity checks is left alone (use --force to redo).
set -euo pipefail

EXPECTED_SHA256="f2c67439443cf7bc6c1419210bfb932e1d838f5b599d94b1801cfa53faf9a05c"
EXPECTED_SIZE=136897543
PKG_NAME="Kurrent-Trace-v0.1"
DEST="${DEST:-data/external/kurrent-trace}"
DRIVE_ID=""
ZIP_PATH=""
VALIDATE=1
FORCE=0

usage() {
  sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
fail() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id)          DRIVE_ID="${2:-}"; shift 2 ;;
    --zip)         ZIP_PATH="${2:-}"; shift 2 ;;
    --dest)        DEST="${2:-}"; shift 2 ;;
    --no-validate) VALIDATE=0; shift ;;
    --force)       FORCE=1; shift ;;
    -h|--help)     usage 0 ;;
    *)             echo "unknown argument: $1" >&2; usage 2 ;;
  esac
done
[[ -n "$DRIVE_ID" || -n "$ZIP_PATH" ]] || { echo "need --id <drive file id> or --zip <path>" >&2; usage 2; }

for tool in curl unzip sha256sum; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool is not installed (sudo apt-get install -y $tool)"
done

# Run from the repository root whatever the caller's cwd.
cd "$(dirname "$(readlink -f "$0")")/.."
mkdir -p "$DEST"
PKG_DIR="$DEST/$PKG_NAME"

sha_of() { sha256sum "$1" | awk '{print $1}'; }

zip_verifies() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  [[ "$(stat -c %s "$f")" -eq "$EXPECTED_SIZE" ]] || return 1
  [[ "$(sha_of "$f")" == "$EXPECTED_SHA256" ]] || return 1
}

# ---------------------------------------------------------------- the zip ---
if [[ -n "$ZIP_PATH" ]]; then
  [[ -f "$ZIP_PATH" ]] || fail "no such file: $ZIP_PATH"
  ZIP="$ZIP_PATH"
else
  ZIP="$DEST/$PKG_NAME.zip"
  if zip_verifies "$ZIP" && [[ $FORCE -eq 0 ]]; then
    say "zip already present and verified: $ZIP"
  else
    say "downloading from Google Drive (137 MB)"
    URL="https://drive.usercontent.google.com/download?id=${DRIVE_ID}&export=download&confirm=t"
    curl -fL --retry 3 --retry-delay 5 --progress-bar -o "$ZIP.part" "$URL"
    if ! unzip -tq "$ZIP.part" >/dev/null 2>&1; then
      rm -f "$ZIP.part"
      fail "Drive returned something that is not the zip (a sign-in or scan page). Download it in a browser and re-run with --zip <path>."
    fi
    mv "$ZIP.part" "$ZIP"
  fi
fi

say "verifying $ZIP"
ACTUAL_SIZE="$(stat -c %s "$ZIP")"
ACTUAL_SHA="$(sha_of "$ZIP")"
echo "size   $ACTUAL_SIZE (expected $EXPECTED_SIZE)"
echo "sha256 $ACTUAL_SHA"
if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA256" ]]; then
  if [[ $FORCE -eq 1 ]]; then
    echo "WARNING: checksum differs from the pinned release; continuing because of --force" >&2
  else
    fail "checksum mismatch: this is not the pinned Kurrent-Trace-v0.1.zip (use --force to unpack anyway)"
  fi
fi
unzip -tq "$ZIP" >/dev/null || fail "zip integrity test failed"

# ------------------------------------------------------------- unpacking ---
if [[ -d "$PKG_DIR" && $FORCE -eq 0 && -f "$PKG_DIR/data/published_gt.jsonl" ]]; then
  say "already unpacked: $PKG_DIR (use --force to redo)"
else
  say "unpacking into $DEST"
  rm -rf "$PKG_DIR"
  unzip -oq "$ZIP" -d "$DEST"
  [[ -d "$PKG_DIR" ]] || fail "expected $PKG_DIR after unpacking; the zip layout changed"
fi

# ---------------------------------------------------------- sanity checks ---
say "sanity checks"
n_gt="$(wc -l < "$PKG_DIR/data/published_gt.jsonl")"
n_dresden_png="$(find "$PKG_DIR/images/lines/dresden1673" -name '*.png' | wc -l)"
n_png="$(find "$PKG_DIR/images" -name '*.png' | wc -l)"
status="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['status'])" "$PKG_DIR/reports/validation-report.json" 2>/dev/null || echo unknown)"
ok=1
[[ "$n_gt" -eq 383 ]]          || { echo "published_gt.jsonl has $n_gt lines, expected 383"; ok=0; }
[[ "$n_dresden_png" -eq 383 ]] || { echo "dresden line crops: $n_dresden_png, expected 383"; ok=0; }
[[ "$n_png" -eq 565 ]]         || { echo "png files: $n_png, expected 565"; ok=0; }
[[ "$status" == "PASS" ]]      || { echo "shipped validation report status: $status, expected PASS"; ok=0; }
[[ $ok -eq 1 ]] || fail "sanity checks failed; the package is not the expected release"
echo "published GT lines  383"
echo "dresden line crops  383"
echo "png files           565"
echo "shipped validation  PASS"

# --------------------------------------------- optional offline validator ---
if [[ $VALIDATE -eq 1 ]]; then
  say "running the package's own validator (hashes, crops; about a minute)"
  ran=0
  if command -v uv >/dev/null 2>&1 && [[ -f pyproject.toml ]]; then
    if uv run --with jsonschema --with pillow python "$PKG_DIR/scripts/validate.py"; then ran=1; else fail "validator reported a problem"; fi
  elif python3 -c 'import PIL, jsonschema' >/dev/null 2>&1; then
    if python3 "$PKG_DIR/scripts/validate.py"; then ran=1; else fail "validator reported a problem"; fi
  fi
  [[ $ran -eq 1 ]] || echo "validator skipped: needs uv (repo root) or python3 with Pillow + jsonschema"
fi

say "done"
echo "package  $PKG_DIR"
echo "zip      $ZIP"
echo "licence  Dresden text: CC BY 4.0 (Zenodo field) vs CC BY-NC-SA 4.0 (README) — nc bucket until resolved; images PDM 1.0; package code CC0"
echo "K1 reads it from data/external/kurrent-trace/$PKG_NAME/ (gitignored)"
