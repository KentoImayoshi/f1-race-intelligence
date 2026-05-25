"""Feature engineering and telemetry-aware analytics artifacts."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_features.contracts import (
    FEATURE_SESSION_RESULTS_COLUMNS,
    SESSION_DRIVER_CONSISTENCY_COLUMNS,
    SESSION_LAP_ANALYSIS_COLUMNS,
    SESSION_PACE_EVOLUTION_COLUMNS,
    SESSION_SECTOR_PERFORMANCE_COLUMNS,
    SESSION_TIRE_STINT_COLUMNS,
)

REQUIRED_PROCESSED_COLUMNS = {
    "season",
    "round",
    "session",
    "driver_code",
    "position",
    "lap_time_ms",
    "processed_at",
}

REQUIRED_LAP_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "lap_time_ms",
    "sector_1_ms",
    "sector_2_ms",
    "sector_3_ms",
    "compound",
    "stint",
    "is_personal_best",
    "source",
    "ingested_at",
}

REQUIRED_TELEMETRY_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "speed_i1_kph",
    "speed_i2_kph",
    "speed_fl_kph",
    "speed_st_kph",
    "tyre_life_laps",
    "track_status",
    "is_pit_out_lap",
    "is_pit_in_lap",
    "source",
    "ingested_at",
}


def build_session_features(*, processed_path: Path, output_dir: Path) -> Path:
    """Read processed session results and write a features parquet artifact."""
    table = pq.read_table(processed_path)
    missing = REQUIRED_PROCESSED_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required processed columns: {missing_list}")

    feature_generated_at = _timestamp_now()
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

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features_session_results.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=_features_schema()), output_path)
    return output_path


def build_session_analytics(
    *,
    laps_path: Path,
    telemetry_path: Path,
    output_dir: Path,
) -> dict[str, Path]:
    """Build telemetry-aware analytics artifacts from lap and telemetry parquet inputs."""
    laps_table = pq.read_table(laps_path)
    telemetry_table = pq.read_table(telemetry_path)

    missing_lap_columns = REQUIRED_LAP_COLUMNS.difference(laps_table.schema.names)
    if missing_lap_columns:
        raise ValueError(f"Missing required lap columns: {', '.join(sorted(missing_lap_columns))}")

    missing_telemetry_columns = REQUIRED_TELEMETRY_COLUMNS.difference(telemetry_table.schema.names)
    if missing_telemetry_columns:
        raise ValueError(
            "Missing required telemetry columns: " f"{', '.join(sorted(missing_telemetry_columns))}"
        )

    laps = sorted(
        laps_table.to_pylist(),
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            str(row["driver_code"]),
            int(row["lap_number"]),
        ),
    )
    if not laps:
        raise ValueError("Lap analysis requires at least one lap row")

    telemetry_map = {_lap_key(row): row for row in telemetry_table.to_pylist()}

    analysis_generated_at = _timestamp_now()
    fastest_lap_ms = min(
        int(row["lap_time_ms"])
        for row in laps
        if row.get("lap_time_ms") is not None and int(row["lap_time_ms"]) > 0
    )
    sector_fastests = {
        "sector_1_ms": _fastest_optional(laps, "sector_1_ms"),
        "sector_2_ms": _fastest_optional(laps, "sector_2_ms"),
        "sector_3_ms": _fastest_optional(laps, "sector_3_ms"),
    }

    lap_analysis: list[dict[str, object]] = []
    sector_rows: list[dict[str, object]] = []
    tire_stint_rows: list[dict[str, object]] = []
    consistency_rows: list[dict[str, object]] = []
    pace_rows: list[dict[str, object]] = []

    laps_by_driver: dict[str, list[dict[str, object]]] = defaultdict(list)
    laps_by_driver_stint: dict[tuple[str, int | None], list[dict[str, object]]] = defaultdict(list)

    for row in laps:
        telemetry = telemetry_map.get(_lap_key(row), {})
        lap_time_ms = _int_or_none(row.get("lap_time_ms"))
        if lap_time_ms is None or lap_time_ms <= 0:
            continue

        top_speed = _top_speed_kph(telemetry)
        delta_to_fastest_ms = lap_time_ms - fastest_lap_ms
        lap_analysis_row = {
            "season": int(row["season"]),
            "round": int(row["round"]),
            "grand_prix": str(row["grand_prix"]),
            "session": str(row["session"]),
            "driver_code": str(row["driver_code"]),
            "lap_number": int(row["lap_number"]),
            "compound": row.get("compound"),
            "stint": _int_or_none(row.get("stint")),
            "lap_time_ms": lap_time_ms,
            "lap_time_seconds": lap_time_ms / 1000.0,
            "sector_1_ms": _int_or_none(row.get("sector_1_ms")),
            "sector_2_ms": _int_or_none(row.get("sector_2_ms")),
            "sector_3_ms": _int_or_none(row.get("sector_3_ms")),
            "delta_to_fastest_ms": delta_to_fastest_ms,
            "delta_to_fastest_pct": _ratio_percent(delta_to_fastest_ms, fastest_lap_ms),
            "lap_rank": 0,
            "top_speed_kph": top_speed,
            "tyre_life_laps": _int_or_none(telemetry.get("tyre_life_laps")),
            "is_personal_best": row.get("is_personal_best"),
            "analysis_generated_at": analysis_generated_at,
        }
        lap_analysis.append(lap_analysis_row)
        laps_by_driver[lap_analysis_row["driver_code"]].append(lap_analysis_row)
        laps_by_driver_stint[(lap_analysis_row["driver_code"], lap_analysis_row["stint"])].append(
            lap_analysis_row
        )

        sector_rows.append(
            {
                "season": lap_analysis_row["season"],
                "round": lap_analysis_row["round"],
                "grand_prix": lap_analysis_row["grand_prix"],
                "session": lap_analysis_row["session"],
                "driver_code": lap_analysis_row["driver_code"],
                "lap_number": lap_analysis_row["lap_number"],
                "sector_1_ms": lap_analysis_row["sector_1_ms"],
                "sector_1_delta_ms": _delta_optional(
                    lap_analysis_row["sector_1_ms"], sector_fastests["sector_1_ms"]
                ),
                "sector_2_ms": lap_analysis_row["sector_2_ms"],
                "sector_2_delta_ms": _delta_optional(
                    lap_analysis_row["sector_2_ms"], sector_fastests["sector_2_ms"]
                ),
                "sector_3_ms": lap_analysis_row["sector_3_ms"],
                "sector_3_delta_ms": _delta_optional(
                    lap_analysis_row["sector_3_ms"], sector_fastests["sector_3_ms"]
                ),
                "combined_sector_ms": _sum_optionals(
                    lap_analysis_row["sector_1_ms"],
                    lap_analysis_row["sector_2_ms"],
                    lap_analysis_row["sector_3_ms"],
                ),
                "top_speed_kph": top_speed,
                "analysis_generated_at": analysis_generated_at,
            }
        )

    ranked_laps = sorted(
        lap_analysis, key=lambda row: (int(row["lap_time_ms"]), str(row["driver_code"]))
    )
    for rank, row in enumerate(ranked_laps, start=1):
        row["lap_rank"] = rank

    for driver_code, driver_laps in laps_by_driver.items():
        ordered_laps = sorted(driver_laps, key=lambda row: int(row["lap_number"]))
        rolling_window: list[int] = []
        for lap in ordered_laps:
            rolling_window.append(int(lap["lap_time_ms"]))
            window = rolling_window[-3:]
            rolling_avg = round(sum(window) / len(window))
            previous_avg = round(sum(window[:-1]) / len(window[:-1])) if len(window) > 1 else None
            pace_rows.append(
                {
                    "season": lap["season"],
                    "round": lap["round"],
                    "grand_prix": lap["grand_prix"],
                    "session": lap["session"],
                    "driver_code": driver_code,
                    "lap_number": lap["lap_number"],
                    "lap_time_ms": lap["lap_time_ms"],
                    "rolling_avg_lap_time_ms": rolling_avg,
                    "delta_to_fastest_ms": lap["delta_to_fastest_ms"],
                    "pace_trend": _pace_trend(rolling_avg, previous_avg),
                    "top_speed_kph": lap["top_speed_kph"],
                    "analysis_generated_at": analysis_generated_at,
                }
            )

        lap_times = [int(lap["lap_time_ms"]) for lap in ordered_laps]
        avg_lap_time = round(sum(lap_times) / len(lap_times))
        best_lap_time = min(lap_times)
        avg_delta_to_fastest = round(
            sum(int(lap["delta_to_fastest_ms"]) for lap in ordered_laps) / len(ordered_laps)
        )
        consistency_rows.append(
            {
                "season": ordered_laps[0]["season"],
                "round": ordered_laps[0]["round"],
                "grand_prix": ordered_laps[0]["grand_prix"],
                "session": ordered_laps[0]["session"],
                "driver_code": driver_code,
                "lap_count": len(ordered_laps),
                "avg_lap_time_ms": avg_lap_time,
                "best_lap_time_ms": best_lap_time,
                "lap_time_stddev_ms": _stddev(lap_times),
                "consistency_index": _consistency_index(lap_times),
                "avg_delta_to_fastest_ms": avg_delta_to_fastest,
                "top_speed_kph": _max_optional([lap.get("top_speed_kph") for lap in ordered_laps]),
                "analysis_generated_at": analysis_generated_at,
            }
        )

    for (driver_code, stint), stint_laps in laps_by_driver_stint.items():
        ordered_laps = sorted(stint_laps, key=lambda row: int(row["lap_number"]))
        tire_stint_rows.append(
            {
                "season": ordered_laps[0]["season"],
                "round": ordered_laps[0]["round"],
                "grand_prix": ordered_laps[0]["grand_prix"],
                "session": ordered_laps[0]["session"],
                "driver_code": driver_code,
                "stint": stint,
                "compound": _first_non_empty([lap.get("compound") for lap in ordered_laps]),
                "lap_count": len(ordered_laps),
                "start_lap": ordered_laps[0]["lap_number"],
                "end_lap": ordered_laps[-1]["lap_number"],
                "avg_lap_time_ms": round(
                    sum(int(lap["lap_time_ms"]) for lap in ordered_laps) / len(ordered_laps)
                ),
                "best_lap_time_ms": min(int(lap["lap_time_ms"]) for lap in ordered_laps),
                "avg_delta_to_fastest_ms": round(
                    sum(int(lap["delta_to_fastest_ms"]) for lap in ordered_laps) / len(ordered_laps)
                ),
                "avg_top_speed_kph": _average_optional(
                    [lap.get("top_speed_kph") for lap in ordered_laps]
                ),
                "analysis_generated_at": analysis_generated_at,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "lap_analysis": output_dir / "analytics_session_lap_analysis.parquet",
        "sector_performance": output_dir / "analytics_session_sector_performance.parquet",
        "tire_stints": output_dir / "analytics_session_tire_stints.parquet",
        "driver_consistency": output_dir / "analytics_session_driver_consistency.parquet",
        "pace_evolution": output_dir / "analytics_session_pace_evolution.parquet",
    }
    pq.write_table(
        pa.Table.from_pylist(lap_analysis, schema=_lap_analysis_schema()), outputs["lap_analysis"]
    )
    pq.write_table(
        pa.Table.from_pylist(sector_rows, schema=_sector_performance_schema()),
        outputs["sector_performance"],
    )
    pq.write_table(
        pa.Table.from_pylist(tire_stint_rows, schema=_tire_stint_schema()),
        outputs["tire_stints"],
    )
    pq.write_table(
        pa.Table.from_pylist(consistency_rows, schema=_driver_consistency_schema()),
        outputs["driver_consistency"],
    )
    pq.write_table(
        pa.Table.from_pylist(pace_rows, schema=_pace_evolution_schema()),
        outputs["pace_evolution"],
    )
    return outputs


def _features_schema() -> pa.Schema:
    return pa.schema(
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


def _lap_analysis_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("lap_number", pa.int64()),
            ("compound", pa.string()),
            ("stint", pa.int64()),
            ("lap_time_ms", pa.int64()),
            ("lap_time_seconds", pa.float64()),
            ("sector_1_ms", pa.int64()),
            ("sector_2_ms", pa.int64()),
            ("sector_3_ms", pa.int64()),
            ("delta_to_fastest_ms", pa.int64()),
            ("delta_to_fastest_pct", pa.float64()),
            ("lap_rank", pa.int64()),
            ("top_speed_kph", pa.int64()),
            ("tyre_life_laps", pa.int64()),
            ("is_personal_best", pa.bool_()),
            ("analysis_generated_at", pa.string()),
        ]
    )


def _sector_performance_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("lap_number", pa.int64()),
            ("sector_1_ms", pa.int64()),
            ("sector_1_delta_ms", pa.int64()),
            ("sector_2_ms", pa.int64()),
            ("sector_2_delta_ms", pa.int64()),
            ("sector_3_ms", pa.int64()),
            ("sector_3_delta_ms", pa.int64()),
            ("combined_sector_ms", pa.int64()),
            ("top_speed_kph", pa.int64()),
            ("analysis_generated_at", pa.string()),
        ]
    )


def _tire_stint_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("stint", pa.int64()),
            ("compound", pa.string()),
            ("lap_count", pa.int64()),
            ("start_lap", pa.int64()),
            ("end_lap", pa.int64()),
            ("avg_lap_time_ms", pa.int64()),
            ("best_lap_time_ms", pa.int64()),
            ("avg_delta_to_fastest_ms", pa.int64()),
            ("avg_top_speed_kph", pa.int64()),
            ("analysis_generated_at", pa.string()),
        ]
    )


def _driver_consistency_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("lap_count", pa.int64()),
            ("avg_lap_time_ms", pa.int64()),
            ("best_lap_time_ms", pa.int64()),
            ("lap_time_stddev_ms", pa.int64()),
            ("consistency_index", pa.float64()),
            ("avg_delta_to_fastest_ms", pa.int64()),
            ("top_speed_kph", pa.int64()),
            ("analysis_generated_at", pa.string()),
        ]
    )


def _pace_evolution_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("lap_number", pa.int64()),
            ("lap_time_ms", pa.int64()),
            ("rolling_avg_lap_time_ms", pa.int64()),
            ("delta_to_fastest_ms", pa.int64()),
            ("pace_trend", pa.string()),
            ("top_speed_kph", pa.int64()),
            ("analysis_generated_at", pa.string()),
        ]
    )


def _lap_key(row: dict[str, object]) -> tuple[int, int, str, str, int]:
    return (
        int(row["season"]),
        int(row["round"]),
        str(row["session"]),
        str(row["driver_code"]),
        int(row["lap_number"]),
    )


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stddev(values: list[int]) -> int:
    if len(values) <= 1:
        return 0
    average = sum(values) / len(values)
    variance = sum((value - average) ** 2 for value in values) / len(values)
    return round(sqrt(variance))


def _consistency_index(values: list[int]) -> float:
    deviation = _stddev(values)
    return round(1.0 / (1.0 + (deviation / 1000.0)), 4)


def _ratio_percent(delta: int, baseline: int) -> float:
    if baseline <= 0:
        return 0.0
    return round((delta / baseline) * 100.0, 3)


def _pace_trend(current_avg: int, previous_avg: int | None) -> str:
    if previous_avg is None:
        return "baseline"
    if current_avg < previous_avg:
        return "improving"
    if current_avg > previous_avg:
        return "declining"
    return "stable"


def _top_speed_kph(telemetry: dict[str, object]) -> int | None:
    return _max_optional(
        [
            telemetry.get("speed_i1_kph"),
            telemetry.get("speed_i2_kph"),
            telemetry.get("speed_fl_kph"),
            telemetry.get("speed_st_kph"),
        ]
    )


def _average_optional(values: list[object]) -> int | None:
    valid = [int(value) for value in values if value is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid))


def _max_optional(values: list[object]) -> int | None:
    valid = [int(value) for value in values if value is not None]
    if not valid:
        return None
    return max(valid)


def _fastest_optional(rows: list[dict[str, object]], column: str) -> int | None:
    valid = [
        int(row[column]) for row in rows if row.get(column) is not None and int(row[column]) > 0
    ]
    if not valid:
        return None
    return min(valid)


def _delta_optional(value: object, fastest: int | None) -> int | None:
    parsed = _int_or_none(value)
    if parsed is None or fastest is None:
        return None
    return parsed - fastest


def _sum_optionals(*values: object) -> int | None:
    parsed = [_int_or_none(value) for value in values]
    if any(value is None for value in parsed):
        return None
    return sum(value for value in parsed if value is not None)


def _first_non_empty(values: list[object]) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


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


__all__ = [
    "FEATURE_SESSION_RESULTS_COLUMNS",
    "SESSION_DRIVER_CONSISTENCY_COLUMNS",
    "SESSION_LAP_ANALYSIS_COLUMNS",
    "SESSION_PACE_EVOLUTION_COLUMNS",
    "SESSION_SECTOR_PERFORMANCE_COLUMNS",
    "SESSION_TIRE_STINT_COLUMNS",
    "build_session_analytics",
    "build_session_features",
]
