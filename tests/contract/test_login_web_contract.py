import pytest
from pytest_bdd import scenarios

scenarios("features/login_web.feature")

pytestmark = pytest.mark.ui
