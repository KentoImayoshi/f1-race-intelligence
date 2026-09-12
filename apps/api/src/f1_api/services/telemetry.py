from __future__ import annotations

import fastf1
import pandas as pd

from f1_core.paths import cache_dir


def get_reference_lap(
    year: int,
    round_number: int,
    session: str = "R",
) -> pd.DataFrame:
    """
    Return telemetry from the fastest lap of the selected session.
    """

    cache_path = cache_dir()
    fastf1.Cache.enable_cache(str(cache_path))

    event = fastf1.get_session(year, round_number, session)
    event.load()

    fastest = event.laps.pick_fastest()

    telemetry = (
        fastest.get_telemetry()
        .add_distance()
        [["Distance", "X", "Y", "Speed", "Throttle", "Brake"]]
        .dropna()
    )

    return telemetry.reset_index(drop=True)


def get_track_coordinates(
    year: int,
    round_number: int,
    session: str = "R",
) -> list[dict]:
    telemetry = get_reference_lap(year, round_number, session)

    return [
        {
            "x": float(row.X),
            "y": float(row.Y),
            "distance": float(row.Distance),
        }
        for row in telemetry.itertuples()
    ]