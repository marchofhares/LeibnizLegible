#!/usr/bin/env bash
# deploy/prepare-store.sh — make the serving copy of the store.
#
# Run on the machine that holds the corpus store (where the pipeline ran). It
# checkpoints the WAL, writes a compact single-file copy with VACUUM INTO (in
# rollback-journal mode, so the server needs no -wal file and the app's
# read-only connections are happy), verifies it, and prints the size and the
# SHA-256 to compare after the transfer. Nothing in the source is modified
# beyond the checkpoint.
#
#   deploy/prepare-store.sh [data/inventory.sqlite] [inventory-serving.sqlite]
#   rsync -avP --checksum inventory-serving.sqlite user@host:/var/lib/leibniz-legible/inventory.sqlite
set -euo pipefail

SRC="${1:-data/inventory.sqlite}"
OUT="${2:-inventory-serving.sqlite}"

[[ -f "$SRC" ]] || { echo "no store at $SRC" >&2; exit 1; }
rm -f "$OUT"

uv run python - "$SRC" "$OUT" <<'PY'
import sqlite3
import sys

src, out = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(src)
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.execute("VACUUM INTO '%s'" % out.replace("'", "''"))
conn.close()
copy = sqlite3.connect(out)
print("integrity:", copy.execute("PRAGMA integrity_check").fetchone()[0])
print("journal mode:", copy.execute("PRAGMA journal_mode").fetchone()[0])
for table in ("works", "pages", "lines", "gt_lines", "runs"):
    print(f"{table}: {copy.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]:,}")
copy.close()
PY

ls -lh "$OUT"
sha256sum "$OUT" | tee "$OUT.sha256"
