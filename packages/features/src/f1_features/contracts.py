"""Contracts for features outputs."""

from __future__ import annotations

FEATURE_SESSION_RESULTS_COLUMNS = [
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

SESSION_LAP_ANALYSIS_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "compound",
    "stint",
    "lap_time_ms",
    "lap_time_seconds",
    "sector_1_ms",
    "sector_2_ms",
    "sector_3_ms",
    "delta_to_fastest_ms",
    "delta_to_fastest_pct",
    "lap_rank",
    "top_speed_kph",
    "tyre_life_laps",
    "is_personal_best",
    "analysis_generated_at",
]

SESSION_SECTOR_PERFORMANCE_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "sector_1_ms",
    "sector_1_delta_ms",
    "sector_2_ms",
    "sector_2_delta_ms",
    "sector_3_ms",
    "sector_3_delta_ms",
    "combined_sector_ms",
    "top_speed_kph",
    "analysis_generated_at",
]

SESSION_TIRE_STINT_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "stint",
    "compound",
    "lap_count",
    "start_lap",
    "end_lap",
    "avg_lap_time_ms",
    "best_lap_time_ms",
    "avg_delta_to_fastest_ms",
    "avg_top_speed_kph",
    "analysis_generated_at",
]

SESSION_DRIVER_CONSISTENCY_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_count",
    "avg_lap_time_ms",
    "best_lap_time_ms",
    "lap_time_stddev_ms",
    "consistency_index",
    "avg_delta_to_fastest_ms",
    "top_speed_kph",
    "analysis_generated_at",
]

SESSION_PACE_EVOLUTION_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "lap_time_ms",
    "rolling_avg_lap_time_ms",
    "delta_to_fastest_ms",
    "pace_trend",
    "top_speed_kph",
    "analysis_generated_at",
]
