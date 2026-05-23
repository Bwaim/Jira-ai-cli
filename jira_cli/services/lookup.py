from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jira_cli.config.loader import load_profile
from jira_cli.jira_client.http import JiraHttpClient


@dataclass
class LookupService:
    client: JiraHttpClient

    def issue_types(self) -> list[dict[str, Any]]:
        return list_issue_types(self.client)

    def projects(self) -> dict[str, Any]:
        return list_projects(self.client)

    def boards(self, project_key: str | None = None, board_type: str | None = None) -> dict[str, Any]:
        return list_boards(self.client, project_key=project_key, board_type=board_type)

    def sprints(self, board_id: int, states: list[str] | None = None) -> dict[str, Any]:
        return list_sprints(self.client, board_id=board_id, states=states)

    def priorities(self) -> dict[str, Any]:
        return list_priorities(self.client)

    def users(self, query: str) -> list[dict[str, Any]]:
        return search_users(self.client, query=query)


def make_lookup_service(config: str | None, profile: str | None) -> LookupService:
    import os

    profile_config = load_profile(config, profile)
    token = os.getenv(profile_config.api_token_env)
    if not token:
        raise ValueError(f"Missing API token env var: {profile_config.api_token_env}")

    client = JiraHttpClient(
        base_url=profile_config.base_url,
        email=profile_config.email,
        api_token=token,
    )
    return LookupService(client)


def list_issue_types(client: JiraHttpClient) -> list[dict[str, Any]]:
    return client.get("/rest/api/3/issuetype")


def list_projects(client: JiraHttpClient) -> dict[str, Any]:
    return client.get("/rest/api/3/project/search")


def list_boards(
    client: JiraHttpClient,
    project_key: str | None = None,
    board_type: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if project_key:
        params["projectKeyOrId"] = project_key
    if board_type:
        params["type"] = board_type
    return client.get("/rest/agile/1.0/board", params=params or None)


def list_sprints(
    client: JiraHttpClient,
    board_id: int,
    states: list[str] | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if states:
        params["state"] = ",".join(states)
    return client.get(f"/rest/agile/1.0/board/{board_id}/sprint", params=params or None)


def list_priorities(client: JiraHttpClient) -> dict[str, Any]:
    return client.get("/rest/api/3/priority/search")


def search_users(client: JiraHttpClient, query: str) -> list[dict[str, Any]]:
    return client.get("/rest/api/3/user/search", params={"query": query})
