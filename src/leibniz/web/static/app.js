// app.js — bootstrap, i18n application to the static chrome, and the router.
//
// The FastAPI app serves this file's index.html for five paths:
//   /                 search
//   /search           search (with ?q=&set=&lang=&stratum=&min_conf=&work=&page=)
//   /work/{work_id}   one work
//   /page/{page_id}   one page
//   /about            about
// The router reads location.pathname + location.search and renders the right
// view; internal navigation is history.pushState with those same real URLs, so
// every deep link survives a reload.

import { initLang, setLang, getLang, onLangChange, t, languages } from './i18n.js';
import { conf } from './dom.js';
import { renderNotFound } from './views/common.js';
import * as searchView from './views/search.js';
import * as workView from './views/work.js';
import * as pageView from './views/page.js';
import * as aboutView from './views/about.js';

const VIEWS = {
  search: searchView,
  work: workView,
  page: pageView,
  about: aboutView,
};

let viewRoot = null;
let searchPanel = null;
let currentCleanup = null;
let currentController = null;
let currentRoute = null;

// ---------------------------------------------------------------------------
// i18n applied to static markup
// ---------------------------------------------------------------------------

const ATTR_KEYS = [
  ['data-i18n-label', 'aria-label'],
  ['data-i18n-placeholder', 'placeholder'],
  ['data-i18n-title', 'title'],
];

/** Apply the string table to every [data-i18n*] node under `root`. */
export function applyI18n(root) {
  if (!root) return;
  const scope = root.querySelectorAll ? root : document;
  for (const node of scope.querySelectorAll('[data-i18n]')) {
    node.textContent = t(node.getAttribute('data-i18n'));
  }
  for (const [dataAttr, target] of ATTR_KEYS) {
    for (const node of scope.querySelectorAll(`[${dataAttr}]`)) {
      node.setAttribute(target, t(node.getAttribute(dataAttr)));
    }
  }
}

function syncLangButtons() {
  const lang = getLang();
  for (const button of document.querySelectorAll('.lang-switch [data-lang]')) {
    button.setAttribute('aria-pressed', String(button.getAttribute('data-lang') === lang));
  }
}

function syncNav() {
  const name = currentRoute ? currentRoute.name : null;
  for (const link of document.querySelectorAll('.site-nav [data-nav]')) {
    const active = link.getAttribute('data-nav') === name;
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
}

// ---------------------------------------------------------------------------
// routing
// ---------------------------------------------------------------------------

/** Map a pathname to a route descriptor. */
export function parseRoute(pathname) {
  const path = pathname.replace(/\/{2,}/g, '/').replace(/(.)\/+$/, '$1');
  if (path === '/' || path === '/search') return { name: 'search' };
  if (path === '/about') return { name: 'about' };
  let m = /^\/work\/(.+)$/.exec(path);
  if (m) return { name: 'work', id: safeDecode(m[1]) };
  m = /^\/page\/(.+)$/.exec(path);
  if (m) return { name: 'page', id: safeDecode(m[1]) };
  return { name: 'notfound', path };
}

function safeDecode(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/** Is this same-origin path one the single-page app owns? */
function isAppPath(pathname) {
  return parseRoute(pathname).name !== 'notfound';
}

/** Navigate to an in-app URL, pushing (or replacing) a history entry. */
export function navigate(url, opts) {
  const { replace = false } = opts || {};
  const target = new URL(url, location.href);
  const same = target.pathname === location.pathname && target.search === location.search;
  if (!same) {
    const to = target.pathname + target.search + target.hash;
    if (replace) history.replaceState({}, '', to);
    else history.pushState({}, '', to);
  }
  render({ focusHeading: true });
}

async function render(opts) {
  const { focusHeading = false } = opts || {};

  if (currentCleanup) {
    try {
      currentCleanup();
    } catch {
      /* a view's teardown must never block the next one */
    }
    currentCleanup = null;
  }
  if (currentController) currentController.abort();
  currentController = new AbortController();
  const { signal } = currentController;

  const route = parseRoute(location.pathname);
  currentRoute = route;
  syncNav();

  if (route.name === 'notfound') {
    detachSearchPanel();
    renderNotFound(viewRoot, t('error.badRoute', { path: route.path }));
    afterRender(focusHeading);
    return;
  }

  const view = VIEWS[route.name];
  const ctx = {
    root: viewRoot,
    route,
    query: new URLSearchParams(location.search),
    signal,
    navigate,
    searchPanel,
    applyI18n,
  };
  try {
    const cleanup = await view.render(ctx);
    if (signal.aborted) {
      if (typeof cleanup === 'function') cleanup();
      return;
    }
    if (typeof cleanup === 'function') currentCleanup = cleanup;
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    // A view is expected to render its own error states; reaching here means a
    // programming fault. Say so plainly rather than leaving a blank page.
    console.error('view failed', err);
    viewRoot.innerHTML =
      `<div class="panel state state--error" role="alert">` +
      `<h1 tabindex="-1" data-view-heading>${t('error.h')}</h1>` +
      `<p>${t('error.network')}</p></div>`;
  }
  afterRender(focusHeading);
}

function afterRender(focusHeading) {
  if (!focusHeading) return;
  const heading = viewRoot.querySelector('[data-view-heading]');
  if (heading) {
    heading.focus({ preventScroll: true });
  }
  window.scrollTo(0, 0);
}

/** Take the statically delivered search form out of the document. */
function detachSearchPanel() {
  if (searchPanel && searchPanel.parentNode) searchPanel.remove();
}

// ---------------------------------------------------------------------------
// global listeners
// ---------------------------------------------------------------------------

function onClick(event) {
  if (event.defaultPrevented || event.button !== 0) return;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const anchor = event.target.closest ? event.target.closest('a[href]') : null;
  if (!anchor) return;
  if (anchor.hasAttribute('download')) return;
  const target = anchor.getAttribute('target');
  if (target && target !== '_self') return;
  const url = new URL(anchor.href, location.href);
  if (url.origin !== location.origin) return;
  if (url.pathname === location.pathname && url.hash && !url.search) return; // in-page anchor
  if (!isAppPath(url.pathname)) return; // /api/…, /manifests/…, /static/… leave the app
  event.preventDefault();
  navigate(url.pathname + url.search);
}

function onLangButton(event) {
  const button = event.target.closest ? event.target.closest('.lang-switch [data-lang]') : null;
  if (!button) return;
  const lang = button.getAttribute('data-lang');
  if (!languages().includes(lang)) return;
  setLang(lang);
}

function wireSearchForm() {
  if (!searchPanel) return;
  const form = searchPanel.querySelector('#search-form');
  const range = searchPanel.querySelector('#min_conf');
  const output = searchPanel.querySelector('#min_conf_out');

  if (range && output) {
    const sync = () => {
      output.value = conf(Number(range.value));
    };
    range.addEventListener('input', sync);
    sync();
  }

  if (form) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const params = new URLSearchParams();
      for (const [key, value] of new FormData(form).entries()) {
        const text = String(value).trim();
        if (!text) continue;
        if (key === 'min_conf' && Number(text) <= 0) continue;
        params.set(key, text);
      }
      // A new query always starts on the first page of results.
      params.delete('page');
      const qs = params.toString();
      navigate(`/search${qs ? `?${qs}` : ''}`);
    });
  }
}

// ---------------------------------------------------------------------------
// boot
// ---------------------------------------------------------------------------

function boot() {
  // Where page images come from is stamped into the shell by the server
  // (<html data-image-origin>): the footer's attribution line must say so.
  if (document.documentElement.dataset.imageOrigin === 'mirror') {
    for (const node of document.querySelectorAll('[data-i18n="attr.images"]')) {
      node.setAttribute('data-i18n', 'attr.images.mirror');
    }
  }
  viewRoot = document.getElementById('view');
  searchPanel = document.getElementById('search-panel');
  detachSearchPanel();

  initLang();
  applyI18n(document);
  applyI18n(searchPanel);
  syncLangButtons();
  wireSearchForm();

  document.addEventListener('click', onClick);
  document.addEventListener('click', onLangButton);
  window.addEventListener('popstate', () => render({ focusHeading: true }));

  onLangChange(() => {
    applyI18n(document);
    applyI18n(searchPanel);
    syncLangButtons();
    render({ focusHeading: false });
  });

  render({ focusHeading: false });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
