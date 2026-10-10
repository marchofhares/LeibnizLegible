// api.js — thin wrappers over the JSON API served by the FastAPI app.
//
// The contract (fixed, implemented by src/leibniz/web/api.py):
//   GET /api/search?q&set&lang&stratum&min_conf&work&page&limit&match
//   GET /api/works               (every work as a row + the browse tree)
//   GET /api/works/{work_id}
//   GET /api/pages/{page_id}
//   GET /api/stats
//   GET /manifests/{work_id}     (linked to, never fetched here)
//   GET /api/pages/{page_id}/text, GET /api/works/{work_id}/text,
//   GET /api/records/{record_id}/text
//                                (plain-text downloads; linked to, never fetched;
//                                 a work's katalog entries carry `text_url` where
//                                 the piece can be placed on the scan)
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
export const SEARCH_PARAMS = [
  'q',
  'set',
  'lang',
  'stratum',
  'min_conf',
  'work',
  'page',
  'limit',
  'match',
];

/**
 * Build a query string from a params object, dropping empty values.
 * `page=1`, `min_conf=0` and `match=all` are dropped too: they are the
 * defaults, and a clean URL is easier to share.
 */
export function searchQuery(params) {
  const qs = new URLSearchParams();
  for (const key of SEARCH_PARAMS) {
    const value = params[key];
    if (value === undefined || value === null || value === '') continue;
    if (key === 'page' && Number(value) <= 1) continue;
    if (key === 'min_conf' && Number(value) <= 0) continue;
    if (key === 'match' && value !== 'any') continue;
    qs.set(key, String(value));
  }
  return qs.toString();
}

/** GET /api/search */
export function search(params, signal) {
  const qs = searchQuery(params);
  return getJSON(`${API}/search${qs ? `?${qs}` : ''}`, signal);
}

/** GET /api/lookup — where a citation points (a shelfmark and folio, an AA number). */
export function lookup(q, signal) {
  return getJSON(`${API}/lookup?q=${encodeURIComponent(q)}`, signal);
}

/** GET /api/letters — Bodemann's letters by correspondent, date and place. */
export function letters(params, signal) {
  const qs = new URLSearchParams();
  for (const key of ['who', 'place', 'from', 'to', 'direction', 'work', 'page', 'limit']) {
    const value = params[key];
    if (value !== undefined && value !== null && value !== '' && !(key === 'page' && Number(value) <= 1)) {
      qs.set(key, String(value));
    }
  }
  const tail = qs.toString();
  return getJSON(`${API}/letters${tail ? `?${tail}` : ''}`, signal);
}

/** GET /api/contents — the convolutes whose catalogue pieces carry the words. */
export function contents(q, signal) {
  return getJSON(`${API}/contents?q=${encodeURIComponent(q)}`, signal);
}

/** GET /api/works — every work as a compact row, and the browse tree. */
export function works(signal) {
  return getJSON(`${API}/works`, signal);
}

/** GET /api/works/{work_id} */
export function work(workId, signal) {
  return getJSON(`${API}/works/${pathSeg(workId)}`, signal);
}

/** GET /api/pages/{page_id} */
export function page(pageId, signal, run) {
  const pinned = run !== undefined && run !== null && run !== '' ? `?run=${encodeURIComponent(run)}` : '';
  return getJSON(`${API}/pages/${pathSeg(pageId)}${pinned}`, signal);
}

/** GET /api/stats */
export function stats(signal) {
  return getJSON(`${API}/stats`, signal);
}

/** The URL of our IIIF Presentation 3 manifest for a work (for linking). */
export function manifestUrl(workId) {
  return `/manifests/${pathSeg(workId)}`;
}

/** One page's transcription as a plain-text download, provenance in its header. */
export function pageTextUrl(pageId, run) {
  const pinned = run !== undefined && run !== null && run !== '' ? `?run=${encodeURIComponent(run)}` : '';
  return `${API}/pages/${pathSeg(pageId)}/text${pinned}`;
}

/** A whole work's transcription as one plain-text download, folio by folio. */
export function workTextUrl(workId) {
  return `${API}/works/${pathSeg(workId)}/text`;
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
