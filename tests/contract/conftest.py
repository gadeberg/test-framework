from __future__ import annotations

import pytest
from contract_pages import LoginPage

from test_framework.ui.pages.base import BasePage


@pytest.fixture
def page_registry() -> dict[str, type[BasePage]]:
    return {"login": LoginPage}
