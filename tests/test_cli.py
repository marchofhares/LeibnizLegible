"""Smoke tests: the `leibniz` CLI is importable and runs.

Offline, no network. The primary check invokes the Typer app in-process; a
second check exercises the real module entry point via a subprocess so the
packaging (`python -m leibniz`) is validated too.
"""

from __future__ import annotations

import subprocess
import sys

from typer.testing import CliRunner

from leibniz import __version__
from leibniz.cli import app

runner = CliRunner()


def test_version_flag_runs() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
    assert "leibniz" in result.stdout


def test_short_version_flag_runs() -> None:
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_flag_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "info" in result.stdout  # the registered subcommand is listed


def test_no_args_shows_help() -> None:
    # no_args_is_help=True => bare invocation renders help (Typer's conventional
    # "no command given" exit code is 2; what matters is that help is shown).
    result = runner.invoke(app, [])
    assert "Usage" in result.output


def test_info_command_runs() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Leibniz Legible" in result.stdout


def test_module_entrypoint_version() -> None:
    # `python -m leibniz --version` must work via the installed package.
    proc = subprocess.run(
        [sys.executable, "-m", "leibniz", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout
