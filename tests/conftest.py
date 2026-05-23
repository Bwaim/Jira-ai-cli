from pathlib import Path
import tomllib

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def pyproject_data(project_root: Path) -> dict:
    pyproject = project_root / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))
