"""Fake backend used by the framework's own self-tests.

Recording calls in memory lets unit/contract tests assert on reporting
behaviour without pytest-html or Allure installed, proving the seam is real.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


@dataclass
class SpyBackend:
    """Records every call it receives for later assertions in tests."""

    steps: list[str] = field(default_factory=list[str])
    ended_steps: list[tuple[str, bool]] = field(default_factory=list[tuple[str, bool]])
    attachments: list[tuple[str, str, str]] = field(default_factory=list[tuple[str, str, str]])
    file_attachments: list[tuple[str, str, str]] = field(default_factory=list[tuple[str, str, str]])
    requirements: list[str] = field(default_factory=list[str])
    checks: list[Check] = field(default_factory=list[Check])

    def start_step(self, name: str) -> None:
        self.steps.append(name)

    def end_step(self, name: str, *, failed: bool = False) -> None:
        self.ended_steps.append((name, failed))

    def attach(self, name: str, body: str, mime: str = "text/plain") -> None:
        self.attachments.append((name, body, mime))

    def attach_file(self, name: str, path: str, mime: str = "application/octet-stream") -> None:
        self.file_attachments.append((name, path, mime))

    def set_requirement(self, requirement_id: str) -> None:
        self.requirements.append(requirement_id)

    def record_check(self, name: str, ok: bool, detail: str) -> None:
        self.checks.append(Check(name=name, ok=ok, detail=detail))
