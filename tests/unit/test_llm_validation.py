from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_llm.explanations import build_top_driver_explanations


@pytest.mark.unit
def test_explanations_require_insight_columns(tmp_path: Path) -> None:
    insights_path = tmp_path / "insights_session_top_drivers.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "rank": 1,
                "driver_code": "VER",
            }
        ]
    )
    pq.write_table(table, insights_path)

    with pytest.raises(
        ValueError,
        match="Missing required insight columns: insight_generated_at, score",
    ):
        build_top_driver_explanations(insights_path=insights_path, output_dir=tmp_path)


@pytest.mark.unit
def test_explanations_reject_empty_input(tmp_path: Path) -> None:
    insights_path = tmp_path / "insights_session_top_drivers.parquet"

    table = pa.Table.from_pylist(
        [],
        schema=pa.schema(
            [
                ("season", pa.int64()),
                ("round", pa.int64()),
                ("session", pa.string()),
                ("rank", pa.int64()),
                ("driver_code", pa.string()),
                ("score", pa.float64()),
                ("insight_generated_at", pa.string()),
            ]
        ),
    )
    pq.write_table(table, insights_path)

    with pytest.raises(ValueError, match="No insight rows to explain"):
        build_top_driver_explanations(insights_path=insights_path, output_dir=tmp_path)
