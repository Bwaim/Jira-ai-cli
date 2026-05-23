from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CustomFieldsConfig:
    global_fields: dict[str, str] = field(default_factory=dict)
    project_overrides: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfileConfig:
    base_url: str
    email: str
    api_token_env: str = "JIRA_API_TOKEN"
    custom_fields: CustomFieldsConfig = field(default_factory=CustomFieldsConfig)
