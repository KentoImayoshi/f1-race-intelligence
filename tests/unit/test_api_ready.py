from pathlib import Path

import pytest

from fastapi import HTTPException

from f1_api.api.routes.health import ready
from f1_core import paths


def test_ready_returns_directory_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path)

    payload = ready()

    assert payload["status"] == "ready"
    directories = payload["directories"]
    assert directories["data_dir"] == str(tmp_path)
    for key in (
        "raw_dir",
        "processed_dir",
        "features_dir",
        "models_dir",
        "insights_dir",
        "llm_dir",
    ):
        assert key in directories


def test_ready_reports_problem_when_storage_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_os_error() -> Path:
        raise OSError("boom")

    monkeypatch.setattr(paths, "data_dir", raise_os_error)

    with pytest.raises(HTTPException) as excinfo:
        ready()

    assert excinfo.value.status_code == 503
