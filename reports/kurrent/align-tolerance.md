# Aligner noise tolerance: how much HTR error the factory survives

1,878 lines of the PHILIUMM validation split in validation order (`reports/philiumm-repro.lines.jsonl`, the B1 reproduction's recorded machine text, CER 7.95 % against the gold), in 76 pieces of 25 consecutive lines; the gold text of each piece, joined with spaces, stands in for the edition's reading text. At each level the machine text is corrupted further (seed 20261009; the model below) until its CER against the gold meets the target, then every piece is aligned by the B2 harness exactly as the factory aligns a piece. A line is **minted** when it clears the factory's gate at the stratum's threshold (confidence ≥ threshold, a non-empty slice, no edition-only burst) and **correct** when its minted slice matches the line's gold at folded similarity ≥ 0.90. Yield is minted ÷ all lines; precision is correct ÷ minted. The confidence is a similarity to the edition text, so the gate that protects precision here is the same one the Kurrent pilot (Task 4) reads as a ground-truth-free measure of a reader.

## The corruption model

Every character of the machine text fires with the level's probability. A fired letter or digit is replaced by a look-alike from the table below (50 %), dropped (15 %: a lost letter or minim), doubled (15 %: a minim too many), merged with the next character where the pair is one a cursive hand runs together (10 %: *in*, *ni*, *rn*, *nn* → *m*; *ii* → *u*; *ri* → *n*; *cl* → *d*; *vv*, *uu* → *w*; *li* → *h*; *ij* → *y*), or split off from its word by a space (10 %). A fired space is a merged word space; a fired accent is dropped; a fired punctuation mark is dropped or swapped. Substitutions are drawn uniformly from the letter's row. The rate is calibrated per level by bisection; the achieved CER is measured on all lines with the B1 scorer's edit distance.

| letter | read as |
|---|---|
| a | o, e, u, n |
| b | h, l, d, p |
| c | e, o, t, r |
| d | a, cl, b, o |
| e | c, o, a, i |
| f | s, l, t |
| g | q, y, s, j |
| h | b, k, li, n |
| i | l, j, t, r, e |
| j | i, g, y |
| k | h, l, b |
| l | i, t, b, f |
| m | n, in, ni, rn, nn |
| n | u, r, m, ri, ii |
| o | a, c, e, u |
| p | q, b, y |
| q | g, p, y |
| r | t, n, c, i |
| s | f, l, r, z, x |
| t | r, l, c, f |
| u | n, v, a, ii |
| v | u, b, r |
| w | vv, uu, m |
| x | z, s, r |
| y | g, j, p, ij |
| z | x, s, y |
| capitals | A → R, N, H; B → R, P, E; C → G, O, E; D → O, Q, P; E → F, B, C; F → E, P, T; G → C, O, Q; H → N, M, K; I → J, L, T; J → I, L, T; K → H, R, X; L → I, T, E; M → N, H, W; N → M, H, A; O → Q, D, C; P → B, R, F; Q → O, G, D; R → B, P, K; S → Z, G, L; T → I, F, L; U → V, W, N; V → U, W, Y; W → V, U, M; X → K, Y, Z; Y → V, X, T; Z → S, X, L |
| digits | 0 → o, O, 6; 1 → l, I, 7; 2 → z, Z, 7; 3 → 5, 8, B; 4 → 9, A, 1; 5 → s, S, 3; 6 → 0, b, G; 7 → 1, T, 2; 8 → 3, B, 0; 9 → 4, g, q |

For comparison, the recorded machine text's own errors against the gold (6,663 edits on 83,773 gold characters) are 39.4 % substitutions, 39.7 % deletions (gold characters the reader lost) and 20.9 % insertions (characters the reader added).

## Achieved error per level

| level | target | rate | operations | CER as written | CER after the aligner's fold | mean confidence | median | lines correct before any threshold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | — | 0.0000 | 0 | **8.0 %** | 6.9 % | 0.948 | 0.980 | 1,819 (96.9 %) |
| cer10 | 10 % | 0.0215 | 1,754 | **10.0 %** | 8.9 % | 0.933 | 0.961 | 1,815 (96.6 %) |
| cer20 | 20 % | 0.1270 | 10,474 | **20.0 %** | 18.6 % | 0.857 | 0.878 | 1,804 (96.1 %) |
| cer30 | 30 % | 0.2354 | 19,496 | **30.0 %** | 28.3 % | 0.777 | 0.789 | 1,786 (95.1 %) |
| cer40 | 40 % | 0.3516 | 28,946 | **40.0 %** | 38.1 % | 0.689 | 0.702 | 1,766 (94.0 %) |
| cer50 | 50 % | 0.4756 | 39,281 | **50.0 %** | 47.9 % | 0.596 | 0.606 | 1,737 (92.5 %) |
| cer60 | 60 % | 0.6074 | 50,110 | **60.0 %** | 57.7 % | 0.500 | 0.500 | 1,666 (88.7 %) |

## Yield at the factory's thresholds

| level | CER | fair_copy (0.55) | light_revision (0.62) | heavy_revision (0.72) | scrap (0.80) | unknown (0.65) |
|---|---:|---:|---:|---:|---:|---:|
| base | 8.0 % | 98.5 % (1,850) | 97.9 % (1,838) | 96.9 % (1,819) | 94.6 % (1,776) | 97.7 % (1,834) |
| cer10 | 10.0 % | 98.4 % (1,848) | 97.7 % (1,835) | 96.4 % (1,810) | 94.1 % (1,768) | 97.6 % (1,832) |
| cer20 | 20.0 % | 97.7 % (1,834) | 96.6 % (1,814) | 93.3 % (1,753) | 84.0 % (1,577) | 95.8 % (1,800) |
| cer30 | 30.0 % | 97.0 % (1,822) | 94.0 % (1,765) | 79.8 % (1,498) | 46.0 % (864) | 92.0 % (1,727) |
| cer40 | 40.0 % | 92.1 % (1,729) | 81.1 % (1,523) | 40.9 % (769) | 11.1 % (208) | 72.6 % (1,363) |
| cer50 | 50.0 % | 73.4 % (1,378) | 42.8 % (804) | 9.3 % (174) | 2.0 % (37) | 30.1 % (566) |
| cer60 | 60.0 % | 30.1 % (566) | 9.1 % (171) | 1.7 % (31) | 0.7 % (13) | 5.4 % (101) |

## Precision of the minted lines at the factory's thresholds

| level | CER | fair_copy (0.55) | light_revision (0.62) | heavy_revision (0.72) | scrap (0.80) | unknown (0.65) |
|---|---:|---:|---:|---:|---:|---:|
| base | 8.0 % | 97.5 % (1,804) | 97.6 % (1,794) | 97.7 % (1,778) | 97.9 % (1,739) | 97.6 % (1,790) |
| cer10 | 10.0 % | 97.3 % (1,798) | 97.4 % (1,787) | 97.6 % (1,766) | 97.7 % (1,727) | 97.4 % (1,784) |
| cer20 | 20.0 % | 96.9 % (1,778) | 97.0 % (1,760) | 97.3 % (1,706) | 97.6 % (1,539) | 97.1 % (1,748) |
| cer30 | 30.0 % | 96.3 % (1,755) | 96.5 % (1,704) | 96.9 % (1,452) | 96.6 % (835) | 96.7 % (1,670) |
| cer40 | 40.0 % | 95.7 % (1,654) | 96.0 % (1,462) | 96.1 % (739) | 94.7 % (197) | 96.0 % (1,308) |
| cer50 | 50.0 % | 95.4 % (1,315) | 94.8 % (762) | 89.1 % (155) | 70.3 % (26) | 94.2 % (533) |
| cer60 | 60.0 % | 91.2 % (516) | 88.3 % (151) | 77.4 % (24) | 61.5 % (8) | 84.2 % (85) |

The best yield any single threshold would give while holding precision at the 95 % gate (a sweep in steps of 0.02; the same for every stratum, since the threshold is the only thing that differs between them):

| level | CER | yield at ≥ 95 % precision | threshold |
|---|---:|---:|---:|
| base | 8.0 % | 99.8 % | 0.00 |
| cer10 | 10.0 % | 99.8 % | 0.00 |
| cer20 | 20.0 % | 99.8 % | 0.00 |
| cer30 | 30.0 % | 99.8 % | 0.00 |
| cer40 | 40.0 % | 97.0 % | 0.44 |
| cer50 | 50.0 % | 81.3 % | 0.52 |
| cer60 | 60.0 % | — | — |

## Break-even

Where yield falls under 50 % and where precision falls under the 95 % gate, per stratum threshold, read along the achieved CER of the levels; the crossing is interpolated linearly between the last level above the floor and the first below it.

| stratum (threshold) | yield < 50 % | precision < 95 % |
|---|---|---|
| fair_copy (0.55) | between 50.0 % and 60.0 % CER, ≈ 55.4 % interpolated | between 50.0 % and 60.0 % CER, ≈ 51.0 % interpolated |
| light_revision (0.62) | between 40.0 % and 50.0 % CER, ≈ 48.1 % interpolated | between 40.0 % and 50.0 % CER, ≈ 48.2 % interpolated |
| heavy_revision (0.72) | between 30.0 % and 40.0 % CER, ≈ 37.7 % interpolated | between 40.0 % and 50.0 % CER, ≈ 41.6 % interpolated |
| scrap (0.80) | between 20.0 % and 30.0 % CER, ≈ 28.9 % interpolated | between 30.0 % and 40.0 % CER, ≈ 38.5 % interpolated |
| unknown (0.65) | between 40.0 % and 50.0 % CER, ≈ 45.3 % interpolated | between 40.0 % and 50.0 % CER, ≈ 45.4 % interpolated |

## What this measures, and what it does not

- The text is Latin and French and the base errors are a Latin-trained reader's; the corruption adds a cursive hand's confusions to it. German lines are longer-worded and a Kurrent reader's errors will have their own shape, but the aligner sees only folded characters, so the character error rate is the quantity that carries over.
- The corruption is spread uniformly over the characters. A real reader's errors cluster on hard lines and hard words: at the same corpus CER, clustered noise leaves more lines clean (kinder to yield) and ruins others wholesale (harsher on the boundaries of their neighbours). The uniform case is the smooth middle, not a bound.
- The reference is the gold itself joined into one text — the diplomatic upper bound. A real edition adds its own divergence on top (B2 measured 3 and 6 %), and pieces the edition omits or interleaves (C2b, P1) are not modelled here.
- The thresholds are the factory's, set for the PHILIUMM model's noise. The sweep table says what a different threshold would buy at each level.
- The model is heavier on substitutions than the recorded errors (50 % of fired letters against 39.4 % of the real edits) and lighter on dropped characters (15 % dropped plus 10 % merged against 39.7 %). A character the reader drops leaves the spine and costs the confidence nothing, where a substituted one counts against it; so at the same CER this noise is the harder case for the gate, and the break-even figures are on the conservative side.
