// i18n.js — the whole UI string table, EN + DE.
//
// Every user-facing string lives here. `t(key, vars)` looks the key up in the
// active language, falls back to English, and finally to the key itself (so a
// missing string is visible, never silent). `{placeholders}` are substituted
// from `vars`.
//
// To add a string: add the key to BOTH `en` and `de` below, in the same
// section, and use `t('your.key')` in a view. Never inline English prose in a
// view module.

const LANGS = ['en', 'de'];
const STORAGE_KEY = 'leibniz-legible.lang';

const STRINGS = {
  en: {
    // ---- chrome ---------------------------------------------------------
    'site.name': 'Leibniz Legible',
    'site.tagline': 'Machine transcription of the Leibniz Nachlass',
    'site.skip': 'Skip to main content',
    'nav.label': 'Main',
    'nav.search': 'Search',
    'nav.browse': 'Browse',
    'nav.about': 'About',
    'crumbs.label': 'Breadcrumb',
    'lang.label': 'Language',
    // Spoken names of the EN / DE buttons; each begins with what the button
    // shows, so that the name contains the visible label (WCAG 2.5.3).
    'lang.en': 'EN: English',
    'lang.de': 'DE: German',
    'footer.label': 'Attribution and licensing',
    'footer.repo': 'Source code and issue tracker',

    // ---- attribution (shown on every view) ------------------------------
    'attr.images':
      'Images: Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. Loaded directly from the GWLB; never rehosted.',
    'attr.images.mirror':
      'Images: Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. Served from this project’s copy of the GWLB’s delivery scans; the originals remain with the GWLB.',
    'attr.katalog':
      'Catalogue: Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA. CC BY 4.0.',
    'attr.transcriptions':
      'Transcriptions: Leibniz Legible, CC BY 4.0 — machine output, not an edition.',
    'attr.code': 'Code: Apache-2.0.',

    // ---- the honesty banner ---------------------------------------------
    'honesty.banner':
      'Machine transcription. Not an edition. Errors are expected (character error rate about 8% on Latin and French; German is unmeasured and worse).',

    // ---- search ----------------------------------------------------------
    'search.heading': 'Search the Nachlass',
    'search.label': 'Search the Nachlass',
    'search.hint':
      'The index is typo-tolerant, and a page must hold every word you type (or any of them, if you tick the box below). Search is over machine transcriptions only. Use "quotes" for an exact phrase and -word to leave a word out; both match exactly, so they miss words the machine misread. A shelfmark with its folio (LH IV, 6, 18 Bl. 1r) or an Akademie-Ausgabe number (A VI, 4 N. 109) also takes you to the place itself.',
    'search.placeholder': 'e.g. calculemus',
    'search.submit': 'Search',
    'search.filters': 'Filters',
    'search.set': 'Collection',
    'search.set.any': 'All collections',
    'search.lang': 'Language of the text',
    'search.lang.any': 'Any language',
    'search.stratum': 'Writing stage',
    'search.stratum.any': 'Any stage',
    'search.minconf': 'Minimum mean confidence',
    'search.results': 'Results',
    'search.summary': '{total} page hits · {ms} ms',
    'search.summary.one': '{total} page hit · {ms} ms',
    'search.backend': 'index: {backend}',
    'search.query': 'for “{q}”',
    'search.loading': 'Searching…',
    'search.start':
      'Enter a word or a phrase to search the machine transcriptions of the Nachlass.',
    'search.empty': 'No page matched.',
    'search.empty.hint':
      'Try fewer filters, a shorter query, a different spelling, or no quotes. The index tolerates typos, but the text it searches is machine output and contains errors.',
    'search.error': 'The search service did not answer.',
    'search.prev': 'Previous',
    'search.next': 'Next',
    'search.pageOf': 'Page {page} of {pages}',
    'search.pagination': 'Result pages',
    'search.hit.lines': '{n} lines',
    'search.also': 'also registered as {labels}',
    'search.lookup.shelfmark': 'This shelfmark in the Nachlass',
    'search.lookup.aa': 'This Akademie-Ausgabe piece on its scan',
    'search.lookup.id': 'Go to',
    'search.lookup.text': 'Text of this piece',
    'search.lookup.more': '… and {n} more: open the browse index for the rest.',
    'search.lookup.none': 'Read as a citation: {reason}.',
    'search.hit.lines.one': '{n} line',
    'search.hit.meanconf': 'mean confidence {c}',
    'search.filteredToWork': 'Restricted to one work.',
    'search.clearWork': 'Search all works',
    'search.noWork': 'Untitled work',
    'search.browse': 'Or browse the Nachlass by shelfmark.',
    'search.match.any': 'Pages with any of the words',
    'search.capped':
      'Only the first {reachable} of the {total} hits can be paged through; narrow the search to reach the rest.',
    'search.pastEnd': 'No hits on this page.',

    // ---- browse ----------------------------------------------------------
    // Family and section names are the archive's own German words; they stay
    // as data in both languages (the API sends them).
    'browse.heading': 'Browse the Nachlass by shelfmark',
    'browse.intro':
      'Every digitized unit of the Nachlass, grouped as it is shelved: the manuscripts (LH) by section, the correspondence (LBr) by correspondent, the annotated books (Marginalien) by number. Each entry opens the work with its folios.',
    'browse.loading': 'Loading the index…',
    'browse.filter.label': 'Filter by shelfmark, name or title',
    'browse.filter.placeholder': 'e.g. LH 35, 3 or Oldenburg',
    'browse.filter.count': '{n} of {total} works match.',
    'browse.filter.count.one': '{n} of {total} works matches.',
    'browse.filter.none': 'No work matches this filter.',
    'browse.matching': '{n} of {total}',
    'browse.works': '{n} works',
    'browse.works.one': '{n} work',
    'browse.pageimages': '{n} page images',
    'browse.pageimages.one': '{n} page image',
    'browse.pages': '{n} pages',
    'browse.pages.one': '{n} page',
    'browse.family.LH': 'Handschriften (LH)',
    'browse.family.LBr': 'Briefwechsel (LBr)',
    'browse.family.Marg': 'Marginalien',
    'browse.family.Other': 'Other',
    'browse.about.LH':
      'Leibniz’s manuscripts, in the sections of the LH shelfmarks. The section names are cut from the library’s own titles.',
    'browse.about.LBr':
      'The correspondence, one convolute per correspondent. A name is shown where the linked records of the Arbeitskatalog name one that fits the alphabetical order of the LBr numbers; otherwise the entry shows its shelfmark only.',
    'browse.about.Marg': 'Printed books with Leibniz’s marginal notes, by number.',
    'browse.about.Other': 'Units outside the three shelfmark series, by collection.',
    'browse.all.LBr': 'All letter convolutes',
    'browse.all.Marg': 'All annotated books',
    'browse.sort.label': 'Order of the letter convolutes',
    'browse.sort.name': 'By name',
    'browse.sort.number': 'By number',
    'browse.unnamed': 'No correspondent established here yet; by number:',
    'browse.katalog': 'catalogue records linked',
    'browse.katalog.short': 'K',
    'browse.note':
      'Titles and shelfmarks are the library’s. Correspondent names come from the Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA, used under CC BY 4.0. K marks a work with linked catalogue records. The texts behind the links are machine transcriptions, not an edition.',

    // ---- work ------------------------------------------------------------
    'work.heading': 'Work',
    'work.set': 'Collection',
    'work.shelfmarks': 'Shelfmarks',
    'work.gwlb': 'GWLB record',
    'work.manifest': 'IIIF manifest (GWLB)',
    'work.ourManifest': 'IIIF manifest with our transcriptions',
    'work.download': 'Download the text of this work',
    'work.katalog': 'Catalogue records',
    'work.katalog.none': 'No catalogue record is linked to this work yet.',
    'work.katalog.incipit': 'Incipit',
    'work.katalog.date': 'Date',
    'work.katalog.sender': 'Sender',
    'work.katalog.addressee': 'Addressee',
    'work.katalog.aa': 'Akademie-Ausgabe',
    'work.katalog.aa.planned': 'Akademie-Ausgabe (assigned, not yet published)',
    'work.katalog.drucke': 'Other printings',
    // How a record came to be linked to this work: the crosswalk's methods in
    // words. A method with no words here falls back to the line after them,
    // which shows its name (visible, never silent).
    'work.katalog.match.gwlb_link':
      'The catalogue record itself links to this scan · confidence {conf}',
    'work.katalog.match.shelfmark': 'Linked by matching shelfmarks · confidence {conf}',
    'work.katalog.match.manual': 'Linked by hand · confidence {conf}',
    'work.katalog.match': 'Link: {method}, confidence {conf}',
    'work.katalog.record': 'Record in the Leibniz-Katalog',
    // The piece's machine text across its folios, offered where the record's
    // shelfmark names a folio range the scan's labels can place; {range} is the
    // catalogue's own "Bl. 1–2", the same in both languages.
    'work.katalog.text': 'Text of this piece ({range})',
    'work.katalog.attr':
      'Catalogue data from the Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA, used under CC BY 4.0.',
    'work.pages': 'Page images',
    'work.canvases': '{n} page images',
    'work.folio': 'Folio {label}',
    'work.canvas': 'Canvas {seq}',
    'work.status.recognized': 'recognised',
    'work.status.skipped': 'skipped',
    'work.lines': '{n} lines',
    'work.twin.spread': 'One image with {labels}: a spread, split at the fold',
    'work.twin.primary': 'Also registered as {labels}; its text is listed here',
    'work.twin.secondary': 'The same scan as {label}, where its text is listed',
    'work.search': 'Search this work',
    'work.search.go': 'Search',
    'work.lines.one': '{n} line',
    'work.noPages': 'No page images are recorded for this work.',
    'work.loading': 'Loading the work…',

    // ---- page ------------------------------------------------------------
    'page.heading': 'Folio {label}',
    'page.headingSeq': 'Canvas {seq}',
    'page.inWork': 'in {title}',
    'page.loading': 'Loading the page…',
    'page.nav': 'Page navigation within the work',
    'page.prev': 'Previous page',
    'page.next': 'Next page',
    'page.overlay.show': 'Show line overlay',
    'page.overlay.hide': 'Hide line overlay',
    'page.viewer.label': 'Page image, zoomable',
    'page.viewer.noIiif':
      'This page is served as a single image; deep zoom is not available for it.',
    'page.skipped': 'This page was not transcribed.',
    'page.skipReason': 'Reason: {reason}',
    'page.lines': 'Lines',
    'page.lines.count': '{n} lines · mean confidence {c}',
    'page.noLines': 'No lines were recognised on this page.',
    'page.linesHelp':
      'Select a line to highlight it on the image; arrow keys move between lines. Drag across the text to select it, or copy the whole page from the Text block below.',
    'page.line': 'Line {n}',
    'page.lineEmpty': '(empty line)',
    'page.mirador': 'Open in Mirador or another IIIF viewer',
    'page.gwlb': 'This page at the GWLB',
    'page.report': 'Report an error',
    // ---- the text block: the page's lines as one piece of selectable text
    'page.textLink': 'Text of this page',
    'page.text': 'Text',
    'page.text.help':
      'The recognised lines as one piece of text in reading order, to select and copy; status and confidence are in the line list above.',
    'page.text.copy': 'Copy the text',
    'page.text.copied': 'Copied: {n} lines.',
    'page.text.copied.one': 'Copied: {n} line.',
    'page.text.copyRefused':
      'The browser did not allow the clipboard. The text is selected: press Ctrl+C (⌘C on a Mac) to copy it.',
    'page.text.download': 'Download this page as text',
    'page.text.prov':
      'Machine transcription: {runs}. Quote it as “the machine reads it as …”, never as “Leibniz wrote”.',
    'page.text.run': '{model}, run of {date}',
    'page.text.noModel': 'model not recorded',
    'page.text.noDate': 'date not recorded',
    'page.provenance': 'Provenance',
    'page.prov.model': 'Model',
    'page.prov.run': 'Run',
    'page.prov.runDate': 'Run date',
    'page.prov.status': 'Status',
    'page.prov.source': 'Source',
    'page.prov.none': 'Machine output; no external source.',
    'page.prov.image': 'Image',
    'page.prov.lineId': 'Line id',
    'page.prov.iiif': 'IIIF image service',
    'page.conf': 'confidence {c}',
    'page.confUnknown': 'confidence not recorded',
    'page.langOf': 'language: {lang}',
    'page.crossesFold': 'across the fold',
    'page.cite': 'Cite',
    'page.cite.page': 'This page, as this reading has it. Select a line to cite it alone.',
    'page.cite.lineWhat': 'Line {n} of this page. Its address now ends in #L{n}: a link to it.',
    'page.cite.text': '{title}, {where}. Machine transcription, not an edition: Leibniz Legible{made}. {link}',
    'page.cite.folio': 'fol. {label}',
    'page.cite.canvas': 'canvas {seq}',
    'page.cite.line': '{where}, line {n}',
    'page.cite.model': 'model {model}',
    'page.cite.run': 'run {run}',
    'page.cite.lineId': 'line id {id}',
    'page.cite.copy': 'Copy citation',
    'page.cite.copied': 'Citation copied.',
    'page.run.older': 'You are reading this page as recognition run {run} left it; a later run ({now}) reads it again. {current}',
    'page.run.pinned': 'This address is pinned to recognition run {run}, the current reading: a later run will not change what it shows. {current}',
    'page.run.current': 'The current reading',
    'page.crossesFold.title': 'The machine read this line across the fold of the spread; it is shown on both halves.',
    'page.twin.spread': 'This image shows two folio pages side by side, and the library registered it under both labels ({others}). This page is its {side} half; lines that run across the fold are shown on both halves.',
    'page.twin.left': 'left',
    'page.twin.right': 'right',
    'page.twin.primary': 'The same scan is also registered as {others}. Search and the downloads give its text once, here.',
    'page.twin.secondary': 'The same scan as {primary}: search and the downloads give its text there. Below is this registration’s own reading.',
    'page.viewerError': 'The page image could not be loaded.',

    // ---- statuses --------------------------------------------------------
    'status.machine': 'machine',
    'status.machine.help': 'HTR output, unreviewed.',
    'status.aligned': 'aligned',
    'status.aligned.help': 'Matched to a printed edition.',
    'status.corrected': 'corrected',
    'status.corrected.help': 'A human or crowd correction.',
    'status.verified': 'verified',
    'status.verified.help': 'Checked by a named expert.',

    // ---- language tags ---------------------------------------------------
    'lang.la': 'Latin',
    'lang.fr': 'French',
    'lang.de.text': 'German',
    'lang.mixed': 'Mixed',
    'lang.unknown': 'Undetermined',

    // ---- strata ----------------------------------------------------------
    'stratum.fair_copy': 'Fair copy',
    'stratum.light_revision': 'Lightly revised',
    'stratum.heavy_revision': 'Heavily revised',
    'stratum.scrap': 'Scrap',
    'stratum.unknown': 'Undetermined',

    // ---- collections -----------------------------------------------------
    'set.LeibnizHandschriften': 'Leibniz-Handschriften (LH)',
    'set.LeibnizBriefwechsel': 'Leibniz-Briefwechsel (LBr)',
    'set.LeibnizMarginalien': 'Leibniz-Marginalien',
    'set.Leibnitiana': 'Leibnitiana',
    'set.leibniz-rekonstruktionen': 'Leibniz-Rekonstruktionen',

    // ---- about -----------------------------------------------------------
    'about.heading': 'About Leibniz Legible',
    'about.what.h': 'What this is',
    'about.what.p1':
      'Leibniz Legible is an access layer for the digitized Leibniz Nachlass held by the Gottfried Wilhelm Leibniz Bibliothek (GWLB) in Hannover. Every page image the library has published is run through handwritten-text recognition, and the result is made searchable and readable line by line, each line carrying its own confidence score and its full provenance.',
    'about.what.p2':
      'This is machine output with honest labels. It is Vorausedition-grade at best, and it is explicitly subordinate to the Akademie-Ausgabe, which remains the scholarly edition of Leibniz. Nothing here is an edition, and nothing here should be quoted as one. By its own count the Akademie-Ausgabe is about half way through the volumes it plans, and one of its editors estimates that three quarters of Leibniz’s papers have never been published anywhere (Herma Kliege-Biller, Leibniz-Forschungsstelle Münster, 2023); making all of it legible and findable is the whole of the ambition.',
    'about.what.p3':
      'The page images are never rehosted. They are loaded in your browser directly from the GWLB’s own servers.',
    'about.what.p3.mirror':
      'The page images are the GWLB’s own delivery scans, Public Domain Mark 1.0, served from a copy this project keeps so that the viewer neither depends on nor loads the library’s servers. Every page links to its original at the GWLB.',

    'about.numbers.h': 'The corpus in numbers',
    'about.numbers.loading': 'Loading the current figures…',
    'about.numbers.error': 'The figures could not be loaded.',
    'about.numbers.works': 'Works',
    'about.numbers.pages': 'Page images',
    'about.numbers.recognized': 'Pages recognised',
    'about.numbers.skipped': 'Pages skipped',
    'about.numbers.lines': 'Lines',
    'about.numbers.images': 'Distinct scans',
    'about.numbers.linesOnce': 'Lines, each scan once',
    'about.numbers.version': 'Software version',
    'about.numbers.caveat':
      'The page and line figures follow the library’s own page records. The GWLB photographs an unfolded sheet as one image, two folio pages side by side, and registers that image under both folio numbers, each with its own copy of the file; the recognition read every such image once per number. Where two registrations are confirmed to be one scan (the same size, nearly the same file, the lines in the same places), search and the downloads give its text once: a spread is split at the fold into its two folio pages, any other repeat is listed on one page. “Distinct scans” and “Lines, each scan once” count that way.',
    'about.numbers.caveatRaw':
      'The page and line figures follow the library’s own page records. The GWLB photographs an unfolded sheet as one image, two folio pages side by side, and registers that image under both folio numbers, so many images were read twice and the line total counts them twice. The next index build finds them and counts each scan once.',
    'about.numbers.backend': 'Search backend',
    'about.numbers.model': 'Recognition model',
    'about.hist.h': 'Distribution of line confidence',
    'about.hist.band': 'Confidence band',
    'about.hist.lines': 'Lines',
    'about.hist.share': 'Share',

    'about.error.h': 'How wrong is it?',
    'about.error.p1':
      'On the PHILIUMM validation split — 1,878 lines of Leibniz’s Latin and French — the model we run measures a character error rate of 7.95% (95% confidence interval 7.49–8.46) and a word error rate of 27.0%. That is roughly one wrong character in every thirteen, and roughly one word in four touched by some error.',
    'about.error.p2':
      'German in Kurrent script is not measured at all, because no ground truth for Leibniz’s German hand exists anywhere. It is certainly much worse, and it is about 15% of the corpus. Mathematical notation, diagrams and heavily revised drafts are likewise weak. Read every line here as a hypothesis about the manuscript, not as a reading of it.',
    'about.error.p3':
      'The model is PHILIUMM’s FoNDUE-GD_v2_ft_Leibniz (Kraken), doi:10.5281/zenodo.21457538, CC BY 4.0. Our reproduction of its published figures is in the project repository.',

    'about.legend.h': 'Line status legend',
    'about.legend.intro':
      'Every line carries one of four statuses. Nothing is published without one.',

    'about.report.h': 'Reporting an error',
    'about.report.p':
      'Every page view has a “Report an error” link that opens an issue in the project repository with the page identifier already filled in. Corrections to individual lines, notes on systematic failures, and reports of wrong catalogue links are all welcome. There is no account system and no comment box; the issue tracker is the channel.',

    'about.license.h': 'Licensing and attribution',
    'about.license.images.h': 'Page images',
    'about.license.images.p':
      'Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. The scans carry no related rights; they are loaded into your browser directly from the GWLB and are never copied onto our servers.',
    'about.license.images.p.mirror':
      'Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. The scans carry no related rights (§ 68 UrhG). The copies shown here are the GWLB’s delivery derivatives, unaltered except for the thumbnails, served from this project’s own storage; each page links to its original at the GWLB, whose master files remain the authoritative source.',
    'about.license.katalog.h': 'Catalogue data',
    'about.license.katalog.p':
      'Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, Berlin-Brandenburgische Akademie der Wissenschaften (BBAW) / TELOTA. CC BY 4.0. The catalogue is the metadata spine of the whole field; every link out to a record is a link to their work.',
    'about.license.transcriptions.h': 'Transcriptions',
    'about.license.transcriptions.p':
      'Leibniz Legible, CC BY 4.0. Machine output. Please do not ingest it as verified text, and please carry the provenance fields with it if you redistribute it. The text can be taken away as plain text, each file with its provenance in a header: per page (every page view has a Text block with a Copy button and a download), per work (from the work page), and per catalogue piece across its folios (from each record on the work page that can be placed on the scan).',
    'about.license.code.h': 'Code',
    'about.license.code.p': 'Apache-2.0, in the project repository.',

    'about.repo.h': 'The project',
    'about.repo.p': 'Source code, datasets, reports and the issue tracker:',
    'about.repo.reports':
      'Reports on Zenodo (CC BY 4.0): the project statement doi:10.5281/zenodo.22782813, the corpus census doi:10.5281/zenodo.22782815, the PHILIUMM reproduction and vision-model benchmark doi:10.5281/zenodo.22782817, and the retro-aligned ground truth doi:10.5281/zenodo.22782819.',

    'about.calculemus.h': 'Calculemus',
    'about.calculemus.p':
      'Calculemus is a game built on this corpus: players adjudicate two machine readings of a manuscript line, and their calibrated, aggregated judgments become crowd agreement over the machine text — corrected, never verified. Play it at',

    'about.who.h': 'Who made this',
    'about.who.p1':
      'Leibniz Legible is a one-person open project by Evan Tabak Atlas, an independent writer and researcher in New York (evanatlas.com, ORCID 0009-0007-7374-2338). It is not affiliated with the Gottfried Wilhelm Leibniz Bibliothek or with the Leibniz-Edition, and it claims nothing they have not claimed first.',
    'about.who.p2':
      'Corrections, questions from editors and offers of help are welcome through the issue tracker linked below.',

    'about.credits.h': 'Built on',
    'about.credits.images':
      'The scans of the Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover (Public Domain Mark 1.0), digitized 2016–2019.',
    'about.credits.katalog':
      'The Arbeitskatalog der Leibniz-Edition (“Ritter-Katalog”), Berlin-Brandenburgische Akademie der Wissenschaften, Leibniz-Edition Potsdam I / TELOTA, CC BY 4.0: more than 70,000 records that tie each scan to its date, title and edition citation.',
    'about.credits.model':
      'The Leibniz handwriting model of the ERC project PHILIUMM (Denisa-Florina Bumba, Laboratoire SPHERE, Université Paris Cité – CNRS, ERC grant 101020985; doi:10.5281/zenodo.21457538, CC BY 4.0), fine-tuned from FoNDUE-GD v2 (Simon Gabay, Geneva) and running on Kraken (Benjamin Kiessling). Leibniz Legible reproduced its published figures before building on it.',
    'about.credits.edition':
      'The reading text of Akademie-Ausgabe volumes whose 25-year edition term (§ 70 UrhG) has expired, used only to train and evaluate; editors’ introductions, apparatus and commentary never enter the pipeline.',
    'about.credits.precedents':
      'The example of Bullinger Digital (Zurich), GLOBALISE (Huygens Institute) and Transcribe Bentham (UCL), which put machine transcription over a whole archive before an edition could, and said so honestly.',

    'about.edition.h': 'Where the real work happens',
    'about.edition.p1':
      'The Akademie-Ausgabe, Gottfried Wilhelm Leibniz: Sämtliche Schriften und Briefe, has been edited since 1923 in Hannover (Leibniz-Archiv / Leibniz-Forschungsstelle at the GWLB), Münster (Leibniz-Forschungsstelle) and Potsdam (Leibniz-Edition Potsdam I and II) for the Berlin-Brandenburgische Akademie der Wissenschaften and the Akademie der Wissenschaften zu Göttingen, within the Akademienprogramm: 68 volumes by 2023, about half of the roughly 130 planned, with completion expected around 2055.',
    'about.edition.p2':
      'For the established text, dating and commentary go to leibnizedition.de, the Arbeitskatalog, and the Leibniz-Archiv’s transcriptions and advance editions; for English translations, Lloyd Strickland’s Leibniz Translations. Every catalogue record linked from a work page here is a link to their work.',

    'about.timeline.h': 'A short timeline',
    'about.timeline.1716': '1716 — Leibniz dies in Hannover; the court seals his papers.',
    'about.timeline.1889': '1889 / 1895 — Bodemann’s catalogues give the letters (LBr) and manuscripts (LH) the shelfmarks still used today.',
    'about.timeline.1901': '1901 — The academies plan the edition; Ritter’s catalogue begins.',
    'about.timeline.1923': '1923 — The first volume of the Akademie-Ausgabe appears.',
    'about.timeline.2007': '2007 — UNESCO inscribes the correspondence in the Memory of the World register.',
    'about.timeline.2016': '2016–2019 — The GWLB digitizes the whole Hannover Nachlass and publishes it under open licences.',
    'about.timeline.2026a': 'July 2026 — PHILIUMM releases its open Leibniz handwriting model and ground truth.',
    'about.timeline.2026b': '21 September 2026 — Leibniz Legible goes live.',
    'about.timeline.2055': 'about 2055 — Planned completion of the Akademie-Ausgabe.',

    'about.cite.h': 'How to cite',
    'about.cite.p':
      'Leibniz Legible (2026), machine transcription of the digitized Leibniz Nachlass, https://leibnizlegible.com, CC BY 4.0; project statement doi:10.5281/zenodo.22782813. Please quote lines as “the machine reads it as …”, with the page link and, ideally, the line id and its confidence.',
    'about.lang.p': 'This page is available in English and German.',

    // ---- errors ----------------------------------------------------------
    'error.h': 'Something went wrong',
    'error.retry': 'Try again',
    'error.network': 'The server could not be reached.',
    'error.http': 'The server answered with status {status}.',
    'error.notfound.h': 'Not found',
    'error.notfound.p': 'There is nothing at this address.',
    'error.notfound.back': 'Go to the search page',
    'error.badRoute': 'Unknown address: {path}',
  },

  de: {
    // ---- chrome ---------------------------------------------------------
    'site.name': 'Leibniz Legible',
    'site.tagline': 'Maschinelle Transkription des Leibniz-Nachlasses',
    'site.skip': 'Zum Hauptinhalt springen',
    'nav.label': 'Hauptnavigation',
    'nav.search': 'Suche',
    'nav.browse': 'Signaturen',
    'nav.about': 'Über das Projekt',
    'crumbs.label': 'Navigationspfad',
    'lang.label': 'Sprache',
    'lang.en': 'EN: Englisch',
    'lang.de': 'DE: Deutsch',
    'footer.label': 'Nachweis und Lizenzen',
    'footer.repo': 'Quellcode und Fehlermeldungen',

    // ---- attribution -----------------------------------------------------
    'attr.images':
      'Digitalisate: Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. Direkt von der GWLB geladen, niemals gespiegelt.',
    'attr.images.mirror':
      'Digitalisate: Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. Ausgeliefert aus der projekteigenen Kopie der GWLB-Auslieferungsscans; die Originale bleiben bei der GWLB.',
    'attr.katalog':
      'Katalogdaten: Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA. CC BY 4.0.',
    'attr.transcriptions':
      'Transkriptionen: Leibniz Legible, CC BY 4.0 — maschinell erzeugt, keine Edition.',
    'attr.code': 'Quellcode: Apache-2.0.',

    // ---- honesty banner --------------------------------------------------
    'honesty.banner':
      'Maschinelle Transkription. Keine Edition. Fehler sind zu erwarten (Zeichenfehlerrate rund 8 % bei Latein und Französisch; Deutsch ist nicht gemessen und schlechter).',

    // ---- search ----------------------------------------------------------
    'search.heading': 'Den Nachlass durchsuchen',
    'search.label': 'Den Nachlass durchsuchen',
    'search.hint':
      'Der Index ist tippfehlertolerant, und eine Seite muss jedes eingegebene Wort enthalten (oder eines davon, wenn Sie das Kästchen unten ankreuzen). Durchsucht werden ausschließlich maschinelle Transkriptionen. Mit „Anführungszeichen“ suchen Sie eine genaue Wortfolge, mit -Wort schließen Sie ein Wort aus; beides sucht exakt und übersieht daher Wörter, die die Maschine falsch gelesen hat. Eine Signatur mit Blatt (LH IV, 6, 18 Bl. 1r) oder eine Nummer der Akademie-Ausgabe (A VI, 4 N. 109) führt außerdem direkt an die Stelle.',
    'search.placeholder': 'z. B. calculemus',
    'search.submit': 'Suchen',
    'search.filters': 'Filter',
    'search.set': 'Bestand',
    'search.set.any': 'Alle Bestände',
    'search.lang': 'Sprache des Textes',
    'search.lang.any': 'Alle Sprachen',
    'search.stratum': 'Schreibstufe',
    'search.stratum.any': 'Alle Stufen',
    'search.minconf': 'Mindestwert der mittleren Konfidenz',
    'search.results': 'Treffer',
    'search.summary': '{total} Seitentreffer · {ms} ms',
    'search.summary.one': '{total} Seitentreffer · {ms} ms',
    'search.backend': 'Index: {backend}',
    'search.query': 'zu „{q}“',
    'search.loading': 'Suche läuft …',
    'search.start':
      'Geben Sie ein Wort oder eine Wendung ein, um die maschinellen Transkriptionen des Nachlasses zu durchsuchen.',
    'search.empty': 'Keine Seite gefunden.',
    'search.empty.hint':
      'Versuchen Sie es mit weniger Filtern, einer kürzeren Anfrage, einer anderen Schreibweise oder ohne Anführungszeichen. Der Index verzeiht Tippfehler, der durchsuchte Text ist jedoch maschinell erzeugt und fehlerhaft.',
    'search.error': 'Der Suchdienst hat nicht geantwortet.',
    'search.prev': 'Zurück',
    'search.next': 'Weiter',
    'search.pageOf': 'Seite {page} von {pages}',
    'search.pagination': 'Trefferseiten',
    'search.hit.lines': '{n} Zeilen',
    'search.also': 'auch verzeichnet als {labels}',
    'search.lookup.shelfmark': 'Diese Signatur im Nachlass',
    'search.lookup.aa': 'Dieses Stück der Akademie-Ausgabe auf seinem Scan',
    'search.lookup.id': 'Gehe zu',
    'search.lookup.text': 'Text dieses Stücks',
    'search.lookup.more': '… und {n} weitere: der Rest im Bestandsverzeichnis.',
    'search.lookup.none': 'Als Zitat gelesen: {reason}.',
    'search.hit.lines.one': '{n} Zeile',
    'search.hit.meanconf': 'mittlere Konfidenz {c}',
    'search.filteredToWork': 'Auf ein Werk eingeschränkt.',
    'search.clearWork': 'Alle Werke durchsuchen',
    'search.noWork': 'Werk ohne Titel',
    'search.browse': 'Oder den Nachlass nach Signaturen durchsehen.',
    'search.match.any': 'Seiten mit einem der Wörter',
    'search.capped':
      'Nur die ersten {reachable} der {total} Treffer lassen sich durchblättern; grenzen Sie die Suche ein, um die übrigen zu erreichen.',
    'search.pastEnd': 'Auf dieser Seite gibt es keine Treffer.',

    // ---- browse ----------------------------------------------------------
    'browse.heading': 'Der Nachlass nach Signaturen',
    'browse.intro':
      'Alle digitalisierten Einheiten des Nachlasses in der Ordnung ihrer Aufstellung: die Handschriften (LH) nach Abteilungen, der Briefwechsel (LBr) nach Korrespondenten, die annotierten Drucke (Marginalien) nach Nummern. Jeder Eintrag führt zum Werk und seinen Blättern.',
    'browse.loading': 'Verzeichnis wird geladen …',
    'browse.filter.label': 'Nach Signatur, Name oder Titel filtern',
    'browse.filter.placeholder': 'z. B. LH 35, 3 oder Oldenburg',
    'browse.filter.count': '{n} von {total} Werken passen.',
    'browse.filter.count.one': '{n} von {total} Werken passt.',
    'browse.filter.none': 'Kein Werk passt zu diesem Filter.',
    'browse.matching': '{n} von {total}',
    'browse.works': '{n} Werke',
    'browse.works.one': '{n} Werk',
    'browse.pageimages': '{n} Seitenbilder',
    'browse.pageimages.one': '{n} Seitenbild',
    'browse.pages': '{n} Seiten',
    'browse.pages.one': '{n} Seite',
    'browse.family.LH': 'Handschriften (LH)',
    'browse.family.LBr': 'Briefwechsel (LBr)',
    'browse.family.Marg': 'Marginalien',
    'browse.family.Other': 'Weitere',
    'browse.about.LH':
      'Leibniz’ Handschriften in den Abteilungen der LH-Signaturen. Die Namen der Abteilungen sind den Titeln der Bibliothek entnommen.',
    'browse.about.LBr':
      'Der Briefwechsel, ein Konvolut je Korrespondent. Ein Name steht dort, wo die verknüpften Datensätze des Arbeitskatalogs einen nennen, der zur alphabetischen Folge der LBr-Nummern passt; sonst steht nur die Signatur.',
    'browse.about.Marg': 'Drucke mit Marginalien von Leibniz, nach Nummern.',
    'browse.about.Other': 'Einheiten außerhalb der drei Signaturenreihen, nach Bestand.',
    'browse.all.LBr': 'Alle Briefkonvolute',
    'browse.all.Marg': 'Alle annotierten Drucke',
    'browse.sort.label': 'Reihenfolge der Briefkonvolute',
    'browse.sort.name': 'Nach Name',
    'browse.sort.number': 'Nach Nummer',
    'browse.unnamed': 'Hier noch ohne ermittelten Korrespondenten; nach Nummer:',
    'browse.katalog': 'Katalogisate verknüpft',
    'browse.katalog.short': 'K',
    'browse.note':
      'Titel und Signaturen sind die der Bibliothek. Die Namen der Korrespondenten stammen aus dem Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA, genutzt unter CC BY 4.0. K kennzeichnet ein Werk mit verknüpften Katalogisaten. Die Texte hinter den Links sind maschinelle Transkriptionen, keine Edition.',

    // ---- work ------------------------------------------------------------
    'work.heading': 'Werk',
    'work.set': 'Bestand',
    'work.shelfmarks': 'Signaturen',
    'work.gwlb': 'Digitalisat bei der GWLB',
    'work.manifest': 'IIIF-Manifest (GWLB)',
    'work.ourManifest': 'IIIF-Manifest mit unseren Transkriptionen',
    'work.download': 'Text dieses Werks herunterladen',
    'work.katalog': 'Katalogisate',
    'work.katalog.none': 'Diesem Werk ist bisher kein Katalogisat zugeordnet.',
    'work.katalog.incipit': 'Incipit',
    'work.katalog.date': 'Datierung',
    'work.katalog.sender': 'Absender',
    'work.katalog.addressee': 'Adressat',
    'work.katalog.aa': 'Akademie-Ausgabe',
    'work.katalog.aa.planned': 'Akademie-Ausgabe (vorgesehen, noch nicht erschienen)',
    'work.katalog.drucke': 'Weitere Drucke',
    'work.katalog.match.gwlb_link':
      'Der Katalogdatensatz verweist selbst auf dieses Digitalisat · Konfidenz {conf}',
    'work.katalog.match.shelfmark':
      'Über übereinstimmende Signaturen zugeordnet · Konfidenz {conf}',
    'work.katalog.match.manual': 'Von Hand zugeordnet · Konfidenz {conf}',
    'work.katalog.match': 'Zuordnung: {method}, Konfidenz {conf}',
    'work.katalog.record': 'Datensatz im Leibniz-Katalog',
    'work.katalog.text': 'Text dieses Stücks ({range})',
    'work.katalog.attr':
      'Katalogdaten aus dem Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA, genutzt unter CC BY 4.0.',
    'work.pages': 'Seitenbilder',
    'work.canvases': '{n} Seitenbilder',
    'work.folio': 'Blatt {label}',
    'work.canvas': 'Bild {seq}',
    'work.status.recognized': 'erkannt',
    'work.status.skipped': 'übersprungen',
    'work.lines': '{n} Zeilen',
    'work.twin.spread': 'Ein Bild mit {labels}: eine Doppelseite, am Falz geteilt',
    'work.twin.primary': 'Auch verzeichnet als {labels}; sein Text steht hier',
    'work.twin.secondary': 'Derselbe Scan wie {label}, wo sein Text steht',
    'work.search': 'In diesem Werk suchen',
    'work.search.go': 'Suchen',
    'work.lines.one': '{n} Zeile',
    'work.noPages': 'Für dieses Werk sind keine Seitenbilder verzeichnet.',
    'work.loading': 'Werk wird geladen …',

    // ---- page ------------------------------------------------------------
    'page.heading': 'Blatt {label}',
    'page.headingSeq': 'Bild {seq}',
    'page.inWork': 'in {title}',
    'page.loading': 'Seite wird geladen …',
    'page.nav': 'Seitennavigation innerhalb des Werks',
    'page.prev': 'Vorherige Seite',
    'page.next': 'Nächste Seite',
    'page.overlay.show': 'Zeilenraster einblenden',
    'page.overlay.hide': 'Zeilenraster ausblenden',
    'page.viewer.label': 'Seitenbild, zoombar',
    'page.viewer.noIiif':
      'Diese Seite wird als einzelnes Bild ausgeliefert; eine Tiefenzoom-Ansicht steht dafür nicht zur Verfügung.',
    'page.skipped': 'Diese Seite wurde nicht transkribiert.',
    'page.skipReason': 'Grund: {reason}',
    'page.lines': 'Zeilen',
    'page.lines.count': '{n} Zeilen · mittlere Konfidenz {c}',
    'page.noLines': 'Auf dieser Seite wurden keine Zeilen erkannt.',
    'page.linesHelp':
      'Wählen Sie eine Zeile, um sie im Bild hervorzuheben; mit den Pfeiltasten wechseln Sie zwischen den Zeilen. Ziehen Sie über den Text, um ihn zu markieren, oder kopieren Sie die ganze Seite aus dem Textblock darunter.',
    'page.line': 'Zeile {n}',
    'page.lineEmpty': '(leere Zeile)',
    'page.mirador': 'In Mirador oder einem anderen IIIF-Viewer öffnen',
    'page.gwlb': 'Diese Seite bei der GWLB',
    'page.report': 'Fehler melden',
    // ---- der Textblock
    'page.textLink': 'Text dieser Seite',
    'page.text': 'Text',
    'page.text.help':
      'Die erkannten Zeilen als ein zusammenhängender Text in Lesereihenfolge, zum Markieren und Kopieren; Status und Konfidenz stehen in der Zeilenliste darüber.',
    'page.text.copy': 'Text kopieren',
    'page.text.copied': 'Kopiert: {n} Zeilen.',
    'page.text.copied.one': 'Kopiert: {n} Zeile.',
    'page.text.copyRefused':
      'Der Browser hat den Zugriff auf die Zwischenablage nicht erlaubt. Der Text ist markiert: Drücken Sie Strg+C (⌘C auf dem Mac), um ihn zu kopieren.',
    'page.text.download': 'Diese Seite als Text herunterladen',
    'page.text.prov':
      'Maschinelle Transkription: {runs}. Zitieren Sie sie als „die Maschine liest …“, nie als „Leibniz schrieb“.',
    'page.text.run': '{model}, Lauf vom {date}',
    'page.text.noModel': 'Modell nicht erfasst',
    'page.text.noDate': 'Datum nicht erfasst',
    'page.provenance': 'Provenienz',
    'page.prov.model': 'Modell',
    'page.prov.run': 'Lauf',
    'page.prov.runDate': 'Datum des Laufs',
    'page.prov.status': 'Status',
    'page.prov.source': 'Quelle',
    'page.prov.none': 'Maschinelle Ausgabe; keine externe Quelle.',
    'page.prov.image': 'Bildquelle',
    'page.prov.lineId': 'Zeilen-ID',
    'page.prov.iiif': 'IIIF-Bilddienst',
    'page.conf': 'Konfidenz {c}',
    'page.confUnknown': 'Konfidenz nicht erfasst',
    'page.langOf': 'Sprache: {lang}',
    'page.crossesFold': 'über den Falz',
    'page.cite': 'Zitieren',
    'page.cite.page': 'Diese Seite in dieser Lesung. Eine Zeile auswählen, um sie allein zu zitieren.',
    'page.cite.lineWhat': 'Zeile {n} dieser Seite. Ihre Adresse endet jetzt auf #L{n}: ein Link auf sie.',
    'page.cite.text': '{title}, {where}. Maschinelle Transkription, keine Edition: Leibniz Legible{made}. {link}',
    'page.cite.folio': 'Bl. {label}',
    'page.cite.canvas': 'Bild {seq}',
    'page.cite.line': '{where}, Zeile {n}',
    'page.cite.model': 'Modell {model}',
    'page.cite.run': 'Lauf {run}',
    'page.cite.lineId': 'Zeilen-ID {id}',
    'page.cite.copy': 'Zitat kopieren',
    'page.cite.copied': 'Zitat kopiert.',
    'page.run.older': 'Sie lesen diese Seite so, wie Erkennungslauf {run} sie hinterlassen hat; ein späterer Lauf ({now}) liest sie neu. {current}',
    'page.run.pinned': 'Diese Adresse ist an Erkennungslauf {run} gebunden, die aktuelle Lesung: Ein späterer Lauf ändert nicht, was sie zeigt. {current}',
    'page.run.current': 'Die aktuelle Lesung',
    'page.crossesFold.title': 'Die Maschine hat diese Zeile über den Falz der Doppelseite hinweg gelesen; sie erscheint auf beiden Hälften.',
    'page.twin.spread': 'Dieses Bild zeigt zwei Blattseiten nebeneinander; die Bibliothek hat es unter beiden Blattnummern verzeichnet ({others}). Diese Seite ist seine {side} Hälfte; Zeilen, die über den Falz laufen, erscheinen auf beiden Hälften.',
    'page.twin.left': 'linke',
    'page.twin.right': 'rechte',
    'page.twin.primary': 'Derselbe Scan ist auch als {others} verzeichnet. Suche und Downloads geben seinen Text einmal, hier.',
    'page.twin.secondary': 'Derselbe Scan wie {primary}: Suche und Downloads geben seinen Text dort. Unten steht die Lesung dieses Eintrags.',
    'page.viewerError': 'Das Seitenbild konnte nicht geladen werden.',

    // ---- statuses --------------------------------------------------------
    'status.machine': 'maschinell',
    'status.machine.help': 'HTR-Ausgabe, ungeprüft.',
    'status.aligned': 'aligniert',
    'status.aligned.help': 'Mit einem gedruckten Editionstext abgeglichen.',
    'status.corrected': 'korrigiert',
    'status.corrected.help': 'Korrektur durch einen Menschen oder die Crowd.',
    'status.verified': 'verifiziert',
    'status.verified.help': 'Von einer namentlich benannten Fachperson geprüft.',

    // ---- language tags ---------------------------------------------------
    'lang.la': 'Latein',
    'lang.fr': 'Französisch',
    'lang.de.text': 'Deutsch',
    'lang.mixed': 'Gemischt',
    'lang.unknown': 'Unbestimmt',

    // ---- strata ----------------------------------------------------------
    'stratum.fair_copy': 'Reinschrift',
    'stratum.light_revision': 'Leicht überarbeitet',
    'stratum.heavy_revision': 'Stark überarbeitet',
    'stratum.scrap': 'Notizzettel',
    'stratum.unknown': 'Unbestimmt',

    // ---- collections -----------------------------------------------------
    'set.LeibnizHandschriften': 'Leibniz-Handschriften (LH)',
    'set.LeibnizBriefwechsel': 'Leibniz-Briefwechsel (LBr)',
    'set.LeibnizMarginalien': 'Leibniz-Marginalien',
    'set.Leibnitiana': 'Leibnitiana',
    'set.leibniz-rekonstruktionen': 'Leibniz-Rekonstruktionen',

    // ---- about -----------------------------------------------------------
    'about.heading': 'Über Leibniz Legible',
    'about.what.h': 'Was das hier ist',
    'about.what.p1':
      'Leibniz Legible ist eine Zugangsschicht zum digitalisierten Leibniz-Nachlass der Gottfried Wilhelm Leibniz Bibliothek (GWLB) in Hannover. Jedes von der Bibliothek veröffentlichte Seitenbild wird durch eine Handschriftenerkennung geführt; das Ergebnis wird Zeile für Zeile lesbar und durchsuchbar gemacht, wobei jede Zeile ihren eigenen Konfidenzwert und ihre vollständige Provenienz mitführt.',
    'about.what.p2':
      'Das ist maschinelle Ausgabe mit ehrlicher Kennzeichnung. Sie hat bestenfalls den Rang einer Vorausedition und ist der Akademie-Ausgabe ausdrücklich nachgeordnet; diese bleibt die wissenschaftliche Edition der Schriften von Leibniz. Nichts hier ist eine Edition, und nichts hier sollte als solche zitiert werden. Nach eigener Zählung ist die Akademie-Ausgabe etwa bei der Hälfte der geplanten Bände, und eine ihrer Editorinnen schätzt, dass drei Viertel der Leibniz-Papiere nie irgendwo veröffentlicht wurden (Herma Kliege-Biller, Leibniz-Forschungsstelle Münster, 2023); alles lesbar und auffindbar zu machen ist der ganze Anspruch dieses Projekts.',
    'about.what.p3':
      'Die Seitenbilder werden nicht gespiegelt. Sie werden in Ihrem Browser unmittelbar von den Servern der GWLB geladen.',
    'about.what.p3.mirror':
      'Die Seitenbilder sind die Auslieferungsscans der GWLB selbst, Public Domain Mark 1.0, ausgeliefert aus einer Kopie, die dieses Projekt vorhält, damit der Viewer weder von den Servern der Bibliothek abhängt noch sie belastet. Jede Seite verweist auf ihr Original bei der GWLB.',

    'about.numbers.h': 'Das Korpus in Zahlen',
    'about.numbers.loading': 'Aktuelle Zahlen werden geladen …',
    'about.numbers.error': 'Die Zahlen konnten nicht geladen werden.',
    'about.numbers.works': 'Werke',
    'about.numbers.pages': 'Seitenbilder',
    'about.numbers.recognized': 'Erkannte Seiten',
    'about.numbers.skipped': 'Übersprungene Seiten',
    'about.numbers.lines': 'Zeilen',
    'about.numbers.images': 'Verschiedene Scans',
    'about.numbers.linesOnce': 'Zeilen, jeder Scan einmal',
    'about.numbers.version': 'Softwareversion',
    'about.numbers.caveat':
      'Die Seiten- und Zeilenzahlen folgen den Seiteneinträgen der Bibliothek. Die GWLB fotografiert einen aufgefalteten Bogen als ein Bild, zwei Blattseiten nebeneinander, und verzeichnet dieses Bild unter beiden Blattnummern, jeweils mit eigener Kopie der Datei; die Erkennung hat jedes solche Bild einmal je Nummer gelesen. Wo zwei Einträge nachweislich ein Scan sind (gleiche Größe, fast dieselbe Datei, die Zeilen an denselben Stellen), geben Suche und Downloads seinen Text einmal: Eine Doppelseite wird am Falz in ihre zwei Blattseiten geteilt, jede andere Wiederholung steht auf einer Seite. „Verschiedene Scans“ und „Zeilen, jeder Scan einmal“ zählen so.',
    'about.numbers.caveatRaw':
      'Die Seiten- und Zeilenzahlen folgen den Seiteneinträgen der Bibliothek. Die GWLB fotografiert einen aufgefalteten Bogen als ein Bild, zwei Blattseiten nebeneinander, und verzeichnet dieses Bild unter beiden Blattnummern; viele Bilder wurden daher zweimal gelesen, und die Zeilensumme zählt sie doppelt. Der nächste Aufbau des Suchindex findet sie und zählt jeden Scan einmal.',
    'about.numbers.backend': 'Suchindex',
    'about.numbers.model': 'Erkennungsmodell',
    'about.hist.h': 'Verteilung der Zeilenkonfidenz',
    'about.hist.band': 'Konfidenzband',
    'about.hist.lines': 'Zeilen',
    'about.hist.share': 'Anteil',

    'about.error.h': 'Wie falsch ist das?',
    'about.error.p1':
      'Auf dem Validierungsteil von PHILIUMM — 1.878 Zeilen aus Leibniz’ lateinischer und französischer Hand — erreicht das von uns eingesetzte Modell eine Zeichenfehlerrate von 7,95 % (95-%-Konfidenzintervall 7,49–8,46) und eine Wortfehlerrate von 27,0 %. Das ist etwa ein falsches Zeichen je dreizehn und etwa jedes vierte Wort von einem Fehler berührt.',
    'about.error.p2':
      'Deutsch in Kurrentschrift ist überhaupt nicht gemessen, denn für Leibniz’ deutsche Hand existieren nirgends Referenzdaten. Es ist mit Sicherheit deutlich schlechter und macht rund 15 % des Korpus aus. Mathematische Notation, Zeichnungen und stark überarbeitete Entwürfe sind ebenso schwach. Lesen Sie jede Zeile hier als eine Vermutung über die Handschrift, nicht als deren Lesung.',
    'about.error.p3':
      'Das Modell ist FoNDUE-GD_v2_ft_Leibniz aus dem Projekt PHILIUMM (Kraken), doi:10.5281/zenodo.21457538, CC BY 4.0. Unsere Reproduktion der veröffentlichten Werte liegt im Projekt-Repositorium.',

    'about.legend.h': 'Legende der Zeilenstatus',
    'about.legend.intro':
      'Jede Zeile trägt einen von vier Status. Ohne Status wird nichts veröffentlicht.',

    'about.report.h': 'Fehler melden',
    'about.report.p':
      'Jede Seitenansicht trägt einen Link „Fehler melden“, der im Projekt-Repositorium ein Ticket mit bereits eingetragener Seitenkennung öffnet. Korrekturen einzelner Zeilen, Hinweise auf systematische Schwächen und Meldungen falscher Katalogzuordnungen sind gleichermaßen willkommen. Es gibt weder Benutzerkonten noch ein Kommentarfeld; der Weg führt über den Issue-Tracker.',

    'about.license.h': 'Lizenzen und Nachweis',
    'about.license.images.h': 'Seitenbilder',
    'about.license.images.p':
      'Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. An den Digitalisaten bestehen keine Leistungsschutzrechte; sie werden unmittelbar von der GWLB in Ihren Browser geladen und niemals auf unsere Server kopiert.',
    'about.license.images.p.mirror':
      'Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. An den Digitalisaten bestehen keine Leistungsschutzrechte (§ 68 UrhG). Die hier gezeigten Kopien sind die Auslieferungsderivate der GWLB, unverändert bis auf die Vorschaubilder, ausgeliefert aus dem eigenen Speicher dieses Projekts; jede Seite verweist auf ihr Original bei der GWLB, deren Masterdateien die maßgebliche Quelle bleiben.',
    'about.license.katalog.h': 'Katalogdaten',
    'about.license.katalog.p':
      'Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, Berlin-Brandenburgische Akademie der Wissenschaften (BBAW) / TELOTA. CC BY 4.0. Der Katalog ist das metadatentragende Rückgrat des ganzen Feldes; jeder Link auf einen Datensatz ist ein Link auf deren Arbeit.',
    'about.license.transcriptions.h': 'Transkriptionen',
    'about.license.transcriptions.p':
      'Leibniz Legible, CC BY 4.0. Maschinelle Ausgabe. Bitte übernehmen Sie sie nicht als geprüften Text, und führen Sie bei einer Weitergabe die Provenienzangaben mit. Der Text lässt sich als reiner Text mitnehmen, jede Datei mit ihrer Provenienz in einem Kopf: je Seite (jede Seitenansicht hat einen Textblock mit Kopierknopf und Download), je Werk (von der Werkseite) und je Katalogstück über seine Blätter hinweg (von jedem Katalogisat auf der Werkseite, das sich auf dem Digitalisat verorten lässt).',
    'about.license.code.h': 'Quellcode',
    'about.license.code.p': 'Apache-2.0, im Projekt-Repositorium.',

    'about.repo.h': 'Das Projekt',
    'about.repo.p': 'Quellcode, Datensätze, Berichte und Issue-Tracker:',
    'about.repo.reports':
      'Berichte auf Zenodo (CC BY 4.0): die Projektbeschreibung doi:10.5281/zenodo.22782813, der Korpuszensus doi:10.5281/zenodo.22782815, die PHILIUMM-Reproduktion mit dem Benchmark der Bildsprachmodelle doi:10.5281/zenodo.22782817 und die retro-alignierte Ground Truth doi:10.5281/zenodo.22782819.',

    'about.calculemus.h': 'Calculemus',
    'about.calculemus.p':
      'Calculemus ist ein Spiel auf der Grundlage dieses Korpus: Spielerinnen und Spieler urteilen über zwei maschinelle Lesungen einer Handschriftenzeile, und ihre kalibrierten, zusammengeführten Urteile werden zur Übereinstimmung der Crowd über den Maschinentext — korrigiert, nie verifiziert. Zu spielen unter',

    'about.who.h': 'Wer das gemacht hat',
    'about.who.p1':
      'Leibniz Legible ist ein offenes Ein-Personen-Projekt von Evan Tabak Atlas, freier Autor und Forscher in New York (evanatlas.com, ORCID 0009-0007-7374-2338). Es ist weder mit der Gottfried Wilhelm Leibniz Bibliothek noch mit der Leibniz-Edition verbunden und beansprucht nichts, was diese nicht zuerst beansprucht hätten.',
    'about.who.p2':
      'Korrekturen, Fragen aus den Editionsstellen und Angebote zur Mitarbeit sind über den unten verlinkten Issue-Tracker willkommen.',

    'about.credits.h': 'Grundlagen',
    'about.credits.images':
      'Die Digitalisate der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover (Public Domain Mark 1.0), digitalisiert 2016–2019.',
    'about.credits.katalog':
      'Der Arbeitskatalog der Leibniz-Edition („Ritter-Katalog“), Berlin-Brandenburgische Akademie der Wissenschaften, Leibniz-Edition Potsdam I / TELOTA, CC BY 4.0: über 70.000 Datensätze, die jeden Scan mit Datierung, Titel und Editionsnachweis verbinden.',
    'about.credits.model':
      'Das Handschriftenmodell des ERC-Projekts PHILIUMM für Leibniz’ Hand (Denisa-Florina Bumba, Laboratoire SPHERE, Université Paris Cité – CNRS, ERC-Grant 101020985; doi:10.5281/zenodo.21457538, CC BY 4.0), nachtrainiert aus FoNDUE-GD v2 (Simon Gabay, Genf) und betrieben mit Kraken (Benjamin Kiessling). Leibniz Legible hat dessen veröffentlichte Werte reproduziert, bevor es darauf aufbaute.',
    'about.credits.edition':
      'Der Lesetext derjenigen Bände der Akademie-Ausgabe, deren 25-jähriger Editionsschutz (§ 70 UrhG) abgelaufen ist, ausschließlich zum Trainieren und Messen; Einleitungen, Apparat und Kommentar der Herausgeber gelangen nie in die Pipeline.',
    'about.credits.precedents':
      'Das Vorbild von Bullinger Digital (Zürich), GLOBALISE (Huygens-Institut) und Transcribe Bentham (UCL), die maschinelle Transkription über ein ganzes Archiv gelegt haben, bevor eine Edition es konnte, und das ehrlich gesagt haben.',

    'about.edition.h': 'Wo die eigentliche Arbeit geschieht',
    'about.edition.p1':
      'Die Akademie-Ausgabe, Gottfried Wilhelm Leibniz: Sämtliche Schriften und Briefe, wird seit 1923 in Hannover (Leibniz-Archiv / Leibniz-Forschungsstelle an der GWLB), Münster (Leibniz-Forschungsstelle) und Potsdam (Leibniz-Edition Potsdam I und II) für die Berlin-Brandenburgische Akademie der Wissenschaften und die Akademie der Wissenschaften zu Göttingen im Akademienprogramm erarbeitet: 68 Bände bis 2023, etwa die Hälfte der rund 130 geplanten, Abschluss voraussichtlich um 2055.',
    'about.edition.p2':
      'Für den gesicherten Text, die Datierung und den Kommentar: leibnizedition.de, der Arbeitskatalog sowie die Transkriptionen und Vorauseditionen des Leibniz-Archivs; für englische Übersetzungen Lloyd Stricklands Leibniz Translations. Jeder von einer Werkseite hier verlinkte Katalogeintrag ist ein Link auf deren Arbeit.',

    'about.timeline.h': 'Eine kurze Zeitleiste',
    'about.timeline.1716': '1716 — Leibniz stirbt in Hannover; der Hof versiegelt seine Papiere.',
    'about.timeline.1889': '1889 / 1895 — Bodemanns Kataloge geben Briefen (LBr) und Handschriften (LH) die bis heute gültigen Signaturen.',
    'about.timeline.1901': '1901 — Die Akademien planen die Edition; Ritters Katalog beginnt.',
    'about.timeline.1923': '1923 — Der erste Band der Akademie-Ausgabe erscheint.',
    'about.timeline.2007': '2007 — Die UNESCO nimmt den Briefwechsel in das Register des Weltdokumentenerbes auf.',
    'about.timeline.2016': '2016–2019 — Die GWLB digitalisiert den gesamten hannoverschen Nachlass und stellt ihn unter offenen Lizenzen bereit.',
    'about.timeline.2026a': 'Juli 2026 — PHILIUMM veröffentlicht sein offenes Leibniz-Handschriftenmodell samt Ground Truth.',
    'about.timeline.2026b': '21. September 2026 — Leibniz Legible geht online.',
    'about.timeline.2055': 'um 2055 — Geplanter Abschluss der Akademie-Ausgabe.',

    'about.cite.h': 'Zitieren',
    'about.cite.p':
      'Leibniz Legible (2026), maschinelle Transkription des digitalisierten Leibniz-Nachlasses, https://leibnizlegible.com, CC BY 4.0; Projektbeschreibung doi:10.5281/zenodo.22782813. Bitte zitieren Sie Zeilen als „die Maschine liest …“, mit dem Link zur Seite und möglichst mit Zeilenkennung und Konfidenz.',
    'about.lang.p': 'Diese Seite liegt auf Englisch und auf Deutsch vor.',

    // ---- errors ----------------------------------------------------------
    'error.h': 'Etwas ist schiefgegangen',
    'error.retry': 'Erneut versuchen',
    'error.network': 'Der Server war nicht erreichbar.',
    'error.http': 'Der Server antwortete mit Status {status}.',
    'error.notfound.h': 'Nicht gefunden',
    'error.notfound.p': 'Unter dieser Adresse liegt nichts.',
    'error.notfound.back': 'Zur Suche',
    'error.badRoute': 'Unbekannte Adresse: {path}',
  },
};

let current = 'en';
const listeners = new Set();

function detect() {
  let stored = null;
  try {
    stored = window.localStorage.getItem(STORAGE_KEY);
  } catch {
    stored = null; // private mode, blocked storage — fall through to navigator
  }
  if (stored && LANGS.includes(stored)) return stored;
  const nav = (navigator.language || 'en').toLowerCase();
  return nav.startsWith('de') ? 'de' : 'en';
}

/** The active language code, 'en' or 'de'. */
export function getLang() {
  return current;
}

/** All supported language codes. */
export function languages() {
  return LANGS.slice();
}

/** The BCP-47 locale used for number formatting. */
export function locale() {
  return current === 'de' ? 'de-DE' : 'en-GB';
}

/** Switch language, persist it, update <html lang>, notify listeners. */
export function setLang(lang) {
  if (!LANGS.includes(lang) || lang === current) return;
  current = lang;
  try {
    window.localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    /* storage unavailable — the choice simply will not persist */
  }
  document.documentElement.lang = lang;
  for (const cb of listeners) cb(lang);
}

/** Subscribe to language changes. Returns an unsubscribe function. */
export function onLangChange(cb) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

/** Look up `key` in the active language and substitute `{placeholders}`. */
export function t(key, vars) {
  const table = STRINGS[current] || STRINGS.en;
  let s = table[key];
  if (s === undefined) s = STRINGS.en[key];
  if (s === undefined) return key;
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (m, name) =>
    Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : m,
  );
}

/** Pick a singular/plural key pair by count: `base` and `base + '.one'`. */
export function tn(base, n, vars) {
  const key = n === 1 ? `${base}.one` : base;
  return t(STRINGS[current][key] !== undefined ? key : base, { n, ...vars });
}

/** Initialise from storage / navigator. Called once by app.js. */
export function initLang() {
  current = detect();
  document.documentElement.lang = current;
  return current;
}
