from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pyarrow.parquet as pq
from f1_core.paths import (
    intelligence_driver_reports_path,
    intelligence_race_trends_path,
    intelligence_session_summaries_path,
    intelligence_strategy_summaries_path,
)

SESSION_SUMMARIES_PATH = intelligence_session_summaries_path()
DRIVER_REPORTS_PATH = intelligence_driver_reports_path()
STRATEGY_SUMMARIES_PATH = intelligence_strategy_summaries_path()
RACE_TRENDS_PATH = intelligence_race_trends_path()


def load_session_intelligence_summaries(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    limit: int = 20,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or SESSION_SUMMARIES_PATH, limit)
    filtered = _filter_rows(rows, season=season, round_number=round_number, session=session)
    return sorted(
        filtered,
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            -float(row["importance_score"]),
            str(row["headline"]),
        ),
    )[:limit]


def load_driver_intelligence_reports(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str | None = None,
    limit: int = 20,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or DRIVER_REPORTS_PATH, limit)
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
        ),
    )[:limit]


def load_strategy_insights(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str | None = None,
    limit: int = 20,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or STRATEGY_SUMMARIES_PATH, limit)
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
            str(row["strategy_headline"]),
        ),
    )[:limit]


def load_race_trend_analysis(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    driver_code: str | None = None,
    limit: int = 50,
    artifact_path: Path | None = None,
) -> list[dict[str, object]]:
    rows = _load_rows(artifact_path or RACE_TRENDS_PATH, limit)
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
            str(row["trend_category"]),
        ),
    )[:limit]


def _load_rows(path: Path, limit: int) -> list[dict[str, object]]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    if not path.exists():
        raise FileNotFoundError(f"Intelligence data not found: {path}")
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
