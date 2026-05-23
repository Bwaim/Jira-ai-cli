import json

from typer.testing import CliRunner

from jira_cli.cli import exit_codes
from jira_cli.cli.main import app
from jira_cli.config.models import CustomFieldsConfig

runner = CliRunner()


class DummyEndpoints:
    def __init__(self) -> None:
        self.last_get = None
        self.last_search = None
        self.last_create = None

    def get_issue(self, issue_key, fields=None):
        self.last_get = (issue_key, fields)
        return {
            "key": issue_key,
            "fields": {"summary": "Sample"},
            "self": f"https://example.atlassian.net/rest/api/3/issue/{issue_key}",
        }

    def search_issues(self, jql, fields=None, limit=None):
        self.last_search = (jql, fields, limit)
        return {"issues": [{"key": "ENG-1"}], "total": 1}

    def create_issue(self, payload):
        self.last_create = payload
        return {"id": "10001", "key": "ENG-1"}


def test_issue_get_accepts_repeated_fields_option_and_outputs_compact_json(monkeypatch):
    endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (endpoints, CustomFieldsConfig()),
    )

    result = runner.invoke(
        app,
        ["issue", "get", "ENG-1", "--fields", "summary", "--fields", "status"],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == '{"summary":"Sample","status":null}'
    assert endpoints.last_get == ("ENG-1", ["summary", "status"])


def test_issue_get_without_fields_keeps_full_payload(monkeypatch):
    endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (endpoints, CustomFieldsConfig()),
    )

    result = runner.invoke(app, ["issue", "get", "ENG-1"])

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {
        "key": "ENG-1",
        "fields": {"summary": "Sample"},
        "self": "https://example.atlassian.net/rest/api/3/issue/ENG-1",
    }
    assert endpoints.last_get == ("ENG-1", None)


def test_issue_create_uses_endpoint_and_outputs_compact_json(monkeypatch):
    endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (
            endpoints,
            CustomFieldsConfig(global_fields={"story_points": "customfield_10016"}),
        ),
    )

    result = runner.invoke(
        app,
        [
            "issue",
            "create",
            "ENG",
            "Task",
            "Implement Task 7",
            "--story-points",
            "3",
            "--original-estimate",
            "2h",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == '{"id":"10001","key":"ENG-1"}'
    assert endpoints.last_create is not None
    assert endpoints.last_create == {
        "fields": {
            "project": {"key": "ENG"},
            "issuetype": {"name": "Task"},
            "summary": "Implement Task 7",
            "timetracking": {"originalEstimate": "2h"},
            "customfield_10016": 3,
        }
    }


def test_issue_search_accepts_repeated_fields_limit_and_outputs_compact_json(monkeypatch):
    endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (endpoints, CustomFieldsConfig()),
    )

    result = runner.invoke(
        app,
        [
            "issue",
            "search",
            'project = "ENG" ORDER BY created DESC',
            "--fields",
            "summary",
            "--fields",
            "assignee",
            "--limit",
            "25",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"issues": [{"key": "ENG-1"}], "total": 1}
    assert endpoints.last_search == (
        'project = "ENG" ORDER BY created DESC',
        ["summary", "assignee"],
        25,
    )


def test_issue_create_wizard_produces_same_payload_as_flag_mode(monkeypatch):
    wizard_endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (
            wizard_endpoints,
            CustomFieldsConfig(
                global_fields={
                    "sprint": "customfield_10020",
                    "story_points": "customfield_10016",
                }
            ),
        ),
    )

    wizard_result = runner.invoke(
        app,
        ["issue", "create", "--wizard"],
        input="ENG\nTask\nImplement Task 8\n2h\n42\n3\n",
    )

    assert wizard_result.exit_code == 0
    assert wizard_endpoints.last_create is not None

    flag_endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (
            flag_endpoints,
            CustomFieldsConfig(
                global_fields={
                    "sprint": "customfield_10020",
                    "story_points": "customfield_10016",
                }
            ),
        ),
    )

    flag_result = runner.invoke(
        app,
        [
            "issue",
            "create",
            "ENG",
            "Task",
            "Implement Task 8",
            "--original-estimate",
            "2h",
            "--sprint",
            "42",
            "--story-points",
            "3",
        ],
    )

    assert flag_result.exit_code == 0
    assert flag_endpoints.last_create is not None
    assert wizard_endpoints.last_create == flag_endpoints.last_create


def test_issue_create_wizard_rejects_blank_required_fields(monkeypatch):
    endpoints = DummyEndpoints()
    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (
            endpoints,
            CustomFieldsConfig(
                global_fields={
                    "sprint": "customfield_10020",
                    "story_points": "customfield_10016",
                }
            ),
        ),
    )

    monkeypatch.setattr(
        "jira_cli.cli.commands.issue.collect_create_issue_wizard_answers",
        lambda prompt, **kwargs: {
            "project_key": "   ",
            "issue_type": "Task",
            "summary": "Summary",
            "original_estimate": "2h",
            "sprint": "42",
            "story_points": "3",
        },
    )

    result = runner.invoke(app, ["issue", "create", "--wizard"])

    assert result.exit_code == 2
    assert '"code":"VALIDATION_ERROR"' in result.stdout
    assert '"message":"project_key is required"' in result.stdout


def test_issue_get_maps_lookup_error_to_not_found_exit_code_and_compact_error_json(monkeypatch):
    class NotFoundEndpoints:
        def get_issue(self, issue_key, fields=None):
            raise LookupError(f"Issue {issue_key} not found")

    monkeypatch.setattr(
        "jira_cli.cli.commands.issue._load_runtime",
        lambda config, profile: (NotFoundEndpoints(), CustomFieldsConfig()),
    )

    result = runner.invoke(app, ["issue", "get", "NOPE-1"])

    assert result.exit_code == exit_codes.NOT_FOUND
    assert result.stdout.strip() == (
        '{"error":{"code":"NOT_FOUND","message":"Issue NOPE-1 not found","details":{}}}'
    )
