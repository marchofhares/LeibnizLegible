// views/browse.js — the browse index at /browse: the Nachlass by shelfmark
// family, section and convolute.
//
// One request (GET /api/works: a compact row per work, and the tree of
// sections with the work ids in order) draws the whole index. Everything after
// that happens on the page: the filter, the order of the letter convolutes,
// opening a section, following a #fragment such as /browse#lh-35.
//
// Family and section names arrive as data and are the archive's own German
// words in both languages; only the chrome around them is translated.

import { t, tn } from '../i18n.js';
import * as api from '../api.js';
import { esc, pathSeg, num, chip } from '../dom.js';
import { errorPanel, loading } from './common.js';

// Kept while the app is open, across re-renders (a language switch draws the
// view again): the index itself, what the reader typed, the order of the
// letters, and the sections they opened.
const kept = { data: null, filter: '', lbrOrder: 'name', open: new Set() };

/** Lower case, accents off, everything that is not a letter or digit one space. */
export function fold(text) {
  return String(text ?? '')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/ß/g, 'ss')
    .replace(/æ/g, 'ae')
    .replace(/œ/g, 'oe')
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim();
}

/**
 * What the filter looks for in an entry's folded text: the query as one run
 * of words, starting at a word ("35" finds LH 35, not LBr. 135) and, when the
 * reader has typed a separator after it, ending at one ("LH 3," is section 3
 * alone, "LH 3" still finds LH 35 while it is being typed).
 */
export function needleOf(query) {
  const folded = fold(query);
  if (!folded) return '';
  return ` ${folded}${/[^\p{L}\p{N}]$/u.test(query) ? ' ' : ''}`;
}

function haystack(work) {
  return ` ${fold([work.label, ...(work.shelfmarks || []), work.title].join(' '))} `;
}

function counts(nWorks, nPages) {
  return (
    `${tn('browse.works', nWorks, { n: num(nWorks) })} · ` +
    `${tn('browse.pageimages', nPages, { n: num(nPages) })}`
  );
}

/** A section's heading: the archive's name for it, or ours for a whole family. */
function sectionTitle(family, section) {
  if (family === 'LBr' || family === 'Marg') return t(`browse.all.${family}`);
  return section.title || section.label;
}

/** The two spans of a letter convolute's link, in the order of the list. */
function letterSpans(work, byNumber) {
  const mark = `<span class="entry__mark">${esc(work.shelfmark)}</span>`;
  if (work.label === work.shelfmark) return mark; // no correspondent established
  const name = `<span class="entry__label">${esc(work.label)}</span>`;
  return byNumber ? `${mark} ${name}` : `${name} ${mark}`;
}

function entry(family, work) {
  let inner;
  if (family === 'LH') {
    inner = `<span class="entry__mark">${esc(work.label)}</span>`;
  } else if (family === 'LBr') {
    inner = letterSpans(work, kept.lbrOrder === 'number');
  } else {
    // the shelfmark, then the title — cut by the server, whole in the tooltip
    const whole = work.title && work.title !== work.label ? ` title="${esc(work.title)}"` : '';
    const label =
      work.label !== work.shelfmark
        ? `<span class="entry__label"${whole}>${esc(work.label)}</span>`
        : '';
    const mark = work.shelfmark ? `<span class="entry__mark">${esc(work.shelfmark)}</span> ` : '';
    inner = mark + label;
  }
  const pages = tn('browse.pages', work.n_canvases, { n: num(work.n_canvases) });
  const records = work.has_katalog
    ? chip('chip--kat', t('browse.katalog.short'), t('browse.katalog'))
    : '';
  return (
    `<li class="entry" data-work="${esc(work.work_id)}">` +
    `<a class="entry__link" href="/work/${esc(pathSeg(work.work_id))}">${inner}</a> ` +
    `<span class="entry__meta"><span class="entry__pages">${esc(pages)}</span>${records}</span>` +
    `</li>`
  );
}

function sortControls() {
  const button = (order) =>
    `<button type="button" class="button button--small" data-order="${order}" ` +
    `aria-pressed="${kept.lbrOrder === order}">${esc(t(`browse.sort.${order}`))}</button>`;
  return (
    `<div class="section__sort" role="group" aria-label="${esc(t('browse.sort.label'))}">` +
    `${button('name')}${button('number')}</div>`
  );
}

function sectionBlock(family, section, works) {
  const items = section.entries
    .map((id) => works.get(id))
    .filter(Boolean)
    .map((work) => entry(family, work))
    .join('');
  // In name order the letters without a name follow the named ones; one line
  // says so. (reorder() moves it to its place and hides it in number order.)
  const note = section.by_number
    ? `<li class="entries__note" data-note hidden>${esc(t('browse.unnamed'))}</li>`
    : '';
  return (
    `<details class="section" id="${esc(section.anchor)}">` +
    `<summary class="section__summary">` +
    `<span class="section__title">${esc(sectionTitle(family, section))}</span> ` +
    `<span class="section__count" data-count></span></summary>` +
    (section.by_number ? sortControls() : '') +
    `<ul class="entries entries--${esc(family.toLowerCase())}">${items}${note}</ul>` +
    `</details>`
  );
}

function familyBlock(group, works) {
  const key = group.family;
  const name = t(`browse.family.${key}`);
  const about = t(`browse.about.${key}`);
  return (
    `<section class="panel family" data-family="${esc(key)}" aria-labelledby="family-${esc(key)}">` +
    `<h2 id="family-${esc(key)}">${esc(name === `browse.family.${key}` ? group.name : name)}</h2>` +
    `<p class="muted family__meta">${esc(counts(group.n_works, group.n_pages))}</p>` +
    (about === `browse.about.${key}` ? '' : `<p class="family__about">${esc(about)}</p>`) +
    group.sections.map((section) => sectionBlock(key, section, works)).join('') +
    `</section>`
  );
}

function safeDecode(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export async function render(ctx) {
  const { root, signal } = ctx;
  document.title = `${t('browse.heading')} — ${t('site.name')}`;

  if (!kept.data) {
    root.innerHTML = `<div class="panel">${loading(t('browse.loading'))}</div>`;
    try {
      kept.data = await api.works(signal);
    } catch (err) {
      if (err && err.name === 'AbortError') return undefined;
      root.innerHTML = errorPanel(err);
      return undefined;
    }
    if (signal.aborted) return undefined;
  }
  const data = kept.data;
  const works = new Map((data.works || []).map((work) => [work.work_id, work]));
  // A link to a section must show it, whatever was typed here before.
  if (location.hash) kept.filter = '';

  root.innerHTML =
    `<article class="browse">` +
    `<header class="panel browse__header">` +
    `<h1 tabindex="-1" data-view-heading>${esc(t('browse.heading'))}</h1>` +
    `<p>${esc(t('browse.intro'))}</p>` +
    `<p class="muted">${esc(counts(data.n_works, data.n_pages))}</p>` +
    `<div class="browse__filter">` +
    `<label class="field__label" for="browse-filter">${esc(t('browse.filter.label'))}</label>` +
    `<input type="search" id="browse-filter" autocomplete="off" spellcheck="false" ` +
    `placeholder="${esc(t('browse.filter.placeholder'))}" aria-describedby="browse-status" />` +
    `<p class="hint" id="browse-status" role="status" aria-live="polite"></p>` +
    `</div></header>` +
    (data.groups || []).map((group) => familyBlock(group, works)).join('') +
    `<p class="attribution__line browse__note">${esc(t('browse.note'))}</p>` +
    `</article>`;

  const input = root.querySelector('#browse-filter');
  const status = root.querySelector('#browse-status');
  input.value = kept.filter;

  // What the listeners work on: every section with its entries and their
  // folded text, read once.
  const sections = [];
  for (const group of data.groups || []) {
    const block = root.querySelector(`[data-family="${CSS.escape(group.family)}"]`);
    for (const section of group.sections) {
      const details = block.querySelector(`#${CSS.escape(section.anchor)}`);
      const rows = new Map();
      for (const li of details.querySelectorAll('li.entry')) rows.set(li.dataset.work, li);
      sections.push({
        section,
        block,
        details,
        list: details.querySelector('ul.entries'),
        count: details.querySelector('[data-count]'),
        note: details.querySelector('[data-note]'),
        rows,
        items: section.entries
          .filter((id) => rows.has(id))
          .map((id) => ({ li: rows.get(id), work: works.get(id), hay: haystack(works.get(id)) })),
      });
    }
  }

  /** Put the letters in the chosen order, and the "no name yet" line with them. */
  function reorder(sec) {
    if (!sec.section.by_number) return;
    const byNumber = kept.lbrOrder === 'number';
    const order = byNumber ? sec.section.by_number : sec.section.entries;
    const unnamed = (id) => {
      const work = works.get(id);
      return work && work.label === work.shelfmark;
    };
    const nodes = [];
    let noted = false;
    for (const id of order) {
      const li = sec.rows.get(id);
      if (!li) continue;
      li.firstElementChild.innerHTML = letterSpans(works.get(id), byNumber);
      if (!byNumber && !noted && unnamed(id)) {
        nodes.push(sec.note);
        noted = true;
      }
      nodes.push(li);
    }
    if (!nodes.includes(sec.note)) nodes.push(sec.note);
    sec.list.append(...nodes);
    for (const button of sec.details.querySelectorAll('[data-order]')) {
      button.setAttribute('aria-pressed', String(button.dataset.order === kept.lbrOrder));
    }
  }

  /** Show what matches the filter; with none, the sections the reader opened. */
  function apply() {
    const needle = needleOf(kept.filter);
    let shown = 0;
    for (const sec of sections) {
      let here = 0;
      let unnamedHere = 0;
      for (const item of sec.items) {
        const hit = !needle || item.hay.includes(needle);
        item.li.hidden = !hit;
        if (hit) {
          here += 1;
          if (item.work.label === item.work.shelfmark) unnamedHere += 1;
        }
      }
      shown += here;
      sec.details.hidden = here === 0;
      sec.details.open = needle ? here > 0 : kept.open.has(sec.section.anchor);
      sec.count.textContent = needle
        ? t('browse.matching', { n: num(here), total: num(sec.items.length) })
        : counts(sec.section.n_works, sec.section.n_pages);
      if (sec.note) sec.note.hidden = kept.lbrOrder === 'number' || unnamedHere === 0;
    }
    const blocks = new Set(sections.map((sec) => sec.block));
    for (const block of blocks) {
      block.hidden = sections.every((sec) => sec.block !== block || sec.details.hidden);
    }
    if (!needle) status.textContent = '';
    else if (shown === 0) status.textContent = t('browse.filter.none');
    else {
      status.textContent = tn('browse.filter.count', shown, {
        n: num(shown),
        total: num(data.n_works),
      });
    }
  }

  /** Open the section the address's #fragment names, and go there. */
  function followHash() {
    const id = safeDecode(location.hash.slice(1));
    const target = id ? document.getElementById(id) : null;
    if (!target || !root.contains(target)) return;
    if (target.tagName === 'DETAILS') {
      kept.open.add(id);
      target.hidden = false;
      target.open = true;
    }
    const summary = target.querySelector('summary') || target;
    summary.focus({ preventScroll: true });
    target.scrollIntoView({ block: 'start' });
  }

  for (const sec of sections) reorder(sec);
  apply();
  followHash();

  input.addEventListener('input', () => {
    kept.filter = input.value;
    apply();
  });

  const onClick = (event) => {
    const button = event.target.closest('[data-order]');
    if (button) {
      kept.lbrOrder = button.dataset.order === 'number' ? 'number' : 'name';
      for (const sec of sections) reorder(sec);
      apply();
      return;
    }
    // Remember which sections the reader opened (not those a filter opened).
    const summary = event.target.closest('summary.section__summary');
    if (summary && !needleOf(kept.filter)) {
      const details = summary.parentElement;
      if (details.open) kept.open.delete(details.id);
      else kept.open.add(details.id);
    }
  };
  root.addEventListener('click', onClick);
  window.addEventListener('hashchange', followHash);

  return () => {
    root.removeEventListener('click', onClick);
    window.removeEventListener('hashchange', followHash);
  };
}
