import importlib.metadata

from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_root_help_has_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "issue" in result.stdout


def test_console_script_entrypoint_is_discoverable():
    entry_points = importlib.metadata.entry_points(group="console_scripts")
    matches = [
        ep
        for ep in entry_points
        if ep.name == "jira-cli" and ep.value == "jira_cli.cli.main:app"
    ]
    assert matches
