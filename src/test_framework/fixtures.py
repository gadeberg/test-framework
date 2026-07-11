"""The framework's pytest plugin: config wiring, fixtures, the ``@REQ-*`` tag
bridge, and requirement traceability in both report outputs.

Registered as a ``pytest11`` entry point, so a consumer's ``conftest.py``
gets everything just by the package being installed (no explicit
``pytest_plugins`` needed, though it can also be loaded that way).
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import pytest
from pluggy import Result

from test_framework import report
from test_framework.api.client import ApiClient
from test_framework.ui.pages.base import BasePage

try:
    import pytest_html  # pyright: ignore[reportMissingTypeStubs] - no stubs shipped
except ImportError:  # pragma: no cover - pytest-html is a core dependency
    pytest_html = None

_DEFAULT_BASE_URL = "http://localhost:8000"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requirement(id): traces a test/scenario to a requirement id, e.g. REQ-1234",
    )
    # Deliberately NOT a `base_url` fixture: pytest-base-url (a hard dependency
    # of pytest-playwright) registers a session-scoped `base_url` fixture via
    # its own pytest11 entry point, and its definition wins the
    # registration-order race, silently shadowing any fixture defined here.
    # Seeding the option it reads cooperates instead of racing, and keeps
    # `--base-url` and the `base_url` ini setting working with their usual
    # precedence (CLI > ini > BASE_URL env var > default).
    if not config.getoption("base_url", default=None) and not config.getini("base_url"):
        config.option.base_url = os.environ.get("BASE_URL", _DEFAULT_BASE_URL)


@pytest.fixture
def api_client(base_url: str) -> Generator[ApiClient, None, None]:
    client = ApiClient(base_url=base_url)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def scenario_context() -> dict[str, Any]:
    """Per-scenario/test scratch space shared across pytest-bdd steps."""
    return {}


@pytest.fixture
def page_registry() -> dict[str, type[BasePage]]:
    """Maps semantic page names (used in ``I am on the "..." page``) to page-object
    classes. Empty by default; a consumer project's conftest overrides this to
    register its own pages, keeping the shared web steps generic."""
    return {}


@pytest.fixture(autouse=True)
def _report_backend() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction] - autouse, invoked by pytest
    report.start_test()
    try:
        yield
    finally:
        report.end_test()


@pytest.fixture(autouse=True)
def _apply_requirement_marker(  # pyright: ignore[reportUnusedFunction] - autouse, invoked by pytest
    request: pytest.FixtureRequest, _report_backend: None
) -> None:
    # pytest's Node.get_closest_marker is dynamically typed upstream (returns Any-ish Mark)
    marker = request.node.get_closest_marker("requirement")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    if marker is not None and marker.args:  # pyright: ignore[reportUnknownMemberType]
        requirement_id = str(marker.args[0])  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        report.set_requirement(requirement_id)
        # Also record it as a per-test property so the machine-readable JUnit
        # XML carries the label (<property name="requirement" .../>), not just
        # the HTML report. Covers Gherkin too: the @REQ-* tag bridge applies
        # this same marker.
        request.node.user_properties.append(("requirement", requirement_id))  # pyright: ignore[reportUnknownMemberType]


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_apply_tag(tag: str, function: Any) -> bool | None:
    """Route Gherkin ``@REQ-*`` tags to the same label the ``@requirement`` decorator uses.

    ``tryfirst`` matters: this is a ``firstresult=True`` hook, and pytest-bdd's
    own built-in implementation unconditionally applies ``pytest.mark.<tag>``
    and returns non-None. Without priority, that default wins and this bridge
    never runs.
    """
    if tag.startswith("REQ-"):
        pytest.mark.requirement(tag)(function)
        return True
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Result[pytest.TestReport], None]:
    outcome = yield
    test_report = outcome.get_result()
    # The call phase always renders; a failed setup/teardown phase renders too,
    # so evidence collected before e.g. a broken fixture isn't lost. (By
    # teardown-report time the per-test backend is already closed, so this
    # never duplicates the call-phase block.)
    if test_report.when != "call" and not test_report.failed:
        return

    backend = report.current_backend_or_none()
    render_html = getattr(backend, "render_html", None)
    if render_html is not None and pytest_html is not None:
        extras: list[Any] = getattr(test_report, "extras", [])
        # pytest-html ships no stubs; it also monkeypatches `extras` onto TestReport at runtime.
        extras.append(pytest_html.extras.html(f"<div>{render_html()}</div>"))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        test_report.extras = extras  # pyright: ignore[reportAttributeAccessIssue]
