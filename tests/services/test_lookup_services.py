from jira_cli.services.lookup import (
    list_boards,
    list_issue_types,
    list_priorities,
    list_projects,
    list_sprints,
    search_users,
)


class DummyClient:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return {"path": path, "params": params}


def test_list_issue_types_calls_issue_type_endpoint():
    client = DummyClient()
    expected = [{"id": "10000", "name": "Task"}]
    calls = []

    def fake_get(path, params=None):
        calls.append((path, params))
        return expected

    client.get = fake_get  # type: ignore[method-assign]

    payload = list_issue_types(client)

    assert payload == expected
    assert calls == [("/rest/api/3/issuetype", None)]


def test_list_projects_calls_project_search_endpoint():
    client = DummyClient()

    payload = list_projects(client)

    assert payload == {"path": "/rest/api/3/project/search", "params": None}
    assert client.calls == [('/rest/api/3/project/search', None)]


def test_list_boards_passes_project_and_type_filters():
    client = DummyClient()

    payload = list_boards(client, project_key="ENG", board_type="scrum")

    assert payload == {
        "path": "/rest/agile/1.0/board",
        "params": {"projectKeyOrId": "ENG", "type": "scrum"},
    }
    assert client.calls == [
        ("/rest/agile/1.0/board", {"projectKeyOrId": "ENG", "type": "scrum"})
    ]


def test_list_sprints_joins_repeated_state_filters():
    client = DummyClient()

    payload = list_sprints(client, board_id=42, states=["active", "future"])

    assert payload == {
        "path": "/rest/agile/1.0/board/42/sprint",
        "params": {"state": "active,future"},
    }
    assert client.calls == [
        ("/rest/agile/1.0/board/42/sprint", {"state": "active,future"})
    ]


def test_list_priorities_calls_priority_search_endpoint():
    client = DummyClient()

    payload = list_priorities(client)

    assert payload == {"path": "/rest/api/3/priority/search", "params": None}
    assert client.calls == [('/rest/api/3/priority/search', None)]


def test_search_users_passes_query_parameter():
    client = DummyClient()
    expected = [{"accountId": "abc", "displayName": "John"}]
    calls = []

    def fake_get(path, params=None):
        calls.append((path, params))
        return expected

    client.get = fake_get  # type: ignore[method-assign]

    payload = search_users(client, query="john")

    assert payload == expected
    assert calls == [("/rest/api/3/user/search", {"query": "john"})]
