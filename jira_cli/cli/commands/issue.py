from __future__ import annotations

import json
import os
from typing import Callable

import typer

from jira_cli.cli import exit_codes
from jira_cli.cli.output import print_error
from jira_cli.config.loader import load_profile
from jira_cli.config.models import CustomFieldsConfig
from jira_cli.jira_client.endpoints import JiraEndpoints
from jira_cli.jira_client.http import JiraHttpClient
from jira_cli.models.errors import CliError
from jira_cli.services.issues import (
    build_create_issue_input,
    build_create_issue_payload,
    collect_create_issue_wizard_answers,
)

issue_app = typer.Typer()
_validation_hook: Callable[[str], None] | None = None


def set_validation_hook(hook: Callable[[str], None]) -> None:
    global _validation_hook
    _validation_hook = hook


@issue_app.command("get")
def issue_get(
    issue_key: str,
    fields: list[str] | None = typer.Option(None, "--fields"),
    config: str | None = typer.Option(None, "--config"),
    profile: str | None = typer.Option(None, "--profile"),
) -> None:
    try:
        if _validation_hook:
            _validation_hook(issue_key)
        parsed_fields = _parse_fields(fields)
        endpoints, _ = _load_runtime(config, profile)
        payload = endpoints.get_issue(issue_key, fields=parsed_fields)
        if parsed_fields:
            payload = _select_issue_fields(payload, parsed_fields)
        typer.echo(_dump_json(payload))
    except Exception as exc:
        _raise_cli_exit(exc)


@issue_app.command("create")
def issue_create(
    project_key: str | None = typer.Argument(None),
    issue_type: str | None = typer.Argument(None),
    summary: str | None = typer.Argument(None),
    original_estimate: str | None = typer.Option(None, "--original-estimate"),
    sprint: int | None = typer.Option(None, "--sprint"),
    story_points: float | None = typer.Option(None, "--story-points"),
    wizard: bool = typer.Option(False, "--wizard"),
    config: str | None = typer.Option(None, "--config"),
    profile: str | None = typer.Option(None, "--profile"),
) -> None:
    try:
        endpoints, custom_fields = _load_runtime(config, profile)
        if wizard:
            issue_input = build_create_issue_input(
                **collect_create_issue_wizard_answers(
                    typer.prompt,
                    project_key=project_key,
                    issue_type=issue_type,
                    summary=summary,
                    original_estimate=original_estimate,
                    sprint=sprint,
                    story_points=story_points,
                )
            )
        else:
            if not project_key or not issue_type or not summary:
                raise ValueError(
                    "project_key, issue_type and summary are required unless --wizard is used"
                )
            issue_input = build_create_issue_input(
                project_key=project_key,
                issue_type=issue_type,
                summary=summary,
                original_estimate=original_estimate,
                sprint=sprint,
                story_points=story_points,
            )

        payload = build_create_issue_payload(
            issue_input,
            custom_fields=custom_fields,
        )
        created = endpoints.create_issue(payload)
        typer.echo(_dump_json(created))
    except Exception as exc:
        _raise_cli_exit(exc)


@issue_app.command("search")
def issue_search(
    jql: str,
    fields: list[str] | None = typer.Option(None, "--fields"),
    limit: int | None = typer.Option(None, "--limit"),
    config: str | None = typer.Option(None, "--config"),
    profile: str | None = typer.Option(None, "--profile"),
) -> None:
    try:
        endpoints, _ = _load_runtime(config, profile)
        payload = endpoints.search_issues(
            jql,
            fields=_parse_fields(fields),
            limit=limit,
        )
        typer.echo(_dump_json(payload))
    except Exception as exc:
        _raise_cli_exit(exc)


def _load_runtime(
    config: str | None,
    profile: str | None,
) -> tuple[JiraEndpoints, CustomFieldsConfig]:
    profile_config = load_profile(config, profile)
    token = os.getenv(profile_config.api_token_env)
    if not token:
        raise ValueError(f"Missing API token env var: {profile_config.api_token_env}")

    client = JiraHttpClient(
        base_url=profile_config.base_url,
        email=profile_config.email,
        api_token=token,
    )
    return JiraEndpoints(client), profile_config.custom_fields


def _parse_fields(fields: list[str] | None) -> list[str] | None:
    if not fields:
        return None
    parsed: list[str] = []
    for value in fields:
        parsed.extend(item.strip() for item in value.split(",") if item.strip())
    return parsed or None


def _dump_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"))


def _select_issue_fields(payload: dict, requested_fields: list[str]) -> dict[str, object]:
    issue_fields = payload.get("fields")
    if not isinstance(issue_fields, dict):
        issue_fields = {}
    return {name: issue_fields.get(name) for name in requested_fields}


def _raise_cli_exit(exc: Exception) -> None:
    err = _handle_exception(exc)
    typer.echo(print_error(err.code, err.message, err.details))
    raise typer.Exit(code=err.exit_code)


def _handle_exception(exc: Exception) -> CliError:
    if isinstance(exc, CliError):
        return exc
    if isinstance(exc, KeyError):
        return CliError(
            code="VALIDATION_ERROR",
            message=str(exc),
            details={},
            exit_code=exit_codes.VALIDATION,
        )
    if isinstance(exc, IndexError):
        return CliError(
            code="INTERNAL_ERROR",
            message="Internal error",
            details={},
            exit_code=exit_codes.INTERNAL,
        )
    if isinstance(exc, LookupError):
        return CliError(
            code="NOT_FOUND",
            message=str(exc),
            details={},
            exit_code=exit_codes.NOT_FOUND,
        )
    if isinstance(exc, ValueError):
        return CliError(
            code="VALIDATION_ERROR",
            message=str(exc),
            details={},
            exit_code=exit_codes.VALIDATION,
        )
    return CliError(
        code="INTERNAL_ERROR",
        message="Internal error",
        details={},
        exit_code=exit_codes.INTERNAL,
    )
