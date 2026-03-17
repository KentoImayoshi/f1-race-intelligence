from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/features/src"))

from f1_features.features import build_session_features  # noqa: E402


@pytest.mark.unit
def test_features_rejects_missing_driver_code(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": None,
                "position": 1,
                "lap_time_ms": 92123,
                "processed_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, processed_path)

    with pytest.raises(ValueError, match=r"Missing required value: driver_code \(row 0\)"):
        build_session_features(processed_path=processed_path, output_dir=tmp_path)


@pytest.mark.unit
def test_features_rejects_missing_session(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": " ",
                "driver_code": "VER",
                "position": 1,
                "lap_time_ms": 92123,
                "processed_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, processed_path)

    with pytest.raises(ValueError, match=r"Missing required value: session \(row 0\)"):
        build_session_features(processed_path=processed_path, output_dir=tmp_path)
