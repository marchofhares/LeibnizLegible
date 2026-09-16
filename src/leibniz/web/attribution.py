"""Attribution and rights strings — one source for the API, the manifests, the
viewer and the dataset cards (SPECS §7.1, §3.4/§3.5)."""

from __future__ import annotations

GWLB_NAME = "Gottfried Wilhelm Leibniz Bibliothek – Niedersächsische Landesbibliothek, Hannover"
GWLB_COLLECTIONS = "https://digitale-sammlungen.gwlb.de/"
GWLB_RESOLVE = "https://digitale-sammlungen.gwlb.de/resolve?id={work_id}"
PDM_URL = "http://creativecommons.org/publicdomain/mark/1.0/"
CC0_URL = "http://creativecommons.org/publicdomain/zero/1.0/"
CC_BY_URL = "http://creativecommons.org/licenses/by/4.0/"

KATALOG_NAME = "Leibniz-Katalog / Arbeitskatalog der Leibniz-Edition"
KATALOG_URL = "https://leibniz-katalog.bbaw.de/"
KATALOG_PUBLISHER = "Berlin-Brandenburgische Akademie der Wissenschaften (TELOTA)"

PHILIUMM_MODEL = "FoNDUE-GD_v2_ft_Leibniz"
PHILIUMM_MODEL_DOI = "10.5281/zenodo.21457538"
PHILIUMM_SEG_DOI = "10.5281/zenodo.21537859"
PHILIUMM_GT = "DenisaB/htr_leibniz_dataset_v1"

PROJECT_NAME = "Leibniz Legible"
PROJECT_URL = "https://github.com/marchofhares/leibnizlegible"
PROJECT_ISSUES = "https://github.com/marchofhares/leibnizlegible/issues"

IMAGES = (
    f"Images: {GWLB_NAME} ({GWLB_COLLECTIONS}). Manuscript scans carry the Public Domain "
    "Mark 1.0 and are loaded directly from the GWLB's own servers; nothing is rehosted."
)
IMAGES_MIRROR = (
    f"Images: {GWLB_NAME} ({GWLB_COLLECTIONS}). Manuscript scans carry the Public Domain "
    "Mark 1.0. The copies shown are the GWLB's own delivery derivatives, served from Leibniz "
    "Legible's mirror; every page links to its original at the GWLB, whose master files remain "
    "the authoritative source."
)
KATALOG = f"Catalogue: {KATALOG_NAME} ({KATALOG_URL}), {KATALOG_PUBLISHER}, CC BY 4.0."
TRANSCRIPTIONS = (
    f"Transcriptions: {PROJECT_NAME}, machine output of the PHILIUMM HTR model "
    f"{PHILIUMM_MODEL} (ERC PHILIUMM, doi:{PHILIUMM_MODEL_DOI}, CC BY 4.0), with per-line "
    "confidence and provenance. Not an edition; subordinate to the Akademie-Ausgabe. CC BY 4.0."
)
HONESTY = (
    "Machine transcription. Not an edition. Errors are expected: about 8% character error "
    "rate on Latin and French lines, higher on German."
)


def images_line(mirrored: bool = False) -> str:
    """The images line: where the pixels come from, honestly (see ``web/images.py``)."""
    return IMAGES_MIRROR if mirrored else IMAGES


def attribution(images_mirrored: bool = False) -> dict[str, str]:
    """The three attribution lines, as the API and the manifests carry them.

    The dataset cards always use :data:`IMAGES` — they reference the GWLB's
    URIs and rehost nothing; the web surfaces pass ``images_mirrored`` per the
    operator's configuration.
    """
    return {
        "images": images_line(images_mirrored),
        "katalog": KATALOG,
        "transcriptions": TRANSCRIPTIONS,
    }


__all__ = [
    "CC0_URL",
    "CC_BY_URL",
    "GWLB_COLLECTIONS",
    "GWLB_NAME",
    "GWLB_RESOLVE",
    "HONESTY",
    "IMAGES",
    "IMAGES_MIRROR",
    "KATALOG",
    "KATALOG_NAME",
    "KATALOG_PUBLISHER",
    "KATALOG_URL",
    "PDM_URL",
    "PHILIUMM_GT",
    "PHILIUMM_MODEL",
    "PHILIUMM_MODEL_DOI",
    "PHILIUMM_SEG_DOI",
    "PROJECT_ISSUES",
    "PROJECT_NAME",
    "PROJECT_URL",
    "TRANSCRIPTIONS",
    "attribution",
    "images_line",
]
