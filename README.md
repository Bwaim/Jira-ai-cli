# Jira AI CLI

A lightweight, JSON-first CLI for Jira, designed for developers, scripts, and AI agents.

## Install

```bash
pipx install jira-lite-cli
```

For local development package validation:

```bash
.venv/bin/python -m pytest -v
.venv/bin/python -m build
pipx install . --force
jira-cli --help
```

## Entrypoint

The package exposes the console script:

```text
jira-cli -> jira_cli.cli.main:app
```
