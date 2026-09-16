# `leibniz/web/static` — the public frontend (Phase D2)

Vanilla HTML + CSS + ES modules. **No build step, no bundler, no framework, no
analytics.** What is in this directory is what the browser gets. The only
network traffic the app causes is our own JSON API on the same origin and
**page images loaded directly from the GWLB** — images are never rehosted or
proxied (SPECS §3.4, §7.1).

## How it is served

The FastAPI app mounts this directory at `/static/` and returns
`static/index.html` for five routes:

| Route            | View                                                        |
| ---------------- | ----------------------------------------------------------- |
| `/`              | search (empty state)                                        |
| `/search`        | search, reading `?q=&set=&lang=&stratum=&min_conf=&work=&page=&limit=` |
| `/work/{work_id}`| one work                                                    |
| `/page/{page_id}`| one page — viewer + lines                                   |
| `/about`         | about                                                       |

Everything in `index.html` is referenced by **absolute** path (`/static/…`)
because the same document is served from nested paths like
`/page/00068642:0007`.

`{page_id}` contains a colon (`00068642:0007`). A colon is a legal path
character (RFC 3986 `pchar`), so it is *not* percent-encoded — in the address
bar or in the API call. Starlette's default `str` path convertor matches it
without any change.

There is no SPA catch-all: an unknown path 404s at the server, which is
correct. The router's own "not found" view exists for API 404s (an unknown
work or page id) and as a defensive fallback.

```bash
# minimal mount on the FastAPI side
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
@app.get("/search")
@app.get("/about")
@app.get("/work/{work_id}")
@app.get("/page/{page_id}")
def spa(...): return FileResponse(STATIC_DIR / "index.html")
```

## Files

| File | What |
| --- | --- |
| `index.html` | the shell: header, nav, language switch, the **statically delivered search form**, footer, `<noscript>` |
| `boot.js` | one line, loaded synchronously in `<head>`: drops the `no-js` class before first paint (a file, not inline, because of the CSP — see below) |
| `robots.txt` | served at `/robots.txt`: human pages open, `/api/`, `/manifests/`, `/annotations/` closed to crawlers (their canvases would pull every GWLB image) |
| `app.js` | boot, i18n over the static chrome, router (`pushState` + `popstate`), link and form interception |
| `api.js` | `search` / `work` / `page` / `stats` wrappers, `ApiError`, URL builders |
| `dom.js` | `esc()`, the snippet sanitiser, number/date formatting, confidence bands, chips and badges |
| `i18n.js` | the whole EN + DE string table and `t()` |
| `style.css` | design tokens, light + dark themes, every component |
| `views/search.js` | grouped results, filters, pagination, empty/error states |
| `views/work.js` | identity, catalogue records, canvas strip |
| `views/page.js` | OpenSeadragon, the SVG line overlay, the line panel, provenance |
| `views/about.js` | the honest page; live figures from `/api/stats` |
| `views/common.js` | shared fragments: honesty banner, loading, error, not-found |
| `vendor/openseadragon/` | OpenSeadragon 5.0.1, BSD-3-Clause — see its `VERSION` |

## Conventions

**Escape everything.** Views build HTML strings and every interpolated API
value goes through `esc()` from `dom.js`. The single exception is the search
`snippet`, which the API generates as HTML with `<mark>` highlights; `snippet()`
re-parses it in an inert `<template>` and rebuilds it keeping text and `<mark>`
elements only. Any other element is dropped (its text is kept), so the API
cannot inject markup even by accident — but it also means **only `<mark>`
survives**: if the API ever wants another tag in a snippet, change `snippet()`.

**Content Security Policy.** The server sends `script-src 'self'` (see
`leibniz/web/middleware.py`), so **no inline `<script>` and no `onclick=`
attributes** — put code in a file under `static/`. Inline `style="…"` is
allowed (`style-src 'unsafe-inline'`; `about.js` uses it for the histogram
bars), and images / `info.json` may come from any https origin because the
store, not the code, says where a work's images live. Re-run the Playwright
pass after touching this: a CSP violation is a console error, not an exception.

**Adding a user-facing string.** Add the key to **both** `en` and `de` in
`i18n.js`, in the matching section, then use `t('your.key')`. Never inline
prose in a view. `t()` interpolates `{placeholders}` and falls back
English → the key itself, so a missing string is visible rather than silent.
For static markup in `index.html`, add `data-i18n="key"` (text content),
`data-i18n-label`, `data-i18n-placeholder` or `data-i18n-title` (attributes);
`app.js` applies them on boot and on every language change. The language is
persisted in `localStorage` under `leibniz-legible.lang` and mirrored to
`<html lang>`.

**Adding a view.** Export `async render(ctx)` from `views/<name>.js` and add it
to `VIEWS` + `parseRoute()` in `app.js`. `ctx` carries `{ root, route, query,
signal, navigate, searchPanel, applyI18n }`. Give the view's `<h1>`
`tabindex="-1" data-view-heading` so focus lands on it after navigation.
Return a cleanup function if you attached listeners or created a viewer;
the router calls it before the next render and aborts `signal` on navigation.

**Accessibility** is a gate, not a nicety: skip link, landmarks, visible focus
rings, labels on every control, `aria-live="polite"` on the results region,
contrast ≥ 4.5:1 in both themes, phone width without horizontal scroll,
`prefers-reduced-motion` respected. A bare `<span>` may not take `aria-label` —
use the `chip()` helper (visible text `aria-hidden`, full label in `.sr-only`).

**Register**: calm and scholarly. Serif (system stack, no web fonts) for
content, sans for chrome. Under-claim — this is machine output, never "an
edition" (SPECS §7, `docs/VOICE`-equivalent posture in `README.md`).

## Without JavaScript

`index.html` ships the real search form (`<form method="get" action="/search">`)
inside `#search-panel`; `app.js` detaches it on boot and re-inserts it into the
search view. With JS off the form still submits, and a `<noscript>` block
explains that results need JS and points at `/api/search`. A plain form GET
sends **empty** values for the untouched selects
(`?q=calculemus&set=&lang=&stratum=&min_conf=0`) — the API must treat an empty
string as "no filter".

## OpenSeadragon

Vendored, not fetched from a CDN: `vendor/openseadragon/openseadragon.min.js`
plus `images/` and `LICENSE.txt`, taken unmodified from the npm tarball of
**5.0.1** (see `vendor/openseadragon/VERSION` for the checksums). It is loaded
as a classic `<script>` before `app.js`, so it is `window.OpenSeadragon`;
`page.js` degrades to an error notice if it is absent.

Tiles come from the GWLB directly:

- `delivery === "iiif"` → `tileSources: image_service_url + "/info.json"`
- `delivery === "static"` → `tileSources: { type: "image", url: image_url }`
  (only about a third of works have an Image API service, so this is the
  common case; see STATUS.md, "Delivery-model correction")

The line overlay is **one** `<svg viewBox="0 0 {width} {height}"
preserveAspectRatio="none">` holding one `<polygon>` per line, added once with
`viewer.addOverlay({ element, location: new OpenSeadragon.Rect(0, 0, 1,
height / width) })`, so OSD scales it with the image. Polygon coordinates are
full-image pixels; a line with an empty `polygon` falls back to a rectangle
from its `bbox`. `fitBounds` divides every bbox dimension by the image *width*,
which is the OSD viewport convention.

Note for anyone touching the overlay: OpenSeadragon captures the pointer on its
own container, so `click` never reaches a polygon. Selection is detected from
`pointerdown` on the polygon plus a `pointerup` that is close enough in space
and time — which also keeps a pan that starts on a line a pan.

## Testing

There are no unit tests in this directory (the Python test suite does not run
JavaScript). The frontend was exercised against a throwaway mock of the API
with Playwright/Chromium: every view and state, `axe-core` for WCAG 2 A/AA,
console-error capture, the page-view interactions, the language switch, the
router, and the no-JS path. Re-do it the same way after substantive changes;
do not add the mock or its screenshots to the repository.
