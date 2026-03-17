from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/insights/src"))

from f1_insights.insights import build_top_driver_insights  # noqa: E402


@pytest.mark.unit
def test_insights_require_baseline_columns(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_session_driver_scores.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "score": 1.0,
            }
        ]
    )
    pq.write_table(table, baseline_path)

    with pytest.raises(
        ValueError,
        match="Missing required baseline columns: model_generated_at, position_numeric",
    ):
        build_top_driver_insights(
            baseline_path=baseline_path,
            output_dir=tmp_path,
        )


@pytest.mark.unit
def test_insights_reject_top_n_leq_zero(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_session_driver_scores.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "score": 1.0,
                "position_numeric": 1,
                "model_generated_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, baseline_path)

    with pytest.raises(
        ValueError,
        match="top_n must be greater than 0",
    ):
        build_top_driver_insights(
            baseline_path=baseline_path,
            output_dir=tmp_path,
            top_n=0,
        )
