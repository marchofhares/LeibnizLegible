"""Serve settings from the environment, and the ASGI factory built from them."""

from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

from leibniz.web.cli import listening_socket
from leibniz.web.settings import DEFAULT_RATE_BURST, DEFAULT_RATE_LIMIT, ServeSettings


def test_defaults() -> None:
    s = ServeSettings.from_env({})
    assert s.backend == "fts5" and s.host == "127.0.0.1" and s.port == 8000
    assert s.workers == 1 and s.base_url is None and s.meili_key is None
    assert s.rate_limit == DEFAULT_RATE_LIMIT and s.rate_burst == DEFAULT_RATE_BURST


def test_env_overrides_and_fallbacks(tmp_path) -> None:
    env = {
        "LEIBNIZ_DB_PATH": str(tmp_path / "x.sqlite"),
        "LEIBNIZ_SEARCH_BACKEND": "MEILI",
        "MEILI_URL": "http://m:7700",
        "MEILI_MASTER_KEY": "master",
        "LEIBNIZ_PORT": "9000",
        "LEIBNIZ_BASE_URL": "https://x.org/",
        "LEIBNIZ_WORKERS": "3",
        "LEIBNIZ_RATE_LIMIT": "0",
        "LEIBNIZ_RATE_BURST": "",  # empty = default
    }
    s = ServeSettings.from_env(env)
    assert s.db_path == tmp_path / "x.sqlite" and s.backend == "meili"
    assert s.meili_url == "http://m:7700" and s.meili_key == "master"
    assert s.port == 9000 and s.base_url == "https://x.org" and s.workers == 3
    assert s.rate_limit == 0.0 and s.rate_burst == DEFAULT_RATE_BURST
    env["MEILI_API_KEY"] = "search-only"  # preferred over the master key
    assert ServeSettings.from_env(env).meili_key == "search-only"


def test_round_trip_through_env() -> None:
    s = ServeSettings(backend="none", base_url="https://a.b/", meili_key="k", port=81, workers=2)
    assert ServeSettings.from_env(s.to_env()) == s
    assert "LEIBNIZ_BASE_URL" in s.to_env() and "MEILI_API_KEY" in s.to_env()
    assert "MEILI_API_KEY" not in ServeSettings(meili_key=None).to_env()


def test_bad_backend_rejected() -> None:
    with pytest.raises(ValueError):
        ServeSettings(backend="solr")


def test_asgi_factory_builds_from_env(store_path, monkeypatch) -> None:
    monkeypatch.setenv("LEIBNIZ_DB_PATH", str(store_path))
    monkeypatch.setenv("LEIBNIZ_SEARCH_BACKEND", "none")
    monkeypatch.setenv("LEIBNIZ_RATE_LIMIT", "0")
    from leibniz.web.asgi import app as factory

    c = TestClient(factory())
    assert c.get("/healthz").json()["store"] is True
    assert c.get("/api/search", params={"q": "x"}).status_code == 503
    assert c.get("/api/works/00068642").status_code == 200


def test_listening_socket_is_tcp_bound_and_inheritable() -> None:
    sock = listening_socket("127.0.0.1", 0)
    try:
        # proto must say TCP, or asyncio never sets TCP_NODELAY on accepted connections
        assert sock.proto == socket.IPPROTO_TCP and sock.type == socket.SOCK_STREAM
        assert sock.family == socket.AF_INET and sock.getsockname()[1] > 0
        assert sock.get_inheritable()
    finally:
        sock.close()
    if socket.has_ipv6:
        try:
            v6 = listening_socket("::1", 0)
        except OSError:  # no IPv6 loopback in this environment
            return
        try:
            assert v6.family == socket.AF_INET6 and v6.proto == socket.IPPROTO_TCP
        finally:
            v6.close()
