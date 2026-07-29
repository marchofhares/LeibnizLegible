"""End-to-end retro-alignment on one real piece (Phase B2 orchestration).

Ties the live components into the pipeline the gate is really about:

    GWLB IIIF page → segment (PHILIUMM seg model) → recognise (PHILIUMM HTR)
        → align to §70-expired edition reading text → minted gt_lines

:func:`run_prototype` takes a GWLB work id, the canvas indices of the piece, and
the piece's constituted reading text (extracted by :mod:`leibniz.align.pdftext`),
and returns a :class:`PrototypeRun` with the segmentation/HTR facts and the
:class:`~leibniz.align.align.AlignmentResult`. Images are pulled straight from
GWLB's IIIF Image API — never rehosted (SPECS §3.4) — via the polite client.

The heavy stack (kraken/torch) is used only inside the seg + HTR steps and
imported lazily there, so importing this module stays cheap.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from leibniz.align.align import DEFAULT_THRESHOLD, AlignmentResult, HtrLine, align_piece
from leibniz.align.normalize import DEFAULT_NORM, AlignNorm
from leibniz.net import PoliteClient, default_user_agent

GWLB_CONTENT = "https://digitale-sammlungen.gwlb.de/content"


@dataclass(slots=True)
class PrototypeRun:
    """The result of one end-to-end prototype alignment."""

    work_id: str
    canvas_indices: list[int]
    n_seg_lines: int
    htr_lines: list[HtrLine]
    result: AlignmentResult
    edition_source: str
    edition_chars: int
    per_page_line_counts: list[int] = field(default_factory=list)


def iiif_service_urls(work_id: str, *, client: PoliteClient) -> list[str]:
    """The IIIF Image API base URLs for every canvas of a work, in page order."""
    manifest = client.get_json(f"{GWLB_CONTENT}/{work_id}/manifest.json")
    out: list[str] = []
    for canvas in manifest["sequences"][0]["canvases"]:
        svc = canvas["images"][0]["resource"].get("service", {})
        base = (svc.get("@id") or "").rstrip("/")
        if base:
            out.append(base)
    return out


def fetch_iiif_images(
    work_id: str,
    canvas_indices: list[int],
    *,
    client: PoliteClient,
    region_size: str = "full",
) -> list[bytes]:
    """Fetch full-resolution page images for the given canvases from GWLB IIIF.

    ``region_size`` maps to the IIIF Image API size (``full`` = native; e.g.
    ``1600,`` for a width-capped derivative). Images come directly from GWLB's
    Image API — the project never rehosts them (SPECS §3.4).
    """
    services = iiif_service_urls(work_id, client=client)
    out: list[bytes] = []
    for idx in canvas_indices:
        base = services[idx]
        out.append(client.get_bytes(f"{base}/full/{region_size}/0/default.jpg"))
    return out


def run_prototype(
    *,
    work_id: str,
    canvas_indices: list[int],
    edition_text: str,
    seg_model_path: str,
    htr_model_path: str,
    edition_source: str,
    threshold: float = DEFAULT_THRESHOLD,
    norm: AlignNorm = DEFAULT_NORM,
    client: PoliteClient | None = None,
    region_size: str = "full",
    htr_batch_size: int = 8,
) -> PrototypeRun:
    """Fetch → segment → recognise → align one piece; return the run.

    ``canvas_indices`` are 0-based positions in the work's IIIF sequence. The
    segmenter and recogniser are the PHILIUMM models; ``edition_text`` is the
    piece's reading text (§70-expired), aligned across all its pages at once so a
    word or sentence spanning a page break still aligns.
    """
    from leibniz.htr.engines import KrakenEngine
    from leibniz.layout.segment import PageSegmenter

    owns = client is None
    client = client or PoliteClient(user_agent=default_user_agent())
    try:
        images = fetch_iiif_images(work_id, canvas_indices, client=client, region_size=region_size)
    finally:
        if owns:
            client.close()

    segmenter = PageSegmenter(seg_model_path)
    engine = KrakenEngine(htr_model_path, batch_size=htr_batch_size)

    htr_lines: list[HtrLine] = []
    per_page_counts: list[int] = []
    for canvas_idx, image in zip(canvas_indices, images, strict=True):
        line_imgs = segmenter.line_images(image)
        per_page_counts.append(len(line_imgs))
        texts = engine.transcribe(line_imgs) if line_imgs else []
        for line_seq, text in enumerate(texts):
            htr_lines.append(
                HtrLine(
                    ref=f"{work_id}:{canvas_idx:04d}:{line_seq:03d}",
                    text=text,
                    meta={"work_id": work_id, "canvas": canvas_idx, "line_seq": line_seq},
                )
            )

    result = align_piece(htr_lines, edition_text, norm=norm, threshold=threshold)
    return PrototypeRun(
        work_id=work_id,
        canvas_indices=list(canvas_indices),
        n_seg_lines=len(htr_lines),
        htr_lines=htr_lines,
        result=result,
        edition_source=edition_source,
        edition_chars=len(edition_text),
        per_page_line_counts=per_page_counts,
    )


__all__ = [
    "GWLB_CONTENT",
    "PrototypeRun",
    "fetch_iiif_images",
    "iiif_service_urls",
    "run_prototype",
]
