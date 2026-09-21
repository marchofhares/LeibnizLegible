# Deploying Leibniz Legible

_The runbook for putting the v1 serving layer on a public host: what to buy,
what to copy, what to run, what to watch. The default path is **systemd +
Caddy on a plain VPS**, everything native, with `install.sh` doing the
bootstrap; the alternative is **the container stack**
(`docker-compose.prod.yml`). Both run the same app from the same environment
variables. Every command below is meant to be pasted._

## What is deployed, and what is not

| Piece | What | Where it comes from |
| --- | --- | --- |
| the app | `leibniz serve`: FastAPI under uvicorn on localhost — JSON API, IIIF manifests + annotations, the viewer. Read-only. | this repository |
| the store | one SQLite file, the serving copy of `data/inventory.sqlite` | copied from the machine that ran the pipeline |
| Meilisearch | the search index (typo tolerance) | built **on the server** from the store, in an hour or two |
| Caddy | TLS certificate, compression, headers, the reverse proxy, the access log | `deploy/Caddyfile` |
| the images | the 395 GB image cache plus thumbnails, on object storage behind `images.leibnizlegible.com` | uploaded once from the desktop (§12) |

**The VPS never touches image traffic.** The viewer and the manifests point at
the image mirror (or, with `LEIBNIZ_IMAGE_BASE_URL` unset, at the GWLB's own
endpoints). **Nothing on the server is precious**: the store is a copy, the
index is rebuilt from it, and the mirror is the cache re-uploaded.

## 1. Sizing

| | |
| --- | --- |
| RAM | **8 GB comfortable, 4 GB probably enough — measure before you buy.** The whole corpus is only about **0.59 GB of transcription text** (13.5 M lines × 43.9 chars mean, measured from `reports/philiumm-repro.lines.jsonl`), roughly 2.5 KB per page document. Meilisearch's index runs a few times that, so it is single-digit GB, not tens. Build it once on the desktop (`docker compose up -d meilisearch && leibniz index build --backend meili`, then `docker system df -v \| grep meili_data`) and buy for the number you see plus the OS. 4 GB also wants `MEILI_MAX_INDEXING_MEMORY=2GiB`. |
| Disk | **80 GB SSD.** The v1 serving store measures **15 GB** (measured 2026-09-20, not estimated: 13.5 M line rows whose baseline and polygon JSON dwarf the 0.59 GB of text). Add the Meilisearch index, the OS, a 4 GB swap file and the venv, and about 30 GB is in use with comfortable headroom for a rebuild alongside the old index. 40 GB would work but leaves no room to hold two index generations at once. |
| CPU | 2 vCPU; `LEIBNIZ_WORKERS=2`. **Arm64 is fully supported and usually the cheapest way to buy RAM** (Hetzner CAX, Oracle Ampere, Scaleway COPARM): `install.sh` fetches the `meilisearch-linux-aarch64` build, the lockfile carries Arm wheels, uv ships an Arm CPython, Caddy has Arm packages. Nothing else changes. Note that Hetzner offers Ampere only in its EU locations. |
| Network | inbound 80/443 only; outbound to Let's Encrypt, GitHub and PyPI during install. Nothing here calls the GWLB — the visitor's browser does. |
| OS | Debian 12 or Ubuntu 24.04 (what `install.sh` targets). |
| Provider | Anything with the above. Hetzner's US locations cost two to three times its German ones for the same plan, so check the location before reading the price. The public base URL is the project's domain, not the host, so **moving provider later costs nothing** — no IIIF identifier changes. |
| DNS | an A (and AAAA) record for the host name, and one for `www`, in place **before** Caddy starts so it can obtain its certificate. On Cloudflare set both to **DNS only** (grey cloud): the orange cloud terminates TLS at the edge and Caddy's certificate challenge fails behind it. Turn the proxy on later if you want it, and then set SSL/TLS to *Full (strict)* and `LEIBNIZ_RATE_LIMIT=0` (§8). The `images.` record R2 created stays proxied. |

## 2. On the desktop: the serving copy of the store

From the repository checkout on the machine that holds the store (the WSL2
box that ran the corpus):

```bash
deploy/prepare-store.sh data/inventory.sqlite inventory-serving.sqlite
```

This checkpoints the WAL, writes a compact single-file copy with `VACUUM INTO`
(rollback-journal mode: no `-wal` sidecar to ship, and the app's read-only
connections are happy), runs `integrity_check`, prints the row counts, the
size and the SHA-256. Budget about **35 seconds per gigabyte**, so roughly ten
minutes for the v1 store; most of it is the `VACUUM INTO`, which prints
nothing at all while it runs.

Its `lines` count is every row in the table, which is slightly higher than the
"lines transcribed" figure in `STATUS.md`: segmentation writes a row per
detected line and recognition fills in the text afterwards, so the handful
that never got text (about 13 k of 13.5 M for v1) are counted here and not
there. Both numbers being a little apart is correct; the recognised count is
what `/api/stats` reports once the index is built. Then, once §3 has created the directory on the server:

```bash
rsync -avP inventory-serving.sqlite root@HOST:/var/lib/leibniz-legible/inventory.sqlite
ssh root@HOST 'sha256sum /var/lib/leibniz-legible/inventory.sqlite && chown leibniz:leibniz /var/lib/leibniz-legible/inventory.sqlite'
```

Compare the checksum with the one `prepare-store.sh` printed. A resumable
transfer of a few GB over a home uplink is the slowest step of the whole
deployment; `rsync -P` resumes if it drops.

## 3. On the server: bootstrap

As root, on a fresh Debian/Ubuntu host (the repository must be public by
then, or the clone inside the script needs `REPO_URL` with a token):

```bash
curl -fsSL https://raw.githubusercontent.com/marchofhares/leibnizlegible/main/deploy/install.sh | bash
```

`install.sh` is idempotent — re-run it after a `git pull` to update. It:

1. installs `git curl openssl rsync`;
2. creates the system users `leibniz` and `meilisearch` and the directories
   `/opt/leibniz-legible` (the checkout + venv), `/var/lib/leibniz-legible`
   (the store), `/var/lib/meilisearch` (the index), `/etc/leibniz-legible`,
   `/etc/meilisearch`;
3. clones the repository and builds the venv **as the `leibniz` user** (git
   and uv both run as that user; `uv sync --frozen --no-dev --extra web`,
   managed CPython 3.12 under the checkout's `.uv/`);
4. installs the Meilisearch binary (the pinned release the kit was verified
   against, `MEILI_VERSION` in the script; only when absent), writes
   `/etc/meilisearch/env` with a **fresh random master key**, installs and
   starts `meilisearch.service` (bound to `127.0.0.1:7700`);
5. installs Caddy from its apt repository, puts `deploy/Caddyfile` in place
   (the stock one is kept as `Caddyfile.dist`), and a systemd drop-in that
   feeds Caddy `/etc/leibniz-legible/caddy.env`;
6. adds a 4 GB swap file if the image has none (insurance against an OOM kill
   part-way through the index build) and sizes
   `MEILI_MAX_INDEXING_MEMORY` to half of the box's RAM;
7. installs `/etc/leibniz-legible/env` from `env.example` (only if absent) and
   `leibniz-legible.service`, enabled but **not started** — it needs the store
   and the index first. Caddy is restarted only once `caddy.env` names a real
   domain, so a placeholder never hits Let's Encrypt.

Doing it by hand is the same six steps; the script is short and commented.

## 4. Configure

Two files, both installed from their `.example`:

- `/etc/leibniz-legible/caddy.env` — `LEIBNIZ_DOMAIN=leibniz.example.org`.
- `/etc/leibniz-legible/env` — set `LEIBNIZ_BASE_URL=https://leibniz.example.org`
  (it is embedded in every IIIF manifest and annotation id, so choose it once)
  and `MEILI_API_KEY` to the **restricted search key**, which you create once
  Meilisearch is running:

```bash
export MEILI_MASTER_KEY="$(sed -n 's/^MEILI_MASTER_KEY=//p' /etc/meilisearch/env)"
/opt/leibniz-legible/deploy/meili-search-key.sh     # prints the key → MEILI_API_KEY
```

The serving process then holds a key that can search, read index statistics
and the build-metadata document, and nothing else. The master key never leaves
`/etc/meilisearch/env` (mode 0640, `root:meilisearch`).

Everything else in `env` has a sensible default; `leibniz serve --help` lists
the same options. Reload Caddy after editing its env:
`systemctl restart caddy`.

## 5. Build the index

One pass over the store, as the service user, detached from your SSH session
and logged to the journal:

```bash
systemd-run --unit=leibniz-index --uid=leibniz --gid=leibniz \
  -p WorkingDirectory=/opt/leibniz-legible \
  --setenv=LEIBNIZ_DB_PATH=/var/lib/leibniz-legible/inventory.sqlite \
  --setenv=MEILI_MASTER_KEY="$(sed -n 's/^MEILI_MASTER_KEY=//p' /etc/meilisearch/env)" \
  /opt/leibniz-legible/.venv/bin/leibniz index build --backend meili
journalctl -fu leibniz-index
```

What to expect, measured on the first deployment (2 vCPU, 4 GB, the 15 GB
v1 store): the corpus statistics first — five scans of the `lines` table,
about **five minutes** — then documents in batches of 2,000, each awaited on
Meilisearch's task queue. The whole build took **5 h 33 m** wall clock for
just under 236 k pages, of which only 32 minutes was CPU: it is bound by
reading 13.5 M line rows off disk, not by Meilisearch. Budget an evening,
not an afternoon, and leave it alone — it is a systemd unit, so closing the
SSH session does not touch it. The `MEILI_MAX_INDEXING_MEMORY` cap in
`/etc/meilisearch/env` keeps the box responsive meanwhile; a 4 GB box dips
a few hundred MB into swap, which is what the swap file `install.sh` creates
is for.

**The document count is lower than the recognised-page count, and that is
correct.** v1 indexed 235,723 of 236,210 recognised pages. A page is
indexable only if at least one of its lines carries text, and a few hundred
pages came out of recognition with every line empty. Confirm the difference
on any store with:

```bash
sudo -u leibniz /opt/leibniz-legible/.venv/bin/python -c "
import sqlite3
c = sqlite3.connect('file:/var/lib/leibniz-legible/inventory.sqlite?mode=ro', uri=True)
r = c.execute(\"SELECT COUNT(*) FROM pages WHERE status='recognized'\").fetchone()[0]
t = c.execute(\"SELECT COUNT(DISTINCT page_id) FROM lines WHERE text IS NOT NULL AND text != ''\").fetchone()[0]
print('recognised', r, '| with text', t, '| difference', r - t)
"
```

The build **replaces** the index wholesale (drop →
create → settings → documents), so re-running it is safe and is how a new
corpus run (C4) goes live. Check the result:

```bash
sudo -u leibniz env MEILI_API_KEY=… /opt/leibniz-legible/.venv/bin/leibniz index status --backend meili
```

**Fallback without Meilisearch:** `leibniz index build` (default `--backend
fts5`) writes a single SQLite FTS5 file, `LEIBNIZ_INDEX_PATH`; set
`LEIBNIZ_SEARCH_BACKEND=fts5`. Prefix matching and the early-modern folding
(u≡v, i≡j, ſ→s, diacritics) work; typo tolerance does not.

## 6. Start and verify

```bash
systemctl start leibniz-legible
journalctl -fu leibniz-legible                 # "Serving Leibniz Legible on http://127.0.0.1:8000 …"
curl -s http://127.0.0.1:8000/healthz          # {"status":"ok","store":true,"search":{"backend":"meili","ok":true}}
curl -s https://$LEIBNIZ_DOMAIN/healthz        # the same, through Caddy and TLS
curl -s "https://$LEIBNIZ_DOMAIN/api/search?q=calculemus" | head -c 400
curl -s https://$LEIBNIZ_DOMAIN/manifests/00068642 | head -c 300   # ids must start with LEIBNIZ_BASE_URL
```

Then open the site: search, open a work, open a page, switch to DE, click
"Report an error" (it must open the repository's issue form with the page id
filled in). The About page's figures come from `/api/stats`, which the index
build recorded.

`/healthz` answers `200` while the store is present, with `"status":
"degraded"` and `"search": {"ok": false}` when Meilisearch is down (pages and
works still serve; search answers `503`). Point an uptime monitor at it.

## 7. Measure

SPECS §3.3 asks for **search p95 under 500 ms**. Measure it the way a user
meets it, through the whole path:

```bash
/opt/leibniz-legible/.venv/bin/leibniz index bench --url https://$LEIBNIZ_DOMAIN --n 200
/opt/leibniz-legible/.venv/bin/leibniz index bench --url https://$LEIBNIZ_DOMAIN --n 200 --concurrency 4
```

It runs a built-in list of fifty Latin/French/German queries (names, terms,
a few misspellings) and prints wall-clock and backend p50/p95/max; exit code
1 means the criterion is missed. `--queries FILE` takes your own list, one
per line. Launches are paced to 8 per second by default, just under the
app's own per-client limit, so the run measures the server and not its own
`429`s (those are counted apart as "rate-limited" and never enter the
percentiles). For a load test rather than a latency measurement, run it on
the host against `http://127.0.0.1:8000` with `--rate 0 --concurrency 4`; the
rate limiter will answer part of it with `429`, which is the point of the
limiter. If p95 is over the bar:

- `backend p95` far below `wall clock p95` → the time is outside Meilisearch:
  TLS/proxy, the app's snippet rendering, gzip. Check `LEIBNIZ_WORKERS`
  (one per core) and that Caddy is not swapping.
- `backend p95` itself high → the index is not in RAM. `free -m` should show
  the index size as cached; if not, the box is too small, or the indexing
  memory cap starved the page cache during the build (it recovers).
- Everything fine locally (`--url http://127.0.0.1:8000`) but slow from
  outside → the network, not the app.

`LEIBNIZ_WORKERS` above 1 is safe for latency: the multi-worker path binds
its own listening socket so that `TCP_NODELAY` is set on every connection
(uvicorn's own socket leaves Nagle's algorithm on there, which cost 40 ms per
kept-alive request in testing).

## 8. Harden

What is already on, and where to turn the knobs:

- **Rate limit (app).** `LEIBNIZ_RATE_LIMIT=10` requests/second per client
  address with `LEIBNIZ_RATE_BURST=40`, on `/api/`, `/manifests/`,
  `/annotations/` — never on the viewer or `/static/`. Over the limit: `429`
  with `Retry-After`. Each worker keeps its own buckets, so the effective
  allowance is `LEIBNIZ_WORKERS` × the rate. The viewer makes one API call per
  navigation; a scholar scripting the API stays under 10/s without noticing.
- **Rate limit (edge).** If you put **Cloudflare** in front, set
  `LEIBNIZ_RATE_LIMIT=0` and use a Cloudflare rate-limiting rule instead —
  otherwise the app keys on Cloudflare's addresses and every visitor shares a
  handful of buckets. A Caddy built with `caddy-ratelimit` is the other
  option; the block is in the Caddyfile, commented out.
- **Headers.** The app sends a Content Security Policy (`script-src 'self'`;
  images and `info.json` from any https origin because the store says where a
  work's images live), `nosniff`, a referrer policy, a permissions policy.
  Caddy adds HSTS and drops `Server`. Framing is allowed on purpose (a
  read-only viewer with no sessions; embedding it is a feature).
- **CORS.** `Access-Control-Allow-Origin: *` on the JSON routes, so Mirador
  or Universal Viewer on another site can load our manifests (deliverable D7).
- **Read-only store.** Every request opens the store with `mode=ro` and
  `PRAGMA query_only`; the service runs under a hardened systemd sandbox
  (`ProtectSystem=strict`, no capabilities, only `/var/lib/leibniz-legible`
  writable, for SQLite's `-shm` sidecar).
- **Logs, and only logs.** There is no analytics (SPECS). Caddy's access log
  (`/var/log/caddy/leibniz-legible.log`, JSON) holds client addresses and is
  rolled and **deleted after seven days**; uvicorn's access log goes to the
  journal (`journalctl -u leibniz-legible`; set `SystemMaxUse=` in
  `journald.conf` if the disk is small). Say so in the site's About page if
  you publish a privacy note.
- **`robots.txt`.** Served by the app: human pages open, `/api/`,
  `/manifests/`, `/annotations/` and `/search?` closed — a crawler walking the
  manifests would request every GWLB image of every canvas, on their
  servers.
- **Caching.** API and manifest responses carry `Cache-Control: public,
  max-age=300`; the viewer shell is `no-cache` (revalidated, so a deploy shows
  at once); `/static/*` is cached an hour by Caddy's header.

## 9. Operate

- **Update the app.** `deploy/install.sh` again (pulls, syncs the venv,
  reinstalls the units), then `systemctl restart leibniz-legible`. Or by hand:
  `git -C /opt/leibniz-legible pull && sudo -u leibniz -H uv sync --project
  /opt/leibniz-legible --frozen --no-dev --extra web && systemctl restart
  leibniz-legible`.
- **A new corpus run (C4).** Repeat §2 (new serving copy), §5 (rebuild the
  index; the app keeps serving the old one until the build swaps it in),
  then restart the app so `/api/stats` picks up the new build metadata.
- **Upgrade Meilisearch.** Its on-disk format changes between minor versions
  and a newer binary refuses an older index. `install.sh` never replaces an
  installed binary. To upgrade: stop the service, replace
  `/usr/local/bin/meilisearch` (same download line as the script, new
  version), delete `/var/lib/meilisearch/data.ms`, start it, rebuild the
  index (§5). Keep `MEILI_VERSION` in `install.sh` in step with what runs.
- **Backups.** None needed for the data: the store is a copy, the index is a
  rebuild. Back up `/etc/leibniz-legible`, `/etc/meilisearch` and
  `/etc/caddy` (a few KB) and you can rebuild the host from this file.
- **Disk.** Watch `/var/lib/meilisearch` after a rebuild (the old index is
  dropped first, so the peak is one index) and `/var/log/caddy`.
- **Monitoring.** `/healthz` from an uptime checker; `systemctl status
  leibniz-legible meilisearch caddy`; `journalctl -u leibniz-legible --since
  today | grep -c ' 5[0-9][0-9] '` for server errors.
- **When Meilisearch is down.** Search returns `503` with a plain message;
  works, pages, manifests and the viewer keep working. `/healthz` says
  `degraded`. `systemctl restart meilisearch` and it recovers without a rebuild.

## 10. The container stack

Same app, same variables, three containers, one command:

```bash
cp deploy/env.example .env      # edit: LEIBNIZ_DOMAIN, LEIBNIZ_BASE_URL, MEILI_MASTER_KEY (openssl rand -hex 32), LEIBNIZ_DATA_DIR
docker compose -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.prod.yml run --rm app \
    leibniz index build --backend meili --meili-key "$MEILI_MASTER_KEY"
export MEILI_URL=http://127.0.0.1:7700   # or exec into the meilisearch container; then:
deploy/meili-search-key.sh              # → MEILI_API_KEY in .env, then `up -d` again
```

`LEIBNIZ_DATA_DIR` (default `../data` relative to the compose file) is
bind-mounted at `/srv/leibniz/data` read-write: even a reader needs to
create SQLite's `-shm` sidecar next to a WAL-mode store. The app and
Meilisearch stay on the internal network; only Caddy publishes 80/443. The
image is built from the repository's `Dockerfile` (uv, non-root, healthcheck
on `/healthz`). Inside the stack `FORWARDED_ALLOW_IPS=*` is right, because
only Caddy can reach the app's port.

## 11. Before going public

- **The GWLB.** The site shows their scans from its own mirror (§12), so
  their servers see none of the viewer's traffic — but the copies are theirs
  in origin, and the relationship matters more than the licence (SPECS
  §7.7). Write to `digitalisierung@gwlb.de` (cc the Leibniz-Archiv) before
  launch: what the site is, that it serves its own copy of the Public Domain
  delivery derivatives with attribution and a link to the original on every
  page, that nothing is fetched from them at serve time, that the project
  competes with no edition and exists as a free open-access resource, a
  contact address, and an open door for their wishes. Include the sixteen
  looping delivery URLs as a courtesy.
- **The repository.** Issues must be enabled (the "Report an error" link
  opens `.github/ISSUE_TEMPLATE/transcription-error.yml`); `LICENSE` is
  Apache-2.0 at the root; the About page names the licences of images,
  catalogue and transcriptions.
- **The legal memo** (SPECS §7.5) is recorded in `reports/release-checklist.md`
  as *not* gating the web app; the datasets are the heavier surface.
- **First-day watch.** Tail the Caddy log for a few hours; a crawler that
  ignores `robots.txt` shows up as a burst of `/manifests/` or `/api/` hits
  from one address and meets the rate limit. If one address is hammering
  image-heavy pages, Caddy can block it in a line (`@bad remote_ip …`,
  `respond @bad 403`).

## 12. The image mirror

The public site serves the GWLB's delivery scans from its own storage
(STATUS.md, Divergences). The mirror is the A2 image cache uploaded **as it
is** — `data/images/{work_id}/{seq:04d}.jpg`, 236,779 files, 395.6 GB —
plus a `thumbs/` tree in the same layout. With `LEIBNIZ_IMAGE_BASE_URL` set,
the app derives every image URL from that layout; the polygons were computed
on exactly these files, so the overlay is pixel-exact by construction.

**Where.** Cloudflare R2 is the natural home when the domain is on
Cloudflare: object storage at about $0.015 per GB-month (≈ $6 a month for
the corpus), no egress fees, and a custom domain bound to the bucket in the
dashboard with Cloudflare's CDN caching in front. Any S3-compatible bucket
behind a hostname works the same way.

1. Cloudflare dashboard → R2 → *Create bucket* `leibniz-images`. A
   **location hint** only places the data; a **jurisdiction** (European
   Union) is a residency guarantee and *changes the S3 endpoint* — see step
   2. Either is fine here. Bucket → *Settings* → *Custom Domains* → add
   `images.leibnizlegible.com` (Cloudflare creates the DNS record, proxied;
   leave it that way — that is the CDN cache). Same page, *CORS Policy* →
   *Edit*:

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 86400
  }
]
```

   The viewer does not need this (OpenSeadragon runs with
   `crossOriginPolicy: false` and never sends a preflight); it is so that
   *other people's* browser tools can read the pixels, which is the point of
   a public-domain mirror.
2. The token lives **outside** the bucket: left sidebar → *R2 Object
   Storage* → the `{} API` button on the overview page → *Manage API
   tokens*, or go straight to
   `https://dash.cloudflare.com/?to=/:account/r2/api-tokens`. Create one
   with *Object Read & Write*, scoped to this bucket only. Copy the Access
   Key ID and the Secret Access Key — the secret is shown once.
   The **endpoint** is the *S3 API* value on the bucket's Settings page,
   **with the trailing `/leibniz-images` removed** (rclone wants the bare
   origin; the bucket name comes from the command). An EU-jurisdiction
   bucket carries an extra `.eu.`:

   | Bucket | Endpoint |
   | --- | --- |
   | default | `https://<account-id>.r2.cloudflarestorage.com` |
   | EU jurisdiction | `https://<account-id>.eu.r2.cloudflarestorage.com` |

3. On the desktop, thumbnails first, then the upload with
   [rclone](https://rclone.org/) (resumable, parallel, checksummed).
   Writing the config file beats the interactive wizard:

```bash
curl -fsSL https://rclone.org/install.sh | sudo bash   # the distro package is often too old for `provider = Cloudflare`
mkdir -p ~/.config/rclone
cat > ~/.config/rclone/rclone.conf <<'EOF'
[r2]
type = s3
provider = Cloudflare
access_key_id = PASTE_ACCESS_KEY_ID
secret_access_key = PASTE_SECRET_ACCESS_KEY
endpoint = https://<account-id>.eu.r2.cloudflarestorage.com
acl = private
EOF
chmod 600 ~/.config/rclone/rclone.conf

rclone lsd r2:                                     # must list leibniz-images — prove the token before a transfer measured in hours
uv run leibniz images thumbs --images /path/to/cache   # data/thumbs/, all cores, resumable

# Thumbnails first: 7 GB proves the whole path in an hour instead of finding
# a broken token 40 hours in.
rclone sync data/thumbs r2:leibniz-images/thumbs --transfers 32 --fast-list --progress

# `--exclude` is load-bearing. `sync` makes the destination identical to the
# source, and data/images has no thumbs/ directory, so without it this DELETES
# the thumbnails you just uploaded — silently, and again on every later re-sync.
rclone sync data/images r2:leibniz-images --exclude "thumbs/**" \
  --transfers 16 --checkers 16 --fast-list --progress

rclone check data/images r2:leibniz-images --one-way   # MD5 of every object against the local file
```

   **Make it survive.** Forty hours is longer than a terminal window lives.
   Run it inside `tmux` (`tmux new -s upload`, detach with Ctrl-B then D,
   return with `tmux attach -t upload`) so closing the window does not send
   the job a hangup. On Windows, also set the machine never to sleep while
   plugged in: WSL stops with the host, and a sleeping laptop is the most
   common way these transfers die overnight.

   The upload is bound by your uplink, and home uplinks are usually slower
   than advertised. **Measure rather than hope:** the store transfer in §2
   prints its real rate, and the image upload takes the same route. At
   2.8 MB/s — a measured figure from the first deployment — 400 GB is about
   **40 hours**, against 9 hours at 100 Mbit/s. Thumbnails are perhaps 7 GB
   and land in an hour. Keep the WSL2 window open for the duration (WSL stops
   when its last window closes); `rclone sync` resumes where it left off if
   it is interrupted. The R2 free tier covers the first 10 GB; the rest
   bills monthly.

   **Do not wait for it.** The mirror is a switch, so the sensible order is:
   leave `LEIBNIZ_IMAGE_BASE_URL` unset and launch with images coming from
   the GWLB (the code's default), which makes the viewer fully testable on
   day one; run the upload over the following days; then set the variable,
   restart, and confirm with `check-mirror`. Announcing and writing to the
   GWLB (§11) belongs after the flip, so the note describes the steady state
   rather than a transition.
4. Verify from anywhere, against the store's own cache manifest:

```bash
uv run leibniz images check-mirror --base-url https://images.leibnizlegible.com            # 500 random pages + thumbnails
uv run leibniz images check-mirror --base-url https://images.leibnizlegible.com --sample 0  # every page (hours)
```

5. On the server, `LEIBNIZ_IMAGE_BASE_URL=https://images.leibnizlegible.com`
   in `/etc/leibniz-legible/env`, then `systemctl restart leibniz-legible`.
   `curl -s https://leibnizlegible.com/api/pages/00068642:0001 | grep -o
   '"image_url":"[^"]*"'` must show the mirror; `/api/stats` says
   `"images": {"origin": "mirror", …}`; the About page's image paragraphs
   switch wording by themselves.

Optional, in Cloudflare → Caching → *Cache Rules*: hostname
`images.leibnizlegible.com`, cache eligible, edge TTL one month. The objects
never change (a re-fetched derivative would replace the same key; purge the
cache then). A new corpus run changes nothing here.
