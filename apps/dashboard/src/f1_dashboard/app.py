import os
from datetime import datetime, timezone
from typing import Any, MutableMapping

import altair as alt
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
SESSION_INTELLIGENCE_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/intelligence/session-summaries"
DRIVER_REPORTS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/intelligence/driver-reports"
STRATEGY_INSIGHTS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/intelligence/strategy-insights"
RACE_TRENDS_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/intelligence/race-trends"
LATEST_RUN_ENDPOINT = f"{API_BASE_URL}{API_PREFIX}/meta/last-run"
AUTO_REFRESH_INTERVAL_SECONDS = 60
ACCENT_COLORS = ["#ff6b57", "#ffb648", "#62d2a2", "#79b8ff", "#ffd166", "#d58cff"]
SOURCE_LABELS: dict[str, str] = {
    "seed": "Demo Dataset",
    "fastf1": "FastF1 Live Timing",
    "openf1": "OpenF1 Telemetry",
    "jolpica": "Jolpica Historical Data",
    "auto": "Auto Source Routing",
}
SESSION_LABELS: dict[str, str] = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "Q": "Qualifying",
    "SQ": "Sprint Qualifying",
    "S": "Sprint",
    "R": "Grand Prix Race",
}
GP_CIRCUIT_LABELS: dict[str, str] = {
    "Bahrain Grand Prix": "Bahrain International Circuit",
    "Saudi Arabian Grand Prix": "Jeddah Corniche Circuit",
    "Australian Grand Prix": "Albert Park Circuit",
    "Japanese Grand Prix": "Suzuka Circuit",
    "Chinese Grand Prix": "Shanghai International Circuit",
    "Miami Grand Prix": "Miami International Autodrome",
    "Emilia Romagna Grand Prix": "Imola Circuit",
    "Monaco Grand Prix": "Circuit de Monaco",
    "Canadian Grand Prix": "Circuit Gilles Villeneuve",
    "Spanish Grand Prix": "Circuit de Barcelona-Catalunya",
    "Austrian Grand Prix": "Red Bull Ring",
    "British Grand Prix": "Silverstone Circuit",
    "Hungarian Grand Prix": "Hungaroring",
    "Belgian Grand Prix": "Circuit de Spa-Francorchamps",
    "Dutch Grand Prix": "Circuit Zandvoort",
    "Italian Grand Prix": "Monza Circuit",
    "Azerbaijan Grand Prix": "Baku City Circuit",
    "Singapore Grand Prix": "Marina Bay Street Circuit",
    "United States Grand Prix": "Circuit of the Americas",
    "Mexico City Grand Prix": "Autodromo Hermanos Rodriguez",
    "Sao Paulo Grand Prix": "Interlagos Circuit",
    "Las Vegas Grand Prix": "Las Vegas Strip Circuit",
    "Qatar Grand Prix": "Lusail International Circuit",
    "Abu Dhabi Grand Prix": "Yas Marina Circuit",
}


def _format_request_error(exc: requests.RequestException) -> str:
    response = getattr(exc, "response", None)
    if response is not None:
        code = response.status_code
        reason = response.reason or "Unknown"
        detail = response.text.strip() or "No body returned"
        return f"{code} {reason}: {detail}"
    return str(exc)


def _render_html_block(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def _friendly_data_error(data_label: str, error: str | None) -> str | None:
    if not error:
        return None
    lower = error.lower()
    if "404" in error:
        return (
            f"{data_label} is not available yet for this session. "
            "Run the pipeline once to generate telemetry and intelligence artifacts."
        )
    if "500" in error:
        return (
            f"{data_label} is temporarily unavailable while race intelligence services "
            "are completing their current processing cycle."
        )
    connectivity_markers = [
        "connection refused",
        "failed to establish a new connection",
        "name or service not known",
        "max retries exceeded",
        "timed out",
    ]
    if any(marker in lower for marker in connectivity_markers):
        return (
            f"{data_label} is taking longer than expected. "
            "This can happen during first-load telemetry warmup."
        )
    return (
        f"{data_label} is currently delayed. "
        "Please refresh in a moment while session data finishes loading."
    )


def _source_label(source: str | None) -> str:
    if not source:
        return "Unknown Source"
    return SOURCE_LABELS.get(source, source.upper())


def _session_label(session_code: str | None) -> str:
    if not session_code:
        return "Unknown Session"
    return SESSION_LABELS.get(session_code, session_code)


def _circuit_label(grand_prix: str) -> str | None:
    return GP_CIRCUIT_LABELS.get(grand_prix)


def _render_data_error(data_label: str, error: str | None) -> bool:
    friendly = _friendly_data_error(data_label, error)
    if not friendly:
        return False
    st.warning(friendly)
    with st.expander(f"{data_label} technical detail", expanded=False):
        st.caption(error or "Unknown error")
    return True


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
    *,
    year: int | None = None,
    season: int | None = None,
    round_value: int,
    session_code: str,
    driver_code: str | None = None,
    limit: int = 200,
) -> dict[str, str | int]:
    if year is None and season is None:
        raise ValueError("Either 'year' or 'season' must be provided.")
    if year is not None and season is not None and year != season:
        raise ValueError("'year' and 'season' must match when both are provided.")

    resolved_season = season if season is not None else year
    params: dict[str, str | int] = {
        "season": resolved_season,
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
    return (pd.to_numeric(series, errors="coerce") / 1000.0).round(3)


def _format_ms_delta(value_ms: float | int | None) -> str:
    if value_ms is None or pd.isna(value_ms):
        return "—"
    seconds = float(value_ms) / 1000.0
    return f"{seconds:+.3f}s"


def _format_ms(value_ms: float | int | None) -> str:
    if value_ms is None or pd.isna(value_ms):
        return "—"
    return f"{float(value_ms):,.0f} ms"


def _format_seconds(value_s: float | int | None) -> str:
    if value_s is None or pd.isna(value_s):
        return "—"
    return f"{float(value_s):.3f}s"


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


def _render_shell() -> None:
    _render_html_block("""
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(214, 58, 43, 0.26), transparent 24%),
                radial-gradient(circle at top right, rgba(255, 183, 77, 0.18), transparent 18%),
                linear-gradient(180deg, #071018 0%, #0d1620 48%, #131c28 100%);
            color: #eff4fa;
        }
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2.4rem;
            max-width: 1460px;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 0;
        }
        .hero-shell {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 24px;
            padding: 1.65rem 1.65rem 1.3rem 1.65rem;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03)),
                linear-gradient(135deg, rgba(255,107,87,0.08), rgba(121,184,255,0.03));
            backdrop-filter: blur(12px);
            box-shadow: 0 24px 72px rgba(0, 0, 0, 0.28);
            margin-bottom: 1.1rem;
        }
        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -8% -38% auto;
            width: 320px;
            height: 320px;
            background: radial-gradient(circle, rgba(255,107,87,0.20), transparent 65%);
            pointer-events: none;
        }
        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.74rem;
            color: #8ca2b8;
            margin-bottom: 0.45rem;
        }
        .hero-title {
            font-size: 2.7rem;
            line-height: 1.02;
            font-weight: 700;
            margin: 0;
            color: #f4f8fb;
        }
        .hero-copy {
            margin-top: 0.7rem;
            max-width: 860px;
            color: #c7d3df;
            font-size: 1.02rem;
        }
        .hero-meta {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1.25rem;
        }
        .meta-pill {
            border-radius: 16px;
            padding: 0.85rem 1rem;
            background: rgba(8, 16, 26, 0.62);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .meta-label {
            font-size: 0.72rem;
            color: #8ca2b8;
            text-transform: uppercase;
            letter-spacing: 0.14em;
        }
        .meta-value {
            margin-top: 0.24rem;
            font-size: 1.02rem;
            color: #f3f7fb;
            font-weight: 600;
        }
        .section-header {
            margin: 1.05rem 0 0.35rem 0;
        }
        .section-title {
            margin: 0;
            font-size: 1.32rem;
            color: #f5f8fb;
        }
        .section-copy {
            color: #9eb0c1;
            margin-top: 0.28rem;
            font-size: 0.95rem;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 0.8rem;
            margin-bottom: 0.35rem;
        }
        .metric-card {
            border-radius: 20px;
            padding: 1.08rem 1.08rem 1rem 1.08rem;
            min-height: 168px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)),
                rgba(8, 15, 24, 0.78);
            border: 1px solid rgba(255, 255, 255, 0.07);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }
        .metric-kicker {
            font-size: 0.74rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #95a7b9;
            margin-bottom: 0.52rem;
        }
        .metric-value {
            font-size: 2rem;
            line-height: 1;
            font-weight: 700;
            color: #f8fbff;
        }
        .metric-detail {
            margin-top: 0.58rem;
            color: #d0dae4;
            font-size: 0.95rem;
        }
        .metric-context {
            margin-top: 0.48rem;
            color: #92a8bc;
            font-size: 0.82rem;
        }
        .story-card {
            border-radius: 20px;
            padding: 1rem 1.08rem;
            margin-bottom: 0.7rem;
            background: rgba(10, 17, 27, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.07);
        }
        .story-tag {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #87a1b9;
        }
        .story-headline {
            margin-top: 0.35rem;
            font-size: 1.04rem;
            font-weight: 600;
            color: #f3f7fb;
        }
        .story-detail {
            margin-top: 0.35rem;
            color: #c7d3df;
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .spotlight-card {
            border-radius: 24px;
            padding: 1.2rem 1.25rem;
            background:
                linear-gradient(135deg, rgba(255,107,87,0.16), rgba(121,184,255,0.08)),
                rgba(9, 18, 29, 0.78);
            border: 1px solid rgba(255, 255, 255, 0.09);
            min-height: 236px;
        }
        .spotlight-title {
            font-size: 1.28rem;
            font-weight: 650;
            color: #f6fbff;
            margin-top: 0.34rem;
        }
        .spotlight-detail {
            margin-top: 0.6rem;
            color: #d5e0ea;
            font-size: 0.97rem;
            line-height: 1.5;
        }
        .small-note {
            margin-top: 0.75rem;
            color: #a6b6c7;
            font-size: 0.82rem;
        }
        .empty-card {
            border-radius: 18px;
            padding: 1rem 1.1rem;
            background: rgba(7, 14, 23, 0.68);
            border: 1px dashed rgba(140, 162, 184, 0.35);
            color: #a8b9ca;
            margin-bottom: 0.85rem;
        }
        @media (max-width: 1100px) {
            .card-grid, .hero-meta {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 760px) {
            .hero-title {
                font-size: 2.05rem;
            }
            .card-grid, .hero-meta {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """)


def _render_section_header(title: str, copy: str) -> None:
    _render_html_block(f"""
        <div class="section-header">
          <div class="section-title">{title}</div>
          <div class="section-copy">{copy}</div>
        </div>
        """)


def _render_empty_state(title: str, detail: str) -> None:
    _render_html_block(f"""
        <div class="empty-card">
          <strong>{title}</strong><br/>
          {detail}
        </div>
        """)


def _render_story_card(title: str, detail: str, tag: str, accent: str) -> None:
    _render_html_block(f"""
        <div class="story-card" style="box-shadow: inset 4px 0 0 {accent};">
          <div class="story-tag">{tag}</div>
          <div class="story-headline">{title}</div>
          <div class="story-detail">{detail}</div>
        </div>
        """)


def _driver_color_scale(drivers: list[str]) -> alt.Scale:
    palette = [
        "#ff6b57",
        "#79b8ff",
        "#62d2a2",
        "#ffd166",
        "#d58cff",
        "#9fe870",
        "#ff8fab",
        "#90e0ef",
        "#f4a261",
        "#c0c7d1",
    ]
    return alt.Scale(domain=drivers, range=palette[: len(drivers)])


def _first_value(frame: pd.DataFrame, column: str, default: str = "—") -> str:
    if frame.empty or column not in frame.columns:
        return default
    value = frame[column].dropna()
    if value.empty:
        return default
    return str(value.iloc[0])


def _session_context(
    lap_df: pd.DataFrame,
    session_intelligence_df: pd.DataFrame,
    latest_run_data: dict[str, object] | None,
    year: int,
    round_value: int,
    session_code: str,
    driver_filter: str | None,
) -> dict[str, str]:
    context_source = lap_df if not lap_df.empty else session_intelligence_df
    grand_prix = _first_value(context_source, "grand_prix", "Race Weekend")
    circuit_name = _circuit_label(grand_prix)
    session_name = _session_label(session_code)
    run_timestamp = (
        str(latest_run_data.get("run_timestamp", "Unknown")) if latest_run_data else "Unknown"
    )
    return {
        "grand_prix": grand_prix,
        "title": f"{grand_prix} · {session_name}",
        "subtitle": (
            "Executive race briefing built from deterministic telemetry analytics, "
            "stint behavior, and grounded strategy intelligence."
        ),
        "season_round": f"{grand_prix} · {year} Championship",
        "session": session_name,
        "circuit": circuit_name or "Circuit context updates once telemetry metadata is available.",
        "focus": driver_filter or "Full-field briefing",
        "run_timestamp": run_timestamp,
    }


def _compute_sector_dominance(lap_df: pd.DataFrame) -> dict[str, str]:
    if lap_df.empty:
        return {
            "value": "—",
            "detail": "Sector performance data will appear after lap analysis loads.",
            "context": "No sector timing available",
        }

    sector_columns = [
        ("sector_1_ms", "S1"),
        ("sector_2_ms", "S2"),
        ("sector_3_ms", "S3"),
    ]
    sector_wins: dict[str, list[str]] = {}
    sector_total: dict[str, float] = {}
    for column, label in sector_columns:
        if column not in lap_df.columns:
            continue
        sector_avg = (
            lap_df.dropna(subset=[column])
            .groupby("driver_code", as_index=False)[column]
            .mean()
            .sort_values(column, ascending=True)
        )
        if sector_avg.empty:
            continue
        winner = str(sector_avg.iloc[0]["driver_code"])
        sector_wins.setdefault(winner, []).append(label)
        sector_total[winner] = sector_total.get(winner, 0.0) + float(sector_avg.iloc[0][column])

    if not sector_wins:
        return {
            "value": "—",
            "detail": "Sector timing is unavailable for the current selection.",
            "context": "No sector timing available",
        }

    winner = sorted(
        sector_wins.items(),
        key=lambda item: (-len(item[1]), sector_total.get(item[0], float("inf")), item[0]),
    )[0][0]
    won_sectors = sector_wins[winner]
    return {
        "value": winner,
        "detail": f"Controlled {', '.join(won_sectors)} on average sector pace.",
        "context": f"{len(won_sectors)} sector win(s) across the session",
    }


def _compute_pace_degradation(pace_df: pd.DataFrame) -> dict[str, str]:
    if pace_df.empty:
        return {
            "value": "—",
            "detail": "Pace drift will appear once rolling lap analysis is available.",
            "context": "No pace evolution available",
        }

    candidates: list[dict[str, Any]] = []
    for driver_code, group in pace_df.groupby("driver_code"):
        ordered = group.sort_values("lap_number")
        if ordered.empty:
            continue
        rolling = pd.to_numeric(ordered["rolling_avg_lap_time_ms"], errors="coerce").dropna()
        if rolling.shape[0] < 2:
            continue
        delta_ms = float(rolling.iloc[-1] - rolling.iloc[0])
        direction = "degradation" if delta_ms > 0 else "recovery"
        candidates.append(
            {
                "driver_code": str(driver_code),
                "delta_ms": delta_ms,
                "direction": direction,
                "start_ms": float(rolling.iloc[0]),
                "end_ms": float(rolling.iloc[-1]),
            }
        )

    if not candidates:
        return {
            "value": "—",
            "detail": "Pace drift requires multiple rolling windows per driver.",
            "context": "Not enough laps to evaluate",
        }

    top = sorted(candidates, key=lambda item: item["delta_ms"], reverse=True)[0]
    drift_label = "largest fade" if top["delta_ms"] > 0 else "strongest late-race recovery"
    return {
        "value": top["driver_code"],
        "detail": (
            f"{_format_ms_delta(top['delta_ms'])} rolling-pace shift from first to last window."
        ),
        "context": drift_label,
    }


def _build_executive_summary(
    lap_df: pd.DataFrame,
    consistency_df: pd.DataFrame,
    stint_df: pd.DataFrame,
    pace_df: pd.DataFrame,
    session_intelligence_df: pd.DataFrame,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    summary_cards: list[dict[str, str]] = []

    if not lap_df.empty:
        fastest_row = lap_df.sort_values("lap_time_seconds", ascending=True).iloc[0]
        summary_cards.append(
            {
                "title": "Fastest Driver",
                "value": str(fastest_row.get("driver_code", "—")),
                "detail": f"Best lap {_format_seconds(fastest_row.get('lap_time_seconds'))}",
                "context": f"Top speed {fastest_row.get('top_speed_kph', '—')} kph",
                "accent": ACCENT_COLORS[0],
            }
        )
    else:
        summary_cards.append(
            {
                "title": "Fastest Driver",
                "value": "—",
                "detail": "No lap analysis has been returned for this session.",
                "context": "Awaiting analytics artifact",
                "accent": ACCENT_COLORS[0],
            }
        )

    if not consistency_df.empty:
        top_consistency = consistency_df.sort_values("consistency_index", ascending=False).iloc[0]
        summary_cards.append(
            {
                "title": "Most Consistent",
                "value": str(top_consistency.get("driver_code", "—")),
                "detail": f"Consistency {float(top_consistency['consistency_index']):.3f}",
                "context": f"Std dev {_format_ms(top_consistency.get('lap_time_stddev_ms'))}",
                "accent": ACCENT_COLORS[1],
            }
        )
    else:
        summary_cards.append(
            {
                "title": "Most Consistent",
                "value": "—",
                "detail": "Consistency rankings are not available yet.",
                "context": "Awaiting consistency artifact",
                "accent": ACCENT_COLORS[1],
            }
        )

    if not stint_df.empty:
        strategy_rank = (
            stint_df.assign(
                weighted_delta=lambda frame: frame["avg_delta_to_fastest_ms"] * frame["lap_count"]
            )
            .groupby("driver_code", as_index=False)
            .agg(
                total_laps=("lap_count", "sum"),
                weighted_delta=("weighted_delta", "sum"),
                best_lap_ms=("best_lap_time_ms", "min"),
            )
        )
        strategy_rank["avg_delta_ms"] = (
            strategy_rank["weighted_delta"] / strategy_rank["total_laps"]
        ).round(1)
        winner = strategy_rank.sort_values("avg_delta_ms", ascending=True).iloc[0]
        best_stint = stint_df[stint_df["driver_code"] == winner["driver_code"]].sort_values(
            "avg_delta_to_fastest_ms", ascending=True
        )
        summary_cards.append(
            {
                "title": "Tire Strategy Winner",
                "value": str(winner.get("driver_code", "—")),
                "detail": f"Weighted stint delta {_format_ms_delta(winner['avg_delta_ms'])}",
                "context": (
                    f"Best stint {best_stint.iloc[0]['compound']} "
                    f"laps {best_stint.iloc[0]['start_lap']}-{best_stint.iloc[0]['end_lap']}"
                ),
                "accent": ACCENT_COLORS[2],
            }
        )
    else:
        summary_cards.append(
            {
                "title": "Tire Strategy Winner",
                "value": "—",
                "detail": "Stint intelligence is unavailable for this session.",
                "context": "Awaiting tire summary artifact",
                "accent": ACCENT_COLORS[2],
            }
        )

    degradation = _compute_pace_degradation(pace_df)
    summary_cards.append(
        {
            "title": "Biggest Pace Degradation",
            "value": degradation["value"],
            "detail": degradation["detail"],
            "context": degradation["context"],
            "accent": ACCENT_COLORS[3],
        }
    )

    sector_dominance = _compute_sector_dominance(lap_df)
    summary_cards.append(
        {
            "title": "Sector Dominance Leader",
            "value": sector_dominance["value"],
            "detail": sector_dominance["detail"],
            "context": sector_dominance["context"],
            "accent": ACCENT_COLORS[4],
        }
    )

    if not session_intelligence_df.empty:
        top_summary = session_intelligence_df.sort_values("importance_score", ascending=False).iloc[
            0
        ]
        spotlight = {
            "title": str(top_summary.get("headline", "Top race intelligence summary")),
            "detail": str(top_summary.get("detail", "")),
            "tag": str(top_summary.get("summary_type", "session intelligence")).replace("_", " "),
            "context": f"Importance score {float(top_summary.get('importance_score', 0.0)):.0f}",
            "accent": ACCENT_COLORS[5],
        }
    else:
        spotlight = {
            "title": "Top race intelligence summary pending",
            "detail": "Run the pipeline or load a completed session to surface the lead storyline.",
            "tag": "session intelligence",
            "context": "Awaiting session summary artifact",
            "accent": ACCENT_COLORS[5],
        }

    return summary_cards, spotlight


def _render_hero(context: dict[str, str]) -> None:
    _render_html_block(f"""
        <div class="hero-shell">
          <div class="eyebrow">Executive Race Intelligence</div>
          <h1 class="hero-title">{context['title']}</h1>
          <div class="hero-copy">{context['subtitle']}</div>
          <div class="hero-meta">
            <div class="meta-pill">
              <div class="meta-label">Weekend</div>
              <div class="meta-value">{context['season_round']}</div>
            </div>
            <div class="meta-pill">
              <div class="meta-label">Session</div>
              <div class="meta-value">{context['session']}</div>
            </div>
            <div class="meta-pill">
              <div class="meta-label">Circuit</div>
              <div class="meta-value">{context['circuit']}</div>
            </div>
            <div class="meta-pill">
              <div class="meta-label">Focus</div>
              <div class="meta-value">{context['focus']}</div>
            </div>
            <div class="meta-pill">
              <div class="meta-label">Latest pipeline run</div>
              <div class="meta-value">{context['run_timestamp']}</div>
            </div>
          </div>
        </div>
        """)


def _render_executive_overview(
    summary_cards: list[dict[str, str]],
    spotlight: dict[str, str],
    latest_run_error: str | None,
    is_pre_run: bool,
) -> None:
    _render_section_header(
        "Executive Overview",
        (
            "Immediate race winners, degradation signals, and sector control "
            "presented as a demo-first motorsport briefing."
        ),
    )

    card_cols = st.columns(3)
    for idx, card in enumerate(summary_cards):
        with card_cols[idx % 3]:
            _render_html_block(f"""
                <div class="metric-card" style="box-shadow: inset 4px 0 0 {card['accent']};">
                  <div class="metric-kicker">{card['title']}</div>
                  <div class="metric-value">{card['value']}</div>
                  <div class="metric-detail">{card['detail']}</div>
                  <div class="metric-context">{card['context']}</div>
                </div>
                """)

    spotlight_left, spotlight_right = st.columns([1.45, 1.0])
    with spotlight_left:
        _render_html_block(f"""
            <div class="spotlight-card">
              <div class="story-tag">{spotlight['tag']}</div>
              <div class="spotlight-title">{spotlight['title']}</div>
              <div class="spotlight-detail">{spotlight['detail']}</div>
              <div class="small-note">{spotlight['context']}</div>
            </div>
            """)
    with spotlight_right:
        if latest_run_error:
            _render_empty_state("Run metadata unavailable", latest_run_error)
        elif is_pre_run:
            _render_empty_state(
                "No completed run yet",
                (
                    "Use the pipeline form in the sidebar to run a session. "
                    "The executive cards and intelligence stories will populate automatically."
                ),
            )
        else:
            _render_story_card(
                "Briefing design",
                (
                    "The dashboard now prioritizes conclusions first: executive calls, "
                    "strategic posture, trend narratives, then supporting evidence."
                ),
                "demo priority",
                "#79b8ff",
            )
            _render_story_card(
                "Storytelling flow",
                (
                    "Top-level cards summarize who owned pace, consistency, sectors, "
                    "and tire execution before the lower-level telemetry views appear."
                ),
                "ux rationale",
                "#ffd166",
            )


def _render_story_column(
    title: str,
    caption: str,
    rows: list[dict[str, object]],
    headline_key: str,
    detail_key: str,
    tag_key: str,
    accent: str,
    empty_message: str,
) -> None:
    st.subheader(title)
    st.caption(caption)
    if not rows:
        _render_empty_state(title, empty_message)
        return

    for row in rows:
        _render_story_card(
            str(row.get(headline_key, title)),
            str(row.get(detail_key, "")),
            str(row.get(tag_key, "")).replace("_", " "),
            accent,
        )


def _render_driver_reports(driver_report_df: pd.DataFrame, driver_report_error: str | None) -> None:
    st.subheader("Driver Intelligence Summaries")
    st.caption("Performance, strategy, tyre behavior, and trend cues for the current focus set.")
    if _render_data_error("Driver intelligence reports", driver_report_error):
        return
    if driver_report_df.empty:
        _render_empty_state(
            "Driver intelligence pending",
            "Select a driver or load a completed session to populate executive driver reports.",
        )
        return

    for row in driver_report_df.to_dict("records")[:3]:
        _render_html_block(f"""
            <div class="story-card" style="box-shadow: inset 4px 0 0 #62d2a2;">
              <div class="story-tag">{row.get('driver_code', 'driver')}</div>
              <div class="story-headline">{row.get('report_title', 'Driver report')}</div>
              <div class="story-detail">
                <strong>Performance:</strong> {row.get('performance_summary', '')}<br/><br/>
                <strong>Strategy:</strong> {row.get('strategy_summary', '')}<br/><br/>
                <strong>Tyres:</strong> {row.get('tire_summary', '')}<br/><br/>
                <strong>Trend:</strong> {row.get('trend_summary', '')}
              </div>
            </div>
            """)


def _render_latest_run_summary(
    latest_run_data: dict[str, object] | None, latest_run_error: str | None
) -> None:
    st.subheader("Pipeline Status")
    if _render_data_error("Latest run metadata", latest_run_error):
        return
    if not latest_run_data:
        st.info("No successful pipeline runs recorded yet.")
        return

    cols = st.columns(4)
    cols[0].metric("Status", str(latest_run_data.get("status", "unknown")).title())
    cols[1].metric("Source", _source_label(str(latest_run_data.get("source", "unknown"))))
    cols[2].metric("Session", _session_label(str(latest_run_data.get("session", "—"))))
    cols[3].metric("Run Timestamp", str(latest_run_data.get("run_timestamp", "unknown")))
    st.caption(f"Last refreshed: {_timestamp_label(state.get('latest_run_updated'))}")

    artifact_availability = latest_run_data.get("artifact_availability") or []
    if artifact_availability:
        artifact_df = pd.DataFrame(artifact_availability)[["artifact_name", "status", "exists"]]
        artifact_df.columns = ["Artifact", "Status", "Exists"]
        st.dataframe(artifact_df, use_container_width=True, hide_index=True)


def _render_pipeline_controls() -> tuple[int, int, str]:
    source_options = list(SOURCE_LABELS.keys())
    source_labels = [SOURCE_LABELS[item] for item in source_options]
    with st.sidebar.form(key="pipeline_form"):
        st.markdown("### Pipeline")
        selected_source_label = st.selectbox("Data Source", source_labels, index=0)
        year = st.number_input("Year", min_value=1950, max_value=2026, value=2024)
        round_value = st.number_input("Championship Round", min_value=1, value=1, step=1)
        session_code = st.selectbox(
            "Session Type",
            list(SESSION_LABELS.keys()),
            index=6,
            format_func=_session_label,
        )
        run_button = st.form_submit_button("Build Session Intelligence")

    source = source_options[source_labels.index(selected_source_label)]

    if run_button:
        state.pipeline_error = None
        state.pipeline_status = "running"
        payload = {
            "source": source,
            "year": year,
            "round": str(round_value),
            "session": session_code,
        }
        with st.spinner(
            "Ingesting telemetry and building race intelligence. "
            "First-load sessions may take a little longer while provider caches warm up..."
        ):

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


def _build_pace_chart(pace_df: pd.DataFrame) -> alt.Chart:
    chart_df = pace_df.copy()
    chart_df["lap_time_seconds"] = _ms_to_seconds(chart_df["lap_time_ms"])
    chart_df["rolling_avg_seconds"] = _ms_to_seconds(chart_df["rolling_avg_lap_time_ms"])
    drivers = sorted(chart_df["driver_code"].dropna().astype(str).unique().tolist())
    scale = _driver_color_scale(drivers)

    base = alt.Chart(chart_df).encode(
        x=alt.X("lap_number:Q", title="Lap"),
        color=alt.Color("driver_code:N", title="Driver", scale=scale),
        tooltip=[
            alt.Tooltip("driver_code:N", title="Driver"),
            alt.Tooltip("lap_number:Q", title="Lap"),
            alt.Tooltip("lap_time_seconds:Q", title="Lap", format=".3f"),
            alt.Tooltip("rolling_avg_seconds:Q", title="Rolling Avg", format=".3f"),
            alt.Tooltip("pace_trend:N", title="Trend"),
        ],
    )
    rolling = base.mark_line(strokeWidth=3).encode(
        y=alt.Y("rolling_avg_seconds:Q", title="Lap Time (s)")
    )
    lap_points = base.mark_circle(size=52, opacity=0.45).encode(y="lap_time_seconds:Q")
    return (
        alt.layer(rolling, lap_points)
        .properties(height=340)
        .configure_axis(labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443")
        .configure_view(strokeOpacity=0)
        .configure_legend(
            labelColor="#e8eef4",
            titleColor="#ffffff",
            fillColor="#0f1823",
            strokeColor="#223040",
            cornerRadius=10,
            padding=12,
        )
    )


def _build_performance_scatter(lap_df: pd.DataFrame) -> alt.Chart:
    scatter_df = lap_df.dropna(subset=["top_speed_kph"]).copy()
    scatter_df["tyre_life_laps"] = pd.to_numeric(
        scatter_df.get("tyre_life_laps", pd.Series([1] * len(scatter_df))), errors="coerce"
    ).fillna(1)
    drivers = sorted(scatter_df["driver_code"].dropna().astype(str).unique().tolist())
    scale = _driver_color_scale(drivers)
    return (
        alt.Chart(scatter_df)
        .mark_circle(opacity=0.72, stroke="#0c1117", strokeWidth=1.2)
        .encode(
            x=alt.X("lap_time_seconds:Q", title="Lap Time (s)"),
            y=alt.Y("top_speed_kph:Q", title="Top Speed (kph)"),
            color=alt.Color("driver_code:N", scale=scale, title="Driver"),
            size=alt.Size("tyre_life_laps:Q", title="Tyre Life"),
            tooltip=[
                alt.Tooltip("driver_code:N", title="Driver"),
                alt.Tooltip("lap_number:Q", title="Lap"),
                alt.Tooltip("lap_time_seconds:Q", title="Lap Time", format=".3f"),
                alt.Tooltip("top_speed_kph:Q", title="Top Speed"),
                alt.Tooltip("compound:N", title="Compound"),
            ],
        )
        .properties(height=320)
        .configure_axis(labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443")
        .configure_view(strokeOpacity=0)
    )


def _build_sector_chart(lap_df: pd.DataFrame) -> alt.Chart:
    sector_df = (
        lap_df.groupby("driver_code", as_index=False)[["sector_1_ms", "sector_2_ms", "sector_3_ms"]]
        .mean(numeric_only=True)
        .sort_values(["sector_1_ms", "sector_2_ms", "sector_3_ms"], ascending=True)
        .head(8)
        .melt(id_vars="driver_code", var_name="sector", value_name="sector_ms")
    )
    sector_df["sector"] = sector_df["sector"].map(
        {"sector_1_ms": "Sector 1", "sector_2_ms": "Sector 2", "sector_3_ms": "Sector 3"}
    )
    return (
        alt.Chart(sector_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("driver_code:N", title="Driver", sort=None),
            y=alt.Y("sector_ms:Q", title="Average Sector Time (ms)"),
            color=alt.Color(
                "sector:N",
                scale=alt.Scale(
                    domain=["Sector 1", "Sector 2", "Sector 3"],
                    range=["#ff6b57", "#ffd166", "#79b8ff"],
                ),
                title="Sector",
            ),
            xOffset="sector:N",
            tooltip=[
                alt.Tooltip("driver_code:N", title="Driver"),
                alt.Tooltip("sector:N", title="Sector"),
                alt.Tooltip("sector_ms:Q", title="Avg Time", format=".0f"),
            ],
        )
        .properties(height=320)
        .configure_axis(labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443")
        .configure_view(strokeOpacity=0)
    )


def _build_consistency_chart(consistency_df: pd.DataFrame) -> alt.Chart:
    chart_df = consistency_df.copy().sort_values("consistency_index", ascending=False).head(8)
    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#62d2a2")
        .encode(
            x=alt.X("driver_code:N", title="Driver"),
            y=alt.Y("consistency_index:Q", title="Consistency Index"),
            tooltip=[
                alt.Tooltip("driver_code:N", title="Driver"),
                alt.Tooltip("consistency_index:Q", title="Consistency", format=".3f"),
                alt.Tooltip("lap_time_stddev_ms:Q", title="Std Dev (ms)"),
            ],
        )
        .properties(height=300)
        .configure_axis(labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443")
        .configure_view(strokeOpacity=0)
    )


def _build_tire_timeline_chart(stint_df: pd.DataFrame) -> alt.Chart:
    chart_df = stint_df.copy()
    chart_df["lap_window"] = (
        chart_df["start_lap"].astype(str) + "-" + chart_df["end_lap"].astype(str)
    )
    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadius=8, size=16)
        .encode(
            x=alt.X("start_lap:Q", title="Lap Window"),
            x2="end_lap:Q",
            y=alt.Y("driver_code:N", title="Driver", sort="-x"),
            color=alt.Color(
                "compound:N",
                title="Compound",
                scale=alt.Scale(
                    domain=["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"],
                    range=["#ff6b57", "#ffd166", "#f1f1f1", "#62d2a2", "#79b8ff"],
                ),
            ),
            tooltip=[
                alt.Tooltip("driver_code:N", title="Driver"),
                alt.Tooltip("compound:N", title="Compound"),
                alt.Tooltip("lap_window:N", title="Laps"),
                alt.Tooltip("avg_lap_time_ms:Q", title="Avg Lap (ms)"),
            ],
        )
        .properties(height=320)
        .configure_axis(labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443")
        .configure_view(strokeOpacity=0)
    )


def _build_strategy_strength_chart(stint_df: pd.DataFrame) -> alt.Chart:
    chart_df = stint_df.copy()
    chart_df["avg_lap_time_s"] = _ms_to_seconds(chart_df["avg_lap_time_ms"])
    chart_df["label"] = chart_df["driver_code"] + " · " + chart_df["compound"].fillna("UNKNOWN")
    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("label:N", title="Driver / Compound", sort=None),
            y=alt.Y("avg_lap_time_s:Q", title="Average Lap Time (s)"),
            color=alt.Color("compound:N", title="Compound"),
            tooltip=[
                alt.Tooltip("driver_code:N", title="Driver"),
                alt.Tooltip("compound:N", title="Compound"),
                alt.Tooltip("lap_count:Q", title="Laps"),
                alt.Tooltip("avg_lap_time_s:Q", title="Avg Lap", format=".3f"),
                alt.Tooltip("avg_delta_to_fastest_ms:Q", title="Avg Delta (ms)"),
            ],
        )
        .properties(height=320)
        .configure_axis(labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443")
        .configure_view(strokeOpacity=0)
    )


st.set_page_config(page_title="F1 Telemetry Intelligence", layout="wide")
_render_shell()

if "latest_run_data" not in state:
    _refresh_latest_run()

year, round_value, session_code = _render_pipeline_controls()
pipeline_status = state.get("pipeline_status")
pipeline_error = state.get("pipeline_error")
pipeline_result = state.get("pipeline_result")
latest_run_data = state.get("latest_run_data")
latest_run_error = state.get("latest_run_error")

base_params = _build_params(
    year=year,
    round_value=round_value,
    session_code=session_code,
    limit=300,
)
with st.spinner("Building executive race briefing..."):
    lap_rows, lap_error = _fetch_json(LAP_ANALYSIS_ENDPOINT, base_params)
    pace_rows, pace_error = _fetch_json(PACE_EVOLUTION_ENDPOINT, base_params)
    stint_rows, stint_error = _fetch_json(TIRE_STINTS_ENDPOINT, base_params)
    consistency_rows, consistency_error = _fetch_json(CONSISTENCY_ENDPOINT, base_params)
    baseline_rows, baseline_error = _fetch_json(BASELINE_ENDPOINT, base_params)
    insight_rows, insight_error = _fetch_json(INSIGHTS_ENDPOINT, base_params)
    explanation_rows, explanation_error = _fetch_json(EXPLANATIONS_ENDPOINT, base_params)
    session_intelligence_rows, session_intelligence_error = _fetch_json(
        SESSION_INTELLIGENCE_ENDPOINT,
        {**base_params, "limit": 12},
    )
    driver_report_rows, driver_report_error = _fetch_json(
        DRIVER_REPORTS_ENDPOINT,
        {**base_params, "limit": 20},
    )
    strategy_insight_rows, strategy_insight_error = _fetch_json(
        STRATEGY_INSIGHTS_ENDPOINT,
        {**base_params, "limit": 20},
    )
    race_trend_rows, race_trend_error = _fetch_json(
        RACE_TRENDS_ENDPOINT,
        {**base_params, "limit": 30},
    )

full_lap_df = _to_frame(lap_rows)
full_pace_df = _to_frame(pace_rows)
full_stint_df = _to_frame(stint_rows)
full_consistency_df = _to_frame(consistency_rows)
baseline_df = _to_frame(baseline_rows)
insight_df = _to_frame(insight_rows)
explanation_df = _to_frame(explanation_rows)
session_intelligence_df = _to_frame(session_intelligence_rows)
full_driver_report_df = _to_frame(driver_report_rows)
full_strategy_insight_df = _to_frame(strategy_insight_rows)
full_race_trend_df = _to_frame(race_trend_rows)

available_drivers = (
    sorted(full_lap_df["driver_code"].dropna().astype(str).unique().tolist())
    if not full_lap_df.empty and "driver_code" in full_lap_df.columns
    else []
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
            **_build_params(
                year=year,
                round_value=round_value,
                session_code=session_code,
                driver_code=driver_filter,
                limit=300,
            ),
            "compare_driver": selected_compare_driver,
        },
    )
    comparison_df = _to_frame(comparison_rows)

lap_df = full_lap_df.copy()
pace_df = full_pace_df.copy()
stint_df = full_stint_df.copy()
driver_report_df = full_driver_report_df.copy()
strategy_insight_df = full_strategy_insight_df.copy()
race_trend_df = full_race_trend_df.copy()
if driver_filter:
    lap_df = lap_df[lap_df["driver_code"] == driver_filter]
    pace_df = pace_df[pace_df["driver_code"] == driver_filter]
    stint_df = stint_df[stint_df["driver_code"] == driver_filter]
    if not driver_report_df.empty and "driver_code" in driver_report_df.columns:
        driver_report_df = driver_report_df[driver_report_df["driver_code"] == driver_filter]
    if not strategy_insight_df.empty and "driver_code" in strategy_insight_df.columns:
        strategy_insight_df = strategy_insight_df[
            strategy_insight_df["driver_code"] == driver_filter
        ]
    if not race_trend_df.empty and "driver_code" in race_trend_df.columns:
        race_trend_df = race_trend_df[race_trend_df["driver_code"] == driver_filter]

summary_cards, spotlight = _build_executive_summary(
    full_lap_df,
    full_consistency_df,
    full_stint_df,
    full_pace_df,
    session_intelligence_df,
)
context = _session_context(
    full_lap_df,
    session_intelligence_df,
    latest_run_data,
    year,
    round_value,
    session_code,
    driver_filter,
)
is_pre_run = latest_run_data is None and all(
    frame.empty
    for frame in [
        full_lap_df,
        full_pace_df,
        full_stint_df,
        full_consistency_df,
        session_intelligence_df,
        full_driver_report_df,
        full_strategy_insight_df,
        full_race_trend_df,
    ]
)

_render_hero(context)
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

_render_executive_overview(summary_cards, spotlight, latest_run_error, is_pre_run)

summary_cols = st.columns(4)
summary_cols[0].metric("Valid laps", int(full_lap_df.shape[0]) if not full_lap_df.empty else 0)
summary_cols[1].metric(
    "Fastest lap",
    _format_seconds(full_lap_df["lap_time_seconds"].min()) if not full_lap_df.empty else "—",
)
summary_cols[2].metric(
    "Top speed",
    (
        f"{int(full_lap_df['top_speed_kph'].dropna().max())} kph"
        if not full_lap_df.empty
        and "top_speed_kph" in full_lap_df.columns
        and full_lap_df["top_speed_kph"].notna().any()
        else "—"
    ),
)
summary_cols[3].metric("Current focus", driver_filter or "Full field")

tab_brief, tab_performance, tab_strategy, tab_artifacts = st.tabs(
    ["Executive Brief", "Performance Lab", "Strategy Room", "Artifact Room"]
)

with tab_brief:
    brief_left, brief_right = st.columns([1.2, 1.0])
    with brief_left:
        if _render_data_error("Session intelligence summaries", session_intelligence_error):
            pass
        else:
            _render_story_column(
                "Key Race Insights",
                (
                    "Top deterministic session summaries ordered by importance "
                    "for immediate briefings."
                ),
                (
                    session_intelligence_df.sort_values(
                        "importance_score", ascending=False
                    ).to_dict("records")[:5]
                    if not session_intelligence_df.empty
                    else []
                ),
                "headline",
                "detail",
                "summary_type",
                "#ff6b57",
                "No intelligence summary available for this session.",
            )
        if _render_data_error("Strategy insights", strategy_insight_error):
            pass
        else:
            _render_story_column(
                "Strategy Summaries",
                "Pit-window and tyre leverage opportunities elevated ahead of raw stint tables.",
                strategy_insight_df.to_dict("records")[:4] if not strategy_insight_df.empty else [],
                "strategy_headline",
                "strategy_detail",
                "opportunity_label",
                "#ffd166",
                "No strategy summary is available for the current selection.",
            )
    with brief_right:
        if _render_data_error("Race trend analysis", race_trend_error):
            pass
        else:
            _render_story_column(
                "Trend Highlights",
                (
                    "Driver-level pace trajectory and ranking narratives surfaced "
                    "for demo storytelling."
                ),
                race_trend_df.to_dict("records")[:4] if not race_trend_df.empty else [],
                "trend_headline",
                "trend_detail",
                "trend_category",
                "#79b8ff",
                "No trend highlights are available for the current selection.",
            )
        _render_driver_reports(driver_report_df, driver_report_error)

with tab_performance:
    _render_section_header(
        "Performance Lab",
        (
            "High-readability visual diagnostics for pace, sector execution, "
            "consistency, and driver comparison."
        ),
    )
    perf_top_left, perf_top_right = st.columns([1.35, 1.0])
    with perf_top_left:
        st.subheader("Pace Evolution")
        st.caption("Rolling pace curves emphasize fade, recovery, and race management shape.")
        if _render_data_error("Pace evolution", pace_error):
            pass
        elif pace_df.empty:
            _render_empty_state("Pace evolution unavailable", "No pace evolution data available.")
        else:
            st.altair_chart(_build_pace_chart(pace_df), use_container_width=True)
            if comparison_error:
                _render_data_error("Driver comparison", comparison_error)
            elif not comparison_df.empty:
                comparison_chart_df = comparison_df.copy()
                comparison_chart_df["lap_time_seconds"] = _ms_to_seconds(
                    comparison_chart_df["lap_time_ms"]
                )
                drivers = sorted(
                    comparison_chart_df["driver_code"].dropna().astype(str).unique().tolist()
                )
                st.caption(f"Direct comparison: {driver_filter} vs {selected_compare_driver}")
                st.altair_chart(
                    (
                        alt.Chart(comparison_chart_df)
                        .mark_line(point=True, strokeWidth=3)
                        .encode(
                            x=alt.X("lap_number:Q", title="Lap"),
                            y=alt.Y("lap_time_seconds:Q", title="Lap Time (s)"),
                            color=alt.Color(
                                "driver_code:N",
                                title="Driver",
                                scale=_driver_color_scale(drivers),
                            ),
                            tooltip=[
                                alt.Tooltip("driver_code:N", title="Driver"),
                                alt.Tooltip("lap_number:Q", title="Lap"),
                                alt.Tooltip("lap_time_seconds:Q", title="Lap Time", format=".3f"),
                            ],
                        )
                        .properties(height=250)
                        .configure_axis(
                            labelColor="#d8e1ea", titleColor="#eff4fa", gridColor="#263443"
                        )
                        .configure_view(strokeOpacity=0)
                    ),
                    use_container_width=True,
                )
    with perf_top_right:
        st.subheader("Sector Dominance")
        st.caption("Average sector bars make control areas obvious in one glance.")
        if _render_data_error("Sector comparison", lap_error):
            pass
        elif lap_df.empty:
            _render_empty_state("Sector comparison unavailable", "No lap data is available.")
        else:
            st.altair_chart(_build_sector_chart(lap_df), use_container_width=True)

    perf_bottom_left, perf_bottom_right = st.columns([1.0, 1.0])
    with perf_bottom_left:
        st.subheader("Performance Envelope")
        st.caption("Lap time versus top speed reveals efficiency and tyre-life trade-offs.")
        if _render_data_error("Performance envelope", lap_error):
            pass
        elif lap_df.empty or "top_speed_kph" not in lap_df.columns:
            _render_empty_state(
                "Performance envelope unavailable",
                "Top speed data is required for the speed-versus-lap-time view.",
            )
        else:
            st.altair_chart(_build_performance_scatter(lap_df), use_container_width=True)
    with perf_bottom_right:
        st.subheader("Consistency Benchmark")
        st.caption("A clean repeatability ranking to support race-engineering conversations.")
        if _render_data_error("Consistency benchmark", consistency_error):
            pass
        elif full_consistency_df.empty:
            _render_empty_state(
                "Consistency benchmark unavailable",
                "No consistency summary is available for this session.",
            )
        else:
            st.altair_chart(_build_consistency_chart(full_consistency_df), use_container_width=True)

with tab_strategy:
    _render_section_header(
        "Strategy Room",
        (
            "Tyre usage, stint windows, and strategic strength views that foreground "
            "race-call quality."
        ),
    )
    strategy_left, strategy_right = st.columns([1.2, 1.0])
    with strategy_left:
        st.subheader("Tire Stint Timeline")
        st.caption("Horizontal stint windows read like a strategy wall rather than a raw table.")
        if _render_data_error("Tire stint timeline", stint_error):
            pass
        elif stint_df.empty:
            _render_empty_state("Tire stint timeline unavailable", "No tire stint data available.")
        else:
            st.altair_chart(_build_tire_timeline_chart(stint_df), use_container_width=True)
    with strategy_right:
        st.subheader("Stint Strength")
        st.caption("Average compound pace by stint to highlight strategic winners and weak phases.")
        if _render_data_error("Stint strength", stint_error):
            pass
        elif stint_df.empty:
            _render_empty_state("Stint strength unavailable", "No tire stint data available.")
        else:
            st.altair_chart(_build_strategy_strength_chart(stint_df), use_container_width=True)

    if not stint_df.empty:
        strategy_table = stint_df.copy()
        strategy_table["avg_lap_time_s"] = _ms_to_seconds(strategy_table["avg_lap_time_ms"])
        strategy_table["best_lap_time_s"] = _ms_to_seconds(strategy_table["best_lap_time_ms"])
        st.subheader("Strategy Support Table")
        st.caption("Compact validation table retained for engineering sanity checks.")
        st.dataframe(
            strategy_table[
                [
                    "driver_code",
                    "stint",
                    "compound",
                    "start_lap",
                    "end_lap",
                    "lap_count",
                    "avg_lap_time_s",
                    "best_lap_time_s",
                    "avg_top_speed_kph",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab_artifacts:
    _render_section_header(
        "Artifact Room",
        (
            "Secondary context, compatibility artifacts, and pipeline observability "
            "retained without competing with the executive narrative."
        ),
    )
    artifact_left, artifact_right = st.columns([1.05, 1.0])
    with artifact_left:
        with st.expander("Baseline ranking and original insight artifacts", expanded=True):
            st.subheader("Baseline Ranking")
            st.caption(
                "Reference model ranking retained for compatibility with the existing product flow."
            )
            if baseline_error:
                _render_data_error("Baseline scores", baseline_error)
            elif baseline_df.empty:
                st.info("No baseline scores available.")
            else:
                st.dataframe(baseline_df, use_container_width=True, hide_index=True)

            st.subheader("Structured Insights")
            st.caption("Original top-driver artifact preserved as supporting context.")
            if insight_error:
                _render_data_error("Structured insights", insight_error)
            elif insight_df.empty:
                st.info("No structured insights available.")
            else:
                st.dataframe(insight_df, use_container_width=True, hide_index=True)

        with st.expander("Lap analysis and consistency tables", expanded=False):
            st.subheader("Lap Analysis")
            if lap_error:
                _render_data_error("Lap analysis", lap_error)
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

            st.subheader("Driver Consistency")
            if consistency_error:
                _render_data_error("Consistency table", consistency_error)
            elif full_consistency_df.empty:
                st.info("No consistency summary available for this session.")
            else:
                display_df = full_consistency_df[
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
    with artifact_right:
        with st.expander("Grounded explanations", expanded=True):
            st.subheader("Grounded Explanations")
            st.caption("Deterministic explanation output retained as a supporting narrative layer.")
            if explanation_error:
                _render_data_error("Grounded explanations", explanation_error)
            elif explanation_df.empty:
                st.info("No explanations available.")
            else:
                for row in explanation_df.to_dict("records"):
                    _render_story_card(
                        str(row.get("explanation_type", "Explanation")),
                        str(row.get("explanation_text", "")),
                        "grounded explanation",
                        "#d58cff",
                    )

        with st.expander("Pipeline status and artifact availability", expanded=False):
            _render_latest_run_summary(latest_run_data, latest_run_error)

if pipeline_result:
    with st.expander("Pipeline artifact response", expanded=False):
        st.json(pipeline_result)
