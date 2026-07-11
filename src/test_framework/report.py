"""The seam: the only module that talks to a concrete reporting backend.

``steplog.py``'s ``step()`` and ``verify.py``'s ``verify.*`` call only into
this module. Swapping or adding a backend (pytest-html <-> Allure <-> spy)
changes only this file and ``reporting/``, never a test.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

import pytest

from test_framework.reporting.base import ReportingBackend

_BACKEND_ENV_VAR = "TEST_FRAMEWORK_REPORT_BACKEND"

_current_backend: ReportingBackend | None = None


def _build_backend(name: str) -> ReportingBackend:
    if name == "pyhtml":
        from test_framework.reporting.pyhtml import PyHtmlBackend

        return PyHtmlBackend()
    if name == "spy":
        from test_framework.reporting.spy import SpyBackend

        return SpyBackend()
    if name == "allure":
        from test_framework.reporting.allure import AllureBackend

        return AllureBackend()
    raise ValueError(f"Unknown reporting backend: {name!r}")


def configured_backend_name() -> str:
    """The backend selected via ``TEST_FRAMEWORK_REPORT_BACKEND``, default ``pyhtml``."""
    return os.environ.get(_BACKEND_ENV_VAR, "pyhtml")


def start_test(backend_name: str | None = None) -> ReportingBackend:
    """Create and activate a fresh backend instance for the current test."""
    global _current_backend
    backend = _build_backend(backend_name or configured_backend_name())
    _current_backend = backend
    return backend


def end_test() -> None:
    """Deactivate the current test's backend."""
    global _current_backend
    _current_backend = None


def get_backend() -> ReportingBackend:
    if _current_backend is None:
        raise RuntimeError(
            "No active reporting backend. report.start_test() must run before "
            "step()/verify.* are used; the framework's pytest plugin (fixtures.py) "
            "does this automatically for every test."
        )
    return _current_backend


def current_backend_or_none() -> ReportingBackend | None:
    """Non-raising accessor for hooks that run outside a guaranteed test context."""
    return _current_backend


def start_step(name: str) -> None:
    get_backend().start_step(name)


def end_step(name: str, *, failed: bool = False) -> None:
    get_backend().end_step(name, failed=failed)


def attach(name: str, body: str, mime: str = "text/plain") -> None:
    get_backend().attach(name, body, mime)


def attach_file(name: str, path: str, mime: str = "application/octet-stream") -> None:
    get_backend().attach_file(name, path, mime)


def set_requirement(requirement_id: str) -> None:
    get_backend().set_requirement(requirement_id)


def record_check(name: str, ok: bool, detail: str) -> None:
    get_backend().record_check(name, ok, detail)


_F = TypeVar("_F", bound=Callable[..., object])


def requirement(requirement_id: str) -> Callable[[_F], _F]:
    """Tag a plain-Python test with a requirement id, e.g. ``REQ-1024``.

    Mirrors Gherkin's ``@REQ-xxxx`` tag; both resolve to the same
    ``report.set_requirement`` call via the pytest plugin's tag bridge in
    ``fixtures.py`` (``pytest_bdd_apply_tag``), so both authoring styles
    produce one label.
    """

    def decorator(func: _F) -> _F:
        marker = pytest.mark.requirement(requirement_id)
        return marker(func)

    return decorator
