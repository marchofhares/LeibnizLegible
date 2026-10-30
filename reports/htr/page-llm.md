# Frontier vision models on whole pages, against the project's readers (LT1)

Generated 2026-10-30. The fair protocol a colleague proposed, adopted: whole pages, one page a call, the frontier models' answers scored with the same metric and policy as the project's line readers (B1's `philiumm` normalisation, K2b's letter-pool metric), so one number stands against another. The B1 numbers of September used line crops, which favour a line recogniser; this is the page-level test.

## The protocol

- One prompt for every model (SHA-256 prefix `a9604646c4b3dd78`): “Transcribe every line of this manuscript page in reading order, one output line per manuscript line, character by character: exactly the characters written, with the original spelling, abbreviations, accents and punctuation. No commentary, no translation, no expansion of abbreviations, no headings or notes of your own — output the transcription and nothing else.”
- The page image downscaled to a long side of 2000 px (JPEG, quality 92), a half at a time where the page list names a column (the PHILIUMM openings — two folios on one scan — are read as left and right); the sizes sent and the APIs' own token counts are in the readings.
- Temperature 0 where the API takes it; `max_tokens` 4000; reasoning off or at the lowest setting the API allows — the setting per model in the table below. A refusal, an empty answer or a runaway (the output cap reached) is recorded, retried once, and scored both ways: charged as 100 % error, and left out.
- Only page images went to an API, and only the GWLB's public-domain scans (the pool's pages from the project's image cache; PHILIUMM's val pages from the dataset's Hub repository, CC BY 4.0). The pool's reference texts (CC BY-NC 4.0) never left the machine; no API output is a training label.

## The models and their settings

| model | engine | reasoning | temperature | max_tokens | pages | calls | input tokens a page | output tokens a page | cost | seconds a page |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| claude-fable-5-1 | anthropic | effort low | not sent | 4000 | 132 | 135 | 3,783 | 975 | 11.43 USD | 13.3 |
| gemini-3.1-pro-preview | gemini | thinking_level low (no off on this model family) | 0.0 | 4000 | 132 | 138 | 1,204 | 700 | 1.43 USD | 14.3 |
| gemini-4-argon | gemini | thinking_level low (no off on this model family) | 0.0 | 4000 | 132 | 140 | 1,254 | 552 | 1.06 USD | 13.4 |

Output tokens include the thinking the APIs bill as output (Claude's thinking cannot be switched off on the current models and Gemini 3.x Pro and 4 Argon have no “off”, so *low* is the floor on both). The cost is the logged usage at the pricing tables in `htr/engines.py` (list rates on the day of the run, estimates).

## PHILIUMM's held-out pages (Latin and French)

The dataset's `val` split — 27 pages (34 calls: an opening is two) carrying 1,878 reference lines and 85,617 reference characters under the headline policy. The reference of a page is the dataset's own PAGE XML for that scan, its lines in document order (the parquet the model was scored on in B1 carries text and image only, no page; the page is rebuilt from the XML the Hub publishes beside each scan). The dataset has no `test` split: `val` is its held-out split, the one B1 reproduced the model's CER on.

Page CER: the edit distance between the page's reference and the model's answer, both as one string of lines joined by spaces, over the reference's length; pooled over pages (Σ edits ÷ Σ reference characters), 95 % bootstrap interval over pages (1,000 resamples, seed 12345), the per-page distribution beside it.

| reader | `philiumm`, failed pages charged | failed pages left out | failed | `lenient` | `strict` | `reading` | per-page median | per-page max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-fable-5-1 | **22.5 %** (18.0 %–27.5 %) | **22.5 %** (18.0 %–27.5 %) | 0 of 34 | 22.1 % | 22.5 % | 22.5 % | 19.9 % | 178.0 % |
| gemini-3.1-pro-preview | **27.2 %** (20.5 %–35.4 %) | **24.5 %** (19.3 %–30.0 %) | 1 of 34 | 26.7 % | 27.2 % | 27.2 % | 18.5 % | 226.5 % |
| gemini-4-argon | **33.6 %** (20.5 %–51.6 %) | **30.7 %** (19.6 %–49.1 %) | 1 of 34 | 32.9 % | 33.5 % | 33.5 % | 17.0 % | 229.2 % |

The PHILIUMM kraken model's row is missing: no line dump of the val pages was given (`bench page-lines`, then `bench run … --engine kraken --out`, then `page-score --kraken-lines`). B1's per-line dump carries parquet row ids, which name no page, so it cannot stand in.

For scale, B1's line-crop numbers (150 lines, zero-shot, September 2026):

| engine (B1, line crops) | CER |
|---|---:|
| Kraken (PHILIUMM, fine-tuned) | 8.19 % |
| gpt-4.1 | 36.60 % |
| gpt-4o | 43.82 % |
| gemini-3.8-flash | 55.11 % |
| gpt-5.6-sol | 74.17 % |
| gpt-5.6-luna | 76.24 % |
| gpt-5.6-terra | 78.66 % |

## The GWLB letter pool (German, Kurrent)

34 letters, 98 pages of K2b's frozen set, drawn seeded (seed 20261028) whole letters at a time: 48 pages in Leibniz's hand and 50 in the correspondents', 18 letters of the selection half and 16 of the test half; 5,276 recognised lines, 82,881 reference characters. The metric is K2b's: each letter's reference aligned to the concatenation of everything read on its pages — for a page model, the page texts in order — an infix alignment, the reference consumed whole, machine text before and after it free; CER pooled over characters, 95 % bootstrap interval over letters. The readers of K2b and K3 are scored on the same letters from their readings on disk; their whole-set numbers (134 letters) stand in the last column as the committed reports carry them.

| reader | these letters, `philiumm` | selection half | test half | Leibniz's hand (L) | the correspondents' (K/k) | `reading` policy | whole set (134 letters, K2b / K3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| k3-kraken | **29.5 %** (23.8 %–34.8 %) | **25.8 %** (19.6 %–32.5 %) | **33.8 %** (25.3 %–41.7 %) | **37.0 %** (29.5 %–45.0 %) | **20.5 %** (15.1 %–26.5 %) | 29.5 % | **30.6 %** (26.5 %–34.5 %) |
| k3-trocr | **26.9 %** (21.9 %–31.9 %) | **24.4 %** (18.1 %–31.1 %) | **29.7 %** (23.2 %–36.3 %) | **33.4 %** (27.0 %–41.2 %) | **19.0 %** (13.5 %–25.2 %) | 26.9 % | **28.6 %** (24.6 %–32.5 %) |
| page:claude-fable-5-1 | **26.4 %** (18.8 %–33.8 %) | **21.3 %** (14.9 %–29.1 %) | **32.3 %** (20.4 %–42.2 %) | **33.9 %** (23.1 %–45.3 %) | **17.4 %** (9.0 %–24.6 %) | 26.4 % | — |
| page:gemini-3.1-pro-preview | **25.8 %** (18.1 %–34.6 %) | **20.4 %** (14.5 %–27.4 %) | **32.2 %** (18.2 %–47.3 %) | **35.8 %** (24.2 %–48.4 %) | **13.8 %** (7.9 %–20.4 %) | 25.8 % | — |
| page:gemini-4-argon | **24.2 %** (17.3 %–31.5 %) | **23.4 %** (14.3 %–33.0 %) | **25.1 %** (16.3 %–33.1 %) | **33.3 %** (24.2 %–42.6 %) | **13.2 %** (7.5 %–19.4 %) | 23.8 % | — |
| trocr-kurrent-xvi-xvii | **35.0 %** (29.0 %–40.8 %) | **32.1 %** (25.4 %–39.7 %) | **38.4 %** (29.1 %–47.3 %) | **45.1 %** (37.7 %–53.6 %) | **22.8 %** (17.6 %–28.3 %) | 35.0 % | **37.0 %** (32.5 %–41.0 %) |
| v1 | **43.9 %** (39.4 %–48.4 %) | **41.1 %** (36.1 %–46.5 %) | **47.3 %** (40.7 %–54.1 %) | **49.7 %** (44.1 %–56.3 %) | **36.9 %** (32.4 %–42.0 %) | 44.1 % | **46.6 %** (43.3 %–49.5 %) |

**Failed pages left out.** 30 of the 34 letters have every page read by every page model; on those letters alone:

| reader | `philiumm` | Leibniz's hand (L) | the correspondents' (K/k) |
|---|---:|---:|---:|
| k3-kraken | **27.8 %** (22.3 %–33.8 %) | **37.0 %** (27.4 %–48.1 %) | **20.5 %** (15.1 %–26.5 %) |
| k3-trocr | **25.7 %** (20.5 %–31.4 %) | **34.1 %** (25.3 %–44.7 %) | **19.0 %** (13.5 %–25.2 %) |
| page:claude-fable-5-1 | **24.4 %** (17.4 %–31.3 %) | **33.3 %** (23.5 %–46.2 %) | **17.4 %** (9.0 %–24.6 %) |
| page:gemini-3.1-pro-preview | **21.7 %** (16.3 %–27.9 %) | **31.7 %** (23.3 %–43.1 %) | **13.8 %** (7.9 %–20.4 %) |
| page:gemini-4-argon | **19.5 %** (14.5 %–24.9 %) | **27.4 %** (19.6 %–36.8 %) | **13.2 %** (7.5 %–19.4 %) |
| trocr-kurrent-xvi-xvii | **33.1 %** (27.2 %–40.3 %) | **46.2 %** (35.5 %–58.0 %) | **22.8 %** (17.6 %–28.3 %) |
| v1 | **43.2 %** (39.1 %–48.2 %) | **51.2 %** (44.9 %–60.7 %) | **36.9 %** (32.4 %–42.0 %) |

## Refusals, empty answers, runaways

| model | set | pages | ok | refused | empty | runaway | error | retried | ok on the second attempt |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-fable-5-1 | philiumm | 34 | 34 | 0 | 0 | 0 | 0 | 2 | 2 |
| gemini-3.1-pro-preview | philiumm | 34 | 33 | 0 | 0 | 1 | 0 | 1 | 0 |
| gemini-4-argon | philiumm | 34 | 33 | 0 | 1 | 0 | 0 | 3 | 2 |
| claude-fable-5-1 | pool | 98 | 98 | 0 | 0 | 0 | 0 | 1 | 1 |
| gemini-3.1-pro-preview | pool | 98 | 94 | 0 | 2 | 2 | 0 | 5 | 1 |
| gemini-4-argon | pool | 98 | 97 | 0 | 1 | 0 | 0 | 5 | 4 |

A page whose final status is not ok is charged as 100 % error in the first column of each table and left out in the second (the pool: the letter it belongs to is left out).

## The line diff: where exactly one reader is right

Each page model's lines and the line reader's lines are aligned to the same reference lines (a Needleman–Wunsch over lines: a pair costs its normalised edit distance, a gap 0.35, so two lines under 30 % similar are not paired), under the headline policy. *Right* is an exact line; *near* within 10% CER. *Invented*: the reader's lines matched to no reference line; *dropped*: reference lines the reader has no line for. On PHILIUMM's pages the reference lines are the dataset's; on the pool the factory's aligner cuts the letter's text into the line reader's lines (the lines it accepts at its gate), so the pool diff is measured on those lines only and the page model's lines are aligned to them.

| set | page model (a) | line reader (b) | ref lines | a lines | b lines | both right | only a right | only b right | both wrong | a near | b near | a invented | a dropped | b invented | b dropped | a length ratio | b length ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pool | page:claude-fable-5-1 | k3-trocr | 1,664 | 3,509 | 1,664 | 97 | 175 | 266 | 1,126 | 849 | 1,068 | 2,119 | 274 | 24 | 24 | 2.20 | 0.98 |
| pool | page:gemini-3.1-pro-preview | k3-trocr | 1,664 | 3,394 | 1,664 | 76 | 134 | 287 | 1,167 | 779 | 1,068 | 2,073 | 343 | 24 | 24 | 2.12 | 0.98 |
| pool | page:gemini-4-argon | k3-trocr | 1,664 | 3,555 | 1,664 | 72 | 118 | 291 | 1,183 | 828 | 1,068 | 2,205 | 314 | 24 | 24 | 2.28 | 0.98 |

## What this measures, and what it does not

- **The page sets are small.** PHILIUMM's held-out split is 27 pages and the pool draw 98 pages of 34 letters; the intervals are wide, and a few refused or runaway pages move a model's number by points. The numbers are the first page-level ones, not the last.
- **The pool's references are the GWLB's checked transcriptions of letters**, made for the edition, not a random sample of the Nachlass's German pages: letters of 1708–1716, half of them in Leibniz's own hand by construction. The German number is the error rate on that material, as K2b's and K3's are.
- The page models never saw the project's line segmentation; the line readers never saw the whole page. Where the diff shows invented and dropped lines, the page model's reading order and its line count are part of what is measured, as the colleague's protocol intends.
- Reasoning could not be switched off on Claude or on Gemini 3.x Pro and 4 Argon; *low* is the floor, named per model above, and the thinking tokens are in the output count and the cost.
