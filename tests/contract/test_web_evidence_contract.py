"""The web assertion steps' evidence contract: a recorded check on pass AND
fail — including the element-never-appears case — with the real assertion
error surfacing (never a swallowed ``expect`` plus a raw Playwright
``TimeoutError`` from re-probing the DOM).
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from contract_pages import LoginPage
from playwright.sync_api import Page, expect

from test_framework.reporting.spy import SpyBackend
from test_framework.steps.web import field_has_text, field_is_visible

pytestmark = pytest.mark.ui


@pytest.fixture
def login_context(page: Page, base_url: str) -> dict[str, Any]:
    login = LoginPage(page, base_url)
    login.goto()
    return {"page": login}


@pytest.fixture
def short_expect_timeout() -> Generator[None, None, None]:
    expect.set_options(timeout=500)
    yield
    expect.set_options(timeout=5000)


def test_has_text_on_missing_element_records_failed_check_and_raises(
    login_context: dict[str, Any], spy: SpyBackend, short_expect_timeout: None
) -> None:
    login_context["page"].locators["missing"] = "#does-not-exist"
    with pytest.raises(AssertionError):
        field_has_text(login_context, "missing", "anything")
    assert spy.checks and spy.checks[-1].ok is False


def test_is_visible_on_missing_element_records_failed_check_and_raises(
    login_context: dict[str, Any], spy: SpyBackend, short_expect_timeout: None
) -> None:
    login_context["page"].locators["missing"] = "#does-not-exist"
    with pytest.raises(AssertionError):
        field_is_visible(login_context, "missing")
    assert spy.checks and spy.checks[-1].ok is False


def test_has_text_records_passing_check(login_context: dict[str, Any], spy: SpyBackend) -> None:
    field_has_text(login_context, "submit", "Log in")
    assert spy.checks and spy.checks[-1].ok is True


def test_is_visible_records_passing_check(login_context: dict[str, Any], spy: SpyBackend) -> None:
    field_is_visible(login_context, "email")
    assert spy.checks and spy.checks[-1].ok is True
