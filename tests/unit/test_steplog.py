from __future__ import annotations

import pytest

from test_framework.reporting.spy import SpyBackend
from test_framework.steplog import step


def test_step_records_start_and_end(spy: SpyBackend) -> None:
    with step("do a thing"):
        pass
    assert spy.steps == ["do a thing"]
    assert spy.ended_steps == [("do a thing", False)]


def test_step_records_failure_and_reraises(spy: SpyBackend) -> None:
    with pytest.raises(ValueError, match="boom"):
        with step("do a failing thing"):
            raise ValueError("boom")
    assert spy.ended_steps == [("do a failing thing", True)]
    assert spy.attachments
    assert spy.attachments[0][0] == "error in step: do a failing thing"


def test_nested_steps_track_independently(spy: SpyBackend) -> None:
    with step("outer"):
        with step("inner"):
            pass
    assert spy.steps == ["outer", "inner"]
    assert spy.ended_steps == [("inner", False), ("outer", False)]
