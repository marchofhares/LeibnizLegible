// views/work.js — one work: its shelfmarks, its catalogue records, and the
// strip of page images it is made of.

import { t, tn } from '../i18n.js';
import * as api from '../api.js';
import { esc, pathSeg, num, conf, setLabel, aaRef, folioLabel } from '../dom.js';
import { errorPanel, loading, renderNotFound } from './common.js';

function identity(data) {
  const shelfmarks = (data.shelfmarks || []).filter(Boolean);
  const rows = [];
  if (data.set) {
    rows.push([t('work.set'), esc(setLabel(data.set))]);
  }
  if (shelfmarks.length) {
    rows.push([t('work.shelfmarks'), shelfmarks.map((s) => esc(s)).join(' · ')]);
  }
  if (typeof data.n_canvases === 'number') {
    rows.push([t('work.pages'), esc(num(data.n_canvases))]);
  }
  const body = rows
    .map(([key, value]) => `<div class="deflist__row"><dt>${esc(key)}</dt><dd>${value}</dd></div>`)
    .join('');
  return body ? `<dl class="deflist">${body}</dl>` : '';
}

function links(data) {
  const items = [
    `<a href="${esc(api.gwlbRecordUrl(data.work_id))}" rel="noopener">${esc(t('work.gwlb'))}</a>`,
  ];
  if (data.manifest_url) {
    items.push(`<a href="${esc(data.manifest_url)}" rel="noopener">${esc(t('work.manifest'))}</a>`);
  }
  items.push(
    `<a href="${esc(api.manifestUrl(data.work_id))}">${esc(t('work.ourManifest'))}</a>`,
  );
  return `<ul class="linklist">${items.map((i) => `<li>${i}</li>`).join('')}</ul>`;
}

function katalogRecord(record) {
  const rows = [];
  if (record.incipit) rows.push([t('work.katalog.incipit'), esc(record.incipit)]);
  if (record.date) rows.push([t('work.katalog.date'), esc(record.date)]);
  if (record.correspondent) rows.push([t('work.katalog.correspondent'), esc(record.correspondent)]);

  const refs = (record.aa_refs || []).map(aaRef).filter(Boolean);
  if (refs.length) {
    rows.push([t('work.katalog.aa'), refs.map((r) => `<span class="aa-ref">${esc(r)}</span>`).join(' ')]);
  }

  const body = rows
    .map(([key, value]) => `<div class="deflist__row"><dt>${esc(key)}</dt><dd>${value}</dd></div>`)
    .join('');

  const match =
    record.match_method || typeof record.match_conf === 'number'
      ? `<p class="katalog__match muted">${esc(
          t('work.katalog.match', {
            method: record.match_method || '—',
            conf: conf(record.match_conf),
          }),
        )}</p>`
      : '';

  const link = record.url
    ? `<p><a href="${esc(record.url)}" rel="noopener">${esc(t('work.katalog.record'))}</a></p>`
    : '';

  const title = record.title || record.record_id || '—';
  return (
    `<li class="katalog">` +
    `<h3 class="katalog__title">${esc(title)}</h3>` +
    (body ? `<dl class="deflist">${body}</dl>` : '') +
    link +
    match +
    `</li>`
  );
}

function katalogSection(data) {
  const records = data.katalog || [];
  const body = records.length
    ? `<ul class="katalog-list">${records.map(katalogRecord).join('')}</ul>`
    : `<p class="muted">${esc(t('work.katalog.none'))}</p>`;
  return (
    `<section class="panel" aria-labelledby="katalog-heading">` +
    `<h2 id="katalog-heading">${esc(t('work.katalog'))}</h2>` +
    body +
    `<p class="attribution__line">${esc(t('work.katalog.attr'))}</p>` +
    `</section>`
  );
}

function canvas(page) {
  const alt = folioLabel(page.label, page.seq);
  const href = `/page/${pathSeg(page.page_id)}`;
  const skipped = page.status === 'skipped';
  const statusLabel = skipped ? t('work.status.skipped') : t('work.status.recognized');
  const image = page.thumb_url
    ? `<img class="canvas__img" src="${esc(page.thumb_url)}" alt="${esc(alt)}" loading="lazy" decoding="async" />`
    : `<span class="canvas__img canvas__img--missing" role="img" aria-label="${esc(alt)}"></span>`;
  const lines =
    typeof page.n_lines === 'number' && !skipped
      ? `<span class="canvas__lines">${esc(tn('work.lines', page.n_lines))}</span>`
      : '';
  const reason = skipped && page.skip_reason ? ` (${page.skip_reason})` : '';
  return (
    `<li class="canvas">` +
    `<a class="canvas__link" href="${esc(href)}">${image}` +
    `<span class="canvas__label" aria-hidden="true">${esc(page.label || page.seq)}</span></a>` +
    `<p class="canvas__meta">` +
    `<span class="dot dot--${skipped ? 'skipped' : 'ok'}" aria-hidden="true"></span>` +
    `<span class="canvas__status">${esc(statusLabel + reason)}</span>${lines}</p>` +
    `</li>`
  );
}

function canvasStrip(data) {
  const pages = data.pages || [];
  const body = pages.length
    ? `<ol class="canvas-strip">${pages.map(canvas).join('')}</ol>`
    : `<p class="muted">${esc(t('work.noPages'))}</p>`;
  return (
    `<section class="panel" aria-labelledby="pages-heading">` +
    `<h2 id="pages-heading">${esc(t('work.pages'))}` +
    (pages.length ? ` <span class="muted">${esc(t('work.canvases', { n: num(pages.length) }))}</span>` : '') +
    `</h2>${body}</section>`
  );
}

export async function render(ctx) {
  const { root, route, signal } = ctx;
  const workId = route.id;

  root.innerHTML = `<div class="panel">${loading(t('work.loading'))}</div>`;
  document.title = `${t('work.heading')} — ${t('site.name')}`;

  let data;
  try {
    data = await api.work(workId, signal);
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    if (err instanceof api.ApiError && err.notFound) {
      renderNotFound(root, err.detail || undefined);
      return;
    }
    root.innerHTML = errorPanel(err);
    return;
  }
  if (signal.aborted) return;

  const title = data.title || workId;
  document.title = `${title} — ${t('site.name')}`;

  root.innerHTML =
    `<article class="work">` +
    `<header class="panel work__header">` +
    `<h1 tabindex="-1" data-view-heading>${esc(title)}</h1>` +
    `<p class="muted work__id"><code>${esc(data.work_id || workId)}</code></p>` +
    identity(data) +
    links(data) +
    `</header>` +
    katalogSection(data) +
    canvasStrip(data) +
    `</article>`;
}
