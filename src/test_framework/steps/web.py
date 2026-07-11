"""Shared, reusable web step vocabulary, driven purely by page-object field
names — never raw selectors — so ``.feature`` files stay POM-compliant.
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Page
from playwright.sync_api import expect as _expect
from pytest_bdd import given as _given
from pytest_bdd import parsers
from pytest_bdd import then as _then
from pytest_bdd import when as _when

from test_framework import report
from test_framework.steplog import step
from test_framework.ui.pages.base import BasePage


@_given(parsers.parse('I am on the "{page_name}" page'))
def go_to_named_page(
    page_name: str,
    page: Page,
    base_url: str,
    page_registry: dict[str, type[BasePage]],
    scenario_context: dict[str, Any],
) -> None:
    with step(f'Go to the "{page_name}" page'):
        page_class = page_registry.get(page_name)
        if page_class is None:
            registered = ", ".join(sorted(page_registry)) or "none"
            raise LookupError(
                f'no page object registered for "{page_name}" (page_registry has: {registered})'
            )
        page_object = page_class(page, base_url)
        page_object.goto()
        scenario_context["page"] = page_object


@_when(parsers.parse('I fill in "{field}" with "{value}"'))
def fill_field(scenario_context: dict[str, Any], field: str, value: str) -> None:
    with step(f'Fill in "{field}" with "{value}"'):
        scenario_context["page"].locator(field).fill(value)


@_when(parsers.parse('I click "{field}"'))
def click_field(scenario_context: dict[str, Any], field: str) -> None:
    with step(f'Click "{field}"'):
        scenario_context["page"].locator(field).click()


@_then(parsers.parse('the "{field}" is visible'))
def field_is_visible(scenario_context: dict[str, Any], field: str) -> None:
    locator = scenario_context["page"].locator(field)
    name = f'"{field}" is visible'
    # Playwright's expect() auto-waits for eventual consistency (e.g. a field
    # revealed by an async fetch) and its AssertionError is the real assertion
    # surface. Evidence flows through the reporting seam on pass and fail.
    try:
        _expect(locator).to_be_visible()  # pyright: ignore[reportUnknownMemberType] - playwright's overload stubs are imprecise here
    except AssertionError as exc:
        report.record_check(name, False, str(exc))
        raise
    report.record_check(name, True, f'"{field}" is visible')


@_then(parsers.parse('the "{field}" has text "{text}"'))
def field_has_text(scenario_context: dict[str, Any], field: str, text: str) -> None:
    locator = scenario_context["page"].locator(field)
    name = f'"{field}" text contains {text!r}'
    try:
        _expect(locator).to_contain_text(text)  # pyright: ignore[reportUnknownMemberType] - playwright's overload stubs are imprecise here
    except AssertionError as exc:
        report.record_check(name, False, str(exc))
        raise
    report.record_check(name, True, f'"{field}" text contains {text!r}')
