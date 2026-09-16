// views/search.js — the search view, served at `/` and `/search?…`.
//
// The form itself is the statically delivered #search-panel (see index.html):
// it exists, and submits as a plain GET to /search, with JavaScript switched
// off. Here we move it into the view, fill it from the URL, and render results
// beneath it.

import { t, tn } from '../i18n.js';
import * as api from '../api.js';
import {
  esc,
  snippet,
  pathSeg,
  num,
  conf,
  chip,
  confBand,
  setLabel,
  langLabel,
  stratumLabel,
  folioLabel,
} from '../dom.js';
import { errorPanel, loading } from './common.js';

const DEFAULT_LIMIT = 20;

/** Read the parameters this view understands out of the URL. */
function readParams(query) {
  const get = (k) => (query.get(k) || '').trim();
  const pageNum = Number.parseInt(get('page'), 10);
  const limitNum = Number.parseInt(get('limit'), 10);
  return {
    q: get('q'),
    set: get('set'),
    lang: get('lang'),
    stratum: get('stratum'),
    min_conf: get('min_conf'),
    work: get('work'),
    page: Number.isFinite(pageNum) && pageNum > 1 ? pageNum : 1,
    limit: Number.isFinite(limitNum) && limitNum > 0 ? limitNum : '',
  };
}

/** Push the URL's state back into the form controls. */
function fillForm(panel, params) {
  const form = panel.querySelector('#search-form');
  if (!form) return;

  const q = form.querySelector('#q');
  if (q) q.value = params.q;

  for (const name of ['set', 'lang', 'stratum']) {
    const select = form.querySelector(`#${name}`);
    if (!select) continue;
    const has = Array.from(select.options).some((o) => o.value === params[name]);
    select.value = has ? params[name] : '';
  }

  const range = form.querySelector('#min_conf');
  const output = form.querySelector('#min_conf_out');
  if (range) {
    const value = Number(params.min_conf);
    range.value = Number.isFinite(value) && value > 0 ? String(value) : '0';
    if (output) output.value = conf(Number(range.value));
  }

  // The work restriction rides along as a hidden field so that submitting the
  // form keeps it, and the "search all works" link can drop it.
  let hidden = form.querySelector('input[name="work"]');
  if (params.work) {
    if (!hidden) {
      hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'work';
      form.append(hidden);
    }
    hidden.value = params.work;
  } else if (hidden) {
    hidden.remove();
  }
}

function meanConfChip(value) {
  const band = confBand(value);
  if (!band) return '';
  return chip(
    `chip--conf chip--conf-${band}`,
    `\u2300 ${conf(value)}`,
    t('search.hit.meanconf', { c: conf(value) }),
  );
}

/** Group hits by work_id: groups in first-appearance order, rank order inside. */
export function groupHits(hits) {
  const groups = new Map();
  for (const hit of hits || []) {
    const key = hit.work_id;
    let group = groups.get(key);
    if (!group) {
      group = {
        work_id: key,
        title: hit.title,
        shelfmarks: hit.shelfmarks || [],
        set: hit.set,
        hits: [],
      };
      groups.set(key, group);
    }
    group.hits.push(hit);
  }
  return Array.from(groups.values());
}

function renderHit(hit) {
  const label = folioLabel(hit.label, hit.seq);
  const href = `/page/${pathSeg(hit.page_id)}`;
  const thumb = hit.thumb_url
    ? `<a class="hit__thumb" href="${esc(href)}" tabindex="-1" aria-hidden="true">` +
      `<img src="${esc(hit.thumb_url)}" alt="" loading="lazy" decoding="async" /></a>`
    : '';
  const meta = [
    meanConfChip(hit.mean_conf),
    typeof hit.n_lines === 'number'
      ? `<span class="meta__item">${esc(tn('search.hit.lines', hit.n_lines))}</span>`
      : '',
    hit.lang ? `<span class="meta__item">${esc(langLabel(hit.lang))}</span>` : '',
    hit.stratum && hit.stratum !== 'unknown'
      ? `<span class="meta__item">${esc(stratumLabel(hit.stratum))}</span>`
      : '',
  ]
    .filter(Boolean)
    .join('');
  return (
    `<li class="hit">${thumb}<div class="hit__body">` +
    `<h4 class="hit__title"><a href="${esc(href)}">${esc(label)}</a></h4>` +
    `<p class="hit__snippet">${snippet(hit.snippet)}</p>` +
    `<p class="hit__meta">${meta}</p>` +
    `</div></li>`
  );
}

function renderGroup(group) {
  const title = group.title || t('search.noWork');
  const shelfmarks = (group.shelfmarks || []).join(' · ');
  const meta = [shelfmarks, setLabel(group.set)].filter(Boolean).join(' — ');
  return (
    `<article class="group">` +
    `<h3 class="group__title">` +
    `<a href="/work/${esc(pathSeg(group.work_id))}">${esc(title)}</a></h3>` +
    (meta ? `<p class="group__meta">${esc(meta)}</p>` : '') +
    `<ol class="hits">${group.hits.map(renderHit).join('')}</ol>` +
    `</article>`
  );
}

function renderPagination(params, data) {
  const limit = Number(data.limit) || Number(params.limit) || DEFAULT_LIMIT;
  const total = Number(data.total) || 0;
  const pageNo = Number(data.page) || params.page || 1;
  const pages = Math.max(1, Math.ceil(total / Math.max(1, limit)));
  if (pages <= 1) return '';

  const link = (target, label, rel) => {
    const qs = api.searchQuery({ ...params, page: target });
    return (
      `<a class="button" rel="${rel}" href="/search${qs ? `?${qs}` : ''}">${esc(label)}</a>`
    );
  };
  const disabled = (label) =>
    `<span class="button button--disabled" aria-disabled="true">${esc(label)}</span>`;

  const prev = pageNo > 1 ? link(pageNo - 1, t('search.prev'), 'prev') : disabled(t('search.prev'));
  const next =
    pageNo < pages ? link(pageNo + 1, t('search.next'), 'next') : disabled(t('search.next'));
  return (
    `<nav class="pagination" aria-label="${esc(t('search.pagination'))}">` +
    `${prev}<span class="pagination__status">${esc(t('search.pageOf', { page: num(pageNo), pages: num(pages) }))}</span>${next}` +
    `</nav>`
  );
}

function renderResults(params, data) {
  const total = Number(data.total) || 0;
  if (total === 0 || !(data.hits || []).length) {
    return (
      `<div class="state state--empty"><p>${esc(t('search.empty'))}</p>` +
      `<p class="hint">${esc(t('search.empty.hint'))}</p></div>`
    );
  }
  const summary =
    `<p class="results__summary">` +
    `<strong>${esc(tn('search.summary', total, { total: num(total), ms: num(Number(data.took_ms) || 0) }))}</strong>` +
    (data.query ? ` <span class="muted">${esc(t('search.query', { q: data.query }))}</span>` : '') +
    (data.backend
      ? ` <span class="muted">${esc(t('search.backend', { backend: data.backend }))}</span>`
      : '') +
    `</p>`;
  const groups = groupHits(data.hits).map(renderGroup).join('');
  return summary + groups + renderPagination(params, data);
}

export async function render(ctx) {
  const { root, query, signal, searchPanel } = ctx;
  const params = readParams(query);

  root.innerHTML =
    `<div id="search-form-slot"></div>` +
    (params.work
      ? `<p class="notice notice--inline">${esc(t('search.filteredToWork'))} ` +
        `<a href="/search?${esc(api.searchQuery({ ...params, work: '', page: 1 }))}">${esc(t('search.clearWork'))}</a></p>`
      : '') +
    `<section class="results" aria-labelledby="results-heading">` +
    `<h2 id="results-heading">${esc(t('search.results'))}</h2>` +
    `<div id="results" class="results__body" aria-live="polite" aria-busy="false"></div>` +
    `</section>`;

  // Re-insert the statically delivered form and fill it from the URL.
  const slot = root.querySelector('#search-form-slot');
  if (searchPanel && slot) {
    slot.replaceWith(searchPanel);
    fillForm(searchPanel, params);
  }

  const results = root.querySelector('#results');
  document.title = params.q
    ? `${params.q} — ${t('search.heading')} — ${t('site.name')}`
    : `${t('search.heading')} — ${t('site.name')}`;

  if (!params.q && !params.work) {
    results.innerHTML = `<p class="state state--start">${esc(t('search.start'))}</p>`;
    return;
  }

  results.setAttribute('aria-busy', 'true');
  results.innerHTML = loading(t('search.loading'));

  let data;
  try {
    data = await api.search(params, signal);
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    results.setAttribute('aria-busy', 'false');
    results.innerHTML = errorPanel(err, { heading: t('search.error') });
    return;
  }
  if (signal.aborted) return;

  results.setAttribute('aria-busy', 'false');
  results.innerHTML = renderResults(params, data);
}
