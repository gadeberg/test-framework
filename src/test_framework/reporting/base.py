"""The backend protocol every reporting engine implements.

``report.py`` is the only module that talks to a concrete backend through
this interface, so swapping engines (pytest-html <-> Allure <-> spy) never
touches a test, step, or verify call.
"""

from __future__ import annotations

from typing import Protocol


class ReportingBackend(Protocol):
    """Minimal surface a reporting backend must provide."""

    def start_step(self, name: str) -> None:
        """Open a named step; steps may nest."""
        ...

    def end_step(self, name: str, *, failed: bool = False) -> None:
        """Close the most recently opened step."""
        ...

    def attach(self, name: str, body: str, mime: str = "text/plain") -> None:
        """Record an inline artifact whose content is ``body`` (log excerpt, ...)."""
        ...

    def attach_file(self, name: str, path: str, mime: str = "application/octet-stream") -> None:
        """Record an artifact that lives on disk (screenshot, trace, ...)."""
        ...

    def set_requirement(self, requirement_id: str) -> None:
        """Tag the current test with a requirement id, e.g. ``REQ-1024``."""
        ...

    def record_check(self, name: str, ok: bool, detail: str) -> None:
        """Record a single pass/fail verification with its evidence."""
        ...
