# AGENTS.md

## Project Context
This repository is building a standalone Python Jira CLI focused on low-token, script-friendly workflows.

## Primary Goal
Deliver a compact JSON-first CLI (`jira-cli`) for common Jira operations, installable with `pipx` (Homebrew secondary).

## Architecture (expected)
- `cli/`: command parsing, args, output
- `jira_client/`: Jira REST HTTP layer
- `services/`: business orchestration and payload transforms
- `models/`: typed schemas
- `config/`: profile/config loading and validation

## Core Conventions
- Default output is compact JSON.
- Keep transport (HTTP), orchestration (services), and CLI parsing separated.
- Return structured JSON errors with stable error codes and mapped exit codes.
- Never persist or print secrets; read API token from env.

## v1 Scope Highlights
- `issue get/create/search`
- `issue-types list`, `project list`, `board list`
- `sprint list`, `priority list`, `user search`
- `issue create --wizard` must produce payload parity with flag mode.

## Config Model
- Default config: `~/.config/jira-lite-cli/config.toml`
- Override: `JIRA_CLI_CONFIG` or `--config`
- Multi-profile via `--profile`
- Custom fields: global + per-project override resolution

## Quality Bar
- Tests with `pytest` + `respx`
- Validate config precedence, field mapping, payload assembly, and exit-code behavior.
