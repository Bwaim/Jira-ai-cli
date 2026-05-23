from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jira_cli.config.models import CustomFieldsConfig, ProfileConfig

DEFAULT_CONFIG_PATH = Path("~/.config/jira-lite-cli/config.toml")


def resolve_config_path(cli_config: str | Path | None) -> Path:
    if cli_config:
        return Path(cli_config).expanduser()

    env_path = os.getenv("JIRA_CLI_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    return DEFAULT_CONFIG_PATH.expanduser()


def load_profile(config_path: str | Path | None, profile: str | None) -> ProfileConfig:
    resolved_path = resolve_config_path(config_path)
    data = _load_toml(resolved_path)

    profiles = data.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("Malformed config: 'profiles' must be a mapping")

    selected_profile = profile or data.get("default_profile", "default")
    if not isinstance(selected_profile, str):
        raise ValueError("Malformed config: selected profile name must be a string")

    profile_data = profiles.get(selected_profile)
    if profile_data is None:
        raise KeyError(f"Profile not found: {selected_profile}")
    if not isinstance(profile_data, dict):
        raise ValueError(
            f"Malformed config: profile '{selected_profile}' must be a mapping"
        )

    base_url = profile_data.get("base_url")
    if not isinstance(base_url, str):
        raise ValueError(
            f"Malformed config: profile '{selected_profile}.base_url' must be a string"
        )
    email = profile_data.get("email")
    if not isinstance(email, str):
        raise ValueError(
            f"Malformed config: profile '{selected_profile}.email' must be a string"
        )
    api_token_env = profile_data.get("api_token_env", "JIRA_API_TOKEN")
    if not isinstance(api_token_env, str):
        raise ValueError(
            f"Malformed config: profile '{selected_profile}.api_token_env' must be a string"
        )

    global_fields = _string_map(data.get("custom_fields", {}))
    project_overrides = _nested_string_map(data.get("project_custom_fields", {}))
    custom_fields = CustomFieldsConfig(
        global_fields=global_fields,
        project_overrides=project_overrides,
    )

    return ProfileConfig(
        base_url=base_url,
        email=email,
        api_token_env=api_token_env,
        custom_fields=custom_fields,
    )


def _load_toml(path: Path) -> dict[str, Any]:
    import tomllib

    with path.open("rb") as fh:
        return tomllib.load(fh)


def _string_map(data: Any) -> dict[str, str]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Malformed config: custom field maps must be mappings")
    result: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(
                "Malformed config: custom field keys and values must be strings"
            )
        result[key] = value
    return result


def _nested_string_map(data: Any) -> dict[str, dict[str, str]]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Malformed config: project custom fields must be a mapping")
    result: dict[str, dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise ValueError("Malformed config: project keys must be strings")
        result[key] = _string_map(value)
    return result
