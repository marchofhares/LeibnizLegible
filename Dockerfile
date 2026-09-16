# syntax=docker/dockerfile:1.7
# Leibniz Legible — the serving layer (JSON API, IIIF manifests + annotations,
# the viewer) in one image. The store is mounted, never baked in; images are
# never proxied (the viewer loads them from the GWLB). See deploy/README.md.
#
#   docker build -t leibniz-legible .
#   docker run --rm -p 8000:8000 -v /path/to/data:/srv/leibniz/data leibniz-legible

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
# Runtime deps + the `web` extra only; the package itself is installed
# non-editable so the source tree is not needed at runtime.
RUN uv sync --frozen --no-dev --extra web --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --system --uid 1000 --create-home --home-dir /srv/leibniz \
        --shell /usr/sbin/nologin leibniz \
    && mkdir -p /srv/leibniz/data \
    && chown -R leibniz:leibniz /srv/leibniz
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    LEIBNIZ_DB_PATH=/srv/leibniz/data/inventory.sqlite \
    LEIBNIZ_INDEX_PATH=/srv/leibniz/data/search.sqlite \
    LEIBNIZ_HOST=0.0.0.0 \
    LEIBNIZ_PORT=8000
USER leibniz
WORKDIR /srv/leibniz
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4).status == 200 else 1)"
CMD ["leibniz", "serve"]
