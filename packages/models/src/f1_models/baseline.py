"""Baseline analytical outputs for session-level driver performance."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_models.contracts import BASELINE_SESSION_DRIVER_SCORES_COLUMNS

REQUIRED_FEATURE_COLUMNS = {
    "season",
    "round",
    "session",
    "driver_code",
    "position_numeric",
    "feature_generated_at",
}


def build_baseline_driver_scores(*, features_path: Path, output_dir: Path) -> Path:
    """Compute a simple baseline score from session features."""
    table = pq.read_table(features_path)
    missing = REQUIRED_FEATURE_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required feature columns: {missing_list}")

    model_generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    records = []
    for index, row in enumerate(table.to_pylist()):
        position_numeric = _require_position_numeric(row.get("position_numeric"), index=index)
        score = 1.0 / position_numeric

        records.append(
            {
                "season": row["season"],
                "round": row["round"],
                "session": row["session"],
                "driver_code": row["driver_code"],
                "position_numeric": position_numeric,
                "score": score,
                "model_generated_at": model_generated_at,
            }
        )

    schema = pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("position_numeric", pa.int64()),
            ("score", pa.float64()),
            ("model_generated_at", pa.string()),
        ]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "baseline_session_driver_scores.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=schema), output_path)

    return output_path


def _require_position_numeric(value: object, *, index: int) -> int:
    if value is None:
        raise ValueError(f"Invalid position_numeric value (row {index})")
    try:
        position = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid position_numeric value (row {index})") from exc
    if position <= 0:
        raise ValueError(f"Invalid position_numeric value (row {index})")
    return position
