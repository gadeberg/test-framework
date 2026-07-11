from __future__ import annotations

from typing import cast

import pytest
from playwright.sync_api import Page

from test_framework.ui.pages.base import BasePage


class _FakePage(BasePage):
    path = "/fake"
    locators = {"email": "#email"}


def test_locators_are_copied_per_instance() -> None:
    page_object = _FakePage(cast(Page, None), "http://x")
    page_object.locators["extra"] = "#extra"
    assert "extra" not in _FakePage.locators
    assert "extra" not in _FakePage(cast(Page, None), "http://x").locators


def test_unknown_locator_field_lists_known_fields() -> None:
    page_object = _FakePage(cast(Page, None), "http://x")
    with pytest.raises(LookupError, match=r"no locator for field 'nope'.*email"):
        page_object.locator("nope")
