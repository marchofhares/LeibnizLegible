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

The build **replaces** the index wholesale, so re-running it is safe and is
how a new corpus run (C4) goes live. Since 2026-10 it builds beside the live
index (`leibniz_pages__next`, settings, documents) and swaps the two in one
Meilisearch task at the end, then deletes the old generation: search keeps
answering from the old index throughout (before, the build dropped it first
and search answered from a half-filled index for hours). Both generations
sit on disk until the swap — the sizing in §1 allows for it. Since 2026-10 it also finds the scans the GWLB
registered under two folio labels (`src/leibniz/images/twins.py`), indexes
each once — a two-page spread as its two halves — and writes the groups to
`/var/lib/leibniz-legible/<index uid>.twins.json`, which the app reads at
start: restart `leibniz-legible` after a build. A partial build (`--work`,
`--set`, `--limit`) leaves that file as it was. A change of ranking or typo
rules alone needs no rebuild: `leibniz index settings` pushes them (it
refuses an index built before the folded metadata field existed). Check the
result:

```bash
sudo -u leibniz env MEILI_API_KEY=… /opt/leibniz-legible/.venv/bin/leibniz index status --backend meili
```

**Fallback without Meilisearch:** `leibniz index build` (default `--backend
fts5`) writes a single SQLite FTS5 file, `LEIBNIZ_INDEX_PATH`; set
`LEIBNIZ_SEARCH_BACKEND=fts5`. Prefix matching and the early-modern folding
(u≡v, i≡j, ſ→s, diacritics) work; typo tolerance does not.

### The letters (once, and whenever correspSearch changes)

```bash
sudo -u leibniz /opt/leibniz-legible/.venv/bin/leibniz catalog letters \
  --db /var/lib/leibniz-legible/inventory.sqlite \
  --cache /var/lib/leibniz-legible/cache/correspsearch
systemctl restart leibniz-legible
```

Eduard Bodemann's catalogue of the letters (1889), letter by letter from
correspSearch (BBAW; CC BY 4.0; data from the Portal Der deutsche Brief im
18. Jahrhundert): about 1,550 requests at one a second, resumable from the
cache directory, written to `/var/lib/leibniz-legible/letters.json`. It names
the letter convolutes the catalogue records leave unnamed and feeds
`/letters`; the attribution travels with every page that shows it.

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

- **See it on staging first** (§14): `deploy/staging.sh BRANCH` puts any
  pushed branch on `staging.leibnizlegible.com`, behind a password, against
  the same store and index; merge and deploy once it looks right there.
- **Update the app.** `deploy/install.sh` again (pulls, syncs the venv,
  reinstalls the units), then `systemctl restart leibniz-legible`. Or by hand,
  running git and uv as the service user as `install.sh` does (git refuses to
  work as root in the leibniz-owned checkout: "dubious ownership"):

  ```bash
  sudo -u leibniz -H git -C /opt/leibniz-legible pull --ff-only
  sudo -u leibniz -H env UV_CACHE_DIR=/opt/leibniz-legible/.uv/cache \
    UV_PYTHON_INSTALL_DIR=/opt/leibniz-legible/.uv/python \
    uv sync --project /opt/leibniz-legible --frozen --no-dev --extra web
  systemctl restart leibniz-legible
  curl -s http://127.0.0.1:8000/healthz    # {"status":"ok",…}
  ```

  The shell names what it loads by content — its stylesheet and boot script
  by hash (`?v=…`), the viewer's ES modules under `/static/m/<build>/`, a
  path that changes when any module does — so a deploy reaches returning
  readers at once and as one consistent set, although Caddy lets browsers
  cache `/static/*` for an hour. (Until 2026-10-06 the modules `app.js`
  imports kept plain addresses, and for an hour after a deploy a returning
  reader could run the new `app.js` against cached old ones.)
- **A new corpus run (C4).** Repeat §2 (new serving copy), §5 (rebuild the
  index; the app keeps serving the old one until the build swaps it in),
  then restart the app so `/api/stats` picks up the new build metadata.
- **Upgrade Meilisearch.** Its on-disk format changes between minor versions
  and a newer binary refuses an older index. `install.sh` never replaces an
  installed binary. To upgrade: stop the service, replace
  `/usr/local/bin/meilisearch` (same download line as the script, new
  version), delete `/var/lib/meilisearch/data.ms`, start it, rebuild the
  index (§5). Keep `MEILI_VERSION` in `install.sh` in step with what runs.
- **Backups.** None needed for this app's data: the store is a copy, the
  index is a rebuild. Back up `/etc/leibniz-legible`, `/etc/meilisearch`,
  `/etc/caddy` and, once Calculemus is installed, `/etc/calculemus` (a few
  KB) and you can rebuild the host from this file — except the game's own
  data, which §13 covers.
- **Disk.** Watch `/var/lib/meilisearch` during a rebuild (both generations
  sit on disk until the swap, so the peak is two indexes; `du -sh
  /var/lib/meilisearch` before a build is roughly what the second one will
  take) and `/var/log/caddy`.
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
sudo apt install -y unzip                              # the install script unpacks a zip and says so unhelpfully if this is missing
curl -fsSL https://rclone.org/install.sh | sudo bash   # Ubuntu 24.04 ships 1.60.1 (2022); R2 wants something current
mkdir -p ~/.config/rclone
cat > ~/.config/rclone/rclone.conf <<'EOF'
[r2]
type = s3
provider = Cloudflare
access_key_id = PASTE_ACCESS_KEY_ID
secret_access_key = PASTE_SECRET_ACCESS_KEY
endpoint = https://<account-id>.eu.r2.cloudflarestorage.com
acl = private
# A bucket-scoped token cannot create or inspect buckets; without this rclone
# tries to and fails before transferring anything.
no_check_bucket = true
EOF
chmod 600 ~/.config/rclone/rclone.conf

# Prove the token INSIDE the bucket. `rclone lsd r2:` calls ListBuckets, which
# is an account-level permission a bucket-scoped token does not have and should
# not have: it answers 403 even when everything is correct.
rclone lsjson r2:leibniz-images                    # `[]` on an empty bucket = authenticated
echo ok > /tmp/r2-probe.txt && rclone copy /tmp/r2-probe.txt r2:leibniz-images/ \
  && rclone ls r2:leibniz-images && rclone delete r2:leibniz-images/r2-probe.txt
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

## 13. Sibling apps on this host — Calculemus

The game **Calculemus!** — its own repository and deployment kit; a Node 22 /
Fastify server with one SQLite file — runs on this same VPS under
`calculemus.leibnizlegible.com`: system user `calculemus`, checkout in
`/opt/calculemus`, Node in `/opt/node`, listening on `127.0.0.1:3000`. Its
kit does its own work; this section is what touches this host and this site.

1. **DNS.** A grey-cloud (DNS only) A and AAAA record for `calculemus` in the
   Cloudflare zone, in place **before** the site block goes live — exactly
   what §1 requires for the apex, for the same reason: Caddy's certificate
   challenge fails behind the orange cloud.
2. **The one-time manual edit on the live box.** `install.sh` copies
   `deploy/Caddyfile` only the first time (it skips whenever
   `/etc/caddy/Caddyfile` already says "Leibniz Legible"), so a box installed
   before the import line existed does not have it. Add, at the **end** of
   `/etc/caddy/Caddyfile`:

```
import /etc/caddy/conf.d/*.caddy
```

   then validate, then reload:

```bash
install -d /etc/caddy/conf.d
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemctl reload caddy
```

   Reload, not restart: no downtime, the apex stays up. If `validate` fails,
   nothing has changed yet — the running Caddy keeps its old configuration
   until the reload. A glob that matches no file is fine (a warning in the
   journal, not an error). Each sibling block names its domain literally,
   never as a `{$VAR:localhost}` fallback, which would duplicate this file's
   fallback address and make Caddy refuse the whole configuration.
3. **Everything else is Calculemus's own kit.** `deploy/install.sh` in the
   Calculemus repository creates the user, installs Node to `/opt/node`,
   clones and builds the game, installs its unit and the backup timer, keeps
   its env in `/etc/calculemus/env`, and writes the site block
   `/etc/caddy/conf.d/calculemus.caddy`. Its runbook is `deploy/README.md` in
   that repository.
4. **Memory.** This box has 4 GB, and Meilisearch relies on the page cache
   for its p95 (§7). The game's server idles around 100–150 MB RSS, but its
   build (`pnpm build`) peaks around 500 MB: run a Calculemus install or
   update when no index build (§5) is running.
5. **Backups.** `/etc/calculemus` joins the small configuration set worth
   backing up (§9). `/var/lib/calculemus` (`game.sqlite`) is the first data
   on this box that is **not** a rebuildable copy: the game's own systemd
   timer keeps daily SQLite backups in `/var/lib/calculemus/backups/`, on the
   same disk; a copy off the host is the operator's.
6. **The switch.** `LEIBNIZ_CALCULEMUS_URL`, unset by default: no link to the
   game anywhere on leibnizlegible.com, and nothing about it in the served
   HTML. To show the link on the About page, set
   `LEIBNIZ_CALCULEMUS_URL=https://calculemus.leibnizlegible.com` in
   `/etc/leibniz-legible/env` and `systemctl restart leibniz-legible`.

## 14. The staging site

A second copy of the app on this same host, at
`https://staging.leibnizlegible.com`, behind HTTP basic auth, running
whatever branch you point it at against the live serving store and the live
search index. It is for seeing a change on the real server, with the real
data, before anyone else does: push a branch, put it on staging, look, merge,
deploy. It previews **code and pages**. A change to the data itself (a
re-mint, a new model, a rebuilt index) reaches it only the way it reaches
production, through a new serving copy or a new index (below).

The kit is three files in `deploy/` and two scripts, and
`tests/test_deploy_staging.py` holds each file to its production counterpart:

| File | What | Differs from production in |
| --- | --- | --- |
| `leibniz-legible-staging.service` | the unit, same sandbox | the checkout `/opt/leibniz-legible-staging`, `EnvironmentFile=/etc/leibniz-legible/staging.env`, the venv |
| `staging.env.example` | → `/etc/leibniz-legible/staging.env` | `LEIBNIZ_PORT=8001`, `LEIBNIZ_WORKERS=1`, `LEIBNIZ_BASE_URL=https://staging.leibnizlegible.com`, `LEIBNIZ_RATE_LIMIT=0` |
| `staging.caddy.example` | → `/etc/caddy/conf.d/staging.caddy` | `basic_auth`, `X-Robots-Tag "noindex, nofollow"`, the upstream, its own log file |
| `staging-install.sh` | one-time setup, idempotent | — |
| `staging.sh` | a branch onto staging; `--main`, `--status`, `--index`, `--drop-index` | — |

What is **shared** with the live site: the serving store (both processes
open it read-only), Meilisearch and its index (read only, through the same
restricted search key), uv's cache and interpreter under
`/opt/leibniz-legible/.uv/`, Caddy. What is **not**: the checkout, the venv,
the unit, the env file, the port, the access log, and the base URL, which
is embedded in every manifest and annotation id staging serves. **Never
send a staging link to anyone**: its ids are not the real ones, and the
site exists so that you see things first.

### One-time setup

1. **DNS.** In the Cloudflare zone, an A record `staging` pointing at this
   host, DNS only (grey cloud), and an AAAA record if the host has IPv6:
   exactly what §1 asks for the apex and §13 for Calculemus, for the same
   reason (Caddy's certificate challenge fails behind the orange cloud).
   Caddy obtains the certificate at the reload below; a certificate for the
   name appears in the public certificate-transparency logs then, which is
   why the password, not obscurity, is what keeps the site private.
2. **The install**, as root, with a terminal (`ssh -t`) because it asks for
   the user name and the password; the password is hashed by `caddy
   hash-password` on the box and only the hash is written. From the live
   checkout, once `main` carries the kit:

   ```bash
   ssh -t root@HOST /opt/leibniz-legible/deploy/staging-install.sh --user NAME
   ```

   Before that, from a clone of the branch that carries it (the clone is
   only the kit; the script makes the staging checkout itself, as the
   `leibniz` user, from the public repository):

   ```bash
   ssh -t root@HOST 'git clone --branch BRANCH --depth 1 https://github.com/marchofhares/leibnizlegible /opt/leibniz-legible-kit \
     && /opt/leibniz-legible-kit/deploy/staging-install.sh --user NAME --branch BRANCH'
   ```

   It checks its preconditions first and changes nothing if one fails (the
   live site installed and configured, `uv` and `caddy` present, the
   Caddyfile's `import /etc/caddy/conf.d/*.caddy` line from §13 in place).
   Then: the checkout and its venv as the service user; the unit; the env
   file from the example, with the store path, the search key and the image
   origin copied over from the live `/etc/leibniz-legible/env` (an existing
   `staging.env` is left alone); the access log file, created for the
   `caddy` user before anything opens it (`caddy validate` runs as root
   and provisions the log writers, so it would create a missing log as
   root, and the reload, as the caddy user, could not open it: what stopped
   the first install); the site block, validated against the
   whole Caddy configuration before `systemctl reload caddy` (a failed
   validate puts the previous block back and reloads nothing; the live site
   never stops, and neither does it when the reload itself is refused: Caddy
   keeps the configuration it runs); then `staging.sh BRANCH` for the first
   deploy. On a Caddy
   older than 2.8 the directive is written as `basicauth`. The clone under
   `/opt/leibniz-legible-kit` can go afterwards: the staging checkout
   carries the kit, and `main` does after the merge.
3. **Check.** The script ends with `/healthz` on `127.0.0.1:8001` and a
   request to the site without credentials, which must answer `401`. Then,
   in a browser, the page opens with the user name and the password, and:

   ```bash
   curl -s https://leibnizlegible.com/api/stats | head -c 200          # the live figures …
   curl -su NAME https://staging.leibnizlegible.com/api/stats | head -c 200   # … the same, from the same index
   ```

### Everyday use

```bash
ssh root@HOST /opt/leibniz-legible/deploy/staging.sh BRANCH     # a pushed branch onto staging
ssh root@HOST /opt/leibniz-legible/deploy/staging.sh --status   # what runs there, and whether it answers
ssh root@HOST /opt/leibniz-legible/deploy/staging.sh --main     # after the merge: staging and production agree again
```

`staging.sh BRANCH` fetches, checks `origin/BRANCH` out as the local branch
`staging`, syncs the venv (`uv sync --frozen`, the shared caches), restarts
the unit, waits for `/healthz`, prints what runs and the address. A branch
that is not on `origin` is refused before anything changes. The sequence for
a change to the site is then: push the branch; `staging.sh BRANCH`; look,
with the password; merge; the §9 update on the live checkout; `staging.sh
--main`, so an old branch never sits on staging half-forgotten. Until `main`
carries the kit, run the script from the staging checkout instead:
`/opt/leibniz-legible-staging/deploy/staging.sh`.

### A branch that changes the data

- **A new serving copy** (M1 and every C4). Staging reads the live copy, so a
  branch whose code expects a different store needs its own: §2 on the
  desktop into a second file, the rsync to a second path such as
  `/var/lib/leibniz-legible/inventory-staging.sqlite` (a 15 GB transfer,
  §2's timing), `chown leibniz:leibniz`, then `LEIBNIZ_DB_PATH` in
  `/etc/leibniz-legible/staging.env` pointed at it and `systemctl restart
  leibniz-legible-staging`. The directory is already writable by the service
  user, which SQLite's `-shm` sidecar needs. Point the line back and delete
  the file when the branch has merged and the live copy has been replaced.
- **A new index.** `staging.sh --index` builds `leibniz_pages_staging` (with
  `leibniz_pages_staging_meta` beside it) from the store `staging.env`
  names, with the master key from `/etc/meilisearch/env`, as a transient
  systemd unit `leibniz-index-staging`, and writes
  `LEIBNIZ_MEILI_INDEX=leibniz_pages_staging` into `staging.env`. It says
  what it will do and asks first: the live index took 5 h 33 m to build on
  this box (§5), the second index takes about as much disk again (it prints
  `df -h /var/lib/meilisearch`), and the staging unit is stopped for the
  duration. The script waits; Ctrl-C leaves the build running under
  systemd, `journalctl -fu leibniz-index-staging` watches it, and
  `systemctl start leibniz-legible-staging` finishes the job by hand. The
  live index is never touched: a build replaces only the index it names
  (`leibniz index build --meili-index`, `LEIBNIZ_MEILI_INDEX` in
  `env.example`). The serving key `meili-search-key.sh` makes is scoped to
  `leibniz_pages*`, which covers the staging name; the script reads the
  key's scope from Meilisearch and refuses to build if a key scoped
  otherwise would leave staging unable to search. `staging.sh --drop-index`
  deletes both staging indexes and points `staging.env` back at
  `leibniz_pages`.

### Memory, the password, teardown

- **Memory.** The box has 4 GB and Meilisearch wants the page cache (§7,
  §13 item 4). Staging runs one worker; what it takes is on the `Memory:`
  line of `systemctl status leibniz-legible-staging`, and `free -m` shows
  what is left for the cache. During any index build on this host, the
  staging unit should be stopped (`--index` does it itself; for a live
  rebuild under §5, `systemctl stop leibniz-legible-staging` first and
  `start` after).
- **The password.** One user, one password, in `/etc/caddy/conf.d/staging.caddy`
  as a bcrypt hash. A new password: `staging-install.sh --password`; a new
  user name: `staging-install.sh --user NAME` (the password is kept). The
  re-run rewrites the block from the example, validates and reloads, and
  touches nothing else that already exists.
- **Teardown.**

  ```bash
  /opt/leibniz-legible/deploy/staging.sh --drop-index   # only if --index was ever run; first, while the unit is there
  systemctl disable --now leibniz-legible-staging
  rm /etc/systemd/system/leibniz-legible-staging.service && systemctl daemon-reload
  rm /etc/caddy/conf.d/staging.caddy && caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile && systemctl reload caddy
  rm -rf /opt/leibniz-legible-staging /etc/leibniz-legible/staging.env /var/log/caddy/leibniz-legible-staging.log*
  ```

  Then remove the `staging` DNS record.
