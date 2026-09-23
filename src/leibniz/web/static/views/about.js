// views/about.js — the honest page. What this is, how wrong it is, who owns
// what, and how to tell us we are wrong.

import { t, getLang, setLang } from '../i18n.js';
import * as api from '../api.js';
import { esc, num, pct, chip, statusBadge } from '../dom.js';
import { errorPanel } from './common.js';

/** The confidence histogram buckets, in the order the API reports them. */
const BANDS = [
  { key: 'ge_0.9', band: 5, label: '≥ 0.90' },
  { key: '0.8_0.9', band: 4, label: '0.80 – 0.90' },
  { key: '0.7_0.8', band: 3, label: '0.70 – 0.80' },
  { key: '0.5_0.7', band: 2, label: '0.50 – 0.70' },
  { key: 'lt_0.5', band: 1, label: '< 0.50' },
];

function langSwitch() {
  const current = getLang();
  const button = (code, label) =>
    `<button type="button" class="button button--small" data-about-lang="${code}"` +
    ` aria-pressed="${current === code}">${esc(label)}</button>`;
  return (
    `<p class="about__lang">${esc(t('about.lang.p'))} ` +
    `<span class="lang-switch lang-switch--inline" role="group" aria-label="${esc(t('lang.label'))}">` +
    `${button('en', 'English')}${button('de', 'Deutsch')}</span></p>`
  );
}

function statTiles(data) {
  const tiles = [
    ['about.numbers.works', data.works],
    ['about.numbers.pages', data.pages],
    ['about.numbers.recognized', data.pages_recognized],
    ['about.numbers.skipped', data.pages_skipped],
    ['about.numbers.lines', data.lines],
  ];
  return (
    `<ul class="stats">` +
    tiles
      .map(
        ([key, value]) =>
          `<li class="stat"><span class="stat__value">${esc(num(Number(value)))}</span>` +
          `<span class="stat__label">${esc(t(key))}</span></li>`,
      )
      .join('') +
    `</ul>`
  );
}

function histogram(data) {
  const hist = data.conf_histogram || {};
  const total = BANDS.reduce((sum, b) => sum + (Number(hist[b.key]) || 0), 0);
  if (!total) return '';
  const rows = BANDS.map((b) => {
    const value = Number(hist[b.key]) || 0;
    const share = value / total;
    const width = Math.max(0.6, share * 100);
    return (
      `<tr><th scope="row">${chip(`chip--conf chip--conf-${b.band}`, b.label, b.label)}</th>` +
      `<td class="num">${esc(num(value))}</td>` +
      `<td class="num">${esc(pct(share))}</td>` +
      `<td class="bar-cell"><span class="bar bar--${b.band}" style="width:${width.toFixed(1)}%"></span></td></tr>`
    );
  }).join('');
  return (
    `<table class="hist">` +
    `<caption>${esc(t('about.hist.h'))}</caption>` +
    `<thead><tr><th scope="col">${esc(t('about.hist.band'))}</th>` +
    `<th scope="col" class="num">${esc(t('about.hist.lines'))}</th>` +
    `<th scope="col" class="num">${esc(t('about.hist.share'))}</th>` +
    `<th scope="col"><span class="sr-only">${esc(t('about.hist.share'))}</span></th></tr></thead>` +
    `<tbody>${rows}</tbody></table>`
  );
}

function provenanceRows(data) {
  const rows = [
    ['about.numbers.version', data.version],
    ['about.numbers.backend', data.backend],
    ['about.numbers.model', data.model],
  ].filter(([, value]) => value !== null && value !== undefined && value !== '');
  if (!rows.length) return '';
  return (
    `<dl class="deflist deflist--tight">` +
    rows
      .map(
        ([key, value]) =>
          `<div class="deflist__row"><dt>${esc(t(key))}</dt><dd><code>${esc(value)}</code></dd></div>`,
      )
      .join('') +
    `</dl>`
  );
}

function legend() {
  const items = ['machine', 'aligned', 'corrected', 'verified'].map(
    (status) =>
      `<li class="legend__item">${statusBadge(status)}` +
      `<span class="legend__help">${esc(t(`status.${status}.help`))}</span></li>`,
  );
  return `<ul class="legend">${items.join('')}</ul>`;
}

/** Where the page images come from, stamped into the shell by the server. */
function imageOrigin() {
  return document.documentElement.dataset.imageOrigin === 'mirror' ? 'mirror' : 'gwlb';
}

function licensing() {
  const images = imageOrigin() === 'mirror' ? 'about.license.images.p.mirror' : 'about.license.images.p';
  const blocks = [
    ['about.license.images.h', images],
    ['about.license.katalog.h', 'about.license.katalog.p'],
    ['about.license.transcriptions.h', 'about.license.transcriptions.p'],
    ['about.license.code.h', 'about.license.code.p'],
  ];
  return blocks
    .map(
      ([h, p]) =>
        `<div class="license"><h3>${esc(t(h))}</h3><p>${esc(t(p))}</p></div>`,
    )
    .join('');
}

export async function render(ctx) {
  const { root, signal } = ctx;
  document.title = `${t('about.heading')} — ${t('site.name')}`;

  root.innerHTML =
    `<article class="about">` +
    `<header class="panel">` +
    `<h1 tabindex="-1" data-view-heading>${esc(t('about.heading'))}</h1>` +
    langSwitch() +
    `</header>` +

    `<section class="panel" aria-labelledby="about-what">` +
    `<h2 id="about-what">${esc(t('about.what.h'))}</h2>` +
    `<p>${esc(t('about.what.p1'))}</p>` +
    `<p>${esc(t('about.what.p2'))}</p>` +
    `<p>${esc(t(imageOrigin() === 'mirror' ? 'about.what.p3.mirror' : 'about.what.p3'))}</p>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-numbers">` +
    `<h2 id="about-numbers">${esc(t('about.numbers.h'))}</h2>` +
    `<div id="about-stats" aria-live="polite" aria-busy="true">` +
    `<p class="state state--loading">${esc(t('about.numbers.loading'))}</p></div>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-error">` +
    `<h2 id="about-error">${esc(t('about.error.h'))}</h2>` +
    `<p>${esc(t('about.error.p1'))}</p>` +
    `<p>${esc(t('about.error.p2'))}</p>` +
    `<p class="muted">${esc(t('about.error.p3'))}</p>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-legend">` +
    `<h2 id="about-legend">${esc(t('about.legend.h'))}</h2>` +
    `<p>${esc(t('about.legend.intro'))}</p>` +
    legend() +
    `</section>` +

    `<section class="panel" aria-labelledby="about-report">` +
    `<h2 id="about-report">${esc(t('about.report.h'))}</h2>` +
    `<p>${esc(t('about.report.p'))}</p>` +
    `<p><a href="${esc(api.REPO_URL)}/issues" rel="noopener">${esc(api.REPO_URL)}/issues</a></p>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-license">` +
    `<h2 id="about-license">${esc(t('about.license.h'))}</h2>` +
    licensing() +
    `</section>` +

    `<section class="panel" aria-labelledby="about-who">` +
    `<h2 id="about-who">${esc(t('about.who.h'))}</h2>` +
    `<p>${esc(t('about.who.p1'))}</p>` +
    `<p>${esc(t('about.who.p2'))}</p>` +
    `<p><a href="https://evanatlas.com/" rel="noopener">evanatlas.com</a> · ` +
    `<a href="https://orcid.org/0009-0007-7374-2338" rel="noopener">ORCID</a></p>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-credits">` +
    `<h2 id="about-credits">${esc(t('about.credits.h'))}</h2>` +
    `<ul>` +
    ['images', 'katalog', 'model', 'edition', 'precedents']
      .map((key) => `<li>${esc(t(`about.credits.${key}`))}</li>`)
      .join('') +
    `</ul>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-edition">` +
    `<h2 id="about-edition">${esc(t('about.edition.h'))}</h2>` +
    `<p>${esc(t('about.edition.p1'))}</p>` +
    `<p>${esc(t('about.edition.p2'))}</p>` +
    `<p>` +
    `<a href="https://www.leibnizedition.de/" rel="noopener">leibnizedition.de</a> · ` +
    `<a href="https://leibniz-katalog.bbaw.de/" rel="noopener">Arbeitskatalog</a> · ` +
    `<a href="https://www.gwlb.de/leibniz" rel="noopener">GWLB / Leibniz-Archiv</a> · ` +
    `<a href="https://www.leibniz-translations.com/" rel="noopener">Leibniz Translations</a>` +
    `</p>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-timeline">` +
    `<h2 id="about-timeline">${esc(t('about.timeline.h'))}</h2>` +
    `<ul>` +
    ['1716', '1889', '1901', '1923', '2007', '2016', '2026a', '2026b', '2055']
      .map((key) => `<li>${esc(t(`about.timeline.${key}`))}</li>`)
      .join('') +
    `</ul>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-cite">` +
    `<h2 id="about-cite">${esc(t('about.cite.h'))}</h2>` +
    `<p>${esc(t('about.cite.p'))}</p>` +
    `</section>` +

    `<section class="panel" aria-labelledby="about-repo">` +
    `<h2 id="about-repo">${esc(t('about.repo.h'))}</h2>` +
    `<p>${esc(t('about.repo.p'))} ` +
    `<a href="${esc(api.REPO_URL)}" rel="noopener">${esc(api.REPO_URL)}</a></p>` +
    `<p>${esc(t('about.repo.reports'))}</p>` +
    `</section>` +

    `</article>`;

  const onLangClick = (event) => {
    const button = event.target.closest ? event.target.closest('[data-about-lang]') : null;
    if (!button) return;
    setLang(button.getAttribute('data-about-lang'));
  };
  root.addEventListener('click', onLangClick);

  // The figures load in the background so that the view — and its cleanup —
  // are in place immediately, whatever the API does.
  const box = root.querySelector('#about-stats');
  api
    .stats(signal)
    .then((data) => {
      if (signal.aborted) return;
      box.setAttribute('aria-busy', 'false');
      box.innerHTML =
        statTiles(data) +
        `<p class="muted">${esc(t('about.numbers.caveat'))}</p>` +
        provenanceRows(data) +
        histogram(data);
    })
    .catch((err) => {
      if (signal.aborted || (err && err.name === 'AbortError')) return;
      box.setAttribute('aria-busy', 'false');
      box.innerHTML = errorPanel(err, { heading: t('about.numbers.error') });
    });

  return function cleanup() {
    root.removeEventListener('click', onLangClick);
  };
}
