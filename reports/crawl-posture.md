# Crawl posture — GWLB & BBAW

_Leibniz Legible, Phase A1. Probed live 2026-07-28 (UTC). Re-verify before any
bulk pull; endpoints drift._

This report records the crawling etiquette baseline required by SPECS §7.4
before any bulk harvest: `robots.txt`, relevant response headers, and an
explicit check for a machine-readable **text-and-data-mining reservation
(§44b UrhG)** on every host the project crawls. Per the phase gate, if a TDM
reservation existed we would **stop and flag**; none does (see the verdict).

## Hosts in scope

| Host | Role | Crawled in phase |
| --- | --- | --- |
| `digitale-sammlungen.gwlb.de` | GWLB Kitodo.Presentation: OAI-PMH, IIIF manifests, IIIF Image API | A1 (metadata), A2 (images) |
| `leibniz-katalog.bbaw.de` | BBAW Ritter-Katalog (scholarly catalogue) | A3 (crosswalk) — probed here in advance |

The GWLB host serves everything A1 touches (OAI + IIIF live on the same host).
The BBAW host is not crawled until A3; it is included here so the project's
crawl posture is recorded in one place before the first pull, as §7.4 intends.

---

## 1. `digitale-sammlungen.gwlb.de` (GWLB)

**Stack.** `Server: Apache/2.4.41 (Ubuntu)`, TYPO3 with the Kitodo.Presentation
(`dlf`) extension. IIIF images served by IIPImage (`X-Powered-By: IIPImage`).

### robots.txt

There is **no static `robots.txt`**. The path is caught by the TYPO3 front
controller and 302-redirects into the application:

```
$ curl -A "<project UA>" -I https://digitale-sammlungen.gwlb.de/robots.txt
HTTP/1.1 302 Found
location: index.php
Content-Length: 0
Content-Type: text/html; charset=UTF-8
```

Following the redirect loops (`index.php` → … → redirect limit). No `Disallow`
rules are served for any path, i.e. nothing is disallowed by a robots policy.
Absence of `robots.txt` is **not** a licence to hammer the host — the SPECS §7.4
rails (≤1 req/s per host, backoff, cache-first, resume, identifying UA) apply
regardless, and this project enforces them in code (`src/leibniz/net.py`).

### Response headers (OAI endpoint)

```
$ curl -A "<project UA>" -I "https://digitale-sammlungen.gwlb.de/oai2/?verb=Identify"
HTTP/1.1 200 OK
Server: Apache/2.4.41 (Ubuntu)
Cache-Control: no-cache
X-UA-Compatible: IE=edge
X-Content-Type-Options: nosniff
Access-Control-Allow-Origin: *
Content-Type: text/xml; charset=utf-8
```

The OAI-PMH `Identify` response names the repository and an admin contact:

```
repositoryName : Gottfried Wilhelm Leibniz Bibliothek
adminEmail     : handschriften@gwlb.de
protocolVersion: 2.0
granularity    : YYYY-MM-DDThh:mm:ssZ
deletedRecord  : transient
```

### Response headers (IIIF Image API delivery — used by A2)

```
$ curl -A "<project UA>" -I ".../iiif/00068642/ptif/00000001.ptif/full/full/0/default.jpg"
HTTP/1.1 200 OK
Server: Apache/2.4.41 (Ubuntu)
X-Powered-By: IIPImage
Access-Control-Allow-Origin: *
Content-Type: image/jpeg
```

`info.json` advertises IIIF Image API **2.0 level1**, source 2008×2561 for the
sampled quarto, tile size 256, `maxWidth`/`maxHeight` 5000. Rights on the object
records are **Public Domain Mark 1.0** (`dv:license`, `mods:accessCondition`) —
consistent with SPECS §1.1. `Access-Control-Allow-Origin: *` means the viewer
(D2) can load tiles directly in-browser with no proxy, as SPECS §3/§4 require.

### TDM reservation (§44b UrhG) — checked

| Mechanism | Probe | Result |
| --- | --- | --- |
| TDMRep well-known | `GET /.well-known/tdmrep.json` | **302 → `index.php`** (no such file) |
| HTTP header | `TDM-Reservation` / `TDM-Policy` on content + image responses | **absent** |
| HTTP header | `X-Robots-Tag` | **absent** |
| HTML `<meta>` | `tdm-reservation` / `tdm-policy` / `robots` on the homepage | **absent** |
| robots.txt rule | any `Disallow` | **none served** (see above) |

**No machine-readable TDM reservation is present on the GWLB host.**

---

## 2. `leibniz-katalog.bbaw.de` (BBAW Ritter-Katalog)

**Stack.** `server: nginx/1.24.0 (Ubuntu)`, a Laravel application (HTTP/2).
Crawled only from A3; recorded now for completeness.

### robots.txt

No usable `robots.txt`. The root path 302-redirects to a language-prefixed URL,
which then returns the application's **404** page (a Laravel "Not Found" HTML
document, not a robots file):

```
$ curl -A "<project UA>" -I https://leibniz-katalog.bbaw.de/robots.txt
HTTP/1.1 302 Found
location: https://leibniz-katalog.bbaw.de/de/robots.txt
# → /de/robots.txt returns an HTML 404 page, no Disallow rules
```

### Response headers

```
$ curl -A "<project UA>" -I https://leibniz-katalog.bbaw.de/de
HTTP/2 200
server: nginx/1.24.0 (Ubuntu)
content-type: text/html; charset=UTF-8
```

No `X-Robots-Tag`, no `TDM-*` headers.

### TDM reservation (§44b UrhG) — checked

| Mechanism | Probe | Result |
| --- | --- | --- |
| TDMRep well-known | `GET /.well-known/tdmrep.json` | **404** (no such file) |
| HTTP header | `TDM-Reservation` / `TDM-Policy` / `X-Robots-Tag` | **absent** |
| robots.txt rule | any `Disallow` | **none served** (404) |

**No machine-readable TDM reservation is present on the BBAW host.** (The
catalogue is separately declared **CC BY 4.0**, SPECS §1.2 — attribution to
BBAW/TELOTA is required and recorded for A3.)

---

## Verdict

> **No machine-readable TDM reservation (§44b UrhG) exists on either host.**
> Neither serves a `robots.txt` with any rule, a TDMRep `/.well-known/tdmrep.json`,
> a `TDM-Reservation`/`TDM-Policy`/`X-Robots-Tag` header, or a `tdm-reservation`
> meta tag. The A1 gate's stop-condition is therefore **not** triggered; harvest
> may proceed under the SPECS §7.4 rails.

The OAI/IIIF endpoints exist precisely to be harvested (SPECS §9). We stay well
inside polite limits and treat the GWLB's goodwill as worth more than any
position we could litigate (SPECS §7.7): the operator email to
`digitalisierung@gwlb.de` (SPECS §8) runs in parallel with, not after, this work.

### Enforced rails (in code, `src/leibniz/net.py`)

- **Identifying User-Agent** with project URL + contact email (from `.env`;
  see `.env.example`), sent on every request.
- **≤ 1 request/second per host**, tracked per host.
- **Exponential backoff** (2s, 4s, 8s, 16s) on 429/5xx/transport errors.
- **Cache-first**: raw OAI XML and IIIF manifests are cached under `data/oai/`
  and `data/manifests/`; a cached item is never re-fetched. Harvest is resumable.
- **No image rehosting**: A2 caches derivatives locally for processing only; the
  public viewer (D2) loads tiles directly from the GWLB IIIF Image API.
