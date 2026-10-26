# The German error rate on the letter-pool test set (K2b Task 3)

**134 letters, 386 pages, 18,815 recognised lines, 325,624 reference characters** — the frozen set of Task 2 (`letterpool-testset.csv`): every letter in Leibniz's hand that placed and a seeded sample of the correspondents' letters, split once into a selection half (67 letters, 7,696 lines) and a test half (67 letters, 11,119 lines). The references are the GWLB Leibniz-Archiv's checked transcriptions (cited below), made from the originals for the edition and selected by no reader; they are CC BY-NC 4.0, nc bucket, so this report carries numbers and letter numbers only.

**The metric.** Each letter's reference text is aligned to the concatenation, in reading order, of every recognised line on its pages — an infix alignment: the reference is consumed whole, the machine text before and after it (an address, an archival note, a neighbour on the leaf) is free, and everything inside the aligned span counts. CER is the edit distance over the reference length, pooled over characters, with a 95 % bootstrap interval over letters (1000 resamples, seed 12345), and as a per-letter distribution. Policies: `philiumm` (NFD, whitespace collapsed; case and diacritics kept — the headline, the B1 harness's), `lenient` (case and diacritics folded), `strict` (NFC; the lines are joined by single spaces on both sides), `reading` (NFC, the long s folded to s, whitespace collapsed — the Kurrent Trace package's policy, as K1 scored Dresden). Nothing is filtered: a line a reader misreads counts whether or not the factory's aligner would have accepted it.

## The readers

| reader | model | device | lines read of 18,815 | ms/line | licence |
|---|---|---|---:|---:|---|
| v1 | v1 | store | 17,399 | — | the store (the C1 run) |
| k3-trocr | data/models/k3/trocr/best | cuda | 18,814 | 105 | MIT (the base) · the fine-tune open |
| k3-kraken | k3-kraken | cuda | 14,874 | 11 | CC BY 4.0 (the base) · the fine-tune open |

`v1` is the stored machine text of the C1 corpus run (what the website shows today); the others read the same lines afresh from the page images through the pilot's crop machinery (the v1 geometry, the polygon masked, no downscaling). A line a reader returned empty counts as deleted.

## CER pooled over characters, 95 % bootstrap interval over letters

| reader | `philiumm`, whole | selection half | test half | `lenient` | `strict` | `reading` |
|---|---:|---:|---:|---:|---:|---:|
| v1 | **46.6 %** (43.3 %–49.5 %) | **44.5 %** (41.4 %–47.6 %) | **48.2 %** (43.1 %–52.4 %) | 45.2 % | 46.8 % | 46.8 % |
| k3-trocr | **28.6 %** (24.6 %–32.5 %) | **24.7 %** (21.0 %–28.3 %) | **31.6 %** (25.3 %–36.8 %) | 27.6 % | 28.6 % | 28.6 % |
| k3-kraken | **30.6 %** (26.5 %–34.5 %) | **26.6 %** (23.0 %–30.4 %) | **33.6 %** (27.0 %–38.9 %) | 29.6 % | 30.7 % | 30.7 % |

## By hand (`philiumm` policy; the `reading` policy in brackets)

| reader | K/k | L |
|---|---:|---:|
| v1 | **38.5 %** (35.9 %–41.9 %) [38.7 %] · 67 letters, 8,059 lines | **53.7 %** (49.9 %–56.9 %) [53.9 %] · 67 letters, 10,756 lines |
| k3-trocr | **19.4 %** (15.7 %–23.8 %) [19.4 %] · 67 letters, 8,059 lines | **36.7 %** (31.9 %–41.0 %) [36.7 %] · 67 letters, 10,756 lines |
| k3-kraken | **20.3 %** (16.8 %–24.6 %) [20.4 %] · 67 letters, 8,059 lines | **39.7 %** (34.7 %–43.9 %) [39.7 %] · 67 letters, 10,756 lines |

*L*: Leibniz's own hand (his drafts and fair copies); *K/k*: the correspondent's hand or the correspondent's scribe's.

## By year (`philiumm` policy)

| reader | 1708 | 1709 | 1710 | 1711 | 1712 | 1713 | 1714 | 1715 | 1716 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 38.8 % (2) | 44.9 % (10) | 38.4 % (3) | 46.2 % (6) | 30.5 % (5) | 44.7 % (48) | 46.5 % (15) | 52.6 % (19) | 46.5 % (26) |
| k3-trocr | 19.5 % (2) | 27.4 % (10) | 21.2 % (3) | 32.1 % (6) | 11.3 % (5) | 25.1 % (48) | 29.5 % (15) | 35.4 % (19) | 28.3 % (26) |
| k3-kraken | 22.5 % (2) | 31.2 % (10) | 22.2 % (3) | 33.2 % (6) | 15.5 % (5) | 26.6 % (48) | 30.8 % (15) | 38.1 % (19) | 30.3 % (26) |

## Per-letter distribution (`philiumm` policy)

| reader | mean | min | Q1 | median | Q3 | max | machine text inside the span |
|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | 45.5 % | 20.8 % | 34.7 % | 42.9 % | 57.9 % | 73.6 % | 68.2 % |
| k3-trocr | 25.5 % | 5.4 % | 12.8 % | 21.2 % | 34.8 % | 70.6 % | 69.1 % |
| k3-kraken | 27.6 % | 5.1 % | 14.7 % | 23.0 % | 39.2 % | 72.0 % | 70.9 % |

## Selected: the line-level CER over the lines the factory's aligner accepts

The same readings aligned line by line with `align_piece` at threshold 0.65 (the factory's gate for a piece of unknown stratum); CER over the accepted lines only, the minted slice against the reader's line. This is what an aligner-filtered evaluation reports, and it is flattered by the selection: the aligner keeps the lines the reader already reads well.

| reader | lines | accepted | yield | `philiumm` CER, selected | `reading` CER, selected |
|---|---:|---:|---:|---:|---:|
| v1 | 18,815 | 4,056 | 21.6 % | 28.7 % | 28.9 % |
| k3-trocr | 18,815 | 6,295 | 33.5 % | 10.3 % | 10.3 % |
| k3-kraken | 18,815 | 5,738 | 30.5 % | 14.6 % | 14.7 % |

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
