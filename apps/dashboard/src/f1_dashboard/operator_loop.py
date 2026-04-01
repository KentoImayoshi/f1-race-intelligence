from __future__ import annotations

from collections.abc import Callable

import requests

PipelineRunner = Callable[[dict[str, object]], dict[str, object]]
LatestRunRefresher = Callable[[], None]


def execute_pipeline_run(
    payload: dict[str, object],
    *,
    run_pipeline: PipelineRunner,
    refresh_latest_run: LatestRunRefresher,
) -> tuple[str, dict[str, object] | None, requests.RequestException | None]:
    try:
        result = run_pipeline(payload)
        return "success", result, None
    except requests.RequestException as exc:
        return "error", None, exc
    finally:
        refresh_latest_run()


def build_operator_feedback(
    request_status: str | None,
    request_error: str | None,
    run: dict[str, object] | None,
) -> tuple[str, str, str | None]:
    if request_status == "running":
        return "info", "Pipeline run in progress...", None

    if request_error:
        if run:
            execution_status = str(run.get("execution_status", "unknown")).title()
            return (
                "error",
                "Pipeline request failed; latest run metadata refreshed "
                f"(latest execution: {execution_status}).",
                request_error,
            )
        return "error", request_error, None

    if request_status == "success":
        execution_status = run.get("execution_status") if run else None
        if execution_status == "failed":
            return (
                "error",
                "Pipeline completed but execution status is Failed; investigate the logs.",
                None,
            )
        if execution_status == "degraded":
            return (
                "warning",
                "Pipeline completed with a degraded execution status; "
                "explanation fallback took over.",
                None,
            )
        if execution_status == "success":
            return "success", "Pipeline completed successfully and latest metadata refreshed.", None
        return "success", "Pipeline completed; metadata refreshed after execution.", None

    return "info", "Run the pipeline above to populate artifacts and dashboards.", None
