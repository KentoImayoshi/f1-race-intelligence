from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import requests

DASHBOARD_SRC = Path(__file__).resolve().parents[2] / "apps" / "dashboard" / "src"
if str(DASHBOARD_SRC) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_SRC))

operator_loop = importlib.import_module("f1_dashboard.operator_loop")
build_operator_feedback = operator_loop.build_operator_feedback
execute_pipeline_run = operator_loop.execute_pipeline_run


@pytest.mark.unit
def test_execute_pipeline_run_refreshes_latest_run_on_request_failure() -> None:
    refresh_calls: list[str] = []

    def _refresh_latest_run() -> None:
        refresh_calls.append("refreshed")

    def _run_pipeline(_: dict[str, object]) -> dict[str, object]:
        raise requests.HTTPError("500 Server Error")

    status, result, error = execute_pipeline_run(
        {"source": "seed", "year": 2024, "round": "1", "session": "R"},
        run_pipeline=_run_pipeline,
        refresh_latest_run=_refresh_latest_run,
    )

    assert status == "error"
    assert result is None
    assert isinstance(error, requests.HTTPError)
    assert refresh_calls == ["refreshed"]


@pytest.mark.unit
def test_build_operator_feedback_uses_latest_run_metadata_on_request_failure() -> None:
    level, message, detail = build_operator_feedback(
        "error",
        "Pipeline request failed: 500 Server Error",
        {"execution_status": "degraded"},
    )

    assert level == "error"
    assert "latest run metadata refreshed" in message
    assert "Degraded" in message
    assert detail == "Pipeline request failed: 500 Server Error"
