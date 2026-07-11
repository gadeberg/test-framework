"""Phase-1 default backend: pure-Python, no JVM.

Human-readable output is pytest-html; machine-readable output is JUnit XML
(pytest's built-in ``--junitxml``). pytest-html has no nested-step concept, so
this backend renders ``step()``/``verify.*`` calls as formatted log lines
(captured into JUnit's system-out) and an HTML block attached to the test row
via pytest-html's ``extra`` mechanism (wired in ``fixtures.py``).
"""

from __future__ import annotations

import base64
import html
import logging
from pathlib import Path

logger = logging.getLogger("test_framework.report")


class PyHtmlBackend:
    def __init__(self) -> None:
        self._html_lines: list[str] = []
        self._depth = 0
        self.requirement_id: str | None = None

    def start_step(self, name: str) -> None:
        logger.info("%sSTEP %s", "  " * self._depth, name)
        self._html_lines.append(
            f'<div style="margin-left:{self._depth * 16}px"><b>Step:</b> {html.escape(name)}</div>'
        )
        self._depth += 1

    def end_step(self, name: str, *, failed: bool = False) -> None:
        self._depth = max(self._depth - 1, 0)
        status = "FAILED" if failed else "ok"
        logger.info("%sEND STEP %s (%s)", "  " * self._depth, name, status)

    def attach(self, name: str, body: str, mime: str = "text/plain") -> None:
        logger.info("ATTACH %s (%s): %s", name, mime, body)
        self._html_lines.append(
            f'<div style="margin-left:{self._depth * 16}px"><i>Attachment {html.escape(name)}:</i> '
            f"<pre>{html.escape(body)}</pre></div>"
        )

    def attach_file(self, name: str, path: str, mime: str = "application/octet-stream") -> None:
        logger.info("ATTACH FILE %s (%s): %s", name, mime, path)
        if mime.startswith("image/"):
            # Embed the image so a --self-contained-html report stays
            # self-contained: a bare file path wouldn't travel with it.
            encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
            content = f'<img src="data:{mime};base64,{encoded}" style="max-width:100%"/>'
        else:
            content = f"<code>{html.escape(path)}</code>"
        self._html_lines.append(
            f'<div style="margin-left:{self._depth * 16}px">'
            f"<i>Attachment {html.escape(name)}:</i> {content}</div>"
        )

    def set_requirement(self, requirement_id: str) -> None:
        self.requirement_id = requirement_id
        logger.info("REQUIREMENT %s", requirement_id)
        self._html_lines.insert(0, f"<div><b>Requirement:</b> {html.escape(requirement_id)}</div>")

    def record_check(self, name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        logger.info("%sCHECK %s: %s - %s", "  " * self._depth, status, name, detail)
        color = "green" if ok else "red"
        self._html_lines.append(
            f'<div style="margin-left:{self._depth * 16}px;color:{color}">'
            f"<b>{status}</b> {html.escape(name)}: {html.escape(detail)}</div>"
        )

    def render_html(self) -> str:
        return "\n".join(self._html_lines)
