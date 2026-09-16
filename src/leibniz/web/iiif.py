"""IIIF Presentation 3 manifests + W3C annotation pages (deliverable D7).

A manifest per work wraps the GWLB's own image services (never our copies) and
references one annotation page per canvas; the annotation page carries the
page's transcription lines as ``supplementing`` annotations targeting the
canvas by ``#xywh``. Every annotation embeds the SPECS §4.5 provenance tuple
under the ``leibniz:`` namespace (model@version, run, confidence, status,
language, polygon) so a Mirador user sees the same honest labels the viewer
shows. Pure functions over store rows; the API serialises them.
"""

from __future__ import annotations

from leibniz import db
from leibniz.web import attribution as attr
from leibniz.web.geometry import line_bbox, polygon_points

PRESENTATION_CONTEXT = "http://iiif.io/api/presentation/3/context.json"
LEIBNIZ_NS = "https://github.com/marchofhares/leibnizlegible/ns#"
CONTEXT = [PRESENTATION_CONTEXT, {"leibniz": LEIBNIZ_NS}]

LANG_TAGS = {"la": "la", "fr": "fr", "de": "de", "mixed": "mul", "unknown": "und"}


def manifest_id(base_url: str, work_id: str) -> str:
    return f"{base_url}/manifests/{work_id}"


def canvas_id(base_url: str, page: db.Page) -> str:
    return f"{base_url}/manifests/{page.work_id}/canvas/{page.seq}"


def annotation_page_id(base_url: str, page_id: str) -> str:
    return f"{base_url}/annotations/{page_id}"


def _image_body(page: db.Page) -> dict:
    if page.delivery == "iiif" and page.image_service_url:
        return {
            "id": f"{page.image_service_url}/full/max/0/default.jpg",
            "type": "Image",
            "format": "image/jpeg",
            "height": page.height,
            "width": page.width,
            "service": [
                {"id": page.image_service_url, "type": "ImageService2", "profile": "level1"}
            ],
        }
    return {
        "id": page.image_url,
        "type": "Image",
        "format": "image/jpeg",
        "height": page.height,
        "width": page.width,
    }


def build_canvas(
    page: db.Page, *, base_url: str, n_lines: int | None = None, source_url: str | None = None
) -> dict:
    """A canvas painting ``page``'s image. ``source_url`` is the GWLB's URI when
    the painted image is a mirror copy, recorded in the canvas metadata."""
    cid = canvas_id(base_url, page)
    label = page.label or str(page.seq)
    canvas: dict = {
        "id": cid,
        "type": "Canvas",
        "label": {"none": [label]},
        "height": page.height,
        "width": page.width,
        "items": [
            {
                "id": f"{cid}/page",
                "type": "AnnotationPage",
                "items": [
                    {
                        "id": f"{cid}/page/image",
                        "type": "Annotation",
                        "motivation": "painting",
                        "body": _image_body(page),
                        "target": cid,
                    }
                ],
            }
        ],
        "annotations": [{"id": annotation_page_id(base_url, page.id), "type": "AnnotationPage"}],
    }
    if page.thumb_url:
        canvas["thumbnail"] = [{"id": page.thumb_url, "type": "Image", "format": "image/jpeg"}]
    meta = [{"label": {"en": ["Pipeline status"]}, "value": {"en": [page.status]}}]
    if page.status == "skipped" and page.skip_reason:
        meta.append({"label": {"en": ["Skip reason"]}, "value": {"en": [page.skip_reason]}})
    if n_lines is not None:
        meta.append({"label": {"en": ["Transcribed lines"]}, "value": {"en": [str(n_lines)]}})
    if source_url:
        meta.append({"label": {"en": ["Source image (GWLB)"]}, "value": {"none": [source_url]}})
    canvas["metadata"] = meta
    return canvas


def build_manifest(
    work: db.Work,
    pages: list[db.Page],
    *,
    base_url: str,
    line_counts: dict[str, int] | None = None,
    images_mirrored: bool = False,
    sources: dict[str, str | None] | None = None,
) -> dict:
    """A Presentation 3 manifest for a work: the images as ``pages`` name them
    (the GWLB's, or the mirror's when ``images_mirrored`` — then ``sources``
    maps page ids to the GWLB URIs recorded per canvas), the annotations ours."""
    counts = line_counts or {}
    srcs = sources or {}
    title = work.title or (work.shelfmarks[0] if work.shelfmarks else work.gwlb_object_id)
    manifest: dict = {
        "@context": CONTEXT,
        "id": manifest_id(base_url, work.gwlb_object_id),
        "type": "Manifest",
        "label": {"none": [title]},
        "summary": {
            "en": [
                "Machine transcription with per-line confidence and provenance "
                "(Leibniz Legible). Not an edition."
            ]
        },
        "metadata": [
            {"label": {"en": ["Shelfmark"]}, "value": {"none": list(work.shelfmarks or [])}},
            {"label": {"en": ["Collection"]}, "value": {"none": [work.set_name]}},
            {"label": {"en": ["GWLB object"]}, "value": {"none": [work.gwlb_object_id]}},
            {"label": {"en": ["Transcription"]}, "value": {"en": [attr.TRANSCRIPTIONS]}},
        ],
        "requiredStatement": {
            "label": {"en": ["Attribution"]},
            "value": {"en": [attr.images_line(images_mirrored), attr.KATALOG]},
        },
        "rights": attr.PDM_URL,
        "provider": [
            {
                "id": attr.GWLB_COLLECTIONS,
                "type": "Agent",
                "label": {"none": [attr.GWLB_NAME]},
                "homepage": [
                    {
                        "id": attr.GWLB_RESOLVE.format(work_id=work.gwlb_object_id),
                        "type": "Text",
                        "label": {"none": ["GWLB digital collections"]},
                        "format": "text/html",
                    }
                ],
            }
        ],
        "homepage": [
            {
                "id": f"{base_url}/work/{work.gwlb_object_id}",
                "type": "Text",
                "label": {"en": ["Leibniz Legible"]},
                "format": "text/html",
            }
        ],
        "items": [
            build_canvas(p, base_url=base_url, n_lines=counts.get(p.id), source_url=srcs.get(p.id))
            for p in pages
        ],
    }
    if work.manifest_url:
        manifest["seeAlso"] = [
            {
                "id": work.manifest_url,
                "type": "Dataset",
                "label": {"en": ["GWLB IIIF manifest (Presentation 2)"]},
                "format": "application/ld+json",
                "profile": "http://iiif.io/api/presentation/2/context.json",
            }
        ]
    return manifest


def build_annotation_page(
    page: db.Page,
    lines: list[db.Line],
    *,
    base_url: str,
    run_dates: dict[int, str] | None = None,
    images_mirrored: bool = False,
) -> dict:
    """The W3C AnnotationPage carrying a page's transcription lines. ``page`` is
    the store's row: ``leibniz:imageUri`` names the GWLB source image whatever
    the viewer displays."""
    dates = run_dates or {}
    cid = canvas_id(base_url, page)
    apid = annotation_page_id(base_url, page.id)
    items: list[dict] = []
    for ln in lines:
        if not ln.text:
            continue
        bbox = line_bbox(ln, page)
        target: str | dict = cid
        if bbox:
            target = f"{cid}#xywh={bbox['x']},{bbox['y']},{bbox['w']},{bbox['h']}"
        ann: dict = {
            "id": f"{apid}/{ln.line_seq}",
            "type": "Annotation",
            "motivation": "supplementing",
            "body": {
                "type": "TextualBody",
                "value": ln.text,
                "format": "text/plain",
                "language": LANG_TAGS.get(ln.lang or "unknown", "und"),
            },
            "target": target,
            "leibniz:lineId": ln.id,
            "leibniz:status": ln.status,
            "leibniz:confidence": ln.conf,
            "leibniz:model": ln.model,
            "leibniz:runId": ln.run_id,
            "leibniz:runAt": dates.get(ln.run_id or -1),
            "leibniz:imageUri": page.image_service_url or page.image_url,
        }
        poly = polygon_points(ln)
        if poly:
            ann["leibniz:polygon"] = poly
        if ln.source:
            ann["leibniz:source"] = ln.source
        items.append(ann)
    return {
        "@context": CONTEXT,
        "id": apid,
        "type": "AnnotationPage",
        "label": {"en": [f"Transcription of {page.id} (machine output, not an edition)"]},
        "leibniz:attribution": attr.attribution(images_mirrored),
        "items": items,
    }


__all__ = [
    "CONTEXT",
    "LEIBNIZ_NS",
    "annotation_page_id",
    "build_annotation_page",
    "build_canvas",
    "build_manifest",
    "canvas_id",
    "manifest_id",
]
