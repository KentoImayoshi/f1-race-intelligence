import os
from datetime import datetime, timezone
from typing import MutableMapping

import pandas as pd
import requests
import streamlit as st
from streamlit import session_state as state
from streamlit_autorefresh import st_autorefresh

from f1_dashboard.operator_loop import build_operator_feedback, execute_pipeline_run


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
LAP_ANALYSIS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/analytics/session-lap-analysis"
LAP_COMPARISON_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/analytics/driver-lap-comparison"
TIRE_STINTS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/analytics/tire-stint-summaries"
PACE_EVOLUTION_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/analytics/pace-evolution"
CONSISTENCY_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/analytics/driver-consistency"
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


def _refresh_latest_run() -> None:
    data, error = _fetch_latest_run()
    state.latest_run_data = data
    state.latest_run_error = error
    state.latest_run_updated = datetime.now(timezone.utc)


def _timestamp_label(ts: datetime | None) -> str:
    if ts is None:
        return "Never"
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _build_params(
    season: int,
    round_value: int,
    session_code: str,
    driver_code: str | None = None,
    limit: int = 200,
) -> dict[str, str | int]:
    params: dict[str, str | int] = {
        "season": season,
        "round": round_value,
        "session": session_code,
        "limit": limit,
    }
    if driver_code:
        params["driver"] = driver_code
    return params


def _to_frame(rows: list[dict[str, object]] | None) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _ms_to_seconds(series: pd.Series) -> pd.Series:
    return (series.astype(float) / 1000.0).round(3)


def _render_operator_feedback(
    request_status: str | None,
    request_error: str | None,
    run: dict[str, object] | None,
) -> None:
    level, message, detail = build_operator_feedback(request_status, request_error, run)
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    elif level == "success":
        st.success(message)
    else:
        st.info(message)
    if detail:
        st.caption(detail)


def _render_latest_run_summary(
    latest_run_data: dict[str, object] | None, latest_run_error: str | None
) -> None:
    st.subheader("Session Status")
    if latest_run_error:
        st.warning(f"Unable to fetch latest run: {latest_run_error}")
        return
    if not latest_run_data:
        st.info("No successful pipeline runs recorded yet.")
        return

    cols = st.columns(4)
    cols[0].metric("Status", str(latest_run_data.get("status", "unknown")).title())
    cols[1].metric("Source", str(latest_run_data.get("source", "unknown")).upper())
    cols[2].metric("Session", str(latest_run_data.get("session", "—")))
    cols[3].metric("Run Timestamp", str(latest_run_data.get("run_timestamp", "unknown")))
    st.caption(f"Last refreshed: {_timestamp_label(state.get('latest_run_updated'))}")

    artifact_availability = latest_run_data.get("artifact_availability") or []
    if artifact_availability:
        artifact_df = pd.DataFrame(artifact_availability)[["artifact_name", "status", "exists"]]
        artifact_df.columns = ["Artifact", "Status", "Exists"]
        st.dataframe(artifact_df, use_container_width=True, hide_index=True)


def _render_pipeline_controls() -> tuple[int, int, str]:
    with st.sidebar.form(key="pipeline_form"):
        st.markdown("### Pipeline")
        source = st.selectbox("Source", ["seed", "fastf1", "openf1", "jolpica", "auto"], index=0)
        year = st.number_input("Year", min_value=1950, max_value=2026, value=2024)
        round_value = st.number_input("Round", min_value=1, value=1, step=1)
        session_code = st.selectbox("Session", ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"], index=6)
        run_button = st.form_submit_button("Run pipeline")

    if run_button:
        state.pipeline_error = None
        state.pipeline_status = "running"
        payload = {
            "source": source,
            "year": year,
            "round": str(round_value),
            "session": session_code,
        }
        with st.spinner("Running telemetry-aware pipeline..."):

            def _run_pipeline(run_payload: dict[str, object]) -> dict[str, object]:
                response = requests.post(PIPELINE_ENDPOINT, json=run_payload, timeout=45)
                response.raise_for_status()
                return response.json()

            pipeline_status, pipeline_result, pipeline_error = execute_pipeline_run(
                payload,
                run_pipeline=_run_pipeline,
                refresh_latest_run=_refresh_latest_run,
            )
            state.pipeline_result = pipeline_result
            state.pipeline_status = pipeline_status
            state.pipeline_error = (
                f"Pipeline request failed: {_format_request_error(pipeline_error)}"
                if pipeline_error
                else None
            )
    return year, round_value, session_code


def _render_hero() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(225, 52, 52, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(255, 182, 72, 0.22), transparent 22%),
                linear-gradient(180deg, #0b0d11 0%, #131720 55%, #171d27 100%);
            color: #f5f5f5;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .hero {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 1.4rem 1.5rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            backdrop-filter: blur(8px);
            margin-bottom: 1rem;
        }
        .hero h1 {
            font-size: 2.4rem;
            margin: 0 0 0.3rem 0;
            letter-spacing: 0.04em;
        }
        .hero p {
            margin: 0;
            color: #c9d2dc;
            font-size: 1rem;
        }
        </style>
        <div class="hero">
          <h1>F1 Telemetry Intelligence</h1>
          <p>
            Lap pace, sector execution, tire behavior, and race evolution from
            parquet-backed session analytics.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="F1 Telemetry Intelligence", layout="wide")
_render_hero()

if "latest_run_data" not in state:
    _refresh_latest_run()

year, round_value, session_code = _render_pipeline_controls()
pipeline_status = state.get("pipeline_status")
pipeline_error = state.get("pipeline_error")
pipeline_result = state.get("pipeline_result")
latest_run_data = state.get("latest_run_data")
latest_run_error = state.get("latest_run_error")

_render_operator_feedback(pipeline_status, pipeline_error, latest_run_data)

auto_refresh = st.sidebar.checkbox(
    f"Auto-refresh latest run ({AUTO_REFRESH_INTERVAL_SECONDS}s)",
    value=state.get("latest_run_auto_refresh_enabled", False),
    key="latest_run_auto_refresh_enabled",
)
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

with st.container():
    _render_latest_run_summary(latest_run_data, latest_run_error)

base_params = _build_params(
    year=year, round_value=round_value, session_code=session_code, limit=300
)
lap_rows, lap_error = _fetch_json(LAP_ANALYSIS_ENDPOINT, base_params)
pace_rows, pace_error = _fetch_json(PACE_EVOLUTION_ENDPOINT, base_params)
stint_rows, stint_error = _fetch_json(TIRE_STINTS_ENDPOINT, base_params)
consistency_rows, consistency_error = _fetch_json(CONSISTENCY_ENDPOINT, base_params)
baseline_rows, baseline_error = _fetch_json(BASELINE_ENDPOINT, base_params)
insight_rows, insight_error = _fetch_json(INSIGHTS_ENDPOINT, base_params)
explanation_rows, explanation_error = _fetch_json(EXPLANATIONS_ENDPOINT, base_params)

lap_df = _to_frame(lap_rows)
pace_df = _to_frame(pace_rows)
stint_df = _to_frame(stint_rows)
consistency_df = _to_frame(consistency_rows)
baseline_df = _to_frame(baseline_rows)
insight_df = _to_frame(insight_rows)
explanation_df = _to_frame(explanation_rows)

available_drivers = (
    sorted(lap_df["driver_code"].dropna().unique().tolist()) if not lap_df.empty else []
)
selected_driver = st.sidebar.selectbox("Primary driver", ["All"] + available_drivers, index=0)
comparison_candidates = [driver for driver in available_drivers if driver != selected_driver]
selected_compare_driver = st.sidebar.selectbox(
    "Comparison driver",
    ["None"] + comparison_candidates,
    index=0,
)

driver_filter = None if selected_driver == "All" else selected_driver
comparison_df = pd.DataFrame()
comparison_error = None
if driver_filter and selected_compare_driver != "None":
    comparison_rows, comparison_error = _fetch_json(
        LAP_COMPARISON_ENDPOINT,
        {
            "season": year,
            "round": round_value,
            "session": session_code,
            "driver": driver_filter,
            "compare_driver": selected_compare_driver,
            "limit": 300,
        },
    )
    comparison_df = _to_frame(comparison_rows)

if driver_filter:
    lap_df = lap_df[lap_df["driver_code"] == driver_filter]
    pace_df = pace_df[pace_df["driver_code"] == driver_filter]
    stint_df = stint_df[stint_df["driver_code"] == driver_filter]

summary_cols = st.columns(4)
if not lap_df.empty:
    summary_cols[0].metric("Valid laps", int(lap_df.shape[0]))
    summary_cols[1].metric("Fastest lap", f"{lap_df['lap_time_seconds'].min():.3f}s")
    summary_cols[2].metric(
        "Top speed",
        (
            f"{int(lap_df['top_speed_kph'].dropna().max())} kph"
            if lap_df["top_speed_kph"].notna().any()
            else "—"
        ),
    )
    summary_cols[3].metric("Primary focus", driver_filter or "Full session")
else:
    summary_cols[0].metric("Valid laps", 0)
    summary_cols[1].metric("Fastest lap", "—")
    summary_cols[2].metric("Top speed", "—")
    summary_cols[3].metric("Primary focus", driver_filter or "Full session")

tab_overview, tab_pace, tab_strategy, tab_context = st.tabs(
    ["Overview", "Pace Evolution", "Tire Strategy", "Context"]
)

with tab_overview:
    left, right = st.columns([1.3, 1.0])
    with left:
        st.subheader("Lap Analysis")
        if lap_error:
            st.error(f"Lap analysis unavailable: {lap_error}")
        elif lap_df.empty:
            st.info("Run the pipeline for this session to populate lap analysis.")
        else:
            display_df = lap_df[
                [
                    "driver_code",
                    "lap_number",
                    "compound",
                    "stint",
                    "lap_time_seconds",
                    "delta_to_fastest_ms",
                    "top_speed_kph",
                ]
            ].copy()
            display_df.columns = [
                "Driver",
                "Lap",
                "Compound",
                "Stint",
                "Lap Time (s)",
                "Delta (ms)",
                "Top Speed",
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Driver Consistency")
        if consistency_error:
            st.error(f"Consistency view unavailable: {consistency_error}")
        elif consistency_df.empty:
            st.info("No consistency summary available for this session.")
        else:
            display_df = consistency_df[
                [
                    "driver_code",
                    "lap_count",
                    "avg_lap_time_ms",
                    "lap_time_stddev_ms",
                    "consistency_index",
                ]
            ].copy()
            display_df["avg_lap_time_ms"] = _ms_to_seconds(display_df["avg_lap_time_ms"])
            display_df.columns = [
                "Driver",
                "Laps",
                "Avg Lap (s)",
                "Std Dev (ms)",
                "Consistency",
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab_pace:
    st.subheader("Pace Evolution")
    if pace_error:
        st.error(f"Pace evolution unavailable: {pace_error}")
    elif pace_df.empty:
        st.info("No pace evolution data available.")
    else:
        chart_df = pace_df.copy()
        chart_df["lap_time_seconds"] = _ms_to_seconds(chart_df["lap_time_ms"])
        chart_df["rolling_avg_seconds"] = _ms_to_seconds(chart_df["rolling_avg_lap_time_ms"])
        st.line_chart(
            chart_df,
            x="lap_number",
            y=["lap_time_seconds", "rolling_avg_seconds"],
            color="driver_code" if "driver_code" in chart_df.columns else None,
        )
        if comparison_error:
            st.warning(f"Comparison fetch failed: {comparison_error}")
        elif not comparison_df.empty:
            comparison_df = comparison_df.copy()
            comparison_df["lap_time_seconds"] = _ms_to_seconds(comparison_df["lap_time_ms"])
            st.caption(f"Comparison: {driver_filter} vs {selected_compare_driver}")
            st.line_chart(
                comparison_df,
                x="lap_number",
                y="lap_time_seconds",
                color="driver_code",
            )

with tab_strategy:
    st.subheader("Tire Stint Summaries")
    if stint_error:
        st.error(f"Tire strategy unavailable: {stint_error}")
    elif stint_df.empty:
        st.info("No tire stint data available.")
    else:
        strategy_df = stint_df.copy()
        strategy_df["avg_lap_time_s"] = _ms_to_seconds(strategy_df["avg_lap_time_ms"])
        strategy_df["best_lap_time_s"] = _ms_to_seconds(strategy_df["best_lap_time_ms"])
        st.bar_chart(strategy_df, x="compound", y="lap_count", color="driver_code")
        st.dataframe(
            strategy_df[
                [
                    "driver_code",
                    "stint",
                    "compound",
                    "start_lap",
                    "end_lap",
                    "lap_count",
                    "avg_lap_time_s",
                    "avg_top_speed_kph",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab_context:
    context_left, context_right = st.columns(2)
    with context_left:
        st.subheader("Baseline Ranking")
        if baseline_error:
            st.error(f"Baseline scores unavailable: {baseline_error}")
        elif baseline_df.empty:
            st.info("No baseline scores available.")
        else:
            st.dataframe(baseline_df, use_container_width=True, hide_index=True)
        st.subheader("Structured Insights")
        if insight_error:
            st.error(f"Insights unavailable: {insight_error}")
        elif insight_df.empty:
            st.info("No structured insights available.")
        else:
            st.dataframe(insight_df, use_container_width=True, hide_index=True)
    with context_right:
        st.subheader("Grounded Explanations")
        if explanation_error:
            st.error(f"Explanations unavailable: {explanation_error}")
        elif explanation_df.empty:
            st.info("No explanations available.")
        else:
            for row in explanation_df.to_dict("records"):
                explanation_type = row.get("explanation_type", "Explanation")
                explanation_text = row.get("explanation_text", "")
                st.markdown(f"**{explanation_type}**  \n{explanation_text}")

if pipeline_result:
    with st.expander("Pipeline artifact response", expanded=False):
        st.json(pipeline_result)
