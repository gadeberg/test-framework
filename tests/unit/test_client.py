from __future__ import annotations

from test_framework.api.client import ApiClient


def test_get_sends_request_and_stores_last_response(mock_server_base_url: str) -> None:
    client = ApiClient(base_url=mock_server_base_url)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert client.last_response is resp
    client.close()


def test_post_sends_json_body(mock_server_base_url: str) -> None:
    client = ApiClient(base_url=mock_server_base_url)
    resp = client.post("/login", json={"email": "user@example.com", "password": "correct-password"})
    assert resp.status_code == 200
    assert "token" in resp.json()
    client.close()


def test_set_auth_header_adds_authorization_header(mock_server_base_url: str) -> None:
    client = ApiClient(base_url=mock_server_base_url)
    client.set_auth_header("abc123")
    resp = client.get("/whoami")
    assert resp.json()["authorization"] == "Bearer abc123"
    client.close()
