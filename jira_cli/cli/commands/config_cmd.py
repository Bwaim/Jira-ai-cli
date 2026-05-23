from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from jira_cli.config.loader import resolve_config_path

config_app = typer.Typer()
custom_field_app = typer.Typer()
config_app.add_typer(custom_field_app, name="custom-field")


@custom_field_app.command("set")
def custom_field_set(
    name: str,
    field_id: str,
    project: str | None = typer.Option(None, "--project"),
    config: str | None = typer.Option(None, "--config"),
) -> None:
    path = resolve_config_path(config)
    data = _load_toml_file(path)

    if project:
        project_fields = data.setdefault("project_custom_fields", {})
        project_fields.setdefault(project, {})[name] = field_id
        payload = {
            "ok": True,
            "custom_field": {"name": name, "id": field_id, "project": project},
        }
    else:
        global_fields = data.setdefault("custom_fields", {})
        global_fields[name] = field_id
        payload = {"ok": True, "custom_field": {"name": name, "id": field_id}}

    _write_toml_file(path, data)
    typer.echo(_dump_json(payload))


@custom_field_app.command("remove")
def custom_field_remove(
    name: str,
    project: str | None = typer.Option(None, "--project"),
    config: str | None = typer.Option(None, "--config"),
) -> None:
    path = resolve_config_path(config)
    data = _load_toml_file(path)

    removed = False
    if project:
        project_fields = data.get("project_custom_fields", {}).get(project, {})
        removed = project_fields.pop(name, None) is not None
        payload = {
            "ok": True,
            "removed": removed,
            "custom_field": {"name": name, "project": project},
        }
    else:
        global_fields = data.get("custom_fields", {})
        removed = global_fields.pop(name, None) is not None
        payload = {
            "ok": True,
            "removed": removed,
            "custom_field": {"name": name},
        }

    _write_toml_file(path, data)
    typer.echo(_dump_json(payload))


@custom_field_app.command("list")
def custom_field_list(
    config: str | None = typer.Option(None, "--config"),
) -> None:
    path = resolve_config_path(config)
    data = _load_toml_file(path)
    payload = {
        "custom_fields": {
            "global": data.get("custom_fields", {}),
            "by_project": data.get("project_custom_fields", {}),
        }
    }
    typer.echo(_dump_json(payload))


def _dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"))


def _load_toml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    import tomllib

    with path.open("rb") as fh:
        return tomllib.load(fh)


def _write_toml_file(path: Path, data: dict[str, Any]) -> None:
    lines: list[str] = _toml_lines(data)
    content = "\n".join(lines).rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _toml_lines(table: dict[str, Any], prefix: str = "") -> list[str]:
    lines: list[str] = []

    for key, value in table.items():
        if not isinstance(key, str) or isinstance(value, dict):
            continue
        lines.append(f"{key} = {_toml_value(value)}")

    nested_items = [
        (key, value)
        for key, value in table.items()
        if isinstance(key, str) and isinstance(value, dict)
    ]
    for key, value in nested_items:
        section = f"{prefix}.{key}" if prefix else key
        lines.append("")
        lines.append(f"[{section}]")
        lines.extend(_toml_lines(value, section))

    return lines


def _toml_value(value: Any) -> str:
    if isinstance(value, str):
        return f'"{_escape_string(value)}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if value is None:
        return '""'
    return f'"{_escape_string(str(value))}"'
