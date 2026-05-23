import pytest

from jira_cli.config.models import CustomFieldsConfig
from jira_cli.models.issues import CreateIssueInput
from jira_cli.services.issues import (
    build_create_issue_input,
    build_create_issue_payload,
    collect_create_issue_wizard_answers,
)


def test_build_create_issue_payload_maps_timetracking_original_estimate():
    payload = build_create_issue_payload(
        CreateIssueInput(
            project_key="ENG",
            issue_type="Task",
            summary="Implement payload mapping",
            original_estimate="2h",
        ),
        custom_fields=CustomFieldsConfig(),
    )

    assert payload == {
        "fields": {
            "project": {"key": "ENG"},
            "issuetype": {"name": "Task"},
            "summary": "Implement payload mapping",
            "timetracking": {"originalEstimate": "2h"},
        }
    }


def test_build_create_issue_payload_maps_sprint_and_story_points_custom_fields():
    payload = build_create_issue_payload(
        CreateIssueInput(
            project_key="ENG",
            issue_type="Story",
            summary="Assemble payload",
            sprint=42,
            story_points=8,
        ),
        custom_fields=CustomFieldsConfig(
            global_fields={
                "sprint": "customfield_10020",
                "story_points": "customfield_10016",
            },
            project_overrides={
                "ENG": {
                    "story_points": "customfield_20000",
                }
            },
        ),
    )

    assert payload == {
        "fields": {
            "project": {"key": "ENG"},
            "issuetype": {"name": "Story"},
            "summary": "Assemble payload",
            "customfield_10020": 42,
            "customfield_20000": 8,
        }
    }


def test_build_create_issue_payload_fails_when_sprint_mapping_missing():
    with pytest.raises(
        ValueError,
        match="Missing custom field mapping for 'sprint' in project 'ENG'",
    ):
        build_create_issue_payload(
            CreateIssueInput(
                project_key="ENG",
                issue_type="Story",
                summary="Assemble payload",
                sprint=42,
            ),
            custom_fields=CustomFieldsConfig(),
        )


def test_build_create_issue_payload_fails_when_story_points_mapping_missing():
    with pytest.raises(
        ValueError,
        match="Missing custom field mapping for 'story_points' in project 'ENG'",
    ):
        build_create_issue_payload(
            CreateIssueInput(
                project_key="ENG",
                issue_type="Story",
                summary="Assemble payload",
                story_points=8,
            ),
            custom_fields=CustomFieldsConfig(),
        )


def test_wizard_and_flag_mode_produce_identical_payloads():
    wizard_answers = collect_create_issue_wizard_answers(
        prompt=lambda _message, default=None: {
            "Project key": "ENG",
            "Issue type": "Story",
            "Summary": "Implement wizard parity",
            "Original estimate (optional)": "2h",
            "Sprint ID (optional)": "42",
            "Story points (optional)": "8",
        }[_message]
    )
    wizard_input = build_create_issue_input(**wizard_answers)
    flag_input = build_create_issue_input(
        project_key="ENG",
        issue_type="Story",
        summary="Implement wizard parity",
        original_estimate="2h",
        sprint=42,
        story_points=8,
    )
    custom_fields = CustomFieldsConfig(
        global_fields={
            "sprint": "customfield_10020",
            "story_points": "customfield_10016",
        }
    )

    assert build_create_issue_payload(wizard_input, custom_fields) == build_create_issue_payload(
        flag_input,
        custom_fields,
    )


@pytest.mark.parametrize("field_name, kwargs", [
    ("project_key", {"project_key": "   ", "issue_type": "Task", "summary": "S"}),
    ("issue_type", {"project_key": "ENG", "issue_type": "   ", "summary": "S"}),
    ("summary", {"project_key": "ENG", "issue_type": "Task", "summary": "   "}),
])
def test_build_create_issue_input_rejects_blank_required_fields(field_name, kwargs):
    with pytest.raises(ValueError, match=rf"{field_name} is required"):
        build_create_issue_input(**kwargs)
