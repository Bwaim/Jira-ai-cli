from __future__ import annotations

from typing import Any

import httpx

from jira_cli.cli import exit_codes
from jira_cli.models.errors import CliError


class JiraHttpClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout: float = 30.0):
        self._client = httpx.Client(
            base_url=base_url,
            auth=(email, api_token),
            timeout=timeout,
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise CliError(
                code="JIRA_API_ERROR",
                message="Jira API request failed",
                details={"errorMessages": [str(exc)], "errors": {}},
                exit_code=exit_codes.JIRA_API,
            ) from exc
        return self._decode_response(response)

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=json)
        except httpx.HTTPError as exc:
            raise CliError(
                code="JIRA_API_ERROR",
                message="Jira API request failed",
                details={"errorMessages": [str(exc)], "errors": {}},
                exit_code=exit_codes.JIRA_API,
            ) from exc
        return self._decode_response(response)

    @staticmethod
    def _decode_response(response: httpx.Response) -> dict[str, Any]:
        if 200 <= response.status_code < 300:
            if response.content:
                try:
                    payload = response.json()
                except ValueError:
                    return {}
                if isinstance(payload, dict):
                    return payload
            return {}

        payload = JiraHttpClient._json_payload(response)
        error_messages = payload.get("errorMessages") or []
        errors = payload.get("errors") or {}

        if response.status_code == 401:
            raise CliError(
                code="AUTH_ERROR",
                message="Authentication failed",
                details={"status": response.status_code},
                exit_code=exit_codes.AUTH,
            )

        if response.status_code == 404:
            raise CliError(
                code="NOT_FOUND",
                message="Resource not found",
                details={"status": response.status_code},
                exit_code=exit_codes.NOT_FOUND,
            )

        raise CliError(
            code="JIRA_API_ERROR",
            message="Jira API request failed",
            details={
                "status": response.status_code,
                "errorMessages": error_messages,
                "errors": errors,
            },
            exit_code=exit_codes.JIRA_API,
        )

    @staticmethod
    def _json_payload(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            return {}

        if isinstance(payload, dict):
            return payload
        return {}
