"""Shared, reusable API step vocabulary. Import this module (directly or via
``test_framework.steps``) so its ``given``/``when``/``then`` definitions are
registered for any ``.feature`` file that uses these phrasings.
"""

from __future__ import annotations

from pytest_bdd import given as _given
from pytest_bdd import parsers
from pytest_bdd import then as _then
from pytest_bdd import when as _when

from test_framework import verify
from test_framework.api.client import ApiClient
from test_framework.steplog import step


@_given("the API is available")
def api_available(api_client: ApiClient) -> None:
    """No-op beyond requiring the api_client fixture: documents intent."""


@_when(parsers.parse('I GET "{path}"'))
def get_path(api_client: ApiClient, path: str) -> None:
    with step(f"GET {path}"):
        api_client.get(path)


@_when(parsers.parse('I POST credentials "{email}" / "{password}"'))
def post_credentials(api_client: ApiClient, email: str, password: str) -> None:
    with step(f"POST credentials {email!r}"):
        api_client.post("/login", json={"email": email, "password": password})


@_then(parsers.parse("the response status is {status:d}"))
def response_status_is(api_client: ApiClient, status: int) -> None:
    assert api_client.last_response is not None, "no request has been made yet"
    verify.status(api_client.last_response, status)


@_then(parsers.parse('the json field "{field}" equals "{value}"'))
def json_field_equals(api_client: ApiClient, field: str, value: str) -> None:
    assert api_client.last_response is not None, "no request has been made yet"
    verify.equals(api_client.last_response.json()[field], value, f'json field "{field}"')
