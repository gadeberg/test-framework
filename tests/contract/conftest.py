from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from contract_pages import LoginPage

from test_framework.ui.pages.base import BasePage


def _default_browsers_cache() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        base = Path(local) if local else Path.home() / "AppData" / "Local"
        return base / "ms-playwright"
    return Path.home() / ".cache" / "ms-playwright"


# Resolved at import time, i.e. before pytester fakes $HOME: Playwright locates
# its browser cache relative to the home directory, so a pytest-in-pytest
# subprocess would otherwise look inside pytester's empty fake home and fail
# with "Executable doesn't exist" on any machine where PLAYWRIGHT_BROWSERS_PATH
# isn't already set.
_REAL_BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or str(_default_browsers_cache())


@pytest.fixture
def playwright_browsers_path() -> str:
    """The real browser-cache location, for handing into pytester subprocesses."""
    return _REAL_BROWSERS_PATH


@pytest.fixture
def page_registry() -> dict[str, type[BasePage]]:
    return {"login": LoginPage}
