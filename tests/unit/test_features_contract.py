import pytest
from f1_features.contracts import (
    FEATURE_SESSION_RESULTS_COLUMNS,
    SESSION_DRIVER_CONSISTENCY_COLUMNS,
    SESSION_LAP_ANALYSIS_COLUMNS,
    SESSION_PACE_EVOLUTION_COLUMNS,
    SESSION_SECTOR_PERFORMANCE_COLUMNS,
    SESSION_TIRE_STINT_COLUMNS,
)


@pytest.mark.unit
def test_feature_contract_columns() -> None:
    assert FEATURE_SESSION_RESULTS_COLUMNS == [
        "season",
        "round",
        "session",
        "driver_code",
        "position",
        "lap_time_ms",
        "has_lap_time",
        "lap_time_seconds",
        "position_numeric",
        "feature_generated_at",
    ]


@pytest.mark.unit
def test_analytics_contract_columns() -> None:
    assert SESSION_LAP_ANALYSIS_COLUMNS[0:6] == [
        "season",
        "round",
        "grand_prix",
        "session",
        "driver_code",
        "lap_number",
    ]
    assert "delta_to_fastest_ms" in SESSION_LAP_ANALYSIS_COLUMNS
    assert "avg_delta_to_fastest_ms" in SESSION_TIRE_STINT_COLUMNS
    assert "consistency_index" in SESSION_DRIVER_CONSISTENCY_COLUMNS
    assert "pace_trend" in SESSION_PACE_EVOLUTION_COLUMNS
    assert "combined_sector_ms" in SESSION_SECTOR_PERFORMANCE_COLUMNS
