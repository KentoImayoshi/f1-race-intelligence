from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _project_dependencies(pyproject_path: Path) -> list[str]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    deps = project.get("dependencies", [])
    return list(deps)


@pytest.mark.unit
def test_ingestion_declares_fastf1_dependency() -> None:
    deps = _project_dependencies(ROOT / "packages" / "ingestion" / "pyproject.toml")
    assert any(dep.startswith("fastf1") for dep in deps)


@pytest.mark.unit
def test_api_declares_fastf1_runtime_dependency() -> None:
    deps = _project_dependencies(ROOT / "apps" / "api" / "pyproject.toml")
    assert any(dep.startswith("fastf1") for dep in deps)
