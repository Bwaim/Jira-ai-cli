from jira_cli.config.custom_fields import resolve_custom_field
from jira_cli.config.models import CustomFieldsConfig


def test_resolve_custom_field_uses_project_override_first():
    fields = CustomFieldsConfig(
        global_fields={"story_points": "customfield_10016"},
        project_overrides={
            "ENG": {"story_points": "customfield_20000"},
        },
    )

    assert resolve_custom_field(fields, "story_points", "ENG") == "customfield_20000"


def test_resolve_custom_field_falls_back_to_global():
    fields = CustomFieldsConfig(
        global_fields={"story_points": "customfield_10016"},
        project_overrides={"ENG": {"severity": "customfield_30000"}},
    )

    assert resolve_custom_field(fields, "story_points", "ENG") == "customfield_10016"


def test_resolve_custom_field_returns_none_when_missing_everywhere():
    fields = CustomFieldsConfig(
        global_fields={},
        project_overrides={"ENG": {}},
    )

    assert resolve_custom_field(fields, "story_points", "ENG") is None
