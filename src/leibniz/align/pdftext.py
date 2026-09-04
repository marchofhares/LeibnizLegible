"""Extract the *reading text* of an edition piece (Phase B2).

Retro-alignment needs the constituted **reading text** of a §70-expired Academy-
Ausgabe piece, and only that. Two hard rails from SPECS §7.2 shape this module:

* **Never** extract editor introductions, apparatus, footnotes, commentary or
  indices — those are ordinary §2 works (70 years p.m.a.), not the §70-expired
  reading text. On an AA page the reading text is the larger type at the top; the
  apparatus is the smaller, stair-stepped block below it keyed by line number.
  Everything below the reading text is off-limits.
* The operator names the reading-text **page range** for a piece, so intro and
  commentary pages are never even fetched.

Older AA volumes are scanned print, so the text has to be *read* off the page.
Two backends satisfy the same small interface:

* :class:`VisionEditionExtractor` — a vision LLM (GPT-4o class) reads a page
  image and returns only the reading text, apparatus excluded, transcribed as
  printed (no expansion, no modernisation). Vision models are excellent on clean
  print (unlike on the secretary hand — see the B1 VLM numbers), which is exactly
  the regime here. **Skips gracefully without an API key** (COMMON CONTEXT).
* :func:`extract_text_layer` — for the minority of volumes shipping a real PDF
  text layer, a dependency-light pull with the same reading-text/​apparatus split
  left to the caller's page range.

Fetch helpers (:func:`fetch_ia_page_image`) pull single page images from an
Internet Archive scan of a public-domain / §70-expired volume, politely.
"""

from __future__ import annotations

import base64
import os
import time
from collections.abc import Callable, Sequence

from leibniz.htr.engines import (
    _TRANSIENT_CALL_ERRORS,
    MissingKeyError,
    _call_deadline,
    _param_error,
    _sniff_media_type,
)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# The extraction contract, spelled out so the model does the reading-text /
# apparatus separation SPECS §7.2 demands. Deliberately conservative: when unsure
# whether a block is reading text or apparatus, leave it out (precision over
# recall — a missed line costs one training pair; an apparatus line bled into the
# GT is a licensing and correctness problem).
EDITION_READING_TEXT_PROMPT = (
    "This image is one page from a printed scholarly edition of Leibniz "
    "(Akademie-Ausgabe). Transcribe ONLY the constituted READING TEXT — the main, "
    "larger-type text of the document itself.\n\n"
    "STRICTLY EXCLUDE, do not transcribe any of:\n"
    "- the critical apparatus / variant readings (the smaller-type, often "
    "stair-stepped block, usually below a rule, keyed by line numbers);\n"
    "- footnotes and editorial notes;\n"
    "- running heads, page numbers, piece numbers (e.g. 'N. 324'), and dateline "
    "headers added by the editors;\n"
    "- any editorial introduction, summary (Überlieferung/Datierung notes), or "
    "commentary.\n\n"
    "Transcribe the reading text exactly as printed: keep the original spelling, "
    "abbreviations, accents and punctuation; do NOT expand abbreviations, "
    "translate, modernise, or add anything. Preserve line breaks as printed. "
    "If the page has no reading text (all front matter/apparatus), output the "
    "single token NO_READING_TEXT. Output only the transcription."
)


class VisionEditionExtractor:
    """Read the reading text off an edition page image with a vision LLM.

    Mirrors :class:`leibniz.htr.engines.OpenAIEngine`: httpx only, graceful skip
    without a key, token-usage accounting. ``extract_page`` returns the page's
    reading text (or ``""`` for a page the model marks as having none).
    """

    def __init__(
        self,
        *,
        model: str = "gpt-4o",
        api_key: str | None = None,
        url: str = OPENAI_URL,
        prompt: str = EDITION_READING_TEXT_PROMPT,
        max_tokens: int = 2000,
        detail: str = "high",
        temperature: float | None = 0.0,
        min_interval: float = 0.2,
        max_retries: int = 4,
        timeout: float = 180.0,
        client=None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise MissingKeyError(
                "OPENAI_API_KEY not set — edition-text extraction is skipped "
                "(the aligner and its evaluation run fully without it)."
            )
        self._key = key
        self.url = url
        self.model = model
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.detail = detail
        self.temperature = temperature
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._deadline_s = timeout + 30.0
        self._sleep = sleep
        self.usage_input = 0
        self.usage_output = 0
        self._owns_client = client is None
        if client is None:
            import httpx

            self._client = httpx.Client(timeout=timeout)
        else:
            self._client = client

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> VisionEditionExtractor:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key}", "content-type": "application/json"}

    def extract_page(self, image: bytes) -> str:
        """Return the reading text of one edition page image (``""`` if none)."""
        media_type = _sniff_media_type(image)
        b64 = base64.standard_b64encode(image).decode("ascii")
        body: dict = {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64}",
                                "detail": self.detail,
                            },
                        },
                    ],
                }
            ],
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        attempt = 0
        while True:
            try:
                with _call_deadline(self._deadline_s):
                    resp = self._client.post(self.url, headers=self._headers(), json=body)
            except _TRANSIENT_CALL_ERRORS:
                if attempt < self.max_retries:
                    attempt += 1
                    self._sleep(2.0**attempt)
                    continue
                raise
            if resp.status_code in (429, 500, 502, 503, 529) and attempt < self.max_retries:
                attempt += 1
                self._sleep(2.0**attempt)
                continue
            if (
                resp.status_code == 400
                and "temperature" in body
                and _param_error(resp) == "temperature"
            ):
                # gpt-5.x-class models pin temperature to the default (see engines).
                body.pop("temperature")
                self.temperature = None
                continue
            resp.raise_for_status()
            text = self._parse(resp.json())
            return "" if text.strip() == "NO_READING_TEXT" else text

    def extract_pages(self, images: Sequence[bytes]) -> list[str]:
        out: list[str] = []
        for i, im in enumerate(images):
            if i and self.min_interval:
                self._sleep(self.min_interval)
            out.append(self.extract_page(im))
        return out

    def _parse(self, payload: dict) -> str:
        usage = payload.get("usage") or {}
        self.usage_input += int(usage.get("prompt_tokens", 0))
        self.usage_output += int(usage.get("completion_tokens", 0))
        choices = payload.get("choices") or [{}]
        return (choices[0].get("message", {}).get("content") or "").strip()


# --------------------------------------------------------------------------- #
# Text-layer fallback (volumes that ship a real PDF text layer)
# --------------------------------------------------------------------------- #


def extract_text_layer(pdf_path: str, pages: Sequence[int]) -> str:
    """Pull embedded text for ``pages`` (0-based) from a PDF's text layer.

    For the minority of AA volumes with a clean text layer this avoids a vision
    pass entirely. The caller restricts ``pages`` to the reading-text range;
    apparatus separation within a page is not attempted here (use the vision
    extractor when a page mixes reading text and apparatus). Needs ``pypdf``.
    """
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:  # pragma: no cover - optional
        raise ModuleNotFoundError(
            "extract_text_layer needs pypdf (`uv pip install pypdf`); or use the "
            "VisionEditionExtractor for scanned volumes."
        ) from exc
    reader = PdfReader(pdf_path)
    return "\n".join(reader.pages[p].extract_text() or "" for p in pages)


# --------------------------------------------------------------------------- #
# Internet Archive page images (public-domain / §70-expired volume scans)
# --------------------------------------------------------------------------- #

IA_DOWNLOAD = "https://archive.org/download"


def fetch_ia_page_image(identifier: str, page_index: int, *, client, width: int = 1500) -> bytes:
    """Fetch one page image (0-based ``page_index``) from an IA book scan.

    Internet Archive serves per-leaf JPEGs at
    ``/download/{id}/page/n{index}_w{width}.jpg``; ``client`` is a
    :class:`leibniz.net.PoliteClient` so the pull obeys the crawl rails.
    """
    url = f"{IA_DOWNLOAD}/{identifier}/page/n{page_index}_w{width}.jpg"
    return client.get_bytes(url)


__all__ = [
    "EDITION_READING_TEXT_PROMPT",
    "IA_DOWNLOAD",
    "VisionEditionExtractor",
    "extract_text_layer",
    "fetch_ia_page_image",
]
