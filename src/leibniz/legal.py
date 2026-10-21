"""The project's legal registries: §70/§71 expiry of the Akademie-Ausgabe (AA)
reading text, and the licence state of every third-party artifact.

The first part encodes, as structured data, which Leibniz Academy Edition
volumes' **constituted reading text** may be redistributed today, and when the
rest become free. It is the single machine-readable source of truth for the
§70/§71 math the project must never get wrong (SPECS §1.4, §7.2).

The second part (Phase L1, 2026-10-21) is the **licence registry**: one entry
per third-party artifact the project obtained, evaluated, built on or runs
beside — the licence as obtained with its date, the licence as currently
published where it changed with the date seen, the bucket consequence (SPECS
§7.3), what was built from it — and the table of this project's own outputs
with the licence each carries and why. Every public surface that states a
licence (the About page, ``llms.txt``, the dataset cards, the attribution
lines) reads it from here; ``leibniz legal licences`` prints it.

The legal rule
--------------
German copyright grants two relevant 25-year neighbouring rights, both measured
from *first publication*:

* **§70 UrhG** — *wissenschaftliche Ausgaben*: the editorial achievement of a
  scientific edition (the constituted reading text, its ordering) is protected
  for 25 years.
* **§71 UrhG** — *editio princeps*: whoever first lawfully publishes a
  previously unpublished work that is itself out of copyright gets 25 years.
  Much of the Nachlass is first made public *in* the AA volumes, so this can
  attach to the text as well as to the edition.

Both terms are computed under the **calendar-year rule (§69 UrhG)**: the clock
starts at the *end* of the calendar year of publication. A volume published in
year *Y* is therefore protected through the end of *Y+25* and enters the public
domain on **1 January of Y+26**. One date per volume clears both §70 and §71,
because both run from the same first-publication event. Hence:

    free_from = date(first_publication_year + 26, 1, 1)

Worked anchors (all cross-checked against leibnizedition.de, July 2026):
    I,17  published 2001  -> free 2027-01-01
    VII,8 published 2024  -> free 2050-01-01

The hard rule (SPECS §7.2)
--------------------------
Only the *reading text* of an expired volume may be extracted or redistributed.
Editor introductions, apparatus, commentary, and indices are ordinary §2 works
(70 years p.m.a.) and are **never** touched, regardless of the volume's §70/§71
status. This registry says *when a volume's reading text is free*; it does not
license anything else in the book.

Re-editions restart the clock
-----------------------------
A genuinely reworked new edition (*Neubearbeitung*) is a fresh scientific
edition with its own 25-year term; a mere *durchgesehener Nachdruck* (reviewed
reprint) is not. Where a later reworked edition is itself already expired we
keep one entry; where it is still protected we list it separately so its date
is tracked. The load-bearing case is **II,1**: the 1926 text is long free, but
the 2006 *Neubearbeitung* is protected until 2032 — extract from the 1926 print.

Coverage & maintenance
----------------------
The registry lists every volume with a *confirmed* first-publication year
through the near-term expiry horizon (all volumes free today, all volumes
expiring by 2050 in the series we care about). It is deliberately not an
exhaustive catalogue of all ~60 AA volumes: later volumes are added as their
years are verified. The public domain grows every 1 January, so re-run
:func:`upcoming_expiries` rather than trusting a cached list. Re-verify against
leibnizedition.de before relying on any single date.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

# The calendar-year offset: 25-year term (§70/§71) + §69 rounding to the end of
# the publication year => public domain on 1 January of publication_year + 26.
FREE_AFTER_YEARS = 26

# Reihen (series) referenced by this registry, as Roman numerals.
_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 6: "VI", 7: "VII"}

# Attribution / usage reminder for anything that consumes expired reading text.
READING_TEXT_ONLY = (
    "Use only the constituted READING TEXT of an expired AA volume. Never "
    "extract or redistribute editor introductions, apparatus, commentary, or "
    "indices — those remain protected as ordinary §2 works (SPECS §7.2)."
)


@dataclass(frozen=True, slots=True)
class Volume:
    """One AA volume (or a distinct edition of one) and its expiry date.

    ``volume`` is usually an ``int`` but may be a string for non-numbered parts
    (e.g. the Reihe I Harz *Supplementband*), mirroring the AA's own
    bibliography. ``edition`` distinguishes re-editions of the same volume
    (e.g. II,1 ``"1926"`` vs ``"2006"``); ``None`` means the volume has a single
    edition.
    """

    series: int
    volume: int | str
    first_publication_year: int
    edition: str | None = None
    note: str | None = None

    @property
    def series_roman(self) -> str:
        return _ROMAN.get(self.series, str(self.series))

    @property
    def free_from_year(self) -> int:
        """Calendar year in which the reading text enters the public domain."""
        return self.first_publication_year + FREE_AFTER_YEARS

    @property
    def free_from(self) -> date:
        """Exact date the reading text becomes free (1 January of that year)."""
        return date(self.free_from_year, 1, 1)

    @property
    def label(self) -> str:
        """Human-readable id, e.g. ``"I,17"`` or ``"II,1 (1926)"``."""
        base = f"{self.series_roman},{self.volume}"
        return f"{base} ({self.edition})" if self.edition else base

    @property
    def key(self) -> tuple[int, str, str]:
        """Stable identity of this entry: (series, volume, edition)."""
        return (self.series, str(self.volume), self.edition or "")

    def is_expired(self, today: date) -> bool:
        """True if the reading text is redistributable on ``today``."""
        return today >= self.free_from


# --------------------------------------------------------------------------- #
# The registry
# --------------------------------------------------------------------------- #
# First-publication years verified against leibnizedition.de (the edition's own
# Forschungsstellen), cross-checked against gwlb.de, rep.adw-goe.de, and
# De Gruyter, July 2026. See STATUS.md for the audit trail and open questions.

REGISTRY: tuple[Volume, ...] = (
    # Reihe I — Allgemeiner politischer und historischer Briefwechsel
    Volume(1, 1, 1923),
    Volume(1, 2, 1927),
    Volume(1, 3, 1938),
    Volume(1, 4, 1950),
    Volume(1, 5, 1954),
    Volume(1, 6, 1957),
    Volume(1, 7, 1964),
    Volume(1, 8, 1970),
    Volume(1, 9, 1975),
    Volume(1, 10, 1979),
    Volume(1, 11, 1982),
    # I,13 (1987) appeared before I,12 (1990): volumes are numbered by the
    # period they cover, not publication order. Both long expired.
    Volume(1, 12, 1990),
    Volume(1, 13, 1987),
    Volume(1, 14, 1993),
    Volume(1, 15, 1998),
    Volume(1, 16, 2000),  # boundary: free 2026-01-01
    Volume(1, 17, 2001),  # boundary: protected until 2027-01-01
    Volume(
        1, "Suppl", 1991, note="Supplementband Harzbergbau (1692–1696); outside main numbering."
    ),
    # Reihe II — Philosophischer Briefwechsel
    Volume(
        2, 1, 1926, edition="1926", note="First edition (Darmstadt); reading text long expired."
    ),
    Volume(
        2,
        1,
        2006,
        edition="2006",
        note="Völlig neubearbeitete Auflage (Berlin) — a fresh scientific edition; "
        "protected until 2032. Extract from the 1926 print, not this one.",
    ),
    # Reihe III — Mathematischer, naturwissenschaftlicher u. technischer Briefwechsel
    Volume(3, 1, 1976, note="2nd ed. 1988 (also expired)."),
    Volume(3, 2, 1987),
    Volume(3, 3, 1991),
    Volume(3, 4, 1995),  # boundary
    Volume(3, 5, 2003),  # boundary: protected until 2029-01-01
    # Reihe IV — Politische Schriften
    Volume(4, 1, 1931, note="3rd ed. 1983 (also expired)."),
    Volume(4, 2, 1963, note="2nd ed. 1984 (also expired)."),
    Volume(4, 3, 1986),  # boundary
    Volume(4, 4, 2001),  # boundary: protected until 2027-01-01
    # Reihe VI — Philosophische Schriften  (VI,5 not yet in print as of 2026)
    Volume(6, 1, 1930, note="Durchgesehener Nachdruck 1990 (reprint does not restart the term)."),
    Volume(6, 2, 1966, note="Durchgesehener Nachdruck 1990."),
    Volume(6, 3, 1980, note="Source ±1yr (site reads 1981); legally immaterial, long expired."),
    Volume(6, 4, 1999, note="Issued in four parts A–D, all 1999."),
    Volume(6, 6, 1962, note="Nouveaux Essais; durchgesehener Nachdruck 1990."),
    # Reihe VII — Mathematische Schriften
    Volume(7, 1, 1990),
    Volume(7, 2, 1996),  # boundary
    Volume(7, 3, 2003),  # boundary: protected until 2029-01-01
    Volume(7, 4, 2008),
    Volume(7, 5, 2008, note="Companion to VII,4 (same year)."),
    Volume(7, 6, 2012),
    Volume(7, 7, 2019),
    Volume(7, 8, 2024),  # anchor: protected until 2050-01-01
)


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #


def _sort_key(v: Volume) -> tuple:
    numeric = isinstance(v.volume, int)
    return (
        v.series,
        0 if numeric else 1,
        v.volume if numeric else 0,
        str(v.volume),
        v.edition or "",
    )


def expired_volumes(today: date, registry: tuple[Volume, ...] = REGISTRY) -> list[Volume]:
    """Volumes whose reading text is redistributable on ``today``.

    "Usable" means the §70/§71 term has run out — i.e. ``today`` is on or after
    the volume's ``free_from`` date. The result is sorted by series then volume.
    """
    return sorted((v for v in registry if v.is_expired(today)), key=_sort_key)


def protected_volumes(today: date, registry: tuple[Volume, ...] = REGISTRY) -> list[Volume]:
    """The complement of :func:`expired_volumes`: still-protected volumes."""
    return sorted((v for v in registry if not v.is_expired(today)), key=_sort_key)


def upcoming_expiries(today: date, registry: tuple[Volume, ...] = REGISTRY) -> list[Volume]:
    """Still-protected volumes, soonest to expire first (then by series/volume).

    Handy for the "new expiries every 1 January" ticker (SPECS §1.4): the first
    group shares the nearest ``free_from`` date.
    """
    return sorted(
        (v for v in registry if not v.is_expired(today)),
        key=lambda v: (v.free_from_year, _sort_key(v)),
    )


def get_volume(
    series: int,
    volume: int | str,
    edition: str | None = None,
    registry: tuple[Volume, ...] = REGISTRY,
) -> Volume | None:
    """Look up one registry entry by (series, volume, edition), or ``None``."""
    for v in registry:
        if v.series == series and v.volume == volume and v.edition == edition:
            return v
    return None


# =========================================================================== #
# The licence registry (Phase L1, 2026-10-21)
# =========================================================================== #
# One entry per third-party artifact. Facts, dated; decisions are the owner's
# and are recorded, not argued (SPECS §7.7). Where a question is legal it goes
# to the lawyer memo (SPECS §7.5; the list in reports/release-checklist.md),
# not into prose here that asserts an answer.
#
# Buckets (SPECS §7.3): ``open`` — text or data derived from the artifact may
# enter the CC BY outputs; ``nc`` — derived text stays in the nc partition,
# never on the site and never in a CC BY release; ``none`` — nothing of the
# artifact is derived into any output (a tool run beside the repository, a
# reader evaluated only, a source not used).
#
# Deposits: the ground-truth dataset D3 is two deposits by channel (the
# owner's scheme of 2026-10-13): ``open`` (CC BY 4.0) for lines whose edition
# text was read through a channel with no terms of its own, ``nc`` (CC BY-NC
# 4.0) for lines read through a channel with non-commercial terms. A channel
# with ``deposit=None`` is never released (the letter pool, the Münster
# Internetausgaben).

BUCKETS = ("open", "nc", "none")
DEPOSITS = ("open", "nc")

# The day the registry was compiled and the public records were re-read.
REGISTRY_DATE = date(2026, 10, 21)


@dataclass(frozen=True, slots=True)
class Terms:
    """A licence as this project saw it on one date."""

    licence: str  # "CC BY 4.0", "CC BY-NC 4.0", "MIT", "none stated", …
    seen: date  # the day it was obtained, or read
    where: str = ""  # the record, page or letter it was read from
    since: date | None = None  # the day a change took effect, where it is known


@dataclass(frozen=True, slots=True)
class Artifact:
    """One third-party artifact and its licence state."""

    key: str
    name: str
    kind: str  # model | dataset | text | images | catalogue | code | tool
    source: str  # DOI or URL
    version: str  # version, revision or commit, as known
    obtained: Terms  # the licence as obtained (as first seen, for one not obtained)
    current: Terms | None  # the licence as currently published, where it changed
    bucket: str  # BUCKETS
    built: str  # what this project built from it
    notes: str = ""
    channel: str | None = None  # the GT factory's channel key (``source``: "channel …")
    deposit: str | None = None  # the D3 deposit lines of this channel go to, or None
    used: bool = True  # False: recorded, nothing built from it
    asked: str = ""  # an open ask, dated

    def __post_init__(self) -> None:
        if self.bucket not in BUCKETS:
            raise ValueError(f"bucket must be in {BUCKETS}: {self.key}")
        if self.deposit is not None and self.deposit not in DEPOSITS:
            raise ValueError(f"deposit must be in {DEPOSITS} or None: {self.key}")

    @property
    def licence_now(self) -> Terms:
        """The licence as currently published (the one obtained, where unchanged)."""
        return self.current or self.obtained

    @property
    def changed(self) -> bool:
        return self.current is not None and self.current.licence != self.obtained.licence


def _d(y: int, m: int, d: int) -> date:
    return date(y, m, d)


_PHILIUMM_RELICENSED = (
    "PHILIUMM relicensed its models (the HTR and the segmentation model) to CC BY-NC 4.0 "
    "on 2026-10-15 (their HTR engineer's note of that day; the Zenodo record updated "
    "2026-10-15, read 2026-10-21); the dataset stays CC BY 4.0 and this project's outputs "
    "may stay CC BY 4.0 and Apache-2.0 with their agreement (the project lead, 2026-10-15). "
    "The copy this project holds was obtained under CC BY 4.0; whether that grant is "
    "irrevocable for copies already obtained (CC BY 4.0 §2(a)(1)) is a lawyer-memo "
    "question, not a position taken here."
)

LICENCES: tuple[Artifact, ...] = (
    # ---- PHILIUMM (ERC, Paris) -------------------------------------------- #
    Artifact(
        key="philiumm-htr-model",
        name="PHILIUMM HTR model for Leibniz's hand (FoNDUE-GD_v2_ft_Leibniz)",
        kind="model",
        source="doi:10.5281/zenodo.21457538",
        version="v1 (FoNDUE-GD_v2_ft_Leibniz.safetensors; record published 2026-07-20)",
        obtained=Terms("CC BY 4.0", _d(2026, 7, 29), "the Zenodo record, Phase B1"),
        current=Terms(
            "CC BY-NC 4.0",
            _d(2026, 10, 21),
            "the Zenodo record (updated 2026-10-15)",
            since=_d(2026, 10, 15),
        ),
        bucket="open",
        built=(
            "the v1 corpus transcription (C1; the site, dataset D2, the IIIF annotations: "
            "machine output, CC BY 4.0), the HTR side of the GT factory (C2), the K1 baseline; "
            "a model fine-tuned from it (v2, K3's kraken candidate) is CC BY-NC 4.0 by the "
            "owner's choice of 2026-10-13"
        ),
        notes=_PHILIUMM_RELICENSED,
    ),
    Artifact(
        key="philiumm-seg-model",
        name="PHILIUMM kraken segmentation model (baselines, SegmOnto zones)",
        kind="model",
        source="doi:10.5281/zenodo.21537859",
        version="1.0.0 (blla_ft_leibniz_v1_0.4750.safetensors; record published 2026-07-24)",
        obtained=Terms("CC BY 4.0", _d(2026, 7, 29), "the Zenodo record, Phase B1"),
        current=Terms(
            "CC BY-NC 4.0",
            _d(2026, 10, 21),
            "the Zenodo record (updated 2026-10-15)",
            since=_d(2026, 10, 15),
        ),
        bucket="open",
        built="the corpus-wide line segmentation (C1): every line's geometry on the site",
        notes=_PHILIUMM_RELICENSED,
    ),
    Artifact(
        key="philiumm-dataset",
        name="PHILIUMM HTR dataset for Leibniz's manuscripts (htr_leibniz_dataset_v1)",
        kind="dataset",
        source=(
            "https://huggingface.co/datasets/DenisaBumba/htr_leibniz_dataset_v1 "
            "(formerly DenisaB/…); Zenodo twin doi:10.5281/zenodo.21622297"
        ),
        version="Hub revision b53f531c (2026-09-02); Zenodo v1 (published 2026-07-27)",
        obtained=Terms("CC BY 4.0", _d(2026, 7, 29), "the Hub card, Phase B1 (the val split)"),
        current=Terms(
            "CC BY 4.0", _d(2026, 10, 21), "the Hub card and the Zenodo record, unchanged"
        ),
        bucket="open",
        built=(
            "the B1 reproduction (val split), the P1 cross-check of A VI,4 (the PAGE files, "
            "fetched 2026-10-08), the held-out pages for C3, C3's training data"
        ),
        notes=(
            "PHILIUMM's relicensing of 2026-10-15 was for the models only; the dataset "
            "stays CC BY 4.0 (the HTR engineer, 2026-10-15; the records read 2026-10-21)."
        ),
    ),
    Artifact(
        key="fondue-gd-base",
        name="FoNDUE-GD v2 (the base PHILIUMM fine-tuned from)",
        kind="model",
        source="doi:10.5281/zenodo.14399779",
        version="v2 (published 2024-12-11)",
        obtained=Terms("CC BY 4.0", _d(2026, 10, 21), "the Zenodo record"),
        current=None,
        bucket="open",
        built="nothing directly: the project uses it only through PHILIUMM's fine-tune",
        used=False,
    ),
    Artifact(
        key="philiumm-code",
        name="PHILIUMM's alignment code (GitLab) and the apparatus-reinsertion script",
        kind="code",
        source="https://gitlab.com/eman8/scripts/htr-ocr/alignement-verite-de-terrain-et-transcriptions",
        version="main at 9d2ee4e500e0 (2026-09-21), as read 2026-10-08",
        obtained=Terms("none stated", _d(2026, 10, 8), "the repository: no licence file (P1)"),
        current=None,
        bucket="none",
        built=(
            "nothing copied: the worked example was fetched by raw URL and compared (P1 Task 1)"
        ),
        notes=(
            "The apparatus-reinsertion script has not been received; its licence is unknown "
            "(2026-10-21). PHILIUMM intends permissive terms for their dataset and code (the "
            "project lead, 2026-10-15)."
        ),
        asked="the code's licence, asked 2026-10-13; the script, the ask stands (2026-10-21)",
        used=False,
    ),
    # ---- Kurrent readers (K1) --------------------------------------------- #
    Artifact(
        key="mccatmus",
        name="McCATMuS v1 (kraken transcription model, 16th–21st c.)",
        kind="model",
        source="doi:10.5281/zenodo.13788177",
        version="V1 (McCATMuS_nfd_nofix_V1.mlmodel; published 2024-09-19)",
        obtained=Terms("CC BY 4.0", _d(2026, 10, 9), "the Zenodo record, Phase K1"),
        current=None,
        bucket="none",
        built="the K1 ranking on Dresden only (evaluated, not built on)",
    ),
    Artifact(
        key="trocr-kurrent-xvi-xvii",
        name="dh-unibe/trocr-kurrent-XVI-XVII (the Bern Kurrent TrOCR model)",
        kind="model",
        source="https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII",
        version="Hub revision a6bb6086 (2026-09-23)",
        obtained=Terms("MIT", _d(2026, 10, 9), "the Hub card, Phase K1"),
        current=None,
        bucket="open",
        built=(
            "K2's reader for the German edition pieces (the minted lines are open-bucket "
            "edition text); K3's TrOCR candidate trained from it has no NC input and is "
            "CC BY 4.0 if released (the owner's choice, 2026-10-21)"
        ),
    ),
    Artifact(
        key="trocr-kurrent-xix",
        name="dh-unibe/trocr-kurrent (the 19th-century base of the Bern model)",
        kind="model",
        source="https://huggingface.co/dh-unibe/trocr-kurrent",
        version="Hub revision 66e374e1 (2026-09-23)",
        obtained=Terms("MIT", _d(2026, 10, 9), "the Hub card, Phase K1"),
        current=None,
        bucket="none",
        built="nothing: a reference reader, off by default in the K1 smoke test",
        used=False,
    ),
    Artifact(
        key="trocr-hanse-xvii",
        name="fgho/trocr-hanseXVII-kurrent",
        kind="model",
        source="https://huggingface.co/fgho/trocr-hanseXVII-kurrent",
        version="Hub revision e2834685 (2026-09-02)",
        obtained=Terms("none stated", _d(2026, 10, 9), "the Hub card, Phase K1"),
        current=Terms("none stated", _d(2026, 10, 21), "the Hub card, unchanged"),
        bucket="none",
        built="evaluated only (K1, K2b); nothing is built on it unless a licence appears",
    ),
    Artifact(
        key="trocr-hanse-xvi",
        name="fgho/trocr-hanseXVI-kurrent",
        kind="model",
        source="https://huggingface.co/fgho/trocr-hanseXVI-kurrent",
        version="Hub revision 7513719c (2026-09-02)",
        obtained=Terms("none stated", _d(2026, 10, 9), "the Hub card, Phase K1"),
        current=Terms("none stated", _d(2026, 10, 21), "the Hub card, unchanged"),
        bucket="none",
        built="evaluated only (K1, K2b); nothing is built on it unless a licence appears",
    ),
    Artifact(
        key="ppocr-v6",
        name="kraken's PP-OCRv6 model (a K3 candidate base)",
        kind="model",
        source="kraken's model repository (the record to be written here when K3 fetches it)",
        version="as the operator's note of 2026-10-21 names it",
        obtained=Terms("Apache-2.0", _d(2026, 10, 21), "the operator's note of 21 October"),
        current=None,
        bucket="open",
        built=(
            "not yet: a K3 candidate; a model trained from it on K2's lines has no NC input "
            "and is CC BY 4.0 if released (the owner's choice, 2026-10-21)"
        ),
        used=False,
    ),
    # ---- Kurrent ground truth and test sets -------------------------------- #
    Artifact(
        key="dresden-1673",
        name=(
            "Dresdner Hofdiarium 1673 (SLUB Mscr.Dresd.K.117) ground truth, as the Kurrent "
            "Trace v0.1 package cuts it"
        ),
        kind="dataset",
        source="doi:10.5281/zenodo.15303243",
        version="1.0 (published 2025-04-29); Kurrent Trace v0.1 fetched 2026-09-30",
        obtained=Terms(
            "CC BY 4.0 (Zenodo field) / CC BY-NC-SA 4.0 (the record's README, applied by the "
            "package)",
            _d(2026, 9, 30),
            "the Zenodo record and the package's dataset summary",
        ),
        current=Terms("CC BY 4.0 (Zenodo field)", _d(2026, 10, 21), "the Zenodo record, unchanged"),
        bucket="nc",
        built=(
            "the K1 ranking and K2's reading check (383 lines, internal evaluation only; "
            "no text in a committed file). Images Public Domain Mark 1.0 (SLUB); the package's "
            "own code CC0"
        ),
        notes=(
            "The licence conflict is the author's to resolve; nc bucket until then. The record "
            "continues doi:10.5281/zenodo.15295553 (the TEI of the 1673 diary, CC BY 4.0) and "
            "supplements doi:10.5281/zenodo.14356190 (the 1665 diary, Mscr.Dresd.K.80, CC BY "
            "4.0), both read 2026-10-21 and neither used."
        ),
    ),
    Artifact(
        key="dresden-1673-tei",
        name="TEI of the Dresdner Hofdiarium 1673 (SLUB Mscr.Dresd.K.117)",
        kind="text",
        source="doi:10.5281/zenodo.15295553",
        version="1.0 (published 2025-04-28)",
        obtained=Terms("CC BY 4.0", _d(2026, 10, 21), "the Zenodo record"),
        current=None,
        bucket="none",
        built="nothing: recorded as the sibling of the 1673 ground truth",
        used=False,
    ),
    Artifact(
        key="dresden-1665",
        name="Dresdner Hofdiarium 1665 (SLUB Mscr.Dresd.K.80) ground truth",
        kind="dataset",
        source="doi:10.5281/zenodo.14356190",
        version="published 2024-12-10",
        obtained=Terms("CC BY 4.0", _d(2026, 10, 21), "the Zenodo record"),
        current=None,
        bucket="none",
        built="nothing: recorded as the sibling of the 1673 ground truth",
        used=False,
    ),
    Artifact(
        key="bullinger-htr",
        name="Bullinger HTR ground truth (pstroe/bullinger-htr)",
        kind="dataset",
        source="https://github.com/pstroe/bullinger-htr",
        version="as read 2026-10-09",
        obtained=Terms("CC BY-SA 4.0", _d(2026, 10, 9), "the repository, Phase K1"),
        current=None,
        bucket="none",
        built=(
            "nothing: the method's precedent (SPECS §1.5), not a training input; whether "
            "ShareAlike would reach a model trained on it is a lawyer-memo question"
        ),
        used=False,
    ),
    Artifact(
        key="letterpool",
        name=(
            "GWLB Leibniz-Archiv Transkriptionspool: the checked transcriptions of the "
            "correspondence 1708–1716"
        ),
        kind="text",
        source=(
            "https://www.gwlb.de/leibniz/digitale-ressourcen/repositorium-des-leibniz-archivs/"
            "laa-transkriptionen-<year>"
        ),
        version="version 1 of each year 1708–1716 (reports/kurrent/letterpool-sources.json)",
        obtained=Terms("CC BY-NC 4.0", _d(2026, 10, 19), "the repository's pages, Phase K2b"),
        current=None,
        bucket="nc",
        built=(
            "K2b's German test set (134 letters; evaluation only: never on the site, in a "
            "release, in a committed file or in training). Training on it is allowed by its "
            "licence for an NC model, after K2b's split — recorded, not done (2026-10-21)"
        ),
        channel="letterpool",
        deposit=None,
    ),
    # ---- Images, catalogue, letters --------------------------------------- #
    Artifact(
        key="gwlb-images",
        name="GWLB digital collections: the Leibniz Nachlass scans and their metadata",
        kind="images",
        source="https://digitale-sammlungen.gwlb.de/ (OAI-PMH, IIIF)",
        version="harvested 2026-07-29 (A1); 236,795 page records",
        obtained=Terms(
            "Public Domain Mark 1.0 (scans); CC0 1.0 (metadata)",
            _d(2026, 7, 29),
            "the GWLB Open-Digitisation-Policy (2019), SPECS §1.1",
        ),
        current=None,
        bucket="open",
        built="everything: the inventory (D1), the line images of the ground truth, the viewer",
    ),
    Artifact(
        key="arbeitskatalog",
        name="Arbeitskatalog der Leibniz-Edition (Leibniz-Katalog, BBAW / Arbeitsstelle Potsdam I)",
        kind="catalogue",
        source="https://leibniz-katalog.bbaw.de/",
        version=(
            "scraped 2026-07-29 (A3 sample) and 2026-09 (the §70 volumes' sweep, C2); the "
            "Arbeitsstelle's Access export of 2026-10-21 (70,405 records, CSV via mdbtools; A3b)"
        ),
        obtained=Terms("CC BY 4.0", _d(2026, 7, 29), "the catalogue's site, SPECS §1.2"),
        current=Terms(
            "CC BY 4.0, stated in writing 2026-10-12",
            _d(2026, 10, 12),
            "the head of the Leibniz-Edition Potsdam I and II, 2026-10-12",
            since=_d(2026, 10, 12),
        ),
        bucket="open",
        built=(
            "the crosswalk, the piece texts, the Faszikel index, the links out; from the "
            "export: the whole catalogue in the store (`leibniz catalog import-access`), the "
            "holdings page and reports/holdings.md, the edition's PDF per piece"
        ),
        notes=(
            "The one-time export offered on 2026-10-12 arrived on 2026-10-21 (STATUS.md Open "
            "question 27); a fixture of at most thirty rows per table is committed under "
            "tests/fixtures/arbeitskatalog/ with the attribution, the export itself never."
        ),
    ),
    Artifact(
        key="bodemann-correspsearch",
        name=(
            "Bodemann's catalogue of the correspondence (1889), letter by letter from "
            "correspSearch (BBAW)"
        ),
        kind="catalogue",
        source="https://correspsearch.net/ (edition uuid-12d4f84d-302d-4a6a-b3c2-362e4c6f9207)",
        version=(
            "fetched 2026-10-11 (15,425 letters); data from the portal Der deutsche Brief im "
            "18. Jahrhundert"
        ),
        obtained=Terms("CC BY 4.0", _d(2026, 10, 10), "correspSearch's terms, Phase W5"),
        current=None,
        bucket="open",
        built="/letters, the letters on each convolute's page, the convolute names (W5)",
    ),
    Artifact(
        key="kalliope",
        name="Kalliope: a record per LBr convolute",
        kind="catalogue",
        source="https://kalliope-verbund.info/",
        version="as read 2026-10-10",
        obtained=Terms("none stated", _d(2026, 10, 10), "the site, Phase W5"),
        current=None,
        bucket="none",
        built="nothing: not used (STATUS.md Open question 25; ask before harvesting)",
        used=False,
    ),
    # ---- The edition text's channels (the GT factory) --------------------- #
    Artifact(
        key="edition-ia",
        name=(
            "Public-domain library scans of the AA volumes on the Internet Archive (Trent "
            "University copies)"
        ),
        kind="text",
        source="https://archive.org/download/<identifier> (align/volumes_sources.py)",
        version="verified 2026-09-11; the hOCR text layers",
        obtained=Terms(
            "public-domain scan, no access restriction (the text §70-free)",
            _d(2026, 9, 11),
            "archive.org, Phase C2",
        ),
        current=None,
        bucket="open",
        built="the reading text of most §70-expired volumes; the C2c re-mint's `channel ia` lines",
        notes="C2c re-mint of 2026-10-20: 213,520 lines (STATUS.md, Key numbers).",
        channel="ia",
        deposit="open",
    ),
    Artifact(
        key="edition-gwlb",
        name="The GWLB Repositorium des Leibniz-Archivs: the Reihe I volume PDFs",
        kind="text",
        source="https://www.gwlb.de/leibniz/digitale-ressourcen/repositorium-des-leibniz-archivs",
        version="LAA-BdI3/9/11/12/14/15/16.pdf; used where no scan exists (I,3, I,14, I,15)",
        obtained=Terms("CC BY-NC 4.0", _d(2026, 9, 11), "the repository's pages, Phase C2"),
        current=None,
        bucket="open",
        built=(
            "the reading text of I,3, I,14 and I,15 (§70-free); the `channel gwlb` lines go to "
            "the NC deposit of D3"
        ),
        notes=(
            "C2c re-mint of 2026-10-20: 52,057 lines (STATUS.md, Key numbers). Whether NC "
            "terms on a PDF reach reading text free of §70 is a lawyer-memo question: if not, "
            "the NC deposit opens up. Reihe I is a Göttingen series."
        ),
        channel="gwlb",
        deposit="nc",
        asked=(
            "the Göttingen series (I, III, VII: the research director in Hanover; II, VI: in "
            "Münster): the operator's letters of October 2026; no answer recorded as of 2026-10-21"
        ),
    ),
    Artifact(
        key="edition-potsdam",
        name="The Potsdam Arbeitsstelle's Reihe IV text PDFs (IV,1–3)",
        kind="text",
        source="https://leibnizp1.bbaw.de/de/edition (files under leibniz-potsdam.bbaw.de)",
        version="IV1text.pdf, IV2text.pdf, IV3text.pdf (born-digital text layers)",
        obtained=Terms(
            "none stated on the page",
            _d(2026, 9, 11),
            "the Arbeitsstelle's page, Phase C2",
        ),
        current=Terms(
            "CC BY-NC 4.0, stated in writing 2026-10-12",
            _d(2026, 10, 12),
            "the head of the Leibniz-Edition Potsdam I and II, 2026-10-12",
            since=_d(2026, 10, 12),
        ),
        bucket="open",
        built=(
            "the reading text of IV,1–3 (§70-free); the `channel potsdam` lines go to the NC "
            "deposit of D3 under the licence stated in writing"
        ),
        notes=(
            "The page seen 2026-10-10: 'Alle hier zur Verfügung gestellten Dateien dürfen "
            "ausschließlich für nichtkommerzielle Zwecke verwendet werden'. The NC term is part "
            "of the BBAW's agreement with De Gruyter (the head, 2026-10-12). C2c re-mint of "
            "2026-10-20: 50,220 lines (STATUS.md, Key numbers). Whether NC terms reach reading "
            "text free of §70 is a lawyer-memo question: if not, the NC deposit opens up."
        ),
        channel="potsdam",
        deposit="nc",
    ),
    Artifact(
        key="edition-muenster",
        name="The Münster Forschungsstelle's Internetausgaben (Reihe II, VI)",
        kind="text",
        source="https://www.uni-muenster.de/Leibniz/ (the download page)",
        version="not fetched",
        obtained=Terms(
            "written permission required", _d(2026, 9, 11), "the download page, Phase C2"
        ),
        current=None,
        bucket="none",
        built="nothing: an operator ask, never auto-fetched",
        channel="muenster",
        deposit=None,
        used=False,
        asked="part of the Göttingen series' question (II, VI: Münster), October 2026",
    ),
    Artifact(
        key="reihe-viii-tei",
        name="Reihe VIII TEI (telota/LeibnizVIII-LaTeX_TEI)",
        kind="text",
        source="https://github.com/telota/LeibnizVIII-LaTeX_TEI",
        version="not fetched",
        obtained=Terms("CC BY-NC", _d(2026, 7, 28), "the repository, SPECS §1.4"),
        current=Terms(
            "CC BY-NC 4.0, stated in writing 2026-10-12",
            _d(2026, 10, 12),
            "the head of the Leibniz-Edition Potsdam I and II, 2026-10-12 (Series VIII)",
        ),
        bucket="nc",
        built="nothing yet (an NC channel if the owner opens it; STATUS.md Next)",
        channel="viii",
        deposit="nc",
        used=False,
    ),
    # ---- NC-quarantined and beside-the-repository material ---------------- #
    Artifact(
        key="hme-leibniz",
        name="HME-Leibniz: mathematical expressions from Leibniz's manuscripts with LaTeX",
        kind="dataset",
        source="doi:10.5281/zenodo.18804566",
        version="published 2026-02-27 (record updated 2026-06-17)",
        obtained=Terms("CC BY-NC 4.0", _d(2026, 7, 28), "the Zenodo record, SPECS §1.3"),
        current=Terms("CC BY-NC 4.0", _d(2026, 10, 21), "the Zenodo record, unchanged"),
        bucket="nc",
        built="nothing: NC-quarantined (SPECS §7.3)",
        used=False,
    ),
    Artifact(
        key="gallicorpora-plus",
        name="Gallicorpora+ (kraken print model, French 16th–19th c.)",
        kind="tool",
        source="doi:10.5281/zenodo.7410360",
        version="published 2022-12-07",
        obtained=Terms(
            "CC BY 4.0 (the Zenodo record); the repository CC0-1.0 per the operator's note",
            _d(2026, 10, 21),
            "the Zenodo record read 2026-10-21; the repository not read here",
        ),
        current=None,
        bucket="none",
        built="nothing imported: a tool run beside the repository",
        used=False,
    ),
    Artifact(
        key="yaltai",
        name="YALTAi (layout analysis for kraken)",
        kind="tool",
        source="https://github.com/PonteIneptique/YALTAi",
        version="archived 2026-04; its README points to dfine_kraken",
        obtained=Terms(
            "GPL-3.0", _d(2026, 10, 13), "the operator's note; the repository not read here"
        ),
        current=None,
        bucket="none",
        built=(
            "nothing imported: a tool run beside the Apache-2.0 codebase; the status of data it "
            "produces is a lawyer-memo question"
        ),
        used=False,
    ),
    Artifact(
        key="dfine-kraken",
        name="mittagessen/dfine_kraken",
        kind="tool",
        source="https://github.com/mittagessen/dfine_kraken",
        version="not read",
        obtained=Terms(
            "to be read", _d(2026, 10, 21), "not read: this session's GitHub access is scoped"
        ),
        current=None,
        bucket="none",
        built="nothing imported: a tool run beside the repository",
        used=False,
        asked="its licence file, to be read by the operator (2026-10-21)",
    ),
    Artifact(
        key="ultralytics-yolo",
        name="Ultralytics YOLO",
        kind="tool",
        source="https://github.com/ultralytics/ultralytics",
        version="as the operator's note of 2026-10-13 names it",
        obtained=Terms("AGPL-3.0", _d(2026, 10, 13), "the operator's note"),
        current=None,
        bucket="none",
        built=(
            "nothing imported: a tool run beside the Apache-2.0 codebase; the status of data it "
            "produces is a lawyer-memo question"
        ),
        used=False,
    ),
    Artifact(
        key="nantes-hmer",
        name="The Nantes HMER code (handwritten mathematical expression recognition)",
        kind="tool",
        source="public repository; its address is not recorded in this repository",
        version="as the operator's note of 2026-10-13 names it",
        obtained=Terms("none stated (no LICENSE file)", _d(2026, 10, 13), "the operator's note"),
        current=None,
        bucket="none",
        built="nothing imported: a tool run beside the repository",
        used=False,
        asked="the repository's address and licence, to be recorded (2026-10-21)",
    ),
)

ARTIFACTS: dict[str, Artifact] = {a.key: a for a in LICENCES}
if len(ARTIFACTS) != len(LICENCES):  # pragma: no cover — a duplicate key is a bug
    raise RuntimeError("duplicate key in the licence registry")

# The GT factory's channel keys → the registry entry that governs them.
CHANNELS: dict[str, Artifact] = {a.channel: a for a in LICENCES if a.channel}


def artifact(key: str) -> Artifact:
    """One registry entry by key (``KeyError`` for an unknown one)."""
    return ARTIFACTS[key]


def deposit_for(channels: Iterable[str], license_bucket: str) -> str | None:
    """Which D3 deposit a minted line belongs to, from the channels its source
    names and its licence bucket — ``"open"``, ``"nc"`` or ``None`` (not released).

    * A channel the registry does not know, or one whose entry says
      ``deposit=None`` (the letter pool, the Münster Internetausgaben), keeps
      the line out of every deposit.
    * One NC-deposit channel among several makes the line NC (a text joined
      from two copies is as restricted as the more restricted copy).
    * A line with no channel recorded (minted before the factory wrote the
      channel into ``source``) goes by its bucket alone: the open bucket is
      the factory's legal gate (§70-expired reading text), so it goes to the
      open deposit; an nc-bucket line without a channel is not released.
    """
    found = [CHANNELS.get(c) for c in channels]
    if any(a is None or a.deposit is None for a in found):
        return None
    if any(a.deposit == "nc" for a in found):  # type: ignore[union-attr]
        return "nc"
    if found:
        return "open" if license_bucket == "open" else None
    return "open" if license_bucket == "open" else None


# --------------------------------------------------------------------------- #
# This project's outputs: the licence each carries, and why
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Output:
    """One thing this project publishes, its licence and the reason."""

    key: str
    name: str
    licence: str
    why: str
    inputs: tuple[str, ...]  # registry keys
    decided: str  # who and when


_OWNER = "the owner's scheme of 2026-10-13 (the plan page), recorded 2026-10-21 (L1)"

OUTPUTS: tuple[Output, ...] = (
    Output(
        "code",
        "the code (this repository; D5, D6)",
        "Apache-2.0",
        "the project's own work; no third-party code is vendored but OpenSeadragon (BSD)",
        (),
        _OWNER,
    ),
    Output(
        "inventory",
        "leibniz-inventory (D1)",
        "CC0 1.0 (inventory) · katalog records CC BY 4.0 (BBAW/TELOTA)",
        "metadata derived from the GWLB's CC0 metadata; the catalogue records travel under "
        "their own CC BY 4.0",
        ("gwlb-images", "arbeitskatalog"),
        _OWNER,
    ),
    Output(
        "transcriptions",
        "the transcriptions: the site, leibniz-transcriptions (D2), the IIIF annotations (D7)",
        "CC BY 4.0",
        "machine output of a model obtained under CC BY 4.0 (the PHILIUMM HTR model, "
        "2026-07-29); PHILIUMM's relicensing of its models (CC BY-NC 4.0, 2026-10-15) was "
        "agreed to leave this project's transcriptions CC BY 4.0 (the project lead, "
        "2026-10-15). The status of a model's output under a weights licence is a "
        "lawyer-memo question",
        ("philiumm-htr-model", "philiumm-seg-model", "gwlb-images"),
        _OWNER,
    ),
    Output(
        "gt-open",
        "leibniz-gt, the open deposit of the ground truth (D3)",
        "CC BY 4.0",
        "edition reading text free of §70 (legal.REGISTRY), read through a channel with no "
        "terms of its own (`channel ia`), on line images under the Public Domain Mark",
        ("edition-ia", "gwlb-images", "philiumm-htr-model", "trocr-kurrent-xvi-xvii"),
        _OWNER,
    ),
    Output(
        "gt-nc",
        "leibniz-gt-nc, the NC-derived deposit of the ground truth (D3)",
        "CC BY-NC 4.0",
        "the same §70-free reading text read through channels with non-commercial terms: "
        "the Potsdam Arbeitsstelle's Reihe IV PDFs (CC BY-NC 4.0, stated in writing "
        "2026-10-12) and the GWLB repository's PDFs (CC BY-NC 4.0); released as a second "
        "deposit instead of left out (the owner, 2026-10-13). If the lawyer memo finds that "
        "NC terms do not reach §70-free reading text, this deposit opens up",
        ("edition-potsdam", "edition-gwlb", "gwlb-images"),
        _OWNER,
    ),
    Output(
        "model-v2",
        "leibniz-htr-v2 (D4) and K3's kraken candidate: models fine-tuned from the PHILIUMM "
        "checkpoint",
        "CC BY-NC 4.0",
        "fine-tuned from a model its makers now publish under CC BY-NC 4.0; the owner honours "
        "the change for models built from theirs (2026-10-13)",
        ("philiumm-htr-model", "philiumm-dataset", "edition-ia", "edition-potsdam", "edition-gwlb"),
        _OWNER,
    ),
    Output(
        "model-k3-trocr",
        "K3's TrOCR candidate, trained from the Bern model on K2's lines",
        "CC BY 4.0 (if released)",
        "no NC input: the Bern model is MIT and K2's lines are open-bucket edition text "
        "(the owner, 2026-10-21)",
        ("trocr-kurrent-xvi-xvii", "edition-ia", "edition-potsdam", "edition-gwlb"),
        "the owner, 2026-10-21 (the operator's note)",
    ),
    Output(
        "model-k3-ppocr",
        "K3's candidate trained from kraken's PP-OCRv6 model, if trained",
        "CC BY 4.0 (if released)",
        "no NC input: PP-OCRv6 is Apache-2.0 and K2's lines are open-bucket edition text "
        "(the owner, 2026-10-21)",
        ("ppocr-v6",),
        "the owner, 2026-10-21 (the operator's note)",
    ),
    Output(
        "reports",
        "the reports (D8) and the project statement on Zenodo",
        "CC BY 4.0",
        "the project's own prose and numbers; NC-bucket text never appears in them",
        (),
        _OWNER,
    ),
)

OUTPUT: dict[str, Output] = {o.key: o for o in OUTPUTS}
if len(OUTPUT) != len(OUTPUTS):  # pragma: no cover
    raise RuntimeError("duplicate key in the outputs table")


def output(key: str) -> Output:
    """One output by key (``KeyError`` for an unknown one)."""
    return OUTPUT[key]


def deposit_licence(deposit: str) -> str:
    """The licence of a D3 deposit (``"open"`` → CC BY 4.0, ``"nc"`` → CC BY-NC 4.0)."""
    return OUTPUT[f"gt-{deposit}"].licence


# --------------------------------------------------------------------------- #
# Tables for the CLI and the reports
# --------------------------------------------------------------------------- #

LICENCE_COLUMNS = (
    "key",
    "name",
    "kind",
    "source",
    "version",
    "licence as obtained",
    "obtained",
    "licence now",
    "seen",
    "bucket",
    "deposit",
    "used",
    "built",
)


def licence_rows(registry: tuple[Artifact, ...] = LICENCES) -> list[dict[str, str]]:
    """One flat row per artifact, in registry order (the CLI table, a report)."""
    rows: list[dict[str, str]] = []
    for a in registry:
        rows.append(
            {
                "key": a.key,
                "name": a.name,
                "kind": a.kind,
                "source": a.source,
                "version": a.version,
                "licence as obtained": a.obtained.licence,
                "obtained": a.obtained.seen.isoformat(),
                "licence now": a.licence_now.licence if a.current else "unchanged",
                "seen": a.licence_now.seen.isoformat() if a.current else "",
                "bucket": a.bucket,
                "deposit": a.deposit or "",
                "used": "yes" if a.used else "no",
                "built": a.built,
            }
        )
    return rows


def output_rows(outputs: tuple[Output, ...] = OUTPUTS) -> list[dict[str, str]]:
    """One flat row per output."""
    return [
        {
            "key": o.key,
            "output": o.name,
            "licence": o.licence,
            "why": o.why,
            "inputs": ", ".join(o.inputs),
            "decided": o.decided,
        }
        for o in outputs
    ]


__all__ = [
    "ARTIFACTS",
    "BUCKETS",
    "CHANNELS",
    "DEPOSITS",
    "FREE_AFTER_YEARS",
    "LICENCES",
    "LICENCE_COLUMNS",
    "OUTPUT",
    "OUTPUTS",
    "READING_TEXT_ONLY",
    "REGISTRY",
    "REGISTRY_DATE",
    "Artifact",
    "Output",
    "Terms",
    "Volume",
    "artifact",
    "deposit_for",
    "deposit_licence",
    "expired_volumes",
    "get_volume",
    "licence_rows",
    "output",
    "output_rows",
    "protected_volumes",
    "upcoming_expiries",
]
