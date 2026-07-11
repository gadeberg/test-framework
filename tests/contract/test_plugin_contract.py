"""Contract tests for the pytest plugin itself, run pytest-in-pytest via
pytester so they see exactly what a bare consumer (no conftest overrides)
sees: entry-point loading, ``base_url`` wiring, JUnit XML evidence, and
UI-failure artifacts for Gherkin scenarios.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest


def test_base_url_env_var_reaches_a_bare_consumer(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Regression for the shadowing bug: the framework used to define its own
    # `base_url` fixture, which pytest-base-url's entry point silently won
    # over, so BASE_URL was ignored in any project without a conftest override.
    monkeypatch.setenv("BASE_URL", "http://from-env:8123")
    pytester.makepyfile(  # pyright: ignore[reportUnknownMemberType] - pytester ships loose types
        """
        def test_base_url_fixture(base_url):
            assert base_url == "http://from-env:8123"
        """
    )
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)


def test_base_url_cli_option_beats_the_env_var(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BASE_URL", "http://from-env:8123")
    pytester.makepyfile(  # pyright: ignore[reportUnknownMemberType] - pytester ships loose types
        """
        def test_base_url_fixture(base_url):
            assert base_url == "http://from-cli:9999"
        """
    )
    result = pytester.runpytest_subprocess("--base-url", "http://from-cli:9999")
    result.assert_outcomes(passed=1)


def test_requirement_label_and_steps_land_in_junit_xml(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The machine-readable audit artifact must carry the requirement label for
    # BOTH authoring styles, plus the step/check evidence when junit_logging
    # is enabled (as this repo's and the example consumer's ini do).
    monkeypatch.setenv("TEST_FRAMEWORK_REPORT_BACKEND", "pyhtml")
    pytester.makefile(
        ".feature",
        tagged="""
        Feature: Tagged
          @REQ-778
          Scenario: tagged scenario
            Given the API is available
        """,
    )
    pytester.makepyfile(  # pyright: ignore[reportUnknownMemberType] - pytester ships loose types
        test_tagged="""
        import pytest
        from pytest_bdd import scenarios
        from test_framework import verify
        from test_framework.steplog import step

        scenarios("tagged.feature")

        @pytest.mark.requirement("REQ-777")
        def test_python_style():
            with step("do the thing"):
                verify.equals(1, 1, "the answer")
        """
    )
    xml_path = pytester.path / "junit.xml"
    result = pytester.runpytest_subprocess(
        f"--junitxml={xml_path}", "-o", "junit_logging=log", "-o", "log_level=INFO"
    )
    result.assert_outcomes(passed=2)

    root = ET.parse(xml_path).getroot()
    properties = [(prop.get("name"), prop.get("value")) for prop in root.iter("property")]
    assert ("requirement", "REQ-777") in properties, "Python-style label missing from JUnit XML"
    assert ("requirement", "REQ-778") in properties, "Gherkin-style label missing from JUnit XML"

    xml_text = xml_path.read_text()
    assert "STEP do the thing" in xml_text, "step evidence missing from JUnit XML"
    assert "CHECK PASS" in xml_text, "check evidence missing from JUnit XML"


@pytest.mark.ui
def test_failing_bdd_web_scenario_captures_screenshot_and_trace(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    mock_server_base_url: str,
    playwright_browsers_path: str,
) -> None:
    # Evidence capture must be equivalent across authoring styles: pytest-
    # playwright's built-in capture (enabled via addopts in both repos) hooks
    # the page/context fixtures, so a failing Gherkin scenario produces the
    # same artifacts a failing plain-Python test does.
    monkeypatch.setenv("BASE_URL", mock_server_base_url)
    # pytester fakes $HOME, which is where Playwright looks for its browser
    # cache - point the subprocess at the real one, when one was resolvable.
    if playwright_browsers_path:
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", playwright_browsers_path)
    pytester.makeconftest(
        """
        import pytest
        from playwright.sync_api import expect
        from test_framework.ui.pages.base import BasePage

        expect.set_options(timeout=1500)

        class LoginPage(BasePage):
            path = "/login-page"
            locators = {"error": "#error"}

        @pytest.fixture
        def page_registry():
            return {"login": LoginPage}
        """
    )
    pytester.makefile(
        ".feature",
        failing_web="""
        Feature: Failing web scenario
          Scenario: error text that never appears
            Given I am on the "login" page
            Then the "error" has text "text that never appears"
        """,
    )
    pytester.makepyfile(  # pyright: ignore[reportUnknownMemberType] - pytester ships loose types
        test_failing_web="""
        from pytest_bdd import scenarios

        scenarios("failing_web.feature")
        """
    )
    result = pytester.runpytest_subprocess(
        "--screenshot=only-on-failure", "--tracing=retain-on-failure"
    )
    result.assert_outcomes(failed=1)

    artifacts = pytester.path / "test-results"
    assert list(artifacts.rglob("*.png")), "no screenshot captured for the failing BDD scenario"
    assert list(artifacts.rglob("trace.zip")), "no trace captured for the failing BDD scenario"
