"""A namespace of verification helpers over plain ``assert``.

Each helper records pass-and-fail evidence via ``report.record_check`` so an
author can't forget to leave a trail, then raises the real ``AssertionError``
on failure — pytest's own assertion machinery still does the failing, this
just can't be skipped silently. Extending the vocabulary is one function.
"""

from __future__ import annotations

from typing import Protocol

from test_framework import report


class _HasStatusCode(Protocol):
    status_code: int


def _check(name: str, ok: bool, detail: str) -> None:
    report.record_check(name, ok, detail)
    assert ok, detail


def equals(actual: object, expected: object, label: str = "value") -> None:
    ok = actual == expected
    detail = f"{label}: expected {expected!r}, got {actual!r}"
    _check(f"{label} equals {expected!r}", ok, detail)


def status(response: _HasStatusCode, expected: int) -> None:
    actual = response.status_code
    ok = actual == expected
    detail = f"response status: expected {expected}, got {actual}"
    _check(f"status equals {expected}", ok, detail)


def contains(container: object, member: object, label: str = "value") -> None:
    try:
        ok = member in container  # pyright: ignore[reportOperatorIssue]
        detail = f"{label}: expected {member!r} in {container!r}"
    except TypeError:
        # e.g. a JSON field that came back as None: un-containability is a
        # failed check with evidence, never a bare TypeError.
        ok = False
        detail = f"{label}: expected {member!r} in {container!r}, which is not a container"
    _check(f"{label} contains {member!r}", ok, detail)


def between(actual: float, low: float, high: float, label: str = "value") -> None:
    ok = low <= actual <= high
    detail = f"{label}: expected {low!r} <= {actual!r} <= {high!r}"
    _check(f"{label} between {low!r} and {high!r}", ok, detail)


def is_true(actual: object, label: str = "condition") -> None:
    ok = bool(actual)
    detail = f"{label}: expected truthy, got {actual!r}"
    _check(f"{label} is true", ok, detail)


__all__ = ["equals", "status", "contains", "between", "is_true"]
