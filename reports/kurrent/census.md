# German census of the edition pieces

10,029 records of the C2 edition cache, each classified by the stopword identifier (`leibniz.enrich.langid`: Latin, French, German, mixed, unknown, with the leading language's share of the stopword hits as its score). 17,162 §70 pieces enumerated on 2026-10-09; 10,121 of them have a text in the cache and are the pieces below (7,041 have none). A piece is placed on its canvases by the C2 resolver; its lines are the recognised v1 lines on those pages, its minted lines the `gt_lines` the factory wrote for its record, its stratum the factory's (layout statistics plus Textart); yield is minted ÷ lines. Read-only over the store.

## The hypothesis

German pieces (German, or mixed with German leading): **2,173** of 10,121 (21.5 %), 1,694 localizable, 1,665 with recognised lines on **5,874 pages, 401,394 lines**; the factory minted **40,915** lines on them (yield 10.2 %). Latin and French pieces: 7,694, 5,269 with lines on 20,559 pages, 1,328,532 lines, **252,762** minted (yield 19.0 %).

| group | pieces | localizable | with lines | pages | lines | minted | yield |
|---|---:|---:|---:|---:|---:|---:|---:|
| German (de, or mixed with de leading) | 2,173 | 1,694 | 1,665 | 5,874 | 401,394 | 40,915 | 10.2 % |
| Latin and French | 7,694 | 5,321 | 5,269 | 20,559 | 1,328,532 | 252,762 | 19.0 % |
| other (mixed otherwise, unknown) | 254 | 202 | 195 | 596 | 38,118 | 5,734 | 15.0 % |

What the factory minted on them, without ground truth: the aligner's confidence of the minted lines, and the language the minted text's stopwords give it — `de` German stopwords only, `la/fr` Latin or French only, `both`, `neither` (short lines, names, dates, figures). A minted line on a German piece whose text reads `la/fr` is an address, a title, a quotation: Latin script, what the Latin-trained model can read. The last two columns are the mean folded length of the machine text the line was aligned on and of the minted slice: a high confidence on a short machine text is the aligner's freedom, not the reader's skill.

| group | minted | mean confidence | de | la/fr | both | neither | machine chars | minted chars |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| German (de, or mixed with de leading) | 40,915 | 0.839 | 27,643 (67.6 %) | 3,178 (7.8 %) | 2,466 (6.0 %) | 7,628 (18.6 %) | 41.0 | 42.3 |
| Latin and French | 252,762 | 0.927 | 914 (0.4 %) | 210,688 (83.4 %) | 2,786 (1.1 %) | 38,374 (15.2 %) | 46.2 | 46.8 |
| other (mixed otherwise, unknown) | 5,734 | 0.899 | 168 (2.9 %) | 3,471 (60.5 %) | 84 (1.5 %) | 2,011 (35.1 %) | 44.7 | 46.0 |

Stratum by stratum (the factory's threshold rises from fair copy to scrap, and the German pieces are mostly drafts):

| stratum | de pieces | de lines | de minted | de yield | de mean conf | la+fr pieces | la+fr lines | la+fr minted | la+fr yield | la+fr mean conf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fair_copy | 4 | 114 | 46 | 40.4 % | 0.723 | 105 | 24,813 | 9,822 | 39.6 % | 0.933 |
| light_revision | 507 | 81,345 | 15,665 | 19.3 % | 0.833 | 2,143 | 342,033 | 78,816 | 23.0 % | 0.916 |
| heavy_revision | 1,124 | 313,296 | 24,983 | 8.0 % | 0.842 | 2,980 | 954,316 | 163,192 | 17.1 % | 0.931 |
| scrap | 31 | 6,639 | 221 | 3.3 % | 0.913 | 43 | 7,370 | 932 | 12.6 % | 0.926 |
| unknown | 507 | 0 | 0 | — | — | 2,423 | 0 | 0 | — | — |

## Pieces by language

| language | cache records | de pieces | de lines | de minted | de yield | de mean conf | la+fr pieces | la+fr lines | la+fr minted | la+fr yield | la+fr mean conf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| la | 3,631 | 3,670 | 2,531 | 2,513 | 10,199 | 714,391 | 139,657 | 19.5 % |
| fr | 3,999 | 4,024 | 2,790 | 2,756 | 10,360 | 614,141 | 113,105 | 18.4 % |
| de | 2,036 | 2,060 | 1,600 | 1,571 | 5,524 | 375,143 | 38,793 | 10.3 % |
| mixed | 331 | 335 | 278 | 271 | 882 | 60,301 | 7,573 | 12.6 % |
| unknown | 32 | 32 | 18 | 18 | 64 | 4,068 | 283 | 7.0 % |

Dominance scores of the pieces classified `de`: quartiles 0.94 / 0.98 / 1.00 (the cut is 0.65; a `mixed` piece has a runner-up at ≥ 0.25).

## By volume

| volume | pieces | la | fr | de | mixed | unknown | de pages | de lines | de minted | de yield | la+fr lines | la+fr minted | la+fr yield | de in Leibniz's hand |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| I,2 | 1 | 0 | 0 | 1 | 0 | 0 | 2 | 50 | 15 | 30.0 % | 0 | 0 | — | 0 |
| I,3 | 675 | 135 | 461 | 42 | 29 | 8 | 102 | 5,085 | 129 | 2.5 % | 73,320 | 10,640 | 14.5 % | 11 |
| I,4 | 3 | 0 | 0 | 3 | 0 | 0 | 4 | 139 | 17 | 12.2 % | 0 | 0 | — | 0 |
| I,5 | 7 | 6 | 0 | 1 | 0 | 0 | 4 | 738 | 0 | 0.0 % | 682 | 103 | 15.1 % | 0 |
| I,6 | 592 | 172 | 290 | 109 | 21 | 0 | 264 | 13,687 | 1,550 | 11.3 % | 56,774 | 12,352 | 21.8 % | 7 |
| I,7 | 607 | 168 | 318 | 104 | 17 | 0 | 216 | 14,184 | 1,598 | 11.3 % | 57,077 | 10,944 | 19.2 % | 25 |
| I,8 | 540 | 139 | 302 | 82 | 15 | 2 | 176 | 11,933 | 857 | 7.2 % | 62,604 | 13,526 | 21.6 % | 3 |
| I,9 | 677 | 254 | 295 | 115 | 13 | 0 | 320 | 18,195 | 1,579 | 8.7 % | 64,809 | 13,594 | 21.0 % | 0 |
| I,10 | 645 | 245 | 271 | 121 | 8 | 0 | 304 | 18,546 | 1,539 | 8.3 % | 54,677 | 12,780 | 23.4 % | 3 |
| I,11 | 747 | 273 | 299 | 147 | 27 | 1 | 398 | 21,346 | 1,895 | 8.9 % | 62,025 | 11,988 | 19.3 % | 0 |
| I,12 | 662 | 242 | 261 | 132 | 26 | 1 | 320 | 15,608 | 1,412 | 9.0 % | 60,626 | 11,921 | 19.7 % | 0 |
| I,14 | 670 | 231 | 354 | 76 | 8 | 1 | 178 | 7,821 | 983 | 12.6 % | 81,675 | 16,850 | 20.6 % | 2 |
| I,15 | 782 | 281 | 317 | 167 | 17 | 0 | 336 | 16,706 | 2,147 | 12.9 % | 72,131 | 12,769 | 17.7 % | 0 |
| I,16 | 676 | 229 | 321 | 104 | 21 | 1 | 278 | 12,897 | 1,770 | 13.7 % | 60,290 | 12,126 | 20.1 % | 3 |
| II,1 | 53 | 26 | 18 | 5 | 4 | 0 | 24 | 1,988 | 209 | 10.5 % | 7,883 | 1,315 | 16.7 % | 0 |
| III,1 | 356 | 209 | 109 | 8 | 17 | 13 | 26 | 1,422 | 135 | 9.5 % | 48,892 | 5,119 | 10.5 % | 0 |
| III,3 | 567 | 93 | 82 | 360 | 31 | 1 | 1,016 | 74,978 | 4,069 | 5.4 % | 36,727 | 4,911 | 13.4 % | 3 |
| III,4 | 424 | 71 | 69 | 266 | 18 | 0 | 636 | 50,165 | 4,343 | 8.7 % | 26,987 | 4,907 | 18.2 % | 2 |
| IV,1 | 153 | 85 | 20 | 41 | 7 | 0 | 352 | 28,932 | 6,142 | 21.2 % | 67,656 | 17,621 | 26.0 % | 2 |
| IV,2 | 154 | 76 | 54 | 21 | 3 | 0 | 72 | 5,864 | 766 | 13.1 % | 13,789 | 3,526 | 25.6 % | 9 |
| IV,3 | 263 | 59 | 54 | 140 | 8 | 2 | 642 | 62,186 | 8,043 | 12.9 % | 53,545 | 13,043 | 24.4 % | 8 |
| VI,1 | 40 | 39 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | — | 13,784 | 2,215 | 16.1 % | 0 |
| VI,3 | 228 | 154 | 36 | 0 | 38 | 0 | 166 | 16,084 | 1,084 | 6.7 % | 84,230 | 11,936 | 14.2 % | 0 |
| VI,4 | 566 | 483 | 60 | 14 | 7 | 2 | 38 | 2,840 | 633 | 22.3 % | 248,861 | 46,330 | 18.6 % | 4 |
| VI,6 | 33 | 0 | 33 | 0 | 0 | 0 | 0 | 0 | 0 | — | 19,488 | 2,246 | 11.5 % | 0 |

## German pieces by stratum and by hand

| stratum | pieces | localizable | with lines | pages | lines | minted | yield |
|---|---:|---:|---:|---:|---:|---:|---:|
| fair_copy | 4 | 4 | 4 | 8 | 114 | 46 | 40.4 % |
| light_revision | 507 | 507 | 506 | 1,948 | 81,345 | 15,665 | 19.3 % |
| heavy_revision | 1,124 | 1,124 | 1,124 | 3,842 | 313,296 | 24,983 | 8.0 % |
| scrap | 31 | 31 | 31 | 76 | 6,639 | 221 | 3.3 % |
| unknown | 507 | 28 | 0 | 0 | 0 | 0 | — |

| hand (Textart) | pieces | localizable | with lines | pages | lines | minted | yield |
|---|---:|---:|---:|---:|---:|---:|---:|
| own | 183 | 131 | 130 | 448 | 34,730 | 2,754 | 7.9 % |
| partial | 542 | 478 | 474 | 1,690 | 103,225 | 10,483 | 10.2 % |
| other | 1,430 | 1,085 | 1,061 | 3,736 | 263,439 | 27,678 | 10.5 % |
| none | 18 | 0 | 0 | 0 | 0 | 0 | — |

German pieces in Leibniz's own hand (`eigh.` on the piece, no sender or Leibniz as sender): **82** with 18,056 recognised lines. *own*: the Textart's `eigh.` qualifies the piece; *partial*: only an address, correction or postscript; *other*: no mark; *none*: no Textart.

## Language by Textart and by hand (all pieces)

| Textart | pieces | la | fr | de | mixed | unknown |
|---|---:|---:|---:|---:|---:|---:|
| Abf. | 1,619 | 561 | 635 | 382 | 39 | 2 |
| Konz., eigh. | 522 | 287 | 186 | 42 | 4 | 3 |
| Konz. | 499 | 219 | 156 | 95 | 29 | 0 |
| Abf., eigh. | 483 | 104 | 289 | 67 | 19 | 4 |
| Abf., eigh. Aufschr., Siegel | 351 | 90 | 122 | 125 | 14 | 0 |
| MF | 317 | 82 | 187 | 43 | 5 | 0 |
| Abf., Bibl.verm. | 210 | 52 | 116 | 42 | 0 | 0 |
| Abf., eigh. Aufschr. | 89 | 29 | 26 | 31 | 3 | 0 |
| Ausz. | 87 | 35 | 44 | 6 | 2 | 0 |
| (none) | 86 | 50 | 17 | 18 | 0 | 1 |
| MF, eigh. | 64 | 21 | 32 | 5 | 6 | 0 |
| Abf., eigh. Aufschr., Siegel, Postverm. | 58 | 20 | 8 | 27 | 3 | 0 |
| Abf., eigh. Aufschr., Siegel, Bibl.verm. | 49 | 16 | 20 | 11 | 2 | 0 |
| Abf., eigh. Aufschr., Siegelrest | 47 | 20 | 13 | 11 | 2 | 1 |
| Abschr. | 44 | 21 | 20 | 2 | 1 | 0 |
| Konz. mit Ändergn | 34 | 6 | 19 | 7 | 2 | 0 |
| Ausz., Murr | 33 | 32 | 0 | 0 | 1 | 0 |
| Ausz., eigh. | 33 | 21 | 9 | 3 | 0 | 0 |
| Abf., eigh. Anschr. | 32 | 1 | 29 | 2 | 0 | 0 |
| Marg., eigh. | 30 | 20 | 9 | 1 | 0 | 0 |

| hand | pieces | la | fr | de | mixed | unknown |
|---|---:|---:|---:|---:|---:|---:|
| own | 1,594 | 659 | 714 | 167 | 41 | 13 |
| partial | 2,038 | 630 | 801 | 526 | 76 | 5 |
| other | 6,403 | 2,331 | 2,492 | 1,349 | 218 | 13 |
| none | 86 | 50 | 17 | 18 | 0 | 1 |
| Leibniz's hand | 1,021 | 556 | 367 | 80 | 13 | 5 |

The factory's Textart rule (`stratum_from_textart`) recognises a document class on 129 of the 10,121 pieces: the catalogue writes `Abf.`, `Konz.`, `Abschr.`, `Ausz.`, `Reinschr.`, which the rule's full-word keys do not match, so the stratum came from the layout statistics alone.

## A look at the classification

The first characters of a few pieces per class (the §70-expired reading text, as the cache holds it), to judge the identifier by eye:

- `de` 1.00 — AA I,9 N.004, katalog 10010 (Reinschr., Korr. von L): “Das project des neüen Wappens oder Insiegels des Churfürstl. Bergamts scheinet an sich selbst gar wohl gefaßet…”
- `de` 0.98 — AA I,9 N.398, katalog 10012 (Abf.; eigh. Aufschr., Siegel, Postverm.: 2gg.): “Ich wil hoffen, dieses werde meinen wehrtesten Gönner bey gesundem wolergehen vorfinden, da Ich in langer zeit…”
- `de` 1.00 — AA I,10 N.161, katalog 10022 (Abf., Schr.; Datum & Unterschr. eigh.): “Euer Excellenz annoch beständiges Wohlergehen versichert mich dero sehr angenehmes unterm 5. dieses, wünsche n…”
- `de` 0.95 — AA I,10 N.367, katalog 10034 (Abf.; eigh. Unterschr.): “Wetzlar d. 1. 7brls 94. Von H. Schiltern restiret noch die antwort und ist der leidige krieg, gleich an viel g…”
- `mixed` 0.53 — AA I,9 N.376, katalog 10109 (Konz. (nur Anrede & Anf.), 15x6,5cm, 3 Zeilen): “(tit) insonders hochg. H. und fürnehmer Gönner Mein jüngstes wird zurecht geliefert worden seyn. Aniezo schrei…”
- `mixed` 0.64 — AA I,10 N.474, katalog 10165 (Abf.; eigh. Aufschr., Siegel): “Vereor, ne justo Dei judicio, hoc Vere idem cum prioribus fatum experiamur, Gallo praeveniente et Heilbrunum, …”
- `mixed` 0.53 — AA I,9 N.376, katalog 10177 (Beginn e.Abf., 11x10,5cm): “(tit) insonders hochg. H. und fürnehmer Gönner Mein jüngstes wird zurecht geliefert worden seyn. Aniezo schrei…”
- `mixed` 0.50 — AA I,9 N.018, katalog 10382 (Abf.; eigh. Aufschr., Siegel): “A Monsieur Monsieur Leibnitz Conseilleur Aulique S. A. Electoral de Brounsvic et Lunebourg etc. à Wolfenbutel …”
- `unknown` 1.00 — AA I,11 N.337, katalog 15667 (Abf.; eigh. Aufschr., Siegelrest): “A Son Excellence Monsr Leibnitz, Conseiller de S. A. S. Electoral de Brunsvic Lynebourg à Hanover franco.…”
- `unknown` 1.00 — AA I,12 N.035, katalog 16991 (Abf.): “contentement (. . .) de Wolfenb. ce 22. Janv. 1696.…”
- `unknown` 0.62 — AA I,14 N.404, katalog 18670 (Abf., Goldschnitt; eigh. Anschr., Bibl.verm.: ad Franconica): “de Conrade, qui t 955? mais de Ludolphe, Duc de Suabe, et ainsy petit fils d’Otton le grand; mes raisons sont:…”
- `unknown` 0.50 — AA I,16 N.066, katalog 22687 (Abf.): “Quittierte Rechnung. Wolfenbüttel, 14. (24.) Februar 1699. [58.67.] 1698 Conto für Monsieur Feiler d. 15ten 9b…”

## What this measures, and what it does not

- The language is the edition text's, piece by piece. A German letter quoting Latin for a third of its length is `de`; a German piece whose cache text carries a bled-in German editorial note stays `de`; a Latin piece with such a note gains German hits and, when short, can read `mixed`. The snippets above are the check.
- Lines are the recognised v1 lines on the piece's canvases, counted the way the factory gathered them; pieces sharing a page share its lines. Minted lines are keyed to the record through the factory's `source` string.
- The hand is the catalogue's word, read by a rule; `partial` and `other` say nothing about who wrote the body, and a letter Leibniz received in its sender's own hand is `own` but not Leibniz's.
