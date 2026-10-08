#!/usr/bin/env bash
# deploy/staging.sh — put a branch on the staging site (deploy/README.md §14).
# As root, any time, from any checkout of the kit. The live site is never
# touched: this script knows only /opt/leibniz-legible-staging, its unit, its
# env file and the staging index.
#
#   staging.sh BRANCH        origin/BRANCH into the staging checkout, uv sync,
#                            restart the unit, /healthz, print the address
#   staging.sh --main        the same with main: after a merge, so an old
#                            branch never sits on staging half-forgotten
#   staging.sh --status      what staging runs, the unit, the index, /healthz
#   staging.sh --index       build a staging index, leibniz_pages_staging, from
#                            the store staging.env names, and point staging at
#                            it: for a branch that changes what the index holds
#                            (M1). Asks before it starts; hours, the index's
#                            disk a second time, staging down meanwhile. The
#                            live index is not touched.
#   staging.sh --drop-index  delete that index; staging back on the live one
set -euo pipefail

APP_DIR=/opt/leibniz-legible                 # the live checkout; its .uv/ caches are shared
STAGING_DIR=/opt/leibniz-legible-staging
STAGING_ENV=/etc/leibniz-legible/staging.env
STAGING_DOMAIN=staging.leibnizlegible.com
STAGING_PORT=8001
UNIT=leibniz-legible-staging
INDEX_UNIT=leibniz-index-staging
STAGING_INDEX=leibniz_pages_staging
LIVE_INDEX=leibniz_pages

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die() { echo "staging: $*" >&2; exit 1; }
as_leibniz() { sudo -u leibniz -H "$@"; }
usage() { sed -n '2,/^set -euo/p' "${BASH_SOURCE[0]}" | sed '$d' | sed 's/^# \{0,1\}//'; }
env_get() { sed -n "s/^$1=//p" "$STAGING_ENV" | tail -1; }
master_key() { sed -n 's/^MEILI_MASTER_KEY=//p' /etc/meilisearch/env | tail -1; }

# set_kv FILE KEY VALUE — replace the KEY= line (set or commented out), else append;
# the file keeps its owner and mode.
set_kv() {
  local file=$1 key=$2 value=$3 tmp
  tmp="$(mktemp)"
  awk -v k="$key" -v v="$value" '
    !done && $0 ~ ("^#? ?" k "=") { print k "=" v; done = 1; next }
    { print }
    END { if (!done) print k "=" v }
  ' "$file" > "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

healthz() { curl -fsS --max-time 5 "http://127.0.0.1:$STAGING_PORT/healthz"; }

wait_healthz() {
  local out
  for _ in $(seq 1 30); do
    if out="$(healthz 2>/dev/null)"; then echo "$out"; return 0; fi
    sleep 1
  done
  echo "no answer on 127.0.0.1:$STAGING_PORT/healthz after 30 s; the journal says:" >&2
  journalctl -u "$UNIT" -n 20 --no-pager >&2
  return 1
}

checkout_summary() {   # "BRANCH at SHA — subject"
  local up
  up="$(as_leibniz git -C "$STAGING_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo '?')"
  echo "${up#origin/} at $(as_leibniz git -C "$STAGING_DIR" rev-parse --short HEAD)" \
       "— $(as_leibniz git -C "$STAGING_DIR" log -1 --format=%s)"
}

deploy_branch() {
  local branch=$1 index
  say "staging ← $branch"
  as_leibniz git -C "$STAGING_DIR" fetch --quiet --prune origin
  as_leibniz git -C "$STAGING_DIR" rev-parse --verify --quiet "origin/$branch^{commit}" >/dev/null \
    || die "no branch '$branch' on origin"
  as_leibniz git -C "$STAGING_DIR" checkout --quiet -B staging "origin/$branch"
  as_leibniz env UV_CACHE_DIR="$APP_DIR/.uv/cache" UV_PYTHON_INSTALL_DIR="$APP_DIR/.uv/python" \
    uv sync --project "$STAGING_DIR" --python 3.12 --frozen --no-dev --extra web
  systemctl restart "$UNIT"
  wait_healthz
  echo "staging runs $(checkout_summary)"
  index="$(env_get LEIBNIZ_MEILI_INDEX)"
  [[ -z "$index" || "$index" == "$LIVE_INDEX" ]] \
    || echo "note: staging searches $index (staging.sh --drop-index puts it back on $LIVE_INDEX)"
  echo "https://$STAGING_DOMAIN/"
}

status() {
  echo "checkout   $(checkout_summary)"
  echo "unit       $UNIT: $(systemctl is-active "$UNIT" || true)"
  echo "index      $(env_get LEIBNIZ_MEILI_INDEX) (store $(env_get LEIBNIZ_DB_PATH))"
  if systemctl is-active --quiet "$INDEX_UNIT" 2>/dev/null; then
    echo "building   $INDEX_UNIT is running (journalctl -fu $INDEX_UNIT)"
  fi
  echo "healthz    $(healthz 2>/dev/null || echo 'no answer')"
  echo "https      $(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://$STAGING_DOMAIN/" || echo 000)" \
       "without credentials (401 is right)"
}

build_index() {
  local db url key master patterns p matched=0 yes rc
  db="$(env_get LEIBNIZ_DB_PATH)"; url="$(env_get MEILI_URL)"; key="$(env_get MEILI_API_KEY)"
  [[ -f "$db" ]] || die "LEIBNIZ_DB_PATH in $STAGING_ENV names no file: '$db'"
  [[ -n "$url" ]] || url=http://127.0.0.1:7700
  master="$(master_key)"
  [[ -n "$master" ]] || die "no MEILI_MASTER_KEY in /etc/meilisearch/env"
  ! systemctl is-active --quiet leibniz-index 2>/dev/null \
    || die "the live index build (leibniz-index) is running; one build at a time (deploy/README.md §13, item 4)"
  ! systemctl is-active --quiet "$INDEX_UNIT" 2>/dev/null \
    || die "$INDEX_UNIT is already running (journalctl -fu $INDEX_UNIT)"
  # The serving key must be allowed to read the staging index. The key
  # deploy/meili-search-key.sh makes is scoped to leibniz_pages*, which covers
  # leibniz_pages_staging; a key scoped otherwise has to be replaced first.
  if [[ -n "$key" ]]; then
    patterns="$(curl -fsS -H "Authorization: Bearer $master" "$url/keys/$key" \
      | "$STAGING_DIR/.venv/bin/python" -c 'import json, sys; print(" ".join(json.load(sys.stdin).get("indexes", [])))')" \
      || die "could not read the search key's scope from Meilisearch ($url/keys/…)"
    for p in $patterns; do
      # shellcheck disable=SC2053  # the pattern is meant to glob
      [[ "$STAGING_INDEX" == $p ]] && matched=1
    done
    (( matched )) || die "the search key in $STAGING_ENV is scoped to '$patterns', which does not cover $STAGING_INDEX:" \
      "make one with deploy/meili-search-key.sh (scoped to leibniz_pages*) and put it in $STAGING_ENV as MEILI_API_KEY"
  fi
  say "a staging index: $STAGING_INDEX on $url, built from $db"
  cat <<WHAT
This will
  1. stop $UNIT: staging is down until the build ends;
  2. write LEIBNIZ_MEILI_INDEX=$STAGING_INDEX into $STAGING_ENV;
  3. run 'leibniz index build --backend meili --meili-index $STAGING_INDEX' as a
     transient systemd unit, $INDEX_UNIT, with the master key: one full pass
     over the store. The live index took 5 h 33 m to build on this box
     (deploy/README.md §5), and the second index takes about as much disk again:
WHAT
  df -h /var/lib/meilisearch | sed 's/^/     /'
  cat <<WHAT
  4. wait here, then start $UNIT again. Ctrl-C leaves the build running:
     'journalctl -fu $INDEX_UNIT' watches it, 'systemctl start $UNIT' when it is done.
The live index ($LIVE_INDEX) and the live site are not touched.
WHAT
  read -r -p "Build it? [y/N] " yes
  [[ "$yes" =~ ^[Yy]([Ee][Ss])?$ ]] || { echo "nothing done"; return 0; }
  systemctl stop "$UNIT"
  set_kv "$STAGING_ENV" LEIBNIZ_MEILI_INDEX "$STAGING_INDEX"
  systemctl reset-failed "$INDEX_UNIT" 2>/dev/null || true
  systemd-run --unit="$INDEX_UNIT" --uid=leibniz --gid=leibniz --remain-after-exit \
    -p WorkingDirectory="$STAGING_DIR" \
    --setenv=LEIBNIZ_DB_PATH="$db" --setenv=MEILI_URL="$url" --setenv=MEILI_MASTER_KEY="$master" \
    "$STAGING_DIR/.venv/bin/leibniz" index build --backend meili --meili-index "$STAGING_INDEX"
  trap 'echo; echo "the build goes on under systemd: journalctl -fu '"$INDEX_UNIT"'; then systemctl start '"$UNIT"'"; exit 130' INT
  echo "waiting; journalctl -fu $INDEX_UNIT in another window shows the progress …"
  while [[ "$(systemctl show -p SubState --value "$INDEX_UNIT")" == running ]]; do sleep 30; done
  trap - INT
  rc="$(systemctl show -p ExecMainStatus --value "$INDEX_UNIT")"
  journalctl -u "$INDEX_UNIT" -n 3 --no-pager
  systemctl stop "$INDEX_UNIT" 2>/dev/null || true
  systemctl reset-failed "$INDEX_UNIT" 2>/dev/null || true
  (( rc == 0 )) || die "the build failed (exit $rc; journalctl -u $INDEX_UNIT has the error)." \
    "$STAGING_ENV still names $STAGING_INDEX: staging.sh --drop-index puts staging back on $LIVE_INDEX"
  systemctl start "$UNIT"
  wait_healthz
  echo "staging searches $STAGING_INDEX"
}

drop_index() {
  local url master uid
  url="$(env_get MEILI_URL)"; [[ -n "$url" ]] || url=http://127.0.0.1:7700
  master="$(master_key)"
  [[ -n "$master" ]] || die "no MEILI_MASTER_KEY in /etc/meilisearch/env"
  say "dropping $STAGING_INDEX; staging back on $LIVE_INDEX"
  for uid in "$STAGING_INDEX" "${STAGING_INDEX}_meta"; do
    curl -sS -o /dev/null -w "DELETE /indexes/$uid → %{http_code}\n" \
      -X DELETE -H "Authorization: Bearer $master" "$url/indexes/$uid"
  done
  set_kv "$STAGING_ENV" LEIBNIZ_MEILI_INDEX "$LIVE_INDEX"
  systemctl restart "$UNIT"
  wait_healthz
  echo "staging searches $LIVE_INDEX again (the deletes are Meilisearch tasks; the disk frees as they run)"
}

main() {
  case "${1:-}" in
    ""|-h|--help) usage; exit 0 ;;
  esac
  [[ $EUID -eq 0 ]] || die "run as root (sudo)"
  [[ -d "$STAGING_DIR/.git" && -f "$STAGING_ENV" ]] || die "staging is not installed (deploy/staging-install.sh)"
  (( $# == 1 )) || die "one branch name, or one option (see --help)"
  case "$1" in
    --main) deploy_branch main ;;
    --status) status ;;
    --index) build_index ;;
    --drop-index) drop_index ;;
    --*) die "unknown option '$1' (see --help)" ;;
    *) deploy_branch "$1" ;;
  esac
}

# Parsed as one unit before anything runs, so a checkout that replaces this
# very file (staging.sh from the staging checkout) cannot trip the running copy.
{ main "$@"; exit; }
