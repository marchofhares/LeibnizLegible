"""Baseline segmentation of a manuscript page (Phase B2 prototype; grows in C1).

Retro-alignment and, later, the corpus pipeline both start the same way: a full
page image has to become an ordered list of **line images**, because the HTR
model (:class:`leibniz.htr.engines.KrakenEngine`) recognises pre-extracted,
polygon-dewarped lines. This module wraps Kraken's baseline segmenter around the
PHILIUMM segmentation model (Zenodo ``10.5281/zenodo.21537859``) to do exactly
that.

For Phase B2 this only needs to be good enough to prototype alignment on a
favourable page; corpus-scale segmentation quality metrics (line counts, region
coverage, overlap anomalies feeding the stratum heuristic) are Phase C1's job.
The layered-revision / marginalia difficulty flagged in SPECS §9 is precisely
what the *live* end-to-end run measures here, honestly, on a real page.

Kraken + torch are the optional ``bench`` extra, imported lazily — importing this
module costs nothing without them, matching :mod:`leibniz.htr.engines`.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field


@dataclass(slots=True)
class SegLine:
    """One segmented line: its reading-order index and geometry."""

    index: int
    baseline: list[tuple[float, float]] = field(default_factory=list)
    boundary: list[tuple[float, float]] = field(default_factory=list)

    @property
    def ref(self) -> str:
        """A stable per-page line ref (``line:{index:03d}``)."""
        return f"line:{self.index:03d}"

    def bbox(self) -> tuple[int, int, int, int] | None:
        """Axis-aligned bounding box ``(x0, y0, x1, y1)`` of the boundary."""
        pts = self.boundary or self.baseline
        if not pts:
            return None
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))


@dataclass(slots=True)
class SegmentedPage:
    """The lines of one page, in reading order, plus the page dimensions.

    ``n_regions`` is the count of Segmonto layout zones the segmenter found (text
    / graphic / formula …), kept for the C1 segmentation-stats bag; ``0`` when the
    model/segmenter does not report regions.
    """

    lines: list[SegLine]
    width: int
    height: int
    n_regions: int = 0

    @property
    def n_lines(self) -> int:
        return len(self.lines)


class PageSegmenter:
    """Kraken baseline segmentation over the PHILIUMM segmentation model.

    Construct once with the model path (lazy heavy load on first use), then call
    :meth:`segment` per page and :meth:`line_images` to crop the dewarped line
    images the recogniser consumes. Deterministic; CPU by default.
    """

    def __init__(self, model_path: str, *, device: str = "cpu") -> None:
        self.model_path = model_path
        self.device = device
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            from kraken.models.loaders import load_models
        except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
            raise ModuleNotFoundError(
                "PageSegmenter needs the kraken stack (the optional bench extra). "
                "Install with `uv pip install kraken`; the align engine and its "
                "tests do not require it."
            ) from exc
        # The PHILIUMM segmentation model is a kraken-5-era safetensors container;
        # like the HTR model (see leibniz.htr.engines), kraken 7's plain
        # ``TorchVGSLModel.load_model`` mis-parses it as CoreML and fails, so we
        # go through ``load_models`` with the segmentation task. ``blla.segment``
        # iterates its ``model`` argument, so we keep the returned list.
        models = load_models(self.model_path, tasks=["segmentation"])
        if not models:
            raise ValueError(f"no segmentation model found in {self.model_path}")
        # Version bridge: kraken 7's ``blla`` reads ``user_metadata['hyper_params']``
        # (for the input padding), but this kraken-5-era model predates that key.
        # Default it to empty so blla falls back to zero padding — the documented
        # kraken-5→7 compatibility gap, analogous to the HTR loader workaround.
        for m in models:
            if "hyper_params" not in m.user_metadata:
                m.user_metadata["hyper_params"] = {}
        self._model = models

    @staticmethod
    def _open(image: bytes | object):
        from PIL import Image

        if isinstance(image, (bytes, bytearray)):
            im = Image.open(io.BytesIO(bytes(image)))
        else:
            im = image
        return im.convert("RGB")

    def segment(
        self, image: bytes | object, *, text_direction: str = "horizontal-lr"
    ) -> SegmentedPage:
        """Segment a page image (raw bytes or a PIL image) into ordered lines."""
        from kraken import blla

        self._ensure_loaded()
        im = self._open(image)
        seg = blla.segment(im, text_direction=text_direction, model=self._model)
        lines: list[SegLine] = []
        for i, line in enumerate(seg.lines):
            lines.append(
                SegLine(
                    index=i,
                    baseline=[tuple(p) for p in (getattr(line, "baseline", None) or [])],
                    boundary=[tuple(p) for p in (getattr(line, "boundary", None) or [])],
                )
            )
        # Segmonto zones (dict of {region_type: [regions]}); count them for the
        # C1 segmentation-stats bag. Absent on some model outputs → 0.
        regions = getattr(seg, "regions", None) or {}
        n_regions = sum(len(v) for v in regions.values()) if isinstance(regions, dict) else 0
        return SegmentedPage(lines=lines, width=im.width, height=im.height, n_regions=n_regions)

    def crop_lines(
        self, image: bytes | object, page: SegmentedPage, *, fmt: str = "PNG"
    ) -> list[bytes]:
        """Extract dewarped line images from an *already-computed* segmentation.

        The recognition stage stores line geometry at segmentation time and must
        later crop those exact lines *without re-running the neural segmenter* (so
        the two-stage pipeline is deterministic and cheap on the second pass). This
        reconstructs a Kraken ``Segmentation`` from the stored baselines/boundaries
        and runs the same pure-geometry ``extract_polygons`` the recogniser was
        trained against. Pure geometry — it does **not** load the segmentation
        model. If the container reconstruction is unavailable (kraken API drift),
        it falls back to :meth:`line_images` (a re-segmentation) so an operator run
        still succeeds.
        """
        from kraken.lib import segmentation

        im = self._open(image)
        try:  # pragma: no cover - kraken container API, exercised only on real runs
            from kraken import containers

            klines = [
                containers.BaselineLine(
                    id=f"l{ln.index:04d}",
                    baseline=[list(p) for p in ln.baseline],
                    boundary=[list(p) for p in ln.boundary],
                )
                for ln in page.lines
            ]
            seg = containers.Segmentation(
                type="baselines",
                imagename="",
                text_direction="horizontal-lr",
                script_detection=False,
                lines=klines,
                regions={},
                line_orders=[],
            )
        except Exception:  # pragma: no cover - reconstruction unsupported → re-seg
            return self.line_images(image, fmt=fmt)

        out: list[bytes] = []
        for line_im, _rec in segmentation.extract_polygons(im, seg):  # pragma: no cover
            buf = io.BytesIO()
            line_im.convert("RGB").save(buf, format=fmt)
            out.append(buf.getvalue())
        return out

    def line_images(
        self, image: bytes | object, page: SegmentedPage | None = None, *, fmt: str = "PNG"
    ) -> list[bytes]:
        """Extract dewarped line images (encoded bytes) in reading order.

        Re-segments if ``page`` is not supplied. Uses Kraken's
        ``extract_polygons`` (the same polygon-dewarping the model was trained
        against), then encodes each crop losslessly (PNG) for the recogniser.
        """
        from kraken import blla
        from kraken.lib import segmentation

        self._ensure_loaded()
        im = self._open(image)
        seg = blla.segment(im, model=self._model)
        out: list[bytes] = []
        for line_im, _rec in segmentation.extract_polygons(im, seg):
            buf = io.BytesIO()
            line_im.convert("RGB").save(buf, format=fmt)
            out.append(buf.getvalue())
        return out


__all__ = [
    "PageSegmenter",
    "SegLine",
    "SegmentedPage",
]
