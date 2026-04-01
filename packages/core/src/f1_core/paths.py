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


def processed_session_results_path() -> Path:
    return processed_dir() / "processed_session_results.parquet"


def features_session_results_path() -> Path:
    return features_dir() / "features_session_results.parquet"


def baseline_driver_scores_path() -> Path:
    return models_dir() / "baseline_session_driver_scores.parquet"


def insights_session_top_drivers_path() -> Path:
    return insights_dir() / "insights_session_top_drivers.parquet"


def explanations_session_top_drivers_path() -> Path:
    return llm_dir() / "explanations_session_top_drivers.parquet"
