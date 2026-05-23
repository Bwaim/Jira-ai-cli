import typer

from jira_cli.cli.commands.board import board_app
from jira_cli.cli.commands.config_cmd import config_app
from jira_cli.cli.commands.issue import issue_app, set_validation_hook
from jira_cli.cli.commands.issue_types import issue_types_app
from jira_cli.cli.commands.init import init_app
from jira_cli.cli.commands.priority import priority_app
from jira_cli.cli.commands.project import project_app
from jira_cli.cli.commands.sprint import sprint_app
from jira_cli.cli.commands.user import user_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(issue_app, name="issue")
app.add_typer(issue_types_app, name="issue-types")
app.add_typer(project_app, name="project")
app.add_typer(board_app, name="board")
app.add_typer(sprint_app, name="sprint")
app.add_typer(priority_app, name="priority")
app.add_typer(user_app, name="user")
app.add_typer(config_app, name="config")
app.add_typer(init_app, name="init")


def raise_demo_validation(issue_key: str) -> None:
    return None


set_validation_hook(lambda issue_key: raise_demo_validation(issue_key))
