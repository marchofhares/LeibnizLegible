# GT hand audit — C2 precision gate

Verdicts from `gt-audit-verdicts-philiumm.csv` (200 sheet lines); stratum weights from the C2 mint of 2026-09-16 (STATUS.md C2 log; reports/gt-factory.md) (fair_copy 9,913, light_revision 96,175, heavy_revision 190,162, scrap 1,174).

**200 lines on the sheet · 199 judged · 1 left blank · 14 unreadable.**

**Corpus-weighted precision: 72.3 %** (strata weighted by their share of minted lines) — gate ≥ 95 %: **FAIL**.

| stratum | judged | correct | boundary | wrong | precision | 95 % CI | usable | weight |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| fair_copy | 50 | 42 | 2 | 6 | 84.0 % | 71–92 % | 88.0 % | 3.3 % |
| light_revision | 45 | 39 | 5 | 1 | 86.7 % | 74–94 % | 97.8 % | 32.3 % |
| heavy_revision | 48 | 31 | 12 | 5 | 64.6 % | 50–77 % | 89.6 % | 63.9 % |
| scrap | 42 | 24 | 14 | 4 | 57.1 % | 42–71 % | 90.5 % | 0.4 % |
| **pooled (unweighted)** | 185 | 136 | 33 | 16 | 73.5 % | 67–79 % | 91.4 % | |

*precision* = correct ÷ (correct + boundary + wrong); *usable* also counts boundary-off lines (the right line, a word or more off at an end). Intervals are Wilson 95 %. Equal numbers were drawn per stratum, so the pooled row over-represents the rare strata; the weighted figure is the one to read.

Per stratum against the same gate: fair_copy FAIL (84.0 %); light_revision FAIL (86.7 %); heavy_revision FAIL (64.6 %); scrap FAIL (57.1 %). Counting boundary-off lines as usable, the corpus-weighted figure is **92.2 %**.

## Second witness: the machine reading

For every judged line the folded similarity between the minted text and the HTR reading of the same strip was computed. 43 of the 63 non-*correct* verdicts sit on lines where the two agree at ≥ 0.8, i.e. the machine read the same words the edition gives; **9 verdicts are listed for re-checking.** The machine reading is not ground truth, but it is an independent reader of the strip, and a *wrong* it contradicts this strongly is more often a misjudged verdict than a misaligned line.

| # | ref | stratum | verdict | agreement | minted text | HTR reading | why re-check |
|---|---|---|---|---:|---|---|---|
| 1 | `00068377:0548:015` | fair_copy | wrong | 0.86 | veüe, à droitfe] ny à gauche, mais avec toutte | verie, adroit ny a gaucme, mais avec toutte | machine reading agrees at 0.86: likely the same line |
| 2 | `DE-611-HS-974894:0325:013` | fair_copy | wrong | 0.98 | environs de Casai et de Pignerol, et faire | environs de Casal et de Pignerol, et faire | machine reading agrees at 0.98: likely the same line |
| 3 | `DE-611-HS-974894:0296:008` | fair_copy | wrong | 0.95 | que Vous aurez veu. Il allégué plusieurs mots | que vous aurer veu. Il alleque plusieurs mots | machine reading agrees at 0.95: likely the same line |
| 4 | `00068377:1383:023` | fair_copy | wrong | 0.82 | tout d’un coup, et [l’jon ne revient pas aussi | tout dun eoup, et on ne reuient pas eus | machine reading agrees at 0.82: likely the same line |
| 5 | `00068285:0194:004` | fair_copy | wrong | 0.91 | salubriter Ecclesiae provideatur. | Salubriter Ecolesiae pracuideatur. | machine reading agrees at 0.91: likely the same line |
| 6 | `00068285:0256:015` | fair_copy | wrong | 0.92 | indulgentiam recipere, ut quando eandem | in dulgentiam reripere et quando eandem | machine reading agrees at 0.92: likely the same line |
| 7 | `00068377:1121:043` | heavy_revision | wrong | 0.89 | vous entretenir. Et je vous envoyé maintenant | levus entreteurr Et je vous envoye maintenant | machine reading agrees at 0.89: likely the same line |
| 8 | `00068377:0280:017` | heavy_revision | wrong | 0.91 | dans un arrest, sans qu’on puisse alléguer contre celuy qui allégué | dans un arroit sans qu’on puisse allequor contre celuy qui allequo | machine reading agrees at 0.91: likely the same line |
| 9 | `DE-611-HS-860722:0087:064` | scrap | wrong | 0.89 | tc., ut patebit substituendo in allatam regulam | rc; ut palebit substituendo. in allatâ Regla | machine reading agrees at 0.89: likely the same line |

## Agreement: PHILIUMM (2026-10-07) vs the operator's preliminary pass (2026-09-16)

On the 20 lines both judged, the verdicts agree on 11 (55 %).

| PHILIUMM (2026-10-07) ↓ · the operator's preliminary pass (2026-09-16) → | correct | boundary | wrong | unreadable |
|---|---:|---:|---:|---:|
| correct | 10 | 0 | 4 | 3 |
| wrong | 2 | 0 | 1 | 0 |

Lines where they differ:

| ref | stratum | PHILIUMM (2026-10-07) | the operator's preliminary pass (2026-09-16) |
|---|---|---|---|
| `DE-611-HS-862260:0064:004` | fair_copy | correct | wrong |
| `DE-611-HS-860628:0257:012` | fair_copy | correct | wrong |
| `00068369:0660:003` | fair_copy | correct | unreadable |
| `DE-611-HS-974894:0325:013` | fair_copy | wrong | correct |
| `DE-611-HS-974894:0243:031` | fair_copy | correct | wrong |
| `00068377:1270:027` | fair_copy | correct | wrong |
| `DE-611-HS-974894:0296:008` | fair_copy | wrong | correct |
| `00068377:0959:022` | fair_copy | correct | unreadable |
| `00068377:0963:001` | fair_copy | correct | unreadable |

## Patterns: why a minted line is not the line's text

One pattern per judged line, from the verdict, the note (85 lines carry one), the minted text and the HTR reading, by the rules listed below (3 settled by the override file). Counts are lines; the share is of the stratum's judged lines.

| stratum | judged | hyphen | boundary-letter | math | addition | bracket | normalization | reading | unreadable | correct | other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fair_copy | 50 | 6 (12 %) | 2 (4 %) | 0 | 0 | 2 (4 %) | 9 (18 %) | 4 (8 %) | 0 | 27 (54 %) | 0 |
| light_revision | 49 | 4 (8 %) | 6 (12 %) | 0 | 0 | 1 (2 %) | 4 (8 %) | 0 | 4 (8 %) | 29 (59 %) | 1 (2 %) |
| heavy_revision | 50 | 2 (4 %) | 11 (22 %) | 2 (4 %) | 1 (2 %) | 3 (6 %) | 3 (6 %) | 0 | 2 (4 %) | 26 (52 %) | 0 |
| scrap | 50 | 1 (2 %) | 16 (32 %) | 3 (6 %) | 1 (2 %) | 1 (2 %) | 0 | 0 | 8 (16 %) | 20 (40 %) | 0 |
| **all** | 199 | 13 (7 %) | 35 (18 %) | 5 (3 %) | 2 (1 %) | 7 (4 %) | 16 (8 %) | 4 (2 %) | 14 (7 %) | 102 (51 %) | 1 (1 %) |

By verdict (what the auditors called the line, and what the pattern says it is):

| verdict | n | hyphen | boundary-letter | math | addition | bracket | normalization | reading | unreadable | correct | other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| correct | 136 | 13 | 4 | 0 | 0 | 3 | 13 | 1 | 0 | 102 | 0 |
| boundary | 33 | 0 | 31 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| wrong | 16 | 0 | 0 | 5 | 2 | 2 | 3 | 3 | 0 | 0 | 1 |
| unreadable | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 0 | 0 |

**Hyphens.** 14 judged lines carry a hyphen signal (13 named *hyphen*, the rest *boundary* lines where the boundary comes first): on 6 the HTR line ends in a hyphen mark the mint dropped (what `keep_hyphen` restores), on 8 the note says the hyphen is on the page but the HTR did not read it either — those the fix cannot reach, since it keeps only what the HTR showed.

Rules, in order of precedence (the first that fires names the line; every rule that fired is in the per-line CSV):

1. *unreadable* — the verdict, or the note says the auditors could not read it.
2. *addition* — the note names an addition (keywords: addition, ajout, not visually on the same line, separate line, interlin, marginal, en marge), or on a *wrong* verdict the minted text exceeds the HTR reading by more than 12 folded characters.
3. *math* — the note names a formula (keywords: math, formul, equation, cartesian, algebra), or at least 2 mathematical operators or Greek letters make ≥ 10 % of the minted text's non-space characters, or with digits ≥ 25 %. The density misses inline algebra in prose (`ia yy x 2ax —` is 4 %); the note catches those.
4. *bracket* — the minted text carries an editorial bracket (`[` or `]`).
5. *hyphen* — the HTR line ends in a hyphen mark and the minted text in a letter, or the note names a missing hyphen; on *correct* verdicts (a *boundary* line is named by its boundary, a *wrong* one by its cause).
6. *boundary-letter* — a *boundary* verdict, or a correction in the note that differs from the minted text by at most 3 characters at one end.
7. *reading* — a correction in the middle of the line whose folded similarity to the minted word is ≥ 0.5 at a length ratio ≥ 0.6: the same word read differently.
8. *normalization* — the note objects to an accent, capital, comma, apostrophe or spelling the edition regularises, a correction folds to the same word as the minted one, or the edit is a punctuation mark.
9. *correct* — a *correct* verdict with nothing else to say. 10. *other* — no rule fired.

## Corrections in the notes: the normalization tax, first sample

46 notes spell out an edit to the minted text; on 45 the edit could be placed and the corrected line compared with the minted one. The table gives the mean character distance minted → corrected per pattern, as written (accents and case kept) and under the aligner's fold; the gap between the two columns is what the fold hides and a diplomatic scorer charges: accents, capitals, punctuation. On the *normalization* lines the folded distance is near zero by construction — that row is the tax itself. These are the auditors' word-level corrections, not full re-transcriptions, so every figure is a floor.

| pattern | lines placed | mean distance, as written | mean distance, folded |
|---|---:|---:|---:|
| boundary-letter | 29 | 8.6 % | 7.9 % |
| math | 2 | 6.7 % | 3.5 % |
| addition | 1 | 32.1 % | 32.7 % |
| bracket | 4 | 8.0 % | 6.3 % |
| normalization | 3 | 3.1 % | 0.0 % |
| reading | 4 | 3.3 % | 3.4 % |
| correct | 1 | 5.4 % | 5.6 % |
| other | 1 | 66.7 % | 44.4 % |
| **all** | 45 | 9.4 % | 7.9 % |

| ref | stratum | verdict | pattern | minted text | edits | corrected text | raw | folded |
|---|---|---|---|---|---|---|---:|---:|
| `00068377:0548:015` | fair_copy | wrong | bracket | veüe, à droitfe] ny à gauche, mais avec toutte | 'à droitfe' → 'àdroit' | veüe, àdroit] ny à gauche, mais avec toutte | 0.91 | 0.93 |
| `DE-611-HS-974894:0325:013` | fair_copy | wrong | reading | environs de Casai et de Pignerol, et faire | 'Casai' → 'Casal' | environs de Casal et de Pignerol, et faire | 0.98 | 0.98 |
| `DE-611-HS-974894:0243:031` | fair_copy | correct | reading | but, qu’il seroit trop long de rapporter icy. | 'icy' → 'ici' | but, qu’il seroit trop long de rapporter ici. | 0.98 | 0.98 |
| `00068377:1383:023` | fair_copy | wrong | bracket | tout d’un coup, et [l’jon ne revient pas aussi | −'[l’j' | tout d’un coup, et on ne revient pas aussi | 0.91 | 0.93 |
| `00068285:0139:040` | fair_copy | boundary | boundary-letter | eae quae a beatis funduntur, | reads 'eae, quae a beatis' | eae, quae a beatis | 0.57 | 0.63 |
| `00068285:0183:029` | fair_copy | correct | normalization | inter se, et cum externis consentientes. | −',' (after:inter se) | inter se et cum externis consentientes. | 0.97 | 1.00 |
| `00068285:0194:004` | fair_copy | wrong | reading | salubriter Ecclesiae provideatur. | 'provideatur' → 'praevideatur' | salubriter Ecclesiae praevideatur. | 0.94 | 0.94 |
| `00068285:0211:023` | fair_copy | boundary | boundary-letter | m divina sapientia dignum esse nega | +'hoc' (before:divina sapientia) | m hoc divina sapientia dignum esse nega | 0.90 | 0.90 |
| `00068285:0256:015` | fair_copy | wrong | reading | indulgentiam recipere, ut quando eandem | 'ut' → 'et' | indulgentiam recipere, et quando eandem | 0.97 | 0.97 |
| `DE-611-HS-957357:0088:009` | light_revision | correct | boundary-letter | rai pas de vous communique | 'communique' → 'communiquer' | rai pas de vous communiquer | 0.96 | 0.96 |
| `DE-611-HS-867205:0001:032` | light_revision | boundary | boundary-letter | tudiis cogitatio; qua ut plurimum | 'tudiis' → 'Studiis' | Studiis cogitatio; qua ut plurimum | 0.97 | 0.97 |
| `DE-611-HS-857075:0050:034` | light_revision | boundary | boundary-letter | aller faire? à quo | 'quo' → 'quoy' | aller faire? à quoy | 0.95 | 0.94 |
| `DE-611-HS-959288:0086:029` | light_revision | wrong | other | érité | 'érité' → 'serviteur' | serviteur | 0.33 | 0.56 |
| `DE-611-HS-866698:0001:007` | light_revision | boundary | boundary-letter | Espagnols aux Francés qu'est surprennent, car a ce pauure Ro | 'Ro' → 'Roy' | Espagnols aux Francés qu'est surprennent, car a ce pauure R… | 0.97 | 0.98 |
| `00068774:0254:026` | light_revision | boundary | boundary-letter | men könne, auf welchen fall objectio superior de rege orbo, | −'orbo' (end) | men könne, auf welchen fall objectio superior de rege | 0.88 | 0.91 |
| `00068768:0161:032` | light_revision | boundary | boundary-letter | Sed etsi aliquid restare supponeretur, id mari et N | −'N' (end) | Sed etsi aliquid restare supponeretur, id mari et | 0.94 | 0.96 |
| `DE-611-HS-868175:0015:002` | heavy_revision | boundary | boundary-letter | J’ay esté en doute si j’oseroi | 'oseroi' → 'oserois' | J’ay esté en doute si j’oserois | 0.97 | 0.97 |
| `00068371:0045:027` | heavy_revision | wrong | addition | indies in melius auctam, restitui perfectè et opto et | −'in melius auctam' | indies , restitui perfectè et opto et | 0.68 | 0.67 |
| `DE-611-HS-860205:0007:021` | heavy_revision | boundary | boundary-letter | chrijft dat selvige Monsr iets van de algebra heeft drucke | 'chrijft' → 'Schrijft'; +'n' (end) | Schrijft dat selvige Monsr iets van de algebra heeft drucken | 0.97 | 0.97 |
| `00068400:0010:100` | heavy_revision | boundary | boundary-letter | quibus jurisconsulti vel judices per se non era | 'non era' → 'non erant' | quibus jurisconsulti vel judices per se non erant | 0.96 | 0.96 |
| `00068377:1121:043` | heavy_revision | wrong | normalization | vous entretenir. Et je vous envoyé maintenant | 'envoyé' → 'envoye' | vous entretenir. Et je vous envoye maintenant | 0.98 | 1.00 |
| `00068778:0014:023` | heavy_revision | boundary | boundary-letter | ipso opere: Constantino Bonelli vescouo di citta` di Castel… | 'vescouo' → 'vescovo'; 'ipso opere' → 'in ipso opere'; 'cit… | in ipso opere: Constantino Bonelli vescovo di città di Cast… | 0.89 | 0.95 |
| `00068647:0042:076` | heavy_revision | correct | correct | Porro is Plantae varia nomina accipiunt, tum a partibus, | −'is' (after:Porro) | Porro Plantae varia nomina accipiunt, tum a partibus, | 0.95 | 0.94 |
| `DE-611-HS-970486:0240:012` | heavy_revision | boundary | boundary-letter | primer ses oeures en 2 Vol. in grand Fol.; il me semble d'e… | 'primer' → 'imprimer' | imprimer ses oeures en 2 Vol. in grand Fol.; il me semble d… | 0.96 | 0.97 |
| `DE-611-HS-960108:0005:046` | heavy_revision | boundary | boundary-letter | bono utilissimam ad finem perducat. De | −'De' (end) | bono utilissimam ad finem perducat. | 0.92 | 0.92 |
| `DE-611-HS-867509:0126:022` | heavy_revision | wrong | math | ia yy x 2ax — xx a Cartesio Geometricam dictam semper Mihi … | 'ia' → 'eg'; −'(' (end) | eg yy x 2ax — xx a Cartesio Geometricam dictam semper Mihi … | 0.93 | 0.97 |
| `00068334:0033:053` | heavy_revision | boundary | bracket | hes. 2] 7) Somnia, visiones, voces, literae, miracula non s… | −'hes. 2]' (start) | 7) Somnia, visiones, voces, literae, miracula non sunt form… | 0.91 | 0.93 |
| `DE-611-HS-958006:0014:030` | heavy_revision | boundary | boundary-letter | Abbé Baudrant, je ne manqueray pas de | 'Abbé' → "l'Abbé" | l'Abbé Baudrant, je ne manqueray pas de | 0.92 | 0.95 |
| `00068377:0280:017` | heavy_revision | wrong | normalization | dans un arrest, sans qu’on puisse alléguer contre celuy qui… | 'celuy qui allégué' → 'celuy qui allegue' | dans un arrest, sans qu’on puisse alléguer contre celuy qui… | 0.96 | 1.00 |
| `00068377:1186:023` | heavy_revision | boundary | boundary-letter | la bonne foy qu’il a | reads 'la bonne foy qu’il' | la bonne foy qu’il | 0.90 | 0.90 |
| `00068823:0324:003` | heavy_revision | correct | bracket | n gelindigkeit und flexibilität erhalten werden[,] | −'n' (start) | gelindigkeit und flexibilität erhalten werden[,] | 0.94 | 0.96 |
| `00068823:0324:025` | heavy_revision | correct | boundary-letter | Mahlzeit. (NB.) Der trunck mus nicht starck s | −'s' (end) | Mahlzeit. (NB.) Der trunck mus nicht starck | 0.96 | 0.95 |
| `DE-611-HS-855794:0242:018` | scrap | correct | boundary-letter | hiarint. Utrumque huic muneri non male praefuturum s | −'s' (end) | hiarint. Utrumque huic muneri non male praefuturum | 0.96 | 0.96 |
| `DE-611-HS-958114:0029:034` | scrap | boundary | boundary-letter | serviteur C | −'C' | serviteur | 0.82 | 0.82 |
| `DE-611-HS-861286:0053:017` | scrap | boundary | boundary-letter | fort connu, et les Medicins pourr | 'pourr' → 'pour' | fort connu, et les Medicins pour | 0.97 | 0.97 |
| `DE-611-HS-959414:0012:041` | scrap | boundary | boundary-letter | la quiter pour suivre son altesse partout | +'de' (start) | de la quiter pour suivre son altesse partout | 0.93 | 0.93 |
| `DE-611-HS-959414:0012:051` | scrap | boundary | boundary-letter | avoir de vos nouvelles affin que sy vo | 'sy vo' → 'sy vous' | avoir de vos nouvelles affin que sy vous | 0.95 | 0.95 |
| `DE-611-HS-859609:0398:021` | scrap | correct | boundary-letter | cepticos nuper miratus | 'cepticos' → 'scepticos' | scepticos nuper miratus | 0.96 | 0.96 |
| `DE-611-HS-856973:0134:011` | scrap | boundary | boundary-letter | ’observatoire, elle servira pour | '’observatoire' → 'L’observatoire' | L’observatoire, elle servira pour | 0.97 | 0.94 |
| `DE-611-HS-3595205:0327:022` | scrap | boundary | boundary-letter | incapable d’etre rompu. Ce | +'et' (start); −'. Ce' (end) | et incapable d’etre rompu | 0.73 | 0.76 |
| `DE-611-HS-3616805:0057:031` | scrap | boundary | boundary-letter | su Amuletorum non facio meam. Addit | −'su' (start); −'Addit' (end) | Amuletorum non facio meam. | 0.74 | 0.74 |
| `00068573:0003:057` | scrap | boundary | boundary-letter | honneur, et plaisirs de convenance; l’un d’estre loué; l’au… | +"l'" (start) | l'honneur, et plaisirs de convenance; l’un d’estre loué; l’… | 0.97 | 0.98 |
| `DE-611-HS-860722:0087:064` | scrap | wrong | math | tc., ut patebit substituendo in allatam regulam | 'tc.' → '+ x' | + x, ut patebit substituendo in allatam regulam | 0.94 | 0.96 |
| `00068369:0132:007` | scrap | boundary | boundary-letter | hristus secundum humanam hoc universum et in eo Ecclesiam g… | 'hristus' → 'Christus'; −'o' (end) | Christus secundum humanam hoc universum et in eo Ecclesiam … | 0.95 | 0.96 |
| `00068369:0132:035` | scrap | boundary | boundary-letter | in medio relinquitur, an autem illaeso Concilio Tridentino d | −'d' (end) | in medio relinquitur, an autem illaeso Concilio Tridentino | 0.97 | 0.97 |
| `DE-611-HS-3595205:0063:045` | scrap | boundary | boundary-letter | choses que vous dites, vous pouvez estre très seur quel en … | −'2 (Danebens' | (not placed) | — | — |
