// views/work.js — one work: its place in the browse index, its shelfmarks, its
// catalogue records, and the strip of page images it is made of.

import { t, tn } from '../i18n.js';
import * as api from '../api.js';
import { esc, pathSeg, num, conf, setLabel, aaRef, folioLabel } from '../dom.js';
import { errorPanel, loading, renderNotFound } from './common.js';

/** The way back into the browse index: "Browse › LH 35 · Mathematik". */
function crumbs(data) {
  const place = data.browse;
  if (!place || !place.anchor) return '';
  // The section's name is the archive's own and arrives as data.
  return (
    `<nav class="crumbs" aria-label="${esc(t('crumbs.label'))}"><ol>` +
    `<li><a href="/browse">${esc(t('nav.browse'))}</a></li>` +
    `<li><a href="/browse#${esc(place.anchor)}">${esc(place.title || place.label)}</a></li>` +
    `</ol></nav>`
  );
}

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
  // The whole work as one plain-text download, when any page has text.
  if ((data.pages || []).some((p) => p.n_lines > 0)) {
    items.push(
      `<a href="${esc(api.workTextUrl(data.work_id))}" download>${esc(t('work.download'))}</a>`,
    );
  }
  return `<ul class="linklist">${items.map((i) => `<li>${i}</li>`).join('')}</ul>`;
}

/**
 * How a catalogue record came to be linked to this work, in words: the
 * crosswalk's method (`gwlb_link`, `shelfmark`) is an identifier, not a label.
 * A method the string table has no words for is shown by name.
 */
function matchLine(record) {
  const vars = { method: record.match_method || '—', conf: conf(record.match_conf) };
  const worded = `work.katalog.match.${record.match_method}`;
  const text = t(worded, vars);
  return text === worded ? t('work.katalog.match', vars) : text;
}

function katalogRecord(record) {
  const rows = [];
  if (record.incipit) rows.push([t('work.katalog.incipit'), esc(record.incipit)]);
  if (record.date) rows.push([t('work.katalog.date'), esc(record.date)]);
  // Sender and addressee, each as the catalogue names them. (One row called
  // "Correspondent" used to show the sender alone: Leibniz, in his own letters.)
  const people = (names) => (names || []).map((name) => esc(name)).join('; ');
  if (people(record.sender)) rows.push([t('work.katalog.sender'), people(record.sender)]);
  if (people(record.addressee)) rows.push([t('work.katalog.addressee'), people(record.addressee)]);

  const refs = (record.aa_refs || []).map(aaRef).filter(Boolean);
  if (refs.length) {
    rows.push([t('work.katalog.aa'), refs.map((r) => `<span class="aa-ref">${esc(r)}</span>`).join(' ')]);
  } else if (record.aa_planned && record.aa_planned.length) {
    // The katalog names a series without a volume: assigned to the AA, not
    // yet published there. Read with the other printings below.
    rows.push([t('work.katalog.aa.planned'), record.aa_planned.map((r) => esc(r)).join(', ')]);
  }
  if (record.drucke) rows.push([t('work.katalog.drucke'), esc(record.drucke)]);

  const body = rows
    .map(([key, value]) => `<div class="deflist__row"><dt>${esc(key)}</dt><dd>${value}</dd></div>`)
    .join('');

  const match =
    record.match_method || typeof record.match_conf === 'number'
      ? `<p class="katalog__match muted">${esc(matchLine(record))}</p>`
      : '';

  // The piece's machine text across its folios, a download, only where the
  // API placed the record on the scan (text_url + folio_label travel together).
  const text = record.text_url
    ? `<p class="katalog__text"><a href="${esc(record.text_url)}" download>` +
      `${esc(t('work.katalog.text', { range: record.folio_label || '' }))}</a></p>`
    : '';

  const link = record.url
    ? `<p><a href="${esc(record.url)}" rel="noopener">${esc(t('work.katalog.record'))}</a></p>`
    : '';

  const title = record.title || record.record_id || '—';
  return (
    `<li class="katalog">` +
    `<h3 class="katalog__title">${esc(title)}</h3>` +
    (body ? `<dl class="deflist">${body}</dl>` : '') +
    text +
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
    twinLine(page) +
    `</li>`
  );
}

/** One scan under several labels: "Spread with fol. 2v", "Same scan as fol. 1r". */
export function twinLine(page) {
  const twin = page.twin;
  if (!twin) return '';
  const labels = (twin.others || []).map((o) => folioLabel(o.label, o.page_id)).join(', ');
  let key = 'work.twin.primary';
  let vars = { labels };
  if (twin.kind === 'spread') {
    key = 'work.twin.spread';
  } else if (!twin.is_primary) {
    const primary = (twin.others || []).find((o) => o.page_id === twin.primary);
    key = 'work.twin.secondary';
    vars = { label: primary ? folioLabel(primary.label, primary.page_id) : '' };
  }
  return `<p class="canvas__twin">${esc(t(key, vars))}</p>`;
}

/** Search inside this work: the search page, narrowed to it. */
function workSearch(data) {
  if (!(data.pages || []).some((p) => p.n_lines > 0)) return '';
  return (
    `<form class="work-search" action="/search" method="get" role="search">` +
    `<label class="field__label" for="work-q">${esc(t('work.search'))}</label>` +
    `<div class="work-search__row">` +
    `<input id="work-q" name="q" type="search" required maxlength="500" autocomplete="off" />` +
    `<input type="hidden" name="work" value="${esc(data.work_id)}" />` +
    `<button type="submit" class="button button--primary">${esc(t('work.search.go'))}</button>` +
    `</div></form>`
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
    crumbs(data) +
    `<h1 tabindex="-1" data-view-heading>${esc(title)}</h1>` +
    `<p class="muted work__id"><code>${esc(data.work_id || workId)}</code></p>` +
    identity(data) +
    links(data) +
    workSearch(data) +
    `</header>` +
    katalogSection(data) +
    canvasStrip(data) +
    `</article>`;
}
