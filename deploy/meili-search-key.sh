#!/usr/bin/env bash
# deploy/meili-search-key.sh — create the restricted Meilisearch key the
# serving process uses (MEILI_API_KEY in /etc/leibniz-legible/env).
#
# The master key can do anything; `leibniz serve` only needs to search, read
# the index statistics for /healthz and the build-metadata document for
# /api/stats. Needs MEILI_MASTER_KEY in the environment and a running server.
#
#   export MEILI_MASTER_KEY=…     # from /etc/meilisearch/env
#   deploy/meili-search-key.sh    # prints the new key
set -euo pipefail

: "${MEILI_MASTER_KEY:?export MEILI_MASTER_KEY first (see /etc/meilisearch/env)}"
MEILI_URL="${MEILI_URL:-http://127.0.0.1:7700}"
PY="${PYTHON:-/opt/leibniz-legible/.venv/bin/python}"
[[ -x "$PY" ]] || PY=python3

curl -sS --fail -X POST "$MEILI_URL/keys" \
  -H "Authorization: Bearer $MEILI_MASTER_KEY" \
  -H 'Content-Type: application/json' \
  --data '{
    "name": "leibniz-serve",
    "description": "Leibniz Legible serving key: search, index stats, build metadata",
    "actions": ["search", "documents.get", "stats.get", "indexes.get"],
    "indexes": ["leibniz_pages*"],
    "expiresAt": null
  }' | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["key"])'
