from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from f1_insights.contracts import INSIGHT_SESSION_TOP_DRIVERS_COLUMNS
from f1_insights.insights import build_top_driver_insights


@pytest.mark.integration
def test_build_top_driver_insights(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_session_driver_scores.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position_numeric": 1,
                "score": 1.0,
                "model_generated_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "PER",
                "position_numeric": 2,
                "score": 0.5,
                "model_generated_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "LEC",
                "position_numeric": 3,
                "score": 0.5,
                "model_generated_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "Q",
                "driver_code": "NOR",
                "position_numeric": 1,
                "score": 1.0,
                "model_generated_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "Q",
                "driver_code": "PIA",
                "position_numeric": 2,
                "score": 0.5,
                "model_generated_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, baseline_path)

    output_path = build_top_driver_insights(
        baseline_path=baseline_path,
        output_dir=tmp_path,
        top_n=2,
    )
    out_table = pq.read_table(output_path)

    assert output_path.name == "insights_session_top_drivers.parquet"
    assert out_table.schema.names == INSIGHT_SESSION_TOP_DRIVERS_COLUMNS

    out_rows = out_table.to_pylist()
    assert len(out_rows) == 4

    r_session = [row for row in out_rows if row["session"] == "R"]
    assert [row["rank"] for row in r_session] == [1, 2]
    assert [row["driver_code"] for row in r_session] == ["VER", "LEC"]

    q_session = [row for row in out_rows if row["session"] == "Q"]
    assert [row["rank"] for row in q_session] == [1, 2]
    assert [row["driver_code"] for row in q_session] == ["NOR", "PIA"]
