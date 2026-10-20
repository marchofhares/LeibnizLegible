# The German error rate on the letter-pool test set (K2b Task 3)

**134 letters, 386 pages, 18,815 recognised lines, 325,624 reference characters** — the frozen set of Task 2 (`letterpool-testset.csv`): every letter in Leibniz's hand that placed and a seeded sample of the correspondents' letters, split once into a selection half (67 letters, 7,696 lines) and a test half (67 letters, 11,119 lines). The references are the GWLB Leibniz-Archiv's checked transcriptions (cited below), made from the originals for the edition and selected by no reader; they are CC BY-NC 4.0, nc bucket, so this report carries numbers and letter numbers only.

**The metric.** Each letter's reference text is aligned to the concatenation, in reading order, of every recognised line on its pages — an infix alignment: the reference is consumed whole, the machine text before and after it (an address, an archival note, a neighbour on the leaf) is free, and everything inside the aligned span counts. CER is the edit distance over the reference length, pooled over characters, with a 95 % bootstrap interval over letters (1000 resamples, seed 12345), and as a per-letter distribution. Policies: `philiumm` (NFD, whitespace collapsed; case and diacritics kept — the headline, the B1 harness's), `lenient` (case and diacritics folded), `strict` (NFC; the lines are joined by single spaces on both sides), `reading` (NFC, the long s folded to s, whitespace collapsed — the Kurrent Trace package's policy, as K1 scored Dresden). Nothing is filtered: a line a reader misreads counts whether or not the factory's aligner would have accepted it.

## The readers

| reader | model | device | lines read of 18,815 | ms/line | licence |
|---|---|---|---:|---:|---|
| v1 | v1 | store | 17,399 | — | the store (the C1 run) |
| philiumm | philiumm | cuda | 17,848 | 15 | CC BY 4.0 |
| trocr-kurrent-xvi-xvii | dh-unibe/trocr-kurrent-XVI-XVII | cuda | 18,807 | 340 | MIT |
| trocr-hanse-xvi | fgho/trocr-hanseXVI-kurrent | cuda | 18,815 | 124 | none stated (evaluate only) |
| trocr-hanse-xvii | fgho/trocr-hanseXVII-kurrent | cuda | 18,815 | 352 | none stated (evaluate only) |

`v1` is the stored machine text of the C1 corpus run (what the website shows today); the others read the same lines afresh from the page images through the pilot's crop machinery (the v1 geometry, the polygon masked, no downscaling). A line a reader returned empty counts as deleted.

## CER pooled over characters, 95 % bootstrap interval over letters

| reader | `philiumm`, whole | selection half | test half | `lenient` | `strict` | `reading` |
|---|---:|---:|---:|---:|---:|---:|
| v1 | **46.6 %** (43.3 %–49.5 %) | **44.5 %** (41.4 %–47.6 %) | **48.2 %** (43.1 %–52.4 %) | 45.2 % | 46.8 % | 46.8 % |
| philiumm | **52.9 %** (49.8 %–55.6 %) | **50.5 %** (47.5 %–53.5 %) | **54.6 %** (50.0 %–58.6 %) | 51.6 % | 53.0 % | 53.0 % |
| trocr-kurrent-xvi-xvii | **37.0 %** (32.5 %–41.0 %) | **34.1 %** (29.5 %–38.6 %) | **39.2 %** (32.2 %–44.8 %) | 35.8 % | 37.1 % | 37.0 % |
| trocr-hanse-xvi | **35.6 %** (31.2 %–39.6 %) | **32.3 %** (27.8 %–36.7 %) | **38.0 %** (31.1 %–43.7 %) | 34.4 % | 35.7 % | 35.7 % |
| trocr-hanse-xvii | **38.9 %** (34.6 %–42.8 %) | **35.8 %** (31.3 %–40.1 %) | **41.2 %** (34.6 %–46.6 %) | 37.6 % | 38.9 % | 38.9 % |

## By hand (`philiumm` policy; the `reading` policy in brackets)

| reader | K/k | L |
|---|---:|---:|
| v1 | **38.5 %** (35.9 %–41.9 %) [38.7 %] · 67 letters, 8,059 lines | **53.7 %** (49.9 %–56.9 %) [53.9 %] · 67 letters, 10,756 lines |
| philiumm | **45.5 %** (43.0 %–48.6 %) [45.7 %] · 67 letters, 8,059 lines | **59.3 %** (55.8 %–62.3 %) [59.5 %] · 67 letters, 10,756 lines |
| trocr-kurrent-xvi-xvii | **23.2 %** (19.6 %–27.3 %) [23.2 %] · 67 letters, 8,059 lines | **49.2 %** (44.8 %–52.9 %) [49.1 %] · 67 letters, 10,756 lines |
| trocr-hanse-xvi | **22.8 %** (19.3 %–27.1 %) [22.9 %] · 67 letters, 8,059 lines | **46.7 %** (42.1 %–50.7 %) [46.8 %] · 67 letters, 10,756 lines |
| trocr-hanse-xvii | **26.4 %** (22.7 %–30.8 %) [26.5 %] · 67 letters, 8,059 lines | **49.8 %** (45.3 %–53.5 %) [49.9 %] · 67 letters, 10,756 lines |

*L*: Leibniz's own hand (his drafts and fair copies); *K/k*: the correspondent's hand or the correspondent's scribe's.

## By year (`philiumm` policy)

| reader | 1708 | 1709 | 1710 | 1711 | 1712 | 1713 | 1714 | 1715 | 1716 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 38.8 % (2) | 44.9 % (10) | 38.4 % (3) | 46.2 % (6) | 30.5 % (5) | 44.7 % (48) | 46.5 % (15) | 52.6 % (19) | 46.5 % (26) |
| philiumm | 43.6 % (2) | 51.4 % (10) | 43.8 % (3) | 52.0 % (6) | 40.6 % (5) | 50.7 % (48) | 53.4 % (15) | 58.6 % (19) | 52.7 % (26) |
| trocr-kurrent-xvi-xvii | 24.1 % (2) | 37.4 % (10) | 26.4 % (3) | 35.4 % (6) | 13.8 % (5) | 34.6 % (48) | 34.6 % (15) | 45.3 % (19) | 37.4 % (26) |
| trocr-hanse-xvi | 23.0 % (2) | 33.7 % (10) | 25.7 % (3) | 34.6 % (6) | 13.8 % (5) | 33.2 % (48) | 33.9 % (15) | 43.8 % (19) | 35.6 % (26) |
| trocr-hanse-xvii | 27.7 % (2) | 37.9 % (10) | 28.3 % (3) | 36.9 % (6) | 17.0 % (5) | 36.4 % (48) | 36.2 % (15) | 47.0 % (19) | 39.8 % (26) |

## Per-letter distribution (`philiumm` policy)

| reader | mean | min | Q1 | median | Q3 | max | machine text inside the span |
|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | 45.5 % | 20.8 % | 34.7 % | 42.9 % | 57.9 % | 73.6 % | 68.2 % |
| philiumm | 51.2 % | 23.5 % | 42.7 % | 49.4 % | 62.2 % | 73.5 % | 67.9 % |
| trocr-kurrent-xvi-xvii | 34.7 % | 7.8 % | 17.0 % | 31.5 % | 50.5 % | 72.2 % | 68.3 % |
| trocr-hanse-xvi | 32.8 % | 7.5 % | 17.0 % | 28.3 % | 47.9 % | 71.6 % | 67.8 % |
| trocr-hanse-xvii | 36.2 % | 10.0 % | 20.3 % | 32.8 % | 52.1 % | 71.6 % | 67.9 % |

## Selected: the line-level CER over the lines the factory's aligner accepts

The same readings aligned line by line with `align_piece` at threshold 0.65 (the factory's gate for a piece of unknown stratum); CER over the accepted lines only, the minted slice against the reader's line. This is what an aligner-filtered evaluation reports, and it is flattered by the selection: the aligner keeps the lines the reader already reads well.

| reader | lines | accepted | yield | `philiumm` CER, selected | `reading` CER, selected |
|---|---:|---:|---:|---:|---:|
| v1 | 18,815 | 4,056 | 21.6 % | 28.7 % | 28.9 % |
| philiumm | 18,815 | 2,821 | 15.0 % | 31.9 % | 32.1 % |
| trocr-kurrent-xvi-xvii | 18,815 | 4,993 | 26.5 % | 15.6 % | 15.6 % |
| trocr-hanse-xvi | 18,815 | 5,408 | 28.7 % | 15.5 % | 15.6 % |
| trocr-hanse-xvii | 18,815 | 5,006 | 26.6 % | 18.0 % | 18.0 % |

## What this measures, and what it does not

- The reference is a checked transcription of the letter's own text; the pages carry more (an address, a note, a neighbour) and the infix alignment leaves that uncharged before and after the letter, but anything in the middle — a note the editor set aside, an insertion printed in the apparatus — is charged, as is a supplied letter the editor added in brackets, which the parser keeps (C2b's rule).
- The letters were chosen by no reader and nothing is filtered, so these are the error rates of reading Leibniz's German correspondence of 1708–1716 as it lies on the leaves — not of the lines a factory would mint. K3 reports its model's rate on this set and never tunes on it; the selection half is where a reader may be chosen.
- The `philiumm` policy keeps case and diacritics; the `reading` policy folds the long s, which the Kurrent readers write and the transcription does not.

## Sources

- Transkriptionen des Leibniz-Briefwechsels 1708 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1708-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1709 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1709-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1710 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1710-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1711 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1711-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1712 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1712-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1713 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 3. November 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1713-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1714 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 3. November 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1714-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1715 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1715-v1.pdf`
- Transkriptionen des Leibniz-Briefwechsels 1716 für die Leibniz-Akademie-Ausgabe (überprüft). Version 1. Erfasst von Renate Essi, bearbeitet von Malte-Ludolf Babin, hrsg. von der Leibniz-Forschungsstelle Hannover der Akademie der Wissenschaften zu Göttingen beim Leibniz-Archiv der Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek. Hannover, 28. Oktober 2020. — version 1, `https://www.gwlb.de/fileadmin/Leibniz/repositorium-des-leibniz-archivs/LAA-Transkriptionen1716-v1.pdf`
