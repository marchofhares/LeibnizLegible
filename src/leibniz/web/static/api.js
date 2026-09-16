// api.js — thin wrappers over the JSON API served by the FastAPI app.
//
// The contract (fixed, implemented by src/leibniz/web/api.py):
//   GET /api/search?q&set&lang&stratum&min_conf&work&page&limit
//   GET /api/works/{work_id}
//   GET /api/pages/{page_id}
//   GET /api/stats
//   GET /manifests/{work_id}     (linked to, never fetched here)
// 404s answer `{"detail": "..."}` with status 404.
//
// Nothing else is fetched from our own origin. The only other network traffic
// the app causes is image loading straight from the GWLB.

import { pathSeg } from './dom.js';

const API = '/api';

/** An HTTP or transport failure, carrying the status (0 = no response). */
export class ApiError extends Error {
  constructor(status, detail, url) {
    super(detail || `HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail || '';
    this.url = url;
  }

  get notFound() {
    return this.status === 404;
  }
}

async function getJSON(url, signal) {
  let response;
  try {
    response = await fetch(url, {
      signal,
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    });
  } catch (err) {
    if (err && err.name === 'AbortError') throw err;
    throw new ApiError(0, '', url);
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    const detail = body && typeof body.detail === 'string' ? body.detail : '';
    throw new ApiError(response.status, detail, url);
  }
  if (body === null) throw new ApiError(response.status, '', url);
  return body;
}

/** The query parameters `/api/search` accepts, in a stable order. */
export const SEARCH_PARAMS = ['q', 'set', 'lang', 'stratum', 'min_conf', 'work', 'page', 'limit'];

/**
 * Build a query string from a params object, dropping empty values.
 * `page=1` and `min_conf=0` are dropped too: they are the defaults, and a
 * clean URL is easier to share.
 */
export function searchQuery(params) {
  const qs = new URLSearchParams();
  for (const key of SEARCH_PARAMS) {
    const value = params[key];
    if (value === undefined || value === null || value === '') continue;
    if (key === 'page' && Number(value) <= 1) continue;
    if (key === 'min_conf' && Number(value) <= 0) continue;
    qs.set(key, String(value));
  }
  return qs.toString();
}

/** GET /api/search */
export function search(params, signal) {
  const qs = searchQuery(params);
  return getJSON(`${API}/search${qs ? `?${qs}` : ''}`, signal);
}

/** GET /api/works/{work_id} */
export function work(workId, signal) {
  return getJSON(`${API}/works/${pathSeg(workId)}`, signal);
}

/** GET /api/pages/{page_id} */
export function page(pageId, signal) {
  return getJSON(`${API}/pages/${pathSeg(pageId)}`, signal);
}

/** GET /api/stats */
export function stats(signal) {
  return getJSON(`${API}/stats`, signal);
}

/** The URL of our IIIF Presentation 3 manifest for a work (for linking). */
export function manifestUrl(workId) {
  return `/manifests/${pathSeg(workId)}`;
}

/** The GWLB's own record page for a work. */
export function gwlbRecordUrl(workId) {
  return `https://digitale-sammlungen.gwlb.de/resolve?id=${encodeURIComponent(workId)}`;
}

export const REPO_URL = 'https://github.com/marchofhares/leibnizlegible';

/**
 * A prefilled "report an error" issue for one page: the repository's issue
 * form (`.github/ISSUE_TEMPLATE/transcription-error.yml`) with the page id and
 * the page's URL already filled in. GitHub prefills form fields from query
 * parameters named after the field ids.
 */
export function reportUrl(pageId) {
  const params = new URLSearchParams({
    template: 'transcription-error.yml',
    title: `Transcription error on page ${pageId}`,
    page_id: pageId,
    page_url: `${window.location.origin}/page/${pathSeg(pageId)}`,
  });
  return `${REPO_URL}/issues/new?${params.toString()}`;
}
