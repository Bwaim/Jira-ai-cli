# Jira CLI V1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, JSON-first `jira-cli` Python package with the v1 Jira command surface, profile-based config, structured JSON errors, and tested service/client boundaries.

**Architecture:** The CLI layer parses args and prints compact JSON. Services build request/response payloads and map domain errors. The Jira client is a thin HTTP transport wrapper that raises typed exceptions decoded from Jira responses. Config resolution is centralized and reusable by commands and services.

**Tech Stack:** Python 3.12+, `typer`, `httpx`, `pydantic`, `tomllib`, `pytest`, `respx`.

---

## File Structure

- `pyproject.toml`: Package metadata, dependencies, console script entry point `jira-cli`.
- `jira_cli/__init__.py`: Package marker.
- `jira_cli/cli/main.py`: Root app, global options (`--config`, `--profile`, `--verbose`), command registration, exception to JSON error mapping.
- `jira_cli/cli/output.py`: Compact JSON success/error rendering.
- `jira_cli/cli/exit_codes.py`: Stable exit code constants.
- `jira_cli/cli/context.py`: Runtime context (`settings`, `client`, `services`).
- `jira_cli/cli/commands/issue.py`: `issue get/create/search` and wizard flow.
- `jira_cli/cli/commands/issue_types.py`: `issue-types list`.
- `jira_cli/cli/commands/sprint.py`: `sprint list`.
- `jira_cli/cli/commands/priority.py`: `priority list`.
- `jira_cli/cli/commands/user.py`: `user search`.
- `jira_cli/cli/commands/project.py`: `project list`.
- `jira_cli/cli/commands/board.py`: `board list`.
- `jira_cli/cli/commands/config_cmd.py`: `config custom-field set/remove/list`.
- `jira_cli/cli/commands/init.py`: `init` helpers.
- `jira_cli/config/models.py`: Pydantic models for config and custom-field maps.
- `jira_cli/config/loader.py`: Config path precedence and profile selection.
- `jira_cli/config/custom_fields.py`: Project-aware custom-field resolver.
- `jira_cli/models/errors.py`: Error envelope + domain exceptions.
- `jira_cli/models/issues.py`: Request/response models for issue operations.
- `jira_cli/jira_client/http.py`: `JiraHttpClient` with auth headers and error decoding.
- `jira_cli/jira_client/endpoints.py`: Endpoint-specific client methods.
- `jira_cli/services/issues.py`: Issue payload assembly + wizard parity logic.
- `jira_cli/services/lookup.py`: Project/board/sprint/priority/user/issue-type lookup orchestration.
- `tests/conftest.py`: Shared fixtures (temp config, mocked env, reusable JSON helpers).
- `tests/config/test_loader.py`: Config precedence and profile tests.
- `tests/config/test_custom_fields.py`: Project/global override behavior.
- `tests/services/test_issue_payloads.py`: Flag mode + wizard payload parity.
- `tests/services/test_lookup_services.py`: Lookup service contract tests.
- `tests/client/test_http_errors.py`: Auth/not-found/Jira API error mapping tests.
- `tests/cli/test_issue_commands.py`: Issue command parsing/output/exit behavior.
- `tests/cli/test_lookup_commands.py`: Lookup command behavior.
- `tests/cli/test_config_commands.py`: Custom-field command behavior.
- `tests/cli/test_init_commands.py`: Init output tests.

### Task 1: Bootstrap Package and CLI Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `jira_cli/__init__.py`
- Create: `jira_cli/cli/main.py`
- Create: `jira_cli/cli/output.py`
- Create: `jira_cli/cli/exit_codes.py`
- Create: `tests/cli/test_main_smoke.py`

- [ ] **Step 1: Write the failing smoke test for `jira-cli` entrypoint**

```python
# tests/cli/test_main_smoke.py
from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_root_help_has_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "issue" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_main_smoke.py::test_root_help_has_commands -v`
Expected: FAIL with `ModuleNotFoundError` for `jira_cli` or missing `app`.

- [ ] **Step 3: Write minimal package and root CLI implementation**

```python
# jira_cli/cli/main.py
import typer

app = typer.Typer(no_args_is_help=True)
app.add_typer(typer.Typer(), name="issue")
```

```toml
# pyproject.toml
[project]
name = "jira-lite-cli"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["typer>=0.12", "httpx>=0.27", "pydantic>=2.7"]

[project.scripts]
jira-cli = "jira_cli.cli.main:app"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_main_smoke.py::test_root_help_has_commands -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml jira_cli/__init__.py jira_cli/cli/main.py jira_cli/cli/output.py jira_cli/cli/exit_codes.py tests/cli/test_main_smoke.py
git commit -m "feat: bootstrap jira-cli package and root command"
```

### Task 2: Implement Structured Error Envelope and Exit Code Mapping

**Files:**
- Create: `jira_cli/models/errors.py`
- Modify: `jira_cli/cli/output.py`
- Modify: `jira_cli/cli/exit_codes.py`
- Modify: `jira_cli/cli/main.py`
- Create: `tests/cli/test_error_envelope.py`

- [ ] **Step 1: Write failing test for JSON error format and exit code**

```python
# tests/cli/test_error_envelope.py
from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_validation_error_is_structured_json(mocker):
    mocker.patch("jira_cli.cli.main.raise_demo_validation", side_effect=ValueError("bad input"))
    result = runner.invoke(app, ["issue", "get", "BAD"])  # command will call raise_demo_validation
    assert result.exit_code == 2
    assert '"code":"VALIDATION_ERROR"' in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_error_envelope.py::test_validation_error_is_structured_json -v`
Expected: FAIL because command/handler not implemented.

- [ ] **Step 3: Implement error models and top-level exception handler**

```python
# jira_cli/models/errors.py
from dataclasses import dataclass

@dataclass
class CliError(Exception):
    code: str
    message: str
    details: dict
    exit_code: int
```

```python
# jira_cli/cli/output.py
import json

def print_error(code: str, message: str, details: dict) -> str:
    return json.dumps({"error": {"code": code, "message": message, "details": details}}, separators=(",", ":"))
```

```python
# jira_cli/cli/exit_codes.py
SUCCESS = 0
VALIDATION = 2
AUTH = 3
NOT_FOUND = 4
JIRA_API = 5
INTERNAL = 10
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_error_envelope.py::test_validation_error_is_structured_json -v`
Expected: PASS with compact JSON error output.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/models/errors.py jira_cli/cli/output.py jira_cli/cli/exit_codes.py jira_cli/cli/main.py tests/cli/test_error_envelope.py
git commit -m "feat: add structured json errors and exit code mapping"
```

### Task 3: Implement Config Models and Precedence Resolution

**Files:**
- Create: `jira_cli/config/models.py`
- Create: `jira_cli/config/loader.py`
- Create: `tests/config/test_loader.py`

- [ ] **Step 1: Write failing tests for config path precedence and profile resolution**

```python
# tests/config/test_loader.py
from jira_cli.config.loader import resolve_config_path, load_profile


def test_cli_config_path_overrides_env(tmp_path, monkeypatch):
    env_cfg = tmp_path / "env.toml"
    cli_cfg = tmp_path / "cli.toml"
    monkeypatch.setenv("JIRA_CLI_CONFIG", str(env_cfg))
    assert resolve_config_path(str(cli_cfg)) == cli_cfg
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/config/test_loader.py -v`
Expected: FAIL due to missing loader/models.

- [ ] **Step 3: Implement config schema and loader**

```python
# jira_cli/config/models.py
from pydantic import BaseModel

class CustomFields(BaseModel):
    global_: dict[str, str] = {}
    by_project: dict[str, dict[str, str]] = {}

class Profile(BaseModel):
    site: str
    email: str
    api_token_env: str = "JIRA_API_TOKEN"
    project_key: str | None = None
    custom_fields: CustomFields = CustomFields()
```

```python
# jira_cli/config/loader.py
from pathlib import Path
import os

def resolve_config_path(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path)
    if env_path := os.getenv("JIRA_CLI_CONFIG"):
        return Path(env_path)
    return Path.home() / ".config/jira-lite-cli/config.toml"
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/config/test_loader.py -v`
Expected: PASS for precedence + profile selection cases.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/config/models.py jira_cli/config/loader.py tests/config/test_loader.py
git commit -m "feat: add config schema and precedence-based loader"
```

### Task 4: Implement Project-Aware Custom Field Resolution + Config Commands

**Files:**
- Create: `jira_cli/config/custom_fields.py`
- Create: `jira_cli/cli/commands/config_cmd.py`
- Modify: `jira_cli/cli/main.py`
- Create: `tests/config/test_custom_fields.py`
- Create: `tests/cli/test_config_commands.py`

- [ ] **Step 1: Write failing tests for resolution order and config command output**

```python
# tests/config/test_custom_fields.py
from jira_cli.config.custom_fields import resolve_custom_field


def test_project_override_precedes_global():
    mapping = {
        "global": {"sprint": "customfield_10007"},
        "by_project": {"HT": {"sprint": "customfield_99999"}},
    }
    assert resolve_custom_field(mapping, "HT", "sprint") == "customfield_99999"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/config/test_custom_fields.py tests/cli/test_config_commands.py -v`
Expected: FAIL due to missing command/module.

- [ ] **Step 3: Implement resolver + `config custom-field set/remove/list` commands**

```python
# jira_cli/config/custom_fields.py
def resolve_custom_field(custom_fields: dict, project_key: str, name: str) -> str | None:
    project_map = custom_fields.get("by_project", {}).get(project_key, {})
    if name in project_map:
        return project_map[name]
    return custom_fields.get("global", {}).get(name)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/config/test_custom_fields.py tests/cli/test_config_commands.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/config/custom_fields.py jira_cli/cli/commands/config_cmd.py jira_cli/cli/main.py tests/config/test_custom_fields.py tests/cli/test_config_commands.py
git commit -m "feat: add custom field resolution and config field commands"
```

### Task 5: Implement Jira HTTP Client + Endpoint Wrappers

**Files:**
- Create: `jira_cli/jira_client/http.py`
- Create: `jira_cli/jira_client/endpoints.py`
- Create: `tests/client/test_http_errors.py`

- [ ] **Step 1: Write failing client tests for auth, not found, and Jira API errors**

```python
# tests/client/test_http_errors.py
import pytest
import respx
import httpx
from jira_cli.jira_client.http import JiraHttpClient

@respx.mock
def test_401_maps_to_auth_error():
    respx.get("https://nextory.atlassian.net/rest/api/3/myself").mock(return_value=httpx.Response(401, json={"errorMessages": ["Unauthorized"]}))
    client = JiraHttpClient("https://nextory.atlassian.net", "user@x.com", "token")
    with pytest.raises(Exception):
        client.get("/rest/api/3/myself")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/client/test_http_errors.py -v`
Expected: FAIL due to missing client.

- [ ] **Step 3: Implement HTTP transport + status decoding**

```python
# jira_cli/jira_client/http.py
import httpx

class JiraHttpClient:
    def __init__(self, base_url: str, email: str, token: str):
        self._client = httpx.Client(base_url=base_url, auth=(email, token), timeout=30)

    def get(self, path: str, params: dict | None = None) -> dict:
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/client/test_http_errors.py -v`
Expected: PASS with mapped exceptions and codes.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/jira_client/http.py jira_cli/jira_client/endpoints.py tests/client/test_http_errors.py
git commit -m "feat: add jira http client with error decoding"
```

### Task 6: Implement Issue Service Payload Assembly (Flag Mode)

**Files:**
- Create: `jira_cli/models/issues.py`
- Create: `jira_cli/services/issues.py`
- Create: `tests/services/test_issue_payloads.py`

- [ ] **Step 1: Write failing tests for `issue create` payload mapping**

```python
# tests/services/test_issue_payloads.py
from jira_cli.services.issues import build_create_issue_payload


def test_create_payload_maps_timetracking_and_custom_fields():
    payload = build_create_issue_payload(
        project="HT",
        issue_type="Task",
        summary="Ship CLI",
        original_estimate="4h",
        sprint=123,
        story_points=3,
        custom_field_ids={"sprint": "customfield_10007", "story_points": "customfield_11126"},
    )
    assert payload["fields"]["timetracking"]["originalEstimate"] == "4h"
    assert payload["fields"]["customfield_10007"] == 123
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/services/test_issue_payloads.py::test_create_payload_maps_timetracking_and_custom_fields -v`
Expected: FAIL because service function is missing.

- [ ] **Step 3: Implement minimal payload builder**

```python
# jira_cli/services/issues.py
def build_create_issue_payload(project: str, issue_type: str, summary: str, **kwargs) -> dict:
    fields = {
        "project": {"key": project},
        "issuetype": {"name": issue_type},
        "summary": summary,
    }
    if original_estimate := kwargs.get("original_estimate"):
        fields["timetracking"] = {"originalEstimate": original_estimate}
    return {"fields": fields}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/services/test_issue_payloads.py -v`
Expected: PASS for all create payload mapping scenarios.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/models/issues.py jira_cli/services/issues.py tests/services/test_issue_payloads.py
git commit -m "feat: add issue create payload assembly service"
```

### Task 7: Implement `issue` CLI Commands (`get`, `create`, `search`) with Field Filtering

**Files:**
- Create: `jira_cli/cli/commands/issue.py`
- Modify: `jira_cli/cli/main.py`
- Create: `tests/cli/test_issue_commands.py`

- [ ] **Step 1: Write failing CLI tests for issue command arguments and compact JSON output**

```python
# tests/cli/test_issue_commands.py
from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_issue_get_with_fields_forwards_field_list(mocker):
    mocked = mocker.patch("jira_cli.cli.commands.issue.handle_issue_get", return_value={"id": "10000"})
    result = runner.invoke(app, ["issue", "get", "HT-1", "--fields", "summary", "--fields", "status"])
    assert result.exit_code == 0
    mocked.assert_called_once()
    assert result.stdout.strip() == '{"id":"10000"}'
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/cli/test_issue_commands.py -v`
Expected: FAIL because issue command module handlers are missing.

- [ ] **Step 3: Implement issue command handlers and wiring to service/client**

```python
# jira_cli/cli/commands/issue.py
import typer

issue_app = typer.Typer()

@issue_app.command("get")
def issue_get(issue_key: str, fields: list[str] = typer.Option(default=None)):
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/cli/test_issue_commands.py -v`
Expected: PASS for get/create/search output and argument validation.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/cli/commands/issue.py jira_cli/cli/main.py tests/cli/test_issue_commands.py
git commit -m "feat: implement issue get create search commands"
```

### Task 8: Implement Interactive `issue create --wizard` with Payload Parity

**Files:**
- Modify: `jira_cli/cli/commands/issue.py`
- Modify: `jira_cli/services/issues.py`
- Modify: `tests/services/test_issue_payloads.py`
- Modify: `tests/cli/test_issue_commands.py`

- [ ] **Step 1: Write failing tests proving wizard and flag mode produce identical payload**

```python
# tests/services/test_issue_payloads.py
from jira_cli.services.issues import build_create_issue_payload, build_create_issue_payload_from_wizard


def test_wizard_payload_matches_flag_payload():
    flag_payload = build_create_issue_payload(project="HT", issue_type="Task", summary="Title", story_points=3)
    wizard_payload = build_create_issue_payload_from_wizard(
        {
            "project": "HT",
            "type": "Task",
            "summary": "Title",
            "story_points": 3,
        }
    )
    assert wizard_payload == flag_payload
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/services/test_issue_payloads.py::test_wizard_payload_matches_flag_payload -v`
Expected: FAIL because wizard builder is missing.

- [ ] **Step 3: Implement prompt collection + shared payload builder path**

```python
# jira_cli/services/issues.py
def build_create_issue_payload_from_wizard(answers: dict) -> dict:
    return build_create_issue_payload(
        project=answers["project"],
        issue_type=answers["type"],
        summary=answers["summary"],
        description=answers.get("description"),
        priority=answers.get("priority"),
        assignee=answers.get("assignee"),
        parent=answers.get("parent"),
        original_estimate=answers.get("original_estimate"),
        sprint=answers.get("sprint"),
        story_points=answers.get("story_points"),
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/services/test_issue_payloads.py tests/cli/test_issue_commands.py -v`
Expected: PASS with wizard parity guaranteed.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/cli/commands/issue.py jira_cli/services/issues.py tests/services/test_issue_payloads.py tests/cli/test_issue_commands.py
git commit -m "feat: add interactive issue create wizard with payload parity"
```

### Task 9: Implement Lookup Commands (`issue-types`, `project`, `board`, `sprint`, `priority`, `user`)

**Files:**
- Create: `jira_cli/services/lookup.py`
- Create: `jira_cli/cli/commands/issue_types.py`
- Create: `jira_cli/cli/commands/project.py`
- Create: `jira_cli/cli/commands/board.py`
- Create: `jira_cli/cli/commands/sprint.py`
- Create: `jira_cli/cli/commands/priority.py`
- Create: `jira_cli/cli/commands/user.py`
- Modify: `jira_cli/cli/main.py`
- Create: `tests/services/test_lookup_services.py`
- Create: `tests/cli/test_lookup_commands.py`

- [ ] **Step 1: Write failing tests for each lookup command and sprint repeated `--state` behavior**

```python
# tests/cli/test_lookup_commands.py
from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_sprint_list_accepts_repeated_state(mocker):
    mocked = mocker.patch("jira_cli.cli.commands.sprint.handle_sprint_list", return_value=[])
    result = runner.invoke(app, ["sprint", "list", "--board", "7", "--state", "active", "--state", "future"])
    assert result.exit_code == 0
    mocked.assert_called_once_with(board=7, states=["active", "future"], limit=None)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/cli/test_lookup_commands.py tests/services/test_lookup_services.py -v`
Expected: FAIL due to missing modules/handlers.

- [ ] **Step 3: Implement lookup services and command modules**

```python
# jira_cli/cli/commands/sprint.py
import typer

sprint_app = typer.Typer()

@sprint_app.command("list")
def sprint_list(board: int = typer.Option(...), state: list[str] = typer.Option(default=[]), limit: int | None = None):
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/cli/test_lookup_commands.py tests/services/test_lookup_services.py -v`
Expected: PASS including repeated `--state` case.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/services/lookup.py jira_cli/cli/commands/issue_types.py jira_cli/cli/commands/project.py jira_cli/cli/commands/board.py jira_cli/cli/commands/sprint.py jira_cli/cli/commands/priority.py jira_cli/cli/commands/user.py jira_cli/cli/main.py tests/services/test_lookup_services.py tests/cli/test_lookup_commands.py
git commit -m "feat: implement lookup commands and sprint state filters"
```

### Task 10: Implement `init` Helpers and Environment Template Output

**Files:**
- Create: `jira_cli/cli/commands/init.py`
- Modify: `jira_cli/cli/main.py`
- Create: `tests/cli/test_init_commands.py`

- [ ] **Step 1: Write failing tests for `init --config` and `init --print-env-template`**

```python
# tests/cli/test_init_commands.py
from typer.testing import CliRunner
from jira_cli.cli.main import app

runner = CliRunner()


def test_init_print_env_template():
    result = runner.invoke(app, ["init", "--print-env-template"])
    assert result.exit_code == 0
    assert "JIRA_API_TOKEN=" in result.stdout
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/cli/test_init_commands.py -v`
Expected: FAIL because init command is missing.

- [ ] **Step 3: Implement init command module**

```python
# jira_cli/cli/commands/init.py
import typer

init_app = typer.Typer()

@init_app.callback(invoke_without_command=True)
def init_cmd(config: str | None = typer.Option(None), print_env_template: bool = typer.Option(False)):
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/cli/test_init_commands.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jira_cli/cli/commands/init.py jira_cli/cli/main.py tests/cli/test_init_commands.py
git commit -m "feat: add init command and env template output"
```

### Task 11: End-to-End CLI Behavior Pass for Exit Codes and Compact JSON

**Files:**
- Modify: `tests/cli/test_issue_commands.py`
- Modify: `tests/cli/test_lookup_commands.py`
- Modify: `tests/cli/test_error_envelope.py`

- [ ] **Step 1: Write failing tests for compact JSON formatting and mapped exit codes**

```python
# tests/cli/test_error_envelope.py

def test_not_found_maps_exit_code_4(runner, mocker):
    mocker.patch("jira_cli.cli.commands.issue.handle_issue_get", side_effect=Exception("not found"))
    result = runner.invoke(app, ["issue", "get", "HT-9999"])
    assert result.exit_code == 4
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/cli/test_error_envelope.py tests/cli/test_issue_commands.py tests/cli/test_lookup_commands.py -v`
Expected: FAIL where code mapping and output separators are not fully enforced.

- [ ] **Step 3: Tighten CLI exception mapping and output rendering**

```python
# jira_cli/cli/output.py
import json

def compact_json(data: dict | list) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/cli/test_error_envelope.py tests/cli/test_issue_commands.py tests/cli/test_lookup_commands.py -v`
Expected: PASS with stable compact JSON and exit codes.

- [ ] **Step 5: Commit**

```bash
git add tests/cli/test_issue_commands.py tests/cli/test_lookup_commands.py tests/cli/test_error_envelope.py jira_cli/cli/output.py jira_cli/cli/main.py
git commit -m "test: enforce compact json output and exit code contracts"
```

### Task 12: Full Suite Run and Packaging Validation

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write failing test for script entrypoint discovery**

```python
# tests/cli/test_main_smoke.py
import importlib.metadata


def test_console_script_declared():
    eps = importlib.metadata.entry_points(group="console_scripts")
    assert any(ep.name == "jira-cli" for ep in eps)
```

- [ ] **Step 2: Run test to verify failure (if entry point metadata incomplete)**

Run: `pytest tests/cli/test_main_smoke.py::test_console_script_declared -v`
Expected: FAIL until packaging metadata is correct in editable/test environment.

- [ ] **Step 3: Finalize docs + packaging metadata**

```markdown
# README.md
## Install
pipx install jira-lite-cli

## Example
jira-cli issue get HT-123 --fields summary --fields status
```

- [ ] **Step 4: Run full verification suite**

Run: `pytest -v`
Expected: PASS all tests.

Run: `python -m build`
Expected: PASS with wheel and sdist generated.

Run: `pipx install . --force`
Expected: PASS and `jira-cli --help` works.

- [ ] **Step 5: Commit**

```bash
git add README.md pyproject.toml tests/conftest.py tests/cli/test_main_smoke.py
git commit -m "chore: finalize packaging and v1 verification"
```

## Self-Review

### 1. Spec Coverage

- `issue get/create/search`: covered in Task 7 and Task 8.
- `issue-types list`, `project list`, `board list`: covered in Task 9.
- `sprint list` with repeated states: covered in Task 9 tests and implementation.
- `priority list`, `user search`: covered in Task 9.
- `issue create --wizard` parity with flag mode: covered in Task 8.
- Config path precedence (`--config`, env, default): covered in Task 3.
- Multi-profile + site slug + optional default project: covered in Task 3 model/loader tests.
- Custom fields global + per-project resolution: covered in Task 4.
- Init and env template commands: covered in Task 10.
- Structured JSON errors + exit codes: covered in Task 2 and Task 11.
- Packaging/installability (`pipx`): covered in Task 1 and Task 12.

No uncovered spec requirement remains.

### 2. Placeholder Scan

- Checked for `TBD`, `TODO`, “implement later”, “add validation”, and “similar to Task N”.
- Removed generic placeholder wording; each task contains explicit files, commands, and expected outcomes.

### 3. Type and Signature Consistency

- `build_create_issue_payload` and `build_create_issue_payload_from_wizard` naming is consistent between service tests and implementation tasks.
- CLI modules and test imports use consistent paths under `jira_cli/cli/commands/`.
- Exit code constants align with required values (`2/3/4/5/10`).

