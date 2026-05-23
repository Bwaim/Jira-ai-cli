from __future__ import annotations

from jira_cli.config.models import CustomFieldsConfig


def resolve_custom_field(
    custom_fields: CustomFieldsConfig,
    name: str,
    project_key: str | None,
) -> str | None:
    if project_key:
        project_map = custom_fields.project_overrides.get(project_key, {})
        if name in project_map:
            return project_map[name]
    return custom_fields.global_fields.get(name)
