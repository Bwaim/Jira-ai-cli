import httpx
import pytest
import respx

from jira_cli.cli import exit_codes
from jira_cli.models.errors import CliError
from jira_cli.jira_client.http import JiraHttpClient


@respx.mock
def test_auth_error_is_decoded_to_cli_error():
    base_url = "https://example.atlassian.net"
    respx.get(f"{base_url}/rest/api/3/myself").mock(
        return_value=httpx.Response(401, json={"errorMessages": ["Unauthorized"]})
    )

    client = JiraHttpClient(base_url=base_url, email="dev@example.com", api_token="token")

    with pytest.raises(CliError) as exc:
        client.get("/rest/api/3/myself")

    assert exc.value.code == "AUTH_ERROR"
    assert exc.value.exit_code == exit_codes.AUTH


@respx.mock
def test_not_found_is_decoded_to_cli_error():
    base_url = "https://example.atlassian.net"
    respx.get(f"{base_url}/rest/api/3/issue/NOPE-1").mock(
        return_value=httpx.Response(404, json={"errorMessages": ["Issue does not exist"]})
    )

    client = JiraHttpClient(base_url=base_url, email="dev@example.com", api_token="token")

    with pytest.raises(CliError) as exc:
        client.get("/rest/api/3/issue/NOPE-1")

    assert exc.value.code == "NOT_FOUND"
    assert exc.value.exit_code == exit_codes.NOT_FOUND


@respx.mock
def test_jira_api_error_includes_payload_details():
    base_url = "https://example.atlassian.net"
    payload = {
        "errorMessages": ["Field validation failed"],
        "errors": {"summary": "Summary is required"},
    }
    respx.post(f"{base_url}/rest/api/3/issue").mock(
        return_value=httpx.Response(400, json=payload)
    )

    client = JiraHttpClient(base_url=base_url, email="dev@example.com", api_token="token")

    with pytest.raises(CliError) as exc:
        client.post("/rest/api/3/issue", json={})

    assert exc.value.code == "JIRA_API_ERROR"
    assert exc.value.exit_code == exit_codes.JIRA_API
    assert exc.value.details["status"] == 400
    assert exc.value.details["errorMessages"] == payload["errorMessages"]
    assert exc.value.details["errors"] == payload["errors"]


def test_transport_error_is_decoded_to_cli_error():
    client = JiraHttpClient(
        base_url="https://example.atlassian.net",
        email="dev@example.com",
        api_token="token",
    )
    client._client = httpx.Client(transport=httpx.MockTransport(_boom_transport))

    with pytest.raises(CliError) as exc:
        client.get("/rest/api/3/myself")

    assert exc.value.code == "JIRA_API_ERROR"
    assert exc.value.exit_code == exit_codes.JIRA_API
    assert exc.value.details["errors"] == {}
    assert exc.value.details["errorMessages"]


@respx.mock
def test_non_json_success_payload_returns_empty_object():
    base_url = "https://example.atlassian.net"
    respx.get(f"{base_url}/rest/api/3/serverInfo").mock(
        return_value=httpx.Response(204, text="")
    )

    client = JiraHttpClient(base_url=base_url, email="dev@example.com", api_token="token")
    data = client.get("/rest/api/3/serverInfo")

    assert data == {}


def _boom_transport(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("dns failure", request=request)
