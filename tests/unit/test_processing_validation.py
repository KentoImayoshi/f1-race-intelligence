from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


from f1_processing.processing import process_session_results  # noqa: E402


@pytest.mark.unit
def test_process_session_results_requires_raw_columns(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position": 1,
                "lap_time_ms": 92123,
            }
        ]
    )
    pq.write_table(table, raw_path)

    with pytest.raises(ValueError, match="Missing required raw columns: ingested_at, source"):
        process_session_results(raw_path=raw_path, output_dir=tmp_path)
