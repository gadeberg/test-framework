"""Optional Allure backend, behind the same seam as the pyhtml default.

Only imported when ``TEST_FRAMEWORK_REPORT_BACKEND=allure`` is selected, so a
team that hasn't opted in never touches ``allure-pytest`` or its JVM report
generator. Requires the ``allure`` extra: ``uv sync --extra allure``.
"""

from __future__ import annotations

from typing import Any


class AllureBackend:
    def __init__(self) -> None:
        try:
            import allure  # type: ignore[import-not-found]  # optional extra, no bundled stubs
        except ImportError as exc:
            raise RuntimeError(
                "The allure backend requires the 'allure' extra: "
                "install with `uv sync --extra allure` (and a JVM to generate the report)."
            ) from exc
        self._allure: Any = allure
        self._open_steps: list[Any] = []

    def start_step(self, name: str) -> None:
        step_cm = self._allure.step(name)
        step_cm.__enter__()
        self._open_steps.append(step_cm)

    def end_step(self, name: str, *, failed: bool = False) -> None:
        if not self._open_steps:
            return
        step_cm = self._open_steps.pop()
        if failed:
            # Close the step with a synthetic exception so Allure marks it
            # failed; the real assertion error still surfaces via pytest.
            error = AssertionError(f"step failed: {name}")
            step_cm.__exit__(type(error), error, None)
        else:
            step_cm.__exit__(None, None, None)

    def _attachment_type(self, mime: str) -> Any:
        if mime == "text/html":
            return self._allure.attachment_type.HTML
        if mime == "image/png":
            return self._allure.attachment_type.PNG
        return self._allure.attachment_type.TEXT

    def attach(self, name: str, body: str, mime: str = "text/plain") -> None:
        self._allure.attach(body, name=name, attachment_type=self._attachment_type(mime))

    def attach_file(self, name: str, path: str, mime: str = "application/octet-stream") -> None:
        self._allure.attach.file(path, name=name, attachment_type=self._attachment_type(mime))

    def set_requirement(self, requirement_id: str) -> None:
        self._allure.dynamic.label("requirement", requirement_id)

    def record_check(self, name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        self._allure.attach(
            detail, name=f"{status}: {name}", attachment_type=self._allure.attachment_type.TEXT
        )
