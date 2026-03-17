from __future__ import annotations

from typing import Iterable

import pyarrow.parquet as pq

from f1_core.paths import baseline_driver_scores_path

MODELS_PATH = baseline_driver_scores_path()


def load_baseline_driver_scores(
    *,
    season: int | None = None,
    round_number: int | None = None,
    session: str | None = None,
    limit: int = 20,
    models_path: Path | None = None,
) -> list[dict[str, object]]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    path = models_path or MODELS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Model data not found: {path}")

    table = pq.read_table(path)
    rows = table.to_pylist()

    filtered = _filter_rows(rows, season=season, round_number=round_number, session=session)
    ordered = sorted(
        filtered,
        key=lambda row: (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            str(row["driver_code"]),
        ),
    )

    return ordered[:limit]


def _filter_rows(
    rows: Iterable[dict[str, object]],
    *,
    season: int | None,
    round_number: int | None,
    session: str | None,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for row in rows:
        if season is not None and int(row.get("season", -1)) != season:
            continue
        if round_number is not None and int(row.get("round", -1)) != round_number:
            continue
        if session is not None and str(row.get("session", "")) != session:
            continue
        results.append(row)
    return results
