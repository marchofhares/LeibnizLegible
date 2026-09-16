// dom.js — the small set of helpers every view uses.
//
// The one rule this module exists to enforce: **all API text is escaped before
// it reaches the DOM**. Views build HTML strings with `esc(...)` around every
// interpolated value. The single exception is the search `snippet`, which the
// API generates with `<mark>` tags; `snippet()` below re-parses it and keeps
// the text and the `<mark>` elements only, so nothing else can ever reach the
// live document.

import { t, locale } from './i18n.js';

const ESCAPES = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/** Escape a value for interpolation into HTML text or a quoted attribute. */
export function esc(value) {
  if (value === null || value === undefined) return '';
  return String(value).replace(/[&<>"']/g, (c) => ESCAPES[c]);
}

/**
 * Render a server-generated search snippet.
 *
 * The API documents the snippet as trusted HTML containing `<mark>` only. We
 * parse it into an inert `<template>` — which neither runs scripts nor loads
 * anything — and rebuild it keeping the text and the `<mark>` elements and
 * nothing else. Entities decode correctly, the highlight survives, and no
 * other element or attribute can ever reach the live document.
 */
export function snippet(value) {
  if (value === null || value === undefined) return '';
  const template = document.createElement('template');
  template.innerHTML = String(value);
  let out = '';
  const walk = (node) => {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        out += esc(child.nodeValue);
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const isMark = child.tagName === 'MARK';
        if (isMark) out += '<mark>';
        walk(child);
        if (isMark) out += '</mark>';
      }
    }
  };
  walk(template.content);
  return out;
}

/**
 * Encode one path segment for a URL.
 *
 * Page ids look like `00068642:0007`. A colon is a legal path character
 * (RFC 3986 `pchar`), so we keep it readable rather than percent-encoding it —
 * `/page/00068642:0007` is what the user sees and what we send to the API.
 */
export function pathSeg(value) {
  return encodeURIComponent(String(value)).replace(/%3A/gi, ':');
}

/** A number formatted for the active locale. */
export function num(n) {
  if (typeof n !== 'number' || !Number.isFinite(n)) return '—';
  return new Intl.NumberFormat(locale()).format(n);
}

/** A confidence value as two decimals, in the active locale. */
export function conf(c) {
  if (typeof c !== 'number' || !Number.isFinite(c)) return '—';
  return new Intl.NumberFormat(locale(), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(c);
}

/** A percentage with one decimal. */
export function pct(fraction) {
  if (typeof fraction !== 'number' || !Number.isFinite(fraction)) return '—';
  return new Intl.NumberFormat(locale(), {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(fraction);
}

/** An ISO timestamp rendered for the active locale; the raw string on failure. */
export function datetime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return new Intl.DateTimeFormat(locale(), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(d);
}

/**
 * The confidence band, 1 (worst) … 5 (best).
 *
 *   5: >= 0.9   4: 0.8–0.9   3: 0.7–0.8   2: 0.5–0.7   1: < 0.5
 */
export function confBand(c) {
  if (typeof c !== 'number' || !Number.isFinite(c)) return 0;
  if (c >= 0.9) return 5;
  if (c >= 0.8) return 4;
  if (c >= 0.7) return 3;
  if (c >= 0.5) return 2;
  return 1;
}

/**
 * A chip: a shaded pill whose visible text is short and whose spoken text is
 * the full label. A bare `<span>` may not take `aria-label`, so the label is
 * carried by a visually hidden child instead.
 */
export function chip(classes, visible, label) {
  return (
    `<span class="chip ${classes}">` +
    `<span aria-hidden="true">${esc(visible)}</span>` +
    `<span class="sr-only">${esc(label)}</span></span>`
  );
}

/** A confidence chip: shaded by band, spoken as "confidence 0.87". */
export function confChip(c) {
  const band = confBand(c);
  if (!band) {
    return `<span class="chip chip--conf chip--conf-0">${esc(t('page.confUnknown'))}</span>`;
  }
  return chip(`chip--conf chip--conf-${band}`, conf(c), t('page.conf', { c: conf(c) }));
}

const LINE_STATUSES = ['machine', 'aligned', 'corrected', 'verified'];

/** A line-status badge with its short explanation as a tooltip and for AT. */
export function statusBadge(status) {
  const known = LINE_STATUSES.includes(status);
  const key = known ? status : 'machine';
  const label = known ? t(`status.${key}`) : String(status || '—');
  const help = known ? t(`status.${key}.help`) : '';
  return (
    `<span class="badge badge--${esc(key)}" title="${esc(help)}">` +
    `${esc(label)}<span class="sr-only">. ${esc(help)}</span></span>`
  );
}

/** A human label for a language tag (la/fr/de/mixed/unknown). */
export function langLabel(code) {
  if (!code) return '';
  const key = code === 'de' ? 'lang.de.text' : `lang.${code}`;
  const label = t(key);
  return label === key ? code : label;
}

/** A human label for a stratum enum value. */
export function stratumLabel(code) {
  if (!code) return '';
  const label = t(`stratum.${code}`);
  return label === `stratum.${code}` ? code : label;
}

/** A human label for an OAI set name; the raw name if we do not know it. */
export function setLabel(name) {
  if (!name) return '';
  const label = t(`set.${name}`);
  return label === `set.${name}` ? name : label;
}

/** A folio label if the page has one, otherwise "Canvas {seq}". */
export function folioLabel(label, seq) {
  return label ? t('work.folio', { label }) : t('work.canvas', { seq });
}

/** Render an Akademie-Ausgabe reference as "AA I,3 N. 123". */
const ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
export function aaRef(ref) {
  if (!ref) return '';
  const series = ROMAN[Number(ref.series)] || String(ref.series ?? '');
  const vol = ref.volume === null || ref.volume === undefined ? '' : String(ref.volume);
  const head = vol ? `AA ${series},${vol}` : `AA ${series}`;
  const piece = ref.piece === null || ref.piece === undefined ? '' : String(ref.piece);
  return piece ? `${head} N. ${piece}` : head;
}
