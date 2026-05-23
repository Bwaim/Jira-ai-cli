from typer.testing import CliRunner

from jira_cli.cli.main import app

runner = CliRunner()


def test_init_writes_config_template_to_requested_path(tmp_path):
    cfg = tmp_path / "config.toml"

    result = runner.invoke(app, ["init", "--config", str(cfg)])

    assert result.exit_code == 0
    assert result.stdout.strip() == f'{{"ok":true,"config_path":"{cfg}"}}'
    assert cfg.exists()
    assert cfg.read_text(encoding="utf-8") == (
        '[profiles.default]\n'
        'base_url = "https://your-domain.atlassian.net"\n'
        'email = "you@example.com"\n'
        'api_token_env = "JIRA_API_TOKEN"\n'
    )


def test_init_print_env_template():
    result = runner.invoke(app, ["init", "--print-env-template"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "JIRA_API_TOKEN=your_jira_api_token"


def test_init_existing_file_without_force_returns_validation_error(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text("existing = true\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(cfg)])

    assert result.exit_code == 2
    assert '"code":"VALIDATION_ERROR"' in result.stdout
    assert "Use --force to overwrite it." in result.stdout
    assert cfg.read_text(encoding="utf-8") == "existing = true\n"


def test_init_overwrites_existing_file_with_force(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text("existing = true\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(cfg), "--force"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f'{{"ok":true,"config_path":"{cfg}"}}'
    assert cfg.read_text(encoding="utf-8") == (
        '[profiles.default]\n'
        'base_url = "https://your-domain.atlassian.net"\n'
        'email = "you@example.com"\n'
        'api_token_env = "JIRA_API_TOKEN"\n'
    )
