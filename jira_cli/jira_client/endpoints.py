from __future__ import annotations

from typing import Any

from jira_cli.jira_client.http import JiraHttpClient


class JiraEndpoints:
    def __init__(self, client: JiraHttpClient):
        self._client = client

    def get_issue(self, issue_key: str, fields: list[str] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self._client.get(f"/rest/api/3/issue/{issue_key}", params=params or None)

    def search_issues(self, jql: str, fields: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"jql": jql}
        if fields:
            payload["fields"] = fields
        if limit is not None:
            payload["maxResults"] = limit
        return self._client.post("/rest/api/3/search", json=payload)

    def create_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.post("/rest/api/3/issue", json=payload)
