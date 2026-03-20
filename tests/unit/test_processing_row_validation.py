from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_processing.processing import process_session_results


@pytest.mark.unit
def test_process_session_results_rejects_null_driver_code(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": None,
                "position": 1,
                "lap_time_ms": 92123,
                "source": "seed",
                "ingested_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, raw_path)

    with pytest.raises(ValueError, match=r"Missing required value: driver_code \(row 0\)"):
        process_session_results(raw_path=raw_path, output_dir=tmp_path)


@pytest.mark.unit
def test_process_session_results_rejects_empty_session(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": " ",
                "driver_code": "VER",
                "position": 1,
                "lap_time_ms": 92123,
                "source": "seed",
                "ingested_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, raw_path)

    with pytest.raises(ValueError, match=r"Missing required value: session \(row 0\)"):
        process_session_results(raw_path=raw_path, output_dir=tmp_path)
