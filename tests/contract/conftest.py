from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from contract_pages import LoginPage

from test_framework.ui.pages.base import BasePage


def _default_browsers_cache() -> Path | None:
    try:
        home = Path.home()
    except RuntimeError:
        # e.g. an arbitrary UID with no passwd entry and no $HOME: a conftest
        # import-time crash would kill collection of the whole suite, so fall
        # back to "no path known" instead.
        return None
    if sys.platform == "darwin":
        return home / "Library" / "Caches" / "ms-playwright"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        base = Path(local) if local else home / "AppData" / "Local"
        return base / "ms-playwright"
    return home / ".cache" / "ms-playwright"


# Resolved at import time, i.e. before pytester fakes $HOME: Playwright locates
# its browser cache relative to the home directory, so a pytest-in-pytest
# subprocess would otherwise look inside pytester's empty fake home and fail
# with "Executable doesn't exist" on any machine where PLAYWRIGHT_BROWSERS_PATH
# isn't already set. Empty string = nothing to hand into the subprocess.
_default_cache = _default_browsers_cache()
_REAL_BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or (
    str(_default_cache) if _default_cache else ""
)


@pytest.fixture
def playwright_browsers_path() -> str:
    """The real browser-cache location, for handing into pytester subprocesses."""
    return _REAL_BROWSERS_PATH


@pytest.fixture
def page_registry() -> dict[str, type[BasePage]]:
    return {"login": LoginPage}
