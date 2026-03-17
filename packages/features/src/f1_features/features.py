"""Minimal feature engineering for session results."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_features.contracts import FEATURE_SESSION_RESULTS_COLUMNS

REQUIRED_PROCESSED_COLUMNS = {
    "season",
    "round",
    "session",
    "driver_code",
    "position",
    "lap_time_ms",
    "processed_at",
}


def build_session_features(*, processed_path: Path, output_dir: Path) -> Path:
    """Read processed session results and write a features parquet artifact."""
    table = pq.read_table(processed_path)
    missing = REQUIRED_PROCESSED_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required processed columns: {missing_list}")

    feature_generated_at = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    records = []
    for index, row in enumerate(table.to_pylist()):
        _require_value(row.get("season"), "season", index=index)
        _require_value(row.get("round"), "round", index=index)
        _require_text(row.get("session"), "session", index=index)
        _require_text(row.get("driver_code"), "driver_code", index=index)
        _require_value(row.get("lap_time_ms"), "lap_time_ms", index=index)

        position_numeric = _require_position(row.get("position"), index=index)
        lap_time_ms = row.get("lap_time_ms")
        has_lap_time = bool(lap_time_ms) and lap_time_ms > 0
        lap_time_seconds = float(lap_time_ms) / 1000.0 if lap_time_ms is not None else 0.0

        records.append(
            {
                "season": row["season"],
                "round": row["round"],
                "session": row["session"],
                "driver_code": row["driver_code"],
                "position": row["position"],
                "lap_time_ms": lap_time_ms,
                "has_lap_time": has_lap_time,
                "lap_time_seconds": lap_time_seconds,
                "position_numeric": position_numeric,
                "feature_generated_at": feature_generated_at,
            }
        )

    schema = pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("position", pa.int64()),
            ("lap_time_ms", pa.int64()),
            ("has_lap_time", pa.bool_()),
            ("lap_time_seconds", pa.float64()),
            ("position_numeric", pa.int64()),
            ("feature_generated_at", pa.string()),
        ]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features_session_results.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=schema), output_path)

    return output_path


def _require_position(value: object, *, index: int) -> int:
    if value is None:
        raise ValueError(f"Invalid position value (row {index})")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid position value (row {index})") from exc


def _require_value(value: object, field: str, *, index: int) -> None:
    if value is None:
        raise ValueError(f"Missing required value: {field} (row {index})")


def _require_text(value: object, field: str, *, index: int) -> None:
    if value is None:
        raise ValueError(f"Missing required value: {field} (row {index})")
    if not str(value).strip():
        raise ValueError(f"Missing required value: {field} (row {index})")
