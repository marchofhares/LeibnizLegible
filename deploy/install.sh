#!/usr/bin/env bash
# deploy/install.sh — bootstrap a Debian 12 / Ubuntu 24.04 server for
# Leibniz Legible: system users, directories, uv + the app's venv, Meilisearch,
# Caddy, and the systemd units. Idempotent — re-run it to update the app.
# Run as root. What it does NOT do: copy the store, build the index, edit the
# configuration files, start the app. deploy/README.md walks through those.
#
#   curl -fsSL https://raw.githubusercontent.com/marchofhares/leibnizlegible/main/deploy/install.sh | bash
#   # or, from a checkout:  sudo deploy/install.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/marchofhares/leibnizlegible.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="${APP_DIR:-/opt/leibniz-legible}"
DATA_DIR="${DATA_DIR:-/var/lib/leibniz-legible}"
CONF_DIR="${CONF_DIR:-/etc/leibniz-legible}"
MEILI_VERSION="${MEILI_VERSION:-v1.53.2}"   # the release this kit was verified against

[[ $EUID -eq 0 ]] || { echo "run as root (sudo)" >&2; exit 1; }

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

say "packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q git curl ca-certificates gnupg openssl rsync sudo

say "users and directories"
id -u leibniz >/dev/null 2>&1 \
  || useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin leibniz
id -u meilisearch >/dev/null 2>&1 \
  || useradd --system --home-dir /var/lib/meilisearch --shell /usr/sbin/nologin meilisearch
install -d -o leibniz -g leibniz -m 0755 "$APP_DIR"
install -d -o leibniz -g leibniz -m 0750 "$DATA_DIR"
install -d -o meilisearch -g meilisearch -m 0750 /var/lib/meilisearch
install -d -m 0750 "$CONF_DIR" /etc/meilisearch

say "the app: $REPO_URL ($BRANCH) → $APP_DIR"
# Everything under $APP_DIR is owned and operated by the service user: git
# refuses to act as root on another user's checkout ("dubious ownership").
as_leibniz() { sudo -u leibniz -H "$@"; }
chown -R leibniz:leibniz "$APP_DIR"
if [[ ! -d "$APP_DIR/.git" ]]; then
  as_leibniz git clone --quiet --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
else
  as_leibniz git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
  as_leibniz git -C "$APP_DIR" checkout --quiet "$BRANCH"
  as_leibniz git -C "$APP_DIR" pull --ff-only --quiet origin "$BRANCH"
fi
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh
fi
# The venv belongs to the service user; uv fetches a managed CPython 3.12.
# Its cache and interpreter live under the checkout's .uv/ (gitignored).
as_leibniz env UV_CACHE_DIR="$APP_DIR/.uv/cache" UV_PYTHON_INSTALL_DIR="$APP_DIR/.uv/python" \
  uv sync --project "$APP_DIR" --python 3.12 --frozen --no-dev --extra web
"$APP_DIR/.venv/bin/leibniz" --version

say "meilisearch $MEILI_VERSION"
# Installed only when absent: a new Meilisearch version cannot read an index
# built by an older one, so upgrading is a deliberate step (README §9), never
# a side effect of re-running this script.
if [[ ! -x /usr/local/bin/meilisearch ]]; then
  case "$(uname -m)" in
    x86_64) asset=meilisearch-linux-amd64 ;;
    aarch64|arm64) asset=meilisearch-linux-aarch64 ;;
    *) echo "no Meilisearch build for $(uname -m)" >&2; exit 1 ;;
  esac
  curl -fsSL -o /usr/local/bin/meilisearch.new \
    "https://github.com/meilisearch/meilisearch/releases/download/$MEILI_VERSION/$asset"
  chmod 0755 /usr/local/bin/meilisearch.new
  mv /usr/local/bin/meilisearch.new /usr/local/bin/meilisearch
fi
/usr/local/bin/meilisearch --version
if ! /usr/local/bin/meilisearch --version | grep -q "${MEILI_VERSION#v}"; then
  echo "note: installed Meilisearch differs from the pinned $MEILI_VERSION; see deploy/README.md §9 before upgrading"
fi
if [[ ! -f /etc/meilisearch/env ]]; then
  install -m 0640 -o root -g meilisearch "$APP_DIR/deploy/meilisearch.env.example" /etc/meilisearch/env
  sed -i "s|^MEILI_MASTER_KEY=.*|MEILI_MASTER_KEY=$(openssl rand -hex 32)|" /etc/meilisearch/env
  echo "wrote /etc/meilisearch/env with a fresh master key"
fi
install -m 0644 "$APP_DIR/deploy/meilisearch.service" /etc/systemd/system/meilisearch.service

say "caddy"
if ! command -v caddy >/dev/null 2>&1; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -q && apt-get install -y -q caddy
fi
if ! grep -q 'Leibniz Legible' /etc/caddy/Caddyfile 2>/dev/null; then
  [[ -f /etc/caddy/Caddyfile ]] && cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.dist
  install -m 0644 "$APP_DIR/deploy/Caddyfile" /etc/caddy/Caddyfile
fi
[[ -f "$CONF_DIR/caddy.env" ]] || install -m 0644 "$APP_DIR/deploy/caddy.env.example" "$CONF_DIR/caddy.env"
install -d /etc/systemd/system/caddy.service.d /var/log/caddy
chown caddy:caddy /var/log/caddy
cat > /etc/systemd/system/caddy.service.d/leibniz.conf <<UNIT
[Service]
EnvironmentFile=-$CONF_DIR/caddy.env
UNIT

say "the app's unit and configuration"
[[ -f "$CONF_DIR/env" ]] || install -m 0640 -o root -g leibniz "$APP_DIR/deploy/env.example" "$CONF_DIR/env"
install -m 0644 "$APP_DIR/deploy/leibniz-legible.service" /etc/systemd/system/leibniz-legible.service
systemctl daemon-reload
systemctl enable --now meilisearch
systemctl enable leibniz-legible   # started once the store and the index exist
systemctl enable caddy
if grep -qE 'example\.org|^LEIBNIZ_DOMAIN=$' "$CONF_DIR/caddy.env"; then
  echo "caddy: LEIBNIZ_DOMAIN in $CONF_DIR/caddy.env is still the placeholder — set it, then: systemctl restart caddy"
else
  systemctl restart caddy
fi

cat <<NEXT

Done. What is left is yours — deploy/README.md walks through it:

  1. Copy the serving store (deploy/prepare-store.sh on the desktop, then rsync)
     to $DATA_DIR/inventory.sqlite and chown it leibniz:leibniz.
  2. Edit $CONF_DIR/caddy.env (LEIBNIZ_DOMAIN), then: systemctl restart caddy
  3. Create the search key: export MEILI_MASTER_KEY from /etc/meilisearch/env,
     run $APP_DIR/deploy/meili-search-key.sh, put the key in $CONF_DIR/env
     as MEILI_API_KEY; set LEIBNIZ_BASE_URL there too.
  4. Build the index as the service user (README §5, a systemd-run one-liner).
  5. systemctl start leibniz-legible; curl -s http://127.0.0.1:8000/healthz
  6. $APP_DIR/.venv/bin/leibniz index bench --url https://YOUR-DOMAIN
NEXT
