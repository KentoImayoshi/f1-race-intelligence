"""Grounded explanations for structured insights."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

REQUIRED_INSIGHT_COLUMNS = {
    "season",
    "round",
    "session",
    "rank",
    "driver_code",
    "score",
    "insight_generated_at",
}


def build_top_driver_explanations(*, insights_path: Path, output_dir: Path) -> Path:
    """Build deterministic explanations from top driver insights."""
    table = pq.read_table(insights_path)
    missing = REQUIRED_INSIGHT_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required insight columns: {missing_list}")

    rows = table.to_pylist()
    if not rows:
        raise ValueError("No insight rows to explain")

    explanation_generated_at = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    grouped: dict[tuple[int, int, str], list[dict[str, object]]] = {}
    for row in rows:
        key = (int(row["season"]), int(row["round"]), str(row["session"]))
        grouped.setdefault(key, []).append(row)

    records = []
    for (season, round_number, session), group_rows in grouped.items():
        sorted_rows = sorted(group_rows, key=lambda r: int(r["rank"]))
        parts = [
            f"{row['driver_code']} (rank {int(row['rank'])}, score {float(row['score'])})"
            for row in sorted_rows
        ]
        explanation_text = f"Top drivers: {', '.join(parts)}."

        records.append(
            {
                "season": season,
                "round": round_number,
                "session": session,
                "explanation_type": "top_drivers",
                "explanation_text": explanation_text,
                "explanation_generated_at": explanation_generated_at,
            }
        )

    schema = pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("session", pa.string()),
            ("explanation_type", pa.string()),
            ("explanation_text", pa.string()),
            ("explanation_generated_at", pa.string()),
        ]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "explanations_session_top_drivers.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=schema), output_path)

    return output_path
