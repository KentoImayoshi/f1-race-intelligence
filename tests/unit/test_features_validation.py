import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/features/src"))

from f1_features.features import build_session_features  # noqa: E402


@pytest.mark.unit
def test_features_require_processed_columns(tmp_path: Path) -> None:
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
            }
        ]
    )
    pq.write_table(table, processed_path)

    with pytest.raises(ValueError, match="Missing required processed columns: processed_at"):
        build_session_features(processed_path=processed_path, output_dir=tmp_path)


@pytest.mark.unit
def test_position_numeric_requires_valid_position(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position": None,
                "lap_time_ms": 92123,
                "processed_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, processed_path)

    with pytest.raises(ValueError, match=r"Invalid position value \(row 0\)"):
        build_session_features(processed_path=processed_path, output_dir=tmp_path)
