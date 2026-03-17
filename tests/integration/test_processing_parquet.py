from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/processing/src"))

from f1_processing.contracts import PROCESSED_SESSION_RESULTS_COLUMNS  # noqa: E402
from f1_processing.processing import process_session_results  # noqa: E402


@pytest.mark.integration
def test_process_session_results_writes_parquet(tmp_path: Path) -> None:
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
                "source": "seed",
                "ingested_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "PER",
                "position": 2,
                "lap_time_ms": 92456,
                "source": "seed",
                "ingested_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, raw_path)

    output_path = process_session_results(raw_path=raw_path, output_dir=tmp_path)

    out_table = pq.read_table(output_path)

    assert output_path.name == "processed_session_results.parquet"
    assert out_table.schema.names == PROCESSED_SESSION_RESULTS_COLUMNS
    assert out_table.num_rows == table.num_rows
