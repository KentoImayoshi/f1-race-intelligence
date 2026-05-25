"""Contracts for structured insights and race intelligence outputs."""

from __future__ import annotations

INSIGHT_SESSION_TOP_DRIVERS_COLUMNS = [
    "season",
    "round",
    "session",
    "rank",
    "driver_code",
    "score",
    "insight_generated_at",
]

INTELLIGENCE_PACE_DEGRADATION_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "pace_slope_ms_per_lap",
    "degradation_level",
    "supporting_delta_ms",
    "intelligence_generated_at",
]

INTELLIGENCE_SECTOR_DOMINANCE_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "dominant_sector",
    "sector_win_count",
    "avg_sector_advantage_ms",
    "dominance_label",
    "intelligence_generated_at",
]

INTELLIGENCE_CONSISTENCY_SCORES_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "consistency_index",
    "consistency_band",
    "lap_time_stddev_ms",
    "reliability_score",
    "intelligence_generated_at",
]

INTELLIGENCE_TIRE_WINDOWS_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "stint",
    "compound",
    "performance_window_start_lap",
    "performance_window_end_lap",
    "window_quality",
    "window_avg_lap_time_ms",
    "intelligence_generated_at",
]

INTELLIGENCE_STRATEGY_OPPORTUNITIES_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "opportunity_type",
    "reference_driver",
    "opportunity_delta_ms",
    "window_start_lap",
    "window_end_lap",
    "opportunity_label",
    "intelligence_generated_at",
]

INTELLIGENCE_STINT_STRENGTH_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "stint",
    "compound",
    "strength_score",
    "strength_label",
    "avg_delta_to_fastest_ms",
    "intelligence_generated_at",
]

INTELLIGENCE_RACE_PACE_RANKINGS_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "rank",
    "driver_code",
    "race_pace_score",
    "pace_gap_ms",
    "ranking_reason",
    "intelligence_generated_at",
]

INTELLIGENCE_QUALIFYING_RACE_COMPARISON_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "driver_code",
    "qualifying_best_lap_ms",
    "race_best_lap_ms",
    "qualifying_to_race_gap_ms",
    "conversion_label",
    "intelligence_generated_at",
]

INTELLIGENCE_SESSION_SUMMARY_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "summary_type",
    "headline",
    "detail",
    "importance_score",
    "intelligence_generated_at",
]

INTELLIGENCE_DRIVER_REPORT_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "report_title",
    "performance_summary",
    "strategy_summary",
    "tire_summary",
    "trend_summary",
    "intelligence_generated_at",
]

INTELLIGENCE_STRATEGY_SUMMARY_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "strategy_headline",
    "strategy_detail",
    "opportunity_type",
    "opportunity_label",
    "intelligence_generated_at",
]

INTELLIGENCE_RACE_TREND_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "trend_category",
    "trend_headline",
    "trend_detail",
    "intelligence_generated_at",
]
