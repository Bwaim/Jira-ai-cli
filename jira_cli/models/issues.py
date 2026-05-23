from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateIssueInput:
    project_key: str
    issue_type: str
    summary: str
    original_estimate: str | None = None
    sprint: int | None = None
    story_points: int | float | None = None
