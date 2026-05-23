from unittest.mock import patch

from jira_cli.cli import exit_codes
from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_validation_error_is_structured_json():
    with patch("jira_cli.cli.main.raise_demo_validation", side_effect=ValueError("bad input")):
        result = runner.invoke(app, ["issue", "get", "BAD"])  # command will call raise_demo_validation
    assert result.exit_code == exit_codes.VALIDATION
    assert result.stdout.strip() == (
        '{"error":{"code":"VALIDATION_ERROR","message":"bad input","details":{}}}'
    )


def test_not_found_error_is_structured_json_and_uses_not_found_exit_code():
    with patch("jira_cli.cli.main.raise_demo_validation", side_effect=LookupError("not found")):
        result = runner.invoke(app, ["issue", "get", "NOPE-1"])
    assert result.exit_code == exit_codes.NOT_FOUND
    assert result.stdout.strip() == (
        '{"error":{"code":"NOT_FOUND","message":"not found","details":{}}}'
    )


def test_index_error_maps_to_internal_error_not_not_found():
    with patch("jira_cli.cli.main.raise_demo_validation", side_effect=IndexError("boom")):
        result = runner.invoke(app, ["issue", "get", "NOPE-1"])
    assert result.exit_code == exit_codes.INTERNAL
    assert result.stdout.strip() == (
        '{"error":{"code":"INTERNAL_ERROR","message":"Internal error","details":{}}}'
    )
