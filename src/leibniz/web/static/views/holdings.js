// views/holdings.js — where Leibniz's papers lie: the Arbeitskatalog's records
// by the institution their shelfmark names, the digitised copies it links by
// domain, and the GWLB's digitised works with and without records. The figures
// come from /api/holdings (leibniz.catalog.holdings over the store); the page
// says whether they cover the whole catalogue (the Arbeitsstelle's export,
// with its date) or the part the site held before it.

import { t } from '../i18n.js';
import * as api from '../api.js';
import { esc, num, pct } from '../dom.js';
import { errorPanel, loading } from './common.js';

/**
 * Holdings with fewer records than this are summed as "other" — on a store of
 * the whole catalogue; a small store (a staging copy, the fixture) shows every row.
 */
function minRecords(data) {
  return (data.records || 0) >= 1000 ? 20 : 1;
}

const LABELS = {
  '(printed witness, no manuscript named)': 'holdings.label.printed',
  '(private collection)': 'holdings.label.private',
  '(whereabouts not stated)': 'holdings.label.unlocated',
  '(no shelfmark)': 'holdings.label.none',
};

/** The API's English labels for the records that name no institution, in the reader's language. */
function holdingName(name) {
  const key = LABELS[name];
  return key ? t(key) : name;
}

function table(caption, head, rows) {
  const ths = head
    .map(([label, numeric]) => `<th scope="col"${numeric ? ' class="num"' : ''}>${esc(label)}</th>`)
    .join('');
  const body = rows
    .map(
      (cells) =>
        `<tr>${cells
          .map(([value, numeric], i) =>
            i === 0
              ? `<th scope="row">${value}</th>`
              : `<td${numeric ? ' class="num"' : ''}>${value}</td>`,
          )
          .join('')}</tr>`,
    )
    .join('');
  // the table scrolls inside its box on a narrow screen; the page never does
  return (
    `<div class="table-scroll"><table class="hist holdings__table">` +
    `<caption>${esc(caption)}</caption>` +
    `<thead><tr>${ths}</tr></thead><tbody>${body}</tbody></table></div>`
  );
}

function byHolding(data) {
  const total = data.records || 0;
  const min = minRecords(data);
  const rows = [];
  let tailCount = 0;
  let tailN = 0;
  for (const row of data.by_holding || []) {
    if (row.records >= min) {
      rows.push([
        [esc(holdingName(row.holding)), false],
        [esc(num(row.records)), true],
        [esc(pct(total ? row.records / total : 0)), true],
      ]);
    } else {
      tailN += 1;
      tailCount += row.records;
    }
  }
  if (tailN) {
    rows.push([
      [`<span class="muted">${esc(t('holdings.other', { n: num(tailN) }))}</span>`, false],
      [esc(num(tailCount)), true],
      [esc(pct(total ? tailCount / total : 0)), true],
    ]);
  }
  return (
    `<section class="panel" aria-labelledby="holdings-by">` +
    `<h2 id="holdings-by">${esc(t('holdings.byHolding.h'))}</h2>` +
    `<p>${esc(t('holdings.byHolding.p', { n: num(min) }))}</p>` +
    table(
      t('holdings.byHolding.h'),
      [
        [t('holdings.col.holding'), false],
        [t('holdings.col.records'), true],
        [t('holdings.col.share'), true],
      ],
      rows,
    ) +
    `</section>`
  );
}

function byDomain(data) {
  const links = data.gwlb_links || {};
  const min = minRecords(data);
  const rows = [];
  let tail = 0;
  for (const row of data.by_domain || []) {
    if (row.records >= min) rows.push([[esc(row.domain), false], [esc(num(row.records)), true]]);
    else tail += row.records;
  }
  if (tail) rows.push([[`<span class="muted">${esc(t('holdings.other', { n: '…' }))}</span>`, false], [esc(num(tail)), true]]);
  return (
    `<section class="panel" aria-labelledby="holdings-domains">` +
    `<h2 id="holdings-domains">${esc(t('holdings.byDomain.h'))}</h2>` +
    `<p>${esc(
      t('holdings.byDomain.p', {
        with: num(data.with_url || 0),
        records: num(data.records || 0),
        id: num(links.id || 0),
        ppn: num(links.PPN || 0),
      }),
    )}</p>` +
    (rows.length
      ? table(
          t('holdings.byDomain.h'),
          [
            [t('holdings.col.domain'), false],
            [t('holdings.col.records'), true],
          ],
          rows,
        )
      : '') +
    `</section>`
  );
}

function works(data) {
  const known = typeof data.works === 'number' && typeof data.works_with_records === 'number';
  const body = known
    ? `<p>${esc(
        t('holdings.works.p', {
          with: num(data.works_with_records),
          total: num(data.works),
          without: num(data.works_without_records || 0),
        }),
      )}</p>` +
      table(
        t('holdings.works.h'),
        [
          [t('holdings.col.set'), false],
          [t('holdings.col.works'), true],
          [t('holdings.col.with'), true],
          [t('holdings.col.without'), true],
        ],
        (data.by_set || []).map((s) => [
          [esc(s.set), false],
          [esc(num(s.works)), true],
          [esc(num(s.with_records)), true],
          [esc(num(s.works - s.with_records)), true],
        ]),
      )
    : `<p class="muted">${esc(t('holdings.works.none'))}</p>`;
  return (
    `<section class="panel" aria-labelledby="holdings-works">` +
    `<h2 id="holdings-works">${esc(t('holdings.works.h'))}</h2>${body}</section>`
  );
}

function page(data) {
  const intro = data.refreshed
    ? t('holdings.intro', { records: num(data.records || 0), date: data.refreshed })
    : t('holdings.intro.partial', { records: num(data.records || 0) });
  return (
    `<p>${esc(intro)}</p>` +
    byHolding(data) +
    byDomain(data) +
    works(data) +
    `<section class="panel" aria-labelledby="holdings-method">` +
    `<h2 id="holdings-method">${esc(t('holdings.method.h'))}</h2>` +
    `<p>${esc(t('holdings.method.p'))}</p>` +
    `<p class="attribution__line">${esc(t('work.katalog.attr'))}</p>` +
    `</section>`
  );
}

export async function render(ctx) {
  const { root, signal } = ctx;
  document.title = `${t('holdings.heading')} — ${t('site.name')}`;
  root.innerHTML =
    `<article class="holdings">` +
    `<header class="panel"><h1 tabindex="-1" data-view-heading>${esc(t('holdings.heading'))}</h1></header>` +
    `<div id="holdings-body" aria-live="polite" aria-busy="true">${loading(t('holdings.loading'))}</div>` +
    `</article>`;
  const box = root.querySelector('#holdings-body');
  try {
    const data = await api.holdings(signal);
    if (signal.aborted) return undefined;
    box.setAttribute('aria-busy', 'false');
    box.innerHTML = page(data);
  } catch (err) {
    if (signal.aborted || (err && err.name === 'AbortError')) return undefined;
    box.setAttribute('aria-busy', 'false');
    box.innerHTML = errorPanel(err, { heading: t('holdings.error') });
  }
  return undefined;
}
