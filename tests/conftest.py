"""Shared fixtures for the framework's own self-tests.

Self-tests assert against the ``spy`` backend (never pytest-html/Allure) so
they need neither installed to verify the reporting seam is real.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Generator

import httpx
import pytest
import uvicorn

# The self-tests *require* the spy backend (fixtures assert on it), so assign
# unconditionally: an ambient TEST_FRAMEWORK_REPORT_BACKEND=pyhtml in the
# user's shell must not silently break every test.
os.environ["TEST_FRAMEWORK_REPORT_BACKEND"] = "spy"

# pytester powers the plugin-contract self-tests (running pytest-in-pytest).
pytest_plugins = ["pytester"]

from support.mockapp.app import app  # noqa: E402

from test_framework import report  # noqa: E402
from test_framework.reporting.spy import SpyBackend  # noqa: E402


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def mock_server_base_url() -> Generator[str, None, None]:
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            httpx.get(f"{base}/health", timeout=0.2)
            break
        except httpx.HTTPError:
            time.sleep(0.05)
    else:
        raise RuntimeError("mock server did not start in time")

    yield base

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def base_url(mock_server_base_url: str) -> str:
    return mock_server_base_url


@pytest.fixture
def spy() -> SpyBackend:
    backend = report.current_backend_or_none()
    assert isinstance(backend, SpyBackend)
    return backend
