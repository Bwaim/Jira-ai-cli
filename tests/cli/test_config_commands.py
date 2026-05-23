import tomllib

from typer.testing import CliRunner

from jira_cli.cli.main import app

runner = CliRunner()


def _write_base_config(path):
    path.write_text(
        """
[profiles.default]
base_url = "https://jira.example"
email = "dev@example.com"
""".strip(),
        encoding="utf-8",
    )


def test_config_custom_field_set_and_list_outputs_json(tmp_path):
    cfg = tmp_path / "config.toml"
    _write_base_config(cfg)

    set_result = runner.invoke(
        app,
        [
            "config",
            "custom-field",
            "set",
            "story_points",
            "customfield_10016",
            "--config",
            str(cfg),
        ],
    )
    assert set_result.exit_code == 0
    assert (
        set_result.stdout.strip()
        == '{"ok":true,"custom_field":{"name":"story_points","id":"customfield_10016"}}'
    )

    list_result = runner.invoke(
        app,
        ["config", "custom-field", "list", "--config", str(cfg)],
    )
    assert list_result.exit_code == 0
    assert (
        list_result.stdout.strip()
        == '{"custom_fields":{"global":{"story_points":"customfield_10016"},"by_project":{}}}'
    )


def test_config_custom_field_set_with_project_and_remove(tmp_path):
    cfg = tmp_path / "config.toml"
    _write_base_config(cfg)

    set_result = runner.invoke(
        app,
        [
            "config",
            "custom-field",
            "set",
            "story_points",
            "customfield_20000",
            "--project",
            "ENG",
            "--config",
            str(cfg),
        ],
    )
    assert set_result.exit_code == 0
    assert (
        set_result.stdout.strip()
        == '{"ok":true,"custom_field":{"name":"story_points","id":"customfield_20000","project":"ENG"}}'
    )

    remove_result = runner.invoke(
        app,
        [
            "config",
            "custom-field",
            "remove",
            "story_points",
            "--project",
            "ENG",
            "--config",
            str(cfg),
        ],
    )
    assert remove_result.exit_code == 0
    assert (
        remove_result.stdout.strip()
        == '{"ok":true,"removed":true,"custom_field":{"name":"story_points","project":"ENG"}}'
    )


def test_config_custom_field_list_matches_loader_shape(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[profiles.default]
base_url = "https://jira.example"
email = "dev@example.com"

[custom_fields]
story_points = "customfield_10016"

[project_custom_fields.ENG]
story_points = "customfield_20000"
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["config", "custom-field", "list", "--config", str(cfg)],
    )
    assert result.exit_code == 0
    assert (
        result.stdout.strip()
        == '{"custom_fields":{"global":{"story_points":"customfield_10016"},"by_project":{"ENG":{"story_points":"customfield_20000"}}}}'
    )

    parsed = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert parsed["custom_fields"]["story_points"] == "customfield_10016"


def test_custom_field_set_preserves_top_level_and_typed_profile_values(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
default_profile = "work"
some_unknown_flag = true

[profiles.work]
base_url = "https://jira.example"
email = "dev@example.com"
verify_ssl = false
timeout = 30
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "config",
            "custom-field",
            "set",
            "story_points",
            "customfield_10016",
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0

    parsed = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert parsed["default_profile"] == "work"
    assert parsed["some_unknown_flag"] is True
    assert parsed["profiles"]["work"]["verify_ssl"] is False
    assert parsed["profiles"]["work"]["timeout"] == 30
    assert parsed["custom_fields"]["story_points"] == "customfield_10016"


def test_custom_field_remove_preserves_top_level_and_typed_profile_values(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
default_profile = "work"
some_unknown_count = 7

[profiles.work]
base_url = "https://jira.example"
email = "dev@example.com"
verify_ssl = true
timeout = 15

[custom_fields]
story_points = "customfield_10016"
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "config",
            "custom-field",
            "remove",
            "story_points",
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0

    parsed = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert parsed["default_profile"] == "work"
    assert parsed["some_unknown_count"] == 7
    assert parsed["profiles"]["work"]["verify_ssl"] is True
    assert parsed["profiles"]["work"]["timeout"] == 15
    assert parsed["custom_fields"] == {}
