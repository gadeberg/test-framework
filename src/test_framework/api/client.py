"""Thin httpx wrapper: the single, canonical API path for tests.

Tests and steps call this wrapper, never raw httpx, so the client behaviour
(base URL, auth, last-response tracking) is consistent everywhere.
"""

from __future__ import annotations

from typing import Any

import httpx


class ApiClient:
    """A thin wrapper around ``httpx.Client``.

    Stores the last response so steps can assert against it without
    threading return values through fixtures manually.
    """

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)
        self.last_response: httpx.Response | None = None

    def set_auth_header(self, token: str, *, scheme: str = "Bearer") -> None:
        self._client.headers["Authorization"] = f"{scheme} {token}"

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        # Cleared first so a raising request (timeout, connection error) can't
        # leave a stale previous response behind for later assertions.
        self.last_response = None
        response = self._client.request(method, path, **kwargs)
        self.last_response = response
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
