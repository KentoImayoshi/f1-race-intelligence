"""Minimal processing slice for raw session results."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_processing.contracts import PROCESSED_SESSION_RESULTS_COLUMNS

REQUIRED_RAW_COLUMNS = {
    "season",
    "round",
    "session",
    "driver_code",
    "position",
    "lap_time_ms",
    "source",
    "ingested_at",
}


def process_session_results(*, raw_path: Path, output_dir: Path) -> Path:
    """Read raw session results and write a processed parquet artifact."""
    table = pq.read_table(raw_path)
    missing = REQUIRED_RAW_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required raw columns: {missing_list}")

    processed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    records = []
    for index, row in enumerate(table.to_pylist()):
        _require_value(row.get("season"), "season", index=index)
        _require_value(row.get("round"), "round", index=index)
        _require_text(row.get("session"), "session", index=index)
        _require_text(row.get("driver_code"), "driver_code", index=index)
        _require_value(row.get("position"), "position", index=index)
        _require_value(row.get("lap_time_ms"), "lap_time_ms", index=index)

        records.append(
            {
                "season": row["season"],
                "round": row["round"],
                "session": row["session"],
                "driver_code": row["driver_code"],
                "position": row["position"],
                "lap_time_ms": row["lap_time_ms"],
                "processed_at": processed_at,
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
            ("processed_at", pa.string()),
        ]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "processed_session_results.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=schema), output_path)

    return output_path


def _require_value(value: object, field: str, *, index: int) -> None:
    if value is None:
        raise ValueError(f"Missing required value: {field} (row {index})")


def _require_text(value: object, field: str, *, index: int) -> None:
    if value is None:
        raise ValueError(f"Missing required value: {field} (row {index})")
    if not str(value).strip():
        raise ValueError(f"Missing required value: {field} (row {index})")
