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
    'nav.about': 'About',
    'lang.label': 'Language',
    'lang.en': 'English',
    'lang.de': 'German',
    'footer.label': 'Attribution and licensing',
    'footer.repo': 'Source code and issue tracker',

    // ---- attribution (shown on every view) ------------------------------
    'attr.images':
      'Images: Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. Loaded directly from the GWLB; never rehosted.',
    'attr.katalog':
      'Catalogue: Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA. CC BY 4.0.',
    'attr.transcriptions':
      'Transcriptions: Leibniz Legible, CC BY 4.0 — machine output, not an edition.',
    'attr.code': 'Code: Apache-2.0.',

    // ---- the honesty banner ---------------------------------------------
    'honesty.banner':
      'Machine transcription. Not an edition. Errors are expected (character error rate about 8% on Latin and French, higher on German).',

    // ---- search ----------------------------------------------------------
    'search.heading': 'Search the Nachlass',
    'search.label': 'Search the Nachlass',
    'search.hint': 'The index is typo-tolerant. Search is over machine transcriptions only.',
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
      'Try fewer filters, a shorter query, or a different spelling. The index tolerates typos, but the text it searches is machine output and contains errors.',
    'search.error': 'The search service did not answer.',
    'search.prev': 'Previous',
    'search.next': 'Next',
    'search.pageOf': 'Page {page} of {pages}',
    'search.pagination': 'Result pages',
    'search.hit.lines': '{n} lines',
    'search.hit.lines.one': '{n} line',
    'search.hit.meanconf': 'mean confidence {c}',
    'search.filteredToWork': 'Restricted to one work.',
    'search.clearWork': 'Search all works',
    'search.noWork': 'Untitled work',

    // ---- work ------------------------------------------------------------
    'work.heading': 'Work',
    'work.set': 'Collection',
    'work.shelfmarks': 'Shelfmarks',
    'work.gwlb': 'GWLB record',
    'work.manifest': 'IIIF manifest (GWLB)',
    'work.ourManifest': 'IIIF manifest with our transcriptions',
    'work.katalog': 'Catalogue records',
    'work.katalog.none': 'No catalogue record is linked to this work yet.',
    'work.katalog.incipit': 'Incipit',
    'work.katalog.date': 'Date',
    'work.katalog.correspondent': 'Correspondent',
    'work.katalog.aa': 'Akademie-Ausgabe',
    'work.katalog.match': 'Link: {method}, confidence {conf}',
    'work.katalog.record': 'Record in the Leibniz-Katalog',
    'work.katalog.attr':
      'Catalogue data from the Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA, used under CC BY 4.0.',
    'work.pages': 'Page images',
    'work.canvases': '{n} page images',
    'work.folio': 'Folio {label}',
    'work.canvas': 'Canvas {seq}',
    'work.status.recognized': 'recognised',
    'work.status.skipped': 'skipped',
    'work.lines': '{n} lines',
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
    'page.overlay.toggle': 'Show line overlay',
    'page.viewer.label': 'Page image, zoomable',
    'page.viewer.noIiif':
      'This page is served as a single image; deep zoom is not available for it.',
    'page.skipped': 'This page was not transcribed.',
    'page.skipReason': 'Reason: {reason}',
    'page.lines': 'Lines',
    'page.lines.count': '{n} lines · mean confidence {c}',
    'page.noLines': 'No lines were recognised on this page.',
    'page.linesHelp':
      'Select a line to highlight it on the image. Arrow keys move between lines.',
    'page.line': 'Line {n}',
    'page.lineEmpty': '(empty line)',
    'page.mirador': 'Open in Mirador or another IIIF viewer',
    'page.report': 'Report an error',
    'page.provenance': 'Provenance',
    'page.prov.model': 'Model',
    'page.prov.run': 'Run',
    'page.prov.runDate': 'Run date',
    'page.prov.status': 'Status',
    'page.prov.source': 'Source',
    'page.prov.none': 'Machine output; no external source.',
    'page.prov.image': 'Image',
    'page.conf': 'confidence {c}',
    'page.confUnknown': 'confidence not recorded',
    'page.langOf': 'language: {lang}',
    'page.viewerError': 'The page image could not be loaded from the GWLB.',

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
      'This is machine output with honest labels. It is Vorausedition-grade at best, and it is explicitly subordinate to the Akademie-Ausgabe, which remains the scholarly edition of Leibniz. Nothing here is an edition, and nothing here should be quoted as one. Roughly three quarters of the Nachlass has never been printed in any form; making it legible and findable is the whole of the ambition.',
    'about.what.p3':
      'The page images are never rehosted. They are loaded in your browser directly from the GWLB’s own servers.',

    'about.numbers.h': 'The corpus in numbers',
    'about.numbers.loading': 'Loading the current figures…',
    'about.numbers.error': 'The figures could not be loaded.',
    'about.numbers.works': 'Works',
    'about.numbers.pages': 'Page images',
    'about.numbers.recognized': 'Pages recognised',
    'about.numbers.skipped': 'Pages skipped',
    'about.numbers.lines': 'Lines',
    'about.numbers.version': 'Data version',
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
    'about.license.katalog.h': 'Catalogue data',
    'about.license.katalog.p':
      'Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, Berlin-Brandenburgische Akademie der Wissenschaften (BBAW) / TELOTA. CC BY 4.0. The catalogue is the metadata spine of the whole field; every link out to a record is a link to their work.',
    'about.license.transcriptions.h': 'Transcriptions',
    'about.license.transcriptions.p':
      'Leibniz Legible, CC BY 4.0. Machine output. Please do not ingest it as verified text, and please carry the provenance fields with it if you redistribute it.',
    'about.license.code.h': 'Code',
    'about.license.code.p': 'Apache-2.0, in the project repository.',

    'about.repo.h': 'The project',
    'about.repo.p': 'Source code, datasets, reports and the issue tracker:',
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
    'nav.about': 'Über das Projekt',
    'lang.label': 'Sprache',
    'lang.en': 'Englisch',
    'lang.de': 'Deutsch',
    'footer.label': 'Nachweis und Lizenzen',
    'footer.repo': 'Quellcode und Fehlermeldungen',

    // ---- attribution -----------------------------------------------------
    'attr.images':
      'Digitalisate: Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover. Public Domain Mark 1.0. Direkt von der GWLB geladen, niemals gespiegelt.',
    'attr.katalog':
      'Katalogdaten: Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA. CC BY 4.0.',
    'attr.transcriptions':
      'Transkriptionen: Leibniz Legible, CC BY 4.0 — maschinell erzeugt, keine Edition.',
    'attr.code': 'Quellcode: Apache-2.0.',

    // ---- honesty banner --------------------------------------------------
    'honesty.banner':
      'Maschinelle Transkription. Keine Edition. Fehler sind zu erwarten (Zeichenfehlerrate rund 8 % bei Latein und Französisch, bei Deutsch höher).',

    // ---- search ----------------------------------------------------------
    'search.heading': 'Den Nachlass durchsuchen',
    'search.label': 'Den Nachlass durchsuchen',
    'search.hint':
      'Der Index ist tippfehlertolerant. Durchsucht werden ausschließlich maschinelle Transkriptionen.',
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
      'Versuchen Sie es mit weniger Filtern, einer kürzeren Anfrage oder einer anderen Schreibweise. Der Index verzeiht Tippfehler, der durchsuchte Text ist jedoch maschinell erzeugt und fehlerhaft.',
    'search.error': 'Der Suchdienst hat nicht geantwortet.',
    'search.prev': 'Zurück',
    'search.next': 'Weiter',
    'search.pageOf': 'Seite {page} von {pages}',
    'search.pagination': 'Trefferseiten',
    'search.hit.lines': '{n} Zeilen',
    'search.hit.lines.one': '{n} Zeile',
    'search.hit.meanconf': 'mittlere Konfidenz {c}',
    'search.filteredToWork': 'Auf ein Werk eingeschränkt.',
    'search.clearWork': 'Alle Werke durchsuchen',
    'search.noWork': 'Werk ohne Titel',

    // ---- work ------------------------------------------------------------
    'work.heading': 'Werk',
    'work.set': 'Bestand',
    'work.shelfmarks': 'Signaturen',
    'work.gwlb': 'Digitalisat bei der GWLB',
    'work.manifest': 'IIIF-Manifest (GWLB)',
    'work.ourManifest': 'IIIF-Manifest mit unseren Transkriptionen',
    'work.katalog': 'Katalogisate',
    'work.katalog.none': 'Diesem Werk ist bisher kein Katalogisat zugeordnet.',
    'work.katalog.incipit': 'Incipit',
    'work.katalog.date': 'Datierung',
    'work.katalog.correspondent': 'Korrespondent',
    'work.katalog.aa': 'Akademie-Ausgabe',
    'work.katalog.match': 'Zuordnung: {method}, Konfidenz {conf}',
    'work.katalog.record': 'Datensatz im Leibniz-Katalog',
    'work.katalog.attr':
      'Katalogdaten aus dem Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, BBAW / TELOTA, genutzt unter CC BY 4.0.',
    'work.pages': 'Seitenbilder',
    'work.canvases': '{n} Seitenbilder',
    'work.folio': 'Blatt {label}',
    'work.canvas': 'Bild {seq}',
    'work.status.recognized': 'erkannt',
    'work.status.skipped': 'übersprungen',
    'work.lines': '{n} Zeilen',
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
    'page.overlay.toggle': 'Zeilenraster einblenden',
    'page.viewer.label': 'Seitenbild, zoombar',
    'page.viewer.noIiif':
      'Diese Seite wird als einzelnes Bild ausgeliefert; eine Tiefenzoom-Ansicht steht dafür nicht zur Verfügung.',
    'page.skipped': 'Diese Seite wurde nicht transkribiert.',
    'page.skipReason': 'Grund: {reason}',
    'page.lines': 'Zeilen',
    'page.lines.count': '{n} Zeilen · mittlere Konfidenz {c}',
    'page.noLines': 'Auf dieser Seite wurden keine Zeilen erkannt.',
    'page.linesHelp':
      'Wählen Sie eine Zeile, um sie im Bild hervorzuheben. Mit den Pfeiltasten wechseln Sie zwischen den Zeilen.',
    'page.line': 'Zeile {n}',
    'page.lineEmpty': '(leere Zeile)',
    'page.mirador': 'In Mirador oder einem anderen IIIF-Viewer öffnen',
    'page.report': 'Fehler melden',
    'page.provenance': 'Provenienz',
    'page.prov.model': 'Modell',
    'page.prov.run': 'Lauf',
    'page.prov.runDate': 'Datum des Laufs',
    'page.prov.status': 'Status',
    'page.prov.source': 'Quelle',
    'page.prov.none': 'Maschinelle Ausgabe; keine externe Quelle.',
    'page.prov.image': 'Bildquelle',
    'page.conf': 'Konfidenz {c}',
    'page.confUnknown': 'Konfidenz nicht erfasst',
    'page.langOf': 'Sprache: {lang}',
    'page.viewerError': 'Das Seitenbild konnte nicht von der GWLB geladen werden.',

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
      'Das ist maschinelle Ausgabe mit ehrlicher Kennzeichnung. Sie hat bestenfalls den Rang einer Vorausedition und ist der Akademie-Ausgabe ausdrücklich nachgeordnet; diese bleibt die wissenschaftliche Edition der Schriften von Leibniz. Nichts hier ist eine Edition, und nichts hier sollte als solche zitiert werden. Etwa drei Viertel des Nachlasses sind nie gedruckt worden; ihn lesbar und auffindbar zu machen ist der ganze Anspruch dieses Projekts.',
    'about.what.p3':
      'Die Seitenbilder werden nicht gespiegelt. Sie werden in Ihrem Browser unmittelbar von den Servern der GWLB geladen.',

    'about.numbers.h': 'Das Korpus in Zahlen',
    'about.numbers.loading': 'Aktuelle Zahlen werden geladen …',
    'about.numbers.error': 'Die Zahlen konnten nicht geladen werden.',
    'about.numbers.works': 'Werke',
    'about.numbers.pages': 'Seitenbilder',
    'about.numbers.recognized': 'Erkannte Seiten',
    'about.numbers.skipped': 'Übersprungene Seiten',
    'about.numbers.lines': 'Zeilen',
    'about.numbers.version': 'Datenstand',
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
    'about.license.katalog.h': 'Katalogdaten',
    'about.license.katalog.p':
      'Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition, Berlin-Brandenburgische Akademie der Wissenschaften (BBAW) / TELOTA. CC BY 4.0. Der Katalog ist das metadatentragende Rückgrat des ganzen Feldes; jeder Link auf einen Datensatz ist ein Link auf deren Arbeit.',
    'about.license.transcriptions.h': 'Transkriptionen',
    'about.license.transcriptions.p':
      'Leibniz Legible, CC BY 4.0. Maschinelle Ausgabe. Bitte übernehmen Sie sie nicht als geprüften Text, und führen Sie bei einer Weitergabe die Provenienzangaben mit.',
    'about.license.code.h': 'Quellcode',
    'about.license.code.p': 'Apache-2.0, im Projekt-Repositorium.',

    'about.repo.h': 'Das Projekt',
    'about.repo.p': 'Quellcode, Datensätze, Berichte und Issue-Tracker:',
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
