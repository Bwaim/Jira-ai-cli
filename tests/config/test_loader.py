from pathlib import Path

import pytest

from jira_cli.config.loader import DEFAULT_CONFIG_PATH, load_profile, resolve_config_path


def test_cli_config_path_overrides_env(tmp_path, monkeypatch):
    env_cfg = tmp_path / "env.toml"
    cli_cfg = tmp_path / "cli.toml"
    monkeypatch.setenv("JIRA_CLI_CONFIG", str(env_cfg))
    assert resolve_config_path(str(cli_cfg)) == cli_cfg


def test_env_config_path_used_when_cli_not_provided(tmp_path, monkeypatch):
    env_cfg = tmp_path / "env.toml"
    monkeypatch.setenv("JIRA_CLI_CONFIG", str(env_cfg))
    assert resolve_config_path(None) == env_cfg


def test_default_config_path_used_when_no_cli_or_env(monkeypatch):
    monkeypatch.delenv("JIRA_CLI_CONFIG", raising=False)
    assert resolve_config_path(None) == DEFAULT_CONFIG_PATH.expanduser()


def test_load_profile_returns_requested_profile(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[profiles.default]
base_url = "https://default.example"
email = "default@example.com"

[profiles.work]
base_url = "https://work.example"
email = "work@example.com"
api_token_env = "WORK_TOKEN"
""".strip()
    )

    profile = load_profile(cfg, "work")
    assert profile.base_url == "https://work.example"
    assert profile.email == "work@example.com"
    assert profile.api_token_env == "WORK_TOKEN"


def test_load_profile_defaults_to_default_profile(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[profiles.default]
base_url = "https://default.example"
email = "default@example.com"
""".strip()
    )

    profile = load_profile(cfg, None)
    assert profile.base_url == "https://default.example"
    assert profile.email == "default@example.com"


def test_load_profile_uses_default_profile_setting(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
default_profile = "work"

[profiles.default]
base_url = "https://default.example"
email = "default@example.com"

[profiles.work]
base_url = "https://work.example"
email = "work@example.com"
""".strip()
    )

    profile = load_profile(cfg, None)
    assert profile.base_url == "https://work.example"
    assert profile.email == "work@example.com"


def test_load_profile_raises_on_non_mapping_profiles(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('profiles = "oops"')

    with pytest.raises(ValueError, match="'profiles' must be a mapping"):
        load_profile(cfg, None)


def test_load_profile_raises_on_non_mapping_profile_data(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('profiles = { default = "oops" }')

    with pytest.raises(ValueError, match="profile 'default' must be a mapping"):
        load_profile(cfg, None)


def test_load_profile_raises_on_non_string_custom_fields(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[profiles.default]
base_url = "https://default.example"
email = "default@example.com"

[custom_fields]
story_points = 42
""".strip()
    )

    with pytest.raises(
        ValueError, match="custom field keys and values must be strings"
    ):
        load_profile(cfg, None)
