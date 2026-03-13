"""Structured insights for session-level driver performance."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_insights.contracts import INSIGHT_SESSION_TOP_DRIVERS_COLUMNS

REQUIRED_BASELINE_COLUMNS = {
    "season",
    "round",
    "session",
    "driver_code",
    "score",
    "position_numeric",
    "model_generated_at",
}


def build_top_driver_insights(*, baseline_path: Path, output_dir: Path, top_n: int = 3) -> Path:
    """Build top driver insights per session from baseline scores."""
    if top_n <= 0:
        raise ValueError("top_n must be greater than 0")

    table = pq.read_table(baseline_path)
    missing = REQUIRED_BASELINE_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required baseline columns: {missing_list}")

    insight_generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    rows = table.to_pylist()
    grouped: dict[tuple[int, int, str], list[dict[str, object]]] = {}
    for row in rows:
        key = (int(row["season"]), int(row["round"]), str(row["session"]))
        grouped.setdefault(key, []).append(row)

    records = []
    for (season, round_number, session), group_rows in grouped.items():
        sorted_rows = sorted(
            group_rows,
            key=lambda r: (-float(r["score"]), str(r["driver_code"])),
        )

        for rank, row in enumerate(sorted_rows[:top_n], start=1):
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "session": session,
                    "rank": rank,
                    "driver_code": row["driver_code"],
                    "score": float(row["score"]),
                    "insight_generated_at": insight_generated_at,
                }
            )

    schema = pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("session", pa.string()),
            ("rank", pa.int64()),
            ("driver_code", pa.string()),
            ("score", pa.float64()),
            ("insight_generated_at", pa.string()),
        ]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "insights_session_top_drivers.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=schema), output_path)

    return output_path
