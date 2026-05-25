from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_insights.contracts import (
    INTELLIGENCE_DRIVER_REPORT_COLUMNS,
    INTELLIGENCE_SESSION_SUMMARY_COLUMNS,
)
from f1_insights.insights import build_race_intelligence


@pytest.mark.integration
def test_build_race_intelligence_writes_expected_artifacts(tmp_path: Path) -> None:
    lap_analysis_path = tmp_path / "analytics_session_lap_analysis.parquet"
    sector_path = tmp_path / "analytics_session_sector_performance.parquet"
    tire_stints_path = tmp_path / "analytics_session_tire_stints.parquet"
    consistency_path = tmp_path / "analytics_session_driver_consistency.parquet"
    pace_path = tmp_path / "analytics_session_pace_evolution.parquet"
    baseline_path = tmp_path / "baseline_session_driver_scores.parquet"

    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "Q",
                    "driver_code": "VER",
                    "lap_number": 1,
                    "compound": "SOFT",
                    "stint": 1,
                    "lap_time_ms": 90000,
                    "delta_to_fastest_ms": 0,
                    "lap_rank": 1,
                    "top_speed_kph": 325,
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_number": 1,
                    "compound": "SOFT",
                    "stint": 1,
                    "lap_time_ms": 92000,
                    "delta_to_fastest_ms": 0,
                    "lap_rank": 1,
                    "top_speed_kph": 322,
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_number": 1,
                    "compound": "SOFT",
                    "stint": 1,
                    "lap_time_ms": 92500,
                    "delta_to_fastest_ms": 500,
                    "lap_rank": 2,
                    "top_speed_kph": 319,
                },
            ]
        ),
        lap_analysis_path,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_number": 1,
                    "sector_1_delta_ms": 0,
                    "sector_2_delta_ms": 20,
                    "sector_3_delta_ms": 10,
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_number": 1,
                    "sector_1_delta_ms": 50,
                    "sector_2_delta_ms": 40,
                    "sector_3_delta_ms": 30,
                },
            ]
        ),
        sector_path,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "stint": 1,
                    "compound": "SOFT",
                    "lap_count": 10,
                    "start_lap": 1,
                    "end_lap": 10,
                    "avg_lap_time_ms": 92200,
                    "best_lap_time_ms": 92000,
                    "avg_delta_to_fastest_ms": 100,
                    "avg_top_speed_kph": 322,
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "stint": 1,
                    "compound": "SOFT",
                    "lap_count": 10,
                    "start_lap": 1,
                    "end_lap": 10,
                    "avg_lap_time_ms": 92600,
                    "best_lap_time_ms": 92500,
                    "avg_delta_to_fastest_ms": 600,
                    "avg_top_speed_kph": 319,
                },
            ]
        ),
        tire_stints_path,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_count": 10,
                    "avg_lap_time_ms": 92200,
                    "best_lap_time_ms": 92000,
                    "lap_time_stddev_ms": 120,
                    "consistency_index": 0.92,
                    "avg_delta_to_fastest_ms": 100,
                    "top_speed_kph": 322,
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_count": 10,
                    "avg_lap_time_ms": 92600,
                    "best_lap_time_ms": 92500,
                    "lap_time_stddev_ms": 260,
                    "consistency_index": 0.81,
                    "avg_delta_to_fastest_ms": 600,
                    "top_speed_kph": 319,
                },
            ]
        ),
        consistency_path,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_number": 1,
                    "lap_time_ms": 92000,
                    "rolling_avg_lap_time_ms": 92000,
                    "delta_to_fastest_ms": 0,
                    "pace_trend": "baseline",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_number": 2,
                    "lap_time_ms": 92300,
                    "rolling_avg_lap_time_ms": 92150,
                    "delta_to_fastest_ms": 150,
                    "pace_trend": "declining",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_number": 1,
                    "lap_time_ms": 92500,
                    "rolling_avg_lap_time_ms": 92500,
                    "delta_to_fastest_ms": 500,
                    "pace_trend": "baseline",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_number": 2,
                    "lap_time_ms": 92900,
                    "rolling_avg_lap_time_ms": 92700,
                    "delta_to_fastest_ms": 700,
                    "pace_trend": "declining",
                },
            ]
        ),
        pace_path,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "session": "R",
                    "driver_code": "VER",
                    "score": 1.0,
                    "position_numeric": 1,
                    "model_generated_at": "2026-03-13T00:00:00Z",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "session": "R",
                    "driver_code": "PER",
                    "score": 0.8,
                    "position_numeric": 2,
                    "model_generated_at": "2026-03-13T00:00:00Z",
                },
            ]
        ),
        baseline_path,
    )

    outputs = build_race_intelligence(
        lap_analysis_path=lap_analysis_path,
        sector_performance_path=sector_path,
        tire_stints_path=tire_stints_path,
        driver_consistency_path=consistency_path,
        pace_evolution_path=pace_path,
        baseline_path=baseline_path,
        output_dir=tmp_path,
    )

    session_summary_table = pq.read_table(outputs["session_summaries"])
    driver_report_table = pq.read_table(outputs["driver_reports"])

    assert session_summary_table.schema.names == INTELLIGENCE_SESSION_SUMMARY_COLUMNS
    assert driver_report_table.schema.names == INTELLIGENCE_DRIVER_REPORT_COLUMNS
    assert session_summary_table.num_rows > 0
    assert driver_report_table.num_rows > 0
