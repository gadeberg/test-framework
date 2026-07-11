from __future__ import annotations

from test_framework.fixtures import pytest_bdd_apply_tag


def test_req_tag_is_routed_to_requirement_marker() -> None:
    def scenario_test() -> None:
        pass

    handled = pytest_bdd_apply_tag("REQ-2048", scenario_test)

    assert handled is True
    marks = [m for m in scenario_test.pytestmark if m.name == "requirement"]  # type: ignore[attr-defined]
    assert marks and marks[0].args == ("REQ-2048",)


def test_non_req_tag_is_left_for_pytest_bdds_default_handling() -> None:
    def scenario_test() -> None:
        pass

    assert pytest_bdd_apply_tag("smoke", scenario_test) is None
    assert not hasattr(scenario_test, "pytestmark")
