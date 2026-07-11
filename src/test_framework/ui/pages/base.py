"""Page-object base: all UI selectors live in page objects, never in tests/steps.

Subclasses declare a ``path`` and a ``locators`` map from semantic field name
to CSS selector. The shared web step library (``steps/web.py``) drives pages
purely by field name, so feature files and Python tests never contain a
selector.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page


class BasePage:
    path: str = "/"
    locators: dict[str, str] = {}

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        # Per-instance copy: an instance tweaking `self.locators` must not
        # mutate the class-level map shared by every other instance.
        self.locators = dict(self.locators)

    def goto(self) -> None:
        self.page.goto(f"{self.base_url}{self.path}")

    def locator(self, field: str) -> Locator:
        selector = self.locators.get(field)
        if selector is None:
            known = ", ".join(sorted(self.locators)) or "none"
            raise LookupError(
                f"{type(self).__name__} has no locator for field {field!r} (known fields: {known})"
            )
        return self.page.locator(selector)
