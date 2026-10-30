// K4 Task 5: the browser checks on the fixture store — About (the registry's licence
// sentences with the stamps filled in, the models and pages-by-language rows), the search
// form's language filter (open, five values, the hint; the writing-stage filter hidden), a
// German page's provenance naming the model per line — in EN and DE, at 1280 and 390 px,
// no console or page errors, axe-core on every view.
//
// Seed the store with tools/browser-checks/k4-seed.py, serve it with `leibniz serve --db … --backend
// none --rate-limit 0`, then from a scratch directory holding `npm install playwright axe-core`
// (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 for a preinstalled Chromium, its path as the last argument):
//   node k4-checks.mjs <base url> <german page id> <screenshot dir> [chrome executable]
import { chromium } from 'playwright';
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const AXE = require.resolve('axe-core/axe.min.js');
const [BASE, PAGE_ID, OUT, EXE] = process.argv.slice(2);
if (!BASE || !PAGE_ID || !OUT) {
  console.error('usage: node checks.mjs <base url> <german page id> <screenshot dir> [chrome]');
  process.exit(2);
}
mkdirSync(OUT, { recursive: true });

// one white pixel, for the GWLB's images
const JPEG = Buffer.from(
  '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==',
  'base64',
);

const STRINGS = {
  en: {
    models: 'Recognition models (lines shown)',
    model: 'Recognition model',
    langs: 'Pages by language',
    german: 'German',
    langField: 'Language (detected)',
    provModel: 'Model',
  },
  de: {
    models: 'Erkennungsmodelle (gezeigte Zeilen)',
    model: 'Erkennungsmodell',
    langs: 'Seiten nach Sprache',
    german: 'Deutsch',
    langField: 'Sprache (erkannt)',
    provModel: 'Modell',
  },
};

const results = [];
let failures = 0;
function check(name, ok, detail = '') {
  results.push({ name, ok, detail });
  if (!ok) failures++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${detail ? ' — ' + detail : ''}`);
}

async function stubbed(context) {
  await context.route(/digitale-sammlungen\.gwlb\.de/, (route) => {
    const url = route.request().url();
    if (url.endsWith('info.json')) {
      const id = url.slice(0, -'/info.json'.length);
      return route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          '@context': 'http://iiif.io/api/image/2/context.json',
          '@id': id,
          protocol: 'http://iiif.io/api/image',
          width: 2000,
          height: 2500,
          profile: ['http://iiif.io/api/image/2/level0.json'],
          sizes: [{ width: 250, height: 313 }, { width: 500, height: 625 }, { width: 1000, height: 1250 }, { width: 2000, height: 2500 }],
          tiles: [{ width: 512, scaleFactors: [1, 2, 4, 8] }],
        }),
      });
    }
    return route.fulfill({ contentType: 'image/jpeg', body: JPEG });
  });
  // axe-core from the app's own origin: the CSP is script-src 'self'
  await context.route('**/axe.min.js', (route) =>
    route.fulfill({ path: AXE, contentType: 'application/javascript' }),
  );
}

async function open(page, path, lang, errors) {
  errors.length = 0;
  await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle' });
  const btn = page.locator(`.lang-switch button[data-lang="${lang}"]`);
  if ((await btn.getAttribute('aria-pressed')) !== 'true') {
    await btn.click();
    await page.waitForFunction((l) => document.documentElement.lang === l, lang);
    await page.waitForLoadState('networkidle');
  }
}

async function axe(page, label) {
  await page.addScriptTag({ url: `${BASE}/axe.min.js` });
  const r = await page.evaluate(() => window.axe.run(document, { resultTypes: ['violations'] }));
  const v = r.violations.map((x) => `${x.id} (${x.nodes.length})`).join(', ');
  check(`axe ${label}`, r.violations.length === 0, v || '0 violations');
}

async function noScroll(page, label) {
  const [sw, iw] = await page.evaluate(() => [
    document.documentElement.scrollWidth,
    window.innerWidth,
  ]);
  check(`no horizontal scroll ${label}`, sw <= iw, `${sw} <= ${iw}`);
}

const browser = await chromium.launch(EXE ? { executablePath: EXE } : {});
try {
  for (const lang of ['en', 'de']) {
    const S = STRINGS[lang];
    for (const width of [1280, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      await stubbed(context);
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
      page.on('console', (m) => {
        if (m.type() === 'error') errors.push(`console: ${m.text()}`);
      });
      page.on('requestfailed', (r) => errors.push(`failed: ${r.url()}`));
      const tag = `${lang} ${width}px`;

      // About
      await open(page, '/about', lang, errors);
      await page.waitForFunction(
        (needle) => document.body.textContent.includes(needle),
        S.langs,
        { timeout: 20000 },
      );
      const about = await page.evaluate(() => document.body.textContent);
      check(`about ${tag}: the models row`, about.includes(S.models) || about.includes(S.model));
      check(`about ${tag}: pages by language with German`, about.includes(S.langs) && about.includes(S.german));
      check(`about ${tag}: READER named from the stamps`, about.includes('k3-trocr'));
      check(`about ${tag}: the base's licence from the stamps`, about.includes('MIT'));
      check(
        `about ${tag}: no placeholder left`,
        !/\{(readerDe|deBase|deModel|deReadings|v1Model|v1Readings|v1ModelObtained)\}/.test(about) &&
          !about.includes('—\n—'),
      );
      check(`about ${tag}: no errors`, errors.length === 0, errors.join(' | '));
      await noScroll(page, `about ${tag}`);
      await page.screenshot({ path: join(OUT, `about-${lang}-${width}.png`), fullPage: true });
      await axe(page, `about ${tag}`);

      // Search
      await open(page, '/search', lang, errors);
      const langSel = page.locator('#lang');
      check(`search ${tag}: the language filter is visible`, await langSel.isVisible());
      const options = await langSel.locator('option').evaluateAll((os) => os.map((o) => o.value));
      check(
        `search ${tag}: its values`,
        JSON.stringify(options) === JSON.stringify(['', 'la', 'fr', 'de', 'mixed', 'unknown']),
        options.join(','),
      );
      const label = (await page.locator('label[for="lang"]').textContent()).trim();
      check(`search ${tag}: its label`, label === S.langField, label);
      const hint = (await page.locator('#lang-help').textContent()).trim();
      check(`search ${tag}: the hint names the pass's numbers`, hint.includes('95') && hint.includes('75'), hint);
      const described = await langSel.getAttribute('aria-describedby');
      check(`search ${tag}: the hint is the field's description`, described === 'lang-help');
      check(`search ${tag}: the writing-stage filter is hidden`, !(await page.locator('#stratum').isVisible()));
      check(`search ${tag}: no errors`, errors.length === 0, errors.join(' | '));
      await noScroll(page, `search ${tag}`);
      await page.screenshot({ path: join(OUT, `search-${lang}-${width}.png`), fullPage: true });
      await axe(page, `search ${tag}`);

      // The German page: the provenance line names the model per line
      await open(page, `/page/${PAGE_ID}`, lang, errors);
      await page.waitForFunction(
        () => document.body.textContent.includes('k3-trocr@runs-615-epoch-5'),
        null,
        { timeout: 20000 },
      );
      const body = await page.evaluate(() => document.body.textContent);
      check(`page ${tag}: READER's run named on its line`, body.includes('k3-trocr@runs-615-epoch-5'));
      check(`page ${tag}: v1 named on the other lines`, body.includes('FoNDUE-GD_v2_ft_Leibniz@v1'));
      const provModel = await page.locator('details.prov').first().textContent();
      check(`page ${tag}: the provenance row is labelled`, provModel.includes(S.provModel), provModel.slice(0, 80));
      check(`page ${tag}: no errors`, errors.length === 0, errors.join(' | '));
      await noScroll(page, `page ${tag}`);
      await page.screenshot({ path: join(OUT, `page-${lang}-${width}.png`), fullPage: true });
      await axe(page, `page ${tag}`);

      await context.close();
    }
  }
} finally {
  await browser.close();
}
writeFileSync(join(OUT, 'results.json'), JSON.stringify(results, null, 1));
console.log(`CHECKS ${results.length - failures} passed, ${failures} failed`);
process.exit(failures ? 1 : 0);
