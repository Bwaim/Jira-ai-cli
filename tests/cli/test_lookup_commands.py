import json

from typer.testing import CliRunner

from jira_cli.cli import exit_codes
from jira_cli.cli.main import app

runner = CliRunner()


class DummyLookupService:
    def __init__(self):
        self.calls = []

    def issue_types(self):
        self.calls.append(("issue_types",))
        return {"issueTypes": [{"id": "10000", "name": "Task"}]}

    def projects(self):
        self.calls.append(("projects",))
        return {"values": [{"key": "ENG", "name": "Engineering"}]}

    def boards(self, project_key=None, board_type=None):
        self.calls.append(("boards", project_key, board_type))
        return {"values": [{"id": 42, "name": "Team Board"}]}

    def sprints(self, board_id, states=None):
        self.calls.append(("sprints", board_id, states))
        return {"values": [{"id": 10, "name": "Sprint 10"}]}

    def priorities(self):
        self.calls.append(("priorities",))
        return {"values": [{"id": "1", "name": "Highest"}]}

    def users(self, query):
        self.calls.append(("users", query))
        return {"users": [{"accountId": "abc", "displayName": "John"}]}


def test_issue_types_list_outputs_compact_json(monkeypatch):
    svc = DummyLookupService()
    monkeypatch.setattr("jira_cli.cli.commands.issue_types._get_lookup_service", lambda c, p: svc)

    result = runner.invoke(app, ["issue-types", "list"])

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"issueTypes": [{"id": "10000", "name": "Task"}]}
    assert svc.calls == [("issue_types",)]


def test_project_list_outputs_compact_json(monkeypatch):
    svc = DummyLookupService()
    monkeypatch.setattr("jira_cli.cli.commands.project._get_lookup_service", lambda c, p: svc)

    result = runner.invoke(app, ["project", "list"])

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"values": [{"key": "ENG", "name": "Engineering"}]}
    assert svc.calls == [("projects",)]


def test_board_list_supports_project_and_type_filters(monkeypatch):
    svc = DummyLookupService()
    monkeypatch.setattr("jira_cli.cli.commands.board._get_lookup_service", lambda c, p: svc)

    result = runner.invoke(app, ["board", "list", "--project", "ENG", "--type", "scrum"])

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"values": [{"id": 42, "name": "Team Board"}]}
    assert svc.calls == [("boards", "ENG", "scrum")]


def test_sprint_list_supports_repeated_state_options(monkeypatch):
    svc = DummyLookupService()
    monkeypatch.setattr("jira_cli.cli.commands.sprint._get_lookup_service", lambda c, p: svc)

    result = runner.invoke(
        app,
        ["sprint", "list", "--board", "42", "--state", "active", "--state", "future"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"values": [{"id": 10, "name": "Sprint 10"}]}
    assert svc.calls == [("sprints", 42, ["active", "future"])]


def test_priority_list_outputs_compact_json(monkeypatch):
    svc = DummyLookupService()
    monkeypatch.setattr("jira_cli.cli.commands.priority._get_lookup_service", lambda c, p: svc)

    result = runner.invoke(app, ["priority", "list"])

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"values": [{"id": "1", "name": "Highest"}]}
    assert svc.calls == [("priorities",)]


def test_user_search_outputs_compact_json(monkeypatch):
    svc = DummyLookupService()
    monkeypatch.setattr("jira_cli.cli.commands.user._get_lookup_service", lambda c, p: svc)

    result = runner.invoke(app, ["user", "search", "john"])

    assert result.exit_code == 0
    assert json.loads(result.stdout.strip()) == {"users": [{"accountId": "abc", "displayName": "John"}]}
    assert svc.calls == [("users", "john")]


def test_project_list_maps_lookup_error_to_not_found_exit_code_and_compact_error_json(monkeypatch):
    class NotFoundLookupService:
        def projects(self):
            raise LookupError("Project not found")

    monkeypatch.setattr(
        "jira_cli.cli.commands.project._get_lookup_service",
        lambda c, p: NotFoundLookupService(),
    )

    result = runner.invoke(app, ["project", "list"])

    assert result.exit_code == exit_codes.NOT_FOUND
    assert (
        result.stdout.strip()
        == '{"error":{"code":"NOT_FOUND","message":"Project not found","details":{}}}'
    )
