from __future__ import annotations

from jira_cli.config.custom_fields import resolve_custom_field
from jira_cli.config.models import CustomFieldsConfig
from jira_cli.models.issues import CreateIssueInput


def collect_create_issue_wizard_answers(
    prompt,
    *,
    project_key: str | None = None,
    issue_type: str | None = None,
    summary: str | None = None,
    original_estimate: str | None = None,
    sprint: int | None = None,
    story_points: int | float | None = None,
) -> dict[str, object]:
    answers: dict[str, object] = {}
    answers["project_key"] = prompt("Project key", default=project_key)
    answers["issue_type"] = prompt("Issue type", default=issue_type)
    answers["summary"] = prompt("Summary", default=summary)
    answers["original_estimate"] = prompt(
        "Original estimate (optional)",
        default=original_estimate,
    )
    answers["sprint"] = prompt(
        "Sprint ID (optional)",
        default=str(sprint) if sprint is not None else None,
    )
    answers["story_points"] = prompt(
        "Story points (optional)",
        default=str(story_points) if story_points is not None else None,
    )
    return answers


def build_create_issue_input(
    *,
    project_key: str,
    issue_type: str,
    summary: str,
    original_estimate: str | None = None,
    sprint: int | str | None = None,
    story_points: int | float | str | None = None,
) -> CreateIssueInput:
    project_value = _require_text(project_key, "project_key")
    issue_type_value = _require_text(issue_type, "issue_type")
    summary_value = _require_text(summary, "summary")

    return CreateIssueInput(
        project_key=project_value,
        issue_type=issue_type_value,
        summary=summary_value,
        original_estimate=_none_if_blank(original_estimate),
        sprint=_parse_optional_int(sprint),
        story_points=_parse_optional_float(story_points),
    )


def build_create_issue_payload(
    issue: CreateIssueInput,
    custom_fields: CustomFieldsConfig,
) -> dict:
    fields: dict[str, object] = {
        "project": {"key": issue.project_key},
        "issuetype": {"name": issue.issue_type},
        "summary": issue.summary,
    }

    if issue.original_estimate:
        fields["timetracking"] = {"originalEstimate": issue.original_estimate}

    if issue.sprint is not None:
        sprint_field = resolve_custom_field(custom_fields, "sprint", issue.project_key)
        if not sprint_field:
            raise ValueError(
                f"Missing custom field mapping for 'sprint' in project '{issue.project_key}'"
            )
        fields[sprint_field] = issue.sprint

    if issue.story_points is not None:
        story_points_field = resolve_custom_field(
            custom_fields,
            "story_points",
            issue.project_key,
        )
        if not story_points_field:
            raise ValueError(
                "Missing custom field mapping for "
                f"'story_points' in project '{issue.project_key}'"
            )
        fields[story_points_field] = issue.story_points

    return {"fields": fields}


def _none_if_blank(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_optional_int(value: int | str | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    cleaned = value.strip()
    if not cleaned:
        return None
    return int(cleaned)


def _parse_optional_float(value: int | float | str | None) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return value
    cleaned = value.strip()
    if not cleaned:
        return None
    return float(cleaned)


def _require_text(value: str | None, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned
