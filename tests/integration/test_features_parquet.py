from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/features/src"))

from f1_features.contracts import FEATURE_SESSION_RESULTS_COLUMNS  # noqa: E402
from f1_features.features import build_session_features  # noqa: E402


@pytest.mark.integration
def test_build_session_features_writes_parquet(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position": 1,
                "lap_time_ms": 92123,
                "processed_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "PER",
                "position": 2,
                "lap_time_ms": 0,
                "processed_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, processed_path)

    output_path = build_session_features(processed_path=processed_path, output_dir=tmp_path)
    out_table = pq.read_table(output_path)

    assert output_path.name == "features_session_results.parquet"
    assert out_table.schema.names == FEATURE_SESSION_RESULTS_COLUMNS
    assert out_table.num_rows == table.num_rows
