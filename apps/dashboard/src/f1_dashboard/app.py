import json
import os
from typing import MutableMapping

import requests
import streamlit as st

from streamlit import session_state as state


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

pipeline_status = state.get("pipeline_status")
pipeline_error = state.get("pipeline_error")
pipeline_result = state.get("pipeline_result")

if pipeline_status == "running":
    st.info("Pipeline run in progress…")
elif pipeline_error:
    st.error(pipeline_error)
elif pipeline_result:
    st.success("Pipeline completed")
    st.json(pipeline_result)
else:
    st.info("Run the pipeline above to populate artifacts and dashboards.")

if pipeline_result:
    query_params: MutableMapping[str, str | int] = {}
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
