"""ASGI factory for process managers.

    uvicorn --factory leibniz.web.asgi:app --workers 2 --host 127.0.0.1 --port 8000

Reads :class:`leibniz.web.settings.ServeSettings` from the environment (the
variables ``deploy/env.example`` lists). ``leibniz serve --workers N`` uses this
same entry point after exporting its options to the environment, because
uvicorn's worker processes must each build the application themselves.
"""

from __future__ import annotations

from fastapi import FastAPI

from leibniz.web.settings import ServeSettings


def app() -> FastAPI:
    """Build the application from the environment (uvicorn ``--factory`` target)."""
    return ServeSettings.from_env().build_app()


__all__ = ["app"]
