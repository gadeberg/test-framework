from __future__ import annotations

from typing import cast

import pytest
from playwright.sync_api import Page

from test_framework.steps.web import go_to_named_page
from test_framework.ui.pages.base import BasePage


class _LoginPage(BasePage):
    path = "/login-page"


def test_unregistered_page_name_lists_registered_pages() -> None:
    with pytest.raises(LookupError, match=r'no page object registered for "nope".*login'):
        go_to_named_page(
            "nope",
            page=cast(Page, None),
            base_url="http://x",
            page_registry={"login": _LoginPage},
            scenario_context={},
        )
