import json
from typing import MutableMapping
import streamlit as st
import requests

from streamlit import session_state as state

API_BASE_URL = st.secrets.get("api_base_url", "http://localhost:8000").rstrip("/")
API_PREFIX = st.secrets.get("api_prefix", "/api/v1").rstrip("/")
PIPELINE_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/pipeline/run-session-baseline"
BASELINE_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/models/baseline-driver-scores"
INSIGHTS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/insights/top-drivers"
EXPLANATIONS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/explanations/session-top-drivers"


st.set_page_config(page_title="F1 Race Intelligence", layout="wide")
st.title("F1 Race Intelligence Dashboard")

with st.sidebar.form(key="pipeline_form"):
    st.subheader("Run Session Baseline Pipeline")
    source = st.selectbox("Source", ["seed", "fastf1"], index=0)
    year = st.number_input("Year", min_value=2000, max_value=2100, value=2024)
    grand_prix = st.text_input("Grand Prix / Round", value="1")
    session_code = st.text_input("Session", value="R")
    run_button = st.form_submit_button("Run pipeline")

if run_button:
    payload = {
        "source": source,
        "year": year,
        "grand_prix": grand_prix,
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
    for key, value in (("season", year), ("round", grand_prix), ("session", session_code)):
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
