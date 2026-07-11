from __future__ import annotations

from test_framework.ui.pages.base import BasePage


class LoginPage(BasePage):
    path = "/login-page"
    locators = {
        "email": "#email",
        "password": "#password",
        "submit": "#submit",
        "error": "#error",
    }
