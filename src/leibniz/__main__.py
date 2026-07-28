"""Allow ``python -m leibniz`` as an alias for the ``leibniz`` console script."""

from leibniz.cli import app

if __name__ == "__main__":  # pragma: no cover
    app()
