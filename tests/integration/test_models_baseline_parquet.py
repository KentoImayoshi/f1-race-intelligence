from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/models/src"))

from f1_models.baseline import build_baseline_driver_scores  # noqa: E402
from f1_models.contracts import BASELINE_SESSION_DRIVER_SCORES_COLUMNS  # noqa: E402


@pytest.mark.integration
def test_build_baseline_driver_scores(tmp_path: Path) -> None:
    features_path = tmp_path / "features_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position_numeric": 1,
                "feature_generated_at": "2026-03-13T00:00:00Z",
                "lap_time_ms": 92123,
                "lap_time_seconds": 92.123,
                "position": 1,
                "has_lap_time": True,
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "PER",
                "position_numeric": 2,
                "feature_generated_at": "2026-03-13T00:00:00Z",
                "lap_time_ms": 92456,
                "lap_time_seconds": 92.456,
                "position": 2,
                "has_lap_time": True,
            },
        ]
    )
    pq.write_table(table, features_path)

    output_path = build_baseline_driver_scores(features_path=features_path, output_dir=tmp_path)
    out_table = pq.read_table(output_path)

    assert output_path.name == "baseline_session_driver_scores.parquet"
    assert out_table.schema.names == BASELINE_SESSION_DRIVER_SCORES_COLUMNS
    assert out_table.num_rows == table.num_rows

    scores = out_table.column("score").to_pylist()
    assert scores[0] > scores[1]
    assert scores == [1.0, 0.5]
