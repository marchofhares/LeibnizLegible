// views/common.js — fragments every view reuses. Pure HTML-string builders,
// no knowledge of the router.

import { t, getLang } from '../i18n.js';
import { esc } from '../dom.js';
import { ApiError } from '../api.js';

/** An ISO date as the reader's language writes it: "19 October 2026", "19. Oktober 2026". */
export function longDate(iso) {
  if (!iso) return '';
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(getLang() === 'de' ? 'de-DE' : 'en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

/**
 * The catalogue data's source line, written once in the registry
 * (leibniz.legal.arbeitskatalog_credit) and carried by the API as `credit` /
 * `katalog_credit`: the catalogue and the Arbeitsstelle linked, the licence,
 * the export's date.
 */
export function sourceLine(credit) {
  if (!credit || !credit.catalogue) return '';
  return (
    `<p class="attribution__line katalog-source">${esc(t('katalog.source.label'))}: ` +
    `<a href="${esc(credit.catalogue.url)}" rel="noopener">${esc(credit.catalogue.name)}</a>, ` +
    `<a href="${esc(credit.edition.url)}" rel="noopener">${esc(credit.edition.name)}</a>, ` +
    `${esc(credit.licence)}, ${esc(t('katalog.source.export', { date: longDate(credit.export_date) }))}</p>`
  );
}

/** The standing honesty notice. Shown at the top of every page view. */
export function honestyBanner() {
  return `<aside class="banner banner--honesty">${esc(t('honesty.banner'))}</aside>`;
}

/** A neutral "working on it" block. */
export function loading(message) {
  return `<p class="state state--loading">${esc(message)}</p>`;
}

/** Turn an error into a panel. `retry` is a data-action name for a button. */
export function errorPanel(err, opts) {
  const { retry, heading } = opts || {};
  let detail;
  if (err instanceof ApiError) {
    detail = err.status === 0 ? t('error.network') : t('error.http', { status: err.status });
    if (err.detail) detail += ` ${err.detail}`;
  } else {
    detail = err && err.message ? err.message : t('error.network');
  }
  const button = retry
    ? `<p><button type="button" class="button" data-action="${esc(retry)}">${esc(t('error.retry'))}</button></p>`
    : '';
  return (
    `<div class="panel state state--error" role="alert">` +
    `<h2>${esc(heading || t('error.h'))}</h2>` +
    `<p>${esc(detail)}</p>${button}</div>`
  );
}

/** The 404 view body. */
export function notFoundPanel(message) {
  return (
    `<div class="panel state state--notfound">` +
    `<h1 tabindex="-1" data-view-heading>${esc(t('error.notfound.h'))}</h1>` +
    `<p>${esc(message || t('error.notfound.p'))}</p>` +
    `<p><a href="/search">${esc(t('error.notfound.back'))}</a></p></div>`
  );
}

/** Render "not found" into a root element and set the document title. */
export function renderNotFound(root, message) {
  root.innerHTML = notFoundPanel(message);
  document.title = `${t('error.notfound.h')} — ${t('site.name')}`;
}
