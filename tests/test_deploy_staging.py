"""The staging kit (deploy/README.md §14) beside its production counterparts.

Each staging file is the production file with the intended differences and
nothing else; the two shell scripts parse (and pass shellcheck where it is
installed) and name the same paths, port, domain and index as the examples.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[1] / "deploy"
STAGING_DOMAIN = "staging.leibnizlegible.com"
STAGING_DIR = "/opt/leibniz-legible-staging"
STAGING_ENV = "/etc/leibniz-legible/staging.env"
STAGING_INDEX = "leibniz_pages_staging"


def _lines(name: str) -> list[str]:
    """Non-blank, non-comment lines, as written."""
    text = (DEPLOY / name).read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def _kv(name: str) -> dict[str, str]:
    """KEY=VALUE lines of an env example (set lines only; comments skipped)."""
    out: dict[str, str] = {}
    for ln in _lines(name):
        key, _, value = ln.partition("=")
        out[key] = value
    return out


def test_staging_unit_is_the_production_unit_with_its_own_paths() -> None:
    prod, staging = _lines("leibniz-legible.service"), _lines("leibniz-legible-staging.service")
    assert len(prod) == len(staging), "the units must keep the same lines in the same order"
    changed = {a.partition("=")[0]: (a, b) for a, b in zip(prod, staging, strict=True) if a != b}
    assert set(changed) == {"Description", "WorkingDirectory", "EnvironmentFile", "ExecStart"}
    assert changed["WorkingDirectory"][1] == f"WorkingDirectory={STAGING_DIR}"
    assert changed["EnvironmentFile"][1] == f"EnvironmentFile={STAGING_ENV}"
    assert changed["ExecStart"][1] == f"ExecStart={STAGING_DIR}/.venv/bin/leibniz serve"
    # the sandbox and the one writable path are untouched
    for line in ("ProtectSystem=strict", "ReadWritePaths=/var/lib/leibniz-legible", "User=leibniz"):
        assert line in staging


def test_staging_env_differs_from_production_in_four_values() -> None:
    prod, staging = _kv("env.example"), _kv("staging.env.example")
    assert set(prod) == set(staging), "the same variables, no more and no fewer"
    changed = {k for k in prod if prod[k] != staging[k]}
    assert changed == {"LEIBNIZ_PORT", "LEIBNIZ_WORKERS", "LEIBNIZ_BASE_URL", "LEIBNIZ_RATE_LIMIT"}
    assert staging["LEIBNIZ_PORT"] == "8001" and prod["LEIBNIZ_PORT"] == "8000"
    assert staging["LEIBNIZ_WORKERS"] == "1"
    assert staging["LEIBNIZ_BASE_URL"] == f"https://{STAGING_DOMAIN}"
    assert staging["LEIBNIZ_RATE_LIMIT"] == "0"
    # shared with the live site: the store copy and, until --index, the live index
    assert staging["LEIBNIZ_DB_PATH"] == prod["LEIBNIZ_DB_PATH"]
    assert staging["LEIBNIZ_MEILI_INDEX"] == prod["LEIBNIZ_MEILI_INDEX"] == "leibniz_pages"
    assert staging["MEILI_API_KEY"] == "" and staging["LEIBNIZ_HOST"] == "127.0.0.1"
    for name in ("env.example", "staging.env.example"):
        text = (DEPLOY / name).read_text(encoding="utf-8")
        assert "\n# LEIBNIZ_CALCULEMUS_URL=" in text, f"{name}: the game switch stays commented out"
    assert STAGING_INDEX in (DEPLOY / "staging.env.example").read_text(encoding="utf-8")


def test_staging_caddy_block_is_the_production_block_behind_a_password() -> None:
    text = (DEPLOY / "staging.caddy.example").read_text(encoding="utf-8")
    staging = {ln.strip() for ln in _lines("staging.caddy.example")}
    # one site, named literally (README §13: never a {$VAR} fallback in a sibling block)
    assert text.count(f"\n{STAGING_DOMAIN} {{\n") == 1
    assert not any("{$" in ln for ln in staging)
    # what staging adds: basic auth with the placeholders the installer fills, noindex
    assert "basic_auth {" in staging and "__STAGING_USER__ __STAGING_HASH__" in staging
    assert 'X-Robots-Tag "noindex, nofollow"' in staging
    assert "reverse_proxy 127.0.0.1:8001" in staging
    assert "output file /var/log/caddy/leibniz-legible-staging.log {" in staging
    # everything in the production site block, verbatim, except the two lines above
    prod = (DEPLOY / "Caddyfile").read_text(encoding="utf-8").splitlines()
    start = prod.index("{$LEIBNIZ_DOMAIN:localhost} {")
    end = prod.index("}", start)
    block = [
        ln.strip() for ln in prod[start + 1 : end] if ln.strip() and not ln.lstrip().startswith("#")
    ]
    assert block, "the production block was not found"
    for line in block:
        if line.startswith("reverse_proxy ") or line.startswith("output file "):
            continue
        assert line in staging, f"production directive missing from the staging block: {line}"


def test_scripts_parse_and_agree_with_the_examples() -> None:
    install = "\n".join(_lines("staging-install.sh"))  # the code, comments left out
    deploy = "\n".join(_lines("staging.sh"))
    for name in ("staging-install.sh", "staging.sh"):
        path = DEPLOY / name
        assert os.access(path, os.X_OK), f"{name} must be executable"
        subprocess.run(["bash", "-n", str(path)], check=True)
    if shutil.which("shellcheck"):
        subprocess.run(
            ["shellcheck", str(DEPLOY / "staging-install.sh"), str(DEPLOY / "staging.sh")],
            check=True,
        )
    for text in (install, deploy):
        assert f"STAGING_DOMAIN={STAGING_DOMAIN}" in text
        assert "STAGING_PORT=8001" in text
        assert f"STAGING_DIR={STAGING_DIR}" in text
        assert "UNIT=leibniz-legible-staging" in text
    assert f"STAGING_ENV={STAGING_ENV}" in deploy and "CONF_DIR/staging.env" in install
    assert f"STAGING_INDEX={STAGING_INDEX}" in deploy and "LIVE_INDEX=leibniz_pages" in deploy
    # the installer fills the example's placeholders and never names the password
    assert "__STAGING_USER__" in install and "__STAGING_HASH__" in install
    assert "caddy hash-password" in install and "--plaintext" not in install
    assert "systemctl reload caddy" in install and "systemctl restart caddy" not in install
    # the access log is created for the caddy user before `caddy validate`, which runs
    # as root and would otherwise create it as root; the reload, as caddy, cannot open that
    assert "LOG_FILE=/var/log/caddy/leibniz-legible-staging.log" in install
    assert (
        'chown caddy:caddy "$LOG_FILE"' in install and "chown caddy:caddy /var/log/caddy" in install
    )
    # the index build goes through the CLI option Task 1 added, with the master key
    assert 'index build --backend meili --meili-index "$STAGING_INDEX"' in deploy
    assert (
        "deploy/meili-search-key.sh" in deploy
    )  # the key's scope, leibniz_pages*, covers the staging index


def test_search_key_scope_covers_the_staging_index() -> None:
    """deploy/meili-search-key.sh scopes the serving key to leibniz_pages*; the
    staging index name must stay under that pattern, or staging could not search."""
    script = (DEPLOY / "meili-search-key.sh").read_text(encoding="utf-8")
    assert '"indexes": ["leibniz_pages*"]' in script
    assert STAGING_INDEX.startswith("leibniz_pages")


@pytest.mark.parametrize("section", ["## 14. ", "staging-install.sh", "staging.sh", STAGING_DOMAIN])
def test_runbook_has_the_staging_section(section: str) -> None:
    assert section in (DEPLOY / "README.md").read_text(encoding="utf-8")
