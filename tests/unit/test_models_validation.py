import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/models/src"))

from f1_models.baseline import build_baseline_driver_scores  # noqa: E402


@pytest.mark.unit
def test_baseline_requires_feature_columns(tmp_path: Path) -> None:
    features_path = tmp_path / "features_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position_numeric": 1,
            }
        ]
    )
    pq.write_table(table, features_path)

    with pytest.raises(ValueError, match="Missing required feature columns: feature_generated_at"):
        build_baseline_driver_scores(features_path=features_path, output_dir=tmp_path)


@pytest.mark.unit
def test_baseline_rejects_invalid_position_numeric(tmp_path: Path) -> None:
    features_path = tmp_path / "features_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position_numeric": 0,
                "feature_generated_at": "2026-03-13T00:00:00Z",
                "lap_time_ms": 92123,
                "lap_time_seconds": 92.123,
                "position": 1,
                "has_lap_time": True,
            }
        ]
    )
    pq.write_table(table, features_path)

    with pytest.raises(ValueError, match=r"Invalid position_numeric value \(row 0\)"):
        build_baseline_driver_scores(features_path=features_path, output_dir=tmp_path)
