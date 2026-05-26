from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

DASHBOARD_SRC = Path(__file__).resolve().parents[2] / "apps" / "dashboard" / "src"
if str(DASHBOARD_SRC) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_SRC))


class _ContextBlock:
    def __enter__(self) -> _ContextBlock:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def metric(self, *args, **kwargs) -> None:
        return None

    def dataframe(self, *args, **kwargs) -> None:
        return None

    def subheader(self, *args, **kwargs) -> None:
        return None

    def caption(self, *args, **kwargs) -> None:
        return None

    def error(self, *args, **kwargs) -> None:
        return None

    def warning(self, *args, **kwargs) -> None:
        return None

    def success(self, *args, **kwargs) -> None:
        return None

    def info(self, *args, **kwargs) -> None:
        return None

    def markdown(self, *args, **kwargs) -> None:
        return None


class _Sidebar:
    def form(self, **kwargs) -> _ContextBlock:
        return _ContextBlock()

    def checkbox(self, *args, **kwargs) -> bool:
        return False

    def selectbox(self, label: str, options: list[str], index: int = 0, **kwargs) -> str:
        return options[index]


class _Response:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.status_code = 200
        self.reason = "OK"
        self.text = ""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _RequestsModule(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("requests")
        self.calls: list[tuple[str, dict[str, object] | None]] = []
        self.RequestException = Exception
        self.HTTPError = Exception

    def get(self, endpoint: str, params=None, timeout: int = 10) -> _Response:
        copied_params = dict(params) if params is not None else None
        self.calls.append((endpoint, copied_params))
        payload: object = {} if endpoint.endswith("/meta/last-run") else []
        return _Response(payload)

    def post(self, endpoint: str, json=None, timeout: int = 45) -> _Response:
        return _Response({})


class _StreamlitModule(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("streamlit")
        self.secrets: dict[str, str] = {}
        self.session_state = _SessionState()
        self.sidebar = _Sidebar()

    def set_page_config(self, **kwargs) -> None:
        return None

    def markdown(self, *args, **kwargs) -> None:
        return None

    def subheader(self, *args, **kwargs) -> None:
        return None

    def caption(self, *args, **kwargs) -> None:
        return None

    def warning(self, *args, **kwargs) -> None:
        return None

    def info(self, *args, **kwargs) -> None:
        return None

    def error(self, *args, **kwargs) -> None:
        return None

    def success(self, *args, **kwargs) -> None:
        return None

    def columns(self, spec) -> list[_ContextBlock]:
        count = spec if isinstance(spec, int) else len(spec)
        return [_ContextBlock() for _ in range(count)]

    def container(self) -> _ContextBlock:
        return _ContextBlock()

    def spinner(self, *args, **kwargs) -> _ContextBlock:
        return _ContextBlock()

    def number_input(self, label: str, **kwargs) -> int:
        return kwargs["value"]

    def selectbox(self, label: str, options: list[str], index: int = 0, **kwargs) -> str:
        return options[index]

    def form_submit_button(self, *args, **kwargs) -> bool:
        return False

    def tabs(self, labels: list[str]) -> list[_ContextBlock]:
        return [_ContextBlock() for _ in labels]

    def dataframe(self, *args, **kwargs) -> None:
        return None

    def metric(self, *args, **kwargs) -> None:
        return None

    def line_chart(self, *args, **kwargs) -> None:
        return None

    def bar_chart(self, *args, **kwargs) -> None:
        return None

    def expander(self, *args, **kwargs) -> _ContextBlock:
        return _ContextBlock()

    def json(self, *args, **kwargs) -> None:
        return None

    def altair_chart(self, *args, **kwargs) -> None:
        return None


class _SessionState(dict[str, object]):
    def __getattr__(self, item: str) -> object:
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: object) -> None:
        self[key] = value


def _load_dashboard_app(monkeypatch: pytest.MonkeyPatch):
    streamlit_module = _StreamlitModule()
    streamlit_errors = types.ModuleType("streamlit.errors")

    class StreamlitSecretNotFoundError(Exception):
        pass

    streamlit_errors.StreamlitSecretNotFoundError = StreamlitSecretNotFoundError
    requests_module = _RequestsModule()
    autorefresh_module = types.ModuleType("streamlit_autorefresh")
    autorefresh_module.st_autorefresh = lambda *args, **kwargs: 0

    monkeypatch.setitem(sys.modules, "streamlit", streamlit_module)
    monkeypatch.setitem(sys.modules, "streamlit.errors", streamlit_errors)
    monkeypatch.setitem(sys.modules, "requests", requests_module)
    monkeypatch.setitem(sys.modules, "streamlit_autorefresh", autorefresh_module)
    monkeypatch.delitem(sys.modules, "f1_dashboard.app", raising=False)

    app_module = importlib.import_module("f1_dashboard.app")
    return app_module, requests_module


@pytest.mark.unit
def test_build_params_accepts_year_alias_and_emits_season(monkeypatch: pytest.MonkeyPatch) -> None:
    app_module, _ = _load_dashboard_app(monkeypatch)

    params = app_module._build_params(
        year=2024,
        round_value=7,
        session_code="R",
        driver_code="VER",
        limit=50,
    )

    assert params == {
        "season": 2024,
        "round": 7,
        "session": "R",
        "driver": "VER",
        "limit": 50,
    }


@pytest.mark.unit
def test_build_params_rejects_conflicting_year_and_season(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module, _ = _load_dashboard_app(monkeypatch)

    with pytest.raises(ValueError, match="must match"):
        app_module._build_params(year=2024, season=2025, round_value=7, session_code="R")


@pytest.mark.unit
def test_dashboard_import_uses_consistent_query_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module, requests_module = _load_dashboard_app(monkeypatch)

    queried_endpoints = {
        endpoint: params
        for endpoint, params in requests_module.calls
        if endpoint != app_module.LATEST_RUN_ENDPOINT
    }

    expected_endpoints = {
        app_module.LAP_ANALYSIS_ENDPOINT,
        app_module.PACE_EVOLUTION_ENDPOINT,
        app_module.TIRE_STINTS_ENDPOINT,
        app_module.CONSISTENCY_ENDPOINT,
        app_module.BASELINE_ENDPOINT,
        app_module.INSIGHTS_ENDPOINT,
        app_module.EXPLANATIONS_ENDPOINT,
        app_module.SESSION_INTELLIGENCE_ENDPOINT,
        app_module.DRIVER_REPORTS_ENDPOINT,
        app_module.STRATEGY_INSIGHTS_ENDPOINT,
        app_module.RACE_TRENDS_ENDPOINT,
    }

    assert expected_endpoints.issubset(queried_endpoints)
    for endpoint in expected_endpoints:
        params = queried_endpoints[endpoint]
        assert params is not None
        assert params["season"] == 2024
        assert "year" not in params
        assert params["round"] == 1
        assert params["session"] == "R"


@pytest.mark.unit
def test_build_executive_summary_surfaces_expected_leaders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module, _ = _load_dashboard_app(monkeypatch)

    lap_df = app_module.pd.DataFrame(
        [
            {
                "driver_code": "VER",
                "lap_time_seconds": 91.2,
                "top_speed_kph": 324,
                "sector_1_ms": 30500,
                "sector_2_ms": 30900,
                "sector_3_ms": 31100,
            },
            {
                "driver_code": "LEC",
                "lap_time_seconds": 91.9,
                "top_speed_kph": 319,
                "sector_1_ms": 30700,
                "sector_2_ms": 30880,
                "sector_3_ms": 31200,
            },
        ]
    )
    consistency_df = app_module.pd.DataFrame(
        [
            {"driver_code": "LEC", "consistency_index": 0.93, "lap_time_stddev_ms": 90},
            {"driver_code": "VER", "consistency_index": 0.82, "lap_time_stddev_ms": 150},
        ]
    )
    stint_df = app_module.pd.DataFrame(
        [
            {
                "driver_code": "VER",
                "lap_count": 10,
                "avg_delta_to_fastest_ms": 150,
                "best_lap_time_ms": 91200,
                "compound": "SOFT",
                "start_lap": 1,
                "end_lap": 10,
            },
            {
                "driver_code": "LEC",
                "lap_count": 10,
                "avg_delta_to_fastest_ms": 300,
                "best_lap_time_ms": 91900,
                "compound": "MEDIUM",
                "start_lap": 1,
                "end_lap": 10,
            },
        ]
    )
    pace_df = app_module.pd.DataFrame(
        [
            {"driver_code": "VER", "lap_number": 1, "rolling_avg_lap_time_ms": 91000},
            {"driver_code": "VER", "lap_number": 2, "rolling_avg_lap_time_ms": 91450},
            {"driver_code": "LEC", "lap_number": 1, "rolling_avg_lap_time_ms": 91900},
            {"driver_code": "LEC", "lap_number": 2, "rolling_avg_lap_time_ms": 92020},
        ]
    )
    session_intelligence_df = app_module.pd.DataFrame(
        [
            {
                "headline": "VER controls the race",
                "detail": "Clear pace and strategy advantage.",
                "summary_type": "driver_performance",
                "importance_score": 99.0,
            }
        ]
    )

    summary_cards, spotlight = app_module._build_executive_summary(
        lap_df,
        consistency_df,
        stint_df,
        pace_df,
        session_intelligence_df,
    )

    assert {card["title"] for card in summary_cards} == {
        "Fastest Driver",
        "Most Consistent",
        "Tire Strategy Winner",
        "Biggest Pace Degradation",
        "Sector Dominance Leader",
    }
    cards_by_title = {card["title"]: card for card in summary_cards}
    assert cards_by_title["Fastest Driver"]["value"] == "VER"
    assert cards_by_title["Most Consistent"]["value"] == "LEC"
    assert cards_by_title["Tire Strategy Winner"]["value"] == "VER"
    assert cards_by_title["Biggest Pace Degradation"]["value"] == "VER"
    assert cards_by_title["Sector Dominance Leader"]["value"] == "VER"
    assert spotlight["title"] == "VER controls the race"
