# "Next" — the earlier paragraphs (before 2026-10-19)

_Moved verbatim from STATUS.md's "Next" by ARCH2 on 2026-11-19, in the order they had: ARCH1's pointer line and the three older paragraphs it left in place (P1 of 2026-10-08, W3, the A0–C2 block), whose phases have no file under `status/` (their entries are in `STATUS-archive.md`). Frozen: nothing is appended here; what is still open of them is carried by "Next" in `STATUS.md`._

_Paragraphs before 2026-10-19 whose every item is done or superseded (W5 of 2026-10-10; K1, the Kurrent path and the letter-pool choice of 2026-10-09; the final merge, W4 and S1 of 2026-10-08; C2b of 2026-10-07; the W3 fix of 2026-10-06; W2 and W1 of 2026-10-02; Phase D deployable of 2026-09-16) → STATUS-archive.md, "Next (archived)"; the three older paragraphs below (P1, W3, the A0–C2 block) stay, each with an open item._

**P1 (2026-10-08): Task 2 ran on the store** (`9c85f0a`); a later `compare`
rerun adds the coverage section to the report (optional, minutes). Task 3
waits for the new RF-DETR model. Merge order unchanged: after the PHILIUMM
team has seen the numbers. The four runs, for the record:

1. `uv run leibniz align philiumm-vi4 fetch` — the Hub listing and the 735
   noisy PAGE files into `data/philiumm/noisy/` at one request a second
   (about fifteen minutes; resumable: run it again if it stops).
2. `uv run leibniz align philiumm-vi4 match` — read-only on the store;
   prints files matched per split, pairs at IoU 0.3/0.5/0.7 and the layouts
   chosen; writes `reports/philiumm/heldout_pages.csv` and
   `vi4-match-summary.json`. Look at the unresolved list: a shelfmark
   spelling the matcher does not try is a one-line fix here.
3. `uv run leibniz align philiumm-vi4 compare` — writes
   `reports/philiumm/vi4-crosscheck.md`, `vi4-summary.json` and
   `vi4-disagreements-sample.csv`; the full CSVs stay under `data/philiumm/`.
4. `uv run leibniz align philiumm-vi4 sheet --images /mnt/d/leibniz-images`
   — `data/philiumm/philiumm-disagreements.html`, 300 lines with both
   texts, verdicts downloadable in the C2 CSV shape: the second sheet to
   offer the PHILIUMM team.
Then `git add reports/philiumm && git commit && git push`, and paste the
console summaries here. Task 3 waits for the new RF-DETR model. Merge order
unchanged: after the PHILIUMM team has seen the numbers.

**W3 (2026-10-06), operator:** ✅ merged (#38) and live the same day; the
checks below passed. The steps were: merge `web-browse-index`, then the §9 update on
the VPS (`deploy/README.md`) — code only: no index rebuild, no Meilisearch
restart, no new dependency. Then, over HTTP: `/browse` answers 200 and its
HTML holds the family headings, `id="lh-35"` and `/work/` links; `/api/works`
answers 200 JSON with `groups`; `/robots.txt` has the line `Allow:
/api/works`; `/sitemap.xml` lists `/browse`; `/llms.txt` mentions `/browse`;
and the three W1/W2 checks still pass (a page's `/text` starts with `# `, the
search page says "for an exact phrase", `style.css` hides the overlay by
`visibility`). In a private window: the nav link, EN and DE, the filter, the
order toggle of the letters, `/browse#lh-35`, a work page's breadcrumb.
(Returning readers were expected to see the old modules for up to an hour;
they saw a broken mix instead — the W3 fix.) Still open: the reply
to the reader at the Leibniz-Edition: the index is there; does the grouping
match how the Arbeitsstellen think of the Faszikel (Open questions #22); and
the two standing asks — a TELOTA contact for an Arbeitskatalog export, which
would name the remaining letter convolutes, and CC BY or written permission
for the Reihe VIII reading text (both answered 2026-10-12: an export is
offered, the text is CC BY-NC 4.0; the L1 note at the top of Next). Next
phase: K1, from a fresh session on the merged main.

**A0–A3 + B1–B2 + C1 (machinery *and* corpus run) + C2 (machinery *and* mint) all green; C2's precision gate is deferred to C3's ablation (audit preliminary).**
Per SPECS §5 sequencing, C is sequential: **C2 minting, then C3**, then C4 and
the D phases.

- **C2 — closed on the mint; the precision gate rides with C3.** 297,424
  lines minted; the hand audit is preliminary (20/200, Q #18) and stays
  open in `reports/gt-audit/` for a reader of the hands. The C3 ablation
  (PHILIUMM GT alone vs + C2 GT) is the empirical test of the minted GT; if
  it shows no gain, come back to Q #18 / Q #17 and the per-stratum
  thresholds before spending on labels. Optional clean-label upgrade:
  vision re-extraction of the minted pieces' pages (priced in the report;
  low three figures at most).
- **Phase C3 — Fine-tune v2 + per-stratum eval (gate).** Train `leibniz-htr-v2`
  from the PHILIUMM checkpoint on PHILIUMM GT + the C2 open-bucket GT
  (+ ablations). Hold out a page-disjoint test set stratified by stratum +
  language; evaluate with the B1 harness. Gate: **CER ≤7% on la/fr**.
- **Operator (SPECS §8), now higher-value than ever:** a **TELOTA katalog
  dump** would complete the scrape *and* supply the §70 anchors in one move —
  and with the corpus read, emailing PHILIUMM (Rabouin/Bumba) the B1/B2/C1
  results carries real weight: their models just machine-read the entire
  Nachlass. Report the 16 redirect-loop delivery URLs to GWLB while at it.

No code or data blockers for C2 minting; the only dependency is the corpus store's location.
