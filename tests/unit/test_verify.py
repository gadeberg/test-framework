from __future__ import annotations

import pytest

from test_framework import verify
from test_framework.reporting.spy import SpyBackend


def test_equals_passes_and_records_check(spy: SpyBackend) -> None:
    verify.equals(1, 1, "count")
    assert spy.checks[-1].ok is True


def test_equals_fails_and_raises(spy: SpyBackend) -> None:
    with pytest.raises(AssertionError):
        verify.equals(1, 2, "count")
    assert spy.checks[-1].ok is False


def test_status_uses_response_status_code(spy: SpyBackend) -> None:
    class FakeResponse:
        status_code = 401

    verify.status(FakeResponse(), 401)
    assert spy.checks[-1].ok is True


def test_status_fails_on_mismatch(spy: SpyBackend) -> None:
    class FakeResponse:
        status_code = 500

    with pytest.raises(AssertionError):
        verify.status(FakeResponse(), 401)
    assert spy.checks[-1].ok is False


def test_contains_passes(spy: SpyBackend) -> None:
    verify.contains([1, 2, 3], 2, "list")
    assert spy.checks[-1].ok is True


def test_contains_fails_and_raises(spy: SpyBackend) -> None:
    with pytest.raises(AssertionError):
        verify.contains([1, 2, 3], 9, "list")
    assert spy.checks[-1].ok is False


def test_contains_on_non_container_records_failed_check(spy: SpyBackend) -> None:
    # e.g. a JSON field that came back as None: still an AssertionError with
    # recorded evidence, never a bare TypeError with no audit trail.
    with pytest.raises(AssertionError, match="not a container"):
        verify.contains(None, "x", "json field")
    assert spy.checks[-1].ok is False


def test_between_passes(spy: SpyBackend) -> None:
    verify.between(5, 1, 10, "value")
    assert spy.checks[-1].ok is True


def test_between_fails_outside_range(spy: SpyBackend) -> None:
    with pytest.raises(AssertionError):
        verify.between(15, 1, 10, "value")
    assert spy.checks[-1].ok is False
