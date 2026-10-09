"""Stopword language identification for edition text (Phase K1; the first `enrich` module).

Returns ``la`` | ``fr`` | ``de`` | ``mixed`` | ``unknown`` with a score, from
nothing but three disjoint lists of function words. The Nachlass is Latin,
French and German, and in the 17th century the three are told apart by their
small words long before any model is needed: *vnd*, *daß*, *seyn*, *alß*, *umb*
and *auff* are German however the scribe spelt them; *j'ay*, *moy*, *estre* and
*mesme* are French; *quod*, *enim*, *tamen* and *igitur* are Latin.

Built for **clean edition text** — the constituted reading text of the Academy
edition in the C2 edition cache, a few hundred to a few thousand words per
piece. It is the ``enrich`` package's first module (SPECS §4.1 places language
identification there, as C4's job on the recognised lines); C4 may well replace
it for noisy HTR lines, where a seven-word line misread at 10 % CER carries two
or three function words at best. Nothing here reaches a model or the network.

The method, in one paragraph. Tokens are the runs of letters in the lowercased
text; a token glued to an apostrophe (``j'``, ``qu'``, ``l'``) is a French
elision clitic and counts as French. Every token is looked up in the three
lists; the lists are disjoint by construction (the words all three share —
*et*, *est*, *de*, *in*, *si*, *non*, *qui*, *des*, *die*, *nos*, *vos* and a
few more — are in none of them). A text shorter than :data:`MIN_TOKENS` tokens,
or with fewer than :data:`MIN_HITS` hits for its leading language, is
``unknown``: stopwords are roughly one token in three in running prose, so
eight tokens give two or three hits, and two is the least that keeps a single
loanword or a Latin date (*die*) from deciding a language. Otherwise the
*dominance* — the leading language's share of all hits — decides: at least
:data:`DOMINANT` (0.65) names the language; a runner-up holding at least
:data:`MIXED_SHARE` (0.25) of the hits makes the text ``mixed``; anything in
between is ``unknown``. The score reported is the dominance.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

MIN_TOKENS = 8
MIN_HITS = 2
DOMINANT = 0.65
MIXED_SHARE = 0.25

LANGS: tuple[str, ...] = ("la", "fr", "de")

# French elision clitics: the part before the apostrophe in j'ay, qu'il, l'on,
# d'un, n'est, s'il, c'est, m'a, t'en. Latin and German do not elide this way.
FR_CLITICS: frozenset[str] = frozenset({"j", "qu", "l", "d", "n", "s", "c", "m", "t"})


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


# Function words and the commonest verbs. The 17th-century spellings sit beside
# the modern ones (the Academy edition keeps the originals' orthography apart
# from u/v and i/j, and the catalogue's own notes are modern). Shared words are
# excluded from every list — see the module docstring.
LATIN: frozenset[str] = _words(
    """
    ad ut vt cum quod quae quam sed ex enim autem etiam vel nec neque atque ac sunt esse
    per ab aut hoc haec hic hunc hanc huius hujus his hos has ego mihi tibi sibi nobis vobis
    suo sua suum suam sui meo mea meum meam mei tuo tua tuum noster nostra nostrum nostro
    nostri nostris vester vestra vestrum vestro ita tamen iam jam ergo igitur quidem quoque
    itaque omnia omnis omne omnes omnium omnibus nihil nil quid quo qua quia dum donec apud pro
    sine inter intra extra supra infra sub super contra circa propter ante tam tum nunc tunc
    ubi vbi unde vnde ibi hinc inde ipse ipsa ipsum ipsius ille illa illud illum illam illius
    illi illos illas eius ejus eorum earum eo ea id eum eam ei eos eas iis eis idem eadem
    cuius cujus cui quibus quos quas quem quorum quarum fuit erat erant fuerunt erit erunt sit
    sint esset essent fuisse fuerit fore sum sumus habet habent habere habeo habuit potest
    possunt posse potuit possit possint vult volunt velle velim vellem voluit debet debent
    debere videtur videntur videre dicit dicunt dicere dixit facit faciunt facere fecit
    scribit scribere scripsi scripsit puto credo scio scire adhuc semper nunquam numquam
    saepe interim olim mox statim denique deinde postea antea ideo idcirco propterea
    praeterea vero verum nam namque quippe scilicet nempe videlicet utique imo immo sane
    certe profecto plane omnino prorsus fere vix paene pene nullus nulla nullum nemo aliquis
    aliquid aliqua aliquo quidam quaedam quoddam quisquam quicquam quidquam quisque quaeque
    uterque utraque altera alterum alius alia aliud alii aliis ceteri caeteri reliqui
    totus tota totum multi multa multum multis plures plura pauci pauca magis potius maxime
    minime satis nimis parum tantum solum modo saltem res rei rem rebus rerum licet nisi etsi
    quamvis quoniam quasi quin tanquam tamquam sicut velut deus dei deo deum dominus domini
    domino domine vir viri viro virum literae literas litterae litteras epistola epistolam
    epistolae vale salutem
    """
)

FRENCH: frozenset[str] = _words(
    """
    le la les un une du au aux ce cet cette ces cela ceci cecy celle celles ceux celui celuy
    il ils elle elles je nous vous on lui luy leur leurs y en pas point que qu quoi quoy
    dont où ou mais donc car ni puis puisque lorsque parce afin ainsi ainsy aussi aussy alors
    encore encor toujours tousjours jamais souvent déjà deja bien très tres trop peu
    beaucoup assez tout tous toute toutes même mesme mesmes autre autres chaque chacun quelque
    quelques plusieurs aucun aucune rien personne son sa ses mon ma mes ton ta tes notre nostre
    votre vostre pour par sur sous dans avec sans chez vers entre contre depuis pendant selon
    comme quand devant après apres avant dessus dessous dedans dehors ici icy là voici voicy
    voilà voila oui ouy soit sont ont font vont avons avez avoir eu eue eut fut furent sera
    seront seroit serait auroit aurait avoit avait avoient avaient peut peuvent pourra pourroit
    pourrait veut veux voudrois voudrais doit doivent devoit devait faut falloit fallait fais
    fait faite faits faire dit dire dis voir vu veu pris prendre mettre mis donner donné
    envoyer envoyé envoye recevoir receu reçu écrire escrire écrit escrit été esté être estre
    estoit estoient étoit étoient suis sommes estes êtes ay sçavoir scavoir sçay sçait sais
    sait moy moi toy toi
    monsieur madame lettre lettres serviteur honneur
    """
)

GERMAN: frozenset[str] = _words(
    """
    und vnd vndt vnnd unnd der dem den das dass daß ein eine einen einem einer eines kein
    keine keinen keinem keiner ist sind sey seyn sein seine seiner seinem seinen seind bin
    bist war wahr waren gewesen worden wird wirdt werden wurde wurden hat hatt habe hab haben
    hatte hatten hette hetten kann kan können könne konnte könnte soll sol sollen sollte solte
    muss muß müssen will wollen wolle wolte wollte lassen lasse laßen machen gemacht geben
    gegeben kommen komen gehen sagen gesagt wissen weiß weis nicht nit nichts nichtes mit mitt
    von zu zue zur zum bey bei beym beim nach vor für fur auf auff uff aus auß auss über vber
    uber unter vnter durch gegen ohne ohn um umb wegen bis biß seit seith zwischen hinter
    neben wider am im vom ins aufs auffs wie als alß alss auch aber oder wenn wan wann weil
    weiln dieweil obwohl obwol wiewol gleichwol sondern denn dann doch ja nein also alßo so
    noch nur nun schon sehr gar ganz gantz viel vil wol wohl dar hier hie allhier alhier dort
    heut heute jetzt itzt jetzo itzo nunmehr vorhin hernach hernacher sonst sonsten selbst
    selbsten etwa etwan gleich bald baldt zumal zumahl zwar daran darin darinn drin darauf
    darauff drauf dabey dabei damit dadurch davon dazu darzu dafür darfür darum darumb
    deswegen derowegen dergleichen derselben desselben demselben dieselbe dieselben dieser
    diese dieses diesem diesen dieß diß jener jene jenes solche solcher solches solchem
    solchen welche welcher welches welchem welchen alle allen aller allem alles andere anderen
    anders etwas man jemand niemand einige viele wenig wenige mehr mehrere meist erst erste
    ersten letzt letzten ich mir mich wir uns vns unser vnser unsere unserer unserem unseren
    mein meine meinem meinen meiner meines gott gnaden weiter ferner wieder wiederum wiederumb
    indem nachdem sowohl sowol hiermit hiemit hierbey hiebey hievon hiervon hierauf hierauff
    euch euer ewer eure ewre ihr ihre ihrer ihrem ihren ihnen ihro dero deren dessen sie er
    es ihm ihn was wer wo womit wodurch wovon wozu hochgeehrter gnädiger gnädigen herr herrn
    hern
    """
)

_LISTS: dict[str, frozenset[str]] = {"la": LATIN, "fr": FRENCH, "de": GERMAN}

# The lists must be disjoint: a shared word would count for two languages at once
# and quietly bias every dominance.
for _a, _b in (("la", "fr"), ("la", "de"), ("fr", "de")):
    _shared = _LISTS[_a] & _LISTS[_b]
    assert not _shared, f"stopword lists {_a}/{_b} share {sorted(_shared)}"

_TOKEN_RE = re.compile(r"([^\W\d_]+)(['’])?")


@dataclass(slots=True)
class LangResult:
    """The verdict on one text and the evidence behind it."""

    lang: str  # la | fr | de | mixed | unknown
    score: float  # the leading language's share of all stopword hits (0 when none)
    top: str | None  # the leading language, even when mixed or unknown
    second: str | None  # the runner-up, when it has any hits
    n_tokens: int
    hits: dict[str, int] = field(default_factory=dict)

    @property
    def coverage(self) -> float:
        """Stopword hits ÷ tokens: how much of the text the lists could read."""
        return sum(self.hits.values()) / self.n_tokens if self.n_tokens else 0.0


def tokens(text: str) -> list[str]:
    """The lowercased letter runs of ``text``; an elided clitic keeps its apostrophe."""
    out: list[str] = []
    for m in _TOKEN_RE.finditer(text.lower().replace("ſ", "s")):
        word, apos = m.group(1), m.group(2)
        out.append(word + "'" if apos and word in FR_CLITICS else word)
    return out


def count_hits(toks: Iterable[str]) -> tuple[dict[str, int], int]:
    """Stopword hits per language and the token count."""
    hits = {lang: 0 for lang in LANGS}
    n = 0
    for tok in toks:
        n += 1
        if tok.endswith("'"):
            hits["fr"] += 1
            continue
        for lang, words in _LISTS.items():
            if tok in words:
                hits[lang] += 1
                break
    return hits, n


def classify(text: str) -> LangResult:
    """Classify one text; see the module docstring for the rule."""
    hits, n = count_hits(tokens(text))
    ranked = sorted(LANGS, key=lambda lang: (-hits[lang], LANGS.index(lang)))
    top, runner = ranked[0], ranked[1]
    total = sum(hits.values())
    top_hits = hits[top]
    score = top_hits / total if total else 0.0
    top_name = top if top_hits else None
    second_name = runner if hits[runner] else None
    if n < MIN_TOKENS or top_hits < MIN_HITS:
        return LangResult("unknown", score, top_name, second_name, n, hits)
    if score >= DOMINANT:
        return LangResult(top, score, top_name, second_name, n, hits)
    if hits[runner] / total >= MIXED_SHARE:
        return LangResult("mixed", score, top_name, second_name, n, hits)
    return LangResult("unknown", score, top_name, second_name, n, hits)


__all__ = [
    "DOMINANT",
    "FRENCH",
    "FR_CLITICS",
    "GERMAN",
    "LANGS",
    "LATIN",
    "MIN_HITS",
    "MIN_TOKENS",
    "MIXED_SHARE",
    "LangResult",
    "classify",
    "count_hits",
    "tokens",
]
