"""Unit tests for the optional Allure backend against a fake ``allure`` module.

The real package (and its JVM report generator) stays optional; these tests
pin the backend's contract: failed steps close as failed, file attachments go
through Allure's file API, and checks/requirements reach the right calls.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from test_framework.reporting.allure import AllureBackend

_Call = tuple[Any, ...]


class _FakeStepCM:
    def __init__(self, calls: list[_Call], name: str) -> None:
        self._calls = calls
        self._name = name

    def __enter__(self) -> _FakeStepCM:
        self._calls.append(("step_enter", self._name))
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self._calls.append(("step_exit", self._name, exc_type))
        return False


class _FakeAttach:
    def __init__(self, calls: list[_Call]) -> None:
        self._calls = calls

    def __call__(self, body: Any, *, name: str, attachment_type: Any) -> None:
        self._calls.append(("attach", body, name, attachment_type))

    def file(self, path: str, *, name: str, attachment_type: Any) -> None:
        self._calls.append(("attach_file", path, name, attachment_type))


@pytest.fixture
def fake_allure(monkeypatch: pytest.MonkeyPatch) -> list[_Call]:
    calls: list[_Call] = []

    def fake_step(name: str) -> _FakeStepCM:
        return _FakeStepCM(calls, name)

    def fake_label(name: str, value: str) -> None:
        calls.append(("label", name, value))

    module = types.ModuleType("allure")
    module.step = fake_step  # pyright: ignore[reportAttributeAccessIssue]
    module.attach = _FakeAttach(calls)  # pyright: ignore[reportAttributeAccessIssue]
    module.attachment_type = types.SimpleNamespace(TEXT="TEXT", HTML="HTML", PNG="PNG")  # pyright: ignore[reportAttributeAccessIssue]
    module.dynamic = types.SimpleNamespace(label=fake_label)  # pyright: ignore[reportAttributeAccessIssue]
    monkeypatch.setitem(sys.modules, "allure", module)
    return calls


def test_failed_step_is_closed_as_failed(fake_allure: list[_Call]) -> None:
    backend = AllureBackend()
    backend.start_step("doomed")
    backend.end_step("doomed", failed=True)
    exit_call = fake_allure[-1]
    assert exit_call[0] == "step_exit"
    assert exit_call[2] is AssertionError


def test_passed_step_is_closed_cleanly(fake_allure: list[_Call]) -> None:
    backend = AllureBackend()
    backend.start_step("fine")
    backend.end_step("fine", failed=False)
    assert fake_allure[-1] == ("step_exit", "fine", None)


def test_attach_file_uses_allures_file_api(fake_allure: list[_Call]) -> None:
    backend = AllureBackend()
    backend.attach_file("screenshot", "/tmp/shot.png", "image/png")
    assert fake_allure[-1] == ("attach_file", "/tmp/shot.png", "screenshot", "PNG")


def test_attach_maps_mime_to_attachment_type(fake_allure: list[_Call]) -> None:
    backend = AllureBackend()
    backend.attach("log", "<p>hi</p>", "text/html")
    assert fake_allure[-1] == ("attach", "<p>hi</p>", "log", "HTML")


def test_record_check_and_requirement(fake_allure: list[_Call]) -> None:
    backend = AllureBackend()
    backend.set_requirement("REQ-1")
    backend.record_check("status equals 200", ok=False, detail="got 500")
    assert ("label", "requirement", "REQ-1") in fake_allure
    assert fake_allure[-1] == ("attach", "got 500", "FAIL: status equals 200", "TEXT")
