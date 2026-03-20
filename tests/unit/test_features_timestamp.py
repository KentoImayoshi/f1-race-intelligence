from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_features.features import build_session_features


@pytest.mark.unit
def test_feature_generated_at_is_utc_iso(tmp_path: Path) -> None:
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
            }
        ]
    )
    pq.write_table(table, processed_path)

    output_path = build_session_features(processed_path=processed_path, output_dir=tmp_path)
    out_table = pq.read_table(output_path)

    generated_at = out_table.column("feature_generated_at").to_pylist()[0]
    parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))

    assert parsed.tzinfo == timezone.utc
