"""Small authenticated Microsoft Graph HTTP client."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

import config
from .auth import MicrosoftAuthenticationError, get_access_token


class GraphError(RuntimeError):
    """Raised for Microsoft Graph transport and API errors."""


class GraphClient:
    """Authenticated client restricted to the configured Microsoft Graph host."""

    def __init__(self, token_provider=get_access_token, session=None):
        self._token_provider = token_provider
        self._session = session or requests.Session()
        self._base_url = config.MICROSOFT_GRAPH_BASE_URL.rstrip("/")

    def _url(self, path: str) -> str:
        if path.startswith("https://") or path.startswith("http://"):
            parsed = urlparse(path)
            base = urlparse(self._base_url)
            if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
                raise GraphError("Graph pagination URL has an unexpected host.")
            return path
        if not path.startswith("/") or path.startswith("//") or ".." in path.split("/"):
            raise GraphError("Graph request path is invalid.")
        return f"{self._base_url}{path}"

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if method.upper() not in {"GET", "POST", "PATCH"}:
            raise GraphError("Only GET, POST, and PATCH requests are supported.")
        try:
            token = self._token_provider()
        except MicrosoftAuthenticationError as exc:
            raise GraphError(f"Microsoft authentication failed: {exc}") from exc
        except Exception as exc:
            raise GraphError("Microsoft authentication failed.") from exc
        try:
            headers = dict(kwargs.pop("headers", {}))
            headers["Authorization"] = f"Bearer {token}"
            headers.setdefault("Accept", "application/json")
            response = self._session.request(
                method.upper(), self._url(path), headers=headers,
                timeout=config.REQUEST_TIMEOUT, **kwargs,
            )
        except requests.RequestException as exc:
            raise GraphError(f"Microsoft Graph request failed: {exc}") from exc
        if not response.ok:
            detail = ""
            try:
                payload = response.json()
                detail = payload.get("error", {}).get("message", "")
            except (ValueError, AttributeError):
                detail = response.text[:200]
            suffix = f": {detail}" if detail else ""
            raise GraphError(
                f"Microsoft Graph returned HTTP {response.status_code}{suffix}"
            )
        if response.status_code == 204 or not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise GraphError("Microsoft Graph returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise GraphError("Microsoft Graph returned an unexpected response.")
        return payload

    def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self.request("POST", path, **kwargs)
