from dataclasses import dataclass, field


@dataclass
class CliError(Exception):
    code: str
    message: str
    details: dict = field(default_factory=dict)
    exit_code: int = 10
