# Jira CLI Design (Standalone Python Tool)

## Overview
Build a standalone Jira CLI to reduce reliance on Atlassian MCP for common Jira operations while minimizing token usage. The tool must be installable (`pipx` primary, Homebrew secondary), extensible for future commands, and easy to test.

## Goals
- Provide a compact JSON-first CLI for high-frequency Jira workflows.
- Support a minimal but practical v1 command set.
- Keep architecture open for additional commands with low change cost.
- Support per-user and multi-profile configuration.
- Enable fast and reliable automated tests.

## Non-Goals (v1)
- OAuth/device-flow authentication.
- Arbitrary custom field passthrough.
- Non-JSON default output format.

## Packaging and Distribution
- Language/runtime: Python.
- Packaging: `pyproject.toml` with console entry point (`jira-cli`).
- Primary installation: `pipx install jira-lite-cli`.
- Secondary installation: Homebrew formula wrapping the package release artifact.

## Architecture
Split code by responsibility:

- `cli/`: command definitions, argument validation, output formatting.
- `jira_client/`: HTTP layer for Jira REST API calls.
- `services/`: orchestration and transformation logic.
- `models/`: typed request/response structures.
- `config/`: profile/config loading and validation.

Design principles:
- JSON output by default for token efficiency and scriptability.
- Clear command modules to add new subcommands safely.
- Keep HTTP and business logic separated from CLI parsing.

## Configuration
Default config path:
- `~/.config/jira-lite-cli/config.toml`

Override options:
- Env var: `JIRA_CLI_CONFIG=/path/config.toml`
- CLI: `--config /path/config.toml`

Profile model:
- Multiple profiles (e.g., `default`, `work`), selected via `--profile`.
- `site` stores Atlassian subdomain slug (e.g., `nextory` from `https://nextory.atlassian.net`).
- Base URL resolved as `https://{site}.atlassian.net`.
- `project_key` is optional and used only as a default when a command omits `--project`.
- Custom fields support global mappings plus optional per-project overrides.

Example config:

```toml
[profile.default]
site = "nextory"
email = "user@nextory.com"
api_token_env = "JIRA_API_TOKEN"
project_key = "HT" # optional default project

[profile.default.custom_fields.global]
sprint = "customfield_10007"
story_points = "customfield_11126"

[profile.default.custom_fields.by_project.HT]
sprint = "customfield_10007"
story_points = "customfield_11126"
```

Config commands:
- `jira-cli config custom-field set <name> <jira_field_id>`
- `jira-cli config custom-field remove <name>`
- `jira-cli config custom-field list`

Bootstrap helpers:
- `jira-cli init --config /path/config.toml`
- `jira-cli init --print-env-template`

## Authentication
Default auth method:
- API token + email from config/env.

Expected env vars:
- token from configured `api_token_env` (default can be `JIRA_API_TOKEN`).

No token should be persisted in clear text config by default.

## Command Surface (v1)

1. `jira-cli issue get <ISSUE_KEY> [--fields ...]`
- Fetch one issue.
- Supports reduced field projection.

2. `jira-cli issue create ...`
Required/standard fields:
- `--project`, `--type`, `--summary`

Optional fields:
- `--description`, `--priority`, `--assignee`, `--parent`, `--original-estimate`

Custom field mapping from config:
- `--sprint` -> configured sprint field id (default `customfield_10007`)
- `--story-points` -> configured story points field id (default `customfield_11126`)

Time tracking mapping:
- `--original-estimate` -> `timetracking.originalEstimate` (e.g., `1d`, `4h`)

Wizard mode:
- `jira-cli issue create --wizard`
- Interactive flow that prompts for required fields first, then optional fields.
- Uses project-aware custom field resolution order:
  1) `custom_fields.by_project.<PROJECT_KEY>`
  2) `custom_fields.global`
- Produces the same final payload contract as non-interactive flag mode.

3. `jira-cli issue-types list --project <KEY>`
- List issue types for a project.

4. `jira-cli sprint list --board <ID> [--state <STATE>]... [--limit N]`
- Supports repeated `--state` values (e.g., `--state active --state future`).

5. `jira-cli priority list`
- List Jira priorities.

6. `jira-cli user search --query "..." [--limit N]`
- Search users for assignment and discovery.

7. `jira-cli issue search --jql "..." [--fields ...] [--limit N]`
- Run JQL queries with optional field filtering.

Additional helper commands:
8. `jira-cli project list`
9. `jira-cli board list --project <KEY>`

## Output and Token Optimization
- Default output: compact JSON.
- Field filtering available on issue get/search to minimize payload.
- Avoid verbose wrappers around successful responses.
- Optional debug mode for troubleshooting only (`--verbose`).
- Wizard prompts are interactive text, but command result output remains compact JSON by default.

## Error Model
Return structured JSON errors:

```json
{
  "error": {
    "code": "AUTH_FAILED",
    "message": "Authentication failed",
    "details": {}
  }
}
```

Exit codes:
- `0`: success
- `2`: validation error
- `3`: auth error
- `4`: not found
- `5`: Jira API error
- `10`: unexpected internal error

## Extensibility Strategy
- Add each new capability as a subcommand module with a stable service interface.
- Keep config-based custom-field mapping generic (`name -> field id`) to support future fields without core refactor.
- Maintain transport-agnostic services so additional frontends (e.g., minimal UI wrapper) remain possible.

## Testing Strategy
Test stack:
- `pytest`
- HTTP mocking via `respx`
- snapshot assertions for compact JSON output

Test layers:
- Unit tests: command parsing, config resolution precedence, field mapping.
- Service tests: payload assembly for create/get/search logic.
- Client tests: HTTP status and Jira error decoding.
- Smoke test: run CLI against a stub server in CI.

## Success Criteria
- All v1 commands execute with JSON output and correct exit codes.
- `issue create` supports parent and `originalEstimate` mapping.
- `issue create --wizard` supports guided interactive creation with payload parity to flag mode.
- Sprint list supports combined state filters.
- Config supports profile selection, site slug, optional default project, and project-aware custom-field management.
- Test suite runs green locally and in CI.

## Risks and Mitigations
- Jira API differences across endpoints: isolate endpoint-specific transforms in client/service boundaries.
- Board/sprint ambiguities: keep board explicit in sprint command and provide board discovery command.
- Token leakage risks: never print secrets, resolve token from env, redact in verbose logs.

## Implementation Handoff Notes
This design intentionally keeps v1 narrow while preserving extension points for future Jira commands (transitions, comments, links, watchers, bulk operations).
