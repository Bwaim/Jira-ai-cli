from __future__ import annotations

import json

import typer

from jira_cli.cli.commands.issue import _handle_exception
from jira_cli.cli.output import print_error
from jira_cli.services.lookup import LookupService, make_lookup_service

board_app = typer.Typer()


@board_app.command("list")
def board_list(
    project: str | None = typer.Option(None, "--project"),
    type: str | None = typer.Option(None, "--type"),
    config: str | None = typer.Option(None, "--config"),
    profile: str | None = typer.Option(None, "--profile"),
) -> None:
    try:
        payload = _get_lookup_service(config, profile).boards(
            project_key=project,
            board_type=type,
        )
        typer.echo(_dump_json(payload))
    except Exception as exc:
        _raise_cli_exit(exc)


def _get_lookup_service(config: str | None, profile: str | None) -> LookupService:
    return make_lookup_service(config, profile)


def _dump_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"))


def _raise_cli_exit(exc: Exception) -> None:
    err = _handle_exception(exc)
    typer.echo(print_error(err.code, err.message, err.details))
    raise typer.Exit(code=err.exit_code)
