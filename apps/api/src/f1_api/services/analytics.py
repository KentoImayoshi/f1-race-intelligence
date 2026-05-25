from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pyarrow.parquet as pq
from f1_core.paths import (
    driver_consistency_path,
    lap_analysis_path,
    pace_evolution_path,
    tire_stint_summary_path,
)

LAP_ANALYSIS_PATH = lap_analysis_path()
TIRE_STINTS_PATH = tire_stint_summary_path()
DRIVER_CONSISTENCY_PATH = driver_consistency_path()
PACE_EVOLUTION_PATH = pace_evolution_path()


def load_session_lap_analysis(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str | None = None,
    limit: int = 200,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or LAP_ANALYSIS_PATH, limit)
    filtered = _filter_rows(
        rows,
        season=season,
        round_number=round_number,
        session=session,
        driver_code=driver_code,
    )
    return sorted(
        filtered,
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            str(row["driver_code"]),
            int(row["lap_number"]),
        ),
    )[:limit]


def load_driver_lap_comparison(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str,
    compare_driver: str,
    limit: int = 200,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = load_session_lap_analysis(
        season=season,
        round_number=round_number,
        session=session,
        limit=limit * 2,
        artifact_path=artifact_path,
    )
    candidates = [
        row for row in rows if str(row.get("driver_code")) in {driver_code, compare_driver}
    ]
    return sorted(candidates, key=lambda row: (int(row["lap_number"]), str(row["driver_code"])))[
        :limit
    ]


def load_tire_stint_summaries(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str | None = None,
    limit: int = 100,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or TIRE_STINTS_PATH, limit)
    filtered = _filter_rows(
        rows,
        season=season,
        round_number=round_number,
        session=session,
        driver_code=driver_code,
    )
    return sorted(
        filtered,
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            str(row["driver_code"]),
            int(row.get("stint") or 0),
        ),
    )[:limit]


def load_pace_evolution(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str | None = None,
    limit: int = 200,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or PACE_EVOLUTION_PATH, limit)
    filtered = _filter_rows(
        rows,
        season=season,
        round_number=round_number,
        session=session,
        driver_code=driver_code,
    )
    return sorted(
        filtered,
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            str(row["driver_code"]),
            int(row["lap_number"]),
        ),
    )[:limit]


def load_driver_consistency(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    limit: int = 50,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or DRIVER_CONSISTENCY_PATH, limit)
    filtered = _filter_rows(rows, season=season, round_number=round_number, session=session)
    return sorted(
        filtered,
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            -float(row["consistency_index"]),
            str(row["driver_code"]),
        ),
    )[:limit]


def _load_rows(path: Path, limit: int) -> list[dict[str, object]]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    if not path.exists():
        raise FileNotFoundError(f"Analytics data not found: {path}")
    return pq.read_table(path).to_pylist()


def _filter_rows(
    rows: Iterable[dict[str, object]],
    *,
    season: int | None,
    round_number: int | None,
    session: str | None,
    driver_code: str | None = None,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for row in rows:
        if season is not None and int(row.get("season", -1)) != season:
            continue
        if round_number is not None and int(row.get("round", -1)) != round_number:
            continue
        if session is not None and str(row.get("session", "")) != session:
            continue
        if driver_code is not None and str(row.get("driver_code", "")) != driver_code:
            continue
        results.append(row)
    return results
