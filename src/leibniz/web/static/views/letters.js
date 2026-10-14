// views/letters.js — Leibniz's letters by correspondent, date and place, as
// Eduard Bodemann catalogued them in 1889 (the LBr numbering), letter by letter
// from correspSearch (BBAW; CC BY 4.0). The filters ride in the address
// (?who=&place=&from=&to=&direction=&work=&page=), so a list can be linked.

import { t, tn } from '../i18n.js';
import * as api from '../api.js';
import { esc, num, pathSeg } from '../dom.js';
import { errorPanel, loading } from './common.js';
import { lettersTable, letterDate, people } from './work.js';

const LIMIT = 50;
const FIELDS = ['who', 'place', 'from', 'to', 'direction', 'work'];

export function readLetterParams(query) {
  const get = (k) => (query.get(k) || '').trim();
  const out = {};
  for (const key of FIELDS) out[key] = get(key);
  const page = Number(get('page'));
  out.page = Number.isInteger(page) && page > 1 ? page : 1;
  return out;
}

export function letterQuery(params) {
  const qs = new URLSearchParams();
  for (const key of FIELDS) if (params[key]) qs.set(key, params[key]);
  if (params.page > 1) qs.set('page', String(params.page));
  return qs.toString();
}

function form(params) {
  const field = (name, label, attrs = '') =>
    `<p class="field"><label class="field__label" for="letters-${name}">${esc(t(label))}</label>` +
    `<input id="letters-${name}" name="${name}" value="${esc(params[name])}" ${attrs} /></p>`;
  const dir = (value, label) =>
    `<option value="${value}"${params.direction === value ? ' selected' : ''}>${esc(t(label))}</option>`;
  return (
    `<form class="letters-form" method="get" action="/letters" role="search">` +
    field('who', 'letters.who', 'type="search" autocomplete="off"') +
    field('place', 'letters.place', 'type="search" autocomplete="off"') +
    field('from', 'letters.from', 'type="number" min="1600" max="1800" inputmode="numeric"') +
    field('to', 'letters.to', 'type="number" min="1600" max="1800" inputmode="numeric"') +
    `<p class="field"><label class="field__label" for="letters-direction">${esc(t('letters.direction'))}</label>` +
    `<select id="letters-direction" name="direction">` +
    dir('', 'letters.direction.any') +
    dir('to', 'letters.direction.to') +
    dir('from', 'letters.direction.from') +
    `</select></p>` +
    (params.work ? `<input type="hidden" name="work" value="${esc(params.work)}" />` : '') +
    `<p class="field"><button type="submit" class="button button--primary">${esc(t('letters.go'))}</button></p>` +
    `</form>`
  );
}

function pagination(params, total) {
  const pages = Math.max(1, Math.ceil(total / LIMIT));
  if (pages <= 1) return '';
  const link = (page, label, rel) =>
    `<a class="button" rel="${rel}" href="/letters?${esc(letterQuery({ ...params, page }))}">${esc(label)}</a>`;
  const off = (label) => `<span class="button button--disabled" aria-disabled="true">${esc(label)}</span>`;
  return (
    `<nav class="pagination" aria-label="${esc(t('search.pagination'))}">` +
    (params.page > 1 ? link(params.page - 1, t('search.prev'), 'prev') : off(t('search.prev'))) +
    `<span class="pagination__status">${esc(t('search.pageOf', { page: num(params.page), pages: num(pages) }))}</span>` +
    (params.page < pages ? link(params.page + 1, t('search.next'), 'next') : off(t('search.next'))) +
    `</nav>`
  );
}

/** One letter with the convolutes that carry it. */
function withWorks(letter) {
  const works = (letter.works || [])
    .map((id) => `<a href="/work/${esc(pathSeg(id))}">${esc(t('letters.convolute'))}</a>`)
    .join(' ');
  return { ...letter, _works: works };
}

function results(params, data) {
  const total = Number(data.total) || 0;
  if (!total) return `<p class="state state--empty">${esc(t('letters.none'))}</p>`;
  const rows = (data.letters || []).map(withWorks);
  const body = rows
    .map(
      (letter) =>
        `<tr><td class="num">${esc(letter.key)}</td><td>${esc(letterDate(letter))}</td>` +
        `<td>${people(letter.senders)} → ${people(letter.addressees)}</td>` +
        `<td>${letter.place ? esc(letter.place.name) : ''}</td><td>${letter._works}</td></tr>`,
    )
    .join('');
  return (
    `<p class="results__summary"><strong>${esc(tn('letters.count', total, { n: num(total) }))}</strong></p>` +
    `<table class="letters"><thead><tr>` +
    `<th scope="col">${esc(t('letters.col.key'))}</th><th scope="col">${esc(t('letters.col.date'))}</th>` +
    `<th scope="col">${esc(t('letters.col.people'))}</th><th scope="col">${esc(t('letters.col.place'))}</th>` +
    `<th scope="col">${esc(t('letters.col.scan'))}</th></tr></thead><tbody>${body}</tbody></table>` +
    pagination(params, total)
  );
}

export async function render(ctx) {
  const { root, query, signal } = ctx;
  const params = readLetterParams(query);
  document.title = `${t('letters.heading')} — ${t('site.name')}`;
  root.innerHTML =
    `<article class="letters-view">` +
    `<header class="panel"><h1 tabindex="-1" data-view-heading>${esc(t('letters.heading'))}</h1>` +
    `<p>${esc(t('letters.intro'))}</p>` +
    (params.work
      ? `<p class="notice notice--inline">${esc(t('letters.oneWork'))} ` +
        `<a href="/letters?${esc(letterQuery({ ...params, work: '', page: 1 }))}">${esc(t('letters.allWorks'))}</a></p>`
      : '') +
    form(params) +
    `</header>` +
    `<section class="panel" aria-live="polite" id="letters-results">${loading(t('letters.loading'))}</section>` +
    `<p class="attribution__line">${esc(t('letters.attr'))}</p>` +
    `</article>`;
  const box = root.querySelector('#letters-results');
  let data;
  try {
    data = await api.letters({ ...params, limit: LIMIT }, signal);
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    box.innerHTML =
      err instanceof api.ApiError && err.status === 503
        ? `<p class="state state--empty">${esc(t('letters.unavailable'))}</p>`
        : errorPanel(err);
    return;
  }
  if (signal.aborted) return;
  box.innerHTML = results(params, data);
}

export { lettersTable };
