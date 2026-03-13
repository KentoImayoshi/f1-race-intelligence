import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/features/src"))

from f1_features.features import build_session_features  # noqa: E402


@pytest.mark.unit
def test_has_lap_time_semantics(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position": 1,
                "lap_time_ms": 0,
                "processed_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "PER",
                "position": 2,
                "lap_time_ms": 92123,
                "processed_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, processed_path)

    output_path = build_session_features(processed_path=processed_path, output_dir=tmp_path)
    out_table = pq.read_table(output_path)

    has_lap_time = out_table.column("has_lap_time").to_pylist()

    assert has_lap_time == [False, True]
