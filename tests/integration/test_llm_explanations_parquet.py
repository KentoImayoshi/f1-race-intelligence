from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from f1_llm.contracts import EXPLANATION_SESSION_TOP_DRIVERS_COLUMNS
from f1_llm.explanations import build_top_driver_explanations


@pytest.mark.integration
def test_build_top_driver_explanations(tmp_path: Path) -> None:
    insights_path = tmp_path / "insights_session_top_drivers.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "rank": 1,
                "driver_code": "VER",
                "score": 1.0,
                "insight_generated_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "rank": 2,
                "driver_code": "LEC",
                "score": 0.5,
                "insight_generated_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "Q",
                "rank": 1,
                "driver_code": "NOR",
                "score": 1.0,
                "insight_generated_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, insights_path)

    output_path = build_top_driver_explanations(
        insights_path=insights_path,
        output_dir=tmp_path,
    )
    out_table = pq.read_table(output_path)

    assert output_path.name == "explanations_session_top_drivers.parquet"
    assert out_table.schema.names == EXPLANATION_SESSION_TOP_DRIVERS_COLUMNS

    out_rows = out_table.to_pylist()
    assert len(out_rows) == 2

    r_session = [row for row in out_rows if row["session"] == "R"][0]
    assert r_session["explanation_type"] == "top_drivers"
    assert r_session["explanation_text"] == (
        "Top drivers: VER (rank 1, score 1.0), LEC (rank 2, score 0.5)."
    )

    q_session = [row for row in out_rows if row["session"] == "Q"][0]
    assert q_session["explanation_text"] == ("Top drivers: NOR (rank 1, score 1.0).")
