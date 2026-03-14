import json
import os
from typing import MutableMapping
import streamlit as st
import requests

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
    if round_value <= 0:
        st.error("Round must be positive.")
        state.pipeline_result = None
    else:
        payload = {
            "source": source,
            "year": year,
            "round": str(round_value),
            "session": session_code,
        }
        try:
            response = requests.post(PIPELINE_ENDPOINT, json=payload, timeout=20)
            response.raise_for_status()
            state.pipeline_result = response.json()
        except requests.RequestException as exc:
            st.error(f"Pipeline request failed: {exc}")
            state.pipeline_result = None

pipeline_result = state.get("pipeline_result")

if pipeline_result:
    st.success("Pipeline completed")
    st.json(pipeline_result)

    query_params: MutableMapping[str, str | int] = {}
    for key, value in (("season", year), ("round", round_value), ("session", session_code)):
        if value:
            query_params[key] = value

    columns = st.columns(3)

    with columns[0]:
        st.subheader("Baseline scores")
        try:
            baseline = requests.get(BASELINE_ENDPOINT, params=query_params, timeout=10)
            baseline.raise_for_status()
            st.table(baseline.json())
        except requests.RequestException as exc:
            st.error(f"Baseline fetch failed: {exc}")

    with columns[1]:
        st.subheader("Top driver insights")
        try:
            insights = requests.get(INSIGHTS_ENDPOINT, params=query_params, timeout=10)
            insights.raise_for_status()
            st.table(insights.json())
        except requests.RequestException as exc:
            st.error(f"Insights fetch failed: {exc}")

    with columns[2]:
        st.subheader("Grounded explanations")
        try:
            explanations = requests.get(EXPLANATIONS_ENDPOINT, params=query_params, timeout=10)
            explanations.raise_for_status()
            st.table(explanations.json())
        except requests.RequestException as exc:
            st.error(f"Explanations fetch failed: {exc}")
else:
    st.info("Run the pipeline above to populate artifacts and dashboards.")
