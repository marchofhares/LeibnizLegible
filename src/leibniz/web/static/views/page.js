// views/page.js — the scholarly view: the GWLB page image on the left, the
// recognised lines on the right, and a polygon overlay joining the two.
//
// Images are loaded straight from the GWLB — IIIF tiles where the work has an
// Image API service, a single static JPEG where it does not. Nothing is ever
// proxied through this application.

import { t, tn } from '../i18n.js';
import * as api from '../api.js';
import {
  esc,
  pathSeg,
  num,
  conf,
  chip,
  confChip,
  statusBadge,
  langLabel,
  datetime,
} from '../dom.js';
import { errorPanel, loading, renderNotFound, honestyBanner } from './common.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
const OSD_PREFIX = '/static/vendor/openseadragon/images/';

function reducedMotion() {
  return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// ---------------------------------------------------------------------------
// the line overlay: shown by default, the reader's choice remembered
// ---------------------------------------------------------------------------

const OVERLAY_KEY = 'leibniz-legible.overlay';
let overlayFallback = true; // the choice for this tab when storage is unavailable

/** Is the line overlay to be shown? The stored choice, else shown. */
function overlayWanted() {
  try {
    const stored = window.localStorage.getItem(OVERLAY_KEY);
    return stored === null ? overlayFallback : stored !== 'hidden';
  } catch {
    return overlayFallback; // private mode, blocked storage
  }
}

function rememberOverlay(shown) {
  overlayFallback = shown;
  try {
    window.localStorage.setItem(OVERLAY_KEY, shown ? 'shown' : 'hidden');
  } catch {
    /* storage unavailable — the choice lasts until the tab is closed */
  }
}

/** The toggle's label names what pressing it does; aria-pressed holds the state. */
function overlayLabel(shown) {
  return t(shown ? 'page.overlay.hide' : 'page.overlay.show');
}

// ---------------------------------------------------------------------------
// geometry
// ---------------------------------------------------------------------------

/** Pixel dimensions of the full image, with a fallback derived from the lines. */
export function imageSize(data) {
  const width = Number(data.width);
  const height = Number(data.height);
  if (Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0) {
    return { width, height };
  }
  let maxX = 0;
  let maxY = 0;
  for (const line of data.lines || []) {
    const box = line.bbox;
    if (!box) continue;
    maxX = Math.max(maxX, Number(box.x || 0) + Number(box.w || 0));
    maxY = Math.max(maxY, Number(box.y || 0) + Number(box.h || 0));
  }
  return { width: maxX || 1000, height: maxY || 1000 };
}

/** `points` for one line: its polygon, or a rectangle from its bbox. */
export function polygonPoints(line) {
  const polygon = Array.isArray(line.polygon) ? line.polygon : [];
  const pairs = polygon.filter(
    (p) => Array.isArray(p) && Number.isFinite(Number(p[0])) && Number.isFinite(Number(p[1])),
  );
  if (pairs.length >= 3) {
    return pairs.map((p) => `${Number(p[0])},${Number(p[1])}`).join(' ');
  }
  const box = line.bbox;
  if (!box) return '';
  const x = Number(box.x) || 0;
  const y = Number(box.y) || 0;
  const w = Number(box.w) || 0;
  const h = Number(box.h) || 0;
  if (w <= 0 || h <= 0) return '';
  return `${x},${y} ${x + w},${y} ${x + w},${y + h} ${x},${y + h}`;
}

// ---------------------------------------------------------------------------
// the line panel
// ---------------------------------------------------------------------------

function provenance(line, run, data) {
  const rows = [];
  const model = line.model || (run && run.model);
  if (model) rows.push([t('page.prov.model'), esc(model)]);
  const runId = line.run_id || (run && run.run_id);
  if (runId) rows.push([t('page.prov.run'), `<code>${esc(runId)}</code>`]);
  const sameRun = run && run.run_id && line.run_id && run.run_id === line.run_id;
  if (run && (sameRun || !line.run_id) && (run.started_at || run.finished_at)) {
    rows.push([t('page.prov.runDate'), esc(datetime(run.started_at || run.finished_at))]);
  }
  rows.push([t('page.prov.status'), statusBadge(line.status)]);

  if (line.source && typeof line.source === 'object') {
    const entries = Object.entries(line.source)
      .filter(([, v]) => v !== null && v !== undefined && v !== '')
      .map(([k, v]) => {
        const value = typeof v === 'object' ? JSON.stringify(v) : String(v);
        return `<span class="prov__pair"><b>${esc(k)}</b> ${esc(value)}</span>`;
      });
    rows.push([t('page.prov.source'), entries.length ? entries.join(' ') : '—']);
  } else {
    rows.push([t('page.prov.source'), esc(t('page.prov.none'))]);
  }

  // provenance names the source image at the GWLB, whatever is displayed
  const imageUrl = data.source_image_url || data.image_service_url || data.image_url;
  if (imageUrl) {
    rows.push([
      t('page.prov.image'),
      `<a href="${esc(imageUrl)}" rel="noopener"><code>${esc(imageUrl)}</code></a>`,
    ]);
  }

  const body = rows
    .map(([key, value]) => `<div class="deflist__row"><dt>${esc(key)}</dt><dd>${value}</dd></div>`)
    .join('');
  return (
    `<details class="prov"><summary>${esc(t('page.provenance'))}</summary>` +
    `<dl class="deflist deflist--tight">${body}</dl></details>`
  );
}

function lineEntry(line, index, run, data) {
  const id = String(line.line_id != null ? line.line_id : index);
  const seq = line.line_seq != null ? line.line_seq : index + 1;
  const text = (line.text || '').trim();
  const meta = [
    statusBadge(line.status),
    confChip(line.conf),
    line.lang
      ? chip('chip--lang', langLabel(line.lang), t('page.langOf', { lang: langLabel(line.lang) }))
      : '',
  ]
    .filter(Boolean)
    .join('');
  return (
    `<li class="line" data-line="${esc(id)}">` +
    `<button type="button" class="line__btn" data-line="${esc(id)}">` +
    `<span class="line__seq" aria-hidden="true">${esc(seq)}</span>` +
    `<span class="sr-only">${esc(t('page.line', { n: seq }))}</span>` +
    `<span class="line__text${text ? '' : ' line__text--empty'}">${esc(text || t('page.lineEmpty'))}</span>` +
    `</button>` +
    `<div class="line__meta">${meta}</div>` +
    provenance(line, run, data) +
    `</li>`
  );
}

function linePanel(data) {
  const lines = data.lines || [];
  const stats = data.stats || {};
  if (!lines.length) {
    return (
      `<section class="panel page-lines" aria-labelledby="lines-heading">` +
      `<h2 id="lines-heading">${esc(t('page.lines'))}</h2>` +
      `<p class="muted">${esc(t('page.noLines'))}</p></section>`
    );
  }
  const count =
    typeof stats.n_lines === 'number' || typeof stats.mean_conf === 'number'
      ? `<p class="muted">${esc(
          t('page.lines.count', {
            n: num(typeof stats.n_lines === 'number' ? stats.n_lines : lines.length),
            c: conf(stats.mean_conf),
          }),
        )}</p>`
      : '';
  return (
    `<section class="panel page-lines" aria-labelledby="lines-heading">` +
    `<h2 id="lines-heading">${esc(t('page.lines'))}</h2>${count}` +
    `<p class="hint" id="lines-help">${esc(t('page.linesHelp'))}</p>` +
    `<ol class="lines" id="lines" aria-describedby="lines-help">` +
    lines.map((line, i) => lineEntry(line, i, data.run, data)).join('') +
    `</ol></section>`
  );
}

// ---------------------------------------------------------------------------
// the text block: the page's lines as one piece of text, to select and copy
// ---------------------------------------------------------------------------

/** The lines' texts, one per line, as the plain-text export writes them: a
 *  line break inside a text becomes a space, so one line stays one line. */
export function textLines(data) {
  return (data.lines || [])
    .map((line) => String(line.text || '').replace(/\s*[\r\n]+\s*/g, ' ').trim())
    .filter(Boolean);
}

/** One entry per recognition run behind the lines, newest first: the model
 *  and the run's date, as the export's header names them. */
function runsLine(data) {
  const seen = new Map();
  for (const line of data.lines || []) {
    const model = line.model || (data.run && data.run.model) || '';
    const key = `${line.run_id != null ? line.run_id : ''}|${model}`;
    if (!seen.has(key)) seen.set(key, { run_id: line.run_id, model, at: line.run_at });
  }
  const runs = Array.from(seen.values()).sort((a, b) => (b.run_id || 0) - (a.run_id || 0));
  if (!runs.length && data.run) {
    runs.push({ model: data.run.model, at: data.run.finished_at || data.run.started_at });
  }
  return runs
    .map((run) =>
      t('page.text.run', {
        model: run.model || t('page.text.noModel'),
        date: run.at ? datetime(run.at) : t('page.text.noDate'),
      }),
    )
    .join('; ');
}

function textPanel(data, pageId) {
  const lines = textLines(data);
  if (!lines.length) return '';
  return (
    `<section class="panel page-text" id="page-text" aria-labelledby="text-heading">` +
    `<h2 id="text-heading">${esc(t('page.text'))}</h2>` +
    `<p class="hint page-text__help">${esc(t('page.text.help'))}</p>` +
    `<div class="page-text__tools">` +
    `<button type="button" class="button button--primary" id="copy-text">${esc(t('page.text.copy'))}</button>` +
    `<a class="button" href="${esc(api.pageTextUrl(data.page_id || pageId))}" download>${esc(t('page.text.download'))}</a>` +
    `<span class="page-text__status" id="copy-status" role="status" aria-live="polite"></span>` +
    `</div>` +
    `<p class="page-text__prov">${esc(t('page.text.prov', { runs: runsLine(data) }))}</p>` +
    `<pre class="page-text__block" id="page-text-block">${esc(lines.join('\n'))}</pre>` +
    `</section>`
  );
}

// ---------------------------------------------------------------------------
// header / chrome
// ---------------------------------------------------------------------------

function pageHeader(data, pageId) {
  const heading = data.label
    ? t('page.heading', { label: data.label })
    : t('page.headingSeq', { seq: data.seq });
  const workLink = data.work_id
    ? `<a href="/work/${esc(pathSeg(data.work_id))}">${esc(data.work_title || data.work_id)}</a>`
    : '';
  const nav = [
    data.prev_page_id
      ? `<a class="button" rel="prev" href="/page/${esc(pathSeg(data.prev_page_id))}">&#8592; ${esc(t('page.prev'))}</a>`
      : `<span class="button button--disabled" aria-disabled="true">&#8592; ${esc(t('page.prev'))}</span>`,
    data.next_page_id
      ? `<a class="button" rel="next" href="/page/${esc(pathSeg(data.next_page_id))}">${esc(t('page.next'))} &#8594;</a>`
      : `<span class="button button--disabled" aria-disabled="true">${esc(t('page.next'))} &#8594;</span>`,
  ].join('');
  const manifest = data.manifest_url || api.manifestUrl(data.work_id);
  // The text block, with the Copy button and the download, sits under the
  // line list; the header points at it (an in-page anchor the router leaves
  // to the browser) whenever there is text to take away.
  const textLink = (data.lines || []).length
    ? `<li><a href="#page-text">${esc(t('page.textLink'))}</a></li>`
    : '';
  return (
    `<header class="panel page-header">` +
    `<h1 tabindex="-1" data-view-heading>${esc(heading)}</h1>` +
    (workLink ? `<p class="page-header__work">${t('page.inWork', { title: workLink })}</p>` : '') +
    `<p class="muted"><code>${esc(data.page_id || pageId)}</code></p>` +
    `<nav class="page-nav" aria-label="${esc(t('page.nav'))}">${nav}</nav>` +
    `<ul class="linklist linklist--inline">` +
    textLink +
    `<li><a href="${esc(manifest)}" rel="noopener">${esc(t('page.mirador'))}</a></li>` +
    `<li><a href="${esc(api.reportUrl(data.page_id || pageId))}" rel="noopener">${esc(t('page.report'))}</a></li>` +
    `</ul></header>`
  );
}

function viewerPanel(data) {
  if (data.status === 'skipped') {
    return (
      `<section class="panel page-viewer page-viewer--skipped" aria-labelledby="viewer-heading">` +
      `<h2 id="viewer-heading" class="sr-only">${esc(t('page.viewer.label'))}</h2>` +
      `<p class="state state--skipped"><strong>${esc(t('page.skipped'))}</strong></p>` +
      (data.skip_reason
        ? `<p>${esc(t('page.skipReason', { reason: data.skip_reason }))}</p>`
        : '') +
      `</section>`
    );
  }
  const hasImage = Boolean(data.image_service_url || data.image_url);
  const hasLines = Boolean((data.lines || []).length);
  const shown = overlayWanted();
  const toggle =
    hasImage && hasLines
      ? `<div class="page-viewer__controls">` +
        `<button type="button" class="button" id="overlay-toggle" aria-pressed="${shown}">` +
        `${esc(overlayLabel(shown))}</button></div>`
      : '';
  return (
    `<section class="panel page-viewer" aria-labelledby="viewer-heading">` +
    `<h2 id="viewer-heading" class="sr-only">${esc(t('page.viewer.label'))}</h2>` +
    toggle +
    (hasImage
      ? `<div id="osd" class="osd"></div>`
      : `<p class="state state--error">${esc(t('page.viewerError'))}</p>`) +
    (data.delivery === 'static' && data.image_origin !== 'mirror'
      ? `<p class="hint">${esc(t('page.viewer.noIiif'))}</p>`
      : '') +
    `<p class="attribution__line">${esc(
      t(data.image_origin === 'mirror' ? 'attr.images.mirror' : 'attr.images'),
    )}</p>` +
    `</section>`
  );
}

// ---------------------------------------------------------------------------
// the viewer + overlay wiring
// ---------------------------------------------------------------------------

function tileSourceFor(data) {
  if (data.delivery === 'iiif' && data.image_service_url) {
    return `${String(data.image_service_url).replace(/\/+$/, '')}/info.json`;
  }
  if (data.image_url) return { type: 'image', url: data.image_url };
  if (data.image_service_url) {
    return `${String(data.image_service_url).replace(/\/+$/, '')}/info.json`;
  }
  return null;
}

function buildOverlay(data) {
  const { width, height } = imageSize(data);
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('class', 'line-overlay');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  (data.lines || []).forEach((line, index) => {
    const points = polygonPoints(line);
    if (!points) return;
    const polygon = document.createElementNS(SVG_NS, 'polygon');
    polygon.setAttribute('points', points);
    polygon.setAttribute('class', 'line-overlay__poly');
    polygon.setAttribute('data-line', String(line.line_id != null ? line.line_id : index));
    svg.append(polygon);
  });
  return { svg, width, height };
}

export async function render(ctx) {
  const { root, route, signal } = ctx;
  const pageId = route.id;

  root.innerHTML = honestyBanner() + `<div class="panel">${loading(t('page.loading'))}</div>`;
  document.title = t('site.name');

  let data;
  try {
    data = await api.page(pageId, signal);
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    if (err instanceof api.ApiError && err.notFound) {
      renderNotFound(root, err.detail || undefined);
      return;
    }
    root.innerHTML = honestyBanner() + errorPanel(err);
    return;
  }
  if (signal.aborted) return;

  const heading = data.label
    ? t('page.heading', { label: data.label })
    : t('page.headingSeq', { seq: data.seq });
  document.title = `${heading} — ${data.work_title || data.work_id} — ${t('site.name')}`;

  root.innerHTML =
    honestyBanner() +
    pageHeader(data, pageId) +
    `<div class="page-layout">${viewerPanel(data)}` +
    `<div class="page-side">${linePanel(data)}${textPanel(data, pageId)}</div></div>`;

  return wire(root, data);
}

/** Wire the viewer, the overlay and the line panel together. Returns cleanup. */
function wire(root, data) {
  const list = root.querySelector('#lines');
  const buttons = list ? Array.from(list.querySelectorAll('.line__btn')) : [];
  const osdEl = root.querySelector('#osd');
  const toggle = root.querySelector('#overlay-toggle');
  const reduce = reducedMotion();

  let viewer = null;
  let overlaySvg = null;
  let selected = null;

  const byId = new Map();
  (data.lines || []).forEach((line, index) => {
    byId.set(String(line.line_id != null ? line.line_id : index), line);
  });

  // While the overlay is hidden a line selected in the panel still zooms the
  // image to it, and its polygon keeps the highlight for when the overlay is
  // shown again; the hidden polygons take no pointer events (style.css).
  function highlight(id) {
    selected = id;
    for (const button of buttons) {
      const active = button.getAttribute('data-line') === id;
      button.closest('.line').classList.toggle('is-active', active);
      if (active) button.setAttribute('aria-current', 'true');
      else button.removeAttribute('aria-current');
    }
    if (overlaySvg) {
      for (const polygon of overlaySvg.querySelectorAll('.line-overlay__poly')) {
        polygon.classList.toggle('is-active', polygon.getAttribute('data-line') === id);
      }
    }
  }

  function zoomTo(id) {
    const line = byId.get(id);
    if (!viewer || !line || !line.bbox || !window.OpenSeadragon) return;
    const { width } = imageSize(data);
    if (!width) return;
    const box = line.bbox;
    const x = Number(box.x) || 0;
    const y = Number(box.y) || 0;
    const w = Number(box.w) || 0;
    const h = Number(box.h) || 0;
    if (w <= 0 || h <= 0) return;
    // Viewport coordinates: the image is 1.0 wide, so every dimension is
    // divided by the image width.
    const padX = w * 0.08;
    const padY = h * 0.6;
    const rect = new window.OpenSeadragon.Rect(
      (x - padX) / width,
      (y - padY) / width,
      (w + padX * 2) / width,
      (h + padY * 2) / width,
    );
    try {
      viewer.viewport.fitBounds(rect, reduce);
    } catch {
      /* the viewer may not be open yet; the highlight still stands */
    }
  }

  function scrollToEntry(id) {
    const button = buttons.find((b) => b.getAttribute('data-line') === id);
    if (!button) return;
    button.scrollIntoView({
      block: 'nearest',
      behavior: reduce ? 'auto' : 'smooth',
    });
  }

  // --- panel -> image ------------------------------------------------------
  //
  // The line's text is selectable inside its button (style.css). A drag over
  // it ends in a click on the same button, and a double-click on a word is
  // two clicks: while a selection stands inside the list, the reader is
  // taking text, not choosing a line, so the click does nothing.
  function selectionInside(el) {
    const sel = window.getSelection ? window.getSelection() : null;
    return Boolean(sel && !sel.isCollapsed && sel.anchorNode && el.contains(sel.anchorNode));
  }

  function onListClick(event) {
    const button = event.target.closest ? event.target.closest('.line__btn') : null;
    if (!button || !list.contains(button)) return;
    if (selectionInside(list)) return;
    const id = button.getAttribute('data-line');
    highlight(id);
    zoomTo(id);
  }

  function onListKeydown(event) {
    const button = event.target.closest ? event.target.closest('.line__btn') : null;
    if (!button) return;
    const index = buttons.indexOf(button);
    if (index < 0) return;
    let next = -1;
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = index + 1;
    else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = index - 1;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = buttons.length - 1;
    else return;
    if (next < 0 || next >= buttons.length) {
      event.preventDefault();
      return;
    }
    event.preventDefault();
    buttons[next].focus();
  }

  // A selection made in the list spans, in document order, the badges, the
  // number and the hidden label of every line between the first and the last
  // text. They are `user-select: none` (style.css), which Chromium honours in
  // the copy but not without a trace (measured on the fixture store: the two
  // texts with a blank line between them, while Selection.toString() still
  // reports "machine. HTR output, unreviewed.", "confidence 0.95", "Line 1"),
  // and other browsers draw the line elsewhere. So a copy whose selection lies
  // inside the list is answered here: the selected part of each line's text,
  // one per line, and nothing else.
  function selectedLineTexts(range) {
    const out = [];
    for (const el of list.querySelectorAll('.line__text')) {
      if (!range.intersectsNode(el)) continue;
      const part = document.createRange();
      part.selectNodeContents(el);
      if (range.compareBoundaryPoints(Range.START_TO_START, part) > 0) {
        part.setStart(range.startContainer, range.startOffset);
      }
      if (range.compareBoundaryPoints(Range.END_TO_END, part) < 0) {
        part.setEnd(range.endContainer, range.endOffset);
      }
      const text = part.toString().replace(/\s+/g, ' ').trim();
      if (text) out.push(text);
    }
    return out;
  }

  function onDocumentCopy(event) {
    const sel = window.getSelection ? window.getSelection() : null;
    if (!sel || sel.isCollapsed || !sel.rangeCount || !event.clipboardData) return;
    const range = sel.getRangeAt(0);
    if (!list.contains(range.commonAncestorContainer)) return;
    const texts = selectedLineTexts(range);
    if (!texts.length) return;
    event.clipboardData.setData('text/plain', texts.join('\n'));
    event.preventDefault();
  }

  if (list) {
    list.addEventListener('click', onListClick);
    list.addEventListener('keydown', onListKeydown);
    document.addEventListener('copy', onDocumentCopy);
  }

  // --- image -> panel ------------------------------------------------------
  //
  // OpenSeadragon captures the pointer on its own container as soon as a
  // gesture starts, so `pointerup`/`click` never reach the polygon and a plain
  // click handler on the overlay would never fire. We therefore remember the
  // polygon a gesture started on and treat it as a click if the pointer came
  // up again promptly and near enough — which also means a pan that begins on
  // a line is still a pan, not a selection.
  let pending = null;
  const CLICK_SLOP_PX = 6;
  const CLICK_MAX_MS = 700;

  function onOverlayPointerDown(event) {
    if (overlaySvg && overlaySvg.classList.contains('is-hidden')) {
      pending = null; // a hidden line is never a click target
      return;
    }
    const polygon = event.target.closest ? event.target.closest('.line-overlay__poly') : null;
    pending = polygon
      ? {
          id: polygon.getAttribute('data-line'),
          x: event.clientX,
          y: event.clientY,
          at: Date.now(),
        }
      : null;
  }

  function onWindowPointerUp(event) {
    const started = pending;
    pending = null;
    if (!started) return;
    const dx = event.clientX - started.x;
    const dy = event.clientY - started.y;
    if (Math.hypot(dx, dy) > CLICK_SLOP_PX) return;
    if (Date.now() - started.at > CLICK_MAX_MS) return;
    highlight(started.id);
    scrollToEntry(started.id);
  }

  // --- OpenSeadragon -------------------------------------------------------
  const tileSource = osdEl && window.OpenSeadragon ? tileSourceFor(data) : null;
  if (osdEl && !window.OpenSeadragon) {
    osdEl.innerHTML = `<p class="state state--error">${esc(t('page.viewerError'))}</p>`;
  } else if (osdEl && tileSource) {
    viewer = window.OpenSeadragon({
      element: osdEl,
      prefixUrl: OSD_PREFIX,
      tileSources: tileSource,
      showNavigator: false,
      showRotationControl: false,
      showFlipControl: false,
      showFullPageControl: true,
      animationTime: reduce ? 0 : 0.8,
      maxZoomPixelRatio: 3,
      visibilityRatio: 0.7,
      constrainDuringPan: true,
      gestureSettingsMouse: { clickToZoom: false, dblClickToZoom: true },
      gestureSettingsTouch: { clickToZoom: false, dblClickToZoom: true },
      crossOriginPolicy: false,
      ajaxWithCredentials: false,
    });

    viewer.addHandler('open', () => {
      const built = buildOverlay(data);
      overlaySvg = built.svg;
      if (toggle && toggle.getAttribute('aria-pressed') === 'false') {
        overlaySvg.classList.add('is-hidden');
      }
      overlaySvg.addEventListener('pointerdown', onOverlayPointerDown);
      window.addEventListener('pointerup', onWindowPointerUp);
      window.addEventListener('pointercancel', onWindowPointerUp);
      viewer.addOverlay({
        element: overlaySvg,
        location: new window.OpenSeadragon.Rect(0, 0, 1, built.height / built.width),
      });
      if (selected) highlight(selected);
    });

    viewer.addHandler('open-failed', () => {
      osdEl.innerHTML = `<p class="state state--error">${esc(t('page.viewerError'))}</p>`;
    });
  }

  // The class hides the overlay through `visibility` (style.css): OpenSeadragon
  // rewrites the element's inline `display` on every redraw.
  function onToggle() {
    const shown = toggle.getAttribute('aria-pressed') !== 'true';
    rememberOverlay(shown);
    toggle.setAttribute('aria-pressed', String(shown));
    toggle.textContent = overlayLabel(shown);
    if (overlaySvg) overlaySvg.classList.toggle('is-hidden', !shown);
    if (!shown) pending = null;
  }
  if (toggle) toggle.addEventListener('click', onToggle);

  // --- the text block ------------------------------------------------------
  //
  // Copy writes the block's text to the clipboard from inside the click
  // handler, where the browser counts the user's gesture. Where it refuses
  // (an insecure context, a denied permission, no clipboard API), the block is
  // selected and the status line says to press Ctrl+C.
  const copyBtn = root.querySelector('#copy-text');
  const block = root.querySelector('#page-text-block');
  const copyStatus = root.querySelector('#copy-status');

  function say(message) {
    if (copyStatus) copyStatus.textContent = message;
  }

  function selectBlock() {
    try {
      const range = document.createRange();
      range.selectNodeContents(block);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    } catch {
      /* selection unavailable */
    }
  }

  function refused() {
    selectBlock();
    say(t('page.text.copyRefused'));
  }

  function onCopy() {
    if (!block) return;
    const text = block.textContent;
    const n = text ? text.split('\n').length : 0;
    say('');
    const clipboard = navigator.clipboard;
    if (clipboard && typeof clipboard.writeText === 'function') {
      clipboard.writeText(text).then(() => say(tn('page.text.copied', n)), refused);
    } else {
      refused();
    }
  }
  if (copyBtn) copyBtn.addEventListener('click', onCopy);

  return function cleanup() {
    if (list) {
      list.removeEventListener('click', onListClick);
      list.removeEventListener('keydown', onListKeydown);
      document.removeEventListener('copy', onDocumentCopy);
    }
    if (toggle) toggle.removeEventListener('click', onToggle);
    if (copyBtn) copyBtn.removeEventListener('click', onCopy);
    if (overlaySvg) overlaySvg.removeEventListener('pointerdown', onOverlayPointerDown);
    window.removeEventListener('pointerup', onWindowPointerUp);
    window.removeEventListener('pointercancel', onWindowPointerUp);
    if (viewer) {
      try {
        viewer.destroy();
      } catch {
        /* nothing useful to do if OSD is already gone */
      }
      viewer = null;
    }
  };
}
