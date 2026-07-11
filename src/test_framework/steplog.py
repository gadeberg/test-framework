"""A structured logger that doubles as the report-step recorder.

Authors wrap each logical action in ``with step("..."):`` — it logs to the
console *and* emits a report step (plus attachment on failure) via
``test_framework.report``, the only module that talks to a concrete backend.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Generator
from contextlib import contextmanager

from test_framework import report

logger = logging.getLogger("test_framework")


@contextmanager
def step(name: str) -> Generator[None]:
    """Wrap one logical action so it reads like the test's intent in the report."""
    logger.info("STEP: %s", name)
    report.start_step(name)
    failed = False
    try:
        yield
    except BaseException as exc:
        failed = True
        report.attach(
            f"error in step: {name}", "".join(traceback.format_exception(exc)), "text/plain"
        )
        raise
    finally:
        report.end_step(name, failed=failed)
