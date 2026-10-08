#!/usr/bin/env bash
# deploy/staging-install.sh — the staging site on the live host (deploy/README.md
# §14): a second checkout of this repository under its own systemd unit on
# 127.0.0.1:8001, behind HTTP basic auth at staging.leibnizlegible.com, sharing
# the serving store, Meilisearch and uv's caches with the live site. Run once as
# root, from any checkout of the kit (the live one, or a clone of a branch).
# Idempotent: a re-run updates the unit, the venv and the site block in place
# and keeps the password unless --password is given. It never touches the live
# checkout, unit, env file or site block, and it starts no index build
# (deploy/staging.sh --index does that, when a branch needs its own index).
#
#   sudo deploy/staging-install.sh [--user NAME] [--password] [--branch BRANCH]
#
#   --user NAME      the basic-auth user name (asked for on the first install)
#   --password       ask for a new password although the site block has one
#   --branch BRANCH  what staging runs after the install (first install: main;
#                    a re-run: what it ran before). deploy/staging.sh BRANCH is
#                    the everyday way to change it.
#
# The password is typed on this terminal, hashed by `caddy hash-password`, and
# only the bcrypt hash is written into the site block: the plaintext passes
# through no command line, no file and no chat.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/marchofhares/leibnizlegible.git}"
STAGING_DIR=/opt/leibniz-legible-staging
CONF_DIR=/etc/leibniz-legible
STAGING_DOMAIN=staging.leibnizlegible.com
STAGING_PORT=8001
UNIT=leibniz-legible-staging
SITE_FILE=/etc/caddy/conf.d/staging.caddy
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die() { echo "staging-install: $*" >&2; exit 1; }
as_leibniz() { sudo -u leibniz -H "$@"; }
shopt -u patsub_replacement 2>/dev/null || true   # bash 5.2: keep & literal in ${x//a/b}

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

usage() { sed -n '2,/^set -euo/p' "${BASH_SOURCE[0]}" | sed '$d' | sed 's/^# \{0,1\}//'; }

USER_NAME="" NEW_PASSWORD=0 BRANCH=""
while (( $# )); do
  case "$1" in
    --user) USER_NAME="${2:?--user needs a name}"; shift 2 ;;
    --password) NEW_PASSWORD=1; shift ;;
    --branch) BRANCH="${2:?--branch needs a branch}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument '$1' (see --help)" ;;
  esac
done

# -- preconditions: fail early, change nothing ------------------------------- #
[[ $EUID -eq 0 ]] || die "run as root (sudo)"
id -u leibniz >/dev/null 2>&1 || die "no user 'leibniz': the live site is not installed (deploy/install.sh)"
[[ -f "$CONF_DIR/env" ]] || die "no $CONF_DIR/env: the live site is not configured (deploy/README.md §4)"
command -v uv >/dev/null 2>&1 || die "uv not found (deploy/install.sh installs it)"
command -v caddy >/dev/null 2>&1 || die "caddy not found"
grep -qE '^[[:space:]]*import /etc/caddy/conf\.d/\*\.caddy' /etc/caddy/Caddyfile \
  || die "/etc/caddy/Caddyfile lacks 'import /etc/caddy/conf.d/*.caddy' (deploy/README.md §13, item 2): add it, validate, reload, run this again"
for f in leibniz-legible-staging.service staging.env.example staging.caddy.example staging.sh; do
  [[ -f "$KIT_DIR/$f" ]] || die "missing $KIT_DIR/$f: run this from a checkout of the deploy kit"
done
case "$(caddy version)" in
  v2.[0-7].*|2.[0-7].*) AUTH_DIRECTIVE=basicauth ;;   # renamed basic_auth in Caddy 2.8
  *) AUTH_DIRECTIVE=basic_auth ;;
esac

# -- the user name and the password hash ------------------------------------- #
EXISTING_USER="" EXISTING_HASH=""
if [[ -f "$SITE_FILE" ]]; then
  read -r EXISTING_USER EXISTING_HASH < <(
    awk '$1 ~ /^basic_?auth$/ { f = 1; next }
         f && $1 == "}" { f = 0 }
         f && NF == 2 && $2 ~ /^\$2[aby]\$/ { print $1, $2; exit }' "$SITE_FILE"
  ) || true
fi
if [[ -z "$USER_NAME" ]]; then
  USER_NAME="$EXISTING_USER"
  if [[ -z "$USER_NAME" ]]; then
    [[ -t 0 ]] || die "no terminal to ask on: pass --user NAME, or run under ssh -t"
    read -r -p "User name for the password prompt on $STAGING_DOMAIN [staging]: " USER_NAME
    USER_NAME="${USER_NAME:-staging}"
  fi
fi
[[ "$USER_NAME" =~ ^[A-Za-z0-9._@-]+$ ]] || die "user name '$USER_NAME': letters, digits and . _ @ - only"
HASH="$EXISTING_HASH"
if [[ -z "$HASH" || "$NEW_PASSWORD" -eq 1 ]]; then
  [[ -t 0 ]] || die "a terminal is needed to type the password: ssh -t … sudo ${BASH_SOURCE[0]}"
  while :; do
    read -rs -p "Password for '$USER_NAME' on $STAGING_DOMAIN: " pw; echo
    read -rs -p "The same again: " pw2; echo
    [[ -n "$pw" && "$pw" == "$pw2" ]] && break
    echo "empty, or not the same twice; once more" >&2
  done
  # Piped, not --plaintext: a flag would show the password in `ps`.
  HASH="$(printf '%s\n' "$pw" | caddy hash-password)"
  unset pw pw2
  [[ "$HASH" =~ ^\$2[aby]\$ ]] || die "caddy hash-password did not return a bcrypt hash: $HASH"
elif [[ -n "$EXISTING_USER" && "$EXISTING_USER" != "$USER_NAME" ]]; then
  echo "user name $EXISTING_USER → $USER_NAME, password kept (--password to change it)"
else
  echo "password kept (--password to change it)"
fi

# -- the checkout, as the service user ---------------------------------------- #
say "the staging checkout: $STAGING_DIR"
install -d -o leibniz -g leibniz -m 0755 "$STAGING_DIR"
if [[ ! -d "$STAGING_DIR/.git" ]]; then
  BRANCH="${BRANCH:-main}"
  as_leibniz git clone --quiet --branch "$BRANCH" "$REPO_URL" "$STAGING_DIR"
  as_leibniz git -C "$STAGING_DIR" checkout --quiet -B staging "origin/$BRANCH"
  echo "cloned $REPO_URL ($BRANCH)"
elif [[ -z "$BRANCH" ]]; then
  # a re-run keeps what staging runs; deploy/staging.sh changes it
  BRANCH="$(as_leibniz git -C "$STAGING_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  BRANCH="${BRANCH#origin/}"
  [[ -n "$BRANCH" ]] || BRANCH=main
  echo "keeping the checkout on $BRANCH"
fi

# -- the unit and the environment file ---------------------------------------- #
say "unit and configuration"
install -m 0644 "$KIT_DIR/leibniz-legible-staging.service" "/etc/systemd/system/$UNIT.service"
if [[ -f "$CONF_DIR/staging.env" ]]; then
  echo "$CONF_DIR/staging.env exists; left as it is"
else
  install -m 0640 -o root -g leibniz "$KIT_DIR/staging.env.example" "$CONF_DIR/staging.env"
  # What the live site has and the example cannot know: the store path, the
  # search key, the image origin, the Calculemus switch, the proxy address.
  for key in LEIBNIZ_DB_PATH LEIBNIZ_SEARCH_BACKEND LEIBNIZ_INDEX_PATH MEILI_URL MEILI_API_KEY \
             LEIBNIZ_IMAGE_BASE_URL LEIBNIZ_CALCULEMUS_URL FORWARDED_ALLOW_IPS; do
    value="$(sed -n "s/^$key=//p" "$CONF_DIR/env" | tail -1)"
    [[ -n "$value" ]] || continue
    set_kv "$CONF_DIR/staging.env" "$key" "$value"
  done
  echo "wrote $CONF_DIR/staging.env from the example, with the live site's store path, search key and image origin:"
  grep -E '^(LEIBNIZ_DB_PATH|LEIBNIZ_PORT|LEIBNIZ_WORKERS|LEIBNIZ_BASE_URL|LEIBNIZ_RATE_LIMIT|LEIBNIZ_MEILI_INDEX|LEIBNIZ_IMAGE_BASE_URL)=' \
    "$CONF_DIR/staging.env" | sed 's/^/  /'
fi

# -- the Caddy site block: write, validate, reload ---------------------------- #
say "caddy: $SITE_FILE ($AUTH_DIRECTIVE, user $USER_NAME)"
install -d /etc/caddy/conf.d /var/log/caddy
block="$(<"$KIT_DIR/staging.caddy.example")"
block="${block//"basic_auth {"/"$AUTH_DIRECTIVE {"}"
block="${block//__STAGING_USER__/$USER_NAME}"
block="${block//__STAGING_HASH__/$HASH}"
previous=""
if [[ -f "$SITE_FILE" ]]; then
  previous="$SITE_FILE.previous"     # not *.caddy: the import glob skips it
  cp -p "$SITE_FILE" "$previous"
fi
tmp="$(mktemp)"
printf '%s\n' "$block" > "$tmp"
install -m 0640 -o root -g caddy "$tmp" "$SITE_FILE"
rm -f "$tmp"
# Validate what the service will load, in its environment (the systemd drop-in
# feeds Caddy caddy.env). A failed validate changes nothing that runs.
# shellcheck disable=SC1091
if [[ -f "$CONF_DIR/caddy.env" ]]; then set -a; . "$CONF_DIR/caddy.env"; set +a; fi
if ! caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile; then
  if [[ -n "$previous" ]]; then mv "$previous" "$SITE_FILE"; else rm -f "$SITE_FILE"; fi
  die "the new site block does not validate; the previous configuration is back in place and Caddy was not reloaded"
fi
[[ -z "$previous" ]] || rm -f "$previous"
if systemctl is-active --quiet caddy; then
  systemctl reload caddy             # reload, never restart: the live site stays up
else
  systemctl start caddy
fi

# -- the unit, then the first deploy through staging.sh ----------------------- #
say "the unit: $UNIT on 127.0.0.1:$STAGING_PORT"
systemctl daemon-reload
systemctl enable --quiet "$UNIT"
"$KIT_DIR/staging.sh" "$BRANCH"      # fetch, checkout, uv sync, restart, /healthz

say "checks"
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$STAGING_DOMAIN/" || true)"
case "$code" in
  401) echo "https://$STAGING_DOMAIN/ answers 401 without credentials, as it should" ;;
  000) echo "https://$STAGING_DOMAIN/ does not answer yet: Caddy may still be obtaining the certificate" \
            "(journalctl -u caddy -n 20); the DNS record must point at this host, DNS only" ;;
  *) echo "https://$STAGING_DOMAIN/ answered $code, not the expected 401: journalctl -u caddy -n 20" ;;
esac
cat <<DONE

Staging is installed.
  address      https://$STAGING_DOMAIN/   user '$USER_NAME', the password you typed
  checkout     $STAGING_DIR on $BRANCH
  unit         $UNIT on 127.0.0.1:$STAGING_PORT, env $CONF_DIR/staging.env
  site block   $SITE_FILE, log /var/log/caddy/leibniz-legible-staging.log

  a branch on staging     sudo $STAGING_DIR/deploy/staging.sh BRANCH
  back to main            sudo $STAGING_DIR/deploy/staging.sh --main
  a new password          sudo $KIT_DIR/staging-install.sh --password
  deploy/README.md §14 has the rest: its own index, a second store, teardown.
DONE
