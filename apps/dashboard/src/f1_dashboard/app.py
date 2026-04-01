import os
from datetime import datetime, timezone
from typing import MutableMapping

import requests
import streamlit as st
from streamlit import session_state as state
from streamlit_autorefresh import st_autorefresh


def _config_value(secret_key: str, env_var: str, default: str) -> str:
    try:
        from streamlit.errors import StreamlitSecretNotFoundError
    except ImportError:
        StreamlitSecretNotFoundError = OSError  # type: ignore[assignment]

    value: str | None = None
    try:
        value = st.secrets[secret_key]
    except (KeyError, StreamlitSecretNotFoundError, FileNotFoundError, OSError):
        value = None
    if value is None:
        value = os.getenv(env_var, default)
    return value.rstrip("/")


API_BASE_URL = _config_value("api_base_url", "F1_API_BASE_URL", "http://localhost:8000")
API_PREFIX = _config_value("api_prefix", "F1_API_PREFIX", "/api/v1")
PIPELINE_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/pipeline/run-session-baseline"
BASELINE_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/models/baseline-driver-scores"
INSIGHTS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/insights/top-drivers"
EXPLANATIONS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/explanations/session-top-drivers"
LATEST_RUN_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/meta/last-run"
AUTO_REFRESH_INTERVAL_SECONDS = 60


def _format_request_error(exc: requests.RequestException) -> str:
    response = getattr(exc, "response", None)
    if response is not None:
        code = response.status_code
        reason = response.reason or "Unknown"
        detail = response.text.strip() or "No body returned"
        return f"{code} {reason}: {detail}"
    return str(exc)


def _fetch_json(
    endpoint: str,
    params: MutableMapping[str, str | int],
    timeout: int = 10,
) -> tuple[list[dict[str, object]] | None, str | None]:
    try:
        response = requests.get(endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, _format_request_error(exc)


def _fetch_latest_run(timeout: int = 10) -> tuple[dict[str, object] | None, str | None]:
    try:
        response = requests.get(LATEST_RUN_ENDPOINT, timeout=timeout)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 404:
            return None, None
        return None, _format_request_error(exc)


def _render_table_section(
    container: st.delta_generator.DeltaGenerator,
    title: str,
    endpoint: str,
    params: MutableMapping[str, str | int],
    empty_message: str,
) -> None:
    with container:
        st.subheader(title)
        data, error = _fetch_json(endpoint, params)
        if error:
            st.error(f"{title} fetch failed: {error}")
            return
        if not data:
            st.info(empty_message)
            return
        st.table(data)


def _format_session_label(run: dict[str, object]) -> str:
    parts: list[str] = []
    round_value = run.get("round")
    if round_value:
        parts.append(f"Round {round_value}")
    session_value = run.get("session")
    if session_value:
        parts.append(str(session_value))
    if not parts:
        return "—"
    return " ".join(parts)


def _format_provenance_label(name: str | None, version: str | None) -> str:
    if not name:
        return "unknown"
    if version:
        return f"{name} · {version}"
    return name


def _build_operational_summary(run: dict[str, object]) -> tuple[str, str, str] | None:
    artifacts = run.get("artifact_availability") or []
    missing_artifacts = any(not entry.get("exists") for entry in artifacts)
    execution_status = run.get("execution_status")
    freshness = run.get("freshness", {})
    freshness_status = freshness.get("status")

    if missing_artifacts:
        return (
            "error",
            "Missing artifacts",
            "One or more artifacts were reported missing. Re-run the pipeline to regenerate them.",
        )

    if execution_status == "failed":
        return (
            "error",
            "Run failed",
            "The latest run did not complete successfully; check logs for details.",
        )

    if execution_status == "degraded":
        return (
            "warning",
            "Degraded run",
            "Explanation fallback was triggered; results may be partial.",
        )

    if freshness_status == "stale":
        return (
            "warning",
            "Stale metadata",
            "Latest run exceeds the freshness threshold; consider rerunning.",
        )

    return (
        "success",
        "Healthy run",
        "Artifacts, explainers, and freshness signals look good.",
    )


def _render_pipeline_completion_feedback(run: dict[str, object] | None) -> None:
    execution_status = run.get("execution_status") if run else None
    if execution_status == "failed":
        st.error("Pipeline completed but execution status is Failed; investigate the logs.")
    elif execution_status == "degraded":
        st.warning(
            "Pipeline completed with a degraded execution status; explanation fallback took over."
        )
    elif execution_status == "success":
        st.success("Pipeline completed successfully and latest metadata refreshed.")
    else:
        st.success("Pipeline completed; metadata refreshed after execution.")


def _render_operator_feedback(
    request_status: str | None,
    request_error: str | None,
    run: dict[str, object] | None,
) -> None:
    if request_status == "running":
        st.info("Pipeline run in progress…")
        return

    if request_error:
        if run:
            execution_status = run.get("execution_status", "unknown")
            st.error(
                "Pipeline request failed; latest run metadata refreshed "
                f"(latest execution: {str(execution_status).title()})."
            )
            st.caption(request_error)
        else:
            st.error(request_error)
        return

    if request_status == "success":
        _render_pipeline_completion_feedback(run)
        return

    st.info("Run the pipeline above to populate artifacts and dashboards.")


def _timestamp_label(ts: datetime | None) -> str:
    if ts is None:
        return "Never"
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _refresh_latest_run() -> None:
    data, error = _fetch_latest_run()
    state.latest_run_data = data
    state.latest_run_error = error
    state.latest_run_updated = datetime.now(timezone.utc)


st.set_page_config(page_title="F1 Race Intelligence", layout="wide")
st.title("F1 Race Intelligence Dashboard")

with st.sidebar.form(key="pipeline_form"):
    st.subheader("Run Session Baseline Pipeline")
    source = st.selectbox("Source", ["seed", "fastf1"], index=0)
    year = st.number_input("Year", min_value=1950, max_value=2026, value=2024)
    round_value = st.number_input("Round", min_value=1, value=1, step=1)
    session_code = st.selectbox("Session", ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"], index=6)
    run_button = st.form_submit_button("Run pipeline")

if run_button:
    state.pipeline_error = None
    state.pipeline_status = "running"
    if round_value <= 0:
        state.pipeline_error = "Round must be positive."
        state.pipeline_result = None
        state.pipeline_status = "error"
    else:
        payload = {
            "source": source,
            "year": year,
            "round": str(round_value),
            "session": session_code,
        }
        with st.spinner("Running pipeline baseline…"):
            try:
                response = requests.post(PIPELINE_ENDPOINT, json=payload, timeout=20)
                response.raise_for_status()
                state.pipeline_result = response.json()
                state.pipeline_status = "success"
            except requests.RequestException as exc:
                state.pipeline_error = f"Pipeline request failed: {_format_request_error(exc)}"
                state.pipeline_result = None
                state.pipeline_status = "error"
            finally:
                _refresh_latest_run()

pipeline_status = state.get("pipeline_status")
pipeline_error = state.get("pipeline_error")
pipeline_result = state.get("pipeline_result")
latest_run_data = state.get("latest_run_data")
latest_run_error = state.get("latest_run_error")

_render_operator_feedback(pipeline_status, pipeline_error, latest_run_data)
if pipeline_result:
    st.json(pipeline_result)


st.divider()
with st.container():
    st.subheader("Latest successful run")
    auto_refresh_default = state.get("latest_run_auto_refresh_enabled", False)
    auto_refresh = st.checkbox(
        f"Enable auto-refresh (every {AUTO_REFRESH_INTERVAL_SECONDS}s)",
        value=auto_refresh_default,
        key="latest_run_auto_refresh_enabled",
    )
    auto_refresh_caption = "Auto-refresh off"
    if auto_refresh:
        tick = st_autorefresh(
            interval=AUTO_REFRESH_INTERVAL_SECONDS * 1000,
            key="latest_run_auto_refresh_timer",
        )
        previous_tick = state.get("latest_run_auto_refresh_tick")
        if previous_tick != tick:
            state.latest_run_auto_refresh_tick = tick
            _refresh_latest_run()
            latest_run_data = state.get("latest_run_data")
            latest_run_error = state.get("latest_run_error")
        auto_refresh_caption = f"Auto-refresh on (every {AUTO_REFRESH_INTERVAL_SECONDS}s)"
    else:
        state.latest_run_auto_refresh_tick = None
    if latest_run_error:
        st.warning(f"Unable to fetch latest run: {latest_run_error}")
    elif not latest_run_data:
        st.info("No successful pipeline runs recorded yet.")
    else:
        refresh = st.button("Refresh latest run", key="refresh_latest_run")
        if refresh:
            _refresh_latest_run()
            latest_run_data = state.get("latest_run_data")
            latest_run_error = state.get("latest_run_error")

        st.caption(
            "Last refreshed: "
            f"{_timestamp_label(state.get('latest_run_updated'))} · {auto_refresh_caption}"
        )
        cols = st.columns(3)
        status_display = str(latest_run_data.get("status", "unknown")).title()
        cols[0].metric("Status", status_display)
        cols[1].metric("Session", _format_session_label(latest_run_data))
        cols[2].metric("Timestamp", str(latest_run_data.get("run_timestamp", "unknown")))
        st.caption(f"Source: {latest_run_data.get('source', 'unknown')}")
        summary = _build_operational_summary(latest_run_data)
        if summary:
            kind, title, detail = summary
            message = f"{title}: {detail}"
            if kind == "success":
                st.success(message)
            else:
                background = "#fff1f0" if kind == "error" else "#fffbe6"
                border = "#ffccc7" if kind == "error" else "#ffe58f"
                emoji = "🛑" if kind == "error" else "⚠️"
                html = (
                    f"<div style='border:1px solid {border}; "
                    f"background:{background}; padding:0.5rem; border-radius:6px;'>"
                    f"<strong>{emoji} {title}</strong><br>{detail}</div>"
                )
                st.markdown(html, unsafe_allow_html=True)
        provenance = latest_run_data.get("provenance")
        if provenance:
            model_label = _format_provenance_label(
                provenance.get("model_name"), provenance.get("model_version")
            )
            explainer_label = _format_provenance_label(
                provenance.get("explainer_name"), provenance.get("explainer_version")
            )
            prov_cols = st.columns(2)
            prov_cols[0].caption(f"Model: {model_label}")
            prov_cols[1].caption(f"Explainer: {explainer_label}")
        freshness = latest_run_data.get("freshness")
        if freshness:
            freshness_status = str(freshness.get("status", "unknown")).title()
            freshness_age = freshness.get("age_seconds")
            freshness_text = freshness_status
            if freshness_age is not None:
                freshness_text = f"{freshness_text} ({freshness_age}s)"
            st.caption(f"Freshness: {freshness_text}")
        execution_status = latest_run_data.get("execution_status")
        if execution_status:
            st.caption(f"Execution: {execution_status.title()}")
        artifact_availability = latest_run_data.get("artifact_availability")
        if artifact_availability:
            availability_rows = []
            for entry in artifact_availability:
                exists = entry.get("exists")
                availability_rows.append(
                    {
                        "Artifact": entry.get("artifact_name", "unknown"),
                        "Exists": "✅" if exists else "❌",
                        "Status": entry.get("status") or ("present" if exists else "missing"),
                    }
                )
            with st.expander("Artifact availability", expanded=False):
                st.table(availability_rows)

if pipeline_result:
    query_params = {}
    for key, value in (("season", year), ("round", round_value), ("session", session_code)):
        if value:
            query_params[key] = value

    st.divider()
    columns = st.columns(3)

    _render_table_section(
        columns[0],
        "Baseline scores",
        BASELINE_ENDPOINT,
        query_params,
        "No baseline scores available for the selected filters.",
    )
    _render_table_section(
        columns[1],
        "Top driver insights",
        INSIGHTS_ENDPOINT,
        query_params,
        "No insights are available for the chosen session yet.",
    )
    _render_table_section(
        columns[2],
        "Grounded explanations",
        EXPLANATIONS_ENDPOINT,
        query_params,
        "No explanations were generated for this session.",
    )
