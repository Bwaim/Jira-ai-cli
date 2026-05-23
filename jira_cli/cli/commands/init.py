from __future__ import annotations

import json
from pathlib import Path

import typer

from jira_cli.cli import exit_codes
from jira_cli.cli.output import print_error
from jira_cli.config.loader import resolve_config_path
from jira_cli.models.errors import CliError

init_app = typer.Typer()

_CONFIG_TEMPLATE = (
    '[profiles.default]\n'
    'base_url = "https://your-domain.atlassian.net"\n'
    'email = "you@example.com"\n'
    'api_token_env = "JIRA_API_TOKEN"\n'
)
_ENV_TEMPLATE = "JIRA_API_TOKEN=your_jira_api_token"


@init_app.callback(invoke_without_command=True)
def init_cmd(
    config: str | None = typer.Option(None, "--config"),
    print_env_template: bool = typer.Option(False, "--print-env-template"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    try:
        if print_env_template:
            typer.echo(_ENV_TEMPLATE)
            return

        path = resolve_config_path(config)
        _write_template(path, force=force)
        typer.echo(
            json.dumps({"ok": True, "config_path": str(path)}, separators=(",", ":"))
        )
    except Exception as exc:
        _raise_cli_exit(exc)


def _write_template(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(
            f"Config file already exists at {path}. Use --force to overwrite it."
        )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_CONFIG_TEMPLATE, encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"Failed to write config file at {path}. Check path permissions and parent directory."
        ) from exc


def _raise_cli_exit(exc: Exception) -> None:
    err = _handle_exception(exc)
    typer.echo(print_error(err.code, err.message, err.details))
    raise typer.Exit(code=err.exit_code)


def _handle_exception(exc: Exception) -> CliError:
    if isinstance(exc, CliError):
        return exc
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
