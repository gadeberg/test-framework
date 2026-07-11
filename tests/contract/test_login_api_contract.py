import pytest
from pytest_bdd import scenarios

scenarios("features/login_api.feature")

pytestmark = pytest.mark.api
