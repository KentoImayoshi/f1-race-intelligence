from __future__ import annotations

from pathlib import Path

DATA_DIR = Path("data")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    return _ensure_dir(DATA_DIR)


def raw_dir() -> Path:
    return _ensure_dir(data_dir() / "raw")


def processed_dir() -> Path:
    return _ensure_dir(data_dir() / "processed")


def features_dir() -> Path:
    return _ensure_dir(data_dir() / "features")


def models_dir() -> Path:
    return _ensure_dir(data_dir() / "models")


def insights_dir() -> Path:
    return _ensure_dir(data_dir() / "insights")


def llm_dir() -> Path:
    return _ensure_dir(data_dir() / "llm")


def artifacts_dir() -> Path:
    return _ensure_dir(data_dir() / "artifacts")


def run_manifests_dir() -> Path:
    return _ensure_dir(artifacts_dir() / "run_manifests")


def latest_run_manifest_path() -> Path:
    return artifacts_dir() / "latest_run_manifest.json"


def raw_session_results_path() -> Path:
    return raw_dir() / "raw_session_results.parquet"


def raw_session_laps_path() -> Path:
    return raw_dir() / "raw_session_laps.parquet"


def raw_session_telemetry_path() -> Path:
    return raw_dir() / "raw_session_telemetry.parquet"


def processed_session_results_path() -> Path:
    return processed_dir() / "processed_session_results.parquet"


def features_session_results_path() -> Path:
    return features_dir() / "features_session_results.parquet"


def lap_analysis_path() -> Path:
    return features_dir() / "analytics_session_lap_analysis.parquet"


def sector_performance_path() -> Path:
    return features_dir() / "analytics_session_sector_performance.parquet"


def tire_stint_summary_path() -> Path:
    return features_dir() / "analytics_session_tire_stints.parquet"


def driver_consistency_path() -> Path:
    return features_dir() / "analytics_session_driver_consistency.parquet"


def pace_evolution_path() -> Path:
    return features_dir() / "analytics_session_pace_evolution.parquet"


def baseline_driver_scores_path() -> Path:
    return models_dir() / "baseline_session_driver_scores.parquet"


def insights_session_top_drivers_path() -> Path:
    return insights_dir() / "insights_session_top_drivers.parquet"


def intelligence_pace_degradation_path() -> Path:
    return insights_dir() / "intelligence_pace_degradation.parquet"


def intelligence_sector_dominance_path() -> Path:
    return insights_dir() / "intelligence_sector_dominance.parquet"


def intelligence_consistency_scores_path() -> Path:
    return insights_dir() / "intelligence_consistency_scores.parquet"


def intelligence_tire_windows_path() -> Path:
    return insights_dir() / "intelligence_tire_performance_windows.parquet"


def intelligence_strategy_opportunities_path() -> Path:
    return insights_dir() / "intelligence_strategy_opportunities.parquet"


def intelligence_stint_strength_path() -> Path:
    return insights_dir() / "intelligence_stint_strength.parquet"


def intelligence_race_pace_rankings_path() -> Path:
    return insights_dir() / "intelligence_race_pace_rankings.parquet"


def intelligence_qualifying_race_comparison_path() -> Path:
    return insights_dir() / "intelligence_qualifying_race_comparison.parquet"


def intelligence_session_summaries_path() -> Path:
    return insights_dir() / "intelligence_session_summaries.parquet"


def intelligence_driver_reports_path() -> Path:
    return insights_dir() / "intelligence_driver_reports.parquet"


def intelligence_strategy_summaries_path() -> Path:
    return insights_dir() / "intelligence_strategy_summaries.parquet"


def intelligence_race_trends_path() -> Path:
    return insights_dir() / "intelligence_race_trends.parquet"


def explanations_session_top_drivers_path() -> Path:
    return llm_dir() / "explanations_session_top_drivers.parquet"
